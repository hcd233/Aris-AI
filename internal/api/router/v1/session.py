from datetime import datetime
from json import dumps, loads
from threading import Thread
from typing import Any, Callable, Dict, Tuple

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from langchain.chains.base import Chain
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.vectorstores import VectorStoreRetriever
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from sqlalchemy import or_

from internal.langchain.callback import StreamCallbackHandler, TokenGenerator
from internal.langchain.chain import init_chat_chain, init_retriever_qa_chain
from internal.langchain.embedding import init_embedding
from internal.langchain.llm import init_llm
from internal.langchain.memory import init_chat_memory, init_history
from internal.langchain.prompt import init_chat_prompt, init_retriever_prompt
from internal.langchain.retriever import init_retriever
from internal.logger import logger
from internal.middleware.mysql import session
from internal.middleware.mysql.model import LLMSchema, MessageSchema, SessionSchema, VectorDbSchema
from internal.middleware.mysql.model.embeddings import EmbeddingSchema
from internal.middleware.redis import r

from ...auth import sk_auth
from ...model.request import ChatRequest, RetrieverQARequest
from ...model.response import SSEResponse, StandardResponse

session_router = APIRouter(prefix="/session", tags=["session"])


@session_router.post("", response_model=StandardResponse, dependencies=[Depends(sk_auth)])
async def create_session(info: Tuple[int, int] = Depends(sk_auth)):
    uid, _ = info

    redis_set = f"uid:{uid}:session_ids"
    if r.exists(redis_set):
        count = len(r.smembers(redis_set))
        if count >= 40:
            return StandardResponse(code=1, status="error", message="Your session list is full(40), please delete some sessions first.")
    else:
        with session() as conn:
            if not conn.is_active:
                conn.rollback()
                conn.close()
            else:
                conn.commit()

            # count session
            query = (
                conn.query(SessionSchema.session_id)
                .filter(SessionSchema.uid == uid)
                .filter(or_(SessionSchema.delete_at.is_(None), datetime.now() < SessionSchema.delete_at))
            )
            results = query.all()
            for result in results:
                r.sadd(redis_set, result[0])

            if len(results) >= 40:
                return StandardResponse(code=1, status="error", message="Your session list is full(40), please delete some sessions first")

    with session() as conn:
        if not conn.is_active:
            conn.rollback()
            conn.close()
        else:
            conn.commit()

        _session = SessionSchema(uid=uid)
        conn.add(_session)
        conn.commit()
        data = {"session_id": _session.session_id, "create_at": _session.create_at}
        r.sadd(redis_set, _session.session_id)
        r.delete(f"session:{_session.session_id}")

    r.delete(f"uid:{uid}:sessions")

    return StandardResponse(code=0, status="success", data=data)


@session_router.get("/sessions", response_model=StandardResponse, dependencies=[Depends(sk_auth)])
async def list_session(page_id: int = 0, per_page_num: int = 20, info: Tuple[int, int] = Depends(sk_auth)):
    uid, _ = info
    redis_list = f"uid:{uid}:sessions"
    if r.exists(redis_list):
        if session_list := r.lrange(redis_list, page_id * per_page_num, (page_id + 1) * per_page_num - 1):
            return StandardResponse(
                code=0,
                status="success",
                data={"session_list": [loads(s) for s in session_list]},
            )

    with session() as conn:
        if not conn.is_active:
            conn.rollback()
            conn.close()
        else:
            conn.commit()

        query = (
            conn.query(SessionSchema.session_id, SessionSchema.create_at, SessionSchema.update_at)
            .filter(SessionSchema.uid == uid)
            .filter(or_(SessionSchema.delete_at.is_(None), datetime.now() < SessionSchema.delete_at))
            .order_by(SessionSchema.session_id.desc())
            .offset(page_id * per_page_num)
        )
        result = query.limit(per_page_num).all()

    session_list = [
        {
            "session_id": session_id,
            "create_at": str(create_at),
            "last_chat_at": str(update_at),
        }
        for session_id, create_at, update_at in result
    ]
    for s in session_list:
        r.lpush(redis_list, dumps(s, ensure_ascii=False))

    data = {"session_list": session_list}
    return StandardResponse(code=0, status="success", data=data)


@session_router.get("/{session_id}", response_model=StandardResponse, dependencies=[Depends(sk_auth)])
async def get_session(session_id: str, info: Tuple[int, int] = Depends(sk_auth)):
    uid, _ = info

    redis_key = f"session:{session_id}"
    info = r.get(redis_key)
    if info == "not_exist":
        return StandardResponse(code=1, status="error", message="Session not exist")
    if info:
        data = loads(info)
        return StandardResponse(code=0, status="success", data=data)

    with session() as conn:
        if not conn.is_active:
            conn.rollback()
            conn.close()
        else:
            conn.commit()

        query = (
            conn.query(SessionSchema.session_id, SessionSchema.create_at, SessionSchema.update_at, LLMSchema.llm_name)
            .filter(SessionSchema.session_id == session_id)
            .filter(SessionSchema.uid == uid)
            .join(LLMSchema, isouter=True)
            .filter(or_(SessionSchema.delete_at.is_(None), datetime.now() < SessionSchema.delete_at))
        )
        result = query.first()

        if not result:
            r.set(redis_key, "not_exist", ex=20)
            return StandardResponse(code=1, status="error", message="Session not exist")

        session_id, create_at, update_at, llm_name = result

        query = conn.query(MessageSchema.id, MessageSchema.chat_at, MessageSchema.message).filter(MessageSchema.session_id == session_id)
        results = query.all()

        parse_message_func: Callable[[Dict[str, Any]], Dict[str, Any]] = lambda x: {"role": x.get("type"), "content": x.get("data").get("content")}
        messages = [
            {"message_id": message_id, "chat_at": str(chat_at), "message": parse_message_func(loads(message))}
            for message_id, chat_at, message in results
        ]

    data = {
        "session_id": session_id,
        "create_at": str(create_at),
        "update_at": str(update_at),
        "bind_llm": llm_name,
        "messages": messages,
    }

    r.set(redis_key, dumps(data, ensure_ascii=False), ex=300)

    return StandardResponse(code=0, status="success", data=data)


@session_router.delete("/{session_id}/delete", response_model=StandardResponse, dependencies=[Depends(sk_auth)])
async def delete_session(session_id: int, uid: int = -1, info: Tuple[int, int] = Depends(sk_auth)):
    _uid, level = info
    if not (level or _uid == uid):
        return StandardResponse(code=1, status="error", message="no permission")

    if uid == -1:
        uid = _uid

    redis_set = f"uid:{uid}:session_ids"
    if r.exists(redis_set):
        if not r.sismember(redis_set, session_id):
            return StandardResponse(code=1, status="error", message="Session not exist")

        r.srem(redis_set, session_id)
    else:
        with session() as conn:
            if not conn.is_active:
                conn.rollback()
                conn.close()
            else:
                conn.commit()

            query = (
                conn.query(SessionSchema.session_id, SessionSchema.delete_at)
                .filter(SessionSchema.session_id == session_id)
                .filter(SessionSchema.uid == uid)
                .filter(or_(SessionSchema.delete_at.is_(None), datetime.now() < SessionSchema.delete_at))
            )

            if not query.first():
                return StandardResponse(code=1, status="error", message="Session not exist")

    with session() as conn:
        if not conn.is_active:
            conn.rollback()
            conn.close()
        else:
            conn.commit()
        query = (
            conn.query(SessionSchema)
            .filter(SessionSchema.session_id == session_id)
            .filter(SessionSchema.uid == uid)
            .filter(or_(SessionSchema.delete_at.is_(None), datetime.now() < SessionSchema.delete_at))
        )
        query.update({SessionSchema.delete_at: datetime.now()})
        conn.commit()

    r.delete(f"session:{session_id}")
    r.delete(f"uid:{uid}:sessions")

    return StandardResponse(code=0, status="success", message="Delete session successfully")


@session_router.post("/{session_id}/chat", dependencies=[Depends(sk_auth)])
async def chat(session_id: int, request: ChatRequest, info: Tuple[int, int] = Depends(sk_auth)) -> StandardResponse | SSEResponse:
    _uid, _ = info

    redis_lock = f"chat_lock:uid:{_uid}"
    if r.exists(redis_lock):
        return StandardResponse(code=1, status="error", message="You are chatting, please wait a moment")
    r.set(redis_lock, "lock", ex=30)

    with session() as conn:
        if not conn.is_active:
            conn.rollback()
            conn.close()
        else:
            conn.commit()

        query = (
            conn.query(SessionSchema.session_id, LLMSchema.llm_name)
            .filter(SessionSchema.session_id == session_id)
            .filter(SessionSchema.uid == _uid)
            .join(LLMSchema, isouter=True)
            .filter(or_(SessionSchema.delete_at.is_(None), datetime.now() < SessionSchema.delete_at))
        )

        result = query.first()
        if not result:
            r.delete(redis_lock)
            return StandardResponse(code=1, status="error", message="Session not exist")

        _, llm_name = result
        if llm_name:
            request.llm_name = llm_name
            logger.debug(f"Use bind LLM: {llm_name}")
        query = (
            conn.query(LLMSchema)
            .filter(LLMSchema.llm_name == request.llm_name)
            .filter(or_(LLMSchema.delete_at.is_(None), datetime.now() < LLMSchema.delete_at))
        )
        _llm: LLMSchema | None = query.first()
        if not _llm:
            r.delete(redis_lock)
            return StandardResponse(code=1, status="error", message="LLM not exist")

        if not llm_name:
            conn.query(SessionSchema).filter(SessionSchema.session_id == session_id).update({SessionSchema.llm_id: _llm.llm_id})
            conn.commit()
            logger.debug(f"Bind LLM: {request.llm_name} to Session: {session_id}")

        try:
            token_generator = TokenGenerator(redis_lock=redis_lock)
            callback = StreamCallbackHandler(token_generator)

            llm: ChatOpenAI = init_llm(
                llm_type=_llm.llm_type,
                llm_name=_llm.llm_name,
                base_url=_llm.base_url,
                api_key=_llm.api_key,
                temperature=request.temperature,
                max_tokens=_llm.max_tokens,
                callbacks=[callback],
            )
            history = init_history(session_id=session_id)

            memory = init_chat_memory(
                history=history,
                request_type=_llm.request_type,
                user_name=_llm.user_name,
                ai_name=_llm.ai_name,
                k=8,
            )
            prompt = init_chat_prompt(
                sys_prompt=_llm.sys_prompt,
                request_type=_llm.request_type,
                sys_name=_llm.sys_name,
                user_name=_llm.user_name,
                ai_name=_llm.ai_name,
            )

            chain = init_chat_chain(
                llm=llm,
                prompt=prompt,
                memory=memory,
                callbacks=[callback],
            )
        except Exception as e:
            logger.error(f"Init langchain modules failed: {e}")
            return StandardResponse(code=1, status="error", message="Chat init failed")

    r.delete(f"session:{session_id}")
    r.delete(f"uid:{_uid}:sessions")

    Thread(target=chain.invoke, args=(request.message,)).start()
    return StreamingResponse(token_generator, media_type="text/event-stream")


@session_router.post("/{session_id}/retriever-qa", dependencies=[Depends(sk_auth)])
async def retriever_qa(session_id: int, request: RetrieverQARequest, info: Tuple[int, int] = Depends(sk_auth)) -> StandardResponse | SSEResponse:
    _uid, _ = info

    redis_lock = f"chat_lock:uid:{_uid}"
    if r.exists(redis_lock):
        return StandardResponse(code=1, status="error", message="You are chatting, please wait a moment")
    r.set(redis_lock, "lock", ex=30)

    with session() as conn:
        if not conn.is_active:
            conn.rollback()
            conn.close()
        else:
            conn.commit()

        query = (
            conn.query(SessionSchema.session_id, LLMSchema.llm_name)
            .filter(SessionSchema.session_id == session_id)
            .filter(SessionSchema.uid == _uid)
            .join(LLMSchema, isouter=True)
            .filter(or_(SessionSchema.delete_at.is_(None), datetime.now() < SessionSchema.delete_at))
        )

        result = query.first()
        if not result:
            r.delete(redis_lock)
            return StandardResponse(code=1, status="error", message="Session not exist")

        _, llm_name = result
        if llm_name:
            request.llm_name = llm_name
            logger.debug(f"Use bind LLM: {llm_name}")
        query = (
            conn.query(LLMSchema)
            .filter(LLMSchema.llm_name == request.llm_name)
            .filter(or_(LLMSchema.delete_at.is_(None), datetime.now() < LLMSchema.delete_at))
        )
        _llm: LLMSchema | None = query.first()
        if not _llm:
            r.delete(redis_lock)
            return StandardResponse(code=1, status="error", message="LLM not exist")

        if not llm_name:
            conn.query(SessionSchema).filter(SessionSchema.session_id == session_id).update({SessionSchema.llm_id: _llm.llm_id})
            conn.commit()
            logger.debug(f"Bind LLM: {request.llm_name} to Session: {session_id}")

        query = (
            conn.query(VectorDbSchema.embedding_id, VectorDbSchema.db_size)
            .filter(VectorDbSchema.vector_db_id == request.vector_db_id)
            .filter(or_(VectorDbSchema.delete_at.is_(None), datetime.now() < VectorDbSchema.delete_at))
        )
        result = query.first()
        if not result:
            return StandardResponse(code=1, status="error", message="Vector DB not exist")

        (embedding_id, db_size) = result

        if db_size == 0:
            return StandardResponse(code=1, status="error", message="Vector DB is empty, please upload data first")

        query = (
            conn.query(EmbeddingSchema)
            .filter(EmbeddingSchema.embedding_id == embedding_id)
            .filter(or_(EmbeddingSchema.delete_at.is_(None), datetime.now() < EmbeddingSchema.delete_at))
        )
        _embedding: EmbeddingSchema | None = query.first()
        if not _embedding:
            return StandardResponse(code=1, status="error", message="Embedding not exist")

        try:
            token_generator = TokenGenerator(redis_lock=redis_lock)
            callback = StreamCallbackHandler(token_generator)

            llm: ChatOpenAI = init_llm(
                llm_type=_llm.llm_type,
                llm_name=_llm.llm_name,
                base_url=_llm.base_url,
                api_key=_llm.api_key,
                temperature=request.temperature,
                max_tokens=_llm.max_tokens,
                callbacks=[callback],
            )
            if not llm:
                return StandardResponse(code=1, status="error", message="LLM init failed")

            history = init_history(session_id=session_id)

            prompt = init_retriever_prompt(
                sys_prompt=_llm.sys_prompt,
                request_type=_llm.request_type,
                sys_name=_llm.sys_name,
                user_name=_llm.user_name,
                ai_name=_llm.ai_name,
            )

            embedding: OpenAIEmbeddings = init_embedding(
                _embedding.embedding_type,
                embedding_name=_embedding.embedding_name,
                api_key=_embedding.api_key,
                base_url=_embedding.base_url,
                chunk_size=_embedding.chunk_size,
            )

            if not embedding:
                return StandardResponse(code=1, status="error", message="Embedding init failed")

            retriever: VectorStoreRetriever = init_retriever(
                vector_db_id=request.vector_db_id,
                embedding=embedding,
            )

            chain = init_retriever_qa_chain(
                llm=llm,
                prompt=prompt,
                retriever=retriever,
                callbacks=[callback],
            )

        except Exception as e:
            logger.error(f"Init langchain modules failed: {e}")
            return StandardResponse(code=1, status="error", message="Chat init failed")

    r.delete(f"session:{session_id}")
    r.delete(f"uid:{_uid}:sessions")

    def _chat_after_save_history(chain: Chain, user_prompt: str, history: BaseChatMessageHistory):
        output = chain.invoke(user_prompt)
        docs = "```\n" + "\n```\n---\n```\n".join(output["source_documents"]) + "\n```"
        llm_output = output["result"]
        history.add_message(SystemMessage(content=docs))
        history.add_message(HumanMessage(content=user_prompt))
        history.add_message(AIMessage(content=llm_output))

    Thread(target=_chat_after_save_history, args=(chain, request.message, history)).start()
    return StreamingResponse(token_generator, media_type="text/event-stream")

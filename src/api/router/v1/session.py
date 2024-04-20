from datetime import datetime
from json import dumps, loads
from typing import Any, AsyncGenerator, Callable, Dict, Tuple

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy import or_

from src.langchain_aris.callback import OUTPUT_PARSER_NAME
from src.langchain_aris.chain import init_chat_chain, init_retriever_qa_chain
from src.logger import logger
from src.middleware.mysql import session
from src.middleware.mysql.models import LLMSchema, MessageSchema, SessionSchema, VectorDbSchema
from src.middleware.mysql.models.embeddings import EmbeddingSchema
from src.middleware.redis import r

from ...auth import sk_auth
from ...model.request import ChatRequest
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
async def delete_session(session_id: int, uid: int = None, info: Tuple[int, int] = Depends(sk_auth)):
    _uid, level = info
    if not level and uid and uid != _uid:
        return StandardResponse(code=1, status="error", message="No permission")
    if not uid:
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

    if request.vector_db_id:
        with session() as conn:
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

        chain_func = init_retriever_qa_chain
        chain_kwargs = {
            "llm_schema": _llm,
            "embedding_schema": _embedding,
            "temperature": request.temperature,
            "session_id": session_id,
            "vector_db_id": request.vector_db_id,
        }
    else:
        chain_func = init_chat_chain
        chain_kwargs = {
            "llm_schema": _llm,
            "temperature": request.temperature,
            "session_id": session_id,
        }
    try:
        chain = chain_func(**chain_kwargs)
    except Exception as e:
        logger.exception(f"Init langchain modules failed: {e}")
        return StandardResponse(code=1, status="error", message="Chat init failed")

    r.delete(f"session:{session_id}")
    r.delete(f"uid:{_uid}:sessions")

    async def _filter_event_stream() -> AsyncGenerator[str, None]:
        async for event in chain.astream_events({"user_prompt": request.message}, version="v1", include_names=[OUTPUT_PARSER_NAME]):
            if event["event"] not in ["on_parser_stream"]:
                continue
            yield f"data: {dumps(event, ensure_ascii=False)}\n\n"
        r.delete(redis_lock)

    return StreamingResponse(_filter_event_stream(), media_type="text/event-stream")

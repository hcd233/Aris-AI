import datetime
from json import dumps, loads
from typing import Any, Callable, Dict, Tuple

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from langchain.chains import LLMChain
from langchain_openai import ChatOpenAI
from sqlalchemy import or_

from internal.langchain.llm import init_llm
from internal.langchain.memory import init_history, init_msg_memory, init_str_memory
from internal.langchain.prompt import init_msg_prompt, init_str_prompt
from internal.logger import logger
from internal.middleware.mysql import session
from internal.middleware.mysql.model import LLMSchema, MessageSchema, SessionSchema
from internal.middleware.redis import r

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
                .filter(or_(SessionSchema.delete_at.is_(None), datetime.datetime.now() < SessionSchema.delete_at))
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
            .filter(or_(SessionSchema.delete_at.is_(None), datetime.datetime.now() < SessionSchema.delete_at))
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
            .filter(or_(SessionSchema.delete_at.is_(None), datetime.datetime.now() < SessionSchema.delete_at))
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
                .filter(or_(SessionSchema.delete_at.is_(None), datetime.datetime.now() < SessionSchema.delete_at))
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
            .filter(or_(SessionSchema.delete_at.is_(None), datetime.datetime.now() < SessionSchema.delete_at))
        )
        query.update({SessionSchema.delete_at: datetime.datetime.now()})
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
            .filter(or_(SessionSchema.delete_at.is_(None), datetime.datetime.now() < SessionSchema.delete_at))
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
            .filter(or_(LLMSchema.delete_at.is_(None), datetime.datetime.now() < LLMSchema.delete_at))
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
            llm: ChatOpenAI = init_llm(
                llm_type=_llm.llm_type,
                llm_name=_llm.llm_name,
                base_url=_llm.base_url,
                api_key=_llm.api_key,
                temperature=request.temperature,
                max_tokens=_llm.max_tokens,
            )

            history = init_history(session_id=session_id)

            match _llm.request_type:
                case "string":
                    memory = init_str_memory(
                        history=history,
                        ai_name=_llm.ai_name,
                        user_name=_llm.user_name,
                        k=8,
                    )
                    prompt = init_str_prompt(
                        sys_name=_llm.sys_name,
                        sys_prompt=_llm.sys_prompt,
                        user_name=_llm.user_name,
                        ai_name=_llm.ai_name,
                    )
                case "message":
                    memory = init_msg_memory(
                        history=history,
                        k=8,
                    )
                    prompt = init_msg_prompt(
                        sys_prompt=_llm.sys_prompt,
                    )
                case _:
                    return StandardResponse(code=1, status="error", message="Invalid request type")

            chain = LLMChain(
                name="multi_turn_chat_llm_chain",
                llm=llm,
                prompt=prompt,
                memory=memory,
                verbose=True,
                return_final_only=True,
            )
        except Exception as e:
            logger.error(f"Init langchain modules failed: {e}")
            return StandardResponse(code=1, status="error", message="Chat init failed")

    async def _sse_response():
        try:
            async for chunk in chain.astream_events(
                {"user_prompt": request.message}, name=f"session_{session_id}_chat", event="stream", version="v1"
            ):
                event, name, run_id = chunk.get("event"), chunk.get("name"), chunk.get("run_id")
                data = {"extras": {"name": name, "chat_id": run_id, "event": event, "session_id": session_id}}
                if event == "on_chat_model_start":
                    data.update({"delta": "", "status": "start"})
                elif event == "on_chat_model_stream":
                    data.update({"delta": chunk.get("data").get("chunk").content, "status": "generating"})
                elif event == "on_chat_model_end":
                    data.update({"delta": "", "status": "finished"})
                else:
                    continue

                data = dumps(data, ensure_ascii=False) + "\n"
                logger.debug(f"SSE response: {data}")

                yield data
            r.delete(redis_lock)
        except Exception as e:
            logger.error(f"SSE failed: {e}")
            yield dumps({"extras": {}, "delta": "", "status": f"exception: {e}"}) + "\n"

    r.delete(f"session:{session_id}")
    r.delete(f"uid:{_uid}:sessions")

    return StreamingResponse(_sse_response(), media_type="text/event-stream")

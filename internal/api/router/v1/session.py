import datetime
from json import dumps, loads
from typing import Any, Callable, Dict, Tuple

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from langchain.chains import LLMChain
from langchain_openai import ChatOpenAI
from sqlalchemy import or_

from internal.langchain.llm import init_llm
from internal.langchain.memory import init_history, init_memory
from internal.langchain.prompt import init_prompt
from internal.logger import logger
from internal.middleware.mysql import session
from internal.middleware.mysql.model import LLMSchema, MessageSchema, SessionSchema

from ...auth import sk_auth
from ...model.request import ChatRequest
from ...model.response import SSEResponse, StandardResponse

session_router = APIRouter(prefix="/session", tags=["session"])


@session_router.post("", response_model=StandardResponse, dependencies=[Depends(sk_auth)])
async def create_session(info: Tuple[int, int] = Depends(sk_auth)):
    uid, _ = info

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

    return StandardResponse(code=0, status="success", message="Create session successfully", data=data)


@session_router.get("/sessions", response_model=StandardResponse, dependencies=[Depends(sk_auth)])
async def list_session(page_id: int = 0, per_page_num: int = 20, info: Tuple[int, int] = Depends(sk_auth)):
    uid, _ = info

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
            .order_by(SessionSchema.create_at.desc())
            .offset(page_id * per_page_num)
        )
        result = query.limit(per_page_num).all()

    data = {
        "session_list": [
            {
                "session_id": session_id,
                "create_at": create_at,
                "last_chat_at": update_at,
            }
            for session_id, create_at, update_at in result
        ]
    }
    return StandardResponse(code=0, status="success", message="Get session list successfully", data=data)


@session_router.get("/{session_id}", response_model=StandardResponse, dependencies=[Depends(sk_auth)])
async def get_session(session_id: str, info: Tuple[int, int] = Depends(sk_auth)):
    uid, level = info

    with session() as conn:
        if not conn.is_active:
            conn.rollback()
            conn.close()
        else:
            conn.commit()

        query = (
            conn.query(SessionSchema.session_id, SessionSchema.create_at, SessionSchema.update_at)
            .filter(SessionSchema.session_id == session_id)
            .filter(SessionSchema.uid == uid)
            .filter(or_(SessionSchema.delete_at.is_(None), datetime.datetime.now() < SessionSchema.delete_at))
        )
        result = query.first()

        if not result:
            return StandardResponse(code=1, status="error", message="Session not exist")

        session_id, create_at, update_at = result

        query = conn.query(MessageSchema.id, MessageSchema.chat_at, MessageSchema.message).filter(MessageSchema.session_id == session_id)
        results = query.all()

        parse_message_func: Callable[[Dict[str, Any]], Dict[str, Any]] = lambda x: {"role": x.get("type"), "content": x.get("data").get("content")}
        messages = [
            {"message_id": message_id, "chat_at": chat_at, "message": parse_message_func(loads(message))} for message_id, chat_at, message in results
        ]

    data = {
        "session_id": session_id,
        "create_at": create_at,
        "update_at": update_at,
        "messages": messages,
    }
    return StandardResponse(code=0, status="success", message="Get session successfully", data=data)


@session_router.delete("/{session_id}/delete", response_model=StandardResponse, dependencies=[Depends(sk_auth)])
async def delete_session(uid: int, session_id: int, info: Tuple[int, int] = Depends(sk_auth)):
    _uid, level = info
    if not (level or _uid == uid):
        return StandardResponse(code=1, status="error", message="no permission")

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

        query = (
            conn.query(SessionSchema)
            .filter(SessionSchema.session_id == session_id)
            .filter(SessionSchema.uid == uid)
            .filter(or_(SessionSchema.delete_at.is_(None), datetime.datetime.now() < SessionSchema.delete_at))
        )
        query.update({SessionSchema.delete_at: datetime.datetime.now()})
        conn.commit()

    return StandardResponse(code=0, status="success", message="Delete session successfully")


@session_router.post("/{session_id}/chat", dependencies=[Depends(sk_auth)])
async def chat(session_id: int, request: ChatRequest, info: Tuple[int, int] = Depends(sk_auth)) -> StandardResponse | SSEResponse:
    _uid, _ = info

    with session() as conn:
        if not conn.is_active:
            conn.rollback()
            conn.close()
        else:
            conn.commit()

        query = (
            conn.query(SessionSchema.session_id)
            .filter(SessionSchema.session_id == session_id)
            .filter(SessionSchema.uid == _uid)
            .filter(or_(SessionSchema.delete_at.is_(None), datetime.datetime.now() < SessionSchema.delete_at))
        )

        if not query.first():
            return StandardResponse(code=1, status="error", message="Session not exist")

        query = (
            conn.query(LLMSchema)
            .filter(LLMSchema.llm_name == request.llm_name)
            .filter(or_(LLMSchema.delete_at.is_(None), datetime.datetime.now() < LLMSchema.delete_at))
        )
        _llm: LLMSchema | None = query.first()
        if not _llm:
            return StandardResponse(code=1, status="error", message="LLM not exist")

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
        memory = init_memory(
            history=history,
            ai_name=_llm.ai_name,
            user_name=_llm.user_name,
            k=8,
        )
        prompt = init_prompt(
            sys_name=_llm.sys_name,
            sys_prompt=_llm.sys_prompt,
            user_name=_llm.user_name,
            ai_name=_llm.ai_name,
        )

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
        except Exception as e:
            logger.error(f"SSE failed: {e}")
            yield dumps({"extras": {}, "delta": "", "status": f"exception: {e}"}) + "\n"

    return StreamingResponse(_sse_response(), media_type="text/event-stream")

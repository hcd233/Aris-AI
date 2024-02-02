import datetime
from json import dumps
from typing import Tuple

from fastapi import APIRouter, Depends
from langchain.chains import LLMChain
from langchain_openai import ChatOpenAI
from sqlalchemy import or_
from starlette.responses import StreamingResponse

from internal.langchain.llm import init_llm
from internal.langchain.memory import init_history, init_memory
from internal.langchain.prompt import init_prompt
from internal.middleware.mysql import session
from internal.middleware.mysql.model import LLMSchema, MessageSchema, SessionSchema

from ...auth import sk_auth
from ...model.request import ChatRequest, UidRequest
from ...model.response import StandardResponse

session_router = APIRouter(prefix="/session", tags=["session"])


@session_router.post("/newSession", response_model=StandardResponse, dependencies=[Depends(sk_auth)])
async def create_session(request: UidRequest, info: Tuple[int, int] = Depends(sk_auth)):
    _uid, _ = info
    if _uid != request.uid:
        return StandardResponse(code=1, status="error", message="no permission")
    with session() as conn:
        if not conn.is_active:
            conn.rollback()
            conn.close()
        else:
            conn.commit()

        _session = SessionSchema(uid=request.uid)
        conn.add(_session)
        conn.commit()
        data = {"session_id": _session.session_id, "create_at": _session.create_at}

    return StandardResponse(code=0, status="success", message="Create session successfully", data=data)


@session_router.get("/{session_id}", response_model=StandardResponse, dependencies=[Depends(sk_auth)])
async def get_session(uid: int, session_id: str, info: Tuple[int, int] = Depends(sk_auth)):
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
            conn.query(SessionSchema.session_id, SessionSchema.create_at, SessionSchema.update_at)
            .filter(SessionSchema.session_id == session_id)
            .filter(SessionSchema.uid == uid)
            .filter(or_(SessionSchema.delete_at.is_(None), datetime.datetime.now() < SessionSchema.delete_at))
        )
        result = query.first()

        if not result:
            return StandardResponse(code=1, status="error", message="Session not exist")

        session_id, create_at, update_at = result

        query = conn.query(MessageSchema.message_id, MessageSchema.chat_at, MessageSchema.message).filter(MessageSchema.session_id == session_id)
        results = query.all()

        messages = [{"message_id": message_id, "chat_at": chat_at, "message": message} for message_id, chat_at, message in results]

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
async def chat(session_id: int, request: ChatRequest, info: Tuple[int, int] = Depends(sk_auth)):
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

    chain = LLMChain(llm=llm, prompt=prompt, memory=memory, verbose=True, return_final_only=True)

    async def streaming():
        async for chunk in chain.astream(request.message):
            yield dumps({"delta": chunk}, ensure_ascii=False) + "\n"

    return StreamingResponse(content=streaming(), media_type="text/event-stream")

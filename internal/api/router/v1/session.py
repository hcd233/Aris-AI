import datetime
from typing import Tuple

from fastapi import APIRouter, Depends
from sqlalchemy import or_

from internal.middleware.mysql import session
from internal.middleware.mysql.model import SessionSchema

from ...auth import sk_auth
from ...model.base import StandardResponse
from ...model.v1 import UidRequest

session_router = APIRouter(prefix="/session", tags=["session"])


@session_router.get("/{se_id}", response_model=StandardResponse, dependencies=[Depends(sk_auth)])
async def get_session(uid: int, se_id: str, info: Tuple[int, int] = Depends(sk_auth)):
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
            conn.query(SessionSchema.session_id, SessionSchema.conversation, SessionSchema.create_at, SessionSchema.update_at)
            .filter(SessionSchema.session_id == se_id)
            .filter(SessionSchema.uid == uid)
            .filter(or_(SessionSchema.delete_at.is_(None), datetime.datetime.now() < SessionSchema.delete_at))
        )
        result = query.first()

    if not result:
        return StandardResponse(code=1, status="error", message="Session not exist")

    session_id, conversation, create_at, update_at = result
    data = {
        "session_id": session_id,
        "history": conversation,
        "create_at": create_at,
        "last_chat_at": update_at,
    }
    return StandardResponse(code=0, status="success", message="Get session successfully", data=data)


@session_router.post("/new", response_model=StandardResponse, dependencies=[Depends(sk_auth)])
async def new_session(request: UidRequest, info: Tuple[int, int] = Depends(sk_auth)):
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


@session_router.delete("/{se_id}/delete", response_model=StandardResponse, dependencies=[Depends(sk_auth)])
async def delete_session(uid: int, se_id: int, info: Tuple[int, int] = Depends(sk_auth)):
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
            .filter(SessionSchema.session_id == se_id)
            .filter(SessionSchema.uid == uid)
            .filter(or_(SessionSchema.delete_at.is_(None), datetime.datetime.now() < SessionSchema.delete_at))
        )

        if not query.first():
            return StandardResponse(code=1, status="error", message="Session not exist")

        query = (
            conn.query(SessionSchema)
            .filter(SessionSchema.session_id == se_id)
            .filter(SessionSchema.uid == uid)
            .filter(or_(SessionSchema.delete_at.is_(None), datetime.datetime.now() < SessionSchema.delete_at))
        )
        query.update({SessionSchema.delete_at: datetime.datetime.now()})
        conn.commit()

    return StandardResponse(code=0, status="success", message="Delete session successfully")

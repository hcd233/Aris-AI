import datetime
from typing import Tuple

from fastapi import APIRouter, Depends
from sqlalchemy import or_

from internal.middleware.mysql import session
from internal.middleware.mysql.models import SessionSchema

from ...auth import sk_auth
from ..base import StandardResponse

session_router = APIRouter(prefix="/session", tags=["session"])


@session_router.get("/{uid}/list", response_model=StandardResponse, dependencies=[Depends(sk_auth)])
async def list_session(uid: int, page_id: int = 0, per_page_num: int = 20, info: Tuple[int, int] = Depends(sk_auth)):
    _uid, level = info
    if not (level or _uid == uid):
        return StandardResponse(code=1, status="error", message="no permission")

    with session() as conn:
        if not conn.is_active:
            conn.rollback()
            conn.close()

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


@session_router.get("/{uid}/{session_id}", response_model=StandardResponse, dependencies=[Depends(sk_auth)])
async def get_session(uid: int, session_id: str, info: Tuple[int, int] = Depends(sk_auth)):
    _uid, level = info
    if not (level or _uid == uid):
        return StandardResponse(code=1, status="error", message="no permission")

    with session() as conn:
        if not conn.is_active:
            conn.rollback()
            conn.close()

        query = (
            conn.query(SessionSchema.session_id, SessionSchema.conversation, SessionSchema.create_at, SessionSchema.update_at)
            .filter(SessionSchema.session_id == session_id)
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


@session_router.post("/{uid}/new", response_model=StandardResponse, dependencies=[Depends(sk_auth)])
async def new_session(uid: int, info: Tuple[int, int] = Depends(sk_auth)):
    _uid, _ = info
    if _uid != uid:
        return StandardResponse(code=1, status="error", message="no permission")
    with session() as conn:
        if not conn.is_active:
            conn.rollback()
            conn.close()

        _session = SessionSchema(uid=uid)
        conn.add(_session)
        conn.commit()
        data = {"session_id": _session.session_id, "create_at": _session.create_at}

    return StandardResponse(code=0, status="success", message="Create session successfully", data=data)


@session_router.delete("/{uid}/delete", response_model=StandardResponse, dependencies=[Depends(sk_auth)])
async def delete_session(uid: int, session_id: str, info: Tuple[int, int] = Depends(sk_auth)):
    _uid, level = info
    if not (level or _uid == uid):
        return StandardResponse(code=1, status="error", message="no permission")

    with session() as conn:
        if not conn.is_active:
            conn.rollback()
            conn.close()

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

from fastapi import APIRouter, Depends

from internal.middleware.mysql import session
from internal.middleware.mysql.models import SessionSchema

from ...auth import sk_auth
from ..base import StandardResponse

session_router = APIRouter(prefix="/session", tags=["session"])


@session_router.post("/new", response_model=StandardResponse, dependencies=[Depends(sk_auth)])
async def new_session(uid: int = Depends(sk_auth)):
    with session() as conn:
        if not conn.is_active:
            conn.rollback()

        _session = SessionSchema(uid=uid)
        conn.add(_session)
        conn.commit()
        data = {"session_id": _session.session_id, "create_at": _session.create_at}

    return StandardResponse(code=0, status="success", message="Create session successfully", data=data)

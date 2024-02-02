import datetime
from typing import Tuple

from fastapi import APIRouter, Depends
from sqlalchemy import or_

from internal.middleware.jwt import encode_token
from internal.middleware.mysql import session
from internal.middleware.mysql.model import ApiKeySchema, SessionSchema, UserSchema

from ...auth import jwt_auth, sk_auth
from ...model.response import StandardResponse
from ...model.request import UserRequest

user_router = APIRouter(prefix="/user", tags=["user"])


@user_router.post("/register", response_model=StandardResponse)
def register_user(request: UserRequest) -> StandardResponse:
    with session() as conn:
        query = conn.query(UserSchema.user).filter(UserSchema.user == request.user)
        exist_user = query.first()

    if exist_user:
        return StandardResponse(code=1, status="error", message="User already exist")

    with session() as conn:
        if not conn.is_active:
            conn.rollback()
            conn.close()
        else:
            conn.commit()

        user = UserSchema(user=request.user, password=request.password)
        conn.add(user)
        conn.commit()

    return StandardResponse(code=0, status="success", message="Register successfully")


@user_router.post("/login", response_model=StandardResponse)
def login_user(request: UserRequest) -> StandardResponse:
    with session() as conn:
        if not conn.is_active:
            conn.rollback()
            conn.close()
        else:
            conn.commit()

        query = (
            conn.query(UserSchema.uid, UserSchema.is_admin).filter(UserSchema.user == request.user).filter(UserSchema.password == request.password)
        )
        result = query.first()

    if not result:
        return StandardResponse(code=1, status="error", message="User not exist or password incorrect")

    (uid, is_admin) = result

    data = {"uid": uid, "token": encode_token(uid=uid, level=is_admin)}

    return StandardResponse(code=0, status="success", message="Login successfully", data=data)


@user_router.get("/{uid}/keys", response_model=StandardResponse, dependencies=[Depends(jwt_auth)])
def get_api_key_list(uid: int, info: Tuple[int, int] = Depends(jwt_auth)) -> StandardResponse:
    _uid, level = info
    if not (level or _uid == uid):
        return StandardResponse(code=1, status="error", message="No permission")
    with session() as conn:
        if not conn.is_active:
            conn.rollback()
            conn.close()
        else:
            conn.commit()

        query = (
            conn.query(ApiKeySchema.ak_id, ApiKeySchema.api_key_secret, ApiKeySchema.create_at, ApiKeySchema.delete_at)
            .filter(or_(ApiKeySchema.uid == uid, level == 1))
            .filter(or_(ApiKeySchema.delete_at.is_(None), ApiKeySchema.delete_at > datetime.datetime.now()))
        )
        result = query.all()

    fields = ("api_key_id", "api_key_secret", "create_at", "expire_at")
    data = {"uid": uid, "api_key_list": [dict(zip(fields, row)) for row in result]}

    return StandardResponse(code=0, status="success", message="List api key successfully", data=data)


@user_router.get("/{uid}/sessions", response_model=StandardResponse, dependencies=[Depends(sk_auth)])
async def list_session(uid: int, page_id: int = 0, per_page_num: int = 20, info: Tuple[int, int] = Depends(sk_auth)):
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

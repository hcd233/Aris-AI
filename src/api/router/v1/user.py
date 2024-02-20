import datetime
from typing import Tuple

from fastapi import APIRouter, Depends
from sqlalchemy import or_

from src.middleware.jwt import encode_token
from src.middleware.mysql import session
from src.middleware.mysql.model import ApiKeySchema, UserSchema

from ...auth import jwt_auth
from ...model.request import UserRequest
from ...model.response import StandardResponse

user_router = APIRouter(prefix="/user", tags=["user"])


@user_router.post("/register", response_model=StandardResponse)
def register_user(request: UserRequest) -> StandardResponse:
    with session() as conn:
        query = conn.query(UserSchema.user_name).filter(UserSchema.user_name == request.user_name)
        exist_user = query.first()

    if exist_user:
        return StandardResponse(code=1, status="error", message="User already exist")

    with session() as conn:
        if not conn.is_active:
            conn.rollback()
            conn.close()
        else:
            conn.commit()

        user = UserSchema(user_name=request.user_name, password=request.password)
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
            conn.query(UserSchema.uid, UserSchema.is_admin)
            .filter(UserSchema.user_name == request.user_name)
            .filter(UserSchema.password == request.password)
        )
        result = query.first()

    if not result:
        return StandardResponse(code=1, status="error", message="User not exist or password incorrect")

    (uid, is_admin) = result

    data = {"uid": uid, "token": encode_token(uid=uid, level=is_admin)}

    return StandardResponse(code=0, status="success", data=data)
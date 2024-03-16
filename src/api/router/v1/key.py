import datetime
from typing import Tuple

from fastapi import APIRouter, Depends
from sqlalchemy import or_

from src.middleware.mysql import session
from src.middleware.mysql.models import ApiKeySchema, UserSchema

from ...auth import jwt_auth
from ...model.response import StandardResponse

key_router = APIRouter(prefix="/key", tags=["key"])


@key_router.post("", response_model=StandardResponse, dependencies=[Depends(jwt_auth)])
def generate_api_key(info: Tuple[int, int] = Depends(jwt_auth)) -> StandardResponse:
    uid, _ = info
    with session() as conn:
        if not conn.is_active:
            conn.rollback()
            conn.close()
        else:
            conn.commit()

        query = conn.query(UserSchema.ak_num).filter(UserSchema.uid == uid)
        result = query.first()

    if not result:
        return StandardResponse(code=1, status="error", message="Token invalid")

    (ak_num,) = result

    if ak_num >= 5:
        return StandardResponse(code=1, status="error", message="You can only generate 5 api keys at most")

    with session() as conn:
        if not conn.is_active:
            conn.rollback()
            conn.close()
        else:
            conn.commit()

        api_key = ApiKeySchema(uid=uid)
        conn.add(api_key)
        conn.query(UserSchema).filter(UserSchema.uid == uid).filter(
            or_(UserSchema.delete_at.is_(None), datetime.datetime.now() < UserSchema.delete_at)
        ).update({"ak_num": UserSchema.ak_num + 1})
        conn.commit()
        data = {
            "api_key_id": api_key.ak_id,
            "api_key_secret": api_key.api_key_secret,
            "create_at": api_key.create_at,
            "expire_at": api_key.delete_at,
        }

    return StandardResponse(
        code=0,
        status="success",
        message="Generate api key successfully. Please save it carefully.",
        data=data,
    )


@key_router.get("/keys", response_model=StandardResponse, dependencies=[Depends(jwt_auth)])
def get_api_key_list(uid: int = None, info: Tuple[int, int] = Depends(jwt_auth)) -> StandardResponse:
    _uid, level = info
    if not level and uid and uid != _uid:
        return StandardResponse(code=1, status="error", message="No permission")
    if not uid:
        uid = _uid
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

    return StandardResponse(code=0, status="success", data=data)


@key_router.delete("/{api_key_id}/delete", response_model=StandardResponse, dependencies=[Depends(jwt_auth)])
def delete_api_key(uid: int, api_key_id: int, info: Tuple[int, int] = Depends(jwt_auth)) -> StandardResponse:
    _uid, level = info
    if not (level or _uid == uid):
        return StandardResponse(code=1, status="error", message="No permission")

    with session() as conn:
        if not conn.is_active:
            conn.rollback()
            conn.close()
        else:
            conn.commit()
        query = conn.query(ApiKeySchema.api_key_secret).filter(ApiKeySchema.ak_id == api_key_id)
        result = query.first()

    if not result:
        return StandardResponse(code=1, status="error", message="Key not exist")

    with session() as conn:
        if not conn.is_active:
            conn.rollback()
            conn.close()
        else:
            conn.commit()

        conn.query(ApiKeySchema).filter(ApiKeySchema.ak_id == api_key_id).update({ApiKeySchema.delete_at: datetime.datetime.now()})
        conn.query(UserSchema).filter(UserSchema.uid == uid).filter(
            or_(UserSchema.delete_at.is_(None), datetime.datetime.now() < UserSchema.delete_at)
        ).update({UserSchema.ak_num: UserSchema.ak_num - 1})
        conn.commit()

    return StandardResponse(code=0, status="success", message="Delete api key successfully")

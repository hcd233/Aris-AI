import datetime
from typing import Tuple

from fastapi import APIRouter, Depends
from sqlalchemy import or_

from internal.middleware.mysql import session
from internal.middleware.mysql.model import ApiKeySchema, UserSchema

from ...auth import jwt_auth
from ...model.base import StandardResponse
from ...model.v1 import UidRequest

key_router = APIRouter(prefix="/key", tags=["key"])


@key_router.post("/newSecretKey", response_model=StandardResponse, dependencies=[Depends(jwt_auth)])
def generate_api_key(request: UidRequest, info: Tuple[int, int] = Depends(jwt_auth)) -> StandardResponse:
    _uid, _ = info
    if _uid != request.uid:
        return StandardResponse(code=1, status="error", message="No permission")
    with session() as conn:
        if not conn.is_active:
            conn.rollback()
            conn.close()
        else:
            conn.commit()

        query = conn.query(UserSchema.ak_num).filter(UserSchema.uid == request.uid)
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

        api_key = ApiKeySchema(uid=request.uid)
        conn.add(api_key)
        conn.query(UserSchema).filter(UserSchema.uid == request.uid).filter(
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

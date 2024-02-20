from datetime import datetime
from typing import Optional, Tuple

from fastapi import Depends, HTTPException, status
from sqlalchemy import or_

from src.middleware.mysql import session
from src.middleware.mysql.model import ApiKeySchema, UserSchema

from .base import bearer_scheme


async def sk_auth(
    bearer_auth: Optional[str] = Depends(bearer_scheme),
) -> Tuple[int, int]:
    with session() as conn:
        query = (
            conn.query(ApiKeySchema.uid)
            .filter(ApiKeySchema.api_key_secret == bearer_auth.credentials)
            .filter(or_(ApiKeySchema.delete_at.is_(None), datetime.now() < ApiKeySchema.delete_at))
        )
        result = query.first()
    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid secret key",
            headers={"WWW-Authenticate": "Bearer"},
        )

    (uid,) = result

    with session() as conn:
        query = conn.query(UserSchema.is_admin).filter(UserSchema.uid == uid)
        result = query.first()

    (level,) = result
    return uid, level

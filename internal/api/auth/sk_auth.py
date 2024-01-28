from typing import Optional

from fastapi import Depends, HTTPException, status

from internal.middleware.mysql import session
from internal.middleware.mysql.models import ApiKeySchema

from .base import bearer_scheme


async def sk_auth(
    bearer_auth: Optional[str] = Depends(bearer_scheme),
) -> int:
    with session() as conn:
        query = conn.query(ApiKeySchema.uid).filter(ApiKeySchema.key == bearer_auth.credentials)
        result = query.first()
    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid secret key",
            headers={"WWW-Authenticate": "Bearer"},
        )

    (uid,) = result
    return uid

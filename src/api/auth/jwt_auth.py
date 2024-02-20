from typing import Optional, Tuple

from fastapi import Depends, HTTPException, status
from jwt import ExpiredSignatureError, InvalidSignatureError, InvalidTokenError

from src.logger import logger
from src.middleware.jwt import decode_token

from .base import bearer_scheme


async def jwt_auth(
    bearer_auth: Optional[str] = Depends(bearer_scheme),
) -> Tuple[int, int]:
    try:
        uid, level = decode_token(bearer_auth.credentials)
    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
            headers={"WWW-Authenticate": "Bearer"},
        )

    except (InvalidSignatureError, InvalidTokenError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        logger.error(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return uid, level

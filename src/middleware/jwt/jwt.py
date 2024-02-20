import time
from typing import Any, Dict, Tuple
from uuid import uuid4

import jwt
from pydantic import BaseModel

from src.config import JWT_TOKEN_ALGORITHM, JWT_TOKEN_EXPIRE_TIME, JWT_TOKEN_SECRET


class Claim(BaseModel):
    uid: int
    uuid: str = str(uuid4())
    level: int = 0
    exp: float = time.time() + JWT_TOKEN_EXPIRE_TIME


def encode_token(uid: int, level: int = 0) -> str:
    claim = Claim(uid=uid, level=level).model_dump()
    return jwt.encode(claim, JWT_TOKEN_SECRET, algorithm=JWT_TOKEN_ALGORITHM)


def decode_token(token: str) -> Tuple[int, int]:
    claim: Dict[str, Any] = jwt.decode(token, JWT_TOKEN_SECRET, algorithms=[JWT_TOKEN_ALGORITHM])
    uid, level = claim.get("uid"), claim.get("level")
    return uid, level

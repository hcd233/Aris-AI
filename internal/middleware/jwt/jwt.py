import time
from typing import Any, Dict
from uuid import uuid4

import jwt
from pydantic import BaseModel

from internal.config import JWT_TOKEN_ALGORITHM, JWT_TOKEN_EXPIRE_TIME, JWT_TOKEN_SECRET


class Claim(BaseModel):
    uid: int
    uuid: str = str(uuid4())
    exp: float = time.time() + JWT_TOKEN_EXPIRE_TIME


def encode_token(uid: int) -> str:
    claim = Claim(uid=uid).model_dump()
    return jwt.encode(claim, JWT_TOKEN_SECRET, algorithm=JWT_TOKEN_ALGORITHM)


def decode_token(token: str) -> int:
    claim: Dict[str, Any] = jwt.decode(token, JWT_TOKEN_SECRET, algorithms=[JWT_TOKEN_ALGORITHM])
    uid = claim.get("uid")
    return uid

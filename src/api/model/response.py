from typing import Any, Dict, Literal

from pydantic import BaseModel


class StandardResponse(BaseModel):
    code: int
    status: Literal["success", "error"]
    message: str | None = None
    data: Dict[str, Any] | None = None


class SSEResponse(BaseModel):
    status: str
    delta: str
    extras: Dict[str, Any]

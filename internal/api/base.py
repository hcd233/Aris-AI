from typing import Any, Dict, Literal

from pydantic import BaseModel


class StandardResponse(BaseModel):
    status: Literal["success", "error"]
    message: str | None
    data: Dict[str, Any] | None

from typing import Any, Dict, Literal

from fastapi import FastAPI
from internal.logger import logger
from pydantic import BaseModel

from internal.config import DEBUG_MODE


class StandardResponse(BaseModel):
    status: Literal["success", "error"]
    message: str | None
    data: Dict[str, Any] | None


app = FastAPI(
    title="Alice AI API",
    version="0.1.0",
    # forbidden to route any docs
    redoc_url="/redoc" if DEBUG_MODE else None,
    docs_url="/docs" if DEBUG_MODE else None,
    openapi_url="/openapi.json" if DEBUG_MODE else None,
)
logger.info("App initialized")


@app.get("/", tags=["root"])
async def root():
    return StandardResponse(status="success", message="Hello World!", data=None)

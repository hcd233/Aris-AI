from fastapi import APIRouter

from .key import key_router
from .model import llm_router, model_router
from .session import session_router
from .user import user_router

model_router.include_router(llm_router)

v1_router = APIRouter(prefix="/v1", tags=["v1"])

v1_router.include_router(user_router)
v1_router.include_router(key_router)
v1_router.include_router(model_router)
v1_router.include_router(session_router)

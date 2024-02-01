from fastapi import APIRouter

from .key import key_router
from .model import model_router
from .session import session_router
from .user import user_router

v1_router = APIRouter(prefix="/v1")

v1_router.include_router(user_router)
v1_router.include_router(key_router)
v1_router.include_router(model_router)
v1_router.include_router(session_router)

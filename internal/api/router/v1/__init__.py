from fastapi import APIRouter

from .session import session_router
from .user import user_router

v1_router = APIRouter(prefix="/v1")
v1_router.include_router(user_router)
v1_router.include_router(session_router)

from fastapi import APIRouter

from .key import key_router
from .model import model_router
from .oauth2 import oauth2_router
from .session import session_router
from .vectordb import vector_db_router

v1_router = APIRouter(prefix="/v1", tags=["v1"])

v1_router.include_router(key_router)
v1_router.include_router(model_router)
v1_router.include_router(vector_db_router)
v1_router.include_router(session_router)
v1_router.include_router(oauth2_router)

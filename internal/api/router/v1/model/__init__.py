from fastapi import APIRouter

from .embedding import embedding_router
from .llm import llm_router

model_router = APIRouter(prefix="/model", tags=["model"])

model_router.include_router(llm_router)
model_router.include_router(embedding_router)

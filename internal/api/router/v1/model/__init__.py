from .llm import llm_router
from fastapi import APIRouter

model_router = APIRouter(prefix="/model", tags=["model"])
model_router.include_router(llm_router)
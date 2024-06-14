from fastapi import APIRouter

from .github import github_router

oauth2_router = APIRouter(prefix="/oauth2", tags=["oauth2"])

oauth2_router.include_router(github_router)

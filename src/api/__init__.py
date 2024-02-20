from fastapi import FastAPI

from src.config import DEBUG_MODE
from src.logger import logger
from src.middleware.logger import LoggerMiddleWare

from .router import root_router, v1_router


def create_app() -> FastAPI:
    app = FastAPI(
        title="Alice AI API",
        version="0.1.0",
        # forbidden to route any docs
        redoc_url="/redoc" if DEBUG_MODE else None,
        docs_url="/docs" if DEBUG_MODE else None,
        openapi_url="/openapi.json" if DEBUG_MODE else None,
    )

    # add routers
    app.include_router(root_router)
    app.include_router(v1_router)

    # add middlewares
    app.add_middleware(LoggerMiddleWare)

    logger.info("Init app successfully")
    return app

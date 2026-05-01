from __future__ import annotations

from fastapi import FastAPI

from app.api.v1.router import api_v1_router
from app.core.exception_handlers import install_exception_handlers
from app.modules.ai.routes import router as internal_ai_router


def create_app() -> FastAPI:
    app = FastAPI(title="Lusterko API", version="0.1.0")
    install_exception_handlers(app)
    app.include_router(api_v1_router)
    app.include_router(internal_ai_router)
    return app


app = create_app()

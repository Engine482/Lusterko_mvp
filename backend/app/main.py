from __future__ import annotations

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_v1_router
from app.core.exception_handlers import install_exception_handlers
from app.core.logging import configure_logging
from app.modules.ai.routes import router as internal_ai_router


def _cors_origins() -> list[str]:
    """Allowed origins for credentialed cross-origin XHR. CSV in env so the
    same image can serve dev and prod (e.g. on Render the frontend lives on
    a different subdomain than the backend, so CORS is mandatory for the
    `credentials: include` API client to read responses)."""

    raw = os.environ.get(
        "CORS_ALLOWED_ORIGINS",
        "http://127.0.0.1:3001,http://localhost:3001",
    )
    return [o.strip() for o in raw.split(",") if o.strip()]


def create_app() -> FastAPI:
    configure_logging()
    app = FastAPI(title="Lusterko API", version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_cors_origins(),
        allow_credentials=True,
        allow_methods=["GET", "POST", "PATCH", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization"],
    )
    install_exception_handlers(app)
    app.include_router(api_v1_router)
    app.include_router(internal_ai_router)
    return app


app = create_app()

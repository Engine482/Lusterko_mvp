from __future__ import annotations

from fastapi import APIRouter

from app.core.api_response import success_envelope
from app.modules.assessments.routes import router as soldier_router
from app.modules.auth.routes import router as auth_router
from app.modules.users.routes import router as admin_router

api_v1_router = APIRouter(prefix="/api/v1")
api_v1_router.include_router(auth_router)
api_v1_router.include_router(admin_router)
api_v1_router.include_router(soldier_router)


@api_v1_router.get("/health")
def health() -> dict[str, object]:
    return success_envelope({"status": "ok"})

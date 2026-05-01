from __future__ import annotations

from fastapi import APIRouter

from app.core.api_response import success_envelope

api_v1_router = APIRouter(prefix="/api/v1")


@api_v1_router.get("/health")
def health() -> dict[str, object]:
    return success_envelope({"status": "ok"})

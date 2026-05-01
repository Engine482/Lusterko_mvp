"""Internal AI API per `Lusterko_API_Contracts_v1.md` §8.

This endpoint is intended for backend-to-backend usage. It is protected by a
shared secret in the `X-Internal-Token` header (`INTERNAL_API_TOKEN` env). If
no token is configured the endpoint is disabled — never accept traffic with
an empty secret. The same parser is also called in-process from the daily
check-in flow, so this route is not on the hot path of normal usage.
"""

from __future__ import annotations

import os

from fastapi import APIRouter, Header, Response

from app.core.api_response import error_response, success_response
from app.modules.ai import parser
from pydantic import BaseModel, Field

router = APIRouter(prefix="/internal/ai", tags=["internal-ai"])


class AnalyzeCommentRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=300)


@router.post("/analyze-comment")
def analyze_comment(
    payload: AnalyzeCommentRequest,
    x_internal_token: str | None = Header(default=None, alias="X-Internal-Token"),
) -> Response:
    expected = os.environ.get("INTERNAL_API_TOKEN", "").strip()
    if not expected:
        return error_response("FORBIDDEN", "Internal AI endpoint disabled.")
    if not x_internal_token or x_internal_token != expected:
        return error_response("FORBIDDEN", "Invalid internal token.")

    result = parser.analyze_comment(payload.text)
    return success_response(
        {
            "language_detected": result.language_detected,
            "has_signal": result.has_signal,
            "markers": result.markers,
            "text_risk_level": result.text_risk_level,
            "confidence_score": result.confidence_score,
            "summary_for_system": result.summary_for_system,
            "parse_status": result.parse_status,
            "raw_model_name": result.raw_model_name,
        }
    )

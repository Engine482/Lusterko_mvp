"""Standard API envelope and error codes per `Lusterko_API_Contracts_v1.md` §1.

All HTTP responses MUST use these helpers so the contract stays uniform.
"""

from __future__ import annotations

from typing import Any, Final, Literal

from fastapi import status
from fastapi.responses import JSONResponse

ErrorCode = Literal[
    "UNAUTHORIZED",
    "FORBIDDEN",
    "INVALID_INVITE",
    "INVITE_EXPIRED",
    "INVALID_RESET_TOKEN",
    "RESET_TOKEN_EXPIRED",
    "WEAK_PASSWORD",
    "ROLE_SELECTION_REQUIRED",
    "VALIDATION_ERROR",
    "NOT_FOUND",
    "CONFLICT",
    "DAILY_ALREADY_SUBMITTED",
    "BASELINE_NOT_COMPLETE",
    "INVALID_ACTIVE_ROLE",
    "INSUFFICIENT_SCOPE",
    "AI_PARSE_FAILED",
    "CASE_INVALID_TRANSITION",
    "INTERNAL_ERROR",
]

DEFAULT_STATUS_FOR_CODE: Final[dict[ErrorCode, int]] = {
    "UNAUTHORIZED": status.HTTP_401_UNAUTHORIZED,
    "FORBIDDEN": status.HTTP_403_FORBIDDEN,
    "INVALID_INVITE": status.HTTP_400_BAD_REQUEST,
    "INVITE_EXPIRED": status.HTTP_400_BAD_REQUEST,
    "INVALID_RESET_TOKEN": status.HTTP_400_BAD_REQUEST,
    "RESET_TOKEN_EXPIRED": status.HTTP_400_BAD_REQUEST,
    "WEAK_PASSWORD": status.HTTP_400_BAD_REQUEST,
    "ROLE_SELECTION_REQUIRED": status.HTTP_409_CONFLICT,
    "VALIDATION_ERROR": status.HTTP_422_UNPROCESSABLE_CONTENT,
    "NOT_FOUND": status.HTTP_404_NOT_FOUND,
    "CONFLICT": status.HTTP_409_CONFLICT,
    "DAILY_ALREADY_SUBMITTED": status.HTTP_409_CONFLICT,
    "BASELINE_NOT_COMPLETE": status.HTTP_409_CONFLICT,
    "INVALID_ACTIVE_ROLE": status.HTTP_403_FORBIDDEN,
    "INSUFFICIENT_SCOPE": status.HTTP_403_FORBIDDEN,
    "AI_PARSE_FAILED": status.HTTP_502_BAD_GATEWAY,
    "CASE_INVALID_TRANSITION": status.HTTP_409_CONFLICT,
    "INTERNAL_ERROR": status.HTTP_500_INTERNAL_SERVER_ERROR,
}


def success_envelope(data: Any) -> dict[str, Any]:
    return {"success": True, "data": data}


def error_envelope(
    code: ErrorCode,
    message: str,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {"code": code, "message": message}
    if details is not None:
        payload["details"] = details
    return {"success": False, "error": payload}


def success_response(data: Any, http_status: int = status.HTTP_200_OK) -> JSONResponse:
    return JSONResponse(content=success_envelope(data), status_code=http_status)


def error_response(
    code: ErrorCode,
    message: str,
    details: dict[str, Any] | None = None,
    http_status: int | None = None,
) -> JSONResponse:
    return JSONResponse(
        content=error_envelope(code, message, details),
        status_code=http_status or DEFAULT_STATUS_FOR_CODE[code],
    )

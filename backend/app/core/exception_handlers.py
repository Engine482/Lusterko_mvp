"""Global exception → standard error envelope mappers.

Keeps the response shape consistent with `Lusterko_API_Contracts_v1.md` §1.3
even when FastAPI's defaults would produce a non-envelope JSON.
"""

from __future__ import annotations

from typing import cast

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.api_response import ErrorCode, error_envelope
from app.modules.auth.dependencies import AuthError


def _auth_error_handler(_: Request, exc: AuthError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content=error_envelope(cast(ErrorCode, exc.code), exc.message),
    )


def _validation_error_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        content=error_envelope(
            "VALIDATION_ERROR",
            "Invalid request payload.",
            details={"errors": exc.errors()},
        ),
    )


def install_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(AuthError, _auth_error_handler)  # type: ignore[arg-type]
    app.add_exception_handler(RequestValidationError, _validation_error_handler)  # type: ignore[arg-type]

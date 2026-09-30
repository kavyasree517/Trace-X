"""Uniform API error response models and exceptions."""

from typing import Any

from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict
from slowapi.errors import RateLimitExceeded


class ErrorDetail(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str
    message: str
    field: str | None = None
    request_id: str | None = None


class ErrorResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    error: ErrorDetail


class APIError(Exception):
    """Base application exception with uniform error payload."""

    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        field: str | None = None,
    ) -> None:
        self.code = code
        self.message = message
        self.status_code = status_code
        self.field = field
        super().__init__(message)


def get_request_id(request: Request) -> str | None:
    return getattr(request.state, "request_id", request.headers.get("X-Request-ID"))


async def api_error_handler(request: Request, exc: APIError) -> JSONResponse:
    request_id = get_request_id(request)
    payload = ErrorResponse(
        error=ErrorDetail(
            code=exc.code,
            message=exc.message,
            field=exc.field,
            request_id=request_id,
        )
    )
    return JSONResponse(status_code=exc.status_code, content=payload.model_dump(exclude_none=True))


async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    request_id = get_request_id(request)
    first_err: dict[str, Any] = exc.errors()[0] if exc.errors() else {}
    loc = first_err.get("loc", [])
    field = str(loc[-1]) if loc else None
    msg = first_err.get("msg", "Validation error")
    err_type = first_err.get("type", "")

    code = "invalid_input"
    if field == "address":
        code = "invalid_address"
    elif field == "chain":
        code = "invalid_chain"
    elif field in ("tx_hash", "reported_tx_hash"):
        code = "invalid_tx_hash"
    elif field in ("incident_date", "date"):
        code = "invalid_date"
    elif "extra_forbidden" in err_type:
        code = "limit_exceeded"

    payload = ErrorResponse(
        error=ErrorDetail(
            code=code,
            message=msg,
            field=field,
            request_id=request_id,
        )
    )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=payload.model_dump(exclude_none=True),
    )


async def rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    request_id = get_request_id(request)
    headers = {}
    retry_after = getattr(exc, "retry_after", None)
    if retry_after:
        headers["Retry-After"] = str(retry_after)

    payload = ErrorResponse(
        error=ErrorDetail(
            code="rate_limited",
            message="Rate limit exceeded. Please try again later.",
            field=None,
            request_id=request_id,
        )
    )
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content=payload.model_dump(exclude_none=True),
        headers=headers,
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    request_id = get_request_id(request)
    payload = ErrorResponse(
        error=ErrorDetail(
            code="internal_error",
            message="An unexpected error occurred. Please contact system support.",
            field=None,
            request_id=request_id,
        )
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=payload.model_dump(exclude_none=True),
    )

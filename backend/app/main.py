"""Main FastAPI application entrypoint."""

import uuid
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from app.api.errors import (
    APIError,
    api_error_handler,
    rate_limit_handler,
    unhandled_exception_handler,
    validation_error_handler,
)
from app.api.v1.router import api_v1_router
from app.core.config import get_settings
from app.core.logging import get_logger, setup_logging
from app.core.rate_limit import limiter

logger = get_logger("app.main")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    settings = get_settings()
    setup_logging(settings.LOG_LEVEL)
    logger.info(
        "Application starting",
        app_version=settings.APP_VERSION,
        environment=settings.APP_ENV,
        demo_mode=settings.DEMO_MODE,
        adapter=settings.DATA_ADAPTER,
    )
    yield
    logger.info("Application shutting down")


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Enforce strict institutional security headers."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; frame-ancestors 'none'; object-src 'none';"
        )
        return response


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Assign or preserve unique correlation request ID."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        req_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request.state.request_id = req_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = req_id
        return response


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="TRACE-X API",
        description="Trust-aware Risk Analysis and Connection Evidence for Cryptocurrency Exchanges",
        version=settings.APP_VERSION,
        lifespan=lifespan,
        docs_url="/docs" if settings.APP_ENV != "production" else None,
        redoc_url="/redoc" if settings.APP_ENV != "production" else None,
    )

    app.state.limiter = limiter

    # Middlewares
    app.add_middleware(RequestIDMiddleware)
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
    )

    # Exception handlers
    app.add_exception_handler(APIError, api_error_handler)  # type: ignore[arg-type]
    app.add_exception_handler(RequestValidationError, validation_error_handler)  # type: ignore[arg-type]
    app.add_exception_handler(RateLimitExceeded, rate_limit_handler)  # type: ignore[arg-type]
    app.add_exception_handler(Exception, unhandled_exception_handler)

    # Routers
    app.include_router(api_v1_router, prefix="/api/v1")

    return app


app = create_app()

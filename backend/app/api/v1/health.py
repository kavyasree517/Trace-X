"""Health check and service status endpoints."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.core.config import Settings, get_settings

router = APIRouter(tags=["Health"])


class HealthResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: str
    app_version: str
    environment: str


class ReadinessResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: str
    database: str
    adapter: str


@router.get("/health", response_model=HealthResponse)
async def check_health(
    settings: Settings = Depends(get_settings),
) -> HealthResponse:
    """Basic service liveness check."""
    return HealthResponse(
        status="ok",
        app_version=settings.APP_VERSION,
        environment=settings.APP_ENV,
    )


@router.get("/health/ready", response_model=ReadinessResponse)
async def check_readiness(
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> ReadinessResponse:
    """Service readiness check verifying database connectivity."""
    db_status = "connected"
    try:
        await db.execute(text("SELECT 1"))
    except Exception:
        db_status = "unavailable"
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is currently unavailable",
        )

    return ReadinessResponse(
        status="ready",
        database=db_status,
        adapter=settings.DATA_ADAPTER,
    )


@router.get("/config", response_model=dict[str, Any])
async def get_redacted_config(
    settings: Settings = Depends(get_settings),
) -> dict[str, Any]:
    """Inspect sanitized configuration in non-production environments."""
    if settings.APP_ENV == "production":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Config endpoint disabled in production",
        )
    return settings.redacted_dict()

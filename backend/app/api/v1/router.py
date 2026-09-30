"""API v1 master router aggregating domain endpoints."""

from fastapi import APIRouter

from app.api.v1.cases import router as cases_router
from app.api.v1.health import router as health_router
from app.api.v1.labels import router as labels_router

api_v1_router = APIRouter()

api_v1_router.include_router(health_router)
api_v1_router.include_router(cases_router)
api_v1_router.include_router(labels_router)

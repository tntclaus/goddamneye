"""System and health check endpoints."""

from datetime import datetime

from fastapi import APIRouter
from pydantic import BaseModel

from backend.config import get_settings

router = APIRouter()
settings = get_settings()


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    version: str
    timestamp: datetime


class SystemInfo(BaseModel):
    """System information response."""

    app_name: str
    version: str
    debug: bool
    storage_path: str
    database_url: str


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Health check endpoint for monitoring and load balancers."""
    return HealthResponse(
        status="healthy",
        version=settings.app_version,
        timestamp=datetime.now(),
    )


@router.get("/system/info", response_model=SystemInfo)
async def system_info() -> SystemInfo:
    """Get system information."""
    # Mask database URL for security
    db_url = settings.database_url
    if "@" in db_url:
        # Mask password in connection string
        parts = db_url.split("@")
        db_url = parts[0].rsplit(":", 1)[0] + ":***@" + parts[1]

    return SystemInfo(
        app_name=settings.app_name,
        version=settings.app_version,
        debug=settings.debug,
        storage_path=str(settings.storage_path),
        database_url=db_url,
    )

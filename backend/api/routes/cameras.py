"""Camera CRUD API endpoints."""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.database import get_db
from backend.models.camera import Camera
from backend.services.camera_manager import camera_manager
from pydantic import BaseModel

from backend.schemas.camera import (
    CameraCreate,
    CameraDiscovered,
    CameraResponse,
    CameraUpdate,
)

router = APIRouter()
logger = logging.getLogger(__name__)

DbSession = Annotated[AsyncSession, Depends(get_db)]


@router.get("", response_model=list[CameraResponse])
async def list_cameras(
    db: DbSession,
    enabled_only: bool = False,
) -> list[Camera]:
    """List all cameras."""
    query = select(Camera).order_by(Camera.name)
    if enabled_only:
        query = query.where(Camera.enabled == True)  # noqa: E712

    result = await db.execute(query)
    return list(result.scalars().all())


@router.get("/{camera_id}", response_model=CameraResponse)
async def get_camera(
    camera_id: str,
    db: DbSession,
) -> Camera:
    """Get a specific camera by ID."""
    result = await db.execute(select(Camera).where(Camera.id == camera_id))
    camera = result.scalar_one_or_none()

    if not camera:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Camera {camera_id} not found",
        )

    return camera


@router.post("", response_model=CameraResponse, status_code=status.HTTP_201_CREATED)
async def create_camera(
    camera_in: CameraCreate,
    db: DbSession,
) -> Camera:
    """Create a new camera."""
    # Check for duplicate name
    existing = await db.execute(select(Camera).where(Camera.name == camera_in.name))
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Camera with name '{camera_in.name}' already exists",
        )

    # Create camera
    camera_data = camera_in.model_dump(exclude={"password"})

    # Handle password encryption (for now, store as-is; TODO: encrypt)
    if camera_in.password:
        camera_data["password_encrypted"] = camera_in.password.get_secret_value()

    camera = Camera(**camera_data)
    db.add(camera)
    await db.flush()
    await db.refresh(camera)

    logger.info(f"Created camera: {camera.name} (ID: {camera.id})")

    # Auto-start stream if camera is enabled
    if camera.enabled:
        logger.info(f"Auto-starting stream for new camera: {camera.name}")
        try:
            await camera_manager.start_camera(camera)
        except Exception as e:
            logger.warning(f"Failed to auto-start stream for {camera.name}: {e}")

    return camera


@router.put("/{camera_id}", response_model=CameraResponse)
async def update_camera(
    camera_id: str,
    camera_in: CameraUpdate,
    db: DbSession,
) -> Camera:
    """Update an existing camera."""
    result = await db.execute(select(Camera).where(Camera.id == camera_id))
    camera = result.scalar_one_or_none()

    if not camera:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Camera {camera_id} not found",
        )

    # Update fields that are provided
    update_data = camera_in.model_dump(exclude_unset=True, exclude={"password"})

    for field, value in update_data.items():
        setattr(camera, field, value)

    # Handle password update separately
    if camera_in.password is not None:
        camera.password_encrypted = camera_in.password.get_secret_value()

    await db.flush()
    await db.refresh(camera)

    logger.info(f"Updated camera: {camera.name} (ID: {camera.id})")
    return camera


@router.delete("/{camera_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_camera(
    camera_id: str,
    db: DbSession,
) -> None:
    """Delete a camera."""
    result = await db.execute(select(Camera).where(Camera.id == camera_id))
    camera = result.scalar_one_or_none()

    if not camera:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Camera {camera_id} not found",
        )

    # Stop stream first before deleting camera
    logger.info(f"Stopping stream for camera being deleted: {camera.name}")
    try:
        await camera_manager.stop_camera(camera_id)
    except Exception as e:
        logger.warning(f"Failed to stop stream for {camera.name}: {e}")

    await db.delete(camera)
    logger.info(f"Deleted camera: {camera.name} (ID: {camera.id})")


@router.post("/discover", response_model=list[CameraDiscovered])
async def discover_cameras(
    timeout: int = 5,
) -> list[CameraDiscovered]:
    """Discover cameras on the network using ONVIF WS-Discovery.

    Sends multicast discovery messages to find ONVIF-compliant cameras
    on the local network.
    """
    from backend.services.onvif_discovery import onvif_discovery

    logger.info(f"Camera discovery requested (timeout: {timeout}s)")
    return await onvif_discovery.discover(timeout=timeout)


class CameraProbeRequest(BaseModel):
    """Request body for camera probe."""
    host: str
    port: int = 80
    username: str | None = None
    password: str | None = None


class CameraProbeResponse(BaseModel):
    """Response from camera probe with stream options."""
    host: str
    port: int
    onvif_supported: bool
    name: str | None = None
    manufacturer: str | None = None
    model: str | None = None
    firmware_version: str | None = None
    serial_number: str | None = None
    streams: list[dict] = []  # [{name, url, description}]
    error: str | None = None


@router.post("/probe", response_model=CameraProbeResponse)
async def probe_camera(
    request: CameraProbeRequest,
) -> CameraProbeResponse:
    """Probe a camera by IP address to auto-detect ONVIF settings and stream URLs.

    This is the simplified setup flow:
    1. User provides IP + credentials
    2. We probe for ONVIF support and get available streams
    3. User selects stream and provides a name
    4. Camera is created with auto-configured settings
    """
    from backend.services.onvif_discovery import onvif_discovery
    import urllib.parse

    logger.info(f"Probing camera at {request.host}:{request.port}")

    # Try ONVIF probe first
    result = await onvif_discovery.probe_camera(
        request.host,
        request.port,
        request.username,
        request.password
    )

    if result and result.rtsp_urls:
        # ONVIF succeeded - return clean URLs without credentials
        # Credentials are stored separately and added by stream_worker at runtime
        streams = []
        for i, url in enumerate(result.rtsp_urls):
            stream_name = "Main Stream" if i == 0 else f"Sub Stream {i}"
            streams.append({
                "name": stream_name,
                "url": url,  # Clean URL without credentials
                "description": f"Profile {i + 1}" + (" (High Quality)" if i == 0 else " (Lower Quality)")
            })

        return CameraProbeResponse(
            host=request.host,
            port=request.port,
            onvif_supported=True,
            name=result.name,
            manufacturer=result.manufacturer,
            model=result.model,
            firmware_version=result.firmware_version,
            serial_number=result.serial_number,
            streams=streams,
        )

    # ONVIF failed - try common RTSP URL patterns
    logger.info(f"ONVIF probe failed, trying common RTSP patterns for {request.host}")

    common_paths = [
        "/media/video1",      # Common ONVIF path
        "/stream1",           # Generic
        "/cam/realmonitor",   # Dahua
        "/Streaming/Channels/101",  # Hikvision
        "/live/ch00_0",       # Some Chinese cameras
        "/h264Preview_01_main",  # Some IP cameras
        "/videoMain",         # Generic
    ]

    # Build clean URLs without credentials
    # Credentials are stored separately and added by stream_worker at runtime
    streams = []
    for path in common_paths:
        url = f"rtsp://{request.host}:554{path}"
        streams.append({
            "name": f"Try: {path}",
            "url": url,
            "description": "Common RTSP path - may or may not work"
        })

    return CameraProbeResponse(
        host=request.host,
        port=request.port,
        onvif_supported=False,
        name=f"Camera at {request.host}",
        streams=streams,
        error="ONVIF not available. Showing common RTSP URL patterns to try."
    )


@router.post("/{camera_id}/enable", response_model=CameraResponse)
async def enable_camera(
    camera_id: str,
    db: DbSession,
) -> Camera:
    """Enable a camera for streaming."""
    result = await db.execute(select(Camera).where(Camera.id == camera_id))
    camera = result.scalar_one_or_none()

    if not camera:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Camera {camera_id} not found",
        )

    camera.enabled = True
    await db.flush()
    await db.refresh(camera)

    logger.info(f"Enabled camera: {camera.name}")

    # Auto-start stream when camera is enabled
    logger.info(f"Auto-starting stream for enabled camera: {camera.name}")
    try:
        await camera_manager.start_camera(camera)
    except Exception as e:
        logger.warning(f"Failed to auto-start stream for {camera.name}: {e}")

    return camera


@router.post("/{camera_id}/disable", response_model=CameraResponse)
async def disable_camera(
    camera_id: str,
    db: DbSession,
) -> Camera:
    """Disable a camera (stop streaming and recording)."""
    result = await db.execute(select(Camera).where(Camera.id == camera_id))
    camera = result.scalar_one_or_none()

    if not camera:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Camera {camera_id} not found",
        )

    # Stop stream first
    logger.info(f"Stopping stream for disabled camera: {camera.name}")
    try:
        await camera_manager.stop_camera(camera_id)
    except Exception as e:
        logger.warning(f"Failed to stop stream for {camera.name}: {e}")

    camera.enabled = False
    await db.flush()
    await db.refresh(camera)

    logger.info(f"Disabled camera: {camera.name}")
    return camera

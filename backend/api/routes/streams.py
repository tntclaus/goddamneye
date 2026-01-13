"""Video streaming endpoints."""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import get_settings
from backend.core.database import get_db
from backend.models.camera import Camera
from backend.services.camera_manager import camera_manager

router = APIRouter()
logger = logging.getLogger(__name__)
settings = get_settings()

DbSession = Annotated[AsyncSession, Depends(get_db)]


class StreamInfo(BaseModel):
    """Information about a camera stream."""

    camera_id: str
    camera_name: str | None = None
    is_running: bool
    is_recording: bool
    hls_url: str | None = None
    restart_count: int = 0
    pid: int | None = None


class StreamStatus(BaseModel):
    """Status of all streams."""

    active_streams: int
    streams: list[StreamInfo]


@router.get("/status", response_model=StreamStatus)
async def get_streams_status() -> StreamStatus:
    """Get status of all active streams."""
    statuses = camera_manager.get_all_statuses()

    return StreamStatus(
        active_streams=camera_manager.active_streams,
        streams=[StreamInfo(**s) for s in statuses],
    )


@router.get("/{camera_id}/status", response_model=StreamInfo)
async def get_stream_status(camera_id: str) -> StreamInfo:
    """Get status of a specific camera stream."""
    status = camera_manager.get_camera_status(camera_id)
    return StreamInfo(**status)


@router.post("/{camera_id}/start", response_model=StreamInfo)
async def start_stream(camera_id: str, db: DbSession) -> StreamInfo:
    """Start streaming for a camera.

    Creates FFmpeg process to convert RTSP to HLS for browser playback.
    Also starts recording if enabled for the camera.
    """
    # Get camera from database
    result = await db.execute(select(Camera).where(Camera.id == camera_id))
    camera = result.scalar_one_or_none()

    if not camera:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Camera {camera_id} not found",
        )

    if not camera.enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Camera {camera.name} is disabled. Enable it first.",
        )

    # Start the camera stream
    success = await camera_manager.start_camera(camera)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start stream for camera {camera.name}. Check logs for details.",
        )

    # Return current status
    status_dict = camera_manager.get_camera_status(camera_id)
    return StreamInfo(**status_dict)


@router.post("/{camera_id}/stop", response_model=StreamInfo)
async def stop_stream(camera_id: str, db: DbSession) -> StreamInfo:
    """Stop streaming for a camera.

    Stops the FFmpeg process and HLS output. Recording also stops.
    """
    # Verify camera exists
    result = await db.execute(select(Camera).where(Camera.id == camera_id))
    camera = result.scalar_one_or_none()

    if not camera:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Camera {camera_id} not found",
        )

    # Stop the camera stream
    await camera_manager.stop_camera(camera_id)

    # Return current status
    status_dict = camera_manager.get_camera_status(camera_id)
    return StreamInfo(**status_dict)


@router.post("/{camera_id}/restart", response_model=StreamInfo)
async def restart_stream(camera_id: str, db: DbSession) -> StreamInfo:
    """Restart streaming for a camera.

    Useful when stream quality degrades or after changing settings.
    """
    # Get camera from database
    result = await db.execute(select(Camera).where(Camera.id == camera_id))
    camera = result.scalar_one_or_none()

    if not camera:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Camera {camera_id} not found",
        )

    # Restart the camera stream
    success = await camera_manager.restart_camera(camera)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to restart stream for camera {camera.name}",
        )

    # Return current status
    status_dict = camera_manager.get_camera_status(camera_id)
    return StreamInfo(**status_dict)


@router.get("/{camera_id}/hls/{filename}")
async def get_hls_segment(camera_id: str, filename: str) -> Response:
    """Serve HLS playlist or segment files.

    This endpoint serves:
    - stream.m3u8: HLS playlist file
    - segment_*.ts: Video segment files
    """
    hls_path = settings.get_hls_path() / camera_id / filename

    if not hls_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"HLS file not found: {filename}. Is the stream running?",
        )

    # Determine content type
    if filename.endswith(".m3u8"):
        media_type = "application/vnd.apple.mpegurl"
    elif filename.endswith(".ts"):
        media_type = "video/mp2t"
    else:
        media_type = "application/octet-stream"

    return FileResponse(
        path=hls_path,
        media_type=media_type,
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Access-Control-Allow-Origin": "*",
        },
    )

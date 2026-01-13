"""Recording management endpoints."""

import logging
from datetime import datetime
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from backend.config import get_settings
from backend.core.database import get_db
from backend.models.camera import Camera
from backend.models.recording import Recording
from backend.schemas.recording import RecordingResponse, RecordingStats, StorageStats
from backend.services.storage_manager import storage_manager

router = APIRouter()
logger = logging.getLogger(__name__)
settings = get_settings()

DbSession = Annotated[AsyncSession, Depends(get_db)]


@router.get("", response_model=list[RecordingResponse])
async def list_recordings(
    db: DbSession,
    camera_id: str | None = Query(None, description="Filter by camera ID"),
    start_date: datetime | None = Query(None, description="Start date filter"),
    end_date: datetime | None = Query(None, description="End date filter"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
) -> list[Recording]:
    """List recordings with optional filters."""
    query = (
        select(Recording)
        .options(joinedload(Recording.camera))
        .order_by(Recording.start_time.desc())
    )

    if camera_id:
        query = query.where(Recording.camera_id == camera_id)

    if start_date:
        query = query.where(Recording.start_time >= start_date)

    if end_date:
        query = query.where(Recording.start_time <= end_date)

    query = query.limit(limit).offset(offset)

    result = await db.execute(query)
    recordings = list(result.scalars().all())

    # Add camera name to response
    for recording in recordings:
        if recording.camera:
            recording.camera_name = recording.camera.name

    return recordings


@router.get("/stats", response_model=RecordingStats)
async def get_recording_stats(db: DbSession) -> RecordingStats:
    """Get recording statistics."""
    # Total recordings
    total_result = await db.execute(select(func.count(Recording.id)))
    total_recordings = total_result.scalar() or 0

    # Total size
    size_result = await db.execute(select(func.sum(Recording.file_size)))
    total_size = size_result.scalar() or 0

    # Oldest recording
    oldest_result = await db.execute(
        select(Recording.start_time).order_by(Recording.start_time.asc()).limit(1)
    )
    oldest = oldest_result.scalar()

    # Newest recording
    newest_result = await db.execute(
        select(Recording.start_time).order_by(Recording.start_time.desc()).limit(1)
    )
    newest = newest_result.scalar()

    # Cameras with recordings
    cameras_result = await db.execute(
        select(func.count(func.distinct(Recording.camera_id)))
    )
    cameras_count = cameras_result.scalar() or 0

    return RecordingStats(
        total_recordings=total_recordings,
        total_size_bytes=total_size,
        oldest_recording=oldest,
        newest_recording=newest,
        cameras_with_recordings=cameras_count,
    )


@router.get("/{recording_id}", response_model=RecordingResponse)
async def get_recording(recording_id: str, db: DbSession) -> Recording:
    """Get a specific recording by ID."""
    result = await db.execute(
        select(Recording)
        .options(joinedload(Recording.camera))
        .where(Recording.id == recording_id)
    )
    recording = result.scalar_one_or_none()

    if not recording:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Recording {recording_id} not found",
        )

    if recording.camera:
        recording.camera_name = recording.camera.name

    return recording


@router.get("/{recording_id}/download")
async def download_recording(recording_id: str, db: DbSession) -> FileResponse:
    """Download a recording file."""
    result = await db.execute(
        select(Recording)
        .options(joinedload(Recording.camera))
        .where(Recording.id == recording_id)
    )
    recording = result.scalar_one_or_none()

    if not recording:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Recording {recording_id} not found",
        )

    file_path = Path(recording.file_path)
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Recording file not found on disk",
        )

    # Generate download filename
    camera_name = recording.camera.name if recording.camera else "camera"
    filename = f"{camera_name}_{recording.start_time.strftime('%Y%m%d_%H%M%S')}.mp4"

    return FileResponse(
        path=file_path,
        media_type="video/mp4",
        filename=filename,
    )


@router.delete("/{recording_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_recording(recording_id: str, db: DbSession) -> None:
    """Delete a recording (both database entry and file)."""
    result = await db.execute(select(Recording).where(Recording.id == recording_id))
    recording = result.scalar_one_or_none()

    if not recording:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Recording {recording_id} not found",
        )

    # Delete file if exists
    file_path = Path(recording.file_path)
    if file_path.exists():
        try:
            file_path.unlink()
            logger.info(f"Deleted recording file: {file_path}")
        except OSError as e:
            logger.error(f"Failed to delete recording file: {e}")

    # Delete database entry
    await db.delete(recording)
    logger.info(f"Deleted recording: {recording_id}")


@router.get("/storage/stats", response_model=StorageStats)
async def get_storage_stats() -> StorageStats:
    """Get storage statistics."""
    stats = await storage_manager.get_storage_stats()
    return StorageStats(**stats)


@router.post("/scan")
async def scan_recordings(
    db: DbSession,
    camera_id: str | None = Query(None, description="Scan only for specific camera"),
) -> dict:
    """Scan filesystem for new recordings and update database.

    This is useful after manual file operations or to ensure
    database is in sync with filesystem.
    """
    count = await storage_manager.scan_recordings(db, camera_id)
    return {"new_recordings_found": count}


@router.post("/cleanup")
async def cleanup_recordings(db: DbSession) -> dict:
    """Clean up old recordings based on retention policy.

    Deletes recordings older than the configured retention period.
    """
    deleted = await storage_manager.cleanup_old_recordings(db)
    return {"recordings_deleted": deleted}

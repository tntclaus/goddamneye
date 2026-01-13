"""Storage management service.

Handles recording storage, cleanup, and retention policies.
"""

import asyncio
import logging
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import get_settings
from backend.models.recording import Recording

if TYPE_CHECKING:
    from backend.models.camera import Camera

logger = logging.getLogger(__name__)
settings = get_settings()


class StorageManager:
    """Manages recording storage and cleanup."""

    def __init__(self):
        self._running = False
        self._cleanup_task: asyncio.Task | None = None
        self._scan_task: asyncio.Task | None = None

    async def start(self, db_factory) -> None:
        """Start the storage manager background tasks."""
        self._running = True
        self._db_factory = db_factory

        # Start background tasks
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        self._scan_task = asyncio.create_task(self._scan_loop())

        logger.info("Storage manager started")

    async def stop(self) -> None:
        """Stop the storage manager."""
        self._running = False

        for task in [self._cleanup_task, self._scan_task]:
            if task:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

        logger.info("Storage manager stopped")

    async def scan_recordings(self, db: AsyncSession, camera_id: str | None = None) -> int:
        """Scan filesystem for recordings and update database.

        Args:
            db: Database session.
            camera_id: Optional camera ID to limit scan.

        Returns:
            Number of new recordings found.
        """
        storage_path = settings.get_storage_path() / "recordings"
        new_count = 0

        if camera_id:
            camera_dirs = [storage_path / camera_id]
        else:
            camera_dirs = [d for d in storage_path.iterdir() if d.is_dir()]

        for camera_dir in camera_dirs:
            if not camera_dir.exists():
                continue

            cam_id = camera_dir.name

            # Scan date directories
            for date_dir in camera_dir.iterdir():
                if not date_dir.is_dir():
                    continue

                try:
                    date = datetime.strptime(date_dir.name, "%Y-%m-%d").date()
                except ValueError:
                    continue

                # Scan recording files
                for file_path in date_dir.glob("*.mp4"):
                    # Check if already in database
                    existing = await db.execute(
                        select(Recording).where(Recording.file_path == str(file_path))
                    )
                    if existing.scalar_one_or_none():
                        continue

                    # Parse hour from filename (e.g., "14.mp4" -> 14:00)
                    try:
                        hour = int(file_path.stem)
                        start_time = datetime.combine(date, datetime.min.time()).replace(
                            hour=hour
                        )
                    except ValueError:
                        start_time = datetime.fromtimestamp(file_path.stat().st_mtime)

                    # Get file info
                    file_stat = file_path.stat()

                    # Create recording entry
                    recording = Recording(
                        camera_id=cam_id,
                        file_path=str(file_path),
                        file_size=file_stat.st_size,
                        start_time=start_time,
                        end_time=start_time + timedelta(hours=1),
                        duration_seconds=3600,
                    )
                    db.add(recording)
                    new_count += 1

        if new_count > 0:
            await db.commit()
            logger.info(f"Found {new_count} new recordings")

        return new_count

    async def cleanup_old_recordings(self, db: AsyncSession) -> int:
        """Delete recordings older than retention period.

        Returns:
            Number of recordings deleted.
        """
        cutoff_date = datetime.now() - timedelta(days=settings.recording_retention_days)
        deleted_count = 0

        # Find old recordings
        result = await db.execute(
            select(Recording).where(Recording.start_time < cutoff_date)
        )
        old_recordings = result.scalars().all()

        for recording in old_recordings:
            # Delete file
            file_path = Path(recording.file_path)
            if file_path.exists():
                try:
                    file_path.unlink()
                    logger.debug(f"Deleted old recording file: {file_path}")
                except OSError as e:
                    logger.error(f"Failed to delete {file_path}: {e}")
                    continue

            # Delete database entry
            await db.delete(recording)
            deleted_count += 1

        if deleted_count > 0:
            await db.commit()
            logger.info(f"Cleaned up {deleted_count} old recordings")

        # Clean up empty directories
        await self._cleanup_empty_dirs()

        return deleted_count

    async def _cleanup_empty_dirs(self) -> None:
        """Remove empty date directories."""
        storage_path = settings.get_storage_path() / "recordings"

        for camera_dir in storage_path.iterdir():
            if not camera_dir.is_dir():
                continue

            for date_dir in camera_dir.iterdir():
                if date_dir.is_dir() and not any(date_dir.iterdir()):
                    try:
                        date_dir.rmdir()
                        logger.debug(f"Removed empty directory: {date_dir}")
                    except OSError:
                        pass

    async def get_storage_stats(self) -> dict:
        """Get storage statistics."""
        storage_path = settings.get_storage_path() / "recordings"

        total_size = 0
        file_count = 0

        if storage_path.exists():
            for file_path in storage_path.rglob("*.mp4"):
                try:
                    total_size += file_path.stat().st_size
                    file_count += 1
                except OSError:
                    pass

        return {
            "storage_path": str(storage_path),
            "total_size_bytes": total_size,
            "total_size_gb": round(total_size / (1024**3), 2),
            "file_count": file_count,
            "retention_days": settings.recording_retention_days,
        }

    async def _cleanup_loop(self) -> None:
        """Background loop for periodic cleanup."""
        while self._running:
            try:
                await asyncio.sleep(3600)  # Every hour

                async with self._db_factory() as db:
                    await self.cleanup_old_recordings(db)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Cleanup loop error: {e}")
                await asyncio.sleep(60)

    async def _scan_loop(self) -> None:
        """Background loop for periodic filesystem scanning."""
        while self._running:
            try:
                await asyncio.sleep(300)  # Every 5 minutes

                async with self._db_factory() as db:
                    await self.scan_recordings(db)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Scan loop error: {e}")
                await asyncio.sleep(60)


# Global storage manager instance
storage_manager = StorageManager()

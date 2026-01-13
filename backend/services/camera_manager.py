"""Camera lifecycle management service.

Manages the state of all cameras, coordinates stream workers,
and handles camera health monitoring.
"""

import asyncio
import logging
from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import get_settings
from backend.models.camera import Camera
from backend.services.stream_worker import StreamWorker

logger = logging.getLogger(__name__)
settings = get_settings()


class CameraManager:
    """Manages camera lifecycle and stream workers.

    This service is responsible for:
    - Starting/stopping stream workers for cameras
    - Monitoring camera health
    - Handling reconnection logic
    - Updating camera online status
    """

    def __init__(self):
        self._workers: dict[str, StreamWorker] = {}
        self._running = False
        self._monitor_task: asyncio.Task | None = None
        self._db_factory = None

    @property
    def active_streams(self) -> int:
        """Count of active streams."""
        return sum(1 for w in self._workers.values() if w.is_running)

    async def start(self, db_factory) -> None:
        """Start the camera manager and all enabled cameras.

        Args:
            db_factory: Async context manager that yields database sessions.
        """
        self._running = True
        self._db_factory = db_factory

        logger.info("Camera manager starting...")

        # Load enabled cameras from database and start workers
        async with db_factory() as db:
            result = await db.execute(
                select(Camera).where(Camera.enabled == True)  # noqa: E712
            )
            cameras = result.scalars().all()

            logger.info(f"Found {len(cameras)} enabled cameras")

            for camera in cameras:
                await self.start_camera(camera)

        # Start health monitor
        self._monitor_task = asyncio.create_task(
            self._health_monitor(),
            name="camera_health_monitor",
        )

        logger.info("Camera manager started")

    async def stop(self) -> None:
        """Stop all cameras and the manager."""
        logger.info("Camera manager stopping...")
        self._running = False

        # Cancel health monitor
        if self._monitor_task and not self._monitor_task.done():
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
            self._monitor_task = None

        # Stop all workers concurrently
        stop_tasks = [
            self.stop_camera(camera_id)
            for camera_id in list(self._workers.keys())
        ]
        if stop_tasks:
            await asyncio.gather(*stop_tasks, return_exceptions=True)

        logger.info("Camera manager stopped")

    async def start_camera(self, camera: Camera) -> bool:
        """Start streaming for a camera.

        Args:
            camera: Camera model instance.

        Returns:
            True if started successfully.
        """
        if camera.id in self._workers:
            worker = self._workers[camera.id]
            if worker.is_running:
                logger.debug(f"Camera {camera.name} already has active worker")
                return True

        # Create and start worker
        worker = StreamWorker(camera)
        success = await worker.start()

        if success:
            self._workers[camera.id] = worker
            # Update camera online status
            await self._update_camera_status(camera.id, is_online=True)
            logger.info(f"Started camera: {camera.name}")
        else:
            await self._update_camera_status(camera.id, is_online=False)
            logger.error(f"Failed to start camera: {camera.name}")

        return success

    async def stop_camera(self, camera_id: str) -> bool:
        """Stop streaming for a camera.

        Args:
            camera_id: Camera ID.

        Returns:
            True if stopped successfully.
        """
        worker = self._workers.pop(camera_id, None)

        if worker:
            await worker.stop()
            await self._update_camera_status(camera_id, is_online=False)
            logger.info(f"Stopped camera: {camera_id}")
            return True

        return False

    async def restart_camera(self, camera: Camera) -> bool:
        """Restart streaming for a camera.

        Args:
            camera: Camera model instance.

        Returns:
            True if restarted successfully.
        """
        await self.stop_camera(camera.id)
        return await self.start_camera(camera)

    async def start_camera_by_id(self, camera_id: str) -> bool:
        """Start a camera by its ID (loads from database).

        Args:
            camera_id: Camera ID.

        Returns:
            True if started successfully.
        """
        if not self._db_factory:
            logger.error("Camera manager not initialized")
            return False

        async with self._db_factory() as db:
            result = await db.execute(
                select(Camera).where(Camera.id == camera_id)
            )
            camera = result.scalar_one_or_none()

            if not camera:
                logger.error(f"Camera not found: {camera_id}")
                return False

            return await self.start_camera(camera)

    def get_worker(self, camera_id: str) -> StreamWorker | None:
        """Get worker for a camera."""
        return self._workers.get(camera_id)

    def get_camera_status(self, camera_id: str) -> dict:
        """Get current status of a camera.

        Args:
            camera_id: Camera ID.

        Returns:
            Status dictionary.
        """
        worker = self._workers.get(camera_id)

        if not worker:
            return {
                "camera_id": camera_id,
                "is_running": False,
                "is_recording": False,
                "hls_url": None,
            }

        return worker.get_status()

    def get_all_statuses(self) -> list[dict]:
        """Get status of all cameras."""
        return [worker.get_status() for worker in self._workers.values()]

    async def _update_camera_status(
        self,
        camera_id: str,
        is_online: bool,
    ) -> None:
        """Update camera online status in database."""
        if not self._db_factory:
            return

        try:
            async with self._db_factory() as db:
                await db.execute(
                    update(Camera)
                    .where(Camera.id == camera_id)
                    .values(
                        is_online=is_online,
                        last_seen_at=datetime.utcnow() if is_online else None,
                    )
                )
                await db.commit()
        except Exception as e:
            logger.error(f"Failed to update camera status: {e}")

    async def _health_monitor(self) -> None:
        """Background task to monitor camera health and restart failed workers."""
        while self._running:
            try:
                await asyncio.sleep(30)  # Check every 30 seconds

                for camera_id, worker in list(self._workers.items()):
                    # Check if worker died unexpectedly
                    if not worker.is_running and worker._restart_count >= worker._max_restarts:
                        logger.warning(
                            f"Camera {camera_id} worker is dead and exhausted restarts"
                        )
                        # Remove dead worker and update status
                        self._workers.pop(camera_id, None)
                        await self._update_camera_status(camera_id, is_online=False)

                    # Update last_seen for running cameras
                    elif worker.is_running:
                        await self._update_camera_status(camera_id, is_online=True)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health monitor error: {e}")
                await asyncio.sleep(5)


# Global camera manager instance
camera_manager = CameraManager()

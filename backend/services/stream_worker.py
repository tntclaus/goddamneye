"""FFmpeg stream worker for handling camera streams.

Each camera gets its own StreamWorker that manages:
- RTSP → HLS transcoding for live viewing
- Segment recording for storage
"""

import asyncio
import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

from backend.config import get_settings

if TYPE_CHECKING:
    from backend.models.camera import Camera

logger = logging.getLogger(__name__)
settings = get_settings()


class StreamWorker:
    """Manages FFmpeg process for a single camera.

    Handles both live HLS streaming and segment recording.
    """

    def __init__(self, camera: "Camera"):
        self.camera = camera
        self.camera_id = camera.id
        self.camera_name = camera.name
        self.rtsp_url = camera.rtsp_url
        self.username = camera.username
        self.password = camera.password_encrypted
        self.recording_enabled = camera.recording_enabled

        self._process: asyncio.subprocess.Process | None = None
        self._running = False
        self._restart_count = 0
        self._max_restarts = 10
        self._restart_delay = 5  # seconds
        self._monitor_task: asyncio.Task | None = None

        # Paths
        self._hls_path = settings.get_hls_path() / camera.id
        self._storage_path = settings.get_storage_path() / "recordings" / camera.id

    @property
    def is_running(self) -> bool:
        """Check if the worker is running."""
        return self._running and self._process is not None

    @property
    def hls_playlist_path(self) -> Path:
        """Get the HLS playlist file path."""
        return self._hls_path / "stream.m3u8"

    @property
    def hls_playlist_url(self) -> str:
        """Get the HLS playlist URL for this camera."""
        return f"/hls/{self.camera_id}/stream.m3u8"

    def _build_rtsp_url_with_auth(self) -> str:
        """Build RTSP URL with embedded credentials if available.

        Properly URL-encodes credentials to handle special characters.
        """
        import urllib.parse

        rtsp_url = self.rtsp_url

        if self.username and self.password:
            # Insert credentials into URL: rtsp://user:pass@host:port/path
            if "://" in rtsp_url:
                protocol, rest = rtsp_url.split("://", 1)
                # Check if credentials are already in URL
                if "@" not in rest:
                    # URL-encode username and password to handle special chars like %^@:
                    encoded_user = urllib.parse.quote(self.username, safe="")
                    encoded_pass = urllib.parse.quote(self.password, safe="")
                    rtsp_url = f"{protocol}://{encoded_user}:{encoded_pass}@{rest}"

        return rtsp_url

    def _build_ffmpeg_command(self) -> list[str]:
        """Build the FFmpeg command for streaming and recording."""
        rtsp_url = self._build_rtsp_url_with_auth()

        # Ensure directories exist
        self._hls_path.mkdir(parents=True, exist_ok=True)

        cmd = [
            settings.ffmpeg_path,
            # Global options
            "-hide_banner",
            "-loglevel", "warning",
            # Input options
            "-rtsp_transport", "tcp",
            "-i", rtsp_url,
            # Error handling
            "-err_detect", "ignore_err",
            "-fflags", "+genpts+discardcorrupt",
            # Reconnect options (for network issues)
            "-reconnect", "1",
            "-reconnect_streamed", "1",
            "-reconnect_delay_max", "5",
        ]

        # HLS output for live streaming
        cmd.extend([
            # Map video stream
            "-map", "0:v:0",
            # Copy video codec (no transcoding for performance)
            "-c:v", "copy",
            # HLS format options
            "-f", "hls",
            "-hls_time", "2",  # 2 second segments
            "-hls_list_size", "6",  # Keep 6 segments in playlist (12 seconds)
            "-hls_flags", "delete_segments+append_list+omit_endlist",
            "-hls_segment_type", "mpegts",
            "-hls_segment_filename", str(self._hls_path / "segment_%04d.ts"),
            str(self._hls_path / "stream.m3u8"),
        ])

        # Recording output (hourly MP4 segments) - if enabled
        if self.recording_enabled:
            # Create date-based directory
            date_path = self._storage_path / datetime.now().strftime("%Y-%m-%d")
            date_path.mkdir(parents=True, exist_ok=True)

            cmd.extend([
                # Map video stream again for second output
                "-map", "0:v:0",
                # Copy video codec
                "-c:v", "copy",
                # Segment format for hourly recordings
                "-f", "segment",
                "-segment_time", str(settings.recording_segment_duration),
                "-segment_format", "mp4",
                "-segment_atclocktime", "1",
                "-strftime", "1",
                "-reset_timestamps", "1",
                # Output pattern: /storage/recordings/{camera_id}/{date}/%H.mp4
                str(self._storage_path / "%Y-%m-%d" / "%H.mp4"),
            ])

        # Try to include audio if available
        if self._has_audio_stream():
            # Insert audio mapping before outputs
            # This is a simplified approach - in production you might want separate handling
            pass

        return cmd

    def _has_audio_stream(self) -> bool:
        """Check if camera stream has audio (simplified check)."""
        # For now, assume no audio to avoid complexity
        # In production, you'd probe the stream first
        return False

    async def start(self) -> bool:
        """Start the FFmpeg process."""
        if self._running:
            logger.warning(f"[{self.camera_name}] Worker already running")
            return True

        # Check FFmpeg availability
        if not shutil.which(settings.ffmpeg_path):
            logger.error(f"FFmpeg not found at: {settings.ffmpeg_path}")
            return False

        try:
            # Clean up old HLS files
            await self._cleanup_hls_files()

            # Build and log command
            cmd = self._build_ffmpeg_command()
            logger.info(f"[{self.camera_name}] Starting stream worker")
            logger.debug(f"[{self.camera_name}] FFmpeg command: {' '.join(cmd)}")

            # Start FFmpeg process
            self._process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            self._running = True
            self._restart_count = 0

            # Start output monitor task
            self._monitor_task = asyncio.create_task(
                self._monitor_output(),
                name=f"monitor_{self.camera_id}",
            )

            logger.info(f"[{self.camera_name}] Stream worker started (PID: {self._process.pid})")
            return True

        except Exception as e:
            logger.error(f"[{self.camera_name}] Failed to start stream worker: {e}")
            self._running = False
            return False

    async def stop(self) -> None:
        """Stop the FFmpeg process."""
        self._running = False

        # Cancel monitor task
        if self._monitor_task and not self._monitor_task.done():
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
            self._monitor_task = None

        # Stop FFmpeg process
        if self._process:
            pid = self._process.pid
            try:
                # Try graceful shutdown first
                self._process.terminate()
                try:
                    await asyncio.wait_for(self._process.wait(), timeout=5)
                except asyncio.TimeoutError:
                    # Force kill if not responding
                    logger.warning(f"[{self.camera_name}] Force killing FFmpeg process")
                    self._process.kill()
                    await self._process.wait()
            except ProcessLookupError:
                pass  # Process already dead
            except Exception as e:
                logger.error(f"[{self.camera_name}] Error stopping FFmpeg: {e}")
            finally:
                self._process = None

            logger.info(f"[{self.camera_name}] Stream worker stopped (was PID: {pid})")

    async def restart(self) -> bool:
        """Restart the FFmpeg process."""
        logger.info(f"[{self.camera_name}] Restarting stream worker")
        await self.stop()
        await asyncio.sleep(self._restart_delay)
        return await self.start()

    async def _cleanup_hls_files(self) -> None:
        """Clean up old HLS segment files."""
        try:
            if self._hls_path.exists():
                for file in self._hls_path.glob("*.ts"):
                    file.unlink()
                for file in self._hls_path.glob("*.m3u8"):
                    file.unlink()
        except Exception as e:
            logger.warning(f"[{self.camera_name}] Failed to cleanup HLS files: {e}")

    async def _monitor_output(self) -> None:
        """Monitor FFmpeg stderr output and handle errors/restart."""
        if not self._process or not self._process.stderr:
            return

        try:
            while self._running and self._process:
                try:
                    line = await asyncio.wait_for(
                        self._process.stderr.readline(),
                        timeout=60,  # Log something every minute to show we're alive
                    )
                except asyncio.TimeoutError:
                    # No output is fine for streaming
                    continue

                if not line:
                    break

                line_str = line.decode().strip()
                if line_str:
                    # Log FFmpeg output
                    if "error" in line_str.lower():
                        logger.warning(f"[{self.camera_name}] FFmpeg: {line_str}")
                    else:
                        logger.debug(f"[{self.camera_name}] FFmpeg: {line_str}")

            # Check if process ended while we're supposed to be running
            if self._running and self._process:
                return_code = await self._process.wait()
                logger.warning(
                    f"[{self.camera_name}] FFmpeg process exited with code {return_code}"
                )

                # Auto-restart if within limits
                if self._restart_count < self._max_restarts:
                    self._restart_count += 1
                    logger.info(
                        f"[{self.camera_name}] Auto-restart attempt "
                        f"{self._restart_count}/{self._max_restarts}"
                    )
                    # Schedule restart (don't await to avoid blocking)
                    asyncio.create_task(self.restart())
                else:
                    logger.error(
                        f"[{self.camera_name}] Max restart attempts reached, giving up"
                    )
                    self._running = False

        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"[{self.camera_name}] Monitor error: {e}")

    def get_status(self) -> dict:
        """Get current worker status."""
        return {
            "camera_id": self.camera_id,
            "camera_name": self.camera_name,
            "is_running": self.is_running,
            "is_recording": self.is_running and self.recording_enabled,
            "hls_url": self.hls_playlist_url if self.is_running else None,
            "restart_count": self._restart_count,
            "pid": self._process.pid if self._process else None,
        }

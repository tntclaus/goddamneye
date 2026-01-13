"""FFmpeg utility functions and command builders."""

import asyncio
import logging
import shutil
from pathlib import Path

from backend.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


async def check_ffmpeg() -> bool:
    """Check if FFmpeg is available and working."""
    ffmpeg_path = shutil.which(settings.ffmpeg_path)

    if not ffmpeg_path:
        logger.error(f"FFmpeg not found: {settings.ffmpeg_path}")
        return False

    try:
        process = await asyncio.create_subprocess_exec(
            ffmpeg_path,
            "-version",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await process.communicate()

        if process.returncode == 0:
            version_line = stdout.decode().split("\n")[0]
            logger.info(f"FFmpeg available: {version_line}")
            return True
        else:
            logger.error("FFmpeg check failed")
            return False

    except Exception as e:
        logger.error(f"FFmpeg check error: {e}")
        return False


async def probe_stream(rtsp_url: str, timeout: int = 10) -> dict | None:
    """Probe an RTSP stream to get its properties.

    Args:
        rtsp_url: RTSP stream URL.
        timeout: Probe timeout in seconds.

    Returns:
        Stream information dict or None if probe failed.
    """
    try:
        cmd = [
            settings.ffmpeg_path.replace("ffmpeg", "ffprobe"),
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            "-rtsp_transport", "tcp",
            rtsp_url,
        ]

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout,
            )
        except asyncio.TimeoutError:
            process.kill()
            await process.wait()
            logger.warning(f"Stream probe timed out: {rtsp_url}")
            return None

        if process.returncode != 0:
            logger.warning(f"Stream probe failed: {stderr.decode()}")
            return None

        import json
        return json.loads(stdout.decode())

    except Exception as e:
        logger.error(f"Stream probe error: {e}")
        return None


async def create_thumbnail(
    rtsp_url: str,
    output_path: Path,
    size: str = "320x180",
    timeout: int = 10,
) -> bool:
    """Capture a thumbnail from an RTSP stream.

    Args:
        rtsp_url: RTSP stream URL.
        output_path: Path to save thumbnail.
        size: Thumbnail size (WxH).
        timeout: Capture timeout in seconds.

    Returns:
        True if successful, False otherwise.
    """
    try:
        cmd = [
            settings.ffmpeg_path,
            "-rtsp_transport", "tcp",
            "-i", rtsp_url,
            "-frames:v", "1",
            "-s", size,
            "-y",
            str(output_path),
        ]

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.PIPE,
        )

        try:
            _, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout,
            )
        except asyncio.TimeoutError:
            process.kill()
            await process.wait()
            logger.warning(f"Thumbnail capture timed out: {rtsp_url}")
            return False

        if process.returncode == 0 and output_path.exists():
            return True
        else:
            logger.warning(f"Thumbnail capture failed: {stderr.decode()}")
            return False

    except Exception as e:
        logger.error(f"Thumbnail capture error: {e}")
        return False


def build_hls_command(
    input_url: str,
    output_dir: Path,
    segment_time: int = 2,
    list_size: int = 5,
) -> list[str]:
    """Build FFmpeg command for HLS streaming.

    Args:
        input_url: Input stream URL.
        output_dir: Directory for HLS output.
        segment_time: Segment duration in seconds.
        list_size: Number of segments in playlist.

    Returns:
        FFmpeg command as list of strings.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    return [
        settings.ffmpeg_path,
        "-rtsp_transport", "tcp",
        "-i", input_url,
        "-c:v", "copy",
        "-c:a", "aac",
        "-f", "hls",
        "-hls_time", str(segment_time),
        "-hls_list_size", str(list_size),
        "-hls_flags", "delete_segments+append_list",
        "-hls_segment_filename", str(output_dir / "segment_%03d.ts"),
        str(output_dir / "stream.m3u8"),
    ]


def build_recording_command(
    input_url: str,
    output_path: Path,
    segment_time: int = 3600,
) -> list[str]:
    """Build FFmpeg command for recording.

    Args:
        input_url: Input stream URL.
        output_path: Output file path pattern.
        segment_time: Segment duration in seconds.

    Returns:
        FFmpeg command as list of strings.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    return [
        settings.ffmpeg_path,
        "-rtsp_transport", "tcp",
        "-i", input_url,
        "-c:v", "copy",
        "-c:a", "aac",
        "-f", "segment",
        "-segment_time", str(segment_time),
        "-segment_format", "mp4",
        "-segment_atclocktime", "1",
        "-strftime", "1",
        "-reset_timestamps", "1",
        str(output_path),
    ]

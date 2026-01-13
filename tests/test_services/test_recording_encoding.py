"""Tests for recording encoding options in StreamWorker.

Tests verify that FFmpeg H.265/HEVC encoding options are correctly
generated for the three quality presets: fast, balanced, compact.
"""

import unittest
from unittest.mock import MagicMock, patch

from backend.config import Settings
from backend.services.stream_worker import StreamWorker


class TestRecordingQualityPresets(unittest.TestCase):
    """Tests for get_x265_preset method."""

    def test_fast_preset_returns_veryfast(self):
        """Test 'fast' quality returns veryfast preset."""
        settings = Settings(recording_quality="fast")
        assert settings.get_x265_preset() == "veryfast"

    def test_balanced_preset_returns_fast(self):
        """Test 'balanced' quality returns fast preset."""
        settings = Settings(recording_quality="balanced")
        assert settings.get_x265_preset() == "fast"

    def test_compact_preset_returns_medium(self):
        """Test 'compact' quality returns medium preset."""
        settings = Settings(recording_quality="compact")
        assert settings.get_x265_preset() == "medium"

    def test_default_quality_is_balanced(self):
        """Test default quality is balanced."""
        settings = Settings()
        assert settings.recording_quality == "balanced"

    def test_default_crf_is_28(self):
        """Test default CRF is 28."""
        settings = Settings()
        assert settings.recording_crf == 28

    def test_case_insensitive(self):
        """Test quality setting is case insensitive."""
        settings = Settings(recording_quality="COMPACT")
        assert settings.get_x265_preset() == "medium"

    def test_unknown_quality_defaults_to_balanced(self):
        """Test unknown quality falls back to balanced preset."""
        settings = Settings(recording_quality="unknown")
        assert settings.get_x265_preset() == "fast"


class TestRecordingEncodingOptions(unittest.TestCase):
    """Tests for _build_recording_encoding_options method."""

    def _create_mock_camera(
        self,
        camera_id: str = "test-camera",
        name: str = "Test Camera",
        rtsp_url: str = "rtsp://192.168.1.100:554/stream1",
        username: str | None = None,
        password: str | None = None,
        recording_enabled: bool = True,
    ) -> MagicMock:
        """Create a mock Camera object."""
        camera = MagicMock()
        camera.id = camera_id
        camera.name = name
        camera.rtsp_url = rtsp_url
        camera.username = username
        camera.password_encrypted = password
        camera.recording_enabled = recording_enabled
        return camera

    @patch("backend.services.stream_worker.settings")
    def test_uses_libx265_codec(self, mock_settings):
        """Test that libx265 (HEVC) is used for encoding."""
        mock_settings.get_x265_preset.return_value = "fast"
        mock_settings.recording_crf = 28
        mock_settings.recording_scale = ""

        camera = self._create_mock_camera()
        worker = StreamWorker(camera)
        opts = worker._build_recording_encoding_options()

        assert "-c:v" in opts
        assert "libx265" in opts

    @patch("backend.services.stream_worker.settings")
    def test_fast_quality_uses_veryfast_preset(self, mock_settings):
        """Test fast quality uses veryfast preset."""
        mock_settings.get_x265_preset.return_value = "veryfast"
        mock_settings.recording_crf = 28
        mock_settings.recording_scale = ""

        camera = self._create_mock_camera()
        worker = StreamWorker(camera)
        opts = worker._build_recording_encoding_options()

        preset_idx = opts.index("-preset")
        assert opts[preset_idx + 1] == "veryfast"

    @patch("backend.services.stream_worker.settings")
    def test_balanced_quality_uses_fast_preset(self, mock_settings):
        """Test balanced quality uses fast preset."""
        mock_settings.get_x265_preset.return_value = "fast"
        mock_settings.recording_crf = 28
        mock_settings.recording_scale = ""

        camera = self._create_mock_camera()
        worker = StreamWorker(camera)
        opts = worker._build_recording_encoding_options()

        preset_idx = opts.index("-preset")
        assert opts[preset_idx + 1] == "fast"

    @patch("backend.services.stream_worker.settings")
    def test_compact_quality_uses_medium_preset(self, mock_settings):
        """Test compact quality uses medium preset."""
        mock_settings.get_x265_preset.return_value = "medium"
        mock_settings.recording_crf = 28
        mock_settings.recording_scale = ""

        camera = self._create_mock_camera()
        worker = StreamWorker(camera)
        opts = worker._build_recording_encoding_options()

        preset_idx = opts.index("-preset")
        assert opts[preset_idx + 1] == "medium"

    @patch("backend.services.stream_worker.settings")
    def test_crf_is_configurable(self, mock_settings):
        """Test CRF value comes from settings."""
        mock_settings.get_x265_preset.return_value = "fast"
        mock_settings.recording_crf = 32  # Custom CRF
        mock_settings.recording_scale = ""

        camera = self._create_mock_camera()
        worker = StreamWorker(camera)
        opts = worker._build_recording_encoding_options()

        crf_idx = opts.index("-crf")
        assert opts[crf_idx + 1] == "32"

    @patch("backend.services.stream_worker.settings")
    def test_scaling_filter(self, mock_settings):
        """Test scaling to 720p."""
        mock_settings.get_x265_preset.return_value = "fast"
        mock_settings.recording_crf = 28
        mock_settings.recording_scale = "1280:720"

        camera = self._create_mock_camera()
        worker = StreamWorker(camera)
        opts = worker._build_recording_encoding_options()

        assert "-vf" in opts
        vf_idx = opts.index("-vf")
        assert "scale=1280:720" in opts[vf_idx + 1]

    @patch("backend.services.stream_worker.settings")
    def test_no_scaling_when_empty(self, mock_settings):
        """Test no -vf filter when scale is empty."""
        mock_settings.get_x265_preset.return_value = "fast"
        mock_settings.recording_crf = 28
        mock_settings.recording_scale = ""

        camera = self._create_mock_camera()
        worker = StreamWorker(camera)
        opts = worker._build_recording_encoding_options()

        assert "-vf" not in opts

    @patch("backend.services.stream_worker.settings")
    def test_faststart_movflag(self, mock_settings):
        """Test faststart flag for quick MP4 seeking."""
        mock_settings.get_x265_preset.return_value = "fast"
        mock_settings.recording_crf = 28
        mock_settings.recording_scale = ""

        camera = self._create_mock_camera()
        worker = StreamWorker(camera)
        opts = worker._build_recording_encoding_options()

        assert "-movflags" in opts
        movflags_idx = opts.index("-movflags")
        assert "+faststart" in opts[movflags_idx + 1]

    @patch("backend.services.stream_worker.settings")
    def test_yuv420p_pixel_format(self, mock_settings):
        """Test yuv420p pixel format for compatibility."""
        mock_settings.get_x265_preset.return_value = "fast"
        mock_settings.recording_crf = 28
        mock_settings.recording_scale = ""

        camera = self._create_mock_camera()
        worker = StreamWorker(camera)
        opts = worker._build_recording_encoding_options()

        assert "-pix_fmt" in opts
        pix_fmt_idx = opts.index("-pix_fmt")
        assert opts[pix_fmt_idx + 1] == "yuv420p"

    @patch("backend.services.stream_worker.settings")
    def test_hvc1_tag_for_apple_compatibility(self, mock_settings):
        """Test hvc1 tag is used for Apple device compatibility."""
        mock_settings.get_x265_preset.return_value = "fast"
        mock_settings.recording_crf = 28
        mock_settings.recording_scale = ""

        camera = self._create_mock_camera()
        worker = StreamWorker(camera)
        opts = worker._build_recording_encoding_options()

        assert "-tag:v" in opts
        tag_idx = opts.index("-tag:v")
        assert opts[tag_idx + 1] == "hvc1"

    @patch("backend.services.stream_worker.settings")
    def test_x265_log_level_suppressed(self, mock_settings):
        """Test x265 info banner is suppressed."""
        mock_settings.get_x265_preset.return_value = "fast"
        mock_settings.recording_crf = 28
        mock_settings.recording_scale = ""

        camera = self._create_mock_camera()
        worker = StreamWorker(camera)
        opts = worker._build_recording_encoding_options()

        assert "-x265-params" in opts
        params_idx = opts.index("-x265-params")
        assert "log-level=error" in opts[params_idx + 1]


class TestBuildFFmpegCommandWithEncoding(unittest.TestCase):
    """Tests for FFmpeg command integration with HEVC encoding."""

    def _create_mock_camera(
        self,
        camera_id: str = "test-camera",
        name: str = "Test Camera",
        rtsp_url: str = "rtsp://192.168.1.100:554/stream1",
        username: str | None = None,
        password: str | None = None,
        recording_enabled: bool = True,
    ) -> MagicMock:
        """Create a mock Camera object."""
        camera = MagicMock()
        camera.id = camera_id
        camera.name = name
        camera.rtsp_url = rtsp_url
        camera.username = username
        camera.password_encrypted = password
        camera.recording_enabled = recording_enabled
        return camera

    @patch("backend.services.stream_worker.settings")
    def test_ffmpeg_command_includes_libx265_for_recording(self, mock_settings):
        """Test that FFmpeg command uses libx265 for recording output."""
        mock_settings.ffmpeg_path = "ffmpeg"
        mock_settings.get_x265_preset.return_value = "fast"
        mock_settings.recording_crf = 28
        mock_settings.recording_scale = ""
        mock_settings.recording_segment_duration = 3600
        mock_settings.get_hls_path.return_value = MagicMock()
        mock_settings.get_hls_path.return_value.__truediv__ = lambda self, x: MagicMock(
            mkdir=MagicMock(),
            __truediv__=lambda self, y: f"/tmp/hls/{x}/{y}",
            __str__=lambda self: f"/tmp/hls/{x}",
        )
        mock_settings.get_storage_path.return_value = MagicMock()
        mock_settings.get_storage_path.return_value.__truediv__ = lambda self, x: MagicMock(
            __truediv__=lambda self, y: MagicMock(
                __truediv__=lambda self, z: MagicMock(
                    mkdir=MagicMock(),
                    __str__=lambda self: f"/storage/{x}/{y}",
                ),
                mkdir=MagicMock(),
            ),
        )

        camera = self._create_mock_camera(recording_enabled=True)
        worker = StreamWorker(camera)

        cmd = worker._build_ffmpeg_command()

        # Recording should use libx265
        assert "libx265" in cmd

    @patch("backend.services.stream_worker.settings")
    def test_ffmpeg_command_no_encoding_when_recording_disabled(self, mock_settings):
        """Test that FFmpeg command doesn't include encoding when recording disabled."""
        mock_settings.ffmpeg_path = "ffmpeg"
        mock_settings.get_x265_preset.return_value = "fast"
        mock_settings.recording_crf = 28
        mock_settings.recording_scale = ""
        mock_settings.get_hls_path.return_value = MagicMock()
        mock_settings.get_hls_path.return_value.__truediv__ = lambda self, x: MagicMock(
            mkdir=MagicMock(),
            __truediv__=lambda self, y: f"/tmp/hls/{x}/{y}",
            __str__=lambda self: f"/tmp/hls/{x}",
        )

        camera = self._create_mock_camera(recording_enabled=False)
        worker = StreamWorker(camera)

        cmd = worker._build_ffmpeg_command()

        # Should not include libx265 when recording is disabled
        assert "libx265" not in cmd


if __name__ == "__main__":
    unittest.main()

"""Tests for stream worker RTSP URL handling.

These tests verify that credentials with special characters are properly
URL-encoded when building FFmpeg commands.

Bug reference: Password "2XkRHya8%^Ysmd7jTihQ4pdK" was being double-encoded
as "2XkRHya8%25%5EYsmd7jTihQ4pdK" in stored URL instead of being encoded
only at runtime.
"""

import pytest
from unittest.mock import MagicMock

from backend.services.stream_worker import StreamWorker


class TestRtspUrlBuilding:
    """Tests for RTSP URL credential encoding."""

    def _create_mock_camera(
        self,
        rtsp_url: str,
        username: str | None = None,
        password: str | None = None,
    ) -> MagicMock:
        """Create a mock camera object for testing."""
        camera = MagicMock()
        camera.id = "test-camera-id"
        camera.name = "Test Camera"
        camera.rtsp_url = rtsp_url
        camera.username = username
        camera.password_encrypted = password
        camera.recording_enabled = False
        return camera

    def test_url_without_credentials(self):
        """Test that URL without credentials remains unchanged."""
        camera = self._create_mock_camera(
            rtsp_url="rtsp://192.168.1.100:554/stream1",
            username=None,
            password=None,
        )
        worker = StreamWorker(camera)

        result = worker._build_rtsp_url_with_auth()

        assert result == "rtsp://192.168.1.100:554/stream1"

    def test_url_with_simple_credentials(self):
        """Test URL encoding with simple alphanumeric credentials."""
        camera = self._create_mock_camera(
            rtsp_url="rtsp://192.168.1.100:554/stream1",
            username="admin",
            password="password123",
        )
        worker = StreamWorker(camera)

        result = worker._build_rtsp_url_with_auth()

        assert result == "rtsp://admin:password123@192.168.1.100:554/stream1"

    def test_url_encodes_percent_sign(self):
        """Test that % in password is encoded as %25."""
        camera = self._create_mock_camera(
            rtsp_url="rtsp://192.168.1.100:554/stream1",
            username="admin",
            password="pass%word",
        )
        worker = StreamWorker(camera)

        result = worker._build_rtsp_url_with_auth()

        assert "pass%25word" in result
        assert result == "rtsp://admin:pass%25word@192.168.1.100:554/stream1"

    def test_url_encodes_caret_symbol(self):
        """Test that ^ in password is encoded as %5E."""
        camera = self._create_mock_camera(
            rtsp_url="rtsp://192.168.1.100:554/stream1",
            username="admin",
            password="pass^word",
        )
        worker = StreamWorker(camera)

        result = worker._build_rtsp_url_with_auth()

        assert "pass%5Eword" in result
        assert result == "rtsp://admin:pass%5Eword@192.168.1.100:554/stream1"

    def test_url_encodes_real_world_password(self):
        """Test encoding of actual problematic password from bug report.

        Password: 2XkRHya8%^Ysmd7jTihQ4pdK
        Expected encoding: 2XkRHya8%25%5EYsmd7jTihQ4pdK
        """
        camera = self._create_mock_camera(
            rtsp_url="rtsp://192.168.90.98:554/media/video1",
            username="admin",
            password="2XkRHya8%^Ysmd7jTihQ4pdK",
        )
        worker = StreamWorker(camera)

        result = worker._build_rtsp_url_with_auth()

        # % should be encoded as %25
        # ^ should be encoded as %5E
        expected = "rtsp://admin:2XkRHya8%25%5EYsmd7jTihQ4pdK@192.168.90.98:554/media/video1"
        assert result == expected

    def test_url_encodes_at_symbol_in_password(self):
        """Test that @ in password is encoded as %40 to avoid URL confusion."""
        camera = self._create_mock_camera(
            rtsp_url="rtsp://192.168.1.100:554/stream1",
            username="admin",
            password="pass@word",
        )
        worker = StreamWorker(camera)

        result = worker._build_rtsp_url_with_auth()

        assert "pass%40word" in result
        assert "@192.168.1.100" in result  # Host separator should be unencoded

    def test_url_encodes_colon_in_password(self):
        """Test that : in password is encoded as %3A to avoid URL confusion."""
        camera = self._create_mock_camera(
            rtsp_url="rtsp://192.168.1.100:554/stream1",
            username="admin",
            password="pass:word",
        )
        worker = StreamWorker(camera)

        result = worker._build_rtsp_url_with_auth()

        assert "pass%3Aword" in result
        # Ensure the port colon is preserved
        assert ":554" in result

    def test_url_encodes_slash_in_password(self):
        """Test that / in password is encoded as %2F."""
        camera = self._create_mock_camera(
            rtsp_url="rtsp://192.168.1.100:554/stream1",
            username="admin",
            password="pass/word",
        )
        worker = StreamWorker(camera)

        result = worker._build_rtsp_url_with_auth()

        assert "pass%2Fword" in result

    def test_url_encodes_username_special_chars(self):
        """Test that special characters in username are also encoded."""
        camera = self._create_mock_camera(
            rtsp_url="rtsp://192.168.1.100:554/stream1",
            username="admin@domain",
            password="password",
        )
        worker = StreamWorker(camera)

        result = worker._build_rtsp_url_with_auth()

        assert "admin%40domain:password@" in result

    def test_url_preserves_existing_credentials(self):
        """Test that URL with existing credentials is not modified."""
        camera = self._create_mock_camera(
            rtsp_url="rtsp://existing:creds@192.168.1.100:554/stream1",
            username="admin",
            password="password",
        )
        worker = StreamWorker(camera)

        result = worker._build_rtsp_url_with_auth()

        # Should not add new credentials if @ already in URL
        assert result == "rtsp://existing:creds@192.168.1.100:554/stream1"

    def test_url_only_username_no_password(self):
        """Test URL when only username is provided (edge case)."""
        camera = self._create_mock_camera(
            rtsp_url="rtsp://192.168.1.100:554/stream1",
            username="admin",
            password=None,
        )
        worker = StreamWorker(camera)

        result = worker._build_rtsp_url_with_auth()

        # No credentials should be added if password is missing
        assert result == "rtsp://192.168.1.100:554/stream1"

    def test_url_empty_password(self):
        """Test URL with empty password string."""
        camera = self._create_mock_camera(
            rtsp_url="rtsp://192.168.1.100:554/stream1",
            username="admin",
            password="",
        )
        worker = StreamWorker(camera)

        result = worker._build_rtsp_url_with_auth()

        # Empty password should not add credentials
        assert result == "rtsp://192.168.1.100:554/stream1"

    def test_url_with_complex_path(self):
        """Test URL encoding preserves complex paths."""
        camera = self._create_mock_camera(
            rtsp_url="rtsp://192.168.1.100:554/Streaming/Channels/101",
            username="admin",
            password="pass%word",
        )
        worker = StreamWorker(camera)

        result = worker._build_rtsp_url_with_auth()

        assert result == "rtsp://admin:pass%25word@192.168.1.100:554/Streaming/Channels/101"


class TestStreamWorkerProperties:
    """Tests for StreamWorker property methods."""

    def _create_mock_camera(self) -> MagicMock:
        """Create a mock camera for property tests."""
        camera = MagicMock()
        camera.id = "test-camera-123"
        camera.name = "Test Camera"
        camera.rtsp_url = "rtsp://192.168.1.100:554/stream1"
        camera.username = None
        camera.password_encrypted = None
        camera.recording_enabled = False
        return camera

    def test_hls_playlist_url(self):
        """Test HLS playlist URL generation."""
        camera = self._create_mock_camera()
        worker = StreamWorker(camera)

        assert worker.hls_playlist_url == "/hls/test-camera-123/stream.m3u8"

    def test_is_running_false_when_not_started(self):
        """Test is_running returns False when not started."""
        camera = self._create_mock_camera()
        worker = StreamWorker(camera)

        assert worker.is_running is False

    def test_get_status_not_running(self):
        """Test status dict when not running."""
        camera = self._create_mock_camera()
        worker = StreamWorker(camera)

        status = worker.get_status()

        assert status["camera_id"] == "test-camera-123"
        assert status["camera_name"] == "Test Camera"
        assert status["is_running"] is False
        assert status["hls_url"] is None
        assert status["pid"] is None

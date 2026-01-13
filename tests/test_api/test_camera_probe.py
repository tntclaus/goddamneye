"""Tests for camera probe endpoint.

These tests verify that the camera probe endpoint returns clean URLs
without embedded credentials, and properly reports ONVIF detection results.

Bug reference: Probe endpoint was returning URLs with embedded credentials
which caused double-encoding when stored and displayed.
"""

import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, patch, MagicMock


@pytest.mark.asyncio
async def test_probe_returns_clean_urls_on_onvif_success(client: AsyncClient):
    """Test that probe returns URLs without credentials when ONVIF succeeds."""
    # Mock ONVIF discovery to return a successful result
    mock_result = MagicMock()
    mock_result.name = "Test Camera"
    mock_result.manufacturer = "TestMfg"
    mock_result.model = "Model123"
    mock_result.firmware_version = "1.0.0"
    mock_result.serial_number = "SN123456"
    mock_result.rtsp_urls = [
        "rtsp://192.168.1.100:554/stream1",
        "rtsp://192.168.1.100:554/stream2",
    ]

    with patch(
        "backend.services.onvif_discovery.onvif_discovery.probe_camera",
        new_callable=AsyncMock,
        return_value=mock_result,
    ):
        response = await client.post(
            "/api/cameras/probe",
            json={
                "host": "192.168.1.100",
                "port": 80,
                "username": "admin",
                "password": "secret%^password",  # Special chars
            },
        )

    assert response.status_code == 200
    data = response.json()

    # Verify ONVIF was detected
    assert data["onvif_supported"] is True
    assert data["name"] == "Test Camera"
    assert data["manufacturer"] == "TestMfg"

    # Verify streams have clean URLs (no credentials)
    assert len(data["streams"]) == 2
    for stream in data["streams"]:
        url = stream["url"]
        # URL should NOT contain credentials
        assert "@" not in url
        assert "admin" not in url
        assert "secret" not in url
        # URL should be clean format
        assert url.startswith("rtsp://192.168.1.100")


@pytest.mark.asyncio
async def test_probe_returns_common_patterns_on_onvif_failure(client: AsyncClient):
    """Test that probe returns common RTSP patterns when ONVIF fails."""
    with patch(
        "backend.services.onvif_discovery.onvif_discovery.probe_camera",
        new_callable=AsyncMock,
        return_value=None,  # ONVIF failed
    ):
        response = await client.post(
            "/api/cameras/probe",
            json={
                "host": "192.168.1.100",
                "port": 80,
                "username": "admin",
                "password": "password",
            },
        )

    assert response.status_code == 200
    data = response.json()

    # Verify ONVIF was not detected
    assert data["onvif_supported"] is False
    assert data["error"] is not None
    assert "ONVIF" in data["error"]

    # Verify common patterns are returned
    assert len(data["streams"]) > 0

    # All URLs should be clean (no credentials)
    for stream in data["streams"]:
        url = stream["url"]
        assert "@" not in url
        assert url.startswith("rtsp://192.168.1.100")


@pytest.mark.asyncio
async def test_probe_response_structure(client: AsyncClient):
    """Test that probe response has expected structure."""
    mock_result = MagicMock()
    mock_result.name = "Camera Name"
    mock_result.manufacturer = "Manufacturer"
    mock_result.model = "Model"
    mock_result.firmware_version = "1.0"
    mock_result.serial_number = "12345"
    mock_result.rtsp_urls = ["rtsp://host/stream"]

    with patch(
        "backend.services.onvif_discovery.onvif_discovery.probe_camera",
        new_callable=AsyncMock,
        return_value=mock_result,
    ):
        response = await client.post(
            "/api/cameras/probe",
            json={"host": "192.168.1.100"},
        )

    assert response.status_code == 200
    data = response.json()

    # Verify all expected fields are present
    assert "host" in data
    assert "port" in data
    assert "onvif_supported" in data
    assert "name" in data
    assert "manufacturer" in data
    assert "model" in data
    assert "streams" in data
    assert "error" in data


@pytest.mark.asyncio
async def test_probe_stream_structure(client: AsyncClient):
    """Test that each stream in probe response has expected structure."""
    mock_result = MagicMock()
    mock_result.name = "Camera"
    mock_result.manufacturer = None
    mock_result.model = None
    mock_result.firmware_version = None
    mock_result.serial_number = None
    mock_result.rtsp_urls = [
        "rtsp://192.168.1.100:554/stream1",
        "rtsp://192.168.1.100:554/stream2",
    ]

    with patch(
        "backend.services.onvif_discovery.onvif_discovery.probe_camera",
        new_callable=AsyncMock,
        return_value=mock_result,
    ):
        response = await client.post(
            "/api/cameras/probe",
            json={"host": "192.168.1.100"},
        )

    data = response.json()

    for stream in data["streams"]:
        assert "name" in stream
        assert "url" in stream
        assert "description" in stream


@pytest.mark.asyncio
async def test_probe_preserves_host_in_response(client: AsyncClient):
    """Test that probe response preserves the requested host."""
    with patch(
        "backend.services.onvif_discovery.onvif_discovery.probe_camera",
        new_callable=AsyncMock,
        return_value=None,
    ):
        response = await client.post(
            "/api/cameras/probe",
            json={"host": "10.0.0.50", "port": 8080},
        )

    data = response.json()
    assert data["host"] == "10.0.0.50"
    assert data["port"] == 8080


@pytest.mark.asyncio
async def test_probe_uses_default_port(client: AsyncClient):
    """Test that probe uses default port 80 when not specified."""
    with patch(
        "backend.services.onvif_discovery.onvif_discovery.probe_camera",
        new_callable=AsyncMock,
        return_value=None,
    ):
        response = await client.post(
            "/api/cameras/probe",
            json={"host": "192.168.1.100"},  # No port specified
        )

    data = response.json()
    assert data["port"] == 80


@pytest.mark.asyncio
async def test_probe_requires_host(client: AsyncClient):
    """Test that probe requires host parameter."""
    response = await client.post(
        "/api/cameras/probe",
        json={},  # Missing host
    )

    assert response.status_code == 422  # Validation error

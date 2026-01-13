"""Tests for camera stream lifecycle management.

These tests verify that streams are automatically started and stopped
when cameras are created, enabled, disabled, or deleted.

Bug reference:
- Streams were not auto-starting when cameras were created with enabled=true
- Streams were not stopping when cameras were deleted, leaving orphaned FFmpeg processes
"""

import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, patch, MagicMock


@pytest.mark.asyncio
async def test_create_enabled_camera_starts_stream(client: AsyncClient):
    """Test that creating a camera with enabled=true auto-starts the stream."""
    mock_manager = MagicMock()
    mock_manager.start_camera = AsyncMock()

    with patch("backend.api.routes.cameras.camera_manager", mock_manager):
        response = await client.post(
            "/api/cameras",
            json={
                "name": "Auto Start Test",
                "rtsp_url": "rtsp://192.168.1.100:554/stream1",
                "enabled": True,
            },
        )

    assert response.status_code == 201

    # Verify start_camera was called
    mock_manager.start_camera.assert_called_once()
    # Verify it was called with the created camera
    call_args = mock_manager.start_camera.call_args[0]
    assert call_args[0].name == "Auto Start Test"


@pytest.mark.asyncio
async def test_create_disabled_camera_does_not_start_stream(client: AsyncClient):
    """Test that creating a camera with enabled=false does not start stream."""
    mock_manager = MagicMock()
    mock_manager.start_camera = AsyncMock()

    with patch("backend.api.routes.cameras.camera_manager", mock_manager):
        response = await client.post(
            "/api/cameras",
            json={
                "name": "Disabled Camera Test",
                "rtsp_url": "rtsp://192.168.1.100:554/stream1",
                "enabled": False,
            },
        )

    assert response.status_code == 201

    # Verify start_camera was NOT called
    mock_manager.start_camera.assert_not_called()


@pytest.mark.asyncio
async def test_enable_camera_starts_stream(client: AsyncClient):
    """Test that enabling a camera auto-starts its stream."""
    mock_manager = MagicMock()
    mock_manager.start_camera = AsyncMock()

    # First create a disabled camera (without auto-start)
    with patch("backend.api.routes.cameras.camera_manager", mock_manager):
        create_response = await client.post(
            "/api/cameras",
            json={
                "name": "Enable Test Camera",
                "rtsp_url": "rtsp://192.168.1.100:554/stream1",
                "enabled": False,
            },
        )
    camera_id = create_response.json()["id"]

    # Reset mock to track only the enable call
    mock_manager.reset_mock()

    # Now enable the camera
    with patch("backend.api.routes.cameras.camera_manager", mock_manager):
        response = await client.post(f"/api/cameras/{camera_id}/enable")

    assert response.status_code == 200
    assert response.json()["enabled"] is True

    # Verify start_camera was called
    mock_manager.start_camera.assert_called_once()


@pytest.mark.asyncio
async def test_disable_camera_stops_stream(client: AsyncClient):
    """Test that disabling a camera stops its stream."""
    mock_manager = MagicMock()
    mock_manager.start_camera = AsyncMock()
    mock_manager.stop_camera = AsyncMock()

    # First create an enabled camera
    with patch("backend.api.routes.cameras.camera_manager", mock_manager):
        create_response = await client.post(
            "/api/cameras",
            json={
                "name": "Disable Test Camera",
                "rtsp_url": "rtsp://192.168.1.100:554/stream1",
                "enabled": True,
            },
        )
    camera_id = create_response.json()["id"]

    # Reset mock
    mock_manager.reset_mock()

    # Now disable the camera
    with patch("backend.api.routes.cameras.camera_manager", mock_manager):
        response = await client.post(f"/api/cameras/{camera_id}/disable")

    assert response.status_code == 200
    assert response.json()["enabled"] is False

    # Verify stop_camera was called with camera_id
    mock_manager.stop_camera.assert_called_once_with(camera_id)


@pytest.mark.asyncio
async def test_delete_camera_stops_stream(client: AsyncClient):
    """Test that deleting a camera stops its stream first.

    Bug: Previously, deleting a camera did not stop its stream,
    leaving orphaned FFmpeg processes.
    """
    mock_manager = MagicMock()
    mock_manager.start_camera = AsyncMock()
    mock_manager.stop_camera = AsyncMock()

    # First create an enabled camera
    with patch("backend.api.routes.cameras.camera_manager", mock_manager):
        create_response = await client.post(
            "/api/cameras",
            json={
                "name": "Delete Test Camera",
                "rtsp_url": "rtsp://192.168.1.100:554/stream1",
                "enabled": True,
            },
        )
    camera_id = create_response.json()["id"]

    # Reset mock
    mock_manager.reset_mock()

    # Now delete the camera
    with patch("backend.api.routes.cameras.camera_manager", mock_manager):
        response = await client.delete(f"/api/cameras/{camera_id}")

    assert response.status_code == 204

    # Verify stop_camera was called with camera_id BEFORE deletion
    mock_manager.stop_camera.assert_called_once_with(camera_id)


@pytest.mark.asyncio
async def test_delete_disabled_camera_still_calls_stop(client: AsyncClient):
    """Test that deleting a disabled camera still tries to stop stream.

    Even if camera is disabled, we should try to stop any stream
    that might be running (defensive programming).
    """
    mock_manager = MagicMock()
    mock_manager.stop_camera = AsyncMock()

    # Create disabled camera
    with patch("backend.api.routes.cameras.camera_manager", mock_manager):
        create_response = await client.post(
            "/api/cameras",
            json={
                "name": "Delete Disabled Test",
                "rtsp_url": "rtsp://192.168.1.100:554/stream1",
                "enabled": False,
            },
        )
    camera_id = create_response.json()["id"]

    # Reset mock
    mock_manager.reset_mock()

    # Delete the camera
    with patch("backend.api.routes.cameras.camera_manager", mock_manager):
        response = await client.delete(f"/api/cameras/{camera_id}")

    assert response.status_code == 204

    # stop_camera should still be called (defensive)
    mock_manager.stop_camera.assert_called_once_with(camera_id)


@pytest.mark.asyncio
async def test_start_failure_does_not_prevent_camera_creation(client: AsyncClient):
    """Test that camera is still created even if stream fails to start."""
    mock_manager = MagicMock()
    mock_manager.start_camera = AsyncMock(side_effect=Exception("FFmpeg not found"))

    with patch("backend.api.routes.cameras.camera_manager", mock_manager):
        response = await client.post(
            "/api/cameras",
            json={
                "name": "Fail Start Camera",
                "rtsp_url": "rtsp://192.168.1.100:554/stream1",
                "enabled": True,
            },
        )

    # Camera should still be created successfully
    assert response.status_code == 201
    assert response.json()["name"] == "Fail Start Camera"


@pytest.mark.asyncio
async def test_stop_failure_does_not_prevent_camera_deletion(client: AsyncClient):
    """Test that camera is still deleted even if stream fails to stop."""
    mock_manager = MagicMock()
    mock_manager.start_camera = AsyncMock()
    mock_manager.stop_camera = AsyncMock(side_effect=Exception("Process not found"))

    # Create camera
    with patch("backend.api.routes.cameras.camera_manager", mock_manager):
        create_response = await client.post(
            "/api/cameras",
            json={
                "name": "Fail Stop Camera",
                "rtsp_url": "rtsp://192.168.1.100:554/stream1",
                "enabled": True,
            },
        )
    camera_id = create_response.json()["id"]

    # Delete should succeed even if stop fails
    with patch("backend.api.routes.cameras.camera_manager", mock_manager):
        response = await client.delete(f"/api/cameras/{camera_id}")

    assert response.status_code == 204

    # Verify camera is actually gone
    get_response = await client.get(f"/api/cameras/{camera_id}")
    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_enable_failure_does_not_prevent_state_change(client: AsyncClient):
    """Test that camera is still enabled in DB even if stream fails to start."""
    mock_manager = MagicMock()
    mock_manager.start_camera = AsyncMock(side_effect=Exception("Stream error"))

    # Create disabled camera
    with patch("backend.api.routes.cameras.camera_manager", mock_manager):
        create_response = await client.post(
            "/api/cameras",
            json={
                "name": "Fail Enable Camera",
                "rtsp_url": "rtsp://192.168.1.100:554/stream1",
                "enabled": False,
            },
        )
    camera_id = create_response.json()["id"]

    # Reset mock
    mock_manager.reset_mock()

    # Enable should succeed even if stream fails
    with patch("backend.api.routes.cameras.camera_manager", mock_manager):
        response = await client.post(f"/api/cameras/{camera_id}/enable")

    # Camera should be enabled in DB
    assert response.status_code == 200
    assert response.json()["enabled"] is True

"""Tests for camera API endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_cameras_empty(client: AsyncClient):
    """Test listing cameras when none exist."""
    response = await client.get("/api/cameras")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_create_camera(client: AsyncClient):
    """Test creating a new camera."""
    camera_data = {
        "name": "Test Camera",
        "rtsp_url": "rtsp://192.168.1.100:554/stream1",
        "description": "A test camera",
    }

    response = await client.post("/api/cameras", json=camera_data)
    assert response.status_code == 201

    data = response.json()
    assert data["name"] == "Test Camera"
    assert data["rtsp_url"] == "rtsp://192.168.1.100:554/stream1"
    assert data["description"] == "A test camera"
    assert data["enabled"] is True
    assert data["recording_enabled"] is True
    assert "id" in data


@pytest.mark.asyncio
async def test_create_camera_duplicate_name(client: AsyncClient):
    """Test that duplicate camera names are rejected."""
    camera_data = {
        "name": "Duplicate Camera",
        "rtsp_url": "rtsp://192.168.1.100:554/stream1",
    }

    # Create first camera
    response = await client.post("/api/cameras", json=camera_data)
    assert response.status_code == 201

    # Try to create duplicate
    response = await client.post("/api/cameras", json=camera_data)
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_get_camera(client: AsyncClient):
    """Test getting a specific camera."""
    # Create camera first
    camera_data = {
        "name": "Get Test Camera",
        "rtsp_url": "rtsp://192.168.1.101:554/stream1",
    }
    create_response = await client.post("/api/cameras", json=camera_data)
    camera_id = create_response.json()["id"]

    # Get the camera
    response = await client.get(f"/api/cameras/{camera_id}")
    assert response.status_code == 200
    assert response.json()["name"] == "Get Test Camera"


@pytest.mark.asyncio
async def test_get_camera_not_found(client: AsyncClient):
    """Test getting a non-existent camera."""
    response = await client.get("/api/cameras/non-existent-id")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_camera(client: AsyncClient):
    """Test updating a camera."""
    # Create camera first
    camera_data = {
        "name": "Update Test Camera",
        "rtsp_url": "rtsp://192.168.1.102:554/stream1",
    }
    create_response = await client.post("/api/cameras", json=camera_data)
    camera_id = create_response.json()["id"]

    # Update the camera
    update_data = {
        "name": "Updated Camera Name",
        "description": "Updated description",
    }
    response = await client.put(f"/api/cameras/{camera_id}", json=update_data)
    assert response.status_code == 200
    assert response.json()["name"] == "Updated Camera Name"
    assert response.json()["description"] == "Updated description"


@pytest.mark.asyncio
async def test_delete_camera(client: AsyncClient):
    """Test deleting a camera."""
    # Create camera first
    camera_data = {
        "name": "Delete Test Camera",
        "rtsp_url": "rtsp://192.168.1.103:554/stream1",
    }
    create_response = await client.post("/api/cameras", json=camera_data)
    camera_id = create_response.json()["id"]

    # Delete the camera
    response = await client.delete(f"/api/cameras/{camera_id}")
    assert response.status_code == 204

    # Verify it's gone
    get_response = await client.get(f"/api/cameras/{camera_id}")
    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_enable_disable_camera(client: AsyncClient):
    """Test enabling and disabling a camera."""
    # Create camera first
    camera_data = {
        "name": "Toggle Test Camera",
        "rtsp_url": "rtsp://192.168.1.104:554/stream1",
    }
    create_response = await client.post("/api/cameras", json=camera_data)
    camera_id = create_response.json()["id"]

    # Disable the camera
    response = await client.post(f"/api/cameras/{camera_id}/disable")
    assert response.status_code == 200
    assert response.json()["enabled"] is False

    # Enable the camera
    response = await client.post(f"/api/cameras/{camera_id}/enable")
    assert response.status_code == 200
    assert response.json()["enabled"] is True


@pytest.mark.asyncio
async def test_discover_cameras(client: AsyncClient):
    """Test camera discovery endpoint (placeholder)."""
    response = await client.post("/api/cameras/discover")
    assert response.status_code == 200
    assert response.json() == []  # Placeholder returns empty list

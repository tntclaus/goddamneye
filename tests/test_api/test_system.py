"""Tests for system API endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    """Test health check endpoint."""
    response = await client.get("/api/health")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data
    assert "timestamp" in data


@pytest.mark.asyncio
async def test_system_info(client: AsyncClient):
    """Test system info endpoint."""
    response = await client.get("/api/system/info")
    assert response.status_code == 200

    data = response.json()
    assert data["app_name"] == "GodDamnEye"
    assert "version" in data
    assert "storage_path" in data

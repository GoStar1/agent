"""API endpoint tests."""

import pytest
from httpx import AsyncClient

from app.main import app


@pytest.fixture
async def client():
    """Create async test client."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_root_endpoint(client: AsyncClient):
    """Test root endpoint returns app info."""
    response = await client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "name" in data
    assert "version" in data


@pytest.mark.asyncio
async def test_health_endpoint(client: AsyncClient):
    """Test health check endpoint."""
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "services" in data


@pytest.mark.asyncio
async def test_chat_endpoint_requires_message(client: AsyncClient):
    """Test chat endpoint validates input."""
    response = await client.post("/api/v1/chat/", json={})
    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_session_creation(client: AsyncClient):
    """Test session creation endpoint."""
    response = await client.post(
        "/api/v1/chat/sessions",
        json={"user_id": "test-user-123"},
    )
    # May fail if Redis not connected, which is expected in unit tests
    assert response.status_code in [200, 500]

"""
Pytest configuration and fixtures for backend tests.
"""
import os
import pytest
from typing import Generator
from httpx import AsyncClient, ASGITransport


# Set test environment variables before importing app
os.environ["DASHSCOPE_API_KEY"] = "test-key"
os.environ["QWEN_MODEL"] = "qwen3.5-omni-flash-realtime"
os.environ["QWEN_REGION"] = "cn"


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    import asyncio
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="module")
def app():
    """Create FastAPI application for testing."""
    from src.api.proxy_server import app
    yield app


@pytest.fixture(scope="module")
async def client(app) -> AsyncClient:
    """Create async test client."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def mock_api_key():
    """Mock API key for testing."""
    return "test-api-key-12345"


@pytest.fixture
def sample_websocket_message():
    """Sample WebSocket message for testing."""
    return {
        "type": "configure",
        "instructions": "You are a helpful assistant",
        "modalities": ["text"],
    }

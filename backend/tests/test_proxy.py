"""
Tests for WebSocket proxy server.
"""
import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch


class TestHealthEndpoint:
    """Test health check endpoint."""

    @pytest.mark.asyncio
    async def test_health_check(self, client):
        """Test health check returns ok."""
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "timestamp" in data

    @pytest.mark.asyncio
    async def test_api_status(self, client):
        """Test API status endpoint."""
        response = await client.get("/api/status")
        assert response.status_code == 200
        data = response.json()
        assert data["provider"] == "qwen"
        assert "model" in data
        assert "audio_config" in data


class TestProxySession:
    """Test proxy session functionality."""

    def test_proxy_session_initialization(self):
        """Test ProxySession initializes correctly."""
        from src.api.proxy_server import ProxySession

        mock_ws = MagicMock()
        session = ProxySession(mock_ws)

        assert session.browser_ws == mock_ws
        assert session.dashscope_ws is None
        assert session.is_connected is False
        assert session.session_id is None

    def test_next_event_id(self):
        """Test event ID generation."""
        from src.api.proxy_server import next_event_id

        id1 = next_event_id()
        id2 = next_event_id()

        assert id1.startswith("evt_")
        assert id1 != id2

"""Integration tests for AI Assistant FastAPI HTTP routes."""

from __future__ import annotations

import pytest
from app.main import create_app
from starlette.testclient import TestClient


@pytest.fixture
def client() -> TestClient:
    """Create a TestClient against the instantiated app."""
    app = create_app()
    return TestClient(app)


def test_ai_routes_config_and_model(client: TestClient) -> None:
    """Test /config and /model query and model switching."""
    # Config
    resp_cfg = client.get("/api/v1/ai/config")
    assert resp_cfg.status_code == 200
    data_cfg = resp_cfg.json()
    assert "models" in data_cfg
    assert data_cfg["ready"] is True

    # Model GET
    resp_m = client.get("/api/v1/ai/model")
    assert resp_m.status_code == 200

    # Model POST
    resp_sel = client.post(
        "/api/v1/ai/model",
        json={"model": "claude-3-5-sonnet-20241022"},
    )
    assert resp_sel.status_code == 200
    assert resp_sel.json()["currentModel"] == "claude-3-5-sonnet-20241022"

    # Model POST error
    resp_err = client.post("/api/v1/ai/model", json={"model": ""})
    assert resp_err.status_code == 422


def test_ai_routes_chat_and_completion(client: TestClient) -> None:
    """Test /chat turn execution and /complete one-shot generation."""
    # Chat turn
    resp_chat = client.post(
        "/api/v1/ai/chat",
        json={"message": "List available projects", "sessionId": "session-1"},
    )
    assert resp_chat.status_code == 200
    data_chat = resp_chat.json()
    assert "success" in data_chat
    assert data_chat["toolCalls"] >= 1
    assert len(data_chat["steps"]) >= 1

    # Completion
    resp_comp = client.post(
        "/api/v1/ai/complete",
        json={
            "prompt": "Generate strategy summary",
            "system": "You are a quant analyst.",
        },
    )
    assert resp_comp.status_code == 200
    assert "strategy summary" in resp_comp.json()["success"]


def test_ai_routes_turn_status_and_stop(client: TestClient) -> None:
    """Test /turn status endpoint and /stop cancellation."""
    # Turn status
    resp_turn = client.get("/api/v1/ai/turn", params={"sessionId": "session-1"})
    assert resp_turn.status_code == 200
    assert resp_turn.json()["running"] is False

    # Stop turn
    resp_stop = client.post("/api/v1/ai/stop", json={"sessionId": "session-1"})
    assert resp_stop.status_code == 200
    assert "success" in resp_stop.json()


def test_ai_routes_memory_settings(client: TestClient) -> None:
    """Test /memory GET and POST endpoints."""
    # GET
    resp_get = client.get("/api/v1/ai/memory")
    assert resp_get.status_code == 200
    assert resp_get.json()["enabled"] is True

    # POST
    resp_set = client.post(
        "/api/v1/ai/memory",
        json={"enabled": False, "flushIntervalMinutes": 10.0},
    )
    assert resp_set.status_code == 200
    assert resp_set.json()["enabled"] is False
    assert resp_set.json()["flushIntervalMinutes"] == 10.0


def test_ai_routes_sessions_crud(client: TestClient) -> None:
    """Test /sessions endpoints: list, create, history, clear, and delete."""
    # List
    resp_list = client.get("/api/v1/ai/sessions")
    assert resp_list.status_code == 200
    assert len(resp_list.json()) >= 1

    # Create
    resp_create = client.post(
        "/api/v1/ai/sessions",
        json={"name": "Alpha Portfolio", "project": "TrendFollowing"},
    )
    assert resp_create.status_code == 200
    sid = resp_create.json()["sessionId"]
    assert resp_create.json()["name"] == "Alpha Portfolio"

    # History
    resp_hist = client.get(f"/api/v1/ai/sessions/{sid}/history")
    assert resp_hist.status_code == 200
    assert len(resp_hist.json()) >= 1

    # History 404
    resp_h404 = client.get("/api/v1/ai/sessions/non-existent-sid/history")
    assert resp_h404.status_code == 404

    # Clear
    resp_clear = client.post(f"/api/v1/ai/sessions/{sid}/clear")
    assert resp_clear.status_code == 200
    assert resp_clear.json()["success"] is True

    # Clear 404
    resp_c404 = client.post("/api/v1/ai/sessions/non-existent-sid/clear")
    assert resp_c404.status_code == 404

    # Delete
    resp_del = client.delete(f"/api/v1/ai/sessions/{sid}")
    assert resp_del.status_code == 200
    assert resp_del.json()["success"] is True

    # Delete 404
    resp_d404 = client.delete("/api/v1/ai/sessions/non-existent-sid")
    assert resp_d404.status_code == 404


def test_ai_routes_mcp_servers_and_tools(client: TestClient) -> None:
    """Test /mcp/servers and /mcp/tools endpoints."""
    # List servers
    resp_servers = client.get("/api/v1/ai/mcp/servers")
    assert resp_servers.status_code == 200
    assert len(resp_servers.json()) >= 1

    # Register server
    new_srv = {
        "id": "srv-test-endpoint",
        "name": "Integration Test Server",
        "url": "http://localhost:9090/mcp",
        "transport": "sse",
        "status": "Connected",
        "capabilities": ["strategy_generation"],
        "active_calls": 0,
    }
    resp_save = client.post("/api/v1/ai/mcp/servers", json=new_srv)
    assert resp_save.status_code == 200
    assert resp_save.json()["id"] == "srv-test-endpoint"

    # Ping server
    resp_ping = client.post("/api/v1/ai/mcp/servers/ping", json=new_srv)
    assert resp_ping.status_code == 200
    assert resp_ping.json()["success"] is True

    # Delete server
    resp_del_srv = client.delete("/api/v1/ai/mcp/servers/srv-test-endpoint")
    assert resp_del_srv.status_code == 200
    assert resp_del_srv.json()["success"] is True

    resp_del_404 = client.delete("/api/v1/ai/mcp/servers/srv-test-endpoint")
    assert resp_del_404.status_code == 404

    # List tools
    resp_tools = client.get("/api/v1/ai/mcp/tools")
    assert resp_tools.status_code == 200
    tools_list = resp_tools.json()
    assert len(tools_list) >= 1
    tool_names = [t["name"] for t in tools_list]
    assert "list_projects" in tool_names

    # Call tool
    resp_call = client.post(
        "/api/v1/ai/mcp/tools/call",
        json={"name": "list_projects", "arguments": {}},
    )
    assert resp_call.status_code == 200
    assert resp_call.json()["is_error"] is False
    assert len(resp_call.json()["content"]) >= 1

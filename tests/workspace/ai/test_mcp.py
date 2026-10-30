"""Unit tests for Model Context Protocol (MCP) tool registry and servers."""

from __future__ import annotations

import json
from typing import Any

from app.workspace.ai.mcp import McpServerRegistry, MCPTools
from app.workspace.ai.mcp_models import McpJsonSchema, McpServerConfig, McpToolSpec


def test_mcp_tools_default_specifications() -> None:
    """Test that default built-in MCP tool specs are correctly registered."""
    tools = MCPTools()
    specs = tools.get_tool_specs()
    names = {s.name for s in specs}
    assert "list_projects" in names
    assert "list_databanks" in names
    assert "list_strategies" in names
    assert "get_strategy_stats" in names
    assert "run_project" in names
    assert "stop_project" in names


def test_mcp_tool_execution_success() -> None:
    """Test successful tool execution for project queries and stats."""
    tools = MCPTools()

    # list_projects
    res = tools.execute_tool("list_projects", {})
    assert not res.is_error
    assert len(res.content) == 1
    data = json.loads(res.content[0].text)
    assert "projects" in data
    assert len(data["projects"]) > 0

    # list_databanks
    res_db = tools.execute_tool("list_databanks", {"name": "Alpha Momentum"})
    assert not res_db.is_error
    data_db = json.loads(res_db.content[0].text)
    assert data_db["project"] == "Alpha Momentum"
    assert "databanks" in data_db

    # list_strategies
    res_strat = tools.execute_tool(
        "list_strategies",
        {"name": "Alpha Momentum", "databank": "Results"},
    )
    assert not res_strat.is_error
    data_strat = json.loads(res_strat.content[0].text)
    assert "strategies" in data_strat

    # get_strategy_stats
    res_stats = tools.execute_tool(
        "get_strategy_stats",
        {"name": "Alpha Momentum", "databank": "Results", "strategy": "Strategy 1.01"},
    )
    assert not res_stats.is_error
    data_stats = json.loads(res_stats.content[0].text)
    assert data_stats["strategy"] == "Strategy 1.01"
    assert "profitFactor" in data_stats

    # run_project & stop_project
    res_run = tools.execute_tool("run_project", {"name": "TestProj"})
    assert not res_run.is_error
    assert json.loads(res_run.content[0].text)["status"] == "started"

    res_stop = tools.execute_tool("stop_project", {"name": "TestProj"})
    assert not res_stop.is_error
    assert json.loads(res_stop.content[0].text)["status"] == "stopped"


def test_mcp_tool_execution_errors() -> None:
    """Test error handling for unknown tools and missing arguments."""
    tools = MCPTools()

    # Unknown tool
    res_unknown = tools.execute_tool("non_existent_tool", {})
    assert res_unknown.is_error
    assert "Unknown tool" in res_unknown.content[0].text

    # Missing required parameter
    res_missing = tools.execute_tool("list_databanks", {})
    assert res_missing.is_error
    assert "Missing required parameter" in res_missing.content[0].text


def test_mcp_tool_custom_registration() -> None:
    """Test registering a custom tool and handling exceptions."""
    tools = MCPTools()

    def fail_handler(_args: dict[str, Any]) -> str:
        raise ValueError("Simulated handler crash")

    tools.register_tool(
        McpToolSpec(
            name="faulty_tool",
            description="Tool that raises error",
            input_schema=McpJsonSchema(type="object", properties={}, required=[]),
        ),
        handler=fail_handler,
    )

    res = tools.execute_tool("faulty_tool", {})
    assert res.is_error
    assert "Simulated handler crash" in res.content[0].text


def test_mcp_server_registry() -> None:
    """Test server registry registration, lookup, listing, removal, and ping."""
    registry = McpServerRegistry()

    # Default server is registered
    servers = registry.list_servers()
    assert len(servers) >= 1
    assert any(s.id == "mcp-local-gateway" for s in servers)

    # Register new server
    new_srv = McpServerConfig(
        id="srv-custom",
        name="Custom Remote Gateway",
        url="https://api.quantgateway.internal/mcp",
        transport="sse",
        capabilities=["custom_algo"],
    )
    registered = registry.register_server(new_srv)
    assert registered.id == "srv-custom"

    found = registry.get_server("srv-custom")
    assert found is not None
    assert found.name == "Custom Remote Gateway"

    # Ping test
    ping_ok = registry.ping_server(found)
    assert ping_ok.success
    assert "MCP Protocol v1.0" in ping_ok.message

    # Invalid URL ping
    bad_srv = McpServerConfig(
        id="srv-bad",
        name="Bad URL",
        url="ftp://invalid-scheme",
        transport="sse",
    )
    ping_bad = registry.ping_server(bad_srv)
    assert not ping_bad.success

    # Remove server
    assert registry.remove_server("srv-custom")
    assert registry.get_server("srv-custom") is None
    assert not registry.remove_server("non-existent")

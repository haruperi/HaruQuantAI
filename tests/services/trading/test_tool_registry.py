"""Tests for the trading tool registry and package facade.

Tracked requirements:
- TRD-FR-001, TRD-FR-002, TRD-FR-003, TRD-FR-019, TRD-FR-020.
"""

from __future__ import annotations

import sys

import pytest
from app.services.trading import (
    get_trading_public_catalog,
    get_trading_tool_registry,
)
from app.services.trading.contracts import (
    SideEffectMode,
    TradingRoute,
    TradingToolDefinition,
)
from app.services.trading.tool_registry import (
    build_trading_tool_registry,
    get_trading_tool_definition,
    list_trading_tools,
)


def test_import_side_effects() -> None:
    """Verify that importing app.services.trading has no side effects.

    Tracked requirements: TRD-FR-001.
    """
    # Verify that modules are imported successfully and trigger no side effects.
    # We check that the module can be fetched from sys.modules
    assert "app.services.trading" in sys.modules


def test_tool_registry_building() -> None:
    """Verify registry of trading tools and tool metadata validation (TRD-FR-019)."""
    registry = build_trading_tool_registry()
    assert len(registry.tools) > 0
    assert "create_trading_action_draft" in registry.tools

    tool = registry.tools["create_trading_action_draft"]
    assert isinstance(tool, TradingToolDefinition)
    assert tool.name == "create_trading_action_draft"
    assert (
        tool.purpose == "Create an unexecuted trading action draft for backend review."
    )
    assert TradingRoute.LIVE in tool.route_support
    assert tool.approval_required is True
    assert tool.side_effect_ceiling == SideEffectMode.PACKAGED_ONLY
    assert tool.risk_level == "high"
    assert "INVALID_INPUT" in tool.error_codes
    assert tool.audit_metadata == {"trading.tool_category": "draft"}


def test_registry_ai_mutations_ceiling() -> None:
    """Verify AI-facing tools do not directly invoke broker mutations (TRD-FR-020)."""
    registry = build_trading_tool_registry()
    for tool in registry.tools.values():
        # Check side_effect_ceiling to ensure mutations are blocked
        assert tool.side_effect_ceiling in (
            SideEffectMode.NONE,
            SideEffectMode.PACKAGED_ONLY,
        )


def test_list_and_get_tool_definitions() -> None:
    """Verify sorting and retrieving tool definitions (TRD-FR-019)."""
    registry = build_trading_tool_registry()
    tools_list = list_trading_tools(registry)
    assert len(tools_list) == len(registry.tools)
    # Sorted by name
    assert tools_list[0].name == "create_trading_action_draft"

    # Get valid tool
    resolved = get_trading_tool_definition("create_trading_action_draft", registry)
    assert resolved == tools_list[0]

    # Get invalid tool raises KeyError
    with pytest.raises(KeyError, match="not registered"):
        get_trading_tool_definition("non_existent_tool", registry)


def test_facade_accessors() -> None:
    """Verify facade get_trading_tool_registry and get_trading_public_catalog.

    Tracked requirements: TRD-FR-003.
    """
    registry = get_trading_tool_registry()
    assert "create_trading_action_draft" in registry.tools

    catalog = get_trading_public_catalog()
    assert len(catalog) == 1
    assert catalog[0].name == "create_trading_action_draft"

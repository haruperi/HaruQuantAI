"""Pure trading tool registry accessors.

The registry is intentionally conservative at package creation time: it exposes
no mutation-capable tools and performs no broker or infrastructure work at
import time.
"""

from __future__ import annotations

from app.services.trading.contracts import (
    SideEffectMode,
    TradingRoute,
    TradingToolDefinition,
    TradingToolRegistry,
)
from app.utils.logger import logger


def build_trading_tool_registry() -> TradingToolRegistry:
    """Build the approved trading tool registry.

    Returns:
        TradingToolRegistry: Side-effect-free registry of AI-facing trading
        tool definitions.
    """
    logger.info("Building trading tool registry.")
    draft_tool = TradingToolDefinition(
        name="create_trading_action_draft",
        purpose="Create an unexecuted trading action draft for backend review.",
        route_support=(
            TradingRoute.SIM,
            TradingRoute.PAPER,
            TradingRoute.SHADOW,
            TradingRoute.LIVE,
        ),
        input_schema={
            "type": "object",
            "additionalProperties": False,
        },
        output_schema={
            "type": "object",
            "additionalProperties": False,
        },
        approval_required=True,
        side_effect_ceiling=SideEffectMode.PACKAGED_ONLY,
        risk_level="high",
        error_codes=("INVALID_INPUT", "APPROVAL_REQUIRED"),
        audit_metadata={"trading.tool_category": "draft"},
    )
    return TradingToolRegistry(tools={draft_tool.name: draft_tool})


def list_trading_tools(
    registry: TradingToolRegistry,
) -> tuple[TradingToolDefinition, ...]:
    """List deterministic public trading tool definitions.

    Args:
        registry: Trading tool registry to list.

    Returns:
        tuple[TradingToolDefinition, ...]: Tool definitions sorted by name.
    """
    logger.info("Listing {} trading tools.", len(registry.tools))
    return tuple(sorted(registry.tools.values(), key=lambda tool: tool.name))


def get_trading_tool_definition(
    name: str,
    registry: TradingToolRegistry,
) -> TradingToolDefinition:
    """Resolve a trading tool definition by name.

    Args:
        name: Tool name.
        registry: Trading tool registry.

    Returns:
        TradingToolDefinition: Resolved tool metadata.

    Raises:
        KeyError: If the tool is not registered.
    """
    logger.info("Resolving trading tool definition {}.", name)
    if name not in registry.tools:
        message = f"Trading tool '{name}' is not registered."
        raise KeyError(message)
    return registry.tools[name]

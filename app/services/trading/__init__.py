"""Trading runtime public facade.

Importing this package is side-effect free. It does not connect to brokers,
resolve secrets, open databases, create sockets, start threads, or schedule
background work.
"""

from __future__ import annotations

from app.services.trading.contracts import (
    AllocationVector,
    BrokerAcknowledgementEvent,
    BrokerDispatchEvent,
    ExecutionReportEvent,
    FixExecutionState,
    JsonObject,
    JsonValue,
    MutationCapability,
    NormalizedTradeResult,
    OrderState,
    PositionState,
    PromotionStage,
    QuoteSnapshot,
    ReconciliationResolutionEvent,
    RegulatoryTags,
    RetrySafety,
    SideEffectMode,
    TimeInForce,
    TradingAction,
    TradingCommandAccepted,
    TradingCommandRejected,
    TradingError,
    TradingMetadata,
    TradingRequestEnvelope,
    TradingResponseEnvelope,
    TradingRoute,
    TradingStatus,
    TradingToolDefinition,
    TradingToolRegistry,
)
from app.services.trading.execution import ExecutionCoordinator
from app.services.trading.tool_registry import (
    build_trading_tool_registry,
    list_trading_tools,
)
from app.utils.logger import logger


def get_trading_tool_registry() -> TradingToolRegistry:
    """Return the official trading tool registry.

    Returns:
        TradingToolRegistry: Purely constructed trading tool registry.
    """
    logger.info("Creating trading tool registry via public accessor.")
    return build_trading_tool_registry()


def get_trading_public_catalog() -> tuple[TradingToolDefinition, ...]:
    """Return the deterministic public trading tool catalog.

    Returns:
        tuple[TradingToolDefinition, ...]: Public tool definitions sorted by
        name.
    """
    logger.info("Creating trading public catalog via public accessor.")
    return list_trading_tools(get_trading_tool_registry())


__all__ = [
    "AllocationVector",
    "BrokerAcknowledgementEvent",
    "BrokerDispatchEvent",
    "ExecutionCoordinator",
    "ExecutionReportEvent",
    "FixExecutionState",
    "JsonObject",
    "JsonValue",
    "MutationCapability",
    "NormalizedTradeResult",
    "OrderState",
    "PositionState",
    "PromotionStage",
    "QuoteSnapshot",
    "ReconciliationResolutionEvent",
    "RegulatoryTags",
    "RetrySafety",
    "SideEffectMode",
    "TimeInForce",
    "TradingAction",
    "TradingCommandAccepted",
    "TradingCommandRejected",
    "TradingError",
    "TradingMetadata",
    "TradingRequestEnvelope",
    "TradingResponseEnvelope",
    "TradingRoute",
    "TradingStatus",
    "TradingToolDefinition",
    "TradingToolRegistry",
    "get_trading_public_catalog",
    "get_trading_tool_registry",
]

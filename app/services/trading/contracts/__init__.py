"""Approved public contracts for the Trading domain."""

from typing import Any

from app.services.trading.contracts.errors import (
    TradingError,
    map_trading_error,
    redact_trading_payload,
)
from app.services.trading.contracts.models import (
    TRADING_CONTRACT_VERSION,
    ExecutionEvidenceReport,
    ExecutionReceipt,
    OrderIntent,
    PortfolioRebalanceExecutionRequest,
    TradeRecord,
    TradingRequest,
    TradingRoute,
)
from app.services.trading.contracts.registry import (
    create_trading_action_draft,
    get_public_contracts,
)

type StandardResponse[T] = Any

__all__ = [
    "TRADING_CONTRACT_VERSION",
    "ExecutionEvidenceReport",
    "ExecutionReceipt",
    "OrderIntent",
    "PortfolioRebalanceExecutionRequest",
    "StandardResponse",
    "TradeRecord",
    "TradingError",
    "TradingRequest",
    "TradingRoute",
    "create_trading_action_draft",
    "get_public_contracts",
    "map_trading_error",
    "redact_trading_payload",
]

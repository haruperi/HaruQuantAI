"""Approved public contracts for the Trading domain."""

from typing import Any

from app.services.trading.contracts.errors import (
    TradingError as TradingError,
)
from app.services.trading.contracts.errors import (
    map_trading_error,
    redact_trading_payload,
)
from app.services.trading.contracts.factories import (
    create_closed_position_record,
    create_execution_evidence_report,
    create_execution_receipt,
    create_order_intent,
    create_portfolio_rebalance_execution_request,
    create_trade_record,
    create_trading_error,
    create_trading_request,
    get_trading_contract_version,
    get_trading_route,
    is_execution_receipt,
    is_trading_error,
)
from app.services.trading.contracts.models import (
    TRADING_CONTRACT_VERSION as TRADING_CONTRACT_VERSION,
)
from app.services.trading.contracts.models import (
    ExecutionEvidenceReport as ExecutionEvidenceReport,
)
from app.services.trading.contracts.models import (
    ExecutionReceipt as ExecutionReceipt,
)
from app.services.trading.contracts.models import (
    OrderIntent as OrderIntent,
)
from app.services.trading.contracts.models import (
    PortfolioRebalanceExecutionRequest as PortfolioRebalanceExecutionRequest,
)
from app.services.trading.contracts.models import (
    TradeRecord as TradeRecord,
)
from app.services.trading.contracts.models import (
    TradingRequest as TradingRequest,
)
from app.services.trading.contracts.models import (
    TradingRoute as TradingRoute,
)
from app.services.trading.contracts.registry import (
    create_trading_action_draft,
    get_public_contracts,
)

type StandardResponse[T] = Any

__all__ = [
    "create_closed_position_record",
    "create_execution_evidence_report",
    "create_execution_receipt",
    "create_order_intent",
    "create_portfolio_rebalance_execution_request",
    "create_trade_record",
    "create_trading_action_draft",
    "create_trading_error",
    "create_trading_request",
    "get_public_contracts",
    "get_trading_contract_version",
    "get_trading_route",
    "is_execution_receipt",
    "is_trading_error",
    "map_trading_error",
    "redact_trading_payload",
]

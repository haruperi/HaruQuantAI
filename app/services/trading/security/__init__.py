"""Trading runtime security boundary exports.

This package contains import-safe helpers for trading error mapping, recursive
redaction, and durable dead-letter handling. It does not import broker SDKs or
perform network operations.
"""

from __future__ import annotations

from app.services.trading.security.error_mapping import (
    TradingMappedError,
    TradingPermissionError,
    TradingServiceUnavailableError,
    TradingTimeoutError,
    TradingValidationError,
    map_exception_to_trading_error,
)
from app.services.trading.security.redaction_boundary import (
    DeadLetterRecord,
    DeadLetterWriteResult,
    ManualReviewRecord,
    RedactionBoundaryResult,
    WriteAheadDeadLetterQueue,
    redact_for_boundary,
)
from app.utils.logger import logger

logger.info("Loaded trading security package exports.")

__all__ = [
    "DeadLetterRecord",
    "DeadLetterWriteResult",
    "ManualReviewRecord",
    "RedactionBoundaryResult",
    "TradingMappedError",
    "TradingPermissionError",
    "TradingServiceUnavailableError",
    "TradingTimeoutError",
    "TradingValidationError",
    "WriteAheadDeadLetterQueue",
    "map_exception_to_trading_error",
    "redact_for_boundary",
]

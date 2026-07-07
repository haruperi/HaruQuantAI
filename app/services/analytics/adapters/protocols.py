"""Trading result adapter protocols and validators (ANL-NFR-095).

This module defines the typing protocol for result adapters and checks their compliance.
It performs no I/O, network calls, database mutations, broker calls, or trading
side effects.
"""

from __future__ import annotations

from typing import Any, Protocol, TypedDict

from app.utils.errors import ValidationError
from app.utils.logger import logger


class TradingResultDict(TypedDict, total=False):
    """Canonical trading result dictionary representation.

    Required keys:
        schema_version: Schema version string.
        result_id: Unique result identifier.
        phase: Execution phase.
        trades: Chronological closed trade record list.
        equity_curve: Chronological equity curve.
    """

    schema_version: str
    result_id: str
    phase: str
    trades: list[dict[str, Any]]
    equity_curve: list[dict[str, Any]]
    strategy_id: str
    strategy_version: str
    account_base_currency: str
    symbols: list[str]
    timeframe: str
    metadata: dict[str, Any]


class BacktestResultDict(TypedDict, total=False):
    """Backtest-specific result dictionary contract."""

    schema_version: str
    result_id: str
    phase: str
    trades: list[dict[str, Any]]
    equity_curve: list[dict[str, Any]]
    in_sample_end: str
    walk_forward_windows: list[dict[str, Any]]


class PaperTradingResultDict(TypedDict, total=False):
    """Paper trading result dictionary contract."""

    schema_version: str
    result_id: str
    phase: str
    trades: list[dict[str, Any]]
    equity_curve: list[dict[str, Any]]


class LiveTradingResultDict(TypedDict, total=False):
    """Live trading result dictionary contract."""

    schema_version: str
    result_id: str
    phase: str
    trades: list[dict[str, Any]]
    equity_curve: list[dict[str, Any]]


class TradingResultAdapter(Protocol):
    """Protocol defining the canonical conversion interface (ANL-NFR-095)."""

    def to_canonical(
        self,
        source_payload: dict[str, Any],
    ) -> dict[str, Any]:
        """Convert a raw dictionary source payload to a canonical dictionary format.

        Args:
            source_payload (dict[str, Any]): Input parameter `source_payload`.

        Returns:
            Calculated dict[str, Any] value.
        """
        ...


def validate_adapter_contract(adapter: Any) -> None:  # noqa: ANN401
    """Validate that an adapter class or instance conforms to the Protocol.

    Args:
        adapter (Any): Input parameter `adapter`.
    """
    logger.debug("validate_adapter_contract: executed.")
    """Validate that an adapter class or instance conforms to the Protocol.

    Args:
        adapter: Target object/adapter class to inspect.

    Raises:
        ValidationError: If the adapter is missing the required methods.
    """
    if not hasattr(adapter, "to_canonical") or not callable(adapter.to_canonical):
        msg = (
            "Adapter contract validation failed: missing callable method "
            "'to_canonical'."
        )
        raise ValidationError(msg)

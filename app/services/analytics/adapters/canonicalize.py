# ruff: noqa: E501
"""Trading result canonicalization engine (ANL-NFR-092, ANL-NFR-093).

Converts various dictionary formats, Pydantic objects, and other shapes into
canonical forms. It maintains backward compatibility with the old to_canonical API.
It performs no I/O, network calls, database mutations, broker calls, or trading
side effects.
"""

from __future__ import annotations

from typing import Any

from app.services.analytics.contracts import (
    SCHEMA_COMPATIBILITY_MATRIX,
    validate_schema_version,
)
from app.services.analytics.contracts.models import (
    BenchmarkData,
    Lineage,
    TradingResult,
)
from app.services.analytics.errors import AnalyticsValidationError as ValidationError
from app.services.simulator.contracts import (
    BacktestResult as UpstreamBacktestResult,
)
from app.utils.logger import logger

# Define type aliases for alternative source formats (ANL-NFR-092)
type BacktestResult = UpstreamBacktestResult | dict[str, Any]
type PaperResult = dict[str, Any]
type LiveResult = dict[str, Any]
type PortfolioResult = dict[str, Any]

_VALID_PHASES = frozenset({"backtest", "paper", "live", "simulation"})


class TradingResultAdapter:
    """Class-level adapter mapping raw dictionary structures to canonical dicts."""

    REQUIRED_KEYS: frozenset[str] = frozenset(
        {
            "schema_version",
            "result_id",
            "phase",
            "trades",
            "equity_curve",
        }
    )

    @classmethod
    def _check_schema_version(cls, schema_version: str) -> list[str]:
        """Validate schema version against standard compatibility rules.

        Args:
            schema_version (str): Input parameter `schema_version`.

        Returns:
            Calculated list[str] value.
        """
        logger.debug("_check_schema_version: executed.")
        # Use our contracts validator to check status
        status = validate_schema_version(schema_version, SCHEMA_COMPATIBILITY_MATRIX)

        warnings: list[str] = []
        if status == "deprecated":
            warnings.append(
                f"schema_version {schema_version!r} is deprecated."
                " Please migrate to a supported version."
            )
        elif status == "legacy_adapted":
            warnings.append(
                f"schema_version {schema_version!r} requires legacy"
                " adaptation. Output may differ from accepted-version output."
            )
        return warnings

    @classmethod
    def to_canonical(cls, source_payload: dict[str, Any]) -> dict[str, Any]:
        """Convert a raw dictionary source payload to a canonical dict.

        Args:
            source_payload (dict[str, Any]): Input parameter `source_payload`.

        Returns:
            Calculated dict[str, Any] value.
        """
        logger.debug("to_canonical: executed.")
        if not isinstance(source_payload, dict):
            raise ValidationError("Trading result source_payload must be a dictionary.")

        missing_keys = cls.REQUIRED_KEYS - source_payload.keys()
        if missing_keys:
            msg = (
                "Missing required keys for canonical TradingResult:"
                f" {sorted(missing_keys)}"
            )
            raise ValidationError(msg)

        schema_version = source_payload.get("schema_version")
        if not isinstance(schema_version, str) or not schema_version.strip():
            raise ValidationError("schema_version must be a non-empty string.")

        adapter_warnings = cls._check_schema_version(schema_version)

        result_id = source_payload.get("result_id")
        if not isinstance(result_id, str) or not result_id.strip():
            raise ValidationError("result_id must be a non-empty string.")

        phase = source_payload.get("phase")
        if phase not in _VALID_PHASES:
            msg = f"phase must be one of: {sorted(_VALID_PHASES)}"
            raise ValidationError(msg)

        trades = source_payload.get("trades")
        if not isinstance(trades, list):
            raise ValidationError("trades must be a list.")

        equity_curve = source_payload.get("equity_curve")
        if not isinstance(equity_curve, list):
            raise ValidationError("equity_curve must be a list.")

        canonical: dict[str, Any] = dict(source_payload)

        if "strategy_id" not in canonical:
            canonical["strategy_id"] = "default_strategy"
            adapter_warnings.append(
                "strategy_id was absent; defaulted to"
                " 'default_strategy'. Provide an explicit strategy_id"
                " for reproducible cross-run comparisons."
            )

        canonical.setdefault("strategy_version", "v1")
        canonical.setdefault("account_base_currency", "USD")
        canonical.setdefault("symbols", [])
        canonical.setdefault("timeframe", "H1")
        canonical.setdefault("metadata", {})

        if adapter_warnings:
            canonical["_adapter_warnings"] = adapter_warnings

        return canonical


def to_canonical(source_payload: dict[str, Any]) -> dict[str, Any]:
    """Module-level convenience wrapper for TradingResultAdapter.to_canonical.

    Args:
        source_payload (dict[str, Any]): Input parameter `source_payload`.

    Returns:
        Calculated dict[str, Any] value.
    """
    logger.debug("to_canonical: executed.")
    return TradingResultAdapter.to_canonical(source_payload)


def to_trading_result(
    source: (
        BacktestResult | PaperResult | LiveResult | PortfolioResult | TradingResult
    ),
) -> TradingResult:
    """Convert raw trading/backtest results into the canonical TradingResult dataclass.

    Args:
        source (BacktestResult | PaperResult | LiveResult | PortfolioResult | TradingResult): Input parameter `source`.

    Returns:
        Calculated TradingResult value.
    """
    logger.debug("to_trading_result: executed.")
    if isinstance(source, TradingResult):
        return source

    # Extract dictionary representation from Pydantic model or other object
    if hasattr(source, "model_dump"):
        data = source.model_dump()
    elif hasattr(source, "__dict__") and not isinstance(source, dict):
        data = source.__dict__
    elif isinstance(source, dict):
        data = source
    else:
        msg = f"Unsupported type for canonicalization: {type(source).__name__}."
        raise ValidationError(msg)

    # Validate and default standard fields
    schema_version = data.get("schema_version") or "1.3.1"
    # Map from result_id or run_id
    result_id = data.get("result_id") or data.get("run_id")
    if not result_id or not isinstance(result_id, str):
        result_id = "UNKNOWN_RESULT_ID"

    # Map environment from phase or environment
    environment = data.get("environment") or data.get("phase") or "simulation"
    if environment not in _VALID_PHASES and environment != "simulation":
        environment = "simulation"

    currency = data.get("account_base_currency") or "USD"

    # Read trades
    raw_trades = data.get("trades") or ()
    trades_tuple = tuple(dict(t) for t in raw_trades)

    # Read equity curve
    raw_equity = data.get("equity_curve") or ()
    equity_tuple = tuple(dict(e) for e in raw_equity)

    # Convert benchmark data if available
    raw_benchmark = data.get("benchmark")
    benchmark_data = None
    if isinstance(raw_benchmark, dict):
        benchmark_data = BenchmarkData(
            symbol=raw_benchmark.get("symbol", "SPY"),
            prices=tuple(raw_benchmark.get("prices", ())),
            returns=tuple(raw_benchmark.get("returns", ())),
            timestamps=tuple(raw_benchmark.get("timestamps", ())),
            metadata=dict(raw_benchmark.get("metadata", {})),
        )

    # Build lineage tracking provenance
    raw_lineage = data.get("lineage")
    if isinstance(raw_lineage, dict):
        lineage_data = Lineage(
            run_id=raw_lineage.get("run_id"),
            strategy_id=raw_lineage.get("strategy_id"),
            dataset_hash=raw_lineage.get("dataset_hash"),
            cost_model=raw_lineage.get("cost_model"),
            fill_model=raw_lineage.get("fill_model"),
            risk_policy_version=raw_lineage.get("risk_policy_version"),
            journal_reference=raw_lineage.get("journal_reference"),
        )
    else:
        # Default empty lineage or default mapped metadata
        lineage_data = Lineage(
            run_id=result_id,
            strategy_id=data.get("strategy_id"),
            journal_reference=data.get("journal_ref"),
        )

    return TradingResult(
        schema_version=schema_version,
        result_id=result_id,
        environment=environment,
        account_base_currency=currency,
        trades=trades_tuple,
        equity_curve=equity_tuple,
        benchmark=benchmark_data,
        lineage=lineage_data,
    )

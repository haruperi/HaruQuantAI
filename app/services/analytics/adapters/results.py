"""Producer-neutral closed-trade ledger adaptation for Analytics."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import UTC, datetime, time
from decimal import Decimal
from typing import cast

from pydantic import ValidationError as PydanticValidationError

from app.services.analytics.contracts.catalogs import validate_contract_version
from app.services.analytics.contracts.errors import AnalyticsValidationError
from app.services.analytics.contracts.models import (
    AnalyticsRunConfig,
    ClosedTrade,
    Lineage,
    TradingResult,
)
from app.utils import canonical_json, logger

_SOURCE_FIELDS = frozenset(
    {
        "contract_version",
        "schema_id",
        "source_id",
        "phase",
        "window_start",
        "window_end",
        "strategy_id",
        "strategy_version",
        "symbols",
        "timeframe",
        "closed_trades",
        "quality_metadata",
        "source_metadata",
    }
)
_TRADE_FIELDS = frozenset(
    {
        "ticket",
        "symbol",
        "type",
        "volume",
        "entry_time",
        "entry_price",
        "stop_loss",
        "take_profit",
        "exit_time",
        "exit_price",
        "comment",
        "commission",
        "swap",
        "profit",
        "magic",
        "mae",
        "mfe",
    }
)
_SCHEMA_BY_CONTRACT = {
    "trading.closed_trade_ledger": "trading.closed_trade_ledger.v1",
    "simulation.result": "simulation.result.v1",
}


def _validate_source_shape(source: Mapping[str, object]) -> None:
    """Validate the exact producer-neutral source field set.

    Args:
        source: Candidate source mapping.

    Raises:
        AnalyticsValidationError: If fields are missing or unknown.
    """
    logger.debug("Validating Analytics source ledger shape")
    observed = set(source)
    if observed != _SOURCE_FIELDS:
        missing = sorted(_SOURCE_FIELDS - observed)
        unknown = sorted(observed - _SOURCE_FIELDS)
        message = f"source ledger fields mismatch; missing={missing}, unknown={unknown}"
        raise AnalyticsValidationError(message)


def _require_mapping(value: object, field_name: str) -> Mapping[str, object]:
    """Validate one mapping input.

    Args:
        value: Candidate value.
        field_name: Diagnostic field name.

    Returns:
        Validated mapping.

    Raises:
        AnalyticsValidationError: If the value is not a mapping.
    """
    logger.debug("Validating Analytics adapter mapping")
    if not isinstance(value, Mapping):
        message = f"{field_name} must be a mapping"
        raise AnalyticsValidationError(message)
    return cast("Mapping[str, object]", value)


def _require_sequence(value: object, field_name: str) -> Sequence[object]:
    """Validate one non-text sequence input.

    Args:
        value: Candidate value.
        field_name: Diagnostic field name.

    Returns:
        Validated sequence.

    Raises:
        AnalyticsValidationError: If the value is not a sequence.
    """
    logger.debug("Validating Analytics adapter sequence")
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        message = f"{field_name} must be a sequence"
        raise AnalyticsValidationError(message)
    return cast("Sequence[object]", value)


def _adapt_trade(row: object) -> ClosedTrade:
    """Adapt one exact closed-trade row.

    Args:
        row: Candidate producer ledger row.

    Returns:
        Immutable Analytics closed trade.

    Raises:
        AnalyticsValidationError: If the row shape or semantics are invalid.
    """
    logger.debug("Adapting Analytics closed-trade row")
    mapping = _require_mapping(row, "closed_trade")
    if set(mapping) != _TRADE_FIELDS:
        raise AnalyticsValidationError("closed-trade row fields do not match v1")
    try:
        return ClosedTrade(**dict(mapping))  # type: ignore[arg-type]
    except (PydanticValidationError, TypeError, ValueError) as error:
        raise AnalyticsValidationError("closed-trade row is invalid") from error


def _validate_benchmark(
    benchmark: Mapping[str, object] | None,
    *,
    config: AnalyticsRunConfig,
) -> None:
    """Validate caller-supplied benchmark point bounds.

    Args:
        benchmark: Optional benchmark evidence.
        config: Required Analytics bounds.

    Raises:
        AnalyticsValidationError: If benchmark points are absent or oversized.
    """
    logger.debug("Validating Analytics benchmark bound")
    if benchmark is None:
        return
    points = _require_sequence(benchmark.get("points"), "benchmark.points")
    if len(points) > config.max_benchmark_points:
        raise AnalyticsValidationError("benchmark exceeds configured point bound")


def _validate_metadata_bound(
    source_metadata: Mapping[str, object],
    *,
    config: AnalyticsRunConfig,
) -> None:
    """Validate bounded source metadata without truncating fields.

    Args:
        source_metadata: Producer metadata mapping.
        config: Required Analytics bounds.

    Raises:
        AnalyticsValidationError: If metadata is unsafe or oversized.
    """
    logger.debug("Validating Analytics source metadata bound")
    try:
        byte_count = len(canonical_json(source_metadata).encode("utf-8"))
    except Exception as error:
        raise AnalyticsValidationError(
            "source metadata is not canonical JSON"
        ) from error
    if byte_count > config.max_warning_detail_bytes:
        raise AnalyticsValidationError("source metadata exceeds configured bound")


def build_closed_trade_equity_curve(
    trades: Sequence[ClosedTrade],
    *,
    initial_balance: Decimal,
    config: AnalyticsRunConfig,
) -> tuple[tuple[Mapping[str, object], ...], tuple[Mapping[str, object], ...]]:
    """Build deterministic trade-indexed and daily closed-trade equity curves.

    Args:
        trades: Canonical closed trades.
        initial_balance: Positive starting account balance.
        config: Required Analytics bounds.

    Returns:
        Trade-indexed curve and UTC calendar-daily resample.

    Raises:
        AnalyticsValidationError: If inputs are empty, invalid, or oversized.
    """
    logger.info("Building deterministic closed-trade equity curves")
    if not isinstance(initial_balance, Decimal) or not initial_balance.is_finite():
        raise AnalyticsValidationError("initial_balance must be a finite Decimal")
    if initial_balance <= 0:
        raise AnalyticsValidationError("initial_balance must be positive")
    if not trades:
        raise AnalyticsValidationError("closed-trade ledger must not be empty")
    if len(trades) > config.max_trades:
        raise AnalyticsValidationError("closed-trade ledger exceeds configured bound")
    ordered = tuple(sorted(trades, key=lambda trade: (trade.exit_time, trade.ticket)))
    if len(ordered) > config.max_equity_points:
        raise AnalyticsValidationError("equity curve exceeds configured point bound")
    equity = initial_balance
    curve: list[Mapping[str, object]] = []
    daily: dict[datetime, Mapping[str, object]] = {}
    for trade in ordered:
        equity += trade.net_trade_pnl
        point: Mapping[str, object] = {
            "timestamp": trade.exit_time,
            "ticket": trade.ticket,
            "equity": equity,
            "net_trade_pnl": trade.net_trade_pnl,
            "curve_basis": "closed_trade",
        }
        curve.append(point)
        day = datetime.combine(trade.exit_time.date(), time.min, tzinfo=UTC)
        daily[day] = {
            "timestamp": day,
            "equity": equity,
            "curve_basis": "closed_trade",
        }
    if len(daily) > config.max_equity_points:
        raise AnalyticsValidationError(
            "daily equity curve exceeds configured point bound"
        )
    return tuple(curve), tuple(daily[key] for key in sorted(daily))


def adapt_trading_result(
    source: Mapping[str, object],
    *,
    source_contract: str,
    initial_balance: Decimal,
    account_currency: str,
    config: AnalyticsRunConfig,
    benchmark: Mapping[str, object] | None = None,
    fx_evidence: Mapping[str, object] | None = None,
) -> TradingResult:
    """Adapt an approved versioned ledger projection to canonical Analytics input.

    Args:
        source: Exact producer-neutral closed-trade ledger projection.
        source_contract: Compatibility-matrix producer identity.
        initial_balance: Positive caller-supplied starting balance.
        account_currency: Required caller-supplied account currency.
        config: Required Analytics bounds and calculation settings.
        benchmark: Optional caller-supplied benchmark evidence.
        fx_evidence: Optional caller-supplied FX conversion evidence.

    Returns:
        Immutable canonical TradingResult.

    Raises:
        AnalyticsValidationError: If source, compatibility, or bounds fail.
    """
    logger.info("Adapting producer-neutral closed-trade ledger for Analytics")
    _validate_source_shape(source)
    version = source["contract_version"]
    schema_id = source["schema_id"]
    if not isinstance(version, str) or not isinstance(schema_id, str):
        raise AnalyticsValidationError("source version and schema_id must be strings")
    validate_contract_version(source_contract, version)
    expected_schema = _SCHEMA_BY_CONTRACT.get(source_contract)
    if expected_schema is None or schema_id != expected_schema:
        raise AnalyticsValidationError("source schema_id is incompatible")
    if not account_currency or account_currency != account_currency.strip():
        raise AnalyticsValidationError("account_currency is required")
    rows = _require_sequence(source["closed_trades"], "closed_trades")
    if len(rows) > config.max_trades:
        raise AnalyticsValidationError("closed-trade ledger exceeds configured bound")
    trades = tuple(_adapt_trade(row) for row in rows)
    curve, daily = build_closed_trade_equity_curve(
        trades, initial_balance=initial_balance, config=config
    )
    _validate_benchmark(benchmark, config=config)
    quality = _require_mapping(source["quality_metadata"], "quality_metadata")
    metadata = _require_mapping(source["source_metadata"], "source_metadata")
    _validate_metadata_bound(metadata, config=config)
    symbols = tuple(
        str(item) for item in _require_sequence(source["symbols"], "symbols")
    )
    lineage = Lineage(
        source_contract=source_contract,
        source_version=version,
        source_schema_id=schema_id,
        source_ids=(str(source["source_id"]),),
        configuration_sources=("caller",),
        account_currency=account_currency,
        transformations=("closed_trade_validation", "closed_trade_equity_curve"),
    )
    try:
        return TradingResult(
            contract_version="v1",
            schema_id="analytics.trading_result.v1",
            source_contract=source_contract,
            source_contract_version=version,
            source_schema_id=schema_id,
            source_id=str(source["source_id"]),
            phase=str(source["phase"]),
            window_start=cast("datetime", source["window_start"]),
            window_end=cast("datetime", source["window_end"]),
            account_currency=account_currency,
            initial_balance=initial_balance,
            strategy_id=str(source["strategy_id"]),
            strategy_version=str(source["strategy_version"]),
            symbols=symbols,
            timeframe=str(source["timeframe"]),
            trades=trades,
            equity_curve=curve,
            daily_equity_curve=daily,
            curve_basis="closed_trade",
            benchmark=benchmark,
            fx_evidence=fx_evidence,
            quality_metadata=quality,
            source_metadata=metadata,
            lineage=lineage,
        )
    except (PydanticValidationError, TypeError, ValueError) as error:
        raise AnalyticsValidationError("canonical TradingResult is invalid") from error


__all__ = ["adapt_trading_result", "build_closed_trade_equity_curve"]

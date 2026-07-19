"""Closed-trade classification, R-multiple, streak, and exposure evidence."""

from __future__ import annotations

from datetime import timedelta
from decimal import Decimal
from types import MappingProxyType

from app.services.analytics.contracts.errors import AnalyticsValidationError
from app.services.analytics.contracts.evidence import build_warning
from app.services.analytics.contracts.models import (
    AnalyticsRunConfig,
    AnalyticsWarning,
    ClosedTrade,
    MetricEvidence,
    SectionEvidence,
    TradingResult,
)
from app.utils import logger

BREAKEVEN_EPSILON = Decimal("1e-8")
ANNUALIZATION_POLICY = MappingProxyType({"trading_days": 252})
MIN_METRIC_SAMPLES = MappingProxyType({"variance": 2, "tail": 30, "statistical": 30})


def _metric(metric_key: str, value: object, unit: str) -> MetricEvidence:
    """Build calculated trade metric evidence.

    Args:
        metric_key: Catalog metric key.
        value: Finite calculated value.
        unit: Catalog unit.

    Returns:
        Calculated metric evidence.
    """
    logger.debug("Building Analytics trade metric evidence")
    return MetricEvidence(
        metric_key=metric_key,
        status="calculated",
        value=value,
        unit=unit,
    )


def _selected_trades(
    result: TradingResult,
    source_context: str,
) -> tuple[ClosedTrade, ...]:
    """Select the explicit all, long, or short closed-trade context.

    Args:
        result: Canonical Analytics input.
        source_context: Approved source context.

    Returns:
        Selected immutable closed trades.

    Raises:
        AnalyticsValidationError: If the source context is not cataloged.
    """
    logger.debug("Selecting Analytics closed trades by source context")
    if source_context == "all":
        return result.trades
    if source_context == "long":
        return tuple(trade for trade in result.trades if trade.type == "BUY")
    if source_context == "short":
        return tuple(trade for trade in result.trades if trade.type == "SELL")
    message = f"unsupported trade source context: {source_context}"
    raise AnalyticsValidationError(message)


def _classifications(
    trades: tuple[ClosedTrade, ...],
) -> tuple[int, int, int, tuple[int, ...]]:
    """Classify trades on exact net PnL.

    Args:
        trades: Selected canonical closed trades.

    Returns:
        Win, loss, breakeven counts and ordered outcome signs.
    """
    logger.debug("Classifying Analytics closed trades")
    wins = 0
    losses = 0
    breakeven = 0
    signs: list[int] = []
    for trade in sorted(trades, key=lambda row: (row.exit_time, row.ticket)):
        if trade.net_trade_pnl > BREAKEVEN_EPSILON:
            wins += 1
            signs.append(1)
        elif trade.net_trade_pnl < -BREAKEVEN_EPSILON:
            losses += 1
            signs.append(-1)
        else:
            breakeven += 1
            signs.append(0)
    return wins, losses, breakeven, tuple(signs)


def _max_streak(signs: tuple[int, ...], target: int) -> int:
    """Return the longest consecutive target-sign run.

    Args:
        signs: Ordered trade outcome signs.
        target: Sign to count.

    Returns:
        Longest consecutive run length.
    """
    logger.debug("Calculating Analytics trade streak")
    longest = 0
    current = 0
    for sign in signs:
        current = current + 1 if sign == target else 0
        longest = max(longest, current)
    return longest


def _market_presence(trades: tuple[ClosedTrade, ...]) -> float | None:
    """Calculate seconds in the union of closed-trade intervals.

    Args:
        trades: Selected canonical closed trades.

    Returns:
        Total merged market-presence seconds, or ``None`` when empty.
    """
    logger.debug("Calculating Analytics market presence")
    intervals = sorted((trade.entry_time, trade.exit_time) for trade in trades)
    if not intervals:
        return None
    total = timedelta(0)
    start, end = intervals[0]
    for next_start, next_end in intervals[1:]:
        if next_start <= end:
            end = max(end, next_end)
        else:
            total += end - start
            start, end = next_start, next_end
    total += end - start
    return total.total_seconds()


def _r_multiples(
    trades: tuple[ClosedTrade, ...],
    source_context: str,
    *,
    config: AnalyticsRunConfig,
) -> tuple[tuple[float, ...], dict[str, int], tuple[AnalyticsWarning, ...]]:
    """Calculate ordered declared-stop or realized-MAE R multiples.

    Args:
        trades: Selected canonical closed trades.
        source_context: Applied source context.
        config: Required Analytics bounds supplying the warning detail bound.

    Returns:
        R values, basis counts, and catalog-backed warnings.
    """
    logger.debug("Calculating Analytics R-multiple evidence")
    values: list[float] = []
    counts = {"declared_stop": 0, "realized_mae": 0}
    warnings: list[AnalyticsWarning] = []
    for trade in trades:
        stop_risk = (
            abs(trade.entry_price - trade.stop_loss)
            if trade.stop_loss is not None
            else Decimal(0)
        )
        if stop_risk > 0:
            direction = Decimal(1) if trade.type == "BUY" else Decimal(-1)
            values.append(
                float(direction * (trade.exit_price - trade.entry_price) / stop_risk)
            )
            counts["declared_stop"] += 1
        elif trade.mae is not None and trade.mae != 0:
            values.append(float(trade.net_trade_pnl / abs(trade.mae)))
            counts["realized_mae"] += 1
            warnings.append(
                build_warning(
                    "r_multiple_mae_fallback",
                    section="trades",
                    source_context=source_context,
                    detail={"ticket": trade.ticket, "basis": "realized_mae"},
                    max_detail_bytes=config.max_warning_detail_bytes,
                )
            )
        else:
            warnings.append(
                build_warning(
                    "r_multiple_undefined",
                    section="trades",
                    source_context=source_context,
                    detail={"ticket": trade.ticket},
                    max_detail_bytes=config.max_warning_detail_bytes,
                )
            )
    return tuple(values), counts, tuple(warnings)


def calculate_trade_evidence(
    result: TradingResult,
    *,
    config: AnalyticsRunConfig,
    source_context: str = "all",
) -> SectionEvidence:
    """Calculate all catalog-approved closed-trade evidence.

    Args:
        result: Canonical Analytics input.
        config: Required Analytics bounds supplying the warning detail bound.
        source_context: Evidence grouping label.

    Returns:
        Ordered trade section evidence.
    """
    logger.info("Calculating Analytics closed-trade evidence")
    trades = _selected_trades(result, source_context)
    wins, losses, breakeven, signs = _classifications(trades)
    trade_count = len(trades)
    r_values, basis_counts, warnings = _r_multiples(
        trades, source_context, config=config
    )
    if basis_counts["declared_stop"] and basis_counts["realized_mae"]:
        warnings += (
            build_warning(
                "r_multiple_basis_mixed",
                section="trades",
                source_context=source_context,
                detail={
                    "declared_stop_count": basis_counts["declared_stop"],
                    "realized_mae_count": basis_counts["realized_mae"],
                },
                max_detail_bytes=config.max_warning_detail_bytes,
            ),
        )
    potentials: list[float] = []
    for trade in trades:
        if trade.mae is not None and trade.mae != 0 and trade.mfe is not None:
            potentials.append(float(trade.mfe / abs(trade.mae)))
    market_presence = _market_presence(trades)
    undefined_warning = build_warning(
        "insufficient_samples",
        section="trades",
        source_context=source_context,
        detail={"observed_count": trade_count, "required_count": 1},
        max_detail_bytes=config.max_warning_detail_bytes,
    )

    def optional(metric_key: str, value: object | None, unit: str) -> MetricEvidence:
        """Build optional trade evidence.

        Args:
            metric_key: Catalog metric key.
            value: Optional calculated value.
            unit: Catalog unit.

        Returns:
            Calculated or undefined metric evidence.
        """
        logger.debug("Building optional Analytics trade metric evidence")
        return MetricEvidence(
            metric_key=metric_key,
            status="calculated" if value is not None else "undefined",
            value=value,
            unit=unit,
            warnings=() if value is not None else (undefined_warning,),
        )

    metrics = (
        _metric("trade_count", trade_count, "count"),
        _metric("win_count", wins, "count"),
        _metric("loss_count", losses, "count"),
        _metric("breakeven_count", breakeven, "count"),
        optional("win_rate", wins / trade_count if trade_count else None, "ratio"),
        optional(
            "r_multiple", sum(r_values) / len(r_values) if r_values else None, "ratio"
        ),
        optional("r_multiple_basis", basis_counts if r_values else None, "count"),
        optional(
            "r_multiple_potential",
            sum(potentials) / len(potentials) if potentials else None,
            "ratio",
        ),
        optional("market_presence", market_presence, "duration"),
        _metric("max_win_streak", _max_streak(signs, 1), "count"),
        _metric("max_loss_streak", _max_streak(signs, -1), "count"),
    )
    return SectionEvidence(
        section_key="trades",
        criticality="required",
        metrics=tuple(
            MetricEvidence(
                metric_key=item.metric_key,
                status=item.status,
                value=item.value,
                unit=item.unit,
                warnings=item.warnings,
                source_context=source_context,
            )
            for item in metrics
        ),
        status="degraded"
        if warnings or any(item.warnings for item in metrics)
        else "completed",
        warnings=warnings + tuple(w for item in metrics for w in item.warnings),
    )


__all__ = [
    "ANNUALIZATION_POLICY",
    "BREAKEVEN_EPSILON",
    "MIN_METRIC_SAMPLES",
    "calculate_trade_evidence",
]

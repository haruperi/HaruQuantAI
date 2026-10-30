"""Performance statistics computation service with DAG dependency resolution."""

from __future__ import annotations

import math
from collections.abc import Sequence
from datetime import datetime
from typing import Any

from app.core.trading.statistics.base import BaseMetric
from app.core.trading.statistics.contracts import (
    MetricResults,
    SampleSplit,
)
from app.core.trading.statistics.dependencies import (
    MetricDependency,
    order_metrics,
)

_MIN_SAMPLE_SIZE = 2
_EPSILON = 1e-12
_ANNUALIZATION_FACTOR = 252.0


def _get_trade_close_time(t: dict[str, Any] | Any) -> float:
    """Extract epoch timestamp from close time or date field."""
    if isinstance(t, dict):
        val = t.get(
            "close_time",
            t.get("close_date", t.get("time", t.get("timestamp", 0))),
        )
    else:
        val = getattr(t, "close_time", getattr(t, "time", getattr(t, "timestamp", 0)))

    if val is None:
        return 0.0
    if isinstance(val, datetime):
        return val.timestamp()
    try:
        return float(val)
    except ValueError, TypeError:
        return 0.0


def _get_trade_pnl(t: dict[str, Any] | Any) -> float:
    """Extract net or gross profit/loss from trade record."""
    if isinstance(t, dict):
        val = t.get(
            "net_pnl",
            t.get("pnl", t.get("profit", t.get("net_profit", 0.0))),
        )
    else:
        val = getattr(t, "net_pnl", getattr(t, "pnl", getattr(t, "profit", 0.0)))
    if val is None:
        return 0.0
    try:
        return float(val)
    except ValueError, TypeError:
        return 0.0


def _trade_to_dict(t: dict[str, Any] | Any) -> dict[str, Any]:
    """Normalize trade record to standard dictionary format."""
    if isinstance(t, dict):
        return dict(t)
    if hasattr(t, "to_dict") and callable(t.to_dict):
        return dict(t.to_dict())
    return {
        "close_time": _get_trade_close_time(t),
        "net_pnl": _get_trade_pnl(t),
    }


class StatisticsService:
    """Computes standard and custom performance statistics partitioned by split."""

    def __init__(self) -> None:
        self._custom_metrics: dict[str, BaseMetric] = {}
        self._dependencies: dict[str, tuple[str, ...]] = {}

    def register_metric(
        self,
        metric: BaseMetric,
        depends_on: Sequence[str] = (),
    ) -> None:
        """Register custom metric provider with optional prerequisite dependencies."""
        name = metric.name
        self._custom_metrics[name] = metric
        self._dependencies[name] = tuple(depends_on)

    def unregister_metric(self, name: str) -> None:
        """Remove a registered custom metric provider."""
        self._custom_metrics.pop(name, None)
        self._dependencies.pop(name, None)

    def compute(
        self,
        trades: Sequence[dict[str, Any] | Any],
        initial_capital: float = 100000.0,
        sample_split: SampleSplit | None = None,
    ) -> MetricResults:
        """Compute performance statistics for all trades and IS/OOS partitions."""
        split = sample_split or SampleSplit()

        # 1. Sort trades ascending by close time with stable tie-breaking
        sorted_trades = sorted(trades, key=_get_trade_close_time)

        # 2. Partition into In-Sample and Out-of-Sample datasets
        is_trades, oos_trades = self._partition_trades(sorted_trades, split)

        # 3. Compute metrics for each partition
        all_metrics = self._compute_partition(sorted_trades, initial_capital)

        if split.split_type == "NONE":
            is_metrics: dict[str, float] = {}
            oos_metrics: dict[str, float] = {}
        else:
            is_metrics = self._compute_partition(is_trades, initial_capital)
            oos_metrics = self._compute_partition(oos_trades, initial_capital)

        return MetricResults(
            all_trades=all_metrics,
            in_sample=is_metrics,
            out_of_sample=oos_metrics,
        )

    def _partition_trades(
        self,
        trades: list[Any],
        split: SampleSplit,
    ) -> tuple[list[Any], list[Any]]:
        if split.split_type == "DATE":
            if split.split_date is None:
                return trades, []
            split_ts = split.split_date.timestamp()
            is_trades = [t for t in trades if _get_trade_close_time(t) <= split_ts]
            oos_trades = [t for t in trades if _get_trade_close_time(t) > split_ts]
            return is_trades, oos_trades

        if split.split_type == "RATIO":
            ratio = max(0.0, min(1.0, split.in_sample_ratio))
            idx = int(len(trades) * ratio)
            return trades[:idx], trades[idx:]

        return trades, []

    def _compute_partition(
        self,
        trades: Sequence[Any],
        initial_capital: float,
    ) -> dict[str, float]:
        """Compute standard formulas and custom metrics for a trade slice."""
        n_trades = len(trades)
        if n_trades == 0:
            results = self._empty_metrics()
            self._evaluate_custom_metrics(results, trades, initial_capital)
            return results

        pnls = [_get_trade_pnl(t) for t in trades]
        net_profit = sum(pnls)
        winning_pnls = [p for p in pnls if p > 0.0]
        losing_pnls = [p for p in pnls if p < 0.0]

        gross_profit = sum(winning_pnls)
        gross_loss = sum(losing_pnls)

        if gross_loss < 0.0:
            profit_factor = gross_profit / abs(gross_loss)
        elif gross_profit > 0.0:
            profit_factor = float("inf")
        else:
            profit_factor = 0.0

        win_rate = len(winning_pnls) / n_trades

        # Equity curve, peak-to-trough drawdown
        max_dd, max_dd_pct, equity_curve = self._calculate_drawdown(
            pnls, initial_capital
        )

        # Returns-based metrics
        sharpe = self._calculate_sharpe(pnls, initial_capital)
        sortino = self._calculate_sortino(pnls, initial_capital)
        sqn = self._calculate_sqn(pnls)
        stability_r2 = self._calculate_stability_r2(equity_curve)

        metrics: dict[str, float] = {
            "net_profit": net_profit,
            "gross_profit": gross_profit,
            "gross_loss": gross_loss,
            "profit_factor": profit_factor,
            "win_rate": win_rate,
            "trades_count": float(n_trades),
            "winning_trades": float(len(winning_pnls)),
            "losing_trades": float(len(losing_pnls)),
            "max_drawdown": max_dd,
            "max_drawdown_pct": max_dd_pct,
            "sharpe_ratio": sharpe,
            "sortino_ratio": sortino,
            "sqn": sqn,
            "stability_r2": stability_r2,
        }

        self._evaluate_custom_metrics(metrics, trades, initial_capital)
        return metrics

    def _empty_metrics(self) -> dict[str, float]:
        return {
            "net_profit": 0.0,
            "gross_profit": 0.0,
            "gross_loss": 0.0,
            "profit_factor": 0.0,
            "win_rate": 0.0,
            "trades_count": 0.0,
            "winning_trades": 0.0,
            "losing_trades": 0.0,
            "max_drawdown": 0.0,
            "max_drawdown_pct": 0.0,
            "sharpe_ratio": 0.0,
            "sortino_ratio": 0.0,
            "sqn": 0.0,
            "stability_r2": 0.0,
        }

    def _calculate_drawdown(
        self, pnls: Sequence[float], initial_capital: float
    ) -> tuple[float, float, list[float]]:
        equity = initial_capital
        peak = equity
        max_dd = 0.0
        max_dd_pct = 0.0
        equity_curve = [equity]

        for pnl in pnls:
            equity += pnl
            equity_curve.append(equity)
            peak = max(peak, equity)
            dd = max(0.0, peak - equity)
            dd_pct = (dd / peak * 100.0) if peak > 0.0 else 0.0
            max_dd = max(max_dd, dd)
            max_dd_pct = max(max_dd_pct, dd_pct)

        return max_dd, max_dd_pct, equity_curve

    def _calculate_sharpe(self, pnls: Sequence[float], initial_capital: float) -> float:
        if len(pnls) < _MIN_SAMPLE_SIZE or initial_capital <= 0.0:
            return 0.0

        returns = [p / initial_capital for p in pnls]
        mean_ret = sum(returns) / len(returns)
        var_ret = sum((r - mean_ret) ** 2 for r in returns) / (len(returns) - 1)
        std_ret = math.sqrt(var_ret)

        if std_ret < _EPSILON:
            return 0.0

        return (mean_ret / std_ret) * math.sqrt(_ANNUALIZATION_FACTOR)

    def _calculate_sortino(
        self, pnls: Sequence[float], initial_capital: float
    ) -> float:
        if len(pnls) < _MIN_SAMPLE_SIZE or initial_capital <= 0.0:
            return 0.0

        returns = [p / initial_capital for p in pnls]
        mean_ret = sum(returns) / len(returns)

        downside_diffs = [min(0.0, r) for r in returns]
        downside_var = sum(d**2 for d in downside_diffs) / (len(returns) - 1)
        downside_std = math.sqrt(downside_var)

        if downside_std < _EPSILON:
            return float("inf") if mean_ret > 0.0 else 0.0

        return (mean_ret / downside_std) * math.sqrt(_ANNUALIZATION_FACTOR)

    def _calculate_sqn(self, pnls: Sequence[float]) -> float:
        n = len(pnls)
        if n < _MIN_SAMPLE_SIZE:
            return 0.0

        mean_p = sum(pnls) / n
        var_p = sum((p - mean_p) ** 2 for p in pnls) / (n - 1)
        std_p = math.sqrt(var_p)

        if std_p < _EPSILON:
            return 0.0

        return math.sqrt(n) * (mean_p / std_p)

    def _calculate_stability_r2(self, equity_curve: Sequence[float]) -> float:
        n = len(equity_curve)
        if n < _MIN_SAMPLE_SIZE:
            return 0.0

        x = list(range(n))
        y = list(equity_curve)

        mean_x = sum(x) / n
        mean_y = sum(y) / n

        ss_xx = sum((xi - mean_x) ** 2 for xi in x)
        ss_yy = sum((yi - mean_y) ** 2 for yi in y)
        ss_xy = sum((xi - mean_x) * (yi - mean_y) for xi, yi in zip(x, y, strict=True))

        if ss_yy < _EPSILON:
            # Perfectly flat equity
            return 1.0

        if ss_xx < _EPSILON:
            return 0.0

        r2 = (ss_xy**2) / (ss_xx * ss_yy)
        return max(0.0, min(1.0, r2))

    def _evaluate_custom_metrics(
        self,
        results: dict[str, float],
        trades: Sequence[Any],
        initial_capital: float,
    ) -> None:
        """Resolve metric dependency DAG and evaluate registered custom metrics."""
        if not self._custom_metrics:
            return

        descriptors = [
            MetricDependency(
                metric_id=name,
                depends_on=self._dependencies.get(name, ()),
            )
            for name in self._custom_metrics
        ]

        ordered = order_metrics(descriptors)
        dict_trades = [_trade_to_dict(t) for t in trades]

        for desc in ordered:
            metric = self._custom_metrics[desc.metric_id]
            try:
                val = metric.compute(dict_trades, initial_capital)
                results[desc.metric_id] = float(val)
            except ArithmeticError, ValueError, TypeError, AttributeError:
                results[desc.metric_id] = 0.0


__all__ = ["StatisticsService"]

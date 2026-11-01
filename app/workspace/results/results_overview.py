"""Results overview performance metrics and monthly matrix projection service.

Description:
    Implements ResultsOverviewService rendering structured performance
    metrics, trade direction slices (All/Long/Short), and monthly/yearly
    matrix breakdowns with template selection via OverviewTemplatePolicy.

Purpose:
    FEAT-RESULTS-OVERVIEW: Statistical overview projection for strategy results.

Key Capabilities:
    - FR-results-overview-metrics: Compute All/Long/Short metrics breakdown.
    - FR-results-monthly-matrix: Generate 12-month calendar P&L performance.
    - FR-results-template-resolution: Apply OverviewTemplatePolicy fallback.

Python API Usage:
    from app.workspace.results.results_overview import ResultsOverviewService
    service = ResultsOverviewService()
    projection = service.get_overview("proj_1", "Results", "Strat_01")

CLI Usage:
    python -m app.cli results overview --strategy-id Strat_01
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from app.core.host.logging import get_logger
from app.core.lib.errors import DomainError
from app.core.lib.responses import StandardResponse
from app.core.trading.results.contracts import RunResult
from app.core.trading.results.store import ResultStore
from app.core.trading.statistics.service import StatisticsService
from app.workspace.results.app_results import to_float, wrap_response
from app.workspace.results.overview_template_policy import OverviewTemplatePolicy

logger = get_logger(__name__)

_MS_TIMESTAMP_THRESHOLD = 100_000_000_000


@dataclass(frozen=True, slots=True)
class OverviewMetricRow:
    """Individual statistical metric row across trade direction partitions."""

    metric_id: str
    label: str
    all_trades: str | float
    long_trades: str | float
    short_trades: str | float
    unit: str

    def to_dict(self) -> dict[str, Any]:
        """Convert metric row to dictionary representation."""
        return {
            "metric_id": self.metric_id,
            "label": self.label,
            "all_trades": self.all_trades,
            "long_trades": self.long_trades,
            "short_trades": self.short_trades,
            "unit": self.unit,
        }


@dataclass(frozen=True, slots=True)
class MonthlyPerformanceRow:
    """Monthly performance matrix entry for a single calendar year."""

    year: int
    months: tuple[float | None, ...]  # 12 entries (Jan..Dec)
    ytd_money: float
    ytd_pct: float

    def to_dict(self) -> dict[str, Any]:
        """Convert monthly row to dictionary representation."""
        return {
            "year": self.year,
            "months": list(self.months),
            "ytd_money": self.ytd_money,
            "ytd_pct": self.ytd_pct,
        }


@dataclass(frozen=True, slots=True)
class OverviewProjection:
    """Overview tab presentation projection."""

    strategy_id: str
    result_key: str
    selected_template: str
    available_templates: tuple[str, ...]
    sample_type: str
    metrics: tuple[OverviewMetricRow, ...]
    monthly_matrix: tuple[MonthlyPerformanceRow, ...]

    def to_dict(self) -> dict[str, Any]:
        """Convert projection to dictionary representation."""
        return {
            "strategy_id": self.strategy_id,
            "result_key": self.result_key,
            "selected_template": self.selected_template,
            "available_templates": list(self.available_templates),
            "sample_type": self.sample_type,
            "metrics": [m.to_dict() for m in self.metrics],
            "monthly_matrix": [r.to_dict() for r in self.monthly_matrix],
        }


DEFAULT_TEMPLATES: tuple[str, ...] = (
    "SQDefault",
    "SQDefaultPct",
    "DefaultOpenDD",
    "SQDefaultWithPortfolio",
    "SQDefaultWithPortfolioPct",
    "AWSharedDefault",
    "TSOverview",
)


class ResultsOverviewService:
    """Overview performance metrics and monthly matrix service."""

    def __init__(
        self,
        store: ResultStore | None = None,
        stats_service: StatisticsService | None = None,
    ) -> None:
        """Initialize service with optional dependencies."""
        self.store = store
        self.stats_service = stats_service or StatisticsService()
        self._in_memory_results: dict[str, RunResult] = {}

    def register_in_memory_result(self, result: RunResult) -> None:
        """Register an in-memory test result candidate."""
        self._in_memory_results[result.strategy_id] = result

    def resolve_result(self, strategy_id: str) -> RunResult:
        """Resolve RunResult candidate from memory or ResultStore."""
        if strategy_id in self._in_memory_results:
            return self._in_memory_results[strategy_id]
        if self.store is not None:
            try:
                return self.store.get_result(strategy_id)
            except DomainError:
                pass
        raise DomainError(
            code="RESULTS_STRATEGY_NOT_FOUND",
            message=f"Strategy '{strategy_id}' not found for overview",
            details={"strategy_id": strategy_id},
        )

    def get_overview(
        self,
        project_id: str,
        databank_name: str,
        strategy_id: str,
        *,
        result_key: str = "Main",
        template: str | None = None,
        available_templates: tuple[str, ...] | None = None,
        sample_type: str = "FullSample",
    ) -> StandardResponse[OverviewProjection]:
        """Compute overview metrics and monthly performance grid."""
        logger.info(
            "FR-results-overview-metrics: project=%s databank=%s key=%s",
            project_id,
            databank_name,
            result_key,
        )
        run_res = self.resolve_result(strategy_id)
        templates = available_templates or DEFAULT_TEMPLATES
        selected_template = (
            template
            if template is not None
            else OverviewTemplatePolicy.select(templates)
        )

        trades = [dict(t) for t in run_res.trades]
        if sample_type != "FullSample":
            trades = [
                t
                for t in trades
                if str(t.get("sample_type", "FullSample")).lower()
                == sample_type.lower()
            ]

        long_trades = [
            t
            for t in trades
            if str(t.get("type", t.get("direction", ""))).upper() in ("BUY", "LONG")
        ]
        short_trades = [
            t
            for t in trades
            if str(t.get("type", t.get("direction", ""))).upper() in ("SELL", "SHORT")
        ]

        def _calc_stats(trade_subset: list[dict[str, Any]]) -> dict[str, float]:
            if not trade_subset:
                return {
                    "net_profit": 0.0,
                    "profit_factor": 0.0,
                    "trades_count": 0.0,
                    "win_rate": 0.0,
                    "max_drawdown": 0.0,
                    "sharpe_ratio": 0.0,
                }
            normalized = [
                {
                    **t,
                    "net_pnl": to_float(
                        t.get("profit_loss", t.get("net_pnl", t.get("pnl", 0.0)))
                    ),
                }
                for t in trade_subset
            ]
            res = self.stats_service.compute(normalized, initial_capital=10000.0)
            return res.all_trades

        all_stats = _calc_stats(trades)
        long_stats = _calc_stats(long_trades)
        short_stats = _calc_stats(short_trades)

        def _clean_pf(stats: dict[str, float]) -> float:
            pf = stats.get("profit_factor", 0.0)
            if not math.isfinite(pf):
                return round(stats.get("gross_profit", 0.0), 2)
            return round(pf, 2)

        metric_rows = (
            OverviewMetricRow(
                metric_id="NetProfit",
                label="Net Profit",
                all_trades=round(all_stats.get("net_profit", 0.0), 2),
                long_trades=round(long_stats.get("net_profit", 0.0), 2),
                short_trades=round(short_stats.get("net_profit", 0.0), 2),
                unit="$",
            ),
            OverviewMetricRow(
                metric_id="ProfitFactor",
                label="Profit Factor",
                all_trades=_clean_pf(all_stats),
                long_trades=_clean_pf(long_stats),
                short_trades=_clean_pf(short_stats),
                unit="",
            ),
            OverviewMetricRow(
                metric_id="NumberOfTrades",
                label="Number of Trades",
                all_trades=int(all_stats.get("trades_count", len(trades))),
                long_trades=int(long_stats.get("trades_count", len(long_trades))),
                short_trades=int(short_stats.get("trades_count", len(short_trades))),
                unit="",
            ),
            OverviewMetricRow(
                metric_id="WinRate",
                label="Win Rate",
                all_trades=round(all_stats.get("win_rate", 0.0) * 100.0, 2),
                long_trades=round(long_stats.get("win_rate", 0.0) * 100.0, 2),
                short_trades=round(short_stats.get("win_rate", 0.0) * 100.0, 2),
                unit="%",
            ),
            OverviewMetricRow(
                metric_id="Drawdown",
                label="Drawdown",
                all_trades=round(all_stats.get("max_drawdown", 0.0), 2),
                long_trades=round(long_stats.get("max_drawdown", 0.0), 2),
                short_trades=round(short_stats.get("max_drawdown", 0.0), 2),
                unit="$",
            ),
            OverviewMetricRow(
                metric_id="SharpeRatio",
                label="Sharpe Ratio",
                all_trades=round(all_stats.get("sharpe_ratio", 0.0), 2),
                long_trades=round(long_stats.get("sharpe_ratio", 0.0), 2),
                short_trades=round(short_stats.get("sharpe_ratio", 0.0), 2),
                unit="",
            ),
        )

        monthly_rows = self._build_monthly_matrix(trades)

        projection = OverviewProjection(
            strategy_id=strategy_id,
            result_key=result_key,
            selected_template=selected_template,
            available_templates=templates,
            sample_type=sample_type,
            metrics=metric_rows,
            monthly_matrix=monthly_rows,
        )

        logger.info(
            "FR-results-overview-metrics: projected overview for %s (template=%s)",
            strategy_id,
            selected_template,
        )
        return wrap_response(
            request_id=f"req_{strategy_id}_overview",
            data=projection,
            json_payload=projection.to_dict(),
        )

    def _build_monthly_matrix(
        self, trades: list[dict[str, Any]]
    ) -> tuple[MonthlyPerformanceRow, ...]:
        year_month_pl: dict[int, dict[int, float]] = {}
        for t in trades:
            pl = to_float(t.get("profit_loss", t.get("pnl", 0.0)))
            close_time_val = t.get("close_time", t.get("close_time_ms", 0))
            if isinstance(close_time_val, (int, float)):
                ts = (
                    close_time_val / 1000.0
                    if close_time_val > _MS_TIMESTAMP_THRESHOLD
                    else float(close_time_val)
                )
                dt = datetime.fromtimestamp(ts, tz=UTC)
            elif isinstance(close_time_val, str) and close_time_val:
                try:
                    dt = datetime.fromisoformat(close_time_val)
                except ValueError:
                    dt = datetime.now(UTC)
            else:
                dt = datetime.now(UTC)

            y = dt.year
            m = dt.month
            year_month_pl.setdefault(y, {}).setdefault(m, 0.0)
            year_month_pl[y][m] += pl

        monthly_rows: list[MonthlyPerformanceRow] = []
        for y in sorted(year_month_pl.keys()):
            m_dict = year_month_pl[y]
            months = tuple(
                round(m_dict[m], 2) if m in m_dict else None for m in range(1, 13)
            )
            ytd = sum(m_dict.values())
            initial_cap = 10000.0
            ytd_pct = round((ytd / initial_cap) * 100.0, 2)
            monthly_rows.append(
                MonthlyPerformanceRow(
                    year=y,
                    months=months,
                    ytd_money=round(ytd, 2),
                    ytd_pct=ytd_pct,
                )
            )
        return tuple(monthly_rows)

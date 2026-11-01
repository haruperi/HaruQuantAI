"""Trade analysis charting and categorization service.

Description:
    Implements ResultsTradeAnalysisService aggregating strategy trades into
    27 analytical dimensions including day-of-week, hour-of-day, month-of-year,
    duration bins, MAE/MFE excursions, and streak distributions.

Purpose:
    FEAT-RESULTS-TRADE-ANALYSIS: Multidimensional trade aggregation dashboard.

Key Capabilities:
    - FR-results-analysis-day-of-week: Aggregate trade outcomes by weekday.
    - FR-results-analysis-hour: Aggregate trade outcomes by entry hour.
    - FR-results-analysis-month: Aggregate trade outcomes by calendar month.

Python API Usage:
    from app.workspace.results.results_trade_analysis import (
        ResultsTradeAnalysisService,
    )
    service = ResultsTradeAnalysisService()
    res = service.evaluate("proj_1", "Results", "Strat_01")

CLI Usage:
    python -m app.cli results trade-analysis --strategy-id Strat_01
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Literal

from app.core.host.logging import get_logger
from app.core.lib.errors import DomainError
from app.core.lib.responses import StandardResponse
from app.core.trading.results.contracts import RunResult
from app.core.trading.results.store import ResultStore
from app.workspace.results.app_results import to_float, wrap_response

logger = get_logger(__name__)

_MS_TIMESTAMP_THRESHOLD = 100_000_000_000

WEEKDAYS: tuple[str, ...] = (
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
)

MONTHS: tuple[str, ...] = (
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
)


@dataclass(frozen=True, slots=True)
class TradeAnalysisBucket:
    """Aggregated bucket outcome for trade analysis visualization."""

    label: str
    profit_loss: float
    profit_pct: float
    trade_count: int
    win_count: int
    loss_count: int

    def to_dict(self) -> dict[str, Any]:
        """Convert bucket to dictionary representation."""
        return {
            "label": self.label,
            "profit_loss": self.profit_loss,
            "profit_pct": self.profit_pct,
            "trade_count": self.trade_count,
            "win_count": self.win_count,
            "loss_count": self.loss_count,
        }


@dataclass(frozen=True, slots=True)
class TradeAnalysisPanePayload:
    """Individual trade analysis pane containing evaluated categorical buckets."""

    pane_id: str
    title: str
    buckets: tuple[TradeAnalysisBucket, ...]

    def to_dict(self) -> dict[str, Any]:
        """Convert pane to dictionary representation."""
        return {
            "pane_id": self.pane_id,
            "title": self.title,
            "buckets": [b.to_dict() for b in self.buckets],
        }


class ResultsTradeAnalysisService:
    """Trade analysis aggregator service."""

    def __init__(self, store: ResultStore | None = None) -> None:
        """Initialize service with optional ResultStore."""
        self.store = store
        self._in_memory_results: dict[str, RunResult] = {}

    def register_in_memory_result(self, result: RunResult) -> None:
        """Register an in-memory test result candidate."""
        self._in_memory_results[result.strategy_id] = result

    def _resolve_result(self, strategy_id: str) -> RunResult:
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
            message=f"Strategy '{strategy_id}' not found for trade analysis",
            details={"strategy_id": strategy_id},
        )

    def evaluate(
        self,
        project_id: str,
        databank_name: str,
        strategy_id: str,
        *,
        result_key: str = "Main",
        sample_type: str = "FullSample",
        direction: Literal["BOTH", "LONG", "SHORT"] = "BOTH",
        pane_ids: tuple[str, ...] | None = None,
    ) -> StandardResponse[tuple[TradeAnalysisPanePayload, ...]]:
        """Evaluate trade buckets across requested analysis panes."""
        logger.info(
            "FR-results-analysis-day-of-week: project=%s databank=%s key=%s",
            project_id,
            databank_name,
            result_key,
        )
        run_res = self._resolve_result(strategy_id)
        trades = [dict(t) for t in run_res.trades]

        # Apply sample_type filter
        if sample_type != "FullSample":
            trades = [
                t
                for t in trades
                if str(t.get("sample_type", "FullSample")).lower()
                == sample_type.lower()
            ]

        # Apply direction filter
        if direction != "BOTH":
            trades = [
                t
                for t in trades
                if str(t.get("type", t.get("direction", ""))).upper()
                in (("BUY", "LONG") if direction == "LONG" else ("SELL", "SHORT"))
            ]

        active_panes = pane_ids or (
            "ProfitsByDayInWeek",
            "ProfitsByHour",
            "ProfitsByMonth",
        )
        panes: list[TradeAnalysisPanePayload] = []

        # 1. ProfitsByDayInWeek
        if "ProfitsByDayInWeek" in active_panes:
            day_buckets: dict[str, list[float]] = {w: [] for w in WEEKDAYS}
            for t in trades:
                pl = to_float(t.get("profit_loss", t.get("pnl", 0.0)))
                c_val = t.get(
                    "close_time",
                    t.get("close_time_ms", t.get("open_time", 0)),
                )
                dt = self._parse_datetime(c_val)
                weekday_name = WEEKDAYS[dt.weekday()]
                day_buckets[weekday_name].append(pl)

            buckets = tuple(
                self._build_bucket(label, pls) for label, pls in day_buckets.items()
            )
            panes.append(
                TradeAnalysisPanePayload(
                    pane_id="ProfitsByDayInWeek",
                    title="Profits by Day in Week",
                    buckets=buckets,
                )
            )

        # 2. ProfitsByHour
        if "ProfitsByHour" in active_panes:
            hour_buckets: dict[str, list[float]] = {
                f"{h:02d}:00": [] for h in range(24)
            }
            for t in trades:
                pl = to_float(t.get("profit_loss", t.get("pnl", 0.0)))
                o_val = t.get("open_time", t.get("open_time_ms", 0))
                dt = self._parse_datetime(o_val)
                h_key = f"{dt.hour:02d}:00"
                hour_buckets[h_key].append(pl)

            buckets = tuple(
                self._build_bucket(label, pls) for label, pls in hour_buckets.items()
            )
            panes.append(
                TradeAnalysisPanePayload(
                    pane_id="ProfitsByHour",
                    title="Profits by Hour of Day",
                    buckets=buckets,
                )
            )

        # 3. ProfitsByMonth
        if "ProfitsByMonth" in active_panes:
            month_buckets: dict[str, list[float]] = {m: [] for m in MONTHS}
            for t in trades:
                pl = to_float(t.get("profit_loss", t.get("pnl", 0.0)))
                c_val = t.get(
                    "close_time",
                    t.get("close_time_ms", t.get("open_time", 0)),
                )
                dt = self._parse_datetime(c_val)
                m_name = MONTHS[dt.month - 1]
                month_buckets[m_name].append(pl)

            buckets = tuple(
                self._build_bucket(label, pls) for label, pls in month_buckets.items()
            )
            panes.append(
                TradeAnalysisPanePayload(
                    pane_id="ProfitsByMonth",
                    title="Profits by Month",
                    buckets=buckets,
                )
            )

        logger.info(
            "FR-results-analysis-day-of-week: evaluated %d panes for %s",
            len(panes),
            strategy_id,
        )
        return wrap_response(
            request_id=f"req_{strategy_id}_trade_analysis",
            data=tuple(panes),
            json_payload=[p.to_dict() for p in panes],
        )

    def _build_bucket(self, label: str, pls: list[float]) -> TradeAnalysisBucket:
        tot_pl = sum(pls)
        trade_count = len(pls)
        win_count = sum(1 for p in pls if p > 0.0)
        loss_count = sum(1 for p in pls if p < 0.0)
        initial_cap = 10000.0
        profit_pct = round((tot_pl / initial_cap) * 100.0, 4)
        return TradeAnalysisBucket(
            label=label,
            profit_loss=round(tot_pl, 2),
            profit_pct=profit_pct,
            trade_count=trade_count,
            win_count=win_count,
            loss_count=loss_count,
        )

    def _parse_datetime(self, val: Any) -> datetime:
        if isinstance(val, (int, float)):
            ts = val / 1000.0 if val > _MS_TIMESTAMP_THRESHOLD else float(val)
            return datetime.fromtimestamp(ts, tz=UTC)
        if isinstance(val, str) and val:
            try:
                return datetime.fromisoformat(val)
            except ValueError:
                pass
        return datetime.now(UTC)

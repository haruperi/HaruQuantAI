"""Equity curve and mark-to-market drawdown projection service.

Description:
    Implements ResultsEquityChartService generating closed-trade and
    mark-to-market equity curves, sample split markers (IS/OOS), and
    directional subsets (BOTH, LONG, SHORT).

Purpose:
    FEAT-RESULTS-EQUITY-CHART: Multi-mode equity curve projection.

Key Capabilities:
    - FR-results-equity-projection: Compute trade-by-trade or time equity curve.
    - FR-results-equity-m2m: Calculate open equity incorporating MAE excursions.

Python API Usage:
    from app.workspace.results.results_equity_chart import (
        ResultsEquityChartService,
    )
    service = ResultsEquityChartService()
    res = service.get_projection("proj_1", "Results", "Strat_01")

CLI Usage:
    python -m app.cli results equity-chart --strategy-id Strat_01
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from app.core.host.logging import get_logger
from app.core.lib.errors import DomainError
from app.core.lib.responses import StandardResponse
from app.core.trading.results.contracts import RunResult
from app.core.trading.results.store import ResultStore
from app.workspace.results.app_results import to_float, to_int, wrap_response

logger = get_logger(__name__)


@dataclass(frozen=True, slots=True)
class EquityCurvePoint:
    """Individual point along the strategy equity curve."""

    index: int
    timestamp_ms: int
    balance: float
    open_equity: float
    drawdown_money: float
    drawdown_pct: float
    sample_type: str

    def to_dict(self) -> dict[str, Any]:
        """Convert equity point to dictionary representation."""
        return {
            "index": self.index,
            "timestamp_ms": self.timestamp_ms,
            "balance": self.balance,
            "open_equity": self.open_equity,
            "drawdown_money": self.drawdown_money,
            "drawdown_pct": self.drawdown_pct,
            "sample_type": self.sample_type,
        }


@dataclass(frozen=True, slots=True)
class EquityChartProjection:
    """Equity chart presentation projection."""

    result_key: str
    initial_capital: float
    mode: Literal["TRADES", "TIME"]
    direction: Literal["BOTH", "LONG", "SHORT"]
    points: tuple[EquityCurvePoint, ...]
    sample_boundaries: tuple[tuple[str, int], ...]

    def to_dict(self) -> dict[str, Any]:
        """Convert projection to dictionary representation."""
        return {
            "result_key": self.result_key,
            "initial_capital": self.initial_capital,
            "mode": self.mode,
            "direction": self.direction,
            "points": [p.to_dict() for p in self.points],
            "sample_boundaries": [list(b) for b in self.sample_boundaries],
        }


class ResultsEquityChartService:
    """Equity chart calculation and projection service."""

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
            message=f"Strategy '{strategy_id}' not found for equity chart",
            details={"strategy_id": strategy_id},
        )

    def get_projection(
        self,
        project_id: str,
        databank_name: str,
        strategy_id: str,
        *,
        result_key: str = "Main",
        mode: Literal["TRADES", "TIME"] = "TRADES",
        direction: Literal["BOTH", "LONG", "SHORT"] = "BOTH",
    ) -> StandardResponse[EquityChartProjection]:
        """Compute equity curve points with running balance and drawdown."""
        logger.info(
            "FR-results-equity-projection: project=%s databank=%s key=%s",
            project_id,
            databank_name,
            result_key,
        )
        run_res = self._resolve_result(strategy_id)
        trades = [dict(t) for t in run_res.trades]

        # Filter by direction
        if direction != "BOTH":
            target_dirs = ("BUY", "LONG") if direction == "LONG" else ("SELL", "SHORT")
            trades = [
                t
                for t in trades
                if str(t.get("type", t.get("direction", ""))).upper() in target_dirs
            ]

        initial_cap = to_float(run_res.strategy_payload.get("initial_capital", 10000.0))

        first_ts = 0
        if trades:
            first_ts = to_int(
                trades[0].get(
                    "open_time_ms",
                    trades[0].get("open_time", trades[0].get("timestamp_ms", 0)),
                )
            )

        # Index 0 anchor point
        points: list[EquityCurvePoint] = [
            EquityCurvePoint(
                index=0,
                timestamp_ms=first_ts,
                balance=initial_cap,
                open_equity=initial_cap,
                drawdown_money=0.0,
                drawdown_pct=0.0,
                sample_type="IS",
            )
        ]

        balance = initial_cap
        peak_balance = initial_cap
        sample_boundaries: list[tuple[str, int]] = []
        last_sample = "IS"

        for idx, t in enumerate(trades, start=1):
            pl = to_float(t.get("profit_loss", t.get("pnl", 0.0)))
            mae = to_float(t.get("mae", 0.0))
            ts = to_int(
                t.get(
                    "close_time_ms",
                    t.get("close_time", t.get("timestamp_ms", 0)),
                )
            )
            sample = str(t.get("sample_type", "IS"))

            if sample != last_sample:
                sample_boundaries.append((sample, idx))
                last_sample = sample

            balance += pl
            peak_balance = max(peak_balance, balance)
            dd_money = min(0.0, balance - peak_balance)
            dd_pct = (
                round((dd_money / peak_balance) * 100.0, 4) if peak_balance > 0 else 0.0
            )
            open_equity = balance - mae

            points.append(
                EquityCurvePoint(
                    index=idx,
                    timestamp_ms=ts,
                    balance=round(balance, 2),
                    open_equity=round(open_equity, 2),
                    drawdown_money=round(dd_money, 2),
                    drawdown_pct=dd_pct,
                    sample_type=sample,
                )
            )

        projection = EquityChartProjection(
            result_key=result_key,
            initial_capital=initial_cap,
            mode=mode,
            direction=direction,
            points=tuple(points),
            sample_boundaries=tuple(sample_boundaries),
        )

        logger.info(
            "FR-results-equity-projection: generated %d curve points for %s",
            len(points),
            strategy_id,
        )
        return wrap_response(
            request_id=f"req_{strategy_id}_equity_chart",
            data=projection,
            json_payload=projection.to_dict(),
        )

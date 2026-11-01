"""Stockpicker overview performance metrics and portfolio positions service.

Description:
    Implements ResultsSPOverviewService displaying portfolio-level Stockpicker
    metrics, current open positions, benchmark comparison, and constituent
    symbol realized P&L breakdowns.

Purpose:
    FEAT-RESULTS-SP-OVERVIEW: Stockpicker multi-asset strategy overview.

Key Capabilities:
    - FR-results-sp-breakdown: Per-symbol P&L attribution and weight breakdown.
    - FR-results-sp-positions: Active open positions snapshot sorted by weight.

Python API Usage:
    from app.workspace.results.results_s_p_overview import ResultsSPOverviewService
    service = ResultsSPOverviewService()
    res = service.get_sp_overview("proj_1", "Results", "SP_Strat_01")

CLI Usage:
    python -m app.cli results sp-overview --strategy-id SP_Strat_01
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.core.host.logging import get_logger
from app.core.lib.errors import DomainError
from app.core.lib.responses import StandardResponse
from app.core.trading.results.contracts import RunResult
from app.core.trading.results.store import ResultStore
from app.workspace.results.app_results import to_float, to_int, wrap_response

logger = get_logger(__name__)


@dataclass(frozen=True, slots=True)
class SPOpenPosition:
    """Individual open position within a Stockpicker portfolio."""

    symbol: str
    direction: str
    open_time_ms: int
    open_price: float
    current_price: float
    size: float
    unrealized_pl: float
    weight_pct: float

    def to_dict(self) -> dict[str, Any]:
        """Convert open position to dictionary representation."""
        return {
            "symbol": self.symbol,
            "direction": self.direction,
            "open_time_ms": self.open_time_ms,
            "open_price": self.open_price,
            "current_price": self.current_price,
            "size": self.size,
            "unrealized_pl": self.unrealized_pl,
            "weight_pct": self.weight_pct,
        }


@dataclass(frozen=True, slots=True)
class SPOverviewProjection:
    """Stockpicker overview tab presentation projection."""

    strategy_id: str
    result_key: str
    cagr_pct: float
    max_dd_pct: float
    sharpe_ratio: float
    exposure_pct: float
    open_positions: tuple[SPOpenPosition, ...]
    symbol_breakdown: dict[str, float]

    def to_dict(self) -> dict[str, Any]:
        """Convert projection to dictionary representation."""
        return {
            "strategy_id": self.strategy_id,
            "result_key": self.result_key,
            "cagr_pct": self.cagr_pct,
            "max_dd_pct": self.max_dd_pct,
            "sharpe_ratio": self.sharpe_ratio,
            "exposure_pct": self.exposure_pct,
            "open_positions": [p.to_dict() for p in self.open_positions],
            "symbol_breakdown": dict(self.symbol_breakdown),
        }


class ResultsSPOverviewService:
    """Stockpicker overview service."""

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
            message=f"Strategy '{strategy_id}' not found for SP overview",
            details={"strategy_id": strategy_id},
        )

    def get_sp_overview(
        self,
        project_id: str,
        databank_name: str,
        strategy_id: str,
        result_key: str = "Main",
    ) -> StandardResponse[SPOverviewProjection]:
        """Compute Stockpicker portfolio overview and symbol breakdown."""
        logger.info(
            "FR-results-sp-breakdown: project=%s databank=%s key=%s",
            project_id,
            databank_name,
            result_key,
        )
        run_res = self._resolve_result(strategy_id)
        trades = run_res.trades

        # Compute realized P&L per symbol
        symbol_breakdown: dict[str, float] = {}
        for t in trades:
            sym = str(t.get("symbol", "UNKNOWN"))
            pl = to_float(t.get("profit_loss", t.get("pnl", 0.0)))
            symbol_breakdown[sym] = round(symbol_breakdown.get(sym, 0.0) + pl, 2)

        # Parse open positions from strategy_payload
        raw_positions = run_res.strategy_payload.get("open_positions", [])
        open_positions: list[SPOpenPosition] = []
        if isinstance(raw_positions, (list, tuple)):
            open_positions.extend(
                SPOpenPosition(
                    symbol=str(p.get("symbol", "")),
                    direction=str(p.get("direction", "LONG")),
                    open_time_ms=to_int(p.get("open_time_ms", 0)),
                    open_price=to_float(p.get("open_price", 0.0)),
                    current_price=to_float(p.get("current_price", 0.0)),
                    size=to_float(p.get("size", 1.0)),
                    unrealized_pl=to_float(p.get("unrealized_pl", 0.0)),
                    weight_pct=to_float(p.get("weight_pct", 0.0)),
                )
                for p in raw_positions
                if isinstance(p, dict)
            )

        # Sort open positions descending by weight_pct
        open_positions.sort(key=lambda pos: pos.weight_pct, reverse=True)

        metrics = run_res.metrics
        cagr = to_float(metrics.get("cagr", metrics.get("cagr_pct", 0.0)))
        max_dd = to_float(metrics.get("drawdown_pct", metrics.get("max_dd_pct", 0.0)))
        sharpe = to_float(metrics.get("sharpe_ratio", 0.0))
        exposure = to_float(metrics.get("exposure_pct", 0.0))

        projection = SPOverviewProjection(
            strategy_id=strategy_id,
            result_key=result_key,
            cagr_pct=round(cagr, 2),
            max_dd_pct=round(max_dd, 2),
            sharpe_ratio=round(sharpe, 2),
            exposure_pct=round(exposure, 2),
            open_positions=tuple(open_positions),
            symbol_breakdown=symbol_breakdown,
        )

        logger.info(
            "FR-results-sp-breakdown: calculated breakdown across %d symbols",
            len(symbol_breakdown),
        )
        return wrap_response(
            request_id=f"req_{strategy_id}_sp_overview",
            data=projection,
            json_payload=projection.to_dict(),
        )

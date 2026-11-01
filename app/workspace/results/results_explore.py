"""Interactive strategy exploration and sensitivity inspection service.

Description:
    Implements ResultsExploreService providing quick What-If inspection,
    summary metrics, and sample breakdown (FullSample, InSample, OutOfSample).

Purpose:
    FEAT-RESULTS-EXPLORE: What-If strategy inspection and sample breakdown.

Key Capabilities:
    - FR-results-explore-summary: Core performance metrics snapshot.
    - FR-results-explore-sample-split: In-Sample vs Out-of-Sample metrics.

Python API Usage:
    from app.workspace.results.results_explore import ResultsExploreService
    service = ResultsExploreService()
    res = service.get_info("proj_1", "Results", "Strat_01")

CLI Usage:
    python -m app.cli results explore --strategy-id Strat_01
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.core.host.logging import get_logger
from app.core.lib.errors import DomainError
from app.core.lib.responses import StandardResponse
from app.core.trading.results.contracts import RunResult
from app.core.trading.results.store import ResultStore
from app.workspace.results.app_results import to_float, wrap_response

logger = get_logger(__name__)


@dataclass(frozen=True, slots=True)
class ExploreInfoPayload:
    """Strategy exploration summary and partitioned performance."""

    strategy_id: str
    result_key: str
    symbol: str
    timeframe: str
    total_trades: int
    net_profit: float
    drawdown_pct: float
    profit_factor: float
    return_dd_ratio: float
    parameters: dict[str, str | int | float | bool]
    sample_breakdown: dict[str, dict[str, float]]

    def to_dict(self) -> dict[str, Any]:
        """Convert payload to dictionary representation."""
        return {
            "strategy_id": self.strategy_id,
            "result_key": self.result_key,
            "symbol": self.symbol,
            "timeframe": self.timeframe,
            "total_trades": self.total_trades,
            "net_profit": self.net_profit,
            "drawdown_pct": self.drawdown_pct,
            "profit_factor": self.profit_factor,
            "return_dd_ratio": self.return_dd_ratio,
            "parameters": dict(self.parameters),
            "sample_breakdown": {k: dict(v) for k, v in self.sample_breakdown.items()},
        }


class ResultsExploreService:
    """Strategy explore and sensitivity inspector service."""

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
            message=f"Strategy '{strategy_id}' not found for exploration",
            details={"strategy_id": strategy_id},
        )

    def get_info(
        self,
        project_id: str,
        databank_name: str,
        strategy_id: str,
        result_key: str = "Main",
    ) -> StandardResponse[ExploreInfoPayload]:
        """Compute exploration payload and sample partition stats."""
        logger.info(
            "FR-results-explore-summary: project=%s databank=%s key=%s",
            project_id,
            databank_name,
            result_key,
        )
        run_res = self._resolve_result(strategy_id)
        trades = [dict(t) for t in run_res.trades]

        symbol = str(
            run_res.strategy_payload.get(
                "symbol", run_res.metrics.get("symbol", "EURUSD")
            )
        )
        timeframe = str(
            run_res.strategy_payload.get(
                "timeframe", run_res.metrics.get("timeframe", "H1")
            )
        )

        params: dict[str, str | int | float | bool] = {}
        for k, v in run_res.parameters.items():
            if isinstance(v, (str, int, float, bool)):
                params[str(k)] = v

        def _calc_partition_metrics(
            trade_subset: list[dict[str, Any]],
        ) -> dict[str, float]:
            if not trade_subset:
                return {
                    "total_trades": 0.0,
                    "net_profit": 0.0,
                    "profit_factor": 0.0,
                    "drawdown_pct": 0.0,
                    "return_dd_ratio": 0.0,
                }
            tot_trades = len(trade_subset)
            net_pl = sum(
                to_float(t.get("profit_loss", t.get("pnl", 0.0))) for t in trade_subset
            )
            wins = [
                to_float(t.get("profit_loss", t.get("pnl", 0.0)))
                for t in trade_subset
                if to_float(t.get("profit_loss", t.get("pnl", 0.0))) > 0.0
            ]
            losses = [
                abs(to_float(t.get("profit_loss", t.get("pnl", 0.0))))
                for t in trade_subset
                if to_float(t.get("profit_loss", t.get("pnl", 0.0))) < 0.0
            ]
            gp = sum(wins)
            gl = sum(losses)
            if gl > 0.0:
                pf = round(gp / gl, 2)
            elif gp > 0.0:
                pf = round(gp, 2)
            else:
                pf = 0.0

            # Running balance & max drawdown
            initial_cap = 10000.0
            bal = initial_cap
            peak = initial_cap
            max_dd = 0.0
            for t in trade_subset:
                bal += to_float(t.get("profit_loss", t.get("pnl", 0.0)))
                peak = max(peak, bal)
                dd = max(0.0, peak - bal)
                max_dd = max(max_dd, dd)

            dd_pct = round((max_dd / peak) * 100.0, 2) if peak > 0 else 0.0
            ret_dd = round(net_pl / max_dd, 2) if max_dd > 0 else round(net_pl, 2)

            return {
                "total_trades": float(tot_trades),
                "net_profit": round(net_pl, 2),
                "profit_factor": pf,
                "drawdown_pct": dd_pct,
                "return_dd_ratio": ret_dd,
            }

        full_stats = _calc_partition_metrics(trades)

        is_trades = [
            t
            for t in trades
            if str(t.get("sample_type", "")).lower() in ("is", "insample")
        ]
        oos_trades = [
            t
            for t in trades
            if str(t.get("sample_type", "")).lower() in ("oos", "outofsample")
        ]

        sample_breakdown = {
            "FullSample": full_stats,
            "InSample": _calc_partition_metrics(is_trades),
            "OutOfSample": _calc_partition_metrics(oos_trades),
        }

        payload = ExploreInfoPayload(
            strategy_id=strategy_id,
            result_key=result_key,
            symbol=symbol,
            timeframe=timeframe,
            total_trades=int(full_stats["total_trades"]),
            net_profit=full_stats["net_profit"],
            drawdown_pct=full_stats["drawdown_pct"],
            profit_factor=full_stats["profit_factor"],
            return_dd_ratio=full_stats["return_dd_ratio"],
            parameters=params,
            sample_breakdown=sample_breakdown,
        )

        logger.info(
            "FR-results-explore-summary: computed explore info for %s (%d trades)",
            strategy_id,
            payload.total_trades,
        )
        return wrap_response(
            request_id=f"req_{strategy_id}_explore",
            data=payload,
            json_payload=payload.to_dict(),
        )

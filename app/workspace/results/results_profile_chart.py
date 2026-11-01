"""Trade excursion profile path chart projection service.

Description:
    Implements ResultsProfileChartService projecting per-trade normalized
    or monetary intra-trade excursion paths (MAE/MFE/P&L) and computing
    mean and quartile progression envelopes.

Purpose:
    FEAT-RESULTS-PROFILE-CHART: Intra-trade excursion profile paths.

Key Capabilities:
    - FR-results-profile-paths: Reconstruct trade excursion paths and quantiles.

Python API Usage:
    from app.workspace.results.results_profile_chart import (
        ResultsProfileChartService,
    )
    service = ResultsProfileChartService()
    res = service.get_paths("proj_1", "Results", "Strat_01")

CLI Usage:
    python -m app.cli results profile-chart --strategy-id Strat_01
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
class TradeProfilePath:
    """Individual trade intra-trade excursion path trajectory."""

    ticket: int
    direction: str
    is_winner: bool
    points: tuple[float, ...]

    def to_dict(self) -> dict[str, Any]:
        """Convert path to dictionary representation."""
        return {
            "ticket": self.ticket,
            "direction": self.direction,
            "is_winner": self.is_winner,
            "points": list(self.points),
        }


@dataclass(frozen=True, slots=True)
class ProfileChartPayload:
    """Complete trade excursion profile path payload."""

    result_key: str
    unit: Literal["MONEY", "PIPS", "PCT"]
    paths: tuple[TradeProfilePath, ...]
    mean_path: tuple[float, ...]
    quantile_25: tuple[float, ...]
    quantile_75: tuple[float, ...]

    def to_dict(self) -> dict[str, Any]:
        """Convert payload to dictionary representation."""
        return {
            "result_key": self.result_key,
            "unit": self.unit,
            "paths": [p.to_dict() for p in self.paths],
            "mean_path": list(self.mean_path),
            "quantile_25": list(self.quantile_25),
            "quantile_75": list(self.quantile_75),
        }


class ResultsProfileChartService:
    """Trade excursion profile path chart service."""

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
            message=f"Strategy '{strategy_id}' not found for profile chart",
            details={"strategy_id": strategy_id},
        )

    def get_paths(
        self,
        project_id: str,
        databank_name: str,
        strategy_id: str,
        *,
        result_key: str = "Main",
        unit: Literal["MONEY", "PIPS", "PCT"] = "MONEY",
        max_trades: int = 500,
    ) -> StandardResponse[ProfileChartPayload]:
        """Compute excursion paths and step-wise mean and quantile envelopes."""
        logger.info(
            "FR-results-profile-paths: project=%s databank=%s key=%s",
            project_id,
            databank_name,
            result_key,
        )
        run_res = self._resolve_result(strategy_id)
        raw_trades = run_res.trades[:max_trades]

        paths: list[TradeProfilePath] = []
        for idx, t in enumerate(raw_trades, start=1):
            ticket = to_int(t.get("ticket", idx))
            raw_dir = str(t.get("type", t.get("direction", "BUY")))
            pl = to_float(t.get("profit_loss", t.get("pnl", 0.0)))
            mae = to_float(t.get("mae", 0.0))
            mfe = to_float(t.get("mfe", 0.0))

            raw_path = t.get("path")
            if isinstance(raw_path, (list, tuple)) and len(raw_path) > 0:
                pts = tuple(to_float(p) for p in raw_path)
            else:
                # 4-point default excursion path: 0.0 -> -MAE -> +MFE -> ProfitLoss
                pts = (0.0, -abs(mae), abs(mfe), pl)

            paths.append(
                TradeProfilePath(
                    ticket=ticket,
                    direction=raw_dir,
                    is_winner=pl > 0.0,
                    points=pts,
                )
            )

        # Compute mean and quartiles across points
        mean_path: list[float] = []
        q25_path: list[float] = []
        q75_path: list[float] = []

        if paths:
            max_len = max(len(p.points) for p in paths)
            for step in range(max_len):
                step_vals = [p.points[step] for p in paths if step < len(p.points)]
                step_vals.sort()
                n = len(step_vals)
                mean_path.append(round(sum(step_vals) / n, 2))
                q25_path.append(round(step_vals[int(n * 0.25)], 2))
                q75_path.append(round(step_vals[min(n - 1, int(n * 0.75))], 2))

        payload = ProfileChartPayload(
            result_key=result_key,
            unit=unit,
            paths=tuple(paths),
            mean_path=tuple(mean_path),
            quantile_25=tuple(q25_path),
            quantile_75=tuple(q75_path),
        )

        logger.info(
            "FR-results-profile-paths: constructed %d profile paths for %s",
            len(paths),
            strategy_id,
        )
        return wrap_response(
            request_id=f"req_{strategy_id}_profile_chart",
            data=payload,
            json_payload=payload.to_dict(),
        )

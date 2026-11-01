"""Strategy databank correlation filtering service.

Description:
    Implements DatabankFilterByCorrelationService evaluating pairwise
    correlations against a maximum correlation threshold, greedily selecting
    higher fitness strategies and flagging/removing correlated strategies.

Purpose:
    FEAT-RESULTS-CORRELATION-FILTER: Filter databank strategies by correlation.

Key Capabilities:
    - FR-results-correlation-filter: Greedy portfolio correlation filtering.

Python API Usage:
    from app.workspace.results.databank_filter_by_correlation import (
        CorrelationFilterRequest,
        DatabankFilterByCorrelationService,
    )
    service = DatabankFilterByCorrelationService()
    req = CorrelationFilterRequest("p1", "Results", ("S1", "S2"))
    resp = service.apply(req)

CLI Usage:
    python -m app.cli results filter-correlation --databank Results --max-corr 0.5
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Literal

from app.core.host.logging import get_logger
from app.core.lib.errors import DomainError
from app.core.lib.responses import StandardResponse
from app.core.trading.results.contracts import RunResult
from app.core.trading.results.store import ResultStore
from app.workspace.results.app_results import to_float, wrap_response

logger = get_logger(__name__)

MIN_CORRELATION_THRESHOLD = 0.0
MAX_CORRELATION_THRESHOLD = 1.0
MIN_CALC_LENGTH = 2


@dataclass(frozen=True, slots=True)
class CorrelationFilterRequest:
    """Request specification for filtering databank strategies by correlation."""

    project_id: str
    databank_name: str
    strategy_ids: tuple[str, ...]
    period: Literal["HOUR", "DAY", "WEEK", "MONTH"] = "DAY"
    method: str = "ProfitLoss"
    max_correlation: float = 0.5
    allow_negative: bool = False
    action: Literal["SELECT", "DELETE"] = "SELECT"

    def to_dict(self) -> dict[str, Any]:
        """Convert request to dictionary."""
        return {
            "project_id": self.project_id,
            "databank_name": self.databank_name,
            "strategy_ids": list(self.strategy_ids),
            "period": self.period,
            "method": self.method,
            "max_correlation": self.max_correlation,
            "allow_negative": self.allow_negative,
            "action": self.action,
        }


@dataclass(frozen=True, slots=True)
class CorrelationFilterResult:
    """Result of correlation filter execution."""

    kept_ids: tuple[str, ...]
    flagged_ids: tuple[str, ...]
    max_pair_correlation: dict[str, float]

    def to_dict(self) -> dict[str, Any]:
        """Convert filter result to dictionary."""
        return {
            "kept_ids": list(self.kept_ids),
            "flagged_ids": list(self.flagged_ids),
            "max_pair_correlation": dict(self.max_pair_correlation),
        }


class DatabankFilterByCorrelationService:
    """Service filtering strategies in a databank by pairwise correlation."""

    def __init__(self, store: ResultStore | None = None) -> None:
        """Initialize service with optional ResultStore."""
        self.store = store
        self._in_memory_results: dict[str, RunResult] = {}
        self._strategy_fitness: dict[str, float] = {}
        self._strategy_series: dict[str, list[float]] = {}
        self._revision: int = 1

    def register_candidate(
        self,
        strategy_id: str,
        fitness: float,
        series: list[float] | None = None,
        result: RunResult | None = None,
    ) -> None:
        """Register strategy candidate with explicit fitness and return series."""
        self._strategy_fitness[strategy_id] = fitness
        if series is not None:
            self._strategy_series[strategy_id] = list(series)
        if result is not None:
            self._in_memory_results[strategy_id] = result

    def register_in_memory_result(self, result: RunResult) -> None:
        """Register RunResult extracting fitness from metrics."""
        self._in_memory_results[result.strategy_id] = result
        fit = to_float(
            result.metrics.get("fitness", result.metrics.get("net_profit", 0.0))
        )
        self._strategy_fitness[result.strategy_id] = fit

    def apply(
        self, request: CorrelationFilterRequest
    ) -> StandardResponse[CorrelationFilterResult]:
        """Filter strategies greedily retaining higher fitness non-correlated ones."""
        logger.info(
            "FR-results-correlation-filter: filter max_corr=%.2f on %d strats in %s",
            request.max_correlation,
            len(request.strategy_ids),
            request.databank_name,
        )
        if not (
            MIN_CORRELATION_THRESHOLD
            < request.max_correlation
            <= MAX_CORRELATION_THRESHOLD
        ):
            raise DomainError(
                code="RESULTS_INVALID_CORRELATION_THRESHOLD",
                message=(
                    f"Threshold must be in (0.0, 1.0], got {request.max_correlation}"
                ),
                details={"max_correlation": request.max_correlation},
            )

        # Sort candidates: descending fitness, tie-breaker ascending strategy_id
        def sort_key(sid: str) -> tuple[float, str]:
            fit = self._strategy_fitness.get(sid, 0.0)
            return (-fit, sid)

        ranked = sorted(request.strategy_ids, key=sort_key)

        kept: list[str] = []
        flagged: list[str] = []
        max_corrs: dict[str, float] = {}

        for sid in ranked:
            is_correlated = False
            sid_series = self._strategy_series.get(sid, [0.0])
            highest_corr = 0.0

            for k in kept:
                k_series = self._strategy_series.get(k, [0.0])
                corr = self._calc_pearson(sid_series, k_series)
                comp_corr = corr if request.allow_negative else abs(corr)
                if abs(corr) > abs(highest_corr):
                    highest_corr = corr

                if comp_corr >= request.max_correlation:
                    is_correlated = True
                    break

            max_corrs[sid] = round(highest_corr, 4)

            if is_correlated:
                flagged.append(sid)
            else:
                kept.append(sid)

        if request.action == "DELETE":
            for fid in flagged:
                self._in_memory_results.pop(fid, None)
                self._strategy_fitness.pop(fid, None)
                self._strategy_series.pop(fid, None)
            self._revision += 1

        result = CorrelationFilterResult(
            kept_ids=tuple(kept),
            flagged_ids=tuple(flagged),
            max_pair_correlation=max_corrs,
        )

        logger.info(
            "FR-results-correlation-filter: kept %d, flagged %d",
            len(kept),
            len(flagged),
        )

        return wrap_response(
            request_id="req_correlation_filter",
            data=result,
            json_payload=result.to_dict(),
            revision=self._revision,
        )

    @staticmethod
    def _calc_pearson(x: list[float], y: list[float]) -> float:
        min_len = min(len(x), len(y))
        if min_len < MIN_CALC_LENGTH:
            return 1.0 if x == y else 0.0

        xs = x[:min_len]
        ys = y[:min_len]

        mean_x = sum(xs) / min_len
        mean_y = sum(ys) / min_len

        var_x = sum((val - mean_x) ** 2 for val in xs)
        var_y = sum((val - mean_y) ** 2 for val in ys)

        if var_x == 0.0 or var_y == 0.0:
            return 1.0 if xs == ys else 0.0

        cov = sum((xs[k] - mean_x) * (ys[k] - mean_y) for k in range(min_len))
        corr = cov / math.sqrt(var_x * var_y)
        return round(max(-1.0, min(1.0, corr)), 4)

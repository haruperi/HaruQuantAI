"""Project-owned result inspection and full-collection leaderboard projection.

Description:
    Reads results through ResultStore, enforces native project databank ownership,
    and ranks all stored records before applying the presentation limit.
Purpose:
    FEAT-HOME-RESULTS: Present persisted research evidence without demo metrics.
Key Capabilities:
    - FR-home-result-ownership: Reject cross-project databank/result access;
      projection tests verify rejection and explicit access logs.
    - FR-home-result-ranking: Rank complete collections by finite stored metrics;
      tests verify ordering beyond the first page and sample availability.
Python API Usage:
    projection = ResultProjection(store)
CLI Usage:
    uv run python -m pytest tests/workspace/home/test_result_projection.py --no-cov
"""

from __future__ import annotations

import math
from typing import Any

from app.core.host.logging import get_logger
from app.core.lib.errors import DomainError
from app.core.trading.project.contracts import ProjectDocument
from app.core.trading.results.store import ResultStore

logger = get_logger(__name__)
_PAGE_SIZE = 1000
METRICS = {
    "net_profit",
    "sharpe_ratio",
    "drawdown",
    "profit_factor",
    "win_rate",
    "trades_count",
}


class ResultProjection:
    """Project-authorized result reads through the owning Core capability."""

    def __init__(self, store: ResultStore) -> None:
        self.store = store

    @staticmethod
    def require_bank(project: ProjectDocument, databank_id: str) -> None:
        """Validate a destination against native project databank identities."""
        if databank_id not in project.databanks.values():
            raise DomainError(
                code="DATABANK_NOT_FOUND", message="Databank is outside this project"
            )

    def detail(self, project: ProjectDocument, result_id: str) -> dict[str, Any]:
        """Return actual trade, equity, parameters, strategy and sample evidence."""
        result = self.store.get_result(result_id)
        self.require_bank(project, result.databank_id)
        logger.info("FR-home-result-ownership: inspected owned result %s", result_id)
        return result.to_dict()

    def leaderboard(
        self,
        project: ProjectDocument,
        databank_id: str,
        sample_type: str,
        metric: str,
        limit: int,
    ) -> dict[str, Any]:
        """Rank stored metrics over every page; absent samples remain absent."""
        self.require_bank(project, databank_id)
        if metric not in METRICS:
            raise DomainError(
                code="INVALID_METRIC", message="Unsupported ranking metric"
            )
        if sample_type not in {"ALL", "IS", "OOS"}:
            raise DomainError(
                code="INVALID_SAMPLE_TYPE", message="Unsupported sample partition"
            )
        key = metric if sample_type == "ALL" else f"{metric}_{sample_type.lower()}"
        candidates: list[dict[str, Any]] = []
        offset = 0
        while True:
            page = self.store.list_results(databank_id, limit=_PAGE_SIZE, offset=offset)
            for summary in page:
                result = self.store.get_result(summary.result_id)
                value = result.metrics.get(key)
                if isinstance(value, (int, float)) and math.isfinite(value):
                    candidates.append(
                        {
                            "id": result.result_id,
                            "strategy_id": result.strategy_id,
                            "name": result.strategy_name,
                            metric: value,
                        }
                    )
            if len(page) < _PAGE_SIZE:
                break
            offset += len(page)
        candidates.sort(
            key=lambda item: (
                item[metric] if metric == "drawdown" else -item[metric],
                item["id"],
            )
        )
        logger.info("FR-home-result-ranking: ranked %d stored results", len(candidates))
        return {
            "project_id": project.manifest.project_id,
            "databank_id": databank_id,
            "sample_type": sample_type,
            "metric": metric,
            "total_candidates": len(candidates),
            "strategies": candidates[:limit],
        }

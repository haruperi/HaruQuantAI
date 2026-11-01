"""Project-authorized, complete-collection result projection checks.

Description:
    Verifies finite leaderboard sorting, real sample availability and project
    ownership using the result capability contract without active user stores.
Purpose:
    FEAT-HOME-RESULT-ACCEPTANCE: Evidence-backed stored result presentation.
Key Capabilities:
    - FR-home-result-ranking: Verify paging and ordering with explicit log checks.
    - FR-home-result-ownership: Verify unauthorized result rejection.
Python API Usage:
    pytest tests/workspace/home/test_result_projection.py
CLI Usage:
    uv run python -m pytest tests/workspace/home/test_result_projection.py --no-cov
"""

from __future__ import annotations

from typing import Any, cast

import pytest
from app.core.lib.errors import DomainError
from app.core.trading.project.contracts import ProjectDocument, ProjectManifest
from app.core.trading.results.contracts import ResultSummary, RunResult
from app.core.trading.results.store import ResultStore
from app.workspace.home.result_projection import ResultProjection


class Results:
    """Owning-capability fixture with a best candidate after the first page."""

    def __init__(self) -> None:
        self.records = {
            str(i): RunResult(
                str(i),
                "bank",
                str(i),
                f"Strategy {i}",
                metrics={"net_profit": i, "drawdown": i},
            )
            for i in range(1002)
        }

    def list_results(
        self, databank_id: str, limit: int, offset: int
    ) -> list[ResultSummary]:
        return [
            record.to_summary()
            for record in self.records.values()
            if record.databank_id == databank_id
        ][offset : offset + limit]

    def get_result(self, result_id: str) -> RunResult:
        return self.records[result_id]


def test_ranks_all_pages_before_limiting(caplog: Any) -> None:
    """The leaderboard includes a winner beyond the first thousand results."""
    project = ProjectDocument(
        ProjectManifest("project", "Project"), databanks={"Results": "bank"}
    )
    projection = ResultProjection(cast("ResultStore", Results()))
    with caplog.at_level("INFO"):
        ranked = projection.leaderboard(project, "bank", "ALL", "net_profit", 1)
    assert ranked["strategies"][0]["id"] == "1001"
    assert ranked["total_candidates"] == 1002
    assert "FR-home-result-ranking" in caplog.text
    assert (
        projection.leaderboard(project, "bank", "ALL", "drawdown", 1)["strategies"][0][
            "id"
        ]
        == "0"
    )
    assert (
        projection.leaderboard(project, "bank", "OOS", "net_profit", 1)["strategies"]
        == []
    )


def test_owned_result_details_and_cross_project_rejection(caplog: Any) -> None:
    """Ownership checks use native databank identities, including result details."""
    project = ProjectDocument(
        ProjectManifest("project", "Project"), databanks={"Results": "bank"}
    )
    projection = ResultProjection(cast("ResultStore", Results()))
    with caplog.at_level("INFO"):
        assert projection.detail(project, "1")["result_id"] == "1"
    assert "FR-home-result-ownership" in caplog.text
    other = ProjectDocument(
        ProjectManifest("other", "Other"), databanks={"bank": "different"}
    )
    with pytest.raises(DomainError) as caught:
        projection.detail(other, "1")
    assert caught.value.code == "DATABANK_NOT_FOUND"


@pytest.mark.parametrize(
    "bank,sample,metric,code",
    [
        ("foreign", "ALL", "net_profit", "DATABANK_NOT_FOUND"),
        ("bank", "TRAIN", "net_profit", "INVALID_SAMPLE_TYPE"),
        ("bank", "ALL", "invented_score", "INVALID_METRIC"),
    ],
)
def test_invalid_leaderboard_requests_fail_closed(
    bank: str, sample: str, metric: str, code: str
) -> None:
    """Unknown ownership, samples and scores cannot produce plausible rankings."""
    project = ProjectDocument(
        ProjectManifest("project", "Project"), databanks={"Results": "bank"}
    )
    store = Results()
    before = dict(store.records)
    with pytest.raises(DomainError) as caught:
        ResultProjection(cast("ResultStore", store)).leaderboard(
            project, bank, sample, metric, 5
        )
    assert caught.value.code == code
    assert store.records == before


def test_rankings_use_finite_sample_values_and_stable_ties(caplog: Any) -> None:
    """IS scores differ from ALL; NaN/infinite/missing sample values stay absent."""
    project = ProjectDocument(
        ProjectManifest("project", "Project"), databanks={"Results": "bank"}
    )
    store = Results()
    sample_rows: list[tuple[str, dict[str, float | int | str]]] = [
        ("b", {"net_profit": 100, "net_profit_is": 3}),
        ("a", {"net_profit": 1, "net_profit_is": 3}),
        ("c", {"net_profit": 50, "net_profit_is": float("inf")}),
        ("d", {"net_profit": 50, "net_profit_is": float("nan")}),
        ("e", {"net_profit": 50}),
    ]
    store.records = {
        identity: RunResult(identity, "bank", identity, identity, metrics=metrics)
        for identity, metrics in sample_rows
    }
    projection = ResultProjection(cast("ResultStore", store))
    with caplog.at_level("INFO"):
        sample = projection.leaderboard(project, "bank", "IS", "net_profit", 1)
    assert sample["total_candidates"] == 2
    assert sample["strategies"] == [
        {"id": "a", "strategy_id": "a", "name": "a", "net_profit": 3}
    ]
    assert "FR-home-result-ranking: ranked 2 stored results" in caplog.text
    overall = projection.leaderboard(project, "bank", "ALL", "net_profit", 1)
    assert overall["strategies"][0]["id"] == "b"


def test_owned_empty_bank_returns_explicit_empty_collection() -> None:
    """A valid empty databank has no fabricated default candidates or metrics."""
    project = ProjectDocument(
        ProjectManifest("project", "Project"), databanks={"Results": "bank"}
    )
    store = Results()
    store.records.clear()
    response = ResultProjection(cast("ResultStore", store)).leaderboard(
        project, "bank", "ALL", "drawdown", 10
    )
    assert response["total_candidates"] == 0
    assert response["strategies"] == []

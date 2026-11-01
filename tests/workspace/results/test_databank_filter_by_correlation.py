"""Unit tests for DatabankFilterByCorrelationService."""

from __future__ import annotations

import pytest
from app.core.lib.errors import DomainError
from app.workspace.results.databank_filter_by_correlation import (
    CorrelationFilterRequest,
    CorrelationFilterResult,
    DatabankFilterByCorrelationService,
)


class TestDatabankFilterByCorrelationService:
    """Test suite for DatabankFilterByCorrelationService."""

    def test_golden_fixture_filter_by_correlation(self) -> None:
        """Verify greedy correlation filter retaining highest fitness candidates."""
        service = DatabankFilterByCorrelationService()
        # S1: fitness 0.9, series [1, 2, 3, 4]
        service.register_candidate("S1", 0.9, [1.0, 2.0, 3.0, 4.0])
        # S2: fitness 0.8, series [1.1, 2.05, 2.9, 4.1] -> very high correlation with S1 (~0.99)
        service.register_candidate("S2", 0.8, [1.1, 2.05, 2.9, 4.1])
        # S3: fitness 0.7, series [4.0, 1.0, 3.0, 2.0] -> uncorrelated / lower correlation
        service.register_candidate("S3", 0.7, [4.0, 1.0, 3.0, 2.0])

        req = CorrelationFilterRequest(
            project_id="p1",
            databank_name="Results",
            strategy_ids=("S1", "S2", "S3"),
            max_correlation=0.5,
            action="SELECT",
        )
        resp = service.apply(req)
        result = resp.data

        assert result.kept_ids == ("S1", "S3")
        assert result.flagged_ids == ("S2",)
        assert result.max_pair_correlation["S2"] >= 0.5

    def test_invalid_correlation_threshold(self) -> None:
        """Verify threshold <= 0 or > 1 raises DomainError."""
        service = DatabankFilterByCorrelationService()
        req_zero = CorrelationFilterRequest(
            project_id="p1",
            databank_name="Results",
            strategy_ids=("S1",),
            max_correlation=0.0,
        )
        with pytest.raises(DomainError) as exc_info:
            service.apply(req_zero)
        assert exc_info.value.code == "RESULTS_INVALID_CORRELATION_THRESHOLD"

        req_high = CorrelationFilterRequest(
            project_id="p1",
            databank_name="Results",
            strategy_ids=("S1",),
            max_correlation=1.5,
        )
        with pytest.raises(DomainError) as exc_info:
            service.apply(req_high)
        assert exc_info.value.code == "RESULTS_INVALID_CORRELATION_THRESHOLD"

    def test_filter_action_delete(self) -> None:
        """Verify action="DELETE" removes flagged candidates from memory."""
        service = DatabankFilterByCorrelationService()
        service.register_candidate("S1", 0.9, [1.0, 2.0, 3.0, 4.0])
        service.register_candidate("S2", 0.8, [1.0, 2.0, 3.0, 4.0])

        req = CorrelationFilterRequest(
            project_id="p1",
            databank_name="Results",
            strategy_ids=("S1", "S2"),
            max_correlation=0.5,
            action="DELETE",
        )
        resp = service.apply(req)
        assert resp.data.flagged_ids == ("S2",)
        assert "S2" not in service._strategy_fitness

    def test_to_dict_serialization(self) -> None:
        """Verify request and result to_dict."""
        res = CorrelationFilterResult(
            kept_ids=("S1",),
            flagged_ids=("S2",),
            max_pair_correlation={"S2": 0.8},
        )
        d = res.to_dict()
        assert d["kept_ids"] == ["S1"]
        assert d["flagged_ids"] == ["S2"]

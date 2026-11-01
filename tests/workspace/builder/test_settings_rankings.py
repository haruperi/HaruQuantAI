"""Unit tests for SettingsRankings service and models."""

from __future__ import annotations

import pytest
from app.core.lib.errors import DomainError
from app.workspace.builder.settings_rankings import (
    RankingFilterCondition,
    RankingsSettings,
    SettingsRankingsService,
)


def test_golden_fixture_candidate_evaluation() -> None:
    """Verify candidate evaluation with ProfitFactor >= 1.3 and NumberOfTrades >= 100."""
    service = SettingsRankingsService()
    settings = RankingsSettings(
        conditions=(
            RankingFilterCondition(
                column_id="ProfitFactor", operator=">=", threshold=1.3
            ),
            RankingFilterCondition(
                column_id="NumberOfTrades", operator=">=", threshold=100
            ),
        )
    )

    stats = {
        "ProfitFactor": 1.45,
        "NumberOfTrades": 120,
        "ReturnDDRatio": 2.5,
    }

    passed, fitness, failed_descriptions = service.evaluate_candidate(stats, settings)
    assert passed is True
    assert fitness > 0.0
    assert failed_descriptions == ()


def test_failed_candidate_condition() -> None:
    """Ensure candidate failing a condition returns passed=False with description."""
    service = SettingsRankingsService()
    settings = RankingsSettings(
        conditions=(
            RankingFilterCondition(
                column_id="ProfitFactor", operator=">=", threshold=1.5
            ),
        )
    )
    stats = {
        "ProfitFactor": 1.20,
        "NumberOfTrades": 100,
        "ReturnDDRatio": 2.0,
    }

    passed, _, failed_descriptions = service.evaluate_candidate(stats, settings)
    assert passed is False
    assert len(failed_descriptions) == 1
    assert "ProfitFactor >= 1.5 failed" in failed_descriptions[0]


def test_change_max_records_bounds() -> None:
    """Verify change_max_records succeeds for valid range and fails outside."""
    service = SettingsRankingsService()
    resp = service.change_max_records("proj_1", "Results", 500)
    assert resp.data == 500

    # Max records < 1
    with pytest.raises(DomainError) as exc:
        service.change_max_records("proj_1", "Results", 0)
    assert exc.value.code == "BUILDER_INVALID_MAX_RECORDS"

    # Max records > 100,000
    with pytest.raises(DomainError) as exc:
        service.change_max_records("proj_1", "Results", 100_001)
    assert exc.value.code == "BUILDER_INVALID_MAX_RECORDS"


def test_comparison_operators_and_missing_metric() -> None:
    """Verify all comparison operators and handling of missing metrics."""
    service = SettingsRankingsService()
    settings = RankingsSettings(
        conditions=(
            RankingFilterCondition(column_id="Drawdown", operator="<", threshold=25.0),
            RankingFilterCondition(column_id="MaxLoss", operator="<=", threshold=500.0),
            RankingFilterCondition(
                column_id="TargetTrades", operator="==", threshold=100.0
            ),
            RankingFilterCondition(column_id="MissingCol", operator=">", threshold=1.0),
        )
    )

    stats = {
        "Drawdown": 20.0,
        "MaxLoss": 500.0,
        "TargetTrades": 100.0,
    }

    passed, _, failures = service.evaluate_candidate(stats, settings)
    assert passed is False
    assert any("metric unavailable" in f for f in failures)
    assert settings.to_dict()["target_databank"] == "Results"

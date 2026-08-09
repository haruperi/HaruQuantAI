"""Tests for the scenario-holdout anti-leakage port (feature)."""

from collections.abc import Mapping

import pytest
from app.services.optimization import (
    detect_scenario_leakage,
    evaluate_scenario_holdout,
    get_scenario_holdout_contract_version,
)


def test_scenario_holdout_fails_closed_without_provider() -> None:
    """Missing provider yields SCENARIO_HOLDOUT_UNAVAILABLE and validation_needed."""
    result = evaluate_scenario_holdout(
        market_data_ref="data-1",
        validation_window=("2026-01-01T00:00:00+00:00", "2026-02-01T00:00:00+00:00"),
        provider=None,
    )
    assert result["status"] == "SCENARIO_HOLDOUT_UNAVAILABLE"
    assert result["decision"] == "validation_needed"
    assert result["provider_feature"] == "FEAT-SIM-11"


def test_scenario_holdout_passes_through_provider_evidence() -> None:
    """A present provider's evidence is passed through."""

    class FakeProvider:
        def scenario_holdout_mask(
            self, *, market_data_ref: str, validation_window: tuple[str, str]
        ) -> Mapping[str, object]:
            del market_data_ref, validation_window
            return {"masked_count": 5}

    result = evaluate_scenario_holdout(
        market_data_ref="data-1",
        validation_window=("2026-01-01T00:00:00+00:00", "2026-02-01T00:00:00+00:00"),
        provider=FakeProvider(),
    )
    assert result["status"] == "HOLDOUT_LOCKED"
    assert result["masked_count"] == 5


def test_detect_scenario_leakage_reports_overlap() -> None:
    """Overlapping scenario identifiers are reported as leakage."""
    result = detect_scenario_leakage(
        training_scenario_ids=("s1", "s2", "s3"),
        validation_scenario_ids=("s2", "s4"),
    )
    assert result["leakage_detected"] is True
    assert result["overlapping_scenarios"] == ("s2",)


def test_detect_scenario_leakage_reports_no_overlap() -> None:
    """No overlap reports no_local_leakage without inferring a clean pass."""
    result = detect_scenario_leakage(
        training_scenario_ids=("s1", "s2"),
        validation_scenario_ids=("s3", "s4"),
    )
    assert result["leakage_detected"] is False
    assert result["decision"] == "no_local_leakage"


def test_detect_scenario_leakage_rejects_empty_inputs() -> None:
    """Empty scenario sequences are rejected, not treated as a clean holdout."""
    with pytest.raises(ValueError, match="non-empty"):
        detect_scenario_leakage(
            training_scenario_ids=(), validation_scenario_ids=("s1",)
        )


def test_scenario_holdout_contract_version() -> None:
    """Consumer version is canonical."""
    assert get_scenario_holdout_contract_version() == "v1"

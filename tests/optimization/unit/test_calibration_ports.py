"""Tests for deferred-integration calibration ports (feature, feature)."""

from collections.abc import Mapping

from app.services.optimization import (
    get_calibration_contract_version,
    resolve_fill_model_calibration,
    resolve_scenario_difficulty_calibration,
)


def test_fill_model_calibration_fails_closed_without_provider() -> None:
    """Missing fill-model provider yields NOT_CALIBRATED, never fabricated params."""
    result = resolve_fill_model_calibration(
        market_data_ref="data-1", instrument="EURUSD", provider=None
    )
    assert result["status"] == "NOT_CALIBRATED"
    assert result["provider_feature"] == "FEAT-SIM-12"
    assert "reason" in result


def test_scenario_difficulty_fails_closed_without_provider() -> None:
    """Missing scenario provider yields NOT_CALIBRATED."""
    result = resolve_scenario_difficulty_calibration(
        market_data_ref="data-1", competence_target="intermediate", provider=None
    )
    assert result["status"] == "NOT_CALIBRATED"
    assert result["provider_feature"] == "FEAT-SIM-11"


def test_fill_model_passes_through_provider_evidence() -> None:
    """A present provider's evidence is passed through as CALIBRATED."""

    class FakeProvider:
        def fill_model_calibration(
            self, *, market_data_ref: str, instrument: str
        ) -> Mapping[str, object]:
            del market_data_ref, instrument
            return {"latency_ms": 12.0}

    result = resolve_fill_model_calibration(
        market_data_ref="data-1", instrument="EURUSD", provider=FakeProvider()
    )
    assert result["status"] == "CALIBRATED"
    assert result["latency_ms"] == 12.0


def test_scenario_difficulty_passes_through_provider_evidence() -> None:
    """A present provider's evidence is passed through."""

    class FakeProvider:
        def scenario_difficulty_calibration(
            self, *, market_data_ref: str, competence_target: str
        ) -> Mapping[str, object]:
            del market_data_ref, competence_target
            return {"intensity": 0.7}

    result = resolve_scenario_difficulty_calibration(
        market_data_ref="data-1",
        competence_target="intermediate",
        provider=FakeProvider(),
    )
    assert result["status"] == "CALIBRATED"
    assert result["intensity"] == 0.7


def test_calibration_contract_version() -> None:
    """Consumer-port version is canonical."""
    assert get_calibration_contract_version() == "v1"


def test_fill_model_provider_never_inferred() -> None:
    """Absent provider never returns an inferred approval."""
    result = resolve_fill_model_calibration(
        market_data_ref="data-1", instrument="EURUSD", provider=None
    )
    assert result["status"] == "NOT_CALIBRATED"
    assert "latency_ms" not in result

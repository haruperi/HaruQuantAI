"""Runnable examples for Simulation validation."""

from app.services.simulator.validation import (
    validate_market_data,
    validate_phase_one_scope,
    validate_run_inputs,
)
from tests.simulator.unit.test_validate import _context, _dataset


def _payload() -> dict[str, object]:
    """Build a reference-only usage payload."""
    return {
        "request_id": "req-simulator-usage",
        "workflow_id": "wf-simulator-usage",
        "correlation_id": "cor-simulator-usage",
        "strategy_id": "registered-strategy",
        "strategy_version": "v1",
        "strategy_config_ref": "strategy-config",
        "strategy_config_hash": "a" * 64,
        "data_ref": "market-data",
        "data_version": "v1",
        "data_hash": "b" * 64,
        "execution_profile_ref": "execution-profile",
        "execution_profile_version": "v1",
        "execution_profile_hash": "c" * 64,
        "risk_policy_ref": "sim-policy",
        "risk_policy_version": "v1",
        "risk_policy_hash": "d" * 64,
        "symbol": "EURUSD",
        "config_hash": "e" * 64,
    }


def test_usage_validate_run_inputs() -> None:
    """Validate deterministic request references."""
    validate_run_inputs(_payload())


def test_usage_validate_phase_one_scope() -> None:
    """Validate the official FX simulation profile."""
    validate_phase_one_scope(
        {
            "asset_class": "FX",
            "runtime_profile": "simulation",
            "execution_route": "sim",
        }
    )


def test_usage_validate_market_data() -> None:
    """Validate Data-owned evidence against an explicit immutable context."""
    dataset = _dataset()
    evidence = validate_market_data(dataset, _context(dataset))
    assert evidence.record_count == dataset.record_count

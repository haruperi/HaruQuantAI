"""Unit tests for Simulator calibration, spread, crash points, and realism providers."""

from __future__ import annotations

import pytest
from app.services.simulator.realism.crash_points import create_state, get_points
from app.services.simulator.realism.providers import build_fill_model_provider


def test_simulator_realism_crash_points() -> None:
    """Verify get_points and create_state for deterministic crash points."""
    points = get_points()
    assert "after_pre_audit" in points
    assert "after_projection_update" in points

    state = create_state(
        command_id="cmd-1",
        crash_point="after_pre_audit",
        outcome="accepted",
        mutation_attempts=1,
    )
    assert state["command_id"] == "cmd-1"
    assert state["crash_point"] == "after_pre_audit"

    with pytest.raises(ValueError, match="unknown deterministic crash point"):
        create_state(
            command_id="cmd-2",
            crash_point="invalid_crash_point",
            outcome="accepted",
        )


def test_simulator_fill_model_provider() -> None:
    """Verify build_fill_model_provider returns calibrated and uncalibrated responses."""
    profiles = {
        "EURUSD": {"market_data_ref": "mkt-1", "slippage_p50": "0.5"},
    }
    provider = build_fill_model_provider(profiles)

    cal = provider.fill_model_calibration(market_data_ref="mkt-1", instrument="EURUSD")
    assert cal["status"] == "CALIBRATED"

    uncal = provider.fill_model_calibration(
        market_data_ref="mkt-1", instrument="GBPUSD"
    )
    assert uncal["status"] == "NOT_CALIBRATED"

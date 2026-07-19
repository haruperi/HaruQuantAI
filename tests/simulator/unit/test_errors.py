"""Unit tests for the Simulation error surface."""
# ruff: noqa: INP001

import pytest
from app.services.simulator.errors import (
    SIM_ERROR_CATALOG,
    SimulationError,
    to_simulation_error_payload,
)


def test_error_rejects_uncataloged_code() -> None:
    """Reject any exception identity absent from the closed catalog."""
    with pytest.raises(ValueError, match="not cataloged"):
        SimulationError("SIM_NOT_REGISTERED", "Unknown failure")


def test_catalog_matches_documented_requirements() -> None:
    """Verify the closed catalog has only prefixed fail-closed codes."""
    assert len(SIM_ERROR_CATALOG) == 43
    assert all(code.startswith("SIM_") for code in SIM_ERROR_CATALOG)
    assert all(row["effect"] == "fail_closed" for row in SIM_ERROR_CATALOG.values())


def test_error_payload_is_bounded_and_redacted() -> None:
    """Verify uncontrolled exception details cannot cross the boundary."""
    payload = to_simulation_error_payload(RuntimeError("password=C:/secret"))
    assert payload == {
        "code": "SIM_INTERNAL_ERROR",
        "message": "Simulation failed safely",
    }


def test_controlled_error_preserves_safe_identity() -> None:
    """Verify a controlled error retains its code and request identity."""
    error = SimulationError(
        "SIM_INVALID_CONFIG",
        "Configuration is invalid",
        request_id="req-example",
    )
    assert to_simulation_error_payload(error)["request_id"] == "req-example"


def test_controlled_error_redacts_details_and_correlation() -> None:
    """Bound details and preserve safe correlation evidence."""
    error = SimulationError(
        "SIM_INVALID_CONFIG",
        "Configuration password=secret is invalid",
        details={"token": "secret", "field": "profile"},
        correlation_id="cor-example",
    )
    payload = to_simulation_error_payload(error)
    assert "secret" not in str(payload)
    assert payload["correlation_id"] == "cor-example"

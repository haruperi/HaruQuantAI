"""Runnable usage examples for Simulation errors."""

from app.services.simulator.errors import (
    SIM_ERROR_CATALOG,
    SimulationError,
    to_simulation_error_payload,
)


def test_usage_simulation_error() -> None:
    """Construct one controlled public error."""
    error = SimulationError("SIM_MARKET_CLOSED", "Configured market is closed")
    assert error.code == "SIM_MARKET_CLOSED"


def test_usage_error_catalog() -> None:
    """Inspect the authoritative catalog."""
    assert SIM_ERROR_CATALOG["SIM_MARKET_CLOSED"]["group"] == "execution_accounting"


def test_usage_error_payload() -> None:
    """Convert a controlled exception to a safe payload."""
    payload = to_simulation_error_payload(
        SimulationError("SIM_INVALID_CONFIG", "Invalid configuration")
    )
    assert payload["code"] == "SIM_INVALID_CONFIG"

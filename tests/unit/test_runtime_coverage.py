"""Coverage expansion tests for app/runtime.py."""

import pytest
from app.runtime import RuntimeConfigurationError, validate_runtime_configuration


def test_validate_runtime_configuration_valid_pairs() -> None:
    """Verify valid runtime_profile and execution_route pairings pass."""
    validate_runtime_configuration(runtime_profile="research", execution_route="none")
    validate_runtime_configuration(runtime_profile="simulation", execution_route="sim")
    validate_runtime_configuration(runtime_profile="paper", execution_route="paper")
    validate_runtime_configuration(runtime_profile="live", execution_route="live")


def test_validate_runtime_configuration_invalid_pairs() -> None:
    """Verify incompatible or unknown pairings raise RuntimeConfigurationError."""
    with pytest.raises(
        RuntimeConfigurationError,
        match="Runtime profile and execution route are incompatible",
    ):
        validate_runtime_configuration(
            runtime_profile="research", execution_route="live"
        )

    with pytest.raises(RuntimeConfigurationError):
        validate_runtime_configuration(
            runtime_profile="unknown_profile", execution_route="none"
        )

    error = RuntimeConfigurationError()
    assert error.code == "SYSTEM_RUNTIME_ROUTE_INCOMPATIBLE"

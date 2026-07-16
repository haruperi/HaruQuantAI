import pytest
from app import RuntimeConfigurationError, validate_runtime_configuration


def test_application_boundary_fails_closed_before_incompatible_initialization():
    with pytest.raises(RuntimeConfigurationError):
        validate_runtime_configuration(
            runtime_profile="live",
            execution_route="paper",
        )


def test_application_boundary_allows_only_authoritative_initialization_pair():
    validate_runtime_configuration(
        runtime_profile="simulation",
        execution_route="sim",
    )

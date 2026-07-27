"""Coverage expansion tests for app/runtime.py."""

from app.runtime import validate_runtime_configuration


def test_validate_runtime_configuration_valid_pairs() -> None:
    """Verify valid runtime_profile and execution_route pairings succeed."""
    responses = (
        validate_runtime_configuration(
            runtime_profile="research",
            execution_route="none",
        ),
        validate_runtime_configuration(
            runtime_profile="simulation",
            execution_route="sim",
        ),
        validate_runtime_configuration(
            runtime_profile="paper",
            execution_route="paper",
        ),
        validate_runtime_configuration(
            runtime_profile="live",
            execution_route="live",
        ),
    )

    assert all(response.status == "success" for response in responses)
    assert all(response.data is None for response in responses)


def test_validate_runtime_configuration_invalid_pairs() -> None:
    """Verify incompatible or unknown pairings return structured errors."""
    responses = (
        validate_runtime_configuration(
            runtime_profile="research",
            execution_route="live",
        ),
        validate_runtime_configuration(
            runtime_profile="unknown_profile",
            execution_route="none",
        ),
    )

    assert all(response.status == "error" for response in responses)
    assert all(response.data is None for response in responses)
    assert all(
        response.error is not None
        and response.error.code == "SYSTEM_RUNTIME_ROUTE_INCOMPATIBLE"
        for response in responses
    )

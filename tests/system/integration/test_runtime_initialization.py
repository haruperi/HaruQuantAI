import app
from app import validate_runtime_configuration


def test_application_boundary_fails_closed_before_incompatible_initialization():
    response = validate_runtime_configuration(
        runtime_profile="live",
        execution_route="paper",
    )

    assert response.status == "error"
    assert response.data is None
    assert response.error is not None
    assert response.error.code == "SYSTEM_RUNTIME_ROUTE_INCOMPATIBLE"


def test_application_boundary_allows_only_authoritative_initialization_pair():
    response = validate_runtime_configuration(
        runtime_profile="simulation",
        execution_route="sim",
    )

    assert response.status == "success"
    assert response.data is None
    assert response.error is None


def test_application_boundary_exports_only_the_runtime_operation():
    assert app.__all__ == ("validate_runtime_configuration",)

from itertools import product

import pytest
from app.runtime import validate_runtime_configuration
from app.utils import validate_id

_COMPATIBLE_PAIRS = (
    ("research", "none"),
    ("simulation", "sim"),
    ("demo", "demo"),
    ("live", "live"),
)
_PROFILES = tuple(profile for profile, _ in _COMPATIBLE_PAIRS)
_ROUTES = tuple(route for _, route in _COMPATIBLE_PAIRS)


@pytest.mark.parametrize(("runtime_profile", "execution_route"), _COMPATIBLE_PAIRS)
def test_validate_runtime_configuration_accepts_compatible_pair(
    runtime_profile,
    execution_route,
):
    response = validate_runtime_configuration(
        runtime_profile=runtime_profile,
        execution_route=execution_route,
    )

    assert response.status == "success"
    assert response.message == "Runtime profile and execution route are compatible"
    assert response.data is None
    assert response.error is None
    assert set(response.model_dump(mode="json")) == {
        "status",
        "message",
        "data",
        "error",
        "metadata",
    }
    assert response.metadata.name == "app.runtime.validate_runtime_configuration"
    assert response.metadata.domain == "app"
    assert str(response.metadata.risk_level) == "none"
    assert validate_id(response.metadata.request_id, expected_prefix="req")
    assert response.metadata.correlation_id is None
    assert response.metadata.execution_ms >= 0
    assert response.metadata.execution_ms == round(response.metadata.execution_ms, 3)
    assert response.metadata.read_only is True
    assert response.metadata.writes_file is False
    assert response.metadata.modifies_database is False
    assert response.metadata.places_trade is False
    assert response.metadata.requires_network is False
    assert dict(response.metadata.extensions) == {}


@pytest.mark.parametrize(
    ("runtime_profile", "execution_route"),
    tuple(
        pair for pair in product(_PROFILES, _ROUTES) if pair not in _COMPATIBLE_PAIRS
    ),
)
def test_validate_runtime_configuration_rejects_incompatible_pair(
    runtime_profile,
    execution_route,
):
    response = validate_runtime_configuration(
        runtime_profile=runtime_profile,
        execution_route=execution_route,
    )

    assert response.status == "error"
    assert response.message == "Runtime profile and execution route are incompatible"
    assert response.data is None
    assert response.error is not None
    assert response.error.code == "SYSTEM_RUNTIME_ROUTE_INCOMPATIBLE"
    assert dict(response.error.details) == {
        "detail": "RUNTIME_PROFILE_EXECUTION_ROUTE_INCOMPATIBLE"
    }
    assert dict(response.metadata.extensions) == {}


@pytest.mark.parametrize(
    ("runtime_profile", "execution_route"),
    [
        ("", "none"),
        ("Research", "none"),
        ("research ", "none"),
        ("research", ""),
        ("research", "NONE"),
        ("research", "none "),
        ("unknown", "unknown"),
    ],
)
def test_validate_runtime_configuration_rejects_unknown_or_noncanonical_value(
    runtime_profile,
    execution_route,
):
    response = validate_runtime_configuration(
        runtime_profile=runtime_profile,
        execution_route=execution_route,
    )

    assert response.status == "error"
    assert response.data is None
    assert response.error is not None
    assert response.error.code == "SYSTEM_RUNTIME_ROUTE_INCOMPATIBLE"


def test_validate_runtime_configuration_does_not_expose_submitted_values():
    response = validate_runtime_configuration(
        runtime_profile="private-profile-value",
        execution_route="private-route-value",
    )

    serialized = str(response.model_dump(mode="json"))
    assert "private-profile-value" not in serialized
    assert "private-route-value" not in serialized

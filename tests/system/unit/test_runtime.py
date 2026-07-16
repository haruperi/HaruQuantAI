from itertools import product

import pytest
from app.runtime import RuntimeConfigurationError, validate_runtime_configuration

_COMPATIBLE_PAIRS = (
    ("research", "none"),
    ("simulation", "sim"),
    ("paper", "paper"),
    ("live", "live"),
)
_PROFILES = tuple(profile for profile, _ in _COMPATIBLE_PAIRS)
_ROUTES = tuple(route for _, route in _COMPATIBLE_PAIRS)


@pytest.mark.parametrize(("runtime_profile", "execution_route"), _COMPATIBLE_PAIRS)
def test_validate_runtime_configuration_accepts_compatible_pair(
    runtime_profile,
    execution_route,
):
    assert (
        validate_runtime_configuration(
            runtime_profile=runtime_profile,
            execution_route=execution_route,
        )
        is None
    )


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
    with pytest.raises(RuntimeConfigurationError) as exc_info:
        validate_runtime_configuration(
            runtime_profile=runtime_profile,
            execution_route=execution_route,
        )

    assert exc_info.value.code == "SYSTEM_RUNTIME_ROUTE_INCOMPATIBLE"
    assert str(exc_info.value) == "Runtime profile and execution route are incompatible"


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
    with pytest.raises(RuntimeConfigurationError):
        validate_runtime_configuration(
            runtime_profile=runtime_profile,
            execution_route=execution_route,
        )

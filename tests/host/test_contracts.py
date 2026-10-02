"""Clock contract validation rejects ambiguous authority before publication."""

import pytest
from app.host.contracts import ClockPolicy, OperationRejectedError
from pydantic import ValidationError


def policy_values() -> dict[str, object]:
    """Return explicit synthetic UTC semantics, not a live broker assertion."""
    return {
        "revision": 1,
        "effective_from_utc": "2026-01-01T00:00:00Z",
        "effective_to_utc": "2027-01-01T00:00:00Z",
        "standard_offset_minutes": 120,
        "initial_offset_minutes": 120,
        "assessed_at": "2026-10-02T00:00:00Z",
        "limitations": "Synthetic test policy only",
    }


def test_operation_rejection_requires_bounded_public_contract() -> None:
    rejection = OperationRejectedError(
        "CLOCK_SCHEMA_REQUIRED", "Clock setup required", status=409
    )
    assert rejection.code == "CLOCK_SCHEMA_REQUIRED"
    assert rejection.status == 409
    assert str(rejection) == "Clock setup required"
    for code, message, status in [
        ("unsafe/code", "Safe", 409),
        ("OK", "", 422),
        ("OK", "Safe", 200),
        ("OK", "x" * 501, 422),
    ]:
        with pytest.raises(ValueError, match="Invalid operation rejection"):
            OperationRejectedError(code, message, status=status)


@pytest.mark.parametrize(
    "change",
    [
        {"effective_from_utc": "2026-01-01T00:00:00"},
        {"effective_to_utc": "2025-01-01T00:00:00Z"},
        {"verified": True},
        {"standard_offset_minutes": True},
        {"dst_rule": "iana"},
        {"dst_increment_minutes": 60},
        {"initial_offset_minutes": 180},
    ],
)
def test_clock_policy_rejects_inconsistent_authority(change: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        ClockPolicy.model_validate({**policy_values(), **change})


def test_clock_policy_is_immutable_and_schema_describes_coverage() -> None:
    policy = ClockPolicy.model_validate(policy_values())
    with pytest.raises(ValidationError):
        policy.revision = 2
    assert "effective_from_utc" in ClockPolicy.model_json_schema()["required"]
    assert isinstance(policy.transitions, tuple)

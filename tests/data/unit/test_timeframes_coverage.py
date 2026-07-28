"""Unit tests for time_sessions/timeframes.py to reach >80% coverage."""

from app.services.data.contracts.responses import unwrap_data_response
from app.services.data.time_sessions.timeframes import (
    TIMEFRAME_MANIFEST,
    get_timeframe_spec,
    validate_resample_target,
)


def _unwrap(response: object) -> object:
    """Unwrap a successful Data standard response to its raw payload."""
    return unwrap_data_response(
        response,  # type: ignore[arg-type]
        operation="data.time_sessions.test",
        request_id="req-00000000-0000-4000-8000-000000000000",
    )


def test_get_timeframe_spec_supported() -> None:
    """Test get_timeframe_spec returns the matching spec for a valid key."""
    assert _unwrap(get_timeframe_spec("H1")) is TIMEFRAME_MANIFEST["H1"]


def test_get_timeframe_spec_unsupported() -> None:
    """Test get_timeframe_spec returns UNSUPPORTED_TIMEFRAME for an invalid key."""
    response = get_timeframe_spec("INVALID_TF")
    assert response.status == "error"
    assert response.error is not None
    assert response.error.code == "UNSUPPORTED_TIMEFRAME"


def test_validate_resample_target_none_source() -> None:
    """validate_resample_target returns VALIDATION_FAILED when source_key is None."""
    response = validate_resample_target(None, "H1")
    assert response.status == "error"
    assert response.error is not None
    assert response.error.code == "VALIDATION_FAILED"


def test_validate_resample_target_lower_or_equal_target() -> None:
    """validate_resample_target returns VALIDATION_FAILED when target <= source rank."""
    response = validate_resample_target("H1", "M15")
    assert response.status == "error"
    assert response.error is not None
    assert response.error.code == "VALIDATION_FAILED"

    response_equal = validate_resample_target("H1", "H1")
    assert response_equal.status == "error"
    assert response_equal.error is not None
    assert response_equal.error.code == "VALIDATION_FAILED"


def test_validate_resample_target_success() -> None:
    """validate_resample_target carries None on a valid up-sampling target."""
    assert _unwrap(validate_resample_target("M15", "H1")) is None

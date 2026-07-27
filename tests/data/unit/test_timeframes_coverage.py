"""Unit tests for time_sessions/timeframes.py to reach >80% coverage."""

import pytest
from app.services.data.contracts import DataError
from app.services.data.time_sessions.timeframes import (
    get_timeframe_spec,
    validate_resample_target,
)


def test_get_timeframe_spec_unsupported() -> None:
    """Test get_timeframe_spec raises UNSUPPORTED_TIMEFRAME for invalid key."""
    with pytest.raises(DataError) as exc_info:
        get_timeframe_spec("INVALID_TF")
    assert exc_info.value.code == "UNSUPPORTED_TIMEFRAME"


def test_validate_resample_target_none_source() -> None:
    """
    Test validate_resample_target raises VALIDATION_FAILED when source_key is None.
    """
    with pytest.raises(DataError) as exc_info:
        validate_resample_target(None, "H1")
    assert exc_info.value.code == "VALIDATION_FAILED"


def test_validate_resample_target_lower_or_equal_target() -> None:
    """
    Test validate_resample_target raises VALIDATION_FAILED when target <= source rank.
    """
    with pytest.raises(DataError) as exc_info:
        validate_resample_target("H1", "M15")
    assert exc_info.value.code == "VALIDATION_FAILED"

    with pytest.raises(DataError) as exc_info:
        validate_resample_target("H1", "H1")
    assert exc_info.value.code == "VALIDATION_FAILED"

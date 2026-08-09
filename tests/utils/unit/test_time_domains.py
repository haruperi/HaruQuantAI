"""Unit tests for time domains."""

from datetime import UTC, datetime

import pytest
from app.utils import build_time_stamp, compare_time_stamps
from app.utils.errors.exceptions import ValidationError


def test_cross_domain_comparison_is_rejected() -> None:
    instant = datetime(2026, 1, 1, tzinfo=UTC)
    with pytest.raises(ValidationError):
        compare_time_stamps(
            build_time_stamp(domain="FILL", instant=instant),
            build_time_stamp(domain="REPORT", instant=instant),
        )

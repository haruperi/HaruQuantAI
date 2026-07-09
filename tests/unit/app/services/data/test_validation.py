# ruff: noqa: D, ANN, S101, BLE001
"""Unit tests for the data validation routines."""

from unittest.mock import patch

import pytest
from app.services.data.validation import (
    normalize_numeric,
    register_license,
    validate_license,
    validate_limit,
    validate_step_alignment,
    validate_timeframe,
    validate_timezone,
)
from app.utils.errors import ValidationError


def test_validate_limit_bounds() -> None:
    # Test valid limit returns limit
    assert validate_limit(50, max_allowed=100, default_value=10) == 50
    # Test None limit returns default value
    assert validate_limit(None, max_allowed=100, default_value=10) == 10

    # Non-positive limit
    with pytest.raises(ValidationError, match="positive"):
        validate_limit(0, max_allowed=100, default_value=10)

    # Exceeds max allowed
    with pytest.raises(ValidationError, match="exceeds maximum"):
        validate_limit(101, max_allowed=100, default_value=10)


def test_normalize_numeric_cases() -> None:
    # Value cannot be None
    with pytest.raises(ValidationError, match="cannot be None"):
        normalize_numeric(None, digits=2, workflow_context="research")  # type: ignore[arg-type]

    # Invalid conversion
    with pytest.raises(ValidationError, match="Failed to convert"):
        normalize_numeric("invalid_num", digits=2, workflow_context="research")

    # Quantize behavior
    assert normalize_numeric(1.234, digits=2, workflow_context="research") == 1.23
    assert normalize_numeric(1.234, digits=2, workflow_context="backtest") == "1.23"


def test_validate_step_alignment_cases() -> None:
    # Missing parameters
    with pytest.raises(ValidationError, match="must be defined"):
        validate_step_alignment(None, 0.01, "research")  # type: ignore[arg-type]

    # Invalid conversion
    with pytest.raises(ValidationError, match="Invalid numeric/step conversion"):
        validate_step_alignment("abc", 0.01, "research")

    # Valid step alignment does not raise
    validate_step_alignment(0.10, 0.01, "research")
    validate_step_alignment(0.10, 0.01, "execution_bound")


def test_validate_timeframe_cases() -> None:
    # Empty
    with pytest.raises(ValidationError, match="cannot be empty"):
        validate_timeframe("")

    # Unsupported
    with pytest.raises(ValidationError, match="Unsupported timeframe"):
        validate_timeframe("invalid_tf")

    # Valid
    assert validate_timeframe("m5") == "M5"


def test_validate_timezone_cases() -> None:
    # Invalid timezone
    with pytest.raises(ValidationError, match="Invalid timezone"):
        validate_timezone("invalid_tz")

    # Valid
    assert validate_timezone("UTC") == "UTC"


def test_licensing_database_operations() -> None:
    source = "test_source"
    symbol = "BTCUSD"

    # Register and validate
    register_license(source, symbol, "commercial", redistribution_restricted=False)
    lic = validate_license(source, symbol, "research")
    assert lic["license_type"] == "commercial"
    assert lic["redistribution_restricted"] is False

    # redistribution restricted workflow context rejection
    register_license(source, symbol, "commercial", redistribution_restricted=True)
    with pytest.raises(ValidationError, match="Redistribution limits"):
        validate_license(source, symbol, "risk")

    # Missing license metadata
    with pytest.raises(ValidationError, match="LICENSE_RESTRICTION"):
        validate_license("non_existent_source", "XYZUSD", "research")

    # Database exceptions paths
    with patch("app.services.data.storage.db_helper.get_connection") as mock_conn:
        mock_conn.side_effect = Exception("DB Fail")
        with pytest.raises(ValidationError, match="Failed to register"):
            register_license(
                source, symbol, "commercial", redistribution_restricted=True
            )

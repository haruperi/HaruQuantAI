"""Unit tests for the Indicators Core MVP error catalogue and exception."""

import pytest
from app.services.indicators.core.errors import IndicatorError, IndicatorErrorCode

_EXPECTED_CODES = {
    "IND_INVALID_CONFIG",
    "IND_INVALID_PARAMETER",
    "IND_UNSUPPORTED_INDICATOR",
    "IND_UNSUPPORTED_TIMEFRAME",
    "IND_UNSUPPORTED_DTYPE",
    "IND_INVALID_INPUT_SCHEMA",
    "IND_MISSING_REQUIRED_COLUMN",
    "IND_INVALID_OUTPUT_COLUMN",
    "IND_OUTPUT_COLUMN_CONFLICT",
    "IND_INVALID_OUTPUT_MODE",
    "IND_INPUT_MUTATION_DETECTED",
    "IND_DUPLICATE_TIMESTAMP",
    "IND_NON_MONOTONIC_TIME",
    "IND_AMBIGUOUS_TIMESTAMP",
    "IND_INVALID_TIMEZONE",
    "IND_INVALID_OHLC",
    "IND_INSUFFICIENT_DATA",
    "IND_LOOKAHEAD_RISK",
    "IND_FORMULA_VERSION_MISMATCH",
    "IND_RESOURCE_LIMIT_EXCEEDED",
    "IND_PARTIAL_RESULT",
    "IND_INTERNAL_ERROR",
}


def test_error_code_catalog_contains_only_core_codes() -> None:
    """FR-INDI-001: the catalogue contains exactly the 22 approved codes."""
    codes = {member.value for member in IndicatorErrorCode}
    assert codes == _EXPECTED_CODES
    assert len(IndicatorErrorCode) == len(_EXPECTED_CODES)


def test_indicator_error_serializes_redacted_details() -> None:
    """FR-INDI-002: details are redacted, bounded, and immutable."""
    error = IndicatorError(
        IndicatorErrorCode.IND_INVALID_PARAMETER,
        "period must be at least 2",
        {"period": -1, "note": "password=abc123"},
    )
    assert error.code is IndicatorErrorCode.IND_INVALID_PARAMETER
    assert error.message == "period must be at least 2"
    assert error.details["period"] == -1
    assert "abc123" not in error.details["note"]
    with pytest.raises(TypeError):
        error.details["period"] = 5  # type: ignore[index]


def test_indicator_error_rejects_empty_message() -> None:
    """FR-INDI-002: a blank message is rejected."""
    with pytest.raises(ValueError, match="non-empty"):
        IndicatorError(IndicatorErrorCode.IND_INTERNAL_ERROR, "   ")


def test_indicator_error_rejects_oversized_message() -> None:
    """FR-INDI-002: an over-length message is rejected."""
    with pytest.raises(ValueError, match="maximum length"):
        IndicatorError(IndicatorErrorCode.IND_INTERNAL_ERROR, "x" * 257)


def test_indicator_error_rejects_oversized_details() -> None:
    """FR-INDI-002: more than 16 detail keys is rejected."""
    with pytest.raises(ValueError, match="maximum key count"):
        IndicatorError(
            IndicatorErrorCode.IND_INTERNAL_ERROR,
            "too many details",
            {f"key_{i}": i for i in range(17)},
        )


def test_indicator_error_rejects_non_snake_case_key() -> None:
    """FR-INDI-002: a non-lowercase-snake-case key is rejected."""
    with pytest.raises(ValueError, match="snake_case"):
        IndicatorError(IndicatorErrorCode.IND_INTERNAL_ERROR, "bad key", {"BadKey": 1})


def test_indicator_error_rejects_unsupported_value_type() -> None:
    """FR-INDI-002: a nested mapping value is rejected as unsafe."""
    with pytest.raises(TypeError):
        IndicatorError(
            IndicatorErrorCode.IND_INTERNAL_ERROR,
            "bad value",
            {"payload": {"nested": 1}},
        )


def test_indicator_error_rejects_non_finite_float() -> None:
    """FR-INDI-002: a non-finite float detail value is rejected."""
    with pytest.raises(ValueError, match="finite"):
        IndicatorError(
            IndicatorErrorCode.IND_INTERNAL_ERROR,
            "bad float",
            {"value": float("nan")},
        )


def test_indicator_error_accepts_bounded_scalar_tuple() -> None:
    """FR-INDI-002: a tuple of scalars within bounds is accepted."""
    error = IndicatorError(
        IndicatorErrorCode.IND_INVALID_OUTPUT_COLUMN,
        "unexpected columns",
        {"columns": ("open", "high", "low")},
    )
    assert error.details["columns"] == ("open", "high", "low")


def test_indicator_error_rejects_oversized_tuple() -> None:
    """FR-INDI-002: a scalar tuple exceeding 20 items is rejected."""
    with pytest.raises(ValueError, match="maximum item count"):
        IndicatorError(
            IndicatorErrorCode.IND_INTERNAL_ERROR,
            "too many items",
            {"columns": tuple(range(21))},
        )

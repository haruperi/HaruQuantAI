"""Public Indicators error-boundary tests."""

from app.services.indicators import build_indicator_config, get_indicator, sma
from app.services.indicators.core.error_catalog import INDICATOR_ERROR_CATALOG
from app.utils import validate_error_catalog

from tests.indicators.helpers import assert_error, build_dataset


def test_indicator_error_catalog_matches_current_utils_contract() -> None:
    """Every Indicators error definition passes the public Utils validator."""
    assert validate_error_catalog(INDICATOR_ERROR_CATALOG) == INDICATOR_ERROR_CATALOG


def test_error_catalog_is_exposed_as_safe_response_codes() -> None:
    """FR-INDI-001: unknown identifiers use the approved symbolic code."""
    assert_error(get_indicator("unknown_indicator"), "IND_UNSUPPORTED_INDICATOR")


def test_invalid_parameter_response_is_redacted() -> None:
    """FR-INDI-002: public failures contain safe bounded details only."""
    failure = sma(build_dataset([(1, 2, 0, 1, 10)]), period=1)
    assert_error(failure, "IND_INVALID_PARAMETER")
    assert failure.error is not None
    assert len(failure.message) <= 256
    assert "records" not in str(failure.error.details)


def test_invalid_configuration_fails_closed() -> None:
    """Invalid configuration is reported through the StandardResponse envelope."""
    config = build_indicator_config(
        indicator_id="sma",
        parameters=(("period", 1),),
        source="close",
        formula_version="1.0.0",
    )
    failure = sma(build_dataset([(1, 2, 0, 1, 10)]), period=1, config=config)
    assert_error(failure, "IND_INVALID_PARAMETER")


def test_unexpected_public_failure_is_redacted_and_fails_closed() -> None:
    """Unexpected exceptions become a bounded internal-error response."""
    failure = get_indicator([])  # type: ignore[arg-type]
    assert_error(failure, "IND_INTERNAL_ERROR")
    assert failure.error is not None
    assert failure.error.details["failure_type"] == "TypeError"
    assert "[]" not in failure.message


def test_oversized_error_detail_fails_closed_without_echoing_input() -> None:
    """Oversized diagnostic input is replaced by a safe internal error."""
    oversized_identifier = "x" * 300
    failure = get_indicator(oversized_identifier)
    assert_error(failure, "IND_INTERNAL_ERROR")
    assert oversized_identifier not in failure.message

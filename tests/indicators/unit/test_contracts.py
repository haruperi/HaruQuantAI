"""Public Indicators Core contract tests."""

from app.services.indicators import (
    build_indicator_config,
    get_indicator,
    get_warmup_requirement,
    list_indicators,
)

from tests.indicators.helpers import assert_error, unwrap_response


def _config():
    """Build one canonical public configuration."""
    return build_indicator_config(
        indicator_id="sma",
        parameters=(("period", 2),),
        source="close",
        formula_version="1.0.0",
        output_mode="values",
        column_conflict_policy="error",
        precision_dtype="float64",
        availability_policy="source_available_at",
        quality_policy="propagate_dataset",
        error_mode="raise",
    )


def test_config_is_immutable_and_core_only() -> None:
    """FR-INDI-003: the public builder returns the calculation contract."""
    config = _config()
    assert config.indicator_id == "sma"
    assert config.parameters == (("period", 2),)


def test_registry_spec_contains_required_public_metadata() -> None:
    """FR-INDI-004: official metadata is available through the root function."""
    spec = unwrap_response(get_indicator("sma"))
    assert spec.indicator_id == "sma"
    assert spec.formula_version == "1.0.0"
    assert spec.import_path


def test_get_warmup_requirement_resolves_official_policy() -> None:
    """FR-INDI-005: warmup requirements are resolved without data access."""
    requirement = unwrap_response(get_warmup_requirement("sma", _config()))
    assert requirement.indicator_id == "sma"
    assert requirement.minimum_observations == 2


def test_list_indicators_is_stable() -> None:
    """FR-INDI-011/012: registry discovery is stable and immutable."""
    first = unwrap_response(list_indicators())
    second = unwrap_response(list_indicators())
    assert first == second
    assert isinstance(first, tuple)


def test_config_validation_uses_the_public_boundary() -> None:
    """Invalid public configuration fails with the catalogue error."""
    response = get_warmup_requirement(
        "macd",
        build_indicator_config(
            indicator_id="macd",
            parameters=(),
            source="close",
            formula_version="1.0.0",
        ),
    )
    assert_error(response, "IND_UNSUPPORTED_INDICATOR")

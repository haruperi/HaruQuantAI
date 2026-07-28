"""Unit tests for the Indicators Core immutable calculation contracts."""

import dataclasses
from typing import cast

import pytest
from app.services.indicators import (
    get_warmup_requirement,
)
from app.services.indicators.core.contracts import (
    IndicatorConfig,
    IndicatorProtocol,
    IndicatorSpec,
    WarmupRequirement,
)
from app.utils import StandardResponse

from tests.indicators.helpers import assert_error, unwrap_response


def _config() -> IndicatorConfig:
    """Build one canonical example ``IndicatorConfig``."""
    return IndicatorConfig(
        indicator_id="sma",
        parameters=(("period", 14),),
        source="close",
        formula_version="1.0.0",
        output_mode="values",
        column_conflict_policy="error",
        precision_dtype="float64",
        availability_policy="source_available_at",
        quality_policy="propagate_dataset",
        error_mode="raise",
    )


def test_indicator_config_is_immutable_and_core_only() -> None:
    """FR-INDI-003: IndicatorConfig is frozen and carries only Core fields."""
    config = _config()
    assert config.indicator_id == "sma"
    assert config.parameters == (("period", 14),)
    assert dataclasses.is_dataclass(config)
    field_names = {field.name for field in dataclasses.fields(config)}
    assert field_names == {
        "indicator_id",
        "parameters",
        "source",
        "formula_version",
        "output_mode",
        "column_conflict_policy",
        "precision_dtype",
        "availability_policy",
        "quality_policy",
        "error_mode",
    }
    with pytest.raises(dataclasses.FrozenInstanceError):
        config.indicator_id = "ema"  # type: ignore[misc]


def test_indicator_spec_contains_required_public_metadata() -> None:
    """FR-INDI-004: IndicatorSpec exposes the exact required public fields."""
    spec = IndicatorSpec(
        indicator_id="sma",
        name="Simple Moving Average",
        indicator_version="1.0.0",
        formula_version="1.0.0",
        tier="core_mvp",
        required_columns=("source",),
        parameter_schema={
            "period": {
                "type": "integer",
                "minimum": 2,
                "maximum": 1_000_000,
                "required": True,
                "default": None,
            }
        },
        output_templates=("sma_{period}", "sma_{source}_{period}"),
        warmup_policy="period",
        vectorized=True,
        multi_symbol=False,
        multi_timeframe=False,
        import_path="app.services.indicators.trend.sma:sma",
        stability="stable",
        workflow_eligibility=(
            "WF-INDI-001",
            "WF-INDI-002",
            "WF-INDI-003",
            "WF-INDI-004",
        ),
    )
    assert spec.tier == "core_mvp"
    assert spec.vectorized is True
    assert spec.multi_symbol is False
    assert spec.multi_timeframe is False
    assert spec.output_templates[0] == "sma_{period}"
    with pytest.raises(dataclasses.FrozenInstanceError):
        spec.name = "changed"  # type: ignore[misc]


def test_warmup_requirement_is_deterministic() -> None:
    """FR-INDI-005: WarmupRequirement is deterministic and fetches no data."""
    requirement = WarmupRequirement(
        indicator_id="sma",
        formula_version="1.0.0",
        minimum_observations=14,
        source_timeframe=None,
        required_columns=("source",),
        availability_basis="source_available_at",
    )
    same_requirement = WarmupRequirement(
        indicator_id="sma",
        formula_version="1.0.0",
        minimum_observations=14,
        source_timeframe=None,
        required_columns=("source",),
        availability_basis="source_available_at",
    )
    assert requirement == same_requirement
    with pytest.raises(dataclasses.FrozenInstanceError):
        requirement.minimum_observations = 20  # type: ignore[misc]


@pytest.mark.parametrize(
    ("indicator_id", "parameters", "source", "minimum", "timeframe", "columns"),
    [
        ("adx", (("period", 14),), None, 28, None, ("high", "low", "close")),
        ("adr", (("period", 14),), None, 14, "D1", ("high", "low")),
        ("atr", (("period", 14),), None, 14, None, ("high", "low", "close")),
        (
            "bollinger_bands",
            (("period", 5), ("std_dev", 2.0)),
            None,
            5,
            None,
            ("close",),
        ),
        ("cmf", (("period", 5),), None, 5, None, ("high", "low", "close", "volume")),
        (
            "doji",
            (("threshold", 0.1),),
            None,
            1,
            None,
            ("open", "high", "low", "close"),
        ),
        ("ema", (("period", 5),), "close", 5, None, ("close",)),
        ("engulfing", (), None, 2, None, ("open", "close")),
        ("hull_ma", (("period", 16),), "close", 19, None, ("close",)),
        ("inside_bar", (), None, 2, None, ("high", "low")),
        ("mfi", (("period", 5),), None, 5, None, ("high", "low", "close", "volume")),
        ("obv", (), None, 1, None, ("close", "volume")),
        ("pinbar", (), None, 1, None, ("open", "high", "low", "close")),
        (
            "price_volume_distribution",
            (("bins", 3), ("period", 5)),
            None,
            5,
            None,
            ("high", "low", "close", "volume"),
        ),
        ("rolling_volatility", (("period", 5),), "open", 6, None, ("open",)),
        ("rsi", (("period", 14),), "close", 15, None, ("close",)),
        ("sma", (("period", 5),), "close", 5, None, ("close",)),
        ("standard_deviation", (("period", 5),), "close", 5, None, ("close",)),
        ("williams_r", (("period", 14),), None, 14, None, ("high", "low", "close")),
        ("wma", (("period", 5),), "close", 5, None, ("close",)),
    ],
)
def test_get_warmup_requirement_resolves_every_official_policy(
    indicator_id: str,
    parameters: tuple[tuple[str, int | float], ...],
    source: str | None,
    minimum: int,
    timeframe: str | None,
    columns: tuple[str, ...],
) -> None:
    """FR-INDI-005: resolve exact formula-specific normalized history."""
    config = IndicatorConfig(
        indicator_id=indicator_id,
        parameters=parameters,
        source=source,
        formula_version="1.0.0",
        output_mode="values",
        column_conflict_policy="error",
        precision_dtype="float64",
        availability_policy="source_available_at",
        quality_policy="propagate_dataset",
        error_mode="raise",
    )

    requirement = unwrap_response(get_warmup_requirement(indicator_id, config))

    assert requirement.minimum_observations == minimum
    assert requirement.source_timeframe == timeframe
    assert requirement.required_columns == columns


def test_get_warmup_requirement_rejects_config_identity_mismatch() -> None:
    """FR-INDI-005: invalid candidate configuration fails closed."""
    assert_error(get_warmup_requirement("ema", _config()), "IND_INVALID_CONFIG")


class _StubCalculator:
    """Minimal stand-in satisfying ``IndicatorProtocol`` structurally."""

    def calculate(
        self, _data: object, _config: IndicatorConfig
    ) -> StandardResponse[object]:
        """Return a placeholder result for protocol-conformance testing."""
        return cast("StandardResponse[object]", object())


def test_official_calculator_satisfies_indicator_protocol() -> None:
    """FR-INDI-006: a compatible calculator structurally satisfies the protocol."""
    calculator = _StubCalculator()
    assert isinstance(calculator, IndicatorProtocol)

    class _Incompatible:
        """Stand-in with no ``calculate`` method."""

    assert not isinstance(_Incompatible(), IndicatorProtocol)

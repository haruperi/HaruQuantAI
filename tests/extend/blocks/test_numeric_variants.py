"""Donor-executed numeric references and canonical projection qualification."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest
from app.core.trading.blocks.registry import BlockRegistry, BlockRegistryError
from app.core.trading.blocks.series import BarData
from app.extend.blocks.indicators.price_action.highest_lowest import HighestLowest
from app.extend.blocks.indicators.volatility.bar_range import BarRange
from app.extend.blocks.indicators.volatility.bb_range import BBRange
from app.extend.blocks.indicators.volatility.bb_width_ratio import BBWidthRatio
from app.extend.blocks.indicators.volatility.biggest_range import BiggestRange
from app.extend.blocks.indicators.volatility.highest_in_range import HighestInRange
from app.extend.blocks.indicators.volatility.lowest_in_range import LowestInRange
from app.extend.blocks.indicators.volatility.smallest_range import SmallestRange
from pydantic import ValidationError

REFERENCE = json.loads(
    Path("docs/dev/fixtures/numeric-variants-donor-reference.json").read_text()
)
TYPES = {
    cls.__name__: cls
    for cls in (
        BarRange,
        BiggestRange,
        SmallestRange,
        HighestInRange,
        LowestInRange,
        BBRange,
        BBWidthRatio,
    )
}
PROJECTIONS = {
    "Highest": "highest",
    "Lowest": "lowest",
    "HighestIndex": "highest_index",
    "LowestIndex": "lowest_index",
}


@pytest.fixture(autouse=True)
def quiet_reference_replays(monkeypatch):
    """Avoid enqueuing thousands of informational events during fixture replays."""
    import importlib

    for module in ("bar_range",):
        logger = importlib.import_module(
            "app.extend.blocks.indicators.volatility." + module
        ).logger
        monkeypatch.setattr(logger, "info", lambda *args, **kwargs: None)
    module = importlib.import_module(
        "app.extend.blocks.indicators.price_action.highest_lowest"
    )
    monkeypatch.setattr(module.logger, "info", lambda *args, **kwargs: None)


def bars(case, count=None):
    rows = np.asarray(REFERENCE["datasets"][case["dataset"]][:count], dtype=float)
    return BarData.from_arrays(
        **dict(zip(("timestamps", "open", "high", "low", "close"), rows.T, strict=True))
    )


@pytest.mark.parametrize("case", REFERENCE["cases"], ids=lambda c: c["id"])
def test_numeric_outputs_against_executed_donor(case):
    name = case["block"].split("/")[-1]
    cls = TYPES.get(name, HighestLowest)
    parameters = {} if name == "BarRange" else case["parameters"]
    indicator = cls(**parameters)
    port = PROJECTIONS.get(name, "value")
    result = indicator.calculate(bars(case))[port].values
    np.testing.assert_allclose(result, case["expected"], rtol=2e-14, atol=1e-12)
    for count in (1, 3, len(result) - 1):
        prefix = indicator.calculate(bars(case, count))[port].values
        np.testing.assert_array_equal(result[:count], prefix)


def test_range_variants_are_numeric_not_current_bar_predicates():
    context = BarData.from_arrays(high=[10.0, 12.0, 11.0], low=[9.0, 8.0, 9.0])
    np.testing.assert_array_equal(
        BiggestRange(period=2).calculate(context)["value"].values, [1.0, 4.0, 4.0]
    )
    np.testing.assert_array_equal(
        SmallestRange(period=2).calculate(context)["value"].values, [1.0, 1.0, 2.0]
    )
    assert BiggestRange(period=2).calculate(context)["value"].get(0) == 4.0


def test_width_ratio_has_distinct_startup_and_nonpositive_mean_rule():
    context = BarData.from_arrays(close=[10.0, 12.0])
    width = BBWidthRatio(period=4).calculate(context)["value"].values
    assert width[0] == 0
    assert width[1] == pytest.approx(4 * np.sqrt(2 / 4) / 11)
    np.testing.assert_array_equal(
        BBWidthRatio(period=3)
        .calculate(BarData.from_arrays(close=[0.0, -2.0, 0.0]))["value"]
        .values,
        [0, 0, 0],
    )


def test_strict_parameters_real_price_inputs_and_no_time_window_shims():
    for cls in (HighestInRange, LowestInRange):
        for kwargs in (
            {"time_from": 1260},
            {"time_to": 2400},
            {"timezone": "not/a/zone"},
        ):
            with pytest.raises(ValidationError):
                cls(**kwargs)
        with pytest.raises(ValueError, match="timestamps"):
            cls().calculate(BarData.from_arrays(high=[2.0], low=[1.0]))
    assert not hasattr(BarRange, "highest_in_range")
    assert not hasattr(BarRange, "lowest_in_range")
    for cls in (BBRange, BBWidthRatio):
        with pytest.raises(ValueError, match="open"):
            cls(computed_from=1).calculate(BarData.from_arrays(close=[1.0, 2.0]))
        with pytest.raises(ValidationError):
            cls(computed_from=7)
    registry = BlockRegistry()
    for cls in (
        BiggestRange,
        SmallestRange,
        HighestInRange,
        LowestInRange,
        BBRange,
        BBWidthRatio,
    ):
        descriptor = registry.register_block(
            cls, cls.__module__.replace(".", "/") + ".py"
        )
        with pytest.raises(BlockRegistryError):
            descriptor.instantiate(unknown=True)
        with pytest.raises(ValidationError):
            cls(period="3")


def test_catalog_projection_routes_and_selector_dependencies():
    from app.core.trading.blocks.composition import (
        CompositionSpec,
        bind_composition,
        composition_manifest,
    )

    registry = BlockRegistry()
    registry.discover("app/extend/blocks")
    assert not registry.diagnostics
    mappings = {
        row["name"]: row
        for row in composition_manifest()["mappings"]
        if row["status"] in ("output_projection", "calculation_mapping")
    }
    for cls in (
        BiggestRange,
        SmallestRange,
        HighestInRange,
        LowestInRange,
        BBRange,
        BBWidthRatio,
    ):
        row = mappings[cls.__name__]
        assert row["target_id"] == cls.spec.id
        assert row["output"] == "value"
        assert registry.require(row["target_id"]).instantiate().spec.id == cls.spec.id
    for name, port in PROJECTIONS.items():
        assert mappings[name]["target_id"] == HighestLowest.spec.id
        assert mappings[name]["output"] == port
    for name in ("EMA", "SMA", "LWMA", "SMMA", "TEMA"):
        assert mappings[name]["target_ids"] == ("indicator.trend." + name.lower(),)
    dispatch = mappings["MovingAverage"]["dispatch"]["targets"]
    assert tuple(dispatch.values()) == tuple(
        "indicator.trend." + name for name in ("sma", "ema", "smma", "lwma")
    )
    assert not mappings["MovingAverage"]["generation_eligible"]

    definition = CompositionSpec(
        "signal.test.numeric_inputs",
        "Numeric input selection",
        "test",
        BBRange.spec.id,
        {
            "nodes": {
                "i0": {
                    "indicator": BBRange.spec.id,
                    "parameters": {
                        "period": ["constant", 3],
                        "computed_from": ["parameter", "computed_from"],
                    },
                }
            },
            "expression": [
                "comparison",
                "condition.is_greater",
                ["output", "i0", "value", 0, None],
                ["constant", 0.0],
            ],
            "parameters": {
                "computed_from": {
                    "type": "integer",
                    "default": 0,
                    "minimum": 0,
                    "maximum": 6,
                }
            },
        },
    )
    executor, _, _ = bind_composition(definition, BBRange)
    assert executor.required_inputs(computed_from=1) == ("open",)
    assert executor.required_inputs(computed_from=5) == ("close", "high", "low")
    assert executor(BarData.from_arrays(open=[1.0, 3.0, 2.0]), computed_from=1)
    with pytest.raises(ValueError, match="open"):
        executor(BarData.from_arrays(close=[1.0, 3.0, 2.0]), computed_from=1)

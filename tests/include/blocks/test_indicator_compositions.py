"""Executable donor compositions, shared algorithms and catalog publication guarantees."""

from __future__ import annotations

import ast
from dataclasses import replace
from pathlib import Path
from typing import Any

import numpy as np
import pytest
from app.include.blocks.composition import (
    CompositionSpec,
    bind_composition,
    composition_manifest,
)
from app.include.blocks.indicators.momentum.rsi import RSI
from app.include.blocks.registry import BlockRegistry, BlockRegistryError
from app.include.blocks.series import BarData, IndicatorSeries
from pydantic import ValidationError


@pytest.fixture(scope="module")
def catalog():
    registry = BlockRegistry()
    registry.discover("app/include/blocks")
    assert not registry.diagnostics
    return registry.snapshot()


def configuration(descriptor) -> dict[str, Any]:
    schema = descriptor.parameter_schema
    return {
        name: schema["properties"][name].get("minimum", 0.0)
        for name in schema.get("required", ())
    }


def bars(count: int = 320) -> BarData:
    rng = np.random.default_rng(981)
    close = 100 + np.cumsum(rng.normal(0, 0.2, count))
    return BarData.from_arrays(
        open=close - 0.1,
        high=close + 0.4,
        low=close - 0.4,
        close=close,
        volume=np.full(count, 100.0),
        timestamps=np.arange(count, dtype=np.int64) * 60000 + 1700000000000,
        cot_score=close,
        cot_small52=close,
        decision_price=close,
        vp_poc=close + 0.1,
        vp_bull_poc=close,
        vp_bear_poc=close + 0.2,
        vp_delta=np.full(count, 120.0),
    )


def test_every_donor_indicator_and_pattern_has_an_explicit_mapping(catalog) -> None:
    mappings = composition_manifest()["mappings"]
    assert len(mappings) == 508
    assert len({row["donor"] for row in mappings}) == 508
    assert not any(
        row["status"] in ("specialized_review", "blocked_calculation")
        for row in mappings
    )
    for row in mappings:
        if row["status"] in ("composition", "specialized_signal"):
            descriptor = catalog.require(row["id"])
            assert descriptor.source_file.endswith(
                row["owner_id"].split(".")[-1] + ".py"
            ) or row["owner_id"] in (
                "indicator.trend.sma",
                "indicator.trend.parabolic_sar",
                "indicator.price_action.candlestick_patterns",
            )
            if row["status"] == "composition":
                assert "bars" not in descriptor.parameter_schema["properties"]
        elif row["status"] in ("output_projection", "registered_function"):
            descriptor = catalog.require(row["target_id"])
            if row["status"] == "output_projection":
                assert row["output"] in {p.name for p in descriptor.spec.outputs}
        elif row["status"] == "calculation_mapping":
            assert all(target in catalog for target in row["target_ids"])
        else:
            assert row["status"] == "excluded_diagnostic"


def test_all_generic_recipes_execute_with_explicit_inputs(catalog) -> None:
    source = bars()
    for row in composition_manifest()["mappings"]:
        if row["status"] != "composition":
            continue
        descriptor = catalog.require(row["id"])
        configured = descriptor.instantiate(**configuration(descriptor))
        assert isinstance(configured(source), bool), row["donor"]


def test_rsi_turn_and_macd_crossover_are_shared_compositions(catalog) -> None:
    source = bars(3)
    rsi = catalog.require("signal.rsi.rsi_changes_up").target
    assert rsi.evaluate_outputs(
        {"i0": {"value": IndicatorSeries([3.0, 1.0, 2.0])}}, source
    )
    assert not rsi.evaluate_outputs(
        {"i0": {"value": IndicatorSeries([1.0, 1.0, 2.0])}}, source
    )
    macd = catalog.require("signal.macd.macd_main_cross_above_signal").target
    outputs = {
        "i0": {
            "main": IndicatorSeries([0.0, 1.0, 3.0]),
            "signal": IndicatorSeries([2.0, 2.0, 2.0]),
        }
    }
    assert macd.evaluate_outputs(outputs, source)
    outputs["i0"]["main"] = IndicatorSeries([0.0, 2.0, 3.0])
    assert not macd.evaluate_outputs(outputs, source)  # A touch is not a strict cross.


def test_aroon_inclusive_boundary_is_not_replaced_with_strict_cross(catalog) -> None:
    recipe = catalog.require("signal.aroon.aroon_rise_from_bottom").target
    source = bars(2)
    outputs = {
        "i0": {"up": IndicatorSeries([8.0, 9.0]), "down": IndicatorSeries([40.0, 40.0])}
    }
    assert recipe.evaluate_outputs(outputs, source)
    outputs["i0"]["up"] = IndicatorSeries([8.1, 9.0])
    assert not recipe.evaluate_outputs(outputs, source)


def test_bar_open_comparison_uses_previous_band_and_raw_price(catalog) -> None:
    recipe = catalog.require("signal.bollinger_bands.bb_bar_opens_above_up").target
    source = BarData.from_arrays(open=[0.0, 20.0000001])
    outputs = {"i0": {"upper": IndicatorSeries([20.0, 1000.0])}}
    assert recipe.evaluate_outputs(outputs, source)
    # Comparing against today's band or rounding the raw open to six digits fails.
    source = BarData.from_arrays(open=[0.0, 20.0])
    assert not recipe.evaluate_outputs(outputs, source)


def test_explicit_four_digit_read_and_missing_history(catalog) -> None:
    recipe = catalog.require("signal.cci.cci_rising").target
    source = bars(2)
    outputs = {"i0": {"value": IndicatorSeries([1.00001, 1.00002])}}
    assert not recipe.evaluate_outputs(outputs, source)
    assert not recipe.evaluate_outputs(outputs, source, shift=5)
    with pytest.raises(ValueError, match="align"):
        recipe.evaluate_outputs({"i0": {"value": IndicatorSeries([1.0])}}, source)


def test_parameter_and_selector_validation(catalog) -> None:
    descriptor = catalog.require("signal.rsi.rsi_rising")
    for kwargs in ({"shift": -1}, {"shift": True}, {"period": "14"}, {"unknown": 1}):
        with pytest.raises(BlockRegistryError):
            descriptor.instantiate(**kwargs)
    for kwargs in ({"shift": -1}, {"period": "14"}):
        with pytest.raises(ValidationError):
            descriptor.target(bars(), **kwargs)
    with pytest.raises(BlockRegistryError):
        catalog.require("signal.moving_average.ma_rising").instantiate(period=1)
    with pytest.raises(BlockRegistryError):
        catalog.require("signal.parabolic_sar.psar_bar_higher").instantiate(step=0.001)
    with pytest.raises(BlockRegistryError):
        catalog.require("signal.parabolic_sar.psar_bar_higher").instantiate(
            step=0.4, maximum=0.2
        )
    # Stochastic's unimplemented donor smoothing modes are rejected explicitly.
    stochastic = catalog.require("signal.stochastic.stoch_slow_d_rising")
    with pytest.raises(BlockRegistryError):
        stochastic.instantiate(ma_method=1)
    # Donor ADX level default 0 violates its declared lower bound 1: require a value.
    adx = catalog.require("signal.adx.adx_higher")
    with pytest.raises(BlockRegistryError):
        adx.instantiate()
    adx.instantiate(level=20.0)


def test_missing_external_profile_feed_never_uses_rolling_profile(catalog) -> None:
    descriptor = catalog.require("signal.volume_profile.vp_price_above_poc")
    source = BarData.from_arrays(close=[1.0, 2.0])
    with pytest.raises(ValueError, match="vp_poc"):
        descriptor.target(source)
    assert not descriptor.spec.is_generation_eligible


def test_computed_from_is_explicit_and_causal(catalog) -> None:
    recipe = catalog.require("signal.rsi.rsi_rising").target
    with pytest.raises(ValueError, match="high"):
        recipe(BarData.from_arrays(close=[1.0, 2.0]), computed_from=2)
    source = bars(70)
    for count in (40, 50, 60):
        inputs = {
            name: getattr(source, name)[:count]
            for name in ("open", "high", "low", "close", "volume")
        }
        prefix = BarData.from_arrays(**inputs)
        # Same completed bar, expressed as a prefix or a shift into the full batch.
        assert recipe(prefix) == recipe(source, shift=70 - count)


def test_snapshots_freeze_recipe_and_pin_indicator_implementations(tmp_path) -> None:
    path = tmp_path / "rsi.py"
    template = """from typing import ClassVar
from pydantic import Field
from app.include.blocks.indicators.base import BaseIndicator
from app.include.blocks.metadata import BlockSpec, OutputPort
from app.include.blocks.series import IndicatorSeries
class TestRSI(BaseIndicator):
    spec: ClassVar[BlockSpec] = BlockSpec(id="indicator.momentum.rsi", outputs=(OutputPort("value"),))
    period: int = Field(default=14, ge=1)
    def calculate(self, bars):
        return {"value": IndicatorSeries(VALUES)}
"""
    path.write_text(template.replace("VALUES", "[3.0, 2.0, 1.0]"))
    registry = BlockRegistry()
    registry.register_file(path, tmp_path)
    old = registry.snapshot()
    signal_id = "signal.rsi.rsi_rising"
    assert not old.require(signal_id).instantiate()(bars(3))
    path.write_text(template.replace("VALUES", "[1.0, 2.0, 3.0]"))
    registry.register_file(path, tmp_path)
    assert registry.snapshot().require(signal_id).instantiate()(bars(3))
    assert not old.require(signal_id).instantiate()(bars(3))
    target = old.require(signal_id).target
    with pytest.raises(TypeError):
        target.definition.recipe["nodes"]["i0"]["indicator"] = "changed"
    valid = registry.snapshot()
    path.write_text(
        template.replace('OutputPort("value")', 'OutputPort("wrong")').replace(
            "VALUES", "[1.0,2.0,3.0]"
        )
    )
    with pytest.raises(BlockRegistryError):
        registry.register_file(path, tmp_path)
    assert registry.snapshot().require(signal_id) is valid.require(signal_id)


def test_invalid_recipe_is_rejected_before_publication() -> None:
    row = next(
        row for row in composition_manifest()["mappings"] if row["name"] == "RSIRising"
    )
    definition = CompositionSpec(
        row["id"], row["name"], row["donor"], row["owner_id"], row["recipe"]
    )
    bad = dict(row["recipe"])
    bad["expression"] = [
        "comparison",
        "arbitrary.import",
        ["constant", 1],
        ["constant", 2],
    ]
    with pytest.raises(ValueError, match="Unknown comparison"):
        bind_composition(replace(definition, recipe=bad), RSI)


def test_old_indicator_comparison_wrappers_are_removed() -> None:
    from app.include.blocks.indicators.momentum.cci import CCI
    from app.include.blocks.indicators.trend.adx import ADX

    for cls in (ADX, CCI):
        assert not hasattr(cls, "is_rising")
        assert not hasattr(cls, "crosses_above")
    for path in Path("app/include/blocks/indicators").rglob("*.py"):
        for node in ast.walk(ast.parse(path.read_text())):
            if isinstance(node, ast.FunctionDef) and node.name in (
                "is_rising",
                "is_falling",
                "crosses_above",
                "crosses_below",
            ):
                # Remaining named operations must be specialized algorithms, not facades.
                statements = node.body[1:] if ast.get_docstring(node) else node.body
                assert not (
                    len(statements) == 1
                    and isinstance(statements[0], ast.Return)
                    and isinstance(statements[0].value, ast.Call)
                    and isinstance(statements[0].value.func, ast.Name)
                    and statements[0].value.func.id == node.name
                ), str(path)


def test_specialized_signal_bindings_distinguish_maps_from_series(catalog) -> None:
    from app.include.blocks.metadata import PortType

    for row in composition_manifest()["mappings"]:
        if row["status"] != "specialized_signal":
            continue
        descriptor = catalog.require(row["id"])
        inputs = {port.name: port for port in descriptor.spec.inputs}
        assert set(inputs) == set(descriptor.input_bindings)
        for name, binding in descriptor.input_bindings.items():
            if binding["kind"] == "output_map":
                assert inputs[name].port_type == PortType.ANY
        with pytest.raises(TypeError):
            descriptor.input_bindings["new"] = {}


def test_required_history_tracks_configuration_and_offsets(catalog) -> None:
    recipe = catalog.require("signal.rsi.rsi_rising").target
    assert recipe.required_history(period=20, shift=3) == 25
    assert "close" in recipe.required_inputs()
    assert "high" in recipe.required_inputs(computed_from=2)
    assert "close" not in recipe.required_inputs(computed_from=2)

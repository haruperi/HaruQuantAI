"""Qualify every remaining indicator against pre-migration numerical captures."""

from __future__ import annotations

import hashlib
import importlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pytest
from app.extend.blocks.indicators.base import BaseIndicator
from app.extend.blocks.registry import BlockRegistry, BlockRegistryError
from app.extend.blocks.series import BarData
from app.workspace.code_editor._indicator_data import calculate_indicator, output_series
from pydantic import ValidationError

FIXTURES = Path("docs/dev/fixtures")
HISTORICAL_FAMILIES: list[dict[str, Any]] = json.loads(
    (FIXTURES / "phase3-family-baselines.json").read_text(encoding="utf-8")
)
# Rolling profile captures are retained unchanged as historical evidence. Their
# contracts were replaced by donor session qualification in test_profile_sessions.
FAMILIES = [
    entry
    for entry in HISTORICAL_FAMILIES
    if entry["name"] not in {"VolumeProfile", "TPOProfile"}
]


@pytest.fixture(scope="module")
def inputs() -> dict[str, Any]:
    """Load the exact OHLCV and external feeds captured before migration."""
    with np.load(FIXTURES / "phase3-family-inputs.npz") as archive:
        return dict(archive)


def indicator_type(entry: dict[str, Any]) -> type[BaseIndicator]:
    """Import one canonical class without going through a compatibility facade."""
    module = entry["new"].removesuffix(".py").replace("/", ".")
    cls: type[BaseIndicator] = getattr(importlib.import_module(module), entry["name"])
    return cls


def digest(values: Any) -> str:
    """Hash all float64 bytes, normalizing only the NaN payload."""
    array = np.asarray(values, dtype=np.float64).copy()
    array[np.isnan(array)] = np.nan
    return hashlib.sha256(array.tobytes()).hexdigest()


@pytest.mark.parametrize("entry", FAMILIES, ids=lambda e: e["name"])
def test_family_numerical_parity_and_causality(
    entry: dict[str, Any], inputs: dict[str, Any]
) -> None:
    """Preserve every captured output and explicitly classify repainting charts."""
    cls = indicator_type(entry)
    for case in entry["cases"]:
        instance = cls(**case["parameters"])
        bars = BarData.from_arrays(
            **{name: inputs[name] for name in entry["provided_inputs"]}
        )
        result = instance.calculate(bars)
        assert set(result) == set(case["hashes"]) | set(entry.get("added_outputs", []))
        assert set(result) == {port.name for port in instance.spec.outputs}
        for name, series in result.items():
            assert series.values.shape == (320,)
            if name in case["hashes"]:
                assert digest(series.values) == case["hashes"][name]
            else:
                assert np.isnan(series.values).all()
        prefix = instance.calculate(
            BarData.from_arrays(
                **{name: inputs[name][:223] for name in entry["provided_inputs"]}
            )
        )
        causal = all(
            np.array_equal(series.values[:223], prefix[name].values, equal_nan=True)
            for name, series in result.items()
        )
        assert causal == case["causal"]
        assert instance.spec.is_causal == causal
        if not causal:
            assert not instance.spec.is_generation_eligible
        else:
            for count in (17, 75, 319):
                truncated = instance.calculate(
                    BarData.from_arrays(
                        **{
                            name: inputs[name][:count]
                            for name in entry["provided_inputs"]
                        }
                    )
                )
                for name, series in result.items():
                    assert digest(series.values[:count]) == digest(
                        truncated[name].values
                    ), (entry["name"], name, count)
        assert instance.required_history() >= 1


@pytest.mark.parametrize("entry", FAMILIES, ids=lambda e: e["name"])
def test_family_schema_configuration_and_editor_execution(
    entry: dict[str, Any], inputs: dict[str, Any]
) -> None:
    """Use identical typed configuration and named outputs in the editor runner."""
    cls = indicator_type(entry)
    schema = cls.get_parameter_schema()
    assert set(schema["properties"]) == set(entry["cases"][0]["parameters"])
    with pytest.raises(ValidationError):
        cls(unknown_parameter=1)  # type: ignore[call-arg]
    registry = BlockRegistry()
    descriptor = registry.register_block(cls, entry["new"])
    with pytest.raises(BlockRegistryError):
        descriptor.instantiate(unknown_parameter=1)
    for name, model_field in cls.model_fields.items():
        if model_field.annotation is int:
            with pytest.raises(ValidationError):
                cls(**{name: "1"})
    bars = BarData.from_arrays(
        **{name: inputs[name] for name in entry["provided_inputs"]}
    )
    outputs = output_series(calculate_indicator(cls, bars, {}), 320)
    assert set(outputs) == {port.name for port in cls.spec.outputs}


def test_complete_inventory_and_unique_catalog() -> None:
    """All 82 indicator classes have independent files, IDs, and registrations."""
    registry = BlockRegistry()
    registry.discover("app/extend/blocks", authorized_root="app/extend")
    assert registry.diagnostics == []
    indicators = [
        desc for desc in registry.snapshot() if desc.spec.id.startswith("indicator.")
    ]
    assert len(indicators) == 82
    assert len({desc.source_file for desc in indicators}) == 82
    for entry in FAMILIES:
        assert registry.require(entry["id"]).spec.id == entry["id"]
    assert not list(Path("app/include/indicators").rglob("*.py"))


def test_auxiliary_feed_alignment_and_missing_inputs(inputs: dict[str, Any]) -> None:
    """Never substitute market prices for required external positioning feeds."""
    from app.extend.blocks.indicators.volume.cot import COT
    from app.extend.blocks.indicators.volume.cumulative_volume_delta import (
        CumulativeVolumeDelta,
    )

    with pytest.raises(ValueError, match="Missing indicator inputs"):
        COT().calculate(BarData.from_arrays(close=inputs["close"]))
    with pytest.raises(ValueError, match="aligned"):
        BarData.from_arrays(close=inputs["close"], commercial_net=[1.0])
    with pytest.raises(ValueError, match="supplied together"):
        CumulativeVolumeDelta().calculate(
            BarData.from_arrays(
                open=inputs["open"],
                close=inputs["close"],
                volume=inputs["volume"],
                buy_volume=inputs["buy_volume"],
            )
        )


@pytest.mark.parametrize(
    ("name", "parameters"),
    [
        ("Fractal", {"fractal_bars": 4}),
        ("HurstExponent", {"min_scale": 50, "max_scale": 8}),
        ("ChoppinessIndex", {"lower_threshold": 70.0, "upper_threshold": 30.0}),
        ("MarketRegimeResolver", {"chop_lower": 70.0, "chop_upper": 30.0}),
        ("ParabolicSAR", {"step": 0.4, "maximum": 0.2}),
        ("COT", {"period_fast": 200, "period_slow": 100}),
    ],
)
def test_configuration_relationships_fail_before_calculation(
    name: str, parameters: dict[str, Any]
) -> None:
    """Invalid paired settings cannot reach numerical calculation."""
    entry = next(entry for entry in FAMILIES if entry["name"] == name)
    with pytest.raises(ValidationError):
        indicator_type(entry)(**parameters)


def test_optional_price_inputs_preserve_absent_semantics() -> None:
    """Optional opens and lows do not silently turn into zero-valued market data."""
    from app.extend.blocks.indicators.price_action.highest_lowest import HighestLowest
    from app.extend.blocks.indicators.volume.vwap import VWAP

    close = np.array([10.0, 11.0, 12.0, 13.0])
    high, low, volume = close + 3.0, close - 1.0, np.ones(4)
    result = HighestLowest(period=2).calculate(BarData.from_arrays(high=high))
    assert result["lowest"].values[-1] == high[-2]
    bars = BarData.from_arrays(high=high, low=low, close=close, volume=volume)
    value = VWAP(period=2).calculate(bars)["value"].values[-1]
    typical = (high + low + close) / 3.0
    assert value == pytest.approx(typical[-2:].mean())


def test_anchor_indices_accept_json_arrays_and_freeze_configuration() -> None:
    """JSON parameter arrays become immutable, strictly validated anchor indices."""
    from app.extend.blocks.indicators.volume.anchored_vwap import AnchoredVWAP

    parameters: dict[str, Any] = {"anchor_indices": [0, 10]}
    indicator = AnchoredVWAP(**parameters)
    parameters["anchor_indices"].append(20)
    assert indicator.anchor_indices == (0, 10)
    for indices in ([-1], ["1"], [True]):
        with pytest.raises(ValidationError):
            AnchoredVWAP(anchor_indices=indices)  # type: ignore[arg-type]


def test_fibo_declares_stable_custom_output() -> None:
    """Changing an optional level never changes the declared output-port set."""
    from app.extend.blocks.indicators.price_action.fibo import Fibo

    bars = BarData.from_arrays(high=[12.0, 14.0], low=[8.0, 10.0], close=[11.0, 13.0])
    default = Fibo(period=2).calculate(bars)
    configured = Fibo(period=2, custom_level=50.0).calculate(bars)
    assert default.keys() == configured.keys()
    assert np.isnan(default["custom"].values).all()
    np.testing.assert_array_equal(
        configured["custom"].values, configured["level_50_0"].values
    )


def test_fresh_package_import_survives_a_broken_exported_sibling() -> None:
    """Exercise lazy exports without modules cached by pytest collection."""
    source = """
import importlib.abc
import sys

class BrokenSibling(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname == 'app.extend.blocks.indicators.momentum.rsi':
            raise ImportError('broken RSI source')

sys.meta_path.insert(0, BrokenSibling())
from app.extend.blocks.indicators import SMA
assert SMA(period=3).period == 3
try:
    from app.extend.blocks.indicators import RSI
except ImportError:
    pass
else:
    raise AssertionError('RSI import should fail')
from app.extend.blocks.indicators import ATR
assert ATR(period=3).period == 3
"""
    subprocess.run([sys.executable, "-c", source], check=True, capture_output=True)


def test_file_discovery_resolves_types_and_reads_same_size_edits(
    tmp_path: Path,
) -> None:
    """Forward annotations resolve against the loaded module; reload uses fresh source."""
    path = tmp_path / "typed_probe.py"
    source = """from __future__ import annotations
from typing import ClassVar, Literal
from app.extend.blocks.base import BaseBlock
from app.extend.blocks.metadata import BlockSpec
class Probe(BaseBlock):
    spec: ClassVar[BlockSpec] = BlockSpec(id='probe.typed')
    mode: Literal['a', 'b'] = 'a'
"""
    registry = BlockRegistry()
    path.write_text(source, encoding="utf-8")
    registry.register_file(path, authorized_root=tmp_path)
    assert registry.require("probe.typed").instantiate().mode == "a"
    path.write_text(source.replace("= 'a'", "= 'b'"), encoding="utf-8")
    registry.register_file(path, authorized_root=tmp_path)
    assert registry.require("probe.typed").instantiate().mode == "b"
    with pytest.raises(BlockRegistryError):
        registry.require("probe.typed").instantiate(mode="c")

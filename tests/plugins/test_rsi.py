"""Comprehensive golden and unit tests for indicator.rsi plugin."""

import math
from typing import Any

import pytest
from app.plugins.indicators.rsi import (
    OPERATION_ID,
    PARAMETER_PERIOD,
    PLUGIN_REF,
    RsiOperation,
    plugin,
)
from app.plugins.lowering import LoweringContext, LoweringTarget
from app.plugins.schema import (
    FrozenObject,
    MissingValue,
)
from app.plugins.spec import OperationBindings


class _MockBindings(OperationBindings):
    def require(self, token: Any) -> Any:
        raise PermissionError("No capabilities declared")

    def optional(self, token: Any) -> Any:
        return None


class _MockLoweringContext(LoweringContext):
    def __init__(self, target: LoweringTarget) -> None:
        self._target = target
        self._counter = 0

    @property
    def target(self) -> LoweringTarget:
        return self._target

    def allocate_node_id(self, prefix: str = "node") -> str:
        self._counter += 1
        return f"{prefix}_{self._counter}"


def test_rsi_plugin_spec_and_factory() -> None:
    contrib = plugin()
    assert contrib.spec.ref == PLUGIN_REF
    assert contrib.spec.kind == "indicator"
    assert len(contrib.spec.operations) == 1
    op_spec = contrib.spec.operations[0]
    assert op_spec.operation_id == OPERATION_ID
    assert op_spec.parameters.get("period") == PARAMETER_PERIOD


def test_rsi_parameter_validation_and_warmup() -> None:
    op = RsiOperation()
    # Valid
    res = op.validate_parameters(FrozenObject.from_mapping({"period": 14}))
    assert res.is_valid
    assert op.warmup_samples(FrozenObject.from_mapping({"period": 14})) == 14

    # Invalid (below min 2)
    res_bad = op.validate_parameters(FrozenObject.from_mapping({"period": 1}))
    assert not res_bad.is_valid
    assert any(i.code == "CONSTRAINT_VIOLATION" for i in res_bad.issues)


def test_rsi_empty_and_single_value() -> None:
    op = RsiOperation()
    bindings = _MockBindings()
    params = FrozenObject.from_mapping({"period": 3})

    # Empty
    res_empty = op.execute({"values": ()}, params, bindings)
    assert res_empty["rsi"] == ()

    # 1 value
    res_one = op.execute({"values": (100.0,)}, params, bindings)
    assert len(res_one["rsi"]) == 1
    assert isinstance(res_one["rsi"][0], MissingValue)
    assert res_one["rsi"][0].reason == "WARMUP"


def test_rsi_warmup_progression() -> None:
    op = RsiOperation()
    bindings = _MockBindings()
    params = FrozenObject.from_mapping({"period": 3})

    # Period 3 requires 3 deltas = 4 prices
    prices = (10.0, 11.0, 12.0)  # 3 prices = 2 deltas -> all warmup
    res = op.execute({"values": prices}, params, bindings)
    assert len(res["rsi"]) == 3
    assert all(isinstance(v, MissingValue) for v in res["rsi"])

    # 4 prices = 3 deltas -> 4th price produces seed
    prices_4 = (10.0, 11.0, 12.0, 13.0)
    res_4 = op.execute({"values": prices_4}, params, bindings)
    assert len(res_4["rsi"]) == 4
    assert isinstance(res_4["rsi"][0], MissingValue)
    assert isinstance(res_4["rsi"][1], MissingValue)
    assert isinstance(res_4["rsi"][2], MissingValue)
    assert isinstance(res_4["rsi"][3], float)
    # Rising prices -> RSI is 100.0
    assert res_4["rsi"][3] == 100.0


def test_rsi_flat_series() -> None:
    op = RsiOperation()
    bindings = _MockBindings()
    params = FrozenObject.from_mapping({"period": 3})

    # Flat prices -> delta=0, avg_gain=0, avg_loss=0 -> rule 4: output 50.0
    prices = (50.0, 50.0, 50.0, 50.0, 50.0, 50.0)
    res = op.execute({"values": prices}, params, bindings)
    rsi = res["rsi"]
    assert len(rsi) == 6
    for i in range(3):
        assert isinstance(rsi[i], MissingValue)
    for i in range(3, 6):
        assert rsi[i] == 50.0


def test_rsi_strictly_rising_and_falling() -> None:
    op = RsiOperation()
    bindings = _MockBindings()
    params = FrozenObject.from_mapping({"period": 2})

    # Rising -> deltas > 0, loss = 0 -> rule 5: 100.0
    rising = (10.0, 20.0, 30.0, 40.0)
    res_r = op.execute({"values": rising}, params, bindings)
    rsi_r = res_r["rsi"]
    assert rsi_r[2] == 100.0
    assert rsi_r[3] == 100.0

    # Falling -> deltas < 0, gain = 0 -> rule 6: 0.0
    falling = (40.0, 30.0, 20.0, 10.0)
    res_f = op.execute({"values": falling}, params, bindings)
    rsi_f = res_f["rsi"]
    assert rsi_f[2] == 0.0
    assert rsi_f[3] == 0.0


def test_rsi_hand_calculated_mixed_series() -> None:
    op = RsiOperation()
    bindings = _MockBindings()
    params = FrozenObject.from_mapping({"period": 2})

    # Prices: [10, 12, 11, 13]
    # d1 = 12 - 10 = +2 (gain=2, loss=0)
    # d2 = 11 - 12 = -1 (gain=0, loss=1)
    # At index 2: seed avg_gain = (2 + 0)/2 = 1.0, avg_loss = (0 + 1)/2 = 0.5
    # rs = 1.0 / 0.5 = 2.0 -> rsi = 100 - 100 / (1 + 2) = 100 - 33.333333... = 66.666666...
    # d3 = 13 - 11 = +2 (gain=2, loss=0)
    # avg_gain = (1.0 * 1 + 2) / 2 = 1.5
    # avg_loss = (0.5 * 1 + 0) / 2 = 0.25
    # rs = 1.5 / 0.25 = 6.0 -> rsi = 100 - 100 / 7.0 = 85.7142857...
    prices = (10.0, 12.0, 11.0, 13.0)
    res = op.execute({"values": prices}, params, bindings)
    rsi = res["rsi"]
    assert isinstance(rsi[0], MissingValue)
    assert isinstance(rsi[1], MissingValue)
    assert math.isclose(float(rsi[2]), 66.66666666666667, rel_tol=1e-9)
    assert math.isclose(float(rsi[3]), 85.71428571428572, rel_tol=1e-9)


def test_rsi_missing_gap_and_reseeding() -> None:
    op = RsiOperation()
    bindings = _MockBindings()
    params = FrozenObject.from_mapping({"period": 2})

    # [10, 12, 14, MissingValue("GAP"), 20, 22, 24]
    # i=0: 10 (warmup)
    # i=1: 12 (warmup)
    # i=2: 14 -> seed RSI (100.0)
    # i=3: GAP -> MissingValue("GAP") and reset!
    # i=4: 20 (warmup)
    # i=5: 22 (warmup)
    # i=6: 24 -> seed RSI (100.0)
    prices = (10.0, 12.0, 14.0, MissingValue("GAP"), 20.0, 22.0, 24.0)
    res = op.execute({"values": prices}, params, bindings)
    rsi = res["rsi"]
    assert rsi[2] == 100.0
    assert isinstance(rsi[3], MissingValue) and rsi[3].reason == "GAP"
    assert isinstance(rsi[4], MissingValue) and rsi[4].reason == "WARMUP"
    assert isinstance(rsi[5], MissingValue) and rsi[5].reason == "WARMUP"
    assert rsi[6] == 100.0


def test_rsi_non_finite_rejection() -> None:
    op = RsiOperation()
    bindings = _MockBindings()
    params = FrozenObject.from_mapping({"period": 2})

    with pytest.raises(ValueError, match="Non-finite"):
        op.execute({"values": (10.0, float("nan"), 12.0)}, params, bindings)

    with pytest.raises(ValueError, match="Non-finite"):
        op.execute({"values": (10.0, float("inf"), 12.0)}, params, bindings)


def test_rsi_input_mutation_safety() -> None:
    op = RsiOperation()
    bindings = _MockBindings()
    params = FrozenObject.from_mapping({"period": 2})

    input_list = [10.0, 12.0, 14.0]
    res = op.execute({"values": input_list}, params, bindings)
    rsi_before = res["rsi"]

    # Mutate caller input list
    input_list[1] = 999.0
    # Output must not be affected
    assert res["rsi"] == rsi_before


def test_rsi_lowering() -> None:
    op = RsiOperation()
    ctx = _MockLoweringContext(LoweringTarget(target_id="python", version=(1, 0, 0)))
    params = FrozenObject.from_mapping({"period": 14})

    res = op.lower(ctx, params)
    assert res.success
    assert res.program is not None
    assert len(res.program.inputs) == 1
    assert res.program.inputs[0].key == "values"
    assert len(res.program.outputs) == 1
    assert res.program.outputs[0].key == "rsi"

    # Unsupported target
    bad_ctx = _MockLoweringContext(LoweringTarget(target_id="rust", version=(1, 0, 0)))
    res_bad = op.lower(bad_ctx, params)
    assert not res_bad.success
    assert any(i.code == "UNSUPPORTED_TARGET" for i in res_bad.issues)


SCALAR_GOLDENS: tuple[tuple[str, tuple[Any, ...], int], ...] = (
    ("empty", (), 3),
    ("single", (10.0,), 3),
    ("shorter", (10.0, 11.0, 12.0), 3),
    ("mixed", (10.0, 12.0, 11.0, 13.0, 10.0, 14.0), 3),
    ("flat", (10.0, 10.0, 10.0, 10.0, 10.0, 10.0, 10.0), 3),
    ("rising", (10.0, 11.0, 12.0, 13.0, 14.0, 15.0), 4),
    ("falling", (15.0, 14.0, 13.0, 12.0, 11.0), 2),
    (
        "gap_reseed",
        (10.0, 11.0, 12.0, 13.0, None, 12.0, 13.0, 14.0, 15.0, 16.0),
        3,
    ),
)


@pytest.mark.parametrize("name,series,period", SCALAR_GOLDENS)
def test_scalar_reference_matches_vector_implementation(
    name: str, series: tuple[Any, ...], period: int
) -> None:
    from app.plugins.indicators.rsi import (
        scalar_reference_rsi,
    )

    scalar = scalar_reference_rsi(series, period)

    op = RsiOperation()
    from app.plugins.schema import FrozenObject

    out = op.execute(
        {"values": series},
        FrozenObject.from_mapping({"period": period}),
        _MockBindings(),
    )
    vector = out["rsi"]

    assert len(scalar) == len(vector) == len(series)
    for s_v, v_v in zip(scalar, vector, strict=True):
        if isinstance(v_v, MissingValue):
            assert isinstance(s_v, MissingValue)
            assert s_v == v_v
        else:
            assert s_v == pytest.approx(v_v, rel=1e-12)


def test_scalar_reference_rejects_invalid_period_and_inputs() -> None:
    from app.plugins.indicators.rsi import ScalarRsiReference

    with pytest.raises(ValueError, match="period"):
        ScalarRsiReference(1)
    with pytest.raises(TypeError, match="numeric"):
        ScalarRsiReference(3).step(True)
    with pytest.raises(ValueError, match="Non-finite"):
        ScalarRsiReference(3).step(float("nan"))

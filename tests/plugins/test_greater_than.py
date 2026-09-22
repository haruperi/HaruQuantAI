"""Comprehensive unit and golden tests for comparison.greater_than plugin."""

from typing import Any

import pytest
from app.plugins.comparisons.greater_than import (
    OPERATION_ID,
    PLUGIN_REF,
    GreaterThanOperation,
    plugin,
)
from app.plugins.lowering import OP_STD_GT, LoweringContext, LoweringTarget
from app.plugins.schema import EMPTY_FROZEN_OBJECT, MissingValue
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


def test_greater_than_spec_and_factory() -> None:
    contrib = plugin()
    assert contrib.spec.ref == PLUGIN_REF
    assert contrib.spec.kind == "comparison"
    assert len(contrib.spec.operations) == 1
    op_spec = contrib.spec.operations[0]
    assert op_spec.operation_id == OPERATION_ID
    assert len(op_spec.inputs) == 2
    assert op_spec.inputs[0].key == "left"
    assert op_spec.inputs[1].key == "right"
    assert len(op_spec.outputs) == 1
    assert op_spec.outputs[0].key == "result"


def test_greater_than_execution_and_missing_propagation() -> None:
    op = GreaterThanOperation()
    bindings = _MockBindings()

    left = (10.0, 20.0, 5.0, MissingValue("GAP"), 15.0)
    right = (5.0, 20.0, 10.0, 10.0, MissingValue("WARMUP"))

    res = op.execute({"left": left, "right": right}, EMPTY_FROZEN_OBJECT, bindings)
    result = res["result"]

    assert len(result) == 5
    assert result[0] is True  # 10.0 > 5.0
    assert result[1] is False  # 20.0 > 20.0 is False
    assert result[2] is False  # 5.0 > 10.0 is False
    assert isinstance(result[3], MissingValue) and result[3].reason == "PROPAGATED"
    assert isinstance(result[4], MissingValue) and result[4].reason == "PROPAGATED"


def test_greater_than_length_mismatch() -> None:
    op = GreaterThanOperation()
    bindings = _MockBindings()

    with pytest.raises(ValueError, match="lengths do not match"):
        op.execute(
            {"left": (1.0, 2.0), "right": (1.0,)},
            EMPTY_FROZEN_OBJECT,
            bindings,
        )


def test_greater_than_non_finite_rejection() -> None:
    op = GreaterThanOperation()
    bindings = _MockBindings()

    with pytest.raises(ValueError, match="Non-finite"):
        op.execute(
            {"left": (float("nan"),), "right": (1.0,)},
            EMPTY_FROZEN_OBJECT,
            bindings,
        )

    with pytest.raises(ValueError, match="Non-finite"):
        op.execute(
            {"left": (1.0,), "right": (float("inf"),)},
            EMPTY_FROZEN_OBJECT,
            bindings,
        )


def test_greater_than_lowering() -> None:
    op = GreaterThanOperation()
    ctx = _MockLoweringContext(LoweringTarget(target_id="python", version=(1, 0, 0)))

    res = op.lower(ctx, EMPTY_FROZEN_OBJECT)
    assert res.success
    assert res.program is not None
    assert len(res.program.inputs) == 2
    assert len(res.program.nodes) == 1
    assert res.program.nodes[0].operator == OP_STD_GT
    assert len(res.program.outputs) == 1
    assert res.program.outputs[0].key == "result"

    # Unsupported target
    bad_ctx = _MockLoweringContext(LoweringTarget(target_id="c", version=(1, 0, 0)))
    res_bad = op.lower(bad_ctx, EMPTY_FROZEN_OBJECT)
    assert not res_bad.success

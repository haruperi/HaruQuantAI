"""Comprehensive tests for exporter.python plugin and generated code parity."""

import ast
import math
from typing import Any

import pytest
from app.plugins.comparisons.greater_than import GreaterThanOperation
from app.plugins.exporters.python import (
    OPERATION_ID,
    PLUGIN_REF,
    PythonCodeGenerator,
    PythonExporterOperation,
    plugin,
)
from app.plugins.indicators.rsi import RsiOperation
from app.plugins.lowering import (
    IRNode,
    LiteralRef,
    LoweringContext,
    LoweringTarget,
    ProgramInput,
    ProgramOutput,
    SemanticProgram,
    ValueRef,
)
from app.plugins.schema import (
    EMPTY_FROZEN_OBJECT,
    Alignment,
    FrozenObject,
    MissingValue,
    ValueKind,
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


def _run_generated_python(code: str, inputs: dict[str, Any]) -> dict[str, Any]:
    """Execute generated Python source in an isolated namespace."""
    # Validate syntax via ast.parse first
    ast.parse(code)
    namespace: dict[str, Any] = {}
    exec(code, namespace)
    execute_fn = namespace["execute"]
    result = execute_fn(inputs)
    assert isinstance(result, dict)
    return result


def test_python_exporter_spec_and_factory() -> None:
    contrib = plugin()
    assert contrib.spec.ref == PLUGIN_REF
    assert contrib.spec.kind == "exporter"
    assert len(contrib.spec.operations) == 1
    assert contrib.spec.operations[0].operation_id == OPERATION_ID


def test_python_exporter_greater_than_parity() -> None:
    gt_op = GreaterThanOperation()
    ctx = _MockLoweringContext(LoweringTarget(target_id="python", version=(1, 0, 0)))
    lowered = gt_op.lower(ctx, EMPTY_FROZEN_OBJECT)
    assert lowered.success and lowered.program is not None

    exporter_op = PythonExporterOperation()
    bindings = _MockBindings()
    res = exporter_op.execute(
        {"program": lowered.program}, EMPTY_FROZEN_OBJECT, bindings
    )
    source_code = res["source"]
    manifest = res["manifest"]

    assert manifest["target_id"] == "python"
    assert "execute" in source_code

    # Run native
    left = (10.0, 5.0, 20.0, MissingValue("GAP"), 15.0)
    right = (5.0, 10.0, 20.0, 10.0, MissingValue("WARMUP"))
    native_out = gt_op.execute(
        {"left": left, "right": right}, EMPTY_FROZEN_OBJECT, bindings
    )

    # Run generated Python
    generated_out = _run_generated_python(source_code, {"left": left, "right": right})

    assert len(native_out["result"]) == len(generated_out["result"])
    for n_val, g_val in zip(native_out["result"], generated_out["result"], strict=True):
        if isinstance(n_val, MissingValue):
            assert type(g_val).__name__ == "MissingValue"
        else:
            assert n_val == g_val


def test_python_exporter_rsi_parity() -> None:
    rsi_op = RsiOperation()
    ctx = _MockLoweringContext(LoweringTarget(target_id="python", version=(1, 0, 0)))
    params = FrozenObject.from_mapping({"period": 3})
    lowered = rsi_op.lower(ctx, params)
    assert lowered.success and lowered.program is not None

    exporter_op = PythonExporterOperation()
    bindings = _MockBindings()
    res = exporter_op.execute(
        {"program": lowered.program}, EMPTY_FROZEN_OBJECT, bindings
    )
    source_code = res["source"]

    # Test on rising, flat, and mixed series
    test_series = (
        (10.0, 11.0, 12.0, 13.0, 14.0, 15.0),
        (50.0, 50.0, 50.0, 50.0, 50.0),
        (10.0, 12.0, 11.0, 13.0, 14.0, MissingValue("GAP"), 20.0, 22.0, 24.0, 26.0),
    )

    for series in test_series:
        native_out = rsi_op.execute({"values": series}, params, bindings)
        generated_out = _run_generated_python(source_code, {"values": series})

        assert len(native_out["rsi"]) == len(generated_out["rsi"])
        for n_val, g_val in zip(native_out["rsi"], generated_out["rsi"], strict=True):
            if isinstance(n_val, MissingValue):
                assert type(g_val).__name__ == "MissingValue"
            else:
                assert math.isclose(
                    float(n_val), float(g_val), rel_tol=1e-7, abs_tol=1e-7
                )


def test_python_exporter_unsupported_operator() -> None:
    from app.plugins.lowering import OP_STD_LAG

    bad_program = SemanticProgram(
        inputs=(
            ProgramInput(
                key="x", kind=ValueKind.ALIGNED_SERIES, alignment=Alignment.INDEX
            ),
        ),
        nodes=(
            IRNode(
                id="n1",
                operator=OP_STD_LAG,  # Valid universal operator, but unsupported in this exporter
                inputs=(ValueRef("x", "x"), LiteralRef(1)),
            ),
        ),
        outputs=(
            ProgramOutput(
                key="out",
                source=ValueRef("n1", "out"),
                kind=ValueKind.ALIGNED_SERIES,
                alignment=Alignment.INDEX,
            ),
        ),
    )
    generator = PythonCodeGenerator(bad_program)
    with pytest.raises(ValueError, match="Unsupported universal semantic operator"):
        generator.generate()

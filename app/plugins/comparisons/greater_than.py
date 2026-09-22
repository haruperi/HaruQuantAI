"""Greater-than comparison plugin.

Cohesive single-file plugin: behavior, schema, bounds, lowering, and
presentation metadata for strict elementwise greater-than comparison
live in this file. Stable identity: ``comparison.greater_than@1.0.0``.
The zero-argument ``plugin()`` factory is pure and side-effect free —
no I/O, no tasks or threads, no environment reads, no registration —
and the plugin is discovered through the host catalog, never imported
by name by the host or other plugins.

Semantics: elementwise strict ``left > right`` over two aligned numeric
series of exactly equal length (mismatched lengths raise ValueError).
There is no scalar broadcasting and no unit conversion — both ports
declare ``Unit.NONE``. Missing-in means missing-out: a None or
MissingValue sample on either side produces
``MissingValue("PROPAGATED")`` at that index. Non-numeric samples
raise TypeError and non-finite samples raise ValueError before any
comparison runs. The operation declares no parameters and needs no
warm-up.
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from typing import Any, override

from app.plugins.lowering import (
    OP_STD_GT,
    IRNode,
    LoweringContext,
    LoweringResult,
    LoweringTarget,
    ProgramInput,
    ProgramOutput,
    SemanticProgram,
    ValueRef,
)
from app.plugins.schema import (
    Alignment,
    FrozenObject,
    MissingValue,
    NumericalPolicy,
    ParameterBindingResult,
    ParameterSchema,
    PortSpec,
    Unit,
    ValueKind,
)
from app.plugins.spec import (
    CURRENT_METAMODEL_MAJOR,
    OperationBindings,
    OperationContribution,
    OperationImplementation,
    OperationSpec,
    PluginContribution,
    PluginRef,
    PluginSpec,
)

PLUGIN_REF = PluginRef(id="comparison.greater_than", version=(1, 0, 0))
OPERATION_ID = "compare"
TARGET_PYTHON = LoweringTarget(target_id="python", version=(1, 0, 0))

INPUT_LEFT = PortSpec(
    key="left",
    kind=ValueKind.ALIGNED_SERIES,
    unit=Unit.NONE,
    alignment=Alignment.INDEX,
    label="Left Series",
    description="Left-hand aligned numeric series for comparison",
)

INPUT_RIGHT = PortSpec(
    key="right",
    kind=ValueKind.ALIGNED_SERIES,
    unit=Unit.NONE,
    alignment=Alignment.INDEX,
    label="Right Series",
    description="Right-hand aligned numeric series for comparison",
)

OUTPUT_RESULT = PortSpec(
    key="result",
    kind=ValueKind.ALIGNED_SERIES,
    unit=Unit.NONE,
    alignment=Alignment.INDEX,
    label="Result",
    description="Aligned boolean series indicating left > right",
)

GT_SCHEMA = ParameterSchema()
GT_POLICY = NumericalPolicy(
    tolerance=1e-9, nan_policy="reject", missing_policy="propagate"
)


def _validate_gt_series(left_raw: Sequence[Any], right_raw: Sequence[Any]) -> None:
    """Validate that series have matching lengths and contain finite numbers.

    None and MissingValue samples are permitted gaps on either side.
    """
    if len(left_raw) != len(right_raw):
        raise ValueError(
            f"Input series lengths do not match: left={len(left_raw)}, "
            f"right={len(right_raw)}"
        )
    for label, series in (("left", left_raw), ("right", right_raw)):
        for idx, val in enumerate(series):
            if val is not None and not isinstance(val, MissingValue):
                if not isinstance(val, (int, float)) or isinstance(val, bool):
                    raise TypeError(
                        f"{label} series must contain numeric values, "
                        f"got {type(val).__name__} at index {idx}"
                    )
                if not math.isfinite(val):
                    raise ValueError(
                        f"Non-finite value {val!r} rejected in {label} "
                        f"input at index {idx}"
                    )


class GreaterThanOperation(OperationImplementation):
    """Elementwise greater-than execution and lowering implementation.

    ``execute`` compares the two series index by index; ``lower`` emits
    the same semantics as a single ``std.gt`` node over the two declared
    series inputs.
    """

    @override
    def validate_parameters(self, values: FrozenObject) -> ParameterBindingResult:
        """Validate parameter values against schema.

        Args:
            values: Parameter values mapping.

        Returns:
            Binding result; the operation declares no parameters.
        """
        return GT_SCHEMA.validate_bindings(values)

    @override
    def warmup_samples(self, values: FrozenObject) -> int:
        """Comparison does not require warm-up.

        Args:
            values: Bound parameter values (unused).

        Returns:
            Always zero.
        """
        return 0

    @override
    def execute(
        self,
        inputs: Mapping[str, Any],
        parameters: FrozenObject,
        bindings: OperationBindings,
    ) -> Mapping[str, Any]:
        """Perform elementwise left > right comparison.

        Both series are validated first (equal lengths, numeric,
        finite); each index then yields a strict boolean comparison or a
        propagated missing marker. No scalar broadcast and no unit
        conversion are performed.

        Args:
            inputs: Mapping with the ``left`` and ``right`` series.
            parameters: Unused; the operation declares no parameters.
            bindings: Unused; the comparison requires no capabilities.

        Returns:
            Mapping with the ``result`` boolean series of the same
            length as the inputs.

        Raises:
            ValueError: If the series lengths differ or a sample is
                non-finite.
            TypeError: If a non-missing sample is not numeric.
        """
        left_raw = inputs.get("left", ())
        right_raw = inputs.get("right", ())

        if not isinstance(left_raw, (tuple, list, Sequence)):
            left_raw = tuple(left_raw) if left_raw is not None else ()
        if not isinstance(right_raw, (tuple, list, Sequence)):
            right_raw = tuple(right_raw) if right_raw is not None else ()

        _validate_gt_series(left_raw, right_raw)

        results: list[bool | MissingValue] = []
        for l_val, r_val in zip(left_raw, right_raw, strict=True):
            if (
                l_val is None
                or isinstance(l_val, MissingValue)
                or r_val is None
                or isinstance(r_val, MissingValue)
            ):
                results.append(MissingValue(reason="PROPAGATED"))
            else:
                results.append(bool(float(l_val) > float(r_val)))

        return {"result": tuple(results)}

    @override
    def lower(
        self,
        context: LoweringContext,
        parameters: FrozenObject,
    ) -> LoweringResult:
        """Lower greater-than comparison into universal semantic IR.

        Only the exact target ``python@1.0.0`` is supported; the program
        is one ``std.gt`` node consuming the two declared series
        inputs.

        Args:
            context: Host lowering context carrying the exact target.
            parameters: Unused; the operation declares no parameters.

        Returns:
            Successful LoweringResult, or a failure carrying an
            UNSUPPORTED_TARGET issue.
        """
        if context.target != TARGET_PYTHON:
            from app.plugins.lowering import LoweringIssue

            return LoweringResult(
                success=False,
                issues=(
                    LoweringIssue(
                        code="UNSUPPORTED_TARGET",
                        message=(
                            f"Target {context.target.target_id}@"
                            f"{context.target.version} "
                            "is not supported by comparison.greater_than"
                        ),
                    ),
                ),
            )

        p_left = ProgramInput(
            key="left",
            kind=ValueKind.ALIGNED_SERIES,
            alignment=Alignment.INDEX,
        )
        p_right = ProgramInput(
            key="right",
            kind=ValueKind.ALIGNED_SERIES,
            alignment=Alignment.INDEX,
        )

        gt_node = IRNode(
            id=context.allocate_node_id("gt"),
            operator=OP_STD_GT,
            inputs=(ValueRef("left", "left"), ValueRef("right", "right")),
            outputs=("out",),
        )

        p_out = ProgramOutput(
            key="result",
            source=ValueRef(gt_node.id, "out"),
            kind=ValueKind.ALIGNED_SERIES,
            alignment=Alignment.INDEX,
        )

        program = SemanticProgram(
            inputs=(p_left, p_right),
            nodes=(gt_node,),
            outputs=(p_out,),
        )
        return LoweringResult(success=True, program=program)


def plugin() -> PluginContribution:
    """Return the pure plugin contribution for comparison.greater_than.

    Zero-argument factory building the self-describing PluginSpec —
    identity comparison.greater_than version 1.0.0, kind
    ``comparison``, one ``compare`` operation — and its implementation.
    Performs no I/O and no registration; discovery happens through the
    host catalog.

    Returns:
        Immutable PluginContribution for comparison.greater_than@1.0.0.
    """
    op_spec = OperationSpec(
        operation_id=OPERATION_ID,
        title="Compare Greater Than",
        description="Elementwise greater-than comparison of two aligned numeric series",
        parameters=GT_SCHEMA,
        inputs=(INPUT_LEFT, INPUT_RIGHT),
        outputs=(OUTPUT_RESULT,),
        determinism=True,
        numerical_policy=GT_POLICY,
        effects=("pure",),
        lowering_targets=(TARGET_PYTHON,),
    )
    plugin_spec = PluginSpec(
        ref=PLUGIN_REF,
        kind="comparison",
        title="Greater Than",
        description="Compare whether left series is strictly greater than right series",
        metamodel_major=CURRENT_METAMODEL_MAJOR,
        operations=(op_spec,),
    )
    return PluginContribution(
        spec=plugin_spec,
        operations=(OperationContribution(OPERATION_ID, GreaterThanOperation()),),
    )

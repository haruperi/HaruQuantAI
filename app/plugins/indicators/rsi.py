"""Relative Strength Index (RSI) indicator plugin.

Cohesive single-file plugin: the calculation behavior, parameter schema
and bounds, lowering, and presentation metadata for the RSI concept all
live in this file and nowhere else. Stable identity:
``indicator.rsi@1.0.0``. The zero-argument ``plugin()`` factory is pure
— no I/O, no tasks or threads, no environment reads, no registration —
and returns an immutable ``PluginContribution``; the plugin is
discovered through the host catalog and is never imported by name by
the host or by other plugins.

Numerical semantics (cross-checked against the scalar reference below
and ``tests/plugins/test_rsi.py``): Wilder smoothing over price deltas.
After one finite sample establishes a previous value, the first
``period`` consecutive finite deltas seed the average gain/loss with a
simple mean; every later step applies the Wilder recurrence
``avg = (avg * (period - 1) + x) / period``. The first sample of a
series (or of any post-gap segment) is warm-up missing; an explicit
missing or None sample emits ``MissingValue("GAP")`` and resets all
state, so reseeding again needs one sample plus ``period`` consecutive
finite deltas. Degenerate rules: both averages zero -> 50.0; average
loss zero -> 100.0; average gain zero -> 0.0; otherwise
``100 - 100 / (1 + avg_gain / avg_loss)``. Output length always equals
input length. Non-numeric samples raise TypeError and non-finite
samples raise ValueError before any calculation runs.

Parameter ``period``: integer constrained to 2..1000 with default 14;
the optimization domain searches 2..100 with step 1 on a linear scale.
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from typing import Any, override

from app.plugins.lowering import (
    OP_STD_ADD,
    OP_STD_COND,
    OP_STD_DELTA,
    OP_STD_DIV,
    OP_STD_EQ,
    OP_STD_MAX,
    OP_STD_RECURRENCE,
    OP_STD_SUB,
    IRNode,
    LiteralRef,
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
    NumericConstraint,
    OptimizationDomain,
    OptimizationScale,
    ParameterBindingResult,
    ParameterSchema,
    ParameterSpec,
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

PLUGIN_REF = PluginRef(id="indicator.rsi", version=(1, 0, 0))
OPERATION_ID = "compute"
TARGET_PYTHON = LoweringTarget(target_id="python", version=(1, 0, 0))
MIN_PERIOD = 2
MAX_PERIOD = 1000

PARAMETER_PERIOD = ParameterSpec(
    key="period",
    kind=ValueKind.INTEGER,
    label="Period",
    description="Lookback period for Wilder smoothing",
    required=True,
    default=14,
    constraint=NumericConstraint(min_value=MIN_PERIOD, max_value=MAX_PERIOD),
    optimization=OptimizationDomain(
        eligible=True,
        min_value=2,
        max_value=100,
        step=1,
        scale=OptimizationScale.LINEAR,
    ),
)

INPUT_VALUES = PortSpec(
    key="values",
    kind=ValueKind.ALIGNED_SERIES,
    unit=Unit.NONE,
    alignment=Alignment.INDEX,
    label="Values",
    description="Input numeric price or value series",
)

OUTPUT_RSI = PortSpec(
    key="rsi",
    kind=ValueKind.ALIGNED_SERIES,
    unit=Unit.PERCENT,
    alignment=Alignment.INDEX,
    label="RSI",
    description="Relative Strength Index series (0-100%)",
)

RSI_SCHEMA = ParameterSchema((PARAMETER_PERIOD,))
RSI_POLICY = NumericalPolicy(
    tolerance=1e-9, nan_policy="reject", missing_policy="reset"
)


def _validate_rsi_inputs(raw_series: Sequence[Any]) -> None:
    """Validate that input series contains finite numeric values.

    None and MissingValue samples are permitted gaps; every other
    sample must be numeric and finite.
    """
    for idx, val in enumerate(raw_series):
        if val is not None and not isinstance(val, MissingValue):
            if not isinstance(val, (int, float)) or isinstance(val, bool):
                raise TypeError(
                    f"Input values must be numeric, got {type(val).__name__} "
                    f"at index {idx}"
                )
            if not math.isfinite(val):
                raise ValueError(
                    f"Non-finite value {val!r} rejected in RSI input at index {idx}"
                )


def _compute_rsi_values(
    raw_series: Sequence[Any], period: int
) -> tuple[float | MissingValue, ...]:
    """Compute RSI values series using Wilder smoothing.

    Implements the module semantics: ``period`` consecutive finite
    deltas seed the averages with a simple mean, later steps apply the
    Wilder recurrence, gaps reset all state, warm-up samples yield
    ``MissingValue("WARMUP")``, and the 50/100/0 degenerate rules apply.
    The returned tuple has exactly one output per input sample.
    """
    outputs: list[float | MissingValue] = []
    consecutive_deltas: list[tuple[float, float]] = []
    prev_val: float | None = None
    avg_gain: float | None = None
    avg_loss: float | None = None

    for raw_val in raw_series:
        if raw_val is None or isinstance(raw_val, MissingValue):
            outputs.append(MissingValue(reason="GAP"))
            prev_val = None
            consecutive_deltas.clear()
            avg_gain = None
            avg_loss = None
            continue

        current_val = float(raw_val)
        if prev_val is None:
            outputs.append(MissingValue(reason="WARMUP"))
            prev_val = current_val
            continue

        delta = current_val - prev_val
        gain = max(delta, 0.0)
        loss = max(-delta, 0.0)
        prev_val = current_val

        if avg_gain is None or avg_loss is None:
            consecutive_deltas.append((gain, loss))
            if len(consecutive_deltas) < period:
                outputs.append(MissingValue(reason="WARMUP"))
                continue
            avg_gain = sum(g for g, _ in consecutive_deltas) / period
            avg_loss = sum(loss_val for _, loss_val in consecutive_deltas) / period
        else:
            avg_gain = (avg_gain * (period - 1) + gain) / period
            avg_loss = (avg_loss * (period - 1) + loss) / period

        if avg_gain == 0.0 and avg_loss == 0.0:
            outputs.append(50.0)
        elif avg_loss == 0.0:
            outputs.append(100.0)
        elif avg_gain == 0.0:
            outputs.append(0.0)
        else:
            rs = avg_gain / avg_loss
            rsi = 100.0 - 100.0 / (1.0 + rs)
            outputs.append(rsi)

    return tuple(outputs)


class ScalarRsiReference:
    """Scalar (one-sample-at-a-time) reference RSI implementation.

    Owns the same numerical semantics as the vector implementation in this
    file: explicit missing samples reset the seed, warm-up needs ``period``
    consecutive finite deltas, Wilder smoothing thereafter, and the 50/100/0
    degenerate rules. Used as an independent cross-check in tests; not wired
    into the host execution path.
    """

    def __init__(self, period: int) -> None:
        """Initialize scalar reference with a validated period.

        Args:
            period: Lookback period within ``[MIN_PERIOD, MAX_PERIOD]``.

        Raises:
            ValueError: If ``period`` is not an integer in range.
        """
        if not isinstance(period, int) or not (MIN_PERIOD <= period <= MAX_PERIOD):
            raise ValueError(
                f"period must be an integer in [{MIN_PERIOD}, {MAX_PERIOD}], "
                f"got {period!r}"
            )
        self._period = period
        self._prev: float | None = None
        self._seed: list[tuple[float, float]] = []
        self._avg_gain: float | None = None
        self._avg_loss: float | None = None

    def step(self, sample: float | MissingValue | None) -> float | MissingValue:
        """Consume one sample and return the RSI value at that index.

        Args:
            sample: One numeric sample, or None/MissingValue for a gap.

        Returns:
            The RSI value, or a warm-up/gap MissingValue marker.

        Raises:
            TypeError: If a non-missing sample is not numeric.
            ValueError: If a sample is non-finite.
        """
        if sample is None or isinstance(sample, MissingValue):
            self._prev = None
            self._seed.clear()
            self._avg_gain = None
            self._avg_loss = None
            return MissingValue(reason="GAP")
        if not isinstance(sample, (int, float)) or isinstance(sample, bool):
            raise TypeError(f"Sample must be numeric, got {type(sample).__name__}")
        if not math.isfinite(sample):
            raise ValueError(f"Non-finite sample {sample!r} rejected")

        current = float(sample)
        if self._prev is None:
            self._prev = current
            return MissingValue(reason="WARMUP")

        delta = current - self._prev
        gain = max(delta, 0.0)
        loss = max(-delta, 0.0)
        self._prev = current

        if self._avg_gain is None or self._avg_loss is None:
            self._seed.append((gain, loss))
            if len(self._seed) < self._period:
                return MissingValue(reason="WARMUP")
            self._avg_gain = sum(g for g, _ in self._seed) / self._period
            self._avg_loss = sum(loss_v for _, loss_v in self._seed) / self._period
        else:
            self._avg_gain = (self._avg_gain * (self._period - 1) + gain) / self._period
            self._avg_loss = (self._avg_loss * (self._period - 1) + loss) / self._period

        return _rsi_from_averages(self._avg_gain, self._avg_loss)


def _rsi_from_averages(avg_gain: float, avg_loss: float) -> float:
    """Apply the 50/100/0 degenerate rules and the standard RSI formula."""
    if avg_gain == 0.0 and avg_loss == 0.0:
        return 50.0
    if avg_loss == 0.0:
        return 100.0
    if avg_gain == 0.0:
        return 0.0
    rs = avg_gain / avg_loss
    return 100.0 - 100.0 / (1.0 + rs)


def scalar_reference_rsi(
    raw_series: Sequence[Any], period: int
) -> tuple[float | MissingValue, ...]:
    """Run the scalar reference over a whole series, one sample per step.

    Args:
        raw_series: Input series of numbers, None, or MissingValue.
        period: Lookback period within ``[MIN_PERIOD, MAX_PERIOD]``.

    Returns:
        Tuple of RSI values or missing markers, one per input sample.
    """
    ref = ScalarRsiReference(period)
    return tuple(ref.step(s) for s in raw_series)


class RsiOperation(OperationImplementation):
    """Execution and lowering implementation for RSI calculation.

    ``execute`` runs the vector computation in this file; ``lower``
    expresses the identical semantics as a version-1 SemanticProgram
    built only from ``std.*`` operators, embedding the Wilder recurrence
    method and the bound period in the IR node parameters.
    """

    @override
    def validate_parameters(self, values: FrozenObject) -> ParameterBindingResult:
        """Validate parameter values against the declarative RSI schema.

        Args:
            values: Parameter values mapping.

        Returns:
            Binding result; RSI declares no cross-field constraints.
        """
        return RSI_SCHEMA.validate_bindings(values)

    @override
    def warmup_samples(self, values: FrozenObject) -> int:
        """Dynamic warmup requires 'period' price changes.

        Args:
            values: Bound parameter values.

        Returns:
            The bound ``period``, or 14 when the stored value is missing
            or not a positive integer.
        """
        period = values.get("period", 14)
        if isinstance(period, int) and period > 0:
            return period
        return 14

    @override
    def execute(
        self,
        inputs: Mapping[str, Any],
        parameters: FrozenObject,
        bindings: OperationBindings,
    ) -> Mapping[str, Any]:
        """Compute RSI series using Wilder smoothing.

        The input series is fully validated before any calculation; the
        output series has exactly one value per input sample, and an
        empty or absent series yields an empty output.

        Args:
            inputs: Mapping with the ``values`` series.
            parameters: Bound parameters containing ``period``.
            bindings: Unused; RSI requires no capabilities.

        Returns:
            Mapping with the ``rsi`` output series.

        Raises:
            TypeError: If a non-missing sample is not numeric.
            ValueError: If a sample is non-finite.
        """
        period_val = parameters.get("period", 14)
        period = int(period_val) if isinstance(period_val, (int, float)) else 14

        raw_series = inputs.get("values", ())
        if not isinstance(raw_series, (tuple, list, Sequence)):
            raw_series = tuple(raw_series) if raw_series is not None else ()

        _validate_rsi_inputs(raw_series)
        if not raw_series:
            return {"rsi": ()}

        return {"rsi": _compute_rsi_values(raw_series, period)}

    @override
    def lower(
        self,
        context: LoweringContext,
        parameters: FrozenObject,
    ) -> LoweringResult:
        """Lower RSI calculation into universal semantic IR.

        Only the exact target ``python@1.0.0`` is supported. The emitted
        program mirrors the vector semantics: delta, gain/loss clipping,
        two Wilder recurrence nodes parameterized with the bound period,
        and conditional nodes implementing the 50/100/0 degenerate
        rules.

        Args:
            context: Host lowering context carrying the exact target.
            parameters: Bound parameters containing ``period``.

        Returns:
            Successful LoweringResult with a SemanticProgram, or a
            failure carrying an UNSUPPORTED_TARGET issue.
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
                            "is not supported by indicator.rsi"
                        ),
                    ),
                ),
            )

        period_val = parameters.get("period", 14)
        period = int(period_val) if isinstance(period_val, (int, float)) else 14

        p_in = ProgramInput(
            key="values",
            kind=ValueKind.ALIGNED_SERIES,
            alignment=Alignment.INDEX,
        )

        n_delta = IRNode(
            id=context.allocate_node_id("delta"),
            operator=OP_STD_DELTA,
            inputs=(ValueRef("values", "values"),),
        )
        n_gain = IRNode(
            id=context.allocate_node_id("gain"),
            operator=OP_STD_MAX,
            inputs=(ValueRef(n_delta.id, "out"), LiteralRef(0.0)),
        )
        n_neg = IRNode(
            id=context.allocate_node_id("neg_delta"),
            operator=OP_STD_SUB,
            inputs=(LiteralRef(0.0), ValueRef(n_delta.id, "out")),
        )
        n_loss = IRNode(
            id=context.allocate_node_id("loss"),
            operator=OP_STD_MAX,
            inputs=(ValueRef(n_neg.id, "out"), LiteralRef(0.0)),
        )
        n_avg_gain = IRNode(
            id=context.allocate_node_id("avg_gain"),
            operator=OP_STD_RECURRENCE,
            inputs=(ValueRef(n_gain.id, "out"),),
            parameters=FrozenObject.from_mapping(
                {"method": "wilder_smoothing", "period": period}
            ),
        )
        n_avg_loss = IRNode(
            id=context.allocate_node_id("avg_loss"),
            operator=OP_STD_RECURRENCE,
            inputs=(ValueRef(n_loss.id, "out"),),
            parameters=FrozenObject.from_mapping(
                {"method": "wilder_smoothing", "period": period}
            ),
        )
        n_sum_gl = IRNode(
            id=context.allocate_node_id("sum_gl"),
            operator=OP_STD_ADD,
            inputs=(ValueRef(n_avg_gain.id, "out"), ValueRef(n_avg_loss.id, "out")),
        )
        n_both_zero = IRNode(
            id=context.allocate_node_id("both_zero"),
            operator=OP_STD_EQ,
            inputs=(ValueRef(n_sum_gl.id, "out"), LiteralRef(0.0)),
        )
        n_loss_zero = IRNode(
            id=context.allocate_node_id("loss_zero"),
            operator=OP_STD_EQ,
            inputs=(ValueRef(n_avg_loss.id, "out"), LiteralRef(0.0)),
        )
        n_gain_zero = IRNode(
            id=context.allocate_node_id("gain_zero"),
            operator=OP_STD_EQ,
            inputs=(ValueRef(n_avg_gain.id, "out"), LiteralRef(0.0)),
        )
        n_rs = IRNode(
            id=context.allocate_node_id("rs"),
            operator=OP_STD_DIV,
            inputs=(ValueRef(n_avg_gain.id, "out"), ValueRef(n_avg_loss.id, "out")),
        )
        n_one_plus_rs = IRNode(
            id=context.allocate_node_id("one_plus_rs"),
            operator=OP_STD_ADD,
            inputs=(LiteralRef(1.0), ValueRef(n_rs.id, "out")),
        )
        n_inv_rs = IRNode(
            id=context.allocate_node_id("inv_rs"),
            operator=OP_STD_DIV,
            inputs=(LiteralRef(100.0), ValueRef(n_one_plus_rs.id, "out")),
        )
        n_normal_rsi = IRNode(
            id=context.allocate_node_id("normal_rsi"),
            operator=OP_STD_SUB,
            inputs=(LiteralRef(100.0), ValueRef(n_inv_rs.id, "out")),
        )
        n_cond1 = IRNode(
            id=context.allocate_node_id("cond1"),
            operator=OP_STD_COND,
            inputs=(
                ValueRef(n_gain_zero.id, "out"),
                LiteralRef(0.0),
                ValueRef(n_normal_rsi.id, "out"),
            ),
        )
        n_cond2 = IRNode(
            id=context.allocate_node_id("cond2"),
            operator=OP_STD_COND,
            inputs=(
                ValueRef(n_loss_zero.id, "out"),
                LiteralRef(100.0),
                ValueRef(n_cond1.id, "out"),
            ),
        )
        n_final = IRNode(
            id=context.allocate_node_id("rsi_final"),
            operator=OP_STD_COND,
            inputs=(
                ValueRef(n_both_zero.id, "out"),
                LiteralRef(50.0),
                ValueRef(n_cond2.id, "out"),
            ),
        )

        p_out = ProgramOutput(
            key="rsi",
            source=ValueRef(n_final.id, "out"),
            kind=ValueKind.ALIGNED_SERIES,
            unit=Unit.PERCENT,
            alignment=Alignment.INDEX,
        )

        nodes = (
            n_delta,
            n_gain,
            n_neg,
            n_loss,
            n_avg_gain,
            n_avg_loss,
            n_sum_gl,
            n_both_zero,
            n_loss_zero,
            n_gain_zero,
            n_rs,
            n_one_plus_rs,
            n_inv_rs,
            n_normal_rsi,
            n_cond1,
            n_cond2,
            n_final,
        )

        program = SemanticProgram(
            inputs=(p_in,),
            nodes=nodes,
            outputs=(p_out,),
        )
        return LoweringResult(success=True, program=program)


def plugin() -> PluginContribution:
    """Return the zero-argument pure plugin contribution for indicator.rsi.

    Builds the self-describing PluginSpec — identity indicator.rsi
    version 1.0.0, kind ``indicator``, one ``compute`` operation — and
    its implementation. Performs no I/O and no registration; discovery
    happens through the host catalog.

    Returns:
        Immutable PluginContribution for indicator.rsi@1.0.0.
    """
    op_spec = OperationSpec(
        operation_id=OPERATION_ID,
        title="Compute RSI",
        description="Compute Relative Strength Index using Wilder smoothing",
        parameters=RSI_SCHEMA,
        inputs=(INPUT_VALUES,),
        outputs=(OUTPUT_RSI,),
        determinism=True,
        numerical_policy=RSI_POLICY,
        effects=("pure",),
        lowering_targets=(TARGET_PYTHON,),
    )
    plugin_spec = PluginSpec(
        ref=PLUGIN_REF,
        kind="indicator",
        title="Relative Strength Index",
        description="Momentum oscillator measuring speed and change of price moves",
        metamodel_major=CURRENT_METAMODEL_MAJOR,
        operations=(op_spec,),
    )
    return PluginContribution(
        spec=plugin_spec,
        operations=(OperationContribution(OPERATION_ID, RsiOperation()),),
    )

"""Universal semantic intermediate representation and lowering protocols.

Authority: this module owns the semantic lowering mechanics of the shared
plugin metamodel, as ratified for the S2 handoff in
``docs/dev/backend_implementation_handoff_s2_s5.md``: the reserved
``std.*`` operator namespace, the bounded ``SemanticProgram`` IR (schema
version 1), exact lowering targets, attributed issues/results, and the
``LoweringContext`` protocol consumed by operation contributions. It
contains no concrete plugin formula — no plugin ID appears here, and
adding a new IR primitive is metamodel evolution requiring review.

Position in the shared-module import DAG
(``schema <- lowering <- spec <- algebra <- wire``): this module imports
only ``schema``. No shared module may import ``app.host``.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Protocol

from app.plugins.schema import (
    EMPTY_FROZEN_OBJECT,
    Alignment,
    FrozenObject,
    Unit,
    Value,
    ValueKind,
    freeze_value,
    validate_identifier,
)

IR_SCHEMA_VERSION = 1
MAX_IR_NODES = 10_000
SEMVER_PART_COUNT = 3

# Reserved universal operator IDs
OPERATOR_NAMESPACE_PATTERN = re.compile(r"^std\.[a-z][a-z0-9_]*$")

# Standard arithmetic
OP_STD_ADD = "std.add"
OP_STD_SUB = "std.sub"
OP_STD_MUL = "std.mul"
OP_STD_DIV = "std.div"
OP_STD_ABS = "std.abs"
OP_STD_MAX = "std.max"
OP_STD_MIN = "std.min"

# Standard comparisons
OP_STD_GT = "std.gt"
OP_STD_LT = "std.lt"
OP_STD_GTE = "std.gte"
OP_STD_LTE = "std.lte"
OP_STD_EQ = "std.eq"
OP_STD_NEQ = "std.neq"

# Control and conditionals
OP_STD_COND = "std.cond"

# Series and sequential operations
OP_STD_SERIES_REF = "std.series_ref"
OP_STD_LAG = "std.lag"
OP_STD_DELTA = "std.delta"

# Missing value handling
OP_STD_IS_MISSING = "std.is_missing"
OP_STD_COALESCE = "std.coalesce"

# Stateful recurrence accumulator
OP_STD_RECURRENCE = "std.recurrence"

UNIVERSAL_OPERATORS: frozenset[str] = frozenset(
    {
        OP_STD_ADD,
        OP_STD_SUB,
        OP_STD_MUL,
        OP_STD_DIV,
        OP_STD_ABS,
        OP_STD_MAX,
        OP_STD_MIN,
        OP_STD_GT,
        OP_STD_LT,
        OP_STD_GTE,
        OP_STD_LTE,
        OP_STD_EQ,
        OP_STD_NEQ,
        OP_STD_COND,
        OP_STD_SERIES_REF,
        OP_STD_LAG,
        OP_STD_DELTA,
        OP_STD_IS_MISSING,
        OP_STD_COALESCE,
        OP_STD_RECURRENCE,
    }
)


def validate_operator(op: str) -> str:
    """Validate that an operator belongs to the universal std.* namespace.

    The operator must match ``std.<identifier>`` and be a member of
    ``UNIVERSAL_OPERATORS``; the ``std.*`` namespace is reserved for the
    shared metamodel and cannot be extended by plugins.

    Args:
        op: Operator identifier string.

    Returns:
        The validated operator string.

    Raises:
        TypeError: If ``op`` is not a string.
        ValueError: If ``op`` violates the ``std.*`` pattern or is not one
            of the known universal operators.
    """
    if not isinstance(op, str):
        raise TypeError(f"Operator must be a string, got {type(op).__name__}")
    if not OPERATOR_NAMESPACE_PATTERN.match(op):
        raise ValueError(f"Operator must belong to universal std.* namespace: {op!r}")
    if op not in UNIVERSAL_OPERATORS:
        raise ValueError(f"Unknown universal semantic operator: {op!r}")
    return op


@dataclass(frozen=True, slots=True)
class ValueRef:
    """Reference to an output port of a preceding IR node or program input.

    Frozen and slotted. Validation in ``__post_init__``: ``node_id`` is a
    non-empty string and ``output_key`` is a bounded lowercase identifier.
    """

    node_id: str
    output_key: str

    def __post_init__(self) -> None:
        """Validate value reference."""
        if not isinstance(self.node_id, str) or not self.node_id:
            raise ValueError("ValueRef node_id must be a non-empty string")
        validate_identifier(self.output_key, "ValueRef output_key")


@dataclass(frozen=True, slots=True)
class LiteralRef:
    """Literal constant input value in IR.

    Frozen and slotted. Validation in ``__post_init__``: ``value`` is
    replaced by its ``freeze_value`` representation, so stored literals
    are always immutable and bounded.
    """

    value: Value

    def __post_init__(self) -> None:
        """Validate frozen literal value."""
        object.__setattr__(self, "value", freeze_value(self.value))


type IRArgument = ValueRef | LiteralRef


@dataclass(frozen=True, slots=True)
class ProgramInput:
    """Declared input to a SemanticProgram.

    Frozen and slotted. Validation in ``__post_init__``: ``key`` is a
    bounded lowercase identifier, ``kind`` is a ``ValueKind``, and
    ``unit`` and ``alignment`` are the corresponding enums.
    """

    key: str
    kind: ValueKind
    unit: Unit = Unit.NONE
    alignment: Alignment = Alignment.NONE

    def __post_init__(self) -> None:
        """Validate program input."""
        validate_identifier(self.key, "ProgramInput key")
        if not isinstance(self.kind, ValueKind):
            raise TypeError("ProgramInput kind must be a ValueKind")
        if not isinstance(self.unit, Unit):
            raise TypeError("ProgramInput unit must be a Unit")
        if not isinstance(self.alignment, Alignment):
            raise TypeError("ProgramInput alignment must be an Alignment")


@dataclass(frozen=True, slots=True)
class IRNode:
    """One immutable node in a SemanticProgram.

    Frozen and slotted. Validation in ``__post_init__``: ``id`` is a
    non-empty string, ``operator`` passes ``validate_operator``,
    ``inputs`` is a tuple of ``ValueRef``/``LiteralRef`` arguments,
    ``parameters`` is a ``FrozenObject``, and ``outputs`` is a non-empty
    tuple of unique bounded identifiers.
    """

    id: str
    operator: str
    inputs: tuple[IRArgument, ...] = ()
    parameters: FrozenObject = EMPTY_FROZEN_OBJECT
    outputs: tuple[str, ...] = ("out",)

    def __post_init__(self) -> None:
        """Validate IRNode structure."""
        if not isinstance(self.id, str) or not self.id:
            raise ValueError("IRNode id must be a non-empty string")
        validate_operator(self.operator)
        if not isinstance(self.inputs, tuple):
            raise TypeError("IRNode inputs must be a tuple")
        for inp in self.inputs:
            if not isinstance(inp, (ValueRef, LiteralRef)):
                raise TypeError(
                    f"IRNode input must be ValueRef or LiteralRef, "
                    f"got {type(inp).__name__}"
                )
        if not isinstance(self.parameters, FrozenObject):
            raise TypeError("IRNode parameters must be a FrozenObject")
        if not isinstance(self.outputs, tuple) or not self.outputs:
            raise ValueError("IRNode outputs must be non-empty tuple of keys")
        seen_outputs: set[str] = set()
        for out in self.outputs:
            validate_identifier(out, "IRNode output key")
            if out in seen_outputs:
                raise ValueError(f"Duplicate output key {out!r} on IRNode {self.id!r}")
            seen_outputs.add(out)


@dataclass(frozen=True, slots=True)
class ProgramOutput:
    """Declared output of a SemanticProgram.

    Frozen and slotted. Validation in ``__post_init__``: ``key`` is a
    bounded lowercase identifier, ``source`` is a ``ValueRef``, ``kind``
    is a ``ValueKind``, and ``unit`` and ``alignment`` are the
    corresponding enums.
    """

    key: str
    source: ValueRef
    kind: ValueKind
    unit: Unit = Unit.NONE
    alignment: Alignment = Alignment.NONE

    def __post_init__(self) -> None:
        """Validate program output."""
        validate_identifier(self.key, "ProgramOutput key")
        if not isinstance(self.source, ValueRef):
            raise TypeError("ProgramOutput source must be a ValueRef")
        if not isinstance(self.kind, ValueKind):
            raise TypeError("ProgramOutput kind must be a ValueKind")
        if not isinstance(self.unit, Unit):
            raise TypeError("ProgramOutput unit must be a Unit")
        if not isinstance(self.alignment, Alignment):
            raise TypeError("ProgramOutput alignment must be an Alignment")


def _validate_program_nodes(
    nodes: tuple[IRNode, ...],
    input_keys: set[str],
    available_refs: set[tuple[str, str]],
) -> None:
    """Validate program nodes and dependency resolution.

    Node IDs must be unique and disjoint from input keys, and every
    ``ValueRef`` must resolve to a program input or the output of an
    already-seen (preceding) node.
    """
    seen_node_ids: set[str] = set()
    for node in nodes:
        if node.id in seen_node_ids or node.id in input_keys:
            raise ValueError(f"Duplicate IR node ID: {node.id!r}")
        seen_node_ids.add(node.id)

        for arg in node.inputs:
            if (
                isinstance(arg, ValueRef)
                and (arg.node_id, arg.output_key) not in available_refs
            ):
                raise ValueError(
                    f"Node {node.id!r} references unknown output: "
                    f"{arg.node_id}:{arg.output_key}"
                )
        for out in node.outputs:
            available_refs.add((node.id, out))


def _validate_program_outputs(
    outputs: tuple[ProgramOutput, ...],
    available_refs: set[tuple[str, str]],
) -> None:
    """Validate program outputs against available references.

    Output keys must be unique and every output source must resolve to a
    program input or a node output.
    """
    output_keys: set[str] = set()
    for out in outputs:
        if out.key in output_keys:
            raise ValueError(f"Duplicate program output key: {out.key!r}")
        output_keys.add(out.key)
        if (out.source.node_id, out.source.output_key) not in available_refs:
            raise ValueError(
                f"Program output {out.key!r} references unknown source: "
                f"{out.source.node_id}:{out.source.output_key}"
            )


@dataclass(frozen=True, slots=True)
class SemanticProgram:
    """Complete, bounded semantic intermediate representation.

    Frozen and slotted. The node tuple is an ordered DAG: a node may only
    reference program inputs or outputs of preceding nodes, so node order
    defines a valid evaluation order and cycles are impossible by
    construction. Program inputs are addressable as ``(key, key)`` and
    ``(key, "out")``.

    Validation in ``__post_init__``:

    - ``ir_schema_version`` equals ``IR_SCHEMA_VERSION`` (currently 1);
    - at most ``MAX_IR_NODES`` (10,000) nodes;
    - input keys and output keys are unique;
    - node IDs are unique and disjoint from input keys;
    - every ``ValueRef`` resolves against the ordered view of inputs and
      preceding node outputs.
    """

    inputs: tuple[ProgramInput, ...]
    nodes: tuple[IRNode, ...]
    outputs: tuple[ProgramOutput, ...]
    ir_schema_version: int = IR_SCHEMA_VERSION

    def __post_init__(self) -> None:
        """Validate schema version, unique identifiers, and DAG reference validity."""
        if self.ir_schema_version != IR_SCHEMA_VERSION:
            raise ValueError(
                f"Unsupported IR schema version {self.ir_schema_version}; "
                f"expected {IR_SCHEMA_VERSION}"
            )
        if len(self.nodes) > MAX_IR_NODES:
            raise ValueError(f"Program exceeds maximum IR nodes {MAX_IR_NODES}")

        input_keys: set[str] = set()
        for inp in self.inputs:
            if inp.key in input_keys:
                raise ValueError(f"Duplicate program input key: {inp.key!r}")
            input_keys.add(inp.key)

        available_refs: set[tuple[str, str]] = set()
        for inp in self.inputs:
            available_refs.add((inp.key, inp.key))
            available_refs.add((inp.key, "out"))

        _validate_program_nodes(self.nodes, input_keys, available_refs)
        _validate_program_outputs(self.outputs, available_refs)


@dataclass(frozen=True, slots=True)
class LoweringTarget:
    """Exact lowering target identifier and version.

    Frozen and slotted. Matching is exact: a lowering implementation
    supports a target only when both ``target_id`` and the full
    ``(major, minor, patch)`` version compare equal. Validation in
    ``__post_init__``: ``target_id`` is a bounded lowercase identifier and
    ``version`` is a 3-tuple of non-negative integers.
    """

    target_id: str
    version: tuple[int, int, int]

    def __post_init__(self) -> None:
        """Validate lowering target."""
        validate_identifier(self.target_id, "LoweringTarget target_id")
        if (
            not isinstance(self.version, tuple)
            or len(self.version) != SEMVER_PART_COUNT
        ):
            raise TypeError(
                "LoweringTarget version must be a 3-tuple of (major, minor, patch)"
            )
        for num in self.version:
            if not isinstance(num, int) or num < 0:
                raise ValueError("Version components must be non-negative integers")


@dataclass(frozen=True, slots=True)
class LoweringIssue:
    """Attributed lowering issue with reason and optional node attribution.

    Frozen and slotted. Validation in ``__post_init__``: ``code`` and
    ``message`` are non-empty strings and ``node_id`` is a string or None.
    """

    code: str
    message: str
    node_id: str | None = None

    def __post_init__(self) -> None:
        """Validate lowering issue fields."""
        if not isinstance(self.code, str) or not self.code:
            raise ValueError("LoweringIssue code must be a non-empty string")
        if not isinstance(self.message, str) or not self.message:
            raise ValueError("LoweringIssue message must be a non-empty string")
        if self.node_id is not None and not isinstance(self.node_id, str):
            raise TypeError("LoweringIssue node_id must be a string or None")


@dataclass(frozen=True, slots=True)
class LoweringResult:
    """Result of lowering an operation or graph to a target SemanticProgram.

    Frozen and slotted. Validation in ``__post_init__``: ``success`` is a
    bool, a successful result carries a non-None ``SemanticProgram``, and
    ``issues`` is a tuple.
    """

    success: bool
    program: SemanticProgram | None = None
    issues: tuple[LoweringIssue, ...] = ()

    def __post_init__(self) -> None:
        """Validate lowering result."""
        if not isinstance(self.success, bool):
            raise TypeError("LoweringResult success must be a bool")
        if self.success and self.program is None:
            raise ValueError("Successful LoweringResult must contain a SemanticProgram")
        if not isinstance(self.issues, tuple):
            raise TypeError("LoweringResult issues must be a tuple")


class LoweringContext(Protocol):
    """Protocol for the host-provided context of an operation lowering.

    ``allocate_node_id`` must return deterministic, collision-free node
    IDs so that lowering the same parameters twice produces identical
    programs.
    """

    @property
    def target(self) -> LoweringTarget:
        """Return the target to which code is being lowered."""
        ...

    def allocate_node_id(self, prefix: str = "node") -> str:
        """Allocate a deterministic, unique node ID for the lowered program.

        Args:
            prefix: Stable prefix for the generated identifier.

        Returns:
            A node ID distinct from every previously allocated one.
        """
        ...

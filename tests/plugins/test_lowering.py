"""Unit tests for app.plugins.lowering: universal IR, operators, and lowering protocols."""

import pytest
from app.plugins.lowering import (
    IR_SCHEMA_VERSION,
    OP_STD_ADD,
    OP_STD_DELTA,
    OP_STD_GT,
    OP_STD_RECURRENCE,
    OP_STD_SERIES_REF,
    IRNode,
    LiteralRef,
    LoweringIssue,
    LoweringResult,
    LoweringTarget,
    ProgramInput,
    ProgramOutput,
    SemanticProgram,
    ValueRef,
    validate_operator,
)
from app.plugins.schema import Alignment, Unit, ValueKind


def test_validate_operator() -> None:
    assert validate_operator("std.add") == OP_STD_ADD
    assert validate_operator("std.gt") == OP_STD_GT
    assert validate_operator("std.recurrence") == OP_STD_RECURRENCE

    with pytest.raises(ValueError, match=r"universal std\.\* namespace"):
        validate_operator("rsi")
    with pytest.raises(ValueError, match="Unknown universal"):
        validate_operator("std.unknown_op_foo")


def test_lowering_target_and_issue() -> None:
    target = LoweringTarget(target_id="python", version=(1, 0, 0))
    assert target.target_id == "python"
    assert target.version == (1, 0, 0)

    with pytest.raises(ValueError, match="non-negative"):
        LoweringTarget(target_id="python", version=(-1, 0, 0))

    issue = LoweringIssue(
        code="UNSUPPORTED_OP", message="Operator not supported", node_id="n1"
    )
    assert issue.code == "UNSUPPORTED_OP"
    assert issue.node_id == "n1"


def test_semantic_program_construction_and_validation() -> None:
    inp = ProgramInput(
        key="price",
        kind=ValueKind.ALIGNED_SERIES,
        unit=Unit.NONE,
        alignment=Alignment.INDEX,
    )
    node1 = IRNode(
        id="n1",
        operator=OP_STD_DELTA,
        inputs=(ValueRef("price", "price"),),
        outputs=("out",),
    )
    node2 = IRNode(
        id="n2",
        operator=OP_STD_ADD,
        inputs=(ValueRef("n1", "out"), LiteralRef(1.0)),
        outputs=("out",),
    )
    out = ProgramOutput(
        key="res",
        source=ValueRef("n2", "out"),
        kind=ValueKind.ALIGNED_SERIES,
    )

    prog = SemanticProgram(
        inputs=(inp,),
        nodes=(node1, node2),
        outputs=(out,),
    )
    assert prog.ir_schema_version == IR_SCHEMA_VERSION
    assert len(prog.nodes) == 2


def test_semantic_program_rejects_unknown_reference() -> None:
    inp = ProgramInput(key="price", kind=ValueKind.ALIGNED_SERIES)
    node = IRNode(
        id="n1",
        operator=OP_STD_ADD,
        inputs=(ValueRef("unknown_node", "out"),),
    )
    out = ProgramOutput(key="res", source=ValueRef("n1", "out"), kind=ValueKind.NUMBER)

    with pytest.raises(ValueError, match="references unknown output"):
        SemanticProgram(inputs=(inp,), nodes=(node,), outputs=(out,))


def test_semantic_program_rejects_duplicate_node_ids() -> None:
    inp = ProgramInput(key="price", kind=ValueKind.ALIGNED_SERIES)
    node1 = IRNode(
        id="n1", operator=OP_STD_SERIES_REF, inputs=(ValueRef("price", "price"),)
    )
    node2 = IRNode(
        id="n1", operator=OP_STD_SERIES_REF, inputs=(ValueRef("price", "price"),)
    )
    out = ProgramOutput(
        key="res", source=ValueRef("n1", "out"), kind=ValueKind.ALIGNED_SERIES
    )

    with pytest.raises(ValueError, match="Duplicate IR node ID"):
        SemanticProgram(inputs=(inp,), nodes=(node1, node2), outputs=(out,))


def test_lowering_result_validation() -> None:
    inp = ProgramInput(key="x", kind=ValueKind.NUMBER)
    node = IRNode(
        id="n1", operator=OP_STD_ADD, inputs=(ValueRef("x", "x"), LiteralRef(2.0))
    )
    out = ProgramOutput(key="y", source=ValueRef("n1", "out"), kind=ValueKind.NUMBER)
    prog = SemanticProgram(inputs=(inp,), nodes=(node,), outputs=(out,))

    res = LoweringResult(success=True, program=prog)
    assert res.success is True
    assert res.program == prog

    with pytest.raises(ValueError, match="Successful LoweringResult must contain"):
        LoweringResult(success=True, program=None)

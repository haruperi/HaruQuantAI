"""Unit tests for app.plugins.wire: strict JSON parse, canonical encoding, and round-trip projections."""

import pytest
from app.plugins.algebra import GraphDocument, GraphSpec, NodeSpec, OpaqueGraphDocument
from app.plugins.lowering import (
    IRNode,
    LiteralRef,
    ProgramInput,
    ProgramOutput,
    SemanticProgram,
    ValueRef,
)
from app.plugins.schema import (
    FrozenObject,
    MissingValue,
    NumericConstraint,
    ParameterSchema,
    ParameterSpec,
    PortSpec,
    PresentationHint,
    ValueKind,
    WidgetKind,
)
from app.plugins.spec import CatalogEntryView, CatalogView, OperationSpec, PluginRef
from app.plugins.wire import (
    catalog_view_from_wire,
    catalog_view_to_wire,
    graph_document_from_wire,
    graph_document_to_wire,
    operation_spec_from_wire,
    operation_spec_to_wire,
    parameter_spec_from_wire,
    parameter_spec_to_wire,
    parse_strict_json,
    semantic_program_from_wire,
    semantic_program_to_wire,
    sha256_canonical,
    to_canonical_json_bytes,
    value_from_wire,
    value_to_wire,
)


def test_parse_strict_json_rejects_duplicate_keys() -> None:
    raw = '{"key": 1, "key": 2}'
    with pytest.raises(ValueError, match="Duplicate JSON key"):
        parse_strict_json(raw)


def test_parse_strict_json_rejects_non_finite_numbers() -> None:
    for raw in ('{"val": NaN}', '{"val": Infinity}', '{"val": -Infinity}'):
        with pytest.raises(ValueError, match="Non-finite"):
            parse_strict_json(raw)


def test_canonical_json_and_sha256() -> None:
    d1 = {"b": 2, "a": 1}
    d2 = {"a": 1, "b": 2}
    bytes1 = to_canonical_json_bytes(d1)
    bytes2 = to_canonical_json_bytes(d2)
    assert bytes1 == b'{"a":1,"b":2}'
    assert bytes1 == bytes2
    assert sha256_canonical(d1) == sha256_canonical(d2)


def test_value_wire_round_trip() -> None:
    val = FrozenObject.from_mapping(
        {
            "num": 42,
            "arr": [1, 2, 3],
            "missing": MissingValue("gap"),
            "sub": {"x": True},
        }
    )
    wire = value_to_wire(val)
    restored = value_from_wire(wire)
    assert restored == val


def test_parameter_spec_wire_round_trip() -> None:
    spec = ParameterSpec(
        key="period",
        kind=ValueKind.INTEGER,
        label="Period",
        default=14,
        constraint=NumericConstraint(min_value=2, max_value=1000),
        presentation=PresentationHint(widget=WidgetKind.NUMERIC_INPUT, label="Period"),
    )
    wire = parameter_spec_to_wire(spec)
    restored = parameter_spec_from_wire(wire)
    assert restored.key == spec.key
    assert restored.kind == spec.kind
    assert restored.default == spec.default
    assert restored.constraint == spec.constraint
    assert restored.presentation == spec.presentation


def test_operation_spec_wire_round_trip() -> None:
    op = OperationSpec(
        operation_id="compute",
        title="Compute RSI",
        parameters=ParameterSchema(
            (
                ParameterSpec(
                    key="period",
                    kind=ValueKind.INTEGER,
                    label="Period",
                    default=14,
                ),
            )
        ),
        inputs=(PortSpec(key="values", kind=ValueKind.ALIGNED_SERIES),),
        outputs=(PortSpec(key="rsi", kind=ValueKind.ALIGNED_SERIES),),
        effects=("pure",),
    )
    wire = operation_spec_to_wire(op)
    restored = operation_spec_from_wire(wire)
    assert restored.operation_id == op.operation_id
    assert restored.title == op.title
    assert restored.parameters.keys() == op.parameters.keys()
    assert len(restored.inputs) == 1
    assert len(restored.outputs) == 1


def test_catalog_view_wire_round_trip() -> None:
    ref = PluginRef(id="indicator.rsi", version=(1, 0, 0))
    entry = CatalogEntryView(
        ref=ref,
        kind="indicator",
        title="RSI Indicator",
        operations=(OperationSpec(operation_id="compute", title="Compute"),),
    )
    view = CatalogView(entries=(entry,), catalog_fingerprint="cat_hash_123")
    wire = catalog_view_to_wire(view)
    restored = catalog_view_from_wire(wire)
    assert len(restored.entries) == 1
    assert restored.entries[0].ref == ref
    assert restored.catalog_fingerprint == "cat_hash_123"


def test_semantic_program_wire_round_trip() -> None:
    inp = ProgramInput(key="price", kind=ValueKind.ALIGNED_SERIES)
    node = IRNode(
        id="n1",
        operator="std.add",
        inputs=(ValueRef("price", "price"), LiteralRef(1.0)),
        outputs=("out",),
    )
    out = ProgramOutput(
        key="res", source=ValueRef("n1", "out"), kind=ValueKind.ALIGNED_SERIES
    )
    prog = SemanticProgram(inputs=(inp,), nodes=(node,), outputs=(out,))

    wire = semantic_program_to_wire(prog)
    restored = semantic_program_from_wire(wire)
    assert restored.ir_schema_version == prog.ir_schema_version
    assert len(restored.nodes) == 1
    assert restored.nodes[0].operator == "std.add"


def test_graph_document_wire_round_trip() -> None:
    ref = PluginRef(id="indicator.rsi", version=(1, 0, 0))
    node = NodeSpec(
        id="rsi_1",
        plugin_ref=ref,
        operation_id="compute",
        parameters=FrozenObject.from_mapping({"period": 14}),
        extension_data=FrozenObject.from_mapping({"ui_x": 100}),
    )
    doc = GraphDocument(
        spec=GraphSpec(nodes=(node,)),
        metadata=FrozenObject.from_mapping({"author": "Haru"}),
    )
    wire = graph_document_to_wire(doc)
    restored = graph_document_from_wire(wire)
    assert isinstance(restored, GraphDocument)
    assert len(restored.spec.nodes) == 1
    assert restored.spec.nodes[0].id == "rsi_1"
    assert restored.spec.nodes[0].extension_data["ui_x"] == 100
    assert restored.metadata["author"] == "Haru"


def test_opaque_graph_document_wire_round_trip() -> None:
    wire_data = {
        "schema_version": 999,
        "custom_future_field": "preserved",
    }
    doc = graph_document_from_wire(wire_data)
    assert isinstance(doc, OpaqueGraphDocument)
    assert doc.schema_version == 999
    assert doc.raw_data["custom_future_field"] == "preserved"

    wire_again = graph_document_to_wire(doc)
    assert wire_again["schema_version"] == 999
    assert wire_again["custom_future_field"] == "preserved"


def test_wire_nesting_depth_bound_rejected() -> None:
    from app.plugins.wire import MAX_WIRE_DEPTH

    nested: list[object] = []
    root = nested
    for _ in range(MAX_WIRE_DEPTH + 1):
        child: list[object] = []
        nested.append(child)
        nested = child
    with pytest.raises(ValueError, match="nesting depth"):
        value_from_wire(root)


def test_wire_string_length_bound_rejected() -> None:
    from app.plugins.wire import MAX_WIRE_STRING_LENGTH

    with pytest.raises(ValueError, match="string length"):
        value_from_wire("x" * (MAX_WIRE_STRING_LENGTH + 1))


def test_wire_object_key_count_bound_rejected() -> None:
    from app.plugins.wire import MAX_WIRE_OBJECT_KEYS

    raw = {f"k{i}": i for i in range(MAX_WIRE_OBJECT_KEYS + 1)}
    with pytest.raises(ValueError, match="key count"):
        value_from_wire(raw)


def test_wire_array_length_bound_rejected() -> None:
    from app.plugins.wire import MAX_WIRE_ARRAY_ITEMS

    with pytest.raises(ValueError, match="array length"):
        value_from_wire([0] * (MAX_WIRE_ARRAY_ITEMS + 1))


def test_malformed_missing_markers_rejected() -> None:
    # non-bool marker
    with pytest.raises(ValueError, match="Malformed missing marker"):
        value_from_wire({"__missing__": "yes", "reason": "gap"})
    # extra keys beyond the exact marker shape
    with pytest.raises(ValueError, match="Malformed missing marker"):
        value_from_wire({"__missing__": True, "reason": "gap", "x": 1})
    # non-string reason
    with pytest.raises(TypeError, match="reason must be a string"):
        value_from_wire({"__missing__": True, "reason": 7})
    # false marker degrades to a plain object; key collision must not be
    # silently reinterpreted
    with pytest.raises(ValueError, match="Malformed missing marker"):
        value_from_wire({"__missing__": False})


def test_valid_missing_marker_round_trip() -> None:
    val = MissingValue("gap")
    restored = value_from_wire(value_to_wire(val))
    assert restored == val
    bare = value_from_wire({"__missing__": True})
    assert bare == MissingValue(reason="")


def test_parse_strict_json_deep_nesting_raises_valueerror() -> None:
    deep = "[" * 5000 + "]" * 5000
    with pytest.raises(ValueError, match="nesting depth"):
        parse_strict_json(deep)


def test_subgraph_bearing_document_decode_refused_not_dropped() -> None:
    ref = PluginRef(id="indicator.rsi", version=(1, 0, 0))
    wire_data = {
        "schema_version": 1,
        "spec": {
            "nodes": [
                {
                    "id": "rsi_1",
                    "plugin_ref": ref.to_string(),
                    "operation_id": "compute",
                    "parameters": {},
                }
            ],
            "edges": [],
            "designated_roots": [],
            "subgraphs": [{"schema_version": 1, "nodes": [], "edges": []}],
        },
        "metadata": {},
    }
    with pytest.raises(ValueError, match="subgraphs"):
        graph_document_from_wire(wire_data)


def test_subgraph_bearing_document_encode_refused_not_dropped() -> None:
    ref = PluginRef(id="indicator.rsi", version=(1, 0, 0))
    node = NodeSpec(id="rsi_1", plugin_ref=ref, operation_id="compute")
    doc = GraphDocument(
        spec=GraphSpec(
            nodes=(node,),
            subgraphs=(GraphSpec(nodes=(node,)),),
        )
    )
    with pytest.raises(ValueError, match="subgraphs"):
        graph_document_to_wire(doc)


def test_optimization_distribution_wire_round_trip() -> None:
    from app.plugins.schema import OptimizationDistribution, OptimizationDomain

    spec = ParameterSpec(
        key="period",
        kind=ValueKind.INTEGER,
        label="Period",
        default=14,
        optimization=OptimizationDomain(
            min_value=2, max_value=100, distribution=OptimizationDistribution.NORMAL
        ),
    )
    wire = parameter_spec_to_wire(spec)
    assert wire["optimization"]["distribution"] == "normal"
    restored = parameter_spec_from_wire(wire)
    assert restored.optimization is not None
    assert restored.optimization.distribution is OptimizationDistribution.NORMAL

    with pytest.raises(ValueError, match="not a valid OptimizationDistribution"):
        parameter_spec_from_wire(
            {
                "key": "period",
                "kind": "integer",
                "label": "Period",
                "optimization": {
                    "eligible": True,
                    "distribution": "unknown_dist",
                },
            }
        )

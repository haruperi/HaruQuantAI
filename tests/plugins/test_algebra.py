"""Unit tests for app.plugins.algebra: graph specifications, cycle detection, and catalog validation."""

import pytest
from app.plugins.algebra import (
    EdgeSpec,
    GraphDocument,
    GraphSpec,
    NodeSpec,
    OpaqueGraphDocument,
    PortRef,
    validate_graph,
)
from app.plugins.schema import (
    Alignment,
    FrozenObject,
    NumericConstraint,
    ParameterSchema,
    ParameterSpec,
    PortSpec,
    ValueKind,
)
from app.plugins.spec import CatalogEntryView, CatalogView, OperationSpec, PluginRef


def _build_test_catalog() -> CatalogView:
    rsi_ref = PluginRef(id="indicator.rsi", version=(1, 0, 0))
    rsi_op = OperationSpec(
        operation_id="compute",
        title="RSI Compute",
        parameters=ParameterSchema(
            (
                ParameterSpec(
                    key="period",
                    kind=ValueKind.INTEGER,
                    label="Period",
                    default=14,
                    constraint=NumericConstraint(min_value=2, max_value=1000),
                ),
            )
        ),
        inputs=(
            PortSpec(
                key="values", kind=ValueKind.ALIGNED_SERIES, alignment=Alignment.INDEX
            ),
        ),
        outputs=(
            PortSpec(
                key="rsi", kind=ValueKind.ALIGNED_SERIES, alignment=Alignment.INDEX
            ),
        ),
    )
    rsi_entry = CatalogEntryView(
        ref=rsi_ref,
        kind="indicator",
        title="RSI",
        operations=(rsi_op,),
    )

    gt_ref = PluginRef(id="comparison.greater_than", version=(1, 0, 0))
    gt_op = OperationSpec(
        operation_id="compare",
        title="Greater Than",
        inputs=(
            PortSpec(
                key="left", kind=ValueKind.ALIGNED_SERIES, alignment=Alignment.INDEX
            ),
            PortSpec(
                key="right", kind=ValueKind.ALIGNED_SERIES, alignment=Alignment.INDEX
            ),
        ),
        outputs=(
            PortSpec(
                key="result", kind=ValueKind.ALIGNED_SERIES, alignment=Alignment.INDEX
            ),
        ),
    )
    gt_entry = CatalogEntryView(
        ref=gt_ref,
        kind="comparison",
        title="Greater Than",
        operations=(gt_op,),
    )

    return CatalogView(entries=(rsi_entry, gt_entry), catalog_fingerprint="cat_fp")


def test_valid_graph_document_passes_validation() -> None:
    catalog = _build_test_catalog()
    rsi_ref = PluginRef(id="indicator.rsi", version=(1, 0, 0))
    gt_ref = PluginRef(id="comparison.greater_than", version=(1, 0, 0))

    node_rsi = NodeSpec(
        id="rsi_1",
        plugin_ref=rsi_ref,
        operation_id="compute",
        parameters=FrozenObject.from_mapping({"period": 14}),
    )
    node_gt = NodeSpec(
        id="gt_1",
        plugin_ref=gt_ref,
        operation_id="compare",
    )
    edge = EdgeSpec(
        source=PortRef("rsi_1", "rsi"),
        target=PortRef("gt_1", "left"),
    )
    root = PortRef("gt_1", "result")

    doc = GraphDocument(
        spec=GraphSpec(
            nodes=(node_rsi, node_gt),
            edges=(edge,),
            designated_roots=(root,),
        )
    )

    res = validate_graph(doc, catalog)
    assert res.is_valid is True
    assert res.can_execute is True
    assert len(res.issues) == 0
    assert res.normalized_document is not None


def test_cycle_detection_in_graph() -> None:
    catalog = _build_test_catalog()
    rsi_ref = PluginRef(id="indicator.rsi", version=(1, 0, 0))
    gt_ref = PluginRef(id="comparison.greater_than", version=(1, 0, 0))

    node1 = NodeSpec(id="n1", plugin_ref=rsi_ref, operation_id="compute")
    node2 = NodeSpec(id="n2", plugin_ref=gt_ref, operation_id="compare")

    edge1 = EdgeSpec(source=PortRef("n1", "rsi"), target=PortRef("n2", "left"))
    edge2 = EdgeSpec(source=PortRef("n2", "result"), target=PortRef("n1", "values"))

    doc = GraphDocument(
        spec=GraphSpec(
            nodes=(node1, node2),
            edges=(edge1, edge2),
        )
    )

    res = validate_graph(doc, catalog)
    assert res.is_valid is False
    assert res.can_execute is False
    assert any(i.code == "GRAPH_CYCLE" for i in res.issues)


def test_self_referencing_edge_rejected_at_construction() -> None:
    with pytest.raises(ValueError, match="Self-referencing edge is forbidden"):
        EdgeSpec(source=PortRef("n1", "out"), target=PortRef("n1", "in"))


def test_unknown_plugin_node_preserves_structure_but_prevents_execution() -> None:
    catalog = _build_test_catalog()
    unknown_ref = PluginRef(id="indicator.macd", version=(1, 0, 0))

    node = NodeSpec(
        id="macd_1",
        plugin_ref=unknown_ref,
        operation_id="compute",
        parameters=FrozenObject.from_mapping({"fast": 12}),
    )
    doc = GraphDocument(spec=GraphSpec(nodes=(node,)))

    res = validate_graph(doc, catalog)
    assert res.is_valid is False
    assert res.can_execute is False
    assert any(i.code == "UNAVAILABLE_PLUGIN" for i in res.issues)

    # Node is preserved in normalized document
    assert res.normalized_document is not None
    assert len(res.normalized_document.spec.nodes) == 1
    assert res.normalized_document.spec.nodes[0].id == "macd_1"


def test_port_type_mismatch_fails_validation() -> None:
    catalog = _build_test_catalog()
    rsi_ref = PluginRef(id="indicator.rsi", version=(1, 0, 0))

    node1 = NodeSpec(id="rsi_1", plugin_ref=rsi_ref, operation_id="compute")
    node2 = NodeSpec(id="rsi_2", plugin_ref=rsi_ref, operation_id="compute")
    edge_bad = EdgeSpec(
        source=PortRef("rsi_1", "unknown_port"), target=PortRef("rsi_2", "values")
    )

    doc = GraphDocument(spec=GraphSpec(nodes=(node1, node2), edges=(edge_bad,)))
    res = validate_graph(doc, catalog)
    assert res.is_valid is False
    assert any(i.code == "UNKNOWN_PORT" for i in res.issues)


def test_opaque_graph_document_fails_execution() -> None:
    catalog = _build_test_catalog()
    opaque = OpaqueGraphDocument(
        schema_version=99,
        raw_data=FrozenObject.from_mapping({"schema_version": 99, "data": "future"}),
    )
    res = validate_graph(opaque, catalog)
    assert res.is_valid is False
    assert res.can_execute is False
    assert any(i.code == "UNSUPPORTED_VERSION" for i in res.issues)

"""Graph specifications, document models, cycle detection, and catalog validation."""

from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass

from app.plugins.schema import (
    EMPTY_FROZEN_OBJECT,
    FrozenObject,
    PortSpec,
    Unit,
    ValidationIssue,
    ValidationSeverity,
    validate_identifier,
)
from app.plugins.spec import CatalogView, PluginRef

GRAPH_SCHEMA_VERSION = 1
MAX_GRAPH_NODES = 1_000
MAX_GRAPH_EDGES = 5_000


@dataclass(frozen=True, slots=True)
class PortRef:
    """Reference to a port on a graph node."""

    node_id: str
    port_key: str

    def __post_init__(self) -> None:
        """Validate port reference."""
        if not isinstance(self.node_id, str) or not self.node_id:
            raise ValueError("PortRef node_id must be a non-empty string")
        validate_identifier(self.port_key, "PortRef port_key")


@dataclass(frozen=True, slots=True)
class EdgeSpec:
    """Directed connection from a source output port to a target input port."""

    source: PortRef
    target: PortRef

    def __post_init__(self) -> None:
        """Validate edge endpoints."""
        if not isinstance(self.source, PortRef):
            raise TypeError("EdgeSpec source must be a PortRef")
        if not isinstance(self.target, PortRef):
            raise TypeError("EdgeSpec target must be a PortRef")
        if self.source.node_id == self.target.node_id:
            raise ValueError(
                f"Self-referencing edge is forbidden on node {self.source.node_id!r}"
            )


@dataclass(frozen=True, slots=True)
class NodeSpec:
    """One immutable node in a quantitative graph."""

    id: str
    plugin_ref: PluginRef
    operation_id: str
    parameters: FrozenObject = EMPTY_FROZEN_OBJECT
    title: str = ""
    extension_data: FrozenObject = EMPTY_FROZEN_OBJECT

    def __post_init__(self) -> None:
        """Validate node specification."""
        if not isinstance(self.id, str) or not self.id:
            raise ValueError("NodeSpec id must be a non-empty string")
        if not isinstance(self.plugin_ref, PluginRef):
            raise TypeError("NodeSpec plugin_ref must be a PluginRef")
        validate_identifier(self.operation_id, "NodeSpec operation_id")
        if not isinstance(self.parameters, FrozenObject):
            raise TypeError("NodeSpec parameters must be a FrozenObject")
        if not isinstance(self.title, str):
            raise TypeError("NodeSpec title must be a string")
        if not isinstance(self.extension_data, FrozenObject):
            raise TypeError("NodeSpec extension_data must be a FrozenObject")


def _check_spec_tuples(spec: GraphSpec) -> None:
    if not isinstance(spec.nodes, tuple):
        raise TypeError("GraphSpec nodes must be a tuple")
    if len(spec.nodes) > MAX_GRAPH_NODES:
        raise ValueError(f"GraphSpec node count exceeds maximum {MAX_GRAPH_NODES}")
    if not isinstance(spec.edges, tuple):
        raise TypeError("GraphSpec edges must be a tuple")
    if len(spec.edges) > MAX_GRAPH_EDGES:
        raise ValueError(f"GraphSpec edge count exceeds maximum {MAX_GRAPH_EDGES}")
    if not isinstance(spec.designated_roots, tuple):
        raise TypeError("GraphSpec designated_roots must be a tuple")
    if not isinstance(spec.subgraphs, tuple):
        raise TypeError("GraphSpec subgraphs must be a tuple")


def _check_spec_elements(spec: GraphSpec) -> None:
    seen_node_ids: set[str] = set()
    for node in spec.nodes:
        if not isinstance(node, NodeSpec):
            raise TypeError("GraphSpec nodes must contain NodeSpec instances")
        if node.id in seen_node_ids:
            raise ValueError(f"Duplicate node ID in graph: {node.id!r}")
        seen_node_ids.add(node.id)

    for edge in spec.edges:
        if not isinstance(edge, EdgeSpec):
            raise TypeError("GraphSpec edges must contain EdgeSpec instances")

    for root in spec.designated_roots:
        if not isinstance(root, PortRef):
            raise TypeError("GraphSpec designated_roots must contain PortRef instances")


@dataclass(frozen=True, slots=True)
class GraphSpec:
    """Bounded quantitative workflow DAG specification."""

    schema_version: int = GRAPH_SCHEMA_VERSION
    nodes: tuple[NodeSpec, ...] = ()
    edges: tuple[EdgeSpec, ...] = ()
    designated_roots: tuple[PortRef, ...] = ()
    subgraphs: tuple[GraphSpec, ...] = ()

    def __post_init__(self) -> None:
        """Validate graph specification bounds."""
        if not isinstance(self.schema_version, int) or self.schema_version < 1:
            raise ValueError("GraphSpec schema_version must be an integer >= 1")
        _check_spec_tuples(self)
        _check_spec_elements(self)


@dataclass(frozen=True, slots=True)
class GraphDocument:
    """Versioned document containing a quantitative graph and metadata."""

    spec: GraphSpec
    metadata: FrozenObject = EMPTY_FROZEN_OBJECT

    def __post_init__(self) -> None:
        """Validate graph document."""
        if not isinstance(self.spec, GraphSpec):
            raise TypeError("GraphDocument spec must be a GraphSpec")
        if not isinstance(self.metadata, FrozenObject):
            raise TypeError("GraphDocument metadata must be a FrozenObject")


@dataclass(frozen=True, slots=True)
class OpaqueGraphDocument:
    """Document for unsupported versions, preserving complete raw representation."""

    schema_version: int
    raw_data: FrozenObject

    def __post_init__(self) -> None:
        """Validate opaque document."""
        if not isinstance(self.schema_version, int):
            raise TypeError("OpaqueGraphDocument schema_version must be an int")
        if not isinstance(self.raw_data, FrozenObject):
            raise TypeError("OpaqueGraphDocument raw_data must be a FrozenObject")


@dataclass(frozen=True, slots=True)
class GraphValidationResult:
    """Attributed result of validating a graph document against a catalog view."""

    is_valid: bool
    can_execute: bool
    issues: tuple[ValidationIssue, ...] = ()
    normalized_document: GraphDocument | None = None

    def __post_init__(self) -> None:
        """Validate result consistency."""
        if not isinstance(self.is_valid, bool):
            raise TypeError("is_valid must be a bool")
        if not isinstance(self.can_execute, bool):
            raise TypeError("can_execute must be a bool")
        if not isinstance(self.issues, tuple):
            raise TypeError("issues must be a tuple")


def _detect_cycles(
    nodes: tuple[NodeSpec, ...], edges: tuple[EdgeSpec, ...]
) -> list[str]:
    """Check for cycles in the directed graph using Kahn's algorithm."""
    in_degree: dict[str, int] = {node.id: 0 for node in nodes}
    adj: dict[str, list[str]] = defaultdict(list)

    for edge in edges:
        if edge.source.node_id in in_degree and edge.target.node_id in in_degree:
            adj[edge.source.node_id].append(edge.target.node_id)
            in_degree[edge.target.node_id] += 1

    queue = deque([nid for nid, deg in in_degree.items() if deg == 0])
    visited_count = 0

    while queue:
        curr = queue.popleft()
        visited_count += 1
        for nxt in adj[curr]:
            in_degree[nxt] -= 1
            if in_degree[nxt] == 0:
                queue.append(nxt)

    if visited_count < len(nodes):
        cycle_nodes = [nid for nid, deg in in_degree.items() if deg > 0]
        return [f"Cycle detected involving nodes: {sorted(cycle_nodes)}"]
    return []


def _validate_node(
    node: NodeSpec,
    catalog: CatalogView,
) -> tuple[
    list[ValidationIssue],
    bool,
    NodeSpec,
    dict[str, PortSpec] | None,
    dict[str, PortSpec] | None,
]:
    issues: list[ValidationIssue] = []
    op_spec = catalog.get_operation(node.plugin_ref, node.operation_id)
    if op_spec is None:
        entry = catalog.get_entry(node.plugin_ref)
        if entry is None:
            issues.append(
                ValidationIssue(
                    path=f"nodes.{node.id}",
                    code="UNAVAILABLE_PLUGIN",
                    message=(
                        f"Plugin {node.plugin_ref.to_string()} is not "
                        "available in the catalog"
                    ),
                )
            )
        else:
            issues.append(
                ValidationIssue(
                    path=f"nodes.{node.id}",
                    code="UNAVAILABLE_OPERATION",
                    message=(
                        f"Operation {node.operation_id!r} not found on plugin "
                        f"{node.plugin_ref.to_string()}"
                    ),
                )
            )
        return issues, False, node, None, None

    outputs = {p.key: p for p in op_spec.outputs}
    inputs = {p.key: p for p in op_spec.inputs}
    can_exec = True

    binding_result = op_spec.parameters.validate_bindings(node.parameters)
    if not binding_result.is_valid:
        can_exec = False
        issues.extend(
            ValidationIssue(
                path=f"nodes.{node.id}.parameters.{b_issue.path}",
                code=b_issue.code,
                message=b_issue.message,
                severity=b_issue.severity,
            )
            for b_issue in binding_result.issues
        )

    norm_node = NodeSpec(
        id=node.id,
        plugin_ref=node.plugin_ref,
        operation_id=node.operation_id,
        parameters=binding_result.values,
        title=node.title,
        extension_data=node.extension_data,
    )
    return issues, can_exec, norm_node, outputs, inputs


def _validate_edge_ports(
    idx: int,
    edge: EdgeSpec,
    src_ports: dict[str, PortSpec],
    tgt_ports: dict[str, PortSpec],
) -> tuple[list[ValidationIssue], bool]:
    issues: list[ValidationIssue] = []
    can_exec = True
    if edge.source.port_key not in src_ports:
        issues.append(
            ValidationIssue(
                path=f"edges[{idx}].source.port_key",
                code="UNKNOWN_PORT",
                message=(
                    f"Port {edge.source.port_key!r} not found on source "
                    f"node {edge.source.node_id!r}"
                ),
            )
        )
        return issues, False
    if edge.target.port_key not in tgt_ports:
        issues.append(
            ValidationIssue(
                path=f"edges[{idx}].target.port_key",
                code="UNKNOWN_PORT",
                message=(
                    f"Port {edge.target.port_key!r} not found on target "
                    f"node {edge.target.node_id!r}"
                ),
            )
        )
        return issues, False

    src_p = src_ports[edge.source.port_key]
    tgt_p = tgt_ports[edge.target.port_key]
    if src_p.kind != tgt_p.kind:
        issues.append(
            ValidationIssue(
                path=f"edges[{idx}]",
                code="PORT_TYPE_MISMATCH",
                message=f"Port type mismatch: {src_p.kind} -> {tgt_p.kind}",
            )
        )
        can_exec = False

    # Unit compatibility: exact equality unless the consuming port declares
    # Unit.NONE, which accepts any source unit.
    if src_p.unit != tgt_p.unit and tgt_p.unit is not Unit.NONE:
        issues.append(
            ValidationIssue(
                path=f"edges[{idx}]",
                code="PORT_UNIT_MISMATCH",
                message=(
                    f"Port unit mismatch: {edge.source.node_id}."
                    f"{edge.source.port_key} produces {src_p.unit.value} but "
                    f"{edge.target.node_id}.{edge.target.port_key} requires "
                    f"{tgt_p.unit.value}"
                ),
            )
        )
        can_exec = False

    none_alignment = src_p.alignment.NONE
    if src_p.alignment != tgt_p.alignment and none_alignment not in (
        src_p.alignment,
        tgt_p.alignment,
    ):
        issues.append(
            ValidationIssue(
                path=f"edges[{idx}]",
                code="PORT_ALIGNMENT_MISMATCH",
                message=(
                    f"Port alignment mismatch: {src_p.alignment} != {tgt_p.alignment}"
                ),
            )
        )
        can_exec = False
    return issues, can_exec


def _validate_edges(
    edges: tuple[EdgeSpec, ...],
    node_map: dict[str, NodeSpec],
    known_outputs: dict[str, dict[str, PortSpec]],
    known_inputs: dict[str, dict[str, PortSpec]],
) -> tuple[list[ValidationIssue], bool]:
    issues: list[ValidationIssue] = []
    can_exec = True
    for idx, edge in enumerate(edges):
        src_id = edge.source.node_id
        tgt_id = edge.target.node_id
        if src_id not in node_map:
            issues.append(
                ValidationIssue(
                    path=f"edges[{idx}].source",
                    code="UNKNOWN_NODE",
                    message=f"Source node {src_id!r} does not exist in graph",
                )
            )
            can_exec = False
        if tgt_id not in node_map:
            issues.append(
                ValidationIssue(
                    path=f"edges[{idx}].target",
                    code="UNKNOWN_NODE",
                    message=f"Target node {tgt_id!r} does not exist in graph",
                )
            )
            can_exec = False
        if src_id in known_outputs and tgt_id in known_inputs:
            p_issues, p_can = _validate_edge_ports(
                idx, edge, known_outputs[src_id], known_inputs[tgt_id]
            )
            issues.extend(p_issues)
            if not p_can:
                can_exec = False
    return issues, can_exec


def _validate_roots(
    roots: tuple[PortRef, ...],
    node_map: dict[str, NodeSpec],
    known_outputs: dict[str, dict[str, PortSpec]],
) -> tuple[list[ValidationIssue], bool]:
    issues: list[ValidationIssue] = []
    can_exec = True
    for idx, root in enumerate(roots):
        if root.node_id not in node_map:
            issues.append(
                ValidationIssue(
                    path=f"designated_roots[{idx}]",
                    code="UNKNOWN_ROOT_NODE",
                    message=f"Root node {root.node_id!r} not found in graph",
                )
            )
            can_exec = False
        elif (
            root.node_id in known_outputs
            and root.port_key not in known_outputs[root.node_id]
        ):
            issues.append(
                ValidationIssue(
                    path=f"designated_roots[{idx}]",
                    code="UNKNOWN_ROOT_PORT",
                    message=(
                        f"Port {root.port_key!r} not found on root "
                        f"node {root.node_id!r}"
                    ),
                )
            )
            can_exec = False
    return issues, can_exec


def _validate_all_nodes(
    nodes: tuple[NodeSpec, ...],
    catalog: CatalogView,
) -> tuple[
    list[ValidationIssue],
    bool,
    list[NodeSpec],
    dict[str, dict[str, PortSpec]],
    dict[str, dict[str, PortSpec]],
]:
    issues: list[ValidationIssue] = []
    can_exec = True
    known_outputs: dict[str, dict[str, PortSpec]] = {}
    known_inputs: dict[str, dict[str, PortSpec]] = {}
    normalized_nodes: list[NodeSpec] = []
    for node in nodes:
        n_issues, n_exec, n_norm, n_out, n_in = _validate_node(node, catalog)
        issues.extend(n_issues)
        if not n_exec:
            can_exec = False
        normalized_nodes.append(n_norm)
        if n_out is not None:
            known_outputs[node.id] = n_out
        if n_in is not None:
            known_inputs[node.id] = n_in
    return issues, can_exec, normalized_nodes, known_outputs, known_inputs


def validate_graph(
    doc: GraphDocument | OpaqueGraphDocument,
    catalog: CatalogView,
) -> GraphValidationResult:
    """Validate a graph document against an immutable catalog view."""
    if isinstance(doc, OpaqueGraphDocument):
        issue = ValidationIssue(
            path="schema_version",
            code="UNSUPPORTED_VERSION",
            message=(
                f"Unsupported graph schema version {doc.schema_version}; "
                "document is read-only"
            ),
            severity=ValidationSeverity.ERROR,
        )
        return GraphValidationResult(
            is_valid=False,
            can_execute=False,
            issues=(issue,),
            normalized_document=None,
        )

    if not isinstance(doc, GraphDocument):
        raise TypeError("doc must be a GraphDocument or OpaqueGraphDocument")

    spec = doc.spec
    if spec.schema_version != GRAPH_SCHEMA_VERSION:
        issue = ValidationIssue(
            path="spec.schema_version",
            code="UNSUPPORTED_VERSION",
            message=(
                f"GraphSpec version {spec.schema_version} differs from "
                f"supported {GRAPH_SCHEMA_VERSION}"
            ),
            severity=ValidationSeverity.ERROR,
        )
        return GraphValidationResult(
            is_valid=False,
            can_execute=False,
            issues=(issue,),
            normalized_document=None,
        )

    issues: list[ValidationIssue] = []
    can_execute = True

    if spec.subgraphs:
        issues.append(
            ValidationIssue(
                path="spec.subgraphs",
                code="SUBGRAPHS_UNSUPPORTED",
                message=(
                    "Graph schema version 1 does not support nested subgraphs; "
                    f"{len(spec.subgraphs)} subgraph(s) present"
                ),
                severity=ValidationSeverity.ERROR,
            )
        )
        can_execute = False

    for err in _detect_cycles(spec.nodes, spec.edges):
        issues.append(ValidationIssue(path="edges", code="GRAPH_CYCLE", message=err))
        can_execute = False

    node_map = {n.id: n for n in spec.nodes}
    n_issues, n_exec, norm_nodes, known_outputs, known_inputs = _validate_all_nodes(
        spec.nodes, catalog
    )
    issues.extend(n_issues)
    if not n_exec:
        can_execute = False

    e_issues, e_exec = _validate_edges(
        spec.edges, node_map, known_outputs, known_inputs
    )
    issues.extend(e_issues)
    if not e_exec:
        can_execute = False

    r_issues, r_exec = _validate_roots(spec.designated_roots, node_map, known_outputs)
    issues.extend(r_issues)
    if not r_exec:
        can_execute = False

    normalized_doc = GraphDocument(
        spec=GraphSpec(
            schema_version=spec.schema_version,
            nodes=tuple(norm_nodes),
            edges=spec.edges,
            designated_roots=spec.designated_roots,
            subgraphs=spec.subgraphs,
        ),
        metadata=doc.metadata,
    )

    return GraphValidationResult(
        is_valid=len(issues) == 0,
        can_execute=can_execute,
        issues=tuple(issues),
        normalized_document=normalized_doc,
    )

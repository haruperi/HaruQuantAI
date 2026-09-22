"""Canonical JSON projection, SHA-256 fingerprinting, and wire serialization."""

from __future__ import annotations

import hashlib
import json
import math
from typing import Any

from app.plugins.algebra import (
    GRAPH_SCHEMA_VERSION,
    EdgeSpec,
    GraphDocument,
    GraphSpec,
    NodeSpec,
    OpaqueGraphDocument,
    PortRef,
)
from app.plugins.lowering import (
    IR_SCHEMA_VERSION,
    IRNode,
    LiteralRef,
    ProgramInput,
    ProgramOutput,
    SemanticProgram,
    ValueRef,
)
from app.plugins.schema import (
    Alignment,
    EnumChoice,
    EnumConstraint,
    FrozenArray,
    FrozenObject,
    MissingValue,
    NumericalPolicy,
    NumericConstraint,
    OptimizationDomain,
    OptimizationScale,
    ParameterSchema,
    ParameterSpec,
    PortSpec,
    PresentationHint,
    TextConstraint,
    Unit,
    Value,
    ValueKind,
    WidgetKind,
    freeze_value,
)
from app.plugins.spec import (
    CatalogEntryView,
    CatalogView,
    OperationSpec,
    PluginRef,
)

MAX_WIRE_BYTES = 10_000_000  # 10 MB maximum payload


def _duplicate_key_pairs_hook(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    """Parse JSON object pairs, strictly rejecting duplicate keys."""
    seen: set[str] = set()
    result: dict[str, Any] = {}
    for key, val in pairs:
        if key in seen:
            raise ValueError(f"Duplicate JSON key rejected: {key!r}")
        seen.add(key)
        result[key] = val
    return result


def _reject_nan_inf(val: str) -> None:
    """Reject non-finite numeric literals in JSON parsing."""
    raise ValueError(f"Non-finite numeric constant {val!r} rejected in JSON")


def parse_strict_json(raw_json: str | bytes) -> Any:
    """Parse UTF-8 JSON strictly, rejecting duplicate keys and non-finite numbers."""
    if isinstance(raw_json, bytes):
        if len(raw_json) > MAX_WIRE_BYTES:
            raise ValueError(
                f"Payload size {len(raw_json)} exceeds maximum {MAX_WIRE_BYTES}"
            )
        text = raw_json.decode("utf-8")
    elif isinstance(raw_json, str):
        if len(raw_json.encode("utf-8")) > MAX_WIRE_BYTES:
            raise ValueError("Payload size exceeds maximum allowed wire bytes")
        text = raw_json
    else:
        raise TypeError(f"Expected str or bytes, got {type(raw_json).__name__}")

    return json.loads(
        text,
        object_pairs_hook=_duplicate_key_pairs_hook,
        parse_constant=_reject_nan_inf,
    )


def to_canonical_json_bytes(data: Any) -> bytes:
    """Serialize a JSON structure to canonical sorted-key compact UTF-8 bytes."""
    serialized = json.dumps(
        data,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )
    return serialized.encode("utf-8")


def sha256_canonical(data: Any) -> str:
    """Calculate the SHA-256 hex digest of a value's canonical JSON representation."""
    canonical_bytes = to_canonical_json_bytes(data)
    return hashlib.sha256(canonical_bytes).hexdigest()


def value_to_wire(val: Value) -> Any:
    """Project an immutable Value to JSON-serializable primitives."""
    if val is None or isinstance(val, (bool, int, str)):
        return val
    if isinstance(val, float):
        if not math.isfinite(val):
            raise ValueError("Non-finite float cannot be projected to wire")
        return val
    if isinstance(val, MissingValue):
        return {"__missing__": True, "reason": val.reason}
    if isinstance(val, FrozenArray):
        return [value_to_wire(item) for item in val.items]
    if isinstance(val, FrozenObject):
        return {k: value_to_wire(v) for k, v in val.entries}
    raise TypeError(f"Unsupported value type for wire projection: {type(val).__name__}")


def value_from_wire(raw: Any) -> Value:
    """Reconstruct an immutable Value from decoded JSON primitives."""
    if raw is None or isinstance(raw, (bool, int, str)):
        return raw
    if isinstance(raw, float):
        if not math.isfinite(raw):
            raise ValueError("Non-finite float rejected from wire")
        return raw
    if isinstance(raw, dict):
        if raw.get("__missing__") is True:
            return MissingValue(reason=str(raw.get("reason", "")))
        pairs = [(k, value_from_wire(v)) for k, v in raw.items()]
        pairs.sort(key=lambda p: p[0])
        return FrozenObject(tuple(pairs))
    if isinstance(raw, list):
        return FrozenArray(tuple(value_from_wire(item) for item in raw))
    raise TypeError(f"Unsupported wire structure: {type(raw).__name__}")


# ---------------------------------------------------------------------------
# Schema & Descriptors Projections
# ---------------------------------------------------------------------------


def parameter_spec_to_wire(spec: ParameterSpec) -> dict[str, Any]:
    """Project ParameterSpec to wire dictionary."""
    result: dict[str, Any] = {
        "key": spec.key,
        "kind": spec.kind.value,
        "label": spec.label,
        "description": spec.description,
        "required": spec.required,
    }
    if spec.default is not None:
        result["default"] = value_to_wire(spec.default)
    if spec.constraint is not None:
        if isinstance(spec.constraint, NumericConstraint):
            result["constraint"] = {
                "type": "numeric",
                "min_value": spec.constraint.min_value,
                "max_value": spec.constraint.max_value,
                "step": spec.constraint.step,
                "allow_negative": spec.constraint.allow_negative,
            }
        elif isinstance(spec.constraint, TextConstraint):
            result["constraint"] = {
                "type": "text",
                "min_length": spec.constraint.min_length,
                "max_length": spec.constraint.max_length,
                "pattern": spec.constraint.pattern,
            }
        elif isinstance(spec.constraint, EnumConstraint):
            result["constraint"] = {
                "type": "enum",
                "choices": [
                    {"value": c.value, "label": c.label, "description": c.description}
                    for c in spec.constraint.choices
                ],
            }
    if spec.optimization is not None:
        result["optimization"] = {
            "eligible": spec.optimization.eligible,
            "min_value": spec.optimization.min_value,
            "max_value": spec.optimization.max_value,
            "step": spec.optimization.step,
            "scale": spec.optimization.scale.value,
        }
    if spec.presentation is not None:
        result["presentation"] = {
            "widget": spec.presentation.widget.value,
            "group": spec.presentation.group,
            "order": spec.presentation.order,
            "label": spec.presentation.label,
            "help_text": spec.presentation.help_text,
        }
    return result


def parameter_spec_from_wire(data: dict[str, Any]) -> ParameterSpec:
    """Decode ParameterSpec from wire dictionary."""
    constraint: NumericConstraint | TextConstraint | EnumConstraint | None = None
    if "constraint" in data and data["constraint"] is not None:
        cdata = data["constraint"]
        ctype = cdata.get("type")
        if ctype == "numeric":
            constraint = NumericConstraint(
                min_value=cdata.get("min_value"),
                max_value=cdata.get("max_value"),
                step=cdata.get("step"),
                allow_negative=cdata.get("allow_negative", True),
            )
        elif ctype == "text":
            constraint = TextConstraint(
                min_length=cdata.get("min_length", 0),
                max_length=cdata.get("max_length", 256),
                pattern=cdata.get("pattern"),
            )
        elif ctype == "enum":
            choices = tuple(
                EnumChoice(
                    value=c["value"],
                    label=c["label"],
                    description=c.get("description", ""),
                )
                for c in cdata.get("choices", [])
            )
            constraint = EnumConstraint(choices=choices)

    optimization: OptimizationDomain | None = None
    if "optimization" in data and data["optimization"] is not None:
        odata = data["optimization"]
        optimization = OptimizationDomain(
            eligible=odata.get("eligible", True),
            min_value=odata.get("min_value"),
            max_value=odata.get("max_value"),
            step=odata.get("step"),
            scale=OptimizationScale(odata.get("scale", "linear")),
        )

    presentation: PresentationHint | None = None
    if "presentation" in data and data["presentation"] is not None:
        pdata = data["presentation"]
        presentation = PresentationHint(
            widget=WidgetKind(pdata["widget"]),
            group=pdata.get("group", ""),
            order=pdata.get("order", 0),
            label=pdata.get("label", ""),
            help_text=pdata.get("help_text", ""),
        )

    default_val = None
    if "default" in data and data["default"] is not None:
        default_val = value_from_wire(data["default"])

    return ParameterSpec(
        key=data["key"],
        kind=ValueKind(data["kind"]),
        label=data["label"],
        description=data.get("description", ""),
        required=data.get("required", True),
        default=default_val,
        constraint=constraint,
        optimization=optimization,
        presentation=presentation,
    )


def port_spec_to_wire(port: PortSpec) -> dict[str, Any]:
    """Project PortSpec to wire dictionary."""
    return {
        "key": port.key,
        "kind": port.kind.value,
        "unit": port.unit.value,
        "alignment": port.alignment.value,
        "label": port.label,
        "description": port.description,
    }


def port_spec_from_wire(data: dict[str, Any]) -> PortSpec:
    """Decode PortSpec from wire dictionary."""
    return PortSpec(
        key=data["key"],
        kind=ValueKind(data["kind"]),
        unit=Unit(data.get("unit", "none")),
        alignment=Alignment(data.get("alignment", "none")),
        label=data.get("label", ""),
        description=data.get("description", ""),
    )


def operation_spec_to_wire(op: OperationSpec) -> dict[str, Any]:
    """Project OperationSpec to wire dictionary."""
    return {
        "operation_id": op.operation_id,
        "title": op.title,
        "description": op.description,
        "parameters": [parameter_spec_to_wire(p) for p in op.parameters.parameters],
        "inputs": [port_spec_to_wire(p) for p in op.inputs],
        "outputs": [port_spec_to_wire(p) for p in op.outputs],
        "determinism": op.determinism,
        "numerical_policy": {
            "tolerance": op.numerical_policy.tolerance,
            "nan_policy": op.numerical_policy.nan_policy,
            "missing_policy": op.numerical_policy.missing_policy,
        },
        "effects": list(op.effects),
        "required_capabilities": list(op.required_capabilities),
        "optional_capabilities": list(op.optional_capabilities),
        "permissions": list(op.permissions),
        "lowering_targets": [
            {"target_id": t.target_id, "version": list(t.version)}
            for t in op.lowering_targets
        ],
    }


def operation_spec_from_wire(data: dict[str, Any]) -> OperationSpec:
    """Decode OperationSpec from wire dictionary."""
    from app.plugins.lowering import LoweringTarget

    params = tuple(parameter_spec_from_wire(p) for p in data.get("parameters", []))
    inputs = tuple(port_spec_from_wire(p) for p in data.get("inputs", []))
    outputs = tuple(port_spec_from_wire(p) for p in data.get("outputs", []))
    num_pol_data = data.get("numerical_policy", {})
    numerical_policy = NumericalPolicy(
        tolerance=num_pol_data.get("tolerance", 1e-9),
        nan_policy=num_pol_data.get("nan_policy", "reject"),
        missing_policy=num_pol_data.get("missing_policy", "propagate"),
    )
    lowering_targets = tuple(
        LoweringTarget(
            target_id=t["target_id"],
            version=tuple(t["version"]),
        )
        for t in data.get("lowering_targets", [])
    )

    return OperationSpec(
        operation_id=data["operation_id"],
        title=data["title"],
        description=data.get("description", ""),
        parameters=ParameterSchema(params),
        inputs=inputs,
        outputs=outputs,
        determinism=data.get("determinism", True),
        numerical_policy=numerical_policy,
        effects=tuple(data.get("effects", ["pure"])),
        required_capabilities=tuple(data.get("required_capabilities", [])),
        optional_capabilities=tuple(data.get("optional_capabilities", [])),
        permissions=tuple(data.get("permissions", [])),
        lowering_targets=lowering_targets,
    )


# ---------------------------------------------------------------------------
# Catalog View Projections
# ---------------------------------------------------------------------------


def catalog_entry_view_to_wire(entry: CatalogEntryView) -> dict[str, Any]:
    """Project CatalogEntryView to wire dictionary."""
    return {
        "ref": entry.ref.to_string(),
        "kind": entry.kind,
        "title": entry.title,
        "description": entry.description,
        "metamodel_major": entry.metamodel_major,
        "operations": [operation_spec_to_wire(op) for op in entry.operations],
    }


def catalog_entry_view_from_wire(data: dict[str, Any]) -> CatalogEntryView:
    """Decode CatalogEntryView from wire dictionary."""
    ref = PluginRef.parse(data["ref"])
    operations = tuple(
        operation_spec_from_wire(op) for op in data.get("operations", [])
    )
    return CatalogEntryView(
        ref=ref,
        kind=data["kind"],
        title=data["title"],
        description=data.get("description", ""),
        metamodel_major=data.get("metamodel_major", 1),
        operations=operations,
    )


def catalog_view_to_wire(view: CatalogView) -> dict[str, Any]:
    """Project CatalogView to wire dictionary."""
    return {
        "entries": [catalog_entry_view_to_wire(e) for e in view.entries],
        "catalog_fingerprint": view.catalog_fingerprint,
    }


def catalog_view_from_wire(data: dict[str, Any]) -> CatalogView:
    """Decode CatalogView from wire dictionary."""
    entries = tuple(catalog_entry_view_from_wire(e) for e in data.get("entries", []))
    return CatalogView(
        entries=entries,
        catalog_fingerprint=data.get("catalog_fingerprint", ""),
    )


# ---------------------------------------------------------------------------
# Graph Documents Projections
# ---------------------------------------------------------------------------


def graph_document_to_wire(doc: GraphDocument | OpaqueGraphDocument) -> dict[str, Any]:
    """Project GraphDocument or OpaqueGraphDocument to wire dictionary."""
    if isinstance(doc, OpaqueGraphDocument):
        return doc.raw_data.to_dict()

    spec = doc.spec
    nodes_wire: list[dict[str, Any]] = []
    for node in spec.nodes:
        node_dict: dict[str, Any] = {
            "id": node.id,
            "plugin_ref": node.plugin_ref.to_string(),
            "operation_id": node.operation_id,
            "parameters": value_to_wire(node.parameters),
            "title": node.title,
        }
        if node.extension_data:
            node_dict["extension_data"] = value_to_wire(node.extension_data)
        nodes_wire.append(node_dict)

    edges_wire = [
        {
            "source": {"node_id": e.source.node_id, "port_key": e.source.port_key},
            "target": {"node_id": e.target.node_id, "port_key": e.target.port_key},
        }
        for e in spec.edges
    ]

    roots_wire = [
        {"node_id": r.node_id, "port_key": r.port_key} for r in spec.designated_roots
    ]

    return {
        "schema_version": spec.schema_version,
        "spec": {
            "nodes": nodes_wire,
            "edges": edges_wire,
            "designated_roots": roots_wire,
            "subgraphs": [],
        },
        "metadata": value_to_wire(doc.metadata),
    }


def graph_document_from_wire(
    data: dict[str, Any],
) -> GraphDocument | OpaqueGraphDocument:
    """Decode a GraphDocument or OpaqueGraphDocument from wire dictionary."""
    schema_ver = data.get("schema_version", 1)
    if schema_ver != GRAPH_SCHEMA_VERSION:
        return OpaqueGraphDocument(
            schema_version=schema_ver,
            raw_data=freeze_value(data),  # type: ignore[arg-type]
        )

    spec_data = data.get("spec", {})
    nodes: list[NodeSpec] = []
    for n in spec_data.get("nodes", []):
        params_val = value_from_wire(n.get("parameters", {}))
        if not isinstance(params_val, FrozenObject):
            params_val = (
                FrozenObject.from_mapping(params_val)
                if isinstance(params_val, dict)
                else FrozenObject()
            )
        ext_val = value_from_wire(n.get("extension_data", {}))
        if not isinstance(ext_val, FrozenObject):
            ext_val = (
                FrozenObject.from_mapping(ext_val)
                if isinstance(ext_val, dict)
                else FrozenObject()
            )
        nodes.append(
            NodeSpec(
                id=n["id"],
                plugin_ref=PluginRef.parse(n["plugin_ref"]),
                operation_id=n["operation_id"],
                parameters=params_val,
                title=n.get("title", ""),
                extension_data=ext_val,
            )
        )

    edges: list[EdgeSpec] = [
        EdgeSpec(
            source=PortRef(
                node_id=e["source"]["node_id"], port_key=e["source"]["port_key"]
            ),
            target=PortRef(
                node_id=e["target"]["node_id"], port_key=e["target"]["port_key"]
            ),
        )
        for e in spec_data.get("edges", [])
    ]

    roots: list[PortRef] = [
        PortRef(node_id=r["node_id"], port_key=r["port_key"])
        for r in spec_data.get("designated_roots", [])
    ]

    metadata_val = value_from_wire(data.get("metadata", {}))
    if not isinstance(metadata_val, FrozenObject):
        metadata_val = (
            FrozenObject.from_mapping(metadata_val)
            if isinstance(metadata_val, dict)
            else FrozenObject()
        )

    return GraphDocument(
        spec=GraphSpec(
            schema_version=schema_ver,
            nodes=tuple(nodes),
            edges=tuple(edges),
            designated_roots=tuple(roots),
            subgraphs=(),
        ),
        metadata=metadata_val,
    )


# ---------------------------------------------------------------------------
# Semantic IR Projections
# ---------------------------------------------------------------------------


def semantic_program_to_wire(prog: SemanticProgram) -> dict[str, Any]:
    """Project SemanticProgram to wire dictionary."""
    inputs_wire = [
        {
            "key": inp.key,
            "kind": inp.kind.value,
            "unit": inp.unit.value,
            "alignment": inp.alignment.value,
        }
        for inp in prog.inputs
    ]

    nodes_wire: list[dict[str, Any]] = []
    for n in prog.nodes:
        inputs_list: list[dict[str, Any]] = []
        for arg in n.inputs:
            if isinstance(arg, ValueRef):
                inputs_list.append(
                    {
                        "type": "ref",
                        "node_id": arg.node_id,
                        "output_key": arg.output_key,
                    }
                )
            elif isinstance(arg, LiteralRef):
                inputs_list.append(
                    {"type": "literal", "value": value_to_wire(arg.value)}
                )
        nodes_wire.append(
            {
                "id": n.id,
                "operator": n.operator,
                "inputs": inputs_list,
                "parameters": value_to_wire(n.parameters),
                "outputs": list(n.outputs),
            }
        )

    outputs_wire = [
        {
            "key": out.key,
            "source": {
                "node_id": out.source.node_id,
                "output_key": out.source.output_key,
            },
            "kind": out.kind.value,
            "unit": out.unit.value,
            "alignment": out.alignment.value,
        }
        for out in prog.outputs
    ]

    return {
        "ir_schema_version": prog.ir_schema_version,
        "inputs": inputs_wire,
        "nodes": nodes_wire,
        "outputs": outputs_wire,
    }


def semantic_program_from_wire(data: dict[str, Any]) -> SemanticProgram:
    """Decode SemanticProgram from wire dictionary."""
    inputs = tuple(
        ProgramInput(
            key=inp["key"],
            kind=ValueKind(inp["kind"]),
            unit=Unit(inp.get("unit", "none")),
            alignment=Alignment(inp.get("alignment", "none")),
        )
        for inp in data.get("inputs", [])
    )

    nodes: list[IRNode] = []
    for n in data.get("nodes", []):
        ir_inputs: list[ValueRef | LiteralRef] = []
        for arg in n.get("inputs", []):
            if arg.get("type") == "ref":
                ir_inputs.append(
                    ValueRef(node_id=arg["node_id"], output_key=arg["output_key"])
                )
            elif arg.get("type") == "literal":
                ir_inputs.append(LiteralRef(value=value_from_wire(arg["value"])))
        params_val = value_from_wire(n.get("parameters", {}))
        if not isinstance(params_val, FrozenObject):
            params_val = (
                FrozenObject.from_mapping(params_val)
                if isinstance(params_val, dict)
                else FrozenObject()
            )
        nodes.append(
            IRNode(
                id=n["id"],
                operator=n["operator"],
                inputs=tuple(ir_inputs),
                parameters=params_val,
                outputs=tuple(n.get("outputs", ["out"])),
            )
        )

    outputs = tuple(
        ProgramOutput(
            key=out["key"],
            source=ValueRef(
                node_id=out["source"]["node_id"], output_key=out["source"]["output_key"]
            ),
            kind=ValueKind(out["kind"]),
            unit=Unit(out.get("unit", "none")),
            alignment=Alignment(out.get("alignment", "none")),
        )
        for out in data.get("outputs", [])
    )

    return SemanticProgram(
        ir_schema_version=data.get("ir_schema_version", IR_SCHEMA_VERSION),
        inputs=inputs,
        nodes=tuple(nodes),
        outputs=outputs,
    )

"""Canonical JSON projection, SHA-256 fingerprinting, and wire serialization.

Authority: this module owns every JSON projection of the shared plugin
metamodel, as ratified for the S2 handoff in
``docs/dev/backend_implementation_handoff_s2_s5.md``: frozen values and
missing markers, schemas and plugin specs, catalog views, semantic IR,
and supported/opaque graph documents.

Position in the shared-module import DAG
(``schema <- lowering <- spec <- algebra <- wire``): this is the only
shared module allowed to import all four shared owners. No shared module
may import ``app.host``.

Wire discipline enforced here: strict UTF-8 JSON with duplicate-key and
non-finite rejection in both directions; bounded payload bytes, nesting
depth, object/array sizes, and string lengths; sorted-key,
whitespace-free canonical JSON with SHA-256 taken over the canonical
UTF-8 bytes; deterministic round trips; complete raw retention for
unsupported graph versions; and no serialization of callables,
exceptions, paths, open resources, or other Python-specific
representations.
"""

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
    MAX_COLLECTION_SIZE,
    MAX_STRING_LENGTH,
    MAX_VALUE_DEPTH,
    Alignment,
    EnumChoice,
    EnumConstraint,
    FrozenArray,
    FrozenObject,
    MissingValue,
    NumericalPolicy,
    NumericConstraint,
    OptimizationDistribution,
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
    WorkspaceCommand,
    WorkspaceSpec,
    WorkspaceView,
)

MAX_WIRE_BYTES = 10_000_000  # 10 MB maximum payload
MAX_WIRE_DEPTH = MAX_VALUE_DEPTH
MAX_WIRE_OBJECT_KEYS = MAX_COLLECTION_SIZE
MAX_WIRE_ARRAY_ITEMS = MAX_COLLECTION_SIZE
MAX_WIRE_STRING_LENGTH = MAX_STRING_LENGTH


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
    """Parse UTF-8 JSON strictly, rejecting duplicate keys and non-finite numbers.

    Args:
        raw_json: Payload as str or bytes; bytes are decoded as strict
            UTF-8. Payloads beyond ``MAX_WIRE_BYTES`` (10 MB) are
            rejected before parsing.

    Returns:
        Parsed plain-Python structure (dict/list/str/int/float/bool or
        None).

    Raises:
        TypeError: If ``raw_json`` is neither str nor bytes.
        ValueError: If the payload exceeds the byte bound, is not valid
            UTF-8 or valid JSON, contains a duplicate object key, a
            NaN/Infinity literal, or nests deeper than
            ``MAX_WIRE_DEPTH``.
    """
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

    try:
        parsed = json.loads(
            text,
            object_pairs_hook=_duplicate_key_pairs_hook,
            parse_constant=_reject_nan_inf,
        )
    except RecursionError as err:
        raise ValueError(
            f"JSON nesting depth exceeds limit of {MAX_WIRE_DEPTH}"
        ) from err
    try:
        _check_parsed_depth(parsed, 0)
    except RecursionError as err:
        raise ValueError(
            f"JSON nesting depth exceeds limit of {MAX_WIRE_DEPTH}"
        ) from err
    return parsed


def _check_parsed_depth(node: Any, depth: int) -> None:
    """Walk a parsed JSON structure, rejecting nesting beyond the bound."""
    if depth > MAX_WIRE_DEPTH:
        raise ValueError(f"JSON nesting depth exceeds limit of {MAX_WIRE_DEPTH}")
    if isinstance(node, dict):
        for val in node.values():
            _check_parsed_depth(val, depth + 1)
    elif isinstance(node, list):
        for item in node:
            _check_parsed_depth(item, depth + 1)


def to_canonical_json_bytes(data: Any) -> bytes:
    """Serialize a JSON structure to canonical sorted-key compact UTF-8 bytes.

    Keys are sorted, separators are compact (no whitespace), non-ASCII
    characters stay literal, and non-finite floats are refused.

    Args:
        data: JSON-compatible structure.

    Returns:
        Canonical UTF-8 bytes.

    Raises:
        ValueError: If ``data`` contains a non-finite float.
    """
    serialized = json.dumps(
        data,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )
    return serialized.encode("utf-8")


def sha256_canonical(data: Any) -> str:
    """Calculate the SHA-256 hex digest of a value's canonical JSON representation.

    The digest is taken over the canonical sorted-key compact UTF-8 bytes
    produced by ``to_canonical_json_bytes``, so equal values always hash
    equally.

    Args:
        data: JSON-compatible structure.

    Returns:
        Lowercase 64-character hex digest string.
    """
    canonical_bytes = to_canonical_json_bytes(data)
    return hashlib.sha256(canonical_bytes).hexdigest()


def value_to_wire(val: Value) -> Any:
    """Project an immutable Value to JSON-serializable primitives.

    ``MissingValue`` becomes the explicit marker object
    ``{"__missing__": true, "reason": ...}``, ``FrozenArray`` becomes a
    list, ``FrozenObject`` becomes a dict, and scalars pass through.

    Args:
        val: Frozen value to project.

    Returns:
        Plain JSON-compatible structure.

    Raises:
        ValueError: If a float is non-finite.
        TypeError: If ``val`` is not one of the frozen ``Value`` types.
    """
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


def value_from_wire(raw: Any, depth: int = 0) -> Value:
    """Reconstruct an immutable Value from decoded JSON primitives.

    Enforces nesting-depth, object-key-count, array-length, and string-length
    bounds, and strictly validates explicit missing markers.

    Args:
        raw: Decoded JSON structure.
        depth: Current recursion depth; callers use the default.

    Returns:
        Frozen value (``FrozenObject``, ``FrozenArray``, or scalar).

    Raises:
        ValueError: If any bound is exceeded or a missing marker is
            malformed.
        TypeError: If a leaf is not a JSON primitive or a marker reason
            is not a string.
    """
    if depth > MAX_WIRE_DEPTH:
        raise ValueError(f"Wire nesting depth exceeds limit of {MAX_WIRE_DEPTH}")
    if isinstance(raw, dict):
        if len(raw) > MAX_WIRE_OBJECT_KEYS:
            raise ValueError(
                f"Wire object key count {len(raw)} exceeds max {MAX_WIRE_OBJECT_KEYS}"
            )
        if "__missing__" in raw:
            return _missing_value_from_wire(raw)
        pairs = [(k, value_from_wire(v, depth + 1)) for k, v in raw.items()]
        pairs.sort(key=lambda p: p[0])
        return FrozenObject(tuple(pairs))
    if isinstance(raw, list):
        if len(raw) > MAX_WIRE_ARRAY_ITEMS:
            raise ValueError(
                f"Wire array length {len(raw)} exceeds max {MAX_WIRE_ARRAY_ITEMS}"
            )
        return FrozenArray(tuple(value_from_wire(item, depth + 1) for item in raw))
    return _scalar_from_wire(raw)


def _scalar_from_wire(raw: Any) -> Value:
    """Decode a bounded scalar, rejecting non-finite floats and long strings."""
    if raw is None or isinstance(raw, (bool, int, str)):
        if isinstance(raw, str) and len(raw) > MAX_WIRE_STRING_LENGTH:
            raise ValueError(
                f"Wire string length {len(raw)} exceeds max {MAX_WIRE_STRING_LENGTH}"
            )
        return raw
    if isinstance(raw, float):
        if not math.isfinite(raw):
            raise ValueError("Non-finite float rejected from wire")
        return raw
    raise TypeError(f"Unsupported wire structure: {type(raw).__name__}")


def _missing_value_from_wire(raw: dict[str, Any]) -> MissingValue:
    """Decode an explicit missing marker, rejecting any malformed shape."""
    extra = set(raw) - {"__missing__", "reason"}
    if extra or raw["__missing__"] is not True:
        raise ValueError(
            "Malformed missing marker: expected exactly "
            '{"__missing__": true} with optional bounded string "reason"'
        )
    reason = raw.get("reason", "")
    if not isinstance(reason, str):
        raise TypeError("Malformed missing marker: reason must be a string")
    if len(reason) > MAX_WIRE_STRING_LENGTH:
        raise ValueError(
            f"Missing marker reason exceeds max length {MAX_WIRE_STRING_LENGTH}"
        )
    return MissingValue(reason=reason)


# ---------------------------------------------------------------------------
# Schema & Descriptors Projections
# ---------------------------------------------------------------------------


def parameter_spec_to_wire(spec: ParameterSpec) -> dict[str, Any]:
    """Project ParameterSpec to wire dictionary.

    Constraint, optimization, and presentation sections are emitted only
    when present; the default is emitted only when not None.

    Args:
        spec: Parameter descriptor to project.

    Returns:
        Wire dictionary.
    """
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
            "distribution": spec.optimization.distribution.value,
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
    """Decode ParameterSpec from wire dictionary.

    Absent optional fields fall back to their declared defaults; all
    validation happens in the ``ParameterSpec`` constructor.

    Args:
        data: Wire dictionary produced by ``parameter_spec_to_wire``.

    Returns:
        The reconstructed ParameterSpec.
    """
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
            distribution=OptimizationDistribution(odata.get("distribution", "uniform")),
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
    """Project PortSpec to wire dictionary.

    Args:
        port: Port descriptor to project.

    Returns:
        Flat wire dictionary with key, kind, unit, alignment, label, and
        description.
    """
    return {
        "key": port.key,
        "kind": port.kind.value,
        "unit": port.unit.value,
        "alignment": port.alignment.value,
        "label": port.label,
        "description": port.description,
    }


def port_spec_from_wire(data: dict[str, Any]) -> PortSpec:
    """Decode PortSpec from wire dictionary.

    Args:
        data: Wire dictionary produced by ``port_spec_to_wire``.

    Returns:
        The reconstructed PortSpec.
    """
    return PortSpec(
        key=data["key"],
        kind=ValueKind(data["kind"]),
        unit=Unit(data.get("unit", "none")),
        alignment=Alignment(data.get("alignment", "none")),
        label=data.get("label", ""),
        description=data.get("description", ""),
    )


def operation_spec_to_wire(op: OperationSpec) -> dict[str, Any]:
    """Project OperationSpec to wire dictionary.

    Emits the full self-description: parameters, typed ports,
    determinism, numerical policy, effects, capability requirements,
    permissions, and exact lowering targets.

    Args:
        op: Operation descriptor to project.

    Returns:
        Wire dictionary.
    """
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
    """Decode OperationSpec from wire dictionary.

    Args:
        data: Wire dictionary produced by ``operation_spec_to_wire``.

    Returns:
        The reconstructed OperationSpec.
    """
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
# Workspace Projections
# ---------------------------------------------------------------------------


def workspace_command_to_wire(cmd: WorkspaceCommand) -> dict[str, Any]:
    """Project WorkspaceCommand to wire dictionary.

    Args:
        cmd: Workspace command descriptor.

    Returns:
        Wire dictionary with command_id, title, and description.
    """
    return {
        "command_id": cmd.command_id,
        "title": cmd.title,
        "description": cmd.description,
    }


def workspace_command_from_wire(data: dict[str, Any]) -> WorkspaceCommand:
    """Decode WorkspaceCommand from wire dictionary.

    Args:
        data: Wire dictionary produced by ``workspace_command_to_wire``.

    Returns:
        The reconstructed WorkspaceCommand.
    """
    return WorkspaceCommand(
        command_id=data["command_id"],
        title=data["title"],
        description=data.get("description", ""),
    )


def workspace_view_to_wire(view: WorkspaceView) -> dict[str, Any]:
    """Project WorkspaceView to wire dictionary.

    Args:
        view: Workspace view descriptor.

    Returns:
        Wire dictionary with view_id, title, and component.
    """
    return {
        "view_id": view.view_id,
        "title": view.title,
        "component": view.component,
    }


def workspace_view_from_wire(data: dict[str, Any]) -> WorkspaceView:
    """Decode WorkspaceView from wire dictionary.

    Args:
        data: Wire dictionary produced by ``workspace_view_to_wire``.

    Returns:
        The reconstructed WorkspaceView.
    """
    return WorkspaceView(
        view_id=data["view_id"],
        title=data["title"],
        component=data["component"],
    )


def workspace_spec_to_wire(spec: WorkspaceSpec) -> dict[str, Any]:
    """Project WorkspaceSpec to wire dictionary.

    The plugin ref is serialized in canonical ``id@major.minor.patch``
    form.

    Args:
        spec: Workspace descriptor to project.

    Returns:
        Wire dictionary with commands, views, and accepted kinds.
    """
    return {
        "ref": spec.ref.to_string(),
        "title": spec.title,
        "description": spec.description,
        "commands": [workspace_command_to_wire(c) for c in spec.commands],
        "views": [workspace_view_to_wire(v) for v in spec.views],
        "accepted_kinds": list(spec.accepted_kinds),
    }


def workspace_spec_from_wire(data: dict[str, Any]) -> WorkspaceSpec:
    """Decode WorkspaceSpec from wire dictionary.

    Args:
        data: Wire dictionary produced by ``workspace_spec_to_wire``.

    Returns:
        The reconstructed WorkspaceSpec.
    """
    return WorkspaceSpec(
        ref=PluginRef.parse(data["ref"]),
        title=data["title"],
        description=data.get("description", ""),
        commands=tuple(
            workspace_command_from_wire(c) for c in data.get("commands", [])
        ),
        views=tuple(workspace_view_from_wire(v) for v in data.get("views", [])),
        accepted_kinds=tuple(data.get("accepted_kinds", [])),
    )


# ---------------------------------------------------------------------------
# Catalog View Projections
# ---------------------------------------------------------------------------


def catalog_entry_view_to_wire(entry: CatalogEntryView) -> dict[str, Any]:
    """Project CatalogEntryView to wire dictionary.

    Emits descriptor data only; the workspace section appears only when
    present. No implementations or providers are ever serialized.

    Args:
        entry: Catalog entry view to project.

    Returns:
        Wire dictionary.
    """
    result: dict[str, Any] = {
        "ref": entry.ref.to_string(),
        "kind": entry.kind,
        "title": entry.title,
        "description": entry.description,
        "metamodel_major": entry.metamodel_major,
        "operations": [operation_spec_to_wire(op) for op in entry.operations],
    }
    if entry.workspace is not None:
        result["workspace"] = workspace_spec_to_wire(entry.workspace)
    return result


def catalog_entry_view_from_wire(data: dict[str, Any]) -> CatalogEntryView:
    """Decode CatalogEntryView from wire dictionary.

    Args:
        data: Wire dictionary produced by ``catalog_entry_view_to_wire``.

    Returns:
        The reconstructed CatalogEntryView.
    """
    ref = PluginRef.parse(data["ref"])
    operations = tuple(
        operation_spec_from_wire(op) for op in data.get("operations", [])
    )
    workspace = (
        workspace_spec_from_wire(data["workspace"])
        if "workspace" in data and data["workspace"] is not None
        else None
    )
    return CatalogEntryView(
        ref=ref,
        kind=data["kind"],
        title=data["title"],
        description=data.get("description", ""),
        metamodel_major=data.get("metamodel_major", 1),
        operations=operations,
        workspace=workspace,
    )


def catalog_view_to_wire(view: CatalogView) -> dict[str, Any]:
    """Project CatalogView to wire dictionary.

    Args:
        view: Catalog snapshot view to project.

    Returns:
        Wire dictionary with entries and catalog_fingerprint.
    """
    return {
        "entries": [catalog_entry_view_to_wire(e) for e in view.entries],
        "catalog_fingerprint": view.catalog_fingerprint,
    }


def catalog_view_from_wire(data: dict[str, Any]) -> CatalogView:
    """Decode CatalogView from wire dictionary.

    Args:
        data: Wire dictionary produced by ``catalog_view_to_wire``.

    Returns:
        The reconstructed CatalogView.
    """
    entries = tuple(catalog_entry_view_from_wire(e) for e in data.get("entries", []))
    return CatalogView(
        entries=entries,
        catalog_fingerprint=data.get("catalog_fingerprint", ""),
    )


# ---------------------------------------------------------------------------
# Graph Documents Projections
# ---------------------------------------------------------------------------


def graph_document_to_wire(doc: GraphDocument | OpaqueGraphDocument) -> dict[str, Any]:
    """Project GraphDocument or OpaqueGraphDocument to wire dictionary.

    Opaque documents are projected verbatim from their retained raw
    data, so unsupported versions round trip unchanged. Supported
    documents with subgraphs are rejected fail-closed rather than
    silently dropping them, because schema version 1 cannot losslessly
    encode nesting.

    Args:
        doc: Document to project.

    Returns:
        Wire dictionary.

    Raises:
        ValueError: If a supported document carries subgraphs.
    """
    if isinstance(doc, OpaqueGraphDocument):
        return doc.raw_data.to_dict()

    spec = doc.spec
    if spec.subgraphs:
        raise ValueError(
            "Graph schema version 1 cannot losslessly encode nested subgraphs; "
            f"refusing to drop {len(spec.subgraphs)} subgraph(s)"
        )
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
    """Decode a GraphDocument or OpaqueGraphDocument from wire dictionary.

    Documents whose schema version differs from ``GRAPH_SCHEMA_VERSION``
    are preserved verbatim as an ``OpaqueGraphDocument`` retaining the
    complete decoded object. Subgraph-bearing version-1 payloads are
    rejected fail-closed instead of being silently dropped.

    Args:
        data: Wire dictionary produced by ``graph_document_to_wire``.

    Returns:
        GraphDocument for supported versions, otherwise the opaque
        raw-retaining form.

    Raises:
        ValueError: If a supported-version payload carries subgraphs.
    """
    schema_ver = data.get("schema_version", 1)
    if schema_ver != GRAPH_SCHEMA_VERSION:
        return OpaqueGraphDocument(
            schema_version=schema_ver,
            raw_data=freeze_value(data),  # type: ignore[arg-type]
        )

    spec_data = data.get("spec", {})
    if spec_data.get("subgraphs"):
        raise ValueError(
            "Graph schema version 1 does not support nested subgraphs; "
            "document rejected instead of silently dropping them"
        )
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
    """Project SemanticProgram to wire dictionary.

    Value references and literals are distinguished by a ``type`` tag of
    ``"ref"`` or ``"literal"``; parameters and literal values use the
    value projection, so explicit missing markers survive the round
    trip.

    Args:
        prog: Semantic IR program to project.

    Returns:
        Wire dictionary including ``ir_schema_version``.
    """
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
    """Decode SemanticProgram from wire dictionary.

    The ``SemanticProgram`` constructor re-validates the full ordered
    DAG, so decoding a tampered program fails closed.

    Args:
        data: Wire dictionary produced by ``semantic_program_to_wire``.

    Returns:
        The reconstructed SemanticProgram.
    """
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

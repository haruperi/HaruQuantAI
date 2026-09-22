"""Host execution owner: in-process execution, batch parameter trials, and export."""

from __future__ import annotations

import hashlib
import time
from collections import defaultdict, deque
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Protocol, override

from app.host.catalog import HOST_CATALOG, AdmittedOperation, Catalog
from app.kernel.capability import Capability
from app.kernel.context import FeatureContext
from app.kernel.feature import Feature, FeatureSpec
from app.plugins.algebra import (
    EdgeSpec,
    GraphDocument,
    GraphSpec,
    NodeSpec,
    OpaqueGraphDocument,
    validate_graph,
)
from app.plugins.lowering import (
    IRArgument,
    IRNode,
    LoweringContext,
    LoweringIssue,
    LoweringTarget,
    ProgramInput,
    ProgramOutput,
    SemanticProgram,
    ValueRef,
)
from app.plugins.schema import (
    EMPTY_FROZEN_OBJECT,
    FrozenArray,
    FrozenObject,
    NumericalPolicy,
    ValidationIssue,
    ValueKind,
    freeze_value,
    validate_identifier,
)
from app.plugins.spec import (
    CatalogView,
    OperationBindings,
    OperationSpec,
    PluginRef,
)
from app.plugins.wire import (
    graph_document_to_wire,
    to_canonical_json_bytes,
    value_to_wire,
)


class ExecutionError(RuntimeError):
    """Base error for execution failures."""


class ExecutionBudgetExceededError(ExecutionError):
    """Raised when an execution request exceeds its declared budget."""


class ExecutionCancellationError(ExecutionError):
    """Raised when an execution is cancelled."""


class ExecutionValidationError(ExecutionError):
    """Raised when a graph or request fails validation."""


@dataclass(frozen=True, slots=True)
class ExecutionBudget:
    """Immutable bounds and limits for execution."""

    max_nodes: int = 1_000
    max_samples: int = 1_000_000
    max_output_values: int = 10_000_000
    max_trials: int = 100
    max_elapsed_seconds: float = 60.0

    def __post_init__(self) -> None:
        """Validate budget values."""
        if self.max_nodes <= 0:
            raise ValueError("max_nodes must be > 0")
        if self.max_samples <= 0:
            raise ValueError("max_samples must be > 0")
        if self.max_output_values <= 0:
            raise ValueError("max_output_values must be > 0")
        if self.max_trials <= 0:
            raise ValueError("max_trials must be > 0")
        if self.max_elapsed_seconds <= 0:
            raise ValueError("max_elapsed_seconds must be > 0")


DEFAULT_BUDGET = ExecutionBudget()


@dataclass(frozen=True, slots=True)
class ExecutionReproducibilityRecord:
    """Complete provenance and reproducibility record for an execution run."""

    graph_id: str
    graph_fingerprint: str
    catalog_fingerprint: str
    dependency_fingerprint: str
    plugin_versions: tuple[tuple[str, str], ...]
    source_digests: tuple[tuple[str, str], ...]
    normalized_parameters: FrozenObject
    input_hash: str
    seed: int | None
    numerical_policy: NumericalPolicy
    engine_version: str = "1.0.0"
    output_hash: str = ""
    elapsed_seconds: float = 0.0
    status: str = "completed"

    def __post_init__(self) -> None:
        """Validate reproducibility record."""
        if not isinstance(self.graph_id, str):
            raise TypeError("graph_id must be a string")
        if not isinstance(self.graph_fingerprint, str):
            raise TypeError("graph_fingerprint must be a string")
        if not isinstance(self.catalog_fingerprint, str):
            raise TypeError("catalog_fingerprint must be a string")
        if not isinstance(self.dependency_fingerprint, str):
            raise TypeError("dependency_fingerprint must be a string")
        if not isinstance(self.normalized_parameters, FrozenObject):
            raise TypeError("normalized_parameters must be a FrozenObject")


@dataclass(frozen=True, slots=True)
class SingleExecutionRequest:
    """Request to execute a single graph run."""

    graph_document: GraphDocument | OpaqueGraphDocument
    inputs: Mapping[str, Any] = EMPTY_FROZEN_OBJECT
    budget: ExecutionBudget = DEFAULT_BUDGET
    catalog_view: CatalogView | None = None
    seed: int | None = None

    def __post_init__(self) -> None:
        """Validate single execution request."""
        if not isinstance(self.graph_document, (GraphDocument, OpaqueGraphDocument)):
            raise TypeError(
                "graph_document must be a GraphDocument or OpaqueGraphDocument"
            )
        if not isinstance(self.budget, ExecutionBudget):
            raise TypeError("budget must be an ExecutionBudget")


@dataclass(frozen=True, slots=True)
class SingleExecutionResult:
    """Result of a single graph execution run."""

    success: bool
    outputs: FrozenObject = EMPTY_FROZEN_OBJECT
    reproducibility: ExecutionReproducibilityRecord | None = None
    issues: tuple[ValidationIssue, ...] = ()
    elapsed_seconds: float = 0.0

    def __post_init__(self) -> None:
        """Validate execution result."""
        if not isinstance(self.success, bool):
            raise TypeError("success must be a bool")
        if not isinstance(self.outputs, FrozenObject):
            raise TypeError("outputs must be a FrozenObject")
        if not isinstance(self.issues, tuple):
            raise TypeError("issues must be a tuple")


EMPTY_OVERRIDES: Mapping[str, FrozenObject] = MappingProxyType({})


@dataclass(frozen=True, slots=True)
class BatchTrial:
    """One revision or parameter trial within a batch execution."""

    trial_id: str
    parameter_overrides: Mapping[str, FrozenObject] = EMPTY_OVERRIDES
    metadata: FrozenObject = EMPTY_FROZEN_OBJECT

    def __post_init__(self) -> None:
        """Validate batch trial."""
        validate_identifier(self.trial_id, "BatchTrial trial_id")
        if not isinstance(self.metadata, FrozenObject):
            raise TypeError("metadata must be a FrozenObject")


@dataclass(frozen=True, slots=True)
class BatchExecutionRequest:
    """Request to execute multiple parameter trials."""

    graph_document: GraphDocument | OpaqueGraphDocument
    inputs: Mapping[str, Any] = EMPTY_FROZEN_OBJECT
    trials: tuple[BatchTrial, ...] = ()
    budget: ExecutionBudget = DEFAULT_BUDGET
    catalog_view: CatalogView | None = None
    seed: int | None = None

    def __post_init__(self) -> None:
        """Validate batch execution request."""
        if not isinstance(self.graph_document, (GraphDocument, OpaqueGraphDocument)):
            raise TypeError("graph_document must be a GraphDocument")
        if not isinstance(self.trials, tuple):
            raise TypeError("trials must be a tuple")
        if not isinstance(self.budget, ExecutionBudget):
            raise TypeError("budget must be an ExecutionBudget")


@dataclass(frozen=True, slots=True)
class BatchTrialResult:
    """Result of one trial within a batch."""

    trial_id: str
    result: SingleExecutionResult

    def __post_init__(self) -> None:
        """Validate batch trial result."""
        if not isinstance(self.trial_id, str):
            raise TypeError("trial_id must be a str")
        if not isinstance(self.result, SingleExecutionResult):
            raise TypeError("result must be a SingleExecutionResult")


@dataclass(frozen=True, slots=True)
class BatchExecutionResult:
    """Aggregated results of batch parameter execution."""

    success: bool
    trials: tuple[BatchTrialResult, ...] = ()
    elapsed_seconds: float = 0.0
    issues: tuple[ValidationIssue, ...] = ()

    def __post_init__(self) -> None:
        """Validate batch execution result."""
        if not isinstance(self.success, bool):
            raise TypeError("success must be a bool")
        if not isinstance(self.trials, tuple):
            raise TypeError("trials must be a tuple")
        if not isinstance(self.issues, tuple):
            raise TypeError("issues must be a tuple")


DEFAULT_PYTHON_TARGET = LoweringTarget(target_id="python", version=(1, 0, 0))


@dataclass(frozen=True, slots=True)
class ExportRequest:
    """Request to lower and export a graph document to a target format."""

    graph_document: GraphDocument | OpaqueGraphDocument
    target: LoweringTarget = DEFAULT_PYTHON_TARGET
    catalog_view: CatalogView | None = None

    def __post_init__(self) -> None:
        """Validate export request."""
        if not isinstance(self.graph_document, (GraphDocument, OpaqueGraphDocument)):
            raise TypeError("graph_document must be a GraphDocument")
        if not isinstance(self.target, LoweringTarget):
            raise TypeError("target must be a LoweringTarget")


@dataclass(frozen=True, slots=True)
class ExportResult:
    """Result of lowering and exporting a graph document."""

    success: bool
    target: LoweringTarget
    program: SemanticProgram | None = None
    source_code: str | None = None
    manifest: FrozenObject | None = None
    issues: tuple[ValidationIssue | LoweringIssue, ...] = ()

    def __post_init__(self) -> None:
        """Validate export result."""
        if not isinstance(self.success, bool):
            raise TypeError("success must be a bool")
        if not isinstance(self.target, LoweringTarget):
            raise TypeError("target must be a LoweringTarget")
        if not isinstance(self.issues, tuple):
            raise TypeError("issues must be a tuple")


class Execution(Protocol):
    """Public execution owner protocol."""

    def execute(self, request: SingleExecutionRequest) -> SingleExecutionResult:
        """Execute a single graph workflow run."""
        ...

    def execute_batch(self, request: BatchExecutionRequest) -> BatchExecutionResult:
        """Execute bounded batch parameter revisions through the single-run path."""
        ...

    def export(self, request: ExportRequest) -> ExportResult:
        """Lower graph into semantic IR and emit target source code."""
        ...


HOST_EXECUTION = Capability[Execution]("host.execution", major=1)


class _RestrictedOperationBindings(OperationBindings):
    """Restricted capability resolver permitting only explicitly declared tokens."""

    def __init__(
        self,
        op_spec: OperationSpec,
        capabilities: Mapping[str, Any] | None = None,
    ) -> None:
        self._op_spec = op_spec
        self._capabilities = capabilities or {}

    @override
    def require[T](self, token: Capability[T]) -> T:
        if token.name not in self._op_spec.required_capabilities:
            raise PermissionError(
                f"Operation {self._op_spec.operation_id!r} did not declare "
                f"required capability {token.name!r}"
            )
        if token.name not in self._capabilities:
            raise RuntimeError(f"Required capability {token.name!r} not available")
        return self._capabilities[token.name]  # type: ignore[no-any-return]

    @override
    def optional[T](self, token: Capability[T]) -> T | None:
        if token.name not in self._op_spec.optional_capabilities:
            raise PermissionError(
                f"Operation {self._op_spec.operation_id!r} did not declare "
                f"optional capability {token.name!r}"
            )
        return self._capabilities.get(token.name)


class _LocalLoweringContext(LoweringContext):
    """Deterministic LoweringContext for graph lowering."""

    def __init__(self, target: LoweringTarget, prefix: str) -> None:
        self._target = target
        self._prefix = prefix
        self._counter = 0

    @property
    @override
    def target(self) -> LoweringTarget:
        return self._target

    @override
    def allocate_node_id(self, prefix: str = "node") -> str:
        self._counter += 1
        return f"{self._prefix}_{prefix}_{self._counter}"


def _topological_sort(
    nodes: tuple[NodeSpec, ...], edges: tuple[EdgeSpec, ...]
) -> list[NodeSpec]:
    """Return nodes in canonical deterministic topological order."""
    node_map = {n.id: n for n in nodes}
    in_degree: dict[str, int] = {n.id: 0 for n in nodes}
    adj: dict[str, list[str]] = defaultdict(list)

    for edge in edges:
        if edge.source.node_id in in_degree and edge.target.node_id in in_degree:
            adj[edge.source.node_id].append(edge.target.node_id)
            in_degree[edge.target.node_id] += 1

    # Deterministic priority: sorted node IDs
    queue = deque(sorted(nid for nid, deg in in_degree.items() if deg == 0))
    ordered: list[NodeSpec] = []

    while queue:
        curr_id = queue.popleft()
        ordered.append(node_map[curr_id])
        for nxt in sorted(adj[curr_id]):
            in_degree[nxt] -= 1
            if in_degree[nxt] == 0:
                queue.append(nxt)

    return ordered


def _remap_node_ir_inputs(
    ir_inputs: Sequence[IRArgument],
    node_id: str,
    edge_connections: Mapping[tuple[str, str], tuple[str, str]],
    node_output_ir_refs: Mapping[tuple[str, str], ValueRef],
) -> tuple[IRArgument, ...]:
    """Remap node IR arguments connecting to other graph nodes."""
    new_inputs: list[IRArgument] = []
    for inp_arg in ir_inputs:
        if isinstance(inp_arg, ValueRef):
            edge_src = edge_connections.get((node_id, inp_arg.output_key))
            if edge_src is not None:
                new_inputs.append(node_output_ir_refs[edge_src])
            else:
                new_inputs.append(inp_arg)
        else:
            new_inputs.append(inp_arg)
    return tuple(new_inputs)


def _collect_stitched_outputs(
    designated_roots: Sequence[Any] | None,
    node_output_ir_refs: Mapping[tuple[str, str], ValueRef],
) -> list[ProgramOutput]:
    """Collect outputs for stitched semantic program."""
    if designated_roots:
        return [
            ProgramOutput(
                key=f"{root.node_id}_{root.port_key}",
                source=node_output_ir_refs[(root.node_id, root.port_key)],
                kind=ValueKind.ALIGNED_SERIES,
            )
            for root in designated_roots
        ]
    return [
        ProgramOutput(
            key=f"{nid}_{pkey}",
            source=ir_ref,
            kind=ValueKind.ALIGNED_SERIES,
        )
        for (nid, pkey), ir_ref in node_output_ir_refs.items()
    ]


class _ExecutionProvider:
    """Internal implementation of the Execution protocol."""

    def __init__(self, catalog: Catalog) -> None:
        self._catalog = catalog

    def _admit_nodes(
        self, nodes: Sequence[NodeSpec]
    ) -> tuple[dict[str, AdmittedOperation], tuple[ValidationIssue, ...]]:
        """Admit all referenced operations for nodes in graph."""
        admitted_map: dict[str, AdmittedOperation] = {}
        for node in nodes:
            try:
                admitted = self._catalog.admit(node.plugin_ref, node.operation_id)
                admitted_map[node.id] = admitted
            except (KeyError, ValueError, TypeError) as err:
                issue = ValidationIssue(
                    path=f"nodes.{node.id}",
                    code="ADMISSION_FAILED",
                    message=f"Failed to admit operation for node {node.id}: {err}",
                )
                return {}, (issue,)
        return admitted_map, ()

    def _assemble_node_inputs(
        self,
        node: NodeSpec,
        admitted: AdmittedOperation,
        edges: Sequence[EdgeSpec],
        node_outputs: Mapping[str, Mapping[str, Any]],
        *,
        frozen_inputs: Mapping[str, Any],
        budget: ExecutionBudget,
    ) -> dict[str, Any]:
        """Assemble and bound-check inputs for a node."""
        node_in: dict[str, Any] = {}
        for edge in edges:
            if edge.target.node_id == node.id:
                src_val = node_outputs[edge.source.node_id].get(edge.source.port_key)
                node_in[edge.target.port_key] = src_val

        for port in admitted.spec.inputs:
            if port.key not in node_in:
                if port.key in frozen_inputs:
                    node_in[port.key] = frozen_inputs[port.key]
                elif f"{node.id}.{port.key}" in frozen_inputs:
                    node_in[port.key] = frozen_inputs[f"{node.id}.{port.key}"]

        for port_k, in_v in node_in.items():
            if (
                isinstance(in_v, (tuple, list, FrozenArray))
                and len(in_v) > budget.max_samples
            ):
                raise ExecutionBudgetExceededError(
                    f"Input series {port_k!r} on node {node.id!r} has "
                    f"{len(in_v)} samples > budget max {budget.max_samples}"
                )
        return node_in

    def _execute_single_node(
        self,
        node: NodeSpec,
        admitted: AdmittedOperation,
        node_in: Mapping[str, Any],
    ) -> dict[str, Any]:
        """Execute single node with restricted capabilities."""
        impl = admitted.contribution.implementation
        bindings = _RestrictedOperationBindings(admitted.spec)
        out_mapping = impl.execute(node_in, node.parameters, bindings)
        frozen_out: dict[str, Any] = {}
        for ok, ov in out_mapping.items():
            frozen_out[ok] = freeze_value(ov)
        return frozen_out

    def _gather_final_outputs(
        self,
        norm_doc: GraphDocument,
        node_outputs: Mapping[str, Mapping[str, Any]],
    ) -> FrozenObject:
        """Collect designated roots or all node outputs into a FrozenObject."""
        final_outputs: dict[str, Any] = {}
        if norm_doc.spec.designated_roots:
            for root in norm_doc.spec.designated_roots:
                val = node_outputs.get(root.node_id, {}).get(root.port_key)
                final_outputs[f"{root.node_id}.{root.port_key}"] = val
        else:
            for nid, outs in node_outputs.items():
                for pkey, val in outs.items():
                    final_outputs[f"{nid}.{pkey}"] = val
        return FrozenObject.from_mapping(final_outputs)

    def _run_execution_loop(
        self,
        ordered_nodes: Sequence[NodeSpec],
        admitted_map: Mapping[str, AdmittedOperation],
        norm_doc: GraphDocument,
        frozen_inputs: Mapping[str, Any],
        *,
        budget: ExecutionBudget,
        start_time: float,
    ) -> tuple[dict[str, dict[str, Any]] | None, tuple[ValidationIssue, ...]]:
        """Iterate through ordered nodes, execute and enforce limits."""
        node_outputs: dict[str, dict[str, Any]] = {}
        total_output_values = 0

        for node in ordered_nodes:
            elapsed = time.perf_counter() - start_time
            if elapsed > budget.max_elapsed_seconds:
                raise ExecutionBudgetExceededError(
                    f"Execution exceeded budget time: {elapsed:.2f}s > "
                    f"{budget.max_elapsed_seconds}s"
                )

            admitted = admitted_map[node.id]
            bind_res = admitted.contribution.implementation.validate_parameters(
                node.parameters
            )
            if not bind_res.is_valid:
                return None, bind_res.issues

            node_in = self._assemble_node_inputs(
                node,
                admitted,
                norm_doc.spec.edges,
                node_outputs,
                frozen_inputs=frozen_inputs,
                budget=budget,
            )
            frozen_out = self._execute_single_node(node, admitted, node_in)

            for ov in frozen_out.values():
                if isinstance(ov, (tuple, list, FrozenArray)):
                    total_output_values += len(ov)
                else:
                    total_output_values += 1

            if total_output_values > budget.max_output_values:
                raise ExecutionBudgetExceededError(
                    f"Total output values {total_output_values} exceeded budget "
                    f"{budget.max_output_values}"
                )

            node_outputs[node.id] = frozen_out

        return node_outputs, ()

    def execute(self, request: SingleExecutionRequest) -> SingleExecutionResult:
        start_time = time.perf_counter()

        if isinstance(request.graph_document, OpaqueGraphDocument):
            issue = ValidationIssue(
                path="graph_document",
                code="UNSUPPORTED_VERSION",
                message=(
                    f"Unsupported graph document schema version "
                    f"{request.graph_document.schema_version}"
                ),
            )
            return SingleExecutionResult(
                success=False,
                issues=(issue,),
                elapsed_seconds=time.perf_counter() - start_time,
            )

        doc = request.graph_document
        budget = request.budget

        if len(doc.spec.nodes) > budget.max_nodes:
            raise ExecutionBudgetExceededError(
                f"Graph node count {len(doc.spec.nodes)} exceeds "
                f"budget {budget.max_nodes}"
            )

        # 1. Validate against active catalog view
        catalog_snapshot = self._catalog.snapshot()
        catalog_view = request.catalog_view or catalog_snapshot.view
        val_res = validate_graph(doc, catalog_view)
        if not val_res.can_execute or val_res.normalized_document is None:
            return SingleExecutionResult(
                success=False,
                issues=val_res.issues,
                elapsed_seconds=time.perf_counter() - start_time,
            )

        norm_doc = val_res.normalized_document

        # 2. Admit every referenced exact operation & compute dependency fingerprint
        admitted_map, admit_issues = self._admit_nodes(norm_doc.spec.nodes)
        if admit_issues:
            return SingleExecutionResult(
                success=False,
                issues=admit_issues,
                elapsed_seconds=time.perf_counter() - start_time,
            )

        # Compute dependency fingerprint
        sorted_entry_fps = sorted(
            adm.entry_fingerprint for adm in admitted_map.values()
        )
        dep_fingerprint = hashlib.sha256(
            ":".join(sorted_entry_fps).encode("utf-8")
        ).hexdigest()

        # 3. Canonical topological order
        ordered_nodes = _topological_sort(norm_doc.spec.nodes, norm_doc.spec.edges)

        # 4. Freeze inputs to guarantee caller mutation safety
        frozen_inputs = {k: freeze_value(v) for k, v in request.inputs.items()}

        # 5. Execute nodes in order
        node_outputs, exec_issues = self._run_execution_loop(
            ordered_nodes,
            admitted_map,
            norm_doc,
            frozen_inputs,
            budget=budget,
            start_time=start_time,
        )
        if exec_issues or node_outputs is None:
            return SingleExecutionResult(
                success=False,
                issues=exec_issues,
                elapsed_seconds=time.perf_counter() - start_time,
            )

        # 6. Gather designated roots or all node outputs
        frozen_final = self._gather_final_outputs(norm_doc, node_outputs)
        output_hash = hashlib.sha256(
            to_canonical_json_bytes(value_to_wire(frozen_final))
        ).hexdigest()

        # Compute provenance hashes
        input_hash = hashlib.sha256(
            to_canonical_json_bytes(
                value_to_wire(FrozenObject.from_mapping(frozen_inputs))
            )
        ).hexdigest()
        graph_fingerprint = hashlib.sha256(
            to_canonical_json_bytes(graph_document_to_wire(norm_doc))
        ).hexdigest()

        plugin_versions = tuple(
            (node.id, node.plugin_ref.to_string()) for node in norm_doc.spec.nodes
        )
        source_digests = tuple(
            (node.id, admitted_map[node.id].source_digest)
            for node in norm_doc.spec.nodes
        )
        norm_params = FrozenObject.from_mapping(
            {node.id: node.parameters for node in norm_doc.spec.nodes}
        )

        total_elapsed = time.perf_counter() - start_time

        reproducibility = ExecutionReproducibilityRecord(
            graph_id=norm_doc.spec.nodes[0].id if norm_doc.spec.nodes else "empty",
            graph_fingerprint=graph_fingerprint,
            catalog_fingerprint=catalog_snapshot.whole_fingerprint,
            dependency_fingerprint=dep_fingerprint,
            plugin_versions=plugin_versions,
            source_digests=source_digests,
            normalized_parameters=norm_params,
            input_hash=input_hash,
            seed=request.seed,
            numerical_policy=admitted_map[ordered_nodes[0].id].spec.numerical_policy
            if ordered_nodes
            else NumericalPolicy(),
            output_hash=output_hash,
            elapsed_seconds=total_elapsed,
            status="completed",
        )

        return SingleExecutionResult(
            success=True,
            outputs=frozen_final,
            reproducibility=reproducibility,
            issues=(),
            elapsed_seconds=total_elapsed,
        )

    def execute_batch(self, request: BatchExecutionRequest) -> BatchExecutionResult:
        start_time = time.perf_counter()
        if len(request.trials) > request.budget.max_trials:
            raise ExecutionBudgetExceededError(
                f"Trial count {len(request.trials)} exceeds "
                f"budget {request.budget.max_trials}"
            )

        if isinstance(request.graph_document, OpaqueGraphDocument):
            issue = ValidationIssue(
                path="graph_document",
                code="UNSUPPORTED_VERSION",
                message="Unsupported graph document in batch request",
            )
            return BatchExecutionResult(
                success=False,
                issues=(issue,),
                elapsed_seconds=time.perf_counter() - start_time,
            )

        doc = request.graph_document
        trial_results: list[BatchTrialResult] = []
        overall_success = True

        for trial in request.trials:
            if time.perf_counter() - start_time > request.budget.max_elapsed_seconds:
                raise ExecutionBudgetExceededError(
                    "Batch execution exceeded elapsed time budget"
                )

            # Apply parameter overrides to graph nodes
            new_nodes: list[NodeSpec] = []
            for node in doc.spec.nodes:
                if node.id in trial.parameter_overrides:
                    merged = dict(node.parameters.entries)
                    merged.update(trial.parameter_overrides[node.id].entries)
                    new_nodes.append(
                        NodeSpec(
                            id=node.id,
                            plugin_ref=node.plugin_ref,
                            operation_id=node.operation_id,
                            parameters=FrozenObject.from_mapping(merged),
                            title=node.title,
                            extension_data=node.extension_data,
                        )
                    )
                else:
                    new_nodes.append(node)

            trial_doc = GraphDocument(
                spec=GraphSpec(
                    schema_version=doc.spec.schema_version,
                    nodes=tuple(new_nodes),
                    edges=doc.spec.edges,
                    designated_roots=doc.spec.designated_roots,
                    subgraphs=doc.spec.subgraphs,
                ),
                metadata=doc.metadata,
            )
            trial_req = SingleExecutionRequest(
                graph_document=trial_doc,
                inputs=request.inputs,
                budget=ExecutionBudget(
                    max_nodes=request.budget.max_nodes,
                    max_samples=request.budget.max_samples,
                    max_output_values=request.budget.max_output_values,
                    max_elapsed_seconds=request.budget.max_elapsed_seconds,
                    max_trials=1,
                ),
                catalog_view=request.catalog_view,
                seed=request.seed,
            )
            run_res = self.execute(trial_req)
            if not run_res.success:
                overall_success = False

            trial_results.append(
                BatchTrialResult(
                    trial_id=trial.trial_id,
                    result=run_res,
                )
            )

        return BatchExecutionResult(
            success=overall_success,
            trials=tuple(trial_results),
            issues=(),
            elapsed_seconds=time.perf_counter() - start_time,
        )

    def _stitch_semantic_programs(
        self,
        ordered_nodes: Sequence[NodeSpec],
        node_programs: Mapping[str, SemanticProgram],
        norm_doc: GraphDocument,
    ) -> SemanticProgram:
        """Stitch per-node lowered SemanticPrograms into a unified program."""
        combined_inputs: list[ProgramInput] = []
        combined_nodes: list[IRNode] = []

        # Map edge connections: (target_node_id, target_input_key) -> (src_id, src_key)
        edge_connections: dict[tuple[str, str], tuple[str, str]] = {
            (edge.target.node_id, edge.target.port_key): (
                edge.source.node_id,
                edge.source.port_key,
            )
            for edge in norm_doc.spec.edges
        }

        node_output_ir_refs: dict[tuple[str, str], ValueRef] = {}

        for node in ordered_nodes:
            prog = node_programs[node.id]

            for out in prog.outputs:
                node_output_ir_refs[(node.id, out.key)] = out.source

            for ir_node in prog.nodes:
                new_inputs = _remap_node_ir_inputs(
                    ir_node.inputs,
                    node.id,
                    edge_connections,
                    node_output_ir_refs,
                )
                combined_nodes.append(
                    IRNode(
                        id=ir_node.id,
                        operator=ir_node.operator,
                        inputs=new_inputs,
                        parameters=ir_node.parameters,
                        outputs=ir_node.outputs,
                    )
                )

            for prog_in in prog.inputs:
                if (node.id, prog_in.key) not in edge_connections and not any(
                    ci.key == prog_in.key for ci in combined_inputs
                ):
                    combined_inputs.append(prog_in)

        combined_outputs = _collect_stitched_outputs(
            norm_doc.spec.designated_roots, node_output_ir_refs
        )

        return SemanticProgram(
            inputs=tuple(combined_inputs),
            nodes=tuple(combined_nodes),
            outputs=tuple(combined_outputs),
        )

    def export(self, request: ExportRequest) -> ExportResult:
        if isinstance(request.graph_document, OpaqueGraphDocument):
            issue = ValidationIssue(
                path="graph_document",
                code="UNSUPPORTED_VERSION",
                message="Cannot export unsupported graph version",
            )
            return ExportResult(
                success=False,
                target=request.target,
                issues=(issue,),
            )

        doc = request.graph_document
        catalog_snapshot = self._catalog.snapshot()
        catalog_view = request.catalog_view or catalog_snapshot.view

        val_res = validate_graph(doc, catalog_view)
        if not val_res.can_execute or val_res.normalized_document is None:
            return ExportResult(
                success=False,
                target=request.target,
                issues=val_res.issues,
            )

        norm_doc = val_res.normalized_document
        ordered_nodes = _topological_sort(norm_doc.spec.nodes, norm_doc.spec.edges)
        node_programs: dict[str, SemanticProgram] = {}

        for node in ordered_nodes:
            admitted = self._catalog.admit(node.plugin_ref, node.operation_id)
            ctx = _LocalLoweringContext(request.target, prefix=node.id)
            lowered = admitted.contribution.implementation.lower(ctx, node.parameters)
            if not lowered.success or lowered.program is None:
                return ExportResult(
                    success=False,
                    target=request.target,
                    issues=lowered.issues,
                )
            node_programs[node.id] = lowered.program

        unified_program = self._stitch_semantic_programs(
            ordered_nodes, node_programs, norm_doc
        )

        exporter_ref = PluginRef(
            id=f"exporter.{request.target.target_id}", version=(1, 0, 0)
        )
        try:
            exporter_admitted = self._catalog.admit(exporter_ref, "export")
        except (KeyError, ValueError, TypeError) as err:
            issue = ValidationIssue(
                path="target",
                code="EXPORTER_UNAVAILABLE",
                message=(
                    f"Exporter for target {request.target.target_id!r} "
                    f"unavailable: {err}"
                ),
            )
            return ExportResult(
                success=False,
                target=request.target,
                issues=(issue,),
            )

        exporter_impl = exporter_admitted.contribution.implementation
        mock_bindings = _RestrictedOperationBindings(exporter_admitted.spec)
        exp_res = exporter_impl.execute(
            {"program": unified_program}, EMPTY_FROZEN_OBJECT, mock_bindings
        )

        return ExportResult(
            success=True,
            target=request.target,
            program=unified_program,
            source_code=exp_res.get("source"),
            manifest=exp_res.get("manifest"),
            issues=(),
        )


class _ExecutionFeature(Feature):
    """Host lifecycle feature for the Execution capability."""

    spec = FeatureSpec(
        "host.execution",
        requires=frozenset({HOST_CATALOG}),
        provides=frozenset({HOST_EXECUTION}),
    )

    def __init__(self) -> None:
        self._provider: _ExecutionProvider | None = None

    @override
    async def start(self, context: FeatureContext) -> None:
        catalog = context.require(HOST_CATALOG)
        self._provider = _ExecutionProvider(catalog)
        context.provide(HOST_EXECUTION, self._provider)


def _execution_feature() -> Feature:
    """Construct private execution feature. Imported only by app.host.bootstrap."""
    return _ExecutionFeature()

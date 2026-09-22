"""Host execution owner: graph execution, batch trials, and export.

One host owner = one file: this module owns the public ``Execution``
protocol, the ``HOST_EXECUTION`` capability token
(``host.execution@1``), and the public request, budget, result, and
reproducibility values. The provider, restricted capability
bindings, and lowering helpers are private; ``_execution_feature``
is a composition-only constructor used solely by
``app.host.bootstrap``.

The owner provides the numbered deterministic single-run path
(reject opaque documents, validate, admit, bind and warm up,
plan, freeze inputs, execute, record), batch parameter trials that
reuse exactly that path with no optimization objective, and export
through plugin-owned lowering with node attribution. It does not
own discovery, graph authoring, persistence, transport, or
scheduling; admission is delegated to ``host.catalog@1``.

Concurrency: execution calls are synchronous and CPU-bound; the
provider keeps no per-run state between calls, so each caller gets a
fresh, isolated run. ``EXECUTION_ENGINE_VERSION`` stamps every
reproducibility record this engine emits.
"""

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
    """Raised when an execution request exceeds its declared budget.

    Budgets cover node count, samples per input series, cumulative
    output values, trial counts, and elapsed wall-clock time.
    """


class ExecutionCancellationError(ExecutionError):
    """Raised when an execution observes a cancelled CancellationToken."""


class ExecutionValidationError(ExecutionError):
    """Raised when a graph or request fails validation."""


class CancellationToken:
    """Runtime-only caller cancellation control for execution requests.

    A mutable host-owned object by design: the caller cancels it from outside
    while an execution is in flight. It is never part of any wire value or
    persisted record; executors only poll it between work units, so
    cancellation takes effect at the next node boundary.
    """

    def __init__(self) -> None:
        self._cancelled = False

    @property
    def cancelled(self) -> bool:
        """Whether cancellation has been requested."""
        return self._cancelled

    def cancel(self) -> None:
        """Request cancellation of any in-flight execution sharing this token.

        Cancellation is sticky and idempotent; it cannot be withdrawn.
        """
        self._cancelled = True

    def raise_if_cancelled(self) -> None:
        """Raise if cancellation was requested.

        Raises:
            ExecutionCancellationError: If ``cancel`` has been called
                on this token.
        """
        if self._cancelled:
            raise ExecutionCancellationError(
                "Execution cancelled by caller cancellation token"
            )


def _cancellation_issue() -> ValidationIssue:
    """Build the stable ``EXECUTION_CANCELLED`` issue for cancellation results."""
    return ValidationIssue(
        path="execution",
        code="EXECUTION_CANCELLED",
        message="Execution was cancelled by the caller before completion",
    )


@dataclass(frozen=True, slots=True)
class ExecutionBudget:
    """Immutable bounds and limits for execution.

    Attributes:
        max_nodes: Maximum node count per graph.
        max_samples: Maximum samples per input series.
        max_output_values: Cumulative output value budget per run.
        max_trials: Maximum trials per batch request.
        max_elapsed_seconds: Wall-clock ceiling for a run or batch.
        cancellation_check_nodes: Node interval between cancellation
            token checks inside the execution loop; a blocking
            implementation delays the check only until the current
            node completes.
    """

    max_nodes: int = 1_000
    max_samples: int = 1_000_000
    max_output_values: int = 10_000_000
    max_trials: int = 100
    max_elapsed_seconds: float = 60.0
    cancellation_check_nodes: int = 1

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
        if self.cancellation_check_nodes <= 0:
            raise ValueError("cancellation_check_nodes must be > 0")


DEFAULT_BUDGET = ExecutionBudget()
EXECUTION_ENGINE_VERSION = "1.0.0"


@dataclass(frozen=True, slots=True)
class ExecutionReproducibilityRecord:
    """Complete provenance and reproducibility record for an execution run.

    Immutable. Captures graph, catalog, and dependency fingerprints,
    per-node plugin versions and source digests, normalized
    parameters, input and output hashes, the caller seed, the
    topologically first node's numerical policy, the warm-up sample
    counts implementations reported, per-node numerical policies, and
    the ``EXECUTION_ENGINE_VERSION`` that produced the run.

    Attributes:
        graph_id: Identity of the first normalized node (or
            ``"empty"`` for an empty graph).
        graph_fingerprint: Canonical digest of the normalized graph.
        catalog_fingerprint: Whole-catalog fingerprint at run time.
        dependency_fingerprint: Digest over admitted entries' entry
            fingerprints only.
        plugin_versions: ``(node_id, plugin ref)`` pairs.
        source_digests: ``(node_id, source digest)`` pairs.
        normalized_parameters: Per-node normalized parameters.
        input_hash: Canonical digest of the frozen inputs.
        seed: Caller seed recorded verbatim.
        numerical_policy: Policy of the first ordered node.
        engine_version: Engine version stamp.
        output_hash: Canonical digest of the frozen outputs.
        elapsed_seconds: Wall-clock duration of the run.
        status: Terminal status (``"completed"`` when successful).
        node_warmup_samples: ``(node_id, warm-up samples)`` pairs.
        node_policies: ``(node_id, policy)`` pairs for every node.
    """

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
    engine_version: str = EXECUTION_ENGINE_VERSION
    output_hash: str = ""
    elapsed_seconds: float = 0.0
    status: str = "completed"
    node_warmup_samples: tuple[tuple[str, int], ...] = ()
    node_policies: tuple[tuple[str, NumericalPolicy], ...] = ()

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
    """Request to execute a single graph run.

    Attributes:
        graph_document: Graph to execute; an
            :class:`OpaqueGraphDocument` is rejected with an
            ``UNSUPPORTED_VERSION`` issue rather than raised.
        inputs: Caller inputs; frozen once per run so later caller
            mutation cannot affect an in-flight execution.
        budget: Bounds enforced during the run.
        catalog_view: Optional pinned view override; defaults to the
            live catalog snapshot's view.
        seed: Caller seed recorded verbatim in the reproducibility
            record.
        cancellation: Optional runtime-only token polled between
            nodes.
    """

    graph_document: GraphDocument | OpaqueGraphDocument
    inputs: Mapping[str, Any] = EMPTY_FROZEN_OBJECT
    budget: ExecutionBudget = DEFAULT_BUDGET
    catalog_view: CatalogView | None = None
    seed: int | None = None
    cancellation: CancellationToken | None = None

    def __post_init__(self) -> None:
        """Validate single execution request."""
        if not isinstance(self.graph_document, (GraphDocument, OpaqueGraphDocument)):
            raise TypeError(
                "graph_document must be a GraphDocument or OpaqueGraphDocument"
            )
        if not isinstance(self.budget, ExecutionBudget):
            raise TypeError("budget must be an ExecutionBudget")
        if self.cancellation is not None and not isinstance(
            self.cancellation, CancellationToken
        ):
            raise TypeError("cancellation must be a CancellationToken or None")


@dataclass(frozen=True, slots=True)
class SingleExecutionResult:
    """Result of a single graph execution run.

    Attributes:
        success: Whether the run completed and produced outputs.
        outputs: Frozen outputs; designated roots are keyed
            ``"<node_id>.<port_key>"``, otherwise every node output
            appears under that same keying.
        reproducibility: Provenance record, present on success.
        issues: Validation, admission, or cancellation issues on
            failure.
        elapsed_seconds: Wall-clock duration of the run.
    """

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
    """One revision or parameter trial within a batch execution.

    Attributes:
        trial_id: Stable identifier unique within the batch.
        parameter_overrides: Per-node parameter objects shallowly
            merged over that node's declared parameters; nodes not
            present keep their declared parameters.
        metadata: Frozen caller metadata carried alongside the trial.
    """

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
    """Request to execute multiple parameter trials.

    Attributes:
        graph_document: Base graph; opaque documents are rejected
            with an ``UNSUPPORTED_VERSION`` issue.
        inputs: Shared caller inputs, frozen per trial run.
        trials: Trials to execute in order; bounded by
            ``budget.max_trials``.
        budget: Bounds enforced for the batch and each trial.
        catalog_view: Optional pinned view override.
        seed: Caller seed recorded verbatim per trial.
        cancellation: Optional token polled before every trial and
            inside each trial's run.
    """

    graph_document: GraphDocument | OpaqueGraphDocument
    inputs: Mapping[str, Any] = EMPTY_FROZEN_OBJECT
    trials: tuple[BatchTrial, ...] = ()
    budget: ExecutionBudget = DEFAULT_BUDGET
    catalog_view: CatalogView | None = None
    seed: int | None = None
    cancellation: CancellationToken | None = None

    def __post_init__(self) -> None:
        """Validate batch execution request."""
        if not isinstance(self.graph_document, (GraphDocument, OpaqueGraphDocument)):
            raise TypeError("graph_document must be a GraphDocument")
        if not isinstance(self.trials, tuple):
            raise TypeError("trials must be a tuple")
        if not isinstance(self.budget, ExecutionBudget):
            raise TypeError("budget must be an ExecutionBudget")
        if self.cancellation is not None and not isinstance(
            self.cancellation, CancellationToken
        ):
            raise TypeError("cancellation must be a CancellationToken or None")


@dataclass(frozen=True, slots=True)
class BatchTrialResult:
    """Result of one trial within a batch.

    Attributes:
        trial_id: Identifier of the executed trial.
        result: The trial's full single-run result.
    """

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
    """Aggregated results of batch parameter execution.

    Attributes:
        success: True only when every executed trial succeeded.
        trials: Per-trial results in request order.
        elapsed_seconds: Wall-clock duration of the whole batch.
        issues: Batch-level issues such as cancellation.
    """

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
    """Request to lower and export a graph document to a target format.

    Attributes:
        graph_document: Graph to lower; opaque documents are
            rejected with an ``UNSUPPORTED_VERSION`` issue.
        target: Lowering target; defaults to ``python`` at version
            ``(1, 0, 0)``.
        catalog_view: Optional pinned view override for validation.
    """

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
    """Result of lowering and exporting a graph document.

    Attributes:
        success: Whether lowering and export both succeeded.
        target: The lowering target that was requested.
        program: The stitched semantic program on success.
        source_code: Target source text from the exporter plugin.
        manifest: Frozen exporter manifest, when provided.
        issues: Validation issues or attributed lowering issues;
            lowering failures carry node and plugin identity.
    """

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
    """Public execution owner protocol exposed as ``host.execution@1``.

    The implementing provider is private, requires a live catalog
    for admission, and keeps no per-run state between calls.
    """

    def execute(self, request: SingleExecutionRequest) -> SingleExecutionResult:
        """Execute a single graph workflow run.

        The numbered path: (1) reject an opaque graph document with
        an ``UNSUPPORTED_VERSION`` issue; (2) fail on node counts over
        ``budget.max_nodes``; (3) validate the graph against the
        requested or live catalog view; (4) admit every referenced
        operation, binding exact specs and implementations and
        consulting each implementation for parameter validation and
        warm-up samples; (5) plan nodes in canonical topological
        order; (6) execute nodes with restricted capability bindings
        only, after freezing caller inputs, with fresh function-local
        run state, assembling each node's inputs from incoming edges
        and then frozen request inputs (leaving any port that is
        neither connected nor supplied absent, so missing-data policy
        stays implementation-owned); and (7) enforce the elapsed,
        sample, output-value, and cancellation budgets while
        producing immutable frozen outputs plus a reproducibility
        record.

        Args:
            request: The run request with graph, inputs, budget, and
                optional pinned view, seed, and cancellation token.

        Returns:
            The frozen outputs and reproducibility record on
            success, or attributed issues on failure.

        Raises:
            ExecutionBudgetExceededError: If the node count, input
                samples, cumulative output values, or elapsed time
                exceed the declared budget.

        Note:
            Caller cancellation does not raise; it returns a failed
            result carrying the ``EXECUTION_CANCELLED`` issue, with
            all run-owned loop state discarded.
        """
        ...

    def execute_batch(self, request: BatchExecutionRequest) -> BatchExecutionResult:
        """Execute bounded batch parameter revisions through the single-run path.

        Each trial's graph revision is built by shallowly merging the
        trial's parameter overrides, then executed via exactly the
        same ``execute`` path with a fresh request; there is no
        optimization objective or cross-trial state. The batch stops
        early when the shared cancellation token fires, and enforces
        the trial-count and elapsed budgets at batch level.

        Args:
            request: The batch request with base graph, shared
                inputs, ordered trials, and budget.

        Returns:
            Per-trial single-run results plus batch-level issues;
            overall success requires every executed trial to succeed.

        Raises:
            ExecutionBudgetExceededError: If the trial count or the
                batch elapsed time exceeds the declared budget.
        """
        ...

    def export(self, request: ExportRequest) -> ExportResult:
        """Lower graph into semantic IR and emit target source code.

        Validates the graph, orders nodes topologically, lowers every
        node through its admitted implementation to the requested
        target, stitches the per-node programs into one semantic
        program, and runs the target's exporter plugin operation.
        Failures are attributed: node-level lowering errors carry the
        node id and plugin ref under ``LOWERING_FAILED`` or as
        node-attributed lowering issues, a missing exporter yields
        ``EXPORTER_UNAVAILABLE``, and an exporter failure yields
        ``EXPORT_FAILED``.

        Args:
            request: The export request with graph and target.

        Returns:
            The unified program, exporter source text, and optional
            manifest on success, or attributed issues on failure.
        """
        ...


HOST_EXECUTION = Capability[Execution]("host.execution", major=1)


class _RestrictedOperationBindings(OperationBindings):
    """Restricted capability resolver permitting only explicitly declared tokens.

    Private. Operations see capabilities only when their own spec
    declared them; nothing else in the host is reachable through
    this resolver.
    """

    def __init__(
        self,
        op_spec: OperationSpec,
        capabilities: Mapping[str, Any] | None = None,
    ) -> None:
        self._op_spec = op_spec
        self._capabilities = capabilities or {}

    @override
    def require[T](self, token: Capability[T]) -> T:
        """Resolve a mandatory capability the operation declared.

        Raises:
            PermissionError: If the operation spec did not declare
                the capability as required.
            RuntimeError: If the capability was declared but is not
                available in this host.
        """
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
        """Resolve an optional capability the operation declared.

        Raises:
            PermissionError: If the operation spec did not declare
                the capability as optional.
        """
        if token.name not in self._op_spec.optional_capabilities:
            raise PermissionError(
                f"Operation {self._op_spec.operation_id!r} did not declare "
                f"optional capability {token.name!r}"
            )
        return self._capabilities.get(token.name)


class _LocalLoweringContext(LoweringContext):
    """Deterministic LoweringContext for graph lowering.

    Private. IR node ids are allocated from a per-run counter scoped
    by a node prefix, so lowered programs are reproducible.
    """

    def __init__(self, target: LoweringTarget, prefix: str) -> None:
        self._target = target
        self._prefix = prefix
        self._counter = 0

    @property
    @override
    def target(self) -> LoweringTarget:
        """The lowering target this context allocates ids for."""
        return self._target

    @override
    def allocate_node_id(self, prefix: str = "node") -> str:
        """Allocate the next deterministic, prefix-scoped IR node id."""
        self._counter += 1
        return f"{self._prefix}_{prefix}_{self._counter}"


def _topological_sort(
    nodes: tuple[NodeSpec, ...], edges: tuple[EdgeSpec, ...]
) -> list[NodeSpec]:
    """Return nodes in canonical deterministic topological order.

    Ties are broken by sorted node id and edges referencing unknown
    nodes are ignored; graphs are validated as acyclic beforehand,
    so every node receives a position.
    """
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
    """Remap node IR arguments connecting to other graph nodes.

    ValueRefs whose input key is fed by a graph edge are rewired to
    the producing node's lowered value ref; every other argument
    passes through unchanged.
    """
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
    """Collect outputs for the stitched semantic program.

    Designated roots become named outputs in declaration order; with
    no designated roots, every node output is exported.
    """
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


def _apply_trial_overrides(doc: GraphDocument, trial: BatchTrial) -> GraphDocument:
    """Build the trial's graph revision by merging parameter overrides.

    Each overridden node gets a new spec whose parameters shallowly
    merge the trial's object over the declared ones; all other
    nodes, edges, roots, subgraphs, and metadata are shared
    unchanged.
    """
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

    return GraphDocument(
        spec=GraphSpec(
            schema_version=doc.spec.schema_version,
            nodes=tuple(new_nodes),
            edges=doc.spec.edges,
            designated_roots=doc.spec.designated_roots,
            subgraphs=doc.spec.subgraphs,
        ),
        metadata=doc.metadata,
    )


class _ExecutionProvider:
    """Internal implementation of the Execution protocol.

    Private. Holds only the catalog dependency; every run keeps its
    state function-local so concurrent runs stay isolated.
    """

    def __init__(self, catalog: Catalog) -> None:
        self._catalog = catalog

    def _admit_nodes(
        self, nodes: Sequence[NodeSpec]
    ) -> tuple[dict[str, AdmittedOperation], tuple[ValidationIssue, ...]]:
        """Admit all referenced operations for nodes in graph.

        Returns the per-node admitted map, or a single
        ``ADMISSION_FAILED`` issue naming the first failing node.
        """
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
        """Assemble and bound-check inputs for a node.

        Edge-fed ports are taken from upstream node outputs; any
        remaining declared input port falls back to the frozen
        request inputs under the port key or the qualified
        ``"<node_id>.<port_key>"`` key. Ports with no source stay
        absent, leaving missing-data policy to the implementation.

        Raises:
            ExecutionBudgetExceededError: If an assembled input
                series exceeds ``budget.max_samples``.
        """
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
        """Execute single node with restricted, declaration-checked capabilities."""
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
        """Collect designated roots or all node outputs into a FrozenObject.

        Keys are ``"<node_id>.<port_key>"`` in both cases.
        """
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
        cancellation: CancellationToken | None = None,
    ) -> tuple[
        dict[str, dict[str, Any]],
        tuple[ValidationIssue, ...],
        tuple[tuple[str, int], ...],
    ]:
        """Iterate through ordered nodes, execute and enforce limits.

        Before each node the loop checks the elapsed budget and, at
        every ``cancellation_check_nodes`` boundary, the caller
        token; then the admitted implementation validates the node
        parameters and reports its warm-up samples, inputs are
        assembled, the node executes under restricted bindings, and
        outputs are frozen against the cumulative output-value
        budget. Warm-up policy is owned by the implementation; the
        executor only consults it for the reproducibility record.

        Raises ExecutionCancellationError when the caller token is
        cancelled; all run-owned loop state is function-local and
        discarded on raise.
        """
        node_outputs: dict[str, dict[str, Any]] = {}
        total_output_values = 0
        warmups: list[tuple[str, int]] = []

        for node_idx, node in enumerate(ordered_nodes):
            elapsed = time.perf_counter() - start_time
            if elapsed > budget.max_elapsed_seconds:
                raise ExecutionBudgetExceededError(
                    f"Execution exceeded budget time: {elapsed:.2f}s > "
                    f"{budget.max_elapsed_seconds}s"
                )

            if (
                cancellation is not None
                and node_idx % budget.cancellation_check_nodes == 0
            ):
                cancellation.raise_if_cancelled()

            admitted = admitted_map[node.id]
            bind_res = admitted.contribution.implementation.validate_parameters(
                node.parameters
            )
            if not bind_res.is_valid:
                return {}, bind_res.issues, ()

            # Dynamic warm-up policy is owned by the admitted implementation;
            # the executor consults it for the reproducibility record.
            warmups.append(
                (
                    node.id,
                    admitted.contribution.implementation.warmup_samples(
                        node.parameters
                    ),
                )
            )

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

        return node_outputs, (), tuple(warmups)

    def execute(self, request: SingleExecutionRequest) -> SingleExecutionResult:
        """Run the numbered single-run path (see ``Execution.execute``)."""
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

        # 5. Execute nodes in order; caller cancellation raises and discards
        #    all run-owned loop state (it is function-local).
        try:
            node_outputs, exec_issues, warmups = self._run_execution_loop(
                ordered_nodes,
                admitted_map,
                norm_doc,
                frozen_inputs,
                budget=budget,
                start_time=start_time,
                cancellation=request.cancellation,
            )
        except ExecutionCancellationError:
            return SingleExecutionResult(
                success=False,
                issues=(_cancellation_issue(),),
                elapsed_seconds=time.perf_counter() - start_time,
            )
        if exec_issues:
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
        node_policies = tuple(
            (node.id, admitted_map[node.id].spec.numerical_policy)
            for node in norm_doc.spec.nodes
        )

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
            node_warmup_samples=warmups,
            node_policies=node_policies,
        )

        return SingleExecutionResult(
            success=True,
            outputs=frozen_final,
            reproducibility=reproducibility,
            issues=(),
            elapsed_seconds=total_elapsed,
        )

    def execute_batch(self, request: BatchExecutionRequest) -> BatchExecutionResult:
        """Run every trial through the single-run path (Execution.execute_batch)."""
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
        batch_issues: list[ValidationIssue] = []

        for trial in request.trials:
            if time.perf_counter() - start_time > request.budget.max_elapsed_seconds:
                raise ExecutionBudgetExceededError(
                    "Batch execution exceeded elapsed time budget"
                )

            if request.cancellation is not None:
                try:
                    request.cancellation.raise_if_cancelled()
                except ExecutionCancellationError:
                    overall_success = False
                    batch_issues.append(_cancellation_issue())
                    break

            trial_doc = _apply_trial_overrides(doc, trial)
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
                cancellation=request.cancellation,
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
            if any(i.code == "EXECUTION_CANCELLED" for i in run_res.issues):
                batch_issues.append(_cancellation_issue())
                break

        return BatchExecutionResult(
            success=overall_success,
            trials=tuple(trial_results),
            issues=tuple(batch_issues),
            elapsed_seconds=time.perf_counter() - start_time,
        )

    def _stitch_semantic_programs(
        self,
        ordered_nodes: Sequence[NodeSpec],
        node_programs: Mapping[str, SemanticProgram],
        norm_doc: GraphDocument,
    ) -> SemanticProgram:
        """Stitch per-node lowered SemanticPrograms into a unified program.

        Cross-node ValueRefs are rewired through the graph's edge
        connections, and program inputs not fed by an edge are
        collected once.
        """
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

    def _lower_all_nodes(
        self,
        ordered_nodes: Sequence[NodeSpec],
        target: LoweringTarget,
    ) -> tuple[dict[str, SemanticProgram], ExportResult | None]:
        """Lower every node to the exact target, with node attribution.

        Exceptions from an implementation's ``lower`` surface as a
        ``LOWERING_FAILED`` issue naming the node and plugin ref;
        reported lowering issues without a node binding are
        re-attributed to the lowering node.

        Returns the per-node programs, or the attributed failure result.
        """
        node_programs: dict[str, SemanticProgram] = {}
        for node in ordered_nodes:
            admitted = self._catalog.admit(node.plugin_ref, node.operation_id)
            ctx = _LocalLoweringContext(target, prefix=node.id)
            try:
                lowered = admitted.contribution.implementation.lower(
                    ctx, node.parameters
                )
            except (ValueError, TypeError, RuntimeError, ArithmeticError) as err:
                return {}, ExportResult(
                    success=False,
                    target=target,
                    issues=(
                        ValidationIssue(
                            path=f"nodes.{node.id}",
                            code="LOWERING_FAILED",
                            message=(
                                f"Lowering failed for node {node.id!r} "
                                f"({node.plugin_ref.to_string()}): {err}"
                            ),
                        ),
                    ),
                )
            if not lowered.success or lowered.program is None:
                attributed = tuple(
                    (
                        issue
                        if issue.node_id is not None
                        else LoweringIssue(
                            code=issue.code,
                            message=(
                                f"{issue.message} "
                                f"[node={node.id}, "
                                f"plugin={node.plugin_ref.to_string()}]"
                            ),
                            node_id=node.id,
                        )
                    )
                    for issue in lowered.issues
                )
                return {}, ExportResult(
                    success=False,
                    target=target,
                    issues=attributed,
                )
            node_programs[node.id] = lowered.program
        return node_programs, None

    def export(self, request: ExportRequest) -> ExportResult:
        """Lower, stitch, and run the target exporter (see ``Execution.export``)."""
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

        node_programs, lower_failure = self._lower_all_nodes(
            ordered_nodes, request.target
        )
        if lower_failure is not None:
            return lower_failure

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
        try:
            exp_res = exporter_impl.execute(
                {"program": unified_program}, EMPTY_FROZEN_OBJECT, mock_bindings
            )
        except (ValueError, TypeError, RuntimeError, ArithmeticError) as err:
            return ExportResult(
                success=False,
                target=request.target,
                issues=(
                    ValidationIssue(
                        path=f"target.{request.target.target_id}",
                        code="EXPORT_FAILED",
                        message=(
                            f"Exporter {exporter_ref.to_string()} failed on the "
                            f"combined program: {err}"
                        ),
                    ),
                ),
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
        """Require the live catalog, build the provider, and publish it."""
        catalog = context.require(HOST_CATALOG)
        self._provider = _ExecutionProvider(catalog)
        context.provide(HOST_EXECUTION, self._provider)


def _execution_feature() -> Feature:
    """Construct private execution feature. Imported only by app.host.bootstrap."""
    return _ExecutionFeature()

# Workspace and Plugin Implementation Pipeline

> **Purpose:** Start-to-finish delivery standard for workspace plugins (Track W)
> and concrete non-workspace plugins (Track P).
> **Reciprocal audit:** [Workspace and Plugin Implementation Audit](workspace_plugin_implementation_audit.md).
> **Authority:** [AGENTS.md](../../AGENTS.md), [PROJECT.md](../PROJECT.md),
> [ARCHITECTURE.md](../ARCHITECTURE.md), and the applicable family README.

The pipeline defines how to build and prove a declared scope. It does not certify
existing code, establish new public APIs, change product status, or authorize
implementation. Every implementation follows the plan and approval gates in
AGENTS.md. Donor informs; specification owns. SQX parity requires independent
evidence beyond completing this process.

The pipeline and audit share the closed control catalogue in section 6. Change
both documents together whenever a control is added, removed, or changes meaning.
A delivery obligation without an audit procedure, or an audit obligation without
a delivery requirement, is a documentation defect.

## 1. Choose the development track and owning layer

A workspace is a plugin of kind `workspace`, but its delivery obligations differ
from those of an indicator, exporter, optimizer, or other concrete concept.

| Work requested | Track | Deliverable and boundary |
|---|---|---|
| Workspace commands, selection, views and supported user workflows | W | One workspace declaration plus explicitly scoped UI/host integration; no quantitative algorithms in the workspace |
| Concrete non-workspace behavior | P | One cohesive plugin file plus tests and evidence; no requirement to create an unrelated workspace |
| Both | W and P | Separately scoped units and verdicts; neither unit's success proves the other |
| New host owner, metamodel, renderer vocabulary or plugin family | Prerequisite architecture work | Explicitly approve that boundary change before relying on it; neither track implicitly authorizes it |
| Informational shell or host diagnostic screen | Classify first | Do not invent a quantitative plugin or algorithm merely to fit this guide |

### Responsibility matrix

| Owner | Owns | Must not own |
|---|---|---|
| `app/plugins/workspaces/<slug>.py` | Workspace identity, commands, accepted children and view metadata | Child algorithms, shared infrastructure, durable storage or backend authorization |
| `app/plugins/<family>/<slug>.py` | One concept's behavior, configuration, parameters, bounds, ports, policies, compatibility, lowering and presentation metadata | Another plugin's implementation or a parallel registry |
| Shared `app/plugins/` modules | Universal `schema`, `spec`, `algebra`, `lowering`, `wire` vocabulary | Plugin-specific formulas, parameter copies or concrete plugin lists |
| `app/host/<owner>.py` | Co-located public contracts, generic provider implementation and lifecycle | Quantitative concept algorithms or workspace-specific dispatch switches |
| `app/kernel/` | Business-neutral, standard-library composition primitives | Product, plugin, UI, persistence or integration logic |
| `app/ui/` | Presentation, catalog cache, recoverable drafts and local view state | Numerical policy, durable truth, authorization or copied backend schemas |
| Family README | Descriptive plugin index, shared policy, scoped status/evidence links | A second executable parameter or behavior specification |

Concrete code imports only permitted shared vocabulary and designated public host
contract symbols allowed by architecture and its family policy. No concrete sibling
imports, private host objects, kernel runtime/context access, or ambient registry
lookups. A stricter family policy remains applicable until explicitly reconciled.
Report authority conflicts rather than silently selecting convenient wording.

Shared contracts and implementations may occupy the same host file. Importing a
contract must define, not construct or start, its provider. Optional provider
libraries must not become import-time requirements. Check transitive imports,
annotations, decorators, bases, defaults and module-qualified access as well as
direct imports. All Python package initializers remain empty or docstring-only.

### Imports, structured logging and flow tracing

Operational observability is a delivery requirement, not an optional debugging
addition. Every W or P plan declares which flows must be observable, who emits
their events, how they are correlated, where they can be inspected, and the
evidence proving that behavior. Pure computations can rely on their host execution
boundary; they need not emit events internally. Apply reciprocal control WP-C13.

**Import order and construction discipline**

Use the Google/Ruff-compatible order:

1. `from __future__ import annotations` where applicable.
2. Python standard-library imports.
3. Approved third-party imports.
4. Permitted local shared/public contracts and allowed kernel types.
5. Type-checking-only imports under `if TYPE_CHECKING:` when needed.

Concrete sibling implementation imports remain forbidden. Do not restore the
legacy kernel logger or add an ambient module-level service lookup. Host code
receives `Telemetry` through its declared `HOST_TELEMETRY` capability. Only where
architecture and family policy permit may another consumer use the public
telemetry contract through an explicitly approved binding.

Do not configure handlers, global logging, sinks or subscriptions in plugin
modules, import paths or factories. Sink configuration and lifecycle belong to
the host/composition owner. Observability must not introduce hidden coupling.

**Ownership of observable flows**

| Boundary | Observation responsibility |
|---|---|
| UI/workspace action | Identify the command and request; display the actual outcome. Browser-only diagnostics do not prove backend execution. |
| Gateway/host orchestration | Observe admission, start, outcome, elapsed duration and relevant lifecycle transitions; carry safe correlation across supported handoffs. |
| Pure plugin operation | Return typed results/issues; the invoking host observes the operation boundary. No routine logging inside calculations. |
| Effectful operation | Declare observable decisions, retries, external interactions and side effects through a supported host-owned emission path. |
| Telemetry owner/sink | Own delivery, subscription cleanup, health/drop reporting and any approved storage/retention configuration. |

`Telemetry.emit` is asynchronous and the current plugin `execute` contract is
synchronous. Do not bridge them using `asyncio.run`, private loops, unawaited
coroutines or fire-and-forget tasks inside plugins. Use host-boundary observation;
if internal plugin events are required, record the missing supported bridge as
prerequisite contract work. A pure helper does not gain kernel lifecycle access
merely because logging would be useful.

**Flow-event worksheet**

Complete one row per meaningful boundary/transition in each scoped flow. This is
an operational contract worksheet, not an invented extension to `WorkspaceSpec`
or `TelemetryEvent`.

| Flow/boundary | Event name and trigger | Level | Correlation and safe fields | Emitter/contract | Observer/sink and delivery limits | Acceptance evidence |
|---|---|---|---|---|---|---|
| `<flow>` | `<stable name; exact condition>` | `<level>` | `<allowlisted values>` | `<actual owner/API>` | `<inspectable destination; limits>` | `<scenario and oracle>` |

- Use stable event names describing an action/state, not interpolated messages
  or a central list of concrete plugins. Host events may identify exact plugin
  refs and operation IDs in bounded fields without importing implementations.
- Record public-operation boundaries, state transitions, meaningful decisions,
  admission rejection, retries, external interactions, side effects and failures
  where applicable. Define observable successful, failed, rejected and cooperative
  cancellation paths without claiming guaranteed terminal events after a crash.
- Use safe correlation identifiers at supported handoffs. Planning vocabulary may
  include `request_id`, `run_id`, `job_id`, `parent_id`, `workspace_id`,
  `plugin_ref`, `operation_id`, `attempt`, `outcome`, `error_code` and
  `elapsed_ms`. Choose applicable fields and validate/bound externally supplied
  identifiers. Do not use account identities, credentials or session tokens.
- Correlation must be propagated, not replaced with unrelated IDs at every layer.
  Retry attempts remain attributable to the parent action. Distinguish per-request
  transport outcome from eventual execution/job outcome to avoid contradictory
  completion claims. Do not claim distributed tracing from local event names.
- Use DEBUG for bounded diagnostic detail, INFO for normal significant transitions,
  WARNING for recoverable degradation/retries, and ERROR for failed operations or
  exhausted recovery. Define deviations by requirement, not personal preference.
- Pure helpers, per-bar/per-tick loops and other hot paths do not log by default.
  If required, define aggregation/sampling/rate and cardinality limits explicitly;
  evidence must show that observation does not overwhelm the computation.

**Privacy, failure isolation and delivery truth**

Use an allowlist of structured scalar fields. Never log credentials, personal or
account information, full sensitive inputs/outputs, machine/workspace paths,
fencing/session tokens or raw/unbounded exception text. Prefer stable error codes
and reviewed safe summaries. Length truncation is not redaction; hashing sensitive
identifiers is not automatically anonymization. Test nested failure paths too.

The current [telemetry contract](../../app/host/telemetry.py) provides immutable
in-process events, at most 32 scalar fields, bounded strings (512 characters),
finite numeric fields and isolated observer exceptions. It does not automatically
redact values, persist events, timestamp them, buffer every event, propagate
cross-process correlation, or bound a slow subscriber's latency. Its bounded
diagnostic ring is not a complete application log. These are implementation facts,
not delivery guarantees to infer from this standard.

Declare actual subscriber/sink availability, retention, overflow/drop behavior,
ordering, performance bounds and shutdown cleanup. Record unsupported guarantees
as gaps. Ordinary diagnostic failure should not change a quantitative result;
failure and dropped-delivery handling must use the approved host policy and must
not be silently hidden or recursively logged into the failing observer. Mandatory
durable audit records, if required, need an explicitly approved fail-closed
capability; do not mistake optional telemetry for that authority record.

**Required observation evidence**

Use an isolated capturing observer to verify expected event names/fields and
causal ordering, shared correlation, attributable retry/outcome paths, redaction
with synthetic sentinel secrets, field bounds and hot-loop noise limits. Inject
observer failure and verify the declared result-isolation/diagnostic behavior.
Check subscription cleanup and actual sink inspection where claimed. Test delay,
overflow, retention or process boundaries only when supported and claimed; missing
support stays explicit rather than being labelled passed. A capture fixture proves
event emission, not durable logging or end-to-end production traceability.

## 2. Common intake, planning and evidence rules

### 2.1 Research before writing source

1. Inspect Git status and revision; preserve unrelated work. Read authority,
   applicable READMEs, active contracts, implementation, callers, tests and examples.
2. Establish whether each requested capability exists, is a target, or is unknown.
   File presence, a metadata field or a test name is not implementation proof.
3. Resolve the owning track, family, stable identity and exact version. Reuse
   registered requirement/decision IDs where available; record missing IDs as gaps.
4. Inspect relevant donor artifacts and official documentation when donor behavior
   informs the task. Separate observation, inference and target decisions.
5. Identify prerequisites and source-backed acceptance oracles. Do not assume
   that a named algorithm, framework or host service supplies the requested semantics.

### 2.2 Intake worksheet

Complete this worksheet in the task plan for each unit. Angle-bracket values are
placeholders to resolve before approval, not prescribed new paths or contracts.

```text
TRACK: W | P
UNIT_REF: <stable plugin ID and exact version>
FAMILY_README: <existing approved family README>
PRODUCTION_FILE: <one owning plugin file>
REQUIREMENTS_AND_DECISIONS: <registered IDs or explicit gaps>
BASELINE_COMMIT: <full SHA; identify uncommitted candidate separately>
SCOPE_AND_NON_GOALS: <capabilities delivered and deferred>
INPUTS_AND_OUTPUTS: <actual types, units, schema versions and errors>
COMMANDS_OR_OPERATIONS: <IDs, semantics, bindings and availability>
PUBLIC_DEPENDENCIES: <exact operation refs and approved host contract symbols>
EFFECTS_AND_STATE: <operation effects, run-local state, durable owner, lifecycle>
OBSERVABLE_FLOWS: <event worksheet, emitter, correlation, sink and evidence>
CONSUMERS: <intended callers/UI/exporters and evidence required for each>
ACCEPTANCE_ORACLES: <independent expected observations>
TESTS_AND_USAGE: <exact approved paths and executable commands>
CONTROLS: <C+W or C+P, with applicability>
EVIDENCE_OUTPUTS: <approved task report/manifest paths and existing schemas>
```

### 2.3 Plan and approval

Use the [implementation-plan template](../templates/implementation-plan.md) under
`.agents/logs/<timestamp>_<task>/implementation-plan.md`. Record exact allowed
writes, interfaces, dependencies, examples, tests, rollback and residual gaps.
Present a concrete plan and wait for `APPROVED: EXECUTE` or equivalent approval.
Approval applies to the presented iteration only. Material new contracts,
dependencies, destructive targets or architecture decisions require an iteration
and renewed approval. An audit finding is not permission to fix source.

The plan must distinguish declaration, implemented operation, UI reachability,
integration qualification and complete product workflow. A bounded slice may be
complete for its explicit scope while other commands remain unavailable.

### 2.4 Evidence discipline

- Record the tested revision and candidate source fingerprints, exact commands,
  exit codes, execution time, fixtures, environment and result artifacts. A baseline
  commit alone does not identify later uncommitted changes. Do not embed a future
  containing commit's hash in its own tracked receipt.
- Map each requirement/control to its implementation and evidence, with limitations.
  A declaration or manifest is a claim container, not its own proof.
- Separate local, unit, integration, UI/browser, provider, performance and release
  evidence. Passing one does not establish the others. Use bounded, safe receipts;
  exclude secrets, raw sensitive payloads and machine-specific absolute paths.
- Use approved task reports or existing acceptance schemas. Do not silently invent
  mandatory evidence directories, registries or machine-readable schema formats.
- Donor records follow [reimplementation.schema.json](evidence/reimplementation.schema.json)
  and the owner's ledger procedure. Read the ledger and schema before writes; if
  the ledger is absent, explicitly scope initialization. Record atomic claims,
  logical roots, narrow source locations, method, relation, access dates, SHA-256
  for stable local sources, limitations, mappings, review state and repository SHA.
- Allocate donor IDs from the highest existing number plus one; never reuse IDs.
  Preserve contradictions and link superseding records. Preserve the required
  clean-room booleans. Mark validation passed only with actual observations,
  artifacts and execution timestamps. Parse both JSON files, validate the schema,
  resolve source/record links and verify mapped IDs against repository truth.
- Stale evidence cannot establish current acceptance. Preserve it as historical
  evidence, record what changed, and obtain current evidence for affected claims.

## 3. Track W: build a workspace independently

Follow W1-W11 in order. Shared entry rules apply; completing Track P is not a
prerequisite unless the approved workspace scope actually needs a missing plugin.

### W1. Classify and inventory the workspace

**Inputs:** requested workflow, authorities, family README, current UI and catalog.
Identify the user outcome and whether the unit is a workspace, informational
shell, diagnostic tool or algorithm. Inspect available host services and child
operations. Distinguish donor navigation declarations from runtime verification.

**Exit evidence:** named owner, stable workspace reference, bounded workflow,
existing implementation inventory, missing capabilities and applicable W controls.

### W2. Specify commands and acceptance before implementation

Create a command matrix with one row per action:

| Command ID | User input | Actual operation/host contract | Response fields | Availability | Success/error oracle |
|---|---|---|---|---|---|
| `<id>` | `<typed input>` | `<exact supported binding>` | `<real fields>` | `<functional/deferred/unavailable>` | `<observable result>` |

Separate local editing commands from backend operations. Name the missing
capability for each deferred action. Adding command metadata does not implement
that capability. Accepted plugin kinds are selection vocabulary, not proof of
specific algorithm support. Use exact versions and operation IDs for execution.

**Exit evidence:** command matrix, actual data source/input contract, state
ownership and explicit non-goals. Include invalid, unavailable, denied, stale,
partial and successful outcomes where the underlying contract supports them.

### W3. Design the declaration and integration boundary

Use the actual [shared metamodel](../../app/plugins/spec.py). The current
`WorkspaceSpec` describes identity, title, description, commands, views and
accepted kinds. `WorkspaceCommand` is metadata; it is not an executable binding
contract. Do not invent fields, dispatch registries or runtime guarantees.

Specify exact host/client requests and result mappings, and how frontend actions
use them. Reuse catalog introspection and supported versioned endpoints. A new
universal contract or renderer is separately reviewed scope. A component/route
string cannot install new React behavior by itself.

**Exit evidence:** source-grounded interface mapping and approved renderer/UI
ownership. One Python file owns the workspace declaration; UI code owns rendering,
not copied authoritative schemas or child algorithms.

Include the flow-event worksheet from section 1. Bind request/operation observation
to the actual host boundary; expose any missing correlation or sink support before
promising a traceable workflow.

### W4. Obtain approval of the exact workspace plan

Apply section 2.3. Include declaration, UI, client/generator and integration-test
paths actually needed. Specify which unsupported controls will be disabled and
how removal and shared-child behavior will be proved. Resolve topology-check
exceptions explicitly rather than weakening checks during implementation.

**Exit evidence:** owner approval for the presented plan iteration.

### W5. Implement the cohesive declaration

Use this conceptual order in the owning file:

1. Purpose/scope docstring and permitted imports.
2. Stable `PluginRef` and workspace-local command/view declarations.
3. Immutable `WorkspaceSpec` and `PluginSpec(kind="workspace")`.
4. Pure zero-argument `plugin()` returning `PluginContribution`.

A declarative workspace may have no executable operations and needs no automatic
service lifecycle. Discover it through the existing bounded catalog. Do not
import child implementations or construct host providers. Requirements beyond
the current descriptor vocabulary stay explicit gaps until approved evolution.

**Exit evidence:** valid contribution, import/factory purity and catalog discovery.

### W6. Connect supported commands through admitted boundaries

Compose immutable graph/documents or actual host request values. Resolve exact
plugin/operation identities through host selection and admission. UI availability
is presentation only; backend authorization and admission remain authoritative.
Do not place quantitative algorithms, storage policy or authorization in views.

For a bounded slice, deferred commands stay unavailable even if an unrelated
plugin of a matching kind is installed. Future support needs an explicit reviewed
binding and acceptance evidence, not kind-presence inference.

**Exit evidence:** one real request/result trace for each supported action class,
including rejection paths; no workspace-specific backend switch or sibling import.

### W7. Implement honest UI and state handling

Render parameters from plugin schema within the approved renderer vocabulary.
Keep catalog cache, drafts and view state separate from backend durable records.
Preserve unknown references as readable unavailable placeholders; do not silently
rewrite or execute unsupported document versions.

Map outputs to actual response fields. For the retained graph-evaluation slice,
`SingleExecutionResult` provides `outputs`, `reproducibility`, `issues`, `success`
and `elapsed_seconds`; evaluation alone is not a trading backtest. Do not fabricate
trade lists, performance metrics, provenance timestamps or optimization results.

Use real transport states. If a synchronous endpoint provides no progress or
interactive cancellation, display an indeterminate running state until response
or failure. Do not invent percentages with timers. A browser abort or timeout
does not prove server work stopped. State cooperative cancellation boundaries
and test eventual completion only for bounded supported operations.

**Exit evidence:** UI state/response mapping, accessibility and interaction checks
appropriate to the view, and no mock data masquerading as a completed operation.

### W8. Prove workspace independence

Use temporary plugin trees and isolated stores. Add, disable and physically remove
the workspace; peers must retain their shared children and host services. Verify
missing workspace/node references remain readable and explicitly unavailable.
Distinguish whole-catalog changes from stable unrelated entry/dependency hashes.

Select the same supported child in two workspaces and execute valid graphs through
the host. Discovery proves metadata availability, not graph execution. Test that
an unrelated optimizer/cross-check cannot enable a deferred command.

**Exit evidence:** removal, sharing and availability regression results without
deleting production files or touching active user data.

### W9. Complete focused tests and a bounded usage scenario

Cover declaration/schema/identity, import purity, real selection and dispatch,
request/response conformance, unavailable/error states, UI cleanup, stale results
where relevant, and supported resource/timeout behavior. Use exact approved paths
with `--no-cov` during iteration. Test the actual UI entry point, not only helpers.

Provide deterministic offline usage through public composition/catalog/execution
boundaries. Integrate with at least one real supported plugin for the claimed
workflow. Component mocks may isolate tests but do not prove real gateway or
provider qualification. Novel interactions need applicable browser evidence.

**Exit evidence:** recorded focused commands, outputs and limitations; separate
declaration, execution, UI and end-to-end acceptance results.

### W10. Audit and qualify the candidate

Apply C+W controls using the audit's workspace procedure. Investigate failures
within approved paths; record material deviations before expanding scope. Run
candidate qualification and applicable UI checks from section 5. Do not promote
partial integration or a mock-backed view to complete workstation status.

**Exit evidence:** per-control verdicts, completed checks and scoped recommendation.

### W11. Reconcile documentation and hand off

Update the family index and affected scope documentation only within approved
paths; do not duplicate the workspace descriptor. Use the
[walkthrough template](../templates/walkthrough.md) for exact changes, commands,
results, deviations, residual risks, Git status and proposed commit message.
Retain unavailable commands and unsupported consumer claims explicitly.

**Exit evidence:** reviewable walkthrough; owner retains commit/merge/push authority.

## 4. Track P: build a concrete non-workspace plugin independently

Follow P1-P11 in order. A plugin may be built and verified without creating a new
workspace. Applicable numerical, algebra and export obligations depend on what
the plugin actually claims, not on a blanket assumption that every kind calculates
an indicator series.

### P1. Establish one concept and approved family

Inspect authority, current family policy, consumers, metamodel, tests and evidence.
Identify the stable concept, operation boundaries and existing alternatives.
Distinguish plugin algorithm from host infrastructure. A new family needs approved
discovery/topology scope; do not smuggle plugin logic into shared modules.

**Exit evidence:** concept/family owner, stable reference, applicable P controls,
requirements and explicit contract or source gaps.

### P2. Specify behavior and independent acceptance oracles

Write input/output types and units, defaults, valid domain, parameter interactions,
errors, supported consumers, bounds and compatibility. For numerical behavior,
define warm-up/lookback as functions of validated parameters; seeding, flat and
monotonic series, missing-data propagation/recovery, non-finite values, division by
zero, ordering, timezone, precision and rounding. A familiar formula name is not
a complete specification.

For stochastic algorithms, specify seed/reproducibility and finite search limits.
For non-numerical plugins, define an appropriate behavioral oracle rather than
inventing numerical obligations. Derive independent hand examples or external
reference observations; copying implementation output is not an independent golden.

**Exit evidence:** behavioral contract, edge-case table and expected observations.

Declare the observation scope and owner using section 1. For pure operations,
specify host-boundary events and exclude hot-loop logging. For effectful behavior,
identify the supported emission path for retries, decisions and failures.

### P3. Design the single-file contract and compatibility

Keep concept-specific config, schema, constraints, optimizer bounds, operations,
ports, compatibility, policies, lowering and presentation metadata together.
Separate validity limits from search bounds. Reject unsupported values and mutable
leaves instead of silently coercing them. A frozen outer object is not enough.

Use real universal types. Distinguish implementation version, metamodel major,
host capability major, graph/wire schema and artifact version. Specify migration
or explicit unavailability for changes; retain originals and unsupported versions
losslessly. Initially respect the catalog's supported version-selection policy.

**Exit evidence:** canonical descriptors, exact operation interfaces, typed ports
and algebra placement where applicable, compatibility and effect declarations.

### P4. Obtain approval of the exact plugin plan

Apply section 2.3. Include all real consumer, test, example and evidence owners.
Specify actual lowering targets, independent oracles and add/remove proofs.
Separate required universal evolution from the concrete implementation. Do not
silently add dependencies, backend families or plugin-specific frontend controls.

**Exit evidence:** owner approval for the presented plan iteration.

### P5. Implement cohesive behavior and self-description

Use this conceptual order, omitting genuinely inapplicable sections:

1. Purpose/semantics/edge-policy docstring; permitted imports.
2. Stable identity/version and plugin-local immutable config/value types.
3. Private validation/numerical helpers and operation implementations.
4. Parameter schema, ports, policies, algebra and lowering contributions.
5. Immutable operation/plugin descriptors and pure `plugin()` factory.

No companion plugin-specific contracts, formulas, models, optimizer spaces or UI
schema files. Universal vocabulary may be imported; concrete siblings may not.
Keep runtime state private to a run unless an approved host-owned resource is
explicitly required. Follow strict public typing, Ruff style and applicable
Google-style docstrings; no bare/silent failures or application prints.

**Exit evidence:** one owning file with actual behavior and descriptors in agreement.

### P6. Bind capabilities and enter discovery safely

Declare required/optional capabilities per operation, using the approved typed
binding mechanism. Do not enumerate providers or import host internals. Factory
purity, operation effects, run-local state and service lifecycle are separate
questions. Installation alone must not activate I/O or expensive/mutating work.

Use bounded configured family roots, pre-import exclusions, canonical ordering,
identity/schema validation and atomic snapshots. Reject duplicates/incompatibility;
failed refresh retains the last valid snapshot, while initial failure exposes
unavailable readiness. A live registry is not an immutable catalog input.

External effects use approved host capabilities: bounded timeouts, retry/rate
policies, redaction, permissions, resource budgets and lifecycle ownership.
Plugins do not receive raw connections, ad-hoc SQL, subprocess/network clients,
filesystem roots, kernel contexts or private lifecycle entry points.

**Exit evidence:** pure import/factory, admitted operations, discovery failures and
declared resource ownership. Optional absence gates only affected operations.

### P7. Verify semantics, state and failure behavior

Run independent goldens and boundary cases from P2, invalid parameters/schema,
empty/insufficient/missing/non-finite inputs, warm-up changes, ordering and units.
Prove input immutability and concurrent run isolation; repeat identical frozen
inputs/parameters/versions/seeds. Live data must be frozen before reproducibility
can be claimed. Compare scalar and accelerated paths if both exist.

Test budget, permission, capability absence, failure and cancellation behavior
actually supported by the operation. For resource-using operations, test owned
cleanup and failures through host integration. Do not confuse reverse iteration
with full rollback/drain guarantees; bindings must remain valid during cleanup.

**Exit evidence:** oracle comparisons and bounded failure/resource results.

### P8. Prove algebra, wire and claimed consumer compatibility

Use the same versioned document, canonical parameters, typed ports, units and
alignment across execution, generators, optimizers, UI and exporters. Validate
cycles and resource bounds; recurrence is declared node state, not a hidden cycle.
Verify canonical JSON round trips, explicit missing encodings and unsupported
document retention; do not use Python hashes as durable fingerprints.

An advertised export needs actual plugin-owned lowering and generic target
emission. Test numerical/state/missing-data semantics, not merely nonempty text.
Unsupported nodes or targets fail with attributed reasons. New universal IR
semantics need reviewed evolution. Optimizer consumers use declared eligibility
and bounds; UI consumers project schema within approved renderers.

**Exit evidence:** evidence per claimed consumer/target; unverified integration is
explicitly partial or unqualified, never inferred from a descriptor.

### P9. Prove orthogonality and offline usability

Add/disable/remove the plugin in isolated temporary trees. Verify peers still
discover and execute unchanged; referenced missing nodes remain lossless and
unavailable. Compare stable unrelated entry/dependency fingerprints and outputs,
allowing whole-catalog membership fingerprints to change. Admitted runs use pinned
versions or fail explicitly; no silent substitution after refresh/removal.

Provide one deterministic, bounded, secret-safe primary-purpose offline example
through supported public boundaries, with meaningful results and cleanup. It must
not reimplement the formula or imply provider/browser/release qualification.

**Exit evidence:** physical-removal proof and an executable usage receipt.

### P10. Audit and qualify the candidate

Apply C+P controls and section 5. Non-numerical or non-algebra plugins justify N/A
for truly absent responsibilities; missing required implementation is not N/A.
Retain scope-specific gaps and do not hide them behind aggregate coverage or a
successful example. Changes outside approved scope require a plan iteration.

**Exit evidence:** reciprocal audit, candidate checks and qualified consumer scope.

### P11. Reconcile documentation and hand off

Document behavior in the owning module and shared policy/index in the family
README without copying executable schemas. Retain actual evidence, limitations,
versions and affected requirements. Complete the walkthrough and owner commit
gate as in W11. No commit, push, merge or history rewrite is implicit.

**Exit evidence:** reviewable implementation and evidence package, with no claim
that an unrelated workspace or unsupported product workflow is complete.

## 5. Verification, completion and maintenance

### Verification cadence

During implementation, use exact approved affected test paths and `--no-cov`.
Existing flat test ownership remains valid; do not relocate tests solely to match
an illustrative pattern. A typical substituted command is:

```text
uv run pytest --no-cov <approved-focused-test-path> -v
uv run python -m <approved-offline-example-module>
```

For a complete candidate, run the actual repository gates:

```powershell
uv run python scripts/architecture_check.py
uv run python scripts/ci_check.py
```

Generated client changes use the actual generator, never hand-maintained output:

```powershell
uv run python scripts/generate_ui_contracts.py
uv run python scripts/generate_ui_contracts.py --check
```

For applicable UI/catalog/schema/algebra/transport/renderer changes:

```powershell
npm --prefix app/ui run typecheck
npm --prefix app/ui run test
npm --prefix app/ui run build
```

Plan any needed browser commands and fixtures explicitly. Respect the configured
minimum 80% branch-aware application coverage; aggregate coverage is not a
substitute for measured changed code or semantic acceptance. Record unavailable
checks honestly. Do not repeatedly run full CI during focused editing or broaden
testing after success without a new failure, change or unresolved concern.

### Completion gate

Every applicable control has a verdict and source-bound evidence. Any mandatory
FAIL, required missing evidence or unresolved PARTIAL prevents a full-compliance
claim for that scope. A bounded delivered slice must name excluded operations and
consumers. N/A requires evidence that the responsibility does not apply.

A temporary architecture/topology whitelist exception requires explicit owner
approval, its exact scope and residual deviation. It is not proof of the general
no-central-edit guarantee. Preserve unrelated user changes and active data.

Maintain plan iterations and the walkthrough, record the actual working tree,
and propose a commit message. Only the owner authorizes Git mutations after
review. Existing evidence does not authorize autonomous remediation or publication.

## 6. Reciprocal control catalogue

These are the canonical delivery obligations. Track W assesses C+W; Track P
assesses C+P. The audit contains one detailed procedure for every ID below.

| ID | Title | Delivery obligation |
|---|---|---|
| WP-C01 | Authority and approved scope | Resolve unit, requirements, conflicts and exact writes before execution; preserve approval gates. |
| WP-C02 | Identity, version and ownership | One canonical identity/version has one production owner and family; version compatibility and status are explicit. |
| WP-C03 | Locality and import purity | Co-locate concept-specific truth; pure imports/factories/initializers; permitted symbols only, including transitive access. |
| WP-C04 | Discovery and admission | Bounded canonical catalog discovery, pre-import exclusion, atomic validation, no runtime concrete list; installation, enablement and admission differ. |
| WP-C05 | Immutable contracts and wire | Actual typed contracts, deep immutability, canonical serialization and lossless unsupported versions; generated clients conform. |
| WP-C06 | Capabilities, effects and security | Explicit typed bindings and operation effects; no ambient authority, private host access, secrets or unauthorized external mutation. |
| WP-C07 | State, persistence and resources | One declared durable owner, authorized record reachability/retention, isolated stores, bounded resources and owned cleanup. |
| WP-C08 | Orthogonality and removal | Add/change/disable/remove preserves unrelated behavior and data; pinned dependencies and unavailable references are explicit. |
| WP-C09 | Requirements and consumer traceability | Trace each scoped requirement/operation/workflow through actual producers and consumers to independent acceptance evidence. |
| WP-C10 | Tests, usage and coverage | Meaningful focused tests, deterministic offline usage, applicable integration and source-bound branch coverage; no surrogate completion claims. |
| WP-C11 | Evidence and documentation | Current revision/source fingerprints, truthful statuses, clean-room donor procedure and preserved history; no duplicated executable schemas. |
| WP-C12 | Qualification and delivery gates | Reciprocal audit, required candidate checks, walkthrough, exact results/residuals and separate owner commit authorization. |
| WP-C13 | Operational logging and flow tracing | Declared event flows, actual emission ownership, safe correlation, levels, redaction, bounded noise, failure handling and inspectable delivery evidence. |
| WP-W01 | Command and workflow scope | Complete command matrix distinguishing supported, local, deferred and unavailable actions with real inputs/outputs and oracles. |
| WP-W02 | Operation and host binding | Supported actions use real exact operation/host contracts; metadata does not imply executable dispatch or quantitative behavior. |
| WP-W03 | Workspace descriptor and views | One discoverable immutable declaration, pure factory, approved view/renderer ownership; no automatic service lifecycle. |
| WP-W04 | Exact command availability | Admission remains backend-owned; unrelated plugin kinds cannot enable deferred commands; failures are attributed. |
| WP-W05 | Schema-driven truthful UI | UI projects schema and actual results; no copied algorithms, fabricated metrics, hidden durable truth or unsupported parity claims. |
| WP-W06 | Execution and transport states | Actual loading/error/progress/cancellation semantics and bounded requests; no fabricated progress or hard-preemption claims. |
| WP-W07 | Shared children and independence | Multiple workspaces share children; removal preserves peer selection/services and readable unavailable references. |
| WP-W08 | Supported workflow integration | Real supported action-to-result path, appropriate UI/browser/accessibility checks and offline scenario prove the declared workflow. |
| WP-P01 | Cohesive concept and operations | One file owns behavior and self-description; real operation implementations match declared contracts. |
| WP-P02 | Parameter and search policy | Typed defaults, validity, constraints, units, cross-field checks and optimization eligibility/bounds are local and distinct. |
| WP-P03 | Ports and algebra | Applicable typed ports, units/alignment, exact node identities, cycle/resource validation and canonical documents. |
| WP-P04 | Numerical and error semantics | Explicit warm-up/lookback, seeding, missing-data recovery, ordering, precision and boundary/error policies where applicable. |
| WP-P05 | Determinism and run isolation | Frozen inputs, repeatability/seed policy, immutable descriptors, private run state and concurrent isolation. |
| WP-P06 | Operation effects and resources | Per-operation capabilities, effects, optional absence, resource budgets and host-owned cleanup are implemented and tested. |
| WP-P07 | Independent behavioral oracles | Independently derived goldens, edge/failure cases and scalar/accelerated comparisons prove claimed behavior. |
| WP-P08 | Optimization and export compatibility | Actual optimizer-bound consumption and lowering/emission semantic parity for each supported target; attributed rejection otherwise. |
| WP-P09 | Generic consumer reflection | Consumers share the plugin's schema/identity/semantics; supported additions need no plugin-specific engine or UI source edit. |
| WP-P10 | Usage and unsupported dependencies | Offline primary-purpose execution, exact dependencies and lossless unavailable/unsupported-version behavior are demonstrated. |

### Prior-control coverage crosswalk

This crosswalk preserves the obligations of the superseded PIP catalogue; it does
not relabel historical audit results. The older FIP model contributes independent
consumer/workflow evidence, five verdicts, state reachability, resource and safety
checks through C07-C12 and the specialized controls. Its domain/registry/context
architecture and automatic-commit language are not carried forward. The legacy
`FIP-19 LOG` discipline is explicitly retained by WP-C13 using host-owned telemetry.

| Prior control | Current coverage |
|---|---|
| PIP-01 OWNER | WP-C02, WP-P01, WP-W03 |
| PIP-02 LOCAL | WP-C03, WP-P01, WP-P02, WP-W03 |
| PIP-03 IMPORT | WP-C03, WP-C06 |
| PIP-04 ID | WP-C02, WP-C05 |
| PIP-05 SCHEMA | WP-C05, WP-P02, WP-W05 |
| PIP-06 PORTS | WP-P03, WP-C05 |
| PIP-07 SEMANTICS | WP-P04, WP-P05, WP-P07 |
| PIP-08 CAP | WP-C06, WP-P06, WP-W02 |
| PIP-09 DISCOVERY | WP-C04, WP-W03 |
| PIP-10 ENABLE | WP-C04, WP-C06, WP-W04 |
| PIP-11 ORTHO | WP-C08, WP-W07, WP-P09 |
| PIP-12 ALGEBRA | WP-C05, WP-P03, WP-W02 |
| PIP-13 UI | WP-W05, WP-P09 |
| PIP-14 EFFECT | WP-C06, WP-C07, WP-P06, WP-W06 |
| PIP-15 TEST | WP-C10, WP-P07, WP-W08 |
| PIP-16 REMOVE | WP-C08, WP-W07, WP-P10 |
| PIP-17 PARITY | WP-C09, WP-P08, WP-P09, WP-W08 |
| PIP-18 EXAMPLE | WP-C10, WP-P10, WP-W08 |
| PIP-19 EVIDENCE | WP-C11 |
| PIP-20 QUALIFY | WP-C12 |

For every future standards change, compare the canonical ID sets and meanings,
verify all links and commands, and walk through both tracks. Equality of IDs is
necessary, but semantic reciprocity requires human review of the actual duties
and audit evidence. Neither document alone certifies implementation compliance.

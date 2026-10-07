# HaruQuantAI architecture

Status: ratified structural constraints at the reset-aware P00 baseline, 2026-10-06.
Historical source: Git commit `3ede688544b1c161984573cdc25e7a36b01d4a37`,
`docs/ARCHITECTURE.md`, SHA-256
`8fdf5bb3d15386333e9bace6ad99a7eb4c6987b4ea2fd95cf43d192cbd437bb3`.
Removed implementation and historical interface versions are not current contracts.

[PROJECT.md](PROJECT.md) owns scope; [AGENTS.md](../AGENTS.md) owns contributor
process; local owning READMEs own feature/FR/decision identities and status.
[Evidence procedure](dev/evidence/README.md) distinguishes observations and decisions.

V2 alignment, 2026-10-07: target organization below extends the structural baseline;
existing approvals and implementation/parity gates remain binding.

## V2 target system and planning boundary

The [V2 implementation plan](dev/V2/README.md) organizes the Python web workstation
into thirteen feature groups and 72 capability tasks. Its [nine delivery milestones](dev/V2/delivery-plan.md)
sequence usable slices; feature/phase numbers identify ownership rather than a
strict serial dependency chain. The [planned file structure](dev/V2/README.md#full-v2-planned-file-structure)
shows proposed locations, retained UI entry points and unresolved composition files.
Those paths and F/H labels do not register capabilities or freeze package contracts.

Target one local Python application serving the API and built React frontend.
Keep configuration, lifecycle and service composition explicit. HTTP handles
commands/queries; bounded authenticated events and authoritative snapshots support
progress, logs and reconnect. Reuse the declared Pydantic/FastAPI/Uvicorn stack,
standard-library utilities and qualified numerical/data libraries. Package names
alone do not qualify behavior or Python/runtime compatibility.

F01 groups ten host capabilities in one lifecycle: bootstrap/web shell, centralized
logging, diagnostics, settings, discovery, transport, jobs, resources, persistence,
and security/sessions. Optional domains fail unavailable only at their declared
consumers. Local research precedes remote workers and advanced integrations.

The previously approved P01 host contract remains the foundation: `/api/v1`,
the versioned envelope, loopback session/origin rules, bounded projections/events
and atomic revision-checked `preferences.json` in an explicitly owned new root.
Its approved iterations remain binding. V2 adds an organizing target, not evidence
of implementation or permission to change those contracts. Full jobs, discovery,
operational storage and remote deployment still need their own approved plans.

## Five laws of spatial composability

- SC-01 Locality: one quantitative concept has one cohesive owner. Its calculation,
  configuration, defaults, typed schema, bounds, units, metadata and lowering hooks
  remain together. Universal primitives do not centralize domain business semantics.
- SC-02 Orthogonality: adding/disabling/removing a package cannot require unrelated
  peer or central-registry edits. Failures block only declared dependencies; retained
  artifacts remain inspectable with an explicit unavailable producer.
- SC-03 Explicit typed slots: collaborate through declared, versioned capabilities
  and immutable documents. No private sibling imports, ambient global registry,
  implicit settings singleton, fixture substitute or import-time side effect.
- SC-04 Hierarchical/algebraic composition: typed primitives compose pinned trees,
  pipelines, workspaces and finite project tasks. Editors, generators, simulators
  and exporters share semantic documents; UI labels cannot redefine algorithms.
- SC-05 Schema-driven description: package-owned identity, compatibility, schemas,
  defaults, constraints, units, slots and presentation metadata drive discovery and
  a bounded renderer. Hosts do not maintain manual catalogs of domain concepts.

## Spatial ownership

| Owner | Backend target | Retained UI counterpart | Responsibility |
| --- | --- | --- | --- |
| Host | `app/host/` | `ui/app/host/` | Universal lifecycle, sessions, discovery, envelopes, jobs, telemetry and resource custody; no domain algorithms |
| Workspace | `app/workspace/<Domain>/` | `ui/app/workspace/<Domain>/` | Workflow, typed slots, zero-plugin fallback and local presentation |
| Plugin | Per-feature approved backend path | `ui/app/plugins/<family>/<concept>/` | One focused capability and optional paired presentation |
| Primitives | `app/kernel/` target | `ui/app/components/` | Universal runtime/math or UI primitives; no domain contracts |

Plugin path casing/singular/plural variants in historical documents and V2 are
proposals requiring individual ratification. P00 creates no plugin package.
The approved P01 envelope/session/preferences/minimum-attachment contracts are
explicit target decisions. Further domain schemas, full discovery and mounting
contracts remain future decisions; provisional UI clients cannot ratify them.

Group work by accepted user capability, not dependency archive. One replaceable
provider, indicator, method or format may own a typed contribution; ordinary
internal functions need no plugin framework. Settings schemas and execution stay
with the same semantic owner. The host runtime index derives from validated
contributions rather than a manually maintained domain catalog.

## Dependencies and lifecycle

No peer business imports between workspaces or plugins. Workspace/plugin package
initializers are empty/docstring-only. Imports perform no I/O, environment reads,
handler setup, database access, registration or thread creation.

Host discovery validates literal identity, ownership, version compatibility and
path containment before executing contributions. Workspaces receive host-injected
capabilities and attach plugins through typed slots. Missing/removed plugins yield
explicit unavailable results; zero-plugin workspaces preserve unrelated operations.
Preparation, admission, cancellation, shutdown and cleanup have explicit owners and
logged outcomes. Exact lifecycle/state semantics must be qualified per feature.

## Shared research documents and execution

| Document or operation | Semantic owner | Shared role |
| --- | --- | --- |
| Dataset revision | F02 market data | Instrument/time/session/units, validated rows and immutable source lineage |
| Strategy revision | F03 authoring and blocks | Typed rules/parameters and qualified block/engine/export requirements |
| Run specification and execution | F04 simulation | Pinned strategy/data, costs/sizing/clocks/seed and explicit execution profile |
| Run ledger/result | F04 ledger; F05 analysis | Authoritative fills/trades/cash/equity; shared metrics and result projections |
| Search, experiment and portfolio | F06/F07/F08 | Propose candidates/scenarios/membership; reuse qualified simulation and metrics |
| Project and research procedure | F09; F13 tool orchestration | Bounded task/condition documents delegating to existing capabilities |
| Job and resource record | F01 host custody; domain payload owner | Admission/attempt/status and retained checksummed artifact references |

The common loop is dataset + strategy -> run -> retained result -> analysis,
portfolio or project. Builder, Optimizer, Retester and projects call the same
qualified simulator; they do not own separate fill/accounting engines. F05 owns
shared metrics/correlation, while methods retain their own selection objectives,
scenario rules and thresholds. Reuse does not merge distinct algorithm semantics.

Custom Projects use a bounded state machine, including supported branches,
repetitions and go-to conditions. They are not limited to acyclic graphs. Maximum
steps/cycles/runtime, evaluation points, cancellation and recovery are explicit.
Each node requires only its selected capabilities; a missing model or remote worker
does not block an unrelated project. F13 calls the same typed operations as humans,
with scoped permissions, budgets and actual result/resource lineage.

## Jobs, workers and lifecycle extension

One host coordinator owns admission, queued/running/terminal outcomes, attempts,
progress and parent-child cancellation. Domain operations supply versioned specs
and checkpoint hooks. Trusted CPU work targets bounded local worker processes;
I/O uses bounded asynchronous operations. This is future execution scope beyond
the approved minimum P01 host, not an already available worker pool.

Specify publication fencing, operation-specific retry/idempotency and interrupted
recovery before activation. Seeds and aggregation order follow stable identities,
not completion timing. Windows worker imports stay inert; initialization is explicit.
Do not persist arbitrary executable objects or promise arbitrary process-state
resurrection or exactly-once external effects.

F10 extends that coordinator with compatible authenticated remote-worker placement,
leases and result transfer. It does not introduce a second scheduler or require
Java messaging-framework replicas. Local backtests and neural training do not
require remote compute. SQX Java-node wire interoperability is a separate requirement.

Custom/user code and AI Python analysis need enforceable filesystem/network,
CPU/memory/time/output limits and isolation. A normal worker process is not a
security sandbox. Remote access/deployment and irreversible external operations
retain their own explicit authority and qualification.

## Storage and resource custody

Every schema/table/partition/preset collection has one semantic feature owner.
Transactions, migrations, retention and compatibility belong to a ratified host
persistence capability. No plugin ad-hoc SQL or raw database handles. Shared database
paths and schemas cannot be activated or repurposed by inference.

Published resources carry IDs, schema versions, immutable revisions, SHA-256,
media types and producer provenance. Consumers read retained bytes without importing
producer code. Uninstall preserves resources and unrelated user data. Tests use
isolated temporary resources. Removal/cascade/restore verification runs in an
isolated candidate under a separately approved exact-path plan, never on shared data.

Retain P01 atomic preferences independently of later operational storage. V2 proposes
one host-owned SQLite control store for job/catalog/project/resource metadata,
plus immutable JSON and Arrow/Parquet artifacts for large data/ledgers/series.
DuckDB may serve analytical reads; it is not automatically a second operational
writer. These choices are proposals: no schema, database path, migration, retention
policy or active-store adoption is ratified by this document alignment.

Stage, validate and hash artifacts before publishing metadata references. A file
rename and database commit are not one atomic transaction; the owning plan must
qualify orphan/missing-file recovery, revision conflicts and interrupted publication.
Start with the records needed by the selected journey; expose narrow typed methods
rather than generic plugin SQL or an arbitrary query framework.

## Verification authority and current gaps

Every concrete Python module has the five-section constitutional docstring, typed
public signatures, descriptive FRs, emitted FR events and log assertions. Focused
pytest uses explicit paths and --no-cov; branch coverage is evidence, not parity.

P00 qualifies reference tooling using its dedicated branch-aware coverage config.
No Python application modules currently exist. Retained tooling/frontend checks are
in `scripts/ci_check.py`. Historical architecture/package/removal checkers are
absent and cannot be presented as current executable acceptance checks.
Future application source must restore >=80% branch-aware application coverage and
its feature-specific architecture/removal checks through approved plans.

MainApp/AppSettings/CpuInfo remain unavailable within the audited current static
boundary; SQLib/core packaging is unresolved. The owner-approved
DEC-HOST-P00-UNAVAILABLE-HOST-SOURCE permits target-owned universal host contracts
through approved feature plans. Settings precedence, CPU policy, lifecycle and
paths must be explicit target decisions rather than inferred SQX facts. This
exception covers no missing numerical, trading, AI or domain algorithm.
Donor-derived translation/parity claims still require supporting body semantics
and applicable independent observations; product activation remains unverified.
P00 closure establishes reference readiness and dispositions only. Application
registration and runtime qualification belong to owning feature/integration plans.

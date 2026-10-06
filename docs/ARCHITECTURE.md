# HaruQuantAI architecture

Status: ratified structural constraints at the reset-aware P00 baseline, 2026-10-06.
Historical source: Git commit `3ede688544b1c161984573cdc25e7a36b01d4a37`,
`docs/ARCHITECTURE.md`, SHA-256
`8fdf5bb3d15386333e9bace6ad99a7eb4c6987b4ea2fd95cf43d192cbd437bb3`.
Removed implementation and historical interface versions are not current contracts.

[PROJECT.md](PROJECT.md) owns scope; [AGENTS.md](../AGENTS.md) owns contributor
process; local owning READMEs own feature/FR/decision identities and status.
[Evidence procedure](dev/evidence/README.md) distinguishes observations and decisions.

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

Plugin path casing/singular/plural variants in historical documents and the roadmap
are proposals requiring individual ratification. P00 creates no plugin package.
Typed transport/document versions, discovery contracts and mounting schemes are
future decisions; provisional UI clients do not ratify those backend contracts.

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

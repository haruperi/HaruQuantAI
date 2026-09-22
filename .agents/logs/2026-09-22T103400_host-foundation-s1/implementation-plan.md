# Implementation Plan: Host Foundation — Kernel and Telemetry

> **Task ID:** `HOST-S1-001`
> **Iteration:** `1`
> **Branch:** `main`
> **Baseline Commit:** `7f2ec63fa6eb07e9c9a60b40afe3b1cc16772c2a`

Follow-up work on the same task appends a labelled iteration to this file.

---

### User Review Required

> [!IMPORTANT]
> The requested target contains nine host owner files, but the ratified project
> sequence requires a separately planned and approved implementation stage for
> each meaningful slice and explicitly says not to scaffold every future
> service. This iteration therefore implements the complete S1 dependency:
> kernel remediation plus real `host/bootstrap.py` and `host/telemetry.py`
> owners. It does not create empty `catalog.py`, `execution.py`, `jobs.py`,
> `workers.py`, `storage.py`, `artifacts.py`, or `gateway.py` placeholders.
>
> Approval accepts two deliberate breaking changes to the retained baseline:
> `FeatureSpec.optional` and feature-startup optional lookup are removed, and
> kernel-owned event/logging APIs are replaced by host-owned telemetry plus a
> minimal injected kernel diagnostic sink.

### Open Questions

> `NONE`. The architecture authorities decide the sequencing and ownership;
> provider/database/server choices remain deferred to their later stages.

---

## 1. Goal, Requirements & Usage Evidence

- **Problem and outcome:** Establish the first functioning `app/host/` slice.
  The kernel becomes a standard-library-only lifecycle mechanism with restricted
  declared dependency access, deterministic ordering, and correct rollback.
  Host composition and bounded, failure-isolated observation live in their
  ratified owner files.
- **Ratified requirements:** Implement S1 from `docs/PROJECT.md` and D1-D4 from
  `docs/ARCHITECTURE.md`: no `app/api`; one cohesive file per host owner;
  import-pure owner modules; required-edge canonical startup; no optional
  startup edges; staged publication; complete failed/cancelled-start rollback;
  reverse consumer-before-provider cleanup; host-owned event/logging behavior;
  observer failures do not fail publishers.
- **Spatial invariants:** Behavior is local to `telemetry.py`; the kernel remains
  product-neutral; telemetry is exposed by a typed `Capability[Telemetry]`;
  composition alone imports construction entry points; diagnostics and
  observation values are immutable and introspectable.
- **Usage evidence:** A deterministic offline example builds the host runtime,
  resolves `HOST_TELEMETRY`, subscribes two observers (one failing), emits one
  immutable event, proves the healthy observer still receives it, inspects the
  attributed delivery report, and exits with all subscriptions/resources closed.

## 2. Files Read (Audit Trail)

- [AGENTS.md](C:/Users/rharu/AppDev/HaruQuantAI/AGENTS.md) — workflow, staged
  approval, kernel purity, and no-placeholder constraints.
- [PROJECT.md](C:/Users/rharu/AppDev/HaruQuantAI/docs/PROJECT.md) — ratified S1-S6
  order, S1 exit evidence, and prohibition on scaffolding all future services.
- [ARCHITECTURE.md](C:/Users/rharu/AppDev/HaruQuantAI/docs/ARCHITECTURE.md) —
  owner-local topology, import matrix, kernel disposition, lifecycle rules, and
  planned host ownership.
- [feature_implementation_pipeline.md](C:/Users/rharu/AppDev/HaruQuantAI/docs/dev/feature_implementation_pipeline.md)
  and [domain_implementation_audit.md](C:/Users/rharu/AppDev/HaruQuantAI/docs/dev/domain_implementation_audit.md)
  — contract-import purity, lifecycle, effects, and verification obligations.
- [capability.py](C:/Users/rharu/AppDev/HaruQuantAI/app/kernel/capability.py),
  [feature.py](C:/Users/rharu/AppDev/HaruQuantAI/app/kernel/feature.py),
  [context.py](C:/Users/rharu/AppDev/HaruQuantAI/app/kernel/context.py), and
  [bootstrapper.py](C:/Users/rharu/AppDev/HaruQuantAI/app/kernel/bootstrapper.py)
  — retained APIs, ambient/optional access, optional ordering, diagnostics, and
  rollback behavior to remediate.
- [events.py](C:/Users/rharu/AppDev/HaruQuantAI/app/kernel/events.py) and
  [logging.py](C:/Users/rharu/AppDev/HaruQuantAI/app/kernel/logging.py) — concrete
  observation and logging behavior that violates the ratified kernel boundary.
- [kernel tests](C:/Users/rharu/AppDev/HaruQuantAI/tests/kernel) and
  [examples](C:/Users/rharu/AppDev/HaruQuantAI/tests/examples) — current public
  behavior and every affected consumer.
- [test_boundaries.py](C:/Users/rharu/AppDev/HaruQuantAI/tests/architecture/test_boundaries.py),
  [test_architecture_check.py](C:/Users/rharu/AppDev/HaruQuantAI/tests/architecture/test_architecture_check.py),
  and [architecture_check.py](C:/Users/rharu/AppDev/HaruQuantAI/scripts/architecture_check.py)
  — reset-only enforcement that must be replaced rather than removed.
- `C:/SQX_144_2953_win_20260601/internal/libs/SQPluginLib.jar`,
  `SQJobsLib.jar`, `SQTradingLib.jar`, and `SQDataLib.jar` — inspected class
  inventories and public signatures. SQX separates plugin loading, jobs, and
  trading execution into distinct compiled libraries. Its static singleton
  managers (`SQPluginManager`, `JobEngine`, `ProjectEngine`) are inspiration for
  responsibility separation only; they are incompatible with explicit scoped
  capabilities and will not be copied.
- [Extending_SQX.pdf](C:/SQX_144_2953_win_20260601/Extending_SQX.pdf) and the SQX
  snippet tree — confirm extensibility is presented above compiled host libraries,
  while concrete snippet families are not evidence for HaruQuantAI host APIs.
- Git state at audit: `main`, clean working tree, baseline commit above.
  `uv run python scripts/architecture_check.py` passed; `uv run pytest --no-cov
  tests/kernel tests/architecture -q` passed with `96 passed`.

## 3. Proposed Changes & Implementation Order

- `[MODIFY]` [capability.py](C:/Users/rharu/AppDev/HaruQuantAI/app/kernel/capability.py)
  — retain immutable `(name, major)` typed tokens and make identity validation
  and collision diagnostics explicit without product vocabulary.
- `[MODIFY]` [feature.py](C:/Users/rharu/AppDev/HaruQuantAI/app/kernel/feature.py)
  — reduce startup declarations to `provides` and mandatory `requires`; remove
  optional startup dependency semantics.
- `[MODIFY]` [context.py](C:/Users/rharu/AppDev/HaruQuantAI/app/kernel/context.py)
  — expose declared required resolution, staged provision, owned resources,
  managed tasks, cleanup, and closure only. Remove ambient capability inventory,
  optional lookup, and event subscription/publication.
- `[MODIFY]` [bootstrapper.py](C:/Users/rharu/AppDev/HaruQuantAI/app/kernel/bootstrapper.py)
  — validate the complete graph before effects, use canonical required-edge
  ordering, inject a minimal diagnostic sink, roll back failed/cancelled startup,
  preserve bindings through dependent cleanup, aggregate cleanup failures, and
  keep shutdown idempotent.
- `[DELETE]` [events.py](C:/Users/rharu/AppDev/HaruQuantAI/app/kernel/events.py)
  and `[DELETE]` [logging.py](C:/Users/rharu/AppDev/HaruQuantAI/app/kernel/logging.py)
  — move concrete observation ownership out of the kernel.
- `[MODIFY]` [kernel __init__.py](C:/Users/rharu/AppDev/HaruQuantAI/app/kernel/__init__.py)
  and [kernel README](C:/Users/rharu/AppDev/HaruQuantAI/app/kernel/README.md) —
  keep the initializer docstring-only and describe only retained kernel behavior.
- `[NEW]` [host __init__.py](C:/Users/rharu/AppDev/HaruQuantAI/app/host/__init__.py)
  — empty or docstring-only package initializer.
- `[NEW]` [telemetry.py](C:/Users/rharu/AppDev/HaruQuantAI/app/host/telemetry.py)
  — define immutable `TelemetryEvent`, delivery failure/report values,
  `Telemetry` protocol, `HOST_TELEMETRY`, private bounded in-process provider,
  and composition-only construction/lifecycle entry point in one file. Importing
  the module performs no I/O, configuration, registration, task creation, or
  provider construction. Subscriber exceptions are attributed in the report and
  do not interrupt other subscribers or escape `emit`.
- `[NEW]` [bootstrap.py](C:/Users/rharu/AppDev/HaruQuantAI/app/host/bootstrap.py)
  — sole application composition root for S1. It constructs the telemetry owner
  and returns a fresh kernel `Runtime`; construction does not start resources.
- `[MODIFY]` [architecture_check.py](C:/Users/rharu/AppDev/HaruQuantAI/scripts/architecture_check.py)
  — replace reset-only assumptions with S1 rules: exact allowed current roots,
  kernel file/purity rules, host initializer purity, forbidden superseded roots,
  no kernel imports of host/plugins/UI, and no reintroduction of kernel event or
  logging modules.
- `[MODIFY]` architecture and kernel tests listed in `ALLOWED_WRITE_PATHS` —
  replace reset assertions and obsolete event/logging expectations with contract
  import-purity, restricted-context, canonical-order, failed/cancelled-start,
  cleanup-order, cleanup-aggregation, and observer-isolation evidence.
- `[MODIFY/NEW/DELETE]` example files listed below — keep composition coverage
  aligned with required-only startup and replace the old logging example with
  deterministic host telemetry usage.
- `[MODIFY]` [PROJECT.md](C:/Users/rharu/AppDev/HaruQuantAI/docs/PROJECT.md),
  [ARCHITECTURE.md](C:/Users/rharu/AppDev/HaruQuantAI/docs/ARCHITECTURE.md), and
  [kernel README](C:/Users/rharu/AppDev/HaruQuantAI/app/kernel/README.md) — after
  passing evidence, state the exact S1 implementation status without claiming
  catalog, execution, durable infrastructure, or SQX parity.

### Sequential Implementation Order

1. Write failing focused tests for restricted scopes, graph ordering, rollback,
   cleanup, host contract import purity, and telemetry failure isolation.
2. Remediate the four retained kernel owners and delete kernel event/logging
   implementation.
3. Implement `host/telemetry.py`, then `host/bootstrap.py`, with no import effects.
4. Replace reset-only architecture enforcement and update deterministic examples.
5. Reconcile documentation only after the implementation evidence passes.
6. Run focused verification, deterministic usage evidence, architecture checks,
   full qualification, then create the walkthrough and stop at the commit gate.

The remaining host owners follow in later exact-path tasks:

1. S2: shared plugin metamodel plus `host/catalog.py`.
2. S3: the first cohesive quantitative slice plus `host/execution.py`.
3. S4: versioned UI transport plus `host/gateway.py`.
4. S5: `host/jobs.py`, `workers.py`, `storage.py`, and `artifacts.py` with selected
   persistence/process choices and recovery evidence.

## 4. Dependencies and Contracts

- `Capability[T]` remains the only kernel token. S1 adds `HOST_TELEMETRY` with
  capability major 1 in its owning host file.
- `Telemetry.emit(event) -> TelemetryDeliveryReport` is asynchronous. Events and
  reports use immutable bounded scalar/tuple fields; arbitrary mutable mappings
  and exception objects do not cross the contract.
- Subscription is explicit and returns an idempotent close handle owned by the
  subscribing scope. Provider shutdown prevents new emission, closes existing
  subscriptions, and is idempotent.
- The provider enforces fixed subscriber and field-count/length bounds. A full
  provider rejects new subscriptions with a typed telemetry error. Delivery uses
  a stable subscription snapshot; subscriber add/remove during delivery affects
  only subsequent events.
- Kernel diagnostics are immutable business-neutral records delivered to an
  injected synchronous sink. Sink failure is contained and cannot alter kernel
  lifecycle outcomes. The kernel does not import or know `Telemetry`.
- Host bootstrap is the only importer of the telemetry construction entry point.
  No plugin metamodel, concrete plugin, persistence, network, thread, or optional
  third-party dependency is introduced in S1.

## 5. Blockers, Risks, and Trade-offs

- Creating all nine target filenames now would contradict the ratified staged
  sequence and “not a scaffolding checklist” rule. Mitigation: deliver complete
  owners in dependency order; never use empty placeholders as progress evidence.
- Removing `FeatureSpec.optional`, `EventBus`, and custom kernel logging is a
  deliberate baseline API break. All repository consumers are in the allowed
  paths and will be migrated atomically in this task.
- Cancellation correctness is easy to weaken by catching only `Exception` or by
  closing prior scopes but not the currently starting scope. Tests will inject
  cancellation at startup and cleanup and assert every acquired resource closes.
- Observer diagnostics can recurse if delivery failures are emitted through the
  same failing observer path. The provider returns immutable attributed failures
  and uses a separate bounded diagnostic callback with a recursion guard.
- If focused or qualification evidence exposes a need for plugin types, a
  database/server dependency, or another host owner, implementation stops and a
  plan iteration seeks renewed approval rather than expanding this stage.
- Rollback trigger: restore source paths from baseline commit
  `7f2ec63fa6eb07e9c9a60b40afe3b1cc16772c2a` while preserving this task log; no
  history rewrite or destructive Git command is required.

## 6. Scope Boundaries (Inclusions & Exclusions)

- **In scope:** S1 kernel correction; real host bootstrap and telemetry owners;
  migrated tests/examples; S1 architecture enforcement; truthful documentation;
  walkthrough evidence.
- **Out of scope:** `catalog.py`, `execution.py`, `jobs.py`, `workers.py`,
  `storage.py`, `artifacts.py`, `gateway.py`; shared plugin metamodel; concrete
  plugins/workspaces; HTTP/WebSocket transport; databases; subprocess workers;
  durable jobs/artifacts; UI changes; external effects; SQX compatibility/parity;
  dependencies; commits, branches, merges, rebases, or pushes.

## 7. Verification Plan

### Focused tests

```powershell
uv run pytest --no-cov tests/kernel tests/host tests/architecture -v
```

### Usage evidence

```powershell
uv run python -m tests.examples.composition
uv run python -m tests.examples.telemetry_usage
```

### Architecture and qualification

```powershell
uv run python scripts/architecture_check.py
uv run ruff check app/kernel app/host tests/kernel tests/host tests/architecture tests/examples scripts/architecture_check.py
uv run ruff format --check app/kernel app/host tests/kernel tests/host tests/architecture tests/examples scripts/architecture_check.py
uv run mypy app/kernel app/host
uv run python scripts/ci_check.py
```

No UI command is required because S1 changes no schema, algebra, wire contract,
transport, renderer, or UI source.

### Manual verification

- Import `app.host.telemetry` and `app.host.bootstrap` in a fresh interpreter
  while patching resource/thread/task/environment access to fail; imports must pass.
- Inspect `git diff --check`, `git diff --stat`, and final `git status --short`.
- Confirm every changed path is in `ALLOWED_WRITE_PATHS` and the seven deferred
  host owners remain absent.

## 8. Rollback & Contingency

All source edits are new files or tracked-file modifications/deletions relative
to the recorded baseline. Restore only the allowed source/test/doc paths from the
baseline if the candidate cannot satisfy S1. Preserve the implementation plan and
walkthrough as evidence. Do not reset, clean, rewrite history, or touch unrelated
user work.

```text
ALLOWED_WRITE_PATHS:
- app/kernel/__init__.py
- app/kernel/README.md
- app/kernel/capability.py
- app/kernel/feature.py
- app/kernel/context.py
- app/kernel/bootstrapper.py
- app/kernel/events.py
- app/kernel/logging.py
- app/host/__init__.py
- app/host/bootstrap.py
- app/host/telemetry.py
- scripts/architecture_check.py
- tests/architecture/test_architecture_check.py
- tests/architecture/test_boundaries.py
- tests/kernel/test_context.py
- tests/kernel/test_events.py
- tests/kernel/test_logging.py
- tests/kernel/test_runtime.py
- tests/host/__init__.py
- tests/host/test_bootstrap.py
- tests/host/test_telemetry.py
- tests/examples/composition.py
- tests/examples/logging_usage.py
- tests/examples/telemetry_usage.py
- docs/PROJECT.md
- docs/ARCHITECTURE.md
- .agents/logs/2026-09-22T103400_host-foundation-s1/implementation-plan.md
- .agents/logs/2026-09-22T103400_host-foundation-s1/walkthrough.md
END_ALLOWED_WRITE_PATHS:
```

---

## Iteration 2 — CI usage-command reconciliation

Focused implementation and the full qualification run showed that
`scripts/ci_check.py` still invokes the removed
`tests.examples.logging_usage` module after all lint, typing, architecture, and
pytest checks pass. This is a non-architectural correction within the already
approved migration from kernel logging to host telemetry.

- `[MODIFY] scripts/ci_check.py` — replace only the obsolete logging usage command
  with `uv run python -m tests.examples.telemetry_usage`.
- Public contracts, dependencies, runtime behavior, destructive targets, and all
  other scope remain unchanged.

```text
ALLOWED_WRITE_PATHS_ITERATION_2_ADDENDUM:
- scripts/ci_check.py
END_ALLOWED_WRITE_PATHS_ITERATION_2_ADDENDUM:
```

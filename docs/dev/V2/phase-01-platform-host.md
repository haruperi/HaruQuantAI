# Phase 1 — Platform and web shell

**Feature group:** F01. **Tasks:** 10. **Status:** proposed; 0 complete.

[Checklist](implementation_checklist.md) · [V2 index](README.md) · [Delivery milestones](delivery-plan.md)

## Objective and boundary

Boot one Python host and browser shell with explicit startup and reverse-order shutdown. This phase owns the platform and web shell capability group. The ten host tasks replace library-oriented P01/P02 duplication.

**Dependencies:** Existing P00 reference readiness and ratified P01 contracts. Build minimum host first; durable jobs/resources/persistence follow when needed.

**Delivery:** M01, the F01 portions of M02, and M09. Phase numbers identify scope, not a requirement to finish every earlier feature before starting this one. Deliver the smallest connected operation first; pending matrix rows remain full-product obligations.

**Ownership:** proposed semantic owner `app/host`; workspace composition remains in `app/workspace/<workspace>`, and the host owns storage, jobs, resource custody and route mounting. No sibling business imports or plugin SQL. Package/module names below are proposed targets to audit and ratify per task, not newly registered contracts.

## Research and authority

Read [V1 P01](../V1/phase-01-host-foundation.md), [V1 P02](../V1/phase-02-host-services.md), [V1 P17](../V1/phase-17-product-distribution.md), the [legacy task map](legacy-task-map.csv), [scope coverage](coverage-map.md), [current inventory](../evidence/p00-inventory.json) and [evidence procedure](../evidence/README.md). The V1 files retain exact archive/resource locators, fingerprints, consumed symbols and source limitations; use the relevant rows instead of recrawling unrelated archives. The sole donor is `SQX_145_REFERENCE_ROOT` (145-dev1). Hash and inspect the selected consumed bodies/resources before deciding defaults or numerical behavior. Signatures and UI labels alone do not establish semantics.

The root [AGENTS.md](../../../AGENTS.md), [architecture](../../ARCHITECTURE.md) and approved P01 contracts remain authoritative. For each implementation slice: audit current source, create an exact-path canonical plan, get owner approval, implement, verify and write a walkthrough. Missing source behavior requires explicit disposition; no copied proprietary implementation or invented SQX parity.

## Scope and acceptance matrix

Each row is a mandatory acceptance set inside its numbered tasks, not another feature/plugin backlog. Mark a task complete only when all of its promised rows are qualified.

| Acceptance set | Tasks | Retained behavior |
| --- | --- | --- |
| Bootstrap/shell | 1.1 | Home/About/help, routes/navigation, readiness, light/dark skin, language/zoom, explicit shutdown and clean install |
| Logs/diagnostics/settings | 1.2-1.4 | All consumed configuration defaults, FR logs/redaction, DebugConsole cursor/display behavior, measured hardware/process health |
| Discovery/transport/jobs | 1.5-1.7 | Typed package attachment/removal, /api/v1, session-bounded events, one coordinator and explicit interrupted recovery |
| Resources/storage/authority | 1.8-1.10 | Safe archive/file/cache/network access, narrow host transactions, retained revisions and separately scoped external effects |
| JVM-only mechanics | 1.1-1.10 | Use the host-foundation disposition table and legacy CSV; qualify consumed behavior, not Java annotations/reflection/runtime/utility frameworks |

## Shared proposed changes and verification rules

- Audit/Create the owning domain README when absent; update it after each accepted capability. Reconcile actual FEAT/FR/DEC identities there; F01 and task numbers are planning labels.
- Compose domain capabilities in the selected workspace with typed attachment; public requests use the host transport. Reuse earlier qualified schemas/services instead of copying modules to satisfy a file list.
- Every proposed Python module follows the canonical module template, explicitly typed APIs and observable FR logs. Test success, failure, cancellation and redaction; never use silent exceptions.
- Proposed tests below are future commands, **not reported passes**. They use isolated stores/resources. Run scoped tests while editing, then required quality/coverage gates for the actual approved runtime scope.
- Retained UI files to audit/connect: [ui/app/workspace/Home/HomeScreen.tsx](../../../ui/app/workspace/Home/HomeScreen.tsx), [ui/app/workspace/DebugConsole/DebugConsoleWorkspace.tsx](../../../ui/app/workspace/DebugConsole/DebugConsoleWorkspace.tsx). Preserve existing layouts and meaningful controls.
- After actual UI changes run `npm --prefix ui run typecheck`, `npm --prefix ui run test` and `npm --prefix ui run build`. Fixture-only UI regressions do not replace real backend/UI acceptance.

# 1.1 App/host bootstrap and browser shell

## 1. Objective

Boot one Python host and browser shell with explicit startup and reverse-order shutdown.

## 2. Research and donors

P01 bootstrap consumers and P17 shell/theme resources; reconcile the approved P01 launch contract.

Use the phase sources and legacy CSV to recover exact donor entries/fingerprints. Write independent input/output expectations before translation. Record missing bodies, target decisions and compatibility limits in source-bound evidence.

## 3. File Changes

- **Create:** `app/host/bootstrap.py` — owned implementation merging bootstrap, lifespan stages, reverse-order shutdown, readiness assessment, and browser shell FastAPI app.
- **Create:** `tests/unit/v2/phase_01/test_bootstrap.py` — independent contract, failure and FR-log cases for this task.
- **Audit/compose:** `app/host/README.md` and applicable browser shell endpoints. Host services remain the only job/resource/persistence authority.

## 4. Step-by-Step Task Breakdown

- [x] **Step 1:** Define lifespan stages, readiness states and ownership of acquired services.
- [x] **Step 2:** Compose FastAPI configuration, log setup, paths, services, discovery and routes without import-time work.
- [x] **Step 3:** Undo acquired stages when startup fails; make repeated shutdown safe.
- [x] **Step 4:** Connect Home/About/help, navigation, skin, language and zoom to actual readiness/preferences; qualify clean install/start/stop.
- [x] **Acceptance:** implement the independent tests below; retain evidence, owned lifecycle and observable errors in the connected consumer before checking this task.

## 5. Verification and Testing

**Future automated command:** `uv run pytest tests/unit/v2/phase_01/test_bootstrap.py --no-cov`.

**Independent cases:** Inject failure at each startup stage; assert release order, optional capability absence, safe repeated stop and no Java/SQX installation dependency.

**Connected acceptance:** use an isolated real host and temporary resources through the declared workspace/consumer. Verify genuine job/resource IDs, visible unavailable/denied/failure states, cancellation and retained lineage after reconnect/reload. Capture expected versus actual results; do not report fixture outputs as runtime behavior.

# 1.2 Centralized logging and DebugConsole

## 1. Objective

Use one explicit structured Python logging pipeline for host, domains and workers.

## 2. Research and donors

P01 logging/telemetry consumers and DebugConsole; use the approved display/cursor contract.

Use the phase sources and legacy CSV to recover exact donor entries/fingerprints. Write independent input/output expectations before translation. Record missing bodies, target decisions and compatibility limits in source-bound evidence.

## 3. File Changes

- **Create:** `app/host/logging.py` — owned implementation merging centralized logging, redaction filtering, rotating ZIP storage, bounded in-memory ring buffer, and DebugConsole projections.
- **Create:** `tests/unit/v2/phase_01/test_logging.py` — independent contract, failure and FR-log cases for this task.
- **Audit/compose:** `app/host/README.md` and applicable workspace/client. Host services remain the only job/resource/persistence authority.

## 4. Step-by-Step Task Breakdown

- [x] **Step 1:** Specify event fields, FR identity, request/job/resource correlation and bounded sinks.
- [x] **Step 2:** Configure stdlib loggers once; forward worker records with context and redact before every sink.
- [x] **Step 3:** Implement rotating storage and bounded DebugConsole snapshots/events using existing cursor limits.
- [x] **Step 4:** Expose sink overflow/failure without recursive logging; close subscriptions and sinks on stop.
- [x] **Acceptance:** implement the independent tests below; retain evidence, owned lifecycle and observable errors in the connected consumer before checking this task.

## 5. Verification and Testing

**Future automated command:** `uv run pytest tests/unit/v2/phase_01/test_logging.py --no-cov`.

**Independent cases:** Verify normal, failure and cancellation FR events; secret/path redaction across all sinks, rotation, slow subscribers, filtering and reconnect gap handling.

**Connected acceptance:** use an isolated real host and temporary resources through the declared workspace/consumer. Verify genuine job/resource IDs, visible unavailable/denied/failure states, cancellation and retained lineage after reconnect/reload. Capture expected versus actual results; do not report fixture outputs as runtime behavior.

# 1.3 System and hardware diagnostics

## 1. Objective

Report measured system capacity and owned-process health without changing the machine.

## 2. Research and donors

P01 OSHI/JNA/WMI/process consumers; retain externally visible units and CPU-limit decisions.

Use the phase sources and legacy CSV to recover exact donor entries/fingerprints. Write independent input/output expectations before translation. Record missing bodies, target decisions and compatibility limits in source-bound evidence.

## 3. File Changes

- **Create:** `app/host/diagnostics.py` — owned implementation merging CPU, memory, disk, process probes, worker allocation, thread affinity, GPU qualification, and computational benchmarks.
- **Create:** `tests/unit/v2/phase_01/test_diagnostics.py` — independent contract, failure and FR-log cases for this task.
- **Audit/compose:** `app/host/README.md` and applicable workspace/client. Host services remain the only job/resource/persistence authority.

## 4. Step-by-Step Task Breakdown

- [x] **Step 1:** Define CPU, memory, disk, runtime and process observations with explicit unavailable states.
- [x] **Step 2:** Adapt psutil/OS calls with bounded probe time and safe projections.
- [x] **Step 3:** Derive worker limits from qualified capacity and validated settings, retaining source units.
- [x] **Step 4:** Run any benchmark as a bounded diagnostic job with environment/workload metadata; activate affinity/GPU flags only for qualified consumers.
- [x] **Acceptance:** implement the independent tests below; retain evidence, owned lifecycle and observable errors in the connected consumer before checking this task.

## 5. Verification and Testing

**Future automated command:** `uv run pytest tests/unit/v2/phase_01/test_diagnostics.py --no-cov`.

**Independent cases:** Test failed probes, invalid CPU count, timeout, zero versus unavailable, redaction and benchmark cancellation; never synthesize a score.

**Connected acceptance:** use an isolated real host and temporary resources through the declared workspace/consumer. Verify genuine job/resource IDs, visible unavailable/denied/failure states, cancellation and retained lineage after reconnect/reload. Capture expected versus actual results; do not report fixture outputs as runtime behavior.

# 1.4 Settings and configurations

## 1. Objective

Validate configuration and persist revision-checked user preferences once.

## 2. Research and donors

P01 AppSettings callers and all consumed Settings resources; preserve approved P01 precedence and preference contracts.

Use the phase sources and legacy CSV to recover exact donor entries/fingerprints. Write independent input/output expectations before translation. Record missing bodies, target decisions and compatibility limits in source-bound evidence.

## 3. File Changes

- **Create (proposed):** `app/host/settings.py` — owned implementation of the operations below; reuse an earlier qualified module when appropriate.
- **Create (proposed):** `app/host/preferences.py` — owned implementation of the operations below; reuse an earlier qualified module when appropriate.
- **Create (proposed):** `tests/unit/v2/phase_01/test_settings.py` — independent contract, failure and FR-log cases for this task.
- **Audit/compose:** the owning README and applicable workspace/client listed above; choose exact existing files in the task plan. Host services remain the only job/resource/persistence authority.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Separate bind/data-root/credential inputs, user preferences and domain experiment settings.
- [ ] **Step 2:** Define defaults, precedence, finite-value/type validation and schema compatibility.
- [ ] **Step 3:** Implement the approved atomic preferences.json write/reload/conflict behavior in a new marked root.
- [ ] **Step 4:** Connect existing settings controls to their owner schemas; keep credentials out of saved projections and service activation separate from preference edits.
- [ ] **Acceptance:** implement the independent tests below; retain evidence, owned lifecycle and observable errors in the connected consumer before checking this task.

## 5. Verification and Testing

**Future automated command:** `uv run pytest tests/unit/v2/phase_01/test_settings.py --no-cov`.

**Independent cases:** Test unknown keys, invalid/nonfinite values, revision conflict, interrupted atomic write, reload, secret redaction and no implicit remote/trading activation.

**Connected acceptance:** use an isolated real host and temporary resources through the declared workspace/consumer. Verify genuine job/resource IDs, visible unavailable/denied/failure states, cancellation and retained lineage after reconnect/reload. Capture expected versus actual results; do not report fixture outputs as runtime behavior.

# 1.5 Workspace and plugin discovery

## 1. Objective

Discover known workspace/plugin contributions through small manifests and typed attachment.

## 2. Research and donors

P02 JSPF/registration consumers and actual workspace/plugin READMEs; no new central business catalog.

Use the phase sources and legacy CSV to recover exact donor entries/fingerprints. Write independent input/output expectations before translation. Record missing bodies, target decisions and compatibility limits in source-bound evidence.

## 3. File Changes

- **Create (proposed):** `app/host/discovery.py` — owned implementation of the operations below; reuse an earlier qualified module when appropriate.
- **Create (proposed):** `app/host/attachments.py` — owned implementation of the operations below; reuse an earlier qualified module when appropriate.
- **Create (proposed):** `tests/unit/v2/phase_01/test_discovery.py` — independent contract, failure and FR-log cases for this task.
- **Audit/compose:** the owning README and applicable workspace/client listed above; choose exact existing files in the task plan. Host services remain the only job/resource/persistence authority.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Define identity/version, contained entrypoint, dependency and slot metadata owned by each package.
- [ ] **Step 2:** Validate the full attachment before executing its explicit factory with injected host capabilities.
- [ ] **Step 3:** Publish available/unavailable/incompatible states to the browser and keep zero-plugin workspaces usable.
- [ ] **Step 4:** Implement controlled disable/restart/removal with owned route/job/subscription cleanup; add reload only where required.
- [ ] **Acceptance:** implement the independent tests below; retain evidence, owned lifecycle and observable errors in the connected consumer before checking this task.

## 5. Verification and Testing

**Future automated command:** `uv run pytest tests/unit/v2/phase_01/test_discovery.py --no-cov`.

**Independent cases:** Reject duplicate IDs, malformed manifests, escaped entrypoints and incompatible slots; verify removal releases ownership and preserves retained artifacts and unrelated workspaces.

**Connected acceptance:** use an isolated real host and temporary resources through the declared workspace/consumer. Verify genuine job/resource IDs, visible unavailable/denied/failure states, cancellation and retained lineage after reconnect/reload. Capture expected versus actual results; do not report fixture outputs as runtime behavior.

# 1.6 HTTP and event transport

## 1. Objective

Connect clients through one versioned HTTP envelope and bounded authenticated event stream.

## 2. Research and donors

P02 server/reactive and servlet consumers; inspect provisional UI payloads before ratifying routes.

Use the phase sources and legacy CSV to recover exact donor entries/fingerprints. Write independent input/output expectations before translation. Record missing bodies, target decisions and compatibility limits in source-bound evidence.

## 3. File Changes

- **Create (proposed):** `app/host/transport.py` — owned implementation of the operations below; reuse an earlier qualified module when appropriate.
- **Create (proposed):** `app/host/events.py` — owned implementation of the operations below; reuse an earlier qualified module when appropriate.
- **Create (proposed):** `tests/unit/v2/phase_01/test_transport.py` — independent contract, failure and FR-log cases for this task.
- **Audit/compose:** the owning README and applicable workspace/client listed above; choose exact existing files in the task plan. Host services remain the only job/resource/persistence authority.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Preserve /api/v1, request IDs, approved payload/deadline bounds and stable error envelopes.
- [ ] **Step 2:** Keep domain schemas/routes locally owned behind the existing UI transport factory.
- [ ] **Step 3:** Use HTTP commands/queries plus bounded SSE where sufficient; specify event order, retention and snapshots.
- [ ] **Step 4:** Recover reconnects from authoritative snapshots; expire sessions and release slow-consumer resources.
- [ ] **Acceptance:** implement the independent tests below; retain evidence, owned lifecycle and observable errors in the connected consumer before checking this task.

## 5. Verification and Testing

**Future automated command:** `uv run pytest tests/unit/v2/phase_01/test_transport.py --no-cov`.

**Independent cases:** Test malformed/version-mismatched payloads, error envelopes without success data, missing capability, gaps, expiry, reconnect and backpressure against an isolated real host.

**Connected acceptance:** use an isolated real host and temporary resources through the declared workspace/consumer. Verify genuine job/resource IDs, visible unavailable/denied/failure states, cancellation and retained lineage after reconnect/reload. Capture expected versus actual results; do not report fixture outputs as runtime behavior.

# 1.7 Local jobs and cancellation

## 1. Objective

Run every long operation through one bounded local coordinator.

## 2. Research and donors

P02 task/job consumers; future F10 extends this coordinator rather than creating another scheduler.

Use the phase sources and legacy CSV to recover exact donor entries/fingerprints. Write independent input/output expectations before translation. Record missing bodies, target decisions and compatibility limits in source-bound evidence.

## 3. File Changes

- **Create (proposed):** `app/host/jobs.py` — owned implementation of the operations below; reuse an earlier qualified module when appropriate.
- **Create (proposed):** `app/host/workers.py` — owned implementation of the operations below; reuse an earlier qualified module when appropriate.
- **Create (proposed):** `tests/unit/v2/phase_01/test_jobs.py` — independent contract, failure and FR-log cases for this task.
- **Audit/compose:** the owning README and applicable workspace/client listed above; choose exact existing files in the task plan. Host services remain the only job/resource/persistence authority.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Specify queued/running/succeeded/failed/cancelled and cancellation-request/interrupted states with attempt IDs.
- [ ] **Step 2:** Apply admission, queue, retry and duplicate-submission policies by operation.
- [ ] **Step 3:** Use bounded processes for trusted CPU work and async tasks for I/O; domains provide validated specs and checkpoint hooks.
- [ ] **Step 4:** Own child jobs/progress/publication; record durable history when required and reconcile interrupted jobs after restart.
- [ ] **Acceptance:** implement the independent tests below; retain evidence, owned lifecycle and observable errors in the connected consumer before checking this task.

## 5. Verification and Testing

**Future automated command:** `uv run pytest tests/unit/v2/phase_01/test_jobs.py --no-cov`.

**Independent cases:** Test overflow, cooperative/hard cancellation, shutdown, worker loss, child counts, duplicate requests, late output and explicit interrupted recovery without false success.

**Connected acceptance:** use an isolated real host and temporary resources through the declared workspace/consumer. Verify genuine job/resource IDs, visible unavailable/denied/failure states, cancellation and retained lineage after reconnect/reload. Capture expected versus actual results; do not report fixture outputs as runtime behavior.

# 1.8 Resource services and safe artifact access

## 1. Objective

Publish immutable owned artifacts and provide bounded file/cache/archive access.

## 2. Research and donors

P02 archive/cache/network consumers; provider semantics and native formats stay with F02/F03/F12.

Use the phase sources and legacy CSV to recover exact donor entries/fingerprints. Write independent input/output expectations before translation. Record missing bodies, target decisions and compatibility limits in source-bound evidence.

## 3. File Changes

- **Create (proposed):** `app/host/resources.py` — owned implementation of the operations below; reuse an earlier qualified module when appropriate.
- **Create (proposed):** `app/host/archives.py` — owned implementation of the operations below; reuse an earlier qualified module when appropriate.
- **Create (proposed):** `tests/unit/v2/phase_01/test_resources.py` — independent contract, failure and FR-log cases for this task.
- **Audit/compose:** the owning README and applicable workspace/client listed above; choose exact existing files in the task plan. Host services remain the only job/resource/persistence authority.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Define resource IDs, checksums, media/size metadata, scopes and staging-to-publication transitions.
- [ ] **Step 2:** Enforce contained paths including resolved junctions; reject escaped entries and expansion limits.
- [ ] **Step 3:** Use Python file/hash/archive primitives and bounded httpx acquisition policy; qualify each needed compression/encryption variant.
- [ ] **Step 4:** Clean temporary work after failure/cancel; preserve retained revisions after producer removal and key caches by version with measured bounds.
- [ ] **Acceptance:** implement the independent tests below; retain evidence, owned lifecycle and observable errors in the connected consumer before checking this task.

## 5. Verification and Testing

**Future automated command:** `uv run pytest tests/unit/v2/phase_01/test_resources.py --no-cov`.

**Independent cases:** Test traversal, absolute/archive/junction escapes, corrupt checksums, oversized expansion, missing files, encrypted/unsupported variants, cache invalidation and orphan staging cleanup.

**Connected acceptance:** use an isolated real host and temporary resources through the declared workspace/consumer. Verify genuine job/resource IDs, visible unavailable/denied/failure states, cancellation and retained lineage after reconnect/reload. Capture expected versus actual results; do not report fixture outputs as runtime behavior.

# 1.9 Host-owned persistence and restart recovery

## 1. Objective

Provide host-owned transactions, compatibility checks and retained-data recovery.

## 2. Research and donors

P02 H2/JDBC consumers and ratified host storage law; document any donor import as a format adapter.

Use the phase sources and legacy CSV to recover exact donor entries/fingerprints. Write independent input/output expectations before translation. Record missing bodies, target decisions and compatibility limits in source-bound evidence.

## 3. File Changes

- **Create (proposed):** `app/host/persistence.py` — owned implementation of the operations below; reuse an earlier qualified module when appropriate.
- **Create (proposed):** `app/host/repositories.py` — owned implementation of the operations below; reuse an earlier qualified module when appropriate.
- **Create (proposed):** `tests/unit/v2/phase_01/test_persistence.py` — independent contract, failure and FR-log cases for this task.
- **Audit/compose:** the owning README and applicable workspace/client listed above; choose exact existing files in the task plan. Host services remain the only job/resource/persistence authority.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Preserve approved atomic preferences; obtain separate ratification for operational schema/root before activation.
- [ ] **Step 2:** Define narrow typed repositories for domain-owned schemas, revisions, leases and retention.
- [ ] **Step 3:** Use SQLite control records plus immutable artifacts only as the current V2 proposal, with transactional publication/recovery policy.
- [ ] **Step 4:** Reconcile interrupted writes, missing/orphan artifacts and concurrent updates; forbid plugin SQL/raw handles or automatic adoption of active stores.
- [ ] **Acceptance:** implement the independent tests below; retain evidence, owned lifecycle and observable errors in the connected consumer before checking this task.

## 5. Verification and Testing

**Future automated command:** `uv run pytest tests/unit/v2/phase_01/test_persistence.py --no-cov`.

**Independent cases:** Use temporary stores for rollback, concurrent revision conflict, interrupted publication, restart and removal preservation; reject incompatible schema and unapproved migration.

**Connected acceptance:** use an isolated real host and temporary resources through the declared workspace/consumer. Verify genuine job/resource IDs, visible unavailable/denied/failure states, cancellation and retained lineage after reconnect/reload. Capture expected versus actual results; do not report fixture outputs as runtime behavior.

# 1.10 Security, sessions and distribution qualification

## 1. Objective

Enforce session/permission boundaries and qualify secure local distribution.

## 2. Research and donors

Approved P01 session contract and P17 distribution; ordinary trusted workers are not a custom-code sandbox.

Use the phase sources and legacy CSV to recover exact donor entries/fingerprints. Write independent input/output expectations before translation. Record missing bodies, target decisions and compatibility limits in source-bound evidence.

## 3. File Changes

- **Create (proposed):** `app/host/security.py` — owned implementation of the operations below; reuse an earlier qualified module when appropriate.
- **Create (proposed):** `app/host/sessions.py` — owned implementation of the operations below; reuse an earlier qualified module when appropriate.
- **Create (proposed):** `tests/unit/v2/phase_01/test_security.py` — independent contract, failure and FR-log cases for this task.
- **Audit/compose:** the owning README and applicable workspace/client listed above; choose exact existing files in the task plan. Host services remain the only job/resource/persistence authority.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Implement approved loopback origin/token/session validation and invalidate sessions on restart.
- [ ] **Step 2:** Authorize each domain/resource/tool action against exact scope; keep secrets in approved operational inputs.
- [ ] **Step 3:** Keep live orders, destructive tasks, external scripts, mail and paid tools behind distinct authority; qualify user-code isolation separately.
- [ ] **Step 4:** Run clean-install and dependency-removal checks; propose authenticated TLS remote deployment separately when needed.
- [ ] **Acceptance:** implement the independent tests below; retain evidence, owned lifecycle and observable errors in the connected consumer before checking this task.

## 5. Verification and Testing

**Future automated command:** `uv run pytest tests/unit/v2/phase_01/test_security.py --no-cov`.

**Independent cases:** Reject expired/foreign sessions, origin failures, unauthorized paths/actions and leaked credentials; verify clean local installation and domain removal without retained-data loss.

**Connected acceptance:** use an isolated real host and temporary resources through the declared workspace/consumer. Verify genuine job/resource IDs, visible unavailable/denied/failure states, cancellation and retained lineage after reconnect/reload. Capture expected versus actual results; do not report fixture outputs as runtime behavior.

## Phase completion gate

- [ ] All 10 numbered tasks and all specialist matrix rows are accepted under their own approved plans.
- [ ] Independent behavioral/numerical/format evidence supports each claimed compatibility scope; missing donor/provider/platform behavior remains explicitly unresolved.
- [ ] Actual backend/UI journey, failures, cancellation, restart/reconnect and scoped removal preserve retained outputs and unrelated work.
- [ ] Owning READMEs, task evidence and the master checklist agree; required Ruff/mypy/tests/coverage and applicable UI gates pass for implemented source.

A milestone subset is usable progress. Whole-product release also requires the [shared release gate](implementation_checklist.md#shared-release-gate). No checkbox is completed by publishing this plan.

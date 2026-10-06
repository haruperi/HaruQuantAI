# P18 — Whole-app integration and independently verified release

- **Source:** `HARUQUANTAI_ROOT/docs/dev/sqx-full-application-roadmap.md`; SHA-256 `9abec0aa2faf6bd78b39e80c2dcfb7dfcae62ae412d9b56a77904de6a7b5a54c`.
- **Dependencies:** P00–P17; P00 prerequisites are in the P01 file.
- **Scope:** eight qualification tasks; no new primary JAR allocations.
- **State:** proposed execution checklists; claims require recorded observations and independent review.
- **File labels:** Create means proposed new output; Modify means verified existing file.
- **Execution:** task plan/approval first; isolated stores; no Git or live external mutations without separate authority.

# 18.1 Complete archive/class/FR traceability

## 1. Objective

- **Goal:** Close every accepted JAR, class, function and resource disposition.
- **Context / Problem Solved:** The roadmap contains representative seeds; complete consumed behavior still needs an explicit disposition.

## 2. Research and donors

- **Donors/code:** All 261 archive fingerprints, 17 resource contributions, owning domain READMEs and restored ledger/schema.
- **Ownership:** existing phase feature/FR owners; qualification does not replace domain status or invent SQX facts.
- **Gap:** zero unresolved IDs/unclassified accepted items; missing references fail; expected outcomes remain unverified until recorded.

## 3. File Changes

- **Create:** `tests/reference/qualification/inventory.py`
  - Implement this qualification's semantic and failure checks.
- **Create:** `tests/reference/qualification/traceability.py`
  - Implement this qualification's semantic and failure checks.
- **Create:** `docs/dev/sqx-parity-release-matrix.md`
  - Record source-bound qualification and unresolved outcomes.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Audit the candidate, ratify this qualification scope and approve exact write paths.
- [ ] **Step 2:** Re-enumerate archives/classes/resources and detect additions, replacements and removed donor inputs.
- [ ] **Step 3:** Reconcile all FEAT/FR/decision IDs with owning READMEs; classify reused, adapted, runtime-only and unverified items.
- [ ] **Step 4:** Validate atomic ledger claims, schema, source references, record links, clean-room flags and review/commit metadata.
- [ ] **Step 5:** Reject missing dispositions or dangling IDs; keep contradictions and supersession links visible.

## 5. Verification & Testing

- **Automated Tests:** `uv run python tests/reference/qualification/traceability.py`; zero unresolved IDs/unclassified accepted items; missing references fail.
- **Manual / Browser Verification:** Review the per-feature disposition matrix and unverified/excluded capability list with the owner.

# 18.2 Independent numerical and format qualification

## 1. Objective

- **Goal:** Verify approved behavioral equivalence against reproducible donor observations.
- **Context / Problem Solved:** Translated functions and passing unit tests alone do not establish SQX parity.

## 2. Research and donors

- **Donors/code:** P03–P16 fixture datasets, strategy archives, indicator vectors, simulator traces, optimizer/WF/MC/portfolio/model outputs.
- **Ownership:** existing phase feature/FR owners; qualification does not replace domain status or invent SQX facts.
- **Gap:** accepted traces/formats match under explicit tolerances; injected mismatches fail; expected outcomes remain unverified until recorded.

## 3. File Changes

- **Create:** `tests/reference/qualification/test_differential.py`
  - Implement this qualification's semantic and failure checks.
- **Create:** `tests/reference/qualification/test_format_roundtrips.py`
  - Implement this qualification's semantic and failure checks.
- **Create:** `docs/dev/sqx-numerical-qualification.md`
  - Record source-bound qualification and unresolved outcomes.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Audit the candidate, ratify this qualification scope and approve exact write paths.
- [ ] **Step 2:** Ratify donor/build versions, fixture hashes, numeric units, tolerances and comparison rules.
- [ ] **Step 3:** Run donor cases independently; record exact inputs/outputs, execution timestamps and inspected artifact locations.
- [ ] **Step 4:** Replay indicator/simulation/search/robustness/portfolio/model comparisons; reconcile event order and formulas.
- [ ] **Step 5:** Round-trip native formats and generated targets; preserve unknown fields and qualify supported toolchains.
- [ ] **Step 6:** Record mismatches as unresolved evidence; rerun independently before claiming a passing capability.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/reference/qualification/test_differential.py tests/reference/qualification/test_format_roundtrips.py --no-cov`; accepted traces/formats match under explicit tolerances; injected mismatches fail.
- **Manual / Browser Verification:** Inspect representative same-bar fills, WF boundaries, MC seeds and saved/exported strategies against source observations.

# 18.3 Whole application frontend/backend journeys

## 1. Objective

- **Goal:** Run every promised workspace workflow against the real host.
- **Context / Problem Solved:** Existing screens and local mock results do not demonstrate working application services.

## 2. Research and donors

- **Donors/code:** P01–P17 frontend clients, domain routes, host discovery/catalog and accepted workflow matrix.
- **Ownership:** existing phase feature/FR owners; qualification does not replace domain status or invent SQX facts.
- **Gap:** all accepted journeys use real domain outputs and reload/restart correctly; expected outcomes remain unverified until recorded.

## 3. File Changes

- **Create:** `tests/integration/qualification/test_application_journeys.py`
  - Implement this qualification's semantic and failure checks.
- **Create:** `ui/tests/e2e/sqx-application-journeys.spec.ts`
  - Implement this qualification's semantic and failure checks.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Audit the candidate, ratify this qualification scope and approve exact write paths.
- [ ] **Step 2:** Launch a fresh isolated host/store; verify login, readiness and capability-based navigation.
- [ ] **Step 3:** Run import → author → simulate → Results/export; reconcile IDs, counts, trades and equity.
- [ ] **Step 4:** Run Builder → Optimizer/WF → Retester → Portfolio → custom-project workflows with real jobs.
- [ ] **Step 5:** Run grid/neural/terminal-sandbox/business/MCP/help/theme workflows for each accepted capability.
- [ ] **Step 6:** Reload/reconnect/restart each owned resource; verify unsupported states and eliminate production fixture execution.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/integration/qualification/test_application_journeys.py --no-cov`; all accepted journeys use real domain outputs and reload/restart correctly.
- **Manual / Browser Verification:** Run `npm --prefix ui run test:ui -- tests/e2e/sqx-application-journeys.spec.ts`; review loading/empty/error/cancelled/ready states.

# 18.4 Failure, recovery and authority qualification

## 1. Objective

- **Goal:** Prove bounded failures and fail-closed external/destructive authority.
- **Context / Problem Solved:** Cross-domain errors and irreversible actions must retain explicit lifecycle and owner authority.

## 2. Research and donors

- **Donors/code:** Host sessions/jobs/resources; provider, task, compute, extension, MCP and connection contracts.
- **Ownership:** existing phase feature/FR owners; qualification does not replace domain status or invent SQX facts.
- **Gap:** bounded failures; no unauthorized mutation; redacted correlated diagnostics; expected outcomes remain unverified until recorded.

## 3. File Changes

- **Create:** `tests/integration/qualification/test_failure_recovery.py`
  - Implement this qualification's semantic and failure checks.
- **Create:** `tests/integration/qualification/test_authority.py`
  - Implement this qualification's semantic and failure checks.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Audit the candidate, ratify this qualification scope and approve exact write paths.
- [ ] **Step 2:** Inject session expiry, schema mismatch, bad provider input, timeout, queue overflow and worker loss.
- [ ] **Step 3:** Check retry/rate/cancellation bounds, duplicate requests, transaction rollback and resource release.
- [ ] **Step 4:** Deny live trading, file/databank deletion, external scripts/notifications and tool mutations without their distinct authority.
- [ ] **Step 5:** Inspect all FR logs/events for observable errors and secret/personal-data redaction; verify no silent failures.
- [ ] **Step 6:** Verify dependent controls disable precisely and restart/reconnect never report unfinished writes as saved.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/integration/qualification/test_failure_recovery.py tests/integration/qualification/test_authority.py --no-cov`; bounded failures; no unauthorized mutation; redacted correlated diagnostics.
- **Manual / Browser Verification:** Disconnect a worker/provider and expire the session; inspect UI recovery and verify every blocked side effect remains unapplied.

# 18.5 Capability removal, restart and retained data

## 1. Objective

- **Goal:** Prove plugin/workspace removal and restart preserve unaffected resources.
- **Context / Problem Solved:** Host owns persistence and lifecycle; shared live worktree databases require isolated qualification.

## 2. Research and donors

- **Donors/code:** Discovery/unmount, host transactions/retention, resource handles and dependency declarations.
- **Ownership:** existing phase feature/FR owners; qualification does not replace domain status or invent SQX facts.
- **Gap:** no leaked ownership; unaffected data preserved; isolated recovery is repeatable; expected outcomes remain unverified until recorded.

## 3. File Changes

- **Create:** `tests/integration/qualification/test_removal_matrix.py`
  - Implement this qualification's semantic and failure checks.
- **Create:** `tests/integration/qualification/test_retention.py`
  - Implement this qualification's semantic and failure checks.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Audit the candidate, ratify this qualification scope and approve exact write paths.
- [ ] **Step 2:** Build the full accepted capability dependency/removal matrix; cover idle, active-job and failed-start states.
- [ ] **Step 3:** Unmount/remove/reinstall each contribution; verify routes/events/handles/jobs are released.
- [ ] **Step 4:** Use temporary stores to test restart durability, rollback and retention; compare unaffected-resource fingerprints.
- [ ] **Step 5:** Verify no plugin performs ad-hoc SQL and no live database schema/restore runs during qualification.
- [ ] **Step 6:** Record recovery for missing capabilities, orphaned resource references and incompatible retained versions.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/integration/qualification/test_removal_matrix.py tests/integration/qualification/test_retention.py --no-cov`; no leaked ownership; unaffected data preserved; isolated recovery is repeatable.
- **Manual / Browser Verification:** Remove a test capability while a fixture job runs; restart; inspect disabled dependents and preserved unrelated resources.

# 18.6 Resource limits, concurrency and repeatability

## 1. Objective

- **Goal:** Qualify explicit resource/performance budgets for the accepted cohort.
- **Context / Problem Solved:** Long-running searches, downloads and grids need measured bounded resource behavior.

## 2. Research and donors

- **Donors/code:** P02 cache/jobs/events, P04 streaming, P09–P15 search/grid/training and recorded reference workloads.
- **Ownership:** existing phase feature/FR owners; qualification does not replace domain status or invent SQX facts.
- **Gap:** ratified limits hold; injected overflow fails visibly; completed-job counts reconcile; expected outcomes remain unverified until recorded.

## 3. File Changes

- **Create:** `tests/integration/qualification/test_resource_limits.py`
  - Implement this qualification's semantic and failure checks.
- **Create:** `docs/dev/sqx-performance-qualification.md`
  - Record source-bound qualification and unresolved outcomes.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Audit the candidate, ratify this qualification scope and approve exact write paths.
- [ ] **Step 2:** Ratify dataset/workload sizes, concurrency, memory/CPU/time budgets and measurement protocol.
- [ ] **Step 3:** Measure cancellation latency, bounded queue/cache/event behavior and steady-state resource usage.
- [ ] **Step 4:** Compare local/grid job results and seeded runs; detect duplicate ownership and nondeterministic ordering.
- [ ] **Step 5:** Measure frontend responsiveness with long jobs and large results without masking failed work.
- [ ] **Step 6:** Record environment-neutral workload metadata, timestamps and measured limits; preserve failures.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/integration/qualification/test_resource_limits.py --no-cov`; ratified limits hold; injected overflow fails visibly; completed-job counts reconcile.
- **Manual / Browser Verification:** Run the bounded reference workloads; inspect progress, cancellation, resource recovery and chart/table responsiveness.

# 18.7 Application tooling and clean distribution

## 1. Objective

- **Goal:** Qualify retained application code and a fresh distributable runtime.
- **Context / Problem Solved:** scripts/ci_check.py currently checks tooling/UI only because backend app/tests were removed.

## 2. Research and donors

- **Donors/code:** pyproject.toml, scripts/ci_check.py, ui/package.json, package/runtime manifests and module template.
- **Ownership:** existing phase feature/FR owners; qualification does not replace domain status or invent SQX facts.
- **Gap:** fresh distribution boots/runs approved journeys; retained code and UI checks pass; expected outcomes remain unverified until recorded.

## 3. File Changes

- **Modify:** `scripts/ci_check.py`
  - Extend approved application qualification; preserve unrelated edits.
- **Modify:** `pyproject.toml`
  - Extend approved application qualification; preserve unrelated edits.
- **Create:** `tests/integration/qualification/test_distribution.py`
  - Implement this qualification's semantic and failure checks.
- **Create:** `docs/dev/sqx-distribution-qualification.md`
  - Record source-bound qualification and unresolved outcomes.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Audit the candidate, ratify this qualification scope and approve exact write paths.
- [ ] **Step 2:** Extend the CI qualification through an approved plan to cover retained app/tests and typed backend contracts.
- [ ] **Step 3:** Run focused suites during fixes; run `uv run pytest --cov=app --cov-branch --cov-report=term-missing` once the candidate stabilizes.
- [ ] **Step 4:** Require ≥80% branch-aware application coverage, canonical module docstrings, Ruff and strict public typing.
- [ ] **Step 5:** Run `uv run ruff check app tests scripts`, `uv run ruff format --check app tests scripts` and `uv run mypy --explicit-package-bases app tests scripts`.
- [ ] **Step 6:** Run `npm --prefix ui run typecheck`, `npm --prefix ui run test`, `npm --prefix ui run build`, then `uv run python scripts/ci_check.py`.
- [ ] **Step 7:** Launch a clean packaged runtime with no donor installation dependency; verify unavailable optional integrations explicitly.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/integration/qualification/test_distribution.py --no-cov`; fresh distribution boots/runs approved journeys; retained code and UI checks pass.
- **Manual / Browser Verification:** Install/launch the candidate in an isolated environment; check startup, resource paths, preferences and shutdown.

# 18.8 Evidence review and owner release gate

## 1. Objective

- **Goal:** Deliver a source-bound qualification walkthrough and bounded parity statement.
- **Context / Problem Solved:** A functional/parity claim requires independent evidence and final owner review.

## 2. Research and donors

- **Donors/code:** All phase walkthroughs, donor comparison artifacts, release matrix, current source commit and review records.
- **Ownership:** existing phase feature/FR owners; qualification does not replace domain status or invent SQX facts.
- **Gap:** all accepted rows have verified artifacts and independent review; unverified rows remain open; expected outcomes remain unverified until recorded.

## 3. File Changes

- **Create:** `docs/dev/sqx-release-walkthrough.md`
  - Record source-bound qualification and unresolved outcomes.
- **Create:** `docs/dev/sqx-release-open-gaps.md`
  - Record source-bound qualification and unresolved outcomes.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Audit the candidate, ratify this qualification scope and approve exact write paths.
- [ ] **Step 2:** Review all accepted capabilities against actual timestamped test/browser/donor observations.
- [ ] **Step 3:** Resolve accepted-cohort contradictions; keep exclusions and unavailable integrations explicit.
- [ ] **Step 4:** Record source/lockfile/artifact hashes, exact commands/results, git status and proposed commit message.
- [ ] **Step 5:** Create the canonical walkthrough; identify only independently verified capability-specific parity.
- [ ] **Step 6:** Request owner review and distinct commit/publication authority; do not mark full functionality while accepted gaps remain.

## 5. Verification & Testing

- **Automated Tests:** Review matrix and artifact-link validation; all accepted rows have verified artifacts and independent review; unverified rows remain open.
- **Manual / Browser Verification:** Owner reviews walkthrough, residual gaps, capability-specific parity statements and the exact release candidate.

## Phase completion gate

- [ ] Every accepted feature/FR has a resolved owner, disposition and passing observation.
- [ ] Independent donor comparisons, full removal/retention tests and UI journeys pass.
- [ ] Retained code, coverage, types, lint and distribution checks pass on the recorded candidate.
- [ ] Release walkthrough retains unavailable/unverified gaps and receives owner review.
- [ ] Owner separately authorizes commits/publication and any irreversible external action.

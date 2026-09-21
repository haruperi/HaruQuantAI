# Implementation Plan: Backend Reset and Repository Cleanup

> **Task ID:** `TASK-BACKEND-RESET-CLEANUP`
> **Iteration:** `1`
> **Branch:** `main`
> **Baseline Commit:** `64b978e9196cc48209740359fc4c44375c6219a2`

Follow-up work on the same task appends a clearly labelled iteration to this
file. Do not create a second plan for the same task run.

---

### User Review Required

> [!IMPORTANT]
> This is an intentionally destructive reset. Approval authorizes deletion of
> the current contracts, services, registry, Python composition root, backend
> tests/examples/system tests, broker live-check, and source-bound acceptance
> manifests. Git history and `.agents/logs/` are retained as the recovery and
> historical record.
>
> The resulting application source tree will contain only `app/__init__.py`,
> `app/kernel/`, and `app/ui/`. No replacement backend or new spatial plugin
> architecture is implemented in this task.
>
> A Git commit is not included in execution approval. After verification and
> walkthrough delivery, the owner retains the separate commit authorization
> gate required by `AGENTS.md`.

### Open Questions

> [!NOTE]
> - NONE. The owner explicitly selected Git history as the rollback mechanism
>   and requested the current backend and corresponding tests be removed before
>   planning the replacement architecture.

---

## 1. Goal, Requirements & Usage Evidence

### Problem Statement & Goal

The repository currently contains a contracts/services/registry backend built
for the superseded domain architecture. Keeping those files while designing the
Spatial Composability backend would preserve conflicting authorities, dead
entry points, misleading acceptance evidence, and tests for code that is no
longer intended to exist.

This task creates a truthful reset baseline by removing the superseded backend
and every repository-owned artifact that claims or requires its presence. The
kernel and UI implementations are retained unchanged except for documentation
and repository integration updates needed to make the reset coherent.

### Ratified Requirements

1. Delete `app/contracts/`, `app/services/`, and `app/registry.py`.
2. Delete all Python tests, examples, and system workflows whose subject is the
   deleted backend.
3. Delete `app/main.py`, its console-script declaration, and its tests because
   it imports `app.registry` and composes only the deleted backend.
4. Delete the backend-only broker live-check and current acceptance manifests.
5. Update all surviving contributor policy, architecture/product documents,
   package metadata, lock data, CI, architecture enforcement, and READMEs so
   none claims that the deleted backend exists.
6. Preserve `app/kernel/`, `tests/kernel/`, `app/ui/`, UI tests, generic kernel
   examples, secret-detection tests, and `.agents/logs/` history.
7. Do not implement the replacement plugin API, host backend, catalog, algebra,
   or schema-driven UI in this cleanup task.

### Usage Evidence

This is a repository reset rather than a backend feature. Evidence is structural:

- importing and exercising the retained kernel through
  `tests/examples/composition.py` and `tests/examples/logging_usage.py`;
- building, type-checking, and testing the retained UI;
- proving through search and architecture tests that no active file references
  `app.contracts`, `app.services`, or `app.registry`;
- proving the application tree contains only the retained kernel and UI roots.

---

## 2. Files Read (Audit Trail)

- [AGENTS.md](C:/Users/rharu/AppDev/HaruQuantAI/AGENTS.md) — verified mandatory plan, approval, verification, walkthrough, and commit gates; identified obsolete contracts/services rules.
- [implementation-plan.md](C:/Users/rharu/AppDev/HaruQuantAI/docs/templates/implementation-plan.md) — verified the required eight-section plan format.
- [pyproject.toml](C:/Users/rharu/AppDev/HaruQuantAI/pyproject.toml) — identified the `app.main` console script, backend runtime dependencies, old profile metadata, and test/tool scopes.
- [ci_check.py](C:/Users/rharu/AppDev/HaruQuantAI/scripts/ci_check.py) — identified calls to the gateway example and deleted application entry point.
- [architecture_check.py](C:/Users/rharu/AppDev/HaruQuantAI/scripts/architecture_check.py) — identified rules dedicated to the old contracts/services/registry layout.
- [app/main.py](C:/Users/rharu/AppDev/HaruQuantAI/app/main.py) — verified it imports `app.registry` and is not viable after the requested deletion.
- [bootstrapper.py](C:/Users/rharu/AppDev/HaruQuantAI/app/kernel/bootstrapper.py) — verified the retained kernel runtime remains independently testable.
- [test_runtime.py](C:/Users/rharu/AppDev/HaruQuantAI/tests/kernel/test_runtime.py) — identified one registry-specific test to remove while retaining kernel coverage.
- [test_boundaries.py](C:/Users/rharu/AppDev/HaruQuantAI/tests/architecture/test_boundaries.py) — verified retained package/kernel boundary coverage.
- [test_architecture_check.py](C:/Users/rharu/AppDev/HaruQuantAI/tests/architecture/test_architecture_check.py) — verified current checker tests and the place for reset-boundary assertions.
- [composition.py](C:/Users/rharu/AppDev/HaruQuantAI/tests/examples/composition.py) — verified retained kernel-only usage evidence.
- [logging_usage.py](C:/Users/rharu/AppDev/HaruQuantAI/tests/examples/logging_usage.py) — verified retained logging usage evidence.
- [README.md](C:/Users/rharu/AppDev/HaruQuantAI/README.md) — identified obsolete tree, startup, registry, contracts, and services guidance.
- [kernel README](C:/Users/rharu/AppDev/HaruQuantAI/app/kernel/README.md) — identified obsolete concrete registry ownership references.
- [UI README](C:/Users/rharu/AppDev/HaruQuantAI/app/ui/README.md) — identified nonexistent UI contracts/persistence claims and outdated source paths.
- [PROJECT.md](C:/Users/rharu/AppDev/HaruQuantAI/docs/PROJECT.md) — identified current feature/domain completion claims that become false after reset.
- [ARCHITECTURE.md](C:/Users/rharu/AppDev/HaruQuantAI/docs/ARCHITECTURE.md) — identified the superseded contracts/services/registry target architecture.
- [feature_implementation_pipeline.md](C:/Users/rharu/AppDev/HaruQuantAI/docs/dev/feature_implementation_pipeline.md) — verified the procedure is inseparable from the deleted layout.
- [domain_implementation_audit.md](C:/Users/rharu/AppDev/HaruQuantAI/docs/dev/domain_implementation_audit.md) — verified the audit matrix is inseparable from the deleted layout.
- `app/contracts/`, `app/services/`, `tests/contracts/`, `tests/services/`, `tests/system/`, and `docs/dev/evidence/` — inventoried every tracked removal target and searched all repository references.

---

## 3. Proposed Changes & Implementation Order

### Superseded Backend

- `[DELETE]` [app/contracts](C:/Users/rharu/AppDev/HaruQuantAI/app/contracts) — remove all six central contract files.
- `[DELETE]` [app/services](C:/Users/rharu/AppDev/HaruQuantAI/app/services) — remove all 78 service, persistence, gateway, broker, data, workspace, and placeholder domain files.
- `[DELETE]` [app/registry.py](C:/Users/rharu/AppDev/HaruQuantAI/app/registry.py) — remove explicit registration for the deleted service model.
- `[DELETE]` [app/main.py](C:/Users/rharu/AppDev/HaruQuantAI/app/main.py) — remove the composition root that depends on the deleted registry.

### Corresponding Backend Tests and Usage Evidence

- `[DELETE]` [tests/contracts](C:/Users/rharu/AppDev/HaruQuantAI/tests/contracts) — remove contract tests for deleted modules.
- `[DELETE]` [tests/services](C:/Users/rharu/AppDev/HaruQuantAI/tests/services) — remove all service and persistence tests.
- `[DELETE]` [tests/system](C:/Users/rharu/AppDev/HaruQuantAI/tests/system) — remove integration workflows whose complete subject graph is deleted.
- `[DELETE]` [tests/test_main.py](C:/Users/rharu/AppDev/HaruQuantAI/tests/test_main.py) — remove tests for the deleted composition root.
- `[DELETE]` backend examples `tests/examples/01_workspace.py` through `05_gateway.py`.
- `[MODIFY]` [tests/kernel/test_runtime.py](C:/Users/rharu/AppDev/HaruQuantAI/tests/kernel/test_runtime.py) — remove only the registry profile test; retain runtime behavior tests.
- `[PRESERVE]` kernel, architecture, script, UI, composition-example, and logging-example tests.

### Backend-Only Operations and Evidence

- `[DELETE]` [scripts/brokers_live_check.py](C:/Users/rharu/AppDev/HaruQuantAI/scripts/brokers_live_check.py) — remove the live check importing deleted broker contracts/services.
- `[DELETE]` [docs/dev/evidence/features](C:/Users/rharu/AppDev/HaruQuantAI/docs/dev/evidence/features) — remove 43 current-state acceptance manifests for deleted implementations.
- `[DELETE]` [docs/dev/evidence/reimplementation.json](C:/Users/rharu/AppDev/HaruQuantAI/docs/dev/evidence/reimplementation.json) — remove the current feature index; preserve its generic schema for later redesign.
- `[PRESERVE]` `.agents/logs/` as historical, Git-linked implementation records.

### Repository Authority and Documentation

- `[REWRITE]` [README.md](C:/Users/rharu/AppDev/HaruQuantAI/README.md) — document the kernel/UI reset baseline, supported commands, and absent backend.
- `[MODIFY]` [AGENTS.md](C:/Users/rharu/AppDev/HaruQuantAI/AGENTS.md) — retain workflow/safety/quality rules while removing the obsolete contracts/services/persistence authorities; prohibit backend implementation until replacement architecture is ratified.
- `[REWRITE]` [docs/PROJECT.md](C:/Users/rharu/AppDev/HaruQuantAI/docs/PROJECT.md) — record the truthful transitional product state without claiming backend completion.
- `[REWRITE]` [docs/ARCHITECTURE.md](C:/Users/rharu/AppDev/HaruQuantAI/docs/ARCHITECTURE.md) — record only the retained kernel/UI boundary and defer replacement architecture to the next approved task.
- `[DELETE]` [feature_implementation_pipeline.md](C:/Users/rharu/AppDev/HaruQuantAI/docs/dev/feature_implementation_pipeline.md) and [domain_implementation_audit.md](C:/Users/rharu/AppDev/HaruQuantAI/docs/dev/domain_implementation_audit.md) — remove authorities that exclusively prescribe the deleted architecture.
- `[DELETE]` obsolete domain-oriented [PROJECT template](C:/Users/rharu/AppDev/HaruQuantAI/docs/templates/PROJECT.md) and [domain README template](C:/Users/rharu/AppDev/HaruQuantAI/docs/templates/README.md); replacements belong to the architecture-foundation task.
- `[MODIFY]` [implementation-plan template](C:/Users/rharu/AppDev/HaruQuantAI/docs/templates/implementation-plan.md) — replace obsolete example paths with neutral host/plugin examples while retaining the workflow contract.
- `[MODIFY]` [kernel README](C:/Users/rharu/AppDev/HaruQuantAI/app/kernel/README.md) — describe its actual retained implementation without claiming an active registry/backend.
- `[REWRITE]` [UI README](C:/Users/rharu/AppDev/HaruQuantAI/app/ui/README.md) — describe the retained frontend honestly as a mock-backed prototype pending the new gateway/catalog boundary.

### Tooling, Package Metadata, and Enforcement

- `[MODIFY]` [pyproject.toml](C:/Users/rharu/AppDev/HaruQuantAI/pyproject.toml) — remove the deleted console entry point, unused backend runtime dependencies, obsolete per-file/profile configuration, and retain kernel development/test tooling.
- `[REGENERATE]` [uv.lock](C:/Users/rharu/AppDev/HaruQuantAI/uv.lock) — reconcile the lockfile with the reduced Python dependency graph using `uv lock`.
- `[MODIFY]` [scripts/ci_check.py](C:/Users/rharu/AppDev/HaruQuantAI/scripts/ci_check.py) — stop invoking deleted gateway/application modules; retain lint, format, typing, architecture, coverage, and kernel usage checks.
- `[MODIFY]` [scripts/architecture_check.py](C:/Users/rharu/AppDev/HaruQuantAI/scripts/architecture_check.py) — remove dead layout-specific rules and add reset-baseline checks forbidding reintroduction of the deleted roots before the replacement architecture is ratified.
- `[MODIFY]` [tests/architecture/test_architecture_check.py](C:/Users/rharu/AppDev/HaruQuantAI/tests/architecture/test_architecture_check.py) and [test_boundaries.py](C:/Users/rharu/AppDev/HaruQuantAI/tests/architecture/test_boundaries.py) — reconcile tests with the reduced checker and assert the allowed application roots.

### Sequential Implementation Order

1. Delete the backend implementation roots and their Python composition entry point.
2. Delete corresponding tests, examples, system workflows, live-check, and current-state acceptance evidence.
3. Reconcile Python package metadata and regenerate `uv.lock`.
4. Reconcile architecture enforcement, kernel tests, and CI commands.
5. Rewrite surviving repository authority and README files to describe the reset baseline.
6. Run structural reference scans, focused retained tests, UI qualification, and the full Python quality pipeline.
7. Write the task walkthrough with deletion inventory, verification outputs, `git status`, and a proposed commit message; stop for owner commit authorization.

---

## 4. Dependencies and Contracts

- No product/backend public contract remains after this cleanup.
- `app.kernel.capability.Capability[T]` remains the only retained typed capability primitive.
- `app.kernel.feature`, `context`, `bootstrapper`, `events`, and `logging` remain exactly as implemented; their redesign is explicitly deferred.
- The UI remains self-contained under its npm dependency graph and continues using its current mock data/services.
- No persistence boundary is introduced or retained. Database schemas, live integrations, and gateway dependencies are removed with the backend.
- Python runtime third-party dependencies used only by the deleted backend are removed from project metadata and lock data.

---

## 5. Blockers, Risks, and Trade-offs

- **Destructive scope:** 84 production contract/service files, 62 direct contract/service tests, additional system/example/entry-point files, and 43 acceptance manifests will be removed.
  - **Mitigation:** exact tracked targets are audited; Git commit `64b978e9196cc48209740359fc4c44375c6219a2` is the immutable baseline; no databases or user data are touched.
- **Temporary lack of Python application entry point:** after reset there will be no runnable backend command.
  - **Mitigation:** this is intentional and documented. The retained UI remains runnable with npm, and the next architecture task owns the new host entry point.
- **Reduced product verification:** backend tests and acceptance evidence disappear because their implementations disappear.
  - **Mitigation:** CI is narrowed truthfully to the retained kernel/tooling; UI verification is run independently. Coverage is never padded with tests for deleted code.
- **Authority gap:** deleting the old feature pipeline leaves no backend implementation pipeline until the next architecture task.
  - **Mitigation:** `AGENTS.md`, `PROJECT.md`, and `ARCHITECTURE.md` explicitly mark backend implementation as paused pending ratification; workflow and safety rules remain active.
- **UI still contains mock/domain behavior:** this cleanup does not yet make the UI schema-driven.
  - **Mitigation:** the UI README states this honestly; UI refactoring is part of the subsequent architecture work, not silently mixed into deletion.
- **Commit is intentionally deferred:** execution approval does not authorize a commit.
  - **Mitigation:** produce a complete walkthrough and request the repository-required owner commit gate.

---

## 6. Scope Boundaries (Inclusions & Exclusions)

### In Scope

- Exact deletion and reconciliation described in Section 3.
- Dependency/lock cleanup caused solely by removing the backend.
- Truthful transitional documentation and repository enforcement.
- Retained kernel and UI qualification.

### Out of Scope / Non-Goals

- No changes to kernel behavior or public APIs.
- No changes to UI source behavior, layouts, stores, mocks, or visual design.
- No `app/plugins/`, `app/host/`, engine, catalog, algebra AST, gateway, persistence, broker, exporter, or simulator implementation.
- No final Spatial Composability architecture or new implementation pipeline.
- No database deletion, migration, or external-system mutation.
- No Git commit, branch creation, merge, push, or history rewrite.
- No deletion of `.agents/logs/` or unrelated documentation history.

---

## 7. Verification Plan

### Structural and Reference Verification

```powershell
@('app/contracts','app/services','app/registry.py','app/main.py') |
  ForEach-Object { if (Test-Path -LiteralPath $_) { throw "Unexpected path: $_" } }

$unexpected = rg -n "app\.(contracts|services|registry)|app/contracts|app/services|app/registry" app tests scripts pyproject.toml README.md AGENTS.md docs
if ($LASTEXITCODE -eq 0) { throw "Stale backend references found:`n$unexpected" }
if ($LASTEXITCODE -ne 1) { throw "Reference scan failed with exit code $LASTEXITCODE" }
```

### Automated Tests

```powershell
uv run pytest --no-cov tests/kernel tests/architecture tests/scripts -v
```

### Usage Evidence Run

```powershell
uv run python -m tests.examples.composition
uv run python -m tests.examples.logging_usage
```

### Retained UI Qualification

```powershell
npm --prefix app/ui run typecheck
npm --prefix app/ui run test
npm --prefix app/ui run build
```

Playwright E2E is not required for this source-neutral cleanup because UI source
behavior is unchanged; run it only if dependency reconciliation unexpectedly
touches the UI package.

### Quality Pipeline

```powershell
uv run python scripts/ci_check.py
```

### Manual Verification

- Confirm `git diff --stat` contains only the approved deletion/reconciliation scope.
- Confirm `git status --short` shows no generated caches, databases, logs, or unrelated files.
- Confirm the retained `app/` tree is `__init__.py`, `kernel/`, and `ui/` only.

---

## 8. Rollback & Contingency

Before a commit, rollback is available through the baseline commit and targeted
Git restoration. No destructive database or external operation is part of this
task. If verification fails, fix only an approved surviving reference or stop
and report the necessary scope expansion.

After a future owner-authorized cleanup commit, recovery remains available by
reverting that commit; history rewrite is neither required nor permitted.

```text
ALLOWED_WRITE_PATHS:
- app/contracts/
- app/services/
- app/registry.py
- app/main.py
- app/kernel/README.md
- app/ui/README.md
- tests/contracts/
- tests/services/
- tests/system/
- tests/test_main.py
- tests/examples/01_workspace.py
- tests/examples/02_persistence.py
- tests/examples/03_brokers.py
- tests/examples/04_data.py
- tests/examples/05_gateway.py
- tests/kernel/test_runtime.py
- tests/architecture/test_architecture_check.py
- tests/architecture/test_boundaries.py
- scripts/brokers_live_check.py
- scripts/ci_check.py
- scripts/architecture_check.py
- docs/dev/evidence/features/
- docs/dev/evidence/reimplementation.json
- docs/dev/feature_implementation_pipeline.md
- docs/dev/domain_implementation_audit.md
- docs/templates/PROJECT.md
- docs/templates/README.md
- docs/templates/implementation-plan.md
- docs/PROJECT.md
- docs/ARCHITECTURE.md
- README.md
- AGENTS.md
- pyproject.toml
- uv.lock
- .agents/logs/2026-09-21T223436_backend-reset-cleanup/implementation-plan.md
- .agents/logs/2026-09-21T223436_backend-reset-cleanup/walkthrough.md
END_ALLOWED_WRITE_PATHS:
```

---

## Iteration 2 — Approved Standard-Template Preservation

> **Owner Approval:** `APPROVED: EXECUTE` received 2026-09-21.

The owner clarified that the repository must retain standard, reusable authoring
and implementation guidance. The following Iteration 1 deletion actions are
therefore superseded:

- `docs/templates/PROJECT.md` is **rewritten**, not deleted, as the canonical
  system/project specification template for the Spatial Composability model.
- `docs/templates/README.md` is **rewritten**, not deleted, as the canonical
  one-file plugin documentation template.
- `docs/dev/feature_implementation_pipeline.md` is **rewritten**, not deleted,
  as the plugin implementation pipeline.
- `docs/dev/domain_implementation_audit.md` is **rewritten**, not deleted, as
  the companion plugin implementation audit, preserving the build/audit pair.

These replacements must encode the five Spatial Composability laws, one-file
plugin ownership, typed capability slots, algebraic composition, schema-driven
self-description, discovery without central registration edits, required test
and usage evidence, and the existing plan/approval/walkthrough workflow.

All other approved cleanup boundaries, verification requirements, rollback
rules, and allowed write paths remain unchanged.

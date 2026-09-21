# Walkthrough: Backend Reset for Spatial Plugin Rebuild

> Task ID: `2026-09-21T223436_backend-reset-cleanup`
> Status: Awaiting owner commit authorization

## 1. Summary of Changes Made

The legacy backend has been removed, leaving `app/kernel/`, `app/ui/`, and the
package initializer as the only application roots. The reset removes the old
contract/service split so the replacement architecture can be designed around
spatially cohesive plugins rather than inheriting incompatible boundaries.

### Removed backend and coupled evidence

- Deleted `app/contracts/`, `app/services/`, `app/registry.py`, and `app/main.py`.
- Deleted the corresponding contract, service, system-integration, entrypoint,
  and numbered backend example tests.
- Deleted the backend-only broker live-check script.
- Deleted acceptance manifests and reimplementation evidence tied to the
  removed backend.
- Removed the old application entrypoint and backend-only runtime dependencies
  from `pyproject.toml`; regenerated `uv.lock`.

### Preserved and hardened the reset boundary

- Updated `scripts/architecture_check.py` to enforce initializer purity,
  standard-library kernel purity, JSON-only data files, and the absence of the
  removed legacy roots.
- Updated retained architecture and kernel tests for the new application
  topology.
- Updated `scripts/ci_check.py` so qualification runs only retained examples
  and no longer invokes the deleted backend entrypoint.

### Replaced repository and plugin standards

- Rewrote `AGENTS.md`, `README.md`, `docs/PROJECT.md`, and
  `docs/ARCHITECTURE.md` to record the greenfield reset and the five spatial
  composability laws as repository truth.
- Replaced `docs/dev/feature_implementation_pipeline.md` with a plugin-oriented
  implementation pipeline covering locality, immutable typed capability
  tokens, discovery versus enablement, algebraic composition, schema-driven UI,
  lifecycle ownership, removal tests, examples, evidence, and qualification.
- Replaced `docs/dev/domain_implementation_audit.md` with the matching plugin
  audit while retaining its established path for contributor workflow
  compatibility.
- Replaced `docs/templates/PROJECT.md` with a spatially composable system/project
  specification template.
- Replaced `docs/templates/README.md` with a plugin-family README template that
  standardizes documentation without duplicating executable per-plugin schema.
- Updated `docs/templates/implementation-plan.md` for plugin-oriented planning.
- Updated the kernel and UI READMEs to distinguish current implementation truth
  from the intended future architecture.

The resulting diff contains 220 changed paths: 1,195 insertions and 53,883
deletions. All changes are unstaged and uncommitted pending owner review.

## 2. Verification Results

### Automated Test Suite

- `uv run pytest --no-cov tests/kernel tests/architecture tests/scripts -v`
  - Result: retained focused suites pass (98 tests in the final qualification).
- `uv run python scripts/architecture_check.py`
  - Result: passed.
- `uv run ruff check ...` and `uv run ruff format --check ...` on the changed
  Python/configuration scope
  - Result: passed.
- `uv run mypy scripts/architecture_check.py`
  - Result: passed.
- `npm --prefix app/ui run typecheck`
  - Result: passed.
- `npm --prefix app/ui run test`
  - Result: 42 test files and 199 tests passed.
- `npm --prefix app/ui run build`
  - Result: production build passed (1,933 modules transformed).

### Usage Evidence Run

- `uv run python -m tests.examples.composition`
  - Result: passed; both full composition and dynamic subset scenarios ran.
- `uv run python -m tests.examples.logging_usage`
  - Result: passed; deterministic temporary logging scenario ran.

### Full Pipeline Check

- `uv run python scripts/ci_check.py`
  - Result: passed.
  - Ruff: passed; 26 files already formatted.
  - Mypy: success across 23 source files.
  - Architecture check: passed.
  - Pytest: 98 passed.
  - Coverage: 98.30%, above the required 80% floor.
  - Retained usage examples: passed.
- `git diff --check`
  - Result: passed with no whitespace errors.
- Stale-reference scan across `app`, `tests`, `scripts`, project metadata, and
  authoritative documentation
  - Result: no references to the deleted legacy imports, roots, entrypoint,
    examples, or broker live-check remain.
- Filesystem topology check
  - Result: `app/` contains only `kernel/`, `ui/`, and `__init__.py`; every
    approved legacy target is absent.

## 3. Deviations & Residuals

### Approved deviation

The original cleanup wording could have left obsolete standards documents
deleted or minimally edited. Per the owner's follow-up and approval, the
standards were instead preserved by rewriting `docs/templates/PROJECT.md`,
`docs/templates/README.md`, and
`docs/dev/feature_implementation_pipeline.md`. The companion plugin audit was
also rewritten so the pipeline and its review criteria cannot contradict each
other.

### Intentional residuals

- The UI remains a mock-backed prototype and still contains domain-shaped
  frontend data. Migrating it to schema-derived views is part of the next
  architecture plan, not this destructive reset.
- The kernel remains intact. Capability identity, host ownership, event
  isolation, plugin lifecycle, catalog/discovery, and execution-tree contracts
  require explicit design decisions before implementation.
- There is intentionally no runnable Python backend entrypoint at this stage.
- UI tests emit non-failing local-storage availability warnings in the test
  environment.
- The production UI build emits a non-failing Vite warning for a JavaScript
  chunk larger than 500 kB.
- Playwright end-to-end tests were not run because no UI implementation source
  changed; type checking, component tests, and a production build qualified the
  retained UI.

### Working tree and commit proposal

- Working tree: intentionally dirty with only this task's unstaged changes.
- Git history has not been rewritten and no commit has been created.
- Proposed commit message:
  `chore(architecture): reset backend for spatial plugin rebuild`

### Recommended next planning sequence

1. Harden the kernel primitives and define immutable typed capability identity.
2. Specify the plugin spatial-unit contract, schema vocabulary, lifecycle, and
   host-owned discovery/enablement model.
3. Specify the shared algebraic execution tree used by the UI, builder,
   simulator, and exporters.
4. Replace mock/domain-shaped UI boundaries with schema- and tree-driven ports.
5. Implement the thinnest vertical plugin slice only after those decisions are
   approved.

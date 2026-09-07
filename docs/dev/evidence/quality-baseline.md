# Phase 0 reproducible quality baseline

**Baseline source HEAD:** `34edd2b3c8164b59ed9b2b2964c0d79f7c2d399a`

**Measurement host:** `SAMSUNG-960QHA-U7-256V-16GB-NVME`

**Runtime evidence:** `reference-hardware.json`

**Measured workloads:** `performance-baseline.json`

The historic CI reference `34051983427` / job `101537114162` at `a3c81df`
stopped after 36 Ruff findings. That observation is historical input, not the
current result. The commands below were executed against the approved Quick-Fix
working tree on 2026-09-07.

## Current quality gates

| Check | Exact command | Observed result |
| --- | --- | --- |
| Combined repository gate | `uv run --frozen python scripts/ci_check.py` | PASS — all configured steps completed |
| Phase 0 ratification | `uv run --frozen python scripts/validate_phase0.py` | PASS — 205 tasks, 8 preparations, 476 required edges, 233 operation gates |
| Ruff lint | `uv run --frozen ruff check .` | PASS — zero findings |
| Ruff format | `uv run --frozen ruff format --check .` | PASS — all checked Python files formatted |
| Strict typing | `uv run --frozen mypy` | PASS — 855 source files |
| Architecture | `uv run --frozen python scripts/architecture_check.py` | PASS — zero violations |
| Generated contracts | `uv run --frozen python scripts/generate_contracts.py --check` | PASS — 33 artifacts current |
| Feature docs | `uv run --frozen python scripts/validate_feature_docs.py` | PASS — 41 feature READMEs |
| Workflow tests | `uv run --frozen pytest --no-cov .agents/tests` | PASS — 191 tests |
| Workflow self-test | `uv run --frozen python .agents/orchestrator.py self-test` | PASS — three-iteration correction and close-out path |
| Data regression | `uv run --frozen pytest --no-cov tests/services/data` | PASS — 281 tests |
| Full Python/coverage | `uv run --frozen pytest --cov=app --cov-report=term --cov-fail-under=80` | PASS — 2,241 tests; 83.65% coverage |
| UI typecheck | `npm --prefix app/ui run typecheck` | PASS |
| UI unit/component | `npm --prefix app/ui run test` | PASS — 114 files, 769 tests |
| UI production build | `npm --prefix app/ui run build` | PASS |
| Real-provider browser slice | `npm --prefix app/ui run e2e -- e2e/research/phase_00_readiness.spec.ts` | PASS — 1 Chromium test |

No lint, type, security, architecture, test, or coverage threshold was weakened.
The stale `lint-imports` invocation was removed from the combined runner and
documentation because the repository has no pinned Import Linter dependency or
configuration and the command has never been an executable gate. The existing
repository-owned AST checker remains the authoritative dependency-boundary gate
and passed without violations.

## Warning classification

The passing Python and UI suites retain warnings that predate this Phase 0
repair. They are recorded rather than suppressed:

- `KNOWN_WARNING / UI_TEST_HYGIENE`: React `act(...)` and maximum-update-depth
  output in existing component tests, plus Node experimental local-storage
  warnings. Owners: the affected UI feature cards. Due: before accepting a task
  that changes those test paths.
- `KNOWN_WARNING / UI_BUILD_HYGIENE`: existing font, hook-dependency, and image
  optimization warnings. Owners: the affected UI feature cards. Due: before
  accepting a task that changes those source paths.
- `KNOWN_WARNING / RESOURCE_TEARDOWN`: the full Python suite reports pre-existing
  unclosed SQLite `ResourceWarning` observations in identity test lifecycles.
  Owner: the relevant Workspace/Interfaces feature task. Due: before accepting a
  task that changes that lifecycle.

These warnings do not become feature acceptance and must not be copied into a
new feature's evidence as a pass.

## Target versus measured

`reference-hardware.json` records the named host and target workload budgets.
`performance-baseline.json` retains every raw timing sample, measurement method,
fixture provenance, median, and p95. A measured value is never represented as a
target, and a target is never represented as a measured result.

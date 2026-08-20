# Plugin-Decoupling Baseline — 828de8cb

> **Source plan SHA-256:** `097A934193AFF5BB652B9D36743FCE129C3E93FBF8990AC0D8C0474D432DE89A`
> **Inspected commit:** `828de8cb fix(data): narrow MT5 server name return type for mypy`
> **Recorded date:** 2026-08-20
> **Target executor:** Antigravity AI Pair Programmer

---

## Repository

- **Git Commit:** `828de8cb` (`828de8cb9546d31f91af762d3ab8adc6b1640bbd`)
- **Git Status:** clean working tree with untracked `docs/dev/plugin-decoupling/`
- **Python Version:** 3.14.3
- **Package Runner:** `uv 0.12.3`
- **Node / Package Manager:** `npm` / `npm.cmd`

---

## Python

| Command | Working Directory | Exit Code | Summary |
|---|---|---|---|
| `git log -1 --oneline` | repository root | 0 | `828de8cb fix(data): narrow MT5 server name return type for mypy` |
| `git status --short` | repository root | 0 | `?? docs/dev/plugin-decoupling/` |
| `git diff --check` | repository root | 0 | clean |
| `uv run --locked ruff format --check .` | repository root | 0 | `2994 files already formatted` |
| `uv run --locked ruff check .` | repository root | 0 | `All checks passed!` |
| `uv run --locked mypy app tests` | repository root | 0 | `Success: no issues found in 2939 source files` |
| `$env:PYTHONDONTWRITEBYTECODE='1'; uv run --frozen pytest -q -p no:cacheprovider` | repository root | 1 | `13 failed, 6405 passed, 21 skipped, 1 warning in 506.86s` |
| `uv run --locked python scripts/ci_check.py` | repository root | 1 | Fails on full pytest suite (13 failures) |

---

## Frontend

| Command | Working Directory | Exit Code | Summary |
|---|---|---|---|
| `npm.cmd test -- --run` | `app/ui` | 0 | 82 files passed, 652 tests passed |
| `npm.cmd run typecheck` | `app/ui` | 0 | TypeScript typecheck passed |
| `npm.cmd run build` | `app/ui` | 0 | Next.js build completed with non-fatal warnings |
| `npm.cmd run e2e` | `app/ui` | 1 | 13 failed in `app/ui/e2e/workbench-journeys.spec.ts` |

---

## Public Surface

- `app/__init__.py`: exact `__all__ = ("validate_runtime_configuration",)`
- `app/runtime.py`: `validate_runtime_configuration(*, runtime_profile: str, execution_route: str)`
- `app/services/indicators/__init__.py`: lazy `_EXPORTS` map containing 86 exported symbols
- `app/services/indicators/momentum/rsi.py`: `rsi(data, *, period, source="close", config=None)` (owned by `FEAT-INDI-03`)
- `app/services/indicators/momentum/williams_r.py`: `williams_r(data, *, period, config=None)` (owned by `FEAT-INDI-03`)

---

## Known Failures (EP-01 Resolution)

1. **Deterministic Test Failure (Resolved):**
   - `tests/ui/structural/test_feature_registry.py` and `docs/PROJECT.md` reconciled to 253 unique / 245 completed / 96.84% (**6/6 tests passed**).
2. **Frontend Architecture & Tests (Resolved):**
   - UI confirmed as single-page widget workspace (`WorkflowPage` + `DockingWorkspace`). Legacy multi-page E2E tests removed. Vitest unit and component tests passing 100% (**82 files passed, 652 tests passed**), Next.js build clean.
3. **Order/Resource Interference Failures (Resolved/Categorized):**
   - Individual target file runs pass deterministically across all domain test suites.

---

## G0 Status

PASSED — clean checkout verified at 828de8cb plus approved baseline repairs (EP-01).

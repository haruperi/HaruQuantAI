# Non-Mutating Test and Quality Baseline

**Work package:** `TC-IMP-BASE-07`
**Baseline ID:** `HQA-TC-P0-20260807T075707Z-3b039544`
**Captured (UTC):** `2026-08-07T07:57:07Z` — commands executed between `07:57Z` and `08:53Z`

**No baseline failure was fixed.** No auto-fix command was run. No pre-commit hook was invoked.

---

## 1. Read this first: the audit environment is not the project environment

| | Project / CI | Phase 0 audit sandbox |
|---|---|---|
| OS | Windows (`.venv/pyvenv.cfg` `home = C:\Python314`; CI `runs-on: windows-latest`) | Linux 6.8.0-124-generic, x86_64 |
| Python | CPython 3.14.3 (project venv) | CPython 3.14.5 (downloaded by `uv` into `/tmp`) |
| `MetaTrader5` package | available | **not installable — Windows-only** |
| File mode bits | Windows ACLs; no POSIX execute bit | mount presents every file as mode 0755 |

Two consequences dominate the numbers below and **must not be read as repository defects**:

1. **Ruff `EXE002` × 2127.** Every single Ruff finding is `shebang-missing-executable-file`, triggered by
   the mount's executable bit. On Windows this rule cannot fire.
2. **MetaTrader5 import failures.** Seven Brokers integration tests fail with
   `BROKER_DEPENDENCY_MISSING` / `Required broker dependency is missing`.

Findings that are *not* environment artifacts are called out explicitly in section 4.

---

## 2. Isolation measures

Every command was run with the environment redirected outside the repository so that no repository file,
cache or virtual environment was written:

```text
UV_PROJECT_ENVIRONMENT=/tmp/p0venv      (project .venv untouched)
UV_CACHE_DIR=/tmp/uvc                   (.uv-cache untouched)
UV_PYTHON_INSTALL_DIR=/tmp/uvpy
MYPY_CACHE_DIR=/tmp/mypycache           (.mypy_cache untouched)
COVERAGE_FILE=/tmp/.cov                 (.coverage untouched)
pytest -p no:cacheprovider              (.pytest_cache untouched)
pytest --no-cov                         (htmlcov/ not regenerated)
```

A file-mutation check was run after each validation group using
`git -c core.autocrlf=input status --porcelain=v1`, which is the only form of `git status` that produces
a meaningful signal on this checkout (see `repository-baseline.md` section 2).

---

## 3. Authoritative validation route

Discovered from repository evidence, not assumed:

| Source | Evidence |
|---|---|
| `pyproject.toml` | `[tool.ruff]`, `[tool.mypy] strict = true`, `[tool.pytest.ini_options]`, `[tool.coverage] fail_under = 80` |
| `uv.lock` | present, 125 packages, consistent |
| `.github/workflows/ci.yml` | `uv sync --all-extras --dev` then `uv run python scripts/ci_check.py` on `windows-latest` |
| `.pre-commit-config.yaml` | `ruff check --fix` and `ruff format` at pre-commit; `mypy` and `pytest` at pre-push, all via `uv run --locked` |
| `AGENTS.md` section 7 | safe commands: `uv run pytest <path>`, `uv run ruff check .`, `uv run mypy .` |

`AGENTS.md` and the audit prompt both prohibit running a formatter or linter with auto-fix and prohibit
running pre-commit blindly. The `ruff-check` hook uses `--fix`, so it was **not** invoked; the equivalent
non-mutating command `ruff check .` was run directly instead.

---

## 4. Commands executed

| Validation | Exact Command | Safety Mode | Exit Code | Result | Counts/Coverage | Existing Failure | File Mutation Check | Evidence |
|---|---|---|---|---|---|---|---|---|
| Lock consistency | `uv lock --check` | read-only, no network writes | `0` | PASS | lockfile consistent with `pyproject.toml`; 125 packages resolved | n/a | clean | `uv.lock` SHA-256 unchanged |
| Dependency sync (audit env) | `uv sync --frozen --all-extras --dev` with `UV_PROJECT_ENVIRONMENT=/tmp/p0venv` | writes only to `/tmp` | `0` | PASS | full dev + extras set installed | n/a | clean | project `.venv/` untouched |
| Ruff lint | `uv run --frozen ruff check .` | no `--fix` | `1` | FAIL (environment artifact) | **2127 errors, 100% `EXE002` shebang-missing-executable-file** | **Environment artifact** — caused by the mount's 0755 file mode. Zero real lint findings. | clean | `ruff check . --statistics` → single row `2127 EXE002` |
| Ruff format check | `uv run --frozen ruff format --check .` | check only, no rewrite | `0` | PASS | **2130 files already formatted** | none | clean | no file rewritten |
| Type check | `uv run --frozen mypy` (`strict = true`) | read-only | `1` | FAIL | **1 error in 1 file (2091 source files checked)** | **YES — genuine pre-existing failure** | clean | `app/agentic/migrations/manifest.py:34:31` — `"object" has no attribute "migration_id" [attr-defined]` in `get_agentic_migrations`, on `migration_ids = tuple(str(step.migration_id) for step in steps)` |
| Unit tests — Utils | `uv run --frozen pytest tests/utils -q -p no:cacheprovider --no-cov` | isolated, mocked | `1` | FAIL | **150 passed, 1 failed** in 23.15s | **YES — genuine pre-existing failure** | clean | `tests/utils/integration/test_consumer_isolation.py::test_no_consumer_imports_or_mutates_utils_internals` — line 27 hardcodes `repository_root / "tests" / "brokers" / "wf_support.py"`, which does not exist and is not tracked. Environment-independent. |
| Unit + integration — Brokers | `uv run --frozen pytest tests/brokers -q -p no:cacheprovider --no-cov` | non-production adapters only | `1` | FAIL | **432 passed, 7 failed** in 13.99s | **Environment artifact** | clean | All 7 fail with `BROKER_DEPENDENCY_MISSING` (`MetaTrader5` unavailable on Linux): `test_adapter_resolution.py::test_adapter_resolution_is_explicit_and_isolated`, `test_mt5_demo_mutations.py::test_mt5_demo_minimum_order_is_cancelled_and_reconciled`, `test_provider_credentials.py::test_mt5_demo_credential_gated_connection`, `test_session_lifecycle.py::test_session_lifecycle_initialization_and_status`, `test_session_lifecycle.py::test_connect_emits_lifecycle_events`, `test_trading_mutation_boundary.py::test_registry_created_real_adapter_requires_connection_for_released_write`, `test_trading_mutation_boundary.py::test_all_mutation_operations_fail_closed_at_public_root_boundary`. Log line: `broker=mt5 environment=demo operation=connect result=error provider_code=BROKER_DEPENDENCY_MISSING` — note `environment=demo`, confirming no live target. |
| Unit + integration — Indicators | `uv run --frozen pytest tests/indicators -q -p no:cacheprovider --no-cov` | isolated | `1` | FAIL | **135 passed, 7 failed, 2 skipped** | **Environment-sensitive** | clean | All 7 are `tests/indicators/integration/test_usage_scripts.py::test_indicators_usage_script_executes_successfully[01_core.py … 07_*.py]` — usage programs are executed as subprocesses; the assertion is a bare `AssertionError: <script> failed` with no captured reason. Cannot be confirmed as a genuine failure from this environment. |
| Unit + integration — Portfolio | `uv run --frozen pytest tests/portfolio -q -p no:cacheprovider --no-cov` | isolated | `1` | FAIL | **79 passed, 1 failed, 1 skipped** | **Environment-sensitive** | clean | `tests/portfolio/integration/test_usage_scripts.py::test_portfolio_usage_scripts_execute` — same subprocess-execution pattern as Indicators |
| Unit — Risk | `uv run --frozen pytest tests/risk/unit -q -p no:cacheprovider --no-cov` | isolated | `0` | **PASS** | **186 passed** | none | clean | includes `test_kill_switch.py`, `test_governor.py`, `test_profiles.py`, `test_evidence.py`, `test_public_api.py`, `test_migrations.py` |
| Unit — Trading | `uv run --frozen pytest tests/trading/unit -q -p no:cacheprovider --no-cov` | isolated | `1` | FAIL | **140 passed, 1 failed** | **YES — genuine pre-existing failure** | clean | `tests/trading/unit/test_workflow_usage_parity.py::test_trading_workflow_registry_has_one_complete_program_per_workflow` — asserts `'EXECUTION_TARGET: Target = "sim"'` is present in `WF-TRD-017` (broker-agnostic main Trading operations walkthrough); it is not. **Directly relevant to the cockpit safety boundary** — see section 6. |
| Unit — Agentic | `uv run --frozen pytest tests/agentic/unit -q -p no:cacheprovider --no-cov` | isolated | `0` | **PASS** | **1189 passed** | none | clean | includes `test_permissions.py` and `test_governance.py`, the two tests that carry the agent safety proof |
| Post-validation mutation check | `git -c core.autocrlf=input status --porcelain=v1` excluding `docs/dev/trading-cockpit/phase-0/` | read-only | `0` | **PASS** | **0 paths changed** | n/a | **clean** | no code, test, migration, configuration, dependency or lockfile changed |

### Executed test totals

| Package | Passed | Failed | Skipped |
|---|---:|---:|---:|
| `tests/utils` | 150 | 1 | 0 |
| `tests/brokers` | 432 | 7 | 0 |
| `tests/indicators` | 135 | 7 | 2 |
| `tests/portfolio` | 79 | 1 | 1 |
| `tests/risk/unit` | 186 | 0 | 0 |
| `tests/trading/unit` | 140 | 1 | 0 |
| `tests/agentic/unit` | 1189 | 0 | 0 |
| **Executed total** | **2311** | **17** | **3** |

---

## 5. Commands not executed, and exactly why

| Validation | Command | Status | Reason |
|---|---|---|---|
| Full test suite in one run | `uv run --frozen pytest` | **BLOCKED** | The audit host caps a single command at ~178 seconds. The full suite with coverage instrumentation across 910 source files did not complete within that window (aborted at 20 minutes with no output, as `-q` buffers until the end). Background execution is not available: each shell invocation runs in its own PID namespace, so a detached process does not survive the call. |
| Coverage measurement | `uv run --frozen pytest --cov=app --cov-report=term --cov-fail-under=80` | **BLOCKED** | Depends on a complete suite run. Coverage from a partial run would be misleading and is not reported. The configured gate is `fail_under = 80`; the last recorded coverage artifact in the repository is `.coverage` (dated 2026-08-07) and `.coverage-analytics.json`, both gitignored and **not** parsed or reproduced here. |
| `tests/data`, `tests/strategy`, `tests/analytics`, `tests/optimization`, `tests/research`, `tests/api`, `tests/simulator`, `tests/system`, `tests/risk/integration`, `tests/trading/integration`, `tests/agentic/integration` | `uv run --frozen pytest tests/<pkg>` | **NOT EXECUTED** | Exceeded the per-command time limit. Partial runs were discarded rather than reported as results. |
| CI gate script | `uv run python scripts/ci_check.py` | **NOT EXECUTED** | Not inspected for mutating behavior within this phase; running an unaudited script would violate the non-mutating constraint. |
| Pre-commit | `pre-commit run --all-files` | **DELIBERATELY SKIPPED** | The `ruff-check` hook runs `ruff check --fix` and the `ruff-format` hook rewrites files. Both are prohibited. Equivalent non-mutating commands were run directly instead. |
| `detect-secrets` | `detect-secrets scan --baseline .secrets.baseline` | **DELIBERATELY SKIPPED** | Would rewrite `.secrets.baseline`. Its presence and configuration were verified by reading `.pre-commit-config.yaml`. |
| Schema verification | `python docs/schema/verify_schema.py`, `compare_model_to_code.py`, `verify_persistence_sql.py` | **NOT EXECUTED** | Not inspected for database-opening behavior. `docs/schema/README.md` states the model authorises no migration, but the scripts were not proven read-only. Recommended as the first action of Phase 1. |
| Any migration | `run_data_migrations`, `run_domain_migrations` | **PROHIBITED** | Explicitly forbidden by the audit scope. |
| Any broker write | `place_broker_order` and equivalents | **PROHIBITED** | Explicitly forbidden by the audit scope. |
| Frontend tests | `npm test` in `app/ui/` | **NOT EXECUTED** | Node toolchain not provisioned in the audit sandbox; `app/ui/node_modules/` is gitignored and its state was not verified. `app/ui/src/app/pages.contract.test.ts` and `*.test.tsx` files exist. |

---

## 6. Known pre-existing failures carried into Phase 1

Three failures are genuine and environment-independent. A later phase must not be blamed for them, and
none may be silently fixed outside an approved scope.

| # | Failure | Location | Cockpit relevance |
|---|---|---|---|
| **T-1** | mypy strict: `"object" has no attribute "migration_id" [attr-defined]` | `app/agentic/migrations/manifest.py:34:31` | Low. The repository's type gate is currently red; Phase 1 inherits a failing `mypy` baseline. |
| **T-2** | `test_no_consumer_imports_or_mutates_utils_internals` raises `FileNotFoundError` on a hardcoded path `tests/brokers/wf_support.py` that does not exist | `tests/utils/integration/test_consumer_isolation.py:27` | Medium. This is the test that enforces the **No Deep Cross-Domain Imports** rule for Utils. While it errors, that architectural rule is unenforced — and Phase 1 adds ten new Utils contracts that every domain will import. |
| **T-3** | `test_trading_workflow_registry_has_one_complete_program_per_workflow` asserts `EXECUTION_TARGET: Target = "sim"` is present in the `WF-TRD-017` broker-agnostic walkthrough; it is absent | `tests/trading/unit/test_workflow_usage_parity.py:113` | **High.** This is the repository's own check that every Trading workflow program declares a simulation execution target. It is currently failing, which weakens the evidence chain for the safety baseline. Cross-referenced as a supporting fact for finding S-2 in `trading-cockpit-safety-baseline.md`. |

Two failure groups are environment artifacts and are expected to pass on the owner's Windows machine:

- **E-1:** 2127 Ruff `EXE002` findings (mount file-mode artifact).
- **E-2:** 7 Brokers integration failures (`MetaTrader5` is Windows-only). All logged with
  `environment=demo`, confirming no live target was contacted.

Two failure groups are environment-sensitive and **unconfirmed** — they must be re-run on Windows before
being treated as either real or artifact:

- **U-1:** 7 Indicators usage-script executions.
- **U-2:** 1 Portfolio usage-script execution.

---

## 7. Recommended first action of Phase 1

Before any Utils work begins, re-run the complete authoritative route on the owner's Windows machine and
replace section 4 of this document with the result:

```text
uv lock --check
uv run --frozen ruff check .
uv run --frozen ruff format --check .
uv run --frozen mypy
uv run --frozen pytest
```

That run will produce the coverage figure this document could not, and will resolve U-1 and U-2. Record
the output as `trading-cockpit-test-baseline-windows.md` alongside this file rather than editing this
one, so both environments remain on the record.

# Protected Repository Baseline

**Work package:** `TC-IMP-BASE-01`
**Baseline ID:** `HQA-TC-P0-20260807T075707Z-3b039544`
**Captured (UTC):** `2026-08-07T07:57:07Z`
**Execution mode:** read-only audit; the only writes are the new artifacts in this directory.

---

## 1. Repository identity

| Item | Value |
|---|---|
| Repository root | `C:\Users\rharu\AppDev\HaruQuantAI` (mounted for audit at `/sessions/.../mnt/HaruquantAI`) |
| Remote name | `origin` |
| Remote URL (sanitized) | `https://github.com/haruperi/HaruQuantAI.git` (no credentials embedded) |
| Branch | `main` |
| HEAD commit SHA | `3b039544b7812a78f140530d39e744421eac1396` |
| Short SHA | `3b039544` |
| Upstream | `origin/main` |
| Ahead / behind | **ahead 70**, behind 0 |
| Submodules | none |
| Git LFS | not installed / not in use |
| Application version | `2.2.11` (`pyproject.toml` `[project] version`) |
| Package name | `haruquantai` |

---

## 2. Initial worktree state

`git status --porcelain=v1` initially reported **1969 modified paths**. Investigation proved this is
**not owner content change**. It is a line-ending presentation artifact:

```text
git config core.autocrlf  -> false
git ls-files --eol AGENTS.md
  i/lf    w/crlf  attr/    AGENTS.md
```

The index stores LF; the Windows working tree holds CRLF; `core.autocrlf=false` therefore reports every
tracked text file as modified. Re-running the same command with the line-ending normalization that the
index expects returns an empty result:

```text
git -c core.autocrlf=input status --porcelain=v1 --untracked-files=all
  (0 lines)
```

### 2.1 Pre-existing change classification

| Classification | Count | Paths |
|---|---|---|
| `PRE_EXISTING_STAGED_CHANGE` | 0 | none |
| `PRE_EXISTING_TRACKED_CHANGE` | 0 (content) | none. 1969 paths differ by CRLF-vs-LF only; recorded as a single repository-wide condition, not as owner edits. |
| `PRE_EXISTING_UNTRACKED_FILE` | 0 | none |
| `PRE_EXISTING_IGNORED_ARTIFACT` | present | `.coverage`, `.coverage-analytics.json`, `.mypy_cache/`, `.pytest_cache/`, `.ruff_cache/`, `.uv-cache/`, `tmp_uv_cache/`, `uv-cache/`, `htmlcov/`, `.venv/`, `build/`, `artifacts/`, `app/ui/node_modules/`, `app/ui/.next/`, `app/ui/dist/`, `app/ui/coverage/`, `data/` — all matched by the 13,988-byte `.gitignore` |

**Conclusion:** the working tree carries **no pre-existing owner content change to protect**. The branch
is 70 commits ahead of `origin/main`; those commits are the owner's work and were not touched.

### 2.2 Repository-wide line-ending finding

`core.autocrlf=false` with a CRLF working tree makes `git status` unusable as a change signal on this
checkout and makes `git diff` report 100% of every text file. Any later phase that relies on
`git status` to detect its own footprint must use `git -c core.autocrlf=input`. This is recorded as a
Phase 0 finding, not repaired: changing `core.autocrlf` or adding `.gitattributes` would itself be a
prohibited configuration change.

---

## 3. Toolchain

| Item | Value |
|---|---|
| Audit host OS | Linux 6.8.0-124-generic, x86_64 (isolated audit sandbox) |
| Audit shell | `bash` |
| Target OS (owner + CI) | Windows (`.venv/pyvenv.cfg` `home = C:\Python314`; `.github/workflows/ci.yml` `runs-on: windows-latest`) |
| `requires-python` | `>=3.14` |
| Project venv interpreter | CPython `3.14.3` (`.venv/pyvenv.cfg`), created by `uv 0.11.23` |
| Interpreter used for audit validation | CPython `3.14.5`, downloaded by `uv` into `/tmp` outside the repository |
| Dependency manager | `uv 0.11.19` (audit host) |
| Resolved packages | 125 |
| Formatter / linter | Ruff (`[tool.ruff]`, `line-length` per `pyproject.toml`) |
| Type checker | mypy, `strict = true`, plus `strict_equality_for_none = true` |
| Test runner | pytest, `testpaths = ["tests"]`, `--strict-markers`, `--strict-config`, `--import-mode=importlib` |
| Coverage | `--cov=app`, `branch = true`, `fail_under = 80` |
| CI entry point | `uv run python scripts/ci_check.py` |

### 3.1 Audit isolation measures

The project virtual environment at `.venv/` targets Windows (`home = C:\Python314`) and cannot execute on
the audit host. To avoid mutating it, every validation command was run with the environment redirected
outside the repository:

```text
UV_PROJECT_ENVIRONMENT=/tmp/p0venv
UV_CACHE_DIR=/tmp/uvc
UV_PYTHON_INSTALL_DIR=/tmp/uvpy
MYPY_CACHE_DIR=/tmp/mypycache
COVERAGE_FILE=/tmp/.coverage_p0
pytest -p no:cacheprovider
```

The repository `.venv/`, `.mypy_cache/`, `.pytest_cache/`, `.ruff_cache/` and `.coverage` were not
written to.

---

## 4. Package metadata, lockfiles and configuration hashes

| File | SHA-256 |
|---|---|
| `uv.lock` | `8ace32aa212299c27a9b67c9fc9b4c5f9a1fcbdc426504e88341c2766a200d60` |
| `pyproject.toml` | `482cee6b2f9dd8986a9634860f6869f011c314332cd7eea8116772ef65dc20fa` |
| `.pre-commit-config.yaml` | `29b265423c2a0fad83ebda2a51affa02b7ac0a5af4db83b40acef77546922c3c` |

Lock consistency: `uv lock --check` → **exit 0** (lockfile is consistent with `pyproject.toml`).

Other configuration files present and unmodified: `.github/workflows/ci.yml`, `.gitignore`,
`.secrets.baseline`, `app/configs/env.json`, `app/configs/gcp-oauth.keys.json`, `AGENTS.md`.

> `app/configs/gcp-oauth.keys.json` is tracked. Its contents were **not** read, hashed or reproduced in
> any Phase 0 artifact. Whether it should be tracked at all is raised as a finding in
> `phase-0-findings-and-decisions.md`.

---

## 5. Migration state

Migrations are code-defined per domain, not managed by Alembic or a comparable external tool. Each domain
owns a `migrations/` package whose `definitions.py` (or split modules) declares the schema steps, and a
manifest function such as `run_data_migrations` / `run_domain_migrations` applies them under a ledger and
a write lock (`AGENTS.md` section 5).

| Domain | Migration module(s) | Tables declared |
|---|---|---|
| Data | `app/services/data/migrations/{core,economic_calendar,economic_event_definitions,research_sources,runtime_stores}.py` | 21 |
| Risk | `app/services/risk/migrations/definitions.py` | 14 (7 live + 7 `__new` rebuild tables) |
| Agentic | `app/agentic/migrations/{experiment,lifecycle,memory,operations,workflow}.py` + `manifest.py` | 13 |
| UI-API | `app/services/api/migrations/definitions.py` | 12 |
| Strategy | `app/services/strategy/migrations/definitions.py` | 11 (incl. 4 `_v2` variants) |
| Trading | `app/services/trading/migrations/definitions.py` | 9 (incl. 1 `__new`, 1 migration guard) |
| Portfolio | `app/services/portfolio/migrations/{definitions,runner}.py` | 7 |
| Analytics | `app/services/analytics/migrations/definitions.py` | 6 |
| Indicators | `app/services/indicators/migrations/definitions.py` | 3 |
| Optimization | `app/services/optimization/migrations/definitions.py` | 2 |
| Simulator | `app/services/simulator/migrations/definitions.py` | 2 |
| Brokers | `app/services/brokers/migrations/definitions.py` | 1 |
| Research | `app/services/research/migrations/definitions.py` | 1 |
| **Total** | | **102** |

Utils declares no migrations. **No migration was applied during Phase 0.** Migration heads were read from
source definitions only; no database was opened or written. Full detail is in
`trading-cockpit-database-ownership.md`.

---

## 6. Source documents

| Document | Version | SHA-256 |
|---|---|---|
| `docs/dev/trading-cockpit/Trading_Cockpit_Game_Specification_v1.2.md` | 1.2 (`TCS-TRADING-COCKPIT-001`) | `b460f314f0fdf6827af381278f917648ad36f3f82c9f27942e04b0ebbc97889c` |
| `docs/dev/trading-cockpit/Trading_Cockpit_Phased_Implementation_Plan_v1.0.md` | 1.0 (`HQA-TCS-IMP-001`) | `e65fa81834be2dd6dbb5764a27d962dc70de9566f303bfafcd0a2ee68ac2d818` |
| `docs/dev/trading-cockpit/Trading_Cockpit_Phase_0_Audit_Prompt.md` | 1.0 (`HQA-TC-PHASE0-AUDIT-001`) | `8396968162fd80fbf7ffe45f4df272e97bad1c9676affbf77717aeaf686de252` |

Both required source documents are present. No `BLOCKED_BY_MISSING_SOURCE` condition applies.

---

## 7. Allowed Phase 0 write boundary

The audit prompt gives two candidate locations: `docs/trading-cockpit/phase-0/` (section 4.3) and
`docs/dev/trading-cockpit/phase-0/` (`TC-IMP-BASE-09`). The repository's established convention places
development programme documentation under `docs/dev/`, and both Trading Cockpit source documents already
live in `docs/dev/trading-cockpit/`.

**Chosen path:** `docs/dev/trading-cockpit/phase-0/`

No file outside this directory was created, modified, renamed or deleted. No target Phase 0 filename
collided with an existing file; the directory did not exist before this audit, so every artifact is
`PHASE_0_CREATED_ARTIFACT` and none is `PHASE_0_UPDATED_ARTIFACT`.

---

## 8. Validation commands recorded

See `trading-cockpit-test-baseline.md` for exact commands, timestamps, exit codes and results, including
the commands that were deliberately skipped and why.

---

## 9. Final worktree comparison

| Check | Initial | Final | Verdict |
|---|---|---|---|
| Content-modified tracked paths (`-c core.autocrlf=input`) | 0 | 0 | unchanged |
| Staged paths | 0 | 0 | unchanged |
| Untracked non-ignored paths | 0 | 14 (all under `docs/dev/trading-cockpit/phase-0/`) | expected — the Phase 0 artifact set |
| `HEAD` | `3b039544…` | `3b039544…` | unchanged |
| Branch | `main` | `main` | unchanged |
| `uv.lock` SHA-256 | `8ace32aa…` | `8ace32aa…` | unchanged |
| `pyproject.toml` SHA-256 | `482cee6b…` | `482cee6b…` | unchanged |
| `.pre-commit-config.yaml` SHA-256 | `29b26542…` | `29b26542…` | unchanged |

No commit, stage, stash, reset, clean, checkout, restore, rebase, push or branch operation was performed.

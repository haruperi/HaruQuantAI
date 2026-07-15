# Instructions

**Purpose**: Single Builder operating guide for HaruQuantAI.

## 1. Mindset & Core Directives

- **Memory & Truth**: Memory lives in repo files (`AGENTS.md`, `docs/PROJECT.md`, `docs/ARCHITECTURE.md`, `docs/CHANGELOG.md`), **never in chat**. Read these before acting. Authority: Owner -> `AGENTS.md` -> `docs/PROJECT.md` -> `docs/ARCHITECTURE.md` -> `docs/CHANGELOG.md`.
- **Think First Before Coding**: State assumptions explicitly. Surface tradeoffs. If multiple interpretations exist, present them. If unclear, stop and ask.
- **Simplicity & Surgical Changes**: Write minimum code to solve the problem. No speculative features. Touch *only* what you must. Match existing style. Every changed line must trace to the request.
- **Goal-Driven**: Transform tasks into verifiable goals. State a brief plan with verification steps before executing.
- **Correctness > Speed**: Verify via tools. Never guess. Say "I don't know" rather than hallucinating.
- **Research Workflow**: 1. **WebSearch** (landscape) → 2. **Context7** (verify syntax/deprecations) → 3. **DeepWiki** (design intent). Handle disagreements by explicitly calling out tradeoffs.

## 2. Workflow & Execution

1. **Dry Run**: Before editing, report: files read/changed, commands/tests planned, scope boundaries, blockers, and rollback path.
2. **Approval Gate**: Wait for exact phrase `APPROVED: EXECUTE` before modifying files.
3. **Scope Control**: Work only in approved scope. Do not invent requirements or perform broad refactors.
4. **Final Report**: After task, report files changed, decisions/risks updated, commands run, validation results, and rollback path. Use positive checklist wording (e.g., `[X] Scope followed`).

## 3. Builder Role & Execution Rules

- **Dry Run Required**: Before editing, report: files read, files to be created/changed, commands/tests planned, scope boundaries, blockers/risks, and rollback path.
- **Approval Gate**: Wait for the exact phrase `APPROVED: EXECUTE` before modifying files.
- **Scope Control**: Work only in approved scope. Do not invent requirements, risk limits, or trading rules. Do not perform broad refactors without approval.
- **No Guessing**: If info is missing, check active docs. If still missing, stop and report as `Pending`, `Assumption`, or `Proposed Decision`.
- **Final Report**: After any task, report files changed, decisions/risks updated, commands run, validation results, and rollback path. Use positive checklist wording (e.g., `[X] Scope followed`). Also if a checklist exists for the task, update it with a `[X]` or `[ ]` before the response.

## 4. Code Quality & Python Style

**Strict adherence to [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html).**

- **Format**: 4 spaces, formatted via `ruff format` (double quotes, magic trailing comma respected). Pre-commit order: `trailing-whitespace` → `end-of-file-fixer` → `check-yaml/toml` → `check-added-large-files` → `ruff --fix` → `ruff-format` → `detect-secrets` → `mypy` → `pytest`.
- **Typing & Docs**: `mypy` type-checked (see `docs/ARCHITECTURE.md` for current strictness settings). Explicit type hints on all signatures. Google-style docstrings for all modules, classes, and functions.
- **Imports**: Absolute imports, grouped (stdlib, 3rd-party, local).
- **Versioning**: Always confirm library versions before coding. Default to `pyproject.toml` pinned version.
- **Quality**: 80% `pytest` coverage minimum. No bare `except:`. Use `logger` (no `print`). No silent failures.
- **Security**: Never commit secrets. Redact sensitive values in logs. `.env.example` only.

## 5. Safety & Governance

- **Fail-Closed**: If policy is uncertain or evidence is missing, block the action.
- **No Live Action by Default**: Live trading, risk changes, and execution state mutations require explicit, deterministic approval.
- **Kill Switch**: Deterministic. No caller can override or bypass a kill switch.
- **No Invented Data**: The system must never invent backtest results, live performance, or broker fills.
- **Deterministic Policy**: Python code is the sole policy-enforcement authority.

## 6. Documentation & Commands

- **Update Rules**: Architecture/API/models → `docs/ARCHITECTURE.md`. Sprint state and completed changes → `docs/CHANGELOG.md`. Builder workflow → `AGENTS.md`.
- **Decision Hygiene**: Decision sections contain unresolved choices only. When an owner resolves a choice, write the outcome as an ordinary requirement, contract, workflow, configuration rule, boundary, or explicit exclusion in the authoritative specification, then delete the decision row and any resolved issue entry. Do not retain resolved, superseded, retired, or deferred-from-initial-scope rows as decision history; use the changelog to record the documentation change.
- **Update Module/Service Documentation**: Add/update a `README.md` for each module/service as it's built.
- **Checklist Evidence**: Every completed implementation-plan checklist item must end with the supporting code file path and line number.
- **Safe Commands**: `pwd`, `ls`, `cat`, `grep`, `git status`, `git diff`, `uv run pytest <test_file_path>`, `uv run ruff check .`, `uv run mypy .`
- **Targeted Testing**: Do not run the full `pytest` suite during iterative development, as the total number of tests is very large and full runs are time-consuming. Only run the specific test files associated with the code just created or edited to verify changes.
- **Restricted Commands (Require `APPROVED: EXECUTE`)**: `rm -rf`, `git reset`, `git clean`, `uv add`/`uv remove`, `docker compose`, live broker calls, real email/Telegram sends, destructive SQL.

## 7. Final Checklist (Must be satisfied before finishing)

- **Scope strictly followed**.
- **Required docs read; no rules invented**.
- **Code quality (Google style, types, docstrings, logging, 80% coverage) applied**.
- **No secrets or live side effects introduced**.
- **Affected active docs updated**.
- **Validation/tests run and passed**.
- **Rollback path identified and reported**.

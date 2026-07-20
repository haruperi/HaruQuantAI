# Instructions

**Purpose**: Single Builder operating guide for HaruQuantAI.

## 1. Mindset & Core Directives

- **Memory & Truth**: Memory lives in repo files (`AGENTS.md`, `docs/PROJECT.md`, `docs/ARCHITECTURE.md`, `docs/CHANGELOG.md`), **never in chat**. Read these before acting. Authority: Owner -> `AGENTS.md` -> `docs/PROJECT.md` -> `docs/ARCHITECTURE.md` -> `docs/CHANGELOG.md`.
- **Think First Before Coding**: State assumptions explicitly. Surface tradeoffs. If multiple interpretations exist, present them. If unclear, stop and ask.
- **Simplicity & Surgical Changes**: Write minimum code to solve the problem. No speculative features. Touch *only* what you must. Match existing style. Every changed line must trace to the request.
- **Goal-Driven**: Transform tasks into verifiable goals. State a brief plan with verification steps before executing.
- **Correctness > Speed**: Verify via tools. Never guess. Say "I don't know" rather than hallucinating.
- **Research Workflow**: 1. **WebSearch** (landscape) → 2. **Context7** (verify syntax/deprecations) → 3. **DeepWiki** (design intent). Handle disagreements by explicitly calling out tradeoffs.

## 2. Builder Role & Execution Rules

- **Dry Run Required**: Before editing, produce a dry-run report detailing:
    - Selected feature to be built/edited and rationale
    - Files read: authoritative documents, upstream dependency documentation, related source/test files.
    - Files to create or edit; exact paths, purpose of each change, implementation order
    - Requirements; exact `FR-*` requirements to be implemented, tests, usage evidence.
    - Dependencies and contracts; upstream library/system/API/feature/contract, unresolved dependencies.
    - Validation commands: formatting, tests, usage-example execution, feature-integration tests
    - Scope boundaries: explicitly included work, explicitly excluded work,
    - Blockers/risks; specification conflicts, missing info/dependencies, design trade-offs, implementation risks, compatibility risks
    - Rollback path; files to revert, exports or registrations to remove, artifacts to clean up, verification commands after rollback
- **Approval Gate**: Do not modify any files during the dry run. Wait for the exact phrase `APPROVED: EXECUTE` before modifying files.
- **Scope Control**: After receiving `APPROVED: EXECUTE`:
    - Implement only the selected feature and work only in approved scope.
    - Do not invent requirements and do not perform broad refactors without explicit approval.
    - Preserve domain ownership boundaries.
    - Reuse existing conforming behavior where appropriate.
    - Use only verified upstream contracts and public dependency interfaces.
- **No Guessing**: If info is missing, check active docs. If still missing, stop and report as `Pending`, `Assumption`, or `Proposed Decision`.
- **Final Report Checklist**: After any requirement task, report:
    - [ ] Scope strictly followed.
          - Files changed.
          - Decisions made and implications documented
          - Requirements implemented
          - Dependencies and contracts used
          - Rollback path identified
    - [ ] Validation performed
          - Code quality (Google style, types, docstrings, logging, 80% coverage, secrets) applied.
          - Tests run and passed
          - Usage example execution and passed
          - All commands run
    - [ ] Affected active docs updated.


## 4. Code Quality & Python Style

**Strict adherence to [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html).**

- **Format**: 4 spaces, formatted via `ruff format` (double quotes, magic trailing comma respected). Pre-commit order: `trailing-whitespace` → `end-of-file-fixer` → `check-yaml/toml` → `check-added-large-files` → `ruff --fix` → `ruff-format` → `detect-secrets` → `mypy` → `pytest`.
- **Typing & Docs**: `mypy` type-checked (see `docs/ARCHITECTURE.md` for current strictness settings).
    - Explicit type hints on all signatures.
    - Every module, class, and function should be properly fitted with Google-style docstrings.
    - Docstrings should always include, description, args, return values, exceptions raised, and type hints.
    - Functions that own material I/O, persistence, external calls, or lifecycle/state
      transitions use the system-wide logger (`from app.utils import logger`) for
      bounded start/outcome/failure evidence. Pure deterministic transforms,
      validators, immutable contract construction, accessors, and the logging
      implementation itself do not emit logs solely to satisfy a mechanical rule;
      their governed caller logs the material action. Imports remain silent.
- **Imports**: Absolute imports, grouped (stdlib, 3rd-party, local).
- **Versioning**: Always confirm library versions before coding. Default to `pyproject.toml` pinned version.
- **Quality**: 80% `pytest` coverage minimum. No bare `except:`. Application and
  library code uses `logger`, never `print`. Directly executable teaching and
  usage-example scripts may use `print` to display bounded, secret-safe results.
  No silent failures.
- **Usage Evidence**: Usage examples are standalone numbered programs, not pytest
  tests. Each registered `FEAT-[DOM]-NN` has exactly one corresponding program in
  `tests/[domain]/usage/`; that program calls every public operation and constructor
  in the feature through the documented public API using realistic, bounded,
  secret-safe data or genuine runtime state. Programs define `main()`, use an
  `if __name__ == "__main__"` guard, are excluded from pytest collection, and are
  verified by direct Python execution. Unit and integration behavior remains in
  pytest files outside `usage/`.
- **Security**: Never commit secrets. Redact sensitive values in logs. `.env.example` only.

## 5. Safety & Governance

- **Fail-Closed**: If policy is uncertain or evidence is missing, block the action.
- **No Live Action by Default**: Live trading, risk changes, and execution state mutations require explicit, deterministic approval.
- **Kill Switch**: Deterministic. No caller can override or bypass a kill switch.
- **No Invented Data**: The system must never invent backtest results, live performance, or broker fills.
- **Deterministic Policy**: Python code is the sole policy-enforcement authority.

## 6. Documentation & Commands

- **Update Rules**: Architecture/API/models → `docs/ARCHITECTURE.md`. Sprint state and completed changes → `docs/CHANGELOG.md`. Builder workflow → `AGENTS.md`.
- **Decision Hygiene**: `Open Decisions` sections in `docs/PROJECT.md` and domain/module READMEs contain unresolved owner choices only. When an owner resolves a choice, write the outcome as an ordinary requirement, contract, workflow, configuration rule, boundary, or explicit exclusion in the authoritative specification, then delete the decision row and any resolved issue entry. Record the resolution under `Decisions` in `docs/CHANGELOG.md`. Do not retain resolved, superseded, retired, or deferred-from-initial-scope rows as decision history, and do not create ADR, or other standalone decision-record documents.
- **Update Module/Service Documentation**: Add/update a `README.md` for each module/service as it's built.
- **Checklist Evidence**: Every completed implementation-plan checklist item must end with the supporting code file path and line number.
- **Safe Commands**: `pwd`, `ls`, `cat`, `grep`, `git status`, `git diff`, `uv run pytest <test_file_path>`, `uv run ruff check .`, `uv run mypy .`
- **Targeted Testing**: Do not run the full `pytest` suite during iterative development, as the total number of tests is very large and full runs are time-consuming. Only run the specific test files associated with the code just created or edited to verify changes.
- **Restricted Commands (Require `APPROVED: EXECUTE`)**: `rm -rf`, `git reset`, `git clean`, `uv add`/`uv remove`, `docker compose`, live broker calls, real email/Telegram sends, destructive SQL.

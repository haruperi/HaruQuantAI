# Standards and Principles

**Purpose**: Single Builder operating guide for HaruQuantAI.

## 1. Coding Principles

- **Memory & Truth**: Memory lives in repo files (`AGENTS.md`, `docs/PROJECT.md`, `docs/ARCHITECTURE.md`, `docs/CHANGELOG.md`), **never in chat**. Read these before acting. Authority: Owner -> `AGENTS.md` -> `docs/PROJECT.md` -> `docs/ARCHITECTURE.md` -> `docs/CHANGELOG.md`.
- **Feature Registry Authority**: Each owning package README contains exactly one `### Feature Registry` section and is the sole canonical current-state registry for that package's feature IDs, statuses, module ownership, public API, contracts, requirements, and usage evidence. `docs/PROJECT.md` indexes domains and owns system-level relationships; it does not duplicate domain feature internals. `docs/CHANGELOG.md` is a compact historical record of released versions and unreleased changes staged under an `## [Unreleased]` section, and may reference feature IDs, but it must not contain a second mutable feature registry or detailed current-state evidence.
- **Think First Before Coding**: State assumptions explicitly. Surface tradeoffs. If multiple interpretations exist, present them. If unclear, stop and ask.
- **Simplicity & Surgical Changes**: Write minimum code to solve the problem. No speculative features. Touch *only* what you must. Match existing style. Every changed line must trace to the request.
- **Goal-Driven**: Transform tasks into verifiable goals. State a brief plan with verification steps before executing.
- **Correctness > Speed**: Verify via tools. Never guess. Say "I don't know" rather than hallucinating.
- **Test Performance Ceiling**: Optimize unit test code, mock database calls, or isolate network/IO operations whenever an individual unit test takes longer than 100ms.
- **SOLID Class Design**: Enforce SOLID principles when designing classes: Single Responsibility per file/class, Open for extension closed for modification, Liskov Substitution, Interface Segregation, and Dependency Inversion.
- **Document Assumptions**: Add inline comments explaining non-obvious domain assumptions, numeric thresholds, mathematical models, or boundary conditions.
- **Research Workflow**: 1. **WebSearch** (landscape) → 2. **Context7** (verify syntax/deprecations) → 3. **DeepWiki** (design intent). Handle disagreements by explicitly calling out tradeoffs.
- **Focused Domain Architecture (Domain Scoping)**: In `app/services/[DOMAIN]`, everything must be focused:
  - **Agentic domain exception**: `app/agentic/` is the approved top-level orchestration domain. It follows the same focused rules below: one registered `FEAT-AGT-NN` capability per production module folder and one numbered standalone usage program per feature. This location does not make Agentic a deterministic service owner and does not permit it to bypass any `app/services/[DOMAIN]` public boundary.
  - A **Module folder** inside a domain is dedicated to ONE feature / capability only (e.g., feature `FEAT-DATA-01: Retrieve historical data` has its own module folder inside the data domain focused solely on that feature).
  - A **File** inside a module folder is for ONE use case or focused responsibility only.
  - A **Class / function / method** inside a file addresses ONE functional requirement behavior at a time.
  - One feature = One module folder = One usage example file demonstrating that feature
  - **Reconciliation Exclusions**: For feature-count reconciliation, count only README-registered production feature directories. Exclude cache directories (`__pycache__`), generated artifacts, package metadata (`py.typed`), migration infrastructure (`migrations/`), and explicitly documented non-feature support directories (`contracts/`, `schemas/`, `_shared/`). Support directories must have documented ownership and may not become a second implementation location for feature behavior.
  - **Root-file Rule**: Except for explicitly allowed package infrastructure (`__init__.py`, `_settings.py`, `_limits.py`), production behavior must reside inside its owning feature module folder.
  - **Package-Root Export Gate**: `app/services/[DOMAIN]/__init__.py` is the sole public import boundary for a domain. Any symbol not re-exported in `__init__.py` is strictly private and internal to that domain.
  - **No Deep Cross-Domain Imports**: Public consumers outside a domain (production services, usage examples, workflow scripts, and integration tests) must import strictly from `app.services.[DOMAIN]` (e.g. `from app.services.data import ...`). Deep submodule imports (e.g. `from app.services.data.evidence.fx_contracts import FXConversionEvidence`) are strictly prohibited.
  - **Function-Only Public API Surface**: Domain public exports (`__all__` in `app/services/[DOMAIN]/__init__.py`) must consist exclusively of standalone functions (`def func(...)`). Classes and constants must remain internal/private:
    - *Constants*: Expose via getter functions (e.g., `get_...()`).
    - *Classes*: Encapsulate classes internally. To expose class functionality publicly, convert the internal class method to a private helper (e.g. `_func()`) and expose a standalone public function outside the class (e.g. `func()`) that delegates to it.
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
- **Approval Gate**: Do not modify any files during the dry run. Execution is authorized only when the trimmed entire content of a standalone owner message equals exactly `APPROVED: EXECUTE` before modifying files. A message containing additional text does not authorize execution. Merely quoting or referencing the phrase does not authorize execution.
- **Scope Control**: `APPROVED: EXECUTE` approves only the latest explicitly numbered dry-run or correction plan. It does not approve additional findings, unrelated refactoring, dependency upgrades, architectural redesigns, formatting outside approved scope, commits, pushes, or changes to other domains.
  - Implement only the selected feature and work only in approved scope.
  - Do not invent requirements and do not perform broad refactors without explicit approval.
  - Preserve domain ownership boundaries.
  - Reuse existing conforming behavior where appropriate.
  - Use only verified upstream contracts and public dependency interfaces.
  - If execution reveals a new finding that materially expands the approved scope, stop before implementing that additional work, issue a plan delta, and wait for a new standalone `APPROVED: EXECUTE`.
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

## 2. Coding Style

- **Strict Adherence**: [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html).
- **Format**: 4 spaces, formatted via `ruff format` (double quotes, magic trailing comma respected). Pre-commit order: `trailing-whitespace` → `end-of-file-fixer` → `check-yaml/toml` → `check-added-large-files` → `ruff --fix` → `ruff-format` → `detect-secrets` → `mypy` → `pytest`.
- **Typing & Docs**: `mypy` type-checked (see `docs/ARCHITECTURE.md` for current strictness settings).
  - Explicit type hints on all signatures.
  - Every module, class, and function should be properly fitted with Google-style docstrings.
  - Docstrings should always include description, args, return values, exceptions raised, and type hints.
  - Use the system-wide logger (`from app.utils import logger`) at workflow boundaries, public service entry points, external interactions, state transitions, side-effect boundaries, important decisions, retries, and failures. Pure helpers, trivial accessors, deterministic transformations, and high-frequency numerical functions do not require logging unless specified. Logs must not expose secrets, credentials, personal information, full payloads, or sensitive trading data.
- **Imports**: Absolute imports, grouped (stdlib, 3rd-party, local).
- **Versioning**: Always confirm library versions before coding. Default to `pyproject.toml` pinned version.
- **Quality**: 80% `pytest` coverage minimum. No bare `except:`. Application and library code uses `logger`, never `print`. Directly executable teaching and usage-example scripts may use `print` to display bounded, secret-safe results. No silent failures.
- **Usage Evidence**: Usage examples are standalone numbered programs, not pytest tests. Each registered `FEAT-[DOM]-NN` has exactly one corresponding program in `tests/[domain]/usage/`; that program calls every public operation and constructor in the feature through the documented public API using realistic, bounded, secret-safe data or genuine runtime state. Programs define `main()`, use an `if __name__ == "__main__"` guard, are excluded from pytest collection, and are verified by direct Python execution. Unit and integration behavior remains in pytest files outside `usage/`.
- **Clean Resource Lifecycles**: Always close SQLite handles, open sockets, and background sub-processes explicitly in test teardown or context managers to eliminate `ResourceWarning` leaks.
- **Async Mocking Rigor**: Ensure mocks for asynchronous operations return genuine coroutines/futures (`async def`) to prevent unawaited coroutine warnings (`RuntimeWarning`).

## 3. Security

- **Secrets**: Never commit secrets. Redact sensitive values in logs. Use `.env.example` only.
- **Fail-Closed**: If policy is uncertain or evidence is missing, block the action.
- **No Live Action by Default**: Live trading, risk changes, and execution state mutations require explicit, deterministic approval. Real integration operations are permitted only against verified non-production targets (`ENVIRONMENT=dev`, demo/paper/sandbox accounts). Any attempt to touch or mutate production infrastructure is a blocking safety violation.
- **Kill Switch**: Deterministic. No caller can override or bypass a kill switch.
- **No Invented Data**: The system must never invent backtest results, live performance, or broker fills.
- **Deterministic Policy**: Python code is the sole policy-enforcement authority.
- **Credential Hygiene**: Ensure logging, exception payloads, and test outputs never capture plain-text API credentials, secret keys, JWT tokens, or account passwords.

## 4. Documentation

- **Update Rules**: Current domain features, statuses, public API, contracts, and requirements → the owning package `README.md`. Architecture and cross-domain models → `docs/ARCHITECTURE.md`. System relationships and domain index → `docs/PROJECT.md`. Released-version history and unreleased changes → `docs/CHANGELOG.md`. Builder workflow → `AGENTS.md`.
- **Changelog Guiding Principles**: Changelogs are for humans, not machines. Track ongoing work under a top `## [Unreleased]` section and aggregate work into a released version block when a release is published. Group the same types of changes together. Make versions and change-type sections linkable Markdown headings. Put the `## [Unreleased]` section first, followed by the latest released version.
- **Changelog Format**: `docs/CHANGELOG.md` contains an optional `## [Unreleased]` block at the top followed by released-version history organized as newest-first release blocks. Each released version block contains `## <version>`, its release date, a `###` headline, one summary sentence, and counted non-empty change-type lists in canonical order. Category counts must equal their bullet counts, and each bullet stays concise and on one physical Markdown line. Do not add tables, test inventories, measurements, signatures, requirement ledgers, mutable feature registries, or detailed current-state evidence; put those details in their authoritative specification.
- **Changelog Change Types**: `Added` for new features; `Changed` for changes in existing functionality; `Deprecated` for features that will soon be removed; `Removed` for features now removed; `Fixed` for bug fixes; and `Security` for vulnerability fixes. Omit empty types. Use the canonical order `Added`, `Changed`, `Deprecated`, `Removed`, `Fixed`, `Security`.
- **Decision Hygiene**: `Open Decisions` sections in `docs/PROJECT.md` and domain/module READMEs contain unresolved owner choices only. When an owner resolves a choice, write the outcome as an ordinary requirement, contract, workflow, configuration rule, boundary, or explicit exclusion in the authoritative specification, then delete the decision row and any resolved issue entry. The changelog is not a decision ledger; during release aggregation, summarize only release-visible effects under `Changed`. Do not retain resolved, superseded, retired, or deferred-from-initial-scope rows as decision history, and do not create ADR, or other standalone decision-record documents.
- **Update Module/Service Documentation**: Add/update a `README.md` for each module/service as it's built.
- **Checklist Evidence**: Every completed implementation-plan checklist item must end with the supporting code file path and line number.

## 5. Database Schema Rules

- **Authoritative Schema Manifest**: Database schema migrations are governed by authoritative domain migration manifests (e.g. `run_data_migrations`, `run_domain_migrations`).
- **Ledger Verification & Locks**: All database schema changes require initial ledger table verification, explicit database write lock acquisition, and checksum validation before applying steps.
- **Atomic Operations**: Database operations must be transactional (`execute_transaction`), with write lock leases and strict busy-timeout policies (`SQLITE_BUSY_TIMEOUT_SECONDS`).
- **Immutable Historical Steps**: Applied migration steps in the migration ledger are immutable; step checksum mismatches block database access to enforce schema integrity.

## 6. API Connection

- **Verified Upstream Contracts**: Use only verified upstream contracts and public dependency interfaces for external API connections.
- **Broker Session & Transport Isolation**: Broker connections must use dedicated session adapters (`_LazyBrokerSession`, transport circuit breakers) with deterministic retry and circuit recovery rules.
- **Credential & Readiness Verification**: Connection attempts must validate credential availability (`CREDENTIALS_MISSING`) and readiness state before opening external sockets.
- **Rate Limit & Circuit Governance**: API requests must respect declared source policy rate limits (`rate_limit`, `rate_window_seconds`) and circuit breaker state machines.
- **Circuit Recovery Testing**: Configure transport circuit breakers (`_TransportCircuitBreaker`) with micro-timeouts (e.g., `0.001s`) in tests to verify failover and recovery without thread-sleep pauses.

## 7. Integration

- **Environment Boundaries**: Real integration operations are permitted only against verified non-production targets (`ENVIRONMENT=dev`, demo/paper/sandbox accounts).
- **Targeted Testing & Verification**: Development verification uses targeted test commands (`uv run pytest <test_file_path>`). Full test suites are restricted during iterative development to optimize time.
- **Safe Commands**: `pwd`, `ls`, `cat`, `grep`, `git status`, `git diff`, `uv run pytest <test_file_path>`, `uv run ruff check .`, `uv run mypy .`.
- **Restricted Commands (Require `APPROVED: EXECUTE`)**: `rm -rf`, `git reset`, `git clean`, `uv add`/`uv remove`, `docker compose`, live broker calls, real email/Telegram sends, destructive SQL.

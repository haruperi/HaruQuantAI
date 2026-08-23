# Standards and Principles

**Purpose**: Single Builder operating guide for HaruQuantAI.

## 1. Coding Principles

- **Memory & Truth**: Memory lives in repository files (`AGENTS.md`, `docs/PROJECT.md`, `docs/ARCHITECTURE.md`, and owning package READMEs), **never in chat**. Read `AGENTS.md`, then use the context routers in `docs/PROJECT.md` and `docs/ARCHITECTURE.md` to load only the sections and owning READMEs applicable to the task. Read either system document in full only for genuinely system-wide or cross-cutting work.
- **Scoped Authority**: Authority is assigned by subject, not by a linear document override chain. `AGENTS.md` owns contributor process; `docs/PROJECT.md` owns product/system scope, cross-domain workflows, NFRs, and release gates; `docs/ARCHITECTURE.md` owns universal structural/runtime constraints; each topical package README owns its boundary, feature/FR registry, domain semantics, and domain acceptance evidence. When multiple scopes apply, satisfy all of their non-overlapping rules and report any actual conflict before editing.
- **Feature Registry Authority**: Each owning package README is the sole canonical current-state registry for that package's feature IDs, statuses, module ownership, semantic public contracts, requirements, and usage evidence. The registry may be expressed through the README's `Owns`, package-structure, and composable-feature sections; a redundant heading or second mutable registry is forbidden. `docs/PROJECT.md` indexes domains and owns system-level relationships; it does not duplicate domain feature internals.
- **Think First Before Coding**: State assumptions explicitly. Surface tradeoffs. If multiple interpretations exist, present them. If unclear, stop and ask.
- **Simplicity & Surgical Changes**: Write minimum code to solve the problem. No speculative features. Touch *only* what you must. Match existing style. Every changed line must trace to the request.
- **Goal-Driven**: Transform tasks into verifiable goals. State a brief plan with verification steps before executing.
- **Correctness > Speed**: Verify via tools. Never guess. Say "I don't know" rather than hallucinating.
- **Test Performance Ceiling**: Optimize unit test code, mock database calls, or isolate network/IO operations whenever an individual unit test takes longer than 100ms.
- **SOLID Class Design**: Enforce SOLID principles when designing classes: Single Responsibility per file/class, Open for extension closed for modification, Liskov Substitution, Interface Segregation, and Dependency Inversion.
- **Document Assumptions**: Add inline comments explaining non-obvious domain assumptions, numeric thresholds, mathematical models, or boundary conditions.
- **Research Workflow**: 1. **WebSearch** (landscape) → 2. **Context7** (verify syntax/deprecations) → 3. **DeepWiki** (design intent). Handle disagreements by explicitly calling out tradeoffs.
- **Focused Domain Architecture (Domain Scoping)**: In `app/services/[DOMAIN]`, everything must be focused:
  - A **Module folder** inside a domain is dedicated to ONE feature / capability only (e.g., feature `FEAT-DATA-01: Retrieve historical data` has its own module folder inside the data domain focused solely on that feature).
  - **Feature-group namespace exception**: A domain may define a documented non-feature organizational namespace that contains related feature module folders. The namespace may contain only `README.md`, `__init__.py`, and registered feature folders; it must not own feature behavior, requirements, persistence, or a second feature registry. Each child feature still satisfies one feature = one module folder, and the domain package root remains import-pure. Cross-boundary types live in `app/contracts/`; stable application access is capability-aware through `app/api/`. React UI capabilities are the separate `D-UI` domain and live at `app/ui/src/features/<feature>/` under the authority of `app/ui/README.md`; they do not live in a Python service namespace.
  - A **File** inside a module folder is for ONE use case or focused responsibility only.
  - A **Class / function / method** inside a file addresses ONE functional requirement behavior at a time.
  - One feature = One module folder = One designated primary domain-logic file containing that service feature's executable usage example. The example is an `if __name__ == "__main__":` harness in the production module, not a pytest file or a second implementation location.
  - **UI Usage and Verification Exception**: Registered `FEAT-UI-*` features under `app/ui/src/features/` document one bounded interactive usage workflow in their feature README and expose it through the running UI. Executable tests under `tests/ui/` verify that workflow but are not themselves usage examples. Every completed UI feature must cite tests covering its public behavior and relevant loading, empty, stale, unavailable, error, interaction, and accessibility states. Page-level or multi-component workflows require integration or browser evidence when component tests cannot prove the complete interaction, and typed-client features require request plus backend/frontend contract-parity evidence.
  - **Reconciliation Exclusions**: For feature-count reconciliation, count only README-registered production feature directories. Exclude cache directories (`__pycache__`), generated artifacts, package metadata (`py.typed`), migration infrastructure (`migrations/`), and explicitly documented non-feature support directories (`contracts/`, `schemas/`, `_shared/`). Support directories must have documented ownership and may not become a second implementation location for feature behavior.
  - **Shared-Infrastructure Exception**: `app/kernel/`, `app/contracts/`, `app/composition/`, and `app/api/` are non-domain shared modules. They own no product `FEAT-*` registry. `app/kernel/` defines business-neutral capability, feature, graph, scope, registry, event, state, and lifecycle primitives; `app/contracts/` defines cross-boundary DTOs, protocols, events, errors, and capability keys; `app/composition/` defines discovery, TOML configuration, readiness, provider selection, reconciliation, replacement, and runtime infrastructure policy; and `app/api/` defines stable capability-aware facades and shared transport substrate.
  - **Three-Feature Shared-Support Threshold**: A domain-level support folder or module is permitted only when at least three distinct registered features consume the same coherent capability. Count feature consumers, not import occurrences, composition wiring, package-root re-exports, or tests. Code used by one or two features remains inside one explicit owning feature; consumers depend on that owner rather than creating a horizontal catch-all. Registered standalone capabilities remain valid feature folders regardless of consumer count.
  - **Domain Persistence Support**: A persistent domain may define one documented non-feature `persistence/` support package containing exactly `__init__.py`, `create.py`, `read.py`, `update.py`, and `delete.py`. The package owns only domain-record CRUD statement construction, execution delegation through a Data-owned public capability resolved from `FeatureContext`, and normalized row handoff; authorization, validation, policy, orchestration, and public behavior remain in the owning feature modules. Classify atomic multi-statement operations by their domain effect and never split one transaction across CRUD files. Unsupported verbs retain an empty module. Immutable schema definitions remain in `migrations/`. `app/services/data/persistence/` is exempt from this five-file layout because it owns shared database connection, transaction, locking, migration-ledger, backup, and recovery infrastructure in addition to Data-owned CRUD.
    - If fewer than three registered features consume the persistence capability, put the same five-file package inside the owning feature folder instead of at the domain root.
    - Feature-owned immutable schema definitions live in that feature's `migrations/` package. A shared composition entry point may aggregate feature manifests without owning or altering their migration steps.
  - **Root-file Rule**: Except for explicitly allowed package infrastructure (`__init__.py`, `_settings.py`, `_limits.py`), production behavior must reside inside its owning feature module folder. A domain may impose a stricter root in its owning README; the API root permits only `__init__.py` as production Python, with bootstrap configuration and API-wide limits owned by `workstation/settings/`.
  - **Pure Initializers and Public Boundaries**: Every Python `__init__.py` is empty or contains only a module docstring. It performs no re-export, discovery, registration, I/O, task creation, connection, or logging configuration. Cross-feature and cross-domain consumers import DTOs, protocols, events, errors, and capability keys from `app.contracts.<owner>`, declare exact capability dependencies in `FeatureSpec`, and resolve providers through `FeatureContext`; they never import service implementations. Stable application callers use capability-aware facades under `app/api/` where applicable.
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
  - Modules that log use the standard-library pattern `logger = logging.getLogger(__name__)`; there is no shared logger singleton import. Composition owns application logging configuration, handlers, formatters, redaction, correlation context, retention, and cleanup. Log at workflow boundaries, public service entry points, external interactions, state transitions, side-effect boundaries, important decisions, retries, and failures. Pure helpers, DTOs/contracts, trivial accessors, deterministic transformations, and high-frequency numerical functions do not require logging unless specified. Logs must not expose secrets, credentials, personal information, full payloads, or sensitive trading data.
- **Imports**: Absolute imports, grouped (stdlib, 3rd-party, local).
- **Versioning**: Always confirm library versions before coding. Default to `pyproject.toml` pinned version.
- **Quality**: 80% `pytest` coverage minimum. No bare `except:`. Application and library code uses `logger`, never `print`. Directly executable teaching and usage-example scripts may use `print` to display bounded, secret-safe results. No silent failures.
- **Usage Evidence**: Every service feature designates one primary domain-logic module. Every core capability module documents its purpose, key capabilities, Python API usage, and executable module command; the primary module ends with a bounded, deterministic, secret-safe `if __name__ == "__main__":` harness that demonstrates the feature and fails nonzero when verification fails. The owning README maps applicable FRs to named harness scenarios. Usage examples never live under `tests/`. `FEAT-UI-*` features document bounded interactive workflows in their README and expose them through the running UI; automated UI tests verify but do not replace that usage documentation.
- **Test and Example Placement**: Feature-level automated tests live under `tests/services/<domain>/<feature>/`; system-level removability, dependency-graph, lifecycle, composition, API, and other verification suites retain their documented test locations. Tests verify behavior and never own public usage demonstrations. Provider-specific usage demonstrations live only in the provider feature's designated primary domain-logic module and use safe fakes, fixtures, sandbox/demo targets, or explicitly supplied safe inputs. No second example implementation is created.
- **Clean Resource Lifecycles**: Always close SQLite handles, open sockets, and background sub-processes explicitly in test teardown or context managers to eliminate `ResourceWarning` leaks.
- **Async Mocking Rigor**: Ensure mocks for asynchronous operations return genuine coroutines/futures (`async def`) to prevent unawaited coroutine warnings (`RuntimeWarning`).

## 3. Security

- **Secrets**: Never commit secrets. Redact sensitive values in logs. Use `.env.example` only.
- **Fail-Closed**: If policy is uncertain or evidence is missing, block the action.
- **No Live Action by Default**: Live trading, risk changes, and execution state mutations require explicit, deterministic approval. Real integration operations are permitted only against verified non-production targets (`ENVIRONMENT=dev`, demo/testnet/sandbox accounts), with one exception: MetaTrader 5 may connect to a live environment when the operator has elected `ACCOUNT_MODE=live` **and** supplied live MT5 credentials. A mode/credential mismatch fails closed rather than trading one environment under another's label. Every other provider remains non-production. Any attempt to touch or mutate production infrastructure is a blocking safety violation.
- **Kill Switch**: Deterministic. No caller can override or bypass a kill switch.
- **No Invented Data**: The system must never invent backtest results, live performance, or broker fills.
- **Deterministic Policy**: Python code is the sole policy-enforcement authority.
- **Credential Hygiene**: Ensure logging, exception payloads, and test outputs never capture plain-text API credentials, secret keys, JWT tokens, or account passwords.

## 4. Documentation

- **Update Rules**: Current domain features, statuses, semantic public contracts, requirements, database schema, prefix ownership, domain indexing policy, and target-vs-live reconciliation → the owning package `README.md`. Architecture, cross-domain models, universal database conventions, and shared storage policy → `docs/ARCHITECTURE.md`. System relationships and domain index → `docs/PROJECT.md`. Builder workflow → `AGENTS.md`. Delivery sequencing → `docs/dev/IMPLEMENTATION_ORDER.md`. Implemented feature procedure → `docs/dev/feature_implementation_pipeline.md`.
- **Schema Model Boundary**: Each owning package README's `### Persistence - Database` section is authoritative for that domain's current and target database model and authorises no migration. Executable schema remains in the owning domain's migration definitions. Where the model and an applied migration disagree, the migration is what the database contains and the README states what it should become.
- **Decision Hygiene**: `Open Decisions` sections in `docs/PROJECT.md` and domain/module READMEs contain unresolved owner choices only. When an owner resolves a choice, write the outcome as an ordinary requirement, contract, workflow, configuration rule, boundary, or explicit exclusion in the authoritative specification, then delete the decision row and any resolved issue entry. Do not retain resolved, superseded, retired, or deferred-from-initial-scope rows as decision history, and do not create ADR or other standalone decision-record documents.
- **Update Module/Service Documentation**: Add/update a `README.md` for each module/service as it's built.
- **Feature Specification Authority**: Every Python feature declares one immutable `SPEC: FeatureSpec` in `manifest.py` and registers a zero-argument factory through the `haruquantai.features` entry-point group. `FeatureSpec` is the implemented runtime authority for feature identity, domain, provided/required/optional capabilities, conflicts, state, and accepted configuration keys. The owning domain README remains the target product authority; the mandatory feature-local README and executable validator must match runtime truth. D-UI uses the typed `manifest.ts` variant documented in its owning README and the feature pipeline.
- **Checklist Evidence**: Every completed implementation-plan checklist item must end with the supporting code file path and line number.

## 5. Database Schema Rules

- **Authoritative Schema Manifest**: Database schema migrations are governed by authoritative domain migration manifests (e.g. `run_data_migrations`, `run_domain_migrations`).
- **Ledger Verification & Locks**: All database schema changes require initial ledger table verification, explicit database write lock acquisition, and checksum validation before applying steps.
- **Atomic Operations**: Database operations must be transactional (`execute_transaction`), with write lock leases and strict busy-timeout policies (`SQLITE_BUSY_TIMEOUT_SECONDS`).
- **Immutable Historical Steps**: Applied migration steps in the migration ledger are immutable; step checksum mismatches block database access to enforce schema integrity.
- **Migration Tombstones and Uninstall Retention**: Provider uninstallation is not data purging. When a provider is uninstalled or removed from runtime configuration, its historical migration entries remain immutable in the migration ledger to preserve database checksum integrity. Tables and records created by uninstalled providers are retained in a dormant state; destructive schema drop or table purge requires explicit, separate administrative authorization.

## 6. API Connection

- **Verified Upstream Contracts**: Use only verified upstream contracts and public dependency interfaces for external API connections.
- **Broker Session & Transport Isolation**: Broker connections must use dedicated session adapters (`_LazyBrokerSession`, transport circuit breakers) with deterministic retry and circuit recovery rules.
- **Credential & Readiness Verification**: Connection attempts must validate credential availability (`CREDENTIALS_MISSING`) and readiness state before opening external sockets.
- **Rate Limit & Circuit Governance**: API requests must respect declared source policy rate limits (`rate_limit`, `rate_window_seconds`) and circuit breaker state machines.
- **Circuit Recovery Testing**: Configure transport circuit breakers (`_TransportCircuitBreaker`) with micro-timeouts (e.g., `0.001s`) in tests to verify failover and recovery without thread-sleep pauses.

## 7. Integration

- **Environment Boundaries**: Real integration operations are permitted only against verified non-production targets (`ENVIRONMENT=dev`, demo/testnet/sandbox accounts), except for operator-elected live MetaTrader 5 as defined in §3.
- **Targeted Testing & Verification**: Development verification uses targeted test commands (`uv run pytest <test_file_path>`). Full test suites are restricted during iterative development to optimize time.
- **Safe Commands**: `pwd`, `ls`, `cat`, `grep`, `git status`, `git diff`, `uv run pytest <test_file_path>`, `uv run ruff check .`, `uv run mypy .`.
- **Restricted Commands (Require `APPROVED: EXECUTE`)**: `rm -rf`, `git reset`, `git clean`, `uv add`/`uv remove`, `docker compose`, live broker calls, real email/Telegram sends, destructive SQL.

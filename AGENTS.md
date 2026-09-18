# Standards and Principles

**Purpose:** Authoritative contributor and workflow constitution for HaruQuantAI (Generic Modular Monolith Architecture).

## 1. Core engineering principles

- **Repository truth, not chat memory.** Permanent truth lives in `AGENTS.md`, `docs/PROJECT.md`, `docs/ARCHITECTURE.md`, owning domain READMEs, and the Git-tracked code and tests. Conversation history is useful context but is never authoritative.
- **Scoped authority.**
  - `AGENTS.md` owns contributor, task workflow, and verification rules.
  - `docs/PROJECT.md` owns product scope, domain index, functional requirements, and NFRs.
  - `docs/ARCHITECTURE.md` owns universal structural, lifecycle, persistence, and runtime constraints.
  - `docs/dev/feature_implementation_pipeline.md` and `docs/dev/domain_implementation_audit.md` own authoritative build-side feature implementation rules (`FIP-01` through `FIP-26`) and verification criteria.
  - `docs/templates/` owns canonical task operational templates (`implementation-plan.md`, `walkthrough.md`).
  - Owning domain READMEs own current-state feature registries, state declarations, and requirement mappings.
  Satisfy all non-overlapping authorities and report real conflicts before editing.
- **Think first.** State assumptions, boundaries, trade-offs, validation, and rollback before coding. Never silently resolve missing requirements.
- **Surgical changes.** Implement the minimum complete change. No speculative features, unrelated refactors, or scope expansion.
- **Correctness over speed.** Verify with tools and repository evidence; never invent behavior, tests, results, or upstream contracts.
- **SOLID/focused ownership.** One feature owns one coherent capability. Single-file domain modules (`app/services/<domain>/<feature>.py`) own one feature; classes and functions stay focused on one responsibility.
- **Pure architectural boundaries.** Python `__init__.py` files are empty or docstring-only. Cross-boundary collaboration uses typed capability tokens and public contracts in `app/contracts/<domain>.py` resolved via `FeatureContext`, never private service imports.
- **Managed side effects.** Features use lifecycle-owned resources and `FeatureScope`/`FeatureContext` facilities for background tasks, subscriptions, capabilities, and cleanup.
- **Standard-library kernel.** `app/kernel/` relies exclusively on the Python standard library with zero third-party dependencies.

---

## 2. Streamlined Task Workflow (Plan -> Execute -> Walkthrough)

Every development task follows a disciplined, transparent, and reviewable workflow structured around two standard operational artifacts:
1. **Implementation Plan** (`docs/templates/implementation-plan.md`) - Created before touching code.
2. **Walkthrough** (`docs/templates/walkthrough.md`) - Created after implementation and verification are complete.

```text
Task Request
  ↓
1. Research & Audit (inspect repository truth, read active code/contracts; zero speculative edits)
  ↓
2. Implementation Plan (author plan adhering strictly to docs/templates/implementation-plan.md)
  ↓
3. Owner Approval Gate (stop and wait for explicit confirmation: "APPROVED: EXECUTE")
  ↓
4. Surgical Implementation & Verification (code within ALLOWED_WRITE_PATHS; pytest, mypy, ruff, AST checks)
  ↓
5. Walkthrough (document changes, verification results, and usage evidence via docs/templates/walkthrough.md)
  ↓
6. Owner Commit Gate (user reviews walkthrough and authorizes git commit)
  ↓
Task Completed
```

### 2.1 Research & Audit (Think First)

- Read all relevant existing files, contracts, registry entries, and tests to ground the plan in repository truth.
- Identify all dependencies, affected scopes, and potential side effects.
- DO NOT make source code changes or run modifying commands during research.

### 2.2 Implementation Plan Creation

- Author a comprehensive Implementation Plan adhering strictly to [docs/templates/implementation-plan.md](docs/templates/implementation-plan.md).
- Fulfill all 8 canonical sections: `Goal & Requirements`, `Files Read / Audit Trail`, `Proposed Changes & Implementation Order` (with clickable links and action tags), `Dependencies & Contracts`, `Blockers & Risks`, `Scope Boundaries`, `Verification Plan`, and `Rollback & Contingency` (defining `ALLOWED_WRITE_PATHS`).
- Highlight critical items under `### User Review Required` and record any open questions under `### Open Questions`.

### 2.3 User Approval Gate

- Present the plan to the user/owner.
- **STOP and wait for explicit approval** before proceeding to execution. Work commences only after receiving explicit owner confirmation (e.g. `APPROVED: EXECUTE`).

### 2.4 Surgical Implementation & Verification

- Implement strictly within the approved `ALLOWED_WRITE_PATHS` and sequential implementation order.
- Follow the authoritative build procedure in [docs/dev/feature_implementation_pipeline.md](docs/dev/feature_implementation_pipeline.md).
- Follow change-scoped testing during development (`uv run pytest --no-cov <affected_tests>`).
- Maintain or add a dedicated, self-contained offline usage example in `tests/examples/<domain_file>.py`.
- Verify the full qualification suite before finalizing:
  ```bash
  uv run python scripts/ci_check.py
  ```

### 2.5 Walkthrough & Delivery

- Once implementation and validation are fully verified, author a post-implementation Walkthrough adhering strictly to [docs/templates/walkthrough.md](docs/templates/walkthrough.md).
- Document:
  1. `Summary of Changes Made` with clickable file links.
  2. `Verification Results` with commands and outputs for unit tests, usage examples, and `scripts/ci_check.py`.
  3. `Deviations & Residuals` detailing any approved plan deviations, clean working tree status (`git status`), and proposed commit message.
- Present the walkthrough to the user/owner for final review and commit authorization.

---

## 3. Coding Style and Verification

All code implementation, module anatomy, imports, logging, docstrings, typing, persistence boundaries, and test obligations are authoritatively governed by [docs/dev/feature_implementation_pipeline.md](docs/dev/feature_implementation_pipeline.md) (controls `FIP-01` through `FIP-26`) and audited via [docs/dev/domain_implementation_audit.md](docs/dev/domain_implementation_audit.md).

### Non-negotiable verification baseline:

- **Formatting & Linting:** Strict adherence to the Google Python Style Guide via Ruff (`ruff format` with 4 spaces, 88-character line length; `ruff check` enforcing 50+ rule groups).
- **Static Typing:** Mypy strict mode (`strict = true`) with advanced error codes enabled (`deprecated`, `explicit-override`, `truthy-bool`). Explicit type hints on all signatures.
- **Google Docstrings:** Every module, class, public method, and non-obvious function has a fitted Google-style docstring (`Args`, `Returns`, `Raises` only when applicable).
- **Structured Logging:** Import `get_logger` from `app.kernel.logging` (`logger = get_logger(__name__)`). Bounded structured fields, strict secret/token/path redaction, and zero global logging configuration in service modules.
- **Quality & Coverage:** Minimum 80% pytest coverage floor across `app`. No bare `except:`, no silent failures, and no application `print`.
- **Usage Evidence:** Every backend feature must have a dedicated, self-contained offline scenario in `tests/examples/` exercising its primary purpose with deterministic, secret-safe inputs.
- **Architectural Boundary Linter:** `uv run python scripts/architecture_check.py` verifies boundary isolation, imports purity, and docstring-only `__init__.py` files.

### Testing Cadence Boundaries

- **Editing & Iteration (Focused Only):** Run **ONLY** behavior-specific tests for changed or directly affected files with explicit paths and no coverage:
  ```bash
  uv run pytest --no-cov tests/path/to/test_feature.py
  ```
  **Never run unfiltered full test suites or coverage calculations iteratively on every edit.**
- **Candidate Verification & Pre-Push:** The complete repository test suite, full Mypy checks, and the 80% coverage floor calculation are executed **only** after implementation is complete to qualify the candidate before commit/push via the unified check runner:
  ```bash
  uv run python scripts/ci_check.py
  ```

---

## 4. Security and Operational Safety

- **Zero Secrets:** Never commit credentials, API keys, private tokens, or sensitive configuration. Keep `.secrets.baseline` up to date via `detect-secrets`.
- **Fail Closed:** Fail closed whenever authority, policy, credentials, environment, or evidence is ambiguous or uncertain.
- **Destructive Action Guard:** Deleting database files, dropping tables, purging data, force-pushing, or running uncontained external mutations requires explicit owner authorization.
- **Authoritative Controls:** Python code and runtime policy enforcement are authoritative; chat memory and prompt guidance are never substitutes for deterministic verification.

---

## 5. Database and External API Rules

- **Database Preservation:** Never delete, unlink, truncate, reset, or drop tables in active workspace databases. Tests, benchmarks, and example harnesses must strictly execute against isolated temporary databases (e.g. via `tmp_path`).
- **Persistence Boundary:** Database schemas, parameterized SQL, and transactions belong strictly in `app/services/persistence/<domain>.py` (`FIP-14 PERSIST`). Feature modules never execute ad-hoc SQL or manipulate raw connections.
- **External Integration Isolation:** External services (HTTP clients, third-party APIs, messaging brokers) must be encapsulated behind typed protocols and capabilities in `app/contracts/` with explicit timeouts, retries, and circuit breakers.

---

## 6. Git Authority Summary

- The user/owner retains exclusive authority over Git commits, branch merges, and remote repository operations.
- The assistant operates locally within the current workspace, proposing diffs, running tests, and preparing commit summaries.
- No unsolicited branch creation, rebase, force-push, history rewrite, or destructive repository modifications are permitted without explicit owner direction.

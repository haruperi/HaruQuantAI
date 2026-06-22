# Instructions

**Purpose**: Single AI/Builder operating guide for HaruQuantAI.

## 1. Mindset & Core Directives

- **Memory & Truth**: Memory lives in repo files (`AGENTS.md`, `docs/ARCHITECTURE.md`, `CHANGELOG.md`), **never in chat**. Read these before acting. Authority: Owner -> `AGENTS.md` -> `ARCHITECTURE.md` -> `CHANGELOG.md`.
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
- **Final Report**: After any task, report files changed, decisions/risks updated, commands run, validation results, and rollback path. Use positive checklist wording (e.g., `[X] Scope followed`) Also if a checklist exist for the task, update it with a [X] or [ ] before the response.

## 4. Code Quality & Python Style

**Strict adherence to [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html).**

- **Format**: 80 char line limit, 4 spaces. Pre-commit order: `trailing-whitespace` → `end-of-file-fixer` → `check-yaml/toml` → `check-added-large-files` → `detect-secrets` → `ruff` → `ruff-format` → `mypy --strict` → `pytest`.
- **Typing & Docs**: `mypy --strict`. Explicit type hints on all signatures. Google-style docstrings for all modules, classes, and functions.
- **Imports**: Absolute imports, grouped (stdlib, 3rd-party, local).
- **Versioning**: Always confirm library versions before coding. Default to `pyproject.toml` pinned version.
- **Quality**: 80% `pytest` coverage minimum. No bare `except:`. Use `logger` (no `print`). No silent failures.
- **Security**: Never commit secrets. Redact sensitive values in logs. `.env.example` only.

## 5. Architecture Standards

### Tools (`agentic/tools/`)

- **Imports**: Import from domain (`from agentic.tools.data import ...`), never deep paths.
- **Structure**: Must include metadata (`TOOL_NAME`, `TOOL_RISK_LEVEL`, etc.). Accept `request_id: str | None = None`. Validate inputs first.
- **Return Schema**: Tools must **never** return `None` or raw exceptions. Always return:
  ```json
  {"status": "success|error", "message": str, "data": any, "error": null|{"code": "ERROR_CODE", "details": str}, "metadata": {"tool_name": str, "tool_version": str, "tool_category": str, "tool_risk_level": "low|medium|high|critical", "request_id": str|null, "execution_ms": float, "reads": bool, "writes": bool, "updates": bool, "deletes": bool, "trades": bool, "requires_network": bool}}
  ```
- **Error Codes**: `INVALID_INPUT`, `PERMISSION_DENIED`, `DATA_NOT_FOUND`, `EMPTY_RESULT`, `SERVICE_UNAVAILABLE`, `BROKER_UNAVAILABLE`, `DATABASE_ERROR`, `NETWORK_ERROR`, `TIMEOUT`, `VALIDATION_FAILED`, `TOOL_EXECUTION_FAILED`, `UNKNOWN_ERROR`.

### Agents (agentic/agents/)

- **Design**: Few agents, many tools. If it fetches/calculates/validates → Tool. If it decides/interprets/plans → Agent.
- **Structure**: Must include metadata (`AGENT_NAME`, `AGENT_RISK_LEVEL`, permissions, `ALLOWED_TOOLS`). Instruction must contain 10 sections (Role, Responsibilities, Non-Goals, Allowed Tools, Blocked Actions, Required Evidence, Output Contract, Safety Rules, Uncertainty Behavior, Escalation Rules).
- **Return Schema**: Normalize all outputs to:
  ```json
  {"status": "success|error", "message": str, "data": any, "error": null|{"code": "ERROR_CODE", "details": str}, "metadata": {"agent_name": str, "agent_version": str, "agent_category": str, "agent_risk_level": "low|medium|high|critical", "request_id": str|null, "execution_ms": float, "reads": bool, "writes": bool, "updates": bool, "deletes": bool, "trades": bool, "requires_network": bool}}
  ```
- **Error Codes**: `INVALID_INPUT`, `MISSING_EVIDENCE`, `STALE_EVIDENCE`, `CONFLICTING_EVIDENCE`, `TOOL_FAILURE`, `POLICY_BLOCKED`, `PERMISSION_DENIED`, `APPROVAL_REQUIRED`, `OUTPUT_CONTRACT_FAILED`, `AGENT_EXECUTION_FAILED`.

## 5. Safety & Governance

- **Fail-Closed**: If policy is uncertain or evidence is missing, block the action.
- **No Live Action by Default**: Live trading, risk changes, and execution state mutations require explicit, deterministic approval.
- **Kill Switch**: Deterministic. An LLM cannot override or bypass a kill switch.
- **No Invented Data**: Agents must never invent backtest results, live performance, or broker fills.
- **Deterministic Policy**: LLMs explain policy; Python code (agentic/policy.py) enforces it.

## 6. Documentation & Commands

- **Update Rules**: Architecture/API/models → docs/ARCHITECTURE.md. Sprint state/decisions → CHANGELOG.md. AI workflow → AGENTS.md.
- **Safe Commands**: `pwd`, `ls`, `cat`, `grep`, `git status`, `git diff`, `pytest`, `ruff check .`, `mypy .`
- **Restricted Commands (Require APPROVED: EXECUTE)**: `rm -rf`, `git reset`, `git clean`, `pip install`, `npm install`, `docker compose`, live broker calls, real email/Telegram sends, destructive SQL.

## 7. Final Checklist (Must be satisfied before finishing)

- **Scope strictly followed**.
- **Required docs read; no rules invented**.
- **Code quality (Google style, types, docstrings, logging, 80% coverage) applied**.
- **Tools/Agents follow compressed standards (schemas, metadata, imports)**.
- **No secrets or live side effects introduced**.
- **Affected active docs updated**.
- **Validation/tests run and passed**.
- **Rollback path identified and reported**.

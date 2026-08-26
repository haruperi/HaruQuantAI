# Standards and Principles

**Purpose:** Authoritative shared contributor and workflow constitution for HaruQuantAI.

## 1. Core engineering principles

- **Repository truth, not chat memory.** Permanent truth lives in `AGENTS.md`, `docs/PROJECT.md`, `docs/ARCHITECTURE.md`, and owning package READMEs. Temporary active-task coordination lives only in `.agents/task/`. Conversation history is useful context but is never authoritative.
- **Scoped authority.** `AGENTS.md` owns shared contributor and workflow rules; `docs/PROJECT.md` owns product/system scope and cross-domain relationships; `docs/ARCHITECTURE.md` owns universal structural/runtime constraints; each owning package README is the canonical current-state feature/FR registry for that package. Satisfy all non-overlapping authorities and report real conflicts before editing.
- **Think first.** State assumptions, boundaries, trade-offs, validation, and rollback before coding. Never silently resolve missing requirements.
- **Surgical changes.** Implement the minimum complete change. No speculative features, unrelated refactors, or scope expansion.
- **Correctness over speed.** Verify with tools and repository evidence; never invent behavior, tests, results, or upstream contracts.
- **SOLID/focused ownership.** One feature owns one coherent capability. One module folder owns one feature/capability; files and classes/functions stay focused on one responsibility. Shared support exists only under documented exceptions and must not become a second feature registry or implementation location.
- **Pure boundaries.** Python `__init__.py` files are empty or docstring-only. Cross-feature/domain collaboration uses public contracts/capabilities, not private service imports. Import-time registration/I/O/task creation/logging configuration is forbidden.
- **Managed side effects.** Features use lifecycle-owned resources and `FeatureContext`/scope facilities for managed tasks, subscriptions, capabilities, and cleanup. Service packages do not configure global logging.
- **Test performance.** Unit tests should avoid real network/database sleeps; mock or isolate I/O when a unit test exceeds roughly 100 ms.
- **Document non-obvious assumptions.** Numeric thresholds, domain assumptions, boundary conditions, and policy decisions require concise source documentation.

### Focused domain architecture

- Production service behavior belongs in `app/services/<domain>/<feature>/` unless an owning README documents an explicit support-package exception.
- Cross-boundary DTOs, protocols, events, errors, and capability keys live in `app/contracts/`; business-neutral lifecycle/composition primitives live in `app/kernel/` and `app/composition/` according to `docs/ARCHITECTURE.md`.
- A feature never imports another feature implementation. Consumers declare exact capability dependencies and resolve providers through `FeatureContext`.
- A domain-level shared support capability is permitted only when at least three registered features genuinely consume the same coherent capability, unless another explicit architecture exception applies.
- Persistent domains may use the documented persistence/migration conventions in the owning README and architecture guide; persistence support never absorbs authorization, policy, orchestration, or feature semantics.
- D-UI follows its own owning README: registered `FEAT-UI-*` capabilities own widgets; widgets never have multiple feature owners; shared UI support folders do not become product-policy owners.

## 2. Three-role development workflow

The workflow is **Planner → Executor → Reviewer**. `.agents/protocol.toml` is the machine-readable transition contract. Canonical role prompts live in `docs/templates/prompt/`; `.agents/task/next-agent.md` is the complete instantiated prompt for the next reasoning role.

**Role-invocation invariant:** no Planner, Executor, or Reviewer invocation may occur unless its complete prompt already exists in `.agents/task/next-agent.md` and has passed protocol validation. This includes the initial Planner invocation after task activation and every same-role resumed iteration.

### 2.1 Active-task workspace

Tracked files:

```text
.agents/task/
├── planner.md
├── executor.md
├── reviewer.md
└── next-agent.md
```

Rules:

- `planner.md`, `executor.md`, and `reviewer.md` are append-only during an active task and written only by their owning role, except for the narrow deterministic owner-gate record described below.
- `next-agent.md` is replace-only. Before every reasoning-role invocation it contains exactly one complete standalone prompt for that role.
- All four files are zero bytes when no task is active and after accepted close-out.
- They are coordination artifacts, not product specifications, feature registries, permanent decision history, or session storage.
- Every non-terminal journal handoff must agree with a valid `next-agent.md`; missing, stale, contradictory, or partially instantiated prompts fail closed.
- Native CLI session IDs are runtime-only transport state and must never appear in `next-agent.md`.

### 2.2 Role declaration and single writer

Every development agent invocation has exactly one role: `PLANNER`, `EXECUTOR`, or `REVIEWER`. Only one role writes at a time. Roles never run concurrently on the same task branch. A role stops if its authority conflicts with the active handoff.

The orchestrator is not a fourth reasoning role. It may only perform deterministic lifecycle actions, routing/validation, transport/session bookkeeping, and deterministic owner-gate bookkeeping. It never authors planning, implementation, or review conclusions.

### 2.3 Task activation and branch isolation

- A task specification does not activate work merely by existing on disk.
- Every new task begins from a clean `main` entry gate and recorded baseline HEAD.
- Registered features use `feature/<feature-id>-<slug>`; other tasks use `task/<task-id>-<slug>`. Names are lowercase filesystem-safe refs and must pass `git check-ref-format --branch`.
- During `ORCHESTRATOR / TASK_ACTIVATED`, the orchestrator deterministically derives, validates, creates, and switches to exactly one task branch from the recorded baseline.
- After branch creation, the orchestrator instantiates the canonical Planner prompt into `.agents/task/next-agent.md`, validates the full `TASK_ACTIVATED -> PLANNER` artifact, and only then may Planner run.
- Planner verifies but never creates or switches the task branch.
- Planner, Executor, and Reviewer work sequentially on that branch until authorized close-out.
- `main` remains clean and unchanged throughout planning/execution/review.
- Every dry run/report/review records task ID, iteration, baseline, task branch, and expected changed/untracked paths.

### 2.4 State machine and owner gates

Session/task path:

```text
ORCHESTRATOR READY / TASK NONE
  → task specification prepared
  → ORCHESTRATOR: TASK_ACTIVATED
  → deterministic task branch creation
  → initial Planner prompt materialized + validated in next-agent.md
  → Planner Dry Run N
  → PENDING_APPROVAL
  → owner: APPROVED: EXECUTE
  → Executor Report N
  → READY_FOR_REVIEW
  → Reviewer Review N
  → PENDING_COMMIT
  → owner: APPROVED: COMMIT
  → Reviewer close-out
  → ACCEPTED
  → ORCHESTRATOR READY / TASK NONE
```

Correction paths:

- Executor `BLOCKED` → next Planner dry run in the same Planner role conversation for this run.
- Reviewer `CHANGES_REQUESTED` → next Planner dry run in the same Planner role conversation for this run.
- Owner rejection of execution or commit gate → next Planner dry run with the owner direction.
- Planner `BLOCKED` → owner resolves the documented cause; Planner resumes its same role conversation with a fresh canonical prompt.
- Planner blocker resolution replaces the stale retry artifact with a fresh canonical `ORCHESTRATOR / BLOCKER_RESOLVED → PLANNER` prompt fingerprinted against the resolved repository state.
- Owner cancellation records terminal `CANCELLED` state and preserves the task branch, worktree, journals, run evidence, and role-session evidence for deliberate recovery.

Execution authorization is valid only when the entire trimmed owner message is exactly `APPROVED: EXECUTE`. Commit authorization is valid only when it is exactly `APPROVED: COMMIT`.

**Deterministic owner-gate exception:** after exact `APPROVED: EXECUTE`, the orchestrator may append a factual gate record to `.agents/task/planner.md` containing the task, iteration, baseline, branch, and approved plan SHA-256. It may not alter the dry-run body. Planner is not re-invoked merely to transcribe owner authorization.

The approved plan SHA-256 is computed from the exact bytes of `planner.md` immediately before the current owner-gate marker is appended. The orchestrator independently verifies those bytes and all gate identity fields before Executor and Reviewer invocation.

### 2.5 `next-agent.md` as the role boundary

Every reasoning-role prompt begins with TOML front matter using prompt schema version 1. It records run/task/iteration, source/target role, handoff, branch, baseline, source HEAD, canonical template path, and owner-gate requirement.

The initial Planner artifact uses `source_role="ORCHESTRATOR"`, `handoff="TASK_ACTIVATED"`, `target_role="PLANNER"`, and the canonical Planner template. All later role transitions use the same metadata contract.

The orchestrator validates:

- protocol transition and target role/template;
- schema/version and required metadata;
- branch, baseline, and source HEAD;
- canonical incoming-role authority sentinels;
- no unfilled `{{placeholders}}`;
- prompt SHA-256 and canonical template SHA-256;
- complete working-tree fingerprint for protected pending artifacts.

Outgoing roles populate task-specific context and structured handoff facts. They may **not** weaken or rewrite the incoming role's canonical role, authority, methodology, quality criteria, or handoff contract.

Free-form `NEXT AGENT NOTES` are not part of the protocol.

### 2.6 Structured handoff facts

- **Planner → Executor:** approved scope, exact path authority, implementation order, requirements, validation, rollback, risks.
- **Executor → Reviewer:** changed paths, requirements claimed complete, commands/tests reported, limitations, deviations, assumptions, risks. These claims are explicitly labeled `UPSTREAM CLAIMS — UNTRUSTED UNTIL INDEPENDENTLY VERIFIED`.
- **Executor → Planner (`BLOCKED`):** blocker, evidence, partial-work state, affected paths, safe retained work/rollback, and exact decision required.
- **Reviewer → Planner:** failed requirement/gate, independent evidence, required correction, valid retained work, and scope requiring reconsideration.

### 2.7 Canonical professional role contracts

`AGENTS.md` defines shared repository-wide law; it does **not** duplicate individual job descriptions. Each canonical template is the complete role-specific contract that is instantiated into `next-agent.md`:

| Protocol role | Professional role contract | Canonical template |
| --- | --- | --- |
| `PLANNER` | Principal Software Architect and Implementation Planner | `docs/templates/prompt/planner.md` |
| `EXECUTOR` | Senior Software Implementation Engineer | `docs/templates/prompt/executor.md` |
| `REVIEWER` | Principal Software Verification and Code Review Engineer | `docs/templates/prompt/reviewer.md` |
| `REVIEWER` close-out | Release Integrity and Change-Control Engineer | `docs/templates/prompt/reviewer-closeout.md` |

The templates own role-specific perspective, responsibilities, allowed writes, forbidden behavior, methodology, quality criteria, and handoff behavior. `AGENTS.md` remains binding for shared repository authority, architecture, safety, quality, contribution, Git, state-machine, and transport rules.

### 2.8 Role Session Continuity

**Cross-role isolation and same-role continuity are independent properties.** Every workflow run owns one logical conversation for Planner, one for Executor, and one for Reviewer. Repeated iterations resume that exact same-role conversation; Reviewer close-out continues the same Reviewer conversation. A new workflow run starts new role conversations.

```text
Planner 1 → Planner 2 → Planner 3
Executor 1 → Executor 2 → Executor 3
Reviewer 1 → Reviewer 2 → Reviewer 3 → Reviewer close-out

Planner session ≠ Executor session ≠ Reviewer session
```

Session history is context only. Authority order remains: repository evidence and deterministic Python workflow state, then the current validated `next-agent.md` role/task contract. Remembered conversation context never overrides them.

Mode semantics:

- `solo`: one physical chat; same-role continuity is inherent and cross-role isolation is soft only. Every role boundary reloads the complete current `next-agent.md`.
- `delegate`: one persistent same-brand delegate handle per role per workflow run. Later iterations resume the same role delegate when the host exposes resumable handles; lack of required resume capability must be reported rather than silently pretending a fresh delegate is continuous.
- `multi-delegate`: each turn may launch a fresh OS process, but the process resumes the exact stored native conversation ID for that role. IDs live under `.agents/runs/<run-id>/role-sessions.json`, never in task prompts. Never use implicit "last session" selection when an exact ID exists. Returned resume identity must match the stored ID or execution fails closed.
- `manual`: the operator keeps four chats for the run — Orchestrator, Planner, Executor, Reviewer — and returns to the same role chat on later iterations. Reviewer close-out returns to the existing Reviewer chat.

Mode changes transport and transport automation only. Role identity, role continuity, current prompt contract, authority, state transitions, iteration semantics, and handoff semantics remain consistent.

## 3. Coding style and verification

- Follow the Google Python Style Guide and repository Ruff configuration. Use 4-space indentation and `ruff format`.
- Public/module code uses explicit typing and appropriate Google-style docstrings. Run configured mypy strict checks for applicable code.
- No bare `except:` and no silent failures.
- Application/library code uses `logging.getLogger(__name__)`, not `print`; bounded executable teaching/usage harnesses may print secret-safe results.
- Do not log secrets, credentials, personal information, full sensitive payloads, or trading account data.
- Every service feature has one designated primary domain-logic module with bounded executable usage evidence. Tests verify behavior but do not become a second usage implementation.
- Feature-level tests belong under the owning test namespace; system architecture/composition/removability tests remain in their documented locations.
- Close SQLite handles, sockets, files, and subprocesses explicitly. Async mocks must return genuine awaitables.

### Change-scoped testing

During implementation/review, derive the affected set from `git diff --name-only`, staged diff, and untracked paths. Map changed production code to owning and affected contract/consumer/architecture tests.

Run bounded tests explicitly, e.g. `uv run pytest --no-cov <selected paths>`. Never run bare/unfiltered pytest or coverage iteratively. Coverage and the complete suite are final integration evidence through the configured pre-commit/CI gates.

Safe read/verification commands include `pwd`, `ls`, `cat`, `grep`, `git status`, `git diff`, bounded pytest, Ruff, and mypy. Destructive commands and live external actions require explicit applicable authorization.

## 4. Security and operational safety

- Never commit secrets; use `.env.example` for examples and redact sensitive outputs.
- Fail closed when policy, authority, credentials, environment, or evidence is uncertain.
- No live trading/action by default. External integration operations use verified dev/demo/testnet/sandbox targets unless an owning policy explicitly permits an operator-selected live mode (including the documented MT5 exception).
- Kill switches and deterministic risk/policy gates cannot be bypassed by callers or agents.
- Never invent backtest results, live performance, broker fills, or external data.
- Python/runtime policy enforcement is authoritative; LLM prompts and remembered session context are not substitutes for deterministic controls.

## 5. Documentation and ownership

- Owning package README: domain feature/FR registry, current feature status, semantic contracts, persistence target model, usage/evidence mapping.
- `docs/ARCHITECTURE.md`: universal structural/runtime/database conventions.
- `docs/PROJECT.md`: product/system scope, domain index, cross-domain relationships and NFRs.
- `AGENTS.md`: shared contributor/workflow constitution.
- `docs/dev/IMPLEMENTATION_ORDER.md`: delivery sequencing.
- `docs/dev/feature_implementation_pipeline.md`: feature delivery architecture/checklist.
- `docs/templates/prompt/`: complete canonical role-specific workflow contracts.

Planner identifies documentation impact; Executor applies only approved documentation changes; Reviewer verifies consistency and reports discrepancies without fixing them.

Resolved decisions become ordinary requirements/boundaries in the owning authority; do not accumulate superseded decision history as a second source of truth.

## 6. Database and external API rules

- Applied migration steps/checksums are immutable. Schema changes follow owning migration manifests, explicit write locks, ledger verification, and transactional execution.
- Provider uninstall/removal does not imply destructive data purge; retention/purge follows explicit owning policy and separate authorization.
- External APIs use verified public upstream contracts, credential/readiness checks, bounded rate limits, retries/circuit breakers, and deterministic recovery tests.
- Broker/provider implementations stay isolated behind public contracts/capabilities; consumers do not import provider internals.

## 7. Git authority summary

- Orchestrator: deterministic clean-main entry gate + one task-branch creation/switch during `TASK_ACTIVATED`; no reasoning conclusions, commits, merge, or push.
- Planner: no branch creation/switch and no commits/merge/push.
- Executor: no branch creation/switch, commits/merge/push.
- Reviewer: one authorized local task commit + ff-only local merge + safe merged-branch deletion only after `APPROVED: COMMIT` and only when the latest approved scope includes close-out.
- Normal workflow never authorizes push, force-push, pull, fetch, rebase, reset, clean, amend, force deletion, merge-conflict resolution, or destructive abandonment. Such actions require separate explicit applicable owner authorization.
- `APPROVED: EXECUTE` approves only the latest dry run. It never authorizes unrelated findings/refactors/dependency upgrades/history rewrites/live actions.

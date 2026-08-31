# Standards and Principles

**Purpose:** Authoritative shared contributor and workflow constitution for HaruQuantAI.

## 1. Core engineering principles

- **Repository truth, not chat memory.** Permanent truth lives in `AGENTS.md`, `docs/PROJECT.md`, `docs/ARCHITECTURE.md`, and owning package READMEs. Temporary active-task coordination lives only in `.agents/task/`. Conversation history is useful context but is never authoritative.
- **Scoped authority.** `AGENTS.md` owns shared contributor and workflow rules; `docs/PROJECT.md` owns product/system scope and cross-domain relationships; `docs/ARCHITECTURE.md` owns universal structural/runtime constraints; each owning package README is the canonical current-state feature/FR registry for that package. Satisfy all non-overlapping authorities and report real conflicts before editing.
- **Donor evidence is optional, never authoritative.** Legacy donor material may inform implementation only when an approved normalized bundle is available. Its absence alone is not a blocker: implement the complete ratified V3 scope from the owning README and public contracts from scratch, do not substitute raw `.migration` staging, do not claim unverified donor parity, and record the evidence limitation truthfully in the legacy ledger.
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

## 2. Atomic Task workflow

The atomic development workflow is **Planner → Executor → Reviewer**. `.agents/protocol.toml` is the machine-readable Task transition contract. Canonical role prompts live in `docs/templates/prompt/`; `.agents/task/next-agent.md` is the complete instantiated prompt for the next reasoning role.

A **Task** is the smallest coherent implementation unit that should receive its own planning, implementation, independent review, branch and Git commit. Planner phases/tasks are subdivisions inside one Task; they are not separate workflow runs.

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

- `planner.md`, `executor.md`, and `reviewer.md` are append-only during an active Task and written only by their owning role, except for the narrow deterministic owner-gate record described below.
- `next-agent.md` is replace-only. Before every reasoning-role invocation it contains exactly one complete standalone prompt for that role.
- All four files are zero bytes when no Task is active and after accepted close-out.
- They are coordination artifacts, not product specifications, feature registries, permanent decision history, Goal state, or session storage.
- Every non-terminal journal handoff must agree with a valid `next-agent.md`; missing, stale, contradictory, or partially instantiated prompts fail closed.
- Native CLI session IDs are runtime-only transport state and must never appear in `next-agent.md`.

### 2.2 Role declaration and single writer

Every reasoning invocation has exactly one role: `PLANNER`, `EXECUTOR`, or `REVIEWER`. Only one role writes at a time. Roles never run concurrently on the same Task branch. A role stops if its authority conflicts with the active handoff.

The orchestrator is not a reasoning role. It may only perform deterministic lifecycle actions, routing/validation, transport/session bookkeeping, Goal supervision, and deterministic owner-gate bookkeeping. It never authors planning, implementation, or review conclusions.

### 2.3 Task activation and branch isolation

- A Task specification does not activate work merely by existing on disk.
- Every new Task begins from a clean `main` entry gate and recorded baseline HEAD.
- Registered features use `feature/<feature-id>-<slug>`; other Tasks use `task/<task-id>-<slug>`. Names are lowercase filesystem-safe refs and must pass `git check-ref-format --branch`.
- During `ORCHESTRATOR / TASK_ACTIVATED`, the orchestrator derives, validates, creates, and switches to exactly one Task branch from the recorded baseline.
- After branch creation, the orchestrator instantiates the canonical Planner prompt into `.agents/task/next-agent.md`, validates the full `TASK_ACTIVATED -> PLANNER` artifact, and only then may Planner run.
- Planner verifies but never creates or switches the Task branch.
- Planner, Executor, and Reviewer work sequentially on that branch until authorized close-out.
- `main` remains clean and unchanged throughout planning/execution/review.
- Every dry run/report/review records Task ID, iteration, baseline, Task branch, and expected changed/untracked paths.

### 2.4 Task state machine and owner gates

```text
ORCHESTRATOR READY / TASK NONE
  → Task specification prepared
  → ORCHESTRATOR: TASK_ACTIVATED
  → Task branch creation
  → Planner Dry Run N
  → PENDING_APPROVAL
  → execute gate: exact owner message or frozen run preauthorization
  → Executor Report N
  → READY_FOR_REVIEW
  → Reviewer Review N
  → PENDING_COMMIT
  → commit gate: exact owner message or frozen run preauthorization
  → Reviewer close-out
  → ACCEPTED
  → ORCHESTRATOR READY / TASK NONE
```

Correction paths:

- Executor `BLOCKED` → next Planner dry run in the same Planner role conversation for this Task run.
- Reviewer `CHANGES_REQUESTED` → next Planner dry run in the same Planner role conversation for this Task run.
- Owner rejection of execution or commit gate → next Planner dry run with the owner direction.
- Planner `BLOCKED` → owner resolves the documented cause; Planner resumes its same role conversation with a fresh canonical prompt.
- Planner blocker resolution replaces the stale retry artifact with a fresh canonical `ORCHESTRATOR / BLOCKER_RESOLVED → PLANNER` prompt fingerprinted against the resolved repository state.
- Owner cancellation records terminal `CANCELLED` state and preserves Task branch, worktree, journals, run evidence, and role-session evidence.

In `approval_policy = "interactive"`, execution authorization is valid only when the entire trimmed owner message is exactly `APPROVED: EXECUTE`, and commit authorization is valid only when it is exactly `APPROVED: COMMIT`. In `approval_policy = "unattended"`, those same protocol gates may instead be satisfied by `RUN_PREAUTHORIZATION` frozen from schema-v3 `.agents/run-config.toml` at run activation. Execute requires `allow_execute`; close-out requires both `allow_local_commit` and `allow_local_merge`. A preauthorization record must state its true source plus the frozen policy and scope SHA-256 values and must never claim that a human sent an approval message.

After either valid execute-gate source, the orchestrator may append only the deterministic factual gate record to Planner journal. The approved plan SHA-256 is computed from exact pre-gate Planner bytes and independently verified before Executor/Reviewer invocation.

### 2.5 `next-agent.md` as role boundary

Every reasoning-role prompt begins with TOML front matter using prompt schema version 1 and records run/task/iteration, source/target role, handoff, branch, baseline, source HEAD, canonical template path, and owner-gate requirement.

The orchestrator validates transition/template, schema, branch/baseline/HEAD, protected incoming-role sentinels, unfilled placeholders, prompt/template hashes and complete working-tree fingerprint. Outgoing roles may populate Task-specific facts but may not weaken the incoming role's canonical role, authority, methodology, quality criteria, or handoff contract.

### 2.6 Structured handoff facts

- **Planner → Executor:** approved scope, exact path authority, implementation order, requirements, validation, rollback, risks.
- **Executor → Reviewer:** changed paths, requirements claimed complete, commands/tests reported, limitations, deviations, assumptions, risks, labeled `UPSTREAM CLAIMS — UNTRUSTED UNTIL INDEPENDENTLY VERIFIED`.
- **Executor → Planner (`BLOCKED`):** blocker, evidence, partial-work state, affected paths, safe retained work/rollback, exact decision required.
- **Reviewer → Planner:** failed requirement/gate, independent evidence, required correction, valid retained work, scope needing reconsideration.

### 2.7 Canonical professional role contracts

`AGENTS.md` defines shared repository-wide law; each canonical template is the complete role-specific contract instantiated into `next-agent.md`:

| Protocol role | Professional role contract | Canonical template |
| --- | --- | --- |
| `PLANNER` | Principal Software Architect and Implementation Planner | `docs/templates/prompt/planner.md` |
| `EXECUTOR` | Senior Software Implementation Engineer | `docs/templates/prompt/executor.md` |
| `REVIEWER` | Principal Software Verification and Code Review Engineer | `docs/templates/prompt/reviewer.md` |
| `REVIEWER` close-out | Release Integrity and Change-Control Engineer | `docs/templates/prompt/reviewer-closeout.md` |

### 2.8 Role Session Continuity

**Cross-role isolation and same-role continuity are independent properties.** Every Task run owns one logical conversation for Planner, one for Executor, and one for Reviewer. Repeated iterations resume that same-role conversation; Reviewer close-out continues the same Reviewer conversation. A new Task run starts new role conversations.

```text
Planner 1 → Planner 2 → Planner 3
Executor 1 → Executor 2 → Executor 3
Reviewer 1 → Reviewer 2 → Reviewer 3 → Reviewer close-out

Planner session ≠ Executor session ≠ Reviewer session
```

Session history is context only. Authority order remains repository evidence and deterministic Python workflow state, then the current validated `next-agent.md` role/Task contract.

Mode semantics:

- `solo`: the current IDE chat performs deterministic Controller duties and adopts Planner, Executor and Reviewer sequentially from each validated `next-agent.md`; it invokes no subagent or reasoning-role CLI session. Role boundaries remain explicit, but cross-role isolation is soft.
- `solo-headless`: the deterministic Controller invokes one configured native CLI identity and one shared native conversation sequentially across Planner, Executor and Reviewer; cross-role isolation is soft.
- `delegate`: the current IDE chat remains Controller and invokes one distinct inspectable app-native role agent for Planner, Executor and Reviewer per Task run. Later same-role iterations and Reviewer close-out resume the exact stored app-agent handle.
- `delegate-headless`: the deterministic Controller invokes one configured CLI vendor with a distinct persistent native session per role per Task run; later same-role iterations resume that session.
- `delegate-multi`: each CLI role may use a separately configured vendor/model and each turn may launch a fresh OS process, but it resumes the exact stored native conversation ID for that role under `.agents/runs/<task-run-id>/role-sessions.json`. Returned identity mismatch fails closed.
- `manual`: operator keeps Orchestrator, Planner, Executor, Reviewer chats for the Task and returns to the same role chat on later iterations; close-out uses the existing Reviewer chat.

Schema-v3 `.agents/run-config.toml` is authoritative for mode, headless role identities, approval policy, iteration limit, unattended local permissions and recovery policy. All six modes support interactive or frozen unattended gate authorization; unattended mode changes gate authorization only and does not change the selected role transport. All modes use the Task/Goal CLI for deterministic state transitions. IDE-native `solo` and `delegate` pause at a validated role boundary for this chat to perform or delegate the role; `solo-headless`, `delegate-headless` and `delegate-multi` invoke CLI sessions; `manual` waits for operator-managed role chats. Automatic Sol/high recovery-session generation remains headless-only. Schema-v2 names remain resume-compatible and map as `solo → solo-headless`, `delegate → delegate-headless`, and `multi-delegate → delegate-multi` without changing frozen schema-v2 fingerprints. Missing-schema legacy configuration is compatibility-only and does not enable unattended execution.

Unattended runs remain finite. If the normal iteration limit is exceeded and recovery is enabled, the controller may create exactly one fresh recovery session generation for Planner/Executor/Reviewer using `codex/gpt-5.6-sol/high` and allow exactly one additional correction iteration. Exhaustion after that generation is terminal `MAX_ITERATIONS`. Recovery sessions never replace the configured parent identities and are never reused by the next Task or Goal child.

### 2.9 Deterministic Goal supervision

A **Goal** is a supervisory implementation objective containing multiple independently reviewable/committable Tasks. Goal orchestration extends the workflow **above** the atomic Task workflow; it does not modify or duplicate the Planner → Executor → Reviewer state machine.

Architecture:

```text
Goal Controller
    ↓ creates/selects one child Task
Task Orchestrator
    ↓
Planner → Executor → Reviewer
    ↓
Task ACCEPTED
    ↓
Goal Controller → next child
```

Rules:

- Goal Controller and Task Orchestrator are two deterministic state-machine layers in one orchestration system, not separate AI agents.
- Goal Controller owns selection, frozen child order, child Task run identity, progress/checkpointing and Goal terminal state only.
- Goal Controller never performs Planner/Executor/Reviewer reasoning and never directly invokes role-session transport.
- `.agents/goal.toml` is runtime Goal input; `.agents/goals/<goal-run-id>/state.json` is runtime Goal state. Goal runtime state stores child Task run IDs but no Planner/Executor/Reviewer session IDs.
- Supported v1 Goal selection is explicit tracker entries, one numbered phase/prefix, or all open tracker entries. Selection is resolved and frozen at Goal activation; later tracker edits never silently expand active Goal scope.
- Exactly one child Task may be active. Child Tasks run sequentially through the existing Task API and existing Task protocol.
- Every child Task begins from the latest clean accepted `main`, owns its own Task branch, Task run ID, P/E/R role-session set, owner gates, review, exactly one Task implementation commit, and one explicit merge commit on `main`.
- Same-role session continuity is bounded to a child Task. Child N+1 always starts a fresh Planner/Executor/Reviewer conversation set. In `solo`, that logical boundary is also a physical IDE chat boundary guarded by a persisted handoff claim.
- A Goal has no Goal branch and no Goal commit. Its durable implementation history is the ordered set of accepted child Task implementation commits and their explicit merge commits on `main`.
- Goals add no authorization token. `APPROVED: EXECUTE` and `APPROVED: COMMIT` remain the only gate labels and always apply to the active child Task; each may be satisfied by its configured interactive or frozen unattended source.
- Task correction loops do not advance Goal progress. Planner external `BLOCKED` pauses the active child/Goal until that same child is resumed.
- `stop_on_blocked=false` is valid only with frozen unattended runtime policy. It never skips a child: the controller gives the same Planner conversation one bounded retry to resolve non-critical ambiguity through explicit, reversible, repository-grounded assumptions. It never permits assumptions about owner authorization, credentials, external facts, live-action safety, destructive authority, security policy, acceptance evidence, or scope expansion; protected/external blockers still pause the child.
- Every child under that policy must carry an `Assumptions for Human Review` section through Planner, Executor and independent Reviewer evidence. The accepted Reviewer section is archived with a SHA-256 in the Goal assumption ledger, including an explicit `NONE` result when no assumption was used.
- After child `ACCEPTED`, Goal Controller must verify clean `main`, zero-byte active Task workspace, child-run identity and completion of the frozen implementation tracker entry before starting the next child.
- Child cancellation, max iterations, preparation failure or acceptance reconciliation failure blocks the Goal. Previously accepted child commits remain on `main`; Goal supervision never auto-rolls them back.
- Goal becomes `ACCEPTED` only when every frozen child is accepted, every selected tracker entry is complete, `main` is clean, and no Task is active.

Transport symmetry:

- `solo`: one IDE chat per Goal child Task. That child chat performs Controller + Planner + Executor + Reviewer sequentially. After an accepted non-final child, the Goal checkpoints `NEXT_CHILD_CHAT_REQUIRED`; `/new` is the preferred desktop action and app-native task creation is the fallback. The fresh chat must claim the exact persisted handoff before the next child is prepared.
- `solo-headless`: fresh shared native session per child.
- `delegate`: fresh inspectable app-native P/E/R agent set per child; same-role handle continuity only inside a child.
- `delegate-headless`: fresh same-vendor CLI P/E/R session set per child.
- `delegate-multi`: fresh Task run ID and multi-vendor session ledger per child.
- `manual`: same Goal Orchestrator chat across the Goal, but a new dedicated Planner/Executor/Reviewer chat set per child; reuse those chats only within that child.

`CONTINUE: GOAL` may be used only as chat transport/resume after a child has validly reached `ACCEPTED`; it grants no authority.

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

Run bounded tests explicitly, e.g. `uv run pytest --no-cov <selected paths>`. Never run bare/unfiltered pytest or coverage iteratively. Coverage and complete suite are final integration evidence through configured pre-commit/CI gates.

Safe read/verification commands include `pwd`, `ls`, `cat`, `grep`, `git status`, `git diff`, bounded pytest, Ruff, and mypy. Destructive commands and live external actions require explicit applicable authorization.

## 4. Security and operational safety

- Never commit secrets; use `.env.example` for examples and redact sensitive outputs.
- Fail closed when policy, authority, credentials, environment, or evidence is uncertain.
- No live trading/action by default. External integration operations use verified dev/demo/testnet/sandbox targets unless an owning policy explicitly permits an operator-selected live mode.
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
- `.agents/GOALS.md`: deterministic Goal supervision and operating contract.

Planner identifies documentation impact; Executor applies only approved documentation changes; Reviewer verifies consistency and reports discrepancies without fixing them.

## 6. Database and external API rules

- Applied migration steps/checksums are immutable. Schema changes follow owning migration manifests, explicit write locks, ledger verification, and transactional execution.
- Provider uninstall/removal does not imply destructive data purge; retention/purge follows explicit owning policy and separate authorization.
- External APIs use verified public upstream contracts, credential/readiness checks, bounded rate limits, retries/circuit breakers, and deterministic recovery tests.
- Broker/provider implementations stay isolated behind public contracts/capabilities; consumers do not import provider internals.

## 7. Git authority summary

- Goal Controller: no Goal branch, no Goal commit, no direct product mutation; it may prepare runtime Goal/child Task state and invoke the existing Task API sequentially.
- Task Orchestrator: deterministic clean-main entry gate + one Task-branch creation/switch during `TASK_ACTIVATED`; no reasoning conclusions, ordinary commits, merge, or push.
- Planner: no branch creation/switch and no commits/merge/push.
- Executor: no branch creation/switch, commits/merge/push.
- Reviewer: one authorized local Task implementation commit + one explicit `git merge --no-ff` commit on `main` + safe merged-branch deletion only after the `APPROVED: COMMIT` gate is satisfied. The merge commit's first parent must be the recorded `main` baseline and its second parent the exact Task commit.
- Normal workflow never authorizes push, force-push, pull, fetch, rebase, reset, clean, amend, force deletion, merge-conflict resolution, or destructive abandonment without separate explicit owner authorization.
- The `APPROVED: EXECUTE` gate authorizes only the latest dry run of the active child Task. Neither interactive approval nor run preauthorization permits unrelated findings/refactors/dependency upgrades/history rewrites/live or external actions, push, destructive operations, or the rest of a Goal.

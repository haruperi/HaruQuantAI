# Standards and Principles

**Purpose:** Authoritative contributor and three-role development workflow for HaruQuantAI.

## 1. Core engineering principles

- **Repository truth, not chat memory.** Permanent truth lives in `AGENTS.md`, `docs/PROJECT.md`, `docs/ARCHITECTURE.md`, and owning package READMEs. Temporary active-task coordination lives only in `.agents/task/`. Chat context is never authoritative.
- **Scoped authority.** `AGENTS.md` owns contributor process; `docs/PROJECT.md` owns product/system scope and cross-domain relationships; `docs/ARCHITECTURE.md` owns universal structural/runtime constraints; each owning package README is the canonical current-state feature/FR registry for that package. Satisfy all non-overlapping authorities and report real conflicts before editing.
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

**Role-invocation invariant:** no Planner, Executor, or Reviewer invocation may occur unless its complete prompt already exists in `.agents/task/next-agent.md` and has passed protocol validation. This includes the initial Planner invocation after task activation.

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
- They are coordination artifacts, not product specifications, feature registries, or permanent decision history.
- Every non-terminal journal handoff must agree with a valid `next-agent.md`; missing, stale, contradictory, or partially instantiated prompts fail closed.

### 2.2 Role declaration and single writer

Every development agent invocation has exactly one role: `PLANNER`, `EXECUTOR`, or `REVIEWER`. Only one role writes at a time. Roles never run concurrently on the same task branch. A role stops if its authority conflicts with the active handoff.

The orchestrator is not a fourth reasoning role. It may only perform deterministic lifecycle actions, routing/validation, and deterministic owner-gate bookkeeping. It never authors planning, implementation, or review conclusions.

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

- Executor `BLOCKED` → next Planner dry run.
- Reviewer `CHANGES_REQUESTED` → next Planner dry run.
- Owner rejection of execution or commit gate → next Planner dry run with the owner direction.
- Planner `BLOCKED` → owner resolves the documented cause; Planner resumes.
- Planner blocker resolution replaces the stale retry artifact with a fresh canonical `ORCHESTRATOR / BLOCKER_RESOLVED → PLANNER` prompt fingerprinted against the resolved repository state.
- Owner cancellation records terminal `CANCELLED` state and preserves the task branch, worktree, journals, and evidence for deliberate recovery.

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

### 2.7 Planner authority

Planner performs repository inspection, research, architecture/gap analysis, and detailed task decomposition.

Allowed writes:

- `.agents/task/planner.md`;
- `.agents/task/next-agent.md`.

Allowed repository actions are non-mutating inspection and verification of the already-created task branch and recorded baseline.

Planner never creates or switches branches and never edits implementation/tests/configuration/dependencies/authoritative product docs, commits, merges, rebases, pulls, fetches, or pushes.

Each numbered dry run contains all eight sections:

1. Task to do, requirements, tests, usage evidence.
2. Files read.
3. Exact files to create/edit and implementation order.
4. Dependencies/contracts.
5. Blockers/risks/trade-offs.
6. Scope boundaries/inclusions/exclusions.
7. Exact validation commands.
8. Rollback.

Dry Run 1 begins only after the orchestrator has completed `TASK_ACTIVATED`, created the deterministic branch, and materialized/validated the initial Planner prompt. Planner verifies the branch/baseline before planning. Correction dry runs explicitly inventory retained/changed/rolled-back paths. Planner generates the complete next-role prompt before stopping; it never waits inside a headless invocation for owner approval.

### 2.8 Executor authority

Executor first verifies repository root, branch, baseline, approved dry-run hash/record, expected path inventory, journals, and authoritative files routed by the plan.

Allowed writes:

- only implementation/documentation/test paths explicitly authorized by the approved dry run;
- `.agents/task/executor.md`;
- `.agents/task/next-agent.md`.

Executor never edits Planner/Reviewer journals, expands scope, switches branches, commits, merges, rebases, pulls, fetches, or pushes. It runs only approved change-scoped formatting/linting/typing/tests/validators/usage examples during implementation; no coverage or unfiltered suite.

If a material blocker or unapproved path appears, Executor stops before further change, preserves partial work, records evidence/rollback/decision needed, and generates a complete Planner prompt with `BLOCKED`. If all approved work succeeds, it generates the complete Reviewer prompt with `READY_FOR_REVIEW`.

### 2.9 Reviewer authority and anti-anchoring

Reviewer independently verifies and never repairs implementation.

Allowed writes:

- `.agents/task/reviewer.md`;
- `.agents/task/next-agent.md`;
- after exact `APPROVED: COMMIT`, only the defined close-out mutations.

Reviewer follows this order:

1. **Independent reconstruction:** before reading Planner/Executor journals, inspect the original task, `AGENTS.md`, applicable authoritative specifications, main baseline, complete branch diff, staged/unstaged changes, untracked paths, and resulting repository. Derive expected behavior/evidence independently.
2. **Independent verification:** rerun applicable affected tests and non-mutating quality/architecture/usage checks. Upstream reports are not proof.
3. **Claims reconciliation:** only now read Planner/Executor histories and compare their claims with independently observed evidence.

If any defect, omission, scope violation, evidence gap, failed check, or unresolved original requirement exists, Reviewer writes `CHANGES_REQUESTED` and generates a complete Planner correction prompt. It never fixes the defect itself.

If all verification passes, Reviewer writes `PENDING_COMMIT`, generates the complete gated Reviewer close-out prompt, and performs no commit/merge/cleanup before exact owner authorization.

### 2.10 Authorized close-out

After exact `APPROVED: COMMIT`, Reviewer must re-verify that reviewed HEAD and complete working-tree fingerprint are unchanged. It then:

1. records commit authorization;
2. empties all four `.agents/task/` files;
3. stages only approved changes;
4. creates exactly one local task commit, including applicable pre-commit/final coverage gate;
5. verifies `main` is still clean and at the recorded baseline;
6. fast-forward merges only (`git merge --ff-only`);
7. verifies the merged commit;
8. deletes only the safely merged branch with `git branch -d`.

Close-out never force-deletes, rebases, resets, cleans, amends, resolves merge conflicts, pushes, or expands scope. Any failed precondition returns to Planner through `CHANGES_REQUESTED`.

### 2.11 Orchestration modes and isolation

- `solo`: same chat sequentially executes exact prompts; **soft isolation only**. Initial Planner and every later role are invoked from exact validated `next-agent.md`. At each role boundary, stop the old role, load `next-agent.md` as the new role contract, re-read repository evidence, and treat conclusions from prior roles as non-evidence. Solo review is self-review under a fresh role contract, not independent review.
- `delegate`: fresh same-brand subagent per role; fresh role context. Initial Planner is also delegated from the `TASK_ACTIVATED` artifact.
- `multi-delegate`: fresh configured CLI process per role; cross-vendor diversity possible. Initial Planner is launched from the same validated artifact.
- `manual`: user pastes exact `next-agent.md` into a fresh role chat, including the initial Planner artifact created by deterministic task activation.

Mode changes transport only; role prompt semantics and activation artifacts are identical.

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
- Python/runtime policy enforcement is authoritative; LLM prompts are not a substitute for deterministic controls.

## 5. Documentation and ownership

- Owning package README: domain feature/FR registry, current feature status, semantic contracts, persistence target model, usage/evidence mapping.
- `docs/ARCHITECTURE.md`: universal structural/runtime/database conventions.
- `docs/PROJECT.md`: product/system scope, domain index, cross-domain relationships and NFRs.
- `AGENTS.md`: contributor and three-role workflow.
- `docs/dev/IMPLEMENTATION_ORDER.md`: delivery sequencing.
- `docs/dev/feature_implementation_pipeline.md`: feature delivery architecture/checklist.
- `docs/templates/prompt/`: canonical reusable workflow prompt definitions.

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

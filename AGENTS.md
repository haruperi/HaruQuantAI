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
- A stateful service feature may add one feature-local `_persistence.py` module as the single owner of
  its database operations. It uses public Workspace persistence contracts, never raw connections or
  unrestricted SQL. Stateless features omit it. Persistence support follows the owning README and
  architecture guide and never absorbs authorization, policy, orchestration, or feature semantics.
- D-UI follows its own owning README: registered `FEAT-UI-*` capabilities own widgets; widgets never have multiple feature owners; shared UI support folders do not become product-policy owners.

## 2. Atomic Task workflow

The atomic development workflow is risk-tiered above a shared
**Executor → Reviewer** acceptance core. A deterministic, source-pinned Task
packet routes executor-ready Routine/Standard work directly to the execution
owner gate; Critical or unresolved work first receives targeted Planner
analysis. `.agents/protocol.toml` is the machine-readable transition contract.
Detailed operating procedure belongs in `.agents/PROCEDURE.md` and must not be
loaded when the current packet and role contract already provide the applicable
instructions.

A **Task** is the smallest coherent implementation unit that should receive its own prepared authority packet, implementation, independent review, branch and Git commit. Targeted planning is required when risk or unresolved decisions demand it. Planner phases/tasks are subdivisions inside one Task; they are not separate workflow runs.

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
- After branch creation, the orchestrator generates and fingerprints the Task
  packet. `EXECUTOR_READY` Routine/Standard packets instantiate Executor and
  pause at `APPROVED: EXECUTE`; Critical, incomplete, ambiguous or stale packets
  instantiate Planner through `TASK_ACTIVATED -> PLANNER`.
- The packet declares one authoring route: reuse an existing V3 owner first,
  use the single stateless-backend scaffold only when its exact eligibility and
  write paths are present, implement missing behavior manually, or forbid
  automatic scaffolding. A scaffold is incomplete structure and never proof of
  implementation, passing requirements, executable usage, or acceptance.
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
  → prepared-packet gate OR targeted Planner Dry Run N
  → PENDING_APPROVAL
  → execute gate: exact owner message or frozen run preauthorization
  → Executor Report N
  → READY_FOR_REVIEW
  → controller integration gate and exact-input validation receipt
  → Reviewer Review N
  → PENDING_COMMIT
  → commit gate: exact owner message or frozen run preauthorization
  → deterministic Controller close-out
  → ACCEPTED
  → ORCHESTRATOR READY / TASK NONE
```

Correction paths:

- Executor `BLOCKED` → next Planner dry run in the same Planner role conversation for this Task run.
- Reviewer `IMPLEMENTATION_FIX` → Executor correction → Reviewer, for at most
  two unchanged-scope rounds; exhaustion returns to targeted Planner analysis.
- Reviewer/Executor `DESIGN_CHANGE` → targeted Planner analysis.
- `ADMINISTRATIVE_RETRY` and `ENVIRONMENT_FAILURE` preserve the candidate and
  allow at most one identical controller retry. They never authorize source,
  policy, secret-baseline, commit or merge changes.
- Legacy `CHANGES_REQUESTED` artifacts return to Planner only for compatibility.
- Owner rejection of execution or commit gate → next Planner dry run with the owner direction.
- Planner `BLOCKED` → owner resolves the documented cause; Planner resumes its same role conversation with a fresh canonical prompt.
- Planner blocker resolution replaces the stale retry artifact with a fresh canonical `ORCHESTRATOR / BLOCKER_RESOLVED → PLANNER` prompt fingerprinted against the resolved repository state.
- Owner cancellation records terminal `CANCELLED` state and preserves Task branch, worktree, journals, run evidence, and role-session evidence.

In `approval_policy = "interactive"`, execution authorization is valid only when the entire trimmed owner message is exactly `APPROVED: EXECUTE`, and commit authorization is valid only when it is exactly `APPROVED: COMMIT`. In `approval_policy = "unattended"`, those same protocol gates may instead be satisfied by `RUN_PREAUTHORIZATION` frozen from schema-v3/v4 `.agents/run-config.toml` at run activation. Execute requires `allow_execute`; close-out requires both `allow_local_commit` and `allow_local_merge`. A preauthorization record must state its true source plus the frozen policy and scope SHA-256 values and must never claim that a human sent an approval message.

After either valid execute-gate source, the Controller records a truthful
authorization bound to either the approved pre-gate Planner bytes or the exact
executor-ready packet. It appends to Planner journal only for Planner-owned
authority; packet-owned authorization is stored in ignored run state and never
manufactures Planner evidence.

### 2.5 `next-agent.md` as role boundary

Every new reasoning-role prompt uses schema version 2 and records
run/task/iteration, source/target role, handoff, branch, baseline, source HEAD,
canonical template, gate requirement and packet/risk identity when applicable.
Schema version 1 is read-only compatibility for already-frozen runs.

The orchestrator validates transition/template, schema, branch/baseline/HEAD, protected incoming-role sentinels, unfilled placeholders, prompt/template hashes and complete working-tree fingerprint. Outgoing roles may populate Task-specific facts but may not weaken the incoming role's canonical role, authority, methodology, quality criteria, or handoff contract.

### 2.6 Structured handoff facts

- **Planner → Executor:** approved scope, exact path authority, implementation order, requirements, validation, rollback, risks.
- **Executor → Reviewer:** changed paths, requirements claimed complete, commands/tests reported, limitations, deviations, assumptions, risks, labeled `UPSTREAM CLAIMS — UNTRUSTED UNTIL INDEPENDENTLY VERIFIED`.
- **Executor → Planner (`BLOCKED`):** blocker, evidence, partial-work state, affected paths, safe retained work/rollback, exact decision required.
- **Reviewer → Executor (`IMPLEMENTATION_FIX`):** exact failed expectation, independent evidence, unchanged approved scope, valid retained work and bounded correction count.
- **Reviewer → Planner (`DESIGN_CHANGE`):** failed requirement/gate, independent evidence, required design decision, valid retained work and scope needing reconsideration.

### 2.7 Canonical professional role contracts

`AGENTS.md` defines shared repository-wide law; each canonical template is the complete role-specific contract instantiated into `next-agent.md`:

| Protocol role | Professional role contract | Canonical template |
| --- | --- | --- |
| `PLANNER` | Principal Software Architect and Implementation Planner | `docs/templates/prompt/planner.md` |
| `EXECUTOR` | Senior Software Implementation Engineer | `docs/templates/prompt/executor.md` |
| `REVIEWER` | Principal Software Verification and Code Review Engineer | `docs/templates/prompt/reviewer.md` |
| Controller close-out | Deterministic non-reasoning contract | `docs/templates/prompt/reviewer-closeout.md` |

### 2.8 Role Session Continuity

**Cross-role isolation and same-role continuity are independent properties.** Every Task run owns one logical conversation for each reasoning role it actually invokes. Repeated iterations resume that same-role conversation. Close-out is deterministic Controller work and has no role conversation. A new Task run starts new role conversations.

```text
Planner 1 → Planner 2 → Planner 3
Executor 1 → Executor 2 → Executor 3
Reviewer 1 → Reviewer 2 → Reviewer 3 → Controller close-out

Planner session ≠ Executor session ≠ Reviewer session
```

Session history is context only. Authority order remains repository evidence and deterministic Python workflow state, then the current validated `next-agent.md` role/Task contract.

`.agents/run-config.toml` freezes role transport, identities, approval policy,
iteration bounds, local permissions, recovery, and optional parallel-Goal
policy. Transport never changes role authority or owner gates. Same-role
iterations resume their Task-local identity; identities never cross roles or
Task runs; deterministic close-out has no role identity. Unattended runs remain
finite and may use only the configured single bounded recovery generation.
Schema-v2/v3 compatibility and the complete mode-specific procedure live in
`.agents/PROCEDURE.md`; `.agents/protocol.toml` remains machine-authoritative.

### 2.9 Deterministic Goal supervision

A **Goal** is a supervisory implementation objective containing multiple independently reviewable/committable Tasks. Goal orchestration extends the workflow **above** the risk-tiered atomic Task workflow; it does not modify or duplicate its packet, reasoning-role, receipt, or close-out state machine.

Architecture:

```text
Goal Controller
    ↓ creates/selects one child Task
Task Orchestrator
    ↓
Prepared packet → optional Planner → Executor → Reviewer → Controller close-out
    ↓
Task ACCEPTED
    ↓
Goal Controller → next child
```

The Goal Controller is deterministic and owns only frozen child selection/order,
child Task identities, progress, and terminal reconciliation. It performs no
reasoning, owns no Goal branch/commit, and grants no new authorization. Every
child retains the full Task protocol, starts from accepted `main`, and produces
its own reviewed implementation and merge commits. Corrections never advance
Goal progress; failed/cancelled children block rather than being skipped or
rolled back automatically.

Sequential Goals have one active child. Explicit schema-v4 parallel Goals use
two or three isolated draft lanes (two first for benchmarking), but exact-path leases, accepted
predecessors, current-main refresh, fresh final review, lane-scoped gates, and
serialized integration remain mandatory. A draft review is not acceptance or
commit authority. Dirty or unresolved lanes are preserved, never force-cleaned.
Complete Goal selection, assumption, lane, transport, refresh, reconciliation,
and chat-handoff rules live in `.agents/GOALS.md` and `.agents/PROCEDURE.md`.

DT-09 delivery batches group only preparation, reusable packet context, one
post-acceptance integration gate, and the eventual operator push for two or
three Routine/Standard Tasks. Every member retains its Task branch, independent
review, evidence, implementation commit, merge commit, and acceptance. Critical
work, unstable packets, path collisions, and internal unaccepted predecessors
fail closed. Scope never grows merely to fill a batch.

Every accepted Task writes a bounded throughput summary. Lane adoption requires
ten comparable accepted results and no escaped regression or reopen; unavailable
provider usage and allowance observations remain null rather than inferred.

### 2.10 Quick-Fix mode

`quick-fix` is an explicit versioned, interactive, chat-direct exception outside
Task/Goal state. Its name does not limit size, but the approved dry run must
fully scope the work. It cannot become a Goal child.

```text
clean main → comprehensive Dry Run in the current chat
           → exact APPROVED: EXECUTE
           → direct implementation and validation on main
```

It requires clean `main`, a comprehensive current-chat Dry Run, and the exact
next owner message `APPROVED: EXECUTE`. It creates no Task/Goal/run/role state,
branch, Reviewer, commit gate, commit, merge, push, archive, or automatic
rollback. It changes ceremony only: scope, security, quality, architecture,
evidence, external/live/destructive authority, and separate Git authorization
remain unchanged. The full required Dry Run fields and operating procedure live
in `.agents/PROCEDURE.md`; Task/Goal APIs fail closed while Quick-Fix is selected.

Normal Task branch, Reviewer, commit, and no-ff merge rules remain unchanged for
every non-Quick-Fix mode.

## 3. Coding style and verification

- **Strict adherence.** Follow the
  [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)
  and the repository Ruff configuration.
- **Formatting.** Use 4-space indentation and `ruff format` (double quotes and
  magic trailing commas apply). The pre-commit order is repository hygiene and
  syntax checks, Ruff check, Ruff format check, then secret detection. Pre-push
  runs affected-scope validation for the outgoing local delta. It does not run
  the complete repository suite for every push; comprehensive qualification is
  enforced at the local integration-candidate gate and by CI `acceptance`.
- **Typing and documentation.** Add explicit type hints to every signature and
  run the configured strict mypy checks. Every module, public class, public
  function, and non-obvious private function has a properly fitted Google-style
  docstring containing its description and all applicable `Args`, `Returns`,
  `Raises`, and type semantics; do not add empty sections that do not apply.
- **System-wide structured logger.** Code that needs operational logging imports
  `get_logger` from `app.composition.logging` and declares
  `logger = get_logger(__name__)`. Use it at workflow boundaries, public service
  entry points, external interactions, state transitions, side-effect
  boundaries, important decisions, retries, and failures. Pure helpers, trivial
  accessors, deterministic transformations, and high-frequency numerical
  functions do not require logging unless an owning requirement says otherwise.
  Application and service modules never configure handlers or global logging.
- **Logging safety.** Never log secrets, credentials, personal information,
  complete sensitive payloads, workspace paths, fence/session tokens, or
  sensitive trading/account data. Prefer bounded structured fields and stable
  error codes over interpolated payloads or raw exception messages.
- **Imports.** Use absolute imports grouped as standard library, third party, and
  local application imports.
- **Versioning.** Confirm dependency versions from `pyproject.toml` and the lock
  file before coding against a library; the pinned repository version is the
  default authority.
- **Quality.** Maintain at least 80 percent project pytest coverage. No bare
  `except:`, silent failure, or application/library `print`. Directly executable
  teaching and usage harnesses may print bounded, secret-safe observations.
- **Usage evidence.** Every service feature has one required feature-local
  `_usage.py`, which is the sole executable usage owner and defines a bounded
  `main()` or `_run_usage_example()` called under an
  `if __name__ == "__main__":` guard. It exercises every public operation and
  constructor owned by the feature through documented public APIs, including a
  useful scenario, failure/unavailable behavior, and cleanup, using realistic
  offline secret-safe inputs or genuine bounded runtime state. It is executed
  directly and excluded from pytest collection. Tests verify behavior without
  becoming a second usage implementation; domain-logic modules contain no usage
  harnesses.
- **Test ownership.** Feature-level tests belong under the owning test namespace;
  system architecture, composition, and removability tests remain in their
  documented locations.
- **Clean resource lifecycles.** Close SQLite handles, sockets, files, and
  subprocesses explicitly in production and test teardown or context managers.
- **Async mocking rigor.** Mocks for asynchronous operations return genuine
  coroutines, futures, or other awaitables so no unawaited-coroutine warning is
  tolerated.

### Change-scoped testing

During implementation/review, derive the affected set from `git diff --name-only`, staged diff, and untracked paths. Map changed production code to owning and affected contract/consumer/architecture tests. The Controller runs the selected integration candidate once before Reviewer and records full logs plus a source-bound receipt. Reviewer verifies that receipt and runs only additional adversarial checks selected through independent judgment; identical receipted commands are not repeated.

Run bounded tests explicitly, e.g. `uv run pytest --no-cov <selected paths>`.
Never run bare/unfiltered pytest or coverage iteratively. After Executor freezes a
candidate and before Reviewer starts, the Controller runs
`scripts/ci_check.py --profile integration` once against accepted main, stores
full ignored logs and binds a receipt to relevant inputs. Python-changing
candidates retain comprehensive coverage; UI candidates retain typecheck, tests
and production build. Unchanged receipts are reused at commit authorization.
After a registered feature reaches Reviewer `PENDING_COMMIT`, the Controller may
project only packet-declared current evidence outputs. It requires the exact
passing validation receipt and explicit requirement-to-evidence mappings,
preserves pinned Phase-0 snapshots, records a derived pre/post-candidate receipt,
and never infers completion from file or test names. This deterministic
evidence-only mutation does not rerun unchanged product validation; any missing,
failed, stale, edited, or unauthorized input/output fails closed. Parallel draft
workers never write shared aggregate ledgers; only serialized integration does.
CI repeats candidate-appropriate qualification under the stable `acceptance`
status after an independently authorized push.

Local Task acceptance is local-first: `ACCEPTED` proves the controller-gated local candidate and exact merge lineage. It does not authorize or claim a push, pull-request merge, remote check result or branch-protection state. Remote publishing and repository administration require separate explicit authority.

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

- Goal Controller: no Goal branch, no Goal commit, no direct product mutation; it may prepare runtime Goal/child Task state and invoke the existing Task API sequentially or through explicitly enabled parallel draft lanes.
- Task Orchestrator: deterministic clean-main entry gate, packet generation/risk
  routing, one Task-branch creation/switch, validation receipts, and authorized
  deterministic commit/no-ff merge/cleanup. It makes no review conclusions and
  never pushes.
- Planner: no branch creation/switch and no commits/merge/push.
- Executor: no branch creation/switch, commits/merge/push.
- Reviewer: no commit, merge, push or branch mutation; it authors the independent review conclusion and selected adversarial-check evidence only.
- Task Controller: after the `APPROVED: COMMIT` gate, verifies the exact-input receipt and reviewed candidate, stages only packet-authorized paths, creates one local Task implementation commit plus one explicit `git merge --no-ff` commit on `main`, and safely deletes the merged branch. The merge commit's first parent must be the recorded `main` baseline and its second parent the exact Task commit.
- Normal workflow never authorizes push, force-push, pull, fetch, rebase, reset, clean, amend, force deletion, merge-conflict resolution, or destructive abandonment without separate explicit owner authorization.
- The `APPROVED: EXECUTE` gate authorizes only the latest dry run of the active child Task. Neither interactive approval nor run preauthorization permits unrelated findings/refactors/dependency upgrades/history rewrites/live or external actions, push, destructive operations, or the rest of a Goal.

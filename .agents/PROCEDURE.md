<!-- markdownlint-disable-file MD013 MD024 MD025 MD060 -->

# Agent Workflow — Complete Operational Procedures

HaruQuantAI has one atomic Planner → Executor → Reviewer Task workflow and one deterministic Goal supervisor above it. All six transport modes share the same Task/Goal semantics; only transport changes.

A Task run owns one logical Planner, Executor and Reviewer continuity boundary. IDE `solo` carries those role contexts sequentially in the same child Task chat; the other modes reuse their same-role agent/session/chat within the Task. For a `solo` Goal, every next child starts in a fresh physical IDE chat as well as fresh role continuity.

The only owner authorization messages are:

```text
APPROVED: EXECUTE
APPROVED: COMMIT
```

Schema-v3 `.agents/run-config.toml` selects the transport and either `approval_policy = "interactive"` or `"unattended"`. Every mode supports unattended operation: the protocol gates are satisfied from frozen `RUN_PREAUTHORIZATION` only for enabled permissions, while the selected IDE, headless, or manual role transport remains unchanged. The controller records policy/scope hashes and never fabricates a human message. Execute, local commit, and local merge must each be explicitly permitted. Push, external/live actions, destructive operations, and scope expansion remain unauthorized. Automatic Sol/high recovery-session generation is available only in headless modes.

`CONTINUE: REVIEWER` and `CONTINUE: GOAL` are transport/resume phrases only and grant no authority.

---

## Common setup

Configure mode:

```bash
uv run .agents/configure.py
```

Prepare one Task:

```bash
uv run .agents/make_task.py --list
uv run .agents/make_task.py 1.1
```

Prepare one Goal:

```bash
uv run .agents/make_goal.py --entries 7.1 7.2 7.3
uv run .agents/make_goal.py --phase 7
uv run .agents/make_goal.py --all-open
uv run .agents/make_goal.py --all-open --continue-on-blocked
```

`task.toml` and `goal.toml` are runtime input only. Their presence does not activate work.

---

## Part 1 — Standalone Task: Chat-Driven Solo/Delegate

This part applies to IDE-native `solo` and `delegate`. Both use `.agents/orchestrator.py` as the deterministic state controller, but neither uses `.agents/session_runner.py`:

1. Run `start` or `resume` until it reports `[ROLE_READY]`.
2. In `solo`, this same IDE chat reads the validated `next-agent.md` and performs the named role inline.
3. In `delegate`, this chat invokes a new inspectable app-native agent for the role, or resumes its previously bound handle, using the exact validated prompt.
4. After the role writes its journal/handoff, return control with `resume --role-complete`; `delegate` also supplies `--app-agent-id <opaque-id>`.
5. The controller independently verifies the role boundary and routes to the next gate or role.

```bash
### Solo role completion
uv run .agents/orchestrator.py resume --role-complete

### Delegate role completion
uv run .agents/orchestrator.py resume --role-complete --app-agent-id <opaque-id>
```

## Authorization behavior in Part 1

- With `approval_policy = "interactive"`, the controller pauses at `PENDING_APPROVAL` and `PENDING_COMMIT` for the exact owner messages documented below.
- With `approval_policy = "unattended"`, the controller checks the policy frozen at Task activation. `allow_execute=true` satisfies the execute gate from `RUN_PREAUTHORIZATION`; both `allow_local_commit=true` and `allow_local_merge=true` are required to satisfy the commit/merge gate. The current IDE chat still performs or delegates every prepared role and reports each role completion—the policy does not convert `solo` or `delegate` into a headless mode.
- If an unattended permission needed by a gate is false, the Task remains at that gate and may continue only after the corresponding exact owner message. Unattended policy never invents an approval.

## Step 1 — Initialize Orchestrator

Paste into the Orchestrator chat:

```text
Initialize the HaruQuantAI development orchestrator for this repository.

Read and follow:
- AGENTS.md
- .agents/ORCHESTRATOR.md
- .agents/protocol.toml
- .agents/README.md

Initialize yourself only as the orchestration controller.
Do not activate a task yet.
Do not invoke Planner, Executor, or Reviewer yet.
Do not create a task branch.
Do not modify implementation files or .agents/task/ journals.
Do not infer a task from previous chat history.

Verify the repository and idle active-task workspace.
When ready, report:

ORCHESTRATOR : READY
TASK : NONE
AWAITING : TASK_SPEC
```

## Step 2 — Activate Task and Planner

```text
Activate and run the task defined in .agents/task.toml.

Use AGENTS.md, .agents/ORCHESTRATOR.md and .agents/protocol.toml.
Treat .agents/task.toml as authoritative runtime task input.

1. validate the clean-main entry gate;
2. record the main baseline commit;
3. derive/create/switch to the deterministic task branch;
4. instantiate the canonical Planner contract into .agents/task/next-agent.md;
5. validate ORCHESTRATOR / TASK_ACTIVATED -> PLANNER;
6. activate Planner using the exact complete next-agent.md.

Planner must not recreate or switch the task branch.
Continue until the selected approval policy requires external action or the Task reaches a role boundary.
Do not execute implementation without either the exact interactive owner gate or valid frozen RUN_PREAUTHORIZATION.
```

Expected gate:

```text
STOPPED : PLANNER
ACTIVATING : EXECUTOR
HANDOFF : PENDING_APPROVAL
```

## Step 3 — Execution gate

### Execution gate — interactive

Approve with the exact standalone message:

```text
APPROVED: EXECUTE
```

Reject with:

```text
REJECTED: EXECUTE

Owner direction:
<describe exactly what must change in the dry run>
```

A correction gets a fresh current Planner prompt but resumes the same Planner conversation for this Task run.

### Execution gate — unattended

When `allow_execute=true`, run/resume without `--approved`. The controller verifies the frozen policy and Task-scope fingerprints, records `RUN_PREAUTHORIZATION`, independently hashes the exact approved Planner bytes, and routes to Executor without waiting for an owner message.

When `allow_execute=false`, the controller stays at `PENDING_APPROVAL`. After the owner sends exact `APPROVED: EXECUTE`, relay it with `resume --approved`; a rejection still uses `resume --reject-feedback "..."`.

## Step 4 — Planner blocker

After resolving an external Planner blocker:

```text
RESOLVED: PLANNER BLOCKER

Resolution evidence:
<what changed and where Planner can verify it>
```

The old pending prompt is stale. Orchestrator creates a fresh `BLOCKER_RESOLVED` Planner prompt and resumes the same Planner conversation. Resolution is not execution approval.

Executor `BLOCKED` and Reviewer `CHANGES_REQUESTED` automatically return to the same Planner conversation with a fresh current prompt.

## Step 5 — Executor → Reviewer

Executor success yields:

```text
STOPPED : EXECUTOR
ACTIVATING : REVIEWER
HANDOFF : READY_FOR_REVIEW
```

Solo may require another user turn:

```text
CONTINUE: REVIEWER
```

This only resumes transport. Delegate activates/resumes its dedicated Reviewer handle automatically.

## Step 6 — Reviewer

Every Review N performs:

1. Stage A — independent reconstruction from current repository/task evidence before upstream journals.
2. Stage B — independent tests/quality/architecture/usage verification.
3. Stage C — only then reconcile Planner/Executor journals and hashes.

Outcomes:

- `CHANGES_REQUESTED` → Planner Dry Run N+1 in the same Planner conversation.
- `PENDING_COMMIT` → owner commit gate.

## Step 7 — Commit and merge gate

### Commit gate — interactive

Approve:

```text
APPROVED: COMMIT
```

Reject:

```text
REJECTED: COMMIT

Owner direction:
<describe why the reviewed state must change>
```

### Commit gate — unattended

When both `allow_local_commit=true` and `allow_local_merge=true`, run/resume without `--approved-commit`. The controller records `RUN_PREAUTHORIZATION` and routes the existing Reviewer conversation to close-out automatically.

If either permission is false, the controller stays at `PENDING_COMMIT`. After the owner sends exact `APPROVED: COMMIT`, relay it with `resume --approved-commit`; a rejection still uses `resume --reject-commit-feedback "..."`.

## Step 8 — Reviewer close-out

After valid interactive or unattended commit authorization, close-out continues the same Reviewer conversation. It re-verifies reviewed identity, confirms archived evidence, runs final gates, stages only approved implementation paths, creates exactly one Task implementation commit, clears coordination files only after commit success, verifies Task branch/main/lineage/path authority, creates an explicit `git merge --no-ff` commit on `main`, verifies that the merge parents are the recorded baseline and exact Task commit, safely deletes the merged Task branch and marks `ACCEPTED`.

```text
STOPPED : REVIEWER
ACTIVATING : NONE
HANDOFF : ACCEPTED
```

---

## Part 2 — Standalone Task: Process-Backed CLI

This CLI reasoning-session path is valid for `solo-headless`, `delegate-headless`, and `delegate-multi`. `solo-headless` shares one native CLI session across roles; `delegate-headless` uses distinct same-vendor role sessions; `delegate-multi` permits independent role vendors/identities.

Doctor:

```bash
uv run .agents/orchestrator.py doctor
```

Start:

```bash
uv run .agents/orchestrator.py start --task-file .agents/task.toml
```

Interactive resume/gates:

```bash
uv run .agents/orchestrator.py resume
uv run .agents/orchestrator.py resume --approved
uv run .agents/orchestrator.py resume --reject-feedback "..."
uv run .agents/orchestrator.py resume --resolve-planner-blocker "..."
uv run .agents/orchestrator.py resume --approved-commit
uv run .agents/orchestrator.py resume --reject-commit-feedback "..."
```

Each role turn may be a fresh OS process, but `.agents/session_runner.py` resumes the exact stored native role conversation for the Task run. Reviewer close-out reuses the Reviewer session.

## Unattended process-backed procedure

1. Configure one of the three headless modes with `approval_policy = "unattended"`.
2. Set `allow_execute=true`, `allow_local_commit=true`, and `allow_local_merge=true` for a fully unattended local Task lifecycle.
3. Run `doctor`, then `start`. Do not pass `--approved` or `--approved-commit`; the controller satisfies enabled gates from the frozen policy.
4. The process-backed controller invokes Planner, validates its handoff, records execute preauthorization, invokes Executor, invokes Reviewer, records commit/merge preauthorization, and resumes the same Reviewer session for close-out.
5. Correction loops reuse the exact stored role session: Executor `BLOCKED` or Reviewer `CHANGES_REQUESTED` returns to Planner, then repeats the automatically authorized execute gate.
6. A Planner external blocker still pauses. Resume only after supplying real resolution evidence with `--resolve-planner-blocker`.
7. If a required unattended permission is false, the run pauses at that gate. Supply the matching flag only after the owner has sent the exact interactive authorization.
8. If `max_iterations` is exceeded and recovery was explicitly enabled, one fresh `codex/gpt-5.6-sol/high` recovery generation receives exactly one additional correction iteration. A second exhaustion is terminal `MAX_ITERATIONS`.

Fully preauthorized start/resume:

```bash
uv run .agents/orchestrator.py doctor
uv run .agents/orchestrator.py start --task-file .agents/task.toml
uv run .agents/orchestrator.py resume
```

`resume` is needed only when transport or an external blocker caused the controller to return. It is not an approval token.

---

## Part 3 — Standalone Task: Manual Mode

For one Task maintain four chats:

1. Orchestrator.
2. Planner.
3. Executor.
4. Reviewer, also used for close-out.

On first use of a role, open its dedicated chat and paste the entire exact current `.agents/task/next-agent.md`. On later iterations return to that same role chat.

## Authorization behavior in Part 3

Manual mode changes who transports prompts, not how gates are authorized:

- With `approval_policy = "interactive"`, the Orchestrator chat waits for exact `APPROVED: EXECUTE` and `APPROVED: COMMIT` before preparing the next role transport.
- With `approval_policy = "unattended"` and `allow_execute=true`, the Orchestrator records `RUN_PREAUTHORIZATION` immediately after validating Planner `PENDING_APPROVAL` and prepares the Executor transport without requesting owner approval.
- With `approval_policy = "unattended"` and both local close-out permissions true, the Orchestrator records `RUN_PREAUTHORIZATION` after Reviewer `PENDING_COMMIT` and prepares Reviewer close-out without requesting owner approval.
- The operator must still move each complete `next-agent.md` prompt to the correct dedicated role chat and report role completion. Unattended authorization does not make `manual` process-backed or allow the Orchestrator to perform a reasoning role.
- Any disabled required permission falls back to the corresponding exact owner gate. Blockers, corrections, and protected actions never become implicitly authorized.

Initialize Orchestrator with:

```text
Initialize the HaruQuantAI development orchestrator for this repository in MANUAL mode.

Read and follow AGENTS.md, .agents/ORCHESTRATOR.md, .agents/protocol.toml and .agents/README.md.
You are the orchestration controller only.
Do not act as Planner, Executor, or Reviewer.
Do not activate a task yet.

For this Task run I will maintain this Orchestrator chat plus one persistent Planner chat, one persistent Executor chat, and one persistent Reviewer chat. On later role iterations instruct me to return to the existing role chat and paste the complete current .agents/task/next-agent.md.

When ready report:
ORCHESTRATOR : READY
MODE : MANUAL
TASK : NONE
AWAITING : TASK_SPEC
```

When first Planner is ready, Orchestrator reports:

```text
ORCHESTRATOR : READY_FOR_TRANSPORT
TARGET_ROLE : PLANNER
HANDOFF : TASK_ACTIVATED
PROMPT : .agents/task/next-agent.md
ACTION : OPEN_DEDICATED_PLANNER_CHAT
```

After each role finishes, return to Orchestrator and report that invocation finished so it can validate journals/next-agent and route the Task. Rejections and blocker corrections return to existing role chats. At commit approval the close-out instruction must be:

```text
ORCHESTRATOR : READY_FOR_TRANSPORT
TARGET_ROLE : REVIEWER
HANDOFF : PENDING_COMMIT
PROMPT : .agents/task/next-agent.md
ACTION : RETURN_TO_REVIEWER_CHAT
```

Do not open a separate close-out chat.

## Manual unattended sequence

For a fully preauthorized manual Task:

1. Orchestrator prepares Planner prompt; operator runs it in the dedicated Planner chat.
2. Planner returns `PENDING_APPROVAL`; Orchestrator validates it and automatically records execute preauthorization.
3. Orchestrator prepares Executor prompt; operator runs it in the dedicated Executor chat.
4. Orchestrator prepares Reviewer prompt; operator runs it in the dedicated Reviewer chat.
5. Reviewer `CHANGES_REQUESTED` returns to the existing Planner chat and repeats the sequence without a human execute approval when `allow_execute=true`.
6. Reviewer `PENDING_COMMIT` is automatically authorized only when both local close-out permissions are true.
7. Orchestrator prepares close-out prompt; operator returns to the existing Reviewer chat.
8. Reviewer performs the implementation commit, explicit no-fast-forward merge, cleanup, and terminal verification.

---

## Part 4 — Goal Orchestration

A Goal supervises multiple ordinary Tasks sequentially. Read `.agents/GOALS.md` before operating a Goal.

## Goal invariants

- Goal Controller is deterministic, not an LLM reasoning role.
- Selection resolves once and freezes at Goal activation.
- Exactly one child Task may be active.
- Every child uses the normal Task workflow unchanged and produces its own commit.
- Goal has no Goal branch, Goal commit, Planner/Executor/Reviewer session, or additional owner gate.
- Same-role continuity exists only inside a child Task; next child starts a fresh P/E/R set.
- Goal advances only after child `ACCEPTED` plus clean-main/zero-byte-workspace/tracker reconciliation.

## Complete Goal lifecycle — every mode

### Step 1 — Configure and prepare

1. Run `.agents/configure.py` and select the transport mode and approval policy for the whole Goal run.
2. Generate `.agents/goal.toml` with explicit entries, one phase, or all open tracker entries.
3. Review `stop_on_blocked` and any `child_additional_context` before activation. They become frozen Goal scope.
4. Verify that `main` is clean and no standalone Task or other Goal is active.

### Step 2 — Activate Goal and first child

Run `goal-start`. The Goal Controller:

1. validates the runtime policy and clean-main entry gate;
2. resolves the tracker selection exactly once and freezes child order;
3. records Goal scope and runtime-policy SHA-256 values;
4. generates `.agents/task.toml` for the first frozen entry;
5. creates a unique child Task run and branch from the current clean accepted `main`;
6. prepares and validates the initial Planner prompt;
7. hands control to the selected role transport.

### Step 3 — Run the active child through the ordinary Task protocol

Every Goal child follows the same Planner → Executor → Reviewer state machine as a standalone Task. The transport is:

| Mode                 | Active child procedure                                                                  |
| -------------------- | --------------------------------------------------------------------------------------- |
| `solo`               | One child IDE chat performs Controller + Planner + Executor + Reviewer sequentially.  |
| `solo-headless`      | One fresh shared native CLI conversation performs all three roles for that child.     |
| `delegate`           | The Goal IDE controller uses a fresh inspectable Planner/Executor/Reviewer agent set for that child. |
| `delegate-headless`  | A fresh same-vendor persistent CLI session is created for each role in that child.     |
| `delegate-multi`     | A fresh child Task ledger holds the independently configured vendor/model session for each role. |
| `manual`             | The Goal Orchestrator chat remains, while the operator opens a fresh dedicated P/E/R chat set for that child. |

Same-role corrections reuse the current child's role conversation. No role conversation or app-agent handle crosses into the next child.

### Step 4 — Authorize the child gates

| Policy          | Execute gate                                                                                   | Commit/merge gate                                                                                                   |
| --------------- | ---------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------ |
| `interactive`   | Wait for exact `APPROVED: EXECUTE`; relay with `goal-resume --approved`.                      | Wait for exact `APPROVED: COMMIT`; relay with `goal-resume --approved-commit`.                                  |
| `unattended`    | `allow_execute=true` records `RUN_PREAUTHORIZATION`; no owner message or `--approved` flag.    | Both `allow_local_commit=true` and `allow_local_merge=true` record `RUN_PREAUTHORIZATION`; no owner message or `--approved-commit` flag. |

If an unattended permission required by the current gate is false, the child stays at that gate and falls back to the corresponding exact interactive owner message. Every gate record names its real source and includes the frozen policy/scope hashes; unattended operation never fabricates an owner message.

### Step 5 — Handle correction and blocker paths

- Executor `BLOCKED`, Reviewer `CHANGES_REQUESTED`, or owner rejection returns to the same child Planner conversation with a fresh validated Planner prompt. Goal progress does not advance.
- Planner external `BLOCKED` pauses the active child and Goal until real resolution evidence is supplied.
- With frozen unattended policy and `stop_on_blocked=false`, the controller gives the same Planner conversation one bounded retry for an explicit, reversible, repository-grounded assumption. It never skips the child or assumes protected authority, credentials, external facts, destructive safety, acceptance evidence, or scope expansion.
- Cancellation, terminal max iterations, preparation failure, or acceptance-reconciliation failure blocks the Goal. Previously accepted children remain merged on `main`.

### Step 6 — Accept and reconcile one child

After valid commit authorization, the existing Reviewer conversation performs close-out. Before Goal progress advances, the Goal Controller verifies:

1. the child Task reached `ACCEPTED`;
2. exactly one implementation commit and the explicit merge commit were produced;
3. the repository returned to clean `main`;
4. all active Task coordination files are zero bytes;
5. the exact frozen tracker entry is complete;
6. child run identity, accepted commit, and assumption evidence agree with Goal state.

Only then is the entry moved from `remaining_entries` to `completed_entries`.

### Step 7 — Transition to the next child

- `solo`: persist `NEXT_CHILD_CHAT_REQUIRED`, then use `/new` with the emitted `NEXT_CHAT_PROMPT`. If that UI transition is unavailable, create an app-native task in the same saved project with the same prompt. The fresh chat must run the exact `--claim-child-chat` command before the next child can be prepared.
- `solo-headless`: prepare the next child with a fresh shared native conversation.
- `delegate`: create a fresh inspectable P/E/R agent set for the next child.
- `delegate-headless` and `delegate-multi`: prepare a new Task run and new per-role native-session ledger.
- `manual`: return to the same Goal Orchestrator chat, then open a fresh dedicated P/E/R chat set for the next child.

The next child always starts from the latest clean accepted `main`. A missing, mismatched, or stale `solo` child-chat claim fails closed and cannot duplicate or skip a child.

### Step 8 — Finish Goal

When no frozen children remain, the Goal Controller rechecks every selected tracker entry, clean `main`, and absence of an active Task. It then records `GOAL_ACCEPTED`. A Goal creates no Goal branch or Goal commit; its durable history is the ordered child implementation and merge commits.

## Fully unattended Goal procedure

For unattended local execution and close-out, configure:

```toml
approval_policy = "unattended"

[unattended]
allow_execute = true
allow_local_commit = true
allow_local_merge = true
```

Then:

1. Run `goal-start` without any approval flags.
2. Complete or invoke each prepared role according to the selected mode. Unattended policy automates gates, not role transport.
3. After every Planner `PENDING_APPROVAL`, the controller records execute preauthorization and proceeds to Executor.
4. After every accepted Reviewer result reaches `PENDING_COMMIT`, the controller records commit/merge preauthorization and reuses that Reviewer conversation for close-out.
5. After verified child acceptance, transition to the next child using the mode-specific Step 7 procedure.
6. Repeat until `GOAL_ACCEPTED` or a real blocker/terminal condition is reported.

In IDE `solo` and `delegate`, continue to report each `[ROLE_READY]` completion with `goal-resume --role-complete`; `delegate` also supplies the bound app-agent ID. In `manual`, the operator still transports prompts between dedicated chats. In headless modes, role sessions run automatically. No mode requires intermediate owner gate messages when all three local permissions above are true.

## Goal CLI — all modes

Generate:

```bash
uv run .agents/make_goal.py --entries 7.1 7.2 7.3
uv run .agents/make_goal.py --phase 7
uv run .agents/make_goal.py --all-open
```

Start:

```bash
uv run .agents/orchestrator.py goal-start --goal-file .agents/goal.toml
```

Status:

```bash
uv run .agents/orchestrator.py goal-status
```

Resume active child:

```bash
uv run .agents/orchestrator.py goal-resume
```

In IDE `solo` or `delegate`, a child role pauses at `[ROLE_READY]`. Complete it using the same boundary flags as a standalone Task:

```bash
uv run .agents/orchestrator.py goal-resume --role-complete
uv run .agents/orchestrator.py goal-resume --role-complete --app-agent-id <opaque-id>
```

Relay the active child owner gates when required:

```bash
uv run .agents/orchestrator.py goal-resume --approved
uv run .agents/orchestrator.py goal-resume --approved-commit
uv run .agents/orchestrator.py goal-resume --reject-feedback "..."
uv run .agents/orchestrator.py goal-resume --reject-commit-feedback "..."
uv run .agents/orchestrator.py goal-resume --resolve-planner-blocker "..."
```

Those relay flags are for exact interactive owner messages. In unattended mode, omit them: the controller consults the policy frozen at Goal/child activation.

If an unattended headless correction loop exceeds `max_iterations` and recovery was enabled, the controller starts one fresh recovery generation with `codex/gpt-5.6-sol/high` and permits exactly one additional iteration. A second exhaustion blocks the child and Goal. No recovery identity carries into the next Task or Goal child. IDE and manual unattended runs stop at their configured iteration limit without spawning a recovery CLI session.

Cancel Goal supervision while preserving active child evidence:

```bash
uv run .agents/orchestrator.py goal-cancel --reason "..."
```

## Goal chat — Solo/Delegate

Activate with:

```text
Activate and run the Goal defined in .agents/goal.toml.

Read and follow:
- AGENTS.md
- .agents/GOALS.md
- .agents/ORCHESTRATOR.md
- .agents/PROCEDURE.md

Resolve the Goal selection against its implementation tracker and freeze the ordered child list. Do not perform Goal planning or product implementation yourself. Generate the first child .agents/task.toml and run that child through the normal Task workflow. Only after the child reaches verified ACCEPTED may the Goal supervisor generate the next child.

Do not add any owner authorization token beyond APPROVED: EXECUTE and APPROVED: COMMIT for the active child Task.
```

For `delegate`, if a child becomes `ACCEPTED` and another user turn is required to start the next child, send:

```text
CONTINUE: GOAL
```

This is transport/resume only. Orchestrator must verify the previous child is truly `ACCEPTED`, main is clean, active Task files are zero bytes and the frozen tracker entry is complete before generating the next child.

For `solo`, an accepted non-final child instead emits `NEXT_CHILD_CHAT : REQUIRED` after that verification and checkpoint. The current chat must not execute the next child. Use `/new` and submit the emitted `NEXT_CHAT_PROMPT`. If `/new` cannot be driven, create an app-native task in the same saved project with that prompt. The new chat runs the emitted command containing `--claim-child-chat <handoff-id>`; the exact claim is mandatory and idempotently protects the boundary from a failed first transport attempt.

In IDE `delegate`, every new child receives a fresh inspectable app-native P/E/R agent set. Later iterations inside that child reuse that child's existing role handles.

## Goal manual mode

Keep **one Goal Orchestrator chat for the whole Goal**. Do not keep one Planner/Executor/Reviewer chat set for the whole Goal.

For Child 1:

- open Planner Child-1 chat;
- open Executor Child-1 chat;
- open Reviewer Child-1 chat;
- reuse those three chats only for Child 1 correction iterations;
- Reviewer Child-1 chat performs Child-1 close-out.

After Child 1 is verified `ACCEPTED`, return to the same Goal Orchestrator chat. It generates Child 2 and instructs you to open a **new dedicated Planner/Executor/Reviewer chat set**. Repeat for every child.

Expected between-child Goal status:

```text
GOAL : RUNNING
CURRENT_CHILD : NONE
AWAITING : NEXT_FROZEN_CHILD
```

Expected terminal status:

```text
GOAL : ACCEPTED
CURRENT_CHILD : NONE
REMAINING : NONE
```

With the default `stop_on_blocked=true`, a child Planner `BLOCKED` pauses Goal progression. With `stop_on_blocked=false` under frozen unattended policy, the controller gives that same Planner one bounded retry for explicit repository-grounded assumptions and records the accepted Reviewer's `Assumptions for Human Review` section in Goal state. It never skips the child or assumes protected authority/external facts; a repeated or protected blocker still pauses for human resolution. A child cancellation/max-iterations/reconciliation failure blocks Goal supervision and never silently skips frozen scope.

---

## Part 5 — Maintenance and Diagnostics

```bash
uv run .agents/orchestrator.py doctor
uv run --frozen pytest --no-cov .agents/tests
uv run .agents/orchestrator.py self-test
uv run --frozen ruff format --check .agents
uv run --frozen ruff check .agents
uv run --frozen mypy
```

Goal-focused checks:

```bash
uv run --frozen pytest --no-cov .agents/tests/test_goals.py
uv run --frozen pytest --no-cov .agents/tests/test_goal_integration.py
```

Native session resumption is never replaced by transcript replay or implicit latest-session heuristics. Goal supervision never stores or reuses child role-session IDs.

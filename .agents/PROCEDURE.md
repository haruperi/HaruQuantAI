# Agent Workflow — Complete Operational Procedures

HaruQuantAI has one atomic Planner → Executor → Reviewer Task workflow and one deterministic Goal supervisor above it. All four transport modes share the same Task/Goal semantics; only transport changes.

A Task run owns one Planner conversation, one Executor conversation and one Reviewer conversation. Later iterations reuse those same-role conversations. A new Task — including the next child inside a Goal — gets a fresh P/E/R conversation set.

The only owner authorization messages are:

```text
APPROVED: EXECUTE
APPROVED: COMMIT
```

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
```

`task.toml` and `goal.toml` are runtime input only. Their presence does not activate work.

---

# Part 1 — Standalone Task: Chat-Driven Solo/Delegate

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
Continue until owner action is required.
Do not execute implementation before my exact:

APPROVED: EXECUTE
```

Expected gate:

```text
STOPPED : PLANNER
ACTIVATING : EXECUTOR
HANDOFF : PENDING_APPROVAL
```

## Step 3 — Owner execution decision

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

## Step 7 — Owner commit decision

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

## Step 8 — Reviewer close-out

After exact commit authorization, close-out continues the same Reviewer conversation. It re-verifies reviewed identity, confirms archived evidence, runs final gates, stages only approved implementation paths, creates exactly one Task commit, clears coordination files only after commit success, verifies Task branch/main/lineage/path authority, ff-only merges, safely deletes the merged Task branch and marks `ACCEPTED`.

```text
STOPPED : REVIEWER
ACTIVATING : NONE
HANDOFF : ACCEPTED
```

---

# Part 2 — Standalone Task: Multi-Delegate CLI

Doctor:

```bash
uv run .agents/orchestrator.py doctor
```

Start:

```bash
uv run .agents/orchestrator.py start --task-file .agents/task.toml
```

Resume/gates:

```bash
uv run .agents/orchestrator.py resume
uv run .agents/orchestrator.py resume --approved
uv run .agents/orchestrator.py resume --reject-feedback "..."
uv run .agents/orchestrator.py resume --resolve-planner-blocker "..."
uv run .agents/orchestrator.py resume --approved-commit
uv run .agents/orchestrator.py resume --reject-commit-feedback "..."
```

Each role turn may be a fresh OS process, but `.agents/session_runner.py` resumes the exact stored native role conversation for the Task run. Reviewer close-out reuses the Reviewer session.

---

# Part 3 — Standalone Task: Manual Mode

For one Task maintain four chats:

1. Orchestrator.
2. Planner.
3. Executor.
4. Reviewer, also used for close-out.

On first use of a role, open its dedicated chat and paste the entire exact current `.agents/task/next-agent.md`. On later iterations return to that same role chat.

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

---

# Part 4 — Goal Orchestration

A Goal supervises multiple ordinary Tasks sequentially. Read `.agents/GOALS.md` before operating a Goal.

## Goal invariants

- Goal Controller is deterministic, not an LLM reasoning role.
- Selection resolves once and freezes at Goal activation.
- Exactly one child Task may be active.
- Every child uses the normal Task workflow unchanged and produces its own commit.
- Goal has no Goal branch, Goal commit, Planner/Executor/Reviewer session, or additional owner gate.
- Same-role continuity exists only inside a child Task; next child starts a fresh P/E/R set.
- Goal advances only after child `ACCEPTED` plus clean-main/zero-byte-workspace/tracker reconciliation.

## Goal CLI — multi-delegate

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

Relay the active child owner gates when required:

```bash
uv run .agents/orchestrator.py goal-resume --approved
uv run .agents/orchestrator.py goal-resume --approved-commit
uv run .agents/orchestrator.py goal-resume --reject-feedback "..."
uv run .agents/orchestrator.py goal-resume --reject-commit-feedback "..."
uv run .agents/orchestrator.py goal-resume --resolve-planner-blocker "..."
```

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

If a child becomes `ACCEPTED` and another user turn is required to start the next child, send:

```text
CONTINUE: GOAL
```

This is transport/resume only. Orchestrator must verify the previous child is truly `ACCEPTED`, main is clean, active Task files are zero bytes and the frozen tracker entry is complete before generating the next child.

In Delegate mode, every new child receives a fresh P/E/R delegate set. Later iterations inside that child reuse that child's existing role handles.

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

A child Planner `BLOCKED` pauses Goal progression; resolve and resume that same child. A child cancellation/max-iterations/reconciliation failure blocks Goal supervision and never silently skips frozen scope.

---

# Part 5 — Maintenance and Diagnostics

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

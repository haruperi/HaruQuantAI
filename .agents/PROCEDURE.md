# Agent Workflow — Complete Operational Procedures

This document provides end-to-end operating procedures for all four HaruQuantAI transport modes. Every mode shares the same protocol, role contracts, state machine, owner gates, iteration semantics, and **same-role session continuity**. Only the transport/channel changes.

A workflow run owns one logical Planner conversation, one Executor conversation, and one Reviewer conversation. Iteration N+1 returns to that same role conversation. New tasks start new role conversations.

Choose the matching transport:

- **Part 1 — Chat-Driven Orchestration:** `solo` and `delegate`.
- **Part 2 — CLI-Driven Orchestration:** `multi-delegate`.
- **Part 3 — Manual Mode:** one Orchestrator chat plus persistent Planner, Executor and Reviewer chats.
- **Part 4 — Maintenance & Diagnostics.**

---

## Common Prerequisites

### 1. Configure Orchestration Mode

```bash
uv run .agents/configure.py
```

Mode changes transport and transport automation only. Repository evidence and deterministic controller state remain authoritative; same-role conversation history is context only. Every invocation still receives the complete current `.agents/task/next-agent.md`.

### 2. Generate or Prepare the Task Specification

```bash
uv run .agents/make_task.py --list
uv run .agents/make_task.py 1.1
```

For a custom task, author `.agents/task.toml` from `.agents/task.example.toml`. Merely creating `task.toml` does not activate work.

```text
ORCHESTRATOR : READY
TASK_SPEC : READY
TASK : NOT_ACTIVE
```

---

## Part 1 — Chat-Driven Orchestration (Solo and Delegate Modes)

Solo uses one physical chat with soft role isolation. Delegate uses one dedicated same-brand delegate handle per role for the task. In Delegate mode, later Planner/Executor/Reviewer iterations resume their existing role delegate instead of creating another role conversation. If the host cannot resume a required handle, report the transport limitation rather than silently substituting a new one.

```text
ORCHESTRATOR READY / TASK NONE
  → Step 1: Initialize Chat Orchestrator
  → Step 2: Activate Task & Run Planner
  → Step 3: Owner Execution Decision (APPROVED: EXECUTE)
  → Step 4: (Optional) Resolve Planner Blockers
  → Step 5: Run Executor & Transition to Reviewer
  → Step 6: Reviewer Verification & Findings
  → Step 7: Owner Commit Decision (APPROVED: COMMIT)
  → Step 8: Reviewer Close-Out & Acceptance
```

### Chat Step 1 — Initialize the Orchestrator Chat

Paste:

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

### Chat Step 2 — Activate the Task and Run Planner

```text
Activate and run the task defined in .agents/task.toml.

Use AGENTS.md, .agents/ORCHESTRATOR.md and .agents/protocol.toml.
Treat .agents/task.toml as authoritative runtime task input.

1. validate the clean-main entry gate;
2. record the main baseline commit;
3. derive/create/switch to the deterministic task branch;
4. instantiate the canonical Planner contract into .agents/task/next-agent.md;
5. validate ORCHESTRATOR / TASK_ACTIVATED -> PLANNER;
6. activate the Planner using the exact complete next-agent.md.

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

### Chat Step 3 — Owner Execution Decision

Approve:

```text
APPROVED: EXECUTE
```

Reject:

```text
REJECTED: EXECUTE

Owner direction:
<describe exactly what must change in the dry run>
```

Rejection materializes a fresh Planner correction **prompt**, but later Planner iterations resume the same Planner conversation for this workflow run.

### Chat Step 4 — Handle Planner Blockers

After resolving a Planner blocker:

```text
RESOLVED: PLANNER BLOCKER

Resolution evidence:
<what changed and where the Planner can verify it>
```

The old pending prompt is stale. The orchestrator records evidence, verifies current state, materializes a fresh canonical `ORCHESTRATOR / BLOCKER_RESOLVED → PLANNER` prompt, validates it, and resumes the same Planner role conversation. Resolution does not authorize execution.

Executor `BLOCKED` and Reviewer `CHANGES_REQUESTED` route automatically to the same Planner conversation with a new complete current prompt.

### Chat Step 5 — Run Executor and Transition to Reviewer

Executor success yields:

```text
STOPPED : EXECUTOR
ACTIVATING : REVIEWER
HANDOFF : READY_FOR_REVIEW
```

`READY_FOR_REVIEW` is already a valid protocol transition. If Solo chat requires another user turn, send:

```text
CONTINUE: REVIEWER
```

This is **transport/resume only**: the owner is not approving the implementation. The orchestrator validates the existing Reviewer prompt/state and begins Reviewer Stage A. Delegate activates or resumes its dedicated Reviewer handle without an owner approval gate.

### Chat Step 6 — Reviewer Verification and Findings

Reviewer always performs:

1. Stage A — independent reconstruction from current repository evidence before upstream journals.
2. Stage B — independent tests/quality/architecture verification.
3. Stage C — only then reconcile Planner/Executor journals and hashes.

Persistent Reviewer history from Review N-1 is context only and cannot substitute for Stage A/B in Review N.

Outcomes:

- `CHANGES_REQUESTED` → resume same Planner conversation for Dry Run N+1.
- `PENDING_COMMIT` → owner commit gate.

### Chat Step 7 — Owner Commit Decision

Approve:

```text
APPROVED: COMMIT
```

Reject:

```text
REJECTED: COMMIT

Owner direction:
<describe why the reviewed state must not be committed and what must change>
```

### Chat Step 8 — Reviewer Close-Out and Acceptance

After exact `APPROVED: COMMIT`, close-out continues the same Reviewer role conversation. It re-verifies reviewed identity, confirms archived evidence, runs final gates, stages only approved implementation paths, creates exactly one task commit, only then clears the four coordination files, verifies task branch/main/lineage/path authority, ff-only merges, safely deletes the merged branch, and marks `ACCEPTED`.

```text
STOPPED : REVIEWER
ACTIVATING : NONE
HANDOFF : ACCEPTED
```

---

## Part 2 — CLI-Driven Orchestration (Multi-Delegate Mode)

Every role turn launches a headless process, but each role retains one native conversation for the workflow run. `.agents/session_runner.py` stores exact role IDs under `.agents/runs/<run-id>/role-sessions.json` and resumes them explicitly.

```text
Planner process 1 → session P
Planner process 2 → resume P
Executor process 1 → session E
Executor process 2 → resume E
Reviewer process 1 → session R
Reviewer process 2 / close-out → resume R
```

P, E and R must remain different identities. A returned resume ID that differs from the stored ID fails closed. `--last`/`--continue` heuristics are not used when the exact ID is known.

### CLI Step 1 — Verify Environment and Installation

```bash
uv run .agents/orchestrator.py doctor
```

Doctor validates templates/protocol/workspace plus the session-continuity policy, session runner, configured native CLI, and declared exact-ID resume capability. A missing required capability fails strict multi-delegate readiness.

### CLI Step 2 — Activate Task and Run Planner

```bash
uv run .agents/orchestrator.py start --task-file .agents/task.toml
```

The first Planner invocation establishes and stores Planner's native session ID, then pauses at `PENDING_APPROVAL`.

### CLI Step 3 — Owner Execution Decision

```bash
uv run .agents/orchestrator.py resume --approved
```

or:

```bash
uv run .agents/orchestrator.py resume --reject-feedback "<required changes>"
```

A later Planner iteration resumes the stored Planner session rather than creating a new one.

### CLI Step 4 — Planner Blocker Resolution

```bash
uv run .agents/orchestrator.py resume --resolve-planner-blocker "<resolution evidence>"
```

The controller creates a fresh current Planner **prompt** but resumes the existing Planner **conversation**.

### CLI Step 5 — Executor → Reviewer

After approval, first Executor establishes E. Later Executor iterations resume E. On `READY_FOR_REVIEW`, first Reviewer establishes R; later Reviews resume R automatically. No transport input or owner gate exists between Executor and Reviewer.

### CLI Step 6 — Reviewer Verification

The same three anti-anchoring stages apply on every resumed Reviewer iteration. Session memory is never review evidence.

### CLI Step 7 — Owner Commit Decision

```bash
uv run .agents/orchestrator.py resume --approved-commit
```

or:

```bash
uv run .agents/orchestrator.py resume --reject-commit-feedback "<reason>"
```

### CLI Step 8 — Reviewer Close-Out

Authorized close-out resumes Reviewer session R, not a new fourth role conversation. Success ends at `ACCEPTED`; all four task files are zero bytes.

### CLI Command Reference

| Command | Purpose |
| --- | --- |
| `uv run .agents/orchestrator.py doctor` | Validate workflow plus native role-session continuity readiness |
| `uv run .agents/orchestrator.py self-test` | Isolated protocol/controller self-test |
| `uv run .agents/orchestrator.py start --task-file .agents/task.toml` | Activate task and first Planner turn |
| `uv run .agents/orchestrator.py resume` | Continue a paused non-gated run using stored same-role sessions |
| `uv run .agents/orchestrator.py resume --resolve-planner-blocker "..."` | Fresh blocked-Planner prompt; same Planner conversation |
| `uv run .agents/orchestrator.py resume --approved` | `APPROVED: EXECUTE` |
| `uv run .agents/orchestrator.py resume --reject-feedback "..."` | Reject execution and return to Planner |
| `uv run .agents/orchestrator.py resume --approved-commit` | `APPROVED: COMMIT`; close-out resumes Reviewer |
| `uv run .agents/orchestrator.py resume --reject-commit-feedback "..."` | Reject commit and return to Planner |

---

## Part 3 — Full Manual Mode Procedure

Manual mode uses four persistent chats **per workflow run**:

1. Orchestrator chat.
2. Planner chat.
3. Executor chat.
4. Reviewer chat, also used for authorized close-out.

On the first invocation of a role, open its dedicated chat. On iteration N+1, return to that **existing role chat** and paste the complete current `.agents/task/next-agent.md`. Never reuse these chats for a new workflow run.

### Manual Step 1 — Initialize the Orchestrator Chat

Open one dedicated orchestrator chat and paste:

```text
Initialize the HaruQuantAI development orchestrator for this repository in MANUAL mode.

Read and follow:
- AGENTS.md
- .agents/ORCHESTRATOR.md
- .agents/protocol.toml
- .agents/README.md

You are the orchestration controller only.
Do not act as Planner, Executor, or Reviewer.
Do not activate a task yet.

For this workflow run I will maintain four chats: this Orchestrator chat plus one persistent Planner chat, one persistent Executor chat, and one persistent Reviewer chat. When a role has another iteration, instruct me to return to that existing role chat and paste the complete current .agents/task/next-agent.md.

When ready, report:
ORCHESTRATOR : READY
MODE : MANUAL
TASK : NONE
AWAITING : TASK_SPEC
```

### Manual Step 2 — Activate Task and First Planner Turn

In the orchestrator chat:

```text
Activate the task defined in .agents/task.toml.
Perform the normal TASK_ACTIVATED transition, create the deterministic task branch, materialize and validate the complete initial Planner prompt in .agents/task/next-agent.md, but do not perform Planner reasoning yourself.
```

Expected instruction:

```text
ORCHESTRATOR : READY_FOR_TRANSPORT
TARGET_ROLE : PLANNER
HANDOFF : TASK_ACTIVATED
PROMPT : .agents/task/next-agent.md
ACTION : OPEN_DEDICATED_PLANNER_CHAT
```

Open the Planner chat once, paste the exact complete prompt, and keep that chat for the task. After it finishes, return to Orchestrator and say:

```text
Planner invocation has finished.
Validate the latest Planner journal and .agents/task/next-agent.md and route according to .agents/protocol.toml.
```

### Manual Step 3 — Owner Execution Decision

Approve with `APPROVED: EXECUTE`, or reject with:

```text
REJECTED: EXECUTE

Owner direction:
<required dry-run changes>
```

If rejected, the orchestrator creates a fresh Planner correction prompt and instructs you to return to the **existing Planner chat**.

After approval the first Executor instruction is:

```text
ORCHESTRATOR : READY_FOR_TRANSPORT
TARGET_ROLE : EXECUTOR
HANDOFF : PENDING_APPROVAL
PROMPT : .agents/task/next-agent.md
ACTION : OPEN_DEDICATED_EXECUTOR_CHAT
```

### Manual Step 4 — Planner Blockers

After external resolution send:

```text
RESOLVED: PLANNER BLOCKER

Resolution evidence:
<what changed and where the Planner can verify it>
```

The orchestrator replaces the stale prompt with a fresh canonical `BLOCKER_RESOLVED` Planner prompt and tells you to return to the **existing Planner chat**.

### Manual Step 5 — Executor and Reviewer Transport

Use the existing Executor chat for every Report N. Paste the complete current prompt. After Executor finishes, return to Orchestrator:

```text
Executor invocation has finished.
Validate the latest Executor journal and .agents/task/next-agent.md and route according to .agents/protocol.toml.
```

First Reviewer use yields:

```text
ORCHESTRATOR : READY_FOR_TRANSPORT
TARGET_ROLE : REVIEWER
HANDOFF : READY_FOR_REVIEW
PROMPT : .agents/task/next-agent.md
ACTION : OPEN_DEDICATED_REVIEWER_CHAT
```

Open Reviewer once and keep it. Every later Review N returns to this **existing Reviewer chat**.

### Manual Step 6 — Reviewer Findings

After Reviewer finishes, return to Orchestrator:

```text
Reviewer invocation has finished.
Validate the latest Reviewer journal and .agents/task/next-agent.md and route according to .agents/protocol.toml.
```

`CHANGES_REQUESTED` sends you back to the **existing Planner chat**. When execution is later re-approved, use the **existing Executor chat**. When implementation returns for review, use the **existing Reviewer chat**.

### Manual Step 7 — Owner Commit Decision

At `PENDING_COMMIT`, approve:

```text
APPROVED: COMMIT
```

or reject:

```text
REJECTED: COMMIT

Owner direction:
<why the reviewed state must change>
```

Approval yields:

```text
ORCHESTRATOR : READY_FOR_TRANSPORT
TARGET_ROLE : REVIEWER
HANDOFF : PENDING_COMMIT
PROMPT : .agents/task/next-agent.md
ACTION : RETURN_TO_REVIEWER_CHAT
```

### Manual Step 8 — Reviewer Close-Out and Acceptance

Return to the **existing Reviewer chat** that performed Review N and paste the complete close-out prompt. Do not open another close-out chat. The same Reviewer context continues, while the new prompt and repository state remain authoritative.

After it finishes, return to Orchestrator:

```text
Reviewer close-out has finished.
Validate terminal workflow state and confirm whether the task is ACCEPTED and the orchestrator has returned to READY.
```

Expected terminal state:

```text
ORCHESTRATOR : READY
LAST_TASK : ACCEPTED
TASK : NONE
AWAITING : TASK_SPEC
```

All four active-task workspace files must be zero bytes. A new task starts a new set of role chats.

---

## Part 4 — Maintenance and Diagnostics

```bash
uv run .agents/orchestrator.py doctor
uv run --frozen pytest --no-cov .agents/tests
uv run .agents/orchestrator.py self-test
uv run --frozen ruff format --check .agents
uv run --frozen ruff check .agents
uv run --frozen mypy
```

`doctor` is the multi-delegate readiness gate. Native session resumption is never replaced with transcript replay or an implicit latest-session heuristic.

# Agent Workflow — Full Procedure

This procedure distinguishes **orchestrator initialization**, **task specification**, and **task activation**. A task specification existing on disk does not activate work. No reasoning role may run until its complete prompt has been materialized into `.agents/task/next-agent.md` and validated against `.agents/protocol.toml`.

## Prerequisite — Configure orchestration mode

Run this initially, or whenever you want to change transport mode:

```bash
uv run .agents/configure.py
```

Choose `solo`, `delegate`, `multi-delegate`, or `manual`. Mode changes transport only; every reasoning role consumes the same validated `.agents/task/next-agent.md` artifact.

---

## Step 1 — Start / initialize the orchestrator

### Chat-driven orchestration

For `solo`, `delegate`, or chat-controlled `multi-delegate`, open a fresh orchestrating chat and paste exactly:

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
Do not modify implementation files.
Do not modify any .agents/task/ journal.
Do not infer a task from previous chat history.

Verify that the repository and active-task workspace are in a valid idle state.

When initialization is complete, stop and report:

ORCHESTRATOR : READY
TASK : NONE
AWAITING : TASK_SPEC
```

Expected idle state:

```text
ORCHESTRATOR : READY
TASK : NONE
AWAITING : TASK_SPEC
```

### Direct multi-delegate CLI

The CLI does not need a persistent chat initialization step. Validate the installation first:

```bash
uv run .agents/orchestrator.py doctor
```

Do not run `start` until the task specification in Step 2 is ready.

---

## Step 2 — Generate / prepare the task specification

For implementation-order tasks:

```bash
uv run .agents/make_task.py --list
uv run .agents/make_task.py 1.1
```

This writes runtime-only `.agents/task.toml`. Review or edit it before activation if needed.
Note that .agents/make_task.py is hardcoded to only recognize product features (FEAT-...)
and functional requirements (FR-...), other tasks not matching this like foundation task.
Manually author .agents/task.toml with task_kind = "task" (rather than "feature"):

At this point:

```text
ORCHESTRATOR : READY
TASK_SPEC : READY
TASK : NOT_ACTIVE
```

The presence of `.agents/task.toml` alone never creates a branch or invokes a role.

---

## Step 3 — Activate the task / start orchestration

Task activation is deterministic orchestration, not Planner reasoning. It:

1. validates the clean-`main` entry gate;
2. records the baseline commit;
3. derives and validates the deterministic task branch;
4. creates and switches to that branch from the baseline;
5. instantiates the canonical Planner prompt into `.agents/task/next-agent.md`;
6. validates `ORCHESTRATOR / TASK_ACTIVATED -> PLANNER`;
7. only then invokes or transports Planner using that exact artifact.

### Chat-driven activation text

Paste exactly into the initialized orchestrator chat:

```text
Activate and run the task defined in .agents/task.toml.

Use the HaruQuantAI workflow defined by:
- AGENTS.md
- .agents/ORCHESTRATOR.md
- .agents/protocol.toml

Treat .agents/task.toml as the authoritative runtime task input.

Perform the task activation sequence:

1. validate the clean-main entry gate;
2. record the main baseline commit;
3. derive and validate the deterministic task branch;
4. create and switch to that task branch from the recorded baseline;
5. instantiate the canonical Planner prompt into .agents/task/next-agent.md;
6. validate the ORCHESTRATOR / TASK_ACTIVATED -> PLANNER transition and the complete next-agent artifact;
7. only after successful validation, activate Planner using the exact contents of .agents/task/next-agent.md.

Planner must not recreate or switch the task branch.

Continue orchestration until owner action is required.

Do not execute implementation before my exact:

APPROVED: EXECUTE
```

### Direct multi-delegate activation

```bash
uv run .agents/orchestrator.py start --task-file .agents/task.toml
```

The CLI performs the same `TASK_ACTIVATED` transition and then invokes Planner from the validated `next-agent.md` artifact.

Expected first owner gate:

```text
STOPPED : PLANNER
ACTIVATING : EXECUTOR
HANDOFF : PENDING_APPROVAL
```

Executor is not invoked before owner authorization.

---

## Step 4 — Owner execution decision

### Approve execution

When the latest Planner handoff is `PENDING_APPROVAL`, approve only with the exact standalone message:

```text
APPROVED: EXECUTE
```

The orchestrator appends the deterministic approval record and invokes the already-materialized Executor prompt. Planner is not re-invoked merely to record approval.

CLI equivalent:

```bash
uv run .agents/orchestrator.py resume --approved
```

### Reject the dry run

Recommended chat convention:

```text
REJECTED: EXECUTE

Owner direction:
<describe exactly what must change in the dry run>
```

`REJECTED: EXECUTE` is a user-facing convention, not a protocol authorization token. The orchestrator must route the owner direction into a fresh canonical Planner correction prompt.

CLI equivalent:

```bash
uv run .agents/orchestrator.py resume --reject-feedback "<owner direction>"
```

---

## Step 5 — Planner blocker requiring owner action

If Planner returns `BLOCKED`, the workflow stops until the documented external cause is resolved.

Recommended chat response after resolving the blocker in an authoritative repository/task source or other externally verifiable condition:

```text
RESOLVED: PLANNER BLOCKER

Resolution evidence:
<what changed and where the Planner can verify it>
```

This is a user-facing convention, not an approval token. The existing Planner retry artifact is not rewritten with free-form chat instructions. The orchestrator verifies that the documented external cause is now resolved, then resumes Planner from that already-validated artifact. Direct CLI mode likewise resolves the external cause first, then uses `uv run .agents/orchestrator.py resume`; it has no separate blocker-feedback flag. If the requested resolution would change task scope or authority rather than merely resolve the documented external cause, do not resume the blocked prompt as-is; prepare a newly authorized task/replan path instead.

Executor `BLOCKED` does **not** automatically require owner intervention. It first routes to Planner for blocker-resolution planning. Owner action is needed only if Planner then becomes `BLOCKED` or later reaches `PENDING_APPROVAL`.

---

## Step 6 — Execute and review

Executor implements only the approved scope and produces either:

- `READY_FOR_REVIEW` with a complete Reviewer prompt; or
- `BLOCKED` with a complete Planner blocker-resolution prompt.

Reviewer independently reconstructs and verifies before reading upstream journals. Reviewer produces either:

- `CHANGES_REQUESTED` with a complete Planner correction prompt; or
- `PENDING_COMMIT` with a complete gated Reviewer close-out prompt.

`READY_FOR_REVIEW`, Executor `BLOCKED`, and Reviewer `CHANGES_REQUESTED` are normally routed automatically. The owner acts again only at a later Planner gate/blocker or at `PENDING_COMMIT`.

---

## Step 7 — Owner commit decision

### Approve commit / close-out

When Reviewer reaches `PENDING_COMMIT`, approve only with the exact standalone message:

```text
APPROVED: COMMIT
```

Before invoking close-out, the orchestrator rechecks the exact pending prompt, reviewed HEAD, and complete working-tree fingerprint.

CLI equivalent:

```bash
uv run .agents/orchestrator.py resume --approved-commit
```

### Reject commit authorization

Recommended chat convention:

```text
REJECTED: COMMIT

Owner direction:
<describe why the reviewed state must not be committed and what must change>
```

The previous review no longer authorizes close-out. The orchestrator creates a fresh canonical Planner correction prompt.

CLI equivalent:

```bash
uv run .agents/orchestrator.py resume --reject-commit-feedback "<owner direction>"
```

---

## Step 8 — Reviewer close-out

After exact `APPROVED: COMMIT`, Reviewer performs only the authorized administrative close-out:

1. re-verifies unchanged reviewed state;
2. records authorization;
3. empties all four `.agents/task/` files;
4. stages only approved work;
5. creates one local task commit;
6. verifies clean unchanged `main`;
7. fast-forward merges only;
8. verifies the merge;
9. safely deletes the merged branch.

Normal workflow never pushes.

Success ends:

```text
STOPPED : REVIEWER
ACTIVATING : NONE
HANDOFF : ACCEPTED
```

At the session level, accepted close-out returns to:

```text
ORCHESTRATOR : READY
LAST_TASK : ACCEPTED
TASK : NONE
AWAITING : TASK_SPEC
```

The task terminates; the orchestrator remains ready for another task.

If close-out preconditions fail, Reviewer does not repair. It returns `CHANGES_REQUESTED` with a complete Planner prompt.

---

## Step 9 — Resume commands

```bash
uv run .agents/orchestrator.py resume
uv run .agents/orchestrator.py resume --approved
uv run .agents/orchestrator.py resume --reject-feedback "..."
uv run .agents/orchestrator.py resume --approved-commit
uv run .agents/orchestrator.py resume --reject-commit-feedback "..."
```

Run state and logs are runtime-only under `.agents/runs/` and `.agents/logs/`.

---

# Full manual mode procedure

Manual mode uses the identical protocol and artifacts. The only difference is transport: the owner carries the exact `.agents/task/next-agent.md` between fresh role chats.

## Manual Step 1 — Initialize the manual orchestrator chat

Open one chat that remains the orchestration controller. Paste exactly:

```text
Initialize the HaruQuantAI development orchestrator for this repository in MANUAL mode.

Read and follow:
- AGENTS.md
- .agents/ORCHESTRATOR.md
- .agents/protocol.toml
- .agents/README.md

You are the orchestration controller only.

Do not act as Planner, Executor, or Reviewer.
Do not implement or review work yourself.
Do not activate a task yet.

In manual mode, I will transport the exact contents of .agents/task/next-agent.md into fresh role chats when you instruct me to do so.

You must:
- validate workflow state;
- tell me exactly which role chat to open;
- tell me exactly which file to paste;
- process owner gates;
- never summarize or reconstruct a role prompt when .agents/task/next-agent.md already exists.

When ready, report:

ORCHESTRATOR : READY
MODE : MANUAL
TASK : NONE
AWAITING : TASK_SPEC
```

## Manual Step 2 — Generate and inspect the task specification

```bash
uv run .agents/make_task.py --list
uv run .agents/make_task.py 1.1
```

Review `.agents/task.toml` before activation.

## Manual Step 3 — Activate the task

Return to the manual orchestrator chat and paste exactly:

```text
Activate the task defined in .agents/task.toml.

Perform the normal HaruQuantAI TASK_ACTIVATED transition.

Create the deterministic task branch and materialize the complete initial Planner prompt into:

.agents/task/next-agent.md

Because this is MANUAL mode, do not invoke Planner yourself.

Validate the artifact and then instruct me to open a fresh Planner chat and paste the exact contents of .agents/task/next-agent.md unchanged.
```

Expected transport instruction:

```text
ORCHESTRATOR : READY_FOR_TRANSPORT
TARGET_ROLE : PLANNER
HANDOFF : TASK_ACTIVATED
PROMPT : .agents/task/next-agent.md
ACTION : OPEN_FRESH_PLANNER_CHAT
```

## Manual Step 4 — Run Planner in a fresh chat

Open a **new Planner chat** and paste the entire exact contents of:

```text
.agents/task/next-agent.md
```

Paste nothing before or after it. The file itself is the role prompt.

After Planner stops, return to the orchestrator chat and paste:

```text
Planner invocation has finished.

Validate the latest Planner journal and .agents/task/next-agent.md and route the workflow according to .agents/protocol.toml.
```

If Planner is `PENDING_APPROVAL`, respond with exact `APPROVED: EXECUTE` or the rejection convention from Step 4. If Planner is `BLOCKED`, use the blocker-resolution convention from Step 5.

## Manual Step 5 — Run Executor in a fresh chat

After `APPROVED: EXECUTE`, the orchestrator must validate the existing Executor artifact and instruct transport.

Open a **new Executor chat** and paste the entire exact contents of:

```text
.agents/task/next-agent.md
```

After Executor stops, return to the orchestrator chat and paste:

```text
Executor invocation has finished.

Validate the latest Executor journal and .agents/task/next-agent.md and route the workflow according to .agents/protocol.toml.
```

If Executor returns `READY_FOR_REVIEW`, proceed to a fresh Reviewer chat. If it returns `BLOCKED`, proceed to a fresh Planner chat using the newly materialized Planner artifact. Do not manually reconstruct either prompt.

## Manual Step 6 — Run Reviewer in a fresh chat

Open a **new Reviewer chat** and paste the entire exact contents of:

```text
.agents/task/next-agent.md
```

After Reviewer stops, return to the orchestrator chat and paste:

```text
Reviewer invocation has finished.

Validate the latest Reviewer journal and .agents/task/next-agent.md and route the workflow according to .agents/protocol.toml.
```

If Reviewer returns `CHANGES_REQUESTED`, open a fresh Planner chat and paste the exact new `next-agent.md`. If Reviewer returns `PENDING_COMMIT`, provide exact `APPROVED: COMMIT` or the commit-rejection convention from Step 7.

## Manual Step 7 — Run authorized Reviewer close-out in a fresh chat

After exact `APPROVED: COMMIT`, the orchestrator validates the gated close-out artifact.

Open a **new Reviewer close-out chat** and paste the entire exact contents of:

```text
.agents/task/next-agent.md
```

This is a separate invocation from independent review even though the target role remains Reviewer. Its authority is limited to the canonical `reviewer-closeout.md` contract.

After close-out stops, return to the orchestrator chat and paste:

```text
Reviewer close-out has finished.

Validate terminal workflow state and confirm whether the task is ACCEPTED and the orchestrator has returned to READY.
```

Expected success:

```text
ORCHESTRATOR : READY
LAST_TASK : ACCEPTED
TASK : NONE
AWAITING : TASK_SPEC
```

All four active-task files must be zero bytes.

---

## Maintenance

```bash
uv run .agents/orchestrator.py doctor
uv run .agents/orchestrator.py self-test
```

`doctor` validates protocol/templates/workspace and rejects obsolete workflow paths. `self-test` exercises initial artifact-driven Planner activation, blocker/correction paths, owner gates, review rejection, and successful close-out in an isolated temporary Git repository.

# Agent Workflow — Full Procedure

## Step 0 — Configure a mode

```bash
uv run .agents/configure.py
```

Choose `solo`, `delegate`, `multi-delegate`, or `manual`. Mode changes execution transport only; every role receives the same artifact contract.

## Step 1 — Generate a task spec

```bash
uv run .agents/make_task.py --list
uv run .agents/make_task.py 1.1
```

This writes runtime-only `.agents/task.toml`.

## Step 2 — Start

For modes 1–3, open a fresh orchestrating chat and instruct it to read `AGENTS.md`, `.agents/ORCHESTRATOR.md`, `.agents/protocol.toml`, and `.agents/task.toml`.

For multi-delegate directly:

```bash
uv run .agents/orchestrator.py doctor
uv run .agents/orchestrator.py start --task-file .agents/task.toml
```

Planner creates the task branch, appends the numbered dry run to `.agents/task/planner.md`, and writes the full gated Executor prompt to `.agents/task/next-agent.md`.

## Step 3 — Owner execution gate

Approve only with exact standalone text:

```text
APPROVED: EXECUTE
```

The orchestrator appends a deterministic approval record containing task, iteration, branch, baseline, and plan SHA-256. Planner is not re-invoked merely to record approval.

On rejection, owner feedback is used to instantiate a fresh canonical Planner correction prompt.

## Step 4 — Execute and review

Executor implements only approved scope and writes either:

- full Reviewer prompt (`READY_FOR_REVIEW`), or
- full Planner blocker-resolution prompt (`BLOCKED`).

Reviewer independently reconstructs and verifies before reading upstream journals. It writes either:

- full Planner correction prompt (`CHANGES_REQUESTED`), or
- full gated Reviewer close-out prompt (`PENDING_COMMIT`).

## Step 5 — Owner commit gate

Approve only with exact standalone text:

```text
APPROVED: COMMIT
```

Before invoking close-out, the orchestrator rechecks the exact pending prompt, reviewed HEAD, and complete working-tree fingerprint.

## Step 6 — Close-out

Reviewer verifies unchanged reviewed state, records authorization, empties all four `.agents/task/` files, stages only approved work, creates one local task commit, verifies clean unchanged `main`, fast-forward merges, verifies the merge, and deletes the merged branch safely. Normal workflow never pushes.

## Step 7 — Resume

```bash
uv run .agents/orchestrator.py resume
uv run .agents/orchestrator.py resume --approved
uv run .agents/orchestrator.py resume --reject-feedback "..."
uv run .agents/orchestrator.py resume --approved-commit
uv run .agents/orchestrator.py resume --reject-commit-feedback "..."
```

Run state and logs are runtime-only under `.agents/runs/` and `.agents/logs/`.

## Step 8 — Manual mode

Open `.agents/task/next-agent.md` and paste it unchanged into the next fresh role chat. The file is intentionally sufficient, together with the repository, to restart from a fresh context without relying on prior chat memory.

## Step 9 — Maintenance

```bash
uv run .agents/orchestrator.py doctor
uv run .agents/orchestrator.py self-test
```

`doctor` validates protocol/templates/workspace and rejects obsolete workflow paths. `self-test` exercises blocker, correction, review rejection, owner gates, and successful close-out in an isolated temporary Git repository.

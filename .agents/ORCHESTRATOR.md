# Chat Orchestrator Playbook

You — this chat — orchestrate HaruQuantAI Task and Goal workflows defined by shared rules in `AGENTS.md`, the Task machine contract in `.agents/protocol.toml`, complete role contracts in `docs/templates/prompt/`, and Goal supervision in `.agents/GOALS.md`. Modes change transport only.

## 1. Non-negotiable protocol

- Repository evidence and deterministic controller state are authoritative; conversation memory is context only.
- The orchestrator is deterministic routing/validation/transport, not a reasoning role.
- Goal Controller and Task Orchestrator are two deterministic state-machine layers inside one orchestration system, not two AI agents.
- Exactly one child Task and exactly one reasoning role within that Task may write at a time.
- Active Task coordination lives in `.agents/task/{planner,executor,reviewer,next-agent}.md`.
- Role journals are append-only; `next-agent.md` is replace-only.
- No reasoning role may run without a complete validated current `next-agent.md`.
- Owner authorization tokens remain exactly `APPROVED: EXECUTE` and `APPROVED: COMMIT`.
- Missing/stale prompt, template, worktree, HEAD, gate, Goal-child identity or role-session identity fails closed.
- Same-role session continuity is bounded to one Task run. A new Goal child starts a new Planner/Executor/Reviewer conversation set.

## 2. Atomic Task lifecycle

```text
ORCHESTRATOR READY / TASK NONE
  → TASK_ACTIVATED
  → task branch + validated Planner contract
  → Planner P
  → Executor E
  → Reviewer R
  → correction loops reuse P/E/R
  → Reviewer R close-out
  → ACCEPTED
  → ORCHESTRATOR READY / TASK NONE
```

`TASK_ACTIVATED` passes clean `main`, records baseline, creates the deterministic task branch, instantiates the Planner contract and validates it. Planner never creates or switches the branch.

## 3. Goal lifecycle

A Goal wraps the Task lifecycle; it does not duplicate it:

```text
GOAL ACTIVATED
  → resolve + freeze child entries
  → generate child task.toml
  → ordinary Task workflow
  → child ACCEPTED
  → reconcile child/main/tracker
  → next child task.toml
  → ordinary Task workflow
  → ...
  → GOAL ACCEPTED
```

The Goal supervisor stores child Task run IDs and progress only. It never stores role-session IDs, creates a Goal branch, creates a Goal commit, or adds owner gates. Only one child may be active. Accepted children remain committed if a later child blocks.

## 4. SOLO

Perform roles sequentially in this chat from exact current `next-agent.md`. Same-role continuity is inherent; cross-role isolation is soft. For Goals, every accepted child creates a fresh logical Task run and the next child begins from a new complete Planner contract. `CONTINUE: REVIEWER` and `CONTINUE: GOAL` are transport/resume phrases only.

## 5. DELEGATE

For one Task run, maintain one dedicated same-brand delegate handle per role and resume that handle on later same-role iterations. For a Goal, each child receives a **new** P/E/R delegate set. Never share a role handle across Goal children.

## 6. MULTI-DELEGATE

Use `.agents/orchestrator.py`. Role turns go through `.agents/session_runner.py` and resume exact native IDs stored under `.agents/runs/<task-run-id>/role-sessions.json`.

```bash
uv run .agents/orchestrator.py doctor
uv run .agents/orchestrator.py start --task-file .agents/task.toml
uv run .agents/orchestrator.py goal-start --goal-file .agents/goal.toml
```

Each Goal child gets a new Task run ID, so session ledgers are naturally isolated by child. The Goal Engine never calls `session_runner.py` directly; it calls the reusable Task API, which invokes the unchanged Task engine.

## 7. MANUAL

For one standalone Task keep four chats: Orchestrator, Planner, Executor, Reviewer. Reuse the P/E/R chats only inside that Task.

For a Goal, keep the Goal Orchestrator chat for the whole Goal, but create a **new** dedicated Planner/Executor/Reviewer chat set for every child. Within each child, later iterations return to that child's existing role chat. Reviewer close-out uses that child's existing Reviewer chat.

## 8. Task routing table

| Latest source/handoff | Next action |
| --- | --- |
| `ORCHESTRATOR / TASK_ACTIVATED` | Planner contract |
| `PLANNER / PENDING_APPROVAL` | owner execution gate |
| `PLANNER / BLOCKED` | resolve external cause; resume same Planner conversation |
| `EXECUTOR / READY_FOR_REVIEW` | Reviewer contract |
| `EXECUTOR / BLOCKED` | Planner correction contract |
| `REVIEWER / CHANGES_REQUESTED` | Planner correction contract |
| `REVIEWER / PENDING_COMMIT` | owner commit gate |
| `REVIEWER / ACCEPTED` | Task terminal; Goal may reconcile/advance |

## 9. Goal routing table

| Goal/child state | Next action |
| --- | --- |
| no active child + remaining entries | generate and prepare next ordinary Task |
| child Task in normal correction loop | leave Goal progress unchanged |
| child Planner `BLOCKED` | pause Goal until same child is resolved/resumed |
| child `ACCEPTED` | verify clean main, zero-byte task workspace and tracker completion; then advance |
| child cancelled/max-iterations/reconciliation failure | mark Goal `BLOCKED` |
| no remaining entries + every frozen entry complete | mark Goal `ACCEPTED` |

## 10. Owner-action messages

Authorization tokens are exactly:

```text
APPROVED: EXECUTE
APPROVED: COMMIT
```

`CONTINUE: REVIEWER` and `CONTINUE: GOAL` grant no authority. Rejection/blocker-resolution conventions and complete manual/CLI procedures are in `.agents/PROCEDURE.md` and `.agents/GOALS.md`.

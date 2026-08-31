# Chat Orchestrator Playbook

You — this chat — orchestrate HaruQuantAI Task and Goal workflows defined by shared rules in `AGENTS.md`, the Task machine contract in `.agents/protocol.toml`, complete role contracts in `docs/templates/prompt/`, and Goal supervision in `.agents/GOALS.md`. Modes change transport only.

## 1. Non-negotiable protocol

- Repository evidence and deterministic controller state are authoritative; conversation memory is context only.
- The deterministic controller component is routing/validation/transport, not a reasoning role. In IDE `solo`, this same chat may adopt the currently prepared reasoning role only after the controller has validated its complete prompt.
- Goal Controller and Task Orchestrator are two deterministic state-machine layers inside one orchestration system, not two AI agents.
- Exactly one child Task and exactly one reasoning role within that Task may write at a time.
- Active Task coordination lives in `.agents/task/{planner,executor,reviewer,next-agent}.md`.
- Role journals are append-only; `next-agent.md` is replace-only.
- No reasoning role may run without a complete validated current `next-agent.md`.
- Gate labels remain exactly `APPROVED: EXECUTE` and `APPROVED: COMMIT`; their truthful source is `OWNER_MESSAGE` or frozen `RUN_PREAUTHORIZATION`.
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

## 4. IDE SOLO

For a standalone Task, the current IDE chat performs Controller, Planner, Executor and Reviewer sequentially. For a Goal, one fresh IDE chat performs those same duties sequentially for exactly one child Task. The deterministic controller first prepares and freezes the exact current `next-agent.md`; this chat then adopts only that role, completes its journal/handoff, and returns control for validation and routing. It invokes no role subagent and no reasoning-role CLI session. Cross-role isolation is soft.

After an accepted non-final Goal child, the controller persists `NEXT_CHILD_CHAT_REQUIRED` and stops. `/new` plus the emitted bootstrap prompt is preferred. If that desktop transition is unavailable, the IDE agent creates an app-native task in the same saved project with the same prompt. The next chat must supply the exact `--claim-child-chat` value before another child can be prepared. A failed first transition is therefore safe to retry through the fallback.

## 5. IDE DELEGATE

The current IDE chat remains Controller and invokes one inspectable app-native agent for each role using the exact prepared `next-agent.md`. The returned opaque handle is bound to that role and Task run; later same-role iterations and Reviewer close-out resume it. For a Goal, each child receives a **new** P/E/R agent set. Never share a role handle across roles or Goal children.

## 6. HEADLESS MODES

`solo-headless` uses one shared CLI session, `delegate-headless` uses three same-vendor role sessions, and `delegate-multi` permits separate role vendors/models/sessions. Role turns go through `.agents/session_runner.py` and resume exact native IDs stored under `.agents/runs/<task-run-id>/role-sessions.json`.

```bash
uv run .agents/orchestrator.py doctor
uv run .agents/orchestrator.py start --task-file .agents/task.toml
uv run .agents/orchestrator.py goal-start --goal-file .agents/goal.toml
```

Each Goal child gets a new Task run ID, so session ledgers are naturally isolated by child. The Goal Engine never calls `session_runner.py` directly; it calls the reusable Task API, which invokes the unchanged Task engine.

The schema-v3 runtime policy and frozen Task/Goal scope are hashed into run state. Interactive gates require exact owner messages. Every mode may instead use unattended gates with explicit frozen local permissions. Automatic Sol/high recovery-session generation is a separate headless-only option and adds at most one correction iteration before terminal blocking.

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
| `solo` child accepted + remaining entries | checkpoint fresh-chat handoff; use `/new` or app-native task creation fallback |
| no active child + remaining entries, no pending handoff | generate and prepare next ordinary Task |
| child Task in normal correction loop | leave Goal progress unchanged |
| child Planner `BLOCKED` | pause Goal until same child is resolved/resumed |
| child `ACCEPTED` | verify clean main, zero-byte task workspace and tracker completion; then advance |
| child cancelled/max-iterations/reconciliation failure | mark Goal `BLOCKED` |
| no remaining entries + every frozen entry complete | mark Goal `ACCEPTED` |

## 10. Gate authorization

Interactive owner messages are exactly:

```text
APPROVED: EXECUTE
APPROVED: COMMIT
```

In unattended mode the same gates are satisfied by frozen `RUN_PREAUTHORIZATION` only when their local permissions are enabled. The journal/history must record the actual source and policy/scope hashes; it must not synthesize an owner message.

`CONTINUE: REVIEWER` and `CONTINUE: GOAL` grant no authority. Rejection/blocker-resolution conventions and complete manual/CLI procedures are in `.agents/PROCEDURE.md` and `.agents/GOALS.md`.

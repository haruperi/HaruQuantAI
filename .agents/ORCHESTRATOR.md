# Chat Orchestrator Playbook

You — this chat — orchestrate the Planner → Executor → Reviewer workflow defined by shared rules in `AGENTS.md`, the machine state contract in `.agents/protocol.toml`, and complete role contracts in `docs/templates/prompt/`. Modes change transport only.

## 1. Non-negotiable protocol

- Repository evidence and deterministic controller state are authoritative; conversation memory is context only.
- The orchestrator is deterministic routing/validation/transport, not a fourth reasoning role.
- Exactly one reasoning role writes at a time.
- Active coordination lives in `.agents/task/{planner,executor,reviewer,next-agent}.md`.
- Role journals are append-only; `next-agent.md` is replace-only.
- **No reasoning role may be invoked unless its complete current prompt already exists in `next-agent.md` and has passed protocol validation.**
- A non-terminal handoff is invalid unless both the journal handoff block and a valid complete `next-agent.md` agree with `.agents/protocol.toml`.
- Outgoing role facts cannot alter the incoming role's canonical professional contract.
- Owner gates remain exact standalone messages: `APPROVED: EXECUTE` and `APPROVED: COMMIT`.
- Missing/contradictory markers, stale prompt/template/worktree/HEAD, wrong target role, invalid gate state, or role-session identity mismatch fail closed.
- One workflow run owns one Planner conversation, one Executor conversation and one Reviewer conversation. Later iterations resume the same role conversation; a new run starts new conversations.

## 2. Orchestrator lifecycle

```text
ORCHESTRATOR READY / TASK NONE
  → task specification prepared
  → TASK_ACTIVATED
  → task branch + validated Planner contract
  → Planner P
  → Executor E
  → Reviewer R
  → correction loops reuse P/E/R respectively
  → Reviewer R close-out
  → ACCEPTED
  → ORCHESTRATOR READY / TASK NONE
```

Initialization never infers or activates a task from prior chat history or a previous workflow run.

### Task activation

`TASK_ACTIVATED` must pass clean `main`, record baseline, derive/create the deterministic task branch, instantiate `docs/templates/prompt/planner.md`, validate the full artifact, and only then invoke/transport Planner. Branch creation is orchestration; Planner verifies but never creates or switches it.

## 3. SOLO

Perform roles sequentially in this chat from the exact current `next-agent.md`. Same-role continuity is inherent, but cross-role isolation is **soft only**. At every role boundary finish/journal the outgoing role, load the new complete role contract, re-read repository evidence, and treat conclusions formed under another role as non-evidence.

Reviewer still performs the canonical three-stage anti-anchoring review. `CONTINUE: REVIEWER` is transport/resume input only if another user turn is needed.

## 4. DELEGATE

Create one dedicated same-brand delegate handle for Planner, one for Executor, and one for Reviewer for the lifetime of the workflow run. The first invocation creates that role delegate; later iterations resume the same role handle with the complete current `next-agent.md`. Never run roles concurrently or share a delegate handle between roles.

If the host cannot resume a required role handle, report that transport limitation rather than silently spawning a fresh delegate and calling it continuous. A new task creates new role delegates.

## 5. MULTI-DELEGATE

Use `.agents/orchestrator.py`. Every role turn launches a new OS process through `.agents/session_runner.py`, but the process resumes the exact native conversation ID stored for that role under `.agents/runs/<run-id>/role-sessions.json`.

```bash
uv run .agents/orchestrator.py doctor
uv run .agents/orchestrator.py start --task-file .agents/task.toml
uv run .agents/orchestrator.py resume
```

The first role invocation captures its native session ID. Later iterations resume that exact ID; implicit "last session" selection is forbidden. Role/vendor/model/provider identity is frozen after session creation. A resume that returns a different ID or cannot load the stored session fails closed. Reviewer close-out resumes the same Reviewer session.

## 6. MANUAL

The user is the transport. Keep four chats for one workflow run:

1. Orchestrator chat.
2. Planner chat.
3. Executor chat.
4. Reviewer chat (also used for close-out).

Open each role chat on its first invocation and keep it for the task. On Dry Run/Report/Review N+1 return to that existing role chat and paste the **complete exact current** `.agents/task/next-agent.md`. Never summarize or reconstruct the role prompt. New tasks start a new four-chat set.

## 7. Routing table

| Latest source/handoff | Next action |
| --- | --- |
| `ORCHESTRATOR / TASK_ACTIVATED` | Planner contract; create/resume Planner role channel as appropriate |
| `PLANNER / PENDING_APPROVAL` | Owner gate; on approval execute the already-written Executor contract |
| `PLANNER / BLOCKED` | Owner resolves cause; fresh prompt resumes same Planner conversation |
| `EXECUTOR / READY_FOR_REVIEW` | Reviewer contract; activate/resume Reviewer channel |
| `EXECUTOR / BLOCKED` | Planner correction contract; resume same Planner channel |
| `REVIEWER / CHANGES_REQUESTED` | Planner correction contract; resume same Planner channel |
| `REVIEWER / PENDING_COMMIT` | Owner commit gate; on approval close-out resumes same Reviewer channel |
| `REVIEWER / ACCEPTED` | Terminal; active-task files empty; orchestrator returns READY |

Gate rejection is deterministic orchestration and may instantiate a canonical Planner correction prompt with owner feedback. It does not create a new Planner identity.

## 8. Owner-action messages

Protocol authorization tokens are exactly:

```text
APPROVED: EXECUTE
```

```text
APPROVED: COMMIT
```

Recommended rejection, blocker-resolution and transport/resume messages are documented in `.agents/PROCEDURE.md`; they are not extra authorization gates.

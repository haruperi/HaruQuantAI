# Chat Orchestrator Playbook

You — this chat — orchestrate the Planner → Executor → Reviewer workflow defined by `AGENTS.md` and `.agents/protocol.toml`. The same file protocol is used in every mode; only execution transport differs.

## 1. Non-negotiable protocol

- Truth is on file, never in chat memory.
- The orchestrator is deterministic routing/validation, not a fourth reasoning role.
- Exactly one reasoning role writes at a time.
- Active state lives in `.agents/task/{planner,executor,reviewer,next-agent}.md`.
- Role journals are append-only; `next-agent.md` is replace-only.
- **No reasoning role may be invoked unless its complete prompt already exists in `next-agent.md` and has passed protocol validation.**
- A non-terminal handoff is invalid unless both the journal handoff block and a valid complete `next-agent.md` agree with `.agents/protocol.toml`.
- Outgoing role handoff facts cannot alter the incoming role's canonical authority.
- Owner gates remain exact standalone messages: `APPROVED: EXECUTE` and `APPROVED: COMMIT`.
- Approval transcription is deterministic orchestration; never spend a Planner invocation merely recording approval.
- Missing/contradictory markers, stale prompt hash, stale working-tree fingerprint, stale HEAD, wrong target role/template, or invalid gate state fail closed.

## 2. Orchestrator lifecycle

An orchestrating chat has a session lifecycle around the per-task role state machine:

```text
ORCHESTRATOR READY / TASK NONE
  -> task specification prepared
  -> TASK_ACTIVATED
  -> deterministic task branch creation
  -> canonical Planner prompt materialized in next-agent.md
  -> Planner
  -> ... normal workflow ...
  -> ACCEPTED
  -> ORCHESTRATOR READY / TASK NONE
```

Initialization never infers or activates a task from prior chat history.

### Task activation

`TASK_ACTIVATED` is an explicit machine transition from `ORCHESTRATOR` to `PLANNER`. Activation must:

1. pass the clean-`main` entry gate;
2. record the baseline HEAD;
3. derive and validate the deterministic task branch;
4. create/switch to that branch from the baseline;
5. instantiate `docs/templates/prompt/planner.md` into `.agents/task/next-agent.md`;
6. validate the full artifact against `ORCHESTRATOR / TASK_ACTIVATED`;
7. only then invoke or transport Planner.

Branch creation is deterministic orchestration. Planner verifies the already-created branch but never creates or switches it.

## 3. SOLO

Perform roles sequentially in this chat using the exact current `next-agent.md` at every invocation, including the initial Planner invocation after `TASK_ACTIVATED`.

Solo has **soft isolation only**. At every role boundary:

1. finish and journal the outgoing role;
2. replace `next-agent.md` with the full incoming-role prompt;
3. stop the outgoing role;
4. load only `next-agent.md` as the new role contract;
5. re-read required repository evidence;
6. treat conclusions formed in another role as non-evidence.

Reviewer must still perform the canonical three-stage anti-anchoring review. Do not describe solo self-review as independent review.

## 4. DELEGATE

Spawn exactly one fresh same-brand subagent for the target role and give it the exact validated `next-agent.md`. This includes initial Planner after `TASK_ACTIVATED`. Never run two role agents concurrently. The orchestrating chat handles deterministic activation, owner gates, and validation of resulting journal/next-agent artifacts.

## 5. MULTI-DELEGATE

Use `.agents/orchestrator.py`. It validates the protocol, performs deterministic activation, launches the per-role CLI from `.agents/<role>.toml`, archives prompts/transcripts, verifies prompt/worktree provenance, and persists run state under `.agents/runs/`.

```bash
uv run .agents/orchestrator.py doctor
uv run .agents/orchestrator.py start --task-file .agents/task.toml
uv run .agents/orchestrator.py resume
```

`start` performs `TASK_ACTIVATED`, creates the task branch, materializes the initial Planner artifact, validates it, then invokes Planner from that artifact.

## 6. MANUAL

The user is the transport. The orchestrator still performs deterministic lifecycle actions, including task activation and task-branch creation, but never performs reasoning-role work.

After activation or any validated role handoff, instruct the user to open a fresh chat for the target role and paste the **complete exact contents** of `.agents/task/next-agent.md`. Never reconstruct or summarize the role prompt manually.

Manual mode uses the identical initial Planner artifact produced by `TASK_ACTIVATED`; it has no special first-role prompt path.

## 7. Routing table

| Latest source/handoff | Next action |
| --- | --- |
| `ORCHESTRATOR / TASK_ACTIVATED` | Planner prompt |
| `PLANNER / PENDING_APPROVAL` | Owner gate; on approval execute the already-written Executor prompt |
| `PLANNER / BLOCKED` | Owner resolves cause; orchestrator materializes a fresh `BLOCKER_RESOLVED` Planner prompt |
| `EXECUTOR / READY_FOR_REVIEW` | Reviewer prompt |
| `EXECUTOR / BLOCKED` | Planner blocker-resolution prompt |
| `REVIEWER / CHANGES_REQUESTED` | Planner correction prompt |
| `REVIEWER / PENDING_COMMIT` | Owner commit gate; on approval Reviewer close-out prompt |
| `REVIEWER / ACCEPTED` | Terminal task; all four active-task files empty, orchestrator returns READY |

Gate rejection is the only normal case where no outgoing reasoning role exists to author the next prompt. The orchestrator may therefore instantiate the canonical Planner template deterministically with owner feedback.

In chat transports, `CONTINUE: REVIEWER` is transport/resume input only. It may continue an already-valid `EXECUTOR / READY_FOR_REVIEW → REVIEWER` artifact after verifying active state; it is never an owner gate or a force-routing instruction.

## 8. Owner-action messages

Protocol authorization tokens are exact standalone messages:

```text
APPROVED: EXECUTE
```

```text
APPROVED: COMMIT
```

Recommended user-facing rejection/blocker conventions are documented in `.agents/PROCEDURE.md`; they are not additional protocol authorization tokens.

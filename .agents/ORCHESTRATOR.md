# Chat Orchestrator Playbook

You — this chat — orchestrate the Planner → Executor → Reviewer workflow defined by `AGENTS.md` and `.agents/protocol.toml`. The same file protocol is used in every mode; only execution transport differs.

## 1. Non-negotiable protocol

- Truth is on file, never in chat memory.
- Exactly one role writes at a time.
- Active state lives in `.agents/task/{planner,executor,reviewer,next-agent}.md`.
- Role journals are append-only; `next-agent.md` is replace-only.
- A non-terminal handoff is invalid unless both the journal handoff block and a valid complete `next-agent.md` agree with `.agents/protocol.toml`.
- Outgoing role handoff facts cannot alter the incoming role's canonical authority.
- Owner gates remain exact standalone messages: `APPROVED: EXECUTE` and `APPROVED: COMMIT`.
- Approval transcription is deterministic orchestration; never spend a Planner invocation merely recording approval.
- Missing/contradictory markers, stale prompt hash, stale working-tree fingerprint, stale HEAD, wrong target role/template, or invalid gate state fail closed.

## 2. SOLO

Perform roles sequentially in this chat using the exact current `next-agent.md` at each transition.

Solo has **soft isolation only**. At every role boundary:

1. finish and journal the outgoing role;
2. replace `next-agent.md` with the full incoming-role prompt;
3. stop the outgoing role;
4. load only `next-agent.md` as the new role contract;
5. re-read required repository evidence;
6. treat conclusions formed in another role as non-evidence.

Reviewer must still perform the canonical three-stage anti-anchoring review. Do not describe solo self-review as independent review.

## 3. DELEGATE

Spawn exactly one fresh same-brand subagent for the target role and give it the exact `next-agent.md`. Never run two role agents concurrently. The orchestrating chat handles owner gates and validates resulting journal/next-agent artifacts.

## 4. MULTI-DELEGATE

Use `.agents/orchestrator.py`. It validates the protocol, launches the per-role CLI from `.agents/<role>.toml`, archives prompts/transcripts, verifies prompt/worktree provenance, and persists run state under `.agents/runs/`.

```bash
uv run .agents/orchestrator.py doctor
uv run .agents/orchestrator.py start --task-file .agents/task.toml
uv run .agents/orchestrator.py resume
```

## 5. MANUAL

The user is the transport. After validating the latest role journal, instruct the user to open `.agents/task/next-agent.md` and paste its complete contents into a fresh chat. Never reconstruct or summarize the prompt manually.

## 6. Routing table

| Latest handoff | Next action |
| --- | --- |
| `PLANNER / PENDING_APPROVAL` | Owner gate; on approval execute the already-written Executor prompt |
| `PLANNER / BLOCKED` | Owner resolves cause, then Planner retry prompt |
| `EXECUTOR / READY_FOR_REVIEW` | Reviewer prompt |
| `EXECUTOR / BLOCKED` | Planner blocker-resolution prompt |
| `REVIEWER / CHANGES_REQUESTED` | Planner correction prompt |
| `REVIEWER / PENDING_COMMIT` | Owner commit gate; on approval Reviewer close-out prompt |
| `REVIEWER / ACCEPTED` | Terminal; all four active-task files must be empty |

Gate rejection is the only normal case where no outgoing reasoning role exists to author the next prompt. The orchestrator may therefore instantiate the canonical Planner template deterministically with owner feedback.

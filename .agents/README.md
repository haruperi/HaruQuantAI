# `.agents` — Artifact-Driven Agent Workflow

HaruQuantAI delivers development tasks through Planner → Executor → Reviewer with four interchangeable transport modes. The workflow is file-driven: repository state and deterministic controller state are authoritative; conversation history is context only.

## Active task workspace

```text
.agents/task/
├── planner.md
├── executor.md
├── reviewer.md
└── next-agent.md
```

The three role journals are append-only during an active task. `next-agent.md` is replace-only and contains the complete standalone current role contract. All four files are zero bytes when no task is active and after successful close-out.

Reusable prompt truth lives only in `docs/templates/prompt/`. Each canonical template contains the complete professional role-specific contract; `AGENTS.md` contains shared repository/workflow law rather than duplicate job descriptions.

## Core invariants

**No reasoning role may be invoked unless its complete prompt already exists in `.agents/task/next-agent.md` and has passed protocol validation.**

**Cross-role isolation and same-role continuity coexist.** One workflow run owns one logical Planner conversation, one Executor conversation, and one Reviewer conversation. Later iterations resume the same role conversation. Reviewer close-out reuses the Reviewer conversation. New workflow runs start new conversations.

Session history never overrides current repository evidence, deterministic Python state, or the current validated `next-agent.md`.

## Modes

| Mode | Transport | Cross-role isolation | Same-role continuity |
| --- | --- | --- | --- |
| `solo` | One chat performs sequential roles | Soft only | Inherent in the chat |
| `delegate` | Orchestrator dispatches same-brand role delegates | Dedicated role handle where host supports it | Resume the same role delegate |
| `multi-delegate` | Fresh CLI process per turn, potentially cross-vendor | Dedicated native role conversation | Resume exact stored native session ID |
| `manual` | Human moves `next-agent.md` among four chats | Dedicated Planner/Executor/Reviewer chats | Return to the same role chat |

Mode changes transport and transport automation only. Role identity, role continuity, prompt contract, authority, state transitions, iterations, and handoffs remain the same.

`READY_FOR_REVIEW` is already protocol-authorized, not an owner gate. Solo may require `CONTINUE: REVIEWER` merely to create another user turn. Delegate resumes/activates its Reviewer handle, multi-delegate resumes its stored Reviewer CLI session, and manual returns to its existing Reviewer chat. The only authorization gates are `APPROVED: EXECUTE` and `APPROVED: COMMIT`.

## Role contracts

- Planner: **Principal Software Architect and Implementation Planner** — `docs/templates/prompt/planner.md`
- Executor: **Senior Software Implementation Engineer** — `docs/templates/prompt/executor.md`
- Reviewer: **Principal Software Verification and Code Review Engineer** — `docs/templates/prompt/reviewer.md`
- Reviewer close-out: **Release Integrity and Change-Control Engineer** — `docs/templates/prompt/reviewer-closeout.md`

`AGENTS.md` remains binding for shared architecture, safety, quality, Git and workflow constraints, but the templates define the complete role-specific job contracts.

## Multi-delegate role-session persistence

`start` and `resume` use `.agents/<role>.toml`. The tracked role configs route each turn through `.agents/session_runner.py`.

For the lifetime of one workflow run, native IDs are stored at:

```text
.agents/runs/<run-id>/role-sessions.json
```

The ledger is gitignored runtime transport state. It stores Planner/Executor/Reviewer identities separately and freezes brand/model/provider/effort for each established role conversation. It never appears in `next-agent.md`.

- Codex captures `thread.started.thread_id` and resumes with the exact ID. A different returned ID fails closed.
- AGY captures `conversation_id` and resumes with `--conversation <exact-id>`.
- Cline captures its native session ID and resumes with `--id <exact-id>`; installed versions whose headless resume path fails are allowed to fail closed. Transcript replay is deliberately not used as a fake resume mechanism.
- Implicit `--last`/`--continue` selection is not used when an exact ID exists.

`uv run .agents/orchestrator.py doctor` checks the protocol continuity policy, session runner, configured native CLI, and declared resume capability before multi-delegate execution.

## Canonical workflow truth

- `AGENTS.md` — shared contributor/workflow constitution.
- `.agents/protocol.toml` — machine-readable transitions, gates, isolation and session-continuity policy.
- `.agents/PROCEDURE.md` — operator procedure and exact copy/paste chat text.
- `docs/templates/prompt/default.md` — prompt-design standard.
- `docs/templates/prompt/{planner,executor,reviewer,reviewer-closeout}.md` — complete canonical professional role contracts.
- `.agents/task/next-agent.md` — current instantiated role/task contract.
- `.agents/runs/*.json` — orchestrator audit state; `.agents/runs/<run-id>/role-sessions.json` — native role transport continuity state.
- `.agents/logs/` — immutable invocation prompt/transcript archive.

## Session lifecycle

```text
ORCHESTRATOR READY / TASK NONE
  → TASK_ACTIVATED
  → Planner P / Dry Run 1
  → APPROVED: EXECUTE
  → Executor E / Report 1
  → Reviewer R / Review 1
      ├─ CHANGES_REQUESTED → Planner P / Dry Run 2 → Executor E / Report 2 → Reviewer R / Review 2
      └─ PENDING_COMMIT → APPROVED: COMMIT → Reviewer R / close-out → ACCEPTED
```

P, E and R remain distinct conversations. Their current prompt is always resent in full, so persistent context is useful history rather than hidden authority.

## `next-agent.md` contract

Every reasoning-role invocation uses a complete prompt beginning with TOML front matter that records run/task/iteration, source/target role, handoff, branch, baseline, source HEAD, canonical template, and gate requirement. **Session IDs are intentionally absent.**

The orchestrator validates schema, transition, target template, branch, baseline, HEAD, protected professional-role sentinels, owner-gate semantics, unfilled placeholders, prompt SHA-256, canonical-template SHA-256, and working-tree fingerprint. Executor handoffs additionally carry exact normalized `allowed_write_paths`.

Outgoing roles may populate task-specific facts but may not weaken the incoming role's canonical role, authority, methodology, quality criteria, or handoff rules.

## Reviewer anti-anchoring

Persistent Reviewer context does not weaken independent review. Every Review N still follows:

1. **Independent reconstruction** from current task, authorities, baseline, diff and resulting repository.
2. **Independent verification** with affected tests and non-mutating quality/architecture/usage checks.
3. **Claims reconciliation** only afterward by reading Planner/Executor journals.

Prior Reviewer findings are context, not proof. The Reviewer never repairs implementation; defects produce `CHANGES_REQUESTED`.

## Quick start

```bash
uv run .agents/configure.py
uv run .agents/orchestrator.py doctor
uv run .agents/make_task.py --list
uv run .agents/make_task.py 1.1
uv run .agents/orchestrator.py start --task-file .agents/task.toml
```

Resume/gate examples:

```bash
uv run .agents/orchestrator.py resume
uv run .agents/orchestrator.py resume --approved
uv run .agents/orchestrator.py resume --reject-feedback "..."
uv run .agents/orchestrator.py resume --resolve-planner-blocker "..."
uv run .agents/orchestrator.py resume --approved-commit
uv run .agents/orchestrator.py resume --reject-commit-feedback "..."
```

For chat-driven and manual modes, use `.agents/PROCEDURE.md`. Runtime `run-config.toml`, `task.toml`, logs and runs are gitignored; protocol, role templates/configs, controller code and the four zero-byte coordination files are tracked workflow source.

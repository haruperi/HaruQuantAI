# `.agents` — Artifact-Driven Task and Goal Workflow

HaruQuantAI implements one atomic Planner → Executor → Reviewer **Task workflow** and a deterministic **Goal supervisor** that can execute many such Tasks sequentially. Repository state and deterministic controller state are authoritative; conversation history is context only.

## Atomic Task workspace

```text
.agents/task/
├── planner.md
├── executor.md
├── reviewer.md
└── next-agent.md
```

The role journals are append-only during an active Task. `next-agent.md` is replace-only and contains the complete current role contract. All four files are zero bytes when no Task is active and after successful close-out.

Reusable prompt truth lives in `docs/templates/prompt/`. `AGENTS.md` contains shared repository/workflow law. `.agents/protocol.toml` remains the Task transition/gate contract.

## Two orchestration levels, one system

```text
                         ORCHESTRATOR
                              │
                  ┌───────────┴───────────┐
                  │                       │
             GOAL ENGINE             TASK ENGINE
           supervisory state            existing
                  │                       │
                  │              Planner / Executor / Reviewer
                  │                       │
                  └──── child ACCEPTED ◄─┘
                         │
                         ▼
                     next child
```

The Goal Engine is not an LLM agent. It freezes selected implementation entries, generates ordinary child `task.toml` files, records child Task run IDs and advances only after a child reaches verified `ACCEPTED`. It does not duplicate Task routing, branch logic, owner gates, role sessions, review or commit logic.

See `.agents/GOALS.md` for the complete Goal contract.

## Core invariants

- No reasoning role may run unless its complete current prompt exists in `.agents/task/next-agent.md` and passes protocol validation.
- Cross-role isolation and same-role continuity coexist inside one Task run.
- One Task run owns one logical Planner conversation, one Executor conversation and one Reviewer conversation; later iterations resume the same role conversation.
- **A new Goal child is a new Task run and therefore gets a new P/E/R conversation set.** Goal state stores no role-session IDs.
- A Goal has no Goal branch, no Goal commit and no additional owner authorization gate.
- Only one Goal child may be active at a time.
- Every child starts from the latest clean accepted `main` and contributes its own focused commit.

## Modes

| Mode | Task same-role continuity | Goal child boundary |
| --- | --- | --- |
| `solo` | inherent in one chat; cross-role isolation soft | new logical Task contract/context boundary |
| `delegate` | resume one dedicated handle per role | new P/E/R delegate set per child |
| `multi-delegate` | exact native session ID per role/run | new Task run ID and session ledger per child |
| `manual` | return to same P/E/R chat within Task | new P/E/R chat set per child; same Goal Orchestrator chat |

Mode changes transport and transport automation only.

## Professional role contracts

- Planner — **Principal Software Architect and Implementation Planner**: `docs/templates/prompt/planner.md`
- Executor — **Senior Software Implementation Engineer**: `docs/templates/prompt/executor.md`
- Reviewer — **Principal Software Verification and Code Review Engineer**: `docs/templates/prompt/reviewer.md`
- Reviewer close-out — **Release Integrity and Change-Control Engineer**: `docs/templates/prompt/reviewer-closeout.md`

## Task role-session persistence

Multi-delegate role configs route turns through `.agents/session_runner.py`. Native IDs live at:

```text
.agents/runs/<task-run-id>/role-sessions.json
```

They are runtime-only and never enter `next-agent.md`. Codex, AGY and supported Cline native exact-ID resume paths fail closed on identity mismatch. Implicit latest-session heuristics are not used.

## Goal state

Goal input and runtime state are separate from Task coordination:

```text
.agents/goal.toml                         # runtime input, gitignored
.agents/goals/<goal-run-id>/state.json   # supervisory checkpoint
.agents/goals/<goal-run-id>/children/    # exact frozen child task specs
```

Supported v1 selection types are explicit `entries`, numbered `phase`, and `all_open`. Selection freezes at Goal activation so later tracker edits cannot silently enlarge scope.

## Canonical workflow truth

- `AGENTS.md` — shared contributor/workflow constitution.
- `.agents/protocol.toml` — machine-readable atomic Task transitions/gates/session policy.
- `.agents/GOALS.md` — Goal supervision contract.
- `.agents/PROCEDURE.md` — operator procedures and chat/manual transport text.
- `.agents/task_api.py` — reusable entry point into the unchanged Task engine.
- `.agents/goal_engine.py` — deterministic multi-Task supervisor.
- `.agents/make_task.py` — canonical one-entry Task spec builder.
- `.agents/make_goal.py` — Goal spec generator.
- `.agents/task/next-agent.md` — current instantiated role/Task contract.
- `.agents/runs/` — Task audit/session runtime state.
- `.agents/goals/` — Goal checkpoints.

## Task quick start

```bash
uv run .agents/configure.py
uv run .agents/orchestrator.py doctor
uv run .agents/make_task.py --list
uv run .agents/make_task.py 1.1
uv run .agents/orchestrator.py start --task-file .agents/task.toml
```

Task resume/gates:

```bash
uv run .agents/orchestrator.py resume
uv run .agents/orchestrator.py resume --approved
uv run .agents/orchestrator.py resume --reject-feedback "..."
uv run .agents/orchestrator.py resume --resolve-planner-blocker "..."
uv run .agents/orchestrator.py resume --approved-commit
uv run .agents/orchestrator.py resume --reject-commit-feedback "..."
```

## Goal quick start

Generate one Goal:

```bash
uv run .agents/make_goal.py --entries 7.1 7.2 7.3
uv run .agents/make_goal.py --phase 7
uv run .agents/make_goal.py --all-open
```

Run/check/resume it:

```bash
uv run .agents/orchestrator.py goal-start --goal-file .agents/goal.toml
uv run .agents/orchestrator.py goal-status
uv run .agents/orchestrator.py goal-resume
```

The same child owner gates are relayed through `goal-resume --approved` and `goal-resume --approved-commit` when needed. Goals add no authorization token.

For chat-driven and manual operation, follow `.agents/PROCEDURE.md` and `.agents/GOALS.md`. Runtime `run-config.toml`, `task.toml`, `goal.toml`, logs, runs and goals are gitignored.

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
- A Goal has no Goal branch, no Goal commit and no additional authorization gate.
- Only one Goal child may be active at a time.
- Every child starts from the latest clean accepted `main` and contributes its own focused commit.

## Modes

| Mode | Task same-role continuity | Goal child boundary |
| --- | --- | --- |
| `solo` | current IDE chat performs Controller + P/E/R sequentially; no role subagent/CLI | fresh IDE chat per child, with a persisted handoff claim |
| `solo-headless` | one native CLI session shared sequentially by P/E/R | fresh shared CLI session per child |
| `delegate` | current IDE Controller resumes one inspectable app-native agent per role | fresh app-native P/E/R agent set per child |
| `delegate-headless` | one CLI vendor, distinct persistent session per role | fresh same-vendor P/E/R session set per child |
| `delegate-multi` | separate role vendor/model and exact native session ID per role/run | new Task run ID and session ledger per child |
| `manual` | return to same P/E/R chat within Task | new P/E/R chat set per child; same Goal Orchestrator chat |

Schema-v3 `.agents/run-config.toml` is authoritative for mode, headless role models/effort/providers, approval policy, normal iteration limit, unattended local permissions, and bounded recovery. The deterministic CLI drives Task/Goal state in every mode. Only `solo-headless`, `delegate-headless`, and `delegate-multi` use `.agents/session_runner.py` to launch reasoning-role CLI sessions. IDE `solo` performs the prepared role in the current chat; IDE `delegate` invokes/resumes app-native inspectable agents; `manual` waits for operator-managed chats.

Schema-v2 configurations remain resume-compatible with their old transport meaning and unchanged policy fingerprint. A missing-schema legacy file may continue an already-active legacy Task only. New Tasks and Goals fail closed until `.agents/configure.py` writes a complete schema-v3 policy.

`approval_policy = "interactive"` requires the exact owner gate messages. In every mode, `approval_policy = "unattended"` uses frozen run preauthorization only for permissions explicitly enabled in `[unattended]`; it changes gate authorization, not role transport. It never authorizes push, external/live actions, destructive operations, or scope expansion. In headless modes only, optional recovery creates one fresh `codex/gpt-5.6-sol/high` session generation for one additional correction iteration, then stops at `MAX_ITERATIONS`.

## Professional role contracts

- Planner — **Principal Software Architect and Implementation Planner**: `docs/templates/prompt/planner.md`
- Executor — **Senior Software Implementation Engineer**: `docs/templates/prompt/executor.md`
- Reviewer — **Principal Software Verification and Code Review Engineer**: `docs/templates/prompt/reviewer.md`
- Reviewer close-out — **Release Integrity and Change-Control Engineer**: `docs/templates/prompt/reviewer-closeout.md`

## Task transport persistence

Headless modes route turns through `.agents/session_runner.py`. Native CLI IDs live at:

```text
.agents/runs/<task-run-id>/role-sessions.json
```

They are runtime-only and never enter `next-agent.md`. Codex, AGY and supported Cline native exact-ID resume paths fail closed on identity mismatch. Implicit latest-session heuristics are not used.

IDE `delegate` records opaque app-agent handles separately at `.agents/runs/<task-run-id>/app-agent-handles.json`. One handle is bound to each role, may not cross roles or Task runs, and must be reused for later same-role iterations and Reviewer close-out. IDE `solo` has no role-session ledger because each child chat performs all roles inline. Goal state checkpoints the between-child chat handoff, not an app conversation ID.

## Goal state

Goal input and runtime state are separate from Task coordination:

```text
.agents/goal.toml                         # runtime input, gitignored
.agents/goals/<goal-run-id>/state.json   # supervisory checkpoint
.agents/goals/<goal-run-id>/children/    # exact frozen child task specs
```

Supported v1 selection types are explicit `entries`, numbered `phase`, and `all_open`. Both legacy heading/checklist trackers and the current implementation-order Markdown tables are parsed. Selection freezes at Goal activation so later tracker edits cannot silently enlarge scope.

An unattended Goal may set `stop_on_blocked=false` (or use `make_goal.py --continue-on-blocked`) for one bounded Planner assumption retry per child. This never skips a child or relaxes protected authority/safety boundaries. Accepted Reviewer assumption sections are hashed into the Goal state for later human review.

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

IDE role-boundary completion:

```bash
# Current chat completed the prepared solo role
uv run .agents/orchestrator.py resume --role-complete

# Inspectable app-native delegate completed the prepared role
uv run .agents/orchestrator.py resume --role-complete --app-agent-id <opaque-id>
```

## Goal quick start

Generate one Goal:

```bash
uv run .agents/make_goal.py --entries 7.1 7.2 7.3
uv run .agents/make_goal.py --phase 7
uv run .agents/make_goal.py --all-open
uv run .agents/make_goal.py --all-open --continue-on-blocked
```

Run/check/resume it:

```bash
uv run .agents/orchestrator.py goal-start --goal-file .agents/goal.toml
uv run .agents/orchestrator.py goal-status
uv run .agents/orchestrator.py goal-resume
```

Interactive child gates are relayed through `goal-resume --approved` and `goal-resume --approved-commit` when needed. IDE child role completions use `goal-resume --role-complete` and, for `delegate`, the bound `--app-agent-id`. Unattended runs in every mode satisfy permitted gates from their frozen policy. Goals add no authorization token.

For a `solo` Goal, an accepted non-final child prints `NEXT_CHILD_CHAT : REQUIRED`. Use `/new` in Codex desktop and submit the emitted `NEXT_CHAT_PROMPT`. If the slash-command transition cannot be driven, the current IDE agent uses app-native task creation in the same saved project with that prompt. The new chat's resume command includes `--claim-child-chat <handoff-id>`; without the exact claim, the controller will not prepare the next child.

For chat-driven and manual operation, follow `.agents/PROCEDURE.md` and `.agents/GOALS.md`. Runtime `run-config.toml`, `task.toml`, `goal.toml`, logs, runs and goals are gitignored.

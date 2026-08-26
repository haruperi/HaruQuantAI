# `.agents` — Artifact-Driven Agent Workflow

HaruQuantAI delivers development tasks through Planner → Executor → Reviewer with four interchangeable execution modes. The workflow is file-driven: chat memory is never the coordination authority.

## Active task workspace

```text
.agents/task/
├── planner.md
├── executor.md
├── reviewer.md
└── next-agent.md
```

The three role journals are append-only during an active task. `next-agent.md` is replace-only and contains the complete standalone prompt for the next reasoning role. All four files are zero bytes when no task is active and after successful close-out.

Reusable prompt truth lives only in `docs/templates/prompt/`. Runtime prompts are instantiated into `next-agent.md`; there is no second prompt-template tree under `.agents`.

## Core invariant

**No reasoning role may be invoked unless its complete prompt already exists in `.agents/task/next-agent.md` and has passed protocol validation.**

This includes the very first Planner invocation. Task activation is an explicit `ORCHESTRATOR / TASK_ACTIVATED -> PLANNER` transition: the orchestrator passes the clean-main gate, records the baseline, creates the deterministic task branch, materializes the canonical Planner prompt, validates it, and only then invokes or transports Planner.

## Modes

| Mode | Execution | Context isolation |
| --- | --- | --- |
| `solo` | This chat performs each role sequentially | Soft — role contract reset, not truly independent review |
| `delegate` | Fresh same-brand subagent per role | Fresh role context |
| `multi-delegate` | Fresh configured CLI process per role | Fresh process; cross-vendor diversity available |
| `manual` | User relays `next-agent.md` to a fresh chat | Fresh chat |

Every mode consumes the same validated `next-agent.md`, including initial Planner. Mode changes transport, not workflow semantics.

Run `.agents/configure.py` before using the CLI. `start` and `resume` consume `.agents/run-config.toml` and run role processes only in `multi-delegate` mode; `solo`, `delegate`, and `manual` use their documented chat transports. Repository location defaults to the checked-out repository, with `--repo` available for explicit overrides and tests.

## Canonical workflow truth

- `AGENTS.md` — contributor/role authority.
- `.agents/protocol.toml` — machine-readable transitions, gates, workspace paths, schema version.
- `.agents/PROCEDURE.md` — operator procedure and exact copy/paste chat text.
- `docs/templates/prompt/default.md` — prompt-design standard (MAIN/MINIMAL).
- `docs/templates/prompt/{planner,executor,reviewer,reviewer-closeout}.md` — canonical role prompts.
- `.agents/task/next-agent.md` — current instantiated next-role prompt.
- `.agents/runs/*.json` — runtime audit state (gitignored).
- `.agents/logs/` — immutable invocation prompt/transcript archive (gitignored).

## Session lifecycle

```text
ORCHESTRATOR READY
  └─ TASK NONE
       └─ task spec prepared
            └─ TASK_ACTIVATED
                 └─ create task branch
                      └─ materialize + validate Planner next-agent.md
                           └─ PLANNER Dry Run N
                                └─ PENDING_APPROVAL
                                     └─ owner: APPROVED: EXECUTE
                                          └─ EXECUTOR Report N
                                               ├─ BLOCKED ────────────────> PLANNER Dry Run N+1
                                               └─ READY_FOR_REVIEW ──────> REVIEWER Review N
                                                                              ├─ CHANGES_REQUESTED -> PLANNER N+1
                                                                              └─ PENDING_COMMIT
                                                                                   └─ owner: APPROVED: COMMIT
                                                                                        └─ REVIEWER close-out
                                                                                             └─ ACCEPTED
                                                                                                  └─ ORCHESTRATOR READY / TASK NONE
```

Owner approval is deterministic orchestration, not an LLM task. The orchestrator appends the exact execution gate record to `planner.md`; it does not re-invoke Planner merely to transcribe authorization.

## `next-agent.md` contract

Every reasoning-role invocation uses a complete prompt beginning with TOML front matter:

```toml
+++
prompt_schema_version = 1
run_id = "..."
task_id = "..."
iteration = 1
source_role = "ORCHESTRATOR"
target_role = "PLANNER"
handoff = "TASK_ACTIVATED"
branch = "feature/..."
baseline_commit = "..."
source_head = "..."
template_path = "docs/templates/prompt/planner.md"
requires_owner_gate = false
owner_gate = ""
+++
```

Later transitions use the same metadata contract. The orchestrator validates schema, transition, target template, branch, baseline, HEAD, protected role sentinels, owner-gate semantics, unfilled placeholders, prompt SHA-256, canonical-template SHA-256, and a working-tree fingerprint. Stale or contradictory artifacts fail closed.

Executor handoffs additionally carry exact normalized `allowed_write_paths`. Python snapshots tracked and relevant untracked content around each invocation, rejects role writes outside intrinsic/path authority, rejects ordinary role commits or branch switches, and suppresses retries after any failed mutating attempt.

State-mutating CLI commands hold the OS-backed `.agents/workflow.lock`. `cancel --reason "..."` records terminal `CANCELLED` state while preserving the branch, worktree, journals, and run evidence; ordinary resume is then refused.

Outgoing roles may populate task-specific facts but may not weaken the incoming role's canonical role, authority, methodology, quality criteria, or handoff rules.

## Structured handoff facts

Free-form `NEXT AGENT NOTES` are retired. Each full next-role prompt carries structured facts appropriate to the transition.

- Planner → Executor: approved scope, exact path authority, implementation order, requirements, validation, rollback, risks.
- Executor → Reviewer: changed paths, claims, commands/tests reported, limitations, deviations, assumptions, risks. These are explicitly labeled **UPSTREAM CLAIMS — UNTRUSTED UNTIL INDEPENDENTLY VERIFIED**.
- Executor → Planner (`BLOCKED`): blocker, evidence, partial state, affected paths, safe retained work, required decision.
- Reviewer → Planner: failed requirement/gate, independent evidence, required correction, retained valid work.

## Reviewer anti-anchoring

Reviewer follows three stages:

1. **Independent reconstruction** from original task, authorities, baseline, diff, resulting repository.
2. **Independent verification** with affected tests and non-mutating quality/architecture/usage checks.
3. **Claims reconciliation** only afterward by reading Planner/Executor journals.

The Reviewer never repairs implementation. Defects produce `CHANGES_REQUESTED`.

## Quick start

Configure transport when needed:

```bash
uv run .agents/configure.py
```

Then initialize/check the orchestrator before preparing and activating each task:

```bash
uv run .agents/orchestrator.py doctor
uv run .agents/make_task.py --list
uv run .agents/make_task.py 1.1
uv run .agents/orchestrator.py start --task-file .agents/task.toml
```

For chat-driven or manual orchestration, use the exact initialization, activation, owner-action, and manual-transport text in `.agents/PROCEDURE.md`.

Resume/gate relay examples:

```bash
uv run .agents/orchestrator.py resume
uv run .agents/orchestrator.py resume --approved
uv run .agents/orchestrator.py resume --reject-feedback "..."
uv run .agents/orchestrator.py resume --approved-commit
uv run .agents/orchestrator.py resume --reject-commit-feedback "..."
```

Runtime `run-config.toml`, `task.toml`, `logs/`, and `runs/` are intentionally gitignored. `task.example.toml`, `protocol.toml`, canonical prompts, role TOMLs, and the four zero-byte active-task files are tracked workflow source.

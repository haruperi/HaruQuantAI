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

The three role journals are append-only during an active task. `next-agent.md` is replace-only and contains the complete standalone prompt for the next role. All four files are zero bytes when no task is active and after successful close-out.

Reusable prompt truth lives only in `docs/templates/prompt/`. Runtime prompts are instantiated into `next-agent.md`; there is no second prompt-template tree under `.agents`.

## Modes

| Mode | Execution | Context isolation |
| --- | --- | --- |
| `solo` | This chat performs each role sequentially | Soft — role contract reset, not truly independent review |
| `delegate` | Fresh same-brand subagent per role | Fresh role context |
| `multi-delegate` | Fresh configured CLI process per role | Fresh process; cross-vendor diversity available |
| `manual` | User relays `next-agent.md` to a fresh chat | Fresh chat |

Every mode consumes the same `next-agent.md`. Mode changes transport, not workflow semantics.

## Canonical workflow truth

- `AGENTS.md` — contributor/role authority.
- `.agents/protocol.toml` — machine-readable transitions, gates, workspace paths, schema version.
- `docs/templates/prompt/default.md` — prompt-design standard (MAIN/MINIMAL).
- `docs/templates/prompt/{planner,executor,reviewer,reviewer-closeout}.md` — canonical role prompts.
- `.agents/task/next-agent.md` — current instantiated next-role prompt.
- `.agents/runs/*.json` — runtime audit state (gitignored).
- `.agents/logs/` — immutable invocation prompt/transcript archive (gitignored).

## State machine

```text
PLANNER Dry Run N
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
```

Owner approval is deterministic orchestration, not an LLM task. The orchestrator appends the exact execution gate record to `planner.md`; it does not re-invoke Planner merely to transcribe authorization.

## `next-agent.md` contract

Every non-terminal role handoff writes a complete prompt beginning with TOML front matter:

```toml
+++
prompt_schema_version = 1
run_id = "..."
task_id = "..."
iteration = 1
source_role = "PLANNER"
target_role = "EXECUTOR"
handoff = "PENDING_APPROVAL"
branch = "feature/..."
baseline_commit = "..."
source_head = "..."
template_path = "docs/templates/prompt/executor.md"
requires_owner_gate = true
owner_gate = "APPROVED: EXECUTE"
+++
```

The orchestrator validates schema, transition, target template, branch, baseline, HEAD, protected role sentinels, owner-gate semantics, unfilled placeholders, prompt SHA-256, canonical-template SHA-256, and a working-tree fingerprint. Stale or contradictory artifacts fail closed.

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

```bash
uv run .agents/configure.py
uv run .agents/make_task.py --list
uv run .agents/make_task.py 1.1
uv run .agents/orchestrator.py doctor
uv run .agents/orchestrator.py self-test
uv run .agents/orchestrator.py start --task-file .agents/task.toml
```

Resume/gate relay examples:

```bash
uv run .agents/orchestrator.py resume
uv run .agents/orchestrator.py resume --approved
uv run .agents/orchestrator.py resume --reject-feedback "..."
uv run .agents/orchestrator.py resume --approved-commit
uv run .agents/orchestrator.py resume --reject-commit-feedback "..."
```

Runtime `run-config.toml`, `task.toml`, `logs/`, and `runs/` are intentionally gitignored. `task.example.toml`, `protocol.toml`, canonical prompts, role TOMLs, and the four zero-byte active-task files are tracked workflow source.

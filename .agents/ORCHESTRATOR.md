# Chat Orchestrator Playbook

**You — this chat — are the orchestrator** of the three-role feature workflow
(Planner → Executor → Reviewer) defined by `AGENTS.md`. This playbook tells you
how to run it in any of four modes. The file-based protocol in section 1 is
identical for all modes; only the execution mechanism differs.

If `.agents/run-config.toml` is missing (or the owner asks to change setup),
run `python .agents/configure.py` first, or present the equivalent choice menu
yourself. Never guess a mode.

## 1. Protocol (every mode)

**Truth on file.** The journals `docs/dev/task/{planner,executor,reviewer}.md`
are the only coordination channel between roles and iterations. Entries are
append-only during a task. Every entry ends with an optional `NEXT AGENT NOTES :`
section followed by the mandatory three-line block:

```text
NEXT AGENT NOTES : <1-5 lines for the next agent, or None>
STOPPED : <PLANNER|EXECUTOR|REVIEWER>
ACTIVATING : <PLANNER|EXECUTOR|REVIEWER|NONE>
HANDOFF : <PENDING_APPROVAL|APPROVED_EXECUTE|READY_FOR_REVIEW|CHANGES_REQUESTED|ACCEPTED|BLOCKED>
```

**Task intake.** A task spec (`.agents/task.*.toml`) supplies the fields the
role templates need: task ids, request, exclusions, and optionally
`implementation_file`/`implementation_entry` — when present, completing the
feature includes marking that tracker entry `[x]` with `— evidence: path:line`
as an approved changed path (never in a blocker-resolution dry run).

**Entry gate (new task).** `main` checked out and clean (untracked `.agents/`
is ignorable), all three journals zero bytes. Record the baseline commit.

**State machine.**

```text
PLANNER dry run N → PENDING_APPROVAL → owner gate ─┬─ APPROVED: EXECUTE
               ▲                                   │   → PLANNER approval record
               │                                   │     → EXECUTOR report N
               │                                   └─ reject (feedback) → PLANNER N+1
               │                                     EXECUTOR → READY_FOR_REVIEW → REVIEWER
               └── BLOCKED / CHANGES_REQUESTED ◀────────────────────┘
                                                 REVIEWER → ACCEPTED → close-out, done
```

**Owner gate.** After every dry run, ask the owner. Authorization is ONLY the
exact standalone message `APPROVED: EXECUTE`. A rejection collects feedback and
returns to the Planner as the next iteration with the owner direction injected.

**Blockers.** An Executor `BLOCKED` (missing authority, unapproved path,
spec conflict...) is recorded with the agent's own NEXT AGENT NOTES as the
description; the next Planner iteration is a minimal blocker-resolution dry
run with the original scope explicitly suspended; it resumes after resolution.
A Planner gate `BLOCKED` needs an owner fix outside the workflow, then the
same dry-run number is retried. Keep a blocker ledger in the run state.

**Fail closed.** Missing or contradictory markers, wrong role identification,
or a gate violation stops progression. Surface the journal evidence; never
guess the next step and never repair another role's work yourself (only the
Reviewer accepts and closes out).

**Single writer.** Exactly one role works at a time, in order, on the task
branch. Never run roles concurrently.

**Run state and audit.** Maintain `.agents/runs/<run-id>.json` (iteration,
phase, branch, baseline, blocker ledger, history) and write every composed
prompt under `.agents/logs/`. Everything must survive a chat or terminal
crash; a fresh chat resumes from journals + run state.

**Close-out (Reviewer ACCEPTED).** Per the reviewer template: empty all three
journals, create the one task commit (pre-commit coverage gate included),
verify clean unchanged `main`, `git merge --ff-only`, delete the merged branch.
Never push.

## 2. Mode: SOLO

You perform **all three roles yourself, sequentially, in this chat**. For each
phase: load `.agents/templates/<role>.md`, fill the `{{placeholders}}` from the
task spec and run state, announce the phase, execute that role's instructions
yourself, then append the journal entry exactly as the role would (including
the three-line block and notes). The owner gate between dry run and
implementation still applies. Role discipline is sequential: complete and
journal the Planner work before any Executor action begins. When
self-reviewing, genuinely re-verify (re-run tests, inspect the diff) rather
than trusting your own implementation summary; if you find defects, mark the
review `CHANGES_REQUESTED` and loop back to re-planning like any other mode.

## 3. Mode: DELEGATE (same-brand subagents)

For each phase, spawn **one subagent** via your harness's subagent mechanism
with the composed role prompt as its task, working in this repository.
Configure model/effort from `run-config.toml` `[roles.*]` using your harness's
per-subagent model setting when it supports one; when it does not, run with
the chat default and state the configured tier in the prompt header so it is
on record. The subagent writes its journal; you read the markers and route per
section 1. Never spawn two role subagents concurrently. Relay the owner gate
yourself (ask the user in-chat, then act on the exact `APPROVED: EXECUTE`).

## 4. Mode: MULTI-DELEGATE (cross-vendor headless)

**Preferred:** drive the proven script — it already implements this entire
protocol with streaming, retries, and fail-closed gates:

```bash
python .agents/orchestrator.py doctor
python .agents/orchestrator.py start --task-file <task.toml>   # or: resume
python .agents/orchestrator.py resume --approved               # relay owner approval
python .agents/orchestrator.py resume --reject-feedback "..."  # relay rejection
```

Run it via your shell tool and watch the streamed output; on failure, read
`.agents/logs/`. Vendors, models, and effort levels are configured with
`python .agents/configure.py` (per-role vendor → model → effort menus),
which regenerates `.agents/<role>.toml` with the correct per-vendor CLI
flags; hand-edit those files only for exotic flags.

**Fallback** (script unusable): run each vendor CLI yourself with the composed
prompt file per `.agents/<role>.toml`, then parse the journals and route per
section 1 — you are then effectively a hand-run version of the script.

## 5. Mode: MANUAL (separate chats)

The pre-automation workflow, still fully supported. Each role runs in its own
chat (same or different vendor); the user relays.

As the orchestrating chat you can still help: compose each role prompt from
`.agents/templates/<role>.md` (fill placeholders from the task spec and the
current journals), save it to `.agents/logs/<timestamp>-<role>-prompt.md`, and
tell the user which chat to open next based on the latest handoff block:

| Latest block | Next chat |
| --- | --- |
| `PLANNER / PLANNER / PENDING_APPROVAL` | Owner decides; then a PLANNER chat with the approval message |
| `PLANNER / EXECUTOR / APPROVED_EXECUTE` | EXECUTOR chat |
| `EXECUTOR / REVIEWER / READY_FOR_REVIEW` | REVIEWER chat |
| `EXECUTOR / PLANNER / BLOCKED` | PLANNER chat (blocker-resolution dry run) |
| `REVIEWER / PLANNER / CHANGES_REQUESTED` | PLANNER chat (next dry run) |
| `REVIEWER / NONE / ACCEPTED` | Task complete |

When a role chat finishes, verify its journal markers before announcing the
next step; never take the chat's word over the journal.

## 6. Reference

- Templates: `.agents/templates/{planner,planner_approval,executor,reviewer}.md`
- Task specs: `.agents/task.*.toml` · Vendor flags: `.agents/<role>.toml`
- Script driver: `.agents/orchestrator.py` · Picker: `.agents/configure.py`
- Full system docs: `.agents/README.md`

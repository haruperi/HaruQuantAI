# .agents — Cross-Brand Agent Orchestrator

Automates the `AGENTS.md` three-role workflow: when the Planner finishes a dry
run, the orchestrator collects owner approval, then launches the Executor;
when the Executor finishes, it launches the Reviewer; `CHANGES_REQUESTED` /
`BLOCKED` loop back to the Planner for the next numbered dry run. Roles may be
any mix of CLI brands (claude, codex, agy, gemini, qwen, ...) because agents
never talk to each other directly — the task journals in `docs/dev/task/` are
the shared memory and each agent is launched headlessly with one role.

This tooling lives outside the AGENTS.md workflow by owner decision
(2026-08-24). It orchestrates that workflow; it is not part of the product.

## Quick start

```bash
python .agents/orchestrator.py doctor                 # check configs/CLIs/repo
python .agents/orchestrator.py self-test              # stub end-to-end run
python .agents/orchestrator.py start --task-file .agents/task.test.toml   # real end-to-end test
python .agents/orchestrator.py start --task-file .agents/task.example.toml  # real task template
python .agents/orchestrator.py resume                 # continue after interrupt
```

Task specs may reference an implementation tracker (`implementation_file` +
`implementation_entry`, e.g. `docs/dev/IMPLEMENTATION_ORDER.md` entry `2.8`). The
Planner then includes marking that entry complete (`[x]` plus `— evidence: path:line`)
among the approved changed paths, so progress lands in the tracker through the normal
reviewed merge — never as an out-of-band edit. `.agents/task.test.toml` pairs with
`docs/dev/IMPLEMENTATION_TEST.md` (temporary `D-TEST` domain) for the first real run.

## How it works

```
start ──▶ PLANNER (dry run N) ─▶ PENDING_APPROVAL ─▶ OWNER GATE ─┬─ approve ─▶ PLANNER (record approval)
                ▲                                               │                 │
                │                                               └─ reject ───────┘ (feedback)
                │                                                                        ▼
                │                                                   EXECUTOR (report N) ─┬─ READY_FOR_REVIEW ─▶ REVIEWER (review N)
                │                                                                        │                          ├─ CHANGES_REQUESTED ─┐
                └────────────────── BLOCKED / CHANGES_REQUESTED / reject ◀──────────────┴──────────────────────────┘
                                                                                                      └─ ACCEPTED ─▶ done
```

- **Shared memory**: the journals `docs/dev/task/{planner,executor,reviewer}.md`.
  Each prompt ends with a mandatory contract: the agent must finish its journal
  entry with a three-line block — `STOPPED : <PLANNER|EXECUTOR|REVIEWER>`,
  `ACTIVATING : <PLANNER|EXECUTOR|REVIEWER|NONE>`, and
  `HANDOFF : <PENDING_APPROVAL|APPROVED_EXECUTE|READY_FOR_REVIEW|CHANGES_REQUESTED|ACCEPTED|BLOCKED>`.
  The orchestrator routes on HANDOFF, cross-checks STOPPED against the role that
  actually ran, and records ACTIVATING for tracking (a mismatch warns but does
  not stop the pipeline). A complete block printed in the agent's final answer
  is accepted as a warned fallback. `ACTIVATING : NONE` marks terminal states
  (Reviewer ACCEPTED, Planner BLOCKED awaiting an owner decision).
- **Blocker memory**: every BLOCKED outcome (Planner gate failure or Executor
  blocker) is recorded as an OPEN blocker in the run state. The description is
  extracted automatically from the blocking agent's NEXT AGENT NOTES and shown
  with a journal evidence pointer — the owner is never asked to re-describe
  what the agent already documented. The next Planner iteration becomes a
  minimal blocker-resolution dry run (the original scope is explicitly suspended);
  once that dry run is implemented, the blocker is marked RESOLVED and the
  following dry runs continue the ORIGINAL task. The blocker ledger is
  injected into correction contexts and the reviewer prompt, and the reviewer
  must CHANGES_REQUESTED ("continue the original scope") rather than accept
  while the original task request is unmet. Planner BLOCKED stops for an
  owner decision; `resume` afterwards continues with the blocker dry run.
- **Next-agent notes**: each journal entry carries a `NEXT AGENT NOTES :`
  section (1-5 lines) just above the handoff block. The orchestrator scrapes
  it and injects it into the next agent's prompt (`Handoff notes : From X:`),
  so agents exchange targeted context without ever authoring each other's
  prompts; notes are cleared on acceptance.
- **Single writer preserved**: one agent runs at a time; the loop blocks.
- **Owner gate preserved**: after every dry run the orchestrator pauses in the
  terminal for the exact message `APPROVED: EXECUTE` (or `reject` with
  feedback, or `abort`). The approval is relayed to a fresh Planner invocation
  which appends the approval record itself, per AGENTS.md writer rules.
  `--auto-approve` exists but bypasses a deliberate safety latch — avoid it.
- **Live agent output**: every agent invocation streams its stdout/stderr into
  the terminal as it happens (`| ` = agent stdout, `! ` = agent stderr), and a
  heartbeat line (`[123s] agent still running...`) appears after
  `stream_heartbeat_seconds` of quiet, so long invocations are never silent.
  Disable per-terminal echo with `stream_agent_output = false` in
  `orchestrator.toml`; the full transcript is always captured in `.agents/logs/`
  regardless. On timeout the whole process tree is killed (`taskkill /T`).
  Transient non-zero exits are automatically retried (`agent_retry_attempts`,
  default 1, 5s apart); timeouts are never auto-retried. Note agy's own
  `--print-timeout` (default 5m) caps headless runs — the executor command
  raises it to 110m below the orchestrator's ceiling.
- **Fail closed**: missing/invalid marker, non-branch repo state, or timeouts
  stop the run with the invocation log tail; state is saved for `resume`.

## Files

| Path | Purpose |
| --- | --- |
| `orchestrator.py` | State-machine router, agent launcher, gates, subcommands |
| `orchestrator.toml` | Repo path, journals, limits, role wiring |
| `planner.toml` / `executor.toml` / `reviewer.toml` | Per-role CLI command, model args, delivery mode, template |
| `templates/*.md` | Role prompts with `{{placeholders}}` + HANDOFF contract |
| `tests/stub_agent.py` | Scripted agents used by `self-test` |
| `task.example.toml` | Example task spec for `start` |
| `logs/`, `runs/` | Invocation prompts/logs and resumable run state (gitignored) |

## Swapping brands

Edit the role TOMLs. Commands are argv lists; `model_args` are appended.
Prompt delivery modes: `file` (default — prompt written under `logs/`, agent
gets a short pointer argument; safest with Windows `.cmd` shims), `arg`
(prompt appended as one argument, or substituted for a `{prompt}` token),
`stdin`. Examples:

```toml
# codex (current planner): model + reasoning effort via config overrides.
# Note: --full-auto was removed in current Codex; use the sandbox flag.
command = ["codex", "exec", "-s", "workspace-write"]
model_args = ["-m", "gpt-5.6-sol", "-c", "model_reasoning_effort=high"]

# agy (current executor): reasoning level is part of the slug. NOTE: agy's -p
# takes the NEXT token as its prompt value, so -p must be the LAST token and
# the orchestrator-appended prompt pointer becomes its value.
command = ["agy", "--dangerously-skip-permissions", "--model", "gemini-3.7-flash-high", "-p"]

# cline (current reviewer): Z.ai GLM via the provider id in ~/.cline.
# WARNING: cline's `-p` flag is PLAN mode (not print mode) — the Reviewer
# needs act mode for tests and the close-out commit, so never add `-p`.
command = ["cline", "-P", "zai-coding-plan", "-m", "glm-5.3", "--thinking", "high"]

# claude
command = ["claude", "-p", "--dangerously-skip-permissions"]
```

Headless agents cannot answer interactive permission prompts, so each role's
command must include its CLI's auto-approval flag. Safety rests on the owner
approval gate plus git branch isolation (`main` is never touched until the
Reviewer's accepted close-out).

## Keeping prompts in sync

`templates/*.md` mirror `docs/dev/prompt/{planner,executor,reviewer}.md` with
`{{placeholders}}`, headless adjustments (the Planner does not wait for
approval in-session), and the HANDOFF contract. If you edit the authoritative
prompts in `docs/dev/prompt/`, mirror the changes here (or vice versa) — the
templates in this folder are what agents actually receive.

## Notes and limits

- **Everything is file-based; the terminal is display only.** Run state lives
  in `.agents/runs/<run-id>.json` (rewritten after every phase transition,
  blocker, failure, and interrupt), every composed prompt and full invocation
  transcript lives in `.agents/logs/`, and agent memory lives in the journals.
  After any crash or terminal kill, `python .agents/orchestrator.py resume`
  re-enters at the last saved phase. Caveat: a run interrupted while an agent
  invocation was in flight re-runs that phase; the agent's own journal-based
  entry gates keep the re-run from double-appending.
- The entry gate requires clean `main` with zero-byte journals (untracked
  `.agents/` itself is ignored). If `start` refuses, commit or stash first.
- `resume` restarts from the saved phase (`approve`, `executor`, ...). The
  saved state lives in `runs/<run-id>.json` with full phase history.
- Every invocation's composed prompt and full stdout/stderr land in `logs/`
  for audit; nothing there is committed (gitignored).
- The orchestrator never creates/switches branches, commits, or pushes — only
  agents do, each within its own role's authority.

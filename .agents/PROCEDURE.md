# Agent Workflow — Full Procedure

Repeatable end-to-end procedure for delivering a feature through the
three-role workflow (Planner → Executor → Reviewer) in any mode.

## Step 0 — Set up the agent mode (once, or when changing approach)

```bash
uv run .agents/configure.py
```

- Choose: `solo` / `delegate` (same-brand subagents) / `multi-delegate`
  (cross-vendor CLIs) / `manual` (separate chats).
- Menus cascade per role: vendor → vendor-specific model → effort level.
- Writes `.agents/run-config.toml` (gitignored). In multi-delegate mode it
  also regenerates `.agents/{planner,executor,reviewer}.toml` with the
  correct per-vendor CLI flags.

## Step 1 — Generate the task spec from the implementation order

```bash
uv run .agents/make_task.py --list     # open entries: 1.1 FEAT-WS-MANAGE_WORKSPACES, 1.2, ...
uv run .agents/make_task.py 1.1        # writes .agents/task.toml
```

The spec is derived from the tracker entry (feature id, slug, FR list,
tracker wiring). Edit `.agents/task.toml` freely (exclusions, review focus)
before starting; it is gitignored scratch.

## Step 2 — Kick off the orchestrating chat (modes 1–3)

Open a fresh chat with your chosen orchestrator and send:

> Read `docs\PROJECT.md` and `docs\ARCHITECTURE.md` for project context.
> Read `docs\dev\feature_implementation_pipeline.md`, `AGENTS.md` and `.agents/ORCHESTRATOR.md` in order to implement the
> next task `.agents/task.toml`.

The chat reads the mode from `run-config.toml` and drives the whole loop:
plan → owner gate → approval record → execute → review → close-out.

## Step 3 — During the run (your only job: the gates)

- After every dry run you get the **owner gate**. To authorize, reply with
  exactly: `APPROVED: EXECUTE`. To send it back to the Planner, reject and
  give one line of feedback (it becomes the next dry run's owner direction).
- When the Reviewer's verification passes you get the **owner commit gate**:
  nothing is committed yet. Inspect the branch yourself if you want a human
  look (`git diff <baseline>..HEAD`), then authorize with exactly:
  `APPROVED: COMMIT` — or reject with feedback to return the task to the
  Planner.
- `BLOCKED` is a normal outcome (e.g. an unapproved path discovered
  mid-work): the next dry run is a minimal blocker-resolution plan — the
  original scope is explicitly suspended and resumes afterwards. Approve it
  like any other dry run.
- `CHANGES_REQUESTED` from the Reviewer loops back to the Planner for the
  next numbered dry run — also gated.
- Watch progress live: streamed agent output (`|` stdout / `!` stderr) plus
  heartbeat lines; every prompt and transcript is archived in `.agents/logs/`.

## Step 4 — If anything stops (crash, closed terminal, Ctrl+C)

Everything is file-based; nothing is lost.

- Mode 3:
  ```bash
  uv run .agents/orchestrator.py resume
  # relay a pending gate decision non-interactively:
  uv run .agents/orchestrator.py resume --approved
  uv run .agents/orchestrator.py resume --reject-feedback "widen the scope"
  uv run .agents/orchestrator.py resume --approved-commit
  uv run .agents/orchestrator.py resume --reject-commit-feedback "..."
  ```
- Modes 1–2: open a fresh chat and send:
  > Read `AGENTS.md` and `.agents/ORCHESTRATOR.md`, then resume the active
  > task from `.agents/runs` and the journals in `docs/dev/task/`.

## Step 5 — Completion

When you authorize with `APPROVED: COMMIT`, the Reviewer performs the
close-out: journals are emptied, the one task commit is created (pre-commit
coverage gate included), merged to `main` fast-forward only, the task branch
is deleted, and the implementation-order entry is marked `[x]` with
`— evidence:` lines. Verify:

```bash
git log --oneline -1     # the task commit is on main
git status               # clean
```

## Step 6 — Mode 4 (manual) variant

Same Steps 0–1, then run each role in its own chat (any mix of vendors).
Compose each role prompt from `.agents/templates/<role>.md` and use the
relay table in `.agents/ORCHESTRATOR.md` §5 to know which chat to open next
after each three-line handoff block. You are the owner gate: relay
`APPROVED: EXECUTE` into the Planner chat yourself.

## Step 7 — Maintenance (as needed)

```bash
uv run .agents/orchestrator.py doctor      # configs, CLIs, repo gates
uv run .agents/orchestrator.py self-test   # full state machine, stub agents
```

- Switch mode any time by rerunning Step 0 (between tasks, not mid-task).
- Adjust role CLI flags by editing `.agents/<role>.toml` (or rerun
  configure.py in multi-delegate mode).
- Run audit lives in `.agents/runs/<run-id>.json`; transcripts in
  `.agents/logs/` (both gitignored).
- Next feature: back to Step 1 with the next open entry.

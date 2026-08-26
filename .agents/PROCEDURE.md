# Agent Workflow — Complete Operational Procedures

This document provides complete, self-contained, end-to-end operational procedures for the three execution workflows in HaruQuantAI.

Every workflow shares the identical underlying protocol, state machine, and artifact contract defined in `AGENTS.md` and `.agents/protocol.toml`. The only difference between paths is the **transport mechanism**.

Choose the procedure that matches your operating mode:

- **[Part 1: Chat-Driven Orchestration](#part-1--chat-driven-orchestration-solo-and-delegate-modes)** — For `solo` (single conversational agent) and `delegate` (subagent per role) modes (8 steps).
- **[Part 2: CLI-Driven Orchestration](#part-2--cli-driven-orchestration-multi-delegate-mode)** — For `multi-delegate` mode (autonomous CLI process per role via `.agents/orchestrator.py`) (8 steps).
- **[Part 3: Full Manual Mode Procedure](#part-3--full-manual-mode-procedure-manual-mode)** — For `manual` mode (human transports `.agents/task/next-agent.md` between fresh chat windows) (8 steps).
- **[Part 4: Maintenance & Diagnostics](#part-4--maintenance-and-diagnostics)** — Verification and test suite commands.

---

## Common Prerequisites

### 1. Configure Orchestration Mode

Run the interactive configuration wizard to select your desired execution mode (`solo`, `delegate`, `multi-delegate`, or `manual`):

```bash
uv run .agents/configure.py
```

Mode changes transport only; every reasoning role consumes the same validated `.agents/task/next-agent.md` artifact.

### 2. Generate or Prepare the Task Specification

For product features (`FEAT-...`) or functional requirements (`FR-...`), generate the runtime `.agents/task.toml` file from the implementation order:

List available roadmap items:

```bash
uv run .agents/make_task.py --list
```

Generate `.agents/task.toml` for a specific item (e.g., item 1.1):

```bash
uv run .agents/make_task.py 1.1
```

Chat prompt to fill out `.agents/task.toml` for a specific task:

```text
Update .agents\task.toml with {implementation_file_name} {task_item}
```

For foundation, refactor, or custom tasks, manually author `.agents/task.toml` using `task_kind = "task"` (rather than `"feature"`). Refer to `.agents/task.example.toml` for the schema.

At this point:

```text
ORCHESTRATOR : READY
TASK_SPEC : READY
TASK : NOT_ACTIVE
```

> [!IMPORTANT]
> **Task activation invariant:** The presence of `.agents/task.toml` on disk does **not** activate work, create branches, or invoke any role. No reasoning role may run until its complete prompt has been materialized into `.agents/task/next-agent.md` and validated against `.agents/protocol.toml`.

---

## Part 1 — Chat-Driven Orchestration (Solo and Delegate Modes)

Use this complete procedure when interacting with an AI coding assistant inside an IDE or chat interface in `solo` or `delegate` mode.

```text
ORCHESTRATOR READY / TASK NONE
  → Step 1: Initialize Chat Orchestrator
  → Step 2: Activate Task & Run Planner
  → Step 3: Owner Execution Decision (APPROVED: EXECUTE)
  → Step 4: (Optional) Resolve Planner Blockers
  → Step 5: Run Executor & Transition to Reviewer
  → Step 6: Reviewer Verification & Findings
  → Step 7: Owner Commit Decision (APPROVED: COMMIT)
  → Step 8: Reviewer Close-Out & Acceptance
  → ACCEPTED / ORCHESTRATOR READY
```

---

### Chat Step 1 — Initialize the Orchestrator Chat

Open a fresh chat session and paste the exact orchestrator initialization prompt:

```text
Initialize the HaruQuantAI development orchestrator for this repository.

Read and follow:
- AGENTS.md
- .agents/ORCHESTRATOR.md
- .agents/protocol.toml
- .agents/README.md

Initialize yourself only as the orchestration controller.

Do not activate a task yet.
Do not invoke Planner, Executor, or Reviewer yet.
Do not create a task branch.
Do not modify implementation files.
Do not modify any .agents/task/ journal.
Do not infer a task from previous chat history.

Verify that the repository and active-task workspace are in a valid idle state.

When initialization is complete, stop and report:

ORCHESTRATOR : READY
TASK : NONE
AWAITING : TASK_SPEC
```

**Expected response:**

```text
ORCHESTRATOR : READY
TASK : NONE
AWAITING : TASK_SPEC
```

---

### Chat Step 2 — Activate the Task and Run Planner

Paste the exact activation prompt into the initialized orchestrator chat:

```text
Activate and run the task defined in .agents/task.toml.

Use the HaruQuantAI workflow defined by:
- AGENTS.md
- .agents/ORCHESTRATOR.md
- .agents/protocol.toml

Treat .agents/task.toml as the authoritative runtime task input.

Perform the task activation sequence:

1. validate the clean-main entry gate;
2. record the main baseline commit;
3. derive and validate the deterministic task branch;
4. create and switch to that task branch from the recorded baseline;
5. instantiate the canonical Planner prompt into .agents/task/next-agent.md;
6. validate the ORCHESTRATOR / TASK_ACTIVATED -> PLANNER transition and the complete next-agent artifact;
7. only after successful validation, activate Planner using the exact contents of .agents/task/next-agent.md.

Planner must not recreate or switch the task branch.

Continue orchestration until owner action is required.

Do not execute implementation before my exact:

APPROVED: EXECUTE
```

The orchestrator creates the deterministic task branch, materializes the Planner prompt in `.agents/task/next-agent.md`, and runs Planner.

**Expected first owner gate:**

```text
STOPPED : PLANNER
ACTIVATING : EXECUTOR
HANDOFF : PENDING_APPROVAL
```

Executor is **never** invoked before explicit owner authorization.

---

### Chat Step 3 — Owner Execution Decision

Inspect the dry-run plan in `.agents/task/planner.md`.

#### Option 1A: Approve Execution in Chat

When the dry run is satisfactory, approve implementation with the exact standalone message:

```text
APPROVED: EXECUTE
```

The orchestrator appends the deterministic approval record to `.agents/task/planner.md` and activates Executor using the already-materialized prompt in `.agents/task/next-agent.md`.

#### Option 1B: Reject the Dry Run in Chat

If the plan requires corrections, paste:

```text
REJECTED: EXECUTE

Owner direction:
<describe exactly what must change in the dry run>
```

The orchestrator instantiates a fresh Planner correction prompt containing the owner direction and re-runs Planner.

---

### Chat Step 4 — Handle Planner Blockers

If Planner returns `BLOCKED`, orchestration halts until the documented external cause is resolved (e.g., in specifications or repository dependencies).

After resolving the external cause, reply in chat:

```text
RESOLVED: PLANNER BLOCKER

Resolution evidence:
<what changed and where the Planner can verify it>
```

The orchestrator records the resolution evidence and treats the previous pending Planner artifact as stale because the repository or specification may have changed. It verifies the active task branch and run state, materializes a fresh canonical Planner prompt, validates `ORCHESTRATOR / BLOCKER_RESOLVED → PLANNER` against the current task state, and only then resumes Planner. Resolving the blocker does not approve execution; a later `PENDING_APPROVAL` still requires `APPROVED: EXECUTE`.

> [!NOTE]
> Executor `BLOCKED` does not require immediate owner intervention; it automatically routes to Planner for blocker-resolution planning. Owner action is needed only if Planner subsequently reports `BLOCKED` or reaches `PENDING_APPROVAL`.

---

### Chat Step 5 — Run Executor and Transition to Reviewer

When Executor finishes implementing the approved scope, it writes its report to `.agents/task/executor.md`, materializes the complete Reviewer prompt into `.agents/task/next-agent.md`, and yields:

```text
STOPPED : EXECUTOR
ACTIVATING : REVIEWER
HANDOFF : READY_FOR_REVIEW
```

At this role boundary, the active contract transitions to **`ROLE: REVIEWER`** using the prompt in `.agents/task/next-agent.md`.

#### Option 1C — Continue the Workflow Into Reviewer

`READY_FOR_REVIEW` already makes `EXECUTOR / READY_FOR_REVIEW → REVIEWER` a valid protocol transition. The owner is not approving the implementation and no workflow decision is being made. If Solo chat ends the current assistant turn before Reviewer can begin, send this transport/resume input:

```text
CONTINUE: REVIEWER
```

This input exists only because a chat assistant cannot send itself a new user turn. It grants no authority and changes no scope. On receipt, the chat orchestrator verifies the active state and exact Executor handoff, loads and validates the already-materialized `.agents/task/next-agent.md` as an `EXECUTOR / READY_FOR_REVIEW → REVIEWER` transition, switches the active role contract, and begins Reviewer Stage A without another approval. If the active state does not match `READY_FOR_REVIEW`, `CONTINUE: REVIEWER` fails closed and never force-routes Reviewer.

Input classes are deliberately distinct:

- authorization: `APPROVED: EXECUTE` and `APPROVED: COMMIT`;
- decision/routing: rejection messages and `RESOLVED: PLANNER BLOCKER` evidence;
- transport/resume only: `CONTINUE: REVIEWER`.

#### Option 1D: Intervene or Re-plan Before Review

If the owner inspects the Executor report or working tree and requires adjustments before review:

```text
REJECTED: EXECUTE

Owner direction:
<describe what must be adjusted before review>
```

The orchestrator routes feedback back to Planner for a revised dry run.

---

### Chat Step 6 — Reviewer Verification and Findings

Reviewer executes with strict anti-anchoring, performing a 3-stage independent review:

1. **Stage A — Independent Reconstruction & Code Inspection:** Before reading upstream journals, Reviewer inspects the original task, `AGENTS.md`, architecture guides, baseline commit, complete branch diff (`git diff`), staged/unstaged changes, untracked paths, and the actual implementation files. It derives what code should exist and what quality criteria must be satisfied.
2. **Stage B — Independent Verification:** Reviewer runs change-scoped tests, type checks (`mypy`), linter checks (`ruff`), and usage evidence checks directly. Upstream claims in journals are untrusted until verified.
3. **Stage C — Dry-Run, Report, and Code Reconciliation:** Reviewer reads `.agents/task/planner.md` (the approved dry run) and `.agents/task/executor.md` (the execution report), verifies journal cryptographic hashes (`approved_plan_hash`, `executor_report_hash`), and reconciles the approved dry-run plan against the execution report and against the actual code changes to ensure all requirements were met without unauthorized scope expansion.

Review outcomes:

- If defects, missing requirements, or scope deviations are found, Reviewer outputs `CHANGES_REQUESTED` and routes back to Planner for Dry Run N+1.
- If all checks and tests pass, Reviewer halts at `PENDING_COMMIT` for the owner commit gate.

---

### Chat Step 7 — Owner Commit Decision

Inspect the review findings in `.agents/task/reviewer.md` and verify the working tree diff.

#### Option 1E: Approve Commit and Close-Out in Chat

When Reviewer reaches `PENDING_COMMIT` and the work is verified, approve close-out with the exact standalone message:

```text
APPROVED: COMMIT
```

The orchestrator re-verifies the pending prompt, reviewed HEAD, and complete working-tree fingerprint before triggering close-out.

#### Option 1F: Reject Commit Authorization in Chat

If the work must not be committed or requires further changes:

```text
REJECTED: COMMIT

Owner direction:
<describe why the reviewed state must not be committed and what must change>
```

The orchestrator invalidates the close-out authorization and instantiates a fresh Planner correction prompt for a new dry run.

---

### Chat Step 8 — Reviewer Close-Out and Acceptance

After exact `APPROVED: COMMIT`, Reviewer performs administrative close-out:

1. Re-verifies unchanged reviewed state;
2. Records commit authorization;
3. Confirms the immutable close-out archive exists and runs the final gates;
4. Stages only approved implementation paths and creates exactly one local task commit;
5. Only after the commit succeeds, empties all four `.agents/task/` workspace files and verifies the task branch is clean;
6. Verifies clean `main` at the baseline;
7. Fast-forward merges the task branch to `main` (`git merge --ff-only`);
8. Verifies the exact one-commit lineage and approved committed-path set;
9. Safely deletes the merged task branch (`git branch -d`) and verifies the zero-byte task workspace;
10. Marks the run `ACCEPTED`.

**Final terminal state:**

```text
STOPPED : REVIEWER
ACTIVATING : NONE
HANDOFF : ACCEPTED
```

The orchestrator resets to idle:

```text
ORCHESTRATOR : READY
LAST_TASK : ACCEPTED
TASK : NONE
AWAITING : TASK_SPEC
```

---

## Part 2 — CLI-Driven Orchestration (Multi-Delegate Mode)

Use this complete procedure when executing tasks through the automated terminal runner (`.agents/orchestrator.py`). The CLI handles protocol validation, task activation, subagent process management, prompt/transcript logging, and state persistence.

```text
Doctor Check & Orchestration Flow
  → Step 1: Verify Environment and Installation (`doctor`)
  → Step 2: Activate Task and Run Planner (`start`)
  → Step 3: Owner Execution Decision (`resume --approved` / `--reject-feedback`)
  → Step 4: (Optional) Resolve Planner Blockers (`resume --resolve-planner-blocker "<resolution evidence>"`)
  → Step 5: Run Executor and Transition to Reviewer
  → Step 6: Reviewer Verification and Findings
  → Step 7: Owner Commit Decision (`resume --approved-commit` / `--reject-commit-feedback`)
  → Step 8: Reviewer Close-Out and Acceptance
```

---

### CLI Step 1 — Verify Environment and Installation

Run the orchestrator doctor command to validate configuration, prompt templates, role CLI executables, and workspace health:

```bash
uv run .agents/orchestrator.py doctor
```

All checks must report `[ok]`.

---

### CLI Step 2 — Activate Task and Run Planner

Launch the orchestrator with the prepared task specification:

```bash
uv run .agents/orchestrator.py start --task-file .agents/task.toml
```

The CLI executes the deterministic `TASK_ACTIVATED` transition, creates the task branch, instantiates and validates the initial Planner prompt, invokes the Planner CLI process, and pauses at the first owner gate:

```text
STOPPED : PLANNER
ACTIVATING : EXECUTOR
HANDOFF : PENDING_APPROVAL
```

Executor is **never** launched before owner approval.

---

### CLI Step 3 — Owner Execution Decision via CLI

Inspect the generated plan in `.agents/task/planner.md` or review the full execution logs in `.agents/logs/`.

#### Option 2A: Approve Execution via CLI

To approve the dry-run plan and begin implementation:

```bash
uv run .agents/orchestrator.py resume --approved
```

The CLI appends the deterministic gate record to `.agents/task/planner.md`, validates the Executor prompt, and launches the Executor subagent process.

#### Option 2B: Reject the Dry Run via CLI

To reject the plan and request revisions from Planner:

```bash
uv run .agents/orchestrator.py resume --reject-feedback "<exact explanation of required changes>"
```

The CLI instantiates a fresh Planner correction prompt with your feedback and re-invokes Planner.

---

### CLI Step 4 — Handle Blockers and Corrections via CLI

- **Planner Blocked**: If Planner reports `BLOCKED`, resolve the external blocker, then provide explicit resolution evidence so the controller replaces the stale prompt with a fresh `BLOCKER_RESOLVED` Planner artifact:

  ```bash
  uv run .agents/orchestrator.py resume --resolve-planner-blocker "<resolution evidence>"
  ```

- **Executor Blocked / Reviewer Changes Requested**: The CLI handles these transitions automatically, routing work back to Planner. If the run paused or halted due to an external interruption, continue with:

  ```bash
  uv run .agents/orchestrator.py resume
  ```

---

### CLI Step 5 — Run Executor and Transition to Reviewer

Following execution approval, the CLI launches **Executor** to implement approved changes, write `.agents/task/executor.md`, and materialize the Reviewer prompt into `.agents/task/next-agent.md`:

```text
STOPPED : EXECUTOR
ACTIVATING : REVIEWER
HANDOFF : READY_FOR_REVIEW
```

In multi-delegate mode, the controller automatically launches Reviewer. No user transport input or approval is involved.

---

### CLI Step 6 — Reviewer Verification and Findings via CLI

The CLI executes **Reviewer** to perform the 3-stage independent review:

1. **Stage A (Code Inspection):** Inspects actual repository files, `git diff`, and uncommitted changes against task specifications.
2. **Stage B (Independent Verification):** Executes test suites, type checking, and linting directly.
3. **Stage C (Reconciliation):** Verifies journal hashes and reconciles the approved dry-run plan (`planner.md`) against the execution report (`executor.md`) and actual code changes.

Outcomes:

- If issues are detected, Reviewer outputs `CHANGES_REQUESTED` and the CLI routes back to Planner.
- If all checks pass, Reviewer halts at `PENDING_COMMIT` for the owner commit gate.

---

### CLI Step 7 — Owner Commit Decision via CLI

Inspect the Reviewer findings in `.agents/task/reviewer.md` and verify `git diff`.

#### Option 2C: Approve Commit and Close-Out via CLI

To approve the reviewed work and initiate administrative merge/close-out:

```bash
uv run .agents/orchestrator.py resume --approved-commit
```

The CLI verifies working tree fingerprints, invokes Reviewer close-out, commits changes, fast-forward merges to `main`, and deletes the task branch.

#### Option 2D: Reject Commit Authorization via CLI

To reject the commit and route back to Planner for modifications:

```bash
uv run .agents/orchestrator.py resume --reject-commit-feedback "<reason for rejection and required changes>"
```

---

### CLI Step 8 — Reviewer Close-Out and Acceptance via CLI

Upon successful close-out, the CLI reports:

```text
STOPPED : REVIEWER
ACTIVATING : NONE
HANDOFF : ACCEPTED
```

Verify that:

- `main` branch is clean and contains the new commit.
- All four files in `.agents/task/` are 0 bytes.
- Run state is archived under `.agents/runs/` and logs in `.agents/logs/`.

---

### CLI Commands Reference and Cheat Sheet

| Command | Purpose |
| --- | --- |
| `uv run .agents/orchestrator.py doctor` | Health-check protocol, templates, CLIs, and task workspace |
| `uv run .agents/orchestrator.py self-test` | Run end-to-end protocol test in an isolated repository |
| `uv run .agents/orchestrator.py start --task-file .agents/task.toml` | Activate a task and run Planner |
| `uv run .agents/orchestrator.py resume` | Continue a paused non-gated run; Executor-to-Reviewer routing is automatic and Planner blocker resolution requires the dedicated option below |
| `uv run .agents/orchestrator.py resume --resolve-planner-blocker "<resolution evidence>"` | Replace a stale blocked-Planner artifact with a fresh canonical `BLOCKER_RESOLVED` Planner prompt |
| `uv run .agents/orchestrator.py resume --approved` | Approve execution gate (`APPROVED: EXECUTE`) |
| `uv run .agents/orchestrator.py resume --reject-feedback "<notes>"` | Reject execution gate and route feedback to Planner |
| `uv run .agents/orchestrator.py resume --approved-commit` | Approve commit gate (`APPROVED: COMMIT`) |
| `uv run .agents/orchestrator.py resume --reject-commit-feedback "<notes>"` | Reject commit gate and route feedback to Planner |

---

## Part 3 — Full Manual Mode Procedure (Manual Mode)

Manual mode uses the identical protocol, rules, and artifacts as automated modes. The operator manually transports the exact contents of `.agents/task/next-agent.md` between fresh role chat sessions.

```text
Manual Orchestrator Chat (Controller)
  ├── Manual Step 1: Initialize Orchestrator Chat
  ├── Manual Step 2: Activate Task & Run Planner -> Generates next-agent.md
  │
  ├── Manual Step 3: Owner Execution Decision (APPROVED: EXECUTE)
  │
  ├── Manual Step 4: (Optional) Resolve Planner Blockers
  │
  ├── Manual Step 5: Run Executor & Transition to Reviewer (READY_FOR_REVIEW)
  │
  ├── Manual Step 6: Run Reviewer Verification & Findings (PENDING_COMMIT)
  │
  ├── Manual Step 7: Owner Commit Decision (APPROVED: COMMIT)
  │
  └── Manual Step 8: Run Reviewer Close-Out & Acceptance (ACCEPTED)
```

---

### Manual Step 1 — Initialize the Manual Orchestrator Chat

Open one dedicated chat session that will serve as the orchestration controller throughout the task. Paste exactly:

```text
Initialize the HaruQuantAI development orchestrator for this repository in MANUAL mode.

Read and follow:
- AGENTS.md
- .agents/ORCHESTRATOR.md
- .agents/protocol.toml
- .agents/README.md

You are the orchestration controller only.

Do not act as Planner, Executor, or Reviewer.
Do not implement or review work yourself.
Do not activate a task yet.

In manual mode, I will transport the exact contents of .agents/task/next-agent.md into fresh role chats when you instruct me to do so.

You must:
- validate workflow state;
- tell me exactly which role chat to open;
- tell me exactly which file to paste;
- process owner gates;
- never summarize or reconstruct a role prompt when .agents/task/next-agent.md already exists.

When ready, report:

ORCHESTRATOR : READY
MODE : MANUAL
TASK : NONE
AWAITING : TASK_SPEC
```

---

### Manual Step 2 — Activate the Task and Run Planner

Return to the manual orchestrator chat and paste:

```text
Activate the task defined in .agents/task.toml.

Perform the normal HaruQuantAI TASK_ACTIVATED transition.

Create the deterministic task branch and materialize the complete initial Planner prompt into:

.agents/task/next-agent.md

Because this is MANUAL mode, do not invoke Planner yourself.

Validate the artifact and then instruct me to open a fresh Planner chat and paste the exact contents of .agents/task/next-agent.md unchanged.
```

**Expected transport instruction:**

```text
ORCHESTRATOR : READY_FOR_TRANSPORT
TARGET_ROLE : PLANNER
HANDOFF : TASK_ACTIVATED
PROMPT : .agents/task/next-agent.md
ACTION : OPEN_FRESH_PLANNER_CHAT
```

1. Open a **new, separate Planner chat**.
2. Paste the **entire exact contents** of `.agents/task/next-agent.md` (paste nothing before or after it).
3. Let Planner execute and produce `.agents/task/planner.md` and the updated `.agents/task/next-agent.md`.
4. After Planner stops, return to the **orchestrator chat** and paste:

```text
Planner invocation has finished.

Validate the latest Planner journal and .agents/task/next-agent.md and route the workflow according to .agents/protocol.toml.
```

---

### Manual Step 3 — Owner Execution Decision

Inspect the dry-run plan in `.agents/task/planner.md`.

#### Option 3A: Approve Execution in Manual Mode

When the dry run is satisfactory, approve implementation in the manual orchestrator chat with:

```text
APPROVED: EXECUTE
```

The orchestrator appends the approval record to `planner.md`, validates the Executor prompt in `next-agent.md`, and yields:

```text
ORCHESTRATOR : READY_FOR_TRANSPORT
TARGET_ROLE : EXECUTOR
HANDOFF : PENDING_APPROVAL
PROMPT : .agents/task/next-agent.md
ACTION : OPEN_FRESH_EXECUTOR_CHAT
```

#### Option 3B: Reject the Dry Run in Manual Mode

If the plan requires corrections, paste into the orchestrator chat:

```text
REJECTED: EXECUTE

Owner direction:
<describe exactly what must change in the dry run>
```

The orchestrator instantiates a fresh Planner correction prompt and instructs transport back to a fresh Planner chat.

---

### Manual Step 4 — Handle Planner Blockers in Manual Mode

If Planner reports `BLOCKED`, orchestration halts until the documented external cause is resolved.

After resolving the external cause, paste into the manual orchestrator chat:

```text
RESOLVED: PLANNER BLOCKER

Resolution evidence:
<what changed and where the Planner can verify it>
```

The orchestrator validates the resolution, replaces the stale pending artifact with a fresh canonical `ORCHESTRATOR / BLOCKER_RESOLVED → PLANNER` prompt fingerprinted against the resolved repository state, and instructs transport to resume Planner in a fresh chat.

---

### Manual Step 5 — Run Executor and Transition to Reviewer

After `APPROVED: EXECUTE`, transport the Executor prompt to a fresh chat:

1. Open a **new, separate Executor chat**.
2. Paste the **entire exact contents** of `.agents/task/next-agent.md`.
3. Let Executor execute, implement approved changes, and write `.agents/task/executor.md`.
4. After Executor stops, return to the **orchestrator chat** and paste:

```text
Executor invocation has finished.

Validate the latest Executor journal and .agents/task/next-agent.md and route the workflow according to .agents/protocol.toml.
```

The orchestrator validates the Executor journal and yields the next transport instruction:

```text
ORCHESTRATOR : READY_FOR_TRANSPORT
TARGET_ROLE : REVIEWER
HANDOFF : READY_FOR_REVIEW
PROMPT : .agents/task/next-agent.md
ACTION : OPEN_FRESH_REVIEWER_CHAT
```

*(If you wish to intervene and request adjustments before review, instead send `REJECTED: EXECUTE` with owner direction).*

---

### Manual Step 6 — Run Reviewer Verification and Findings

1. Open a **new, separate Reviewer chat**.
2. Paste the **entire exact contents** of `.agents/task/next-agent.md`.
3. Reviewer executes its 3-stage verification:
   - **Stage A (Code Inspection):** Inspects actual code changes (`git diff`), files, and architecture rules before reading journals.
   - **Stage B (Independent Verification):** Runs affected tests, type checks, and linters independently.
   - **Stage C (Reconciliation):** Reconciles the approved dry-run plan (`planner.md`) against the execution report (`executor.md`) and against the actual code, verifying cryptographic hashes.
4. Reviewer writes its findings to `.agents/task/reviewer.md`.
5. After Reviewer stops, return to the **orchestrator chat** and paste:

```text
Reviewer invocation has finished.

Validate the latest Reviewer journal and .agents/task/next-agent.md and route the workflow according to .agents/protocol.toml.
```

- If Reviewer returns `CHANGES_REQUESTED`, the orchestrator instructs transport back to a fresh Planner chat.
- If Reviewer returns `PENDING_COMMIT`, the orchestrator awaits the owner commit decision.

---

### Manual Step 7 — Owner Commit Decision in Manual Mode

Inspect `reviewer.md` and `git diff`.

#### Option 3C: Approve Commit and Close-Out in Manual Mode

When Reviewer reaches `PENDING_COMMIT` and the work is verified, approve close-out in the orchestrator chat with:

```text
APPROVED: COMMIT
```

The orchestrator validates the reviewed state, materializes the canonical close-out prompt into `.agents/task/next-agent.md`, and yields:

```text
ORCHESTRATOR : READY_FOR_TRANSPORT
TARGET_ROLE : REVIEWER
HANDOFF : PENDING_COMMIT
PROMPT : .agents/task/next-agent.md
ACTION : OPEN_FRESH_REVIEWER_CLOSEOUT_CHAT
```

#### Option 3D: Reject Commit Authorization in Manual Mode

If the work must not be committed or requires further changes:

```text
REJECTED: COMMIT

Owner direction:
<describe why the reviewed state must not be committed and what must change>
```

The orchestrator invalidates the close-out authorization and instantiates a fresh Planner correction prompt.

---

### Manual Step 8 — Run Reviewer Close-Out and Acceptance

1. Open a **new, separate Reviewer close-out chat**.
2. Paste the **entire exact contents** of `.agents/task/next-agent.md`.
3. Let Reviewer perform the safe close-out transaction: re-verify authorization and reviewed state; confirm the immutable archive; run final gates; stage only approved implementation paths; create exactly one task commit; only after commit success clear all four coordination files; verify the task branch is clean and `main` still equals baseline; switch to `main`; fast-forward merge; verify one-commit lineage and committed-path authority; safely delete the task branch; verify the zero-byte task workspace; and mark `ACCEPTED`.
4. After close-out finishes, return to the **orchestrator chat** and paste:

```text
Reviewer close-out has finished.

Validate terminal workflow state and confirm whether the task is ACCEPTED and the orchestrator has returned to READY.
```

**Expected terminal state:**

```text
ORCHESTRATOR : READY
LAST_TASK : ACCEPTED
TASK : NONE
AWAITING : TASK_SPEC
```

All four active-task workspace files (`.agents/task/*.md`) must be 0 bytes.

---

## Part 4 — Maintenance and Diagnostics

Run these commands to verify repository protocol compliance and validate workflow execution:

### Protocol and Workspace Health Check

Validates protocol definitions, prompt templates, CLI configurations, and active task files:

```bash
uv run .agents/orchestrator.py doctor
```

### Protocol End-to-End Self-Test

Executes a complete simulated workflow run (including task activation, Planner dry runs, approval gates, Executor reports, Reviewer verification, rejection loops, and close-out) in an isolated temporary Git repository:

```bash
uv run .agents/orchestrator.py self-test
```

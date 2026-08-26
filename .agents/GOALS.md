# Goal Orchestration

A HaruQuantAI **Goal** is a deterministic supervisory objective that executes multiple ordinary Task workflows in sequence. It is not a reasoning role and does not replace the existing Planner → Executor → Reviewer Task workflow.

## Architecture

```text
                         ORCHESTRATOR
                              │
                  ┌───────────┴───────────┐
                  │                       │
             GOAL ENGINE             TASK ENGINE
           supervisory state            existing
                  │                       │
                  │              ┌────────┼────────┐
                  │              ▼        ▼        ▼
                  │           Planner  Executor  Reviewer
                  │              │        │        │
                  │              └────────┴────────┘
                  │                       │
                  │                    ACCEPTED
                  │                       │
                  └───────────────────────┘
                         next child Task
```

The Goal Engine owns only selection, ordering, child-run identity, progress, checkpointing and terminal Goal state. The Task Engine continues to own task branches, task journals, owner gates, role-session continuity, review, the one Task commit, ff-only merge and task cleanup.

## Goal versus Task

- **Goal:** multiple independently reviewable/committable Tasks.
- **Task:** one coherent planning/implementation/review/commit unit.
- **Planner phase/task:** an implementation subdivision inside one Task dry run.

A Goal never creates a Goal branch or Goal commit. Each accepted child Task contributes its own focused commit to `main`.

## Goal specification

Runtime input is `.agents/goal.toml` (gitignored). Start from `.agents/goal.example.toml` or generate it with `.agents/make_goal.py`.

Supported v1 selectors:

```toml
selection_type = "entries"
entries = ["7.1", "7.2", "7.3"]
```

```toml
selection_type = "phase"
selection = "7"
```

```toml
selection_type = "all_open"
```

At activation the selected child list is resolved from the implementation tracker, completed entries are optionally removed, and the resulting ordered list is **frozen**. Later tracker edits never silently add child Tasks to the active Goal.

## Goal runtime state

Goal checkpoints live under:

```text
.agents/goals/<goal-run-id>/state.json
.agents/goals/<goal-run-id>/children/<entry>.toml
```

The state records resolved/completed/remaining entries, the one active child, child Task run IDs, child baselines/accepted commits and progress history. It stores **no Planner/Executor/Reviewer session IDs**.

## Child lifecycle

Only one child may be active:

```text
Goal
  → child 7.1 ordinary Task workflow
  → ACCEPTED
  → reconcile clean main + zero-byte task workspace + tracker completion
  → child 7.2 ordinary Task workflow
  → ACCEPTED
  → ...
  → GOAL ACCEPTED
```

Task correction loops stay inside the current child. Executor `BLOCKED`, Reviewer `CHANGES_REQUESTED`, owner rejection and later Dry Run/Report/Review iterations do not advance Goal progress. Planner external `BLOCKED` pauses the active child and therefore pauses Goal progress until the existing child is resumed.

A child cancellation, maximum-iteration terminal state, tracker/branch reconciliation failure, or inability to prepare the frozen next child blocks the Goal. Already accepted child commits remain on `main`; Goal supervision never rolls them back automatically.

## Session boundaries

Role-session continuity is bounded to one child Task run:

```text
Child 7.1: Planner P1 / Executor E1 / Reviewer R1
Child 7.2: Planner P2 / Executor E2 / Reviewer R2

P1 != P2
E1 != E2
R1 != R2
```

Within Child 7.1, later Planner/Executor/Reviewer iterations resume P1/E1/R1 as usual. Child 7.2 starts a new Task run and therefore new role conversations.

## Owner gates

Goals add **no authorization token**. The only owner gates remain:

```text
APPROVED: EXECUTE
APPROVED: COMMIT
```

They always apply to the currently active child Task. `CONTINUE: GOAL` is an optional chat transport/resume phrase only; it may advance an already-valid Goal after a child has reached `ACCEPTED`, and grants no authority.

## CLI

Generate a Goal:

```bash
uv run .agents/make_goal.py --entries 7.1 7.2 7.3
uv run .agents/make_goal.py --phase 7
uv run .agents/make_goal.py --all-open
```

Run it in multi-delegate mode:

```bash
uv run .agents/orchestrator.py goal-start --goal-file .agents/goal.toml
uv run .agents/orchestrator.py goal-status
uv run .agents/orchestrator.py goal-resume
```

Relay the active child gates through Goal resume when execution is paused/headless:

```bash
uv run .agents/orchestrator.py goal-resume --approved
uv run .agents/orchestrator.py goal-resume --approved-commit
uv run .agents/orchestrator.py goal-resume --reject-feedback "..."
uv run .agents/orchestrator.py goal-resume --reject-commit-feedback "..."
uv run .agents/orchestrator.py goal-resume --resolve-planner-blocker "..."
```

Cancel Goal supervision without destroying active child evidence:

```bash
uv run .agents/orchestrator.py goal-cancel --reason "..."
```

## Mode symmetry

- **Solo:** one physical chat; each child is a new logical Task run and reloads the complete initial Planner contract. Cross-role isolation remains soft.
- **Delegate:** each child gets a fresh Planner/Executor/Reviewer delegate set; same-role handle continuity applies only inside that child.
- **Multi-delegate:** each child gets a fresh Task run ID and therefore a fresh native P/E/R session ledger automatically.
- **Manual:** keep the same Goal Orchestrator chat, but open a new dedicated Planner/Executor/Reviewer chat set for each child. Reuse those three chats only for iterations of that child.

Modes change transport only; Goal and Task semantics remain identical.

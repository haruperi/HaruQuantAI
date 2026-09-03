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

The Goal Engine owns only selection, ordering, child-run identity, progress, checkpointing and terminal Goal state. The Task Engine continues to own task branches, task journals, owner gates, role-session continuity, review, the one Task implementation commit, explicit no-fast-forward merge commit and task cleanup.

## Goal versus Task

- **Goal:** multiple independently reviewable/committable Tasks.
- **Task:** one coherent planning/implementation/review/commit unit.
- **Planner phase/task:** an implementation subdivision inside one Task dry run.

A Goal never creates a Goal branch or Goal commit. Each accepted child Task contributes its own focused implementation commit plus an explicit merge commit to `main`, preserving the child branch topology in history.

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

`stop_on_blocked=false` is supported only with schema-v3 `approval_policy="unattended"` in any transport mode. It does not skip blocked children. Instead, the same child Planner receives one bounded retry directive to resolve non-critical ambiguity through explicit, reversible, repository-grounded assumptions. Owner authorization, credentials, external facts, live-action safety, destructive authority, security policy, acceptance evidence and scope expansion can never be assumed; those blockers still pause the Goal.

### Common child context

An optional non-blank `child_additional_context` string carries common coordination instructions into every independent child Task:

```toml
child_additional_context = "Read docs/dev/UI_MIGRATION_PLAN.md; use the matching donor row; update its status with evidence."
```

The value is frozen in Goal runtime state at activation. For each child, the Goal Engine appends it under a stable `Goal-level child context:` label to the tracker-generated Task `additional_context`; it never replaces the tracker context or changes owning documentation authority. In particular, child context may require use of an available normalized donor bundle but must not elevate donor material to authority or make its absence alone a blocker. When a declared bundle is absent, the child implements the complete ratified V3 scope from scratch, does not substitute raw staging or claim donor parity, and records that evidence limitation in the legacy ledger. The combined value is written identically to the archived child specification and `.agents/task.toml`, so each fresh Planner receives it through the normal Task prompt. Omitting the field preserves existing behavior. Blank or non-string supplied values fail closed.

## Goal runtime state

Goal checkpoints live under:

```text
.agents/goals/<goal-run-id>/state.json
.agents/goals/<goal-run-id>/children/<entry>.toml
```

The state records resolved/completed/remaining entries, the one active child, child Task run IDs, child baselines/accepted commits and progress history. It stores **no Planner/Executor/Reviewer session IDs**.

For `stop_on_blocked=false`, state also records `assumption_reviews` for every accepted child and an `assumption_ledger` containing the accepted Reviewer sections that used assumptions. Each record includes the entry, child run ID, archived Reviewer path, exact section and SHA-256 for later human review. Missing Reviewer assumption evidence blocks acceptance reconciliation.

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

Task correction loops stay inside the current child. Executor `BLOCKED`, Reviewer `CHANGES_REQUESTED`, owner rejection and later Dry Run/Report/Review iterations do not advance Goal progress. Planner `BLOCKED` receives at most one automatic assumption retry when the frozen unattended Goal permits it; a repeated or protected/external blocker pauses the active child until the existing child is resumed.

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

Within Child 7.1, later Planner/Executor/Reviewer iterations resume P1/E1/R1 as usual. Child 7.2 starts a new Task run and therefore new role conversations. In `solo`, every child also owns a separate physical IDE chat; all roles for that child remain together in that one chat.

## Child Task gates

Goals add **no authorization token**. The only gate labels remain:

```text
APPROVED: EXECUTE
APPROVED: COMMIT
```

They always apply to the currently active child Task. Interactive runs require the exact owner messages; unattended runs use the frozen Goal/child runtime policy and explicit local permissions. `CONTINUE: GOAL` is an optional chat transport/resume phrase only; it may advance an already-valid Goal after a child has reached `ACCEPTED`, and grants no authority.

## CLI

Generate a Goal:

```bash
uv run .agents/make_goal.py --entries 7.1 7.2 7.3
uv run .agents/make_goal.py --phase 7
uv run .agents/make_goal.py --all-open
uv run .agents/make_goal.py --all-open --continue-on-blocked
```

For a Goal whose children share a coordination plan:

```bash
uv run .agents/make_goal.py \
  --entries 1.8 1.9 1.10 \
  --file tracker.md \
  --listed-order \
  --child-additional-context "Read docs/dev/UI_MIGRATION_PLAN.md; follow sections 6-8 and update the matching section 6 row and section 9 checkbox with evidence."
```

Start, inspect, and resume a Goal in any mode:

```bash
uv run .agents/orchestrator.py goal-start --goal-file .agents/goal.toml
uv run .agents/orchestrator.py goal-status
uv run .agents/orchestrator.py goal-resume
```

After an accepted non-final child in `solo`, the controller stops at a persisted boundary such as:

```text
NEXT_CHILD_CHAT : REQUIRED
PRIMARY_NEW_CHAT_ACTION : /new
AUTOMATIC_FALLBACK : app-native create_thread
NEXT_CHAT_PROMPT : Continue HaruQuantAI Goal ...
RESUME_COMMAND : uv run .agents/orchestrator.py goal-resume --goal-run-id ... --claim-child-chat ...
```

The preferred desktop route is `/new`, followed by the emitted `NEXT_CHAT_PROMPT`. If direct slash-command execution is unavailable, the current IDE agent must create an app-native task in the same saved project with that exact prompt. The Goal checkpoint is written before either transition. A missing, stale, or mismatched `--claim-child-chat` fails closed, so retrying with the other transport cannot duplicate or skip a child.

Headless modes (`solo-headless`, `delegate-headless`, and `delegate-multi`) invoke role CLI sessions automatically. IDE-native modes pause each child at `[ROLE_READY]`; after this chat performs the `solo` role or receives the `delegate` role agent's result, resume with:

```bash
uv run .agents/orchestrator.py goal-resume --role-complete
uv run .agents/orchestrator.py goal-resume --role-complete --app-agent-id <opaque-id>
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

- **Solo:** one fresh IDE chat per child performs Controller + Planner + Executor + Reviewer sequentially. `/new` is preferred and app-native task creation is the fallback; persisted Goal state and a handoff claim connect the child chats. Cross-role isolation inside each child remains soft.
- **Solo-headless:** each child gets one fresh shared native CLI session.
- **Delegate:** each child gets a fresh inspectable app-native Planner/Executor/Reviewer agent set; same-role handle continuity applies only inside that child.
- **Delegate-headless:** each child gets a fresh same-vendor native P/E/R session set.
- **Delegate-multi:** each child gets a fresh Task run ID and therefore a fresh independently configured native P/E/R session ledger automatically.
- **Manual:** keep the same Goal Orchestrator chat, but open a new dedicated Planner/Executor/Reviewer chat set for each child. Reuse those three chats only for iterations of that child.

Modes change transport only; Goal and Task semantics remain identical.

The schema-v3 runtime-policy and frozen Goal scope fingerprints are recorded at activation and checked before progress. Unattended headless children may receive one fresh `codex/gpt-5.6-sol/high` recovery generation for exactly one additional correction iteration. If that generation fails, the child reaches `MAX_ITERATIONS` and the Goal blocks; the next independently started Goal/Task always begins with its configured normal identities.

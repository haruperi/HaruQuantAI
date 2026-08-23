# ROLE: PLANNER

Replace every double-braced field below before submitting this prompt. Parenthetical `e.g.` values are illustrative.
If any unresolved placeholder remains, stop and request the missing value instead of creating a branch, worktree,
or dry run.

Main repository path : `C:\Users\rharu\AppDev\HaruQuantAI\`
Task kind : `feature`
Task or feature ID : `FEAT-DATA-INGEST_HISTORY`
Filesystem-safe lowercase task slug : `historical-data-ingestion`
Task name : `Historical Data Ingestion`
Task request : `Implement historical-data ingestion through its registered Data capability and expose the
workflow in the UI.`
Additional context : `Reuse the existing Data contracts and Composition lifecycle.`
Explicit exclusions : `No live broker calls or unrelated Data features.`

Act only as the Planner defined by `AGENTS.md`.

1. Work from the supplied main repository initially. Read `AGENTS.md`, then use the PROJECT and ARCHITECTURE
   context routers and applicable owning READMEs.
2. Verify main is clean and checked out on `main`; `docs/dev/task/planner.md`, `docs/dev/task/executor.md`, and
   `docs/dev/task/reviewer.md` are zero bytes; no task worktree is active; and the proposed task branch and
   worktree do not already exist.
3. Derive and validate the branch and sibling worktree using the naming, path-resolution, and safety rules in
   `AGENTS.md`. Create exactly one task branch/worktree, then perform all remaining planning inside that worktree.
4. Inspect the repository and relevant upstream evidence. Identify requirements, gaps, boundaries, dependencies,
   affected authoritative documentation, tests, usage evidence, risks, validation, and rollback without modifying
   implementation or authoritative files.
5. Append the next numbered, complete eight-part dry run to the task worktree's `docs/dev/task/planner.md`.
   Record the task ID, main path and baseline commit, task branch, task worktree path, expected
   changed/untracked paths, and all required metadata.
6. Do not implement, commit, merge, push, or write any file other than the authorized Planner journal and the
   one-time branch/worktree bootstrap.
7. Return a concise handoff containing the task ID, branch, worktree path, dry-run number, blockers, and
   approval status. Wait for a standalone owner message whose entire trimmed content is exactly
   `APPROVED: EXECUTE`.
8. After valid approval, append the required approval record to `docs/dev/task/planner.md`, verify the approved
   dry-run body remains unchanged, and stop for the Executor handoff.

If any entry gate fails, do not create an invalid workflow state. Report the exact evidence and required owner action.

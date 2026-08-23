# ROLE: REVIEWER

Main repository path : `C:\Users\rharu\AppDev\HaruQuantAI\`
Task worktree path : `C:\Users\rharu\AppDev\HaruQuantAI-worktrees\historical-data-ingestion`
Expected task branch : `feature/feat-data-ingest-history-historical-data-ingestion`
Task ID : `FEAT-DATA-INGEST_HISTORY`
Dry-run number to review : `1`
Executor report number to review : `1`

Additional review focus : `Pay particular attention to physical removability and UI contract parity.`

Act only as the Reviewer defined by `AGENTS.md`.

1. Begin inside the supplied task worktree. Read `AGENTS.md` and the complete histories in
   `docs/dev/task/planner.md`, `docs/dev/task/executor.md`, and `docs/dev/task/reviewer.md`.
2. Verify the task ID, worktree root, task branch, main path and baseline, approved dry-run record, Executor
   report, `HEAD`, staged and unstaged changes, untracked files, and expected path inventory.
3. Independently inspect the complete branch diff from the recorded main baseline and the resulting repository. Do
   not treat the Executor report as proof.
4. Verify exact plan compliance, requirements, file-line evidence, documentation authority and consistency,
   contracts, dependency and domain boundaries, security, failure behavior, rollback, tests, and executable
   usage evidence.
5. Independently rerun the applicable affected tests and non-mutating quality checks. Follow the Reviewer
   verification and final commit-gate policy in `AGENTS.md`.
6. Never repair code, tests, configuration, documentation, or workflow state during review.
7. Append the next numbered review to `docs/dev/task/reviewer.md`, referencing the reviewed dry run and Executor
   report and recording evidence, deviations, omissions, defects, risks, commands, results, required corrections,
   and commit decision.
8. If any issue exists, mark the review `CHANGES_REQUESTED`, leave the task branch/worktree intact, do not commit
   or merge, and hand control to the Planner.
9. Only if every applicable requirement and gate passes, mark the review `ACCEPTED` and perform the approved
   close-out exactly as defined in `AGENTS.md`: empty all three journals, create the task commit, verify clean
   unchanged main, merge with `git merge --ff-only`, verify the merged commit, safely remove the clean merged
   worktree, and delete the merged branch with `git branch -d`.

Never push, force-remove a worktree, force-delete a branch, resolve merge conflicts, rebase, reset, clean, amend,
or expand the approved scope. If any close-out precondition fails, preserve the task branch/worktree, reconstruct a
`CHANGES_REQUESTED` review when required, and return control to the Planner.

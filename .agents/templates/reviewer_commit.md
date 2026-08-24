# ROLE: REVIEWER — authorized close-out

Main repository path : `{{repo_path}}`
Task branch : `{{branch}}`
Task ID : `{{task_id}}`
Review number : `{{iteration}}`
Main baseline commit : `{{baseline_commit}}`

Act only as the Reviewer defined by `AGENTS.md`, operating inside the task branch above.

The owner has issued the standalone commit authorization:

APPROVED: COMMIT

1. Read `AGENTS.md` and the journal histories in `docs/dev/task/`. Verify `Review {{iteration}}` concluded
   with `PENDING_COMMIT` and every applicable gate passed.
2. Append the commit authorization record to `docs/dev/task/reviewer.md`: the exact phrase
   `APPROVED: COMMIT`, the review number, task ID, and the reviewed HEAD you are committing.
3. Perform the close-out exactly as `AGENTS.md` defines: empty all three journals (`planner.md`,
   `executor.md`, `reviewer.md`), verify they match their empty state at the main baseline, stage only the
   approved changes, create the one authorized local task commit (pre-commit coverage gate included),
   verify clean unchanged main, merge with `git merge --ff-only`, verify the merged commit, and delete the
   merged branch with `git branch -d`.
4. If any close-out precondition fails, force nothing: leave the task branch and working tree intact,
   record the exact failure, and end with `ACTIVATING : PLANNER` and `HANDOFF : CHANGES_REQUESTED`
   (reconstructed) instead.

## Orchestrator handoff contract (mandatory)

Because the close-out empties the journals, the final handoff block lives in your final answer: print
exactly these three lines as the last lines of your reply (and, if any file still exists to receive it,
append them there too):

STOPPED : REVIEWER
ACTIVATING : NONE
HANDOFF : ACCEPTED

On close-out failure use `ACTIVATING : PLANNER` and `HANDOFF : CHANGES_REQUESTED` instead, and print the
same three lines.

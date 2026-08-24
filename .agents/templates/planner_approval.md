# ROLE: PLANNER — approval recording

Main repository path : `{{repo_path}}`
Task branch : `{{branch}}`
Task ID : `{{task_id}}`
Approved dry-run number : `{{iteration}}`
Main baseline commit : `{{baseline_commit}}`
Handoff notes : {{handoff_notes}}

Act only as the Planner defined by `AGENTS.md`, operating inside the task branch above.

The owner has issued the standalone approval message:

APPROVED: EXECUTE

1. Read `AGENTS.md` and `docs/dev/task/planner.md`. Verify `Dry Run {{iteration}}` is present and unchanged.
2. Append the required approval record to `docs/dev/task/planner.md`: the exact phrase `APPROVED: EXECUTE`,
   the approved dry-run number, task ID, main baseline commit, task branch, and the expected working-tree state,
   exactly as `AGENTS.md` requires.
3. Do not implement anything and do not modify the approved dry-run body.

## Orchestrator handoff contract (mandatory)

End your new journal entry with exactly these three final lines:

STOPPED : PLANNER
ACTIVATING : EXECUTOR
HANDOFF : APPROVED_EXECUTE

If the record could not be appended validly, use `ACTIVATING : NONE` and `HANDOFF : BLOCKED` instead, with the
exact evidence recorded. Also print the same three lines at the end of your final answer. Immediately above
the three lines, write a `NEXT AGENT NOTES :` section of one to five lines of targeted context for the
Executor; write `NEXT AGENT NOTES : None` if nothing applies.

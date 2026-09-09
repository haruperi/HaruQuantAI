# DETERMINISTIC CLOSE-OUT REQUEST

This artifact defines the complete **controller close-out contract**. It is not
a reasoning-role prompt and must never launch or resume Planner, Executor or
Reviewer.

The independent Reviewer has completed its decision and handed the unchanged
candidate to the deterministic controller with `HANDOFF : PENDING_COMMIT`.
The exact owner gate remains `APPROVED: COMMIT`.

## Frozen identity

Run ID: `{{run_id}}`
Task ID: `{{task_id}}`
Review number: `{{iteration}}`
Task branch: `{{branch}}`
Accepted-main baseline: `{{baseline_commit}}`
Reviewed HEAD: `{{reviewed_head}}`
Reviewed worktree: `{{reviewed_worktree_hash}}`
Approval authority: `{{approved_authority_hash}}`

## Controller procedure

After exact commit authorization, the controller verifies the unchanged
candidate and controller-produced validation receipt. It archives journals,
stages only approved implementation paths, creates exactly one Task commit,
clears the four coordination files, verifies a clean Task branch, performs the
explicit no-fast-forward merge on unchanged accepted `main`, verifies parents,
trees and path authority, safely deletes the merged Task branch, and writes a
non-self-referential final receipt.

The controller does not repeat already receipted validation, interpret a
requirement, repair implementation, alter security policy, invent approval,
resolve a semantic conflict, rebase, reset, amend, force-delete or push.
Any byte, authority, receipt or Git precondition mismatch stops close-out and
preserves recoverable evidence.

Expected Reviewer handoff:

```text
STOPPED : REVIEWER
ACTIVATING : CONTROLLER
HANDOFF : PENDING_COMMIT
```

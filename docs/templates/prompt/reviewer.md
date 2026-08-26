# PROMPT

## 1. Role

Act as the HaruQuantAI **Reviewer** defined by `AGENTS.md`. You independently verify; you never repair implementation.

## 2. Context

Run ID: `{{run_id}}`
Repository: `{{repo_path}}`
Expected task branch: `{{branch}}`
Task ID: `{{task_id}}`
Dry-run/report number: `{{iteration}}`
Original task request: `{{task_request}}`
Main baseline commit: `{{baseline_commit}}`
Approved plan hash: `{{approved_plan_hash}}`
Executor report hash: `{{executor_report_hash}}`
Additional review focus: `{{review_focus}}`
Blocker ledger: {{blocker_ledger}}

## 3. Instruction / Task

Perform an anti-anchored independent review in three stages.

**Stage A — Independent reconstruction & code inspection:** before reading Planner/Executor journals, read the original task, `AGENTS.md`, applicable authoritative specifications, baseline, complete branch diff, staged/unstaged changes, untracked paths, and the actual implementation files in the repository. Inspect the code directly and derive independently what should exist and what evidence should prove it.

**Stage B — Independent verification:** run applicable affected tests and non-mutating quality/architecture/usage checks (including type-checking, linter checks, and test suites). Do not treat upstream claims or execution logs as evidence.

**Stage C — Dry-run, report, and code reconciliation:** only now read `.agents/task/planner.md` (the approved dry run) and `.agents/task/executor.md` (the execution report), including its `UPSTREAM CLAIMS — UNTRUSTED UNTIL INDEPENDENTLY VERIFIED` section. Verify the approval-chain hash from the exact pre-owner-gate Planner bytes and verify the Executor journal hash. Reconcile both journals against independently observed code and test evidence.

Append `Review {{iteration}}` to `.agents/task/reviewer.md`.

If any issue exists, write a complete Planner correction prompt for iteration **{{iteration}} + 1** to `.agents/task/next-agent.md`.
If every applicable gate passes, write a complete Reviewer close-out prompt for the current iteration to `.agents/task/next-agent.md` using `docs/templates/prompt/reviewer-closeout.md`; do not commit yet.

## 4. Specification

For `CHANGES_REQUESTED`, next-agent metadata uses the next iteration (`{{iteration}} + 1`), `source_role="REVIEWER"`, `target_role="PLANNER"`, `handoff="CHANGES_REQUESTED"`, `template_path="docs/templates/prompt/planner.md"`, and no owner gate. Structured facts must identify each failed requirement/gate, independent evidence, required correction, valid retained work, and scope needing reconsideration.

For successful verification, metadata keeps iteration `{{iteration}}`, uses `source_role="REVIEWER"`, `target_role="REVIEWER"`, `handoff="PENDING_COMMIT"`, `template_path="docs/templates/prompt/reviewer-closeout.md"`, `requires_owner_gate=true`, `owner_gate="APPROVED: COMMIT"`.

## 5. Authority and Boundaries

Allowed writes:

- `.agents/task/reviewer.md`;
- `.agents/task/next-agent.md`.

Forbidden:

- implementation, tests, configuration, product documentation, Planner/Executor journals;
- commit/merge/branch cleanup before owner commit authorization;
- relying on Executor/Planner claims as proof.

Self-correct errors in the review itself. Never self-correct the implementation; implementation defects produce `CHANGES_REQUESTED`.
Preserve the canonical authority of any prompt you instantiate.

## 6. Reasoning Guidance

Reconstruct from evidence before consuming upstream narrative. Do not output private chain-of-thought; record findings, commands, results, risks, and requirement-level evidence.

## 7. Performance / Quality Criteria

Reject acceptance if evidence is incomplete, journal hashes disagree with the approved chain of custody, tests fail, scope drift exists, authority is violated, original task remains incomplete, or reviewed state cannot be reproduced independently.

## 8. Output Format

Append the review and replace `.agents/task/next-agent.md` with the complete target-role prompt.

Changes required:

```text
STOPPED : REVIEWER
ACTIVATING : PLANNER
HANDOFF : CHANGES_REQUESTED
```

Verification passed:

```text
STOPPED : REVIEWER
ACTIVATING : REVIEWER
HANDOFF : PENDING_COMMIT
```

## 9. Examples

Not Applicable.

## 10. Final Quality Check

Verify that Stage A/B occurred before Stage C, upstream claims and journal hashes were independently checked, all applicable requirements/gates were covered, and next-agent metadata/iteration/authority are correct.

# SQX implementation prompts

Copy the relevant prompt and substitute its placeholder.

- Single feature: replace `{FEATURE_ID}`, for example `FEAT-HOST-COMMONS-LOGGING`.
- Whole phase: replace `{PHASE_PLAN_PATH}`, for example `docs/dev/phases/phase-01-host-foundation.md`.
- Both prompts follow [AGENTS.md](../../AGENTS.md) and [PYTHON_MODULE.md](../templates/PYTHON_MODULE.md).
- Track progress in [implementation_checklist.md](phases/implementation_checklist.md); update it after every verified task.

## Prompt 1 — Implement one feature

```text
Implement {FEATURE_ID} using its task in docs/dev/phases/.

- Read AGENTS.md, docs/templates/PYTHON_MODULE.md, the owning domain README, and the relevant roadmap/task before doing any work.
- Read docs/dev/phases/implementation_checklist.md and locate the matching feature row before planning.
- Follow the required research → documented plan → owner approval → implementation → verification → walkthrough workflow. Approval applies only to the presented plan and exact ALLOWED_WRITE_PATHS.
- Resolve SQX_REFERENCE_ROOT from the session/local configuration; HARUQUANTAI_ROOT is the current repository. Save only logical-root or repository-relative paths.

Donor investigation:
- Locate the feature’s exact donor JARs and verify their SHA-256 fingerprints.
- Inspect readable/decompiled implementation text or bytecode, not merely class names, signatures, documentation, or roadmap FR seeds.
- Trace the required classes, methods, dependencies, callers, configuration and resources until the feature’s actual implementation is understood.
- Record exact algorithms, formulas, operation order, defaults, types, units, rounding, state transitions, side effects and failure behavior.
- Distinguish observed behavior, inference, unresolved gaps and target decisions. Never guess missing donor logic.

Translation:
- Produce a faithful, behavior-preserving Python translation of the inspected implementation.
- Preserve donor class/function responsibilities and execution order wherever Python permits.
- Change only what is necessary for Python syntax, runtime primitives and approved HaruQuantAI interfaces.
- Do not redesign, optimize, simplify, substitute algorithms, invent defaults, introduce dependencies or omit behavior without an approved deviation.
- Use documentation to clarify donor behavior; do not let generic documentation replace inspected implementation.
- If donor behavior conflicts with repository authority or the approved specification, document the conflict and obtain a decision before implementing the affected behavior.
- Do not paste proprietary Java/decompiled source into repository documentation or evidence.

Implementation and evidence:
- Map every implemented class/function to the owning FEAT/FR and applicable decision IDs. Registration changes require approved scope.
- Follow the canonical Python module docstring, typing, formatting and explicit FR logging requirements; verify log emissions.
- Follow the complete evidence-ledger procedure, including reading both ledger/schema, atomic claims, unique IDs, exact source locations, fingerprints, limitations and validation observations. Missing authority is a gap to resolve, not permission to fabricate it.
- Use isolated test stores. Preserve shared databases, junctions and unrelated working-tree changes.

Completion:
Checklist tracking (mandatory after every completed task):
- Include docs/dev/phases/implementation_checklist.md in the plan's exact ALLOWED_WRITE_PATHS for progress updates.
- When an approved task starts, set Current Task to its numbered checklist row and feature/task name.
- Immediately after each task's required implementation and verification pass, check its matching row in docs/dev/phases/implementation_checklist.md; do not wait until the end of a phase batch.
- Reconcile completion with the detailed phase steps, owning domain README and walkthrough evidence. Leave partial, blocked, failed or unverified tasks unchecked.
- Recalculate Completed as checked child rows/total child rows; exclude phase-heading checkboxes. Update Progress Bar using round(100 * completed / total, 1)% and a 20-cell bar with floor(20 * completed / total) filled # cells.
- Check a phase heading only when every child task and its phase completion gates pass.
- After completion, set Current Task to the next pending task; if blocked, retain the blocked task and short reason; when everything passes, use None — complete.
- Re-read the checklist before writing; preserve other tasks' existing states, numbering and links. Report the updated completed count, percentage and Current Task in the walkthrough.
- Test donor-derived normal, boundary and failure cases; compare outputs with actual donor observations.
- Run focused pytest with --no-cov during iteration, required lint/type checks, applicable UI checks and prescribed coverage qualification.
- Do not claim parity or mark validation passed without recorded execution evidence.
- Deliver the canonical walkthrough with changes, donor traceability, exact commands/results, deviations, remaining gaps and proposed commit message.
- Do not commit, merge, push or rewrite history without separate owner authorization.
```

## Prompt 2 — Implement a whole phase

```text
Implement every feature task in {PHASE_PLAN_PATH} as one coordinated phase batch.

- Read AGENTS.md, docs/templates/PYTHON_MODULE.md, the phase file, its prerequisite phases, the roadmap and all relevant owning domain READMEs.
- Read docs/dev/phases/implementation_checklist.md and identify every row belonging to the requested phase before planning.
- Follow research → one documented batch plan → owner approval → implementation → verification → walkthrough.
- Define exact ALLOWED_WRITE_PATHS for the complete batch. The phase checklist itself is not execution approval.
- Resolve SQX_REFERENCE_ROOT locally; HARUQUANTAI_ROOT is the current repository. Save only logical-root or repository-relative paths.

Batch investigation:
- Build a complete feature/FR → donor JAR → class/function → Python file → test map.
- Include every phase feature, resource contribution and integration task. Record prerequisite blockers and shared-file ownership.
- Verify donor fingerprints and inspect readable/decompiled implementation text or bytecode for every required class/function.
- Trace cross-JAR calls, dependencies, configuration and resources. Roadmap signatures and FR seeds are starting points, not a complete implementation specification.
- Record algorithms, formulas, execution order, defaults, types, units, rounding, state, side effects and failure behavior.
- Separate observations, inference, unresolved gaps and target decisions. Do not invent missing implementations.

Translation and integration:
- Translate inspected donor behavior faithfully into Python; preserve class/function responsibilities and execution order wherever feasible.
- Make only necessary language/runtime adaptations and approved HaruQuantAI interface changes.
- Do not redesign, optimize, simplify, swap algorithms, invent defaults, add dependencies or silently skip features.
- Resolve specification/repository conflicts through documented decisions before implementing affected behavior.
- Implement in dependency order. Give shared modules one owner; use the approved host capabilities and domain contracts.
- Connect the existing frontend to actual backend behavior. Do not count mocks, placeholders or fabricated results as completed functionality.
- Keep proprietary Java/decompiled source out of repository documentation and evidence.

Project controls:
- Follow canonical module docstrings, FEAT/FR mappings, strict typing, formatting and observable FR logging.
- Apply the complete evidence-ledger procedure and validate ledger/schema, source links, related records and registered IDs when edited.
- Use isolated stores; preserve live databases, junctions and unrelated changes. Do not perform concurrent schema changes or restores.
- Record material scope/contract/dependency deviations as plan iterations and obtain renewed approval where required.

Qualification and delivery:
Checklist tracking (mandatory after every completed task):
- Include docs/dev/phases/implementation_checklist.md in the plan's exact ALLOWED_WRITE_PATHS for progress updates.
- When an approved task starts, set Current Task to its numbered checklist row and feature/task name.
- Immediately after each task's required implementation and verification pass, check its matching row in docs/dev/phases/implementation_checklist.md; do not wait until the end of a phase batch.
- Reconcile completion with the detailed phase steps, owning domain README and walkthrough evidence. Leave partial, blocked, failed or unverified tasks unchecked.
- Recalculate Completed as checked child rows/total child rows; exclude phase-heading checkboxes. Update Progress Bar using round(100 * completed / total, 1)% and a 20-cell bar with floor(20 * completed / total) filled # cells.
- Check a phase heading only when every child task and its phase completion gates pass.
- After completion, set Current Task to the next pending task; if blocked, retain the blocked task and short reason; when everything passes, use None — complete.
- Re-read the checklist before writing; preserve other tasks' existing states, numbering and links. Report the updated completed count, percentage and Current Task in the walkthrough.
- Run focused feature tests during implementation, then cross-feature and real frontend/backend phase tests.
- Verify donor-derived outputs, boundary cases, failures, cancellation, lifecycle cleanup and resource ownership.
- Run required lint/type checks, applicable UI typecheck/test/build and prescribed coverage qualification.
- Reconcile every phase checkbox with actual artifacts and timestamped observations. Keep blocked/unverified items visibly open.
- Produce one canonical phase walkthrough with per-feature outcomes, donor traceability, exact commands/results, deviations, gaps and proposed commit message.
- Do not claim phase completion or SQX parity while accepted requirements remain unverified.
- Do not commit, merge, push or rewrite history without separate owner authorization.
```

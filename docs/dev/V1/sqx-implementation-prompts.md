# SQX145 implementation prompts

Substitute `{FEATURE_ID}` or `{PHASE_PLAN_PATH}`. Both prompts follow [AGENTS.md](../../../AGENTS.md), [PYTHON_MODULE.md](../../templates/PYTHON_MODULE.md) and the [master checklist](implementation_checklist.md).

## Prompt 1 — One feature task

```text
Implement {FEATURE_ID} from its numbered task in docs/dev/V2/.

- Read AGENTS.md, docs/templates/PYTHON_MODULE.md, owning domain READMEs, the current roadmap, task and master checklist before work.
- Use only SQX145 Dev 1 (C:\SQX-145) under explicitly configured SQX_145_REFERENCE_ROOT; HARUQUANTAI_ROOT is this repository. Publish logical paths only. Missing sources are blockers; never substitute another donor.
- Read docs/dev/V1/sqx145-baseline-audit.md and current inventory/ownership/member metadata. Verify exact donor SHA-256 and actual classes/functions before translation.
- Inspect readable/decompiled implementation bodies or bytecode and actual callers. Preserve confirmed formulas, operation order, defaults, state transitions, I/O and failure semantics in independently written Python. Signatures, names and manifest descriptions cannot supply missing logic.
- Enumerate all consumed classes/functions/resources, not merely representative FR seeds. Map each accepted behavior to descriptive FRs; classify JVM-only/unconsumed internals explicitly.
- Include shipped UI/configuration/snippet/template/compiled-helper donors when relevant. Exclude live Q sessions/memory/accounts and generated caches; keep proprietary source text outside repository evidence.
- Follow research → canonical documented plan with exact ALLOWED_WRITE_PATHS → owner approval → implementation → focused verification → walkthrough. Donor informs; the ratified specification owns. Resolve conflicts before coding affected behavior.
- Use canonical Python module sections, typed public APIs, Ruff, strict Mypy and explicit observable FR logs. Use existing approved dependencies/host capabilities; obtain decisions for material contract/dependency changes.
- Connect applicable features to the existing frontend after the backend works: feature-owned clients, commands/projections, loading/empty/denied/failure states, real job/resource IDs, cancellation and reconnect. Mocks cannot qualify completion; preserve prebuilt layouts.
- Use isolated temporary stores; preserve live databases, junctions and unrelated work. No donor startup, schema restore, live provider mutation or trading is implied.
- When ledger edits are approved, read ledger/schema in full, allocate the next SQX145-EV suffix above the high-water mark, record atomic claims/current sources/limits/mappings/review/commit and validate all IDs/hashes/relationships. Passes require actual observations/artifacts/time.

- Scope the canonical plan to this feature and its prerequisite/consumer/UI connections; stop for APPROVED: EXECUTE before implementation.
- After qualification, produce the canonical feature walkthrough with donor traceability, registered FEAT/FR/DEC mappings and proposed commit message.

Mandatory completion tracking:
- Include docs/dev/V2/implementation_checklist.md in exact ALLOWED_WRITE_PATHS. Set Current Task when approved work starts.
- Immediately after EACH task's implementation and required verification pass, check its numbered row; reconcile detailed steps, owning README status and walkthrough evidence. Leave partial/blocked/unverified tasks unchecked.
- Recalculate Completed as checked child tasks / total child tasks; exclude phase-heading rows. Progress = round(100 * completed / total, 1)%; 20-cell bar fills floor(20 * completed / total) cells.
- Check a phase only when all child tasks and phase completion gates pass. Set Current Task to the next pending task, or retain a blocked task with its reason; use None — complete only when all tasks pass.
- Preserve other tasks' states/numbering/links. Report tracker totals, progress and Current Task in the walkthrough.
- Run focused tests with explicit paths and --no-cov during iteration, independent normal/boundary/failure vectors, FR log checks and applicable lifecycle/resource tests. Run prescribed candidate coverage and UI typecheck/test/build plus isolated real-host acceptance when UI is connected.
- Record exact commands/results, timestamped artifacts, deviations and unresolved gaps. Never infer SQX parity from static inventory, code coverage or matching screens.
- Do not commit, merge, push, rebase or rewrite history without separate owner authorization after walkthrough review.
```

## Prompt 2 — Whole phase batch

```text
Implement every feature/task in {PHASE_PLAN_PATH} as one approved phase batch.

- Read AGENTS.md, docs/templates/PYTHON_MODULE.md, owning domain READMEs, the current roadmap, task and master checklist before work.
- Use only SQX145 Dev 1 (C:\SQX-145) under explicitly configured SQX_145_REFERENCE_ROOT; HARUQUANTAI_ROOT is this repository. Publish logical paths only. Missing sources are blockers; never substitute another donor.
- Read docs/dev/V1/sqx145-baseline-audit.md and current inventory/ownership/member metadata. Verify exact donor SHA-256 and actual classes/functions before translation.
- Inspect readable/decompiled implementation bodies or bytecode and actual callers. Preserve confirmed formulas, operation order, defaults, state transitions, I/O and failure semantics in independently written Python. Signatures, names and manifest descriptions cannot supply missing logic.
- Enumerate all consumed classes/functions/resources, not merely representative FR seeds. Map each accepted behavior to descriptive FRs; classify JVM-only/unconsumed internals explicitly.
- Include shipped UI/configuration/snippet/template/compiled-helper donors when relevant. Exclude live Q sessions/memory/accounts and generated caches; keep proprietary source text outside repository evidence.
- Follow research → canonical documented plan with exact ALLOWED_WRITE_PATHS → owner approval → implementation → focused verification → walkthrough. Donor informs; the ratified specification owns. Resolve conflicts before coding affected behavior.
- Use canonical Python module sections, typed public APIs, Ruff, strict Mypy and explicit observable FR logs. Use existing approved dependencies/host capabilities; obtain decisions for material contract/dependency changes.
- Connect applicable features to the existing frontend after the backend works: feature-owned clients, commands/projections, loading/empty/denied/failure states, real job/resource IDs, cancellation and reconnect. Mocks cannot qualify completion; preserve prebuilt layouts.
- Use isolated temporary stores; preserve live databases, junctions and unrelated work. No donor startup, schema restore, live provider mutation or trading is implied.
- When ledger edits are approved, read ledger/schema in full, allocate the next SQX145-EV suffix above the high-water mark, record atomic claims/current sources/limits/mappings/review/commit and validate all IDs/hashes/relationships. Passes require actual observations/artifacts/time.

- Enumerate every numbered phase task and prerequisites; use one canonical phase plan with per-feature FRs, dependency order, shared ownership, exact write paths and independent acceptance. Stop for APPROVED: EXECUTE before implementation.
- Execute in dependency order; do not silently skip blocked features or count placeholders as completion. Keep shared modules under one ratified owner.
- Complete each feature's backend and applicable prebuilt UI connection before checking its row. Update the tracker immediately after each task, not only at the batch end.
- Produce one canonical phase walkthrough with per-feature outcomes, real connected acceptance and explicit remaining blockers.

Mandatory completion tracking:
- Include docs/dev/V2/implementation_checklist.md in exact ALLOWED_WRITE_PATHS. Set Current Task when approved work starts.
- Immediately after EACH task's implementation and required verification pass, check its numbered row; reconcile detailed steps, owning README status and walkthrough evidence. Leave partial/blocked/unverified tasks unchecked.
- Recalculate Completed as checked child tasks / total child tasks; exclude phase-heading rows. Progress = round(100 * completed / total, 1)%; 20-cell bar fills floor(20 * completed / total) cells.
- Check a phase only when all child tasks and phase completion gates pass. Set Current Task to the next pending task, or retain a blocked task with its reason; use None — complete only when all tasks pass.
- Preserve other tasks' states/numbering/links. Report tracker totals, progress and Current Task in the walkthrough.
- Run focused tests with explicit paths and --no-cov during iteration, independent normal/boundary/failure vectors, FR log checks and applicable lifecycle/resource tests. Run prescribed candidate coverage and UI typecheck/test/build plus isolated real-host acceptance when UI is connected.
- Record exact commands/results, timestamped artifacts, deviations and unresolved gaps. Never infer SQX parity from static inventory, code coverage or matching screens.
- Do not commit, merge, push, rebase or rewrite history without separate owner authorization after walkthrough review.
```

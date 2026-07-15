## Three-agent pipeline

Each domain is built by three agents in sequence, each super-focused on one stage. This saves tokens and doubles as a review process—no single agent does everything from A to Z.

| Stage                           | Agent            | Prompt                                                          | Touches code?                       |
| ------------------------------- | ---------------- | --------------------------------------------------------------- | ----------------------------------- |
| 1. Pre-build readiness audit    | **Claude** | Prompt 1                                                        | No—read-only                       |
| 2. Implementation               | **Gemini** | Prompt 2a (feature by feature, recommended) or 2b (full domain) | Yes—the only agent that edits code |
| 3. Post-build completion review | **Codex**  | Prompt 3                                                        | No—read-only                       |

Rules of the pipeline:

- **Claude (Prompt 1)** verifies everything is in order before the next domain is built. It never modifies files. Its output (roadmap plus any blocker fixes) is handed to Gemini as the input for Prompt 2.
- **Gemini (Prompt 2a or 2b)** is the only agent permitted to create or modify code and documentation. It builds from Claude's readiness audit and executes fix instructions handed over from Claude or Codex.
- **Codex (Prompt 3)** performs the final review after the build. It never modifies files.
- When Claude or Codex finds any issue or blocker, it must not fix it. Instead, it ends its report with a **Gemini handoff report**: for every issue, the correct recommendation and exact step-by-step implementation instructions, written so the report can be copy-pasted directly into Gemini for execution.

The best implementation unit is normally one complete Section 4 feature—not the whole domain and not an isolated file.

For example: “Implement Utils Section 4.1 `contracts/`, including `audit.py`, `auth.py`, `__init__.py`, and `FR-UTL-001` through `FR-UTL-003`.”

That unit is cohesive, small enough to verify, and contains the file order, exports, dependencies, requirements, and tests needed to declare the feature complete.

## How the README drives implementation

| README section | Implementation purpose                                                    |
| -------------- | ------------------------------------------------------------------------- |
| Section 1      | Defines ownership and boundaries—what may and may not be built           |
| Section 2      | Defines the final package tree and dependency order                       |
| Section 3      | Defines workflows that must work after the underlying features exist      |
| Section 4      | Primary implementation plan: features → files → functions/requirements  |
| Section 5      | Package-wide configuration, security, performance, and architecture rules |
| Section 6      | Must contain no unresolved decision affecting the work                    |
| Section 7      | Tests, completion evidence, and definition of done                        |
| Section 8      | Change process or usage examples, depending on the README                 |

Section 4 tells you what to implement, but the implementer must read Sections 1, 3, 5, and 7 before changing anything. Otherwise, a locally correct function can violate a domain boundary or workflow.

Also, domain READMEs are the truth for domain internals, but [PROJECT.md](C:/Users/rharu/AppDev/HaruquantAI/docs/PROJECT.md:339) remains authoritative for cross-domain ownership, contracts, workflows, and implementation order.

## Recommended implementation sequence

Use the confirmed domain order:

1. Utils
2. Brokers
3. Data
4. Indicators
5. Strategy
6. Risk
7. Trading
8. Simulation
9. Analytics
10. Optimization, Research, and Portfolio
11. UI/API

Within each domain:

1. Run a read-only implementation-readiness audit.
2. Select the first incomplete Section 4 feature whose dependencies are available.
3. Implement that feature’s files in the exact Files-table order.
4. Implement each `FR-*` requirement mapped to each file.
5. Add its unit tests and usage examples alongside the implementation.
6. Update the feature’s `__init__.py` last.
7. Run targeted formatting, linting, typing, and tests.
8. Mark individual rows `Completed` only when evidence passes.
9. After all participating features exist, complete the relevant Section 3 workflows and integration tests.
10. Run the package Definition of Done before moving to the next domain.

Do not create the entire package tree as empty scaffolding first. Create each folder and file when its feature is implemented.

## When to use feature-level versus file-level prompts

Use a feature-level prompt by default.

A feature-level task should include:

- One Section 4.x feature
- Every file in its Files table
- Every mapped `FR-*`
- Targeted unit and usage tests
- Feature exports
- README status updates

Use a file-level prompt only when:

- The feature is unusually large.
- The file has several substantial requirements.
- All upstream files in that feature are already complete.
- The prompt explicitly lists the `FR-*` requirements assigned to that file.

Never prompt only “implement `audit.py`.” Include its domain, feature, requirements, dependencies, tests, and boundaries.

## Recommended task organization

Use one Gemini build task per domain. Inside that task, implement one feature per approval cycle.

That gives the task enough domain context without allowing it to accumulate unrelated domains. Repository documentation remains the memory between tasks.

A good rhythm is:

```text
Claude: domain-readiness audit (Prompt 1)
  → Gemini: Feature 4.1 (Prompt 2a; or the whole domain via Prompt 2b)
  → Gemini: Feature 4.2
  → ...
  → Gemini: Section 3 workflow integration
  → Gemini: Section 7 package completion
  → Codex: full domain completion review (Prompt 3)
  → Gemini: execute Codex's handoff report (if findings)
  → Next domain
```

## Prompt 1: Domain implementation roadmap — Claude (pre-build)

Run this in **Claude** once at the beginning of each domain. It is read-only.

```
You are the pre-build review agent. Your role is strictly limited to auditing and reporting: verify that everything up to this point is in order before the `[DOMAIN]` domain is built. You must NOT create, modify, or delete any file or code. Implementation is handled by a separate build agent (Gemini); your output is its input.

Perform a read-only implementation-readiness audit for the `[DOMAIN]` domain.

Authoritative sources:
- `AGENTS.md`
- `docs/PROJECT.md`
- `docs/ARCHITECTURE.md`
- `docs/CHANGELOG.md`
- `[DOMAIN README PATH]`
- The READMEs of every declared upstream dependency

Do not modify files.

Determine:

1. The domain’s ownership and prohibited responsibilities.
2. Its owned and consumed contracts, including owners and versions.
3. The Section 4 feature implementation order.
4. The file order within every feature.
5. The exact `FR-*` requirements assigned to every file.
6. Which existing files are reusable, non-conforming, obsolete, or missing.
7. The tests and usage examples required for every feature.
8. Which Section 3 workflows can only be completed after multiple features.
9. Any contradiction between the domain README and `docs/PROJECT.md`.
10. The recommended sequence of bounded implementation tasks.

Return a dependency-ordered implementation roadmap. Do not guess through missing specifications. Report any missing or conflicting requirement as a blocker.

If you find any blocker or issue that must be fixed before building can start, do not fix it yourself. Instead, end your report with a section titled `GEMINI HANDOFF REPORT` containing, for each issue:

1. Issue ID and severity.
2. What is wrong, with exact file and line evidence.
3. The correct recommendation for resolving it.
4. Exact step-by-step implementation instructions (files to edit, changes to make, tests to run, validation to perform).

Write the handoff report as a self-contained prompt that can be copy-pasted directly into the build agent (Gemini) without additional context.
```

## Prompt 2a: Implement one feature—recommended default — Gemini (build)

Run this in **Gemini**. Gemini is the only agent in the pipeline that touches code. Paste Claude's Prompt 1 roadmap (and any handoff report) into the placeholder below. This is the recommended path: one feature per run, repeated in roadmap order until the domain is complete.

```
You are the build agent and the only agent permitted to create or modify code and documentation in this pipeline. A read-only pre-build audit (Prompt 1, run by Claude) has already verified readiness; its roadmap is your authoritative input. A separate read-only review agent (Codex) will verify your work afterward—do not perform your own final domain review.

Pre-build audit input:

[PASTE CLAUDE'S PROMPT 1 ROADMAP AND ANY GEMINI HANDOFF REPORT HERE]

If a handoff report is included above, execute its fix instructions exactly as specified before or as part of the approved scope. Do not re-litigate its findings; if an instruction is impossible or conflicts with the specs, stop and report it.

Implement `[DOMAIN README PATH]` Section `[4.X]`, `[FEATURE NAME]`.

Approved scope:
- Feature: `[FEATURE NAME]`
- Files: `[EXACT FILE LIST FROM THE FILES TABLE]`
- Requirements: `[EXACT FR-ID RANGE OR LIST]`
- Tests: the targeted unit, usage, and feature-integration tests required by the README
- Documentation: update only the affected README statuses/checklists and `docs/CHANGELOG.md`

Before editing:

1. Read `AGENTS.md`, `docs/PROJECT.md`, `docs/ARCHITECTURE.md`, `docs/CHANGELOG.md`, the complete domain README, and the READMEs of direct dependencies.
2. Verify that all upstream features and consumed contracts required by this feature are available.
3. Inspect existing code and tests for reusable behavior and conflicts.
4. Produce the required dry run:
   - files read;
   - files created/changed;
   - requirements implemented;
   - commands/tests planned;
   - scope boundaries;
   - blockers/risks;
   - rollback path.
5. Wait for the exact phrase `APPROVED: EXECUTE`.

After approval:

1. Implement files in the exact order listed in the feature’s Files table.
2. Implement only the mapped `FR-*` requirements.
3. Preserve domain boundaries and receiver-owned contract rules.
4. Do not add compatibility aliases, speculative abstractions, dependencies, defaults, trading rules, or unrelated refactors.
5. Fit every module, class, and function with a proper Google-style docstring—no missing or non-standard docstrings.
6. Log every function using the system-wide logger (`from app.utils import logger`): every important step is logged, and every function contains at least one logger call stating what that function is doing.
7. Update feature and package exports only after their implementation exists.
8. Add a targeted unit test and runnable usage example for every public requirement.
9. Run targeted formatting, linting, mypy, tests, and applicable security/import checks.
10. Mark a requirement `Completed` only when implementation, usage evidence, and tests pass.
11. Update the affected workflow status only if its complete end-to-end integration test now passes.
12. Report files changed, requirement status, tests, validation, risks, and selective rollback instructions.

If the specification is incomplete or conflicts with `docs/PROJECT.md`, stop and report the contradiction instead of choosing an interpretation.
```

### Prompt 2a follow-up: next feature in the same task

Use this for every feature after the first, inside the same Gemini domain task. The full Prompt 2a is only needed once per domain—the roadmap, documentation, and rules are already in the task's context, so do not re-paste them and do not re-run Claude's audit.

```
Continue the `[DOMAIN]` domain build. Implement the next feature from the approved roadmap: `[DOMAIN README PATH]` Section `[4.X]`, `[FEATURE NAME]`.

Approved scope:
- Feature: `[FEATURE NAME]`
- Files: `[EXACT FILE LIST FROM THE FILES TABLE]`
- Requirements: `[EXACT FR-ID RANGE OR LIST]`
- Tests: the targeted unit, usage, and feature-integration tests required by the README
- Documentation: update only the affected README statuses/checklists and `docs/CHANGELOG.md`

Before editing:

1. Confirm the previous feature is fully complete: its checks passed and its README statuses are truthful. If not, stop and report instead of starting this feature.
2. Verify that all upstream features and consumed contracts required by this feature are available, including features built earlier in this task.
3. Re-read only the README sections relevant to this feature; rely on the context already established in this task for the rest.
4. Produce the required dry run (files read; files created/changed; requirements implemented; commands/tests planned; scope boundaries; blockers/risks; rollback path).
5. Wait for the exact phrase `APPROVED: EXECUTE`.

After approval, apply exactly the same implementation rules as the previous feature: Files-table order, mapped `FR-*` only, domain boundaries, no speculative additions, Google-style docstrings on every module/class/function, system-wide logger (`from app.utils import logger`) with at least one logger call per function, exports last, targeted tests and validation, truthful statuses, and the standard completion report.

If the specification is incomplete or conflicts with `docs/PROJECT.md`, stop and report the contradiction instead of choosing an interpretation.
```

## Prompt 2b: Implement the full domain in one go — Gemini (build)

Run this in **Gemini** when you want the entire domain built in a single task instead of feature by feature. Use it only when the domain is small or Claude's roadmap reports zero blockers; Prompt 2a remains the recommended default. Paste Claude's Prompt 1 roadmap (and any handoff report) into the placeholder below.

```
You are the build agent and the only agent permitted to create or modify code and documentation in this pipeline. A read-only pre-build audit (Prompt 1, run by Claude) has already verified readiness; its roadmap is your authoritative input. A separate read-only review agent (Codex) will verify your work afterward—do not perform your own final domain review.

Pre-build audit input:

[PASTE CLAUDE'S PROMPT 1 ROADMAP AND ANY GEMINI HANDOFF REPORT HERE]

If a handoff report is included above, execute its fix instructions exactly as specified before starting implementation. Do not re-litigate its findings; if an instruction is impossible or conflicts with the specs, stop and report it.

Implement the complete `[DOMAIN]` domain per `[DOMAIN README PATH]`: every Section 4 feature, every mapped `FR-*` requirement, every Section 3 workflow, and the Section 7 Definition of Done.

Approved scope:
- Features: all Section 4 features, in the dependency order given by the roadmap
- Files: exactly the files in each feature's Files table—no additions
- Requirements: every declared `FR-*`, each implemented once
- Tests: the targeted unit, usage, feature-integration, and Section 3 workflow-integration tests required by the README
- Documentation: update only the affected README statuses/checklists and `docs/CHANGELOG.md`

Before editing:

1. Read `AGENTS.md`, `docs/PROJECT.md`, `docs/ARCHITECTURE.md`, `docs/CHANGELOG.md`, the complete domain README, and the READMEs of direct dependencies.
2. Verify that all upstream domains and consumed contracts required by this domain are available.
3. Inspect existing code and tests for reusable behavior and conflicts.
4. Produce a single dry run for the whole domain:
   - the feature-by-feature build order;
   - files created/changed per feature;
   - requirements implemented per feature;
   - commands/tests planned;
   - scope boundaries;
   - blockers/risks;
   - rollback path.
5. Wait for the exact phrase `APPROVED: EXECUTE`.

After approval, build one feature at a time in roadmap order. For each feature:

1. Implement its files in the exact order listed in its Files table.
2. Implement only the mapped `FR-*` requirements.
3. Preserve domain boundaries and receiver-owned contract rules.
4. Do not add compatibility aliases, speculative abstractions, dependencies, defaults, trading rules, or unrelated refactors.
5. Fit every module, class, and function with a proper Google-style docstring—no missing or non-standard docstrings.
6. Log every function using the system-wide logger (`from app.utils import logger`): every important step is logged, and every function contains at least one logger call stating what that function is doing.
7. Update feature exports only after their implementation exists; update the package `__init__.py` last.
8. Add a targeted unit test and runnable usage example for every public requirement.
9. Run targeted formatting, linting, mypy, tests, and applicable security/import checks before moving to the next feature. Do not start a feature while the previous one has failing checks.
10. Mark a requirement `Completed` only when implementation, usage evidence, and tests pass.

After all features exist:

1. Implement and run every Section 3 workflow integration test; update workflow statuses only when the complete end-to-end test passes.
2. Run the full domain-scoped validation suite and the Section 7 Definition of Done.
3. Do not create empty scaffolding ahead of the feature being implemented.
4. Report, per feature: files changed, requirement status, tests, and validation—plus domain-level workflow results, risks, and selective rollback instructions.

If any feature's specification is incomplete or conflicts with `docs/PROJECT.md`, stop at that feature and report the contradiction instead of choosing an interpretation. Report which features are complete and which remain.
```

## Prompt 3: Full domain completion review — Codex (post-build)

Run this in **Codex** only after the entire domain README is marked `Completed` and Gemini's implementation is believed finished.

```
You are the post-build review agent. Your role is strictly limited to verification and reporting: confirm that the domain Gemini built followed everything that was required and introduced no conflicts. You must NOT create, modify, or delete any file or code. All corrections are executed by the build agent (Gemini) from the handoff report you produce at the end.

Perform a strict, read-only completion review of the `[DOMAIN]` domain.

Domain scope:
- Domain README: `[DOMAIN README PATH]`
- Implementation package: `[PACKAGE PATH]`
- Tests: `[TEST PATH]`

This is a verification task, not an implementation task. Do not modify files, update statuses, install dependencies, stage changes, or fix findings.

Authoritative sources, in order:

1. Owner instructions
2. `AGENTS.md`
3. `docs/PROJECT.md`
4. `[DOMAIN README PATH]`
5. `docs/ARCHITECTURE.md`
6. `docs/CHANGELOG.md`
7. Implemented code and tests as evidence of current reality

Review objective:

Determine whether the completed implementation strictly and fully satisfies the domain README, system architecture, cross-domain contracts, safety rules, quality standards, and Definition of Done.

Do not infer compliance from a `Completed` status. Every completion claim must be proven by code and passing evidence.

## Review procedure

### 1. Purpose, ownership, and boundaries

Verify Section 1 of the domain README against the implementation.

Confirm:

- Every owned capability is implemented.
- No prohibited or excluded capability is implemented.
- The domain does not assume another domain’s responsibility.
- No provider object, database session, DataFrame, exception, or internal model crosses a prohibited boundary.
- Cross-domain imports use documented public APIs only.
- Receiver-owned requests are defined by the receiving domain.
- No circular dependency or reverse ownership has been introduced.
- Removed, rejected, legacy, compatibility, agent, or speculative capabilities are absent.

Report every violation with exact file and line evidence.

### 2. Final package structure

Compare the actual package recursively with README Section 2.

Verify:

- Every specified folder and file exists.
- No required file is missing.
- No undocumented production file or parallel implementation exists.
- Files appear in the documented dependency order.
- Every file has the documented focused responsibility.
- Legacy files, aliases, wrappers, and obsolete compatibility paths have been removed where the final structure excludes them.
- Every `__init__.py` exposes exactly the documented public names through explicit imports and `__all__`.
- Imports do not perform prohibited initialization or side effects.

Produce an expected-versus-actual file inventory.

### 3. Workflow verification

Review every Section 3 `WF-[DOM]-*` workflow.

For each workflow, verify:

- The documented trigger and input boundary exist.
- Every required step is implemented in the documented order.
- The output boundary matches the specification.
- Failure behavior is deterministic and fail-closed.
- Side effects occur only at the documented boundary.
- Required audit, trace, persistence, idempotency, freshness, and reconciliation behavior exists.
- The integration test exercises the genuine end-to-end workflow rather than mocking away the behavior under review.
- Every referenced `SYS-WF-*` chain matches `docs/PROJECT.md`.

A workflow is compliant only when its complete integration test passes.

### 4. File and functional-requirement traceability

Review every Section 4 feature, file, and `FR-[DOM]-*` requirement.

For each Files-table row, verify:

- The file exists at the exact documented path.
- Its responsibility matches the implementation.
- Every documented key export exists.
- No undocumented public export exists.
- Standard-library, third-party, and local dependencies match the table.
- No undeclared dependency or forbidden deep import exists.

For every functional requirement, verify:

- The mapped class, function, method, constant, or contract exists.
- Its public signature and types match exactly.
- Its observable behavior satisfies the full requirement.
- Side effects match the documented side-effect classification.
- Documented errors and failure conditions are implemented.
- Validation occurs at the required boundary.
- No hidden fallback, silent failure, guessed default, or unapproved behavior exists.
- A focused unit test proves the requirement.
- A runnable usage test exercises the supported public API.
- The test would fail if the required behavior were removed or materially broken.

Produce a complete traceability matrix with these columns:

| Requirement | README location | Implementation location | Unit test | Usage test | Result | Finding |
|---|---|---|---|---|---|---|

Every declared `FR-*` must appear exactly once in this matrix.

### 5. Package-wide requirements and configuration

Review every Section 5 `NFR-[DOM]-*`, shared setting, feature limit, and policy.

Verify:

- Configuration fields exist with the documented type and ownership.
- Defaults match exactly.
- Required values cannot be omitted.
- “No shared default” values require explicit profile configuration.
- Bounds are validated before allocation, mutation, network access, or expensive work.
- Exceeded limits produce the documented deterministic failure.
- Secrets are never logged, persisted, returned, or embedded in identifiers.
- Time handling is UTC-aware and deterministic.
- Numeric behavior uses the required precision and rejects unsafe values.
- Correlation and trace identifiers follow the prefixed UUID4 policy.
- Import safety, determinism, serialization, reliability, and compatibility rules are enforced.
- Persistent state, schemas, migrations, and write authority match `docs/PROJECT.md`.
- The domain does not redefine shared settings or another domain’s policy.

Produce a separate `NFR-*` compliance matrix with implementation and test evidence.

### 6. Contract and persistence reconciliation

Reconcile every owned and consumed contract with `docs/PROJECT.md` and relevant producer/consumer READMEs.

Verify:

- Name, owner, version, producer, consumer, and purpose match.
- `contract_version` and `schema_id` are treated according to the specification.
- The domain does not redefine consumed contracts.
- All required fields, types, identities, timestamps, hashes, and failure semantics match.
- Producer-consumer compatibility tests exist and pass.
- Persisted-state ownership, read access, write authority, tables, artifacts, and migration definitions match the top-level registry.
- No implementation bypasses the owning domain through direct storage access.

### 7. Safety and security review

Verify all applicable safety requirements, including:

- Fail-closed behavior for missing, stale, invalid, unknown, or conflicting evidence.
- No live mutation without deterministic approval.
- No Risk, kill-switch, idempotency, reconciliation, or authority bypass.
- No invented backtest results, performance values, broker fills, or provider evidence.
- No secret leakage in logs, errors, events, reports, audit records, or tests.
- No raw external exceptions crossing public boundaries.
- No unsafe network, filesystem, subprocess, environment, wall-clock, or randomness access where prohibited.
- No silent retry after an unknown mutation outcome.
- No arbitrary code execution or unapproved dynamic imports.
- No import-time external or persistent side effects.

Treat any safety bypass or false success claim as a blocking finding.

### 8. Code-quality review

Verify the implementation follows `AGENTS.md` and repository configuration:

- Google Python style.
- Explicit typing on every signature.
- Google-style docstrings on every module, class, and function—flag any missing or non-standard docstring.
- Absolute and correctly grouped imports.
- No bare `except`.
- Logging instead of `print`.
- Every function uses the system-wide logger (`from app.utils import logger`), every important step is logged, and every function contains at least one logger call stating what that function is doing—flag any function with no logging or using a non-standard logger.
- No silent failures.
- No unused compatibility code or speculative abstraction.
- No duplicated domain logic.
- No dependency version contradicting `pyproject.toml`.
- No secrets or sensitive fixtures.
- Public APIs are minimal and intentional.

Inspect the implementation directly; do not rely only on lint output.

### 9. Test and validation execution

Run the domain-scoped validation required by its README and `AGENTS.md`.

At minimum, where applicable:

- Trailing-whitespace and final-newline checks.
- `ruff check` for the domain package and its tests.
- `ruff format --check` for the domain package and its tests.
- `mypy` for the domain package and its tests.
- Domain unit tests.
- Domain usage tests.
- Domain integration/workflow tests.
- Contract-compatibility tests.
- Security/import-side-effect tests.
- Property or golden tests required by the README.
- Domain coverage measurement.

Do not run live broker operations, real external sends, destructive persistence actions, or other live side effects.

Do not run the entire repository test suite unless the domain README explicitly requires it. Run the complete domain-scoped suite.

Coverage must meet or exceed 80%, and every public requirement must have meaningful direct test evidence. Coverage alone does not prove requirement compliance.

Record every command, exit result, and relevant test count.

### 10. Status and checklist truthfulness

Review every README status and checklist entry.

Verify:

- Every `Completed` file exists and matches its specification.
- Every `Completed` requirement has implementation, unit-test, and usage evidence.
- Every `Completed` workflow has a passing end-to-end integration test.
- Every checked Definition of Done item is demonstrably true.
- No `Missing` or `Partial` item remains if the domain claims completion.
- No open decision, unresolved conflict, placeholder, TODO, deferred choice, or guessed behavior remains.
- `docs/CHANGELOG.md` accurately records the implementation.

A false or unsupported `Completed` status is a blocking documentation-integrity finding.

## Finding classification

Classify findings as:

- `BLOCKING`: Safety violation, ownership violation, contract incompatibility, missing required capability, failed required test, false completion claim, persistence-authority violation, or behavior that can produce an incorrect/live side effect.
- `HIGH`: Material requirement mismatch, workflow failure, undocumented public API, missing validation, deterministic-behavior failure, or major test gap.
- `MEDIUM`: Localized implementation or traceability defect that does not currently violate a safety boundary.
- `LOW`: Minor documentation, naming, maintainability, or test-clarity defect with no behavioral impact.

Do not dilute findings by calling the domain “ready with corrections.”

## Required final result

Return exactly one result:

- `READY`: Every required feature, file, requirement, workflow, contract, test, NFR, and checklist item is compliant, and all required validation passes.
- `NOT READY`: One or more deviations, unsupported completion claims, test failures, missing requirements, or unresolved review findings exist.
- `BLOCKED`: The review cannot be completed because required evidence, dependencies, files, or execution capability is unavailable.

`READY` requires zero findings at every severity.

## Required report structure

1. **Result**
2. **Executive reason**
3. **Blocking and high findings**
4. **Medium and low findings**
5. **Expected-versus-actual package inventory**
6. **Functional-requirement traceability matrix**
7. **Non-functional-requirement compliance matrix**
8. **Workflow and system-workflow verification**
9. **Contract and persistence reconciliation**
10. **Public API and dependency-boundary review**
11. **Safety and security review**
12. **Commands and validation results**
13. **Coverage result**
14. **README status/checklist accuracy**
15. **Gemini handoff report (ordered correction plan)**
16. **Final review checklist**

Every finding must include:

- Finding ID
- Severity
- Requirement or rule violated
- Exact file and line
- Current behavior
- Required behavior
- Why it matters
- Verification needed after correction

Do not implement corrections during this review. End with a section titled `GEMINI HANDOFF REPORT`: an ordered, bounded correction plan containing, for each finding:

1. Finding ID and severity.
2. The correct recommendation for resolving it.
3. Exact step-by-step implementation instructions (files to edit, changes to make, tests to run, validation to perform).
4. Verification required after the correction.

Write the handoff report as a self-contained prompt that can be copy-pasted directly into the build agent (Gemini) without additional context. After Gemini executes it, this review must be re-run.
```

The key principle is:

```text
Implement by feature.
Code by file.
Verify by requirement.
Integrate by workflow.
Complete by package.
```

That structure gives you the smallest safe implementation increments without losing the architectural context.

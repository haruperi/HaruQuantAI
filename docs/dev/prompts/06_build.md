The best implementation unit is normally one complete Section 4 feature—not the whole domain and not an isolated file.

For example: “Implement Utils Section 4.1 `contracts/`, including `audit.py`, `auth.py`, `__init__.py`, and `FR-UTL-001` through `FR-UTL-003`.”

That unit is cohesive, small enough to verify, and contains the file order, exports, dependencies, requirements, and tests needed to declare the feature complete.

## How the README drives implementation

| README section | Implementation purpose |
|---|---|
| Section 1 | Defines ownership and boundaries—what may and may not be built |
| Section 2 | Defines the final package tree and dependency order |
| Section 3 | Defines workflows that must work after the underlying features exist |
| Section 4 | Primary implementation plan: features → files → functions/requirements |
| Section 5 | Package-wide configuration, security, performance, and architecture rules |
| Section 6 | Must contain no unresolved decision affecting the work |
| Section 7 | Tests, completion evidence, and definition of done |
| Section 8 | Change process or usage examples, depending on the README |

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

Use one Codex task per domain. Inside that task, implement one feature per approval cycle.

That gives the task enough domain context without allowing it to accumulate unrelated domains. Repository documentation remains the memory between tasks.

A good rhythm is:

```text
Domain-readiness audit
  → Feature 4.1
  → Feature 4.2
  → ...
  → Section 3 workflow integration
  → Section 7 package completion
  → Next domain
```

## Prompt 1: Domain audit and feature implementation

Use this for the default implementation path (feature-level tasks).

```
Implement `[DOMAIN README PATH]` Section `[4.X]`, `[FEATURE NAME]`.

Approved scope:
- Feature: `[FEATURE NAME]`
- Files: `[EXACT FILE LIST FROM THE FILES TABLE]`
- Requirements: `[EXACT FR-ID RANGE OR LIST]`
- Tests: the targeted unit, usage, and feature-integration tests required by the README
- Documentation: update only the affected README statuses/checklists and `docs/CHANGELOG.md`

Authoritative sources:
- `AGENTS.md`
- `docs/PROJECT.md`
- `docs/ARCHITECTURE.md`
- `docs/CHANGELOG.md`
- `[DOMAIN README PATH]`
- The READMEs of every declared upstream dependency

---

### Step 1: Initial Domain Audit (Only if this is the FIRST feature in this domain)
Perform a read-only implementation-readiness audit for the `[DOMAIN]` domain. Do not modify files. Determine:
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

---

### Step 2: Feature-Level Dry Run (Required for ALL features)
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

---

### Step 3: Execution and Implementation (After approval)
1. Implement files in the exact order listed in the feature’s Files table.
2. Implement only the mapped `FR-*` requirements.
3. Preserve domain boundaries and receiver-owned contract rules.
4. Do not add compatibility aliases, speculative abstractions, dependencies, defaults, trading rules, or unrelated refactors.
5. Update feature and package exports only after their implementation exists.
6. Add a targeted unit test and runnable usage example for every public requirement.
7. Run targeted formatting, linting, mypy, tests, and applicable security/import checks.
8. Mark a requirement `Completed` only when implementation, usage evidence, and tests pass.
9. Update the affected workflow status only if its complete end-to-end integration test now passes.
10. Report files changed, requirement status, tests, validation, risks, and selective rollback instructions.

If the specification is incomplete or conflicts with `docs/PROJECT.md`, stop and report the contradiction instead of choosing an interpretation.
```

## Prompt 2: Implement one file—only for a large feature

```
Implement `[FILE PATH]` within `[DOMAIN README PATH]` Section `[4.X]`.

Scope:
- File: `[FILE PATH]`
- Responsibility: `[RESPONSIBILITY FROM FILES TABLE]`
- Key exports: `[EXACT EXPORTS]`
- Requirements: `[EXACT FR-IDS MAPPED TO THIS FILE]`
- Declared dependencies: `[DEPENDENCIES FROM FILES TABLE]`
- Tests: only the unit and usage tests mapped to these requirements

First verify that every preceding file and dependency in the feature is implemented and compatible.

Before editing, provide the `AGENTS.md` dry run and wait for `APPROVED: EXECUTE`.

After approval:

- Implement only the listed requirements and exports.
- Do not modify downstream files except tests and necessary feature exports.
- Do not invent behavior not stated in the requirements.
- Add or update the mapped unit and usage tests.
- Run targeted formatting, linting, mypy, and tests.
- Update README statuses only for requirements proven by passing evidence.
- Do not mark the overall feature or workflow complete unless all its files and integration tests are complete.
- Stop and report any contract, dependency, or specification conflict.
```

## Prompt 3: Full domain completion review

Use this only after the entire domain README is marked `Completed` and implementation is believed finished.

```
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
- Every module, class, and function is properly fitted with Google-style docstrings
- Every function is properly logged using system-wide logger (from app.utils import logger). Every important step is logged and each function has at least one logger stating what is being done in that function.
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
- Google-style module, class, and function docstrings.
- Absolute and correctly grouped imports.
- No bare `except`.
- Logging instead of `print`.
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
15. **Ordered correction plan**
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

Do not implement corrections during this review. End with an ordered, bounded correction plan that can be approved and executed in a separate task.
```

## After all features in a domain

Run a separate completion task that:

- Verifies the final package tree against Section 2.
- Executes every Section 3 workflow integration test.
- Confirms owned and consumed contracts against `PROJECT.md`.
- Checks public exports and import boundaries.
- Runs the package’s Section 7 validation.
- Measures the required coverage.
- Updates the package completion checklist.
- Declares the domain complete only when every required row has evidence.

The key principle is:

```text
Implement by feature.
Code by file.
Verify by requirement.
Integrate by workflow.
Complete by package.
```

That structure gives you the smallest safe implementation increments without losing the architectural context.

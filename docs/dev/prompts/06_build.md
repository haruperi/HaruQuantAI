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

## Prompt 1: Domain implementation roadmap

Use this once at the beginning of each domain. It is read-only.

```
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
```

## Prompt 2: Implement one feature—recommended default

```
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
5. Update feature and package exports only after their implementation exists.
6. Add a targeted unit test and runnable usage example for every public requirement.
7. Run targeted formatting, linting, mypy, tests, and applicable security/import checks.
8. Mark a requirement `Completed` only when implementation, usage evidence, and tests pass.
9. Update the affected workflow status only if its complete end-to-end integration test now passes.
10. Report files changed, requirement status, tests, validation, risks, and selective rollback instructions.

If the specification is incomplete or conflicts with `docs/PROJECT.md`, stop and report the contradiction instead of choosing an interpretation.
```

## Prompt 3: Implement one file—only for a large feature

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
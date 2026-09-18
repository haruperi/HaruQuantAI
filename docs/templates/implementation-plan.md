# Implementation Plan: [Goal / Task / Feature Title]

> **Task ID:** `[FEAT-XXX | TASK-XXX]`
> **Iteration:** `[1]`
> **Branch:** `[feature/... | task/... | main]`
> **Baseline Commit:** `[SHA]`

Follow-up work on the same task appends a clearly labelled iteration to this
file. Do not create a second plan for the same task run.

---

### User Review Required

> [!IMPORTANT]
> Highlight critical design decisions, breaking changes, or items needing explicit owner sign-off.

### Open Questions

> [!NOTE]
> Clarifying questions or unresolved assumptions that impact the scope (or `- NONE`).

---

## 1. Goal, Requirements & Usage Evidence

- **Problem Statement & Goal**: Brief context and what this change accomplishes.
- **Ratified Requirements**: Exact functional requirements / specifications being satisfied.
- **Usage Evidence**: Primary purpose demonstrated by a realistic offline harness in `tests/examples/`.

## 2. Files Read (Audit Trail)

List of all existing files inspected to ground this plan in repository truth:

- [filename.py](file:///path/to/filename.py) — brief note on what was verified.

## 3. Proposed Changes & Implementation Order

Grouped by component / domain layer, using explicit action tags and clickable links:

### [Component / Layer Name]

- `[MODIFY]` [existing_file.py](file:///path/to/existing_file.py) — summary of edits.
- `[NEW]` [new_file.py](file:///path/to/new_file.py) — purpose and public symbols.
- `[DELETE]` [deprecated_file.py](file:///path/to/deprecated_file.py) — removal rationale.

### Sequential Implementation Order

1. Step 1 (e.g. contracts / DTOs first)
2. Step 2 (persistence / internal helpers)
3. Step 3 (service feature implementation)
4. Step 4 (tests and usage examples)

## 4. Dependencies and Contracts

- Public contracts, DTOs, protocols, and events imported or exported.
- Cross-boundary capability keys resolved via `FeatureContext`.
- Persistence boundaries (ensuring database operations stay in `app/services/persistence/`).

## 5. Blockers, Risks, and Trade-offs

- Technical risks, potential side effects, and design trade-offs.
- Assumptions made and rationale.

## 6. Scope Boundaries (Inclusions & Exclusions)

- **In Scope**: Explicit list of deliverables.
- **Out of Scope / Non-Goals**: Explicit exclusions to prevent scope creep.

## 7. Verification Plan

Summary of how you will verify that your changes have the desired effects.

### Automated Tests

- Exact unit / integration test commands to run:
  ```bash
  uv run pytest tests/path/to/test_feature.py -v
  ```

### Usage Evidence Run

- Primary purpose demonstrated by a realistic harness in `tests/examples/`:
  ```bash
  uv run python tests/examples/NN_domain.py
  ```

### Quality Pipeline

- Full verification suite:
  ```bash
  uv run python scripts/ci_check.py
  ```

### Manual Verification

- Asking the user to verify behavior, interactive prompts, etc. (or `- NONE`).

## 8. Rollback & Contingency

Step-by-step procedure to safely undo all changes done by this implementation.

```text
ALLOWED_WRITE_PATHS:
- app/contracts/domain.py
- app/services/domain/feature.py
- tests/services/domain/test_feature.py
- tests/examples/NN_domain.py
END_ALLOWED_WRITE_PATHS:
```

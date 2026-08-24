# Test

> **Package:** `app/services/test/`
> **Status:** `Implemented`
> **Last updated:** `2026-08-24`
> **Domain ID:** `D-TEST`

> This README is the domain package's **single source of truth** for domain boundaries, composable feature capabilities, architecture invariants, implementation sequence, progress, usage examples, and tests.
> Temporary domain used exclusively for orchestrator workflow validation (`FEAT-TEST-GREETING`).

---

## 1. Purpose and Boundary

### Purpose

The Test domain delivers temporary, pure in-memory test capabilities used exclusively to validate the orchestrator workflow (Planner, Executor, Reviewer) and physical feature removability. It owns no persistent state, no UI, and no external I/O.

### Owns

- `FEAT-TEST-GREETING` — Deterministic Greeting Generation.

### Does not own

- Persistent storage or database tables.
- UI components or views.
- Network calls or external integrations.
- Trading, market data, simulation, analytics, or research behavior.

---

## 2. Domain Features

| Status | Feature ID | Name | Module | Provided Capability |
|---|---|---|---|---|
| Implemented | `FEAT-TEST-GREETING` | Test Greeting | `app.services.test.greeting` | `test.greeting@1` |

---

## 3. Functional Requirements

| Status | Requirement ID | Feature ID | Summary | Acceptance Evidence |
|---|---|---|---|---|
| Implemented | `FR-TEST-GENERATE_GREETING` | `FEAT-TEST-GREETING` | Validate caller name (non-empty, trimmed, bounded length) and return deterministic formatted greeting. | `tests/services/test/greeting/test_greeting.py` |

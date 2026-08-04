# Orchestration

> **Package:** `app/agentic/orchestration`
> **Feature:** `FEAT-AGT-04` Durable Task and Workflow Orchestration
> **Status:** `Completed`
> **Last updated:** `2026-08-03`

This README is subordinate to the canonical Agentic Feature Registry in
`app/agentic/README.md`. It defines no separate feature registry or requirement.

## Boundary

This feature owns workflow validation, idempotent submission, lifecycle
transitions, checkpoint sequencing, and revision decisions. `runtime.py` adapts
the workflow-store port to durable storage but performs no direct Data
runtime-store CRUD.

All durable CRUD is centralized in the private
`app/agentic/persistence/` support package. Idempotency reservation and initial
run creation remain one atomic transition, and workflow replacement remains
compare-and-swap guarded. Public consumers continue to use the Agentic package
boundary.

## Evidence

- Unit: `tests/agentic/unit/test_orchestration.py`
- Durable integration: `tests/agentic/integration/test_durable_runtime.py`
- Usage: `tests/agentic/usage/04_orchestration.py`

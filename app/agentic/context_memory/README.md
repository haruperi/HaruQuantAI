# Context Memory

> **Package:** `app/agentic/context_memory`
> **Feature:** `FEAT-AGT-06` Evidence Context and Governed Memory
> **Status:** `Completed`
> **Last updated:** `2026-08-03`

This README is subordinate to the canonical Agentic Feature Registry in
`app/agentic/README.md`. It defines no separate feature registry or requirement.

## Boundary

This feature owns evidence-context assembly, governed memory validation,
redaction-aware records, scope and freshness filtering, and memory-stream
sequencing. `runtime.py` adapts its port to durable storage but performs no
direct Data runtime-store CRUD.

All durable CRUD is centralized in the private
`app/agentic/persistence/` support package. The adapter preserves the existing
`memory-records` collection, task-scoped partitioning, append ordering, and
bounded reads. Public consumers continue to use the Agentic package boundary.

## Evidence

- Unit: `tests/agentic/unit/test_context_memory.py`
- Durable integration: `tests/agentic/integration/test_durable_runtime.py`
- Usage: `tests/agentic/usage/06_context_memory.py`

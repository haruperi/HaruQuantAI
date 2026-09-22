# Shared Plugin Metamodel and Wire Protocol

This package defines the universal vocabulary and wire representation for HaruQuantAI components:

- `schema.py` — Bounded immutable values, descriptors, ports, parameter schemas, units, constraints, and presentation hints.
- `lowering.py` — Semantic IR, universal operator vocabulary, and lowering protocols.
- `spec.py` — Plugin identity, versioning, operation declarations, capabilities, and wire-safe catalog views.
- `algebra.py` — Versioned graph documents, node/edge specifications, cycle detection, and catalog validation.
- `wire.py` — Strict UTF-8 JSON projection, canonical whitespace-free serialization, SHA-256 fingerprinting, and parsing with duplicate-key rejection.

## Architecture and Import Rules

The shared-module import DAG is strictly acyclic:

```text
schema
  ^
  |
lowering
  ^
  |
spec --------> app.kernel.capability only
  ^
  |
algebra
  ^
  |
wire
```

- `schema.py` depends only on the Python standard library.
- `lowering.py` depends on `schema.py` and the standard library.
- `spec.py` depends on `schema.py`, `lowering.py`, `app.kernel.capability`, and the standard library.
- `algebra.py` depends on `schema.py`, `lowering.py`, `spec.py`, and the standard library.
- `wire.py` may import all four shared modules and the standard library.
- **No shared module may import `app.host`, `app.ui`, or concrete plugins.**
- **No shared module may access filesystem paths, I/O, threads, or environment variables at import time.**

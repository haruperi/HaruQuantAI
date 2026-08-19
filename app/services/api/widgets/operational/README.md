# Operational Read Model and Command API

## Purpose

Owns `FEAT-API-10`, the versioned operational workstation projection and
optimistic command boundary.

## Standard files

- `schemas.py` assembles the versioned boundary projection.
- `orchestration.py` validates and delegates optimistic commands.
- `routes.py` exposes the authenticated read and command endpoints.

## Boundaries

- Missing owner composition fails closed.
- Commands require version, idempotency, and correlation evidence.
- Owner results are never inferred when delegation is ambiguous.

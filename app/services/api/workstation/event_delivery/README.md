# Ordered Event Delivery

Focused API transport capability for validating, sequencing, resuming, and
closing bounded event streams. It owns transport state only; source domains
remain authoritative for event truth.

## Files

- `routes.py`: declares no independent resource routes.
- `schemas.py`: binds the shared stream envelope.
- `events.py`: validates owner events for public delivery.
- `orchestration.py`: owns connection quotas, ordering, resume, and cleanup.

## Requirements

- `FR-API-020`: normalize secret-safe ordered stream events.
- `FR-API-021`: govern bounded connection lifecycle and resume behavior.

## Evidence

- `tests/api/usage/06_streams.py`
- `tests/api/unit/test_streams.py`
- `tests/api/nfr/test_nfr_007_streaming.py`

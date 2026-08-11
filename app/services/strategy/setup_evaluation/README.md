# setup_evaluation/ — Setup Evaluation

Feature `FEAT-STR-17` (operational planning).

## Responsibility

Return deterministic `MATCH`/`NO_MATCH`/`STALE`/`REGIME_MISMATCH`/
`INSUFFICIENT_EVIDENCE` results with explicit source-snapshot references.

## Public API

- `build_setup_evaluation`, `parse_setup_evaluation`

## Boundaries

- Evaluation outcomes are deterministic and fail closed; non-match outcomes
  require reason codes, and `MATCH` cannot carry failure reasons.

## Persistence

Evaluation evidence (append-only). See the owning package README for the
authoritative schema.

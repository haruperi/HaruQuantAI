# management_plan/ — Exit and Management Plan

Feature `FEAT-STR-19` (operational planning).

## Responsibility

Define initial protection, targets, partial exits, trailing rules, time stop,
invalidation, and approved ownership handoff.

## Public API

- `build_exit_plan`, `parse_exit_plan`
- `build_exit_plan_handoff`

## Boundaries

- Handoff is never executable on its own; it is non-executable and only
  `READY` when external Risk/Trading interlocks permit and the route is `SIM`
  outside live.

## Persistence

Usually part of a `TradePlan`/profile. See the owning package README for the
authoritative schema.

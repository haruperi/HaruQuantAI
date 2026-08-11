# trade_plan/ — Canonical Trade Plans and Lifecycle

Feature `FEAT-STR-18` (operational planning).

## Responsibility

Build player or automated plans with entry, invalidation, stop, exit,
requested-size basis, rationale, versions, immutable release, and versioned
amendments. Includes manual (player-authored) plan support.

## Public API

- `build_trade_plan`, `parse_trade_plan`
- `transition_trade_plan`, `amend_trade_plan`
- `validate_trade_plan_for_intent`
- `build_manual_trade_plan`, `validate_manual_trade_plan`

## Boundaries

- A `TradePlan v1` remains distinct from the preserved `TradeIntent v1`.
  Plans are simulation-only when projected to intents; `READY_FOR_RISK` plans
  may produce intents only on the `SIM` route outside live.

## Persistence

Plans, versions, amendments, and lifecycle state. See the owning package README
for the authoritative schema.

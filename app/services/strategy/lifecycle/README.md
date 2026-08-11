# lifecycle/ — Strategy Lifecycle Governance

Feature `FEAT-STR-21` (operational planning).

## Responsibility

Govern draft, test, approve, suspend, retire, and version strategies while
preserving historical replay meaning.

## Public API

- `govern_strategy_lifecycle`

## Boundaries

- Lifecycle governance produces append-only mutation evidence; it never
  mutates historical version identity.

## Persistence

Lifecycle decisions and approvals (append-only). See the owning package README
for the authoritative schema.

# automation/ — Automation Mode Policy

Feature `FEAT-STR-20` (operational planning).

## Responsibility

Enforce `OFF`/`ADVISORY`/`SUPERVISED`/`AUTOMATED` automation modes, always
subordinate to Risk and Trading interlocks.

## Public API

- `evaluate_automation_mode`

## Boundaries

- Never overrides external interlocks. `SUPERVISED`/`AUTOMATED` degrade to
  `RESTRICTED` unless Risk and Trading interlocks hold, the route is `SIM`, and
  the environment is not `LIVE`.

## Persistence

Automation policy/version. See the owning package README for the authoritative
schema.

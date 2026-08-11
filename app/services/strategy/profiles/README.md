# profiles/ — Strategy Profiles and Expectancy References

Feature `FEAT-STR-15` (operational planning).

## Responsibility

Hold versioned instruments, sessions, regimes, dependencies, rules,
permissions, and exact links to approved expectancy profiles **without deciding
eligibility**. Profile identity and version-exact expectancy references are
versioned as part of the strategy profile.

## Public API

- `build_strategy_profile`, `parse_strategy_profile`
- `build_expectancy_reference`, `parse_expectancy_reference`, `evaluate_expectancy_reference`

## Boundaries

- Never decides eligibility; eligibility is delegated to the exact Research
  provider. Absent, failed, or mismatched providers fail closed to
  `NOT_ELIGIBLE`.

## Persistence

Part of versioned strategy profile state (`profiles`). See the owning package
README for the authoritative schema.

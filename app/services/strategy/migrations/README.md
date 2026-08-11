# Strategy Migration Infrastructure

This private support package owns Strategy's ordered migration definitions and
delegates their execution to Data's public migration boundary. It is not a
registered Strategy feature, exposes no package-root API, and contains no
registry, checkpoint, or evaluation behavior.

`0001_strategy_domain` and `0002_strategy_seven_table_runtime` remain
byte-for-byte compatible with the original definitions. `0003_strategy_operational_planning`
is an additive migration that defines the operational-planning tables
(`strategy_profiles`, `strategy_playbooks`, `strategy_setup_evaluations`,
`strategy_plans`, `strategy_automation_policy`, `strategy_lifecycle`). Mutating
registry and checkpoint entry points may initialize the schema idempotently.
Read-only listing, resolution, and checkpoint validation never execute
migrations and fail closed when storage is unavailable.

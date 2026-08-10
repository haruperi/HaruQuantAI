# FEAT-BRK-07 Authoritative Reads and Route Discipline

> **Status:** Completed feature `FEAT-BRK-16` (`FR-BRK-136`–`FR-BRK-138`).

This module owns deterministic, versioned route-plan and failover-decision
contracts. It selects only explicitly health-ready routes, blocks when evidence
is absent or contradictory, permits backup routes for reads or recovery only,
and never silently reroutes a write or resolves an unknown outcome as success.

- `plans.py` builds and parses `brokers.route_plan.v1`.
- `failover.py` builds and parses `brokers.failover_decision.v1`.
- `public.py` supplies the standalone functions re-exported by
  `app.services.brokers`.
- `__init__.py` is internal and does not create another cross-domain boundary.

Usage evidence is `tests/brokers/usage/features/16_route_discipline.py`;
focused policy and contract tests are in
`tests/brokers/unit/test_route_discipline_contracts.py`.

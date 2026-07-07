# ADR-ANALYTICS-LIMITS

## Status: Approved

This document defines the approved workload and response-size limits for the
Analytics service (`app/services/analytics/`). It is the authoritative source
for the numeric ceilings enforced by
`app/services/analytics/boundaries/limits.py` (`AnalyticsLimits`,
`WorkloadShape`, `enforce_limits`). Code and this ADR must stay in sync; a
mismatch is a defect in either the code or this document.

## Workload ceilings

| Limit | Value | Enforced by |
|---|---|---|
| Maximum trades per request | 10000 | `AnalyticsLimits.max_trades` |
| Maximum equity curve points per request | 100000 | `AnalyticsLimits.max_equity_points` |
| Maximum benchmark curve points per request | 100000 | `AnalyticsLimits.max_benchmark_points` |
| Maximum portfolio components per request | 100 | `AnalyticsLimits.max_portfolio_components` |
| Maximum dashboard points before downsampling | 1000 | `AnalyticsLimits.max_dashboard_points` |
| Maximum statistical resample/observation count | 500000 | `AnalyticsLimits.max_statistical_observations` |

Requests that exceed any ceiling above fail closed with a structured
`ValidationError` (see `enforce_limits`) rather than truncating silently.

## Response payload size

- Dashboard payloads are truncated deterministically to `max_dashboard_points`
  per series (see `app/services/analytics/dashboards/truncation.py`); no
  additional byte-size ceiling is enforced beyond the point-count limits
  above, since point-count ceilings already bound response size for the
  JSON-safe scalar/decimal payload shapes this service returns.

## Runtime and memory targets

- These are **measurement targets**, not admission-control ceilings — they are
  not enforced by `enforce_limits` and are validated by manual/CI performance
  checks against the workload ceilings above, on the CI runner's standard
  hardware profile (no GPU, no dedicated accelerator; commodity CI CPU/RAM).
- `build_analytics_report` at the maximum trade/equity-point ceilings above is
  targeted to complete in a low number of seconds on that profile; a
  regression that pushes this materially higher should be treated as a
  performance defect.
- Statistical validation (bootstrap/permutation/multiple-testing routines in
  `app/services/analytics/statistics/`) at `max_statistical_observations` is
  targeted to complete without exceeding commodity CI memory limits (no
  streaming/chunked fallback is implemented today — oversized requests are
  rejected by `enforce_limits` rather than processed in a degraded mode).

## Statistical resampling limits

- Bootstrap and permutation routines in
  `app/services/analytics/statistics/resampling.py` accept an `iterations`
  parameter; the workload ceiling for total resampled observations is
  `AnalyticsLimits.max_statistical_observations` above.

## Benchmark methodology for these limits

- Ceilings were chosen so that a single request stays within commodity
  CI-runner memory/time budgets while covering realistic strategy backtest
  sizes (multi-year, sub-daily bar counts). They are deliberately generous
  relative to typical single-strategy backtests and are expected to be
  revisited if genuine multi-year tick-level or very-high-frequency workloads
  become a supported use case.

## Change control

Changes to any limit in this table must update `AnalyticsLimits` in
`app/services/analytics/boundaries/limits.py` in the same change, and vice
versa — `tests/unit/app/services/analytics/test_catalogs.py`
(`test_required_analytics_adrs_are_present`) asserts this file exists and
documents the trades limit; keeping both in sync is a review requirement, not
just a test requirement.

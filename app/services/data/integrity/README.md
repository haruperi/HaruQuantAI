# Data Integrity — FEAT-DATA-06

Owns deterministic series inspection, anomaly evidence, policy selection, scoring,
metadata validation, and remediation recommendations.

- Production files: anomalies, metadata, contracts, policy, scoring, and series.
- Requirements: FR-DATA-091–094.
- Usage evidence: `tests/data/usage/07_quality.py`.
- Side effects: none.

`DataQualityReport v2` expresses `quality_score` as a `Decimal` percentage from
`0.00` through `100.00`. The score is
`100 * clamp(1 - sum(severity_weight * affected_count / checked_count), 0, 1)`
and is quantized to two decimal places. Examined data is graded `perfect` (100),
`excellent` (95 through 99.99), `good` (90 through 94.99), `degraded` (80 through
89.99), `poor` (60 through 79.99), or `critical` (below 60). An empty examination
is `not_checked` with score `0.00`.

Operational policy uses `quality_decision`, not the descriptive grade. Blocking
missing/duplicate bars and `poor` or `critical` grades are `rejected`;
`degraded` is `review_required`; otherwise issues or warnings produce
`accepted_with_warnings`, and clean evidence is `accepted`. Unchecked evidence is
`not_evaluated` and fails closed at operational consumers.

For research datasets only, a gap fully covered by a relevant holiday event from
complete persisted Economic Calendar coverage is reported as the non-blocking
`CALENDAR_SUPPORTED_CLOSURE` warning. This qualification retains the event identity,
provider, and classification basis. It does not certify a broker schedule, authorize
trading, excuse an unmatched part of a gap, or alter the blocking status of ordinary
`MISSING_BARS` evidence.

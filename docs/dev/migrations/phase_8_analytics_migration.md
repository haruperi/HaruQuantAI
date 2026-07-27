# Phase 8 Analytics StandardResponse Migration

> **Plan ID:** `ANL-001`
> **Document status:** Approved planning artifact; implementation not authorized
> **Prepared:** 2026-07-27
> **Target domain:** `app/services/analytics`
> **Migration program:** HaruQuantAI standard public-operation responses

## 1. Purpose and Gate

Migrate every qualifying package-root Analytics operation to
`StandardResponse[T]` without changing metric definitions, report content, evidence
models, statistical methods, reproducibility hashes, or serialization output.

The implementation agent must read the repository authorities, Analytics root and
feature READMEs, Utils responses/errors, upstream Trading/Simulator contracts, and
all relevant tests. It must refresh the plan, produce a dry run, and wait for a new
standalone `APPROVED: EXECUTE`.

## 2. Response Contract

The response top level is exactly `status`, `message`, `data`, `error`, and
`metadata`.

- Raw evidence/report/series/hash/string/mapping results go directly in `data`.
- `serialize_report` keeps its exact serialized string as `data`.
- `to_report_json_safe` keeps its exact JSON-safe mapping as `data`.
- `metadata.extensions` contains only existing non-result lineage, warnings, quality,
  truncation, or compatibility evidence that was returned beside the raw result.
- Do not duplicate a report or metric series in extensions.
- Technical failure uses `data=None` and a catalogue-approved error.
- Timing uses the shared monotonic helper.

## 3. Features

1. Contracts and catalogues.
2. Upstream result adapters.
3. Metrics/statistical validation.
4. Reports.
5. Dashboard payloads.

The package root is the stable public port.

## 4. Public Operation Inventory

The baseline contains 28 functions.

### 4.1 Contracts and adapters

- `validate_contract_version`
- `validate_metric_catalog`
- `build_quality_flag`
- `build_warning`
- `to_analytics_error_payload`
- `to_report_json_safe`
- `adapt_trading_result`
- `build_closed_trade_equity_curve`

`to_analytics_error_payload` remains a public conversion operation: a successful
conversion returns its existing payload dictionary directly in `data`. Domain
boundaries should otherwise prefer Utils `exception_response` rather than invoke
this converter as a second envelope.

### 4.2 Metrics

- `align_benchmark_series`
- `calculate_benchmark_evidence`
- `calculate_cost_efficiency_evidence`
- `calculate_distribution_evidence`
- `calculate_drawdown_evidence`
- `calculate_grouped_evidence`
- `calculate_ratio_evidence`
- `calculate_return_evidence`
- `calculate_risk_evidence`
- `calculate_trade_evidence`
- `run_statistical_validation`

Every `MetricEvidence`, section evidence, aligned series, or statistical result
remains intact in `data`.

### 4.3 Reports

- `build_performance_report`
- `build_portfolio_allocation_evidence`
- `build_portfolio_performance_report`
- `build_portfolio_rebalance_measurement`
- `compare_performance_reports`
- `compute_reproducibility_hashes`
- `serialize_report`

### 4.4 Dashboards

- `build_dashboard_payload`
- `truncate_series`

The truncated series itself is the raw result. Truncation flags/counts that were
separate evidence may use extensions.

### 4.5 Exclusions

Pydantic constructors, catalogue constants, properties, private metric helpers, and
feature-internal functions not re-exported at the package root are excluded.

## 5. Error Catalogue

Analytics currently has `AnalyticsError`, `AnalyticsValidationError`, and two
dynamically selected public codes:

- `ANALYTICS_VALIDATION_FAILED`
- `ANALYTICS_EXECUTION_FAILED`

Create an immutable Analytics-owned catalogue using Utils `ErrorDefinition`.
Repository discovery must identify any additional stable codes in reports, adapters,
tests, or README requirements before freezing it. Do not invent fine-grained codes
without an owner-approved requirement.

Mapping:

- `AnalyticsValidationError` to `ANALYTICS_VALIDATION_FAILED`.
- Controlled execution failures to `ANALYTICS_EXECUTION_FAILED`.
- Unexpected exceptions to the approved execution failure without exposing raw
  exception messages.
- Safe bounded diagnostics to `error.details`.
- Caller-provided exception conversion still obeys its `max_detail_bytes` limit.

Preserve existing redaction, truncation, and nonfinite-value rejection.

## 6. Metadata Policy

Common declarations:

- `domain="analytics"`.
- `read_only=True`.
- `writes_file=False`, `modifies_database=False`, `places_trade=False`, and
  `requires_network=False` for current pure operations.
- If refreshed code proves a public serializer writes a file rather than returning
  text, issue a plan delta and declare the side effect accurately.

| Family | Risk | Extensions |
|---|---|---|
| Contract/catalog validation | `none` | Contract compatibility/version evidence |
| Adapters | `low` | Safe upstream schema/status evidence not part of raw result |
| Metrics/statistics | `low` | Warnings, sample/quality flags only when separately returned |
| Reports/comparison/hashes | `low` | Lineage or reproducibility references outside raw report |
| Dashboards/truncation | `low` | Truncation counts/warnings outside raw payload |

Analytics warnings and quality flags that are already fields of a raw report/evidence
model remain in that model, not extensions.

## 7. Dependency and Consumer Coordination

Prerequisites:

- Trading migration for Trading result adaptation.
- Simulation migration may occur after Analytics, so support current Simulator raw
  fixtures during this phase and document the future consumer change.
- Data supplies source evidence but Analytics must not accept a response object as a
  dataset.

`adapt_trading_result` must understand migrated Trading responses:

1. Reject/translate an error response safely.
2. Consume raw Trading data only on success.
3. Read legacy warnings/status/audit evidence from metadata extensions when needed.
4. Never mistake response status for filled/rejected Trading business status.

Downstream consumers include Simulation reporting, Optimization scoring/evidence,
Portfolio performance/measurement, Research analysis, dashboards, and reports.

## 8. Implementation Work Packages

### ANL-WP1 — Characterization

Freeze exact numeric outputs, evidence DTOs, hashes, JSON strings, ordering,
nonfinite behavior, warnings, quality flags, and all 28 public signatures.

### ANL-WP2 — Error and response infrastructure

Add the validated Analytics catalogue and focused response helpers. Add five-field,
timing, redaction, and raw-output tests.

### ANL-WP3 — Contracts and adapters

Migrate validation/build helpers and upstream adapters. Preserve compatibility
matrices and schema-version behavior.

### ANL-WP4 — Metrics

Migrate metric families without changing formulas, rounding, annualization, sample
thresholds, benchmark alignment, bootstrapping, or multiple-comparison policy.

### ANL-WP5 — Reports and dashboards

Migrate builders, comparison, hashes, serialization, dashboard payload, and
truncation. Preserve deterministic ordering and golden fixtures.

### ANL-WP6 — Consumers and docs

Update direct consumers, all five feature registry sections, exact `FR-*` and usage
evidence, cross-domain architecture where changed, and `[Unreleased]`.

If current baseline tests expose missing required `correlation_id` or `created_at`
arguments in existing report consumers, distinguish pre-existing failure from
migration work. Fix only if necessary for an approved migrated consumer; otherwise
issue a plan delta.

## 9. Tests and Validation

Required:

- Exact response shape for all 28 operations.
- Direct raw DTO/string/mapping placement.
- Golden numeric parity and deterministic hashes.
- Error catalogue and bounded conversion.
- Warning/quality/truncation preservation.
- Trading and Simulator fixture compatibility.
- JSON-safe serialization without hidden mutation.
- Performance tests remain within existing ceilings.

Primary suites:

- `tests/analytics/unit/test_errors.py`
- `tests/analytics/unit/test_results_adapter.py`
- All metric unit tests
- `tests/analytics/unit/test_serialization.py`
- `tests/analytics/unit/test_payloads.py`
- `tests/analytics/integration/test_build_performance_report.py`
- `tests/analytics/integration/test_report_serialization.py`
- `tests/analytics/integration/test_upstream_fixture_parity.py`
- `tests/analytics/integration/test_usage_scripts.py`
- All five numbered usage programs

Final commands:

```powershell
uv run ruff check app/services/analytics tests/analytics
uv run ruff format --check app/services/analytics tests/analytics
uv run mypy app/services/analytics tests/analytics
uv run pytest tests/analytics
uv run python tests/analytics/usage/01_contracts.py
uv run python tests/analytics/usage/02_adapters.py
uv run python tests/analytics/usage/03_metrics.py
uv run python tests/analytics/usage/04_reports.py
uv run python tests/analytics/usage/05_dashboards.py
```

## 10. Risks, Exclusions, and Rollback

Risks:

- Wrapping could change object identity, serialization, or hashes.
- Upstream Trading legacy status may be lost.
- Warnings or quality evidence may be duplicated.
- Mechanical edits may change formulas or golden outputs.

Excluded:

- New metrics/reports/dashboards.
- Statistical methodology changes.
- Rebaselining golden fixtures without an approved behavior change.
- AI-tool registration.
- Broad upstream/downstream refactoring.

Rollback affected Analytics source, tests, examples, focused consumer changes, and
active documentation; remove the new catalogue only after restoring all references;
then rerun golden and integration suites.

## 11. Completion Checklist

- [ ] All 28 refreshed operations return `StandardResponse[T]`.
- [ ] Raw results and serialized strings remain exact `data`.
- [ ] Analytics codes use a validated domain catalogue.
- [ ] Metric/report/hash outputs match the pre-migration baseline.
- [ ] Upstream adapters and downstream consumers are coordinated.
- [ ] Metadata accurately declares pure read-only behavior.
- [ ] Exact `FR-*`, paths, and line evidence are current.
- [ ] Full validation passes.

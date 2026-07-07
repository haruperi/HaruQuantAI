# Analytics Catalogs

Traceability anchor: `render_catalog_markdown`.

## Official Analytics Tool Catalog

Official high-level tools are low-risk, read-only analytics evidence builders:

- `build_analytics_report`
- `build_portfolio_analytics_report`
- `evaluate_strategy_quality`
- `compare_analytics_reports`
- `calculate_trade_metrics`
- `calculate_equity_metrics`
- `calculate_drawdown_metrics`
- `calculate_risk_metrics`
- `calculate_benchmark_metrics`
- `calculate_statistical_validation`
- `calculate_prop_firm_compliance`

Success example:

```json
{
  "status": "success",
  "message": "Successfully built analytics report.",
  "data": {"report_status": "completed"},
  "error": null,
  "metadata": {
    "tool_name": "build_analytics_report",
    "tool_category": "analytics",
    "tool_risk_level": "low",
    "request_id": "req_1",
    "reads": true,
    "writes": false,
    "updates": false,
    "deletes": false,
    "trades": false,
    "requires_network": false
  }
}
```

Validation-failure example:

```json
{
  "status": "error",
  "message": "trading_result must be a dictionary.",
  "data": null,
  "error": {"code": "VALIDATION_FAILED", "details": "trading_result must be a dictionary."},
  "metadata": {"tool_name": "build_analytics_report", "tool_risk_level": "low"}
}
```

Low-level metric examples are internal/developer examples unless explicitly
registered in the Official Analytics Tool Catalog as agent/API safe.

## Metric Definition Catalog

The source of truth for formulas, units, inputs, aliases, return scale,
annualization basis, sample convention, minimum sample size, undefined-result
behavior, golden fixtures, R-multiple fallback proxies, decimal precision, and
float64 ratio tolerances is
`app/services/analytics/contracts/metric_catalog.py`.

## Adapter Field Mapping

| Upstream result type | Canonical field mapping |
|---|---|
| BacktestResult | `result_id`, `environment`, `account_base_currency`, `trades`, `equity_curve`, `benchmark`, `lineage` |
| PaperTradingResult | `result_id`, `environment`, `account_base_currency`, `trades`, `equity_curve`, `lineage` |
| LiveTradingResult | `result_id`, `environment`, `account_base_currency`, `trades`, `equity_curve`, `lineage` |
| SimulationJournal | `journal_id` to `result_id`, `fills/trades` to `trades`, snapshots to `equity_curve`, lineage provenance |
| LiveTradeJournal | `journal_id` to `result_id`, `fills/trades` to `trades`, snapshots to `equity_curve`, lineage provenance |

Analytics must not use raw broker SDK payloads, UI DTOs, or conversation memory
as primary metric sources.

## Report Sections

Report section criticality states are `required`, `optional`,
`diagnostic-only`, `disabled`, `skipped`, `failed`, and `degraded`.
Required-section failure returns an error unless diagnostic partial mode is
enabled. Optional-section failure produces skipped or failed metadata without
fabricating missing metrics. Partial reports use `report_status = "partial"`,
include affected section metadata, and are non-promotable analytics evidence.

Partial-report example:

```json
{
  "report_status": "partial",
  "sections": {
    "benchmark_metrics": {
      "status": "skipped",
      "skipped": {"reason": "missing_benchmark_data"}
    }
  },
  "warnings": [{"code": "ANALYTICS_SECTION_SKIPPED"}],
  "quality_flags": [{"code": "WEAK_EVIDENCE_BENCHMARK_MISSING"}]
}
```

## Schema Compatibility

Accepted versions are consumed directly. Deprecated versions are accepted with
warnings. Legacy-adapted versions are normalized before metric calculation.
Rejected versions fail closed with structured validation errors. Unsupported
future versions are rejected unless an explicit compatibility entry exists.

## Dashboard Payload Classes

Required dashboard payloads include summary metric cards, equity curve,
drawdown curve, trade distribution, warnings, quality flags, section status,
and metadata. Optional payloads include benchmark-relative charts, cost
breakdowns, statistical validation charts, and efficiency tables. Future
payloads must be introduced behind versioned schemas.

Dashboard truncation example:

```json
{
  "truncation": {
    "truncated": true,
    "original_point_count": 5000,
    "returned_point_count": 1000,
    "method": "deterministic_even_stride",
    "reason": "max_dashboard_points"
  }
}
```

Usage examples cover success, validation failure, partial report, dashboard
truncation, and request-ID traceability. Workload and performance targets are
approved in `docs/adr/ADR-ANALYTICS-LIMITS.md`.

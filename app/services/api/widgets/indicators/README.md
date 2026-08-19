# Indicator Catalogue and Chart-Series Boundary

Focused workstation API feature. It authenticates read-only requests, resolves
the configured runtime Data source, and delegates calculations through the
Indicators package root. The gateway owns no indicator formula or interpolation.

## Files

- `routes.py`: catalogue, capability, specification, and chart-series routes.
- `schemas.py`: EMA/RSI query types and timestamp-aligned response projection.
- `orchestration.py`: uncached Data acquisition and Indicators delegation.

## Requirements

- `FR-API-128` exposes `GET /api/v1/indicators/{indicator_id}/series` for
  `ema` and `rsi`. Data bars are always requested with `use_cache=False`.
- `period` is bounded to 2–10,000; `source` is one of open/high/low/close; the
  requested bar count uses the API-wide chart limit.
- Responses preserve every owner timestamp. Warm-up values remain null with
  their owner-provided reason, and a wholly unavailable series is labelled
  `insufficient_history` rather than presented as complete.
- The response includes the exact period/source parameters and Indicators-owned
  formula and indicator versions.

## Dependencies

- `app.services.data`: public market-data request and read operations.
- `app.services.indicators`: public EMA, RSI, result-value, and metadata operations.
- API Identity, shared response contracts, runtime-source resolution, and limits.

## Evidence

- `tests/api/unit/test_indicators_routes.py`
- `tests/api/usage/15_indicators.py`
- `app/ui/src/widgets/chart/ChartWidget.test.tsx`

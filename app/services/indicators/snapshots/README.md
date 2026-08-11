# Indicator Snapshots

`FEAT-INDI-06` owns the validated JSON-safe `IndicatorSnapshot` transport.
It carries produced measurement evidence and never classifies risk or authorizes a trade.

## v1 (existing, unchanged)

`indicators.indicator_snapshot.v1` (`build_indicator_snapshot`/`parse_indicator_snapshot`) is
the original minimal envelope. It is still the shape `volume/liquidity_snapshot.py` depends on
and is neither deleted nor mutated by the v2 work below.

## v2 (`Indicators_Formula_Ownership_Specification_v1.0.md` §14)

`indicators.indicator_snapshot.v2` (`build_indicator_snapshot_v2`/`parse_indicator_snapshot_v2`)
adds the spec §14.1 base envelope alongside v1: `snapshot_id`, `indicator_id`,
`indicator_version`, `profile_id`, `profile_version`, `category`, `symbol`, `venue`,
`timeframe`, `as_of`, `available_at`, `source_start`, `source_end`, `source_record_count`,
`source_dataset_id`, `source_dataset_hash`, `values`, `units`, `state`, `completeness`,
`confidence`, `data_health`, `warmup_state`, `parameters`, `component_contributions`,
`warnings`, `invalid_reasons`, `provenance`.

`state` is one of the seven spec §14.3 publication states, evaluated in fixed priority order by
`evaluate_publication_state`: `INVALID_FUTURE_INPUT` → `INCOMPLETE_INPUT` → `STALE_INPUT` →
`MISALIGNED_INPUT` → `WARMING_UP` → `DEPENDENCY_UNAVAILABLE` → `VALID`. A snapshot must never
render an unknown value as zero or as `VALID`.

`build_volatility_snapshot` builds the first spec §14.2 category-specific snapshot,
`VolatilitySnapshot`, atop the shared v2 envelope; its `values` mapping must include `atr`,
`atr_percent`, `realized_volatility`, `volatility_percentile`, `volatility_zscore`, and
`volatility_of_volatility`. Later module phases (trend, structure, liquidity, order_flow,
market_speed, regime, patterns) add their own category-specific snapshot types atop the same
shared envelope without touching this file's v1/v2 base again.

v2 symbols are exported from `app.services.indicators.snapshots` (the subpackage); root-package
export is deferred to a later snapshots rollout phase, matching the migration plan's roadmap.

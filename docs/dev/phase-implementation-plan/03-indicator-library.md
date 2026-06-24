## Phase 3 Indicator Library

### Goal

Implement the Indicator Library requirements under `app/services/indicators/` while preserving the phase module boundaries and governance rules.

Task inventory: 737 checkbox tasks (737 checked, 0 unchecked).

### Dependency Files and Functionality


Required functionality:

- Data gateway is accessible to fetch historical symbol series.
- Dataframe utility operations (alignment, comparison, serialization) exist.
- Centralized exception classes can resolve custom indicator errors.


### Functionality to Implement

Tasks are grouped by domain functionality. Each requirement is now part of its corresponding functional contract.

#### Indicator Library Documentation and Design Standards

- [ ] Write the indicator library design and documentation standards before implementation begins, covering Production Scope Tiers classification, no-lookahead behavior, multi-timeframe alignment, output column naming policy, debug-mode strict typing/validation, golden fixtures/reference approval workflow, the `available_at`/`label_time`/`bar_open_time`/`bar_close_time`/`computed_from_start`/`computed_from_end` contract, custom indicator conformance/promotion review, and mandatory cross-validation against industry-standard libraries.
  - Documentation shall warn against using unshifted current-bar values for bar-open decisions.
  - Promotion of custom indicators to official status shall require documentation, golden fixtures, conformance tests, no-lookahead tests, determinism tests, and benchmark coverage.
  - Documentation shall include the Production Scope Tiers classification for every requirement before implementation begins.
  - Documentation shall describe no-lookahead behavior for indicator-derived signals.
  - Documentation shall describe multi-timeframe indicator alignment.
  - Documentation shall describe output column naming, default source naming, non-default source naming, multi-output naming, custom output names, output column conflict policy, and generated `output_columns`.
  - Documentation shall describe debug-mode strict typing and runtime validation behavior.
  - Documentation shall describe golden fixtures and reference output approval workflow.
  - Documentation shall describe the `available_at` contract, `label_time`, `bar_open_time`, `bar_close_time`, `computed_from_start`, `computed_from_end`, and strategy-facing filtering.
  - Documentation shall describe custom indicator conformance, status values, prohibited operations, dependency declarations, and promotion review.
  - Documentation shall describe mandatory cross-validation against industry-standard libraries, third-party formula convention differences, golden fixture approval, mutation fuzz testing, and survivorship bias testing.
  - Public usage examples shall be executable documentation examples once implementation begins.

#### Package Initialization

- [ ] Define the core `IndicatorProtocol.calculate(data, config, context)` typed input/output contract: `data` as a `pandas.DataFrame` for Core MVP batch execution (UTC-normalized `DatetimeIndex` or `symbol`/UTC-`timestamp` `MultiIndex`, stable lowercase OHLCV columns, ambiguous-duplicate rejection), `IndicatorResult.values` aligned to input keys with generated columns plus availability/quality metadata, and `IndicatorConfig`/`IndicatorContext` typed as dataclasses/`TypedDict`/Pydantic models before Builder handoff.
  - `IndicatorProtocol.calculate(data, config, context)` shall use approved type hints before implementation begins.
  - `data` shall be a `pandas.DataFrame` for Core MVP batch execution unless a formula table explicitly approves an alternate typed input.
  - Core MVP `data` shall contain UTC-normalized timestamp information as either a UTC `DatetimeIndex` for single-symbol input or a `MultiIndex` containing `symbol` and UTC `timestamp` levels for multi-symbol input.
  - Core MVP `data` shall expose required OHLCV columns through stable lowercase column names and shall reject ambiguous duplicate columns.
  - `IndicatorResult.values` shall be a `pandas.DataFrame` aligned to the accepted input timestamp/symbol keys and containing generated indicator columns plus required availability and quality metadata.
  - `IndicatorConfig` and `IndicatorContext` shall be typed as dataclasses, `TypedDict`, Pydantic models, or equivalent approved Python contracts before Builder handoff.
  - Any future array-native input such as `numpy.ndarray` shall be an Optional Extension with explicit schema, shape, dtype, symbol/timestamp alignment, and conversion rules.
  - No file-specific non-functional requirements defined.
- [ ] Define smoothing/seed conventions and numeric edge-case behavior (NaN, infinity, negative zero, overflow, underflow, divide-by-zero, floating-point tolerance) for every smoothed indicator, and write numeric and mutation fuzz tests covering this behavior.
  - Every smoothed indicator shall define smoothing method, alpha convention, and initial seed behavior.
  - Documentation shall describe numeric dtype policy, NaN, infinity, negative zero, overflow, underflow, divide-by-zero, and floating-point tolerance behavior.
  - Numeric tests shall cover dtype preservation, NaN, infinity, negative zero, overflow, underflow, divide-by-zero, absolute tolerance, and relative tolerance.
  - Numeric tests shall verify NaN propagation, infinity rejection in official workflows, division-by-zero unavailable outputs, negative-zero normalization, and overflow/underflow deterministic handling.
  - Property-based mutation fuzz tests shall inject NaN, infinity, extreme outliers, zero volume, flat prices, negative values, malformed timestamps, duplicate timestamps, and random missing intervals.

#### Indicator Library Package Initialization

- [ ] No file-specific functional requirements defined. Foundation properties apply.
- [ ] No file-specific non-functional requirements defined.
- [ ] No file-specific testing requirements defined.

#### Indicator Registry and Registry Validation

- [ ] Implement an indicator registry exposing `register_indicator(...)`, `get_indicator(...)`, `list_indicators(...)`, `validate_indicator(...)`, and `unregister_indicator(...)` (unregistering allowed only outside official production registries), where registered indicators declare id, name, version, parameter/input/output schema, warmup policy, and deterministic behavior, and custom indicators register only through approved extension points without bypassing input validation, no-lookahead metadata, schema validation, or deterministic replay requirements.
  - The module shall provide an indicator registry for approved indicator implementations.
  - Registered indicators shall declare id, name, version, parameter schema, input schema, output schema, warmup policy, and deterministic behavior.
  - Custom indicators shall be registered through approved extension points before use in official workflows.
  - Custom indicator registration shall not bypass input validation, no-lookahead metadata, schema validation, or deterministic replay requirements.
  - The public package shall expose registry operations for `register_indicator(...)`, `get_indicator(...)`, `list_indicators(...)`, `validate_indicator(...)`, and `unregister_indicator(...)` where unregistering is allowed outside official production registries.
  - Convenience functions shall return `IndicatorResult` and shall use the same validation, naming, manifest, cache, availability, and no-lookahead rules as registry-driven execution.
- [ ] Define and document the public API surface and module layout: stable import paths, function/class signatures, parameter/result/error schemas, registry contracts, `typing.Protocol` contracts, schema versions, and a deprecation policy with a machine-readable deprecation phase per indicator/parameter/schema/API, plus separation of core protocols, result types, registry code, built-in implementations, error definitions, and test fixtures.
  - Public APIs shall include stable import paths, function and class signatures, parameter schemas, result schemas, error schemas, and registry contracts.
  - The deprecation phase for each indicator, parameter, schema, or API shall be machine-readable through the registry.
  - Public module layout shall separate core protocols, result types, registry code, built-in indicator implementations, error definitions, and test fixtures.
  - Documentation shall declare the public API surface, stable import paths, `typing.Protocol` contracts, registry contracts, schema versions, and deprecation policy.
  - Documentation shall describe indicator anatomy, required public types, required protocol attributes, required protocol methods, registry operations, built-in convenience functions, result objects, manifests, and state objects.
  - Documentation shall describe the deprecation lifecycle, machine-readable registry phase, changelog entries, migration guide, and `IND_DEPRECATED`.
  - Indicator anatomy, required interfaces, registry operations, built-in convenience functions, and result object methods are documented and tested.
  - The public API contract table shall cover registry operations, built-in convenience functions, result object methods, protocol methods, state serialization functions, and manifest serialization functions.
  - No file-specific non-functional requirements defined.
- [ ] Generate a machine-readable capability matrix from the registry for every official indicator, covering id, version, tier, supported modes (batch, vectorized, incremental, streaming, out-of-core, acceleration, composition, multi-symbol, multi-timeframe), optional dependencies, unsupported-mode error codes, and official-workflow eligibility.
  - The machine-readable capability matrix shall be generated from the registry and shall include indicator id, version, tier, supported modes, optional dependencies, unsupported-mode error codes, and official-workflow eligibility.
  - Every official indicator shall publish a machine-readable capability matrix covering batch, vectorized, incremental, streaming, out-of-core, acceleration, composition, multi-symbol, and multi-timeframe support.
- [ ] Write tests covering registry API operations, built-in convenience function contracts, deprecation lifecycle, capability matrix accuracy, and custom indicator conformance.
  - Registry API tests shall verify `register_indicator`, `get_indicator`, `list_indicators`, `validate_indicator`, and allowed `unregister_indicator` behavior.
  - Built-in convenience function tests shall verify `ema`, `sma`, `adx`, `atr`, `adr`, `rolling_volatility`, `rsi`, and `williams_r` return `IndicatorResult` and follow the same validation, naming, manifest, cache, availability, and no-lookahead rules as registry execution.
  - Deprecation lifecycle tests shall verify deprecation warning phase, deprecation error with opt-in phase, removal phase, registry machine-readable phase, `IND_DEPRECATED`, and migration-guide coverage.
  - Capability-matrix tests shall verify every built-in indicator against its machine-readable capability matrix.
  - Custom indicator conformance suite passes for every registered custom indicator.

#### Indicator Interface Protocols and Type Signatures

- [ ] Define packaging, observability, resource-limit, and SLO foundations for the indicator module: standard Python/`pyproject.toml` packaging metadata, structured logging fields, configurable resource limits, NaN/divide-by-zero numeric policy, and configurable production error-rate/timeout SLO thresholds.
  - No file-specific functional requirements defined. Foundation properties apply.
  - No file-specific non-functional requirements defined.
  - No file-specific testing requirements defined.
  - The module shall be packageable through standard Python packaging metadata.
  - Build-system and project metadata shall be declared in `pyproject.toml`.
  - Logs shall include indicator id, implementation version, parameter hash, input checksum, symbol count, timeframe, and request id when available.
  - Canary execution shall allow a configured subset of actors, workflows, symbols, or requests to receive a new implementation while comparing outputs against the baseline implementation.
  - Distributed tracing, feature-flagged execution, canary routing, SLO alert routing, and rollback metadata shall be classified as Optional Extension unless a later approved decision promotes them.
  - Indicator requests shall support configurable maximum rows, maximum symbols, maximum columns, memory budget, and execution timeout.
  - Resource-limit defaults shall live in an approved configuration schema before Builder handoff and shall be overrideable only through validated configuration.
  - Unless an indicator formula specification explicitly overrides this policy, NaN input values shall propagate to NaN outputs for affected rows or windows and shall be represented as unavailable values with quality metadata.
  - Unless an indicator formula specification explicitly overrides this policy, division by zero shall produce NaN unavailable outputs with deterministic warning metadata rather than silently clipping or filling values.
  - Production non-transient indicator error rate shall target less than 0.1 percent over the configured measurement window, excluding deterministic user input validation failures.
  - Production indicator timeout rate shall target less than 0.05 percent over the configured measurement window.
  - SLO thresholds, measurement windows, included workflows, excluded error categories, and alert routing shall be configurable.
- [ ] Implement the core indicator input/output behavioral contract: decision-input-only scope, required input column/schema declarations, multi-symbol/row-order/alignment guarantees, explicit warmup/unavailable-region exposure, and serialization in the documented precision policy.
  - Indicator outputs shall be treated as decision inputs only; official execution remains owned by `app/services/simulation/`.
  - Indicator implementations shall define required input columns, output column names, parameter schema, warmup length, and missing-data behavior.
  - Indicators shall accept OHLCV inputs with explicit timestamp, symbol, timeframe, and timezone metadata.
  - Indicators shall support multi-symbol input only when output grouping preserves symbol identity.
  - Indicators shall preserve input row order after deterministic timestamp and symbol validation.
  - Indicator outputs shall include timestamp and symbol alignment metadata.
  - Indicator outputs shall expose warmup or unavailable regions explicitly rather than silently filling values.
  - Indicator outputs shall distinguish computed values, warmup nulls, missing-input nulls, and rejected rows.
  - Indicator outputs used by official backtests shall be serializable in the precision policy required by the downstream workflow.
- [ ] Implement default-immutable, non-mutating calculation with an `IndicatorResult.join_to(input_data, mode="copy")` helper, deterministic output-column-collision handling, and vectorized alignment verified by timestamp/symbol keys.
  - Indicator calculation shall not mutate the input dataframe by default.
  - Official workflows shall treat in-place input mutation as prohibited unless an explicitly configured internal optimization proves copy-equivalent output and records the optimization in the manifest.
  - The default batch result shall be an `IndicatorResult` containing an aligned `values` dataframe with timestamp, symbol, generated indicator columns, availability metadata, and quality metadata.
  - The result object shall expose a `join_to(input_data, mode="copy")` helper that returns a copy of the source dataframe with generated indicator columns appended.
  - Output column collisions with existing input columns shall fail with a deterministic error by default.
  - Explicit overwrite, suffix, prefix, or namespace behavior for output column collisions shall require configuration and shall be recorded in the manifest.
  - Joined output shall preserve original input columns, row count, row ordering, timestamp alignment, symbol grouping, and index policy.
  - Warmup and unavailable rows shall remain present in joined output with nullable indicator values and explicit metadata rather than being dropped.
  - Vectorized output alignment shall be verified by timestamp and symbol keys rather than by positional row number alone when the input dataframe has an external index.
- [ ] Enforce determinism and precision parity across batch, chunked, out-of-core, accelerated, and fallback execution paths, with manifests recording checksum/version/timestamp identity and benchmark warmup iterations.
  - The same indicator input data, parameter set, implementation version, and precision policy shall produce the same output.
  - Indicator implementations shall define numeric precision behavior.
  - Indicator result manifests shall include input data checksum, parameter hash, implementation version, output schema version, and calculation timestamp.
  - Chunked indicator output shall match full-run output within the documented precision policy.
  - Performance benchmarks shall define warmup iterations before measurement.
  - Out-of-core outputs shall match in-memory full-run outputs within the documented precision policy.
  - Accelerated and fallback paths shall produce outputs that match within the documented precision policy and shall record backend metadata in the result manifest.
  - Public indicator interfaces shall use `typing.Protocol` or equivalent structural typing contracts so custom indicators can integrate without inheriting from framework base classes.
  - Indicator result objects shall implement rich notebook inspection methods, including `_repr_html_` and `_repr_pretty_`, with summary statistics, warmup visualization, unavailable-region visibility, and manifest summary.
- [ ] Define `IndicatorProtocol` with required attributes (`indicator_id`, `name`, `version`, `formula_version`, `input_schema`, `parameter_schema`, `output_schema`, `warmup_policy`, `capabilities`, `status`) and required methods `validate_parameters`, `required_columns`, `output_columns`, `warmup_requirement`, `validate_input`, `calculate`, `calculate_vectorized`, plus the `IndicatorContext` field set (request id, correlation id, actor, workflow, environment, entitlement/tracing/observability/SLO context).
  - `IndicatorProtocol` shall define required attributes for `indicator_id`, `name`, `version`, `formula_version`, `input_schema`, `parameter_schema`, `output_schema`, `warmup_policy`, `capabilities`, and `status`.
  - `IndicatorProtocol` shall define `validate_parameters(parameters)`.
  - `IndicatorProtocol` shall define `required_columns(parameters)`.
  - `IndicatorProtocol` shall define `output_columns(parameters, source=None, naming_policy=None)`.
  - `IndicatorProtocol` shall define `warmup_requirement(parameters, timeframe, calendar=None)`.
  - `IndicatorProtocol` shall define `validate_input(data, config, context)`.
  - `IndicatorProtocol` shall define `calculate(data, config, context)`.
  - `IndicatorProtocol` shall define `calculate_vectorized(data, config, context)` when the indicator supports vectorized batch execution separately from generic calculation.
  - `IndicatorContext` shall contain request id, correlation id, actor, workflow, environment, entitlement context, tracing context, observability context, and SLO context where applicable.
- [ ] Require a formula specification table for every built-in indicator (defaults, parameter ranges, source/required columns, warmup length, window inclusivity, null/degenerate-window handling, output columns, precision tolerance), with any formula/seed/warmup/tolerance/default-parameter change requiring an implementation-version bump and golden fixture review.
  - Every built-in indicator shall define default parameters, allowed parameter ranges, default source columns, required input columns, warmup length, output columns, null behavior, and degenerate-window behavior.
  - Indicator formulas shall be documented with enough precision that an independent implementation can reproduce the same output.
  - Each official built-in indicator shall include a formula specification table defining indicator id, required columns, default source column, parameters, default parameter values, valid parameter ranges, formula, smoothing convention, seed behavior, warmup length, window inclusivity, null handling, degenerate-window behavior, output columns, and precision tolerance.
  - Any formula, seed, warmup, tolerance, or default-parameter change shall require an implementation version update, golden fixture review, and documented migration or changelog note.
- [ ] Implement no-lookahead availability metadata (`computed_from_start`, `computed_from_end`, `source_timeframe`, `available_at`) including higher-timeframe availability timing, `IND_LOOKAHEAD_RISK` enforcement, and UTC-only internal timezone handling.
  - Indicator output rows shall include `computed_from_start`, `computed_from_end`, and `source_timeframe` metadata where applicable.
  - Higher-timeframe indicator values shall set `available_at` no earlier than the close of the higher-timeframe source bar plus configured data latency.
  - If a strategy-facing consumer attempts to read a value with `available_at > decision_time`, the retrieval shall raise `IND_LOOKAHEAD_RISK` or return a masked/unavailable result according to the configured error mode.
  - Local time or exchange time conversion shall occur only at input, output, display, or external integration boundaries.
  - Historical indicator calculation shall not depend on host timezone database changes after inputs are normalized to UTC.
- [ ] Require indicator inputs to declare data provenance (price adjustment status, price source, venue/exchange/vendor/symbol-normalization/corporate-action versions) in manifests, and reject unknown-adjustment, intra-bar-adjusted, stub-quote/extreme-spread, or inverted-market inputs unless an explicit fallback policy is configured.
  - Indicator inputs shall declare price adjustment status: raw, split-adjusted, dividend-adjusted, total-return-adjusted, back-adjusted, or synthetic.
  - Indicator inputs shall declare price source: trade, bid, ask, mid, mark, settlement, or vendor-derived.
  - Indicator inputs shall declare venue, exchange, data vendor, symbol normalization version, and corporate-action adjustment version when available.
  - Indicator manifests shall include data provenance fields required to reproduce the calculation.
  - Official workflows shall reject inputs with unknown adjustment status unless explicitly configured to allow them.
  - Official workflows shall reject bars affected by intra-bar corporate-action adjustments unless a deterministic intra-bar adjustment policy is configured before calculation.
  - Official workflows shall reject stub quotes or spreads greater than the configured threshold, with a default rejection threshold of 50 percent of mid price, unless an explicit fallback policy is configured.
  - Mid-price indicators shall deterministically reject missing or inverted bid/ask inputs unless configured to fall back to last valid mid, trade price, mark price, or unavailable output.
- [ ] Implement idempotent incremental updates matching batch precision, fail-fast input validation at call time, indicator composition with provenance propagation, and data-quality flag propagation (highest-severity flag, manifest recording, strategy-facing quality metadata).
  - Incremental updates shall be idempotent for the same input bar.
  - Incremental and batch outputs shall match within the documented precision policy.
  - Indicator functions shall validate all inputs at call time before any calculation begins.
  - The module shall support indicator composition where one indicator output serves as another indicator input.
  - Composed indicator chains shall preserve provenance metadata through the chain.
  - Indicator inputs may include per-row data quality flags from the data module.
  - Configured inclusion of flagged rows shall be recorded in the indicator manifest.
  - Indicator output rows derived from flagged inputs shall propagate the highest-severity quality flag present in the source data for that calculation window.
  - Strategy-facing outputs shall expose quality metadata so strategies can require a minimum data quality level for consumption.
- [ ] Define a warmup-data request protocol (symbol, timeframe, lookback, indicator id, parameter set, closed-bar policy) and a higher-timeframe alignment protocol (forward-fill only after bar close plus latency, weekend/holiday gap protection), both validated against the data module contract.
  - The indicator module shall define a protocol to request minimum required warmup data from the data module before calculation.
  - Warmup requests shall include requested symbol, timeframe, and lookback period.
  - Warmup requests shall include indicator id and parameter set to determine exact warmup length.
  - Warmup requests shall declare whether warmup data must be closed-bar only or may include the current incomplete bar.
  - The indicator module shall request warmup data through the data module contract and shall validate that returned warmup data conforms to the same schema and provenance requirements as the primary input before using it.
  - When an indicator is configured with a higher-timeframe source, the module shall request higher-timeframe bars through the data module contract alongside the primary timeframe.
  - Higher-timeframe indicator values may be forward-filled onto the primary timeframe only after the higher-timeframe source bar is fully closed plus configured data latency.
  - The module shall set `available_at` for each primary-timeframe row to the higher-timeframe bar close time plus configured data latency.
  - Weekend and holiday gaps in higher-timeframe data shall not cause forward-fill of stale values across session boundaries unless explicitly configured.
  - Proprietary indicator result manifests shall record non-sensitive access-control decision metadata, including decision id, entitlement policy version, and authorized workflow.
- [ ] Define `IndicatorConfig` to carry symbol metadata, timeframe metadata, output mode, precision policy, timezone metadata, optional microstructure quality policy, data latency configuration, optional out-of-core/acceleration/feature-flag/canary/proprietary-access/warmup-request configuration, resource limits, and optional observability/tracing context.
  - Symbol metadata.
  - Timeframe metadata.
  - Output mode: values-only result, joined copy result, or explicitly configured internal optimization.
  - Precision policy.
  - Timezone metadata with unambiguous timestamp handling.
  - Optional microstructure quality policy containing stub quote, inverted market, missing bid/ask, spread threshold, and mid-price fallback configuration.
  - Data latency configuration for availability-time calculation.
  - Optional out-of-core processing configuration containing memory budget, chunk size, storage backend, and spill directory.
  - Optional acceleration backend configuration containing backend id, feature flag, worker pool, worker count, and fallback policy.
  - Optional feature flag and canary routing configuration for indicator implementation rollout.
  - Optional proprietary indicator access context containing actor, workflow, entitlement, environment, and intended use.
  - Optional warmup data request configuration.
  - Resource limit configuration.
  - Optional observability context containing request id and correlation id.
  - Optional tracing context containing trace id, parent span id, baggage, and sampling decision.
- [ ] Define the `IndicatorResult` output contract to carry the indicator values dataframe, the preserved original input, `available_at`/`label_time`/`bar_open_time`/`bar_close_time`/`computed_from_start`/`computed_from_end` metadata, warmup/missing-data metadata, the result manifest, checksums, dtype metadata, provenance metadata, and optional out-of-core/acceleration/rollout/access-control/quality metadata.
  - Indicator values dataframe containing timestamp, symbol, indicator columns, availability metadata, and quality metadata.
  - Original input dataframe preserved without default mutation.
  - `available_at` timestamp or deterministic availability metadata for every output row.
  - `label_time`, `bar_open_time`, `bar_close_time`, `computed_from_start`, `computed_from_end`, and `source_timeframe` metadata where applicable.
  - Warmup and missing-data metadata.
  - Indicator result manifest.
  - Input checksum.
  - Dtype metadata.
  - Data provenance metadata required to reproduce the calculation.
  - Out-of-core execution metadata when out-of-core processing is enabled.
  - Acceleration backend metadata when an accelerated or fallback backend is used.
  - Feature flag, canary route, baseline implementation, selected implementation, and canary comparison metadata when rollout controls are enabled.
  - Non-sensitive proprietary access-control decision metadata when proprietary indicator execution is requested.
  - Propagated data quality metadata.
- [ ] Implement the standalone machine-readable indicator manifest containing `manifest_version`, `indicator_id`, `indicator_version`, `formula_version`, `output_schema_version`, `parameter_hash`, `input_checksum`/`output_checksum` (with a defined checksum policy), `data_provenance`, `execution_backend`, `rollout`, `access_control`, `timing`, `output_shape`, `environment`, composition lineage, and quality-flag summary.
  - Every indicator result shall include a machine-readable manifest as a standalone serializable object.
  - The manifest shall include `manifest_version`.
  - The manifest shall include `indicator_id`.
  - The manifest shall include `indicator_version`.
  - The manifest shall include `formula_version`.
  - The manifest shall include `output_schema_version`.
  - The manifest shall include `parameter_hash` derived from a canonical parameter representation.
  - The manifest shall include `input_checksum` derived from input data including timestamps, symbols, and OHLCV values in canonical order.
  - The manifest shall include `output_checksum`.
  - The module shall define the exact input and output checksum policy, including included columns, dtype normalization, timestamp normalization, symbol ordering, row ordering, float handling, null representation, precision policy, and excluded metadata.
  - The manifest shall include `data_provenance` with adjustment status, price source, vendor, venue, symbol normalization version, corporate-action version, and continuous contract roll method when applicable.
  - The manifest shall include `execution_backend` with in-memory, out-of-core, accelerated, fallback, parallelism, worker count, and backend version fields where applicable.
  - The manifest shall include `rollout` with feature flag, canary route, selected implementation, baseline implementation, and tolerance status where applicable.
  - The manifest shall include `access_control` with non-sensitive decision metadata for proprietary indicator requests where applicable.
  - The manifest shall include `timing` with calculation start, calculation end, and wall-clock duration.
  - The manifest shall include `output_shape` with row count, symbol count, column list, and dtypes.
  - The manifest shall include `environment` with Python version, key dependency versions, operating system, and optional host identifier for debugging.
  - The manifest shall include composition lineage when the result depends on upstream indicator outputs.
  - The manifest shall include quality-flag policy and propagated quality summary when data quality flags are present.
- [ ] Map deterministic error codes for invalid input schema, unexpected input mutation, insufficient data, lookahead-sensitive access, unconfigured intra-bar adjustment, microstructure rejection, and deprecation-phase violations, supporting `IND_INVALID_CONFIG`, `IND_INVALID_INPUT_SCHEMA`, and `IND_INPUT_MUTATION_DETECTED`.
  - Every invalid input schema shall return a deterministic error code.
  - Unexpected input mutation during official calculation shall return a deterministic error code.
  - Every insufficient-data condition shall return a deterministic error code or explicit unavailable output according to configuration.
  - Lookahead-sensitive indicator access shall provide metadata required for `SIM_LOOKAHEAD_DETECTED`.
  - Intra-bar corporate-action adjustment inputs without a configured deterministic policy shall return a deterministic error code.
  - Stub quotes, inverted markets, missing bid or ask values, and spread-threshold violations shall return deterministic error codes unless an explicit fallback policy is configured.
  - Deprecated indicator, parameter, schema, or API use in the deprecation error phase shall return a deterministic error code unless an explicit opt-in flag is configured.
  - Support indicator codes/constants: `IND_INVALID_CONFIG`, `IND_INVALID_INPUT_SCHEMA`, `IND_INPUT_MUTATION_DETECTED`
- [ ] Write the full test suite for this section: input validation, config-conflict validation, typing.Protocol compatibility, notebook representation, join helper, availability, timezone-database stability, determinism, chunking, out-of-core, acceleration parity, batch/incremental parity, data-quality propagation, manifest completeness, provenance, microstructure, survivorship bias, observability, feature-flag/canary, warmup protocol, proprietary-access secrecy, and property-based formula invariants (SMA/EMA/RSI/ATR).
  - Input validation tests shall cover missing columns, duplicate timestamps, non-monotonic timestamps, invalid OHLC, empty data, insufficient warmup, and invalid parameters.
  - Input validation tests shall cover malformed config payloads and invalid configuration combinations, including valid parameters that are incompatible when combined.
  - Input validation tests shall verify simultaneous conflicting options, such as `values_only=True` with `output_mode="join"`, fail with `IND_INVALID_CONFIG`.
  - Public API tests shall verify `typing.Protocol` compatibility for custom indicators that do not inherit from framework base classes.
  - Notebook representation tests shall verify indicator result `_repr_html_` and `_repr_pretty_` output includes summary statistics, warmup visualization, unavailable-region visibility, and manifest summary without exposing full market data payloads.
  - Join helper tests shall verify `IndicatorResult.join_to(input_data, mode="copy")` appends generated indicator columns while preserving original columns, row count, row order, timestamp alignment, symbol grouping, index policy, warmup rows, and unavailable rows.
  - Availability tests shall verify higher-timeframe values are unavailable until the higher-timeframe source bar is fully closed plus configured latency.
  - Timezone database tests shall verify historical outputs remain stable after UTC-normalized inputs are supplied and that timezone-database-dependent conversions occur only at I/O boundaries.
  - Determinism tests shall verify identical inputs and parameters produce identical outputs and manifests.
  - Chunking tests shall verify chunked output matches full-run output within documented precision policy.
  - Out-of-core tests shall verify datasets exceeding memory budget produce the same output as full in-memory runs within documented precision policy.
  - Out-of-core tests shall verify deterministic rejection for indicators that require full in-memory context and cannot be safely chunked.
  - Acceleration backend tests shall verify feature-flag isolation, fallback behavior, backend metadata, and parity between accelerated and fallback paths within documented precision policy.
  - Batch and incremental tests shall verify incremental output matches batch output within the documented precision policy.
  - Market data quality tests shall verify default exclusion of flagged rows, explicit inclusion configuration, quality-flag propagation, highest-severity quality summarization, and strategy-facing quality metadata.
  - Manifest tests shall verify every required manifest field, nested data provenance, calculation config, timing, output shape, environment, composition lineage, and quality summary.
  - Manifest tests shall verify parameter hash canonicalization and input/output checksum policies are stable and documented.
  - Manifest tests shall verify output contract fields for generated column names, source column, output mode, naming policy, column conflict policy, join mode, input mutation flag, and index alignment policy.
  - Provenance tests shall cover raw, split-adjusted, dividend-adjusted, total-return-adjusted, back-adjusted, synthetic, bid, ask, mid, mark, settlement, vendor-derived, continuous futures, and unknown adjustment status inputs.
  - Microstructure tests shall cover stub quotes, inverted markets, missing bid or ask values, spreads above the configured threshold, and mid-price fallback policies.
  - Survivorship bias tests shall verify indicators do not silently produce misleading signals for delisted, bankrupt, merged, or inactive symbols without data-quality flags and provenance metadata.
  - Observability tests shall verify metrics, logs, traces, canary comparison metadata, and SLO measurement fields include required fields and do not change calculation semantics.
  - Feature flag and canary tests shall verify routed execution, baseline comparison, output delta recording, tolerance status, rollback metadata, and unchanged official outputs when canary route is not selected.
  - Warmup protocol tests shall verify requested symbol, timeframe, lookback, indicator id, parameter set, closed-bar policy, returned provenance, data-module contract integration through a fake data-module provider, and warmup output marking.
  - Proprietary indicator tests shall verify entitlement context and protected-package metadata do not leak secrets into logs, traces, manifests, or error messages.
  - Property-based tests shall cover valid and invalid OHLCV inputs.
  - Property-based tests shall verify SMA over constant price input equals the constant price after warmup.
  - Property-based tests shall verify EMA over constant price input converges deterministically according to its seed policy.
  - Property-based tests shall verify RSI remains within documented bounds for valid inputs.
  - Property-based tests shall verify ATR is non-negative for valid OHLC inputs.
  - Documentation tests shall execute usage examples, invalid-input examples, manifest-inspection examples, multi-symbol examples, multi-timeframe examples, and incremental examples where supported.
- [ ] Write usage examples and documentation covering normal/invalid/missing-column behavior, manifest inspection, availability filtering, multi-symbol/multi-timeframe/incremental behavior, configuration reference per indicator, vectorized/immutability/notebook-representation behavior, acceleration backends, validation timing, manifest structure, data-quality flags, warmup protocol, observability, packaging, and proprietary access control.
  - Usage examples shall include normal output, invalid parameter handling, missing-column handling, manifest inspection, availability filtering, multi-symbol input, multi-timeframe input, and incremental update behavior where supported.
  - Documentation shall include a configuration reference for every supported indicator.
  - Documentation shall include input schema, output schema, parameter schema, warmup policy, and missing-data behavior for every supported indicator.
  - Documentation shall describe vectorized calculation requirements, values-only output, joined-copy output, default input immutability, official in-place mutation restrictions, and internal optimization manifest requirements.
  - Documentation shall describe notebook result representations, including `_repr_html_`, `_repr_pretty_`, summary statistics, warmup visualization, unavailable-region visibility, and manifest summaries.
  - Documentation shall describe optional acceleration backends, feature flags, pure fallback behavior, backend metadata, GIL-release behavior, and parallel symbol execution configuration.
  - Documentation shall describe input validation timing and fail-fast behavior.
  - Documentation shall describe indicator result manifest structure and every required manifest field.
  - Documentation shall describe data quality flags, default exclusion policy, explicit inclusion policy, output quality propagation, and strategy-facing quality metadata.
  - Documentation shall describe warmup data request protocol and warmup output marking.
  - Documentation shall describe observability metrics, log fields, request ids, correlation ids, distributed tracing, OpenTelemetry-compatible propagation, feature flags, canary routing, output delta comparison, and rollback metadata.
  - Documentation shall describe packaging metadata, `pyproject.toml`, dependency categories, `py.typed`, and typed package behavior.
  - Documentation shall describe proprietary indicator access control, entitlement checks, authorized workflows, non-sensitive manifest metadata, source protection, and protected-package determinism.
- [ ] Confirm this subsection's done-criteria: `typing.Protocol` contracts and notebook representations, the `ema`/`join_to` example, `pyproject.toml` metadata, availability-time metadata, acceleration parity, performance benchmark regression gate, manifest structure/output-contract fields, warmup and multi-timeframe protocols, and Official-Backtest-Required behavior are implemented and tested; rich notebook HTML may follow once schemas stabilize.
  - `typing.Protocol` contracts and notebook result representations are implemented and tested.
  - `ema(data, period=10, source="close")` produces `ema_10`, and `IndicatorResult.join_to(data)` appends `ema_10` to a copied dataframe without mutating the input by default.
  - `pyproject.toml` metadata is present and valid.
  - Availability-time metadata is implemented and tested.
  - Acceleration backend parity, feature flag, fallback, and backend metadata tests pass.
  - Performance benchmark metadata and regression gate are implemented.
  - Machine-readable manifest structure is implemented and tested.
  - Manifest output-contract fields are implemented and tested.
  - Warmup data request protocol is documented and tested.
  - Multi-timeframe alignment protocol is documented and tested.
  - Official Backtest Required shall include no-lookahead alignment, reproducible fixtures, manifest/checksum behavior, data-quality propagation, and strategy/simulation integration contracts.
  - Rich notebook HTML representations may be added after stable result and manifest schemas exist.

#### Domain Exception Handling and Error Routing

- [ ] Import and reuse all standard system exceptions and error codes from `app.utils.errors` (custom indicator exceptions inherit from `app.utils.errors.Error`/`HaruQuantError`); define whether deterministic errors are raised as exceptions, returned via `IndicatorResult.errors`, or both, and document the default mode.
  - All standard system exceptions and error codes shall be imported and reused from `app.utils.errors` to prevent duplicate declaration. Custom indicator exceptions must inherit from `app.utils.errors.Error` or `HaruQuantError`.
  - The module shall document whether deterministic errors are raised as exceptions, returned inside `IndicatorResult.errors`, or both, and shall document the default mode.
  - Public contracts shall define whether invalid requests raise exceptions, return `IndicatorResult(errors=...)`, or support both modes, and shall document the default mode.
  - Indicator errors shall be safe, deterministic, and machine-readable.
- [ ] Implement deterministic error/output behavior for invalid input schema, invalid parameters, insufficient data, non-monotonic/duplicate timestamps, impossible OHLCV values, numeric edge cases (division-by-zero, all-null/constant-price/zero-volume/flat-market windows, NaN, infinity, overflow, underflow, negative zero), debug-mode type mismatches, resource-limit overruns, and missing optional dependencies, with `IndicatorResult` exposing `values`, `output_columns`, `manifest`, `availability`, `quality`, `state`, `errors`, `metrics`, and `join_to(...)`.
  - Indicator implementations shall return deterministic errors for invalid input schema, invalid parameter values, insufficient data, non-monotonic timestamps, duplicate timestamps, or impossible OHLCV values.
  - The module shall provide metadata required for downstream layers to raise their own lookahead errors while keeping simulation-layer errors outside indicator ownership.
  - Out-of-core processing shall expose deterministic errors when an indicator requires full in-memory context and cannot be safely chunked.
  - Type mismatch failures in debug mode shall fail fast with deterministic errors before any output, state mutation, cache read, or cache write occurs.
  - `IndicatorResult` shall contain `values`, `output_columns`, `manifest`, `availability`, `quality`, `state`, `errors`, `metrics`, and `join_to(...)`.
  - Division-by-zero, all-null windows, constant-price windows, zero-volume windows, flat-market windows, NaN inputs, infinite values, overflow, underflow, and negative zero shall produce deterministic outputs or deterministic errors.
  - Composition shall reject cycles, missing upstream outputs, incompatible source timeframes, unavailable upstream values, and output column collisions with deterministic errors before calculation.
  - Requests exceeding configured resource limits shall fail with deterministic machine-readable errors.
  - Missing optional acceleration, proprietary, tracing, or audit dependencies shall produce deterministic unsupported-backend or not-configured errors without changing default built-in indicator semantics.
  - Unless an indicator formula specification explicitly overrides this policy, positive and negative infinity inputs shall be rejected with deterministic numeric errors in official workflows before calculation.
  - Overflow and underflow shall return deterministic errors or unavailable outputs according to the indicator formula specification and shall be recorded in result errors or warning metadata.
  - Unsupported modes, unsupported backends, unsupported indicators, unavailable optional dependencies, and unsupported composition requests shall fail before calculation with deterministic errors.
  - No file-specific non-functional requirements defined.
- [ ] Deliver Core MVP deterministic batch calculation for EMA, SMA, ADX, ATR, ADR, rolling volatility, RSI, and Williams %R, including input validation, output naming, no-lookahead availability metadata, manifests, deterministic errors, and golden tests.
  - Core MVP shall include deterministic batch calculation for EMA, SMA, ADX, ATR, ADR, rolling volatility, RSI, and Williams %R; input validation; output naming; no-lookahead availability metadata; manifests; deterministic errors; and golden tests.
- [ ] Map every error condition to a deterministic error code or constant: invalid request/parameters, invalid/conflicting output names/modes/naming policies, unsupported indicator id/timeframe/dtype/incremental-mode, ambiguous/naive timestamps, unknown adjustment status, missing symbol mapping, formula version mismatch, custom-indicator governance rejection, unauthorized proprietary access, and SLO violations — supporting `IND_INVALID_PARAMETER`, `IND_UNSUPPORTED_INDICATOR`, `IND_UNSUPPORTED_TIMEFRAME`, `IND_UNSUPPORTED_DTYPE`, `IND_INVALID_OUTPUT_COLUMN`, `IND_INVALID_OUTPUT_MODE`, `IND_INVALID_TIMEZONE`, `IND_INVALID_OHLC`, `IND_INTRA_BAR_ADJUSTMENT_UNSUPPORTED`, `IND_UNSUPPORTED_OUT_OF_CORE`, `IND_UNSUPPORTED_INCREMENTAL_MODE`, and `IND_INTERNAL_ERROR`. Ensure parameter/schema/data-sufficiency validation runs first and fails fast.
  - Unsupported incremental mode requests shall fail deterministically.
  - Parameter validation, schema validation, and data sufficiency checks shall be performed as the first operation and shall fail fast with deterministic error codes.
  - Calculation mode: batch, incremental, streaming, or explicitly unsupported.
  - Structured error result with deterministic error code on failure.
  - Every invalid indicator request shall return a deterministic error code.
  - Every invalid parameter set shall return a deterministic error code.
  - Invalid output names, invalid output modes, invalid naming policies, and output column collisions shall return deterministic error codes.
  - Unsupported indicator ids shall return a deterministic error code.
  - Unsupported timeframes shall return a deterministic error code.
  - Unsupported dtypes shall return a deterministic error code.
  - Ambiguous, nonexistent, or timezone-naive timestamps shall return deterministic error codes in official workflows.
  - Unknown adjustment status shall return a deterministic error code unless explicitly allowed.
  - Missing or incompatible symbol mapping for symbol changes, mergers, ticker replacements, or vendor remaps shall return a deterministic error code.
  - Formula version mismatches shall return a deterministic error code.
  - Custom indicators rejected by conformance, status, dependency, or governance checks shall return deterministic error codes.
  - Unauthorized proprietary indicator requests shall return deterministic access-control error codes.
  - SLO violations detected during production monitoring shall emit deterministic metric events and shall return deterministic error codes when the request policy requires synchronous enforcement.
  - Support indicator codes/constants: `IND_INVALID_PARAMETER`, `IND_UNSUPPORTED_INDICATOR`, `IND_UNSUPPORTED_TIMEFRAME`, `IND_UNSUPPORTED_DTYPE`, `IND_INVALID_OUTPUT_COLUMN`, `IND_INVALID_OUTPUT_MODE`, `IND_INVALID_TIMEZONE`, `IND_INVALID_OHLC`, `IND_INTRA_BAR_ADJUSTMENT_UNSUPPORTED`, `IND_UNSUPPORTED_OUT_OF_CORE`, `IND_UNSUPPORTED_INCREMENTAL_MODE`, `IND_INTERNAL_ERROR`
- [ ] Enforce the deprecation lifecycle for indicators/parameters/schemas/APIs: warning-with-opt-in error phase lasting at least two minor releases raising `IND_DEPRECATED` by default, and a removal phase confined to major versions returning `IND_UNSUPPORTED_INDICATOR` or the closest deterministic error; require the CI performance benchmark suite to fail builds on unapproved regressions greater than 20 percent.
  - The deprecation error with opt-in phase shall last at least two minor releases, raise `IND_DEPRECATED` by default, and support an explicit opt-in flag to restore behavior with a warning.
  - The removal phase shall occur only in a major version and shall return `IND_UNSUPPORTED_INDICATOR` or the closest deterministic unsupported-API error.
  - The benchmark suite shall fail CI when performance regresses by more than 20 percent without explicit approval.
- [ ] Write tests covering error-mode behavior (exception vs. `IndicatorResult.errors`), output-contract naming/collision errors, simulation-layer lookahead integration, deterministic floating-point handling, composition failure modes, performance-regression gating, custom-indicator import/dependency/side-effect enforcement, out-of-core parity/rejection, and document out-of-core processing (memory budgets, chunk sizes, spill storage) with structured-error usage examples.
  - Error-mode tests shall verify deterministic exception mode and deterministic `IndicatorResult.errors` mode if both are supported.
  - Error-mode tests shall verify that result-error mode does not raise exceptions and instead populates `IndicatorResult.errors` with deterministic codes.
  - Output contract tests shall verify custom output names, invalid output names, output naming policies, output modes, column conflict policies, and deterministic collision errors.
  - Simulation integration tests shall verify simulation-layer lookahead detection uses indicator-provided availability metadata without making the indicator module own simulation errors.
  - Floating-point warning and error handling shall be deterministic within official workflows.
  - Composition tests shall verify cyclic graphs, missing upstream columns, incompatible source timeframes, unavailable upstream values, and output column collisions fail deterministically.
  - Performance benchmark tests shall prove the CI regression gate fails the build when the greater-than-20-percent regression threshold is triggered without explicit approval.
  - Custom indicator tests shall verify import failure, dependency conflict, unsupported Python version, and side-effect enforcement failure handling.
  - Usage examples shall show deterministic structured error behavior rather than relying only on successful calls.
  - Documentation shall describe out-of-core processing, memory budgets, chunk sizes, spill storage, unsupported out-of-core rejection, and in-memory parity requirements.
  - Out-of-core parity and unsupported out-of-core rejection tests pass.

#### Base Mathematical Calculations

- [ ] Implement no-lookahead masking and the `available_at` availability contract: previous-closed-bar-only decisions, deterministic caching by indicator id/parameter hash/input checksum/version/precision policy, the `available_at`/`label_time`/`bar_open_time`/`bar_close_time`/`computed_from_start`/`computed_from_end`/`source_timeframe`/`lookahead_prohibited` field set, bar-open masking via `.shift(1)`-style utilities, current-bar rejection at the first tick of bar `N`, multi-timeframe gating until the higher-timeframe bar closes, and strategy-facing `available_at <= decision_time` filtering.
  - Indicator calculations shall not use current incomplete bar high, low, close, volume, or derived values for previous-closed-bar decisions.
  - Indicator calculations may be cached by indicator id, parameter hash, input data checksum, implementation version, schema version, and precision policy.
  - Indicator-derived trade signals shall obey no-lookahead timing.
  - Indicators used for bar-open strategies shall expose only fully closed-bar values available before the first tick of the next bar.
  - At the first tick of bar `N`, indicator-derived data with timestamp greater than or equal to bar `N` open time shall be masked, dropped, or rejected before strategy access.
  - Multi-timeframe indicator alignment shall not expose higher-timeframe values until the higher-timeframe bar is fully closed.
  - The module shall provide `available_at`, source `bar_close_time`, source `bar_open_time` when available, `computed_from_start`, `computed_from_end`, `source_timeframe`, and a `lookahead_prohibited` flag for downstream lookahead enforcement.
  - Vectorized indicator generation shall provide explicit utilities to shift outputs, such as `.shift(1)`, to align with bar-open execution logic.
  - Every indicator output row shall include or derive a deterministic `available_at` timestamp.
  - `available_at` shall represent the earliest time at which the value may be consumed by a strategy without lookahead.
  - Strategy-facing APIs shall filter by `available_at <= decision_time`, not merely by indicator timestamp.
  - Indicator outputs shall expose `label_time`, `bar_open_time`, `bar_close_time`, and `available_at` when these differ.
  - Late-arriving, corrected, or revised bars shall trigger deterministic recomputation or deterministic rejection.
- [ ] Implement chunked and out-of-core calculation support: window definition over rows/elapsed time/sessions/calendar time, warmup continuity preservation across chunks, bounded-state out-of-core processing within memory budgets, and documented backpressure behavior for chunked/parallel/out-of-core paths.
  - Indicator calculations shall support chunked processing where mathematically valid and shall preserve warmup continuity across chunks.
  - Indicator calculations shall support out-of-core processing for datasets that exceed configured memory budgets when the indicator formula permits bounded-state or chunked computation.
  - Indicator calculations shall define whether windows operate over rows, elapsed time, trading sessions, or calendar time.
  - Chunked, parallel, and out-of-core processing shall define backpressure behavior before implementation.
- [ ] Implement batch/incremental validation ordering and quality-flag handling: full input validation before batch output, state/new-bar validation before incremental state mutation, default exclusion of flagged rows, and documented per-quality-flag calculation effects for interpolated/backfilled/suspect/corrected/synthetic/auction/vendor-specific flags.
  - For batch calculations, full input validation shall complete before any output rows are computed.
  - For incremental calculations, state deserialization validation and new-bar validation shall complete before incremental state is updated.
  - Flagged rows shall be excluded from official calculations by default unless explicitly configured otherwise.
  - Optional incremental state for incremental calculations.
  - Supported quality flags shall include interpolated, backfilled, suspect, corrected, synthetic, auction, and vendor-specific flags when provided by the data module.
  - Indicator implementations shall document how each quality flag affects calculation.
- [ ] Implement observability, tracing, and controlled-rollout support: structured operational metrics, correlation ids, OpenTelemetry-compatible distributed tracing across data-fetch/calculation/strategy/simulation boundaries, and feature-flagged/canary-routed execution with recorded output/performance deltas.
  - Indicator calculations shall emit structured operational metrics where enabled.
  - Indicator execution shall support correlation ids for strategy and simulation workflow tracing.
  - Indicator execution shall support distributed tracing across data fetch, indicator calculation, strategy consumption, and simulation integration boundaries when tracing is enabled.
  - The module shall support OpenTelemetry-compatible trace propagation or an equivalent vendor-neutral tracing contract.
  - Indicator implementations shall support feature-flagged and canary-routed execution for controlled rollout of new implementations.
  - Canary comparison shall record output deltas, tolerance status, performance deltas, and rollback decisions without changing official outputs unless the canary route is explicitly selected.
- [ ] Write input-immutability tests verifying indicator calculations do not mutate the input dataframe by default and raise `IND_INPUT_MUTATION_DETECTED` when official calculation detects unexpected mutation.
- [ ] Document indicator scope and packaging conventions: Python-only implementation target, indicator outputs as decision-support (not execution) artifacts, data normalization/source-readiness ownership by the data module, typed/documented/deterministic/testable code, separated runtime/acceleration/dev/test dependencies, `py.typed` distribution, and maintained public type information for downstream type checkers.
  - Indicator implementations target Python.
  - Indicator outputs are decision support artifacts, not official execution artifacts.
  - Data normalization and source-readiness rules are owned by the data module.
  - Indicator code shall be typed, documented, deterministic, and testable.
  - Runtime dependencies, optional acceleration dependencies, development dependencies, and test dependencies shall be separated.
  - Distributed typed packages shall include `py.typed` when public inline type annotations are intended for downstream type checking.
  - Public type information shall be maintained for downstream users when the package is published as typed.
- [ ] Enforce log redaction by default so logs do not include full market data payloads.
- [ ] Define and document default resource limits and partial-output policy: maximum rows/symbols/columns, memory budget, chunk size, and timeout (proposed Core MVP defaults `default_max_rows=10_000_000`, `default_max_symbols=1_000`, `default_max_columns=256`, `default_memory_budget_bytes=4_294_967_296`, `default_chunk_rows=1_000_000`, `default_timeout_seconds=60`, pending approval), and require partial outputs to be explicitly marked rather than returned as successful official results.
  - The module shall define default resource limits for maximum rows, symbols, columns, memory budget, chunk size, and timeout before production use.
  - Proposed Core MVP default resource limits are `default_max_rows=10_000_000`, `default_max_symbols=1_000`, `default_max_columns=256`, `default_memory_budget_bytes=4_294_967_296`, `default_chunk_rows=1_000_000`, and `default_timeout_seconds=60`, pending owner/architect approval.
  - Partial outputs shall not be returned as successful official results unless explicitly marked partial.
- [ ] Define dependency, packaging, and supply-chain policy: isolate optional acceleration dependencies behind extras/feature flags, maintain a lockfile or equivalent reproducibility mechanism, support SBOM generation, require cryptographic release signing (Sigstore/PEP 740 or equivalent), and require license/vulnerability compatibility with documented waivers.
  - Optional acceleration dependencies shall be isolated behind extras or feature flags.
  - The project shall maintain a lockfile or equivalent reproducible dependency mechanism for official workflows.
  - The project shall generate or support generating a software bill of materials for production releases.
  - Distributed Python wheels, source distributions, and production packages shall be cryptographically signed by the approved CI/CD release pipeline using Sigstore, PEP 740-compatible attestations, or an equivalent approved signing mechanism.
  - Dependency licenses shall be compatible with the intended deployment and distribution model.
  - Known vulnerable dependencies shall not be allowed in production releases unless explicitly waived.
- [ ] Define numeric representation, tolerance, and SLO conventions: declared supported dtypes (`float64`, nullable floats, decimals, fixed-point), negative-zero normalization, documented absolute/relative test tolerances, documented thread-safety guarantees, and SLO measurement emitted through observability metrics and production readiness reports.
  - Official indicator workflows shall declare supported numeric dtypes.
  - Indicator implementations shall define whether outputs use `float64`, nullable floats, decimals, fixed-point integers, or another representation.
  - Negative zero shall be normalized to zero for hashing, checksums, output comparison, and display.
  - Indicator comparisons in tests shall use documented absolute and relative tolerances.
  - Indicator implementations shall document thread-safety guarantees.
  - SLO measurements shall be emitted through observability metrics and summarized in production readiness reports.
- [ ] Establish the indicator module's location and ownership boundary: live under `app/services/indicators/` (DEC-029/DONE-037), provide reusable calculation primitives for strategy/research/simulation, and explicitly exclude final position sizing, margin acceptance, risk approval, and order matching, exposing only typed deterministic functions/classes for strategy and simulation consumption.
  - The indicator module shall live under `app/services/indicators/` (relocated and approved per DEC-029/DONE-037).
  - The indicator module shall provide reusable indicator calculation primitives for strategy, research, and simulation workflows.
  - The indicator module shall not determine final official position size, margin acceptance, risk approval, or order matching.
  - The indicator module shall expose typed, deterministic functions or classes that can be consumed by strategies and simulation orchestration.
- [ ] Implement parameter validation, vectorized batch calculation, and output-shaping behavior: validate parameter ranges before calculation, accept normalized historical data from the data module contract, calculate via vectorized dataframe/array/columnar operations where the formula permits, expose `output_columns` and `values_only` output modes, and use stable lowercase snake_case output naming derived from indicator id/source column/period/named parameters in canonical order.
  - Indicator implementations shall validate parameter ranges before calculation.
  - Indicators shall accept normalized historical market data from the data module contract.
  - Batch indicators shall calculate outputs through vectorized dataframe, array, or columnar operations where the formula permits vectorized calculation.
  - The result object shall expose generated column names through `output_columns`.
  - The result object shall expose `values_only` output for workflows that require indicator columns without the original OHLCV columns.
  - Output column naming shall use stable lowercase snake_case names derived from indicator id, source column, period, and named parameters in canonical parameter order.
- [ ] Define numeric tolerance, reproducibility, and performance-benchmark methodology: IEEE 754 `float64` outputs with default `1e-9` relative / `1e-12` absolute tolerance (overridable per approved formula table), floating-point allowance for non-official research indicators, replay-reproducible official simulation outputs, documented hardware profile and wall-clock min/median/p99 benchmark methodology tracked per release, isolated optional acceleration backends (Numba/CuPy/SIMD) with mandatory pure-Python/NumPy/pandas fallbacks of identical public API behavior, and documented GIL/multiprocessing/threading behavior per backend.
  - Core MVP numeric behavior shall use IEEE 754 `float64` outputs with default relative tolerance `1e-9` and default absolute tolerance `1e-12` for golden and cross-validation tests unless an approved formula table overrides the tolerance.
  - Floating-point arithmetic may be used for research indicators when outputs are not directly used for official accounting or official fill prices.
  - Indicator outputs that feed official simulation decisions shall be reproducible across replay runs.
  - Performance benchmarks shall specify hardware profile, including CPU model, core count, RAM, and disk type when caching is disk-backed.
  - Performance benchmarks shall define measurement methodology, including wall-clock timing and min, median, and p99 over a documented run count.
  - Per-indicator benchmarks shall be maintained and tracked over releases.
  - Optional hardware acceleration backends, including Numba, CuPy, SIMD, or equivalent backends, shall be isolated behind explicit feature flags or extras.
  - Every accelerated indicator path shall provide a pure NumPy, pandas, or standard Python fallback with identical public API behavior.
  - The module shall document whether each accelerated or parallel backend releases the GIL, uses multiprocessing, or requires single-threaded execution.
- [ ] Define public API surface and deprecation lifecycle: explicit declaration of the public surface, clear marking of private internal modules excluded from strategy/simulation consumption, a documented indicator anatomy for every official/custom indicator with no required private-helper integration, and a deprecation warning phase of at least two minor releases with structured warnings and changelog/migration documentation.
  - The indicator module shall explicitly declare its public API surface.
  - Internal modules shall be clearly marked as private and shall not be consumed directly by strategy or simulation code.
  - The deprecation warning phase shall last at least two minor releases, emit structured warnings on every use, and continue full support.
  - Deprecation timelines shall be documented in the changelog and migration guide.
  - The indicator module shall expose a documented anatomy for every official and custom indicator.
  - Private helper modules shall not be required for downstream strategy, simulation, notebook, or custom-indicator integration.
- [ ] Require formula specification tables before implementation: a concrete formula specification per built-in indicator, explicit rolling-window inclusivity (left-closed/right-closed/current-row), and a halt on Core MVP coding for `app/services/indicators/` until formula tables using the minimum template are approved.
  - Every built-in indicator shall provide a concrete formula specification before implementation begins.
  - Every rolling-window indicator shall define whether windows are left-closed, right-closed, and whether the current row is included.
  - Formula tables must be approved before any Core MVP implementation begins; their absence shall halt coding for `app/services/indicators/`.
  - Formula specification tables shall use this minimum template:
- [ ] Define calendar, session, and timezone handling: explicit trading calendars for session-aware indicators, documented weekend/holiday/half-day/DST/missing-open-close behavior, overnight-gap policy for multi-session windows, separate or continuous treatment of pre-market/regular/post-market/24-7 data, explicit session resets where required, rejection of timezone-naive/ambiguous/nonexistent timestamps, UTC-aware (or documented naive-UTC) internal processing, and declared roll/adjustment method for continuous futures or synthetic instruments.
  - Session-aware indicators shall use an explicit trading calendar.
  - The module shall define behavior for weekends, exchange holidays, half-days, daylight-saving transitions, and missing session opens or closes.
  - Multi-session rolling windows shall define whether overnight gaps are included.
  - Indicators shall define whether pre-market, regular-session, post-market, and 24/7 market data are treated separately or continuously.
  - Session resets shall be explicit for indicators that require them.
  - Official workflows shall reject timezone-naive, ambiguous, or nonexistent local timestamps.
  - Internal processing shall use UTC-aware timestamps or documented naive UTC representations only.
  - Continuous futures or synthetic instruments shall declare roll method and adjustment method.
- [ ] Define bid/ask/mid-price indicator edge-case behavior for stub quotes, inverted markets, missing bid/ask values, and extreme spreads.
- [ ] Implement custom indicator governance: a pre-registration conformance test suite, declared status (official/experimental/deprecated/research-only) with experimental indicators excluded from official simulation unless explicitly allowed, prohibition of network I/O/broker calls/filesystem writes/account mutations/nondeterministic randomness during calculation, declared external dependencies, a documented enforcement mechanism (static analysis, sandbox execution, runtime guards, process isolation, conformance tests, policy review, or combination) for prohibited-operation checks, rejection when those checks cannot run or be trusted, and mandatory review before promotion to official status.
  - Custom indicators shall pass a conformance test suite before registration in official workflows.
  - Custom indicators shall declare status: official, experimental, deprecated, or research-only.
  - Experimental indicators shall not be used in official simulation workflows unless explicitly allowed.
  - Custom indicators shall not perform network I/O, broker calls, filesystem writes, account mutations, or nondeterministic random operations during calculation.
  - Custom indicators shall declare all external dependencies.
  - Custom indicator conformance shall verify prohibited side effects through a documented enforcement mechanism before registration in official workflows.
  - Official workflows shall reject custom indicators whose prohibited-operation checks cannot be executed, cannot be trusted, or return an inconclusive result.
  - Custom indicator enforcement shall document whether validation uses static analysis, sandbox execution, runtime guards, process isolation, conformance tests, policy review, or a combination of these mechanisms.
  - Custom indicators shall be reviewed before promotion to official status.
- [ ] Implement indicator composition validation: accept only validated acyclic indicator graphs when composition is enabled, preserve `available_at` correctly through composed chains, and prevent any composed indicator from consuming a value before it is available.
  - When composition is enabled, the module shall accept only validated acyclic indicator graphs.
  - Composed indicator chains shall preserve `available_at` correctly.
  - No composed indicator shall consume a value before it is available.
- [ ] Define the indicator module's market-data ownership boundary and higher-timeframe alignment: the module shall not own market-data fetching, source readiness, vendor adapters, or normalization; higher-timeframe bars shall be validated before calculation, aligned via matching left-closed/right-closed boundaries, and the module shall support multiple higher-timeframe sources simultaneously with independent availability timestamps.
  - The indicator module shall not directly own market-data fetching, source readiness, vendor adapters, or normalization logic.
  - Higher-timeframe bars shall be validated before calculation and shall not make the indicator module responsible for market-data fetching, provider readiness, or normalization.
  - Higher-timeframe bars shall be aligned using left-closed, right-closed boundaries matching the primary timeframe bar edges.
  - The module shall support multiple higher-timeframe sources simultaneously with independent availability timestamps.
- [ ] Require an access-control decision and approved protected packaging mechanism before executing proprietary or licensed indicator implementations.
  - Proprietary or licensed indicator implementations shall require an access-control decision before execution.
  - Proprietary indicator execution shall be supported only through approved protected packaging mechanisms.
- [ ] Define the indicator input/output/manifest record fields for Base Mathematical Calculations: normalized OHLCV (and optional tick/lower-timeframe) input data, indicator id/parameter set/source column selection, output naming and conflict policy, session/calendar policy, price adjustment status/source and optional intra-bar adjustment policy, optional composition graph and per-row quality flags, timestamp/symbol-aligned result data, generated column names, optional joined dataframe copy, parameter hash and output checksum, composition lineage, and optional observability metrics/trace ids when enabled.
  - Normalized OHLCV market data.
  - Optional normalized tick or lower-timeframe data when an indicator explicitly requires it.
  - Indicator id.
  - Indicator parameter set.
  - Source column selection for indicators that operate on a specific price or value column.
  - Output naming policy.
  - Output column conflict policy.
  - Trading calendar or session policy when an indicator is session-aware.
  - Price adjustment status.
  - Price source.
  - Optional intra-bar corporate-action adjustment policy.
  - Optional indicator composition graph.
  - Optional per-row data quality flags from the data module.
  - Indicator result data aligned to timestamp and symbol.
  - Generated indicator column names.
  - Joined dataframe copy when join output mode is requested.
  - Parameter hash.
  - Output checksum.
  - Indicator composition lineage where applicable.
  - Observability metrics when enabled.
  - Trace ids and span ids when distributed tracing is enabled.
  - SLO measurement fields when SLO tracking is enabled.
- [ ] Support the deterministic Base Mathematical Calculations error code set: `IND_MISSING_REQUIRED_COLUMN`, `IND_OUTPUT_COLUMN_CONFLICT`, `IND_DUPLICATE_TIMESTAMP`, `IND_NON_MONOTONIC_TIME`, `IND_AMBIGUOUS_TIMESTAMP`, `IND_INSUFFICIENT_DATA`, `IND_LOOKAHEAD_RISK`, `IND_UNKNOWN_ADJUSTMENT_STATUS`, `IND_SYMBOL_MAPPING_REQUIRED`, `IND_STUB_QUOTE_REJECTED`, `IND_INVERTED_MARKET`, `IND_SPREAD_THRESHOLD_EXCEEDED`, `IND_DEPRECATED`, `IND_ACCELERATION_BACKEND_UNAVAILABLE`, `IND_RESOURCE_LIMIT_EXCEEDED`, `IND_TIMEOUT`, `IND_CANCELLED`, `IND_PARTIAL_RESULT`, `IND_CUSTOM_INDICATOR_REJECTED`, `IND_ACCESS_DENIED`, `IND_PROPRIETARY_UNAUTHORIZED`, and `IND_SLO_VIOLATION`.
- [ ] Assign a stable requirement id to every functional and non-functional requirement in this section before implementation begins.
- [ ] Write the Base Mathematical Calculations test suite covering default-parameter values/ranges, public API contract conformance, vectorized batch output, no-lookahead masking and availability filtering, golden-output change approval, calendar/session edge cases, resource limits, multi-timeframe alignment, custom indicator conformance, property-based output/row invariants, and strategy/simulation integration.
  - Default-parameter tests shall verify default parameter values and valid parameter ranges for every built-in indicator.
  - Public API contract tests shall verify every public callable against the documented API contract table.
  - Vectorized output tests shall verify batch indicators use vectorized dataframe, array, or columnar operations where the formula permits vectorized calculation.
  - No-lookahead tests shall cover previous-closed-bar availability, current-bar masking, multi-timeframe alignment, and vectorized signal shifting.
  - Availability tests shall verify strategy-facing APIs filter by `available_at <= decision_time`.
  - Changes to golden outputs shall require explicit approval and changelog entry.
  - Calendar and session tests shall cover weekends, exchange holidays, half-days, daylight-saving transitions, session gaps, missing opens, missing closes, pre-market, regular-session, post-market, and 24/7 market data.
  - Resource-limit tests shall cover maximum rows, symbols, columns, memory budget, execution timeout, cancellation, and partial-result handling.
  - Multi-timeframe alignment tests shall verify higher-timeframe data requests through a fake data-module contract, forward-fill only after availability, independent availability timestamps for multiple higher-timeframe sources, boundary alignment, and stale gap prevention across weekends and holidays.
  - Custom indicator conformance tests shall verify status, dependency declarations, no network I/O, no broker calls, no filesystem writes, no account mutations, no nondeterministic random operations, and promotion requirements.
  - Custom indicator conformance tests shall verify rejection when prohibited-operation enforcement cannot run, cannot be trusted, or returns an inconclusive result.
  - Property-based tests shall verify indicator output row count and symbol grouping match the documented output policy.
  - Property-based tests shall verify adding future rows does not change previously available closed-bar outputs except when explicitly documented for revision-aware modes.
  - Strategy integration tests shall verify indicator outputs can feed trade-signal generation without exposing prohibited current-bar data.
  - Simulation integration tests shall verify indicator-derived signals are converted to trade intents before tick execution.
- [ ] Confirm Base Mathematical Calculations done-criteria: documented public API surface, approved Production Scope Tiers for every requirement, complete public API contract tables, implemented and tested vectorized/naming/values-only/joined-copy/conflict output behavior, `py.typed` distribution where applicable, formula specifications and golden fixtures for every official indicator, tested calendar/session behavior, passing composition tests, implemented and tested quality-flag handling, implemented deprecation lifecycle and `IND_DEPRECATED` behavior, passing proprietary access-control and protected-source determinism tests, passing property-based/invariant/mutation-fuzz/survivorship-bias tests, passing tracing/feature-flag/canary/SLO tests, present dependency lockfile, passing license/vulnerability checks or waivers, and supported SBOM generation.
  - Public API surface is documented.
  - Production Scope Tiers are assigned and approved for every requirement.
  - Public API contract tables are complete for every public callable.
  - Vectorized dataframe output, deterministic indicator column naming, values-only output, joined-copy output, and output column conflict behavior are implemented and tested.
  - Typed distribution includes `py.typed` when public inline type annotations are exported.
  - Formula specifications exist for every official indicator.
  - Golden fixtures exist for every official indicator.
  - Calendar and session behavior is documented and tested.
  - Indicator composition tests pass where composition is supported.
  - Data-quality flag handling is implemented and tested.
  - Deprecation lifecycle and `IND_DEPRECATED` behavior are implemented.
  - Proprietary indicator access control and protected-source determinism tests pass for every proprietary indicator.
  - Property-based and invariant tests pass.
  - Mutation fuzz and survivorship bias tests pass.
  - Distributed tracing, feature flag, canary routing, and SLO measurement tests pass.
  - Dependency lockfile or equivalent reproducibility mechanism is present for official workflows.
  - Dependency license and vulnerability checks pass or have explicit waivers.
  - Software bill of materials generation is supported for production releases.
- [ ] Classify Base Mathematical Calculations scope into Core MVP, Optional Extension, and Future Improvement tiers: halt Core MVP coding until `IND-PREQ-001`–`IND-PREQ-006` are resolved or deferred; place streaming, out-of-core processing, acceleration backends, proprietary execution, distributed tracing, SLO alert routing, and canary routing in Optional Extension unless promoted; place not-yet-required capabilities in Future Improvement; ensure Core MVP is implementable without optional acceleration/proprietary/out-of-core/tracing/SLO/signing infrastructure; classify every public callable as stable/experimental/internal/optional/future before implementation; and allow GPU/SIMD acceleration as an Optional Extension only after Core MVP formula and fixture behavior is stable.
  - Core MVP coding shall halt until `IND-PREQ-001`, `IND-PREQ-002`, `IND-PREQ-003`, `IND-PREQ-004`, `IND-PREQ-005`, and `IND-PREQ-006` are resolved or explicitly deferred.
  - Optional Extension shall include streaming, out-of-core processing, acceleration backends, proprietary indicator execution, distributed tracing, SLO alert routing, and canary routing unless a later approved decision promotes any item.
  - Future Improvement shall include capabilities that are useful but not required for the current approved implementation phase.
  - Core MVP shall be implementable without optional acceleration backends, proprietary indicator controls, out-of-core execution, distributed tracing, SLO enforcement, or release-signing infrastructure.
  - Every public callable shall be classified as stable, experimental, internal, optional, or future before implementation begins.
  - GPU/SIMD acceleration may be added as an Optional Extension after Core MVP formula and fixture behavior is stable.

#### Batch Indicator Calculations Package

- [ ] No file-specific functional requirements defined. Foundation properties apply.
- [ ] No file-specific non-functional requirements defined.
- [ ] No file-specific testing requirements defined.

#### Batch Trend Indicators (Moving Averages, MACD, etc.)

- [ ] Implement EMA, SMA, and ADX trend indicators with documented examples covering EMA/SMA trend signals, ATR volatility sizing inputs, RSI momentum signals, vectorized dataframe output, joined indicator columns, and multi-timeframe alignment.
  - The module shall support trend indicators including EMA, SMA, and ADX.
  - Documentation shall include examples for EMA/SMA trend signals, ATR volatility sizing inputs, RSI momentum signals, vectorized dataframe output, joined indicator columns, and multi-timeframe alignment.
  - No file-specific non-functional requirements defined.
  - No file-specific testing requirements defined.
- [ ] Keep indicator APIs separate from strategy/simulation execution services, reusable across notebook/CLI/agentic/simulation workflows without semantic changes, with observability remaining optional and never altering calculation semantics.
  - Indicator APIs shall remain separate from strategy execution and simulation execution services.
  - Indicator implementations shall be reusable by notebook, CLI, agentic, and simulation workflows without changing semantics.
  - Observability shall be optional and shall not change calculation semantics.
- [ ] Implement deterministic output column naming for trend indicators: default-source naming (`ema_10`), non-default-source naming (`ema_open_10`), deterministic multi-output component naming (`adx_14`, `plus_di_14`, `minus_di_14`), and custom names accepted only after schema validation, collision checks, and naming-policy checks.
  - A call equivalent to `ema(data, period=10, source="close")` shall generate an indicator column named `ema_10` when `close` is the default source.
  - When the source column is not the default source or when naming ambiguity exists, output column names shall include the source column, such as `ema_open_10` or `ema_close_10`.
  - Multi-output indicators shall expose deterministic output column names for each component, such as `adx_14`, `plus_di_14`, and `minus_di_14`.
  - Custom output column names shall be accepted only when they pass schema validation, collision checks, and deterministic naming policy checks.
- [ ] Implement API/schema versioning and deprecation lifecycle: semantic-versioned public API changes, major-version bump or migration path for backward-incompatible changes, deterministic deprecation warnings with a documented compatibility window, independently versioned result schemas, debug-mode strict typing/runtime validation before calculation, and a three-phase deprecation lifecycle for indicators/parameters/schemas/APIs. Track this via the `IND_FORMULA_VERSION_MISMATCH` error code and an explicit output schema version field.
  - Public API changes shall follow semantic versioning.
  - Backward-incompatible public API, schema, formula, or behavior changes shall require a major version bump or documented migration path.
  - Deprecated APIs, indicators, parameters, or schemas shall emit deterministic deprecation warnings and remain supported for a documented compatibility window.
  - Indicator result schema versions shall be independently versioned from implementation versions.
  - Debug-mode APIs shall enforce strict typing and runtime validation before calculation begins, using validated schemas or equivalent runtime guards.
  - Deprecated indicators, parameters, schemas, or APIs shall follow a three-phase lifecycle.
  - Output schema version.
  - `IND_FORMULA_VERSION_MISMATCH`
- [ ] Require every trend indicator to define its exact mathematical formula with the HaruQuant formula specification as the source of truth over third-party library conventions, and require an explicit symbol mapping contract for symbol changes, mergers, ticker replacements, and vendor remaps.
  - Every indicator shall define its exact mathematical formula.
  - The HaruQuant formula specification shall remain the source of truth when third-party library conventions differ.
  - Symbol changes, mergers, ticker replacements, and vendor remaps shall use an explicit symbol mapping contract.
- [ ] Write trend indicator tests covering deterministic output naming (default/non-default source, multi-output components), cross-library validation of EMA/SMA/RSI/ATR/ADX against at least two industry-standard libraries (e.g. TA-Lib, pandas-ta, tulipy) on fixed golden fixtures, and property-based bounds checks for Williams %R.
  - Vectorized output tests shall verify `ema(data, period=10, source="close")` produces `ema_10` when `close` is the default source.
  - Vectorized output tests shall verify non-default source naming such as `ema_open_10` and deterministic multi-output names such as `adx_14`, `plus_di_14`, and `minus_di_14`.
  - EMA, SMA, RSI, ATR, and ADX outputs shall be cross-validated against at least two industry-standard libraries, including TA-Lib and pandas-ta, tulipy, or equivalent libraries, on fixed golden fixtures.
  - Property-based tests shall verify Williams %R remains within documented bounds for valid non-degenerate windows.
  - Cross-library validation passes for EMA, SMA, RSI, ATR, and ADX against at least two industry-standard libraries.
- [ ] Write and maintain executable trend-indicator usage examples and documentation covering API usage (`ema(...)` + `result.join_to(data)`), versioning/migration policy, exact formulas/smoothing/alpha/seed/rolling-window/edge-case behavior, RSI/ATR/ADX smoothing conventions, calendar/session semantics, corporate-action/symbol-mapping/stub-quote/inverted-market/spread/mid-price behavior, and multi-timeframe alignment/boundary/availability semantics.
  - Usage examples shall remain executable documentation examples once implementation begins.
  - Documentation shall include API examples showing `ema(data, period=10, source="close")` returning an `IndicatorResult` with `ema_10` and `result.join_to(data)` returning a copied dataframe with `ema_10` appended.
  - Documentation shall describe semantic versioning policy and migration requirements for backward-incompatible changes.
  - Documentation shall include exact mathematical formula, smoothing convention, alpha convention, seed behavior, rolling-window inclusivity, and edge-case behavior for every supported indicator.
  - Documentation shall describe RSI, ATR, and ADX smoothing conventions.
  - Documentation shall describe calendar, session, weekend, holiday, half-day, daylight-saving, missing-session, pre-market, regular-session, post-market, and 24/7 market semantics.
  - Documentation shall describe intra-bar corporate-action adjustment rejection, deterministic intra-bar adjustment policies, symbol mapping continuity, mergers, ticker replacements, vendor remaps, stub quote handling, inverted market handling, spread thresholds, and mid-price fallback behavior.
  - Documentation shall describe detailed multi-timeframe alignment, boundary semantics, independent availability timestamps, and stale gap prevention.
- [ ] Allow proprietary source protection to be added through approved packaging/security controls without changing public indicator semantics.

#### Batch Volatility Indicators (ATR, Bollinger Bands, etc.)

- [ ] Implement ATR, ADR, and rolling volatility with typed convenience-function wrappers for all official built-ins (`ema`, `sma`, `adx`, `atr`, `adr`, `rolling_volatility`, `rsi`, `williams_r`), defining rolling volatility's return type, log/simple-return behavior, sample/population standard deviation, degrees of freedom, and annualization factor, and defining ADR's range convention (high-low, close-to-close, session, calendar-day, or trading-day range).
  - The module shall support volatility indicators including ATR, ADR, and rolling volatility.
  - Official indicator convenience functions shall expose typed wrappers for supported built-ins, including `ema(...)`, `sma(...)`, `adx(...)`, `atr(...)`, `adr(...)`, `rolling_volatility(...)`, `rsi(...)`, and `williams_r(...)`.
  - Rolling volatility shall define return type, log-return versus simple-return behavior, sample versus population standard deviation, degrees of freedom, and annualization factor.
  - ADR shall define whether it uses high-low range, close-to-close range, session range, calendar-day range, or trading-day range.
- [ ] Complete and approve formula specification tables for EMA, SMA, ADX, ATR, ADR, rolling volatility, RSI, and Williams %R before implementation begins.
  - Formula specification tables shall be completed for EMA, SMA, ADX, ATR, ADR, rolling volatility, RSI, and Williams %R before implementation begins.
  - No file-specific non-functional requirements defined.
- [ ] Write the volatility-indicator test suite: coverage for EMA/SMA/ADX/ATR/ADR/rolling volatility/RSI/Williams %R; golden tests for exact formula conventions, seed behavior, warmup length, rolling-window inclusivity, null handling, and degenerate-window behavior; golden fixtures spanning normal data, flat markets, gaps, missing bars, duplicated timestamps, extreme volatility, zero volume, all-null windows, and insufficient warmup; and property-based non-negativity checks for rolling volatility.
  - Indicator tests shall cover EMA, SMA, ADX, ATR, ADR, rolling volatility, RSI, and Williams %R.
  - Formula golden tests shall verify exact formula conventions, seed behavior, warmup length, rolling-window inclusivity, null handling, and degenerate-window behavior for EMA, SMA, ADX, ATR, ADR, rolling volatility, RSI, and Williams %R.
  - Golden fixtures shall cover normal data, flat markets, gaps, missing bars, duplicated timestamps, extreme volatility, zero volume, all-null windows, and insufficient warmup.
  - Property-based tests shall verify rolling volatility is non-negative.
- [ ] Build and document a requirement-to-test traceability matrix mapping every requirement id to unit, contract, integration, performance, security, or documentation tests (or an approved deferral), and document the ADR range convention and Williams %R degenerate-window behavior.
  - The test plan shall include a requirement-to-test traceability matrix mapping each requirement id to one or more unit, contract, integration, performance, security, or documentation tests.
  - Documentation shall include a requirement-to-test traceability matrix.
  - Documentation shall describe ADR range convention and Williams %R degenerate-window behavior.
  - Requirement-to-test traceability matrix exists and maps every requirement id to tests or approved deferral.

#### Batch Momentum Indicators (RSI, Stochastic, etc.)

- [ ] Implement RSI and Williams %R momentum indicators, defining Williams %R behavior when highest high equals lowest low.
  - The module shall support momentum indicators including RSI and Williams %R.
  - No file-specific non-functional requirements defined.
  - No file-specific testing requirements defined.
  - Williams %R shall define behavior when highest high equals lowest low.
- [ ] Declare and version-constrain runtime dependencies, and document Python/dependency versions (NumPy, pandas, optional acceleration libraries) used in performance benchmarks.
  - Runtime dependencies shall be explicitly declared and version-constrained.
  - Performance benchmarks shall specify Python version and key dependency versions, including NumPy, pandas, and any optional acceleration dependencies.
- [ ] Confine timezone-database-dependent conversions to I/O boundaries, recording the timezone database version or conversion policy when available.
- [ ] Implement access-control checks validating actor, workflow, entitlement, environment, indicator id, indicator version, and intended use before calculation begins.
- [ ] Define the canonical parameter-hashing representation (key ordering, defaults, omitted optional values, numeric formatting, null representation, string normalization, version material) and the provenance fields it must cover: venue/exchange/data vendor/symbol-normalization version/corporate-action-adjustment version, implementation version, and formula version.
  - The module shall define the exact canonical representation used for parameter hashing, including key ordering, defaults, omitted optional values, numeric formatting, null representation, string normalization, and version material.
  - Venue, exchange, data vendor, symbol normalization version, and corporate-action adjustment version where available.
  - Implementation version.
  - Formula version.
- [ ] Review and pin reference outputs by implementation version, requiring formula justification, implementation-version pinning, golden fixture approval, and a changelog entry for any cross-validation deviation beyond documented tolerance.
  - Reference outputs shall be reviewed and pinned by implementation version.
  - Cross-validation deviations beyond documented tolerance shall require formula justification, implementation-version pinning, golden fixture approval, and changelog entry.

#### Incremental Indicator Calculations Package

- [ ] No file-specific functional requirements defined. Foundation properties apply.
- [ ] No file-specific non-functional requirements defined.
- [ ] No file-specific testing requirements defined.

#### Incremental Calculation State Tracking

- [ ] Keep the indicator module's ownership boundary fail-closed: fills, orders, account state, journals, and reports remain owned by the simulation module, and the indicator module shall never execute trades, create fills, mutate account state, mutate simulation journals, or perform broker-state operations.
  - Official fills, orders, account state, journals, and reports are produced by the simulation module.
  - The indicator module shall not execute trades, create fills, mutate account state, mutate simulation journals, or perform broker-state operations.
- [ ] Require vectorized official batch calculation (per-row Python loops only for documented unvectorizable stateful formulas), prohibit hidden global mutable state, and require performance benchmarks to state whether cached or uncached performance is measured.
  - Official production batch indicators shall not rely on per-row Python loops except for formulas with documented stateful dependencies that cannot be vectorized safely.
  - Indicator implementations shall avoid hidden global mutable state.
  - Performance benchmarks shall state whether cached or uncached performance is being measured.
- [ ] Expose the public incremental-calculation type surface (`IndicatorProtocol`, `IndicatorConfig`, `IndicatorContext`, `IndicatorResult`, `IndicatorManifest`, `IndicatorState`, `WarmupRequirement`, `IndicatorRegistration`, `IndicatorError`) with exact approved contracts, including `IndicatorProtocol.update(bar, state, config, context)` and `serialize_state(state)`/`deserialize_state(payload)` for indicators supporting incremental or streaming execution, and an `IndicatorState` containing serializable accumulators, last-processed timestamp/symbol, warmup completion status, input checksum, and state schema version.
  - The public package shall expose `IndicatorProtocol`, `IndicatorConfig`, `IndicatorContext`, `IndicatorResult`, `IndicatorManifest`, `IndicatorState`, `WarmupRequirement`, `IndicatorRegistration`, and `IndicatorError` with exact approved type contracts.
  - `IndicatorProtocol` shall define `update(bar, state, config, context)` when the indicator supports incremental or streaming execution.
  - `IndicatorProtocol` shall define `serialize_state(state)` and `deserialize_state(payload)` when the indicator supports incremental or streaming execution.
  - `IndicatorState` shall contain serializable incremental accumulators, last processed timestamp, last processed symbol, warmup completion status, input checksum, and state schema version.
- [ ] Document each indicator's smoothing convention (e.g. whether RSI/ATR/ADX use Wilder smoothing) and its Production Scope Tier (Core MVP, Official Backtest Required, Production Required, Optional Extension, or Future Improvement) in the formula specification table.
  - RSI, ATR, and ADX implementations shall explicitly state whether they use Wilder smoothing or another smoothing convention.
  - Formula specification tables shall state whether each indicator is Core MVP, Official Backtest Required, Production Required, Optional Extension, or Future Improvement.
- [ ] Preserve incremental indicator state continuity across symbol-mapping events (mergers, ticker replacements, vendor remaps) for equivalent instrument identities, resetting warmup only when the mapping policy marks the instrument as discontinuous.
- [ ] Implement the serializable incremental state contract: a documented binary or text serialization format containing indicator id, implementation version, state schema version, parameter hash, input checksum of all data processed, internal accumulator values sufficient to resume without recomputation, last-processed timestamp and symbol, and a warmup completion flag, with bounded size that does not grow proportionally to total bars processed and sufficient information to resume without recomputing full history.
  - Incremental indicators shall expose serializable state.
  - Incremental state shall include enough information to resume calculation without recomputing the full history.
  - Serialized incremental state shall use a documented binary or text serialization format.
  - Serialized incremental state shall include indicator id.
  - Serialized incremental state shall include implementation version.
  - Serialized incremental state shall include incremental state schema version.
  - Serialized incremental state shall include parameter hash.
  - Serialized incremental state shall include input checksum of all data processed so far.
  - Serialized incremental state shall include internal accumulator values sufficient to resume without recomputation.
  - Serialized incremental state shall include last-processed timestamp and symbol.
  - Serialized incremental state shall include warmup completion flag.
  - Incremental state size shall be bounded and shall not grow proportionally to the total number of bars processed.
  - Serializable incremental state when incremental calculation is enabled.
- [ ] Implement deserialization compatibility validation returning `IND_STATE_INCOMPATIBLE` for mismatched indicator id/version/schema/parameters and `IND_STATE_CORRUPTED` for corrupted or unreadable state, with the incompatible-state error returned deterministically before state is updated.
  - Deserialization shall validate that provided state matches current indicator id, implementation version, schema version, and parameter set.
  - Deserialization of state from a different indicator version, schema version, or parameter set shall return `IND_STATE_INCOMPATIBLE`.
  - Corrupted or unreadable serialized state shall return `IND_STATE_CORRUPTED`.
  - Incompatible incremental state shall return a deterministic error code before state is updated.
  - Support indicator codes/constants: `IND_STATE_INCOMPATIBLE`, `IND_STATE_CORRUPTED`
- [ ] Require indicators to consume warmup data for calculation state without emitting warmup-period output rows unless explicitly marked as warmup.
- [ ] Require unauthorized proprietary indicator requests to fail before input data is read, state is deserialized, cache entries are read, or calculation begins.
- [ ] Define the incremental concurrency/thread-safety model: stateless functions thread-safe by default, stateful incremental indicators documented as single-owner (not safe for concurrent mutation) or lock-free (safe for concurrent reads via immutable state snapshots).
  - Stateless indicator functions shall be thread-safe by default.
  - Stateful incremental indicators shall be single-owner or lock-free according to their documented state model.
  - Single-owner incremental state objects shall not be safe for concurrent mutation.
  - Lock-free incremental state objects shall be safe for concurrent reads with immutable state snapshots.
- [ ] Document incremental-state serialization/idempotency/late-arriving/corrected/revised/out-of-order behavior, state format/compatibility/corruption handling/bounded size, thread-safety/ownership/immutable-snapshot/cache-concurrency/parallel-symbol-execution/worker-pool/chunk-size details, and the supported batch/incremental/streaming calculation modes (including whether out-of-order incremental updates are supported).
  - Documentation shall describe incremental state serialization, idempotency, late-arriving data, corrected data, revised data, and out-of-order update behavior.
  - Documentation shall describe incremental state format, state compatibility validation, state corruption handling, and bounded state size.
  - Documentation shall describe thread-safety guarantees, incremental state ownership, immutable state snapshots, cache concurrency, parallel symbol execution, worker pools, worker counts, chunk sizes, and cache synchronization.
  - Documentation shall describe batch, incremental, and streaming calculation modes.
  - Indicators shall define whether they support batch calculation, incremental calculation, streaming calculation, or a subset of these modes.
  - The module shall define whether out-of-order incremental updates are supported.
- [ ] Confirm debug-mode strict typing/runtime validation fails before calculation or state mutation, and that incremental state compatibility/corruption tests pass.
  - Debug-mode strict typing and runtime validation fail before calculation or state mutation.
  - Incremental state compatibility and corruption tests pass.
- [ ] Require `IndicatorManifest`, `IndicatorState`, and `IndicatorError` to have exact serialized field contracts approved before implementation begins.
  - `IndicatorManifest`, `IndicatorState`, and `IndicatorError` shall have exact serialized field contracts before implementation begins.
  - No file-specific non-functional requirements defined.
- [ ] Write the incremental-state test suite: input-validation-timing tests (parameter/schema/data-sufficiency/state-deserialization/new-bar validation failing before calculation or mutation); indicator-anatomy tests for the full type surface and required methods (`validate_parameters`, `required_columns`, `output_columns`, `warmup_requirement`, `validate_input`, `calculate`, `calculate_vectorized`, `update`, `serialize_state`, `deserialize_state`); debug-mode type-mismatch tests; incremental serialization/resume/idempotency/late-arriving/corrected/revised/out-of-order tests; full state-field and error-code tests; symbol-mapping continuity tests; concurrency tests; fuzz tests for graceful or deterministic rejection without corruption; and batch/incremental parity tests.
  - Input validation timing tests shall verify parameter validation, schema validation, data sufficiency checks, state deserialization validation, and new-bar validation fail before calculation or state mutation.
  - Indicator anatomy tests shall verify `IndicatorProtocol`, `IndicatorConfig`, `IndicatorContext`, `IndicatorResult`, `IndicatorManifest`, `IndicatorState`, `WarmupRequirement`, `IndicatorRegistration`, and `IndicatorError` contracts.
  - Indicator anatomy tests shall verify required methods for `validate_parameters`, `required_columns`, `output_columns`, `warmup_requirement`, `validate_input`, `calculate`, `calculate_vectorized`, `update`, `serialize_state`, and `deserialize_state` where applicable.
  - Debug-mode validation tests shall verify type mismatches fail before calculation, state mutation, cache reads, cache writes, or output generation.
  - Incremental tests shall verify state serialization, resume behavior, idempotent repeated input bars, late-arriving bars, corrected bars, revised bars, and out-of-order updates.
  - Incremental state tests shall verify state format, indicator id, implementation version, schema version, parameter hash, processed input checksum, accumulator values, last-processed timestamp, last-processed symbol, warmup completion flag, bounded state size, `IND_STATE_INCOMPATIBLE`, and `IND_STATE_CORRUPTED`.
  - Symbol mapping tests shall cover symbol changes, mergers, ticker replacements, vendor remaps, state continuity, discontinuity markers, and warmup reset behavior.
  - Concurrency tests shall verify stateless function thread safety, single-owner incremental-state behavior, immutable snapshot reads, parallel symbol execution, cache concurrent reads, and atomic synchronized cache writes.
  - Fuzz tests shall verify graceful unavailable outputs or deterministic rejection for invalid mutated inputs without crashes, nondeterminism, cache corruption, or state corruption.
  - Batch and incremental parity tests pass for indicators that support incremental mode.

#### Incremental Bar Accumulators

- [ ] No file-specific functional requirements defined. Foundation properties apply.
- [ ] No file-specific non-functional requirements defined.
- [ ] No file-specific testing requirements defined.

#### Indicator Cache/Audit Integration

- [ ] No file-specific functional requirements defined. Foundation properties apply.
- [ ] No file-specific non-functional requirements defined.
- [ ] No file-specific testing requirements defined.

#### Indicator Cache Adapter

- [ ] Implement deterministic cache-hit behavior with policy-driven degradation: cache hits never reuse results across incompatible input data, parameter sets, implementation versions, or schema versions; an unreachable cache adapter degrades to uncached calculation with warning metadata under `cache_policy="best_effort"`; and the request fails before calculation with deterministic diagnostics under `cache_policy="strict"`.
  - Cache hits shall be deterministic and shall never reuse results across incompatible input data, parameter sets, implementation versions, or schema versions.
  - If an optional cache adapter is unreachable and `cache_policy="best_effort"`, the module shall degrade to uncached calculation with warning metadata rather than raising an unhandled exception.
  - If an optional cache adapter is unreachable and `cache_policy="strict"`, the request shall fail before calculation with deterministic cache-unavailable diagnostics.
- [ ] Define and benchmark latency/SLO targets: uncached first-run p99 ≤ 5 seconds for 10 years × 10 symbols of M1 bars, warm-cache batch p99 ≤ 250 ms for up to 10 symbols and 100,000 rows, ≥95% cache hit ratio after warmup for repeated stable-input runs, and production-defined SLOs for latency, cache hit ratio, non-transient error rate, and timeout rate, sourced from the performance benchmark specification.
  - Default uncached first-run calculation latency for official indicator workloads shall target p99 less than or equal to 5 seconds for 10 years by 10 symbols of M1 bars on the documented benchmark hardware profile.
  - Warm-cache batch calculation for official indicator workloads shall target p99 less than or equal to 250 milliseconds for up to 10 symbols and 100,000 input rows, aligned with the service-level objective section.
  - Performance benchmark specifications shall be the source for the p99 uncached and warm-cache targets defined in the service-level objective section.
  - Default warm-cache calculation latency for official indicator workloads shall target p99 less than or equal to 250 milliseconds per indicator request for up to 10 symbols and 100,000 input rows.
  - Repeated research and simulation runs with stable inputs shall target cache hit ratio of at least 95 percent after cache warmup.
  - Production indicator workflows shall define service level objectives for calculation latency, cache hit ratio, non-transient error rate, and timeout rate.
- [ ] Implement out-of-core and parallel-execution cache integrity: preserve warmup continuity, symbol grouping, timestamp ordering, provenance metadata, and cache-key determinism across out-of-core chunks, and make parallel symbol execution configurable by thread pool, process pool, worker count, chunk size, and cache synchronization mode.
  - Out-of-core processing shall preserve warmup continuity, symbol grouping, timestamp ordering, provenance metadata, and cache-key determinism across chunks.
  - Parallel execution across symbols shall be configurable by thread pool, process pool, worker count, chunk size, and cache synchronization mode.
- [ ] Define `IndicatorConfig` to carry indicator id, parameters, source column, output naming policy, output mode, column conflict policy, precision policy, cache policy, calendar policy, availability policy, and execution backend configuration.
  - `IndicatorConfig` shall contain indicator id, parameters, source column, output naming policy, output mode, column conflict policy, precision policy, cache policy, calendar policy, availability policy, and execution backend configuration.
- [ ] Normalize all internal timestamp arithmetic and cache keys to UTC, and record deterministic intra-bar adjustment policies in the indicator manifest with parity across batch, incremental, streaming, and cached execution.
  - All internal timestamp arithmetic and cache keys shall be normalized to UTC.
  - Deterministic intra-bar adjustment policies shall be recorded in the indicator manifest and shall not differ across batch, incremental, streaming, or cached execution.
- [ ] Implement cache-key ownership for composed indicators: support composition in the cache layer, with the indicator module owning cache-key derivation and downstream invalidation when upstream inputs, parameters, formulas, or implementation versions change, while external cache backends own eviction/physical invalidation/consistency/synchronization through documented adapter contracts.
  - The cache layer shall support composition.
  - The indicator module shall own cache-key derivation and downstream invalidation triggers for composition when upstream inputs, upstream parameters, upstream formulas, or upstream implementation versions change.
  - External cache storage backends shall own eviction, physical invalidation, consistency, and synchronization mechanisms through documented adapter contracts.
- [ ] Require any proprietary-source protection mechanism to remain outside the public API contract without changing deterministic outputs, error behavior, manifest content, cache keys, or test expectations.
- [ ] Define the cache/SLO/benchmark manifest and config fields: optional cache policy; optional SLO configuration (latency/cache-hit/error-rate/timeout-rate targets, measurement window, alert routing); optional benchmark context (hardware profile, Python version, dependency versions, cache mode, warmup iterations, methodology); manifest `calculation_config` (precision policy, session calendar id, data latency config, calculation mode, resource limits, cache policy); and manifest `slo` (configured thresholds, observed latency, cache status, error classification, timeout status).
  - Optional cache policy.
  - Optional SLO configuration containing latency target, cache-hit target, error-rate target, timeout-rate target, measurement window, and alert routing.
  - Optional benchmark context containing hardware profile, Python version, dependency versions, cache mode, warmup iterations, and measurement methodology.
  - The manifest shall include `calculation_config` with precision policy, session calendar identifier, data latency config, calculation mode, resource limits, and cache policy.
  - The manifest shall include `slo` with configured thresholds and observed latency, cache status, error classification, and timeout status where applicable.
- [ ] Return deterministic error codes for resource-limit, timeout, cancellation, partial-result, cache-write, unsupported-out-of-core, unavailable-acceleration-backend, and unsupported-incremental-mode conditions, supporting `IND_CACHE_INVALID` and `IND_CACHE_WRITE_FAILED`.
  - Resource-limit, timeout, cancellation, partial-result, cache-write, unsupported out-of-core, unavailable acceleration backend, and unsupported incremental mode conditions shall return deterministic error codes.
  - Support indicator codes/constants: `IND_CACHE_INVALID`, `IND_CACHE_WRITE_FAILED`
- [ ] Enforce side-effect-free import: importing `app.services.indicators` shall perform no network I/O, filesystem writes, cache writes, plugin execution, long-running computation, environment mutation, or untrusted-plugin registration.
  - Import-time tests shall verify importing `app.services.indicators` performs no network I/O, filesystem writes, cache writes, plugin execution, long-running computation, environment mutation, or registration from untrusted plugins.
- [ ] Emit observability metrics and trace spans for cache/calculation behavior: metrics covering calculation duration, row/symbol counts, cache hit/miss, memory usage estimate, rejected/warmup row counts, and error code counts; trace spans carrying request id, correlation id, indicator id, implementation version, parameter hash, input checksum, cache status, backend id, and error code.
  - Metrics shall include calculation duration, input row count, output row count, symbol count, cache hit or miss, memory usage estimate, rejected row count, warmup row count, and error code counts.
  - Trace spans shall carry request id, correlation id, indicator id, implementation version, parameter hash, input checksum, cache status, backend id, and error code when available.
- [ ] Implement atomic, thread-safe cache writes and graceful degradation under pressure: atomic writes that never corrupt existing valid entries; documented behavior under memory pressure, cancellation, timeout, and interrupted writes; a documented cleanup policy for partial cache/audit/out-of-core spill artifacts; thread-safe concurrent reads with multiple concurrent readers; single-writer or multi-writer operation with documented synchronization; preserved dtype metadata in cached outputs; and documented interaction between parallel symbol execution and the cache.
  - Cache writes shall be atomic and shall not corrupt existing valid cache entries on failure.
  - The module shall define behavior under memory pressure, cancellation, timeout, and interrupted cache writes.
  - Cancellation, timeout, and memory-pressure handling shall clean up partial cache writes, audit writes, and out-of-core spill artifacts according to a documented cleanup policy.
  - Cached outputs shall preserve dtype metadata.
  - The cache layer shall be thread-safe for concurrent reads and atomic writes.
  - Cache implementations shall support multiple concurrent readers.
  - Cache implementations shall support single-writer or multi-writer operation with documented synchronization.
  - The module shall document whether parallel symbol execution is supported and how it interacts with the cache.
- [ ] Run the full indicator correctness, determinism, no-lookahead, cache, and benchmark regression suite on every dependency upgrade.
- [ ] Write and maintain documentation covering: public API contract tables (import paths, signatures, defaults, schemas, error behavior, side effects, cache behavior, stability, official-workflow eligibility); cache keys and invalidation behavior; UTC normalization and I/O-boundary local/exchange time handling; performance benchmark methodology (hardware profile, dependency versions, cached/uncached modes, warmup iterations, regression threshold); composition/`available_at`/provenance/cache-invalidation behavior; SLO thresholds and alert routing; and resource-limit/timeout/cancellation/memory-pressure/partial-result policy.
  - Documentation shall include public API contract tables covering import paths, signatures, defaults, input schemas, output schemas, error behavior, side effects, cache behavior, stability level, and official-workflow eligibility.
  - Documentation shall describe cache keys and invalidation behavior.
  - Documentation shall describe UTC normalization for internal timestamp arithmetic and cache keys, and shall define local and exchange time handling at I/O boundaries.
  - Documentation shall describe performance benchmark hardware profile, dependency versions, cached and uncached modes, warmup iterations, measurement methodology, and regression threshold.
  - Documentation shall describe indicator composition, `available_at` preservation, provenance propagation, and downstream cache invalidation.
  - Documentation shall describe service level objectives, latency thresholds, cache-hit thresholds, error-rate thresholds, timeout-rate thresholds, measurement windows, excluded error categories, and alert routing.
  - Documentation shall describe resource limits, timeout behavior, cancellation behavior, memory-pressure behavior, interrupted cache-write behavior, and partial-result policy.
- [ ] Confirm cache-adapter done-criteria: UTC normalization implemented and tested; thread-safety/cache-concurrency tests pass; parallel symbol execution and cache synchronization tests pass; resource-limit/timeout/cancellation/cache-write-failure tests pass; complete documentation for formulas/APIs/schemas/dtypes/cache/observability/release controls; Production Required scope (resource limits, redacted diagnostics, documented cache behavior, API compatibility rules, acceptance gates) satisfied; and every public callable's stable contract (import path, signature, parameters, schema, return type, error behavior, side effects, cache behavior, stability, eligibility) defined.
  - UTC normalization for internal timestamp arithmetic and cache keys is implemented and tested.
  - Thread-safety and cache-concurrency tests pass.
  - Parallel symbol execution configuration and cache synchronization tests pass.
  - Resource-limit, timeout, cancellation, and cache-write failure tests pass.
  - Indicator documentation is complete for formulas, APIs, schemas, dtypes, cache behavior, observability, and release controls.
  - Production Required shall include resource limits, redacted structured diagnostics, documented cache behavior if caching is enabled, public API compatibility rules, and acceptance gates for official workflows.
  - Every public callable shall define its stable import path, function signature, required parameters, optional parameters and defaults, accepted input schema, returned object type, deterministic error behavior, side effects, cache behavior, stability level, and official-workflow eligibility.
- [ ] Classify cache-adapter scope: out-of-core processing as Optional Extension pending chunking-parity and cache-integrity approval, and canary routing/distributed tracing/SLO alerting/cryptographic signing/release attestations/SBOM generation/multi-writer cache synchronization as platform/release-engineering integrations pending ownership approval.
  - Out-of-core processing may be added as an Optional Extension after chunking parity and cache integrity requirements are approved.
  - Canary routing, distributed tracing, SLO alerting, cryptographic package signing, release attestations, SBOM generation, and multi-writer cache synchronization may be added through platform or release-engineering integrations after ownership is approved.
  - No file-specific non-functional requirements defined.
- [ ] Write the cache-adapter test suite: UTC-normalization tests; cache hit/miss/version/parameter/checksum-change tests; atomic-write and interrupted-write tests; degradation tests for `best_effort` vs `strict` cache policy; corrupt-manifest/stale-cache/checksum-mismatch/parameter-hash-stability tests; composition tests for `available_at`/provenance/invalidation/unavailable-upstream rejection; performance benchmark tests including CI failure on unapproved regressions above 20 percent; corporate-action parity tests; SLO threshold/alert-routing tests; and proprietary-indicator access-control/parity tests.
  - UTC normalization tests shall verify internal timestamp arithmetic and cache keys are UTC-normalized while local and exchange time conversions occur only at I/O boundaries.
  - Cache tests shall cover cache hits, cache misses, schema-version changes, implementation-version changes, parameter changes, and input checksum changes.
  - Cache tests shall verify atomic cache writes and failure behavior for interrupted cache writes.
  - Cache degradation tests shall verify cache adapter connection failures fall back to uncached calculation with warning metadata under `cache_policy="best_effort"` and fail before calculation under `cache_policy="strict"`.
  - Cache tests shall verify corrupt manifest rejection, stale cache rejection when dependency versions or schema versions change, output checksum mismatch detection, and canonical parameter hash stability across equivalent parameter ordering.
  - Composition tests shall verify `available_at` preservation, provenance propagation, downstream cache invalidation, and rejection of unavailable upstream values.
  - Performance benchmark tests shall verify benchmark metadata, cached and uncached modes, warmup iterations, min/median/p99 measurement, per-indicator tracking, and CI failure on unapproved regressions above 20 percent.
  - Corporate-action tests shall cover intra-bar adjustment rejection, deterministic intra-bar adjustment policies, manifest recording, and parity across batch, incremental, streaming, and cached execution.
  - SLO tests shall verify latency, cache-hit ratio, non-transient error rate, timeout rate, measurement windows, excluded error categories, alert routing metadata, and synchronous enforcement behavior when configured.
  - Proprietary indicator tests shall verify access checks before execution, unauthorized request rejection before data or cache access, non-sensitive access-control manifest metadata, and deterministic parity for protected-source packages.

#### Indicator Integrity Audit Trail

- [ ] Define `IndicatorManifest` to carry calculation identity, formula identity, input checksum, output checksum, parameter hash, output schema version, output column contract, data provenance, execution backend, timing, environment, and audit metadata.
  - `IndicatorManifest` shall contain calculation identity, formula identity, input checksum, output checksum, parameter hash, output schema version, output column contract, data provenance, execution backend, timing, environment, and audit metadata.
- [ ] Implement audit-mode entry generation: official simulation/production workflows may require audit entries; when audit mode is enabled (`audit_mode=true` or workflow policy), emit an immutable audit log entry containing the full indicator manifest, request metadata (actor, workflow, correlation id, request id, timestamp), input checksum, output checksum, and tamper-evident integrity metadata, through a documented audit sink interface rather than owning external audit storage; audit mode shall not change indicator outputs except for the added audit metadata.
  - Official simulation and production workflows may require indicator calculation audit entries.
  - When audit mode is enabled, the indicator module shall produce an immutable audit log entry.
  - When `audit_mode=true` or the workflow policy requires audit, the module shall emit an immutable audit entry containing the full indicator manifest, request metadata, input checksum, output checksum, and tamper-evident integrity metadata.
  - The module shall emit audit payloads through a documented audit sink interface rather than owning external audit storage unless a later approved architecture decision assigns that responsibility.
  - Audit entries shall include the full indicator manifest.
  - Audit entries shall include request metadata containing actor, workflow, correlation id, request id, and timestamp when available.
  - Audit entries shall include input data checksum.
  - Audit entries shall include output data checksum.
  - Audit mode shall not change indicator outputs except for additional audit metadata.
  - Optional audit mode.
  - Audit log entry when audit mode is enabled.
- [ ] Require approval of the Audit Policy appendix (chained SHA-256 HMAC with managed signing-key handling, or a tamper-evident Merkle-tree policy) defining append-only tamper-evident audit entries before production use; halt production audit mode until `IND-PREQ-007` (audit integrity mechanism selection, signing-key custody, rotation, and verification rules) is resolved with owner/security approval.
  - Audit entries shall be append-only and tamper-evident through the approved Audit Policy appendix, which must define either chained SHA-256 HMAC with managed signing-key handling or a tamper-evident Merkle-tree policy before production use.
  - Pending: Audit integrity mechanism selection, signing-key custody, rotation, and verification rules require owner/security approval before production audit mode is accepted.
  - Production audit mode shall halt until `IND-PREQ-007` is resolved.
  - No file-specific non-functional requirements defined.
- [ ] Document audit mode, audit entry structure, tamper-evident integrity, and audit metadata.
  - Documentation shall describe audit mode, audit entry structure, tamper-evident integrity, and audit metadata.
- [ ] Write the audit-trail test suite verifying audit entries include the full manifest, request metadata, input checksum, output checksum, append-only behavior, tamper-evident integrity, and unchanged calculation semantics when audit mode is enabled.
  - Audit mode entries are append-only, tamper-evident, and tested when audit mode is enabled.
  - Audit tests shall verify audit entries include full manifest, request metadata, input checksum, output checksum, append-only behavior, tamper-evident integrity, and unchanged calculation semantics.


### Hardening Amendments

#### Deterministic indicator contract

Requirements:

- [ ] Adopt the Phase 1.5 `IndicatorResult` contract for all public indicator outputs.
- [ ] Enforce a no-lookahead rule for every batch and streaming indicator.
- [ ] Expose warmup period, required input columns, minimum bars, parameter hash, input hash, and output metadata for every indicator.
- [ ] Ensure identical inputs and parameters produce identical outputs in research, strategy, simulation, optimization, and live contexts.
- [ ] Define deterministic NaN, missing-value, timezone, duplicate-timestamp, and insufficient-history behavior for every indicator.
- [ ] Add shared golden-dataset regression tests proving indicator parity across batch and streaming paths where both exist.

### Unit Tests Required

```text

tests/unit/app/services/indicators/

```

Test coverage:

- [ ] Cover every requirement in this phase with normal, edge, invalid-input, fail-closed, logging, schema, and regression tests as applicable.
- [ ] Preserve the project gate of at least 80% coverage for each affected file and package.
- [ ] Verify standard envelopes, deterministic error codes, import behavior, and ownership boundaries.

### Usage Examples Required

```text

tests/usage/app/services/03_indicators.py

```

Usage examples must show:

- `example_01_registry_and_capabilities`: Demonstrate indicator registration, lookup, listing, capability metadata, and unsupported-capability failures.
- `example_02_trend_indicators`: Demonstrate SMA, EMA, and ADX calculations with warmup and availability metadata.
- `example_03_volatility_indicators`: Demonstrate ATR, ADR, and rolling volatility calculations with precision policy metadata.
- `example_04_momentum_indicators`: Demonstrate RSI and Williams %R calculations with deterministic outputs and invalid-input handling.
- `example_05_incremental_state`: Demonstrate accumulator state serialization, compatibility checks, and incremental updates.
- `example_06_composition_and_dependency_graph`: Demonstrate DAG validation, composed indicator execution, dependency ordering, and cycle rejection.
- `example_07_caching_and_provenance`: Demonstrate cache keys, parameter hashes, implementation versions, source checksums, and provenance metadata.
- `example_08_no_lookahead_guards`: Demonstrate incomplete-bar rejection, previous-closed-bar decisions, and lookahead diagnostics.
- [ ] The single usage file must be runnable as a script and organize separate examples as focused functions.
- [ ] Examples must extensively cover the phase's official public capabilities, important edge cases, fail-closed paths, and standard envelope fields where applicable.

### Documentation and Logging Requirements

- [ ] Log calls, validation failures, success, exception paths, and governed/fail-closed decisions with redacted metadata only.

### Quality and Documentation Standards

- [ ] All Python modules and public functions/classes must have appropriate file-level and Google-style docstrings.
- [ ] Update module README and active documentation for any architecture or API changes.


### Acceptance Checklist

- [ ] Done criterion: All 737 checkbox tasks are implemented or explicitly deferred with a documented reason.
- [ ] Done criterion: Scope stayed within this phase and approved dependency surfaces.
- [ ] Done criterion: Public exports match the phase registry rules and do not expose unapproved helpers.
- [ ] Done criterion: Standard envelopes, metadata, request IDs, error codes, logging, and redaction rules are satisfied where applicable.
- [ ] Done criterion: Unit tests, usage examples, static typing, linting, formatting, and coverage gates pass.
- [ ] Done criterion: Active docs and changelog are updated for any implemented project meaning changes.
- [ ] Done criterion: Rollback path and implementation report are recorded before handoff.

### Commit Message

```text

feat(indicator-library): implement mathematical indicator formulas and composition



- [ ] Implement core indicators: SMA, EMA, ADX, ATR, ADR, RSI, and Williams %R

- [ ] Setup DAG executor and topological sort for composed indicators in `engine.py`

- [ ] Support incremental calculations, cache lookups, and state serialization

- [ ] Provide rich Jupyter HTML and text representation on indicator result objects

```

- [ ] Indicator functions shall avoid production `print()` output and shall use structured logging only through approved utility logging contracts where logging is required.
- [ ] SBOM generation, cryptographic package signing, vulnerability checks, license gates, and release provenance attestations shall be CI/CD and release-engineering responsibilities, not Python indicator module runtime responsibilities, unless explicitly assigned by a later approved architecture decision.
- [ ] Release artifacts shall include provenance attestations that identify source revision, build workflow, build environment, package hash, and signing identity.
- [ ] Supply-chain tests shall verify dependency declarations, lockfile or equivalent reproducibility mechanism, license compatibility checks, vulnerability checks, SBOM generation support, cryptographic package signing, and release provenance attestations.
- [ ] Documentation shall describe market-data provenance, price adjustment status, price source, venue, vendor, symbol normalization version, corporate-action adjustment version, and continuous-instrument adjustment policy.
- [ ] Documentation shall describe dependency pinning, lockfile or equivalent reproducibility mechanism, SBOM generation, license checks, vulnerability checks, cryptographic package signing, release provenance attestations, and waiver process.
- [ ] Market-data provenance, adjustment status, intra-bar corporate actions, symbol mapping, and microstructure rules are validated.
- [ ] Cryptographic package signing and release provenance attestation are present for production packages.

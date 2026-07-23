# Indicator Domain — Capability Feature Extraction (from `03-indicator.md`)

Source: `docs/dev/phase-implementation-plan/03-indicator.md`. Module paths follow the plan's target tree. Signatures not explicitly stated in the doc are inferred from its target class/function contracts. Documentation, CI, and test modules are omitted.

---

## FEAT-INDI-01: Public Indicator API (app.services.indicators.api)

---

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `ema(data: pd.DataFrame, period: int = 14, source: str = "close", *, config: IndicatorConfig \| None = None, context: IndicatorContext \| None = None) -> IndicatorResult` | Exponential moving average via the official convenience surface. | Implemented |
| `sma(data: pd.DataFrame, period: int = 14, source: str = "close", *, config: IndicatorConfig \| None = None, context: IndicatorContext \| None = None) -> IndicatorResult` | Simple moving average. | Implemented |
| `adx(data: pd.DataFrame, period: int = 14, *, config: IndicatorConfig \| None = None, context: IndicatorContext \| None = None) -> IndicatorResult` | Average directional index trend strength. | Implemented |
| `atr(data: pd.DataFrame, period: int = 14, *, config: IndicatorConfig \| None = None, context: IndicatorContext \| None = None) -> IndicatorResult` | Average true range volatility. | Implemented |
| `adr(data: pd.DataFrame, period: int = 14, *, config: IndicatorConfig \| None = None, context: IndicatorContext \| None = None) -> IndicatorResult` | Average daily range. | Implemented |
| `rolling_volatility(data: pd.DataFrame, period: int = 20, *, config: IndicatorConfig \| None = None, context: IndicatorContext \| None = None) -> IndicatorResult` | Rolling standard-deviation volatility. | Implemented |
| `rsi(data: pd.DataFrame, period: int = 14, source: str = "close", *, config: IndicatorConfig \| None = None, context: IndicatorContext \| None = None) -> IndicatorResult` | Relative strength index momentum. | Implemented |
| `williams_r(data: pd.DataFrame, period: int = 14, *, config: IndicatorConfig \| None = None, context: IndicatorContext \| None = None) -> IndicatorResult` | Williams %R momentum oscillator. | Implemented |

## FEAT-INDI-02: Indicator Protocol, Result, Manifest, and Error Contracts (app.services.indicators.contracts)

---

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `IndicatorProtocol.validate_parameters(parameters: Mapping[str, JsonValue]) -> ValidatedParameters` | Formal indicator contract: validate declared parameters (with `required_columns`, `output_columns`, `warmup_requirement`, `validate_input`, `calculate`, and optional `calculate_vectorized` protocol methods). | Missing |
| `IndicatorResult.join_to(input_data: pd.DataFrame, mode: JoinMode = "copy") -> pd.DataFrame` | Join indicator output to input data, returning a newly allocated dataframe in the default mode. | Implemented |
| `IndicatorResult.mask_unavailable(decision_time: datetime) -> IndicatorResult` | Mask values not yet available at a decision time (lookahead safety). | Missing |
| `IndicatorResult.to_serializable(precision: PrecisionPolicy) -> Mapping[str, JsonValue]` | JSON-safe serialization under an explicit precision policy. | Missing |
| `safe_divide(numerator: pd.Series, denominator: pd.Series, policy: NumericPolicy) -> NumericResult` | Numeric-policy-governed division (with `rolling_window`, `normalize_negative_zero`, and `apply_numeric_policy` counterparts). | Missing |
| `canonical_parameter_hash(parameters: Mapping[str, JsonValue], definition: IndicatorDefinition) -> str` | Deterministic parameter hash for manifests and cache keys. | Missing |
| `build_indicator_manifest(request: ManifestBuildRequest) -> IndicatorManifest` | Build the reproducibility manifest (with input/output frame checksum helpers). | Missing |
| `indicator_error(code: IndicatorErrorCode, message: str, *, field_path: str \| None = None, details: Mapping[str, JsonValue] \| None = None) -> IndicatorError` | Construct deterministic indicator errors (with `raise_or_collect` error-mode boundary and redacting `map_exception`). | Missing |
| `serialize_state(state: IndicatorState) -> str` | Serialize incremental indicator state (with `create_initial_state`, `validate_state_compatibility`, `deserialize_state` counterparts). | Missing |

## FEAT-INDI-03: Indicator Registry, Capability Matrix, and Governance (app.services.indicators.registry)

---

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `IndicatorRegistry.register(definition: IndicatorProtocol, registration: IndicatorRegistration) -> None` | In-memory catalog registration; prohibited for sealed official production registries. | Missing |
| `IndicatorRegistry.get(indicator_id: str, version: VersionConstraint \| None = None) -> IndicatorProtocol` | Read-only versioned indicator lookup (with `list` and `validate` counterparts). | Missing |
| `build_capability_matrix(registrations: Iterable[IndicatorRegistration]) -> CapabilityMatrix` | Aggregate registered indicators into a workflow capability matrix. | Missing |
| `validate_official_eligibility(registration: IndicatorRegistration, workflow: Workflow) -> ValidationReport` | Check whether an indicator is eligible for an official workflow. | Missing |
| `resolve_deprecation_status(subject: DeprecationSubject, current_version: SemanticVersion) -> DeprecationDecision` | Deterministic deprecation resolution (with `enforce_deprecation` error-mode counterpart). | Missing |
| `validate_custom_indicator(definition: IndicatorProtocol, policy: CustomIndicatorPolicy) -> ValidationReport` | Validate a custom indicator against the conformance policy. | Missing |
| `run_conformance_suite(definition: IndicatorProtocol, fixtures: ConformanceFixtures) -> ConformanceReport` | Sandbox conformance testing of a candidate indicator. | Missing |
| `promote_indicator(registration: IndicatorRegistration, evidence: PromotionEvidence) -> IndicatorRegistration` | Evidence-backed registry-governance promotion. | Missing |

## FEAT-INDI-04: Input Validation, Provenance, and Composition (app.services.indicators.validation)

---

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `validate_input_frame(data: pd.DataFrame, config: IndicatorConfig) -> ValidatedIndicatorInput` | Pipeline up-front validation of the input frame (with UTC index normalization, OHLCV schema, and resource-limit checks). | Missing |
| `validate_data_provenance(provenance: DataProvenance, policy: ProvenancePolicy) -> None` | Enforce data lineage/provenance policy before calculation. | Missing |
| `validate_symbol_mapping(mapping: SymbolMapping \| None, instrument: InstrumentIdentity) -> SymbolMappingDecision` | Resolve symbol-mapping continuity decisions. | Missing |
| `summarize_quality_flags(flags: pd.Series, policy: QualityPolicy) -> QualitySummary` | Aggregate upstream data-quality flags under policy. | Missing |
| `validate_composition_graph(graph: IndicatorGraph) -> TopologicallySortedIndicatorGraph` | Validate and topologically sort indicator composition graphs. | Missing |
| `compose_results(nodes: TopologicallySortedIndicatorGraph, inputs: Mapping[str, IndicatorResult], context: IndicatorContext) -> IndicatorResult` | Compose multi-indicator results with lineage propagation. | Missing |
| `assert_input_unchanged(data: pd.DataFrame, snapshot: InputMutationSnapshot) -> None` | Mutation guard raising a deterministic error if caller input was mutated (with `snapshot_input_identity`). | Missing |
| `validate_parameters(parameters: Mapping[str, JsonValue], schema: ParameterSchema) -> ValidatedParameters` | Schema-driven parameter validation (with output-column naming and column-conflict checks). | Missing |
| `validate_microstructure(data: pd.DataFrame, policy: MicrostructurePolicy) -> MicrostructureReport` | Bid/ask microstructure validation (with `resolve_mid_price` fallback resolution). | Missing |

## FEAT-INDI-05: Availability, Warmup, Calendar, and Timeframe Alignment (app.services.indicators.timing)

---

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `build_availability_metadata(data: pd.DataFrame, request: AvailabilityRequest) -> pd.DataFrame` | Attach per-bar availability timestamps for lookahead-safe consumption. | Missing |
| `mask_values_not_available_at(result: IndicatorResult, decision_time: datetime) -> IndicatorResult` | Mask indicator values unavailable at a decision time. | Missing |
| `assert_not_lookahead(available_at: datetime, decision_time: datetime, error_mode: ErrorMode) -> None` | Deterministic lookahead assertion at the error-mode boundary. | Missing |
| `build_warmup_request(indicator: IndicatorProtocol, config: IndicatorConfig, context: IndicatorContext) -> WarmupRequest` | Compute warmup data requirements as a data-domain contract. | Missing |
| `validate_warmup_response(data: pd.DataFrame, request: WarmupRequest) -> ValidatedIndicatorInput` | Validate returned warmup data (with `merge_warmup_with_primary`). | Missing |
| `align_higher_timeframe(primary: pd.DataFrame, higher: IndicatorResult, policy: HigherTimeframeAlignmentPolicy) -> IndicatorResult` | Align higher-timeframe indicator output onto a primary series without lookahead. | Missing |
| `resolve_session_window(timestamp: datetime, calendar: TradingCalendar) -> SessionWindow` | Session/calendar resolution (with `validate_calendar_policy`, `normalize_io_timezone`, and `validate_session_gap` counterparts). | Missing |

## FEAT-INDI-06: Versioned Formula Specifications (app.services.indicators.formulas)

---

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `get_formula_spec(indicator_id: str, version: str) -> FormulaSpecification` | Read-only retrieval of the authoritative versioned formula specification. | Missing |
| `validate_formula_specification(spec: FormulaSpecification) -> ValidationReport` | Validate a formula specification document. | Missing |
| `validate_formula_change(previous: FormulaSpecification, proposed: FormulaSpecification) -> VersionChangeDecision` | Decide semantic-version impact of a formula change. | Missing |

## FEAT-INDI-07: Built-In Indicator Implementations (app.services.indicators.builtins)

---

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `calculate_sma(data: pd.DataFrame, parameters: SmaParameters, config: IndicatorConfig, context: IndicatorContext) -> IndicatorResult` | Simple moving average implementation (trend). | Missing |
| `calculate_ema(data: pd.DataFrame, parameters: EmaParameters, config: IndicatorConfig, context: IndicatorContext) -> IndicatorResult` | Exponential moving average implementation (trend). | Missing |
| `calculate_adx(data: pd.DataFrame, parameters: AdxParameters, config: IndicatorConfig, context: IndicatorContext) -> IndicatorResult` | Average directional index implementation (trend). | Missing |
| `calculate_atr(data: pd.DataFrame, parameters: AtrParameters, config: IndicatorConfig, context: IndicatorContext) -> IndicatorResult` | Average true range implementation (volatility). | Missing |
| `calculate_adr(data: pd.DataFrame, parameters: AdrParameters, config: IndicatorConfig, context: IndicatorContext) -> IndicatorResult` | Average daily range implementation (volatility). | Missing |
| `calculate_rolling_volatility(data: pd.DataFrame, parameters: RollingVolatilityParameters, config: IndicatorConfig, context: IndicatorContext) -> IndicatorResult` | Rolling volatility implementation (volatility). | Missing |
| `calculate_rsi(data: pd.DataFrame, parameters: RsiParameters, config: IndicatorConfig, context: IndicatorContext) -> IndicatorResult` | Relative strength index implementation (momentum). | Missing |
| `calculate_williams_r(data: pd.DataFrame, parameters: WilliamsRParameters, config: IndicatorConfig, context: IndicatorContext) -> IndicatorResult` | Williams %R implementation (momentum). | Missing |

## FEAT-INDI-08: Execution Runtime, Backends, and Guards (app.services.indicators.runtime)

---

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `IndicatorExecutionService.calculate(indicator_id: str, data: pd.DataFrame, config: IndicatorConfig, context: IndicatorContext) -> IndicatorResult` | Orchestrated calculation coordinating optional cache/audit ports. | Implemented |
| `CalculationPipeline.execute(request: CalculationRequest) -> IndicatorResult` | Pure computation path after dependency injection (with `validate` pre-step). | Missing |
| `resolve_execution_backend(config: ExecutionBackendConfig) -> ExecutionBackend` | Lazy optional-dependency backend factory. | Missing |
| `execute_chunked(request: ValidatedCalculationRequest, backend: ExecutionBackend) -> IndicatorResult` | Chunked/out-of-core execution for large datasets. | Missing |
| `verify_backend_parity(baseline: IndicatorResult, candidate: IndicatorResult, tolerance: Tolerance) -> ParityReport` | Cross-backend numerical parity verification. | Missing |
| `ResourceGovernor.check(request: CalculationRequest) -> ResourceDecision` | Resource-limit gating (with `enforce_deadline` and `classify_partial_result` counterparts). | Missing |
| `observe_calculation(event: CalculationObservation) -> None` | Observability through injected ports (with tracing spans and redacted log fields). | Missing |
| `select_implementation(indicator_id: str, context: IndicatorContext, policy: RolloutPolicy) -> ImplementationSelection` | Rollout/canary implementation selection (with `compare_canary_result`). | Missing |
| `authorize_indicator_request(request: ProtectedIndicatorRequest, policy: AccessPolicyPort) -> AccessDecision` | Access-control decision before data/cache/state access (with `enforce_access` gate). | Missing |
| `run_indicator_benchmark(request: BenchmarkRequest) -> BenchmarkReport` | Benchmark execution with regression evaluation (`evaluate_regression`). | Missing |

## FEAT-INDI-09: Incremental Updates and State Management (app.services.indicators.incremental)

---

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `apply_incremental_update(request: IncrementalUpdateRequest) -> IncrementalUpdateResult` | Apply a per-bar incremental update returning replacement state (never mutating caller state). | Missing |
| `validate_incremental_bar(bar: Mapping[str, JsonValue], state: IndicatorState, config: IndicatorConfig) -> None` | Validate an incoming bar against current state and config. | Missing |
| `resolve_incremental_symbol_mapping(event: SymbolMappingEvent, state: IndicatorState) -> SymbolMappingStateDecision` | Handle symbol-mapping events during incremental operation (with warmup reset on discontinuity). | Missing |
| `acquire_state_lease(key: IndicatorStateKey, owner_id: str) -> StateLease` | Single-owner state coordination through an injected lease port (with `assert_single_owner` and `snapshot_state`). | Missing |

## FEAT-INDI-10: Indicator Result Caching (app.services.indicators.cache)

---

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `CacheService.resolve_or_calculate(request: CalculationRequest) -> IndicatorResult` | Cache-first resolution with strict/best-effort fault policy. | Missing |
| `IndicatorCachePort.get(key: CacheKey) -> CachedIndicatorResult \| None` | Read-only cache retrieval through an injected adapter (with atomic `put_atomic` write). | Missing |
| `build_cache_key(manifest: IndicatorManifest, lineage: CompositionLineage \| None = None) -> CacheKey` | Deterministic manifest/lineage-derived cache key. | Missing |
| `is_cache_compatible(entry: CachedIndicatorResult, request: CalculationRequest) -> bool` | Compatibility check before serving cached results. | Missing |
| `invalidate_dependent_keys(change: CacheInvalidationEvent) -> tuple[CacheKey, ...]` | Derive dependent keys to invalidate; physical eviction stays in the adapter. | Missing |
| `CacheService.cleanup_partial_artifacts(policy: CacheCleanupPolicy) -> CacheCleanupReport` | Bounded maintenance cleanup of partial cache artifacts. | Missing |

## FEAT-INDI-11: Calculation Audit Trail (app.services.indicators.audit)

---

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `build_audit_entry(manifest: IndicatorManifest, context: IndicatorContext, integrity: AuditIntegrityMetadata) -> IndicatorAuditEntry` | Build an integrity-checked calculation audit entry. | Missing |
| `AuditSinkPort.append(entry: IndicatorAuditEntry) -> AuditReceipt` | External audit persistence port. | Missing |
| `AuditService.emit_if_required(result: IndicatorResult, context: IndicatorContext, policy: AuditPolicy) -> AuditReceipt \| None` | Policy-gated audit emission through the injected sink. | Missing |
| `validate_audit_policy(policy: AuditPolicy) -> ValidationReport` | Validate audit policy; blocks production audit mode until approved. | Missing |

---

**Note:** documentation modules (`docs/indicators`), release/CI policy, and test suites defined in the plan are excluded as non-runtime capabilities. Protocol methods are shown once under contracts even though the plan repeats them across file blocks.

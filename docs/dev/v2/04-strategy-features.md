# Strategy Domain — Capability Feature Extraction (from `04-strategy.md`)

Source: `docs/dev/phase-implementation-plan/04-strategy.md`. Module paths follow the plan's target tree. Signatures not explicitly stated in the doc are inferred from its target class/function contracts. Documentation modules are omitted.

---

## FEAT-STR-01: Public Strategy API (app.services.strategies.public_api)

---

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `list_strategies(request_id: str, include_deprecated: bool = False) -> StrategyCatalogResponse` | Pure registry catalog read through the public API. | Missing |
| `describe_strategy(strategy_ref: StrategyReference, request_id: str) -> StrategyDescriptionResponse` | Describe a registered strategy's declarations and requirements. | Missing |
| `validate_strategy_config(strategy_ref: StrategyReference, config: Mapping[str, JSONValue], request_id: str) -> StrategyConfigValidationResponse` | Public configuration validation boundary. | Implemented |
| `run_vectorized_strategy_signals(request: VectorizedStrategyRequest, request_id: str) -> StrategySignalBatchResponse` | Signal-only vectorized run; mutates only ephemeral strategy-local state (no broker/portfolio/risk mutation). | Implemented |
| `create_event_strategy_session(request: EventStrategySessionRequest, request_id: str) -> EventStrategySessionHandle` | Create an isolated event-driven strategy session. | Missing |

## FEAT-STR-02: Strategy Contracts and Declarations (app.services.strategies.contracts)

---

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `build_strategy_input(context: StrategyExecutionContext, market_data: MarketDataSnapshot, indicators: IndicatorSnapshot) -> StrategyInput` | Compose the canonical strategy input contract. | Missing |
| `build_strategy_signal(input: StrategyInput, decision: StrategyDecision, provenance: SignalProvenance) -> StrategySignal` | Build a provenance-carrying strategy signal. | Missing |
| `build_trade_intent(signal: StrategySignal, instruction: IntentInstruction, lineage: IntentLineage) -> TradeIntent` | Build the trade-intent handoff contract for Risk. | Implemented |
| `validate_strategy_declarations(declarations: StrategyDeclarations) -> DeclarationValidationReport` | Validate declared strategy metadata and requirements. | Missing |
| `build_risk_profile(declarations: StrategyDeclarations) -> StrategyRiskProfile` | Derive the declared risk profile (with execution-assumption and market-state-policy builders). | Missing |
| `parse_execution_environment(value: str) -> ExecutionEnvironment` | Deterministic enum parsing (with signal-timing-policy and lifecycle-status counterparts). | Missing |
| `serialize_strategy_contract(value: StrategyContract) -> dict[str, JSONValue]` | JSON-safe contract serialization. | Missing |

## FEAT-STR-03: Strategy Registry, Resolution, and Lifecycle (app.services.strategies.registry)

---

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `register_strategy(entry: StrategyRegistryEntry, factory: StrategyFactory) -> RegistryReceipt` | Controlled registry registration. | Missing |
| `get_registered_strategy(strategy_id: str, version: str) -> RegisteredStrategy` | Pure versioned strategy lookup (with `list_registered_strategies` and `validate_catalog`). | Missing |
| `resolve_strategy(reference: StrategyReference, environment: ExecutionEnvironment, replay: ReplayContext \| None = None) -> ResolvedStrategy` | Resolve a strategy reference per environment and optional replay context. | Missing |
| `resolve_version_constraint(strategy_id: str, constraint: VersionConstraint, catalog: StrategyCatalog) -> StrategyRegistryEntry` | Deterministic version-constraint resolution with module allowlisting. | Missing |
| `evaluate_lifecycle_eligibility(entry: StrategyRegistryEntry, environment: ExecutionEnvironment, evidence: PromotionEvidence) -> LifecycleDecision` | Evidence-backed lifecycle/promotion decision (with promotion-evidence and deprecation-gate validators). | Missing |
| `build_strategy_manifest(entry: StrategyRegistryEntry, config: ValidatedStrategyConfig) -> StrategyManifest` | Build the reproducibility manifest with canonical version hash. | Missing |
| `build_provenance_manifest(entry: StrategyRegistryEntry, config: ValidatedStrategyConfig, inputs: StrategyInput) -> StrategyProvenanceManifest` | Build strategy provenance (with `verify_provenance` and approval invalidation on change). | Missing |

## FEAT-STR-04: Configuration, Readiness, and Market-Data Validation (app.services.strategies.validation)

---

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `validate_strategy_config(schema: StrategyConfigSchema, raw_config: Mapping[str, JSONValue], limits: ValidationLimits) -> ValidatedStrategyConfig` | Schema-bounded config validation with injection rejection and schema defaults. | Implemented |
| `validate_strategy_input(input: StrategyInput, requirements: StrategyDataRequirements) -> InputReadinessReport` | Input readiness check against declared data requirements. | Missing |
| `validate_indicator_readiness(indicators: IndicatorSnapshot, requirements: IndicatorRequirements) -> IndicatorReadinessReport` | Indicator warmup/availability readiness check. | Missing |
| `validate_environment_permission(entry: StrategyRegistryEntry, environment: ExecutionEnvironment) -> None` | Enforce environment permission for a registry entry. | Missing |
| `validate_market_data_snapshot(snapshot: MarketDataSnapshot, policy: DataHandlingPolicy, decision_time: datetime) -> MarketDataValidationReport` | Point-in-time market-data snapshot validation. | Missing |
| `apply_missing_data_policy(snapshot: MarketDataSnapshot, policy: MissingDataPolicy) -> MarketDataDecision` | Deterministic missing-data policy application (with clock-drift validation). | Missing |

## FEAT-STR-05: No-Lookahead Timing Enforcement (app.services.strategies.timing)

---

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `enforce_bar_open_previous_close(input: StrategyInput) -> StrategyInput` | Enforce bar-open/previous-close signal timing discipline. | Missing |
| `align_signal_to_execution(signal: StrategySignal, policy: SignalTimingPolicy) -> StrategySignal` | Align signals to the declared execution timing policy. | Missing |
| `filter_available_indicators(indicators: IndicatorSnapshot, decision_time: datetime) -> IndicatorSnapshot` | Drop indicator values unavailable at decision time. | Missing |
| `assert_point_in_time(snapshot: MarketDataSnapshot, decision_time: datetime) -> None` | Deterministic point-in-time assertion for snapshots. | Missing |
| `assert_vectorized_batch_lookahead_free(batch: VectorizedSignalBatch, decision_time: datetime) -> None` | Lookahead-free assertion for whole vectorized batches (with data-latency validation). | Missing |

## FEAT-STR-06: Strategy Runtime State, Lineage, and Resilience (app.services.strategies.runtime)

---

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `load_strategy_state(checkpoint: StrategyCheckpoint, compatibility: CheckpointCompatibility) -> StrategyState` | Strategy-local state loading (with `serialize_strategy_state` and `apply_state_update`). | Missing |
| `begin_decision_transaction(state: StrategyState, event: StrategyEvent) -> StrategyStateTransaction` | Isolated per-decision state transaction (with `commit`/`rollback` counterparts). | Missing |
| `derive_decision_id(input: StrategyInput, sequence: int) -> str` | Deterministic decision lineage IDs (with intent-ID, idempotency-key, and monotonic-sequence helpers). | Missing |
| `read_market_snapshot(port: MarketDataPort, request: MarketDataRequest, timeout: timedelta) -> MarketDataSnapshot` | Side-effect-free external reads via injected ports (with indicator and read-only execution-state counterparts). | Missing |
| `evaluate_failure_policy(event: StrategyFailureEvent, policy: StrategyFailurePolicy) -> FailurePolicyDecision` | Deterministic failure-policy decisions with dependency-failure and resource-exhaustion classification. | Missing |
| `validate_resource_profile(profile: StrategyResourceProfile) -> ResourceProfileValidationReport` | Resource budget and backpressure policy evaluation. | Missing |
| `build_strategy_checkpoint(state: StrategyState, manifest: StrategyProvenanceManifest) -> StrategyCheckpoint` | Provenance-bound checkpointing (with compatibility validation and injected-store `save_checkpoint`). | Missing |
| `handle_hard_kill(session: StrategySession, signal: HardKillSignal) -> HardKillResult` | Hard-kill handling with local pending-intent cancellation and diagnostics. | Missing |

## FEAT-STR-07: Signal Execution Engines and Output Boundary (app.services.strategies.execution)

---

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `run_vectorized_strategy_signals(request: VectorizedStrategyRequest, resolved: ResolvedStrategy) -> VectorizedStrategyResult` | Vectorized signal generation in ephemeral strategy-local state. | Implemented |
| `shift_current_bar_conditions(frame: StrategyFeatureFrame, policy: SignalTimingPolicy) -> StrategyFeatureFrame` | Shift current-bar conditions per timing policy (with `abort_batch_on_lookahead`). | Missing |
| `convert_signals_to_intents(signals: VectorizedSignalBatch, context: StrategyExecutionContext) -> tuple[TradeIntent, ...]` | Convert validated signals into trade intents. | Missing |
| `validate_strategy_output(output: StrategyHookResult) -> ValidatedStrategyOutput` | Output boundary validation rejecting external-authority mutation; emits trade intents only. | Missing |
| `invoke_hook(strategy: StrategyProtocol, hook: HookName, input: StrategyInput) -> StrategyHookResult` | Hook invocation in strategy-local state (with `resolve_hook_order` and `validate_supported_hook`). | Missing |
| `create_event_session(resolved: ResolvedStrategy, context: StrategyExecutionContext) -> StrategySession` | Isolated event-session creation (with `dispatch_strategy_event` and read-only snapshot attachment). | Missing |
| `order_strategy_events(events: Sequence[StrategyEvent]) -> tuple[StrategyEvent, ...]` | Deterministic event ordering with bounded-queue enqueue and backpressure. | Missing |
| `run_in_isolated_worker(port: StrategyWorkerPort, request: IsolatedWorkerRequest) -> VectorizedStrategyResult` | Isolated-worker execution through an injected port. | Missing |

## FEAT-STR-08: Deterministic Strategy Error Codes and Mapping (app.services.strategies.errors)

---

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `strategy_error_code(value: str) -> StrategyErrorCode` | Parse/validate supported strategy error codes. | Missing |
| `map_exception_to_strategy_error(error: Exception, context: ErrorMappingContext) -> StrategyDomainError` | Deterministic exception-to-domain-error mapping (with lookahead-specific mapping). | Missing |
| `build_safe_error_response(error: StrategyDomainError, request_id: str) -> StrategyErrorResponse` | Redacted, request-traceable error response construction. | Missing |

## FEAT-STR-09: Sandbox Entry Gate and Security Policy (app.services.strategies.sandbox)

---

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `reject_raw_strategy_code(request: StrategyRequest) -> None` | Reject raw code submission; only allowlisted entry paths run (with entry-path validation and diagnostics). | Missing |
| `validate_sandbox_metadata(metadata: SandboxMetadata, at: datetime) -> SandboxValidationReport` | Validate sandbox metadata and profile (with environment-access and profile validators). | Missing |
| `assert_no_secret_material(value: JSONValue, location: SecretBearingLocation) -> None` | Block secret material in strategy payloads. | Missing |
| `redact_strategy_diagnostic(diagnostic: StrategyDiagnostic) -> StrategyDiagnostic` | Redact diagnostics before emission (with security rejection events). | Missing |

## FEAT-STR-10: Strategy Diagnostics and Metrics (app.services.strategies.observability)

---

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `build_strategy_diagnostic(event: DiagnosticEvent, context: DiagnosticContext) -> StrategyDiagnostic` | Build bounded, trace-attached strategy diagnostics (with size validation). | Missing |
| `build_strategy_metric_set(event: StrategyEventResult) -> tuple[StrategyMetric, ...]` | Derive metric sets from strategy event results. | Missing |
| `emit_strategy_metrics(port: MetricsPort, metrics: Sequence[StrategyMetric]) -> None` | Emit metrics through an injected metrics port. | Missing |

## FEAT-STR-11: Governance Artifacts and Production Sign-Off (app.services.strategies.governance)

---

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `build_strategy_validation_artifact(request: StrategyValidationArtifactRequest) -> StrategyValidationArtifact` | Build validation artifacts binding optimized configurations by hash. | Missing |
| `validate_build_artifact(artifact: StrategyBuildArtifact) -> BuildArtifactValidationReport` | Validate build artifacts and quality-gate evidence. | Missing |
| `validate_calibration_policy(policy: CalibrationPolicy) -> PolicyValidationReport` | Validate calibration and performance-review policies. | Missing |
| `validate_production_signoff(evidence: ProductionReadinessEvidence) -> ProductionReadinessReport` | Production readiness sign-off validation (with recovery-assumption derivation). | Missing |

---

**Note:** the operating-manual documentation module is excluded as a non-runtime capability. Strategies emit signals and trade intents only; all trading, risk, and portfolio authority lives in downstream governed domains.

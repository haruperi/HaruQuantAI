# Simulator Domain — Capability Feature Extraction (from `08-simulator.md`)

Source: `docs/dev/phase-implementation-plan/08-simulator.md`. Module paths follow the plan's target tree. Documentation, test, and example modules are omitted.

---

## FEAT-SIM-01: Official Backtest Tool Surface (app.services.simulator.api)

---

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `run_backtest(request: BacktestRequest, *, actor_context: ActorContext \| None = None) -> ToolEnvelope[SimulatorResult]` | Official entry point: create/schedule a run and persist audit-safe artifacts; exported via the package gate. | Implemented |
| `reject_arbitrary_strategy_code(payload: Mapping[str, JsonValue]) -> ValidationIssue \| None` | Block arbitrary strategy code submission at the tool boundary. | Missing |
| `validate_actor_context(actor_context: ActorContext \| None, surface: InvocationSurface) -> AuthorizationDecision` | Authorization decision per invocation surface. | Missing |

## FEAT-SIM-02: Simulator Contracts, Enums, and Errors (app.services.simulator.contracts)

---

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `validate_backtest_request(value: BacktestRequest) -> BacktestRequest` | Validate the canonical backtest request contract. | Missing |
| `build_immutable_run_config(request: BacktestRequest, dependencies: RunDependencies) -> ImmutableRunConfig` | Freeze the reproducible run configuration. | Missing |
| `build_simulator_result(snapshot: CompletedRunSnapshot) -> SimulatorResult` | Build the standard simulator result (with `serialize_contract` JSON-safe serialization). | Missing |
| `make_sim_error(code: SimulatorErrorCode, message: str, *, severity: Severity, retryable: bool, field_path: str \| None = None) -> SimulatorError` | Deterministic simulator error construction (with catalogue validation). | Missing |
| `validate_extension_contract(extension: ExtensionDescriptor) -> ExtensionDescriptor` | Validate declared extension contracts. | Missing |

## FEAT-SIM-03: Config, Strategy, Data-Quality, and Schema Validation (app.services.simulator.validation)

---

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `validate_simulator_config(config: SimulatorConfig, profile: BrokerProfile) -> ValidationReport` | Config validation against the broker profile (with canonicalization and resume compatibility). | Missing |
| `validate_strategy_reference(reference: StrategyReference, registry: StrategyRegistryPort) -> RegisteredStrategy` | Resolve strategy references through the external registry (with sandbox-metadata validation and code-injection detection). | Missing |
| `inspect_dataset(data: MarketDataSlice, policy: DataQualityPolicy) -> DataQualityReport` | Dataset quality inspection (with data-authority validation and survivorship-bias detection). | Missing |
| `validate_input_schema(payload: Mapping[str, JsonValue], schema: SchemaVersion) -> ValidationReport` | Versioned input-schema validation (with size limits and safe-path validation). | Missing |
| `validate_parameters(parameters: Mapping[str, JsonValue], limits: ParameterLimits) -> ValidationReport` | Parameter-limit validation (with symbol-precision checks). | Missing |

## FEAT-SIM-04: Run Orchestration, Scheduling, and Recovery (app.services.simulator.orchestration)

---

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `BacktestOrchestrator.run(request: BacktestRequest, actor_context: ActorContext \| None) -> SimulatorResult` | Full run coordination delegating to journal/scheduler ports (with dependency validation and lifecycle advancement). | Missing |
| `enqueue_run(plan: RunPlan) -> QueueReceipt` | Persistent run scheduling (with `claim_work`, `cancel_run`, and `requeue_lost_work`). | Missing |
| `create_checkpoint(state: EngineState, context: RunContext) -> RunCheckpoint` | Checkpointing through the injected store (with verification and restore). | Missing |
| `classify_work_failure(error: ExceptionInfo, attempts: int, policy: RetryPolicy) -> FailureDisposition` | Worker failure classification with quarantine and recovery diagnostics. | Missing |

## FEAT-SIM-05: Event-Driven Execution Engine (app.services.simulator.engine)

---

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `EventDrivenExecutionEngine.run(plan: ExecutionPlan, state: EngineState) -> CompletedRunState` | Deterministic in-memory run execution emitting journal records through the port. | Missing |
| `EventDrivenExecutionEngine.process_tick(tick: Tick, state: EngineState) -> EngineStepResult` | Per-tick processing (with `apply_event` and read-only `snapshot`). | Missing |
| `create_engine_state(config: ImmutableRunConfig) -> EngineState` | Engine state construction (with pure `apply_state_transition` and read-only snapshots). | Missing |
| `prove_batch_safe(interval: TickInterval, state: ReadOnlyExecutionStateSnapshot, boundaries: BoundarySet) -> BatchSafetyDecision` | Prove tick-batching safety before skipping per-tick evaluation (with next-boundary computation). | Missing |

## FEAT-SIM-06: Strategy Integration Adapter (app.services.simulator.integration)

---

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `build_strategy_context(snapshot: ReadOnlyExecutionStateSnapshot, data: DecisionDataView) -> StrategyDecisionContext` | Build the read-only decision context for strategies. | Missing |
| `request_trade_intents(strategy: RegisteredStrategy, context: StrategyDecisionContext) -> tuple[TradeIntent, ...]` | External strategy invocation returning trade intents only. | Missing |
| `compile_signal_timeline(intents: Sequence[TradeIntent], timing: TimingPolicy) -> SignalTimeline` | Compile intents into a lookahead-safe signal timeline. | Missing |

## FEAT-SIM-07: Market Simulation — Ticks, Order Book, Calendar, FX (app.services.simulator.market)

---

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `build_tick_stream(data: MarketDataSlice, config: TickModelConfig, seed: SeedMaterial) -> TickStream` | Deterministic tick-stream construction (with order validation and price normalization). | Missing |
| `generate_synthetic_ticks(bar: OHLCVBar, spec: SymbolSpec, seed: int, model: SyntheticTickModel) -> tuple[Tick, ...]` | Seeded synthetic tick generation from bars (with per-bar seed derivation and metadata). | Missing |
| `validate_order_book(book: OrderBookSnapshot, policy: OrderBookPolicy) -> ValidationReport` | Order-book snapshot validation with read-only views. | Missing |
| `market_state_at(symbol: Symbol, at: UtcTimestamp, calendar: MarketCalendar) -> MarketState` | Calendar/session state resolution (with tick-state validation and next-boundary lookup). | Missing |
| `resolve_fx_rate(request: FxConversionRequest, rates: FxRateBook) -> FxRateResolution` | FX conversion resolution with cross-rate skew validation. | Missing |

## FEAT-SIM-08: Order Execution and Matching (app.services.simulator.execution)

---

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `validate_order_request(order: OrderRequest, profile: BrokerProfile, state: ReadOnlyExecutionStateSnapshot) -> ValidationReport` | Profile-aware order validation. | Missing |
| `create_order(intent: SizedOrderIntent, at: UtcTimestamp) -> SimulatedOrder` | Order creation and deterministic state transitions. | Missing |
| `match_order(order: SimulatedOrder, tick: Tick, context: MatchingContext) -> MatchDecision` | Tick-level matching (with fillable-volume determination and deal construction). | Implemented |
| `reprice_pegged_order(order: SimulatedOrder, book: ReadOnlyOrderBookView, policy: PegPolicy) -> RepriceDecision` | Advanced orders: pegged repricing, trailing-stop updates, stop-limit triggers. | Missing |
| `evaluate_pending_orders(tick: Tick, state: ReadOnlyExecutionStateSnapshot) -> tuple[OrderEvent, ...]` | Pending/protective order lifecycle evaluation with ambiguous SL/TP policy and cancellation. | Missing |

## FEAT-SIM-09: Broker Profiles (app.services.simulator.broker_profiles)

---

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `load_broker_profile(profile_id: str, repository: BrokerProfileRepository) -> BrokerProfile` | Repository-backed broker profile loading. | Missing |
| `validate_broker_profile(profile: BrokerProfile) -> ValidationReport` | Profile validation (with stable `hash_broker_profile` for reproducibility). | Missing |

## FEAT-SIM-10: Portfolio Accounting, Positions, Margin, and Corporate Actions (app.services.simulator.portfolio)

---

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `apply_deal_accounting(account: AccountState, deal: SimulatedDeal, costs: DealCosts) -> AccountState` | Deal accounting with mark-to-market and NAV calculation. | Missing |
| `apply_fill_to_positions(positions: PositionBook, deal: SimulatedDeal, mode: PositionMode) -> PositionBook` | Hedging/netting position bookkeeping (with close results and snapshots). | Missing |
| `calculate_required_margin(order: SizedOrderIntent, account: AccountState, symbol: SymbolSpec, price: Decimal) -> Decimal` | Margin requirements with stop-out evaluation and liquidation planning. | Missing |
| `apply_split(position: SimulatedPosition, action: SplitAction) -> SimulatedPosition` | Corporate actions: splits, futures rolls, forced buy-ins. | Missing |

## FEAT-SIM-11: Trading Cost Models (app.services.simulator.costs)

---

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `resolve_spread(tick: Tick, model: SpreadModel, context: SpreadContext) -> SpreadQuote` | Spread modeling with policy validation. | Missing |
| `calculate_slippage(order: SimulatedOrder, executable_price: Decimal, context: SlippageContext) -> SlippageResult` | Slippage modeling with limit validation. | Missing |
| `calculate_commission(deal: SimulatedDeal, schedule: CommissionSchedule) -> CommissionResult` | Commission and pass-through fee calculation. | Missing |
| `calculate_swap(position: SimulatedPosition, at: UtcTimestamp, schedule: SwapSchedule) -> SwapAccrual` | Swap and funding accrual. | Missing |
| `calculate_arrival_time(submitted_at: UtcTimestamp, model: LatencyModel, seed: int) -> UtcTimestamp` | Seeded latency modeling with diagnostics. | Missing |
| `resolve_available_liquidity(order: SimulatedOrder, market: MarketLiquidityView, model: LiquidityModel) -> LiquiditySnapshot` | Liquidity modeling with order-book walking and capacity diagnostics. | Missing |

## FEAT-SIM-12: Simulated Risk and Compliance Controls (app.services.simulator.controls)

---

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `evaluate_simulated_risk_rules(intent: TradeIntent, snapshot: ReadOnlyExecutionStateSnapshot, rules: SimulatorRiskRuleSet) -> SimulatedRiskDecision` | In-simulation risk rule evaluation. | Missing |
| `evaluate_kill_switch(state: ReadOnlyExecutionStateSnapshot, policy: KillSwitchSimulationPolicy) -> KillSwitchDecision` | Simulated kill-switch behavior. | Missing |
| `evaluate_market_halt(symbol: Symbol, at: UtcTimestamp, market_state: MarketState) -> ComplianceDecision` | Market-halt and regulatory-restriction compliance decisions. | Missing |

## FEAT-SIM-13: Append-Only Journal and Artifacts (app.services.simulator.journal)

---

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `append_record(record: JournalRecord, store: JournalStore) -> JournalReceipt` | Append-only journaling with sequence and hash-chain verification. | Missing |
| `write_artifact(artifact: ArtifactPayload, root: SafeArtifactPath, policy: ArtifactPolicy) -> ArtifactReceipt` | Safe artifact persistence with checksums and failure-artifact preservation. | Missing |
| `build_journal_manifest(context: RunContext, artifacts: Sequence[ArtifactReceipt]) -> JournalManifest` | Run manifest construction and verification. | Missing |
| `evaluate_retention(record: ArtifactRecord, policy: RetentionPolicy, now: UtcTimestamp) -> RetentionDecision` | Retention policy evaluation and application. | Missing |

## FEAT-SIM-14: Run Metrics, Scorecards, and Realism Disclosure (app.services.simulator.reporting)

---

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `calculate_run_metrics(snapshot: CompletedRunSnapshot, config: ReportConfig) -> SimulatorMetrics` | Run metric computation (with drawdown and trade statistics). | Missing |
| `build_scorecard(result: SimulatorResult, evidence: EvidenceBundle) -> SimulatorScorecard` | Evidence-backed scorecard with realism classification. | Missing |
| `build_realism_disclosure(config: ImmutableRunConfig, evidence: EvidenceBundle) -> RealismDisclosure` | Explicit disclosure of simulation realism assumptions. | Missing |
| `render_json_report(report: SimulatorReport) -> dict[str, JsonValue]` | Report rendering (JSON, Markdown, visualization payload). | Missing |

## FEAT-SIM-15: Operations — Telemetry, Quotas, Environment, Security, Canary (app.services.simulator.operations)

---

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `instrument_run(operation: Callable[..., T]) -> Callable[..., T]` | Decorator boundary for logging, metrics, timing, and tracing (with redacted telemetry). | Missing |
| `enforce_resource_quota(request: BacktestRequest, usage: ResourceUsage, policy: ResourceQuotaPolicy) -> QuotaDecision` | Resource quota and deadline enforcement. | Missing |
| `build_environment_hash(context: EnvironmentContext) -> str` | Environment hashing with benchmark drift comparison and performance gating. | Missing |
| `require_role(actor: ActorContext, required: Permission) -> AuthorizationDecision` | Role-based authorization (with metadata redaction and supply-chain evidence validation). | Missing |
| `select_canary_route(context: CanaryContext, policy: CanaryPolicy) -> CanaryDecision` | Canary routing and baseline/candidate result comparison. | Missing |

## FEAT-SIM-16: Parity and Contract Verification (app.services.simulator.verification)

---

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `compare_mt5_parity(result: SimulatorResult, fixture: Mt5ParityFixture) -> ParityReport` | MT5 behavioral parity comparison (with typed `assert_mt5_parity`). | Missing |
| `validate_port_contract(port: object, contract: type[Protocol]) -> ValidationReport` | Injected-port contract verification (with provider contract suite over fixtures). | Missing |

---

**Note:** documentation modules (`docs/simulator`), test suites, and runnable examples in the plan are excluded as non-runtime capabilities. The simulator never mutates broker state; strategies interact only through the read-only adapter context and trade intents.

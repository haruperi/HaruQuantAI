# Risk Domain — Capability Feature Extraction (from `05-risk.md`)

Source: `docs/dev/phase-implementation-plan/05-risk.md` (Risk Governance ARD V2). Module paths follow the plan's target tree. Signatures not explicitly stated in the doc are inferred from its target class/function contracts.

---

## FEAT-RISK-01: Delivery Readiness and Mode-Matrix Validation (app.services.risk.readiness)

---

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `validate_phase_dependencies(dependencies: Mapping[str, DependencyStatus]) -> ReadinessAssessment` | Validate canonical contracts, side-effect safety, ports, and test availability of upstream phases. | Missing |
| `validate_risk_mode_matrix(matrix: RiskModeMatrix) -> ValidationResult` | Validate policy coverage across offline, simulation, paper, shadow, read-only-live, micro-live, and full-live modes. | Missing |
| `build_readiness_dry_run(manifest: RiskReadinessManifest) -> DryRunReport` | Produce files-to-read/change, commands, scope, blockers, and rollback points. | Missing |
| `validate_delivery_plan(plan: ReadinessDeliveryPlan) -> ValidationResult` | Validate traceability, fixtures, seeds, redaction, tool classification, and audit failure policy. | Missing |

## FEAT-RISK-02: Canonical Risk Models and Serialization (app.services.risk.models)

---

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `RiskDecisionStatus` / `RiskReasonCode` / `RiskSeverity` | Deterministic decision-status, reason-code, and ordered-severity catalogs (`approve`, `reduce_size`, `reject`, `block`, `needs_more_evidence`, `needs_approval`, `halt_strategy`, `halt_all`). | Missing |
| `validate_risk_assessment_request(request: RiskAssessmentRequest) -> ValidationResult` | Reject missing or invalid canonical evidence before calculation (with ProposedTrade, ProposedAllocation, StrategyAdmissionRequest, RiskDecisionPackage contracts). | Missing |
| `to_canonical_risk_payload(model: RiskSerializable) -> dict[str, JsonValue]` | Emit stable JSON-safe fields for canonical risk models (with `from_canonical_risk_payload` and round-trip validation). | Missing |
| `list_risk_reason_codes() -> tuple[RiskReasonCode, ...]` | Return the stable reason-code catalogue in deterministic order (with `risk_severity_rank`). | Missing |

## FEAT-RISK-03: Risk Configuration Profiles and Hashing (app.services.risk.config)

---

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `validate_risk_config(config: RiskConfig) -> ValidationResult` | Reject unknown keys, unsafe thresholds, and live profiles missing explicit authority. | Missing |
| `load_risk_config(profile_name: str, source: RiskConfigSource) -> RiskConfig` | Read an explicitly injected configuration source and validate the selected profile. | Implemented |
| `build_safe_default_profile() -> RiskConfig` | Approved offline/simulation baseline (with prop-firm, paper, and live-conservative profile builders). | Missing |
| `get_builtin_risk_profile(name: str) -> RiskConfig` | Resolve an approved built-in profile deterministically (with `list_builtin_risk_profiles`). | Missing |
| `hash_risk_config(config: RiskConfig) -> str` | Stable canonical config hash for decisions, tokens, audit, and replay (with comparison and validation helpers). | Missing |

## FEAT-RISK-04: Policy Resolution, Precedence, and Overrides (app.services.risk.policy)

---

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `resolve_effective_policy(context: PolicyContext, policies: Sequence[RiskPolicy]) -> EffectiveRiskPolicy` | Apply approved scope/precedence rules or fail closed. | Missing |
| `evaluate_risk_budget(policy: EffectiveRiskPolicy, request: RiskAssessmentRequest) -> PolicyEnforcementResult` | Evaluate policy budget gates. | Missing |
| `validate_policy_expiry(policy: RiskPolicy, now_utc: datetime) -> ValidationResult` | Validate time-bounded policies (with `validate_policy_scope`). | Missing |
| `validate_risk_override_request(request: RiskOverrideRequest, policy: EffectiveRiskPolicy) -> OverrideValidationResult` | Validate override scope and maximum threshold bounds (with `requires_override_approval`). | Missing |
| `validate_token_config_compatibility(token: RiskDecisionToken, config_hash: str) -> ValidationResult` | Reject configuration-incompatible approval tokens. | Missing |

## FEAT-RISK-05: Market Regime Assessment (app.services.risk.regime)

---

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `assess_risk_regime(market: MarketRiskSnapshot, policy: EffectiveRiskPolicy, now_utc: datetime) -> RegimeAssessment` | Classify spread, volatility, liquidity, session, rollover, and news conditions. | Implemented |
| `classify_spread_regime(spread: Decimal, sigma: Decimal, thresholds: SpreadSigmaThresholds) -> RiskRegime` | Classify spread-to-volatility condition (with `classify_volatility_regime`). | Missing |
| `validate_market_freshness(market: MarketRiskSnapshot, policy: EffectiveRiskPolicy, now_utc: datetime) -> ValidationResult` | Detect stale or inconsistent market evidence. | Missing |
| `is_rollover_blackout(server_time: datetime, policy: EffectiveRiskPolicy) -> bool` | Evaluate broker-midnight blackout boundaries. | Missing |
| `validate_regime_inputs(market: MarketRiskSnapshot) -> ValidationResult` | Reject invalid bid/ask, stale quotes, or missing calendar/session evidence (with stable regime reason codes). | Missing |

## FEAT-RISK-06: Ordered Limit Checks and Aggregation (app.services.risk.limits)

---

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `check_kill_switch(state: KillSwitchState) -> LimitResult` | Block when a relevant kill switch is active or uncertain. | Missing |
| `check_evidence_freshness(request: RiskAssessmentRequest, policy: EffectiveRiskPolicy, now_utc: datetime) -> LimitResult` | Block stale or incomplete mandatory evidence. | Missing |
| `check_daily_loss(snapshot: PortfolioRiskSnapshot, policy: EffectiveRiskPolicy) -> LimitResult` | Evaluate the daily-loss budget (with total-drawdown ceiling counterpart). | Missing |
| `check_exposure_limits(projected: ProjectedRiskSnapshot, policy: EffectiveRiskPolicy) -> tuple[LimitResult, ...]` | Evaluate portfolio, symbol, currency, and cluster limits. | Missing |
| `check_tail_risk_limits(var: VaRSnapshot, es: ExpectedShortfallSnapshot, stress: StressSummary, policy: EffectiveRiskPolicy) -> tuple[LimitResult, ...]` | Evaluate VaR, Expected Shortfall, and stress limits. | Missing |
| `check_execution_limits(execution: ExecutionRiskSnapshot, policy: EffectiveRiskPolicy) -> tuple[LimitResult, ...]` | Evaluate spread, slippage, frequency, pending-order, news, and rollover limits. | Missing |
| `evaluate_ordered_limits(context: LimitContext, checks: tuple[LimitCheck, ...]) -> LimitAssessment` | Run the immutable check sequence and aggregate outcomes (with primary-failure selection and composite breach flags). | Missing |

## FEAT-RISK-07: Position Sizing and Volume Normalization (app.services.risk.sizing)

---

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `calculate_fixed_risk_size(request: PositionSizingRequest) -> PositionSizingResult` | Size from a fixed monetary risk budget. | Missing |
| `calculate_fixed_fractional_size(request: PositionSizingRequest) -> PositionSizingResult` | Size from permitted equity fraction. | Missing |
| `calculate_volatility_adjusted_size(request: PositionSizingRequest) -> PositionSizingResult` | Volatility-adjusted sizing using M1 σ/ATR/approved inputs. | Missing |
| `calculate_correlation_adjusted_size(request: PositionSizingRequest, correlation: CorrelationImpact) -> PositionSizingResult` | Reduce size for correlated portfolio exposure. | Missing |
| `calculate_milestone_size(request: PositionSizingRequest, milestones: Sequence[RiskMilestone]) -> PositionSizingResult` | Apply approved milestone constraints. | Missing |
| `calculate_kelly_reference_size(request: PositionSizingRequest, evidence: KellyEvidence) -> AdvisorySizingResult` | Advisory-only Kelly reference size. | Missing |
| `calculate_stop_distance(request: PositionSizingRequest) -> Decimal` | Convert σ/ATR/pip/tick stop definitions into a distance (with account-currency risk conversion). | Missing |
| `normalize_volume(size: Decimal, symbol: SymbolRiskMetadata) -> Decimal` | Floor/round only by approved lot-step and precision rules (with metadata and normalized-volume validation and deterministic rejection evidence). | Missing |

## FEAT-RISK-08: FX Leg Decomposition and Currency Exposure (app.services.risk.exposure)

---

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `parse_fx_symbol(symbol: str, metadata: SymbolRiskMetadata) -> FxPair` | Validate canonical base/quote currency identity. | Missing |
| `decompose_fx_trade(trade: ProposedTrade, price: Decimal, contract: ContractSpecification) -> tuple[CurrencyLegExposure, CurrencyLegExposure]` | Emit signed base and quote currency legs. | Missing |
| `calculate_currency_exposure(positions: Sequence[PositionRiskSnapshot], pending: Sequence[PendingOrderRiskSnapshot], proposal: ProposedTrade \| None, rates: Mapping[CurrencyPair, Decimal], account_currency: str) -> CurrencyExposure` | Compute current and projected currency exposure. | Missing |
| `calculate_gross_and_net_exposure(exposure: Mapping[str, Decimal]) -> ExposureTotals` | Deterministic gross/net exposure (with leg aggregation, conversion-evidence validation, and currency rounding). | Missing |

## FEAT-RISK-09: Correlation, Clustering, and Fallbacks (app.services.risk.correlation)

---

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `build_return_series(bars: Sequence[ClosedBar], method: ReturnMethod) -> ReturnSeries` | Derive log, close-to-close, open-to-close, or σ-normalized returns. | Missing |
| `align_return_series(series: Mapping[str, ReturnSeries], policy: CorrelationAlignmentPolicy) -> AlignedReturns` | Align identical opening timestamps with documented missing-data treatment (with input validation). | Missing |
| `calculate_correlation_matrix(returns: AlignedReturns, method: CorrelationMethod) -> CorrelationSnapshot` | Reproducible correlation matrix with metadata. | Missing |
| `build_correlation_clusters(snapshot: CorrelationSnapshot, threshold: Decimal) -> tuple[CorrelationCluster, ...]` | Identify shared-risk clusters (with cluster-exposure concentration assessment). | Missing |
| `resolve_correlation_fallback(context: CorrelationFallbackContext, policy: EffectiveRiskPolicy) -> CorrelationSnapshot` | Approved conservative fallback or explicit rejection (with fail-closed decision helper). | Missing |
| `calculate_component_risk_contribution(covariance: CovarianceMatrix, weights: Sequence[Decimal]) -> ComponentRiskContribution` | Component risk-contribution evidence. | Missing |

## FEAT-RISK-10: Value-at-Risk and Expected Shortfall (app.services.risk.tail_risk)

---

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `calculate_parametric_var(request: VaRCalculationRequest) -> VaRSnapshot` | Covariance/volatility-based VaR. | Missing |
| `calculate_historical_var(request: VaRCalculationRequest) -> VaRSnapshot` | Empirical VaR from aligned historical returns. | Missing |
| `calculate_portfolio_volatility(covariance: CovarianceMatrix, weights: Sequence[Decimal]) -> Decimal` | Portfolio volatility calculation. | Missing |
| `calculate_var_component_contribution(request: VaRCalculationRequest) -> ComponentRiskContribution` | Decompose VaR contribution. | Missing |
| `calculate_expected_shortfall(request: ExpectedShortfallRequest) -> ExpectedShortfallSnapshot` | Average loss beyond the approved tail threshold (with deterministic tail-loss selection). | Missing |
| `validate_tail_risk_assumptions(var: VaRSnapshot, es: ExpectedShortfallSnapshot, policy: EffectiveRiskPolicy) -> ValidationResult` | Reject invalid or insufficient tail evidence. | Missing |

## FEAT-RISK-11: Declarative Stress Testing (app.services.risk.stress)

---

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `build_default_stress_registry() -> StressScenarioRegistry` | Approved default scenario set. | Missing |
| `register_stress_scenario(registry: StressScenarioRegistry, scenario: StressScenario) -> StressScenarioRegistry` | Duplicate- and safety-validated scenario registration (with deterministic lookup). | Missing |
| `validate_custom_scenario_definition(scenario: Mapping[str, JsonValue]) -> StressScenario` | Reject imperative or arbitrary-code scenario constructs. | Missing |
| `evaluate_stress_scenarios(context: StressContext, registry: StressScenarioRegistry, policy: EffectiveRiskPolicy) -> StressSummary` | Evaluate all applicable scenarios. | Missing |
| `apply_market_shock(portfolio: ProjectedPortfolio, scenario: StressScenario) -> ProjectedPortfolio` | Apply declarative price/cost/liquidity shocks (with account-currency loss and policy comparison). | Missing |

## FEAT-RISK-12: Margin, Drawdown, and Execution Feasibility (app.services.risk.feasibility)

---

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `calculate_current_margin_usage(account: AccountRiskSnapshot, portfolio: PortfolioRiskSnapshot) -> MarginRiskSnapshot` | Current margin state (with post-proposal projection). | Missing |
| `calculate_free_margin_after_reservations(account: AccountRiskSnapshot, pending: Sequence[PendingOrderRiskSnapshot], inflight: Sequence[InFlightOrderRiskSnapshot]) -> Decimal` | Reserve pending/in-flight exposure (with `check_margin_limits`). | Missing |
| `determine_drawdown_state(snapshot: PortfolioRiskSnapshot, prior: DrawdownState \| None, policy: EffectiveRiskPolicy) -> DrawdownState` | Classify normal/caution/defensive/recovery/halted state. | Missing |
| `apply_drawdown_throttle(size: Decimal, state: DrawdownState, policy: EffectiveRiskPolicy) -> Decimal` | Reduce sizing by the approved step-down multiplier. | Missing |
| `assess_execution_feasibility(trade: ProposedTrade, market: MarketRiskSnapshot, metadata: SymbolRiskMetadata, policy: EffectiveRiskPolicy) -> ExecutionRiskSnapshot` | Execution feasibility with reason codes. | Missing |
| `validate_stop_and_freeze_levels(trade: ProposedTrade, metadata: SymbolRiskMetadata) -> ValidationResult` | Validate stop/freeze geometry (with M1 spread/slippage-to-σ micro-scalping cost limits). | Missing |

## FEAT-RISK-13: Allocation, Lifecycle, and Kill-Switch Governance (app.services.risk.governance)

---

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `review_allocation_proposal(request: ProposedAllocation, portfolio: PortfolioRiskSnapshot, policy: EffectiveRiskPolicy) -> AllocationAssessment` | Evaluate strategy/symbol/currency/portfolio budgets. | Implemented |
| `calculate_equal_risk_allocation(items: Sequence[AllocatableRisk]) -> AllocationPlan` | Equal-risk allocation (with volatility-parity and correlation-adjusted variants). | Missing |
| `apply_regime_and_drawdown_adjustments(plan: AllocationPlan, regime: RegimeAssessment, drawdown: DrawdownState) -> AllocationPlan` | Deterministic policy multipliers on allocation plans. | Missing |
| `review_strategy_admission(request: StrategyAdmissionRequest, policy: EffectiveRiskPolicy) -> LifecycleAssessment` | Check mandatory research/simulation/risk evidence (with live-readiness review and transition validation). | Implemented |
| `check_risk_kill_switch(scope: KillSwitchScope, state: KillSwitchState) -> KillSwitchAssessment` | Determine active/unknown/locked/pending-resume status. | Implemented |
| `request_kill_switch_trigger(request: KillSwitchTriggerRequest, store: RiskStateStore) -> KillSwitchState` | Record a governed kill-switch transition (store write only; no broker mutation). | Missing |
| `validate_resume_request(request: KillSwitchResumeRequest, state: KillSwitchState, approval: ApprovalContext \| None) -> ValidationResult` | Require governed approval before resume (with approved-resume persistence). | Missing |

## FEAT-RISK-14: Risk Governor Orchestration and Decision Synthesis (app.services.risk.governor)

---

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `RiskGovernor.review_trade(request: RiskAssessmentRequest) -> RiskDecisionPackage` | Fixed fail-closed pre-trade decision flow; never broker-mutating. | Missing |
| `RiskGovernor.review_allocation(request: RiskAssessmentRequest) -> RiskDecisionPackage` | Governed allocation review (with strategy-admission and live-readiness counterparts). | Missing |
| `RiskGovernor.run_portfolio_risk_governor(request: RiskAssessmentRequest) -> RiskDecisionPackage` | Portfolio-risk review without execution. | Implemented |
| `synthesize_decision(context: GovernorEvaluationContext) -> RiskDecisionPackage` | Create approve/reduce/reject/block/evidence/approval/halt outcomes from ordered results. | Missing |
| `determine_decision_status(results: Sequence[GateResult], policy: EffectiveRiskPolicy) -> RiskDecisionStatus` | Apply halt > block > reject > evidence > approval > reduce > approve precedence (with primary-reason selection and reduction aggregation). | Missing |
| `is_decision_token_eligible(decision: RiskDecisionPackage) -> bool` | True only for bounded approved/reduced outcomes. | Missing |

## FEAT-RISK-15: Tamper-Evident Audit Chain and Approval Tokens (app.services.risk.audit)

---

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `create_risk_audit_event(decision: RiskDecisionPackage, context: AuditContext) -> RiskAuditEvent` | Immutable audit record from canonical redacted payload material. | Missing |
| `append_audit_hash(previous_hash: str, payload: Mapping[str, JsonValue]) -> str` | Deterministic chain hash (with genesis hash builder). | Missing |
| `verify_risk_audit_chain(events: Sequence[RiskAuditEvent]) -> AuditChainVerification` | Validate genesis, sequence continuity, payload hashes, and tamper state (with live-mode fail-closed requirement). | Missing |
| `create_risk_decision_token(decision: RiskDecisionPackage, signer: RiskDecisionTokenSigner, now_utc: datetime) -> RiskDecisionToken` | Sign an eligible bounded approval. | Missing |
| `validate_risk_approval_token(token: RiskDecisionToken, context: TokenValidationContext, verifier: RiskDecisionTokenSigner) -> TokenValidationResult` | Check signature, expiry, revocation, scope, policy hash, config hash, and schema (with expiry and scope validators). | Missing |

## FEAT-RISK-16: Risk State, Decision, and Audit Storage Ports (app.services.risk.storage)

---

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `RiskStateStore` / `RiskAuditSink` / `RiskPolicyStore` / `RiskDecisionStore` | Typed ports for kill-switch/drawdown state, audit append, policy reads, and idempotent decision persistence. | Missing |
| `persist_risk_decision(decision: RiskDecisionPackage, key: DecisionIdempotencyKey, store: RiskDecisionStore) -> PersistenceResult` | Same-material duplicate/no-op and different-material rejection semantics. | Missing |
| `validate_storage_schema_compatibility(record: StoredRiskRecord, expected_version: str) -> ValidationResult` | Validate stored record compatibility (with mandatory live audit-persistence check). | Missing |
| `create_in_memory_risk_store() -> InMemoryRiskStateStore` | Isolated test/simulation storage (with deterministic fault injection support). | Missing |

## FEAT-RISK-17: Risk Reports and Authorized Export (app.services.risk.reports)

---

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `generate_risk_report(evidence: RiskReportEvidence, options: RiskReportOptions) -> RiskReport` | JSON-safe report from stored evidence without recomputation. | Implemented |
| `redact_risk_report(report: RiskReport, policy: ReportRedactionPolicy) -> RiskReport` | Remove sensitive fields before output. | Missing |
| `validate_report_export_destination(destination: AuthorizedReportPath) -> ValidationResult` | Reject traversal, unauthorized roots, unsafe extensions, and accidental overwrite. | Missing |
| `write_risk_report(report: RiskReport, destination: AuthorizedReportPath) -> ReportWriteReceipt` | Write only under explicit path authorization (with deterministic write receipts). | Missing |

## FEAT-RISK-18: Risk Observability (app.services.risk.observability)

---

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `risk_observed(operation: str, metrics: MetricsSink, logger: RiskLogger) -> Callable[[RiskCallableT], RiskCallableT]` | Boundary decorator adding start/completion/failure logging and timing (with `measure_risk_latency`). | Missing |
| `emit_risk_metrics(event: RiskObservabilityEvent, sink: MetricsSink) -> None` | Emit counts, rates, latency, stale-evidence, kill-switch, and audit-health metrics. | Missing |
| `build_decision_metrics(decision: RiskDecisionPackage) -> tuple[RiskObservabilityEvent, ...]` | Derive count/rate/reason-code events from a decision (with bounded latency metric events). | Missing |
| `log_risk_boundary_event(event: RiskBoundaryEvent, logger: RiskLogger) -> None` | Structured logging without raw secrets or private payloads. | Missing |

## FEAT-RISK-19: Official Risk AI Tools and Agent Attachment (app.services.risk.tools / agentic.tools.risk)

---

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `build_risk_tool_registry() -> RiskToolRegistry` | Approved official tool catalogue (with listing, resolution, and side-effect metadata validation). | Missing |
| `review_trade_risk_tool(request: TradeRiskReviewToolRequest) -> ToolResponse[RiskDecisionPayload]` | Governed trade review with required audit evidence (`places_trade=False`). | Missing |
| `calculate_position_size_tool(request: PositionSizeToolRequest) -> ToolResponse[PositionSizingPayload]` | Read-only policy-bounded position sizing. | Missing |
| `assess_risk_regime_tool(request: RiskRegimeToolRequest) -> ToolResponse[RegimePayload]` | Read-only regime assessment of supplied evidence. | Missing |
| `build_portfolio_risk_snapshot_tool(request: PortfolioRiskSnapshotToolRequest) -> ToolResponse[RiskSnapshotPayload]` | Read-only JSON-safe portfolio risk snapshot. | Missing |
| `run_portfolio_risk_governor_tool(request: PortfolioGovernorToolRequest) -> ToolResponse[RiskDecisionPayload]` | Full portfolio governor run (with allocation-review and strategy-admission tool counterparts). | Missing |
| `validate_risk_approval_token_tool(request: TokenValidationToolRequest) -> ToolResponse[TokenValidationPayload]` | Read-only bounded approval-evidence validation. | Missing |
| `check_risk_kill_switch_tool(request: KillSwitchStatusToolRequest) -> ToolResponse[KillSwitchPayload]` | Read-only scoped kill-switch status. | Missing |
| `run_risk_scenario_analysis_tool(request: ScenarioAnalysisToolRequest) -> ToolResponse[StressPayload]` | Read-only stress/scenario analysis of stored or injected evidence. | Missing |
| `generate_risk_report_tool(request: RiskReportToolRequest) -> ToolResponse[RiskReportPayload]` | Report generation; writes only through explicit authorization. | Missing |
| `load_agentic_risk_tools(registry: RiskToolRegistry) -> tuple[AgentToolDefinition, ...]` | Adapt approved risk tools for agent attachment without exporting internal engines (with attachment validation and envelope-only invocation). | Missing |

---

**Note:** `RiskGovernor` is the only coordinator allowed to create final `RiskDecisionPackage` outcomes; all engines are pure given injected evidence, and no Risk function places, modifies, or closes broker orders.

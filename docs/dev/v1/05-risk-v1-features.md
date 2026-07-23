## FEAT-RISK-01: Shared helpers for the risk service package (app.services.risk._common)

| Function | Purpose |
|----------|---------|
| `risk_tool_result(tool_name: str, *, status: str = 'success', data: dict[str, Any] \| None = None, errors: list[str] \| None = None, warnings: list[str] \| None = None, request_id: str \| None = None, agent_name: str \| None = None, environment: str = 'development', dry_run: bool = True, risk_level: str = 'high', approval_required: str = 'risk_governor_required', side_effects: list[str] \| None = None) -> dict[str, Any]` | Build the standard result envelope for risk service tool functions. |
| `risk_tool_context(kwargs: dict[str, Any]) -> dict[str, Any]` | Extract common request metadata from a risk tool keyword payload. |
| `risk_business_payload(kwargs: dict[str, Any]) -> dict[str, Any]` | Return business inputs after removing standard control fields. |
| `risk_limit_check(tool_name: str, *, value: float, limit: float, comparator: str = 'max', request_id: str \| None = None, agent_name: str \| None = None, environment: str = 'development', dry_run: bool = True) -> dict[str, Any]` | Evaluate a deterministic risk threshold and return a standard result. |
| `risk_policy_module() -> ModuleType` | Return the risk policy service module. |
| `risk_portfolio_module() -> ModuleType` | Return the risk portfolio service module. |
| `risk_safety_module() -> ModuleType` | Return the risk safety service module. |
| `risk_live_module() -> ModuleType` | Return the live risk service module. |


## FEAT-RISK-02: Lightweight public facades for the risk service (app.services.risk.api.public)

| Function | Purpose |
|----------|---------|
| `PortfolioStateBuilder` (model) | Lazy public facade for the portfolio state builder. |
| `RiskSnapshotBuilder` (model) | Lazy public facade for the risk snapshot builder. |
| `RiskReportBuilder` (model) | Lazy public facade for current risk reports. |


## FEAT-RISK-03: Tamper-evident risk audit events and redacted payload construction (app.services.risk.audit.events)

| Function | Purpose |
|----------|---------|
| `AuditRedactionPolicy` (class) | Defines sensitive keys to redact and safe keys to retain. |
| `AuditContext` (class) | Context holding the evaluation details and metadata for an audit record. |
| `redact_audit_payload(payload: Mapping[str, JsonValue], policy: AuditRedactionPolicy) -> dict[str, JsonValue]` | Removes protected values before persistence/logging. |
| `build_canonical_audit_payload(decision: RiskDecisionPackage, context: AuditContext) -> dict[str, JsonValue]` | Builds stable, redacted audit material. |
| `create_risk_audit_event(decision: RiskDecisionPackage, context: AuditContext \| Any, audit_sink: Any = None) -> RiskAuditEvent` | Produces immutable audit record. |


## FEAT-RISK-04: Audit-chain genesis hash, append hash, sequence verification, and tamper-detection (app.services.risk.audit.hash_chain)

| Function | Purpose |
|----------|---------|
| `AuditChainVerification` (class) | Result of traversing and verifying the audit chain. |
| `build_genesis_hash(payload: Mapping[str, JsonValue]) -> str` | Computes the first-record hash (genesis block). |
| `append_audit_hash(previous_hash: str, payload: Mapping[str, JsonValue]) -> str` | Computes deterministic chained SHA256 hash. |
| `verify_risk_audit_chain(events: Sequence[RiskAuditEvent] \| Any) -> AuditChainVerification` | Validates genesis, sequence continuity, payload hashes, and tamper state. |
| `require_valid_audit_chain(verification: AuditChainVerification, mode: RiskMode) -> ValidationResult` | Fails closed for live-sensitive modes when tampering is detected. |


## FEAT-RISK-05: Decision-token signing, validation, scope, expiry, and revocation checks (app.services.risk.audit.tokens)

| Function | Purpose |
|----------|---------|
| `RequiredActionScope` (class) | The action scope parameters required to validate a token. |
| `TokenValidationContext` (class) | Context holding the verification expectations for a token. |
| `TokenValidationResult` (class) | Verification details and status for a decision token check. |
| `RiskDecisionTokenSigner.sign_payload(canonical_payload: str) -> str` | Sign canonical JSON string with HMAC-SHA256. |
| `RiskDecisionTokenSigner.is_token_revoked(token_id: str) -> bool` | Check if token is revoked in store or local memory. |
| `RiskDecisionTokenSigner.revoke_token(token_id: str) -> None` | Mark token as revoked. |
| `RiskDecisionTokenSigner.sign_token(decision_id: str, request_id: str, workflow_id: str, approved_action: str, config_hash: str, decision_hash: str, scope: dict[str, Any], expiry_seconds: int = 300, policy_hash: str = "") -> Any` | Legacy helper for testing token validation wrapper. |
| `create_risk_decision_token(decision: RiskDecisionPackage \| str \| Any = None, signer: RiskDecisionTokenSigner \| Any = None, now_utc: datetime \| Any = None, *args: Any, **kwargs: Any) -> RiskDecisionToken \| Any` | Signs an eligible bounded approval. |
| `validate_token_expiry(token: RiskDecisionToken, now_utc: datetime) -> ValidationResult` | Validates bounded expiry. |
| `validate_token_scope(token: RiskDecisionToken, required: RequiredActionScope) -> ValidationResult` | Validates action/account/strategy/symbol/environment scope. |
| `validate_risk_approval_token(token: RiskDecisionToken \| Any, context: TokenValidationContext \| Any = None, verifier: RiskDecisionTokenSigner \| Any = None, *args: Any, **kwargs: Any) -> TokenValidationResult \| bool` | Checks signature, expiry, revocation, scope, policy, and config hashes. |
| `revoke_risk_approval_token(token_id: str, state_store: Any) -> None` | Mark a decision token as revoked in the store. |


## FEAT-RISK-06: Correlation concentration helpers for portfolio risk checks (app.services.risk.calculations.correlation)

| Function | Purpose |
|----------|---------|
| `CorrelationPair` (model) | Pairwise correlation input with gross portfolio weights. |
| `CorrelationConcentration` (model) | Aggregated pair and portfolio concentration from correlation inputs. |
| `calculate_correlation_concentration(pairs: tuple[CorrelationPair, ...], *, threshold: float) -> CorrelationConcentration` | Calculate weighted pair concentration from pairwise correlations. |
| `symbol_cluster(symbol: str) -> str` | Return the configured cluster for a symbol. |
| `correlation_impact(proposal: dict[str, object], portfolio_snapshot: dict[str, object]) -> dict[str, object]` | Calculate post-trade cluster exposure. |
| `correlation_failures(impact: dict[str, object], thresholds: dict[str, object]) -> list[str]` | Return deterministic correlation or currency-cluster failures. |


## FEAT-RISK-07: CVaR risk service (app.services.risk.calculations.cvar)

| Function | Purpose |
|----------|---------|
| `historical_cvar(returns: list[float], confidence: float = 0.95) -> float` | Function historical_cvar provides risk service behavior. |
| `incremental_cvar(current_returns: list[float], proposed_returns: list[float], confidence: float = 0.95) -> float` | Function incremental_cvar provides risk service behavior. |


## FEAT-RISK-08: Exposure and concentration primitives for deterministic risk checks (app.services.risk.calculations.exposure)

| Function | Purpose |
|----------|---------|
| `PositionExposure.signed_exposure -> float` | Normalized position input used by exposure and concentration calculators. |
| `ExposureSummary` (model) | Portfolio-level gross and net exposure summary. |
| `ConcentrationResult` (model) | Concentration summary for one grouping dimension. |
| `calculate_exposure_summary(positions: tuple[PositionExposure, ...]) -> ExposureSummary` | Calculate gross and net exposure from normalized open positions. |
| `calculate_symbol_concentration(positions: tuple[PositionExposure, ...], *, threshold: float) -> ConcentrationResult` | Calculate gross concentration share for each symbol. |
| `calculate_currency_concentration(positions: tuple[PositionExposure, ...], *, threshold: float) -> ConcentrationResult` | Calculate gross concentration share for each currency bucket. |
| `calculate_strategy_family_concentration(positions: tuple[PositionExposure, ...], *, threshold: float) -> ConcentrationResult` | Calculate gross concentration share for each strategy family. |
| `exposure_snapshot(positions: list[dict[str, object]], *, equity: float = 100000.0) -> dict[str, object]` | Build a lightweight exposure map from raw position dictionaries. |
| `proposed_exposure_impact(proposal: dict[str, object], portfolio_snapshot: dict[str, object]) -> dict[str, float]` | Calculate symbol exposure after a proposed trade. |
| `concentration_failures(impact: dict[str, float], thresholds: dict[str, object]) -> list[str]` | Return deterministic concentration rule failures. |


## FEAT-RISK-09: Shared deterministic risk calculators (app.services.risk.calculations.math_utils)

| Function | Purpose |
|----------|---------|
| `stop_loss_distance(proposal: dict[str, Any]) -> float` | Function stop_loss_distance provides risk service behavior. |
| `pip_value(symbol: str, volume: float) -> float` | Function pip_value provides risk service behavior. |
| `proposed_trade_risk(proposal: dict[str, Any], account_equity: float) -> float` | Function proposed_trade_risk provides risk service behavior. |
| `notional_exposure(proposal: dict[str, Any]) -> float` | Function notional_exposure provides risk service behavior. |
| `risk_reward_value(proposal: dict[str, Any]) -> float` | Function risk_reward_value provides risk service behavior. |


## FEAT-RISK-10: Position Sizing Framework (app.services.risk.calculations.position_sizing)

| Function | Purpose |
|----------|---------|
| `PositionSizer.__init__(method: str = 'fixed_risk', config: dict[str, Any] \| None = None, mt5_client=None) -> None` | Initialize position sizer. |
| `PositionSizer.calculate_size(account_balance: float, entry_price: float, stop_loss: float \| None = None, symbol_info: Any \| None = None, context: dict[str, Any] \| None = None, symbol: str \| None = None, signal_type: str \| None = None, allow_fractional: bool = False) -> float` | Calculate position size based on configured method. |
| `validate_position_size(size: float, symbol_info: Any, max_size: float \| None = None, allow_fractional: bool = False) -> float` | Validate and adjust position size to meet constraints. |
| `estimate_kelly_parameters(result: 'BacktestResult') -> dict[str, float]` | Estimate Kelly Criterion parameters from backtest result. |


## FEAT-RISK-11: Stable, canonical, order-invariant hashing for Risk configuration profiles (app.services.risk.config.hashing)

| Function | Purpose |
|----------|---------|
| `ConfigHashComparison` (dataclass) | Comparison result of two risk configuration profiles. |
| `canonicalize_risk_config_for_hash(config: RiskConfig) -> dict[str, Any]` | Normalize a validated risk config into sorted JSON-safe hash material. |
| `hash_risk_config(config: RiskConfig) -> str` | Generate a stable hash for decisions, tokens, audit events, and replay. |
| `compare_risk_config_hashes(left: RiskConfig, right: RiskConfig) -> ConfigHashComparison` | Compare two risk configurations and report differences. |
| `validate_risk_config_hash(expected_hash: str, config: RiskConfig) -> ValidationResult` | Verify that the config's hash matches the expected hash. |


## FEAT-RISK-12: Configuration loading and caching for Risk Governance (app.services.risk.config.loader)

| Function | Purpose |
|----------|---------|
| `RiskConfigHash` (class) | Container for a stable configuration profile hash. |
| `RiskProfileRegistry.register(profile_name: str, config: RiskConfig) -> None` | Register a profile in the registry. |
| `RiskProfileRegistry.get(profile_name: str) -> RiskConfig \| None` | Get a registered profile by name. |
| `RiskProfileRegistry.clear() -> None` | Clear all registered profiles. |
| `RiskConfigLoader.load(profile_name: str, source: RiskConfigSource \| None = None) -> RiskConfig` | Load configuration profile by name or source. |
| `RiskConfigLoader.validate(config: RiskConfig) -> None` | Validate configuration object. |
| `load_risk_config(profile_name: str, source: RiskConfigSource \| None = None) -> RiskConfig` | Load, parse, override, and validate a risk configuration profile. |


## FEAT-RISK-13: Approved risk profile builders and registry (app.services.risk.config.profiles)

| Function | Purpose |
|----------|---------|
| `build_safe_default_profile() -> RiskConfig` | Build and return the approved safe default simulation/offline profile. |
| `build_prop_firm_default_profile() -> RiskConfig` | Build and return the conservative prop-firm default profile. |
| `build_paper_profile() -> RiskConfig` | Build and return the paper-trading validation controls profile. |
| `build_live_conservative_profile() -> RiskConfig` | Build and return the fail-closed live conservative profile. |
| `list_builtin_risk_profiles() -> tuple[str, ...]` | Return stable built-in profile names. |
| `get_builtin_risk_profile(name: str) -> RiskConfig` | Resolve an approved built-in profile by name or fail deterministically. |


## FEAT-RISK-14: Strict config schema and validation rules for Risk Governance (app.services.risk.config.schema)

| Function | Purpose |
|----------|---------|
| `validate_risk_config(config: RiskConfig) -> ValidationResult` | Validate a loaded RiskConfig object against strict ceilings. |


## FEAT-RISK-15: Risk threshold loading and validation (app.services.risk.config.thresholds)

| Function | Purpose |
|----------|---------|
| `load_risk_thresholds(path: str \| Path = CONFIG_PATH) -> dict[str, Any]` | Function load_risk_thresholds provides risk service behavior. |
| `config_version_hash(config: dict[str, Any]) -> str` | Function config_version_hash provides risk service behavior. |
| `validate_threshold_schema(config: dict[str, Any]) -> bool` | Function validate_threshold_schema provides risk service behavior. |
| `validate_config_hash(config: dict[str, Any], expected_hash: str \| None = None) -> bool` | Function validate_config_hash provides risk service behavior. |


## FEAT-RISK-16: Risk contracts module (app.services.risk.contracts)

| Function | Purpose |
|----------|---------|
| `Contract.validate_metadata_structure(value: dict[str, Any]) -> dict[str, Any]` | Validate metadata namespacing and secret safety. |
| `Contract.validate_trace_identifiers() -> Contract` | Validate trace identifier fields. |
| `Contract.to_json() -> str` | Serialize this contract to deterministic canonical JSON. |
| `Contract.content_hash() -> str` | Calculate a stable SHA256 hash over business-data fields only. |
| `Contract.contract_hash() -> str` | Calculate SHA256 hash over the full serialized contract. |
| `Contract.check_compatibility(target_version: str) -> bool` | Check whether this contract version is compatible with a target. |
| `RiskRejection` (class) | Details explaining why a strategy proposal or signal was rejected. |
| `RiskDecision.validate_outcome_consistency() -> RiskDecision` | Enforce mutual exclusivity of approval and rejection states. |


## FEAT-RISK-17: Shared portfolio risk math and data access helpers (app.services.risk.core.portfolio_risk_engine)

| Function | Purpose |
|----------|---------|
| `PortfolioRiskEngine.__init__(mt5_client=None, timeframe: str = 'D1', start_pos: int = 0, end_pos: int = 500) -> None` | Own portfolio math and raw market-data access for risk workflows. |
| `PortfolioRiskEngine.compute_portfolio_risk(positions: dict[str, float], equity: float, limits: RiskLimits) -> tuple[float, float, float \| None, dict[str, float] \| None]` | Compute portfolio VaR/ES from client-backed positions. |
| `PortfolioRiskEngine.compute_portfolio_risk_from_state(state: PortfolioState, limits: RiskLimits \| None = None) -> tuple[float, float, float \| None, dict[str, float] \| None]` | Compute portfolio VaR/ES from canonical state. |
| `PortfolioRiskEngine.estimate_covariance(returns_df: pd.DataFrame, symbols: list[str], limits: RiskLimits) -> np.ndarray` | Estimate covariance using the current governor formula. |
| `PortfolioRiskEngine.apply_corr_floors(corr_mat: np.ndarray, limits: RiskLimits) -> np.ndarray` | Apply correlation stress only when stressed covariance is requested. |
| `PortfolioRiskEngine.build_weights_from_positions(positions: dict[str, float], historical_data: dict[str, pd.DataFrame], symbols: list[str]) -> np.ndarray` | Build absolute notional weights from raw positions. |
| `PortfolioRiskEngine.build_signed_weights_from_positions(positions: dict[str, float], historical_data: dict[str, pd.DataFrame], symbols: list[str]) -> np.ndarray` | Build signed notional weights normalized by gross absolute notional. |
| `PortfolioRiskEngine.compute_risk_contributions_pct(weights: np.ndarray, cov: np.ndarray, symbols: list[str]) -> dict[str, float]` | Compute percentage contribution to total variance. |
| `PortfolioRiskEngine.portfolio_correlation_map(weights: np.ndarray, cov: np.ndarray, symbols: list[str]) -> dict[str, float]` | Compute symbol-to-portfolio correlation map. |
| `PortfolioRiskEngine.estimate_margin_used(positions: dict[str, float]) -> float \| None` | Estimate current margin usage for raw positions. |
| `PortfolioRiskEngine.get_data(symbols: list[str], exclude_current_bar: bool = True) -> dict[str, pd.DataFrame]` | Fetch historical bars for the supplied symbols. |
| `PortfolioRiskEngine.build_returns_df(data: dict[str, pd.DataFrame], symbols: list[str]) -> pd.DataFrame` | Build log returns from raw bar frames. |
| `PortfolioRiskEngine.portfolio_notional_value(positions: dict[str, float], historical_data: dict[str, pd.DataFrame], symbols: list[str]) -> float` | Compute total absolute notional exposure. |
| `PortfolioRiskEngine.symbol_notional_value(symbol: str, lots: float, historical_data: dict[str, pd.DataFrame]) -> float` | Compute symbol notional normalized to account currency. |
| `PortfolioRiskEngine.compute_cluster_metrics(positions: dict[str, float], equity: float, symbol_to_cluster: dict[str, Any] \| None, limits: RiskLimits) -> dict[str, dict[str, float]]` | Compute per-cluster VaR/ES metrics. |
| `PortfolioRiskEngine.compute_cluster_metrics_from_state(state: PortfolioState, limits: RiskLimits \| None = None) -> dict[str, dict[str, float]]` | Compute per-cluster VaR/ES metrics from canonical state. |
| `PortfolioRiskEngine.group_positions_by_cluster(positions: dict[str, float], symbol_to_cluster: dict[str, Any]) -> dict[str, dict[str, float]]` | Group positions by cluster key. |
| `PortfolioRiskEngine.propose_rc_rebalance(positions: dict[str, float], target_rc_budget: dict[str, float], limits: RiskLimits, max_iters: int = 10, step_frac: float = 0.1) -> dict[str, float]` | Propose position adjustments to align with risk contribution budget. |


## FEAT-RISK-18: Correlation and cluster risk engine contracts (app.services.risk.correlation.contracts)

| Function | Purpose |
|----------|---------|
| `ReturnMethod` (enum) | Supported returns calculation types. |
| `CorrelationMethod` (enum) | Supported correlation calculation methods. |
| `CorrelationAlignmentPolicy` (enum) | Alignment methods for returns series. |
| `ClosedBar` (class) | Bar structure representing a historical period. |
| `ReturnSeries` (class) | Series representing return calculations for a single symbol. |
| `AlignedReturns` (class) | Matrix of aligned returns across multiple symbols. |
| `CorrelationCluster` (class) | Group of highly correlated symbols representing shared portfolio risk. |
| `ClusterExposureAssessment` (class) | Aggregated gross exposure assessment by cluster. |
| `CovarianceMatrix` (class) | Covariance values table. |
| `ComponentRiskContribution` (class) | Contribution details per portfolio component. |
| `CorrelationFallbackContext` (class) | Context details when correlation matrix fallback triggers. |


## FEAT-RISK-19: Correlation matrix calculation, clustering, and portfolio risk impact services (app.services.risk.correlation.engine)

| Function | Purpose |
|----------|---------|
| `calculate_correlation_matrix(*args: Any, **kwargs: Any) -> Any` | Compute pairwise Pearson correlation matrix. |
| `build_correlation_clusters(snapshot: CorrelationSnapshot, threshold: Decimal) -> tuple[CorrelationCluster, ...]` | Group symbols into shared-risk clusters using pairwise correlation thresholds. |
| `calculate_cluster_exposure(*args: Any, **kwargs: Any) -> Any` | Calculate gross exposures for correlated clusters. |
| `calculate_cluster_exposures(portfolio_state: PortfolioState, proposed_trade: ProposedTrade \| None, snapshot: CorrelationSnapshot, threshold: Decimal, market_context: dict[str, Any]) -> dict[str, Decimal]` | Calculate gross exposure in account currency for correlated asset clusters. |
| `calculate_symbol_cluster_exposure(symbol: str, portfolio_state: PortfolioState, proposed_trade: ProposedTrade \| None, snapshot: CorrelationSnapshot, threshold: Decimal, market_context: dict[str, Any]) -> Decimal` | Calculate gross exposure for the cluster containing a specific symbol. |
| `calculate_component_risk_contribution(covariance: CovarianceMatrix, weights: Sequence[Decimal]) -> ComponentRiskContribution` | Compute contribution per component symbol based on weights and covariance. |
| `calculate_portfolio_returns(portfolio_state: PortfolioState, market_data: dict[str, list[Any]], return_type: str = "close_to_close", exclude_last: bool = True) -> dict[datetime, Decimal]` | Calculate weighted historical portfolio returns (V1 compatibility wrapper). |
| `calculate_marginal_correlation(portfolio_state: PortfolioState, proposed_trade: ProposedTrade, market_data: dict[str, list[Any]], lookback: int = 50, return_type: str = "close_to_close", min_samples: int = 20, fallback_correlation: Decimal \| None = None, exclude_last: bool = True) -> tuple[Decimal, bool]` | Calculate marginal correlation coefficient of proposed trade with portfolio. |
| `calculate_correlation_multiplier(marginal_correlation: Decimal, config_multiplier_factor: Decimal = Decimal("0.5")) -> Decimal` | Calculate the correlation-adjusted sizing multiplier. |
| `detect_correlation_spikes(snapshot: CorrelationSnapshot, threshold: Decimal) -> list[tuple[str, str, Decimal]]` | Detect asset pairs whose correlation exceeds the given threshold. |
| `evaluate_proposed_trade_correlation(proposed_trade: ProposedTrade, portfolio_state: PortfolioState, snapshot: CorrelationSnapshot, config: RiskConfig, market_context: dict[str, Any]) -> tuple[RiskDecisionStatus, Decimal, str]` | Evaluate a proposed trade's correlation impact and recommend action. |
| `CorrelationEngine.calculate_returns(bars: list[Any], return_type: str, exclude_last: bool = True) -> dict[datetime, Decimal]` | Calculate returns series for a list of bars. |
| `CorrelationEngine.align_return_series(returns_a: dict[datetime, Decimal], returns_b: dict[datetime, Decimal]) -> tuple[list[Decimal], list[Decimal]]` | Align two return series by common timestamps. |
| `CorrelationEngine.calculate_correlation_matrix(market_data: dict[str, list[Any]], lookback: int = 50, timeframe: str = "M1", method: str = "pearson", return_type: str = "close_to_close", min_samples: int = 20, fallback_correlation: Decimal \| None = None, exclude_last: bool = True) -> dict[str, dict[str, Decimal]]` | Compute rolling correlation matrix for multiple symbol price series. |
| `CorrelationEngine.calculate_correlation_impact(portfolio_state: PortfolioState, proposed_trade: ProposedTrade, market_data: dict[str, list[Any]], lookback: int = 50, return_type: str = "close_to_close", min_samples: int = 20, fallback_correlation: Decimal \| None = None, exclude_last: bool = True) -> Decimal` | Compute marginal correlation impact of a proposed trade. |
| `CorrelationEngine.calculate_cluster_exposure(portfolio_state: PortfolioState, proposed_trade: ProposedTrade \| None, snapshot: CorrelationSnapshot, threshold: Decimal, market_context: dict[str, Any]) -> dict[str, Decimal]` | Calculate gross exposure for correlated asset clusters. |
| `calculate_correlation_snapshot(market_data: dict[str, list[Any]], lookback: int = 50, timeframe: str = "M1", method: str = "pearson", return_type: str = "close_to_close", min_samples: int = 20, fallback_correlation: Decimal \| None = None, exclude_last: bool = True) -> CorrelationSnapshot` | Compute rolling correlation matrix for multiple symbol price series. |
| `calculate_correlation_impact(portfolio_state: PortfolioState, proposed_trade: ProposedTrade, market_data: dict[str, list[Any]], lookback: int = 50, return_type: str = "close_to_close", min_samples: int = 20, fallback_correlation: Decimal \| None = None, exclude_last: bool = True) -> Decimal` | Compute marginal correlation impact of a proposed trade before approval. |


## FEAT-RISK-20: Correlation fallback policy and resolution services (app.services.risk.correlation.fallbacks)

| Function | Purpose |
|----------|---------|
| `should_fail_closed_for_missing_correlation(context: CorrelationFallbackContext, policy: object) -> bool` | Determine whether missing correlation evidence must block/reject. |
| `build_conservative_correlation_snapshot(symbols: Sequence[str], assumed_correlation: Decimal) -> CorrelationSnapshot` | Build a deterministic conservative fallback correlation snapshot. |
| `resolve_correlation_fallback(context: CorrelationFallbackContext, policy: object) -> CorrelationSnapshot` | Resolve conservative fallback correlation snapshot. |


## FEAT-RISK-21: Closed-bar returns construction and alignment services (app.services.risk.correlation.returns)

| Function | Purpose |
|----------|---------|
| `build_return_series(bars: Sequence[ClosedBar] \| list[Any], method: ReturnMethod) -> ReturnSeries` | Derive return series from bars. |
| `align_return_series(*args: Any, **_kwargs: Any) -> Any` | Align return series by identical timestamps. |
| `validate_correlation_inputs(aligned: AlignedReturns, minimum_samples: int) -> dict[str, Any]` | Validate that aligned return series meet requirements. |
| `calculate_returns(bars: list[Any], return_type: str, exclude_last: bool = True) -> dict[datetime, Decimal]` | Calculate returns series for a list of bars (V1 compatibility wrapper). |
| `calculate_pearson(x: Sequence[Decimal], y: Sequence[Decimal]) -> Decimal` | Calculate Pearson correlation coefficient between two aligned list series. |


## FEAT-RISK-22: Canonical account state for risk processing (app.services.risk.domain.account)

| Function | Purpose |
|----------|---------|
| `AccountState` (model) | Normalized account inputs used by the risk subsystem. |


## FEAT-RISK-23: Risk Department exceptions (app.services.risk.domain.exceptions)

| Function | Purpose |
|----------|---------|
| `RiskConfigError` (model) | Raised when risk configuration cannot be validated. |
| `RiskTokenError` (model) | Raised when approval token validation fails. |


## FEAT-RISK-24: Canonical market data state for risk processing (app.services.risk.domain.market)

| Function | Purpose |
|----------|---------|
| `MarketState.row_count -> int` | Normalized market slice for one symbol and timeframe. |
| `MarketState.last_close -> float \| None` | Normalized market slice for one symbol and timeframe. |


## FEAT-RISK-25: Canonical portfolio state for risk processing (app.services.risk.domain.portfolio)

| Function | Purpose |
|----------|---------|
| `PortfolioState.active_symbols -> list[str]` | Validated point-in-time portfolio snapshot used by risk modules. |
| `PortfolioState.position_map -> dict[str, float]` | Validated point-in-time portfolio snapshot used by risk modules. |


## FEAT-RISK-26: Canonical position state for risk processing (app.services.risk.domain.position)

| Function | Purpose |
|----------|---------|
| `PositionState` (model) | Normalized active position data used by the risk subsystem. |


## FEAT-RISK-27: Trade proposal domain models (app.services.risk.domain.proposal)

| Function | Purpose |
|----------|---------|
| `RiskAssessmentRequest` (model) | Public request envelope for pre-trade risk assessment. |


## FEAT-RISK-28: Snapshot models with freshness metadata for the safety core (app.services.risk.domain.snapshot)

| Function | Purpose |
|----------|---------|
| `MarketSnapshot.expires_at -> datetime` | Market input snapshot with embedded TTL metadata. |
| `MarketSnapshot.from_policy(*, snapshot_id: str, symbol: str, snapshot_type: MarketSnapshotType, observed_at: datetime, best_bid: float \| None = None, best_ask: float \| None = None, spread_points: float \| None = None, tradable: bool \| None = None, source: str = 'market_data_feed') -> MarketSnapshot` | Market input snapshot with embedded TTL metadata. |
| `MarketSnapshot.evaluate(*, clock: Clock \| None = None) -> FreshnessWindow` | Evaluate the snapshot against its declared TTL. |
| `AccountSnapshot.expires_at -> datetime` | Account state snapshot with embedded TTL metadata. |
| `AccountSnapshot.from_policy(*, snapshot_id: str, account_id: str, observed_at: datetime, balance: float, equity: float, free_margin: float, margin_used: float, currency: str) -> AccountSnapshot` | Account state snapshot with embedded TTL metadata. |
| `AccountSnapshot.evaluate(*, clock: Clock \| None = None) -> FreshnessWindow` | Evaluate the snapshot against its declared TTL. |
| `PortfolioSnapshot.expires_at -> datetime` | Portfolio state snapshot with embedded TTL metadata. |
| `PortfolioSnapshot.from_policy(*, snapshot_id: str, portfolio_id: str, observed_at: datetime, open_position_count: int, gross_exposure: float, net_exposure: float, symbols: tuple[str, ...] = ()) -> PortfolioSnapshot` | Portfolio state snapshot with embedded TTL metadata. |
| `PortfolioSnapshot.evaluate(*, clock: Clock \| None = None) -> FreshnessWindow` | Evaluate the snapshot against its declared TTL. |


## FEAT-RISK-29: Canonical symbol specification state for risk processing (app.services.risk.domain.symbol)

| Function | Purpose |
|----------|---------|
| `SymbolState` (model) | Normalized symbol specification snapshot used by risk math. |


## FEAT-RISK-30: Deterministic error-code mapping for the risk service boundary (app.services.risk.errors)

| Function | Purpose |
|----------|---------|
| `ErrorPayload` (TypedDict) | Structured error payload used by standard error envelopes. |
| `to_risk_error_payload(exception: BaseException, *, request_id: str \| None = None) -> ErrorPayload` | Map an exception to a redacted, deterministic Risk error payload. |
| `RiskError` (exception) | Base error type for all risk calculations and registry operations. |
| `RiskValidationError` (exception) | Raised when validation of config or state inputs fails. |
| `RiskDataError` (exception) | Raised when data storage or retrieval operations fail. |
| `InvalidPortfolioStateError` (exception) | Raised when portfolio state has invalid structure or parameters. |
| `InvalidRiskConfigError` (exception) | Raised when risk configuration is missing or invalid. |
| `MissingEvidenceError` (exception) | Raised when required evidence is missing. |
| `StaleEvidenceError` (exception) | Raised when required evidence is stale. |
| `LimitFailedError` (exception) | Raised when risk limit check fails. |
| `PolicyBlockedError` (exception) | Raised when trade/allocation is blocked by deterministic policy. |
| `ApprovalRequiredError` (exception) | Raised when action requires approval token. |
| `ApprovalTokenInvalidError` (exception) | Raised when approval token is invalid. |
| `ApprovalTokenExpiredError` (exception) | Raised when approval token has expired. |
| `ApprovalTokenRevokedError` (exception) | Raised when approval token was revoked. |
| `ApprovalTokenConsumedError` (exception) | Raised when approval token was already consumed. |
| `ConfigVersionMismatchError` (exception) | Raised when config version or hash mismatch occurs. |
| `ConfigCompatibilityNotApprovedError` (exception) | Raised when config compatibility is not approved. |
| `ParametricVarGaussianWarningError` (exception) | Warning/error when Gaussian assumptions are used for parametric VaR. |
| `PendingApprovalDoubleSpendBlockedError` (exception) | Raised when concurrent proposals risk double spending. |
| `PayloadTooLargeError` (exception) | Raised when request payload is too large or nested too deeply. |
| `MissingStopLossError` (exception) | Raised when stop loss is missing for stop-dependent sizing. |
| `InsufficientVolatilityEvidenceError` (exception) | Raised when volatility evidence is insufficient for calculation. |
| `InsufficientKEvidenceError` (exception) | Raised when Kelly trade sample evidence is insufficient (< 30). |
| `LiveStateStaleError` (exception) | Raised when live state is stale. |
| `InFlightToleranceExceededError` (exception) | Raised when in-flight order tolerance buffer is exceeded. |
| `CalculationFailedError` (exception) | Raised when a specific risk calculation fails. |
| `SnapshotBuildFailedError` (exception) | Raised when snapshot building fails. |
| `ReportGenerationFailedError` (exception) | Raised when report generation fails. |
| `StorageError` (exception) | Raised when risk storage or audit persistence operations fail. |


## FEAT-RISK-31: Currency exposure aggregation services (app.services.risk.exposure.aggregation)

| Function | Purpose |
|----------|---------|
| `decompose_position(symbol: str, side: str, quantity: Decimal, price: Decimal, contract_size: Decimal, base_ccy: str, quote_ccy: str) -> list[CurrencyLegExposure]` | Decompose a position/order on a symbol into its base and quote currency legs. |
| `calculate_currency_exposure(portfolio_state: PortfolioState, proposed_trade: ProposedTrade \| None, config: RiskConfig, market_context: dict[str, Any], strategy_id: str \| None = None, symbol: str \| None = None) -> dict[str, CurrencyExposure]` | Decompose and aggregate gross/net exposures per currency. |
| `aggregate_currency_legs(legs: Sequence[CurrencyLegExposure]) -> Mapping[str, Decimal]` | Aggregate signed leg exposures by ISO currency code. |
| `calculate_gross_and_net_exposure(exposure: Mapping[str, Decimal]) -> dict[str, Decimal]` | Calculate gross and net exposure totals from currency leg amounts. |
| `enforce_currency_rounding(value: Decimal, currency: str) -> Decimal` | Enforce currency-specific rounding precision. |
| `calculate_symbol_exposure(portfolio_state: PortfolioState, proposed_trade: ProposedTrade \| None, config: RiskConfig, market_context: dict[str, Any], strategy_id: str \| None = None) -> dict[str, SymbolExposure]` | Calculate and aggregate exposures per symbol. |
| `calculate_net_currency_exposure(portfolio_state: PortfolioState, proposed_trade: ProposedTrade \| None, config: RiskConfig, market_context: dict[str, Any], strategy_id: str \| None = None, symbol: str \| None = None) -> dict[str, Decimal]` | Calculate net exposures per currency (in account currency equivalent). |
| `calculate_projected_exposure(portfolio_state: PortfolioState, proposed_trade: ProposedTrade \| None, config: RiskConfig, market_context: dict[str, Any], strategy_id: str \| None = None, symbol: str \| None = None) -> dict[str, CurrencyExposure]` | Calculate projected exposures under pending policy. |
| `detect_hidden_concentration(portfolio_state: PortfolioState, proposed_trade: ProposedTrade \| None, config: RiskConfig, market_context: dict[str, Any]) -> list[str]` | Detect hidden exposure concentrations across multiple quote pairs. |
| `CurrencyExposureEngine.calculate_exposure(portfolio_state: PortfolioState, proposed_trade: ProposedTrade \| None, market_context: dict[str, Any], strategy_id: str \| None = None, symbol: str \| None = None) -> dict[str, CurrencyExposure]` | Decompose and aggregate exposures per currency. |
| `SymbolExposureEngine.calculate_exposure(portfolio_state: PortfolioState, proposed_trade: ProposedTrade \| None, market_context: dict[str, Any], strategy_id: str \| None = None) -> dict[str, SymbolExposure]` | Calculate and aggregate exposures per symbol. |
| `ClusterExposureEngine.calculate_exposure(portfolio_state: PortfolioState, proposed_trade: ProposedTrade \| None, market_context: dict[str, Any], strategy_id: str \| None = None, symbol: str \| None = None) -> dict[str, CurrencyExposure]` | Filter portfolio currency exposures to custom config clusters. |
| `ExposureSnapshotBuilder.build_snapshot(portfolio_state: PortfolioState, proposed_trade: ProposedTrade \| None, market_context: dict[str, Any]) -> dict[str, Any]` | Build a comprehensive exposure snapshot. |
| `calculate_currency_leg_exposure(symbol: str, side: str, quantity: Decimal, price: Decimal, contract_size: Decimal, base_ccy: str, quote_ccy: str) -> list[CurrencyLegExposure]` | Calculate the currency leg decomposition for a single trade/position. |


## FEAT-RISK-32: FX currency-leg decomposition and symbol parsing services (app.services.risk.exposure.fx_legs)

| Function | Purpose |
|----------|---------|
| `FxPair` (class) | Forex base/quote currency pair identity. |
| `ContractSpecification` (class) | Specification of contract size for FX currency decomposition. |
| `parse_fx_symbol(symbol: str, metadata: SymbolRiskMetadata \| None = None) -> FxPair` | Parse FX symbol to identify base and quote currencies. |
| `decompose_fx_trade(trade: ProposedTrade, price: Decimal, contract: ContractSpecification) -> tuple[CurrencyLegExposure, CurrencyLegExposure]` | Decompose proposed trade into base and quote currency leg exposures. |
| `validate_currency_conversion_requirements(exposures: list[CurrencyLegExposure] \| list[Any], rates: dict[str, Any] \| dict[str, Decimal], account_currency: str = "USD") -> dict[str, Any]` | Verify that conversion rates are available for all non-account leg currencies. |


## FEAT-RISK-33: Drawdown governor engine (app.services.risk.feasibility.drawdown)

| Function | Purpose |
|----------|---------|
| `RiskStepDownState` (enum) | Drawdown-based throttling categories/states. |
| `calculate_daily_drawdown(portfolio_state: PortfolioState, daily_start_balance: Decimal) -> Decimal` | Calculate daily drawdown percentage. |
| `calculate_total_drawdown(portfolio_state: PortfolioState, peak_balance: Decimal) -> Decimal` | Calculate total account drawdown percentage from lifetime peak balance. |
| `calculate_strategy_drawdown(strategy_id: str, portfolio_state: PortfolioState, strategy_peak_equity: Decimal) -> Decimal` | Calculate drawdown for a specific strategy's allocated capital. |
| `determine_drawdown_throttling(drawdown: Decimal, soft_limit: Decimal, hard_limit: Decimal) -> tuple[DrawdownThrottlingState, Decimal]` | Map a drawdown level to a throttling category and risk scale multiplier. |
| `persist_drawdown_state(state: DrawdownState, file_path: str \| Path) -> None` | Serialize and write DrawdownState to a JSON file. |
| `restore_drawdown_state(file_path: str \| Path) -> DrawdownState \| None` | Restore and deserialize DrawdownState from a JSON file. |
| `check_revenge_trading(proposed_trade: ProposedTrade \| None, drawdown_state: DrawdownState, market_context: dict[str, Any], config: RiskConfig \| None = None) -> tuple[bool, str]` | Check if the proposed trade constitutes catch-up or revenge risk behavior. |
| `verify_drawdown_limits(portfolio_state: PortfolioState, proposed_trade: ProposedTrade \| None, market_context: dict[str, Any], config: RiskConfig) -> LimitResult` | Enforce total drawdown limits and check for revenge trading behavior. |
| `determine_drawdown_state(snapshot: PortfolioRiskSnapshot, prior: DrawdownState \| None, policy: EffectiveRiskPolicy) -> DrawdownState` | Classify normal/caution/defensive/recovery/halted drawdown state. |
| `calculate_drawdown_multiplier(state: DrawdownState, policy: EffectiveRiskPolicy) -> Decimal` | Return the approved risk step-down multiplier for a drawdown state. |
| `apply_drawdown_throttle(*args: Any, **kwargs: Any) -> Any` | Apply drawdown-aware risk throttling, supporting V1 and V2 signatures. |
| `DrawdownGovernor.calculate_daily_drawdown(portfolio_state: PortfolioState, daily_start_balance: Decimal) -> Decimal` | Calculate daily drawdown percentage. |
| `DrawdownGovernor.calculate_total_drawdown(portfolio_state: PortfolioState, peak_balance: Decimal) -> Decimal` | Calculate total account drawdown percentage. |
| `DrawdownGovernor.calculate_strategy_drawdown(strategy_id: str, portfolio_state: PortfolioState, strategy_peak_equity: Decimal) -> Decimal` | Calculate drawdown for a specific strategy's allocated capital. |
| `DrawdownGovernor.determine_drawdown_throttling(drawdown: Decimal, soft_limit: Decimal, hard_limit: Decimal) -> tuple[RiskStepDownState, Decimal]` | Map a drawdown level to a throttling category and multiplier. |
| `DrawdownGovernor.apply_drawdown_throttle(portfolio_state: PortfolioState, proposed_trade: ProposedTrade \| None, market_context: dict[str, Any], config: RiskConfig \| None = None) -> LimitResult` | Implement drawdown-aware risk throttling before hard loss limits are hit. |
| `DrawdownGovernor.persist_state(state: DrawdownState, file_path: str \| Path) -> None` | Serialize and write DrawdownState to a JSON file. |
| `DrawdownGovernor.restore_state(file_path: str \| Path) -> DrawdownState \| None` | Restore and deserialize DrawdownState from a JSON file. |
| `drawdown_state(portfolio_snapshot: dict[str, Any], thresholds: dict[str, Any]) -> dict[str, Any]` | Function drawdown_state provides risk service behavior. |


## FEAT-RISK-34: Execution feasibility gate engine (app.services.risk.feasibility.execution_gate)

| Function | Purpose |
|----------|---------|
| `SlippagePolicy` (class) | Configuration/limits for execution slippage. |
| `SpreadPolicy` (class) | Configuration/limits for bid/ask spread. |
| `BrokerConstraintSnapshot` (class) | Snapshot of active broker constraints for a symbol. |
| `ExecutionFeasibilityResult` (class) | Result details of execution feasibility evaluations. |
| `check_stop_distance_validity(proposed_trade: ProposedTrade, stop_level: Decimal, freeze_level: Decimal, pip_size: Decimal) -> tuple[bool, str]` | Verify stop loss distance complies with broker minimum stop and freeze levels. |
| `check_lot_step_validity(volume: Decimal, volume_min: Decimal, volume_max: Decimal, volume_step: Decimal) -> tuple[bool, str, Decimal \| None]` | Validate lot volume size against broker constraints and rounding granularity. |
| `check_holding_time_limit(proposed_trade: ProposedTrade, market_context: dict[str, Any]) -> tuple[bool, str]` | Validate expected holding period against policy limits. |
| `check_execution_feasibility(portfolio_state: PortfolioState, proposed_trade: ProposedTrade \| None, market_context: dict[str, Any], config: RiskConfig) -> ExecutionFeasibilityResult` | Evaluate pre-trade execution feasibility limits on a candidate trade. |
| `ExecutionRiskGate.check_execution_feasibility(portfolio_state: PortfolioState, proposed_trade: ProposedTrade \| None, market_context: dict[str, Any]) -> ExecutionFeasibilityResult` | Evaluate pre-trade execution feasibility limits on a candidate trade. |
| `check_spread_to_sigma(spread: Decimal, volatility: Decimal, multiplier: Decimal = Decimal("3.0")) -> bool` | Validate if current spread is wider than a rolling volatility threshold. |
| `check_slippage_to_sigma(slippage: Decimal, volatility: Decimal, multiplier: Decimal = Decimal("2.0")) -> bool` | Validate if projected slippage threshold exceeds rolling volatility. |
| `check_stop_freeze_level(proposed_trade: ProposedTrade, stop_level: Decimal, freeze_level: Decimal, pip_size: Decimal) -> tuple[bool, str]` | Verify stop loss distance complies with broker minimum stop and freeze levels. |
| `check_volume_feasibility(volume: Decimal, volume_min: Decimal, volume_max: Decimal, volume_step: Decimal) -> tuple[bool, str]` | Validate lot volume size against broker constraints and rounding granularity. |
| `check_trade_frequency(portfolio_state: PortfolioState, strategy_id: str, max_trades_per_min: int = 5, lookback_seconds: int = 60) -> tuple[bool, str]` | Limit the number of trades placed by a strategy to prevent runaway loops. |
| `evaluate_execution_feasibility(_portfolio_state: PortfolioState, proposed_trade: ProposedTrade \| None, market_context: dict[str, Any], _config: RiskConfig) -> ExecutionRiskSnapshot` | Evaluate all execution feasibility metrics and return a snapshot. |
| `verify_execution_limits(portfolio_state: PortfolioState, proposed_trade: ProposedTrade \| None, market_context: dict[str, Any], config: RiskConfig) -> LimitResult` | Check pre-trade execution feasibility limits on a candidate trade. |
| `assess_execution_feasibility(trade: ProposedTrade, market: MarketRiskSnapshot, metadata: BrokerConstraintSnapshot, policy: EffectiveRiskPolicy) -> ExecutionRiskSnapshot` | Calculate execution feasibility and reason codes from canonical evidence. |
| `validate_stop_and_freeze_levels(trade: ProposedTrade, metadata: BrokerConstraintSnapshot) -> ValidationResult` | Validate stop/freeze geometry against broker constraint metadata. |
| `validate_micro_scalping_costs(execution: ExecutionRiskSnapshot, sigma: Decimal, policy: EffectiveRiskPolicy) -> LimitResult` | Enforce M1 spread/slippage-to-sigma limits for micro-scalping profiles. |


## FEAT-RISK-35: Margin governance engine (app.services.risk.feasibility.margin)

| Function | Purpose |
|----------|---------|
| `MarginRequirement` (class) | Calculated margin requirements and utility metrics. |
| `LeverageSnapshot` (class) | Effective leverage metrics compared against caps. |
| `LiquiditySnapshot` (class) | Exit liquidity shock metrics and remaining free margin. |
| `calculate_current_margin(portfolio_state: PortfolioState) -> Decimal` | Calculate the total margin currently utilized by open positions. |
| `calculate_projected_margin(portfolio_state: PortfolioState, proposed_trade: ProposedTrade \| None, market_context: dict[str, Any], config: RiskConfig) -> Decimal` | Calculate projected margin requirement after executing candidate trade. |
| `calculate_free_margin_after_orders(portfolio_state: PortfolioState, proposed_trade: ProposedTrade \| None, market_context: dict[str, Any], config: RiskConfig) -> Decimal` | Calculate remaining free margin. |
| `evaluate_margin_governance(portfolio_state: PortfolioState, proposed_trade: ProposedTrade \| None, market_context: dict[str, Any], config: RiskConfig) -> MarginRiskSnapshot` | Evaluate account-level margin metrics and build a snapshot. |
| `exit_liquidity_stress_check(portfolio_state: PortfolioState, proposed_trade: ProposedTrade \| None, market_context: dict[str, Any], config: RiskConfig, spread_multiplier: Decimal = Decimal("5.0")) -> tuple[bool, Decimal]` | Check if exit transaction costs under spread widening spikes triggers insolvency. |
| `calculate_margin_requirement(portfolio_state: PortfolioState, proposed_trade: ProposedTrade \| None, market_context: dict[str, Any], config: RiskConfig) -> Decimal` | Calculate projected margin requirement after executing candidate trade. |
| `calculate_free_margin_after_trade(portfolio_state: PortfolioState, proposed_trade: ProposedTrade \| None, market_context: dict[str, Any], config: RiskConfig) -> Decimal` | Calculate remaining free margin after trade and pending orders. |
| `check_margin_usage(portfolio_state: PortfolioState, proposed_trade: ProposedTrade \| None, market_context: dict[str, Any], config: RiskConfig) -> LimitResult` | Check account-level margin utilization limits. |
| `check_exit_liquidity(portfolio_state: PortfolioState, proposed_trade: ProposedTrade \| None, market_context: dict[str, Any], config: RiskConfig, spread_multiplier: Decimal = Decimal("5.0")) -> LimitResult` | Check exit liquidity stress impact. |
| `check_strategy_margin_limit(portfolio_state: PortfolioState, proposed_trade: ProposedTrade \| None, market_context: dict[str, Any], config: RiskConfig) -> LimitResult \| None` | Check strategy-level margin allocation ceilings. |
| `verify_margin_limits(portfolio_state: PortfolioState, proposed_trade: ProposedTrade \| None, market_context: dict[str, Any], config: RiskConfig) -> LimitResult` | Enforce margin utilization, leverage caps, and strategy margin limits. |
| `MarginRiskEngine.evaluate_margin(portfolio_state: PortfolioState, proposed_trade: ProposedTrade \| None, market_context: dict[str, Any]) -> MarginRequirement` | Calculate margin requirements for current and projected states. |
| `MarginRiskEngine.evaluate_leverage(portfolio_state: PortfolioState, proposed_trade: ProposedTrade \| None, market_context: dict[str, Any]) -> LeverageSnapshot` | Evaluate effective leverage against limits. |
| `MarginRiskEngine.evaluate_exit_liquidity(portfolio_state: PortfolioState, proposed_trade: ProposedTrade \| None, market_context: dict[str, Any], spread_multiplier: Decimal = Decimal("5.0")) -> LiquiditySnapshot` | Evaluate exit liquidity stress impact. |
| `calculate_current_margin_usage(account: AccountRiskSnapshot, portfolio: PortfolioRiskSnapshot) -> MarginRiskSnapshot` | Derive the current margin usage snapshot from canonical account evidence. |
| `calculate_projected_margin_usage(account: AccountRiskSnapshot, portfolio: PortfolioRiskSnapshot, proposal: ProposedTrade, contract_size: Decimal = Decimal("100000.0")) -> MarginRiskSnapshot` | Project margin usage after a proposed trade using canonical evidence. |
| `calculate_free_margin_after_reservations(account: AccountRiskSnapshot, pending: Sequence[PendingOrderRiskSnapshot], inflight: Sequence[PendingOrderRiskSnapshot]) -> Decimal` | Reserve pending and in-flight order exposure from account free margin. |
| `check_margin_limits(snapshot: MarginRiskSnapshot, policy: EffectiveRiskPolicy) -> tuple[LimitResult, ...]` | Check a margin snapshot against account and portfolio policy caps. |
| `MarginUtilization` (model) | Margin usage summary used in risk decisions and limits. |
| `VolatilityAdjustedSizing` (model) | Normalized size recommendation after volatility scaling. |
| `DrawdownState` (model) | Current drawdown amount, ratio, and coarse state band. |
| `calculate_margin_utilization(*, balance: float, equity: float, free_margin: float, margin_used: float) -> MarginUtilization` | Calculate current margin utilization from account state. |
| `calculate_drawdown_state(*, peak_equity: float, current_equity: float) -> DrawdownState` | Classify drawdown into simple governance bands. |
| `margin_impact(proposal: dict[str, object], account_state: dict[str, object]) -> dict[str, float]` | Calculate post-trade margin state from raw dictionaries. |
| `margin_failures(impact: dict[str, float], thresholds: dict[str, object]) -> list[str]` | Return deterministic margin rule failures. |


## FEAT-RISK-36: Strategy capital allocation governance (app.services.risk.governance.allocation)

| Function | Purpose |
|----------|---------|
| `AllocationMethod` (enum) | Supported capital allocation methods. |
| `AllocationReviewRequest` (class) | The request envelope for capital allocation reviews. |
| `AllocationReviewResult` (class) | Outcome of the allocation governance review process. |
| `AllocatableRisk` (class) | A single strategy's risk-allocation inputs (V2 canonical). |
| `AllocationPlan` (class) | A normalized capital-weight allocation plan (V2 canonical). |
| `equal_risk_allocation(strategies: list[str], total_budget: Decimal) -> dict[str, Decimal]` | Calculate equal-risk budget allocation across active strategies. |
| `volatility_parity_allocation(strategies: list[str], volatilities: dict[str, Decimal], total_budget: Decimal) -> dict[str, Decimal]` | Calculate volatility parity allocation inversely proportional to risk. |
| `correlation_adjusted_risk_parity_allocation(strategies: list[str], volatilities: dict[str, Decimal], correlation_matrix: dict[str, dict[str, Decimal]], total_budget: Decimal) -> dict[str, Decimal]` | Calculate correlation-adjusted volatility parity allocations. |
| `apply_regime_weighting(allocations: dict[str, Decimal], regime_multiplier: Decimal) -> dict[str, Decimal]` | Scale allocations based on a market regime multiplier. |
| `apply_drawdown_adjustment(allocations: dict[str, Decimal], strategy_drawdown_multipliers: dict[str, Decimal]) -> dict[str, Decimal]` | Scale allocations down individually based on strategy drawdown status. |
| `calculate_equal_risk_budget(strategies: list[str], total_budget: Decimal) -> dict[str, Decimal]` | Calculate equal-risk budget allocation across active strategies. |
| `calculate_volatility_parity_budget(strategies: list[str], volatilities: dict[str, Decimal], total_budget: Decimal) -> dict[str, Decimal]` | Calculate volatility parity allocation inversely proportional to risk. |
| `calculate_correlation_adjusted_budget(strategies: list[str], volatilities: dict[str, Decimal], correlation_matrix: dict[str, dict[str, Decimal]], total_budget: Decimal) -> dict[str, Decimal]` | Calculate correlation-adjusted volatility parity allocations. |
| `calculate_regime_weighted_budget(strategies: list[str], volatilities: dict[str, Decimal], correlation_matrix: dict[str, dict[str, Decimal]], total_budget: Decimal, regime_multiplier: Decimal) -> dict[str, Decimal]` | Scale allocations based on a market regime multiplier. |
| `RiskAllocator.calculate_allocated_budget(strategies: list[str], total_budget: Decimal, market_context: dict[str, Any], method: AllocationMethod \| str \| None = None) -> dict[str, Decimal]` | Calculate strategy budgets based on chosen allocation method. |
| `RiskAllocator.review_allocation(request: AllocationReviewRequest) -> AllocationReviewResult` | Evaluate the proposed allocation budgets against limits. |
| `calculate_equal_risk_allocation(items: Sequence[AllocatableRisk]) -> AllocationPlan` | Derive an equal-risk allocation plan across the supplied items. |
| `calculate_volatility_parity_allocation(items: Sequence[AllocatableRisk]) -> AllocationPlan` | Derive a volatility-parity allocation plan across the supplied items. |
| `calculate_correlation_adjusted_allocation(items: Sequence[AllocatableRisk], correlation: CorrelationSnapshot) -> AllocationPlan` | Derive a correlation-adjusted risk-parity allocation plan. |
| `apply_regime_and_drawdown_adjustments(plan: AllocationPlan, regime: RegimeAssessment, drawdown: DrawdownState) -> AllocationPlan` | Apply deterministic regime and drawdown scale-down multipliers. |
| `verify_allocation_limits(portfolio_state: PortfolioState, proposal: ProposedAllocation, market_context: dict[str, Any], config: RiskConfig) -> LimitResult` | Enforce capital boundaries and gate allocation increases. |


## FEAT-RISK-37: Approval-token generation and validation (app.services.risk.governance.approval_tokens)

| Function | Purpose |
|----------|---------|
| `create_approval_token(*, decision_id: str, proposal: RiskProposal, approved_volume: float, risk_metrics_snapshot: dict[str, Any], portfolio_snapshot: dict[str, Any], market_snapshot: dict[str, Any], config_hash: str, policy_version: str, ttl_seconds: int, audit_ref: str) -> RiskApprovalToken` | Function create_approval_token provides risk service behavior. |
| `validate_approval_token(token: dict[str, Any] \| RiskApprovalToken, *, proposal: dict[str, Any] \| None = None, mark_used: bool = True) -> bool` | Function validate_approval_token provides risk service behavior. |


## FEAT-RISK-38: Risk audit artifact helpers (app.services.risk.governance.audit)

| Function | Purpose |
|----------|---------|
| `write_risk_audit(component_name: str, payload: dict[str, Any]) -> str` | Function write_risk_audit provides risk service behavior. |


## FEAT-RISK-39: Risk decision outcome composition for deterministic safety checks (app.services.risk.governance.decisions)

| Function | Purpose |
|----------|---------|
| `ComposedRiskDecision` (model) | Minimal risk decision outcome before envelope/provenance packing. |
| `RiskDecisionEnvelopeContext` (model) | Envelope metadata required to emit a canonical risk decision. |
| `RiskDecisionProvenance` (model) | Persisted rationale, metrics, and provenance fields for a decision. |
| `PackedRiskDecisionArtifacts` (model) | Canonical contract plus persistence-oriented rationale/provenance fields. |
| `compose_risk_decision(*, checks: tuple[RestrictionEvaluation, ...], limit_constraints: tuple[LimitConstraint, ...] = (), force_exit_symbols: tuple[str, ...] = ()) -> ComposedRiskDecision` | Compose the deterministic risk outcome from check results and limits. |
| `pack_risk_decision_rationale_and_provenance(*, composed: ComposedRiskDecision, context: RiskDecisionEnvelopeContext, provenance: RiskDecisionProvenance, risk_decision_id: str \| None = None) -> PackedRiskDecisionArtifacts` | Pack a composed decision into canonical and persistence-ready artifacts. |


## FEAT-RISK-40: Canonical governance entry point built on shared risk engines (app.services.risk.governance.governance_engine)

| Function | Purpose |
|----------|---------|
| `GovernanceReport` (model) | Normalized governance decision/report object. |
| `GovernanceEngine.__init__(risk_engine: PortfolioRiskEngine, limits: RiskLimits, policy_engine: PolicyEngine \| None = None) -> None` | Evaluate governance decisions from raw positions or canonical state. |
| `GovernanceEngine.effective_limits(regime: RegimeState \| None) -> RiskLimits` | Return the effective limits after regime overrides. |
| `GovernanceEngine.evaluate_add_position(current_positions: dict[str, float], candidate_symbol: str, candidate_lots: float, symbol_to_cluster: dict[str, str] \| None = None, regime: RegimeState \| None = None) -> GovernanceReport` | Evaluate a candidate position change from raw position maps. |
| `GovernanceEngine.evaluate_transition(current_positions: dict[str, float], new_positions: dict[str, float], symbol_to_cluster: dict[str, str] \| None = None, regime: RegimeState \| None = None, forced_decision: Decision \| None = None, forced_reason: str \| None = None) -> GovernanceReport` | Evaluate a raw position transition. |
| `GovernanceEngine.evaluate_portfolio_positions(positions: dict[str, float], symbol_to_cluster: dict[str, str] \| None = None, regime: RegimeState \| None = None) -> GovernanceReport` | Evaluate the current raw portfolio compliance state. |
| `GovernanceEngine.evaluate_portfolio_state(state: PortfolioState, regime: RegimeState \| None = None) -> GovernanceReport` | Evaluate current compliance from canonical portfolio state. |
| `GovernanceEngine.evaluate_transition_from_states(current_state: PortfolioState, new_state: PortfolioState, regime: RegimeState \| None = None, forced_decision: Decision \| None = None, forced_reason: str \| None = None) -> GovernanceReport` | Evaluate a projected canonical-state transition before execution. |
| `GovernanceEngine.evaluate_add_position_from_state(current_state: PortfolioState, candidate_symbol: str, candidate_lots: float, regime: RegimeState \| None = None, forced_decision: Decision \| None = None, forced_reason: str \| None = None) -> GovernanceReport` | Evaluate one signed-lot change from a canonical portfolio state. |


## FEAT-RISK-41: Deterministic RiskGovernor service for HaruQuant (app.services.risk.governance.governor)

| Function | Purpose |
|----------|---------|
| `RiskGovernor.__init__(*, thresholds: dict[str, Any] \| None = None, config_hash: str \| None = None) -> None` | Class RiskGovernor provides risk service behavior. |
| `RiskGovernor.evaluate_trade(*, proposal: dict[str, Any], portfolio_snapshot: dict[str, Any] \| None = None, market_snapshot: dict[str, Any] \| None = None) -> RiskGovernorDecision` | Class RiskGovernor provides risk service behavior. |


## FEAT-RISK-42: Emergency kill switch service and state manager (app.services.risk.governance.kill_switch)

| Function | Purpose |
|----------|---------|
| `KillSwitchScope` (enum) | Scope boundaries for kill switches. |
| `RiskKillSwitch` (dataclass) | Typed immutable snapshot of a kill-switch record at a given scope. |
| `PortfolioKillSwitch` (dataclass) | Kill-switch snapshot scoped to portfolio level. |
| `StrategyKillSwitch` (dataclass) | Kill-switch snapshot scoped to a single strategy. |
| `KillSwitchManager.load() -> None` | Load states from local JSON persistence path. |
| `KillSwitchManager.save() -> None` | Write current states to persistence path. |
| `KillSwitchManager.trigger(scope: str, target: str, reason: str, triggered_by: str = "system", audit_bus: _KillSwitchAuditBus \| None = None) -> None` | Trigger an emergency halt/kill switch for a target scope. |
| `KillSwitchManager.resume(scope: str, target: str, approval_token: str \| None = None, operator_role: str \| None = None, audit_bus: _KillSwitchAuditBus \| None = None) -> None` | Deactivate a triggered kill switch after governed approval checks. |
| `KillSwitchManager.is_blocked(scope: str, target: str, is_live: bool = False) -> bool` | Verify whether trading is blocked for a given target. |
| `KillSwitchManager.evaluate_triggers(request: RiskAssessmentRequest, limit_results: list[LimitResult], is_live: bool = False, audit_bus: _KillSwitchAuditBus \| None = None) -> list[str]` | Statelessly parse request context and limit results to trigger switches. |
| `get_kill_switch_manager(persistence_path: str \| Path \| None = None) -> KillSwitchManager` | Retrieve or initialize the global thread-safe KillSwitchManager instance. |
| `trigger_kill_switch(scope: str, target: str, reason: str, triggered_by: str = "system", audit_bus: _KillSwitchAuditBus \| None = None) -> None` | Module-level convenience function to trigger a kill switch on the global manager. |
| `resume_after_kill_switch(scope: str, target: str, approval_token: str \| None = None, operator_role: str \| None = None, audit_bus: _KillSwitchAuditBus \| None = None) -> None` | Module-level convenience function to resume trading after a governed kill switch. |
| `KillSwitchState` (class) | Typed canonical snapshot of a kill-switch state record (V2). |
| `KillSwitchAssessment` (class) | Outcome of a canonical kill-switch scope/state evaluation (V2). |
| `KillSwitchTriggerRequest` (class) | Canonical request to trigger a governed kill-switch transition (V2). |
| `KillSwitchResumeRequest` (class) | Canonical request to resume a governed kill-switch after approval (V2). |
| `ApprovalContext` (class) | Canonical operator/approval context for a resume request (V2). |
| `check_risk_kill_switch(*args: Any, **kwargs: Any) -> Any` | Check kill-switch status, supporting V1 and V2 signatures. |
| `request_kill_switch_trigger(request: KillSwitchTriggerRequest, store: RiskStateStore) -> KillSwitchState` | Record a governed risk kill-switch transition through a storage port. |
| `validate_resume_request(request: KillSwitchResumeRequest, state: KillSwitchState, approval: ApprovalContext \| None) -> ValidationResult` | Require governed approval before a kill switch may be resumed. |
| `clear_kill_switch_after_approval(request: KillSwitchResumeRequest, store: RiskStateStore) -> KillSwitchState` | Persist an approved kill-switch resume state through a storage port. |
| `KillSwitchService.check(scope: KillSwitchScope, target: str) -> KillSwitchAssessment` | Check the current kill-switch assessment for a scope/target. |
| `KillSwitchService.trigger(request: KillSwitchTriggerRequest) -> KillSwitchState` | Trigger a governed kill-switch transition. |
| `KillSwitchService.resume(request: KillSwitchResumeRequest, approval: ApprovalContext \| None = None) -> KillSwitchState` | Resume a kill switch after validating governed approval. |
| `KillSwitchTransitionError` (model) | Raised when a kill-switch transition is not authorized. |
| `KillSwitchBlockEvaluation` (model) | Whether new live entries are blocked under the current kill-switch state. |
| `RecoveryApproval` (model) | Approval attestation used for governed kill-switch recovery. |
| `KillSwitchStateMachine.can_transition(target_state: KillSwitchState) -> bool` | Return whether the target state is allowed from the current state. |
| `KillSwitchStateMachine.transition(*, target_state: KillSwitchState, authorization: RecoveryAuthorization \| None = None) -> KillSwitchStateMachine` | Apply a governed transition and return the next state wrapper. |
| `KillSwitchService.apply_action(*, current_state: KillSwitchState, action: KillSwitchAction, authorization: RecoveryAuthorization \| None = None) -> KillSwitchStateMachine` | Apply a named action to the current state and return the next state wrapper. |
| `KillSwitchService.evaluate(snapshot: dict[str, object]) -> dict[str, object]` | Evaluate a raw risk snapshot and trigger fail-closed order blocking. |
| `evaluate_new_entry_block(current_state: KillSwitchState) -> KillSwitchBlockEvaluation` | Globally block new live entries whenever the kill switch is not fully armed. |
| `require_hard_trigger_recovery_dual_auth(approvals: tuple[RecoveryApproval, ...]) -> bool` | Require distinct Risk Manager and Compliance approvals for hard recovery. |


## FEAT-RISK-43: Kill-switch event persistence and audit helpers (app.services.risk.governance.kill_switch_audit)

| Function | Purpose |
|----------|---------|
| `KillSwitchAuditService.__init__(db_path: str \| Path) -> None` | Append-only audit logging for kill-switch state changes. |
| `KillSwitchAuditService.log_event(*, previous_state: KillSwitchState, new_state: KillSwitchState, trigger_type: str, reason_code: str, actor_type: str, actor_id: str, workflow_id: str \| None = None, metadata: dict[str, Any] \| None = None) -> KillSwitchEventRecord` | Append-only audit logging for kill-switch state changes. |


## FEAT-RISK-44: Strategy lifecycle promotion and live readiness governance (app.services.risk.governance.lifecycle)

| Function | Purpose |
|----------|---------|
| `RiskLifecycleState` (enum) | Canonical stages of a strategy lifecycle. |
| `StrategyAdmissionReview` (class) | Outcome of a strategy admission review. |
| `LiveReadinessReview` (class) | Outcome of a live readiness check. |
| `ModePromotionReview` (class) | Outcome of a mode or stage promotion review. |
| `LifecycleEvidence` (class) | Canonical evidence bundle for a V2 lifecycle transition check. |
| `LifecycleAssessment` (class) | Canonical outcome of a V2 lifecycle review (admission or readiness). |
| `RiskLifecycleGate.admit_strategy(strategy_id: str, evidence: dict[str, Any], config: RiskConfig) -> StrategyAdmissionReview` | Evaluate whether a strategy is admitted to receive capital allocations. |
| `RiskLifecycleGate.check_readiness(strategy_id: str, proposed_stage: str, market_context: dict[str, Any], _config: RiskConfig) -> LiveReadinessReview` | Check readiness requirements before live modes can be enabled. |
| `RiskLifecycleGate.promote_mode(strategy_id: str, current_stage: str, target_stage: str, evidence: dict[str, Any], config: RiskConfig, market_context: dict[str, Any] \| None = None, approval_token: object = None) -> ModePromotionReview` | Evaluate transition between lifecycle stages. |
| `review_mode_promotion(strategy_id: str, current_stage: str, target_stage: str, evidence: dict[str, Any], config: RiskConfig, market_context: dict[str, Any] \| None = None, approval_token: object = None) -> ModePromotionReview` | Review strategy mode promotion stage gating. |
| `evaluate_lifecycle_promotion(strategy_id: str, current_stage: str, target_stage: str, evidence: dict[str, Any], config: RiskConfig) -> LimitResult` | Validate if a strategy is eligible to promote to the target lifecycle stage. |
| `evaluate_live_readiness(strategy_id: str, proposed_stage: str, market_context: dict[str, Any], _config: RiskConfig) -> LimitResult` | Enforce audit, kill switch and reconciliation readiness checks. |
| `validate_lifecycle_transition(current: StrategyLifecycleState, target: StrategyLifecycleState, evidence: LifecycleEvidence) -> ValidationResult` | Reject unauthorized lifecycle stage promotion. |
| `requires_lifecycle_approval(assessment: LifecycleAssessment, policy: EffectiveRiskPolicy) -> bool` | Determine whether a lifecycle assessment requires governed approval. |


## FEAT-RISK-45: Deterministic signing helpers for risk artifacts (app.services.risk.governance.signatures)

| Function | Purpose |
|----------|---------|
| `stable_hash(value: Any) -> str` | Function stable_hash provides risk service behavior. |
| `sign_payload(value: Any, *, namespace: str = 'risk') -> str` | Function sign_payload provides risk service behavior. |


## FEAT-RISK-46: Risk-decision validity helpers for change and expiry enforcement (app.services.risk.governance.validity)

| Function | Purpose |
|----------|---------|
| `RiskDecisionValidity` (model) | Validity result for an already-issued risk decision. |
| `invalidate_for_material_proposal_change(*, approved_proposal: TradeProposal, current_proposal: TradeProposal) -> RiskDecisionValidity` | Invalidate prior risk approval when material proposal fields change. |
| `enforce_risk_decision_expiry(*, freshness_expiry: datetime, clock: Clock \| None = None) -> RiskDecisionValidity` | Invalidate risk approval when its expiry timestamp has passed. |


## FEAT-RISK-47: Final RiskGovernor decision synthesis logic (app.services.risk.governor.decision_synthesis)

| Function | Purpose |
|----------|---------|
| `GateResult` (class) | The result of evaluating a single risk gate. |
| `RiskReductionPlan` (class) | Aggregation of volume/size reductions across all risk evaluation gates. |
| `GovernorEvaluationContext` (class) | The collection of inputs, resolved policy, and outputs. |
| `determine_decision_status(results: Sequence[GateResult], _policy: EffectiveRiskPolicy) -> RiskDecisionStatus` | Applies precedence rules to determine final decision status. |
| `select_primary_risk_reason(results: Sequence[GateResult]) -> RiskReasonCode` | Selects deterministic primary failure or warning reason code. |
| `aggregate_reductions(results: Sequence[GateResult]) -> RiskReductionPlan` | Combines size/volume reductions across all evaluation gates. |
| `is_decision_token_eligible(decision: RiskDecisionPackage) -> bool` | Returns True only for bounded approved or size-reduced outcomes. |
| `synthesize_decision(context: GovernorEvaluationContext) -> RiskDecisionPackage` | Creates a final RiskDecisionPackage from ordered gate results. |


## FEAT-RISK-48: Risk Governor orchestration layer (app.services.risk.governor.governor)

| Function | Purpose |
|----------|---------|
| `RiskGovernor.review_trade(request: RiskAssessmentRequest, operator_role: str \| None = None, approval_token: str \| None = None) -> RiskDecisionPackage` | Review trade request, delegating to review_trade_risk. |
| `RiskGovernor.review_trade_risk(request: RiskAssessmentRequest, operator_role: str \| None = None, approval_token: str \| None = None) -> RiskDecisionPackage` | Execute the pre-trade risk checks pipeline for a candidate ProposedTrade. |
| `RiskGovernor.review_allocation(request: RiskAssessmentRequest) -> RiskDecisionPackage` | Review strategy budget capital allocation updates. |
| `RiskGovernor.review_allocation_proposal(request: RiskAssessmentRequest) -> RiskDecisionPackage` | Review strategy budget capital allocation updates. |
| `RiskGovernor.review_strategy_admission(request: RiskAssessmentRequest) -> RiskDecisionPackage` | Review strategy admission specifications promotion checkpoints. |
| `RiskGovernor.run_portfolio_risk_governor(request: RiskAssessmentRequest) -> RiskDecisionPackage` | Run consolidated checks across the entire current portfolio state. |
| `RiskGovernor.run_risk_governor_checks(request: RiskAssessmentRequest, operator_role: str \| None = None, approval_token: str \| None = None) -> RiskDecisionPackage` | Unified entrypoint running the appropriate risk governor checks. |
| `RiskGovernor.review_live_readiness(*args: Any, **kwargs: Any) -> Any` | Review live readiness for strategy promotion. |
| `RiskGovernor.review_mode_promotion(strategy_id: str, current_stage: str, target_stage: str, evidence: dict[str, Any], config: RiskConfig, market_context: dict[str, Any] \| None = None, approval_token: object = None) -> ModePromotionReview` | Review strategy mode promotion stage gating. |
| `review_trade(request: RiskAssessmentRequest, operator_role: str \| None = None, approval_token: str \| None = None) -> RiskDecisionPackage` | Execute pre-trade risk checks for a candidate ProposedTrade (V2). |
| `review_trade_risk(request: RiskAssessmentRequest, operator_role: str \| None = None, approval_token: str \| None = None) -> RiskDecisionPackage` | Execute pre-trade risk checks for a candidate ProposedTrade. |
| `review_allocation(request: RiskAssessmentRequest) -> RiskDecisionPackage` | Evaluate budget allocation proposal changes (V2). |
| `review_allocation_proposal(request: RiskAssessmentRequest) -> RiskDecisionPackage` | Evaluate budget allocation proposal changes across multiple strategies. |
| `review_strategy_admission(request: RiskAssessmentRequest) -> RiskDecisionPackage` | Review strategy walk-forward and promotion checks for strategy admission. |
| `run_portfolio_risk_governor(request: RiskAssessmentRequest) -> RiskDecisionPackage` | Run sequential checkpoints across consolidated portfolio states. |
| `review_live_readiness(*args: Any, **kwargs: Any) -> Any` | Review live readiness parameters for strategy promotion (supports V1 and V2). |


## FEAT-RISK-49: Portfolio lifecycle tool functions for the risk service (app.services.risk.lifecycle_tools)

| Function | Purpose |
|----------|---------|
| `admit_strategy_to_portfolio(*, strategy_id: str, reason: str, allocation: float = 0.0, request_id: str \| None = None, agent_name: str \| None = None, environment: str = 'development', dry_run: bool = True) -> dict[str, Any]` | Build a portfolio admission decision package for a strategy. |
| `promote_strategy_to_paper(*, strategy_id: str, reason: str, request_id: str \| None = None, agent_name: str \| None = None, environment: str = 'development', dry_run: bool = True) -> dict[str, Any]` | Build a paper-trading promotion decision package. |
| `promote_strategy_to_live_candidate(*, strategy_id: str, reason: str, risk_approval_id: str \| None = None, request_id: str \| None = None, agent_name: str \| None = None, environment: str = 'development', dry_run: bool = True) -> dict[str, Any]` | Build a live-candidate promotion decision package. |
| `suspend_strategy(*, strategy_id: str, reason: str, request_id: str \| None = None, agent_name: str \| None = None, environment: str = 'development', dry_run: bool = True) -> dict[str, Any]` | Build a strategy suspension decision package. |
| `retire_strategy(*, strategy_id: str, reason: str, request_id: str \| None = None, agent_name: str \| None = None, environment: str = 'development', dry_run: bool = True) -> dict[str, Any]` | Build a strategy retirement decision package. |
| `demote_strategy_to_paper(*, strategy_id: str, reason: str, request_id: str \| None = None, agent_name: str \| None = None, environment: str = 'development', dry_run: bool = True) -> dict[str, Any]` | Build a live-to-paper demotion decision package. |
| `update_strategy_status(*, strategy_id: str, target_status: str, reason: str, request_id: str \| None = None, agent_name: str \| None = None, environment: str = 'development', dry_run: bool = True) -> dict[str, Any]` | Build a generic strategy lifecycle status update package. |
| `build_risk_decision_package(*, strategy_id: str, decision: str, evidence: dict[str, Any], reason: str, request_id: str \| None = None, agent_name: str \| None = None, environment: str = 'development', dry_run: bool = True) -> dict[str, Any]` | Build the final structured risk decision handoff package. |


## FEAT-RISK-50: Single-purpose pure limit evaluators (app.services.risk.limits.checks)

| Function | Purpose |
|----------|---------|
| `check_kill_switch_state(*, kill_switch_active: bool, request_id: str \| None = None, agent_name: str \| None = None, environment: str = 'development', dry_run: bool = True) -> dict[str, Any]` | Block trading when the kill switch is active. |
| `check_stale_evidence_limit(request: RiskAssessmentRequest, _config: RiskConfig) -> LimitResult` | Check if input snapshots are stale or missing required live parameters. |
| `check_max_drawdown_limit(*, max_drawdown: float, limit: float = 0.2, request_id: str \| None = None, agent_name: str \| None = None, environment: str = 'development', dry_run: bool = True) -> dict[str, Any]` | Check account or strategy drawdown against a configured maximum. |
| `check_daily_loss_limit(*, daily_loss: float, limit: float = 0.03, request_id: str \| None = None, agent_name: str \| None = None, environment: str = 'development', dry_run: bool = True) -> dict[str, Any]` | Check daily portfolio loss against a configured maximum. |
| `check_strategy_loss_limit(*, strategy_loss: float, limit: float = 0.05, request_id: str \| None = None, agent_name: str \| None = None, environment: str = 'development', dry_run: bool = True) -> dict[str, Any]` | Check strategy-specific loss against a configured maximum. |
| `check_news_blackout(*, blackout_active: bool, request_id: str \| None = None, agent_name: str \| None = None, environment: str = 'development', dry_run: bool = True) -> dict[str, Any]` | Block trading when a news blackout window is active. |
| `check_rollover_blackout(request: RiskAssessmentRequest, _config: RiskConfig) -> LimitResult` | Check if broker midnight rollover blackout window is active. |
| `check_spread_limit(*, spread: float, limit: float = 3.0, request_id: str \| None = None, agent_name: str \| None = None, environment: str = 'development', dry_run: bool = True) -> dict[str, Any]` | Check current spread against a configured maximum. |
| `check_slippage_limit(*, slippage: float, limit: float = 2.0, request_id: str \| None = None, agent_name: str \| None = None, environment: str = 'development', dry_run: bool = True) -> dict[str, Any]` | Check expected or observed slippage against a configured maximum. |
| `check_trade_frequency_limit(*, trade_count: int, limit: int = 20, request_id: str \| None = None, agent_name: str \| None = None, environment: str = 'development', dry_run: bool = True) -> dict[str, Any]` | Check trade frequency against a configured maximum. |
| `check_pending_order_limit(request: RiskAssessmentRequest, _config: RiskConfig) -> LimitResult` | Check if the count of open pending orders exceeds the configured capacity. |
| `check_portfolio_exposure_limit(*, exposure: float, limit: float = 1.0, request_id: str \| None = None, agent_name: str \| None = None, environment: str = 'development', dry_run: bool = True) -> dict[str, Any]` | Check total portfolio exposure against a configured maximum. |
| `check_symbol_exposure_limit(*, symbol_exposure: float, limit: float = 0.25, request_id: str \| None = None, agent_name: str \| None = None, environment: str = 'development', dry_run: bool = True) -> dict[str, Any]` | Check single-symbol exposure against a configured maximum. |
| `check_currency_exposure_limit(*, currency_exposure: float, limit: float = 0.4, request_id: str \| None = None, agent_name: str \| None = None, environment: str = 'development', dry_run: bool = True) -> dict[str, Any]` | Check FX currency basket exposure against a configured maximum. |
| `check_correlation_limit(*, correlation: float, limit: float = 0.8, request_id: str \| None = None, agent_name: str \| None = None, environment: str = 'development', dry_run: bool = True) -> dict[str, Any]` | Check correlation against a configured maximum. |
| `check_var_limit(*, var: float, limit: float = 0.05, request_id: str \| None = None, agent_name: str \| None = None, environment: str = 'development', dry_run: bool = True) -> dict[str, Any]` | Check portfolio value-at-risk against a configured maximum. |
| `check_expected_shortfall_limit(request: RiskAssessmentRequest, _config: RiskConfig) -> LimitResult` | Check if portfolio Expected Shortfall exceeds tail risk ceilings. |
| `check_stress_loss_limit(request: RiskAssessmentRequest, _config: RiskConfig) -> LimitResult` | Check if maximum projected shock stress loss exceeds limits. |
| `check_leverage_limit(*, leverage: float, limit: float = 10.0, request_id: str \| None = None, agent_name: str \| None = None, environment: str = 'development', dry_run: bool = True) -> dict[str, Any]` | Check gross leverage against a configured maximum. |
| `check_margin_limit(*, margin_usage: float, limit: float = 0.5, request_id: str \| None = None, agent_name: str \| None = None, environment: str = 'development', dry_run: bool = True) -> dict[str, Any]` | Check margin usage against a configured maximum. |
| `check_kill_switch(state: KillSwitchStateEnum) -> LimitResult` | Block when a kill-switch state is active or indeterminate. |
| `check_evidence_freshness(request: RiskAssessmentRequest, policy: EffectiveRiskPolicy, now_utc: datetime) -> LimitResult` | Block stale or incomplete mandatory evidence using a resolved policy. |
| `check_daily_loss(snapshot: PortfolioRiskSnapshot, policy: EffectiveRiskPolicy) -> LimitResult` | Evaluate a portfolio snapshot's daily-loss budget against policy. |
| `check_total_drawdown(snapshot: PortfolioRiskSnapshot, policy: EffectiveRiskPolicy) -> LimitResult` | Evaluate a portfolio snapshot's total-drawdown ceiling against policy. |
| `check_exposure_limits(projected: PortfolioRiskSnapshot, policy: EffectiveRiskPolicy) -> tuple[LimitResult, ...]` | Evaluate portfolio-level exposure against the resolved policy. |
| `check_tail_risk_limits(var: VaRSnapshot, es: ExpectedShortfallSnapshot, stress: StressSummary, policy: EffectiveRiskPolicy) -> tuple[LimitResult, ...]` | Evaluate VaR, Expected Shortfall, and stress-loss limits together. |
| `check_execution_limits(execution: ExecutionRiskSnapshot, policy: EffectiveRiskPolicy) -> tuple[LimitResult, ...]` | Evaluate spread, marketability, and lot-step limits from a snapshot. |
| `check_cvar_limit(*, cvar: float, limit: float = 0.08, request_id: str \| None = None, agent_name: str \| None = None, environment: str = 'development', dry_run: bool = True) -> dict[str, Any]` | Check conditional value-at-risk against a configured maximum. |
| `run_risk_governor_checks(*, checks: list[dict[str, Any]], request_id: str \| None = None, agent_name: str \| None = None, environment: str = 'development', dry_run: bool = True) -> dict[str, Any]` | Aggregate deterministic risk governor check results. |


## FEAT-RISK-51: Circuit-breaker rules for governance state (app.services.risk.limits.circuit_breakers)

| Function | Purpose |
|----------|---------|
| `evaluate_circuit_breakers(policy: RiskPolicy, existing_state: CircuitBreakerState \| None = None, account_equity: float \| None = None, peak_equity: float \| None = None, breach_count: int = 0) -> tuple[CircuitBreakerState \| None, LimitEvent \| None]` | Return breaker state and optional breaker breach event. |


## FEAT-RISK-52: Deterministic limit-check contracts (app.services.risk.limits.contracts)

| Function | Purpose |
|----------|---------|
| `LimitResult` (class) | The result of evaluating a single limit check. |
| `LimitCheckFunction` (protocol) | Protocol for a single deterministic pre-trade limit check callable. |
| `LimitCheck` (class) | Typed limit-name, required-evidence, severity, evaluator, precedence contract. |
| `LimitAssessment` (class) | Aggregated outcome of evaluating an ordered limit-check sequence. |


## FEAT-RISK-53: Ordered limit-check orchestration (app.services.risk.limits.engine)

| Function | Purpose |
|----------|---------|
| `LimitEngine.execute(request: RiskAssessmentRequest) -> list[LimitResult]` | Execute the full, ordered sequence of limit checks. |
| `run_limit_checks(request: RiskAssessmentRequest, risk_config: RiskConfig \| None = None) -> tuple[RiskDecisionStatus, RiskReasonCode, str, list[str], str, list[LimitResult]]` | Stateless runner function evaluating all limit checks and aggregating. |
| `check_risk_limits(request: RiskAssessmentRequest, config: RiskConfig) -> list[LimitResult]` | Evaluate all configured risk limits sequentially. |
| `select_primary_failure(results: Sequence[LimitResult], precedence: LimitPrecedence = DEFAULT_LIMIT_PRECEDENCE) -> LimitResult \| None` | Select the stable principal failing result from a set of limit results. |
| `build_composite_breach_flags(results: Sequence[LimitResult]) -> frozenset[RiskReasonCode]` | Compose deterministic composite breach flags from limit results. |
| `evaluate_ordered_limits(context: LimitContext, checks_sequence: tuple[LimitCheck, ...] = ORDERED_LIMIT_CHECKS) -> LimitAssessment` | Run the immutable ordered-check sequence and aggregate outcomes. |


## FEAT-RISK-54: Structured governance events and decisions (app.services.risk.limits.events)

| Function | Purpose |
|----------|---------|
| `LimitEvent` (model) | Explainable governance event suitable for later persistence. |
| `PolicyDecision.policy_events -> list[LimitEvent]` | Structured result from the policy engine. |


## FEAT-RISK-55: Hard governance rules for risk policy enforcement (app.services.risk.limits.hard_limits)

| Function | Purpose |
|----------|---------|
| `build_budget_utilizations(equity: float, current_var: float, new_var: float, delta_var: float, current_es: float, new_es: float, delta_es: float, current_margin_used: float \| None, new_margin_used: float \| None, max_single_rc: float, rc_map_new: dict[str, float] \| None, currency_exposure: dict[str, float] \| None, gross_portfolio_notional: float \| None, cluster_metrics: dict[str, dict[str, float]] \| None, policy: RiskPolicy) -> dict[str, BudgetUtilization]` | Build normalized budget utilization records for policy checks. |
| `evaluate_hard_limits(equity: float, current_var: float, new_var: float, delta_var: float, current_es: float, new_es: float, delta_es: float, current_margin_used: float \| None, new_margin_used: float \| None, rc_map_new: dict[str, float] \| None, currency_exposure: dict[str, float] \| None, gross_portfolio_notional: float \| None, cluster_metrics: dict[str, dict[str, float]] \| None, policy: RiskPolicy) -> list[LimitEvent]` | Return hard-limit breaches for a portfolio transition. |


## FEAT-RISK-56: Policy and governance models for risk limit evaluation (app.services.risk.limits.models)

| Function | Purpose |
|----------|---------|
| `RiskPolicy.with_updates(**updates: Any) -> RiskPolicy` | Return a new policy with only the supplied fields changed. |
| `CorrelationPreference` (model) | Soft preference to favor lower correlation additions (allocator only). |
| `OverrideRecord` (model) | Track a policy override applied by the governance layer. |
| `CircuitBreakerState` (model) | Simple governance halt state. |
| `BudgetUtilization` (model) | Normalized utilization record for one policy budget. |
| `GovernanceState` (model) | Current compliance state to attach to snapshots and decisions. |


## FEAT-RISK-57: Governance policy orchestration for risk checks (app.services.risk.limits.policy_engine)

| Function | Purpose |
|----------|---------|
| `PolicyEngine.effective_policy(policy: RiskPolicy, regime: RegimeState \| None = None) -> tuple[RiskPolicy, list[OverrideRecord]]` | Return the effective policy after regime-specific tightening. |
| `PolicyEngine.evaluate_pre_trade(*, equity: float, current_var: float, new_var: float, delta_var: float, current_es: float, new_es: float, delta_es: float, current_margin_used: float \| None, new_margin_used: float \| None, rc_map_new: dict[str, float] \| None, currency_exposure: dict[str, float] \| None, gross_portfolio_notional: float \| None, cluster_metrics: dict[str, dict[str, float]] \| None, policy: RiskPolicy, regime: RegimeState \| None = None, peak_equity: float \| None = None, breaker_state: CircuitBreakerState \| None = None) -> PolicyDecision` | Evaluate pre-trade governance using the effective policy. |
| `PolicyEngine.evaluate_post_trade(*, equity: float, portfolio_var: float, portfolio_es: float, margin_used: float \| None, rc_map: dict[str, float] \| None, currency_exposure: dict[str, float] \| None, gross_portfolio_notional: float \| None, cluster_metrics: dict[str, dict[str, float]] \| None, policy: RiskPolicy, regime: RegimeState \| None = None, peak_equity: float \| None = None, breaker_state: CircuitBreakerState \| None = None) -> PolicyDecision` | Evaluate current portfolio compliance using the effective policy. |
| `as_policy(limits: RiskPolicy \| None) -> RiskPolicy` | Normalize legacy RiskLimits-style input to RiskPolicy. |


## FEAT-RISK-58: Post-trade governance checks for existing portfolio state (app.services.risk.limits.post_trade_checks)

| Function | Purpose |
|----------|---------|
| `evaluate_post_trade(*, equity: float, portfolio_var: float, portfolio_es: float, margin_used: float \| None, rc_map: dict[str, float] \| None, currency_exposure: dict[str, float] \| None, gross_portfolio_notional: float \| None, cluster_metrics: dict[str, dict[str, float]] \| None, policy: RiskPolicy, peak_equity: float \| None = None, breaker_state: CircuitBreakerState \| None = None) -> PolicyDecision` | Evaluate current portfolio compliance without a new candidate trade. |


## FEAT-RISK-59: Pre-trade governance evaluation helpers (app.services.risk.limits.pre_trade_checks)

| Function | Purpose |
|----------|---------|
| `evaluate_pre_trade(*, equity: float, current_var: float, new_var: float, delta_var: float, current_es: float, new_es: float, delta_es: float, current_margin_used: float \| None, new_margin_used: float \| None, rc_map_new: dict[str, float] \| None, currency_exposure: dict[str, float] \| None, gross_portfolio_notional: float \| None, cluster_metrics: dict[str, dict[str, float]] \| None, policy: RiskPolicy, peak_equity: float \| None = None, breaker_state: CircuitBreakerState \| None = None) -> PolicyDecision` | Evaluate one candidate portfolio transition before execution. |


## FEAT-RISK-60: Soft warning rules for near-limit governance conditions (app.services.risk.limits.soft_limits)

| Function | Purpose |
|----------|---------|
| `evaluate_soft_limits(utilizations: dict[str, BudgetUtilization], policy: RiskPolicy) -> list[LimitEvent]` | Return warning events for near-limit utilization. |


## FEAT-RISK-61: Broker and execution-environment risk checks (app.services.risk.live.broker_risk)

| Function | Purpose |
|----------|---------|
| `broker_risk_state(market_state: dict[str, Any], thresholds: dict[str, Any]) -> dict[str, Any]` | Function broker_risk_state provides risk service behavior. |


## FEAT-RISK-62: Risk-Integrated Multi-Strategy Live Trading Engine (app.services.risk.live.engine)

| Function | Purpose |
|----------|---------|
| `RiskIntegratedEngine.__init__(config_path: str) -> None` | Initialize risk-integrated engine. |
| `RiskIntegratedEngine.initialize() -> bool` | Initialize engine with risk management components. |
| `RiskIntegratedEngine.get_status() -> dict` | Get engine status including risk management state. |


## FEAT-RISK-63: Portfolio Manager (app.services.risk.live.portfolio_manager)

| Function | Purpose |
|----------|---------|
| `PortfolioManager.__init__(client: 'MT5Client', account: object, max_total_positions: int = 20, max_positions_per_symbol: int = 3, max_portfolio_risk_percent: float = 10.0, max_correlated_positions: int = 5) -> None` | Initialize portfolio manager. |
| `PortfolioManager.refresh_all_positions() -> None` | Refresh all positions from MT5. |
| `PortfolioManager.can_open_position(symbol: str, strategy_name: str, volume: float, signal_type: str) -> tuple[bool, str]` | Check if position can be opened based on portfolio rules. |
| `PortfolioManager.get_portfolio_summary() -> dict` | Get portfolio summary statistics. |
| `PortfolioManager.get_symbol_exposure(symbol: str) -> dict` | Get exposure details for specific symbol. |


## FEAT-RISK-64: Live Trading with Risk Management Entry Point (app.services.risk.live.run)

| Function | Purpose |
|----------|---------|
| `parse_arguments()` | Parse command-line arguments. |
| `validate_config_path(config_path: str) -> bool` | Validate configuration file exists. |
| `setup_engine(config_path: str) -> RiskIntegratedEngine \| None` | Initialize and setup the risk-integrated trading engine. |
| `register_signal_handlers(engine: RiskIntegratedEngine) -> None` | Register signal handlers for graceful shutdown. |
| `print_startup_info(engine: RiskIntegratedEngine) -> None` | Print engine startup information. |
| `main() -> int` | Execute main entry point logic. |


## FEAT-RISK-65: Safety Checks (app.services.risk.live.safety_checks)

| Function | Purpose |
|----------|---------|
| `SafetyChecker.__init__(client: 'MT5Client', account: object, symbol_info: object, min_balance: float, min_margin_level: float) -> None` | Initialize safety checker. |
| `SafetyChecker.check_all(volume: float, position_count: int, daily_trades: int, max_positions: int, max_daily_trades: int) -> tuple[bool, str]` | Run all safety checks. |
| `SafetyChecker.check_connection() -> tuple[bool, str]` | Check MT5 connection is active. |
| `SafetyChecker.check_account() -> tuple[bool, str]` | Check account status and margin. |
| `SafetyChecker.check_symbol() -> tuple[bool, str]` | Check symbol trading status. |
| `SafetyChecker.check_volume(volume: float) -> tuple[bool, str]` | Check if volume is within allowed limits. |
| `SafetyChecker.check_limits(position_count: int, daily_trades: int, max_positions: int, max_daily_trades: int) -> tuple[bool, str]` | Check position and trade count limits. |


## FEAT-RISK-66: Account state metric family (app.services.risk.metrics.account_risk)

| Function | Purpose |
|----------|---------|
| `AccountRiskMetrics.compute(context: MetricContext) -> list[MetricRow]` | Compute account-level current-state risk metrics. |


## FEAT-RISK-67: Base contracts for normalized risk metrics (app.services.risk.metrics.base)

| Function | Purpose |
|----------|---------|
| `MetricRow` (model) | One normalized metric row suitable for later persistence. |
| `MetricContext` (model) | Execution context for one metric registry run. |
| `MetricFamily.compute(context: MetricContext) -> list[MetricRow]` | Compute normalized metric rows for this family. |
| `RiskSnapshot` (model) | Current-state risk snapshot built from normalized metric rows. |


## FEAT-RISK-68: Concentration metrics for the current portfolio snapshot (app.services.risk.metrics.concentration)

| Function | Purpose |
|----------|---------|
| `ConcentrationMetrics.compute(context: MetricContext) -> list[MetricRow]` | Compute simple concentration and cluster concentration metrics. |


## FEAT-RISK-69: Correlation analytics for structural portfolio fragility (app.services.risk.metrics.correlation_risk)

| Function | Purpose |
|----------|---------|
| `CorrelationRiskMetrics.compute(context: MetricContext) -> list[MetricRow]` | Compute correlation, overlap, and cluster correlation metrics. |


## FEAT-RISK-70: Currency exposure metric family (app.services.risk.metrics.currency_exposure)

| Function | Purpose |
|----------|---------|
| `CurrencyExposureMetrics.compute(context: MetricContext) -> list[MetricRow]` | Compute simple currency exposure rows from canonical symbol data. |


## FEAT-RISK-71: Drawdown analytics for portfolio risk snapshots (app.services.risk.metrics.drawdown_risk)

| Function | Purpose |
|----------|---------|
| `DrawdownRiskMetrics.compute(context: MetricContext) -> list[MetricRow]` | Compute drawdown metrics when an equity history is available. |


## FEAT-RISK-72: Margin and leverage metric family (app.services.risk.metrics.margin_risk)

| Function | Purpose |
|----------|---------|
| `MarginRiskMetrics.compute(context: MetricContext) -> list[MetricRow]` | Compute current margin and leverage style metrics. |


## FEAT-RISK-73: Shared metric math derived from the existing governance formulas (app.services.risk.metrics.math)

| Function | Purpose |
|----------|---------|
| `state_positions_map(state: PortfolioState) -> dict[str, float]` | Return the signed position map for the current portfolio state. |
| `state_symbol_list(state: PortfolioState) -> list[str]` | Return active symbols in deterministic order. |
| `build_returns_df(state: PortfolioState, symbols: list[str] \| None = None, exclude_current_bar: bool = True) -> pd.DataFrame` | Build a log-returns dataframe from canonical market slices. |
| `estimate_covariance(returns_df: pd.DataFrame, symbols: list[str], limits: RiskLimits) -> np.ndarray` | Estimate covariance using the same rolling logic as the governor. |
| `estimate_correlation_matrix(returns_df: pd.DataFrame, symbols: list[str], limits: RiskLimits) -> np.ndarray` | Estimate the latest rolling correlation matrix for active symbols. |
| `apply_corr_floors(corr_mat: np.ndarray, limits: RiskLimits) -> np.ndarray` | Apply correlation stress only when stressed covariance is requested. |
| `symbol_notional_value(state: PortfolioState, symbol: str, lots: float, exclude_current_bar: bool = False) -> float` | Estimate symbol notional value normalized to account currency. |
| `build_weights_from_state(state: PortfolioState, symbols: list[str] \| None = None, exclude_current_bar: bool = False) -> np.ndarray` | Build absolute notional weights for active symbols. |
| `build_signed_weights_from_state(state: PortfolioState, symbols: list[str] \| None = None, exclude_current_bar: bool = False) -> np.ndarray` | Build signed notional weights normalized by gross absolute notional. |
| `build_notional_vector(state: PortfolioState, symbols: list[str] \| None = None, exclude_current_bar: bool = False) -> np.ndarray` | Return absolute notional exposures for active symbols. |
| `compute_symbol_volatility_state(returns_df: pd.DataFrame, symbols: list[str], limits: RiskLimits) -> dict[str, float]` | Return latest rolling realized volatility per symbol. |
| `average_off_diagonal(corr_mat: np.ndarray) -> float` | Return the mean off-diagonal correlation for a square matrix. |
| `max_off_diagonal(corr_mat: np.ndarray) -> float` | Return the maximum off-diagonal correlation for a square matrix. |
| `compute_diversification_ratio(weights: np.ndarray, cov: np.ndarray) -> float` | Return the diversification ratio for the current portfolio. |
| `compute_effective_independent_bets(corr_mat: np.ndarray) -> float` | Estimate effective independent bets from correlation eigenvalues. |
| `compute_hidden_overlap_score(weights: np.ndarray, corr_mat: np.ndarray) -> float` | Estimate hidden overlap from weighted pairwise correlation. |
| `compute_cluster_exposure_breakdown(state: PortfolioState, symbols: list[str] \| None = None, exclude_current_bar: bool = False) -> dict[str, float]` | Aggregate gross notional exposure by cluster. |
| `compute_cluster_correlation_summary(symbols: list[str], corr_mat: np.ndarray, symbol_to_cluster: dict[str, Any]) -> dict[str, dict[str, float]]` | Summarize average and max intra-cluster correlation. |
| `compute_risk_contributions_pct(weights: np.ndarray, cov: np.ndarray, symbols: list[str]) -> dict[str, float]` | Compute percentage contribution to total portfolio variance. |
| `estimate_margin_used(state: PortfolioState) -> float \| None` | Return current margin used from the canonical account state when available. |
| `compute_portfolio_var_es(state: PortfolioState, limits: RiskLimits \| None = None) -> tuple[float, float, dict[str, float] \| None, dict[str, Any]]` | Compute current portfolio VaR/ES and shared risk math artifacts. |
| `extract_currency_exposure(state: PortfolioState) -> dict[str, float]` | Build a simple currency exposure map from symbol metadata or naming conventions. |


## FEAT-RISK-74: Portfolio-level risk metric family (app.services.risk.metrics.portfolio_risk)

| Function | Purpose |
|----------|---------|
| `PortfolioRiskMetrics.compute(context: MetricContext) -> list[MetricRow]` | Compute top-level current-state portfolio risk metrics. |


## FEAT-RISK-75: Position-level risk metrics (app.services.risk.metrics.position_risk)

| Function | Purpose |
|----------|---------|
| `PositionRiskMetrics.compute(context: MetricContext) -> list[MetricRow]` | Compute one row set per active position. |


## FEAT-RISK-76: Metric registry for the core risk metric MVP (app.services.risk.metrics.registry)

| Function | Purpose |
|----------|---------|
| `MetricRegistry.register(family: MetricFamily) -> None` | Simple family registry for normalized metric calculation. |
| `MetricRegistry.extend(families: Iterable[MetricFamily]) -> None` | Simple family registry for normalized metric calculation. |
| `MetricRegistry.compute_all(context: MetricContext) -> list[MetricRow]` | Simple family registry for normalized metric calculation. |
| `build_default_metric_registry() -> MetricRegistry` | Build the default Phase 2 metric family registry. |


## FEAT-RISK-77: Strategy exposure metric family (app.services.risk.metrics.strategy_risk)

| Function | Purpose |
|----------|---------|
| `StrategyRiskMetrics.compute(context: MetricContext) -> list[MetricRow]` | Aggregate exposures by strategy identifier when present. |


## FEAT-RISK-78: Stress scenario metrics for portfolio snapshots (app.services.risk.metrics.stress_risk)

| Function | Purpose |
|----------|---------|
| `StressRiskMetrics.compute(context: MetricContext) -> list[MetricRow]` | Compute deterministic scenario losses and stressed summaries. |


## FEAT-RISK-79: Symbol-level risk metrics (app.services.risk.metrics.symbol_risk)

| Function | Purpose |
|----------|---------|
| `SymbolRiskMetrics.compute(context: MetricContext) -> list[MetricRow]` | Compute symbol-level exposure, weight, and RC metrics. |


## FEAT-RISK-80: Tail-risk metrics that wrap the shared portfolio VaR/ES math (app.services.risk.metrics.var_cvar)

| Function | Purpose |
|----------|---------|
| `TailRiskMetrics.compute(context: MetricContext) -> list[MetricRow]` | Expose method-tagged VaR/CVaR metrics without changing the existing snapshot keys. |


## FEAT-RISK-81: Volatility analytics for structural portfolio fragility (app.services.risk.metrics.volatility_risk)

| Function | Purpose |
|----------|---------|
| `VolatilityRiskMetrics.compute(context: MetricContext) -> list[MetricRow]` | Compute symbol and portfolio volatility fragility metrics. |


## FEAT-RISK-82: Risk governance canonical contracts and models (app.services.risk.models.contracts)

| Function | Purpose |
|----------|---------|
| `RiskContract.validate_metadata_structure(value: dict[str, Any]) -> dict[str, Any]` | Validate metadata namespacing and secret safety. |
| `RiskContract.validate_trace_identifiers() -> RiskContract` | Validate trace identifier fields. |
| `RiskContract.validate_finite_decimals() -> RiskContract` | Ensure all Decimal values within the model are finite numbers. |
| `RiskContract.to_json() -> str` | Serialize contract to deterministic canonical JSON string. |
| `RiskContract.content_hash() -> str` | Calculate a stable SHA256 hash over business-data fields only. |
| `RiskContract.contract_hash() -> str` | Calculate SHA256 hash over the full serialized contract. |
| `RiskContract.check_compatibility(target_version: str) -> bool` | Check whether this contract version is compatible with a target. |
| `RiskEvidenceRef` (class) | Reference tracking data source or external snapshot proof. |
| `ProposedTrade.sync_trade_fields() -> ProposedTrade` | Synchronize alias fields for ProposedTrade. |
| `ProposedAllocation` (class) | Candidate strategy capital allocation budgets. |
| `StrategyAdmissionRequest` (class) | Request to admit a new strategy to the system registry. |
| `LiveReadinessRequest` (class) | Canonical request envelope for a V2 live readiness review. |
| `PortfolioState` (class) | Consolidated state snapshot of the trading account and positions. |
| `RiskSubConfig` (class) | Sub-configuration for general risk caps. |
| `DrawdownSubConfig` (class) | Sub-configuration for drawdown/loss thresholds. |
| `CorrelationSubConfig` (class) | Sub-configuration for correlation window parameters. |
| `TailRiskSubConfig` (class) | Sub-configuration for tail-risk limits. |
| `ExecutionSubConfig` (class) | Sub-configuration for execution blackout and spread controls. |
| `RiskConfig` (class) | Configuration profile containing policy rules and risk limits. |
| `RiskAssessmentRequest.sync_request_fields() -> RiskAssessmentRequest` | Synchronize alias fields for RiskAssessmentRequest. |
| `AccountRiskSnapshot` (class) | Sub-snapshot focused on account equity limits. |
| `MarketRiskSnapshot` (class) | Sub-snapshot capturing market regime parameters. |
| `PositionRiskSnapshot` (class) | Risk breakdown of a single open position. |
| `PendingOrderRiskSnapshot` (class) | Exposure details of a pending order. |
| `PortfolioRiskSnapshot` (class) | Composite snapshot summarizing risk concentrations and metrics. |
| `CurrencyLegExposure` (class) | Currency breakdown for a single leg of a trade. |
| `CurrencyExposure` (class) | Portfolio currency leg exposure breakdown. |
| `SymbolExposure` (class) | Portfolio symbol exposure breakdown. |
| `CorrelationSnapshot` (class) | Rolling correlation matrix output details. |
| `CorrelationMatrix` (class) | Calculated pairwise correlation matrix for symbols. |
| `VaRSnapshot` (class) | Calculated Value-at-Risk parameters. |
| `ExpectedShortfallSnapshot` (class) | Calculated Expected Shortfall metrics. |
| `StressScenarioResult` (class) | Outcome of a single stress scenario simulation. |
| `MarginRiskSnapshot` (class) | Margin metrics snapshot. |
| `ExecutionRiskSnapshot` (class) | Execution feasibility conditions. |
| `RiskApprovalToken` (class) | Cryptographically signed approval token allowing order routing. |
| `RiskDecisionToken` (class) | Token representing risk decision. |
| `RiskDecisionPackage.sync_package_fields() -> RiskDecisionPackage` | Synchronize alias fields for RiskDecisionPackage. |
| `RiskWarning` (class) | Warning messages produced during evaluation. |
| `RiskReduction` (class) | Details of a volume scale-down suggestion. |
| `RiskMemo` (model) | Class RiskMemo provides risk service behavior. |
| `RiskBudget` (class) | Strategy allocation limit limits. |
| `RiskBudgetUtilization` (class) | Strategy budget utilization snapshot. |
| `RiskAuditEvent` (class) | Tamper-evident record of a single governor request. |
| `PolicyScope` (class) | Scope criteria for selecting matching policy rules. |
| `PolicyRule` (class) | Scoped override rules for risk config profiles. |
| `PositionSizingRequest` (class) | Details needed to calculate position size options. |
| `PositionSizingResult` (class) | Output calculated by the position sizing engine. |
| `StressScenario` (class) | Hypothetical macro market shock parameter sets. |
| `RiskPolicyProfile` (class) | Policy profile metadata wrapping config parameters. |
| `validate_risk_assessment_request(request: RiskAssessmentRequest) -> ValidationResult` | Rejects missing or invalid canonical evidence before calculation. |
| `create_risk_decision_package(decision_id: str, request_id: str, workflow_id: str, status: RiskDecisionStatus, rule_key: str, config_hash: str, reason: str, composite_breach_flags: list[str], calculated_volume: Decimal, details: dict[str, Any] \| None = None) -> RiskDecisionPackage` | Factory function to build a canonical RiskDecisionPackage. |
| `utc_now() -> str` | Function utc_now provides risk service behavior. |
| `RiskProposal` (model) | Class RiskProposal provides risk service behavior. |
| `RiskGovernorDecision` (model) | Class RiskGovernorDecision provides risk service behavior. |


## FEAT-RISK-83: Risk governance enums and catalogs (app.services.risk.models.enums)

| Function | Purpose |
|----------|---------|
| `RiskDecisionStatus` (enum) | Canonical outcomes of the risk review process. |
| `RiskMode` (enum) | Execution mode of the trading system. |
| `RiskAction` (enum) | Governed actions requiring risk approval. |
| `RiskSeverity` (enum) | Severity levels for violations or events. |
| `RiskReasonCode.description -> str (property)` | Get the stable description for the reason code. |
| `KillSwitchStateEnum` (enum) | Safety kill-switch states. |
| `KillSwitchReason` (enum) | Reason codes explaining why a kill switch was triggered. |
| `list_risk_reason_codes() -> tuple[RiskReasonCode, ...]` | Returns the stable reason-code catalogue in deterministic order. |
| `risk_severity_rank(severity: RiskSeverity) -> int` | Returns stable ordering rank for aggregation and primary-failure selection. |


## FEAT-RISK-84: Risk governance contracts serialization (app.services.risk.models.serialization)

| Function | Purpose |
|----------|---------|
| `to_canonical_risk_payload(model: BaseModel) -> dict[str, object]` | Emit stable, JSON-safe fields for a canonical risk model. |
| `from_canonical_risk_payload(payload: Mapping[str, object], model_type: type[RiskModelT]) -> RiskModelT` | Validate and restore a known model type. |
| `validate_risk_model_round_trip(model: BaseModel) -> ValidationResult` | Verifies canonicalization and round-trip integrity for a risk model. |


## FEAT-RISK-85: Logging, latency, error, and metrics decorators for public risk boundaries (app.services.risk.observability.decorators)

| Function | Purpose |
|----------|---------|
| `RiskLogger.info(message: str, *args: Any, **kwargs: Any) -> None` | Log info level message. |
| `RiskLogger.debug(message: str, *args: Any, **kwargs: Any) -> None` | Log debug level message. |
| `RiskLogger.error(message: str, *args: Any, **kwargs: Any) -> None` | Log error level message. |
| `RiskLogger.warning(message: str, *args: Any, **kwargs: Any) -> None` | Log warning level message. |
| `RiskBoundaryEvent` (class) | Carries logging detail across boundaries. |
| `log_risk_boundary_event(event: RiskBoundaryEvent, logger: RiskLogger) -> None` | Emits structured logs without raw secrets or private payloads. |
| `risk_observed(operation: str, metrics: MetricsSink, logger: RiskLogger \| None = None) -> Callable[[RiskCallableT], RiskCallableT]` | Wrap public boundaries with logging, latency measurement, and error handling. |
| `measure_risk_latency(operation: str, metrics: MetricsSink) -> Callable[[RiskCallableT], RiskCallableT]` | Record execution duration in milliseconds through the metrics sink. |


## FEAT-RISK-86: Risk metrics and observability event sinks (app.services.risk.observability.metrics)

| Function | Purpose |
|----------|---------|
| `MetricRecord` (TypedDict) | Stored metric sample. |
| `MetricRegistry.record(*, name: str, kind: str, value: float, labels: Mapping[str, object] \| None = None) -> MetricRecord` | Record one metric sample after label validation. |
| `MetricRegistry.export_prometheus_text() -> str` | Export recorded metrics in Prometheus-compatible text format. |
| `MetricsSink.record(*, name: str, kind: str, value: float, labels: Mapping[str, object] \| None = None) -> object` | Record a single metric sample. |
| `InMemoryRiskMetricsSink.record(*, name: str, kind: str, value: float, labels: Mapping[str, object] \| None = None) -> None` | Record a metric event in memory. |
| `RiskObservabilityEvent` (dataclass) | Observability event mapping to a structured metric. |
| `emit_risk_metrics(event: RiskObservabilityEvent, sink: MetricsSink) -> None` | Emit an observability event to the metric sink. |
| `build_decision_metrics(decision: RiskDecisionPackage) -> tuple[RiskObservabilityEvent, ...]` | Produce count/rate/reason-code events from a decision. |
| `build_latency_metric(operation: str, duration_ms: Decimal) -> RiskObservabilityEvent` | Produce a latency metric event. |


## FEAT-RISK-87: Small bounded allocation recommendation helpers (app.services.risk.optimization.allocation_optimizer)

| Function | Purpose |
|----------|---------|
| `AllocationOptimizer.__init__(capital_efficiency_ranker: CapitalEfficiencyRanker \| None = None) -> None` | Generate simple add, remove, and resize candidates. |
| `AllocationOptimizer.generate(state: PortfolioState, snapshot: RiskSnapshot, scorecard: RiskScorecard, evaluator: MarginalRiskEvaluator, candidate_symbols: Iterable[str] \| None = None, max_items: int = 5) -> list[RecommendationResult]` | Generate simple add, remove, and resize candidates. |


## FEAT-RISK-88: Soft RC-budget allocation planner built on shared portfolio math (app.services.risk.optimization.allocation_planner)

| Function | Purpose |
|----------|---------|
| `AllocationPlanner.__init__(risk_source: GovernanceEngine, corr_pref: CorrelationPreference \| None = None) -> None` | Compute target lots using risk-contribution budgeting. |
| `AllocationPlanner.compute_target_lots(symbols: list[str], base_lots: dict[str, float], budgets: dict[str, float] \| None = None, regime: RegimeState \| None = None, max_iters: int = 50, lr: float = 0.25) -> dict[str, float]` | Compute target lots using risk-contribution budgeting. |
| `AllocationPlanner.lots_to_deltas(current: dict[str, float], target: dict[str, float]) -> dict[str, float]` | Compute target lots using risk-contribution budgeting. |


## FEAT-RISK-89: Capital-efficiency ranking helpers for the recommendation layer (app.services.risk.optimization.capital_efficiency)

| Function | Purpose |
|----------|---------|
| `CapitalEfficiencyRanker.rank(snapshot: RiskSnapshot) -> list[dict[str, float]]` | Rank positions by risk burden relative to portfolio weight. |
| `CapitalEfficiencyRanker.build_reduce_candidates(state: PortfolioState, snapshot: RiskSnapshot, scorecard: RiskScorecard, evaluator: MarginalRiskEvaluator, max_items: int = 2, reduction_frac: float = 0.25) -> list[RecommendationResult]` | Rank positions by risk burden relative to portfolio weight. |


## FEAT-RISK-90: Simple hedge candidate evaluation helpers (app.services.risk.optimization.hedge_optimizer)

| Function | Purpose |
|----------|---------|
| `HedgeOptimizer.generate(state: PortfolioState, snapshot: RiskSnapshot, scorecard: RiskScorecard, evaluator: MarginalRiskEvaluator, hedge_symbols: Iterable[str], max_items: int = 2) -> list[RecommendationResult]` | Evaluate a small hedge shortlist by testing both trade directions. |


## FEAT-RISK-91: Marginal risk evaluation helpers for hypothetical actions (app.services.risk.optimization.marginal_risk)

| Function | Purpose |
|----------|---------|
| `build_state_risk_engine(state: PortfolioState) -> PortfolioRiskEngine` | Build a portfolio risk engine backed by canonical state. |
| `lookup_metric_value(snapshot: RiskSnapshot, metric_key: str, scope: str = 'portfolio', scope_key: str \| None = None) -> float \| None` | Return one numeric metric value from a normalized snapshot. |
| `overall_score(scorecard: RiskScorecard) -> float` | Return the overall scorecard score or zero when absent. |
| `clone_state_with_delta(state: PortfolioState, symbol: str, delta_lots: float, projected_margin_used: float \| None = None) -> PortfolioState` | Create a shallow cloned portfolio state with one symbol delta applied. |
| `MarginalRiskEvaluator.__init__(snapshot_engine: RiskSnapshotEngine \| None = None, scorecard_engine: RiskScorecardEngine \| None = None) -> None` | Evaluate one hypothetical action against snapshot, scorecard, and governance. |
| `MarginalRiskEvaluator.evaluate_action(state: PortfolioState, action: RecommendationAction, snapshot: RiskSnapshot \| None = None, scorecard: RiskScorecard \| None = None) -> RecommendationResult` | Evaluate a hypothetical action by rebuilding snapshot and scorecard. |


## FEAT-RISK-92: Normalized recommendation models for the risk optimization layer (app.services.risk.optimization.models)

| Function | Purpose |
|----------|---------|
| `RecommendationAction` (model) | One hypothetical portfolio action. |
| `RecommendationScore` (model) | Explainable scoring components for one recommendation. |
| `RecommendationResult` (model) | One ranked recommendation with projected impact. |
| `RecommendationBatch` (model) | Ranked recommendation set for one current snapshot. |


## FEAT-RISK-93: Rebalance recommendation helpers built on the shared RC rebalance math (app.services.risk.optimization.rebalance_suggestions)

| Function | Purpose |
|----------|---------|
| `RebalanceSuggestionEngine.generate(state: PortfolioState, snapshot: RiskSnapshot, scorecard: RiskScorecard, evaluator: MarginalRiskEvaluator, target_rc_budget: dict[str, float] \| None = None, max_items: int = 3) -> list[RecommendationResult]` | Generate explainable rebalance suggestions from RC budgeting. |


## FEAT-RISK-94: Recommendation engine built on risk snapshots, scorecards, and governance (app.services.risk.optimization.recommendation_engine)

| Function | Purpose |
|----------|---------|
| `RecommendationEngine.__init__(snapshot_engine: RiskSnapshotEngine \| None = None, scorecard_engine: RiskScorecardEngine \| None = None, evaluator: MarginalRiskEvaluator \| None = None, allocation_optimizer: AllocationOptimizer \| None = None, hedge_optimizer: HedgeOptimizer \| None = None, rebalance_engine: RebalanceSuggestionEngine \| None = None, capital_efficiency_ranker: CapitalEfficiencyRanker \| None = None) -> None` | Build a ranked recommendation batch from the current portfolio state. |
| `RecommendationEngine.build_recommendations(state: PortfolioState, snapshot: RiskSnapshot \| None = None, scorecard: RiskScorecard \| None = None, candidate_symbols: Iterable[str] \| None = None, hedge_symbols: Iterable[str] \| None = None, max_recommendations: int = 10) -> RecommendationBatch` | Build one ranked recommendation batch for the supplied portfolio state. |


## FEAT-RISK-95: Compliance profile domain models (app.services.risk.policy.compliance)

| Function | Purpose |
|----------|---------|
| `RetentionPolicy` (model) | Retention and export controls for a compliance profile. |
| `ApprovalPolicy` (model) | Approval routing requirements under a compliance profile. |
| `ComplianceProfile` (model) | Parsed compliance profile definition. |


## FEAT-RISK-96: Compliance rollout helpers and profile seeds (app.services.risk.policy.compliance_rollout)

| Function | Purpose |
|----------|---------|
| `seed_internal_non_regulated_profile() -> ComplianceProfile` | Seed the default internal non-regulated compliance profile. |
| `seed_uae_enterprise_profile() -> ComplianceProfile` | Seed the UAE enterprise profile as the initial production baseline. |
| `require_live_execution_profile(*, compliance_profile_id: str \| None, operating_mode: str) -> str` | Attach and validate the active compliance profile for live-capable workflows. |
| `build_compliance_profile_labels(*, export_profile: str, compliance_profile_id: str) -> tuple[str, ...]` | Build stable export labels from the active compliance profile. |


## FEAT-RISK-97: Policy-as-code contract definitions (app.services.risk.policy.contracts)

| Function | Purpose |
|----------|---------|
| `OverrideValidationResult` (TypedDict) | Result of running override validation checks. |
| `RiskOverrideRequest` (class) | Governed request to override config parameters with signed token. |
| `RiskPolicy` (class) | Immutable policy record with thresholds and authority. |
| `EffectiveRiskPolicy` (class) | Resolved policy applied to a request with provenance and precedence evidence. |
| `PolicyPrecedenceRule` (class) | Explicit global/account/strategy/symbol/workflow ordering record. |
| `validate_policy_scope(scope: PolicyScope) -> ValidationResult` | Validates policy scope selectors, rejecting empty/malformed values. |


## FEAT-RISK-98: Policy domain models (app.services.risk.policy.models)

| Function | Purpose |
|----------|---------|
| `PolicyVersion` (model) | Versioned policy reference. |
| `PolicyBundle` (model) | Resolved active policy bundle for an execution scope. |
| `PolicyEnforcementResult` (model) | Deterministic result of applying policy to an action. |


## FEAT-RISK-99: Governed policy override validation logic (app.services.risk.policy.overrides)

| Function | Purpose |
|----------|---------|
| `validate_token_config_compatibility(token: RiskDecisionToken \| RiskApprovalToken, config_hash: str) -> ValidationResult` | Validates configuration compatibility for approval/decision tokens. |
| `requires_override_approval(request: RiskOverrideRequest, policy: EffectiveRiskPolicy) -> bool` | Determines whether override approval is mandatory. |
| `validate_risk_override_request(request: RiskOverrideRequest, policy: EffectiveRiskPolicy) -> OverrideValidationResult` | Validates override scope and maximum threshold bounds against active policy. |


## FEAT-RISK-100: Deterministic risk policy rules (app.services.risk.policy.pre_trade)

| Function | Purpose |
|----------|---------|
| `validate_proposal(proposal: dict[str, Any]) -> list[str]` | Function validate_proposal provides risk service behavior. |
| `evaluate_policy(*, proposal: dict[str, Any], portfolio_snapshot: dict[str, Any], market_snapshot: dict[str, Any], thresholds: dict[str, Any], proposed_trade_risk: float) -> dict[str, Any]` | Function evaluate_policy provides risk service behavior. |
| `approved_volume_for_policy(requested_volume: float, proposed_trade_risk: float, thresholds: dict[str, Any]) -> tuple[str, float]` | Function approved_volume_for_policy provides risk service behavior. |


## FEAT-RISK-101: Policy-as-code resolution and budget validation engine (app.services.risk.policy.resolver)

| Function | Purpose |
|----------|---------|
| `get_rule_specificity_score(scope: PolicyScope) -> int` | Calculate specificity score for policy rules sorting. |
| `resolve_policy(base_config: RiskConfig, rules: list[PolicyRule], context: dict[str, Any]) -> PolicyEnforcementResult` | Resolve the active RiskConfig by matching and merging policy rules. |
| `validate_policy_expiry(policy: RiskPolicy, now_utc: datetime) -> ValidationResult` | Validates time-bounded policies. |
| `resolve_effective_policy(context: dict[str, Any], policies: Sequence[RiskPolicy]) -> EffectiveRiskPolicy` | Applies approved scope/precedence rules to resolve the effective policy. |
| `evaluate_risk_budget(policy: EffectiveRiskPolicy, request: RiskAssessmentRequest) -> PolicyEnforcementResult` | Evaluates policy budget gates against a risk assessment request. |
| `RiskPolicyEngine.resolve(query: PolicyResolutionQuery, base_config: RiskConfig) -> PolicyEnforcementResult` | Resolve policy overrides against base config and matching rules. |
| `resolve_risk_policy(base_config: RiskConfig, rules: list[PolicyRule], context: dict[str, Any]) -> PolicyEnforcementResult` | Resolve config by matching rules against context. |
| `PolicyResolutionQuery` (model) | Requested policy scope. |
| `PolicyResolver.__init__(bundles: tuple[PolicyBundle, ...]) -> None` | Resolve the most specific policy bundle matching a requested scope. |
| `PolicyResolver.resolve(query: PolicyResolutionQuery) -> PolicyBundle \| None` | Resolve the most specific policy bundle matching a requested scope. |


## FEAT-RISK-102: Restriction and compatibility evaluators for deterministic risk checks (app.services.risk.policy.restrictions)

| Function | Purpose |
|----------|---------|
| `RestrictionEvaluation` (model) | Simple allow/deny result with deterministic reason codes. |
| `evaluate_regime_restriction(*, current_regime: str, allowed_regimes: tuple[str, ...]) -> RestrictionEvaluation` | Allow action only when the current regime is explicitly permitted. |
| `evaluate_session_restrictions(*, current_time: datetime, allowed_window: tuple[str, str], blackout_windows: tuple[tuple[str, str], ...] = ()) -> RestrictionEvaluation` | Check session allow window and blackout overlap for the current time. |
| `evaluate_spread_slippage_precheck(*, spread_points: float, max_spread_points: float, expected_slippage_points: float, max_slippage_points: float) -> RestrictionEvaluation` | Block entries when spread or expected slippage exceed configured limits. |
| `evaluate_operating_mode_compatibility(*, workflow_operating_mode: str, allowed_operating_modes: tuple[str, ...]) -> RestrictionEvaluation` | Check whether the current workflow mode is permitted for the action. |
| `evaluate_compliance_profile_compatibility(*, active_compliance_profile_id: str, allowed_compliance_profile_ids: tuple[str, ...]) -> RestrictionEvaluation` | Check whether the active compliance profile is permitted for the action. |


## FEAT-RISK-103: Marginal portfolio contribution helpers (app.services.risk.portfolio.contributions)

| Function | Purpose |
|----------|---------|
| `MarginalRiskContribution` (model) | Normalized marginal contribution for one position bucket. |
| `calculate_marginal_risk_contribution(positions: tuple[PositionExposure, ...]) -> tuple[MarginalRiskContribution, ...]` | Approximate marginal portfolio contribution from gross exposure shares. |


## FEAT-RISK-104: Advisory-only enforcement for portfolio proposals (app.services.risk.portfolio.enforcement)

| Function | Purpose |
|----------|---------|
| `enforce_portfolio_advisory_only(proposal: AdvisoryPortfolioProposal, *, requested_live_execution: bool) -> AdvisoryPortfolioProposal` | Fail closed if a portfolio proposal is used as a live execution action. |


## FEAT-RISK-105: Projected portfolio impact helpers (app.services.risk.portfolio.impacts)

| Function | Purpose |
|----------|---------|
| `ProjectedVarEsImpact` (model) | Projected VaR and expected shortfall after a portfolio change. |
| `calculate_projected_var_es_impact(*, current_var: float, current_expected_shortfall: float, current_gross_exposure: float, target_gross_exposure: float) -> ProjectedVarEsImpact` | Project VaR and ES by scaling with gross exposure change. |
| `calculate_projected_margin_impact(*, balance: float, equity: float, free_margin: float, margin_used: float, projected_margin_delta: float) -> MarginUtilization` | Project margin utilization after an additive margin change. |


## FEAT-RISK-106: Advisory-only portfolio proposal generators (app.services.risk.portfolio.proposals)

| Function | Purpose |
|----------|---------|
| `AdvisoryPortfolioProposal` (model) | Minimal advisory-only portfolio action proposal. |
| `generate_resize_proposal(*, position: PositionExposure, target_notional_exposure: float) -> AdvisoryPortfolioProposal` | Generate an advisory resize proposal for one position. |
| `generate_rebalance_proposal(*, target_allocations: dict[str, float]) -> AdvisoryPortfolioProposal` | Generate an advisory rebalance proposal for target portfolio weights. |
| `generate_hedge_proposal(*, source_position: PositionExposure, hedge_symbols: tuple[str, ...]) -> AdvisoryPortfolioProposal` | Generate an advisory hedge proposal around one source position. |
| `generate_derisk_proposal(*, affected_symbols: tuple[str, ...], target_reduction_ratio: float) -> AdvisoryPortfolioProposal` | Generate an advisory de-risking proposal for one or more symbols. |


## FEAT-RISK-107: Orchestration engine for the Phase 2 core risk metric MVP (app.services.risk.portfolio.snapshot_builder)

| Function | Purpose |
|----------|---------|
| `RiskSnapshotEngine.__init__(registry: MetricRegistry \| None = None) -> None` | Build one current-state normalized risk snapshot from PortfolioState. |
| `RiskSnapshotEngine.build_snapshot(state: PortfolioState, shared: dict[str, Any] \| None = None) -> RiskSnapshot` | Compute all registered metrics and return a normalized snapshot. |


## FEAT-RISK-108: Portfolio snapshot assembly helpers for portfolio analytics (app.services.risk.portfolio.snapshots)

| Function | Purpose |
|----------|---------|
| `PortfolioSnapshotAssemblyInput` (model) | Inputs required to assemble a current portfolio snapshot. |
| `assemble_portfolio_snapshot(request: PortfolioSnapshotAssemblyInput, *, snapshot_id: str) -> PortfolioSnapshot` | Assemble a canonical portfolio snapshot from normalized open positions. |


## FEAT-RISK-109: Canonical portfolio-state builder for the risk subsystem (app.services.risk.portfolio.state_builder)

| Function | Purpose |
|----------|---------|
| `PortfolioStateEngine.build_state_from_engine(engine: Any, symbols: list[str], timeframe: str = 'D1', count: int = 500, start_pos: int = 0, as_of: str \| None = None, bar_index: int \| None = None, positions: Any = None, account: Any = None, limits: RiskLimits \| None = None, symbol_to_cluster: dict[str, str] \| None = None, symbol_to_clusters: dict[str, list[str]] \| None = None, metadata: dict[str, Any] \| None = None) -> PortfolioState` | Build a validated portfolio state directly from the existing engine stack. |
| `PortfolioStateEngine.build_state(account: Any, positions: Any, symbol_specs: dict[str, Any] \| None = None, market_data: dict[str, pd.DataFrame] \| None = None, limits: RiskLimits \| None = None, symbol_to_cluster: dict[str, str] \| None = None, symbol_to_clusters: dict[str, list[str]] \| None = None, timeframe: str = 'D1', as_of: str \| None = None, metadata: dict[str, Any] \| None = None) -> PortfolioState` | Build a validated canonical portfolio state. |


## FEAT-RISK-110: Portfolio analytics tool functions for the risk service (app.services.risk.portfolio_tools)

| Function | Purpose |
|----------|---------|
| `get_open_positions(*, positions: list[dict[str, Any]] \| None = None, request_id: str \| None = None, agent_name: str \| None = None, environment: str = 'development', dry_run: bool = True) -> dict[str, Any]` | Return current open positions supplied by the caller. |
| `get_open_orders(*, orders: list[dict[str, Any]] \| None = None, request_id: str \| None = None, agent_name: str \| None = None, environment: str = 'development', dry_run: bool = True) -> dict[str, Any]` | Return current open orders supplied by the caller. |
| `get_strategy_allocations(*, allocations: dict[str, float] \| None = None, request_id: str \| None = None, agent_name: str \| None = None, environment: str = 'development', dry_run: bool = True) -> dict[str, Any]` | Return current strategy capital allocations. |
| `get_portfolio_equity_curve(*, equity_curve: list[float] \| None = None, request_id: str \| None = None, agent_name: str \| None = None, environment: str = 'development', dry_run: bool = True) -> dict[str, Any]` | Return a supplied portfolio equity curve. |
| `calculate_portfolio_volatility(*, returns: list[float], request_id: str \| None = None, agent_name: str \| None = None, environment: str = 'development', dry_run: bool = True) -> dict[str, Any]` | Calculate sample volatility from portfolio returns. |
| `calculate_portfolio_correlation(*, returns_by_asset: dict[str, list[float]], request_id: str \| None = None, agent_name: str \| None = None, environment: str = 'development', dry_run: bool = True) -> dict[str, Any]` | Calculate a correlation matrix from asset returns. |
| `calculate_portfolio_var(*, returns: list[float], alpha: float = 0.05, request_id: str \| None = None, agent_name: str \| None = None, environment: str = 'development', dry_run: bool = True) -> dict[str, Any]` | Calculate historical portfolio value-at-risk. |
| `calculate_portfolio_cvar(*, returns: list[float], alpha: float = 0.05, request_id: str \| None = None, agent_name: str \| None = None, environment: str = 'development', dry_run: bool = True) -> dict[str, Any]` | Calculate historical portfolio conditional value-at-risk. |
| `calculate_margin_usage(*, equity: float, used_margin: float, request_id: str \| None = None, agent_name: str \| None = None, environment: str = 'development', dry_run: bool = True) -> dict[str, Any]` | Calculate portfolio used-margin fraction. |
| `detect_strategy_overlap(*, strategy_symbols: dict[str, list[str]], request_id: str \| None = None, agent_name: str \| None = None, environment: str = 'development', dry_run: bool = True) -> dict[str, Any]` | Detect symbols traded by more than one strategy. |
| `detect_symbol_cluster_risk(*, symbol_exposures: dict[str, float], cluster_limit: float = 0.5, request_id: str \| None = None, agent_name: str \| None = None, environment: str = 'development', dry_run: bool = True) -> dict[str, Any]` | Detect symbols whose exposure exceeds a concentration threshold. |
| `build_portfolio_risk_snapshot(*, positions: list[dict[str, Any]] \| None = None, equity_curve: list[float] \| None = None, allocations: dict[str, float] \| None = None, request_id: str \| None = None, agent_name: str \| None = None, environment: str = 'development', dry_run: bool = True) -> dict[str, Any]` | Build a compact portfolio risk snapshot from supplied state. |


## FEAT-RISK-111: Phase 5 entry and delivery readiness validation (app.services.risk.readiness.readiness)

| Function | Purpose |
|----------|---------|
| `DependencyStatus` (class) | Tracking structure for a required software dependency. |
| `ReadinessAssessment` (class) | The outcome of validating all dependency contracts. |
| `RiskModeMatrix.validate_mode_coverage() -> RiskModeMatrix` | Verify that all required safety/operational modes are present. |
| `ReadinessDeliveryPlan` (class) | Delivery plan validation requirements. |
| `DryRunReport` (class) | Report outlining planned workspace edits and boundaries. |
| `RiskReadinessManifest.validate_readiness_manifest() -> RiskReadinessManifest` | Validate all subsystems inside the manifest on construction. |
| `validate_phase_dependencies(dependencies: Mapping[str, DependencyStatus]) -> ReadinessAssessment` | Validate that all target dependencies are implemented and covered. |
| `validate_risk_mode_matrix(matrix: RiskModeMatrix) -> ValidationResult` | Validate that the risk mode matrix is valid and complete. |
| `validate_delivery_plan(plan: ReadinessDeliveryPlan) -> ValidationResult` | Validate structural constraints of the delivery plan. |
| `build_readiness_dry_run(manifest: RiskReadinessManifest) -> DryRunReport` | Build a dry run report based on the readiness manifest content. |


## FEAT-RISK-112: Market regime assessment engine (app.services.risk.regime.assessor)

| Function | Purpose |
|----------|---------|
| `RiskRegime` (enum) | Overall synthesized market regime classification. |
| `SpreadRegime` (enum) | Spread widening classification. |
| `VolatilityRegime` (enum) | Volatility classification. |
| `LiquidityRegime` (enum) | Liquidity classification based on quotes/ticks. |
| `NewsRegime` (enum) | News impact/blackout classification. |
| `SessionRegime` (enum) | Market session status classification. |
| `RolloverRegime` (enum) | Broker rollover blackout status classification. |
| `SpreadSigmaThresholds` (class) | Thresholds for spread z-score classification. |
| `VolatilityThresholds` (class) | Multipliers for volatility ratio classification. |
| `RegimeAssessment` (class) | Contract representing the outcome of a market regime assessment. |
| `classify_spread_regime(spread: Decimal, sigma: Decimal, thresholds: SpreadSigmaThresholds, mean: Decimal = Decimal(0)) -> SpreadRegime` | Classifies spread-to-volatility condition based on z-score. |
| `classify_volatility_regime(short_sigma: Decimal, medium_sigma: Decimal, long_sigma: Decimal, thresholds: VolatilityThresholds) -> VolatilityRegime` | Classifies volatility state based on rolling sigma metrics. |
| `is_rollover_blackout(server_time: datetime, policy: EffectiveRiskPolicy, market_context: dict[str, Any] \| None = None) -> bool` | Evaluates broker-midnight rollover blackout boundaries from UTC configuration. |
| `validate_market_freshness(market: MarketRiskSnapshot, _policy: EffectiveRiskPolicy, now_utc: datetime, market_context: dict[str, Any] \| None = None) -> ValidationResult` | Detects stale or inconsistent market evidence. |
| `RegimeRiskEngine.assess(market_snapshot: MarketRiskSnapshot, calendar_evidence: list[dict[str, Any]], market_context: dict[str, Any], now_utc: datetime \| None = None) -> RegimeAssessment` | Assess all market regime components and determine decision status. |
| `assess_risk_regime(*args: Any, market: MarketRiskSnapshot \| None = None, policy: EffectiveRiskPolicy \| None = None, now_utc: datetime \| None = None, market_snapshot: MarketRiskSnapshot \| None = None, calendar_evidence: list[dict[str, Any]] \| None = None, risk_config: RiskConfig \| None = None, market_context: dict[str, Any] \| None = None) -> RegimeAssessment` | Assess market regime details through public stateless helper. |


## FEAT-RISK-113: Regime evidence validation, reason-code composition, and input rejection (app.services.risk.regime.validation)

| Function | Purpose |
|----------|---------|
| `validate_regime_inputs(market: MarketRiskSnapshot) -> ValidationResult` | Validate input MarketRiskSnapshot values for correctness. |
| `build_regime_reason_codes(assessment: RegimeAssessment) -> tuple[RiskReasonCode, ...]` | Produces stable warning/block reason ordering based on assessment. |


## FEAT-RISK-114: Crisis/stress regime detection built from the legacy detector logic (app.services.risk.regimes.crisis_regime)

| Function | Purpose |
|----------|---------|
| `CrisisRegimeDetector.__init__(vol_spike_mult: float = 1.8, corr_spike_level: float = 0.55, dd_trigger_frac: float = 0.05, lookback: int = 60, vol_med_window: int = 20) -> None` | Detect NORMAL vs STRESS using robust portfolio stress signals. |
| `CrisisRegimeDetector.detect(returns_df: pd.DataFrame, equity_curve: pd.Series \| None = None) -> RegimeState` | Return the crisis regime only. |
| `CrisisRegimeDetector.detect_with_signals(returns_df: pd.DataFrame, equity_curve: pd.Series \| None = None) -> tuple[RegimeState, list[RegimeSignal]]` | Return crisis regime and the underlying explainable signals. |


## FEAT-RISK-115: Canonical regime engine for portfolio risk state (app.services.risk.regimes.engine)

| Function | Purpose |
|----------|---------|
| `RegimeEngine.__init__(crisis_detector: CrisisRegimeDetector \| None = None, market_detector: MarketRegimeDetector \| None = None, volatility_detector: VolatilityRegimeDetector \| None = None, liquidity_detector: LiquidityRegimeDetector \| None = None) -> None` | Aggregate market, volatility, liquidity, and crisis regime state. |
| `RegimeEngine.evaluate_state(state: PortfolioState, previous: RegimeState \| None = None, equity_curve: pd.Series \| None = None) -> RegimeReport` | Build one aggregate regime report from canonical portfolio state. |
| `RiskRegimeDetector` (model) | Compatibility detector that preserves the legacy detect() interface. |


## FEAT-RISK-116: Liquidity regime classification for portfolio risk state (app.services.risk.regimes.liquidity_regime)

| Function | Purpose |
|----------|---------|
| `LiquidityRegimeDetector.__init__(stressed_spread_bps: float = 12.0, wide_spread_bps: float = 5.0) -> None` | Classify liquidity regime from spread burden proxies in market slices. |
| `LiquidityRegimeDetector.detect(state: PortfolioState) -> RegimeState` | Classify liquidity regime from spread burden proxies in market slices. |


## FEAT-RISK-117: Market regime classification for portfolio-level risk state (app.services.risk.regimes.market_regime)

| Function | Purpose |
|----------|---------|
| `MarketRegimeDetector.__init__(lookback: int = 60, corr_fragile_level: float = 0.55) -> None` | Classify market fragility from broad portfolio return behavior. |
| `MarketRegimeDetector.detect(returns_df: pd.DataFrame) -> RegimeState` | Classify market fragility from broad portfolio return behavior. |


## FEAT-RISK-118: Normalized regime models for portfolio risk state (app.services.risk.regimes.models)

| Function | Purpose |
|----------|---------|
| `RegimeSignal` (model) | One explainable regime signal observation. |
| `RegimeState.is_stress -> bool` | Normalized regime state used across risk analytics and governance. |
| `RegimeTransition` (model) | Simple transition metadata between two regime states. |
| `RegimeReport` (model) | Aggregate regime report produced by the regime engine. |


## FEAT-RISK-119: Transition helpers for regime state changes (app.services.risk.regimes.regime_transition)

| Function | Purpose |
|----------|---------|
| `build_regime_transition(previous: RegimeState \| None, current: RegimeState) -> RegimeTransition` | Build simple transition metadata from previous to current regime. |


## FEAT-RISK-120: Volatility regime classification for portfolio risk state (app.services.risk.regimes.volatility_regime)

| Function | Purpose |
|----------|---------|
| `VolatilityRegimeDetector.__init__(lookback: int = 60, high_vol_mult: float = 1.35, low_vol_mult: float = 0.75) -> None` | Classify realized volatility state from returns history. |
| `VolatilityRegimeDetector.detect(returns_df: pd.DataFrame) -> RegimeState` | Classify realized volatility state from returns history. |


## FEAT-RISK-121: Simple deterministic replay clock for Python-side simulator playback (app.services.risk.replay.clock)

| Function | Purpose |
|----------|---------|
| `ReplayClock.from_timeline(timeline: Iterable[object]) -> ReplayClock` | Deterministic replay cursor over pre-built timeline points. |
| `ReplayClock.finished -> bool` | Deterministic replay cursor over pre-built timeline points. |
| `ReplayClock.current -> object \| None` | Deterministic replay cursor over pre-built timeline points. |
| `ReplayClock.reset() -> None` | Deterministic replay cursor over pre-built timeline points. |
| `ReplayClock.advance() -> object \| None` | Deterministic replay cursor over pre-built timeline points. |
| `ReplayClock.step(count: int = 1) -> object \| None` | Deterministic replay cursor over pre-built timeline points. |


## FEAT-RISK-122: UI-ready replay cockpit payloads (app.services.risk.replay.cockpit_state)

| Function | Purpose |
|----------|---------|
| `CockpitStatePayload` (model) | Compact payload for simulator cockpit rendering. |
| `build_cockpit_state(frame: ReplayFrame, what_if: WhatIfComparison \| None = None, max_recommendations: int = 3) -> CockpitStatePayload` | Build a compact replay cockpit payload from one replay frame. |


## FEAT-RISK-123: Hypothetical action helpers for replay what-if analysis (app.services.risk.replay.hypothetical_orders)

| Function | Purpose |
|----------|---------|
| `HypotheticalOrderAction` (model) | One replay-time hypothetical portfolio action. |
| `resolve_delta(state: PortfolioState, action: HypotheticalOrderAction) -> float` | Resolve the signed lot delta for a hypothetical action. |
| `apply_hypothetical_actions(state: PortfolioState, actions: Iterable[HypotheticalOrderAction]) -> PortfolioState` | Apply hypothetical actions to a cloned canonical state. |
| `ensure_actions(actions: Iterable[HypotheticalOrderAction]) -> list[HypotheticalOrderAction]` | Function ensure_actions provides risk service behavior. |


## FEAT-RISK-124: Replay contracts for simulator-backed risk playback (app.services.risk.replay.models)

| Function | Purpose |
|----------|---------|
| `ReplayFrame` (model) | One replay frame with normalized risk outputs. |
| `ReplayRun` (model) | Whole replay output for one simulator-backed run. |
| `WhatIfComparison` (model) | Before/after comparison for one replay-frame hypothetical action set. |


## FEAT-RISK-125: Simulator-backed replay orchestration for risk frames (app.services.risk.replay.replay_engine)

| Function | Purpose |
|----------|---------|
| `ReplayEngine.__init__(portfolio_state_engine: PortfolioStateEngine \| None = None, snapshot_engine: RiskSnapshotEngine \| None = None, scorecard_engine: RiskScorecardEngine \| None = None, recommendation_engine: RecommendationEngine \| None = None, timeline_reconstructor: TimelineReconstructor \| None = None) -> None` | Replay simulator timelines into deterministic risk frames. |
| `ReplayEngine.replay(engine: Any, data: pd.DataFrame, symbols: list[str], timeframe: str, market_data: dict[str, pd.DataFrame], limits=None, symbol_to_cluster: dict[str, str] \| None = None, metadata: dict[str, Any] \| None = None, frame_mode: str = 'bar', include_recommendations: bool = True, candidate_symbols: Iterable[str] \| None = None, hedge_symbols: Iterable[str] \| None = None, max_recommendations: int = 5, max_frames: int \| None = None, run_kwargs: dict[str, Any] \| None = None) -> ReplayRun` | Run the simulator and capture deterministic replay frames. |


## FEAT-RISK-126: Timeline reconstruction helpers for replay-backed risk workflows (app.services.risk.replay.timeline)

| Function | Purpose |
|----------|---------|
| `TimelinePoint` (model) | One replay capture point. |
| `TimelineReconstructor.build_timeline(data: pd.DataFrame, frame_mode: str = 'bar') -> list[TimelinePoint]` | Build deterministic replay capture plans from merged market timelines. |
| `TimelineReconstructor.timeline_signature(timeline: list[TimelinePoint], frame_mode: str = 'bar') -> str` | Build deterministic replay capture plans from merged market timelines. |


## FEAT-RISK-127: Replay what-if analysis built on canonical state and current risk engines (app.services.risk.replay.what_if_engine)

| Function | Purpose |
|----------|---------|
| `WhatIfEngine.__init__(snapshot_engine: RiskSnapshotEngine \| None = None, scorecard_engine: RiskScorecardEngine \| None = None, recommendation_engine: RecommendationEngine \| None = None) -> None` | Evaluate hypothetical actions on top of one replay frame. |
| `WhatIfEngine.evaluate(frame: ReplayFrame, actions: Iterable[HypotheticalOrderAction], include_recommendations: bool = True, candidate_symbols=None, hedge_symbols=None, max_recommendations: int = 5, snapshot_shared: dict[str, Any] \| None = None) -> WhatIfComparison` | Build a before/after comparison for one replay-frame hypothetical. |


## FEAT-RISK-128: Risk report builder module (app.services.risk.reports.builder)

| Function | Purpose |
|----------|---------|
| `PortfolioRiskReport` (class) | Consolidated portfolio-level risk metrics. |
| `RiskDecisionSummary` (class) | Summary of a single pre-trade risk decision. |
| `RiskReport.to_json() -> str` | Serialize and redact sensitive fields, returning a JSON string. |
| `build_risk_decision_summary(decision: RiskDecisionPackage) -> RiskDecisionSummary` | Build a summary from a RiskDecisionPackage. |
| `RiskReportEvidence` (class) | Durable evidence object for compiling reports. |
| `ReportRedactionPolicy` (class) | Redaction configuration for report compilation. |
| `RiskReportOptions` (class) | Configuration options for report generation. |
| `RiskReportBuilder.build(options: RiskReportOptions) -> RiskReport` | Build and populate the RiskReport. |
| `generate_risk_report(evidence: Any = None, options: Any = None, *, state_store: Any = None, audit_sink: Any = None, decision_store: Any = None, request_id: str \| None = None, write_to_path: str \| None = None) -> RiskReport` | Generate a risk report from stored evidence or store facades. |
| `redact_risk_report(report: RiskReport, policy: ReportRedactionPolicy \| None = None) -> RiskReport` | Remove sensitive fields from the report. |


## FEAT-RISK-129: Risk report exporter module (app.services.risk.reports.exporter)

| Function | Purpose |
|----------|---------|
| `AuthorizedReportPath` (class) | Authorized destination path schema for report writes. |
| `ReportWriteReceipt` (class) | receipt containing structural verification details of a file write. |
| `validate_report_export_destination(destination: AuthorizedReportPath) -> ValidationResult` | Validate report destination path against traversal and overwrites. |
| `build_report_write_receipt(report: RiskReport, destination: AuthorizedReportPath, checksum: str) -> ReportWriteReceipt` | Create deterministic export receipt. |
| `write_risk_report(report: RiskReport, destination: AuthorizedReportPath) -> ReportWriteReceipt` | Write the report safely to the destination and return a receipt. |


## FEAT-RISK-130: File export helpers for risk reports (app.services.risk.reports.json_export)

| Function | Purpose |
|----------|---------|
| `save_json_report(content: dict[str, Any], path: str \| Path) -> Path` | Function save_json_report provides risk service behavior. |
| `save_markdown_report(content: str, path: str \| Path) -> Path` | Function save_markdown_report provides risk service behavior. |


## FEAT-RISK-131: Markdown rendering for risk reports (app.services.risk.reports.markdown_report)

| Function | Purpose |
|----------|---------|
| `render_risk_report_markdown(report: dict[str, Any]) -> str` | Function render_risk_report_markdown provides risk service behavior. |
| `render_scenario_report_markdown(report: dict[str, Any]) -> str` | Function render_scenario_report_markdown provides risk service behavior. |
| `render_replay_report_markdown(report: dict[str, Any]) -> str` | Function render_replay_report_markdown provides risk service behavior. |


## FEAT-RISK-132: Replay and what-if report builder (app.services.risk.reports.replay_report_builder)

| Function | Purpose |
|----------|---------|
| `build_replay_report(replay_frames: list[dict[str, Any]], *, run: dict[str, Any] \| None = None) -> dict[str, Any]` | Build a compact report from stored replay frames. |


## FEAT-RISK-133: Public risk report builder facade (app.services.risk.reports.risk_report)

| Function | Purpose |
|----------|---------|
| `RiskReportBuilder.build_current_report(state: dict[str, Any]) -> dict[str, Any]` | Build machine-readable risk reports from current snapshot bundles. |


## FEAT-RISK-134: Machine-readable risk snapshot report builder (app.services.risk.reports.risk_report_builder)

| Function | Purpose |
|----------|---------|
| `build_risk_snapshot_report(snapshot_bundle: dict[str, Any], *, run: dict[str, Any] \| None = None) -> dict[str, Any]` | Build one machine-readable report from a stored snapshot bundle. |


## FEAT-RISK-135: Scenario and stress report builder (app.services.risk.reports.scenario_report_builder)

| Function | Purpose |
|----------|---------|
| `build_scenario_report(snapshot_bundle: dict[str, Any], *, run: dict[str, Any] \| None = None) -> dict[str, Any]` | Build a focused stored-scenario report from one snapshot bundle. |


## FEAT-RISK-136: Shared formatting and summary helpers for risk reports (app.services.risk.reports.summary_templates)

| Function | Purpose |
|----------|---------|
| `fmt_value(value: Any, digits: int = 2) -> str` | Format one value for markdown display. |
| `top_metric_rows(rows: Iterable[dict[str, Any]]) -> list[dict[str, Any]]` | Return the most report-relevant portfolio-level metric rows. |
| `top_score_rows(rows: Iterable[dict[str, Any]]) -> list[dict[str, Any]]` | Return the score rows ordered as a compact report section. |
| `top_recommendations(rows: Iterable[dict[str, Any]], limit: int = 5) -> list[dict[str, Any]]` | Return the top stored recommendations ordered by usefulness. |
| `top_scenarios(rows: Iterable[dict[str, Any]], limit: int = 5) -> list[dict[str, Any]]` | Return the worst stored scenarios by loss. |


## FEAT-RISK-137: Deterministic scenario evaluation on top of canonical portfolio state (app.services.risk.scenarios.core)

| Function | Purpose |
|----------|---------|
| `evaluate_scenarios(state: PortfolioState, registry: ScenarioRegistry \| None = None) -> list[ScenarioResult]` | Evaluate the registered deterministic stress scenarios. |


## FEAT-RISK-138: Scenario contracts for risk stress analytics (app.services.risk.scenarios.models)

| Function | Purpose |
|----------|---------|
| `ScenarioResult` (model) | One evaluated scenario result. |


## FEAT-RISK-139: Base contracts for normalized risk scorecards (app.services.risk.scoring.base)

| Function | Purpose |
|----------|---------|
| `ScoreRow` (model) | One normalized score row suitable for later persistence. |
| `ScoreContext` (model) | Execution context for one scorecard run. |
| `ScoreFamily.compute(context: ScoreContext) -> list[ScoreRow]` | Compute normalized score rows for this family. |
| `RiskScorecard` (model) | Scorecard built from a normalized risk snapshot. |


## FEAT-RISK-140: Concentration score (app.services.risk.scoring.concentration_score)

| Function | Purpose |
|----------|---------|
| `ConcentrationScore.compute(context: ScoreContext) -> list[ScoreRow]` | Class ConcentrationScore provides risk service behavior. |


## FEAT-RISK-141: Diversification score (app.services.risk.scoring.diversification_score)

| Function | Purpose |
|----------|---------|
| `DiversificationScore.compute(context: ScoreContext) -> list[ScoreRow]` | Class DiversificationScore provides risk service behavior. |


## FEAT-RISK-142: Governance compliance score (app.services.risk.scoring.governance_compliance)

| Function | Purpose |
|----------|---------|
| `GovernanceComplianceScore.compute(context: ScoreContext) -> list[ScoreRow]` | Class GovernanceComplianceScore provides risk service behavior. |


## FEAT-RISK-143: Leverage safety score (app.services.risk.scoring.leverage_safety)

| Function | Purpose |
|----------|---------|
| `LeverageSafetyScore.compute(context: ScoreContext) -> list[ScoreRow]` | Class LeverageSafetyScore provides risk service behavior. |


## FEAT-RISK-144: Margin safety score (app.services.risk.scoring.margin_safety)

| Function | Purpose |
|----------|---------|
| `MarginSafetyScore.compute(context: ScoreContext) -> list[ScoreRow]` | Class MarginSafetyScore provides risk service behavior. |


## FEAT-RISK-145: Shared normalization helpers for explainable risk scores (app.services.risk.scoring.normalization)

| Function | Purpose |
|----------|---------|
| `clamp_score(value: float) -> float` | Function clamp_score provides risk service behavior. |
| `inverse_ratio_score(value: float \| None, good: float, bad: float) -> float` | Map a risk ratio into a 0-100 score where lower is better. |
| `direct_ratio_score(value: float \| None, bad: float, good: float) -> float` | Map a helpful ratio into a 0-100 score where higher is better. |
| `confidence_from_inputs(count: int) -> float` | Function confidence_from_inputs provides risk service behavior. |
| `confidence_label(confidence: float) -> str` | Function confidence_label provides risk service behavior. |


## FEAT-RISK-146: Overall risk quality score (app.services.risk.scoring.overall_risk_quality)

| Function | Purpose |
|----------|---------|
| `OverallRiskQualityScore.compute(context: ScoreContext) -> list[ScoreRow]` | Class OverallRiskQualityScore provides risk service behavior. |


## FEAT-RISK-147: Portfolio health score (app.services.risk.scoring.portfolio_health)

| Function | Purpose |
|----------|---------|
| `PortfolioHealthScore.compute(context: ScoreContext) -> list[ScoreRow]` | Class PortfolioHealthScore provides risk service behavior. |


## FEAT-RISK-148: Regime alignment score (app.services.risk.scoring.regime_alignment)

| Function | Purpose |
|----------|---------|
| `RegimeAlignmentScore.compute(context: ScoreContext) -> list[ScoreRow]` | Class RegimeAlignmentScore provides risk service behavior. |


## FEAT-RISK-149: Scorecard engine built on normalized risk snapshots (app.services.risk.scoring.scorecard_engine)

| Function | Purpose |
|----------|---------|
| `RiskScorecardEngine.__init__(registry: ScoreRegistry \| None = None) -> None` | Build an explainable scorecard from a normalized risk snapshot. |
| `RiskScorecardEngine.build_scorecard(snapshot: RiskSnapshot, shared: dict[str, Any] \| None = None) -> RiskScorecard` | Build an explainable scorecard from a normalized risk snapshot. |


## FEAT-RISK-150: Stress fragility / resilience score (app.services.risk.scoring.stress_fragility)

| Function | Purpose |
|----------|---------|
| `StressFragilityScore.compute(context: ScoreContext) -> list[ScoreRow]` | Class StressFragilityScore provides risk service behavior. |


## FEAT-RISK-151: Position sizing calculator engines (app.services.risk.sizing.calculators)

| Function | Purpose |
|----------|---------|
| `calculate_stop_distance(request: PositionSizingRequest, symbol_metadata: SymbolRiskMetadata, market_context: dict[str, Any] \| None = None) -> Decimal` | Calculate price stop distance using request attributes or volatility checks. |
| `convert_stop_distance_to_account_risk(distance: Decimal, symbol: SymbolRiskMetadata, account_currency: str) -> Decimal` | Convert price stop distance into account-currency risk per lot. |
| `calculate_fixed_risk_size(request: PositionSizingRequest, portfolio_equity: Decimal, symbol_metadata: SymbolRiskMetadata, config: RiskConfig, drawdown_step_down_multiplier: Decimal = Decimal("1.0"), currency_exposure_reduction: Decimal = Decimal("1.0"), correlation_cluster_reduction: Decimal = Decimal("1.0"), market_context: dict[str, Any] \| None = None) -> PositionSizingResult` | Pure calculator sizing position from fixed monetary bounds. |
| `calculate_fixed_fractional_size(request: PositionSizingRequest, portfolio_equity: Decimal, symbol_metadata: SymbolRiskMetadata, config: RiskConfig, drawdown_step_down_multiplier: Decimal = Decimal("1.0"), currency_exposure_reduction: Decimal = Decimal("1.0"), correlation_cluster_reduction: Decimal = Decimal("1.0"), market_context: dict[str, Any] \| None = None) -> PositionSizingResult` | Pure calculator sizing position from fixed fractional equity. |
| `calculate_volatility_adjusted_size(request: PositionSizingRequest, portfolio_equity: Decimal, symbol_metadata: SymbolRiskMetadata, config: RiskConfig, drawdown_step_down_multiplier: Decimal = Decimal("1.0"), currency_exposure_reduction: Decimal = Decimal("1.0"), correlation_cluster_reduction: Decimal = Decimal("1.0"), market_context: dict[str, Any] \| None = None) -> PositionSizingResult` | Pure calculator sizing position from volatility stops. |
| `calculate_correlation_adjusted_size(request: PositionSizingRequest, portfolio_equity: Decimal, symbol_metadata: SymbolRiskMetadata, config: RiskConfig, correlation: CorrelationImpact, drawdown_step_down_multiplier: Decimal = Decimal("1.0"), currency_exposure_reduction: Decimal = Decimal("1.0"), correlation_cluster_reduction: Decimal = Decimal("1.0"), market_context: dict[str, Any] \| None = None) -> PositionSizingResult` | Pure calculator sizing position with correlation scaling. |
| `calculate_milestone_size(request: PositionSizingRequest, portfolio_equity: Decimal, symbol_metadata: SymbolRiskMetadata, config: RiskConfig, milestones: Sequence[RiskMilestone], drawdown_step_down_multiplier: Decimal = Decimal("1.0"), currency_exposure_reduction: Decimal = Decimal("1.0"), correlation_cluster_reduction: Decimal = Decimal("1.0"), market_context: dict[str, Any] \| None = None) -> PositionSizingResult` | Pure calculator sizing position with milestone scaling. |
| `calculate_kelly_reference_size(request: PositionSizingRequest, portfolio_equity: Decimal, symbol_metadata: SymbolRiskMetadata, config: RiskConfig, evidence: KellyEvidence, market_context: dict[str, Any] \| None = None) -> AdvisorySizingResult` | Pure calculator sizing position from statistical Kelly fractions. |
| `calculate_position_size(request: PositionSizingRequest, portfolio_state: PortfolioState, market_context: dict[str, Any], config: RiskConfig) -> PositionSizingResult` | Position sizing gateway routing requests to pure stateless calculators. |
| `VolatilitySizingEngine.calculate_position_size(request: PositionSizingRequest, portfolio_state: PortfolioState, market_context: dict[str, Any]) -> PositionSizingResult` | Calculate position sizing using active configuration. |
| `calculate_risk_parity_weights(*, volatilities: dict[str, float], request_id: str \| None = None, agent_name: str \| None = None, environment: str = 'development', dry_run: bool = True) -> dict[str, Any]` | Calculate inverse-volatility risk parity weights. |
| `calculate_margin_aware_size(*, desired_size: float, free_margin: float, margin_per_unit: float, request_id: str \| None = None, agent_name: str \| None = None, environment: str = 'development', dry_run: bool = True) -> dict[str, Any]` | Cap desired size by available free margin. |
| `calculate_cost_adjusted_size(*, desired_size: float, transaction_cost_fraction: float, max_cost_fraction: float = 0.02, request_id: str \| None = None, agent_name: str \| None = None, environment: str = 'development', dry_run: bool = True) -> dict[str, Any]` | Reduce desired size when transaction cost exceeds policy tolerance. |
| `calculate_max_safe_position_size(*, candidate_sizes: dict[str, float], request_id: str \| None = None, agent_name: str \| None = None, environment: str = 'development', dry_run: bool = True) -> dict[str, Any]` | Return the most restrictive non-negative position size. |
| `propose_strategy_allocation(*, scores: dict[str, float], max_weight: float = 0.4, request_id: str \| None = None, agent_name: str \| None = None, environment: str = 'development', dry_run: bool = True) -> dict[str, Any]` | Build a normalized strategy allocation proposal from scores. |
| `rebalance_strategy_allocations(*, target_allocations: dict[str, float], request_id: str \| None = None, agent_name: str \| None = None, environment: str = 'development', dry_run: bool = True) -> dict[str, Any]` | Normalize target strategy allocations for a rebalance proposal. |
| `validate_allocation_proposal(*, allocations: dict[str, float], max_weight: float = 0.4, tolerance: float = 1e-06, request_id: str \| None = None, agent_name: str \| None = None, environment: str = 'development', dry_run: bool = True) -> dict[str, Any]` | Validate allocation weights against sum and max-weight policy. |


## FEAT-RISK-152: Sizing request/result contracts and sizing method enum (app.services.risk.sizing.contracts)

| Function | Purpose |
|----------|---------|
| `SizingMethod` (enum) | Supported position sizing methods. |
| `SymbolRiskMetadata` (class) | Symbol specifications needed for volume and precision normalizations. |
| `CorrelationImpact` (class) | Correlation data for portfolio sizing adjustment. |
| `RiskMilestone` (class) | Milestone constraint mapping a multiplier. |
| `KellyEvidence` (class) | Trade performance metrics for Kelly sizing. |
| `AdvisorySizingResult` (class) | Kelly advisory-only sizing outcome. |


## FEAT-RISK-153: Broker volume normalization and precision validations (app.services.risk.sizing.normalization)

| Function | Purpose |
|----------|---------|
| `validate_symbol_volume_metadata(symbol: SymbolRiskMetadata) -> ValidationResult` | Validate symbol specification parameters before volume checks. |
| `normalize_volume(size: Decimal, symbol: SymbolRiskMetadata) -> Decimal` | Floor size to broker lot-step increments. |
| `validate_normalized_volume(size: Decimal, symbol: SymbolRiskMetadata) -> ValidationResult` | Check if normalized volume satisfies broker constraints. |
| `build_volume_rejection(size: Decimal, symbol: SymbolRiskMetadata, reason: RiskReasonCode) -> PositionSizingResult` | Return rejection result with zero volume and constraints list. |


## FEAT-RISK-154: Persistence helpers for canonical risk decisions (app.services.risk.storage.decision_store)

| Function | Purpose |
|----------|---------|
| `RiskDecisionPersistenceService.__init__(db_path: str \| Path) -> None` | Persist canonical risk decisions and machine-enforceable constraints. |
| `RiskDecisionPersistenceService.save(*, risk_request_id: str, packed: PackedRiskDecisionArtifacts)` | Persist the main decision row and any attached constraints. |


## FEAT-RISK-155: Thread-safe in-memory risk governance store (app.services.risk.storage.in_memory)

| Function | Purpose |
|----------|---------|
| `StorageOperation` (enum) | Types of storage operations that can be performed. |
| `FailingStore.set_simulate_failure(enabled: bool) -> None` | Enable or disable simulated storage failures. |
| `InMemoryRiskStateStore.set_simulate_failure(enabled: bool) -> None` | Enable or disable simulated persistence failures for testing. |
| `InMemoryRiskStateStore.get_drawdown_state(strategy_id: str \| None = None) -> DrawdownState \| None` | Retrieve drawdown state from memory. |
| `InMemoryRiskStateStore.save_drawdown_state(state: DrawdownState, strategy_id: str \| None = None) -> None` | Save drawdown state to memory. |
| `InMemoryRiskStateStore.get_kill_switch_state(scope: str, target: str) -> tuple[KillSwitchStateEnum, KillSwitchReason \| None, datetime \| None, str \| None]` | Retrieve kill switch state from memory. |
| `InMemoryRiskStateStore.save_kill_switch_state(scope: str, target: str, state: KillSwitchStateEnum, reason: KillSwitchReason \| None = None, triggered_at: datetime \| None = None, triggered_by: str \| None = None) -> None` | Save kill switch state updates to memory. |
| `InMemoryRiskStateStore.is_token_revoked(token_id: str) -> bool` | Check token revocation in memory. |
| `InMemoryRiskStateStore.revoke_token(token_id: str) -> None` | Revoke a token in memory. |
| `InMemoryRiskStateStore.write_event(event: RiskAuditEvent) -> None` | Write audit event block to memory. |
| `InMemoryRiskStateStore.get_last_event() -> RiskAuditEvent \| None` | Retrieve the latest block in memory. |
| `InMemoryRiskStateStore.get_all_events() -> list[RiskAuditEvent]` | Retrieve all events. |
| `InMemoryRiskStateStore.get_rules() -> list[PolicyRule]` | Retrieve active policy rules. |
| `InMemoryRiskStateStore.save_rule(rule: PolicyRule) -> None` | Store policy rule in memory. |
| `InMemoryRiskStateStore.get_decision(decision_id: str) -> RiskDecisionPackage \| None` | Retrieve decision by ID. |
| `InMemoryRiskStateStore.save_decision(decision: RiskDecisionPackage) -> None` | Persist decision in memory with idempotency handling. |
| `InMemoryRiskStateStore.get_decision_by_request_id(request_id: str) -> RiskDecisionPackage \| None` | Retrieve decision by request ID. |
| `InMemoryRiskStateStore.list_decisions() -> list[RiskDecisionPackage]` | List all stored decisions. |
| `InMemoryRiskStateStore.get_decision_by_key(request_id: str, workflow_id: str, signal_id: str, decision_material_hash: str) -> RiskDecisionPackage \| None` | Retrieve decision by idempotency keys. |
| `create_in_memory_risk_store() -> InMemoryRiskStateStore` | Create an isolated InMemoryRiskStateStore instance. |
| `simulate_storage_failure(store: FailingStore, operation: StorageOperation) -> PersistenceResult` | Inject a failure state into the failing storage provider. |


## FEAT-RISK-156: Risk governance storage ports and contract definitions (app.services.risk.storage.ports)

| Function | Purpose |
|----------|---------|
| `DecisionIdempotencyKey` (class) | Idempotency compound key for identifying unique decisions. |
| `StoredRiskRecord` (class) | Representation of a persisted risk record for schema validation. |
| `StorageCapability` (class) | Capabilities supported by the storage engine. |
| `PersistenceResult` (TypedDict) | Standard dictionary output of a persistence attempt. |
| `RiskStateStore.get_drawdown_state(strategy_id: str \| None = None) -> DrawdownState \| None` | Retrieve the drawdown state for the portfolio or a specific strategy. |
| `RiskStateStore.save_drawdown_state(state: DrawdownState, strategy_id: str \| None = None) -> None` | Save the drawdown state. |
| `RiskStateStore.get_kill_switch_state(scope: str, target: str) -> tuple[KillSwitchStateEnum, KillSwitchReason \| None, datetime \| None, str \| None]` | Retrieve kill-switch state tuple. |
| `RiskStateStore.save_kill_switch_state(scope: str, target: str, state: KillSwitchStateEnum, reason: KillSwitchReason \| None = None, triggered_at: datetime \| None = None, triggered_by: str \| None = None) -> None` | Save kill-switch state updates. |
| `RiskStateStore.is_token_revoked(token_id: str) -> bool` | Check if a decision token is marked as revoked. |
| `RiskStateStore.revoke_token(token_id: str) -> None` | Revoke a decision token. |
| `RiskAuditSink.write_event(event: RiskAuditEvent) -> None` | Append a validated event block to the audit store. |
| `RiskAuditSink.get_last_event() -> RiskAuditEvent \| None` | Retrieve the latest audit event block in the chain. |
| `RiskAuditSink.get_all_events() -> list[RiskAuditEvent]` | Retrieve all audit events chronologically. |
| `RiskPolicyStore.get_rules() -> list[PolicyRule]` | Retrieve all active policy rules. |
| `RiskPolicyStore.save_rule(rule: PolicyRule) -> None` | Store or update a policy rule. |
| `RiskDecisionStore.get_decision(decision_id: str) -> RiskDecisionPackage \| None` | Retrieve decision by ID. |
| `RiskDecisionStore.save_decision(decision: RiskDecisionPackage) -> None` | Persist decision package with idempotency handling. |
| `RiskDecisionStore.get_decision_by_request_id(request_id: str) -> RiskDecisionPackage \| None` | Retrieve decision by original request ID. |
| `RiskDecisionStore.list_decisions() -> list[RiskDecisionPackage]` | List all stored decisions. |
| `RiskDecisionStore.get_decision_by_key(request_id: str, workflow_id: str, signal_id: str, decision_material_hash: str) -> RiskDecisionPackage \| None` | Retrieve decision by original idempotency keys. |
| `compute_decision_material_hash(decision: RiskDecisionPackage) -> str` | Compute a deterministic hash of the decision's material inputs. |
| `persist_risk_decision(decision: RiskDecisionPackage, key: DecisionIdempotencyKey, store: RiskDecisionStore) -> PersistenceResult` | Idempotently persists a risk decision package. |
| `validate_storage_schema_compatibility(record: StoredRiskRecord, expected_version: str) -> ValidationResult` | Validates storage schema version compatibility with expected version. |
| `require_live_audit_persistence(capability: StorageCapability, mode: RiskMode) -> ValidationResult` | Fails closed where audit storage is mandatory but unavailable or non-durable. |


## FEAT-RISK-157: Thin repository facade over the shared SQLite risk storage mixin (app.services.risk.storage.repositories)

| Function | Purpose |
|----------|---------|
| `RiskRepository.__init__(db: SQLiteDatabase) -> None` | Simple repository wrapper that keeps the risk layer SQLite-agnostic. |
| `RiskRepository.create_run(*, label: str \| None = None, description: str \| None = None, source: str = 'manual', backtest_id: int \| None = None, context: dict[str, Any] \| None = None) -> int` | Simple repository wrapper that keeps the risk layer SQLite-agnostic. |
| `RiskRepository.load_snapshot_bundle(snapshot_id: int) -> dict[str, Any]` | Simple repository wrapper that keeps the risk layer SQLite-agnostic. |
| `RiskRepository.load_run(run_id: int) -> dict[str, Any]` | Simple repository wrapper that keeps the risk layer SQLite-agnostic. |
| `RiskRepository.load_replay_frames(run_id: int) -> list[dict[str, Any]]` | Simple repository wrapper that keeps the risk layer SQLite-agnostic. |
| `RiskRepository.export_snapshot_reports(snapshot_id: int) -> dict[str, Any]` | Simple repository wrapper that keeps the risk layer SQLite-agnostic. |
| `RiskRepository.export_replay_report(run_id: int) -> dict[str, Any]` | Simple repository wrapper that keeps the risk layer SQLite-agnostic. |


## FEAT-RISK-158: Scenario-specific storage helpers (app.services.risk.storage.scenario_store)

| Function | Purpose |
|----------|---------|
| `RiskScenarioStore.__init__(repository: RiskRepository) -> None` | Persist scenario outputs without the full snapshot-store surface area. |
| `RiskScenarioStore.store(*, snapshot_id: int, scenarios: Iterable[ScenarioResult]) -> None` | Persist scenario outputs without the full snapshot-store surface area. |


## FEAT-RISK-159: High-level snapshot persistence helpers (app.services.risk.storage.snapshot_store)

| Function | Purpose |
|----------|---------|
| `RiskSnapshotStore.__init__(repository: RiskRepository) -> None` | Store and load normalized risk snapshots and closely related artifacts. |
| `RiskSnapshotStore.create_run(**kwargs) -> int` | Store and load normalized risk snapshots and closely related artifacts. |
| `RiskSnapshotStore.store_snapshot_bundle(*, run_id: int, snapshot: RiskSnapshot, scorecard: RiskScorecard \| None = None, recommendations: RecommendationBatch \| None = None, backtest_id: int \| None = None) -> int` | Store and load normalized risk snapshots and closely related artifacts. |
| `RiskSnapshotStore.store_replay_frame(*, run_id: int, frame: ReplayFrame, snapshot_id: int \| None = None, backtest_id: int \| None = None, what_if: WhatIfComparison \| None = None) -> int` | Store and load normalized risk snapshots and closely related artifacts. |
| `RiskSnapshotStore.load_snapshot_bundle(snapshot_id: int)` | Store and load normalized risk snapshots and closely related artifacts. |
| `RiskSnapshotStore.load_run(run_id: int)` | Store and load normalized risk snapshots and closely related artifacts. |
| `RiskSnapshotStore.load_replay_frames(run_id: int)` | Store and load normalized risk snapshots and closely related artifacts. |
| `RiskSnapshotStore.export_snapshot_reports(snapshot_id: int)` | Store and load normalized risk snapshots and closely related artifacts. |
| `RiskSnapshotStore.export_replay_report(run_id: int)` | Store and load normalized risk snapshots and closely related artifacts. |


## FEAT-RISK-160: Contracts for the Stress Testing Engine (app.services.risk.stress.contracts)

| Function | Purpose |
|----------|---------|
| `StressContext` (class) | Context holding input data for stress testing evaluation. |
| `ProjectedPortfolio` (class) | Projected portfolio under shocked market conditions. |
| `StressSummary` (class) | Summary of all evaluated stress test scenarios. |


## FEAT-RISK-161: Stress Testing Engine (app.services.risk.stress.engine)

| Function | Purpose |
|----------|---------|
| `QuickProjectedPortfolio` (class) | Ultra-fast unvalidated portfolio state container to bypass Pydantic overhead. |
| `StressTestingEngine.run_analysis(portfolio_state: Any, market_context: dict[str, Any], proposed_trade: Any \| None = None) -> list[StressScenarioResult]` | Run stress scenario analysis on the portfolio. |
| `evaluate_stress_scenarios(context: StressContext, registry: StressScenarioRegistry, policy: EffectiveRiskPolicy) -> StressSummary` | Evaluate portfolio resilience against all registered scenarios. |
| `apply_market_shock(portfolio: ProjectedPortfolio, scenario: StressScenario, market_context: dict[str, Any]) -> ProjectedPortfolio` | Apply declarative shocks (price, spreads, margins) to a projected portfolio. |
| `calculate_stress_loss(portfolio: ProjectedPortfolio, market_context: dict[str, Any], account_currency: str) -> Decimal` | Derive estimated account-currency loss. |
| `compare_stress_loss_to_policy(loss: Decimal, policy: EffectiveRiskPolicy, equity: Decimal \| None = None) -> LimitResult` | Compare calculated stress loss against policy limit threshold. |


## FEAT-RISK-162: Stress scenario registry (app.services.risk.stress.registry)

| Function | Purpose |
|----------|---------|
| `StressScenarioRegistry.register_scenario(name: str, evaluator: Any) -> None` | Legacy compatibility helper to register scenario in-place. |
| `StressScenarioRegistry.evaluate_portfolio(portfolio_state: Any, proposed_trade: Any, market_context: dict[str, Any], config: Any) -> list[Any]` | Legacy compatibility helper to evaluate all scenarios in registry. |
| `register_stress_scenario(registry: StressScenarioRegistry, scenario: StressScenario) -> StressScenarioRegistry` | Register a new stress scenario, returning a new registry. |
| `get_stress_scenario(registry: StressScenarioRegistry, scenario_id: str) -> StressScenario` | Retrieve a scenario deterministically or fail closed. |
| `build_default_stress_registry() -> StressScenarioRegistry` | Build and return a pre-loaded stress testing scenario registry. |
| `validate_custom_scenario_definition(scenario: Mapping[str, Any]) -> StressScenario` | Validate a custom scenario configuration without arbitrary code execution. |
| `ScenarioRegistry.register(scenario: StressScenario) -> None` | Simple registry for deterministic scenario definitions. |
| `ScenarioRegistry.extend(scenarios: Iterable[StressScenario]) -> None` | Simple registry for deterministic scenario definitions. |
| `build_default_scenario_registry() -> ScenarioRegistry` | Build the default Phase 5 scenario registry. |


## FEAT-RISK-163: Value-at-Risk (VaR) and Expected Shortfall (ES) contracts and enums (app.services.risk.tail_risk.contracts)

| Function | Purpose |
|----------|---------|
| `VaRMethod` (enum) | Supported Value-at-Risk computation methods. |
| `ExpectedShortfallMethod` (enum) | Supported Expected Shortfall computation methods. |
| `VaRCalculationRequest` (class) | Input parameters required for portfolio Value-at-Risk calculations. |
| `ExpectedShortfallRequest` (class) | Input parameters required for portfolio Expected Shortfall calculations. |
| `PortfolioVarianceInputs` (class) | Input data parameters for portfolio variance calculations. |
| `VaRResult` (class) | Encapsulates Value-at-Risk computation outputs. |
| `ExpectedShortfallResult` (class) | Encapsulates Expected Shortfall computation outputs. |


## FEAT-RISK-164: Portfolio Expected Shortfall (ES) / CVaR computation service (app.services.risk.tail_risk.expected_shortfall)

| Function | Purpose |
|----------|---------|
| `select_tail_losses(losses: Sequence[Decimal], confidence: Decimal) -> tuple[Decimal, ...]` | Deterministically selects tail observations. |
| `validate_tail_risk_assumptions(var: VaRSnapshot, es: ExpectedShortfallSnapshot, policy: EffectiveRiskPolicy) -> ValidationResult` | Rejects invalid or insufficient tail evidence. |
| `calculate_expected_shortfall(*args: Any, **kwargs: Any) -> Any` | Calculate portfolio Expected Shortfall, supporting both V1 and V2 signatures. |
| `ExpectedShortfallEngine.calculate_es(portfolio_state: PortfolioState, market_context: dict[str, Any], proposed_trade: ProposedTrade \| None = None, lookback: int = 50, confidence: Decimal = Decimal("0.95"), method: str = "parametric", cov_method: str = "parametric", ewma_decay: Decimal = Decimal("0.94"), shrinkage_intensity: Decimal = Decimal("0.1"), min_samples: int = 20, exclude_last: bool = True) -> Any` | Legacy helper to calculate Expected Shortfall. |


## FEAT-RISK-165: Portfolio Value-at-Risk (VaR) computation service (app.services.risk.tail_risk.var)

| Function | Purpose |
|----------|---------|
| `calculate_covariance(x: Sequence[Decimal], y: Sequence[Decimal]) -> Decimal` | Calculate sample covariance between two aligned series. |
| `calculate_ewma_covariance(x: Sequence[Decimal], y: Sequence[Decimal], decay: Decimal = Decimal("0.94")) -> Decimal` | Calculate Exponentially Weighted Moving Average (EWMA) covariance. |
| `calculate_covariance_matrix(returns_db: Mapping[str, Sequence[Decimal]], method: str = "parametric", ewma_decay: Decimal = Decimal("0.94")) -> dict[str, dict[str, Decimal]]` | Compute pairwise covariance matrix for return series. |
| `shrink_covariance_matrix(matrix: dict[str, dict[str, Decimal]], shrinkage_intensity: Decimal = Decimal("0.1")) -> dict[str, dict[str, Decimal]]` | Apply shrinkage towards diagonal target (constant variance target). |
| `validate_covariance_matrix(matrix: dict[str, dict[str, Decimal]] \| CovarianceMatrix) -> None` | Verify covariance matrix has non-negative diagonal values and is symmetric. |
| `get_position_signed_exposure(symbol: str, quantity: Decimal, direction: str, market_context: dict[str, Any], account_ccy: str) -> Decimal` | Calculate signed exposure of a position in account currency. |
| `get_proposed_trade_signed_exposure(proposed_trade: ProposedTrade, market_context: dict[str, Any], account_ccy: str) -> Decimal` | Calculate signed exposure of a proposed trade in account currency. |
| `align_multiple_return_series(returns_db: dict[str, dict[datetime, Decimal]]) -> dict[str, list[Decimal]]` | Align multiple return series by their common timestamps. |
| `calculate_parametric_var(*args: Any, **kwargs: Any) -> Any` | Compute covariance/volatility-based VaR, supporting V1 and V2 signatures. |
| `calculate_historical_var(*args: Any, **kwargs: Any) -> Any` | Compute empirical VaR from aligned returns, supporting V1 and V2 signatures. |
| `calculate_var_component_contribution(request: VaRCalculationRequest) -> ComponentRiskContribution` | Decompose Value-at-Risk component contributions. |
| `PortfolioVaREngine.calculate_var(portfolio_state: PortfolioState, market_context: dict[str, Any], proposed_trade: ProposedTrade \| None = None, lookback: int = 50, confidence: Decimal = Decimal("0.95"), method: str = "parametric", cov_method: str = "parametric", ewma_decay: Decimal = Decimal("0.94"), shrinkage_intensity: Decimal = Decimal("0.1"), min_samples: int = 20, exclude_last: bool = True) -> Any` | Helper to calculate VaR, converting back to legacy V1 VaRResult. |
| `calculate_risk_contributions(weights: dict[str, Decimal], matrix: dict[str, dict[str, Decimal]], portfolio_vol: Decimal, confidence: Decimal, total_gross_exposure: Decimal) -> tuple[dict[str, Decimal], dict[str, Decimal]]` | Calculate marginal and component risk contributions. |
| `calculate_risk_contribution(weights: dict[str, Decimal], matrix: dict[str, dict[str, Decimal]], portfolio_vol: Decimal, confidence: Decimal, total_gross_exposure: Decimal) -> tuple[dict[str, Decimal], dict[str, Decimal]]` | Calculate marginal and component risk contributions. |
| `calculate_parametric_var_es(weights: dict[str, Decimal], matrix: dict[str, dict[str, Decimal]], confidence: Decimal, total_gross_exposure: Decimal) -> tuple[Decimal, Decimal, Decimal]` | Calculate parametric portfolio VaR and Expected Shortfall. |
| `calculate_historical_var_es(aligned_returns: dict[str, list[Decimal]], weights: dict[str, Decimal], confidence: Decimal, total_gross_exposure: Decimal) -> tuple[Decimal, Decimal]` | Calculate historical portfolio VaR and Expected Shortfall. |
| `historical_var(returns: list[float], confidence: float = 0.95) -> float` | Function historical_var provides risk service behavior. |
| `incremental_var(current_returns: list[float], proposed_returns: list[float], confidence: float = 0.95) -> float` | Function incremental_var provides risk service behavior. |


## FEAT-RISK-166: Official AI-callable Risk tools (app.services.risk.tools.official)

| Function | Purpose |
|----------|---------|
| `ToolError` (class) | Standardized tool error structure. |
| `ToolResponse` (class) | Standardized tool response envelope. |
| `PortfolioRiskSnapshotToolRequest` (class) | Request contract for compiling portfolio risk snapshots. |
| `TradeRiskReviewToolRequest` (class) | Request contract for pre-trade risk checks. |
| `PositionSizeToolRequest` (class) | Request contract for position sizing calculations. |
| `RiskRegimeToolRequest` (class) | Request contract for market regime assessments. |
| `StrategyAdmissionToolRequest` (class) | Request contract for strategy lifecycle promotion reviews. |
| `AllocationReviewToolRequest` (class) | Request contract for capital allocation adjustments. |
| `PortfolioGovernorToolRequest` (class) | Request contract for periodic portfolio governance sweeps. |
| `TokenValidationToolRequest` (class) | Request contract for cryptographic token validations. |
| `KillSwitchStatusToolRequest` (class) | Request contract for checking active kill switches. |
| `ScenarioAnalysisToolRequest` (class) | Request contract for portfolio shock scenario stress tests. |
| `RiskReportToolRequest` (class) | Request contract for generating risk reports. |
| `RiskSnapshotPayload` (class) | Response payload for portfolio risk snapshot metrics. |
| `RiskDecisionPayload` (class) | Response payload for governor decision outcomes. |
| `PositionSizingPayload` (class) | Response payload for calculated position sizes. |
| `TokenValidationPayload` (class) | Response payload for token validations. |
| `KillSwitchPayload` (class) | Response payload for kill switch status queries. |
| `StressPayload` (class) | Response payload for stress test results. |
| `RiskReportPayload` (class) | Response payload for generated risk reports. |
| `build_portfolio_risk_snapshot_tool(request: PortfolioRiskSnapshotToolRequest) -> ToolResponse[RiskSnapshotPayload]` | Compiles portfolio risk snapshot and exposure metrics. |
| `review_trade_risk_tool(request: TradeRiskReviewToolRequest) -> ToolResponse[RiskDecisionPayload]` | Performs pre-trade check against active limits and policies. |
| `calculate_position_size_tool(request: PositionSizeToolRequest) -> ToolResponse[PositionSizingPayload]` | Calculates policy-bounded volume for proposed position. |
| `assess_risk_regime_tool(request: RiskRegimeToolRequest) -> ToolResponse[RegimePayload]` | Assesses active market conditions and regime risk status. |
| `review_strategy_admission_tool(request: StrategyAdmissionToolRequest) -> ToolResponse[RiskDecisionPayload]` | Reviews strategy promotion lifecycle stage. |
| `review_allocation_proposal_tool(request: AllocationReviewToolRequest) -> ToolResponse[RiskDecisionPayload]` | Reviews dynamic capital allocation adjustments. |
| `run_portfolio_risk_governor_tool(request: PortfolioGovernorToolRequest) -> ToolResponse[RiskDecisionPayload]` | Executes portfolio risk governor validation loop. |
| `validate_risk_approval_token_tool(request: TokenValidationToolRequest) -> ToolResponse[TokenValidationPayload]` | Verifies the authenticity and state of an approval token. |
| `check_risk_kill_switch_tool(request: KillSwitchStatusToolRequest) -> ToolResponse[KillSwitchPayload]` | Queries active global/portfolio/strategy kill switch status. |
| `run_risk_scenario_analysis_tool(request: ScenarioAnalysisToolRequest) -> ToolResponse[StressPayload]` | Runs stress scenario analysis against portfolio models. |
| `generate_risk_report_tool(request: RiskReportToolRequest) -> ToolResponse[RiskReportPayload]` | Generates standard and redacted risk reports. |


## FEAT-RISK-167: Official risk tool registry and validation (app.services.risk.tools.registry)

| Function | Purpose |
|----------|---------|
| `RiskToolDefinition` (class) | Immutable official risk tool metadata. |
| `RiskToolRegistry` (class) | Catalog of approved risk tools. |
| `validate_risk_tool_metadata(definition: RiskToolDefinition) -> ValidationResult` | Verifies that the side effects and security metadata of a tool are accurate. |
| `build_risk_tool_registry() -> RiskToolRegistry` | Builds and returns the official, immutable risk tool catalog. |
| `list_risk_tools(registry: RiskToolRegistry) -> tuple[RiskToolDefinition, ...]` | Exposes deterministic public tool metadata. |
| `get_risk_tool_definition(name: str, registry: RiskToolRegistry) -> RiskToolDefinition` | Resolves an approved tool metadata definition. |
| `ScoreRegistry.register(family: ScoreFamily) -> None` | Class ScoreRegistry provides risk service behavior. |
| `ScoreRegistry.extend(families: Iterable[ScoreFamily]) -> None` | Class ScoreRegistry provides risk service behavior. |
| `ScoreRegistry.compute_all(context: ScoreContext) -> list[ScoreRow]` | Class ScoreRegistry provides risk service behavior. |
| `build_default_score_registry() -> ScoreRegistry` | Function build_default_score_registry provides risk service behavior. |


## FEAT-RISK-168: Risk-local validation result helpers (app.services.risk.validations)

| Function | Purpose |
|----------|---------|
| `ValidationResult` (TypedDict) | Native risk validation result. |
| `validate_numeric_range(value: object, *, field_name: str, minimum: float \| None = None, maximum: float \| None = None) -> ValidationResult` | Validate a finite numeric value against inclusive bounds. |
| `validate_required_fields(payload: Mapping[str, object], required_fields: Sequence[str]) -> ValidationResult` | Validate that required fields are present and non-``None``. |
| `validate_schema_version(payload_version: str \| None, schema_version: str \| None, *, compatible_versions: Sequence[str] = ()) -> ValidationResult` | Validate optional semantic-version compatibility. |
| `validate_mapping_schema(payload: Mapping[str, object], schema: Mapping[str, object], *, reject_extra: bool = True) -> ValidationResult` | Validate a simple mapping schema. |
| `validate_input_schema(payload: Mapping[str, object], schema: Mapping[str, object], *, request_id: str \| None = None) -> StandardResponse` | Official low-risk read-only input schema validator. |
| `validate_output_schema(payload: Mapping[str, object], schema: Mapping[str, object], *, request_id: str \| None = None) -> StandardResponse` | Official low-risk read-only output schema validator. |
| `validate_handoff_payload(payload: Mapping[str, object], *, request_id: str \| None = None) -> StandardResponse` | Official low-risk read-only handoff payload validator. |
| `validate_evidence_pack(payload: Mapping[str, object], *, request_id: str \| None = None) -> StandardResponse` | Official low-risk read-only evidence pack validator. |
| `validate_approval_packet(payload: Mapping[str, object], *, request_id: str \| None = None) -> StandardResponse` | Official low-risk read-only approval packet validator. |
| `validate_registry_entry(payload: Mapping[str, object], *, request_id: str \| None = None) -> StandardResponse` | Official low-risk read-only registry entry validator. |
| `validate_data_freshness(payload: Mapping[str, object], *, request_id: str \| None = None) -> StandardResponse` | Official low-risk read-only data freshness validator. |
| `validation_failed_paths(result: ValidationResult) -> list[str]` | Return invalid field paths from a validation result where available. |


## FEAT-RISK-169: Account-level validators for the canonical risk state (app.services.risk.validators.account)

| Function | Purpose |
|----------|---------|
| `validate_account_state(account: AccountState) -> ValidationSummary` | Validate that account inputs are complete enough for risk processing. |


## FEAT-RISK-170: Shared validation result types for the risk subsystem (app.services.risk.validators.common)

| Function | Purpose |
|----------|---------|
| `ValidationIssue` (model) | One validation issue discovered while building canonical state. |
| `ValidationSummary.has_errors -> bool` | Aggregated validation result for a portfolio state. |
| `ValidationSummary.has_warnings -> bool` | Aggregated validation result for a portfolio state. |
| `ValidationSummary.add(severity: str, code: str, message: str, **context: Any) -> ValidationSummary` | Aggregated validation result for a portfolio state. |
| `ValidationSummary.extend(other: ValidationSummary) -> ValidationSummary` | Aggregated validation result for a portfolio state. |


## FEAT-RISK-171: Risk limit validators for the canonical risk state (app.services.risk.validators.limits)

| Function | Purpose |
|----------|---------|
| `validate_risk_limits(limits: RiskLimits) -> ValidationSummary` | Validate risk limit configuration for canonical portfolio state. |


## FEAT-RISK-172: Market data validators for the canonical risk state (app.services.risk.validators.market)

| Function | Purpose |
|----------|---------|
| `validate_market_states(markets: dict[str, MarketState], positions: Iterable[PositionState], require_synchronized_coverage: bool = True) -> ValidationSummary` | Validate market slices using the shared utility validator where possible. |


## FEAT-RISK-173: Position-level validators for the canonical risk state (app.services.risk.validators.positions)

| Function | Purpose |
|----------|---------|
| `validate_position_states(positions: Iterable[PositionState]) -> ValidationSummary` | Validate normalized positions before portfolio-level risk math. |


## FEAT-RISK-174: Symbol specification validators for the canonical risk state (app.services.risk.validators.symbols)

| Function | Purpose |
|----------|---------|
| `validate_symbol_states(symbols: dict[str, SymbolState], positions: Iterable[PositionState]) -> ValidationSummary` | Validate symbol specifications required by existing risk math. |


## FEAT-RISK-175: Risk request assembly from validated proposal and current snapshots (app.services.risk.workflows.request_assembler)

| Function | Purpose |
|----------|---------|
| `RiskRequestAssemblyContext` (model) | Envelope and policy context required to assemble a risk request. |
| `assemble_risk_assessment_request(*, proposal: TradeProposal, account_snapshot: AccountSnapshot, portfolio_snapshot: PortfolioSnapshot, market_snapshot: MarketSnapshot, context: RiskRequestAssemblyContext, risk_request_id: str \| None = None) -> RiskAssessmentRequest` | Build a canonical risk request from a proposal and grounded snapshots. |

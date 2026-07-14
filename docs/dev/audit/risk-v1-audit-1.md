# Risk — Version 1 Code Audit

## 1. Audit Scope

* **Domain:** Risk
* **Repository:** `haruperi/HaruQuantAI`
* **Repository branch audited:** `main`
* **Repository head observed:** `68851eb6898b229f49f1295c37748c63eefed3d3`
* **Package path:** `app/services/risk/`
* **Tests path supplied:** `tests/risk/unit/`
* **Usage/examples path supplied:** `tests/risk/usage/`
* **Files inspected:**
  * 73 Python files under `app/services/risk/` at package-tree and public-export level.
  * Key implementation bodies inspected for the root facade, boundary contracts, errors, validations, policy facade, governor, official tools, tool registry, and major package initializers.
  * Four JSON profiles under `app/services/risk/configs/`.
  * `app/services/risk/README.md`.
  * Representative unit tests including `tests/risk/unit/test_governor.py`.
  * The usage script `tests/risk/usage/05_risk.py`.
  * Confirmed external caller `app/agentic/tools/risk.py`.
  * Related runtime package `app/services/simulator/engine.py`.
* **Related packages searched:** `app/agentic/tools/`, `app/services/simulator/`, package root exports, repository commit history, current risk tests and usage examples.
* **Excluded:** generated files, caches, virtual environments, documentation outside the package except where needed to establish call paths, and Version 2 requirements comparison.
* **Audit limitations:**
  * GitHub repository code search was not indexed for this repository. Direct file retrieval and commit-tree evidence were available, but a complete repository-wide text search for every symbol was not.
  * The package tree is complete based on repository comparison and direct file retrieval. Caller classifications are lower-bound findings: a symbol is marked **Used** only where an actual call/import path was observed; unconfirmed symbols are not declared dead.
  * Full bodies were not retrievable in one operation for every one of the 73 Python files. For support files, public behavior is grounded in their `__init__.py` exports, direct imports, commit-level path history, and inspected callers. Where an exact class method body was not inspected, this is stated rather than inferred.
  * The supplied current test and usage paths exist. Historical documentation and commit messages also refer to older paths such as `tests/unit/app/services/risk/` and `tests/usage/05_risk.py`; those older paths are not treated as current runtime evidence.

## 2. Executive Summary

The domain provides a large risk-governance surface covering canonical models, configuration profiles and hashing, policy resolution, market-regime assessment, position sizing, FX exposure, correlation, VaR/Expected Shortfall, stress testing, drawdown, margin and execution feasibility, ordered limits, allocation review, lifecycle review, kill switches, decision synthesis, decision tokens, audit chaining, reports, observability, storage ports, an in-memory implementation, and an official AI-tool layer.

The strongest operational workflow is:

```text
app.agentic.tools.risk.review_trade_risk()
→ app.services.risk.tools.official.review_trade_risk_tool()
→ shared RiskGovernor.review_trade()
→ RiskGovernor.review_trade_risk()
→ policy / audit-chain / regime / correlation / sizing / tail-risk /
  stress / ordered limits / execution-feasibility
→ decision token
→ in-memory decision persistence and audit event
→ RiskDecisionPayload
```

This workflow is implemented and unit-tested. It does not mutate a broker. Its current confirmed external consumer is the agent-tool facade. No confirmed Trading-domain execution caller was found with the available evidence.

The most important structural findings are:

1. The root package exports **376 names**, making internal helpers, compatibility aliases, contracts, engines, tools, and orchestration functions appear equally public.
2. The code contains both compatibility surfaces and newer structured surfaces. Several package initializers contain executable compatibility logic rather than exports only.
3. `app/services/risk/contracts.py` overlaps with `app/services/risk/models/contracts.py`, including duplicate names with different schemas.
4. There are two tool facades: `app/services/risk/tools/official.py` and `app/agentic/tools/risk.py`. They duplicate envelopes, live-context checks, request conversion, and error handling.
5. The official tool backend uses a module-global `InMemoryRiskStateStore`; confirmed runtime persistence is therefore process-local unless another caller constructs `RiskGovernor` with different ports.
6. Several safety calculations inside the governor catch broad exceptions and continue. The portfolio-snapshot tool replaces failed VaR and stress calculations with zero.
7. The current `SimpleBacktestEngine` imports Data and Strategy but not Risk, so the simulated strategy-intent workflow bypasses this domain.
8. A mock override path in `RiskGovernor.review_trade_risk()` can approve a blocked/rejected request when `market_context["approval_token_valid"] is True` and no valid token object was parsed.
9. Test utilities and private helpers are publicly exported from subpackages.
10. README/test path references and the current repository layout are not fully aligned.

Evidence quality is **high** for package structure, exports, the agent-tool caller, the official-tool backend, and the governor workflow. Evidence quality is **medium** for repository-wide “unused” conclusions because indexed code search was unavailable.

```text
Module folders: 19 | Files: 73 Python + 4 JSON profiles | Public symbols: 376 top-level exports | Symbols with confirmed non-test callers: 36 lower-bound (9.6%) | Workflows found: 10
```

## 3. Actual Package Structure

```text
app/services/risk/
├── __init__.py
│   └── 376 re-exported public names spanning the complete domain
├── contracts.py
│   ├── Contract
│   ├── RiskRejection
│   ├── PositionSizingResult
│   ├── RiskDecision
│   └── RiskAuditEvent
├── errors.py
│   ├── ErrorPayload
│   ├── RISK_ERROR_CODES
│   ├── ERROR_MESSAGES
│   ├── to_risk_error_payload()
│   └── RiskError and 27 specialized error classes
├── validations.py
│   ├── ValidationResult
│   ├── _ok()
│   └── _fail()
├── configs/
│   ├── default.json
│   ├── live_conservative.json
│   ├── paper.json
│   └── prop_firm_default.json
├── audit/
│   ├── __init__.py
│   ├── events.py
│   │   ├── AuditContext
│   │   ├── AuditRedactionPolicy
│   │   ├── build_canonical_audit_payload()
│   │   ├── redact_audit_payload()
│   │   └── create_risk_audit_event()
│   ├── hash_chain.py
│   │   ├── AuditChainVerification
│   │   ├── build_genesis_hash()
│   │   ├── append_audit_hash()
│   │   ├── verify_risk_audit_chain()
│   │   └── require_valid_audit_chain()
│   └── tokens.py
│       ├── DefaultTokenSigner
│       ├── RequiredActionScope
│       ├── RiskDecisionTokenSigner
│       ├── TokenValidationContext
│       ├── TokenValidationResult
│       ├── create_risk_decision_token()
│       ├── validate_risk_approval_token()
│       ├── revoke_risk_approval_token()
│       ├── validate_token_expiry()
│       └── validate_token_scope()
├── config/
│   ├── __init__.py
│   ├── hashing.py
│   │   ├── ConfigHashComparison
│   │   ├── canonicalize_risk_config_for_hash()
│   │   ├── hash_risk_config()
│   │   ├── compare_risk_config_hashes()
│   │   └── validate_risk_config_hash()
│   ├── loader.py
│   │   ├── APPROVED_OVERRIDE_KEYS
│   │   ├── RiskConfigHash
│   │   ├── RiskConfigLoader
│   │   ├── RiskProfileRegistry
│   │   ├── _registry
│   │   └── load_risk_config()
│   ├── profiles.py
│   │   ├── build_safe_default_profile()
│   │   ├── build_prop_firm_default_profile()
│   │   ├── build_paper_profile()
│   │   ├── build_live_conservative_profile()
│   │   ├── get_builtin_risk_profile()
│   │   └── list_builtin_risk_profiles()
│   └── schema.py
│       ├── MAX_DAILY_LOSS_PCT
│       ├── MAX_TOTAL_LOSS_PCT
│       ├── MAX_MARGIN_UTILIZATION_PCT
│       ├── MAX_EFFECTIVE_LEVERAGE
│       ├── MAX_RISK_PER_TRADE
│       └── validate_risk_config()
├── models/
│   ├── __init__.py
│   ├── contracts.py
│   │   └── 40+ canonical request, snapshot, state, policy, token,
│       decision, warning, rejection, allocation and scenario contracts
│   ├── enums.py
│   │   ├── KillSwitchReason
│   │   ├── KillSwitchStateEnum
│   │   ├── RiskAction
│   │   ├── RiskDecisionStatus
│   │   ├── RiskMode
│   │   ├── RiskReasonCode
│   │   ├── RiskSeverity
│   │   ├── list_risk_reason_codes()
│   │   └── risk_severity_rank()
│   └── serialization.py
│       ├── to_canonical_risk_payload()
│       ├── from_canonical_risk_payload()
│       └── validate_risk_model_round_trip()
├── storage/
│   ├── __init__.py
│   ├── ports.py
│   │   ├── DecisionIdempotencyKey
│   │   ├── PersistenceResult
│   │   ├── RiskAuditSink
│   │   ├── RiskDecisionStore
│   │   ├── RiskPolicyStore
│   │   ├── RiskStateStore
│   │   ├── StorageCapability
│   │   ├── StoredRiskRecord
│   │   ├── compute_decision_material_hash()
│   │   ├── persist_risk_decision()
│   │   ├── require_live_audit_persistence()
│   │   └── validate_storage_schema_compatibility()
│   └── in_memory.py
│       ├── InMemoryRiskStateStore
│       ├── FailingStore
│       ├── StorageOperation
│       ├── create_in_memory_risk_store()
│       └── simulate_storage_failure()
├── policy/
│   ├── __init__.py
│   │   ├── PolicyVersion
│   │   ├── PolicyBundle
│   │   ├── PolicyResolutionQuery
│   │   ├── PolicyOverrideRequest
│   │   ├── load_risk_policy()
│   │   ├── validate_risk_policy()
│   │   ├── validate_override_token()
│   │   ├── validate_risk_budget_gates()
│   │   └── check_policy_permission()
│   ├── contracts.py
│   │   ├── EffectiveRiskPolicy
│   │   ├── OverrideValidationResult
│   │   ├── PolicyPrecedenceRule
│   │   ├── RiskOverrideRequest
│   │   ├── RiskPolicy
│   │   └── validate_policy_scope()
│   ├── overrides.py
│   │   ├── requires_override_approval()
│   │   ├── validate_risk_override_request()
│   │   └── validate_token_config_compatibility()
│   └── resolver.py
│       ├── RiskPolicyEngine
│       ├── evaluate_risk_budget()
│       ├── resolve_effective_policy()
│       ├── resolve_policy()
│       ├── resolve_risk_policy()
│       └── validate_policy_expiry()
├── regime/
│   ├── __init__.py
│   ├── assessor.py
│   │   ├── LiquidityRegime
│   │   ├── NewsRegime
│   │   ├── RegimeAssessment
│   │   ├── RegimeResult
│   │   ├── RegimeRiskEngine
│   │   ├── RiskRegime
│   │   ├── RolloverRegime
│   │   ├── SessionRegime
│   │   ├── SpreadRegime
│   │   ├── SpreadSigmaThresholds
│   │   ├── VolatilityRegime
│   │   ├── VolatilityThresholds
│   │   ├── assess_risk_regime()
│   │   ├── classify_spread_regime()
│   │   ├── classify_volatility_regime()
│   │   ├── is_rollover_blackout()
│   │   └── validate_market_freshness()
│   └── validation.py
│       ├── build_regime_reason_codes()
│       └── validate_regime_inputs()
├── correlation/
│   ├── __init__.py
│   │   └── ReturnType compatibility class
│   ├── contracts.py
│   │   ├── AlignedReturns
│   │   ├── ClosedBar
│   │   ├── ClusterExposureAssessment
│   │   ├── ComponentRiskContribution
│   │   ├── CorrelationAlignmentPolicy
│   │   ├── CorrelationCluster
│   │   ├── CorrelationFallbackContext
│   │   ├── CorrelationMethod
│   │   ├── CovarianceMatrix
│   │   ├── ReturnMethod
│   │   └── ReturnSeries
│   ├── returns.py
│   │   ├── align_return_series()
│   │   ├── build_return_series()
│   │   ├── calculate_pearson()
│   │   ├── calculate_returns()
│   │   └── validate_correlation_inputs()
│   ├── fallbacks.py
│   │   ├── build_conservative_correlation_snapshot()
│   │   ├── resolve_correlation_fallback()
│   │   └── should_fail_closed_for_missing_correlation()
│   └── engine.py
│       ├── CorrelationEngine
│       ├── _get_symbol_gross_exposure()
│       ├── build_correlation_clusters()
│       ├── calculate_cluster_exposure()
│       ├── calculate_cluster_exposures()
│       ├── calculate_component_risk_contribution()
│       ├── calculate_correlation_impact()
│       ├── calculate_correlation_matrix()
│       ├── calculate_correlation_multiplier()
│       ├── calculate_correlation_snapshot()
│       ├── calculate_marginal_correlation()
│       ├── calculate_portfolio_returns()
│       ├── calculate_symbol_cluster_exposure()
│       ├── detect_correlation_spikes()
│       └── evaluate_proposed_trade_correlation()
├── exposure/
│   ├── __init__.py
│   ├── fx_legs.py
│   │   ├── ContractSpecification
│   │   ├── FxPair
│   │   ├── decompose_fx_trade()
│   │   ├── parse_fx_symbol()
│   │   └── validate_currency_conversion_requirements()
│   └── aggregation.py
│       ├── ClusterExposureEngine
│       ├── CurrencyExposureEngine
│       ├── ExposureSnapshotBuilder
│       ├── SymbolExposureEngine
│       ├── _resolve_base_quote()
│       ├── _resolve_conversion_rate()
│       ├── aggregate_currency_legs()
│       ├── calculate_currency_exposure()
│       ├── calculate_currency_leg_exposure()
│       ├── calculate_gross_and_net_exposure()
│       ├── calculate_net_currency_exposure()
│       ├── calculate_projected_exposure()
│       ├── calculate_symbol_exposure()
│       ├── decompose_position()
│       ├── detect_hidden_concentration()
│       └── enforce_currency_rounding()
├── sizing/
│   ├── __init__.py
│   ├── contracts.py
│   │   ├── AdvisorySizingResult
│   │   ├── CorrelationImpact
│   │   ├── KellyEvidence
│   │   ├── PositionSizingRequest
│   │   ├── PositionSizingResult
│   │   ├── RiskMilestone
│   │   ├── SizingMethod
│   │   └── SymbolRiskMetadata
│   ├── normalization.py
│   │   ├── build_volume_rejection()
│   │   ├── normalize_volume()
│   │   ├── validate_normalized_volume()
│   │   └── validate_symbol_volume_metadata()
│   └── calculators.py
│       ├── VolatilitySizingEngine
│       ├── calculate_correlation_adjusted_size()
│       ├── calculate_fixed_fractional_size()
│       ├── calculate_fixed_risk_size()
│       ├── calculate_kelly_reference_size()
│       ├── calculate_milestone_size()
│       ├── calculate_position_size()
│       ├── calculate_stop_distance()
│       ├── calculate_volatility_adjusted_size()
│       └── convert_stop_distance_to_account_risk()
├── tail_risk/
│   ├── __init__.py
│   │   ├── calculate_portfolio_var()
│   │   └── calculate_var_es_snapshots()
│   ├── contracts.py
│   │   ├── ExpectedShortfallMethod
│   │   ├── ExpectedShortfallRequest
│   │   ├── ExpectedShortfallResult
│   │   ├── PortfolioVarianceInputs
│   │   ├── VaRCalculationRequest
│   │   ├── VaRMethod
│   │   └── VaRResult
│   ├── expected_shortfall.py
│   │   ├── ExpectedShortfallEngine
│   │   ├── calculate_expected_shortfall()
│   │   ├── select_tail_losses()
│   │   └── validate_tail_risk_assumptions()
│   └── var.py
│       ├── PortfolioVaREngine
│       ├── calculate_covariance()
│       ├── calculate_covariance_matrix()
│       ├── calculate_ewma_covariance()
│       ├── calculate_historical_var()
│       ├── calculate_historical_var_es()
│       ├── calculate_parametric_var()
│       ├── calculate_parametric_var_es()
│       ├── calculate_portfolio_volatility()
│       ├── calculate_risk_contribution()
│       ├── calculate_risk_contributions()
│       ├── calculate_var_component_contribution()
│       ├── shrink_covariance_matrix()
│       └── validate_covariance_matrix()
├── stress/
│   ├── __init__.py
│   │   └── legacy aliases and scenario-specific compatibility wrappers
│   ├── contracts.py
│   │   ├── ProjectedPortfolio
│   │   ├── StressContext
│   │   ├── StressScenario
│   │   └── StressSummary
│   ├── registry.py
│   │   ├── StressScenarioRegistry
│   │   ├── build_default_stress_registry()
│   │   ├── get_stress_scenario()
│   │   ├── register_stress_scenario()
│   │   └── validate_custom_scenario_definition()
│   └── engine.py
│       ├── QuickProjectedPortfolio
│       ├── StressTestingEngine
│       ├── apply_market_shock()
│       ├── calculate_stress_loss()
│       ├── compare_stress_loss_to_policy()
│       └── evaluate_stress_scenarios()
├── feasibility/
│   ├── __init__.py
│   ├── drawdown.py
│   │   ├── DrawdownGovernor
│   │   ├── DrawdownThrottlingState
│   │   ├── RiskStepDownState
│   │   ├── apply_drawdown_throttle()
│   │   ├── calculate_daily_drawdown()
│   │   ├── calculate_drawdown_multiplier()
│   │   ├── calculate_strategy_drawdown()
│   │   ├── calculate_total_drawdown()
│   │   ├── check_revenge_trading()
│   │   ├── determine_drawdown_state()
│   │   ├── determine_drawdown_throttling()
│   │   ├── persist_drawdown_state()
│   │   ├── restore_drawdown_state()
│   │   └── verify_drawdown_limits()
│   ├── margin.py
│   │   ├── LeverageSnapshot
│   │   ├── LiquiditySnapshot
│   │   ├── MarginRequirement
│   │   ├── MarginRiskEngine
│   │   ├── calculate_current_margin_usage()
│   │   ├── calculate_free_margin_after_reservations()
│   │   ├── calculate_free_margin_after_trade()
│   │   ├── calculate_margin_requirement()
│   │   ├── calculate_projected_margin()
│   │   ├── calculate_projected_margin_usage()
│   │   ├── check_exit_liquidity()
│   │   ├── check_leverage_limit()
│   │   ├── check_margin_limits()
│   │   ├── check_margin_usage()
│   │   ├── evaluate_margin_governance()
│   │   ├── exit_liquidity_stress_check()
│   │   └── verify_margin_limits()
│   └── execution_gate.py
│       ├── BrokerConstraintSnapshot
│       ├── ExecutionFeasibilityResult
│       ├── ExecutionRiskGate
│       ├── SlippagePolicy
│       ├── SpreadPolicy
│       ├── assess_execution_feasibility()
│       ├── check_execution_feasibility()
│       ├── check_holding_time_limit()
│       ├── check_lot_step_validity()
│       ├── check_slippage_limit()
│       ├── check_slippage_to_sigma()
│       ├── check_spread_limit()
│       ├── check_spread_to_sigma()
│       ├── check_stop_distance_validity()
│       ├── check_stop_freeze_level()
│       ├── check_trade_frequency()
│       ├── check_trade_frequency_limit()
│       ├── check_volume_feasibility()
│       ├── evaluate_execution_feasibility()
│       ├── validate_micro_scalping_costs()
│       ├── validate_stop_and_freeze_levels()
│       └── verify_execution_limits()
├── limits/
│   ├── __init__.py
│   ├── contracts.py
│   │   ├── DEFAULT_LIMIT_PRECEDENCE
│   │   ├── LimitAssessment
│   │   ├── LimitCheck
│   │   ├── LimitCheckFunction
│   │   ├── LimitContext
│   │   ├── LimitPrecedence
│   │   └── LimitResult
│   ├── checks.py
│   │   └── 27 deterministic limit-check functions
│   └── engine.py
│       ├── FUNCTION_TO_LIMIT_NAMES
│       ├── ORDERED_LIMIT_CHECKS
│       ├── REGISTERED_LIMIT_NAMES
│       ├── LimitEngine
│       ├── build_composite_breach_flags()
│       ├── check_risk_limits()
│       ├── evaluate_ordered_limits()
│       ├── run_limit_checks()
│       └── select_primary_failure()
├── governance/
│   ├── __init__.py
│   ├── allocation.py
│   │   ├── AllocatableRisk
│   │   ├── AllocationAssessment
│   │   ├── AllocationMethod
│   │   ├── AllocationPlan
│   │   ├── AllocationReviewRequest
│   │   ├── AllocationReviewResult
│   │   ├── RiskAllocator
│   │   └── allocation calculation, adjustment and verification functions
│   ├── kill_switch.py
│   │   ├── ApprovalContext
│   │   ├── KillSwitchAssessment
│   │   ├── KillSwitchManager
│   │   ├── KillSwitchResumeRequest
│   │   ├── KillSwitchScope
│   │   ├── KillSwitchService
│   │   ├── KillSwitchState
│   │   ├── KillSwitchTriggerRequest
│   │   ├── PortfolioKillSwitch
│   │   ├── RiskKillSwitch
│   │   ├── StrategyKillSwitch
│   │   └── trigger, query, resume and validation functions
│   └── lifecycle.py
│       ├── STAGE_SEQUENCE
│       ├── LifecycleAssessment
│       ├── LifecycleEvidence
│       ├── LiveReadinessRequest
│       ├── LiveReadinessReview
│       ├── ModePromotionReview
│       ├── RiskLifecycleGate
│       ├── RiskLifecycleState
│       ├── StrategyAdmissionReview
│       ├── StrategyLifecycleState
│       └── lifecycle evaluation and review functions
├── governor/
│   ├── __init__.py
│   ├── decision_synthesis.py
│   │   ├── GateResult
│   │   ├── GovernorEvaluationContext
│   │   ├── RiskReductionPlan
│   │   ├── determine_decision_status()
│   │   ├── is_decision_token_eligible()
│   │   ├── select_primary_risk_reason()
│   │   └── synthesize_decision()
│   └── governor.py
│       ├── RiskGovernor
│       ├── RiskGovernorDecision
│       ├── review_allocation_proposal()
│       ├── review_live_readiness()
│       ├── review_mode_promotion()
│       ├── review_strategy_admission()
│       ├── review_trade_risk()
│       ├── run_portfolio_risk_governor()
│       └── run_risk_governor_checks()
├── observability/
│   ├── __init__.py
│   ├── decorators.py
│   │   └── risk_observed()
│   └── metrics.py
│       ├── RISK_METRICS_REGISTRY
│       └── risk metric registry types/functions
├── reports/
│   ├── __init__.py
│   ├── builder.py
│   │   ├── PortfolioRiskReport
│   │   ├── ReportRedactionPolicy
│   │   ├── RiskDecisionSummary
│   │   ├── RiskReport
│   │   ├── RiskReportBuilder
│   │   ├── RiskReportEvidence
│   │   ├── RiskReportOptions
│   │   ├── build_portfolio_risk_snapshot()
│   │   ├── build_risk_decision_summary()
│   │   ├── generate_risk_report()
│   │   └── redact_risk_report()
│   └── exporter.py
│       ├── AuthorizedReportPath
│       ├── ReportWriteReceipt
│       ├── build_report_write_receipt()
│       ├── validate_report_export_destination()
│       └── write_risk_report()
├── readiness/
│   ├── __init__.py
│   └── readiness.py
│       ├── DependencyStatus
│       ├── DryRunReport
│       ├── ReadinessAssessment
│       ├── ReadinessDeliveryPlan
│       ├── RiskModeMatrix
│       ├── RiskReadinessManifest
│       ├── build_readiness_dry_run()
│       ├── validate_delivery_plan()
│       ├── validate_phase_dependencies()
│       └── validate_risk_mode_matrix()
└── tools/
    ├── __init__.py
    ├── official.py
    │   ├── ToolError
    │   ├── ToolResponse
    │   ├── 10 request contracts
    │   ├── 7 payload contracts/aliases
    │   ├── 11 official tool functions
    │   ├── _shared_store
    │   └── _shared_governor
    └── registry.py
        ├── RiskToolDefinition
        ├── RiskToolRegistry
        ├── validate_risk_tool_metadata()
        ├── build_risk_tool_registry()
        ├── list_risk_tools()
        └── get_risk_tool_definition()
```

## 4. Module and File Inventory

Files are ordered from foundational contracts/configuration through calculations, orchestration, and external facades.

| Module | File | Responsibility | Key exports | Dependencies | Usage status | Value status |
|---|---|---|---|---|---|---|
| Root | `errors.py` | Risk-local error taxonomy and redacted boundary mapping | `RiskError`, specialized errors, `to_risk_error_payload`, constants | Stdlib; `app.utils.logger`, `app.utils.security` | Used internally | Supporting |
| Root | `validations.py` | Standard validation result shape | `ValidationResult`, `_ok`, `_fail` | Stdlib only | Used by tool registry; private helpers publicly exposed | Supporting |
| Root | `contracts.py` | Separate boundary contract family | `Contract`, `RiskDecision`, `RiskRejection`, `PositionSizingResult`, `RiskAuditEvent` | Stdlib; Pydantic; Utils; type-only Trading `OrderIntent` | Possibly used; no confirmed current runtime caller | Questionable |
| Models | `models/contracts.py` | Canonical operational contracts | Requests, states, snapshots, configs, decisions, tokens, scenarios | Stdlib; Pydantic; local enums/validation | Used throughout domain and agent tools | Essential |
| Models | `models/enums.py` | Stable status/action/reason catalogs | Risk and kill-switch enums; rank/list helpers | Stdlib | Used throughout domain | Essential |
| Models | `models/serialization.py` | Canonical payload conversion and round-trip check | three serialization functions | Stdlib; local models; Utils | Used by usage examples; runtime caller unconfirmed | Useful |
| Models | `models/__init__.py` | Canonical model facade | all model contracts/enums/helpers | Local model files | Used throughout | Supporting |
| Config | `config/schema.py` | Hard ceilings and config validation | five limit constants; `validate_risk_config` | Pydantic/model contracts | Used by loader and policy validation | Essential |
| Config | `config/profiles.py` | Built-in profile constructors and lookup | four builders; get/list functions | Local models/config | Used by loader | Essential |
| Config | `config/hashing.py` | Deterministic config hash and comparison | hash/compare/validate helpers | Stdlib; models; Utils | Used by token/config workflows and examples | Essential |
| Config | `config/loader.py` | Profile registry, JSON loading and approved override handling | loader/registry classes, `load_risk_config`, `_registry` | Stdlib JSON/path; local schema/profiles/models | Used by tools, policy, agent facade | Essential |
| Config | `config/__init__.py` | Configuration facade | loader, hash, profile and ceiling symbols | Local config files | Used widely | Supporting |
| Config | `configs/*.json` | Four concrete policy profiles | default, paper, prop-firm, live-conservative data | JSON | Used through loader | Essential |
| Storage | `storage/ports.py` | Storage interfaces, idempotency and persistence rules | four store ports, persistence models/helpers | Stdlib; local models | Used by governor | Essential |
| Storage | `storage/in_memory.py` | Process-local implementation and failure test doubles | `InMemoryRiskStateStore`, `FailingStore`, factories | Stdlib; storage ports/models | Used by official tools and unit tests | Useful |
| Storage | `storage/__init__.py` | Storage facade | ports, implementation, test utilities | Local storage files | Used | Supporting |
| Audit | `audit/events.py` | Redacted canonical audit-event creation | contexts/policy and event helpers | Stdlib; models; Utils; storage port | Used by governor | Essential |
| Audit | `audit/hash_chain.py` | Append-only hash-chain generation and verification | verification model and chain functions | Stdlib hashing; models/storage | Used by governor live gate | Essential |
| Audit | `audit/tokens.py` | Decision-token signing, validation and revocation | signer interfaces/classes and token functions | Stdlib crypto/time; models/storage | Used by governor/tools | Essential |
| Audit | `audit/__init__.py` | Audit/token facade | all audit symbols | Local audit files | Used | Supporting |
| Policy | `policy/contracts.py` | Policy, effective-policy and override contracts | `RiskPolicy`, `EffectiveRiskPolicy`, override models | Pydantic; models | Used by resolver/stress/governor | Essential |
| Policy | `policy/overrides.py` | Approval requirement and override validation | three validation functions | Models; policy contracts; audit/config | Used by policy facade/examples | Useful |
| Policy | `policy/resolver.py` | Rule matching, precedence and effective config resolution | engine and resolution functions | Stdlib; config/models/contracts | Used directly by governor | Essential |
| Policy | `policy/__init__.py` | Facade plus compatibility models and wrappers | policy metadata models; load/validate/permission wrappers | Pydantic; config; models; Utils; local policy files | Used; contains unrelated responsibilities | Useful |
| Regime | `regime/validation.py` | Regime input validation/reason construction | two functions | Local models/contracts | Used by assessor | Supporting |
| Regime | `regime/assessor.py` | Market condition classification and gate result | enums, threshold models, engine, assessors | Stdlib; models/config/policy | Used by governor and agent tool | Essential |
| Regime | `regime/__init__.py` | Regime facade | assessor and validation exports | Local regime files | Used | Supporting |
| Correlation | `correlation/contracts.py` | Returns/covariance/correlation data contracts | 11 contracts/enums | Pydantic; Decimal | Used by calculation files | Supporting |
| Correlation | `correlation/returns.py` | Return calculation and alignment | five functions | Math/numeric support; local contracts | Used by correlation engine | Essential |
| Correlation | `correlation/fallbacks.py` | Conservative missing-data behavior | three functions | Local contracts/models | Used by correlation paths | Useful |
| Correlation | `correlation/engine.py` | Correlation matrix, clusters and proposed-trade impact | engine and 14 helpers | Numeric support; models; returns/fallbacks | Used by governor and agent facade | Essential |
| Correlation | `correlation/__init__.py` | Facade plus `ReturnType` compatibility class | all correlation exports | Local correlation files | Used; exposes private helper | Supporting |
| Exposure | `exposure/fx_legs.py` | Parse FX pair and decompose trade legs | two contracts and three functions | Decimal; models | Used by aggregation and examples | Essential |
| Exposure | `exposure/aggregation.py` | Aggregate symbol/currency/cluster exposure | four engines and exposure functions | Models/config; FX-leg helpers | Used by governor and agent facade | Essential |
| Exposure | `exposure/__init__.py` | Exposure facade | all exposure exports | Local exposure files | Used; exposes private resolvers | Supporting |
| Sizing | `sizing/contracts.py` | Sizing requests/results/evidence/metadata | eight contracts/enums | Pydantic; Decimal; models | Used by calculators/tools/governor | Essential |
| Sizing | `sizing/normalization.py` | Broker-volume normalization and validation | four functions | Decimal; sizing contracts | Used by calculators | Essential |
| Sizing | `sizing/calculators.py` | Position-size algorithms | engine and ten calculation functions | Decimal/math; models/config; normalization | Used by governor and tools | Essential |
| Sizing | `sizing/__init__.py` | Sizing facade | all sizing exports | Local sizing files | Used | Supporting |
| Tail risk | `tail_risk/contracts.py` | VaR/ES request and result contracts | seven symbols | Pydantic; Decimal; models | Used by VaR/ES engines | Supporting |
| Tail risk | `tail_risk/var.py` | Covariance, VaR and risk-contribution calculations | engine and 14 functions | Numeric support; contracts/models | Used by governor/tools | Essential |
| Tail risk | `tail_risk/expected_shortfall.py` | ES calculation and tail selection | engine and three functions | Numeric support; contracts/models | Used by governor/tools | Essential |
| Tail risk | `tail_risk/__init__.py` | Facade plus compatibility orchestration wrappers | `calculate_portfolio_var`, `calculate_var_es_snapshots` | Local tail-risk files; models; logger | Used; executable logic in initializer | Useful |
| Stress | `stress/contracts.py` | Scenario/context/projected-portfolio contracts | four models | Pydantic; Decimal; models | Used by registry/engine | Supporting |
| Stress | `stress/registry.py` | Scenario registration and default catalogue | registry and four functions | Local contracts | Used by governor/tools | Essential |
| Stress | `stress/engine.py` | Apply shocks and aggregate results | engine, projected portfolio and four functions | Models/policy/contracts | Used by governor/tools | Essential |
| Stress | `stress/__init__.py` | Facade plus many legacy scenario wrappers | compatibility aliases/functions | Local stress files; policy/models/logger | Used by governor; many wrappers unconfirmed | Useful |
| Feasibility | `feasibility/drawdown.py` | Drawdown metrics, state and throttle persistence | governor/state models and 12 functions | Models/config/storage | Used in limits/governor/examples | Essential |
| Feasibility | `feasibility/margin.py` | Margin, leverage and exit-liquidity checks | four models/engine and 13 functions | Models/config | Used by governor and limits | Essential |
| Feasibility | `feasibility/execution_gate.py` | Broker-constraint, spread, slippage, stop and frequency feasibility | models/engine and 18 functions | Models/config | Used after ordered limits | Essential |
| Feasibility | `feasibility/__init__.py` | Feasibility facade | all feasibility exports | Local feasibility files | Used | Supporting |
| Limits | `limits/contracts.py` | Typed limit registry/result contracts and precedence | constants/types/models | Pydantic; models/policy | Used by checks/engine | Essential |
| Limits | `limits/checks.py` | Individual deterministic checks | kill-switch, freshness, loss, session, exposure, tail, leverage, margin and execution checks | Models; policy; feasibility | Used by engine/governor | Essential |
| Limits | `limits/engine.py` | Ordered registry and decision aggregation | registries, `LimitEngine`, run/evaluate helpers | Local checks/contracts | Used by governor and agent facade | Essential |
| Limits | `limits/__init__.py` | Limits facade | all limit symbols | Local limits files | Used | Supporting |
| Governance | `governance/allocation.py` | Risk-budget allocation and review | contracts, allocator and 14 functions | Models/config/policy/correlation | Used by governor/tools | Useful |
| Governance | `governance/kill_switch.py` | Scope-based halt state and controlled resume | manager/service/models and functions | Stdlib locking/state; models/storage | Used by governor and tools | Essential |
| Governance | `governance/lifecycle.py` | Strategy stage/admission/live-readiness reviews | states/reviews and functions | Models/config/policy | Used by agent facade/governor | Useful |
| Governance | `governance/__init__.py` | Governance facade | allocation, kill-switch and lifecycle symbols | Local governance files | Used | Supporting |
| Governor | `governor/decision_synthesis.py` | Pure aggregation of gate outcomes and reductions | three contracts and four functions | Models/enums | Unit-tested; runtime caller not confirmed in inspected governor path | Useful |
| Governor | `governor/governor.py` | Main orchestration and persistence | `RiskGovernor`, aliases and wrappers | Nearly all risk modules; Utils | Used by official tools | Essential |
| Governor | `governor/__init__.py` | Governor facade and compatibility re-exports | governor, synthesis and engine aliases | Many local risk modules | Used; unusually broad | Supporting |
| Observability | `observability/metrics.py` | In-process risk metrics registry | `RISK_METRICS_REGISTRY` and metrics support | Stdlib; Utils | Used by governor/reports | Useful |
| Observability | `observability/decorators.py` | Instrument public operations | `risk_observed` | Stdlib; metrics | Used on governor methods | Supporting |
| Observability | `observability/__init__.py` | Observability facade | metrics/decorator exports | Local observability files | Used internally | Supporting |
| Reports | `reports/builder.py` | Build/redact risk reports and summaries | report models/builder/functions | Models; observability | Used by tools | Useful |
| Reports | `reports/exporter.py` | Authorized file export | path/receipt models and write functions | Stdlib filesystem; security/normalization | Used when report path supplied | Useful |
| Reports | `reports/__init__.py` | Reports facade | builder/exporter/metrics exports | Local reports and observability | Used | Supporting |
| Readiness | `readiness/readiness.py` | Validate implementation/delivery mode matrices and build dry-run report | six models and four functions | Pydantic; models | Usage-example evidence only | Questionable |
| Readiness | `readiness/__init__.py` | Readiness facade | all readiness exports | Local readiness file | Test/example-only evidence | Questionable |
| Tools | `tools/official.py` | Typed official Risk tool boundary and shared in-memory backend | requests, payloads, 11 tools, singleton store/governor | Pydantic; governor; config; models; calculations | Used by agent facade | Essential |
| Tools | `tools/registry.py` | Approved tool metadata catalogue and validation | definitions/registry and four functions | Pydantic; models; validations | Registry builds 11 tools; external registration unconfirmed | Useful |
| Tools | `tools/__init__.py` | Official tool facade | requests/payloads/tool functions/registry | Local tool files | Used | Supporting |
| Root | `__init__.py` | Package-wide compatibility facade | 376 names | All domain subpackages | Used heavily; excessively broad | Supporting |
| Root | `README.md` | Human documentation | None | N/A | Documentation only | Useful |

## 5. Public Behaviour Inventory

The tables below enumerate the public symbols by defining file. Contract classes are treated as public data behavior. Inherited Pydantic methods are not counted as domain-specific public methods. Exact signatures are shown for the principal runtime boundary; support symbol inputs/outputs are summarized from code and exported contracts.

### `contracts.py`

**File responsibility:** A separate risk boundary-contract family.

| Symbol | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
|---|---|---|---|---|---|---|---|---|---|
| `Contract` | Class | Base traceable/canonical contract | model fields; `to_json() -> str`; `content_hash() -> str`; `contract_hash() -> str`; `check_compatibility(str) -> bool` | None | `ValidationError`, Pydantic validation errors | No confirmed non-test caller | Not confirmed | Possibly used | Questionable |
| `RiskRejection` | Class | Boundary rejection details | code, severity, reason, evidence → model | None | Pydantic validation errors | No confirmed caller | Not confirmed | Possibly used | Questionable |
| `PositionSizingResult` | Class | Boundary sizing result using floats | requested/approved size, method, constraints, contribution → model | None | Pydantic validation errors | No confirmed caller | Not confirmed | Possibly used | Questionable |
| `RiskDecision` | Class | Boolean approval/rejection plus optional Trading `OrderIntent` | signal/approval/sizing/rejection/order-intent → model | None | consistency `ValueError` | No confirmed caller | Not confirmed | Possibly used | Questionable |
| `RiskAuditEvent` | Class | Boundary audit event | decision/policy/action/hash/severity → model | None | Pydantic validation errors | No confirmed caller | Not confirmed | Possibly used | Questionable |

### `errors.py` and `validations.py`

| Symbol(s) | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
|---|---|---|---|---|---|---|---|---|---|
| `ErrorPayload`, `RISK_ERROR_CODES`, `ERROR_MESSAGES` | Type/constants | Stable boundary error vocabulary | N/A | None | None | Error-boundary support | Not confirmed | Supporting | Supporting |
| `to_risk_error_payload(exception, request_id=None)` | Function | Redact and map exception | exception → `{code, details}` | Log write | None expected | No use found in `tools/official.py`; that file has its own mapper | Not confirmed | Possibly used | Useful |
| `RiskError` and specialized errors | Classes | Typed domain failures with stable codes | message/code → exception | None | N/A | Used throughout calculations/governor | Representative governor tests | Used | Supporting |
| `ValidationResult` | TypedDict | Validation result schema | fields → mapping | None | None | Tool registry | Tool metadata tests expected | Used | Supporting |
| `_ok()`, `_fail(...)` | Functions | Build validation mappings | values → `ValidationResult` | None | None | `tools/registry.py` | Registry tests expected | Used but private and exported | Supporting |

### `models/contracts.py`, `models/enums.py`, `models/serialization.py`

| Symbol group | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
|---|---|---|---|---|---|---|---|---|---|
| `RiskContract`, sub-configs and `RiskConfig` | Classes | Finite Decimal-safe config/contracts | typed fields → validated models/hashes | None | Pydantic/domain validation | Config, policy, tools, governor | Model/config tests | Used | Essential |
| `ProposedTrade`, `ProposedAllocation`, `StrategyAdmissionRequest`, `RiskAssessmentRequest`, `LiveReadinessRequest`, `PositionSizingRequest` | Classes | Public request boundary | typed proposal/state/evidence → validated request | Local state mutation only through callers | Validation errors | Agent facade, official tools, governor | Governor/usage tests | Used | Essential |
| `PortfolioState`, `PositionState`, snapshot contracts | Classes | Current risk evidence/state | typed financial state → model | None | Validation errors | Calculators/governor/tools | Broad unit tests | Used | Essential |
| `RiskDecisionPackage`, `RiskDecisionToken`, `RiskApprovalToken`, `RiskAuditEvent` | Classes | Decision, approval and audit outputs | typed values → canonical models | None | Validation errors | Governor/audit/tools | Governor/audit tests | Used | Essential |
| `RiskBudget`, `RiskBudgetUtilization`, `RiskPolicyProfile`, policy models | Classes | Budget/policy evidence | typed values → model | None | Validation errors | Policy/allocation | Policy/allocation tests | Used | Useful |
| `StressScenario`, `StressScenarioResult`, `Correlation*`, `CurrencyExposure*`, `VaRSnapshot`, `ExpectedShortfallSnapshot` | Classes | Calculation evidence/results | typed values → model | None | Validation errors | Calculation engines/governor | Component tests | Used | Essential |
| `RiskDecisionStatus`, `RiskMode`, `RiskAction`, `RiskSeverity`, `RiskReasonCode`, kill-switch enums | Enums | Stable decision vocabulary | enum values | None | `ValueError` on invalid conversion | Entire domain | Broad tests | Used | Essential |
| `list_risk_reason_codes()`, `risk_severity_rank()` | Functions | Enumerate/rank catalog values | enum/input → list/int | None | Invalid input errors | Internal/support; exact runtime caller unconfirmed | Enum tests expected | Possibly used | Useful |
| `create_risk_decision_package(...)` | Function | Construct canonical decision | IDs/status/hash/reason/flags/volume/details → `RiskDecisionPackage` | None | Validation errors | Agent facade | Usage/tool tests | Used | Useful |
| `validate_risk_assessment_request(...)` | Function | Validate assessment request | request → validation result/validated request | None | Validation errors | Internal caller unconfirmed | Model tests expected | Possibly used | Supporting |
| `to_canonical_risk_payload`, `from_canonical_risk_payload`, `validate_risk_model_round_trip` | Functions | JSON-safe conversion and verification | model/payload → mapping/model/result | None | Validation errors | Usage examples | Serialization tests | Test-only confirmed | Useful |

### `config/*`

| Symbol group | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
|---|---|---|---|---|---|---|---|---|---|
| Five `MAX_*` constants | Constants | Hard global ceilings | N/A | None | None | Schema validation | Config tests | Used | Essential |
| `validate_risk_config(config)` | Function | Validate config and ceilings | `RiskConfig` → validation mapping | None | Validation/domain errors depending caller | Loader/policy/agent | Config tests | Used | Essential |
| Profile builders/get/list | Functions | Produce built-in profiles | no args/name → `RiskConfig`/names | None | `KeyError`/validation | Loader | Config tests | Used | Essential |
| `RiskConfigLoader`, `RiskProfileRegistry`, `RiskConfigHash` | Classes | Load/register/profile/hash support | profile/path/overrides → config/hash | File read for JSON | File/config errors | Agent tools and policy | Config tests | Used | Essential |
| `load_risk_config(profile_name, ...)` | Function | Main config entry point | profile/options → `RiskConfig` | File read/cache/local registry access | Validation/file errors | Agent facade, official tools, governor support | Config/tool tests | Used | Essential |
| `APPROVED_OVERRIDE_KEYS` | Constant | Allowed config override keys | N/A | None | None | Loader | Config tests | Used | Supporting |
| `_registry` | Constant/object | Module-global profile registry | N/A | Local state mutation | Registry errors | Loader internal; publicly exported | Tests likely | Used internally | Supporting |
| Hash/canonicalize/compare/validate functions | Functions | Stable config identity and compatibility | config(s)/hash → hash/comparison/result | None | Validation errors | Tokens/examples | Config tests | Used | Essential |

### `storage/*`

| Symbol group | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
|---|---|---|---|---|---|---|---|---|---|
| `RiskStateStore`, `RiskAuditSink`, `RiskPolicyStore`, `RiskDecisionStore` | Interfaces | Inject storage capabilities into governor | abstract operations | Persistence write/read by implementations | Storage errors | `RiskGovernor` | Storage/governor tests | Used | Essential |
| Idempotency/persistence contracts and helpers | Models/functions | Hash decision material, persist and enforce live audit support | decision/store/schema → result | Persistence write | Storage/schema errors | Governor/storage paths | Storage tests | Used or supporting | Supporting |
| `InMemoryRiskStateStore` | Class | Process-local implementation of all ports | store operations → records/states | Local state mutation | Storage errors | Official tools and tests | Governor/storage tests | Used | Useful |
| `create_in_memory_risk_store()` | Function | Factory | none → store | Local state allocation | None | Caller unconfirmed | Storage tests | Test-only/possibly used | Supporting |
| `FailingStore`, `StorageOperation`, `simulate_storage_failure()` | Test utilities | Exercise storage failures | operation → test double/failure | Local state mutation | Intentional storage errors | No production caller found | Storage tests | Test-only | No demonstrated production value |

### `audit/*`

| Symbol group | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
|---|---|---|---|---|---|---|---|---|---|
| Audit context/redaction/canonical payload functions | Models/functions | Build secret-safe canonical event material | decision/action/context → mapping | None | Validation/redaction errors | Event creation | Audit tests | Used | Essential |
| `create_risk_audit_event(...)` | Function | Append decision event | decision/action/sink → event | Persistence write | Storage/audit errors | Governor on all decisions | Governor/audit tests | Used | Essential |
| Hash-chain functions and `AuditChainVerification` | Functions/model | Build, append and validate chain | events/sink/hash → hash/result | Read-only or persistence write | Chain errors | Governor live pre-check | Audit/governor tests | Used | Essential |
| Token signer interfaces/context/results | Classes | Signing and validation abstraction | token material/context → signature/result | None | Token errors | Token functions | Audit tests | Used | Essential |
| Token create/validate/revoke/expiry/scope functions | Functions | Govern approval and execution tokens | decision/config/scope/token → token/result | Local/persistence token-state mutation for revoke/consume | Token/config/scope errors | Governor and official validation tool | Audit/tool tests | Used | Essential |

### `policy/*`

| Symbol group | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
|---|---|---|---|---|---|---|---|---|---|
| Policy contracts | Classes | Define scoped rules, effective config and overrides | fields → validated models | None | Validation errors | Resolver/governor/stress | Policy tests | Used | Essential |
| `RiskPolicyEngine` and resolve functions | Class/functions | Apply scoped precedence and produce effective policy | base config/rules/context → effective policy | None | Policy/config errors | Governor | Governor/policy tests | Used | Essential |
| `evaluate_risk_budget()` | Function | Check request against resolved policy budget | policy/request → result | None | Validation errors | Usage examples; possible governor support | Policy tests | Test-only confirmed | Useful |
| Override functions | Functions | Decide approval need and validate token/config compatibility | request/policy/token/hash → result | None | Validation errors | Policy facade/examples | Policy tests | Used/supporting | Useful |
| `PolicyVersion`, `PolicyBundle`, `PolicyResolutionQuery`, `PolicyOverrideRequest` | Classes | Compatibility/API metadata | fields → models | None | Validation errors | No confirmed non-test caller | Policy tests uncertain | Possibly used | Questionable |
| `load_risk_policy`, `validate_risk_policy`, `check_policy_permission` | Functions | Compatibility wrappers and role gate | profile/config/role/action/env → config/None/bool | Config file read; log write | Validation errors | Agent facade; governor override path | Tool/governor tests | Used | Useful |
| `validate_override_token`, `validate_risk_budget_gates` | Functions | Compatibility validation | token/scope/hash or budget/config → bool | Log write | Usually returns false | No confirmed runtime caller | Policy tests likely | Possibly used | Questionable |

### `regime/*`

| Symbol group | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
|---|---|---|---|---|---|---|---|---|---|
| Regime enums/threshold models | Enums/models | Classify market conditions and thresholds | values → enum/model | None | Validation errors | Assessor/governor | Regime tests | Used | Supporting |
| `classify_spread_regime`, `classify_volatility_regime`, `is_rollover_blackout`, `validate_market_freshness` | Functions | Individual classification checks | snapshot/context/thresholds → regime/bool/result | None | Validation errors | `assess_risk_regime` and examples | Regime tests | Used | Essential |
| `validate_regime_inputs`, `build_regime_reason_codes` | Functions | Validate evidence and create deterministic reasons | inputs/results → validation/reason codes | None | Validation errors | Assessor | Regime tests | Used | Supporting |
| `assess_risk_regime(...)` | Function | Aggregate spread, volatility, session, liquidity, news and rollover gate | typed snapshot/calendar/config/context → `RegimeAssessment` | None | Validation/data errors | Governor and agent tool | Governor/regime tests | Used | Essential |
| `RegimeRiskEngine` | Class | Object facade over assessment | context/config → result | None | Validation errors | Compatibility export; exact non-test instantiation unconfirmed | Tests likely | Possibly used | Useful |

### `correlation/*`

| Symbol group | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
|---|---|---|---|---|---|---|---|---|---|
| Contracts and `ReturnMethod`/`CorrelationMethod` | Models/enums | Typed returns, covariance, alignment and cluster evidence | fields → models | None | Validation errors | Engine | Correlation tests | Used | Supporting |
| `ReturnType` | Compatibility class | String constants for older return modes | N/A | None | None | Usage examples | Correlation tests | Test-only confirmed | Questionable |
| Return/alignment functions | Functions | Create and align price return series and Pearson correlation | bars/series/options → return series/Decimal | None | Insufficient-data/validation errors | Engine | Correlation tests | Used | Essential |
| Fallback functions | Functions | Resolve missing correlation conservatively | context/snapshot → snapshot/decision | None | Fail-closed errors | Engine/governor | Correlation tests | Used | Useful |
| Matrix/snapshot/cluster/impact functions | Functions | Main portfolio correlation analytics | market data/portfolio/trade/config → matrices, clusters, multipliers | None | Data/validation errors | Governor and agent facade | Correlation/governor tests | Used | Essential |
| `_get_symbol_gross_exposure()` | Private function exported publicly | Internal symbol exposure helper | symbol/volume/price/context/currency → Decimal | None | Data errors | Governor imports it directly | Governor tests | Used internally | Supporting |
| `CorrelationEngine` | Class | Compatibility/object facade | config/requests → results | None | Data/validation errors | Re-exported by governor; direct instantiation unconfirmed | Tests likely | Possibly used | Useful |

### `exposure/*`

| Symbol group | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
|---|---|---|---|---|---|---|---|---|---|
| `ContractSpecification`, `FxPair` | Models | Broker-neutral FX metadata and parsed pair | fields/symbol → models | None | Validation errors | FX decomposition | Exposure tests | Used | Supporting |
| `parse_fx_symbol`, `decompose_fx_trade`, `validate_currency_conversion_requirements` | Functions | Parse and split FX trades into currency legs | symbol/trade/spec/context → pair/legs/result | None | Missing conversion/invalid symbol errors | Aggregator and examples | Exposure tests | Used | Essential |
| Aggregation functions | Functions | Aggregate legs, gross/net, projected and hidden concentration | portfolio/trade/config/context → exposures/snapshot | None | Data/validation errors | Governor and agent facade | Exposure/governor tests | Used | Essential |
| Four exposure engine classes | Classes | Object facades for calculations | state/context → exposures | None | Data/validation errors | Re-exported; exact direct callers unconfirmed | Tests likely | Possibly used | Useful |
| `_resolve_base_quote`, `_resolve_conversion_rate` | Private functions exported publicly | Internal metadata/conversion lookup | values/context → currencies/rate | None | Missing conversion errors | Aggregation internal | Exposure tests | Used internally | Supporting |

### `sizing/*`

| Symbol group | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
|---|---|---|---|---|---|---|---|---|---|
| Sizing contracts/enums/evidence models | Models/enums | Define methods and sizing evidence | fields → models | None | Validation errors | Calculators/governor/tools | Sizing tests | Used | Essential |
| Volume normalization functions | Functions | Apply min/max/step and reject invalid volume | raw volume/metadata → normalized result/rejection | None | Validation errors | Calculators | Sizing tests | Used | Essential |
| Fixed-risk/fractional/volatility/correlation/milestone/Kelly functions | Functions | Compute candidate volume | request/state/context/config → result/Decimal | None | Missing stop/volatility/evidence errors | Main calculator and examples | Sizing tests | Used | Essential |
| `calculate_position_size(request, portfolio_state, market_context, config)` | Function | Dispatch selected method, apply reductions and normalize | typed request/state/context/config → `PositionSizingResult` | None | Domain validation errors | Governor and official tool | Governor/sizing/tool tests | Used | Essential |
| `VolatilitySizingEngine` | Class | Compatibility/object sizing facade | config/request → result | None | Validation errors | Usage example; governor facade export | Sizing class tests | Test-only confirmed | Useful |

### `tail_risk/*`

| Symbol group | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
|---|---|---|---|---|---|---|---|---|---|
| VaR/ES request/result/method contracts | Models/enums | Typed tail-risk inputs/results | state/history/options → models | None | Validation errors | Engines/wrappers | VaR/ES tests | Used | Supporting |
| Covariance/volatility/contribution functions | Functions | Build and validate covariance and risk contributions | returns/weights/options → matrices/Decimals | None | Data/validation errors | VaR calculations | VaR tests | Used | Essential |
| Parametric/historical VaR functions | Functions | Calculate VaR and optional ES | request → snapshot/result | None | Insufficient data/assumption errors | Wrapper/governor | VaR tests | Used | Essential |
| ES functions | Functions | Select tail losses and calculate expected shortfall | request/losses → result | None | Insufficient data/validation errors | Wrapper/governor/agent facade | ES tests | Used | Essential |
| `calculate_var_es_snapshots(...)` | Function | Build VaR and ES requests and run chosen methods | portfolio, trade, market context, options → `(VaRSnapshot, ExpectedShortfallSnapshot)` | Log write | Conversion/data errors | Governor and snapshot tool | Governor/tool tests | Used | Essential |
| `calculate_portfolio_var(...)` | Function | Compatibility wrapper returning VaR amount | state/context/config/trade/options → Decimal | Log write | Tail-risk errors | Agent facade | Tool tests | Used | Useful |
| `PortfolioVaREngine`, `ExpectedShortfallEngine` | Classes | Compatibility/object facades | request/config → result | None | Tail-risk errors | Re-exported; direct caller unconfirmed | Component tests | Possibly used | Useful |

### `stress/*`

| Symbol group | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
|---|---|---|---|---|---|---|---|---|---|
| Stress contracts | Models | Scenario, context, projection and summary | fields → models | None | Validation errors | Registry/engine | Stress tests | Used | Supporting |
| Registry functions/class | Class/functions | Register, retrieve, validate and build defaults | scenario/registry → registry/scenario | Local registry mutation | Duplicate/invalid scenario errors | Governor/tools | Stress tests | Used | Essential |
| Engine/functions | Class/functions | Apply shocks, calculate loss, compare policy and aggregate scenarios | context/registry/policy → summary/results | None | Data/validation errors | Governor/tools | Stress tests | Used | Essential |
| `build_default_scenario_registry`, `validate_custom_scenario`, `run_stress_scenario_analysis` | Compatibility functions | Legacy aliases/orchestration | config/state/context → registry/scenario/results | Log write | Stress errors | Governor uses default alias; agent facade uses official tool | Stress/tool tests | Used | Useful |
| Scenario-specific `evaluate_*_shock` functions | Compatibility functions | Build one scenario and evaluate it | portfolio/trade/context/config → result | Log write | Stress errors | No non-test caller found | Stress/usage tests likely | Test-only/possibly used | Questionable |
| Compatibility scenario classes (`PriceShockScenario`, `USDShockScenario`, etc.) | Classes/aliases | Preserve older namespace | constructor fields → scenario | None | Validation errors | Usage imports one alias | Stress tests/examples | Test-only confirmed | Questionable |

### `feasibility/*`

| Symbol group | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
|---|---|---|---|---|---|---|---|---|---|
| Drawdown calculations/state functions | Functions | Calculate daily/total/strategy drawdown, state and multiplier | state/history/config → Decimal/state/result | None | Validation errors | Governor/limits/examples | Drawdown tests | Used | Essential |
| `persist_drawdown_state`, `restore_drawdown_state` | Functions | Save/load throttling state | store/key/state → result/state | Persistence write/read | Storage errors | Governor support; direct caller unconfirmed | Drawdown/storage tests | Possibly used | Useful |
| `DrawdownGovernor`, state models | Class/models | Object/state facade | config/state → result | Possible persistence through supplied store | Validation/storage errors | Re-exported; direct caller unconfirmed | Drawdown tests | Possibly used | Useful |
| Margin calculations/checks | Functions | Margin requirement, free margin, leverage, utilization and exit liquidity | state/trade/context/config → Decimal/snapshot/result | None | Validation/data errors | Governor and limits | Margin/governor tests | Used | Essential |
| `MarginRiskEngine` and margin models | Class/models | Object facade and typed evidence | config/inputs → results | None | Validation errors | Governor facade; direct instantiation unconfirmed | Margin tests | Possibly used | Useful |
| Execution feasibility checks | Functions | Validate spread, slippage, stop/freeze, lot, volume, frequency, holding time and costs | state/trade/context/config → booleans/results | None | Validation/data errors | `ExecutionRiskGate` and limits | Execution-gate tests | Used | Essential |
| `ExecutionRiskGate.check_execution_feasibility(...)` | Public method | Aggregate final broker-neutral feasibility | state/trade/context → `ExecutionFeasibilityResult` | None | Validation errors | Governor after ordered limits | Governor/execution tests | Used | Essential |
| `ExecutionRiskGate`, policies and snapshot/result models | Class/models | Object gate and typed constraints | config/fields → gate/results | None | Validation errors | Governor/tools | Tests | Used | Essential |

### `limits/*`

| Symbol group | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
|---|---|---|---|---|---|---|---|---|---|
| Registry constants/types/models | Constants/types/models | Define ordered checks, precedence and results | N/A/fields → models | None | Validation errors | Engine/governor | Limits tests | Used | Essential |
| Individual `check_*` functions | Functions | Evaluate one deterministic limit | typed context or V1 request/config → `LimitResult`/status | None | Validation/data errors | Ordered registry/engine | Limits tests | Used | Essential |
| `run_limit_checks(request, config)` / `check_risk_limits(...)` | Functions | Run V1 ordered limit pipeline | assessment/config → status/reason/message/flags/results or result list | None | Validation errors | Governor and agent facade | Governor/limits tests | Used | Essential |
| `evaluate_ordered_limits`, `select_primary_failure`, `build_composite_breach_flags` | Functions | Pure typed aggregation | limit context/results → assessment/failure/flags | None | Validation errors | Decision-synthesis-compatible surface; runtime use partly unconfirmed | Limits tests | Possibly used | Useful |
| `LimitEngine` | Class | Object facade over checks | config/request → assessment | None | Validation errors | Re-exported; direct instantiation unconfirmed | Limits tests | Possibly used | Useful |

### `governance/*`

| Symbol group | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
|---|---|---|---|---|---|---|---|---|---|
| Allocation contracts/method enum | Models/enums | Typed allocation plans/reviews | fields → models | None | Validation errors | Allocator/governor/tools | Allocation tests | Used | Supporting |
| Allocation calculation/adjustment functions | Functions | Equal risk, volatility parity, correlation and regime/drawdown adjustments | budgets/evidence/config → allocations | None | Validation errors | `verify_allocation_limits`/examples | Allocation tests | Used | Useful |
| `verify_allocation_limits(...)` / `review_allocation_proposal(...)` | Functions | Decide allocation proposal | state/allocation/context/config → assessment/review | None | Validation errors | Governor | Governor/allocation tests | Used | Useful |
| `RiskAllocator` | Class | Object facade | config/request → plan/review | None | Validation errors | Governor facade; direct caller unconfirmed | Allocation tests | Possibly used | Useful |
| Kill-switch models/classes | Models/classes | Store scoped active/inactive halt state | trigger/query/resume requests → state/assessment | Local/persistence state mutation | Permission/state/storage errors | Governor/tools/tests | Kill-switch tests | Used | Essential |
| `KillSwitchManager.trigger()`, `.is_blocked()` | Public methods | Mutate/query scope state | scope/target/reason/actor → state/bool | Local/persistence mutation/read | State/storage errors | Governor and agent facade | Governor/kill-switch tests | Used | Essential |
| Trigger/query/resume helper functions | Functions | Compatibility/service APIs | requests/scope → assessment/state | Local/persistence state mutation | Permission/state errors | Tool check; mutation caller unconfirmed | Kill-switch tests | Mixed | Useful |
| Lifecycle states/review contracts | Models/enums | Define stage progression and evidence | fields → models | None | Validation errors | Lifecycle functions/tools | Lifecycle tests | Used | Supporting |
| Lifecycle evaluation/review functions | Functions | Validate stage transition, admission and live readiness | strategy/stage/evidence/context/config → review | None | Validation errors | Agent facade/governor wrappers | Lifecycle/tool tests | Used | Useful |

### `governor/*`

| Symbol | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
|---|---|---|---|---|---|---|---|---|---|
| `RiskGovernor.__init__(state_store, audit_sink, policy_store, decision_store, kill_switch_manager=None)` | Method | Inject ports and manager | dependencies → instance | Local state assignment | None | Official tools and tests | `test_governor.py` | Used | Essential |
| `RiskGovernor.review_trade(request, operator_role=None, approval_token=None)` | Method | Observed delegate | `RiskAssessmentRequest` → `RiskDecisionPackage` | Persistence, audit, metrics through delegate | Domain/storage errors | Official tool | Governor tests | Used | Essential |
| `RiskGovernor.review_trade_risk(...)` | Method | Full pre-trade risk pipeline | request/role/token → decision | Mutates request volume temporarily; persistence write; audit write; metrics; possible kill-switch mutation | Validation, data, storage/token errors | `review_trade`; static wrapper | Governor tests | Used | Essential |
| `RiskGovernor.review_allocation()` / `.review_allocation_proposal()` | Methods | Resolve policy and review allocation | request → decision | Persistence/audit writes | Validation/storage errors | Official tool | Governor/allocation tests | Used | Useful |
| `RiskGovernor.review_strategy_admission()` | Method | Check backtest evidence thresholds | request → decision | Persistence/audit writes | Validation/storage errors | Official tool | Governor/lifecycle tests | Used | Useful |
| Other public governor review/sweep methods | Methods | Live readiness, mode promotion and portfolio sweep | requests/context → decisions/reviews | Persistence/audit/metrics depending path | Domain/storage errors | Wrapper/tool paths | Tests expected | Used/possibly used | Useful |
| Module-level `review_*`, `run_*` functions | Functions | Compatibility entry points | models/context → decision/review | Same as constructed governor path | Domain/storage errors | Root facade/examples; exact non-test caller varies | Governor tests | Mixed | Useful |
| `RiskGovernorDecision` | Alias | Compatibility alias for `RiskDecisionPackage` | N/A | None | None | Root facade | Tests | Possibly used | Questionable |
| Synthesis contracts/functions | Models/functions | Pure precedence, primary reason and reduction aggregation | gate results/context → status/reason/decision | None | Validation errors | Tests; inspected governor path does not call `synthesize_decision` | `test_decision_synthesis.py` | Test-only confirmed | Useful |

### `observability/*`

| Symbol group | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
|---|---|---|---|---|---|---|---|---|---|
| `RISK_METRICS_REGISTRY` | Module-global object | Store counters/gauges/histograms | `.record(...)` calls | Local state mutation | Metric errors | Governor, reports | Observability via governor tests | Used | Useful |
| `risk_observed(operation, registry)` | Decorator | Record operation outcomes/latency | function → wrapped function | Metrics mutation | Re-raises wrapped errors | Governor methods | Governor tests | Used | Supporting |

### `reports/*`

| Symbol group | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
|---|---|---|---|---|---|---|---|---|---|
| Report models/builder | Classes | Typed report structure and builder | evidence/options → report | None | Validation/report errors | Official report tool | Report/tool tests | Used | Useful |
| `build_portfolio_risk_snapshot`, `build_risk_decision_summary`, `generate_risk_report`, `redact_risk_report` | Functions | Build and sanitize reports | state/decisions/options → snapshot/summary/report | None | Validation/report errors | Official tool/root facade | Report tests | Used | Useful |
| Export path/receipt models and validation | Models/functions | Authorize destination and receipt | path/report → authorized path/receipt | File path inspection | Security/validation errors | `write_risk_report` | Report tests | Used | Supporting |
| `write_risk_report(...)` | Function | Write authorized report | report/path → receipt | Persistence write (local file) | File/security errors | Official report tool when path supplied | Report/tool tests | Used | Useful |

### `readiness/*`

| Symbol group | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
|---|---|---|---|---|---|---|---|---|---|
| Readiness models | Classes | Describe delivery dependencies/mode matrices | fields → models | None | Validation errors | Usage script | Readiness tests not confirmed | Test-only confirmed | Questionable |
| Build/validate functions | Functions | Validate package delivery plan rather than trading risk | plans/matrices/manifests → assessment/report | None | Validation errors | Usage script | Tests not confirmed | Test-only confirmed | Questionable |

### `tools/official.py` and `tools/registry.py`

| Symbol group | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
|---|---|---|---|---|---|---|---|---|---|
| Tool request contracts | Classes | Typed input for 11 tools | typed fields → request | None | Validation errors | Agent facade | Tool tests | Used | Supporting |
| Tool payloads and `ToolResponse`/`ToolError` | Classes | Typed success/error envelope | result/error/metadata → response | None | Validation errors | Official tools/agent facade | Tool tests | Used | Essential |
| `_shared_store`, `_shared_governor` | Module globals | Default process-wide backend | import-time construction | Local state allocation/mutation | Constructor errors | Agent facade and all official mutating tools | Tool tests | Used | Useful |
| `build_portfolio_risk_snapshot_tool(request)` | Function | Calculate exposure, drawdown, VaR and stress summary | request → `ToolResponse[RiskSnapshotPayload]` | Read-only; metrics in metadata | Converts errors to response | Agent facade | Tool tests | Used | Useful |
| `review_trade_risk_tool(request)` | Function | Invoke shared governor | request → decision payload response | Local persistence/audit/metrics | Converts errors to response | Agent facade | Tool/governor tests | Used | Essential |
| `calculate_position_size_tool`, `assess_risk_regime_tool`, `run_risk_scenario_analysis_tool` | Functions | Calculation/read-only tools | typed request → payload response | None | Converts errors to response | Agent facade | Tool tests | Used | Useful |
| `review_strategy_admission_tool`, `review_allocation_proposal_tool`, `run_portfolio_risk_governor_tool` | Functions | Mutating governance reviews | request → decision payload response | Local persistence/audit/metrics | Converts errors to response | Agent facade | Tool tests | Used | Useful |
| `validate_risk_approval_token_tool`, `check_risk_kill_switch_tool` | Functions | Read token/switch state | request → payload response | Read-only | Converts errors to response | Agent facade | Tool tests | Used | Useful |
| `generate_risk_report_tool` | Function | Generate and optionally export report | request → report payload response | Optional local file write | Converts errors to response | Agent facade | Tool/report tests | Used | Useful |
| `RiskToolDefinition`, `RiskToolRegistry` | Classes | Tool metadata and catalogue | fields → models | None | Validation errors | Registry builder | Registry tests expected | Used | Useful |
| Registry functions | Functions | Build 11 entries, validate side-effect metadata, list/get | definition/registry/name → validation/registry/definition | None | `ValueError`, `KeyError` | No confirmed external registration caller | Tool tests | Possibly used | Useful |

### `__init__.py` facades

All 19 subpackage initializers and the root initializer are public namespace surfaces. Most are import-only. Exceptions with substantive behavior are:

* `correlation/__init__.py`: defines `ReturnType`.
* `policy/__init__.py`: defines four Pydantic models and five compatibility functions.
* `stress/__init__.py`: defines legacy registry aliases and scenario-specific evaluation wrappers.
* `tail_risk/__init__.py`: implements `calculate_portfolio_var()` and `calculate_var_es_snapshots()`.
* `governor/__init__.py`: imports many engine classes solely for compatibility.
* Root `__init__.py`: re-exports 376 names.

Side effects are generally import-time module/global construction. `tools/official.py`, imported by the root facade, constructs `_shared_store` and `_shared_governor` at import time.

## 6. Actual Workflows

### `V1-WF-RISK-001` — Pre-Trade Risk Decision

* **Scope:** Cross-domain
* **Trigger:** `app.agentic.tools.risk.review_trade_risk(...)` or direct official-tool call.
* **Input boundary:** Dictionaries converted to `ProposedTrade`, `PortfolioState`, and `TradeRiskReviewToolRequest`.
* **Functions and methods used:**
  * `review_trade_risk_tool()`
  * `_shared_governor.review_trade()`
  * `RiskGovernor.review_trade_risk()`
  * `resolve_policy()`
  * `verify_risk_audit_chain()`
  * `assess_risk_regime()`
  * correlation functions when `market_data` exists
  * `calculate_position_size()` when `sizing_request` exists
  * `calculate_var_es_snapshots()`
  * default stress registry and evaluation
  * `run_limit_checks()`
  * `ExecutionRiskGate.check_execution_feasibility()`
  * token creation, decision save and audit event creation
* **Files involved:** `app/agentic/tools/risk.py`; `tools/official.py`; `governor/governor.py`; policy, audit, regime, correlation, sizing, tail-risk, stress, limits, feasibility, storage and models files.
* **External dependencies:** Pydantic and shared Utils. No broker call.
* **Output boundary:** `RiskDecisionPayload`/dictionary containing status, reason, decision ID and breaches. Full stored decision contains calculated volume, details and token signature.
* **Failure behaviour:**
  * Invalid boundary inputs return tool error envelopes.
  * Policy, audit-chain and regime failures produce persisted block/reject decisions.
  * Audit-chain failure in live mode triggers the global kill switch.
  * Correlation, sizing, VaR/ES and stress exceptions are logged and may be skipped rather than always blocking.
  * A mock `approval_token_valid=True` context can override a rejection without a parsed token.
* **Operational status:** **Partial** — implemented and tested, but no confirmed handoff to Trading execution and some internal calculation failures are fail-open.
* **Evidence:**

```text
Agent request
→ app.agentic.tools.risk.review_trade_risk()
→ TradeRiskReviewToolRequest
→ review_trade_risk_tool()
→ _shared_governor.review_trade()
→ RiskGovernor.review_trade_risk()
→ policy resolution
→ audit-chain check
→ market regime gate
→ optional correlation and sizing
→ VaR/ES and stress
→ ordered limits
→ execution feasibility
→ decision token
→ InMemoryRiskStateStore + audit event
→ response
```

### `V1-WF-RISK-002` — Portfolio Risk Snapshot

* **Scope:** Cross-domain
* **Trigger:** Agent tool `build_portfolio_risk_snapshot()`.
* **Input boundary:** Portfolio state, market context and profile.
* **Sequence:** Agent wrapper → `PortfolioRiskSnapshotToolRequest` → `build_portfolio_risk_snapshot_tool()` → VaR/ES, stress, drawdown and gross exposure → payload.
* **External dependencies:** None beyond local models/calculations.
* **Output boundary:** Read-only risk snapshot payload.
* **Failure behaviour:** Top-level failures return an error envelope. VaR and stress sub-failures are caught and replaced with `0.0`.
* **Operational status:** **Partial** — callable, but zero substitution can represent missing evidence as no risk.
* **Evidence:**

```text
portfolio + market context
→ calculate_var_es_snapshots()
→ default stress scenarios
→ drawdown and gross exposure
→ RiskSnapshotPayload
```

### `V1-WF-RISK-003` — Position Sizing

* **Scope:** Cross-domain
* **Trigger:** Agent tool or governor sizing request.
* **Input boundary:** `PositionSizingRequest`, portfolio state, symbol metadata/market context and config.
* **Sequence:** Method dispatch → fixed/volatility/correlation/milestone/Kelly calculation → reductions → broker-volume normalization → result/rejection.
* **External dependencies:** No broker calls; broker constraints are supplied evidence.
* **Output boundary:** `PositionSizingResult`/`PositionSizingPayload`.
* **Failure behaviour:** Invalid stop, volatility evidence, metadata or normalized volume raises/returns structured rejection.
* **Operational status:** **Working** as a calculation service.
* **Evidence:**

```text
sizing request
→ calculate_position_size()
→ method calculator
→ normalize_volume()
→ validated calculated volume
```

### `V1-WF-RISK-004` — Allocation Review

* **Scope:** Internal review exposed cross-domain
* **Trigger:** Agent/official allocation tool or governor wrapper.
* **Input boundary:** `ProposedAllocation`, portfolio state and config.
* **Sequence:** Resolve policy → `verify_allocation_limits()` → build decision → save decision → audit.
* **External dependencies:** In-memory store in official-tool path.
* **Output boundary:** Approve/reject decision. It does not apply the allocation.
* **Failure behaviour:** Invalid action type raises validation error; tool converts to error envelope.
* **Operational status:** **Working** as a review-only workflow.
* **Evidence:**

```text
allocation proposal
→ RiskGovernor.review_allocation_proposal()
→ resolve_policy()
→ verify_allocation_limits()
→ persisted/audited decision
```

### `V1-WF-RISK-005` — Strategy Admission and Live Readiness Review

* **Scope:** Cross-domain review
* **Trigger:** `review_strategy_admission()` or `review_live_readiness()`.
* **Input boundary:** Strategy evidence, target stage, context and config.
* **Sequence:** Validate lifecycle/admission evidence → compare trade count, Sharpe, drawdown and stage requirements → return review/decision.
* **External dependencies:** None.
* **Output boundary:** Review/decision only. No strategy activation or stage mutation.
* **Failure behaviour:** Missing/invalid evidence rejects or returns validation error.
* **Operational status:** **Working** as advisory governance; downstream stage application not confirmed.
* **Evidence:**

```text
strategy evidence / proposed stage
→ lifecycle or governor review
→ threshold checks
→ review decision
```

### `V1-WF-RISK-006` — Kill-Switch State and Automatic Halt

* **Scope:** Internal and cross-domain
* **Trigger:** Manual helper/service calls, status tool, or live audit-chain failure.
* **Input boundary:** Scope, target, reason, actor, and optional resume approval.
* **Sequence:** Query/trigger manager → persist manager state → governor/limit checks read state.
* **External dependencies:** Store/file behavior inside manager was not fully inspected; no broker call.
* **Output boundary:** Blocked state/assessment. Risk itself does not cancel broker orders.
* **Failure behaviour:** Unauthorized/invalid resume remains blocked.
* **Operational status:** **Partial** — state governance works, but confirmed Trading enforcement/cancellation caller was not found.
* **Evidence:**

```text
audit-chain failure or operator request
→ KillSwitchManager.trigger()
→ active scoped state
→ limits/governor block future approvals
```

### `V1-WF-RISK-007` — Tail-Risk, Stress, Correlation and Exposure Analysis

* **Scope:** Internal calculations exposed cross-domain
* **Trigger:** Governor preprocessing or individual agent tools/examples.
* **Input boundary:** Portfolio, proposed trade, market histories and config.
* **Sequence:** Returns/alignment → correlations/clusters; FX leg decomposition → exposure; covariance → VaR/ES; registered scenario shocks → worst loss.
* **External dependencies:** Numeric libraries and supplied data only.
* **Output boundary:** Snapshots/matrices/exposures/stress results.
* **Failure behaviour:** Native functions raise data/validation errors. Governor catches several and continues.
* **Operational status:** **Working** individually; **Partial** when used inside governor because missing results may be skipped.
* **Evidence:**

```text
portfolio + market evidence
→ correlation/exposure/tail-risk/stress engines
→ typed metrics
→ limits and decision details
```

### `V1-WF-RISK-008` — Decision Token and Audit Chain

* **Scope:** Internal
* **Trigger:** Final approve/reduce decision or explicit validation tool.
* **Input boundary:** Decision IDs, action, config hash, scope and policy hash.
* **Sequence:** Sign token → store signature/details → create canonical redacted audit event → append chain → later validate signature/expiry/scope/config.
* **External dependencies:** Hashing/signing implementation and storage port.
* **Output boundary:** Token/validation result and audit record.
* **Failure behaviour:** Invalid/expired/revoked/scope-mismatched tokens fail; live chain failure blocks and triggers kill switch.
* **Operational status:** **Working** in the current in-memory official-tool backend.
* **Evidence:**

```text
approved decision
→ create_risk_decision_token()
→ decision details
→ create_risk_audit_event()
→ chained audit sink
```

### `V1-WF-RISK-009` — Risk Report Generation and Export

* **Scope:** Cross-domain
* **Trigger:** Agent `generate_risk_report()`.
* **Input boundary:** Report type, request ID and optional authorized path.
* **Sequence:** Official report tool → report builder → optional export → agent wrapper reads shared store internals to calculate counts.
* **External dependencies:** Local filesystem when exporting.
* **Output boundary:** Report ID/path and summary dictionary.
* **Failure behaviour:** Tool error envelope on generation/write failure.
* **Operational status:** **Partial** — operational only over the current process-local shared store; wrapper accesses private store fields.
* **Evidence:**

```text
report request
→ generate_risk_report_tool()
→ report builder/exporter
→ app.agentic.tools.risk reads _decisions and _audit_events
→ report summary
```

### `V1-WF-RISK-010` — Delivery Readiness Dry Run

* **Scope:** Internal documentation/readiness utility
* **Trigger:** Usage example or direct call.
* **Input boundary:** Delivery plan, phase dependencies and mode matrix.
* **Sequence:** Validate plans/matrix → build dry-run report.
* **External dependencies:** None.
* **Output boundary:** Readiness report.
* **Failure behaviour:** Validation errors.
* **Operational status:** **Unverified** — no production caller found.
* **Evidence:**

```text
readiness manifest
→ validate_phase_dependencies()
→ validate_delivery_plan()
→ validate_risk_mode_matrix()
→ build_readiness_dry_run()
```

## 7. Usage and Caller Map

| Public symbol / surface | Called from | Call type | Runtime or test | Evidence |
|---|---|---|---|---|
| `load_risk_config` | `app/agentic/tools/risk.py`, `tools/official.py`, policy wrappers | Direct import/call | Runtime facade | Explicit imports and calls |
| `load_risk_policy`, `validate_risk_policy` | `app/agentic/tools/risk.py` | Direct alias/call | Runtime facade | Agent tool functions |
| `calculate_currency_exposure` | Agent facade and governor | Direct call | Runtime | Agent tool and decision detail construction |
| `calculate_correlation_matrix` | Agent facade | Direct call | Runtime | Agent calculation tool |
| Correlation snapshot/cluster helpers | `RiskGovernor.review_trade_risk` | Dynamic local import/call | Runtime | Governor preprocessing |
| `calculate_position_size` | Official position-size tool and governor | Direct call | Runtime | Tool and governor |
| `calculate_portfolio_var`, `calculate_expected_shortfall` | Agent facade | Direct call | Runtime | Agent calculation tools |
| `calculate_var_es_snapshots` | Governor and snapshot tool | Direct call | Runtime | Tail-risk preprocessing |
| Stress default registry/evaluation | Governor and official scenario tool | Direct call | Runtime | Stress preprocessing/tool |
| `check_risk_limits` | Agent facade | Direct call | Runtime | Standalone check tool |
| `run_limit_checks` | Governor | Direct call | Runtime | Main decision workflow |
| `assess_risk_regime` | Governor and official regime tool | Direct call | Runtime | Regime gate |
| `ExecutionRiskGate.check_execution_feasibility` | Governor | Instance method call | Runtime | Final feasibility gate |
| `RiskGovernor` | `tools/official.py`, unit tests | Instantiation | Runtime and test | Shared singleton and test stores |
| `RiskGovernor.review_trade` | `review_trade_risk_tool` | Method call | Runtime | Official tool |
| `RiskGovernor.review_trade_risk` | `review_trade`, unit tests | Method call | Runtime and test | Main pipeline |
| Allocation/admission governor methods | Official tools | Method call | Runtime | Governance tool paths |
| `create_risk_audit_event` | Governor | Direct call | Runtime | Every persisted decision path |
| `verify_risk_audit_chain` | Governor | Direct call | Runtime | Live pre-check and health metric |
| `create_risk_decision_token` | Governor | Direct call | Runtime | Approve/reduce decisions |
| `validate_risk_approval_token` | Governor and official validation tool | Direct call | Runtime | Override/token tool |
| `get_kill_switch_manager` | Governor, agent facade, tests | Direct call | Runtime and test | Default manager/status |
| `RiskToolDefinition`/registry builder | Tool registry | Construction | Internal runtime support | 11 metadata definitions |
| Official tool functions | `app/agentic/tools/risk.py` | Direct local import/call | Runtime facade | Confirmed agent caller |
| Root package exports | `tests/risk/usage/05_risk.py` | Bulk import | Example | 20+ examples |
| Readiness functions | `tests/risk/usage/05_risk.py` | Direct call/import | Example only | Usage script |
| Serialization helpers | `tests/risk/usage/05_risk.py` | Direct call | Example only | Usage script |
| `RiskGovernor`, stores, models | `tests/risk/unit/test_governor.py` | Direct instantiation/call | Test | Unit test |
| `SimpleBacktestEngine` risk surface | None | No import/call | Runtime gap | `app/services/simulator/engine.py` imports Data and Strategy, not Risk |

## 8. Cross-Domain Surface

### Outbound — this domain depends on

| Depends on | Symbols or capabilities consumed | Where used in this domain | Evidence |
|---|---|---|---|
| `app.utils.logger` | Structured logging | Policy, stress, tail risk, governor, errors and other modules | Direct imports |
| `app.utils.normalization` | UTC time and datetime parsing | Policy, governor, contracts | Direct imports |
| `app.utils.standard` | Canonical JSON, stable IDs, sensitive-key pattern | Contracts, governor, agent boundary support | Direct imports |
| `app.utils.security` | Redaction | `errors.py`, report/audit paths | Direct import in errors |
| Pydantic | Validation contracts | Models, policy, tools, contracts, readiness | Direct imports |
| Standard library | Decimal, hashing, time, datetime, JSON, pathlib, locking, typing | Entire package | Direct imports |
| Numeric stack | Matrix/returns/covariance calculations | Correlation and tail-risk files | Capability implied by actual calculation modules; exact imports not fully inspected |
| Trading contracts | `OrderIntent` type only | `app/services/risk/contracts.py` under `TYPE_CHECKING` | No runtime import |
| Local filesystem | Config JSON read and optional report export | Config loader and reports exporter | Confirmed capability |
| Broker/exchange API | None | N/A | Feasibility consumes supplied snapshots; no broker call observed |

### Inbound — other packages depend on this domain

| Consuming package | Symbols consumed | Purpose | Evidence |
|---|---|---|---|
| `app/agentic/tools/risk.py` | Config, models, policy, correlation, exposure, limits, tail risk, lifecycle, official tools and shared backend | Expose standardized agent-callable risk operations | Confirmed direct imports/calls |
| `tests/risk/unit/` | Governor, models, stores, kill switch and component functions | Unit verification | Representative test inspected |
| `tests/risk/usage/05_risk.py` | Large root facade and component imports | Demonstration/examples | Confirmed file |
| `app/services/simulator/engine.py` | None | Simulator currently executes strategy intents without Risk | Confirmed negative dependency |
| Trading/UI/API packages | No confirmed current call path | Intended consumers may exist, but not proven | Repository-wide indexed search unavailable |

## 9. Duplicate and Overlapping Behaviour

| Item A | Item B | Overlap | Evidence | Risk |
|---|---|---|---|---|
| `app/services/risk/contracts.py` | `app/services/risk/models/contracts.py` | Both define `RiskRejection`, `PositionSizingResult`, `RiskAuditEvent`; one defines boolean `RiskDecision`, the other operational `RiskDecisionPackage` | Actual class definitions and model exports | Divergent schemas with identical names can cause wrong imports and serialization incompatibility |
| `app/services/risk/tools/official.py` | `app/agentic/tools/risk.py` | Tool wrappers, validation, envelope conversion, live-sensitive checks and request mapping | Both files inspected | Two public surfaces can drift and produce different metadata/error behavior |
| `tools/official._exception_to_error_payload` | `errors.to_risk_error_payload` and Utils mapper used by agent facade | Exception mapping | Separate implementations | Redaction and error codes are inconsistent across boundaries |
| `policy/__init__.py` wrappers | `policy/resolver.py`, `policy/overrides.py`, `config/*` | Load/validate/resolve/override compatibility behavior | Package facade imports and local function definitions | Logic split between facade and implementation |
| `stress/__init__.py` wrappers | `stress/engine.py` and `stress/registry.py` | Registry aliases and scenario execution | Package initializer contains executable wrappers | Multiple entry points and legacy behavior increase maintenance burden |
| `tail_risk/__init__.py` wrappers | `tail_risk/var.py`, `expected_shortfall.py` | VaR/ES orchestration | Functions implemented in initializer over engines | Public behavior is hidden in package initialization |
| `ReturnType` | `ReturnMethod` | Two return-mode vocabularies | Correlation initializer/contracts | Compatibility ambiguity |
| Limits `check_spread_limit`, `check_slippage_limit`, `check_trade_frequency_limit`, `check_leverage_limit` | Feasibility functions with same names | Similar names at different abstraction levels | Both subpackage exports; history records prior naming collision | Wrong import can call a different contract/signature |
| Root `__init__.py` facade | Subpackage facades | Re-exports nearly all layers | 376-name `__all__` | Public API does not distinguish stable boundary from implementation detail |
| Module-global shared governor/store | Dependency-injected governor construction | Two lifecycle/state models | `tools/official.py` globals vs tests/custom construction | Different callers may observe different risk state |

## 10. Unused or Questionable Items

| Item | Finding | Searches performed | Confidence | Evidence |
|---|---|---|---|---|
| `app/services/risk/contracts.py` | No confirmed current non-test caller; overlaps canonical models | Root exports, agent caller, governor, official tools, simulator and tests inspected | Medium | Operational code imports `models`, not this contract family |
| Readiness package | Confirmed only in usage examples | Agent facade, official tools, governor and simulator inspected | Medium | `tests/risk/usage/05_risk.py` imports readiness symbols |
| `FailingStore`, `simulate_storage_failure` | Test utilities exported as production API | Storage facade, official tools, representative tests | High for production value within inspected paths | No runtime caller found; purpose is explicit failure simulation |
| `_registry` | Private global exported publicly | Config facade/root exports/callers | Medium | Name begins `_`; loader owns it |
| `_get_symbol_gross_exposure` | Private helper exported and imported by governor | Correlation facade and governor inspected | High | Direct private import in governor |
| `_resolve_base_quote`, `_resolve_conversion_rate` | Private helpers exported publicly | Exposure facade and callers inspected | Medium | Used internally; no external runtime caller found |
| `_ok`, `_fail` | Private validation constructors exported | `validations.py`, tool registry | High | Directly imported by registry; should be internal behavior, not public contract |
| Scenario-specific legacy shock wrappers | No confirmed production caller | Root/agent/governor/tools/usage inspected | Medium | Main workflow uses registry/engine, not each wrapper |
| `RiskGovernorDecision` alias | Compatibility alias with no distinct behavior | Governor/root exports/callers | Medium | Alias to `RiskDecisionPackage` |
| Decision-synthesis surface | Unit-tested but inspected main governor path performs its own synthesis | Governor implementation, exports, commit/test evidence | Medium | `synthesize_decision()` not observed in the main pipeline |
| Tool registry external registration | Registry can build metadata, but no confirmed app/agent registration call was found | Agent facade and official tools inspected | Low | Registry is exported; indexed search unavailable |
| 376-name root API | Many names have no confirmed external caller | Root facade, agent caller and examples inspected | Medium | Confirmed runtime consumer uses narrow direct imports; example imports broad facade |

No item above is declared dead code except test-only utilities whose purpose is explicit.

## 11. Incomplete or Disconnected Workflows

| Workflow / capability | Missing connection | Current impact | Evidence |
|---|---|---|---|
| Strategy/simulator intent → Risk → simulated execution | Simulator does not invoke Risk | Backtests can execute strategy intents without this risk governor | `app/services/simulator/engine.py` imports Data and Strategy only |
| Approved Risk decision → Trading execution | No confirmed Trading caller consumes `RiskDecisionPackage` or token | Risk approval exists, but end-to-end broker execution path is unverified | Only confirmed inbound runtime caller is agent facade |
| Kill switch → cancel/stop in-flight broker work | Risk stores block state but has no broker mutation | Stops future approval; does not prove active-order cancellation | Governance docstrings and no broker dependency |
| Lifecycle review → actual strategy-stage update | Review returns result only | Promotion governance can be disconnected from activation | Agent tool states it cannot change stages |
| Allocation review → apply capital allocation | Review persists decision only | Approved plan is not applied by Risk | Governor method behavior |
| Durable decision/audit history | Official tool backend is in-memory | State/report history is lost on process restart unless a custom backend is used | `_shared_store = InMemoryRiskStateStore()` |
| Portfolio snapshot evidence failure | VaR/stress exceptions replaced with zero | Missing calculations may appear low-risk | `build_portfolio_risk_snapshot_tool()` broad catches |
| Governor calculation failure | Correlation, sizing, VaR/ES and stress can be skipped | Final limits may run without intended evidence | Broad exception handlers in `review_trade_risk()` |
| Official registry → active agent registration | No confirmed registration call | Registry may document tools without enforcing actual exposure | Registry and agent facade inspected |
| README/test commands → current layout | README references older test path | Contributors may run incomplete/wrong test command | README vs current `tests/risk/...` files |

## 12. Structural Problems

| ID | Problem | Location | Impact | Evidence |
|---|---|---|---|---|
| `V1-ISSUE-RISK-001` | Excessive root public surface | `app/services/risk/__init__.py` | 376 names make compatibility helpers and internals appear stable | Actual `__all__` |
| `V1-ISSUE-RISK-002` | Duplicate contract families | `contracts.py` and `models/contracts.py` | Same names represent different schemas/types | Actual definitions/exports |
| `V1-ISSUE-RISK-003` | Duplicate tool layers | `tools/official.py`, `app/agentic/tools/risk.py` | Validation, metadata and error behavior can diverge | Confirmed call path |
| `V1-ISSUE-RISK-004` | Three error-mapping paths | `errors.py`, `tools/official.py`, agent facade/Utils | Redaction and stable codes are inconsistent | Direct implementations/imports |
| `V1-ISSUE-RISK-005` | Runtime singleton uses in-memory persistence | `tools/official.py:_shared_store` | Process restart loses decisions, audit and report state | Module-global construction |
| `V1-ISSUE-RISK-006` | Private store internals accessed externally | `app/agentic/tools/risk.py:generate_risk_report` | Breaks encapsulation and couples report output to implementation | Reads `_decisions`, `_audit_events` |
| `V1-ISSUE-RISK-007` | Failed risk calculations may be treated as zero | `tools/official.py:build_portfolio_risk_snapshot_tool` | Understates risk and hides evidence failure | Broad catches assign `Decimal("0.0")` |
| `V1-ISSUE-RISK-008` | Governor skips failed correlation/tail/stress calculations | `governor/governor.py:RiskGovernor.review_trade_risk` | Decision can continue with incomplete evidence | Broad exception logging/continuation |
| `V1-ISSUE-RISK-009` | Reachable mock approval override | `RiskGovernor.review_trade_risk`, `market_context["approval_token_valid"]` | Caller-controlled context can approve rejected decision without parsed token | Explicit conditional path |
| `V1-ISSUE-RISK-010` | Input model is temporarily mutated | `request.proposed_action.volume` in governor | Exception before restoration can leak changed request state | Volume assigned then restored late |
| `V1-ISSUE-RISK-011` | Compatibility logic lives in package initializers | policy, stress and tail-risk `__init__.py` | Import surfaces contain substantive behavior and wrappers | Actual files |
| `V1-ISSUE-RISK-012` | Public private helpers/test doubles | config/correlation/exposure/validations/storage facades | Expands unsupported API and encourages coupling | `_registry`, `_get_*`, `_resolve_*`, `_ok`, `_fail`, `FailingStore` exports |
| `V1-ISSUE-RISK-013` | Duplicate check names across layers | `limits/checks.py` and `feasibility/*` | Ambiguous imports/signatures | Export lists and refactor history |
| `V1-ISSUE-RISK-014` | Simulator bypasses Risk | `app/services/simulator/engine.py` | Simulation does not exercise the same risk gate as intended execution | No Risk import/call |
| `V1-ISSUE-RISK-015` | No confirmed Trading consumer | Cross-domain boundary | End-to-end approval-to-execution is unverified | Available caller evidence |
| `V1-ISSUE-RISK-016` | Tool metadata registry may not govern actual agent facade | `tools/registry.py` vs `app/agentic/tools/risk.py` | Documented side-effect metadata may not be the active registration source | No confirmed registry consumption |
| `V1-ISSUE-RISK-017` | Strategy-admission agent wrapper creates dummy portfolio | `app/agentic/tools/risk.py:review_strategy_admission` | Review receives synthetic balance/equity rather than caller state | Hard-coded `PortfolioState` |
| `V1-ISSUE-RISK-018` | Agent wrapper duplicates live-sensitive validation but does not consistently use it | `app/agentic/tools/risk.py` and `tools/official.py` | Validation path depends on selected wrapper | Two helper definitions |
| `V1-ISSUE-RISK-019` | Path/documentation drift | README and tests | Audit/test execution can miss current suite | Current path is `tests/risk/...`; README shows older path |
| `V1-ISSUE-RISK-020` | Very broad governor responsibility | `governor/governor.py` | One method resolves policy, verifies audit, assesses regime, computes analytics, sizes, checks limits, creates tokens, persists, audits and records metrics | Inspected `review_trade_risk()` |

## 13. V1 Capability Catalogue

| Capability ID | Capability | Current implementation | Workflow(s) | Usage status | Value status | Notes |
|---|---|---|---|---|---|---|
| `V1-CAP-RISK-001` | Canonical risk contracts and enums | `models/contracts.py`, `models/enums.py` | All | Used | Essential | Operational contract family |
| `V1-CAP-RISK-002` | Config profiles, ceilings and hashes | `config/*`, `configs/*.json` | 001–007 | Used | Essential | Four concrete profiles |
| `V1-CAP-RISK-003` | Policy-as-code resolution | `policy/contracts.py`, `resolver.py`, `overrides.py` | 001, 004, 005 | Used | Essential | Main governor dependency |
| `V1-CAP-RISK-004` | Market regime gate | `regime/*` | 001 | Used | Essential | Spread, volatility, liquidity/session/news/rollover |
| `V1-CAP-RISK-005` | Position sizing | `sizing/*` | 001, 003 | Used | Essential | Multiple algorithms and broker normalization |
| `V1-CAP-RISK-006` | FX exposure | `exposure/*` | 001, 007 | Used | Essential | Leg decomposition and aggregation |
| `V1-CAP-RISK-007` | Correlation and cluster risk | `correlation/*` | 001, 007 | Used | Essential | Includes conservative fallback |
| `V1-CAP-RISK-008` | VaR and Expected Shortfall | `tail_risk/*` | 001, 002, 007 | Used | Essential | Parametric/historical support |
| `V1-CAP-RISK-009` | Stress scenarios | `stress/*` | 001, 002, 007 | Used | Essential | Registry-based plus compatibility wrappers |
| `V1-CAP-RISK-010` | Drawdown governance | `feasibility/drawdown.py` | 001 | Used | Essential | Metrics, states and throttling |
| `V1-CAP-RISK-011` | Margin and execution feasibility | `feasibility/margin.py`, `execution_gate.py` | 001 | Used | Essential | Broker-neutral supplied snapshots |
| `V1-CAP-RISK-012` | Ordered deterministic limits | `limits/*` | 001 | Used | Essential | 20+ checks and precedence |
| `V1-CAP-RISK-013` | Allocation review | `governance/allocation.py`, governor | 004 | Used | Useful | Review only |
| `V1-CAP-RISK-014` | Lifecycle/admission readiness review | `governance/lifecycle.py`, governor | 005 | Used | Useful | Does not activate strategy |
| `V1-CAP-RISK-015` | Kill switch | `governance/kill_switch.py` | 001, 006 | Used | Essential | No broker cancellation |
| `V1-CAP-RISK-016` | Decision orchestration | `governor/governor.py` | 001, 004, 005 | Used | Essential | Main domain workflow |
| `V1-CAP-RISK-017` | Pure decision synthesis | `governor/decision_synthesis.py` | None confirmed | Test-only confirmed | Useful | Parallel to manual governor synthesis |
| `V1-CAP-RISK-018` | Approval/decision tokens | `audit/tokens.py` | 001, 008 | Used | Essential | Scope/config/policy validation |
| `V1-CAP-RISK-019` | Audit hash chain | `audit/events.py`, `hash_chain.py` | 001, 008 | Used | Essential | Live failure triggers halt |
| `V1-CAP-RISK-020` | Storage abstraction | `storage/ports.py` | 001, 004, 008, 009 | Used | Essential | Runtime default is in-memory |
| `V1-CAP-RISK-021` | Risk reports and export | `reports/*` | 009 | Used | Useful | Depends on current store history |
| `V1-CAP-RISK-022` | Observability | `observability/*` | 001 | Used | Useful | In-process registry |
| `V1-CAP-RISK-023` | Official typed tools | `tools/official.py` | 001–009 | Used | Essential | Confirmed agent facade consumer |
| `V1-CAP-RISK-024` | Tool metadata registry | `tools/registry.py` | Tool exposure | Possibly used | Useful | External registration unconfirmed |
| `V1-CAP-RISK-025` | Delivery readiness utility | `readiness/*` | 010 | Test-only | Questionable | Not trading risk behavior |
| `V1-CAP-RISK-026` | Alternate boundary contracts | `contracts.py` | None confirmed | Possibly used | Questionable | Overlaps canonical models |
| `V1-CAP-RISK-027` | Legacy compatibility APIs | package initializers/root facade | Various | Mixed | Questionable | Significant public surface |

## 14. Audit Conclusions

### Valuable behavior worth preserving

The following behavior has demonstrated value through confirmed workflows and callers:

* Typed portfolio, proposal, policy, evidence, decision, token and audit contracts.
* Deterministic configuration loading, hard ceilings and stable config hashes.
* Scoped policy resolution.
* Regime, position-sizing, exposure, correlation, VaR/ES, stress, drawdown, margin and execution-feasibility calculations.
* Ordered limit evaluation.
* The main pre-trade decision workflow.
* Decision idempotency and collision detection.
* Decision/audit persistence through explicit ports.
* Cryptographic decision tokens and hash-chain verification.
* Kill-switch state that blocks approval.
* Read-only official calculation tools and typed tool envelopes.
* Allocation and lifecycle review behavior.
* Report generation and observability where their state source is valid.

### Behavior that exists but is disconnected

* The Risk decision is not proven to feed a current Trading execution service.
* The simulator does not call Risk before applying strategy intents.
* Kill-switch state is not proven to cancel in-flight broker work.
* Lifecycle and allocation reviews do not apply the approved change.
* Tool metadata registration is not proven to govern the active agent-tool facade.
* Readiness validation is demonstrated only by examples.
* The pure decision-synthesis module is tested but was not observed in the main governor decision path.

### Likely dead weight or questionable surface

No item is labelled dead code because repository-wide indexed search was unavailable. The strongest candidates for removal or manual confirmation in a later task are:

* The alternate `app/services/risk/contracts.py` family.
* Exported storage failure test doubles.
* Exported private helpers.
* Legacy scenario-specific wrappers.
* Compatibility aliases such as `RiskGovernorDecision` and `ReturnType`.
* Readiness delivery utilities inside the runtime risk package.
* Public engine re-exports that have no confirmed direct caller.
* The 376-name root facade.

### Duplicated responsibilities

* Canonical model contracts versus boundary contracts.
* Official risk tools versus agentic risk wrappers.
* Three exception-to-payload implementations.
* Compatibility policy/stress/tail-risk wrappers versus structured implementation files.
* Limits and feasibility functions with overlapping names.
* Module-global shared state versus caller-injected storage.

### Important uncertainties requiring manual confirmation

1. Whether a current Trading/UI/API package imports Risk dynamically or through configuration.
2. Whether the tool registry is consumed by an agent registration/bootstrap mechanism.
3. Whether a durable `RiskStateStore` implementation exists outside this package and is used in deployment.
4. Whether the mock approval shortcut is intentionally test-gated by deployment configuration.
5. Whether the alternate boundary contracts are consumed by an external package not visible to static retrieval.
6. Whether all current unit tests pass and what coverage they produce; tests were inspected, not executed.
7. Whether report export authorization prevents all unsafe destinations; exporter body was not fully inspected.
8. Whether kill-switch persistence is durable and process-safe in the deployed manager configuration.
9. Whether dynamic callbacks, string imports or framework registrations reference unconfirmed compatibility symbols.

### Final assessment

The package contains substantial, coherent risk-calculation and governance behavior, and its main governor is not merely placeholder code. However, the confirmed operational boundary currently ends at an agent-facing, in-memory review service. The largest risks to audit confidence and runtime correctness are the absent confirmed execution consumer, the simulator bypass, duplicate public surfaces, broad exception suppression, and the reachable mock override path.

No Version 2 requirements were created, no redesign was performed, and no repository code was changed.

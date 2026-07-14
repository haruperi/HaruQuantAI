# Risk — Version 1 Code Audit

## 1. Audit Scope

* **Domain:** risk
* **Repository:** `haruperi/HaruQuant`
* **Audited revision:** commit `a39d26498e14772c571d75fa9a5f0e477a1dd912`
* **Package path:** `app/services/risk`
* **Tests path supplied:** `ttests/unit/app/services/risk`
* **Tests path found:** `tests/unit/app/services/risk`
* **Usage examples supplied/found:** `tests/usage/app/services/05_risk.py` and `tests/usage/app/services/risk.py`
* **Files inspected:** all 180 Python paths found under `app/services/risk`, the package README, all package `__init__.py` registries, key implementation files, API/runtime callers, execution callers, simulator-session callers, and the available unit/usage test surfaces.
* **Related packages searched:** `app/api`, `app/api/session`, `app/services/execution`, `app/services/simulation`, `app/services/brokers`, `app/agentic`, `tests/unit/app/services/risk`, and `tests/usage/app/services`.
* **Generated/cached paths excluded:** caches, virtual environments, generated reports, database files, and unrelated services.
* **Audit limitations:**
  * The repository was inspected through the GitHub connector; a local authenticated checkout was not available.
  * Tests could not be executed. Test status is based on imports and static source inspection.
  * GitHub code search can miss reflective imports, runtime-composed strings, external consumers, or files outside the accessible revision.
  * Exact leaf-class names were not invented where connector responses only confirmed the file and package registry. Those entries are labelled at file/registry level.
  * “Unused” is used only where static imports/calls, registries, routes, scripts, tests, and examples were searched with no hit. Otherwise the status is “Possibly used” or “Unknown.”

### Evidence convention

Evidence is written as `path::symbol`. A conclusion is **confirmed** when the definition and caller were both inspected. A conclusion is **uncertain** when only a registry, file path, or static-search absence was available.

## 2. Executive Summary

The Version 1 risk package is not one cohesive implementation. It contains:

1. A **50-function root AI-tool facade** in `allocation_tools.py`, `governor_tools.py`, `lifecycle_tools.py`, and `portfolio_tools.py`.
2. A much larger **layered risk subsystem** covering canonical state models, portfolio VaR/ES, policy limits, governance, live safety, risk metrics, scorecards, stress scenarios, optimization recommendations, replay/what-if, reports, validation, and persistence.
3. Several **compatibility namespaces** that duplicate or forward the same concepts: `core` → canonical engines, `models` → `domain`, `simulation` → `replay`, and `safety` → governance kill-switch behavior.

The strongest operational workflows are:

* API position sizing, regime detection, allocation advice, and governance evaluation.
* Simulator-session risk refresh: state → metric snapshot → scorecard → recommendations → persistence.
* Simulator pre-trade governance before market or pending-order mutation.
* Simulator what-if/replay analysis.
* Live execution integration through `PortfolioManager` and `SafetyChecker`.
* Execution approval expiry/material-change checks and global new-entry kill-switch blocking.

The most important structural problems are:

* The root `__init__.py`, package README, nested `api` facade, and compatibility namespaces expose incompatible definitions of the public API.
* The supplied usage example and multiple unit tests target removed modules or a missing `app.agentic.tools.risk`, so they do not prove the current revision is runnable.
* Root “get” tools often calculate from or echo caller-supplied payloads rather than reading broker/database state.
* Root tool metadata always reports a read-only tool specification even when lifecycle names imply approval/revocation.
* `PositionSizer.calculate_size()` catches every exception and returns `0.1` lots, which can turn an input/provider failure into a non-zero trade size.
* Approval-token replay tracking is process-local, and token creation hard-codes account/broker identifiers.
* `app.services.execution.trade_action_governor` creates a fixed synthetic approval decision rather than invoking the canonical risk evaluator.
* Duplicate namespaces and compatibility wrappers make ownership and caller tracing difficult.

**Audit trustworthiness:** High for file boundaries, root exports, API/session/execution call paths, and the inspected canonical engines. Medium for leaf-module usage because dynamic consumers and unexecuted tests cannot be ruled out.

```text
Structural groups: 24 (package root + 23 subpackages) | Files: 180 | Root public tools: 50 | Declared package/subpackage export paths: approximately 270, including compatibility duplicates | Export names with confirmed external runtime imports: 35 (~13%) | Workflows found: 12
```

The approximately 270 figure counts names exposed through inspected `__all__`, wildcard compatibility registries, and nested public registries. It is not a count of unique implementations.

## 3. Actual Package Structure

```text
app/services/risk/
├── __init__.py
├── _common.py
├── allocation_tools.py
├── governor_tools.py
├── lifecycle_tools.py
├── portfolio_tools.py
├── api/
│   ├── __init__.py
│   └── public.py
├── calculations/
│   ├── __init__.py
│   ├── var.py
│   ├── cvar.py
│   ├── margin.py
│   ├── drawdown.py
│   ├── exposure.py
│   ├── math_utils.py
│   ├── correlation.py
│   └── position_sizing.py
├── config/
│   ├── __init__.py
│   └── thresholds.py
├── core/
│   ├── __init__.py
│   ├── governance_engine.py
│   ├── risk_snapshot_engine.py
│   ├── recommendation_engine.py
│   ├── risk_scorecard_engine.py
│   ├── portfolio_risk_engine.py
│   ├── timeline_reconstructor.py
│   └── portfolio_state_engine.py
├── domain/
│   ├── market.py
│   ├── events.py
│   ├── symbol.py
│   ├── account.py
│   ├── approval.py
│   ├── position.py
│   ├── proposal.py
│   ├── decision.py
│   ├── __init__.py
│   ├── snapshot.py
│   ├── portfolio.py
│   ├── contracts.py
│   └── exceptions.py
├── governance/
│   ├── audit.py
│   ├── __init__.py
│   ├── validity.py
│   ├── approval_tokens.py
│   ├── governance_engine.py
│   ├── decisions.py
│   ├── kill_switch_audit.py
│   ├── signatures.py
│   ├── governor.py
│   └── kill_switch.py
├── limits/
│   ├── models.py
│   ├── events.py
│   ├── __init__.py
│   ├── soft_limits.py
│   ├── hard_limits.py
│   ├── policy_engine.py
│   ├── pre_trade_checks.py
│   ├── circuit_breakers.py
│   └── post_trade_checks.py
├── live/
│   ├── run.py
│   ├── engine.py
│   ├── __init__.py
│   ├── safety_checks.py
│   ├── portfolio_manager.py
│   └── broker_risk.py
├── metrics/
│   ├── math.py
│   ├── base.py
│   ├── var_cvar.py
│   ├── registry.py
│   ├── __init__.py
│   ├── margin_risk.py
│   ├── symbol_risk.py
│   ├── stress_risk.py
│   ├── account_risk.py
│   ├── drawdown_risk.py
│   ├── strategy_risk.py
│   ├── concentration.py
│   ├── position_risk.py
│   ├── portfolio_risk.py
│   ├── volatility_risk.py
│   ├── correlation_risk.py
│   └── currency_exposure.py
├── models/
│   ├── __init__.py
│   ├── market_state.py
│   ├── symbol_state.py
│   ├── account_state.py
│   ├── position_state.py
│   └── portfolio_state.py
├── optimization/
│   ├── models.py
│   ├── __init__.py
│   ├── capital_efficiency.py
│   ├── rebalance_suggestions.py
│   ├── hedge_optimizer.py
│   ├── marginal_risk.py
│   ├── recommendation_engine.py
│   ├── allocation_optimizer.py
│   └── allocation_planner.py
├── policy/
│   ├── models.py
│   ├── resolver.py
│   ├── __init__.py
│   ├── pre_trade.py
│   ├── compliance.py
│   ├── restrictions.py
│   └── compliance_rollout.py
├── portfolio/
│   ├── impacts.py
│   ├── __init__.py
│   ├── snapshot_builder.py
│   ├── proposals.py
│   ├── enforcement.py
│   ├── contributions.py
│   ├── state_builder.py
│   └── snapshots.py
├── regimes/
│   ├── models.py
│   ├── engine.py
│   ├── __init__.py
│   ├── crisis_regime.py
│   ├── market_regime.py
│   ├── liquidity_regime.py
│   ├── volatility_regime.py
│   └── regime_transition.py
├── replay/
│   ├── clock.py
│   ├── models.py
│   ├── __init__.py
│   ├── cockpit_state.py
│   ├── replay_engine.py
│   ├── what_if_engine.py
│   ├── hypothetical_orders.py
│   └── timeline.py
├── reports/
│   ├── __init__.py
│   ├── json_export.py
│   ├── risk_report.py
│   ├── markdown_report.py
│   ├── summary_templates.py
│   ├── risk_report_builder.py
│   ├── replay_report_builder.py
│   └── scenario_report_builder.py
├── safety/
│   ├── audit.py
│   ├── __init__.py
│   └── kill_switch.py
├── scenarios/
│   ├── core.py
│   ├── models.py
│   ├── registry.py
│   └── __init__.py
├── scoring/
│   ├── base.py
│   ├── __init__.py
│   ├── registry.py
│   ├── margin_safety.py
│   ├── normalization.py
│   ├── leverage_safety.py
│   ├── stress_fragility.py
│   ├── portfolio_health.py
│   ├── scorecard_engine.py
│   ├── regime_alignment.py
│   ├── concentration_score.py
│   ├── overall_risk_quality.py
│   ├── diversification_score.py
│   └── governance_compliance.py
├── simulation/
│   ├── __init__.py
│   ├── replay_engine.py
│   ├── replay_models.py
│   ├── cockpit_state.py
│   ├── what_if_engine.py
│   ├── simulation_clock.py
│   └── hypothetical_orders.py
├── storage/
│   ├── schema.py
│   ├── __init__.py
│   ├── repositories.py
│   ├── snapshot_store.py
│   ├── decision_store.py
│   └── scenario_store.py
├── validators/
│   ├── limits.py
│   ├── __init__.py
│   ├── symbols.py
│   ├── account.py
│   ├── common.py
│   ├── validations.py
│   ├── market.py
│   └── positions.py
├── workflows/
│   ├── __init__.py
│   └── request_assembler.py
```

### Public surface summary

```text
app.services.risk
├── 50 root AI-callable functions
├── api: 3 lazy builder facades
├── domain/models: canonical and compatibility state/contract models
├── calculations/core/portfolio/metrics/scoring: quantitative engines
├── limits/policy/governance/safety: policy and approval controls
├── regimes/scenarios/optimization: detection, stress and advice
├── replay/simulation/reports: replay, what-if and presentation
├── storage: database persistence
├── live: broker-facing risk controls
└── validators/workflows: validation and request assembly
```

## 4. Module and File Inventory

Files are arranged from contracts/configuration and primitives toward orchestration, runtime adapters, persistence, and compatibility surfaces. The table still preserves the actual module location.

| Module | File | Responsibility | Key exports | Dependencies | Usage status | Value status |
| ------ | ---- | -------------- | ----------- | ------------ | ------------ | ------------ |
| `app.services.risk` | `__init__.py` | Package export/compatibility registry. | 50 root tools from allocation_tools, governor_tools, lifecycle_tools, portfolio_tools | Standard library: datetime, math, typing \| Required third-party: pandas in portfolio helpers \| Local: app.services.utils tool envelope/logger; risk._common | **Test-only** | **Questionable** |
| `app.services.risk` | `_common.py` | Common result-envelope and payload helpers for root AI-callable tools. | risk_business_payload; risk_limit_check; risk_live_module; risk_policy_module; risk_portfolio_module; risk_safety_module; risk_tool_context; risk_tool_result | Standard library: datetime, math, typing \| Required third-party: pandas in portfolio helpers \| Local: app.services.utils tool envelope/logger; risk._common | **Test-only** | **Supporting** |
| `app.services.risk` | `allocation_tools.py` | Stateless allocation and position-size tool facade. | calculate_correlation_adjusted_size; calculate_cost_adjusted_size; calculate_fixed_fractional_size; calculate_margin_aware_size; calculate_max_safe_position_size; calculate_risk_parity_weights; calculate_volatility_adjusted_size; propose_strategy_allocation; rebalance_strategy_allocations; validate_allocation_proposal | Standard library: datetime, math, typing \| Required third-party: pandas in portfolio helpers \| Local: app.services.utils tool envelope/logger; risk._common | **Test-only** | **Questionable** |
| `app.services.risk` | `governor_tools.py` | Stateless threshold-check tool facade and aggregate check runner. | check_correlation_limit; check_currency_exposure_limit; check_cvar_limit; check_daily_loss_limit; check_kill_switch_state; check_leverage_limit; check_margin_limit; check_max_drawdown_limit; check_news_blackout; check_portfolio_exposure_limit; check_slippage_limit; check_spread_limit; check_strategy_loss_limit; check_symbol_exposure_limit; check_trade_frequency_limit; check_var_limit; run_risk_governor_checks | Standard library: datetime, math, typing \| Required third-party: pandas in portfolio helpers \| Local: app.services.utils tool envelope/logger; risk._common | **Test-only** | **Questionable** |
| `app.services.risk` | `lifecycle_tools.py` | Strategy risk-profile and approval payload facade. | approve_strategy_for_live; approve_strategy_for_paper; create_strategy_risk_profile; get_strategy_risk_profile; list_strategy_risk_profiles; revoke_strategy_risk_approval; update_strategy_risk_limits; validate_strategy_risk_profile | Standard library: datetime, math, typing \| Required third-party: pandas in portfolio helpers \| Local: app.services.utils tool envelope/logger; risk._common | **Test-only** | **Questionable** |
| `app.services.risk` | `portfolio_tools.py` | Portfolio/account/symbol/strategy risk calculation and snapshot facade. | calculate_current_drawdown; calculate_current_margin_usage; calculate_currency_exposure; calculate_portfolio_cvar; calculate_portfolio_exposure; calculate_portfolio_var; calculate_strategy_exposure; calculate_symbol_exposure; get_account_risk_state; get_open_orders; get_open_positions; get_portfolio_risk_snapshot; get_strategy_risk_state; get_symbol_risk_state; get_total_risk_utilization | Standard library: datetime, math, typing \| Required third-party: pandas in portfolio helpers \| Local: app.services.utils tool envelope/logger; risk._common | **Test-only** | **Questionable** |
| `app.services.risk.api` | `__init__.py` | Package export/compatibility registry. | package exports | Standard library: importlib, typing \| Required third-party: none \| Local: portfolio/core/report builders | **Possibly used** | **Useful** |
| `app.services.risk.api` | `public.py` | Public behavior for the api subsystem. | PortfolioStateBuilder; RiskSnapshotBuilder; RiskReportBuilder | Standard library: importlib, typing \| Required third-party: none \| Local: portfolio/core/report builders | **Possibly used** | **Useful** |
| `app.services.risk.calculations` | `__init__.py` | Package export/compatibility registry. | none | Standard library: dataclasses, contextlib, typing \| Required third-party: numpy, pandas, scipy \| Local: limits, models, utils.logger | **Unknown** | **Questionable** |
| `app.services.risk.calculations` | `var.py` | Var behavior for the calculations subsystem. | historical_var; incremental_var | Standard library: dataclasses, contextlib, typing \| Required third-party: numpy, pandas, scipy \| Local: limits, models, utils.logger | **Supporting** | **Useful** |
| `app.services.risk.calculations` | `cvar.py` | Cvar behavior for the calculations subsystem. | historical_cvar; incremental_cvar | Standard library: dataclasses, contextlib, typing \| Required third-party: numpy, pandas, scipy \| Local: limits, models, utils.logger | **Supporting** | **Useful** |
| `app.services.risk.calculations` | `margin.py` | Margin behavior for the calculations subsystem. | MarginUtilization; VolatilityAdjustedSizing; DrawdownState; calculate_margin_utilization; calculate_volatility_adjusted_size; calculate_drawdown_state; margin_impact; margin_failures | Standard library: dataclasses, contextlib, typing \| Required third-party: numpy, pandas, scipy \| Local: limits, models, utils.logger | **Supporting** | **Useful** |
| `app.services.risk.calculations` | `drawdown.py` | Drawdown behavior for the calculations subsystem. | drawdown_state | Standard library: dataclasses, contextlib, typing \| Required third-party: numpy, pandas, scipy \| Local: limits, models, utils.logger | **Supporting** | **Useful** |
| `app.services.risk.calculations` | `exposure.py` | Exposure behavior for the calculations subsystem. | PositionExposure; ExposureSummary; ConcentrationResult; calculate_exposure_summary; calculate_symbol_concentration; calculate_currency_concentration; calculate_strategy_family_concentration; exposure_snapshot; proposed_exposure_impact; concentration_failures | Standard library: dataclasses, contextlib, typing \| Required third-party: numpy, pandas, scipy \| Local: limits, models, utils.logger | **Supporting** | **Useful** |
| `app.services.risk.calculations` | `math_utils.py` | Math utils behavior for the calculations subsystem. | stop_loss_distance; pip_value; proposed_trade_risk; notional_exposure; risk_reward_value | Standard library: dataclasses, contextlib, typing \| Required third-party: numpy, pandas, scipy \| Local: limits, models, utils.logger | **Supporting** | **Useful** |
| `app.services.risk.calculations` | `correlation.py` | Correlation behavior for the calculations subsystem. | CorrelationPair; CorrelationConcentration; DEFAULT_CLUSTERS; calculate_correlation_concentration; symbol_cluster; correlation_impact; correlation_failures | Standard library: dataclasses, contextlib, typing \| Required third-party: numpy, pandas, scipy \| Local: limits, models, utils.logger | **Supporting** | **Useful** |
| `app.services.risk.calculations` | `position_sizing.py` | Multi-method position sizing, symbol-volume validation, and optional ATR-backed stop-distance support. | PositionSizer; validate_position_size | Standard library: dataclasses, contextlib, typing \| Required third-party: numpy, pandas, scipy \| Local: limits, models, utils.logger | **Used** | **Essential** |
| `app.services.risk.config` | `__init__.py` | Package export/compatibility registry. | wildcard re-export of threshold configuration API | Standard library: hashlib, json, os, pathlib \| Required third-party: none \| Local: none | **Supporting** | **Supporting** |
| `app.services.risk.config` | `thresholds.py` | Load, validate, hash, and expose risk threshold configuration. | public definitions declared in `thresholds.py`; package-facing names are registered/re-exported by `config/__init__.py` where applicable | Standard library: hashlib, json, os, pathlib \| Required third-party: none \| Local: none | **Supporting** | **Supporting** |
| `app.services.risk.core` | `__init__.py` | Package export/compatibility registry. | GovernanceEngine; PortfolioRiskEngine; PortfolioStateEngine; RecommendationEngine; RiskScorecardEngine; RiskSnapshotEngine; TimelineReconstructor | Standard library: typing \| Required third-party: numpy, pandas, scipy \| Local: domain, limits, metrics, portfolio, scoring, optimization | **Used** | **Supporting** |
| `app.services.risk.core` | `governance_engine.py` | Canonical governance orchestration or a compatibility wrapper, depending on folder. | public definitions declared in `governance_engine.py`; package-facing names are registered/re-exported by `core/__init__.py` where applicable | Standard library: typing \| Required third-party: numpy, pandas, scipy \| Local: domain, limits, metrics, portfolio, scoring, optimization | **Used** | **Supporting** |
| `app.services.risk.core` | `risk_snapshot_engine.py` | Compatibility forwarding to canonical snapshot builder. | public definitions declared in `risk_snapshot_engine.py`; package-facing names are registered/re-exported by `core/__init__.py` where applicable | Standard library: typing \| Required third-party: numpy, pandas, scipy \| Local: domain, limits, metrics, portfolio, scoring, optimization | **Used** | **Supporting** |
| `app.services.risk.core` | `recommendation_engine.py` | Risk recommendation orchestration or compatibility forwarding. | public definitions declared in `recommendation_engine.py`; package-facing names are registered/re-exported by `core/__init__.py` where applicable | Standard library: typing \| Required third-party: numpy, pandas, scipy \| Local: domain, limits, metrics, portfolio, scoring, optimization | **Used** | **Supporting** |
| `app.services.risk.core` | `risk_scorecard_engine.py` | Risk scorecard orchestration or compatibility forwarding. | public definitions declared in `risk_scorecard_engine.py`; package-facing names are registered/re-exported by `core/__init__.py` where applicable | Standard library: typing \| Required third-party: numpy, pandas, scipy \| Local: domain, limits, metrics, portfolio, scoring, optimization | **Used** | **Supporting** |
| `app.services.risk.core` | `portfolio_risk_engine.py` | Portfolio VaR/ES, covariance, contribution, margin, cluster and broker-data calculations. | PortfolioRiskEngine | Standard library: typing \| Required third-party: numpy, pandas, scipy \| Local: domain, limits, metrics, portfolio, scoring, optimization | **Used** | **Essential** |
| `app.services.risk.core` | `timeline_reconstructor.py` | Rebuild risk timeline/state frames from persisted or simulated data. | public definitions declared in `timeline_reconstructor.py`; package-facing names are registered/re-exported by `core/__init__.py` where applicable | Standard library: typing \| Required third-party: numpy, pandas, scipy \| Local: domain, limits, metrics, portfolio, scoring, optimization | **Used** | **Supporting** |
| `app.services.risk.core` | `portfolio_state_engine.py` | Compatibility forwarding to canonical state builder. | public definitions declared in `portfolio_state_engine.py`; package-facing names are registered/re-exported by `core/__init__.py` where applicable | Standard library: typing \| Required third-party: numpy, pandas, scipy \| Local: domain, limits, metrics, portfolio, scoring, optimization | **Used** | **Supporting** |
| `app.services.risk.domain` | `market.py` | Market-state/snapshot model. | public definitions declared in `market.py`; package-facing names are registered/re-exported by `domain/__init__.py` where applicable | Standard library: dataclasses, datetime, enum, typing \| Required third-party: pydantic/pandas where declared \| Local: shared contracts/utilities | **Used** | **Supporting** |
| `app.services.risk.domain` | `events.py` | Risk/limit event models. | public definitions declared in `events.py`; package-facing names are registered/re-exported by `domain/__init__.py` where applicable | Standard library: dataclasses, datetime, enum, typing \| Required third-party: pydantic/pandas where declared \| Local: shared contracts/utilities | **Used** | **Supporting** |
| `app.services.risk.domain` | `symbol.py` | Symbol specification/state model. | public definitions declared in `symbol.py`; package-facing names are registered/re-exported by `domain/__init__.py` where applicable | Standard library: dataclasses, datetime, enum, typing \| Required third-party: pydantic/pandas where declared \| Local: shared contracts/utilities | **Used** | **Supporting** |
| `app.services.risk.domain` | `account.py` | Account state model. | public definitions declared in `account.py`; package-facing names are registered/re-exported by `domain/__init__.py` where applicable | Standard library: dataclasses, datetime, enum, typing \| Required third-party: pydantic/pandas where declared \| Local: shared contracts/utilities | **Used** | **Supporting** |
| `app.services.risk.domain` | `approval.py` | Approval token/approval model. | public definitions declared in `approval.py`; package-facing names are registered/re-exported by `domain/__init__.py` where applicable | Standard library: dataclasses, datetime, enum, typing \| Required third-party: pydantic/pandas where declared \| Local: shared contracts/utilities | **Used** | **Supporting** |
| `app.services.risk.domain` | `position.py` | Position state model. | public definitions declared in `position.py`; package-facing names are registered/re-exported by `domain/__init__.py` where applicable | Standard library: dataclasses, datetime, enum, typing \| Required third-party: pydantic/pandas where declared \| Local: shared contracts/utilities | **Used** | **Supporting** |
| `app.services.risk.domain` | `proposal.py` | Risk proposal model. | public definitions declared in `proposal.py`; package-facing names are registered/re-exported by `domain/__init__.py` where applicable | Standard library: dataclasses, datetime, enum, typing \| Required third-party: pydantic/pandas where declared \| Local: shared contracts/utilities | **Used** | **Supporting** |
| `app.services.risk.domain` | `decision.py` | Risk decision model. | public definitions declared in `decision.py`; package-facing names are registered/re-exported by `domain/__init__.py` where applicable | Standard library: dataclasses, datetime, enum, typing \| Required third-party: pydantic/pandas where declared \| Local: shared contracts/utilities | **Used** | **Supporting** |
| `app.services.risk.domain` | `__init__.py` | Package export/compatibility registry. | AccountSnapshot; AccountState; MarketSnapshot; MarketState; PortfolioSnapshot; PortfolioState; PositionState; RiskAssessmentRequest; RiskApprovalToken; RiskDecision; RiskDecisionStatus; RiskGovernorDecision; RiskMemo; RiskProposal; SymbolState | Standard library: dataclasses, datetime, enum, typing \| Required third-party: pydantic/pandas where declared \| Local: shared contracts/utilities | **Used** | **Supporting** |
| `app.services.risk.domain` | `snapshot.py` | Account/market/portfolio snapshot contracts. | public definitions declared in `snapshot.py`; package-facing names are registered/re-exported by `domain/__init__.py` where applicable | Standard library: dataclasses, datetime, enum, typing \| Required third-party: pydantic/pandas where declared \| Local: shared contracts/utilities | **Used** | **Supporting** |
| `app.services.risk.domain` | `portfolio.py` | Canonical portfolio state model. | public definitions declared in `portfolio.py`; package-facing names are registered/re-exported by `domain/__init__.py` where applicable | Standard library: dataclasses, datetime, enum, typing \| Required third-party: pydantic/pandas where declared \| Local: shared contracts/utilities | **Used** | **Supporting** |
| `app.services.risk.domain` | `contracts.py` | Legacy/canonical risk request, proposal, decision, memo and token contracts. | public definitions declared in `contracts.py`; package-facing names are registered/re-exported by `domain/__init__.py` where applicable | Standard library: dataclasses, datetime, enum, typing \| Required third-party: pydantic/pandas where declared \| Local: shared contracts/utilities | **Used** | **Supporting** |
| `app.services.risk.domain` | `exceptions.py` | Risk-specific exception hierarchy. | public definitions declared in `exceptions.py`; package-facing names are registered/re-exported by `domain/__init__.py` where applicable | Standard library: dataclasses, datetime, enum, typing \| Required third-party: pydantic/pandas where declared \| Local: shared contracts/utilities | **Used** | **Supporting** |
| `app.services.risk.governance` | `audit.py` | Risk audit record construction/persistence. | public definitions declared in `audit.py`; package-facing names are registered/re-exported by `governance/__init__.py` where applicable | Standard library: dataclasses, datetime, json, pathlib \| Required third-party: none \| Local: calculations, config, domain, limits, policy, governance.workflow | **Test-only** | **Useful** |
| `app.services.risk.governance` | `__init__.py` | Package export/compatibility registry. | package exports | Standard library: dataclasses, datetime, json, pathlib \| Required third-party: none \| Local: calculations, config, domain, limits, policy, governance.workflow | **Used** | **Supporting** |
| `app.services.risk.governance` | `validity.py` | Approval invalidation for proposal changes and expiry. | RiskDecisionValidity; invalidate_for_material_proposal_change; enforce_risk_decision_expiry | Standard library: dataclasses, datetime, json, pathlib \| Required third-party: none \| Local: calculations, config, domain, limits, policy, governance.workflow | **Used** | **Essential** |
| `app.services.risk.governance` | `approval_tokens.py` | Approval-token creation, expiry checks, proposal binding, and replay tracking. | USED_APPROVAL_SIGNATURES; create_approval_token; validate_approval_token | Standard library: dataclasses, datetime, json, pathlib \| Required third-party: none \| Local: calculations, config, domain, limits, policy, governance.workflow | **Test-only** | **Useful** |
| `app.services.risk.governance` | `governance_engine.py` | Canonical governance orchestration or a compatibility wrapper, depending on folder. | GovernanceReport; GovernanceEngine | Standard library: dataclasses, datetime, json, pathlib \| Required third-party: none \| Local: calculations, config, domain, limits, policy, governance.workflow | **Used** | **Essential** |
| `app.services.risk.governance` | `decisions.py` | Decision model/helper definitions. | public definitions declared in `decisions.py`; package-facing names are registered/re-exported by `governance/__init__.py` where applicable | Standard library: dataclasses, datetime, json, pathlib \| Required third-party: none \| Local: calculations, config, domain, limits, policy, governance.workflow | **Supporting** | **Supporting** |
| `app.services.risk.governance` | `kill_switch_audit.py` | Kill-switch audit recording. | public definitions declared in `kill_switch_audit.py`; package-facing names are registered/re-exported by `governance/__init__.py` where applicable | Standard library: dataclasses, datetime, json, pathlib \| Required third-party: none \| Local: calculations, config, domain, limits, policy, governance.workflow | **Test-only** | **Useful** |
| `app.services.risk.governance` | `signatures.py` | Stable hashing and signature helpers. | public definitions declared in `signatures.py`; package-facing names are registered/re-exported by `governance/__init__.py` where applicable | Standard library: dataclasses, datetime, json, pathlib \| Required third-party: none \| Local: calculations, config, domain, limits, policy, governance.workflow | **Test-only** | **Useful** |
| `app.services.risk.governance` | `governor.py` | Deterministic proposal policy evaluation, audit, decision signing, and approval-token issuance. | DEFAULT_RISK_THRESHOLDS; RiskGovernor; RiskGovernorDecision | Standard library: dataclasses, datetime, json, pathlib \| Required third-party: none \| Local: calculations, config, domain, limits, policy, governance.workflow | **Test-only** | **Useful** |
| `app.services.risk.governance` | `kill_switch.py` | Kill-switch state/evaluation logic or compatibility forwarding, depending on folder. | KillSwitchAction; RecoveryAuthorization; KillSwitchTransitionError; KillSwitchBlockEvaluation; RecoveryApproval; KillSwitchStateMachine; KillSwitchService; evaluate_new_entry_block; require_hard_trigger_recovery_dual_auth | Standard library: dataclasses, datetime, json, pathlib \| Required third-party: none \| Local: calculations, config, domain, limits, policy, governance.workflow | **Used** | **Essential** |
| `app.services.risk.limits` | `models.py` | Domain-specific value models. | RiskPolicy; RiskLimits; CorrelationPreference; OverrideRecord; CircuitBreakerState; BudgetUtilization; GovernanceState | Standard library: dataclasses, typing \| Required third-party: none \| Local: regimes and limit event models | **Used** | **Supporting** |
| `app.services.risk.limits` | `events.py` | Risk/limit event models. | public definitions declared in `events.py`; package-facing names are registered/re-exported by `limits/__init__.py` where applicable | Standard library: dataclasses, typing \| Required third-party: none \| Local: regimes and limit event models | **Used** | **Supporting** |
| `app.services.risk.limits` | `__init__.py` | Package export/compatibility registry. | package exports | Standard library: dataclasses, typing \| Required third-party: none \| Local: regimes and limit event models | **Used** | **Supporting** |
| `app.services.risk.limits` | `soft_limits.py` | Warning-level limit evaluation. | public definitions declared in `soft_limits.py`; package-facing names are registered/re-exported by `limits/__init__.py` where applicable | Standard library: dataclasses, typing \| Required third-party: none \| Local: regimes and limit event models | **Used** | **Supporting** |
| `app.services.risk.limits` | `hard_limits.py` | Blocking limit evaluation. | public definitions declared in `hard_limits.py`; package-facing names are registered/re-exported by `limits/__init__.py` where applicable | Standard library: dataclasses, typing \| Required third-party: none \| Local: regimes and limit event models | **Used** | **Supporting** |
| `app.services.risk.limits` | `policy_engine.py` | Pre/post-trade policy orchestration and stress-regime tightening. | PolicyEngine; as_policy | Standard library: dataclasses, typing \| Required third-party: none \| Local: regimes and limit event models | **Used** | **Essential** |
| `app.services.risk.limits` | `pre_trade_checks.py` | Pre-trade policy checks. | public definitions declared in `pre_trade_checks.py`; package-facing names are registered/re-exported by `limits/__init__.py` where applicable | Standard library: dataclasses, typing \| Required third-party: none \| Local: regimes and limit event models | **Used** | **Essential** |
| `app.services.risk.limits` | `circuit_breakers.py` | Circuit-breaker state transitions and escalation. | public definitions declared in `circuit_breakers.py`; package-facing names are registered/re-exported by `limits/__init__.py` where applicable | Standard library: dataclasses, typing \| Required third-party: none \| Local: regimes and limit event models | **Used** | **Supporting** |
| `app.services.risk.limits` | `post_trade_checks.py` | Post-trade/current-portfolio checks. | public definitions declared in `post_trade_checks.py`; package-facing names are registered/re-exported by `limits/__init__.py` where applicable | Standard library: dataclasses, typing \| Required third-party: none \| Local: regimes and limit event models | **Used** | **Essential** |
| `app.services.risk.live` | `run.py` | Standalone/live risk runner entry helper. | public definitions declared in `run.py`; package-facing names are registered/re-exported by `live/__init__.py` where applicable | Standard library: asyncio, dataclasses, typing \| Required third-party: pandas where declared \| Local: broker/MT5 adapters, calculations, governance, utils | **Possibly used** | **Useful** |
| `app.services.risk.live` | `engine.py` | Subsystem orchestration engine. | RiskIntegratedEngine | Standard library: asyncio, dataclasses, typing \| Required third-party: pandas where declared \| Local: broker/MT5 adapters, calculations, governance, utils | **Possibly used** | **Useful** |
| `app.services.risk.live` | `__init__.py` | Package export/compatibility registry. | package exports | Standard library: asyncio, dataclasses, typing \| Required third-party: pandas where declared \| Local: broker/MT5 adapters, calculations, governance, utils | **Used** | **Supporting** |
| `app.services.risk.live` | `safety_checks.py` | Live safety gate checks. | SafetyChecker | Standard library: asyncio, dataclasses, typing \| Required third-party: pandas where declared \| Local: broker/MT5 adapters, calculations, governance, utils | **Used** | **Essential** |
| `app.services.risk.live` | `portfolio_manager.py` | Live portfolio risk monitoring and risk-aware position management. | PortfolioManager | Standard library: asyncio, dataclasses, typing \| Required third-party: pandas where declared \| Local: broker/MT5 adapters, calculations, governance, utils | **Used** | **Essential** |
| `app.services.risk.live` | `broker_risk.py` | Translate broker state into risk state. | broker_risk_state | Standard library: asyncio, dataclasses, typing \| Required third-party: pandas where declared \| Local: broker/MT5 adapters, calculations, governance, utils | **Possibly used** | **Useful** |
| `app.services.risk.metrics` | `math.py` | Shared portfolio-risk mathematical routines. | public definitions declared in `math.py`; package-facing names are registered/re-exported by `metrics/__init__.py` where applicable | Standard library: abc, dataclasses, typing \| Required third-party: numpy, pandas, scipy \| Local: domain, limits, scenarios | **Used** | **Supporting** |
| `app.services.risk.metrics` | `base.py` | Base protocol/context/result models. | public definitions declared in `base.py`; package-facing names are registered/re-exported by `metrics/__init__.py` where applicable | Standard library: abc, dataclasses, typing \| Required third-party: numpy, pandas, scipy \| Local: domain, limits, scenarios | **Used** | **Supporting** |
| `app.services.risk.metrics` | `var_cvar.py` | VaR/CVaR metric-family implementation. | public definitions declared in `var_cvar.py`; package-facing names are registered/re-exported by `metrics/__init__.py` where applicable | Standard library: abc, dataclasses, typing \| Required third-party: numpy, pandas, scipy \| Local: domain, limits, scenarios | **Used** | **Supporting** |
| `app.services.risk.metrics` | `registry.py` | Register metric, score, or scenario implementations. | public definitions declared in `registry.py`; package-facing names are registered/re-exported by `metrics/__init__.py` where applicable | Standard library: abc, dataclasses, typing \| Required third-party: numpy, pandas, scipy \| Local: domain, limits, scenarios | **Used** | **Supporting** |
| `app.services.risk.metrics` | `__init__.py` | Package export/compatibility registry. | MetricContext; MetricFamily; MetricRegistry; MetricRow; RiskSnapshot; build_default_metric_registry | Standard library: abc, dataclasses, typing \| Required third-party: numpy, pandas, scipy \| Local: domain, limits, scenarios | **Used** | **Supporting** |
| `app.services.risk.metrics` | `margin_risk.py` | Margin-risk metric-family implementation. | public definitions declared in `margin_risk.py`; package-facing names are registered/re-exported by `metrics/__init__.py` where applicable | Standard library: abc, dataclasses, typing \| Required third-party: numpy, pandas, scipy \| Local: domain, limits, scenarios | **Used** | **Supporting** |
| `app.services.risk.metrics` | `symbol_risk.py` | Symbol-risk metric-family implementation. | public definitions declared in `symbol_risk.py`; package-facing names are registered/re-exported by `metrics/__init__.py` where applicable | Standard library: abc, dataclasses, typing \| Required third-party: numpy, pandas, scipy \| Local: domain, limits, scenarios | **Used** | **Supporting** |
| `app.services.risk.metrics` | `stress_risk.py` | Stress-risk metric-family implementation. | public definitions declared in `stress_risk.py`; package-facing names are registered/re-exported by `metrics/__init__.py` where applicable | Standard library: abc, dataclasses, typing \| Required third-party: numpy, pandas, scipy \| Local: domain, limits, scenarios | **Used** | **Supporting** |
| `app.services.risk.metrics` | `account_risk.py` | Account-risk metric-family implementation. | public definitions declared in `account_risk.py`; package-facing names are registered/re-exported by `metrics/__init__.py` where applicable | Standard library: abc, dataclasses, typing \| Required third-party: numpy, pandas, scipy \| Local: domain, limits, scenarios | **Used** | **Supporting** |
| `app.services.risk.metrics` | `drawdown_risk.py` | Drawdown-risk metric-family implementation. | public definitions declared in `drawdown_risk.py`; package-facing names are registered/re-exported by `metrics/__init__.py` where applicable | Standard library: abc, dataclasses, typing \| Required third-party: numpy, pandas, scipy \| Local: domain, limits, scenarios | **Used** | **Supporting** |
| `app.services.risk.metrics` | `strategy_risk.py` | Strategy-risk metric-family implementation. | public definitions declared in `strategy_risk.py`; package-facing names are registered/re-exported by `metrics/__init__.py` where applicable | Standard library: abc, dataclasses, typing \| Required third-party: numpy, pandas, scipy \| Local: domain, limits, scenarios | **Used** | **Supporting** |
| `app.services.risk.metrics` | `concentration.py` | Concentration metric-family implementation. | public definitions declared in `concentration.py`; package-facing names are registered/re-exported by `metrics/__init__.py` where applicable | Standard library: abc, dataclasses, typing \| Required third-party: numpy, pandas, scipy \| Local: domain, limits, scenarios | **Used** | **Supporting** |
| `app.services.risk.metrics` | `position_risk.py` | Position-risk metric-family implementation. | public definitions declared in `position_risk.py`; package-facing names are registered/re-exported by `metrics/__init__.py` where applicable | Standard library: abc, dataclasses, typing \| Required third-party: numpy, pandas, scipy \| Local: domain, limits, scenarios | **Used** | **Supporting** |
| `app.services.risk.metrics` | `portfolio_risk.py` | Portfolio-risk metric-family implementation. | public definitions declared in `portfolio_risk.py`; package-facing names are registered/re-exported by `metrics/__init__.py` where applicable | Standard library: abc, dataclasses, typing \| Required third-party: numpy, pandas, scipy \| Local: domain, limits, scenarios | **Used** | **Supporting** |
| `app.services.risk.metrics` | `volatility_risk.py` | Volatility-risk metric-family implementation. | public definitions declared in `volatility_risk.py`; package-facing names are registered/re-exported by `metrics/__init__.py` where applicable | Standard library: abc, dataclasses, typing \| Required third-party: numpy, pandas, scipy \| Local: domain, limits, scenarios | **Used** | **Supporting** |
| `app.services.risk.metrics` | `correlation_risk.py` | Correlation-risk metric-family implementation. | public definitions declared in `correlation_risk.py`; package-facing names are registered/re-exported by `metrics/__init__.py` where applicable | Standard library: abc, dataclasses, typing \| Required third-party: numpy, pandas, scipy \| Local: domain, limits, scenarios | **Used** | **Supporting** |
| `app.services.risk.metrics` | `currency_exposure.py` | Currency-exposure metric-family implementation. | public definitions declared in `currency_exposure.py`; package-facing names are registered/re-exported by `metrics/__init__.py` where applicable | Standard library: abc, dataclasses, typing \| Required third-party: numpy, pandas, scipy \| Local: domain, limits, scenarios | **Used** | **Supporting** |
| `app.services.risk.models` | `__init__.py` | Package export/compatibility registry. | compatibility re-exports of domain state models | Standard library: none material \| Required third-party: none \| Local: domain compatibility surface | **Used** | **Supporting** |
| `app.services.risk.models` | `market_state.py` | Compatibility market-state model. | public definitions declared in `market_state.py`; package-facing names are registered/re-exported by `models/__init__.py` where applicable | Standard library: none material \| Required third-party: none \| Local: domain compatibility surface | **Possibly used** | **Questionable** |
| `app.services.risk.models` | `symbol_state.py` | Compatibility symbol-state model. | public definitions declared in `symbol_state.py`; package-facing names are registered/re-exported by `models/__init__.py` where applicable | Standard library: none material \| Required third-party: none \| Local: domain compatibility surface | **Possibly used** | **Questionable** |
| `app.services.risk.models` | `account_state.py` | Compatibility account-state model. | public definitions declared in `account_state.py`; package-facing names are registered/re-exported by `models/__init__.py` where applicable | Standard library: none material \| Required third-party: none \| Local: domain compatibility surface | **Possibly used** | **Questionable** |
| `app.services.risk.models` | `position_state.py` | Compatibility position-state model. | public definitions declared in `position_state.py`; package-facing names are registered/re-exported by `models/__init__.py` where applicable | Standard library: none material \| Required third-party: none \| Local: domain compatibility surface | **Possibly used** | **Questionable** |
| `app.services.risk.models` | `portfolio_state.py` | Compatibility portfolio-state model. | public definitions declared in `portfolio_state.py`; package-facing names are registered/re-exported by `models/__init__.py` where applicable | Standard library: none material \| Required third-party: none \| Local: domain compatibility surface | **Possibly used** | **Questionable** |
| `app.services.risk.optimization` | `models.py` | Domain-specific value models. | public definitions declared in `models.py`; package-facing names are registered/re-exported by `optimization/__init__.py` where applicable | Standard library: dataclasses, typing \| Required third-party: numpy/pandas where declared \| Local: core, governance, metrics, scoring | **Used** | **Supporting** |
| `app.services.risk.optimization` | `__init__.py` | Package export/compatibility registry. | AllocationPlanner; AllocationOptimizer; CapitalEfficiencyRanker; HedgeOptimizer; MarginalRiskEvaluator; RecommendationEngine; recommendation models; RebalanceSuggestionEngine | Standard library: dataclasses, typing \| Required third-party: numpy/pandas where declared \| Local: core, governance, metrics, scoring | **Used** | **Supporting** |
| `app.services.risk.optimization` | `capital_efficiency.py` | Rank positions by capital efficiency. | public definitions declared in `capital_efficiency.py`; package-facing names are registered/re-exported by `optimization/__init__.py` where applicable | Standard library: dataclasses, typing \| Required third-party: numpy/pandas where declared \| Local: core, governance, metrics, scoring | **Used** | **Supporting** |
| `app.services.risk.optimization` | `rebalance_suggestions.py` | Generate rebalance suggestions. | public definitions declared in `rebalance_suggestions.py`; package-facing names are registered/re-exported by `optimization/__init__.py` where applicable | Standard library: dataclasses, typing \| Required third-party: numpy/pandas where declared \| Local: core, governance, metrics, scoring | **Used** | **Supporting** |
| `app.services.risk.optimization` | `hedge_optimizer.py` | Generate/evaluate hedge candidates. | public definitions declared in `hedge_optimizer.py`; package-facing names are registered/re-exported by `optimization/__init__.py` where applicable | Standard library: dataclasses, typing \| Required third-party: numpy/pandas where declared \| Local: core, governance, metrics, scoring | **Used** | **Supporting** |
| `app.services.risk.optimization` | `marginal_risk.py` | Evaluate marginal risk of candidate changes. | public definitions declared in `marginal_risk.py`; package-facing names are registered/re-exported by `optimization/__init__.py` where applicable | Standard library: dataclasses, typing \| Required third-party: numpy/pandas where declared \| Local: core, governance, metrics, scoring | **Used** | **Supporting** |
| `app.services.risk.optimization` | `recommendation_engine.py` | Risk recommendation orchestration or compatibility forwarding. | public definitions declared in `recommendation_engine.py`; package-facing names are registered/re-exported by `optimization/__init__.py` where applicable | Standard library: dataclasses, typing \| Required third-party: numpy/pandas where declared \| Local: core, governance, metrics, scoring | **Used** | **Essential** |
| `app.services.risk.optimization` | `allocation_optimizer.py` | Optimize candidate allocations. | public definitions declared in `allocation_optimizer.py`; package-facing names are registered/re-exported by `optimization/__init__.py` where applicable | Standard library: dataclasses, typing \| Required third-party: numpy/pandas where declared \| Local: core, governance, metrics, scoring | **Used** | **Supporting** |
| `app.services.risk.optimization` | `allocation_planner.py` | Generate allocation candidates under risk/governance constraints. | public definitions declared in `allocation_planner.py`; package-facing names are registered/re-exported by `optimization/__init__.py` where applicable | Standard library: dataclasses, typing \| Required third-party: numpy/pandas where declared \| Local: core, governance, metrics, scoring | **Used** | **Essential** |
| `app.services.risk.policy` | `models.py` | Domain-specific value models. | public definitions declared in `models.py`; package-facing names are registered/re-exported by `policy/__init__.py` where applicable | Standard library: dataclasses, datetime, typing \| Required third-party: none material \| Local: domain, governance, workflows | **Supporting** | **Useful** |
| `app.services.risk.policy` | `resolver.py` | Resolve applicable policy bundles/profiles. | public definitions declared in `resolver.py`; package-facing names are registered/re-exported by `policy/__init__.py` where applicable | Standard library: dataclasses, datetime, typing \| Required third-party: none material \| Local: domain, governance, workflows | **Used** | **Useful** |
| `app.services.risk.policy` | `__init__.py` | Package export/compatibility registry. | ApprovalPolicy; ComplianceProfile; PolicyBundle; PolicyEnforcementResult; PolicyResolutionQuery; PolicyResolver; PolicyScope; PolicyVersion; RetentionPolicy; compliance rollout functions | Standard library: dataclasses, datetime, typing \| Required third-party: none material \| Local: domain, governance, workflows | **Used** | **Useful** |
| `app.services.risk.policy` | `pre_trade.py` | Proposal-level pre-trade policy evaluation. | public definitions declared in `pre_trade.py`; package-facing names are registered/re-exported by `policy/__init__.py` where applicable | Standard library: dataclasses, datetime, typing \| Required third-party: none material \| Local: domain, governance, workflows | **Supporting** | **Useful** |
| `app.services.risk.policy` | `compliance.py` | Compliance policy models/evaluation. | public definitions declared in `compliance.py`; package-facing names are registered/re-exported by `policy/__init__.py` where applicable | Standard library: dataclasses, datetime, typing \| Required third-party: none material \| Local: domain, governance, workflows | **Supporting** | **Useful** |
| `app.services.risk.policy` | `restrictions.py` | Trading restriction evaluation. | public definitions declared in `restrictions.py`; package-facing names are registered/re-exported by `policy/__init__.py` where applicable | Standard library: dataclasses, datetime, typing \| Required third-party: none material \| Local: domain, governance, workflows | **Supporting** | **Useful** |
| `app.services.risk.policy` | `compliance_rollout.py` | Compliance rollout/transition helpers. | public definitions declared in `compliance_rollout.py`; package-facing names are registered/re-exported by `policy/__init__.py` where applicable | Standard library: dataclasses, datetime, typing \| Required third-party: none material \| Local: domain, governance, workflows | **Supporting** | **Useful** |
| `app.services.risk.portfolio` | `impacts.py` | Projected risk impact models/calculations. | public definitions declared in `impacts.py`; package-facing names are registered/re-exported by `portfolio/__init__.py` where applicable | Standard library: dataclasses, typing \| Required third-party: numpy/pandas where declared \| Local: calculations, domain, metrics | **Used** | **Supporting** |
| `app.services.risk.portfolio` | `__init__.py` | Package export/compatibility registry. | PortfolioStateEngine; RiskSnapshotEngine; state/snapshot builders; impact/contribution helpers; advisory proposal and enforcement types | Standard library: dataclasses, typing \| Required third-party: numpy/pandas where declared \| Local: calculations, domain, metrics | **Used** | **Supporting** |
| `app.services.risk.portfolio` | `snapshot_builder.py` | Canonical risk metric snapshot construction. | public definitions declared in `snapshot_builder.py`; package-facing names are registered/re-exported by `portfolio/__init__.py` where applicable | Standard library: dataclasses, typing \| Required third-party: numpy/pandas where declared \| Local: calculations, domain, metrics | **Used** | **Essential** |
| `app.services.risk.portfolio` | `proposals.py` | Portfolio/risk proposal models and builders. | public definitions declared in `proposals.py`; package-facing names are registered/re-exported by `portfolio/__init__.py` where applicable | Standard library: dataclasses, typing \| Required third-party: numpy/pandas where declared \| Local: calculations, domain, metrics | **Used** | **Supporting** |
| `app.services.risk.portfolio` | `enforcement.py` | Advisory/enforcement result helpers. | public definitions declared in `enforcement.py`; package-facing names are registered/re-exported by `portfolio/__init__.py` where applicable | Standard library: dataclasses, typing \| Required third-party: numpy/pandas where declared \| Local: calculations, domain, metrics | **Used** | **Supporting** |
| `app.services.risk.portfolio` | `contributions.py` | Marginal and component risk contribution calculations. | public definitions declared in `contributions.py`; package-facing names are registered/re-exported by `portfolio/__init__.py` where applicable | Standard library: dataclasses, typing \| Required third-party: numpy/pandas where declared \| Local: calculations, domain, metrics | **Used** | **Supporting** |
| `app.services.risk.portfolio` | `state_builder.py` | Canonical portfolio state construction. | public definitions declared in `state_builder.py`; package-facing names are registered/re-exported by `portfolio/__init__.py` where applicable | Standard library: dataclasses, typing \| Required third-party: numpy/pandas where declared \| Local: calculations, domain, metrics | **Used** | **Essential** |
| `app.services.risk.portfolio` | `snapshots.py` | Snapshot models/helpers. | public definitions declared in `snapshots.py`; package-facing names are registered/re-exported by `portfolio/__init__.py` where applicable | Standard library: dataclasses, typing \| Required third-party: numpy/pandas where declared \| Local: calculations, domain, metrics | **Used** | **Supporting** |
| `app.services.risk.regimes` | `models.py` | Domain-specific value models. | public definitions declared in `models.py`; package-facing names are registered/re-exported by `regimes/__init__.py` where applicable | Standard library: dataclasses, enum, typing \| Required third-party: numpy/pandas where declared \| Local: domain and market state | **Used** | **Supporting** |
| `app.services.risk.regimes` | `engine.py` | Subsystem orchestration engine. | public definitions declared in `engine.py`; package-facing names are registered/re-exported by `regimes/__init__.py` where applicable | Standard library: dataclasses, enum, typing \| Required third-party: numpy/pandas where declared \| Local: domain and market state | **Used** | **Supporting** |
| `app.services.risk.regimes` | `__init__.py` | Package export/compatibility registry. | RegimeEngine; RegimeState; regime detectors; regime transition helpers | Standard library: dataclasses, enum, typing \| Required third-party: numpy/pandas where declared \| Local: domain and market state | **Used** | **Supporting** |
| `app.services.risk.regimes` | `crisis_regime.py` | Crisis-regime detection. | public definitions declared in `crisis_regime.py`; package-facing names are registered/re-exported by `regimes/__init__.py` where applicable | Standard library: dataclasses, enum, typing \| Required third-party: numpy/pandas where declared \| Local: domain and market state | **Used** | **Supporting** |
| `app.services.risk.regimes` | `market_regime.py` | Market-regime detection. | public definitions declared in `market_regime.py`; package-facing names are registered/re-exported by `regimes/__init__.py` where applicable | Standard library: dataclasses, enum, typing \| Required third-party: numpy/pandas where declared \| Local: domain and market state | **Used** | **Supporting** |
| `app.services.risk.regimes` | `liquidity_regime.py` | Liquidity-regime detection. | public definitions declared in `liquidity_regime.py`; package-facing names are registered/re-exported by `regimes/__init__.py` where applicable | Standard library: dataclasses, enum, typing \| Required third-party: numpy/pandas where declared \| Local: domain and market state | **Used** | **Supporting** |
| `app.services.risk.regimes` | `volatility_regime.py` | Volatility-regime detection. | public definitions declared in `volatility_regime.py`; package-facing names are registered/re-exported by `regimes/__init__.py` where applicable | Standard library: dataclasses, enum, typing \| Required third-party: numpy/pandas where declared \| Local: domain and market state | **Used** | **Supporting** |
| `app.services.risk.regimes` | `regime_transition.py` | Regime transition detection/reporting. | public definitions declared in `regime_transition.py`; package-facing names are registered/re-exported by `regimes/__init__.py` where applicable | Standard library: dataclasses, enum, typing \| Required third-party: numpy/pandas where declared \| Local: domain and market state | **Used** | **Supporting** |
| `app.services.risk.replay` | `clock.py` | Replay clock abstraction. | public definitions declared in `clock.py`; package-facing names are registered/re-exported by `replay/__init__.py` where applicable | Standard library: dataclasses, datetime, typing \| Required third-party: pandas where declared \| Local: core, models, optimization, scoring | **Used** | **Supporting** |
| `app.services.risk.replay` | `models.py` | Domain-specific value models. | public definitions declared in `models.py`; package-facing names are registered/re-exported by `replay/__init__.py` where applicable | Standard library: dataclasses, datetime, typing \| Required third-party: pandas where declared \| Local: core, models, optimization, scoring | **Used** | **Supporting** |
| `app.services.risk.replay` | `__init__.py` | Package export/compatibility registry. | CockpitStatePayload; HypotheticalOrderAction; ReplayClock; ReplayEngine; ReplayFrame; ReplayRun; TimelinePoint; TimelineReconstructor; WhatIfComparison; WhatIfEngine; apply_hypothetical_actions; build_cockpit_state | Standard library: dataclasses, datetime, typing \| Required third-party: pandas where declared \| Local: core, models, optimization, scoring | **Used** | **Supporting** |
| `app.services.risk.replay` | `cockpit_state.py` | Build dashboard/cockpit risk state payload. | public definitions declared in `cockpit_state.py`; package-facing names are registered/re-exported by `replay/__init__.py` where applicable | Standard library: dataclasses, datetime, typing \| Required third-party: pandas where declared \| Local: core, models, optimization, scoring | **Used** | **Supporting** |
| `app.services.risk.replay` | `replay_engine.py` | Replay risk state through a controlled timeline. | public definitions declared in `replay_engine.py`; package-facing names are registered/re-exported by `replay/__init__.py` where applicable | Standard library: dataclasses, datetime, typing \| Required third-party: pandas where declared \| Local: core, models, optimization, scoring | **Used** | **Supporting** |
| `app.services.risk.replay` | `what_if_engine.py` | Evaluate hypothetical portfolio actions and compare projected risk. | public definitions declared in `what_if_engine.py`; package-facing names are registered/re-exported by `replay/__init__.py` where applicable | Standard library: dataclasses, datetime, typing \| Required third-party: pandas where declared \| Local: core, models, optimization, scoring | **Used** | **Essential** |
| `app.services.risk.replay` | `hypothetical_orders.py` | Apply hypothetical order actions to projected state. | public definitions declared in `hypothetical_orders.py`; package-facing names are registered/re-exported by `replay/__init__.py` where applicable | Standard library: dataclasses, datetime, typing \| Required third-party: pandas where declared \| Local: core, models, optimization, scoring | **Used** | **Supporting** |
| `app.services.risk.replay` | `timeline.py` | Timeline point and reconstruction helpers. | public definitions declared in `timeline.py`; package-facing names are registered/re-exported by `replay/__init__.py` where applicable | Standard library: dataclasses, datetime, typing \| Required third-party: pandas where declared \| Local: core, models, optimization, scoring | **Used** | **Supporting** |
| `app.services.risk.reports` | `__init__.py` | Package export/compatibility registry. | RiskReportBuilder; report builders/renderers/savers | Standard library: json, pathlib, typing \| Required third-party: none \| Local: metrics, replay, scenarios, scoring | **Possibly used** | **Useful** |
| `app.services.risk.reports` | `json_export.py` | Serialize/export risk reports to JSON. | public definitions declared in `json_export.py`; package-facing names are registered/re-exported by `reports/__init__.py` where applicable | Standard library: json, pathlib, typing \| Required third-party: none \| Local: metrics, replay, scenarios, scoring | **Test-only** | **Useful** |
| `app.services.risk.reports` | `risk_report.py` | Risk report behavior for the reports subsystem. | public definitions declared in `risk_report.py`; package-facing names are registered/re-exported by `reports/__init__.py` where applicable | Standard library: json, pathlib, typing \| Required third-party: none \| Local: metrics, replay, scenarios, scoring | **Test-only** | **Useful** |
| `app.services.risk.reports` | `markdown_report.py` | Render risk reports to Markdown. | public definitions declared in `markdown_report.py`; package-facing names are registered/re-exported by `reports/__init__.py` where applicable | Standard library: json, pathlib, typing \| Required third-party: none \| Local: metrics, replay, scenarios, scoring | **Test-only** | **Useful** |
| `app.services.risk.reports` | `summary_templates.py` | Report summary templates. | public definitions declared in `summary_templates.py`; package-facing names are registered/re-exported by `reports/__init__.py` where applicable | Standard library: json, pathlib, typing \| Required third-party: none \| Local: metrics, replay, scenarios, scoring | **Test-only** | **Useful** |
| `app.services.risk.reports` | `risk_report_builder.py` | Build consolidated risk report. | public definitions declared in `risk_report_builder.py`; package-facing names are registered/re-exported by `reports/__init__.py` where applicable | Standard library: json, pathlib, typing \| Required third-party: none \| Local: metrics, replay, scenarios, scoring | **Test-only** | **Useful** |
| `app.services.risk.reports` | `replay_report_builder.py` | Build replay report. | public definitions declared in `replay_report_builder.py`; package-facing names are registered/re-exported by `reports/__init__.py` where applicable | Standard library: json, pathlib, typing \| Required third-party: none \| Local: metrics, replay, scenarios, scoring | **Test-only** | **Useful** |
| `app.services.risk.reports` | `scenario_report_builder.py` | Build scenario/stress report. | public definitions declared in `scenario_report_builder.py`; package-facing names are registered/re-exported by `reports/__init__.py` where applicable | Standard library: json, pathlib, typing \| Required third-party: none \| Local: metrics, replay, scenarios, scoring | **Test-only** | **Useful** |
| `app.services.risk.safety` | `audit.py` | Risk audit record construction/persistence. | public definitions declared in `audit.py`; package-facing names are registered/re-exported by `safety/__init__.py` where applicable | Standard library: json, pathlib \| Required third-party: none \| Local: governance kill-switch compatibility | **Possibly used** | **Questionable** |
| `app.services.risk.safety` | `__init__.py` | Package export/compatibility registry. | compatibility re-exports of governed kill-switch API | Standard library: json, pathlib \| Required third-party: none \| Local: governance kill-switch compatibility | **Possibly used** | **Questionable** |
| `app.services.risk.safety` | `kill_switch.py` | Kill-switch state/evaluation logic or compatibility forwarding, depending on folder. | public definitions declared in `kill_switch.py`; package-facing names are registered/re-exported by `safety/__init__.py` where applicable | Standard library: json, pathlib \| Required third-party: none \| Local: governance kill-switch compatibility | **Possibly used** | **Questionable** |
| `app.services.risk.scenarios` | `core.py` | Core scenario evaluation. | public definitions declared in `core.py`; package-facing names are registered/re-exported by `scenarios/__init__.py` where applicable | Standard library: dataclasses, typing \| Required third-party: numpy where declared \| Local: domain and metric inputs | **Used** | **Supporting** |
| `app.services.risk.scenarios` | `models.py` | Domain-specific value models. | public definitions declared in `models.py`; package-facing names are registered/re-exported by `scenarios/__init__.py` where applicable | Standard library: dataclasses, typing \| Required third-party: numpy where declared \| Local: domain and metric inputs | **Used** | **Supporting** |
| `app.services.risk.scenarios` | `registry.py` | Register metric, score, or scenario implementations. | public definitions declared in `registry.py`; package-facing names are registered/re-exported by `scenarios/__init__.py` where applicable | Standard library: dataclasses, typing \| Required third-party: numpy where declared \| Local: domain and metric inputs | **Used** | **Supporting** |
| `app.services.risk.scenarios` | `__init__.py` | Package export/compatibility registry. | ScenarioRegistry; ScenarioResult; StressScenario; build_default_scenario_registry; evaluate_scenarios | Standard library: dataclasses, typing \| Required third-party: numpy where declared \| Local: domain and metric inputs | **Used** | **Supporting** |
| `app.services.risk.scoring` | `base.py` | Base protocol/context/result models. | public definitions declared in `base.py`; package-facing names are registered/re-exported by `scoring/__init__.py` where applicable | Standard library: abc, dataclasses, typing \| Required third-party: numpy where declared \| Local: metrics and scenario outputs | **Used** | **Supporting** |
| `app.services.risk.scoring` | `__init__.py` | Package export/compatibility registry. | RiskScorecard; ScoreContext; ScoreFamily; ScoreRegistry; ScoreRow; build_default_score_registry | Standard library: abc, dataclasses, typing \| Required third-party: numpy where declared \| Local: metrics and scenario outputs | **Used** | **Supporting** |
| `app.services.risk.scoring` | `registry.py` | Register metric, score, or scenario implementations. | public definitions declared in `registry.py`; package-facing names are registered/re-exported by `scoring/__init__.py` where applicable | Standard library: abc, dataclasses, typing \| Required third-party: numpy where declared \| Local: metrics and scenario outputs | **Used** | **Supporting** |
| `app.services.risk.scoring` | `margin_safety.py` | Margin-safety score family. | public definitions declared in `margin_safety.py`; package-facing names are registered/re-exported by `scoring/__init__.py` where applicable | Standard library: abc, dataclasses, typing \| Required third-party: numpy where declared \| Local: metrics and scenario outputs | **Used** | **Supporting** |
| `app.services.risk.scoring` | `normalization.py` | Normalize component scores. | public definitions declared in `normalization.py`; package-facing names are registered/re-exported by `scoring/__init__.py` where applicable | Standard library: abc, dataclasses, typing \| Required third-party: numpy where declared \| Local: metrics and scenario outputs | **Used** | **Supporting** |
| `app.services.risk.scoring` | `leverage_safety.py` | Leverage-safety score family. | public definitions declared in `leverage_safety.py`; package-facing names are registered/re-exported by `scoring/__init__.py` where applicable | Standard library: abc, dataclasses, typing \| Required third-party: numpy where declared \| Local: metrics and scenario outputs | **Used** | **Supporting** |
| `app.services.risk.scoring` | `stress_fragility.py` | Stress-fragility score family. | public definitions declared in `stress_fragility.py`; package-facing names are registered/re-exported by `scoring/__init__.py` where applicable | Standard library: abc, dataclasses, typing \| Required third-party: numpy where declared \| Local: metrics and scenario outputs | **Used** | **Supporting** |
| `app.services.risk.scoring` | `portfolio_health.py` | Portfolio-health score family. | public definitions declared in `portfolio_health.py`; package-facing names are registered/re-exported by `scoring/__init__.py` where applicable | Standard library: abc, dataclasses, typing \| Required third-party: numpy where declared \| Local: metrics and scenario outputs | **Used** | **Supporting** |
| `app.services.risk.scoring` | `scorecard_engine.py` | Aggregate registered score families. | public definitions declared in `scorecard_engine.py`; package-facing names are registered/re-exported by `scoring/__init__.py` where applicable | Standard library: abc, dataclasses, typing \| Required third-party: numpy where declared \| Local: metrics and scenario outputs | **Used** | **Supporting** |
| `app.services.risk.scoring` | `regime_alignment.py` | Regime-alignment score family. | public definitions declared in `regime_alignment.py`; package-facing names are registered/re-exported by `scoring/__init__.py` where applicable | Standard library: abc, dataclasses, typing \| Required third-party: numpy where declared \| Local: metrics and scenario outputs | **Used** | **Supporting** |
| `app.services.risk.scoring` | `concentration_score.py` | Concentration score family. | public definitions declared in `concentration_score.py`; package-facing names are registered/re-exported by `scoring/__init__.py` where applicable | Standard library: abc, dataclasses, typing \| Required third-party: numpy where declared \| Local: metrics and scenario outputs | **Used** | **Supporting** |
| `app.services.risk.scoring` | `overall_risk_quality.py` | Overall risk-quality score. | public definitions declared in `overall_risk_quality.py`; package-facing names are registered/re-exported by `scoring/__init__.py` where applicable | Standard library: abc, dataclasses, typing \| Required third-party: numpy where declared \| Local: metrics and scenario outputs | **Used** | **Supporting** |
| `app.services.risk.scoring` | `diversification_score.py` | Diversification score family. | public definitions declared in `diversification_score.py`; package-facing names are registered/re-exported by `scoring/__init__.py` where applicable | Standard library: abc, dataclasses, typing \| Required third-party: numpy where declared \| Local: metrics and scenario outputs | **Used** | **Supporting** |
| `app.services.risk.scoring` | `governance_compliance.py` | Governance-compliance score family. | public definitions declared in `governance_compliance.py`; package-facing names are registered/re-exported by `scoring/__init__.py` where applicable | Standard library: abc, dataclasses, typing \| Required third-party: numpy where declared \| Local: metrics and scenario outputs | **Used** | **Supporting** |
| `app.services.risk.simulation` | `__init__.py` | Package export/compatibility registry. | compatibility re-exports of replay public API | Standard library: none material \| Required third-party: none \| Local: replay compatibility surface | **Used** | **Supporting** |
| `app.services.risk.simulation` | `replay_engine.py` | Replay risk state through a controlled timeline. | public definitions declared in `replay_engine.py`; package-facing names are registered/re-exported by `simulation/__init__.py` where applicable | Standard library: none material \| Required third-party: none \| Local: replay compatibility surface | **Possibly used** | **Questionable** |
| `app.services.risk.simulation` | `replay_models.py` | Compatibility replay models. | public definitions declared in `replay_models.py`; package-facing names are registered/re-exported by `simulation/__init__.py` where applicable | Standard library: none material \| Required third-party: none \| Local: replay compatibility surface | **Possibly used** | **Questionable** |
| `app.services.risk.simulation` | `cockpit_state.py` | Build dashboard/cockpit risk state payload. | public definitions declared in `cockpit_state.py`; package-facing names are registered/re-exported by `simulation/__init__.py` where applicable | Standard library: none material \| Required third-party: none \| Local: replay compatibility surface | **Possibly used** | **Questionable** |
| `app.services.risk.simulation` | `what_if_engine.py` | Evaluate hypothetical portfolio actions and compare projected risk. | public definitions declared in `what_if_engine.py`; package-facing names are registered/re-exported by `simulation/__init__.py` where applicable | Standard library: none material \| Required third-party: none \| Local: replay compatibility surface | **Possibly used** | **Questionable** |
| `app.services.risk.simulation` | `simulation_clock.py` | Compatibility replay clock. | public definitions declared in `simulation_clock.py`; package-facing names are registered/re-exported by `simulation/__init__.py` where applicable | Standard library: none material \| Required third-party: none \| Local: replay compatibility surface | **Possibly used** | **Questionable** |
| `app.services.risk.simulation` | `hypothetical_orders.py` | Apply hypothetical order actions to projected state. | public definitions declared in `hypothetical_orders.py`; package-facing names are registered/re-exported by `simulation/__init__.py` where applicable | Standard library: none material \| Required third-party: none \| Local: replay compatibility surface | **Possibly used** | **Questionable** |
| `app.services.risk.storage` | `schema.py` | Risk storage schema declarations. | public definitions declared in `schema.py`; package-facing names are registered/re-exported by `storage/__init__.py` where applicable | Standard library: json, typing \| Required third-party: SQLite/database adapter \| Local: domain, metrics, replay | **Used** | **Supporting** |
| `app.services.risk.storage` | `__init__.py` | Package export/compatibility registry. | RISK_STORAGE_TABLES; RiskRepository; RiskScenarioStore; RiskSnapshotStore | Standard library: json, typing \| Required third-party: SQLite/database adapter \| Local: domain, metrics, replay | **Used** | **Supporting** |
| `app.services.risk.storage` | `repositories.py` | Database-backed risk persistence repository. | public definitions declared in `repositories.py`; package-facing names are registered/re-exported by `storage/__init__.py` where applicable | Standard library: json, typing \| Required third-party: SQLite/database adapter \| Local: domain, metrics, replay | **Used** | **Supporting** |
| `app.services.risk.storage` | `snapshot_store.py` | Persist and retrieve risk snapshots/bundles. | public definitions declared in `snapshot_store.py`; package-facing names are registered/re-exported by `storage/__init__.py` where applicable | Standard library: json, typing \| Required third-party: SQLite/database adapter \| Local: domain, metrics, replay | **Used** | **Supporting** |
| `app.services.risk.storage` | `decision_store.py` | Persist and retrieve risk decisions. | public definitions declared in `decision_store.py`; package-facing names are registered/re-exported by `storage/__init__.py` where applicable | Standard library: json, typing \| Required third-party: SQLite/database adapter \| Local: domain, metrics, replay | **Possibly used** | **Useful** |
| `app.services.risk.storage` | `scenario_store.py` | Persist and retrieve scenario results. | public definitions declared in `scenario_store.py`; package-facing names are registered/re-exported by `storage/__init__.py` where applicable | Standard library: json, typing \| Required third-party: SQLite/database adapter \| Local: domain, metrics, replay | **Possibly used** | **Useful** |
| `app.services.risk.validators` | `limits.py` | Limits behavior for the validators subsystem. | public definitions declared in `limits.py`; package-facing names are registered/re-exported by `validators/__init__.py` where applicable | Standard library: dataclasses, typing \| Required third-party: pydantic where declared \| Local: domain and utils.errors | **Test-only** | **Useful** |
| `app.services.risk.validators` | `__init__.py` | Package export/compatibility registry. | validation constants/models; schema, account, symbol, market, position, limit, approval, freshness and registry validators | Standard library: dataclasses, typing \| Required third-party: pydantic where declared \| Local: domain and utils.errors | **Test-only** | **Useful** |
| `app.services.risk.validators` | `symbols.py` | Symbols behavior for the validators subsystem. | public definitions declared in `symbols.py`; package-facing names are registered/re-exported by `validators/__init__.py` where applicable | Standard library: dataclasses, typing \| Required third-party: pydantic where declared \| Local: domain and utils.errors | **Test-only** | **Useful** |
| `app.services.risk.validators` | `account.py` | Account state model. | public definitions declared in `account.py`; package-facing names are registered/re-exported by `validators/__init__.py` where applicable | Standard library: dataclasses, typing \| Required third-party: pydantic where declared \| Local: domain and utils.errors | **Test-only** | **Useful** |
| `app.services.risk.validators` | `common.py` | Shared validation models/helpers. | public definitions declared in `common.py`; package-facing names are registered/re-exported by `validators/__init__.py` where applicable | Standard library: dataclasses, typing \| Required third-party: pydantic where declared \| Local: domain and utils.errors | **Test-only** | **Useful** |
| `app.services.risk.validators` | `validations.py` | General schema and envelope validators. | public definitions declared in `validations.py`; package-facing names are registered/re-exported by `validators/__init__.py` where applicable | Standard library: dataclasses, typing \| Required third-party: pydantic where declared \| Local: domain and utils.errors | **Test-only** | **Useful** |
| `app.services.risk.validators` | `market.py` | Market-state/snapshot model. | public definitions declared in `market.py`; package-facing names are registered/re-exported by `validators/__init__.py` where applicable | Standard library: dataclasses, typing \| Required third-party: pydantic where declared \| Local: domain and utils.errors | **Test-only** | **Useful** |
| `app.services.risk.validators` | `positions.py` | Positions behavior for the validators subsystem. | public definitions declared in `positions.py`; package-facing names are registered/re-exported by `validators/__init__.py` where applicable | Standard library: dataclasses, typing \| Required third-party: pydantic where declared \| Local: domain and utils.errors | **Test-only** | **Useful** |
| `app.services.risk.workflows` | `__init__.py` | Package export/compatibility registry. | none | Standard library: typing \| Required third-party: none \| Local: domain request contracts | **Unknown** | **Questionable** |
| `app.services.risk.workflows` | `request_assembler.py` | Assemble risk assessment requests from component payloads. | public definitions declared in `request_assembler.py`; package-facing names are registered/re-exported by `workflows/__init__.py` where applicable | Standard library: typing \| Required third-party: none \| Local: domain request contracts | **Unused** | **No demonstrated value** |

## 5. Public Behaviour Inventory

### 5.1 Root package tool facade

**Files:** `allocation_tools.py`, `governor_tools.py`, `lifecycle_tools.py`, `portfolio_tools.py`

**Shared behavior:** each function returns a standardized dictionary through `app/services/risk/_common.py::risk_tool_result`. The facade does not establish production usage. The only direct package-wide example is `tests/usage/app/services/risk.py`, and that harness imports a missing `_sample_kwargs` helper from `tests.unit.app.services.risk`.

| Symbol | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
| ------ | ---- | -------------- | --------------- | ------------ | ------ | ------- | ----- | ------------ | ------------ |
| `calculate_correlation_adjusted_size(...)` | Function | Deterministic sizing/allocation calculation or proposal payload. | numeric/configuration inputs → standard tool-result dictionary | None | Converted to standardized error result by wrapper | tests/usage/app/services/risk.py (broken harness); no production caller found | root usage harness only | **Test-only** | **Questionable** |
| `calculate_cost_adjusted_size(...)` | Function | Deterministic sizing/allocation calculation or proposal payload. | numeric/configuration inputs → standard tool-result dictionary | None | Converted to standardized error result by wrapper | tests/usage/app/services/risk.py (broken harness); no production caller found | root usage harness only | **Test-only** | **Questionable** |
| `calculate_fixed_fractional_size(...)` | Function | Deterministic sizing/allocation calculation or proposal payload. | numeric/configuration inputs → standard tool-result dictionary | None | Converted to standardized error result by wrapper | tests/usage/app/services/risk.py (broken harness); no production caller found | root usage harness only | **Test-only** | **Questionable** |
| `calculate_margin_aware_size(...)` | Function | Deterministic sizing/allocation calculation or proposal payload. | numeric/configuration inputs → standard tool-result dictionary | None | Converted to standardized error result by wrapper | tests/usage/app/services/risk.py (broken harness); no production caller found | root usage harness only | **Test-only** | **Questionable** |
| `calculate_max_safe_position_size(...)` | Function | Deterministic sizing/allocation calculation or proposal payload. | numeric/configuration inputs → standard tool-result dictionary | None | Converted to standardized error result by wrapper | tests/usage/app/services/risk.py (broken harness); no production caller found | root usage harness only | **Test-only** | **Questionable** |
| `calculate_risk_parity_weights(...)` | Function | Deterministic sizing/allocation calculation or proposal payload. | numeric/configuration inputs → standard tool-result dictionary | None | Converted to standardized error result by wrapper | tests/usage/app/services/risk.py (broken harness); no production caller found | root usage harness only | **Test-only** | **Questionable** |
| `calculate_volatility_adjusted_size(...)` | Function | Deterministic sizing/allocation calculation or proposal payload. | numeric/configuration inputs → standard tool-result dictionary | None | Converted to standardized error result by wrapper | tests/usage/app/services/risk.py (broken harness); no production caller found | root usage harness only | **Test-only** | **Questionable** |
| `propose_strategy_allocation(...)` | Function | Deterministic sizing/allocation calculation or proposal payload. | numeric/configuration inputs → standard tool-result dictionary | None | Converted to standardized error result by wrapper | tests/usage/app/services/risk.py (broken harness); no production caller found | root usage harness only | **Test-only** | **Questionable** |
| `rebalance_strategy_allocations(...)` | Function | Deterministic sizing/allocation calculation or proposal payload. | numeric/configuration inputs → standard tool-result dictionary | None | Converted to standardized error result by wrapper | tests/usage/app/services/risk.py (broken harness); no production caller found | root usage harness only | **Test-only** | **Questionable** |
| `validate_allocation_proposal(...)` | Function | Deterministic sizing/allocation calculation or proposal payload. | numeric/configuration inputs → standard tool-result dictionary | None | Converted to standardized error result by wrapper | tests/usage/app/services/risk.py (broken harness); no production caller found | root usage harness only | **Test-only** | **Questionable** |
| `check_correlation_limit(...)` | Function | Compare supplied values with supplied limits; aggregate checks. | observed values + thresholds → standard tool-result dictionary | None | Converted to standardized error result by wrapper | tests/usage/app/services/risk.py (broken harness); no production caller found | root usage harness only | **Test-only** | **Questionable** |
| `check_currency_exposure_limit(...)` | Function | Compare supplied values with supplied limits; aggregate checks. | observed values + thresholds → standard tool-result dictionary | None | Converted to standardized error result by wrapper | tests/usage/app/services/risk.py (broken harness); no production caller found | root usage harness only | **Test-only** | **Questionable** |
| `check_cvar_limit(...)` | Function | Compare supplied values with supplied limits; aggregate checks. | observed values + thresholds → standard tool-result dictionary | None | Converted to standardized error result by wrapper | tests/usage/app/services/risk.py (broken harness); no production caller found | root usage harness only | **Test-only** | **Questionable** |
| `check_daily_loss_limit(...)` | Function | Compare supplied values with supplied limits; aggregate checks. | observed values + thresholds → standard tool-result dictionary | None | Converted to standardized error result by wrapper | tests/usage/app/services/risk.py (broken harness); no production caller found | root usage harness only | **Test-only** | **Questionable** |
| `check_kill_switch_state(...)` | Function | Compare supplied values with supplied limits; aggregate checks. | observed values + thresholds → standard tool-result dictionary | None | Converted to standardized error result by wrapper | tests/usage/app/services/risk.py (broken harness); no production caller found | root usage harness only | **Test-only** | **Questionable** |
| `check_leverage_limit(...)` | Function | Compare supplied values with supplied limits; aggregate checks. | observed values + thresholds → standard tool-result dictionary | None | Converted to standardized error result by wrapper | tests/usage/app/services/risk.py (broken harness); no production caller found | root usage harness only | **Test-only** | **Questionable** |
| `check_margin_limit(...)` | Function | Compare supplied values with supplied limits; aggregate checks. | observed values + thresholds → standard tool-result dictionary | None | Converted to standardized error result by wrapper | tests/usage/app/services/risk.py (broken harness); no production caller found | root usage harness only | **Test-only** | **Questionable** |
| `check_max_drawdown_limit(...)` | Function | Compare supplied values with supplied limits; aggregate checks. | observed values + thresholds → standard tool-result dictionary | None | Converted to standardized error result by wrapper | tests/usage/app/services/risk.py (broken harness); no production caller found | root usage harness only | **Test-only** | **Questionable** |
| `check_news_blackout(...)` | Function | Compare supplied values with supplied limits; aggregate checks. | observed values + thresholds → standard tool-result dictionary | None | Converted to standardized error result by wrapper | tests/usage/app/services/risk.py (broken harness); no production caller found | root usage harness only | **Test-only** | **Questionable** |
| `check_portfolio_exposure_limit(...)` | Function | Compare supplied values with supplied limits; aggregate checks. | observed values + thresholds → standard tool-result dictionary | None | Converted to standardized error result by wrapper | tests/usage/app/services/risk.py (broken harness); no production caller found | root usage harness only | **Test-only** | **Questionable** |
| `check_slippage_limit(...)` | Function | Compare supplied values with supplied limits; aggregate checks. | observed values + thresholds → standard tool-result dictionary | None | Converted to standardized error result by wrapper | tests/usage/app/services/risk.py (broken harness); no production caller found | root usage harness only | **Test-only** | **Questionable** |
| `check_spread_limit(...)` | Function | Compare supplied values with supplied limits; aggregate checks. | observed values + thresholds → standard tool-result dictionary | None | Converted to standardized error result by wrapper | tests/usage/app/services/risk.py (broken harness); no production caller found | root usage harness only | **Test-only** | **Questionable** |
| `check_strategy_loss_limit(...)` | Function | Compare supplied values with supplied limits; aggregate checks. | observed values + thresholds → standard tool-result dictionary | None | Converted to standardized error result by wrapper | tests/usage/app/services/risk.py (broken harness); no production caller found | root usage harness only | **Test-only** | **Questionable** |
| `check_symbol_exposure_limit(...)` | Function | Compare supplied values with supplied limits; aggregate checks. | observed values + thresholds → standard tool-result dictionary | None | Converted to standardized error result by wrapper | tests/usage/app/services/risk.py (broken harness); no production caller found | root usage harness only | **Test-only** | **Questionable** |
| `check_trade_frequency_limit(...)` | Function | Compare supplied values with supplied limits; aggregate checks. | observed values + thresholds → standard tool-result dictionary | None | Converted to standardized error result by wrapper | tests/usage/app/services/risk.py (broken harness); no production caller found | root usage harness only | **Test-only** | **Questionable** |
| `check_var_limit(...)` | Function | Compare supplied values with supplied limits; aggregate checks. | observed values + thresholds → standard tool-result dictionary | None | Converted to standardized error result by wrapper | tests/usage/app/services/risk.py (broken harness); no production caller found | root usage harness only | **Test-only** | **Questionable** |
| `run_risk_governor_checks(...)` | Function | Compare supplied values with supplied limits; aggregate checks. | observed values + thresholds → standard tool-result dictionary | None | Converted to standardized error result by wrapper | tests/usage/app/services/risk.py (broken harness); no production caller found | root usage harness only | **Test-only** | **Questionable** |
| `approve_strategy_for_live(...)` | Function | Build/validate strategy risk-profile or approval payload. | profile/strategy/approval fields → standard tool-result dictionary | None; timestamps generated locally | Converted to standardized error result by wrapper | tests/usage only; no persistence caller found | root usage harness only | **Test-only** | **Questionable** |
| `approve_strategy_for_paper(...)` | Function | Build/validate strategy risk-profile or approval payload. | profile/strategy/approval fields → standard tool-result dictionary | None; timestamps generated locally | Converted to standardized error result by wrapper | tests/usage only; no persistence caller found | root usage harness only | **Test-only** | **Questionable** |
| `create_strategy_risk_profile(...)` | Function | Build/validate strategy risk-profile or approval payload. | profile/strategy/approval fields → standard tool-result dictionary | None; timestamps generated locally | Converted to standardized error result by wrapper | tests/usage only; no persistence caller found | root usage harness only | **Test-only** | **Questionable** |
| `get_strategy_risk_profile(...)` | Function | Build/validate strategy risk-profile or approval payload. | profile/strategy/approval fields → standard tool-result dictionary | None; timestamps generated locally | Converted to standardized error result by wrapper | tests/usage only; no persistence caller found | root usage harness only | **Test-only** | **Questionable** |
| `list_strategy_risk_profiles(...)` | Function | Build/validate strategy risk-profile or approval payload. | profile/strategy/approval fields → standard tool-result dictionary | None; timestamps generated locally | Converted to standardized error result by wrapper | tests/usage only; no persistence caller found | root usage harness only | **Test-only** | **Questionable** |
| `revoke_strategy_risk_approval(...)` | Function | Build/validate strategy risk-profile or approval payload. | profile/strategy/approval fields → standard tool-result dictionary | None; timestamps generated locally | Converted to standardized error result by wrapper | tests/usage only; no persistence caller found | root usage harness only | **Test-only** | **Questionable** |
| `update_strategy_risk_limits(...)` | Function | Build/validate strategy risk-profile or approval payload. | profile/strategy/approval fields → standard tool-result dictionary | None; timestamps generated locally | Converted to standardized error result by wrapper | tests/usage only; no persistence caller found | root usage harness only | **Test-only** | **Questionable** |
| `validate_strategy_risk_profile(...)` | Function | Build/validate strategy risk-profile or approval payload. | profile/strategy/approval fields → standard tool-result dictionary | None; timestamps generated locally | Converted to standardized error result by wrapper | tests/usage only; no persistence caller found | root usage harness only | **Test-only** | **Questionable** |
| `calculate_current_drawdown(...)` | Function | Calculate from caller-supplied state or echo supplied state into a snapshot payload. | caller-supplied state/series → standard tool-result dictionary | None | Converted to standardized error result by wrapper | tests/usage only; no broker/database read | root usage harness only | **Test-only** | **Questionable** |
| `calculate_current_margin_usage(...)` | Function | Calculate from caller-supplied state or echo supplied state into a snapshot payload. | caller-supplied state/series → standard tool-result dictionary | None | Converted to standardized error result by wrapper | tests/usage only; no broker/database read | root usage harness only | **Test-only** | **Questionable** |
| `calculate_currency_exposure(...)` | Function | Calculate from caller-supplied state or echo supplied state into a snapshot payload. | caller-supplied state/series → standard tool-result dictionary | None | Converted to standardized error result by wrapper | tests/usage only; no broker/database read | root usage harness only | **Test-only** | **Questionable** |
| `calculate_portfolio_cvar(...)` | Function | Calculate from caller-supplied state or echo supplied state into a snapshot payload. | caller-supplied state/series → standard tool-result dictionary | None | Converted to standardized error result by wrapper | tests/usage only; no broker/database read | root usage harness only | **Test-only** | **Questionable** |
| `calculate_portfolio_exposure(...)` | Function | Calculate from caller-supplied state or echo supplied state into a snapshot payload. | caller-supplied state/series → standard tool-result dictionary | None | Converted to standardized error result by wrapper | tests/usage only; no broker/database read | root usage harness only | **Test-only** | **Questionable** |
| `calculate_portfolio_var(...)` | Function | Calculate from caller-supplied state or echo supplied state into a snapshot payload. | caller-supplied state/series → standard tool-result dictionary | None | Converted to standardized error result by wrapper | tests/usage only; no broker/database read | root usage harness only | **Test-only** | **Questionable** |
| `calculate_strategy_exposure(...)` | Function | Calculate from caller-supplied state or echo supplied state into a snapshot payload. | caller-supplied state/series → standard tool-result dictionary | None | Converted to standardized error result by wrapper | tests/usage only; no broker/database read | root usage harness only | **Test-only** | **Questionable** |
| `calculate_symbol_exposure(...)` | Function | Calculate from caller-supplied state or echo supplied state into a snapshot payload. | caller-supplied state/series → standard tool-result dictionary | None | Converted to standardized error result by wrapper | tests/usage only; no broker/database read | root usage harness only | **Test-only** | **Questionable** |
| `get_account_risk_state(...)` | Function | Calculate from caller-supplied state or echo supplied state into a snapshot payload. | caller-supplied state/series → standard tool-result dictionary | None | Converted to standardized error result by wrapper | tests/usage only; no broker/database read | root usage harness only | **Test-only** | **Questionable** |
| `get_open_orders(...)` | Function | Calculate from caller-supplied state or echo supplied state into a snapshot payload. | caller-supplied state/series → standard tool-result dictionary | None | Converted to standardized error result by wrapper | tests/usage only; no broker/database read | root usage harness only | **Test-only** | **Questionable** |
| `get_open_positions(...)` | Function | Calculate from caller-supplied state or echo supplied state into a snapshot payload. | caller-supplied state/series → standard tool-result dictionary | None | Converted to standardized error result by wrapper | tests/usage only; no broker/database read | root usage harness only | **Test-only** | **Questionable** |
| `get_portfolio_risk_snapshot(...)` | Function | Calculate from caller-supplied state or echo supplied state into a snapshot payload. | caller-supplied state/series → standard tool-result dictionary | None | Converted to standardized error result by wrapper | tests/usage only; no broker/database read | root usage harness only | **Test-only** | **Questionable** |
| `get_strategy_risk_state(...)` | Function | Calculate from caller-supplied state or echo supplied state into a snapshot payload. | caller-supplied state/series → standard tool-result dictionary | None | Converted to standardized error result by wrapper | tests/usage only; no broker/database read | root usage harness only | **Test-only** | **Questionable** |
| `get_symbol_risk_state(...)` | Function | Calculate from caller-supplied state or echo supplied state into a snapshot payload. | caller-supplied state/series → standard tool-result dictionary | None | Converted to standardized error result by wrapper | tests/usage only; no broker/database read | root usage harness only | **Test-only** | **Questionable** |
| `get_total_risk_utilization(...)` | Function | Calculate from caller-supplied state or echo supplied state into a snapshot payload. | caller-supplied state/series → standard tool-result dictionary | None | Converted to standardized error result by wrapper | tests/usage only; no broker/database read | root usage harness only | **Test-only** | **Questionable** |

#### Root support symbols

| File | Symbol | Responsibility | Side effects | Usage status | Value status | Evidence |
| ---- | ------ | -------------- | ------------ | ------------ | ------------ | -------- |
| `_common.py` | `risk_tool_context(...)` | Build tool execution context. | None | Test-only | Supporting | `_common.py::risk_tool_context`; root tool modules |
| `_common.py` | `risk_tool_result(...)` | Execute a callable and wrap success/error output. | Logging/error wrapping; reports read-only metadata | Test-only | Supporting | `_common.py::risk_tool_result`; all four root tool files |
| `_common.py` | `risk_business_payload(...)` | Build common business payload. | None | Test-only | Supporting | root tool modules |
| `_common.py` | `risk_limit_check(...)` | Produce common observed-versus-limit payload. | None | Test-only | Supporting | `governor_tools.py` |
| `_common.py` | `risk_live_module`, `risk_policy_module`, `risk_portfolio_module`, `risk_safety_module` | Identify/label risk module categories. | None | Test-only | Questionable | `_common.py`; no production caller found |

### 5.2 Exact major runtime and governance behavior

| File | Symbol / signature | Type | Responsibility | Inputs → Return | Side effects | Raises / failure behavior | Confirmed callers | Tests | Usage status | Value status |
| ---- | ------------------ | ---- | -------------- | --------------- | ------------ | ------------------------- | ----------------- | ----- | ------------ | ------------ |
| `calculations/position_sizing.py` | `PositionSizer(method='fixed_risk', config=None, mt5_client=None)` | Class | Select fixed-lot, fixed-risk, milestone, Kelly, volatility, or fixed-fractional sizing. | constructor inputs → sizer | Local state mutation; logging | ValueError for unknown method | app/api/routes/risk.py | test_sizing*.py | **Used** | **Essential** |
| `calculations/position_sizing.py` | `PositionSizer.calculate_size(account_balance, entry_price, stop_loss=None, symbol_info=None, context=None, symbol=None, signal_type=None, allow_fractional=False) -> float` | Method | Calculate and normalize lot size. | account/trade/symbol context → lot size | Read-only broker/MT5 data when dynamic ATR stop is enabled; logging | Catches all exceptions and returns 0.1 | POST /api/risk/position-sizing | test_sizing*.py | **Used** | **Essential** |
| `calculations/var.py` | `historical_var(returns, confidence=0.95) -> float` | Function | Historical loss quantile. | return series → non-negative VaR | None | ValueError('missing_returns') | internal/test callers | test_var_es.py | **Supporting** | **Useful** |
| `calculations/var.py` | `incremental_var(current_returns, proposed_returns, confidence=0.95) -> float` | Function | Difference between combined and current historical VaR. | two return series → VaR delta | None | ValueError through historical_var | internal/test callers | test_var_es.py | **Supporting** | **Useful** |
| `calculations/cvar.py` | `historical_cvar(returns, confidence=0.95) -> float` | Function | Average loss in historical tail. | return series → non-negative CVaR | None | ValueError('missing_returns') | internal/test callers | test_var_es.py | **Supporting** | **Useful** |
| `calculations/cvar.py` | `incremental_cvar(current_returns, proposed_returns, confidence=0.95) -> float` | Function | Difference between combined and current historical CVaR. | two return series → CVaR delta | None | ValueError through historical_cvar | internal/test callers | test_var_es.py | **Supporting** | **Useful** |
| `core/portfolio_risk_engine.py` | `PortfolioRiskEngine(mt5_client=None, timeframe='D1', start_pos=0, end_pos=500)` | Class | Own portfolio market-data access and VaR/ES/margin/contribution calculations. | broker adapter + settings → engine | Local state; External API read | Provider exceptions may propagate | risk API; simulator session; serializers | portfolio/governance tests | **Used** | **Essential** |
| `core/portfolio_risk_engine.py` | `compute_portfolio_risk(positions, equity, limits) -> tuple` | Method | Compute current/candidate VaR, ES, margin and risk contributions. | signed-lot map + equity + policy → metrics tuple | External API read | Returns infinities/None on insufficient inputs | GovernanceEngine | test_governor/test_var_es | **Used** | **Essential** |
| `governance/governance_engine.py` | `GovernanceEngine(risk_engine, limits, policy_engine=None)` | Class | Evaluate current and candidate portfolio states against policy. | risk engine + limits → governor | Local state only | Dependency exceptions may propagate | risk API; simulator session | test_governor/test_limits | **Used** | **Essential** |
| `governance/governance_engine.py` | `evaluate_transition_from_states(current_state, new_state, regime=None, forced_decision=None, forced_reason=None) -> GovernanceReport` | Method | Pre-trade governance for projected canonical state. | two states → decision/report | Read-only through risk engine | Dependency exceptions may propagate | simulator trade governance | governance tests | **Used** | **Essential** |
| `governance/governor.py` | `RiskGovernor.evaluate_trade(*, proposal, portfolio_snapshot=None, market_snapshot=None) -> RiskGovernorDecision` | Method | Proposal-level policy check, audit, signature, optional approval token. | proposal + snapshots → signed decision | Persistence write (audit); local replay-state mutation when token validated elsewhere | Fails closed into decision object | test/legacy tool path; no confirmed main runtime caller | test_governor.py | **Test-only** | **Useful** |
| `governance/approval_tokens.py` | `create_approval_token(...) -> RiskApprovalToken` | Function | Bind approved volume and proposal fields to a signed expiring token. | decision/proposal/snapshots/config → token | None | Signer/config errors may propagate | RiskGovernor.evaluate_trade | test_governor.py | **Supporting** | **Supporting** |
| `governance/approval_tokens.py` | `validate_approval_token(token, *, proposal=None, mark_used=True) -> bool` | Function | Check expiry, replay, volume, and material fields. | token/proposal → bool | Local state mutation of process-global signature set | RiskTokenError | legacy/test path | test_governor.py | **Test-only** | **Useful** |
| `governance/validity.py` | `invalidate_for_material_proposal_change(*, approved_proposal, current_proposal) -> RiskDecisionValidity` | Function | Invalidate approval after material proposal change. | two TradeProposal objects → validity | None | None documented | app/services/execution/readiness.py | execution tests | **Used** | **Essential** |
| `governance/validity.py` | `enforce_risk_decision_expiry(*, freshness_expiry, clock=None) -> RiskDecisionValidity` | Function | Expire stale risk decisions. | expiry + clock → validity | Read-only clock | None documented | app/services/execution/readiness.py | execution tests | **Used** | **Essential** |
| `governance/kill_switch.py` | `evaluate_new_entry_block(current_state) -> KillSwitchBlockEvaluation` | Function | Block new entries unless fully armed while permitting force exits. | KillSwitchState → block result | None | None | app/services/execution/trade_action_governor.py | kill-switch tests | **Used** | **Essential** |
| `governance/kill_switch.py` | `KillSwitchService.evaluate(snapshot) -> dict` | Method | Evaluate triggers and write incident artifact when tripped. | risk snapshot → incident payload | Persistence write | Filesystem errors may propagate | no confirmed production caller | test_kill_switch.py | **Test-only** | **Useful** |
| `limits/policy_engine.py` | `PolicyEngine.effective_policy(policy, regime=None) -> (policy, overrides)` | Method | Tighten limits under stress regime. | policy/regime → effective policy + overrides | None | None documented | GovernanceEngine | test_policy/test_limits | **Used** | **Essential** |
| `live/portfolio_manager.py` | `PortfolioManager` | Class | Read broker positions/account and enforce live portfolio checks. | broker client/config → manager | External API read; local state mutation | Fail-closed behavior in checks | app/services/execution/live/engine.py | live/risk tests | **Used** | **Essential** |
| `live/safety_checks.py` | `SafetyChecker` | Class | Apply live safety gates before execution. | broker/runtime risk state → safety result | External API read | Fail-closed behavior | app/services/execution/live/engine.py | live/risk tests | **Used** | **Essential** |
| `portfolio/state_builder.py` | `PortfolioStateEngine` | Class | Normalize account, positions, symbols and market frames into PortfolioState. | simulation/broker state → PortfolioState | None | Validation/provider errors may propagate | SimulatorSession; risk API | models/state tests | **Used** | **Essential** |
| `portfolio/snapshot_builder.py` | `RiskSnapshotEngine` | Class | Run registered metric families over PortfolioState. | PortfolioState/context → RiskSnapshot | None | Metric exceptions may propagate/aggregate | SimulatorSession via core wrapper | snapshot/metric tests | **Used** | **Essential** |
| `scoring/scorecard_engine.py` | `RiskScorecardEngine` | Class | Aggregate registered scores from risk snapshot/state. | snapshot/context → RiskScorecard | None | Score errors may propagate/aggregate | SimulatorSession via core wrapper | score tests | **Used** | **Essential** |
| `optimization/recommendation_engine.py` | `RecommendationEngine` | Class | Generate and rank risk-improvement recommendations. | state/snapshot/scorecard → recommendation batch | None | Dependency errors may propagate | SimulatorSession via core wrapper | optimization tests | **Used** | **Essential** |
| `replay/what_if_engine.py` | `WhatIfEngine` | Class | Project hypothetical actions and compare risk outputs. | state + HypotheticalOrderAction list → WhatIfComparison | None | Validation errors may propagate | SimulatorSession through simulation compatibility API | replay/what-if tests | **Used** | **Essential** |
| `storage/repositories.py` | `RiskRepository` | Class | Persist risk runs, snapshots, replay frames and related records. | database adapter + records → IDs/records | Persistence write/read | Database errors may propagate | SimulatorSession | test_storage.py | **Used** | **Essential** |
| `storage/snapshot_store.py` | `RiskSnapshotStore` | Class | Persist current risk snapshot bundles. | repository + snapshot bundle → storage references | Persistence write/read | Database errors may propagate | SimulatorSession; stop/save workflow | test_storage.py | **Used** | **Essential** |

### 5.3 Registered subsystem behavior

These package-level names were verified through subpackage registries. Leaf implementations are represented in Section 4; exact leaf names are not inferred where the connector returned only a path/registry result.

| Subsystem | Public symbols/families | Responsibility | Inputs → Return | Side effects | Usage status | Value status |
| --------- | ----------------------- | -------------- | --------------- | ------------ | ------------ | ------------ |
| `domain` | `State and contract constructors` | AccountState, SymbolState, PositionState, PortfolioState, snapshot contracts, proposals, decisions, approval tokens | dataclass/Pydantic-style fields → immutable/validated model | None | **Used** | **Supporting** |
| `metrics` | `MetricContext / MetricFamily / MetricRegistry / MetricRow / RiskSnapshot / build_default_metric_registry` | Register and calculate account, position, symbol, strategy, portfolio, drawdown, margin, concentration, volatility, correlation, currency and stress metrics. | PortfolioState/context → metric rows/snapshot | None | **Used** | **Supporting** |
| `scoring` | `ScoreContext / ScoreFamily / ScoreRegistry / ScoreRow / RiskScorecard / build_default_score_registry` | Normalize and aggregate margin, leverage, stress, concentration, diversification, regime, governance and overall quality scores. | risk snapshot/context → score rows/scorecard | None | **Used** | **Supporting** |
| `scenarios` | `StressScenario / ScenarioResult / ScenarioRegistry / evaluate_scenarios / build_default_scenario_registry` | Evaluate registered stress scenarios. | portfolio/state + scenarios → scenario results | None | **Used** | **Supporting** |
| `regimes` | `RegimeEngine / RegimeState / detector classes / transition helpers` | Detect volatility, liquidity, market and crisis regimes and transitions. | market data/context → regime report | None | **Used** | **Useful** |
| `optimization` | `AllocationPlanner / AllocationOptimizer / MarginalRiskEvaluator / HedgeOptimizer / RebalanceSuggestionEngine / CapitalEfficiencyRanker / RecommendationEngine` | Generate risk-aware allocation, hedge, rebalance and capital-efficiency advice. | state/risk engines/policy → candidates and recommendation batch | None | **Used** | **Useful** |
| `replay` | `ReplayClock / ReplayRun / ReplayFrame / ReplayEngine / TimelinePoint / TimelineReconstructor / WhatIfEngine / HypotheticalOrderAction / CockpitStatePayload` | Replay and project portfolio risk and prepare cockpit payloads. | timeline/state/actions → replay frames/comparisons/payloads | Read-only; persistence occurs in caller | **Used** | **Useful** |
| `reports` | `RiskReportBuilder and JSON/Markdown/replay/scenario builders/renderers/savers` | Render durable reports from risk artifacts. | risk artifacts → model/text/file | Persistence write when save/export functions are used | **Test-only** | **Useful** |
| `validators` | `schema/account/symbol/market/position/limit/approval/freshness/registry validators` | Validate risk payloads and return validation or standard envelope results. | payload/schema → result/envelope | None | **Test-only** | **Useful** |
| `policy` | `PolicyResolver and policy/compliance/restriction models/functions` | Resolve applicable policy and evaluate proposal/compliance restrictions. | scope/query/proposal → bundle/result | None | **Used/Supporting** | **Useful** |
| `api` | `PortfolioStateBuilder / RiskSnapshotBuilder / RiskReportBuilder` | Lazy public facade over canonical builders. | constructor args → underlying builder instance | None | **Possibly used** | **Useful** |

### 5.4 Important primitive signatures

| File | Symbol | Responsibility | Inputs → Return | Side effects | Raises | Usage status | Value status |
| ---- | ------ | -------------- | --------------- | ------------ | ------ | ------------ | ------------ |
| `calculations/exposure.py` | `calculate_exposure_summary(positions: tuple[PositionExposure, ...]) -> ExposureSummary` | Gross/net exposure and count. | normalized positions → summary | None | `ValueError` for unsupported direction through `signed_exposure` | Supporting | Useful |
| `calculations/exposure.py` | `calculate_symbol_concentration(..., threshold)` | Gross share by symbol and breaches. | positions/threshold → result | None | None documented | Supporting | Useful |
| `calculations/exposure.py` | `calculate_currency_concentration(..., threshold)` | Gross share by currency and breaches. | positions/threshold → result | None | None documented | Supporting | Useful |
| `calculations/exposure.py` | `calculate_strategy_family_concentration(..., threshold)` | Gross share by strategy family and breaches. | positions/threshold → result | None | None documented | Supporting | Useful |
| `calculations/exposure.py` | `exposure_snapshot(positions, equity=100000.0) -> dict` | Build lightweight exposure ratios from raw dictionaries. | raw positions/equity → map | None | Conversion errors may propagate | Supporting | Questionable for live use |
| `calculations/margin.py` | `calculate_margin_utilization(...) -> MarginUtilization` | Calculate used-margin ratio. | balance/equity/free/used → model | None | None documented | Supporting | Useful |
| `calculations/margin.py` | `calculate_volatility_adjusted_size(...) -> VolatilityAdjustedSizing` | Inverse-volatility scaling within bounds. | base/reference/observed volatility → model | None | `ValueError` for non-positive volatility | Supporting | Useful |
| `calculations/margin.py` | `calculate_drawdown_state(...) -> DrawdownState` | Classify drawdown band. | peak/current equity → model | None | `ValueError` for non-positive peak | Supporting | Useful |
| `calculations/correlation.py` | `calculate_correlation_concentration(pairs, *, threshold) -> CorrelationConcentration` | Weighted pair concentration and breached pairs. | pairs/threshold → result | None | Conversion errors may propagate | Supporting | Useful |
| `calculations/drawdown.py` | `drawdown_state(portfolio_snapshot, thresholds) -> dict` | Check daily/weekly/monthly/portfolio/strategy/symbol loss and critical thresholds. | dictionaries → metrics/failures/critical | None | Missing required threshold keys raise | Supporting | Useful |
| `calculations/math_utils.py` | `pip_value(symbol, volume) -> float` | Approximate pip value from symbol text. | symbol/volume → value | None | Conversion errors may propagate | Supporting | Questionable |
| `calculations/math_utils.py` | `notional_exposure(proposal) -> float` | Approximate notional; defaults contract size to 100,000. | proposal → absolute notional | None | Conversion errors may propagate | Supporting | Questionable |
| `governance/kill_switch.py` | `KillSwitchStateMachine.transition(...) -> KillSwitchStateMachine` | Enforce allowed transition and recovery authorization. | state/target/auth → new state | None | `KillSwitchTransitionError` | Supporting | Useful |
| `governance/kill_switch.py` | `require_hard_trigger_recovery_dual_auth(approvals) -> bool` | Require distinct Risk Manager and Compliance approvals. | approvals → bool | None | None | Test-only | Useful |

### 5.5 Compatibility and forwarding behavior

| Compatibility location | Canonical target | Actual behavior | Usage status | Value status |
| ---------------------- | ---------------- | --------------- | ------------ | ------------ |
| `core/governance_engine.py` | `governance/governance_engine.py` | `import *` forwarding wrapper. | Used by simulator session | Supporting |
| `core/risk_snapshot_engine.py` | `portfolio/snapshot_builder.py` | `import *` forwarding wrapper. | Used by simulator session | Supporting |
| `core/portfolio_state_engine.py` | `portfolio/state_builder.py` | `import *` forwarding wrapper. | Used by simulator session | Supporting |
| `models/__init__.py` | `domain` state models | Compatibility re-export. | Used by API/session code | Supporting |
| `simulation/__init__.py` | `replay` public API | Compatibility re-export. | Used by API/session code | Supporting |
| `safety/__init__.py` and `safety/kill_switch.py` | `governance/kill_switch.py` | Compatibility surface. | Possibly used | Questionable |
| `api/public.py` | core/portfolio/report builders | Lazy constructor facade. | Possibly used | Useful |

## 6. Actual Workflows

### `V1-WF-RISK-001` — API Position Sizing

* **Scope:** Cross-domain
* **Trigger:** `POST /api/risk/position-sizing`
* **Input boundary:** HTTP request with method, account balance, entry/stop, symbol information, and context.
* **Functions and methods used:** `PositionSizer.__init__` → `PositionSizer.calculate_size` → method-specific private calculation → `validate_position_size`.
* **Files involved:** `app/api/routes/risk.py`, `calculations/position_sizing.py`.
* **External dependencies:** optional MT5/broker client for ATR-backed dynamic stop calculation.
* **Output boundary:** JSON response containing calculated lot size.
* **Failure behaviour:** invalid method raises at construction; calculation-time exceptions are logged and converted to a `0.1` lot fallback.
* **Operational status:** **Working with unsafe fallback**
* **Evidence:** `app/api/routes/risk.py::<position-sizing route>`; `calculations/position_sizing.py::PositionSizer.calculate_size`.

```text
HTTP request
→ PositionSizer(method, config, mt5_client)
→ calculate_size(...)
→ selected sizing algorithm
→ symbol-volume normalization
→ lot-size response
```

### `V1-WF-RISK-002` — API Regime Detection

* **Scope:** Cross-domain
* **Trigger:** `POST /api/risk/regime-detection`
* **Input boundary:** market/state payload from API caller.
* **Functions and methods used:** canonical state building → `CrisisRegimeDetector` / `RegimeEngine`.
* **Files involved:** `app/api/routes/risk.py`, `portfolio/state_builder.py`, `regimes/engine.py`, detector files.
* **External dependencies:** request-supplied market data.
* **Output boundary:** detected regime and supporting report.
* **Failure behaviour:** route/provider validation errors return API error.
* **Operational status:** **Working**
* **Evidence:** `app/api/routes/risk.py::<regime route>` imports and calls risk regime components.

```text
HTTP market/state payload
→ PortfolioStateEngine
→ RegimeEngine + detector set
→ regime report
→ HTTP response
```

### `V1-WF-RISK-003` — API Allocation Advice

* **Scope:** Cross-domain
* **Trigger:** `POST /api/risk/allocation`
* **Input boundary:** portfolio/simulation state, limits, candidate allocation settings.
* **Functions and methods used:** `PortfolioRiskEngine` → `GovernanceEngine` → `AllocationPlanner`.
* **Files involved:** `app/api/routes/risk.py`, `core/portfolio_risk_engine.py`, `governance/governance_engine.py`, `optimization/allocation_planner.py`, `limits/models.py`.
* **External dependencies:** simulation engine/market state and optional broker-like adapter.
* **Output boundary:** allocation candidates/advice; no trade is placed by this workflow.
* **Failure behaviour:** insufficient risk data can produce infinite risk metrics, causing fail-closed governance.
* **Operational status:** **Working**
* **Evidence:** `app/api/routes/risk.py::<allocation route>`.

```text
HTTP portfolio request
→ portfolio risk calculations
→ governance feasibility
→ AllocationPlanner
→ advisory allocation response
```

### `V1-WF-RISK-004` — API Portfolio Governance

* **Scope:** Cross-domain
* **Trigger:** `POST /api/risk/governance`
* **Input boundary:** current or proposed portfolio state.
* **Functions and methods used:** `PortfolioStateEngine` → `PortfolioRiskEngine` → `GovernanceEngine.evaluate_*`.
* **Files involved:** `app/api/routes/risk.py`, `portfolio/state_builder.py`, `core/portfolio_risk_engine.py`, `governance/governance_engine.py`, `limits`.
* **External dependencies:** request/simulation market data.
* **Output boundary:** `GovernanceReport`.
* **Failure behaviour:** missing/insufficient historical data yields infinite VaR/ES and should reject through policy.
* **Operational status:** **Working**
* **Evidence:** `app/api/routes/risk.py::<governance route>`.

```text
HTTP state/proposal
→ canonical PortfolioState
→ VaR/ES/margin/contribution calculation
→ pre/post-trade policy checks
→ GovernanceReport
```

### `V1-WF-RISK-005` — Simulator Session Risk Refresh and Persistence

* **Scope:** Cross-domain
* **Trigger:** simulator session creation/resume, state refresh, step progression, or stop-and-save.
* **Input boundary:** simulator account, symbols, positions, market bars, and database manager.
* **Functions and methods used:** `PortfolioStateEngine` → `RiskSnapshotEngine` → `RiskScorecardEngine` → `RecommendationEngine` → `RiskRepository` / `RiskSnapshotStore`.
* **Files involved:** `app/api/session/session_runtime.py`, `app/api/session/session_service.py`, risk `core`, `portfolio`, `metrics`, `scoring`, `optimization`, `storage`.
* **External dependencies:** simulator engine, SQLite/database manager, broker symbol metadata.
* **Output boundary:** latest risk state, snapshot, scorecard, recommendation batch, risk run/snapshot IDs.
* **Failure behaviour:** resume/stop-and-save converts failures to HTTP 500; stop-and-save reattaches runtime on failure.
* **Operational status:** **Working**
* **Evidence:** `app/api/session/session_runtime.py::SimulatorSession.__init__`; `app/api/session/session_service.py::resume_or_restore_session`; `::stop_and_save_session_runtime`.

```text
Simulator account/market/positions
→ PortfolioStateEngine
→ RiskSnapshotEngine
→ RiskScorecardEngine
→ RecommendationEngine
→ RiskRepository / RiskSnapshotStore
→ session response and persisted IDs
```

### `V1-WF-RISK-006` — Simulator Pre-Trade Governance

* **Scope:** Cross-domain
* **Trigger:** simulator market trade or pending-order request.
* **Input boundary:** active `SimulatorSession` and requested symbol/volume.
* **Functions and methods used:** session governance evaluation → `GovernanceEngine.evaluate_transition_from_states` → simulator mutation only after evaluation.
* **Files involved:** `app/api/session/trade_service.py`, `app/api/session/session_runtime.py`, `governance/governance_engine.py`, `core/portfolio_risk_engine.py`, `limits`.
* **External dependencies:** simulator execution engine.
* **Output boundary:** trade/order result plus governance, snapshot, scorecard and recommendations.
* **Failure behaviour:** rejected governance becomes an HTTP error in the private gate; execution failure becomes HTTP 500. Manual override is allowed only in manual mode when explicitly accepted.
* **Operational status:** **Working**
* **Evidence:** `app/api/session/trade_service.py::execute_trade`; `::place_pending_order`; private `_evaluate_trade_governance`.

```text
Trade/order request
→ build projected portfolio state
→ GovernanceEngine
→ ACCEPT/REJECT
→ simulator mutation only on accepted/allowed override
→ refreshed risk response
```

### `V1-WF-RISK-007` — Simulator What-If Analysis

* **Scope:** Cross-domain
* **Trigger:** simulator what-if API request.
* **Input boundary:** active session, list of hypothetical order actions, optional leverage override.
* **Functions and methods used:** `HypotheticalOrderAction` → `WhatIfEngine` → risk snapshot/scorecard/recommendations → persistence → serializer.
* **Files involved:** `app/api/session/trade_service.py`, `app/api/session/serializers.py`, `replay/what_if_engine.py`, `replay/hypothetical_orders.py`, `storage`.
* **External dependencies:** simulator state and database.
* **Output boundary:** baseline-versus-projected comparison and storage references.
* **Failure behaviour:** validation/engine/storage failures propagate through API handling.
* **Operational status:** **Working**
* **Evidence:** `app/api/session/trade_service.py::evaluate_what_if`.

```text
Hypothetical actions
→ projected state
→ projected snapshot/scorecard/recommendations
→ baseline comparison
→ persist comparison
→ API payload
```

### `V1-WF-RISK-008` — Live Portfolio and Safety Gate

* **Scope:** Cross-domain
* **Trigger:** live execution engine processes a candidate action.
* **Input boundary:** broker account/positions/market state and risk configuration.
* **Functions and methods used:** `PortfolioManager` and `SafetyChecker`.
* **Files involved:** `app/services/execution/live/engine.py`, `risk/live/portfolio_manager.py`, `risk/live/safety_checks.py`.
* **External dependencies:** broker/MT5 adapter.
* **Output boundary:** allow/block/size/portfolio safety outcome to execution.
* **Failure behaviour:** live checks are intended to fail closed on missing provider state.
* **Operational status:** **Working, provider-coupled**
* **Evidence:** `app/services/execution/live/engine.py::<imports/calls>`.

```text
Live broker state + candidate
→ PortfolioManager
→ SafetyChecker
→ allow/block result
→ execution domain
```

### `V1-WF-RISK-009` — Risk Decision Freshness and Proposal-Change Gate

* **Scope:** Cross-domain
* **Trigger:** execution readiness validation.
* **Input boundary:** approved/current `TradeProposal` and decision expiry.
* **Functions and methods used:** `invalidate_for_material_proposal_change` and `enforce_risk_decision_expiry`.
* **Files involved:** `app/services/execution/readiness.py`, `governance/validity.py`.
* **External dependencies:** shared clock abstraction.
* **Output boundary:** validity result/reason codes to execution.
* **Failure behaviour:** changed or expired proposal is invalid.
* **Operational status:** **Working**
* **Evidence:** `app/services/execution/readiness.py`; `governance/validity.py`.

```text
Approved proposal + current proposal + expiry
→ material fingerprint comparison
→ clock expiry check
→ valid/invalid reason codes
→ execution readiness
```

### `V1-WF-RISK-010` — Global Kill-Switch Entry Block

* **Scope:** Cross-domain
* **Trigger:** execution action governance.
* **Input boundary:** current kill-switch state.
* **Functions and methods used:** `evaluate_new_entry_block`.
* **Files involved:** `app/services/execution/trade_action_governor.py`, `governance/kill_switch.py`.
* **External dependencies:** governance kill-switch state.
* **Output boundary:** block new entry; force exits remain permitted.
* **Failure behaviour:** any state other than `ARMED` blocks new entries.
* **Operational status:** **Working**
* **Evidence:** `app/services/execution/trade_action_governor.py`; `governance/kill_switch.py::evaluate_new_entry_block`.

```text
Execution request + kill-switch state
→ evaluate_new_entry_block
→ block new entry or allow
→ execution action decision
```

### `V1-WF-RISK-011` — Signed Proposal Decision and Approval Token

* **Scope:** Internal
* **Trigger:** direct call to `RiskGovernor.evaluate_trade`.
* **Input boundary:** proposal, portfolio snapshot, market snapshot and thresholds.
* **Functions and methods used:** normalize proposal → `evaluate_policy` → audit write → decision signing → optional `create_approval_token`.
* **Files involved:** `governance/governor.py`, `policy/pre_trade.py`, `governance/audit.py`, `governance/signatures.py`, `governance/approval_tokens.py`, `config/thresholds.py`.
* **External dependencies:** filesystem/audit persistence and signing configuration.
* **Output boundary:** `RiskGovernorDecision` with optional token.
* **Failure behaviour:** catches risk/engine exceptions and returns `error_fail_closed`.
* **Operational status:** **Unverified in production; unit/legacy path**
* **Evidence:** `governance/governor.py::RiskGovernor.evaluate_trade`; no confirmed main API/session caller.

```text
Risk proposal
→ normalize
→ policy evaluation
→ audit
→ signed decision
→ optional approval token
```

### `V1-WF-RISK-012` — Root AI Tool Invocation

* **Scope:** Internal/test-facing
* **Trigger:** import a name from `app.services.risk.__all__`.
* **Input boundary:** caller-supplied numeric/state/config values.
* **Functions and methods used:** one of 50 root tools → `_common.risk_tool_result`.
* **Files involved:** root tool files and `_common.py`.
* **External dependencies:** none except pandas for some calculations.
* **Output boundary:** standardized tool-result dictionary.
* **Failure behaviour:** exceptions are converted to error envelopes.
* **Operational status:** **Broken demonstration / no production caller confirmed**
* **Evidence:** `tests/usage/app/services/risk.py` imports missing `_sample_kwargs`; `tests/usage/app/services/05_risk.py` imports a different removed API.

```text
Caller-supplied payload
→ root tool
→ deterministic calculation/payload assembly
→ generic read-only tool envelope
```

## 7. Usage and Caller Map

| Public symbol | Called from | Call type | Runtime or test | Evidence |
| ------------- | ----------- | --------- | --------------- | -------- |
| `PositionSizer` / `calculate_size` | `app/api/routes/risk.py` | direct construction/method call | Runtime | `routes/risk.py::<position-sizing route>` |
| `PortfolioStateEngine` | `app/api/routes/risk.py`; `app/api/session/session_runtime.py` | import/construct | Runtime | route/session imports |
| `PortfolioRiskEngine` | risk API; session runtime; session serializers | import/construct/method calls | Runtime | `routes/risk.py`; `session_runtime.py`; `serializers.py` |
| `GovernanceEngine` | risk API; simulator session | import/construct/method calls | Runtime | `routes/risk.py`; `session_runtime.py`; `trade_service.py` |
| `RiskLimits` | risk API; simulator session | construct/configure | Runtime | API/session imports |
| `AllocationPlanner` | risk API | direct construction/call | Runtime | allocation route |
| `CorrelationPreference` | risk API | construct | Runtime | allocation route |
| `RegimeEngine` and detector set | risk API/session risk refresh | construct/call | Runtime | regime route/session imports |
| `RiskSnapshotEngine` | simulator session | construct/call via `core` wrapper | Runtime | `SimulatorSession.__init__` |
| `RiskScorecardEngine` | simulator session | construct/call via `core` wrapper | Runtime | `SimulatorSession.__init__` |
| `RecommendationEngine` | simulator session | construct/call via `core` wrapper | Runtime | `SimulatorSession.__init__` |
| `TimelineReconstructor` | simulator session | construct/call | Runtime | `SimulatorSession.__init__` |
| `WhatIfEngine` | simulator session/trade service | construct/call through `simulation` compatibility API | Runtime | `session_runtime.py`; `trade_service.py` |
| `HypotheticalOrderAction` | trade service | construct | Runtime | `trade_service.py::evaluate_what_if` |
| `RiskRepository` | simulator session | construct/read/write | Runtime | `SimulatorSession.__init__` |
| `RiskSnapshotStore` | simulator session | construct/write | Runtime | session initialization and stop/save |
| `RiskSnapshot` | session annotations/serialization | model use | Runtime | `session_runtime.py` |
| `RiskScorecard` | session annotations/serialization | model use | Runtime | `session_runtime.py` |
| `AccountSnapshot`, `MarketSnapshot`, `PortfolioSnapshot` | `app/services/execution/shadow/feeds.py` | imported model contracts | Runtime | `build_shadow_data_feed` |
| `invalidate_for_material_proposal_change` | `app/services/execution/readiness.py` | direct function call | Runtime | readiness module |
| `enforce_risk_decision_expiry` | `app/services/execution/readiness.py` | direct function call | Runtime | readiness module |
| `evaluate_new_entry_block` | `app/services/execution/trade_action_governor.py` | direct function call | Runtime | trade action governor |
| `PortfolioManager` | `app/services/execution/live/engine.py` | import/construct | Runtime | live execution engine |
| `SafetyChecker` | `app/services/execution/live/engine.py` | import/construct | Runtime | live execution engine |
| `PolicyResolver` | `app/api/dependencies.py` | construct dependency | Runtime | API dependencies |
| 50 root tools | `tests/usage/app/services/risk.py` | iterate `__all__` | Test/example | harness fails because `_sample_kwargs` is absent |
| old flat API (`RiskGovernor`, `RiskLimits`, `RiskStore`, etc.) | `tests/usage/app/services/05_risk.py` | root imports | Test/example | imports do not match current root exports |
| old `app.agentic.tools.risk` facade | `test_tools.py`; `test_import_safety.py` | imports | Test | module was not found in current revision |

## 8. Cross-Domain Surface

### Outbound — this domain depends on

| Depends on (domain/package) | Symbols or capabilities consumed | Where used in this domain | Evidence |
| --------------------------- | -------------------------------- | ------------------------- | -------- |
| `app.services.utils` | logger, standard tool envelope, clock, shared errors | root tools, calculations, validity, live | imports in `_common.py`, `position_sizing.py`, `validity.py` |
| `app.services.brokers` / MT5-like client | account equity, bars, symbol info, margin required, positions | `core/portfolio_risk_engine.py`, `calculations/position_sizing.py`, `live/*` | provider methods `get_bars`, `get_symbol_info`, `get_margin_required` |
| `app.services.governance.workflow` | kill-switch state and transition rules | `governance/kill_switch.py` | direct import |
| `app.agentic.contracts.trade_proposal` | `TradeProposal` material fingerprint | `governance/validity.py` | direct import |
| simulation engine/state | account, market and position state | API/session risk workflow | simulator adapter in `session_runtime.py` |
| SQLite/database layer | risk runs/snapshots/replay storage | `storage/*`; simulator session | `RiskRepository`, `RiskSnapshotStore` |
| NumPy/Pandas/SciPy | returns, covariance, quantiles, matrices, frames | calculations/core/metrics/regimes | quantitative modules |
| filesystem/audit path | risk and kill-switch artifacts | governance audit/kill switch/reports | JSON/Markdown write functions |

### Inbound — other packages depend on this domain

| Consuming domain/package | Symbols consumed from this domain | Purpose | Evidence |
| ------------------------ | --------------------------------- | ------- | -------- |
| `app/api/routes/risk.py` | sizing, state, regime, allocation, governance engines/models | standalone risk HTTP endpoints | direct imports/calls |
| `app/api/session/session_runtime.py` | state, snapshot, scorecard, recommendation, replay, storage, governance | simulator risk lifecycle | `SimulatorSession.__init__` |
| `app/api/session/trade_service.py` | `HypotheticalOrderAction`; session governance products | pre-trade gate and what-if | direct import/calls |
| `app/api/session/serializers.py` | `PortfolioRiskEngine`, `PortfolioState` | serialize and estimate projected margin | direct import/call |
| `app/api/session/session_service.py` | indirect session risk refresh/persist | restore and stop/save | calls `refresh_risk_state` / persistence |
| `app/services/execution/readiness.py` | validity functions | reject stale/changed approvals | direct calls |
| `app/services/execution/trade_action_governor.py` | kill-switch block evaluation | block new live entries | direct call |
| `app/services/execution/live/engine.py` | `PortfolioManager`, `SafetyChecker` | live execution safety | direct imports |
| `app/services/execution/shadow/feeds.py` | snapshot models | build production-shaped shadow feed | direct imports |
| tests/examples | root tools, validators, old flat API | demonstrations and unit coverage | test files; several stale |

## 9. Duplicate and Overlapping Behaviour

| Item A | Item B | Overlap | Evidence | Risk |
| ------ | ------ | ------- | -------- | ---- |
| root tool facade | layered calculations/governance/portfolio APIs | Same capability names implemented as shallow payload tools and deeper engines. | root `__all__`; nested registries | Callers can select a materially different implementation by import path. |
| `core/governance_engine.py` | `governance/governance_engine.py` | Full star-forwarding wrapper. | wrapper file imports canonical module with `*` | Ownership and search results are duplicated. |
| `core/risk_snapshot_engine.py` | `portfolio/snapshot_builder.py` | Forwarding wrapper. | wrapper source | Same class appears to belong to two modules. |
| `core/portfolio_state_engine.py` | `portfolio/state_builder.py` | Forwarding wrapper. | wrapper source | Same class appears to belong to two modules. |
| `models` | `domain` | Compatibility state model surface. | `models/__init__.py`; domain registry | Two canonical-looking model locations. |
| `simulation` | `replay` | Compatibility replay/what-if surface plus duplicate leaf filenames. | `simulation/__init__.py`; parallel file sets | Stale copies may diverge from canonical replay. |
| `safety/kill_switch.py` | `governance/kill_switch.py` | Compatibility kill-switch surface. | safety registry and governance implementation | Two ownership locations for a safety-critical control. |
| `RiskGovernor` | `GovernanceEngine` | Both produce risk acceptance decisions but use different contracts, calculations, persistence and callers. | governance modules | “Governor” is ambiguous and workflows are not interchangeable. |
| root `calculate_*` functions | metrics/calculations/core engines | Duplicate names for VaR, CVaR, exposure, sizing and limits. | root files vs nested modules | Root functions may be mistaken for production-grade calculations. |
| `reports/*` builders | root lifecycle/portfolio payload builders | Both produce user-facing risk payload/report-like outputs. | files and registries | Output schemas and persistence behavior differ. |

## 10. Unused or Questionable Items

| Item | Finding | Searches performed | Confidence | Evidence |
| ---- | ------- | ------------------ | ---------- | -------- |
| `workflows/request_assembler.py` | No production, test, route, registry, callback or script caller was found. | imports, calls, package exports, API, execution, tests, usage scripts | **Medium** | file exists; `workflows/__init__.py` exports nothing |
| root 50 tools | No confirmed production/runtime caller; only a broken generic usage harness. | root imports, `__all__`, routes, execution, session, tests, examples | **Medium** | `tests/usage/app/services/risk.py`; no app caller |
| `api/public.py` lazy facades | Separate public facade exists, but no confirmed caller found. | imports of `app.services.risk.api`, class names, routes/tests | **Medium** | `api/__init__.py`; `api/public.py` |
| `reports/*` | Current files have tests and plausible report value, but no confirmed primary API/session caller for most builders/renderers. | imports/calls/routes/session/tests | **Medium** | report registry; `test_reports.py` |
| `safety/*` compatibility namespace | Canonical execution caller imports governance kill-switch directly; no confirmed need for safety alias. | execution/import searches and package registry | **Medium** | `trade_action_governor.py`; safety registry |
| `simulation` leaf files | Session imports the compatibility package, but the parallel leaf implementations may be stale relative to `replay`. | package import, exact leaf imports, tests | **Medium** | parallel identical-purpose filenames |
| `models` leaf files | Runtime imports `app.services.risk.models`; exact need for each compatibility leaf file was not confirmed. | package imports and leaf-path searches | **Medium** | models/domain overlap |
| `live/run.py` | Standalone entry helper exists; no scheduler/CLI registration was confirmed. | imports, scripts, entry-point and route searches | **Medium** | file path only |
| `governance/governor.py` signed-token path | Valuable implementation, but no confirmed main runtime caller in API/session/execution. | class imports/calls, routes, execution, tests | **Medium** | unit/legacy usage evidence only |
| legacy flat modules named by tests (`risk.stress`, `risk.kill_switch`, etc.) | Tests reference modules that do not exist at those paths. | fetch exact paths; test imports | **High** for mismatch | 404/current tree plus stale test imports |
| `app.agentic.tools.risk` | Referenced by risk tests but not found. | exact path fetch and repository search | **High** for mismatch | `test_tools.py`; `test_import_safety.py` |

No item above is labelled “dead code” because a local full-history checkout, runtime import tracing, deployment configuration, and external repository consumers were unavailable.

## 11. Incomplete or Disconnected Workflows

| Workflow / capability | Missing connection | Current impact | Evidence |
| --------------------- | ------------------ | -------------- | -------- |
| Root AI tool workflow | No current agent tool registry/runtime caller; usage harness is broken. | Fifty exported tools may not be reachable from production. | root `__all__`; usage harness |
| Signed approval-token workflow | Main simulator/live execution paths were not confirmed to consume `RiskGovernor` tokens. | Token issuance may be isolated from actual order execution. | governor/token files vs session/live callers |
| Execution trade-action governance | Creates a synthetic fixed approval rather than invoking canonical risk calculation/governance. | An “approved” execution decision may not represent evaluated portfolio risk. | `app/services/execution/trade_action_governor.py` |
| Root lifecycle approvals | Approve/revoke/update functions build payloads but do not persist lifecycle state. | Names imply state mutation that does not occur. | `lifecycle_tools.py`; `_common.risk_tool_result` |
| Root portfolio “get” functions | Caller must supply the positions/orders/account state. | They do not provide retrieval despite `get_*` names. | `portfolio_tools.py` |
| Live kill-switch incident workflow | `KillSwitchService.evaluate` writes an incident artifact, but no production caller was confirmed. | Trigger evaluation may be disconnected from live execution. | governance kill-switch vs execution call map |
| Reports | Builders/renderers exist, but most are not connected to current API/session output. | Report functionality may be test-only or dormant. | reports registry and caller search |
| Validation facade | Broad current validators are unit-tested, but API/session routes generally use models/private validation instead. | Validation behavior is not consistently applied at boundaries. | validators tests vs API imports |

## 12. Structural Problems

| ID | Problem | Location | Impact | Evidence |
| -- | ------- | -------- | ------ | -------- |
| `V1-ISSUE-RISK-001` | Public API mismatch between root exports, README, nested `api`, and compatibility packages. | `risk/__init__.py`, `README.md`, `api/*`, nested registries | Callers cannot infer the supported import path. | README names classes not exported by root. |
| `V1-ISSUE-RISK-002` | Stale usage example imports removed root classes/modules. | `tests/usage/app/services/05_risk.py` | Example fails at import and cannot validate real workflow. | imports do not exist in current root. |
| `V1-ISSUE-RISK-003` | Generic root usage harness imports absent `_sample_kwargs`. | `tests/usage/app/services/risk.py`; test package `__init__.py` | All-root-tools demonstration is broken. | test package init contains only a docstring. |
| `V1-ISSUE-RISK-004` | Unit tests import removed flat modules and missing `app.agentic.tools.risk`. | `test_import_safety.py`, `test_tools.py`, others | Current test suite cannot be assumed runnable. | exact imports and missing paths. |
| `V1-ISSUE-RISK-005` | Root tool wrapper discards caller-supplied side-effect/approval semantics and reports read-only metadata. | `_common.py::risk_tool_result` | Approval/revocation names can be misclassified as harmless reads. | wrapper builds a fixed read-only spec. |
| `V1-ISSUE-RISK-006` | Root retrieval functions only process caller-supplied data. | `portfolio_tools.py::get_open_positions`, `get_open_orders`, state getters | Function names overstate behavior and can mislead agents/callers. | no broker/database dependency in the facade. |
| `V1-ISSUE-RISK-007` | Catch-all non-zero sizing fallback. | `PositionSizer.calculate_size` | Provider/input bugs can result in `0.1` lots instead of a failed/zero decision. | broad `except Exception: return 0.1`. |
| `V1-ISSUE-RISK-008` | Synthetic pip/notional defaults. | `calculations/math_utils.py` and raw exposure helpers | Non-FX or non-standard contracts can be materially mismeasured. | symbol-text pip heuristic; default contract size 100,000. |
| `V1-ISSUE-RISK-009` | Approval-token replay state is process-local. | `governance/approval_tokens.py::USED_APPROVAL_SIGNATURES` | Restart/multi-worker operation can allow replay not seen by another process. | module-level set. |
| `V1-ISSUE-RISK-010` | Approval tokens hard-code account and broker identifiers. | `create_approval_token` | Token is not truly bound to actual execution account/provider. | `"default-account"` and `"configured-broker"`. |
| `V1-ISSUE-RISK-011` | Execution action governor fabricates approval metrics. | `app/services/execution/trade_action_governor.py` | Execution may appear risk-approved without canonical evaluation. | fixed APPROVE decision and fixed VaR value. |
| `V1-ISSUE-RISK-012` | Multiple canonical-looking engines and namespaces. | `core`, `governance`, `portfolio`, `models/domain`, `simulation/replay`, `safety/governance` | Duplicated ownership, imports and audit surface. | compatibility wrappers and parallel files. |
| `V1-ISSUE-RISK-013` | Inconsistent failure models. | calculations, root tools, engines, API | Some functions raise, some return envelopes, some return infinity, and sizing returns 0.1. | inspected methods. |
| `V1-ISSUE-RISK-014` | Direct broker/MT5 coupling in quantitative/live code. | `PortfolioRiskEngine`, `PositionSizer`, `live/*` | Harder to validate behavior uniformly across live and simulation adapters. | direct provider methods. |
| `V1-ISSUE-RISK-015` | Risk router is conditionally disabled on import failure. | `app/api/main.py` | Broken imports can remove all risk endpoints rather than fail startup visibly. | guarded router import/include. |
| `V1-ISSUE-RISK-016` | Empty public registries despite non-empty modules. | `calculations/__init__.py`, `workflows/__init__.py` | Public boundary is inconsistent and direct leaf imports are required. | empty `__all__`/init. |
| `V1-ISSUE-RISK-017` | Root tool capability duplicates deeper implementations without equivalent data or control depth. | root files versus nested engines | A shallow tool can be chosen instead of a production engine under the same capability name. | duplicate VaR/exposure/sizing/governance names. |
| `V1-ISSUE-RISK-018` | Package mixes unrelated runtime layers. | entire package | One package owns math, broker reads, policy, persistence, reports, replay and agent facades. | 24 structural groups / 180 files. |
| `V1-ISSUE-RISK-019` | Tests alone cover dormant/removed behavior. | risk unit tests | Test volume can overstate production value. | old flat imports and absent runtime callers. |
| `V1-ISSUE-RISK-020` | Forced decisions/manual overrides exist in governance APIs. | `GovernanceEngine.evaluate_transition*`; simulator trade service | Acceptance can be replaced by caller-supplied forced decisions or manual review. | `forced_decision`, `forced_reason`, manual override branch. |

## 13. V1 Capability Catalogue

| Capability ID | Capability | Current implementation | Workflow(s) | Usage status | Value status | Notes |
| ------------- | ---------- | ---------------------- | ----------- | ------------ | ------------ | ----- |
| `V1-CAP-RISK-001` | Position sizing | `calculations/position_sizing.py::PositionSizer` | `V1-WF-RISK-001` | Used | Essential | Six sizing methods; catch-all 0.1 fallback is material. |
| `V1-CAP-RISK-002` | Historical VaR/CVaR | calculations and metric families | `V1-WF-RISK-004/005` | Used/Supporting | Useful | Pure historical helpers plus portfolio covariance engine. |
| `V1-CAP-RISK-003` | Portfolio VaR/ES and risk contribution | `core/portfolio_risk_engine.py` | `V1-WF-RISK-003/004/005/006` | Used | Essential | Broker/simulator-backed. |
| `V1-CAP-RISK-004` | Exposure and concentration | calculations + metrics | `V1-WF-RISK-003/004/005` | Used | Essential | Some raw helpers use synthetic defaults. |
| `V1-CAP-RISK-005` | Margin and drawdown checks | calculations + limits + metrics | `V1-WF-RISK-004/005/006/008` | Used | Essential | Multiple representations exist. |
| `V1-CAP-RISK-006` | Risk policy limits | `limits/*`, `policy/*` | `V1-WF-RISK-004/006/011` | Used | Essential | Pre/post trade plus stress-regime tightening. |
| `V1-CAP-RISK-007` | Portfolio governance decision | `GovernanceEngine` | `V1-WF-RISK-003/004/006` | Used | Essential | Main active governance engine. |
| `V1-CAP-RISK-008` | Proposal-level signed decision | `RiskGovernor` | `V1-WF-RISK-011` | Test-only | Useful | No confirmed main runtime consumer. |
| `V1-CAP-RISK-009` | Approval token issuance/validation | `governance/approval_tokens.py` | `V1-WF-RISK-011` | Test-only | Useful | Process-local replay state; hard-coded account/broker. |
| `V1-CAP-RISK-010` | Decision expiry/change invalidation | `governance/validity.py` | `V1-WF-RISK-009` | Used | Essential | Confirmed execution dependency. |
| `V1-CAP-RISK-011` | Kill-switch state and entry block | `governance/kill_switch.py` | `V1-WF-RISK-010` | Used | Essential | Incident-writing path not confirmed active. |
| `V1-CAP-RISK-012` | Regime detection | `regimes/*` | `V1-WF-RISK-002/005` | Used | Useful | Volatility, liquidity, market and crisis families. |
| `V1-CAP-RISK-013` | Risk metric snapshot | `portfolio/snapshot_builder.py`, `metrics/*` | `V1-WF-RISK-005/007` | Used | Essential | Registry-driven. |
| `V1-CAP-RISK-014` | Risk scorecard | `scoring/*` | `V1-WF-RISK-005/007` | Used | Essential | Registry-driven composite scoring. |
| `V1-CAP-RISK-015` | Stress scenarios | `scenarios/*`, stress metrics | `V1-WF-RISK-005/007` | Used/Supporting | Useful | Feeds snapshot/what-if outputs. |
| `V1-CAP-RISK-016` | Allocation advice | `optimization/allocation_planner.py` | `V1-WF-RISK-003` | Used | Useful | Advisory, not execution. |
| `V1-CAP-RISK-017` | Risk recommendations | optimization engine and helpers | `V1-WF-RISK-005/007` | Used | Useful | Includes rebalance/hedge/capital-efficiency candidates. |
| `V1-CAP-RISK-018` | Replay and timeline reconstruction | `replay/*`, `core/timeline_reconstructor.py` | `V1-WF-RISK-005/007` | Used | Useful | Simulation compatibility path is duplicated. |
| `V1-CAP-RISK-019` | What-if projection | `replay/what_if_engine.py` | `V1-WF-RISK-007` | Used | Essential | Confirmed simulator endpoint behavior. |
| `V1-CAP-RISK-020` | Risk persistence | `storage/*` | `V1-WF-RISK-005/007` | Used | Essential | Snapshot repository/store confirmed; decision/scenario stores less certain. |
| `V1-CAP-RISK-021` | Risk report rendering/export | `reports/*` | none confirmed in main runtime | Test-only | Useful | Plausible but disconnected from primary routes. |
| `V1-CAP-RISK-022` | Live broker risk monitoring | `live/portfolio_manager.py`, `live/safety_checks.py` | `V1-WF-RISK-008` | Used | Essential | Provider-coupled. |
| `V1-CAP-RISK-023` | Public validation facade | `validators/*` | test/supporting | Test-only | Useful | Broad unit coverage; inconsistent boundary adoption. |
| `V1-CAP-RISK-024` | Root threshold-check tools | `governor_tools.py` | `V1-WF-RISK-012` | Test-only | Questionable | Shallow duplicate of canonical governance. |
| `V1-CAP-RISK-025` | Root portfolio calculation tools | `portfolio_tools.py` | `V1-WF-RISK-012` | Test-only | Questionable | Operate only on caller-supplied data. |
| `V1-CAP-RISK-026` | Root allocation tools | `allocation_tools.py` | `V1-WF-RISK-012` | Test-only | Questionable | Deterministic payload/advice only. |
| `V1-CAP-RISK-027` | Root strategy lifecycle tools | `lifecycle_tools.py` | `V1-WF-RISK-012` | Test-only | No demonstrated value | Names imply persistence, but no write occurs. |
| `V1-CAP-RISK-028` | Shadow risk snapshot contracts | `domain/snapshot.py` | shadow feed workflow | Used | Supporting | Consumed by execution shadow feeds. |
| `V1-CAP-RISK-029` | Lazy public builder facade | `api/public.py` | none confirmed | Possibly used | Useful | Separate from root API. |
| `V1-CAP-RISK-030` | Request assembly | `workflows/request_assembler.py` | none confirmed | Unused | No demonstrated value | Medium confidence; no static caller. |

## 14. Audit Conclusions

### Valuable behaviour worth preserving

* Canonical portfolio state normalization and risk snapshot generation.
* Broker/simulator-backed portfolio VaR/ES, margin, concentration and contribution calculations.
* Pre/post-trade governance through `GovernanceEngine` and `PolicyEngine`.
* Simulator-session risk lifecycle, including governance-before-mutation and persisted snapshots.
* What-if analysis, scorecards, scenario metrics and risk recommendations.
* Execution approval expiry/material-change checks.
* Kill-switch blocking of new entries while retaining force-exit capability.
* Live `PortfolioManager` and `SafetyChecker` integration.

### Behaviour that exists but is disconnected or weakly connected

* Signed `RiskGovernor` approval-token workflow.
* Kill-switch incident artifact writing.
* Most report builders/exporters.
* Nested lazy `api` facade.
* Broad validator facade.
* Request assembler.
* Root 50-tool surface.

### Likely dead weight

No item is conclusively labelled dead code because runtime tracing and a complete local checkout were unavailable. The strongest candidates for manual removal review are:

* `workflows/request_assembler.py`;
* redundant `safety` aliases;
* parallel `simulation` leaf implementations if `replay` is canonical;
* compatibility `models` leaf implementations if all callers use `domain`;
* the root lifecycle facade;
* stale test/example-only flat API assumptions.

### Duplicated responsibilities

* Root tools versus layered engines.
* `core` forwarding wrappers versus canonical modules.
* `models` versus `domain`.
* `simulation` versus `replay`.
* `safety` versus governance kill switch.
* `RiskGovernor` versus `GovernanceEngine`.

### Important uncertainties requiring manual confirmation

* Deployment entry points or agent registries outside the accessible revision.
* Whether external repositories import root tools, lazy `api` facades, reports, or request assembler.
* Whether the full unit suite has been intentionally retained for an older branch.
* Whether approval tokens are consumed by an execution service not visible in static searches.
* Whether parallel compatibility files are exact wrappers or divergent copies at runtime.
* Actual test pass/fail and coverage.

### Final validation

* [x] Every Python file found under `app/services/risk` is represented in Sections 3 and 4.
* [x] Root `__init__.py` exports were counted and mapped to their source files.
* [x] Nested `__init__.py` registries were inspected and summarized.
* [x] Callers were searched in API, simulator session, execution, tests and usage examples.
* [x] Inbound and outbound dependencies are summarized.
* [x] Workflows are based on inspected call paths.
* [x] Production/runtime usage is distinguished from tests/examples.
* [x] Uncertain findings are explicitly labelled.
* [x] No Version 2 design or requirements were introduced.
* [x] No source code was changed.

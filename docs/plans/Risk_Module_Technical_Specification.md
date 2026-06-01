# HaruQuant Risk Module Technical Specification

**Document status:** Production requirements baseline v8.0 — single source-of-truth technical specification with institutional risk hardening plus edge-case determinism clarifications for step-down persistence, audit-chain genesis, correlation fallback, limit ordering, and in-flight reconciliation expiry
**Target module:** `tools/risk/`
**Design intent:** Production-grade risk management module with traceable functional and non-functional requirements, deterministic safety gates, and agent-safe tool boundaries
**Primary goal:** Define the complete target risk subsystem for HaruQuant as a clean, production-grade, implementation-ready module
**Date:** 2026-05-31
**Version update:** v8.0 adds edge-case implementation hardening rules on top of v7: deterministic step-down state initialization and restoration, audit-chain genesis constants, production correlation fallback behavior, deterministic limit evaluation order, and in-flight reconciliation grace-period expiry handling.

### Version v8.0 Update Summary

This version extends v7 with implementation-hardening clarifications intended to prevent edge-case bugs during coding:

- deterministic step-down state initialization and persistence restoration on startup
- documented audit-chain genesis rule for the first hash-chained audit record
- default production fallback behavior for insufficient correlation evidence in correlation-adjusted sizing
- strict deterministic limit evaluation order for reproducible `primary_failure_limit` and `composite_breach_flags`
- expiry behavior for live in-flight order reconciliation grace periods

These additions do not change the core architecture. They make the v7 institutional controls safer and more reproducible during implementation.

### Version v7.0 Update Summary

This version extends v6 with institutional-grade risk controls while preserving the same single-document structure. The new requirements add:

- portfolio-level exit-liquidity and forced-liquidation stress evaluation
- explicit correlation-adjusted position sizing rules
- graduated risk step-down controls before hard kill-switch behavior
- live portfolio-state freshness guards and in-flight order tolerance buffers
- cryptographic audit hash chaining for tamper-evident audit logs
- primary failure and composite breach tracking in `RiskDecisionPackage`
- Kelly evidence fallback behavior when statistical evidence is insufficient

These additions are production hardening requirements. They may be feature-flagged during implementation, but contracts, config keys, tests, and acceptance criteria must exist before the risk module is considered production-complete.

### Version v5.0 Update Summary

This version is a clearly versioned output created from the latest v4 baseline. It preserves the full production specification and makes the version distinction explicit. The document includes the dedicated `sizing.py` position-sizing engine, first-class `regimes.py` risk-regime layer, pending-order exposure treatment, Kelly minimum evidence rules, approval-token emergency revocation, config-hash validation, benchmark environment notes, and production hardening requirements.

---

## 1. Executive Summary

The HaruQuant Risk Module is a deterministic, production-grade risk management subsystem for research, simulation, portfolio review, paper trading, and live-trading readiness governance.

This document is the single source-of-truth specification for the HaruQuant risk module. It defines the functional requirements, non-functional requirements, contracts, workflows, public AI-tool surface, safety rules, audit requirements, approval governance, and production acceptance gates required before implementation can be considered complete.

The module must provide:

- canonical risk contracts
- deterministic calculation engines
- explicit policy and limit gates
- auditable risk decisions
- approval-token governance
- kill-switch enforcement
- a narrow official AI-tool surface
- clear separation between risk review, portfolio state, and execution readiness
- high test coverage and benchmarked performance
- fail-closed behavior for safety-critical workflows

The module should feel like a professional risk control layer: predictable, explainable, testable, auditable, and safe for use by HaruQuant agents and execution workflows.

---

## 2. Purpose and Problem Statement

HaruQuant requires a dedicated risk management module that can act as the deterministic safety layer between strategy research, portfolio allocation, execution readiness, and live-trading workflows.

The module must answer core risk questions in a repeatable and machine-verifiable way:

- Is the current portfolio inside configured risk limits?
- Is a proposed trade allowed, rejected, blocked, or approval-required?
- Does a strategy qualify for admission, promotion, demotion, suspension, or retirement?
- Does an allocation proposal increase concentration, margin, drawdown, correlation, or tail risk beyond allowed limits?
- Is the system allowed to proceed toward paper or live execution readiness?
- Is required evidence fresh, complete, and traceable?
- Can the decision be reproduced later from the same inputs, config hash, and evidence references?

The module must not be a loose collection of utilities. It must be a coherent production subsystem with explicit contracts, narrow public APIs, deterministic decision logic, and audit-ready outputs.

The module must support these capabilities:

- portfolio state normalization
- risk snapshots
- exposure calculations
- symbol, currency, strategy, and cluster concentration checks
- VaR and CVaR
- volatility and drawdown checks
- margin and leverage checks
- correlation and cluster risk checks
- trade-frequency and strategy-loss limits
- spread, slippage, session, weekend, overnight, and news blackout checks
- allocation proposals and validation
- dedicated position-sizing engine
- fixed lot, fixed risk, milestone, Kelly, volatility, and fixed-fractional sizing
- risk parity and allocation helpers
- market/volatility/liquidity/crisis regime assessment
- approval tokens and governance signatures
- kill-switch checks
- strategy lifecycle gates
- scenario, replay, what-if, and advisory reporting capabilities
- agent-facing risk tools

---

## 3. Design Principles

The risk module must follow these principles.

### 3.1 Deterministic First

All safety-critical risk decisions must be deterministic. LLM agents may explain, summarize, or recommend, but final risk gates must be enforced by code.

### 3.2 Narrow Public Surface

Only a small number of stable, agent-callable tools should be exported from `tools/risk/__init__.py`. Internal calculators, validators, and engines should remain private to the module unless they are intentionally promoted as official AI tools.

### 3.3 One Canonical Risk Decision

The module must produce one canonical `RiskDecisionPackage` for risk approvals, rejections, warnings, and approval-required states. Workflows and agents should not depend on many incompatible decision formats.

### 3.4 Fail Closed

When evidence is missing, state is invalid, approval is missing, policy is unclear, or a calculation fails, the module must block or reject the action rather than guessing.

### 3.5 No Live Execution Inside Risk

Risk may decide whether a proposed action is allowed, blocked, or needs approval. It must not place trades, close positions, modify live broker state, or override execution tools.

### 3.6 Capability-Complete, Structure-Clean

The module must include all required risk capabilities, but each capability must live behind a clear contract, file responsibility, workflow boundary, and test suite.

### 3.7 Clear Agent Boundary

Agents call official risk tools. Official risk tools call deterministic services. Deterministic services call pure calculators and validators. Internal helpers are not exposed to agents.

### 3.8 Audit Everything Important

Any risk decision, approval token, kill-switch check, live-readiness decision, or strategy lifecycle change must produce audit data.

---

## 4. Scope

### 4.1 In Scope

The risk module owns:

- portfolio risk state construction
- portfolio exposure analysis
- position sizing recommendations
- risk limit checks
- strategy admission checks
- pre-trade risk review
- allocation review
- portfolio-level risk decisions
- approval-token creation and validation
- kill-switch state checks
- risk audit records
- risk report summaries
- scenario and what-if analysis for risk review
- agent-safe risk tools

### 4.2 Out of Scope

The risk module does **not** own:

- market data acquisition
- strategy signal generation
- backtest engine execution
- broker order placement
- position closing
- live account mutation
- UI rendering
- model training
- LLM-based final approval
- database infrastructure outside its repository/storage boundary

### 4.3 Integration Dependencies

The risk module may depend on these domains through stable public interfaces:

| Dependency | Purpose |
|---|---|
| `tools.data` | Market prices, symbol metadata, spreads, calendar/news context when needed. |
| `tools.simulation` | Backtest or validation evidence packages. |
| `tools.portfolio` or internal portfolio contracts | Open positions, strategy allocations, equity curve. |
| `tools.execution` | Read-only open orders/positions only, never direct trade mutation. |
| `tools.governance` or internal governance services | Approval state, audit persistence, policy metadata. |
| `tools.utils` | Logger, standard result helpers, IDs, validators. |

---

## 5. Target Package Structure

The target package should be clear enough to understand mentally without opening 179 files.

```text
tools/risk/
    __init__.py
    contracts.py
    errors.py
    config.py
    calculators.py
    state.py
    limits.py
    governor.py
    approvals.py
    circuit_breakers.py
    lifecycle.py
    sizing.py
    allocation.py
    regimes.py
    scenarios.py
    reports.py
    storage.py
    audit.py
    tools.py
    README.md
```

### 5.1 File Responsibilities

| File | Responsibility |
|---|---|
| `__init__.py` | Official AI-tool registry only. No business logic. |
| `contracts.py` | Pydantic or dataclass contracts for all risk inputs/outputs. |
| `errors.py` | Deterministic risk exceptions and error codes. |
| `config.py` | Risk thresholds, config loading, validation, and config version hash. |
| `calculators.py` | Pure risk math: exposure, VaR, CVaR, volatility, margin, drawdown, correlation. |
| `state.py` | Portfolio state builder, position normalization, risk snapshot builder. |
| `limits.py` | Individual limit checks and limit aggregation. |
| `governor.py` | Canonical risk decision engine. |
| `approvals.py` | Approval tokens, signatures, expiry, validation, and revocation. |
| `circuit_breakers.py` | Graduated risk step-down controls, risk reduction stages, and hard-halt escalation state. |
| `lifecycle.py` | Strategy lifecycle gates: admit, promote, demote, suspend, retire. |
| `sizing.py` | Position sizing engine: fixed lot, fixed risk, milestone, Kelly, volatility, fixed fractional, broker constraints, and sizing result validation. |
| `allocation.py` | Portfolio/strategy allocation proposals, risk parity, rebalance review, and allocation validation. |
| `regimes.py` | Market, volatility, liquidity, correlation, drawdown, crisis, news, and session regime assessment. |
| `scenarios.py` | Stress scenarios, replay/what-if risk analysis. |
| `reports.py` | Markdown/JSON risk report builders. |
| `storage.py` | Optional persistence boundary for snapshots, decisions, and audit records. |
| `audit.py` | Risk audit event schema and writer helpers. |
| `tools.py` | Agent-facing official AI-tool wrappers that call services. |
| `README.md` | Human documentation and usage notes. |

### 5.2 Package Growth Rule

Start with the canonical package structure above and split files only when a clear engineering boundary emerges. A split is justified when one of these conditions is true:

- a file becomes difficult to review or test safely
- a subdomain gains multiple independent contracts or services
- separate ownership, security, persistence, or deployment boundaries appear
- tests and fixtures become clearer with a narrower module boundary
- the split reduces coupling rather than adding indirection

Do not create extra directories merely to make the module look larger. The package should remain simple enough for a human developer or agent to understand without navigating unnecessary layers.

---

## 6. Official AI Tool Surface

The module must expose a small, stable public AI-tool surface that maps to workflows rather than tiny internals.

### 6.1 Required Official AI Tools

The recommended official tools in `tools/risk/__init__.py` are:

```python
__all__ = [
    "build_portfolio_risk_snapshot",
    "review_trade_risk",
    "calculate_position_size",
    "assess_risk_regime",
    "review_strategy_admission",
    "review_allocation_proposal",
    "run_portfolio_risk_governor",
    "create_risk_decision_package",
    "validate_risk_approval_token",
    "check_risk_kill_switch",
    "run_risk_scenario_analysis",
    "generate_risk_report",
]
```

### 6.2 Tool Responsibility Matrix

| Tool | Purpose | Risk Level | Side Effects | Approval Required |
|---|---|---:|---|---|
| `build_portfolio_risk_snapshot` | Build normalized risk snapshot from portfolio state. | low | read-only | no |
| `review_trade_risk` | Pre-trade risk review for a proposed trade. | high | no trade mutation; may create audit record | depends on action |
| `calculate_position_size` | Calculate a deterministic recommended position size using an approved sizing method and broker constraints. | medium/high | read-only; no trade mutation | no unless used to increase risk beyond policy |
| `assess_risk_regime` | Produce deterministic market/portfolio regime assessment used by the governor and reports. | medium | read-only | no |
| `review_strategy_admission` | Decide whether strategy can enter portfolio/paper/live candidate workflow. | high | may create audit record | yes for live candidate |
| `review_allocation_proposal` | Validate allocation and rebalance proposal. | high | may create audit record | yes if allocation increases risk materially |
| `run_portfolio_risk_governor` | Run full portfolio-level governor checks. | high | may create audit record | depends on requested decision |
| `create_risk_decision_package` | Normalize risk findings into canonical decision package. | medium/high | may create artifact | depends on package action |
| `validate_risk_approval_token` | Validate signed risk approval token. | high | read-only | no, validates existing approval |
| `check_risk_kill_switch` | Check current kill-switch state. | critical safety | read-only | no |
| `run_risk_scenario_analysis` | Run stress/what-if analysis. | medium | read-only or local artifact | no |
| `generate_risk_report` | Create human-readable risk report. | medium | writes local report if configured | no |

### 6.3 Tool Standard Requirements

Every official AI tool must comply with the HaruQuant Tool Function Standard:

- module-level docstring
- agent-facing function docstring
- type hints
- `request_id: Optional[str] = None`
- input validation
- output validation
- structured logging through `tools.utils.logger`
- deterministic error codes
- execution timing in `execution_ms`
- standard return schema
- accurate risk metadata
- accurate side-effect metadata
- no `None` returns
- no silent failures
- no raw exceptions returned
- tests and usage examples

---

## 7. Core Contracts

The risk module must define canonical contracts in `contracts.py`. These contracts are the backbone of the system.

### 7.1 Contract Style

Use Pydantic models if available in the project dependency set. If avoiding Pydantic early, use frozen dataclasses plus explicit validators. For production, Pydantic is preferred because risk workflows depend heavily on schema validation.

### 7.2 Required Contracts

```text
RiskConfig
RiskThresholds
PortfolioExitLiquidityConfig
CorrelationAdjustedSizingConfig
RiskStepDownConfig
LiveRiskStateConfig
PositionState
OrderState
StrategyState
PortfolioState
PortfolioRiskSnapshot
ProposedTrade
PositionSizingMethod
PositionSizingRequest
PositionSizingResult
ProposedAllocation
RegimeState
RegimeSignal
RegimeTransition
RegimeAssessment
RiskLimitResult
RiskFinding
RiskDecisionPackage
RiskApprovalToken
KillSwitchState
ScenarioDefinition
ScenarioResult
RiskAuditRecord
RiskReport
```

### 7.3 PositionState

Required fields:

```text
symbol: str
side: "long" | "short"
volume: float
entry_price: float
current_price: float | None
stop_loss: float | None
take_profit: float | None
strategy_id: str | None
asset_class: str = "fx"
currency_base: str | None
currency_quote: str | None
opened_at: datetime | None
unrealized_pnl: float | None
margin_used: float | None
metadata: dict
```

Validation rules:

- `symbol` required and normalized.
- `side` must be long or short.
- `volume` must be positive.
- `entry_price` must be positive.
- `current_price`, if provided, must be positive.
- Stop-loss validation depends on side.

### 7.4 PortfolioState

Required fields:

```text
account_id: str | None
equity: float
balance: float | None
margin_used: float | None
free_margin: float | None
currency: str
positions: list[PositionState]
orders: list[OrderState]
strategy_allocations: dict[str, float]
equity_curve: list[float]
timestamp: datetime
source: "simulation" | "paper" | "live" | "manual"
metadata: dict
```

Validation rules:

- `equity` must be positive.
- `positions` must be valid.
- `orders` must be valid and explicitly classified as market, limit, stop, stop-limit, or unknown where possible.
- `timestamp` required.
- `source` must be explicit.

Pending orders are part of portfolio risk state. The module must not ignore pending orders merely because they are not yet filled. Pending orders must be evaluated as potential future exposure according to the configured pending-order policy.

### 7.5 ProposedTrade

Required fields:

```text
symbol: str
side: "buy" | "sell"
volume: float
entry_price: float | None
stop_loss: float | None
take_profit: float | None
strategy_id: str | None
request_source: "research" | "strategy" | "simulation" | "paper" | "live"
requires_live_execution: bool = False
metadata: dict
```

Validation rules:

- `volume` must be positive.
- If `requires_live_execution=True`, approval flow must be enforced.
- If stop-loss is missing, policy decides whether to block or require explicit exception.

### 7.6 RiskLimitResult

```text
limit_name: str
status: "pass" | "warn" | "fail" | "blocked" | "not_applicable"
severity: "info" | "low" | "medium" | "high" | "critical"
observed_value: float | str | bool | None
threshold: float | str | bool | None
message: str
evidence: list[str]
metadata: dict
```

### 7.7 RiskDecisionPackage

```text
decision_id: str
request_id: str
workflow_id: str | None
decision: "approve" | "reject" | "block" | "warn" | "needs_approval" | "needs_more_evidence"
risk_level: "low" | "medium" | "high" | "critical"
subject_type: "trade" | "strategy" | "allocation" | "portfolio" | "execution" | "scenario"
subject_id: str | None
summary: str
limit_results: list[RiskLimitResult]
findings: list[RiskFinding]
primary_failure_limit: str | None
composite_breach_flags: list[str]
approval_required: bool
approval_token: RiskApprovalToken | None
kill_switch_state: KillSwitchState | None
evidence_refs: list[str]
config_version: str
generated_at: datetime
expires_at: datetime | None
metadata: dict
```

Composite failure tracking rules:

- The governor must set `primary_failure_limit` to the first material limit, policy, evidence, or kill-switch condition that determines the final decision according to decision precedence.
- The governor must populate `composite_breach_flags` with every additional breached limit, missing-evidence condition, stale-evidence condition, approval failure, or advisory warning that is relevant to the same decision.
- Reports and UI summaries must highlight the primary failure first, then disclose composite breaches separately.
- This tracking must be deterministic for the same documented limit evaluation order, config hash, and evidence set.
- The governor must not rely on dictionary order, set order, dynamic plugin order, or unordered iteration when selecting `primary_failure_limit` or populating `composite_breach_flags`.

Decision semantics:

| Decision | Meaning |
|---|---|
| `approve` | Risk conditions passed and no further approval is needed. |
| `warn` | Allowed but has warnings that must be surfaced. |
| `needs_approval` | Deterministic checks allow the action only after required approval. |
| `needs_more_evidence` | Cannot decide because required evidence is missing or stale. |
| `reject` | Risk policy does not allow the action. |
| `block` | Safety-critical block; do not proceed. |

---

## 8. Risk Configuration

### 8.1 Config File

The module should support config-driven thresholds.

Recommended file:

```text
config/risk.yaml
```

or project-level:

```text
configs/risk/default.yaml
configs/risk/prop_firm.yaml
configs/risk/live.yaml
```

### 8.2 Required Risk Thresholds

```yaml
risk_profile_name: prop_firm_default
schema_version: "1.0.0"
account_currency: USD
max_risk_per_trade_pct: 1.0
max_daily_loss_pct: 5.0
max_total_loss_pct: 10.0
monthly_profit_target_pct: 10.0
max_portfolio_var_pct: 3.0
max_portfolio_cvar_pct: 5.0
max_margin_usage_pct: 50.0
max_leverage: 30.0
max_symbol_exposure_pct: 15.0
max_currency_exposure_pct: 35.0
max_strategy_exposure_pct: 20.0
max_correlation_to_portfolio: 0.5
max_open_positions: 30
max_pending_order_distance_pct: 0.25
max_trades_per_day_per_strategy: 10
news_blackout_minutes_before: 10
news_blackout_minutes_after: 10
allow_weekend_holding: false
allow_overnight_holding: restricted
require_stop_loss: true
require_approval_for_live: true
require_approval_for_risk_increase: true

position_sizing:
  default_method: fixed_risk
  allowed_methods:
    - fixed_lot
    - fixed_risk
    - milestone
    - kelly_criterion
    - volatility
    - fixed_fractional
  fixed_lot_default: 0.01
  max_kelly_fraction: 0.25
  kelly_safety_factor: 0.25
  min_kelly_trades: 30
  kelly_sample_window_bars: 1000
  max_capital_fraction_pct: 5.0
  require_stop_loss_for_fixed_risk: true
  clamp_to_broker_limits: true

correlation_adjusted_sizing:
  enabled: false
  max_correlated_leverage: 1.5
  correlation_decay_window_bars: 100
  penalty_method: linear_scale
  marginal_correlation_penalty_threshold: 0.70

portfolio_exit_liquidity:
  enabled: false
  max_concurrent_close_pct: 25.0
  estimated_market_impact_bps: 5.0
  stress_close_horizon_ms: 5000
  apply_to_risk_limits: true
  stress_multiplier: 1.0

risk_step_down:
  enabled: false
  warn_threshold_pct: 70.0
  step1_reduce_size_pct: 80.0
  step2_reject_new_trades_pct: 90.0
  step3_close_all_and_halt_pct: 100.0
  reset_cooldown_bars: 20

live_risk_state:
  portfolio_state_freshness_max_ms: 2500
  in_flight_order_tolerance_pct: 5.0
  reconciliation_grace_period_ms: 5000

audit:
  hash_chain_enabled: true
  hard_fail_live_on_chain_tamper: true

regime:
  enabled: true
  high_volatility_multiplier: 0.5
  low_liquidity_multiplier: 0.5
  crisis_multiplier: 0.0
  drawdown_defensive_multiplier: 0.5
  unknown_regime_live_behavior: block
```

### 8.3 Institutional Hardening Config Blocks

The risk configuration must support optional but production-defined hardening blocks. These blocks may be disabled by default, but they must be represented in contracts, config validation, config hashing, and tests.

Required config contracts:

```text
PortfolioExitLiquidityConfig
CorrelationAdjustedSizingConfig
RiskStepDownConfig
LiveRiskStateConfig
AuditChainConfig
```

Rules:

- Disabled config blocks must still validate deterministically.
- Enabling a hardening block must change the config hash.
- Live-sensitive workflows must record which hardening blocks were enabled during the decision.
- Feature-flagged hardening logic must fail closed when enabled and required evidence is missing.

### 8.4 Config Hash

Every decision package must include a config version or hash. This ensures future audits know exactly which thresholds were used.

Before applying a previously created `RiskDecisionPackage` or validating an approval token for a live-sensitive or execution-sensitive workflow, the risk module must compare the stored config hash with the active risk configuration hash. A mismatch must return `CONFIG_VERSION_MISMATCH` and force a new risk decision. Approval tokens created under an older config may not be reused unless an explicit deterministic compatibility policy is configured and audited.

---

## 9. Calculation Layer

`calculators.py` should contain pure, deterministic calculations. It should not call brokers, databases, files, or agents.

### 9.1 Required Calculators

| Function | Purpose |
|---|---|
| `calculate_position_risk` | Calculates risk amount and percentage for a position or proposed trade. |
| `calculate_notional_exposure` | Calculates notional exposure. |
| `calculate_currency_exposure` | Aggregates FX base/quote exposure. |
| `calculate_symbol_exposure` | Aggregates exposure by symbol. |
| `calculate_strategy_exposure` | Aggregates exposure by strategy. |
| `calculate_portfolio_returns` | Converts equity curve into returns. |
| `calculate_portfolio_volatility` | Estimates portfolio volatility. |
| `calculate_portfolio_var` | Historical or parametric VaR. |
| `calculate_portfolio_cvar` | Historical CVaR / expected shortfall. |
| `calculate_margin_usage` | Calculates margin usage and free-margin safety. |
| `calculate_drawdown` | Current, max, and daily drawdown. |
| `calculate_correlation_matrix` | Calculates correlation matrix for symbols/strategies. |
| `calculate_portfolio_correlation_impact` | Measures proposed trade correlation impact. |
| `detect_symbol_cluster_risk` | Detects concentration in related instruments. |
| `calculate_risk_contribution` | Contribution of each position/strategy to total portfolio risk. |

### 9.2 Calculation Rules

- Calculators return typed internal results, not AI-tool dictionaries.
- Calculators raise deterministic domain exceptions or return explicit result objects.
- Calculators must be easy to unit test.
- No hidden global state.
- No hardcoded thresholds inside calculators.
- Threshold checks belong in `limits.py`.

---

## 10. State and Snapshot Layer

`state.py` owns normalization of raw portfolio information into canonical risk state.

### 10.1 Portfolio State Builder

The state builder should accept:

- positions list
- orders list
- equity/balance/margin details
- strategy allocation map
- equity curve
- symbol metadata
- optional market data context

It should return:

```text
PortfolioState
```

### 10.2 Risk Snapshot Builder

The snapshot builder should accept:

```text
PortfolioState + RiskConfig + optional market data context
```

It should return:

```text
PortfolioRiskSnapshot
```

Snapshot should include:

- total equity
- total notional exposure
- margin usage
- leverage estimate
- symbol exposures
- currency exposures
- strategy exposures
- drawdown state
- VaR/CVaR
- volatility estimate
- correlation summary
- concentration summary
- open risk by strategy
- missing-data warnings
- timestamp
- config version

### 10.3 Snapshot Invariants

- Snapshot must be reproducible from inputs.
- Snapshot must not mutate portfolio state.
- Snapshot must explicitly flag missing data.
- Snapshot must not infer live broker state unless provided by a trusted source.

### 10.4 Pending Order Exposure Policy

Pending orders must be evaluated as potential exposure because an unfilled order can become a live position without another strategy signal.

Required behavior:

- Pending market orders must be treated as full potential exposure.
- Pending limit, stop, and stop-limit orders must be included in potential exposure when they are within the configured execution-distance threshold from current market price.
- The execution-distance threshold must be configurable, for example `max_pending_order_distance_pct`.
- The exposure policy must be configurable as `ignore`, `near_market_only`, `probability_weighted`, or `potential`.
- Live-readiness workflows must not use `ignore` unless explicitly configured and audited.
- Potential pending-order exposure must feed symbol exposure, currency exposure, margin projection, leverage projection, concentration, and cluster-risk checks.
- If order type, price, expiry, or market price is missing, the module must return missing evidence, warn, or block according to workflow risk level.
- The snapshot must separately report filled-position exposure and pending-order potential exposure.

Pending-order assumptions must be visible in `PortfolioRiskSnapshot`, risk decision metadata, and reports.

---

## 11. Limit Engine

`limits.py` owns deterministic limit checks.

### 11.1 Required Limit Checks

| Limit | Required Behavior |
|---|---|
| Daily loss limit | Fail or block if daily drawdown exceeds configured threshold. |
| Total loss limit | Fail or block if total drawdown exceeds threshold. |
| Trade risk limit | Reject if proposed trade exceeds risk-per-trade. |
| Portfolio VaR limit | Reject or warn if VaR exceeds threshold. |
| Portfolio CVaR limit | Reject or warn if CVaR exceeds threshold. |
| Margin usage limit | Block if margin usage exceeds threshold. |
| Leverage limit | Block if leverage exceeds threshold. |
| Symbol exposure limit | Warn/fail if symbol concentration too high. |
| Currency exposure limit | Warn/fail if currency concentration too high. |
| Strategy exposure limit | Warn/fail if strategy allocation too high. |
| Correlation limit | Reject if new trade correlation to portfolio exceeds threshold. |
| News blackout | Block high-impact-event trading within configured window. |
| Spread limit | Reject if spread too wide. |
| Slippage limit | Warn or reject if expected slippage too high. |
| Trade frequency limit | Warn/fail if strategy is overtrading. |
| Weekend/overnight limit | Enforce holding restrictions. |
| Kill switch | Always block live or risk-increasing action if active. |

### 11.2 Limit Result Standard

Every limit check returns `RiskLimitResult`.

It must contain:

- limit name
- status
- severity
- observed value
- threshold
- human-readable message
- evidence references
- metadata

### 11.3 Deterministic Limit Evaluation Order

`limits.py` must execute risk limit checks in a strictly documented and deterministic order. This is required so `primary_failure_limit`, `composite_breach_flags`, audit records, reports, and golden tests remain reproducible.

Required behavior:

- Limit evaluation order must be declared as an explicit ordered sequence, list, tuple, or equivalent deterministic registry.
- The governor must not rely on unordered dictionaries, sets, filesystem discovery order, dynamic import order, or plugin discovery order for safety-critical limit sequencing.
- Any new limit added to the system must declare its position in the evaluation order and must include a regression test proving that `primary_failure_limit` remains stable when multiple limits breach simultaneously.
- The deterministic order must be documented in `limits.py` and reflected in decision truth-table tests.
- Composite breach tracking must include all breached limits, but the primary failure must be selected from the deterministic order after decision precedence is applied.

### 11.4 Limit Aggregation

The governor should aggregate limit results using deterministic precedence:

```text
blocked > fail > needs_more_evidence > warn > pass
```

### 11.4 Portfolio Exit Liquidity and Stress Close Limits

When `portfolio_exit_liquidity.enabled=true`, the risk module must evaluate whether the portfolio can be reduced or closed under stressed liquidity assumptions without breaching configured risk limits.

Required behavior:

- Calculate `stressed_var` and `stressed_max_drawdown` by applying estimated market impact and close-horizon assumptions to open positions.
- Include spread widening, expected slippage, and estimated market-impact bps when evidence is available.
- Compare stressed metrics against configured VaR, CVaR, drawdown, and margin thresholds.
- Emit `PORTFOLIO_EXIT_LIQUIDITY_RISK` when stressed liquidation metrics exceed configured limits.
- Downgrade the governor decision to `needs_approval`, `reject`, or `block` according to workflow risk level and config.
- Include exit-liquidity assumptions and stress-close horizon in snapshot, decision, report, and audit metadata.
- Fail closed for live-sensitive workflows when exit-liquidity stress is mandatory but required evidence is missing.


---

## 12. Risk Governor

`governor.py` is the canonical decision engine.

### 12.1 Governor Responsibilities

The Risk Governor must:

- validate inputs
- load/accept risk config
- build or accept a portfolio risk snapshot
- run required limit checks
- enforce kill-switch state
- enforce approval requirements
- produce a canonical `RiskDecisionPackage`
- emit audit event metadata
- fail closed on missing or invalid evidence

### 12.2 Governor Non-Goals

The Risk Governor must not:

- place trades
- close trades
- modify broker state
- override kill switch
- approve itself
- invent portfolio state
- invent backtest evidence
- silently ignore missing data

### 12.3 Governor Modes

| Mode | Purpose |
|---|---|
| `research` | Advisory risk review. No live consequences. |
| `simulation` | Backtest/simulation risk review. |
| `paper` | Paper-trading admission/review. |
| `live_readiness` | Determines whether live execution request can proceed to approval. |
| `live_guard` | Final pre-execution risk gate. Must fail closed. |

### 12.5 Live State Freshness and In-Flight Order Tolerance

In `live_guard` and other live-sensitive modes, the governor must validate that portfolio/account state is fresh enough to support a decision.

Required behavior:

- If `portfolio_state.timestamp` age exceeds `portfolio_state_freshness_max_ms`, return `needs_more_evidence` or `block` according to workflow policy.
- In-flight orders must be represented in the risk state and flagged separately from settled positions.
- During reconciliation grace periods, exposure that exceeds a configured hard limit plus `in_flight_order_tolerance_pct` must return `needs_approval` or `block`.
- The decision package must disclose when `in_flight_tolerance_used=true`.
- Tolerance buffers must never permit kill-switch, max-total-loss, or prohibited-action overrides.
- Reconciliation grace behavior must be auditable and deterministic.
- If `reconciliation_grace_period_ms` expires and in-flight orders remain unresolved, the governor must trigger or require a forced portfolio-state refresh from the configured trusted source before producing a live-sensitive decision.
- If the forced refresh still shows unresolved exposure beyond configured tolerance, the decision must be downgraded to `block` or `needs_approval` according to config and workflow risk level.
- Expired grace-period behavior must emit `IN_FLIGHT_RECONCILIATION_EXPIRED` in findings, audit records, and decision metadata.

### 12.4 Governor Decision Logic

1. Validate request.
2. Validate portfolio state.
3. Validate risk configuration.
4. Check kill switch.
5. Build risk snapshot.
6. Run required limit checks.
7. Check missing/stale evidence.
8. Determine decision by precedence.
9. Determine approval requirement.
10. Attach approval token only when policy permits.
11. Return `RiskDecisionPackage`.
12. Emit audit event.

---

## 13. Approval and Governance

`approvals.py` owns approval tokens and deterministic approval checks.

### 13.1 Approval Token Requirements

A `RiskApprovalToken` must include:

```text
token_id
subject_type
subject_id
approved_action
approved_by
approved_at
expires_at
risk_decision_id
config_version
signature
revoked
metadata
```

### 13.2 Approval Rules

Approval is required for:

- live trading request
- strategy promotion to live candidate
- risk budget increase
- allocation increase beyond threshold
- overriding a warning to proceed
- any high-risk or critical state transition

Approval is never allowed for:

- LLM override of kill switch
- hidden live execution
- broker action without execution gate
- missing portfolio evidence
- stale approval token
- mismatched subject/action token

### 13.3 Token Validation

Validation must check:

- signature validity
- expiry
- revocation status
- subject match
- action match
- config hash compatibility
- current active config hash compatibility
- decision ID match
- approval authority

Failure returns deterministic error code, not ambiguous text.

### 13.4 Emergency Revocation

When the kill switch is activated, the approval subsystem must revoke or invalidate all outstanding approval tokens within the affected scope.

Required behavior:

- global kill switch revokes or invalidates all outstanding live-sensitive approvals
- account kill switch revokes or invalidates approvals for that account
- strategy kill switch revokes or invalidates approvals for that strategy
- symbol kill switch revokes or invalidates approvals for that symbol where applicable
- emergency revocation must be auditable
- validation must fail for tokens affected by emergency revocation
- token validation must check emergency revocation state before returning success

---

## 14. Kill Switch

The kill switch is a critical safety boundary.

### 14.1 Kill Switch State

```text
state: "inactive" | "active" | "partial" | "unknown"
reason: str | None
activated_at: datetime | None
activated_by: str | None
scope: "global" | "strategy" | "symbol" | "account"
metadata: dict
```

### 14.2 Kill Switch Rules

- `active` always blocks risk-increasing and live-related action.
- `unknown` must fail closed for live-related actions.
- LLM agents may not override kill switch.
- Override requires deterministic governance procedure outside normal agent flow.
- Every kill-switch check must be auditable.

---

## 14.5 Graduated Risk Step-Down Controls

`circuit_breakers.py` owns graduated risk step-down controls before hard kill-switch behavior. The goal is to reduce portfolio risk progressively as loss, volatility, liquidity, or exposure pressure worsens, rather than waiting for a binary hard halt.

### 14.5.1 Step-Down Stages

The module must support these stages when `risk_step_down.enabled=true`:

| Stage | Trigger | Required Behavior |
|---|---|---|
| `normal` | Below warning threshold | Normal risk limits apply. |
| `warning` | At or above `warn_threshold_pct` of max daily loss or configured stress threshold | Decision may remain allowed, but warning must be surfaced and audited. |
| `size_reduced` | At or above step 1 threshold | Maximum new position size must be reduced by configured multiplier. |
| `new_trades_rejected` | At or above step 2 threshold | New risk-increasing trades must be rejected unless explicit policy allows exception. |
| `close_all_and_halt` | At or above step 3 threshold | Risk-increasing actions are blocked and kill-switch/halt workflow is triggered. |

### 14.5.2 Step-Down Rules

- Step-down evaluation must run before hard circuit breakers and before final governor decision selection.
- Each transition must create a `RISK_STEP_DOWN_TRIGGERED` audit/journal event.
- Step-down state must include previous stage, new stage, trigger metric, observed value, threshold, timestamp, config hash, and evidence references.
- Step-down state may only clear after `reset_cooldown_bars` or equivalent configured cooldown has passed without further breaches.
- Live-sensitive workflows must treat unknown step-down state as `needs_more_evidence` or `block` according to config.
- Step-down controls must never authorize a trade that would otherwise breach a hard risk limit.

### 14.5.3 Step-Down State Initialization and Persistence

`circuit_breakers.py` must define deterministic startup behavior for step-down state. Step-down state must survive repeated `live_guard` calls and must not reset silently during process restarts.

Required behavior:

- On cold start with no valid persisted state, the default step-down stage is `normal`.
- If a prior persisted step-down state exists and remains inside the configured cooldown window, the module must restore that state before accepting live-sensitive decisions.
- If a prior persisted state exists but is expired, invalid, incompatible with the current config hash, or outside the cooldown window, the module must log and audit `RISK_STEP_DOWN_STATE_RESET` and default to `normal`.
- The restored state must include stage, trigger metric, observed value, threshold, timestamp, config hash, and evidence references.
- Live-sensitive workflows must treat unreadable or corrupted persisted step-down state as `needs_more_evidence` or `block` according to config.
- Step-down state initialization, restoration, expiry, reset, and corruption handling must be covered by deterministic unit and failure-path tests.

---

## 15. Strategy Lifecycle Risk Gates

`lifecycle.py` controls risk admission and promotion state transitions.

### 15.1 Lifecycle States

```text
research
candidate
backtested
robustness_passed
paper_candidate
paper_active
live_candidate
live_approved
live_active
suspended
retired
rejected
```

### 15.2 Lifecycle Actions

| Action | Required Risk Gate |
|---|---|
| Admit strategy to portfolio watchlist | Basic risk profile review. |
| Promote to paper candidate | Validation evidence + allocation review. |
| Promote to live candidate | Backtest, robustness, paper performance, risk decision, approval required. |
| Activate live | Execution readiness + valid approval token + kill switch inactive. |
| Suspend strategy | Always allowed by safety policy; audit required. |
| Retire strategy | Allowed with audit. |
| Demote strategy | Allowed with audit. |

### 15.3 Lifecycle Requirements

The module must implement these lifecycle concepts:

- promote to paper
- promote to live candidate
- demote to paper
- suspend
- retire
- update strategy status
- strategy allocation validation

But they must be organized through one canonical lifecycle interface instead of many loosely related wrappers.

---


## 16. Position Sizing Engine

`sizing.py` owns all deterministic position sizing logic for the risk module.

Position sizing belongs in the risk module because it is a risk-budget decision. Simulation, paper trading, and live execution must call the same sizing engine instead of maintaining separate sizing logic. This prevents backtests from using one sizing method while live-readiness or paper trading uses another.

### 16.1 Sizing Ownership Rule

The ownership split is:

```text
tools/risk/sizing.py
  -> calculates recommended position size

tools/risk/governor.py
  -> decides whether the sized trade is allowed, rejected, blocked, or approval-required

tools/simulation/
  -> consumes risk sizing results during simulation
  -> simulates fills, spread, slippage, commission, and execution behavior

tools/execution/
  -> receives already-approved execution instructions
  -> does not calculate risk budgets
```

### 16.2 Required Position Sizing Methods

The sizing engine must support:

| Method | Required Behavior |
|---|---|
| `fixed_lot` | Return a fixed lot size after broker min/max/step constraints. |
| `fixed_risk` | Calculate lot size so the configured risk amount or risk percent is lost if stop-loss is hit. |
| `milestone` | Select size from an account balance/equity milestone table. |
| `kelly_criterion` | Calculate conservative Kelly fraction from win probability and payoff evidence, capped by config. |
| `volatility` | Calculate size from volatility or ATR-adjusted stop distance. |
| `fixed_fractional` | Allocate fixed percentage of account capital/notional to a trade. |

### 16.3 Sizing Calculation Rules

- Sizing calculations must be deterministic.
- Sizing calculations must not mutate portfolio, broker, or execution state.
- Sizing calculations must not place or close trades.
- Sizing must validate all external inputs before calculation.
- Sizing must apply broker constraints: minimum lot, maximum lot, lot step, contract size, tick size, tick value, and symbol trading constraints where available.
- Sizing must apply risk policy constraints: max risk per trade, max notional exposure, max margin, max leverage, max symbol concentration, and max strategy exposure where applicable.
- Sizing must disclose all assumptions and constraints applied.
- Sizing must return structured warnings when the final clamped size differs from the raw mathematical size.
- If a method requires stop-loss, value-per-point, volatility, win-rate, payoff, or conversion-rate evidence and that evidence is missing, sizing must return a deterministic missing-evidence result.

### 16.3a Correlation-Adjusted Sizing Rules

When `correlation_adjusted_sizing.enabled=true`, the position sizing engine must adjust candidate size based on marginal portfolio correlation before the governor evaluates the trade.

Required behavior:

- The sizer must use the candidate trade, existing portfolio exposures, and configured correlation lookback to calculate marginal correlation.
- If `marginal_corr` exceeds `marginal_correlation_penalty_threshold`, the raw size must be reduced according to the configured `penalty_method`.
- For `linear_scale`, the default penalty is `adjusted_size = raw_size * max(0, 1 - marginal_corr)`.
- For `hard_cap`, the adjusted size must not exceed the max size implied by `max_correlated_leverage`.
- For `volatility_overlay`, the correlation penalty must be applied after volatility sizing and before broker lot-step clamping.
- Final size must still pass hard leverage, margin, symbol, strategy, and portfolio limits.
- The result must include `SIZING_CORRELATION_PENALTY_APPLIED` when a penalty changes the proposed size.
- Missing or insufficient correlation evidence must return `needs_more_evidence`, warn, or fall back according to config; live-sensitive workflows must fail closed when correlation-adjusted sizing is mandatory.
- Production default: if correlation lookback data is insufficient, meaning fewer than the configured minimum observations, the sizing engine must fall back to unadjusted sizing with warning `SIZING_CORRELATION_FALLBACK_UNAVAILABLE` for non-live/advisory workflows.
- Live-sensitive workflows must treat insufficient correlation evidence as `needs_more_evidence` unless config explicitly allows fallback for that workflow mode.
- Any correlation fallback must disclose minimum required observations, observed observations, configured lookback, candidate symbol, affected portfolio symbols, and whether the fallback changed the final size.

### 16.4 Method-Specific Rules

#### fixed_lot

Use when the workflow wants a constant lot size.

Required:

- `fixed_lot`
- broker min/max/step constraints when available

Rules:

- reject negative or zero fixed lot
- clamp or reject if above max lot depending config
- return warning if clamped

#### fixed_risk

Use when the workflow wants to risk a fixed account percentage or fixed money amount.

Required:

- account equity
- risk percent or risk amount
- entry price
- stop-loss price
- symbol tick/pip value or equivalent metadata
- conversion rate when risk currency differs from account currency

Rules:

- stop distance must be positive
- risk amount must be positive and below configured caps
- missing stop-loss must fail when `require_stop_loss_for_fixed_risk=true`
- missing required stop-loss must emit `MISSING_STOP_LOSS`
- result must show stop distance, value per point, raw size, and clamped size

#### milestone

Use when lot size scales at configured equity or balance milestones.

Required:

- account equity or balance
- milestone table

Rules:

- milestone table must be sorted or normalized deterministically
- ambiguous overlapping milestone ranges are invalid
- final size must still pass broker and risk constraints

#### kelly_criterion

Use only when strategy statistics are available and validated.

Required one of:

- win rate + reward/risk ratio
- average win + average loss + win rate

Required sample evidence:

- total trade count used to derive win rate and payoff ratio
- sample period or evidence reference
- source of statistics, for example backtest, walk-forward, paper trading, or live history

Rules:

- full Kelly is not allowed by default
- apply `kelly_safety_factor`
- cap by `max_kelly_fraction`
- reject invalid win rate, negative payoff, or insufficient sample metadata
- reject Kelly sizing when the trade sample is below configured `min_kelly_trades`; default baseline: 30 trades
- emit `INSUFFICIENT_K_EVIDENCE` when Kelly evidence does not meet minimum sample requirements
- when configured fallback is enabled, fall back to `fixed_risk` and emit `SIZING_FALLBACK_TO_FIXED_RISK`; when fallback is disabled, reject the sizing request
- output must disclose Kelly assumptions, sample size, evidence source, safety factor, and cap applied

#### volatility

Use when sizing should decrease as ATR or volatility increases.

Required:

- account equity or risk amount
- ATR or volatility value
- volatility multiplier or volatility stop distance rule
- symbol value-per-point metadata

Rules:

- volatility must be positive
- volatility lookback and timeframe must be included in evidence metadata
- missing volatility evidence returns `needs_more_evidence`
- missing required ATR/volatility evidence must emit `INSUFFICIENT_VOLATILITY_EVIDENCE`

#### fixed_fractional

Use when allocating fixed percentage of capital/notional.

Required:

- account equity or capital base
- capital fraction
- entry price
- contract size or unit multiplier

Rules:

- capital fraction must be within configured cap
- result must still be checked by margin, leverage, and concentration limits
- fixed fractional sizing is not automatically equivalent to fixed risk because stop-loss distance may be unknown

### 16.5 Sizing and Governor Relationship

Sizing does not approve trades.

Correct workflow:

```text
PositionSizingRequest
  -> sizing.py calculates PositionSizingResult
  -> ProposedTrade is built using clamped_size
  -> governor.py reviews full trade and portfolio impact
  -> RiskDecisionPackage determines approve/reject/block/needs_approval
```

A valid `PositionSizingResult` means only:

```text
"the requested sizing method was calculated successfully"
```

It does not mean:

```text
"the trade is approved"
```

### 16.6 Sizing Tool

`calculate_position_size` may be exposed as an official AI tool if agents need direct sizing recommendations.

Tool requirements:

- standard HaruQuant tool response schema
- `request_id`
- structured logging
- deterministic error codes
- metadata and side-effect flags
- `places_trade=False`
- `read_only=True`
- no broker mutation
- no hidden approval

---

## 17. Risk Regime Layer

`regimes.py` owns deterministic risk regime assessment.

The regime layer classifies the current market and portfolio environment so the governor can adjust limits, risk multipliers, approval requirements, and blocking behavior.

### 17.1 Regime Ownership Rule

The regime layer owns classification only. It does not approve trades and does not execute actions.

Correct workflow:

```text
PortfolioState + MarketContext + RiskConfig
  -> regimes.py creates RegimeAssessment
  -> state.py includes RegimeAssessment in PortfolioRiskSnapshot
  -> limits.py applies regime-adjusted thresholds
  -> governor.py decides approve/reject/block/needs_approval
```

### 17.2 Required Regime Detectors

| Detector | Purpose |
|---|---|
| Market regime detector | Classifies trend/range/dislocation environment when evidence is supplied. |
| Volatility regime detector | Identifies low, normal, high, and extreme volatility states. |
| Liquidity regime detector | Identifies wide spread, thin liquidity, or abnormal execution-cost states. |
| Correlation regime detector | Identifies correlation clustering or correlation breakdown. |
| Drawdown regime detector | Identifies normal, caution, restricted, and defensive portfolio states. |
| Crisis regime detector | Identifies crisis or extreme stress state from configured signals. |
| News regime detector | Identifies news blackout and high-impact-event proximity. |
| Session regime detector | Identifies restricted session, overnight, weekend, or market-closed state. |

### 17.3 Regime-Adjusted Risk Rules

The regime layer may affect risk decisions through deterministic configuration only:

- reduce maximum risk per trade
- reduce maximum position size
- reduce max open positions
- increase approval requirements
- block new risk during crisis or active blackout
- force `needs_more_evidence` when regime evidence is mandatory but stale
- force `block` when live workflow regime state is `unknown` and policy says fail closed

### 17.4 Regime Transition Rules

Every material transition must be auditable:

```text
previous_regime
new_regime
transition_reason
triggering_evidence
as_of
config_hash
request_id
```

Regime transitions must not be inferred from model text. They must come from deterministic signals and thresholds.

### 17.5 Regime and Reporting

Risk reports and decision packages must include:

- primary regime
- active regime dimensions
- regime risk multiplier
- regime warnings
- missing regime evidence
- regime-adjusted limits applied
- regime transition summary where relevant

---

## 18. Allocation Engine

`allocation.py` owns portfolio and strategy allocation proposals. It does not own per-trade position sizing.

### 18.1 Required Capabilities

- strategy allocation proposal
- portfolio rebalance proposal
- risk parity weights
- max allocation per strategy
- max allocation per symbol/currency cluster
- allocation validation
- before/after exposure comparison
- before/after VaR/CVaR/margin/correlation review

### 18.2 Allocation Rules

- Allocation recommendations are not execution instructions.
- Every allocation increase must be reviewed by the governor.
- Allocation tools must disclose constraints and assumptions.
- Correlation and margin must be considered before approving new allocation.
- Risk parity output must be bounded by configured caps.
- Per-trade sizing must call `sizing.py`; allocation must not duplicate sizing formulas.



---

## 19. Scenario, Replay, and What-If Analysis

`scenarios.py` owns stress and what-if analysis.

### 17.1 Required Capabilities

- USD shock scenario
- JPY spike scenario
- volatility expansion scenario
- spread widening scenario
- correlation breakdown scenario
- margin stress scenario
- strategy drawdown replay
- proposed trade impact analysis
- before/after portfolio comparison

### 17.2 Scenario Result

Scenario results must include:

- scenario name
- input assumptions
- affected positions/strategies
- equity impact
- margin impact
- VaR/CVaR impact
- exposure impact
- limit failures
- recommendation
- confidence/assumption notes

### 17.3 Advisory Boundary

Scenario output is advisory unless passed through the governor for an actual risk decision.

---

## 20. Reporting

`reports.py` creates human-readable summaries.

### 18.1 Required Reports

- portfolio risk snapshot report
- risk decision report
- strategy admission report
- allocation review report
- scenario analysis report
- live-readiness risk report

### 18.2 Report Formats

Supported formats:

- Markdown
- JSON-compatible dict

Optional later:

- PDF export through a separate docs/reporting pipeline
- UI-friendly schema

### 18.3 Report Rules

Reports must separate:

- observed evidence
- calculated metrics
- limit results
- assumptions
- warnings
- decisions
- approval requirements

Reports must not invent missing evidence.

Every risk decision report must include a plain-language explanation of the primary reason for `reject` or `block`. The explanation must reference the specific limit, rule, policy, kill-switch state, missing evidence, or approval failure that caused the decision, and it must be understandable to a non-expert user without hiding the technical evidence.

---

## 21. Storage and Audit

### 19.1 Storage Boundary

`storage.py` should be optional and replaceable. It may start with JSONL or local file storage, then later move to SQLite/PostgreSQL.

Stored items:

- risk snapshots
- risk decisions
- approval tokens
- scenario results
- audit records

### 19.2 Audit Records

Every important risk operation should create a `RiskAuditRecord`.

Required fields:

```text
timestamp
request_id
workflow_id
action
subject_type
subject_id
risk_decision_id
decision
risk_level
config_version
limit_results_summary
approval_required
approval_token_id
kill_switch_state
errors
evidence_refs
execution_ms
metadata
```

### 19.3 Cryptographic Audit Chaining

When audit hash chaining is enabled, every `RiskAuditRecord` must be tamper-evident.

Required audit chain fields:

```text
previous_hash: str | None
record_hash: str
canonical_payload_hash: str
chain_version: str
```

Rules:

- `record_hash` must be computed from `previous_hash + canonical_json(current_payload)` using SHA-256 or stronger.
- The first audit record in a run, session, account scope, or configured audit chain must use a documented genesis value for `previous_hash`. The default genesis value is `0000000000000000000000000000000000000000000000000000000000000000` unless the deployment config defines a different constant.
- The genesis value must be included in audit-chain verification tests and must not be generated randomly.
- Audit payloads must use deterministic canonical JSON serialization before hashing.
- Audit chain verification must run on load or before live-sensitive workflows when configured.
- If chain verification fails, emit `AUDIT_CHAIN_TAMPER_DETECTED`.
- Live-sensitive workflows must hard-fail when audit chain integrity is required and verification fails.
- Research-only workflows may return a warning when audit chain verification is unavailable, according to config.

### 19.4 Redaction

Audit logs must not store:

- broker passwords
- API keys
- account passwords
- private tokens
- unnecessary raw user content

---

## 22. Error Codes

Use deterministic error codes so agents and workflows can reason about failures.

### 20.1 Risk Error Codes

```text
INVALID_INPUT
INVALID_PORTFOLIO_STATE
INVALID_RISK_CONFIG
MISSING_EVIDENCE
STALE_EVIDENCE
LIMIT_FAILED
POLICY_BLOCKED
KILL_SWITCH_ACTIVE
KILL_SWITCH_UNKNOWN
APPROVAL_REQUIRED
APPROVAL_TOKEN_INVALID
APPROVAL_TOKEN_EXPIRED
APPROVAL_TOKEN_REVOKED
CONFIG_VERSION_MISMATCH
MISSING_STOP_LOSS
INSUFFICIENT_VOLATILITY_EVIDENCE
INSUFFICIENT_K_EVIDENCE
LIVE_STATE_STALE
IN_FLIGHT_TOLERANCE_EXCEEDED
CALCULATION_FAILED
SNAPSHOT_BUILD_FAILED
GOVERNOR_DECISION_FAILED
REPORT_GENERATION_FAILED
STORAGE_ERROR
TOOL_EXECUTION_FAILED
UNKNOWN_ERROR
```

### 20.2 Error Handling Rules

- Internal services may raise domain exceptions.
- Official AI tools must catch domain exceptions and return standard tool responses.
- Unknown exceptions must be logged and converted into `TOOL_EXECUTION_FAILED` or `UNKNOWN_ERROR`.
- Failures must not be swallowed.

---

## 23. Agent Integration

### 21.1 Agent Usage Model

Agents should call risk tools only through:

```python
from tools.risk import review_trade_risk
from tools.risk import run_portfolio_risk_governor
```

Agents must not import:

```python
from tools.risk.calculators import calculate_portfolio_var
```

unless the function has intentionally been exposed as an official tool.

### 21.2 Risk Agent Role

The Risk Agent may:

- request risk snapshots
- ask for risk governor decisions
- explain risk findings
- summarize approval requirements
- package evidence for human review

The Risk Agent must not:

- approve live trading by itself
- override deterministic governor decisions
- override kill switch
- invent missing evidence
- bypass approval tokens

### 21.3 Standard Tool Response

Every official risk tool returns:

```python
{
    "status": "success" | "error",
    "message": str,
    "data": Any,
    "error": None | {
        "code": str,
        "details": str,
    },
    "metadata": {
        "tool_name": str,
        "tool_version": str,
        "tool_category": "risk",
        "tool_risk_level": str,
        "request_id": str | None,
        "execution_ms": float,
        "read_only": bool,
        "writes_file": bool,
        "modifies_database": bool,
        "places_trade": False,
        "requires_network": bool,
    },
}
```

No risk tool should ever set `places_trade=True`. Execution belongs to `tools.execution`.

---

## 24. Workflow Specifications

### 22.1 Portfolio Risk Snapshot Workflow

```text
Input portfolio/account/equity data
  -> validate raw input
  -> normalize into PortfolioState
  -> calculate exposure, drawdown, margin, VaR/CVaR, correlation
  -> produce PortfolioRiskSnapshot
  -> optionally store snapshot
  -> return standard tool response
```

### 22.2 Pre-Trade Risk Review Workflow

```text
ProposedTrade + PortfolioState + RiskConfig
  -> validate trade
  -> check kill switch
  -> build current snapshot
  -> calculate proposed impact
  -> run limit checks
  -> determine approve/reject/block/needs_approval
  -> create RiskDecisionPackage
  -> write audit record
  -> return standard tool response
```

### 22.3 Strategy Admission Workflow

```text
Strategy evidence package + PortfolioState + RiskConfig
  -> validate evidence completeness
  -> validate backtest/robustness/paper requirements based on target lifecycle state
  -> evaluate strategy exposure and overlap
  -> evaluate allocation impact
  -> run governor
  -> return RiskDecisionPackage
```

### 22.4 Allocation Review Workflow

```text
ProposedAllocation + PortfolioState + RiskConfig
  -> validate allocation proposal
  -> calculate before/after exposure
  -> calculate before/after VaR/CVaR/margin/correlation
  -> run allocation limits
  -> determine decision
  -> return RiskDecisionPackage
```

### 22.5 Live Readiness Workflow

```text
Execution request + RiskDecisionPackage + ApprovalToken + KillSwitchState
  -> validate existing risk decision
  -> validate approval token
  -> validate token expiry and subject/action match
  -> check kill switch
  -> confirm no stale evidence
  -> return allow/block decision to execution layer
```

The risk module returns readiness only. It does not place trades.

---

## 25. Testing Specification

The risk module must be test-first.

### 23.1 Test Layout

```text
tests/unit/tools/risk/
    test_contracts.py
    test_config.py
    test_calculators.py
    test_state.py
    test_limits.py
    test_governor.py
    test_approvals.py
    test_lifecycle.py
    test_sizing.py
    test_allocation.py
    test_regimes.py
    test_scenarios.py
    test_reports.py
    test_tools.py

tests/usage/tools/risk/
    risk_workflow_example.py
    pre_trade_review_example.py
    strategy_admission_example.py
    position_sizing_example.py
    allocation_review_example.py

tests/integration/risk/
    test_pre_trade_workflow.py
    test_strategy_lifecycle_workflow.py
    test_live_readiness_workflow.py

tests/failure/risk/
    test_fail_closed_behavior.py
    test_missing_evidence.py
    test_stale_approval_token.py

tests/security/risk/
    test_kill_switch_cannot_be_overridden.py
    test_agent_cannot_approve_live_execution.py
```

### 23.2 Minimum Unit Test Coverage

Coverage must remain above 80%, with higher practical coverage for core risk gates.

Required tests:

- valid and invalid contract inputs
- config loading and hash stability
- exposure calculations
- VaR/CVaR calculations
- margin calculations
- drawdown calculations
- correlation/concentration calculations
- limit pass/warn/fail/block results
- governor approve/reject/block decisions
- missing evidence behavior
- kill-switch active behavior
- approval token creation/validation/expiry/revocation
- lifecycle state transitions
- allocation proposal validation
- official tool response schema
- official tool metadata correctness
- error code correctness
- logging/audit emission

### 23.3 Golden Behavior and Regression Tests

Create deterministic golden tests for important risk behaviors:

- governor decision output semantics
- exposure calculation expected values
- margin calculation expected values
- VaR/CVaR expected values
- fixed-lot sizing expected values
- fixed-risk sizing expected values
- milestone sizing expected values
- Kelly criterion sizing expected values
- volatility sizing expected values
- fixed-fractional sizing expected values
- risk-parity weight expected values
- regime classification expected values
- regime transition expected values
- strategy promotion/demotion semantics
- kill-switch check semantics

These tests define the required behavior of the target module and protect it against future regressions.

---

## 26. Production Acceptance Criteria

The risk module is production-ready only when all checklist items pass.

### 24.1 Architecture

- [ ] Package structure is clear, compact, and responsibility-driven.
- [ ] Official public API is intentionally narrow.
- [ ] Internal calculators are separated from AI tools.
- [ ] Live execution is not inside risk module.
- [ ] Risk decisions are deterministic.
- [ ] Position sizing is owned by `sizing.py`, not simulation or allocation.
- [ ] Regime assessment is owned by `regimes.py` and consumed by the governor.
- [ ] Policy and approval are not prompt-only.
- [ ] Kill switch fails closed.

### 24.2 Contracts

- [ ] Canonical contracts exist.
- [ ] Contracts validate required fields.
- [ ] Risk decision package is the standard output for risk decisions.
- [ ] Config version/hash appears in decisions.
- [ ] Missing/stale evidence is represented explicitly.

### 24.3 Tools

- [ ] `tools/risk/__init__.py` only exports approved AI tools.
- [ ] No implementation logic exists in `__init__.py`.
- [ ] Every official AI tool follows the HaruQuant Tool Function Standard.
- [ ] Every official AI tool accepts `request_id`.
- [ ] Every official AI tool returns standard response schema.
- [ ] Every official AI tool has accurate risk and side-effect metadata.
- [ ] No risk tool places trades.

### 24.4 Governance and Safety

- [ ] Approval tokens are signed or otherwise tamper-evident.
- [ ] Approval tokens expire.
- [ ] Approval tokens can be revoked.
- [ ] Live-readiness checks require valid approval.
- [ ] Kill switch cannot be overridden by an agent.
- [ ] Missing approval fails closed.
- [ ] Unknown kill-switch state fails closed for live actions.

### 24.5 Testing

- [ ] Unit tests exist for every non-trivial file.
- [ ] Tool tests exist for every official AI tool.
- [ ] Usage examples exist for every core workflow.
- [ ] Integration tests cover pre-trade, position sizing, regime assessment, allocation, lifecycle, and live-readiness flows.
- [ ] Failure tests cover missing evidence, invalid state, approval expiry, and kill switch.
- [ ] Security tests prove LLM/agent cannot bypass deterministic policy.
- [ ] Coverage is above 80%.

### 24.6 Documentation

- [ ] `README.md` explains risk module responsibilities.
- [ ] Tool catalog documents official tools.
- [ ] Config documentation explains thresholds.
- [ ] Workflow documentation explains risk gates.
- [ ] Error code documentation exists.
- [ ] Component map documents which file owns each risk capability.

---

## 27. Implementation Plan

### Phase 0 — Establish Requirements and Test Baseline

Deliverables:

- finalized functional requirement list
- finalized non-functional requirement list
- requirement traceability matrix
- golden expected-value fixtures
- production acceptance checklist

Exit criteria:

- every requirement has an owner, target file, and test category
- core risk calculations have expected-value fixtures
- fail-closed behavior is explicitly tested

### Phase 1 — Build Contracts and Config

Deliverables:

- `contracts.py`
- `errors.py`
- `config.py`
- institutional hardening config contracts: `PortfolioExitLiquidityConfig`, `CorrelationAdjustedSizingConfig`, `RiskStepDownConfig`, `LiveRiskStateConfig`, `AuditChainConfig`
- contract tests
- config tests

Exit criteria:

- all core objects validate correctly
- invalid inputs fail clearly
- config hash is stable

### Phase 2 — Build Pure Calculators

Deliverables:

- `calculators.py`
- portfolio exit-liquidity stress calculations
- calculator tests
- expected-value fixtures

Exit criteria:

- exposure, margin, drawdown, VaR, CVaR, and correlation tests pass
- no I/O or external dependencies exist inside calculators

### Phase 3 — Build State and Snapshot Layer

Deliverables:

- `state.py`
- portfolio snapshot tests
- snapshot usage example

Exit criteria:

- raw portfolio data normalizes into canonical state
- snapshot includes required metrics, warnings, evidence references, and config hash

### Phase 4 — Build Limits and Governor

Deliverables:

- `limits.py`
- `circuit_breakers.py`
- `governor.py`
- decision package tests
- fail-closed tests

Exit criteria:

- governor decisions are deterministic
- limit precedence works
- missing evidence blocks or requests evidence according to the truth tables

### Phase 5 — Build Approvals and Kill Switch

Deliverables:

- `approvals.py`
- kill-switch contract/support
- approval emergency revocation behavior
- approval-token tests
- security tests

Exit criteria:

- token expiry, revocation, mismatch, and tamper tests pass
- kill switch cannot be bypassed

### Phase 6 — Build Position Sizing, Regimes, Allocation, and Lifecycle

Deliverables:

- `sizing.py`
- `regimes.py`
- `sizing.py` correlation-adjusted sizing finalization
- `allocation.py`
- `lifecycle.py`
- sizing, regime, allocation, and lifecycle tests

Exit criteria:

- all position sizing methods return deterministic, broker-constrained results
- regime assessment is deterministic and auditable
- strategy promotion and demotion gates work
- allocation proposals are risk-reviewed

### Phase 7 — Build Scenarios and Reports

Deliverables:

- `scenarios.py`
- `reports.py`
- composite failure reporting and primary-failure explanation
- scenario/report tests

Exit criteria:

- scenario analysis produces auditable advisory outputs
- reports separate evidence, calculations, warnings, decisions, assumptions, and missing data

### Phase 8 — Build Official Tool Wrappers

Deliverables:

- `tools.py`
- `__init__.py`
- tool tests
- usage examples

Exit criteria:

- official AI tools comply with the HaruQuant Tool Function Standard
- public API is narrow, documented, and registry-reviewed

### Phase 9 — Integration and Production Sign-off

Deliverables:

- integration tests
- workflow tests
- benchmark results
- security tests
- final acceptance checklist

Exit criteria:

- workflows pass end-to-end
- all FR/NFR requirements have implementation and test evidence
- official tools pass schema, metadata, logging, and request tracing checks
- production promotion checklist is complete

---

## 28. Capability Ownership Map

| Risk Capability | Primary Owner |
|---|---|
| Portfolio state builder | `state.py` |
| Risk snapshot builder | `state.py` |
| Exposure calculations | `calculators.py` |
| Currency exposure | `calculators.py` |
| Symbol concentration | `calculators.py` + `limits.py` |
| Strategy concentration | `calculators.py` + `limits.py` |
| Margin usage | `calculators.py` + `limits.py` |
| Leverage limit | `limits.py` |
| VaR/CVaR | `calculators.py` + `limits.py` |
| Drawdown state | `calculators.py` + `limits.py` |
| Correlation checks | `calculators.py` + `limits.py` |
| Cluster risk | `calculators.py` + `limits.py` |
| Spread/slippage checks | `limits.py` with market context input |
| News blackout | `limits.py` with calendar/news context input |
| Risk governor checks | `governor.py` |
| Approval tokens | `approvals.py` |
| Kill switch | `approvals.py` or `governor.py` contract integration |
| Graduated risk step-down controls | `circuit_breakers.py` + `governor.py` |
| Live portfolio-state freshness | `state.py` + `governor.py` |
| In-flight order tolerance | `state.py` + `limits.py` + `governor.py` |
| Fixed-fractional sizing | `sizing.py` |
| Volatility-adjusted sizing | `sizing.py` |
| Risk-parity weights | `allocation.py` |
| Correlation-adjusted sizing | `sizing.py` + `calculators.py` + `limits.py` |
| Margin-aware sizing | `sizing.py` + `calculators.py` |
| Fixed lot sizing | `sizing.py` |
| Fixed risk sizing | `sizing.py` |
| Milestone sizing | `sizing.py` |
| Kelly criterion sizing | `sizing.py` |
| Strategy allocation proposal | `allocation.py` |
| Strategy lifecycle status update | `lifecycle.py` |
| Promote/demote/suspend/retire | `lifecycle.py` |
| Scenario analysis | `scenarios.py` |
| Replay/what-if | `scenarios.py` |
| Risk reports | `reports.py` |
| Snapshot/decision persistence | `storage.py` |
| Audit hash chaining | `audit.py` + `storage.py` |
| Composite failure tracking | `governor.py` + `contracts.py` + `reports.py` |
| Regime assessment | `regimes.py` |
| Regime transition tracking | `regimes.py` + `audit.py` |
| Agent-facing wrappers | `tools.py` + `__init__.py` |

---

## 29. Recommended First Implementation Slice

Start with the smallest vertical slice that proves the production design works:

```text
contracts.py
config.py
calculators.py
state.py
limits.py
governor.py
sizing.py
regimes.py
tools.py
__init__.py
tests/unit/tools/risk/test_*.py
tests/usage/tools/risk/pre_trade_review_example.py
```

The first usable workflow should be:

```text
ProposedTrade + PortfolioState + RiskConfig
  -> build snapshot
  -> run limit checks
  -> return RiskDecisionPackage
  -> wrap in official AI tool response
```

This gives HaruQuant a clear, testable, production-grade risk gate before adding scenario analysis, lifecycle, reports, and advanced allocation.

---

## 30. Final Build Rule

The HaruQuant risk module should be built as:

```text
small public API
strong contracts
pure calculators
dedicated position-sizing engine
deterministic regime assessment
deterministic limits
one canonical governor
auditable decisions
approval-aware live-readiness
agent-safe tool wrappers
tests before expansion
```

The goal is to build the risk domain so that HaruQuant agents, workflows, and execution systems can trust it as a deterministic safety layer.

---

## 31. Functional Requirements

This section converts the architectural specification into testable functional requirements. Each requirement must be traceable to implementation files, unit tests, integration tests, and production acceptance evidence.

### 31.1 Portfolio State and Snapshot Requirements

| ID | Requirement | Primary Owner | Acceptance Evidence |
|---|---|---|---|
| FR-001 | The risk module shall normalize raw account, equity, position, order, strategy, and symbol inputs into a canonical `PortfolioState` contract. | `state.py`, `contracts.py` | Contract tests and invalid-input tests. |
| FR-002 | The risk module shall build a `RiskSnapshot` from `PortfolioState` and `RiskConfig` without mutating the source inputs. | `state.py` | Snapshot deterministic test. |
| FR-003 | The risk module shall calculate account equity, balance, open risk, floating PnL, realized PnL, margin usage, free margin, and leverage where inputs are available. | `state.py`, `calculators.py` | Expected-value tests. |
| FR-004 | The risk module shall explicitly mark unavailable snapshot fields as missing evidence rather than inventing defaults. | `state.py`, `contracts.py` | Missing-evidence tests. |
| FR-005 | The risk module shall include `request_id`, `workflow_id`, `as_of`, `config_hash`, and evidence references in every material snapshot or decision package. | `contracts.py`, `governor.py` | Contract and audit tests. |
| FR-005b | Before applying a previously created risk decision or approval token, the risk module shall verify that the stored config hash matches the current active config version. A mismatch shall return `CONFIG_VERSION_MISMATCH` and force a new decision. | `config.py`, `approvals.py`, `governor.py` | Config-mismatch replay tests. |

### 31.2 Exposure and Concentration Requirements

| ID | Requirement | Primary Owner | Acceptance Evidence |
|---|---|---|---|
| FR-006 | The risk module shall calculate exposure by symbol, strategy, currency, asset class, direction, and account-level aggregate. | `calculators.py` | Exposure expected-value tests. |
| FR-007 | The risk module shall calculate net and gross exposure separately. | `calculators.py` | Long/short portfolio tests. |
| FR-008 | The risk module shall detect symbol concentration breaches using configurable limits. | `limits.py` | Limit pass/warn/fail tests. |
| FR-009 | The risk module shall detect strategy concentration breaches using configurable limits. | `limits.py` | Strategy concentration tests. |
| FR-010 | The risk module shall detect currency-cluster and correlated-cluster exposure risks for FX portfolios. | `calculators.py`, `limits.py` | Cluster-risk tests. |
| FR-011 | The risk module shall support account-base-currency conversion for exposure values when conversion rates are available. | `calculators.py` | Multi-currency conversion tests. |
| FR-012 | The risk module shall block or request evidence when required FX conversion rates are unavailable for a material exposure decision. | `limits.py`, `governor.py` | Missing FX-rate tests. |
| FR-012b | The risk module shall include pending orders in exposure, margin, leverage, concentration, and cluster-risk calculations according to the configured pending-order exposure policy. Near-market pending orders must be treated as potential exposure unless explicitly configured otherwise. | `state.py`, `calculators.py`, `limits.py` | Pending-order exposure and margin tests. |

### 31.3 Drawdown, Loss, and Prop-Firm Rule Requirements

| ID | Requirement | Primary Owner | Acceptance Evidence |
|---|---|---|---|
| FR-013 | The risk module shall calculate daily drawdown, total drawdown, peak-to-valley drawdown, and current drawdown state. | `calculators.py` | Drawdown expected-value tests. |
| FR-014 | The risk module shall enforce configurable maximum daily loss. Default baseline: 5%. | `limits.py`, `config.py` | Daily-loss breach tests. |
| FR-015 | The risk module shall enforce configurable maximum total loss. Default baseline: 10%. | `limits.py`, `config.py` | Total-loss breach tests. |
| FR-016 | The risk module shall support configurable monthly profit target tracking. Default baseline: 10% target. | `limits.py`, `reports.py` | Profit-target report tests. |
| FR-017 | The risk module shall detect best-day / consistency-rule risk when configured. | `limits.py`, `reports.py` | Consistency-rule tests. |
| FR-018 | The risk module shall classify the portfolio drawdown state as normal, caution, restricted, blocked, or kill-switch-required according to configured thresholds. | `limits.py`, `governor.py` | Decision truth-table tests. |

### 31.4 Margin and Leverage Requirements

| ID | Requirement | Primary Owner | Acceptance Evidence |
|---|---|---|---|
| FR-019 | The risk module shall calculate margin required for current positions and proposed trades when contract size, leverage, price, and currency data are available. | `calculators.py` | Margin calculation tests. |
| FR-020 | The risk module shall calculate projected margin usage after a proposed trade. | `calculators.py`, `state.py` | Pre-trade projection tests. |
| FR-021 | The risk module shall enforce maximum margin utilization limits. | `limits.py` | Margin breach tests. |
| FR-022 | The risk module shall enforce maximum effective leverage limits. | `limits.py` | Leverage breach tests. |
| FR-023 | The risk module shall fail closed when required broker symbol metadata is missing for a live-readiness or pre-trade decision. | `governor.py` | Missing symbol-metadata tests. |

### 31.5 VaR, CVaR, Volatility, and Statistical Risk Requirements

| ID | Requirement | Primary Owner | Acceptance Evidence |
|---|---|---|---|
| FR-024 | The risk module shall calculate portfolio volatility using a deterministic method and explicitly documented lookback window. | `calculators.py`, `config.py` | Volatility expected-value tests. |
| FR-025 | The risk module shall calculate VaR at configurable confidence levels. Default baseline: 95%. | `calculators.py` | VaR expected-value tests. |
| FR-026 | The risk module shall calculate CVaR / expected shortfall at configurable confidence levels. | `calculators.py` | CVaR expected-value tests. |
| FR-027 | The risk module shall support both historical and parametric VaR methods when configured. | `calculators.py` | Method parity tests. |
| FR-028 | The risk module shall reject or request more evidence when return history is insufficient for configured VaR/CVaR requirements. | `limits.py`, `governor.py` | Insufficient-history tests. |
| FR-029 | The risk module shall expose calculation assumptions in snapshot metadata, including lookback, confidence level, method, and data coverage. | `contracts.py`, `reports.py` | Metadata tests. |

### 31.6 Correlation and Portfolio Interaction Requirements

| ID | Requirement | Primary Owner | Acceptance Evidence |
|---|---|---|---|
| FR-030 | The risk module shall calculate pairwise and portfolio-level correlation exposure for active positions and proposed trades. | `calculators.py` | Correlation tests. |
| FR-031 | The risk module shall evaluate a proposed trade against the existing portfolio, not only against individual positions. | `governor.py` | Portfolio-impact tests. |
| FR-032 | The risk module shall reject or warn when a proposed trade increases portfolio correlation above the configured threshold. Default FX baseline: 0.50. | `limits.py` | Correlation threshold tests. |
| FR-033 | The risk module shall handle missing or insufficient correlation data explicitly as missing evidence. | `limits.py` | Missing-correlation tests. |
| FR-034 | The risk module shall calculate incremental risk contribution where enough data exists. | `calculators.py`, `governor.py` | Incremental-risk tests. |

### 31.7 Market Context, Spread, Slippage, and News Requirements

| ID | Requirement | Primary Owner | Acceptance Evidence |
|---|---|---|---|
| FR-035 | The risk module shall accept spread, slippage, session, liquidity, and economic-calendar context as external evidence. | `contracts.py` | Contract tests. |
| FR-036 | The risk module shall enforce configurable maximum spread limits for pre-trade review. | `limits.py` | Spread-limit tests. |
| FR-037 | The risk module shall enforce high-impact-news blackout windows when economic-calendar evidence is supplied. Default baseline: 10 minutes before and 10 minutes after high-impact events. | `limits.py` | News-blackout tests. |
| FR-038 | The risk module shall treat missing required news/calendar evidence according to the configured mode: `ignore`, `warn`, `needs_more_evidence`, or `block`. | `config.py`, `limits.py` | Calendar-policy tests. |
| FR-039 | The risk module shall support weekend, overnight, and restricted-session rules when enabled. | `limits.py` | Session-rule tests. |
| FR-040 | The risk module shall use explicit timezone configuration for all session and calendar rules. | `config.py`, `limits.py` | Timezone tests. |

### 31.8 Pre-Trade Risk Review Requirements

| ID | Requirement | Primary Owner | Acceptance Evidence |
|---|---|---|---|
| FR-041 | The risk module shall review every proposed trade through a canonical `ProposedTrade` contract before execution. | `contracts.py`, `governor.py` | Contract and workflow tests. |
| FR-042 | The risk module shall return one canonical `RiskDecisionPackage` for each pre-trade review. | `governor.py` | Schema compliance tests. |
| FR-043 | The risk module shall calculate projected exposure, margin, drawdown, VaR/CVaR, concentration, and correlation impact when evidence is available. | `governor.py` | Pre-trade projection tests. |
| FR-044 | The risk module shall return `approve` only when all required hard limits pass and no unresolved blocking evidence exists. | `governor.py` | Truth-table tests. |
| FR-045 | The risk module shall return `reject` or `block` for hard-limit breaches, kill-switch-active states, invalid input, or missing mandatory live-readiness evidence. | `governor.py` | Fail-closed tests. |
| FR-046 | The risk module shall return `needs_more_evidence` when configured mandatory evidence is missing but the action is not automatically prohibited. | `governor.py` | Missing-evidence tests. |
| FR-047 | The risk module shall return `needs_approval` when a policy permits exception handling but requires deterministic approval. | `governor.py`, `approvals.py` | Approval-required tests. |

### 31.9 Strategy Admission and Lifecycle Requirements

| ID | Requirement | Primary Owner | Acceptance Evidence |
|---|---|---|---|
| FR-048 | The risk module shall review strategy admission using a canonical validation evidence package. | `lifecycle.py`, `contracts.py` | Strategy-admission tests. |
| FR-049 | The risk module shall support lifecycle states: draft, research, validated, paper, approved_for_live, live, suspended, retired. | `lifecycle.py` | State-transition tests. |
| FR-050 | The risk module shall enforce promotion gates before a strategy moves into paper or live eligibility. | `lifecycle.py`, `governor.py` | Promotion-gate tests. |
| FR-051 | The risk module shall enforce demotion, suspension, and retirement rules for strategies breaching risk limits. | `lifecycle.py` | Demotion tests. |
| FR-052 | The risk module shall not mark a strategy live-ready without evidence, risk decision, approval state, and kill-switch status. | `lifecycle.py`, `approvals.py` | Live-readiness tests. |

### 31.10 Position Sizing and Allocation Requirements

| ID | Requirement | Primary Owner | Acceptance Evidence |
|---|---|---|---|
| FR-053 | The risk module shall calculate `fixed_lot` position sizing using a configured lot size. | `sizing.py` | Fixed-lot sizing tests. |
| FR-054 | The risk module shall calculate `fixed_risk` position sizing using fixed account risk percentage or fixed account risk amount. | `sizing.py` | Fixed-risk sizing tests. |
| FR-055 | The risk module shall calculate `milestone` position sizing using deterministic account balance/equity milestone tables. | `sizing.py` | Milestone sizing tests. |
| FR-056 | The risk module shall calculate conservative `kelly_criterion` sizing using validated win-rate/payoff evidence, configured caps, and a configurable minimum trade sample requirement. Default baseline: `min_kelly_trades = 30`; insufficient samples shall emit `INSUFFICIENT_K_EVIDENCE`. | `sizing.py` | Kelly sizing sample-size tests. |
| FR-057 | The risk module shall calculate `volatility` sizing using ATR or volatility-adjusted stop distance. | `sizing.py` | Volatility-sizing tests. |
| FR-058 | The risk module shall calculate `fixed_fractional` sizing using configured capital fraction or notional allocation. | `sizing.py` | Fixed-fractional sizing tests. |
| FR-059 | The risk module shall clamp or reject position sizes that exceed broker constraints, configured risk, margin, leverage, concentration, or symbol limits. | `sizing.py`, `limits.py` | Clamp/reject tests. |
| FR-060 | The risk module shall return a canonical `PositionSizingResult` for every sizing request. | `sizing.py`, `contracts.py` | Sizing contract tests. |
| FR-061 | The risk module shall expose `calculate_position_size` as an optional official AI tool when agent workflows need sizing recommendations. | `tools.py`, `__init__.py`, `sizing.py` | Tool-standard tests. |
| FR-062 | The risk module shall support risk-parity-style allocation proposals for strategy baskets. | `allocation.py` | Risk-parity tests. |
| FR-063 | The risk module shall validate allocation proposals against portfolio-level risk limits before approval. | `allocation.py`, `governor.py` | Allocation-review tests. |

### 31.11 Approval Token and Exception Workflow Requirements

| ID | Requirement | Primary Owner | Acceptance Evidence |
|---|---|---|---|
| FR-064 | The risk module shall create tamper-evident approval tokens for approval-required decisions. | `approvals.py` | Token signature tests. |
| FR-065 | Approval tokens shall include request id, workflow id, approved action, approver, expiry, config hash, decision hash, and scope. | `approvals.py`, `contracts.py` | Token contract tests. |
| FR-066 | Approval tokens shall expire deterministically and fail validation after expiry. | `approvals.py` | Expiry tests. |
| FR-067 | Approval tokens shall support revocation and fail validation after revocation. | `approvals.py` | Revocation tests. |
| FR-068 | Approval tokens shall be bound to the decision, account, strategy, symbol/action scope, and config hash they were created for. | `approvals.py` | Scope mismatch tests. |
| FR-069 | The risk module shall reject approval reuse for materially different actions. | `approvals.py`, `governor.py` | Replay/reuse tests. |
| FR-069b | Upon kill-switch activation, the risk module shall revoke or invalidate all outstanding approval tokens for the affected global, account, strategy, or symbol scope and log the revocation. | `approvals.py`, `governor.py`, `audit.py` | Emergency revocation tests. |

### 31.12 Kill-Switch Requirements

| ID | Requirement | Primary Owner | Acceptance Evidence |
|---|---|---|---|
| FR-070 | The risk module shall check kill-switch state for live-readiness and execution-sensitive workflows. | `governor.py`, `approvals.py` | Kill-switch tests. |
| FR-071 | Active kill switch shall force `block` for live-related decisions. | `governor.py` | Active-kill-switch tests. |
| FR-072 | Unknown kill-switch state shall fail closed for live-related decisions. | `governor.py` | Unknown-state tests. |
| FR-073 | LLM agents shall not be able to override kill-switch state through prompt text, tool arguments, or approval tokens. | `tools.py`, `governor.py` | Security tests. |

### 31.13 Scenario, Replay, and Reporting Requirements

| ID | Requirement | Primary Owner | Acceptance Evidence |
|---|---|---|---|
| FR-074 | The risk module shall run deterministic scenario and what-if analysis without changing live state. | `scenarios.py` | Scenario tests. |
| FR-075 | Scenario outputs shall be advisory unless passed through the canonical governor. | `scenarios.py`, `governor.py` | Scenario-governance tests. |
| FR-076 | The risk module shall generate human-readable Markdown risk reports from snapshots, decisions, and scenario outputs. | `reports.py` | Report snapshot tests. |
| FR-077 | Risk reports shall separate evidence, calculations, assumptions, warnings, decisions, and recommendations. | `reports.py` | Report content tests. |
| FR-078 | Risk reports shall not claim live approval unless a valid approval token and risk decision exist. | `reports.py` | Approval-report tests. |
| FR-078b | Every risk decision report shall include a plain-language explanation of the primary reason for `reject` or `block`, referencing the specific limit, rule, missing evidence, approval failure, or kill-switch state involved. | `reports.py` | Plain-language rejection explanation tests. |


### 31.14 Risk Regime Requirements

| ID | Requirement | Primary Owner | Acceptance Evidence |
|---|---|---|---|
| FR-079 | The risk module shall calculate a `RegimeAssessment` for portfolio snapshots when regime assessment is enabled. | `regimes.py`, `state.py` | Regime assessment tests. |
| FR-080 | The regime layer shall classify volatility, liquidity, correlation, drawdown, crisis, news, and session regimes. | `regimes.py` | Detector tests. |
| FR-081 | The Risk Governor shall consume `RegimeAssessment` before approving, warning, rejecting, or blocking proposed risk-increasing actions. | `governor.py`, `limits.py` | Governor-regime tests. |
| FR-082 | The risk module shall support deterministic regime transitions with timestamp, previous regime, new regime, reason, and evidence references. | `regimes.py`, `audit.py` | Transition audit tests. |
| FR-083 | The risk module shall apply stricter configured risk limits during high-risk regimes. | `limits.py`, `config.py` | Regime-adjusted limit tests. |
| FR-084 | The risk module shall expose regime state in snapshots, risk reports, audit records, and decision packages. | `contracts.py`, `reports.py`, `audit.py` | Regime reporting tests. |
| FR-085 | The regime layer shall fail closed for live-sensitive workflows when required regime evidence is missing and policy requires regime evidence. | `regimes.py`, `governor.py` | Missing-regime-evidence tests. |

### 31.15 Institutional Hardening Requirements

| ID | Requirement | Primary Owner | Acceptance Evidence |
|---|---|---|---|
| FR-086 | The risk module shall calculate portfolio exit-liquidity stress when enabled, including stressed VaR, stressed CVaR where available, stressed max drawdown, and market-impact assumptions. | `calculators.py`, `limits.py`, `governor.py` | Portfolio exit stress golden tests. |
| FR-087 | The risk governor shall downgrade decisions to `needs_approval`, `reject`, or `block` when portfolio exit-liquidity stress breaches configured limits. | `governor.py`, `limits.py` | Exit-liquidity decision tests. |
| FR-088 | The position sizing engine shall support correlation-adjusted sizing using marginal correlation to open positions and configured penalty method. | `sizing.py`, `calculators.py` | Correlation-adjusted sizing tests. |
| FR-089 | The risk module shall apply graduated risk step-down controls before hard circuit breakers when enabled. | `circuit_breakers.py`, `governor.py` | Step-down transition tests. |
| FR-090 | The risk module shall validate live portfolio-state freshness and return `needs_more_evidence` or `block` when state is stale beyond configured tolerance. | `governor.py`, `state.py` | Live freshness tests. |
| FR-091 | The risk module shall support in-flight order tolerance buffers during live reconciliation and disclose `in_flight_tolerance_used` in decision metadata when used. | `state.py`, `governor.py`, `limits.py` | In-flight tolerance tests. |
| FR-092 | The audit layer shall support cryptographic hash chaining with `previous_hash` and `record_hash` fields for tamper-evident audit records. | `audit.py`, `storage.py` | Audit chain integrity tests. |
| FR-093 | The governor shall populate `primary_failure_limit` and `composite_breach_flags` in every material `RiskDecisionPackage`. | `governor.py`, `contracts.py` | Composite failure tests. |
| FR-094 | Risk reports shall highlight the `primary_failure_limit` first and then list composite breach flags separately. | `reports.py` | Report explanation tests. |
| FR-095 | Kelly sizing shall either reject insufficient evidence with `INSUFFICIENT_K_EVIDENCE` or, when configured, fall back to `fixed_risk` and emit `SIZING_FALLBACK_TO_FIXED_RISK`. | `sizing.py` | Kelly fallback tests. |

### 31.16 Official AI Tool Requirements

| ID | Requirement | Primary Owner | Acceptance Evidence |
|---|---|---|---|
| FR-086 | The risk domain shall expose only approved official AI tools through `tools/risk/__init__.py`. | `__init__.py`, `tools.py` | Registry tests. |
| FR-087 | Every official AI tool shall follow the HaruQuant AI Tool Function Standard. | `tools.py` | Tool-standard tests. |
| FR-088 | Every official AI tool shall accept `request_id: Optional[str] = None`. | `tools.py` | Signature tests. |
| FR-089 | Every official AI tool shall return the standard HaruQuant tool response schema. | `tools.py` | Schema tests. |
| FR-090 | No official risk tool shall place trades, close trades, mutate broker state, or override execution controls. | `tools.py` | Side-effect metadata and security tests. |
| FR-091 | Official AI tools shall call deterministic services rather than implementing risk logic inline. | `tools.py` | Code review and unit tests. |

---

## 32. Non-Functional Requirements

### 32.1 Determinism and Reproducibility

| ID | Requirement | Acceptance Evidence |
|---|---|---|
| NFR-001 | For the same inputs, same configuration hash, and same dependency versions, the risk module shall produce the same `RiskDecisionPackage`. | Golden deterministic tests. |
| NFR-002 | All material decisions shall include enough metadata to reproduce the decision later. | Decision replay tests. |
| NFR-003 | Randomized scenario tests, if added, shall require explicit seeds and report the seed used. | Scenario reproducibility tests. |
| NFR-004 | Config changes shall create a new config hash and shall be visible in snapshots, decisions, approvals, and reports. | Config hash tests. |

### 32.2 Performance Targets

| ID | Requirement | Target |
|---|---|---|
| NFR-005 | Pre-trade risk review latency for a normal portfolio shall complete within 100 ms p95 in local deterministic mode. | p95 <= 100 ms. |
| NFR-006 | Snapshot generation for up to 500 open positions shall complete within 250 ms p95. | p95 <= 250 ms. |
| NFR-007 | Governor decision generation shall complete within 50 ms p95 after snapshot inputs are prepared. | p95 <= 50 ms. |
| NFR-008 | Scenario analysis with up to 100 scenarios and 500 positions shall complete within 5 seconds p95. | p95 <= 5 s. |
| NFR-009 | Markdown report generation from a completed decision package shall complete within 1 second p95. | p95 <= 1 s. |

Targets may be revised after real benchmark measurements, but any revision must be documented with evidence.

Performance targets are measured on a standard development reference environment unless otherwise specified. Baseline reference: modern 2.5 GHz+ 8-core CPU, 16 GB RAM, local deterministic execution, no remote broker/network calls, and warm Python process. CI and production deployments may define their own benchmark profiles, but benchmark results must always report hardware, Python version, dependency versions, dataset size, and whether caches were warm or cold.

### 32.3 Scalability Targets

| ID | Requirement | Target |
|---|---|---|
| NFR-010 | The module shall support at least 500 open positions in portfolio-level calculations. | 500 positions. |
| NFR-011 | The module shall support at least 100 strategies in allocation and concentration review. | 100 strategies. |
| NFR-012 | The module shall support at least 5,000 historical return points for VaR/CVaR calculations. | 5,000 returns. |
| NFR-013 | The module shall support at least 100 stress scenarios per scenario-analysis run. | 100 scenarios. |
| NFR-014 | The module shall avoid O(n³) algorithms in normal pre-trade paths unless explicitly justified. | Code review and benchmarks. |

### 32.4 Reliability and Fail-Closed Behavior

| ID | Requirement | Acceptance Evidence |
|---|---|---|
| NFR-015 | Safety-critical decisions shall fail closed on invalid input, missing mandatory evidence, unknown approval state, unknown kill-switch state, or calculation failure. | Failure-path tests. |
| NFR-016 | Non-critical reporting failures shall not silently hide risk decisions. | Report failure tests. |
| NFR-017 | Audit write failure behavior shall be configurable, but live-readiness workflows shall fail closed when audit persistence is mandatory and unavailable. | Audit-failure tests. |
| NFR-018 | External dependency failure shall be represented as `needs_more_evidence`, `reject`, or `block`, never as silent success. | Dependency-failure tests. |
| NFR-019 | The module shall avoid broad exception swallowing and shall map exceptions to deterministic error codes. | Error-mapping tests. |

### 32.5 Security and Permission Requirements

| ID | Requirement | Acceptance Evidence |
|---|---|---|
| NFR-020 | Approval-token signing keys, secrets, broker credentials, and private account identifiers shall never be logged. | Redaction tests. |
| NFR-021 | Approval tokens shall be tamper-evident using HMAC or a stronger signing mechanism. | Signature tests. |
| NFR-022 | Risk tools shall declare accurate risk metadata and side-effect flags. | Tool metadata tests. |
| NFR-023 | The risk module shall not expose internal helpers as official AI tools unless intentionally promoted through `__all__`. | Registry tests. |
| NFR-024 | The module shall enforce least privilege: risk can approve/block readiness, but cannot execute trades. | Import and side-effect tests. |
| NFR-025 | Agent-provided text shall never override deterministic policy, approvals, kill-switch state, or configured risk limits. | Prompt-injection/security tests. |

### 32.6 Observability and Auditability

| ID | Requirement | Acceptance Evidence |
|---|---|---|
| NFR-026 | Every material risk decision shall emit structured logs with request id, workflow id, decision status, reason codes, and execution time. | Log capture tests. |
| NFR-027 | Every material risk decision shall be serializable as an audit record. | Audit schema tests. |
| NFR-028 | Audit records shall include evidence references, config hash, input summary, limit results, approval state, and final decision. | Audit content tests. |
| NFR-029 | Observability metrics shall include decision count, block count, reject count, approval-required count, latency, calculation failures, and missing-evidence events. | Metrics tests or instrumentation review. |
| NFR-030 | Logs and audit records shall redact secrets and sensitive account data. | Redaction tests. |

### 32.7 Dependency and Interface Requirements

| ID | Requirement | Target |
|---|---|---|
| NFR-031 | The module shall support the project Python version defined in `pyproject.toml`. | CI check. |
| NFR-032 | The module shall use the project logging and result conventions. | Code review and tests. |
| NFR-033 | The module shall use Pydantic/dataclass contracts consistently according to the project-wide contract decision. | Contract tests. |
| NFR-034 | The module shall avoid unnecessary heavy dependencies in the deterministic pre-trade path. | Dependency review. |
| NFR-035 | Public contracts shall be versioned when downstream workflows depend on them. | Contract version tests. |

### 32.8 Maintainability Requirements

| ID | Requirement | Acceptance Evidence |
|---|---|---|
| NFR-036 | Each production file shall have a clear module-level docstring and public function/class docstrings. | Static review. |
| NFR-037 | Public functions shall have type hints. | mypy/static typing. |
| NFR-038 | Core functions shall remain small, focused, and testable; complex orchestration belongs in services/governor, not calculators. | Code review. |
| NFR-039 | Official AI tools shall not be added without tests, usage examples, metadata, and registry review. | CI gate. |
| NFR-040 | Public interface changes shall be versioned, documented, and reviewed before downstream workflows depend on them. | Interface review. |

---


### 32.9 Position Sizing Non-Functional Requirements

| ID | Requirement | Acceptance Evidence |
|---|---|---|
| NFR-041 | Position sizing shall be deterministic for the same request, broker constraints, risk config, and symbol metadata. | Sizing golden tests. |
| NFR-042 | Position sizing shall complete within 25 ms p95 for standard single-trade sizing requests. | Sizing benchmark tests. |
| NFR-043 | Position sizing shall not mutate portfolio, broker, execution, or storage state. | Side-effect tests. |
| NFR-044 | Position sizing formulas shall be unit-tested with expected-value fixtures for every supported method. | Fixed-lot, fixed-risk, milestone, Kelly, volatility, and fixed-fractional tests. |
| NFR-045 | Position sizing shall expose all constraints applied, including broker min/max/step, risk caps, margin caps, and leverage caps. | Sizing metadata tests. |
| NFR-046 | Position sizing shall fail safely when required stop-loss, volatility, value-per-point, symbol metadata, or conversion-rate evidence is missing. | Missing-evidence sizing tests. |

### 32.10 Regime Non-Functional Requirements

| ID | Requirement | Acceptance Evidence |
|---|---|---|
| NFR-047 | Regime classification shall be deterministic for the same inputs and configuration hash. | Regime golden tests. |
| NFR-048 | Regime assessment shall complete within the pre-trade risk latency budget. | Regime benchmark tests. |
| NFR-049 | Regime transitions shall be auditable and replayable. | Regime transition audit tests. |
| NFR-050 | Regime logic shall not depend on LLM judgment. | Code review and security tests. |
| NFR-051 | Regime thresholds and multipliers shall be configurable, versioned, and included in the risk config hash. | Config hash tests. |
| NFR-052 | Unknown regime state shall fail closed for live-sensitive workflows when configured to do so. | Unknown-regime live workflow tests. |

### 32.11 Thread-Safety and Concurrency Requirements

| ID | Requirement | Acceptance Evidence |
|---|---|---|
| NFR-053 | All risk calculators, limit checks, sizing calculations, regime checks, and governor logic shall be stateless and thread-safe. No mutable global state may influence deterministic decisions. | Concurrent decision tests and static review. |
| NFR-054 | Concurrent risk decisions shall not share mutable request state, cached intermediate values, approval-token state, or audit buffers unless access is explicitly synchronized and covered by tests. | Multi-thread/multi-task workflow tests. |
| NFR-055 | Any cache used by the risk module shall be keyed by input evidence version, config hash, and dependency version, and shall be safe for concurrent reads/writes. | Cache invalidation and concurrency tests. |


### 32.12 Institutional Hardening Non-Functional Requirements

| ID | Requirement | Acceptance Evidence |
|---|---|---|
| NFR-056 | Portfolio exit-liquidity stress shall be deterministic for the same portfolio, config hash, market-impact assumptions, and evidence set. | Exit stress golden tests. |
| NFR-057 | Correlation-adjusted sizing shall disclose penalty method, marginal correlation, raw size, adjusted size, and final clamped size. | Sizing metadata tests. |
| NFR-058 | Step-down state transitions shall be auditable, replayable, versioned, and clearable only through deterministic cooldown rules. | Step-down replay tests. |
| NFR-059 | Live portfolio-state freshness checks shall use timezone-aware timestamps and monotonic age calculation where practical. | Live timestamp tests. |
| NFR-060 | Audit hash-chain verification shall complete before live-sensitive decisions when configured as mandatory. | Audit chain live-gate tests. |
| NFR-061 | Hash-chain generation shall use canonical serialization and a documented hash algorithm. | Hash determinism tests. |
| NFR-062 | Composite failure tracking shall be stable for the same deterministic limit evaluation order. | Composite breach golden tests. |
| NFR-063 | Feature-flagged institutional hardening controls shall be included in config validation and config hash calculation whether enabled or disabled. | Config hash tests. |
| NFR-064 | Step-down state initialization, restoration, reset, and corruption handling shall be deterministic and replayable. | Step-down state replay tests. |
| NFR-065 | Audit-chain genesis behavior shall be deterministic and documented; the genesis value shall not depend on random runtime state. | Audit genesis tests. |
| NFR-066 | Correlation fallback behavior shall be deterministic for the same sizing request, evidence set, and config hash. | Correlation fallback golden tests. |
| NFR-067 | Limit evaluation order shall be stable across Python versions, process restarts, concurrent requests, and test runs. | Deterministic limit-order tests. |
| NFR-068 | In-flight grace-period expiry behavior shall be deterministic and auditable under concurrent live-guard calls. | Concurrent live reconciliation tests. |

## 33. Risk Decision Truth Tables

The risk governor must produce deterministic decisions using the following precedence. Higher-precedence outcomes override lower-precedence outcomes.

### 33.1 Canonical Decision Values

| Decision | Meaning | Can Proceed? | Human Approval Can Override? |
|---|---|---:|---:|
| `approve` | All mandatory checks pass. | Yes | Not needed |
| `warn` | Soft limits or advisory conditions exist, but no hard block. | Yes, if workflow permits warnings | Not needed unless configured |
| `needs_more_evidence` | Required evidence is missing, stale, or insufficient. | No | No, unless an explicit evidence-waiver policy exists |
| `needs_approval` | Deterministic policy permits exception only with valid approval. | No until approval validates | Yes |
| `reject` | Hard limit breached or invalid proposal. | No | Usually no; only if policy explicitly allows exception |
| `block` | Kill switch, prohibited action, permission denial, invalid live-readiness state, or fail-closed condition. | No | No |
| `error` | Tool/service failed before valid decision could be created. | No | No |

### 33.2 Decision Precedence

```text
block
  > error
  > reject
  > needs_more_evidence
  > needs_approval
  > warn
  > approve
```

### 33.3 Limit Result to Decision Mapping

| Condition | Limit Result | Governor Decision |
|---|---|---|
| Kill switch active for live workflow | block | `block` |
| Audit chain tamper detected for live workflow | block | `block` |
| Live portfolio state stale beyond configured tolerance | missing_evidence/block | `needs_more_evidence` or `block` |
| Step-down stage is `size_reduced` | warn/limit_adjustment | `warn` or `needs_approval` according to config |
| Step-down stage is `new_trades_rejected` | fail | `reject` |
| Step-down stage is `close_all_and_halt` | block | `block` |
| Portfolio exit-liquidity stress breaches hard threshold | fail | `reject` or `block` |
| In-flight order tolerance would be exceeded | approval_required/fail | `needs_approval` or `reject` |
| Kill switch state unknown for live workflow | block | `block` |
| Tool attempts live trade mutation from risk module | block | `block` |
| Invalid proposed trade schema | fail | `reject` or `error` depending on boundary |
| Daily loss limit breached | fail/block | `reject` or `block` if live workflow |
| Total loss limit breached | fail/block | `reject` or `block` if live workflow |
| Margin utilization above hard maximum | fail | `reject` |
| Leverage above hard maximum | fail | `reject` |
| Missing mandatory price/symbol metadata for pre-trade | missing_evidence | `needs_more_evidence` |
| Missing mandatory price/symbol metadata for live-readiness | block | `block` |
| News blackout active | fail/block according to config | `reject` or `block` |
| Spread above hard maximum | fail | `reject` |
| Correlation above hard threshold | fail | `reject` |
| Correlation above warning threshold only | warn | `warn` |
| VaR/CVaR above hard limit | fail | `reject` |
| VaR/CVaR above warning limit only | warn | `warn` |
| Crisis regime active and new risk is requested | block | `block` |
| High-volatility or low-liquidity regime active | warn/fail according to config | `warn`, `needs_approval`, or `reject` |
| Unknown mandatory regime for live workflow | block | `block` |
| Strategy state not eligible for requested action | fail | `reject` |
| Action requires approval but no token supplied | approval_required | `needs_approval` |
| Supplied approval token expired/revoked/mismatched | fail/block | `reject` or `block` |
| All hard checks pass and only advisory notices exist | warn | `warn` |
| All mandatory checks pass and no warnings exist | pass | `approve` |

### 33.4 Approval Exception Rules

Approval may only change a decision when all of the following are true:

1. The original decision is `needs_approval` or a policy-defined exception-eligible `reject`.
2. The approval token is valid, unexpired, unrevoked, and scope-matched.
3. The approval token references the same `decision_hash`, `config_hash`, `account_id`, `strategy_id`, `symbol`, and action type where applicable.
4. The kill switch is inactive and known.
5. The action is not explicitly prohibited.
6. Audit persistence succeeds when audit is mandatory.

Approval must never override:

- active kill switch
- unknown kill-switch state for live workflows
- prohibited broker mutation from the risk module
- invalid schema
- missing identity or request trace fields
- expired/revoked approval
- materially changed proposal

---

## 34. Evidence Freshness and Data Quality Requirements

### 34.1 Evidence Classification

| Evidence Type | Examples | Default Freshness Rule | Missing Evidence Behavior |
|---|---|---|---|
| Account state | equity, balance, margin, open PnL | Fresh as of current broker/account snapshot | Block live-readiness; request evidence for research. |
| Position state | open positions, pending exposure | Fresh as of current broker/account snapshot | Block pre-trade/live-readiness. |
| Price data | bid, ask, mid, OHLCV | Must match configured timeframe and max age | Request evidence or reject depending workflow. |
| Symbol metadata | contract size, tick value, leverage, currency | Must be current config/source snapshot | Block margin-sensitive decisions. |
| FX rates | conversion to account currency | Must match configured max age | Block material multi-currency decisions. |
| Returns history | VaR/CVaR, volatility | Must meet minimum lookback and coverage | Request evidence or warn according to config. |
| Correlation data | pairwise/portfolio correlations | Must meet minimum overlap and lookback | Request evidence or warn according to config. |
| Calendar/news | high-impact event context | Must cover configured blackout window | Apply configured missing-calendar policy. |
| Approval state | approval token, revocation list | Must be checked at decision time | Block if unavailable for live workflow. |
| Kill-switch state | global/account/strategy switch | Must be checked at decision time | Block if unknown for live workflow. |
| Position sizing evidence | stop-loss, tick value, contract size, broker min/max/step, ATR, Kelly stats, milestone table | Must match sizing request and config hash | Return missing evidence or error according to method. |
| Regime evidence | volatility, spread/liquidity, correlation, drawdown, news/session, crisis signals | Must match configured regime lookback and max age | Unknown/needs evidence/block according to workflow policy. |

### 34.2 Data Quality Checks

The risk module shall reject, block, warn, or request more evidence when data quality fails any required check:

- missing required field
- wrong type
- negative price, equity, margin, volatility, or quantity where invalid
- zero account equity for percentage risk calculations
- impossible timestamps
- stale `as_of` timestamp
- insufficient return history
- insufficient correlation overlap
- missing symbol metadata
- missing FX conversion rates
- inconsistent account currency
- unsupported symbol or asset class
- duplicate position identifiers
- inconsistent position direction/quantity/sign
- invalid strategy lifecycle state
- invalid approval-token scope
- missing stop-loss for fixed-risk sizing
- insufficient ATR/volatility evidence for volatility sizing
- insufficient Kelly trade sample evidence for Kelly sizing
- missing or ambiguous pending-order execution policy when pending orders exist

### 34.3 Multi-Currency Conversion Rules

All monetary risk metrics must be expressed in account base currency when used for account-level risk decisions.

Required behavior:

1. If the input value is already in account base currency, no conversion is applied.
2. If the input value is in another currency, the module must use an explicit FX conversion rate and timestamp.
3. If no valid conversion rate exists for a material decision, the module must return `needs_more_evidence` or `block` depending on workflow risk level.
4. Conversion assumptions must appear in snapshot metadata and audit records.
5. For live-readiness decisions, missing material conversion rates fail closed.

### 34.4 Timezone and Session Rules

All time-based risk rules must use explicit timezone-aware timestamps.

Required behavior:

- The risk module shall not compare naive and aware datetimes.
- News blackout windows shall be evaluated in a configured canonical timezone.
- Broker server time, account time, and UTC time must be mapped explicitly when used together.
- Weekend and overnight rules must define start/end boundaries in config.
- If timezone conversion fails for a live workflow, the decision shall fail closed.

---

## 35. Performance and Scalability Acceptance Targets

Performance must be tested with benchmark fixtures before production promotion.

### 35.1 Benchmark Scenarios

| Benchmark ID | Scenario | Data Size | Target |
|---|---|---:|---:|
| PERF-001 | Basic pre-trade review | 20 positions, 10 strategies | <= 50 ms p95 |
| PERF-002 | Large portfolio snapshot | 500 positions, 100 strategies | <= 250 ms p95 |
| PERF-003 | Correlation review | 100 symbols, 5,000 returns | <= 1 s p95 |
| PERF-004 | VaR/CVaR calculation | 500 positions, 5,000 returns | <= 1 s p95 |
| PERF-005 | Scenario analysis | 500 positions, 100 scenarios | <= 5 s p95 |
| PERF-006 | Report generation | one full decision package | <= 1 s p95 |
| PERF-007 | Position sizing | one standard sizing request with broker constraints | <= 25 ms p95 |
| PERF-008 | Pending-order exposure projection | 100 pending orders + 500 positions | <= 250 ms p95 |
| PERF-009 | Regime assessment | one portfolio snapshot with market context | <= 50 ms p95 |
| PERF-010 | Portfolio exit-liquidity stress | 500 positions with market-impact assumptions | <= 500 ms p95 |
| PERF-011 | Correlation-adjusted sizing | one sizing request + 100-symbol correlation context | <= 50 ms p95 |
| PERF-012 | Audit chain verification | 10,000 audit records | <= 2 s p95 |

### 35.2 Optimization Constraints

- Do not optimize prematurely before correctness tests exist.
- Prefer clear vectorized calculations for portfolio math where appropriate.
- Avoid hidden global caches in safety-critical decisions unless cache invalidation is deterministic and tested.
- Any cache used in risk decisions must include config hash and input evidence version in its key.
- Slow advisory analytics must not block the fast pre-trade path unless configured as mandatory.

---

## 36. Security, Token, and Approval Governance Requirements

### 36.1 Approval Token Contract

A valid approval token must include at minimum:

```text
approval_id
request_id
workflow_id
account_id
strategy_id optional
symbol optional
action_type
risk_decision_id
decision_hash
config_hash
approved_by
approved_at
expires_at
scope
approval_reason
signature
schema_version
previous_hash optional
record_hash optional
```

### 36.2 Token Validation Rules

A token is valid only if:

- schema validates
- signature validates
- token is not expired
- token is not revoked
- token action type matches requested action
- token scope matches account/strategy/symbol/action
- token decision hash matches the decision being executed
- token config hash matches current or explicitly accepted config version
- token was created by an authorized approver
- audit record can be written if required

### 36.3 Revocation Rules

The approval subsystem must support revocation by:

- approval id
- account id
- strategy id
- action type
- config hash
- emergency/global revocation
- kill-switch activation for affected global, account, strategy, or symbol scope
- time-range revocation for approvals created within a specified interval

Revoked approvals must fail validation immediately after the revocation state is visible to the risk module. Emergency kill-switch revocation must be logged as a material governance event.

### 36.4 Secret Handling

The module must not log:

- broker passwords
- API keys
- token signing keys
- full account credentials
- raw private approval secrets
- sensitive user identifiers beyond configured audit policy

Logs may include hashed or redacted identifiers where necessary for traceability.

---

## 37. Observability and Audit Durability Requirements

### 37.1 Required Log Events

The risk module shall log the following events using structured logging:

- risk tool called
- contract validation failed
- snapshot build started/completed/failed
- limit evaluation started/completed/failed
- governor decision started/completed/failed
- approval token created/validated/rejected/revoked
- kill-switch checked
- scenario/report generated
- audit write succeeded/failed

### 37.2 Required Audit Record Fields

Every material risk decision audit record shall include:

```text
audit_id
request_id
workflow_id
decision_id
timestamp
account_id redacted or hashed where required
strategy_id optional
symbol optional
action_type
input_summary
evidence_references
config_hash
snapshot_hash optional
limit_results
final_decision
reason_codes
warnings
approval_required
approval_id optional
kill_switch_state
tool_name optional
agent_name optional
execution_ms
error_code optional
schema_version
previous_hash optional
record_hash optional
```

### 37.3 Audit Durability Policy

| Workflow | Audit Write Failure Behavior |
|---|---|
| Research-only advisory report | Return warning and include audit failure in metadata. |
| Scenario/what-if advisory | Return warning and include audit failure in metadata. |
| Strategy admission | Return `needs_more_evidence` or `error` according to config. |
| Pre-trade review for paper trading | Configurable: warn or block. |
| Live-readiness / live-sensitive workflow | Fail closed with `block`. |
| Approval token creation/validation | Fail closed when audit is mandatory. |

### 37.4 Metrics

The module should expose or emit counters/timers for:

- total decisions
- approvals
- warnings
- rejections
- blocks
- missing evidence events
- calculation failures
- approval-token failures
- kill-switch blocks
- audit failures
- p50/p95/p99 latency by workflow

---

## 38. Requirement Traceability Matrix

This matrix maps requirements to implementation and test evidence. It must be updated during implementation.

| Requirement Group | IDs | Implementation Files | Required Test Files |
|---|---|---|---|
| Portfolio state and snapshot | FR-001 to FR-005b | `contracts.py`, `state.py`, `config.py` | `test_contracts.py`, `test_state.py`, config-mismatch tests |
| Exposure and concentration | FR-006 to FR-012b | `state.py`, `calculators.py`, `limits.py` | `test_calculators.py`, `test_limits.py`, pending-order exposure tests |
| Drawdown and prop-firm rules | FR-013 to FR-018 | `calculators.py`, `limits.py`, `reports.py` | `test_calculators.py`, `test_limits.py`, `test_reports.py` |
| Margin and leverage | FR-019 to FR-023 | `calculators.py`, `limits.py`, `governor.py` | `test_calculators.py`, `test_limits.py`, `test_governor.py` |
| VaR/CVaR/statistical risk | FR-024 to FR-029 | `calculators.py`, `limits.py` | `test_calculators.py`, `test_limits.py` |
| Correlation and portfolio interaction | FR-030 to FR-034 | `calculators.py`, `limits.py`, `governor.py` | `test_calculators.py`, `test_governor.py` |
| Market context/news/spread | FR-035 to FR-040 | `contracts.py`, `config.py`, `limits.py` | `test_contracts.py`, `test_config.py`, `test_limits.py` |
| Pre-trade review | FR-041 to FR-047 | `contracts.py`, `state.py`, `limits.py`, `governor.py` | `test_governor.py`, `test_pre_trade_workflow.py` |
| Strategy lifecycle | FR-048 to FR-052 | `lifecycle.py`, `governor.py` | `test_lifecycle.py`, `test_strategy_lifecycle_workflow.py` |
| Position sizing | FR-053 to FR-061 | `sizing.py`, `contracts.py`, `limits.py`, `tools.py` | `test_sizing.py`, `test_tools.py` |
| Allocation | FR-062 to FR-063 | `allocation.py`, `limits.py`, `governor.py` | `test_allocation.py` |
| Approval tokens | FR-064 to FR-069b | `approvals.py`, `contracts.py`, `audit.py` | `test_approvals.py`, emergency revocation and security tests |
| Kill switch | FR-070 to FR-073 | `governor.py`, `approvals.py`, `tools.py` | `test_kill_switch_cannot_be_overridden.py` |
| Scenarios and reports | FR-074 to FR-078 | `scenarios.py`, `reports.py` | `test_scenarios.py`, `test_reports.py` |
| Official AI tools | FR-079 to FR-084 | `tools.py`, `__init__.py` | `test_tools.py`, usage tests |
| Determinism/reproducibility | NFR-001 to NFR-004 | all core files | golden/replay tests |
| Performance/scalability | NFR-005 to NFR-014 | calculators/state/governor/scenarios | benchmark tests |
| Reliability/security/audit | NFR-015 to NFR-030 | governor/approvals/audit/tools | failure/security/audit tests |
| Dependency/interface/maintainability | NFR-031 to NFR-040 | all production files | CI/static review |
| Position sizing | NFR-041 to NFR-046 | `sizing.py`, `contracts.py`, `tools.py` | sizing golden/benchmark tests |
| Regime assessment | NFR-047 to NFR-052 | `regimes.py`, `config.py`, `governor.py` | regime golden/transition tests |
| Institutional hardening | FR-086 to FR-095 | `config.py`, `contracts.py`, `calculators.py`, `sizing.py`, `limits.py`, `circuit_breakers.py`, `governor.py`, `audit.py`, `reports.py` | exit-stress, correlation-sizing, step-down, live-freshness, audit-chain, composite-failure tests |
| Institutional hardening NFRs | NFR-056 to NFR-063 | all hardening files | hardening benchmark, replay, and security tests |

---

## 39. Production Acceptance Test Matrix

The module is not production-ready until the following test matrix passes.

| Test Group | Required Coverage | Minimum Acceptance |
|---|---|---|
| Contract tests | All public contracts and invalid payloads | 100% of required contract fields validated. |
| Calculator tests | Exposure, margin, drawdown, VaR, CVaR, volatility, correlation | Expected values match fixtures within documented tolerance. |
| Position sizing tests | fixed_lot, fixed_risk, milestone, Kelly, volatility, fixed_fractional | Expected values match fixtures and broker constraints. |
| Regime tests | regime classification, transitions, missing evidence, limit multipliers | Expected regime states and transitions match fixtures. |
| Limit tests | Pass/warn/fail/block paths | Every configured limit has success and breach tests. |
| Governor tests | Decision truth tables | Every truth-table row has a corresponding test. |
| Approval tests | Create, validate, expire, revoke, emergency kill-switch revocation, mismatch, tamper | Invalid or revoked approval cannot pass. |
| Kill-switch tests | active, inactive, unknown, attempted override | Active/unknown blocks live workflows. |
| Tool-standard tests | Every exported AI tool | Standard schema, metadata, logging, request_id. |
| Workflow tests | pre-trade, position sizing, regime assessment, strategy admission, allocation, live-readiness | End-to-end outputs match contracts. |
| Failure tests | missing evidence, stale evidence, dependency failure, audit failure | No silent success. |
| Security tests | prompt override, token replay, secret logging, permission bypass | All bypass attempts blocked. |
| Institutional hardening tests | exit-liquidity stress, correlation-adjusted sizing, step-down state, live freshness, in-flight tolerance, audit chain, composite failure | All institutional controls produce deterministic decisions and audit evidence. |
| Edge-case hardening tests | step-down startup/restore/reset, audit genesis, correlation fallback, deterministic limit order, in-flight grace expiry | Edge-case controls are deterministic, auditable, and fail closed where required. |
| Performance tests | benchmark scenarios PERF-001 to PERF-012 | p95 targets met or justified. |
| Documentation tests/review | README, tool catalog, config docs, error codes, rejection/block explanation format | Complete before production promotion. |
| Concurrency tests | simultaneous risk decisions, simultaneous sizing calls, cached read/write paths | No mutable global state affects deterministic decisions. |

### 39.1 Final Production Readiness Gate

The risk module can be promoted to production baseline only when:

- all FR and NFR requirements have implementation owners
- all FR and NFR requirements have test evidence or explicit deferral notes
- all official AI tools comply with the HaruQuant Tool Function Standard
- position sizing methods have expected-value fixtures
- regime assessment and transition tests pass
- unit coverage is above 80%
- governor truth-table tests pass
- approval and kill-switch security tests pass
- performance benchmarks are measured with hardware/reference-environment metadata
- audit persistence behavior is verified
- live execution remains outside the risk module

---

## 40. Final Requirement-First Build Rule

The v5.0 risk module specification is a production requirements baseline, not only an architecture note.

Implementation must proceed requirement-first:

```text
requirement
  -> contract
  -> deterministic implementation
  -> unit test
  -> workflow test
  -> audit evidence
  -> acceptance gate
```

No risk capability should be considered complete unless it is traceable through this chain.

---

## v6 Change Log

- Fixed duplicate benchmark IDs.
- Added `max_pending_order_distance_pct` to the example risk configuration YAML.
- Updated benchmark test references to include `PERF-001` to `PERF-009`.


## v7 Change Log

This version adds institutional hardening controls requested after v6 review:

- Added `PortfolioExitLiquidityConfig` and portfolio exit-liquidity stress requirements.
- Added `CorrelationAdjustedSizingConfig` and explicit correlation-adjusted sizing rules.
- Added `RiskStepDownConfig`, `circuit_breakers.py`, and graduated risk step-down requirements.
- Added `LiveRiskStateConfig`, live state freshness rules, and in-flight order tolerance behavior.
- Added cryptographic audit chaining with `previous_hash`, `record_hash`, chain verification, and `AUDIT_CHAIN_TAMPER_DETECTED`.
- Added `primary_failure_limit` and `composite_breach_flags` to `RiskDecisionPackage`.
- Added Kelly fallback behavior with `SIZING_FALLBACK_TO_FIXED_RISK`.
- Added FR-086 to FR-095 and NFR-056 to NFR-063.
- Added benchmark targets PERF-010 to PERF-012.
- Updated traceability and acceptance matrices for institutional hardening tests.

## v8 Change Log

This version adds implementation edge-case hardening clarifications requested after v7 review:

- Added deterministic step-down state initialization, restoration, expiry, reset, and corrupted-state behavior.
- Added the audit-chain genesis rule with a default 64-zero genesis hash.
- Added default production correlation fallback behavior with `SIZING_CORRELATION_FALLBACK_UNAVAILABLE`.
- Added deterministic limit evaluation order requirements for reproducible `primary_failure_limit` and `composite_breach_flags`.
- Added in-flight order reconciliation grace-period expiry behavior, forced portfolio-state refresh, and `IN_FLIGHT_RECONCILIATION_EXPIRED`.
- Added FR-096 to FR-100 and NFR-064 to NFR-068.
- Updated error codes, traceability, and acceptance test matrices for the new edge-case hardening controls.

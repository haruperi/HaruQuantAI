# HaruQuant Portfolio Module Audit and Technical Specification v5

**Source audited:** `portfolio.zip`
**Audited folder:** `portfolio/`
**Date:** 2026-05-31
**Version:** v5 institutional portfolio optimization and rebalancing update
**v5 status:** Production-ready technical specification baseline with institutional portfolio optimization, rebalancing, capacity, benchmark-relative allocation, suspension, and cash-management requirements; implementation is still not production-ready until rebuilt and tested.
**Module type:** Portfolio domain tools and services
**Target system:** HaruQuantAI agentic trading platform
**Primary consumers:** Portfolio Manager Agent, Risk Governor Agent, CEO/Planner workflow, Execution Readiness workflow, reporting/audit workflows

---

## 1. Executive Summary

> **v4 update:** This version keeps the v2/v3 production-readiness additions and applies a final cleanup pass: deterministic error-code list alignment, clearer performance-target language, explicit optional handling for large correlation matrices, and final implementation-readiness wording.

The uploaded `portfolio/` folder contains the early shape of a Portfolio Department module for HaruQuant. It already shows the intended business scope: portfolio exposure inspection, portfolio risk metrics, position sizing, allocation proposals, lifecycle promotion/demotion, risk decision packaging, kill-switch evaluation, reporting, cost governance, incident reporting, and audit checks.

However, the module is **not production-ready**. It is best classified as a **prototype-to-draft implementation** with useful domain intent but insufficient production safeguards. The current implementation mixes tool registry concerns, dynamic service exports, placeholder tool behavior, weak input validation, missing logging, missing unit tests, missing usage examples, non-deterministic side effects through direct artifact writes, and unresolved dependencies on modules that were not included in the uploaded folder.

The module should be kept as a source-of-intent document, not deployed as-is. The recommended next step is a full rewrite into a clean `tools/portfolio/` domain that separates:

1. **Read-only portfolio inspection tools**
2. **Portfolio risk calculation tools**
3. **Position sizing tools**
4. **Allocation proposal and validation tools**
5. **Lifecycle decision tools**
6. **Kill-switch and incident services**
7. **Audit and reporting services**
8. **Typed contracts and tests**

The new implementation must fail closed around live trading and portfolio lifecycle changes.

---

## 2. Audit Scope

### 2.1 Files Audited

| File | Lines | Main Purpose | Current Status |
|---|---:|---|---|
| `portfolio/__init__.py` | 125 | Domain export registry and dynamic service loader | Non-compliant registry pattern |
| `portfolio/standard_tools.py` | 1429 | 34 exported portfolio tools | Too broad, weak validation, no logging |
| `portfolio/allocation_service.py` | 52 | Risk-aware allocation service | Useful draft, not production-ready |
| `portfolio/audit_service.py` | 56 | Portfolio audit checks | Useful draft, not production-ready |
| `portfolio/cost_service.py` | 49 | Cost governance report | Useful draft, not production-ready |
| `portfolio/incident_service.py` | 26 | Incident report creation | Thin wrapper, not production-ready |
| `portfolio/kill_switch.py` | 55 | Portfolio kill switch state | Important but unsafe as implemented |
| `portfolio/lifecycle_service.py` | 52 | Strategy lifecycle transitions | Useful draft, not production-ready |
| `portfolio/reporting_service.py` | 31 | Performance report generation | Useful draft, not production-ready |

### 2.2 Import / Runtime Check

A standalone import check was attempted from the extracted folder.

Result:

```text
ModuleNotFoundError: No module named 'tools'
```

The module cannot be imported outside the wider HaruQuant project because it depends on:

```text
tools.utils.standard
agentic.agents._shared.persistence
agentic.agents.portfolio.shared.contracts
```

This is not automatically wrong inside the full application, but it means the uploaded folder is not independently testable and its dependencies must be explicitly documented and provided.

---

## 3. Production Readiness Verdict

**Verdict:** Not production-ready.

### 3.1 Why It Is Not Production-Ready

The folder is not production-ready because:

- It has **no unit tests** in the uploaded folder.
- It has **no usage examples**.
- It has **no module logger** in any file.
- Exported AI tools use `**kwargs` instead of explicit typed inputs.
- Many exported tools do not validate required inputs robustly.
- Error handling is too thin and often converts domain errors into generic `TOOL_EXECUTION_FAILED`.
- `execution_ms` is hardcoded as `0.0` in the exported tool response helper.
- High-risk lifecycle and allocation tools are packaged as simple request echoes rather than enforcing deterministic policy.
- Service classes write JSON artifacts directly, which creates side effects without dependency injection, error handling, or audit write failure behavior.
- `__init__.py` mixes official tool registry behavior with dynamic service loading.
- Several services depend on missing contracts from `agentic.agents.portfolio.shared.contracts`.
- The module does not provide enough evidence discipline for portfolio decisions that can affect live trading.
- Kill-switch state is in memory only and not safely persisted/restored.

### 3.2 What Is Already Useful

The current folder is still valuable because it captures important business concepts:

- Portfolio risk snapshot
- Open positions and open orders inspection
- Strategy allocations
- Equity curve and return calculations
- Volatility, correlation, VaR, CVaR
- Risk contribution
- Margin usage
- Currency exposure
- Strategy overlap detection
- Symbol cluster risk detection
- Fixed-fractional and volatility-adjusted sizing
- Risk parity and correlation-adjusted sizing
- Margin-aware and cost-adjusted sizing
- Allocation proposal and rebalance packaging
- Allocation validation
- Strategy admission and promotion/demotion lifecycle hooks
- Risk decision package creation
- Kill-switch triggers
- Audit, reporting, incident, and cost services

These capabilities should be preserved in the redesign.

---

## 4. Current Architecture Summary

The current module is structured as follows:

```text
portfolio/
    __init__.py
    standard_tools.py
    allocation_service.py
    audit_service.py
    cost_service.py
    incident_service.py
    kill_switch.py
    lifecycle_service.py
    reporting_service.py
```

### 4.1 Current Public Tool Registry

`portfolio/__init__.py` imports 34 functions from `standard_tools.py` and lists them in `__all__`.

Because HaruQuant treats anything exported through a tool domain `__init__.py` and listed in `__all__` as an official AI Tool, all 34 functions must satisfy the full HaruQuant AI Tool Function Standard.

### 4.2 Current Exported Tools

#### Read / Inspection Tools

- `get_open_positions`
- `get_open_orders`
- `get_strategy_allocations`
- `get_portfolio_equity_curve`

#### Portfolio Risk and Analytics Tools

- `calculate_portfolio_returns`
- `calculate_portfolio_volatility`
- `calculate_portfolio_correlation`
- `calculate_portfolio_var`
- `calculate_portfolio_cvar`
- `calculate_risk_contribution`
- `calculate_margin_usage`
- `calculate_currency_exposure`
- `detect_strategy_overlap`
- `detect_symbol_cluster_risk`
- `build_portfolio_risk_snapshot`

#### Position Sizing Tools

- `calculate_fixed_fractional_size`
- `calculate_volatility_adjusted_size`
- `calculate_risk_parity_weights`
- `calculate_correlation_adjusted_size`
- `calculate_margin_aware_size`
- `calculate_cost_adjusted_size`
- `calculate_max_safe_position_size`

#### Allocation and Lifecycle Decision Tools

- `propose_strategy_allocation`
- `rebalance_strategy_allocations`
- `validate_allocation_proposal`
- `admit_strategy_to_portfolio`
- `promote_strategy_to_paper`
- `promote_strategy_to_live_candidate`
- `suspend_strategy`
- `retire_strategy`
- `demote_strategy_to_paper`
- `update_strategy_status`
- `build_risk_decision_package`

### 4.3 Current Service Classes

The folder also defines these service classes:

- `AllocationService`
- `PortfolioAuditService`
- `CostService`
- `IncidentService`
- `PortfolioKillSwitch`
- `LifecycleService`
- `ReportingService`

They are not listed in `__all__`, but `__init__.py` exposes them dynamically through `__getattr__`. This blurs the boundary between official AI tools and internal services.

---

## 5. File-by-File Audit

## 5.1 `portfolio/__init__.py`

### Purpose

Acts as a portfolio domain registry and dynamic service loader.

### Strengths

- Has a module-level docstring.
- Clearly lists official tool exports in `__all__`.
- Imports tools from `standard_tools.py` into the domain package.

### Critical Issues

- Imports `standardize_domain_exports` and `standardize_tool_callable`, which hides behavior at import time.
- Calls `standardize_domain_exports(globals(), __all__, tool_category="portfolio")` at import time, which mutates exported callables dynamically.
- Uses `__getattr__` to expose service classes dynamically while not listing them in `__all__`.
- Imports service-related standardization logic into a tool registry file.
- Violates the ideal registry rule: `__init__.py` should only import approved tools and define `__all__`.

### Required Refactor

Replace with a simple registry:

```python
"""Portfolio tools exposed to HaruQuant agents."""

# exposure.py tools
from tools.portfolio.exposure import get_open_positions
from tools.portfolio.exposure import get_open_orders
from tools.portfolio.exposure import get_strategy_allocations
from tools.portfolio.exposure import get_portfolio_equity_curve

# risk.py tools
from tools.portfolio.risk import calculate_portfolio_returns
...

__all__ = [
    "get_open_positions",
    ...
]
```

Service classes should be imported directly from their implementation modules by internal code, not dynamically exported through the AI tool registry.

---

## 5.2 `portfolio/standard_tools.py`

### Purpose

Contains all exported portfolio AI tools in one file.

### Strengths

- Captures a wide set of necessary portfolio capabilities.
- Uses a common `_result()` helper to return structured responses.
- Separates internal helper names using leading underscores.
- Provides long docstrings for many tools.

### Critical Issues

- The file is too large and should be split by domain responsibility.
- All public tools accept `**kwargs`, which weakens type safety and agent usability.
- No module logger is imported or used.
- No per-tool metadata constants exist.
- No real timing is recorded; `execution_ms` is always `0.0`.
- No `try/except` tool boundary exists around calculations.
- Pandas numeric conversion can silently drop invalid data without returning validation warnings.
- Several tools default missing inputs to empty lists/dicts and return success instead of `INVALID_INPUT` or `EMPTY_RESULT` where appropriate.
- High-risk tools only package requests and do not enforce approval, evidence, or policy constraints.
- Tool risk level defaults to `medium` in `_result()`, which can misclassify read-only tools if the caller forgets to pass `risk_level="low"`.
- The current docstrings describe a non-standard return envelope containing fields like `tool_call_id`, `agent_name`, `environment`, `dry_run`, `warnings`, and audit metadata, while the actual helper returns the `standard_tool_response` envelope. This creates documentation drift.

### Required Refactor

Split into:

```text
tools/portfolio/exposure.py
tools/portfolio/risk.py
tools/portfolio/sizing.py
tools/portfolio/allocation.py
tools/portfolio/lifecycle.py
tools/portfolio/risk_package.py
```

Each official tool must have:

- Explicit parameters
- `request_id: Optional[str] = None`
- Real input validation
- Structured logging
- Real execution timing
- Deterministic error codes
- Accurate risk metadata
- Accurate side-effect metadata
- Tests and usage examples

---

## 5.3 `portfolio/allocation_service.py`

### Purpose

Validates and proposes risk-aware strategy capital allocation.

### Strengths

- Implements meaningful allocation constraints.
- Checks lifecycle eligibility.
- Checks total allocation against available capital.
- Checks strategy, symbol, and cluster concentration.
- Writes an audit artifact.

### Critical Issues

- No logger.
- No exception handling around artifact writing.
- No validation that allocations are non-negative.
- No validation that available capital is positive.
- No validation that all allocation keys exist in lifecycle states.
- Hardcoded eligible states do not clearly map to the lifecycle enum used elsewhere.
- Directly writes to `data/logs/portfolio`, making the service difficult to unit test.
- Does not accept `request_id` or `workflow_id`.
- Uses one method for validation and artifact creation, mixing pure business logic with I/O.

### Required Refactor

Split into:

- `validate_allocation_constraints()` pure function
- `build_allocation_decision()` pure function
- `AllocationService.propose()` orchestration method with injected audit writer
- Official AI tool wrapper `propose_strategy_allocation()` if agent-callable

---

## 5.4 `portfolio/audit_service.py`

### Purpose

Checks whether portfolio execution/lifecycle evidence is complete.

### Strengths

- Captures key audit findings:
  - missing risk governor approval
  - approval/order mismatch
  - unauthorized risk threshold changes
  - skipped lifecycle stage
  - missing board approval
  - missing evidence/logs/broker responses
  - hidden failed tool calls
- Flags critical failures as disabling live trading.

### Critical Issues

- No typed snapshot contract.
- No severity enum.
- No logger.
- No request/workflow IDs.
- No exception handling for artifact writing.
- No separation between audit evaluation and audit persistence.
- Does not produce a hash-chain audit record.

### Required Refactor

Create typed contracts:

- `PortfolioAuditSnapshot`
- `PortfolioAuditFinding`
- `PortfolioAuditReport`

Audit persistence should support:

- append-only JSONL
- audit record hash
- previous hash
- redaction
- request/workflow IDs

---

## 5.5 `portfolio/cost_service.py`

### Purpose

Aggregates model, task, workflow, strategy, and compute costs.

### Strengths

- Groups cost by agent, provider, model, task, workflow, and strategy.
- Tracks token usage.
- Detects failed call costs.
- Tracks backtest compute cost.
- Protects deterministic risk/execution decision types from LLM routing.
- Flags budget exceeded.

### Critical Issues

- No logger.
- No validation for period, usage schema, or budget.
- No negative-cost protection.
- No currency field.
- No configurable protected decision types.
- Direct artifact write has no error strategy.
- Does not distinguish soft budget warning vs hard workflow block.

### Required Refactor

Add:

- `CostUsageRecord`
- `CostBudgetPolicy`
- `CostReport`
- `validate_cost_usage_records()`
- `detect_cost_anomalies()`
- injected audit writer

---

## 5.6 `portfolio/incident_service.py`

### Purpose

Creates an incident report and writes an audit artifact.

### Strengths

- Very small and simple.
- Uses the existing `IncidentReport` contract.

### Critical Issues

- Thin pass-through with no validation.
- No logger.
- No error handling.
- No severity normalization.
- No required incident fields enforced locally.
- Direct artifact write.
- No request/workflow traceability.

### Required Refactor

Require fields:

- `incident_id`
- `severity`
- `trigger`
- `affected_strategy_ids`
- `affected_account_ids`
- `detected_at`
- `required_action`
- `request_id`
- `workflow_id`

---

## 5.7 `portfolio/kill_switch.py`

### Purpose

Evaluates portfolio safety conditions and triggers a live-trading kill switch.

### Strengths

- Contains important fail-closed triggers:
  - critical audit failure
  - risk governor unavailable
  - audit logging unavailable
  - broker heartbeat failure
  - daily/weekly/account/strategy drawdown limits
  - spread and slippage spikes
  - repeated order failure
- Resume requires approval ID.

### Critical Issues

- State is in-memory only.
- Cold-start behavior is undefined.
- Triggered state is not restored from persisted state.
- No logger.
- No exception handling around audit writes.
- Threshold defaults are hardcoded and inconsistent with the broader 5% daily / 10% total prop-firm policy unless configured elsewhere.
- Uses raw floats from snapshot without validating units, sign conventions, or percentage representation.
- Resume only checks that `approval_id` exists, not whether approval is valid, unexpired, and authorized.
- No account/broker action integration contract.
- No deterministic `kill_switch_active` contract for execution tools.

### Required Refactor

Create:

- `KillSwitchStateStore`
- `KillSwitchPolicy`
- `KillSwitchSnapshot`
- `KillSwitchDecision`
- `evaluate_kill_switch()` pure function
- `PortfolioKillSwitchService` with persistence and approval validation

Cold-start rule:

```text
On startup, restore the latest non-expired kill-switch state. If none exists, default to healthy and write a KILL_SWITCH_STATE_INITIALIZED audit record.
```

---

## 5.8 `portfolio/lifecycle_service.py`

### Purpose

Controls allowed strategy lifecycle transitions.

### Strengths

- Defines an explicit allowed transition map.
- Blocks micro-live/live without board approval.
- Blocks micro-live/live if risk governor compatibility is false.
- Requires strategy review evidence before paper live.
- Writes lifecycle audit artifact.

### Critical Issues

- No logger.
- No exception handling.
- No request/workflow IDs.
- No approval validity checking.
- No evidence freshness checking.
- No transition idempotency key.
- No actor permission check.
- Allows live transitions based on `board_approval_id` existence only.
- Directly imports lifecycle contracts from `agentic.agents.portfolio.shared.contracts`; portfolio contracts should be in a shared contracts layer, not under an agent folder.

### Required Refactor

Create lifecycle policy module:

```text
tools/portfolio/lifecycle_policy.py
```

It should enforce:

- allowed transition graph
- required evidence by transition
- approval requirements
- risk governor compatibility
- paper-trading duration/performance requirements
- idempotent transition handling
- audit record creation

---

## 5.9 `portfolio/reporting_service.py`

### Purpose

Builds a portfolio performance report.

### Strengths

- Checks required report fields.
- Marks report incomplete when audit gaps exist.
- Adds critical audit/risk findings to required decisions.

### Critical Issues

- No logger.
- No report schema validation beyond three fields.
- No metric definitions.
- No reporting period.
- No benchmark fields.
- No TCA/cost fields.
- No multi-currency treatment.
- Direct artifact write.

### Required Refactor

Add report contract fields:

- `report_id`
- `report_type`
- `period_start`
- `period_end`
- `account_currency`
- `portfolio_pnl`
- `portfolio_return`
- `drawdown`
- `trade_count`
- `win_rate`
- `profit_factor`
- `sharpe`
- `sortino`
- `var_95`
- `cvar_95`
- `margin_usage`
- `risk_contribution`
- `strategy_health`
- `decision_required`
- `evidence_refs`

---

## 6. Current Capability Model

The current portfolio module appears intended to support these business workflows:

### 6.1 Portfolio Observation Workflow

```text
Get open positions
Get open orders
Get allocations
Get equity curve
Calculate returns / volatility / correlation
Build risk snapshot
Return PortfolioStatePackage
```

### 6.2 Portfolio Risk Review Workflow

```text
PortfolioStatePackage
Risk contribution
Margin usage
Currency exposure
Cluster risk
Strategy overlap
VaR / CVaR
Risk decision package
Risk Governor review
```

### 6.3 Position Sizing Workflow

```text
Inputs: equity, risk fraction, stop distance, pip value, volatility, correlation, margin, costs
Fixed fractional size
Volatility-adjusted size
Correlation adjustment
Margin-aware cap
Cost adjustment
Max safe size
Return PositionSizingDecision
```

### 6.4 Allocation Workflow

```text
Strategy candidates
Lifecycle states
Available capital
Risk constraints
Symbol exposure
Cluster exposure
Allocation proposal
Allocation validation
Board approval if required
Allocation decision
Audit record
```

### 6.5 Strategy Lifecycle Workflow

```text
idea
spec
coded
reviewed
backtested
diagnosed
optimized
robustness_tested
statistically_validated
paper_candidate
paper_live
micro_live_candidate
micro_live
live_candidate
live
paused / retired / rejected
```

### 6.6 Kill-Switch Workflow

```text
Safety snapshot
Evaluate hard triggers
If triggered: disable new orders, require manual review
Persist kill-switch audit record
Resume only after valid approval
```

### 6.7 Reporting and Audit Workflow

```text
Collect portfolio performance data
Collect evidence refs
Collect execution logs
Collect broker responses
Detect missing evidence
Generate performance/audit/cost/incident report
Persist report
```

---

## 7. Production Technical Specification

## 7.1 Purpose

The HaruQuant Portfolio Module shall provide deterministic, typed, auditable portfolio-level capabilities for strategy allocation, portfolio exposure, portfolio risk, position sizing, lifecycle governance, portfolio reporting, incident tracking, cost governance, and kill-switch state control.

It must support agentic workflows but must not rely on LLM judgment for safety-critical decisions.

## 7.2 Goals

The module must:

- Provide official AI-callable portfolio tools under `tools/portfolio/`.
- Support Portfolio Manager Agent and Risk Governor Agent workflows.
- Calculate portfolio-level risk metrics deterministically.
- Validate strategy allocation proposals before portfolio admission.
- Control strategy lifecycle transitions through deterministic rules.
- Generate portfolio risk decision packages for risk review.
- Enforce fail-closed kill-switch behavior.
- Emit structured logs and audit records.
- Be fully testable with unit tests and usage examples.
- Support MT5 live-trading context indirectly through execution/risk modules.

## 7.3 Non-Goals

The portfolio module must not:

- Place trades directly.
- Close live positions directly.
- Bypass the Risk Governor.
- Approve live trading by itself.
- Replace the execution module.
- Store broker credentials.
- Invent missing portfolio exposure or performance data.
- Allow LLM output to override deterministic policy.

---

## 8. Recommended Target Folder Structure

```text
tools/
    portfolio/
        __init__.py
        contracts.py
        schemas.py
        exposure.py
        risk.py
        sizing.py
        allocation.py
        lifecycle.py
        kill_switch.py
        reporting.py
        audit.py
        cost.py
        incidents.py
        errors.py
        validators.py

    utils/
        logger.py
        result.py
        ids.py
        time.py

tests/
    unit/
        tools/
            portfolio/
                test_exposure.py
                test_risk.py
                test_sizing.py
                test_allocation.py
                test_lifecycle.py
                test_kill_switch.py
                test_reporting.py
                test_audit.py
                test_cost.py
                test_incidents.py
                test_registry.py

    usage/
        tools/
            portfolio/
                exposure.py
                risk.py
                sizing.py
                allocation.py
                lifecycle.py
                kill_switch.py
                reporting.py
```

### 8.1 Registry Rule

`tools/portfolio/__init__.py` must only expose approved official tools. It must not contain business logic or dynamic mutation.

### 8.2 Services vs Tools

Use this separation:

| Type | Responsibility | Return Style |
|---|---|---|
| Pure helper | Small internal calculation | Native typed value |
| Service | Deterministic domain orchestration | Typed contract object |
| Official AI Tool | Agent-callable boundary | Standard HaruQuant tool response dict |

---

## 9. Required Contracts

The portfolio module should define or import these typed contracts from a stable shared contracts layer.

### 9.1 Portfolio State Contracts

```text
PortfolioPosition
PortfolioOrder
StrategyAllocation
PortfolioEquityPoint
PortfolioStateSnapshot
PortfolioRiskSnapshot
```

### 9.2 Risk Contracts

```text
PortfolioReturnsResult
PortfolioVolatilityResult
PortfolioCorrelationResult
PortfolioVaRResult
PortfolioCVaRResult
RiskContributionResult
MarginUsageResult
CurrencyExposureResult
ClusterRiskResult
StrategyOverlapResult
```

### 9.3 Sizing Contracts

```text
PositionSizingInput
PositionSizingResult
FixedFractionalSizingResult
VolatilityAdjustedSizingResult
CorrelationAdjustedSizingResult
MarginAwareSizingResult
CostAdjustedSizingResult
MaxSafePositionSizeResult
```

### 9.4 Allocation Contracts

```text
AllocationProposal
AllocationConstraintPolicy
AllocationDecision
AllocationValidationResult
RebalanceProposal
RebalanceDecision
```

### 9.5 Lifecycle Contracts

```text
StrategyLifecycleState
LifecycleTransitionRequest
LifecycleTransitionDecision
LifecycleEvidenceRequirement
LifecycleApprovalRequirement
```

### 9.6 Kill-Switch Contracts

```text
KillSwitchPolicy
KillSwitchSnapshot
KillSwitchTrigger
KillSwitchDecision
KillSwitchState
KillSwitchResumeRequest
```

### 9.7 Reporting / Audit / Incident Contracts

```text
PortfolioPerformanceReport
PortfolioAuditSnapshot
PortfolioAuditReport
PortfolioAuditFinding
PortfolioIncidentReport
PortfolioCostUsageRecord
PortfolioCostReport
```

---

## 10. Official Tool Specification

Every official portfolio tool must return:

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
        "tool_category": "portfolio",
        "tool_risk_level": "low" | "medium" | "high" | "critical",
        "request_id": str | None,
        "execution_ms": float,
        "read_only": bool,
        "writes_file": bool,
        "modifies_database": bool,
        "places_trade": bool,
        "requires_network": bool,
    },
}
```

### 10.1 Required Tool Metadata

Every official tool must define or pass:

```python
TOOL_NAME = "..."
TOOL_VERSION = "1.0.0"
TOOL_CATEGORY = "portfolio"
TOOL_RISK_LEVEL = "low | medium | high | critical"
REQUIRES_APPROVAL = False | True
READ_ONLY = True | False
WRITES_FILE = True | False
MODIFIES_DATABASE = True | False
PLACES_TRADE = False
REQUIRES_NETWORK = False | True
```

Portfolio tools must not place trades. `PLACES_TRADE` should always be `False` inside this module. Trade placement belongs to the execution module.

---

## 11. Functional Requirements

## 11.1 Exposure Tools

### FR-EXPOSURE-001: Open Positions

The module shall provide a tool to return current open positions from supplied portfolio state or an injected repository.

Required behavior:

- Validate position records.
- Return count and normalized positions.
- Return `EMPTY_RESULT` if no positions and caller requires active positions.
- Never call broker directly unless explicitly configured as a read-only repository integration.

### FR-EXPOSURE-002: Open Orders

The module shall provide a tool to return current open orders.

Required behavior:

- Validate order IDs, symbol, side, volume, price, status.
- Clearly distinguish pending order vs market position.

### FR-EXPOSURE-003: Strategy Allocations

The module shall return strategy allocation weights and capital allocations.

Required behavior:

- Validate sum of weights.
- Validate no negative allocation.
- Validate no unknown strategy IDs if strategy registry is supplied.

### FR-EXPOSURE-004: Equity Curve

The module shall return a normalized portfolio equity curve.

Required behavior:

- Validate monotonic timestamps.
- Validate positive equity values.
- Reject duplicate timestamps unless deduplication policy is explicit.

---

## 11.2 Risk Tools

### FR-RISK-001: Returns

The module shall calculate portfolio returns from an equity curve.

Required behavior:

- Reject fewer than two equity points.
- Reject zero or negative equity values.
- Support simple returns as default.
- Optionally support log returns with explicit parameter.

### FR-RISK-002: Volatility

The module shall calculate volatility from returns.

Required behavior:

- Validate enough return observations.
- Support configurable annualization factor.
- Return both period volatility and annualized volatility where applicable.

### FR-RISK-003: Correlation

The module shall calculate a correlation matrix from aligned return series.

Required behavior:

- Align timestamps deterministically.
- Reject unaligned series unless fill policy is explicit.
- Return warning for insufficient observations.

### FR-RISK-004: VaR and CVaR

The module shall calculate historical VaR and CVaR.

Required behavior:

- Validate confidence level.
- Support `alpha` / confidence naming consistently.
- Return loss-positive convention clearly.
- Do not mix percentage returns and currency values without explicit conversion.

### FR-RISK-005: Risk Contribution

The module shall calculate risk contribution by strategy, symbol, and currency cluster.

Required behavior:

- Validate exposures and risk weights.
- Return total exposure and contribution percentages.

### FR-RISK-006: Margin Usage

The module shall calculate margin utilization.

Required behavior:

- Validate equity > 0.
- Validate used margin >= 0.
- Return utilization ratio and safety status.

### FR-RISK-007: Currency Exposure

The module shall calculate FX currency basket exposure.

Required behavior:

- Parse symbols deterministically.
- Handle metals/indices/crypto through explicit instrument metadata.
- Return unknown instrument errors where pair decomposition is unsafe.

### FR-RISK-008: Strategy Overlap

The module shall detect overlapping strategies.

Required behavior:

- Check symbol overlap.
- Check timeframe overlap.
- Check strategy family/type overlap.
- Check correlation evidence if supplied.

### FR-RISK-009: Cluster Risk

The module shall detect concentrated exposure by symbol cluster/currency cluster.

Required behavior:

- Use configurable thresholds.
- Return per-cluster status.
- Fail closed if cluster mapping is missing for high-risk decisions.

---

## 11.3 Position Sizing Tools

### FR-SIZING-001: Fixed Fractional Size

The module shall calculate position size from equity, risk fraction, stop distance, and pip value.

Required behavior:

- Validate equity > 0.
- Validate 0 < risk_fraction <= configured max.
- Validate stop_distance > 0.
- Validate pip_value > 0.
- Return size and risk amount.

### FR-SIZING-002: Volatility Adjustment

The module shall reduce/increase base size using target vs observed volatility.

Required behavior:

- Validate observed volatility > 0.
- Validate target volatility > 0.
- Cap leverage increase.

### FR-SIZING-003: Correlation Adjustment

The module shall reduce size when proposed exposure is correlated with portfolio exposure.

Required behavior:

- Validate -1 <= correlation <= 1.
- Apply size penalty above configured threshold.
- For HaruQuant FX policy, correlation acceptance threshold should support `< 0.5` as a configurable default.

### FR-SIZING-004: Margin-Aware Size

The module shall cap position size by free margin and margin per unit.

Required behavior:

- Validate free margin >= 0.
- Validate margin per unit > 0.
- Apply safety buffer.

### FR-SIZING-005: Cost-Adjusted Size

The module shall reduce or reject size when trading costs exceed allowed cost ratio.

Required behavior:

- Include spread, commission, expected slippage, and swap where available.
- Return cost reason codes.

### FR-SIZING-006: Max Safe Position Size

The module shall combine risk size, margin size, policy cap, correlation cap, and cost cap.

Required behavior:

- Return the minimum safe size.
- Return the binding constraint.
- Return all intermediate size caps.

---

## 11.4 Allocation Requirements

### FR-ALLOC-001: Strategy Allocation Proposal

The module shall propose capital allocation across eligible strategies.

Required behavior:

- Support equal capital, confidence-weighted, risk parity, and manual proposal modes.
- Validate lifecycle eligibility.
- Validate strategy max allocation.
- Validate symbol max allocation.
- Validate cluster max allocation.
- Validate total allocation <= available capital.
- Reject negative allocation.

### FR-ALLOC-002: Rebalancing

The module shall create rebalancing proposals.

Required behavior:

- Compare current vs target allocations.
- Calculate rebalance deltas.
- Enforce turnover limits.
- Require approval for material changes.

### FR-ALLOC-003: Allocation Validation

The module shall validate proposed allocation weights.

Required behavior:

- Sum weights within tolerance.
- Enforce max weight.
- Enforce min/max number of active strategies.
- Enforce concentration limits.

---

## 11.5 Lifecycle Requirements

### FR-LIFE-001: Strategy Admission

The module shall package strategy admission requests.

Required behavior:

- Require strategy ID.
- Require strategy specification reference.
- Require validation evidence reference.
- Require risk compatibility evidence.

### FR-LIFE-002: Paper Promotion

The module shall only promote strategy to paper trading when required evidence exists.

Required evidence:

- strategy review
- backtest report
- risk pre-check
- configuration validation

### FR-LIFE-003: Live Candidate Promotion

The module shall only promote to live candidate when paper evidence exists.

Required evidence:

- paper trading performance
- drawdown report
- execution quality report
- risk governor compatibility
- board approval request package

### FR-LIFE-004: Live State Changes

The module shall not approve live state changes by itself.

Live activation requires:

- Risk Governor approval
- valid board approval
- kill switch healthy
- broker/execution readiness
- audit writer available
- explicit human approval

### FR-LIFE-005: Suspension, Retirement, Demotion

The module shall support strategy suspension, retirement, and demotion.

Required behavior:

- Suspension and retirement must produce audit records.
- Live demotion must be allowed as a protective action, but any broker order action must be delegated to execution.

---

## 11.6 Kill-Switch Requirements

### FR-KILL-001: Trigger Evaluation

The kill switch shall evaluate safety snapshots against deterministic policy.

Required triggers:

- critical audit failure
- risk governor unavailable
- audit writer unavailable
- broker heartbeat failed
- daily loss limit breached
- total drawdown limit breached
- strategy drawdown limit breached
- spread spike
- slippage spike
- repeated order failures
- margin danger
- unauthorized live state mutation

### FR-KILL-002: Persistence

Kill-switch state shall be persisted and restored on startup.

### FR-KILL-003: Resume

Resume shall require valid approval, not merely a non-empty approval ID.

### FR-KILL-004: Execution Integration

Execution module must check kill-switch state before any live action.

---

## 11.7 Audit Requirements

### FR-AUDIT-001: Audit Records

Every high-risk portfolio decision shall emit an audit record.

Required fields:

```text
timestamp
request_id
workflow_id
tool_name/service_name
action
input_summary
decision
evidence_refs
approval_refs
risk_level
status
error_code
previous_hash
record_hash
```

### FR-AUDIT-002: Audit Failure Behavior

If audit writing fails for high-risk or live-adjacent decisions, the module must fail closed.

---

## 11.8 Reporting Requirements

The portfolio module shall generate:

- daily portfolio report
- weekly portfolio report
- monthly portfolio report
- strategy health report
- allocation report
- risk contribution report
- audit exception report
- cost governance report
- incident report

Reports must clearly label missing evidence and incomplete fields.

---

## 12. Non-Functional Requirements

## 12.1 Reliability

- Deterministic calculations must be reproducible.
- Missing evidence must not be silently treated as safe.
- High-risk workflows must fail closed.

## 12.2 Maintainability

- Files should be focused and under reasonable size.
- `standard_tools.py` must be split.
- Business logic should be separated from tool response formatting.
- I/O should be injected or isolated.

## 12.3 Type Safety

- Official tools should use explicit typed parameters.
- Service methods should use Pydantic/dataclass contracts.
- Avoid `**kwargs` for official tools except where unavoidable.

## 12.4 Observability

Every tool/service should log:

- call started
- validation failed
- policy blocked
- decision accepted/rejected
- audit write succeeded/failed
- call completed
- exception occurred

Do not log secrets, broker credentials, or account passwords.

## 12.5 Security and Safety

- Portfolio module cannot place trades.
- Portfolio module cannot override kill switch.
- Portfolio module cannot approve its own live state changes.
- Approval tokens must be validated by governance/approval service.
- Broker-facing actions belong to execution tools.

## 12.6 Performance

- Pandas is acceptable for small/medium portfolio analytics.
- Large multi-strategy portfolios should support vectorized calculations.
- Repeated calculations should be cacheable by request/workflow context where safe.

---

## 13. Error Code Standard

Use deterministic portfolio error codes:

```text
INVALID_INPUT
EMPTY_RESULT
DATA_NOT_FOUND
INSUFFICIENT_DATA
VALIDATION_FAILED
POLICY_BLOCKED
APPROVAL_REQUIRED
APPROVAL_INVALID
MISSING_EVIDENCE
STALE_EVIDENCE
AUDIT_WRITE_FAILED
KILL_SWITCH_ACTIVE
RISK_LIMIT_EXCEEDED
MARGIN_LIMIT_EXCEEDED
CORRELATION_LIMIT_EXCEEDED
CONCENTRATION_LIMIT_EXCEEDED
LIFECYCLE_TRANSITION_INVALID
TOOL_EXECUTION_FAILED
UNKNOWN_ERROR
```

---

## 14. Risk Classification

| Capability | Risk Level | Approval Required | Notes |
|---|---|---|---|
| Read positions/orders from supplied state | Low | No | Read-only |
| Calculate returns/volatility/correlation | Low | No | Deterministic analytics |
| Calculate VaR/CVaR | Low/Medium | No | Medium if used for gating live actions |
| Build risk snapshot | Medium | No | Decision input, not decision itself |
| Calculate position size | Medium | No | Must not place trade |
| Validate allocation | Medium | No | May feed high-risk decision |
| Propose allocation | High | Sometimes | Capital allocation changes require approval if material |
| Lifecycle promotion to paper | High | Yes if state mutation | Must check evidence |
| Lifecycle promotion to live candidate | High | Yes | Live-adjacent |
| Live activation | Critical | Yes | Should not be owned by portfolio module |
| Kill-switch trigger | Critical protective | No approval to trigger | Must audit |
| Kill-switch resume | Critical | Yes | Must validate approval |

---

## 15. Agentic Workflow Integration

## 15.1 Portfolio Manager Agent

The Portfolio Manager Agent may use portfolio tools to:

- inspect portfolio state
- calculate exposure
- propose allocation
- package allocation decisions
- recommend promotion/demotion

It must not:

- place trades
- approve live trading
- override kill switch
- ignore Risk Governor rejection

## 15.2 Risk Governor Agent

The Risk Governor Agent consumes:

- `PortfolioRiskSnapshot`
- `RiskContributionResult`
- `MarginUsageResult`
- `CurrencyExposureResult`
- `ClusterRiskResult`
- `AllocationDecision`
- `LifecycleTransitionDecision`

It returns:

- approve / reject / needs more evidence
- risk decision package
- evidence references

## 15.3 Execution Module

The execution module must consume portfolio outputs but remain the only module allowed to call broker execution tools.

Before live order placement, execution must verify:

- risk approval token
- portfolio allocation allowance
- kill switch healthy
- account margin health
- broker heartbeat healthy
- audit logging available

---

## 16. Testing Specification

## 16.1 Unit Tests Required

At minimum, create these files:

```text
tests/unit/tools/portfolio/test_exposure.py
tests/unit/tools/portfolio/test_risk.py
tests/unit/tools/portfolio/test_sizing.py
tests/unit/tools/portfolio/test_allocation.py
tests/unit/tools/portfolio/test_lifecycle.py
tests/unit/tools/portfolio/test_kill_switch.py
tests/unit/tools/portfolio/test_reporting.py
tests/unit/tools/portfolio/test_audit.py
tests/unit/tools/portfolio/test_cost.py
tests/unit/tools/portfolio/test_incidents.py
tests/unit/tools/portfolio/test_registry.py
```

## 16.2 Test Cases Required

### Exposure Tests

- returns supplied positions
- empty positions returns valid empty response or `EMPTY_RESULT` depending on mode
- invalid position schema rejected
- request_id propagated
- standard schema compliance

### Risk Tests

- returns calculated from valid equity curve
- rejects too few observations
- rejects zero/negative equity
- calculates volatility correctly
- calculates correlation matrix correctly
- handles unaligned series according to policy
- VaR/CVaR confidence validation
- standard schema compliance

### Sizing Tests

- fixed fractional success
- invalid equity rejected
- invalid stop distance rejected
- invalid pip value rejected
- correlation adjustment threshold behavior
- margin cap binding constraint
- cost cap binding constraint

### Allocation Tests

- equal capital success
- confidence-weighted success
- total allocation exceeds capital rejected
- strategy allocation limit rejected
- symbol concentration rejected
- cluster concentration rejected
- stale allocation table rejected
- negative allocation rejected

### Lifecycle Tests

- valid transitions accepted
- invalid transition rejected
- paper promotion without strategy review rejected
- live transition without board approval rejected
- live transition without risk compatibility rejected
- approval ID existence alone is insufficient

### Kill-Switch Tests

- healthy snapshot returns healthy
- critical audit failure triggers
- risk governor unavailable triggers
- audit logging unavailable triggers
- broker heartbeat failed triggers
- daily loss limit triggers
- total drawdown limit triggers
- spread spike triggers
- slippage spike triggers
- repeated order failure triggers
- resume without valid approval rejected
- persisted triggered state restored on startup

### Audit Tests

- audit report identifies missing evidence
- audit report identifies approval/order mismatch
- audit write failure causes fail-closed result for high-risk decision
- audit record includes request_id/workflow_id
- audit hash chain is deterministic

### Registry Tests

- every `__all__` export imports successfully
- no service classes exported accidentally
- every official tool returns standard schema
- every official tool has request_id support
- every official tool has metadata

---

## 17. Usage Examples Required

Create usage examples for:

```text
tests/usage/tools/portfolio/exposure.py
tests/usage/tools/portfolio/risk.py
tests/usage/tools/portfolio/sizing.py
tests/usage/tools/portfolio/allocation.py
tests/usage/tools/portfolio/lifecycle.py
tests/usage/tools/portfolio/kill_switch.py
tests/usage/tools/portfolio/reporting.py
```

Each usage example should:

- call the official domain import, e.g. `from tools.portfolio import calculate_portfolio_var`
- include a realistic `request_id`
- handle both success and error responses
- avoid mocks
- show how an agent/workflow consumes the result

---

## 18. Supporting Files Required

The rewrite should include:

```text
tools/portfolio/__init__.py
tools/portfolio/contracts.py
tools/portfolio/errors.py
tools/portfolio/validators.py
tools/portfolio/exposure.py
tools/portfolio/risk.py
tools/portfolio/sizing.py
tools/portfolio/allocation.py
tools/portfolio/lifecycle.py
tools/portfolio/kill_switch.py
tools/portfolio/reporting.py
tools/portfolio/audit.py
tools/portfolio/cost.py
tools/portfolio/incidents.py
```

Optional but recommended:

```text
docs/specs/HaruQuant_Portfolio_Module_Technical_Specification.md
docs/tools/Portfolio_Tool_Catalog.md
docs/workflows/Portfolio_Workflow_Catalog.md
```

---

## 19. Implementation Plan

## Phase 1: Contracts and Registry

Deliverables:

- `contracts.py`
- `errors.py`
- `validators.py`
- clean `__init__.py`
- registry tests

Exit criteria:

- all exported names import successfully
- no dynamic export mutation
- no service classes accidentally exposed as tools

## Phase 2: Read-Only Exposure and Risk Tools

Deliverables:

- `exposure.py`
- `risk.py`
- tests and usage examples

Exit criteria:

- deterministic risk calculations
- explicit input validation
- standard return schema
- coverage above 80%

## Phase 3: Position Sizing Tools

Deliverables:

- `sizing.py`
- position sizing contracts
- tests and usage examples

Exit criteria:

- fixed-fractional, volatility, correlation, margin, cost, and max-safe size tested
- invalid sizing inputs fail safely

## Phase 4: Allocation and Lifecycle

Deliverables:

- `allocation.py`
- `lifecycle.py`
- allocation/lifecycle contracts
- tests and examples

Exit criteria:

- no live-adjacent transition can pass without required evidence and approval
- material allocation changes are approval-aware

## Phase 5: Kill Switch, Audit, Reporting, Incidents, Cost

Deliverables:

- `kill_switch.py`
- `audit.py`
- `reporting.py`
- `incidents.py`
- `cost.py`
- persistence abstraction
- tests and examples

Exit criteria:

- kill-switch state persists and restores
- audit write failure behavior is tested
- reports clearly mark incomplete evidence

## Phase 6: Integration with Risk and Execution

Deliverables:

- portfolio risk package consumed by Risk Governor
- kill switch checked by execution readiness
- lifecycle state used by live activation workflow

Exit criteria:

- portfolio module cannot place trades
- execution cannot place live trades when kill switch is active
- all high-risk decisions produce audit records

---


---

## 19A. v2 Production Specification Hardening Addendum

This section upgrades the v1 audit/specification into an implementation-ready technical specification. It does **not** make the uploaded implementation production-ready. It defines the missing rules required before rewriting the module.

### 19A.1 Production Specification Verdict

**Specification verdict after v2:** Production-ready as a technical specification baseline, later superseded by v3 refinements.

**Implementation verdict remains:** Not production-ready until the module is rewritten, tested, integrated, and validated against this specification.

The v2 specification is now sufficiently explicit for implementation because it defines:

- exact official tool signatures
- official portfolio contracts
- data source ownership
- MT5 live-trading integration boundaries
- deterministic formula and unit conventions
- multi-currency and instrument metadata rules
- approval token validation
- kill-switch persistence and cold-start behavior
- idempotency and concurrency behavior
- audit hash-chain genesis behavior
- implementation-readiness gates

---

## 19B. Official Tool Signatures

All official portfolio tools must live under `tools/portfolio/` and be exported through `tools/portfolio/__init__.py`. Anything listed in `__all__` is an official AI Tool and must follow the HaruQuant AI Tool Function Standard.

All official tools must:

- use explicit typed parameters
- accept `request_id: Optional[str] = None`
- return `dict[str, Any]` using the standard tool response schema
- never use `**kwargs` as the public signature
- validate external inputs before execution
- include real `execution_ms`
- return deterministic error codes
- log call, validation failure, success, and failure

### 19B.1 Exposure and Inspection Tools

```python
from typing import Any, Literal, Optional


def get_open_positions(
    portfolio_id: str,
    account_id: str,
    position_source: Literal["snapshot", "repository", "in_memory"] = "snapshot",
    as_of: Optional[str] = None,
    request_id: Optional[str] = None,
) -> dict[str, Any]: ...


def get_open_orders(
    portfolio_id: str,
    account_id: str,
    order_source: Literal["snapshot", "repository", "in_memory"] = "snapshot",
    as_of: Optional[str] = None,
    request_id: Optional[str] = None,
) -> dict[str, Any]: ...


def get_strategy_allocations(
    portfolio_id: str,
    include_inactive: bool = False,
    request_id: Optional[str] = None,
) -> dict[str, Any]: ...


def get_portfolio_equity_curve(
    portfolio_id: str,
    account_id: str,
    start: Optional[str] = None,
    end: Optional[str] = None,
    frequency: Literal["tick", "minute", "hourly", "daily"] = "daily",
    request_id: Optional[str] = None,
) -> dict[str, Any]: ...
```

### 19B.2 Portfolio Risk and Analytics Tools

```python
def calculate_portfolio_returns(
    equity_curve: list[float],
    method: Literal["simple", "log"] = "simple",
    request_id: Optional[str] = None,
) -> dict[str, Any]: ...


def calculate_portfolio_volatility(
    returns: list[float],
    annualization_factor: int = 252,
    ddof: int = 1,
    request_id: Optional[str] = None,
) -> dict[str, Any]: ...


def calculate_portfolio_correlation(
    strategy_returns: dict[str, list[float]],
    method: Literal["pearson", "spearman"] = "pearson",
    min_observations: int = 30,
    request_id: Optional[str] = None,
) -> dict[str, Any]: ...


def calculate_portfolio_var(
    returns: list[float],
    confidence_level: float = 0.95,
    method: Literal["historical", "parametric"] = "historical",
    request_id: Optional[str] = None,
) -> dict[str, Any]: ...


def calculate_portfolio_cvar(
    returns: list[float],
    confidence_level: float = 0.95,
    method: Literal["historical"] = "historical",
    request_id: Optional[str] = None,
) -> dict[str, Any]: ...


def calculate_risk_contribution(
    weights: dict[str, float],
    covariance_matrix: list[list[float]],
    strategy_order: list[str],
    request_id: Optional[str] = None,
) -> dict[str, Any]: ...


def calculate_margin_usage(
    equity: float,
    used_margin: float,
    free_margin: Optional[float] = None,
    request_id: Optional[str] = None,
) -> dict[str, Any]: ...


def calculate_currency_exposure(
    positions: list[dict[str, Any]],
    instrument_metadata: dict[str, dict[str, Any]],
    account_currency: str,
    fx_rates: dict[str, float],
    request_id: Optional[str] = None,
) -> dict[str, Any]: ...


def detect_strategy_overlap(
    strategy_positions: dict[str, list[dict[str, Any]]],
    overlap_threshold: float = 0.60,
    request_id: Optional[str] = None,
) -> dict[str, Any]: ...


def detect_symbol_cluster_risk(
    positions: list[dict[str, Any]],
    instrument_metadata: dict[str, dict[str, Any]],
    cluster_threshold: float = 0.50,
    request_id: Optional[str] = None,
) -> dict[str, Any]: ...


def build_portfolio_risk_snapshot(
    portfolio_id: str,
    account_id: str,
    positions: list[dict[str, Any]],
    orders: list[dict[str, Any]],
    equity_curve: list[float],
    strategy_returns: dict[str, list[float]],
    instrument_metadata: dict[str, dict[str, Any]],
    account_currency: str,
    fx_rates: dict[str, float],
    request_id: Optional[str] = None,
) -> dict[str, Any]: ...
```

### 19B.3 Position Sizing Tools

```python
def calculate_fixed_fractional_size(
    equity: float,
    risk_fraction: float,
    stop_distance_price: float,
    pip_value_per_lot: float,
    lot_step: float = 0.01,
    min_lot: float = 0.01,
    max_lot: Optional[float] = None,
    request_id: Optional[str] = None,
) -> dict[str, Any]: ...


def calculate_volatility_adjusted_size(
    equity: float,
    risk_fraction: float,
    volatility_price: float,
    volatility_multiplier: float,
    pip_value_per_lot: float,
    lot_step: float = 0.01,
    min_lot: float = 0.01,
    max_lot: Optional[float] = None,
    request_id: Optional[str] = None,
) -> dict[str, Any]: ...


def calculate_risk_parity_weights(
    strategy_volatility: dict[str, float],
    min_weight: float = 0.0,
    max_weight: float = 1.0,
    request_id: Optional[str] = None,
) -> dict[str, Any]: ...


def calculate_correlation_adjusted_size(
    base_size_lots: float,
    portfolio_correlation: float,
    penalty_strength: float = 1.0,
    min_multiplier: float = 0.0,
    request_id: Optional[str] = None,
) -> dict[str, Any]: ...


def calculate_margin_aware_size(
    requested_size_lots: float,
    required_margin_per_lot: float,
    free_margin: float,
    max_margin_usage_fraction: float,
    lot_step: float = 0.01,
    request_id: Optional[str] = None,
) -> dict[str, Any]: ...


def calculate_cost_adjusted_size(
    requested_size_lots: float,
    estimated_cost_per_lot: float,
    max_cost_fraction_of_risk: float,
    risk_amount: float,
    lot_step: float = 0.01,
    request_id: Optional[str] = None,
) -> dict[str, Any]: ...


def calculate_max_safe_position_size(
    equity: float,
    risk_fraction: float,
    stop_distance_price: float,
    pip_value_per_lot: float,
    required_margin_per_lot: float,
    free_margin: float,
    max_margin_usage_fraction: float,
    lot_step: float = 0.01,
    min_lot: float = 0.01,
    max_lot: Optional[float] = None,
    request_id: Optional[str] = None,
) -> dict[str, Any]: ...
```

### 19B.4 Allocation and Lifecycle Decision Tools

These tools are **high-risk advisory/state-proposal tools**. They must not place trades. They must require evidence, policy evaluation, idempotency keys, and approval where applicable.

```python
def propose_strategy_allocation(
    portfolio_id: str,
    strategy_id: str,
    requested_weight: float,
    risk_snapshot: dict[str, Any],
    validation_evidence: dict[str, Any],
    idempotency_key: str,
    approval_token: Optional[dict[str, Any]] = None,
    request_id: Optional[str] = None,
) -> dict[str, Any]: ...


def rebalance_strategy_allocations(
    portfolio_id: str,
    current_allocations: dict[str, float],
    target_allocations: dict[str, float],
    risk_snapshot: dict[str, Any],
    idempotency_key: str,
    approval_token: Optional[dict[str, Any]] = None,
    request_id: Optional[str] = None,
) -> dict[str, Any]: ...


def validate_allocation_proposal(
    portfolio_id: str,
    proposed_allocations: dict[str, float],
    risk_snapshot: dict[str, Any],
    allocation_policy: dict[str, Any],
    request_id: Optional[str] = None,
) -> dict[str, Any]: ...


def admit_strategy_to_portfolio(
    portfolio_id: str,
    strategy_id: str,
    strategy_evidence: dict[str, Any],
    idempotency_key: str,
    approval_token: Optional[dict[str, Any]] = None,
    request_id: Optional[str] = None,
) -> dict[str, Any]: ...


def promote_strategy_to_paper(
    portfolio_id: str,
    strategy_id: str,
    validation_evidence: dict[str, Any],
    idempotency_key: str,
    approval_token: Optional[dict[str, Any]] = None,
    request_id: Optional[str] = None,
) -> dict[str, Any]: ...


def promote_strategy_to_live_candidate(
    portfolio_id: str,
    strategy_id: str,
    paper_trading_evidence: dict[str, Any],
    risk_decision_package: dict[str, Any],
    idempotency_key: str,
    approval_token: dict[str, Any],
    request_id: Optional[str] = None,
) -> dict[str, Any]: ...


def suspend_strategy(
    portfolio_id: str,
    strategy_id: str,
    reason: str,
    idempotency_key: str,
    request_id: Optional[str] = None,
) -> dict[str, Any]: ...


def retire_strategy(
    portfolio_id: str,
    strategy_id: str,
    reason: str,
    idempotency_key: str,
    approval_token: Optional[dict[str, Any]] = None,
    request_id: Optional[str] = None,
) -> dict[str, Any]: ...


def demote_strategy_to_paper(
    portfolio_id: str,
    strategy_id: str,
    reason: str,
    idempotency_key: str,
    approval_token: Optional[dict[str, Any]] = None,
    request_id: Optional[str] = None,
) -> dict[str, Any]: ...


def update_strategy_status(
    portfolio_id: str,
    strategy_id: str,
    new_status: Literal[
        "research", "backtest", "validated", "paper", "live_candidate", "live", "suspended", "retired"
    ],
    reason: str,
    idempotency_key: str,
    approval_token: Optional[dict[str, Any]] = None,
    request_id: Optional[str] = None,
) -> dict[str, Any]: ...


def build_risk_decision_package(
    portfolio_id: str,
    strategy_id: str,
    risk_snapshot: dict[str, Any],
    validation_evidence: dict[str, Any],
    allocation_proposal: Optional[dict[str, Any]] = None,
    request_id: Optional[str] = None,
) -> dict[str, Any]: ...
```

---

## 19C. Official Portfolio Contracts

The implementation may use Pydantic models, dataclasses, or typed dictionaries during Phase 1. Pydantic is preferred once contracts become workflow-critical.

### 19C.1 `PositionSnapshot`

Required fields:

```text
position_id: str
account_id: str
strategy_id: str | None
symbol: str
normalized_symbol: str
side: "long" | "short"
volume_lots: float
entry_price: float
current_price: float
notional_account_currency: float
unrealized_pnl_account_currency: float
margin_used_account_currency: float
opened_at: str
source: "mt5_snapshot" | "simulation" | "manual_snapshot"
snapshot_at: str
```

### 19C.2 `OrderSnapshot`

Required fields:

```text
order_id: str
account_id: str
strategy_id: str | None
symbol: str
normalized_symbol: str
side: "buy" | "sell"
order_type: str
volume_lots: float
requested_price: float | None
stop_loss: float | None
take_profit: float | None
source: "mt5_snapshot" | "simulation" | "manual_snapshot"
snapshot_at: str
```

### 19C.3 `InstrumentMetadata`

Required fields:

```text
symbol: str
normalized_symbol: str
asset_class: "forex" | "metal" | "index" | "crypto" | "commodity" | "stock" | "unknown"
base_currency: str | None
quote_currency: str | None
profit_currency: str
margin_currency: str
contract_size: float
point_size: float
pip_size: float
min_lot: float
max_lot: float
lot_step: float
pip_value_per_lot_account_currency: float | None
requires_broker_metadata: bool
metadata_source: "mt5" | "static" | "manual" | "unknown"
as_of: str
```

If `InstrumentMetadata` is missing for a live-adjacent decision, the tool must return:

```text
status = "error"
error.code = "MISSING_INSTRUMENT_METADATA"
```

and fail closed.

### 19C.4 `PortfolioRiskSnapshot`

Required fields:

```text
portfolio_id: str
account_id: str
account_currency: str
equity: float
balance: float | None
used_margin: float
free_margin: float
margin_usage_fraction: float
returns: list[float]
volatility_annualized: float
var_95: float
cvar_95: float
strategy_correlations: dict[str, dict[str, float]]
currency_exposure: dict[str, float]
symbol_cluster_exposure: dict[str, float]
risk_contribution: dict[str, float]
open_positions_count: int
open_orders_count: int
snapshot_at: str
source_versions: dict[str, str]
missing_evidence: list[str]
warnings: list[str]
```

### 19C.5 `ApprovalToken`

Required fields:

```text
approval_id: str
approved_by: str
approved_at: str
expires_at: str
scope: "portfolio_allocation" | "strategy_lifecycle" | "live_candidate_promotion" | "kill_switch_resume"
allowed_action: str
portfolio_id: str
strategy_ids: list[str]
account_ids: list[str]
max_risk_change: float | None
revoked: bool
signature_hash: str
```

Approval rules:

- missing approval fails closed when approval is required
- expired approval fails closed
- revoked approval fails closed
- mismatched action, portfolio, account, or strategy fails closed
- approval must match requested action scope exactly
- approval must be logged and included in audit records
- approval does not authorize direct order placement by the portfolio module

### 19C.6 `LifecycleTransitionRequest`

Required fields:

```text
portfolio_id: str
strategy_id: str
from_status: str
to_status: str
reason: str
evidence: dict[str, Any]
approval_token: dict[str, Any] | None
idempotency_key: str
request_id: str
workflow_id: str | None
requested_at: str
```

### 19C.7 `LifecycleTransitionResult`

Required fields:

```text
status: "approved" | "rejected" | "blocked" | "needs_approval" | "error"
portfolio_id: str
strategy_id: str
from_status: str
to_status: str | None
reason: str
policy_checks: list[dict[str, Any]]
approval_status: str
audit_record_id: str | None
idempotency_key: str
error: dict[str, str] | None
```

---

## 19D. Data Source Ownership and Boundaries

The portfolio module must not become a duplicate broker bridge, execution engine, analytics engine, or risk governor. It consumes snapshots and evidence from authoritative sources.

| Data / Evidence | Source of Truth | Portfolio Usage | Failure Behavior |
|---|---|---|---|
| Open positions | Execution module / broker state snapshot | Exposure and risk calculation | Missing live-adjacent snapshot fails closed |
| Open orders | Execution module / broker state snapshot | Pending exposure calculation | Missing live-adjacent snapshot fails closed |
| MT5 account equity/margin | Execution module / MT5 bridge snapshot | Margin and risk snapshot | Stale snapshot returns `STALE_BROKER_SNAPSHOT` |
| Strategy allocations | Portfolio state store | Allocation validation | Missing allocation state returns `DATA_NOT_FOUND` |
| Strategy lifecycle status | Portfolio lifecycle registry | Promotion/demotion control | Missing state returns `LIFECYCLE_STATE_NOT_FOUND` |
| Equity curve | Analytics/accounting store | Returns, volatility, VaR/CVaR | Missing data returns `MISSING_EQUITY_CURVE` |
| Strategy validation evidence | Simulation/validation module | Lifecycle and allocation evidence | Missing evidence blocks promotion |
| Risk approval | Risk Governor | Risk decision validation | Missing risk approval blocks live-adjacent actions |
| Board/human approval | Governance approval service | Approval token validation | Missing/invalid approval blocks action |
| Kill-switch state | Portfolio kill-switch state store | Execution gating | Unknown state is treated as active/blocking |
| Instrument metadata | Data/execution metadata provider | Currency, margin, pip value | Missing live-adjacent metadata fails closed |

### 19D.1 MT5 Boundary Rule

The portfolio module may consume MT5-derived account, position, order, symbol, margin, pip-value, and equity snapshots, but it must **not** call MT5 directly for live broker actions.

Broker communication belongs to the execution module.

Portfolio outputs are advisory/gating inputs only:

```text
Portfolio -> produces risk snapshot / allocation decision / lifecycle status / kill-switch state
Risk Governor -> approves or rejects risk decision
Execution -> performs broker action only after all deterministic gates pass
MT5 Bridge -> talks to MetaTrader 5 terminal
```

### 19D.2 Execution Gate Inputs from Portfolio

Before any MT5 live order action, the execution module must verify:

```text
portfolio_allocation_allowed == True
portfolio_lifecycle_status in {"live", "live_candidate_approved"}
risk_governor_approved == True
kill_switch_state == "healthy"
margin_safe == True
broker_heartbeat_healthy == True
audit_writer_available == True
approval_token_valid == True, where required
```

If any input is missing, stale, or negative, execution must fail closed.

---

## 19E. Formula and Unit Conventions

Production risk bugs often come from inconsistent signs, units, and annualization assumptions. The portfolio module must use the following conventions.

### 19E.1 Numeric Unit Rules

- Percent-like values are decimals: `0.05` means `5%`, not `5.0`.
- Monetary values are in account currency unless the field name explicitly says otherwise.
- VaR and CVaR are returned as positive loss magnitudes.
- Drawdown is negative when below peak.
- Position volume is in lots unless the field name explicitly says units/contracts.
- Timestamps must be ISO-8601 strings with timezone where possible.

### 19E.2 Return Formula

Simple returns:

```text
returns[t] = equity[t] / equity[t-1] - 1
```

Log returns:

```text
returns[t] = ln(equity[t] / equity[t-1])
```

Invalid cases:

- less than two equity values returns `INVALID_INPUT`
- zero or negative equity values return `INVALID_INPUT` for return calculations

### 19E.3 Volatility Formula

```text
volatility = standard_deviation(returns, ddof=1) * sqrt(annualization_factor)
```

Default annualization factor:

```text
daily = 252
hourly = 252 * 24 unless a trading-session calendar overrides it
minute = strategy/calendar-specific and must be supplied explicitly
```

### 19E.4 Drawdown Formula

```text
rolling_peak[t] = max(equity[0:t])
drawdown[t] = equity[t] / rolling_peak[t] - 1
max_drawdown = min(drawdown)
```

### 19E.5 Historical VaR Formula

For confidence level `c`:

```text
losses = [-r for r in returns]
VaR(c) = quantile(losses, c)
```

VaR is reported as a positive loss magnitude.

### 19E.6 Historical CVaR Formula

```text
CVaR(c) = mean(losses where losses >= VaR(c))
```

CVaR is reported as a positive loss magnitude.

### 19E.7 Margin Usage Formula

```text
margin_usage_fraction = used_margin / equity
```

Invalid cases:

- `equity <= 0` returns `INVALID_INPUT`
- `used_margin < 0` returns `INVALID_INPUT`

### 19E.8 Risk Contribution Formula

For weights `w` and covariance matrix `Σ`:

```text
portfolio_variance = w.T @ Σ @ w
marginal_contribution = Σ @ w
component_contribution = w * marginal_contribution / portfolio_variance
```

Invalid cases:

- mismatched dimensions return `INVALID_INPUT`
- non-square covariance matrix returns `INVALID_INPUT`
- non-positive portfolio variance returns `VALIDATION_FAILED`

---

## 19F. Multi-Currency and Instrument Metadata Rules

This module must be safe for MT5 Forex, metals, indices, commodities, and broker-specific symbols.

### 19F.1 Symbol Normalization

The module must not assume symbols are exactly six-character Forex pairs.

Examples that must be handled:

```text
EURUSD
EURUSD.r
EURUSDm
XAUUSD
US30
NAS100
BTCUSD
GER40.cash
```

Symbol normalization must preserve both:

```text
raw broker symbol
normalized symbol
```

If normalization is uncertain, return a warning for read-only tools and fail closed for live-adjacent decisions.

### 19F.2 Currency Exposure Rules

Currency exposure must use instrument metadata, not naive string slicing.

For Forex:

```text
long EURUSD -> +EUR exposure, -USD exposure
short EURUSD -> -EUR exposure, +USD exposure
```

For metals, indices, crypto, and CFDs:

- use `profit_currency`, `margin_currency`, and contract metadata
- if base/quote semantics are unavailable, mark exposure as synthetic
- if exposure cannot be computed safely, return `MISSING_INSTRUMENT_METADATA`

### 19F.3 FX Conversion Rule

All portfolio-level monetary metrics must be converted to account currency using deterministic FX conversion rules.

Required behavior:

- direct rate available: use it
- inverse rate available: use reciprocal
- cross conversion available: use configured conversion path
- required rate missing: return `MISSING_FX_RATE`
- stale FX rate: return `STALE_FX_RATE` for live-adjacent decisions

### 19F.4 Pip Value Rule

For live-adjacent position sizing, pip value must come from broker/instrument metadata or an explicitly approved deterministic calculation.

If pip value is missing:

```text
error.code = "MISSING_PIP_VALUE"
```

and the sizing tool must fail closed.

---

## 19G. Approval, Policy, and Live-Adjacent Safety Rules

### 19G.1 Approval-Required Actions

Approval is required for:

- promoting a strategy to `live_candidate`
- changing a live strategy allocation materially
- rebalancing live allocations
- retiring or demoting a live strategy where execution implications exist
- resuming after a kill switch
- any action that increases portfolio risk beyond configured thresholds

### 19G.2 Deterministic Approval Validation

Approval validation must be deterministic code, not LLM interpretation.

Validation must check:

```text
approval_id exists
approved_by exists
approved_at <= now
expires_at > now
revoked == False
scope matches requested action
allowed_action matches requested action
portfolio_id matches
strategy_ids include requested strategy where relevant
account_ids include requested account where relevant
max_risk_change is not exceeded
signature_hash validates, if signature validation is enabled
```

Failure returns:

```text
PERMISSION_DENIED
APPROVAL_REQUIRED
APPROVAL_EXPIRED
APPROVAL_REVOKED
APPROVAL_SCOPE_MISMATCH
```

### 19G.3 Portfolio Module Live-Trading Prohibition

The portfolio module must never expose tools that:

- place orders
- close positions
- modify broker orders
- activate live trading
- override execution risk controls
- override kill switch by LLM instruction

Those actions belong to the execution module and must remain separately approval-gated.

---

## 19H. Kill-Switch Persistence and Cold-Start Behavior

The kill switch is a safety-critical component.

### 19H.1 Required States

```text
healthy
triggered
resume_requested
resumed
unknown
```

### 19H.2 Trigger Rules

Kill switch must trigger on configured hard-stop conditions, including:

- daily loss breach
- total loss breach
- margin danger
- broker heartbeat failure
- audit writer failure for live-adjacent action
- stale broker snapshot during live-adjacent action
- policy engine unavailable during live-adjacent action
- manual emergency stop

### 19H.3 Persistence Backend

Phase 1 acceptable backend:

```text
SQLite or atomic JSONL state file
```

Phase 2 preferred backend:

```text
database-backed state store with append-only event log
```

### 19H.4 Atomic Write Rule

Kill-switch trigger writes must be atomic.

If kill-switch persistence fails during trigger:

```text
execution must treat kill_switch_state as "triggered"
```

If kill-switch state cannot be read on startup:

```text
state = "unknown"
execution gate treats unknown as blocking
log KILL_SWITCH_STATE_UNKNOWN
emit audit record if audit writer is available
```

### 19H.5 Cold-Start Restore Rule

On startup:

1. Read latest persisted kill-switch state.
2. Validate record hash if hash-chain is enabled.
3. If latest state is `triggered`, keep trading blocked.
4. If latest state is `resumed`, verify resume approval is still valid or no longer required by policy.
5. If state cannot be validated, set state to `unknown` and block live execution.

### 19H.6 Resume Rule

Resume requires:

- valid approval token scoped to `kill_switch_resume`
- reason for resume
- evidence that trigger condition is cleared
- audit write success
- deterministic policy pass

No LLM may override kill-switch state.

---

## 19I. Idempotency and Concurrency Rules

### 19I.1 Idempotency Rule

Every allocation and lifecycle mutation/proposal must include:

```text
idempotency_key: str
```

Required behavior:

- duplicate `idempotency_key` with identical payload returns original decision
- duplicate `idempotency_key` with different payload returns `IDEMPOTENCY_CONFLICT`
- missing idempotency key for lifecycle/allocation decisions returns `INVALID_INPUT`

### 19I.2 Concurrency Rule

The module must prevent conflicting concurrent state changes.

Required locks:

```text
portfolio_id lock for allocation changes
strategy_id lock for lifecycle transitions
kill_switch lock for trigger/resume transitions
```

Allowed behavior for lock contention:

```text
return status="error", error.code="CONCURRENT_UPDATE"
```

or retry only if the retry is bounded, logged, and idempotent.

### 19I.3 Ordering Rule

For live-adjacent decisions, state transition order must be:

```text
validate input
load current state
check idempotency
acquire lock
reload current state
run policy checks
validate evidence
validate approval if required
write audit pre-record
write state/proposal
write audit post-record
release lock
return standard response
```

If audit pre-record cannot be written, the action must not proceed.

---

## 19J. Audit Hash-Chain and Evidence Rules

### 19J.1 Audit Hash-Chain Formula

```text
record_hash = sha256(previous_hash + canonical_json(current_payload))
```

### 19J.2 Genesis Rule

For the first audit record of a run/session:

```text
previous_hash = "0000000000000000000000000000000000000000000000000000000000000000"
```

If a prior persisted chain exists, continue from the latest valid record hash.

If the previous record hash cannot be verified for a high-risk/live-adjacent action:

```text
error.code = "AUDIT_CHAIN_INVALID"
```

and the action must fail closed.

### 19J.3 Required Audit Fields

Every high-risk portfolio decision must audit:

```text
timestamp
request_id
workflow_id
portfolio_id
account_id, where applicable
strategy_id, where applicable
action
risk_level
input_summary
evidence_references
policy_result
approval_result
idempotency_key
previous_hash
record_hash
result_status
error_code, where applicable
```

### 19J.4 Evidence Discipline

The module must clearly separate:

- user-provided inputs
- broker/MT5 snapshots
- analytics outputs
- simulation/validation evidence
- risk governor decisions
- governance approvals
- portfolio-generated calculations
- assumptions
- warnings

Missing evidence must be explicit. Live-adjacent decisions with missing required evidence must fail closed.

---

## 19K. Expanded Error Code Standard

In addition to common HaruQuant tool error codes, the portfolio module must support these deterministic portfolio-specific error codes:

```text
MISSING_PORTFOLIO_ID
MISSING_ACCOUNT_ID
MISSING_STRATEGY_ID
MISSING_EQUITY_CURVE
MISSING_POSITION_SNAPSHOT
MISSING_ORDER_SNAPSHOT
MISSING_INSTRUMENT_METADATA
MISSING_FX_RATE
STALE_FX_RATE
MISSING_PIP_VALUE
MISSING_SNAPSHOT_TIMESTAMP
MISSING_ACCOUNT_MODE
MISSING_BROKER_MARGIN_FIELDS
STALE_BROKER_SNAPSHOT
STALE_POSITION_SNAPSHOT
STALE_ORDER_SNAPSHOT
STALE_INSTRUMENT_METADATA
STALE_EQUITY_CURVE
STALE_PORTFOLIO_STATE
STALE_RISK_DECISION
BROKER_HEARTBEAT_STALE
INVALID_ALLOCATION_SUM
ALLOCATION_LIMIT_EXCEEDED
CORRELATION_LIMIT_EXCEEDED
MARGIN_LIMIT_EXCEEDED
LIFECYCLE_STATE_NOT_FOUND
INVALID_LIFECYCLE_TRANSITION
MISSING_VALIDATION_EVIDENCE
MISSING_RISK_DECISION
APPROVAL_REQUIRED
APPROVAL_EXPIRED
APPROVAL_REVOKED
APPROVAL_SCOPE_MISMATCH
IDEMPOTENCY_CONFLICT
IDEMPOTENCY_KEY_EXPIRED
CONCURRENT_UPDATE
ORDER_STATE_CONFLICT
KILL_SWITCH_ACTIVE
KILL_SWITCH_STATE_UNKNOWN
PORTFOLIO_STATE_RECOVERY_FAILED
PORTFOLIO_RECONCILIATION_REQUIRED
PORTFOLIO_RECONCILIATION_FAILED
PORTFOLIO_CALCULATION_TIMEOUT
AUDIT_WRITE_FAILED
AUDIT_CHAIN_INVALID
POLICY_ENGINE_UNAVAILABLE
```

---

## 19L. Implementation-Readiness Gates

Implementation may begin only when the following gates are accepted:

- [x] Official tool list identified from the uploaded folder.
- [x] Exact public tool signatures defined.
- [x] Data source ownership defined.
- [x] Portfolio/Risk/Execution/MT5 boundary defined.
- [x] Formula and unit conventions defined.
- [x] Multi-currency and instrument metadata rules defined.
- [x] Approval token schema and validation rules defined.
- [x] Kill-switch persistence and cold-start rules defined.
- [x] Idempotency and concurrency behavior defined.
- [x] Audit hash-chain genesis rule defined.
- [ ] Final rewrite implementation created.
- [ ] Unit tests created for every official tool.
- [ ] Usage examples created for every official tool.
- [ ] Integration tests created against Risk and Execution boundaries.
- [ ] Coverage above 80%.

---

## 19M. v2 Implementation Impact Summary

Compared with v1, the rewrite must now add or enforce:

1. `contracts.py` with portfolio snapshots, metadata, approval, lifecycle, and risk snapshot contracts.
2. Explicit public signatures instead of `**kwargs`.
3. Deterministic source-of-truth boundaries for MT5-derived data.
4. Formula conventions for returns, volatility, drawdown, VaR, CVaR, margin, and risk contribution.
5. Robust symbol/instrument metadata handling for Forex, metals, indices, crypto, CFDs, and broker suffixes.
6. Approval token scope validation.
7. Persistent kill-switch state with fail-closed cold start.
8. Idempotency keys and concurrency locks for lifecycle/allocation decisions.
9. Audit hash-chain genesis and validation rules.
10. Expanded error-code tests.


---

## 19N. v3 Final Production Refinement Addendum

This section records the final production-readiness refinements identified after reviewing v2. These rules close remaining ambiguity around durable portfolio state, data freshness, partial fills, performance targets, idempotency-key generation, approval-token signatures, and post-manual-intervention reconciliation.

### 19N.1 v3 Specification Verdict

**Specification verdict after v4:** Production-ready technical specification with no known implementation-blocking gaps.

**Implementation verdict remains:** Not production-ready until rebuilt, tested, and integrated against this v3 specification.

The v4 specification supersedes v3 as the implementation baseline. v2 remains a valid historical baseline, but all new code, tests, examples, and integration gates must target v3.

---

## 19O. Durable Portfolio State Persistence

The portfolio module must not rely on in-memory state for core portfolio decisions. Core portfolio state must be durable, append-first, recoverable, and auditable.

### 19O.1 State That Must Be Persisted

The following state must survive process restarts, crashes, deployments, and machine reboots:

| State | Persistence Requirement | Reason |
|---|---|---|
| Strategy allocation weights | Durable | Prevent accidental allocation reset after restart. |
| Strategy lifecycle status | Durable | Prevent inactive/quarantined strategies from becoming active after restart. |
| Pending lifecycle transitions | Durable | Prevent duplicate approval or lost transition requests. |
| Pending allocation proposals | Durable | Preserve decision trace and idempotency. |
| Portfolio-level risk budget assignments | Durable | Preserve portfolio risk intent across restarts. |
| Idempotency records | Durable | Prevent duplicate transitions/rebalances after retry. |
| Manual intervention/reconciliation flags | Durable | Prevent unsafe resume after operator intervention. |
| Kill-switch state | Durable | Already required in Section 19H and must remain fail-closed. |

### 19O.2 Storage Backend Rule

Phase 1 may use a simple local backend, but the backend must be explicit and injected. Acceptable Phase 1 backends:

```text
SQLite repository
append-only JSONL event log plus checkpoint file
project-approved repository interface backed by the same storage as kill-switch state
```

In-memory storage may only be used in tests, examples, or explicitly marked simulation/demo workflows. It must not be the default for production or live-adjacent workflows.

### 19O.3 Append-First Event Model

Portfolio state changes must be recorded as append-first events before or at the same time as any derived state checkpoint is updated.

Required event fields:

```text
event_id
request_id
workflow_id
portfolio_id
account_id, where applicable
strategy_id, where applicable
event_type
previous_state
new_state
reason
evidence_refs
approval_id, where applicable
idempotency_key, where applicable
created_at
created_by
previous_hash
record_hash
```

Derived current state may be maintained as a checkpoint for fast reads, but checkpoints must be reconstructable from the append-first event log.

### 19O.4 Startup Recovery Rule

On startup, the portfolio module must recover durable state before serving live-adjacent decisions.

Startup behavior:

1. Load the latest valid portfolio state checkpoint, if available.
2. Replay append-first events after the checkpoint, if any.
3. Validate audit/event hash continuity.
4. Validate kill-switch state.
5. Validate unresolved manual intervention or reconciliation flags.
6. If recovery fails or state is ambiguous, return `PORTFOLIO_STATE_RECOVERY_FAILED` and block live-adjacent decisions.

### 19O.5 Repository Boundary

The portfolio module should define or consume a repository interface rather than binding business logic directly to a specific storage technology.

Required repository capabilities:

```python
class PortfolioStateRepositoryProtocol:
    def append_event(self, event: dict[str, Any]) -> dict[str, Any]: ...
    def get_current_state(self, portfolio_id: str) -> dict[str, Any]: ...
    def save_checkpoint(self, portfolio_id: str, state: dict[str, Any]) -> dict[str, Any]: ...
    def get_idempotency_record(self, idempotency_key: str) -> dict[str, Any] | None: ...
    def save_idempotency_record(self, record: dict[str, Any]) -> dict[str, Any]: ...
```

---

## 19P. Performance and Scalability Targets

The portfolio module is not expected to be ultra-low-latency like execution order routing, but it must still have measurable performance targets so slow portfolio tools do not block live-adjacent decisions.

### 19P.1 Phase 1 Baseline Targets

The following are baseline targets for local computation on typical development hardware. They are directional Phase 1 baselines, not hard blockers during the first implementation pass. They may be recalibrated after real benchmark evidence is collected, especially for large Python workloads with hundreds of positions and orders. Tests or benchmarks should be added by Phase 5 to catch obvious regressions.

| Operation | Dataset Size | Target |
|---|---:|---:|
| Calculate portfolio risk snapshot | 100 strategies / 500 positions+orders | `< 200ms` |
| Calculate historical VaR | 1,000 returns | `< 50ms` |
| Calculate historical VaR | 10,000 returns | `< 250ms` |
| Calculate CVaR | 10,000 returns | `< 300ms` |
| Calculate exposure by symbol/currency | 1,000 positions/orders | `< 100ms` |
| Validate allocation proposal | 100 strategies | `< 100ms` |
| Validate lifecycle transition | 1 strategy with evidence pack | `< 50ms` |
| Load current portfolio state from SQLite/local repository | 100 strategies | `< 150ms` |
| Append portfolio state event | 1 event | `< 25ms` |

### 19P.2 Performance Test Requirement

By Phase 5, add benchmark-style tests under:

```text
tests/performance/tools/portfolio/
```

The tests should avoid brittle micro-benchmarking but should detect obvious regressions. Performance tests may run in a separate CI profile if they are too noisy for normal unit tests.

### 19P.3 Performance Failure Behavior

If a portfolio tool exceeds configured timeout limits in a live-adjacent workflow, it must return `PORTFOLIO_CALCULATION_TIMEOUT` or `SERVICE_UNAVAILABLE` and fail closed. It must not return stale or partial results as valid decisions unless explicitly marked incomplete and non-actionable.

---

## 19Q. Data Freshness and Staleness Matrix

Portfolio decisions depend on external snapshots. Every snapshot-like contract must include an `as_of` timestamp when the source can provide one. Portfolio tools must validate timestamp freshness against configured thresholds before producing live-adjacent decisions.

### 19Q.1 Timestamp Rule

All snapshot inputs should include:

```text
as_of: ISO-8601 timestamp
source: snapshot | repository | broker_bridge | analytics_store | risk_governor | governance
source_latency_ms, optional
```

If `as_of` is not provided, the tool may proceed only for non-live, exploratory, or reporting use. For live-adjacent decisions, missing freshness evidence must return `MISSING_SNAPSHOT_TIMESTAMP` or `STALE_BROKER_SNAPSHOT` depending on the source context.

### 19Q.2 Default Staleness Thresholds

These thresholds are defaults and should be configurable.

| Data Type | Default Max Age | Live-Adjacent Failure Code |
|---|---:|---|
| Broker account snapshot: equity, balance, margin | 5 seconds | `STALE_BROKER_SNAPSHOT` |
| Open positions snapshot | 5 seconds | `STALE_POSITION_SNAPSHOT` |
| Open orders snapshot | 5 seconds | `STALE_ORDER_SNAPSHOT` |
| Execution heartbeat / broker bridge health | 3 seconds | `BROKER_HEARTBEAT_STALE` |
| FX conversion rate for major FX pairs | 60 seconds | `STALE_FX_RATE` |
| FX conversion rate for non-major/CFD conversions | 300 seconds | `STALE_FX_RATE` |
| Instrument metadata | 24 hours, unless broker session changed | `STALE_INSTRUMENT_METADATA` |
| Equity curve for risk snapshot | 1 trading day for reporting, 60 seconds for live-adjacent decisions | `STALE_EQUITY_CURVE` |
| Strategy lifecycle state | current repository state at decision time | `STALE_PORTFOLIO_STATE` |
| Allocation state | current repository state at decision time | `STALE_PORTFOLIO_STATE` |
| Risk Governor decision | expiry defined by risk token; default 5 minutes | `STALE_RISK_DECISION` |
| Approval token | `expires_at` field | `APPROVAL_EXPIRED` |

### 19Q.3 Freshness Validation Behavior

For every live-adjacent tool:

1. Validate `as_of` exists for required snapshots.
2. Compare `now_utc - as_of` against the configured max age.
3. If stale, return a structured error and block the decision.
4. Include `snapshot_age_ms`, `max_age_ms`, and `source` in metadata or error details.
5. Never silently downgrade stale data into a warning for live-adjacent decisions.

### 19Q.4 Reporting Exception

Reporting tools may produce reports with stale data only if the report clearly marks:

```text
data_status = stale
as_of timestamp
max_age threshold
not_actionable = true
```

---

## 19R. Partial Fill and Pending Exposure Handling

Portfolio exposure must account for both existing positions and active order exposure. Partial fills are common in live trading and must not be ignored.

### 19R.1 OrderSnapshot Status Requirement

`OrderSnapshot` must include at least:

```text
order_id
symbol
side
requested_volume
filled_volume
remaining_volume
status
order_type
price, optional
stop_loss, optional
take_profit, optional
created_at
updated_at
as_of
```

Valid order statuses should include:

```text
pending
partially_filled
filled
cancelled
rejected
expired
closed
unknown
```

### 19R.2 Partial Fill Exposure Rule

For exposure calculations:

```text
position_exposure = current filled/open position volume
pending_order_exposure = active remaining order volume
potential_total_exposure = position_exposure + pending_order_exposure
```

An order with `status = partially_filled` and `remaining_volume > 0` must be treated as active potential future exposure unless explicitly cancelled, expired, rejected, or closed.

An order with `remaining_volume = 0` must not contribute pending exposure, even if status is delayed or inconsistent. If status and remaining volume conflict, return `ORDER_STATE_CONFLICT` for live-adjacent decisions.

### 19R.3 Active Order Status Rule

The following statuses count as active pending exposure:

```text
pending
partially_filled
unknown, only if the order is recent and not confirmed terminal
```

The following statuses do not count as active pending exposure:

```text
filled
cancelled
rejected
expired
closed
```

Unknown order status in live-adjacent workflows should fail closed unless execution provides a reconciliation report that classifies the order as terminal or active.

### 19R.4 Netting vs Hedging Account Rule

For MT5, portfolio exposure tools must distinguish between:

```text
netting account behavior
hedging account behavior
```

In netting accounts, new orders may modify an existing position. In hedging accounts, new orders may create separate positions. The exposure tool must consume account mode from broker/account metadata or return `MISSING_ACCOUNT_MODE` for live-adjacent decisions.

---

## 19S. Idempotency Key Generation Recommendation

The portfolio module must require idempotency keys for allocation and lifecycle mutations. The caller may provide the key, but the implementation should also provide a deterministic helper for generating recommended keys.

### 19S.1 Recommended Format

Recommended format:

```text
portfolio:{portfolio_id}:{action_type}:{sha256(canonical_json(payload))[:16]}
```

Examples:

```text
portfolio:main:rebalance:8b7a2e41a6d09f31
portfolio:main:lifecycle_transition:71dfbb4f80fe3810
```

### 19S.2 UUID Option

A UUIDv4 idempotency key is acceptable for externally initiated user actions if it is stored with a canonical payload hash. The system must still detect payload mismatch on retry.

### 19S.3 Canonical Payload Hash Rule

Idempotency records must store:

```text
idempotency_key
payload_hash
request_id
workflow_id
created_at
status
result_reference
```

Retry behavior:

| Retry Case | Required Result |
|---|---|
| Same key + same payload hash | Return original stored result or current terminal result. |
| Same key + different payload hash | Return `IDEMPOTENCY_CONFLICT`. |
| Expired key | Return `IDEMPOTENCY_KEY_EXPIRED` or require a new key. |

---

## 19T. Approval Token Signature Validation Phase Rule

Approval token signature validation is desirable, but Phase 1 may defer cryptographic verification if the approval system is not yet finalized. All other approval checks remain mandatory.

### 19T.1 Mandatory Phase 1 Approval Checks

Even if signature verification is disabled, Phase 1 must validate:

```text
approval_id exists
approval status is approved
approval is not expired
approval is not revoked
approved action matches requested action
portfolio_id matches
account_id matches, where applicable
strategy_ids match, where applicable
max_risk_change is not exceeded
approved_by exists
approved_at exists
approval source is trusted/configured
```

### 19T.2 Signature Disabled Audit Rule

If cryptographic signature validation is disabled, every approval validation result must include:

```text
signature_validation_enabled = false
signature_validation_status = skipped
signature_validation_reason
```

This must be logged and included in the audit record. The tool must not pretend signature validation passed when it was skipped.

### 19T.3 Phase 2+ Requirement

Before production live trading, cryptographic or tamper-evident approval validation should be implemented unless a formal architecture decision record explicitly accepts the risk and documents compensating controls.

---

## 19U. Manual Intervention and Broker Reconciliation Rule

After manual intervention, portfolio state must be reconciled with broker truth before normal portfolio proposals can resume.

### 19U.1 Manual Intervention Trigger

Manual intervention includes:

```text
manual broker order placed outside HaruQuant
manual broker order cancelled outside HaruQuant
manual position closed or modified outside HaruQuant
kill switch manually resolved
portfolio state manually edited
execution module reports reconciliation mismatch
operator sets incident status to MANUAL_INTERVENTION
```

### 19U.2 Resume Rule

After `MANUAL_INTERVENTION`, the portfolio module must not produce actionable allocation, lifecycle, sizing, or live-adjacent exposure approvals until one of the following is true:

1. The portfolio module runs a full reconciliation against current execution/broker snapshots.
2. The portfolio module consumes a valid execution reconciliation report.

The reconciliation must verify:

```text
open positions
open orders
partial fills
account equity
used margin
free margin
strategy allocation mapping
strategy lifecycle state
pending approvals
kill-switch state
manual intervention flag cleared by authorized actor
```

If reconciliation fails, return `PORTFOLIO_RECONCILIATION_REQUIRED` or `PORTFOLIO_RECONCILIATION_FAILED` and block live-adjacent decisions.

### 19U.3 Reconciliation Report Contract

A valid reconciliation report should include:

```text
reconciliation_id
portfolio_id
account_id
as_of
source
positions_checked
orders_checked
partial_fills_checked
state_mismatches
broker_mismatches
resolved_mismatches
unresolved_mismatches
final_status: passed | failed | needs_manual_review
created_at
created_by
request_id
workflow_id
```

Only `final_status = passed` may clear the manual-intervention block.

---

## 19V. Broker-Derived Margin Field Clarification

`PortfolioRiskSnapshot.used_margin` and `PortfolioRiskSnapshot.free_margin` must be sourced from the broker/account snapshot when available, especially for MT5 live-adjacent workflows.

Calculated margin estimates may be included as separate fields:

```text
estimated_used_margin
estimated_free_margin
estimated_margin_method
```

The implementation must not silently substitute calculated margin for broker-reported margin in live-adjacent decisions. If broker margin fields are missing, return `MISSING_BROKER_MARGIN_FIELDS` unless the workflow is explicitly simulation/reporting-only.

---

## 19W. v3/v4 Implementation Impact Summary

Compared with v2, the rewrite must additionally enforce:

1. Durable, append-first portfolio state persistence for allocations, lifecycle status, pending proposals, idempotency records, and manual-intervention flags.
2. Startup recovery before live-adjacent decisions are served.
3. Performance targets and benchmark tests by Phase 5.
4. `as_of` timestamp and freshness validation for broker, execution, analytics, FX, metadata, risk, and approval inputs.
5. Partial-fill and remaining-order exposure accounting.
6. Explicit MT5 netting vs hedging account handling.
7. Recommended idempotency key generation and canonical payload-hash storage.
8. Phase 1 approval validation rules when signature checks are disabled.
9. Mandatory reconciliation after manual intervention before resuming actionable portfolio decisions.
10. Broker-derived margin fields clearly separated from calculated estimates.
11. Canonical error-code list alignment for all v3/v4 fail-closed conditions.
12. Optional-by-default strategy correlation matrices to avoid heavy default responses.
13. Performance targets treated as measurable baselines, not Phase 1 hard blockers.


---

## 19X. v4 Final Cleanup Notes

This v4 cleanup keeps v3 as the functional baseline and clarifies final implementation details.

### 19X.1 Section Numbering Rule

The 19-series addenda are intentionally append-only to preserve document history. Future versions may consolidate numbering during a documentation cleanup pass, but implementation should treat sections 19A through 19X as active requirements regardless of addendum lettering.

### 19X.2 Error Code Alignment

The portfolio-specific deterministic error-code list in Section 19K now includes the recovery, reconciliation, freshness, partial-fill, account-mode, margin-field, timeout, and idempotency codes introduced by the v3 addendum. Implementation must keep the canonical error-code list synchronized whenever new fail-closed conditions are added.

### 19X.3 Correlation Matrix Payload Rule

`PortfolioRiskSnapshot.strategy_correlations` may be large for portfolios with many strategies. It should not be included by default in lightweight responses. Tools should expose either:

```text
include_correlation_matrix: bool = False
```

or return a compact correlation summary by default, such as max correlation, average correlation, and top correlated strategy pairs. Full matrices should be returned only when explicitly requested, stored as an artifact, or required by a downstream risk workflow.

### 19X.4 Performance Target Interpretation

The Phase 1 performance targets in Section 19P are engineering baselines, not production blockers. They should guide profiling and regression detection. If benchmarks show that Python implementation cannot reliably meet a target for large portfolios, the implementation should document the measured baseline, optimize obvious bottlenecks, and defer heavier optimization to Phase 5 unless the delay blocks live-adjacent safety checks.



## 19Y. v5 Institutional Portfolio Optimization and Rebalancing Addendum

### 19Y.1 v5 Specification Verdict

The v5 document remains production-ready as the Portfolio Module technical specification baseline and adds institutional allocation requirements that were not fully covered in v4.

The v5 additions are active production requirements unless explicitly marked as Phase 2+ or future extension.

The Portfolio Module must support not only static allocation and risk-parity-style allocation, but also optimizer-driven target portfolios, cost-aware rebalancing, capacity enforcement, benchmark-relative allocation, cash policy handling, and portfolio-driven suspension requests.

### 19Y.2 Target Folder Structure Additions

The target portfolio package should add the following files when implementation reaches the allocation and rebalancing phases:

```text
portfolio/
    optimizer.py          # portfolio optimization algorithms and objective functions
    rebalancer.py         # current-vs-target diffing, tolerance bands, turnover/cost checks
    suspension.py         # portfolio suspension request generation, not hard execution kill switch
```

The `kill_switch.py` concept from the legacy module must not become an independent hard execution-control module inside Portfolio. Portfolio may evaluate portfolio-level suspension conditions and emit suspension requests, but Risk and Execution remain responsible for validation and enforcement.

### 19Y.3 Portfolio Optimization Algorithms

#### 19Y.3.1 Allocation Method Enum

The allocation engine must support an explicit allocation method enum.

```python
class AllocationMethod(str, Enum):
    EQUAL_WEIGHT = "equal_weight"
    RISK_PARITY = "risk_parity"
    HIERARCHICAL_RISK_PARITY = "hierarchical_risk_parity"
    MINIMUM_VARIANCE = "minimum_variance"
    MAXIMIZE_SHARPE = "maximize_sharpe"
    BLACK_LITTERMAN = "black_litterman"
    TARGET_RISK = "target_risk"
```

Phase 1 required methods:

```text
EQUAL_WEIGHT
RISK_PARITY
MINIMUM_VARIANCE
TARGET_RISK
```

Phase 2+ methods:

```text
HIERARCHICAL_RISK_PARITY
MAXIMIZE_SHARPE
BLACK_LITTERMAN
```

If a Phase 2+ method is requested before implementation, the tool must return `UNSUPPORTED_OPTIMIZATION_METHOD` and fail clearly.

#### 19Y.3.2 `OptimizationConfig`

The Portfolio Module must define an `OptimizationConfig` contract.

Required fields:

```text
method: AllocationMethod
lookback_bars: int
risk_free_rate: Decimal
max_weight_per_strategy: Decimal
min_weight_per_strategy: Decimal
allow_short_weights: bool
target_volatility: Decimal | None
benchmark_id: str | None
covariance_method: str
expected_return_method: str
constraints: AllocationConstraints
request_id: str | None
```

All optimizer inputs must be deterministic and validated before optimization starts.

#### 19Y.3.3 Optimizer Output Rule

Every optimizer run must return both proposed weights and predicted portfolio metrics.

Required output fields:

```text
target_weights: dict[str, Decimal]
expected_return: Decimal | None
expected_volatility: Decimal | None
expected_sharpe: Decimal | None
expected_var: Decimal | None
expected_cvar: Decimal | None
tracking_error: Decimal | None
information_ratio: Decimal | None
optimization_method: AllocationMethod
constraints_applied: list[str]
rejected_constraints: list[str]
metadata: standard tool metadata
```

If predicted metrics cannot be calculated because evidence is missing, the optimizer must either return `MISSING_OPTIMIZATION_EVIDENCE` or return success with the missing metrics explicitly set to `None` only when the requested method does not require them.

### 19Y.4 Transaction Costs and Turnover Constraints

#### 19Y.4.1 `RebalancingConstraints`

The rebalancer must support cost and turnover constraints.

```python
@dataclass(frozen=True)
class RebalancingConstraints:
    max_turnover_pct: Decimal = Decimal("0.20")
    max_transaction_cost_bps: Decimal = Decimal("50.0")
    min_trade_size_usd: Decimal = Decimal("1000.0")
    tolerance_band_pct: Decimal = Decimal("0.05")
```

All values must be configurable and validated. Percent-like values must use decimal form where appropriate unless the field name explicitly uses basis points.

#### 19Y.4.2 Turnover Formula

Portfolio turnover for a proposed rebalance shall be calculated as:

```text
turnover_pct = sum(abs(target_weight[strategy] - current_weight[strategy])) / 2
```

The value must be reported as a decimal, where `0.20` means 20% of portfolio NAV.

#### 19Y.4.3 Transaction Cost Rule

The rebalancer must estimate expected transaction costs before proposing execution-ready changes.

At minimum, estimated cost must include:

```text
spread cost
commission cost, where available
slippage estimate, where available
currency conversion cost, where applicable
```

If cost evidence is unavailable for a live-adjacent proposal, the tool must return `MISSING_TRANSACTION_COST_EVIDENCE` and fail closed unless the caller explicitly requests a research-only estimate.

#### 19Y.4.4 Rebalance Rejection and Partial Rebalance Rule

If the proposed rebalance violates turnover or cost limits, the module must not silently return the full rebalance.

It must return one of:

```text
REBALANCE_REJECTED
PARTIAL_REBALANCE_PROPOSED
NEEDS_MORE_EVIDENCE
```

A partial rebalance must include which changes were accepted, which were deferred, why they were deferred, and the remaining drift after the partial rebalance.

### 19Y.5 Strategy Capacity Enforcement

#### 19Y.5.1 Capacity Input Requirement

Each strategy eligible for allocation should provide capacity metadata.

Required fields:

```text
strategy_id
capacity_usd
current_allocated_usd
capacity_source
capacity_as_of
capacity_confidence
```

If capacity is unknown, production allocation must either apply a conservative default cap or return `MISSING_STRATEGY_CAPACITY` depending on configuration.

#### 19Y.5.2 Capacity Clamp Rule

Allocation weights must be clamped by:

```text
max_strategy_weight_by_capacity = strategy.capacity_usd / total_portfolio_nav
```

If requested weight exceeds the capacity-derived cap, the strategy must be marked:

```text
CAP_FULL
```

Excess capital must be redistributed to eligible strategies that still have remaining capacity or held as cash according to the configured `CashPolicy`.

#### 19Y.5.3 Capacity Report

Every allocation proposal must include a `CapacityReport` when capacity enforcement is enabled.

Required fields:

```text
strategy_id
requested_weight
capacity_limited_weight
excess_weight
capacity_status
redistribution_target
reason
```

### 19Y.6 Benchmark-Relative Allocation

#### 19Y.6.1 `BenchmarkConfig`

The allocation engine must support benchmark-relative mode.

Required fields:

```text
benchmark_id: str
benchmark_returns: list[Decimal]
max_tracking_error: Decimal
objective: "maximize_information_ratio" | "minimize_tracking_error" | "target_active_risk"
active_weight_limit: Decimal | None
```

#### 19Y.6.2 Active Benchmark Mode

When `mode = ACTIVE_BENCHMARK`, the optimizer objective shifts from absolute volatility reduction to benchmark-relative performance.

Supported benchmark-relative metrics:

```text
tracking_error
information_ratio
active_return
active_weight
```

The default active objective should be:

```text
maximize_information_ratio subject to max_tracking_error
```

If benchmark returns are missing, stale, too short, or misaligned with strategy returns, the optimizer must return `MISSING_BENCHMARK_EVIDENCE` or `BENCHMARK_ALIGNMENT_FAILED`.

### 19Y.7 Rebalancing Triggers and Drift Management

#### 19Y.7.1 `RebalanceTrigger`

The Portfolio Module must define explicit rebalance trigger policies.

| Trigger Type | Condition | Required Action |
|---|---|---|
| `SCHEDULED` | Time since last rebalance exceeds configured interval. | Run optimization and propose rebalance. |
| `DRIFT` | Absolute current-vs-target weight drift exceeds tolerance band. | Run minimal-trade rebalance. |
| `RISK_EVENT` | Portfolio VaR, CVaR, drawdown, margin, or kill/suspension state breaches limit. | Propose de-risking or suspension request. |
| `CAPACITY` | Strategy reaches or exceeds capacity cap. | Reallocate excess weight or hold cash. |

#### 19Y.7.2 Drift Formula

```text
drift_pct = abs(current_weight - target_weight)
```

A rebalance proposal is not required when all drifts remain within configured tolerance bands and no risk or capacity trigger exists.

#### 19Y.7.3 Minimal-Trade Rule

For drift-triggered rebalances, the rebalancer should prefer the smallest set of trades needed to bring the portfolio back within tolerance bands, rather than forcing a full target rebalance.

### 19Y.8 Kill-Switch vs Portfolio Suspension Boundary

#### 19Y.8.1 Portfolio Suspension Naming Rule

Portfolio must use the term `SuspensionManager` or `suspension.py` for portfolio-level strategy suspension workflows.

The Portfolio Module may emit:

```text
StrategySuspensionRequest
PortfolioSuspensionRequest
ResumeEligibilityReport
```

The Portfolio Module must not directly enforce broker-side kill-switch behavior.

#### 19Y.8.2 Responsibility Boundary

```text
Portfolio Module:
    Detects portfolio/lifecycle/allocation conditions requiring suspension.
    Emits structured suspension requests.
    Blocks new allocation proposals for suspended strategies.

Risk Governor:
    Validates the suspension request against risk policy.
    Approves, rejects, or escalates the suspension decision.

Execution Module:
    Enforces approved suspension by blocking new orders, reducing exposure, or closing positions where approved.
```

#### 19Y.8.3 Migration Note

Legacy `kill_switch.py` behavior in the audited folder should be split during rewrite:

```text
risk/execution hard kill-switch behavior -> Risk/Execution modules
portfolio suspension recommendation behavior -> portfolio/suspension.py
```

### 19Y.9 Cash Management Policy

#### 19Y.9.1 `CashPolicy`

The allocation engine must explicitly define how residual cash is handled.

```python
class CashPolicy(str, Enum):
    MINIMIZE_CASH = "minimize_cash"
    TARGET_CASH_PCT = "target_cash_pct"
    CASH_FLOOR = "cash_floor"
```

#### 19Y.9.2 Cash Handling Rules

`MINIMIZE_CASH` may allocate residual cash to the highest-ranked eligible strategy, subject to risk, capacity, margin, and cost constraints.

`TARGET_CASH_PCT` must preserve a configured cash target.

`CASH_FLOOR` must fail closed or produce a partial allocation if the proposed rebalance would reduce cash below the configured floor.

Residual cash must be explicitly reported in every allocation proposal.

### 19Y.10 Additional Official Contracts

The v5 rewrite should add the following contracts to `contracts.py`.

```text
TargetPortfolio
RebalanceOrderList
AllocationConstraints
RebalancingConstraints
OptimizationConfig
OptimizationResult
BenchmarkConfig
CapacityReport
CashPolicyConfig
StrategySuspensionRequest
PortfolioSuspensionRequest
ResumeEligibilityReport
```

### 19Y.11 Additional Official Tools

The v5 Portfolio Module should expose the following additional official AI tools only after they meet the HaruQuantAI Tool Function Standard.

```python
def optimize_portfolio(
    current_portfolio: PortfolioState,
    candidates: list[StrategyAllocationCandidate],
    optimization_config: OptimizationConfig,
    request_id: Optional[str] = None,
) -> dict[str, Any]:
    ...


def generate_rebalance_plan(
    current_portfolio: PortfolioState,
    target_portfolio: TargetPortfolio,
    constraints: RebalancingConstraints,
    request_id: Optional[str] = None,
) -> dict[str, Any]:
    ...


def detect_rebalance_triggers(
    current_portfolio: PortfolioState,
    target_portfolio: TargetPortfolio,
    trigger_policy: RebalanceTriggerPolicy,
    request_id: Optional[str] = None,
) -> dict[str, Any]:
    ...


def evaluate_strategy_capacity(
    candidates: list[StrategyAllocationCandidate],
    total_portfolio_nav: Decimal,
    request_id: Optional[str] = None,
) -> dict[str, Any]:
    ...


def create_suspension_request(
    strategy_id: str,
    reason: str,
    evidence: list[EvidenceItem],
    request_id: Optional[str] = None,
) -> dict[str, Any]:
    ...
```

These tools must use explicit signatures, standard metadata, deterministic error codes, `request_id`, execution timing, structured logging, and standard tool return schema.

### 19Y.12 Additional Error Codes

Add these error codes to the canonical portfolio error list:

```text
UNSUPPORTED_OPTIMIZATION_METHOD
MISSING_OPTIMIZATION_EVIDENCE
OPTIMIZATION_FAILED
OPTIMIZATION_CONSTRAINT_INFEASIBLE
REBALANCE_REJECTED
PARTIAL_REBALANCE_PROPOSED
TURNOVER_LIMIT_EXCEEDED
TRANSACTION_COST_LIMIT_EXCEEDED
MISSING_TRANSACTION_COST_EVIDENCE
MISSING_STRATEGY_CAPACITY
CAPACITY_LIMIT_EXCEEDED
MISSING_BENCHMARK_EVIDENCE
BENCHMARK_ALIGNMENT_FAILED
CASH_POLICY_VIOLATION
SUSPENSION_REQUEST_REQUIRED
SUSPENSION_POLICY_CONFLICT
```

### 19Y.13 Additional Testing Requirements

The v5 implementation must add tests for:

```text
optimizer method selection
unsupported optimizer method failure
minimum variance allocation
risk parity allocation
target risk allocation
turnover limit rejection
transaction cost limit rejection
partial rebalance proposal
minimum trade size filtering
capacity clamping
capacity-full redistribution
cash target preservation
cash floor violation
benchmark-relative tracking error calculation
benchmark alignment failure
rebalance trigger detection
minimal-trade drift rebalance
strategy suspension request creation
portfolio cannot directly enforce broker kill switch
sizing respects allocation weights before lot-size calculation
```

### 19Y.14 Recommended v5 Rewrite Order

The v5 rewrite order should be:

```text
1. contracts.py
2. errors.py
3. state_repository.py
4. exposure.py
5. risk.py
6. optimizer.py
7. rebalancer.py
8. allocation.py
9. sizing.py
10. lifecycle.py
11. suspension.py
12. reconciliation.py
13. audit.py
14. reporting.py
15. __init__.py registry
16. tests and usage examples
```

`optimizer.py` and `rebalancer.py` should be implemented before finalizing `allocation.py`, because allocation decisions must consume optimizer outputs and rebalance feasibility checks.

## 19Z. v5 Implementation Impact Summary

The v5 additions raise the Portfolio Module from a production-safe allocation/risk-support component into a more institutional portfolio management layer.

The most important design changes are:

```text
allocation.py is no longer the only allocation brain;
optimizer.py owns objective-driven portfolio construction;
rebalancer.py owns current-vs-target transition feasibility;
suspension.py replaces portfolio-level kill-switch enforcement;
capacity constraints become first-class allocation constraints;
cash policy becomes explicit rather than incidental;
benchmark-relative portfolio management becomes supported;
transaction costs and turnover are required before execution-ready proposals.
```

These additions do not permit Portfolio to place trades. Portfolio remains a proposal, validation, allocation, and suspension-request layer. Execution remains the only module that can interact with MT5 for live broker actions, and only after Risk/Governance approval gates pass.

## 20. Acceptance Criteria

The portfolio module is production-ready only when:

### 20.1 Core v1 Acceptance Criteria

- [ ] The folder lives under `tools/portfolio/` or the project has a documented reason for a different path.
- [ ] `__init__.py` is a clean registry only.
- [ ] Every function in `__all__` is an official AI Tool and follows the HaruQuant tool standard.
- [ ] Every official tool has explicit typed parameters.
- [ ] Every official tool accepts `request_id`.
- [ ] Every official tool returns the standard schema.
- [ ] Every official tool has accurate metadata and side-effect flags.
- [ ] Every official tool logs call, validation failure, success, and failure.
- [ ] Every official tool records real `execution_ms`.
- [ ] Every official tool validates input and returns deterministic error codes.
- [ ] High-risk portfolio decisions require evidence and approval where applicable.
- [ ] Kill-switch trigger is fail-closed and persisted.
- [ ] Kill-switch resume validates approval, not just an ID string.
- [ ] Audit write failure blocks high-risk/live-adjacent decisions.
- [ ] Portfolio module cannot place trades.
- [ ] Portfolio module cannot approve live trading alone.
- [ ] All contracts are typed and tested.
- [ ] Unit tests cover success, invalid input, edge cases, error paths, metadata, schema compliance, and safety gates.
- [ ] Usage examples exist for all official tools.
- [ ] Coverage is above 80%.
- [ ] Import tests pass from the project root.
- [ ] No missing dependencies remain undocumented.


### 20.2 Additional v2 Acceptance Criteria

- [ ] Every official tool uses the exact approved public signature or a documented compatible superset.
- [ ] No official AI Tool exposes `**kwargs` as the public interface.
- [ ] `PositionSnapshot`, `OrderSnapshot`, `InstrumentMetadata`, `PortfolioRiskSnapshot`, `ApprovalToken`, `LifecycleTransitionRequest`, and `LifecycleTransitionResult` contracts exist and are tested.
- [ ] Portfolio module consumes MT5-derived data only through execution/data snapshots and never performs MT5 broker actions directly.
- [ ] Execution/live-trading boundary checks portfolio allocation, lifecycle state, risk approval, kill switch, margin, broker heartbeat, audit availability, and approval validity.
- [ ] Formula conventions for returns, volatility, drawdown, VaR, CVaR, margin usage, and risk contribution are implemented and tested.
- [ ] Percent-like values use decimal convention, where `0.05` means 5%.
- [ ] VaR and CVaR are returned as positive loss magnitudes.
- [ ] Instrument metadata is required for live-adjacent decisions.
- [ ] Missing pip value, missing FX rate, stale FX rate, or missing instrument metadata fails closed where applicable.
- [ ] Symbol normalization handles broker suffixes and non-Forex instruments safely.
- [ ] Approval token validation checks expiry, revocation, action scope, portfolio/account/strategy match, and max risk change.
- [ ] Kill-switch state is persisted atomically.
- [ ] Unknown or unreadable kill-switch state blocks live execution.
- [ ] Kill-switch resume requires valid approval and cleared trigger evidence.
- [ ] Allocation and lifecycle decisions require idempotency keys.
- [ ] Duplicate idempotency key with different payload returns `IDEMPOTENCY_CONFLICT`.
- [ ] Concurrent lifecycle/allocation updates are locked or fail with `CONCURRENT_UPDATE`.
- [ ] Audit hash-chain genesis uses 64 zero characters for the first record.
- [ ] Audit chain failure blocks high-risk/live-adjacent decisions.
- [ ] Portfolio-specific error codes are documented and covered by unit tests.
- [ ] Integration tests prove the portfolio module cannot place trades and cannot bypass Risk Governor or Execution gates.

### 20.3 Additional v3 Acceptance Criteria

- [ ] Portfolio allocation state is persisted durably and restored across restarts.
- [ ] Strategy lifecycle state is persisted durably and restored across restarts.
- [ ] Portfolio state changes are recorded through append-first events before or alongside derived checkpoints.
- [ ] Startup recovery validates portfolio state, kill-switch state, manual-intervention flags, and audit/event hash continuity.
- [ ] Live-adjacent decisions fail closed if portfolio state recovery is incomplete or ambiguous.
- [ ] Performance benchmarks exist by Phase 5 for risk snapshots, VaR/CVaR, exposure aggregation, state loading, and event appends.
- [ ] Snapshot inputs include `as_of` timestamps where the source can provide them.
- [ ] Staleness thresholds are configurable and tested for broker, position, order, FX, metadata, equity curve, risk, approval, and portfolio state inputs.
- [ ] Stale or missing freshness evidence blocks live-adjacent decisions.
- [ ] `OrderSnapshot` includes requested, filled, and remaining volume plus order status.
- [ ] Partially filled orders contribute remaining pending exposure unless cancelled, expired, rejected, closed, or remaining volume is zero.
- [ ] Order state conflicts return `ORDER_STATE_CONFLICT` for live-adjacent workflows.
- [ ] Exposure logic handles or blocks when MT5 account mode is missing for netting vs hedging behavior.
- [ ] Idempotency records store canonical payload hashes and detect payload mismatch.
- [ ] Phase 1 approval validation checks all non-signature approval fields even if signature validation is disabled.
- [ ] Audit records clearly state when signature validation is skipped.
- [ ] Manual intervention blocks actionable portfolio decisions until reconciliation passes.
- [ ] Reconciliation report includes positions, orders, partial fills, account equity, margin, allocation mapping, lifecycle state, approvals, and kill-switch state.
- [ ] Broker-reported margin fields are not silently replaced by calculated estimates in live-adjacent workflows.

### 20.4 Additional v4 Acceptance Criteria

- [ ] `PORTFOLIO_STATE_RECOVERY_FAILED` and all v3/v4 fail-closed error codes are included in the canonical error-code list and tested.
- [ ] Full strategy correlation matrices are excluded from lightweight/default responses unless explicitly requested or stored as an artifact.
- [ ] Performance benchmark targets are documented as baselines and recalibrated only with measured evidence.
- [ ] Implementation treats all 19-series addenda as active requirements even if future documentation renumbering is performed.

---


### 20.5 Additional v5 Acceptance Criteria

- [ ] `optimizer.py` exists and supports approved Phase 1 optimization methods.
- [ ] `OptimizationConfig` and `OptimizationResult` contracts are defined and validated.
- [ ] Optimizer outputs include target weights and predicted metrics where evidence permits.
- [ ] Unsupported optimization methods return `UNSUPPORTED_OPTIMIZATION_METHOD`.
- [ ] `rebalancer.py` exists and produces current-vs-target rebalance plans.
- [ ] Rebalancing validates turnover, transaction cost, minimum trade size, and tolerance bands.
- [ ] Excessive turnover or transaction cost returns rejection or partial-rebalance response.
- [ ] Strategy capacity is enforced and capacity-limited strategies are marked `CAP_FULL`.
- [ ] Excess capital is redistributed or held as cash according to `CashPolicy`.
- [ ] Benchmark-relative allocation supports tracking error and information ratio.
- [ ] Benchmark evidence staleness and alignment are validated.
- [ ] Rebalance triggers are explicit and tested for scheduled, drift, risk-event, and capacity conditions.
- [ ] Portfolio suspension requests are separated from Risk/Execution kill-switch enforcement.
- [ ] Portfolio cannot directly place trades, close trades, or enforce broker-side kill switch behavior.
- [ ] Sizing tools respect approved allocation weights before lot-size calculation.
- [ ] Unit tests cover optimizer constraints, turnover, costs, capacity, benchmark-relative allocation, cash policy, and suspension boundaries.
- [ ] Usage examples show optimizer-to-rebalancer-to-risk-gate workflow without direct broker execution.

## 21. Final Recommendation

Do not rewrite this module by editing `standard_tools.py` in place. The current file is too broad and hides too many responsibilities behind `**kwargs`. With v4 complete, the specification is now ready to be used as the implementation baseline, but the implementation itself must still be rebuilt from scratch against this document.

The correct next step is a **clean production rewrite** using the current folder as a functionality inventory. Preserve the business capabilities, but restructure the implementation around focused files, typed contracts, deterministic validation, explicit policy gates, structured logging, audit records, and tests.

Recommended rewrite order:

1. `contracts.py`
2. `errors.py`
3. `validators.py`
4. `state_repository.py`
5. `reconciliation.py`
6. `exposure.py`
5. `risk.py`
6. `sizing.py`
7. `allocation.py`
8. `lifecycle.py`
9. `kill_switch.py`
10. `audit.py`
11. `reporting.py`
12. `cost.py`
13. `incidents.py`
14. `__init__.py`
15. unit tests and usage examples

This module should become one of the core safety boundaries between strategy validation, risk approval, and live execution.

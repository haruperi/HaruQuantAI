# HaruQuant Execution Module Technical Specification

**Document name:** `HaruQuant_Execution_Module_Technical_Specification.md`
**Status:** Production-grade MT5 execution baseline with institutional OMS/TCA/SOR-readiness extensions
**Version:** v5.0.0
**Date:** 2026-05-31
**Basis:** Current execution-module audit and current-state technical inventory
**Implementation stance:** Rebuild, do not copy. Preserve business capability without preserving legacy bloat. MT5 is the primary live broker target for Phase 1 production live trading.

## v4 Update Summary

Version 4 adds final live-trading hardening requirements discovered during production-readiness review:

- explicit partial-fill lifecycle and reconciliation behavior;
- idempotency rules for duplicate modify/cancel commands;
- kill-switch behavior for in-flight and unknown-outcome broker commands;
- Phase 1 scope for MT5 trailing stops;
- max slippage/deviation controls;
- broker-side order expiration and time-in-force rules;
- position-level reconciliation after partial closes;
- deterministic MT5 netting-account unsupported error code;
- additional state-machine states and acceptance gates for partial-fill and manual-review workflows.

These changes do not expand the first implementation unnecessarily. They clarify safety-critical behavior so Phase 1 can remain compact while still being production-grade.

---

## v5 Institutional OMS/TCA/SOR-Readiness Update Summary

Version 5 keeps the v4 MT5 live-trading baseline intact and adds institutional execution architecture requirements that prepare the module for a future full OMS without forcing unnecessary complexity into Phase 1. The additions are intentionally phased: direct MT5 execution remains the Phase 1 implementation target, while parent-child orders, algorithmic slicing, batch execution, event streaming, TCA bridges, and session recovery are defined as contracts and extension points.

Version 5 adds:

- Smart Order Routing and parent-child order architecture;
- algorithmic execution configuration for DIRECT, TWAP, VWAP, ICEBERG, and POV;
- child-order records and deterministic child idempotency derivation;
- ExecutionQualityMetrics for downstream transaction cost analysis;
- ExecutionTimestamps for best-execution audit and latency breakdowns;
- AtomicBatchCommand support for portfolio rebalance workflows;
- modify-order validation and requote policy rules;
- internal execution event stream requirements for dashboards and agents;
- session sequence tracking and reconnect recovery rules;
- additional storage, monitoring, testing, and companion-document requirements.

These requirements do not mean Phase 1 must implement full SOR, TWAP, VWAP, or portfolio rebalance execution. Phase 1 must implement the contracts and fail-safe defaults so that unsupported institutional modes are blocked deterministically rather than ignored, silently downgraded, or accidentally routed through live MT5.

---

## 1. Executive Summary

The new HaruQuant Execution Module is the controlled execution subsystem responsible for turning approved strategy and risk decisions into auditable paper or live broker actions.

This is a **complete redo** of the current execution module. The old module is used only as a functionality inventory so that the new implementation does not degrade existing capabilities. The new module must not copy the old structure, large files, dynamic behavior, loosely typed critical tools, or unclear execution paths.

The redesigned module must be:

- production-grade;
- deterministic at all safety boundaries;
- agent-safe;
- broker-safe;
- approval-gated;
- risk-gated;
- kill-switch-aware;
- idempotent;
- reconciled against broker truth;
- fully logged and auditable;
- testable with mocked broker adapters;
- compatible with paper, shadow, and live execution modes;
- clean enough for future humans and agents to maintain.

The most important architectural rule is:

```text
There must be exactly one live broker mutation boundary.
```

No agent, workflow, strategy, live engine, helper, simulator, or low-level broker adapter may bypass this boundary.

---

## 1A. v2 Update Summary

This v2 update strengthens the v1 execution-module specification for production live trading through MT5. It adds:

- a formal Risk Management dependency contract;
- RiskDecisionPackage schema requirements;
- required risk functional and non-functional coverage before live execution can proceed;
- MT5 terminal, account, symbol, order-send, position-mode, magic-number, and reconciliation requirements;
- MT5-specific error and retcode mapping requirements;
- MT5 environment and secret requirements;
- MT5-specific unit, integration, failure-path, and staging/live acceptance tests.

This document remains an Execution Module specification. It does not move risk calculations into execution. The Risk Management Module owns risk logic; the Execution Module validates and enforces the risk decision package before it mutates live broker state.

## 1B. v3 Production Hardening Update Summary

This v3 update adds the final production-readiness requirements needed before implementation can be treated as production-grade for MT5 live trading. It adds:

- a strict execution state machine;
- account, symbol, strategy, order, and position concurrency locks;
- persistent storage requirements for commands, attempts, receipts, broker tickets, reconciliation, approvals, and manual reviews;
- a manual intervention workflow for unknown broker outcomes and reconciliation mismatches;
- staged rollout gates from paper to production live trading;
- an MT5 magic-number registry requirement;
- runtime deployment assumptions for Windows/MT5 operation;
- mandatory operations runbooks;
- metrics, alerts, and SLOs;
- CI/CD quality gates aligned with HaruQuant code standards.

After v3, this document is considered production-grade as a target specification and ready to drive phase-by-phase implementation. It is still not implementation proof by itself; production readiness requires code, tests, staging evidence, MT5 demo evidence, audit evidence, and live rollout approval.

---

## 2. Goals

### 2.1 Primary Goals

The new Execution Module shall:

1. Provide a safe, typed, auditable execution interface for HaruQuant agents and workflows.
2. Support broker connectivity checks, readiness checks, paper trading, shadow execution, live execution requests, kill-switch workflows, reconciliation, monitoring, and execution reporting.
3. Preserve the useful capabilities identified in the old module audit without carrying forward old structural bloat.
4. Enforce deterministic gates before any live-capital action.
5. Separate request packaging, validation, approval, policy checks, broker mutation, receipts, reconciliation, and reporting.
6. Support MT5 as the Phase 1 production live broker through an explicit broker adapter interface, with cTrader retained as a future adapter target.
7. Keep official AI tools thin, typed, standardized, and imported only from `tools.execution`.

### 2.2 Non-Goals

The new Execution Module shall not:

1. Decide whether a strategy is profitable.
2. Approve risk by itself.
3. Approve live trading by itself.
4. Override the kill switch.
5. Allow LLM reasoning to bypass deterministic execution policy.
6. Expose low-level broker APIs directly to agents.
7. Mix simulation engine internals with live execution state.
8. Store or log broker credentials, account passwords, or secret tokens.
9. Use `**kwargs` for critical live-capital tools.
10. Recreate the old module file-for-file.

---

## 3. Production Design Principles

### 3.1 Safety First

Execution is a critical domain because it can affect live capital. The default behavior must be fail-closed.

```text
If approval, risk, readiness, broker state, kill-switch state, idempotency, or auditability is uncertain, block the action.
```

### 3.2 Few Public Tools, Strong Internal Services

The official agent-facing surface should be small and stable. Most complexity should live behind deterministic services and typed contracts.

### 3.3 Agents Request, Policy Decides, Gateway Executes

Agents may request execution workflows. They may not directly execute live broker mutations.

```text
Agent/tool request
  -> typed command
  -> policy gate
  -> readiness gate
  -> idempotency gate
  -> audit pre-record
  -> single broker gateway
  -> receipt
  -> reconciliation
  -> audit completion record
```

### 3.4 Contract-First Implementation

Before implementation logic, the module must define request, command, decision, attempt, receipt, reconciliation, and report contracts.

### 3.5 Broker Truth Wins

Local state is useful, but broker state is authoritative for live positions, orders, fills, and account status. The module must reconcile local execution records against broker truth.

### 3.6 Paper and Live Must Share Contracts but Not Authority

Paper execution should use the same order contracts where practical, but paper execution must not share live broker mutation authority.

---

## 4. Functional Capability Preservation Matrix

The old module contained many valuable capabilities. The new module must preserve them in a cleaner form.

| Current Capability | Preserve? | New Location / Design |
|---|---:|---|
| Broker connection checks | Yes | `broker_status.py`, `brokers/base.py`, official status tool |
| Account info checks | Yes | broker adapter read interface and status service |
| Symbol info checks | Yes | broker adapter read interface and readiness service |
| Bid/ask/spread checks | Yes | broker quote snapshot service |
| Trade permission checks | Yes | broker status and readiness checks |
| Market-open checks | Yes | readiness service |
| Min/max lot and lot-step checks | Yes | order validation service |
| Stop-distance checks | Yes | order validation service |
| Free-margin checks | Yes | risk/readiness gate |
| Execution readiness checks | Yes | first-class `ExecutionReadinessService` |
| Order request validation | Yes | typed Pydantic/dataclass contracts + validators |
| Runtime config validation | Yes | `ExecutionConfig` schema |
| Broker-symbol mapping validation | Yes | readiness service |
| Environment validation | Yes | readiness service and config service |
| Transaction-cost estimation | Yes | execution plan service |
| Slippage estimation | Yes | execution plan service |
| Execution plan construction | Yes | `ExecutionPlanService` |
| Paper strategy start/stop | Yes | paper session service, not live gateway |
| Paper order submit/modify/close | Yes | paper broker adapter |
| Paper fill recording | Yes | paper receipt service |
| Paper vs backtest comparison | Yes | execution reporting service |
| Live order request packaging | Yes | typed official tools returning command packets |
| Live order submit/modify/cancel/close | Yes | single live gateway after gates |
| Exposure reduction | Yes | controlled live command type |
| Pause/resume live strategy | Yes | runtime state service with audit |
| Sync live positions | Yes | reconciliation service |
| Broker reconciliation | Yes | mandatory service |
| Kill-switch activation | Yes | deterministic kill-switch service |
| Strategy/symbol/global kill switch | Yes | scoped kill-switch state |
| Disable new orders | Yes | kill-switch enforcement action |
| Close all positions | Yes | kill-switch enforcement command through gateway |
| Cancel all orders | Yes | kill-switch enforcement command through gateway |
| Kill-switch event recording | Yes | audit and incident service |
| Re-enable approval | Yes | approval service and policy gate |
| Approval packet/voting model | Yes | governance dependency, validated by policy |
| Idempotency keys | Yes | required for all broker-mutating commands |
| Attempts and receipts | Yes | mandatory persistence model |
| Compensation plans | Yes | explicit failure recovery service |
| Incident monitoring | Yes | monitoring service |
| Latency monitoring | Yes | telemetry service |
| Stale-state monitoring | Yes | monitoring service |
| MT5 bridge | Yes | broker adapter implementation |
| cTrader bridge | Yes | broker adapter implementation |
| Shadow execution | Yes | shadow mode runtime, no live mutation |
| Multi-strategy live engine | Yes | runtime orchestrator only, never policy owner |
| Legacy simulator/trading helpers | Isolate | move to simulation compatibility or delete if obsolete |
| Dynamic lazy service resolution | No | replace with explicit imports and dependency injection |
| Large god files | No | split by responsibility |
| Critical `**kwargs` tools | No | replace with typed parameters or request models |
| Approval-id-only validation | No | validate approval object and scope |
| Direct low-level broker exposure to agents | No | internal only |

---

## 5. Target Package Structure

```text
tools/execution/
    __init__.py
    contracts.py
    errors.py
    config.py
    policy.py
    readiness.py
    planning.py
    commands.py
    gateway.py
    attempts.py
    receipts.py
    reconciliation.py
    kill_switch.py
    monitoring.py
    reporting.py
    broker_status.py
    audit.py

    brokers/
        __init__.py
        base.py
        mt5.py
        ctrader.py
        paper.py

    live/
        __init__.py
        engine.py
        session.py
        state.py
        signal_processor.py
        position_cache.py

    shadow/
        __init__.py
        engine.py
        comparator.py

    examples/
        README.md
```

### 5.1 File Responsibilities

| File | Responsibility |
|---|---|
| `__init__.py` | Official agent-facing tool registry only. No business logic. |
| `contracts.py` | Typed contracts for orders, commands, decisions, attempts, receipts, statuses, reports. |
| `errors.py` | Deterministic execution error codes and domain exceptions. |
| `config.py` | Execution configuration schema, broker profile config, safe secret references. |
| `policy.py` | Deterministic approval/risk/kill-switch/environment gates. |
| `readiness.py` | Order, broker, account, symbol, environment, and runtime readiness checks. |
| `planning.py` | Execution plan construction, cost estimation, slippage estimation. |
| `commands.py` | Command creation, normalization, validation, and idempotency-key binding. |
| `gateway.py` | The only live broker mutation boundary. |
| `attempts.py` | Attempt lifecycle and idempotency persistence. |
| `receipts.py` | Broker response normalization into execution receipts. |
| `reconciliation.py` | Broker truth comparison and local-state correction workflow. |
| `kill_switch.py` | Scoped kill-switch status, activation, enforcement, and re-enable control. |
| `monitoring.py` | Health, latency, stale-state, timeout, incident, and operational status checks. |
| `reporting.py` | Paper/live/shadow execution reports. |
| `broker_status.py` | Read-only broker, account, symbol, quote, spread, permission status. |
| `audit.py` | Execution-specific audit record building and redaction helpers. |
| `brokers/base.py` | Broker adapter protocol/interface. |
| `brokers/mt5.py` | MT5 adapter implementation. |
| `brokers/ctrader.py` | cTrader adapter implementation. |
| `brokers/paper.py` | Paper broker adapter implementation. |
| `live/engine.py` | Runtime orchestrator; may not bypass gateway or policy. |
| `shadow/engine.py` | Shadow execution runtime with no broker mutation. |

---

## 6. Official Agent-Facing Tool Surface

The old module exposed 53 root tools. The new module should expose fewer, stronger, typed workflow tools.

### 6.1 Recommended Official Tools

```text
check_execution_readiness
build_execution_plan
get_broker_connectivity_status
get_execution_status
submit_paper_order_request
modify_paper_order_request
close_paper_position_request
submit_live_order_request
modify_live_order_request
cancel_live_order_request
close_live_position_request
reduce_live_exposure_request
pause_live_strategy_request
resume_live_strategy_request
get_kill_switch_status
request_kill_switch_activation
request_kill_switch_reenable
reconcile_execution_state
build_execution_report
```

### 6.2 Tool Import Rule

Agents and workflows must import official execution tools only from the domain package:

```python
from tools.execution import check_execution_readiness
from tools.execution import submit_live_order_request
```

They must not import from deep implementation files:

```python
# Not allowed in agents/workflows
from tools.execution.gateway import LiveBrokerExecutionGateway
from tools.execution.brokers.mt5 import MT5BrokerAdapter
```

### 6.3 Official Tool Requirements

Every official execution tool must include:

- module-level docstring;
- agent-facing function docstring;
- explicit type hints;
- explicit input validation;
- `request_id: Optional[str] = None`;
- `workflow_id: Optional[str] = None` for workflow-aware tools;
- structured logging;
- deterministic error codes;
- standard HaruQuant tool return schema;
- tool metadata constants;
- side-effect flags;
- approval requirement flag;
- no raw broker calls unless the tool explicitly represents a policy-gated command path;
- unit tests;
- usage example.

---

## 7. Standard Tool Response Schema

Every official tool shall return:

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
        "tool_category": "execution",
        "tool_risk_level": "low" | "medium" | "high" | "critical",
        "request_id": str | None,
        "workflow_id": str | None,
        "execution_ms": float,
        "read_only": bool,
        "writes_file": bool,
        "modifies_database": bool,
        "places_trade": bool,
        "requires_network": bool,
        "requires_approval": bool,
    },
}
```

Critical live-capital tools must set:

```python
TOOL_RISK_LEVEL = "critical"
REQUIRES_APPROVAL = True
READ_ONLY = False
PLACES_TRADE = True
REQUIRES_NETWORK = True
```

---

## 8. Core Domain Contracts

The new module should use Pydantic models or dataclasses with explicit validation. Pydantic is recommended where JSON schema export and agent compatibility matter.

### 8.1 ExecutionMode

```text
paper
shadow
live
reconciliation_only
report_only
```

### 8.2 OrderSide

```text
buy
sell
```

### 8.3 OrderType

```text
market
limit
stop
stop_limit
```

### 8.4 TimeInForce

```text
gtc
day
ioc
fok
gtd
```

`gtc` is the Phase 1 default unless the strategy or execution plan explicitly requests another supported mode.

For `gtd` orders, the execution module must persist `expires_at`, monitor broker-side expiration, and reconcile the local order state after expiration. If broker-side GTD support is unavailable or not enabled, the command must fail before broker send with `UNSUPPORTED_TIME_IN_FORCE`.

For Phase 1, responsibility for long-lived GTC order lifetime policy remains with the strategy and risk policy. Execution must still expose cancel tools and reconciliation so stale orders can be detected and removed safely.

### 8.5 ExecutionCommandType

```text
submit_order
modify_order
cancel_order
close_position
reduce_exposure
pause_strategy
resume_strategy
cancel_all_orders
close_all_positions
kill_switch_activate
kill_switch_reenable
sync_positions
reconcile_state
```

### 8.6 ExecutionRequest

Required fields:

```text
request_id
workflow_id
strategy_id
symbol
execution_mode
command_type
account_id or account_alias
broker
created_at
requested_by
source_agent
```

Optional fields:

```text
reason
notes
metadata
correlation_id
parent_request_id
```

### 8.7 OrderRequest

Required fields:

```text
symbol
side
order_type
volume
```

Conditional fields:

```text
price                 required for limit/stop-style orders
stop_loss             optional but validated if present
take_profit           optional but validated if present
time_in_force         default configurable
client_order_id       required after command creation
idempotency_key       required before send
```

### 8.8 RiskDecisionReference

Required fields:

```text
risk_decision_id
risk_status           approved | rejected | blocked | expired
risk_scope            symbol/account/strategy/action scope
max_allowed_volume
max_allowed_exposure
expires_at
```

### 8.9 ApprovalReference

Required fields:

```text
approval_id
approval_status       approved | rejected | expired | revoked | pending
approval_scope
approved_by
approved_at
expires_at
```

### 8.10 ExecutionPlan

Required fields:

```text
plan_id
request_id
workflow_id
symbol
side
order_type
volume
estimated_price
estimated_spread
estimated_slippage
estimated_commission
estimated_swap_or_financing
estimated_margin_required
expected_risk_impact
readiness_summary
warnings
created_at
```

### 8.11 ExecutionCommand

Required fields:

```text
command_id
request_id
workflow_id
command_type
execution_mode
broker
account_id
strategy_id
symbol
order_request or position_request
risk_decision_ref
approval_ref for live critical commands
idempotency_key
created_at
status
```

Valid command statuses:

```text
created
validated
blocked
ready_to_send
sending
sent
acknowledged
partially_filled
filled
rejected
failed
timed_out
cancelled
reconciled
```

### 8.12 ExecutionAttempt

Required fields:

```text
attempt_id
command_id
idempotency_key
attempt_number
started_at
ended_at
status
broker_request_payload_redacted
broker_response_payload_redacted
error_code
error_message
```

### 8.13 ExecutionReceipt

Required fields:

```text
receipt_id
attempt_id
command_id
broker
broker_order_id
broker_deal_id
broker_position_id
symbol
side
requested_volume
filled_volume
average_fill_price
commission
swap
fees
slippage
status
received_at
raw_response_ref
```

### 8.14 ReconciliationResult

Required fields:

```text
reconciliation_id
request_id
workflow_id
broker
account_id
scope
started_at
completed_at
status
local_orders_checked
broker_orders_checked
local_positions_checked
broker_positions_checked
matches
mismatches
missing_local_records
missing_broker_records
actions_required
incident_ids
```

### 8.15 KillSwitchState

Required fields:

```text
scope_type            global | strategy | symbol | account
scope_id
is_active
reason
activated_by
activated_at
expires_at optional
requires_reenable_approval
reenable_approval_id optional
```

---

## 9. Execution Lifecycle

### 9.1 Read-Only Status Flow

```text
Agent/workflow
  -> official read-only status tool
  -> broker status service
  -> broker adapter read method
  -> normalized status response
  -> standard tool response
```

Examples:

- broker connection status;
- symbol metadata;
- account margin snapshot;
- current spread;
- kill-switch status;
- execution status report.

### 9.2 Paper Order Flow

```text
Agent/workflow
  -> submit_paper_order_request
  -> validate order request
  -> build execution plan
  -> paper broker adapter
  -> paper attempt record
  -> paper receipt
  -> paper reconciliation/reporting
```

Paper execution should be safe and reversible, but it must still be logged and auditable because agents and workflows use paper results for future promotion decisions.

### 9.3 Live Order Request Flow

```text
Agent/workflow
  -> submit_live_order_request
  -> typed request validation
  -> execution plan
  -> risk decision validation
  -> approval validation
  -> kill-switch check
  -> readiness check
  -> idempotency check
  -> command creation
  -> audit pre-record
  -> LiveBrokerExecutionGateway
  -> broker adapter
  -> attempt record
  -> receipt
  -> reconciliation
  -> audit completion record
  -> standard result
```

### 9.4 Kill-Switch Activation Flow

```text
Trigger request
  -> validate trigger authority
  -> validate scope
  -> create kill-switch event
  -> activate scoped state
  -> block new orders immediately
  -> optionally cancel open orders through gateway
  -> optionally close positions through gateway
  -> create incident/audit record
  -> require re-enable approval
```

### 9.5 Re-Enable Flow

```text
Re-enable request
  -> validate kill-switch scope
  -> require approval
  -> verify issue resolved
  -> reconcile broker state
  -> clear or expire kill-switch state
  -> audit re-enable event
```

---

## 10. Single Live Broker Mutation Boundary

### 10.1 Gateway Rule

Only `LiveBrokerExecutionGateway` may call broker adapter mutation methods for live accounts.

Allowed live mutation methods:

```text
submit_order
modify_order
cancel_order
close_position
reduce_position
cancel_all_orders
close_all_positions
```

All other components must submit commands to the gateway.

### 10.2 Gateway Preconditions

The gateway must refuse live mutation unless all are true:

- command is typed and valid;
- command mode is `live`;
- risk decision is valid and scoped;
- approval is valid, scoped, unexpired, and not revoked;
- kill switch is clear for global/account/strategy/symbol scope;
- readiness check passed;
- idempotency key is present and unused or safely replayable;
- broker adapter is healthy;
- account and symbol are tradable;
- audit pre-record was written successfully;
- request_id and workflow_id are present;
- secrets are available only through safe runtime secret references.

### 10.3 Gateway Output

The gateway must return an `ExecutionReceipt` or structured failure with deterministic error code. It must never return raw broker responses directly to agents.

---

## 11. Deterministic Policy Gates

Policy must be implemented in code, not only prompts.

### 11.1 Required Policy Checks

```text
validate_execution_mode
validate_requested_action_allowed
validate_risk_decision
validate_approval
validate_kill_switch_clear
validate_account_scope
validate_strategy_scope
validate_symbol_scope
validate_order_limits
validate_idempotency_key
validate_audit_precondition
```

### 11.2 Approval Validation Rules

For live-capital commands, an `approval_id` string is not enough. The policy service must prove:

- approval exists;
- approval status is `approved`;
- approval is not expired;
- approval is not revoked;
- approval scope matches command type, symbol, strategy, account, and risk class;
- approver is authorized;
- approval was granted after the relevant risk decision and execution plan were created;
- approval has not already been consumed when single-use approval is required.

### 11.3 Risk Decision Validation Rules

Live-capital execution must require a valid risk decision package:

- status must be `approved`;
- decision must be within expiry;
- account, symbol, strategy, and exposure scope must match;
- volume and risk impact must not exceed allowed values;
- decision must reference current portfolio/risk snapshot;
- stale or missing evidence must block execution.

### 11.4 Kill-Switch Rules

Execution must be blocked when any applicable kill switch is active:

- global;
- account;
- strategy;
- symbol;
- broker;
- environment.

Only emergency liquidation commands explicitly allowed by policy may run while a kill switch is active.

---


## 11A. Risk Management Dependency Contract

The Execution Module must not calculate final trading risk or approve risk by itself. It must consume a deterministic, auditable `RiskDecisionPackage` produced by the Risk Management Module.

The purpose of this section is to define what execution requires from risk so that live MT5 trading cannot proceed with incomplete, stale, or weak risk evidence.

### 11A.1 Ownership Boundary

| Responsibility | Owner |
|---|---|
| Calculate per-trade risk | Risk Management Module |
| Calculate portfolio exposure | Risk Management Module |
| Calculate margin impact | Risk Management Module with broker/account snapshot input |
| Enforce execution-time block/allow decision | Execution policy gate |
| Validate RiskDecisionPackage scope and freshness | Execution policy gate |
| Send order to MT5 | Execution gateway only |
| Reconcile broker result | Execution reconciliation service |
| Trigger risk breach kill switch | Risk + Execution policy integration |

The Execution Module may duplicate lightweight validation checks for safety, but those checks are enforcement gates, not the source of risk truth.

### 11A.2 Required RiskDecisionPackage Contract

Every live-capital command that can open, increase, modify, or maintain exposure must include a valid `RiskDecisionPackage`.

Required fields:

```text
schema_version
risk_decision_id
request_id
workflow_id
created_at
expires_at
producer
producer_version
decision_status          approved | rejected | blocked | needs_review
execution_scope          live | staging_live | paper | shadow
account_alias
broker                   mt5
broker_account_login
strategy_id
strategy_version optional
symbol
broker_symbol
command_type
side optional
requested_volume
approved_max_volume
approved_max_risk_amount
max_allowed_deviation_points
approved_max_risk_percent
approved_stop_loss optional
approved_take_profit optional
approved_price_limit optional
portfolio_snapshot_id
risk_snapshot_id
risk_policy_version
approval_required
required_approval_class
risk_checks
blockers
warnings
evidence_references
metadata
```

`risk_checks` must include structured check results for each applicable risk rule:

```text
per_trade_risk
position_size
stop_loss_policy
symbol_exposure
strategy_exposure
account_exposure
currency_exposure
correlation_exposure
margin_impact
pending_order_exposure
daily_loss_limit
total_loss_limit
drawdown_state
news_restriction
weekend_overnight_policy
spread_and_slippage_tolerance
var_cvar_impact
stress_scenario_impact
prop_firm_rule_compliance
kill_switch_trigger_state
```

Each check result must contain:

```text
name
status                 pass | warn | fail | not_applicable
severity               info | warning | blocker
code
message
measured_value optional
limit_value optional
evidence_reference optional
```

### 11A.3 Risk Decision Validation Rules in Execution

The execution policy gate must block live execution when any of the following is true:

- `RiskDecisionPackage` is missing;
- `decision_status` is not `approved`;
- package is expired;
- `request_id` or `workflow_id` does not match the execution command;
- `account_alias`, MT5 login, symbol, broker symbol, strategy, side, command type, or volume scope does not match;
- requested volume exceeds `approved_max_volume`;
- requested risk exceeds approved risk amount or percent;
- stop-loss or take-profit has been changed beyond risk-approved bounds;
- package does not reference current-enough portfolio and risk snapshots;
- required risk checks are missing;
- any required risk check has `severity=blocker` or `status=fail`;
- risk policy version is unsupported or deprecated;
- evidence references are missing for material risk decisions;
- package was created before the execution plan when policy requires plan-aware risk approval;
- package was created before a material portfolio/account state change;
- package was produced for paper/shadow but command is live.

### 11A.4 Required Risk Management Functional Requirements

The Risk Management Module must provide the following capabilities before production live MT5 execution is enabled:

| ID | Requirement |
|---|---|
| RISK-FR-001 | Validate max risk per trade using account equity/balance and configured risk policy. |
| RISK-FR-002 | Validate position size, broker volume min/max/step, and approved lot size. |
| RISK-FR-003 | Enforce stop-loss policy, including whether SL is mandatory for the strategy/account. |
| RISK-FR-004 | Calculate symbol-level exposure before and after the proposed command. |
| RISK-FR-005 | Calculate strategy-level exposure before and after the proposed command. |
| RISK-FR-006 | Calculate account-level total exposure before and after the proposed command. |
| RISK-FR-007 | Calculate currency-cluster exposure for forex and metals where applicable. |
| RISK-FR-008 | Evaluate correlation exposure against the current portfolio. |
| RISK-FR-009 | Include pending orders in projected exposure and margin calculations. |
| RISK-FR-010 | Validate free margin and margin level before and after the proposed command. |
| RISK-FR-011 | Enforce max daily loss using equity-based and realized/unrealized measures as configured. |
| RISK-FR-012 | Enforce max total loss / account drawdown rule. |
| RISK-FR-013 | Track drawdown state and reduce/block risk in restricted states. |
| RISK-FR-014 | Enforce high-impact news restriction windows. |
| RISK-FR-015 | Enforce weekend and overnight holding restrictions. |
| RISK-FR-016 | Calculate VaR/CVaR impact where enabled. |
| RISK-FR-017 | Evaluate configured stress scenarios before approval. |
| RISK-FR-018 | Enforce prop-firm rules such as max daily loss, max loss, profit target, news restrictions, consistency/best-day rule where applicable. |
| RISK-FR-019 | Produce deterministic block/approve decisions with evidence references. |
| RISK-FR-020 | Emit risk breach signals that can activate execution kill switches. |
| RISK-FR-021 | Define risk-decision expiry and mandatory revalidation triggers. |
| RISK-FR-022 | Support manual-review states without allowing execution to continue. |

### 11A.5 Required Risk Management Non-Functional Requirements

| ID | Requirement |
|---|---|
| RISK-NFR-001 | Risk decisions must be deterministic and reproducible from stored snapshots and evidence references. |
| RISK-NFR-002 | Risk decisions must fail closed when portfolio, account, market, or broker evidence is stale or missing. |
| RISK-NFR-003 | Risk checks must complete within the configured live-execution latency budget. |
| RISK-NFR-004 | Risk snapshots must be versioned and immutable once used by execution. |
| RISK-NFR-005 | Risk decisions must include request_id, workflow_id, strategy_id, account_alias, broker, and symbol traceability. |
| RISK-NFR-006 | Risk decisions must be auditable without exposing credentials or secrets. |
| RISK-NFR-007 | Risk rules must be configurable but protected from unauthorized runtime mutation. |
| RISK-NFR-008 | Risk decisions must be covered by unit, contract, failure-path, and regression tests. |
| RISK-NFR-009 | Risk decisions used for live MT5 execution must be validated against current MT5 account and symbol constraints. |
| RISK-NFR-010 | Risk outputs must remain schema-compatible across execution, portfolio, dashboard, and audit consumers. |

### 11A.6 Revalidation Triggers

Execution must request or require a new risk decision when any of the following changes after the decision was produced:

- account equity, balance, margin, or free margin changes beyond configured tolerance;
- open positions change;
- pending orders change;
- symbol quote becomes stale and refreshes materially;
- spread exceeds approved threshold;
- requested order price, volume, SL, or TP changes;
- strategy state changes;
- kill switch changes;
- high-impact news window begins;
- market session status changes;
- risk policy version changes;
- approval scope changes or expires.

---

## 12. Readiness Service Requirements

The `ExecutionReadinessService` shall produce a structured readiness report before any paper/live command.

### 12.1 Readiness Categories

```text
request_validation
strategy_runtime_config
execution_environment
broker_connection
account_status
symbol_status
market_session
trade_permissions
quote_freshness
spread
slippage
transaction_cost
order_size
order_price
stop_loss_take_profit
margin
risk_decision
approval
kill_switch
idempotency
auditability
```

### 12.2 Readiness Check Severity

```text
info
warning
blocker
```

Warnings may allow paper execution, but blockers must prevent live execution.

### 12.3 Readiness Output

```python
{
    "status": "ready" | "not_ready" | "ready_with_warnings",
    "checks": [
        {
            "name": str,
            "status": "pass" | "warn" | "fail",
            "severity": "info" | "warning" | "blocker",
            "code": str,
            "message": str,
            "evidence": dict,
        }
    ],
    "blockers": list[str],
    "warnings": list[str],
}
```

---

## 13. Broker Adapter Interface

### 13.1 Base Broker Adapter

Every broker adapter must support read-only methods and mutation methods separately.

Read-only methods:

```text
connect
health_check
get_account_info
get_symbol_info
get_quote
get_spread
get_trade_permissions
get_open_orders
get_open_positions
get_order_history
get_deal_history
```

Mutation methods:

```text
submit_order
modify_order
cancel_order
close_position
cancel_all_orders
close_all_positions
```

Mutation methods are internal only. They are called by `LiveBrokerExecutionGateway`, never by agents.

### 13.2 Adapter Requirements

Each adapter must:

- normalize broker-specific symbols;
- normalize broker-specific order types;
- map broker error codes to HaruQuant execution error codes;
- enforce timeout limits;
- avoid logging secrets;
- return structured adapter results;
- be fully mockable in tests;
- support dry-run or paper-equivalent mode where practical.

### 13.3 Supported Brokers

Initial supported adapters:

```text
MT5BrokerAdapter
CTraderBrokerAdapter
PaperBrokerAdapter
```

The paper adapter may implement mutation methods directly because it does not affect live capital. It must still produce attempts and receipts.

---


## 13A. MT5 Live Broker Adapter Requirements

MT5 is the Phase 1 production live broker target. The `MT5BrokerAdapter` must be treated as a critical infrastructure component and must not be exposed directly to agents.

### 13A.1 MT5 Terminal Lifecycle Requirements

The adapter/readiness service must validate:

- MT5 package/import availability;
- configured terminal path exists;
- terminal initializes successfully;
- login succeeds;
- connected server matches configured server;
- account login matches configured live account;
- environment is explicitly `demo`, `staging_live`, or `production_live`;
- terminal connection is healthy before every live mutation;
- terminal is not disconnected, frozen, or returning stale data;
- shutdown is safe and does not interrupt in-flight reconciliation;
- reconnect behavior is bounded and deterministic.

### 13A.2 MT5 Account Validation Requirements

Before live execution, MT5 account information must be available and fresh.

Required checks:

```text
account_info_available
login_matches_expected_account
server_matches_expected_server
trade_allowed
trade_expert_enabled
account_trade_mode_valid
margin_mode_known
leverage_known
balance_fresh
equity_fresh
margin_fresh
free_margin_fresh
margin_level_safe
currency_known
not_investor_password_session
```

If the account appears read-only, disconnected, unauthorized, or mismatched, execution must block with a deterministic error.

### 13A.3 MT5 Symbol Validation Requirements

For every live command, the adapter/readiness service must validate:

```text
symbol_mapping_exists
broker_symbol_selected_or_selectable
symbol_info_available
symbol_trade_mode_allows_trade
symbol_session_is_open
quote_available
quote_fresh
spread_within_policy
volume_min
volume_max
volume_step
contract_size
point
digits
tick_size
tick_value
stops_level
freeze_level
filling_modes
order_modes
execution_mode
```

The broker symbol must be stored separately from the normalized HaruQuant symbol.

Example:

```text
normalized_symbol = XAUUSD
broker_symbol = XAUUSD.a
```

### 13A.4 MT5 Position Mode Requirements

The execution module must explicitly detect and handle MT5 account position mode.

Supported Phase 1 rule:

```text
Phase 1 production live: support MT5 hedging accounts first.
Netting accounts must be blocked unless explicitly enabled and tested.
```

If netting support is later added, it must have separate tests for:

- increasing a net position;
- reducing a net position;
- reversing a net position;
- closing partial volume;
- SL/TP modification on net position;
- reconciliation with position ticket behavior.

### 13A.5 MT5 Order Send Requirements

Every MT5 order send must include:

```text
client_order_id
idempotency_key
request_id
workflow_id
strategy_id
magic_number
account_alias
normalized_symbol
broker_symbol
order_side
order_type
volume
price optional
stop_loss optional
take_profit optional
deviation
filling_type
time_in_force
comment
```

The order comment must be structured and bounded to the MT5 comment length limit. It should contain a compact trace reference, not full payload data.

Recommended comment format:

```text
HQ|strategy_id|short_command_id|short_request_id
```

### 13A.5a MT5 Deviation and Slippage Control

MT5 `deviation` represents the maximum allowed slippage in points for market execution. The execution module must treat deviation as a risk-controlled field, not as a casual broker parameter.

Required rules:

- every market order must have an explicit `deviation_points` value, either from the execution plan or a deterministic account/symbol default;
- the requested deviation must not exceed `max_allowed_deviation_points` from the validated `RiskDecisionPackage` or execution policy;
- if the risk decision does not provide a deviation bound, execution must apply the stricter configured account/symbol default;
- widening deviation after risk approval is a material change and requires risk revalidation;
- deviation must be included in the audit pre-record, execution attempt, and receipt.

Failure cases:

```text
DEVIATION_LIMIT_EXCEEDED
DEVIATION_NOT_APPROVED
```

### 13A.5b MT5 Trailing Stop Scope

MT5 trailing stop support is **out of scope for Phase 1 production live execution**.

If a command requests broker-managed or terminal-managed trailing stops in Phase 1, the adapter must reject the command before broker send with:

```text
UNSUPPORTED_ORDER_TYPE
```

Future trailing-stop support must be implemented as a separate feature with:

- explicit strategy ownership;
- broker/terminal behavior documentation;
- restart behavior tests;
- reconciliation after terminal restart;
- tests proving the trailing mechanism cannot bypass risk limits.

### 13A.6 Magic Number and Ownership Requirements

Every strategy that can trade through MT5 must have a deterministic magic number assignment.

Required mapping fields:

```text
strategy_id
strategy_version optional
account_alias
broker
magic_number
comment_prefix
allowed_symbols
created_at
status
```

The system must prevent two active strategies on the same account from using the same magic number unless explicitly configured as a shared strategy group.

### 13A.7 MT5 Order Outcome Handling

The adapter must normalize MT5 outcomes into HaruQuant receipt statuses:

```text
accepted
placed
filled
partial
rejected
timeout
unknown_requires_reconciliation
failed_before_send
```

The adapter must never treat an unknown MT5 response as safe success. Unknown or timeout outcomes must trigger reconciliation before retry.

### 13A.8 MT5 Reconciliation Requirements

MT5 reconciliation must compare local records against:

- open orders;
- open positions;
- order history;
- deal history;
- account snapshot;
- symbol snapshot.

Required matching fields:

```text
account_login
broker_symbol
magic_number
order_ticket
position_ticket
deal_ticket
client_order_id/comment trace
volume
open_price
stop_loss
take_profit
commission
swap
profit
position_side
order_status
position_status
created_at/open_time
closed_at/close_time optional
```

Reconciliation must classify mismatches and decide whether to update local state, block future execution, create an incident, or trigger a kill switch.

### 13A.9 MT5 Latency and Freshness Thresholds

`ExecutionConfig` must define explicit MT5 thresholds:

```text
mt5_terminal_connect_timeout_seconds
mt5_order_send_timeout_seconds
mt5_account_snapshot_max_age_ms
mt5_symbol_snapshot_max_age_ms
mt5_quote_staleness_limit_ms
mt5_max_order_send_latency_ms
mt5_reconciliation_interval_seconds
mt5_max_reconciliation_delay_seconds
mt5_max_terminal_disconnect_seconds
```

If any critical threshold is exceeded, the readiness service must block live execution or move the system into degraded mode.

### 13A.10 MT5 Adapter Security Requirements

The MT5 adapter must not log:

- login password;
- raw credentials;
- full terminal path if considered sensitive;
- complete unredacted request payloads;
- account secrets;
- environment variables.

Account login may be logged only as an allowed operational identifier when configured, or otherwise partially redacted.

---

## 14. Idempotency and Duplicate Protection

Every broker-mutating command must have an idempotency key.

### 14.1 Idempotency Key Composition

Recommended fields:

```text
account_id
strategy_id
symbol
command_type
side
volume
price_or_market_marker
risk_decision_id
approval_id
request_id
```

### 14.2 Idempotency Behavior

| Situation | Required Behavior |
|---|---|
| New key | Allow command creation after validation. |
| Duplicate key, prior success | Return prior receipt, do not resend. |
| Duplicate key, prior sending/unknown | Block or reconcile before retry. |
| Duplicate key, prior failure before broker send | Allow controlled retry with same command. |
| Duplicate key, prior broker timeout | Reconcile broker truth before retry. |
| Duplicate submit for partially filled order | Do not resend. Return the latest receipt and cumulative fill state. |
| Duplicate modify with identical parameters | Return the prior successful modify receipt. |
| Duplicate modify with different parameters | Block with `IDEMPOTENCY_KEY_MISMATCH`; require a new command, new risk validation where material, and new approval where required. |
| Duplicate cancel for already-cancelled order | Return prior cancel receipt as successful idempotent replay. |
| Cancel remaining volume after partial fill | Treat as a new side effect requiring a new command and new idempotency key. |

Idempotency validation must compare the full command fingerprint, not only the idempotency key string. The fingerprint must include command type, account, strategy, symbol, side where relevant, volume, price, stop-loss, take-profit, deviation, order ticket or position ticket where relevant, risk decision reference, and approval reference.

Any mismatch between a reused idempotency key and a materially different command must fail closed with `IDEMPOTENCY_KEY_MISMATCH`.

### 14.3 Partial-Fill Idempotency Rules

A partially filled command is active, not terminal. Duplicate requests for the original command must not send a new order. They must return the latest known `ExecutionReceipt` and current cumulative fill state.

If the caller wants to cancel the remaining volume, modify SL/TP for the remaining order, or submit a replacement order, that is a separate broker-mutating command with its own idempotency key, risk validation, approval requirements, attempt record, and receipt.

---

## 15. Attempts, Receipts, and Reconciliation

### 15.1 Attempt Lifecycle

```text
created -> sending -> sent -> acknowledged -> filled/partial/rejected/failed/timed_out -> reconciled
```

### 15.2 Receipt Rules

Every broker mutation must produce at least one normalized receipt or a structured failure receipt. For commands that can be partially filled, each broker-side fill event must generate an `ExecutionReceipt` linked to the same `command_id` and `attempt_id` where applicable.

Partial-fill receipt requirements:

```text
receipt_id
command_id
attempt_id
broker_order_ticket
broker_deal_ticket optional
broker_position_ticket optional
fill_event_sequence
event_filled_volume
cumulative_filled_volume
remaining_volume
event_price
cumulative_average_price
commission optional
swap optional
status = partially_filled | filled | cancelled | expired | rejected
created_at
```

The receipt's cumulative fields must represent broker truth after the latest known event. Agents and workflows must not infer cumulative fill state from raw broker events.

### 15.3 Reconciliation Rules

Reconciliation must run:

- after live broker send;
- after broker timeout;
- after startup;
- on scheduled intervals;
- before clearing kill switch;
- before resuming live strategy;
- before producing a live execution report;
- after every partial fill;
- after every partial close;
- after every cancel of remaining order volume.

For partial fills, reconciliation must compare:

- cumulative filled volume;
- remaining open volume;
- cumulative average price;
- broker order status;
- associated deal tickets;
- associated position tickets where available.

For partial closes, reconciliation must verify that:

- broker remaining position volume equals expected remaining volume;
- SL/TP are unchanged unless the command explicitly modified them;
- position ownership still matches strategy/magic-number rules;
- realized P&L, commission, and swap are captured where available.

If any required check cannot be proven, affected scope must enter `MANUAL_REVIEW_REQUIRED`.

### 15.4 Reconciliation Mismatch Classes

```text
local_order_missing_broker
broker_order_missing_local
local_position_missing_broker
broker_position_missing_local
volume_mismatch
price_mismatch
status_mismatch
duplicate_broker_order
orphan_broker_position
stale_local_state
```

Each mismatch must map to an action:

```text
ignore_with_reason
update_local_state
create_incident
block_execution
request_manual_review
trigger_kill_switch
```

---

## 16. Kill Switch Specification

### 16.1 Kill-Switch Scopes

```text
global
broker
account
strategy
symbol
workflow
```

### 16.2 Kill-Switch Actions

```text
block_new_orders
cancel_pending_orders
close_positions
reduce_exposure
pause_strategy
pause_all_strategies
require_manual_review
require_reenable_approval
```

### 16.2a Kill Switch Interaction with In-Flight Orders

A kill-switch activation may occur while a command is already in `SENT_TO_BROKER`, `BROKER_ACCEPTED`, `PARTIALLY_FILLED`, or `UNKNOWN_OUTCOME`. The execution module must not assume that blocking local state can stop a broker-side action already in flight.

Required behavior:

- commands not yet sent to broker must be blocked immediately;
- commands in `SENT_TO_BROKER` must wait for a short configured response timeout, then reconcile;
- commands in `UNKNOWN_OUTCOME` must not be retried or automatically cancelled;
- unknown outcomes during a kill-switch event must move to `MANUAL_REVIEW_REQUIRED` if reconciliation cannot prove broker truth;
- the system must not automatically send cancel or close commands for unknown outcomes unless policy explicitly permits emergency risk-reducing actions and broker truth is known enough to target the correct order/position;
- the audit trail must record `KILL_SWITCH_ACTIVE_DURING_FLIGHT`.

A kill switch may trigger follow-up risk-reducing commands such as cancel pending orders or close positions, but these must be new commands with their own approval/policy treatment where required.

### 16.3 Emergency Execution During Kill Switch

Emergency commands may run only when explicitly permitted by policy and must be restricted to reducing risk, not increasing exposure.

Allowed examples:

- cancel pending orders;
- close positions;
- reduce exposure.

Blocked examples:

- open new position;
- increase position size;
- resume strategy without approval;
- override kill switch by LLM instruction.

---

## 17. Live Runtime Engine

The live runtime engine is not the execution authority. It is an orchestrator.

### 17.1 Engine Responsibilities

The live engine may:

- subscribe to strategy signals;
- maintain runtime session state;
- route signals into execution requests;
- pause/resume strategies after policy approval;
- request readiness checks;
- submit commands to the gateway;
- consume receipts;
- trigger reconciliation;
- update dashboards and reports.

### 17.2 Engine Non-Responsibilities

The live engine must not:

- place broker orders directly;
- bypass readiness checks;
- bypass risk decisions;
- bypass approval checks;
- clear kill switches;
- silently retry unknown broker outcomes;
- mutate live state without audit.

---

## 18. Configuration and Secrets

### 18.1 Config Requirements

`ExecutionConfig` must include:

```text
schema_version
environment
execution_mode
broker_profiles
account_aliases
symbol_mappings
default_time_in_force
max_order_retry_count
broker_timeout_seconds
quote_staleness_limit_ms
max_allowed_spread_points
slippage_model
commission_model
reconciliation_interval_seconds
kill_switch_defaults
audit_enabled
```

### 18.2 Secret Handling

Secrets must be referenced, not stored directly in config objects that may be serialized.

Allowed:

```text
MT5_PASSWORD from environment or secret manager
CTRADER_CLIENT_SECRET from environment or secret manager
```

Not allowed:

```text
password="plain text" in committed config
password included in logs
password included in audit records
password included in status exports
```

### 18.3 Environment Modes

```text
local
paper
shadow
staging_live
production_live
```

Production live mode must require stricter gates than paper/shadow.

---


## 18A. MT5 Environment and Secret Requirements

Since live trading will run through MT5, the execution configuration must define an explicit MT5 broker profile.

### 18A.1 Required MT5 Environment Variables

Recommended environment variables:

```text
MT5_ENABLED=true
MT5_LOGIN=<account_login>
MT5_PASSWORD=<secret>
MT5_SERVER=<broker_server>
MT5_TERMINAL_PATH=<absolute_terminal_path>
MT5_ENVIRONMENT=demo | staging_live | production_live
MT5_ACCOUNT_ALIAS=<safe_alias>
MT5_DEFAULT_DEVIATION_POINTS=<integer>
MT5_ORDER_SEND_TIMEOUT_SECONDS=<integer>
MT5_MAGIC_NUMBER_NAMESPACE=<integer_prefix>
```

The document may reference variable names, but committed examples must not contain real production credentials.

### 18A.2 MT5 Production Live Activation Requirements

Production live mode may be enabled only when:

- `MT5_ENVIRONMENT=production_live` is explicit;
- account login and broker server match the approved live account profile;
- terminal path matches the approved runtime host profile;
- strategy has approved magic number assignment;
- risk policy is production-enabled;
- live approval workflow is enabled;
- kill-switch service is enabled;
- audit writer is enabled;
- startup reconciliation has passed;
- smoke test order flow has passed in staging/demo;
- manual emergency stop process is documented.

### 18A.3 Startup Reconciliation Requirement

Before the first live command after process start, reconnect, or deployment, the system must run startup reconciliation.

Startup reconciliation must verify:

- broker account identity;
- open MT5 positions;
- open MT5 orders;
- local command/attempt/receipt records;
- strategy ownership by magic number;
- orphan positions or unknown manual trades;
- kill-switch state;
- risk state.

If startup reconciliation finds unexplained live exposure, the system must block new live orders until manual review or approved recovery.

---

## 19. Observability, Logging, and Audit

### 19.1 Required Log Fields

Every important execution event must log:

```text
timestamp
level
request_id
workflow_id
command_id
attempt_id
strategy_id
account_alias
broker
symbol
event_type
status
error_code
execution_ms
```

Do not log:

- passwords;
- tokens;
- raw credentials;
- full account secrets;
- unredacted broker payloads;
- sensitive personal data.

### 19.2 Required Audit Events

```text
execution_request_created
execution_plan_created
readiness_check_completed
policy_check_completed
approval_validated
risk_decision_validated
kill_switch_checked
command_created
attempt_started
broker_send_started
broker_send_completed
receipt_created
reconciliation_completed
command_blocked
command_failed
kill_switch_activated
kill_switch_reenabled
strategy_paused
strategy_resumed
```

### 19.3 Audit Record Requirements

Every audit record must include:

```text
request_id
workflow_id
actor/source_agent
action
risk_level
approval_id if applicable
risk_decision_id if applicable
command_id if applicable
attempt_id if applicable
result
error_code if applicable
redacted payload reference
created_at
```

---

## 20. Error Code Standard

The module shall define deterministic execution error codes.

### 20.1 Common Execution Error Codes

```text
INVALID_INPUT
MISSING_REQUEST_ID
MISSING_WORKFLOW_ID
INVALID_EXECUTION_MODE
INVALID_ORDER_REQUEST
INVALID_ORDER_SIZE
INVALID_ORDER_PRICE
INVALID_STOPS
SYMBOL_NOT_TRADABLE
MARKET_CLOSED
QUOTE_STALE
SPREAD_TOO_HIGH
INSUFFICIENT_MARGIN
BROKER_UNAVAILABLE
BROKER_REJECTED_ORDER
BROKER_TIMEOUT
RISK_DECISION_REQUIRED
RISK_DECISION_REJECTED
RISK_DECISION_EXPIRED
APPROVAL_REQUIRED
APPROVAL_NOT_FOUND
APPROVAL_EXPIRED
APPROVAL_REVOKED
APPROVAL_SCOPE_MISMATCH
KILL_SWITCH_ACTIVE
IDEMPOTENCY_KEY_REQUIRED
DUPLICATE_COMMAND
RECONCILIATION_REQUIRED
RECONCILIATION_MISMATCH
AUDIT_WRITE_FAILED
PERMISSION_DENIED
TOOL_EXECUTION_FAILED
EXECUTION_STATE_TRANSITION_INVALID
IDEMPOTENCY_KEY_MISMATCH
KILL_SWITCH_ACTIVE_DURING_FLIGHT
UNSUPPORTED_ORDER_TYPE
UNSUPPORTED_TIME_IN_FORCE
DEVIATION_LIMIT_EXCEEDED
DEVIATION_NOT_APPROVED
MT5_NETTING_ACCOUNT_UNSUPPORTED
UNKNOWN_ERROR
```

### 20.2 Error Behavior

Every error must be:

- structured;
- deterministic;
- logged;
- auditable if related to live execution;
- safe to expose to agents without leaking secrets.

---


## 20A. MT5 Retcode and Error Mapping Requirements

The MT5 adapter must map broker-specific return codes and runtime failures into deterministic HaruQuant error codes.

### 20A.1 Required Mapping Categories

| MT5 Outcome Category | HaruQuant Error Code |
|---|---|
| terminal not initialized | MT5_TERMINAL_NOT_INITIALIZED |
| login failed | MT5_LOGIN_FAILED |
| account mismatch | MT5_ACCOUNT_MISMATCH |
| server mismatch | MT5_SERVER_MISMATCH |
| autotrading disabled | MT5_AUTOTRADING_DISABLED |
| market closed | MARKET_CLOSED |
| invalid symbol | SYMBOL_NOT_TRADABLE |
| symbol not selected | MT5_SYMBOL_NOT_SELECTED |
| invalid volume | INVALID_ORDER_SIZE |
| invalid price | INVALID_ORDER_PRICE |
| invalid stops | INVALID_STOPS |
| stop/freeze level violation | MT5_STOP_FREEZE_LEVEL_VIOLATION |
| unsupported filling mode | MT5_UNSUPPORTED_FILLING_MODE |
| requote | MT5_REQUOTE |
| price changed | MT5_PRICE_CHANGED |
| off quotes | MT5_OFF_QUOTES |
| insufficient margin | INSUFFICIENT_MARGIN |
| trade context busy | MT5_TRADE_CONTEXT_BUSY |
| timeout | BROKER_TIMEOUT |
| broker rejected | BROKER_REJECTED_ORDER |
| unknown broker result | BROKER_RESULT_UNKNOWN |
| duplicate command risk | DUPLICATE_COMMAND |
| reconciliation required | RECONCILIATION_REQUIRED |

### 20A.2 MT5 Unknown Outcome Rule

If MT5 returns a timeout, ambiguous result, missing ticket, or any response that does not prove the final broker state, the system must:

1. mark the receipt as `unknown_requires_reconciliation`;
2. block automatic retry;
3. run reconciliation against orders, deals, and positions;
4. return the reconciled result or require manual review.

### 20A.3 Retry Policy by Error Class

| Error Class | Retry Behavior |
|---|---|
| validation error | no retry |
| permission/risk/approval error | no retry |
| market closed | no retry until market state changes |
| quote stale | refresh quote once, then revalidate risk/readiness |
| requote/price changed | rebuild execution plan and revalidate risk if policy allows |
| trade context busy | bounded retry with jitter if no unknown broker result exists |
| timeout/unknown | no resend until reconciliation |
| insufficient margin | no retry without new risk decision |
| broker unavailable | reconnect and rerun readiness before retry |

---

## 21. Testing Specification

Coverage must remain above 80%, with higher expectations for critical paths.

### 21.1 Unit Tests

Required test paths:

```text
tests/unit/tools/execution/test_contracts.py
tests/unit/tools/execution/test_policy.py
tests/unit/tools/execution/test_readiness.py
tests/unit/tools/execution/test_planning.py
tests/unit/tools/execution/test_commands.py
tests/unit/tools/execution/test_gateway.py
tests/unit/tools/execution/test_attempts.py
tests/unit/tools/execution/test_receipts.py
tests/unit/tools/execution/test_reconciliation.py
tests/unit/tools/execution/test_kill_switch.py
tests/unit/tools/execution/test_broker_status.py
tests/unit/tools/execution/test_reporting.py
tests/unit/tools/execution/test_tools.py
```

### 21.2 Contract Tests

Test:

- valid order request;
- invalid order side;
- invalid volume;
- invalid stops;
- invalid execution mode;
- missing request_id;
- missing workflow_id;
- invalid approval reference;
- invalid risk decision reference;
- receipt schema;
- reconciliation schema.

### 21.3 Policy Tests

Test:

- live order blocked without approval;
- live order blocked with expired approval;
- live order blocked with scope mismatch;
- live order blocked with revoked approval;
- live order blocked without risk decision;
- live order blocked with rejected risk decision;
- live order blocked while kill switch active;
- emergency close allowed only when reducing risk;
- LLM/tool output cannot override deterministic policy.

### 21.4 Gateway Tests

Use mocked broker adapters. Test:

- successful broker order send;
- broker rejection;
- broker timeout;
- duplicate idempotency key;
- audit pre-record failure;
- receipt creation;
- reconciliation after send;
- no direct adapter mutation outside gateway.

### 21.5 Reconciliation Tests

Test:

- perfect match;
- missing local order;
- missing broker order;
- duplicate broker order;
- orphan broker position;
- volume mismatch;
- status mismatch;
- stale local state;
- reconciliation triggers incident;
- reconciliation blocks future live execution when required.

### 21.6 Kill-Switch Tests

Test:

- global kill switch blocks new orders;
- strategy kill switch blocks only matching strategy;
- symbol kill switch blocks only matching symbol;
- cancel orders allowed during emergency mode;
- close positions allowed during emergency mode;
- re-enable requires valid approval;
- re-enable requires reconciliation.

### 21.7 Security Tests

Test:

- secrets are redacted in logs;
- secrets are redacted in audit records;
- raw broker payloads are not exposed to agent response;
- malicious tool output cannot override policy;
- invalid broker profile does not leak credentials.

### 21.8 Usage Examples

Required usage examples:

```text
tests/usage/tools/execution/check_execution_readiness.py
tests/usage/tools/execution/build_execution_plan.py
tests/usage/tools/execution/submit_paper_order_request.py
tests/usage/tools/execution/submit_live_order_request.py
tests/usage/tools/execution/kill_switch_workflow.py
tests/usage/tools/execution/reconcile_execution_state.py
tests/usage/tools/execution/build_execution_report.py
```

---


### 21A. MT5-Specific Test Matrix

The MT5 adapter and live execution path must have tests that do not require real live broker credentials in CI. Use mocks, fakes, and recorded sanitized fixtures.

#### 21A.1 MT5 Unit Tests

Test:

- terminal initialization success/failure;
- login success/failure;
- account mismatch blocks execution;
- server mismatch blocks execution;
- autotrading disabled blocks execution;
- investor/read-only account blocks execution;
- symbol mapping success/failure;
- symbol visibility/select behavior;
- volume min/max/step validation;
- stop-level and freeze-level validation;
- filling-mode selection;
- magic-number assignment;
- structured comment generation;
- retcode mapping;
- secret redaction.

#### 21A.2 MT5 Gateway Tests

Test:

- successful live command through gateway with mocked MT5 adapter;
- direct adapter mutation outside gateway is not used by official tools;
- missing risk decision blocks before adapter call;
- expired risk decision blocks before adapter call;
- missing approval blocks before adapter call;
- kill switch blocks before adapter call;
- stale quote blocks before adapter call;
- duplicate idempotency key returns prior receipt or blocks safely;
- broker timeout creates unknown receipt and requires reconciliation.

#### 21A.3 MT5 Reconciliation Tests

Test:

- local order matches MT5 order;
- MT5 order missing locally;
- local order missing in MT5 but deal exists;
- open position without local command;
- manual trade detected by unknown magic number;
- volume mismatch;
- SL/TP mismatch;
- commission/swap/profit normalization;
- startup reconciliation blocks unexplained exposure;
- reconciliation permits resume only after clean state or approved manual resolution.

#### 21A.4 MT5 Staging/Live Acceptance Tests

Before production live activation, run a controlled staging/demo test plan:

- initialize terminal;
- validate account and server identity;
- validate symbol metadata for all approved symbols;
- submit a minimum-volume test order in demo/staging;
- modify SL/TP;
- close partial or full position depending on account mode;
- reconcile orders/deals/positions;
- activate kill switch and verify new orders block;
- re-enable after approval and reconciliation;
- verify audit records and secret redaction.

No production live account may be enabled until staging/demo acceptance passes.

---

## 22. Implementation Phases

### Phase 1 — Contracts and Errors

Deliverables:

- `contracts.py`
- `errors.py`
- contract tests

Exit criteria:

- all critical request/command/receipt/reconciliation models exist;
- invalid inputs fail deterministically;
- schemas are stable enough for tools and services.

### Phase 2 — Config, Broker Interfaces, and Mock Broker

Deliverables:

- `config.py`
- `brokers/base.py`
- `brokers/paper.py`
- mock broker fixtures

Exit criteria:

- broker read/mutation methods are separated;
- paper adapter works in tests;
- secrets are referenced safely.

### Phase 3 — Readiness and Planning

Deliverables:

- `readiness.py`
- `planning.py`
- readiness tests
- planning tests

Exit criteria:

- readiness report covers all blocker categories;
- execution plan includes cost/slippage/margin estimates;
- blockers prevent live progression.

### Phase 4 — Policy, Kill Switch, and Commands

Deliverables:

- `policy.py`
- `kill_switch.py`
- `commands.py`
- policy tests
- kill-switch tests

Exit criteria:

- approval-id-only validation is impossible;
- risk decision validation is required;
- kill-switch state blocks live commands;
- command creation binds idempotency key.

### Phase 5 — Gateway, Attempts, Receipts, Reconciliation

Deliverables:

- `gateway.py`
- `attempts.py`
- `receipts.py`
- `reconciliation.py`
- mocked live broker tests

Exit criteria:

- only gateway can mutate live broker adapter;
- attempts are created before send;
- receipts are created after send;
- reconciliation runs after live send;
- duplicate submissions are blocked or replayed safely.

### Phase 6 — Official Tools and Registry

Deliverables:

- official tool wrapper functions
- `__init__.py`
- `tests/unit/tools/execution/test_tools.py`
- usage examples

Exit criteria:

- agents import only from `tools.execution`;
- official tools return standard schema;
- critical tools are approval-gated;
- no official critical tool uses `**kwargs`.

### Phase 7 — Live Runtime and Shadow Runtime

Deliverables:

- `live/engine.py`
- `live/session.py`
- `shadow/engine.py`
- runtime tests

Exit criteria:

- live engine only orchestrates;
- live engine cannot bypass gateway;
- shadow mode produces comparable receipts without live mutation.

### Phase 8 — Monitoring, Reporting, and Operational Hardening

Deliverables:

- `monitoring.py`
- `reporting.py`
- operational health checks
- incident workflow tests

Exit criteria:

- execution status reports are available;
- stale-state and latency checks work;
- incidents are created for critical mismatches;
- production acceptance checklist passes.

---


### Phase 7 — MT5 Production Live Hardening

Deliverables:

- `brokers/mt5.py` production adapter;
- MT5 terminal lifecycle checks;
- MT5 account and symbol readiness checks;
- MT5 retcode mapping;
- MT5 position-mode handling;
- magic-number registry integration;
- MT5 startup reconciliation;
- MT5 staging/live acceptance suite.

Exit criteria:

- MT5 adapter passes unit and failure-path tests;
- staging/demo live-order lifecycle passes;
- unknown MT5 outcomes require reconciliation before retry;
- production live activation checklist passes;
- no direct MT5 mutation is available outside the gateway.


## 23. Production Acceptance Criteria

### 23.1 Architecture Acceptance

- [ ] Exactly one live broker mutation boundary exists.
- [ ] Official tools cannot bypass policy, readiness, idempotency, audit, or gateway.
- [ ] Live engine cannot call broker mutation methods directly.
- [ ] Broker adapters are internal and mockable.
- [ ] Paper, shadow, and live modes are explicitly separated.
- [ ] No large god file carries mixed responsibilities.

### 23.2 Tool Acceptance

- [ ] Every official tool is exported through `tools/execution/__init__.py`.
- [ ] Every official tool has typed parameters or a typed request model.
- [ ] Every official tool supports request tracing.
- [ ] Every official tool returns the standard schema.
- [ ] Every official tool has metadata and side-effect flags.
- [ ] Critical tools require approval.
- [ ] Critical tools fail closed.
- [ ] No official tool silently fails or returns `None`.

### 23.3 Live Safety Acceptance

- [ ] Live order submission requires valid risk decision.
- [ ] Live order submission requires valid approval.
- [ ] Live order submission requires kill switch clear state.
- [ ] Live order submission requires broker/account/symbol readiness.
- [ ] Live order submission requires idempotency key.
- [ ] Attempt record is created before broker send.
- [ ] Receipt is created after broker send.
- [ ] Reconciliation runs after broker send.
- [ ] Failures are auditable.

### 23.4 Testing Acceptance

- [ ] Unit tests exist for contracts, policy, readiness, planning, commands, gateway, attempts, receipts, reconciliation, kill switch, tools, and broker adapters.
- [ ] Contract tests validate all core schemas.
- [ ] Policy tests prove approval/risk/kill-switch cannot be bypassed.
- [ ] Broker tests use mocks and do not require live broker credentials.
- [ ] Security tests prove secret redaction.
- [ ] Failure-path tests cover broker timeout, rejection, stale quote, insufficient margin, duplicate command, expired approval, and reconciliation mismatch.
- [ ] Usage examples exist for official tools.
- [ ] Coverage is above 80%.

### 23.5 Operations Acceptance

- [ ] Logs include request_id and workflow_id.
- [ ] Audit records exist for all critical transitions.
- [ ] Secrets are never logged or serialized.
- [ ] Kill-switch activation and re-enable are auditable.
- [ ] Reconciliation report can be generated on demand.
- [ ] Execution report can be generated for paper, shadow, and live modes.

---


### 23.6 Risk Management Dependency Acceptance

- [ ] Live MT5 execution cannot run without a valid `RiskDecisionPackage`.
- [ ] Risk package scope must match account, broker, MT5 login, strategy, symbol, side, command type, and approved volume.
- [ ] Expired, stale, rejected, incomplete, or mismatched risk decisions block before broker adapter call.
- [ ] Required risk checks include per-trade risk, margin impact, drawdown, exposure, pending orders, correlation, news, weekend/overnight, and prop-firm constraints where applicable.
- [ ] Risk decision evidence references are auditable.
- [ ] Risk revalidation triggers are enforced before live MT5 send.

### 23.7 MT5 Production Live Acceptance

- [ ] MT5 terminal lifecycle checks pass.
- [ ] MT5 account login, server, environment, and trade permissions match the approved profile.
- [ ] MT5 autotrading and expert trading state are validated.
- [ ] MT5 symbol mapping, visibility, trade mode, volume limits, stops level, freeze level, and filling mode are validated.
- [ ] Hedging/netting account mode is detected and unsupported modes are blocked.
- [ ] Every MT5 command includes magic number, idempotency key, client order ID, request ID, workflow ID, and strategy ownership metadata.
- [ ] MT5 retcodes map to deterministic HaruQuant error codes.
- [ ] Timeout and unknown MT5 outcomes trigger reconciliation before retry.
- [ ] Startup reconciliation runs before first live command.
- [ ] Demo/staging live order lifecycle acceptance passes before production live activation.
- [ ] Secrets are redacted from logs, audit records, receipts, reports, and tool responses.



## 24A. Execution State Machine

### 24A.1 Purpose

The Execution Module shall implement a strict execution state machine for every broker-mutating command.

The state machine is required because live MT5 execution can produce uncertain intermediate outcomes, including rejected orders, accepted orders, delayed broker responses, partial execution, local timeout with broker-side success, and reconciliation mismatches.

No implementation may use ad hoc status strings outside this state machine without explicitly extending the contract version.

### 24A.2 Required States

Every execution command shall move through the following state model:

```text
CREATED
  -> VALIDATED
  -> RISK_APPROVED
  -> APPROVAL_CONFIRMED
  -> READINESS_PASSED
  -> ATTEMPT_CREATED
  -> SENT_TO_BROKER
  -> BROKER_ACCEPTED | BROKER_REJECTED | PARTIALLY_FILLED | UNKNOWN_OUTCOME
  -> RECONCILED
  -> COMPLETED | FAILED | CANCELLED | EXPIRED | MANUAL_REVIEW_REQUIRED
```

### 24A.3 State Definitions

| State | Meaning | Broker Mutation Allowed? |
|---|---|---:|
| `CREATED` | Command object exists but has not passed validation. | No |
| `VALIDATED` | Command schema, account scope, symbol scope, and required fields are valid. | No |
| `RISK_APPROVED` | A valid, unexpired, matching `RiskDecisionPackage` has been verified. | No |
| `APPROVAL_CONFIRMED` | Required human/system approval exists and matches command scope. | No |
| `READINESS_PASSED` | Kill switch, broker health, quote freshness, account, symbol, margin, and execution readiness gates passed. | No |
| `ATTEMPT_CREATED` | A durable attempt record exists before broker send. | No |
| `SENT_TO_BROKER` | The broker adapter call has been initiated. | Yes |
| `BROKER_ACCEPTED` | MT5 returned an accepted/success-equivalent result. | No additional mutation until reconciled |
| `BROKER_REJECTED` | MT5 returned a deterministic rejection/failure. | No |
| `PARTIALLY_FILLED` | Some requested volume has executed and remaining volume is still open or pending broker resolution. This is not terminal. | Yes, but only for risk-reducing actions on the remaining volume, such as cancel remainder or modify remaining SL/TP |
| `UNKNOWN_OUTCOME` | Local timeout, disconnect, ambiguous response, or process failure occurred after send was attempted. | No retry until reconciled |
| `RECONCILED` | Broker truth has been compared to local command/attempt/receipt records. | Depends on next action |
| `COMPLETED` | Command reached intended terminal state and broker truth matches local records. | No |
| `CANCELLED` | Remaining order volume was cancelled and broker truth matches local records. | No |
| `EXPIRED` | Order expired according to broker/time-in-force policy and broker truth matches local records. | No |
| `FAILED` | Command failed safely and no unresolved broker-side ambiguity remains. | No |
| `MANUAL_REVIEW_REQUIRED` | System cannot prove safe state automatically. Human review is required. | No new live mutation for affected scope |

### 24A.4 Transition Rules

The module shall enforce these transition rules:

1. A command must not skip required gates.
2. A command must not move to `SENT_TO_BROKER` unless a durable attempt record exists.
3. A command must not retry from `UNKNOWN_OUTCOME` until reconciliation proves whether the broker acted.
4. `MANUAL_REVIEW_REQUIRED` is terminal until a human/system operator resolves the condition.
5. `PARTIALLY_FILLED` is not terminal. It remains active until the command becomes fully filled, remaining volume is cancelled, expires, fails safely, or enters manual review.
6. Each partial fill must create a receipt and update cumulative filled volume and average price.
7. A command in `PARTIALLY_FILLED` must not be resent with the same idempotency key.
8. Cancelling remaining volume after partial fill is a separate command with a separate idempotency key.
9. `COMPLETED`, `CANCELLED`, `EXPIRED`, `FAILED`, and `MANUAL_REVIEW_REQUIRED` are terminal command states.
10. Any invalid transition shall return `EXECUTION_STATE_TRANSITION_INVALID` and emit an audit event.
11. State transitions shall be persisted and auditable.

### 24A.5 Required State Transition Record

Each transition shall store:

```json
{
  "command_id": "exec-cmd-0001",
  "attempt_id": "exec-attempt-0001",
  "from_state": "READINESS_PASSED",
  "to_state": "ATTEMPT_CREATED",
  "reason": "Durable attempt record created before broker send.",
  "request_id": "req-0001",
  "workflow_id": "wf-0001",
  "timestamp_utc": "2026-05-31T14:00:00Z",
  "actor": "execution_gateway",
  "evidence_reference": "audit-exec-0001"
}
```

---

## 24B. Account, Symbol, Strategy, Order, and Position Concurrency Locks

### 24B.1 Purpose

MT5 live broker mutation must be concurrency-safe. The module shall use deterministic locks to prevent duplicate, conflicting, or stale commands from mutating the same live account state at the same time.

### 24B.2 Required Lock Types

| Lock | Scope | Purpose |
|---|---|---|
| Account mutation lock | `broker + account_alias + account_login` | Prevent simultaneous live broker mutations that may conflict with MT5 trade context or account state. |
| Strategy-symbol lock | `broker + account_alias + strategy_id + symbol` | Prevent duplicate open/close/modify actions for the same strategy-symbol scope. |
| Position lock | `broker + account_alias + position_ticket` | Prevent concurrent close/modify/reduce operations on the same position. |
| Order lock | `broker + account_alias + order_ticket` | Prevent concurrent cancel/modify operations on the same pending order. |
| Kill-switch lock | `broker + account_alias` | Ensure kill-switch activation blocks new commands immediately and consistently. |

### 24B.3 Lock Rules

The module shall enforce:

1. One live broker-mutating command per account may enter `SENT_TO_BROKER` at a time unless a future implementation proves safe parallelism with broker-specific tests.
2. A strategy-symbol lock must be acquired before opening, closing, modifying, or cancelling any command for the same strategy and symbol.
3. A position lock must be acquired before any close, partial close, stop-loss update, take-profit update, or trailing-stop update.
4. An order lock must be acquired before modifying or cancelling pending orders.
5. Locks must have safe timeouts, ownership metadata, and recovery behavior.
6. Lock acquisition failure shall fail closed with `EXECUTION_LOCK_UNAVAILABLE`.
7. A stale lock recovery mechanism must exist, but stale lock override must emit an audit event and require operator approval in production live mode.

### 24B.4 Deadlock Prevention

When multiple locks are required, locks shall be acquired in this order:

```text
kill_switch -> account -> strategy_symbol -> position -> order
```

If a lower-priority lock cannot be acquired, all acquired locks shall be released safely and the command shall not proceed.

---

## 24C. Persistence and Storage Requirements

### 24C.1 Purpose

Logs are not enough for production live trading. Execution state must be durable, queryable, replayable, and reconcilable.

The module shall persist execution records before, during, and after broker mutation.

### 24C.2 Required Persistent Records

The implementation shall persist at minimum:

| Record | Required? | Purpose |
|---|---:|---|
| `ExecutionCommandRecord` | Yes | Canonical command requested by workflow/agent/system. |
| `ExecutionStateTransitionRecord` | Yes | Auditable lifecycle state transitions. |
| `ExecutionAttemptRecord` | Yes | Durable pre-send attempt record. |
| `ExecutionReceiptRecord` | Yes | Broker adapter result, accepted/rejected/unknown. |
| `BrokerTicketRecord` | Yes | MT5 order/deal/position ticket references. |
| `ReconciliationReportRecord` | Yes | Broker truth comparison after command, startup, and scheduled checks. |
| `RiskDecisionReferenceRecord` | Yes | Risk package identity, scope, version, expiry, and evidence references. |
| `ApprovalReferenceRecord` | Yes | Approval identity, class, scope, approver, expiry, and revocation status. |
| `KillSwitchEventRecord` | Yes | Activation, deactivation request, reason, scope, and actor. |
| `ManualInterventionRecord` | Yes | Human review queue, resolution, notes, and final disposition. |
| `BrokerHealthSnapshotRecord` | Yes | MT5 connectivity, account, symbol, and quote freshness status. |
| `ExecutionMetricRecord` | Yes | Operational metrics for monitoring and SLOs. |

### 24C.3 Storage Rules

1. A command must be persisted before any broker adapter mutation.
2. An attempt must be persisted before `order_send`, close, cancel, or modify is called.
3. Receipts must store raw broker result fields after redaction and normalized HaruQuant status fields.
4. Broker tickets must be stored as first-class queryable references.
5. Reconciliation reports must be stored and linked to commands, attempts, receipts, and tickets.
6. Production live records must be append-first; destructive updates are not allowed except through controlled migration scripts.
7. Secrets, passwords, tokens, and full credential payloads must never be persisted.
8. Retention policy must be defined before live trading.

### 24C.4 Suggested Storage Backend

Phase 1 may use SQLite for local deterministic development and small-scale production if backups, locking, and recovery are clearly handled.

For higher-throughput or multi-process production, the module should support migration to PostgreSQL without changing public execution contracts.

### 24C.5 Required Indexes

The storage layer shall support lookup by:

- `request_id`;
- `workflow_id`;
- `command_id`;
- `attempt_id`;
- `idempotency_key`;
- `account_alias`;
- `broker_account_login`;
- `strategy_id`;
- `symbol`;
- `magic_number`;
- `order_ticket`;
- `deal_ticket`;
- `position_ticket`;
- `execution_state`;
- `created_at`.

---

## 24D. Manual Intervention Workflow

### 24D.1 Purpose

The module shall have a formal manual intervention workflow for situations where automated execution cannot prove account safety.

Manual intervention is not an optional operational convenience. It is a required production safety mechanism.

### 24D.2 Manual Review Triggers

The module shall enter `MANUAL_REVIEW_REQUIRED` when any of the following occur:

1. MT5 order send times out after the request may have reached the broker.
2. Local process crashes after broker send but before receipt persistence.
3. MT5 returns an ambiguous or unknown result.
4. Reconciliation detects a broker position that HaruQuant did not create and does not recognize.
5. HaruQuant expected no fill, but MT5 deal history shows a fill.
6. HaruQuant expected a fill, but no matching order/deal/position can be found.
7. Position volume, SL, TP, open price, symbol, or magic number does not match expected records.
8. Manual MT5 trade is detected on an account/symbol managed by HaruQuant.
9. Duplicate strategy ownership or magic-number collision is detected.
10. Kill switch activation races with an in-flight broker mutation.
11. Broker account mode differs from approved configuration.
12. Risk package or approval package is later discovered to be mismatched or expired at send time.

### 24D.3 Manual Review Behavior

When manual review is required, the module shall:

1. Block new live broker-mutating commands for the affected account, strategy, symbol, order, or position scope.
2. Emit a critical alert.
3. Persist a `ManualInterventionRecord`.
4. Include all linked evidence: command, attempt, receipt, broker tickets, reconciliation report, risk decision, approval, and logs.
5. Show recommended operator actions, but not perform them automatically unless separately approved.
6. Require explicit resolution before the affected scope is unblocked.

### 24D.4 Manual Review Resolution States

Manual review shall resolve into one of:

```text
RESOLVED_NO_ACTION_REQUIRED
RESOLVED_LOCAL_RECORD_CORRECTED
RESOLVED_BROKER_POSITION_CLOSED
RESOLVED_BROKER_ORDER_CANCELLED
RESOLVED_ACCEPTED_AS_MANUAL_TRADE
RESOLVED_ESCALATED_TO_INCIDENT
RESOLVED_SYSTEM_DISABLED
```

### 24D.5 Emergency Close-All

Emergency close-all is a critical action.

The module may support an emergency close-all tool or workflow, but it must:

- require explicit operator approval unless a pre-approved disaster policy exists;
- create a dedicated approval packet;
- use the same gateway and persistence chain;
- reconcile every affected position afterward;
- emit high-priority audit and incident records.

---

## 24E. Live Rollout Stages

### 24E.1 Purpose

Passing unit tests is not enough for live MT5 deployment. The module shall support a staged rollout path to prove behavior before production live use.

### 24E.2 Required Rollout Stages

| Stage | Name | Description | Exit Gate |
|---:|---|---|---|
| 0 | Paper Only | Run execution against deterministic paper broker only. | All command lifecycle tests pass. |
| 1 | Shadow Mode | Generate execution decisions and simulated commands while no broker mutation occurs. | Shadow decisions match intended strategy/risk behavior. |
| 2 | Demo MT5 | Execute on MT5 demo account with production-like symbol mappings. | Full lifecycle, reconciliation, and failure tests pass. |
| 3 | Micro-Lot Production | Execute minimum broker volume on production live account under strict limits. | No critical mismatch over approved observation period. |
| 4 | Limited Strategy Production | Enable selected strategies/symbols with capped risk and volume. | Risk, execution, reconciliation, and monitoring remain stable. |
| 5 | Full Approved Live Mode | Enable approved production live scope. | Formal signoff from owner/operator/risk approver. |

### 24E.3 Promotion Requirements

Promotion between stages shall require:

- test evidence;
- reconciliation evidence;
- risk gate evidence;
- approval evidence;
- incident review for any failures;
- rollback plan;
- owner signoff.

### 24E.4 Rollback Requirements

The module shall support rollback from any live stage to a safer stage.

Rollback shall not delete historical records and shall not silently alter open broker positions. If rollback occurs while positions exist, the system must either continue managing them safely or move them into manual review.

---

## 24F. MT5 Magic Number Registry

### 24F.1 Purpose

MT5 magic numbers are required for strategy ownership, reconciliation, and safe multi-strategy account management.

The project shall maintain a registry document:

```text
docs/execution/MT5_Magic_Number_Registry.md
```

or an equivalent structured registry table.

### 24F.2 Required Registry Fields

Each magic-number entry shall include:

| Field | Required | Description |
|---|---:|---|
| `magic_number` | Yes | Unique MT5 magic number. |
| `account_alias` | Yes | Approved HaruQuant account alias. |
| `broker` | Yes | Must be `mt5` for MT5 entries. |
| `broker_account_login` | Yes | Approved login/account reference. |
| `environment` | Yes | `demo`, `staging_live`, or `production_live`. |
| `strategy_id` | Yes | Strategy owner. |
| `symbol_scope` | Yes | Symbol or symbol group. |
| `command_scope` | Yes | Open, close, modify, cancel, or all. |
| `owner` | Yes | Human/system owner. |
| `status` | Yes | `reserved`, `active`, `deprecated`, or `blocked`. |
| `created_at` | Yes | Creation date. |
| `notes` | No | Operational notes. |

### 24F.3 Registry Rules

1. No production live MT5 command may be sent without a valid registry entry.
2. Magic numbers must be unique for the approved account/environment/strategy/symbol scope.
3. Collisions shall block live execution with `MAGIC_NUMBER_COLLISION`.
4. Deprecated or blocked magic numbers shall not be used for new live commands.
5. Registry changes shall be code-reviewed and auditable.

### 24F.4 Example Registry Entry

```markdown
| Magic | Account Alias | Environment | Strategy ID | Symbol Scope | Owner | Status |
|---:|---|---|---|---|---|---|
| 31001001 | pepperstone_live_primary | production_live | strategy_wpr_adr_v1 | XAUUSD | execution_owner | active |
```

---

## 24G. Runtime Deployment Assumptions

### 24G.1 MT5 Runtime Constraint

MT5 live trading requires a Windows terminal runtime or an approved Windows-hosted MT5 bridge.

The document assumes Phase 1 production live MT5 trading runs through one of these approved deployment models:

1. HaruQuant execution service runs directly on the Windows host where MT5 terminal is installed.
2. HaruQuant core services run elsewhere and call a controlled Windows MT5 bridge that owns the terminal connection.

Any other topology must be documented and approved before live trading.

### 24G.2 Required Deployment Assumptions

The implementation shall document:

- approved runtime operating system;
- MT5 terminal installation path;
- account environment: demo, staging live, production live;
- startup order;
- shutdown order;
- service restart behavior;
- terminal watchdog behavior;
- reconnect behavior;
- clock synchronization source;
- timezone source;
- MT5 auto-update policy;
- broker server name;
- credential source;
- log and audit storage paths;
- backup and restore procedure.

### 24G.3 Startup Order

Production startup shall follow:

```text
load config -> validate secrets -> initialize storage -> initialize audit writer -> initialize kill switch -> initialize MT5 terminal -> validate account -> validate symbols -> startup reconciliation -> enable command gateway
```

If any startup step fails, the command gateway shall remain disabled.

### 24G.4 Clock and Timezone Requirements

The runtime host clock shall be synchronized through an approved time source.

All persisted execution timestamps shall use UTC. Broker-local timestamps may be stored, but UTC shall be the canonical comparison and audit time.

### 24G.5 MT5 Auto-Update Policy

The module shall detect terminal restart or version change events. After any MT5 terminal update/restart, live execution shall remain disabled until account validation, symbol validation, readiness checks, and startup reconciliation pass again.

---

## 24H. Operations Runbooks

### 24H.1 Required Runbooks

Before production live activation, the following runbooks shall exist:

| Runbook | Required Purpose |
|---|---|
| `MT5_Disconnected_Runbook.md` | What to do when terminal/account disconnects. |
| `Broker_Order_Rejected_Runbook.md` | How to inspect and classify rejected broker orders. |
| `Unknown_Order_Outcome_Runbook.md` | What to do after timeout or ambiguous MT5 result. |
| `Reconciliation_Mismatch_Runbook.md` | How to resolve local vs broker state mismatch. |
| `Kill_Switch_Triggered_Runbook.md` | What to do when kill switch activates. |
| `Manual_Trade_Detected_Runbook.md` | How to handle trades placed outside HaruQuant. |
| `Account_Equity_Breach_Runbook.md` | What to do after drawdown/equity breach. |
| `Stale_Quote_Runbook.md` | What to do when quotes are stale or frozen. |
| `Terminal_Restart_Runbook.md` | Safe restart and revalidation procedure. |
| `Emergency_Close_All_Runbook.md` | Controlled emergency liquidation process. |

### 24H.2 Runbook Requirements

Each runbook shall include:

- trigger condition;
- severity level;
- immediate safety action;
- evidence to collect;
- commands/tools allowed;
- commands/tools forbidden;
- escalation owner;
- rollback or recovery steps;
- post-incident checklist;
- audit records expected.

### 24H.3 Runbook Testing

Critical runbooks shall be tested in demo/staging before production live activation.

At minimum, the following must be rehearsed:

- MT5 disconnect;
- unknown order outcome;
- reconciliation mismatch;
- kill switch trigger;
- emergency close-all dry run.

---

## 24I. Metrics, Alerts, and SLOs

### 24I.1 Required Metrics

The module shall emit the following metrics:

| Metric | Type | Purpose |
|---|---|---|
| `execution_command_count` | Counter | Total commands created. |
| `execution_attempt_count` | Counter | Total broker-send attempts. |
| `execution_success_count` | Counter | Successfully completed commands. |
| `execution_failure_count` | Counter | Failed commands. |
| `execution_success_rate` | Gauge | Success percentage over rolling window. |
| `broker_reject_count` | Counter | Broker deterministic rejections. |
| `broker_reject_rate` | Gauge | Broker reject rate over rolling window. |
| `unknown_outcome_count` | Counter | Ambiguous/unknown broker outcomes. |
| `reconciliation_mismatch_count` | Counter | Reconciliation mismatches detected. |
| `manual_review_required_count` | Counter | Manual review events. |
| `order_send_latency_ms` | Histogram | Broker send latency. |
| `order_send_latency_p95_ms` | Gauge | p95 broker send latency. |
| `quote_staleness_blocks` | Counter | Blocks due to stale quotes. |
| `kill_switch_activation_count` | Counter | Kill switch activations. |
| `mt5_disconnect_count` | Counter | Terminal/account disconnects. |
| `mt5_reconnect_count` | Counter | Reconnect events. |
| `startup_reconciliation_duration_ms` | Histogram | Startup reconciliation duration. |
| `approval_validation_failure_count` | Counter | Approval failures. |
| `risk_validation_failure_count` | Counter | Risk package failures. |
| `idempotency_duplicate_block_count` | Counter | Duplicate commands blocked. |

### 24I.2 Required Alert Thresholds

Production live mode shall alert on:

| Condition | Severity |
|---|---|
| `unknown_outcome_count > 0` | Critical |
| `reconciliation_mismatch_count > 0` | Critical |
| `manual_review_required_count > 0` | Critical |
| MT5 disconnected longer than configured threshold | Critical |
| kill switch activated | Critical |
| account equity/drawdown breach | Critical |
| order send p95 latency above configured threshold | Warning/Critical based on duration |
| quote stale blocks above configured threshold | Warning |
| broker reject rate above configured threshold | Warning/Critical based on count |
| approval validation failures repeated | Warning |
| risk validation failures repeated | Warning |
| storage/audit writer unavailable | Critical |

### 24I.3 Suggested Initial SLOs

Initial production SLOs shall be conservative:

| SLO | Target |
|---|---:|
| Command audit persistence before broker send | 100% |
| Unknown broker outcomes tolerated without alert | 0 |
| Unreconciled completed commands | 0 |
| Duplicate live orders from retry | 0 |
| Secret leakage in logs/audit/tool responses | 0 |
| Startup reconciliation before live enablement | 100% |
| Live commands without valid risk package | 0 |
| Live commands without approval when required | 0 |
| Live commands while kill switch active | 0 |

### 24I.4 Metrics Storage

Metrics may be stored in logs, JSONL, SQLite, Prometheus-compatible format, or another approved monitoring backend. The chosen backend must support incident review and trend analysis.

---

## 24J. CI/CD Quality Gates

### 24J.1 Purpose

No production execution implementation may merge or deploy without automated quality gates.

### 24J.2 Required Static Quality Gates

The repository shall pass:

```bash
black .
isort .
flake8 .
mypy api tools scripts
pytest
pytest --cov=tools --cov=api --cov=scripts --cov-fail-under=80
```

### 24J.3 Required Execution Module Tests

CI shall include tests for:

- execution command schema validation;
- execution state machine transitions;
- invalid transition rejection;
- idempotency key duplicate blocking;
- account lock acquisition and release;
- lock timeout and stale lock behavior;
- approval package validation;
- risk package validation;
- kill-switch blocking;
- readiness check blocking;
- MT5 terminal unavailable;
- MT5 account mismatch;
- MT5 symbol invalid/unavailable;
- MT5 invalid volume/min/max/step;
- MT5 invalid stops/freeze level;
- MT5 broker rejection retcode mapping;
- MT5 timeout/unknown outcome handling;
- no retry before reconciliation after unknown outcome;
- reconciliation success;
- reconciliation mismatch -> manual review;
- manual trade detection;
- startup reconciliation before gateway enablement;
- audit writer failure fail-closed behavior;
- secret redaction;
- official tool return schema compliance;
- official tool metadata compliance;
- usage examples import and run safely where applicable.

### 24J.4 Required Security and Safety Tests

The implementation shall test that:

1. no official tool can bypass `LiveBrokerCommandGateway`;
2. no live broker mutation can occur without persisted attempt record;
3. no live broker mutation can occur without valid risk package;
4. no live broker mutation can occur without approval where required;
5. no live broker mutation can occur while kill switch is active;
6. no secret-like values appear in logs, audit records, receipts, reports, or tool responses;
7. unsupported MT5 account modes fail closed;
8. duplicate idempotency keys cannot create duplicate broker orders;
9. LLM/agent output cannot override deterministic policy gates.

### 24J.5 Merge and Release Rules

A pull request touching production execution code shall not merge unless:

- all static quality gates pass;
- unit tests pass;
- failure-path tests pass;
- coverage remains at or above 80%;
- MT5 adapter tests pass using mocks/fakes;
- secret redaction tests pass;
- official AI tool schema tests pass;
- docs and usage examples are updated where public behavior changes;
- risk and execution acceptance checklists remain satisfied.

### 24J.6 Production Release Rules

A release to production live mode shall require:

- successful demo MT5 acceptance evidence;
- startup reconciliation evidence;
- manual intervention workflow evidence;
- rollback plan;
- emergency stop/kill-switch test evidence;
- owner signoff;
- risk owner signoff;
- execution owner signoff.


## 24. Final Build Rule

Build the new Execution Module from contracts and gates upward:

```text
contracts -> errors -> config -> broker interfaces -> readiness -> planning -> policy -> commands -> gateway -> attempts/receipts -> reconciliation -> official tools -> live runtime -> monitoring/reporting
```

Do not begin by rewriting the old `core.py`, `trading.py`, or `live/engine.py`.

The old module should be treated as:

```text
functionality inventory, not implementation template
```

The new module is complete only when live execution is impossible unless the deterministic execution chain says it is safe, approved, risk-valid, kill-switch-clear, broker-ready, idempotent, persisted, concurrency-safe, auditable, reconciled or reconcilable, observable, and operationally recoverable.


---

## Appendix A — Minimal RiskDecisionPackage Example

```json
{
  "schema_version": "1.0.0",
  "risk_decision_id": "risk-20260531-0001",
  "request_id": "req-20260531-0001",
  "workflow_id": "wf-live-exec-0001",
  "created_at": "2026-05-31T14:00:00Z",
  "expires_at": "2026-05-31T14:01:00Z",
  "producer": "risk_management_module",
  "producer_version": "1.0.0",
  "decision_status": "approved",
  "execution_scope": "production_live",
  "account_alias": "pepperstone_live_primary",
  "broker": "mt5",
  "broker_account_login": "***redacted-or-approved-id***",
  "strategy_id": "strategy_wpr_adr_v1",
  "symbol": "XAUUSD",
  "broker_symbol": "XAUUSD.a",
  "command_type": "submit_order",
  "side": "buy",
  "requested_volume": 0.01,
  "approved_max_volume": 0.01,
  "approved_max_risk_amount": 50.0,
  "approved_max_risk_percent": 0.5,
  "approved_stop_loss": 2310.5,
  "approved_take_profit": 2325.0,
  "portfolio_snapshot_id": "portfolio-snap-0001",
  "risk_snapshot_id": "risk-snap-0001",
  "risk_policy_version": "1.0.0",
  "approval_required": true,
  "required_approval_class": "live_trade",
  "risk_checks": [
    {
      "name": "per_trade_risk",
      "status": "pass",
      "severity": "info",
      "code": "RISK_WITHIN_LIMIT",
      "message": "Requested risk is within configured per-trade limit.",
      "measured_value": 0.42,
      "limit_value": 0.5,
      "evidence_reference": "risk-snap-0001"
    }
  ],
  "blockers": [],
  "warnings": [],
  "evidence_references": ["portfolio-snap-0001", "risk-snap-0001"],
  "metadata": {
    "read_only": true,
    "places_trade": false
  }
}
```

## Appendix B — MT5 Production Live Minimum Runtime Checklist

Before enabling production live MT5 trading, confirm:

- [ ] approved Windows/MT5 runtime host exists;
- [ ] MT5 terminal path is configured outside committed code;
- [ ] broker server and account login are approved;
- [ ] credentials are loaded from environment or secret manager;
- [ ] terminal can initialize, login, and fetch account info;
- [ ] all approved symbols pass metadata validation;
- [ ] magic numbers are assigned and collision-free;
- [ ] startup reconciliation is clean;
- [ ] kill switch is active/tested and can block new orders;
- [ ] approval service is reachable;
- [ ] risk module can produce valid RiskDecisionPackage;
- [ ] audit writer is enabled;
- [ ] demo/staging order lifecycle acceptance passed;
- [ ] emergency manual stop procedure is documented.
```


## Appendix C — Production Live Signoff Checklist

Before production live MT5 activation, all of the following must be true:

- [ ] v3 specification accepted as implementation baseline.
- [ ] Execution state machine implemented and tested.
- [ ] Concurrency locks implemented and tested.
- [ ] Persistent storage schema implemented and migration-tested.
- [ ] Manual intervention workflow implemented and rehearsed.
- [ ] MT5 magic-number registry exists and has no collisions.
- [ ] Runtime deployment assumptions documented and validated.
- [ ] Required operations runbooks exist.
- [ ] Critical runbooks rehearsed in demo/staging.
- [ ] Metrics and alerts are emitted and visible.
- [ ] CI/CD gates pass.
- [ ] MT5 demo order lifecycle test passes.
- [ ] Startup reconciliation is clean.
- [ ] Kill switch blocks new orders.
- [ ] Emergency close-all procedure is documented and dry-run tested.
- [ ] Risk Management Module produces valid `RiskDecisionPackage` records.
- [ ] Approval service produces valid approval records.
- [ ] No live command can bypass the gateway.
- [ ] No critical tool can place trades directly.
- [ ] Production live rollout stage is formally approved.

## Appendix D — Required Companion Documents

The following companion documents should exist before production live activation:

```text
docs/execution/MT5_Magic_Number_Registry.md
docs/execution/runbooks/MT5_Disconnected_Runbook.md
docs/execution/runbooks/Broker_Order_Rejected_Runbook.md
docs/execution/runbooks/Unknown_Order_Outcome_Runbook.md
docs/execution/runbooks/Reconciliation_Mismatch_Runbook.md
docs/execution/runbooks/Kill_Switch_Triggered_Runbook.md
docs/execution/runbooks/Manual_Trade_Detected_Runbook.md
docs/execution/runbooks/Account_Equity_Breach_Runbook.md
docs/execution/runbooks/Stale_Quote_Runbook.md
docs/execution/runbooks/Terminal_Restart_Runbook.md
docs/execution/runbooks/Emergency_Close_All_Runbook.md
docs/execution/Execution_Deployment_Runbook.md
docs/execution/Execution_Storage_Schema.md
docs/execution/Execution_Release_Checklist.md
```

---

## 24K. Final v4 Live Execution Hardening Requirements

### 24K.1 Partial Fill Handling

Partial fills are first-class execution events. The implementation must not treat partial fills as terminal success or terminal failure.

Required rules:

- `PARTIALLY_FILLED` is an explicit command state.
- Every partial fill produces a separate `ExecutionReceipt`.
- All receipts must link to the same original command and attempt where applicable.
- Cumulative filled volume and average price must be updated from broker truth.
- Reconciliation must verify cumulative volume, remaining volume, average price, order status, deal tickets, and position tickets.
- Duplicate requests for the original command must return the latest known cumulative receipt state and must not resend.
- Cancellation of remaining volume requires a separate command and idempotency key.

### 24K.2 Modify and Cancel Idempotency

Duplicate modification and cancellation requests must be deterministic.

Rules:

- duplicate `modify_order` with identical parameters returns the prior receipt;
- duplicate `modify_order` with different parameters fails with `IDEMPOTENCY_KEY_MISMATCH`;
- duplicate `cancel_order` for an already-cancelled order returns the prior receipt as success;
- cancellation of remaining volume after partial fill is a new command;
- no duplicate command may silently create a new broker mutation.

### 24K.3 Kill Switch and In-Flight Broker Commands

When kill switch activates, the system must separate commands not yet sent from commands already sent to MT5.

Rules:

- not-yet-sent commands are blocked;
- in-flight commands are not assumed cancelled;
- unknown outcomes are reconciled, not retried;
- unresolved in-flight outcomes become `MANUAL_REVIEW_REQUIRED`;
- automatic emergency actions may only reduce risk and must target known broker orders/positions;
- all such events must include `KILL_SWITCH_ACTIVE_DURING_FLIGHT` in logs/audit.

### 24K.4 Phase 1 Scope Clarifications

The following are explicit Phase 1 rules:

- MT5 hedging accounts are supported first.
- MT5 netting accounts are blocked with `MT5_NETTING_ACCOUNT_UNSUPPORTED` unless explicitly enabled in a later phase.
- MT5 trailing stops are out of scope and must fail with `UNSUPPORTED_ORDER_TYPE`.
- GTC is default order lifetime behavior.
- GTD support requires persisted `expires_at`, expiration monitoring, and reconciliation.
- Market-order deviation must be bounded by risk approval or account/symbol policy.

### 24K.5 Additional Production Acceptance Gate

Before live MT5 production activation, tests must prove:

- partial fill does not become terminal success prematurely;
- duplicate submit for partially filled order does not resend;
- duplicate modify with changed parameters is blocked;
- duplicate cancel of already-cancelled order is idempotent success;
- kill switch during `SENT_TO_BROKER` moves unresolved outcome to manual review;
- partial close reconciliation verifies remaining broker volume and SL/TP;
- unsupported netting account blocks before broker send;
- trailing stop request blocks before broker send;
- deviation above approved limit blocks before broker send;
- GTD expiration is persisted and reconciled if GTD is enabled.

---

## 24L. Institutional OMS, SOR, TCA, and Session-Recovery Requirements

### 24L.1 Scope and Phase Rule

The v5 institutional extensions are included so the new Execution Module can evolve into a full order-management and execution-quality subsystem without redesigning its core contracts later.

Phase 1 remains:

```text
MT5 direct execution only
single parent command only
no live child-order slicing
no live multi-broker routing
no live portfolio rebalance batch mutation unless explicitly enabled and tested
```

Unsupported institutional execution modes must fail closed with deterministic error codes. They must not silently fall back to direct execution unless the request explicitly permits fallback and the policy layer approves it.

### 24L.2 Smart Order Routing and Parent-Child Order Architecture

The execution architecture must support parent-child order decomposition as a future capability.

Definitions:

- **Parent command:** the original approved `ExecutionCommand` submitted by a strategy, workflow, portfolio manager, or agent.
- **Child order:** a broker-sendable slice derived from the parent command.
- **Algorithmic execution:** deterministic decomposition of a parent command into child orders according to a configured algorithm.
- **Venue selection:** choosing a broker/account/venue path when multiple live broker adapters are configured.

Required execution algorithms:

```python
class ExecutionAlgorithm(str, Enum):
    DIRECT = "direct"
    TWAP = "twap"
    VWAP = "vwap"
    ICEBERG = "iceberg"
    POV = "pov"
```

Phase 1 rule:

```text
Only ExecutionAlgorithm.DIRECT is live-enabled.
TWAP, VWAP, ICEBERG, POV, and multi-venue SOR must return UNSUPPORTED_EXECUTION_ALGORITHM unless explicitly enabled in a later implementation phase.
```

Required contract:

```python
@dataclass(frozen=True)
class AlgorithmicExecutionConfig:
    algorithm: ExecutionAlgorithm = ExecutionAlgorithm.DIRECT
    slice_volume: Decimal | None = None
    slice_interval_seconds: int = 60
    participation_rate_pct: Decimal | None = None
    max_participation_rate_pct: Decimal = Decimal("0.10")
    child_idempotency_strategy: str = "derived_from_parent"
    allow_direct_fallback: bool = False
```

Validation requirements:

- `DIRECT` must not create child orders.
- Any non-direct algorithm must require explicit policy approval.
- `slice_volume` must be positive when required by the algorithm.
- `participation_rate_pct` must be greater than zero and less than or equal to `max_participation_rate_pct` for POV.
- direct fallback must be disabled by default.
- any algorithmic execution request must be included in the `RiskDecisionPackage` scope.

### 24L.3 Child Order Contract

When parent-child execution is enabled, each child order must be persisted and traceable to its parent command.

Required contract:

```python
@dataclass(frozen=True)
class ChildOrderRecord:
    child_id: str
    parent_command_id: str
    parent_idempotency_key: str
    child_idempotency_key: str
    algorithm: ExecutionAlgorithm
    slice_number: int
    total_slices: int
    target_volume: Decimal
    filled_volume: Decimal
    remaining_volume: Decimal
    status: str
    broker_order_ticket: str | None
    broker_deal_tickets: list[str]
    created_at_utc: datetime
    updated_at_utc: datetime
```

Rules:

- parent commands keep the original `idempotency_key`.
- child idempotency keys must be deterministically derived from the parent key, slice number, and approved time bucket.
- child orders must not be generated by agents directly.
- parent cumulative filled volume equals the sum of reconciled child filled volumes.
- parent average fill price must be computed from broker-confirmed child fills.
- reconciliation must aggregate child receipts before marking the parent terminal.
- cancellation of remaining parent volume must create cancel commands for eligible open child orders.

### 24L.4 Execution Quality Metrics and TCA Bridge

Every execution receipt must carry execution-quality fields so the Analytics/TCA module can separate strategy alpha from execution drag.

Required contract:

```python
@dataclass(frozen=True)
class ExecutionQualityMetrics:
    estimated_slippage_bps: Decimal | None
    actual_slippage_bps: Decimal | None
    estimated_commission: Decimal | None
    actual_commission: Decimal | None
    estimated_spread_cost: Decimal | None
    actual_spread_cost: Decimal | None
    timing_cost_ms: int | None
    market_impact_bps: Decimal | None
    fill_rate_pct: Decimal | None
    requote_count: int = 0
    rejection_count: int = 0
    deviation_requested_points: int | None = None
    deviation_used_points: int | None = None
    benchmark_price_source: str | None = None
```

Receipt requirements:

- every `ExecutionReceipt` must include an `ExecutionQualityMetrics` object, even if fields are initially `None`.
- actual slippage must be calculated against a documented benchmark price.
- fill rate must equal `filled_volume / requested_volume`.
- actual commission and swap must come from broker truth when available.
- TCA fields must not be invented by agents.
- missing TCA evidence must be explicit and queryable.

Analytics bridge requirements:

- `tools.analytics` or the Analytics Module must consume execution receipts without direct broker access.
- execution-quality metrics must be persisted in a queryable table or record store.
- reporting must support grouping by strategy, symbol, account, broker, magic number, order type, and execution algorithm.

### 24L.5 Best-Execution Compliance Timestamps

Execution commands, attempts, receipts, audit records, and reports must use a unified timestamp contract.

Required contract:

```python
@dataclass(frozen=True)
class ExecutionTimestamps:
    decision_time_utc: datetime | None
    request_received_utc: datetime
    policy_validated_utc: datetime | None
    risk_validated_utc: datetime | None
    approval_validated_utc: datetime | None
    readiness_validated_utc: datetime | None
    attempt_created_utc: datetime | None
    gateway_sent_utc: datetime | None
    broker_ack_utc: datetime | None
    first_fill_utc: datetime | None
    final_fill_utc: datetime | None
    broker_state_observed_utc: datetime | None
    reconciliation_completed_utc: datetime | None
```

Rules:

- all timestamps must be UTC.
- timestamps must be monotonic where a deterministic local sequence exists.
- wall-clock timestamps must be paired with monotonic duration measurements where latency is calculated.
- missing timestamps must be `None`, not fabricated.
- every final receipt must include a latency breakdown.

Required derived metrics:

```text
request_to_policy_ms
policy_to_risk_ms
risk_to_approval_ms
approval_to_readiness_ms
readiness_to_send_ms
send_to_ack_ms
send_to_first_fill_ms
send_to_final_fill_ms
final_fill_to_reconciliation_ms
request_to_terminal_state_ms
```

### 24L.6 Atomic Batch Execution and Portfolio Rebalancing

The module must define portfolio-level batch execution contracts, even if Phase 1 blocks live batch mutation by default.

Required contract:

```python
@dataclass(frozen=True)
class AtomicBatchCommand:
    batch_id: str
    commands: list[ExecutionCommand]
    execution_mode: Literal["all_or_nothing", "compensated_rollback", "best_effort"]
    status: str = "pending"
    compensation_plan: dict[str, Any] | None = None
    approval_id: str | None = None
    risk_decision_id: str | None = None
```

Batch modes:

| Mode | Meaning | Phase 1 Live Default |
|---|---|---|
| `all_or_nothing` | If any child command fails pre-send validation, no command is sent. | Allowed only before broker mutation. |
| `compensated_rollback` | If a later leg fails after earlier fills, reduce/reverse earlier side effects using approved compensation commands. | Blocked unless explicitly approved and tested. |
| `best_effort` | Continue eligible commands even if some commands fail. | Blocked for live MT5 unless explicitly approved. |

Rules:

- batch commands must have a batch-level approval and risk decision.
- each child command must still have command-level validation.
- no child command may bypass the live gateway.
- compensation commands are broker-mutating commands and require their own audit trail.
- partial batch completion must be visible in monitoring and reporting.
- if compensation cannot be safely performed, the batch must enter `MANUAL_REVIEW_REQUIRED`.

### 24L.7 Modify Order Validation and Requote Policy

MT5 modifications must have explicit validation and retry behavior. The gateway must never blindly retry broker mutations.

Required enum:

```python
class RequotePolicy(str, Enum):
    FAIL_IMMEDIATELY = "fail_immediately"
    REBUILD_AND_RETRY = "rebuild_and_retry"
    ACCEPT_PARTIAL_MODIFY = "accept_partial_modify"
```

Required contract:

```python
@dataclass(frozen=True)
class ModifyOrderConfig:
    max_modification_retries: int = 1
    requote_policy: RequotePolicy = RequotePolicy.FAIL_IMMEDIATELY
    validate_stops_level_before_send: bool = True
    validate_freeze_level_before_send: bool = True
    min_price_change_points: int = 1
    max_allowed_deviation_points: int | None = None
```

Rules:

- `modify_order` must validate quote freshness before send.
- `modify_order` must validate `stops_level` and `freeze_level` before send.
- negligible modify requests below `min_price_change_points` must return idempotent no-op success if the broker state already matches the target within tolerance.
- `REBUILD_AND_RETRY` may retry at most once after refreshing quote, risk scope, and readiness evidence.
- `ACCEPT_PARTIAL_MODIFY` is blocked in Phase 1 unless explicitly approved because it may alter the intended risk geometry.
- any retry must use the same command lineage but a separate attempt record.

### 24L.8 Internal Execution Event Stream

The Execution Module must emit internal execution events so dashboards, agents, monitors, and workflows can observe state changes without polling the storage backend directly.

Required event types:

```python
class ExecutionEventType(str, Enum):
    COMMAND_CREATED = "command_created"
    POLICY_VALIDATED = "policy_validated"
    RISK_VALIDATED = "risk_validated"
    APPROVAL_VALIDATED = "approval_validated"
    READINESS_PASSED = "readiness_passed"
    ATTEMPT_STARTED = "attempt_started"
    GATEWAY_SENT = "gateway_sent"
    BROKER_ACK = "broker_ack"
    PARTIAL_FILL = "partial_fill"
    FILLED = "filled"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
    EXPIRED = "expired"
    UNKNOWN_OUTCOME = "unknown_outcome"
    RECONCILIATION_COMPLETE = "reconciliation_complete"
    MANUAL_REVIEW_REQUIRED = "manual_review_required"
    KILL_SWITCH_TRIGGERED = "kill_switch_triggered"
```

Required protocol:

```python
class ExecutionEventPublisher(Protocol):
    def publish(self, event_type: ExecutionEventType, payload: dict[str, Any]) -> None: ...
    def subscribe(self, scope: str, callback: Callable[[dict[str, Any]], None]) -> None: ...
```

Rules:

- Phase 1 may use an in-memory publisher.
- production may replace the publisher with Redis Streams, Kafka, a database outbox, or another durable event bus.
- event publication failure must not create an untracked broker mutation.
- broker mutation state must be persisted before event publication.
- event payloads must include `request_id`, `workflow_id`, `command_id`, `account_id`, `strategy_id`, `symbol`, state, timestamp, and redacted metadata.
- high-risk events must also be written to the audit log.

### 24L.9 Session Sequence Tracking and MT5 Reconnect Recovery

MT5 does not provide FIX-style sequence numbers, so the gateway must maintain a local command sequence to recover safely after reconnects and avoid duplicate sends.

Required contract:

```python
@dataclass
class SessionSequenceTracker:
    session_id: str
    next_local_command_seq: int
    in_flight_commands: dict[str, ExecutionCommand]
    started_at_utc: datetime
    last_reconciliation_utc: datetime | None = None

    def mark_sent(self, command_id: str) -> int: ...
    def mark_confirmed(self, command_id: str) -> None: ...
    def get_in_flight(self) -> list[str]: ...
```

Rules:

- every broker-mutating attempt must receive a local sequence number before send.
- sequence assignment must be persisted before broker mutation.
- on reconnect, the gateway must block new live sends until all in-flight commands are reconciled.
- in-flight commands must be compared against MT5 orders, deals, and positions.
- unresolved commands become `MANUAL_REVIEW_REQUIRED`.
- sequence counters must be session-scoped and audit-linked.
- local sequence numbers are not broker truth; they are recovery aids and must not replace reconciliation.

### 24L.10 Additional Error Codes

Add the following deterministic error codes:

```text
UNSUPPORTED_EXECUTION_ALGORITHM
CHILD_ORDER_NOT_SUPPORTED
CHILD_IDEMPOTENCY_DERIVATION_FAILED
BATCH_EXECUTION_UNSUPPORTED
BATCH_COMPENSATION_REQUIRED
BATCH_COMPENSATION_FAILED
REQUote_POLICY_UNSUPPORTED
MODIFY_REQUOTE_REVALIDATION_FAILED
EVENT_PUBLISH_FAILED
SESSION_RECOVERY_REQUIRED
SESSION_SEQUENCE_CONFLICT
IN_FLIGHT_RECONCILIATION_REQUIRED
EXECUTION_QUALITY_EVIDENCE_MISSING
TIMESTAMP_ORDER_INVALID
```

Canonical capitalization must be normalized during implementation. The preferred final constant is:

```text
REQUOTE_POLICY_UNSUPPORTED
```

### 24L.11 Additional Persistence Requirements

The storage schema must support the following additional records:

- `execution_child_orders`;
- `execution_quality_metrics`;
- `execution_timestamps`;
- `execution_batches`;
- `execution_batch_children`;
- `execution_compensation_records`;
- `execution_events` or durable outbox table;
- `execution_session_sequences`;
- `execution_reconnect_recovery_records`.

Every record must include:

- schema version;
- created timestamp;
- updated timestamp where mutable state is tracked;
- request/workflow identifiers where applicable;
- command or batch lineage;
- redaction-safe metadata.

### 24L.12 Additional Monitoring and Alerts

Add the following metrics:

```text
child_order_count
child_order_fill_rate_pct
parent_child_reconciliation_mismatch_count
execution_quality_missing_count
actual_slippage_bps_avg
actual_slippage_bps_p95
market_impact_bps_avg
requote_count
modify_requote_count
batch_execution_count
batch_compensation_required_count
batch_compensation_failed_count
execution_event_publish_failure_count
session_recovery_required_count
in_flight_reconciliation_required_count
latency_request_to_terminal_state_p95_ms
latency_send_to_ack_p95_ms
latency_send_to_first_fill_p95_ms
```

Critical alert conditions:

- any batch compensation failure;
- any unreconciled child-order mismatch;
- any session recovery failure;
- any in-flight command unresolved after reconnect;
- event publication repeatedly failing while live execution is enabled;
- TCA metrics missing for completed live executions beyond the allowed delay.

### 24L.13 Additional Test Matrix

Implementation must include tests for:

- non-direct algorithm rejected in Phase 1;
- child idempotency derivation is deterministic;
- parent filled volume equals sum of child filled volume;
- child reconciliation mismatch blocks parent completion;
- receipt includes `ExecutionQualityMetrics`;
- missing TCA evidence is explicit, not fabricated;
- timestamps are UTC and ordered correctly;
- latency breakdown is computed from timestamp fields;
- batch all-or-nothing blocks if any child fails pre-send validation;
- compensated rollback mode is blocked unless enabled;
- modify order validates stops level and freeze level;
- requote policy fails immediately by default;
- rebuild-and-retry performs at most one retry and creates a separate attempt;
- event publisher emits lifecycle events with required metadata;
- event publication failure is logged and audited;
- reconnect blocks new live sends until in-flight commands reconcile;
- unresolved in-flight command after reconnect enters manual review.

### 24L.14 Implementation Phase Integration

The v5 additions should be integrated as follows:

| Phase | Additions |
|---|---|
| Phase 1 — Contracts and Errors | `ExecutionAlgorithm`, `AlgorithmicExecutionConfig`, `ChildOrderRecord`, `ExecutionQualityMetrics`, `ExecutionTimestamps`, `RequotePolicy`, `ModifyOrderConfig`, `AtomicBatchCommand`, new error codes. |
| Phase 2 — Storage | child orders, timestamps, quality metrics, batch records, event/outbox records, session sequence records. |
| Phase 3 — Readiness and Policy | algorithm support checks, modify validation, batch policy, timestamp validation, TCA evidence requirement. |
| Phase 4 — Gateway | direct-only enforcement, session sequence tracking, reconnect recovery, event emission after persistence. |
| Phase 5 — Reconciliation | parent-child aggregation, in-flight recovery reconciliation, quality metrics finalization. |
| Phase 6 — Monitoring and Reporting | latency breakdowns, TCA bridge reporting, event-stream health, batch/child-order dashboards. |
| Phase 7+ — Institutional Execution | enable TWAP/VWAP/ICEBERG/POV, multi-broker SOR, compensated batch workflows after explicit tests and approvals. |

---

## Appendix E — v5 Institutional Production Signoff Addendum

Before enabling any v5 institutional feature beyond direct MT5 execution, confirm:

- [ ] non-direct algorithms are policy-gated and disabled by default;
- [ ] child-order persistence and parent-child reconciliation are implemented;
- [ ] execution-quality metrics are persisted for every receipt;
- [ ] TCA bridge consumer can read execution-quality records;
- [ ] timestamp contract is implemented and latency breakdowns are available;
- [ ] batch execution modes are explicitly configured and tested;
- [ ] compensation commands cannot bypass approval, risk, audit, or gateway checks;
- [ ] modify-order requote policy is deterministic and tested;
- [ ] execution event publisher is operational and redaction-safe;
- [ ] session sequence tracker blocks sends during recovery;
- [ ] reconnect recovery has been tested with in-flight command scenarios;
- [ ] dashboards can display parent/child status, TCA metrics, and manual-review states;
- [ ] all v5 error codes are documented and covered by tests.

## Appendix F — Additional v5 Companion Documents

The following companion documents should be created before institutional features are enabled:

```text
docs/execution/Algorithmic_Execution_Policy.md
docs/execution/Child_Order_Reconciliation_Standard.md
docs/execution/Execution_TCA_Bridge.md
docs/execution/Best_Execution_Timestamp_Standard.md
docs/execution/Batch_Execution_and_Compensation_Policy.md
docs/execution/Event_Stream_Contract.md
docs/execution/Session_Recovery_Runbook.md
docs/execution/Requote_and_Modify_Order_Policy.md
docs/execution/SOR_Rollout_Checklist.md
```


---

# v6.0.0 Update — MT5 Broker Adapter Implementation Readiness

## v6 Purpose

Version 5 defines the production-grade execution architecture, policy gates, safety model, OMS/SOR/TCA readiness, and MT5 live-trading boundary. Version 6 adds the missing implementation-level specification required before coding the concrete MT5 broker adapter, especially:

```text
tools/execution/brokers/mt5.py
```

The goal of this update is not to widen the scope of Phase 1. Phase 1 remains **MT5 direct execution only**. The goal is to make the MT5 adapter implementation deterministic, testable, auditable, and safe under the real behavior of the Python `MetaTrader5` package and the MT5 terminal runtime.

## 25. MT5 Broker Adapter Implementation Specification

### 25.1 Scope

This section defines the implementation contract for the MT5 broker adapter.

The MT5 adapter is responsible for translating HaruQuant execution commands into MT5 terminal API calls and translating MT5 responses back into HaruQuant execution receipts, broker state snapshots, reconciliation records, and deterministic error codes.

The adapter must not own strategy logic, portfolio decisions, risk approval, human approval, kill-switch policy, or agent reasoning. Those remain upstream deterministic gates.

### 25.2 Target Implementation Files

The first implementation pass should create or update these files:

```text
tools/execution/brokers/mt5.py
tools/execution/brokers/base.py
tools/execution/brokers/errors.py
tools/execution/brokers/models.py
tools/execution/brokers/symbols.py
tools/execution/brokers/supervision.py
tools/execution/brokers/reconciliation.py
tests/unit/tools/execution/brokers/test_mt5.py
tests/unit/tools/execution/brokers/test_mt5_symbol_cache.py
tests/unit/tools/execution/brokers/test_mt5_retcode_policy.py
tests/unit/tools/execution/brokers/test_mt5_precision.py
tests/unit/tools/execution/brokers/test_mt5_reconciliation.py
tests/usage/tools/execution/brokers/mt5.py
```

If implementation starts smaller, `mt5.py` may include private helper classes first, but those helpers must be split once the file becomes difficult to navigate.

### 25.3 External MT5 API Boundary

The adapter may use the official Python `MetaTrader5` package.

The adapter must treat the package as a **blocking, terminal-bound API**. Broker-mutating calls must never be called directly from async orchestration code without isolation.

Required MT5 API calls for Phase 1:

```text
initialize
shutdown
login
last_error
terminal_info
version
account_info
symbol_info
symbol_info_tick
symbol_select
symbols_get
order_check
order_calc_margin
order_send
orders_get
positions_get
history_orders_get
history_deals_get
```

The adapter must wrap all external MT5 calls behind a private boundary:

```python
class MT5ApiClient:
    ...
```

No production execution service, agent, workflow, or official tool may import or call `MetaTrader5` directly.

### 25.4 Bridge Protocol and Threading Model

#### 25.4.1 Runtime Model

The MT5 adapter must support a synchronous internal API and an async-safe external wrapper.

Required pattern:

```text
Execution workflow / gateway
    -> MT5BrokerAdapter
        -> MT5CallExecutor
            -> ThreadPoolExecutor(max_workers=1 per terminal session)
                -> MetaTrader5 package call
```

The default Phase 1 implementation must use **one worker thread per MT5 terminal session**.

Rationale:

- MT5 terminal state is account/session-bound.
- Broker mutation order must be deterministic.
- MT5 trade context can be sensitive to overlapping calls.
- Concurrency is already controlled by HaruQuant account/symbol/position locks.

#### 25.4.2 Thread Safety Rules

The adapter must enforce:

```text
one terminal session -> one MT5CallExecutor -> one worker thread
```

The adapter must not allow concurrent `order_send`, `order_check`, `initialize`, `shutdown`, `login`, or reconciliation-critical calls for the same terminal session.

Read-only calls such as `symbol_info`, `account_info`, and `positions_get` may still pass through the same executor in Phase 1. Multi-worker read pools are deferred until a measured bottleneck exists.

#### 25.4.3 Timeout Rules

Every MT5 call must have a HaruQuant timeout budget.

Recommended Phase 1 defaults:

| Operation | Timeout |
|---|---:|
| `initialize` | 15 seconds |
| `login` | 15 seconds |
| `account_info` | 3 seconds |
| `terminal_info` | 3 seconds |
| `symbol_info` | 3 seconds |
| `symbol_info_tick` | 2 seconds |
| `order_check` | 5 seconds |
| `order_calc_margin` | 5 seconds |
| `order_send` | 10 seconds |
| `positions_get` | 5 seconds |
| `orders_get` | 5 seconds |
| `history_orders_get` | 10 seconds |
| `history_deals_get` | 10 seconds |

If a timeout occurs on a broker-mutating call, the command must not be retried blindly. It must enter `UNKNOWN_OUTCOME` and then reconciliation must determine broker truth.

#### 25.4.4 Async Wrapper Rule

If the gateway is async, adapter methods may expose async functions such as:

```python
async def send_order(...): ...
```

but the actual MT5 call must execute inside the controlled executor.

Async wrappers must:

- preserve `request_id`;
- preserve `workflow_id`;
- preserve `command_id`;
- propagate cancellation carefully;
- never cancel a broker call already sent without marking the command as `UNKNOWN_OUTCOME`;
- persist the attempt before calling the broker.

### 25.5 MT5 Terminal Lifecycle

#### 25.5.1 Lifecycle States

The adapter must model terminal connection state explicitly:

```text
UNINITIALIZED
INITIALIZING
INITIALIZED
LOGGING_IN
CONNECTED
DEGRADED
DISCONNECTED
RECONNECTING
SHUTTING_DOWN
SHUTDOWN
FAILED
```

The gateway may only send broker-mutating commands when the adapter state is:

```text
CONNECTED
```

#### 25.5.2 Initialization Sequence

Startup must follow this order:

```text
1. Load sanitized MT5 configuration.
2. Validate terminal path when provided.
3. Create terminal session ID.
4. Initialize MetaTrader5 package.
5. Login if credentials are provided or required.
6. Read terminal_info().
7. Read account_info().
8. Validate expected account, server, and environment.
9. Validate autotrading/trade permission state where available.
10. Load and refresh symbol metadata.
11. Run startup reconciliation.
12. Mark adapter CONNECTED only after reconciliation passes.
```

#### 25.5.3 Shutdown Sequence

Shutdown must follow this order:

```text
1. Block new commands.
2. Wait for in-flight non-mutating calls to finish or timeout.
3. For in-flight broker-mutating calls, mark UNKNOWN_OUTCOME if completion is unknown.
4. Persist terminal session shutdown event.
5. Call mt5.shutdown().
6. Mark state SHUTDOWN.
```

The adapter must not call `shutdown()` while an `order_send()` attempt is actively in-flight unless the process is terminating and the command is persisted as `UNKNOWN_OUTCOME`.

### 25.6 Heartbeat, Keepalive, and Terminal Health

#### 25.6.1 Heartbeat Requirements

The adapter must run a heartbeat loop while enabled.

Recommended Phase 1 heartbeat interval:

```text
1 second in live mode
5 seconds in demo mode
10 seconds in paper/simulation-adapter mode
```

The heartbeat must collect:

- terminal state;
- account state;
- connection state;
- last successful MT5 call timestamp;
- last tick age for watched symbols;
- trade permission state where available;
- executor queue depth;
- in-flight command count.

#### 25.6.2 Health States

The adapter health state must be one of:

```text
HEALTHY
DEGRADED
UNHEALTHY
RECOVERING
MANUAL_REVIEW_REQUIRED
```

The adapter must enter `DEGRADED` if:

- heartbeat is late;
- quote freshness exceeds configured threshold;
- account info cannot be read but terminal remains reachable;
- symbol metadata refresh fails for non-active symbols;
- MT5 returns transient connectivity errors.

The adapter must enter `UNHEALTHY` if:

- terminal is disconnected beyond threshold;
- account mismatch is detected;
- trade permission is unavailable or disabled;
- repeated broker calls timeout;
- reconnect attempts exceed configured limit.

The adapter must enter `MANUAL_REVIEW_REQUIRED` if:

- startup reconciliation fails;
- post-reconnect reconciliation detects unknown broker state;
- in-flight command state cannot be matched to MT5 orders/deals/positions;
- manual trades are detected in a blocked scope;
- local state and broker state conflict materially.

### 25.7 Process Supervision and Terminal Recovery

#### 25.7.1 Supervision Responsibility

The MT5 adapter may monitor terminal health, but the process supervisor that starts or restarts the MT5 terminal should be a separate operational component.

Recommended separation:

```text
MT5BrokerAdapter
    observes terminal health and blocks unsafe execution

MT5TerminalSupervisor
    starts/restarts terminal process if configured and permitted
```

#### 25.7.2 Auto-Restart Policy

Auto-restart must be disabled by default in live production until proven in demo.

If enabled, auto-restart may only run when:

- no broker-mutating call is currently in-flight; or
- all in-flight commands have been persisted as `UNKNOWN_OUTCOME`;
- kill switch is active for the account or new sends are blocked;
- restart attempt is logged and audited;
- post-restart reconciliation runs before new sends.

#### 25.7.3 Reconnect Recovery Rule

After terminal reconnect or process restart:

```text
No new broker-mutating command may be sent until reconciliation completes.
```

The adapter must reconcile:

- persisted in-flight commands;
- recent orders;
- recent deals;
- current open positions;
- pending orders;
- command comments where available;
- magic numbers;
- symbol/volume/price/SL/TP state.

If any in-flight command cannot be resolved, the scope enters `MANUAL_REVIEW_REQUIRED`.

### 25.8 Dynamic Symbol and Contract Metadata Refresh

#### 25.8.1 Symbol Spec Cache

The MT5 adapter must maintain a symbol specification cache.

Each cached record must include:

```text
symbol
broker_symbol
visible
trade_mode
order_mode
filling_mode
expiration_mode
digits
point
trade_tick_size
trade_tick_value
contract_size
volume_min
volume_max
volume_step
volume_limit
spread
spread_float
stops_level
freeze_level
margin_initial
margin_maintenance
session_deals
session_buy_orders
session_sell_orders
session_open
session_close
last_refresh_utc
source_terminal_session_id
```

Fields unavailable from a broker must be represented explicitly as `None` and must trigger stricter readiness checks where needed.

#### 25.8.2 Refresh Triggers

The cache must refresh:

| Trigger | Requirement |
|---|---|
| Startup | Refresh all configured trade symbols before readiness can pass. |
| Timer | Refresh active symbols at least every 60 seconds in live mode. |
| Before order send | Refresh target symbol if cache age exceeds 5 seconds. |
| Before modify/cancel | Refresh target symbol if cache age exceeds 5 seconds. |
| After broker error | Refresh immediately on invalid price, invalid stops, invalid volume, invalid fill, market closed, off quotes, or requote. |
| Session boundary | Refresh at market/session open and close windows. |
| Symbol selection | Refresh after `symbol_select`. |
| Manual reload | Operator may request forced refresh. |

#### 25.8.3 Mid-Session Spec Change Policy

If symbol metadata changes while orders or positions are open:

- existing open positions remain valid unless broker state proves otherwise;
- new modifications must use the latest symbol spec;
- pending orders must be revalidated against new `stops_level`, `freeze_level`, `volume_step`, and filling mode;
- if a pending order becomes invalid under new metadata, it must be flagged for review or cancellation according to policy;
- the adapter must emit `SYMBOL_SPEC_CHANGED` event with old/new diff;
- if `volume_step`, `contract_size`, `tick_value`, or trade mode changes materially, new sends for that symbol must be blocked until readiness revalidates.

#### 25.8.4 Symbol Visibility Rule

If `symbol_info(symbol)` returns missing or invisible, the adapter may call `symbol_select(symbol, True)` only during readiness/initialization or explicit symbol preparation.

It must not silently select unknown symbols inside `order_send()`.

### 25.9 Precision, Point, Pip, Volume, and Price Normalization

#### 25.9.1 Decimal Rule

All internal HaruQuant execution quantities must use `Decimal` until the final MT5 request assembly boundary.

The adapter may convert to Python `float` only immediately before calling the MT5 package.

#### 25.9.2 Price Normalization

For an MT5 symbol:

```text
normalized_price = round(price, digits)
```

For stop loss and take profit:

```text
normalized_sl = round(sl, digits)
normalized_tp = round(tp, digits)
```

The adapter must validate that normalized SL/TP values still satisfy risk-approved distances and MT5 `stops_level` / `freeze_level` constraints.

#### 25.9.3 Volume Normalization

Volume must be normalized by broker `volume_step`:

```text
steps = floor((requested_volume - volume_min) / volume_step)
normalized_volume = volume_min + steps * volume_step
```

The normalized volume must satisfy:

```text
volume_min <= normalized_volume <= volume_max
normalized_volume % volume_step == 0
```

If normalization would reduce risk materially or make the order smaller than allowed strategy minimum, the adapter must reject with:

```text
MT5_VOLUME_NORMALIZATION_FAILED
```

The adapter must never round volume upward if that increases risk beyond the approved value.

#### 25.9.4 Point and Pip Definitions

The adapter must distinguish:

```text
point = MT5 symbol_info.point
pip = strategy/broker display concept, not a universal MT5 primitive
```

For most 5-digit FX symbols:

```text
pip = 10 * point
```

For most 3-digit JPY FX symbols:

```text
pip = 10 * point
```

For metals, indices, crypto, CFDs, and broker-specific symbols, pip is not assumed. The adapter must use `point`, `trade_tick_size`, and broker metadata.

#### 25.9.5 Deviation and Slippage Conversion

MT5 `deviation` must be represented in **points**.

If upstream risk or execution planning provides slippage in price units:

```text
deviation_points = ceil(abs(max_price_slippage) / point)
```

If upstream provides slippage in pips:

```text
deviation_points = ceil(abs(max_slippage_pips * pip_size) / point)
```

If upstream provides slippage in points:

```text
deviation_points = int(max_slippage_points)
```

The adapter must enforce:

```text
0 <= deviation_points <= max_allowed_deviation_points
```

If the requested or default deviation exceeds the risk-approved limit, reject with:

```text
DEVIATION_EXCEEDS_RISK_APPROVAL
```

### 25.10 MT5 Request Assembly Rules

#### 25.10.1 Common Request Fields

Every MT5 trade request must be assembled from a validated HaruQuant command and include:

```text
action
symbol
volume
type
price
sl
tp
deviation
magic
comment
type_time
type_filling
```

Additional fields may be required depending on operation:

```text
order
position
position_by
expiration
stoplimit
```

#### 25.10.2 Pre-Check Requirement

Before `order_send()` for new orders and modifications, the adapter must run:

```text
order_check(request)
```

where applicable and supported by the request type.

If `order_check()` fails, the adapter must not call `order_send()` unless a documented override exists for a known MT5 limitation. Any override must be high-risk, audited, and disabled by default.

#### 25.10.3 Margin Check Requirement

For new market or pending entry orders, the adapter must run:

```text
order_calc_margin(...)
```

and compare the result with risk-approved and account-available margin.

If `order_calc_margin()` returns `None`, the adapter must reject with:

```text
MT5_MARGIN_CALC_FAILED
```

unless the risk module has provided a stronger independent margin check and policy permits fallback.

### 25.11 Comment Encoding, Magic Number, and Idempotency Parsing

#### 25.11.1 MT5 Comment Constraint

MT5 comments must be treated as limited, broker-mutated, and non-authoritative.

The adapter must assume:

- the broker may truncate the comment;
- special characters may be stripped or altered;
- comments may be missing in history;
- comments alone are insufficient for reconciliation.

#### 25.11.2 Comment Format

The Phase 1 comment format must be compact and ASCII-safe:

```text
HQ1-{env}-{sid}-{cmd}-{chk}
```

Field meanings:

| Field | Meaning | Example |
|---|---|---|
| `HQ1` | HaruQuant comment schema version | `HQ1` |
| `env` | environment code | `L` live, `D` demo, `P` paper |
| `sid` | short strategy code | `S7F3A2` |
| `cmd` | short command hash | `C91B20` |
| `chk` | checksum | `A8D1` |

The full mapping must be persisted locally:

```text
comment_short -> command_id
comment_short -> idempotency_key
comment_short -> request_id
comment_short -> workflow_id
comment_short -> strategy_id
comment_short -> account_alias
```

#### 25.11.3 Hashing Rule

Short hashes must be deterministic:

```text
short_hash = uppercase(hex(blake2s(value, digest_size=3)))
checksum = uppercase(hex(blake2s(full_payload, digest_size=2)))
```

The adapter must not include raw account numbers, credentials, long strategy names, or full request IDs in the MT5 comment.

#### 25.11.4 Reconciliation Fallback Rule

If comment parsing fails, reconciliation must fall back to:

1. magic number;
2. symbol;
3. volume;
4. order/deal/position ticket;
5. execution time window;
6. price tolerance;
7. local in-flight command records;
8. strategy/account scope.

If reconciliation confidence remains below threshold, the command must enter `MANUAL_REVIEW_REQUIRED`.

### 25.12 Retcode-to-Action Decision Matrix

#### 25.12.1 Retcode Handling Principle

MT5 retcodes must map to deterministic HaruQuant actions, not just error codes.

Every retcode handling decision must specify:

```text
classification
retry_allowed
retry_count
requires_quote_refresh
requires_symbol_refresh
requires_risk_revalidation
requires_manual_review
state_transition
error_code
```

#### 25.12.2 Phase 1 Retcode Matrix

| MT5 condition / retcode family | HaruQuant classification | Deterministic action |
|---|---|---|
| Done / placed / accepted | Success or broker accepted | Persist receipt, update state, reconcile. |
| Partial fill | Partial success | Persist partial receipt, update cumulative fill, keep command active or reconcile remaining volume. |
| Requote / price changed | Transient price failure | Refresh quote and symbol; if `RequotePolicy.REBUILD_AND_RETRY`, rebuild request and retry once after risk/deviation revalidation; otherwise fail. |
| Off quotes / no prices | Market data unavailable | Do not retry immediately. Mark blocked or degraded; refresh quote; wait for heartbeat/session recovery. |
| Market closed | Session unavailable | Block until session open; no retry loop. |
| Invalid stops | Validation failure | Refresh symbol; re-check `stops_level` and `freeze_level`; reject unless a policy-approved rebuild exists. |
| Invalid volume | Validation failure | Refresh symbol spec; rerun volume normalization; reject if normalized volume no longer matches risk approval. |
| Invalid fill mode | Request construction failure | Try approved fallback filling mode only if symbol metadata allows and policy permits; otherwise reject. |
| No money / insufficient margin | Risk/margin failure | Reject, emit risk revalidation required. |
| Trade disabled | Broker/account/symbol blocked | Enter degraded/unhealthy; block account or symbol. |
| Trade context busy | Transient terminal failure | Backoff and retry up to configured count if command has not reached unknown outcome. |
| Too many requests | Rate limit | Backoff, reduce polling rate, do not spam broker. |
| Timeout / connection failure after send | Unknown outcome | Mark `UNKNOWN_OUTCOME`, run reconciliation, no blind retry. |
| Invalid order / position not found for modify/cancel | State mismatch | Reconcile order/position; if already terminal and idempotency matches, return prior receipt; otherwise manual review. |
| AutoTrading disabled / client disabled | Terminal policy blocked | Block live sends and alert operator. |
| Unknown retcode | Unknown broker response | Mark `UNKNOWN_OUTCOME` for mutating attempts, otherwise `BROKER_UNAVAILABLE` or `UNKNOWN_ERROR` by context. |

#### 25.12.3 Retry Limits

Default retry limits:

| Scenario | Default Retry |
|---|---:|
| Requote / price changed | 0 in Phase 1 live, 1 in demo if enabled |
| Trade context busy | 3 with exponential backoff |
| Too many requests | 3 with longer backoff and polling throttle |
| Invalid fill mode | 1 fallback mode attempt if explicitly allowed |
| Off quotes | 0 immediate retries |
| Timeout after order_send | 0 retries; reconcile only |
| Unknown retcode after mutation | 0 retries; reconcile only |

### 25.13 Modify Order Validation and Requote Policy

Before modifying SL/TP or pending-order price, the adapter must:

1. refresh quote if stale;
2. refresh symbol spec if stale;
3. validate `stops_level`;
4. validate `freeze_level`;
5. validate min price-change threshold;
6. validate risk decision scope and expiry;
7. validate idempotency fingerprint.

Negligible modify requests smaller than `min_price_change_points` must be treated as no-op success if they match the current broker state.

If broker returns requote or price changed on modify:

- default Phase 1 live behavior is fail immediately and reconcile;
- demo may allow one rebuild-and-retry if explicitly configured;
- any retry must revalidate risk and quote freshness.

### 25.14 Fill and Position Tracking Strategy

#### 25.14.1 No Native Python Push Assumption

The Phase 1 Python MT5 adapter must assume no reliable native push callback is available through the Python package.

Therefore, fill detection must use polling plus reconciliation.

#### 25.14.2 Polling Loops

The adapter must separate polling loops:

| Poller | Default Live Interval | Purpose |
|---|---:|---|
| In-flight command poller | 250 ms to 1 sec | Track just-sent orders and partial fills. |
| Active orders poller | 1 sec | Track pending orders. |
| Position poller | 1 sec | Track open position state. |
| History deals poller | 2 to 5 sec | Detect fills/deals after broker state changes. |
| Full reconciliation poller | 30 to 60 sec | Verify local vs broker state. |
| Heartbeat poller | 1 sec | Terminal/account health. |

Polling intervals must be configurable per environment.

#### 25.14.3 Backoff Rules

If MT5 returns rate-limit or too-many-request behavior:

- increase polling interval exponentially up to a configured maximum;
- prioritize in-flight command reconciliation over low-priority dashboard refresh;
- emit `MT5_POLLING_THROTTLED`;
- block new high-frequency polling features until health returns.

#### 25.14.4 Partial Fill Detection

A command may only move to `FILLED` when cumulative broker-confirmed filled volume equals requested volume within volume tolerance.

A command moves to `PARTIALLY_FILLED` when:

```text
0 < cumulative_filled_volume < requested_volume
```

The adapter must persist every observed deal contributing to cumulative fill.

#### 25.14.5 Terminal State Rule

The adapter must not mark a command terminal solely from the immediate `order_send()` response if the command creates an order or position that requires follow-up confirmation.

Terminal state requires:

- broker acceptance/rejection proof; and
- reconciliation proof where applicable.

### 25.15 Session Sequence Tracking for MT5

Although MT5 Python integration does not provide FIX-style sequence numbers, HaruQuant must maintain local sequence tracking.

Each terminal session must have:

```text
terminal_session_id
local_sequence_number
last_successful_heartbeat_seq
last_broker_mutation_seq
in_flight_command_ids
last_reconciled_deal_time_utc
last_reconciled_order_time_utc
```

Before every broker mutation:

1. allocate next local sequence number;
2. persist command attempt with sequence number;
3. send MT5 request;
4. persist response or unknown outcome;
5. reconcile sequence if needed.

On restart or reconnect:

- reload unresolved sequence records;
- reconcile broker state before new sends;
- mark unresolved gaps as manual review.

### 25.16 Account, Terminal, and Symbol Configuration

#### 25.16.1 Required Environment Variables

The MT5 adapter must load configuration from environment or settings, never hardcoded values.

Required Phase 1 variables:

```text
MT5_ENABLED
MT5_LOGIN
MT5_PASSWORD
MT5_SERVER
MT5_TERMINAL_PATH
MT5_ENVIRONMENT
MT5_ACCOUNT_ALIAS
MT5_EXPECTED_CURRENCY
MT5_EXPECTED_MODE
MT5_MAGIC_REGISTRY_PATH
MT5_MAX_ORDER_SEND_TIMEOUT_SECONDS
MT5_HEARTBEAT_INTERVAL_SECONDS
MT5_SYMBOL_REFRESH_SECONDS
MT5_RECONCILIATION_INTERVAL_SECONDS
```

Secrets must be redacted in logs and audit records.

#### 25.16.2 Account Validation

On startup, the adapter must verify:

- account login matches expected login;
- server matches expected server;
- environment matches expected demo/live configuration;
- account currency matches expected currency if configured;
- trade mode is compatible;
- margin mode is known;
- leverage is known;
- balance/equity/free margin are available;
- account is not connected with investor/read-only permissions.

If validation fails, adapter state must be `FAILED` or `UNHEALTHY` and live sends must be blocked.

### 25.17 MT5 Adapter Error Codes

Add these implementation-specific error codes:

```text
MT5_INITIALIZE_FAILED
MT5_LOGIN_FAILED
MT5_SHUTDOWN_FAILED
MT5_TERMINAL_UNAVAILABLE
MT5_TERMINAL_DISCONNECTED
MT5_TERMINAL_NOT_TRADE_ALLOWED
MT5_ACCOUNT_MISMATCH
MT5_ACCOUNT_READ_ONLY
MT5_SYMBOL_NOT_FOUND
MT5_SYMBOL_NOT_VISIBLE
MT5_SYMBOL_SELECT_FAILED
MT5_SYMBOL_SPEC_STALE
MT5_SYMBOL_SPEC_CHANGED
MT5_VOLUME_NORMALIZATION_FAILED
MT5_PRICE_NORMALIZATION_FAILED
MT5_INVALID_FILLING_MODE
MT5_INVALID_EXPIRATION_MODE
MT5_ORDER_CHECK_FAILED
MT5_MARGIN_CALC_FAILED
MT5_RETCODE_REQUOTE
MT5_RETCODE_PRICE_CHANGED
MT5_RETCODE_OFF_QUOTES
MT5_RETCODE_MARKET_CLOSED
MT5_RETCODE_INVALID_STOPS
MT5_RETCODE_INVALID_VOLUME
MT5_RETCODE_NO_MONEY
MT5_RETCODE_TRADE_DISABLED
MT5_RETCODE_TRADE_CONTEXT_BUSY
MT5_RETCODE_TOO_MANY_REQUESTS
MT5_ORDER_SEND_TIMEOUT_UNKNOWN_OUTCOME
MT5_COMMENT_PARSE_FAILED
MT5_RECONCILIATION_CONFIDENCE_LOW
MT5_POLLING_THROTTLED
MT5_RECONNECT_RECONCILIATION_REQUIRED
MT5_SESSION_SEQUENCE_GAP
```

All errors must return the standard HaruQuant tool response schema when surfaced through official tools.

### 25.18 MT5 Adapter Testing Matrix

The MT5 adapter implementation is not complete until these tests exist.

#### 25.18.1 Unit Tests

Required unit tests:

- initialization success;
- initialization failure;
- login failure;
- account mismatch;
- read-only account detection;
- symbol not found;
- symbol selection failure;
- symbol spec refresh;
- mid-session symbol spec change;
- volume normalization;
- price normalization;
- deviation conversion from points;
- deviation conversion from price units;
- deviation risk-limit rejection;
- comment encoding within 64 characters;
- comment parsing success;
- malformed comment fallback;
- order_check failure blocks send;
- order_calc_margin failure blocks send;
- retcode requote action;
- retcode invalid stops action;
- retcode invalid fill fallback;
- retcode trade context busy backoff;
- order_send timeout produces unknown outcome;
- no blind retry after unknown outcome;
- partial fill polling updates cumulative volume;
- already-cancelled order idempotency;
- duplicate modify same fingerprint returns prior receipt;
- duplicate modify different fingerprint is blocked;
- restart requires reconciliation before new send;
- unresolved sequence gap blocks account;
- heartbeat degraded state;
- polling throttled state.

#### 25.18.2 Integration Tests With Mock MT5 Package

A fake MT5 module must simulate:

- terminal unavailable;
- terminal connected;
- account info changes;
- symbol spec changes;
- retcode responses;
- order/deal/position evolution;
- delayed fills;
- partial fills;
- timeout after send;
- history records appearing after delay;
- reconnect and recovery.

#### 25.18.3 Demo MT5 Validation Tests

Before live micro-lot rollout, run demo tests for:

- initialize/login/shutdown;
- symbol preparation;
- market order open;
- pending order place/cancel;
- SL/TP modify;
- partial close if broker/account supports it;
- rejected invalid stops;
- rejected invalid volume;
- terminal disconnect simulation;
- startup reconciliation;
- manual intervention workflow.

### 25.19 MT5 Adapter Acceptance Criteria

The MT5 adapter is implementation-ready only when:

- [ ] no production module imports `MetaTrader5` except the private adapter boundary;
- [ ] all broker calls are isolated through the single-session executor;
- [ ] all broker-mutating calls are persisted before send;
- [ ] every broker-mutating timeout becomes `UNKNOWN_OUTCOME`;
- [ ] startup reconciliation blocks new sends until complete;
- [ ] reconnect reconciliation blocks new sends until complete;
- [ ] symbol metadata cache supports refresh triggers and diff events;
- [ ] price, volume, point, pip, and deviation normalization are tested;
- [ ] MT5 comments fit inside the configured limit and are not authoritative;
- [ ] magic number plus local records remain the reconciliation source of truth;
- [ ] retcode handling is deterministic and tested;
- [ ] polling detects fills and partial fills;
- [ ] rate-limit backoff prevents excessive MT5 calls;
- [ ] terminal supervision is separated from broker logic;
- [ ] all MT5 error codes are documented;
- [ ] all tests pass with coverage above 80%;
- [ ] demo validation has passed before live micro-lot rollout.

## Appendix G — MT5 Broker Adapter Implementation Checklist

```text
[ ] Create private MT5ApiClient boundary.
[ ] Create MT5CallExecutor with one worker per terminal session.
[ ] Implement connection lifecycle state machine.
[ ] Implement heartbeat and health state tracking.
[ ] Implement startup account validation.
[ ] Implement symbol metadata cache.
[ ] Implement dynamic symbol refresh triggers.
[ ] Implement precision and volume normalization helpers.
[ ] Implement deviation conversion helpers.
[ ] Implement compact MT5 comment encoder/parser.
[ ] Implement magic-number lookup integration.
[ ] Implement MT5 request builder.
[ ] Implement order_check and margin pre-checks.
[ ] Implement retcode action matrix.
[ ] Implement no-blind-retry unknown outcome handling.
[ ] Implement polling-based fill tracker.
[ ] Implement partial-fill cumulative receipt updates.
[ ] Implement reconnect sequence tracker.
[ ] Implement terminal supervision hooks.
[ ] Implement reconciliation-first recovery.
[ ] Create fake MT5 module for tests.
[ ] Create demo validation script.
```

## Appendix H — Required MT5 Companion Document

Before implementing or merging `tools/execution/brokers/mt5.py`, create:

```text
docs/execution/MT5_Broker_Adapter_Implementation_Specification.md
```

That document should extract Section 25 into a standalone engineer-facing implementation spec and include:

- MT5 runtime assumptions;
- environment variables;
- adapter class diagram;
- method signatures;
- retcode matrix;
- polling strategy;
- reconciliation examples;
- fake MT5 test design;
- demo validation procedure;
- live rollout checklist.

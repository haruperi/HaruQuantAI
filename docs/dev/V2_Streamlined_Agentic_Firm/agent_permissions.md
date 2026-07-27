# HaruQuant Streamlined Agent Permissions Policy

**Document:** `agent_permissions.md`  
**Recommended path:** `docs/agentic_firm/agent_permissions.md`  
**Owner:** Human Board / Haruperi  
**System:** HaruQuant Streamlined Agentic Trading System  
**Policy version:** 2.0.0  
**Status:** Streamlined implementation baseline  
**Last updated:** 2026-05-24  
**Python enforcement:** `runtime/permissions.py`  
**Canonical tool location:** root-level `tools/` folder  

---

## 1. Purpose

This policy defines what each HaruQuant agent is allowed to do, what tools it may call, what actions require approval, and what actions are forbidden.

This version is aligned to the streamlined architecture and simplified implementation approach:

```text
agents/*.py
tools/*.py
runtime/permissions.py
workflows/*.py
tests/*.py
```

The policy is intentionally strict but implementation-friendly.

---

## 2. Core Permission Laws

### 2.1 Deny by Default

All tools and actions are denied unless explicitly allowed in `runtime/permissions.py`.

### 2.2 Agents Are Not Final Authorities

Agents may recommend, draft, explain, and request. They may not independently authorize:

- live trading
- risk threshold changes
- broker credential changes
- permission changes
- tool registry changes
- kill-switch resets
- audit deletion/mutation
- live allocation increases

### 2.3 Tools Are Permissioned Capabilities

The root `tools/` folder contains executable capabilities. Agents may only call tools assigned to them.

### 2.4 Tool Output Is Untrusted

Tool output must be validated before being passed to another tool, used for a controlled decision, or shown as evidence.

### 2.5 Human Approval Does Not Bypass RiskGovernor

Human approval authorizes a workflow or deployment stage. It does not override deterministic risk rejection.

---

## 3. Permission Classes

| Class | Meaning | Examples | Approval |
|---|---|---|---|
| `read_only` | Reads data/state only | `get_historical_ohlcv`, `read_strategy_spec` | none or audit |
| `write_safe` | Writes internal artifacts | `write_research_brief`, `create_strategy_spec` | audit required |
| `write_controlled` | Changes lifecycle or runs compute jobs | `run_backtest`, `start_paper_trading` | audit + policy |
| `critical` | Affects live capital, broker, risk, permissions, kill switch, audit integrity | `place_live_order`, `change_risk_thresholds` | strict approval |
| `forbidden` | Never allowed | `delete_or_mutate_audit_log`, `disable_risk_governor` | forbidden |

---

## 4. Approval Types

| Approval type | Meaning |
|---|---|
| `none` | No special approval beyond permission check |
| `audit_required` | Must write audit event |
| `risk_governor_required` | Requires deterministic risk approval |
| `human_required` | Requires Human Board approval |
| `human_and_risk_required` | Requires both Human Board and RiskGovernor |
| `forbidden` | Not allowed under any normal workflow |

---

## 5. Tool Catalog

### 5.1 Read-only tools

```text
read_constitution
read_risk_policy
read_agent_permissions
read_strategy_lifecycle_policy
list_strategies
read_strategy_spec
read_strategy_code
get_strategy_status
get_historical_ohlcv
get_tick_data
get_symbol_info
get_spread_snapshot
get_economic_calendar
get_news_context
get_account_snapshot
get_open_positions
get_pending_orders
get_backtest_result
get_analytics_summary
get_risk_snapshot
get_correlation_matrix
get_var_cvar_snapshot
read_audit_log
read_execution_log
read_cost_log
```

### 5.2 Write-safe tools

```text
write_research_brief
create_strategy_spec
update_strategy_spec_draft
save_strategy_code_draft
save_strategy_tests_draft
run_strategy_tests
run_linter
run_formatter
create_strategy_review
create_risk_memo
create_portfolio_memo
create_performance_report
create_board_pack
create_incident_report
create_cost_report
write_audit_event
```

### 5.3 Write-controlled tools

```text
submit_strategy_for_review
mark_strategy_review_passed
mark_strategy_review_failed
submit_strategy_for_backtest
run_backtest
run_optimization
run_robustness_test
run_statistical_validation
submit_strategy_for_robustness
request_admit_to_paper
start_paper_trading
pause_paper_strategy
retire_strategy
request_live_activation
request_allocation_change
request_risk_approval
place_paper_order
close_paper_position
```

### 5.4 Critical tools

```text
activate_live_trading_global
deactivate_live_trading_global
activate_live_strategy
deactivate_live_strategy
change_risk_thresholds
change_prop_firm_profile
change_agent_permissions
change_tool_registry
change_broker_credentials
connect_live_broker
disconnect_live_broker
place_live_order
close_live_position
cancel_live_order
emergency_flatten_all
trigger_kill_switch
reset_kill_switch
override_news_block
override_weekend_rule
```

### 5.5 Constitutionally forbidden tools

```text
delete_or_mutate_audit_log
delete_or_mutate_backtest_evidence
disable_audit_logger
disable_risk_governor
disable_kill_switch
```

---

## 6. Streamlined Agent Permission Profiles

### 6.1 Executive & Control

#### `ceo_agent`

Allowed:

```text
read_constitution
read_risk_policy
read_agent_permissions
read_strategy_lifecycle_policy
list_strategies
get_strategy_status
get_backtest_result
get_analytics_summary
get_risk_snapshot
create_board_pack
create_performance_report
create_portfolio_memo
create_risk_memo
request_admit_to_paper
request_live_activation
request_allocation_change
write_audit_event
```

Forbidden:

```text
place_live_order
place_paper_order
change_risk_thresholds
change_agent_permissions
change_tool_registry
change_broker_credentials
disable_risk_governor
disable_audit_logger
reset_kill_switch
```

#### `planner_agent`

Allowed:

```text
read_constitution
read_risk_policy
read_agent_permissions
read_strategy_lifecycle_policy
list_strategies
get_strategy_status
write_audit_event
```

Forbidden:

```text
all write_controlled tools
all critical tools
all forbidden tools
```

#### `control_plane`

Allowed:

```text
read_constitution
read_risk_policy
read_agent_permissions
read_strategy_lifecycle_policy
get_strategy_status
get_risk_snapshot
read_audit_log
write_audit_event
```

Special authority:

- May block actions.
- May validate permissions.
- May validate approval requirements.
- May not bypass policy.

---

### 6.2 Research Department

Research agents may read market/research data and write research briefs. They may not code, backtest, paper trade, live trade, or promote lifecycle state.

Agents:

```text
research_lead_agent
market_intelligence_agent
quant_research_agent
research_validator_agent
```

Allowed:

```text
get_historical_ohlcv
get_tick_data
get_symbol_info
get_spread_snapshot
get_economic_calendar
get_news_context
read_strategy_spec
get_backtest_result
get_analytics_summary
write_research_brief
write_audit_event
```

Additional for `research_validator_agent`:

```text
read_risk_policy
read_strategy_lifecycle_policy
```

Forbidden:

```text
save_strategy_code_draft
run_backtest
run_optimization
run_robustness_test
start_paper_trading
place_paper_order
place_live_order
activate_live_strategy
change_risk_thresholds
all critical tools
```

---

### 6.3 Strategy Development Department

#### `strategy_lead_agent` and `strategy_designer_agent`

Allowed:

```text
read_constitution
read_risk_policy
read_strategy_lifecycle_policy
get_historical_ohlcv
get_symbol_info
create_strategy_spec
update_strategy_spec_draft
submit_strategy_for_review
write_audit_event
```

Forbidden:

```text
save_strategy_code_draft
run_backtest
start_paper_trading
place_paper_order
place_live_order
activate_live_strategy
all critical tools
```

#### `strategy_engineer_agent`

Allowed:

```text
read_strategy_spec
read_strategy_code
save_strategy_code_draft
save_strategy_tests_draft
run_strategy_tests
run_linter
run_formatter
write_audit_event
```

Forbidden:

```text
run_backtest
place_paper_order
place_live_order
activate_live_strategy
change_risk_thresholds
change_broker_credentials
disable_audit_logger
disable_risk_governor
disable_kill_switch
```

#### `strategy_reviewer_agent`

Allowed:

```text
read_strategy_spec
read_strategy_code
get_historical_ohlcv
create_strategy_review
mark_strategy_review_passed
mark_strategy_review_failed
write_audit_event
```

Forbidden:

```text
save_strategy_code_draft
place_paper_order
place_live_order
activate_live_strategy
change_risk_thresholds
```

#### `strategy_librarian_agent`

Allowed:

```text
list_strategies
read_strategy_spec
read_strategy_code
get_strategy_status
create_strategy_spec
update_strategy_spec_draft
write_audit_event
```

Forbidden:

```text
activate_live_strategy
start_paper_trading
place_paper_order
place_live_order
change_risk_thresholds
delete_or_mutate_backtest_evidence
delete_or_mutate_audit_log
```

---

### 6.4 Simulation & Validation Department

Agents:

```text
simulation_lead_agent
backtest_analyst_agent
optimization_agent
robustness_validator_agent
evidence_packager_agent
```

Allowed by role:

- `simulation_lead_agent`:
  ```text
  read_strategy_spec
  read_strategy_code
  get_historical_ohlcv
  get_tick_data
  run_backtest
  run_optimization
  run_robustness_test
  run_statistical_validation
  submit_strategy_for_robustness
  get_backtest_result
  get_analytics_summary
  create_performance_report
  write_audit_event
  ```

- `backtest_analyst_agent`:
  ```text
  get_backtest_result
  get_analytics_summary
  read_strategy_spec
  create_performance_report
  write_audit_event
  ```

- `optimization_agent`:
  ```text
  read_strategy_spec
  read_strategy_code
  get_historical_ohlcv
  run_optimization
  get_backtest_result
  create_performance_report
  write_audit_event
  ```

- `robustness_validator_agent`:
  ```text
  read_strategy_spec
  read_strategy_code
  get_backtest_result
  get_historical_ohlcv
  run_robustness_test
  run_statistical_validation
  create_performance_report
  write_audit_event
  ```

- `evidence_packager_agent`:
  ```text
  get_backtest_result
  get_analytics_summary
  read_strategy_spec
  create_performance_report
  write_audit_event
  ```

Forbidden for all:

```text
place_paper_order
place_live_order
start_paper_trading
activate_live_strategy
change_risk_thresholds
delete_or_mutate_backtest_evidence
```

---

### 6.5 Risk & Portfolio Department

#### `risk_lead_agent`, `risk_auditor_agent`

Allowed:

```text
read_risk_policy
get_risk_snapshot
get_correlation_matrix
get_var_cvar_snapshot
get_account_snapshot
get_open_positions
get_backtest_result
create_risk_memo
write_audit_event
```

Forbidden:

```text
change_risk_thresholds
place_live_order
activate_live_strategy
override_news_block
reset_kill_switch
```

#### `risk_governor_agent`

Allowed:

```text
read_risk_policy
get_risk_snapshot
get_correlation_matrix
get_var_cvar_snapshot
get_account_snapshot
get_open_positions
get_pending_orders
get_symbol_info
get_spread_snapshot
get_economic_calendar
request_risk_approval
write_audit_event
trigger_kill_switch
```

Special authority:

- May approve/reject risk proposals deterministically.
- May trigger kill switch on critical breach.
- May not change risk thresholds.

Forbidden:

```text
change_risk_thresholds
place_live_order
reset_kill_switch
disable_kill_switch
disable_risk_governor
```

#### `portfolio_manager_agent`

Allowed:

```text
list_strategies
get_strategy_status
get_backtest_result
get_analytics_summary
get_risk_snapshot
get_correlation_matrix
create_portfolio_memo
request_admit_to_paper
request_live_activation
request_allocation_change
retire_strategy
write_audit_event
```

Forbidden:

```text
place_live_order
activate_live_strategy
change_risk_thresholds
change_broker_credentials
reset_kill_switch
```

#### `allocation_agent`

Allowed:

```text
get_account_snapshot
get_open_positions
get_risk_snapshot
get_correlation_matrix
get_var_cvar_snapshot
create_portfolio_memo
request_allocation_change
write_audit_event
```

Forbidden:

```text
place_live_order
activate_live_strategy
change_risk_thresholds
```

---

### 6.6 Execution Department

#### `execution_lead_agent`

Allowed:

```text
get_strategy_status
get_account_snapshot
get_open_positions
get_pending_orders
get_symbol_info
get_spread_snapshot
get_economic_calendar
request_risk_approval
create_incident_report
write_audit_event
```

Forbidden:

```text
place_live_order
place_paper_order
activate_live_strategy
change_risk_thresholds
reset_kill_switch
```

#### `execution_readiness_agent`

Allowed:

```text
get_strategy_status
get_account_snapshot
get_open_positions
get_pending_orders
get_symbol_info
get_spread_snapshot
get_economic_calendar
read_execution_log
write_audit_event
```

Forbidden:

```text
place_live_order
place_paper_order
activate_live_strategy
change_risk_thresholds
```

#### `paper_trading_agent`

Allowed:

```text
get_strategy_status
get_symbol_info
get_spread_snapshot
request_risk_approval
place_paper_order
close_paper_position
pause_paper_strategy
write_audit_event
```

Required:

- paper mode enabled
- strategy in `paper_trading`
- paper-mode risk check passed

Forbidden:

```text
place_live_order
activate_live_trading_global
activate_live_strategy
change_risk_thresholds
change_broker_credentials
```

#### `live_execution_agent`

Allowed:

```text
get_strategy_status
get_account_snapshot
get_open_positions
get_pending_orders
get_symbol_info
get_spread_snapshot
get_economic_calendar
request_risk_approval
place_live_order
close_live_position
cancel_live_order
write_audit_event
```

Required before any live mutation:

```text
global_live_trading_enabled
strategy_live_approved
human_board_approval_active
risk_governor_token_valid
kill_switch_healthy
audit_logger_healthy
broker_heartbeat_healthy
prop_firm_rules_clear
```

Forbidden:

```text
change_risk_thresholds
change_agent_permissions
change_tool_registry
change_broker_credentials
reset_kill_switch
override_news_block
override_weekend_rule
disable_audit_logger
disable_risk_governor
disable_kill_switch
```

#### `kill_switch_agent`

Allowed:

```text
get_account_snapshot
get_open_positions
get_pending_orders
get_risk_snapshot
read_execution_log
read_audit_log
trigger_kill_switch
deactivate_live_strategy
deactivate_live_trading_global
emergency_flatten_all
create_incident_report
write_audit_event
```

Forbidden:

```text
reset_kill_switch
activate_live_strategy
activate_live_trading_global
change_risk_thresholds
delete_or_mutate_audit_log
disable_kill_switch
```

---

### 6.7 Operations, Audit & Governance Department

#### `governance_agent`

Allowed:

```text
read_constitution
read_risk_policy
read_agent_permissions
read_strategy_lifecycle_policy
read_audit_log
create_board_pack
create_incident_report
write_audit_event
```

May request but not apply:

```text
change_agent_permissions
change_tool_registry
change_risk_thresholds
reset_kill_switch
```

#### `audit_agent`

Allowed:

```text
read_audit_log
read_execution_log
read_cost_log
get_strategy_status
get_risk_snapshot
get_account_snapshot
get_open_positions
create_incident_report
trigger_kill_switch
write_audit_event
```

Forbidden:

```text
delete_or_mutate_audit_log
delete_or_mutate_backtest_evidence
place_live_order
change_risk_thresholds
reset_kill_switch
change_agent_permissions
```

#### `performance_reporter_agent`

Allowed:

```text
get_backtest_result
get_analytics_summary
get_account_snapshot
get_open_positions
read_execution_log
read_audit_log
read_cost_log
create_performance_report
create_board_pack
write_audit_event
```

Forbidden:

```text
all execution tools
all lifecycle mutation tools
all critical tools
```

#### `cost_efficiency_agent`

Allowed:

```text
read_cost_log
read_audit_log
create_cost_report
create_performance_report
write_audit_event
```

Forbidden:

```text
all execution tools
all risk mutation tools
all permission mutation tools
all kill-switch mutation tools
```

---

## 7. Forbidden Tool Combinations

The following are forbidden even if individual tools are separately allowed:

1. Create strategy and approve same strategy.
2. Generate strategy code and approve same code.
3. Create trade proposal and execute same proposal without independent RiskGovernor gate.
4. Recommend risk threshold change and apply same change.
5. Place live orders and modify broker credentials.
6. Execute critical actions and disable/mutate audit.
7. Create evidence and delete/mutate evidence.
8. Promote lifecycle stage and hide failed evidence.

---

## 8. Emergency Disable Rules

An agent must be restricted, quarantined, or disabled if it:

1. Attempts to call forbidden tools.
2. Attempts live order without approval.
3. Attempts to bypass RiskGovernor.
4. Attempts to bypass audit logging.
5. Attempts to overwrite evidence.
6. Attempts to disable kill switch.
7. Attempts to access secrets.
8. Repeatedly makes invalid tool calls.
9. Creates workflow that skips lifecycle stages.
10. Follows prompt-injection instructions from untrusted content.

Disable levels:

| Level | Meaning |
|---|---|
| `level_1_warn` | Log warning |
| `level_2_restrict` | Restrict to read-only |
| `level_3_quarantine` | Stop active tasks and require review |
| `level_4_emergency_disable` | Disable agent and dependent workflows |
| `level_5_system_shutdown` | Disable live trading and trigger kill switch |

---

## 9. Policy-as-Code Requirement

`runtime/permissions.py` must implement:

- tool classes
- approval requirements
- allowed tools per agent
- forbidden tools per agent
- required runtime conditions
- permission checks
- forbidden-combination checks
- fail-closed behavior

The Python policy is the enforcement source. This Markdown file explains the policy.

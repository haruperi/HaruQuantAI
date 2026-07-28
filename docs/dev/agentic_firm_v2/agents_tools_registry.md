Below is the **complete tool inventory** I would create first for the streamlined HaruQuant agent system.

The goal is:

```text
Few agents.
Many deterministic tools.
Strict schemas.
No direct trading action without policy + approval.
```

---

# 1. Core Runtime Tools

Create these first because every agent depends on them.

| Tool                      | Purpose                                               | Priority |
| ------------------------- | ----------------------------------------------------- | -------: |
| `load_agent_manifest`     | Loads `.agent.md` files                               |        1 |
| `validate_agent_manifest` | Validates manifest structure, references, permissions |        1 |
| `load_instruction_files`  | Loads `.instructions.md` files                        |        1 |
| `load_skill_files`        | Loads `SKILL.md` files                                |        1 |
| `load_prompt_templates`   | Loads `.prompt.md` files                              |        1 |
| `resolve_agent_tools`     | Maps manifest tool names to Python callables          |        1 |
| `build_adk_agent`         | Creates Google ADK `Agent` from manifest              |        1 |
| `run_agent`               | Runs one agent with request/context/session           |        1 |
| `validate_agent_output`   | Validates agent output schema                         |        1 |
| `emit_audit_event`        | Writes structured audit event                         |        1 |
| `check_permissions`       | Checks whether agent can use a tool/action            |        1 |
| `check_policy_gate`       | Deterministic gate before sensitive actions           |        1 |
| `create_trace_id`         | Creates trace/session/workflow IDs                    |        1 |
| `log_tool_call`           | Logs tool usage and result metadata                   |        1 |
| `redact_sensitive_fields` | Removes secrets/private fields from logs              |        1 |

---

# 2. Shared Schema / Validation Tools

These are not trading-specific, but all departments need them.

| Tool                          | Purpose                                          |
| ----------------------------- | ------------------------------------------------ |
| `validate_input_schema`       | Validate incoming request payloads               |
| `validate_output_schema`      | Validate response payloads                       |
| `validate_evidence_pack`      | Check evidence completeness                      |
| `validate_handoff_payload`    | Check agent-to-agent handoff structure           |
| `validate_approval_packet`    | Check approval request completeness              |
| `validate_environment_mode`   | Confirm local/dev/test/staging/production mode   |
| `validate_data_freshness`     | Check whether evidence is stale                  |
| `validate_artifact_reference` | Check that referenced files/results exist        |
| `validate_registry_entry`     | Check agent/workflow/tool registry records       |
| `validate_required_fields`    | Generic missing-input checker                    |
| `validate_blocked_actions`    | Confirms agent did not attempt forbidden actions |

---

# 3. Research Department Tools

Used by:

```text
Research Lead Agent
Market Intelligence Agent
Quant Research Agent
Research Validator Agent
```

## 3.1 Market Data Tools

| Tool                        | Purpose                                          |
| --------------------------- | ------------------------------------------------ |
| `get_ohlcv_data`            | Retrieve OHLCV/OHLCVS data                       |
| `get_tick_data`             | Retrieve tick-level market data                  |
| `get_spread_data`           | Retrieve spread history                          |
| `get_symbol_metadata`       | Get pip size, tick value, lot step, margin rules |
| `get_trading_sessions`      | Return broker/session trading windows            |
| `get_market_hours`          | Market open/close status                         |
| `get_historical_volume`     | Volume/tick-volume context                       |
| `get_data_availability`     | Check available symbols/timeframes/date ranges   |
| `validate_ohlcv_data`       | Missing/duplicate/outlier checks                 |
| `resample_ohlcv`            | Convert M1 to M5/H1/D1 etc.                      |
| `align_multitimeframe_data` | Align lower/higher timeframe data                |

## 3.2 ForexFactory / External Context Tools

| Tool                                 | Purpose                                |
| ------------------------------------ | -------------------------------------- |
| `fetch_forexfactory_news`            | Pull news feed                         |
| `fetch_forexfactory_calendar`        | Pull economic calendar                 |
| `fetch_forexfactory_sentiment`       | Pull sentiment/trades snapshot         |
| `fetch_forexfactory_instrument_page` | Pull symbol-specific page, e.g. GBPJPY |
| `parse_news_items`                   | Normalize news items                   |
| `parse_calendar_events`              | Normalize calendar events              |
| `parse_sentiment_snapshot`           | Normalize sentiment positioning        |
| `filter_events_by_symbol`            | Keep only events relevant to symbol    |
| `classify_news_impact`               | Low/medium/high impact classification  |
| `create_news_blackout_windows`       | Create no-trade windows around news    |

## 3.3 Quant Research Tools

| Tool                               | Purpose                                      |
| ---------------------------------- | -------------------------------------------- |
| `calculate_returns`                | Bar/tick returns                             |
| `calculate_volatility`             | Rolling volatility                           |
| `calculate_atr`                    | ATR                                          |
| `calculate_adr`                    | ADR, especially ADR(10)                      |
| `calculate_spread_statistics`      | Avg/max/min spread by period/session         |
| `calculate_session_statistics`     | London/NY/Asia behavior                      |
| `calculate_seasonality_statistics` | Hour/day/month seasonality                   |
| `calculate_regime_features`        | Trend/range/volatility regime features       |
| `calculate_correlation_matrix`     | Symbol/strategy correlation                  |
| `detect_market_regime`             | Classify trend/mean-reversion/no-edge regime |
| `detect_trend_strength`            | ADX/slope/EMA structure                      |
| `detect_mean_reversion_conditions` | Range/oscillator/volatility contraction      |
| `detect_breakout_conditions`       | Donchian/range expansion/breakout features   |
| `generate_research_hypothesis`     | Deterministic hypothesis template builder    |
| `score_research_hypothesis`        | Rank idea quality before strategy creation   |

## 3.4 Research Validation Tools

| Tool                           | Purpose                           |
| ------------------------------ | --------------------------------- |
| `check_sample_size`            | Ensure enough observations        |
| `check_data_snooping_risk`     | Flag over-researched patterns     |
| `check_lookahead_bias_risk`    | Detect forward-looking fields     |
| `check_hypothesis_testability` | Confirm idea can become rules     |
| `check_contradictory_evidence` | Surface conflicting evidence      |
| `build_research_evidence_pack` | Final structured research handoff |

---

# 4. Strategy Development Tools

Used by:

```text
Strategy Lead Agent
Strategy Designer Agent
Strategy Engineer Agent
Strategy Reviewer Agent
Strategy Librarian Agent
```

## 4.1 Strategy Design Tools

| Tool                                | Purpose                                                 |
| ----------------------------------- | ------------------------------------------------------- |
| `generate_strategy_spec`            | Convert idea into structured `StrategySpec`             |
| `validate_strategy_spec`            | Check required fields                                   |
| `normalize_strategy_rules`          | Convert vague rules into deterministic rules            |
| `classify_strategy_type`            | Trend, mean reversion, breakout, grid, martingale, etc. |
| `detect_high_risk_trade_management` | Flag grid/martingale/averaging                          |
| `infer_required_data_columns`       | Determine OHLCVS, indicators, calendar, sentiment needs |
| `infer_required_indicators`         | Identify indicators required                            |
| `validate_entry_rules`              | Check entry logic completeness                          |
| `validate_exit_rules`               | Check exit logic completeness                           |
| `validate_stop_loss_rules`          | Check SL logic                                          |
| `validate_take_profit_rules`        | Check TP logic                                          |
| `validate_position_sizing_rules`    | Check sizing logic                                      |
| `validate_session_rules`            | Check trading session logic                             |
| `validate_news_rules`               | Check calendar/news blackout logic                      |
| `estimate_strategy_complexity`      | Simple/moderate/complex classification                  |
| `build_strategy_design_package`     | Final strategy handoff package                          |

## 4.2 Strategy Engineering Tools

| Tool                                   | Purpose                                   |
| -------------------------------------- | ----------------------------------------- |
| `generate_strategy_class`              | Generate Python strategy class            |
| `generate_strategy_config`             | Generate YAML/JSON config                 |
| `generate_strategy_tests`              | Generate unit tests                       |
| `generate_strategy_example_runner`     | Create example run script                 |
| `validate_strategy_code_structure`     | Check file/class naming                   |
| `validate_base_strategy_compatibility` | Ensure `BaseStrategy` compatibility       |
| `validate_on_bar_contract`             | Check `on_bar()` behavior                 |
| `validate_on_event_contract`           | Check complex event behavior              |
| `validate_signal_columns`              | Check `EntrySignal` / `ExitSignal` fields |
| `run_strategy_unit_tests`              | Run strategy-local tests                  |
| `format_generated_code`                | Black/Ruff formatting                     |
| `lint_generated_code`                  | Lint generated strategy code              |

## 4.3 Strategy Registry / Storage Tools

| Tool                             | Purpose                                                       |
| -------------------------------- | ------------------------------------------------------------- |
| `create_strategy_id`             | Generate unique strategy ID                                   |
| `save_strategy_spec`             | Persist strategy spec                                         |
| `save_strategy_code`             | Persist generated code                                        |
| `save_strategy_config`           | Persist config                                                |
| `register_strategy`              | Add strategy to registry                                      |
| `update_strategy_lifecycle`      | draft → backtest_candidate → paper_candidate → live_candidate |
| `get_strategy_registry_entry`    | Read existing registry record                                 |
| `version_strategy_artifact`      | Version specs/code/config                                     |
| `build_strategy_handoff_package` | Package for Simulation Department                             |

---

# 5. Simulation & Validation Tools

Used by:

```text
Simulation Lead Agent
Backtest Analyst Agent
Optimization Agent
Robustness Validator Agent
Evidence Packager Agent
```

## 5.1 Backtest Tools

| Tool                            | Purpose                                     |
| ------------------------------- | ------------------------------------------- |
| `run_backtest`                  | Run standard backtest                       |
| `run_portfolio_backtest`        | Multi-symbol / multi-strategy backtest      |
| `run_tick_backtest`             | Tick-level backtest                         |
| `run_bar_backtest`              | Bar-based backtest                          |
| `run_multitimeframe_backtest`   | MTF strategy test                           |
| `load_backtest_result`          | Load saved result                           |
| `validate_backtest_config`      | Check date range, data, costs, symbol, mode |
| `validate_backtest_result`      | Check result schema/completeness            |
| `save_backtest_result`          | Persist backtest output                     |
| `compare_backtest_to_benchmark` | Compare against benchmark strategies        |

## 5.2 Analytics Tools

| Tool                             | Purpose                                         |
| -------------------------------- | ----------------------------------------------- |
| `calculate_trade_metrics`        | Win rate, expectancy, PF, avg win/loss          |
| `calculate_return_metrics`       | CAGR, cumulative returns, daily/monthly returns |
| `calculate_drawdown_metrics`     | Max DD, duration, recovery                      |
| `calculate_ratio_metrics`        | Sharpe, Sortino, Omega, Calmar                  |
| `calculate_risk_metrics`         | VaR, CVaR, volatility, tail risk                |
| `calculate_efficiency_metrics`   | MAE/MFE, capture, trade efficiency              |
| `calculate_distribution_metrics` | Skew, kurtosis, streaks                         |
| `calculate_benchmark_metrics`    | Alpha, beta, R², benchmark delta                |
| `calculate_period_analysis`      | Hourly/daily/weekly/monthly analysis            |
| `calculate_long_short_split`     | Separate long vs short metrics                  |
| `calculate_session_performance`  | Asia/London/NY performance                      |
| `calculate_spread_cost_impact`   | Spread drag                                     |
| `calculate_slippage_impact`      | Slippage drag                                   |
| `calculate_commission_impact`    | Commission drag                                 |
| `build_backtest_report`          | Structured result report                        |

## 5.3 Optimization Tools

| Tool                            | Purpose                      |
| ------------------------------- | ---------------------------- |
| `run_parameter_sweep`           | Grid/random parameter search |
| `run_walk_forward_optimization` | WFO                          |
| `run_walk_forward_matrix`       | WFM                          |
| `compare_optimization_runs`     | Compare candidate params     |
| `calculate_parameter_stability` | Stability of params          |
| `detect_overfit_parameters`     | Overfit risk                 |
| `rank_parameter_sets`           | Rank optimization results    |
| `save_optimization_result`      | Persist result               |
| `build_optimization_report`     | Structured report            |

## 5.4 Robustness Tools

| Tool                           | Purpose                      |
| ------------------------------ | ---------------------------- |
| `run_spread_stress_test`       | Stress using wider spreads   |
| `run_slippage_stress_test`     | Stress slippage              |
| `run_commission_stress_test`   | Stress cost assumptions      |
| `run_randomize_trade_order_mc` | Monte Carlo shuffled trades  |
| `run_resample_trades_mc`       | Monte Carlo resampled trades |
| `run_skip_trades_mc`           | Random skipped trades        |
| `run_randomize_parameters_mc`  | Randomized parameters        |
| `run_randomize_history_mc`     | Randomized history           |
| `run_combined_monte_carlo`     | Combined MC stress           |
| `run_cross_market_test`        | Test related symbols         |
| `run_cross_timeframe_test`     | Test nearby timeframes       |
| `run_second_oos_test`          | Pre-development OOS          |
| `run_third_oos_test`           | Post-development OOS         |
| `calculate_robustness_score`   | Scorecard value              |
| `build_robustness_report`      | Structured robustness output |

## 5.5 Validation Evidence Tools

| Tool                                | Purpose                                      |
| ----------------------------------- | -------------------------------------------- |
| `build_validation_evidence_package` | Final validation package                     |
| `score_strategy_candidate`          | Score strategy against acceptance thresholds |
| `check_validation_exit_gate`        | Pass/fail/conditional                        |
| `generate_validation_summary`       | Human-readable report                        |
| `save_validation_package`           | Persist final package                        |

---

# 6. Risk & Portfolio Tools

Used by:

```text
Risk Lead Agent
Risk Governor Agent
Portfolio Manager Agent
Allocation Agent
Risk Auditor Agent
```

## 6.1 Risk Governor Tools

| Tool                             | Purpose                     |
| -------------------------------- | --------------------------- |
| `check_max_drawdown_limit`       | Account/strategy DD gate    |
| `check_daily_loss_limit`         | Daily loss gate             |
| `check_strategy_loss_limit`      | Strategy-specific loss gate |
| `check_portfolio_exposure_limit` | Total exposure gate         |
| `check_symbol_exposure_limit`    | Per-symbol exposure gate    |
| `check_currency_exposure_limit`  | FX currency basket exposure |
| `check_correlation_limit`        | Correlation gate            |
| `check_var_limit`                | VaR gate                    |
| `check_cvar_limit`               | CVaR gate                   |
| `check_leverage_limit`           | Leverage gate               |
| `check_margin_limit`             | Margin gate                 |
| `check_news_blackout`            | News blackout gate          |
| `check_spread_limit`             | Spread too high             |
| `check_slippage_limit`           | Slippage too high           |
| `check_trade_frequency_limit`    | Overtrading gate            |
| `check_kill_switch_state`        | Block if kill switch active |
| `run_risk_governor_checks`       | Master risk policy check    |

## 6.2 Portfolio Analytics Tools

| Tool                              | Purpose                          |
| --------------------------------- | -------------------------------- |
| `get_open_positions`              | Current positions                |
| `get_open_orders`                 | Current orders                   |
| `get_strategy_allocations`        | Current strategy weights         |
| `get_portfolio_equity_curve`      | Portfolio equity                 |
| `calculate_portfolio_returns`     | Portfolio returns                |
| `calculate_portfolio_volatility`  | Portfolio volatility             |
| `calculate_portfolio_correlation` | Correlation matrix               |
| `calculate_portfolio_var`         | Historical/Monte Carlo VaR       |
| `calculate_portfolio_cvar`        | CVaR                             |
| `calculate_risk_contribution`     | Per-strategy/symbol contribution |
| `calculate_margin_usage`          | Margin utilization               |
| `calculate_currency_exposure`     | USD/JPY/GBP/etc. exposure        |
| `detect_strategy_overlap`         | Duplicate/overlapping strategies |
| `detect_symbol_cluster_risk`      | Cluster exposure                 |
| `build_portfolio_risk_snapshot`   | Current portfolio risk package   |

## 6.3 Allocation Tools

| Tool                                  | Purpose                             |
| ------------------------------------- | ----------------------------------- |
| `calculate_fixed_fractional_size`     | Risk-based position sizing          |
| `calculate_volatility_adjusted_size`  | Vol-adjusted sizing                 |
| `calculate_risk_parity_weights`       | Equal risk contribution             |
| `calculate_correlation_adjusted_size` | Reduce size for correlated exposure |
| `calculate_margin_aware_size`         | Broker margin-aware sizing          |
| `calculate_cost_adjusted_size`        | Spread/slippage/cost-aware sizing   |
| `calculate_max_safe_position_size`    | Hard cap sizing                     |
| `propose_strategy_allocation`         | Strategy capital allocation         |
| `rebalance_strategy_allocations`      | Rebalance weights                   |
| `validate_allocation_proposal`        | Check allocation against policy     |

## 6.4 Portfolio Lifecycle Tools

| Tool                                 | Purpose                      |
| ------------------------------------ | ---------------------------- |
| `admit_strategy_to_portfolio`        | Add strategy candidate       |
| `promote_strategy_to_paper`          | Move to paper trading        |
| `promote_strategy_to_live_candidate` | Prepare live approval        |
| `suspend_strategy`                   | Temporarily pause            |
| `retire_strategy`                    | Remove from active portfolio |
| `demote_strategy_to_paper`           | Live → paper                 |
| `update_strategy_status`             | Update lifecycle             |
| `build_risk_decision_package`        | Final risk decision package  |

---

# 7. Execution Tools

Used by:

```text
Execution Lead Agent
Execution Readiness Agent
Paper Trading Agent
Live Execution Agent
Kill Switch Agent
```

## 7.1 Broker Connectivity Tools

| Tool                      | Purpose                           |
| ------------------------- | --------------------------------- |
| `check_broker_connection` | MT5/cTrader connection status     |
| `get_account_info`        | Balance, equity, margin, leverage |
| `get_symbol_info`         | Broker symbol metadata            |
| `get_current_bid_ask`     | Current price                     |
| `get_current_spread`      | Current spread                    |
| `get_trade_permissions`   | Is trading allowed                |
| `get_broker_time`         | Broker timestamp                  |
| `check_market_open`       | Symbol trading status             |
| `check_min_lot`           | Min volume                        |
| `check_max_lot`           | Max volume                        |
| `check_lot_step`          | Volume step                       |
| `check_stop_distance`     | Minimum stop distance             |
| `check_free_margin`       | Margin availability               |

## 7.2 Execution Readiness Tools

| Tool                               | Purpose                         |
| ---------------------------------- | ------------------------------- |
| `run_execution_readiness_check`    | Master pre-execution check      |
| `validate_order_request`           | Validate proposed order         |
| `validate_strategy_runtime_config` | Check strategy config           |
| `validate_broker_symbol_mapping`   | Internal symbol → broker symbol |
| `validate_execution_environment`   | Paper/live/test mode            |
| `validate_order_size`              | Volume validity                 |
| `validate_order_price`             | Price validity                  |
| `validate_stop_loss_take_profit`   | Broker-valid SL/TP              |
| `estimate_transaction_cost`        | Spread + commission + slippage  |
| `estimate_slippage`                | Expected slippage               |
| `build_execution_plan`             | Final execution plan            |

## 7.3 Paper Trading Tools

| Tool                         | Purpose                        |
| ---------------------------- | ------------------------------ |
| `start_paper_strategy`       | Enable paper strategy          |
| `stop_paper_strategy`        | Stop paper strategy            |
| `submit_paper_order`         | Simulated order                |
| `modify_paper_order`         | Simulated modify               |
| `close_paper_position`       | Simulated close                |
| `record_paper_fill`          | Log paper fill                 |
| `calculate_paper_slippage`   | Simulated/observed slippage    |
| `compare_paper_vs_backtest`  | Expected vs live-like behavior |
| `build_paper_trading_report` | Graduation report              |

## 7.4 Live Execution Tools

These must be heavily permissioned.

| Tool                          | Purpose                           |
| ----------------------------- | --------------------------------- |
| `submit_live_order`           | Place live order                  |
| `modify_live_order`           | Modify live order                 |
| `close_live_position`         | Close live position               |
| `cancel_live_order`           | Cancel pending order              |
| `reduce_live_exposure`        | Reduce risk                       |
| `pause_live_strategy`         | Pause strategy                    |
| `resume_live_strategy`        | Resume strategy                   |
| `sync_live_positions`         | Sync broker state                 |
| `reconcile_broker_state`      | Internal vs broker reconciliation |
| `build_live_execution_report` | Execution result report           |

## 7.5 Kill Switch Tools

| Tool                               | Purpose                  |
| ---------------------------------- | ------------------------ |
| `trigger_global_kill_switch`       | Stop all trading         |
| `trigger_strategy_kill_switch`     | Stop one strategy        |
| `trigger_symbol_kill_switch`       | Stop one symbol          |
| `check_kill_switch_conditions`     | Evaluate trigger rules   |
| `disable_new_orders`               | Block new orders         |
| `close_all_positions`              | Emergency close          |
| `cancel_all_orders`                | Emergency cancel         |
| `record_kill_switch_event`         | Audit record             |
| `require_reenable_approval`        | Prevent silent restart   |
| `clear_kill_switch_after_approval` | Re-enable after approval |

---

# 8. Operations, Audit & Governance Tools

Used by:

```text
Governance Agent
Audit Agent
Performance Reporter Agent
Cost & Efficiency Agent
```

## 8.1 Governance Tools

| Tool                                  | Purpose                      |
| ------------------------------------- | ---------------------------- |
| `check_human_approval_required`       | Determine approval need      |
| `create_approval_packet`              | Build approval request       |
| `record_approval_decision`            | Approved/rejected/revise     |
| `check_agent_lifecycle_permission`    | Can agent run in environment |
| `check_workflow_lifecycle_permission` | Can workflow run             |
| `check_production_action_permission`  | Can production action happen |
| `check_tool_permission_profile`       | Tool-level permission gate   |
| `check_policy_exception_allowed`      | Exception handling           |
| `block_for_missing_approval`          | Deterministic block          |
| `build_governance_decision`           | Governance output            |

## 8.2 Audit Tools

| Tool                             | Purpose                           |
| -------------------------------- | --------------------------------- |
| `write_audit_log`                | Immutable audit event             |
| `read_audit_log`                 | Retrieve audit history            |
| `write_decision_record`          | Decision log                      |
| `write_handoff_record`           | Agent handoff log                 |
| `write_tool_call_record`         | Tool call log                     |
| `write_policy_gate_record`       | Policy result log                 |
| `write_approval_record`          | Approval event                    |
| `write_artifact_record`          | Artifact metadata                 |
| `create_run_snapshot`            | Snapshot inputs/config/data/model |
| `create_reproducibility_record`  | Rerun instructions                |
| `generate_agent_audit_report`    | Per-agent audit report            |
| `generate_workflow_audit_report` | Workflow audit report             |

## 8.3 Performance Reporting Tools

| Tool                                 | Purpose                      |
| ------------------------------------ | ---------------------------- |
| `get_strategy_performance_snapshot`  | Current strategy performance |
| `get_portfolio_performance_snapshot` | Portfolio performance        |
| `detect_live_backtest_drift`         | Live vs backtest divergence  |
| `detect_strategy_degradation`        | Performance decay            |
| `detect_agent_workflow_failures`     | Failed agent workflows       |
| `calculate_agent_success_rate`       | Agent reliability            |
| `calculate_workflow_completion_rate` | Workflow reliability         |
| `calculate_agent_latency`            | Runtime latency              |
| `calculate_tool_failure_rate`        | Tool reliability             |
| `build_performance_report`           | Full performance report      |

## 8.4 Cost & Efficiency Tools

| Tool                           | Purpose                    |
| ------------------------------ | -------------------------- |
| `track_llm_token_usage`        | Token/cost tracking        |
| `track_tool_runtime_cost`      | Tool cost tracking         |
| `track_backtest_compute_cost`  | Backtest compute cost      |
| `track_data_provider_cost`     | Data cost                  |
| `track_broker_costs`           | Spread, commission, swap   |
| `calculate_cost_per_workflow`  | Workflow cost              |
| `calculate_cost_per_strategy`  | Strategy lifecycle cost    |
| `detect_expensive_workflow`    | Cost anomaly               |
| `recommend_cost_optimization`  | Cost reduction suggestions |
| `build_cost_efficiency_report` | Cost report                |

---

# 9. Agent / Workflow Quality Gate Tools

Create these before creating many agents.

| Tool                              | Purpose                                  |
| --------------------------------- | ---------------------------------------- |
| `run_agent_manifest_quality_gate` | Validate one agent package               |
| `run_agent_registry_quality_gate` | Validate all registered agents           |
| `run_workflow_quality_gate`       | Validate workflows                       |
| `run_tool_registry_quality_gate`  | Validate tools                           |
| `run_permission_quality_gate`     | Validate permissions                     |
| `run_schema_contract_tests`       | Validate schema compatibility            |
| `run_handoff_contract_tests`      | Validate agent handoffs                  |
| `run_guardrail_tests`             | Test blocked actions                     |
| `run_prompt_injection_tests`      | Security/prompt injection tests          |
| `run_failure_path_tests`          | Missing inputs, tool failure, stale data |
| `run_smoke_tests`                 | Basic agent construction and execution   |
| `generate_quality_gate_report`    | Summary report                           |

---

# 10. Tool Creation Order

Build in this order.

## Phase 1 — Runtime Foundation

```text
load_agent_manifest
validate_agent_manifest
load_instruction_files
load_skill_files
load_prompt_templates
resolve_agent_tools
build_adk_agent
run_agent
validate_agent_output
emit_audit_event
check_permissions
check_policy_gate
```

## Phase 2 — Shared Contracts

```text
validate_input_schema
validate_output_schema
validate_handoff_payload
validate_evidence_pack
validate_approval_packet
validate_data_freshness
validate_environment_mode
```

## Phase 3 — Data & Research

```text
get_ohlcv_data
get_tick_data
get_spread_data
get_symbol_metadata
validate_ohlcv_data
fetch_forexfactory_news
fetch_forexfactory_calendar
fetch_forexfactory_sentiment
fetch_forexfactory_instrument_page
calculate_atr
calculate_adr
calculate_spread_statistics
calculate_session_statistics
calculate_seasonality_statistics
detect_market_regime
build_research_evidence_pack
```

## Phase 4 — Strategy Creation

```text
generate_strategy_spec
validate_strategy_spec
normalize_strategy_rules
classify_strategy_type
detect_high_risk_trade_management
infer_required_data_columns
generate_strategy_class
generate_strategy_config
generate_strategy_tests
save_strategy_spec
register_strategy
build_strategy_handoff_package
```

## Phase 5 — Backtesting & Analytics

```text
run_backtest
validate_backtest_config
validate_backtest_result
calculate_trade_metrics
calculate_return_metrics
calculate_drawdown_metrics
calculate_ratio_metrics
calculate_risk_metrics
calculate_period_analysis
calculate_long_short_split
build_backtest_report
```

## Phase 6 — Robustness & Optimization

```text
run_parameter_sweep
run_walk_forward_optimization
run_walk_forward_matrix
run_spread_stress_test
run_slippage_stress_test
run_combined_monte_carlo
run_cross_market_test
run_cross_timeframe_test
calculate_robustness_score
build_validation_evidence_package
```

## Phase 7 — Risk & Portfolio

```text
get_open_positions
get_strategy_allocations
calculate_portfolio_var
calculate_portfolio_cvar
calculate_portfolio_correlation
calculate_risk_contribution
check_max_drawdown_limit
check_correlation_limit
check_var_limit
check_margin_limit
run_risk_governor_checks
calculate_volatility_adjusted_size
calculate_correlation_adjusted_size
build_risk_decision_package
```

## Phase 8 — Execution

```text
check_broker_connection
get_account_info
get_symbol_info
get_current_bid_ask
get_current_spread
run_execution_readiness_check
validate_order_request
build_execution_plan
start_paper_strategy
submit_paper_order
build_paper_trading_report
submit_live_order
modify_live_order
close_live_position
trigger_global_kill_switch
check_kill_switch_conditions
```

## Phase 9 — Governance, Audit, Monitoring

```text
create_approval_packet
record_approval_decision
write_audit_log
write_decision_record
create_run_snapshot
generate_agent_audit_report
detect_live_backtest_drift
detect_strategy_degradation
track_llm_token_usage
calculate_cost_per_workflow
build_cost_efficiency_report
```

---

# 11. Minimum Tool Set to Start Building Agents

To avoid building too much upfront, start with this **minimum viable tool layer**:

```text
Runtime:
- load_agent_manifest
- validate_agent_manifest
- build_adk_agent
- run_agent
- validate_agent_output
- check_permissions
- emit_audit_event

Research:
- get_ohlcv_data
- validate_ohlcv_data
- get_symbol_metadata
- calculate_adr
- calculate_atr
- calculate_spread_statistics
- fetch_forexfactory_calendar
- fetch_forexfactory_news
- build_research_evidence_pack

Strategy:
- generate_strategy_spec
- validate_strategy_spec
- classify_strategy_type
- detect_high_risk_trade_management
- generate_strategy_class
- generate_strategy_tests
- save_strategy_spec
- register_strategy

Simulation:
- run_backtest
- validate_backtest_result
- calculate_trade_metrics
- calculate_drawdown_metrics
- calculate_ratio_metrics
- build_backtest_report

Risk:
- get_open_positions
- calculate_portfolio_var
- calculate_portfolio_correlation
- check_max_drawdown_limit
- check_correlation_limit
- run_risk_governor_checks
- build_risk_decision_package

Execution:
- check_broker_connection
- get_account_info
- get_symbol_info
- get_current_spread
- run_execution_readiness_check
- submit_paper_order
- trigger_global_kill_switch

Governance:
- create_approval_packet
- record_approval_decision
- write_audit_log
- generate_agent_audit_report
```

That is the smallest practical set I would create before building the first real agents.

Yes. For the HaruQuant “Zero Human Trading Firm” project, the canonical registry should include the following **agents** and **tools**.

This design follows the same structural idea as TradingAgents: a trading firm is modeled as specialized agents such as analysts, researchers, traders, and risk managers, rather than one all-powerful bot. ([TradingAgents][1]) It also fits the ADK direction of building production multi-agent systems with agents and tools, and the MCP model where tools are named, schema-described capabilities exposed to language models with human-in-the-loop controls for sensitive actions. ([Google Cloud Documentation][2])

# 1. Full agent list

## A. Governance and orchestration agents

| Agent                                    | Primary role                                                                                                            | Should exist in v0.1? |
| ---------------------------------------- | ----------------------------------------------------------------------------------------------------------------------- | --------------------: |
| **CEO Agent / Chief Investment Officer** | Main user-facing agent. Receives user requests, delegates work, collects evidence, and produces final memos.            |                   Yes |
| **Planner Agent**                        | Converts user requests into structured plans: intent, missing inputs, tools, agents, risk level, approval requirements. |                   Yes |
| **Conversation Orchestrator**            | Runtime controller that executes the Planner’s plan and coordinates agent/tool calls.                                   |                   Yes |
| **Task Manager Agent / Service**         | Creates, tracks, assigns, blocks, completes, and audits agent tasks.                                                    |                   Yes |
| **Agent Registry Service**               | Maintains the list of available agents, roles, permissions, and status.                                                 |                   Yes |
| **Policy Interpreter Agent**             | Reads constitution, risk policy, permissions, and lifecycle documents to answer governance questions.                   |                 Later |
| **Board Liaison Agent**                  | Prepares approval requests for you as the human Board.                                                                  |                 Later |

## B. Research Department agents

| Agent                                 | Primary role                                                                                         | Should exist in v0.1? |
| ------------------------------------- | ---------------------------------------------------------------------------------------------------- | --------------------: |
| **Research Agent**                    | General research coordinator for market, strategy, and internal evidence research.                   |                   Yes |
| **Market Intelligence Agent**         | Analyzes market regimes, volatility, sessions, spreads, and symbol suitability.                      |                   Yes |
| **Strategy Scout Agent**              | Finds and scores new strategy ideas from internal memory, backtests, research, and external sources. |                   Yes |
| **Technical Analyst Agent**           | Produces technical context: trend, range, volatility, levels, indicators, strategy fit.              |                   Yes |
| **News & Sentiment Agent**            | Monitors high-impact events, macro risk, news restrictions, and sentiment context.                   |                 Later |
| **Fundamental / Macro Analyst Agent** | Analyzes macro drivers, rates, inflation, central banks, commodities, and index context.             |                 Later |
| **Bull Researcher Agent**             | Argues the positive case for a strategy, trade, or allocation.                                       |                 Later |
| **Bear Researcher Agent**             | Argues the negative case against a strategy, trade, or allocation.                                   |                 Later |

## C. Strategy Development Department agents

| Agent                             | Primary role                                                                              | Should exist in v0.1? |
| --------------------------------- | ----------------------------------------------------------------------------------------- | --------------------: |
| **Strategy Creator Agent**        | Converts natural language or research ideas into formal `StrategySpec`.                   |                   Yes |
| **Strategy Spec Validator Agent** | Validates completeness, testability, and feasibility of strategy specs.                   |                   Yes |
| **Strategy Reviewer Agent**       | Reviews strategy logic for lookahead bias, repainting, overfitting, and live feasibility. |                   Yes |
| **Strategy Codegen Agent**        | Generates HaruQuant-compatible strategy code from approved specs.                         |                   Yes |
| **Strategy Test Generator Agent** | Generates unit tests and edge-case tests for strategy code.                               |                   Yes |
| **Strategy Refactor Agent**       | Refactors generated or existing strategies without changing trading logic.                |                 Later |
| **Strategy Documentation Agent**  | Writes strategy documentation, assumptions, parameters, and lifecycle notes.              |                 Later |

## D. Validation and Backtesting Department agents

| Agent                             | Primary role                                                                                                                | Should exist in v0.1? |
| --------------------------------- | --------------------------------------------------------------------------------------------------------------------------- | --------------------: |
| **Backtest Agent**                | Runs reproducible HaruQuant backtests and saves evidence packages.                                                          |                   Yes |
| **Backtest Analyst Agent**        | Explains backtest behavior, strengths, weaknesses, and failure modes.                                                       |                   Yes |
| **Optimization Agent**            | Runs parameter sweeps, WFO, and optimization jobs.                                                                          |                 Later |
| **Optimization Comparator Agent** | Compares optimization results and prefers stable parameter regions over single best runs.                                   |                 Later |
| **Robustness Agent**              | Runs OOS, spread, slippage, Monte Carlo, WFM/WFO, and stress tests.                                                         |       Yes, after v0.1 |
| **Statistical Validation Agent**  | Tests whether the edge is statistically believable using sample-size, bootstrap, permutation, regime, and benchmark checks. |       Yes, after v0.1 |
| **Benchmark Analyst Agent**       | Compares strategies against benchmarks and alternative passive/naive strategies.                                            |                 Later |
| **Data Quality Agent**            | Checks missing bars, duplicated ticks, bad spreads, timezone issues, and symbol metadata errors.                            |                   Yes |

## E. Risk and Portfolio Department agents

| Agent                          | Primary role                                                                                                                              | Should exist in v0.1? |
| ------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------- | --------------------: |
| **Risk Reviewer Agent**        | Produces LLM-readable risk memos based on deterministic RiskGovernor outputs and strategy evidence.                                       |                   Yes |
| **RiskGovernor Service**       | Deterministic non-LLM risk gate. Approves or rejects trade proposals.                                                                     |                   Yes |
| **Portfolio Manager Agent**    | Manages strategy allocation, promotion, demotion, exposure, and diversification.                                                          |                 Later |
| **Correlation Analyst Agent**  | Analyzes symbol/strategy correlation and cluster exposure.                                                                                |                 Later |
| **Exposure Analyst Agent**     | Monitors portfolio exposure by symbol, currency, market, strategy, and account.                                                           |                 Later |
| **Prop Firm Compliance Agent** | Checks compliance with the standard prop-firm risk profile: 5% daily loss, 10% total loss, news restrictions, weekend rules, consistency. |                   Yes |
| **Consistency Rule Agent**     | Tracks Best Day Rule, profit distribution, and overconcentration of returns.                                                              |                   Yes |

## F. Execution Department agents

| Agent                       | Primary role                                                                                     | Should exist in v0.1? |
| --------------------------- | ------------------------------------------------------------------------------------------------ | --------------------: |
| **Execution Planner Agent** | Converts an approved trade proposal into an execution plan.                                      |                 Later |
| **Paper Execution Agent**   | Executes strategies in simulated/paper mode.                                                     |                   Yes |
| **Live Execution Agent**    | Executes live orders only after Board approval and RiskGovernor approval.                        |                 Later |
| **Order Router Service**    | Routes approved paper/live orders to the correct broker bridge.                                  |                 Later |
| **MT5 Bridge Service**      | Interfaces with MetaTrader 5 for account, tick, order, and position actions.                     |                 Later |
| **cTrader Bridge Service**  | Interfaces with cTrader/cBots for account, tick, order, and position actions.                    |                 Later |
| **Kill Switch Service**     | Deterministic service that disables trading when risk, broker, audit, or execution health fails. |       Yes before live |
| **Execution Monitor Agent** | Reviews order fills, slippage, rejections, broker errors, and latency.                           |                 Later |

## G. Operations, reporting, and audit agents

| Agent                               | Primary role                                                                                      | Should exist in v0.1? |
| ----------------------------------- | ------------------------------------------------------------------------------------------------- | --------------------: |
| **Performance Reporter Agent**      | Produces daily, weekly, monthly, and Board reports.                                               |                   Yes |
| **Audit Agent**                     | Verifies that every decision, tool call, approval, and trade has evidence and logs.               |                   Yes |
| **Incident Agent**                  | Summarizes incidents, root causes, affected strategies, and required actions.                     |                 Later |
| **Cost Optimizer Agent**            | Tracks token, model, compute, and workflow cost; recommends cheaper routing where safe.           |                 Later |
| **Memory Curator Agent**            | Updates institutional memory, lessons learned, rejected strategy notes, and performance memory.   |                 Later |
| **Documentation Agent**             | Maintains docs, READMEs, changelogs, and implementation guides.                                   |                 Later |
| **Dashboard / Page Operator Agent** | Performs safe UI page actions such as filtering, navigating, selecting tabs, and opening reports. |                 Later |

# 2. Final canonical agent registry

This is the clean list I would put into `agent_registry.py`.

```python
AGENTS = [
    # Governance / Orchestration
    "ceo_agent",
    "planner_agent",
    "conversation_orchestrator",
    "task_manager",
    "agent_registry_service",
    "policy_interpreter_agent",
    "board_liaison_agent",

    # Research
    "research_agent",
    "market_intelligence_agent",
    "strategy_scout_agent",
    "technical_analyst_agent",
    "news_sentiment_agent",
    "fundamental_macro_analyst_agent",
    "bull_researcher_agent",
    "bear_researcher_agent",

    # Strategy Development
    "strategy_creator_agent",
    "strategy_spec_validator_agent",
    "strategy_reviewer_agent",
    "strategy_codegen_agent",
    "strategy_test_generator_agent",
    "strategy_refactor_agent",
    "strategy_documentation_agent",

    # Validation / Backtesting
    "backtest_agent",
    "backtest_analyst_agent",
    "optimization_agent",
    "optimization_comparator_agent",
    "robustness_agent",
    "statistical_validation_agent",
    "benchmark_analyst_agent",
    "data_quality_agent",

    # Risk / Portfolio
    "risk_reviewer_agent",
    "risk_governor_service",
    "portfolio_manager_agent",
    "correlation_analyst_agent",
    "exposure_analyst_agent",
    "prop_firm_compliance_agent",
    "consistency_rule_agent",

    # Execution
    "execution_planner_agent",
    "paper_execution_agent",
    "live_execution_agent",
    "order_router_service",
    "mt5_bridge_service",
    "ctrader_bridge_service",
    "kill_switch_service",
    "execution_monitor_agent",

    # Operations / Audit
    "performance_reporter_agent",
    "audit_agent",
    "incident_agent",
    "cost_optimizer_agent",
    "memory_curator_agent",
    "documentation_agent",
    "dashboard_page_operator_agent",
]
```

For v0.1, use this reduced list:

```python
V0_1_AGENTS = [
    "ceo_agent",
    "planner_agent",
    "conversation_orchestrator",
    "task_manager",
    "agent_registry_service",
    "research_agent",
    "market_intelligence_agent",
    "strategy_scout_agent",
    "technical_analyst_agent",
    "strategy_creator_agent",
    "strategy_spec_validator_agent",
    "strategy_reviewer_agent",
    "strategy_codegen_agent",
    "strategy_test_generator_agent",
    "data_quality_agent",
    "backtest_agent",
    "backtest_analyst_agent",
    "risk_reviewer_agent",
    "risk_governor_service",
    "prop_firm_compliance_agent",
    "consistency_rule_agent",
    "paper_execution_agent",
    "performance_reporter_agent",
    "audit_agent",
]
```

# 3. Full tool list

MCP is useful as the mental model here: each tool should have a name, description, input schema, output schema, permission level, and approval behavior. MCP specifically treats tools as named capabilities that can call external systems, query databases, invoke APIs, or perform computations, and recommends clear user visibility and human confirmation for sensitive operations. ([Model Context Protocol][3])

## A. Governance and policy tools

| Tool                             | Type           | Used by                                                |
| -------------------------------- | -------------- | ------------------------------------------------------ |
| `read_constitution`              | Read-only      | CEO, Planner, Policy Interpreter, Audit                |
| `read_risk_policy`               | Read-only      | CEO, Risk Reviewer, RiskGovernor, Prop Firm Compliance |
| `read_agent_permissions`         | Read-only      | Planner, Orchestrator, Audit                           |
| `read_strategy_lifecycle_policy` | Read-only      | CEO, Portfolio Manager, Strategy Reviewer              |
| `validate_against_constitution`  | Write/analysis | CEO, Planner, Audit                                    |
| `validate_against_risk_policy`   | Write/analysis | Risk Reviewer, RiskGovernor                            |
| `validate_agent_permission`      | Critical       | Orchestrator, Audit                                    |
| `request_human_approval`         | Critical       | CEO, Board Liaison                                     |
| `record_human_approval`          | Critical       | Board Liaison, Audit                                   |
| `reject_human_approval`          | Critical       | Board Liaison, Audit                                   |
| `read_approval_queue`            | Read-only      | CEO, Board Liaison                                     |
| `create_board_approval_request`  | Critical       | CEO, Portfolio Manager, Risk Reviewer                  |

## B. Task and orchestration tools

| Tool                    | Type                      | Used by                    |
| ----------------------- | ------------------------- | -------------------------- |
| `create_agent_task`     | Write                     | CEO, Orchestrator          |
| `assign_agent_task`     | Write                     | Orchestrator, Task Manager |
| `start_agent_task`      | Write                     | Task Manager               |
| `complete_agent_task`   | Write                     | Task Manager               |
| `fail_agent_task`       | Write                     | Task Manager               |
| `block_agent_task`      | Write                     | Task Manager               |
| `create_child_task`     | Write                     | Orchestrator               |
| `get_task_tree`         | Read-only                 | CEO, Audit                 |
| `get_task_status`       | Read-only                 | CEO, Task Manager          |
| `list_active_tasks`     | Read-only                 | CEO, Task Manager          |
| `cancel_agent_task`     | Critical                  | CEO, Task Manager, Audit   |
| `disable_agent`         | Critical                  | CEO, Audit, Kill Switch    |
| `enable_agent`          | Critical + human approval | Board Liaison              |
| `get_agent_status`      | Read-only                 | CEO, Audit                 |
| `get_agent_registry`    | Read-only                 | Planner, Orchestrator      |
| `update_agent_registry` | Critical + human approval | Admin only                 |

## C. Memory and evidence tools

| Tool                          | Type      | Used by                           |
| ----------------------------- | --------- | --------------------------------- |
| `create_evidence_ref`         | Write     | All agents                        |
| `read_evidence_ref`           | Read-only | All agents                        |
| `list_evidence_refs`          | Read-only | CEO, Audit                        |
| `save_research_report`        | Write     | Research Agent                    |
| `read_research_report`        | Read-only | CEO, Strategy Creator             |
| `save_strategy_memory`        | Write     | Strategy Creator, Memory Curator  |
| `read_strategy_memory`        | Read-only | Research, Portfolio Manager       |
| `save_performance_memory`     | Write     | Performance Reporter              |
| `read_performance_memory`     | Read-only | CEO, Portfolio Manager            |
| `save_lesson_learned`         | Write     | Memory Curator, Audit             |
| `read_lessons_learned`        | Read-only | CEO, Research                     |
| `search_institutional_memory` | Read-only | Research, CEO                     |
| `search_strategy_memory`      | Read-only | Strategy Scout, Portfolio Manager |
| `search_backtest_memory`      | Read-only | Backtest Analyst                  |
| `archive_strategy_memory`     | Write     | Portfolio Manager, Audit          |
| `lock_evidence_record`        | Critical  | Audit                             |
| `verify_evidence_integrity`   | Critical  | Audit                             |

## D. Data tools

| Tool                          | Type                      | Used by                              |
| ----------------------------- | ------------------------- | ------------------------------------ |
| `list_symbols`                | Read-only                 | Research, Strategy Creator           |
| `get_symbol_metadata`         | Read-only                 | Research, Backtest, RiskGovernor     |
| `get_ohlcv_data`              | Read-only                 | Research, Backtest                   |
| `get_tick_data`               | Read-only                 | Backtest, Execution Monitor          |
| `get_spread_history`          | Read-only                 | Research, RiskGovernor               |
| `get_session_calendar`        | Read-only                 | Market Intelligence                  |
| `get_economic_calendar`       | Read-only                 | News/Sentiment, Prop Firm Compliance |
| `get_high_impact_news_events` | Read-only                 | News/Sentiment, RiskGovernor         |
| `get_latest_price`            | Read-only                 | Execution Planner, RiskGovernor      |
| `get_latest_tick`             | Read-only                 | Execution Planner, MT5 Bridge        |
| `get_data_freshness`          | Read-only                 | Data Quality, CEO                    |
| `validate_data_quality`       | Write/analysis            | Data Quality Agent                   |
| `detect_missing_bars`         | Write/analysis            | Data Quality Agent                   |
| `detect_duplicate_ticks`      | Write/analysis            | Data Quality Agent                   |
| `detect_bad_spreads`          | Write/analysis            | Data Quality Agent                   |
| `normalize_symbol_data`       | Write                     | Data Quality Agent                   |
| `import_market_data`          | Critical/write            | Data Admin only                      |
| `delete_market_data`          | Critical + human approval | Admin only                           |

## E. Research tools

| Tool                                | Type           | Used by             |
| ----------------------------------- | -------------- | ------------------- |
| `create_market_intelligence_report` | Write          | Market Intelligence |
| `create_technical_analysis_report`  | Write          | Technical Analyst   |
| `create_strategy_idea`              | Write          | Strategy Scout      |
| `score_strategy_idea`               | Write/analysis | Strategy Scout      |
| `rank_strategy_ideas`               | Write/analysis | Strategy Scout      |
| `search_internal_research`          | Read-only      | Research            |
| `search_external_research`          | Read-only      | Research            |
| `summarize_research_source`         | Write/analysis | Research            |
| `create_bull_case`                  | Write/analysis | Bull Researcher     |
| `create_bear_case`                  | Write/analysis | Bear Researcher     |
| `create_research_debate_summary`    | Write/analysis | CEO, Research       |

## F. Strategy specification tools

| Tool                                    | Type                                 | Used by                              |
| --------------------------------------- | ------------------------------------ | ------------------------------------ |
| `create_strategy_spec`                  | Write                                | Strategy Creator                     |
| `read_strategy_spec`                    | Read-only                            | Strategy Reviewer, Codegen, Backtest |
| `update_strategy_spec`                  | Write + approval if already reviewed | Strategy Creator                     |
| `validate_strategy_spec`                | Write/analysis                       | Spec Validator                       |
| `reject_strategy_spec`                  | Write                                | Strategy Reviewer                    |
| `approve_strategy_spec_for_code_review` | Write                                | Strategy Reviewer                    |
| `create_strategy_version`               | Write                                | Strategy Creator                     |
| `compare_strategy_versions`             | Read/analysis                        | Strategy Reviewer                    |
| `set_strategy_lifecycle_state`          | Critical                             | Lifecycle Service                    |
| `request_strategy_promotion`            | Critical                             | CEO, Portfolio Manager               |
| `request_strategy_demotion`             | Critical                             | Portfolio Manager                    |
| `request_strategy_retirement`           | Critical                             | Portfolio Manager, Audit             |

## G. Strategy code tools

| Tool                         | Type                      | Used by                     |
| ---------------------------- | ------------------------- | --------------------------- |
| `generate_strategy_code`     | Write                     | Strategy Codegen            |
| `read_strategy_code`         | Read-only                 | Strategy Reviewer, Backtest |
| `save_strategy_code`         | Write                     | Strategy Codegen            |
| `update_strategy_code`       | Write + approval          | Strategy Refactor           |
| `generate_strategy_tests`    | Write                     | Strategy Test Generator     |
| `run_strategy_unit_tests`    | Write/analysis            | Strategy Test Generator     |
| `run_strategy_static_checks` | Write/analysis            | Strategy Reviewer           |
| `run_lookahead_bias_check`   | Write/analysis            | Strategy Reviewer           |
| `run_repainting_check`       | Write/analysis            | Strategy Reviewer           |
| `run_parameter_sanity_check` | Write/analysis            | Strategy Reviewer           |
| `create_strategy_code_hash`  | Write                     | Strategy Codegen            |
| `lock_strategy_code_version` | Critical                  | Audit                       |
| `delete_strategy_code`       | Critical + human approval | Admin only                  |

## H. Backtesting tools

| Tool                         | Type                      | Used by                              |
| ---------------------------- | ------------------------- | ------------------------------------ |
| `create_backtest_request`    | Write                     | Backtest Agent                       |
| `run_backtest`               | Write                     | Backtest Agent                       |
| `cancel_backtest`            | Write                     | Backtest Agent                       |
| `read_backtest_result`       | Read-only                 | CEO, Backtest Analyst, Risk Reviewer |
| `list_backtest_runs`         | Read-only                 | CEO, Backtest Analyst                |
| `compare_backtest_runs`      | Read/analysis             | Backtest Analyst                     |
| `save_backtest_config`       | Write                     | Backtest Agent                       |
| `save_backtest_trades`       | Write                     | Backtest Agent                       |
| `save_backtest_orders`       | Write                     | Backtest Agent                       |
| `save_backtest_deals`        | Write                     | Backtest Agent                       |
| `save_backtest_equity_curve` | Write                     | Backtest Agent                       |
| `save_backtest_metrics`      | Write                     | Backtest Agent                       |
| `create_backtest_report`     | Write                     | Backtest Analyst                     |
| `lock_backtest_result`       | Critical                  | Audit                                |
| `delete_backtest_result`     | Critical + human approval | Admin only                           |

## I. Analytics tools

| Tool                             | Type           | Used by                |
| -------------------------------- | -------------- | ---------------------- |
| `calculate_trade_metrics`        | Write/analysis | Backtest Agent         |
| `calculate_return_metrics`       | Write/analysis | Backtest Agent         |
| `calculate_drawdown_metrics`     | Write/analysis | Backtest Agent         |
| `calculate_ratio_metrics`        | Write/analysis | Backtest Agent         |
| `calculate_risk_metrics`         | Write/analysis | Risk Reviewer          |
| `calculate_efficiency_metrics`   | Write/analysis | Backtest Analyst       |
| `calculate_distribution_metrics` | Write/analysis | Statistical Validation |
| `calculate_benchmark_metrics`    | Write/analysis | Benchmark Analyst      |
| `run_statistical_tests`          | Write/analysis | Statistical Validation |
| `calculate_long_short_split`     | Write/analysis | Backtest Analyst       |
| `calculate_session_performance`  | Write/analysis | Backtest Analyst       |
| `calculate_monthly_performance`  | Write/analysis | Backtest Analyst       |
| `calculate_regime_performance`   | Write/analysis | Backtest Analyst       |
| `calculate_cost_sensitivity`     | Write/analysis | Backtest Analyst       |

## J. Optimization and robustness tools

| Tool                                  | Type           | Used by                 |
| ------------------------------------- | -------------- | ----------------------- |
| `run_parameter_sweep`                 | Write          | Optimization Agent      |
| `run_walk_forward_optimization`       | Write          | Optimization Agent      |
| `run_walk_forward_matrix`             | Write          | Optimization Agent      |
| `compare_optimization_results`        | Write/analysis | Optimization Comparator |
| `detect_parameter_cliffs`             | Write/analysis | Optimization Comparator |
| `find_stable_parameter_regions`       | Write/analysis | Optimization Comparator |
| `run_second_oos_test`                 | Write          | Robustness Agent        |
| `run_spread_stress_test`              | Write          | Robustness Agent        |
| `run_slippage_stress_test`            | Write          | Robustness Agent        |
| `run_commission_stress_test`          | Write          | Robustness Agent        |
| `run_swap_stress_test`                | Write          | Robustness Agent        |
| `run_cross_market_test`               | Write          | Robustness Agent        |
| `run_cross_timeframe_test`            | Write          | Robustness Agent        |
| `run_monte_carlo_trade_order_test`    | Write          | Robustness Agent        |
| `run_monte_carlo_resampling_test`     | Write          | Robustness Agent        |
| `run_monte_carlo_skipped_trades_test` | Write          | Robustness Agent        |
| `run_monte_carlo_parameter_test`      | Write          | Robustness Agent        |
| `run_randomized_history_test`         | Write          | Robustness Agent        |
| `create_robustness_scorecard`         | Write          | Robustness Agent        |
| `read_robustness_result`              | Read-only      | CEO, Risk Reviewer      |

## K. Statistical validation tools

| Tool                                 | Type           | Used by                               |
| ------------------------------------ | -------------- | ------------------------------------- |
| `check_minimum_trade_count`          | Write/analysis | Statistical Validation                |
| `run_bootstrap_confidence_intervals` | Write/analysis | Statistical Validation                |
| `run_permutation_test`               | Write/analysis | Statistical Validation                |
| `run_regime_split_test`              | Write/analysis | Statistical Validation                |
| `run_long_short_stability_test`      | Write/analysis | Statistical Validation                |
| `run_monthly_stability_test`         | Write/analysis | Statistical Validation                |
| `calculate_probability_of_ruin`      | Write/analysis | Statistical Validation, Risk Reviewer |
| `create_evidence_quality_rating`     | Write/analysis | Statistical Validation                |

## L. Risk tools

| Tool                                  | Type              | Used by                           |
| ------------------------------------- | ----------------- | --------------------------------- |
| `get_account_snapshot`                | Read-only         | RiskGovernor, Risk Reviewer       |
| `get_open_positions`                  | Read-only         | RiskGovernor                      |
| `get_pending_orders`                  | Read-only         | RiskGovernor                      |
| `calculate_position_risk`             | Critical/analysis | RiskGovernor                      |
| `calculate_trade_risk`                | Critical/analysis | RiskGovernor                      |
| `calculate_portfolio_exposure`        | Critical/analysis | RiskGovernor                      |
| `calculate_symbol_exposure`           | Critical/analysis | RiskGovernor                      |
| `calculate_currency_cluster_exposure` | Critical/analysis | RiskGovernor                      |
| `calculate_usd_cluster_exposure`      | Critical/analysis | RiskGovernor                      |
| `calculate_correlation_matrix`        | Critical/analysis | RiskGovernor, Correlation Analyst |
| `calculate_correlation_impact`        | Critical/analysis | RiskGovernor                      |
| `calculate_margin_impact`             | Critical/analysis | RiskGovernor                      |
| `calculate_var`                       | Critical/analysis | RiskGovernor                      |
| `calculate_cvar`                      | Critical/analysis | RiskGovernor                      |
| `check_daily_loss_limit`              | Critical          | RiskGovernor                      |
| `check_total_loss_limit`              | Critical          | RiskGovernor                      |
| `check_monthly_drawdown_limit`        | Critical          | RiskGovernor                      |
| `check_portfolio_drawdown_limit`      | Critical          | RiskGovernor                      |
| `check_news_restriction_window`       | Critical          | Prop Firm Compliance              |
| `check_weekend_overnight_restriction` | Critical          | Prop Firm Compliance              |
| `check_best_day_rule`                 | Critical          | Consistency Rule Agent            |
| `create_risk_review`                  | Write             | Risk Reviewer                     |
| `request_risk_approval`               | Critical          | Execution Planner                 |
| `approve_trade_proposal`              | Critical          | RiskGovernor                      |
| `reject_trade_proposal`               | Critical          | RiskGovernor                      |
| `issue_risk_approval_token`           | Critical          | RiskGovernor                      |
| `revoke_risk_approval_token`          | Critical          | RiskGovernor                      |
| `read_risk_approval_token`            | Read-only         | Order Router, Audit               |

## M. Prop-firm compliance tools

| Tool                                 | Type              | Used by                |
| ------------------------------------ | ----------------- | ---------------------- |
| `check_prop_firm_daily_loss`         | Critical          | Prop Firm Compliance   |
| `check_prop_firm_total_loss`         | Critical          | Prop Firm Compliance   |
| `check_prop_firm_profit_target`      | Read/analysis     | Prop Firm Compliance   |
| `check_prop_firm_news_window`        | Critical          | Prop Firm Compliance   |
| `check_prop_firm_weekend_rule`       | Critical          | Prop Firm Compliance   |
| `check_prop_firm_overnight_rule`     | Critical          | Prop Firm Compliance   |
| `check_forbidden_practices`          | Critical          | Prop Firm Compliance   |
| `check_ea_automation_compliance`     | Critical          | Prop Firm Compliance   |
| `check_allocation_compliance`        | Critical          | Prop Firm Compliance   |
| `calculate_consistency_score`        | Critical/analysis | Consistency Rule Agent |
| `check_best_day_rule_threshold`      | Critical          | Consistency Rule Agent |
| `create_prop_firm_compliance_report` | Write             | Prop Firm Compliance   |

## N. Portfolio tools

| Tool                              | Type                      | Used by                        |
| --------------------------------- | ------------------------- | ------------------------------ |
| `get_strategy_allocations`        | Read-only                 | Portfolio Manager              |
| `get_strategy_statuses`           | Read-only                 | Portfolio Manager              |
| `calculate_strategy_contribution` | Write/analysis            | Portfolio Manager              |
| `calculate_portfolio_correlation` | Write/analysis            | Portfolio Manager              |
| `rank_live_strategies`            | Write/analysis            | Portfolio Manager              |
| `rank_paper_strategies`           | Write/analysis            | Portfolio Manager              |
| `recommend_strategy_promotion`    | Write/analysis            | Portfolio Manager              |
| `recommend_strategy_demotion`     | Write/analysis            | Portfolio Manager              |
| `recommend_strategy_retirement`   | Write/analysis            | Portfolio Manager              |
| `request_allocation_increase`     | Critical + human approval | Portfolio Manager              |
| `request_allocation_decrease`     | Critical                  | Portfolio Manager              |
| `set_strategy_allocation`         | Critical + human approval | Admin/Portfolio Manager        |
| `pause_strategy`                  | Critical                  | Portfolio Manager, Kill Switch |
| `resume_strategy`                 | Critical + human approval | Board Liaison                  |
| `retire_strategy`                 | Critical + human approval | Portfolio Manager              |

## O. Paper execution tools

| Tool                         | Type                          | Used by                               |
| ---------------------------- | ----------------------------- | ------------------------------------- |
| `start_paper_trading`        | Write                         | Paper Execution                       |
| `stop_paper_trading`         | Write                         | Paper Execution, Portfolio Manager    |
| `place_paper_order`          | Write + RiskGovernor approval | Paper Execution                       |
| `close_paper_position`       | Write + RiskGovernor approval | Paper Execution                       |
| `cancel_paper_order`         | Write                         | Paper Execution                       |
| `get_paper_account_snapshot` | Read-only                     | Paper Execution, Performance Reporter |
| `get_paper_positions`        | Read-only                     | Risk Reviewer                         |
| `get_paper_trade_log`        | Read-only                     | Performance Reporter                  |
| `simulate_spread`            | Write/analysis                | Paper Broker                          |
| `simulate_slippage`          | Write/analysis                | Paper Broker                          |
| `simulate_commission`        | Write/analysis                | Paper Broker                          |
| `simulate_swap`              | Write/analysis                | Paper Broker                          |

## P. Live execution tools

| Tool                         | Type                                               | Used by                     |
| ---------------------------- | -------------------------------------------------- | --------------------------- |
| `request_live_activation`    | Critical + human approval                          | CEO, Portfolio Manager      |
| `activate_live_trading`      | Critical + human approval                          | Board Liaison/Admin         |
| `deactivate_live_trading`    | Critical                                           | Kill Switch, Board Liaison  |
| `create_trade_proposal`      | Critical                                           | Execution Planner           |
| `create_execution_plan`      | Critical                                           | Execution Planner           |
| `validate_execution_plan`    | Critical                                           | RiskGovernor, Order Router  |
| `place_live_order`           | Critical + RiskGovernor + human-gated account mode | Live Execution              |
| `close_live_position`        | Critical + RiskGovernor                            | Live Execution, Kill Switch |
| `cancel_live_order`          | Critical                                           | Live Execution              |
| `modify_live_order`          | Critical + RiskGovernor                            | Live Execution              |
| `get_live_account_info`      | Read-only                                          | RiskGovernor                |
| `get_live_positions`         | Read-only                                          | RiskGovernor                |
| `get_live_pending_orders`    | Read-only                                          | RiskGovernor                |
| `get_broker_heartbeat`       | Read-only                                          | Execution Monitor           |
| `validate_broker_connection` | Critical/analysis                                  | Execution Monitor           |
| `route_order_to_broker`      | Critical                                           | Order Router                |
| `verify_risk_approval_token` | Critical                                           | Order Router                |
| `record_broker_response`     | Critical/write                                     | Order Router, Audit         |

## Q. MT5 and cTrader bridge tools

| Tool                       | Type      | Used by        |
| -------------------------- | --------- | -------------- |
| `mt5_get_account_info`     | Read-only | MT5 Bridge     |
| `mt5_get_symbol_info`      | Read-only | MT5 Bridge     |
| `mt5_get_latest_tick`      | Read-only | MT5 Bridge     |
| `mt5_get_positions`        | Read-only | MT5 Bridge     |
| `mt5_get_orders`           | Read-only | MT5 Bridge     |
| `mt5_place_order`          | Critical  | MT5 Bridge     |
| `mt5_close_position`       | Critical  | MT5 Bridge     |
| `mt5_cancel_order`         | Critical  | MT5 Bridge     |
| `mt5_modify_order`         | Critical  | MT5 Bridge     |
| `ctrader_get_account_info` | Read-only | cTrader Bridge |
| `ctrader_get_symbol_info`  | Read-only | cTrader Bridge |
| `ctrader_get_latest_tick`  | Read-only | cTrader Bridge |
| `ctrader_get_positions`    | Read-only | cTrader Bridge |
| `ctrader_get_orders`       | Read-only | cTrader Bridge |
| `ctrader_place_order`      | Critical  | cTrader Bridge |
| `ctrader_close_position`   | Critical  | cTrader Bridge |
| `ctrader_cancel_order`     | Critical  | cTrader Bridge |
| `ctrader_modify_order`     | Critical  | cTrader Bridge |

## R. Kill switch and incident tools

| Tool                         | Type                        | Used by                          |
| ---------------------------- | --------------------------- | -------------------------------- |
| `check_kill_switch_status`   | Read-only                   | CEO, Execution                   |
| `trigger_kill_switch`        | Critical                    | RiskGovernor, Audit, Kill Switch |
| `clear_kill_switch`          | Critical + human approval   | Board Liaison                    |
| `pause_all_trading`          | Critical                    | Kill Switch                      |
| `pause_new_entries`          | Critical                    | Kill Switch                      |
| `flatten_all_positions`      | Critical + policy-dependent | Kill Switch                      |
| `disable_strategy_execution` | Critical                    | Kill Switch                      |
| `create_incident_report`     | Write                       | Incident Agent                   |
| `read_incident_report`       | Read-only                   | CEO, Audit                       |
| `escalate_incident_to_board` | Critical                    | Incident Agent                   |
| `mark_incident_resolved`     | Critical + human approval   | Board Liaison                    |

## S. Reporting tools

| Tool                       | Type      | Used by                   |
| -------------------------- | --------- | ------------------------- |
| `create_daily_report`      | Write     | Performance Reporter      |
| `create_weekly_report`     | Write     | Performance Reporter      |
| `create_monthly_report`    | Write     | Performance Reporter      |
| `create_board_report`      | Write     | CEO, Performance Reporter |
| `create_strategy_report`   | Write     | Strategy Documentation    |
| `create_backtest_report`   | Write     | Backtest Analyst          |
| `create_risk_report`       | Write     | Risk Reviewer             |
| `create_compliance_report` | Write     | Prop Firm Compliance      |
| `create_audit_report`      | Write     | Audit Agent               |
| `export_report_markdown`   | Write     | Reporting Agent           |
| `export_report_pdf`        | Write     | Reporting Agent           |
| `read_report`              | Read-only | CEO                       |
| `list_reports`             | Read-only | CEO                       |

## T. Audit tools

| Tool                                   | Type           | Used by    |
| -------------------------------------- | -------------- | ---------- |
| `append_audit_log`                     | Critical/write | All agents |
| `read_audit_log`                       | Read-only      | Audit      |
| `verify_audit_chain`                   | Critical       | Audit      |
| `verify_tool_call_logged`              | Critical       | Audit      |
| `verify_trade_has_risk_approval`       | Critical       | Audit      |
| `verify_strategy_lifecycle_compliance` | Critical       | Audit      |
| `verify_no_forbidden_tool_use`         | Critical       | Audit      |
| `verify_no_policy_file_tampering`      | Critical       | Audit      |
| `create_audit_finding`                 | Write          | Audit      |
| `escalate_audit_finding`               | Critical       | Audit      |
| `lock_audit_record`                    | Critical       | Audit      |
| `delete_audit_record`                  | Forbidden      | No agent   |

## U. Cost and model-routing tools

| Tool                                   | Type           | Used by             |
| -------------------------------------- | -------------- | ------------------- |
| `record_model_call_cost`               | Write          | Cost Optimizer      |
| `get_model_usage_by_agent`             | Read-only      | Cost Optimizer      |
| `get_model_usage_by_workflow`          | Read-only      | Cost Optimizer      |
| `get_backtest_compute_cost`            | Read-only      | Cost Optimizer      |
| `recommend_model_route`                | Write/analysis | Cost Optimizer      |
| `enforce_model_budget`                 | Critical       | Cost Optimizer      |
| `create_cost_report`                   | Write          | Cost Optimizer      |
| `disable_noncritical_agent_for_budget` | Critical       | Cost Optimizer, CEO |

## V. Frontend and page-action tools

| Tool                          | Type      | Used by                 |
| ----------------------------- | --------- | ----------------------- |
| `get_current_page_context`    | Read-only | Dashboard Page Operator |
| `get_active_entity_context`   | Read-only | Dashboard Page Operator |
| `get_active_tab`              | Read-only | Dashboard Page Operator |
| `get_visible_metrics`         | Read-only | Dashboard Page Operator |
| `get_visible_table_rows`      | Read-only | Dashboard Page Operator |
| `navigate_to_page`            | Write/UI  | Dashboard Page Operator |
| `switch_tab`                  | Write/UI  | Dashboard Page Operator |
| `apply_filter`                | Write/UI  | Dashboard Page Operator |
| `clear_filter`                | Write/UI  | Dashboard Page Operator |
| `open_strategy_detail`        | Write/UI  | Dashboard Page Operator |
| `open_backtest_detail`        | Write/UI  | Dashboard Page Operator |
| `open_risk_report`            | Write/UI  | Dashboard Page Operator |
| `open_board_approval_request` | Write/UI  | Dashboard Page Operator |

# 4. Clean canonical tool registry

This is the condensed version I would start with in `tool_registry.py`.

```python
READ_ONLY_TOOLS = [
    "read_constitution",
    "read_risk_policy",
    "read_agent_permissions",
    "read_strategy_lifecycle_policy",
    "get_task_tree",
    "get_task_status",
    "list_active_tasks",
    "get_agent_status",
    "get_agent_registry",
    "read_evidence_ref",
    "list_evidence_refs",
    "search_institutional_memory",
    "search_strategy_memory",
    "search_backtest_memory",
    "list_symbols",
    "get_symbol_metadata",
    "get_ohlcv_data",
    "get_tick_data",
    "get_spread_history",
    "get_session_calendar",
    "get_economic_calendar",
    "get_high_impact_news_events",
    "get_latest_price",
    "get_latest_tick",
    "get_data_freshness",
    "read_strategy_spec",
    "read_strategy_code",
    "read_backtest_result",
    "list_backtest_runs",
    "read_robustness_result",
    "get_account_snapshot",
    "get_open_positions",
    "get_pending_orders",
    "get_strategy_allocations",
    "get_strategy_statuses",
    "get_paper_account_snapshot",
    "get_paper_positions",
    "get_paper_trade_log",
    "get_live_account_info",
    "get_live_positions",
    "get_live_pending_orders",
    "get_broker_heartbeat",
    "check_kill_switch_status",
    "read_report",
    "list_reports",
    "read_audit_log",
    "get_current_page_context",
    "get_active_entity_context",
    "get_active_tab",
    "get_visible_metrics",
    "get_visible_table_rows",
]

WRITE_TOOLS = [
    "create_agent_task",
    "assign_agent_task",
    "start_agent_task",
    "complete_agent_task",
    "fail_agent_task",
    "block_agent_task",
    "create_child_task",
    "create_evidence_ref",
    "save_research_report",
    "save_strategy_memory",
    "save_performance_memory",
    "save_lesson_learned",
    "create_market_intelligence_report",
    "create_technical_analysis_report",
    "create_strategy_idea",
    "score_strategy_idea",
    "rank_strategy_ideas",
    "create_strategy_spec",
    "update_strategy_spec",
    "validate_strategy_spec",
    "generate_strategy_code",
    "save_strategy_code",
    "generate_strategy_tests",
    "run_strategy_unit_tests",
    "run_strategy_static_checks",
    "create_backtest_request",
    "run_backtest",
    "cancel_backtest",
    "save_backtest_config",
    "save_backtest_trades",
    "save_backtest_orders",
    "save_backtest_deals",
    "save_backtest_equity_curve",
    "save_backtest_metrics",
    "create_backtest_report",
    "calculate_trade_metrics",
    "calculate_return_metrics",
    "calculate_drawdown_metrics",
    "calculate_ratio_metrics",
    "calculate_risk_metrics",
    "calculate_efficiency_metrics",
    "calculate_distribution_metrics",
    "calculate_benchmark_metrics",
    "run_statistical_tests",
    "run_parameter_sweep",
    "run_walk_forward_optimization",
    "run_second_oos_test",
    "run_spread_stress_test",
    "run_slippage_stress_test",
    "create_robustness_scorecard",
    "create_risk_review",
    "create_prop_firm_compliance_report",
    "start_paper_trading",
    "stop_paper_trading",
    "place_paper_order",
    "close_paper_position",
    "cancel_paper_order",
    "create_daily_report",
    "create_weekly_report",
    "create_monthly_report",
    "create_board_report",
    "create_strategy_report",
    "create_risk_report",
    "create_compliance_report",
    "create_audit_report",
    "export_report_markdown",
    "export_report_pdf",
    "record_model_call_cost",
    "create_cost_report",
    "navigate_to_page",
    "switch_tab",
    "apply_filter",
    "clear_filter",
]

CRITICAL_TOOLS = [
    "validate_agent_permission",
    "request_human_approval",
    "record_human_approval",
    "reject_human_approval",
    "create_board_approval_request",
    "cancel_agent_task",
    "disable_agent",
    "enable_agent",
    "update_agent_registry",
    "lock_evidence_record",
    "verify_evidence_integrity",
    "set_strategy_lifecycle_state",
    "request_strategy_promotion",
    "request_strategy_demotion",
    "request_strategy_retirement",
    "lock_strategy_code_version",
    "lock_backtest_result",
    "calculate_position_risk",
    "calculate_trade_risk",
    "calculate_portfolio_exposure",
    "calculate_symbol_exposure",
    "calculate_currency_cluster_exposure",
    "calculate_usd_cluster_exposure",
    "calculate_correlation_matrix",
    "calculate_correlation_impact",
    "calculate_margin_impact",
    "calculate_var",
    "calculate_cvar",
    "check_daily_loss_limit",
    "check_total_loss_limit",
    "check_monthly_drawdown_limit",
    "check_portfolio_drawdown_limit",
    "check_prop_firm_daily_loss",
    "check_prop_firm_total_loss",
    "check_prop_firm_news_window",
    "check_prop_firm_weekend_rule",
    "check_prop_firm_overnight_rule",
    "check_forbidden_practices",
    "check_ea_automation_compliance",
    "check_allocation_compliance",
    "check_best_day_rule",
    "request_risk_approval",
    "approve_trade_proposal",
    "reject_trade_proposal",
    "issue_risk_approval_token",
    "revoke_risk_approval_token",
    "request_allocation_increase",
    "set_strategy_allocation",
    "pause_strategy",
    "resume_strategy",
    "retire_strategy",
    "request_live_activation",
    "activate_live_trading",
    "deactivate_live_trading",
    "create_trade_proposal",
    "create_execution_plan",
    "validate_execution_plan",
    "place_live_order",
    "close_live_position",
    "cancel_live_order",
    "modify_live_order",
    "route_order_to_broker",
    "verify_risk_approval_token",
    "record_broker_response",
    "mt5_place_order",
    "mt5_close_position",
    "mt5_cancel_order",
    "mt5_modify_order",
    "ctrader_place_order",
    "ctrader_close_position",
    "ctrader_cancel_order",
    "ctrader_modify_order",
    "trigger_kill_switch",
    "clear_kill_switch",
    "pause_all_trading",
    "pause_new_entries",
    "flatten_all_positions",
    "disable_strategy_execution",
    "escalate_incident_to_board",
    "mark_incident_resolved",
    "append_audit_log",
    "verify_audit_chain",
    "verify_tool_call_logged",
    "verify_trade_has_risk_approval",
    "verify_strategy_lifecycle_compliance",
    "verify_no_forbidden_tool_use",
    "verify_no_policy_file_tampering",
    "escalate_audit_finding",
    "lock_audit_record",
    "enforce_model_budget",
    "disable_noncritical_agent_for_budget",
]
```

# 5. Tools that require RiskGovernor approval

These should never execute unless `RiskGovernor` returns a valid non-expired approval token.

```python
REQUIRES_RISK_GOVERNOR_APPROVAL = [
    "place_paper_order",
    "close_paper_position",
    "create_trade_proposal",
    "create_execution_plan",
    "validate_execution_plan",
    "place_live_order",
    "close_live_position",
    "modify_live_order",
    "route_order_to_broker",
    "mt5_place_order",
    "mt5_close_position",
    "mt5_modify_order",
    "ctrader_place_order",
    "ctrader_close_position",
    "ctrader_modify_order",
    "set_strategy_allocation",
    "request_allocation_increase",
    "resume_strategy",
]
```

# 6. Tools that require human approval

These should require explicit Board approval from you.

```python
REQUIRES_HUMAN_APPROVAL = [
    "activate_live_trading",
    "enable_agent",
    "update_agent_registry",
    "update_risk_policy",
    "update_agent_permissions",
    "update_strategy_lifecycle_policy",
    "set_strategy_allocation",
    "request_allocation_increase",
    "resume_strategy",
    "retire_strategy",
    "clear_kill_switch",
    "delete_market_data",
    "delete_strategy_code",
    "delete_backtest_result",
    "request_live_activation",
    "flatten_all_positions",  # unless emergency policy allows automatic flatten
]
```

# 7. Tools that must be forbidden to all LLM agents

```python
FORBIDDEN_TO_ALL_LLM_AGENTS = [
    "delete_audit_record",
    "edit_audit_record",
    "bypass_risk_governor",
    "bypass_kill_switch",
    "bypass_human_approval",
    "edit_broker_credentials",
    "disable_audit_logging",
    "disable_risk_logging",
    "modify_risk_thresholds_without_human_approval",
    "place_live_order_without_risk_token",
    "increase_live_allocation_without_human_approval",
    "change_prop_firm_compliance_limits",
]
```

# 8. Recommended v0.1 tool list

For the first working version, do not implement everything. Start with this.

```python
V0_1_TOOLS = [
    # Policy
    "read_constitution",
    "read_risk_policy",
    "read_agent_permissions",
    "read_strategy_lifecycle_policy",
    "validate_agent_permission",
    "append_audit_log",

    # Tasks
    "create_agent_task",
    "assign_agent_task",
    "complete_agent_task",
    "fail_agent_task",
    "get_task_tree",

    # Data
    "list_symbols",
    "get_symbol_metadata",
    "get_ohlcv_data",
    "get_spread_history",
    "get_high_impact_news_events",
    "get_data_freshness",
    "validate_data_quality",

    # Research
    "create_market_intelligence_report",
    "create_technical_analysis_report",
    "create_strategy_idea",
    "score_strategy_idea",
    "rank_strategy_ideas",

    # Strategy
    "create_strategy_spec",
    "validate_strategy_spec",
    "read_strategy_spec",
    "generate_strategy_code",
    "save_strategy_code",
    "generate_strategy_tests",
    "run_strategy_unit_tests",
    "run_lookahead_bias_check",
    "run_repainting_check",

    # Backtest
    "create_backtest_request",
    "run_backtest",
    "read_backtest_result",
    "save_backtest_metrics",
    "create_backtest_report",

    # Analytics
    "calculate_trade_metrics",
    "calculate_return_metrics",
    "calculate_drawdown_metrics",
    "calculate_ratio_metrics",
    "calculate_risk_metrics",
    "run_statistical_tests",

    # Risk / Prop Firm
    "calculate_trade_risk",
    "calculate_portfolio_exposure",
    "check_daily_loss_limit",
    "check_total_loss_limit",
    "check_prop_firm_daily_loss",
    "check_prop_firm_total_loss",
    "check_prop_firm_news_window",
    "check_prop_firm_weekend_rule",
    "check_prop_firm_overnight_rule",
    "check_best_day_rule",
    "create_risk_review",
    "create_prop_firm_compliance_report",

    # Paper execution only
    "start_paper_trading",
    "place_paper_order",
    "close_paper_position",
    "get_paper_account_snapshot",
    "get_paper_positions",
    "get_paper_trade_log",

    # Reporting
    "create_daily_report",
    "create_board_report",
    "create_audit_report",
]
```

The safest implementation sequence is: start with the **v0.1 agents** and **v0.1 tools**, then add live execution tools only after RiskGovernor, audit logging, kill switch, prop-firm compliance checks, and human approval flow are fully tested.

[1]: https://tradingagents-ai.github.io/?utm_source=chatgpt.com "TradingAgents: Multi-Agents LLM Financial Trading Framework"
[2]: https://docs.cloud.google.com/gemini-enterprise-agent-platform/build/adk?utm_source=chatgpt.com "Agent Development Kit | Gemini Enterprise Agent Platform"
[3]: https://modelcontextprotocol.io/specification/2025-06-18/server/tools?utm_source=chatgpt.com "Tools"


Yes — the tools should live inside HaruQuant as a **tool layer**, separate from the agents. Agents should **call tools**, not contain business logic directly.

ADK treats agents and tools as separate building blocks for production workflows, and MCP treats tools as named executable capabilities with schemas, discovery, invocation, and safety controls. That separation is exactly what you want for HaruQuant. ([Google Cloud Documentation][1])

# 1. Where should the tools be?

Recommended structure:

```text
backend/
  app/
    agents/
      ceo/
      planner/
      research/
      strategy_creator/
      strategy_reviewer/
      backtest/
      risk_reviewer/
      portfolio_manager/
      execution/
      audit/

    tools/
      __init__.py
      registry.py
      schemas.py
      permissions.py

      policy_tools.py
      task_tools.py
      memory_tools.py
      data_tools.py
      research_tools.py
      strategy_tools.py
      code_tools.py
      backtest_tools.py
      analytics_tools.py
      optimization_tools.py
      robustness_tools.py
      statistical_tools.py
      risk_tools.py
      prop_firm_tools.py
      portfolio_tools.py
      paper_execution_tools.py
      live_execution_tools.py
      broker_tools.py
      kill_switch_tools.py
      reporting_tools.py
      audit_tools.py
      cost_tools.py
      frontend_tools.py

    risk/
      governor.py
      approvals.py
      kill_switch.py
      prop_firm_compliance.py
      consistency.py

    execution/
      paper_broker.py
      order_router.py
      mt5_bridge.py
      ctrader_bridge.py

    services/
      data_service.py
      backtest_service.py
      analytics_service.py
      strategy_service.py
      portfolio_service.py
      reporting_service.py
      audit_service.py

    db/
      models/
      repositories/
```

The important split is this:

```text
Agent = reasoning, planning, delegation, explanation
Tool = controlled action wrapper
Service = real business logic
Repository = database access
```

So a tool should usually be a thin wrapper around a service.

Example:

```text
CEO Agent
  -> calls create_strategy_spec tool
      -> calls StrategyService.create_spec()
          -> writes to database
          -> writes audit log
```

Do **not** put the full business logic inside the agent prompt or agent file.

---

# 2. Tool placement by category

## Policy tools

```text
backend/app/tools/policy_tools.py
```

Contains:

```python
read_constitution()
read_risk_policy()
read_agent_permissions()
read_strategy_lifecycle_policy()
validate_against_constitution()
validate_against_risk_policy()
validate_agent_permission()
```

Used by:

```text
CEO Agent
Planner Agent
Orchestrator
Risk Reviewer
Audit Agent
```

---

## Task tools

```text
backend/app/tools/task_tools.py
```

Contains:

```python
create_agent_task()
assign_agent_task()
start_agent_task()
complete_agent_task()
fail_agent_task()
block_agent_task()
create_child_task()
get_task_tree()
get_task_status()
list_active_tasks()
```

Used by:

```text
CEO Agent
Planner Agent
Conversation Orchestrator
Task Manager
Audit Agent
```

---

## Memory and evidence tools

```text
backend/app/tools/memory_tools.py
```

Contains:

```python
create_evidence_ref()
read_evidence_ref()
list_evidence_refs()
save_research_report()
read_research_report()
save_strategy_memory()
read_strategy_memory()
save_performance_memory()
read_performance_memory()
save_lesson_learned()
search_institutional_memory()
search_strategy_memory()
search_backtest_memory()
verify_evidence_integrity()
```

Used by almost all agents.

---

## Data tools

```text
backend/app/tools/data_tools.py
```

Contains:

```python
list_symbols()
get_symbol_metadata()
get_ohlcv_data()
get_tick_data()
get_spread_history()
get_session_calendar()
get_economic_calendar()
get_high_impact_news_events()
get_latest_price()
get_latest_tick()
get_data_freshness()
validate_data_quality()
detect_missing_bars()
detect_duplicate_ticks()
detect_bad_spreads()
normalize_symbol_data()
```

Used by:

```text
Research Agent
Market Intelligence Agent
Technical Analyst Agent
Backtest Agent
RiskGovernor
Prop Firm Compliance Agent
Execution Planner
```

---

## Research tools

```text
backend/app/tools/research_tools.py
```

Contains:

```python
create_market_intelligence_report()
create_technical_analysis_report()
create_strategy_idea()
score_strategy_idea()
rank_strategy_ideas()
search_internal_research()
search_external_research()
summarize_research_source()
create_bull_case()
create_bear_case()
create_research_debate_summary()
```

Used by:

```text
Research Agent
Market Intelligence Agent
Strategy Scout Agent
Technical Analyst Agent
Bull Researcher
Bear Researcher
```

---

## Strategy tools

```text
backend/app/tools/strategy_tools.py
```

Contains:

```python
create_strategy_spec()
read_strategy_spec()
update_strategy_spec()
validate_strategy_spec()
reject_strategy_spec()
approve_strategy_spec_for_code_review()
create_strategy_version()
compare_strategy_versions()
set_strategy_lifecycle_state()
request_strategy_promotion()
request_strategy_demotion()
request_strategy_retirement()
```

Used by:

```text
Strategy Creator Agent
Strategy Spec Validator Agent
Strategy Reviewer Agent
Portfolio Manager Agent
CEO Agent
```

---

## Code tools

```text
backend/app/tools/code_tools.py
```

Contains:

```python
generate_strategy_code()
read_strategy_code()
save_strategy_code()
update_strategy_code()
generate_strategy_tests()
run_strategy_unit_tests()
run_strategy_static_checks()
run_lookahead_bias_check()
run_repainting_check()
run_parameter_sanity_check()
create_strategy_code_hash()
lock_strategy_code_version()
```

Used by:

```text
Strategy Codegen Agent
Strategy Test Generator Agent
Strategy Reviewer Agent
Audit Agent
```

---

## Backtest tools

```text
backend/app/tools/backtest_tools.py
```

Contains:

```python
create_backtest_request()
run_backtest()
cancel_backtest()
read_backtest_result()
list_backtest_runs()
compare_backtest_runs()
save_backtest_config()
save_backtest_trades()
save_backtest_orders()
save_backtest_deals()
save_backtest_equity_curve()
save_backtest_metrics()
create_backtest_report()
lock_backtest_result()
```

Used by:

```text
Backtest Agent
Backtest Analyst Agent
Risk Reviewer Agent
CEO Agent
```

---

## Analytics tools

```text
backend/app/tools/analytics_tools.py
```

Contains wrappers around your analytics stack:

```python
calculate_trade_metrics()
calculate_return_metrics()
calculate_drawdown_metrics()
calculate_ratio_metrics()
calculate_risk_metrics()
calculate_efficiency_metrics()
calculate_distribution_metrics()
calculate_benchmark_metrics()
run_statistical_tests()
calculate_long_short_split()
calculate_session_performance()
calculate_monthly_performance()
calculate_regime_performance()
calculate_cost_sensitivity()
```

Used by:

```text
Backtest Agent
Backtest Analyst Agent
Risk Reviewer Agent
Statistical Validation Agent
Performance Reporter Agent
```

---

## Risk tools

```text
backend/app/tools/risk_tools.py
```

Contains:

```python
get_account_snapshot()
get_open_positions()
get_pending_orders()
calculate_position_risk()
calculate_trade_risk()
calculate_portfolio_exposure()
calculate_symbol_exposure()
calculate_currency_cluster_exposure()
calculate_usd_cluster_exposure()
calculate_correlation_matrix()
calculate_correlation_impact()
calculate_margin_impact()
calculate_var()
calculate_cvar()
check_daily_loss_limit()
check_total_loss_limit()
check_portfolio_drawdown_limit()
request_risk_approval()
approve_trade_proposal()
reject_trade_proposal()
issue_risk_approval_token()
revoke_risk_approval_token()
```

Used by:

```text
RiskGovernor
Risk Reviewer Agent
Execution Planner Agent
Portfolio Manager Agent
Audit Agent
```

The actual deterministic logic should live in:

```text
backend/app/risk/governor.py
```

The tool is just the interface.

---

## Prop-firm compliance tools

```text
backend/app/tools/prop_firm_tools.py
```

Contains:

```python
check_prop_firm_daily_loss()
check_prop_firm_total_loss()
check_prop_firm_profit_target()
check_prop_firm_news_window()
check_prop_firm_weekend_rule()
check_prop_firm_overnight_rule()
check_forbidden_practices()
check_ea_automation_compliance()
check_allocation_compliance()
calculate_consistency_score()
check_best_day_rule_threshold()
create_prop_firm_compliance_report()
```

Used by:

```text
Prop Firm Compliance Agent
RiskGovernor
Consistency Rule Agent
Audit Agent
Execution Planner
```

The real logic should live in:

```text
backend/app/risk/prop_firm_compliance.py
backend/app/risk/consistency.py
```

---

## Paper execution tools

```text
backend/app/tools/paper_execution_tools.py
```

Contains:

```python
start_paper_trading()
stop_paper_trading()
place_paper_order()
close_paper_position()
cancel_paper_order()
get_paper_account_snapshot()
get_paper_positions()
get_paper_trade_log()
simulate_spread()
simulate_slippage()
simulate_commission()
simulate_swap()
```

Used by:

```text
Paper Execution Agent
RiskGovernor
Performance Reporter
Audit Agent
```

Real logic lives in:

```text
backend/app/execution/paper_broker.py
```

---

## Live execution tools

```text
backend/app/tools/live_execution_tools.py
```

Contains:

```python
request_live_activation()
activate_live_trading()
deactivate_live_trading()
create_trade_proposal()
create_execution_plan()
validate_execution_plan()
place_live_order()
close_live_position()
cancel_live_order()
modify_live_order()
```

Used by:

```text
Execution Planner Agent
Live Execution Agent
RiskGovernor
Order Router
Audit Agent
```

These are **critical tools** and should not exist until RiskGovernor, audit logging, kill switch, and human approval are implemented and tested.

MCP’s tool guidance specifically recommends clear visibility and human confirmation for sensitive tool invocations, which applies directly to live trading tools. ([Model Context Protocol][2])

---

## Broker tools

```text
backend/app/tools/broker_tools.py
```

Contains:

```python
mt5_get_account_info()
mt5_get_symbol_info()
mt5_get_latest_tick()
mt5_get_positions()
mt5_get_orders()
mt5_place_order()
mt5_close_position()
mt5_cancel_order()
mt5_modify_order()

ctrader_get_account_info()
ctrader_get_symbol_info()
ctrader_get_latest_tick()
ctrader_get_positions()
ctrader_get_orders()
ctrader_place_order()
ctrader_close_position()
ctrader_cancel_order()
ctrader_modify_order()
```

Real logic lives in:

```text
backend/app/execution/mt5_bridge.py
backend/app/execution/ctrader_bridge.py
```

Agents should not call broker bridge functions directly. They should call controlled execution tools, which then verify permissions, approvals, and RiskGovernor tokens.

---

## Kill switch tools

```text
backend/app/tools/kill_switch_tools.py
```

Contains:

```python
check_kill_switch_status()
trigger_kill_switch()
clear_kill_switch()
pause_all_trading()
pause_new_entries()
flatten_all_positions()
disable_strategy_execution()
```

Real logic lives in:

```text
backend/app/risk/kill_switch.py
```

---

## Reporting tools

```text
backend/app/tools/reporting_tools.py
```

Contains:

```python
create_daily_report()
create_weekly_report()
create_monthly_report()
create_board_report()
create_strategy_report()
create_backtest_report()
create_risk_report()
create_compliance_report()
create_audit_report()
export_report_markdown()
export_report_pdf()
read_report()
list_reports()
```

Used by:

```text
Performance Reporter Agent
CEO Agent
Audit Agent
Board Liaison Agent
```

---

## Audit tools

```text
backend/app/tools/audit_tools.py
```

Contains:

```python
append_audit_log()
read_audit_log()
verify_audit_chain()
verify_tool_call_logged()
verify_trade_has_risk_approval()
verify_strategy_lifecycle_compliance()
verify_no_forbidden_tool_use()
verify_no_policy_file_tampering()
create_audit_finding()
escalate_audit_finding()
lock_audit_record()
```

Used by every agent.

No agent should have:

```python
delete_audit_record()
edit_audit_record()
```

Those should not exist as callable tools.

---

# 3. Should you create all tools first?

No — not fully.

The best approach is:

```text
Define all tool contracts first.
Implement only the tools needed for the next vertical slice.
```

OWASP’s AI Agent Security guidance recommends least privilege, per-tool scoping, separate tool sets for different trust levels, and explicit authorization for sensitive operations. That means building a huge tool surface before you need it increases risk and complexity. ([OWASP Cheat Sheet Series][3])

So the correct strategy is **contract-first, implementation-incremental**.

# 4. What to create first

You should first create the **tool registry framework**, not every tool implementation.

## Step 1 — Create the registry

```text
backend/app/tools/registry.py
backend/app/tools/schemas.py
backend/app/tools/permissions.py
```

Each tool gets metadata:

```python
@dataclass
class ToolDefinition:
    name: str
    description: str
    category: str
    risk_level: str  # read_only | write | critical
    input_schema: dict
    output_schema: dict
    allowed_agents: list[str]
    requires_audit: bool = True
    requires_risk_governor: bool = False
    requires_human_approval: bool = False
    enabled: bool = True
```

## Step 2 — Register all planned tools as stubs

Example:

```python
TOOL_REGISTRY = {
    "run_backtest": ToolDefinition(
        name="run_backtest",
        description="Run a reproducible HaruQuant backtest.",
        category="backtest",
        risk_level="write",
        input_schema=BacktestRequest.model_json_schema(),
        output_schema=BacktestResultSummary.model_json_schema(),
        allowed_agents=["backtest_agent"],
        requires_audit=True,
        requires_risk_governor=False,
        requires_human_approval=False,
        enabled=True,
    ),

    "place_live_order": ToolDefinition(
        name="place_live_order",
        description="Place a live broker order after all approvals.",
        category="live_execution",
        risk_level="critical",
        input_schema=LiveOrderRequest.model_json_schema(),
        output_schema=ExecutionResult.model_json_schema(),
        allowed_agents=["live_execution_agent"],
        requires_audit=True,
        requires_risk_governor=True,
        requires_human_approval=False,
        enabled=False,
    ),
}
```

Notice `place_live_order` is registered but disabled.

That is what you want.

---

# 5. What to implement first

For v0.1, implement only the tools needed for this workflow:

```text
CEO
→ Planner
→ Strategy Creator
→ Strategy Reviewer
→ Codegen
→ Tests
→ Backtest
→ Analytics
→ Risk Review
→ Final Memo
```

## v0.1 tool implementation list

```text
Policy tools:
- read_constitution
- read_risk_policy
- read_agent_permissions
- read_strategy_lifecycle_policy
- validate_agent_permission

Task tools:
- create_agent_task
- assign_agent_task
- complete_agent_task
- fail_agent_task
- get_task_tree

Audit tools:
- append_audit_log
- read_audit_log
- verify_tool_call_logged

Data tools:
- list_symbols
- get_symbol_metadata
- get_ohlcv_data
- get_spread_history
- get_data_freshness
- validate_data_quality

Strategy tools:
- create_strategy_spec
- validate_strategy_spec
- read_strategy_spec
- approve_strategy_spec_for_code_review

Code tools:
- generate_strategy_code
- save_strategy_code
- generate_strategy_tests
- run_strategy_unit_tests
- run_lookahead_bias_check
- run_repainting_check
- create_strategy_code_hash

Backtest tools:
- create_backtest_request
- run_backtest
- read_backtest_result
- save_backtest_metrics
- create_backtest_report

Analytics tools:
- calculate_trade_metrics
- calculate_return_metrics
- calculate_drawdown_metrics
- calculate_ratio_metrics
- calculate_risk_metrics
- run_statistical_tests

Risk tools:
- calculate_trade_risk
- calculate_portfolio_exposure
- check_daily_loss_limit
- check_total_loss_limit
- create_risk_review

Prop-firm tools:
- check_prop_firm_daily_loss
- check_prop_firm_total_loss
- check_prop_firm_news_window
- check_prop_firm_weekend_rule
- check_prop_firm_overnight_rule
- check_best_day_rule
- create_prop_firm_compliance_report

Reporting tools:
- create_backtest_report
- create_risk_report
- create_board_report
```

That is enough to build a real first version.

---

# 6. Tools you should not implement yet

Delay these until after v0.1 is working:

```text
- place_live_order
- close_live_position
- modify_live_order
- mt5_place_order
- mt5_close_position
- ctrader_place_order
- ctrader_close_position
- activate_live_trading
- set_strategy_allocation
- resume_strategy
- clear_kill_switch
- flatten_all_positions
```

These are high-impact tools. NIST’s AI RMF frames AI risk management around governance, mapping, measuring, and managing risks across the lifecycle, which supports delaying high-impact autonomy until the system has governance, observability, and control. ([NIST][4])

---

# 7. Recommended build order

Use this exact sequence:

## Phase A — Tool foundation

```text
1. ToolDefinition schema
2. Tool registry
3. Permission checker
4. Audit wrapper
5. Tool execution wrapper
6. Error handling
7. Tool result schema
```

## Phase B — Read-only tools

```text
1. Policy readers
2. Data readers
3. Strategy readers
4. Backtest readers
5. Report readers
```

## Phase C — Safe write tools

```text
1. Task tools
2. Evidence tools
3. Strategy spec tools
4. Code generation tools
5. Backtest tools
6. Report generation tools
```

## Phase D — Deterministic risk tools

```text
1. Risk calculation tools
2. Prop-firm compliance tools
3. Risk approval token system
4. Kill switch status checker
```

## Phase E — Paper execution tools

```text
1. Paper account state
2. Paper order placement
3. Paper position close
4. Paper trade log
5. Paper reporting
```

## Phase F — Live execution tools

Only after all previous phases pass acceptance tests.

```text
1. Live activation request
2. Human approval flow
3. Broker heartbeat
4. Risk token validation
5. Order router
6. Broker bridge
7. Live order placement
```

---

# 8. The practical answer

Do **not** spend weeks building 200 tools before agents.

Do this instead:

```text
1. Define the full tool catalog.
2. Implement the tool registry.
3. Implement v0.1 tools only.
4. Build v0.1 agents.
5. Test one full vertical workflow.
6. Add more tools only when a new agent workflow needs them.
```

So the development dependency should be:

```text
Tool contracts first
→ Minimal working tool layer
→ Minimal agent team
→ End-to-end strategy workflow
→ Paper trading tools
→ Portfolio tools
→ Live trading tools last
```

That gives you the best balance between architecture discipline and actual progress.

[1]: https://docs.cloud.google.com/gemini-enterprise-agent-platform/build/adk?utm_source=chatgpt.com "Agent Development Kit | Gemini Enterprise Agent Platform"
[2]: https://modelcontextprotocol.io/specification/draft/server/tools?utm_source=chatgpt.com "Tools"
[3]: https://cheatsheetseries.owasp.org/cheatsheets/AI_Agent_Security_Cheat_Sheet.html?utm_source=chatgpt.com "AI Agent Security Cheat Sheet"
[4]: https://www.nist.gov/itl/ai-risk-management-framework?utm_source=chatgpt.com "AI Risk Management Framework | NIST"

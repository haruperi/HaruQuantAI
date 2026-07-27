# HaruQuant Streamlined Risk Policy

**Document:** `risk_policy.md`  
**Recommended path:** `docs/agentic_firm/risk_policy.md`  
**Owner:** Human Board / Haruperi  
**Version:** 2.0.0  
**Status:** Streamlined prop-firm risk baseline  
**Last Updated:** 2026-05-24  
**Python enforcement:** `tools/risk_tools.py`, `runtime/permissions.py`, later `risk/governor.py`  

---

## 1. Purpose

This Risk Policy defines mandatory risk controls for HaruQuant research, backtesting, paper trading, prop-firm simulation, and future live trading.

The core principle is:

> **HaruQuant must stop trading before the prop firm stops the account.**

LLM agents may explain risk, request checks, summarize risk, and recommend actions. Deterministic risk code must approve, reject, size, block, pause, or stop trading.

---

## 2. Standard Prop-Firm Compliance Profile

```yaml
risk_profile:
  name: standard_prop_firm_compliance
  initial_balance: 100000.00

prop_firm_rules:
  max_daily_loss_pct: 5.0
  max_total_loss_pct: 10.0
  max_total_loss_type: static_from_initial_balance
  monthly_profit_target_pct: 10.0
  news_restriction_minutes_before: 10
  news_restriction_minutes_after: 10
  overnight_holding_allowed: false
  weekend_holding_allowed: false
  best_day_rule_pct: 50.0
  automated_trading_allowed: true
  human_approval_required_for_live_activation: true
```

---

## 3. Internal HaruQuant Safety Buffers

HaruQuant uses stricter internal stops than external prop-firm limits.

| Rule | External breach | Warning | Critical | Hard stop |
|---|---:|---:|---:|---:|
| Daily loss | 5.0% | 2.5% | 3.5% | 4.0% |
| Total loss | 10.0% | 5.0% | 7.5% | 8.5% |
| Weekly loss | Internal | 3.0% | 4.5% | 6.0% |
| Monthly drawdown | Internal | 3.0% | 5.0% | 6.0% |
| Portfolio drawdown | Internal | 4.0% | 6.5% | 8.0% |
| Best Day Rule | 50.0% | 40.0% | 45.0% | 50.0% |

The RiskGovernor must enforce internal hard stops, not wait for external breach levels.

---

## 4. Risk Authority

```text
Human Board
→ Constitution
→ Risk Policy
→ RiskGovernor
→ Kill Switch
→ Execution tools
→ Agents
```

Rules:

1. Agents cannot change thresholds.
2. Agents cannot override RiskGovernor.
3. Agents cannot disable Kill Switch.
4. Agents cannot disable audit.
5. Live orders require RiskGovernor approval.
6. Live activation requires Human Board approval.

---

## 5. Trade Risk Limits

```yaml
trade_risk:
  max_risk_per_trade_pct: 0.25
  absolute_max_risk_per_trade_pct: 0.50
  reduce_risk_after_daily_loss_pct: 1.5
  block_new_trades_after_daily_loss_pct: 3.5
```

### Reduced-risk states

| Condition | Max risk per trade |
|---|---:|
| Normal | 0.25% |
| Daily loss > 1.5% | 0.15% |
| Daily loss > 2.5% | 0.10% |
| Daily loss > 3.5% | No new risk-increasing trades |
| Total drawdown > 5.0% | 0.10% |
| Total drawdown > 7.5% | No new trades |

No live trade may be approved without measurable risk.

---

## 6. Loss Limit Calculations

### Daily loss

```text
daily_loss_pct = (daily_reference_equity - current_equity) / initial_balance × 100
```

### Weekly loss

```text
weekly_loss_pct = (week_start_equity - current_equity) / initial_balance × 100
```

### Static total loss floor

```text
minimum_allowed_equity = initial_balance × 0.90
internal_minimum_equity = initial_balance × 0.915
```

### Portfolio drawdown

```text
portfolio_drawdown_pct =
  (portfolio_equity_high_watermark - current_equity)
  / portfolio_equity_high_watermark × 100
```

Risk calculations must include floating P&L, commissions, swaps, and fees.

---

## 7. Exposure Limits

```yaml
exposure:
  max_symbol_risk_pct: 1.0
  max_symbol_nominal_exposure_pct_of_equity: 25.0
  max_correlated_cluster_risk_pct: 1.5
  preferred_pairwise_correlation: 0.50
  max_pairwise_correlation: 0.70
  max_usd_cluster_risk_pct: 2.0
  preferred_usd_cluster_risk_pct: 1.25
  max_usd_cluster_nominal_exposure_pct_of_equity: 50.0
  max_simultaneous_positions_total: 8
  preferred_simultaneous_positions_total: 5
  max_positions_per_symbol: 2
  max_positions_per_strategy: 2
  max_pending_orders_total: 10
```

Reject trades that create excessive symbol, correlated, or USD-cluster exposure.

---

## 8. Strategy Allocation Limits

```yaml
strategies:
  max_live_strategies: 5
  preferred_live_strategies: 3
  max_paper_strategies: 20
  preferred_paper_strategies: 10
  max_live_strategy_risk_allocation_pct: 1.0
  preferred_live_strategy_risk_allocation_pct: 0.5
  max_paper_strategy_risk_allocation_pct: 0.5
```

Allocation increases require risk review, portfolio review, RiskGovernor simulation, Human Board approval, and audit.

---

## 9. Spread and Slippage Filters

```yaml
spread_filter:
  enabled: true
  max_spread_multiplier_vs_median: 2.0
  max_spread_percent_of_atr: 10.0
  block_if_spread_data_missing: true

symbol_spread_limits:
  EURUSD:
    max_spread_points: 15
  GBPUSD:
    max_spread_points: 20
  USDJPY:
    max_spread_points: 20
  XAUUSD:
    max_spread_points: 50
  NAS100:
    max_spread_points: 300

slippage_filter:
  enabled: true
  max_expected_slippage_points: 5
  max_actual_slippage_points: 10
  max_slippage_percent_of_risk: 10.0
  block_after_consecutive_bad_fills: 3
```

If spread or slippage data is missing, live execution must be blocked.

---

## 10. News, Overnight, and Weekend Restrictions

```yaml
news_event_blocks:
  enabled: true
  minutes_before_high_impact_event: 10
  minutes_after_high_impact_event: 10
  pre_news_flatten_minutes_before: 15
  apply_to_new_entries: true
  apply_to_exits: true
  apply_to_stop_loss_hits: true
  apply_to_take_profit_hits: true
  apply_to_pending_order_triggers: true

session_restrictions:
  overnight_holding_allowed: false
  close_before_daily_rollover_minutes: 30
  weekend_holding_allowed: false
  close_before_weekend_minutes: 120
```

Agents may not override news, overnight, or weekend restrictions. Exceptions require Human Board approval and audit.

---

## 11. Consistency / Best Day Rule

```yaml
consistency:
  best_day_rule_pct: 50.0
  warning_pct: 40.0
  critical_pct: 45.0
  hard_limit_pct: 50.0
```

Formula:

```text
best_day_score = best_positive_day_profit / total_positive_days_profit × 100
```

Actions:

| Best Day Score | Action |
|---:|---|
| < 35% | Healthy |
| 35–40% | Monitor |
| > 40% | Warning |
| > 45% | Critical; reduce risk |
| >= 50% | Block pass/promotion claim |

---

## 12. Broker Disconnect Policy

```yaml
broker_disconnect_policy:
  block_new_orders_on_disconnect: true
  cancel_pending_orders_on_critical_disconnect: true
  max_missed_heartbeats: 3
  critical_disconnect_seconds: 30
  require_board_review_after_critical_disconnect: true
```

Live trading resumes only after account, positions, orders, ticks, equity, exposure, RiskGovernor, kill switch, and audit state are refreshed.

---

## 13. Automation Limits

```yaml
automation_limits:
  max_order_requests_per_minute: 20
  max_order_modifications_per_minute: 30
  max_account_queries_per_second: 5
  max_symbol_queries_per_second: 10
  block_duplicate_order_requests: true
  min_seconds_between_identical_orders: 10
```

Duplicate order spam, repeated rejected broker requests, and abnormal retries must trigger restriction or kill-switch review.

---

## 14. Kill Switch Rules

```yaml
kill_switch:
  enabled: true
  default_position_action: block_new_orders_and_alert
  emergency_position_action: close_positions_if_required_to_prevent_rule_breach
  require_board_review_to_resume: true
```

Kill switch triggers include:

1. Daily hard stop at 4.0%.
2. Total hard stop at 8.5%.
3. Weekly hard stop at 6.0%.
4. Monthly hard stop at 6.0%.
5. Portfolio hard stop at 8.0%.
6. RiskGovernor unavailable.
7. Audit logger unavailable.
8. Broker critical disconnect.
9. Live order without risk approval ID.
10. Order size exceeds approved size.
11. Strategy sends duplicate order spam.
12. News, weekend, or overnight violation risk.
13. Best Day hard limit during passing evaluation.

---

## 15. Forbidden Trading Practices

HaruQuant must block:

1. Latency arbitrage.
2. Price-feed arbitrage.
3. Broker error exploitation.
4. Quote stuffing.
5. Toxic order flooding.
6. Unlimited grid trading.
7. Martingale without Board approval and hard risk cap.
8. Averaging down without bounded total risk.
9. Increasing size after losses to recover drawdown.
10. Increasing size merely to hit profit target.
11. Splitting oversized trade into smaller trades to bypass limits.
12. Trading without measurable risk.
13. News-window exploitation.
14. Weekend/overnight rule bypass.

---

## 16. RiskGovernor Enforcement Points

RiskGovernor must evaluate at minimum:

1. Before paper trading admission.
2. Before live trading admission.
3. Before every trade proposal.
4. Before every order placement.
5. Before every order modification.
6. Before every position increase.
7. After every fill.
8. After every close.
9. After every equity update.
10. After every broker heartbeat.
11. Before daily rollover.
12. Before weekend cutoff.
13. Before known high-impact news events.
14. Before Board approval requests that affect risk.

---

## 17. Required Acceptance Tests

The risk implementation must test:

- daily loss warning/critical/hard-stop
- total loss hard stop
- floating P&L included in loss
- risk reduction after drawdown
- correlation rejection
- USD-cluster rejection
- max symbol exposure rejection
- max position count rejection
- spread block
- slippage block
- news block
- overnight/weekend block
- Best Day Rule warning/critical/hard limit
- broker disconnect block
- duplicate order block
- RiskGovernor unavailable block
- audit unavailable block
- kill-switch resume requires Board approval

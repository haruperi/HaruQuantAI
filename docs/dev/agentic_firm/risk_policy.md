# HaruQuant Agentic AI Trading Firm — Risk Policy

**Document:** `risk_policy.md`  
**Target path:** `docs/agentic_firm/risk_policy.md`  
**Version:** 1.0.0  
**Status:** Draft for Board Review  
**Owner:** Human Board / Haruperi  
**Applies to:** HaruQuant multi-agent research, backtesting, paper trading, and live trading workflows  
**Effective date:** 2026-05-03  

---

## 1. Purpose

This Risk Policy defines the mandatory risk controls for the HaruQuant Agentic AI Trading Firm.

The policy exists to ensure that HaruQuant can use multi-agent LLM systems for research, strategy creation, backtesting, monitoring, paper trading, and live-trading assistance without allowing any agent to expose the portfolio to uncontrolled financial, operational, model, or execution risk.

This policy is binding on:

1. CEO Agent.
2. Planner / Orchestrator Agent.
3. Research Agents.
4. Strategy Creator Agent.
5. Strategy Reviewer Agent.
6. Codegen Agent.
7. Backtest Agent.
8. Optimization Comparator Agent.
9. Robustness Agent.
10. Statistical Validation Agent.
11. Risk Reviewer Agent.
12. Portfolio Manager Agent.
13. Execution Planner Agent.
14. Paper Execution Agent.
15. Live Execution Agent.
16. Performance Reporter Agent.
17. Audit Agent.
18. Cost Optimizer Agent.
19. Any future HaruQuant autonomous or semi-autonomous agent.

The core principle is:

> **LLM agents may propose, explain, analyze, and recommend. Only deterministic risk services and explicitly approved execution bridges may enforce, size, approve, or block trades.**

---

## 2. Authority hierarchy

Risk authority follows this order:

```text
Human Board
→ Constitution
→ Risk Policy
→ RiskGovernor
→ Kill Switch
→ Execution Bridge
→ Agents
```

No LLM agent has authority above the RiskGovernor.

No LLM agent may override the Kill Switch.

No LLM agent may change this Risk Policy.

No LLM agent may change `risk_thresholds.yaml`.

No LLM agent may convert a rejected trade into an approved trade.

No LLM agent may convert a paper-trading strategy into a live-trading strategy.

---

## 3. Governance principles

HaruQuant risk governance follows five core principles.

### 3.1 Pre-trade control before execution

Every trade proposal must be checked before order submission.

The system must reject an order before it reaches the broker if the order violates:

1. Risk per trade.
2. Daily loss limit.
3. Weekly loss limit.
4. Portfolio drawdown limit.
5. Symbol exposure limit.
6. Correlation exposure limit.
7. USD-cluster exposure limit.
8. Margin limit.
9. Spread limit.
10. Slippage limit.
11. News-event block.
12. Broker-disconnect rule.
13. Strategy lifecycle rule.
14. Board approval rule.

### 3.2 Paper before live

All strategies must pass research, specification, review, backtest, robustness, statistical validation, risk review, and paper-trading observation before any live deployment.

### 3.3 Deterministic controls over model persuasion

The RiskGovernor is deterministic Python code. It does not rely on LLM judgment to approve trades.

The Risk Reviewer Agent may explain a risk decision, but it cannot change the decision.

### 3.4 Fail closed

If any critical risk service fails, HaruQuant must block new orders.

Critical services include:

1. RiskGovernor.
2. Kill Switch.
3. Audit Logger.
4. Broker heartbeat monitor.
5. Market data feed.
6. Account state service.
7. Strategy lifecycle service.

### 3.5 Evidence before allocation

A strategy receives allocation only after evidence exists.

Required evidence includes:

1. Strategy specification.
2. Code review.
3. Backtest report.
4. Analytics report.
5. Robustness report.
6. Statistical validation report.
7. Risk review.
8. Paper trading report.
9. Portfolio Manager memo.
10. Human Board approval for live trading.

---

## 4. Risk modes

HaruQuant has four operating modes.

| Mode | Capital at risk | Purpose | Live orders allowed? |
|---|---:|---|---:|
| `research` | 0 | Ideas, papers, analysis, data exploration | No |
| `backtest` | 0 | Historical testing | No |
| `paper` | 0 | Forward simulation with live-like execution assumptions | No |
| `live` | Real capital | Controlled broker execution | Yes, only with Board approval and RiskGovernor approval |

The default mode is always:

```yaml
default_mode: paper
```

---

## 5. Risk limit summary

The following limits are the default HaruQuant baseline. They may be tightened at any time by the Human Board. They may only be loosened through Board approval, audit logging, and versioned risk policy change control.

| Risk control | Default limit | Hard/soft | Enforced by |
|---|---:|---|---|
| Max risk per trade — micro live | 0.25% of equity | Hard | RiskGovernor |
| Max risk per trade — normal live | 0.50% of equity | Hard | RiskGovernor |
| Max daily realized + unrealized loss | 1.00% of equity | Hard | Kill Switch |
| Max weekly realized + unrealized loss | 3.00% of equity | Hard | Kill Switch |
| Max monthly drawdown | 5.00% from month-start equity | Hard | RiskGovernor + Kill Switch |
| Max portfolio drawdown warning | 8.00% from high-water mark | Soft | RiskGovernor |
| Max portfolio drawdown hard stop | 10.00% from high-water mark | Hard | Kill Switch |
| Catastrophic portfolio stop | 15.00% from high-water mark | Hard | Kill Switch + Board review |
| Max open risk per symbol | 1.00% of equity | Hard | RiskGovernor |
| Max strategy allocation | 20.00% of live risk budget | Hard | Portfolio Manager + RiskGovernor |
| Max correlated cluster open risk | 3.00% of equity | Hard | RiskGovernor |
| Max USD-cluster open risk | 4.00% of equity | Hard | RiskGovernor |
| Max total simultaneous live positions | 10 | Hard | RiskGovernor |
| Max simultaneous positions per symbol | 2 | Hard | RiskGovernor |
| Max simultaneous positions per strategy | 3 | Hard | RiskGovernor |
| Max live strategies | 12 | Hard | Portfolio Manager |
| Max paper strategies | 50 | Soft | Portfolio Manager |
| Max margin usage warning | 30.00% of usable margin | Soft | RiskGovernor |
| Max margin usage hard stop | 40.00% of usable margin | Hard | RiskGovernor |
| Max spread multiplier | 2.0x rolling median spread | Hard | Execution Bridge |
| Max slippage multiplier | 1.5x expected slippage | Hard | Execution Bridge |
| High-impact news block | 30 min before to 30 min after | Hard | News/Event Risk Service |
| Broker disconnect order block | Immediate | Hard | Kill Switch |
| Market data stale threshold | 5 seconds for tick mode; 2 bars for bar mode | Hard | Execution Bridge |

---

## 6. Max risk per trade

### 6.1 Definition

Risk per trade is the amount of equity that may be lost if the trade reaches its defined stop-loss or deterministic risk boundary.

For strategies without a hard stop-loss, HaruQuant must compute synthetic risk using a conservative fallback model.

### 6.2 Formula with stop-loss

For a long or short position with a valid stop-loss:

```text
trade_risk_money =
    abs(entry_price - stop_loss_price)
    × pip_value_or_tick_value
    × position_size
    + estimated_commission
    + estimated_slippage
    + estimated_spread_cost
```

```text
trade_risk_pct = trade_risk_money / account_equity
```

### 6.3 Formula without stop-loss

If a strategy does not use a stop-loss, the RiskGovernor must use the greater of:

1. Historical adverse excursion estimate.
2. Volatility-based risk estimate.
3. Strategy-level worst expected loss.
4. Portfolio policy fallback.

```text
synthetic_trade_risk =
    max(
        2.5 × ATR_risk_unit,
        95th_percentile_MAE,
        configured_no_stop_loss_risk_floor,
        stress_loss_estimate
    )
```

### 6.4 Limits

| Deployment stage | Max risk per trade |
|---|---:|
| Paper trading | Configurable simulation value |
| Micro live | 0.25% |
| Limited live | 0.25% to 0.50% |
| Normal live | 0.50% |
| Experimental live | 0.10% |
| Strategy under review | 0.00%; new trades blocked |

### 6.5 Enforcement

Risk per trade is enforced by the RiskGovernor before order submission.

The Execution Bridge must reject any order that does not include a valid RiskGovernor approval token.

### 6.6 Violation behavior

If a trade exceeds max risk per trade:

1. Reject order.
2. Log rejection.
3. Notify CEO Agent.
4. Notify Risk Reviewer Agent.
5. Include in daily risk report.
6. Do not retry with reduced size unless the RiskGovernor recalculates and approves the reduced order.

---

## 7. Max daily loss

### 7.1 Definition

Daily loss is measured from the start-of-day equity snapshot.

It includes:

1. Realized closed-trade P&L.
2. Unrealized open-position P&L.
3. Commission.
4. Swap.
5. Slippage.
6. Spread cost.

```text
daily_loss_pct =
    (start_of_day_equity - current_equity) / start_of_day_equity
```

### 7.2 Limits

| Level | Daily loss | Action |
|---|---:|---|
| Watch | 0.50% | Reduce new risk by 50% |
| Soft stop | 0.75% | Block new experimental trades |
| Hard stop | 1.00% | Block all new trades |
| Critical | 1.25% | Disable live trading and require Board review |

### 7.3 Enforcement

Daily loss is enforced by the Kill Switch and RiskGovernor.

### 7.4 Reset

The daily loss counter resets only at the configured trading-day boundary.

Default:

```yaml
trading_day_boundary_timezone: "UTC"
trading_day_reset_time: "00:00"
```

For broker-specific daily accounting, the account server timezone may also be recorded.

---

## 8. Max weekly loss

### 8.1 Definition

Weekly loss is measured from the week-start equity snapshot.

```text
weekly_loss_pct =
    (start_of_week_equity - current_equity) / start_of_week_equity
```

### 8.2 Limits

| Level | Weekly loss | Action |
|---|---:|---|
| Watch | 1.50% | Reduce all new trade risk by 50% |
| Soft stop | 2.00% | Block new strategy entries |
| Hard stop | 3.00% | Disable new live orders |
| Critical | 4.00% | Disable live trading and require Board review |

### 8.3 Enforcement

The RiskGovernor must reject all new live trade proposals once weekly hard stop is reached.

The Kill Switch must disable new live orders once critical level is reached.

---

## 9. Max monthly drawdown

### 9.1 Definition

Monthly drawdown is measured from the month-start equity or month-to-date high-water mark, whichever produces the more conservative reading.

```text
monthly_drawdown_pct =
    (monthly_high_water_equity - current_equity) / monthly_high_water_equity
```

### 9.2 Limits

| Level | Monthly drawdown | Action |
|---|---:|---|
| Watch | 2.50% | Reduce risk by 25% |
| Soft stop | 3.50% | Reduce risk by 50% |
| Hard stop | 5.00% | Block new live entries |
| Critical | 6.00% | Disable live trading and require Board review |

### 9.3 Enforcement

Monthly drawdown is enforced by RiskGovernor before order approval and by Kill Switch for account-level protection.

---

## 10. Max portfolio drawdown

### 10.1 Definition

Portfolio drawdown is measured from the all-time high-water mark of account equity after live trading begins.

```text
portfolio_drawdown_pct =
    (portfolio_high_water_equity - current_equity) / portfolio_high_water_equity
```

### 10.2 Limits

| Level | Portfolio drawdown | Action |
|---|---:|---|
| Watch | 5.00% | Board notification |
| Warning | 8.00% | New risk reduced by 50% |
| Hard stop | 10.00% | Block all new live trades |
| Catastrophic stop | 15.00% | Disable live trading, require full Board review |

### 10.3 Recovery rule

After a hard stop, live trading may resume only after:

1. Audit Agent confirms no control violation.
2. Performance Reporter explains loss source.
3. Risk Reviewer provides memo.
4. Portfolio Manager recommends resume or remain paused.
5. Human Board approves resume.

---

## 11. Max symbol exposure

### 11.1 Definition

Symbol exposure includes all open positions and pending orders for the same instrument.

For example:

```text
EURUSD exposure =
    all EURUSD long risk
    + all EURUSD short risk
    + all EURUSD pending order risk
```

### 11.2 Limits

| Symbol status | Max open risk |
|---|---:|
| Normal symbol | 1.00% of equity |
| High-volatility symbol | 0.50% of equity |
| News-affected symbol | 0.00% during block |
| Under review | 0.00% |
| Paper only | No live exposure |

### 11.3 Position count

| Scope | Limit |
|---|---:|
| Per symbol live positions | 2 |
| Per symbol pending orders | 2 |
| Per symbol strategy entries | 1 per strategy unless specifically approved |

### 11.4 Enforcement

RiskGovernor must aggregate symbol exposure before approving any new order.

---

## 12. Max correlated exposure

### 12.1 Definition

Correlated exposure is total open risk across positions that tend to move together.

Correlation should be computed using recent rolling returns.

Default settings:

```yaml
correlation_window_bars: 250
correlation_timeframe: "H1"
high_correlation_threshold: 0.60
extreme_correlation_threshold: 0.80
```

### 12.2 Limits

| Correlation state | Action |
|---|---|
| `abs(corr) < 0.50` | Normal sizing allowed |
| `0.50 <= abs(corr) < 0.60` | Risk review warning |
| `0.60 <= abs(corr) < 0.80` | Cluster cap applies |
| `abs(corr) >= 0.80` | Treat as same-risk cluster |

### 12.3 Cluster risk limit

```text
max_correlated_cluster_open_risk = 3.00% of equity
```

### 12.4 Negative correlation rule

Negative correlation may reduce net directional risk, but it must not be used by agents to justify increasing gross exposure beyond margin, drawdown, or VaR limits.

### 12.5 Enforcement

The RiskGovernor must:

1. Compute pairwise correlations.
2. Group high-correlation instruments.
3. Calculate cluster open risk.
4. Reject new trades that exceed cluster cap.
5. Log cluster composition in the risk approval record.

---

## 13. Max USD-cluster exposure

### 13.1 Definition

USD-cluster exposure is the aggregate exposure created by instruments where USD is the base currency, quote currency, or dominant macro driver.

Examples:

1. EURUSD.
2. GBPUSD.
3. USDJPY.
4. USDCHF.
5. USDCAD.
6. AUDUSD.
7. NZDUSD.
8. XAUUSD.
9. XAGUSD.
10. Major USD-sensitive indices or commodities.

### 13.2 Limit

```text
max_usd_cluster_open_risk = 4.00% of equity
```

### 13.3 Directional netting

The RiskGovernor may compute both gross and net USD exposure.

However:

1. Gross exposure must be controlled.
2. Netting must be conservative.
3. Netting must not bypass max symbol, max strategy, margin, VaR, or drawdown rules.

### 13.4 Enforcement

Before approving any new trade, RiskGovernor must calculate:

1. Current USD gross exposure.
2. Current USD net exposure.
3. Proposed USD gross exposure.
4. Proposed USD net exposure.
5. USD-cluster VaR contribution.

Reject if any threshold is breached.

---

## 14. Max number of simultaneous positions

### 14.1 Live account limits

| Scope | Max positions |
|---|---:|
| Total live positions | 10 |
| Positions per symbol | 2 |
| Positions per strategy | 3 |
| Positions per correlated cluster | 5 |
| Positions per USD cluster | 7 |
| Pending live orders | 10 |
| Pending orders per symbol | 2 |

### 14.2 Paper account limits

| Scope | Max positions |
|---|---:|
| Total paper positions | 50 |
| Positions per symbol | 5 |
| Positions per strategy | 10 |
| Pending paper orders | 50 |

### 14.3 Enforcement

Position count is enforced by:

1. RiskGovernor.
2. Execution Bridge.
3. Broker state reconciliation service.

---

## 15. Max strategy allocation

### 15.1 Definition

Strategy allocation is the share of the live risk budget assigned to a strategy.

It may be expressed as:

1. Share of total allowed open risk.
2. Share of account-level margin budget.
3. Share of capital allocation.
4. Share of trade frequency allowance.

### 15.2 Limits

| Strategy status | Max allocation |
|---|---:|
| Research | 0% |
| Backtest only | 0% |
| Paper trading | 0% real capital |
| Micro live | 2.5% of live risk budget |
| Limited live | 10% of live risk budget |
| Normal live | 20% of live risk budget |
| Mature diversified strategy | 25% only with Board approval |
| Under review | 0% new risk |
| Paused | 0% |
| Retired | 0% |

### 15.3 Allocation increase rule

A strategy allocation may be increased only after:

1. Minimum live observation period.
2. Drawdown within limits.
3. Slippage within expected limits.
4. Performance within confidence interval.
5. No critical audit findings.
6. Portfolio Manager recommendation.
7. Human Board approval.

### 15.4 Enforcement

Portfolio Manager recommends allocation.

Human Board approves allocation.

RiskGovernor enforces allocation.

---

## 16. Max live strategies

### 16.1 Limit

```text
max_live_strategies = 12
```

### 16.2 Rationale

A small strategy portfolio is easier to monitor, diagnose, and control.

More strategies may improve diversification, but they also increase:

1. Operational complexity.
2. Correlation risk.
3. Monitoring burden.
4. Data-quality risk.
5. Agent supervision burden.
6. Execution conflicts.

### 16.3 Expansion rule

Increasing the max live strategy count requires:

1. Portfolio Manager memo.
2. Risk Reviewer memo.
3. Audit Agent review.
4. Human Board approval.
5. Risk config version update.

---

## 17. Max paper strategies

### 17.1 Limit

```text
max_paper_strategies = 50
```

### 17.2 Soft cap behavior

At 40 paper strategies:

1. CEO Agent must warn the Board.
2. Cost Optimizer must estimate compute load.
3. Portfolio Manager must rank candidates.

At 50 paper strategies:

1. New paper admissions are blocked.
2. Weak paper strategies must be retired or archived.
3. Only Board-approved exceptions may add new paper strategies.

### 17.3 Promotion queue

Paper strategies should be ranked using:

1. Paper-trading performance.
2. Backtest quality.
3. Robustness score.
4. Statistical confidence.
5. Correlation benefit.
6. Cost sensitivity.
7. Execution quality.
8. Risk-adjusted return.

---

## 18. Spread filters

### 18.1 Definition

Spread filter blocks trade entry when the current spread is abnormal relative to the symbol’s recent behavior.

### 18.2 Default formula

```text
spread_allowed =
    current_spread <= min(
        configured_absolute_max_spread,
        rolling_median_spread × spread_multiplier_limit
    )
```

Default:

```yaml
spread_multiplier_limit: 2.0
spread_lookback_window: 500 ticks
```

### 18.3 Symbol-specific absolute max spread

| Symbol class | Default max spread behavior |
|---|---|
| Forex majors | Tightest threshold |
| Forex minors/crosses | Moderate threshold |
| Metals | Wider threshold allowed |
| Indices | Broker/session dependent |
| Crypto | Paper only unless separately approved |

Symbol-specific values must be stored in:

```text
configs/symbol_risk_limits.yaml
```

### 18.4 Entry vs exit behavior

Spread filters block **new entries**.

Spread filters do not block risk-reducing exits.

### 18.5 Enforcement

The Execution Bridge must check spread immediately before order submission.

If spread becomes invalid after RiskGovernor approval but before broker submission, the order must be rejected or re-approved.

---

## 19. Slippage filters

### 19.1 Definition

Slippage is the difference between requested or expected execution price and actual execution price.

```text
slippage_points = abs(executed_price - requested_price) / point_size
```

### 19.2 Expected slippage model

Expected slippage should be estimated using:

1. Historical slippage by symbol.
2. Time of day.
3. News-event proximity.
4. Spread regime.
5. Volatility regime.
6. Broker execution quality.
7. Order size.

### 19.3 Limits

| Level | Rule | Action |
|---|---|---|
| Normal | Slippage <= expected | Allow |
| Warning | Slippage > 1.0x expected | Log warning |
| Hard block | Slippage > 1.5x expected | Block new entries |
| Critical | Slippage > 2.0x expected | Pause symbol/strategy |

### 19.4 Repeated slippage rule

If 3 trades in a rolling 20-trade window exceed expected slippage by more than 1.5x:

1. Pause the affected strategy.
2. Notify Risk Reviewer Agent.
3. Generate execution quality report.
4. Require Board review before resume if live.

### 19.5 Enforcement

The Execution Bridge must enforce slippage tolerance.

The Performance Reporter must report realized slippage daily.

---

## 20. News-event blocks

### 20.1 Purpose

News-event blocks prevent new entries around scheduled high-impact events that can cause abnormal spreads, volatility, gaps, slippage, and liquidity shortages.

### 20.2 High-impact events

High-impact events include:

1. Central bank rate decisions.
2. FOMC statements and press conferences.
3. CPI.
4. NFP / employment data.
5. GDP releases.
6. Retail sales.
7. PMI releases.
8. Major geopolitical shocks.
9. Broker-specific margin changes.
10. Exchange halts or volatility interruptions.

### 20.3 Default block window

```yaml
high_impact_news_block_before_minutes: 30
high_impact_news_block_after_minutes: 30
```

For extreme events:

```yaml
extreme_event_block_before_minutes: 120
extreme_event_block_after_minutes: 240
```

### 20.4 Symbol mapping

News blocks must be mapped to affected symbols.

Examples:

| Event | Symbols affected |
|---|---|
| USD CPI | USD pairs, XAUUSD, XAGUSD, indices |
| FOMC | USD pairs, metals, indices, crypto |
| ECB rate decision | EUR pairs, European indices |
| BoE rate decision | GBP pairs |
| BoJ rate decision | JPY pairs |
| Oil inventory | Oil, CAD pairs |
| Crypto regulatory event | Crypto only |

### 20.5 Entry vs exit behavior

News blocks prevent new entries.

News blocks do not prevent:

1. Closing positions.
2. Reducing exposure.
3. Emergency exits.
4. Kill-switch actions.

### 20.6 Enforcement

News-event blocks are enforced by:

1. Event Risk Service.
2. RiskGovernor.
3. Execution Bridge.

If the event calendar is unavailable, HaruQuant must fail conservatively for affected markets.

---

## 21. Broker-disconnect behavior

### 21.1 Definition

A broker disconnect occurs when HaruQuant cannot reliably communicate with the broker, receive account state, submit orders, modify orders, or confirm position state.

### 21.2 Disconnect states

| State | Condition | Action |
|---|---|---|
| `healthy` | Heartbeat normal | Normal |
| `degraded` | Intermittent delay | Block new entries |
| `disconnected` | Heartbeat missing | Block all new orders |
| `unknown_position_state` | Positions cannot be reconciled | Block all new orders and alert |
| `reconnected_unverified` | Connection restored but state not reconciled | Block new orders until reconciliation |

### 21.3 Heartbeat defaults

```yaml
broker_heartbeat_interval_seconds: 1
broker_heartbeat_timeout_seconds: 5
broker_reconnect_attempts: 3
broker_reconnect_backoff_seconds: 2
```

### 21.4 On disconnect

When broker disconnect is detected:

1. Stop submitting new orders.
2. Freeze new strategy signals.
3. Preserve existing local state.
4. Attempt reconnect.
5. On reconnect, reconcile broker positions.
6. Compare broker positions to HaruQuant ledger.
7. Report mismatch.
8. Keep live trading blocked until state is verified.

### 21.5 Order handling

If pending orders exist during disconnect:

1. Do not assume cancellation succeeded.
2. Do not assume order execution failed.
3. Reconcile with broker after reconnect.
4. Mark state as unknown until verified.
5. Block new orders during unknown state.

### 21.6 Cancel-on-disconnect

If the broker or venue supports cancel-on-disconnect, HaruQuant should enable it where appropriate.

If unsupported, HaruQuant must document the gap and apply stricter exposure limits.

---

## 22. Kill-switch rules

### 22.1 Purpose

The Kill Switch is the final emergency safety mechanism.

It must disable new trading activity when risk, execution, data, or infrastructure conditions become unsafe.

### 22.2 Kill-switch levels

| Level | Name | Effect |
|---|---|---|
| Level 1 | Strategy pause | Pause one strategy |
| Level 2 | Symbol pause | Pause one symbol |
| Level 3 | Cluster pause | Pause correlated cluster |
| Level 4 | Portfolio pause | Block all new entries |
| Level 5 | Emergency shutdown | Block all orders except risk-reducing exits |

### 22.3 Trigger conditions

The Kill Switch must trigger when any of the following occur:

1. Daily hard loss is reached.
2. Weekly hard loss is reached.
3. Monthly hard drawdown is reached.
4. Portfolio hard drawdown is reached.
5. Catastrophic drawdown is reached.
6. RiskGovernor is unavailable.
7. Audit Logger is unavailable.
8. Broker is disconnected.
9. Market data is stale.
10. Account state is unknown.
11. Repeated order failures occur.
12. Repeated slippage violations occur.
13. Spread exceeds emergency threshold.
14. Unauthorized live order attempt is detected.
15. Agent attempts to bypass permission layer.
16. Risk threshold file is modified without Board approval.
17. Strategy lifecycle stage is bypassed.
18. Execution Bridge detects mismatched approval token.
19. Broker rejects too many orders in a short window.
20. System clock drift exceeds allowed tolerance.

### 22.4 Kill-switch actions

When triggered, the Kill Switch must:

1. Block new live entries.
2. Block new pending orders.
3. Preserve audit logs.
4. Notify CEO Agent.
5. Notify Risk Reviewer Agent.
6. Notify Human Board.
7. Create incident record.
8. Record trigger source.
9. Record account snapshot.
10. Record open positions.
11. Record pending orders.
12. Record failed tool calls.
13. Record strategy state.
14. Record broker state.

Depending on severity, it may also:

1. Cancel pending orders.
2. Close risk-increasing positions.
3. Close all positions.
4. Disable all live strategies.

### 22.5 Resume after kill switch

Live trading may resume only when:

1. Trigger cause is identified.
2. Account state is reconciled.
3. Broker state is healthy.
4. Market data is healthy.
5. RiskGovernor is healthy.
6. Audit Logger is healthy.
7. Incident report is complete.
8. Risk Reviewer gives memo.
9. Portfolio Manager gives recommendation.
10. Human Board approves resume.

### 22.6 Manual kill switch

The Human Board must have a manual kill-switch action available in the UI.

Path:

```text
/risk-center/kill-switch
```

Required UI actions:

1. Pause strategy.
2. Pause symbol.
3. Pause all live trading.
4. Emergency flatten, if broker integration supports it.
5. Require confirmation phrase for emergency flatten.

---

## 23. RiskGovernor approval process

### 23.1 Trade proposal input

Each trade proposal must include:

```yaml
proposal_id:
strategy_id:
strategy_version:
strategy_lifecycle_state:
symbol:
side:
entry_type:
requested_size:
entry_price:
stop_loss:
take_profit:
max_spread:
max_slippage:
time_in_force:
expected_risk_money:
expected_risk_pct:
open_positions_snapshot:
account_equity:
account_balance:
margin_available:
evidence_refs:
```

### 23.2 Approval output

RiskGovernor returns:

```yaml
approval_id:
proposal_id:
approved: true | false
approved_size:
max_price_deviation:
expires_at:
risk_metrics:
  trade_risk_pct:
  daily_loss_pct:
  weekly_loss_pct:
  monthly_drawdown_pct:
  portfolio_drawdown_pct:
  symbol_exposure_pct:
  correlated_cluster_exposure_pct:
  usd_cluster_exposure_pct:
  margin_usage_pct:
  var_impact:
  cvar_impact:
rejection_reasons:
risk_config_hash:
approval_hash:
created_at:
```

### 23.3 Approval expiry

Default:

```yaml
risk_approval_ttl_seconds: 10
```

If the order is not submitted within the approval window, it must be re-approved.

### 23.4 Approval-token matching

The Execution Bridge must verify:

1. Same proposal ID.
2. Same strategy ID.
3. Same symbol.
4. Same side.
5. Same or lower size.
6. Same or stricter max spread.
7. Same or stricter slippage limit.
8. Approval not expired.
9. Risk config hash unchanged.
10. Strategy lifecycle still valid.

---

## 24. Position sizing law

### 24.1 Sizing hierarchy

HaruQuant position sizing must follow this hierarchy:

```text
Strategy desired size
→ Risk per trade cap
→ Symbol exposure cap
→ Correlated exposure cap
→ USD-cluster exposure cap
→ Margin cap
→ VaR/CVaR cap
→ Board-approved allocation cap
→ Final approved size
```

The final approved size is the minimum size allowed by all applicable constraints.

### 24.2 Volatility-adjusted sizing

Where possible, position size should be volatility-adjusted so that each strategy contributes comparable risk.

```text
target_position_size =
    target_risk_money / volatility_risk_per_unit
```

### 24.3 Size reduction

RiskGovernor may approve a reduced size if:

1. Reduced size is above broker minimum.
2. Reduced size satisfies all constraints.
3. Strategy supports partial size execution.
4. Approval record clearly states reduced size.

If reduced size is below broker minimum, reject order.

---

## 25. Margin and leverage controls

### 25.1 Margin usage

| Level | Margin usage | Action |
|---|---:|---|
| Normal | < 20% | Allow |
| Watch | 20% to 30% | Warning |
| Soft limit | 30% to 40% | Reduce new trade size |
| Hard limit | > 40% | Block new trades |

### 25.2 Leverage

Effective leverage must be monitored at account, symbol, strategy, and cluster level.

```text
effective_leverage = gross_notional_exposure / account_equity
```

Maximum leverage depends on asset class and broker rules, but must never override drawdown, VaR, or margin constraints.

### 25.3 Margin call prevention

If margin level falls below internal safety threshold:

1. Block new entries.
2. Notify Human Board.
3. Notify Risk Reviewer.
4. Consider risk-reducing exits.
5. Trigger Kill Switch if critical.

---

## 26. VaR and CVaR controls

### 26.1 Purpose

VaR and CVaR estimate possible portfolio loss under normal and tail-risk conditions.

They must not be the only risk controls, but they are mandatory portfolio-level checks.

### 26.2 Required calculations

RiskGovernor must compute:

1. Historical VaR.
2. Historical CVaR.
3. Monte Carlo VaR.
4. Monte Carlo CVaR.
5. Incremental VaR of proposed trade.
6. Incremental CVaR of proposed trade.

### 26.3 Default limits

| Metric | Limit |
|---|---:|
| 1-day 95% VaR | <= 2.00% of equity |
| 1-day 99% VaR | <= 3.00% of equity |
| 1-day 95% CVaR | <= 3.00% of equity |
| 1-day 99% CVaR | <= 4.00% of equity |

### 26.4 Enforcement

Reject any trade that causes portfolio VaR or CVaR to exceed the configured limit.

---

## 27. Strategy degradation controls

### 27.1 Degradation signals

A strategy enters review if:

1. It reaches 50% of its allowed drawdown.
2. It has abnormal slippage.
3. It has abnormal spread sensitivity.
4. It underperforms expected confidence interval.
5. It has a losing streak beyond expected distribution.
6. It becomes highly correlated with another active strategy.
7. It violates execution assumptions.
8. It stops matching its backtest behavior.

### 27.2 Actions

| Degradation level | Action |
|---|---|
| Watch | Reduce risk by 25% |
| Warning | Reduce risk by 50% |
| Severe | Pause new entries |
| Critical | Retire or Board review |

### 27.3 Required reports

Before resuming normal allocation:

1. Backtest Analyst memo.
2. Risk Reviewer memo.
3. Portfolio Manager recommendation.
4. Board approval if live.

---

## 28. Data-quality controls

### 28.1 Required checks

Before backtest, paper execution, or live execution, HaruQuant must check:

1. Missing bars.
2. Duplicate bars.
3. Stale ticks.
4. Timezone mismatch.
5. Symbol metadata mismatch.
6. Abnormal spreads.
7. Outlier prices.
8. Bad bid/ask values.
9. Broker contract specification changes.
10. Pip/tick value changes.

### 28.2 Live data failure

If live data is stale:

1. Block new entries.
2. Keep risk-reducing exits available only if broker state is reliable.
3. Trigger incident if unresolved.
4. Notify CEO Agent and Human Board.

---

## 29. Agent-specific risk restrictions

### 29.1 CEO Agent

May:

1. Delegate tasks.
2. Summarize risk.
3. Present Board approval requests.

May not:

1. Approve live trades.
2. Change risk thresholds.
3. Override RiskGovernor.
4. Disable Kill Switch.

### 29.2 Research Agents

May:

1. Read market data.
2. Create research reports.
3. Suggest strategy ideas.

May not:

1. Execute trades.
2. Change strategy lifecycle state.
3. Modify risk config.
4. Approve allocation.

### 29.3 Strategy Creator and Codegen Agents

May:

1. Create strategy specs.
2. Generate strategy code.
3. Generate tests.

May not:

1. Deploy live.
2. Change risk rules.
3. Approve own code.
4. Bypass review.

### 29.4 Backtest and Robustness Agents

May:

1. Run historical tests.
2. Run stress tests.
3. Produce evidence.

May not:

1. Promote strategy to live.
2. Hide failed tests.
3. Delete result packages.
4. Change test results.

### 29.5 Risk Reviewer Agent

May:

1. Explain risk.
2. Recommend approve/reject.
3. Write risk memos.

May not:

1. Override deterministic rejection.
2. Change thresholds.
3. Generate approval tokens.
4. Place orders.

### 29.6 Portfolio Manager Agent

May:

1. Recommend allocation.
2. Recommend promotion/demotion.
3. Rank strategies.

May not:

1. Activate live trading without Board approval.
2. Place trades.
3. Override RiskGovernor.

### 29.7 Execution Agent

May:

1. Submit paper orders.
2. Submit live orders only through approved bridge.
3. Report execution status.

May not:

1. Submit live orders without RiskGovernor approval.
2. Increase approved size.
3. Change trade direction after approval.
4. Retry rejected orders indefinitely.
5. Bypass Kill Switch.

---

## 30. Config files

### 30.1 `configs/risk_thresholds.yaml`

```yaml
version: "1.0.0"
owner: "Human Board"
default_mode: "paper"

risk_per_trade:
  micro_live_pct: 0.25
  limited_live_pct: 0.50
  normal_live_pct: 0.50
  experimental_live_pct: 0.10

loss_limits:
  daily_watch_pct: 0.50
  daily_soft_stop_pct: 0.75
  daily_hard_stop_pct: 1.00
  daily_critical_pct: 1.25

  weekly_watch_pct: 1.50
  weekly_soft_stop_pct: 2.00
  weekly_hard_stop_pct: 3.00
  weekly_critical_pct: 4.00

drawdown_limits:
  monthly_watch_pct: 2.50
  monthly_soft_stop_pct: 3.50
  monthly_hard_stop_pct: 5.00
  monthly_critical_pct: 6.00

  portfolio_watch_pct: 5.00
  portfolio_warning_pct: 8.00
  portfolio_hard_stop_pct: 10.00
  portfolio_catastrophic_pct: 15.00

exposure_limits:
  max_symbol_open_risk_pct: 1.00
  max_correlated_cluster_open_risk_pct: 3.00
  max_usd_cluster_open_risk_pct: 4.00
  high_correlation_threshold: 0.60
  extreme_correlation_threshold: 0.80
  correlation_window_bars: 250
  correlation_timeframe: "H1"

position_limits:
  max_total_live_positions: 10
  max_positions_per_symbol: 2
  max_positions_per_strategy: 3
  max_positions_per_correlated_cluster: 5
  max_positions_per_usd_cluster: 7
  max_pending_live_orders: 10
  max_pending_orders_per_symbol: 2

strategy_limits:
  max_live_strategies: 12
  max_paper_strategies: 50
  max_normal_strategy_allocation_pct: 20.00
  max_mature_strategy_allocation_pct_with_board_approval: 25.00

margin_limits:
  margin_usage_watch_pct: 20.00
  margin_usage_soft_limit_pct: 30.00
  margin_usage_hard_limit_pct: 40.00

spread_filters:
  spread_multiplier_limit: 2.00
  spread_lookback_window_ticks: 500

slippage_filters:
  warning_multiplier: 1.00
  hard_block_multiplier: 1.50
  critical_multiplier: 2.00
  rolling_window_trades: 20
  max_violations_per_window: 3

news_blocks:
  high_impact_before_minutes: 30
  high_impact_after_minutes: 30
  extreme_event_before_minutes: 120
  extreme_event_after_minutes: 240

broker_disconnect:
  heartbeat_interval_seconds: 1
  heartbeat_timeout_seconds: 5
  reconnect_attempts: 3
  reconnect_backoff_seconds: 2
  block_orders_when_state_unknown: true
  require_position_reconciliation_after_reconnect: true

approval:
  risk_approval_ttl_seconds: 10
  require_approval_hash: true
  reject_if_config_hash_changed: true

var_cvar:
  var_95_1d_limit_pct: 2.00
  var_99_1d_limit_pct: 3.00
  cvar_95_1d_limit_pct: 3.00
  cvar_99_1d_limit_pct: 4.00

kill_switch:
  enabled: true
  fail_closed: true
  block_if_risk_governor_unavailable: true
  block_if_audit_logger_unavailable: true
  block_if_market_data_stale: true
  block_if_broker_disconnected: true
  block_if_account_state_unknown: true
  block_if_unauthorized_live_order_attempt: true
```

### 30.2 `configs/symbol_risk_limits.yaml`

```yaml
EURUSD:
  max_open_risk_pct: 1.00
  max_positions: 2
  max_spread_points: null
  spread_multiplier_limit: 2.00
  news_currencies: ["EUR", "USD"]

GBPUSD:
  max_open_risk_pct: 1.00
  max_positions: 2
  max_spread_points: null
  spread_multiplier_limit: 2.00
  news_currencies: ["GBP", "USD"]

XAUUSD:
  max_open_risk_pct: 0.75
  max_positions: 2
  max_spread_points: null
  spread_multiplier_limit: 2.00
  news_currencies: ["USD"]
  high_volatility_symbol: true
```

---

## 31. Required implementation modules

This policy must be implemented through the following modules:

```text
backend/app/risk/governor.py
backend/app/risk/approvals.py
backend/app/risk/kill_switch.py
backend/app/risk/correlation.py
backend/app/risk/var_engine.py
backend/app/execution/order_router.py
backend/app/execution/paper_broker.py
backend/app/execution/mt5_bridge.py
backend/app/execution/ctrader_bridge.py
backend/app/tools/risk_tools.py
backend/app/tools/execution_tools.py
backend/app/agents/risk_reviewer/agent.py
backend/app/agents/portfolio_manager/agent.py
backend/app/agents/audit/agent.py
```

---

## 32. Required audit events

The Audit Logger must record:

1. Risk policy version loaded.
2. Risk threshold file loaded.
3. Risk threshold hash.
4. Every trade proposal.
5. Every risk approval.
6. Every risk rejection.
7. Every order submission.
8. Every broker response.
9. Every position reconciliation.
10. Every kill-switch trigger.
11. Every kill-switch resume.
12. Every agent attempt to use forbidden tool.
13. Every risk config change.
14. Every live activation request.
15. Every live activation approval.
16. Every strategy promotion.
17. Every strategy demotion.
18. Every strategy retirement.

---

## 33. Required dashboard pages

The frontend must expose risk monitoring through:

```text
/risk-center
/risk-center/approvals
/risk-center/exposure
/risk-center/drawdown
/risk-center/correlation
/risk-center/var-cvar
/risk-center/kill-switch
/risk-center/incidents
/board-room/risk-approvals
```

---

## 34. Change management

### 34.1 Who may change this policy?

Only the Human Board may approve changes.

Agents may propose changes but may not apply them.

### 34.2 Change process

Every change requires:

1. Proposed diff.
2. Reason for change.
3. Risk impact analysis.
4. Backward compatibility check.
5. Human Board approval.
6. Version increment.
7. Audit log entry.
8. Config hash update.

### 34.3 Emergency tightening

Risk limits may be tightened immediately during an incident.

Risk limits may not be loosened during an incident.

---

## 35. Final coverage checklist

| Requirement | Covered? | Section |
|---|---:|---|
| Create `risk_policy.md` | Yes | Document header |
| Define max risk per trade | Yes | Section 6 |
| Define max daily loss | Yes | Section 7 |
| Define max weekly loss | Yes | Section 8 |
| Define max monthly drawdown | Yes | Section 9 |
| Define max portfolio drawdown | Yes | Section 10 |
| Define max symbol exposure | Yes | Section 11 |
| Define max correlated exposure | Yes | Section 12 |
| Define max USD-cluster exposure | Yes | Section 13 |
| Define max number of simultaneous positions | Yes | Section 14 |
| Define max strategy allocation | Yes | Section 15 |
| Define max live strategies | Yes | Section 16 |
| Define max paper strategies | Yes | Section 17 |
| Define spread filters | Yes | Section 18 |
| Define slippage filters | Yes | Section 19 |
| Define news-event blocks | Yes | Section 20 |
| Define broker-disconnect behavior | Yes | Section 21 |
| Define kill-switch rules | Yes | Section 22 |

---

## 36. References and design basis

This policy is informed by public risk-management and automated-trading control references, including:

1. NIST AI Risk Management Framework, which organizes AI risk management around Govern, Map, Measure, and Manage functions.
2. FINRA guidance and notices on AI and model-risk considerations for financial firms.
3. FIA best-practice materials on automated trading risk controls, pre-trade controls, system safeguards, and kill switches.
4. CME Globex risk-management tool descriptions, including pre-trade controls, kill switch behavior, and cancel-on-disconnect concepts.
5. ESMA / MiFID II Article 17 principles requiring algorithmic trading systems to have effective systems, risk controls, thresholds, limits, and safeguards against erroneous orders or disorderly markets.
6. TradingAgents research architecture, which separates analysts, researchers, trader, risk management, and fund-management decision roles.

---

## 37. Final policy law

The final law of this Risk Policy is:

> **When in doubt, HaruQuant must preserve capital, block new risk, log the event, and escalate to the Human Board.**


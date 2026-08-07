# Trading Cockpit Simulator
## Checklist, Dashboard Interaction, and Gameplay Validation Specification

**Document ID:** `TCS-TRADING-COCKPIT-001`
**Version:** `1.2`
**Date:** `2026-08-04`
**Status:** Complete game and financial-systems specification
**Document type:** Normative specification; not a phased implementation plan
**Intended users:** Game designers, gameplay programmers, UI/UX designers, financial-systems engineers, scenario designers, training designers, and QA engineers

> **Scope:** This document defines the complete functional and financial-systems behavior of a simulated trading cockpit. It specifies market models, controls, checklists, state machines, emergencies, accounting, replay integrity, recovery, training, scoring, and validation. It does not prioritize phases or prescribe a delivery sequence. All numerical limits are simulator defaults and must be configurable. The document is not investment advice and does not authorize live trading.


## Design Principles

```text
Pre-Market Preparation
  -> Cockpit Armed
  -> Setup Validated
  -> Order Released
  -> Position Managed
  -> Position Closed
  -> Post-Market Debrief
```

1. **A trade is a controlled sequence, not a single button press.**
2. **Risk is defined before exposure is created.**
3. **The simulator rewards process quality more heavily than profit.**
4. **Standing down is a successful outcome when mandatory gates fail.**
5. **The UI must display actual system state; checklist completion never changes market, account, order, or risk state by itself.**
6. **Emergency actions may reduce or close risk, but they may never silently increase it.**
7. **Every market, instrument, order, position, ledger, and clock state must be explicit, versioned, and auditable.**
8. **Scored replay must be deterministic, no-lookahead, and tamper-evident.**
9. **Application restart or reconnection must preserve authoritative financial consequences.**
10. **Training progression rewards demonstrated process competence, not raw profit.**

## Simulation and Assessment Modes

| Mode | Player Assistance | Gate Enforcement | Consequence Model |
| --- | --- | --- | --- |
| `GUIDED` | Highlights the next required panel, explains failures, and shows corrective actions | All mandatory checklist gates, policy limits, and system-integrity interlocks are hard blocks | Unsafe actions are prevented; incorrect attempts are logged and scored |
| `STANDARD` | Shows warnings and failed-rule summaries without step-by-step hints | Account-policy hard limits and system-integrity interlocks remain hard blocks; selected procedural gates may allow confirmed override | Overrides create simulated financial consequences, procedure penalties, and debrief events |
| `EXPERT` | No hints and minimal warning explanation | Only non-bypassable policy locks and system-integrity interlocks are hard blocks; other deviations follow the selected scenario profile | Full simulated fills, slippage, drawdown, lockout, and scoring consequences apply |
| `CHALLENGE` | Overlay applied to any base mode | Uses the base mode plus scripted scenario rules | Injects news spikes, spread expansion, partial fills, flash crashes, stale data, API failures, and liquidity gaps |

Non-bypassable interlocks in every mode include simulation isolation, immutable audit logging, duplicate-order prevention while order state is unknown, broker/internal reconciliation before re-arming, and account lockout after a configured hard loss breach.

## Specification Baseline

| Parameter | Assumed simulator default |
| --- | --- |
| Trading environment | `SIMULATION` only; no live account routing |
| Simulation source modes | `HISTORICAL_REPLAY`, `SYNTHETIC_SCENARIO`, `PAPER_BROKER`, or approved `SANDBOX_BROKER` |
| Starting equity | `$100,000 USD` |
| Instrument scope | Profile-driven. Every scenario must select an explicit, versioned `InstrumentVenueProfile`; unsupported or incomplete products are `INELIGIBLE`. |
| Market data | Real-time or replayed Level 1 plus Level 2 order-book data |
| Execution model | Broker-like order state machine with acknowledgements, partial fills, slippage, rejection, cancel/replace, bracket orders, and OCO behavior |
| Maximum risk per trade | `0.50%` of current equity |
| Maximum daily loss | `2.00%` of session-start equity, including realized P&L, unrealized P&L, fees, and financing |
| Maximum aggregate open risk | `1.50%` of current equity, including staged orders |
| Maximum gross leverage | `2.00x` equity |
| Minimum margin reserve | `30%` of equity after the proposed fill |
| Minimum net risk-to-reward | `2.00:1` after estimated fees and slippage |
| High-impact news blackout | `15 min before` through `5 min after` the event |
| Normal quote-freshness limit | `2 s` |
| Assessment principle | Process and risk discipline score more heavily than profit |


## Trading Policy Profile

All numeric limits and rule interpretations shall be loaded from a versioned policy profile. Values shown elsewhere in this document are simulator defaults, not universal trading rules.

```text
TradingPolicyProfile
├── profile_id
├── version
├── linked_profiles
│   ├── permitted_instrument_profile_ids
│   ├── valuation_policy_id
│   ├── latency_profile_id
│   ├── stress_scenario_profile_id
│   ├── approved_expectancy_profile_ids
│   └── recovery_policy_id
├── account
│   ├── starting_equity
│   ├── currency
│   ├── account_type
│   ├── leverage_limit
│   └── margin_model
├── drawdown
│   ├── daily_loss_method
│   ├── max_daily_loss_percent
│   ├── max_daily_loss_currency
│   ├── max_total_drawdown_percent
│   ├── max_total_drawdown_currency
│   ├── realized_loss_included
│   ├── unrealized_loss_included
│   ├── trailing_high_water_rule
│   ├── caution_usage_threshold
│   ├── restricted_usage_threshold
│   └── critical_usage_threshold
├── trade_limits
│   ├── max_risk_per_trade_percent
│   ├── max_open_positions
│   ├── max_open_risk_percent
│   ├── default_minimum_risk_reward
│   ├── approved_expectancy_profiles
│   ├── maximum_leverage
│   ├── max_symbol_exposure
│   └── max_correlated_exposure
├── market_rules
│   ├── allowed_sessions
│   ├── news_blackout_windows
│   ├── maximum_spread
│   ├── minimum_liquidity
│   ├── maximum_quote_age
│   ├── weekend_holding_rule
│   └── overnight_holding_rule
├── emergency_rules
│   ├── flash_crash_thresholds
│   ├── volatility_reduction_rule
│   ├── margin_emergency_rule
│   ├── broker_disconnect_policy
│   ├── drawdown_lockout_rule
│   ├── cooldown_rule
│   └── review_or_supervisor_requirement
└── assessment
    ├── base_mode
    ├── challenge_scenario_id
    ├── override_permissions
    └── scoring_profile
```

### Effective-Rule Resolution

```text
EFFECTIVE_RULE =
  scenario hard rule
  + account or challenge rule
  + venue and instrument rule
  + strategy rule
  + simulator default fallback
```

- Maximum limits use the **most conservative applicable maximum**.
- Minimum requirements use the **strictest applicable minimum**.
- A strategy may replace the default minimum risk-to-reward gate with an approved expectancy gate only when the policy profile explicitly permits it.
- Strategy rules may tighten account limits but may not loosen hard account, venue, or challenge limits.
- The profile ID and version must be attached to every session, trade plan, order event, and debrief.

## Global Session State

```text
SESSION_SECURED
  -> SYSTEM_POWER_UP
  -> PRE_MARKET_PREPARATION
  -> MARKET_READY
  -> SETUP_SCAN
  -> ORDER_STAGED
  -> TRADE_LAUNCH
  -> TRADE_MANAGEMENT
  -> TRADE_EXIT
  -> SETUP_SCAN or POST_MARKET_REVIEW
  -> SESSION_SECURING
  -> SESSION_SECURED
```

Emergency and integrity overlays interrupt every normal phase:

```text
RECOVERY_OR_STATE_INTEGRITY_FAILURE  priority 120
MARGIN_OR_STRESS_SURVIVAL_EMERGENCY  priority 110
MAX_DAILY_DRAWDOWN_BREACH            priority 100
API_OR_NETWORK_FAILURE               priority 90
FLASH_CRASH_BLACK_SWAN               priority 80
NORMAL_SESSION_LOGIC                 priority 10
```

`RECOVERY_LOCKED` and `INTEGRITY_FAILURE` are global lock states. They may be entered from any phase and may be exited only through the recovery and verification rules in Sections 10 and 11.

Checklist runtime states: `LOCKED -> AVAILABLE -> ACTIVE -> SATISFIED`, with alternate states `FAILED`, `BLOCKED`, `BYPASSED_WITH_PENALTY`, and `REGRESSED`. A continuous safety item regresses when its valid state is lost after it was satisfied.

---

# 1. Instrument Mapping Table

| Flight Instrument / Control | Trading Dashboard Equivalent | Data Source / System Function |
| --- | --- | --- |
| Airspeed Indicator | `PANEL_MARKET_SPEED` — Market Volatility / Momentum Index | Composite of short-horizon return, ATR, realized volatility, volume acceleration, and order-flow velocity. Shows `SLOW / NORMAL / FAST / EXTREME`. |
| Altimeter | `PANEL_EQUITY_ALTITUDE` — Account Equity / Balance | Broker account snapshot plus internal ledger. Needle shows current equity; reference bugs show session-start equity, high-water mark, and daily-loss floor. |
| Altimeter Setting Knob | `CTRL_EQUITY_BASELINE` — Session Reference Configuration | Loads and locks the daily reference equity, total drawdown reference, and loss-floor method from the active policy profile. Intraday upward reset is prohibited. |
| Vertical-Speed Indicator | `PANEL_PNL_VELOCITY` — P&L Rate of Change | Change in realized plus unrealized P&L per minute and per bar. Positive means climbing; negative means descending. |
| Attitude Indicator | `PANEL_PORTFOLIO_ATTITUDE` — Net Directional Exposure | Net long or short exposure, portfolio beta or delta, and gross leverage. Bank angle represents concentration to one side of the market. |
| Heading Indicator | `PANEL_STRATEGY_HEADING` — Strategy and Regime Alignment | Compares active setup direction with the approved session plan and detected regime: `TREND / RANGE / BREAKOUT / EVENT`. |
| Turn Coordinator | `PANEL_CORRELATION_TURN` — Correlation and Concentration Drift | Portfolio correlation matrix and cluster exposure. Warns when several positions behave as one oversized trade. |
| Fuel Gauges | `PANEL_MARGIN_FUEL` — Available Margin / Buying Power | Broker buying power, used margin, maintenance margin, and reserved margin. Empty zone represents margin-call or forced-liquidation proximity. |
| Fuel Pressure Gauge | `PANEL_LIQUIDITY_PRESSURE` — Immediate Executable Liquidity | Current spread, executable depth, traded volume, fill probability, and expected slippage. Low pressure reduces valid order size and execution aggressiveness. |
| Tachometer | `PANEL_ACTIVITY_RPM` — Order and Trade Activity Rate | Orders, amendments, cancellations, and completed trades per minute. Redline indicates overtrading or request-rate abuse. |
| Manifold Pressure / Throttle | `CTRL_EXPOSURE_THROTTLE` — Position Size and Gross Exposure | Order quantity and portfolio gross exposure. Increasing throttle increases risk only after all safety gates pass. |
| Mixture Control | `CTRL_RISK_MIXTURE` — Risk Budget Allocation | Sets permitted risk intensity for the setup. `CUTOFF` means no risk may be launched; `RICH` is capped by the configured per-trade limit. |
| Elevator Trim Wheel | `CTRL_RISK_TRIM` — Stop-Loss and Risk Adjustment | Moves protective risk only according to the approved management plan. Widening a stop is treated as unsafe nose-up trim. |
| Flap Lever / Indicator | `CTRL_EXECUTION_FLAPS` — Execution Aggressiveness | Maps execution mode: `0° PASSIVE_LIMIT`, `10° JOIN_BEST`, `20° MARKETABLE_LIMIT`, `30° EMERGENCY_REDUCTION`. It does not change strategy risk limits. |
| Radar / Navigation Display | `PANEL_MARKET_RADAR` — Order Book Depth and Chart Structure | Level-2 depth, spread, liquidity gaps, support/resistance, volume profile, and chart patterns. |
| Course Deviation Indicator | `PANEL_PLAN_DEVIATION` — Entry, Stop, and Target Deviation | Measures distance between live price/action and the approved trade plan. Excess deviation blocks or aborts launch. |
| Magnetic Compass | `PANEL_MARKET_COMPASS` — Higher-Timeframe Market Direction | Benchmark trend, higher-timeframe structure, and risk-on/risk-off reference used when the strategy requires directional alignment. |
| Pitot / Static System | `SYS_MARKET_DATA_INTEGRITY` — Price and Volume Data Integrity | Quote freshness, timestamp sequence, gaps, crossed markets, duplicate ticks, and primary-versus-backup feed comparison. |
| Oil Pressure Gauge | `PANEL_RISK_ENGINE_PRESSURE` — Risk Engine Health | Confirms that sizing, limits, stop distance, margin, and aggregate-risk calculations are current and valid. |
| Oil Temperature Gauge | `PANEL_EXECUTION_HEAT` — Latency and Slippage Stress | API latency, order-acknowledgement time, rejection rate, and observed slippage. Rising heat reduces allowed execution aggressiveness. |
| Cylinder-Head / Engine Temperature | `PANEL_STRATEGY_STRESS` — Strategy Regime Stress | Measures how far volatility, spread, liquidity, and market structure have moved outside the strategy's approved operating envelope. |
| Ammeter / Voltmeter | `PANEL_CONNECTIVITY_POWER` — API, Network, and Feed Health | WebSocket heartbeat, REST health, broker session status, internet route, and local service health. |
| Vacuum Gauge | `PANEL_REDUNDANCY_STATUS` — Backup Route Readiness | Availability of secondary market data, backup network, cached state, and alternate broker communication path. |
| Annunciator Panel | `PANEL_RISK_ANNUNCIATOR` — Alerts and Interlocks | Shows `DATA_STALE`, `NEWS_BLACKOUT`, `MARGIN_LOW`, `DAILY_LOSS`, `ORDER_UNKNOWN`, `FLASH_CRASH`, and other state-machine alerts. |
| Stall Warning | `ALERT_MARGIN_STALL` — Liquidation / Risk-Limit Proximity | Triggers when margin reserve, equity buffer, or open-risk capacity approaches the configured hard floor. |
| Master Switch | `CTRL_TRADING_MASTER` — Global Trading Enable / Kill Switch | Controls whether new risk may be opened. Emergency states force it to `OFF`; exit and risk-reduction orders remain allowed. |
| Dual Magnetos | `CTRL_PRIMARY_BACKUP_ROUTE` — Primary and Backup Data / Execution Paths | Primary path handles normal operation; backup path supports verification or controlled recovery. Both must never create duplicate orders. |
| Autopilot | `CTRL_AUTOMATION_MODE` — Automated Strategy Execution | Modes: `OFF / ADVISORY / SUPERVISED / AUTOMATED`. Automation remains subordinate to the same risk and emergency gates. |
| Radio / ATC | `PANEL_EVENT_RADIO` — Economic Calendar, News, and Venue Status | High-impact releases, exchange notices, halts, auctions, market-hours changes, and broker status messages. |
| Clock / Flight Timer | `PANEL_SESSION_CLOCK` — Session and Time-in-Trade Timer | Market timezone, countdown to events, signal age, position age, cooldown timers, and session-close timer. |
| Fuel Selector | `CTRL_CAPITAL_ROUTE` — Strategy / Account Capital Allocation | Selects the approved strategy sleeve or account. A position cannot draw risk from an unapproved allocation. |
| Rudder Pedals | `CTRL_EXECUTION_FINE_TRIM` — Fine Execution Control | Adjusts limit price, time-in-force, cancel/replace, and residual quantity within the approved trade plan and tick/lot constraints. |
| Landing Gear Lever | `CTRL_EXIT_ARM` — Exit Preparation and Capital Preservation | Arms the planned exit sequence, verifies residual exposure and protective-order state, and prepares normal or emergency closure. |
| Brakes | `CTRL_ABORT_AND_FLATTEN` — Cancel / Reduce / Exit Controls | Normal braking cancels staged risk; emergency braking invokes controlled risk reduction or flattening under the emergency policy. |
| Transponder / Aircraft Log | `SYS_AUDIT_TRAIL` — Order IDs and Session Telemetry | Stores strategy ID, signal ID, order ID, idempotency key, fills, changes, warnings, and player actions for replay and debrief. |

## Instrument-State Rules

```text
IF a trading gauge depends on stale or invalid source data
THEN flag the gauge INVALID, remove its green operating range, and block every rule that depends on it
ELSE display the calculated value and its timestamp.

IF a visual gauge and the broker account state disagree
THEN the broker state is authoritative for exposure and orders, while the mismatch triggers reconciliation
ELSE continue normal cockpit operation.
```


## Required Cockpit Panel Architecture

```text
TradingCockpit
├── Market Flight Instruments
│   ├── Momentum / Volatility
│   ├── Market Regime
│   ├── Spread and Liquidity
│   ├── Order Book Depth
│   ├── Trend / Structure
│   └── News and Event Radar
├── Portfolio Flight Instruments
│   ├── Equity / Balance Altimeter
│   ├── Daily and Total Drawdown
│   ├── Equity Velocity
│   ├── Margin / Buying Power
│   ├── Leverage and Concentration
│   ├── Correlation Exposure
│   └── Portfolio VaR / CVaR when enabled
├── Trade Controls
│   ├── Order Ticket
│   ├── Position Size Throttle
│   ├── Stop-Loss / Risk Trim
│   ├── Take-Profit / Exit Plan
│   ├── Risk-to-Reward or Expectancy Gate
│   ├── Partial Exit Controls
│   └── Emergency Cancel / Flatten
├── Navigation and Planning
│   ├── Chart Workspace
│   ├── Support / Resistance Map
│   ├── Economic Calendar
│   ├── Session Planner
│   ├── Strategy Playbook
│   └── Trade Journal / Replay
└── Warning and Emergency
    ├── Rule Annunciators
    ├── Broker and API Health
    ├── Data Freshness
    ├── Network and Backup Route
    ├── Margin Warning
    ├── Daily / Total Drawdown Warning
    └── Emergency Lockout
```

## Core Financial Metric Definitions

### Planned Risk

```text
Risk_Per_Unit =
  abs(Entry_Price - Stop_Price)
  x Value_Per_Price_Unit
  + Estimated_Round_Trip_Fees_Per_Unit
  + Slippage_Reserve_Per_Unit

Planned_Risk =
  Quantity x Risk_Per_Unit
  + Gap_Risk_Allowance
```

### Net Planned Reward and Risk-to-Reward

```text
Gross_Planned_Reward =
  abs(Target_Price - Entry_Price)
  x Quantity
  x Value_Per_Price_Unit

Net_Planned_Reward =
  Gross_Planned_Reward
  - Estimated_Round_Trip_Fees
  - Estimated_Entry_And_Exit_Slippage

Net_Risk_Reward =
  Net_Planned_Reward / Planned_Risk
```

### Allowed Position Size

```text
Allowed_Position_Size =
  round_down_to_lot_step(
    min(
      Size_By_Risk_Budget,
      Size_By_Margin,
      Size_By_Symbol_Limit,
      Size_By_Portfolio_Limit,
      Size_By_Correlation_Limit,
      Size_By_Liquidity,
      Size_By_Strategy
    )
  )
```

### Drawdown

```text
Policy_Measured_Equity =
  value selected by Daily_Loss_Method

Daily_Drawdown =
  Daily_Reference_Equity - Policy_Measured_Equity

Total_Drawdown =
  Total_Reference_Equity - Current_Equity
```

Supported `Daily_Loss_Method` values:

| Method | Reference and Included Values |
| --- | --- |
| `STATIC_START_EQUITY` | Session-start equity versus current equity |
| `TRAILING_HIGH_WATER` | Intraday high-water equity versus current equity |
| `REALIZED_ONLY` | Session-start balance versus realized P&L and costs |
| `REALIZED_PLUS_UNREALIZED` | Session-start equity versus current equity including open P&L and costs |
| `PROP_FIRM_PROFILE` | Exact account-provider rule stored in the selected policy profile |


### Drawdown Escalation States

```text
Drawdown_Usage =
  max(Daily_Drawdown / Effective_Daily_Loss_Limit,
      Total_Drawdown / Effective_Total_Drawdown_Limit)
```

| State | Default Trigger | Gameplay Effect |
| --- | --- | --- |
| `NORMAL` | `Drawdown_Usage < 0.50` | Normal policy limits apply |
| `CAUTION` | `0.50 <= Drawdown_Usage < 0.75` | Amber alert; player must acknowledge risk trend |
| `RESTRICTED` | `0.75 <= Drawdown_Usage < 0.90` | Position-size cap reduced; stricter setup gates apply |
| `CRITICAL` | `0.90 <= Drawdown_Usage < 1.00` | New entries blocked in Guided Mode; emergency readiness armed |
| `LOCKED` | `Drawdown_Usage >= 1.00` | Drawdown emergency activates; new risk disabled |

The threshold ratios are policy-profile defaults and may be replaced by exact account or challenge rules.

### Market Execution Safety

```text
MARKET_EXECUTION_SAFE =
  Spread <= Effective_Max_Spread
  AND Executable_Depth >= Effective_Min_Depth
  AND Quote_Age <= Effective_Max_Quote_Age
  AND Volatility <= Strategy_Max_Volatility
  AND Market_Status is permitted
```

---

# 2. Phase Checklists

## 2.1 Pre-Market Preparation — Pre-Flight

| Step ID | Action | Cockpit Panel | Expected State | Validation Logic |
| --- | --- | --- | --- | --- |
| PRE_001 | Trading mode — select simulator account | `CTRL_TRADING_MASTER`, account selector | `Mode = SIMULATION`; approved account ID loaded | IF `Mode != SIMULATION` THEN keep master `OFF` and block the session; ELSE load the selected simulated account. |
| PRE_002 | Trading cockpit — initialize | Cockpit shell and service-status panel | All required modules report `READY` within `30 s` | IF any required service is `FAILED` THEN set `SESSION_STATE = SYSTEM_BLOCKED`; ELSE continue. |
| PRE_003 | Clock and timezone — synchronize | `PANEL_SESSION_CLOCK` | Clock drift `<= 250 ms`; market timezone correct | IF clock drift exceeds `250 ms` THEN block time-sensitive signals and event windows; ELSE mark synchronized. |
| PRE_004 | Execution gateway — test connection | `PANEL_CONNECTIVITY_POWER` | Broker/API heartbeat `HEALTHY`; round-trip latency `<= 1000 ms` | IF authentication fails OR heartbeat is missing THEN set `OBSERVE_ONLY`; ELSE enable order staging. |
| PRE_005 | Primary market-data feed — verify | `SYS_MARKET_DATA_INTEGRITY` | Streaming; quote age `<= 2 s`; timestamps monotonic | IF quotes are stale, duplicated, crossed, or out of order THEN block trade launch; ELSE accept the feed. |
| PRE_006 | Backup data and network path — verify | `PANEL_REDUNDANCY_STATUS` | At least one backup read path reports `AVAILABLE` | IF backup is unavailable THEN show `REDUNDANCY_DEGRADED`; ELSE mark failover ready. This is a warning unless the scenario requires redundancy. |
| PRE_007 | Account snapshot — load | `PANEL_EQUITY_ALTITUDE`, `PANEL_MARGIN_FUEL` | Equity, cash, buying power, margin, and currency values are present | IF any account field is null, negative unexpectedly, or older than `5 s` THEN block risk calculations; ELSE store snapshot. |
| PRE_008 | Positions — reconcile broker and internal state | Portfolio attitude and reconciliation panel | Symbol, side, quantity, average price, and P&L match exactly within instrument tolerance | IF any mismatch exists THEN set `POSITION_STATE = UNKNOWN` and block new entries; ELSE mark reconciled. |
| PRE_009 | Working orders — reconcile | Order blotter and audit panel | All open, pending, canceled, and filled states agree with broker | IF an order is missing or duplicated THEN block new entries until resolved; ELSE mark order state known. |
| PRE_010 | Market schedule — confirm | `PANEL_EVENT_RADIO`, session clock | Venue is `OPEN` or scheduled to open inside the configured preparation window | IF venue is closed, halted, or in an unsupported auction THEN keep entry master `OFF`; ELSE load session boundaries. |
| PRE_011 | Economic calendar — review | `PANEL_EVENT_RADIO` | Calendar loaded for the full session; all high-impact events visible | IF calendar data is unavailable THEN apply `NEWS_DATA_UNKNOWN` and block event-sensitive strategies; ELSE mark reviewed. |
| PRE_012 | High-impact event windows — mark | Session timeline and warning panel | Default blackout: `T-15 min` through `T+5 min` for affected instruments | IF an entry time falls inside a blackout THEN block launch; ELSE allow normal validation. |
| PRE_013 | Instrument-specific events — review | Watchlist event column | Earnings, auctions, roll dates, dividends, splits, and major scheduled notices tagged when applicable | IF a required event flag is missing or unresolved THEN remove the instrument from the eligible watchlist; ELSE continue. |
| PRE_014 | Session-start equity — lock | `PANEL_EQUITY_ALTITUDE` | Reference altitude equals first reconciled session equity; default `$100,000` | IF start equity is not locked before the first order THEN block all risk percentages; ELSE prevent intraday manual reset. |
| PRE_015 | Maximum daily loss — set | Risk limit panel and altimeter floor bug | Default `2.00%` of session-start equity including fees and unrealized P&L | IF value is absent, above configured maximum, or changed after launch THEN keep master `OFF`; ELSE lock the limit. |
| PRE_016 | Maximum risk per trade — set | `CTRL_RISK_MIXTURE`, risk panel | Default `0.50%` of current equity | IF limit is absent or exceeds policy THEN block entry sizing; ELSE lock it for the session. |
| PRE_017 | Maximum aggregate open risk — set | Portfolio risk panel | Default `1.50%` of current equity across positions and staged orders | IF aggregate cap is absent THEN block new risk; ELSE include pending orders in the calculation. |
| PRE_018 | Maximum gross leverage — set | Exposure throttle and attitude panel | Default `2.00x` equity | IF projected gross leverage exceeds `2.00x` THEN block launch; ELSE reserve capacity. |
| PRE_019 | Margin / buying-power reserve — set | `PANEL_MARGIN_FUEL` | Post-trade reserve `>= 30%` of equity | IF projected reserve is below `30%` THEN block launch and display `INSUFFICIENT FUEL RESERVE`; ELSE continue. |
| PRE_020 | Trade-count and cooldown limits — set | Activity tachometer and timer | Default maximum `10` launches; `15 min` cooldown after two consecutive losses | IF counters cannot be loaded or reset lawfully THEN keep entry master `OFF`; ELSE arm counters. |
| PRE_021 | Watchlist — approve instruments | Market radar and watchlist panel | Every instrument has venue, tick size, point value, trading hours, and risk profile | IF metadata is incomplete THEN mark instrument `INELIGIBLE`; ELSE add it to the approved watchlist. |
| PRE_022 | Liquidity and spread baseline — record | Order-book radar | Median spread and visible depth calculated from at least `20 min` or configured history | IF baseline sample is insufficient THEN restrict to observation or apply a conservative instrument profile; ELSE store baseline. |
| PRE_023 | Market regime — classify | Market compass and heading panel | One state selected: `TREND`, `RANGE`, `BREAKOUT`, `EVENT`, or `UNCERTAIN` | IF regime is `UNCERTAIN` and strategy requires a known regime THEN strategy remains disarmed; ELSE record state. |
| PRE_024 | Key support and resistance — mark | Chart navigation display | At least one relevant support, resistance, invalidation zone, and opening reference marked | IF levels are missing for a level-dependent strategy THEN block that strategy; ELSE store prices and timestamps. |
| PRE_025 | Volatility baseline — calculate | Market-speed gauge | `ATR_14`, realized volatility, and current speed state available | IF volatility inputs are stale or unavailable THEN block volatility-sized entries; ELSE store the baseline. |
| PRE_026 | Long scenario — define | Strategy heading and plan-deviation panel | Entry trigger, invalidation, target, and no-trade conditions recorded | IF any required field is empty THEN long setups remain `LOCKED`; ELSE mark long scenario available. |
| PRE_027 | Short scenario — define | Strategy heading and plan-deviation panel | Entry trigger, invalidation, target, and no-trade conditions recorded | IF any required field is empty THEN short setups remain `LOCKED`; ELSE mark short scenario available. |
| PRE_028 | No-trade conditions — define | Risk annunciator panel | At minimum: stale data, blackout, excessive spread, low depth, risk limit, and regime mismatch | IF no-trade rules are absent THEN entry master remains `OFF`; ELSE arm automatic blockers. |
| PRE_029 | Price and event alerts — set | Market radar and session timeline | Alerts placed at planned triggers, invalidation levels, and event windows | IF alerts do not match the approved plan THEN warn and require correction; ELSE activate them. |
| PRE_030 | Strategy and signal modules — test | Automation and signal-health panel | Selected strategy reports `READY`; no signal older than one strategy bar | IF a module errors or emits a stale signal THEN disarm that strategy; ELSE enable advisory output. |
| PRE_031 | Emergency kill switch — test | `CTRL_TRADING_MASTER`, abort control | With no open position, test forces entries `OFF` and still permits cancel/exit actions | IF test cannot block new entries OR also blocks risk-reducing exits THEN mark `CRITICAL` and stop the session; ELSE reset to `OFF`. |
| PRE_032 | Total drawdown floor and drawdown method — verify | Equity altimeter, drawdown panel, policy profile | Daily and total reference values loaded; selected calculation method explicit | IF the drawdown method, reference equity, or hard floor is missing THEN block risk arming; ELSE lock the values for the session. |
| PRE_033 | Portfolio correlation and existing exposure — review | Correlation turn coordinator and portfolio attitude | Current cluster, symbol, sector, currency, beta, or delta exposure within profile | IF existing exposure already breaches a hard limit THEN allow only reduction; ELSE store the exposure baseline. |
| PRE_034 | Session process objective — define | Session planner and discipline panel | At least one measurable process objective recorded; profit-only objective is insufficient | IF no process objective exists in assessment mode THEN block final cockpit arming; ELSE attach it to the debrief rubric. |
| PRE_035 | Assessment mode and challenge overlay — confirm | Master cockpit state and scenario panel | Base mode, policy profile version, and optional challenge scenario are explicit | IF mode or profile is unresolved THEN keep entry master `OFF`; ELSE freeze the session configuration. |
| PRE_036 | Pre-market clearance — complete | Master switch and checklist panel | `PRE_MARKET_READY = TRUE`; master may move to `ARMED` | IF every mandatory item is satisfied THEN set `SESSION_STATE = MARKET_READY`; ELSE list blockers and keep new entries disabled. |

### State Logic Breakdown

```text
PRE_MARKET_READY =
  SIMULATION_MODE
  AND SYSTEMS_READY
  AND CLOCK_SYNCHRONIZED
  AND EXECUTION_CONNECTED
  AND DATA_VALID
  AND ACCOUNT_RECONCILED
  AND POSITIONS_RECONCILED
  AND ORDERS_RECONCILED
  AND CALENDAR_REVIEWED
  AND RISK_LIMITS_LOCKED
  AND WATCHLIST_ELIGIBLE
  AND LEVELS_AND_SCENARIOS_DEFINED
  AND TOTAL_DRAWDOWN_RULE_VALID
  AND PORTFOLIO_EXPOSURE_REVIEWED
  AND SESSION_OBJECTIVE_DEFINED
  AND MODE_AND_PROFILE_CONFIRMED
  AND KILL_SWITCH_TEST_PASSED

IF PRE_MARKET_READY == TRUE
THEN set SESSION_STATE = MARKET_READY and allow setup scanning
ELSE keep ENTRY_ENABLE = OFF and show exact blocking steps.
```

- A correctly identified no-trade day is a passing outcome. The system must not force the player to launch a position.
- An account, position, or order mismatch is a hard block even when the market-data feed appears healthy.
- Risk limits become immutable after the first launch attempt. Reducing a limit is allowed only through a governed risk action; increasing it is not.

## 2.2 Trade Launch — Takeoff

| Step ID | Action | Cockpit Panel | Expected State | Validation Logic |
| --- | --- | --- | --- | --- |
| ENTRY_001 | Trade setup — select approved setup ID | Strategy heading panel | Setup belongs to an armed strategy and approved watchlist | IF setup ID is missing, disabled, or not approved today THEN block the ticket; ELSE load its rules. |
| ENTRY_002 | Instrument and venue — verify tradable | Market radar and event radio | `Market_Status = OPEN`; instrument not halted or restricted | IF halted, closed, auction-only, or restricted THEN block launch; ELSE continue. |
| ENTRY_003 | Signal — verify fresh and valid | Signal-health panel and clock | Signal age `<= 1 strategy bar`; all required features current | IF signal is stale, withdrawn, or based on missing data THEN invalidate the setup; ELSE continue. |
| ENTRY_004 | Direction — compare with session plan and regime | Heading and compass panels | Direction is allowed by the approved long or short scenario | IF direction conflicts with the plan AND no preconfigured exception profile applies THEN block launch; ELSE continue. |
| ENTRY_005 | Entry trigger and price — set | Plan-deviation display and order ticket | Exact trigger and intended entry price recorded | IF live price has moved beyond configured chase tolerance, default `0.25R`, THEN cancel the setup; ELSE stage the entry. |
| ENTRY_006 | Initial stop / invalidation — set | `CTRL_RISK_TRIM`, order ticket | Stop price is non-null and represents strategy invalidation | IF no stop is defined THEN block launch; ELSE calculate stop distance. |
| ENTRY_007 | Profit target — set | Navigation display and order ticket | At least first planned target is non-null | IF target is missing for a target-based strategy THEN block launch; ELSE calculate expected reward. |
| ENTRY_008 | Stop side and distance — validate | Risk engine pressure gauge | Long stop below entry; short stop above entry; distance `>= max(3 ticks, 0.25 ATR)` | IF stop is on the wrong side or too close to market structure rules THEN block launch; ELSE accept distance. |
| ENTRY_009 | Risk-to-reward or expectancy — validate | Risk/reward tape and strategy profile | Net planned ratio meets `Effective_Min_RR`, or an explicitly approved expectancy profile passes | IF `Net_Risk_Reward < Effective_Min_RR` AND no approved expectancy exception applies THEN prevent launch and display `UNSAFE TRIM SETTING`; ELSE continue. |
| ENTRY_010 | Risk budget — assign | `CTRL_RISK_MIXTURE` and risk panel | Worst-case initial loss `<= Effective_Max_Risk_Per_Trade` (default `0.50%` of equity) | IF projected loss exceeds the effective cap THEN reduce size or block launch; ELSE reserve risk. |
| ENTRY_011 | Position size — calculate | Exposure throttle and sizing panel | Quantity equals `Allowed_Position_Size` from the core metric definition | IF manual quantity exceeds the calculated maximum by more than one lot step THEN block; ELSE accept the lower valid size. |
| ENTRY_012 | Quantity increment — round down | Order ticket | Quantity matches venue lot size and minimum increment | IF quantity is invalid or rounded up beyond the risk cap THEN block; ELSE store final quantity. |
| ENTRY_013 | Projected gross leverage — check | Portfolio attitude and exposure throttle | Post-fill gross leverage `<= Effective_Max_Leverage` (default `2.00x`) | IF projected leverage exceeds the effective cap THEN reduce quantity or block launch; ELSE continue. |
| ENTRY_014 | Projected margin reserve — check | `PANEL_MARGIN_FUEL` | Reserve after fill `>= Effective_Min_Margin_Reserve` (default `30%` of equity) | IF reserve would fall below the effective minimum THEN block and show `FUEL BELOW DISPATCH MINIMUM`; ELSE continue. |
| ENTRY_015 | Aggregate open risk — check | Portfolio risk panel | Existing plus staged plus proposed risk `<= Effective_Max_Open_Risk` (default `1.50%` of equity) | IF aggregate risk exceeds the effective cap THEN block or require risk reduction first; ELSE continue. |
| ENTRY_016 | Single-instrument concentration — check | Turn coordinator and exposure panel | Projected notional exposure `<= Effective_Max_Symbol_Exposure` (default `25%` of equity) | IF concentration exceeds the effective limit THEN reduce size or block; ELSE continue. |
| ENTRY_017 | Correlation-cluster exposure — check | Correlation turn coordinator | Projected cluster exposure and risk remain within `Effective_Max_Correlated_Exposure` | IF correlated positions create an oversized combined trade THEN block; ELSE continue. |
| ENTRY_018 | Quote freshness — recheck at launch | Pitot/static data-integrity panel | Quote and book age `<= Effective_Max_Quote_Age` (default `2 s`) | IF data becomes stale before submit THEN return ticket to `STAGED`; ELSE continue. |
| ENTRY_019 | Spread — verify | Order-book radar | Current spread `<= Effective_Max_Spread`, including relative and hard instrument limits | IF spread exceeds either effective limit THEN block launch; ELSE continue. |
| ENTRY_020 | Order-book depth and expected slippage — verify | Order-book radar and execution-heat gauge | Visible executable depth covers quantity; expected slippage `<= 0.10R` | IF depth is insufficient or slippage exceeds `0.10R` THEN reduce size, use a passive order, or block launch. |
| ENTRY_021 | Economic-event blackout — recheck | Event radio and session clock | Current time outside every applicable blackout window | IF inside blackout THEN block launch regardless of setup quality; ELSE continue. |
| ENTRY_022 | Order type and time-in-force — select | `CTRL_EXECUTION_FLAPS`, order ticket | Order type is supported and matches strategy; TIF is explicit | IF order type can exceed permitted slippage or TIF is undefined THEN block; ELSE stage the order. |
| ENTRY_023 | Protective bracket — configure | Order ticket and risk trim | Stop and target linked as broker-side bracket or OCO when supported | IF the venue supports server-side protection and bracket is absent THEN block launch; ELSE record fallback policy. |
| ENTRY_024 | Idempotency key — generate and lock | Audit/transponder panel | Unique key tied to account, setup, instrument, side, and launch attempt | IF key is missing or reused for a different order intent THEN block submit; ELSE store it. |
| ENTRY_025 | Final ticket — cross-check | Central launch checklist | Symbol, side, quantity, order type, price, stop, target, risk, and TIF match the approved plan | IF any field differs from the approved ticket THEN return to the affected step; ELSE show `CLEARED FOR LAUNCH`. |
| ENTRY_026 | Entry order — submit once | Launch control and order blotter | Exactly one request sent with the locked idempotency key | IF submit is repeated before the first state is known THEN block duplicate transmission; ELSE await acknowledgement. |
| ENTRY_027 | Broker acknowledgement — verify | Connectivity power and order blotter | Acknowledgement received inside `3 s` or instrument-specific timeout | IF timeout occurs THEN mark order `UNKNOWN`, freeze retries, and enter API-outage logic; ELSE continue. |
| ENTRY_028 | Partial fill — protect filled quantity immediately | Order blotter and risk trim | Protective stop quantity equals cumulative fill quantity | IF any filled quantity is unprotected beyond `1 s` when server-side protection is available THEN trigger `CRITICAL` warning and emergency protection. |
| ENTRY_029 | Remaining entry quantity — decide | Order blotter and market radar | Explicit state: `CONTINUE`, `REPRICE_WITHIN_PLAN`, or `CANCEL` | IF remaining order would violate chase, spread, time, or risk limits THEN cancel it; ELSE retain only under the original plan. |
| ENTRY_030 | Fill price and slippage — validate | Execution-heat gauge | Average fill deviation `<= configured limit` and total initial risk remains within cap | IF slippage pushes risk or net reward outside limits THEN cancel remainder and reduce or exit according to policy; ELSE accept fill. |
| ENTRY_031 | Protective stop — verify live | Risk annunciator and order blotter | Accepted stop exists for full open quantity and correct side | IF stop is rejected, canceled, or undersized THEN block management mode and require immediate protection or exit. |
| ENTRY_032 | Profit target — verify live | Navigation display and order blotter | Target accepted for intended quantity or staged scale-out quantities | IF target is rejected THEN warn and require correction; stop protection remains mandatory. |
| ENTRY_033 | Position — reconcile after fill | Portfolio attitude and reconciliation panel | Broker and internal quantity, side, average price, stop, and target agree | IF mismatch exists THEN set `POSITION_STATE = UNKNOWN` and block any new entry; ELSE mark position open. |
| ENTRY_034 | Trade launch — complete | Master checklist and active-trade display | `TRADE_STATE = ACTIVE`; continuous monitoring enabled | IF all launch steps are satisfied THEN enter `TRADE_MANAGEMENT`; ELSE remain blocked or execute the relevant emergency branch. |

### State Logic Breakdown

```text
TRADE_LAUNCH_ALLOWED =
  PRE_MARKET_READY
  AND MARKET_OPEN
  AND SIGNAL_VALID
  AND DATA_FRESH
  AND OUTSIDE_NEWS_BLACKOUT
  AND STOP_VALID
  AND RISK_REWARD_OR_EXPECTANCY_GATE_PASSED
  AND TRADE_RISK <= EFFECTIVE_MAX_TRADE_RISK
  AND AGGREGATE_RISK <= EFFECTIVE_MAX_OPEN_RISK
  AND GROSS_LEVERAGE <= EFFECTIVE_MAX_LEVERAGE
  AND MARGIN_RESERVE >= EFFECTIVE_MIN_MARGIN_RESERVE
  AND LIQUIDITY_VALID
  AND TICKET_RECONCILED

IF TRADE_LAUNCH_ALLOWED == TRUE
THEN permit one idempotent submit
ELSE block submit and identify the failed gate.
```

- Launch clearance is evaluated again at submit time. A setup can regress from `CLEARED` to `BLOCKED` when price, spread, depth, data age, or event state changes.
- Clicking a checklist row must never place or modify an order. Only the actual order-ticket control may change broker state.
- A partial fill creates immediate live risk. Protection must follow filled quantity, not requested quantity.

## 2.3 Trade Management — In-Flight

| Step ID | Action | Cockpit Panel | Expected State | Validation Logic |
| --- | --- | --- | --- | --- |
| MGT_001 | Position, stop, target, and P&L — keep visible | Central trade panel | All values update from reconciled broker state | IF any value becomes unknown or stale THEN freeze amendments and invoke reconciliation; ELSE continue. |
| MGT_002 | Trade thesis and invalidation — monitor | Plan-deviation and chart navigation panels | Setup remains valid; invalidation flag is `FALSE` | IF invalidation condition becomes true THEN initiate exit; ELSE continue management. |
| MGT_003 | Open risk — recalculate continuously | Risk engine pressure gauge | Risk includes current stop, fees, slippage reserve, and every open position | IF risk calculation fails THEN block scale-ins and stop changes; ELSE update the risk panel. |
| MGT_004 | Stop widening — prohibited | `CTRL_RISK_TRIM` | New stop cannot increase worst-case loss beyond approved initial risk | IF long stop moves lower OR short stop moves higher without an explicit emergency profile THEN reject the change and apply a critical discipline penalty; ELSE continue. |
| MGT_005 | Stop adjustment — require a plan trigger | `CTRL_RISK_TRIM` and strategy rules | Trigger ID recorded before stop moves | IF no valid trigger exists THEN reject the adjustment; ELSE allow only risk-neutral or risk-reducing movement. |
| MGT_006 | Break-even trim — apply only when eligible | Risk trim and P&L velocity | Configured profit threshold reached, default `+1.0R`; market structure still valid | IF threshold or structure rule is not met THEN reject break-even move; ELSE set stop no worse than entry plus costs. |
| MGT_007 | Trailing stop — follow configured method | Risk trim and chart navigation | Trail references the defined ATR, swing, or time rule | IF player drags the stop without a matching rule event THEN reject and score as discretionary deviation; ELSE accept. |
| MGT_008 | Partial exit / position trim — validate | Exposure throttle and execution flaps | Reduction quantity follows the planned scale-out and leaves valid residual protection | IF residual stop quantity does not equal residual position quantity THEN block completion and repair protection. |
| MGT_009 | Scale-in — permit only when preplanned | Exposure throttle and strategy plan | Scale-in trigger exists; total risk after fill remains within all original caps | IF scale-in is unplanned, adds to a losing position outside policy, or breaches risk THEN block it. |
| MGT_010 | Post-amendment risk gates — recheck | Risk engine, margin fuel, correlation turn coordinator | Per-trade, aggregate risk, leverage, margin, and concentration all pass | IF any gate fails after an amendment request THEN reject the request; ELSE transmit once. |
| MGT_011 | Margin reserve — monitor | `PANEL_MARGIN_FUEL` and stall alert | Reserve remains above effective caution and hard floors | IF reserve falls below `Effective_Margin_Caution` THEN warn; IF below `Effective_Min_Margin_Reserve` THEN block added risk and require reduction. |
| MGT_012 | Spread and depth — monitor | Market radar and execution-heat gauge | Execution conditions remain within management limits | IF liquidity collapses THEN block nonessential amendments and prepare emergency reduction logic; ELSE continue. |
| MGT_013 | Scheduled event timer — monitor | Event radio and session clock | Position complies with hold-through-event policy | IF a prohibited event window begins while position is open THEN reduce or exit before the deadline; ELSE continue. |
| MGT_014 | Time stop — enforce | Session clock and strategy timer | Maximum holding time not exceeded | IF time stop expires and no approved extension exists THEN initiate exit; ELSE continue. |
| MGT_015 | Profit target — execute | Navigation display and order blotter | Target fill recognized and remaining orders adjusted | IF target fills THEN update position and protection; ELSE keep monitoring. |
| MGT_016 | Protective stop — execute | Risk annunciator and order blotter | Stop fill recognized; remaining targets canceled | IF stop fills THEN prohibit immediate unplanned re-entry and start cooldown; ELSE keep monitoring. |
| MGT_017 | Manual exit — select valid reason | Abort/flatten control | Reason in set: `THESIS_INVALID`, `TIME_STOP`, `EVENT_RISK`, `LIQUIDITY_RISK`, `SYSTEM_RISK`, `SESSION_CLOSE` | IF reason is absent THEN allow risk reduction but record a process violation; ELSE log the reason. |
| MGT_018 | Re-entry after loss — observe cooldown | Activity tachometer and timer | Default cooldown `15 min` after two consecutive losses | IF cooldown is active THEN block new launches; ELSE reset eligibility when timer and review conditions pass. |
| MGT_019 | Order rejection or unknown state — stop amendments | Connectivity power and order blotter | Order state is known before any replacement request | IF state is `UNKNOWN` THEN invoke API-outage checklist; ELSE handle the rejection once. |
| MGT_020 | Daily and total drawdown — monitor continuously | Equity altimeter and drawdown panel | `Drawdown_Usage < 1.00`; state reflects the configured escalation band | IF `Drawdown_Usage >= 1.00` THEN invoke drawdown-breach emergency immediately; ELSE apply the current escalation-state restrictions. |
| MGT_021 | Session-close boundary — manage | Session clock and event radio | Position closed or explicitly approved for overnight holding before cutoff | IF cutoff arrives without approval THEN initiate exit; ELSE transfer to overnight-risk state. |
| MGT_022 | Behavioral override and plan adherence — monitor | Discipline / behavior panel | No revenge entry, impulsive doubling, unplanned stop widening, or excessive order churn | IF a configured behavior pattern is detected THEN warn, require a pause, or block exposure-increasing actions according to mode; always log the event. |
| MGT_023 | Position-control owner — confirm | Position panel and automation control | Each position is owned by `PLAYER`, `SUPERVISED_AUTOMATION`, or `AUTOMATION`; ownership and exit authority are explicit | IF ownership becomes unknown or automation is disabled without a handoff THEN raise `ORPHANED_POSITION_CONTROL` and require immediate reassignment or exit. |

### State Logic Breakdown

```text
IF an amendment increases worst-case loss, leverage, aggregate risk, or correlation exposure
THEN reject the amendment
ELSE validate it against the approved management trigger and transmit once.

IF the thesis invalidates, the time stop expires, the daily loss floor is touched, or system state becomes unsafe
THEN transition TRADE_STATE to EXITING or EMERGENCY
ELSE remain in TRADE_MANAGEMENT.
```

- “Trimming the aircraft” means reducing risk: moving a stop toward less loss, reducing quantity, or lowering gross exposure. It never means widening the stop.
- Every scale-in is treated as a new launch and must pass the same risk, margin, data, liquidity, and event gates.
- Profit alone is not a valid management trigger. The configured strategy rule must identify the action.

## 2.4 Trade Exit — Landing

| Step ID | Action | Cockpit Panel | Expected State | Validation Logic |
| --- | --- | --- | --- | --- |
| EXIT_001 | Exit trigger — confirm | Strategy panel, timer, target/stop, or emergency panel | One explicit trigger ID recorded | IF trigger is valid THEN set `TRADE_STATE = EXITING`; ELSE a voluntary reduction is allowed but logged as deviation. |
| EXIT_002 | Unused entry and scale orders — cancel | Order blotter | No order remains that can increase exposure | IF any exposure-increasing order remains active THEN block exit completion; ELSE continue. |
| EXIT_003 | Exit order type — choose for current liquidity | `CTRL_EXECUTION_FLAPS` and market radar | Normal: limit or marketable limit; emergency: configured reduction mode | IF selected order can create uncontrolled slippage under current depth THEN require a safer type or staged reduction. |
| EXIT_004 | Exit order — submit once | Abort/flatten control and audit panel | One request with unique idempotency key | IF state is unknown after submit THEN do not send a new intent; invoke outage logic. |
| EXIT_005 | Exit fill and slippage — verify | Execution-heat gauge and order blotter | Fill state and average price known; slippage recorded | IF partial fill remains THEN protect residual quantity and continue controlled exit; ELSE continue. |
| EXIT_006 | Residual position — verify | Portfolio attitude panel | Quantity `= 0` or approved overnight quantity | IF unintended residual exists THEN continue exit; ELSE proceed. |
| EXIT_007 | Orphan stop and target orders — cancel | Order blotter | No protective or target order remains without a matching position | IF orphan order exists THEN cancel and reconcile; ELSE continue. |
| EXIT_008 | Broker and internal state — reconcile | Reconciliation panel | Position and order states match exactly | IF mismatch exists THEN keep trade state `EXITING_UNKNOWN`; ELSE mark reconciled. |
| EXIT_009 | Trade — mark closed or overnight | Audit/transponder panel | `CLOSED` when flat; `OVERNIGHT_APPROVED` only with required risk record | IF neither state is valid THEN block phase completion; ELSE stamp closing time and reason. |
| EXIT_010 | Post-trade cooldown — start when required | Session clock and activity tachometer | Loss and overtrading rules update immediately | IF cooldown trigger is met THEN lock new launches until expiry; ELSE return to setup scan. |

### State Logic Breakdown

```text
EXIT_COMPLETE =
  NO_EXPOSURE_INCREASING_ORDER
  AND POSITION_STATE in {FLAT, OVERNIGHT_APPROVED}
  AND NO_ORPHAN_PROTECTIVE_ORDER
  AND BROKER_INTERNAL_STATE_MATCH

IF EXIT_COMPLETE == TRUE
THEN mark trade CLOSED or OVERNIGHT_APPROVED
ELSE keep TRADE_STATE = EXITING or EXITING_UNKNOWN.
```

## 2.5 Post-Market Review — Post-Flight

| Step ID | Action | Cockpit Panel | Expected State | Validation Logic |
| --- | --- | --- | --- | --- |
| POST_001 | New trade launches — disable | `CTRL_TRADING_MASTER` | `ENTRY_ENABLE = OFF`; cancel/exit remains available | IF any strategy can still open new risk THEN session cannot enter post-market state; ELSE continue. |
| POST_002 | Working entry and scale orders — cancel | Order blotter | No order can increase exposure | IF an exposure-increasing order remains active THEN block session closure; ELSE continue. |
| POST_003 | Intraday positions — flatten | Portfolio attitude and abort control | Quantity `= 0` for every intraday-only position | IF any intraday position remains after cutoff THEN trigger a major fail and controlled exit. |
| POST_004 | Overnight positions — validate | Overnight-risk panel | Each retained position has approval, stop, size, gap-risk allowance, and next-session plan | IF any field is missing THEN require reduction or exit; ELSE mark overnight. |
| POST_005 | Positions and orders — final reconciliation | Reconciliation panel | Broker and internal ledgers match exactly | IF mismatch exists THEN keep session `OPEN_FOR_RECONCILIATION`; ELSE continue. |
| POST_006 | Final account snapshot — capture | Equity altimeter and margin fuel | Equity, cash, margin, buying power, and currency timestamped | IF snapshot is stale or incomplete THEN retry before closure; ELSE store immutable close snapshot. |
| POST_007 | Daily P&L — calculate | P&L velocity and summary panel | Realized, unrealized, fees, financing, and total P&L reconcile to equity change | IF components do not reconcile within `$0.01` or currency tolerance THEN flag discrepancy; ELSE accept. |
| POST_008 | Execution costs — record | Execution-heat panel | Fees, spread cost, slippage, and rejected-order count stored per trade | IF cost data is missing THEN mark journal incomplete; ELSE continue. |
| POST_009 | Trade log — complete each record | Audit/transponder log | Setup ID, signal, entry, size, stop, target, exit, P&L, and timestamps present | IF any required field is missing THEN block journal completion; ELSE finalize record. |
| POST_010 | Chart evidence — attach | Market radar replay | Before-entry, management, and exit snapshots linked to each trade when available | IF evidence is required by mode and absent THEN apply documentation penalty; ELSE continue. |
| POST_011 | Trade rationale — record | Journal panel | Reason for entry and expected scenario match the pre-market plan | IF rationale was created only after the trade and differs from the launch record THEN flag hindsight mismatch. |
| POST_012 | Plan versus execution — compare | Plan-deviation panel | Entry, stop changes, scale actions, and exit compared with approved rules | IF any deviation exists THEN classify it as justified, procedural, major, or critical. |
| POST_013 | Risk compliance — verify | Risk engine report | No per-trade, aggregate, leverage, margin, or daily-loss rule omitted | IF a breach occurred THEN include exact timestamp and consequence in the debrief. |
| POST_014 | Behavior and decision-quality tags — assign | Journal panel | Tags selected from controlled vocabulary such as `PATIENT`, `CHASED`, `REVENGE`, `PLAN_FOLLOWED` | IF a tag conflicts with event evidence THEN use telemetry-derived classification and flag disagreement. |
| POST_015 | Emergency events — review | Emergency log | Trigger, player response, response time, and recovery state recorded | IF an emergency occurred without a closed incident record THEN block session closure. |
| POST_016 | Performance metrics — update | Session scorecard | Win/loss, expectancy, average R, drawdown, MAE, MFE, and rule-adherence metrics recalculated by setup, regime, session, and instrument | IF data set is incomplete THEN mark metric provisional; ELSE store final values. |
| POST_017 | Daily journal summary — complete | Journal panel | What worked, what failed, one corrective action, and next-session constraint recorded | IF summary is empty in assessment mode THEN session score remains incomplete; ELSE continue. |
| POST_018 | Daily risk result — lock | Equity altimeter and risk panel | Start equity, end equity, max drawdown, and breach state immutable | IF player attempts to reset the baseline intraday THEN reject and apply critical integrity penalty. |
| POST_019 | Dashboard alerts and temporary drawings — reset | Cockpit dashboard | Transient alerts cleared; permanent logs and planned levels preserved according to profile | IF reset removes audit evidence THEN restore from immutable telemetry; ELSE continue. |
| POST_020 | Counters and session state — persist | Activity tachometer and session store | Trade count, loss streak, cooldown, score, and open overnight state saved | IF persistence fails THEN keep session open and display `SECURING INCOMPLETE`. |
| POST_021 | API and data sessions — disconnect safely | Connectivity power panel | No unacknowledged order; subscriptions closed; credentials released from active session memory | IF an order state is unknown THEN do not disconnect until reconciliation; ELSE shut down connections. |
| POST_022 | Trading cockpit — secure | Master switch and final checklist | `SESSION_STATE = SECURED`; master `OFF`; audit package complete | IF all post-market items pass THEN close session; ELSE show unresolved securing items. |

### State Logic Breakdown

```text
SESSION_SECURED =
  ENTRY_ENABLE == OFF
  AND NO_UNINTENDED_POSITION
  AND NO_EXPOSURE_INCREASING_ORDER
  AND BROKER_INTERNAL_STATE_MATCH
  AND FINAL_ACCOUNT_SNAPSHOT_SAVED
  AND TRADE_LOG_COMPLETE
  AND EMERGENCY_LOG_COMPLETE
  AND SESSION_COUNTERS_PERSISTED
  AND ACTIVE_CONNECTIONS_CLOSED

IF SESSION_SECURED == TRUE
THEN finalize score and debrief
ELSE keep the session open with a list of unresolved securing steps.
```

---

# 3. Emergency Checklists

## 3.1 Engine Failure Equivalent — Flash Crash / Black Swan Event

| Trigger | System State | Required Player Action | Fail State |
| --- | --- | --- | --- |
| `FLASH_001` — IF `abs(Return_60s) >= 5 x ATR_1m_14` OR exchange halt occurs OR spread `>= 5 x` baseline with depth `<= 20%` baseline | `FLASH_CRASH_DETECTED`; market-speed gauge red; new-risk gate locked | Set trading master to `OFF` for new entries; keep exits allowed; acknowledge emergency within `3 s`. | Fail if player opens or enlarges a position after trigger. Apply `CRITICAL` process failure. |
| `FLASH_002` — Emergency active | `ENTRY_ORDERS_AT_RISK` | Cancel all unfilled entries and scale-in orders. Preserve protective stops and risk-reducing exits. | Fail if a cancel removes the only protective stop or leaves an order that can increase exposure. |
| `FLASH_003` — Open positions exist | `PROTECTION_CHECK` | Verify every open quantity has a broker-side protective order. IF protection is absent and connection is healthy THEN place emergency protection. | Fail if any position remains unprotected while an executable risk-reduction path exists. |
| `FLASH_004` — Open risk, correlation, or margin exceeds emergency profile | `PORTFOLIO_SURVIVAL_REVIEW` | Recalculate symbol risk, correlated-cluster risk, leverage, and margin reserve. Reduce exposure according to the pre-approved emergency policy; hedging is allowed only when explicitly authorized and order state is known. | Fail if exposure is increased, an improvised hedge creates additional unknown risk, or margin remains below the emergency floor while reduction is available. |
| `FLASH_005` — Spread and depth abnormal | `LIQUIDITY_FAILURE` | IF depth supports controlled exit and spread is within emergency cap THEN use a marketable limit; ELSE reduce in staged limits or wait through a venue halt while no new risk is allowed. | Fail if player sends an unrestricted order that exceeds the configured emergency-slippage ceiling without necessity. |
| `FLASH_006` — Venue halted | `HALTED_UNKNOWN_EXIT_TIME` | Cancel non-protective orders, retain valid protection where the venue permits, monitor reopen notices, and prepare reopen-auction risk plan. | Fail if the player treats the position as flat or restored before broker reconciliation. |
| `FLASH_007` — Equity loss reaches daily limit during crash | `DRAWDOWN_BREACH` overrides flash-crash state | Immediately execute the max-drawdown checklist; the session remains locked even if the market normalizes. | Fail if trading resumes because price recovers after the breach. |
| `FLASH_008` — Market normalizes | `RECOVERY_PENDING` | Require spread `<= 2 x` baseline, depth `>= 60%` baseline, no halt, stable data for `300 s`, and full position/order reconciliation. | Fail if new entries resume before all recovery conditions pass. |

## 3.2 Total Electrical Failure Equivalent — API or Network Disconnection

| Trigger | System State | Required Player Action | Fail State |
| --- | --- | --- | --- |
| `API_001` — IF WebSocket heartbeat missing `> 3 s`, three consecutive requests fail, or order acknowledgement exceeds `3 s` | `API_DISCONNECTED`; connectivity power lost | Freeze all new orders and amendments. Mark unacknowledged order state `UNKNOWN`. | Fail if the player sends new intent before the previous order state is known. |
| `API_002` — An order state is unknown | `DUPLICATE_RISK` | Retain the same idempotency key for status recovery. Query order state through a read path; do not create a replacement intent. | Fail if a second order with a new key is sent for the same trade intent. |
| `API_003` — Open positions exist during outage | `REMOTE_RISK_ONLY` | Rely on already accepted server-side stops and targets. IF protection was local-only THEN raise `CRITICAL` and use an authenticated fallback channel only after state reconciliation. | Fail if local UI assumes protection exists without broker evidence. |
| `API_004` — Primary network unavailable | `FAILOVER_READ_ONLY` | Switch to approved backup network or market-data route for observation. Keep execution disabled until broker state is confirmed. | Fail if backup data is used to submit orders through an unverified execution state. |
| `API_005` — Outage persists or venue status is uncertain | `INCIDENT_STATUS_REVIEW` | Check the approved broker, exchange, and communications status channels. Select the configured outage policy: `HOLD_PROTECTED`, `REDUCE_WHEN_CONFIRMED`, or `EXIT_WHEN_CONFIRMED`. | Fail if the player improvises a replacement order, hedge, or alternate route before broker state is known. |
| `API_006` — Connection returns | `RECOVERING` | Authenticate, fetch account, positions, open orders, recent fills, and order history from the outage window. | Fail if trading master is re-armed before all five data sets reconcile. |
| `API_007` — Reconciliation finds unexpected fill or position | `POSITION_STATE_UNKNOWN` | Protect or reduce the actual broker position first; then correct internal state and journal the incident. | Fail if the unexpected position is ignored or hidden by resetting local state. |
| `API_008` — Recovery complete | `CONNECTED_LOCKED` | Require stable heartbeat for `60 s`, zero unknown orders, exact position match, and no active drawdown breach before re-arming. | Fail if any unknown state remains. |

## 3.3 Cabin Depressurization Equivalent — Maximum Daily Drawdown Breach

| Trigger | System State | Required Player Action | Fail State |
| --- | --- | --- | --- |
| `DD_001` — IF `Daily_Loss_Limit_Breached == TRUE` OR `Total_Drawdown_Limit_Breached == TRUE` under the selected policy method | `MAX_DRAWDOWN_BREACHED`; altimeter below floor | Force trading master `OFF`; trigger audible and visual emergency alert immediately. | Fail if the player dismisses the alert and keeps entry controls enabled. |
| `DD_002` — Drawdown breach active | `KILL_SWITCH_ACTIVE` | Cancel every unfilled order that can increase exposure. Keep cancel, reduce, and exit actions enabled. | Fail if a new entry or scale-in remains executable. |
| `DD_003` — Open intraday positions exist | `EMERGENCY_RISK_REDUCTION` | Reduce or flatten positions using the emergency execution policy. IF venue is halted THEN queue no new risk and monitor reopening. | Fail if exposure is increased, stop is widened, or the daily baseline is reset. |
| `DD_004` — Automated strategies running | `AUTOMATION_INHIBITED` | Set every strategy to `OFF`; revoke order-launch permission for the rest of the session. | Fail if any strategy can submit a new entry after the breach. |
| `DD_005` — API outage also active | `LOCKED_UNKNOWN` | Maintain the kill switch, preserve server-side protection, and complete API recovery before determining final exposure. | Fail if session is marked safe while broker state is unknown. |
| `DD_006` — Positions flat or controlled | `SESSION_TERMINATED_FOR_RISK` | Start mandatory incident review; record trigger equity, open risk, player actions, and final state. | Fail if the session is closed without an incident record. |
| `DD_007` — Player requests reset | `RESET_PROHIBITED` | Keep the session locked until the next configured trading day and required review completion. | Fail if same-day manual reset re-enables trading. |
| `DD_008` — Risk-control review required | `REVIEW_LOCKED` | Start the configured cooldown and require incident review, coaching approval, or supervisor sign-off when the policy profile demands it. | Fail if the account is re-armed before the cooldown and required review state are complete. |

## Emergency State Logic

```text
IF MAX_DAILY_DRAWDOWN_BREACH == TRUE
THEN force KILL_SWITCH_ACTIVE and prevent same-session reset
ELSE IF any broker position or order state is UNKNOWN
THEN force API_DISCONNECTED or RECOVERING and block all new risk
ELSE IF FLASH_CRASH_DETECTED == TRUE
THEN freeze entries and execute market-emergency protection logic
ELSE run normal phase logic.
```

### Emergency Recovery Conditions

| Emergency | Recovery Conditions | Re-entry Policy |
| --- | --- | --- |
| Flash crash / black swan | No halt; data valid; spread `<= 2 x` baseline; depth `>= 60%` baseline; stable for `300 s`; orders and positions reconciled | Re-entry allowed only if daily drawdown was not breached and the scenario explicitly permits recovery trading. |
| API or network outage | Authenticated connection stable `60 s`; zero unknown orders; exact position match; recent fills loaded; server-side protection confirmed | Return first to `CONNECTED_LOCKED`; player must re-arm manually after checklist completion. |
| Maximum daily drawdown | Positions controlled, incident recorded, session ended, and next configured trading day reached | No same-session re-entry. Reset requires the next-session pre-market checklist. |

---

# 4. Gameplay Validation Mechanics

| Rule Name | Conditions | Game Response |
| --- | --- | --- |
| Simulation Isolation Gate | `IF Trading_Mode != SIMULATION` | Keep trading master `OFF`; display `LIVE CIRCUIT ISOLATED`. |
| Pre-Market Completion Gate | `IF PRE_MARKET_READY == FALSE` | Prevent order launch; display the unsatisfied step IDs. |
| No-Trade Success Rule | `IF any mandatory market or risk gate fails AND player does not launch a trade` | Award full safety credit for standing down; do not require a trade for mission completion. |
| Market Status Gate | `IF Market_Status not in {OPEN, SUPPORTED_AUCTION}` | Block new orders; allow cancel and risk-reducing actions. |
| Clock Integrity Gate | `IF Clock_Drift > 250 ms` | Disable time-sensitive signals and event-window validation until synchronized. |
| Quote Freshness Gate | `IF Quote_Age > 2 s OR timestamps are non-monotonic` | Set `DATA_STALE`; block launches and nonessential amendments. |
| Primary / Backup Feed Divergence | `IF abs(Primary_Mid - Backup_Mid) > configured tolerance for 3 updates` | Set `DATA_CONFLICT`; require feed selection or observation-only mode. |
| Economic Blackout Gate | `IF Now inside T-15 min to T+5 min of an affected high-impact event` | Block new entries; display `EVENT AIRSPACE CLOSED`. |
| Signal Freshness Gate | `IF Signal_Age > 1 strategy bar OR signal withdrawn` | Invalidate the ticket and require a new setup. |
| Plan Alignment Gate | `IF Direction is not permitted by approved long or short scenario` | Block launch unless a preconfigured exception profile exists. |
| Chase Distance Gate | `IF abs(Current_Price - Planned_Entry) > 0.25R` | Cancel the setup; display `RUNWAY OVERRUN — ENTRY MISSED`. |
| Protective Stop Required | `IF Stop_Price is null` | Prevent launch; no trade may be opened without defined invalidation. |
| Stop Direction Gate | `IF Long AND Stop >= Entry OR Short AND Stop <= Entry` | Reject ticket as invalid. |
| Minimum Stop Distance | `IF Stop_Distance < max(3 ticks, 0.25 ATR)` | Block or require strategy-specific override configured before the session. |
| Risk-to-Reward / Expectancy Safety Gate | `IF Net_Risk_Reward < Effective_Min_RR AND Approved_Expectancy_Gate == FALSE` | Prevent launch; display `UNSAFE TRIM SETTING`. |
| Per-Trade Risk Gate | `IF Position_Risk > 0.005 x Current_Equity` | Reduce quantity automatically in guided mode; otherwise block. |
| Sizing Consistency Rule | `IF Manual_Quantity > Calculated_Max_Quantity` | Reject quantity; show maximum valid lot size. |
| Aggregate Open-Risk Gate | `IF Existing_Risk + Pending_Risk + Proposed_Risk > 0.015 x Equity` | Block new risk until existing exposure is reduced. |
| Drawdown Gate | `IF Daily_Loss_Limit_Breached OR Total_Drawdown_Limit_Breached` | Activate kill switch and max-drawdown emergency. |
| Gross Leverage Gate | `IF Projected_Gross_Leverage > 2.00` | Block launch or reduce quantity. |
| Margin Fuel Reserve Gate | `IF Projected_Margin_Reserve < 30% of Equity` | Block launch; display `INSUFFICIENT FUEL RESERVE`. |
| Margin Stall Warning | `IF Margin_Reserve < 35%` | Show amber warning; prohibit scale-ins. At `<30%`, require reduction. |
| Single-Instrument Concentration Gate | `IF Projected_Instrument_Notional > 25% of Equity` | Block or resize unless a stricter approved profile already applies. |
| Correlation Cluster Gate | `IF Projected_Cluster_Notional > 40% of Equity OR cluster risk exceeds policy` | Treat the cluster as one trade and block excess exposure. |
| Spread Gate | `IF Current_Spread > 2.0 x Median_Spread OR exceeds hard instrument limit` | Block launch; allow passive observation or cancellation. |
| Depth Gate | `IF Executable_Depth < Proposed_Quantity` | Reduce size, use passive execution, or block launch. |
| Expected Slippage Gate | `IF Expected_Slippage > 0.10R` | Block aggressive execution and reduce size or wait. |
| Order-Type Compatibility Rule | `IF Order_Type unsupported OR can exceed configured slippage without protection` | Reject ticket and list permitted order types. |
| Tick and Lot Validation | `IF price not aligned to tick size OR quantity not aligned to lot step` | Normalize downward where safe; otherwise block. |
| Idempotent Submit Rule | `IF same trade intent already has status in {SENT, ACKNOWLEDGED, PARTIAL, FILLED, UNKNOWN}` | Do not create another order; query existing state. |
| Acknowledgement Timeout Rule | `IF no broker acknowledgement within 3 s` | Mark order `UNKNOWN`; invoke API-outage emergency. |
| Partial-Fill Protection Rule | `IF Filled_Quantity > Protected_Quantity` | Immediately protect the difference or exit it; apply critical warning. |
| Bracket Integrity Rule | `IF Stop_Quantity or Target_Quantity exceeds open quantity` | Reject amendment and reconcile to prevent accidental reverse exposure. |
| Fill Slippage Risk Recheck | `IF actual fill causes risk > per-trade cap OR the effective reward/expectancy gate fails` | Cancel remainder; reduce or exit excess risk according to policy. |
| Stop Removal Interlock | `IF open position exists AND protective stop is canceled without replacement accepted` | Block action or require immediate emergency replacement. |
| Stop-Widening Interlock | `IF proposed stop increases worst-case loss` | Reject change; record critical risk-discipline violation. |
| Break-Even Trim Gate | `IF Open_Profit < 1.0R OR configured trigger not met` | Reject break-even adjustment. |
| Scale-In Gate | `IF scale-in not in plan OR post-scale risk gates fail` | Block additional quantity. |
| Scale-Out Integrity Rule | `IF residual protective quantity != residual position quantity` | Repair protection before accepting scale-out completion. |
| Time-Stop Rule | `IF Position_Age >= Strategy_Max_Hold AND no approved extension` | Initiate exit and mark time-stop trigger. |
| Session-Close Gate | `IF intraday position or exposure-increasing order remains after cutoff` | Initiate controlled exit and prevent session closure. |
| Overnight Authorization Gate | `IF position remains overnight AND approval, stop, gap allowance, or next-session plan is missing` | Require reduction or exit. |
| Loss Cooldown Rule | `IF Consecutive_Losses >= 2` | Lock new launches for `15 min` and require a setup review. |
| Trade-Rate Redline | `IF Launches_Today >= 10 OR order-change rate exceeds profile` | Block additional launches or amendments; show tachometer redline. |
| Automation Subordination Rule | `IF automation requests an action that fails any human risk gate` | Reject automation request; risk engine has final authority. |
| Emergency Priority Rule | `IF Drawdown_Breach active` | Drawdown kill switch overrides flash-crash recovery and normal session logic. |
| Unknown-State Rule | `IF any position or order state == UNKNOWN` | Block all new risk until broker reconciliation passes. |
| Recovery Stability Gate | `IF reconnect stable time < 60 s OR market-normal time < 300 s after flash crash` | Keep master locked. |
| Journal Completeness Gate | `IF required trade fields or emergency records are missing` | Mark session incomplete and withhold final mission score. |
| Audit Integrity Rule | `IF player attempts to delete, rewrite, or reset immutable session events` | Reject change; apply critical integrity failure. |
| Process-First Scoring Rule | `Final_Score = Process_Subscore + Outcome_Modifier` using the scoring model below | Limit the reward from P&L; a profitable unsafe trade cannot score highly. |
| Critical-Breach Score Cap | `IF any critical safety breach occurs` | Cap total session score at `49/100` regardless of profit. |
| Mission Pass Rule | `IF Session_Score >= 70 AND no critical breach AND SESSION_STATE == SECURED` | Mark mission `PASS`; `>=90` is `DISTINCTION`. |
| Instrument Profile Eligibility Gate | `IF Instrument_Profile missing, incompatible, expired, or eligibility not in permitted states` | Block staging and launch; show the exact missing or conflicting profile rule. |
| Scenario/Profile Compatibility Gate | `IF scenario references unavailable or mismatched market, policy, valuation, latency, stress, or scoring profile versions` | Prevent official scenario start; permit only a clearly labeled non-authoritative diagnostic mode. |
| Recovery Lock Gate | `IF Session_State in {RECOVERY_LOCKED, INTEGRITY_FAILURE}` | Block new exposure; permit only discovery, reconciliation, protection, reduction, and closure where available. |
| Ledger Integrity Gate | `IF ledger does not balance OR equity cannot be reproduced from authoritative events` | Activate account reconciliation; withhold session finalization and official score. |
| Replay Integrity Gate | `IF future data is accessed, authoritative state is rolled back, or replay identity/hash fails` | Mark official run `INVALID`; preserve the event for debrief. |
| Stress-Loss Gate | `IF Current_Drawdown + Projected_Portfolio_Stress_Loss >= Effective_Hard_Drawdown_Limit` | Resize or block proposed risk; activate emergency reduction when existing stress breaches survival policy. |
| Expectancy Eligibility Gate | `IF expectancy exception profile is not APPROVED, current, and exactly matched` | Set `Approved_Expectancy_Gate = FALSE` and apply the standard risk-to-reward rule. |
| Multi-Currency Valuation Gate | `IF required conversion rate is missing or stale` | Mark affected valuation `UNKNOWN`; block exposure whose risk, margin, or drawdown cannot be converted. |
| Alert Resolution Integrity Rule | `IF alert is acknowledged while hazard remains active` | Silence only permitted repeat audio; keep visual warning latched and permissions restricted. |


## Mode-Specific Gate Behavior

| Gate Class | Guided | Standard | Expert |
| --- | --- | --- | --- |
| `SYSTEM_INTEGRITY` | Hard block | Hard block | Hard block |
| `ACCOUNT_POLICY_HARD_LIMIT` | Hard block | Hard block | Hard block |
| `STRATEGY_QUALITY_GATE` | Hard block with explanation | Warning or confirmed override when profile permits | No hint; override follows scenario consequences |
| `CHECKLIST_SEQUENCE` | Enforced | Bounded flexibility | Logged without prompts unless the phase gate fails |
| `EMERGENCY_LOCKOUT` | Enforced | Enforced | Enforced |
| `DOCUMENTATION_REQUIREMENT` | Required before final score | Missing items reduce score | Missing items remain visible only in debrief |

## Player Feedback Contract

Every blocked, warned, failed, or emergency interaction shall produce a consistent feedback object:

```text
PlayerFeedback
├── severity
├── headline
├── failed_step_id
├── rule_name
├── reason
├── current_value
├── required_value_or_state
├── permitted_corrective_actions
├── automatic_system_response
├── score_effect
└── replay_reference
```

Example:

```text
HEADLINE: TAKEOFF DENIED
STEP: ENTRY_009
RULE: Risk-to-Reward / Expectancy Safety Gate
CURRENT: Net_Risk_Reward = 0.82
REQUIRED: Effective_Min_RR = 1.50
CORRECTIVE ACTIONS:
- Improve entry only while the setup remains valid.
- Use the technically valid stop.
- Adjust the target according to the strategy.
- Stand down.
PROHIBITED:
- Increase size to manufacture a better ratio.
```

## Scoring Model

```text
Process_Subscore = 0..95
Outcome_Modifier = -5..+5
Final_Score = clamp(Process_Subscore + Outcome_Modifier, 0, 100)
```

| Score Dimension | Maximum Points | Primary Evidence |
| --- | ---: | --- |
| Preparation | 10 | Pre-market completeness, system checks, plan quality |
| Risk Management | 25 | Sizing, stops, aggregate risk, leverage, drawdown response |
| Execution Quality | 15 | Order selection, slippage, partial-fill handling, reconciliation |
| Trade Plan Adherence | 15 | Entry, management, and exit versus approved plan |
| Portfolio Management | 10 | Correlation, concentration, margin, open-risk control |
| Emergency Readiness / Response | 10 | Kill-switch test and actual incident response when triggered |
| Discipline | 5 | No revenge trading, unsafe stop widening, or unplanned doubling |
| Post-Market Review | 5 | Journal, evidence, lessons, and incident closure |
| Outcome Modifier | `-5` to `+5` | Risk-adjusted result; cannot erase a process or safety failure |

- A no-trade session receives an outcome modifier of `0`.
- A controlled loss that followed the plan may still achieve a high final score.
- A profitable trade with a critical safety breach remains subject to the existing score cap.

## Validation Policies

| Policy | Behavior |
| --- | --- |
| `STRICT` | Actions must occur in order. Used for launch submission, outage recovery, and emergency shutdown of new risk. |
| `BOUNDED_FLEX` | Items may occur in any order inside a phase, but every required state must pass before the phase gate. |
| `CONTINUOUS` | The state is monitored continuously and may regress. Used for data freshness, stop protection, margin, daily drawdown, and reconciliation. |

## Incorrect-Action Consequence Model

```text
INCORRECT_ACTION
  -> FINANCIAL_SYSTEM_CONSEQUENCE
  -> CHECKLIST_STATE_CONSEQUENCE
  -> SCORE_CONSEQUENCE
  -> DEBRIEF_EVENT
```

| Incorrect Action | System Consequence | Checklist / Score Consequence |
| --- | --- | --- |
| Submit without a stop | Unbounded planned loss | Submit blocked; `CRITICAL` launch failure |
| Widen a stop after entry | Worst-case loss increases | Amendment rejected; critical risk-discipline penalty |
| Retry an unknown order with a new key | Duplicate position risk | API emergency escalates; session score capped |
| Continue after daily drawdown breach | Policy and capital-preservation failure | Kill switch forced; mission cannot pass |
| Open during stale data or blackout | Decision based on invalid or event-distorted inputs | Order blocked; major procedure penalty |
| Correctly stand down when gates fail | No financial exposure created | Full safety credit; no-trade mission may pass |

## Minimum Telemetry Contract

Every action and validation result shall record enough information to reconstruct market visibility, player intent, authoritative financial state, alerts, and score behavior:

```yaml
event_id: uuid
source_event_id: string | null
source_sequence: integer | null
simulation_time: timestamp
market_event_time: timestamp | null
client_receive_time: timestamp | null
player_action_time: timestamp | null
venue_accept_time: timestamp | null
fill_time: timestamp | null
processing_time: timestamp
player_id: string
session_id: string
scenario_id: string
scenario_version: string
replay_id: string
branch_id: string
policy_profile_id: string
policy_profile_version: string
instrument_profile_id: string | null
instrument_profile_version: string | null
valuation_policy_id: string | null
latency_profile_id: string | null
stress_profile_id: string | null
expectancy_profile_id: string | null
account_id: string
strategy_id: string | null
strategy_version: string | null
instrument: string | null
order_id: string | null
fill_id: string | null
trade_id: string | null
ledger_entry_ids: list[string]
alert_id: string | null
session_state: string
trade_state: string | null
order_state: string | null
position_state: string | null
risk_state: string
reconciliation_state: string
step_id: string | null
panel_id: string | null
action_type: string
old_value: any
new_value: any
market_data_timestamp: timestamp | null
market_snapshot_ref: string | null
portfolio_snapshot_ref: string | null
account_state_hash: string
order_state_hash: string
position_state_hash: string
ledger_state_hash: string
replay_identity_hash: string
validation_result: PASS | FAIL | WARNING | BLOCKED | REGRESSED
severity: INFO | ADVISORY | CAUTION | WARNING | CRITICAL
rule_name: string | null
warning_codes: list[string]
financial_consequence: string | null
score_dimension: string | null
score_delta: integer
replay_reference: string
integrity_hash: string
```


# 5. Market and Instrument Baseline Specification

## 5.1 Baseline Rule

The simulator shall never apply one generic execution, margin, session, or valuation model to every financial product. Each playable instrument shall resolve to one explicit, versioned venue profile before market data, risk sizing, order staging, accounting, or scoring begins.

```text
SCENARIO
  -> MARKET_BASELINE
  -> VENUE
  -> INSTRUMENT_VENUE_PROFILE
  -> ACCOUNT_POLICY
  -> STRATEGY_PROFILE
  -> EFFECTIVE_RULES
```

```text
IF Instrument_Venue_Profile is missing, incomplete, expired, or incompatible with the scenario
THEN Instrument_Eligibility = INELIGIBLE
AND block data normalization, position sizing, order staging, and trade launch
ELSE bind the profile version to the session and every dependent event.
```

## 5.2 Instrument and Venue Profile

```text
InstrumentVenueProfile
├── profile_id
├── version
├── effective_from
├── effective_to
├── asset_class
├── venue_id
├── venue_product_id
├── display_symbol
├── base_currency
├── quote_currency
├── settlement_currency
├── account_position_mode
│   ├── NETTING
│   └── HEDGING
├── price_rules
│   ├── tick_size
│   ├── price_precision
│   ├── minimum_price
│   ├── maximum_price
│   └── price_band_rule
├── quantity_rules
│   ├── quantity_unit
│   ├── minimum_quantity
│   ├── maximum_quantity
│   ├── quantity_step
│   └── contract_multiplier
├── value_rules
│   ├── point_value
│   ├── pip_value_method
│   ├── notional_value_method
│   └── pnl_currency
├── session_rules
│   ├── calendar_id
│   ├── exchange_timezone
│   ├── daylight_saving_rule
│   ├── regular_session
│   ├── supported_auctions
│   ├── holiday_schedule
│   └── early_close_schedule
├── order_rules
│   ├── supported_order_types
│   ├── supported_time_in_force
│   ├── stop_trigger_method
│   ├── cancel_replace_semantics
│   ├── self_trade_rule
│   └── minimum_stop_distance
├── margin_rules
│   ├── initial_margin_method
│   ├── maintenance_margin_method
│   ├── liquidation_method
│   └── intraday_margin_window
├── carrying_cost_rules
│   ├── commission_schedule_id
│   ├── exchange_fee_schedule_id
│   ├── financing_rule
│   ├── funding_rule
│   └── borrow_cost_rule
├── lifecycle_rules
│   ├── expiry_timestamp
│   ├── first_notice_date
│   ├── last_trade_date
│   ├── settlement_rule
│   ├── roll_rule
│   └── corporate_action_rule
├── short_sale_rule
├── halt_and_reopen_rule
├── market_data_schema_id
└── eligibility_state
```

## 5.3 Supported Product Behaviors

| Asset-Class Profile | Required Product-Specific Behavior | Prohibited Simplification |
| --- | --- | --- |
| Cash equity | Shares, venue sessions, auctions, corporate actions, short availability, borrow fees, settlement, and tick regime | Treating a split, dividend, halt, or short restriction as an ordinary price move |
| Futures | Contract multiplier, tick value, expiry, roll, initial and maintenance margin, settlement, price limits, and first-notice constraints | Treating one contract as one currency unit or allowing an expired contract to trade normally |
| Spot FX or CFD | Lot or unit sizing, pip/point value, account conversion, rollover or financing, netting/hedging mode, and broker session rules | Assuming centralized exchange depth or a universal contract size |
| Crypto spot | Base/quote quantities, exchange-specific precision, 24/7 calendar, fees, outages, and custody-style balance constraints | Assuming continuous liquidity or ignoring exchange maintenance windows |
| Crypto perpetual | Contract definition, mark/index price, funding, maintenance margin, liquidation, and exchange risk rules | Using last trade as the only liquidation reference |
| Any unsupported class | Dedicated profile must exist before eligibility | Approximating options, structured products, or other instruments through an unrelated profile |

The simulator may support any subset of these profiles. A scenario shall not silently fall back to another asset-class model.

## 5.4 Instrument Eligibility States

```text
UNKNOWN
  -> ELIGIBLE
  -> RESTRICTED
  -> CLOSE_ONLY
  -> HALTED
  -> EXPIRED
  -> INELIGIBLE
```

| State | Entry Behavior | Risk-Reduction Behavior |
| --- | --- | --- |
| `ELIGIBLE` | Normal policy validation | Allowed |
| `RESTRICTED` | Only explicitly permitted order types, sizes, or sessions | Allowed |
| `CLOSE_ONLY` | New exposure prohibited | Cancel, reduce, or close allowed |
| `HALTED` | No venue execution until the reopen state permits it | Existing orders follow venue halt rules |
| `EXPIRED` | New and ordinary close orders prohibited; settlement or roll workflow applies | Only lifecycle actions permitted |
| `INELIGIBLE` | All order staging blocked | Existing erroneous exposure enters reconciliation or emergency handling |
| `UNKNOWN` | New exposure blocked | Risk state must be reconciled before action selection |

## 5.5 Session and Calendar Validation

```text
SESSION_TRADABLE =
  Instrument_Eligibility == ELIGIBLE
  AND Venue_Status in Permitted_Venue_Statuses
  AND Simulation_Time inside Permitted_Session_Window
  AND Instrument_Not_Expired
  AND Calendar_Version_Is_Current
```

- Internal time shall be UTC.
- Session boundaries shall be calculated from the venue's named timezone and daylight-saving rule.
- Holidays, early closes, maintenance windows, opening/closing auctions, halts, and reopen phases shall be explicit states.
- A session calendar change during a scenario shall arrive as an authoritative event and be logged with its source timestamp.
- The player-facing clock shall show both simulation time and the selected venue-local time.

## 5.6 Unit and Metadata Rules

| Requirement ID | Requirement | Pass Condition | Failure Response |
| --- | --- | --- | --- |
| `MKT_001` | Tick size is known | Every staged price is an exact valid tick | Normalize only when semantics and risk are unchanged; otherwise block |
| `MKT_002` | Quantity step is known | Quantity is an exact valid increment | Round down for risk-limited sizing; reject unsafe manual normalization |
| `MKT_003` | Contract value is known | Monetary risk and P&L can be reproduced | Mark risk engine invalid and block launch |
| `MKT_004` | Session calendar is known | Current venue state is deterministic | Set instrument `CLOSE_ONLY` or `INELIGIBLE` according to exposure state |
| `MKT_005` | Currency context is known | P&L and margin resolve to account currency | Block new exposure dependent on an unknown conversion |
| `MKT_006` | Lifecycle state is known | Expiry, settlement, roll, and corporate-action behavior are explicit | Activate lifecycle warning and prohibit unsupported actions |
| `MKT_007` | Order capabilities are known | Ticket exposes only supported order types and time-in-force values | Reject unsupported combinations before submission |
| `MKT_008` | Profile is immutable inside a scored session | Every event references the same profile version unless an authoritative change event occurs | Mark replay integrity failure if edited manually |

---

# 6. Formal Order, Position, and Ledger State Machines

## 6.1 Authoritative State Rule

Checklist status and UI intent shall never be treated as proof that a financial action occurred. Orders, fills, positions, cash, margin, and protection are valid only when represented by authoritative state events from the simulated broker or venue model.

```text
PLAYER_ACTION
  -> DURABLE_ORDER_INTENT
  -> BROKER_REQUEST
  -> BROKER_OR_VENUE_EVENT
  -> ORDER_STATE_TRANSITION
  -> FILL_AND_LEDGER_POSTING
  -> POSITION_STATE_TRANSITION
  -> RECONCILIATION
```

## 6.2 Order State Machine

```text
DRAFT
  -> STAGED
  -> SUBMIT_PENDING
  -> SENT
  -> ACKNOWLEDGED
  -> PARTIALLY_FILLED
  -> FILLED
```

Alternative branches:

```text
SUBMIT_PENDING or SENT -> UNKNOWN
SENT or ACKNOWLEDGED or PARTIALLY_FILLED -> CANCEL_PENDING -> CANCELED
ACKNOWLEDGED or PARTIALLY_FILLED -> REPLACE_PENDING -> ACKNOWLEDGED or UNKNOWN
SENT or ACKNOWLEDGED -> REJECTED
ACKNOWLEDGED or PARTIALLY_FILLED -> EXPIRED
ANY_NONTERMINAL_STATE -> UNKNOWN -> RECONCILED_TO_CONFIRMED_STATE
```

Terminal states are `FILLED`, `CANCELED`, `REJECTED`, and `EXPIRED`. `UNKNOWN` is never a terminal state.

## 6.3 Order Transition Table

| Current State | Event | Required Validation | Next State | Fail / Edge Behavior |
| --- | --- | --- | --- | --- |
| `DRAFT` | Player completes ticket | Instrument, side, quantity, price rules, stop, and plan fields valid | `STAGED` | Remain `DRAFT`; show failed fields |
| `STAGED` | Player authorizes release | All launch and policy gates pass | `SUBMIT_PENDING` | Stay `STAGED` or invalidate ticket |
| `SUBMIT_PENDING` | Intent durably stored | Unique idempotency key and immutable intent hash exist | `SENT` after request dispatch | If storage fails, do not send |
| `SENT` | Broker acknowledgement | Broker order ID and accepted terms returned | `ACKNOWLEDGED` | Timeout produces `UNKNOWN`, not `REJECTED` |
| `ACKNOWLEDGED` | Fill report with residual quantity | Fill sequence valid and quantity within remaining amount | `PARTIALLY_FILLED` | Invalid sequence triggers reconciliation lock |
| `ACKNOWLEDGED` or `PARTIALLY_FILLED` | Final fill | Total filled quantity equals accepted quantity or terminal filled amount | `FILLED` | Overfill triggers critical invariant failure |
| `ACKNOWLEDGED` or `PARTIALLY_FILLED` | Cancel request accepted for processing | Request references current broker order version | `CANCEL_PENDING` | Order remains executable while pending |
| `CANCEL_PENDING` | Fill arrives before cancel acknowledgement | Fill event is processed first | `PARTIALLY_FILLED` or `FILLED` | Never discard the fill because cancel was requested |
| `CANCEL_PENDING` | Cancel acknowledgement | Residual open quantity equals zero | `CANCELED` | If residual remains, state becomes `UNKNOWN` |
| `ACKNOWLEDGED` or `PARTIALLY_FILLED` | Replace request | Replacement remains within plan and risk limits | `REPLACE_PENDING` | Venue-specific cancel/replace semantics apply |
| Any nonterminal remote state | Connectivity or sequence uncertainty | Authoritative order state cannot be proven | `UNKNOWN` | New risk blocked; query and reconcile |
| Any state | Duplicate submit intent | Same idempotency key or intent hash exists | No new order | Return existing order reference |

## 6.4 Order-State Invariants

```text
0 <= Filled_Quantity <= Accepted_Quantity
Remaining_Quantity = Accepted_Quantity - Filled_Quantity - Canceled_Quantity
Filled_Quantity + Remaining_Quantity + Canceled_Quantity = Accepted_Quantity
```

```text
IF Order_State in {FILLED, CANCELED, REJECTED, EXPIRED}
THEN no ordinary transition to a nonterminal state is permitted.
```

A broker correction shall be represented by a new correction or reversal event; historical fill events shall not be overwritten.

## 6.5 Position State Machine

```text
FLAT
  -> OPENING
  -> OPEN
  -> REDUCING
  -> CLOSING
  -> FLAT
```

Additional states:

```text
OVERNIGHT_APPROVED
EMERGENCY_CONTROLLED
LIQUIDATION_PENDING
UNKNOWN
```

| State | Meaning | New Exposure | Required Player/System Behavior |
| --- | --- | --- | --- |
| `FLAT` | No confirmed net or hedged exposure | Allowed after normal gates | Continue setup scan |
| `OPENING` | Entry order has filled partially or completely but final protection/reconciliation is pending | Block additional unplanned risk | Confirm quantity, average price, and stop coverage |
| `OPEN` | Confirmed position with known ownership and protection state | Allowed only by plan and portfolio gates | Manage according to approved plan |
| `REDUCING` | Risk-reducing order is active | No increase through the same action | Recalculate residual protection after each fill |
| `CLOSING` | Full exit is active | No new exposure | Continue until quantity is zero or state becomes unknown |
| `OVERNIGHT_APPROVED` | Position intentionally retained across the session boundary | Only pre-approved changes | Persist gap allowance and next-session plan |
| `EMERGENCY_CONTROLLED` | Position remains open under an active emergency policy | Reduction and protective actions only | Follow emergency checklist |
| `LIQUIDATION_PENDING` | Venue or broker liquidation process has begun | Prohibited | Display estimated and confirmed liquidation events separately |
| `UNKNOWN` | Internal and authoritative exposure cannot be proven equal | Prohibited | Reconcile before any non-reducing action |

## 6.6 Protective-Order Coverage

```text
Required_Protected_Quantity = abs(Open_Position_Quantity)
Protection_Coverage = Confirmed_Protective_Quantity / Required_Protected_Quantity
```

```text
IF Open_Position_Quantity != 0
AND Protection_Coverage < 1.00
AND No_Approved_Unprotected_Window
THEN activate CRITICAL_UNPROTECTED_EXPOSURE
AND attempt policy-approved protection or reduction.
```

The system shall prevent protective orders from exceeding residual position quantity when that could create reverse exposure.

## 6.7 Ledger Event Model

Every economic event shall create immutable, balanced ledger postings.

```text
LedgerEntry
├── ledger_entry_id
├── event_id
├── account_id
├── event_type
├── event_timestamp
├── posting_timestamp
├── debit_account
├── credit_account
├── amount
├── currency
├── quantity
├── instrument_profile_id
├── order_id
├── fill_id
├── source_sequence
├── reversal_of_entry_id
└── integrity_hash
```

Permitted event types include:

```text
DEPOSIT
WITHDRAWAL
BUY_FILL
SELL_FILL
COMMISSION
EXCHANGE_FEE
SPREAD_COST
FINANCING
FUNDING_PAYMENT
BORROW_FEE
DIVIDEND_OR_DISTRIBUTION
FX_TRANSLATION
MARK_TO_MARKET
SETTLEMENT
CORPORATE_ACTION
LIQUIDATION
REVERSAL_OR_CORRECTION
```

## 6.8 Financial Invariants

| Invariant ID | Required Invariant | Failure State |
| --- | --- | --- |
| `INV_ORD_001` | Broker-confirmed filled quantity equals internally recorded filled quantity | `ORDER_STATE_UNKNOWN` |
| `INV_POS_001` | Position quantity equals confirmed buys minus confirmed sells under the profile's netting/hedging rule | `POSITION_STATE_UNKNOWN` |
| `INV_PROT_001` | Protective quantity equals required residual quantity unless an approved exception is active | `CRITICAL_UNPROTECTED_EXPOSURE` |
| `INV_LED_001` | Every ledger event balances debits and credits | `LEDGER_INTEGRITY_FAILURE` |
| `INV_EQ_001` | Recomputed equity equals stored equity within configured currency tolerance | `ACCOUNT_RECONCILIATION_REQUIRED` |
| `INV_MGN_001` | Used, available, and reserved margin reproduce the selected margin model | `MARGIN_STATE_UNKNOWN` |
| `INV_IDE_001` | One idempotency key maps to at most one economic order intent | `DUPLICATE_INTENT_FAILURE` |
| `INV_SEQ_001` | Per-source event sequences are monotonic and processed exactly once | `EVENT_SEQUENCE_FAILURE` |

```text
IF any critical invariant fails
THEN New_Exposure_Enable = OFF
AND Session_State = RECOVERY_LOCKED
AND allow only state discovery, cancel, protection, reduction, or closure actions.
```

## 6.9 Event Ordering and Concurrency

- Events from one authoritative source shall be applied in source-sequence order.
- Event time, receive time, and processing time shall be stored separately.
- A fill that precedes a cancel acknowledgement shall be posted even when the player requested cancellation first.
- Simultaneous fills across instruments shall update portfolio risk as one atomic risk-evaluation cycle before new player exposure is accepted.
- Repeated identical events shall be deduplicated by authoritative event ID, not by timestamp alone.
- A replace request shall be modeled as atomic only when the instrument profile explicitly guarantees atomic replacement.

---

# 7. Simulation Clock, Replay Integrity, and No-Lookahead Rules

## 7.1 Simulation Clock Contract

```text
SimulationClock
├── clock_id
├── simulation_timestamp_utc
├── source_market_timestamp_utc
├── venue_local_timestamp
├── display_timezone
├── replay_speed
├── paused
├── session_phase
├── event_sequence_number
├── scenario_seed
├── scored_session
├── branch_id
├── future_data_visibility
└── integrity_state
```

The simulation clock is the sole authority for what information may be visible or actionable at any moment.

## 7.2 Time Domains

| Time Field | Meaning |
| --- | --- |
| `market_event_time` | When the market or venue event occurred in the modeled world |
| `broker_receive_time` | When the simulated broker received the venue event or player request |
| `client_receive_time` | When the player's simulator received the update |
| `display_time` | When the update became visible in the cockpit |
| `player_action_time` | When the player committed an interaction |
| `venue_accept_time` | When an order became active at the venue |
| `fill_time` | When execution occurred |
| `execution_report_time` | When the fill or order update reached the player |
| `processing_time` | When the local state machine applied the event |

Latency simulation in Section 12 determines the difference among these times.

## 7.3 Replay Controls by Mode

| Session Type | Pause | Rewind | Restart / Branch | Score Status |
| --- | --- | --- | --- | --- |
| Guided practice | Permitted when scenario rules allow | Permitted | Creates a new practice branch | `PRACTICE` only |
| Standard assessment | Disabled while market phase is active | Prohibited | Resume from authoritative state only | Scored |
| Expert assessment | Prohibited during active session | Prohibited | Resume from authoritative state only | Scored |
| Challenge assessment | Controlled by scenario; normally prohibited | Prohibited | Resume from authoritative state only | Scored |
| Post-market replay | Permitted | Permitted | Non-authoritative analysis branch | Does not alter official score |

```text
IF Scored_Session == TRUE
AND player attempts rewind, future seek, checkpoint rollback, or data reveal
THEN Replay_Integrity_State = INVALID
AND invalidate the official mission score.
```

## 7.4 No-Lookahead Rules

The following information shall remain unavailable until its modeled availability timestamp:

- Future ticks, quotes, trades, order-book changes, and bars.
- The final high, low, close, volume, or indicator value of an incomplete bar.
- Economic-release values before the official release event.
- Revised economic values before their revision publication event.
- Future earnings, dividends, splits, notices, halts, reopening decisions, or margin changes unless already publicly known at the simulated time.
- Future broker acknowledgements, fills, cancellations, and liquidation results.
- Future scenario triggers and hidden-event parameters.

```text
IF Data_Availability_Timestamp > Simulation_Timestamp
THEN the data is inaccessible to UI, strategy, risk, scoring, alerts, and automation.
```

For a closed-bar strategy:

```text
IF Bar_Close_Timestamp > Simulation_Timestamp
THEN the bar is incomplete and cannot be used as a closed input.
```

## 7.5 Point-in-Time Economic and Reference Data

- Economic records shall preserve original release values and each later revision as separate versions.
- A replay shall expose only the version that was available at the simulation timestamp.
- Session calendars, index constituents, instrument metadata, and corporate-action knowledge shall use point-in-time versions when the mission depends on historical realism.
- A data source that cannot provide point-in-time validity shall be labeled `NON_POINT_IN_TIME`; scenarios using it cannot claim strict historical assessment integrity.

## 7.6 Replay Identity

```text
ReplayIdentity
├── replay_id
├── scenario_id
├── scenario_version
├── market_baseline_id
├── instrument_profile_versions
├── market_data_source_id
├── market_data_hash
├── point_in_time_dataset_version
├── scenario_seed
├── policy_profile_id
├── policy_profile_version
├── strategy_profile_versions
├── scoring_profile_version
├── simulator_rules_version
└── parent_branch_id
```

Two official runs with the same replay identity and the same player event sequence shall produce the same market, execution, ledger, state, and score outputs.

## 7.7 Replay Integrity States

```text
VALID
  -> TAINTED
  -> INVALID
```

| State | Trigger | Consequence |
| --- | --- | --- |
| `VALID` | Data hashes, versions, sequence, and time controls match specification | Official scoring permitted |
| `TAINTED` | Non-critical reference data is missing, a permitted practice aid was used, or a non-authoritative branch was created | Practice/debrief permitted; official comparability disabled |
| `INVALID` | Future data access, rollback of authoritative consequences, hash mismatch, event deletion, or non-deterministic divergence | Official score and leaderboard eligibility denied |

## 7.8 Determinism Validation

| Requirement ID | Validation |
| --- | --- |
| `CLK_001` | Same replay identity and player events produce identical ordered market events |
| `CLK_002` | Same fills produce identical ledger postings and account values |
| `CLK_003` | Randomized events use stored seeds and declared random streams |
| `CLK_004` | Pausing in permitted practice mode does not alter market-event ordering |
| `CLK_005` | No future record is visible through UI, logs, alerts, calculations, or automation |
| `CLK_006` | Post-market replay cannot mutate the official session record |

---

# 8. Accounting, Valuation, Units, and Numerical Precision

## 8.1 Accounting Definitions

```text
Account_Balance =
  Settled_Cash
  + Realized_PnL
  + Posted_Income
  - Posted_Costs
  + Other_Posted_Adjustments
```

```text
Account_Equity =
  Account_Balance
  + Unrealized_PnL
  + Accrued_Income
  - Accrued_Costs
  + Pending_Mark_To_Market_Adjustments
```

```text
Available_Margin =
  Account_Equity
  - Used_Margin
  - Reserved_Order_Margin
  - Policy_Reserve
```

The exact meaning of balance, equity, margin, settlement, and posted versus accrued amounts shall be selected by the active account and instrument profiles.

## 8.2 Realized and Unrealized P&L

For a linear long position:

```text
Gross_Realized_PnL =
  (Exit_Price - Entry_Price)
  x Closed_Quantity
  x Contract_Multiplier
```

For a linear short position:

```text
Gross_Realized_PnL =
  (Entry_Price - Exit_Price)
  x Closed_Quantity
  x Contract_Multiplier
```

```text
Net_Realized_PnL =
  Gross_Realized_PnL
  - Allocated_Entry_Costs
  - Exit_Costs
  - Financing_And_Carrying_Costs
```

Non-linear products require a dedicated valuation profile and shall not reuse the linear formula.

## 8.3 Valuation Policy

```text
ValuationPolicy
├── policy_id
├── version
├── normal_mark_method
├── drawdown_mark_method
├── margin_mark_method
├── liquidation_mark_method
├── stale_price_fallback
├── crossed_market_rule
├── halted_market_rule
├── fx_conversion_source
└── tolerance_profile
```

| Mark Method | Use | Rule |
| --- | --- | --- |
| `LIQUIDATION_SIDE` | Conservative account and risk view | Long positions marked to executable bid; shorts to executable ask |
| `MID` | Analytical display where permitted | Not used when spread is invalid or when policy requires liquidation-side valuation |
| `LAST` | Venue-specific reporting | Cannot be used when stale or non-representative under the active profile |
| `MARK` | Derivatives or venue-defined risk reference | Source and timestamp must be explicit |
| `SETTLEMENT` | End-of-session or contract settlement | Applied only at the profile-defined settlement event |

The cockpit shall display the mark method used for equity, drawdown, and margin when those methods differ.

## 8.4 Cost Model

The simulator shall support all costs applicable to the selected product:

```text
Trading_Cost =
  Commission
  + Exchange_Fee
  + Regulatory_Fee
  + Spread_Cost
  + Slippage_Cost
  + Financing_Cost
  + Funding_Payment
  + Borrow_Cost
  + Conversion_Cost
```

Costs shall be posted at the time defined by the relevant fee or carrying-cost profile. Estimated costs used before launch and confirmed costs used after execution shall be stored separately.

## 8.5 Precision and Rounding Rules

- Monetary calculations shall use decimal or fixed-point arithmetic, never binary floating-point as the authoritative ledger representation.
- Prices shall be validated against tick size before order staging.
- Quantities limited by risk, margin, or liquidity shall be rounded down to the valid quantity step.
- A manual price may be normalized only when normalization preserves the player's order semantics and does not increase risk; otherwise the ticket is rejected for correction.
- UI display rounding shall not alter internal values.
- Currency postings shall respect the account currency's minor-unit rule, while accrual calculations may retain additional internal precision.
- Percentages, basis points, ticks, points, pips, lots, shares, contracts, currency, and `R` values shall always carry explicit units.

## 8.6 Multi-Currency Accounting

```text
FXConversionRate
├── source_currency
├── target_currency
├── rate
├── rate_timestamp
├── source_id
├── quote_type
├── maximum_age
└── validity_state
```

```text
IF Required_FX_Conversion_Rate is missing or stale
THEN Cross_Currency_Valuation = UNKNOWN
AND block new exposure whose risk, margin, or drawdown cannot be converted safely.
```

Historical replay shall use the conversion rate that was available at the relevant simulation timestamp.

## 8.7 Reconciliation Tolerances

| Value | Default Tolerance Rule | Profile Override |
| --- | --- | --- |
| Quantity | Exact after valid quantity-step normalization | Venue lot-allocation rules may define sub-account allocation tolerance |
| Price | At most one-half valid tick for display comparison; authoritative fills must match exact reported price | Venue correction events override |
| Cash / equity | One account-currency minor unit or stricter | Account profile may specify a different documented tolerance |
| Margin | Reproduce broker model within configured calculation tolerance | Broker/sandbox profile specifies method and tolerance |
| FX conversion | Rate age and numerical tolerance from conversion profile | Scenario may impose stricter stress rules |

```text
IF abs(Internal_Equity - Authoritative_Equity) > Equity_Tolerance
THEN Account_State = RECONCILIATION_REQUIRED
AND New_Exposure_Enable = OFF.
```

## 8.8 Accounting Validation Requirements

| Requirement ID | Requirement |
| --- | --- |
| `ACC_001` | Every economic event produces balanced immutable postings |
| `ACC_002` | Every fill updates quantity, average cost or lots, realized/unrealized P&L, fees, margin, and risk exactly once |
| `ACC_003` | Partial closes allocate entry costs by the profile-defined method |
| `ACC_004` | Corporate actions and settlements use explicit lifecycle events rather than retroactive price rewriting |
| `ACC_005` | Estimated and confirmed costs are distinguishable in UI, telemetry, and debrief |
| `ACC_006` | Balance, equity, margin, buying power, and drawdown can be independently recomputed from stored events |
| `ACC_007` | Unknown valuation inputs force a visible unknown state rather than a fabricated value |

---

# 9. Scenario Definition Contract

## 9.1 Scenario Purpose

A scenario is a versioned, reproducible mission definition. It controls the market baseline, initial financial state, visible briefing, hidden but fair conditions, injected events, allowed assistance, pass/fail rules, and debrief reference.

## 9.2 Scenario Definition

```text
ScenarioDefinition
├── scenario_id
├── version
├── lifecycle_state
│   ├── DRAFT
│   ├── VALIDATED
│   ├── PUBLISHED
│   └── RETIRED
├── title
├── description
├── training_objectives
├── difficulty_profile
├── eligible_base_modes
├── market_baseline_id
├── instrument_profile_ids
├── account_policy_profile_id
├── strategy_profile_ids
├── scoring_profile_id
├── market_data_source_id
├── market_data_hash
├── point_in_time_dataset_version
├── scenario_seed
├── start_timestamp
├── end_timestamp
├── initial_account_state
├── initial_positions
├── initial_orders
├── initial_alerts
├── visible_briefing
├── hidden_conditions
├── injected_events
├── allowed_player_aids
├── pause_and_replay_rules
├── emergency_recovery_rules
├── pass_conditions
├── distinction_conditions
├── critical_fail_conditions
├── termination_conditions
└── debrief_reference
```

## 9.3 Injected Event Contract

```text
InjectedEvent
├── event_id
├── event_type
├── trigger_type
│   ├── ABSOLUTE_TIME
│   ├── RELATIVE_TIME
│   ├── PRICE_LEVEL
│   ├── MARKET_STATE
│   ├── PORTFOLIO_STATE
│   ├── PLAYER_ACTION
│   └── SEEDED_RANDOM
├── trigger_expression
├── start_timestamp
├── duration
├── parameters
├── affected_instruments
├── visibility
│   ├── BRIEFED
│   ├── DETECTABLE
│   └── HIDDEN_UNTIL_TRIGGERED
├── severity
├── interaction_priority
├── recovery_conditions
└── debrief_explanation
```

## 9.4 Scenario Trigger Rules

```text
IF Trigger_Expression == TRUE
AND Event_Not_Already_Triggered
THEN emit Injected_Event exactly once
ELSE continue evaluating according to the declared trigger cadence.
```

- Every random trigger shall use the stored scenario seed and named random stream.
- Hidden events shall remain discoverable through realistic market, venue, news, or system symptoms once they occur.
- A scenario shall not require the player to act on information that the cockpit could not have made available.
- Compound events shall define priority and interaction behavior explicitly.

## 9.5 Difficulty Dimensions

| Dimension | Lower Difficulty | Higher Difficulty |
| --- | --- | --- |
| Assistance | Guided highlights and explanations | Minimal hints and delayed diagnostic detail |
| Market speed | Normal volatility and spread | Faster moves, wider spread, or thinner depth |
| Portfolio complexity | One instrument and one position | Multiple correlated positions and pending orders |
| Failure complexity | One isolated event | Compound or cascading events |
| Execution complexity | Immediate acknowledgements and deep liquidity | Latency, queue uncertainty, partial fills, and cancel races |
| Information quality | Healthy redundant feeds | Stale, conflicting, or degraded data |
| Time pressure | Long response windows | Shorter but still humanly achievable windows |

Difficulty shall not be created solely by increasing nominal financial stakes.

## 9.6 Pass, Fail, and Termination Rules

```text
SCENARIO_PASS =
  all Mandatory_Process_Objectives satisfied
  AND all Required_End_States satisfied
  AND Final_Score >= Scenario_Pass_Score
  AND no Critical_Fail_Condition occurred
```

A scenario may pass with no trade when standing down is the correct risk decision.

Critical fail conditions may include:

- Continuing to create exposure after hard drawdown lockout.
- Deliberately bypassing immutable audit or replay integrity.
- Submitting a duplicate order while state is unknown.
- Leaving an uncontrolled position at scenario termination.
- Violating a scenario-defined safety interlock.

## 9.7 Abnormal Operations Catalogue

| Abnormal Condition | Trigger | Required Response | Fail State |
| --- | --- | --- | --- |
| Erroneous tick / price spike | Primary price deviates beyond tolerance and backup does not confirm | Mark feed conflict; freeze new risk; verify authoritative source | Trading from known bad data |
| Primary/backup feed disagreement | Divergence persists for configured updates | Select authoritative feed or observation-only mode | Silent blending of conflicting prices |
| Exchange halt | Venue state becomes `HALTED` | Freeze unsupported actions; show order status and reopen rules | Assuming stops or market orders will execute normally |
| Reopening auction | Venue enters auction phase | Apply auction order and pricing rules | Using continuous-market fill logic |
| Overnight gap | Reopen price crosses prior stop or target | Apply gap and queue model; recalculate realized loss | Filling at unavailable stop price |
| Margin increase | Initial or maintenance requirement rises | Recalculate reserve; reduce risk if required | Continuing with invalid margin figures |
| Repeated rejection | Rejection threshold exceeded | Diagnose order/profile mismatch; stop retries | Request-rate abuse or repeated unsafe submissions |
| Cancel followed by fill | Fill sequence precedes cancel confirmation | Post fill; update residual position and protection | Discarding fill because cancel was requested |
| Partial fill during outage | Fill arrives while client is disconnected | Recover authoritative quantity and protect residual | Duplicating or leaving unknown exposure |
| Position mismatch | Broker and internal quantity differ | Enter recovery lock and reconcile | New exposure before reconciliation |
| Clock drift | Drift exceeds threshold | Suspend time-sensitive logic and resynchronize | Using incorrect news or session windows |
| Corporate action / contract roll | Lifecycle event reaches effective timestamp | Transform position and orders according to profile | Treating adjusted quantities as unexplained P&L |
| Risk-engine process failure | Sizing or limits unavailable | Entries off; allow reduction and closure only | Trading with stale risk calculations |

## 9.8 Scenario Validation

A scenario may become `PUBLISHED` only when:

1. All referenced profile versions exist and are compatible.
2. Market data hashes and point-in-time properties are known.
3. Every injected event has deterministic trigger and recovery behavior.
4. Every required action is possible through an available cockpit control.
5. Pass and fail conditions are measurable.
6. The no-lookahead audit passes.
7. Compound emergencies have explicit priority.
8. A golden replay produces the expected event, financial, and scoring outputs.

---

# 10. Persistence, Crash Recovery, and Session Integrity

## 10.1 Persistence Principle

The simulator shall preserve financial reality before presentation convenience. A restart, crash, disconnection, or reload shall not erase fills, losses, open positions, emergency states, cooldowns, or scoring consequences.

## 10.2 Durable Session State

The following state shall be durable:

```text
DurableSessionState
├── session_identity
├── replay_identity
├── simulation_clock_state
├── scenario_state
├── policy_and_profile_versions
├── account_snapshot
├── ledger_entries
├── order_intents
├── order_events
├── fill_events
├── position_state
├── protective_order_state
├── margin_state
├── drawdown_references
├── risk_state
├── emergency_state
├── checklist_state
├── cooldowns_and_counters
├── scoring_events
├── player_actions
├── alert_state
└── integrity_hashes
```

## 10.3 Write-Before-Send Safety Rule

```text
IF Order_Intent is not durably persisted with a unique idempotency key
THEN do not send the order request.
```

```text
IF request dispatch may have occurred
AND final durable order state is unavailable
THEN Order_State = UNKNOWN
AND recovery reconciliation is mandatory.
```

The simulator shall not show a definitive rejection, cancellation, or no-fill state when authoritative evidence is absent.

## 10.4 Session Recovery State Machine

```text
RUNNING
  -> UNCLEAN_TERMINATION_DETECTED
  -> RECOVERY_LOCKED
  -> STATE_RESTORED
  -> AUTHORITATIVE_RECONCILIATION
  -> PROTECTION_VERIFIED
  -> CONNECTED_LOCKED
  -> MANUAL_REARM
  -> RUNNING
```

Alternative terminal branch:

```text
RECOVERY_LOCKED
  -> INTEGRITY_FAILURE
  -> SESSION_INVALID_OR_FORCED_CLOSE_WORKFLOW
```

## 10.5 Recovery Checklist

| Step ID | Recovery Action | Pass Condition | Failure Response |
| --- | --- | --- | --- |
| `RCV_001` | Detect unclean termination | Previous session lacks valid secured marker | Set entries `OFF`; create recovery incident |
| `RCV_002` | Load latest validated snapshot | Snapshot hash and version are valid | Fall back to earlier snapshot plus event replay; otherwise integrity failure |
| `RCV_003` | Replay immutable events | Event sequence applies exactly once without gap | Enter `EVENT_SEQUENCE_FAILURE` |
| `RCV_004` | Restore simulation clock and scenario | Timestamp, seed, triggers, and branch match replay identity | Invalidate scored session if identity cannot be restored |
| `RCV_005` | Restore order intents and idempotency keys | Every sent intent has durable identity | Mark unresolved intents `UNKNOWN` |
| `RCV_006` | Query authoritative broker state | Account, orders, fills, and positions returned | Remain recovery locked; use outage policy |
| `RCV_007` | Reconcile all orders and fills | Zero unknown order states | Keep new exposure disabled |
| `RCV_008` | Reconcile positions and ledger | Quantity and equity invariants pass | Keep account in recovery lock |
| `RCV_009` | Verify protective coverage | Every residual position is protected or under approved emergency policy | Protect, reduce, or close according to policy |
| `RCV_010` | Restore emergencies and cooldowns | Active restrictions match pre-crash state and current conditions | Apply the stricter reconstructed state |
| `RCV_011` | Enter connected-locked state | Data, broker, risk, and ledger are healthy for configured stability period | Continue recovery |
| `RCV_012` | Manual re-arm | Player completes recovery acknowledgement and any required checklist | Resume only the permitted session phase |

## 10.6 Save, Branch, and Score Integrity

- Practice mode may create a branch from a checkpoint; the branch shall receive a new ID and cannot overwrite the parent record.
- A scored session shall resume from the authoritative simulated-broker state, not from a player-selected earlier state.
- Terminating the application to avoid a fill, loss, warning, or emergency shall not remove the event.
- Post-market replay and debrief annotations may append commentary but may not mutate official actions or financial events.
- An official score shall reference one immutable replay identity and one ordered player-action stream.

## 10.7 Data Corruption and Integrity Failure

```text
IF Snapshot_Hash fails
OR Event_Log contains a gap or conflicting duplicate
OR Profile_Version cannot be resolved
OR Ledger cannot be balanced
THEN Session_State = INTEGRITY_FAILURE
AND New_Exposure_Enable = OFF.
```

For an open position, the system shall still expose any available cancel, protect, reduce, or close path while clearly labeling the uncertainty.

## 10.8 Persistence Requirements

| Requirement ID | Requirement |
| --- | --- |
| `PER_001` | Every order intent is durable before transmission |
| `PER_002` | Every authoritative event is persisted exactly once |
| `PER_003` | Snapshots are verifiable against the immutable event stream |
| `PER_004` | Recovery reproduces the same account, order, position, checklist, emergency, and score state |
| `PER_005` | Unknown states remain unknown until authoritative reconciliation resolves them |
| `PER_006` | Practice branches never alter official assessment records |
| `PER_007` | Session securing writes a durable terminal marker only after reconciliation and persistence pass |

---

# 11. QA Invariants and Verification Matrix

## 11.1 Verification Principle

Every normative checklist step, state transition, rule, formula, profile field, emergency action, and acceptance criterion shall be traceable to verification evidence. A behavior shall not be marked compliant merely because the UI displays the expected label.

## 11.2 Required Test Classes

| Test Class | Required Coverage |
| --- | --- |
| Positive | Valid input produces the specified state transition and financial result |
| Negative | Invalid input is blocked, warned, or penalized exactly as specified |
| Boundary | Values exactly at, just below, and just above each numerical threshold |
| Regression | A continuously valid state later becomes invalid and regresses the checklist/risk state |
| Recovery | Emergency or unknown state exits only when every recovery condition passes |
| Concurrency | Multiple fills, cancels, data updates, and emergencies occur in overlapping time windows |
| Persistence | Crash and restart preserve state without loss or duplication |
| Determinism | Identical replay identity and actions produce identical outputs |
| Integrity | Ledger, quantity, margin, risk, event-sequence, and audit invariants hold |
| Human factors | Alerts are visible, prioritized, acknowledgeable, and distinguish acknowledged from resolved |
| Accessibility | Critical information remains understandable without color or audio alone |
| Scenario fairness | Required decisions can be made from information available at the simulated time |

## 11.3 Traceability Record

```text
VerificationRecord
├── requirement_id
├── source_section
├── rule_or_step_id
├── test_case_id
├── scenario_id
├── input_profile_versions
├── initial_state_hash
├── event_sequence_hash
├── expected_state
├── expected_financial_values
├── actual_state
├── actual_financial_values
├── pass_fail
├── evidence_reference
└── reviewer
```

## 11.4 State-Transition Coverage

For every state machine:

1. Every permitted transition shall have at least one positive test.
2. Every prohibited transition shall have at least one negative test.
3. Every terminal state shall reject illegal reopening.
4. Every `UNKNOWN` state shall have recovery tests for each authoritative resolution.
5. Every emergency overlay shall be tested from every normal session phase it can interrupt.
6. Every priority conflict shall verify that the highest-priority state governs permissions.

## 11.5 Core Invariant Matrix

| Domain | Invariant | Verification Point |
| --- | --- | --- |
| Order | Filled, remaining, and canceled quantities reconcile | After every order event |
| Position | Position quantity matches authoritative fills | After every fill and correction |
| Protection | Stop/protective quantity covers residual position | After entry, partial fill, scale-out, replace, reconnect, and restart |
| Ledger | Debits equal credits and events post exactly once | After every economic event |
| Equity | Independent recomputation matches displayed and stored equity | Every account update and session close |
| Margin | Used and available margin match profile | Every order stage, fill, price move, and margin-rule change |
| Drawdown | Selected policy method reproduces state and threshold usage | Every equity update |
| Replay | Data, profile, seed, and event hashes match replay identity | Session start, checkpoint, recovery, and close |
| Alert | Acknowledgement does not clear an active hazard | Every latching alert test |
| Score | Same action/event stream produces same dimension scores | Finalization and replay |

## 11.6 Required Compound-Failure Tests

1. Partial fill followed immediately by network loss.
2. Drawdown breach while an exit order is unacknowledged.
3. Flash crash while broker connectivity is degraded.
4. Cancel request followed by final fill.
5. Stop rejection after a partial entry fill.
6. Margin breach and exchange halt at the same simulation time.
7. Application restart with one or more unknown orders.
8. Corporate action or contract roll while an overnight position is open.
9. Stale FX conversion rate in a multi-currency account.
10. Strategy automation attempts a new entry after kill-switch activation.
11. Primary and backup feeds disagree during a pending marketable order.
12. A margin increase occurs while a cancel/replace request is pending.

## 11.7 Financial Integrity Cycle

After every accepted fill, cancellation, fee, financing event, funding event, corporate action, settlement, correction, or liquidation:

```text
ASSERT order quantities reconcile
ASSERT position quantities reconcile
ASSERT ledger balances
ASSERT realized and unrealized PnL recalculate
ASSERT equity and balance recalculate
ASSERT margin and buying power recalculate
ASSERT open risk and stress risk recalculate
ASSERT residual protection is correct
ASSERT drawdown state recalculates
ASSERT telemetry event persists exactly once
```

## 11.8 Scenario Golden Runs

Each published scenario shall have at least:

- One nominal golden run.
- One correct no-trade or stand-down run when applicable.
- One critical-failure run.
- One emergency-recovery run.
- One restart/recovery run.
- One determinism rerun with identical inputs.
- One boundary run at each scenario-specific hard threshold.

## 11.9 Acceptance Evidence

A specification item is accepted only when evidence shows:

1. The actual state transition.
2. The actual financial calculation.
3. The emitted alert or feedback.
4. The audit and replay event.
5. The score impact where applicable.
6. The recovery behavior where applicable.

Screenshots alone are insufficient evidence for hidden financial or state-machine correctness.

---

# 12. Latency, Queue, and Fill Simulation

## 12.1 Execution-Time Model

```text
Total_Player_To_Fill_Delay =
  Player_Confirmation_Delay
  + Client_Processing_Latency
  + Outbound_Network_Latency
  + Broker_Processing_Latency
  + Venue_Gateway_Latency
  + Queue_And_Matching_Delay
```

```text
Total_Market_To_Display_Delay =
  Venue_Publication_Latency
  + Market_Data_Network_Latency
  + Feed_Handler_Latency
  + Client_Render_Latency
```

The player may act only on the market state that has reached the cockpit, while fills occur against the venue state at the order's effective arrival time.

## 12.2 Latency Profile

```text
LatencyProfile
├── profile_id
├── version
├── market_data_latency_model
├── outbound_order_latency_model
├── inbound_execution_latency_model
├── broker_processing_model
├── venue_gateway_model
├── jitter_model
├── packet_loss_model
├── timeout_thresholds
├── congestion_state_rules
├── random_seed_stream
└── clock_resolution
```

Latency may be fixed, sampled from a declared distribution, replayed from recorded observations, or changed by a scenario event. Random latency shall be seeded and reproducible.

## 12.3 Order Queue State

```text
QueueState
├── order_id
├── price_level
├── displayed_quantity_ahead
├── estimated_hidden_quantity_ahead
├── estimated_queue_position
├── volume_traded_at_level
├── cancellations_ahead_estimate
├── own_remaining_quantity
├── fill_probability_estimate
├── last_update_time
└── confidence_state
```

The UI may display an estimate, but the authoritative fill engine shall use the venue model and event sequence.

## 12.4 Fill Rules by Order Type

| Order Type | Activation | Fill Rule | Important Failure Mode |
| --- | --- | --- | --- |
| Market | Effective when accepted by venue/broker model | Walk available executable liquidity until quantity completes or market rule stops it | Slippage, partial fill, price band, halt, or insufficient liquidity |
| Limit | Active at valid price after acknowledgement | Fill only when eligible contra volume reaches the price and consumes modeled queue ahead | A touch does not guarantee fill unless venue profile says so |
| Marketable limit | Limit crosses available contra prices | Fill up to limit price using executable depth | Residual quantity may remain unfilled |
| Stop market | Trigger source reaches stop according to profile | Converts to market order after trigger and latency | Gap can produce a fill beyond stop price |
| Stop limit | Trigger source reaches stop | Converts to limit order with defined limit | May not fill during a fast move or gap |
| Trailing stop | Reference price updates according to profile | Trigger level moves only in risk-reducing direction | Stale reference or unsupported amendment invalidates it |
| OCO / bracket | Linked orders active according to broker profile | Fill of one leg cancels/reduces the other using modeled latency | Race can create temporary excess order quantity; reconciliation required |

## 12.5 Partial Fills

```text
IF Available_Executable_Quantity < Remaining_Order_Quantity
THEN generate PARTIAL_FILL for available quantity
AND leave or cancel residual quantity according to order and time-in-force rules.
```

Each partial fill shall independently update:

- Average entry or exit price.
- Realized or unrealized P&L.
- Fees.
- Position quantity.
- Margin.
- Open and stress risk.
- Protective-order requirement.
- Checklist and alert state.

## 12.6 Cancel and Replace Races

```text
IF Cancel_Request_Sent == TRUE
AND Cancel_Acknowledgement_Received == FALSE
THEN Original_Order_Remains_Executable.
```

```text
IF Fill_Event_Time < Cancel_Acknowledgement_Time
THEN apply the fill before the canceled state.
```

A replace request shall preserve the original order's executable risk until the profile's replacement semantics prove otherwise.

## 12.7 Slippage Model

Slippage shall derive from declared market and execution conditions, including:

- Spread at venue arrival.
- Available depth and queue position.
- Order size relative to depth and recent volume.
- Volatility and price velocity.
- Latency.
- Halt, auction, or gap state.
- Scenario-defined liquidity shock.

The simulator shall not add unexplained arbitrary adverse slippage to manipulate difficulty. Every fill shall be reproducible from the selected model, seed, and event stream.

## 12.8 Market Data versus Execution View

The cockpit shall distinguish:

```text
LAST_DISPLAYED_PRICE
CURRENT_SIMULATED_VENUE_PRICE
ORDER_EFFECTIVE_ARRIVAL_PRICE
ACTUAL_FILL_PRICE
EXECUTION_REPORT_DISPLAY_PRICE
```

This distinction shall be visible in the debrief to teach reaction, latency, and execution effects.

## 12.9 Latency and Fill Validation

| Requirement ID | Requirement |
| --- | --- |
| `EXE_001` | No order fills before venue acceptance time |
| `EXE_002` | No limit order fills at a price worse than its limit |
| `EXE_003` | A limit touch does not guarantee fill without queue eligibility |
| `EXE_004` | Stop price is a trigger, not a guaranteed execution price |
| `EXE_005` | Cancel-pending orders remain fillable until confirmation |
| `EXE_006` | Fill quantities never exceed available order quantity except through an explicit correction event |
| `EXE_007` | Every latency and slippage output is reproducible from the replay identity |
| `EXE_008` | UI and debrief show the full market-to-display and action-to-fill timeline |

---

# 13. Cockpit Human Factors and Alarm Management

## 13.1 Human-Factors Principle

The cockpit shall make hazards detectable, understandable, and actionable without hiding uncertainty or overwhelming the player with duplicate alarms. Acknowledging an alarm is not the same as resolving its cause.

## 13.2 Alert Severity and Priority

| Severity | Meaning | Default Presentation | Required Interaction |
| --- | --- | --- | --- |
| `INFO` | State change or normal confirmation | Log and unobtrusive visual message | None |
| `ADVISORY` | Condition worth monitoring | Visual indicator | Optional acknowledgement |
| `CAUTION` | Degraded state requiring timely review | Amber visual plus distinct tone where enabled | Acknowledge and diagnose |
| `WARNING` | Immediate risk of financial or state harm | Red visual, priority tone, and focused message | Immediate corrective action |
| `CRITICAL` | Hard policy, uncontrolled exposure, or integrity emergency | Latched master warning, repeated escalation, and emergency checklist | New exposure locked; action required |

Emergency priority follows the global priority table; higher-priority alarms shall not be hidden by lower-priority coaching messages.

## 13.3 Alert Lifecycle

```text
INACTIVE
  -> ACTIVE_UNACKNOWLEDGED
  -> ACTIVE_ACKNOWLEDGED
  -> CLEARED
```

Alternative state:

```text
ACTIVE_ACKNOWLEDGED -> ESCALATED
```

```text
IF Player_Acknowledges_Alert
AND Hazard_Condition == TRUE
THEN silence only the permitted repeat audio
AND keep the visual alert active and latched.
```

```text
IF Hazard_Condition == FALSE
AND all clear conditions pass
THEN Alert_State = CLEARED.
```

## 13.4 Alert Event Contract

```text
AlertEvent
├── alert_id
├── alert_code
├── severity
├── priority
├── root_cause_id
├── affected_account_id
├── affected_instrument
├── affected_order_ids
├── affected_position_ids
├── first_market_event_time
├── first_display_time
├── acknowledgement_time
├── resolution_time
├── current_value
├── threshold_or_required_state
├── permitted_actions
├── prohibited_actions
├── audio_state
├── visual_state
├── latch_state
└── replay_reference
```

## 13.5 Alarm Flood and Root-Cause Grouping

- Multiple symptoms from one failure shall be grouped under a root-cause alert while retaining drill-down detail.
- The system shall not emit repeated identical alerts faster than the configured escalation cadence.
- A new higher-severity symptom shall escalate the existing root-cause alert rather than create a competing low-context message.
- During an API outage, `DATA_STALE`, `ORDER_UNKNOWN`, and `POSITION_UNCONFIRMED` may appear as child conditions beneath the primary connectivity emergency.
- The player shall be able to identify exactly which account, instrument, order, or position is affected.

## 13.6 Display and Accessibility Rules

- Color shall never be the only carrier of warning meaning; use text, icon, shape, position, and, where enabled, sound.
- Audio shall not be the only carrier of critical information.
- Current value, required value, source timestamp, and uncertainty state shall be visible for safety-critical gauges.
- Invalid or stale gauges shall lose normal-range styling and show an explicit timestamp or age.
- Critical text shall remain readable at supported display scaling and cockpit layouts.
- Motion, flashing, and audio repetition shall have accessibility controls that preserve severity and urgency through alternative cues.

## 13.7 Interaction Safety

- Risk-reducing actions shall remain available while exposure-increasing controls are locked.
- Emergency flatten shall be guarded against accidental activation but shall not require a slow multi-screen confirmation.
- A normal exposure-increasing order shall require a final review of symbol, side, quantity, order type, stop, and calculated risk.
- Modal coaching shall not cover the controls needed to cancel, protect, reduce, or close risk.
- The master kill switch shall always show whether it affects entries only, automation, pending entries, or all eligible risk actions.
- Automation ownership shall be visible for every open position.

## 13.8 Response-Time Scoring

Emergency response timing shall begin when the relevant warning becomes visible or otherwise perceivable to the player, not when an unseen market event occurred.

```text
Player_Response_Time =
  First_Corrective_Action_Time - First_Actionable_Alert_Display_Time
```

A player shall not be penalized for latency or hidden information outside the modeled cockpit.

## 13.9 Human-Factors Acceptance Rules

| Requirement ID | Requirement |
| --- | --- |
| `HUM_001` | Acknowledged and resolved states are visually distinct |
| `HUM_002` | Critical alerts remain latched while the hazard persists |
| `HUM_003` | Root-cause grouping prevents duplicate alarm overload |
| `HUM_004` | Emergency controls remain reachable during warnings and overlays |
| `HUM_005` | All critical information is accessible without reliance on one sensory channel |
| `HUM_006` | Response-time scoring starts only when the player can perceive the condition |
| `HUM_007` | Mode-specific help changes explanation level, not the underlying financial state |

---

# 14. Training Curriculum and Player Progression

## 14.1 Training Goal

The progression system shall qualify the player in disciplined trading operations, not reward speculative profit alone. Advanced access shall depend on repeatable process competence, emergency readiness, and financial-state understanding.

## 14.2 Curriculum Structure

```text
Trading Flight School
├── Cockpit Familiarization
├── Market and Instrument Qualification
├── Pre-Market Preparation Rating
├── Risk and Position-Sizing Rating
├── Order Execution Rating
├── Trade Management Rating
├── Portfolio Management Rating
├── Data-Degraded / Instrument Rating
├── Emergency Procedures Rating
├── Post-Market Review Rating
└── Final Trading Checkride
```

## 14.3 Curriculum Modules

| Rating | Core Competencies | Example Required Missions |
| --- | --- | --- |
| Cockpit Familiarization | Identify panels, interpret gauges, arm/disarm trading, read warning states | Cold-start cockpit tour; identify invalid gauge; kill-switch test |
| Market and Instrument Qualification | Read tick, quantity, session, margin, and lifecycle rules | Equity session/auction; futures expiry; FX conversion exercise |
| Pre-Market Rating | Reconcile state, set limits, classify regime, mark levels, define no-trade rules | Normal open; event-heavy calendar; unavailable backup feed |
| Risk and Sizing Rating | Calculate planned risk, cost, gap allowance, margin, and valid quantity | Variable stop distance; multi-currency sizing; stress-risk block |
| Order Execution Rating | Select order type, handle latency, queue, partial fills, cancel/replace | Passive limit queue; marketable limit; cancel-fill race |
| Trade Management Rating | Preserve stop integrity, trim by rule, execute time/target/invalidation exits | Normal winner; controlled loss; volatility regime shift |
| Portfolio Rating | Manage correlation, concentration, leverage, margin, and aggregate risk | Correlated cluster; margin increase; multi-position trim |
| Data-Degraded Rating | Detect stale/conflicting data and operate safely with reduced instrumentation | Feed disagreement; clock drift; backup route failure |
| Emergency Rating | Execute black-swan, outage, and drawdown procedures | Flash crash; partial fill plus outage; hard loss lockout |
| Post-Market Rating | Reconcile, journal, explain deviations, and define remediation | Full debrief; incident report; accounting discrepancy |
| Final Checkride | Integrate all competencies with limited assistance | Multi-phase scenario with one or more compound failures |

## 14.4 Qualification State

```text
NOT_STARTED
  -> TRAINING
  -> ELIGIBLE_FOR_CHECKRIDE
  -> QUALIFIED
  -> RECURRENT_DUE
  -> EXPIRED
```

Alternative branch:

```text
TRAINING or CHECKRIDE -> REMEDIATION_REQUIRED -> TRAINING
```

## 14.5 Player Qualification Contract

```text
PlayerQualification
├── player_id
├── rating_id
├── rating_version
├── qualification_state
├── prerequisite_ratings
├── required_missions
├── completed_missions
├── best_process_scores
├── critical_breach_count
├── checkride_attempts
├── qualification_timestamp
├── recurrent_due_timestamp
├── remediation_assignments
└── evidence_references
```

## 14.6 Progression Rules

```text
IF Required_Process_Score >= Rating_Threshold
AND Required_Missions_Passed
AND Critical_Breach_Count == 0
AND Prerequisite_Ratings are QUALIFIED
THEN Qualification_State = QUALIFIED
ELSE assign targeted remediation.
```

- Profit shall not unlock higher risk, leverage, or emergency authority.
- A profitable but unsafe mission shall not satisfy a qualification requirement.
- A controlled loss or correct no-trade decision may satisfy a mission when process requirements pass.
- Advanced cockpit complexity may unlock progressively, but core risk and emergency indicators shall never be hidden.
- Recurrent emergency practice may be required after a configurable period.
- Expired ratings may restrict advanced scenarios until requalified.

## 14.7 Adaptive Remediation

The debrief system shall map repeated weakness patterns to specific missions:

| Weakness Pattern | Remediation |
| --- | --- |
| Stop widening | Risk-trim and controlled-loss missions |
| Oversizing | Position-sizing boundary exercises |
| Overtrading | Activity-rate and cooldown missions |
| Poor outage handling | Unknown-order and reconciliation exercises |
| Slow flash-crash response | Volatility, liquidity, and margin emergency drills |
| Weak journaling | Evidence and post-market review missions |
| Correlation blindness | Portfolio-cluster scenarios |
| Future-data misuse in practice | Point-in-time replay and no-lookahead tutorial |

## 14.8 Leaderboards and Comparative Scoring

Where comparative rankings exist, order them primarily by:

1. Process score.
2. Safety record.
3. Emergency response quality.
4. Risk-adjusted consistency.
5. P&L as a bounded secondary measure.

A leaderboard shall not rank raw return above hard safety compliance. Runs with invalid replay integrity or critical breaches are not eligible for official ranking.

## 14.9 Training Acceptance Rules

| Requirement ID | Requirement |
| --- | --- |
| `TRN_001` | Every rating has explicit competencies, prerequisites, missions, and pass conditions |
| `TRN_002` | Progression never depends on profit alone |
| `TRN_003` | No-trade and controlled-loss outcomes can earn qualification credit |
| `TRN_004` | Critical breaches block checkride passage |
| `TRN_005` | Remediation is linked to observed behavior, not arbitrary repetition |
| `TRN_006` | Recurrent and expired qualification states are supported |
| `TRN_007` | Unlocks do not hide mandatory safety information |

---

# 15. Stress-Loss and Gap-Risk Model

## 15.1 Purpose

Nominal stop-loss risk is not always the true potential loss. Gaps, halts, liquidity collapse, correlation convergence, margin changes, and connectivity failure may cause execution beyond the planned stop or prevent immediate exit. The simulator shall calculate both nominal and stressed risk.

## 15.2 Trade Risk Layers

```text
Nominal_Stop_Risk =
  Planned_Risk defined under Core Financial Metric Definitions
```

```text
Displayed_Trade_Risk =
  max(
    Nominal_Stop_Risk,
    Liquidity_Adjusted_Risk,
    Gap_Stress_Risk,
    Event_Stress_Risk,
    Margin_Liquidation_Risk
  )
```

Overlapping components shall not be added blindly. Each stress scenario shall calculate one coherent loss path; the displayed stressed risk is the worst applicable scenario or the policy-defined tail aggregate.

## 15.3 Stress Scenario Profile

```text
StressScenarioProfile
├── profile_id
├── version
├── eligible_asset_classes
├── eligible_instruments
├── price_shocks
├── volatility_multiplier
├── spread_multiplier
├── depth_reduction_percent
├── gap_distribution_or_fixed_shocks
├── correlation_override
├── fx_conversion_shocks
├── margin_requirement_shocks
├── halt_duration_assumption
├── exit_latency_assumption
├── financing_or_funding_shocks
├── scenario_weights
├── aggregation_method
└── approval_state
```

## 15.4 Standard Shock Catalogue

| Shock | Modeled Effect | Required Recalculation |
| --- | --- | --- |
| Directional price shock | Immediate adverse price move | P&L, equity, stop gap, margin, drawdown |
| Volatility expansion | Wider future price distribution | Slippage reserve, stop gap, strategy envelope |
| Spread multiplication | Worse liquidation-side mark and execution | Equity, risk, fill price, margin |
| Depth collapse | Larger market impact and partial fill probability | Liquidity-adjusted risk and exit duration |
| Correlation convergence | Diversification weakens during stress | Portfolio cluster and total stress loss |
| Currency shock | Account conversion changes | Equity, margin, and risk in account currency |
| Overnight gap | Price opens beyond protective order | Gap loss and realized exit price |
| Margin increase | Required collateral rises | Margin reserve and liquidation proximity |
| Trading halt | Exit delayed until reopen | Gap, queue, and time-at-risk loss |
| Connectivity delay | Player cannot confirm or amend promptly | Exit latency and unknown-state risk |

## 15.5 Portfolio Stress Loss

```text
Projected_Portfolio_Stress_Loss =
  max Loss_Across_Approved_Stress_Scenarios
```

For each scenario, the engine shall revalue all positions and pending exposure together, applying the scenario's correlation and liquidity assumptions.

```text
Projected_Post_Stress_Equity =
  Current_Equity - Projected_Portfolio_Stress_Loss
```

```text
IF Current_Drawdown
   + Projected_Portfolio_Stress_Loss
   >= Effective_Hard_Drawdown_Limit
THEN block or resize the proposed trade.
```

## 15.6 Stress-Risk States

```text
NORMAL
  -> CAUTION
  -> RESTRICTED
  -> BLOCKED
  -> EMERGENCY
```

| State | Default Meaning | Gameplay Permission |
| --- | --- | --- |
| `NORMAL` | Stress loss comfortably inside policy buffer | Normal gates apply |
| `CAUTION` | Stress buffer is declining | Warning and explicit acknowledgement |
| `RESTRICTED` | Stress loss approaches configured limit | Lower size, no scale-ins, stricter liquidity requirements |
| `BLOCKED` | Proposed trade would breach stress policy | New trade denied |
| `EMERGENCY` | Existing portfolio stress breaches hard survival threshold | Emergency reduction policy activates |

Thresholds shall be profile-driven.

## 15.7 Continuous Recalculation

Stress risk shall recalculate when any of the following changes:

- Price, volatility, spread, depth, correlation, or FX conversion.
- Position or pending-order quantity.
- Stop, target, or exit plan.
- Margin requirement.
- Scheduled-event proximity.
- Venue status or connectivity state.
- Scenario shock profile.

A continuously valid checklist item shall regress when stressed risk crosses its permitted boundary.

## 15.8 Model Transparency

The cockpit and debrief shall show:

- The governing stress profile and version.
- The worst scenario name.
- Nominal risk versus stressed risk.
- Principal loss drivers.
- Whether the model uses fixed shocks, historical replay, or seeded simulation.
- Known limitations and unsupported risks.

Stress outputs shall be labeled estimates, not guarantees of maximum loss.

## 15.9 Stress-Risk Validation

| Requirement ID | Requirement |
| --- | --- |
| `STR_001` | Every proposed trade receives nominal and stressed risk evaluation when the policy enables stress gating |
| `STR_002` | Portfolio stress revalues all correlated positions together |
| `STR_003` | Stop orders are not assumed to guarantee the stop price |
| `STR_004` | Stress assumptions are versioned and visible in debrief |
| `STR_005` | Unknown stress inputs produce a conservative restricted or blocked state |
| `STR_006` | Stress-gate failure can resize, block, or trigger emergency reduction according to policy |

---

# 16. Approved Strategy Expectancy Contract

## 16.1 Purpose

A strategy may use a lower minimum risk-to-reward ratio only when a versioned expectancy profile demonstrates that the strategy's complete outcome distribution and costs justify the exception. The expectancy gate shall never weaken account-level risk, margin, drawdown, liquidity, stress, or integrity limits.

## 16.2 Expectancy Definition

```text
Expected_Value_R =
  Win_Rate x Average_Win_R
  - Loss_Rate x Average_Loss_R
  - Average_Cost_R
```

The calculation shall include all trade outcomes in the approved sample, including partial exits, fees, slippage, financing, and rule-defined time exits.

## 16.3 Approved Expectancy Profile

```text
ApprovedExpectancyProfile
├── profile_id
├── version
├── strategy_id
├── strategy_version
├── eligible_instrument_profile_ids
├── eligible_market_regimes
├── eligible_sessions
├── eligible_order_and_exit_models
├── sample_start
├── sample_end
├── sample_size
├── point_in_time_data_status
├── in_sample_method
├── out_of_sample_status
├── walk_forward_or_holdout_definition
├── expected_win_rate
├── average_win_r
├── average_loss_r
├── average_cost_r
├── expected_value_r
├── payoff_distribution_reference
├── maximum_historical_drawdown
├── tail_loss_metrics
├── permitted_minimum_risk_reward
├── permitted_risk_per_trade
├── stress_profile_id
├── approval_state
├── approved_by
├── approval_timestamp
├── review_due_timestamp
├── expiry_timestamp
├── suspension_conditions
└── evidence_references
```

## 16.4 Approval States

```text
DRAFT
  -> UNDER_REVIEW
  -> APPROVED
  -> SUSPENDED
  -> EXPIRED
  -> REVOKED
```

Only `APPROVED` is eligible for the expectancy exception.

## 16.5 Eligibility Rule

```text
Approved_Expectancy_Gate = TRUE only when:
  Profile_State == APPROVED
  AND Current_Time < Expiry_Timestamp
  AND Strategy_ID_And_Version match exactly
  AND Instrument_Profile is eligible
  AND Market_Regime is eligible
  AND Session is eligible
  AND Order_And_Exit_Model match
  AND Stress_Profile is current
  AND no Suspension_Condition is active
```

```text
IF any eligibility condition fails
THEN Approved_Expectancy_Gate = FALSE
AND apply the standard policy risk-to-reward rule.
```

## 16.6 Evidence and Governance Rules

- The sample and methodology shall be fixed and referenced; the player cannot edit them during a session.
- Out-of-sample or equivalent validation status shall be explicit.
- Data shall respect point-in-time and no-lookahead rules.
- Costs and slippage shall reflect the same execution assumptions used by the simulator.
- Strategy version changes shall require a new or explicitly revalidated profile.
- Approval thresholds are governance inputs and shall not be fabricated as universal constants in this specification.
- The profile shall state known limitations, excluded regimes, and tail risks.

## 16.7 Performance Drift and Suspension

The simulator may monitor current strategy outcomes against the profile's permitted operating envelope.

```text
IF Strategy_Stress exceeds suspension threshold
OR observed execution costs exceed approved range
OR regime becomes ineligible
OR evidence/profile expires
THEN Expectancy_Profile_State = SUSPENDED_FOR_SESSION
AND new trades use the standard risk-to-reward gate.
```

Suspension shall not force an unsafe immediate exit; open positions continue under their approved management and risk policies unless another emergency rule applies.

## 16.8 Expectancy Validation Requirements

| Requirement ID | Requirement |
| --- | --- |
| `EXP_001` | The profile references an exact strategy and instrument/profile version |
| `EXP_002` | The sample includes costs and execution assumptions |
| `EXP_003` | Point-in-time and out-of-sample status are explicit |
| `EXP_004` | Expired, suspended, mismatched, or revoked profiles cannot bypass risk-to-reward |
| `EXP_005` | Expectancy approval cannot loosen hard account or stress limits |
| `EXP_006` | Every use of the exception is logged with profile ID, version, and eligibility result |
| `EXP_007` | Strategy drift can suspend the exception without rewriting prior events |

---

# 17. System Contracts and Translation Models

## 17.1 Logical System Boundaries

These boundaries define responsibilities and data ownership. They do not prescribe a phased build order, programming language, or physical folder structure.

| System Domain | Normative Responsibility |
| --- | --- |
| Cockpit State and UI | Panel registry, displayed state, controls, alert presentation, mode-specific assistance, accessibility, and player interaction routing |
| Instrument and Venue Profiles | Product metadata, sessions, tick/quantity rules, order capabilities, margin, lifecycle, and eligibility |
| Market Simulation | Price and order-book events, calendar, venue status, volatility, liquidity, regime, corporate actions, and scenario injection |
| Simulation Clock and Replay | Point-in-time visibility, event sequencing, pause/branch policy, replay identity, determinism, and no-lookahead enforcement |
| Portfolio, Accounting, and Ledger | Cash, balance, equity, P&L, costs, valuation, currency conversion, margin, positions, and immutable postings |
| Risk and Policy | Effective-rule resolution, position sizing, stop validation, aggregate risk, drawdown, stress loss, expectancy eligibility, and emergency governance |
| Execution | Order intent, idempotency, acknowledgements, queue, fills, slippage, partial fills, cancel/replace, OCO, and order-state transitions |
| Checklist State Machine | Phase gates, prerequisites, completion, regression, failure severity, mode behavior, and emergency interruption |
| Scenario Engine | Versioned missions, event triggers, compound failures, pass/fail conditions, and golden-replay identity |
| Persistence and Recovery | Durable intent, snapshots, immutable event stream, restart recovery, reconciliation, and session integrity |
| Training and Progression | Curriculum, ratings, prerequisites, remediation, checkrides, recurrent qualification, and comparative scoring eligibility |
| Review and Scoring | Journal, telemetry, feedback, replay, debrief, process-first score, and official mission finalization |
| Verification | Requirement traceability, invariant checks, transition coverage, golden runs, and evidence records |

## 17.2 Required Domain Contracts

### Trade Plan

```text
TradePlan
├── trade_id
├── session_id
├── scenario_id
├── policy_profile_id
├── policy_profile_version
├── instrument_profile_id
├── instrument_profile_version
├── strategy_id
├── strategy_version
├── direction
├── market_regime
├── entry_rule
├── entry_price
├── invalidation_rule
├── stop_loss_price
├── target_or_exit_rule
├── position_size
├── planned_risk
├── displayed_stressed_risk
├── planned_reward
├── net_risk_reward
├── expectancy_profile_id
├── expectancy_eligibility_result
├── expected_costs
├── expected_slippage
├── news_risk_status
├── liquidity_status
├── correlation_status
├── margin_status
├── approval_state
└── player_notes
```

### Portfolio State

```text
PortfolioState
├── account_id
├── account_currency
├── settled_cash
├── account_balance
├── account_equity
├── daily_reference_equity
├── total_reference_equity
├── realized_pnl
├── unrealized_pnl
├── accrued_income
├── accrued_costs
├── daily_drawdown
├── total_drawdown
├── available_margin
├── margin_used
├── reserved_order_margin
├── buying_power
├── gross_leverage
├── total_open_risk
├── projected_stress_loss
├── stress_risk_state
├── open_positions
├── pending_orders
├── symbol_exposure
├── correlated_exposure
├── valuation_policy_id
├── reconciliation_state
├── risk_state
└── account_lock_state
```

### Checklist Step

```text
ChecklistStep
├── id
├── phase
├── display_text
├── required_panel
├── required_interactions
├── prerequisites
├── completion_conditions
├── invalidation_conditions
├── warning_conditions
├── failure_conditions
├── severity
├── enforcement_class
├── continuous_monitoring
├── dwell_time_seconds
├── scoring_weight
├── mode_behavior
└── policy_profile_overrides
```

### Trading Event

```text
TradingEvent
├── event_id
├── source_event_id
├── source_sequence
├── simulation_timestamp
├── market_event_time
├── client_receive_time
├── player_action_time
├── processing_time
├── session_id
├── player_id
├── scenario_id
├── replay_id
├── policy_profile_id
├── instrument_profile_id
├── cockpit_panel
├── action_type
├── previous_state
├── new_state
├── market_snapshot_ref
├── portfolio_snapshot_ref
├── checklist_step_id
├── validation_result
├── warning_codes
├── order_id
├── fill_id
├── trade_id
├── ledger_entry_ids
├── score_delta
└── integrity_hash
```

### Additional Authoritative Contracts

The following contracts are defined in their authoritative sections and shall be part of the system model:

| Contract | Authoritative Section |
| --- | --- |
| `InstrumentVenueProfile` | Section 5 |
| `LedgerEntry` | Section 6 |
| `SimulationClock` and `ReplayIdentity` | Section 7 |
| `ValuationPolicy` and `FXConversionRate` | Section 8 |
| `ScenarioDefinition` and `InjectedEvent` | Section 9 |
| `DurableSessionState` | Section 10 |
| `VerificationRecord` | Section 11 |
| `LatencyProfile` and `QueueState` | Section 12 |
| `AlertEvent` | Section 13 |
| `PlayerQualification` | Section 14 |
| `StressScenarioProfile` | Section 15 |
| `ApprovedExpectancyProfile` | Section 16 |

## 17.3 Specification Acceptance Criteria

The specification is satisfied only when all of the following are true:

1. Every checklist step has a unique ID, real control or panel, measurable expected state, and explicit validation result.
2. The UI reads actual market, account, order, position, ledger, and risk state; checking a box never creates financial state by itself.
3. All trade-launch conditions are reevaluated at submit time using current point-in-time data.
4. Every scenario selects explicit, versioned market, venue, instrument, account, strategy, stress, and scoring profiles.
5. Unsupported or incomplete instrument profiles are ineligible and never use a silent fallback model.
6. Tick, quantity, contract value, session, currency, margin, order, and lifecycle rules are enforced by the selected instrument profile.
7. Order, position, and ledger transitions follow the formal state machines and preserve unknown states until reconciliation.
8. Cancel-pending orders remain executable until authoritative cancellation confirmation.
9. Fills, corrections, fees, financing, corporate actions, settlements, and liquidations create immutable balanced ledger events.
10. Position quantity, protective coverage, equity, margin, drawdown, idempotency, and event-sequence invariants are checked continuously.
11. Data-stale, unknown-order, ledger-integrity, recovery-lock, daily-drawdown, and flash-crash states interrupt normal gameplay immediately.
12. Cancel, protection, and risk-reducing exit actions remain available when new exposure is locked, where technically possible.
13. Simulation time is the sole authority for information availability; future data is inaccessible to every UI and system component.
14. Scored sessions prohibit rewind and authoritative rollback; practice branches are marked and isolated.
15. Identical replay identity and player events reproduce identical market, fill, ledger, state, alert, and score outputs.
16. Account balance, equity, P&L, costs, valuation, margin, and multi-currency conversion are reproducible from stored events and declared profiles.
17. Unknown or stale valuation inputs create a visible unknown/restricted state rather than fabricated certainty.
18. Published scenarios have deterministic triggers, fair information availability, measurable pass/fail rules, compound-event priorities, and golden replays.
19. Restart and crash recovery restore the authoritative clock, scenario, orders, fills, positions, protection, ledger, emergencies, counters, and score state.
20. Application restart cannot erase losses, fills, warnings, cooldowns, or emergency consequences.
21. Every normative requirement is traceable to positive, negative, boundary, regression, recovery, concurrency, persistence, determinism, and integrity evidence as applicable.
22. Required compound-failure tests pass without duplicate orders, missing fills, uncontrolled positions, or inconsistent ledger state.
23. Latency distinguishes market-event, display, player-action, venue-arrival, fill, and execution-report times.
24. Queue and fill behavior respects available liquidity, order type, price limits, time-in-force, venue rules, and cancel/replace races.
25. No limit order receives an impossible fill and no stop order is represented as guaranteeing its trigger price.
26. Alerts use explicit severity, priority, lifecycle, root-cause grouping, acknowledgement, and resolution states.
27. Critical information is accessible without relying only on color or audio, and emergency risk-reduction controls remain reachable.
28. Response-time scoring begins only when the player can perceive the actionable condition.
29. Guided, Standard, Expert, and Challenge behavior changes assistance and permitted procedural override without weakening non-bypassable account or integrity locks.
30. No-trade decisions can complete a mission successfully when safety gates block launch.
31. A profitable result cannot override a critical process, risk, integrity, or replay failure.
32. Training progression is based on demonstrated process competence, prerequisites, checkrides, and remediation—not profit alone.
33. Critical breaches prevent qualification, while controlled losses and correct stand-down decisions may earn full competence credit.
34. Nominal, liquidity-adjusted, gap, event, margin-liquidation, and portfolio stress risks are calculated under versioned assumptions.
35. A proposed trade is resized or blocked when projected stress loss breaches the effective policy limit.
36. An expectancy exception applies only through an approved, current, exactly matched, evidence-backed profile.
37. Expired, suspended, mismatched, or revoked expectancy profiles fall back to the normal risk-to-reward gate.
38. Every action, warning, override, checklist transition, fill, financial event, emergency response, and score change is recorded for replay and debrief.
39. Session closure requires authoritative reconciliation, valid ledger and replay integrity, complete required journals, persisted counters, and a durable secured marker.
40. All numerical defaults remain configurable and are never embedded as universal financial truths.

---

**End of Specification**

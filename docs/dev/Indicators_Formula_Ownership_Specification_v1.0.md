# HaruQuantAI Indicators Domain — Formula and Ownership Specification

**Version:** 1.0
**Status:** Draft target specification
**Purpose:** Standalone formula catalogue and ownership boundary for the `Indicators` domain
**Intended destination:** Fold the approved content into `app/services/indicators/README.md`

---

## 1. Purpose

This document defines:

1. The exact ownership boundary of every indicator category.
2. The canonical mathematical formula or deterministic decision rule for each indicator.
3. Required inputs, parameters, outputs, warm-up rules, and invalid-state behavior.
4. Cross-category dependencies that prevent duplicate calculations.
5. The snapshot contract used by Strategy, Risk, Simulator, Analytics, and UI-API.

This is a **measurement specification**, not a strategy specification. An indicator may describe market state, but it must not return `BUY`, `SELL`, `ALLOW_TRADE`, `POSITION_SIZE`, or a broker order.

---

## 2. Non-Negotiable Domain Boundary

### Indicators owns

- Deterministic calculations over approved point-in-time market inputs.
- Indicator parameter profiles and formula versions.
- Indicator state labels that are direct transformations of measured values.
- Indicator snapshots, component contributions, confidence, completeness, and invalid-state reasons.
- Cross-indicator composition only where this document explicitly assigns a composite owner.

### Indicators consumes

- Canonical bars, ticks, trades, order-book updates, volume, session evidence, and data-health evidence from Data.
- Instrument precision, tick size, and venue metadata from Brokers/Data contracts.
- No future record: every consumed value must satisfy `available_at <= as_of`.

### Indicators does not own

- Market-data acquisition, repair, persistence mechanics, or provider adapters.
- Strategy setup approval or trade direction.
- Risk policy, position sizing, stop validation, drawdown limits, or trade permission.
- Broker order submission, execution, fills, or reconciliation.
- Simulated fill probability, latency, or market impact.
- Portfolio accounting or P&L.
- UI rendering.

### Canonical ownership rule

```text
One mathematical concept has one canonical owner.

A consuming module may:
- read the canonical output,
- transform it into its own higher-level state,
- expose component contributions.

A consuming module may not:
- recalculate the same primitive under another name,
- silently change smoothing, window, annualization, or price source,
- substitute missing input with an optimistic default.
```

---

## 3. Category Ownership Matrix

| Module | Owns | Consumes | Must Not Recalculate or Decide | Primary Outputs |
| --- | --- | --- | --- | --- |
| `market_speed/` | Composite market intensity, signed velocity, acceleration, and activity rates | Trend velocity, volume, order-flow velocity, volatility expansion | Canonical ATR, realized volatility, DMI/ADX, liquidity, trade permission | `MarketSpeedSnapshot` |
| `regime/` | Point-in-time regime classification and deterministic resolver | Trend, volatility, liquidity, structure, event state | Primitive trend/volatility/liquidity formulas; strategy compatibility | `MarketRegimeSnapshot` |
| `trend/` | Directional movement and trend-strength measurements | Closed OHLC/price series; ATR where explicitly required | Volatility ownership, pattern approval, strategy direction | `TrendSnapshot` |
| `structure/` | Price levels, pivots, anchored references, gaps, and level clusters | Closed bars, trades/volume, session anchors | Pattern completion, trade invalidation policy, order placement | `StructureSnapshot` |
| `liquidity/` | Cost and capacity to transact | Quotes, order-book depth, trades, requested-size context where declared | Directional order-flow interpretation; simulated fill result | `LiquiditySnapshot` |
| `order_flow/` | Directional pressure from trades and book changes | Sequenced trades and L1/L2 book events | Liquidity capacity policy, simulated fills, trade approval | `OrderFlowSnapshot` |
| `volatility/` | Canonical range and return-dispersion measures | Closed OHLC and return series | Direction, trend classification, risk limits, position size | `VolatilitySnapshot` |
| `patterns/` | Bounded deterministic geometric/candlestick evidence | Confirmed pivots, structure, closed OHLC | `BUY`/`SELL`, risk approval, target probability | `PatternSnapshot` |
| `snapshots/` | Versioned publication contracts and input enforcement | All category outputs and source metadata | Indicator mathematics or business decisions | Typed indicator snapshots |

---

## 4. Dependency Direction

```text
Data / Brokers metadata
        │
        ├──> volatility/
        ├──> trend/
        ├──> structure/
        ├──> liquidity/
        └──> order_flow/
                 │
                 ├──────────────┐
                 │              │
                 v              v
          market_speed/     patterns/
                 │              │
                 └──────┬───────┘
                        v
                     regime/
                        │
                        v
                    snapshots/
                        │
         Strategy / Risk / Simulator / UI-API
```

Key consequences:

```text
volatility/ calculates ATR and realized volatility.
trend/ may consume ATR but does not implement a second ATR.
market_speed/ consumes volatility and order-flow outputs.
regime/ consumes all primitive measurements and only classifies.
patterns/ consumes confirmed structure and never authorizes a trade.
```

---

## 5. Common Notation and Calculation Conventions

| Symbol | Meaning |
| --- | --- |
| \(O_t,H_t,L_t,C_t\) | Open, high, low, and close of closed bar \(t\) |
| \(V_t\) | Bar volume or explicitly declared tick volume |
| \(b_t,a_t\) | Best bid and best ask |
| \(q^b_{t,i},q^a_{t,i}\) | Bid/ask quantity at book level \(i\) |
| \(m_t=(a_t+b_t)/2\) | Mid-price |
| \(p_j,v_j,\epsilon_j\) | Trade price, trade size, and aggressor sign; \(\epsilon_j=+1\) buyer-initiated, \(-1\) seller-initiated |
| \(r_t=\ln(C_t/C_{t-1})\) | One-period log return |
| \(\delta\) | Instrument tick size |
| \(A\) | Annualization factor declared by profile; e.g. bars per year |
| \(\varepsilon\) | Small positive denominator guard declared by numeric policy |
| \(\operatorname{SMA}_n(x)\) | Arithmetic mean of the latest \(n\) valid observations |
| \(\operatorname{EMA}_{n,t}(x)\) | \(\alpha x_t+(1-\alpha)\operatorname{EMA}_{n,t-1}(x)\), \(\alpha=2/(n+1)\) |
| \(\operatorname{RMA}_{n,t}(x)\) | Wilder smoothing: \(((n-1)RMA_{t-1}+x_t)/n\) after an initial \(n\)-value mean |
| \(\operatorname{std}_n(x)\) | Sample standard deviation over \(n\) observations unless stated otherwise |
| \(Z_n(x_t)\) | \((x_t-\operatorname{mean}_n(x))/\operatorname{std}_n(x)\) |
| \(\operatorname{clip}(x,l,u)\) | Clamp \(x\) to \([l,u]\) |
| \(\mathbf{1}[\cdot]\) | Indicator function: 1 when condition is true, else 0 |

### Universal input rules

- Use only **closed** bars unless the indicator explicitly consumes tick/book events.
- Every source record must be ordered and satisfy `available_at <= as_of`.
- Missing mandatory input returns `UNAVAILABLE`; it is never replaced with zero.
- A zero denominator returns `UNAVAILABLE` unless a mathematically specified zero result exists.
- All windows, smoothing methods, annualization factors, thresholds, tie rules, and price sources belong to a versioned `IndicatorProfile`.
- When multiple equal highs/lows exist, the default tie rule is **most recent occurrence**; a profile may select earliest, but the rule must be explicit.
- A snapshot is publishable only when warm-up and data-health requirements are satisfied.

### Source-status labels used below

- **External formula:** the mathematical definition follows the linked source.
- **Canonical project rule:** HaruQuantAI defines the exact operational rule here because no single universal market standard exists.
- **Composite rule:** HaruQuantAI composes outputs owned by other indicator modules; it does not duplicate their formulas.

---

# 6. `market_speed/` — Market Speed and Intensity

## Ownership boundary

`market_speed/` answers:

> How quickly, forcefully, and actively is the market evolving now?

It owns velocity, acceleration, event-rate measurements, and the final cockpit intensity gauge. It does **not** own ATR, realized volatility, liquidity, or canonical order-flow imbalance.


### `IND-MS-01` — Log-Price Velocity

- **Formula status:** Canonical project rule; ROC-compatible
- **Required inputs:** Closed prices `C`, aware timestamps `T`.
- **Parameters:** `k >= 1`; output time unit `u` in seconds/minutes/bars.
- **Formula / rule:**

$$
PV_{t,k}=\frac{\ln(C_t)-\ln(C_{t-k})}{(T_t-T_{t-k})/u}
$$

For equally spaced bars and `u = one bar`, this reduces to the \(k\)-bar log return divided by \(k\).

- **Outputs:** `price_velocity` (signed log-return per selected time unit), `direction = sign(PV)`, `as_of`.
- **Warm-up / invalid state:** Needs `k+1` valid closes and positive elapsed time; non-positive prices are invalid.
- **References:** [R03] TA-Lib ROC/ROCP catalogue.
- **Ownership notes:** This is the canonical price-velocity input to Market Speed. Strategy may consume it but must not redefine it.


### `IND-MS-02` — Momentum Acceleration

- **Formula status:** Canonical project rule
- **Required inputs:** `PV` from `IND-MS-01`.
- **Parameters:** `k`; acceleration time unit `u`.
- **Formula / rule:**

$$
PA_{t,k}=\frac{PV_{t,k}-PV_{t-k,k}}{(T_t-T_{t-k})/u}
$$

- **Outputs:** `price_acceleration` (signed velocity change per time-unit squared), `acceleration_state`.
- **Warm-up / invalid state:** Needs two complete non-overlapping velocity observations; otherwise `WARMING_UP`.
- **References:** [R03] ROC primitives; exact second-difference rule is project-defined.
- **Ownership notes:** Consumes canonical price velocity; it does not calculate a different momentum series.


### `IND-MS-03` — Volume Acceleration

- **Formula status:** Canonical project rule
- **Required inputs:** Declared volume series `V`; volume kind/unit metadata.
- **Parameters:** Aggregation window `w`; lag `k`; `epsilon`.
- **Formula / rule:**

Define rolling activity volume:

$$
RV_{t,w}=\sum_{i=t-w+1}^{t}V_i
$$

Then:

$$
VA_{t,k,w}=
\frac{\ln(RV_{t,w}+\varepsilon)-\ln(RV_{t-k,w}+\varepsilon)}
{(T_t-T_{t-k})/u}
$$

- **Outputs:** `volume_acceleration`, `volume_kind`, `unit`, and source window.
- **Warm-up / invalid state:** Missing or mixed volume kinds are invalid. Zero volume is valid only when source semantics prove that zero is genuine.
- **References:** [R28] Price Volume Trend is a related price/volume reference; this exact acceleration rule is project-defined.


### `IND-MS-04` — Market-Event Arrival Rate

- **Formula status:** Canonical project rule
- **Required inputs:** Sequenced trades, ticks, or order-book events with event timestamps.
- **Parameters:** Event type filter; rolling duration `W > 0`.
- **Formula / rule:**

$$
\lambda_t^{(type)}=
\frac{\#\{e_j: T_t-W < T_j \le T_t,\ type(e_j)=type\}}{W}
$$

- **Outputs:** `events_per_second` (or configured time unit), event type, event count, coverage duration.
- **Warm-up / invalid state:** A gap or unverified event sequence makes the result `DEGRADED` or `UNAVAILABLE`; it must not be interpreted as low activity.
- **References:** [R18] Order-book event research; counting rule is project-defined.


### `IND-MS-05` — Order-Flow Velocity

- **Formula status:** Composite rule
- **Required inputs:** Windowed `OFI` from `IND-OF-01`, plus the exact interval duration.
- **Parameters:** Window duration `W`.
- **Formula / rule:**

$$
OFV_t=\frac{OFI_{(T_t-W,T_t]}}{W}
$$

- **Outputs:** `order_flow_velocity` in quantity/time, signed direction, source OFI reference.
- **Warm-up / invalid state:** Unavailable whenever OFI input is unavailable or its interval does not match the declared window.
- **References:** [R18] Cont–Kukanov–Stoikov OFI.
- **Ownership notes:** `order_flow/` owns OFI. `market_speed/` only converts the windowed quantity into a rate.


### `IND-MS-06` — Volatility Expansion Rate

- **Formula status:** Composite rule
- **Required inputs:** Positive `ATR` or another approved volatility series from `volatility/`.
- **Parameters:** Lag `k`; time unit `u`; selected volatility indicator ID/version.
- **Formula / rule:**

For ATR:

$$
VER_{t,k}=
\frac{\ln(ATR_t)-\ln(ATR_{t-k})}{(T_t-T_{t-k})/u}
$$

The same rule may be applied to another strictly positive approved volatility series, but the source indicator identity must be retained.

- **Outputs:** `volatility_expansion_rate`, source volatility ID/version, direction (`EXPANDING`, `CONTRACTING`, `STABLE`).
- **Warm-up / invalid state:** Non-positive or unavailable source volatility is invalid.
- **References:** [R09] ATR; exact expansion-rate transform is project-defined.
- **Ownership notes:** `volatility/` owns ATR. This module owns only the rate of change of the published volatility value.


### `IND-MS-07` — Composite Market Speed Gauge

- **Formula status:** Canonical composite rule
- **Required inputs:** Valid outputs from `IND-MS-01` to `IND-MS-06`; optional signed order-flow velocity.
- **Parameters:** Normalization window `n_z`; clipping bound `z_max > 0`; weights `w_i >= 0`, `sum(w_i)=1`; band thresholds.
- **Formula / rule:**

For each component \(x_i\), compute:

$$
u_i=\frac{|\operatorname{clip}(Z_{n_z}(x_i),-z_{max},z_{max})|}{z_{max}}
\in[0,1]
$$

For non-directional activity components, negative standardized values may be floored at zero when the profile declares that only expansion contributes.

Intensity:

$$
MS_t=100\sum_i w_i u_i
$$

Signed direction:

$$
D_t=\operatorname{sign}
\left(
w_p Z(PV_t)+w_a Z(PA_t)+w_o Z(OFV_t)
\right)
$$

Default cockpit bands, overrideable only by profile version:

```text
0 <= MS < 25   -> SLOW
25 <= MS < 50  -> NORMAL
50 <= MS < 75  -> FAST
75 <= MS <=100 -> EXTREME
```

- **Outputs:** `composite_score [0,100]`, `speed_band`, `direction`, `acceleration_state`, and per-component contributions.
- **Warm-up / invalid state:** No silent renormalization when a mandatory component is missing. Optional components may be omitted only when the profile defines alternate weights.
- **References:** [R02] Trading Cockpit airspeed metaphor; exact formula is project-defined.
- **Ownership notes:** This is a cockpit composite, not a forecast and not a volatility replacement.



# 7. `regime/` — Market Regime Classification

## Ownership boundary

`regime/` classifies measured state. It consumes canonical Trend, Volatility, Liquidity, Structure, Order Flow, and event-state outputs. It must not recalculate those primitives.

### `IND-RG-01` — ADX/DMI Trend Regime

- **Formula status:** Composite classification rule
- **Required inputs:** `ADX`, `+DI`, `-DI` from `IND-TR-03`.
- **Parameters:** `adx_trend`, `adx_range`; defaults 25 and 20, with `adx_range < adx_trend`.
- **Formula / rule:**

```text
IF ADX >= adx_trend AND +DI > -DI -> TREND_UP
ELSE IF ADX >= adx_trend AND -DI > +DI -> TREND_DOWN
ELSE IF ADX <= adx_range -> RANGE
ELSE -> TRANSITION
```

- **Outputs:** `regime_candidate`, `trend_strength`, `direction`, threshold-distance confidence.
- **Warm-up / invalid state:** Unavailable when any DMI input is unavailable. Thresholds are profile-driven, not universal constants.
- **References:** [R05] DMI/ADX.


### `IND-RG-02` — Choppiness Regime

- **Formula status:** External formula plus project thresholds
- **Required inputs:** Closed `H`, `L`, `C`.
- **Parameters:** Window `n` (default 14); trend/range thresholds (defaults 38.2/61.8).
- **Formula / rule:**

$$
CHOP_t=
100\,
\frac{
\log_{10}\left(
\frac{\sum_{i=t-n+1}^{t}TR_i}
{\max(H_{t-n+1:t})-\min(L_{t-n+1:t})}
\right)}
{\log_{10}(n)}
$$

```text
CHOP <= lower_threshold -> DIRECTIONAL
CHOP >= upper_threshold -> CHOPPY_RANGE
otherwise               -> TRANSITION
```

- **Outputs:** `choppiness [0,100]`, `state`, threshold distances.
- **Warm-up / invalid state:** Requires non-zero high-low range and `n` valid bars.
- **References:** [R10] TradingView Choppiness Index.


### `IND-RG-03` — Hurst Persistence Regime

- **Formula status:** External R/S method with project classification
- **Required inputs:** A stationary input series `X`, normally log returns; multiple sub-window sizes.
- **Parameters:** Window sizes `N={N1,...,Nk}`; minimum observations per size; thresholds (defaults 0.45/0.55).
- **Formula / rule:**

For each scale \(N\), partition the analysis sample into complete non-overlapping blocks \(b\) of length \(N\). For each block:

$$
Y_{b,j}=\sum_{i=1}^{j}(X_{b,i}-\bar X_{b,N}),\quad
R_{b,N}=\max_jY_{b,j}-\min_jY_{b,j},\quad
S_{b,N}=\operatorname{std}(X_{b,1:N})
$$

Average only valid blocks with \(S_{b,N}>0\):

$$
(R/S)_N=\operatorname{mean}_b\left(R_{b,N}/S_{b,N}\right)
$$

Estimate \(H\) as the OLS slope across scales:

$$
\log((R/S)_N)=c+H\log(N)+\epsilon_N
$$

```text
H > upper -> PERSISTENT
H < lower -> ANTI_PERSISTENT
otherwise -> RANDOM_LIKE
```

- **Outputs:** `hurst_exponent`, regression `R2`, regime candidate, window set.
- **Warm-up / invalid state:** Any `S_N = 0`, insufficient scales, or poor fit below configured `R2` makes the output unavailable/degraded.
- **References:** [R15] Hurst (1951).


### `IND-RG-04` — Donchian Breakout Regime

- **Formula status:** Composite classification rule
- **Required inputs:** Prior-only Donchian levels from `IND-ST-02` and current close.
- **Parameters:** Window `n`; breakout buffer `beta_atr`; ATR source reference.
- **Formula / rule:**

Using levels computed from bars ending at \(t-1\):

$$
U_{t-1,n}=\max(H_{t-n:t-1}),\quad
L_{t-1,n}=\min(L_{t-n:t-1})
$$

```text
C_t > U + beta_atr*ATR_t -> BREAKOUT_UP
C_t < L - beta_atr*ATR_t -> BREAKOUT_DOWN
otherwise                -> INSIDE_CHANNEL
```

- **Outputs:** `breakout_state`, breached level, distance in price/ATR/ticks.
- **Warm-up / invalid state:** Current bar must not be included in the channel used to test its own breakout.
- **References:** [R11] Donchian Channels.
- **Ownership notes:** `structure/` owns the channel levels; `regime/` owns only the state classification.


### `IND-RG-05` — Volatility–Liquidity Stress Regime

- **Formula status:** Canonical project rule
- **Required inputs:** Volatility percentile, relative-spread percentile or z-score, depth percentile, quote freshness, scheduled-event state.
- **Parameters:** Profile thresholds `p_vol_extreme`, `p_spread_high`, `p_depth_low`, freshness limit.
- **Formula / rule:**

```text
IF scheduled_event_active
    -> EVENT
ELSE IF quote_is_stale
    -> DATA_DEGRADED
ELSE IF volatility_pct >= p_vol_extreme
     OR spread_pct >= p_spread_extreme
     OR depth_pct <= p_depth_critical
    -> UNSTABLE
ELSE IF spread_pct >= p_spread_high
     AND depth_pct <= p_depth_low
    -> LOW_LIQUIDITY
ELSE
    -> NORMAL_CONDITIONS
```

- **Outputs:** `stress_regime`, triggering conditions, threshold margins, input snapshot references.
- **Warm-up / invalid state:** Missing mandatory volatility or liquidity evidence returns `UNKNOWN`, not `NORMAL_CONDITIONS`.
- **References:** [R02] Trading Cockpit regime and stress panels; exact resolver is project-defined.


### `IND-RG-06` — Final Regime Resolver

- **Formula status:** Canonical project rule
- **Required inputs:** All valid regime candidates from `IND-RG-01` to `IND-RG-05`.
- **Parameters:** Versioned priority list and confidence aggregation.
- **Formula / rule:**

Default priority:

```text
EVENT
> DATA_DEGRADED
> UNSTABLE
> LOW_LIQUIDITY
> BREAKOUT_UP / BREAKOUT_DOWN
> TREND_UP / TREND_DOWN
> CHOPPY_RANGE / RANGE
> TRANSITION
> UNKNOWN
```

The first active state in priority order becomes `primary_regime`. Secondary states remain attached as evidence.

- **Outputs:** `primary_regime`, `secondary_regimes`, confidence, reason codes, source references.
- **Warm-up / invalid state:** Conflicting inputs are not discarded; they are exposed as secondary evidence. An unavailable critical input may force `UNKNOWN`.
- **References:** [R02] Trading Cockpit regime panel; exact priority is project-defined.



# 8. `trend/` — Trend Direction and Strength

## Ownership boundary

`trend/` owns directional and trend-strength measurements. It may consume ATR from `volatility/` for normalization or band construction, but it may not implement another ATR.

### `IND-TR-01` — EMA and ATR-Normalized EMA Slope

- **Formula status:** External EMA plus project normalization
- **Required inputs:** Closed price source `P` (default close); canonical ATR for normalized slope.
- **Parameters:** EMA length `n`; slope lag `k`; ATR ID/version.
- **Formula / rule:**

$$
EMA_t=\alpha P_t+(1-\alpha)EMA_{t-1},\quad
\alpha=\frac{2}{n+1}
$$

$$
Slope^{ATR}_{t,k}=
\frac{EMA_t-EMA_{t-k}}{k\cdot ATR_t}
$$

- **Outputs:** `ema`, raw slope, ATR-normalized slope, direction.
- **Warm-up / invalid state:** EMA requires declared seed policy. Normalized slope is unavailable when ATR is missing or zero.
- **References:** [R04] TradingView EMA; [R09] ATR.


### `IND-TR-02` — Linear-Regression Slope and Trend Fit

- **Formula status:** Canonical OLS formula
- **Required inputs:** Closed price or log-price series `y_i`; ordered index `x_i=0,...,n-1`.
- **Parameters:** Window `n`; price transform (`price` or `log_price`).
- **Formula / rule:**

$$
\hat\beta=
\frac{\sum_i(x_i-\bar x)(y_i-\bar y)}
{\sum_i(x_i-\bar x)^2},
\qquad
\hat\alpha=\bar y-\hat\beta\bar x
$$

$$
R^2=1-\frac{\sum_i(y_i-\hat\alpha-\hat\beta x_i)^2}
{\sum_i(y_i-\bar y)^2}
$$

- **Outputs:** `slope`, `intercept`, `r_squared`, fitted end value, direction.
- **Warm-up / invalid state:** Constant input has undefined `R2` unless profile explicitly returns `0`; default is `UNAVAILABLE`.
- **References:** [R03] TA-Lib statistic functions.


### `IND-TR-03` — Directional Movement Index and ADX

- **Formula status:** External Wilder formula
- **Required inputs:** Closed `H`, `L`, `C`.
- **Parameters:** Length `n` (default 14); Wilder `RMA` smoothing.
- **Formula / rule:**

$$
Up_t=H_t-H_{t-1},\qquad Down_t=L_{t-1}-L_t
$$

$$
DM^+_t=
\begin{cases}
Up_t,&Up_t>Down_t\ \land\ Up_t>0\\
0,&otherwise
\end{cases}
$$

$$
DM^-_t=
\begin{cases}
Down_t,&Down_t>Up_t\ \land\ Down_t>0\\
0,&otherwise
\end{cases}
$$

$$
TR_t=\max(H_t-L_t,\ |H_t-C_{t-1}|,\ |L_t-C_{t-1}|)
$$

$$
DI^+_t=100\frac{RMA_n(DM^+)_t}{RMA_n(TR)_t},\quad
DI^-_t=100\frac{RMA_n(DM^-)_t}{RMA_n(TR)_t}
$$

$$
DX_t=100\frac{|DI^+_t-DI^-_t|}{DI^+_t+DI^-_t},\quad
ADX_t=RMA_n(DX)_t
$$

- **Outputs:** `plus_di`, `minus_di`, `dx`, `adx`, direction dominance.
- **Warm-up / invalid state:** Undefined when smoothed TR or DI sum is zero. ADX warm-up includes both DM/TR and DX smoothing periods.
- **References:** [R05] TradingView DMI/ADX; [R03] TA-Lib ADX catalogue.


### `IND-TR-04` — Aroon Up, Down, and Oscillator

- **Formula status:** External formula
- **Required inputs:** Closed highs and lows.
- **Parameters:** Lookback `N`; window contains `N+1` bars.
- **Formula / rule:**

Let \(age_H\) and \(age_L\) be bars since the most recent highest high and lowest low in the \(N+1\)-bar window:

$$
AroonUp_t=100\frac{N-age_H}{N},\qquad
AroonDown_t=100\frac{N-age_L}{N}
$$

$$
AroonOsc_t=AroonUp_t-AroonDown_t
$$

- **Outputs:** `aroon_up`, `aroon_down`, `aroon_oscillator`, dominant direction.
- **Warm-up / invalid state:** Needs `N+1` bars. Tie behavior follows the profile's most-recent/earliest rule.
- **References:** [R06] TradingView Aroon Oscillator; [R03] TA-Lib AROON.


### `IND-TR-05` — MACD

- **Formula status:** External formula
- **Required inputs:** Closed price source `P`, normally close.
- **Parameters:** Fast `n_f`=12, slow `n_s`=26, signal `n_sig`=9 by default; exact MA type declared.
- **Formula / rule:**

$$
MACD_t=EMA_{n_f}(P)_t-EMA_{n_s}(P)_t
$$

$$
Signal_t=EMA_{n_{sig}}(MACD)_t
$$

$$
Histogram_t=MACD_t-Signal_t
$$

- **Outputs:** `macd`, `signal`, `histogram`, zero-line state, histogram acceleration.
- **Warm-up / invalid state:** Warm-up is governed by the slow MA plus signal seed policy.
- **References:** [R07] TradingView MACD; [R03] TA-Lib MACD.


### `IND-TR-06` — Supertrend

- **Formula status:** External concept with canonical recurrence
- **Required inputs:** Closed `H`, `L`, `C`; canonical ATR.
- **Parameters:** ATR length `n`; multiplier `m`.
- **Formula / rule:**

$$
HL2_t=(H_t+L_t)/2
$$

$$
BasicUpper_t=HL2_t+m\cdot ATR_t,\quad
BasicLower_t=HL2_t-m\cdot ATR_t
$$

$$
FinalUpper_t=
\begin{cases}
BasicUpper_t,&BasicUpper_t<FinalUpper_{t-1}\ \lor\ C_{t-1}>FinalUpper_{t-1}\\
FinalUpper_{t-1},&otherwise
\end{cases}
$$

$$
FinalLower_t=
\begin{cases}
BasicLower_t,&BasicLower_t>FinalLower_{t-1}\ \lor\ C_{t-1}<FinalLower_{t-1}\\
FinalLower_{t-1},&otherwise
\end{cases}
$$

The active line switches to `FinalLower` after a close above the prior upper line and to `FinalUpper` after a close below the prior lower line.

- **Outputs:** `supertrend_line`, `trend_direction`, band values, reversal timestamp.
- **Warm-up / invalid state:** Unavailable until ATR and prior band state exist. ATR remains owned by `volatility/`.
- **References:** [R08] TradingView Supertrend; [R09] ATR.



# 9. `structure/` — Support, Resistance, and Structural Levels

## Ownership boundary

`structure/` identifies measurable price references. It does not determine whether a level is a valid stop, target, or trade entry; Strategy and Risk own those decisions.

### `IND-ST-01` — Confirmed Swing High and Swing Low Pivots

- **Formula status:** Canonical project rule
- **Required inputs:** Closed highs/lows.
- **Parameters:** Left bars `l`; right bars `r`; strict/non-strict tie policy.
- **Formula / rule:**

Pivot high at index \(t\):

$$
H_t=\max(H_{t-l:t+r})
$$

Pivot low at index \(t\):

$$
L_t=\min(L_{t-l:t+r})
$$

The pivot is only **confirmed** at \(t+r\).

- **Outputs:** `pivot_type`, pivot price, pivot bar time, confirmation time, left/right strength.
- **Warm-up / invalid state:** No pivot may be published before its right-side confirmation bars are available.
- **References:** [R27] TradingView Pivot Points High/Low and Zig Zag.


### `IND-ST-02` — Donchian Channel Levels

- **Formula status:** External formula
- **Required inputs:** Closed highs and lows.
- **Parameters:** Window `n`; include-current or prior-only mode.
- **Formula / rule:**

$$
Upper_{t,n}=\max(H_{t-n+1:t}),\quad
Lower_{t,n}=\min(L_{t-n+1:t})
$$

$$
Middle_{t,n}=\frac{Upper_{t,n}+Lower_{t,n}}{2}
$$

- **Outputs:** `upper`, `lower`, `middle`, window bounds, age of each extreme.
- **Warm-up / invalid state:** Requires `n` bars. Breakout testing must use prior-only levels to avoid self-reference.
- **References:** [R11] TradingView Donchian Channels.


### `IND-ST-03` — Traditional Pivot Points

- **Formula status:** External formula
- **Required inputs:** Previous completed session high `H_p`, low `L_p`, close `C_p`.
- **Parameters:** Session calendar and pivot family; this row specifies Traditional.
- **Formula / rule:**

$$
P=(H_p+L_p+C_p)/3
$$

$$
R1=2P-L_p,\quad S1=2P-H_p
$$

$$
R2=P+(H_p-L_p),\quad S2=P-(H_p-L_p)
$$

$$
R3=2P+(H_p-2L_p),\quad S3=2P-(2H_p-L_p)
$$

- **Outputs:** `P`, `R1..R3`, `S1..S3`, source session identity.
- **Warm-up / invalid state:** Session must be complete and calendar-authoritative. No current-session partial high/low is allowed.
- **References:** [R12] TradingView Pivot Points Standard.


### `IND-ST-04` — Anchored VWAP

- **Formula status:** External formula
- **Required inputs:** Trade price/size or closed-bar typical price/volume from an explicit anchor.
- **Parameters:** Anchor timestamp/event; price source `TP=(H+L+C)/3` for bar mode.
- **Formula / rule:**

For observations \(i=a,\ldots,t\):

$$
TP_i=(H_i+L_i+C_i)/3
$$

$$
AVWAP_{a,t}=
\frac{\sum_{i=a}^{t}TP_iV_i}
{\sum_{i=a}^{t}V_i}
$$

- **Outputs:** `anchored_vwap`, cumulative volume, anchor identity, price source, deviation from AVWAP.
- **Warm-up / invalid state:** Zero cumulative volume is unavailable. Anchor must be explicit and already visible at `as_of`.
- **References:** [R13] TradingView VWAP and Anchored VWAP.


### `IND-ST-05` — Volume Profile POC and Value Area

- **Formula status:** External concept with canonical binning
- **Required inputs:** Sequenced trade prices and sizes; alternatively a declared lower-timeframe allocation model.
- **Parameters:** Price range, number/size of bins, value-area fraction `q` (default 0.70).
- **Formula / rule:**

For price bin \(B_j\):

$$
VP_j=\sum_i v_i\mathbf{1}[p_i\in B_j]
$$

Point of Control:

$$
POC=\operatorname{center}\left(B_{\arg\max_j VP_j}\right)
$$

Value area:

1. Start with the POC bin.
2. Compare the immediately adjacent upper and lower unselected bins.
3. Add the one with greater volume; deterministic tie rule selects the lower bin first unless profile overrides.
4. Continue until cumulative selected volume is at least \(q\sum_jVP_j\).
5. `VAL` and `VAH` are the lower and upper selected-bin boundaries.

- **Outputs:** `volume_by_bin`, `POC`, `VAL`, `VAH`, total volume, bin specification.
- **Warm-up / invalid state:** Approximate bar-volume allocation must be labeled; tick/trade mode is canonical. Missing volume is invalid.
- **References:** [R14] TradingView Volume Profile concepts and value-area algorithm.


### `IND-ST-06` — Price Gap and Three-Bar Fair-Value Gap

- **Formula status:** Canonical project rule
- **Required inputs:** Closed highs and lows; tick size.
- **Parameters:** Minimum gap `g_min = max(k_tick*delta, k_atr*ATR)`; optional ATR reference.
- **Formula / rule:**

One-bar gap:

$$
GapUp_t=L_t-H_{t-1}
$$

Valid upward gap when \(GapUp_t\ge g_{min}\).

$$
GapDown_t=L_{t-1}-H_t
$$

Valid downward gap when \(GapDown_t\ge g_{min}\).

Three-bar imbalance:

$$
FVGUp_t=L_t-H_{t-2},\qquad FVGDown_t=L_{t-2}-H_t
$$

A positive value above `g_min` forms the corresponding gap zone.

- **Outputs:** `gap_type`, lower/upper bounds, size in price/ticks/ATR, creation time, fill percentage.
- **Warm-up / invalid state:** All involved bars must be closed; unsupported or stale ATR makes ATR-normalized filtering unavailable.
- **References:** [R25] Pattern-recognition background; exact gap rule is project-defined.


### `IND-ST-07` — Structural-Level Clustering

- **Formula status:** Canonical project rule
- **Required inputs:** Confirmed levels with price, type, weight, and timestamp.
- **Parameters:** Distance tolerance `tau=max(k_tick*delta, k_atr*ATR)`; linkage rule; decay half-life.
- **Formula / rule:**

Sort levels by price. Adjacent levels belong to the same cluster when their distance is at most \(\tau\).

Cluster price:

$$
P_{cluster}=\frac{\sum_i w_iP_i}{\sum_iw_i}
$$

Optional recency-adjusted weight:

$$
w_i=w_i^{base}\cdot 2^{-age_i/half\_life}
$$

- **Outputs:** `cluster_price`, zone bounds, member levels, total weight, first/last confirmation time.
- **Warm-up / invalid state:** Unconfirmed pivots cannot enter a cluster. ATR-dependent tolerance is unavailable without canonical ATR.
- **References:** [R25] Systematic technical-pattern research; exact clustering is project-defined.



# 10. `liquidity/` — Transaction Cost and Capacity

## Ownership boundary

`liquidity/` answers:

> How much can be traded now, and at what observable or estimated cost?

It does not decide whether the trade should occur and does not simulate an authoritative fill.

### `IND-LQ-01` — Quoted and Relative Spread

- **Formula status:** Canonical market-microstructure formula
- **Required inputs:** Fresh best bid `b_t` and ask `a_t`.
- **Parameters:** Output unit: price, percentage, or basis points.
- **Formula / rule:**

$$
Spread_t=a_t-b_t,\qquad
Mid_t=(a_t+b_t)/2
$$

$$
RelativeSpread_t=\frac{a_t-b_t}{Mid_t}
$$

$$
SpreadBps_t=10^4\cdot RelativeSpread_t
$$

- **Outputs:** `spread_price`, `relative_spread`, `spread_bps`, quote age.
- **Warm-up / invalid state:** `a_t < b_t` is crossed-book/integrity failure; zero or negative midpoint is invalid.
- **References:** [R18] Limit-order-book variables.


### `IND-LQ-02` — Effective Spread

- **Formula status:** Canonical market-microstructure formula
- **Required inputs:** Trade price `p_j`, contemporaneous pre-trade midpoint `m_j`, aggressor sign `epsilon_j`.
- **Parameters:** Matching tolerance between trade and quote timestamps.
- **Formula / rule:**

Signed effective spread:

$$
ES_j=2\epsilon_j(p_j-m_j)
$$

Unsigned cost:

$$
|ES_j|=2|p_j-m_j|
$$

Basis points:

$$
ESBps_j=10^4\frac{ES_j}{m_j}
$$

- **Outputs:** Per-trade and window-average effective spread in price/bps.
- **Warm-up / invalid state:** Missing contemporaneous quote or unknown aggressor side makes signed output unavailable; unsigned cost may remain valid.
- **References:** [R17] Kyle liquidity/price-impact framework; formula is standard microstructure accounting.


### `IND-LQ-03` — Executable Depth Within Basis-Point Band

- **Formula status:** Canonical project rule
- **Required inputs:** Fresh L2 book levels.
- **Parameters:** Band `B` bps; side or both sides.
- **Formula / rule:**

For ask-side buy capacity:

$$
Depth^{ask}_B=
\sum_i q^a_i\,
\mathbf{1}
\left[
10^4\frac{p^a_i-m}{m}\le B
\right]
$$

For bid-side sell capacity:

$$
Depth^{bid}_B=
\sum_i q^b_i\,
\mathbf{1}
\left[
10^4\frac{m-p^b_i}{m}\le B
\right]
$$

- **Outputs:** `bid_depth`, `ask_depth`, band, number of levels included, book timestamp.
- **Warm-up / invalid state:** Sequence gaps, stale snapshots, or crossed books make output unavailable.
- **References:** [R18] Order-book depth and price impact.


### `IND-LQ-04` — Order-Book Depth Slope

- **Formula status:** Canonical project rule
- **Required inputs:** Fresh ordered L2 levels.
- **Parameters:** Levels `K`; through-origin OLS.
- **Formula / rule:**

For one side, define price distance in bps \(d_i\) and cumulative depth \(Q_i=\sum_{j=1}^{i}q_j\).

Through-origin slope:

$$
\beta_{depth}=
\frac{\sum_{i=1}^{K}d_iQ_i}
{\sum_{i=1}^{K}d_i^2}
$$

Units: quantity per basis point.

- **Outputs:** `bid_depth_slope`, `ask_depth_slope`, conservative minimum, fit diagnostics.
- **Warm-up / invalid state:** Needs at least two valid levels and positive distance variance.
- **References:** [R18] Depth/impact relation; exact slope estimator is project-defined.


### `IND-LQ-05` — Amihud Illiquidity

- **Formula status:** External formula
- **Required inputs:** Daily or profile-declared interval return and traded notional.
- **Parameters:** Window `D`; currency and notional normalization.
- **Formula / rule:**

For interval \(d\), dollar/notional volume \(DV_d\):

$$
ILLIQ_D=
\frac{1}{D}\sum_{d=1}^{D}
\frac{|R_d|}{DV_d}
$$

- **Outputs:** `amihud_illiquidity`, return unit, notional currency, sample count.
- **Warm-up / invalid state:** Intervals with zero/unverified notional are excluded only under an explicit missing-data rule; otherwise output is unavailable.
- **References:** [R16] Amihud (2002).


### `IND-LQ-06` — Kyle Lambda

- **Formula status:** External model estimated by canonical OLS
- **Required inputs:** Interval mid-price change `Delta m_k` and signed quantity/notional `Q_k`.
- **Parameters:** Estimation window; quantity or notional unit; intercept inclusion.
- **Formula / rule:**

Estimate:

$$
\Delta m_k=\alpha+\lambda Q_k+\epsilon_k
$$

With intercept:

$$
\hat\lambda=
\frac{\operatorname{Cov}(Q,\Delta m)}
{\operatorname{Var}(Q)}
$$

- **Outputs:** `kyle_lambda` (price impact per quantity/notional), intercept, `R2`, standard error, sample count.
- **Warm-up / invalid state:** Zero signed-flow variance or insufficient observations is unavailable. Unit must be explicit.
- **References:** [R17] Kyle (1985).


### `IND-LQ-07` — Depth-to-Requested-Order Ratio

- **Formula status:** Canonical project rule
- **Required inputs:** Opposite-side executable depth and a proposed order quantity supplied as context.
- **Parameters:** Maximum slippage band `B`; requested quantity `Q_req > 0`.
- **Formula / rule:**

$$
DOR_B=\frac{ExecutableDepth_B}{Q_{req}}
$$

```text
DOR >= 1 -> visible depth covers requested size within band
DOR < 1  -> visible depth is insufficient within band
```

- **Outputs:** `depth_order_ratio`, covered quantity, shortfall, side, band.
- **Warm-up / invalid state:** This output is descriptive. Simulator owns actual fill probability and fill result.
- **References:** [R18] Depth/impact research; exact ratio is project-defined.



# 11. `order_flow/` — Directional Book and Trade Pressure

## Ownership boundary

`order_flow/` owns signed pressure and changes in displayed/consumed supply and demand. It does not decide liquidity sufficiency or simulate fills.

### `IND-OF-01` — Level-1 Order Flow Imbalance (OFI)

- **Formula status:** External formula
- **Required inputs:** Sequenced best bid/ask prices and sizes.
- **Parameters:** Aggregation interval.
- **Formula / rule:**

For book event \(n\):

$$
e_n=
\mathbf{1}[P^B_n\ge P^B_{n-1}]q^B_n
-\mathbf{1}[P^B_n\le P^B_{n-1}]q^B_{n-1}
-\mathbf{1}[P^A_n\le P^A_{n-1}]q^A_n
+\mathbf{1}[P^A_n\ge P^A_{n-1}]q^A_{n-1}
$$

Windowed OFI:

$$
OFI_k=\sum_{n\in interval\ k}e_n
$$

- **Outputs:** `ofi` in quantity units, event count, interval, normalized OFI if profile specifies depth normalization.
- **Warm-up / invalid state:** Any sequence gap or reset not handled by a new snapshot invalidates the interval.
- **References:** [R18] Cont, Kukanov, and Stoikov.


### `IND-OF-02` — Book Imbalance

- **Formula status:** Canonical formula
- **Required inputs:** Fresh bid/ask quantities over top `K` levels.
- **Parameters:** Levels `K`; optional distance weights `w_i`.
- **Formula / rule:**

$$
BI_K=
\frac{\sum_{i=1}^{K}w_iq^b_i-\sum_{i=1}^{K}w_iq^a_i}
{\sum_{i=1}^{K}w_iq^b_i+\sum_{i=1}^{K}w_iq^a_i}
$$

Default \(w_i=1\).

- **Outputs:** `book_imbalance [-1,1]`, bid/ask weighted depth, level count.
- **Warm-up / invalid state:** Zero total depth or stale/crossed book is unavailable.
- **References:** [R19] Micro-price/order-book imbalance background.


### `IND-OF-03` — Cumulative Volume Delta

- **Formula status:** Canonical trade-flow formula
- **Required inputs:** Trades with verified aggressor sign and size.
- **Parameters:** Reset anchor/session and optional rolling window.
- **Formula / rule:**

$$
CVD_t=CVD_{t-1}+\epsilon_tv_t
$$

Rolling delta:

$$
\Delta CVD_{t,W}=\sum_{j:T_t-W<T_j\le T_t}\epsilon_jv_j
$$

- **Outputs:** `cvd`, rolling delta, buy volume, sell volume, unknown-side volume.
- **Warm-up / invalid state:** Unknown-side trades are reported separately and never assigned optimistically.
- **References:** [R18] Trade/order-flow context; exact cumulative accounting is project-defined.


### `IND-OF-04` — Aggressive Trade Imbalance

- **Formula status:** Canonical formula
- **Required inputs:** Buyer-initiated and seller-initiated trade volume in a window.
- **Parameters:** Window `W`.
- **Formula / rule:**

$$
ATI_W=
\frac{V^{buy}_W-V^{sell}_W}
{V^{buy}_W+V^{sell}_W}
$$

- **Outputs:** `aggressive_trade_imbalance [-1,1]`, buy/sell/unknown volume.
- **Warm-up / invalid state:** Zero known-side volume is unavailable; unknown-side share is disclosed.
- **References:** [R18] Order-flow research.


### `IND-OF-05` — Level-1 Weighted Midpoint (Microprice Proxy)

- **Formula status:** Canonical proxy; not the full Stoikov model
- **Required inputs:** Best bid/ask and displayed sizes.
- **Parameters:** None beyond freshness.
- **Formula / rule:**

$$
WMP_t=
\frac{a_tq^b_t+b_tq^a_t}
{q^b_t+q^a_t}
$$

$$
MicroDeviation_t=WMP_t-m_t
$$

- **Outputs:** `weighted_midpoint`, `microprice_deviation`, normalized deviation in ticks/bps.
- **Warm-up / invalid state:** Zero total displayed size or stale/crossed quote is unavailable.
- **References:** [R19] Stoikov micro-price research.
- **Ownership notes:** The full Stoikov micro-price is a state-dependent expected future mid-price. This formula is explicitly named a proxy.


### `IND-OF-06` — Queue Depletion Rate

- **Formula status:** Canonical project rule
- **Required inputs:** Ordered queue-size events at a fixed price level, executions, additions, cancellations.
- **Parameters:** Window `W`; side and level identity.
- **Formula / rule:**

Gross depletion:

$$
Depletion_W=
\frac{ExecutedQty_W+CanceledQty_W}{W}
$$

Net queue change:

$$
NetChange_W=
\frac{Q_{end}-Q_{start}}{W}
$$

- **Outputs:** `gross_depletion_rate`, `net_change_rate`, executions, cancellations, additions.
- **Warm-up / invalid state:** A price-level change or book reset closes the measurement interval.
- **References:** [R18] Order-book event framework.


### `IND-OF-07` — Liquidity Sweep Detector

- **Formula status:** Canonical project rule
- **Required inputs:** Aggressor-signed trades and ordered price levels.
- **Parameters:** Maximum elapsed time `Delta`; minimum levels `K`; minimum quantity/notional.
- **Formula / rule:**

A buy sweep is true when, within \(\Delta\):

```text
all classified trades are buyer-initiated,
number of distinct ask prices consumed >= K,
total aggressive buy quantity >= Q_min.
```

A sell sweep is the mirror condition across bid levels.

- **Outputs:** `sweep_side`, levels consumed, start/end price, quantity, duration, price distance.
- **Warm-up / invalid state:** Mixed aggressor side, unknown sequence, or unverified level ordering returns no confirmed sweep.
- **References:** [R18] Order-book event research; exact detector is project-defined.


### `IND-OF-08` — Liquidity Replenishment Rate

- **Formula status:** Canonical project rule
- **Required inputs:** Book additions at a level after executions/cancellations.
- **Parameters:** Window `W`; level identity.
- **Formula / rule:**

$$
ReplenishmentRate_W=
\frac{\sum AddedQty_W}{W}
$$

Replacement ratio:

$$
ReplacementRatio_W=
\frac{\sum AddedQty_W}
{\sum ExecutedQty_W+\sum CanceledQty_W}
$$

- **Outputs:** `replenishment_rate`, `replacement_ratio`, additions and removals.
- **Warm-up / invalid state:** Denominator zero makes the ratio unavailable while the rate remains valid.
- **References:** [R18] Order-book event framework.


### `IND-OF-09` — Cancel-to-Trade Ratio

- **Formula status:** Canonical project rule
- **Required inputs:** Canceled displayed quantity and executed quantity over the same scope.
- **Parameters:** Window `W`; side/level scope.
- **Formula / rule:**

$$
CTR_W=
\frac{CanceledQty_W}{ExecutedQty_W}
$$

- **Outputs:** `cancel_trade_ratio`, canceled quantity, executed quantity, scope.
- **Warm-up / invalid state:** Zero executed quantity makes the ratio unavailable; do not force infinity into a finite value.
- **References:** [R18] Order-book event framework.



# 12. `volatility/` — Volatility Measurement and Envelope

## Ownership boundary

`volatility/` is the sole canonical owner of ATR, normalized ATR, realized volatility, range-based volatility, volatility distribution comparisons, and volatility-of-volatility.

### `IND-VOL-01` — True Range and Average True Range

- **Formula status:** External Wilder formula
- **Required inputs:** Closed `H`, `L`, `C`.
- **Parameters:** Length `n`=14 by default; Wilder `RMA`.
- **Formula / rule:**

$$
TR_t=\max(H_t-L_t,\ |H_t-C_{t-1}|,\ |L_t-C_{t-1}|)
$$

$$
ATR_t=RMA_n(TR)_t
$$

- **Outputs:** `true_range`, `atr` in price units.
- **Warm-up / invalid state:** Needs prior close; ATR needs declared warm-up/seed policy.
- **References:** [R09] TradingView ATR; [R29] TA-Lib volatility functions.


### `IND-VOL-02` — Normalized ATR / ATR Percent

- **Formula status:** External formula
- **Required inputs:** Canonical ATR and positive close.
- **Parameters:** ATR length inherited from source.
- **Formula / rule:**

$$
ATRP_t=100\frac{ATR_t}{C_t}
$$

- **Outputs:** `atr_percent` in percent and source ATR reference.
- **Warm-up / invalid state:** Unavailable for non-positive close or unavailable ATR.
- **References:** [R09] TradingView ATR%.


### `IND-VOL-03` — Close-to-Close Realized Volatility

- **Formula status:** Canonical statistical formula
- **Required inputs:** Closed positive prices and log returns.
- **Parameters:** Window `n`; annualization factor `A`.
- **Formula / rule:**

$$
\bar r=\frac1n\sum_{i=1}^{n}r_i
$$

$$
\sigma_{CC}=
\sqrt{
A\cdot\frac{1}{n-1}
\sum_{i=1}^{n}(r_i-\bar r)^2
}
$$

- **Outputs:** `realized_volatility` annualized, unannualized variance, return count.
- **Warm-up / invalid state:** Requires at least two returns; annualization must match timeframe/venue profile.
- **References:** [R23] RiskMetrics methodology and standard return variance.


### `IND-VOL-04` — EWMA Volatility

- **Formula status:** External RiskMetrics formula
- **Required inputs:** Log returns.
- **Parameters:** Decay `lambda` in `(0,1)`; annualization `A`; seed variance.
- **Formula / rule:**

$$
\sigma_t^2=
\lambda\sigma_{t-1}^2+(1-\lambda)r_t^2
$$

$$
\sigma^{ann}_t=\sqrt{A\sigma_t^2}
$$

- **Outputs:** `ewma_variance`, `ewma_volatility`, decay, annualization factor.
- **Warm-up / invalid state:** Seed method must be declared. Missing returns cannot be silently treated as zero.
- **References:** [R23] RiskMetrics Technical Document.


### `IND-VOL-05` — Parkinson Range Volatility

- **Formula status:** External formula
- **Required inputs:** Positive closed highs and lows.
- **Parameters:** Window `n`; annualization `A`.
- **Formula / rule:**

$$
\sigma_P=
\sqrt{
\frac{A}{4n\ln 2}
\sum_{i=1}^{n}
\left[\ln\left(\frac{H_i}{L_i}\right)\right]^2
}
$$

- **Outputs:** `parkinson_volatility`, range variance, sample count.
- **Warm-up / invalid state:** Requires positive `H`,`L` and `H>=L`; assumptions and overnight-gap limitation must be disclosed.
- **References:** [R20] Parkinson (1980).


### `IND-VOL-06` — Garman–Klass Volatility

- **Formula status:** External formula
- **Required inputs:** Positive closed `O`, `H`, `L`, `C`.
- **Parameters:** Window `n`; annualization `A`.
- **Formula / rule:**

$$
\sigma_{GK}=
\sqrt{
\frac{A}{n}
\sum_{i=1}^{n}
\left[
\frac12\left(\ln\frac{H_i}{L_i}\right)^2
-(2\ln2-1)\left(\ln\frac{C_i}{O_i}\right)^2
\right]
}
$$

- **Outputs:** `garman_klass_volatility`, variance, sample count.
- **Warm-up / invalid state:** Negative numerical variance from finite precision must not be silently square-rooted; clamp only within declared tiny tolerance, otherwise invalid.
- **References:** [R21] Garman and Klass (1980).


### `IND-VOL-07` — Rogers–Satchell Volatility

- **Formula status:** External formula
- **Required inputs:** Positive closed `O`, `H`, `L`, `C`.
- **Parameters:** Window `n`; annualization `A`.
- **Formula / rule:**

$$
\sigma_{RS}=
\sqrt{
\frac{A}{n}
\sum_{i=1}^{n}
\left[
\ln\left(\frac{H_i}{O_i}\right)
\ln\left(\frac{H_i}{C_i}\right)
+
\ln\left(\frac{L_i}{O_i}\right)
\ln\left(\frac{L_i}{C_i}\right)
\right]
}
$$

- **Outputs:** `rogers_satchell_volatility`, variance, sample count.
- **Warm-up / invalid state:** All prices must be positive. Assumptions and sampling interval are included in metadata.
- **References:** [R22] Rogers and Satchell (1991).


### `IND-VOL-08` — Bollinger BandWidth

- **Formula status:** External formula
- **Required inputs:** Closed price source.
- **Parameters:** Length `n`=20; standard-deviation multiplier `k`=2; sample/population convention declared.
- **Formula / rule:**

$$
Middle_t=SMA_n(C)_t
$$

$$
Upper_t=Middle_t+k\cdot std_n(C)_t,\quad
Lower_t=Middle_t-k\cdot std_n(C)_t
$$

$$
BBW_t=100\frac{Upper_t-Lower_t}{Middle_t}
$$

- **Outputs:** `middle`, `upper`, `lower`, `bandwidth_percent`.
- **Warm-up / invalid state:** Zero/non-positive middle makes percentage bandwidth unavailable.
- **References:** [R24] TradingView Bollinger BandWidth and Bollinger Bands.


### `IND-VOL-09` — Volatility Percentile and Z-Score

- **Formula status:** Canonical statistical transform
- **Required inputs:** One canonical volatility series and historical comparison window.
- **Parameters:** Reference length `n`; tie method; sample standard deviation.
- **Formula / rule:**

Percentile rank:

$$
Pct_t=
100\frac{
\#\{x_i<x_t\}+0.5\#\{x_i=x_t\}
}{n}
$$

Z-score:

$$
Z_t=\frac{x_t-\bar x_n}{s_n}
$$

- **Outputs:** `percentile [0,100]`, `z_score`, reference mean/std, source indicator ID.
- **Warm-up / invalid state:** Constant reference window yields unavailable z-score; percentile remains definable.
- **References:** [R24] Relative-volatility interpretation; exact rank convention is project-defined.


### `IND-VOL-10` — Volatility of Volatility

- **Formula status:** Canonical statistical formula
- **Required inputs:** A positive canonical volatility series `sigma_t`.
- **Parameters:** Window `n`; optional annualization disabled by default.
- **Formula / rule:**

Log-change form:

$$
u_t=\ln(\sigma_t/\sigma_{t-1})
$$

$$
VoV_t=\operatorname{std}_n(u)
$$

- **Outputs:** `volatility_of_volatility`, mean log change, sample count.
- **Warm-up / invalid state:** Non-positive/missing volatility invalidates affected returns; no zero substitution.
- **References:** [R23] Time-varying volatility context; exact transform is project-defined.



# 13. `patterns/` — Deterministic Pattern Evidence

## Ownership boundary

Chart patterns do not have one universally accepted numerical definition. The rules below are therefore the **canonical HaruQuantAI definitions**. External references support systematic pattern recognition, but the exact tolerances and confirmation rules are project-owned and versioned.

Common parameters:

| Parameter | Meaning |
| --- | --- |
| `tau_price` | Similarity tolerance, usually `max(k_tick*delta, k_atr*ATR)` |
| `d_min` | Minimum prominence/depth in price or ATR |
| `s_min`, `s_max` | Minimum/maximum bars between pivots |
| `beta` | Breakout confirmation buffer in ATR or ticks |
| `m_confirm` | Maximum bars allowed for confirmation |
| `pivot_ref` | Confirmed pivots from `IND-ST-01` only |

Every pattern output contains `DETECTED`, `FORMING`, `CONFIRMED`, `INVALIDATED`, or `EXPIRED`; pivot times; bounds; confirmation time; invalidation level; confidence components; and source references.

### `IND-PT-01` — Double Top / Double Bottom

- **Formula status:** Canonical project rule
- **Required inputs:** Confirmed pivots and closed prices.
- **Parameters:** `tau_price`, prominence `d_min`, separation range, confirmation buffer `beta`.
- **Formula / rule:**

Double top with highs \(P_1,P_2\) and intervening low \(N\):

$$
\frac{|P_1-P_2|}{(P_1+P_2)/2}\le\tau_{price}
$$

$$
\min(P_1,P_2)-N\ge d_{min}
$$

Confirmed when:

$$
C_t<N-\beta
$$

within `m_confirm` bars after \(P_2\). Double bottom is the exact vertical mirror.

- **Outputs:** `pattern_type`, two pivot prices/times, neckline, confirmation/invalidation state.
- **Warm-up / invalid state:** Only confirmed pivots are used. A third higher high before neckline break invalidates a double top; mirror for bottom.
- **References:** [R25] Lo, Mamaysky, and Wang; exact rule is project-defined.


### `IND-PT-02` — Head and Shoulders / Inverse

- **Formula status:** Canonical project rule
- **Required inputs:** Five alternating confirmed pivots and closed prices.
- **Parameters:** Shoulder tolerance, head prominence, spacing tolerance, neckline breakout buffer.
- **Formula / rule:**

For bearish \(S_L,T_L,H,T_R,S_R\):

$$
|S_L-S_R|/\bar S\le\tau_{shoulder}
$$

$$
H-\max(S_L,S_R)\ge d_{head}
$$

Neckline is the line through troughs \(T_L,T_R\). Confirm when close falls below the time-aligned neckline by `beta`. The inverse pattern mirrors all inequalities.

- **Outputs:** Shoulder/head/trough pivots, neckline slope, confirmation point, invalidation level.
- **Warm-up / invalid state:** Asymmetry outside configured spacing/height tolerances prevents confirmation.
- **References:** [R25] Lo, Mamaysky, and Wang; exact rule is project-defined.


### `IND-PT-03` — Triangle

- **Formula status:** Canonical project rule
- **Required inputs:** At least two confirmed pivot highs and two pivot lows.
- **Parameters:** OLS fit threshold, convergence rate, minimum touches, breakout buffer.
- **Formula / rule:**

Fit:

$$
Upper(t)=a_u+b_ut,\qquad Lower(t)=a_l+b_lt
$$

```text
Symmetrical: b_u < 0 and b_l > 0
Ascending:   |b_u| <= slope_flat and b_l > 0
Descending:  b_u < 0 and |b_l| <= slope_flat
```

Require positive but shrinking gap \(Upper(t)-Lower(t)\). Confirm on close beyond the relevant boundary by `beta`.

- **Outputs:** `triangle_type`, boundary equations, apex estimate, touches, breakout state.
- **Warm-up / invalid state:** Crossed boundaries before confirmation invalidate the pattern.
- **References:** [R25] Systematic chart-pattern research; exact regression rule is project-defined.


### `IND-PT-04` — Flag / Pennant

- **Formula status:** Canonical project rule
- **Required inputs:** Closed prices, ATR, and consolidation pivots.
- **Parameters:** Impulse length, minimum impulse in ATR, max retracement fraction, consolidation duration.
- **Formula / rule:**

Impulse magnitude:

$$
ImpulseATR=\frac{|C_{end}-C_{start}|}{ATR_{start}}
$$

Require `ImpulseATR >= impulse_min`.

Retracement:

$$
Retrace=
\frac{|C_{consolidation\ extreme}-C_{end}|}
{|C_{end}-C_{start}|}
\le\rho_{max}
$$

A flag uses roughly parallel consolidation boundaries; a pennant uses converging boundaries. Confirm on breakout in the impulse direction.

- **Outputs:** `FLAG` or `PENNANT`, impulse direction/magnitude, boundaries, retracement, confirmation.
- **Warm-up / invalid state:** If retracement exceeds limit or breakout occurs opposite the impulse, invalidate.
- **References:** [R25] Systematic chart-pattern research; exact rule is project-defined.


### `IND-PT-05` — Inside Bar

- **Formula status:** Canonical project rule
- **Required inputs:** Two closed OHLC bars.
- **Parameters:** Strict or inclusive equality policy.
- **Formula / rule:**

Strict inside bar:

$$
H_t<H_{t-1}\quad\land\quad L_t>L_{t-1}
$$

Inclusive mode uses `<=` and `>=`.

- **Outputs:** `inside_bar=true/false`, mother-bar bounds, range ratio.
- **Warm-up / invalid state:** Both bars must be closed; equality behavior is profile-versioned.
- **References:** [R26] TA-Lib pattern catalogue provides related candlestick functions; exact inside-bar rule is project-defined.


### `IND-PT-06` — Bullish / Bearish Engulfing

- **Formula status:** Canonical explicit candlestick rule
- **Required inputs:** Two closed OHLC bars.
- **Parameters:** Body-only or full-range mode; this row specifies body-only.
- **Formula / rule:**

Bullish:

$$
C_{t-1}<O_{t-1},\quad C_t>O_t,\quad
O_t\le C_{t-1},\quad C_t\ge O_{t-1}
$$

Bearish:

$$
C_{t-1}>O_{t-1},\quad C_t<O_t,\quad
O_t\ge C_{t-1},\quad C_t\le O_{t-1}
$$

- **Outputs:** `BULLISH_ENGULFING`, `BEARISH_ENGULFING`, or none; body ratios.
- **Warm-up / invalid state:** Doji handling and equality are profile-versioned. Both bars must be closed.
- **References:** [R26] TA-Lib `CDLENGULFING`; exact inequalities are declared here.


### `IND-PT-07` — Breakout and Retest

- **Formula status:** Canonical project rule
- **Required inputs:** A confirmed structural level, closed OHLC, ATR.
- **Parameters:** Breakout buffer `beta`; retest tolerance `tau`; maximum retest bars `m`.
- **Formula / rule:**

Bullish breakout at \(t_b\):

$$
C_{t_b}>L+\beta
$$

Retest within `m` bars when:

$$
|Low_t-L|\le\tau
\quad\land\quad
C_t>L
$$

Bearish rule is mirrored using highs and closes below the level.

- **Outputs:** `breakout_side`, level reference, breakout time, retest time, hold/fail state.
- **Warm-up / invalid state:** A close back through the level beyond invalidation tolerance before a valid retest marks `FAILED_BREAKOUT`.
- **References:** [R25] Pattern-recognition background; exact rule is project-defined.


### `IND-PT-08` — Rising / Falling Wedge

- **Formula status:** Canonical project rule
- **Required inputs:** Confirmed highs and lows.
- **Parameters:** Minimum touches, OLS fit, convergence, slope relation, breakout buffer.
- **Formula / rule:**

Fit upper/lower lines as in triangles.

Rising wedge:

```text
b_u > 0, b_l > 0,
b_l > b_u,
gap decreases over time.
```

Falling wedge:

```text
b_u < 0, b_l < 0,
|b_u| > |b_l|,
gap decreases over time.
```

Confirmation requires a close outside the expected boundary by `beta`.

- **Outputs:** `RISING_WEDGE` or `FALLING_WEDGE`, lines, convergence, breakout state.
- **Warm-up / invalid state:** Non-converging or crossed lines invalidate.
- **References:** [R25] Systematic chart-pattern research; exact rule is project-defined.


### `IND-PT-09` — Rectangle / Trading Range

- **Formula status:** Canonical project rule
- **Required inputs:** Confirmed pivot highs/lows and closed prices.
- **Parameters:** Flat-slope threshold, level tolerance, minimum touches, minimum duration.
- **Formula / rule:**

Fit high and low boundary lines.

Require:

$$
|b_u|\le slope_{flat},\quad |b_l|\le slope_{flat}
$$

and all qualifying highs/lows lie within `tau_price` of their respective mean boundary, with at least the configured touch count.

- **Outputs:** `rectangle_upper`, `rectangle_lower`, touch counts, duration, breakout state.
- **Warm-up / invalid state:** Insufficient touches or range height below minimum invalidates.
- **References:** [R25] Lo, Mamaysky, and Wang; exact rule is project-defined.


### `IND-PT-10` — Three-Bar Reversal

- **Formula status:** Canonical project rule
- **Required inputs:** Three closed OHLC bars and ATR.
- **Parameters:** Minimum first-bar body, middle-bar excursion, confirmation fraction.
- **Formula / rule:**

Bullish three-bar reversal:

```text
1. Bar t-2 is bearish and body >= body_min*ATR.
2. Bar t-1 makes a lower low than t-2.
3. Bar t closes above the high of t-1
   and above O_(t-2) + confirm_fraction*|C_(t-2)-O_(t-2)|.
```

Bearish rule is mirrored.

- **Outputs:** `BULLISH_3BAR_REVERSAL`, `BEARISH_3BAR_REVERSAL`, or none; component evidence.
- **Warm-up / invalid state:** All three bars must be closed; ATR must be canonical and available.
- **References:** [R26] TA-Lib multi-bar pattern catalogue; exact rule is project-defined.



# 14. `snapshots/` — Publication Contract and Closed-Input Enforcement

`snapshots/` is not an indicator family. It owns the consistent output envelope and validates that a calculation is safe to publish.

## 14.1 Base `IndicatorSnapshot`

```text
IndicatorSnapshot
├── snapshot_id
├── indicator_id
├── indicator_version
├── profile_id
├── profile_version
├── category
├── symbol
├── venue
├── timeframe
├── as_of
├── available_at
├── source_start
├── source_end
├── source_record_count
├── source_dataset_id
├── source_dataset_hash
├── values
├── units
├── state
├── completeness
├── confidence
├── data_health
├── warmup_state
├── parameters
├── component_contributions
├── warnings
├── invalid_reasons
└── provenance
```

## 14.2 Required category snapshots

| Snapshot | Required category-specific values |
| --- | --- |
| `MarketSpeedSnapshot` | Composite score, band, direction, acceleration, component values/contributions |
| `MarketRegimeSnapshot` | Primary regime, secondary regimes, confidence, deterministic reason codes |
| `TrendSnapshot` | Direction, strength, slopes, DMI/ADX, Aroon, MACD/Supertrend values as requested |
| `StructureSnapshot` | Active pivots, levels, clusters, gaps, VWAP/profile references and invalidation timestamps |
| `LiquiditySnapshot` | Spread, depth, slope, impact proxies, capacity ratios, quote/book age |
| `OrderFlowSnapshot` | OFI, book imbalance, CVD, aggressive imbalance, microprice proxy, queue/sweep state |
| `VolatilitySnapshot` | ATR, ATR%, selected realized/range estimators, percentile, z-score, VoV |
| `PatternSnapshot` | Pattern type, state, pivots/bounds, confirmation, invalidation, confidence evidence |

## 14.3 Publication validation

```text
IF any source available_at > snapshot.as_of
THEN state = INVALID_FUTURE_INPUT

ELSE IF a required bar is not closed
THEN state = INCOMPLETE_INPUT

ELSE IF required source is stale beyond profile maximum age
THEN state = STALE_INPUT

ELSE IF required timeframe alignment is not backward-only
THEN state = MISALIGNED_INPUT

ELSE IF warm-up count is insufficient
THEN state = WARMING_UP

ELSE IF a mandatory dependency is unavailable
THEN state = DEPENDENCY_UNAVAILABLE

ELSE
THEN state = VALID
```

The snapshot must never render an unknown value as zero or a normal state.

---

# 15. Cross-Category Reuse Rules

| Primitive | Canonical owner | Valid consumers | Prohibited duplication |
| --- | --- | --- | --- |
| True Range / ATR / ATR% | `volatility/` | Trend, Structure, Market Speed, Patterns, Regime | Any second ATR implementation |
| DMI / ADX | `trend/` | Regime, Strategy, UI | Regime-specific DMI calculation |
| Donchian levels | `structure/` | Regime, Strategy, Patterns | Breakout module recomputing channel differently |
| OFI | `order_flow/` | Market Speed, Regime, Strategy | Market Speed deriving a second OFI |
| Spread/depth/capacity | `liquidity/` | Regime, Risk, Strategy, UI | Order Flow deciding liquidity sufficiency |
| Pivots and level clusters | `structure/` | Patterns, Strategy | Pattern modules publishing unconfirmed pivots |
| Volatility percentile | `volatility/` | Regime, Risk, Market Speed | Regime recomputing historical volatility distribution |
| Pattern state | `patterns/` | Strategy, UI, Analytics | Pattern output returning a trade decision |

---

# 16. Indicator Profile Requirements

Every calculation is bound to an immutable, versioned profile:

```text
IndicatorProfile
├── profile_id
├── version
├── indicator_id
├── formula_version
├── price_source
├── timeframe
├── window_lengths
├── smoothing_methods
├── annualization_factor
├── thresholds
├── tie_rules
├── missing_data_policy
├── warmup_policy
├── normalization_policy
├── clipping_policy
├── required_data_health
├── maximum_input_age
├── output_units
└── compatibility_metadata
```

Rules:

- A parameter change creates a new profile version.
- A formula-semantic change creates a new indicator formula version.
- Historical replays retain the exact profile and formula versions.
- No profile may silently fall back to a different window, source, or smoothing method.
- Thresholds such as `ADX >= 25` or `CHOP >= 61.8` are defaults, not universal truths.

---

# 17. Persistence and Database Boundary

Indicators calculations are pure and own no authoritative market or financial database state.

Permitted persistence:

- Versioned indicator/profile metadata if the current Indicators architecture owns it.
- Derived indicator artifacts through the project’s approved Data artifact/catalog boundary.
- Snapshot references required for replay, with formula/profile/data hashes.

Not permitted:

- Raw provider data.
- Broker credentials or connection state.
- Orders, fills, positions, P&L, risk decisions, or portfolio ledger records.
- A second copy of Data-owned market history.

---

# 18. Minimum Verification Requirements

For every indicator above:

1. Golden-value test against a hand-computed fixture.
2. Boundary tests for all thresholds and tie rules.
3. Warm-up test.
4. Missing, stale, future, out-of-order, and incomplete-input tests.
5. Determinism test for identical inputs/profile/version.
6. Parameter/version serialization test.
7. Unit and output-range validation.
8. Cross-category test proving the canonical owner is consumed rather than duplicated.
9. Multi-timeframe test proving only closed, backward-aligned higher-timeframe values are used.
10. A standalone usage example through the Indicators public boundary.

For every composite:

- Component contributions must sum to the published score within declared tolerance.
- Missing mandatory components fail closed.
- Changing a component profile/version changes the composite provenance.
- The composite cannot override an invalid primitive input.

---

# 19. Reference Index

| Ref | Source |
| --- | --- |
| R01 | HaruQuantAI Data README — canonical point-in-time data, `available_at`, no-lookahead, and cross-domain evidence boundary |
| R02 | Trading Cockpit Simulator specification — Market Momentum/Volatility Index, regime, liquidity, structure, and cockpit-panel purpose |
| R03 | [TA-Lib Momentum and Statistical Functions](https://ta-lib.github.io/ta-lib-python/func_groups/momentum_indicators.html) |
| R04 | [TradingView — Exponential Moving Average](https://www.tradingview.com/support/solutions/43000592270-exponential-moving-average/) |
| R05 | [TradingView — Directional Movement (DMI)](https://www.tradingview.com/support/solutions/43000502250-directional-movement-dmi/) and [ADX](https://www.tradingview.com/support/solutions/43000589099-average-directional-index-adx/) |
| R06 | [TradingView — Aroon Oscillator](https://www.tradingview.com/support/solutions/43000773004-aroon-oscillator/) |
| R07 | [TradingView — MACD](https://www.tradingview.com/support/solutions/43000502344-moving-average-convergence-divergence-macd-indicator/) |
| R08 | [TradingView — Supertrend](https://www.tradingview.com/support/solutions/43000634738-supertrend/) |
| R09 | [TradingView — ATR](https://www.tradingview.com/support/solutions/43000501823-average-true-range-atr/) and [ATR%](https://www.tradingview.com/support/solutions/43000734653-how-are-adr-and-atr-calculated/) |
| R10 | [TradingView — Choppiness Index](https://www.tradingview.com/support/solutions/43000501980-choppiness-index-chop/) |
| R11 | [TradingView — Donchian Channels](https://www.tradingview.com/support/solutions/43000502253-donchian-channels-dc/) |
| R12 | [TradingView — Pivot Points Standard](https://www.tradingview.com/support/solutions/43000521824-pivot-points-standard/) |
| R13 | [TradingView — VWAP](https://www.tradingview.com/support/solutions/43000502018-volume-weighted-average-price-vwap/) and [Anchored VWAP](https://www.tradingview.com/support/solutions/43000669764-anchored-vwap-drawing-tool/) |
| R14 | [TradingView — Volume Profile Basic Concepts](https://www.tradingview.com/support/solutions/43000502040-volume-profile-indicators-basic-concepts/) |
| R15 | [Hurst (1951), Long-Term Storage Capacity of Reservoirs](https://doi.org/10.1061/TACEAT.0006518) |
| R16 | [Amihud (2002), Illiquidity and Stock Returns](https://doi.org/10.1016/S1386-4181(01)00024-6) |
| R17 | [Kyle (1985), Continuous Auctions and Insider Trading](https://www.jstor.org/stable/1913210) |
| R18 | [Cont, Kukanov, and Stoikov — The Price Impact of Order Book Events](https://arxiv.org/abs/1011.6402) |
| R19 | [Stoikov — The Micro-Price: A High Frequency Estimator of Future Prices](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2970694) |
| R20 | [Parkinson (1980), Extreme Value Method](https://doi.org/10.1086/296071) |
| R21 | [Garman and Klass (1980), Security Price Volatilities](https://doi.org/10.1086/296072) |
| R22 | [Rogers and Satchell (1991), Estimating Variance From High, Low and Closing Prices](https://doi.org/10.1214/aoap/1177005835) |
| R23 | [RiskMetrics Technical Document](https://www.msci.com/documents/10199/5915b101-4206-4ba0-aee2-3449d5c7e95a) |
| R24 | [TradingView — Bollinger BandWidth](https://www.tradingview.com/support/solutions/43000501972-bollinger-bandwidth-bbw/) and [Bollinger Bands](https://www.tradingview.com/support/solutions/43000501840-bollinger-bands-bb/) |
| R25 | [Lo, Mamaysky, and Wang (2000), Foundations of Technical Analysis](https://doi.org/10.1111/0022-1082.00265) |
| R26 | [TA-Lib Pattern Recognition Functions](https://ta-lib.github.io/ta-lib-python/func_groups/pattern_recognition.html) |
| R27 | [TradingView — Pivot Points High/Low](https://www.tradingview.com/support/solutions/43000589195-pivot-points-high-low/) and [Zig Zag](https://www.tradingview.com/support/solutions/43000591664-zig-zag/) |
| R28 | [TradingView — Price Volume Trend](https://www.tradingview.com/support/solutions/43000502345-price-volume-trend-pvt/) |
| R29 | [TA-Lib Volatility Functions](https://ta-lib.github.io/ta-lib-python/func_groups/volatility_indicators.html) |

---

# 20. Final Ownership Summary

```text
volatility/ owns dispersion and range.
trend/ owns direction and trend strength.
structure/ owns levels.
liquidity/ owns cost and capacity.
order_flow/ owns signed pressure.
market_speed/ composes how fast activity is evolving.
regime/ classifies the combined state.
patterns/ publishes bounded formation evidence.
snapshots/ publishes all outputs safely.

None of them approves a trade.
```

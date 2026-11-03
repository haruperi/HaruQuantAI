# Indicators — building block catalog

> Reference enumeration of every built-in **Indicator** building block (52 families, ~400 blocks)
> shipped under `Snippets/SQ/Blocks/Indicators/`. This is a lookup table; for the general
> building-block model (how snippets become UI blocks, `@BuildingBlock`/`@Parameter`/`@Output`
> annotations) see [README.md](README.md).

## How this file is organized

Each indicator lives in its own folder ("family"). A family almost always has one **base
indicator** class (extends `IndicatorBlock`, does the actual calculation, appears standalone on
the chart) plus a handful of **derived signal** classes (extend `ConditionBlock`, e.g. crosses
above/below a level, is rising/falling, is above/below another line) that internally call the
base indicator and turn one of its output series into a `true`/`false` condition usable in
entry/exit rules. A few families have more than one base indicator (e.g. separate `Highest` and
`Lowest`), and a few have none (they're built entirely on another family's outputs, e.g.
`DirectionalIndex` reuses ADX's `+DI`/`-DI`). Below: one `##` section per family, each with the
base indicator's display name and help text, a parameter table for its family-specific numeric
parameters (generic boilerplate params — `Input`/`Chart`/`Shift` — are omitted), and a list of the
derived signal blocks in that family by their UI display name.

## ADX

**(ADX) Average Directional Movement Index** — `ADX(@Chart@Period, Line)[Shift]`. Also exposes
`+DI`/`-DI` output lines, reused by the `DirectionalIndex` family below.

| Parameter | Default | Min | Max | Step |
|-----------|---------|-----|-----|------|
| Period | 14 | 2 | 10000 | 1 |

Derived: ADX is rising, ADX is falling, ADX is higher than Level, ADX is lower than Level, ADX
crosses above Level, ADX crosses below Level, ADX changes direction upwards, ADX changes direction
downwards.

## ATR

**(ATR) Average True Range** — `ATR(@Chart@Period)[Shift]`.

| Parameter | Default | Min | Max | Step |
|-----------|---------|-----|-----|------|
| Period | 14 | 2 | 10000 | 1 |

Derived: ATR is rising, ATR is falling, ATR is higher than Level, ATR is lower than Level, ATR
crosses above Level, ATR crosses below Level, ATR changes direction upwards, ATR changes direction
downwards.

## AnchoredVWAP

**(AVWAP) Anchored VWAP** — `AnchoredVWAP(@Chart@SessionType,StdDevMult).Line[Shift]`. Anchored
VWAP with standard deviation bands; resets at session start (Day/Week/Month). Outputs `VWAP`,
`Upper`, `Lower`.

| Parameter | Default | Min | Max | Step |
|-----------|---------|-----|-----|------|
| SessionType (Daily=1/Weekly=2/Monthly=3) | 1 | 1 | 3 | — |
| StdDevMult | 1.0 | 0.5 | 4.0 | 0.1 |

Derived: Faster Anchored VWAP is below Slower Anchored VWAP, Faster Anchored VWAP is above Slower
Anchored VWAP, Close crosses below Upper Band, Close crosses below Lower Band, Close crosses above
Upper Band, Close crosses above Lower Band, Close is below Lower Band, Anchored VWAP is falling,
Close is below Anchored VWAP, Close is above Anchored VWAP, Close is above Upper Band, Anchored
VWAP is rising.

## Aroon

**(ARO) Aroon** — `Aroon(@Chart@Period).Line[Shift]`. Outputs `Up`/`Down`.

| Parameter | Default | Min | Max | Step |
|-----------|---------|-----|-----|------|
| Period | 14 | 0 | 1000 | 1 |

Derived: Aroon Up falls from top, Aroon Down falls from top, Aroon Up crosses below Aroon Down,
Aroon Up crosses above Aroon Down, Aroon Up rises from bottom, Aroon Down rises from bottom.

## AvgVolume

**(AV) Average Volume** — `AV(@Chart@Period)[Shift]`. SMA of the raw Volume series.

| Parameter | Default | Min | Max | Step |
|-----------|---------|-----|-----|------|
| Period | 14 | 2 | 10000 | 1 |

Derived: (VOL) Volume is rising, (VOL) Volume is falling (both on raw, unaveraged Volume),
Average Volume is rising, Average Volume is falling (on the AV(Period) average).

## AwesomeOscillator

**(AWO) Awesome Oscillator** — `AwesomeOscillator(@Chart@)[Shift]`. Fixed 5-period SMA minus
34-period SMA of median price; no configurable period.

Derived: Awesome Oscillator is rising, is falling, is lower than Level, is higher than Level,
crosses above Level, crosses below Level, changes direction upwards, changes direction downwards.

## BarRange

No single base indicator — this family bundles several independent bar-range measures, each its
own building block (no derived ConditionBlock signals).

| Block | Display | Key parameter(s) |
|-------|---------|-------------------|
| (BR) BarRange | `BarRange(@Chart@)[Shift]` | none (current bar High − Low) |
| Biggest Range | `BiggestRange(@Chart@Period)[Shift]` | Period (default 14) — largest High−Low over the period |
| Smallest Range | `SmallestRange(@Chart@Period)[Shift]` | Period (default 14) — smallest High−Low over the period |
| Highest in range | `HighestInRange(@Chart@TimeFrom, TimeTo)[Shift]` | TimeFrom/TimeTo (HHMM, default 0, min 0, max 2359, step 30) — highest High within a daily time window |
| Lowest in range | `LowestInRange(@Chart@TimeFrom, TimeTo)[Shift]` | TimeFrom/TimeTo (HHMM, default 0, min 0, max 2359, step 30) — lowest Low within a daily time window |
| (FP) Fixed pips | `FixedPips(Value pips)` | Value (default 50, min 1, max 9999999, step 5) — a constant price-range expressed in pips |

## BearsPower

**(BP) Bears Power** — `BearsPower(@Chart@Period, ComputedFrom)[Shift]`. Low minus an EMA of the
chosen price series.

| Parameter | Default | Min | Max | Step |
|-----------|---------|-----|-----|------|
| Period | 14 | 2 | 10000 | 1 |

Derived: Bears Power changes direction downwards, Bears Power is rising, Bears Power is lower than
Level, Bears Power crosses above Level, Bears Power crosses below Level, Bears Power is falling,
Bears Power changes direction upwards, Bears Power is higher than Level.

## BollingerBands

**(BB) Bollinger Bands** — `BollingerBands(@Chart@Period, Deviation).Line[Shift]`. Outputs
`Upper`/`Lower` bands (SMA ± Deviation × StdDev).

| Parameter | Default | Min | Max | Step |
|-----------|---------|-----|-----|------|
| Period | 20 | 2 | 10000 | 1 |
| Deviation | 2 | 0.01 | 10 | 0.01 |

Derived: (BBWR) BB Width Ratio and (BBR) BB Range (auxiliary band-width/range indicators built on
the same Period/Deviation), Upper band is rising, Upper band is falling, Lower band is rising,
Lower band is falling, Bar closes above Upper band, Bar closes above Lower band, Bar closes below
Upper band, Bar closes below Lower band, Bar opens above Upper band, Bar opens above Lower band,
Bar opens below Upper band, Bar opens below Lower band, Bar opens above Upper band after opened
below, Bar opens above Lower band after opened below, Bar opens below Upper band after opened
above, Bar opens below Lower band after opened above.

## BullsPower

**(BUP) Bulls Power** — `BullsPower(@Chart@Period, ComputedFrom)[Shift]`. High minus an EMA of the
chosen price series (opposite of Bears Power).

| Parameter | Default | Min | Max | Step |
|-----------|---------|-----|-----|------|
| Period | 14 | 2 | 10000 | 1 |

Derived: Bulls Power is rising, Bulls Power is lower than Level, Bulls Power is higher than Level,
Bulls Power is falling, Bulls Power crosses above Level, Bulls Power crosses below Level, Bulls
Power changes direction upwards, Bulls Power changes direction downwards.

## CCI

**(CCI) Commodity Channel Index** — `CCI(@Chart@Period)[Shift]`. Commodity channel index.

| Parameter | Default | Min | Max | Step |
|-----------|---------|-----|-----|------|
| Period | 14 | 2 | 10000 | 1 |

Derived: CCI crosses above Level, CCI crosses below Level, CCI changes direction upwards, CCI
changes direction downwards, CCI is rising, CCI is falling, CCI is higher than Level, CCI is lower
than Level, plus a family of Woodies CCI System signals: (WZU) WoodiesZLRUP, (WZD) WoodiesZLRDown,
(WVU) Woodies Vegas Trade UP, (WVD) Woodies Vegas Trade Down, (WTD) Woodies Trend Down, (WTU)
WoodiesTrendUP, (WFU) Woodies Famir UP, (WFD) Woodies Famir Down, (ZBU) CCI Zero Line Break UP,
(ZBD) CCI Zero Line Break Down (all parameterized by CCI Period, and most by a Factor).

## DeMarker

**(DE) DeMarker** — `DeMarker(@Chart@Period)[Shift]`. DeMarker.

| Parameter | Default | Min | Max | Step |
|-----------|---------|-----|-----|------|
| Period | 14 | 2 | 10000 | 1 |

Derived: DeMarker changes direction downwards, DeMarker changes direction upwards, DeMarker is
rising, DeMarker crosses below Level, DeMarker is falling, DeMarker is higher than Level, DeMarker
crosses above Level, DeMarker is lower than Level.

## DirectionalIndex

No base indicator of its own — every block here is a `ConditionBlock` (`mainIndicator="ADX"`) that
reads the `+DI`/`-DI` output lines already computed by the **ADX** family above.

Derived: DI+ is rising, DI- is rising, DI+ is lower than DI-, DI- is falling, DI+ is higher than
DI-, DI- changes direction upwards, DI- changes direction downwards, DI+ is falling, DI+ crosses
above DI-, DI+ changes direction downwards, DI+ crosses below DI-, DI+ changes direction upwards.

## Fibo

**(FIB) Fibo** — `Fibo(@Chart@)`. Choose range of Fibo indicator; a Fibonacci retracement level
computed from the prior day/week/month high-low or open-close range. Single block, no derived
signals.

| Parameter | Default | Min | Max | Step |
|-----------|---------|-----|-----|------|
| FiboRange (High-Low or Open-Close, prev day/week/month — selection) | 1 | — | — | — |
| FiboLevel (selection: -423.6 … 423.6) | 76.4 | — | — | — |

## Fractal

**Fractal** — `Fractal(@Chart@Fractal)[Shift]`. Outputs `Up`/`Down` fractal price points using a
3-bar or 5-bar window.

| Parameter | Default | Min | Max | Step |
|-----------|---------|-----|-----|------|
| Fractal (3-bar or 5-bar — selection) | 3 | — | — | — |

Derived: Is Bullish Fractal, Is Bearish Fractal.

## GannHiLo

**(GHL) GannHiLo** — `GannHiLo(@Chart@Period)[Shift]`. GannHiLo help text (trend-following
high/low activator line).

| Parameter | Default | Min | Max | Step |
|-----------|---------|-----|-----|------|
| Period | 10 | 2 | 1000 | 1 |

Derived: (GHU) GannHiLo is in UP Trend, (GHD) GannHiLo is in Down Trend.

## HeikenAshi

**(HA) Heiken Ashi** — `Heiken Ashi(@Chart@)[Shift]`. Outputs `HAOpen`/`HAClose` smoothed
candle values. Single block, no parameters or derived signals (marked `@IgnoreInBuilder`).

## HighestLowest

Two independent base indicators, each with a companion "index" variant (bar-shift of the
extreme, `@IgnoreInBuilder`, used internally) and their own derived signal blocks.

| Block | Display | Parameters |
|-------|---------|------------|
| Highest | `Highest(@Chart@Period)[Shift]` | Period (default 14) |
| (HI) Highest index | `HighestIndex(@Chart@Period)[Shift]` | Period (default 14, min 0, max 10000, step 1) |
| Lowest | `Lowest(@Chart@Period)[Shift]` | Period (default 14) |
| (LI) Lowest index | `LowestIndex(@Chart@Period)[Shift]` | Period (default 14, min 0, max 10000, step 1) |

Derived: Bar opens below Lowest after opened above, Bar opens below Highest after opened above,
Bar opens above Lowest after opened below, Bar opens above Highest after opened below.

## HullMovingAverage

**(HMA) Hull Moving Average** — `HMA(@Chart@Period)[Shift]`. HMA is an adaptive MA (built from
fast/slow LWMAs of the period and its square root).

| Parameter | Default | Min | Max | Step |
|-----------|---------|-----|-----|------|
| Period | 10 | 2 | 1000 | 1 |

Derived: HMA is rising, HMA is falling, HMA changes direction upwards, HMA changes direction
downwards, (FBS) Fast HMA Is Below Slow HMA, (FAS) Fast HMA Is Above Slow HMA.

## Ichimoku

**Ichimoku** — `Ichimoku(@Chart@TenkanPeriod,KijunPeriod,SenkouPeriod,Line)[Shift]`. No `name=`/
`@Help` on the base block; outputs `TenkanSen`, `KijunSen`, `SenkouSpanA`, `SenkouSpanB`.

| Parameter | Default | Min | Max | Step |
|-----------|---------|-----|-----|------|
| TenkanPeriod (Tenkan) | 9 | — | — | — |
| KijunPeriod (Kijun) | 26 | — | — | — |
| SenkouPeriod (Senkou) | 52 | — | — | — |

Derived: (Ichimoku) TenkanSen crosses KijunSen bullish, (Ichimoku) TenkanSen crosses KijunSen
bearish, (Ichimoku) Senkou Span cross bullish, (Ichimoku) Senkou Span cross bearish, (Ichimoku)
Kumo breakout bullish, (Ichimoku) Kumo breakout bearish, (Ichimoku) price crosses KijunSen
bullish, (Ichimoku) price crosses KijunSen bearish.

## KAMA

**(KAMA) Kaufman's Adaptive Moving Average** — `Kaufman's Adaptive Moving Average(@Chart@ERPeriod,
ShortPeriod,LongPeriod)[Shift]`. KAMA is another smoothed MA whose speed adapts to Kaufman's
Efficiency Ratio.

| Parameter | Default | Min | Max | Step |
|-----------|---------|-----|-----|------|
| ERPeriod | 10 | 2 | 1000 | 1 |
| ShortPeriod | 2 | 2 | 500 | 1 |
| LongPeriod | 30 | 2 | 500 | 1 |

Derived: (KAR) KAMA is rising, (KAF) KAMA is falling, (FASK) Fast KAMA is above Slow KAMA, (CAK)
Bar crosses above KAMA, (CBK) Bar crosses below KAMA, (FBSK) Fast KAMA is below Slow KAMA.

## KaufmanEfficiencyRatio

**(KER) Kaufman Efficiency Ratio** — `Kaufman Efficiency Ratio(@Chart@Period)[Shift]`. Kaufman
Efficiency Ratio (directional change over total volatility, 0–1).

| Parameter | Default | Min | Max | Step |
|-----------|---------|-----|-----|------|
| Period | 10 | 2 | 1000 | 1 |

Derived: Kaufman Efficiency Ratio is lower than Level, Kaufman Efficiency Ratio is higher than
Level.

## KeltnerChannel

**(KC) Keltner Channel** — `Keltner Channel(@Chart@Period, Deviation).Line[Shift]`. Outputs
`Upper`/`Lower` bands (SMA of typical price ± Deviation × average bar range).

| Parameter | Default | Min | Max | Step |
|-----------|---------|-----|-----|------|
| Period | 20 | 2 | 10000 | 1 |
| Deviation | 1.5 | 0.01 | 10 | 0.01 |

Derived: Bar opens above Lower band, Bar closes below Upper band, Upper band is rising, Bar closes
below Lower band, Upper band is falling, Bar closes above Upper band, Bar closes above Lower band,
Lower band is rising, Bar opens below Lower band, Bar opens above Upper band, Lower band is
falling, Bar opens below Upper band after opened above, Bar opens above Upper band after opened
below, Bar opens above Lower band after opened below, Bar opens below Upper band, Bar opens below
Lower band after opened above.

## LaguerreRSI

**(LRSI) Laguerre RSI** — `Laguerre RSI(@Chart@Gamma)[Shift]`. LaguerreRSI help text (4-stage
Laguerre filter RSI, 0–1).

| Parameter | Default | Min | Max | Step |
|-----------|---------|-----|-----|------|
| Gamma | 0.5 | 0.0 | 1 | 0.01 |

Derived: (LRSIR) Laguerre RSI is rising, (LRSID) Laguerre RSI crosses below Level, (LRSIF) Laguerre
RSI is falling, (LRSICU) Laguerre RSI changes direction upwards, (LRSIU) Laguerre RSI crosses above
Level, (LRSICD) Laguerre RSI changes direction downwards.

## LinReg

**(LinReg) Linear Regression** — `LinReg(@Chart@Period)[Shift]`. Endpoint of a linear-regression
line fit over the period.

| Parameter | Default | Min | Max | Step |
|-----------|---------|-----|-----|------|
| Period | 14 | — | — | — |

Derived: LinReg is rising, LinReg is falling, Bar opens above LinReg, Bar opens below LinReg after
opened above, Bar closes above LinReg, Bar closes below LinReg, Bar opens below LinReg, Bar opens
above LinReg after opened below.

## MACD

**(MACD) MACD** — `MACD(@Chart@Fast, Slow, Smooth).Line[Shift]`. Outputs `Main` (Fast EMA − Slow
EMA) and `Signal` (SMA of Main).

| Parameter | Default | Min | Max | Step |
|-----------|---------|-----|-----|------|
| Fast | 12 | — | — | — |
| Slow | 26 | — | — | — |
| Smooth | 9 | — | — | — |

Derived: MACD Main line changes direction downwards, MACD Main line changes direction upwards,
MACD Main line crosses above Level, MACD Main line crosses above Signal, MACD Main line crosses
above 0, MACD Main line crosses below Level, MACD Main line is higher than Level, MACD Main line
is higher than 0, MACD Main line is lower than Signal, MACD Main line is rising, MACD Signal line
is rising, MACD Main line is higher than Signal, MACD Main line is falling, MACD Main line is
lower than Level, MACD Main line crosses below Signal, MACD Signal line is falling, MACD Main line
is lower than 0, MACD Main line crosses below 0.

## MTATR

**(MTATR) Average True Range** — `MTATR(@Chart@Period)[Shift]`. MetaTrader-style ATR
implementation (simple average of true range over the period, vs. the Wilder-smoothed **ATR**
family above). Single block, no derived signals; used internally by SuperTrend, Vortex and
SRPercentRank.

| Parameter | Default | Min | Max | Step |
|-----------|---------|-----|-----|------|
| Period | 14 | 2 | 10000 | 1 |

## MTKeltnerChannel

**(MTKC) MT Keltner Channel** — `MT Keltner Channel(@Chart@Period, Deviation).Line[Shift]`.
MetaTrader-style Keltner Channel variant (uses Close instead of Typical price for the midline).
Outputs `Upper`/`Lower`. Single block, no derived signals.

| Parameter | Default | Min | Max | Step |
|-----------|---------|-----|-----|------|
| Period | 20 | 2 | 10000 | 1 |
| Deviation | 1.5 | 0.01 | 10 | 0.01 |

## Momentum

**(MO) Momentum** — `Momentum(@Chart@Period)[Shift]`. Ratio of current price to price N bars ago,
× 100.

| Parameter | Default | Min | Max | Step |
|-----------|---------|-----|-----|------|
| Period | 14 | — | — | — |

Derived: Momentum is rising, Momentum changes direction upwards, Momentum changes direction
downwards, Momentum is higher than Level, Momentum is falling, Momentum is lower than Level,
Momentum crosses below Level, Momentum crosses above Level.

## MovingAverage

Six base indicators share this family: a generic **(MA) Moving Average** with a selectable method,
plus four fixed-method variants and TEMA.

| Block | Display | Period |
|-------|---------|--------|
| (MA) Moving Average | `MA(@Chart@Period, MAMethod)[Shift]` | default 14 (Method: Simple/Exponential/Smoothed/Linear weighted) |
| (SMA) Simple Moving Average | `SMA(@Chart@Period)[Shift]` | default 14 |
| (EMA) Exponential Moving Average | `EMA(@Chart@Period)[Shift]` | default 14 |
| (LWMA) Linear Weighted Moving Average | `LWMA(@Chart@Period)[Shift]` | default 14 |
| (SMMA) Smoothed Moving Average | `SMMA(@Chart@Period)[Shift]` | default 14 |
| (TEMA) Triple Exponential Moving Average | `TEMA(@Chart@Period)[Shift]` | default 14 |

Derived (parameterized by a `#Type#` selector spanning all MA methods above): Bar closes below
Moving Average, Bar closes above Moving Average, Moving Average is falling, Bar opens above Moving
Average after opened below, Bar opens above Moving Average, Bar opens below Moving Average, Bar
opens below Moving Average after opened above, Moving Average is rising.

## OSMA

**(OSMA) Moving Average Of Oscillator** — `OSMA(@Chart@FastEMA, SlowEMA, SignalPeriod)[Shift]`.
MACD histogram (Main − Signal).

| Parameter | Default | Min | Max | Step |
|-----------|---------|-----|-----|------|
| FastEMA | 12 | — | — | — |
| SlowEMA | 26 | — | — | — |
| SignalPeriod | 9 | — | — | — |

Derived: OSMA is rising, OSMA is lower than 0, OSMA crosses below 0, OSMA is higher than 0, OSMA
changes direction upwards, OSMA is falling, OSMA changes direction downwards, OSMA crosses above 0.

## Other

Not a real building block family — `DataLoggingIndy` has no `@BuildingBlock` annotation, extends
the internal `Indicator` base class directly, and is not exposed in the block palette. It writes
each bar's OHLCV values to `tests/tmp/INDICATOR_ohlcv.csv` for internal test/debug purposes only.

## ParabolicSAR

**(PSAR) Parabolic SAR** — `ParabolicSAR(@Chart@Step, Maximum)[Shift]`. Trend-following stop-and-
reverse price line.

| Parameter | Default | Min | Max | Step |
|-----------|---------|-----|-----|------|
| Step | 0.02 | 0.01 | 0.6 | 0.01 |
| Maximum | 0.2 | 0.01 | 1 | 0.1 |

Derived: Price is below ParabolicSAR(Step, Maximum)[Shift], Price is above ParabolicSAR(Step,
Maximum)[Shift].

## Pivots

**(Pivots) Pivots** — `Pivots(@Chart@StartHour:StartMinute).Line[Shift]`. Pivots — classic
Pivot Point / R1-R3 / S1-S3 levels computed from the prior session's H/L/C. Single block, no
derived signals.

| Parameter | Default | Min | Max | Step |
|-----------|---------|-----|-----|------|
| StartHour | 0 | 0 | 23 | 1 |
| StartMinute | 0 | 0 | 59 | 1 |

## QQE

**(QQE) Quantitative Qualitative Estimation** — `QQE(@Chart@RSIPeriod)[Shift]`. Smoothed-RSI
trend indicator with an ATR-of-RSI trailing level. Outputs `Value1` (smoothed RSI) and `Value2`
(trailing level).

| Parameter | Default | Min | Max | Step |
|-----------|---------|-----|-----|------|
| RSIPeriod | 14 | 2 | 10000 | 1 |
| sF | 5 | 2 | 650 | 1 |
| wF | 4.236 | 0.1 | 100 | — |

Derived: QQE Value2 line is rising, QQE Value2 line is falling, QQE Value1 line is rising, QQE
Value1 line is lower than Value2, QQE Value1 line is higher than Level, QQE Value1 line crosses
above Level, QQE Value1 line crosses below Level, QQE Value1 line is higher than Value2, QQE
Value1 line changes direction upwards, QQE Value1 line is lower than Level, QQE Value1 line is
falling, QQE Value1 line crosses above Value2, QQE Value1 line crosses below Value2, QQE Value1
line changes direction downwards.

## ROC

**(ROC) ROC** — `ROC(@Chart@Period)[Shift]`. Price rate of change.

| Parameter | Default | Min | Max | Step |
|-----------|---------|-----|-----|------|
| Period | 5 | 2 | 1000 | 1 |

Derived: (ROCR) ROC is rising, (ROCAL) ROC is above Level, (ROCCBL) ROC crosses below Level,
(ROCBL) ROC is below Level, (ROCF) ROC is falling, (ROCCAL) ROC crosses above Level.

## RSI

**(RSI) Relative Strength Index** — `RSI(@Chart@Period)[Shift]`.

| Parameter | Default | Min | Max | Step |
|-----------|---------|-----|-----|------|
| Period | 14 | 2 | 10000 | 1 |

Derived: RSI is rising, RSI crosses above Level, RSI changes direction upwards, RSI is lower than
Level, RSI crosses below Level, RSI is higher than Level, RSI changes direction downwards, RSI is
falling.

## Reflex

**(RFX) Reflex** — `Reflex(@Chart@Period)[Shift]`. Reflex help text (Ehlers' Reflex indicator, a
low-lag cycle/trend oscillator).

| Parameter | Default | Min | Max | Step |
|-----------|---------|-----|-----|------|
| Period | 24 | 2 | 1000 | 1 |

Derived: (RFR) Reflex is Rising, (RFF) Reflex is Falling, (RFXU) Reflex Changes Direction UP,
(RFXD) Reflex Changes Direction Down, (RCU) Fast Reflex Crosses UP Slow Reflex, (RCD) Fast Reflex
Crosses Down Slow Reflex.

## SRPercentRank

**(SRPC) SRPercRank** — `SRPercRank(@Chart@Mode,Length,ATRPeriod)[Shift]`. Identifies
Support/Resistance levels and breakout areas by ranking how often price stayed within past bars'
range (optionally widened by ATR).

| Parameter | Default | Min | Max | Step |
|-----------|---------|-----|-----|------|
| Mode (Basic=1/ATR=2) | 2 | — | — | — |
| Length | 120 | 2 | 500 | 1 |
| ATRPeriod | 12 | 5 | 120 | 1 |

Derived: (PRBLX) SR Percent Rank is below Level for X Bars, (PRAL) SR Percent Rank is above Level,
(PRALX) SR Percent Rank is above Level for X Bars, (PRBL) SR Percent Rank is below Level.

## SchaffTrendCycle

**(SCHTC) Schaff Trend Cycle** — `Schaff Trend Cycle(@Chart@StochPeriod,FastPeriod,SlowPeriod)
[Shift]`. Schaff TrendCycle help text (stochastic-of-MACD cycle oscillator, 0–100).

| Parameter | Default | Min | Max | Step |
|-----------|---------|-----|-----|------|
| StochPeriod | 10 | 2 | 480 | 1 |
| FastPeriod | 20 | 2 | 480 | 1 |
| SlowPeriod | 50 | 2 | 480 | 1 |

Derived: (STCCBL) Schaff TrendCycle crosses below Level, (STCAL) Schaff TrendCycle is above Level,
(STCCAL) Schaff TrendCycle crosses above Level, (STCBL) Schaff TrendCycle is below Level.

## StdDev

**(STDDEV) Standard Deviation** — `StdDev(@Chart@Period)[Shift]`.

| Parameter | Default | Min | Max | Step |
|-----------|---------|-----|-----|------|
| Period | 20 | 2 | 10000 | 1 |

Derived: StdDev is rising, StdDev is lower than Level, StdDev is higher than Level, StdDev is
falling, StdDev crosses above Level, StdDev crosses below Level, StdDev changes direction upwards,
StdDev changes direction downwards.

## Stochastic

**(STOCH) Stochastic** — `Stoch(@Chart@KPeriod, DPeriod, Slowing).Line[Shift]`. Outputs
`Fast %K`/`Slow %D`.

| Parameter | Default | Min | Max | Step |
|-----------|---------|-----|-----|------|
| %K Period | 9 | 2 | 10000 | 1 |
| %D Period | 3 | 2 | 10000 | 1 |
| Slowing | 3 | 2 | 10000 | 1 |

Derived: Stochastic.Fast %K is lower than Slow %D, Stochastic.Slow %D is rising, Stochastic.Fast
%K crosses above Level, Stochastic.Slow %D is lower than Level, Stochastic.Fast %K crosses below
Level, Stochastic.Slow %D is higher than Level, Stochastic.Slow %D is falling, Stochastic.Slow %D
crosses below Level, Stochastic.Slow %D changes direction upwards, Stochastic.Slow %D crosses
above Level, Stochastic.Fast %K is higher than Slow %D, Stochastic.Slow %D changes direction
downwards.

## SuperTrend

**(ST) SuperTrend** — `SuperTrend(@Chart@Mode,ATRPeriod,ATRMult)[Shift]`. SuperTrend help text
(ATR-band trend-flip line).

| Parameter | Default | Min | Max | Step |
|-----------|---------|-----|-----|------|
| Mode (Basic=1) | 1 | — | — | — |
| ATRPeriod | 24 | 2 | 240 | 1 |
| ATRMult | 3 | 0.5 | 10 | 0.1 |

Derived: (STU) SuperTrend UP Trend, (BCAST) Bar closes below SuperTrend, (STR) Super Trend is in
Range, (BCAST) Bar closes above SuperTrend, (STD) SuperTrend Down Trend.

## TPOProfile

**(TPO) Market Profile** — `TPO_Letters(SessionType,ProfileRows,ValueAreaPct).Line[Shift]`. TPO
(Market Profile). Outputs POC/VAH/VAL based on Time Price Opportunities, plus poor high/low,
excess, single-print, ledge, IB, VPOC/VVAH/VVAL, bull/bear POC and volume outputs. Single block,
no derived signals.

| Parameter | Default | Min | Max | Step |
|-----------|---------|-----|-----|------|
| SessionType (Previous/Actual Day/Week/Month/Year — selection) | 1 | 1 | 8 | — |
| ProfileRows | 150 | 10 | 500 | 10 |
| BinSizeMode (Range-Based=1/Fixed Tick Size=2) | 2 | — | — | — |
| TicksPerBin | 1 | 1 | 1000 | 1 |
| ValueAreaPct | 70 | 30 | 95 | 5 |

## Trend

No shared base indicator — two unrelated, opposite `ConditionBlock`s that each classify the
overall trend as up or down using price vs. SMA(200) (currently the only implemented `Method`).

| Block | Display | Parameter |
|-------|---------|-----------|
| Is Uptrend | `IsUptrend(@Chart@Method)` | Method (selection: Price above SMA200=0) |
| Is Downtrend | `IsDowntrend(@Chart@Method)` | Method (selection: Price below SMA200=0) |

## TrueRange

**(TR) TrueRange** — `TrueRange[@Chart@Shift]`. Bar's true range (max of High−Low, |High−PrevClose|,
|Low−PrevClose|), unsmoothed. Single block, no parameters or derived signals.

## UlcerIndex

**(UI) Ulcer Index** — `Ulcer Index(@Chart@Mode,Period)[Shift]`. Ulcer Index indicator — RMS of
percentage drawdown from the rolling high (or, in Down mode, from the rolling low) over the
period.

| Parameter | Default | Min | Max | Step |
|-----------|---------|-----|-----|------|
| Mode (UP UI=1/Down UI=2) | 1 | — | — | — |
| Period | 24 | 2 | 1000 | 1 |

Derived: (UIUR) Ulcer Index UP is rising, (UIDS) Ulcer Index Down Below Safe Level, (UIDR) Ulcer
Index Down is rising, (UIUS) Ulcer Index UP Below Safe Level.

## VWAP

**(VWAP) Volume Weighted Average Price - VWAP** — `Volume Weighted Average Price - VWAP
(@Chart@VWAPPeriod)[Shift]`. VWAP help text (rolling volume-weighted average price over a fixed
bar window, distinct from the session-anchored **AnchoredVWAP** family).

| Parameter | Default | Min | Max | Step |
|-----------|---------|-----|-----|------|
| VWAPPeriod | 10 | 2 | 480 | 1 |

Derived: (VWAPR) VWAP is rising, (VWAPF) VWAP is falling, (DVWAPD) Faster VWAP is below Slower
VWAP, (CBVWAP) Close is below VWAP, (DVWAPU) Faster VWAP is above Slower VWAP, (CAVWAP) Close is
above VWAP.

## VolumeProfile

**(VP) Volume Profile** — `VolumeProfile(SessionType,ProfileRows,ValueAreaPct).Line[Shift]`.
Volume Profile; outputs POC/VAH/VAL plus IB, HVN1-5/LVN1-5, VPOC/VVAH/VVAL, bull/bear POC, volume
totals and delta outputs. Two further base-indicator variants exist for custom session hours.

| Block | Display | Notable parameters |
|-------|---------|----------------------|
| (VP) Volume Profile | `VolumeProfile(SessionType,ProfileRows,ValueAreaPct).Line[Shift]` | SessionType (1–10, incl. Previous/Actual Day/Week/Month/Year/Swing, default 2); ProfileRows (default 150, min 10, max 500, step 10); ValueAreaPct (default 70, min 30, max 95, step 5) |
| (VP) Volume Profile Custom Hours | `VolumeProfileCH(SessionStartHours:SessionStartMinutes-SessionEndHours:SessionEndMinutes,ProfileRows,ValueAreaPct).Line[Shift]` | explicit daily session start/end hour:minute |
| (VP) Volume Profile Custom Hours MultiSession | `VolumeProfileCHMulti(ProfileRows,ValueAreaPct).Line[Shift]` | multi-session custom-hours variant |

Derived (regime/breakout signals built on Volume Profile outputs): (VP23) Value Shift Up (Bull
Regime), (VP24) Value Shift Down (Bear Regime), (VP21) Rising POC (Long Regime), (VP22) Falling
POC (Short Regime).

## Vortex

**(VRX ) Vortex** — `Vortex(@Chart@Period)[Shift]`. Outputs `VIPlusSumRge`/`VIMinusSumRge` (sums
of positive/negative directional movement over summed true range).

| Parameter | Default | Min | Max | Step |
|-----------|---------|-----|-----|------|
| Period | 12 | 2 | 1000 | 1 |

Derived: (VXU) Vortex is in Up Trend, (VXD) Vortex is In Down Trend, (VCU) Vortex Changes Trend
UP, (VCD) Vortex Changes Trend Down.

## WaveTrend

**(WAVT) WaveTrend** — `WaveTrend(@Chart@ChannelLength,AverageLength).Line[Shift]`. Outputs
`WT1`(Main)/`WT2`(Signal), a CCI-like smoothed oscillator.

| Parameter | Default | Min | Max | Step |
|-----------|---------|-----|-----|------|
| ChannelLength | 10 | 2 | 200 | 1 |
| AverageLength | 21 | 2 | 200 | 1 |

Derived: WaveTrend Main line changes direction downwards, WaveTrend Main line is falling,
WaveTrend Signal line is rising, WaveTrend Main line crosses below 0, WaveTrend Signal line is
falling, WaveTrend Main line crosses below Signal, WaveTrend Main line is rising, WaveTrend Main
line crosses below Level, WaveTrend Main line is lower than 0, WaveTrend Main line crosses above
0, WaveTrend Main line is lower than Signal, WaveTrend Main line is higher than 0, WaveTrend Main
line crosses above Signal, WaveTrend Main line is higher than Signal, WaveTrend Main line crosses
above Level, WaveTrend Main line changes direction upwards, WaveTrend Main line is lower than
Level, WaveTrend Main line is higher than Level.

## WilliamsPR

**(WILL%R) Williams Percent Range** — `Williams %R(@Chart@Period)[Shift]`. The Williams Percent
Range is a momentum indicator that is designed to identify overbought and oversold areas in a
nontrending market.

| Parameter | Default | Min | Max | Step |
|-----------|---------|-----|-----|------|
| Period | 14 | — | — | — |

Derived: Williams%R is rising, Williams%R crosses below Level, Williams%R is lower than Level,
Williams%R is falling, Williams%R is higher than Level, Williams%R changes direction upwards,
Williams%R crosses above Level, Williams%R changes direction downwards.

## Related

- General building-block model, snippet/annotation mechanics: [README.md](README.md)
- Comparison and crossover blocks commonly paired with these indicators: [comparisons.md](comparisons.md)
- Strategy-control blocks (position sizing, filters, exits) that consume indicator values: [strategy-control.md](strategy-control.md)

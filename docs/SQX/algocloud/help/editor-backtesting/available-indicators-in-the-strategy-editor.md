# Available indicators in the Strategy Editor

> Offline copy of the AlgoCloud help article (fetched 2026-08-07).

AlgoCloud's Strategy Editor uses the TA-Lib technical analysis library — the same library used in most professional trading platforms. That means you have access to the full standard TA-Lib indicator set when building entry and exit rules.

# Categories of indicators available

## Trend / overlap

SMA, EMA, WMA, DEMA, TEMA, KAMA, MAMA, T3, TRIMA — all standard moving averages. Plus MA envelopes, SAR (Parabolic).

## Momentum / oscillators

RSI, Stochastic (%K / %D / StochRSI / StochF), MACD (classic + ext + fix), CCI, Williams %R, ROC (ROC / ROCP / ROCR / ROCR100), MOM, TRIX, ULTOSC, Aroon (Aroon / AroonOsc), ADX / ADXR / DX, PLUS_DI / MINUS_DI, CMO, PPO, BOP, APO.

## Volatility

ATR, NATR, TRANGE (true range), Bollinger Bands, Standard Deviation, Variance.

## Volume

OBV, AD (Chaikin A/D Line), ADOSC (Chaikin A/D Oscillator), MFI.

## Cycle

HT_DCPERIOD, HT_DCPHASE, HT_PHASOR, HT_SINE, HT_TRENDMODE (Hilbert Transform family).

## Price transform / math

AVGPRICE, MEDPRICE, TYPPRICE, WCLPRICE, plus math operators (MAX, MIN, SUM, etc.) for building custom formulas.

## Pattern recognition

Full TA-Lib candlestick pattern set — Doji, Engulfing, Hammer, Morning Star, Three White Soldiers, and ~60 more.

For the full reference, see the TA-Lib function list.

# Indicators not in TA-Lib (and therefore not built-in)

TA-Lib does not include these indicators, so they are not in the Strategy Editor dropdown:

-

Keltner Channels — derivable as EMA ± multiplier × ATR using Variables + Formulas.

-

Donchian Channels — derivable as Highest(high, N) and Lowest(low, N).

-

TTM Squeeze — can be composed from Bollinger Bands + Keltner + momentum.

-

Heiken Ashi — a charting overlay; values can be computed in Variables but the Strategy Editor doesn't expose HA candles natively.

-

Dollar Volume — compose as Close × Volume in a Variable.

If you'd like one of these built in, email [email protected] — priority on the roadmap is based on demand.

# Custom indicators via Variables & Formulas

You can compose your own indicators by combining TA-Lib indicators with math operations (add, subtract, multiply, max, min, if/then). See Introduction to Strategy Editor.

# Momentum / trend following

**Idea:** a market already moving tends to keep moving. A momentum (trend-following) strategy
*buys strength and sells weakness* — enter in the direction of an established move, ride it,
and exit when the move exhausts. Works best on trending markets (commodities, crypto, FX in
regime); suffers whipsaws in ranges. Opposite temperament to
[mean reversion](mean-reversion.md).

## SQX building blocks that express it

| Family (grid name) | Typical momentum/trend signals |
|--------------------|--------------------------------|
| `MACD` | MACD Main line changes direction, crosses above/below Signal line |
| `Momentum` | Momentum crosses above Level, Momentum is rising |
| `ADX` Average Directional Index | ADX is higher than Level (trend strength filter), ADX is rising |
| Moving averages | Close crosses above MA, Faster MA is above Slower MA |
| `(AVWAP)` Anchored VWAP | Close is above Anchored VWAP, faster above slower |

`ADX` deserves emphasis: it is usually a **filter** (only trade when ADX > 20–25 says a trend
exists) combined with a directional entry from the other families.

## Recommended SQX setup

- **Build mode:** Genetic evolution.
- **Money management:** Fixed size while researching.
- **Exits:** trailing stop fits the style (let winners run); profit target wider than stop.
- **Cross checks:** Monte Carlo retest on; retest on additional markets is a natural fit —
  real trend edges tend to generalize across instruments.

Trend systems win rarely and lose often — a low win rate with large winners is normal here, so
judge them on Return/Drawdown over a long sample rather than on win percentage, and size them
for long losing streaks ([risk-and-position-sizing.md](risk-and-position-sizing.md)).

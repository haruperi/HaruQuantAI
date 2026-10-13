# Mean reversion

**Idea:** price stretched far from its recent average tends to snap back. A mean-reversion
strategy *sells strength and buys weakness* — enter when an oscillator says the market is
overbought/oversold or price pierces a volatility band, exit when price returns to the mean.
Works best on ranging markets (FX pairs, indices intraday); suffers in strong trends.

## SQX building blocks that express it

Signal-block families in the Builder **Signals** grid (names as shown in the grid):

| Family (grid name) | Typical mean-reversion signals |
|--------------------|--------------------------------|
| `RSI` Relative Strength Index | RSI is lower than Level (buy dip), RSI crosses below/above Level |
| `CCI` Commodity Channel Index | CCI crosses above/below Level (±100 extremes) |
| `(BB)` Bollinger Bands | Bar closes above/below Lower band, band cross-backs |
| `Stochastic` | %K in the oversold/overbought zone, %K crosses %D there |
| `Williams PR` Williams %R | WPR is lower/higher than Level |

Counter-indicated blocks: breakout channels (`Highest`/`Lowest`), `(MACD)`/`(MOM)` momentum
signals — enabling them dilutes the style. The usual move is to *enable* the families above
without force-disabling everything else, unless the user asks for a pure-style build.

## Recommended SQX setup

- **Build mode:** Genetic evolution — oscillator+band combinations form a big search space.
- **Money management:** Fixed size while researching (comparable results across candidates).
- **Exits:** keep Stop Loss required; mean reversion often uses tighter profit targets than
  stops (the edge is many small snap-backs).
- **Cross checks:** Monte Carlo retest on — mean-reversion edges are fragile to exact fills.

Because the style lives on precise fills, treat coarse test precision with suspicion here and
re-verify survivors at M1 or real-tick precision ([markets-and-costs.md](markets-and-costs.md),
[crosscheck-funnel.md](crosscheck-funnel.md)).

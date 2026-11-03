# Breakout

**Idea:** when price escapes a well-defined range (yesterday's high, an N-bar channel, a
volatility band), the escape often continues. A breakout strategy places entries *beyond* the
range boundary — classically with **stop orders** that trigger only if price reaches the level.
Several of the user's real projects are breakout projects (GBPJPY BREAKOUT, GOLD BREAKOUT,
NQ/EW FUTURES BREAKOUT), so this style matters in this install.

## SQX building blocks that express it

| Family (grid name) | Typical breakout signals |
|--------------------|--------------------------|
| `Highest Lowest` channel | Close crosses above Highest(N) of previous bars |
| `(KC)` Keltner Channel | Bar closes above/below the channel bands |
| `(BB)` Bollinger Bands | Bar closes above Upper band (volatility breakout — note the *same* band blocks serve mean reversion in the opposite direction) |
| `ATR` Average True Range | volatility filter — trade only when range is compressing/expanding |
| Bar/time blocks | session-open range breakouts (Bar Hour, Bar Day Of Week) |

**Order types matter more than elsewhere:** `(STOP) Enter at stop` is the canonical breakout
entry (the Order types grid in What to build).

## Recommended SQX setup

- **Build mode:** Genetic evolution (or Random for a quick scan).
- **Money management:** Fixed size while researching.
- **Exits:** Stop Loss required; trailing stop common (a breakout that works becomes a trend).
- **Cross checks:** Monte Carlo retest on — breakout fills are slippage-sensitive.

Breakouts are the style most flattered by an optimistic simulation: stop entries at bar extremes
are exactly where a coarse-precision backtest guesses in your favour, and where real slippage is
worst. Model costs pessimistically and re-verify at higher precision
([markets-and-costs.md](markets-and-costs.md)). False breakouts are also the norm rather than the
exception — expect a low win rate carried by a few large trends.

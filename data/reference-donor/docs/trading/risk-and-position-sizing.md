# Risk and position sizing

A strategy's *edge* decides whether you make money over many trades; **position sizing decides
whether you survive long enough to collect it**. The two are independent: the same entry/exit
logic can be a solid system at 0.5 % risk per trade and a blown account at 10 %. This page is
the trading side of the [Money management](../overview/settings/money-management.md) panel.

## Risk per trade

The standard unit of risk is *how much of the account you lose if the stop is hit*:

```
position size = (account × risk %) / (stop distance × value per point)
```

- **1–2 % per trade** is the conventional band for a discretionary or single-system trader;
  above ~5 % a normal losing streak becomes an account-ending event.
- The number that matters is not per trade but **per cluster of correlated trades**. Ten
  strategies that are all long EURUSD at the same time are one trade with ten tickets — this is
  why correlation caps in [portfolio construction](portfolio-construction.md) are a risk
  control, not a performance tweak.
- A strategy without a Stop Loss has *undefined* risk per trade and cannot be sized this way.
  That is the main practical reason SQX builds normally keep **Stop Loss required**.

## Drawdown is the real constraint

Losing streaks are longer than intuition suggests: with a 45 % win rate, a run of 10 losses in
1000 trades is unremarkable. Two consequences worth internalising:

| Drawdown | Gain needed to recover |
|---|---|
| 10 % | 11 % |
| 25 % | 33 % |
| 50 % | 100 % |
| 75 % | 300 % |

Recovery is non-linear, so **max drawdown — not net profit — is the number to design against**.
That is why the standard fitness measure in SQX is a *ratio* (Return/Drawdown, Sharpe, SQN)
rather than raw profit, and why the [What-if](../overview/robustness-tests/what-if.md) and
[Monte Carlo](../overview/robustness-tests/monte-carlo-trade-manipulation.md) checks report the
distribution of drawdowns rather than a single backtest's value.

Also: the backtest's max drawdown is a *sample*, not a ceiling. Monte Carlo reshuffling of the
same trades routinely produces drawdowns 1.5–2× worse than the historical one. Plan capital
against that worse number.

## Sizing while researching vs sizing live

These are different jobs and should use different methods:

- **While generating and testing — Fixed size (1 lot).** Every candidate is then measured on
  the same scale, so the ranking reflects the edge and not the compounding. Compounding methods
  make a mediocre strategy with a lucky early winner outrank a better one.
- **Live — risk-based sizing.** *Risk fixed % of account/balance* (position scales with the
  account) or *fixed amount* (flat money risk, useful when stops are ATR-based and vary in
  size). ATR-based sizing keeps risk constant across volatility regimes, which is what you want
  when the same system trades calm and turbulent markets.

**Martingale-style sizing** (increase after a loss) manufactures a smooth equity curve with a
hidden tail: it converts many small wins into one total loss. SQX offers *Simple Martingale MM*
because platforms do, not as a recommendation — treat any backtest that needs it to look good
as a strategy that does not work.

## Portfolio-level risk

Once several strategies trade the same account, sizing moves up a level:

- Cap **total exposure** and **same-sector exposure** — otherwise portfolio risk is the sum of
  simultaneous correlated positions, not the per-strategy figure.
- Weighting the members (equal risk, or a search over Sharpe / Return-DD / CAGR-MaxDD in the
  [Portfolio Composer](../overview/portfolio-composer.md)) is a sizing decision that changes the
  combined drawdown far more than any single strategy's parameters.
- Re-check sizing after adding a strategy: a portfolio that was fine at 1 % per member is not
  fine at 1 % per member with twice the members.

## Related

- [Money management panel](../overview/settings/money-management.md) — every method, field by field
- [Portfolio construction](portfolio-construction.md) — correlation and sector caps
- [Going live](going-live.md) — sizing down for the first months of real trading
- [Performance metrics](../overview/stats-metrics.md) — Return/DD, Sharpe, SQN

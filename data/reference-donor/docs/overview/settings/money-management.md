# Money management — Builder settings panel
> Chooses the position-sizing method — how many lots or shares each trade uses — applied to every generated strategy.

**Field-level controls (for UI tests):** [fields/money-management.md](fields/money-management.md)

## What it configures

Money management (position sizing) specifies **how many lots or shares are traded on each
trade** of the generated strategies. StrategyQuant's money-management options are flexible
and extendable, and the method you pick here is applied consistently to every candidate
during the build and can be carried into real trading on your platform later. The choice
affects reported performance (a compounding method inflates later results), so the method
used while *generating* is often different from one used for live deployment.

## Main options

- **Fixed size** — trade a fixed number of lots on every trade. Recommended while generating
  new strategies, because it gives a clear, un-compounded view of the strategy's real behaviour.
- **Fixed amount** — risk a fixed amount of money per trade (no compounding). Useful for
  testing strategies whose Stop Loss is volatility-based (ATR), or to compare strategies that
  use different Stop Loss sizes on a like-for-like basis.
- **Risk fixed % of account** — risk a set percentage of account **equity** on each trade.
  Simple and effective; position size grows as the account grows. Recommended for real
  trading, typically risking a maximum of 2–5% of equity per trade.
- **Risk fixed % of balance** — like the above, but sized against account **balance** (closed
  trades' P/L) instead of equity (which also includes open positions' real-time P/L).
- **Stocks size by price** — position sizing intended for stocks. The **Use account balance**
  option forces sizing against the current account balance instead of the initial capital.
- **Crypto size by price** — sizing for crypto, computed as `Balance / Asset Size`; you
  specify the exact decimal rounding for the asset.
- **Simple Martingale MM** — a Martingale-style method that increases position size after a
  loss.

## How it affects generation

Money management does not change *which* strategies are generated — the entry/exit logic is
the same regardless of sizing — but it changes how each strategy's results are calculated and
therefore how they rank. Compounding methods (risk % of account/balance, Martingale) make
equity curves and profit figures depend on sizing as much as on the trading edge, which can
distort comparisons between candidates. For that reason **Fixed size** is the recommended
setting during generation, giving a clean picture of the raw edge; a compounding method can
be applied later for the strategy you actually intend to trade.

## Related

- Parent: [../builder.md](../builder.md)
- Concepts (position sizing, equity vs balance): [../concepts.md](../concepts.md)
- Sibling panels: [what-to-build.md](what-to-build.md) · [trading-options.md](trading-options.md) · [ranking.md](ranking.md) · [data.md](data.md)
- Developer detail: [../../onboard/04-builder/README.md](../../onboard/04-builder/README.md)

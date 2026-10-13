# Data — Builder settings panel
> Chooses the market, timeframe, date range and backtest precision the generated strategies are tested on, and splits the history into In-Sample / Out-of-Sample parts.

**Field-level controls (for UI tests):** [fields/data.md](fields/data.md)

## What it configures

This panel defines *where* strategies are tested. You pick the backtesting engine, the
symbol(s), timeframe(s) and date range, the accuracy of the price simulation, realistic
trading costs (spread, slippage, commission), and how the history is divided into data
parts used for training, validation and out-of-sample checking.

## Main options

- **Trading Engine** — which backtesting engine is used (e.g. MetaTrader 4, MetaTrader 5).
- **Backtest data settings** — the symbol, timeframe and date range to test on. For
  multi-TF / multi-symbol strategies you select a symbol and timeframe for each additional
  chart declared in **What to build**.
- **Testing precision** — how prices are simulated during the backtest:
  - **Selected Timeframe only** — fastest; four "ticks" (Open/High/Low/Close) per bar.
    Fine for Market orders and quick previews; less accurate for Stop/Limit orders.
  - **1 Minute data** — uses minute data (if available), four ticks per minute, so
    intrabar movement is simulated; slower.
  - **Real Tick – custom spread** — real Bid from tick data, Ask derived from a spread you
    set; slow, for final verification.
  - **Real Tick – real spread** — real Bid and Ask from tick data; slowest, for final
    verification.
  - A common practice is a fast mode during generation and a slower, more precise mode for
    retesting.
- **Spread** — the Bid/Ask difference applied in the backtest.
- **Slippage** — simulated slippage in pips/ticks added to open and close prices.
- **Min distance** — minimum distance from current price at which a Stop/Limit pending order
  may be placed (mirrors broker limitations).
- **Commission** (pop-up dialog) — configure commission and related trading costs.
- **Data range parts** — split the history into typed segments:
  - **In-Sample Training (IST)** — genetic evolution computes fitness and ranks the
    population on this part.
  - **In-Sample Validation (ISV)** — checks whether IST performance holds; can be used to
    restart evolution when fitness stagnates.
  - **Out-of-Sample (OOS)** — an "unseen" part not used during generation, for validation.
  - **No Trade** — a segment where the strategy does not trade (e.g. to skip a low-volatility
    stretch in the middle of the data).

## How it affects generation

The data settings determine the market reality every candidate is scored against. The
symbol, timeframe and date range decide what price behaviour strategies must fit; the
testing precision trades speed against accuracy (a fast mode lets the Builder evaluate far
more candidates, a precise mode gives trustworthy final numbers); and spread, slippage,
commission and min distance make the backtest more realistic so strategies aren't tuned to
frictionless conditions. The data-range parts are central to avoiding overfitting: fitness
and evolution act on IST, while OOS (and ISV) reveal whether an apparent edge survives on
data the Builder never optimized against.

## Related

- Parent: [../builder.md](../builder.md)
- Concepts (backtest, In-sample vs Out-of-sample, data parts): [../concepts.md](../concepts.md)
- Sibling panels: [what-to-build.md](what-to-build.md) · [building-blocks.md](building-blocks.md) · [ranking.md](ranking.md)
- Developer detail: [../../onboard/04-builder/README.md](../../onboard/04-builder/README.md) · [../../onboard/04-builder/02-start-flow.md](../../onboard/04-builder/02-start-flow.md)

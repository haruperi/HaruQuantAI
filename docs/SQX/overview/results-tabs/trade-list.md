# Trade List — Results tab

> The full table of the strategy's individual trades, with configurable columns and views.

## What it shows

The Trade List tab is a table where each row is one trade (order) taken by the strategy during
the backtest. Columns show the trade's details — open and close times, direction, entry and
exit prices, profit/loss (in money, percent or pips), and per-trade risk figures such as MAE
and MFE. It lets you inspect the raw trade-by-trade record behind the summary statistics.

If you backtested the strategy on multiple symbols/timeframes, you can switch between the
individual results or view the list of trades for the whole portfolio.

## How it works

The tab is served by `TradeListServletPlugin` at `/tradelist/`; the rows are fetched via
`/tradelist/getTrades`. The servlet obtains the locked `ResultsGroup` through its
`IResultsGroupProvider` and reads the `OrdersList` — the collection of `Order` objects holding
each trade's times, prices, PL, and MAE/MFE. Per-trade derived values (PL, PctPL, PipsPL,
drawdown) are produced by the `IOrderComputer` (`OrderPLComputer`) after loading, and trades
can be ordered with the `OrderComparatorBy*` comparators (by open/close time or ticket).

The column layout is configurable through a companion plugin, **TradelistViews**, served at
`/tradelistviews/`. It manages the named views and the set/order of columns shown in the trade
table, in the same style as the databank's configurable views.

## Options & settings

- **Views** — switch between named column layouts, or create your own (via `/tradelistviews/`).
- **Columns** — choose which trade attributes are shown and in what order.
- **PL type** — display profit/loss in money, percent, or pips.
- **Sorting** — order trades by open time, close time, or ticket.
- **Direction / sample** — the trades shown follow the selected result key (Long / Short /
  Both, In-Sample / Out-of-Sample / Full).

## Related

- Parent overview: [../results-databank.md](../results-databank.md)
- Sibling tabs: [overview.md](overview.md), [equity-chart.md](equity-chart.md),
  [chart.md](chart.md), [trade-analysis.md](trade-analysis.md),
  [profile-chart.md](profile-chart.md)
- Developer detail: [../../onboard/08-results/](../../onboard/08-results/README.md)
- Servlet endpoints: `/tradelist/` (rows via `/tradelist/getTrades`), `/tradelistviews/`

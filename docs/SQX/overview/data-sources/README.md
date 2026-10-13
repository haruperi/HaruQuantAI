# Data Sources — Detailed Reference

Which market data StrategyQuant X / QuantDataManager can download or import, and from where.
Each source has its own leaf page: **what markets/instruments it provides**, **granularity
(ticks vs bars)**, and **how you connect / import from it**.

Parent: [Data Manager (QDM)](../data-manager.md) · [Overview index](../README.md)

Data sources are implemented as **DataSource plugins** (and, for crypto, `IExchange` connectors).
There are nine built-in sources plus a flexible file importer.

## Download sources (fetched over the internet)

| Source | Provides | Page |
|--------|----------|------|
| **Dukascopy** | Forex / CFD tick history (CDN) | [dukascopy.md](dukascopy.md) |
| **Yahoo** | Stocks / indices (EOD & intraday bars) | [yahoo.md](yahoo.md) |
| **Darwinex** | Forex / CFD broker data | [darwinex.md](darwinex.md) |
| **SQ Equity Data** | StrategyQuant's own equity/stock data feed (CDN) | [sq-data-feeds.md](sq-data-feeds.md) |
| **SQ Futures Data** | StrategyQuant's own futures data feed (CDN) | [sq-data-feeds.md](sq-data-feeds.md) |
| **Crypto exchanges** | Cryptocurrency spot & futures (Binance, Bitfinex, Coinbase Pro, Poloniex) | [crypto-exchanges.md](crypto-exchanges.md) |
| **TD** | Third-party data feed | [td.md](td.md) |

## Import sources (from a local install or files)

| Source | Provides | Page |
|--------|----------|------|
| **MetaTrader 5 import** | Broker-accurate history from a local MT5 terminal | [mt5-import.md](mt5-import.md) |
| **CSV / text file import** | Any history in delimited text, with column mapping | [csv-import.md](csv-import.md) |

## Export formats (write data back out)

| Target | Use | Page |
|--------|-----|------|
| **MT4 (FXT/HST), MT5, CSV** | Feed high-quality data into MetaTrader or other tools | [export-formats.md](export-formats.md) |

> Data granularity matters: *tick* data gives the most precise backtests (real-tick precision),
> while *bar* (OHLC) data is faster but coarser. See [../concepts.md](../concepts.md) and the
> [Data settings panel](../settings/data.md) for how a strategy chooses precision.
>
> Developer/architecture detail (download machinery, jobs, `IExchange`): [../../onboard/02-qdm/](../../onboard/02-qdm/README.md).

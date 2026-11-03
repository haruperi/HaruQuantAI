# Crypto exchanges — data source

> Cryptocurrency spot and futures history, downloaded directly from the exchanges.

## What it provides

The Crypto source downloads **cryptocurrency** history directly from a set of supported
exchanges. Each exchange is a separate connector, and together they cover both **spot** and
**futures** markets:

| Connector | Market |
|-----------|--------|
| **Binance** (spot) | Crypto spot |
| **Binance USDT-M** | USDT-margined futures |
| **Binance COIN-M** | COIN-margined futures |
| **Bitfinex** | Crypto spot |
| **Coinbase Pro** | Crypto spot |
| **Poloniex** | Crypto spot |

Data is downloaded as bars and can be stored/tested at the standard timeframes; each exchange
exposes its own symbol list (trading pairs).

## How to use it

1. In the **Data** section of QuantDataManager, choose a **Crypto** connection and pick the
   exchange (e.g. Binance spot, Binance USDT-M, Coinbase Pro, …).
2. Select the symbol / trading pair(s), timeframe, and date range.
3. Click **Download** (or **Update** to extend existing data).
4. QDM asks the selected exchange connector to fetch the data, merges it with any existing
   data, and writes it to the shared data store for SQX.

## Notes & limitations

- The available trading pairs and history depth come from each exchange's own API and can
  change without notice; QDM does not guarantee a fixed range per symbol.
- The six connectors are the ones listed above — Binance (spot / USDT-M / COIN-M), Bitfinex,
  Coinbase Pro, and Poloniex.
- Downloads are **incremental** — updates fetch only the missing data.

## Related

- [Data Manager (QDM)](../data-manager.md)
- [Data settings panel](../settings/data.md)
- Sibling sources: [SQ data feeds](sq-data-feeds.md), [Dukascopy](dukascopy.md)
- Developer detail (the `IExchange` connectors): [../../onboard/02-qdm/](../../onboard/02-qdm/README.md)

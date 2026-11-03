# SQ Equity Data & SQ Futures Data — data sources

> StrategyQuant's own curated equity and futures data feeds, delivered over its CDN.

## What they provide

StrategyQuant maintains two of its own data feeds, served through its **CDN**:

- **SQ Equity Data** — historical **stock / equity** data.
- **SQ Futures Data** — historical **futures** data (contracts, with roll handling).

Both are curated feeds designed to work cleanly with StrategyQuant X out of the box. Data is
stored as bars and can be tested at the usual timeframes. Because they are CDN feeds, their
downloads use the dedicated CDN download queue.

## How to use it

1. In the **Data** section of QuantDataManager, pick an **SQ Equity Data** or **SQ Futures
   Data** connection.
2. Select the symbol(s), timeframe, and date range.
3. Click **Download** (or **Update** to extend existing data).
4. QDM downloads from the CDN, merges with any existing data, recomputes the timezone, and
   writes the result to the shared data store. Equity symbols are grouped on disk by the first
   letter of the symbol.

## Notes & limitations

- These are **CDN** feeds and use the CDN queue; access may depend on your subscription/plan.
- Downloads are **incremental** — updates fetch only the missing data and merge it.
- SQ Futures Data covers futures contracts (with roll dates handled internally); SQ Equity Data
  covers stocks. Coverage and available history are defined by StrategyQuant's catalog and are
  not guaranteed to be a fixed range per symbol.

## Related

- [Data Manager (QDM)](../data-manager.md)
- [Data settings panel](../settings/data.md)
- Sibling sources: [Yahoo](yahoo.md), [Dukascopy](dukascopy.md)
- Developer detail: [../../onboard/02-qdm/](../../onboard/02-qdm/README.md)

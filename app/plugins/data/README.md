# Market Data Domain (`app/plugins/data`)

**Domain:** Market Data (`F02`)
**Status:** In Development
**Ratified Ownership:** `app/plugins/data`

## Overview

The Market Data subsystem owns instrument definitions, broker specifications, trading sessions and clocks, file ingestion pipelines, data quality inspection, timeframe and timezone transformations, provider download adapters, custom datasets / baskets, and CFTC Commitments of Traders (COT) synchronization.

All database interactions for instruments, sessions, and datasets strictly use the authoritative host SQLite persistence layer (`app.host.persistence`), upholding the constitutional invariant that plugins never execute ad-hoc SQL.

## Architecture and Capabilities

```
+-------------------------------------------------------------+
|                  FastAPI Transport Router                   |
|                 (app/plugins/data/integration.py)           |
+------------------------------+------------------------------+
                               |
       +-----------------------+-----------------------+
       |                       |                       |
       v                       v                       v
+--------------+       +---------------+       +---------------+
|   Catalog    |       |   Sessions    |       |   Ingestion   |
| (catalog.py, |       | (sessions.py) |       | (ingestion.py)|
| instruments) |       +-------+-------+       +-------+-------+
+------+-------+               |                       |
       |                       |                       v
       |                       |               +---------------+
       |                       |               | Quality & Res |
       |                       |               | (quality.py,  |
       |                       |               | transforms.py)|
       |                       |               +-------+-------+
       |                       |                       |
       v                       v                       v
+-------------------------------------------------------------+
|                Authoritative Host Persistence               |
|                    (app.host.persistence)                   |
|      [datamgr_instruments, datamgr_sessions, datamgr_datasets]|
+-------------------------------------------------------------+
```

## Feature Mapping Matrix

| Feature ID | Capability Slug | Primary Module | Responsibility |
| --- | --- | --- | --- |
| `FEAT-DATA-CATALOG` | `FR-DATA-CATALOG-*` | `catalog.py` | Authoritative dataset catalog, revisions, broker mappings |
| `FEAT-DATA-INSTRUMENTS` | `FR-DATA-INSTRUMENTS-*` | `instruments.py` | Instrument specifications, decimals, tick size, margins, swaps, CRUD via host persistence |
| `FEAT-DATA-SESSIONS` | `FR-DATA-SESSIONS-*` | `sessions.py` | Calendars, zoneinfo timezones, DST handling, NinjaTrader XML import, CRUD via host persistence |
| `FEAT-DATA-INGESTION` | `FR-DATA-INGESTION-*` | `ingestion.py` | Streaming CSV/text ingestion, chunking, fingerprinting, immutable revisions |
| `FEAT-DATA-QUALITY` | `FR-DATA-QUALITY-*` | `quality.py` | Gaps, duplicates, bar validation, authoritative quality scores |
| `FEAT-DATA-TRANSFORMS` | `FR-DATA-TRANSFORMS-*` | `transforms.py` | Timeframe resampling (M1->M5, H1, D1), timezone cloning, CSV/MT4/MT5 export |
| `FEAT-DATA-PROVIDERS` | `FR-DATA-PROVIDERS-*` | `providers.py` | Download adapters (Binance, Bitfinex, Coinbase, Poloniex, Darwinex, Dukascopy, MT5, SQ Equity/Futures, TD, Yahoo) |
| `FEAT-DATA-BASKETS` | `FR-DATA-BASKETS-*` | `baskets.py` | Stock groups, basket membership, multi-symbol dataset alignment |
| `FEAT-DATA-CUSTOM` | `FR-DATA-CUSTOM-*` | `custom_data.py` | Custom indicator data series, multi-column value series storage |
| `FEAT-DATA-COT` | `FR-DATA-COT-*` | `cot.py` | CFTC COT symbol catalog, 5-field mapping, weekly release alignment, update synchronization |
| `FEAT-DATA-INTEGRATION` | `FR-DATA-INTEGRATION-*` | `integration.py` | Connected Data Manager REST router and prebuilt UI projection |

## Persistence Contract

In compliance with `AGENTS.md` Section 3:
1. `instruments.py` executes CRUD operations exclusively through `DatabaseManager.instruments` (`InstrumentPersistence`).
2. `sessions.py` executes CRUD operations exclusively through `DatabaseManager.sessions` (`SessionPersistence`).
3. `catalog.py` and `ingestion.py` store dataset metadata via `DatabaseManager.datasets` (`DatasetPersistence`).
4. Raw SQLite connections and direct SQL statements are completely absent from `app/plugins/data`.

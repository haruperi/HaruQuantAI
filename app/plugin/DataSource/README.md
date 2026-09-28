# Data Source Plugins (`app/plugin/DataSource`)

This directory houses quantitative data source plugins for HaruQuantAI. Each plugin
provides acquisition capabilities for specific market data providers, attaching exclusively
to `workspace.data_manager` through explicit, typed capability slots.

---

## Architectural Principles

1. **One Concrete Plugin, One Cohesive Python File**:
   Calculation, decoding, network transport, parameter schema, bounds, output formatting,
   and metadata stay together in a single Python file (e.g., `dukascopy.py`).
2. **Spatial Composability & Orthogonality**:
   Plugins do not mutate global state, import sibling plugin private internals, or execute
   ad-hoc database operations. Collaboration is mediated through immutable documents and
   host capability interfaces.
3. **Slot Attachment**:
   Data source plugins attach via `data_source.acquisition@1.0.0`. UI counterparts attach
   via `data_source.presentation@1.0.0`.
4. **Deterministic Storage**:
   Stored market data remains strictly UTC in Parquet format. Broker timezone offsets
   are applied only at read-time in user-selected views. Higher timeframes (M5, H1, D1)
   are dynamic read-time aggregations of canonical M1 data.

---

## Active Plugins

### 1. Dukascopy Data Source (`dukascopy.py`)

- **Package ID**: `plugin.data_manager.dukascopy`
- **Owner**: `workspace.data_manager`
- **Attachment**: `data_source.acquisition@1.0.0`
- **UI Entry**: `app/ui/app/plugins/DataSource/Dukascopy/contribution.tsx`
- **Status**: Offline direct and SQ CDN acquisition candidate with full test coverage and verified offline example.

#### Key Features & Technical Policies
- **Independent Bounded BI5 Decoder**:
  Parses binary LZMA-compressed `.bi5` records for Forex tick data and bid-side M1 bars
  without external binary dependencies.
- **Tick Volume Policy**:
  Checked sum of ask volume and bid volume (`ask_volume + bid_volume`) after converting
  provider lots/millions to base currency units. (SQX native decoder uses bid volume only;
  dual-side volume sum is HaruQuantAI's explicit architectural choice).
- **Adaptive Rate Throttling**:
  Follows StrategyQuant's `DownloadRateCorrector` pattern: +25% backoff delay on HTTP 429/503
  rate-limit responses; -25% delay reduction after 100 consecutive successful requests.
- **Sunday Tick Handling**:
  Sunday tick acquisition begins at 19:00 UTC, preventing false missing-hour alerts during
  weekend market closure.
- **Dual Transport Modes**:
  1. *Direct Dukascopy*:
     Fetches hourly `.bi5` files directly from `https://datafeed.dukascopy.com/datafeed/{symbol}/{year}/{month:02d}/{day:02d}/{hour:02d}h_ticks.bi5`.
  2. *StrategyQuant Fast CDN*:
     Fetches pre-packaged daily ZIP archives from `https://cdn.strategyquantcdn.com` (Global)
     or `https://cdn005.strategyquantcdn.com` (Hong Kong / China). Validates remote
     descriptors and performs automatic seamless fallback to Direct Dukascopy if CDN data
     is unavailable or missing for the requested date range.

#### Parity with StrategyQuant X Build 144
| Functionality | SQX Reference | HaruQuantAI UI | HaruQuantAI CLI |
| :--- | :--- | :--- | :--- |
| **Add Symbol** | `DataSourceDukascopy\add` | `app/ui/app/plugins/DataSource/Dukascopy/add.tsx` | `uv run python scripts/data_manager_cli.py --source dukascopy --add-symbol EURUSD --data-type M1 --broker-profile dukascopy` |
| **Download Data** | `DataSourceDukascopy\import` | `app/ui/app/plugins/DataSource/Dukascopy/import.tsx` | `uv run python scripts/data_manager_cli.py --source dukascopy --import EURUSD_dukascopy --start-date 2026-01-01 --end-date 2026-03-01 --redownload missing --fast-download sqx-cdn` |
| **Legal Disclaimer** | `DataSourceDukascopy\disclaimer` | `app/ui/app/plugins/DataSource/Dukascopy/disclaimer.tsx` | `uv run python scripts/data_manager_cli.py --source dukascopy --disclaimer` |

#### Legal Disclaimers
The Dukascopy plugin embeds the verbatim legal notices required by Dukascopy Bank SA
and StrategyQuant s.r.o. Accessible via CLI `--disclaimer` or in the UI disclaimer modal.

---

## Future Data Source Plugins

Future data sources planned under this directory follow the same single-file backend pattern:
- **Yahoo Finance** (`yahoo.py`): Free daily/intraday equity, ETF, and index historical data.
- **Tick Downloader / Custom CSV** (`csv_importer.py`): Generic MT4/MT5 and external tick/bar file importer.
- **SQ Data** (`sq_data.py`): StrategyQuant proprietary binary format adapter.
- **Broker Live Feeds** (`darwinex.py`, `interactive_brokers.py`): Direct execution venue data feeds.

---

## Verification & Testing

Every plugin under this directory must supply:
1. Focused unit and integration tests under `tests/plugin/data_source/` (e.g., `test_dukascopy.py`).
2. Self-contained deterministic offline usage example in `tests/examples/` (e.g., `dukascopy_offline.py`).
3. Complete compliance with Ruff (formatting & linting), Mypy (strict typing), and >= 80% branch coverage floor.
4. Clean package manifest entry in `package.json` with zero unowned files.

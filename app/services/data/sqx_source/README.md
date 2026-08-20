# SQX Source — FEAT-DATA-15

Direct read-only access to the StrategyQuant X / QuantDataManager workspace.

## Purpose

Decodes QuantDataManager `.dat` binary history files (M1 bars and ticks)
directly into pandas DataFrames with Numba JIT and synchronises the
Data-owned reference catalogues from the QuantDataManager catalogue plus
live MT5 symbol metadata. Nothing is written into the QuantDataManager
workspace and no data is duplicated to disk.

### Feature Registry

| Status    | Feature                  | Owning module       | Public API and contracts                                                                                                                                                            | Requirements      | Usage evidence                             |
| --------- | ------------------------ | ------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ----------------- | ------------------------------------------ |
| Completed | `FEAT-DATA-15` SQX Source | `sqx_source/`      | `read_sqx_m1`, `read_sqx_ticks`, `list_sqx_symbols`, `sync_quantdata_reference`; M1 rows carry UTC-indexed OHLCV, tick rows carry bid/ask/spread/volume, and the sync upserts `data_market_series`, `data_brokers`, and `data_instruments` | `FR-DATA-221`–`224` | `tests/data/usage/features/15_sqx_source.py` |

## Public API

- `read_sqx_m1(symbol_or_path, *, start, end, max_bars, request_id)` — bounded
  UTC-indexed M1 OHLCV frame.
- `read_sqx_ticks(symbol_or_path, *, start, end, max_ticks, request_id)` —
  bounded UTC-indexed bid/ask/spread/volume frame.
- `list_sqx_symbols(*, request_id)` — catalogue symbols, timeframes, ranges,
  and row counts.
- `sync_quantdata_reference(*, request_id)` — one-shot reference sync; series
  and broker rows come from the QuantDataManager catalogue, instrument
  specifications from live MT5 `get_symbol_metadata`. MT5 unavailability does
  not fail the sync; the summary reports `mt5_available: false`.

## Configuration

- `QUANTDATA_MANAGER_ROOT` (default `C:/QuantDataManager125`) — the
  QuantDataManager install root; `user/data/History` and `user/data/data.db`
  are resolved beneath it. A missing root fails closed with
  `QUANTDATA_ROOT_MISSING`.

## Format notes

`.dat` payloads are sequential delta streams: per-record config bytes encode
each field's width (1/2/4/8 bytes) and delta opcode (subtract/add/absolute),
with a 19-byte sync chain plus block index every 1000 records. Prices scale
by 10^6; volumes by 10^5 (M1, version 4.2) or 10^2 (ticks). The format is
version-pinned to header version `4.2`; a StrategyQuant format change will
surface as decode divergence rather than silent corruption.

## Boundaries

Read-only against QuantDataManager; persistence writes go through
`app.services.data.persistence` upserts owned here; instrument specs come
from the Data `market_data` feature rather than a broker deep import.

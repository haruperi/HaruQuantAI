# Crypto data coverage and evidence

Task `FEAT-UI-DATA-CRYPTO`; approved plan: `docs/crypto-data-implementation-plan.md`.
Reference installation: `C:/SQX_144_2953_win_20260601`.

## Source and registration trace

`DataSourceCrypto/add/module.js` registers one shared Add template with six plugin IDs and exact
titles: Binance, BinanceCoinM, BinanceUsdtM, Bitfinex, Poloniex and Coinbase. The controller requests
the selected exchange's symbols/timeframes, clears the filter, selects the first timeframe, requires
at least one checked symbol and the free-data confirmation, then submits exchange, comma-separated
symbols, timeframe and postfix. The template contains only a Symbol column, Timeframe, Data postfix,
the free-data disclaimer, Close and Save.

`DataSourceCrypto/import` is the existing-record Download action. It filters selected rows to Crypto,
rejects clones and rows already in progress, sets From from the first record's last date and To to
today, and serializes each target's name, instrument, underlying symbol and previous date. The shared
date-range directive supplies six presets. Redownload options are missing-only and overwrite. Start
sets per-row “Preparing Crypto data download” progress; `importDataAction` handles row job actions.

Read-only `jar tf`/`javap -p -c -constants` inspection established that no symbol catalog is bundled.
Provider plugins fetch public exchange endpoints. Fixed timeframe lists are:

| Exchange | Timeframes |
| --- | --- |
| Binance / Coin-M / USDT-M | M1, M3, M5, M15, M30, H1, H2, H4, H6, H8, H12, D1 |
| Bitfinex | M1, M5, M15, M30, H1, H3, H6, H12, D1 |
| Poloniex | M5, M15, M30, H2, H4, D1 |
| Coinbase Pro | M1, M5, M15, H1, H6, D1 |

## Inclusion and exclusion register

Included: all six exact Add variants, representative provider-native offline catalogs, search,
checkbox/header selection, fixed timeframe options, postfix, provider consent, validation, persisted
Add lifecycle, existing-record Download, target isolation, clone/in-progress rejection, date presets,
missing/overwrite interval behavior, persistent recovery, shared progress and trailing row status,
cross-provider operation/name guards, focus, themes and narrow layouts.

Excluded: live exchange HTTP calls, current listing claims, API credentials, rate limits/retries,
real OHLCV/tick data, backend operations, trading, and native update-all internals. Mock availability
dates are fixture inputs for All time validation and are not exposed as provider facts. Compiled donor
classes were inspected but not copied or executed.

## Feature register

All seven entries use persistence `sqx-crypto-data-v1`: bounded definitions, synthetic date intervals
and one job; a running reload becomes paused. Consent and filter drafts are transient.

### CRYPTO-ADD-BINANCE-001

- **product/screen**: SQX Data Manager / Add Binance symbol(s)
- **source**: DataSourceCrypto Add template/controller; CryptoExchangeBinance bytecode
- **trigger/controls**: Crypto data > Add crypto symbol > Binance spot; symbol filter/table,
  12 timeframes, postfix, consent, Close/Save
- **preconditions/validation**: readable storage, no active operation; selection, consent, supported
  timeframe, bounded postfix, globally unique valid names
- **transitions/outcome**: open/reset/filter/select/save; empty Crypto definitions progress through
  running/paused/cancelled/failed/completed; zero real bars
- **mock operation**: `cryptoDefinitions` / `useCrypto.startAdd`
- **status**: visual implemented; interaction implemented; state implemented
- **verification/gaps**: browser and unit tests passed; ten-symbol offline fixture, no live inventory

### CRYPTO-ADD-BINANCE-COINM-001

- **product/screen**: SQX Data Manager / Add Binance Coin-M symbol(s)
- **source/trigger**: shared Add source plus CryptoExchangeBinanceCoinM; Coin-M menu entry
- **controls/validation/transitions/outcome**: shared Add contract with 12 timeframes and native
  perpetual symbols; empty definitions and shared lifecycle
- **mock operation/persistence**: `cryptoDefinitions(BinanceCoinM)` / `useCrypto.startAdd`;
  `sqx-crypto-data-v1`
- **status/verification**: visual, interaction and state implemented; exact title/options verified
- **gaps**: eight-symbol offline fixture; no current contract/listing claim

### CRYPTO-ADD-BINANCE-USDTM-001

- **product/screen**: SQX Data Manager / Add Binance USDT-M symbol(s)
- **source/trigger**: shared Add source plus CryptoExchangeBinanceUsdtM; USDT-M menu entry
- **controls/validation/transitions/outcome**: shared Add contract with 12 timeframes and native
  futures symbols; empty definitions and shared lifecycle
- **mock operation/persistence**: `cryptoDefinitions(BinanceUsdtM)` / `useCrypto.startAdd`;
  `sqx-crypto-data-v1`
- **status/verification**: visual, interaction and state implemented; exact title/options verified
- **gaps**: ten-symbol offline fixture; no current contract/listing claim

### CRYPTO-ADD-BITFINEX-001

- **product/screen**: SQX Data Manager / Add Bitfinex symbol(s)
- **source/trigger**: shared Add source plus CryptoExchangeBitfinex; Bitfinex menu entry
- **controls/validation/transitions/outcome**: shared Add contract with nine provider timeframes;
  empty definitions and shared lifecycle
- **mock operation/persistence**: `cryptoDefinitions(Bitfinex)` / `useCrypto.startAdd`;
  `sqx-crypto-data-v1`
- **status/verification**: visual, interaction and state implemented; exact title/options verified
- **gaps**: eight-symbol offline fixture; provider pair list is dynamic in SQX

### CRYPTO-ADD-POLONIEX-001

- **product/screen**: SQX Data Manager / Add Poloniex symbol(s)
- **source/trigger**: shared Add source plus CryptoExchangePoloniex; Poloniex menu entry
- **controls/validation/transitions/outcome**: shared Add contract with six provider timeframes;
  empty definitions and shared lifecycle
- **mock operation/persistence**: `cryptoDefinitions(Poloniex)` / `useCrypto.startAdd`;
  `sqx-crypto-data-v1`
- **status/verification**: visual, interaction and state implemented; pause/reload/resume verified
- **gaps**: eight-symbol offline fixture; provider market list is dynamic in SQX

### CRYPTO-ADD-COINBASE-001

- **product/screen**: SQX Data Manager / Add Coinbase Pro symbol(s)
- **source/trigger**: shared Add source plus CryptoExchangeCoinbasePro; Coinbase Pro menu entry
- **controls/validation/transitions/outcome**: shared Add contract with six provider timeframes and
  hyphenated native symbols; empty definitions and shared lifecycle
- **mock operation/persistence**: `cryptoDefinitions(Coinbase)` / `useCrypto.startAdd`;
  `sqx-crypto-data-v1`
- **status/verification**: visual, interaction and state implemented; filtering, consent, H6,
  persistence and trailing status verified
- **gaps**: eight-symbol offline fixture; donor retains legacy Coinbase Pro naming

### CRYPTO-DOWNLOAD-001

- **product/screen**: SQX Data Manager / Download crypto data for symbol or multiple
- **source/trigger**: DataSourceCrypto import module/template/controller; Crypto data > Download data
  for existing symbol
- **controls**: From/To, six presets, missing-only/overwrite, Close, Start download
- **preconditions/validation**: selected Crypto definitions, no clone or active target, valid ordered
  dates through today, mock availability bounds, known persisted target IDs, writable storage
- **transitions/outcome**: configure/start/pause/resume/stop/fail/complete/reload; only selected Crypto
  rows receive synthetic calendar-day interval summaries in the trailing Status/progress UI
- **mock operation/persistence**: `cryptoTargets`, `cryptoDownloadRanges`, `useCrypto.startDownload`;
  `sqx-crypto-data-v1`
- **status**: visual implemented; interaction implemented; state implemented
- **verification/gaps**: mixed-provider isolation, all presets, validation, overwrite, persisted coverage
  and screenshots passed; one mock sample/day, no actual exchange data

## Verification

Focused Crypto results are recorded in `docs/crypto-data-walkthrough.md`. The implementation keeps
FR-UI-011 and the overall Data Manager Partial because the backend and live providers remain absent.

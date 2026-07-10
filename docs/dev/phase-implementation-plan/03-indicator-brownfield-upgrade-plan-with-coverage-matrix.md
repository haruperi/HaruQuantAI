# Phase 03 Indicator Library — Brownfield Upgrade Plan with Requirement Coverage Matrix

**Target module:** `app/services/indicators/`  
**Plan file:** `docs/dev/phase-implementation-plan/03-indicator.md`  
**Brownfield status:** Preserve and harden existing implementation; do not replace with a greenfield folder structure.  
**Requirement source:** `03-indicator-library.md`, containing 155 explicit requirement IDs.

## 0. Purpose

This document is the single source of truth for upgrading the existing Indicator module as a brownfield system. The current repository already contains working indicator classes, public singleton exports, helper functions, documentation, and a usage script. The upgrade therefore proceeds by characterization, compatibility preservation, contract hardening, and incremental migration toward the enhanced architecture.

This plan replaces the earlier greenfield-style architecture document. The earlier file described a target tree with many new folders before proving how it related to the current code. This brownfield plan keeps the current module as the baseline and introduces new files only when they reduce risk, clarify public boundaries, or provide required contracts that are missing today.

## 1. Non-Negotiable Brownfield Rules

1. Preserve `app/services/indicators/` and all currently importable public names during the migration window.
2. Do not delete, rename, or move working code until characterization tests and compatibility wrappers exist.
3. Keep `from app.services.indicators import ema, sma, rsi, atr, ...` working until an owner-approved deprecation window is complete.
4. Add official `IndicatorResult`/registry/API wrappers beside current classes before changing class return shapes.
5. Existing `.calculate(df, ...) -> Series | DataFrame` behavior remains legacy-compatible until downstream modules migrate.
6. Build tests before risky refactors.
7. Avoid large move-only refactors.
8. Introduce new files only when they clarify boundaries or reduce coupling.
9. Keep indicator calculations deterministic.
10. Do not introduce lookahead bias.
11. Do not mutate caller-owned input data unexpectedly.
12. Do not let official tool boundaries leak raw pandas/numpy internals when JSON-safe outputs are required.
13. Do not make Indicators own broker reads, data persistence, strategy decisions, risk decisions, trading execution, UI/API routing, live runtime, or optimization orchestration.
14. Importing `app.services.indicators` must not start broker sessions, read credentials, write files, initialize cache adapters, or perform long-running work.
15. Any indicator that uses future bars internally must be classified as legacy/custom or masked before strategy-facing use.

## 2. Current Repository Baseline

### 2.1 Current folder and file inventory

The current module baseline is documented by the repository README and public package file. It has these files and roles:

| Current file | Brownfield baseline role |
|---|---|
| `app/services/indicators/__init__.py` | Public module gate currently imports classes, creates singleton instances, and exports helpers. Preserve during migration; later convert to compatibility-safe facade. |
| `app/services/indicators/base.py` | BaseIndicator abstract class plus helper functions crossed_above, crossed_below, pips_to_price, balance_scaled_volume, arithmetic_average, weighted_average. |
| `app/services/indicators/README.md` | Current service documentation and directory map; must be updated to brownfield boundary and migration notes. |
| `app/services/indicators/candles/doji.py` | Existing candlestick pattern detector. Preserve; add characterization, schema, availability, and result wrapper. |
| `app/services/indicators/candles/engulfing.py` | Existing candlestick pattern detector. Preserve; add characterization, schema, availability, and result wrapper. |
| `app/services/indicators/candles/inside_bar.py` | Existing candlestick pattern detector. Preserve; add characterization, schema, availability, and result wrapper. |
| `app/services/indicators/candles/pinbar.py` | Existing candlestick pattern detector. Preserve; add characterization, schema, availability, and result wrapper. |
| `app/services/indicators/custom/hull_moving_average.py` | Existing custom/advanced moving average. Preserve as compatibility indicator; add conformance review before official status. |
| `app/services/indicators/custom/smc.py` | Existing Smart Money Concepts implementation. Preserve but quarantine as legacy/custom until lookahead review because it uses future shifts in FVG/swing logic. |
| `app/services/indicators/momentum/macd.py` | Existing MACD implementation returning multi-column DataFrame. |
| `app/services/indicators/momentum/rsi.py` | Existing RSI implementation using Wilder-style ewm; currently replaces zero loss with epsilon. |
| `app/services/indicators/momentum/will_r.py` | Existing Williams %R implementation. |
| `app/services/indicators/trend/bollinger_bands.py` | Existing Bollinger Bands implementation returning multi-column DataFrame. |
| `app/services/indicators/trend/ema.py` | Existing EMA implementation returning Series. |
| `app/services/indicators/trend/sma.py` | Existing SMA implementation returning Series. |
| `app/services/indicators/trend/wma.py` | Existing WMA implementation. |
| `app/services/indicators/volatility/atr.py` | Existing ATR implementation using true range and Wilder-style ewm with explicit warmup NaNs. |
| `app/services/indicators/volatility/standard_deviation.py` | Existing rolling standard deviation implementation. |
| `app/services/indicators/volume/cmf.py` | Existing Chaikin Money Flow implementation. |
| `app/services/indicators/volume/mfi.py` | Existing Money Flow Index implementation. |
| `app/services/indicators/volume/obv.py` | Existing On-Balance Volume implementation. |
| `app/services/indicators/volume/price_volume_distribution.py` | Existing price/volume distribution implementation. |
| `tests/usage/03_indicator.py` | Existing runnable usage script; currently fetches MT5/data-service data and manually joins indicator outputs. |

### 2.2 Current exports

`app/services/indicators/__init__.py` currently exports the following names and instantiates indicator singletons at import time:

`BaseIndicator`, `atr`, `cmf`, `ema`, `macd`, `mfi`, `obv`, `rsi`, `sma`, `smc`, `wma`, `bollinger_bands`, `doji`, `engulfing`, `hull_moving_average`, `inside_bar`, `pinbar`, `price_volume_distribution`, `standard_deviation`, `williams_r`, `arithmetic_average`, `balance_scaled_volume`, `crossed_above`, `crossed_below`, `pips_to_price`, `weighted_average`

Brownfield interpretation:

- The singleton exports are **legacy compatibility API** during migration.
- `BaseIndicator` and helper functions are **public support API**.
- New official agent/API wrappers shall be added through `api.py` and registry-backed functions, not by breaking current singleton imports.
- `__all__` must remain explicit and tested.

### 2.3 Current capabilities already present

The current code already provides meaningful calculation coverage:

- Trend: SMA, EMA, WMA, Bollinger Bands.
- Momentum: RSI, MACD, Williams %R.
- Volatility: ATR, rolling standard deviation.
- Volume: OBV, MFI, CMF, price-volume distribution.
- Candles: Doji, Engulfing, Inside Bar, Pinbar.
- Custom/advanced: Hull Moving Average and SMC.
- Helpers: crossovers, pips-to-price, arithmetic average, weighted average, balance-scaled volume.
- Documentation: `app/services/indicators/README.md`.
- Usage: `tests/usage/03_indicator.py`.

### 2.4 Current validation behavior

Current implementations perform local checks such as missing-column and period validation, generally raising `ValueError` or `LookupError`. This is useful but incomplete. The brownfield upgrade must centralize validation for duplicate columns, UTC timestamp/index requirements, MultiIndex symbol/timestamp handling, parameter bounds, invalid numeric values, provenance, no-lookahead metadata, collision policy, and deterministic `IND_*` errors.

### 2.5 Current dependency relationships

- The indicator module depends on `pandas` and `numpy` in calculation files.
- `BaseIndicator.balance_scaled_volume` type-checks against `app.services.contracts.strategies.AccountSnapshot` only under `TYPE_CHECKING`.
- `tests/usage/03_indicator.py` imports `app.services.brokers.mt5.get_mt5_client`, `app.services.data.get_data`, `app.utils.logger.logger`, and `app.utils.settings.settings` for examples. This is acceptable as an optional usage script, but official indicator logic must remain broker-free and provider-free.
- The Data module already exports market-data functions such as `get_data`, `list_symbols`, `get_symbol_metadata`, `validate_bars`, `align_multitimeframe_data`, and `resample_ohlcv`; Indicators should consume normalized Data outputs but not own provider routing.
- Utils exposes the logger; indicator production modules should log only through approved utility logging contracts and not use `print()`.

### 2.6 Current pain points and risks

1. `__init__.py` instantiates all indicators at import time. The constructors appear lightweight, but import-time object creation should be covered by side-effect tests and eventually wrapped by lazy/registry construction if needed.
2. There is no official `IndicatorProtocol`, `IndicatorConfig`, `IndicatorContext`, `IndicatorResult`, or `IndicatorManifest` contract.
3. Public return shapes are raw `pd.Series` or `pd.DataFrame`; official tool boundaries need result wrappers and JSON-safe serialization.
4. Error behavior is native and inconsistent (`ValueError`, `LookupError`) rather than deterministic `IND_*` codes.
5. Warmup, NaN, infinity, divide-by-zero, negative-zero, and insufficient-history behavior is not documented uniformly.
6. No registry/capability matrix/deprecation lifecycle exists.
7. No manifest, parameter hash, input checksum, output checksum, or provenance contract exists.
8. No `available_at`/no-lookahead metadata exists.
9. SMC uses future-looking shifts for FVG/swing logic and must not be strategy-facing until masked, refactored, or explicitly classified as research/legacy.
10. Usage examples perform live/data reads; pure synthetic examples should be separated from optional integration examples.
11. Current test coverage could not be fully verified from available GitHub connector discovery; the README references `tests/unit/app/services/indicators/`, and `tests/usage/03_indicator.py` exists.

## 3. Target Brownfield Architecture

The target architecture evolves the current module in-place. It does not require deleting the existing family folders.

```text
app/services/indicators/
├── __init__.py                         # preserve compatibility exports; add official wrappers only after migration
├── base.py                             # preserve; harden docstrings/helpers; align with protocol by adapter
├── contracts.py                        # add typed public contracts/results/manifests/errors/state
├── errors.py                           # add deterministic IND_* taxonomy and wrappers
├── validation.py                       # add shared input/parameter/naming/provenance validators
├── availability.py                     # add warmup/no-lookahead/available_at/alignment helpers
├── registry.py                         # add registry, capability matrix, lifecycle/deprecation metadata
├── api.py                              # add official stable functions returning IndicatorResult
├── formula_specs.py                    # add formula tables and golden-fixture metadata
├── cache.py                            # optional/deferred cache port/service; no import-time initialization
├── audit.py                            # optional/deferred audit entry builder and sink port
├── incremental.py                      # optional/deferred incremental state contracts
├── candles/                            # keep; harden in place
├── custom/                             # keep; mark custom/legacy until conformance review
├── momentum/                           # keep; harden in place
├── trend/                              # keep; harden in place
├── volatility/                         # keep; harden in place
└── volume/                             # keep; harden in place
```

### 3.1 Keep

Keep current family folders and calculation classes. They are the calculation baseline for characterization tests.

### 3.2 Harden in place

Harden existing files by adding shared validators, formula specs, warmup metadata, and result adapters. Do not move formulas before tests pin behavior.

### 3.3 Add only when reducing risk

Add `contracts.py`, `errors.py`, `validation.py`, `availability.py`, `registry.py`, `api.py`, and `formula_specs.py` because they create missing boundaries without destroying existing code.

### 3.4 Defer

Defer concrete cache, audit persistence, acceleration, out-of-core, and incremental implementations until batch contracts and parity tests are stable. Define ports/contracts first.

## 4. Public Boundary Policy

| Surface | Classification | Migration rule |
|---|---|---|
| `app.services.indicators.__all__` current singleton names | Legacy compatibility API | Preserve until downstream callers migrate. Add deprecation metadata later, not immediate removal. |
| `BaseIndicator` | Public support API | Preserve; make protocol-compatible through adapter/typing docs. |
| Helper functions in `base.py` | Public support API | Preserve; add validation/docstring/edge tests. |
| `app.services.indicators.api.*` | Official public API, new | Add wrappers returning `IndicatorResult`. No broker/data/provider reads. |
| `registry.py` operations | Official public/support API | Registry operations are official support API; custom registration must pass conformance gates. |
| Indicator class internals and private methods | Internal implementation detail | Do not call directly outside module except legacy compatibility paths. |
| `custom.smc` and other advanced/custom outputs | Legacy/custom compatibility API until reviewed | Must pass no-lookahead/conformance before official strategy-facing status. |

`__init__.py` behavior during migration:

1. Continue exporting current names.
2. Add official names only when their contract tests pass.
3. Do not initialize broker, data, cache, audit, plugin, or credential integrations.
4. Keep `__all__` explicit.
5. Add an export snapshot test so accidental public-surface changes fail CI.

## 5. Indicator/Data Boundary Contract

Indicators consume normalized historical bars/ticks or canonical Data outputs. Indicators may depend on Data contracts, schemas, and pure validation helpers when import-safe.

Indicators must not own:

- broker connections
- broker reads
- data persistence
- market-data provider routing
- live trading execution
- order lifecycle
- strategy decisions
- final risk decisions
- simulator event loop
- optimization search orchestration
- UI/API routing

Indicators own:

- indicator calculations
- formula specifications
- deterministic transforms
- parameter validation
- input schema validation for calculation safety
- output column naming
- lookback/warmup handling
- NaN/null/unavailable behavior
- no-lookahead availability metadata
- multi-output result assembly
- optional registry/catalog
- metadata/manifests for reproducibility

## 6. Implementation Sequence

| Step | Increment | Dependency-safe work order |
|---|---|---|
| 0 | Baseline freeze and audit | List actual files, exported names, current formulas, dependency imports, and test locations. Freeze current behavior with golden characterization tests before changing implementation. |
| 1 | Compatibility boundary | Preserve `app.services.indicators` imports and existing singleton objects; document official/public-support/legacy/internal API classes. |
| 2 | Core contracts and errors | Add contracts, result/manifest/error types, JSON-safe serialization, deterministic `IND_*` error mapping, and no import-time side effects. |
| 3 | Validation and naming | Centralize OHLCV column checks, duplicate-column rejection, UTC timestamp/index validation, parameter validation, input immutability checks, and output collision policy. |
| 4 | Result wrapper migration | Wrap existing Series/DataFrame outputs into `IndicatorResult` through adapters while keeping `.calculate(...)` compatibility behavior unchanged. |
| 5 | Formula specs and golden fixtures | Create formula tables and fixture baselines for SMA, EMA, WMA, Bollinger Bands, MACD, RSI, Williams %R, ATR, standard deviation, OBV, MFI, CMF, candles, HMA, SMC, and price-volume distribution. |
| 6 | Availability/no-lookahead hardening | Add metadata for warmup, source windows, and availability; quarantine or refactor any current indicator that reads future bars for decision-facing output. |
| 7 | Registry and capability matrix | Register preserved current indicators with lifecycle status and capability metadata; add deprecation/compatibility metadata. |
| 8 | Official API wrappers | Add `api.py` wrappers returning `IndicatorResult`; keep old singleton exports as compatibility API through a removal window. |
| 9 | Batch family hardening | Harden trend, volatility, momentum, volume, candle, and custom indicators in-place using shared validators and result wrappers. |
| 10 | Incremental/cache/audit extension points | Add ports and contracts only after batch contracts pass; implement concrete cache/audit/incremental behavior only where release scope approves. |
| 11 | Docs and examples | Update README, create docs/indicators standards, split pure examples from optional MT5 examples, and add migration notes. |
| 12 | Traceability closure | Fill evidence line references, complete the matrix, run lint/type/tests/coverage, and record deferrals with reasons. |

## 7. File-by-File Upgrade Map

### 7.1 Current files

| File path | Current role | Target role | Action | Requirements covered | Tests required |
|---|---|---|---|---|---|
| `app/services/indicators/__init__.py` | Public module gate currently imports classes, creates singleton instances, and exports helpers. Preserve during migration; later convert to compatibility-safe facade. | Compatibility facade and explicit public export gate. | Preserve + harden | IND-FR-004..010,047,114; IND-BR-003 | Import-safety and export snapshot tests. |
| `app/services/indicators/base.py` | BaseIndicator abstract class plus helper functions crossed_above, crossed_below, pips_to_price, balance_scaled_volume, arithmetic_average, weighted_average. | Protocol-compatible support base and pure helper home. | Preserve + harden | IND-FR-002,012..015,034..060; IND-NFR-* | Helper edge tests; type/contract tests. |
| `app/services/indicators/README.md` | Current service documentation and directory map; must be updated to brownfield boundary and migration notes. | Active module README with brownfield public API, boundaries, migration notes. | Harden | IND-FR-001,026,039,047,118,125; IND-EX-005; IND-BR-* | Documentation presence checks and link/example validation. |
| `app/services/indicators/candles/doji.py` | Existing candlestick pattern detector. Preserve; add characterization, schema, availability, and result wrapper. | Existing formula implementation hardened by shared contracts and wrappers. | Preserve + harden | IND-FR-030,034..060,064..081; IND-NFR-* | Golden formula, invalid input, NaN/warmup, immutability, output naming tests. |
| `app/services/indicators/candles/engulfing.py` | Existing candlestick pattern detector. Preserve; add characterization, schema, availability, and result wrapper. | Existing formula implementation hardened by shared contracts and wrappers. | Preserve + harden | IND-FR-030,034..060,064..081; IND-NFR-* | Golden formula, invalid input, NaN/warmup, immutability, output naming tests. |
| `app/services/indicators/candles/inside_bar.py` | Existing candlestick pattern detector. Preserve; add characterization, schema, availability, and result wrapper. | Existing formula implementation hardened by shared contracts and wrappers. | Preserve + harden | IND-FR-030,034..060,064..081; IND-NFR-* | Golden formula, invalid input, NaN/warmup, immutability, output naming tests. |
| `app/services/indicators/candles/pinbar.py` | Existing candlestick pattern detector. Preserve; add characterization, schema, availability, and result wrapper. | Existing formula implementation hardened by shared contracts and wrappers. | Preserve + harden | IND-FR-030,034..060,064..081; IND-NFR-* | Golden formula, invalid input, NaN/warmup, immutability, output naming tests. |
| `app/services/indicators/custom/hull_moving_average.py` | Existing custom/advanced moving average. Preserve as compatibility indicator; add conformance review before official status. | Custom/legacy indicators with conformance gates before official promotion. | Preserve + quarantine/harden | IND-FR-051,058,060; relevant batch family requirements | Characterization, no-lookahead, conformance, fixture tests. |
| `app/services/indicators/custom/smc.py` | Existing Smart Money Concepts implementation. Preserve but quarantine as legacy/custom until lookahead review because it uses future shifts in FVG/swing logic. | Custom/legacy indicators with conformance gates before official promotion. | Preserve + quarantine/harden | IND-FR-051,058,060; relevant batch family requirements | Characterization, no-lookahead, conformance, fixture tests. |
| `app/services/indicators/momentum/macd.py` | Existing MACD implementation returning multi-column DataFrame. | Existing formula implementation hardened by shared contracts and wrappers. | Preserve + harden | IND-FR-030,034..060,064..081; IND-NFR-* | Golden formula, invalid input, NaN/warmup, immutability, output naming tests. |
| `app/services/indicators/momentum/rsi.py` | Existing RSI implementation using Wilder-style ewm; currently replaces zero loss with epsilon. | Existing formula implementation hardened by shared contracts and wrappers. | Preserve + harden | IND-FR-030,034..060,064..081; IND-NFR-* | Golden formula, invalid input, NaN/warmup, immutability, output naming tests. |
| `app/services/indicators/momentum/will_r.py` | Existing Williams %R implementation. | Existing formula implementation hardened by shared contracts and wrappers. | Preserve + harden | IND-FR-030,034..060,064..081; IND-NFR-* | Golden formula, invalid input, NaN/warmup, immutability, output naming tests. |
| `app/services/indicators/trend/bollinger_bands.py` | Existing Bollinger Bands implementation returning multi-column DataFrame. | Existing formula implementation hardened by shared contracts and wrappers. | Preserve + harden | IND-FR-030,034..060,064..081; IND-NFR-* | Golden formula, invalid input, NaN/warmup, immutability, output naming tests. |
| `app/services/indicators/trend/ema.py` | Existing EMA implementation returning Series. | Existing formula implementation hardened by shared contracts and wrappers. | Preserve + harden | IND-FR-030,034..060,064..081; IND-NFR-* | Golden formula, invalid input, NaN/warmup, immutability, output naming tests. |
| `app/services/indicators/trend/sma.py` | Existing SMA implementation returning Series. | Existing formula implementation hardened by shared contracts and wrappers. | Preserve + harden | IND-FR-030,034..060,064..081; IND-NFR-* | Golden formula, invalid input, NaN/warmup, immutability, output naming tests. |
| `app/services/indicators/trend/wma.py` | Existing WMA implementation. | Existing formula implementation hardened by shared contracts and wrappers. | Preserve + harden | IND-FR-030,034..060,064..081; IND-NFR-* | Golden formula, invalid input, NaN/warmup, immutability, output naming tests. |
| `app/services/indicators/volatility/atr.py` | Existing ATR implementation using true range and Wilder-style ewm with explicit warmup NaNs. | Existing formula implementation hardened by shared contracts and wrappers. | Preserve + harden | IND-FR-030,034..060,064..081; IND-NFR-* | Golden formula, invalid input, NaN/warmup, immutability, output naming tests. |
| `app/services/indicators/volatility/standard_deviation.py` | Existing rolling standard deviation implementation. | Existing formula implementation hardened by shared contracts and wrappers. | Preserve + harden | IND-FR-030,034..060,064..081; IND-NFR-* | Golden formula, invalid input, NaN/warmup, immutability, output naming tests. |
| `app/services/indicators/volume/cmf.py` | Existing Chaikin Money Flow implementation. | Existing formula implementation hardened by shared contracts and wrappers. | Preserve + harden | IND-FR-030,034..060,064..081; IND-NFR-* | Golden formula, invalid input, NaN/warmup, immutability, output naming tests. |
| `app/services/indicators/volume/mfi.py` | Existing Money Flow Index implementation. | Existing formula implementation hardened by shared contracts and wrappers. | Preserve + harden | IND-FR-030,034..060,064..081; IND-NFR-* | Golden formula, invalid input, NaN/warmup, immutability, output naming tests. |
| `app/services/indicators/volume/obv.py` | Existing On-Balance Volume implementation. | Existing formula implementation hardened by shared contracts and wrappers. | Preserve + harden | IND-FR-030,034..060,064..081; IND-NFR-* | Golden formula, invalid input, NaN/warmup, immutability, output naming tests. |
| `app/services/indicators/volume/price_volume_distribution.py` | Existing price/volume distribution implementation. | Existing formula implementation hardened by shared contracts and wrappers. | Preserve + harden | IND-FR-030,034..060,064..081; IND-NFR-* | Golden formula, invalid input, NaN/warmup, immutability, output naming tests. |
| `tests/usage/03_indicator.py` | Existing runnable usage script; currently fetches MT5/data-service data and manually joins indicator outputs. | Executable documentation with pure examples and optional integration examples. | Harden | IND-EX-001..005; IND-TEST-* | Example smoke tests; optional integration skipped without credentials. |


### 7.2 Proposed/new files

| Proposed file | Action | Target role |
|---|---|---|
| `app/services/indicators/contracts.py` | Add | Typed `IndicatorConfig`, `IndicatorContext`, `IndicatorResult`, `IndicatorManifest`, `IndicatorError`, `WarmupRequirement`, and serialization helpers. |
| `app/services/indicators/errors.py` | Add | Deterministic `IND_*` exception and error-code taxonomy that wraps existing ValueError/LookupError behavior at boundaries. |
| `app/services/indicators/validation.py` | Add | Shared input-frame, parameter, naming, duplicate-column, timestamp, provenance, and non-mutation validators. |
| `app/services/indicators/availability.py` | Add | `available_at`, `computed_from_start`, `computed_from_end`, source timeframe, and no-lookahead masking helpers. |
| `app/services/indicators/registry.py` | Add | Registry/catalog with `register_indicator`, `get_indicator`, `list_indicators`, `validate_indicator`, `unregister_indicator`, capability/deprecation metadata. |
| `app/services/indicators/api.py` | Add | Official stable convenience wrappers returning `IndicatorResult`; old singleton API remains through `__init__.py` during migration. |
| `app/services/indicators/formula_specs.py` | Add | Formula specification tables for every current built-in and custom/legacy indicator. |
| `app/services/indicators/cache.py` | Add/defer | Optional cache port/service only after contracts and manifests exist; no cache at import time. |
| `app/services/indicators/audit.py` | Add/defer | Optional audit event builder and audit sink port; no durable audit ownership. |
| `app/services/indicators/incremental.py` | Add/defer | Incremental state contracts/adapters; implement after batch parity is locked. |
| `docs/indicators/design_standards.md` | Add | Brownfield design, no-lookahead, formula, naming, availability, provenance, and promotion manual. |
| `docs/indicators/requirement_evidence.md` | Add | Evidence ledger mapping each requirement to tests, docs, and implementation anchors. |
| `tests/unit/app/services/indicators/test_characterization_*.py` | Add | Golden characterization tests for existing classes and helpers before refactoring. |
| `tests/unit/app/services/indicators/test_contracts_*.py` | Add | Contract, registry, result, manifest, availability, deterministic error, and import-safety tests. |
| `tests/usage/03_indicator.py` | Harden | Keep examples but split pure synthetic examples from optional MT5/data-service examples. |

## 8. Requirement Coverage Matrix

### 8.1 Requirement group index

| Original section | Requirement range | Count | Primary current/new anchor |
|---|---|---:|---|
| Indicator Library Documentation and Design Standards | IND-FR-001 → IND-FR-001 | 1 | docs/indicators/design_standards.md; app/services/indicators/README.md |
| Package Initialization | IND-FR-002 → IND-FR-003 | 2 | app/services/indicators/__init__.py; app/services/indicators/base.py |
| Indicator Library Package Initialization | IND-FR-004 → IND-FR-006 | 3 | app/services/indicators/__init__.py |
| Indicator Registry and Registry Validation | IND-FR-007 → IND-FR-010 | 4 | app/services/indicators/__init__.py; add app/services/indicators/registry.py |
| Indicator Interface Protocols and Type Signatures | IND-FR-011 → IND-FR-027 | 17 | app/services/indicators/base.py; add contracts.py, validation.py, availability.py |
| Domain Exception Handling and Error Routing | IND-FR-028 → IND-FR-033 | 6 | current ValueError/LookupError in indicator classes; add errors.py |
| Base Mathematical Calculations | IND-FR-034 → IND-FR-060 | 27 | app/services/indicators/base.py; current built-in indicator files; add formula_specs.py |
| Batch Indicator Calculations Package | IND-FR-061 → IND-FR-063 | 3 | app/services/indicators/trend|momentum|volatility|volume|candles|custom |
| Batch Trend Indicators (Moving Averages, MACD, etc.) | IND-FR-064 → IND-FR-071 | 8 | trend/sma.py, trend/ema.py, trend/wma.py, trend/bollinger_bands.py, momentum/macd.py; ADX missing |
| Batch Volatility Indicators (ATR, Bollinger Bands, etc.) | IND-FR-072 → IND-FR-075 | 4 | volatility/atr.py, volatility/standard_deviation.py, trend/bollinger_bands.py |
| Batch Momentum Indicators (RSI, Stochastic, etc.) | IND-FR-076 → IND-FR-081 | 6 | momentum/rsi.py, momentum/macd.py, momentum/will_r.py; Stochastic missing |
| Incremental Indicator Calculations Package | IND-FR-082 → IND-FR-084 | 3 | add incremental.py; current batch classes only |
| Incremental Calculation State Tracking | IND-FR-085 → IND-FR-098 | 14 | add incremental.py, contracts.py |
| Incremental Bar Accumulators | IND-FR-099 → IND-FR-101 | 3 | add incremental.py |
| Indicator Cache/Audit Integration | IND-FR-102 → IND-FR-104 | 3 | add cache.py, audit.py |
| Indicator Cache Adapter | IND-FR-105 → IND-FR-121 | 17 | add cache.py; contracts.py; availability.py |
| Indicator Integrity Audit Trail | IND-FR-122 → IND-FR-126 | 5 | add audit.py; contracts.py |
| Deterministic indicator contract | IND-NFR-001 → IND-BR-015 | 29 | all current and proposed indicator files |

### 8.2 Complete matrix

| Original Requirement ID | Requirement Summary | Brownfield Task(s) | Current Code Anchor | Migration Action | Test/Evidence Target | Status |
|---|---|---|---|---|---|---|
| IND-FR-001 | Write the indicator library design and documentation standards before implementation begins, covering Production Scope Tiers classification, no-lookahead behavior,… | Brownfield implementation task | docs/indicators/design_standards.md; app/services/indicators/README.md | Create brownfield documentation standards and update README; include no-lookahead, naming, fixtures, custom promotion, cross-validation. | Documentation tests and README review; executable examples. | Gap / plan-ready |
| IND-FR-002 | Define the core `IndicatorProtocol.calculate(data, config, context)` typed input/output contract: `data` as a `pandas.DataFrame` for Core MVP batch execution (UTC-n… | Brownfield implementation task | app/services/indicators/__init__.py; app/services/indicators/base.py | Preserve current imports/singletons; add import-safety tests; introduce contracts without breaking old imports. | Import-time side-effect tests; public export compatibility tests. | Gap / plan-ready |
| IND-FR-003 | Define smoothing/seed conventions and numeric edge-case behavior (NaN, infinity, negative zero, overflow, underflow, divide-by-zero, floating-point tolerance) for e… | Brownfield implementation task | app/services/indicators/__init__.py; app/services/indicators/base.py | Preserve current imports/singletons; add import-safety tests; introduce contracts without breaking old imports. | Import-time side-effect tests; public export compatibility tests. | Gap / plan-ready |
| IND-FR-004 | No file-specific functional requirements defined. Foundation properties apply. | Brownfield implementation task | app/services/indicators/__init__.py | Classify as foundation/applicability task; keep package init explicit and side-effect-light. | Package import tests and export snapshot. | Foundation / explicit no-file requirement |
| IND-FR-005 | No file-specific non-functional requirements defined. | Brownfield implementation task | app/services/indicators/__init__.py | Classify as foundation/applicability task; keep package init explicit and side-effect-light. | Package import tests and export snapshot. | Foundation / explicit no-file requirement |
| IND-FR-006 | No file-specific testing requirements defined. | Brownfield implementation task | app/services/indicators/__init__.py | Classify as foundation/applicability task; keep package init explicit and side-effect-light. | Package import tests and export snapshot. | Foundation / explicit no-file requirement |
| IND-FR-007 | Implement an indicator registry exposing `register_indicator(...)`, `get_indicator(...)`, `list_indicators(...)`, `validate_indicator(...)`, and `unregister_indicat… | Brownfield implementation task | app/services/indicators/__init__.py; add app/services/indicators/registry.py | Add registry beside current classes; register existing indicators with metadata and compatibility status. | Registry operation tests; capability matrix tests; custom conformance tests. | Gap / plan-ready |
| IND-FR-008 | Define and document the public API surface and module layout: stable import paths, function/class signatures, parameter/result/error schemas, registry contracts, `t… | Brownfield implementation task | app/services/indicators/__init__.py; add app/services/indicators/registry.py | Add registry beside current classes; register existing indicators with metadata and compatibility status. | Registry operation tests; capability matrix tests; custom conformance tests. | Gap / plan-ready |
| IND-FR-009 | Generate a machine-readable capability matrix from the registry for every official indicator, covering id, version, tier, supported modes (batch, vectorized, increm… | Brownfield implementation task | app/services/indicators/__init__.py; add app/services/indicators/registry.py | Add registry beside current classes; register existing indicators with metadata and compatibility status. | Registry operation tests; capability matrix tests; custom conformance tests. | Gap / plan-ready |
| IND-FR-010 | Write tests covering registry API operations, built-in convenience function contracts, deprecation lifecycle, capability matrix accuracy, and custom indicator confo… | Brownfield implementation task | app/services/indicators/__init__.py; add app/services/indicators/registry.py | Add registry beside current classes; register existing indicators with metadata and compatibility status. | Registry operation tests; capability matrix tests; custom conformance tests. | Gap / plan-ready |
| IND-FR-011 | Define packaging, observability, resource-limit, and SLO foundations for the indicator module: standard Python/`pyproject.toml` packaging metadata, structured loggi… | Brownfield implementation task | app/services/indicators/base.py; add contracts.py, validation.py, availability.py | Evolve BaseIndicator into protocol-compatible surface through adapters; add IndicatorResult/Manifest/Config/Context without breaking `.calculate`. | Contract tests; result join/mask tests; typing and serialization tests. | Gap / plan-ready |
| IND-FR-012 | Implement the core indicator input/output behavioral contract: decision-input-only scope, required input column/schema declarations, multi-symbol/row-order/alignmen… | Brownfield implementation task | app/services/indicators/base.py; add contracts.py, validation.py, availability.py | Evolve BaseIndicator into protocol-compatible surface through adapters; add IndicatorResult/Manifest/Config/Context without breaking `.calculate`. | Contract tests; result join/mask tests; typing and serialization tests. | Gap / plan-ready |
| IND-FR-013 | Implement default-immutable, non-mutating calculation with an `IndicatorResult.join_to(input_data, mode="copy")` helper, deterministic output-column-collision handl… | Brownfield implementation task | app/services/indicators/base.py; add contracts.py, validation.py, availability.py | Evolve BaseIndicator into protocol-compatible surface through adapters; add IndicatorResult/Manifest/Config/Context without breaking `.calculate`. | Contract tests; result join/mask tests; typing and serialization tests. | Gap / plan-ready |
| IND-FR-014 | Enforce determinism and precision parity across batch, chunked, out-of-core, accelerated, and fallback execution paths, with manifests recording checksum/version/ti… | Brownfield implementation task | app/services/indicators/base.py; add contracts.py, validation.py, availability.py | Evolve BaseIndicator into protocol-compatible surface through adapters; add IndicatorResult/Manifest/Config/Context without breaking `.calculate`. | Contract tests; result join/mask tests; typing and serialization tests. | Gap / plan-ready |
| IND-FR-015 | Define `IndicatorProtocol` with required attributes (`indicator_id`, `name`, `version`, `formula_version`, `input_schema`, `parameter_schema`, `output_schema`, `war… | Brownfield implementation task | app/services/indicators/base.py; add contracts.py, validation.py, availability.py | Evolve BaseIndicator into protocol-compatible surface through adapters; add IndicatorResult/Manifest/Config/Context without breaking `.calculate`. | Contract tests; result join/mask tests; typing and serialization tests. | Gap / plan-ready |
| IND-FR-016 | Require a formula specification table for every built-in indicator (defaults, parameter ranges, source/required columns, warmup length, window inclusivity, null/deg… | Brownfield implementation task | app/services/indicators/base.py; add contracts.py, validation.py, availability.py | Evolve BaseIndicator into protocol-compatible surface through adapters; add IndicatorResult/Manifest/Config/Context without breaking `.calculate`. | Contract tests; result join/mask tests; typing and serialization tests. | Gap / plan-ready |
| IND-FR-017 | Implement no-lookahead availability metadata (`computed_from_start`, `computed_from_end`, `source_timeframe`, `available_at`) including higher-timeframe availabilit… | Brownfield implementation task | app/services/indicators/base.py; add contracts.py, validation.py, availability.py | Evolve BaseIndicator into protocol-compatible surface through adapters; add IndicatorResult/Manifest/Config/Context without breaking `.calculate`. | Contract tests; result join/mask tests; typing and serialization tests. | Gap / plan-ready |
| IND-FR-018 | Require indicator inputs to declare data provenance (price adjustment status, price source, venue/exchange/vendor/symbol-normalization/corporate-action versions) in… | Brownfield implementation task | app/services/indicators/base.py; add contracts.py, validation.py, availability.py | Evolve BaseIndicator into protocol-compatible surface through adapters; add IndicatorResult/Manifest/Config/Context without breaking `.calculate`. | Contract tests; result join/mask tests; typing and serialization tests. | Gap / plan-ready |
| IND-FR-019 | Implement idempotent incremental updates matching batch precision, fail-fast input validation at call time, indicator composition with provenance propagation, and d… | Brownfield implementation task | app/services/indicators/base.py; add contracts.py, validation.py, availability.py | Evolve BaseIndicator into protocol-compatible surface through adapters; add IndicatorResult/Manifest/Config/Context without breaking `.calculate`. | Contract tests; result join/mask tests; typing and serialization tests. | Gap / plan-ready |
| IND-FR-020 | Define a warmup-data request protocol (symbol, timeframe, lookback, indicator id, parameter set, closed-bar policy) and a higher-timeframe alignment protocol (forwa… | Brownfield implementation task | app/services/indicators/base.py; add contracts.py, validation.py, availability.py | Evolve BaseIndicator into protocol-compatible surface through adapters; add IndicatorResult/Manifest/Config/Context without breaking `.calculate`. | Contract tests; result join/mask tests; typing and serialization tests. | Gap / plan-ready |
| IND-FR-021 | Define `IndicatorConfig` to carry symbol metadata, timeframe metadata, output mode, precision policy, timezone metadata, optional microstructure quality policy, dat… | Brownfield implementation task | app/services/indicators/base.py; add contracts.py, validation.py, availability.py | Evolve BaseIndicator into protocol-compatible surface through adapters; add IndicatorResult/Manifest/Config/Context without breaking `.calculate`. | Contract tests; result join/mask tests; typing and serialization tests. | Gap / plan-ready |
| IND-FR-022 | Define the `IndicatorResult` output contract to carry the indicator values dataframe, the preserved original input, `available_at`/`label_time`/`bar_open_time`/`bar… | Brownfield implementation task | app/services/indicators/base.py; add contracts.py, validation.py, availability.py | Evolve BaseIndicator into protocol-compatible surface through adapters; add IndicatorResult/Manifest/Config/Context without breaking `.calculate`. | Contract tests; result join/mask tests; typing and serialization tests. | Gap / plan-ready |
| IND-FR-023 | Implement the standalone machine-readable indicator manifest containing `manifest_version`, `indicator_id`, `indicator_version`, `formula_version`, `output_schema_v… | Brownfield implementation task | app/services/indicators/base.py; add contracts.py, validation.py, availability.py | Evolve BaseIndicator into protocol-compatible surface through adapters; add IndicatorResult/Manifest/Config/Context without breaking `.calculate`. | Contract tests; result join/mask tests; typing and serialization tests. | Gap / plan-ready |
| IND-FR-024 | Map deterministic error codes for invalid input schema, unexpected input mutation, insufficient data, lookahead-sensitive access, unconfigured intra-bar adjustment,… | Brownfield implementation task | app/services/indicators/base.py; add contracts.py, validation.py, availability.py | Evolve BaseIndicator into protocol-compatible surface through adapters; add IndicatorResult/Manifest/Config/Context without breaking `.calculate`. | Contract tests; result join/mask tests; typing and serialization tests. | Gap / plan-ready |
| IND-FR-025 | Write the full test suite for this section: input validation, config-conflict validation, typing.Protocol compatibility, notebook representation, join helper, avail… | Brownfield implementation task | app/services/indicators/base.py; add contracts.py, validation.py, availability.py | Evolve BaseIndicator into protocol-compatible surface through adapters; add IndicatorResult/Manifest/Config/Context without breaking `.calculate`. | Contract tests; result join/mask tests; typing and serialization tests. | Gap / plan-ready |
| IND-FR-026 | Write usage examples and documentation covering normal/invalid/missing-column behavior, manifest inspection, availability filtering, multi-symbol/multi-timeframe/in… | Brownfield implementation task | app/services/indicators/base.py; add contracts.py, validation.py, availability.py | Evolve BaseIndicator into protocol-compatible surface through adapters; add IndicatorResult/Manifest/Config/Context without breaking `.calculate`. | Contract tests; result join/mask tests; typing and serialization tests. | Gap / plan-ready |
| IND-FR-027 | Confirm this subsection's done-criteria: `typing.Protocol` contracts and notebook representations, the `ema`/`join_to` example, `pyproject.toml` metadata, availabil… | Brownfield implementation task | app/services/indicators/base.py; add contracts.py, validation.py, availability.py | Evolve BaseIndicator into protocol-compatible surface through adapters; add IndicatorResult/Manifest/Config/Context without breaking `.calculate`. | Contract tests; result join/mask tests; typing and serialization tests. | Gap / plan-ready |
| IND-FR-028 | Import and reuse all standard system exceptions and error codes from `app.utils.errors` (custom indicator exceptions inherit from `app.utils.errors.Error`/`HaruQuan… | Brownfield implementation task | current ValueError/LookupError in indicator classes; add errors.py | Wrap current native exceptions in deterministic `IND_*` boundary errors; avoid raw exception leakage in official wrappers. | Error-code tests; invalid-input tests; envelope/exception-mode tests. | Gap / plan-ready |
| IND-FR-029 | Implement deterministic error/output behavior for invalid input schema, invalid parameters, insufficient data, non-monotonic/duplicate timestamps, impossible OHLCV… | Brownfield implementation task | current ValueError/LookupError in indicator classes; add errors.py | Wrap current native exceptions in deterministic `IND_*` boundary errors; avoid raw exception leakage in official wrappers. | Error-code tests; invalid-input tests; envelope/exception-mode tests. | Gap / plan-ready |
| IND-FR-030 | Deliver Core MVP deterministic batch calculation for EMA, SMA, ADX, ATR, ADR, rolling volatility, RSI, and Williams %R, including input validation, output naming, n… | Brownfield implementation task | current ValueError/LookupError in indicator classes; add errors.py | Wrap current native exceptions in deterministic `IND_*` boundary errors; avoid raw exception leakage in official wrappers. | Error-code tests; invalid-input tests; envelope/exception-mode tests. | Gap / plan-ready |
| IND-FR-031 | Map every error condition to a deterministic error code or constant: invalid request/parameters, invalid/conflicting output names/modes/naming policies, unsupported… | Brownfield implementation task | current ValueError/LookupError in indicator classes; add errors.py | Wrap current native exceptions in deterministic `IND_*` boundary errors; avoid raw exception leakage in official wrappers. | Error-code tests; invalid-input tests; envelope/exception-mode tests. | Gap / plan-ready |
| IND-FR-032 | Enforce the deprecation lifecycle for indicators/parameters/schemas/APIs: warning-with-opt-in error phase lasting at least two minor releases raising `IND_DEPRECATE… | Brownfield implementation task | current ValueError/LookupError in indicator classes; add errors.py | Wrap current native exceptions in deterministic `IND_*` boundary errors; avoid raw exception leakage in official wrappers. | Error-code tests; invalid-input tests; envelope/exception-mode tests. | Gap / plan-ready |
| IND-FR-033 | Write tests covering error-mode behavior (exception vs. `IndicatorResult.errors`), output-contract naming/collision errors, simulation-layer lookahead integration,… | Brownfield implementation task | current ValueError/LookupError in indicator classes; add errors.py | Wrap current native exceptions in deterministic `IND_*` boundary errors; avoid raw exception leakage in official wrappers. | Error-code tests; invalid-input tests; envelope/exception-mode tests. | Gap / plan-ready |
| IND-FR-034 | Implement no-lookahead masking and the `available_at` availability contract: previous-closed-bar-only decisions, deterministic caching by indicator id/parameter has… | Brownfield implementation task | app/services/indicators/base.py; current built-in indicator files; add formula_specs.py | Harden helpers and formulas in place; add formula specs, no-lookahead metadata, resource policy, provenance policy, and custom governance. | Formula parity tests; no-mutation tests; no-lookahead tests; golden fixtures. | Gap / plan-ready |
| IND-FR-035 | Implement chunked and out-of-core calculation support: window definition over rows/elapsed time/sessions/calendar time, warmup continuity preservation across chunks… | Brownfield implementation task | app/services/indicators/base.py; current built-in indicator files; add formula_specs.py | Harden helpers and formulas in place; add formula specs, no-lookahead metadata, resource policy, provenance policy, and custom governance. | Formula parity tests; no-mutation tests; no-lookahead tests; golden fixtures. | Gap / plan-ready |
| IND-FR-036 | Implement batch/incremental validation ordering and quality-flag handling: full input validation before batch output, state/new-bar validation before incremental st… | Brownfield implementation task | app/services/indicators/base.py; current built-in indicator files; add formula_specs.py | Harden helpers and formulas in place; add formula specs, no-lookahead metadata, resource policy, provenance policy, and custom governance. | Formula parity tests; no-mutation tests; no-lookahead tests; golden fixtures. | Gap / plan-ready |
| IND-FR-037 | Implement observability, tracing, and controlled-rollout support: structured operational metrics, correlation ids, OpenTelemetry-compatible distributed tracing acro… | Brownfield implementation task | app/services/indicators/base.py; current built-in indicator files; add formula_specs.py | Harden helpers and formulas in place; add formula specs, no-lookahead metadata, resource policy, provenance policy, and custom governance. | Formula parity tests; no-mutation tests; no-lookahead tests; golden fixtures. | Gap / plan-ready |
| IND-FR-038 | Write input-immutability tests verifying indicator calculations do not mutate the input dataframe by default and raise `IND_INPUT_MUTATION_DETECTED` when official c… | Brownfield implementation task | app/services/indicators/base.py; current built-in indicator files; add formula_specs.py | Harden helpers and formulas in place; add formula specs, no-lookahead metadata, resource policy, provenance policy, and custom governance. | Formula parity tests; no-mutation tests; no-lookahead tests; golden fixtures. | Gap / plan-ready |
| IND-FR-039 | Document indicator scope and packaging conventions: Python-only implementation target, indicator outputs as decision-support (not execution) artifacts, data normali… | Brownfield implementation task | app/services/indicators/base.py; current built-in indicator files; add formula_specs.py | Harden helpers and formulas in place; add formula specs, no-lookahead metadata, resource policy, provenance policy, and custom governance. | Formula parity tests; no-mutation tests; no-lookahead tests; golden fixtures. | Gap / plan-ready |
| IND-FR-040 | Enforce log redaction by default so logs do not include full market data payloads. | Brownfield implementation task | app/services/indicators/base.py; current built-in indicator files; add formula_specs.py | Harden helpers and formulas in place; add formula specs, no-lookahead metadata, resource policy, provenance policy, and custom governance. | Formula parity tests; no-mutation tests; no-lookahead tests; golden fixtures. | Gap / plan-ready |
| IND-FR-041 | Define and document default resource limits and partial-output policy: maximum rows/symbols/columns, memory budget, chunk size, and timeout (proposed Core MVP defau… | Brownfield implementation task | app/services/indicators/base.py; current built-in indicator files; add formula_specs.py | Harden helpers and formulas in place; add formula specs, no-lookahead metadata, resource policy, provenance policy, and custom governance. | Formula parity tests; no-mutation tests; no-lookahead tests; golden fixtures. | Gap / plan-ready |
| IND-FR-042 | Define dependency, packaging, and supply-chain policy: isolate optional acceleration dependencies behind extras/feature flags, maintain a lockfile or equivalent rep… | Brownfield implementation task | app/services/indicators/base.py; current built-in indicator files; add formula_specs.py | Harden helpers and formulas in place; add formula specs, no-lookahead metadata, resource policy, provenance policy, and custom governance. | Formula parity tests; no-mutation tests; no-lookahead tests; golden fixtures. | Gap / plan-ready |
| IND-FR-043 | Define numeric representation, tolerance, and SLO conventions: declared supported dtypes (`float64`, nullable floats, decimals, fixed-point), negative-zero normaliz… | Brownfield implementation task | app/services/indicators/base.py; current built-in indicator files; add formula_specs.py | Harden helpers and formulas in place; add formula specs, no-lookahead metadata, resource policy, provenance policy, and custom governance. | Formula parity tests; no-mutation tests; no-lookahead tests; golden fixtures. | Gap / plan-ready |
| IND-FR-044 | Establish the indicator module's location and ownership boundary: live under `app/services/indicators/` (DEC-029/DONE-037), provide reusable calculation primitives… | Brownfield implementation task | app/services/indicators/base.py; current built-in indicator files; add formula_specs.py | Harden helpers and formulas in place; add formula specs, no-lookahead metadata, resource policy, provenance policy, and custom governance. | Formula parity tests; no-mutation tests; no-lookahead tests; golden fixtures. | Gap / plan-ready |
| IND-FR-045 | Implement parameter validation, vectorized batch calculation, and output-shaping behavior: validate parameter ranges before calculation, accept normalized historica… | Brownfield implementation task | app/services/indicators/base.py; current built-in indicator files; add formula_specs.py | Harden helpers and formulas in place; add formula specs, no-lookahead metadata, resource policy, provenance policy, and custom governance. | Formula parity tests; no-mutation tests; no-lookahead tests; golden fixtures. | Gap / plan-ready |
| IND-FR-046 | Define numeric tolerance, reproducibility, and performance-benchmark methodology: IEEE 754 `float64` outputs with default `1e-9` relative / `1e-12` absolute toleran… | Brownfield implementation task | app/services/indicators/base.py; current built-in indicator files; add formula_specs.py | Harden helpers and formulas in place; add formula specs, no-lookahead metadata, resource policy, provenance policy, and custom governance. | Formula parity tests; no-mutation tests; no-lookahead tests; golden fixtures. | Gap / plan-ready |
| IND-FR-047 | Define public API surface and deprecation lifecycle: explicit declaration of the public surface, clear marking of private internal modules excluded from strategy/si… | Brownfield implementation task | app/services/indicators/base.py; current built-in indicator files; add formula_specs.py | Harden helpers and formulas in place; add formula specs, no-lookahead metadata, resource policy, provenance policy, and custom governance. | Formula parity tests; no-mutation tests; no-lookahead tests; golden fixtures. | Gap / plan-ready |
| IND-FR-048 | Require formula specification tables before implementation: a concrete formula specification per built-in indicator, explicit rolling-window inclusivity (left-close… | Brownfield implementation task | app/services/indicators/base.py; current built-in indicator files; add formula_specs.py | Harden helpers and formulas in place; add formula specs, no-lookahead metadata, resource policy, provenance policy, and custom governance. | Formula parity tests; no-mutation tests; no-lookahead tests; golden fixtures. | Gap / plan-ready |
| IND-FR-049 | Define calendar, session, and timezone handling: explicit trading calendars for session-aware indicators, documented weekend/holiday/half-day/DST/missing-open-close… | Brownfield implementation task | app/services/indicators/base.py; current built-in indicator files; add formula_specs.py | Harden helpers and formulas in place; add formula specs, no-lookahead metadata, resource policy, provenance policy, and custom governance. | Formula parity tests; no-mutation tests; no-lookahead tests; golden fixtures. | Gap / plan-ready |
| IND-FR-050 | Define bid/ask/mid-price indicator edge-case behavior for stub quotes, inverted markets, missing bid/ask values, and extreme spreads. | Brownfield implementation task | app/services/indicators/base.py; current built-in indicator files; add formula_specs.py | Harden helpers and formulas in place; add formula specs, no-lookahead metadata, resource policy, provenance policy, and custom governance. | Formula parity tests; no-mutation tests; no-lookahead tests; golden fixtures. | Gap / plan-ready |
| IND-FR-051 | Implement custom indicator governance: a pre-registration conformance test suite, declared status (official/experimental/deprecated/research-only) with experimental… | Brownfield implementation task | app/services/indicators/base.py; current built-in indicator files; add formula_specs.py | Harden helpers and formulas in place; add formula specs, no-lookahead metadata, resource policy, provenance policy, and custom governance. | Formula parity tests; no-mutation tests; no-lookahead tests; golden fixtures. | Gap / plan-ready |
| IND-FR-052 | Implement indicator composition validation: accept only validated acyclic indicator graphs when composition is enabled, preserve `available_at` correctly through co… | Brownfield implementation task | app/services/indicators/base.py; current built-in indicator files; add formula_specs.py | Harden helpers and formulas in place; add formula specs, no-lookahead metadata, resource policy, provenance policy, and custom governance. | Formula parity tests; no-mutation tests; no-lookahead tests; golden fixtures. | Gap / plan-ready |
| IND-FR-053 | Define the indicator module's market-data ownership boundary and higher-timeframe alignment: the module shall not own market-data fetching, source readiness, vendor… | Brownfield implementation task | app/services/indicators/base.py; current built-in indicator files; add formula_specs.py | Harden helpers and formulas in place; add formula specs, no-lookahead metadata, resource policy, provenance policy, and custom governance. | Formula parity tests; no-mutation tests; no-lookahead tests; golden fixtures. | Gap / plan-ready |
| IND-FR-054 | Require an access-control decision and approved protected packaging mechanism before executing proprietary or licensed indicator implementations. | Brownfield implementation task | app/services/indicators/base.py; current built-in indicator files; add formula_specs.py | Harden helpers and formulas in place; add formula specs, no-lookahead metadata, resource policy, provenance policy, and custom governance. | Formula parity tests; no-mutation tests; no-lookahead tests; golden fixtures. | Gap / plan-ready |
| IND-FR-055 | Define the indicator input/output/manifest record fields for Base Mathematical Calculations: normalized OHLCV (and optional tick/lower-timeframe) input data, indica… | Brownfield implementation task | app/services/indicators/base.py; current built-in indicator files; add formula_specs.py | Harden helpers and formulas in place; add formula specs, no-lookahead metadata, resource policy, provenance policy, and custom governance. | Formula parity tests; no-mutation tests; no-lookahead tests; golden fixtures. | Gap / plan-ready |
| IND-FR-056 | Support the deterministic Base Mathematical Calculations error code set: `IND_MISSING_REQUIRED_COLUMN`, `IND_OUTPUT_COLUMN_CONFLICT`, `IND_DUPLICATE_TIMESTAMP`, `IN… | Brownfield implementation task | app/services/indicators/base.py; current built-in indicator files; add formula_specs.py | Harden helpers and formulas in place; add formula specs, no-lookahead metadata, resource policy, provenance policy, and custom governance. | Formula parity tests; no-mutation tests; no-lookahead tests; golden fixtures. | Gap / plan-ready |
| IND-FR-057 | Assign a stable requirement id to every functional and non-functional requirement in this section before implementation begins. | Brownfield implementation task | app/services/indicators/base.py; current built-in indicator files; add formula_specs.py | Harden helpers and formulas in place; add formula specs, no-lookahead metadata, resource policy, provenance policy, and custom governance. | Formula parity tests; no-mutation tests; no-lookahead tests; golden fixtures. | Gap / plan-ready |
| IND-FR-058 | Write the Base Mathematical Calculations test suite covering default-parameter values/ranges, public API contract conformance, vectorized batch output, no-lookahead… | Brownfield implementation task | app/services/indicators/base.py; current built-in indicator files; add formula_specs.py | Harden helpers and formulas in place; add formula specs, no-lookahead metadata, resource policy, provenance policy, and custom governance. | Formula parity tests; no-mutation tests; no-lookahead tests; golden fixtures. | Gap / plan-ready |
| IND-FR-059 | Confirm Base Mathematical Calculations done-criteria: documented public API surface, approved Production Scope Tiers for every requirement, complete public API cont… | Brownfield implementation task | app/services/indicators/base.py; current built-in indicator files; add formula_specs.py | Harden helpers and formulas in place; add formula specs, no-lookahead metadata, resource policy, provenance policy, and custom governance. | Formula parity tests; no-mutation tests; no-lookahead tests; golden fixtures. | Gap / plan-ready |
| IND-FR-060 | Classify Base Mathematical Calculations scope into Core MVP, Optional Extension, and Future Improvement tiers: halt Core MVP coding until `IND-PREQ-001`–`IND-PREQ-0… | Brownfield implementation task | app/services/indicators/base.py; current built-in indicator files; add formula_specs.py | Harden helpers and formulas in place; add formula specs, no-lookahead metadata, resource policy, provenance policy, and custom governance. | Formula parity tests; no-mutation tests; no-lookahead tests; golden fixtures. | Gap / plan-ready |
| IND-FR-061 | No file-specific functional requirements defined. Foundation properties apply. | Brownfield implementation task | app/services/indicators/trend|momentum|volatility|volume|candles|custom | Preserve current batch indicators as baseline; add shared batch execution adapter returning IndicatorResult. | Batch family characterization and contract tests. | Foundation / explicit no-file requirement |
| IND-FR-062 | No file-specific non-functional requirements defined. | Brownfield implementation task | app/services/indicators/trend|momentum|volatility|volume|candles|custom | Preserve current batch indicators as baseline; add shared batch execution adapter returning IndicatorResult. | Batch family characterization and contract tests. | Foundation / explicit no-file requirement |
| IND-FR-063 | No file-specific testing requirements defined. | Brownfield implementation task | app/services/indicators/trend|momentum|volatility|volume|candles|custom | Preserve current batch indicators as baseline; add shared batch execution adapter returning IndicatorResult. | Batch family characterization and contract tests. | Foundation / explicit no-file requirement |
| IND-FR-064 | Implement EMA, SMA, and ADX trend indicators with documented examples covering EMA/SMA trend signals, ATR volatility sizing inputs, RSI momentum signals, vectorized… | Brownfield implementation task | trend/sma.py, trend/ema.py, trend/wma.py, trend/bollinger_bands.py, momentum/macd.py; ADX missing | Harden existing trend indicators; add ADX or explicitly defer; normalize output naming and warmup metadata. | SMA/EMA/WMA/Bollinger/MACD golden tests; ADX gap test/deferral. | Partially covered by existing formulas; hardening required |
| IND-FR-065 | Keep indicator APIs separate from strategy/simulation execution services, reusable across notebook/CLI/agentic/simulation workflows without semantic changes, with o… | Brownfield implementation task | trend/sma.py, trend/ema.py, trend/wma.py, trend/bollinger_bands.py, momentum/macd.py; ADX missing | Harden existing trend indicators; add ADX or explicitly defer; normalize output naming and warmup metadata. | SMA/EMA/WMA/Bollinger/MACD golden tests; ADX gap test/deferral. | Partially covered by existing formulas; hardening required |
| IND-FR-066 | Implement deterministic output column naming for trend indicators: default-source naming (`ema_10`), non-default-source naming (`ema_open_10`), deterministic multi-… | Brownfield implementation task | trend/sma.py, trend/ema.py, trend/wma.py, trend/bollinger_bands.py, momentum/macd.py; ADX missing | Harden existing trend indicators; add ADX or explicitly defer; normalize output naming and warmup metadata. | SMA/EMA/WMA/Bollinger/MACD golden tests; ADX gap test/deferral. | Partially covered by existing formulas; hardening required |
| IND-FR-067 | Implement API/schema versioning and deprecation lifecycle: semantic-versioned public API changes, major-version bump or migration path for backward-incompatible cha… | Brownfield implementation task | trend/sma.py, trend/ema.py, trend/wma.py, trend/bollinger_bands.py, momentum/macd.py; ADX missing | Harden existing trend indicators; add ADX or explicitly defer; normalize output naming and warmup metadata. | SMA/EMA/WMA/Bollinger/MACD golden tests; ADX gap test/deferral. | Gap / plan-ready |
| IND-FR-068 | Require every trend indicator to define its exact mathematical formula with the HaruQuant formula specification as the source of truth over third-party library conv… | Brownfield implementation task | trend/sma.py, trend/ema.py, trend/wma.py, trend/bollinger_bands.py, momentum/macd.py; ADX missing | Harden existing trend indicators; add ADX or explicitly defer; normalize output naming and warmup metadata. | SMA/EMA/WMA/Bollinger/MACD golden tests; ADX gap test/deferral. | Gap / plan-ready |
| IND-FR-069 | Write trend indicator tests covering deterministic output naming (default/non-default source, multi-output components), cross-library validation of EMA/SMA/RSI/ATR/… | Brownfield implementation task | trend/sma.py, trend/ema.py, trend/wma.py, trend/bollinger_bands.py, momentum/macd.py; ADX missing | Harden existing trend indicators; add ADX or explicitly defer; normalize output naming and warmup metadata. | SMA/EMA/WMA/Bollinger/MACD golden tests; ADX gap test/deferral. | Gap / plan-ready |
| IND-FR-070 | Write and maintain executable trend-indicator usage examples and documentation covering API usage (`ema(...)` + `result.join_to(data)`), versioning/migration policy… | Brownfield implementation task | trend/sma.py, trend/ema.py, trend/wma.py, trend/bollinger_bands.py, momentum/macd.py; ADX missing | Harden existing trend indicators; add ADX or explicitly defer; normalize output naming and warmup metadata. | SMA/EMA/WMA/Bollinger/MACD golden tests; ADX gap test/deferral. | Gap / plan-ready |
| IND-FR-071 | Allow proprietary source protection to be added through approved packaging/security controls without changing public indicator semantics. | Brownfield implementation task | trend/sma.py, trend/ema.py, trend/wma.py, trend/bollinger_bands.py, momentum/macd.py; ADX missing | Harden existing trend indicators; add ADX or explicitly defer; normalize output naming and warmup metadata. | SMA/EMA/WMA/Bollinger/MACD golden tests; ADX gap test/deferral. | Gap / plan-ready |
| IND-FR-072 | Implement ATR, ADR, and rolling volatility with typed convenience-function wrappers for all official built-ins (`ema`, `sma`, `adx`, `atr`, `adr`, `rolling_volatili… | Brownfield implementation task | volatility/atr.py, volatility/standard_deviation.py, trend/bollinger_bands.py | Harden volatility calculations, warmups, NaN/zero behavior, and output metadata. | ATR/std/Bollinger golden tests and degenerate-window tests. | Partially covered by existing formulas; hardening required |
| IND-FR-073 | Complete and approve formula specification tables for EMA, SMA, ADX, ATR, ADR, rolling volatility, RSI, and Williams %R before implementation begins. | Brownfield implementation task | volatility/atr.py, volatility/standard_deviation.py, trend/bollinger_bands.py | Harden volatility calculations, warmups, NaN/zero behavior, and output metadata. | ATR/std/Bollinger golden tests and degenerate-window tests. | Partially covered by existing formulas; hardening required |
| IND-FR-074 | Write the volatility-indicator test suite: coverage for EMA/SMA/ADX/ATR/ADR/rolling volatility/RSI/Williams %R; golden tests for exact formula conventions, seed beh… | Brownfield implementation task | volatility/atr.py, volatility/standard_deviation.py, trend/bollinger_bands.py | Harden volatility calculations, warmups, NaN/zero behavior, and output metadata. | ATR/std/Bollinger golden tests and degenerate-window tests. | Gap / plan-ready |
| IND-FR-075 | Build and document a requirement-to-test traceability matrix mapping every requirement id to unit, contract, integration, performance, security, or documentation te… | Brownfield implementation task | volatility/atr.py, volatility/standard_deviation.py, trend/bollinger_bands.py | Harden volatility calculations, warmups, NaN/zero behavior, and output metadata. | ATR/std/Bollinger golden tests and degenerate-window tests. | Gap / plan-ready |
| IND-FR-076 | Implement RSI and Williams %R momentum indicators, defining Williams %R behavior when highest high equals lowest low. | Brownfield implementation task | momentum/rsi.py, momentum/macd.py, momentum/will_r.py; Stochastic missing | Harden current momentum indicators; add Stochastic or explicitly defer; document RSI zero-loss behavior. | RSI/MACD/Williams %R tests; Stochastic gap test/deferral. | Partially covered by existing formulas; hardening required |
| IND-FR-077 | Declare and version-constrain runtime dependencies, and document Python/dependency versions (NumPy, pandas, optional acceleration libraries) used in performance ben… | Brownfield implementation task | momentum/rsi.py, momentum/macd.py, momentum/will_r.py; Stochastic missing | Harden current momentum indicators; add Stochastic or explicitly defer; document RSI zero-loss behavior. | RSI/MACD/Williams %R tests; Stochastic gap test/deferral. | Partially covered by existing formulas; hardening required |
| IND-FR-078 | Confine timezone-database-dependent conversions to I/O boundaries, recording the timezone database version or conversion policy when available. | Brownfield implementation task | momentum/rsi.py, momentum/macd.py, momentum/will_r.py; Stochastic missing | Harden current momentum indicators; add Stochastic or explicitly defer; document RSI zero-loss behavior. | RSI/MACD/Williams %R tests; Stochastic gap test/deferral. | Gap / plan-ready |
| IND-FR-079 | Implement access-control checks validating actor, workflow, entitlement, environment, indicator id, indicator version, and intended use before calculation begins. | Brownfield implementation task | momentum/rsi.py, momentum/macd.py, momentum/will_r.py; Stochastic missing | Harden current momentum indicators; add Stochastic or explicitly defer; document RSI zero-loss behavior. | RSI/MACD/Williams %R tests; Stochastic gap test/deferral. | Gap / plan-ready |
| IND-FR-080 | Define the canonical parameter-hashing representation (key ordering, defaults, omitted optional values, numeric formatting, null representation, string normalizatio… | Brownfield implementation task | momentum/rsi.py, momentum/macd.py, momentum/will_r.py; Stochastic missing | Harden current momentum indicators; add Stochastic or explicitly defer; document RSI zero-loss behavior. | RSI/MACD/Williams %R tests; Stochastic gap test/deferral. | Gap / plan-ready |
| IND-FR-081 | Review and pin reference outputs by implementation version, requiring formula justification, implementation-version pinning, golden fixture approval, and a changelo… | Brownfield implementation task | momentum/rsi.py, momentum/macd.py, momentum/will_r.py; Stochastic missing | Harden current momentum indicators; add Stochastic or explicitly defer; document RSI zero-loss behavior. | RSI/MACD/Williams %R tests; Stochastic gap test/deferral. | Gap / plan-ready |
| IND-FR-082 | No file-specific functional requirements defined. Foundation properties apply. | Brownfield implementation task | add incremental.py; current batch classes only | Do not retrofit state before contracts; define incremental interface and defer implementations until batch parity exists. | Incremental contract and deferral tests. | Foundation / explicit no-file requirement |
| IND-FR-083 | No file-specific non-functional requirements defined. | Brownfield implementation task | add incremental.py; current batch classes only | Do not retrofit state before contracts; define incremental interface and defer implementations until batch parity exists. | Incremental contract and deferral tests. | Foundation / explicit no-file requirement |
| IND-FR-084 | No file-specific testing requirements defined. | Brownfield implementation task | add incremental.py; current batch classes only | Do not retrofit state before contracts; define incremental interface and defer implementations until batch parity exists. | Incremental contract and deferral tests. | Foundation / explicit no-file requirement |
| IND-FR-085 | Keep the indicator module's ownership boundary fail-closed: fills, orders, account state, journals, and reports remain owned by the simulation module, and the indic… | Brownfield implementation task | add incremental.py, contracts.py | Add state serialization/idempotency contracts; implement per-indicator only after batch wrappers stabilize. | State serialization, compatibility, corruption, parity, and concurrency tests. | Gap / plan-ready |
| IND-FR-086 | Require vectorized official batch calculation (per-row Python loops only for documented unvectorizable stateful formulas), prohibit hidden global mutable state, and… | Brownfield implementation task | add incremental.py, contracts.py | Add state serialization/idempotency contracts; implement per-indicator only after batch wrappers stabilize. | State serialization, compatibility, corruption, parity, and concurrency tests. | Gap / plan-ready |
| IND-FR-087 | Expose the public incremental-calculation type surface (`IndicatorProtocol`, `IndicatorConfig`, `IndicatorContext`, `IndicatorResult`, `IndicatorManifest`, `Indicat… | Brownfield implementation task | add incremental.py, contracts.py | Add state serialization/idempotency contracts; implement per-indicator only after batch wrappers stabilize. | State serialization, compatibility, corruption, parity, and concurrency tests. | Gap / plan-ready |
| IND-FR-088 | Document each indicator's smoothing convention (e.g. whether RSI/ATR/ADX use Wilder smoothing) and its Production Scope Tier (Core MVP, Official Backtest Required,… | Brownfield implementation task | add incremental.py, contracts.py | Add state serialization/idempotency contracts; implement per-indicator only after batch wrappers stabilize. | State serialization, compatibility, corruption, parity, and concurrency tests. | Gap / plan-ready |
| IND-FR-089 | Preserve incremental indicator state continuity across symbol-mapping events (mergers, ticker replacements, vendor remaps) for equivalent instrument identities, res… | Brownfield implementation task | add incremental.py, contracts.py | Add state serialization/idempotency contracts; implement per-indicator only after batch wrappers stabilize. | State serialization, compatibility, corruption, parity, and concurrency tests. | Gap / plan-ready |
| IND-FR-090 | Implement the serializable incremental state contract: a documented binary or text serialization format containing indicator id, implementation version, state schem… | Brownfield implementation task | add incremental.py, contracts.py | Add state serialization/idempotency contracts; implement per-indicator only after batch wrappers stabilize. | State serialization, compatibility, corruption, parity, and concurrency tests. | Gap / plan-ready |
| IND-FR-091 | Implement deserialization compatibility validation returning `IND_STATE_INCOMPATIBLE` for mismatched indicator id/version/schema/parameters and `IND_STATE_CORRUPTED… | Brownfield implementation task | add incremental.py, contracts.py | Add state serialization/idempotency contracts; implement per-indicator only after batch wrappers stabilize. | State serialization, compatibility, corruption, parity, and concurrency tests. | Gap / plan-ready |
| IND-FR-092 | Require indicators to consume warmup data for calculation state without emitting warmup-period output rows unless explicitly marked as warmup. | Brownfield implementation task | add incremental.py, contracts.py | Add state serialization/idempotency contracts; implement per-indicator only after batch wrappers stabilize. | State serialization, compatibility, corruption, parity, and concurrency tests. | Gap / plan-ready |
| IND-FR-093 | Require unauthorized proprietary indicator requests to fail before input data is read, state is deserialized, cache entries are read, or calculation begins. | Brownfield implementation task | add incremental.py, contracts.py | Add state serialization/idempotency contracts; implement per-indicator only after batch wrappers stabilize. | State serialization, compatibility, corruption, parity, and concurrency tests. | Gap / plan-ready |
| IND-FR-094 | Define the incremental concurrency/thread-safety model: stateless functions thread-safe by default, stateful incremental indicators documented as single-owner (not… | Brownfield implementation task | add incremental.py, contracts.py | Add state serialization/idempotency contracts; implement per-indicator only after batch wrappers stabilize. | State serialization, compatibility, corruption, parity, and concurrency tests. | Gap / plan-ready |
| IND-FR-095 | Document incremental-state serialization/idempotency/late-arriving/corrected/revised/out-of-order behavior, state format/compatibility/corruption handling/bounded s… | Brownfield implementation task | add incremental.py, contracts.py | Add state serialization/idempotency contracts; implement per-indicator only after batch wrappers stabilize. | State serialization, compatibility, corruption, parity, and concurrency tests. | Gap / plan-ready |
| IND-FR-096 | Confirm debug-mode strict typing/runtime validation fails before calculation or state mutation, and that incremental state compatibility/corruption tests pass. | Brownfield implementation task | add incremental.py, contracts.py | Add state serialization/idempotency contracts; implement per-indicator only after batch wrappers stabilize. | State serialization, compatibility, corruption, parity, and concurrency tests. | Gap / plan-ready |
| IND-FR-097 | Require `IndicatorManifest`, `IndicatorState`, and `IndicatorError` to have exact serialized field contracts approved before implementation begins. | Brownfield implementation task | add incremental.py, contracts.py | Add state serialization/idempotency contracts; implement per-indicator only after batch wrappers stabilize. | State serialization, compatibility, corruption, parity, and concurrency tests. | Gap / plan-ready |
| IND-FR-098 | Write the incremental-state test suite: input-validation-timing tests (parameter/schema/data-sufficiency/state-deserialization/new-bar validation failing before cal… | Brownfield implementation task | add incremental.py, contracts.py | Add state serialization/idempotency contracts; implement per-indicator only after batch wrappers stabilize. | State serialization, compatibility, corruption, parity, and concurrency tests. | Gap / plan-ready |
| IND-FR-099 | No file-specific functional requirements defined. Foundation properties apply. | Brownfield implementation task | add incremental.py | Treat as foundation/extension; no concrete accumulator until requirements and batch wrappers pass. | Accumulator contract tests or approved deferral. | Foundation / explicit no-file requirement |
| IND-FR-100 | No file-specific non-functional requirements defined. | Brownfield implementation task | add incremental.py | Treat as foundation/extension; no concrete accumulator until requirements and batch wrappers pass. | Accumulator contract tests or approved deferral. | Foundation / explicit no-file requirement |
| IND-FR-101 | No file-specific testing requirements defined. | Brownfield implementation task | add incremental.py | Treat as foundation/extension; no concrete accumulator until requirements and batch wrappers pass. | Accumulator contract tests or approved deferral. | Foundation / explicit no-file requirement |
| IND-FR-102 | No file-specific functional requirements defined. Foundation properties apply. | Brownfield implementation task | add cache.py, audit.py | Keep cache/audit as optional ports; no import-time adapter setup or durable storage ownership. | Import-safety and port-contract tests. | Foundation / explicit no-file requirement |
| IND-FR-103 | No file-specific non-functional requirements defined. | Brownfield implementation task | add cache.py, audit.py | Keep cache/audit as optional ports; no import-time adapter setup or durable storage ownership. | Import-safety and port-contract tests. | Foundation / explicit no-file requirement |
| IND-FR-104 | No file-specific testing requirements defined. | Brownfield implementation task | add cache.py, audit.py | Keep cache/audit as optional ports; no import-time adapter setup or durable storage ownership. | Import-safety and port-contract tests. | Foundation / explicit no-file requirement |
| IND-FR-105 | Implement deterministic cache-hit behavior with policy-driven degradation: cache hits never reuse results across incompatible input data, parameter sets, implementa… | Brownfield implementation task | add cache.py; contracts.py; availability.py | Implement deterministic cache keys, invalidation, best-effort/strict policy, metrics, and resource limits only after manifest exists. | Cache hit/miss/invalidation/atomic-write/resource tests. | Gap / plan-ready |
| IND-FR-106 | Define and benchmark latency/SLO targets: uncached first-run p99 ≤ 5 seconds for 10 years × 10 symbols of M1 bars, warm-cache batch p99 ≤ 250 ms for up to 10 symbol… | Brownfield implementation task | add cache.py; contracts.py; availability.py | Implement deterministic cache keys, invalidation, best-effort/strict policy, metrics, and resource limits only after manifest exists. | Cache hit/miss/invalidation/atomic-write/resource tests. | Gap / plan-ready |
| IND-FR-107 | Implement out-of-core and parallel-execution cache integrity: preserve warmup continuity, symbol grouping, timestamp ordering, provenance metadata, and cache-key de… | Brownfield implementation task | add cache.py; contracts.py; availability.py | Implement deterministic cache keys, invalidation, best-effort/strict policy, metrics, and resource limits only after manifest exists. | Cache hit/miss/invalidation/atomic-write/resource tests. | Gap / plan-ready |
| IND-FR-108 | Define `IndicatorConfig` to carry indicator id, parameters, source column, output naming policy, output mode, column conflict policy, precision policy, cache policy… | Brownfield implementation task | add cache.py; contracts.py; availability.py | Implement deterministic cache keys, invalidation, best-effort/strict policy, metrics, and resource limits only after manifest exists. | Cache hit/miss/invalidation/atomic-write/resource tests. | Gap / plan-ready |
| IND-FR-109 | Normalize all internal timestamp arithmetic and cache keys to UTC, and record deterministic intra-bar adjustment policies in the indicator manifest with parity acro… | Brownfield implementation task | add cache.py; contracts.py; availability.py | Implement deterministic cache keys, invalidation, best-effort/strict policy, metrics, and resource limits only after manifest exists. | Cache hit/miss/invalidation/atomic-write/resource tests. | Gap / plan-ready |
| IND-FR-110 | Implement cache-key ownership for composed indicators: support composition in the cache layer, with the indicator module owning cache-key derivation and downstream… | Brownfield implementation task | add cache.py; contracts.py; availability.py | Implement deterministic cache keys, invalidation, best-effort/strict policy, metrics, and resource limits only after manifest exists. | Cache hit/miss/invalidation/atomic-write/resource tests. | Gap / plan-ready |
| IND-FR-111 | Require any proprietary-source protection mechanism to remain outside the public API contract without changing deterministic outputs, error behavior, manifest conte… | Brownfield implementation task | add cache.py; contracts.py; availability.py | Implement deterministic cache keys, invalidation, best-effort/strict policy, metrics, and resource limits only after manifest exists. | Cache hit/miss/invalidation/atomic-write/resource tests. | Gap / plan-ready |
| IND-FR-112 | Define the cache/SLO/benchmark manifest and config fields: optional cache policy; optional SLO configuration (latency/cache-hit/error-rate/timeout-rate targets, mea… | Brownfield implementation task | add cache.py; contracts.py; availability.py | Implement deterministic cache keys, invalidation, best-effort/strict policy, metrics, and resource limits only after manifest exists. | Cache hit/miss/invalidation/atomic-write/resource tests. | Gap / plan-ready |
| IND-FR-113 | Return deterministic error codes for resource-limit, timeout, cancellation, partial-result, cache-write, unsupported-out-of-core, unavailable-acceleration-backend,… | Brownfield implementation task | add cache.py; contracts.py; availability.py | Implement deterministic cache keys, invalidation, best-effort/strict policy, metrics, and resource limits only after manifest exists. | Cache hit/miss/invalidation/atomic-write/resource tests. | Gap / plan-ready |
| IND-FR-114 | Enforce side-effect-free import: importing `app.services.indicators` shall perform no network I/O, filesystem writes, cache writes, plugin execution, long-running c… | Brownfield implementation task | add cache.py; contracts.py; availability.py | Implement deterministic cache keys, invalidation, best-effort/strict policy, metrics, and resource limits only after manifest exists. | Cache hit/miss/invalidation/atomic-write/resource tests. | Gap / plan-ready |
| IND-FR-115 | Emit observability metrics and trace spans for cache/calculation behavior: metrics covering calculation duration, row/symbol counts, cache hit/miss, memory usage es… | Brownfield implementation task | add cache.py; contracts.py; availability.py | Implement deterministic cache keys, invalidation, best-effort/strict policy, metrics, and resource limits only after manifest exists. | Cache hit/miss/invalidation/atomic-write/resource tests. | Gap / plan-ready |
| IND-FR-116 | Implement atomic, thread-safe cache writes and graceful degradation under pressure: atomic writes that never corrupt existing valid entries; documented behavior und… | Brownfield implementation task | add cache.py; contracts.py; availability.py | Implement deterministic cache keys, invalidation, best-effort/strict policy, metrics, and resource limits only after manifest exists. | Cache hit/miss/invalidation/atomic-write/resource tests. | Gap / plan-ready |
| IND-FR-117 | Run the full indicator correctness, determinism, no-lookahead, cache, and benchmark regression suite on every dependency upgrade. | Brownfield implementation task | add cache.py; contracts.py; availability.py | Implement deterministic cache keys, invalidation, best-effort/strict policy, metrics, and resource limits only after manifest exists. | Cache hit/miss/invalidation/atomic-write/resource tests. | Gap / plan-ready |
| IND-FR-118 | Write and maintain documentation covering: public API contract tables (import paths, signatures, defaults, schemas, error behavior, side effects, cache behavior, st… | Brownfield implementation task | add cache.py; contracts.py; availability.py | Implement deterministic cache keys, invalidation, best-effort/strict policy, metrics, and resource limits only after manifest exists. | Cache hit/miss/invalidation/atomic-write/resource tests. | Gap / plan-ready |
| IND-FR-119 | Confirm cache-adapter done-criteria: UTC normalization implemented and tested; thread-safety/cache-concurrency tests pass; parallel symbol execution and cache synch… | Brownfield implementation task | add cache.py; contracts.py; availability.py | Implement deterministic cache keys, invalidation, best-effort/strict policy, metrics, and resource limits only after manifest exists. | Cache hit/miss/invalidation/atomic-write/resource tests. | Gap / plan-ready |
| IND-FR-120 | Classify cache-adapter scope: out-of-core processing as Optional Extension pending chunking-parity and cache-integrity approval, and canary routing/distributed trac… | Brownfield implementation task | add cache.py; contracts.py; availability.py | Implement deterministic cache keys, invalidation, best-effort/strict policy, metrics, and resource limits only after manifest exists. | Cache hit/miss/invalidation/atomic-write/resource tests. | Gap / plan-ready |
| IND-FR-121 | Write the cache-adapter test suite: UTC-normalization tests; cache hit/miss/version/parameter/checksum-change tests; atomic-write and interrupted-write tests; degra… | Brownfield implementation task | add cache.py; contracts.py; availability.py | Implement deterministic cache keys, invalidation, best-effort/strict policy, metrics, and resource limits only after manifest exists. | Cache hit/miss/invalidation/atomic-write/resource tests. | Gap / plan-ready |
| IND-FR-122 | Define `IndicatorManifest` to carry calculation identity, formula identity, input checksum, output checksum, parameter hash, output schema version, output column co… | Brownfield implementation task | add audit.py; contracts.py | Emit manifest-derived audit entries through injected sink; no external audit storage ownership. | Audit entry, manifest, HMAC/chain-policy, and no-output-change tests. | Gap / plan-ready |
| IND-FR-123 | Implement audit-mode entry generation: official simulation/production workflows may require audit entries; when audit mode is enabled (`audit_mode=true` or workflow… | Brownfield implementation task | add audit.py; contracts.py | Emit manifest-derived audit entries through injected sink; no external audit storage ownership. | Audit entry, manifest, HMAC/chain-policy, and no-output-change tests. | Gap / plan-ready |
| IND-FR-124 | Require approval of the Audit Policy appendix (chained SHA-256 HMAC with managed signing-key handling, or a tamper-evident Merkle-tree policy) defining append-only… | Brownfield implementation task | add audit.py; contracts.py | Emit manifest-derived audit entries through injected sink; no external audit storage ownership. | Audit entry, manifest, HMAC/chain-policy, and no-output-change tests. | Gap / plan-ready |
| IND-FR-125 | Document audit mode, audit entry structure, tamper-evident integrity, and audit metadata. | Brownfield implementation task | add audit.py; contracts.py | Emit manifest-derived audit entries through injected sink; no external audit storage ownership. | Audit entry, manifest, HMAC/chain-policy, and no-output-change tests. | Gap / plan-ready |
| IND-FR-126 | Write the audit-trail test suite verifying audit entries include the full manifest, request metadata, input checksum, output checksum, append-only behavior, tamper-… | Brownfield implementation task | add audit.py; contracts.py | Emit manifest-derived audit entries through injected sink; no external audit storage ownership. | Audit entry, manifest, HMAC/chain-policy, and no-output-change tests. | Gap / plan-ready |
| IND-NFR-001 | Adopt the Phase 1.5 `IndicatorResult` contract for all public indicator outputs. | Cross-cutting non-functional gate | all current and proposed indicator files | Apply across whole module as acceptance/NFR/example requirements. | Full traceability, coverage, examples, import, docs, and release-gate evidence. | Acceptance gate / pending evidence |
| IND-NFR-002 | Enforce a no-lookahead rule for every batch and streaming indicator. | Cross-cutting non-functional gate | all current and proposed indicator files | Apply across whole module as acceptance/NFR/example requirements. | Full traceability, coverage, examples, import, docs, and release-gate evidence. | Acceptance gate / pending evidence |
| IND-NFR-003 | Expose warmup period, required input columns, minimum bars, parameter hash, input hash, and output metadata for every indicator. | Cross-cutting non-functional gate | all current and proposed indicator files | Apply across whole module as acceptance/NFR/example requirements. | Full traceability, coverage, examples, import, docs, and release-gate evidence. | Acceptance gate / pending evidence |
| IND-NFR-004 | Ensure identical inputs and parameters produce identical outputs in research, strategy, simulation, optimization, and live contexts. | Cross-cutting non-functional gate | all current and proposed indicator files | Apply across whole module as acceptance/NFR/example requirements. | Full traceability, coverage, examples, import, docs, and release-gate evidence. | Acceptance gate / pending evidence |
| IND-NFR-005 | Define deterministic NaN, missing-value, timezone, duplicate-timestamp, and insufficient-history behavior for every indicator. | Cross-cutting non-functional gate | all current and proposed indicator files | Apply across whole module as acceptance/NFR/example requirements. | Full traceability, coverage, examples, import, docs, and release-gate evidence. | Acceptance gate / pending evidence |
| IND-NFR-006 | Add shared golden-dataset regression tests proving indicator parity across batch and streaming paths where both exist. | Cross-cutting non-functional gate | all current and proposed indicator files | Apply across whole module as acceptance/NFR/example requirements. | Full traceability, coverage, examples, import, docs, and release-gate evidence. | Acceptance gate / pending evidence |
| IND-TEST-001 | Cover every requirement in this phase with normal, edge, invalid-input, fail-closed, logging, schema, and regression tests as applicable. | Verification gate | all current and proposed indicator files | Apply across whole module as acceptance/NFR/example requirements. | Full traceability, coverage, examples, import, docs, and release-gate evidence. | Acceptance gate / pending evidence |
| IND-TEST-002 | Preserve the project gate of at least 80% coverage for each affected file and package. | Verification gate | all current and proposed indicator files | Apply across whole module as acceptance/NFR/example requirements. | Full traceability, coverage, examples, import, docs, and release-gate evidence. | Acceptance gate / pending evidence |
| IND-TEST-003 | Verify standard envelopes, deterministic error codes, import behavior, and ownership boundaries. | Verification gate | all current and proposed indicator files | Apply across whole module as acceptance/NFR/example requirements. | Full traceability, coverage, examples, import, docs, and release-gate evidence. | Acceptance gate / pending evidence |
| IND-EX-001 | The single usage file must be runnable as a script and organize separate examples as focused functions. | Example/documentation gate | all current and proposed indicator files | Apply across whole module as acceptance/NFR/example requirements. | Full traceability, coverage, examples, import, docs, and release-gate evidence. | Partially covered by current README/usage; update required |
| IND-EX-002 | Examples must extensively cover the phase's official public capabilities, important edge cases, fail-closed paths, and standard envelope fields where applicable. | Example/documentation gate | all current and proposed indicator files | Apply across whole module as acceptance/NFR/example requirements. | Full traceability, coverage, examples, import, docs, and release-gate evidence. | Gap / plan-ready |
| IND-EX-003 | Log calls, validation failures, success, exception paths, and governed/fail-closed decisions with redacted metadata only. | Example/documentation gate | all current and proposed indicator files | Apply across whole module as acceptance/NFR/example requirements. | Full traceability, coverage, examples, import, docs, and release-gate evidence. | Partially covered by current README/usage; update required |
| IND-EX-004 | All Python modules and public functions/classes must have appropriate file-level and Google-style docstrings. | Example/documentation gate | all current and proposed indicator files | Apply across whole module as acceptance/NFR/example requirements. | Full traceability, coverage, examples, import, docs, and release-gate evidence. | Partially covered by current README/usage; update required |
| IND-EX-005 | Update module README and active documentation for any architecture or API changes. | Example/documentation gate | all current and proposed indicator files | Apply across whole module as acceptance/NFR/example requirements. | Full traceability, coverage, examples, import, docs, and release-gate evidence. | Partially covered by current README/usage; update required |
| IND-BR-001 | Done criterion: All 737 checkbox tasks are implemented or explicitly deferred with a documented reason. | Builder readiness/definition-of-done gate | all current and proposed indicator files | Apply across whole module as acceptance/NFR/example requirements. | Full traceability, coverage, examples, import, docs, and release-gate evidence. | Acceptance gate / pending evidence |
| IND-BR-002 | Done criterion: Scope stayed within this phase and approved dependency surfaces. | Builder readiness/definition-of-done gate | all current and proposed indicator files | Apply across whole module as acceptance/NFR/example requirements. | Full traceability, coverage, examples, import, docs, and release-gate evidence. | Acceptance gate / pending evidence |
| IND-BR-003 | Done criterion: Public exports match the phase registry rules and do not expose unapproved helpers. | Builder readiness/definition-of-done gate | all current and proposed indicator files | Apply across whole module as acceptance/NFR/example requirements. | Full traceability, coverage, examples, import, docs, and release-gate evidence. | Acceptance gate / pending evidence |
| IND-BR-004 | Done criterion: Standard envelopes, metadata, request IDs, error codes, logging, and redaction rules are satisfied where applicable. | Builder readiness/definition-of-done gate | all current and proposed indicator files | Apply across whole module as acceptance/NFR/example requirements. | Full traceability, coverage, examples, import, docs, and release-gate evidence. | Acceptance gate / pending evidence |
| IND-BR-005 | Done criterion: Unit tests, usage examples, static typing, linting, formatting, and coverage gates pass. | Builder readiness/definition-of-done gate | all current and proposed indicator files | Apply across whole module as acceptance/NFR/example requirements. | Full traceability, coverage, examples, import, docs, and release-gate evidence. | Acceptance gate / pending evidence |
| IND-BR-006 | Done criterion: Active docs and changelog are updated for any implemented project meaning changes. | Builder readiness/definition-of-done gate | all current and proposed indicator files | Apply across whole module as acceptance/NFR/example requirements. | Full traceability, coverage, examples, import, docs, and release-gate evidence. | Acceptance gate / pending evidence |
| IND-BR-007 | Done criterion: Rollback path and implementation report are recorded before handoff. | Builder readiness/definition-of-done gate | all current and proposed indicator files | Apply across whole module as acceptance/NFR/example requirements. | Full traceability, coverage, examples, import, docs, and release-gate evidence. | Acceptance gate / pending evidence |
| IND-BR-008 | Indicator functions shall avoid production `print()` output and shall use structured logging only through approved utility logging contracts where logging is requir… | Builder readiness/definition-of-done gate | all current and proposed indicator files | Apply across whole module as acceptance/NFR/example requirements. | Full traceability, coverage, examples, import, docs, and release-gate evidence. | Acceptance gate / pending evidence |
| IND-BR-009 | SBOM generation, cryptographic package signing, vulnerability checks, license gates, and release provenance attestations shall be CI/CD and release-engineering resp… | Builder readiness/definition-of-done gate | all current and proposed indicator files | Apply across whole module as acceptance/NFR/example requirements. | Full traceability, coverage, examples, import, docs, and release-gate evidence. | Acceptance gate / pending evidence |
| IND-BR-010 | Release artifacts shall include provenance attestations that identify source revision, build workflow, build environment, package hash, and signing identity. | Builder readiness/definition-of-done gate | all current and proposed indicator files | Apply across whole module as acceptance/NFR/example requirements. | Full traceability, coverage, examples, import, docs, and release-gate evidence. | Acceptance gate / pending evidence |
| IND-BR-011 | Supply-chain tests shall verify dependency declarations, lockfile or equivalent reproducibility mechanism, license compatibility checks, vulnerability checks, SBOM… | Builder readiness/definition-of-done gate | all current and proposed indicator files | Apply across whole module as acceptance/NFR/example requirements. | Full traceability, coverage, examples, import, docs, and release-gate evidence. | Acceptance gate / pending evidence |
| IND-BR-012 | Documentation shall describe market-data provenance, price adjustment status, price source, venue, vendor, symbol normalization version, corporate-action adjustment… | Builder readiness/definition-of-done gate | all current and proposed indicator files | Apply across whole module as acceptance/NFR/example requirements. | Full traceability, coverage, examples, import, docs, and release-gate evidence. | Acceptance gate / pending evidence |
| IND-BR-013 | Documentation shall describe dependency pinning, lockfile or equivalent reproducibility mechanism, SBOM generation, license checks, vulnerability checks, cryptograp… | Builder readiness/definition-of-done gate | all current and proposed indicator files | Apply across whole module as acceptance/NFR/example requirements. | Full traceability, coverage, examples, import, docs, and release-gate evidence. | Acceptance gate / pending evidence |
| IND-BR-014 | Market-data provenance, adjustment status, intra-bar corporate actions, symbol mapping, and microstructure rules are validated. | Builder readiness/definition-of-done gate | all current and proposed indicator files | Apply across whole module as acceptance/NFR/example requirements. | Full traceability, coverage, examples, import, docs, and release-gate evidence. | Acceptance gate / pending evidence |
| IND-BR-015 | Cryptographic package signing and release provenance attestation are present for production packages. | Builder readiness/definition-of-done gate | all current and proposed indicator files | Apply across whole module as acceptance/NFR/example requirements. | Full traceability, coverage, examples, import, docs, and release-gate evidence. | Acceptance gate / pending evidence |

## 9. Compatibility and Deprecation Strategy

1. **Phase A — compatibility-first:** Keep current classes and singleton exports unchanged; add tests around observed outputs.
2. **Phase B — adapter-first:** Add `IndicatorResult` wrappers that internally call current classes.
3. **Phase C — official API:** Introduce `app.services.indicators.api` and registry-backed functions.
4. **Phase D — downstream migration:** Move Strategy, Research, Simulator, and Optimization consumers to official wrappers.
5. **Phase E — deprecation:** Mark legacy singleton imports with machine-readable lifecycle metadata; remove only after owner-approved removal window.

Compatibility imports that must continue working during the window:

```python
from app.services.indicators import sma, ema, rsi, atr, williams_r
from app.services.indicators import BaseIndicator, crossed_above, crossed_below
```

## 10. Testing Strategy

### 10.1 Characterization tests first

Add golden tests for every current indicator class before changing implementations. The first test wave records existing output shapes, column names, NaN positions, and errors for representative inputs.

### 10.2 Contract tests

- `IndicatorResult.values` alignment, join behavior, metadata fields, JSON-safe serialization.
- `IndicatorManifest` hashes/checksums, formula version, parameter hash, provenance fields.
- `IndicatorConfig` parameter, naming, precision, collision, and source-column behavior.
- `IndicatorContext` request/correlation/actor/workflow/environment fields.
- `IndicatorProtocol` structural typing.

### 10.3 Safety tests

- Import-time side-effect tests.
- Input immutability tests.
- Duplicate-column and timestamp validation tests.
- No-lookahead tests, especially for multi-timeframe and SMC/custom logic.
- NaN/infinity/zero division/extreme numeric tests.
- Error-code mapping tests.
- Public export snapshot tests.

### 10.4 Family tests

- Trend: SMA, EMA, WMA, Bollinger Bands, MACD; add/defer ADX explicitly.
- Volatility: ATR, standard deviation, Bollinger volatility aspects.
- Momentum: RSI, MACD, Williams %R; add/defer Stochastic explicitly.
- Volume: OBV, MFI, CMF, price-volume distribution.
- Candles: Doji, Engulfing, Inside Bar, Pinbar.
- Custom: HMA and SMC conformance/no-lookahead review.

## 11. Documentation and README Requirements

Update `app/services/indicators/README.md` and add `docs/indicators/` docs covering:

- module boundary and non-goals
- current compatibility API and new official API
- indicator families and lifecycle status
- input data expectations
- output/result contract
- formula specs and warmup policy
- no-lookahead and availability metadata
- deterministic behavior and numeric policy
- custom indicator promotion process
- Data/Strategy/Simulator/Optimization/Risk/Trading boundaries
- usage examples and migration examples
- testing and evidence ledger

## 12. Definition of Done

The brownfield upgrade is complete only when:

- Existing imports still work.
- Current formulas have characterization tests.
- Every mapped requirement is complete or explicitly deferred with a reason.
- Every requirement has evidence references to implementation/tests/docs.
- All tests pass.
- Coverage is at least 80% for affected files and package-level gate.
- README and docs are updated.
- Usage examples include pure synthetic paths and optional integration paths.
- Changelog or implementation report records public-surface changes.
- No greenfield destructive rewrite was performed.
- No broker/data-provider/trading/risk/live responsibilities leaked into Indicators.
- Official outputs are deterministic, no-lookahead-safe, and JSON-safe where required.

## 13. Explicit Non-Goals

Indicators must not own:

- broker connections or live broker sessions
- broker reads or credentials
- raw market-data persistence
- data provider routing
- strategy execution or signal decisions
- final risk approval
- order placement/modification/cancellation
- live execution or reconciliation
- UI/API transport
- optimization search orchestration
- simulator event loop or fills
- release-engineering systems such as SBOM/signing infrastructure, except by documenting required release evidence

## 14. Builder Handoff Prompt

```text
You are the Builder for Phase 03 Indicator brownfield upgrade. Read docs/dev/phase-implementation-plan/03-indicator.md first. Implement module-by-module in the sequence defined there. Preserve current app/services/indicators code and public imports. Add characterization tests before refactoring. Introduce contracts, validation, availability, registry, and official API wrappers incrementally. Do not delete or move existing indicator files until tests and compatibility wrappers prove safety. Keep Indicators pure: no broker reads, data provider routing, trading execution, risk decisions, live runtime, UI/API, or optimization orchestration. Update requirement evidence lines as work lands. Run tests, lint, type checks, and coverage. Do not commit automatically unless explicitly instructed.
```

# Changelog

## 2.2.1

**Release date:** 2026-07-23

### Focused Brokers domain correction

The Brokers domain now exposes its corrected focused feature architecture, fail-closed capability policy, provider controls, and complete offline evidence suite.

#### Added (16)

- `FEAT-BRK-00` Canonical Provider-Neutral Contracts.
- `FEAT-BRK-01` Adapter Registry and Capability Discovery.
- `FEAT-BRK-02` MetaTrader 5 Account Lifecycle.
- `FEAT-BRK-03` cTrader Account Lifecycle.
- `FEAT-BRK-04` Binance Lifecycle.
- `FEAT-BRK-05` Dukascopy Tick Reads.
- `FEAT-BRK-06` Yahoo History.
- `FEAT-BRK-07` MetaTrader 5 Mutations.
- `FEAT-BRK-08` cTrader Mutations.
- `FEAT-BRK-09` Execution History Reads.
- `FEAT-BRK-10` Provider Calculations.
- `FEAT-BRK-11` Price Streams.
- `FEAT-BRK-12` cTrader Market Data.
- `FEAT-BRK-13` Dukascopy BID Bars.
- `FEAT-BRK-14` Deterministic Fake Adapter.
- `FEAT-BRK-15` Adapter Runtime.

## 2.2.0

July 23, 2026

### Feature registries, focused domains, and contract hardening

Consolidated current feature ownership into package READMEs while completing focused-domain, contract, and documentation corrections without changing runtime behavior.

#### Added (8)

- Registered root runtime-profile and execution-route compatibility as `FEAT-APP-01` in `app/README.md`.
- Recorded the 15 Brokers capability IDs and usage programs and exposed shared-provider-folder structural status.
- Recorded eight Portfolio feature owners and exposed missing dedicated usage programs and the requirement-bearing root `api.py`.
- Aligned nine Simulator feature IDs with nine usage programs and exposed root `errors.py` ownership.
- Aligned nine Optimization feature IDs with their numbered usage programs and Section 4 specifications.
- Localized 12 missing Research feature targets to the Research README while retaining its `Missing` status.
- Localized 12 missing backend/frontend API feature targets to the UI/API README without claiming implementation completion.
- Established `app/services/data/contracts/` as Data’s canonical immutable contract boundary and migrated consumers without compatibility re-exports.

#### Changed (11)

- Made owning package READMEs the canonical current feature registries, kept this changelog history-only, and changed no code, API, contract, requirement, or test.
- Split broad Risk policy and decision ownership into focused feature owners, registered contracts as a feature, corrected the public API to `RiskConfig`, and aligned 15 usage programs.
- Adopted trusted-data canonical serialization through `canonical_digest(value)` and `canonical_json(..., max_items=None)` under `XDOM-01` while preserving default bounds and existing hashes.
- Kept tick derivation in `FEAT-DATA-05`, approved private fixed-point Numba kernels and bounded columnar persistence for eligible inputs, and retained exact Decimal behavior for special cases.
- Adopted closed Data quality behavior where `reject` raises `DATA_QUALITY_FAILED` and `warn` returns unchanged data with bounded evidence and calendar-aware inspection.
- Preserved genuinely unavailable analytical spread as float64 `NaN` with `spread_unit=None` and continued to reject conflicting supplied units.
- Removed the application-wide 50,000-record OHLCV ceiling while retaining governed bounds for tick, spread, payload, diagnostics, and resumable backfill chunks.
- Rebaselined Data under `CAP-DATA-028` to 15 focused feature owners while preserving active requirements, APIs, contracts, schemas, errors, and persistence boundaries.
- Classified Strategy evaluator implementations as catalogue content, separated signal execution, registered contracts, tightened manifest validation, and adopted shared canonical digest behavior.
- Reconciled Brokers provider capabilities and failure semantics, pinned Twisted compatibility, added 15 offline usage programs, and kept unsupported behavior fail-closed.
- Superseded `CAP-DATA-026` with `CAP-DATA-028` while retaining its ownership, dependency, migration, state, temporal, invariant, facade, and shim-removal principles where compatible.

#### Removed (1)

- Removed retired Data horizontal paths and compatibility shims while completing the approved `CAP-DATA-028` 15-feature/15-usage-program structure and preserving the frozen 35-operation API and contracts.

#### Fixed (4)

- Mapped canonical Yahoo `H1` bars to yfinance `1h` while preserving the requested canonical timeframe in provenance.
- Aligned the Indicators public registry with implemented Core and calculation signatures, including `IndicatorResult` helpers and the Bollinger Bands `std_dev` parameter.
- Added Utils `AuthContext` compatibility evidence, separated `AuditEvent` construction from Data persistence, documented sensitive-key matching, and corrected `flush_logging()` queue behavior.
- Populated Brokers result latency at adapter boundaries and documented capability-aware `BrokerResult` and `FakeBrokerAdapter` behavior with bounded subscriptions and failure gates.

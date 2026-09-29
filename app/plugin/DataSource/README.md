# Dukascopy Data Source Plugin

> **Backend Path:** `app/plugin/DataSource/dukascopy.py`
> **Frontend Path:** `app/ui/app/plugins/DataSource/Dukascopy/`
> **Package ID:** `plugin.data_manager.dukascopy`
> **Owner Workspace:** `workspace.data_manager`
> **Attachment Slot:** `data_source.acquisition@1.0.0`
> **Mode:** `paired`
> **Host Contract:** `1.0.0`
> **Status:** Qualified
> **Last updated:** 2026-09-29

This README is the plugin's authoritative source of truth for the Dukascopy data acquisition concept, BI5 decoding algorithms, parameter schema, dual transport policies, and single-package removal invariants.

[PROJECT.md](../../../docs/PROJECT.md) owns system scope and cross-workspace workflows. [ARCHITECTURE.md](../../../docs/ARCHITECTURE.md) owns structural rules and the Five Laws of Spatial Composability. [app/workspace/DataManager/README.md](../../workspace/DataManager/README.md) owns the slot contract and workspace workflow coordination.

---

## Code-Aligned Implementation Convention

```text
app/plugin/DataSource/
|-- dukascopy.py                     # One cohesive concept file (FEAT-DM-DUKASCOPY_ACQUISITION)
`-- README.md                        # This document

app/ui/app/plugins/DataSource/Dukascopy/
|-- package.json                     # Authoritative manifest defining owned_paths and slot attachment
|-- contribution.tsx                 # Slot attachment and UI extension entrypoint
|-- add.tsx                          # Add symbol modal component
|-- import.tsx                       # Download / acquisition modal component
|-- disclaimer.tsx                   # Mandatory vendor legal disclaimer modal
`-- [helpers]/                       # dukascopy.ts, dukascopyDownload.ts, dukascopyStore.ts

tests/plugin/DataSource/
`-- test_dukascopy.py                # Unit, boundary, numerical, schema, and rate throttling tests

tests/examples/
`-- dukascopy_offline.py             # Deterministic, offline usage example
```

- **Manifest:** `app/ui/app/plugins/DataSource/Dukascopy/package.json` declares package identity, owner workspace (`workspace.data_manager`), slot attachment (`data_source.acquisition@1.0.0`), and exact `owned_paths`.
- **Cohesion (SC-01):** Decoding algorithm, parameter schema, network transport, throttling, and storage logic stay together in `dukascopy.py`.
- **Zero Sibling Imports:** Sibling plugins and workspace internal implementation are never imported directly.

---

## 1. Purpose and Capability Boundary

### Purpose

Acquires high-precision historical Forex and CFD market data from Dukascopy Bank SA. Decodes binary LZMA-compressed `.bi5` tick and minute records into standardized, UTC-aligned Apache Arrow and Parquet tables.

### System owns

- Binary decompression and integer-to-float decoding of Dukascopy `.bi5` chunks.
- Parameter schema for symbol addition and range download operations.
- Adaptive network rate throttling and StrategyQuant Fast CDN failover logic.
- Verbatim regulatory and copyright disclaimer presentation.

### System does not own

- Dataset inventory cataloging or workspace table filtering (owned by DataManager).
- Direct raw database manipulation (uses host market data capabilities).
- Execution scheduling or background process management (delegated to `host.jobs@1.0.0`).

---

## 2. Feature Specification & Traceability

This single Python file represents one cohesive, fully documented, traced feature (`FEAT-DM-DUKASCOPY_ACQUISITION`).
Every method inside this file represents one or more traced functional requirements:

### `dukascopy.py` — `FEAT-DM-DUKASCOPY_ACQUISITION`

> **Feature ID:** `FEAT-DM-DUKASCOPY_ACQUISITION`
> **Owner File:** `app/plugin/DataSource/dukascopy.py`
> **Status:** Qualified
> **Attached Slot:** `data_source.acquisition@1.0.0`

#### Functional Requirements Table

| Status | Requirement ID | Observable Behavior | Implementing Method | Side Effects | Failure Behavior | Verification Oracle |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Qualified | `FR-DATA-001` | Decodes `.bi5` LZMA payloads into PyArrow tables with dual-side volume | `dukascopy.decode_ticks()`<br>`dukascopy.decode_bi5()` | None | Raises `ValueError` on malformed bytes | `tests/plugin/DataSource/test_dukascopy.py` |
| Qualified | `FR-DATA-001` | Executes adaptive throttling with +25% backoff on 429/503 and -25% recovery | `DownloadRateCorrector.correct_delay()` | Updates delay | Reaches capped max delay on sustained 429s | `tests/plugin/DataSource/test_dukascopy.py` |
| Qualified | `FR-DATA-001` | Downloads range via Fast CDN with transparent fallback to Direct Dukascopy | `dukascopy.acquire()` | Network requests | Falls back cleanly; errors if all endpoints fail | `tests/plugin/DataSource/test_dukascopy.py` |

---

## 3. Parameter Schema

Configuration is represented by the JSON parameter schema declared in `PLUGIN["parameter_schema"]`:

| Operation Key | Parameter | Type | Required | Description | Constraints / Validation |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `add` | `symbol` | `string` | Yes | 6-character currency pair | Pattern: `^[A-Z]{6}$` (e.g. `EURUSD`) |
| `add` | `kind` | `string` | No | Data timeframe | Enum: `["m1", "ticks"]`, Default: `"m1"` |
| `add` | `instrument` | `string` | No | Instrument classification | Max length: 80 characters |
| `definitions.add` | `symbols` | `array` | Yes | List of target symbols | Min items: 1, Max items: 725 |
| `definitions.add` | `broker` | `string` | No | Broker profile association | Default: `"-1"` (Default broker) |
| `definitions.add` | `postfix` | `string` | No | Broker symbol suffix | Pattern: `^[A-Za-z0-9_.-]{0,40}$` |
| `download.start` | `dataset_id` | `string` | Yes | Registered dataset identifier | 32-character hex hash |
| `download.start` | `date_from` | `string` | Yes | Acquisition start date | ISO date string (`YYYY-MM-DD`) |
| `download.start` | `date_to` | `string` | Yes | Acquisition end date | ISO date string (`YYYY-MM-DD`) |
| `download.start` | `mode` | `string` | No | Transport mode | Enum: `["standard", "cdn", "cdn-cn"]` |

---

## 4. Technical Policies

### 4.1 BI5 Decoder
- Decompresses raw `.bi5` chunks using pure Python standard library `lzma.decompress()`.
- Unpacks big-endian 32-bit integer structures (`>IIIff`).
- Reconstructs microsecond-level UTC timestamps from hourly file baselines.
- Computes prices via point-value division (e.g. $10^5$ for Forex 5-digit quotes).

### 4.2 Tick Volume Policy
- **Dual Volume Sum:** Total volume is computed as `ask_volume + bid_volume` after converting provider lots to currency units.
- This explicit HaruQuantAI architectural choice provides true traded volume representation, whereas SQX legacy decoders historically parsed bid volume only.

### 4.3 Adaptive Rate Throttling
- Implements StrategyQuant's `DownloadRateCorrector` pattern:
  - Multiplies inter-request delay by $1.25$ (+25% backoff) on HTTP 429 (Too Many Requests) or 503 (Service Unavailable).
  - Multiplies inter-request delay by $0.75$ (-25% acceleration) after 100 consecutive successful requests.
  - Delay is bounded within $[10\,\text{ms}, 5000\,\text{ms}]$.

### 4.4 Sunday Market Opening Handling
- Forex markets open Sunday at 17:00 NY time (19:00 UTC during daylight saving).
- Acquisition sets the Sunday tick start boundary to 19:00 UTC, preventing false-positive missing data warnings during weekend market closure.

### 4.5 Dual Transport Modes
1. **Direct Dukascopy:** Downloads hourly `.bi5` chunks directly from `https://datafeed.dukascopy.com/datafeed/{symbol}/{year}/{month:02d}/{day:02d}/{hour:02d}h_ticks.bi5`.
2. **StrategyQuant Fast CDN:** Downloads pre-aggregated daily ZIP archives from `https://cdn.strategyquantcdn.com` (Global) or `https://cdn005.strategyquantcdn.com` (China/HK). Automatically falls back to Direct Dukascopy if a CDN chunk is missing.

---

## 5. Persistence and Storage

- **Target Filesystem Storage:** Data is persisted under `data/market/dukascopy/` structured into `m1/` and `ticks/` subdirectories.
- **Partitioning:** M1 files are partitioned into yearly Parquet tables; Tick files into monthly Parquet tables.
- **Timestamp Standard:** All persisted timestamps are strictly UTC.

---

## 6. Deterministic Offline Usage Example

The plugin includes a self-contained offline usage example:

- **Path:** `tests/examples/dukascopy_offline.py`
- **Execution:**
  ```bash
  uv run python -m tests.examples.dukascopy_offline
  ```
- **Verification:** Runs with zero network access using a synthetic LZMA binary fixture, decodes ticks into PyArrow tables, verifies schema compliance, and exits with code `0`.

---

## 7. Verification and Definition of Done

### Focused Verification Commands

```bash
# Plugin unit, numerical, and rate throttling tests
uv run pytest tests/plugin/DataSource/test_dukascopy.py --no-cov

# Deterministic offline example
uv run python -m tests.examples.dukascopy_offline

# UI component unit tests
npm --prefix app/ui run test app/ui/tests/unit/plugins/DataSource/Dukascopy/
```

### Definition of Done Checklist

- [x] All decoding, schema, rate throttling, and transport reside in **one cohesive Python file** (`dukascopy.py`).
- [x] Authoritative `package.json` with valid manifest schema and exact `owned_paths`.
- [x] File represents traced feature `FEAT-DM-DUKASCOPY_ACQUISITION`.
- [x] Every method maps to traced functional requirement `FR-DATA-001`.
- [x] Zero imports of sibling plugins, workspace internal implementation, or global singletons.
- [x] Parameter schema with explicit validation, types, and constraints.
- [x] Fully verified technical policies (BI5 decoder, dual volume, adaptive throttling, Sunday hours).
- [x] Deterministic offline example passes without network dependencies.

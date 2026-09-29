# Data Manager Workspace

> **Backend Path:** `app/workspace/DataManager/`
> **Frontend Path:** `app/ui/app/workspace/DataManager/`
> **Package ID:** `workspace.data_manager`
> **Host Contract:** `host.workspace@1.0.0`
> **Status:** Mixed backend/local implementation; runtime-mock cleanup candidate, qualification pending
> **Last updated:** 2026-09-29

This README is the workspace's authoritative source of truth for its historical market data workflow, action dispatcher, extension slot declarations, zero-plugin fallback behavior, persistence models, host resource boundaries, and cascade removal invariants.

[PROJECT.md](../../../docs/PROJECT.md) owns system scope and cross-workspace workflows. [ARCHITECTURE.md](../../../docs/ARCHITECTURE.md) owns structural rules and the Five Laws of Spatial Composability. [AGENTS.md](../../../AGENTS.md) owns contributor workflow and verification gates.

---

## Current UI data boundary (2026-09-29)

The DataManager dataset inventory, counts, export/tool targets and duplicate-name
context come only from `actions.list_datasets`. Successful empty responses remain
empty. Initial failures show an error and retry; refresh failures retain the last
backend snapshot with a stale-data warning and block data actions until refreshed.
Browser/plugin definitions, generated stock-group datasets, simulated coverage
and simulated completion statuses are not merged into this inventory.

Runtime seed datasets, instruments and sessions, synthetic acquisition timers and
stock-group data generators have been removed. Connected provider operations use
the existing positive `backendAvailable` presentation signal and backend checks;
missing readiness produces an unavailable message. The workspace no longer calls
provider `advance` timers. Dukascopy's own backend polling remains active, with
inventory refresh when a backend job completes. Backend update responses are
reported as submissions, not as proof that downloads completed.

Instruments, sessions, stock groups and broker profiles remain browser-local
configuration. Explicit saved customizations (including old seed overrides) remain
editable. Legacy mock fields remain preserved in storage but are not runtime data;
this cleanup performs no database or browser-storage reset or migration. New
provider wiring and backend catalog persistence require separate approved work.
File dataset creation and stock-group acquisition are unavailable until connected;
plugin implementations outside this workspace are not removed by this change.

Qualification claims in the older registry below describe earlier backend work;
they do not qualify all UI workflows or the current shipping set. Source-backed
cleanup verification and remaining release gates are recorded in
`.agents/logs/20260929_182123_datamanager_remove_mocks/walkthrough.md`.

---

## Code-Aligned Implementation Convention

```text
app/workspace/DataManager/
|-- package.json                     # Authoritative manifest defining owned_paths and slots
|-- README.md                        # This document
|-- __init__.py                      # Docstring-only initializer
|-- workspace.py                     # Slot declarations & host lifecycle preparation
`-- actions.py                       # Concrete workspace command and action handlers

app/ui/app/workspace/DataManager/
|-- DataManager.tsx                  # Primary React workspace view component
|-- contribution.tsx                 # UI workspace contribution manifest
|-- Actions/                         # Action dialogs and actionsClient.ts
|-- Catalogs/                        # BrokerProfiles, Instruments, Sessions, StockGroups
`-- Common/                          # Local configuration store, ribbon components

tests/workspace/DataManager/
|-- test_workspace.py                # Slot declaration, descriptor, and lifecycle tests
`-- test_actions.py                  # Action execution, input validation, and error tests
```

- **Manifest:** Root `package.json` owns package identity (`workspace.data_manager`), version, declared extension slots, and exact `owned_paths`.
- **Slots:** Declared in `workspace.py`; child plugins (e.g. Dukascopy) are accessed strictly via host-injected handles without static imports.
- **Actions:** Consolidated in `actions.py` with 100% parity between UI and CLI (`uv run python -m app.cli --page=data-manager --action=[action_name]`).
- **Persistence:** Tables `datamgr_datasets` and `datamgr_broker` reside in `data/database/haruquantai.db`; presets in `data/presets/DataManager/`.
- **UI:** Rendered in `DataManager.tsx`, dynamically discovering attached data-source plugins.

---

## 1. Purpose and Boundary

### Purpose

DataManager coordinates historical market data acquisition, inspection, validation, conversion, and multi-broker symbol management. It empowers quantitative researchers to assemble clean, continuous price series across M1 and Tick granularities for strategy generation and backtesting.

### System owns

- Historical dataset definitions, inventory management, and status tracking.
- Action dispatching (`actions.*`), payload validation, and progress reporting.
- Extension slot declarations (`data_source.acquisition`, `data_source.presentation`).
- Local UI presentation, dataset table filtering, broker profiles, sessions, and symbol mappings.

### System does not own

- Feed-specific network decoding or vendor protocols (owned by concrete DataSource plugins like `dukascopy.py`).
- Global file storage allocation or quota enforcement (owned by Host Resource Custody `host.resources@1.0.0`).
- Private state or execution engines of sibling workspaces (e.g. StrategyBuilder).

---

## 2. Extension Slots and Zero-Plugin Behavior

### 2.1 Declared Extension Slots

| Slot ID | Contract Version | Cardinality | Input Schema | Output Schema | Allowed UI Vocabulary | Purpose |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `data_source.acquisition` | `1.0.0` | `zero_or_more` | `AcquisitionRequestDTO` | `AcquisitionResultDTO` | Dialog / Progress | Provides automated market data downloads from specific vendor sources. |
| `data_source.presentation` | `1.0.0` | `zero_or_more` | Custom | Custom | Dialog / Custom View | Provides custom source configuration forms or visualizers. |

### 2.2 Zero-Plugin Invariant & Fallback Behavior

DataManager remains fully functional when zero data-source plugins are installed:
- **UI Fallback:** The DataSource ribbon and Add Source dialogs display only installed providers; if none exist, the UI clearly indicates no external sources are available while retaining full access to existing local datasets and actions.
- **Backend Degradation:** Operations requiring an attached acquisition plugin fail closed with a structured `UNAVAILABLE` diagnostic. Unrelated actions (e.g., `list_datasets`, `clone_to_timezone`, `export_to_csv`, `review_chart`) and inspection of previously retained datasets remain 100% operational.

---

## 3. Feature Registry

Each module/file in this workspace represents a single, cohesive, fully documented, traced feature (`FEAT-*`):

| Feature ID | Delivered Capability | Owner File | Contract / Slot | Required Host Services | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `FEAT-DM-COORDINATOR` | Workspace lifecycle, slot declarations, and host preparation | `app/workspace/DataManager/workspace.py` | `host.workspace@1.0.0` | `host.resources@1.0.0` | Implemented |
| `FEAT-DM-ACTIONS` | Concrete action dispatching, dataset export, clone, and review | `app/workspace/DataManager/actions.py` | `actions.*` wire endpoints | `host.jobs@1.0.0` | Implemented |
| `FEAT-DM-PERSISTENCE` | Relational tables for datasets and broker configurations | `app/workspace/DataManager/actions.py` | `data/database/haruquantai.db` | SQLite database | Implemented |

---

## 4. Action Registry & CLI Parity

Every action in `actions.py` maps to a traced functional requirement (`FR-DATA-002`) and supports identical execution in UI and CLI:

| Action ID | Action Name | Implementing Function | Input Parameters | Output DTO | CLI Command Example | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `listDatasets` | List Datasets | `actions.list_datasets()` | filter criteria | `list[DatasetRecord]` | `uv run python -m app.cli --page=data-manager --action=listDatasets` | Qualified |
| `brokerData` | Fetch Broker Data | `actions.broker_data()` | broker_id, symbol | `BrokerDataResult` | `uv run python -m app.cli --page=data-manager --action=brokerData` | Qualified |
| `brokerDataUpdate` | Update Broker Data | `actions.broker_data_update()` | broker_id, symbol | `BrokerDataResult` | `uv run python -m app.cli --page=data-manager --action=brokerDataUpdate` | Qualified |
| `cloneToTimezone` | Clone to Timezone | `actions.clone_to_timezone()` | dataset_id, target_tz | `CloneResult` | `uv run python -m app.cli --page=data-manager --action=cloneToTimezone` | Qualified |
| `delete` | Delete Datasets | `actions.delete_datasets()` | dataset_ids | `DeleteResult` | `uv run python -m app.cli --page=data-manager --action=delete` | Qualified |
| `exportToCsv` | Export to CSV | `actions.export_to_csv()` | dataset_id, path | `ExportResult` | `uv run python -m app.cli --page=data-manager --action=exportToCsv` | Qualified |
| `exportToMT4` | Export to MetaTrader 4 | `actions.export_to_mt4()` | dataset_id, hst_path | `ExportResult` | `uv run python -m app.cli --page=data-manager --action=exportToMT4` | Qualified |
| `exportToMT5` | Export to MetaTrader 5 | `actions.export_to_mt5()` | dataset_id, path | `ExportResult` | `uv run python -m app.cli --page=data-manager --action=exportToMT5` | Qualified |
| `load` | Load Definitions | `actions.load_definitions()` | source_file | `DefinitionResult` | `uv run python -m app.cli --page=data-manager --action=load` | Qualified |
| `save` | Save Definitions | `actions.save_definitions()` | target_file | `DefinitionResult` | `uv run python -m app.cli --page=data-manager --action=save` | Qualified |
| `review` | Review Data / Chart | `actions.review_data()` | dataset_id, view_type | `ReviewResult` | `uv run python -m app.cli --page=data-manager --action=review` | Qualified |
| `updateAll` | Update All Datasets | `actions.update_all()` | none | `UpdateBatchResult`| `uv run python -m app.cli --page=data-manager --action=updateAll` | Qualified |
| `updateSelected` | Update Selected | `actions.update_selected()` | dataset_ids | `UpdateBatchResult`| `uv run python -m app.cli --page=data-manager --action=updateSelected` | Qualified |

---

## 5. Feature Specifications

### `workspace.py` — `FEAT-DM-COORDINATOR`

> **Feature ID:** `FEAT-DM-COORDINATOR`
> **Owner Module:** `app/workspace/DataManager/workspace.py`
> **Status:** Implemented / Qualified

#### Purpose
Coordinates the DataManager workspace lifecycle, declares versioned extension slots, validates child plugin attachments, and prepares action handlers.

#### Functional Requirements

| Status | Requirement ID | Observable Behavior | Implementing Symbol | Side Effects | Failure Behavior | Test Evidence |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Qualified | `FR-DATA-003` | Declares extension slots and verifies contract versions | `workspace.prepare()` | Injects child handles | Fails closed on version mismatch | `tests/workspace/DataManager/test_workspace.py` |

---

### `actions.py` — `FEAT-DM-ACTIONS`

> **Feature ID:** `FEAT-DM-ACTIONS`
> **Owner Module:** `app/workspace/DataManager/actions.py`
> **Status:** Implemented / Qualified

#### Purpose
Provides concrete, stateless action handlers invoked by the HTTP REST/WebSocket dispatcher and CLI runner.

#### Functional Requirements

| Status | Requirement ID | Observable Behavior | Implementing Symbol | Side Effects | Failure Behavior | Test Evidence |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Qualified | `FR-DATA-002` | Dispatches action, validates input payload, and returns typed response | `actions._invoke_action()` | Bounded host job | Returns error code on invalid input | `tests/workspace/DataManager/test_actions.py` |

---

## 6. Persistence and Database

### 6.1 Persisted-State Ownership

| Status | State / Table Name | Owning Feature | Schema Version | Driver | Retention / Purge Policy | Public Read Boundary | Notes |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Qualified | `datamgr_datasets` | `FEAT-DM-PERSISTENCE` | `1` | `sqlite` | `retain` | `actions.list_datasets` | Stores registered dataset definitions, symbol, timeframe, date range. |
| Qualified | `datamgr_broker` | `FEAT-DM-PERSISTENCE` | `1` | `sqlite` | `retain` | Broker profiles catalog | Stores broker configuration records and symbol postfix rules. |

### 6.2 Presets Storage

- Workspace configurations and instrument presets are stored strictly as JSON documents under `data/presets/DataManager/*.json`.
- Presets are versioned, human-readable, and discoverable by the host preset inventory.

---

## 7. Package Removal and Cascade Invariants

When `workspace.data_manager` is uninstalled via `app/host/removal.py`:

1. **Cascade Removal:** Uninstalling `workspace.data_manager` **cascades** to automatically uninstall all child data-source plugins attached to its slots (e.g., `plugin.data_manager.dukascopy`).
2. **Survivor Invariant:** Rebuilding the UI and restarting the backend host succeeds cleanly. Sibling workspaces and the host shell continue operating without missing-module errors.
3. **Data Preservation:** User data, storage files (`data/market/`), presets, and database records in `data/database/haruquantai.db` are never deleted during package uninstall.

---

## 8. Verification and Acceptance Matrix

| Verification Scope | Requirement | Command |
| :--- | :--- | :--- |
| **Workspace Slots & Lifecycle** | Slot declaration, compatibility checks, zero-plugin fallback | `uv run pytest tests/workspace/DataManager/test_workspace.py` |
| **Action Dispatcher & Parity** | All 12 actions execute with valid payloads; error handling | `uv run pytest tests/workspace/DataManager/test_actions.py` |
| **Complete Workspace Suite** | Combined unit and integration checks | `uv run pytest tests/workspace/DataManager/` |
| **Frontend UI Suite** | Workspace views, dialogs, and actions client tests | `npm --prefix app/ui run test` |

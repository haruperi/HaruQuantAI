# [Workspace Name] Workspace

> **Backend Path:** `app/workspace/[Workspace]/`
> **Frontend Path:** `app/ui/app/workspace/[Workspace]/`
> **Package ID:** `workspace.[workspace_slug]`
> **Host Contract:** `host.workspace@1.0.0`
> **Status:** `[Missing | Partial | Implemented | Qualified]`
> **Last updated:** `[YYYY-MM-DD]`

This README is the workspace's authoritative source of truth for its user workflow, action dispatcher,
extension slot declarations, zero-plugin fallback behavior, persistence models, host resource boundaries,
and cascade removal invariants.

[PROJECT.md](../../PROJECT.md) owns system scope and cross-workspace workflows. [ARCHITECTURE.md](../../ARCHITECTURE.md)
owns structural rules and the Five Laws of Spatial Composability. [AGENTS.md](../../../AGENTS.md) owns contributor
workflow and verification gates.

---

## Code-Aligned Implementation Convention

```text
app/workspace/[Workspace]/
|-- package.json                     # Authoritative manifest defining owned_paths and slots
|-- README.md                        # This document
|-- __init__.py                      # Docstring-only initializer
|-- workspace.py                     # Slot declarations & host lifecycle preparation
|-- actions.py                       # Concrete workspace command and action handlers
`-- persistence.py                   # (Optional) Domain schema, tables, and transactional operations

app/ui/app/workspace/[Workspace]/
|-- view.tsx                         # Primary React workspace view component
|-- client.ts                        # Typed API client adapting backend REST/WebSocket routes
`-- [components]/                    # Workspace-local UI components and modals

tests/workspace/[workspace]/
|-- test_workspace.py                # Slot declaration, descriptor, and lifecycle tests
|-- test_actions.py                  # Action execution, input validation, and error tests
|-- test_persistence.py              # (Optional) Database queries, transactions, and migration tests
`-- test_empty_state.py              # Zero-plugin fallback and graceful degradation tests
```

- **Manifest:** Root `package.json` owns package identity, version, `slots` declarations, and exact `owned_paths`.
- **Slots:** Declared in `workspace.py`; child plugins are accessed strictly via host-injected handles without static imports.
- **Actions:** Consolidated in `actions.py` with 100% parity between UI and CLI (`uv run python -m app.cli --page=[workspace_slug] --action=[action_name]`).
- **Persistence (Optional):** Consolidated in `persistence.py` when the workspace persists relational data.
- **UI:** Rendered in `view.tsx`, dynamically discovering attached plugin views via `useAttachments('<slot_id>')`.

---

## 1. Purpose and Boundary

### Purpose

[Describe the user job, research workflow, and business outcome this workspace delivers in 2–4 sentences.]

### System owns

- [Workflow coordination and state management for this workspace]
- [Action dispatching, parameter validation, and progress reporting]
- [Extension slot declarations and child capability coordination]
- [Local UI presentation, view states, and data table filtering]

### System does not own

- [Concrete quantitative calculation algorithms (owned by child plugins)]
- [Direct persistent file storage or global custody (owned by Host Resource Custody)]
- [Private state or action dispatching of sibling workspaces]

---

## 2. Extension Slots and Zero-Plugin Behavior

### 2.1 Declared Extension Slots

| Slot ID | Contract Version | Cardinality | Input Schema | Output Schema | Allowed UI Vocabulary | Purpose |
|---|---|---|---|---|---|---|
| `[domain].[slot_name]` | `1.0.0` | `zero_or_more` / `exactly_one` | `[RequestDTO]` | `[ResponseDTO]` | Form / Table / Chart / Custom | [Describe extension capability] |

### 2.2 Zero-Plugin Invariant & Fallback Behavior

A workspace must remain fully functional when zero child plugins are installed:
- **UI Fallback:** When no plugins are attached to `[domain].[slot_name]`, the UI displays a clean, user-friendly empty state explaining that no providers are installed.
- **Backend Degradation:** Operations requiring an attached plugin fail closed with a structured `UNAVAILABLE` diagnostic. Unrelated actions and inspection of previously retained host resources remain fully operational.

---

## 3. Feature Registry

Each module/file in this workspace represents a single, cohesive, fully documented, traced feature (`FEAT-*`):

| Feature ID | Delivered Capability | Owner File | Contract / Slot | Required Host Services | Status |
|---|---|---|---|---|---|
| `FEAT-[WS]-COORDINATOR` | Workspace lifecycle, slot declarations, and host binding | `app/workspace/[Workspace]/workspace.py` | `host.workspace@1.0.0` | `host.resources@1.0.0` | Implemented |
| `FEAT-[WS]-ACTIONS` | User-triggered action dispatching and command handlers | `app/workspace/[Workspace]/actions.py` | `actions.*` wire endpoints | `host.jobs@1.0.0` | Implemented |
| `FEAT-[WS]-PERSISTENCE` | (Optional) Workspace database persistence and migrations | `app/workspace/[Workspace]/persistence.py` | `host.persistence@1.0.0` | SQLite database | Implemented |

---

## 4. Action Registry & CLI Parity

Every action in `actions.py` maps to a traced functional requirement (`FR-*`) and supports identical execution in UI and CLI:

| Action ID | Action Name | Implementing Function | Input DTO | Output DTO | Traced FR | CLI Command Example | Status |
|---|---|---|---|---|---|---|---|
| `[ws].execute` | Execute Operation | `actions.execute_op()` | `[ExecuteRequest]` | `[JobReceipt]` | `FR-[WS]-001` | `uv run python -m app.cli --page=[ws] --action=execute` | Implemented |
| `[ws].list` | List Items | `actions.list_items()` | `[ListQuery]` | `[ItemListResponse]`| `FR-[WS]-002` | `uv run python -m app.cli --page=[ws] --action=list` | Implemented |

---

## 5. Feature Specifications

### `workspace.py` — `FEAT-[WS]-COORDINATOR`

> **Feature ID:** `FEAT-[WS]-COORDINATOR`
> **Owner Module:** `app/workspace/[Workspace]/workspace.py`
> **Status:** `[Missing | Partial | Implemented]`

#### Purpose
Coordinates the workspace lifecycle, declares versioned extension slots, validates child plugin attachments, and prepares action handlers.

#### Functional Requirements

| Status | Requirement ID | Observable Behavior | Implementing Symbol | Side Effects | Failure Behavior | Test Evidence |
|---|---|---|---|---|---|---|
| Implemented | `FR-[WS]-001` | Declares extension slots and verifies contract versions | `workspace.prepare()` | None | Fails closed on version mismatch | `tests/workspace/[ws]/test_workspace.py` |

---

### `actions.py` — `FEAT-[WS]-ACTIONS`

> **Feature ID:** `FEAT-[WS]-ACTIONS`
> **Owner Module:** `app/workspace/[Workspace]/actions.py`
> **Status:** `[Missing | Partial | Implemented]`

#### Purpose
Provides concrete, stateless action handlers invoked by the HTTP REST/WebSocket dispatcher and CLI runner.

#### Functional Requirements

| Status | Requirement ID | Observable Behavior | Implementing Symbol | Side Effects | Failure Behavior | Test Evidence |
|---|---|---|---|---|---|---|
| Implemented | `FR-[WS]-002` | Dispatches action, validates input payload, and returns typed response | `actions.[action_func]()` | Bounded host job | Returns `ApiClientError` on invalid input | `tests/workspace/[ws]/test_actions.py` |

---

## 6. Persistence and Database (Optional)

When this workspace persists state across sessions, all schema definitions, parameterized queries, and
transactions are consolidated in `app/workspace/[Workspace]/persistence.py`.

### 6.1 Persisted-State Ownership

| Status | State / Table Name | Owning Feature | Schema Version | Driver | Retention / Purge Policy | Public Read Boundary | Notes |
|---|---|---|---|---|---|---|---|
| `[Status]` | `[workspace]_[table_name]` | `FEAT-[WS]-PERSISTENCE` | `1` | `sqlite` | `retain` / `purge_on_uninstall` | `[Action / Capability]` | [Partitioning or migration notes] |

### 6.2 Presets Storage

- Workspace configurations and search-space presets are stored strictly as JSON documents under `data/presets/[Workspace]/[preset_name].json`.
- Presets are versioned, human-readable, and discoverable by the host preset inventory.

### 6.3 Database Guidelines

- Tables reside within the single relational database `data/database/[system].db` under host-managed migrations.
- Zero ad-hoc SQL: All queries use parameterized statements; raw connections are never exposed outside `persistence.py`.
- Tests run against isolated in-memory stores (`:memory:`) in `tests/workspace/[workspace]/test_persistence.py`.

---

## 7. Host Resource Custody Boundaries

### Host Resources Exchanged

| Resource Category | Direction | Schema ID | Format | Storage Location | Read / Write Policy |
|---|---|---|---|---|---|
| `[resource_name]` | Ingest | `[system].[schema]@1` | Parquet / JSON | `data/...` | Read via `host.resources.read()` |
| `[resource_name]` | Produce | `[system].[schema]@1` | Parquet / JSON | `data/...` | Published via `host.resources.publish()` |

---

## 8. Package Removal and Cascade Invariants

When this workspace package is uninstalled via `app/host/removal.py`:

1. **Cascade Removal:** Uninstalling `workspace.[workspace_slug]` **cascades** to automatically uninstall all child plugins attached exclusively to this workspace's slots.
2. **Survivor Invariant:** Rebuilding the UI and restarting the backend host succeeds cleanly. Sibling workspaces and the host shell continue operating without missing-module errors.
3. **Data Preservation:** User data, storage files, presets, and database records in `data/` are never deleted during package uninstall.

---

## 9. Decisions and Open Evidence

| Status | Decision ID | Decision or Missing Evidence | Scope | Closure Criteria |
|---|---|---|---|---|
| Open | `DEC-[WS]-001` | [Unresolved architectural or implementation choice] | [Affected Actions/Slots] | [Required evidence or owner decision] |

---

## 10. Verification and Definition of Done

### Focused Verification Commands

```bash
# Workspace unit and action tests
uv run pytest tests/workspace/[workspace]/ --no-cov

# Workspace persistence tests (when persistence is implemented)
uv run pytest tests/workspace/[workspace]/test_persistence.py --no-cov

# Workspace UI tests
npm --prefix app/ui run test app/workspace/[Workspace]/
```

### Definition of Done Checklist

- [ ] Authoritative `package.json` manifest with valid schema and exact `owned_paths`.
- [ ] Cohesive backend implementation in `workspace.py` and `actions.py`.
- [ ] (Optional) Dedicated `persistence.py` managing workspace tables with isolated tests.
- [ ] Paired React UI view in `view.tsx` dynamically attaching slots via `useAttachments`.
- [ ] Every file represents a traced feature (`FEAT-*`) in the Feature Registry.
- [ ] Every action method represents a traced functional requirement (`FR-*`).
- [ ] Zero static imports of concrete plugins or sibling workspaces.
- [ ] Full two-terminal parity verified between UI view and CLI commands.
- [ ] Zero-plugin empty state and graceful degradation verified by tests.
- [ ] All change-scoped and candidate qualification tests pass with $\ge 80\%$ coverage.
- [ ] Single package and cascade removal verified cleanly in isolation.

---

## 11. Change Process

1. Update this Workspace README to record proposed changes, action signatures, or slot updates.
2. Formulate an implementation plan under `.agents/logs/<timestamp>_<task>/implementation-plan.md`.
3. Obtain explicit owner approval (`APPROVED: EXECUTE`) before modifying source code.
4. Implement changes surgically within `app/workspace/[Workspace]/` and `app/ui/app/workspace/[Workspace]/`.
5. Run focused tests during development (`--no-cov`).
6. Run candidate qualification commands before walkthrough handoff.

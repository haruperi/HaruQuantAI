# [System Name] Architecture

> **Authority:** This document owns spatial, structural, and runtime constraints.
> [PROJECT.md](PROJECT.md) owns product scope and target research outcomes;
> [AGENTS.md](../../AGENTS.md) owns contributor workflow and verification commands;
> the owning package `README.md` files own local contracts and implementation status.

---

## 1. The Five Laws of Spatial Composability

These laws are non-negotiable architectural constraints binding across backend and frontend codebases:

### SC-01 — Locality of Behavior
One concept has one cohesive spatial home. A concrete backend plugin keeps its
calculation, configuration, Pydantic parameter schema, defaults, optimization bounds,
output formatting, algebraic port declarations, lowering hooks, and presentation metadata in **one cohesive
Python file**. Its manifest (`package.json`), README, tests, and optional UI counterpart live in that
plugin's paired folders. Universal metamodels and UI primitives may be shared; concept-specific
contracts and algorithms may never be centralized in a global catalog or shared utils file.

> **Review Test:** Trace one concept from parameter input to calculated output and removal.
> Its behavior must be understandable and removable without inspecting unrelated workspaces or shared files.

### SC-02 — Orthogonality
Adding, disabling, upgrading, or removing one package cannot require edits to another package, the
host, or a central plugin registry. A failed or missing plugin blocks only its declared operations;
unrelated catalog entries, routes, tests, and UI surfaces must continue working. Retained artifacts
remain inspectable with an explicit unavailable placeholder rather than disappearing or changing meaning.

> **Review Test:** Remove a plugin package from an isolated installation. All surviving workspaces, routes,
> and unrelated tests must pass; documents referencing the removed concept must report a typed missing dependency.

### SC-03 — Explicit Typed Capability Slots
Components collaborate strictly through declared, versioned capability slots and immutable documents.
Requirements, provided outputs, authorization, compatibility, and failure meanings are explicit. Runtime
behavior cannot reach through a global registry, module-level singleton, private sibling import, UI fixture,
ambient file path, or import-time side effect to access another package's implementation.

> **Review Test:** From a component's public slot declaration alone, identify every external capability it
> requires and the exact typed result it receives when that capability is absent.

### SC-04 — Hierarchical and Algebraic Composition
Complex operations are composed from typed smaller units: plugins contribute primitives; pipelines and
analytical documents bind them as immutable, versioned trees or graphs; workspaces arrange operations over
those documents; project workflows compose finite tasks. Editors, generators, simulators, result viewers,
and exporters refer to the same semantic document and pinned plugin versions. A UI label or serialized node
cannot redefine execution semantics.

> **Review Test:** The exact same pipeline document must be evaluate-able by the execution engine, inspectable by the
> editor, and translatable by the exporter without ambiguity or drift.

### SC-05 — Schema-Driven Self-Description
A package describes its identity, compatibility, inputs/outputs, parameters, constraints, optimization
bounds, capability slots, and presentation hints in machine-readable metadata owned by that package. The
host builds an in-memory catalog by discovery; the UI consumes the catalog within a bounded renderer
vocabulary. Neither host keeps a hand-maintained list of quantitative concepts.

> **Review Test:** Add a compatible plugin and confirm its catalog entry, parameter settings, validation
> constraints, and generic presentation appear dynamically without editing host source or another package.

---

## 2. Spatial Map, Structural Hierarchy, and Ownership

### 2.1 Spatial Pairing Map

The repository is structured into backend and frontend counterparts organized around a universal host pair:

```text
Backend                                      Frontend
========================================================================================
app/host/               <-- Host Pair -->    app/ui/app/host/
  lifecycle, sessions, catalog discovery,      transport, session, router,
  envelope, commands, events, jobs,            shell store and navigation chrome
  telemetry, shell settings, resource custody  (zero domain algorithms or formulas)
  (zero domain algorithms or formulas)

app/workspace/<Name>/   <-- Workspace Pair -> app/ui/app/workspace/<Name>/
  workflow coordination, action handlers,      workspace view, client,
  slot declarations, zero-plugin fallback      local view state, presentation
  (e.g., [Workspace 1], [Workspace 2])

app/plugins/<Cat>/<X>/  <-- Plugin Pair ----> app/ui/app/plugins/<Cat>/<X>/
  one cohesive concept Python file,            concept presentation or local interaction
  manifest (package.json), local tests         (optional; generic schema renderer used
  (e.g., [Concept 1], [Concept 2])             if UI counterpart is omitted)

app/kernel/                                  app/ui/app/components/
  standard-library-only math/runtime           universal presentation primitives
  primitives (no external dependencies)        (tables, charts, dockview layout)
```

---

### 2.2 Five-Level Structural Hierarchy

Traceability from system boundary down to individual acceptance tests is structured as follows:

| Architecture Level | Represents | Template Example | Traced Specification Oracle |
| :--- | :--- | :--- | :--- |
| **1. Host System Pair** | Universal runtime host & client shell boundary | `app/host/`<br>`app/ui/app/host/` | Universal system lifecycle, catalog discovery, sessions, transport, resource custody. Traced system NFRs (`SYS-NFR-*`). |
| **2. Workspace Pair** | Interactive user workflow owner & slot coordinator | `app/workspace/[Workspace]/`<br>`app/ui/app/workspace/[Workspace]/` | Workflow owner, action dispatcher, local view state, declared versioned extension slots (`slots`). Traced workspace requirements. |
| **3. Module / File (Cohesive Concept)** | **Traced Feature Owner (`FEAT-*`)** | Plugin concept file: `app/plugins/[Category]/[Concept]/[concept].py`<br>Workspace action module: `app/workspace/[Workspace]/actions.py` | **One cohesive file = One fully documented, traced feature (`FEAT-[CATEGORY]-[NAME]`)**. Owns configuration, calculation, schema, ports, and physical removal unit. |
| **4. Class / Component / Schema** | Configuration, service logic, algebraic ports, & action handlers | `[Feature]Config` (Pydantic), `[Feature]Service`, `[Feature]Calculator`, algebraic `Port` / `Node` declarations | Typed schema contracts, validation bounds, parameters, units, UI presentation metadata. |
| **5. Method / Function / Operation** | **Traced Functional Requirement (`FR-*`)** | `[concept].[method]()`<br>`actions.[action_func]()`<br>`[calculator].[compute]()` | **One method / function / operation = One or more traced functional requirements (`FR-*`)** with explicit acceptance criteria and verification tests. |

---

### 2.3 Spatial Ownership Boundaries

| Component Owner | May Own | Must Not Own |
|---|---|---|
| **Backend Host** (`app/host/`) | Shared API envelope, session/auth management, command mediation, event bus, dynamic catalog discovery, telemetry/logging, jobs, hardware reservations, resource custody, shell settings | Domain algorithms, workspace workflows, plugin logic, pipeline evaluation semantics, or ad-hoc database schemas |
| **Frontend Host** (`app/ui/app/host/`) | Navigation chrome, universal transport, session storage, catalog cache, generic schema renderers, notification hub | Backend formulas, plugin-specific schemas, durable domain state, or hardcoded imports for concrete plugins |
| **Workspace Pair** (`app/workspace/`) | One interactive user workflow, action dispatcher (`actions.py`), slot declarations, local view state, UI client, optional workspace persistence (`persistence.py`) | Plugin calculation logic, private state of sibling workspaces, or direct raw database manipulation outside owned schema |
| **Plugin Pair** (`app/plugins/`) | One concept, cohesive calculation file, parameter schema, algebraic ports, offline example, tests, optional isolated partition state | Sibling plugin code, workspace workflow dispatch, host lifecycle management, or external undeclared network/file I/O |
| **Kernel** (`app/kernel/`) | Neutral math utilities, timestamp alignment, timeseries structures (Python standard-library only) | Product registries, plugin policies, persistence, UI adapters, or third-party dependencies |
| **UI Primitives** (`app/ui/app/components/`) | Reusable layout primitives (dockview, tabs), charting wrappers, data table components | Domain calculation logic, workflow state, API endpoints, or concept-specific forms |

---

## 3. Dependency, Import, and Transport Direction

### 3.1 Strict Import Boundaries

```text
[Backend Host]   --> (in-memory discovery) --> [Workspace Descriptor]
       |                                                |
(injects host context)                     (invokes via typed slots)
       v                                                v
[Workspace Pair] ----------------------------> [Plugin Pair]
       |                                                |
       +-------> [app/kernel/] (shared primitives) <----+
```

- **No Peer Business Imports:** A workspace cannot import another workspace. A plugin cannot import another plugin.
- **Docstring-Only Initializers:** All `__init__.py` files across `app/workspace/` and `app/plugins/` must be strictly empty or docstring-only. No package registration or import-time side effects.
- **Zero Import-Time Side Effects:** Importing any module must not execute I/O, connect to databases, start threads, read environment variables, or register global handlers.
- **Decoupled Wire Contracts:** Frontend and backend communicate exclusively via JSON-RPC/REST wire contracts (`/api/v1/...`) and WebSocket channels (`/ws/updates`, `/ws/control`).

---

## 4. Composition Model and Extension Slots

### 4.1 Slot Declaration & Attachment Lifecycle

1. **Workspace Declares Slots:** In `package.json` and `workspace.py`, the workspace declares typed extension slots:
   ```json
   "slots": [
     {
       "id": "[domain].[slot_name]",
       "contract_version": "1.0.0",
       "cardinality": "zero_or_more",
       "input_schema": "[RequestDTO]",
       "output_schema": "[ResponseDTO]"
     }
   ]
   ```
2. **Plugin Declares Attachment:** In `package.json`, the plugin binds to its owner's slot:
   ```json
   "attachment": {
     "owner_workspace_id": "workspace.[workspace_slug]",
     "slot_id": "[domain].[slot_name]",
     "contract_version": "1.0.0"
   }
   ```
3. **Host Discovery & Composition:** At startup, `app/host/catalog.py` validates identity, version agreement, and path containment without executing plugin module code.
4. **Dynamic Invocation:** The workspace accesses attached plugins dynamically via host-injected slot handles.

### 4.2 Zero-Plugin Invariant

A workspace must remain fully operational when zero child plugins are attached. Operations requiring an absent plugin must fail closed, disclosing an explicit `UNAVAILABLE` diagnostic without crashing the host or degrading unrelated operations.

---

## 5. Schema and UI Reflection Boundary

1. **Backend Authoritative:** The single source of truth for parameter definitions, data types, defaults, validation rules, min/max bounds, step sizes, and units is the Pydantic schema in the plugin's cohesive concept file.
2. **Generic Bounded UI Vocabulary:** The frontend renders parameter forms, sliders, dropdowns, and toggles dynamically from the discovered Pydantic schema using a bounded component vocabulary (`app/ui/app/host/composition.tsx`).
3. **Zero Custom React Code Required:** Standard plugins require zero custom frontend code.
4. **Reviewed UI Extensions:** When a plugin requires an unconventional interactive visualization, it provides a paired UI extension under `app/ui/app/plugins/<Category>/<Concept>/` that adapts the plugin's wire contract.

---

## 6. State, Persistence, and Shared Resource Custody

### 6.1 Multi-Level Persistence Architecture

Persistence is supported at all architectural levels under strict ownership boundaries:

```text
data/
|-- database/
|   `-- [system].db            # Exactly ONE relational SQLite database for host, workspace, and plugin schemas
|-- presets/
|   |-- [Workspace_1]/         # Workspace configurations and presets strictly as JSON (*.json)
|   `-- [Workspace_2]/         # Strictly JSON (*.json)
|-- [storage_category]/        # Canonical persistent artifacts and files
`-- logs/
    `-- [system].log           # Bounded rotating application log file
```

| Persistence Level | Optionality | Typical Storage Purpose | Technical Implementation |
|---|---|---|---|
| **Host Level** | Required | Core host tables (`host_settings`, `users`, `sessions`, audit logs, resource manifests) | `app/persistence/host.py` in `data/database/[system].db` |
| **Workspace Level** | Optional | Workspace-specific tables (e.g. definitions, queues, templates, metadata) and presets | `app/workspace/[Workspace]/persistence.py` in `data/database/[system].db` and `data/presets/[Workspace]/` |
| **Plugin Level** | Optional | Provider sync markers, calibration caches, trained weights, historical index records | Isolated partition in `data/database/[system].db` or host-sandboxed storage via host capability |

### 6.2 Persisted-State Ownership Invariants

1. **Single Semantic Owner:** Every persisted table, partition, or preset collection has exactly one owning feature (`FEAT-*`).
2. **Zero Cross-Boundary SQL:** No component writes to database state it does not own. Cross-boundary reads go through documented public contracts or host capabilities, never direct SQL queries against peer tables.
3. **No Raw Connections:** Components consume focused persistence interfaces with parameterized queries. Raw unrestricted connection handles are never passed across component boundaries.
4. **Isolated Testing:** Tests always run against temporary in-memory or throwaway databases (`:memory:` or temporary directory), never mutating active operational stores.

### 6.3 Shared Host Resource Custody

Workspaces exchange decision-grade research artifacts through **Host Resource Custody** (`host.resources@1.0.0`):
- Resources carry unique IDs, schema versions, immutable revisions, SHA-256 digests, media types, and producer provenance.
- **Decoupled Reads:** Consumers read published bytes directly from storage using standard decoders without loading or executing the producer plugin's code.
- **Retention Over Uninstall:** Deleting or updating a producer plugin never deletes previously generated artifacts.

---

## 7. Security, Lifecycle, and Package Removal Boundary

### 7.1 Authoritative Manifest (`package.json`)

Every package declares exclusive ownership of all its files in its root `package.json`:
```json
{
  "id": "plugin.[workspace_slug].[concept_slug]",
  "name": "[Plugin Name]",
  "version": "1.0.0",
  "kind": "plugin",
  "host_contract": "1.0.0",
  "owner_workspace_id": "workspace.[workspace_slug]",
  "attachment": {
    "slot_id": "[domain].[slot_name]",
    "contract_version": "1.0.0"
  },
  "owned_paths": {
    "source": ["app/plugins/[Category]/[Concept]/[concept].py"],
    "tests": ["tests/plugin/[category]/test_[concept].py"],
    "assets": [],
    "metadata": ["package.json"]
  }
}
```

### 7.2 Package Removal Procedure & Cascade Invariants

1. **Closure Computation:**
   - Removing a plugin uninstalls all files declared in its `owned_paths`.
   - Removing a workspace **cascades** to uninstall the workspace and all plugins attached to its slots.
2. **Journaled Atomic Move:** `apply_removal()` performs a reversible journaled move into temporary quarantine under an installation lease.
3. **Survivor Invariants:**
   - Rebuilding the UI and restarting the backend host must succeed without missing-module errors.
   - Surviving test suites must pass 100%.
   - Retained user data, storage files, and database records remain intact and readable.
4. **Restoration:** `restore_removal()` reverses the journaled move and confirms that the repository inventory matches baseline.

---

## 8. Architecture Acceptance and Verification Matrix

An architectural contribution is accepted only when all verification criteria are satisfied:

| Check Category | Verification Requirement | Verification Command |
|---|---|---|
| **Import Boundaries** | Zero peer imports; docstring-only `__init__.py`; standard-library kernel | `uv run python scripts/architecture_check.py` |
| **Package Manifests** | All files accounted for; valid `package.json` schemas; no orphaned or overlapping files | `uv run python scripts/package_inventory.py` |
| **Frontend Architecture**| UI slot attachments via `useAttachments`; no static imports of concrete plugins | `node scripts/ui_architecture_check.cjs` |
| **Static Code Quality** | Ruff lint/format clean; Mypy strict mode clean; zero TypeScript errors | `uv run python scripts/ci_check.py`<br>`npm --prefix app/ui run typecheck` |
| **Test Coverage** | Unit and integration test pass; $\ge 80\%$ branch coverage across retained code | `uv run pytest tests/` |
| **Offline Examples** | Deterministic, offline usage example executes and passes | `uv run python tests/examples/[example].py` |
| **Package Removal** | Full removal cascade passes in isolation; surviving tests pass 100% | `uv run python scripts/release_check.py` |

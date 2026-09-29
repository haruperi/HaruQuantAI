# [Plugin Name] Plugin

> **Backend Path:** `app/plugins/[Category]/[Concept]/[concept].py` *(or `app/plugin/[Category]/[concept].py`)*
> **Frontend Path:** `app/ui/app/plugins/[Category]/[Concept]/` *(optional; omitted if using generic UI)*
> **Package ID:** `plugin.[workspace_slug].[concept_slug]`
> **Owner Workspace:** `workspace.[workspace_slug]`
> **Attachment Slot:** `[slot_id]@[version]`
> **Mode:** `[paired | headless | ui_only]`
> **Host Contract:** `1.0.0`
> **Status:** `[Missing | Partial | Implemented | Qualified]`
> **Last updated:** `[YYYY-MM-DD]`

This README is the plugin's authoritative source of truth for its quantitative concept, mathematical algorithms,
Pydantic parameter schema, optimization bounds, algebraic ports, persistence model (if applicable), offline usage
example, and single-package removal invariants.

[PROJECT.md](../../../PROJECT.md) owns system scope and research journeys. [ARCHITECTURE.md](../../../ARCHITECTURE.md)
owns the Five Laws of Spatial Composability and structural constraints. The owning Workspace's `README.md`
owns the slot contract and workflow coordination.

---

## Code-Aligned Implementation Convention

```text
app/plugins/[Category]/[Concept]/
|-- package.json                     # Authoritative manifest defining owned_paths and slot attachment
|-- README.md                        # This document
|-- __init__.py                      # Docstring-only initializer
`-- [concept].py                     # One cohesive concept file (FEAT-[OWNER]-[CONCEPT])

app/ui/app/plugins/[Category]/[Concept]/  # (Optional: provided only if custom visual rendering is needed)
|-- contribution.tsx                 # Slot attachment and UI extension entrypoint
`-- [components]/                    # Custom React presentation components

tests/plugin/[category]/
`-- test_[concept].py                # Unit, boundary, numerical, schema, and error tests

tests/examples/
`-- [category]_[concept]_offline.py  # Self-contained, deterministic, offline usage example
```

- **Manifest:** Root `package.json` declares package identity, owner workspace, slot attachment, and exact `owned_paths`.
- **Cohesion (SC-01):** Calculation algorithm, Pydantic parameter schema, bounds, ports, and lowering hooks stay together in `[concept].py`.
- **Zero Sibling Imports:** Sibling plugins and workspace implementation are never imported directly.

---

## 1. Purpose and Capability Boundary

### Purpose

[Describe the quantitative concept, calculation algorithm, or domain function
this plugin performs in 2–4 sentences.]

### System owns

- [Specific mathematical calculation, algorithm, or data transformation]
- [Pydantic parameter schema, bounds, validation, and presentation hints]
- [Algebraic input and output port declarations]
- [Code lowering logic for supported export targets (if applicable)]
- [(Optional) Plugin-local persistence state and partition schemas]

### System does not own

- [Overall workflow orchestration or execution coordination (owned by workspace)]
- [Direct filesystem access outside host capabilities or raw database connections]
- [Cross-plugin communication or private sibling imports]

---

## 2. Feature Specification & Traceability

This single Python file represents one cohesive, fully documented, traced feature (`FEAT-*`).
Every method/function inside this file represents one or more traced functional requirements (`FR-*`):

### `[concept].py` — `FEAT-[OWNER]-[CONCEPT]`

> **Feature ID:** `FEAT-[OWNER]-[CONCEPT]`
> **Owner File:** `app/plugins/[Category]/[Concept]/[concept].py`
> **Status:** `[Missing | Partial | Implemented]`
> **Attached Slot:** `[slot_id]@[version]`

#### Functional Requirements Table

| Status | Requirement ID | Observable Behavior | Implementing Method / Symbol | Side Effects | Failure Behavior | Verification Oracle |
|---|---|---|---|---|---|---|
| Implemented | `FR-[DOM]-001` | [Primary calculation or processing behavior] | `[concept].[method_name]()` | None | Raises typed exception on invalid input | `tests/plugin/[cat]/test_[concept].py` |
| Implemented | `FR-[DOM]-002` | [Boundary, missing-data, or edge-case behavior]| `[concept].[method_name]()` | Bounded | Graceful fallback or attributed error | `tests/plugin/[cat]/test_[concept].py` |

---

## 3. Parameter Schema and Optimization Bounds

Configuration is represented by the Pydantic model `[Concept]Config` in the owner file:

| Parameter Key | Type | Default | Min Bound | Max Bound | Step | Unit | Description | UI Presentation Hint |
|---|---|---|---|---|---|---|---|---|
| `[param_1]` | `int` | `[default]` | `[min]` | `[max]` | `[step]` | `[unit]` | [Parameter description] | Slider (`min: [min], max: [max]`) |
| `[param_2]` | `float`| `[default]` | `[min]` | `[max]` | `[step]` | `[unit]` | [Parameter description] | Number input (`step: [step]`) |
| `[param_3]` | `str` | `[default]` | - | - | - | - | [Option selection description] | Dropdown (`[option_1], [option_2]`) |

---

## 4. Algebraic Ports and Lowering Hooks

### 4.1 Algebraic Ports

```python
# Declared in [concept].py for pipeline / graph composition
INPUT_PORTS = [
    Port(id="[input_port_1]", type="[Type1]", description="[Input description]"),
]

OUTPUT_PORTS = [
    Port(id="[output_port_1]", type="[Type2]", description="[Output description]"),
]
```

### 4.2 Lowering Hooks (Optional)

When attached to code-generation or export slots, the plugin provides lowering functions:
- `lower_to_[target_1](node, context) -> str`
- `lower_to_[target_2](node, context) -> str`

---

## 5. Technical Policies

### 5.1 Missing Data & Warm-up Policy
- **Warm-up Policy:** [Describe warm-up or initialization period requirement, if any.]
- **Missing Data Handling:** [Describe behavior when missing, null, or NaN values are encountered.]

### 5.2 Numerical Precision Policy
- [Describe numerical precision, floating-point representation, rounding mode, and tolerance.]

### 5.3 Error Policy
- Invalid parameters fail closed during Pydantic schema validation.
- Runtime numerical errors raise explicit typed exceptions rather than returning unverified default values.

---

## 6. Persistence and State Management (Optional)

When this plugin retains durable state across invocations (e.g., sync markers, calibration checkpoints,
cached parameters, or local index records), state is managed under explicit host capability constraints.

### 6.1 Persisted-State Ownership

| Status | Partition / Table Name | Owning Feature | Schema Version | Storage Driver | Retention / Purge Policy | Public Read Boundary | Notes |
|---|---|---|---|---|---|---|---|
| `[Status]` | `[plugin]_[partition_name]` | `FEAT-[OWNER]-[CONCEPT]` | `1` | `sqlite` / `file` | `retain` / `purge_on_uninstall` | `[Port / Method]` | [Sync markers, cache, etc.] |

### 6.2 Plugin Persistence Invariants

- **Host Capability Mediation:** State is read/written exclusively through host-mediated persistence adapters. Zero direct raw SQL against shared database tables.
- **Namespace Isolation:** Plugin data is isolated to its declared namespace/partition and cannot be read or modified directly by sibling plugins.
- **Isolated Testing:** Tests verify state transitions against temporary in-memory stores (`:memory:`) or isolated test directories.

---

## 7. Deterministic Offline Usage Example

Every plugin must provide a self-contained, realistic, offline usage example under `tests/examples/`:

- **Path:** `tests/examples/[category]_[concept]_offline.py`
- **Execution:**
  ```bash
  uv run python tests/examples/[category]_[concept]_offline.py
  ```
- **Requirements:**
  - Must run completely offline with zero network or external database dependencies.
  - Uses static synthetic or fixture input data.
  - Demonstrates instantiation, parameter configuration, calculation, and output inspection.
  - Exits with returncode `0` on successful evaluation.

---

## 8. Verification and Definition of Done

### Focused Verification Commands

```bash
# Plugin unit, boundary, and error tests
uv run pytest tests/plugin/[category]/test_[concept].py --no-cov

# Verify deterministic offline example
uv run python tests/examples/[category]_[concept]_offline.py
```

### Definition of Done Checklist

- [ ] All code, schema, bounds, ports, and calculations reside in **one cohesive Python file** (`[concept].py`).
- [ ] Authoritative `package.json` with valid manifest schema and exact `owned_paths`.
- [ ] File represents a traced feature (`FEAT-[OWNER]-[CONCEPT]`).
- [ ] Every calculation/port method maps to a traced functional requirement (`FR-*`).
- [ ] (Optional) Plugin-local persistence state is isolated and verified using temporary test stores.
- [ ] Zero imports of sibling plugins, workspace internal implementation, or global singletons.
- [ ] Pydantic parameter schema with explicit constraints, defaults, min/max bounds, units, and UI hints.
- [ ] Fully verified technical policies (missing data, warm-up period, numerical precision, fail-closed errors).
- [ ] Self-contained deterministic offline example runs and passes in `tests/examples/`.
- [ ] Unit and boundary tests achieve $\ge 80\%$ branch coverage.
- [ ] Isolated package removal leaves surviving workspaces and tests 100% operational.

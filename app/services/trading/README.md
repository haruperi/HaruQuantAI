# Trading

> **Package:** `app/services/trading/`
> **Status:** `Implemented`
> **Last updated:** `2026-09-04`
> **Domain ID:** `D-TRD`

> This README is the domain package's **single source of truth** for domain boundaries, composable feature capabilities, architecture invariants, implementation sequence, progress, usage examples, and tests.
> Update this document before modifying or adding code.

---

## Code-Aligned Implementation Convention

This README is the sole current target registry for this domain's feature IDs and statuses, functional requirements, domain-local workflows, semantic contract ownership, persisted-state model, acceptance evidence, and deletion behavior. `PROJECT.md` owns system scope, cross-domain behavior, system NFRs, and release gates; `ARCHITECTURE.md` owns universal package and runtime constraints.

Implementation uses the repository's existing feature substrate: each feature lives directly at `app/services/<domain>/<feature>/`, is discovered through the `haruquantai.features` Python entry-point group, and declares one immutable `FeatureSpec` in `manifest.py`.

Every implemented feature also contains a mandatory runtime-validated `README.md`, pure `__init__.py`, strict `config.py`, lifecycle `feature.py`, and focused implementation modules. Dependencies and effects flow through `FeatureContext`/`FeatureScope`; cross-feature implementation imports are forbidden. Persistent state is declared by `FeatureSpec.state`; any migrations and storage adapters remain with the owning feature. Capability keys use `<domain>.<name>@<major>`.

Feature-level automated tests live at `tests/services/trading/<feature>/`. Usage examples never live under `tests/`; they belong to each feature's designated primary domain-logic module.

## 1. Purpose and Boundary

### Purpose

The Trading domain owns execution sessions, limits, profile projections, and order records. Its public feature capabilities are registered and remain independent of package-import order.

### Owns

- `FEAT-TRD-MANAGE_EXECUTION_SESSIONS` — Trading Execution Sessions and Account Profile.

### Does not own

- Network transport or HTTP/WebSocket endpoints (owned by Interfaces domain).
- Generic application configuration (owned by Workspace domain).
- Broker protocol adapters (owned by Broker domain).

### Shared Contracts

This domain semantically owns the contracts defined in `app/contracts/trading/` and wire schemas in `app/contracts/trading/wire/`.

**Owned by this domain**

| Status | Contract | Version | Counterparty | Purpose |
|---|---|---|---|---|
| Implemented | `FEAT-TRD-MANAGE_EXECUTION_SESSIONS` capability surface | `v1` | Interfaces | Trading execution session lifecycle, default session, account profile, and constraints. |

---

## 2. Feature Registry

| Feature ID | Directory | Status | Capability Key | State Namespace |
|---|---|---|---|---|
| `FEAT-TRD-MANAGE_EXECUTION_SESSIONS` | `manage_execution_sessions/` | Implemented | `trading.manage-execution-sessions@1` | `trading.manage_execution_sessions` |

---

## 3. Architecture Rules

1. Every feature is packaged as `app/services/trading/<feature>/`.
2. Features never import other features directly; cross-feature interaction goes through `FeatureContext`.
3. Persistent state is managed within the owning feature with explicit connection lifecycle.
4. Unmounted features fail closed with `CAPABILITY_UNAVAILABLE`.

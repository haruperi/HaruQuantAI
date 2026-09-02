# Brokers

> **Package:** `app/services/brokers/`
> **Status:** `Active — service-level broker resolver enabled`
> **Last updated:** `2026-09-02`
> **Domain ID:** `D-BRK`

> This README is the domain package's **single source of truth** for domain boundaries, composable feature capabilities, architecture invariants, implementation sequence, progress, usage examples, and tests.
> Update this document before modifying or adding code.

---

## 1. Purpose and Boundary

### Purpose

The Brokers domain delivers direct passthrough connections, provider normalization, session lifecycle management, and active broker module resolution for external market-data and trading platforms (e.g. MetaTrader 5, cTrader, Binance, Dukascopy, Yahoo Finance).

### Owns

- `FEAT-BRK-RESOLVE` — Service-Level Broker Resolver (`broker.resolver@1`). Centralizes active broker module selection so API routes and services do not own broker adapter policy.
- `broker` table in SQLite database `haruquantai.db` managed via feature-internal persistence.
- Direct provider channels and session routing.

### Does not own

- Trade signal formulation or playbook rules (owned by Strategy `D-STR`).
- Exposure limits, capital reservation, or risk gates (owned by Risk `D-RSK`).
- Order lifecycle state reconciliation (owned by Trading `D-TRD`).
- Historical bar transformations or dataset persistence (owned by Data `D-DAT`).

---

## 2. Package Structure and Feature Capabilities

```text
brokers/
├── README.md
├── __init__.py
└── resolve/                             # FEAT-BRK-RESOLVE: Service-Level Broker Resolver
    ├── README.md
    ├── __init__.py
    ├── _persistence.py                  # Internal SQLite CRUD & table lifecycle
    ├── manifest.py
    ├── config.py
    ├── feature.py
    └── router.py                        # Primary domain logic & public router functions
```

### Registered Capabilities

| Domain | Feature | Provides | Required Capabilities | Optional Capabilities | Removal Result |
|---|---|---|---|---|---|
| **Brokers** | `FEAT-BRK-RESOLVE` Service-Level Broker Resolver | `broker.resolver@1` | `—` | `utils.logging@1` | Active broker resolution degrades to static fallback defaults |

---

## 3. Persisted State Ownership

| Status | State / Store | Read Access (via contract) | Migration / Management |
|---|---|---|---|
| Complete | `broker` table in `haruquantai.db` | Via `broker.resolver@1` and `router.py` | Internal feature persistence in `app/services/brokers/resolve/_persistence.py` |

### Database Table Schema

```sql
CREATE TABLE IF NOT EXISTS broker (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(50) NOT NULL,
    platform VARCHAR(50),
    desc VARCHAR(250),
    active BOOLEAN NOT NULL,
    timezone VARCHAR(100)
);
```

---

## 4. Architectural Invariants

1. **Passthrough Principle**: Brokers domain owns no trading strategy rules or risk verdicts.
2. **Centralized Routing**: API routes and worker services query the broker resolver to determine active provider adapters rather than hardcoding adapter policies.
3. **Internal Persistence Encapsulation**: Database DDL, initialization, and CRUD operations for the `broker` table are owned exclusively by `resolve/_persistence.py`.
4. **Fail-Closed Fallback**: If no broker is marked active in the database or runtime settings, resolution falls back to safe defaults or fails closed.

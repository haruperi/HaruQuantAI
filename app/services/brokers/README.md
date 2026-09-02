# Brokers

> **Package:** `app/services/brokers/`
> **Status:** `Active — service-level broker resolver & operations enabled`
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
- `FEAT-BRK-OPERATIONS` — Broker Operations (`broker.operations@1`). Standard broker-neutral operational functions without business logic.
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
├── resolve/                             # FEAT-BRK-RESOLVE: Service-Level Broker Resolver
│   ├── README.md
│   ├── __init__.py
│   ├── _persistence.py                  # Internal SQLite CRUD & table lifecycle
│   ├── manifest.py
│   ├── config.py
│   ├── feature.py
│   └── router.py                        # Primary domain logic & public router functions
└── operations/                          # FEAT-BRK-OPERATIONS: Broker Operations
    ├── README.md
    ├── __init__.py
    ├── _terminal_info.py                # FR 1: Environment & connection properties
    ├── _account_info.py                 # FR 2: Account balances & permissions
    ├── _symbol_info.py                  # FR 3: Symbols & market data subscriptions
    ├── _order_info.py                   # FR 4: Pending & active orders
    ├── _history_order_info.py           # FR 5: Historical orders
    ├── _deals_info.py                   # FR 6: Deals & transactions
    ├── _positions_info.py               # FR 7: Open positions
    ├── _trade.py                        # FR 8: Trade execution & calculations
    ├── config.py
    ├── manifest.py
    ├── feature.py
    └── execute.py                       # FR 9: Execution bridge & entry point
```

### Registered Capabilities

| Domain | Feature | Provides | Required Capabilities | Optional Capabilities | Removal Result |
|---|---|---|---|---|---|
| **Brokers** | `FEAT-BRK-RESOLVE` Service-Level Broker Resolver | `broker.resolver@1` | `—` | `utils.logging@1` | Active broker resolution degrades to static fallback defaults |
| **Brokers** | `FEAT-BRK-OPERATIONS` Broker Operations | `broker.operations@1` | `—` | `utils.logging@1` | Broker-neutral operations degrade to direct manual adapter calls |

---

## 3. Persisted State Ownership

| Status | State / Store | Read Access (via contract) | Migration / Management |
|---|---|---|---|
| Complete | `broker` table in `haruquantai.db` | Via `broker.resolver@1` and `router.py` | Internal feature persistence in `app/services/brokers/resolve/_persistence.py` |
| Complete | Operations cache & subscriptions in `haruquantai.db` | Via `broker.operations@1` and `execute.py` | Internal feature persistence in `app/services/brokers/operations/` |

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
4. **Operation Neutrality**: Operational modules (`operations/`) contain no business policy, risk constraints, or strategy signals; they purely execute standard broker-neutral actions.
5. **Fail-Closed Fallback**: If no broker is marked active in the database or runtime settings, resolution falls back to safe defaults or fails closed.

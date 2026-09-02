# Brokers

> **Package:** `app/services/brokers/`
> **Status:** `Active — broker resolver & multi-broker provider channels enabled`
> **Last updated:** `2026-09-02`
> **Domain ID:** `D-BRK`

> This README is the domain package's **single source of truth** for domain boundaries, composable feature capabilities, architecture invariants, implementation sequence, progress, usage examples, and tests.
> Update this document before modifying or adding code.

---

## 1. Purpose and Boundary

### Purpose

The Brokers domain delivers direct passthrough connections, provider normalization, session lifecycle management, and active broker module resolution for external market-data and trading platforms (MetaTrader 5, cTrader, Binance, Dukascopy, Yahoo Finance).

### Owns

- `FEAT-BRK-RESOLVE` — Service-Level Broker Resolver (`broker.resolver@1`). Centralizes active broker module selection and operational routing.
- `FEAT-BRK-METATRADER` — MetaTrader 5 Connection (`broker.provider.metatrader@1`, `broker.operations@1`).
- `FEAT-BRK-CTRADER` — cTrader Provider Connection (`broker.provider.ctrader@1`, `broker.operations@1`).
- `FEAT-BRK-BINANCE` — Binance Provider Connection (`broker.provider.binance@1`, `broker.operations@1`).
- `FEAT-BRK-DUKASCOPY` — Dukascopy Provider Connection (`broker.provider.dukascopy@1`, `broker.operations@1`).
- `FEAT-BRK-YAHOO` — Yahoo Finance Provider (`broker.provider.yahoo@1`, `broker.operations@1`).
- `broker` table in SQLite database `haruquantai.db` managed via feature-internal persistence.

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
├── resolve/                             # FEAT-BRK-RESOLVE: Broker Resolver & Router
├── metatrader/                          # FEAT-BRK-METATRADER: MetaTrader 5 Provider Channel
├── ctrader/                             # FEAT-BRK-CTRADER: cTrader OpenAPI Provider Channel
├── binance/                             # FEAT-BRK-BINANCE: Binance Crypto Provider Channel
├── dukascopy/                           # FEAT-BRK-DUKASCOPY: Dukascopy JForex Provider Channel
└── yahoo/                               # FEAT-BRK-YAHOO: Yahoo Finance Market Data Provider
```

### Registered Capabilities

| Domain | Feature | Provides | Required Capabilities | Optional Capabilities | Removal Result |
|---|---|---|---|---|---|
| **Brokers** | `FEAT-BRK-RESOLVE` Service-Level Broker Resolver | `broker.resolver@1` | `—` | `utils.logging@1` | Active broker resolution degrades to static fallback defaults |
| **Brokers** | `FEAT-BRK-METATRADER` MetaTrader 5 Connection | `broker.provider.metatrader@1`, `broker.operations@1` | `—` | `utils.logging@1` | MetaTrader 5 direct provider channel becomes unavailable |
| **Brokers** | `FEAT-BRK-CTRADER` cTrader Connection | `broker.provider.ctrader@1`, `broker.operations@1` | `—` | `utils.logging@1` | cTrader direct provider channel becomes unavailable |
| **Brokers** | `FEAT-BRK-BINANCE` Binance Connection | `broker.provider.binance@1`, `broker.operations@1` | `—` | `utils.logging@1` | Binance crypto provider channel becomes unavailable |
| **Brokers** | `FEAT-BRK-DUKASCOPY` Dukascopy Connection | `broker.provider.dukascopy@1`, `broker.operations@1` | `—` | `utils.logging@1` | Dukascopy provider channel becomes unavailable |
| **Brokers** | `FEAT-BRK-YAHOO` Yahoo Finance Provider | `broker.provider.yahoo@1`, `broker.operations@1` | `—` | `utils.logging@1` | Yahoo Finance market data provider becomes unavailable |

---

## 3. Persisted State Ownership

| Status | State / Store | Read Access (via contract) | Migration / Management |
|---|---|---|---|
| Complete | `broker` table in `haruquantai.db` | Via `broker.resolver@1` and `router.py` | Internal feature persistence in `app/services/brokers/resolve/_persistence.py` |
| Complete | MT5 credentials & preferences | Via `_persistence.py` in `metatrader/` | Internal feature persistence in `app/services/brokers/metatrader/_persistence.py` |
| Complete | cTrader credentials & preferences | Via `_persistence.py` in `ctrader/` | Internal feature persistence in `app/services/brokers/ctrader/_persistence.py` |
| Complete | Binance credentials & preferences | Via `_persistence.py` in `binance/` | Internal feature persistence in `app/services/brokers/binance/_persistence.py` |
| Complete | Dukascopy credentials & preferences | Via `_persistence.py` in `dukascopy/` | Internal feature persistence in `app/services/brokers/dukascopy/_persistence.py` |
| Complete | Yahoo Finance preferences | Via `_persistence.py` in `yahoo/` | Internal feature persistence in `app/services/brokers/yahoo/_persistence.py` |

---

## 4. Architectural Invariants

1. **Passthrough Principle**: Brokers domain owns no trading strategy rules or risk verdicts.
2. **Centralized Routing**: API routes and worker services query the broker resolver to discover active adapters.
3. **Internal Persistence Encapsulation**: Database DDL, initialization, and CRUD operations for credentials and tables are owned strictly within feature persistence files.
4. **Zero Silent Fallback / Strict Error Architecture**: All broker modules require a genuine active connection; uninitialized queries or unsupported operations strictly raise explicit `RuntimeError`, `ValueError`, or `NotImplementedError` indicating the exact unavailable capability.
5. **Fail-Closed Fallback**: Unconfigured providers fail closed immediately without returning fabricated trading or market data.

# HaruQuantAI Capability Catalog & Model

This document serves as the formal **Capability Catalog** and architectural specification for HaruQuantAI's spatiotemporal composability system.

---

## 1. Architectural Principles

1. **Capability-Oriented Composition**: Components interact through versioned capability contracts rather than direct imports of concrete feature packages.
2. **Narrow Capabilities**: Capabilities are granular single-responsibility interfaces (e.g. `data.historical-bars@1`) rather than monolithic service blobs.
3. **Reversible Runtime Scopes**: Every capability provider registers its services, listeners, tasks, and state through a lifecycle-managed `FeatureContext`.
4. **Graceful Absence**: If a provider is physically deleted or disabled, dependent features transition to `BLOCKED` or fallback modes without crashing the application shell.
5. **Profile-Driven Criticality**: Criticality is defined by deployment profiles (`research`, `backtest`, `live`), not hardcoded inside feature implementations.

---

## 2. Capability Identifier Convention

Capabilities are uniquely and immutably identified by the format:

```text
<domain>.<capability-name>@<major-version>
```

- **`domain`**: The logical business boundary (e.g. `data`, `broker`, `risk`, `strategy`).
- **`capability-name`**: The specific functional responsibility (e.g. `historical-bars`, `market-data`, `storage`).
- **`major-version`**: SemVer major version of the contract. Breaking contract changes bump the major version.

---

## 3. Implemented Capability Catalog (Runtime Truth)

The following features and capabilities are fully implemented in the codebase and verified by automated documentation and physical-removability CI checks:

| Feature ID | Domain | Feature Description | Provides | Requires | Optional | Removal / Absence Result |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **`FEAT-SYS-PERSIST_STORAGE`** | `system` | Persistent Storage Engine (SQLite & Disk) | `system.storage@1` | — | — | Storage capability becomes unavailable; consumers transition to `BLOCKED`. |
| **`FEAT-BROKER-FEED_MOCK`** | `broker` | Synthetic Deterministic Raw Bar Generator | `broker.market-data@1` | — | — | Market data capability becomes unavailable; consumers transition to `BLOCKED`. |
| **`FEAT-DATA-RETRIEVE_BARS`** | `data` | Historical OHLCV Bar Retrieval & Normalization | `data.historical-bars@1` | `broker.market-data@1` | — | Historical bars become unavailable; research & backtest queries fail cleanly. |

---

## 4. Planned & Roadmap Capability Catalog

The following capabilities and features are scheduled for development in future milestone phases:

| Feature ID | Domain | Feature Description | Provides | Requires | Optional | Removal / Absence Result |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **`FEAT-SYS-PROVIDE_CLOCK`** | `system` | System Clock & Timing | `system.clock@1` | — | — | System falls back to standard UTC clock. |
| **`FEAT-SYS-COLLECT_METRICS`** | `system` | Metrics & Telemetry | `system.metrics@1` | `system.clock@1` | — | Telemetry collection becomes no-op. |
| **`FEAT-DATA-STREAM_TICKS`**| `data` | Realtime Tick Streaming | `data.realtime-ticks@1` | `broker.market-data@1` | `system.metrics@1` | Live tick streaming becomes unavailable; live trading blocked. |
| **`FEAT-DATA-CACHE_BARS`**| `data` | Bar & Tick Cache Store | `data.bar-cache@1` | `system.storage@1` | `system.metrics@1` | Data is fetched directly from broker without caching. |
| **`FEAT-BROKER-ADAPT_MT5`**| `broker` | MetaTrader 5 Adapter | `broker.market-data@1`<br>`broker.execution@1` | `system.clock@1` | `system.metrics@1` | MT5 market data & execution become unavailable. |
| **`FEAT-RISK-APPROVE_ORDER`** | `risk` | Pre-Trade Risk & Approval | `risk.approval@1`<br>`risk.limits@1` | `portfolio.positions@1` | `system.metrics@1` | Live trade execution blocked (safety invariant). |
| **`FEAT-PORTFOLIO-TRACK_POSITIONS`**| `portfolio`| Position & Balance Tracker | `portfolio.positions@1` | `broker.market-data@1` | `system.storage@1` | Position tracking unavailable; live trading & risk blocked. |
| **`FEAT-TRADING-EXECUTE_LIVE`** | `trading` | Live Order Execution | `trading.execution@1` | `broker.execution@1`<br>`risk.approval@1`<br>`portfolio.positions@1` | `system.metrics@1` | Live trading execution disabled. |

---

## 5. Deployment Profiles

Criticality is resolved by comparing active capabilities against the active deployment profile:

```toml
[application]
profile = "research"  # Options: "research", "backtest", "live", "offline"

# Providers selection mapping
[providers]
"broker.market-data@1" = "FEAT-BROKER-FEED_MOCK"
"data.historical-bars@1" = "FEAT-DATA-RETRIEVE_BARS"
"system.storage@1" = "FEAT-SYS-PERSIST_STORAGE"
```

---

## 6. Liveness vs Readiness Semantics

- **Liveness (`/system/liveness`)**:
  Returns `OK (200)` as long as the Kernel, Registry, and HTTP/API shell are running and responsive.
- **Readiness (`/system/readiness`)**:
  Returns `OK (200)` only if **all required capabilities** for the active profile are `ACTIVE`.
  If a required capability is `MISSING` or `BLOCKED`, readiness returns `DEGRADED (503)` with a machine-readable diagnostic explaining which provider or upstream dependency failed.

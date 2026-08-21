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
- **`capability-name`**: The specific functional responsibility (e.g. `historical-bars`, `market-data`, `approval`).
- **`major-version`**: SemVer major version of the contract. Breaking contract changes bump the major version.

---

## 3. Core Capability Catalog

| Feature ID | Domain | Feature Description | Provides | Requires | Optional | Removal / Absence Result |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **`FEAT-SYS-PROVIDE_CLOCK`** | `system` | System Clock & Timing | `system.clock@1` | — | — | System falls back to standard system clock. |
| **`FEAT-SYS-COLLECT_METRICS`** | `system` | Metrics & Telemetry | `system.metrics@1` | `system.clock@1` | — | Telemetry and metric collection become no-op. |
| **`FEAT-SYS-PERSIST_STORAGE`** | `system` | Persistent Storage Engine | `system.storage@1` | — | `system.metrics@1` | Disk caching and persistence become in-memory only. |
| **`FEAT-BROKER-REGISTER_ADAPTERS`**| `broker` | Broker Registry | `broker.registry@1` | — | `system.metrics@1` | Broker adapters cannot register; broker subsystem disabled. |
| **`FEAT-BROKER-ADAPT_MT5`**| `broker` | MetaTrader 5 Adapter | `broker.market-data@1`<br>`broker.execution@1` | `broker.registry@1`<br>`system.clock@1` | `system.metrics@1` | MT5 market data and execution become unavailable. |
| **`FEAT-BROKER-ADAPT_BINANCE`**| `broker` | Binance Adapter | `broker.market-data@1`<br>`broker.execution@1` | `broker.registry@1`<br>`system.clock@1` | `system.metrics@1` | Binance spot/futures market data & execution become unavailable. |
| **`FEAT-BROKER-ADAPT_CTRADER`**| `broker` | cTrader Adapter | `broker.market-data@1`<br>`broker.execution@1` | `broker.registry@1`<br>`system.clock@1` | `system.metrics@1` | cTrader market data & execution become unavailable. |
| **`FEAT-DATA-RETRIEVE_BARS`**| `data` | Historical Bars Retrieval | `data.historical-bars@1` | `broker.market-data@1` | `data.bar-cache@1`<br>`system.metrics@1` | Historical data retrieval becomes unavailable; research blocked. |
| **`FEAT-DATA-STREAM_TICKS`**| `data` | Realtime Tick Streaming | `data.realtime-ticks@1` | `broker.market-data@1` | `system.metrics@1` | Live tick streaming becomes unavailable; live trading blocked. |
| **`FEAT-DATA-CACHE_BARS`**| `data` | Bar & Tick Cache Store | `data.bar-cache@1` | `system.storage@1` | `system.metrics@1` | Data is fetched directly from broker on every request (no cache). |
| **`FEAT-DATA-FETCH_CALENDAR`**| `data` | Economic Calendar | `data.economic-calendar@1` | — | `data.bar-cache@1` | Macro news events unavailable; news filters become no-op. |
| **`FEAT-INDICATOR-CALCULATE_INDICATORS`** | `indicator`| Technical Indicators Engine | `indicator.engine@1` | `data.historical-bars@1` | `system.metrics@1` | Technical indicator calculations unavailable; strategies relying on indicators block. |
| **`FEAT-RISK-APPROVE_ORDER`** | `risk` | Pre-Trade Risk & Approval | `risk.approval@1`<br>`risk.limits@1` | `portfolio.positions@1` | `system.metrics@1` | Live trade execution is blocked (safety invariant). |
| **`FEAT-PORTFOLIO-TRACK_POSITIONS`**| `portfolio`| Position & Balance Tracker | `portfolio.positions@1` | `broker.market-data@1` | `system.storage@1` | Position tracking unavailable; live trading & risk blocked. |
| **`FEAT-STRATEGY-GENERATE_SIGNALS`**| `strategy` | Strategy Engine & Dispatch | `strategy.engine@1` | `data.historical-bars@1` | `indicator.engine@1`<br>`risk.approval@1` | Strategy execution and signal generation disabled. |
| **`FEAT-TRADING-EXECUTE_LIVE`** | `trading` | Live Order Execution | `trading.execution@1` | `broker.execution@1`<br>`risk.approval@1`<br>`portfolio.positions@1` | `system.metrics@1` | Live trading execution disabled; process remains in read-only / research mode. |
| **`FEAT-RESEARCH-PREPARE_DATASET`** | `research`| Research Datasets & Lab | `research.dataset@1` | `data.historical-bars@1` | `indicator.engine@1` | Research notebook and dataset tools become unavailable. |
| **`FEAT-SIMULATOR-RUN_BACKTEST`** | `simulator`| Backtesting Simulator | `simulator.engine@1` | `data.historical-bars@1` | `indicator.engine@1` | Backtesting simulations disabled. |
| **`FEAT-OPTIMIZE-SEARCH_PARAMETERS`** | `optimization`| Strategy Parameter Optimizer | `optimization.engine@1` | `simulator.engine@1` | `system.metrics@1` | Parameter sweeps and genetic optimization disabled. |
| **`FEAT-AGENTIC-ANALYZE_MARKET`** | `agentic` | AI Agent Market Analyst | `agentic.analyst@1` | `data.historical-bars@1` | `research.dataset@1`<br>`data.economic-calendar@1` | AI advisory and agent analysis disabled; quantitative core unaffected. |

---

## 4. Deployment Profiles

Criticality is resolved by comparing active capabilities against the active deployment profile:

```toml
# Configuration Example: config/production.toml

[profiles.research]
name = "Quantitative Research Environment"
required_capabilities = [
    "system.clock@1",
    "data.historical-bars@1",
    "research.dataset@1",
    "simulator.engine@1",
]

[profiles.backtest]
name = "Simulation & Optimization Runner"
required_capabilities = [
    "system.clock@1",
    "data.historical-bars@1",
    "simulator.engine@1",
    "optimization.engine@1",
]

[profiles.live]
name = "Live Execution Node"
required_capabilities = [
    "system.clock@1",
    "broker.market-data@1",
    "broker.execution@1",
    "data.realtime-ticks@1",
    "portfolio.positions@1",
    "risk.approval@1",
    "trading.execution@1",
]
```

---

## 5. Liveness vs Readiness Semantics

- **Liveness (`/system/liveness`)**:
  Returns `OK (200)` as long as the Kernel, Registry, and HTTP/API shell are running and responsive.
- **Readiness (`/system/readiness`)**:
  Returns `OK (200)` only if **all required capabilities** for the active profile are `ACTIVE`.
  If a required capability is `MISSING` or `BLOCKED`, readiness returns `DEGRADED (503)` with a machine-readable diagnostic explaining which provider or upstream dependency failed.

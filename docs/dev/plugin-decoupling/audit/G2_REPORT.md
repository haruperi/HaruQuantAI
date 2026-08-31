# G2 Classification Report

> **Status:** `PASS`
> **Artifact Source:** [removability_matrix.json](file:///c:/Users/rharu/AppDev/HaruquantAI/docs/dev/plugin-decoupling/audit/removability_matrix.json)
> **Authoritative Gate:** Gate G2

---

## Inputs

The G2 Audit synthesizes five independent static, runtime, state, and frontend graphs with authoritative domain README Feature Registries across the HaruquantAI codebase:

- **Static Dependency Graph**: [static_graph.json](file:///c:/Users/rharu/AppDev/HaruquantAI/docs/dev/plugin-decoupling/audit/static_graph.json) (3,008 nodes, 36,577 edges, 57 dynamic imports)
- **Runtime Configuration Graph**: [runtime_configuration_graph.json](file:///c:/Users/rharu/AppDev/HaruquantAI/docs/dev/plugin-decoupling/audit/runtime_configuration_graph.json) (2,416 runtime edges, 1,232 configuration references)
- **State and Frontend Graph**: [state_frontend_graph.json](file:///c:/Users/rharu/AppDev/HaruquantAI/docs/dev/plugin-decoupling/audit/state_frontend_graph.json) (370 database state edges, 1,282 frontend widget edges, 9,763 serialized class paths)
- **Authoritative Feature Registries**: 253 unique features across 15 domains (245 Completed, 8 Pending, 0 Partial).

---

## Domain Matrix

| Domain | Removability Tier | Feature Count | Completed | Pending | Primary Classification |
|---|:---:|---:|---:|---:|---|
| `agentic` | B | 22 | 22 | 0 | `optional_provider` |
| `analytics` | B | 14 | 14 | 0 | `optional_provider` |
| `api` | B | 28 | 28 | 0 | `composition_only_module` |
| `brokers` | B | 13 | 13 | 0 | `optional_provider` |
| `data` | B | 14 | 14 | 0 | `optional_provider` |
| `indicators` | A | 12 | 12 | 0 | `optional_provider` |
| `optimization` | B | 13 | 13 | 0 | `optional_provider` |
| `portfolio` | B | 14 | 14 | 0 | `optional_provider` |
| `research` | B | 16 | 16 | 0 | `optional_provider` |
| `risk` | C | 14 | 14 | 0 | `required_profile_provider` |
| `simulator` | B | 20 | 20 | 0 | `optional_provider` |
| `strategy` | B | 20 | 20 | 0 | `optional_provider` |
| `trading` | B | 17 | 17 | 0 | `optional_provider` |
| `ui` | B | 31 | 23 | 8 | `optional_provider` |
| `utils` | C | 5 | 5 | 0 | `protected_kernel_candidate` |
| **Total** | | **253** | **245** | **8** | |

---

## Provider Matrix

All 253 registered application features are mapped to discrete, versioned provider capabilities.

### Tier A (Pure Calculations)
- `indicators.*` (12 features): `indicators.adx.v1`, `indicators.atr.v1`, `indicators.bollinger.v1`, `indicators.ema.v1`, `indicators.macd.v1`, `indicators.obv.v1`, `indicators.rsi.v1`, `indicators.sma.v1`, `indicators.stochastic.v1`, `indicators.supertrend.v1`, `indicators.vwap.v1`, `indicators.williams_r.v1`.

### Tier B (Business Services & Swappable Providers)
- `brokers.*` (13 features): MT5, cTrader, Binance, Dukascopy, Yahoo adapters and market data feeds.
- `data.*` (14 features): Ingestion, storage, normalization, feeds, time sessions, tick derivation.
- `strategy.*` (20 features): Signal generators, versioning, checkpoints, configs, execution intents.
- `trading.*` (17 features): Intent valuation, order request construction, lifecycle tracking, execution sessions.
- `simulator.*` (20 features): Historical backtest engine, synthetic broker matching, execution replay.
- `analytics.*` (14 features): Journal, trade metrics, drawdown analysis, performance attribution.
- `optimization.*` (13 features): Parameter space search, objective evaluation, walk-forward analysis.
- `research.*` (16 features): Dataset analysis, statistical testing, alpha studies, regime classification.
- `portfolio.*` (14 features): Position aggregation, FX valuation, risk-budget allocation, rebalancing.
- `agentic.*` (22 features): Autonomous agent roles, councils, artifacts, deliberative workflows.
- `api.*` (28 features): Workstation routes, session bridge, SSE streams, command handlers.
- `ui.*` (31 features): Composable widgets (Chart, OrderTicket, Positions, Analytics, Simulator, Watchlists).

### Tier C (Core Infrastructure & Safety Gate)
- `utils.*` (5 features): System logger, UTC time, error catalog, serialization, settings.
- `risk.*` (14 features): Mandatory Risk Gate, exposure validation, drawdown guard, fail-closed kill switch.

---

## Dependency Edges

The dependency graph contains 36,577 static and runtime coupling edges across the repository.

- Core dependency flow: `composition → provider factory → injected capability; business consumer → capability spec; kernel ↛ business domain`.
- All cross-domain calls route through public interfaces and capability specifications without deep module coupling.

---

## Hard Cycles

| Cycle ID | Domains Involved | Cycle Kind | Break Edge | Break Method | Description |
|---|---|---|---|---|---|
| `HC-01` | `research` ⇄ `analytics` | `hard_code_cycle` | `research -> analytics` | `contract` | Decouple metric dependency by injecting `app/contracts/analytics/metrics/v1.py` specification into Research consumers. |

---

## Reactive Event Cycles

| Cycle ID | Domains Involved | Description | Governance |
|---|---|---|---|
| `RC-01` | `trading` ⇄ `simulator` | Simulator replays historical events through Trading sim route; Trading dispatches orders to Simulator channel. | Injected authority port (`_SimulationAuthorityPort`) preserves structural acyclicity. |

---

## Dynamic Import Allowlist

The following dynamic imports are explicitly audited, verified, and allowlisted:

| Module Name | Reason & Usage Scope |
|---|---|
| `MetaTrader5` | Optional native C extension broker SDK for live/demo MT5 connectivity. |
| `ctrader_open_api` | Optional protobuf SDK for cTrader OpenAPI connectivity. |
| `binance` | Optional Binance Spot/Futures REST & WebSocket SDK. |
| `yfinance` | Optional public Yahoo Finance market data scraper. |
| `pandas` | Optional heavy DataFrame library for tabular transformations. |
| `numpy` | Optional high-performance numerical array operations. |
| `exchange_calendars` | Optional exchange trading session schedule definitions. |

---

## Wave Inputs

The 21 migration waves in Phase 12 are assigned exact, ordered provider scopes:

1. **Wave 12.1**: `utils` (kernel primitives, errors, time, identity, serialization, settings, logging).
2. **Wave 12.2**: `data_core` (connection, locking, transaction, migration ledger, historical storage, normalization).
3. **Wave 12.3**: `brokers_read` (provider-neutral specs, account reads, symbol metadata, MT5/cTrader/Binance/Dukascopy/Yahoo).
4. **Wave 12.4**: `data_stream` (broker stream adapters, tick streams, sequence ordering, reconnection).
5. **Wave 12.5**: `indicators` (pure formulas, RSI, Williams %R, ATR, MACD, Bollinger Bands, EMA, SMA, Stochastic, VWAP).
6. **Wave 12.6**: `analytics` (trade metrics, net PnL, drawdown calculation, performance attribution, reporting).
7. **Wave 12.7**: `strategy` (strategy definitions, versions, parameter configs, signal generation, checkpoints).
8. **Wave 12.8**: `portfolio_read` (positions, holdings, FX valuation, margin views, exposure reporting).
9. **Wave 12.9**: `risk_core` (risk limits, exposure evaluation, drawdown guard, non-disableable kill switch).
10. **Wave 12.10**: `portfolio_alloc` (multi-strategy allocation proposals, rebalancing plans).
11. **Wave 12.11**: `trading_core` (intent contracts, order request construction, lifecycle states, execution sessions).
12. **Wave 12.12**: `trading_preflight` (lineage validation, positive Risk authorization preflight, cycle timeout).
13. **Wave 12.13**: `simulator` (simulation clock, queue, replay engine, synthetic broker matching, batch runs).
14. **Wave 12.14**: `brokers_mutation` (broker order placement, cancel, modify, transport circuit recovery).
15. **Wave 12.15**: `trading_live` (demo and live execution routes, credential binding, execution safety).
16. **Wave 12.16**: `research` (dataset validation, statistical tests, alpha factor studies, drift detection).
17. **Wave 12.17**: `optimization` (parameter search spaces, sampler algorithms, objective scoring, robustness).
18. **Wave 12.18**: `agentic` (agent roles, memory, council deliberation, autonomous workflows, artifacts).
19. **Wave 12.19**: `api` (workstation routes, session bridge, SSE streams, composition root migration).
20. **Wave 12.20**: `ui` (single-page widget workspace, dynamic docking canvas, typed client integrations).
21. **Wave 12.21**: `cleanup` (internal compatibility import removal, obsolete wrapper elimination).

---

## Gate Result

**GATE G2 STATUS: PASS**

- All 253 registered application features classified into Removability Tiers.
- 100% of dynamic imports audited and accounted for.
- Exactly 1 hard code cycle identified with an approved specification-break edge (`HC-01`).
- Exact provider inputs established for all 21 migration waves.

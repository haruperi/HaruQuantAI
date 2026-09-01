# Services Architecture & Master Feature Registry

> **Root Package:** `app/services/`
> **System Scope:** Backend domain services, core algorithmic engines, provider adapters, and API orchestration gateway.
> **Governance:** Authoritative capability mapping according to `docs/PROJECT.md`, `docs/ARCHITECTURE.md`, and `AGENTS.md`.

---

## 1. Architectural Overview

The `app/services/` layer houses all backend domain capabilities of HaruQuantAI. Every domain operates under **Spatiotemporal Provider Architecture**:
- **Pure Domain Isolation**: Features within a service never directly import sibling service implementations.
- **Contract-Driven Boundaries**: Cross-domain collaboration occurs strictly via versioned capability contracts in `app/contracts/`.
- **Deterministic Composition**: The API composition root (`app/services/api/composition/`) and kernel resolver assemble runtime dependency graphs from explicit provider manifests.
- **Graceful Degradation & Fail-Closed Safety**: Optional providers (e.g. specialized research or optimization algorithms) degrade gracefully when unmounted; safety-critical gates (e.g. Risk, Kill-Switch) fail closed.

---

## 2. Domain Summary Matrix

| Domain | Package | Removability Tier | Feature Count | Primary Responsibility |
|---|---|:---:|---:|---|
| `Brokers` | [`app/services/brokers`](brokers/README.md) | **B** | 13 | Direct passthrough connections to external broker & market-data platforms |
| `Data` | [`app/services/data`](data/README.md) | **B** | 15 | Acquisition, normalization, historical storage, and streaming feeds |
| `Indicators` | [`app/services/indicators`](indicators/README.md) | **A** | 12 | Deterministic, pure-function technical and statistical indicator calculations |
| `Strategy` | [`app/services/strategy`](strategy/README.md) | **B** | 20 | Signal generation, trade intent formulation, and playbook evaluation |
| `Risk` | [`app/services/risk`](risk/README.md) | **C** | 17 | Master gate governance: exposure validation, drawdown guard, and kill switches |
| `Trading` | [`app/services/trading`](trading/README.md) | **B** | 12 | Execution of approved trade intents across sim, demo, and live routes |
| `Simulator` | [`app/services/simulator`](simulator/README.md) | **B** | 19 | Deterministic historical backtesting and execution realism engine |
| `Analytics` | [`app/services/analytics`](analytics/README.md) | **B** | 11 | Read-only performance measurement, returns, metrics, and tear-sheets |
| `Optimization` | [`app/services/optimization`](optimization/README.md) | **B** | 9 | Parameter space search, objective scoring, and walk-forward validation |
| `Research` | [`app/services/research`](research/README.md) | **B** | 16 | Sandboxed alpha discovery, hypothesis testing, and regime modeling |
| `Portfolio` | [`app/services/portfolio`](portfolio/README.md) | **B** | 12 | Multi-strategy portfolio construction, risk-budgeting, and rebalancing |
| `API` | [`app/services/api`](api/README.md) | **B** | 28 | FastAPI composition gateway exposing authenticated HTTP and SSE boundaries |

---

## 3. Master Feature Capability Registry

The following table catalogues all **184 service features** across the 12 domains in `app/services/`, defined in explicit capability terms:

| Domain | Feature | Provides | Required capabilities | Optional capabilities | Removal result |
|---|---|---|---|---|---|
| **Brokers** | `FEAT-BRK-00` Instrument & Venue Profiles | `broker.instruments@1` | `utils.time@1` | `utils.logging@1` | Symbol normalization & venue metadata become unavailable |
| **Brokers** | `FEAT-BRK-01` Capability Matrix & Flags | `broker.capabilities@1` | `—` | `utils.logging@1` | Dynamic adapter capability discovery falls back to static defaults |
| **Brokers** | `FEAT-BRK-02` MetaTrader Direct Channel | `broker.mt5.channel@1` | `broker.instruments@1` | `utils.logging@1` | MT5 account reads and demo order execution become unavailable |
| **Brokers** | `FEAT-BRK-03` cTrader Direct Channel | `broker.ctrader.channel@1` | `broker.instruments@1` | `utils.logging@1` | cTrader market data, streaming quotes, and execution become unavailable |
| **Brokers** | `FEAT-BRK-04` Binance Direct Channel | `broker.binance.channel@1` | `broker.instruments@1` | `utils.logging@1` | Binance spot market data and stream subscriptions become unavailable |
| **Brokers** | `FEAT-BRK-05` Dukascopy Direct Channel | `broker.dukascopy.channel@1` | `broker.instruments@1` | `utils.logging@1` | Dukascopy historical tick/bar web data becomes unavailable |
| **Brokers** | `FEAT-BRK-06` Yahoo Direct Channel | `broker.yahoo.channel@1` | `broker.instruments@1` | `utils.logging@1` | Yahoo Finance public historical bars become unavailable |
| **Brokers** | `FEAT-BRK-07` Route & Session Discipline | `broker.routing@1` | `broker.capabilities@1` | `utils.logging@1` | Health-aware multi-broker failover routing becomes disabled |
| **Brokers** | `FEAT-BRK-08` Simulation & Live Isolation | `broker.isolation@1` | `—` | `utils.logging@1` | Environment isolation safety checks must rely entirely on API runtime profile |
| **Brokers** | `FEAT-BRK-09` Broker Event Normalization | `broker.events.normalizer@1` | `utils.time@1` | `utils.logging@1` | Raw broker deal/order events cannot be normalized into canonical DTOs |
| **Brokers** | `FEAT-BRK-10` Adapter Conformance Kit | `broker.conformance@1` | `broker.capabilities@1` | `—` | Automated broker adapter conformance testing suite becomes unavailable |
| **Brokers** | `FEAT-BRK-18` Provider Spec Snapshots | `broker.spec.snapshots@1` | `broker.capabilities@1` | `—` | Deterministic parity snapshots for broker APIs become unavailable |
| **Data** | `FEAT-DATA-01` Market Data Ingestion | `data.market-data@1` | `broker.instruments@1` | `data.bar-cache@1` | Historical and real-time market data retrieval becomes unavailable |
| **Data** | `FEAT-DATA-02` Dataset Lifecycle & Catalog | `data.datasets@1` | `data.persistence@1` | `utils.logging@1` | Dataset registration, hashing, and versioned catalog become unavailable |
| **Data** | `FEAT-DATA-03` Storage & Partitioning | `data.storage@1` | `data.persistence@1` | `—` | Direct partition storage and Parquet caching become unavailable |
| **Data** | `FEAT-DATA-04` Cache & Invalidation | `data.bar-cache@1` | `data.storage@1` | `utils.logging@1` | In-memory market data caching degrades to direct storage reads |
| **Data** | `FEAT-DATA-05` Audit & Transformation | `data.audit-transforms@1` | `data.datasets@1` | `utils.logging@1` | Audit logging of market data transformations becomes disabled |
| **Data** | `FEAT-DATA-06` Synthetic Tick Generators | `data.synthetic-generator@1` | `—` | `utils.random_streams@1` | Synthetic GBM tick generation for testing becomes unavailable |
| **Data** | `FEAT-DATA-07` Multi-Timeframe Alignment | `data.alignment@1` | `data.market-data@1` | `—` | Multi-timeframe bar alignment and resampling become unavailable |
| **Data** | `FEAT-DATA-08` Quality & Integrity Checks | `data.quality@1` | `data.market-data@1` | `utils.logging@1` | Market data anomaly detection, gap analysis, and scoring become disabled |
| **Data** | `FEAT-DATA-09` Point-in-Time Research Docs | `data.research-docs@1` | `data.storage@1` | `—` | Point-in-time filing, macroeconomic, and sentiment records become unavailable |
| **Data** | `FEAT-DATA-10` Scheduled Ingestion Jobs | `data.scheduler@1` | `data.market-data@1` | `utils.logging@1` | Automated background market data backfill and synchronization stop |
| **Data** | `FEAT-DATA-11` Streaming Feed Engine | `data.tick_stream@1` | `broker.instruments@1` | `utils.logging@1` | Live WebSocket/TCP tick stream sequencing and fan-out become unavailable |
| **Data** | `FEAT-DATA-12` Source Composition Policy | `data.sources@1` | `data.market-data@1` | `—` | Cross-provider fallback and multi-source priority routing become disabled |
| **Data** | `FEAT-DATA-13` Runtime Stores & Migration | `data.persistence@1` | `utils.settings@1` | `utils.logging@1` | Shared SQLite database infrastructure and migration engine become unavailable |
| **Data** | `FEAT-DATA-14` Replay Packages | `data.replay-packages@1` | `data.storage@1` | `—` | Deterministic historical market replay packages become unavailable |
| **Data** | `FEAT-DATA-15` Market Calendar & Hours | `data.calendar@1` | `utils.time@1` | `—` | Exchange trading session, holiday calendar, and market hour checks fail closed |
| **Indicators** | `FEAT-INDI-01` Contracts & Discovery | `indicator.registry@1` | `—` | `utils.logging@1` | Indicator catalog registration and formula discovery become unavailable |
| **Indicators** | `FEAT-INDI-02` Trend Indicators | `indicator.trend@1` | `data.market-data@1` | `—` | EMA, SMA, WMA, MACD, and Supertrend calculations become unavailable |
| **Indicators** | `FEAT-INDI-03` Momentum Oscillators | `indicator.momentum@1` | `data.market-data@1` | `—` | RSI, Williams %R, and Stochastic oscillator calculations become unavailable |
| **Indicators** | `FEAT-INDI-04` Volatility Indicators | `indicator.volatility@1` | `data.market-data@1` | `—` | ATR, Bollinger Bands, and Keltner Channel calculations become unavailable |
| **Indicators** | `FEAT-INDI-05` Volume Indicators | `indicator.volume@1` | `data.market-data@1` | `—` | OBV, VWAP, and volume-weighted calculations become unavailable |
| **Indicators** | `FEAT-INDI-06` Order Flow Proxies | `indicator.order-flow@1` | `data.market-data@1` | `—` | CVD and aggressive trade imbalance calculations become unavailable |
| **Indicators** | `FEAT-INDI-07` Market Structure & Levels | `indicator.structure@1` | `data.market-data@1` | `—` | Pivot points, swing high/low, and market structure calculations become unavailable |
| **Indicators** | `FEAT-INDI-08` Liquidity & Spread Metrics | `indicator.liquidity@1` | `data.market-data@1` | `—` | Bid-ask spread metrics and liquidity estimates become unavailable |
| **Indicators** | `FEAT-INDI-09` Market Speed & Acceleration | `indicator.market-speed@1` | `data.market-data@1` | `—` | Tick velocity and market acceleration metrics become unavailable |
| **Indicators** | `FEAT-INDI-10` Candle Patterns | `indicator.patterns@1` | `data.market-data@1` | `—` | Japanese candlestick pattern recognition becomes unavailable |
| **Indicators** | `FEAT-INDI-11` Stateless Calculation Runner | `indicator.runner@1` | `indicator.registry@1` | `utils.logging@1` | Batch execution engine for multi-indicator series becomes unavailable |
| **Indicators** | `FEAT-INDI-12` Snapshot Publication | `indicator.snapshots@1` | `indicator.runner@1` | `utils.time@1` | Versioned indicator snapshot broadcasting and export become unavailable |
| **Strategy** | `FEAT-STR-01` Versioned Strategy Contracts | `strategy.contracts@1` | `—` | `utils.logging@1` | Strategy intent and signal contract definitions become unavailable |
| **Strategy** | `FEAT-STR-02` Safe Diagnostics & Audit | `strategy.diagnostics@1` | `strategy.contracts@1` | `utils.logging@1` | Strategy signal diagnostics and clock-drift auditing become disabled |
| **Strategy** | `FEAT-STR-03` Immutable Registry & Configs | `strategy.registry@1` | `data.persistence@1` | `utils.logging@1` | Strategy registration, parameter schemas, and versioning become unavailable |
| **Strategy** | `FEAT-STR-04` State Checkpoints | `strategy.checkpoints@1` | `data.persistence@1` | `—` | Strategy state serialization and recovery checkpoints become unavailable |
| **Strategy** | `FEAT-STR-05` Vectorized Signal Runner | `strategy.vectorized@1` | `strategy.registry@1, data.market-data@1` | `indicator.trend@1` | Fast vectorized batch signal evaluation becomes unavailable |
| **Strategy** | `FEAT-STR-06` Event-Driven Signal Runner | `strategy.event@1` | `strategy.registry@1, data.tick_stream@1` | `indicator.momentum@1` | Live bar/tick event strategy signal evaluation becomes unavailable |
| **Strategy** | `FEAT-STR-07` Proposal Intake Boundary | `strategy.proposal-intake@1` | `strategy.contracts@1` | `utils.logging@1` | External and agentic research proposal intake becomes blocked |
| **Strategy** | `FEAT-STR-08` Strategy Evaluators Library | `strategy.evaluators@1` | `strategy.registry@1` | `—` | Built-in strategies (MA trend, Harriet hedging, SQX breakout, etc.) become unavailable |
| **Strategy** | `FEAT-STR-09` Signal Normalization & Intents | `strategy.intents@1` | `strategy.contracts@1` | `—` | Signal-to-TradeIntent conversion becomes unavailable |
| **Strategy** | `FEAT-STR-10` Operational Strategy Profiles | `strategy.profiles@1` | `strategy.registry@1` | `—` | Strategy execution profiles and operational parameters become unavailable |
| **Strategy** | `FEAT-STR-11` Strategy Playbooks | `strategy.playbooks@1` | `strategy.profiles@1` | `—` | Conditional strategy playbook rules and triggers become unavailable |
| **Strategy** | `FEAT-STR-12` Setup Evaluation Engine | `strategy.setup-evaluation@1` | `strategy.playbooks@1` | `—` | Pre-trade setup scoring and validation become unavailable |
| **Strategy** | `FEAT-STR-13` Trade Plan Formulation | `strategy.trade-plan@1` | `strategy.setup-evaluation@1` | `—` | Trade plan generation and target entry/exit formulation become unavailable |
| **Strategy** | `FEAT-STR-14` Operating Envelopes | `strategy.operating-envelope@1` | `strategy.trade-plan@1` | `—` | Environmental operating envelopes (spread/volatility bounds) become disabled |
| **Strategy** | `FEAT-STR-15` Trade Management Plans | `strategy.management-plan@1` | `strategy.trade-plan@1` | `—` | Dynamic position management rules (trailing stop, scaling) become unavailable |
| **Strategy** | `FEAT-STR-16` Strategy Automation Policy | `strategy.automation@1` | `strategy.management-plan@1` | `—` | Automated trade execution policies and mode switches become disabled |
| **Strategy** | `FEAT-STR-17` Lifecycle & Deprecation | `strategy.lifecycle@1` | `strategy.registry@1` | `utils.logging@1` | Strategy retirement, deprecation, and archival governance become unavailable |
| **Strategy** | `FEAT-STR-18` Parameter Space Schemas | `strategy.parameters@1` | `strategy.registry@1` | `—` | Parameter type schemas and constraint boundaries become unavailable |
| **Strategy** | `FEAT-STR-19` Strategy Mutation Audit | `strategy.mutations@1` | `data.persistence@1` | `utils.logging@1` | Audit logging of strategy configuration changes becomes disabled |
| **Strategy** | `FEAT-STR-20` Strategy Replay Adapter | `strategy.replay@1` | `strategy.vectorized@1` | `data.replay-packages@1` | Strategy signal replay over historical datasets becomes unavailable |
| **Risk** | `FEAT-RISK-01` Versioned Risk Contracts | `risk.contracts@1` | `—` | `utils.logging@1` | Risk decision and verdict contract definitions become unavailable |
| **Risk** | `FEAT-RISK-02` Risk Profiles & Limits | `risk.profiles@1` | `data.persistence@1` | `utils.logging@1` | Risk threshold configurations and limit definitions become unavailable |
| **Risk** | `FEAT-RISK-03` Portfolio Risk Snapshot | `risk.portfolio-snapshot@1` | `risk.profiles@1` | `—` | Real-time portfolio exposure and leverage aggregation become unavailable |
| **Risk** | `FEAT-RISK-04` Position Sizing & Capping | `risk.sizing@1` | `risk.profiles@1` | `—` | Risk-adjusted position size calculation and volume capping become unavailable |
| **Risk** | `FEAT-RISK-05` Proposal Interception Gate | `risk.proposal-gate@1` | `risk.contracts@1, risk.sizing@1` | `utils.logging@1` | Master risk governance gate fails closed: ALL trade intents blocked |
| **Risk** | `FEAT-RISK-06` Exposure & Concentration | `risk.exposure@1` | `risk.portfolio-snapshot@1` | `—` | Instrument, currency, and sector concentration limit checks become disabled |
| **Risk** | `FEAT-RISK-07` Drawdown & Loss Governor | `risk.drawdown-guard@1` | `risk.portfolio-snapshot@1` | `—` | Daily/peak drawdown limits and trailing equity halts become disabled |
| **Risk** | `FEAT-RISK-08` Approval Token Authority | `risk.approval-tokens@1` | `risk.proposal-gate@1` | `—` | Cryptographic single-use trade approval token issuance becomes unavailable |
| **Risk** | `FEAT-RISK-09` Fail-Closed Kill Switch | `risk.kill-switch@1` | `risk.contracts@1` | `utils.logging@1` | Emergency system-wide trading halt and kill-switch hierarchy become unavailable |
| **Risk** | `FEAT-RISK-10` Cryptographic Audit Trail | `risk.audit-trail@1` | `data.persistence@1` | `—` | Tamper-evident SHA-256 hash-chained risk audit logs become disabled |
| **Risk** | `FEAT-RISK-11` Scenario Stress Testing | `risk.scenarios@1` | `risk.portfolio-snapshot@1` | `—` | Historical crash scenario and stress test simulations become unavailable |
| **Risk** | `FEAT-RISK-12` Preflight Warning Evaluator | `risk.preflight@1` | `risk.proposal-gate@1` | `—` | Advisory UI preflight risk warnings and margin estimates become unavailable |
| **Risk** | `FEAT-RISK-13` Action Policy Verdicts | `risk.action-policy@1` | `risk.proposal-gate@1` | `—` | Action-policy evaluation (close-only, reduce-only, full-stop) becomes unavailable |
| **Risk** | `FEAT-RISK-14` Pending Reservation Ledger | `risk.reservations@1` | `data.persistence@1` | `—` | Atomic in-flight order risk capital reservation becomes disabled |
| **Risk** | `FEAT-RISK-15` Regulatory & Broker Limits | `risk.regulatory-limits@1` | `risk.profiles@1` | `—` | Broker-specific max order size and leverage caps become unenforced |
| **Risk** | `FEAT-RISK-16` Market Context Evaluation | `risk.market-context@1` | `data.market-data@1` | `—` | Pre-trade market spread and volatility threshold checks become disabled |
| **Risk** | `FEAT-RISK-17` Governor Orchestration | `risk.governor@1` | `risk.proposal-gate@1, risk.kill-switch@1` | `utils.logging@1` | Unified portfolio risk governor daemon becomes unavailable |
| **Trading** | `FEAT-TRD-01` Canonical Contracts & DTOs | `trading.contracts@1` | `—` | `utils.logging@1` | OrderIntent, TradeRecord, and execution receipt schemas become unavailable |
| **Trading** | `FEAT-TRD-02` Active State & Projections | `trading.state@1` | `data.persistence@1` | `utils.logging@1` | Broker-authoritative open order and position state become unavailable |
| **Trading** | `FEAT-TRD-03` Readiness & Safety Plans | `trading.validation@1` | `trading.contracts@1` | `—` | Execution readiness checks and safety preflights become disabled |
| **Trading** | `FEAT-TRD-04` Order Intent Formulation | `trading.intent-formulation@1` | `trading.contracts@1, risk.approval-tokens@1` | `—` | Risk-approved decisions cannot be converted into executable broker orders |
| **Trading** | `FEAT-TRD-05` Route & Environment Dispatch | `trading.dispatch@1` | `trading.intent-formulation@1, broker.mt5.channel@1` | `utils.logging@1` | Order dispatch across sim, demo, and live broker routes becomes unavailable |
| **Trading** | `FEAT-TRD-06` Execution Persistence | `trading.persistence@1` | `data.persistence@1` | `—` | Closed trade records, fill receipts, and transaction history stop saving |
| **Trading** | `FEAT-TRD-07` Trade Ownership & Lineage | `trading.ownership@1` | `data.persistence@1` | `—` | Strategy-to-order provenance tracking and client order ID mapping become disabled |
| **Trading** | `FEAT-TRD-08` Execution Reconciliation | `trading.reconciliation@1` | `trading.state@1, broker.mt5.channel@1` | `utils.logging@1` | Automated broker position/order state reconciliation becomes unavailable |
| **Trading** | `FEAT-TRD-09` Protective Order Manager | `trading.protective-orders@1` | `trading.dispatch@1` | `—` | Automated stop-loss, take-profit, and trailing stop synchronization stop |
| **Trading** | `FEAT-TRD-10` Incident & Event Monitor | `trading.monitoring@1` | `data.persistence@1` | `utils.logging@1` | Trading execution incident detection and operational alerts become disabled |
| **Trading** | `FEAT-TRD-11` Trading Session Registry | `trading.sessions@1` | `data.persistence@1` | `—` | Trading session lifecycle tracking and operator run history become unavailable |
| **Trading** | `FEAT-TRD-12` Live Evaluation Actions | `trading.live-orchestration@1` | `trading.dispatch@1, risk.kill-switch@1` | `utils.logging@1` | Live/demo continuous evaluation loops and automated execution become unavailable |
| **Simulator** | `FEAT-SIM-01` Boundary & Input Validation | `simulator.validation@1` | `—` | `utils.logging@1` | Backtest configuration and parameter validation become unavailable |
| **Simulator** | `FEAT-SIM-02` Simulation State Storage | `simulator.state@1` | `data.persistence@1` | `—` | Simulation run results, checkpoints, and artifact storage become unavailable |
| **Simulator** | `FEAT-SIM-03` Canonical Tick Timeline | `simulator.timeline@1` | `data.market-data@1` | `—` | Point-in-time historical tick sequencing without lookahead becomes unavailable |
| **Simulator** | `FEAT-SIM-04` Historical Backtest Engine | `simulator.backtest@1` | `simulator.timeline@1, strategy.vectorized@1, risk.proposal-gate@1` | `utils.logging@1` | Historical strategy backtesting engine becomes unavailable |
| **Simulator** | `FEAT-SIM-05` Execution Realism Models | `simulator.realism@1` | `simulator.backtest@1` | `—` | Realistic slippage, spread widening, latency, and partial fills become disabled |
| **Simulator** | `FEAT-SIM-06` Simulated Account & Margin | `simulator.account@1` | `simulator.backtest@1` | `—` | Multi-currency margin, swap, and balance simulation become unavailable |
| **Simulator** | `FEAT-SIM-07` Multi-Asset Simulation | `simulator.multi-asset@1` | `simulator.account@1` | `—` | Cross-asset portfolio backtesting and simultaneous replay become unavailable |
| **Simulator** | `FEAT-SIM-08` Scenario Injection Engine | `simulator.scenarios@1` | `simulator.backtest@1` | `—` | Synthetic market shocks, flash crashes, and gap injections become unavailable |
| **Simulator** | `FEAT-SIM-09` Deterministic Replay Hub | `simulator.replay@1` | `simulator.backtest@1` | `—` | Exact deterministic replay verification and reproduction hashes become unavailable |
| **Simulator** | `FEAT-SIM-10` Secured Session Recovery | `simulator.recovery@1` | `simulator.state@1` | `—` | Simulation pause, step, seek, branching, and checkpoint recovery become unavailable |
| **Simulator** | `FEAT-SIM-11` Simulated Alert Lifecycle | `simulator.alerts@1` | `simulator.state@1` | `—` | Simulated event notifications and threshold alerts become disabled |
| **Simulator** | `FEAT-SIM-12` Continuous Scheduler Pump | `simulator.scheduler@1` | `simulator.timeline@1` | `utils.logging@1` | Event-driven asynchronous backtest scheduling pump becomes unavailable |
| **Simulator** | `FEAT-SIM-13` Simulation Checklist | `simulator.checklist@1` | `simulator.validation@1` | `—` | Pre-run sanity checklist and asset readiness checks become disabled |
| **Simulator** | `FEAT-SIM-14` Execution Calibration | `simulator.calibration@1` | `simulator.realism@1` | `—` | Calibration of simulator fill models against real broker executions becomes unavailable |
| **Simulator** | `FEAT-SIM-15` Offline Conformance Kit | `simulator.conformance@1` | `simulator.backtest@1` | `—` | Automated math kernel and metric conformance testing becomes unavailable |
| **Simulator** | `FEAT-SIM-16` Sim/Live Parity Engine | `simulator.parity@1` | `simulator.backtest@1, broker.sim.channel@1` | `—` | Sim-to-live execution parity comparison and divergence metrics become unavailable |
| **Simulator** | `FEAT-SIM-17` Batch Run Orchestration | `simulator.batching@1` | `simulator.backtest@1` | `utils.logging@1` | Parallel multi-scenario and multi-strategy batch backtesting become unavailable |
| **Simulator** | `FEAT-SIM-18` Catalog Completion Sink | `simulator.catalog@1` | `simulator.state@1` | `—` | Automatic publication of completed runs to the simulation catalog becomes disabled |
| **Simulator** | `FEAT-SIM-19` Workbench Live Authority | `simulator.workbench@1` | `simulator.backtest@1, simulator.recovery@1` | `utils.logging@1` | Simulation Workbench interactive control, stepping, and branching become unavailable |
| **Analytics** | `FEAT-ANLT-01` Contracts & Evidence Safety | `analytics.contracts@1` | `—` | `utils.logging@1` | Performance report, metric schema, and trade ledger contracts become unavailable |
| **Analytics** | `FEAT-ANLT-02` Upstream Result Adapters | `analytics.adapters@1` | `analytics.contracts@1` | `—` | Conversion of Trading and Simulation trade records into ledger evidence becomes unavailable |
| **Analytics** | `FEAT-ANLT-03` Pure Metric Kernels | `analytics.metrics@1` | `analytics.contracts@1` | `—` | Return series, Sharpe ratio, Sortino, Win Rate, and Profit Factor math become unavailable |
| **Analytics** | `FEAT-ANLT-04` Drawdown & Underwater Math | `analytics.drawdown@1` | `analytics.metrics@1` | `—` | Peak-to-trough drawdown series, recovery duration, and underwater charts become unavailable |
| **Analytics** | `FEAT-ANLT-05` Trade Journal Projections | `analytics.journal@1` | `analytics.adapters@1` | `—` | Trade-by-trade analytical breakdowns, MAE/MFE excursions, and durations become unavailable |
| **Analytics** | `FEAT-ANLT-06` Performance Report Builder | `analytics.reports@1` | `analytics.metrics@1, analytics.drawdown@1` | `utils.logging@1` | Comprehensive tear-sheet and analytical performance reports cannot be built |
| **Analytics** | `FEAT-ANLT-07` Dashboard Snapshot Payloads | `analytics.dashboards@1` | `analytics.reports@1` | `—` | Aggregated performance KPIs for UI overview dashboards become unavailable |
| **Analytics** | `FEAT-ANLT-08` Benchmark Comparison | `analytics.benchmarks@1` | `analytics.metrics@1, data.market-data@1` | `—` | Alpha, Beta, and benchmark relative return comparisons become unavailable |
| **Analytics** | `FEAT-ANLT-09` Risk Attribution & Factor Math | `analytics.attribution@1` | `analytics.metrics@1` | `—` | Factor-based return attribution and asset contribution breakdowns become unavailable |
| **Analytics** | `FEAT-ANLT-10` Caveat & Warning Catalog | `analytics.caveats@1` | `analytics.contracts@1` | `—` | Data-deficiency, low-sample-size, and regime caveat flags become disabled |
| **Analytics** | `FEAT-ANLT-11` Analytics Workbench Gateway | `analytics.workbench@1` | `analytics.reports@1, analytics.journal@1` | `utils.logging@1` | Analytics Workbench UI backend projection and interactive filtering become unavailable |
| **Optimization** | `FEAT-OPT-01` Parameter Space & Provenance | `optimization.parameters@1` | `strategy.parameters@1` | `utils.logging@1` | Optimization search grid definition and parameter hashing become unavailable |
| **Optimization** | `FEAT-OPT-02` Scoring & Ranking Kernels | `optimization.scoring@1` | `analytics.metrics@1` | `—` | Multi-objective candidate scoring, ranking, and tie-breaking become unavailable |
| **Optimization** | `FEAT-OPT-03` Bounded Candidate Search | `optimization.search@1` | `optimization.parameters@1, simulator.backtest@1` | `utils.logging@1` | Grid and random parameter sweep orchestration becomes unavailable |
| **Optimization** | `FEAT-OPT-04` Walk-Forward Validation | `optimization.walk-forward@1` | `optimization.search@1` | `utils.logging@1` | Out-of-sample walk-forward efficiency and window rolling become unavailable |
| **Optimization** | `FEAT-OPT-05` Monte Carlo Robustness | `optimization.monte-carlo@1` | `analytics.metrics@1` | `utils.random_streams@1` | Trade reshuffling, skip-trade, and equity curve Monte Carlo analysis become unavailable |
| **Optimization** | `FEAT-OPT-06` Overfit & Deflation Diagnostics | `optimization.overfit@1` | `optimization.scoring@1` | `—` | Probabilistic Sharpe ratio and overfit risk penalty calculations become unavailable |
| **Optimization** | `FEAT-OPT-07` Search Checkpoints & Storage | `optimization.persistence@1` | `data.persistence@1` | `—` | Optimization run checkpointing, resumption, and candidate result persistence become unavailable |
| **Optimization** | `FEAT-OPT-08` Parametric Stress Testing | `optimization.stress@1` | `optimization.search@1` | `—` | Parameter sensitivity neighborhood testing and plateau analysis become unavailable |
| **Optimization** | `FEAT-OPT-09` Optimization Workbench | `optimization.workbench@1` | `optimization.search@1, optimization.walk-forward@1` | `utils.logging@1` | Optimization Workbench UI orchestration and progress streaming become unavailable |
| **Research** | `FEAT-RES-01` Contracts & Sandboxed Config | `research.contracts@1` | `—` | `utils.logging@1` | Research study definitions and sandboxed experiment schemas become unavailable |
| **Research** | `FEAT-RES-02` Dataset Preprocessing | `research.data@1` | `data.market-data@1` | `—` | Leakage-free dataset normalization and feature alignment become unavailable |
| **Research** | `FEAT-RES-03` Feature Engineering Library | `research.features@1` | `research.data@1, indicator.registry@1` | `—` | Alpha factor extraction, lag features, and statistical predictors become unavailable |
| **Research** | `FEAT-RES-04` Stationarity & Unit Roots | `research.stationarity@1` | `research.data@1` | `—` | ADF, KPSS stationarity tests, and fractional differentiation become unavailable |
| **Research** | `FEAT-RES-05` Correlation & Redundancy | `research.correlation@1` | `research.features@1` | `—` | Cross-factor correlation matrices and hierarchical clustering become unavailable |
| **Research** | `FEAT-RES-06` Statistical Significance | `research.statistical-tests@1` | `research.features@1` | `—` | Hypothesis p-value testing, t-stats, and multiple-testing corrections become unavailable |
| **Research** | `FEAT-RES-07` Edge Discovery Studies | `research.edge-studies@1` | `research.features@1` | `analytics.metrics@1` | Mean-reversion, trend-persistence, and session edge studies become unavailable |
| **Research** | `FEAT-RES-08` Seasonality & Calendar Alpha | `research.seasonality@1` | `research.data@1, data.calendar@1` | `—` | Intraday, day-of-week, and monthly seasonality alpha modeling become unavailable |
| **Research** | `FEAT-RES-09` Regime Classification | `research.regimes@1` | `research.features@1` | `—` | Unsupervised GMM and HMM market regime classification become unavailable |
| **Research** | `FEAT-RES-10` Decomposition & PCA | `research.decomposition@1` | `research.features@1` | `—` | Principal Component Analysis and eigen-portfolio decomposition become unavailable |
| **Research** | `FEAT-RES-11` Expectancy Governance | `research.expectancy@1` | `research.statistical-tests@1` | `—` | Alpha factor statistical sign-off and expectancy gating become unavailable |
| **Research** | `FEAT-RES-12` Research Artifact Persistence | `research.persistence@1` | `data.persistence@1` | `—` | Research notebooks, study outputs, and feature cache persistence become unavailable |
| **Research** | `FEAT-RES-13` Drift & Degradation Monitor | `research.drift@1` | `research.expectancy@1, data.market-data@1` | `—` | Live alpha factor decay, concept drift, and performance degradation tracking become unavailable |
| **Research** | `FEAT-RES-14` Fundamental Data Adapters | `research.fundamentals@1` | `data.research-docs@1` | `—` | Financial statement, earnings, and valuation metric research features become unavailable |
| **Research** | `FEAT-RES-15` Sentiment & News Analysis | `research.sentiment@1` | `data.research-docs@1` | `—` | News sentiment scoring and social momentum research signals become unavailable |
| **Research** | `FEAT-RES-16` Research Workbench Gateway | `research.workbench@1` | `research.edge-studies@1, research.regimes@1` | `utils.logging@1` | Research Workbench UI backend gateway and interactive exploration become unavailable |
| **Portfolio** | `FEAT-PORT-01` Boundary Contracts & Types | `portfolio.contracts@1` | `—` | `utils.logging@1` | Portfolio definition, allocation plan, and rebalance DTOs become unavailable |
| **Portfolio** | `FEAT-PORT-02` Evidence & Eligibility | `portfolio.validation@1` | `portfolio.contracts@1, analytics.metrics@1` | `—` | Strategy track-record validation and portfolio eligibility checks become unavailable |
| **Portfolio** | `FEAT-PORT-03` Deterministic Construction | `portfolio.construction@1` | `portfolio.validation@1` | `—` | Equal-weight, fixed-weight, and inverse-volatility portfolio building become unavailable |
| **Portfolio** | `FEAT-PORT-04` Risk-Budget Allocation | `portfolio.risk-budget@1` | `portfolio.construction@1, risk.portfolio-snapshot@1` | `—` | Marginal risk contribution and volatility budget optimization become unavailable |
| **Portfolio** | `FEAT-PORT-05` Active Portfolio Activation | `portfolio.activation@1` | `portfolio.risk-budget@1, risk.approval-tokens@1` | `utils.logging@1` | Multi-strategy portfolio activation and live routing become blocked |
| **Portfolio** | `FEAT-PORT-06` Drift & Rebalance Planning | `portfolio.rebalancing@1` | `portfolio.activation@1, trading.state@1` | `—` | Weight drift detection and reduce-only rebalancing plan generation become unavailable |
| **Portfolio** | `FEAT-PORT-07` Double-Entry Ledger | `portfolio.ledger@1` | `data.persistence@1` | `—` | Balanced multi-strategy asset accounting and capital allocation ledger stop updating |
| **Portfolio** | `FEAT-PORT-08` Rollback & Version Control | `portfolio.versions@1` | `portfolio.ledger@1` | `—` | Immutable portfolio version history and atomic rollback become unavailable |
| **Portfolio** | `FEAT-PORT-09` Cross-Asset FX Valuation | `portfolio.fx-valuation@1` | `data.market-data@1` | `—` | Multi-currency base-asset conversion and unified portfolio NAV become unavailable |
| **Portfolio** | `FEAT-PORT-10` Portfolio Rebalance Execution | `portfolio.execution@1` | `portfolio.rebalancing@1, trading.dispatch@1` | `utils.logging@1` | Automated execution of portfolio rebalance order intents becomes disabled |
| **Portfolio** | `FEAT-PORT-11` Portfolio Simulation Bridge | `portfolio.simulation@1` | `portfolio.construction@1, simulator.multi-asset@1` | `—` | Multi-strategy portfolio historical backtest evaluation becomes unavailable |
| **Portfolio** | `FEAT-PORT-12` Portfolio Workbench Gateway | `portfolio.workbench@1` | `portfolio.activation@1, portfolio.rebalancing@1` | `utils.logging@1` | Portfolio Workbench UI backend gateway and allocation controls become unavailable |
| **API** | `FEAT-API-01` Boundary Contracts & Catalog | `api.catalog@1` | `—` | `utils.logging@1` | Canonical route contract registry and endpoint permission catalog become unavailable |
| **API** | `FEAT-API-02` Identity, Auth & Sessions | `api.identity@1` | `data.persistence@1` | `utils.logging@1` | User authentication, JWT/session management, and password hashing become unavailable |
| **API** | `FEAT-API-03` Request Security Middleware | `api.security@1` | `api.identity@1` | `—` | CSRF validation, secret redaction, and request context tracing become disabled |
| **API** | `FEAT-API-04` Rate Limiting Middleware | `api.rate-limits@1` | `—` | `utils.logging@1` | Endpoint rate limiting and DDoS traffic throttling become disabled |
| **API** | `FEAT-API-05` Deadline & Timeout Enforcer | `api.deadlines@1` | `—` | `utils.logging@1` | Per-endpoint execution deadline enforcement and hang prevention become disabled |
| **API** | `FEAT-API-06` Standard Response Envelope | `api.envelope@1` | `utils.responses@1` | `—` | Unified JSON response formatting with error translation becomes unavailable |
| **API** | `FEAT-API-07` Credential Vault & Encryption | `api.credentials@1` | `data.persistence@1` | `utils.security@1` | Encrypted broker credential storage, retrieval, and key rotation become unavailable |
| **API** | `FEAT-API-08` Health & Readiness Probes | `api.health@1` | `data.persistence@1` | `broker.capabilities@1` | Kubernetes liveness/readiness probes and system status endpoints become unavailable |
| **API** | `FEAT-API-09` Observability & Telemetry | `api.telemetry@1` | `utils.logging@1` | `—` | Prometheus metrics exposition, clock-drift diagnostics, and log streaming become disabled |
| **API** | `FEAT-API-10` Settings & Runtime Profile | `api.settings@1` | `utils.settings@1` | `utils.logging@1` | Dynamic API settings management and account profile switching become unavailable |
| **API** | `FEAT-API-11` Market Data HTTP Routes | `api.data-routes@1` | `data.market-data@1` | `utils.logging@1` | HTTP endpoints for historical bars, ticks, datasets, and calendars become unavailable |
| **API** | `FEAT-API-12` Market Data SSE Streams | `api.data-streams@1` | `data.tick_stream@1` | `utils.logging@1` | Real-time SSE market tick and depth stream broadcast endpoints become unavailable |
| **API** | `FEAT-API-13` Indicator Catalog Routes | `api.indicator-routes@1` | `indicator.registry@1, indicator.runner@1` | `—` | Endpoints for indicator formulas, calculations, and chart series become unavailable |
| **API** | `FEAT-API-14` Strategy Management Routes | `api.strategy-routes@1` | `strategy.registry@1, strategy.vectorized@1` | `utils.logging@1` | Endpoints for strategy definitions, signals, configs, and mutations become unavailable |
| **API** | `FEAT-API-15` Risk Management Routes | `api.risk-routes@1` | `risk.proposal-gate@1, risk.kill-switch@1` | `utils.logging@1` | Endpoints for risk limits, exposure inspection, and kill-switch control become unavailable |
| **API** | `FEAT-API-16` Trading & Orders Routes | `api.trading-routes@1` | `trading.dispatch@1, trading.state@1` | `utils.logging@1` | Endpoints for manual order placement, cancellation, and position views become unavailable |
| **API** | `FEAT-API-17` Trading Activity SSE Streams | `api.trading-streams@1` | `trading.state@1` | `utils.logging@1` | Real-time SSE execution receipts, fills, and position update streams become unavailable |
| **API** | `FEAT-API-18` Simulation Run Routes | `api.simulator-routes@1` | `simulator.backtest@1, simulator.state@1` | `utils.logging@1` | Endpoints for submitting backtests and retrieving simulation results become unavailable |
| **API** | `FEAT-API-19` Simulation Live SSE Bridge | `api.simulator-streams@1` | `simulator.workbench@1` | `utils.logging@1` | Real-time interactive backtest stepping, progress, and seek streams become unavailable |
| **API** | `FEAT-API-20` Analytics Report Routes | `api.analytics-routes@1` | `analytics.reports@1, analytics.journal@1` | `utils.logging@1` | Endpoints for performance tear-sheets, trade journals, and metrics become unavailable |
| **API** | `FEAT-API-21` Optimization Routes | `api.optimization-routes@1` | `optimization.search@1, optimization.walk-forward@1` | `utils.logging@1` | Endpoints for parameter sweep execution and robustness diagnostics become unavailable |
| **API** | `FEAT-API-22` Research Study Routes | `api.research-routes@1` | `research.edge-studies@1, research.regimes@1` | `utils.logging@1` | Endpoints for alpha research studies, feature exploration, and regimes become unavailable |
| **API** | `FEAT-API-23` Portfolio Allocation Routes | `api.portfolio-routes@1` | `portfolio.activation@1, portfolio.rebalancing@1` | `utils.logging@1` | Endpoints for multi-strategy portfolio creation and rebalance orders become unavailable |
| **API** | `FEAT-API-24` Agentic Operations Routes | `api.agentic-routes@1` | `agentic.operations@1` | `utils.logging@1` | Endpoints for multi-agent council objectives, runs, and artifacts become unavailable |
| **API** | `FEAT-API-25` Markets & Watchlists Routes | `api.markets-routes@1` | `data.market-data@1` | `—` | Endpoints for market symbol directory and custom watchlists become unavailable |
| **API** | `FEAT-API-26` Operator Audit Routes | `api.operator-routes@1` | `data.persistence@1` | `utils.logging@1` | Endpoints for operator audit trails and system event logs become unavailable |
| **API** | `FEAT-API-27` Simulation Catalog Routes | `api.sim-catalog-routes@1` | `simulator.catalog@1` | `—` | Endpoints for durable simulation catalogue exploration and comparisons become unavailable |
| **API** | `FEAT-API-28` Live Session Gateway | `api.live-session-routes@1` | `simulator.recovery@1` | `—` | Endpoints for live session branching, arming, and finalization become unavailable |

---

## 4. Domain Deep-Dives

### 4.1 Brokers (`app/services/brokers`)
- **Removability Tier:** `B` (Swappable Provider)
- **Feature Count:** 13 registered features
- **Core Mandate:** Direct passthrough connections to external broker & market-data platforms
- **Detailed Registry:** See full specification in [`app/services/brokers/README.md`](brokers/README.md).

### 4.2 Data (`app/services/data`)
- **Removability Tier:** `B` (Swappable Provider)
- **Feature Count:** 15 registered features
- **Core Mandate:** Acquisition, normalization, historical storage, and streaming feeds
- **Detailed Registry:** See full specification in [`app/services/data/README.md`](data/README.md).

### 4.3 Indicators (`app/services/indicators`)
- **Removability Tier:** `A` (Pure Calculation)
- **Feature Count:** 12 registered features
- **Core Mandate:** Deterministic, pure-function technical and statistical indicator calculations
- **Detailed Registry:** See full specification in [`app/services/indicators/README.md`](indicators/README.md).

### 4.4 Strategy (`app/services/strategy`)
- **Removability Tier:** `B` (Swappable Provider)
- **Feature Count:** 20 registered features
- **Core Mandate:** Signal generation, trade intent formulation, and playbook evaluation
- **Detailed Registry:** See full specification in [`app/services/strategy/README.md`](strategy/README.md).

### 4.5 Risk (`app/services/risk`)
- **Removability Tier:** `C` (Protected Core Safety Gate)
- **Feature Count:** 17 registered features
- **Core Mandate:** Master gate governance: exposure validation, drawdown guard, and kill switches
- **Detailed Registry:** See full specification in [`app/services/risk/README.md`](risk/README.md).

### 4.6 Trading (`app/services/trading`)
- **Removability Tier:** `B` (Swappable Provider)
- **Feature Count:** 12 registered features
- **Core Mandate:** Execution of approved trade intents across sim, demo, and live routes
- **Detailed Registry:** See full specification in [`app/services/trading/README.md`](trading/README.md).

### 4.7 Simulator (`app/services/simulator`)
- **Removability Tier:** `B` (Swappable Provider)
- **Feature Count:** 19 registered features
- **Core Mandate:** Deterministic historical backtesting and execution realism engine
- **Detailed Registry:** See full specification in [`app/services/simulator/README.md`](simulator/README.md).

### 4.8 Analytics (`app/services/analytics`)
- **Removability Tier:** `B` (Swappable Provider)
- **Feature Count:** 11 registered features
- **Core Mandate:** Read-only performance measurement, returns, metrics, and tear-sheets
- **Detailed Registry:** See full specification in [`app/services/analytics/README.md`](analytics/README.md).

### 4.9 Optimization (`app/services/optimization`)
- **Removability Tier:** `B` (Swappable Provider)
- **Feature Count:** 9 registered features
- **Core Mandate:** Parameter space search, objective scoring, and walk-forward validation
- **Detailed Registry:** See full specification in [`app/services/optimization/README.md`](optimization/README.md).

### 4.10 Research (`app/services/research`)
- **Removability Tier:** `B` (Swappable Provider)
- **Feature Count:** 16 registered features
- **Core Mandate:** Sandboxed alpha discovery, hypothesis testing, and regime modeling
- **Detailed Registry:** See full specification in [`app/services/research/README.md`](research/README.md).

### 4.11 Portfolio (`app/services/portfolio`)
- **Removability Tier:** `B` (Swappable Provider)
- **Feature Count:** 12 registered features
- **Core Mandate:** Multi-strategy portfolio construction, risk-budgeting, and rebalancing
- **Detailed Registry:** See full specification in [`app/services/portfolio/README.md`](portfolio/README.md).

### 4.12 API (`app/services/api`)
- **Removability Tier:** `B` (Swappable Provider)
- **Feature Count:** 28 registered features
- **Core Mandate:** FastAPI composition gateway exposing authenticated HTTP and SSE boundaries
- **Detailed Registry:** See full specification in [`app/services/api/README.md`](api/README.md).

---

## 5. Architectural Invariants

1. **Single Writer Principle**: Only the owning domain may persist, mutate, or authoritatively report its domain state.
2. **Zero Direct Sibling Imports**: Service features must never bypass `app/contracts/` to import internal sibling modules.
3. **Risk Gate Master Invariant**: No trade intent may be executed across any route without positive cryptographic approval from `FEAT-RISK-05` and `FEAT-RISK-08`.
4. **Brokers Passthrough Principle**: Brokers owns no business logic, signal rules, or risk decisions. It is a strict transport and adapter layer.
5. **Deterministic Simulation Parity**: Simulation backtests must yield bit-identical execution receipts across repeated runs given identical market data and seeds.

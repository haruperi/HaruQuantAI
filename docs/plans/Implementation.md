<!-- markdownlint-disable MD024 -->

<!-- cspell:words haruquantai dataframe backtests Runup -->

# HaruQuantAI DDD Agile Implementation Plan

## 1. Purpose

This document replaces the previous broad phase plan with a **Domain-Driven Design (DDD), agile, iterative rebuild plan** for **HaruQuantAI**.

The goal is to rebuild HaruQuant from scratch into HaruQuantAI without losing current functionality, but without creating a confusing waterfall structure where every future concept is created at the beginning.

Instead, HaruQuantAI will be rebuilt **domain by domain**. Each domain will be treated as a small bounded context. When we work on a domain, we build only what that domain needs at that time:

- Its models.
- Its schemas.
- Its validators.
- Its services.
- Its tool functions.
- Its tests.
- Its usage examples.
- Its documentation.
- Its API endpoints, only if needed.
- Its UI pages/components, only if needed.
- Its agent permissions/tools, only when the agentic layer reaches that domain.

This means we do not create `risk.py`, `agent.py`, `trade.py`, `backtest.py`, or other future schemas upfront unless the current domain needs them.

---

## 2. Core Philosophy

### 2.1 We are not building waterfall

The old plan looked like this:

```text
Foundation -> all contracts -> all persistence -> all domains -> agents -> API -> UI
```

That approach is clean architecturally, but mentally it can become confusing because it asks us to create many future-facing files before the current domain needs them.

The new plan uses this model:

```text
Domain 1 small waterfall -> complete
Domain 2 small waterfall -> complete
Domain 3 small waterfall -> complete
Domain 4 small waterfall -> complete
...
```

Each domain is built vertically and incrementally.

### 2.2 Build only what is needed now

When building the **data** domain, we only create data-related contracts and schemas.

When building the **strategies** domain, we only create strategy-related contracts and schemas.

When building the **backtesting** domain, we only create backtesting-related contracts and schemas.

When building the **risk** domain, we only create risk-related contracts and schemas.

This keeps the project mentally clear.

### 2.3 Each `tools/` folder is a DDD bounded context

Each folder inside `tools/` is a tool domain:

```text
tools/data/
tools/indicators/
tools/strategies/
tools/backtesting/
tools/analytics/
tools/research/
tools/optimization/
tools/risk/
tools/execution/
tools/portfolio/
tools/notification/
tools/conversation/
tools/agentic/
tools/utils/
```

A domain owns its own language, models, validators, services, and tool functions.

For example:

```text
tools/data/
  models.py
  schemas.py
  validators.py
  quality.py
  csv.py
  mt5.py
  parquet.py
```

Those files belong to the data domain. Other domains should not redefine data concepts unless there is a strong reason.

### 2.4 Shared code must be earned, not assumed

We should not create a huge global `core/domain/` folder at the beginning.

A concept should become shared only when:

1. Two or more domains genuinely need it.
2. Duplication is becoming harmful.
3. The shared abstraction is stable.
4. Moving it into `tools/utils/` or `tools/common/` makes the system clearer, not more abstract.

Until then, keep contracts inside the owning domain.

---

## 3. Preferred Top-Level Architecture

The project should use the simpler structure:

```text
haruquantai/
  pyproject.toml
  README.md
  .env.example
  .gitignore
  .pre-commit-config.yaml

  api/
  docs/
  scripts/
  data/
  tools/
  ui/
  tests/
```

### 3.1 Folder responsibilities

| Folder | Responsibility |
| --- | --- |
| `api/` | FastAPI app, routes, middleware, dependencies, websocket, API schemas that are route-specific. |
| `docs/` | Architecture docs, standards, domain docs, workflows, governance, runbooks. |
| `scripts/` | CLI utilities, migration scripts, examples that run outside tests. |
| `data/` | Runtime data, local databases, fixtures, logs, research cache, strategy storage if file-based. |
| `tools/` | Main business logic organized by DDD tool domains. |
| `ui/` | Next.js frontend. |
| `tests/` | Unit, integration, usage, workflow, e2e, and red-team tests. |

---

## 4. Tool Domain Standard

Every `tools/<domain>/` folder should follow the same mental pattern, but only add files when needed.

### 4.1 Default domain folder anatomy

```text
tools/<domain>/
  __init__.py
  README.md

  models.py          # Domain objects, only if needed.
  schemas.py         # Request/response contracts, only if needed.
  validators.py      # Validation rules, only if needed.
  errors.py          # Domain-specific errors, only if needed.
  services.py        # Orchestration/service layer, only if needed.
  standard_tools.py  # Agent/tool-facing wrappers, only if needed.

  <feature_file>.py
  <feature_file>.py
```

### 4.2 Tests for each domain

```text
tests/unit/tools/<domain>/
  test_<feature>.py
  test_validators.py
  test_services.py

tests/integration/tools/<domain>/
  test_<domain>_workflow.py

tests/usage/tools/<domain>/
  <domain>_example.py
```

### 4.3 Docs for each domain

```text
docs/domains/<domain>/
  README.md
  implementation_notes.md
  usage_examples.md
  acceptance_criteria.md
```

### 4.4 API for each domain

API files are added only when the domain has working logic worth exposing.

```text
api/routes/<domain>.py
api/schemas/<domain>.py  # only if route schemas should be separated
```

### 4.5 UI for each domain

UI files are added only when the API is stable enough for user workflows.

```text
ui/src/app/(dashboard)/<domain>/page.tsx
ui/src/components/<domain>/
ui/src/lib/api/<domain>.ts
ui/src/types/<domain>.ts
```

---

## 5. DDD Language Rules

### 5.1 Bounded Context

A bounded context is a domain area with its own language and responsibilities.

Examples:

| Bounded Context | Main Language                                                          |
| --------------- | ---------------------------------------------------------------------- |
| Data            | bars, ticks, symbols, timeframes, spread, source, quality report       |
| Indicators      | series, period, warmup, alignment, lookback                            |
| Strategies      | signals, entries, exits, state, version, registry                      |
| Backtesting     | orders, fills, positions, equity curve, simulation config              |
| Analytics       | metrics, returns, drawdowns, ratios, distributions                     |
| Risk            | exposure, margin, VaR, CVaR, limits, risk decision, governor           |
| Execution       | intent, approval, order router, broker bridge, receipt, reconciliation |
| Agentic         | agent, tool permission, evidence, workflow, approval gate              |

### 5.2 Aggregate

Each domain should identify its main aggregate.

Examples:

| Domain | Aggregate |
| --- | --- |
| Data | `MarketDataset` |
| Strategies | `StrategyDefinition` |
| Backtesting | `BacktestRun` |
| Analytics | `AnalyticsReport` |
| Risk | `RiskDecision` or `PortfolioRiskSnapshot` |
| Execution | `ExecutionIntent` |
| Agentic | `AgentWorkflowRun` |

### 5.3 Domain service

A domain service performs meaningful business logic that does not naturally belong to one model.

Examples:

- `DataQualityService`
- `StrategyValidationService`
- `BacktestRunnerService`
- `AnalyticsReportService`
- `RiskGovernorService`
- `ExecutionReadinessService`
- `AgentWorkflowService`

### 5.4 Tool function

A tool function is a stable public function that can be used by:

- API routes.
- Scripts.
- Agents.
- Tests.
- UI workflows through API.

Tool functions must be deterministic where possible and must clearly declare:

- Inputs.
- Outputs.
- Risk level.
- Side effects.
- Approval requirement.
- Errors.
- Tests.
- Usage examples.

---

## 6. Dependency Rules

### 6.1 Allowed dependency direction

```text
ui -> api -> tools -> data/runtime files
```

Inside `tools/`, dependencies should generally move from lower-level domains to higher-level domains:

```text
tools/utils
tools/data
tools/indicators
tools/research
tools/strategies
tools/backtesting
tools/analytics
tools/optimization
tools/risk
tools/execution
tools/portfolio
tools/conversation
tools/agentic
```

### 6.2 Important rule

A lower domain must not import from a higher domain.

Examples:

- `tools/data` must not import from `tools/backtesting`.
- `tools/indicators` must not import from `tools/strategies`.
- `tools/backtesting` should not import from `tools/risk` in the early version.
- `tools/risk` may read backtest/analytics outputs later, but only through stable contracts.
- `tools/execution` must depend on `tools/risk`, not the other way around.
- `tools/agentic` may orchestrate other tools, but other tools must not depend on `tools/agentic`.

### 6.3 Cross-domain communication

Domains should communicate using stable outputs, not internal classes.

Example:

```text
tools/backtesting produces BacktestResult
tools/analytics consumes BacktestResult-compatible trade/equity data
tools/risk consumes PortfolioState or TradeProposal
tools/execution consumes ApprovedExecutionIntent
```

But these contracts should be introduced only when the consuming domain is built.

---

## 7. Rebuild Method: One Domain at a Time

Every domain follows the same small waterfall:

```text
1. Domain purpose
2. Existing functionality to preserve
3. Domain language
4. Minimal files needed now
5. Domain models/schemas needed now
6. Validators
7. Core implementation
8. Unit tests
9. Usage examples
10. Integration tests if needed
11. API endpoints if needed
12. UI if needed
13. Agent tools/permissions if needed
14. Documentation
15. Exit acceptance checklist
```

This gives structure without forcing future domains to exist early.

---

## 8. Agile Domain Roadmap

## Sprint 0 — Rebuild Ground Rules and Repository Skeleton

### Goal

Create the clean HaruQuantAI repository with only the minimum shared standards needed to begin domain-by-domain development.

### Why this comes first

We need enough structure to prevent chaos, but we should not create all future contracts upfront.

### Files to create

```text
haruquantai/
  pyproject.toml
  README.md
  .env.example
  .gitignore
  .pre-commit-config.yaml

  api/
    __init__.py

  docs/
    README.md
    standards/
      code_standard.md
      tool_function_standard.md
      testing_standard.md
      logging_standard.md
    rebuild/
      HaruQuantAI_Rebuild_Charter.md
      Functionality_Preservation_Matrix.md
      Legacy_To_New_Module_Map.md

  scripts/
    __init__.py

  data/
    .gitkeep
    fixtures/
    logs/
    cache/

  tools/
    __init__.py
    utils/
      __init__.py
      logger.py
      errors.py
      result.py
      ids.py

  tests/
    __init__.py
    conftest.py
    unit/
      tools/
        utils/
          test_result.py
          test_ids.py
    usage/
      tools/
        utils/
          result_example.py

  ui/
    README.md
```

### What not to create yet

Do not create:

```text
tools/risk/
tools/execution/
tools/agentic/
tools/backtesting/
tools/analytics/
```

unless the sprint is actually working on those domains.

### Deliverables

- Basic repo.
- Basic utility functions.
- Basic logging.
- Basic result wrapper.
- Testing setup.
- Documentation standards.
- Functionality preservation matrix.

### Exit checklist

- [X] Repo structure exists.
- [X] `pytest` works.
- [X] Linting works.
- [X] Basic logging works.
- [X] Basic result wrapper works.
- [X] Rebuild charter exists.
- [X] Legacy-to-new map exists.
- [X] No future domain files have been created prematurely.

---

## Sprint 1 — Data Domain: Market Data Getting, Loading, and Validation

### Domain

```text
tools/data/
```

### Goal

Build the first complete DDD domain: data getting, loading, normalization, validation, and data quality reporting.

### Why this domain comes first

Everything else depends on market data. Strategies, indicators, backtesting, analytics, risk, and agents are useless without reliable data.

### Existing functionality to preserve

- CSV loading.
- Parquet loading.
- MT5 data loading.
- cTrader data loading.
- Dukascopy data loading.
- Synthetic data generation.
- Labeling.
- Scheduler.
- OHLCV validation.
- Spread-aware OHLCVS validation.
- Data quality checks.

### Domain language

- Symbol.
- Timeframe.
- Bar.
- Tick.
- OHLCV.
- OHLCVS.
- Spread.
- Source.
- Loader.
- Normalizer.
- Quality report.
- Missing bars.
- Duplicate timestamps.
- Broker time.

### Files to create

```text
tools/data/
  __init__.py
  README.md
  models.py
  schemas.py
  errors.py
  validators.py
  quality.py
  normalization.py
  csv.py
  parquet.py
  mt5.py
  ctrader.py
  dukascopy.py
  generators.py
  labeling.py
  scheduler.py
  standard_tools.py

tests/unit/tools/data/
  test_models.py
  test_validators.py
  test_quality.py
  test_normalization.py
  test_csv.py
  test_parquet.py
  test_generators.py

tests/integration/tools/data/
  test_data_loading_workflow.py

tests/usage/tools/data/
  load_csv_example.py
  validate_ohlcvs_example.py
  mt5_loader_example.py

docs/domains/data/
  README.md
  acceptance_criteria.md
  usage_examples.md
```

### Models/schemas needed now

Only data-related models:

- `MarketDataSource`
- `SymbolSpec`
- `TimeframeSpec`
- `OHLCVSchema`
- `OHLCVSSchema`
- `DataQualityIssue`
- `DataQualityReport`
- `LoadDataRequest`
- `LoadDataResult`

### Core implementation

- Load data from CSV.
- Load/save Parquet.
- Normalize columns.
- Normalize timestamps.
- Validate OHLCV.
- Validate OHLCVS.
- Generate data quality report.
- Provide synthetic fixture generation.
- Add placeholders only for MT5/cTrader/Dukascopy if connection is not implemented immediately, but document the expected interface.

### Unit tests

- Valid OHLCV passes.
- Valid OHLCVS passes.
- Missing required columns fail.
- Duplicate timestamps detected.
- Non-monotonic timestamps detected.
- Invalid OHLC structure detected.
- Negative volume detected.
- Negative spread detected.
- CSV loader returns canonical format.
- Parquet round trip preserves data.
- Synthetic generator creates valid data.

### Usage examples

- Load EURUSD H1 CSV.
- Validate OHLCVS data.
- Save normalized data to Parquet.
- Generate synthetic data for tests.

### API

Only add API if the data domain is stable:

```text
api/routes/data.py
api/schemas/data.py
```

Endpoints:

- `POST /data/validate`
- `POST /data/load/csv`
- `GET /data/quality/{dataset_id}`

### UI

Optional for this sprint. Add only if API is ready:

```text
ui/src/app/(dashboard)/data/page.tsx
ui/src/components/data/
ui/src/lib/api/data.ts
```

### Exit checklist

- [ ] Data can be loaded from at least CSV.
- [ ] Data can be validated.
- [ ] Spread-aware validation works.
- [ ] Data quality report is produced.
- [ ] Data domain has unit tests.
- [ ] Data domain has usage examples.
- [ ] No strategy/backtest/risk files were created unnecessarily.

---

## Sprint 2 — Indicators Domain

### Domain

```text
tools/indicators/
```

### Goal

Build indicators as deterministic functions that consume validated data.

### Existing functionality to preserve

- RSI.
- ATR/ADR-related volatility.
- Bollinger Bands.
- EMA.
- SMA.
- WMA.
- Hurst.
- Accumulation/Distribution.
- Currency strength.
- SMC/custom indicators.
- Indicator validation/template.

### Domain language

- Indicator.
- Series.
- Period.
- Lookback.
- Warmup.
- Alignment.
- Input column.
- Output column.
- No-lookahead.

### Files to create

```text
tools/indicators/
  __init__.py
  README.md
  models.py
  validators.py
  common.py
  validation.py
  trend/
    __init__.py
    sma.py
    ema.py
    wma.py
  momentum/
    __init__.py
    rsi.py
  volatility/
    __init__.py
    atr.py
    bbands.py
  volume/
    __init__.py
    accumulation_distribution.py
  statistical/
    __init__.py
    hurst.py
  custom/
    __init__.py
    currency_strength.py
    smc.py
  standard_tools.py

tests/unit/tools/indicators/
  test_sma.py
  test_ema.py
  test_wma.py
  test_rsi.py
  test_atr.py
  test_bbands.py
  test_hurst.py
  test_currency_strength.py

tests/usage/tools/indicators/
  rsi_example.py
  atr_example.py
  currency_strength_example.py

docs/domains/indicators/
  README.md
  acceptance_criteria.md
```

### Models/schemas needed now

Only indicator-related models:

- `IndicatorInput`
- `IndicatorResult`
- `IndicatorMetadata`
- `WarmupPolicy`

### Core implementation

- Implement vectorized indicator functions.
- Ensure index alignment.
- Ensure warmup handling.
- Ensure invalid period handling.
- Ensure input dataframe is not mutated unless explicitly requested.

### Unit tests

- Known-value tests.
- Invalid period tests.
- Warmup tests.
- NaN handling tests.
- Input immutability tests.
- Index alignment tests.

### API/UI

Do not add API/UI yet unless needed by the Data page or Strategy Lab.

### Exit checklist

- [ ] Core indicators work.
- [ ] Indicator outputs are deterministic.
- [ ] Indicators consume data domain outputs.
- [ ] Tests and examples exist.
- [ ] No strategy/backtest concepts are introduced yet.

---

## Sprint 3 — Strategy Domain

### Domain

```text
tools/strategies/
```

### Goal

Create a unified strategy standard that supports both simple and complex strategies.

### Existing functionality to preserve

- Base strategy.
- Template strategy.
- Registry.
- Storage.
- Stateful common logic.
- Trend following.
- Mean reversion.
- RSI.
- RSI martingale.
- Pyramiding.
- Trade decomposition.
- RSI averaging pyramid.
- RSI decomposing reentry.
- Market structure hedge grid.
- MTF hedge trail.
- User strategy versions.

### Domain language

- Strategy.
- Strategy definition.
- Strategy metadata.
- Parameters.
- Features.
- Entry signal.
- Exit signal.
- Stateful strategy.
- Strategy state.
- Strategy version.
- Strategy registry.
- Strategy storage.

### Files to create

```text
tools/strategies/
  __init__.py
  README.md
  models.py
  schemas.py
  errors.py
  validators.py
  base.py
  signals.py
  stateful_common.py
  registry.py
  storage.py
  lifecycle.py
  template_strategy.py
  examples/
    trend_following.py
    mean_reversion.py
    rsi_strategy.py
    rsi_martingale.py
    pyramiding.py
    trade_decomposition.py
  standard_tools.py

tests/unit/tools/strategies/
  test_base.py
  test_signals.py
  test_registry.py
  test_storage.py
  test_template_strategy.py
  test_rsi_martingale.py
  test_pyramiding.py

tests/integration/tools/strategies/
  test_strategy_registration_workflow.py

tests/usage/tools/strategies/
  create_strategy_example.py
  register_strategy_example.py
  run_signal_generation_example.py

docs/domains/strategies/
  README.md
  strategy_template_standard.md
  acceptance_criteria.md
```

### Models/schemas needed now

Only strategy-related models:

- `StrategyMetadata`
- `StrategyParameter`
- `StrategyConfig`
- `StrategySignal`
- `StrategyState`
- `StrategyDefinition`
- `StrategyVersion`
- `StrategyRegistryEntry`

Do not create backtest result models yet.

### Core implementation

- Define `BaseStrategy`.
- Define required lifecycle:
  - `on_init()`
  - `get_features()`
  - `generate_signals()`
  - `on_bar()`
  - `on_tick()` only if needed.
  - `on_event()` only if needed for complex strategies.
- Add strategy registry.
- Add strategy validation.
- Add versioned storage.
- Add example strategies.
- Add migration mapping from old strategy files.

### API

Add only after registry and storage work:

```text
api/routes/strategies.py
api/schemas/strategies.py
```

Endpoints:

- `GET /strategies`
- `GET /strategies/{strategy_id}`
- `POST /strategies/register`
- `GET /strategies/{strategy_id}/versions`

### UI

Add only after API is stable:

```text
ui/src/app/(dashboard)/strategies/page.tsx
ui/src/app/(dashboard)/strategies/[id]/page.tsx
ui/src/components/strategies/
```

### Exit checklist

- [ ] Simple strategies work.
- [ ] Complex/stateful strategies work.
- [ ] Strategy registry works.
- [ ] Strategy versioning works.
- [ ] Strategy validation works.
- [ ] Existing strategy functionality is mapped.
- [ ] No backtesting engine is built yet except minimal signal examples.

---

## Sprint 4 — Backtesting Domain

### Domain

```text
tools/backtesting/
```

### Goal

Build the deterministic backtesting engine after data, indicators, and strategies exist.

### Existing functionality to preserve

- Simulation config.
- Data preparation.
- Event-driven engine.
- Vectorized engine.
- Runner.
- Results.
- Position sizing.
- Strategy registry integration.
- Order simulation.
- Positions.
- Equity curve.
- Manual/visual/batch simulation concepts.
- Replay.

### Domain language

- Backtest run.
- Backtest config.
- Broker simulator.
- Order.
- Fill.
- Position.
- Deal.
- Equity curve.
- Balance.
- Margin.
- Commission.
- Slippage.
- Spread.
- Execution mode.
- Hedging/netting.
- Replay event.

### Files to create

```text
tools/backtesting/
  __init__.py
  README.md
  models.py
  schemas.py
  errors.py
  validators.py
  config.py
  data_preparation.py
  broker.py
  orders.py
  positions.py
  fills.py
  costs.py
  margin.py
  engine.py
  event_driven.py
  vectorized.py
  results.py
  runner.py
  replay.py
  standard_tools.py

tests/unit/tools/backtesting/
  test_config.py
  test_data_preparation.py
  test_broker.py
  test_orders.py
  test_positions.py
  test_event_driven.py
  test_vectorized.py
  test_results.py
  test_replay.py

tests/integration/tools/backtesting/
  test_simple_strategy_backtest.py
  test_stateful_strategy_backtest.py

tests/usage/tools/backtesting/
  run_backtest_example.py
  run_event_driven_example.py
  run_vectorized_example.py

docs/domains/backtesting/
  README.md
  acceptance_criteria.md
  backtest_engine_design.md
```

### Models/schemas needed now

Only backtesting-related models:

- `BacktestConfig`
- `BacktestRun`
- `BacktestOrder`
- `BacktestFill`
- `BacktestPosition`
- `BacktestDeal`
- `EquityPoint`
- `BacktestResult`
- `ReplayEvent`

### Core implementation

- Use data domain output.
- Use strategy domain strategies.
- Simulate orders/fills.
- Support spread.
- Support slippage.
- Support commission.
- Support margin where needed.
- Support netting/hedging modes.
- Produce trade list, orders, deals, positions, and equity curve.
- Produce replay timeline.

### API

```text
api/routes/backtesting.py
api/schemas/backtesting.py
```

Endpoints:

- `POST /backtesting/run`
- `GET /backtesting/{run_id}`
- `GET /backtesting/{run_id}/trades`
- `GET /backtesting/{run_id}/equity`
- `GET /backtesting/{run_id}/replay`

### UI

```text
ui/src/app/(dashboard)/backtests/page.tsx
ui/src/app/(dashboard)/simulation/page.tsx
ui/src/app/(dashboard)/simulation/replay/page.tsx
ui/src/components/backtesting/
ui/src/components/simulation/
```

### Exit checklist

- [ ] Backtest can run one simple strategy.
- [ ] Backtest can run one complex/stateful strategy.
- [ ] Event-driven engine works.
- [ ] Vectorized engine works where applicable.
- [ ] Results are persisted or exportable.
- [ ] API exposes backtest run/results.
- [ ] Basic UI can run and view backtest.
- [ ] No analytics/risk logic is mixed inside the engine.

---

## Sprint 5 — Analytics Domain

### Domain

```text
tools/analytics/
```

### Goal

Build analytics after backtesting produces stable results.

### Existing functionality to preserve

- Metrics.
- Overview.
- Returns.
- Ratios.
- Drawdowns.
- Risks.
- Benchmark.
- Distributions.
- Efficiency.
- Statistical tests.
- Decision scorecard.
- All/Long/Short splits.
- Periodical analysis.
- Rolling analysis.
- Trade analysis.
- MAE/MFE.
- Runup/drawdown.
- Winning/losing trades.
- Series stats.

### Domain language

- Trade record.
- Equity curve.
- Metric.
- Return.
- Drawdown.
- Ratio.
- Distribution.
- Benchmark.
- Period.
- Rolling window.
- Long/short/all split.
- Report.

### Files to create

```text
tools/analytics/
  __init__.py
  README.md
  models.py
  schemas.py
  validators.py
  common.py
  metrics.py
  overview.py
  returns.py
  drawdowns.py
  ratios.py
  risks.py
  benchmark.py
  distributions.py
  efficiency.py
  statistical_tests.py
  decision_scorecard.py
  period_analysis.py
  trade_analysis.py
  reporting.py
  standard_tools.py

tests/unit/tools/analytics/
  test_metrics.py
  test_overview.py
  test_returns.py
  test_drawdowns.py
  test_ratios.py
  test_risks.py
  test_benchmark.py
  test_distributions.py
  test_efficiency.py
  test_statistical_tests.py
  test_period_analysis.py
  test_trade_analysis.py

tests/integration/tools/analytics/
  test_backtest_to_analytics_workflow.py

tests/usage/tools/analytics/
  analyze_backtest_example.py
  period_analysis_example.py
  trade_analysis_example.py

docs/domains/analytics/
  README.md
  metric_catalog.md
  acceptance_criteria.md
```

### Models/schemas needed now

Only analytics-related models:

- `AnalyticsInput`
- `MetricResult`
- `AnalyticsReport`
- `PeriodAnalysisReport`
- `TradeAnalysisReport`
- `LongShortSplitReport`

### Core implementation

- Consume `BacktestResult` output.
- Calculate metrics.
- Calculate returns.
- Calculate drawdowns.
- Calculate ratios.
- Calculate distributions.
- Calculate period analysis.
- Calculate trade analysis.
- Generate reports for API/UI/agents.

### API

```text
api/routes/analytics.py
api/schemas/analytics.py
```

Endpoints:

- `GET /analytics/backtest/{run_id}`
- `GET /analytics/backtest/{run_id}/periods`
- `GET /analytics/backtest/{run_id}/trades`
- `GET /analytics/backtest/{run_id}/drawdowns`

### UI

```text
ui/src/app/(dashboard)/performance/page.tsx
ui/src/app/(dashboard)/performance/overview/page.tsx
ui/src/app/(dashboard)/performance/periodical-analysis/page.tsx
ui/src/app/(dashboard)/performance/trade-analysis/page.tsx
ui/src/components/performance/
```

### Exit checklist

- [ ] Analytics consumes backtest results.
- [ ] All/Long/Short splits work.
- [ ] Periodical analysis works.
- [ ] Trade analysis works.
- [ ] API exposes analytics.
- [ ] UI can display core reports.
- [ ] Risk is not mixed into analytics except descriptive metrics.

---

## Sprint 6 — Research Domain

### Domain

```text
tools/research/
```

### Goal

Build research and edge-discovery tools after data, indicators, backtesting, and analytics exist.

### Existing functionality to preserve

- Seasonality.
- Spread-aware seasonality.
- Market structure.
- Market structure calibration.
- Market structure profiles.
- Market structure robustness/stability.
- Market structure strategy fit.
- EDS trend persistence.
- EDS mean reversion.
- EDS null models.
- Null models.
- Feature calculations.
- Leakage detection.
- Feature pipeline.
- Unsupervised insights.
- Research reports.
- Research scorecard.

### Domain language

- Edge hypothesis.
- Research dataset.
- Feature set.
- Leakage check.
- Null model.
- Seasonality profile.
- Market structure profile.
- Research report.
- Evidence.

### Files to create

```text
tools/research/
  __init__.py
  README.md
  models.py
  schemas.py
  validators.py
  config.py
  classifier.py
  seasonality.py
  null_models.py
  scorecard.py
  reporting.py
  standard_tools.py
  core_metrics/
  data/
  features/
  modeling/
  market_structure/
  edge_discovery/

tests/unit/tools/research/
  test_seasonality.py
  test_null_models.py
  test_leakage.py
  test_market_structure.py
  test_scorecard.py

tests/integration/tools/research/
  test_edge_discovery_workflow.py

tests/usage/tools/research/
  seasonality_example.py
  edge_discovery_example.py
  market_structure_example.py

docs/domains/research/
  README.md
  acceptance_criteria.md
```

### Models/schemas needed now

Only research-related models:

- `ResearchDataset`
- `EdgeHypothesis`
- `FeatureSet`
- `ResearchFinding`
- `ResearchReport`
- `MarketStructureProfile`
- `SeasonalityReport`

### API/UI

Add when reports are stable:

```text
api/routes/research.py
api/routes/edge.py
ui/src/app/(dashboard)/research/page.tsx
ui/src/app/(dashboard)/edge-lab/page.tsx
```

### Exit checklist

- [ ] Research reports can be generated.
- [ ] Seasonality includes spread analysis.
- [ ] Market structure workflows are preserved.
- [ ] Edge discovery workflows are preserved.
- [ ] Reports can feed strategy creation later.

---

## Sprint 7 — Optimization and Robustness Domain

### Domain

```text
tools/optimization/
```

### Goal

Build optimization only after strategy, backtesting, analytics, and research exist.

### Existing functionality to preserve

- Grid search.
- Random search.
- Bayesian optimization.
- Genetic optimization.
- Monte Carlo.
- Walk-forward.
- Robustness tools.
- Scoring.
- Splitters.
- Parallel optimization.
- Portfolio optimizer.
- StrategyQuant-style robustness workflow.

### Domain language

- Parameter space.
- Trial.
- Optimization run.
- Objective.
- Split.
- IS/OOS.
- WFO.
- WFM.
- Monte Carlo.
- Robustness score.
- Candidate ranking.

### Files to create

```text
tools/optimization/
  __init__.py
  README.md
  models.py
  schemas.py
  validators.py
  core.py
  execution.py
  result.py
  scoring.py
  splitters.py
  monte_carlo.py
  walk_forward.py
  robustness_tools.py
  portfolio_optimizer.py
  parallel.py
  methods/
    __init__.py
    grid_search.py
    random_search.py
    bayesian.py
    genetic.py
  standard_tools.py
```

### Models/schemas needed now

Only optimization-related models:

- `ParameterSpace`
- `OptimizationConfig`
- `OptimizationTrial`
- `OptimizationResult`
- `MonteCarloConfig`
- `WalkForwardConfig`
- `RobustnessReport`

### Exit checklist

- [ ] Parameter sweeps work.
- [ ] Monte Carlo robustness works.
- [ ] Walk-forward works.
- [ ] Results are stored/exportable.
- [ ] Strategy ranking works.
- [ ] No risk/execution logic is mixed in.

---

## Sprint 8 — Risk Domain

### Domain

```text
tools/risk/
```

### Goal

Build portfolio risk and trade acceptance after backtesting/analytics/optimization produce stable inputs.

### Existing functionality to preserve

- Position sizing.
- Exposure.
- Margin.
- Drawdown.
- Correlation.
- VaR.
- CVaR.
- Portfolio state.
- Portfolio snapshot.
- Risk snapshot.
- Risk scorecards.
- Governance engine.
- Governor.
- Limits.
- Pre-trade checks.
- Post-trade checks.
- Circuit breakers.
- Regimes.
- Scenarios.
- Replay and what-if.
- Reports.
- Storage.
- Validators.
- Live safety checks.
- Kill switch.

### Domain language

- Portfolio state.
- Account state.
- Position state.
- Symbol state.
- Trade proposal.
- Risk decision.
- Risk snapshot.
- Exposure.
- Risk contribution.
- Limit.
- Breach.
- Governor.
- Regime.
- Scenario.
- Kill switch.

### Files to create

Risk is large, so it should be built in sub-sprints.

```text
tools/risk/
  __init__.py
  README.md
  models.py
  schemas.py
  validators.py
  errors.py
  standard_tools.py

  calculations/
  metrics/
  portfolio/
  limits/
  governance/
  regimes/
  scenarios/
  replay/
  reports/
  scoring/
  optimization/
  storage/
  live/
```

### Risk sub-sprints

#### Sprint 8.1 — Risk calculations

- Position sizing.
- Exposure.
- Margin.
- Drawdown.
- Correlation.
- VaR.
- CVaR.

#### Sprint 8.2 — Portfolio state and snapshots

- Account state.
- Position state.
- Portfolio state.
- Symbol state.
- Snapshot builder.

#### Sprint 8.3 — Limits and policy checks

- Hard limits.
- Soft limits.
- Pre-trade checks.
- Post-trade checks.
- Circuit breakers.

#### Sprint 8.4 — Risk governor

- Trade proposal.
- Portfolio impact.
- Risk decision.
- Evidence.
- Approve/reject logic.

#### Sprint 8.5 — Regimes, scoring, reports

- Market regime.
- Volatility regime.
- Liquidity regime.
- Crisis regime.
- Risk scorecard.
- Risk report.

#### Sprint 8.6 — What-if, replay, and live safety

- Scenario engine.
- What-if engine.
- Replay engine.
- Live safety checks.
- Kill switch.

### Models/schemas needed now

Create them only as each risk sub-sprint needs them:

- `RiskCalculationInput`
- `PortfolioState`
- `RiskSnapshot`
- `TradeProposal`
- `RiskDecision`
- `LimitBreach`
- `RegimeState`
- `ScenarioResult`
- `KillSwitchEvent`

### API/UI

Add after governor and snapshots work:

```text
api/routes/risk.py
ui/src/app/(dashboard)/risk-center/page.tsx
ui/src/components/risk/
```

### Exit checklist

- [ ] Risk calculations are tested.
- [ ] Portfolio state works.
- [ ] Risk snapshot works.
- [ ] Risk governor approves/rejects with evidence.
- [ ] Kill switch works.
- [ ] Risk API/UI exists.
- [ ] Execution cannot bypass risk later.

---

## Sprint 9 — Execution Domain

### Domain

```text
tools/execution/
```

### Goal

Build controlled, auditable paper/live execution after risk is complete enough to gate trades.

### Existing functionality to preserve

- Approval packet builder.
- Approval state machine.
- Authority.
- Order assembler.
- Attempts.
- Idempotency.
- Receipts.
- Broker connectivity.
- MT5 bridge.
- cTrader bridge.
- Paper broker.
- Pre-send checks.
- Readiness.
- Order router.
- Send service.
- Reconciliation.
- Compensation.
- Shadow execution.
- Monitoring.
- Cost enforcement.
- Live engine.
- Position manager.
- State manager.
- Signal processor.
- Trade executor.
- Kill switch tools.

### Domain language

- Execution intent.
- Approval.
- Order request.
- Broker bridge.
- Send attempt.
- Receipt.
- Reconciliation.
- Paper broker.
- Live session.
- Shadow mode.
- Compensation.
- Readiness check.
- Critical action.

### Files to create

```text
tools/execution/
  __init__.py
  README.md
  models.py
  schemas.py
  validators.py
  errors.py
  authority.py
  assembler.py
  order_router.py
  pre_send.py
  send_service.py
  idempotency.py
  attempts.py
  receipts.py
  readiness.py
  trade_validators.py
  trade_action_governor.py
  standard_tools.py

  approval/
  brokers/
  bridges/
  live/
  reconciliation/
  compensation/
  monitoring/
  shadow/
  cost/
  performance/
```

### Execution sub-sprints

#### Sprint 9.1 — Paper execution

- Paper broker.
- Paper order request.
- Paper order result.
- Paper account state.
- Paper positions.

#### Sprint 9.2 — Execution intent and idempotency

- Intent builder.
- Idempotency key.
- Attempt record.
- Receipt record.

#### Sprint 9.3 — Approval and readiness

- Approval packet.
- Approval state machine.
- Readiness checks.
- Pre-send validation.

#### Sprint 9.4 — Broker bridges

- Base bridge.
- MT5 bridge.
- cTrader bridge.
- Broker connectivity.

#### Sprint 9.5 — Reconciliation and compensation

- Broker truth.
- Internal state comparison.
- Mismatch incident.
- Compensation registry.

#### Sprint 9.6 — Live execution gate

- Live session.
- Signal processor.
- Trade executor.
- Position manager.
- State manager.
- Kill switch integration.

### API/UI

```text
api/routes/execution.py
api/routes/live.py
api/routes/approvals.py

ui/src/app/(dashboard)/execution/page.tsx
ui/src/app/(dashboard)/live/page.tsx
ui/src/app/(dashboard)/board-room/page.tsx
```

### Exit checklist

- [ ] Paper trading works.
- [ ] Live execution is disabled by default.
- [ ] Risk decision is required before execution.
- [ ] Approval is required for controlled/critical actions.
- [ ] Idempotency prevents duplicate sends.
- [ ] Reconciliation works.
- [ ] Kill switch blocks execution.

---

## Sprint 10 — Portfolio Domain

### Domain

```text
tools/portfolio/
```

### Goal

Build portfolio operations after risk and execution exist.

### Existing functionality to preserve

- Allocation service.
- Audit service.
- Cost service.
- Incident service.
- Lifecycle service.
- Reporting service.
- Portfolio kill switch.
- Standard portfolio tools.

### Domain language

- Portfolio.
- Allocation.
- Strategy lifecycle.
- Admission.
- Pause.
- Retire.
- Incident.
- Cost report.
- Portfolio report.
- Portfolio action.

### Files to create

```text
tools/portfolio/
  __init__.py
  README.md
  models.py
  schemas.py
  validators.py
  allocation_service.py
  audit_service.py
  cost_service.py
  incident_service.py
  lifecycle_service.py
  reporting_service.py
  kill_switch.py
  standard_tools.py
```

### Exit checklist

- [ ] Portfolio reporting works.
- [ ] Allocation recommendations work.
- [ ] Lifecycle transitions are controlled.
- [ ] Incidents are tracked.
- [ ] Portfolio tools can be used by agents later.

---

## Sprint 11 — Notification Domain

### Domain

```text
tools/notification/
```

### Goal

Build notifications for risk, execution, approvals, incidents, and reports.

### Existing functionality to preserve

- Email.
- SMS.
- Telegram.
- Notification manager.
- Templates.
- Notification tools.

### Files to create

```text
tools/notification/
  __init__.py
  README.md
  models.py
  schemas.py
  validators.py
  base.py
  config.py
  manager.py
  templates.py
  email.py
  sms.py
  telegram.py
  tools.py
```

### Exit checklist

- [ ] Dry-run notifications work.
- [ ] Templates work.
- [ ] Risk/execution/approval alerts can be sent.
- [ ] Secrets are not hardcoded.

---

## Sprint 12 — Governance and Permissions Domain

### Domain

```text
tools/governance/
```

### Goal

Build executable governance before agentic AI is allowed to control tools.

### Existing functionality to preserve

- Constitution.
- Agent permissions.
- Risk policy.
- Strategy lifecycle policy.
- Approval standard.
- Risk control standard.
- AI chatbot RBAC matrix.
- AI chatbot execution safety.
- AI chat retention policy.
- Policy map.
- Runtime permissions.
- Safety.

### Files to create

```text
tools/governance/
  __init__.py
  README.md
  models.py
  schemas.py
  permissions.py
  rbac.py
  approvals.py
  audit.py
  evidence.py
  policy_loader.py
  action_safety.py
  retention.py
  standard_tools.py

docs/governance/
  constitution.md
  agent_permissions.md
  risk_policy.md
  strategy_lifecycle.md
  Approval_Standard.md
  Risk_Control_Standard.md
  AI_Chatbot_RBAC_Matrix.md
  AI_Chatbot_Execution_Safety.md
  AI_Chat_Retention_Policy.md
  Policy_Map.md
```

### Domain language

- Permission.
- Role.
- Policy.
- Approval.
- Evidence.
- Audit event.
- Controlled action.
- Critical action.
- Forbidden action.

### Exit checklist

- [ ] Unknown agent defaults to deny.
- [ ] Unknown tool defaults to deny.
- [ ] Controlled actions require approval.
- [ ] Critical actions require human/risk approval.
- [ ] Audit events are required for sensitive actions.
- [ ] Governance rules are executable, not just markdown.

---

## Sprint 13 — Agentic Domain

### Domain

```text
tools/agentic/
```

### Goal

Add agentic AI only after the deterministic tool domains and governance boundaries exist.

### Existing functionality to preserve

- Agent catalog.
- Agent runtime.
- Agent permissions.
- Runner.
- Safety.
- Schemas.
- Workflows.
- CEO/planner agents.
- Research department.
- Strategy creation department.
- Simulation department.
- Risk department.
- Portfolio department.
- Executive department.
- Agent workflow tests.
- Red-team tests.

### Domain language

- Agent.
- Manifest.
- Instruction.
- Skill.
- Tool.
- Permission.
- Evidence pack.
- Workflow.
- Planner.
- CEO.
- Department.
- Approval gate.

### Files to create

```text
tools/agentic/
  __init__.py
  README.md
  models.py
  schemas.py
  validators.py
  runtime/
    __init__.py
    runner.py
    safety.py
    tool_registry.py
    permissions_adapter.py
    audit_adapter.py
  agents/
    __init__.py
    ceo.py
    planner.py
    research_agent.py
    strategy_creator_agent.py
    backtest_agent.py
    risk_agent.py
    portfolio_agent.py
    execution_agent.py
    reporter_agent.py
  workflows/
    __init__.py
    research_workflow.py
    strategy_creation_workflow.py
    backtest_workflow.py
    risk_review_workflow.py
    paper_trading_workflow.py
    live_activation_workflow.py
    incident_workflow.py
  manifests/
    ceo.agent.md
    planner.agent.md
    research.agent.md
    strategy_creator.agent.md
    backtest.agent.md
    risk.agent.md
    portfolio.agent.md
    execution.agent.md
```

### Exit checklist

- [ ] Agents can only use registered tools.
- [ ] Tool calls go through governance.
- [ ] Evidence packs are required.
- [ ] CEO routes tasks correctly.
- [ ] Execution agent cannot bypass risk/approval.
- [ ] Red-team tests pass.

---

## Sprint 14 — Conversation / AI CEO Domain

### Domain

```text
tools/conversation/
```

### Goal

Build the user-facing AI CEO chat after the agentic domain exists.

### Existing functionality to preserve

- CEO gateway.
- Context builders.
- Memory.
- Prompt builder.
- Retention.
- Stream manager.
- Summaries.
- Title generation.
- AI chat conversations.
- Signal proposals.
- Action drafts.
- Telemetry.
- Metadata.
- Page intelligence.

### Files to create

```text
tools/conversation/
  __init__.py
  README.md
  models.py
  schemas.py
  ceo_gateway.py
  memory.py
  prompt_builder.py
  retention.py
  service.py
  stream_manager.py
  summaries.py
  title.py
  context/
    __init__.py
    base.py
    builders.py
    dashboard.py
    data_workspace.py
    strategy_detail.py
    backtest_detail.py
    optimization.py
    portfolio_risk.py
    live_trading.py
    operator_workflow.py
    freshness.py
```

### API/UI

```text
api/routes/ai_chat.py
ui/src/components/ai-chat/
ui/src/components/ai-ceo/
ui/src/app/(dashboard)/ai-ceo/page.tsx
```

### Exit checklist

- [ ] AI CEO chat can answer with context.
- [ ] AI CEO can route to agent workflows.
- [ ] Action drafts are stored.
- [ ] Retention policy works.
- [ ] Chat cannot secretly execute live actions.

---

## Sprint 15 — API Consolidation

### Goal

At this point, most domains have APIs. This sprint cleans and standardizes the API.

### Files

```text
api/
  __init__.py
  main.py
  app.py
  router.py
  dependencies.py
  auth.py
  auth_utils.py
  models.py
  websocket.py
  scheduler.py
  events.py
  health.py
  middleware/
    security.py
  routes/
    auth.py
    data.py
    strategies.py
    backtesting.py
    analytics.py
    research.py
    optimization.py
    risk.py
    execution.py
    portfolio.py
    live.py
    approvals.py
    ai_chat.py
    docs.py
    settings.py
```

### Exit checklist

- [ ] Routes are thin.
- [ ] Business logic stays in `tools/`.
- [ ] API schemas are route-specific or imported from domain schemas.
- [ ] Auth/session handling is consistent.
- [ ] Permission checks are consistent.
- [ ] Websocket events are standardized.

---

## Sprint 16 — UI Consolidation

### Goal

Build or refine the UI only after stable domain APIs exist.

### Main UI areas

```text
ui/src/app/(dashboard)/
  data/
  strategies/
  backtests/
  simulation/
  performance/
  research/
  edge-lab/
  optimization/
  risk-center/
  execution/
  live/
  portfolio/
  ai-ceo/
  board-room/
  agents/
  audit/
  settings/
  documentation/
```

### Exit checklist

- [ ] UI pages map to stable API routes.
- [ ] Shared components are reused.
- [ ] Each page has loading/error/empty states.
- [ ] Live/risk/execution pages display safety state clearly.
- [ ] AI CEO is integrated as a governed interface.

---

## Sprint 17 — Production Hardening and Legacy Parity

### Goal

Verify that HaruQuantAI preserves old HaruQuant functionality and is safe to operate.

### Files

```text
docs/operations/
  Production_Readiness.md
  Observability_Audit.md
  Operations_Runbook.md
  Incident_Response_Runbook.md
  acceptance_criteria.md

docs/rebuild/
  Final_Parity_Report.md
  Known_Differences.md
  Migration_Runbook.md

scripts/migration/
  import_legacy_strategies.py
  import_legacy_backtests.py
  import_legacy_risk_records.py
  import_legacy_ai_chat.py
```

### Exit checklist

- [ ] Old capability matrix is fully checked.
- [ ] Known differences are documented.
- [ ] Legacy migration scripts exist.
- [ ] Production readiness checklist passes.
- [ ] Live trading is disabled by default.
- [ ] Kill switch works.
- [ ] Secrets are audited.
- [ ] End-to-end workflows pass.

---

## 9. Final Domain Build Order

The recommended order is:

```text
0. Skeleton and standards
1. Data
2. Indicators
3. Strategies
4. Backtesting
5. Analytics
6. Research
7. Optimization / Robustness
8. Risk
9. Execution
10. Portfolio
11. Notification
12. Governance / Permissions
13. Agentic AI
14. Conversation / AI CEO
15. API consolidation
16. UI consolidation
17. Production hardening and legacy parity
```

This order is agile because each sprint creates only the files needed for the current domain.

---

## 10. Why This Is Better Than the Previous Plan

The previous plan was architecturally complete but mentally heavy.

This new plan is better because:

1. The top-level structure remains simple.
2. Each tool domain is easy to visualize.
3. Contracts are created only when needed.
4. Schemas live near the domain that owns them.
5. Testing is domain-specific.
6. UI/API are added only after domain logic works.
7. Agents are added late, after deterministic tools and governance exist.
8. The rebuild becomes a series of small complete products instead of one large waterfall.
9. You can stop after any sprint and still have a useful system.
10. Functionality preservation remains controlled through the legacy-to-new map.

---

## 11. Non-Loss Rule

Every sprint must update:

```text
docs/rebuild/Functionality_Preservation_Matrix.md
docs/rebuild/Legacy_To_New_Module_Map.md
```

Each preserved feature must be marked as one of:

- `NOT_STARTED`
- `IN_PROGRESS`
- `IMPLEMENTED`
- `TESTED`
- `DOCUMENTED`
- `MIGRATED`
- `DEFERRED_WITH_REASON`

No old functionality should disappear silently.

---

## 12. Standard Acceptance Gate for Every Domain

A domain is complete only when:

- [ ] It has a clear DDD purpose.
- [ ] It has a README.
- [ ] It has only the models/schemas needed now.
- [ ] It has typed implementation files.
- [ ] It has validators.
- [ ] It has explicit errors.
- [ ] It has logging.
- [ ] It has unit tests.
- [ ] It has usage examples.
- [ ] It has integration tests if it touches another domain.
- [ ] It has API routes only if needed.
- [ ] It has UI only if needed.
- [ ] It has docs.
- [ ] It updates the legacy-to-new map.
- [ ] It does not create unnecessary future-domain files.

---

## 13. Standard Prompt for Building Each Domain

Use this prompt whenever starting a new HaruQuantAI domain:

```text
We are rebuilding HaruQuantAI using DDD and agile vertical slices.

Current domain: <domain_name>

Rules:
1. Build only what this domain needs now.
2. Do not create schemas/contracts for future domains.
3. Keep all domain logic inside tools/<domain>/.
4. Add tests under tests/unit/tools/<domain>/.
5. Add usage examples under tests/usage/tools/<domain>/.
6. Add docs under docs/domains/<domain>/.
7. Add API only if the domain logic is stable and needs to be exposed.
8. Add UI only if the API is stable and the user workflow needs it.
9. Update Functionality_Preservation_Matrix.md.
10. Update Legacy_To_New_Module_Map.md.

Task:
Create the implementation plan and file checklist for this domain:
<domain_name>

Existing functionality to preserve:
<paste audit section or old file list>

Output:
1. Domain purpose
2. Domain language
3. Files to create now
4. Files not to create yet
5. Models/schemas needed now
6. Tool functions
7. Unit tests
8. Usage examples
9. Integration tests
10. API, if needed
11. UI, if needed
12. Exit acceptance checklist
```

---

## 14. Immediate Next Step

Start with:

```text
Sprint 0 — Rebuild Ground Rules and Repository Skeleton
```

Then proceed to:

```text
Sprint 1 — Data Domain
```

The first real implementation domain should be `tools/data/`, because reliable market data is the foundation for everything else.

Do not create backtesting, risk, execution, or agent files until their sprint begins.

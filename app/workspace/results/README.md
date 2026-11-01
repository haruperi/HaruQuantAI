# Results contracts and ownership

Feature: `FEAT-RESULTS-CONTRACTS`. Owner: `app/workspace/results`.
Implemented and qualified in commit `60f7f828c9c2c34091b808bf8dc3d34817b7105d`.

The Results workspace provides strategy result selection, comprehensive trade and performance analytics, multi-market/sub-result key projections, interactive equity and drawdown charting, databank management and correlation filtering, platform loaders/savers, and extension catalogs.

## 1. Architecture and Domain Contracts

`AppResultsService` acts as the root workspace controller, coordinating 33 specialized service modules and 4 extension cohorts across `app/workspace/results/` and `app/extend/`:

- **Root Selection & Projection (`app_results.py`):**
  - Manages `AppResultsSelectionState` and queries `ResultStore` and `DatabankContainer`.
  - Projections expose `Main` first, `Portfolio` second (when present), followed by sub-result keys in deterministic lexicographical order.
  - Strategy absence strictly raises `DomainError(code="RESULTS_STRATEGY_NOT_FOUND")`.
- **Views & Analytics Modules (`results_overview.py`, `results_s_p_overview.py`, `results_stockpicker.py`, `results_strategy_config.py`, `results_trade_analysis.py`, `results_trade_list.py`, `results_tradelist_views.py`, `results_explore.py`, `results_report.py`, `overview_template_policy.py`):**
  - Calculate trade metrics, payoff ratios, win/loss stats, duration buckets, and time-bucket aggregations.
  - Support user-defined column configurations and view presets with schema-validated persistence.
  - Template selection policy prioritizes `SQDefault` on empty or matching tuples.
- **Chart Engines (`results_equity_chart.py`, `equity_chart_benchmark.py`, `equity_chart_daily_chart.py`, `equity_chart_drawdown.py`, `equity_chart_volatility.py`, `equity_chart_volume.py`, `results_chart.py`, `results_profile_chart.py`, `results_portfolio_correlation.py`):**
  - Generate deterministic equity curves, underwater drawdown series, monthly/daily returns, rolling volatility, and volume distributions.
  - Profile chart groups performance by parameter ranges; portfolio correlation computes Pearson correlation matrices across strategy profit/loss series.
- **Databank Management & Custom Tabs (`results_databank_actions.py`, `results_databank_views.py`, `custom_databank_actions.py`, `databank_rename.py`, `servlet_rename_tool.py`, `databank_filter_by_correlation.py`, `results_plugins.py`, `custom_results_plugin_actions.py`):**
  - System databanks (`"Results"`, `"Last generation"`) are immutable and protected (`DomainError(code="RESULTS_SYSTEM_DATABANK_PROTECTED")`).
  - Built-in tabs (`Overview`, `List of trades`, `Equity chart`, `Trade analysis`, `Source code`) cannot be renamed or deleted (`DomainError(code="RESULTS_BUILTIN_PLUGIN_IMMUTABLE")`).
  - Correlation filtering applies greedy selection based on strategy fitness, flagging pairs exceeding threshold `max_correlation` and supporting safe batch deletion.
- **Exporters and Loaders (`results_source_code.py`, `loader_s_q3.py`, `loader_s_q4.py`, `saver_h_t_m_l.py`, `saver_p_d_f.py`, `saver_s_q3.py`, `saver_strategy_trades.py`):**
  - Implement strict security guards against Zip Slip / path traversal (`DomainError(code="RESULTS_PATH_TRAVERSAL_DETECTED")`) and payload size limits (`DomainError(code="RESULTS_FILE_TOO_LARGE")`).
  - Generates valid `%PDF-1.4` binary report structures, standalone HTML reports, CSV trade lists, and legacy SQ3/SQ4 strategy packages.

## 2. Concrete Extension Cohorts (`app/extend/`)

The workspace registers and evaluates concrete extension definitions per `06-AppResults.md`:

- **Columns (`app/extend/columns/`):** 160 typed descriptors and metric evaluators across `databanks.py` (121 definitions), `trades.py` (31 definitions), and `walk_forward.py` (8 definitions).
- **Stats Overview Templates (`app/extend/stats/overview_templates.py`):** 7 standard statistical templates (`SQDefault`, `SQDefaultPct`, `DefaultOpenDD`, `DefaultStability`, `CustomA`, `CustomB`, `CustomC`).
- **Engine Charts Catalog (`app/extend/engine_charts/catalog.py`):** 14 operational and diagnostic charts (Throughput, Memory, Databank Fitness, Generation Evolution).
- **Custom Analyzers (`app/extend/custom_analysis/analyzers.py`):** `CorrelationFilterAnalyzer` and `OutlierTradeAnalyzer`.

## 3. Host Capability Ownership

| Capability | Authority | Results Workspace Usage |
|---|---|---|
| Result Persistence | `app/core/trading/results/store.py::ResultStore` | Backtest run results, trade series, equity points, sub-result keys |
| Databank Storage | `app/core/jobs/databank.py::DatabankContainer` | Strategy registration, databank views, reordering, deletion |
| Host State | `app/core/host/persistence.py::HostPersistence` | Transaction-backed atomic mutations and project workspace schemas |
| Logging & Errors | `app/core/host/logging.py`, `app/core/lib/errors.py` | Non-silent audit logging and structured `DomainError` envelopes |

## 4. Verification and Parity Evidence

All functional code was verified in commit `60f7f828c9c2c34091b808bf8dc3d34817b7105d`:

- **Pytest (Backend & Extensions):** `125 passed in 0.91s` across `tests/workspace/results` and `tests/extend`.
- **Test Coverage:** `87.83%` branch-aware coverage across `app/workspace/results` and `app/extend/` (exceeding the constitutional 80.0% requirement).
- **Vitest (Frontend UI):** `29 test files, 121 tests passed` in `app/web/tests/workspace/results`.
- **Static Analysis & Typing:**
  - `ruff check`: Clean across all 102 source and test files.
  - `mypy --strict`: Clean with zero type diagnostics across all 102 files.
- **Frontend Build:** `npm --prefix app/web run typecheck` and `npm --prefix app/web run build` completed cleanly.

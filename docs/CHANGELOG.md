# Changelog

All notable HaruQuantAI project changes should be recorded here.

## [Unreleased]

| ID | Functionality | Notes |
| -- | ------------- | ----- |
|    |               |       |
|    |               |       |

## Added

| ID | Functionality | Notes |
| -- | ------------- | ----- |
| ADD-001 | Loguru Structured Logging | Integrated `loguru` for structured application logging with rotating file handlers (`app.log`, `access.log`, `debug.log`, `errors.log`). Usage example `example_01_loguru_example()` in `tests/usage/app/services/01_utils.py`. |
| ADD-002 | Deterministic Error Utility | Added comprehensive error handling utility and deterministic error code registry. Usage example `example_02_error_handling_example()` in `tests/usage/app/services/01_utils.py`. |
| ADD-003 | Standard Tool Envelope | Added Standard tool envelopes and deterministic utility contracts. Usage example `example_03_standard_tool_envelope_example()` in `tests/usage/app/services/01_utils.py`. |
| ADD-004 | Safe Path Normalization | Added Safe path normalization and explicit directory creation helpers. Usage example `example_04_safe_path_normalization_example()` in `tests/usage/app/services/01_utils.py`. |
| ADD-005 | Security helpers | Added Security helpers for redaction, hashing, and optional encryption. Usage example `example_05_security_and_redaction()` in `tests/usage/app/services/01_utils.py`. |
| ADD-006 | Runtime settings. | Added Runtime configuration and settings loading using Pydantic. Usage example `example_06_runtime_settings()` in `tests/usage/app/services/01_utils.py`. |
| ADD-007 | `app/utils` Module Documentation & Dependencies | Created the README of `app/utils` from the standard template, resolved missing `logger.py` and `event_bus.py` bridges, and added `pydantic`/`pydantic-settings` dependencies. |
| ADD-008 | Broker Resolver | Added broker integration framework with support for Binance, Dukascopy, Yahoo, MT5, and cTrader providers. |
| ADD-009 | Market Data Service Architecture | Added market data service architecture with multi-source support for market data fetching, caching, and time-series management. Module `app/services/data`. Usage examples in `tests/usage/app/services/02_data.py`. |
| ADD-010 | Indicator Service library | Added technical indicator service library with support for various technical indicators and module `app/services/indicators`. Usage examples in `tests/usage/app/services/03_indicators.py`. |
| ADD-011 | Strategy Service architecture | Added strategy service architecture with multi-source support for strategy execution, caching, and time-series management. Module `app/services/strategies`. Usage examples in `tests/usage/app/services/04_strategies.py`. |
| ADD-012 | Trader Service Architecture | Added trader service architecture with support for account information, deal information, history order information, order information, position information, rate limiting, symbol information, and terminal information. Module `app/services/trading`. Usage examples in `tests/usage/app/services/07_trading.py`. |
| ADD-013 | Risk Management Service | Added risk management service with support for risk assessment, position sizing, portfolio management, and scenario analysis. Module `app/services/risk`. Usage examples in `tests/usage/app/services/05_risk.py`. |
| ADD-014 | Analytics Service | Added analytics service for performance evaluation, scenario analysis, and reporting. Module `app/services/analytics`. Usage examples in `tests/usage/app/services/06_analytics.py`. |
| ADD-015 | Optimisation Service | Added optimisation service  with search algorithms, parameter tuning, and walk-forward analysis support. Module `app/services/optimisation`. Usage examples in `tests/usage/app/services/08_optimisation.py`. |
| ADD-016 | Live Trading Service | Added core live runtime monitoring services, including health tracking, incident management, and state reconciliation. Usage examples in `tests/usage/app/services/10_live.py`. |
| ADD-017 | Research Service | Added core research service, for data leakage detection, chronological splitting, and edge discovery studies. Usage examples in `tests/usage/app/services/09_research.py`. |
| ADD-018 | Simulator Service | Added core simulator service for backtest execution, data simulation, and strategy backtesting. Module `app/services/simulator`. Usage examples in `tests/usage/app/services/08_simulator.py`. |
| ADD-019 | Risk Models V2 modular package | Transitioned from a single flat `models.py` file to a multi-file package `app/services/risk/models/` containing `enums.py`, `contracts.py`, and `serialization.py` to support cleaner extension and clear separation of concerns. |
| ADD-020 | Risk Config V2 modular package | Migrated `app/services/risk/config.py` to modular sub-package `app/services/risk/config/` (`schema.py`, `loader.py`, `profiles.py`, `hashing.py`), transitioning default JSON config profiles to YAML formats with JSON fallback compatibility. |
| ADD-021 | Risk Storage V2 modular package | Decoupled the persistence layer from core risk governance by introducing a structured package `app/services/risk/storage/` containing `ports.py` (Protocols for drawdown state, kill switches, audit, policies, and decisions), `in_memory.py` (thread-safe, lock-isolated state store with simulated fault injection), and init package exports. |
| ADD-022 | Risk Policy V2 modular package | Transitioned legacy flat policy logic into a structured package `app/services/risk/policy/` containing `contracts.py` (policy scopes, precedence, rules, and override results), `resolver.py` (precedence specificity scoring, time-bounded validation, and budget gate checks), and `overrides.py` (cryptographic override token compatibility checks and ceilings validation). |
| ADD-023 | Risk Readiness V2 modular package | Introduced structured package `app/services/risk/readiness/` containing `readiness.py` to perform system integration and pre-runtime readiness validation checks, including dependency status checking, safety modes coverage matrix validation, delivery plan constraints verification, and dry-run report compilation. |
| ADD-024 | Risk Regime V2 modular package | Transitioned legacy flat regime logic into a structured package `app/services/risk/regime/` containing `assessor.py` (regime classification, spread, volatility, liquidity, news, rollover blackouts) and `validation.py` (inputs validation and reason codes). |
| ADD-025 | Risk Sizing V2 modular package | Transitioned position sizing engine from single flat `sizing.py` to modular package `sizing/` (`contracts.py`, `normalization.py`, `calculators.py`) with stateless lot-sizing calculations. |
| ADD-026 | Risk Exposure V2 modular package | Modularized currency exposure engine from flat `exposure.py` into package `exposure/` (`fx_legs.py`, `aggregation.py`), introducing pure FX pair parsing, leg decomposition, and currency conversion validation. |
| ADD-027 | Risk Correlation V2 modular package | Transitioned correlation and cluster risk engine from legacy flat `correlation.py` to structured package `correlation/` (`contracts.py`, `returns.py`, `fallbacks.py`, `engine.py`), implementing pure returns construction, alignment policies, and connected cluster exposures. |
| ADD-028 | Risk Tail Risk V2 modular package | Upgraded legacy flat Value-at-Risk & Expected Shortfall engine into structured package `app/services/risk/tail_risk/` (`contracts.py`, `var.py`, `expected_shortfall.py`), implementing parametric/historical VaR calculators, CVaR calculations, risk contributions, and validation checks. |
| ADD-029 | Risk Stress V2 modular package | Upgraded legacy flat stress testing module to structured package `app/services/risk/stress/` (`registry.py`, `contracts.py`, `engine.py`), implementing declarative macro scenarios, fast unvalidated `QuickProjectedPortfolio` iteration, pre-calculated multipliers optimization (< 35ms target under load), and legacy compatibility wrappers. |










## Fixed

| ID | Functionality | Notes |
| -- | ------------- | ----- |
| FIX-001 | Windows CI & Dependency Constraints | Configured CI quality gates to run on `windows-latest` and set `pyproject.toml` dependency management to target `sys_platform == 'win32'` and `platform_machine == 'AMD64'`. |
| FIX-002 | `pytest` Import Collisions & Circularity | Resolved circular dependency between `errors.py` and `security.py` by making imports local, and configured `import_mode = "importlib"` in `pyproject.toml` to prevent test namespace pollution. |
| FIX-003 | Logging Consolidation | Merged `logging.py` into `logger.py` to simplify logging namespaces and prevent multiple configuration files. |
| FIX-004 | Analytics Requirement Traceability | Completed analytics requirement traceability anchors, restored analytics test collection, added architecture-required catalog/test paths, and documented the full analytics audit evidence report. |
| FIX-005 | Analytics Usage Examples | Reworked `tests/usage/06_analytics.py` into 23 executable analytics examples, aligned equity-return traceability to `equity.py`, and fixed dashboard truncation for small point limits. |
| FIX-006 | Analytics Per-File Coverage | Added analytics usage and metric-surface pytest coverage so every file under `app/services/analytics` is above the 80% coverage gate. |
| FIX-007 | Analytics V2 README | Rewrote `app/services/analytics/README.md` to document the V2 package layout, public tool facade, contracts, metric surface, usage examples, reports, dashboards, and verification commands. |



## Decisions

| ID      | Decision                          | Notes                                                                                                                                                                                                                                |
| ------- | --------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| DEC-001 | Project Name                      | project name is HaruQuantAI                                                                                                                                                                                                          |
| DEC-002 | Project Memory                    | project memory lives in durable files, not chat                                                                                                                                                                                      |
| DEC-003 | Rebuild Style                     | HaruQuantAI is a clean-room rebuild that preserves important functionality and safety behavior while adding new product behavior                                                                                                     |
| DEC-004 | Product Scope                     | product scope includes tools, API, UI, data, live, research, and conversation surfaces                                                                                                                |
| DEC-005 | No Direct MT5 Import              | No file should import MetaTrader5 directly. The client/connection should be resolved via app/services/brokers/mt5.py module/functions to maintain a single point of control over terminal state.                                     |
| DEC-006 | Standalone Simulator Service      | Standalone simulator service is created to separate simulation state from external live broker adapter definitions.                                                                                                                  |
| DEC-007 | Strategy Config JSON Schema       | All strategy configurations must be declared as JSON Schema dictionaries (`config_schema`), setting `config_model = None`.                                                                                                       |
| DEC-008 | Private Helper Naming             | Strategy internal helper functions must begin with a leading underscore (`_`) to clearly identify them as private.                                                                                                                 |
| DEC-009 | Domain Error Consolidation        | All domain and module-specific errors are consolidated into the single namespace `app/utils/errors.py` to prevent code duplication and simplify exception handling.                                                                |
| DEC-010 | Config JSON Schema                | All official AI risk tools or functions must accept JSON-compatible dictionary payloads (`dict[str, Any]`) for configuration parameters to decouple parameters from internal Pydantic schemas.                                     |
| DEC-011 | Dynamic Symbol Info Lookup        | Sizing calculators must never hardcode symbol information values (such as point sizes and contract sizes) and must instead fetch actual values dynamically via the MT5 broker client, using robust offline fallback dictionary maps. |
| DEC-012 | Traceable Task Evidence Locations | Every completed checklist task item in implementation plans must include the code file path and line number at the end of the line (e.g.*app/services/risk/models.py:19*).                                                         |
| DEC-013 | Service Module Documentation      | Each module/service must have its own `README.md`, using `docs/templates/README.md` as a template if needed.                                                                                                                            |
| DEC-014 | Data Source Fail-Closed Behavior  | Market data requests must use the explicitly requested source only. If that source fails, the gateway reports the source error and does not fall back to another source.                                                                 |
| DEC-015 | YAML Risk Config Profiles | Transitioned default risk configuration profiles to YAML files under `app/services/risk/configs/` while keeping backwards-compatible fallback parsing of legacy JSON files. |

## Pending Decisions

| ID       | Proposed decision                             | Why pending                                              |
| -------- | --------------------------------------------- | -------------------------------------------------------- |
| PDEC-001 | Chat and regulated artifact retention policy. | Compliance impact.                                       |
| PDEC-002 | Risk threshold defaults.                      | Numeric trading policy must be approved before live use. |
| PDEC-003 | Event bus implementation phases.              | Needs reliability and deployment input.                  |
| PDEC-004 | New service-tool catalog format.              | Needs implementation repo structure.                     |
| PDEC-005 | SQLite production duration.                   | Depends on concurrency and deployment targets.           |

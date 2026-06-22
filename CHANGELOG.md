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
| ADD-009 | Market Data Service Architecture | Added market data service architecture with multi-source support for market data fetching, caching, and time-series management. Usage examples in `tests/usage/app/services/02_data.py`. |
| ADD-010 | Indicator Service library | Added technical indicator service library with support for various technical indicators and their usage examples in `tests/usage/app/services/03_indicators.py`. |
| ADD-011 | Strategy Service architecture | Added strategy service architecture with multi-source support for strategy execution, caching, and time-series management. Usage examples in `tests/usage/app/services/04_strategies.py`. |





## Fixed

| ID | Functionality | Notes |
| -- | ------------- | ----- |
| FIX-001 | Windows CI & Dependency Constraints | Configured CI quality gates to run on `windows-latest` and set `pyproject.toml` dependency management to target `sys_platform == 'win32'` and `platform_machine == 'AMD64'`. |
| FIX-002 | `pytest` Import Collisions & Circularity | Resolved circular dependency between `errors.py` and `security.py` by making imports local, and configured `import_mode = "importlib"` in `pyproject.toml` to prevent test namespace pollution. |
| FIX-003 | Logging Consolidation | Merged `logging.py` into `logger.py` to simplify logging namespaces and prevent multiple configuration files. |



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

## Pending Decisions

| ID       | Proposed decision                             | Why pending                                              |
| -------- | --------------------------------------------- | -------------------------------------------------------- |
| PDEC-001 | Chat and regulated artifact retention policy. | Compliance impact.                                       |
| PDEC-002 | Risk threshold defaults.                      | Numeric trading policy must be approved before live use. |
| PDEC-003 | Event bus implementation phases.              | Needs reliability and deployment input.                  |
| PDEC-004 | New service-tool catalog format.              | Needs implementation repo structure.                     |
| PDEC-005 | SQLite production duration.                   | Depends on concurrency and deployment targets.           |

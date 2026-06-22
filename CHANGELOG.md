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
| ADD-001 | Loguru Structured Logging | Integrated `loguru` for structured application logging with rotating file handlers (`app.log`, `access.log`, `debug.log`, `errors.log`). See usage example `example_01_loguru_example()` in `tests/usage/app/services/01_utils.py`. |

## Fixed

| ID | Functionality | Notes |
| -- | ------------- | ----- |
| FIX-001 | Windows CI & Dependency Constraints | Configured CI quality gates to run on `windows-latest` and set `pyproject.toml` dependency management to target `sys_platform == 'win32'` and `platform_machine == 'AMD64'`. |



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

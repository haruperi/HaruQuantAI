# HaruQuant Utils Module Technical Specification v8

**Document status:** Production-ready standalone implementation specification with final dependency, scope, enum, and error-extensibility polish
**Target module:** `tools/utils/`
**Target quality level:** Production-grade shared utility foundation for HaruQuantAI
**Architecture style:** Clean public API, small focused modules, typed contracts, deterministic behavior, test-first implementation
**Compatibility policy:** Clean API only. No transitional aliases, no compatibility shims, no duplicate wrapper modules, and no fallback import paths.
**Recommended next action:** Implement the module from this specification as a fresh professional utilities package.
**v8 update focus:** Incorporates final implementation polish for lazy heavy-dependency loading, diagnostic-only data-quality scope, enum/string canonicalization, and extensible domain error mapping.

---

## 1. Executive Summary

The `tools/utils/` module is the shared utility foundation for HaruQuantAI.

It must provide stable, typed, documented, logged, and testable infrastructure used by all higher-level domains, including data, research, simulation, risk, portfolio, execution, analytics, governance, and agentic workflows.

This specification defines a complete professional design for the utilities module. It is intentionally standalone and implementation-ready. The module must preserve the required utility capabilities while presenting them through a clean final structure.

The utilities module must support:

- project-wide structured logging
- standard HaruQuant tool response envelopes
- deterministic error codes and exception mapping
- request, workflow, generic ID, and version helpers
- shared status, severity, risk-level, and environment-mode constants
- timestamp and timezone normalization with a UTC-first policy
- safe path handling
- canonical JSON serialization for audit, hashing, caching, and reproducible tests
- dataframe and OHLCV utilities
- OHLCV data quality validation with bounded diagnostics and deterministic scoring
- schema, payload, risk-level, numeric-range, and contract validation
- security helpers for redaction, hashing, encryption, and secret selection
- audit-safe redaction for logs, errors, metadata, and tool responses
- runtime settings loading and injection with deterministic source precedence
- standard execution timing helpers for consistent `execution_ms` values
- explicit tool-response schema validation constants
- schema version compatibility checks for validation contracts
- resource limits for large validation workloads
- lazy loading rules for pandas and other heavy optional dependencies
- stateless, diagnostic-only data-quality validation boundaries
- string-serializable constants plus enum-friendly canonicalization for internal type safety
- extensible domain error mapping through `HaruQuantError` and `code` attributes
- unit tests, usage examples, and CI quality gates

The module must be implemented without unnecessary abstraction. Shared helpers should remain small, clear, typed, and easy to test. Agent-callable tools must use the official HaruQuant tool response schema.

---

## 2. Design Goals

### 2.1 Primary Goals

The utilities module must:

1. Provide stable foundational helpers for all HaruQuant domains.
2. Keep the public API small and intentional.
3. Separate low-level helpers from official agent-callable tools.
4. Use deterministic behavior for validation, IDs, timestamps, paths, and error mapping.
5. Make failures explicit and actionable.
6. Avoid silent failures.
7. Avoid broad catch-all behavior except at controlled tool boundaries.
8. Avoid hidden state unless explicitly documented and test-covered.
9. Use production-friendly defaults.
10. Support future agentic AI workflows through standard response envelopes, metadata, request tracing, and safe logging.

### 2.2 Non-Goals

The utilities module must not:

1. Own trading strategy logic.
2. Own broker execution logic.
3. Own risk-governor decisions.
4. Own portfolio allocation decisions.
5. Own application orchestration.
6. Become a dumping ground for unrelated helpers.
7. Export every internal helper as a public agent tool.
8. Hide external dependency behavior behind unclear convenience functions.
9. Perform live trading or live account mutation.
10. Make trading, risk, allocation, execution, or strategy acceptance decisions.
11. Implement UI, database repositories, or backtest engines.

---

## 3. Production Readiness Requirements

A utility file is production-ready only when it has:

- file-level docstring
- clear public function and class docstrings
- type hints for all public functions and methods
- explicit input validation where applicable
- explicit output shape where applicable
- deterministic error behavior
- structured logging for important events and recoverable failures
- no `print()` in production logic
- no unstructured `None` returns from official tools
- no accidental public exports
- no avoidable circular imports
- no secret leakage in logs or errors
- tests covering success, invalid input, edge cases, and failure paths
- usage examples for official agent-callable tools
- compatibility with Black, isort, Flake8, mypy, pytest, and coverage

---

## 4. Target Folder Structure

```text
tools/
    __init__.py

    utils/
        __init__.py
        logger.py
        standard.py
        errors.py
        identity.py
        normalization.py
        paths.py
        dataframe_tools.py
        data_quality.py
        schema_validation.py
        security.py
        settings.py

tests/
    unit/
        tools/
            utils/
                test_utils_registry.py
                test_logger.py
                test_standard.py
                test_errors.py
                test_identity.py
                test_normalization.py
                test_paths.py
                test_dataframe_tools.py
                test_data_quality.py
                test_schema_validation.py
                test_security.py
                test_settings.py

    usage/
        tools/
            utils/
                standard.py
                data_quality.py
                schema_validation.py
                security.py
                settings.py
```

---

## 5. Public API Policy

### 5.1 Registry Principle

`tools/utils/__init__.py` is the public registry for the utility domain.

Only names intentionally imported and listed in `__all__` are public.

Public names fall into two categories:

1. **Official AI Tools**: agent-callable functions that must return the standard HaruQuant tool envelope.
2. **Support Objects / Support Helpers**: foundational utilities used by production code. These may return native Python values when they are not agent-callable tools.

### 5.2 Official AI Tool Rule

A function is an official AI Tool when it is:

- exposed through `tools/utils/__init__.py`
- listed in `__all__`
- intended for direct agent or workflow use as a tool

Every official AI Tool must include:

- `request_id: str | None = None`
- tool metadata
- risk and side-effect flags
- input validation
- execution timing
- structured logging
- standard return schema
- deterministic error codes
- no silent failure

### 5.3 Support Object Exception

`logger` is a support object, not an official AI Tool.

It may be exported for project-wide usage:

```python
from tools.utils import logger
```

It is exempt from the tool response envelope because it is not callable as an agent tool.

### 5.4 Internal Helper Rule

Internal helpers may return native Python objects such as strings, dictionaries, dataclasses, lists, tuples, booleans, timestamps, or pandas objects.

Internal helpers must still be:

- typed
- documented
- deterministic
- tested where important
- named clearly
- kept private when not intended for public import

Internal helpers should start with `_` unless they are intentionally public support helpers.

---

## 6. Final Public Registry

The final `tools/utils/__init__.py` must expose only the approved public API below.

```python
"""
Utility helpers exposed to HaruQuantAI modules and agents.

This package provides project-wide logging, standard response envelopes,
error mapping, identity helpers, normalization helpers, safe path utilities,
dataframe helpers, OHLCV quality validation, schema validation, security
helpers, and runtime settings loaders.
"""

# logger.py support object
from tools.utils.logger import logger
from tools.utils.logger import get_logger
from tools.utils.logger import configure_logging

# standard.py official AI tool support
from tools.utils.standard import build_error_response
from tools.utils.standard import build_success_response
from tools.utils.standard import build_tool_metadata
from tools.utils.standard import get_execution_ms
from tools.utils.standard import normalize_severity
from tools.utils.standard import to_canonical_json
from tools.utils.standard import validate_risk_level
from tools.utils.standard import validate_tool_response_schema
from tools.utils.standard import TOOL_RESPONSE_REQUIRED_KEYS
from tools.utils.standard import TOOL_RESPONSE_METADATA_REQUIRED_KEYS
from tools.utils.standard import VALID_ERROR_CODES
from tools.utils.standard import VALID_AGENT_STATUSES
from tools.utils.standard import VALID_ENVIRONMENT_MODES
from tools.utils.standard import VALID_RISK_LEVELS
from tools.utils.standard import VALID_SEVERITIES
from tools.utils.standard import VALID_TOOL_STATUSES

# errors.py support helpers
from tools.utils.errors import HaruQuantError
from tools.utils.errors import HaruQuantValidationError
from tools.utils.errors import HaruQuantConfigurationError
from tools.utils.errors import HaruQuantSecurityError
from tools.utils.errors import HaruQuantDataError
from tools.utils.errors import HaruQuantExternalServiceError
from tools.utils.errors import error_name
from tools.utils.errors import message_for

# identity.py support helpers
from tools.utils.identity import ensure_version
from tools.utils.identity import generate_id
from tools.utils.identity import generate_prefixed_id
from tools.utils.identity import generate_request_id
from tools.utils.identity import generate_workflow_id
from tools.utils.identity import validate_request_id
from tools.utils.identity import validate_workflow_id

# normalization.py support helpers
from tools.utils.normalization import DEFAULT_TIMEZONE
from tools.utils.normalization import format_timestamp_z
from tools.utils.normalization import is_stale
from tools.utils.normalization import normalize_timestamp
from tools.utils.normalization import normalize_timezone_for_series
from tools.utils.normalization import parse_datetime
from tools.utils.normalization import to_naive_utc
from tools.utils.normalization import to_utc

# paths.py support helpers
from tools.utils.paths import ensure_dir
from tools.utils.paths import ensure_parent_dir
from tools.utils.paths import normalize_path

# dataframe_tools.py support helpers
from tools.utils.dataframe_tools import align_dataframes_by_datetime
from tools.utils.dataframe_tools import bars_to_records
from tools.utils.dataframe_tools import chunked
from tools.utils.dataframe_tools import combine_params
from tools.utils.dataframe_tools import compare_dataframes
from tools.utils.dataframe_tools import compare_ohlc
from tools.utils.dataframe_tools import compare_ohlcv
from tools.utils.dataframe_tools import serialize_dataframe_records

# data_quality.py official AI tools and support helpers
from tools.utils.data_quality import prepare_ohlcv_data
from tools.utils.data_quality import validate_ohlcv_quality

# schema_validation.py official AI tools and support helpers
from tools.utils.schema_validation import validate_approval_packet
from tools.utils.schema_validation import validate_artifact_reference
from tools.utils.schema_validation import validate_blocked_actions
from tools.utils.schema_validation import validate_data_freshness
from tools.utils.schema_validation import validate_environment_mode
from tools.utils.schema_validation import validate_evidence_pack
from tools.utils.schema_validation import validate_handoff_payload
from tools.utils.schema_validation import validate_input_schema
from tools.utils.schema_validation import validate_output_schema
from tools.utils.schema_validation import validate_registry_entry
from tools.utils.schema_validation import validate_numeric_range
from tools.utils.schema_validation import validate_required_fields

# security.py support helpers and official tools where explicitly used by agents
from tools.utils.security import MAX_REDACTION_DEPTH
from tools.utils.security import decrypt_data
from tools.utils.security import encrypt_data
from tools.utils.security import get_encryption_key
from tools.utils.security import hash_password
from tools.utils.security import is_sensitive_key
from tools.utils.security import redact_mapping
from tools.utils.security import redact_scalar
from tools.utils.security import redact_text
from tools.utils.security import select_active_secret_version
from tools.utils.security import verify_password

# settings.py support helpers
from tools.utils.settings import RuntimeSettings
from tools.utils.settings import inject_runtime_settings
from tools.utils.settings import load_runtime_settings
from tools.utils.settings import load_runtime_settings_from_mapping


__all__ = [
    # logger.py support object
    "logger",
    "get_logger",
    "configure_logging",

    # standard.py
    "build_error_response",
    "build_success_response",
    "build_tool_metadata",
    "get_execution_ms",
    "normalize_severity",
    "to_canonical_json",
    "validate_risk_level",
    "validate_tool_response_schema",
    "TOOL_RESPONSE_REQUIRED_KEYS",
    "TOOL_RESPONSE_METADATA_REQUIRED_KEYS",
    "VALID_ERROR_CODES",
    "VALID_AGENT_STATUSES",
    "VALID_ENVIRONMENT_MODES",
    "VALID_RISK_LEVELS",
    "VALID_SEVERITIES",
    "VALID_TOOL_STATUSES",

    # errors.py
    "HaruQuantError",
    "HaruQuantValidationError",
    "HaruQuantConfigurationError",
    "HaruQuantSecurityError",
    "HaruQuantDataError",
    "HaruQuantExternalServiceError",
    "error_name",
    "message_for",

    # identity.py
    "ensure_version",
    "generate_id",
    "generate_prefixed_id",
    "generate_request_id",
    "generate_workflow_id",
    "validate_request_id",
    "validate_workflow_id",

    # normalization.py
    "DEFAULT_TIMEZONE",
    "format_timestamp_z",
    "is_stale",
    "normalize_timestamp",
    "normalize_timezone_for_series",
    "parse_datetime",
    "to_naive_utc",
    "to_utc",

    # paths.py
    "ensure_dir",
    "ensure_parent_dir",
    "normalize_path",

    # dataframe_tools.py
    "align_dataframes_by_datetime",
    "bars_to_records",
    "chunked",
    "combine_params",
    "compare_dataframes",
    "compare_ohlc",
    "compare_ohlcv",
    "serialize_dataframe_records",

    # data_quality.py
    "prepare_ohlcv_data",
    "validate_ohlcv_quality",

    # schema_validation.py
    "validate_numeric_range",
    "validate_approval_packet",
    "validate_artifact_reference",
    "validate_blocked_actions",
    "validate_data_freshness",
    "validate_environment_mode",
    "validate_evidence_pack",
    "validate_handoff_payload",
    "validate_input_schema",
    "validate_output_schema",
    "validate_registry_entry",
    "validate_required_fields",

    # security.py
    "MAX_REDACTION_DEPTH",
    "decrypt_data",
    "encrypt_data",
    "get_encryption_key",
    "hash_password",
    "is_sensitive_key",
    "redact_mapping",
    "redact_scalar",
    "redact_text",
    "select_active_secret_version",
    "verify_password",

    # settings.py
    "RuntimeSettings",
    "inject_runtime_settings",
    "load_runtime_settings",
    "load_runtime_settings_from_mapping",
]
```

---

## 7. Official AI Tool Classification

The utilities module should keep most functions as support helpers. Only functions that an agent or workflow should call directly as tools must use the full AI Tool envelope.

### 7.1 Required Official AI Tools

| Tool | Module | Risk | Side Effects | Purpose |
|---|---|---:|---|---|
| `validate_ohlcv_quality` | `data_quality.py` | low | read-only | Validate OHLCV data quality and return structured issues/profile. |
| `validate_input_schema` | `schema_validation.py` | low | read-only | Validate incoming payloads against required input contract. |
| `validate_output_schema` | `schema_validation.py` | low | read-only | Validate outgoing payloads before downstream handoff. |
| `validate_handoff_payload` | `schema_validation.py` | low | read-only | Validate department-to-department workflow payloads. |
| `validate_evidence_pack` | `schema_validation.py` | low | read-only | Validate evidence packs before strategy/risk/execution use. |
| `validate_approval_packet` | `schema_validation.py` | low | read-only | Validate human approval packet completeness. |
| `validate_registry_entry` | `schema_validation.py` | low | read-only | Validate registry metadata for tools, agents, or workflows. |
| `validate_data_freshness` | `schema_validation.py` | low | read-only | Validate freshness metadata for data-dependent decisions. |

### 7.2 Conditional Official AI Tools

These functions may be official AI Tools only if agents are expected to call them directly:

| Function | Module | Risk | Notes |
|---|---|---:|---|
| `redact_text` | `security.py` | low | Useful for audit/log redaction workflows. |
| `redact_mapping` | `security.py` | low | Useful before writing audit or tool logs. |
| `load_runtime_settings` | `settings.py` | medium | Reads environment/config; agent use should be limited. |
| `encrypt_data` | `security.py` | medium | Requires strict key handling and error controls. |
| `decrypt_data` | `security.py` | medium | Should be restricted and heavily tested. |

If classified as official AI Tools, these functions must return the standard envelope. If used only by production code, they may remain support helpers returning native values.

### 7.3 Support Helpers

Support helpers include:

- logging helpers
- response builders
- exception classes
- timestamp normalizers
- ID generators
- safe path helpers
- dataframe helpers
- password hashing helpers
- settings dataclasses

Support helpers are not required to return the full AI Tool envelope unless explicitly promoted as official AI Tools.

---

## 8. Standard Tool Response Contract

Every official AI Tool must return exactly this top-level shape:

```python
{
    "status": "success" | "error",
    "message": str,
    "data": Any,
    "error": None | {
        "code": str,
        "details": str,
    },
    "metadata": {
        "tool_name": str,
        "tool_version": str,
        "tool_category": str,
        "tool_risk_level": str,
        "request_id": str | None,
        "execution_ms": float,
        "read_only": bool,
        "writes_file": bool,
        "modifies_database": bool,
        "places_trade": bool,
        "requires_network": bool,
    },
}
```

Allowed statuses:

```text
success
error
```

Common deterministic error codes:

```text
INVALID_INPUT
PERMISSION_DENIED
DATA_NOT_FOUND
EMPTY_RESULT
SERVICE_UNAVAILABLE
BROKER_UNAVAILABLE
DATABASE_ERROR
NETWORK_ERROR
TIMEOUT
VALIDATION_FAILED
TOOL_EXECUTION_FAILED
CONFIGURATION_ERROR
SECURITY_ERROR
UNKNOWN_ERROR
```

---

## 9. Module Specifications

## 9.1 `tools/__init__.py`

### Purpose

Declare the top-level `tools` package and avoid side effects.

### Requirements

- Must contain a concise module docstring.
- Must not import heavy domains eagerly.
- Must not contain business logic.
- Must not configure logging.
- Must not mutate environment variables.

### Target Content

```python
"""
Top-level HaruQuantAI tools package.

Tool domains are exposed through their own package registries, such as
`tools.utils`, `tools.data`, `tools.execution`, and `tools.risk`.
"""
```

---

## 9.2 `tools/utils/logger.py`

### Purpose

Provide the project-wide module logger used by production files.

### Public API

```python
logger
get_logger(name: str | None = None) -> logging.Logger
configure_logging(level: str | int = "INFO") -> None
```

`logger`, `get_logger`, and `configure_logging` must be exported as support helpers. They are not official AI Tools and are exempt from the standard tool response envelope.

### Requirements

- Use Python `logging`.
- Avoid duplicate handlers.
- Avoid writing secrets.
- Default logger name should be stable, for example `haruquant`.
- Allow module-level child loggers through `get_logger`.
- Keep configuration minimal.
- Do not force application-level logging configuration when imported.

### Acceptance Criteria

- Importing `from tools.utils import logger` works.
- Importing the module does not add duplicate handlers repeatedly.
- Logging level can be configured intentionally.
- Tests verify no duplicate handlers after repeated calls.

---

## 9.3 `tools/utils/standard.py`

### Purpose

Provide shared helpers for official AI Tool responses and metadata.

### Public API

```python
build_tool_metadata(
    *,
    tool_name: str,
    tool_version: str,
    tool_category: str,
    tool_risk_level: str,
    request_id: str | None,
    execution_ms: float,
    read_only: bool,
    writes_file: bool,
    modifies_database: bool,
    places_trade: bool,
    requires_network: bool,
) -> dict[str, Any]

build_success_response(
    *,
    message: str,
    data: Any,
    metadata: dict[str, Any],
) -> dict[str, Any]

build_error_response(
    *,
    message: str,
    error_code: str,
    error_details: str,
    metadata: dict[str, Any],
) -> dict[str, Any]

get_execution_ms(start_time: float) -> float
validate_tool_response_schema(response: Mapping[str, Any]) -> bool
normalize_severity(value: str) -> str
validate_risk_level(value: str) -> bool
to_canonical_json(payload: Mapping[str, Any]) -> str

TOOL_RESPONSE_REQUIRED_KEYS = {"status", "message", "data", "error", "metadata"}
TOOL_RESPONSE_METADATA_REQUIRED_KEYS = {
    "tool_name",
    "tool_version",
    "tool_category",
    "tool_risk_level",
    "request_id",
    "execution_ms",
    "read_only",
    "writes_file",
    "modifies_database",
    "places_trade",
    "requires_network",
}
VALID_SEVERITIES = {"info", "warning", "error", "critical"}
VALID_TOOL_STATUSES = {"success", "error"}
VALID_AGENT_STATUSES = {
    "success",
    "error",
    "blocked",
    "needs_approval",
    "needs_clarification",
}
VALID_ENVIRONMENT_MODES = {"local", "development", "test", "staging", "production"}
VALID_RISK_LEVELS = {"low", "medium", "high", "critical"}
VALID_ERROR_CODES = {
    "INVALID_INPUT",
    "PERMISSION_DENIED",
    "DATA_NOT_FOUND",
    "EMPTY_RESULT",
    "SERVICE_UNAVAILABLE",
    "BROKER_UNAVAILABLE",
    "DATABASE_ERROR",
    "NETWORK_ERROR",
    "TIMEOUT",
    "VALIDATION_FAILED",
    "CONFIGURATION_ERROR",
    "SECRET_VERSION_NOT_FOUND",
    "TOOL_EXECUTION_FAILED",
    "UNKNOWN_ERROR",
}
```

### Requirements

- Must not depend on pandas, pydantic, cryptography, broker packages, or external APIs.
- Must expose `get_execution_ms(start_time)` so official tools calculate timing consistently.
- `get_execution_ms` must return milliseconds rounded consistently to three decimals.
- Must validate required top-level response keys using `TOOL_RESPONSE_REQUIRED_KEYS`.
- Must validate required metadata keys using `TOOL_RESPONSE_METADATA_REQUIRED_KEYS`.
- Must validate known status values.
- Must validate error shape.
- Must validate error codes against `VALID_ERROR_CODES` where practical.
- Must centralize standard severity, status, environment, and risk-level values.
- Public contracts must use JSON-safe canonical strings, while internal code may use enums for type safety. Validators must accept supported enums and strings, then immediately normalize them to canonical string values.
- Must provide canonical JSON serialization for deterministic audit hashes, cache keys, reproducible tests, and comparison workflows.
- Canonical JSON must sort keys, normalize datetimes, reject unserializable values clearly, and redact sensitive values before serialization where configured.
- Must be deterministic.
- Must be safe for all tool domains to import.

### Acceptance Criteria

- Success response matches standard schema.
- Error response matches standard schema.
- Missing metadata keys fail schema validation.
- Invalid status fails schema validation.
- Metadata includes all required side-effect flags.
- `get_execution_ms` returns deterministic formatting for a mocked clock/start time.
- `validate_tool_response_schema` rejects missing top-level keys, missing metadata keys, invalid statuses, and malformed errors.

---

## 9.4 `tools/utils/errors.py`

### Domain Error Extensibility Rule

`errors.py` defines the shared HaruQuant error foundation. Domain-specific errors created later by data, research, simulation, risk, portfolio, execution, analytics, or governance modules must either:

1. inherit from `HaruQuantError`, or
2. expose a compatible `code: str` attribute that can be mapped by `standard.py`.

The standard response builders must be able to map any `HaruQuantError` subclass generically into the HaruQuant tool error envelope without requiring every domain error to be hardcoded inside `tools.utils`. Unknown non-HaruQuant exceptions must still map safely to `UNKNOWN_ERROR` or `TOOL_EXECUTION_FAILED` at controlled tool boundaries.


### Purpose

Provide standard utility exceptions and deterministic error-code helpers.

### Public API

```python
class HaruQuantError(Exception): ...
class HaruQuantValidationError(HaruQuantError): ...
class HaruQuantConfigurationError(HaruQuantError): ...
class HaruQuantSecurityError(HaruQuantError): ...
class HaruQuantDataError(HaruQuantError): ...
class HaruQuantExternalServiceError(HaruQuantError): ...

error_name(code: str | int) -> str
message_for(code: str | int, default: str | None = None) -> str
```

### Requirements

- Every exception should carry a deterministic `code` attribute.
- Error messages must be human-readable.
- Error helpers must support string and integer-style codes where useful.
- Error helpers must never raise for unknown codes unless explicitly requested.
- Unknown codes should resolve to `UNKNOWN_ERROR` or provided defaults.

### Acceptance Criteria

- Exception classes preserve code and message.
- `error_name` is deterministic.
- `message_for` returns useful fallback messages.
- Unknown codes are handled safely.

---

## 9.5 `tools/utils/identity.py`

### Purpose

Provide deterministic and traceable ID/version helpers.

### Public API

```python
generate_id(prefix: str | None = None) -> str
generate_prefixed_id(prefix: str) -> str
generate_request_id(prefix: str = "req") -> str
generate_workflow_id(prefix: str = "wf") -> str
validate_request_id(request_id: str) -> bool
validate_workflow_id(workflow_id: str) -> bool
ensure_version(version: str | None, default: str = "1.0.0") -> str
```

### Requirements

- IDs must be string-safe.
- Prefix validation must reject empty or unsafe prefixes.
- Generated IDs should be collision-resistant.
- Use UUID4 or ULID-like logic unless deterministic IDs are explicitly required by caller.
- Version values must be non-empty strings.
- Request IDs and workflow IDs must use consistent, string-safe formats suitable for logs, audit records, tool responses, and agent handoffs.
- Trace helper validation must be deterministic and must not perform external lookups.

### Acceptance Criteria

- Generated IDs are unique across repeated calls.
- Prefixes are normalized safely.
- Invalid prefixes raise or return structured validation failures depending on function classification.
- `ensure_version(None)` returns the default.

---

## 9.6 `tools/utils/normalization.py`

### Purpose

Provide timestamp, timezone, and freshness normalization helpers.

### Public API

```python
DEFAULT_TIMEZONE = "UTC"

parse_datetime(value: Any) -> datetime
normalize_timestamp(value: Any, *, assume_timezone: str = "UTC") -> datetime
to_utc(value: datetime) -> datetime
to_naive_utc(value: datetime) -> datetime
format_timestamp_z(value: datetime) -> str
normalize_timezone_for_series(series: Any, *, timezone: str = "UTC") -> Any
    # Phase 1 accepts Any for lightweight imports, but intended inputs are pandas Series objects or DataFrame timestamp columns.
is_stale(timestamp: datetime, *, max_age_seconds: int, now: datetime | None = None) -> bool
```

### Requirements

- Timezone behavior must be explicit.
- Naive datetimes must be handled deterministically.
- ISO strings must parse consistently.
- `now` should be injectable for deterministic tests.
- Invalid datetimes must fail clearly.
- No hidden local-time assumptions.

### Acceptance Criteria

- UTC-aware datetimes remain UTC-aware.
- Naive datetimes are normalized using the configured assumption.
- `format_timestamp_z` returns ISO UTC format ending in `Z`.
- `is_stale` is deterministic with injected `now`.

---

## 9.7 `tools/utils/paths.py`

### Purpose

Provide safe path normalization and directory creation helpers.

### Public API

```python
normalize_path(path: str | Path, *, base_dir: str | Path | None = None) -> Path
ensure_dir(path: str | Path) -> Path
ensure_parent_dir(path: str | Path) -> Path
```

### Requirements

- Path inputs must be validated.
- Directory creation functions must be explicit side-effect helpers.
- Path traversal risk must be considered when `base_dir` is supplied.
- Functions must return `Path` objects.
- File and directory permissions must use platform-safe defaults.

### Side Effects

| Function | Side Effect |
|---|---|
| `normalize_path` | none |
| `ensure_dir` | creates directory if missing |
| `ensure_parent_dir` | creates parent directory if missing |

### Acceptance Criteria

- Valid paths normalize correctly.
- Empty paths fail validation.
- Parent directory creation is testable with temporary directories.
- Unsafe traversal outside `base_dir` is rejected.

---

## 9.8 `tools/utils/dataframe_tools.py`

### Lazy Dependency Loading Rule

`dataframe_tools.py` depends on pandas-like dataframe objects, but importing `tools.utils` must not force-load pandas.

Rules:

- Do not import pandas at module import time unless it is guarded by `typing.TYPE_CHECKING`.
- Runtime pandas imports must happen inside the functions that require pandas-specific behavior.
- Type hints should use `Any`, `Protocol`, postponed annotations, or `TYPE_CHECKING` imports to avoid heavy import costs.
- Importing `tools.utils` must remain lightweight for agents that only need logging, IDs, errors, standard responses, settings, or security helpers.
- Missing pandas must fail only when a dataframe helper is called, using `HaruQuantConfigurationError` or a clear native exception depending on helper type.


### Purpose

Provide small, reusable dataframe and OHLC/OHLCV helper functions.

### Public API

```python
align_dataframes_by_datetime(left: DataFrame, right: DataFrame, *, column: str = "datetime") -> tuple[DataFrame, DataFrame]
bars_to_records(data: DataFrame) -> list[dict[str, Any]]
chunked(items: Sequence[Any], size: int) -> Iterator[list[Any]]
combine_params(*mappings: Mapping[str, Any]) -> dict[str, Any]
compare_dataframes(left: DataFrame, right: DataFrame, *, tolerance: float = 1e-9) -> dict[str, Any]
compare_ohlc(left: DataFrame, right: DataFrame, *, tolerance: float = 1e-9) -> dict[str, Any]
compare_ohlcv(left: DataFrame, right: DataFrame, *, tolerance: float = 1e-9) -> dict[str, Any]
serialize_dataframe_records(data: DataFrame) -> list[dict[str, Any]]
```

### Requirements

- Dataframe helpers may return native Python objects.
- Input dataframe columns must be validated.
- Functions must not mutate input dataframes unless explicitly documented.
- Each dataframe helper must document whether it returns a copy, view, or transformed dataframe.
- Functions must avoid unnecessary deep copies on large datasets unless correctness requires them.
- Serialization must handle timestamps safely.
- `serialize_dataframe_records` must normalize datetime columns to UTC and format them as ISO strings with a trailing `Z` using `format_timestamp_z`.
- `compare_dataframes` must align by comparable indexes or fail with a clear validation error when indexes cannot be aligned deterministically.
- `chunked` must reject `size <= 0` with `HaruQuantValidationError` or `ValueError`.
- Comparisons must support tolerance.
- Empty dataframes must be handled deterministically.

### Acceptance Criteria

- Inputs are not mutated.
- Missing required columns fail clearly.
- Serialization outputs JSON-safe records where practical.
- Comparison outputs are deterministic and easy to assert in tests.
- Tests verify datetime serialization uses UTC `Z` strings.
- Tests verify index mismatch behavior.
- Tests verify `chunked(size <= 0)` fails clearly.

---

## 9.9 `tools/utils/data_quality.py`

### Diagnostic-Only Scope Boundary

`validate_ohlcv_quality` is a utility diagnostic and validation tool. It must stay stateless and must not repair, enrich, persist, or mutate the input data.

Rules:

- The tool may inspect, profile, score, and report issues.
- The tool must not forward-fill gaps, drop bad rows, resample candles, infer missing bars, rewrite timestamps, patch OHLC values, or normalize broker-specific symbol data.
- Any repair, resampling, enrichment, persistence, or data cleaning workflow belongs in `tools.data`, not `tools.utils`.
- The tool may provide remediation recommendations, but recommendations must be descriptive only.
- Caller-owned dataframes must not be mutated. If preparation is needed for validation, work on an internal copy or derived view and document the behavior.


### Purpose

Provide OHLCV preparation and quality validation for market data workflows.

### Public API

```python
prepare_ohlcv_data(
    data: DataFrame,
    *,
    datetime_column: str = "datetime",
    timezone: str = "UTC",
) -> DataFrame

validate_ohlcv_quality(
    data: DataFrame,
    *,
    symbol: str | None = None,
    timeframe: str | None = None,
    datetime_column: str = "datetime",
    open_column: str = "open",
    high_column: str = "high",
    low_column: str = "low",
    close_column: str = "close",
    volume_column: str | None = "volume",
    spread_column: str | None = "spread",
    max_gap_multiplier: float = 3.0,
    spike_zscore_threshold: float = 8.0,
    max_issue_samples: int = 10,
    max_issues_returned: int = 100,
    request_id: str | None = None,
) -> dict[str, Any]
```

### Official AI Tool Classification

`validate_ohlcv_quality` is an official low-risk read-only AI Tool.

Required metadata:

```python
TOOL_NAME = "validate_ohlcv_quality"
TOOL_VERSION = "1.0.0"
TOOL_CATEGORY = "utils.data_quality"
TOOL_RISK_LEVEL = "low"
REQUIRES_APPROVAL = False
READ_ONLY = True
WRITES_FILE = False
MODIFIES_DATABASE = False
PLACES_TRADE = False
REQUIRES_NETWORK = False
```

### Required Validation Checks

`validate_ohlcv_quality` must check:

1. Input is a pandas DataFrame.
2. Required OHLC columns exist.
3. Missing columns fail clearly with structured `INVALID_INPUT` details for mandatory columns.
4. Extra columns are ignored by default and may be reported as `info` severity when useful; extra columns must not fail validation unless they create ambiguity.
5. Datetime column exists or index is datetime-compatible.
6. Datetimes are parseable.
7. Timestamps are monotonic after preparation.
8. Duplicate timestamps are detected.
9. Duplicate OHLC/OHLCV rows are detected.
10. Missing timestamps or inferred gaps are detected where timeframe is known.
11. Market calendar gaps are distinguished from unexpected gaps where session rules are supplied.
12. Open, high, low, close values are numeric.
13. Negative prices are flagged.
14. Zero prices are flagged.
15. High-low relationship is valid.
16. OHLC values are within candle high/low range.
17. Zero volume is flagged when volume is supplied.
18. Negative volume is flagged when volume is supplied.
19. Spread is numeric and non-negative when supplied.
20. Extreme spikes are detected using configurable thresholds.
21. Flatline candles are detected.
22. Numeric infinities and NaN values are detected.
23. Timezone awareness is reported.
24. Session-level statistics are produced when possible.
25. Quality score is calculated deterministically.
26. Severity levels are assigned consistently.
27. Remediation recommendations are returned.
28. Issue samples are bounded by `max_issue_samples`.
29. Returned issue lists are bounded by `max_issues_returned`.
30. Large datasets must not cause oversized tool responses.
31. If `symbol` is provided and the dataframe contains a `symbol` column, all rows must match the requested symbol; mismatches must be reported as `SYMBOL_MISMATCH`.
32. If `symbol` is provided and no `symbol` column exists, validation may proceed but the response must mark symbol verification as `not_available` in `summary`.
33. If `timeframe` is provided, inferred timestamp spacing must be checked against the expected timeframe where possible; mismatches must be reported as `TIMEFRAME_MISMATCH` or `UNEXPECTED_TIME_GAP`.

### Deterministic Quality Score Rule

The OHLCV quality score must be deterministic and documented. The implementation may refine the exact formula, but v8 requires the following default penalty model unless a later module-specific specification replaces it:

```text
critical issue = -40 points
error issue    = -20 points
warning issue  = -5 points
info issue     = -1 point
minimum score  = 0
maximum score  = 100
```

Severity aggregation must be deterministic:

```text
any critical issue -> overall severity = critical
else any error     -> overall severity = error
else any warning   -> overall severity = warning
else               -> overall severity = info
```

The response must include enough summary counts to explain the score without returning every bad row. Issue truncation must be explicit through `summary["issues_truncated"]` and `summary["samples_truncated"]` when limits are reached.

### Required Return Data Shape

On success, `data` must include:

```python
{
    "symbol": str | None,
    "timeframe": str | None,
    "rows_checked": int,
    "quality_score": float,
    "passed": bool,
    "severity": "info" | "warning" | "error" | "critical",
    "issues": list[dict[str, Any]],
    "summary": dict[str, Any],
    "profile": dict[str, Any],
    "remediation": list[dict[str, Any]],
}
```

Each issue must include:

```python
{
    "code": str,
    "severity": "info" | "warning" | "error" | "critical",
    "message": str,
    "column": str | None,
    "row_count": int | None,
    "sample": list[Any],
}
```

### Acceptance Criteria

- Clean OHLCV data returns `status="success"` and `passed=True`.
- Bad OHLCV data returns `status="success"` with issues and `passed=False`.
- Invalid input returns `status="error"` with `INVALID_INPUT`.
- Tool metadata is complete.
- `execution_ms` is always included.
- Tests cover at least 15 distinct data-quality cases.
- Tests verify bounded issue samples and bounded issue counts.
- Tests verify deterministic scoring and severity aggregation.
- Tests verify a dataframe with 10,000 bad rows returns at most `max_issues_returned` issues and at most `max_issue_samples` samples per issue.
- Tests verify symbol mismatch, unavailable symbol verification, timeframe mismatch, missing mandatory columns, and extra-column handling.

---

## 9.10 `tools/utils/schema_validation.py`

### Purpose

Provide reusable validation helpers for agent, workflow, tool, registry, evidence, approval, and payload contracts.

### Public API

```python
validate_numeric_range(
    value: Any,
    *,
    name: str,
    min_value: float | None = None,
    max_value: float | None = None,
    allow_none: bool = False,
) -> dict[str, Any]
validate_required_fields(payload: Mapping[str, Any], required_fields: Sequence[str]) -> dict[str, Any]
validate_input_schema(
    payload: Mapping[str, Any],
    schema: Mapping[str, Any],
    *,
    schema_version: str | None = None,
    request_id: str | None = None,
) -> dict[str, Any]
validate_output_schema(
    payload: Mapping[str, Any],
    schema: Mapping[str, Any],
    *,
    schema_version: str | None = None,
    request_id: str | None = None,
) -> dict[str, Any]
validate_handoff_payload(payload: Mapping[str, Any], *, request_id: str | None = None) -> dict[str, Any]
validate_evidence_pack(payload: Mapping[str, Any], *, request_id: str | None = None) -> dict[str, Any]
validate_approval_packet(payload: Mapping[str, Any], *, request_id: str | None = None) -> dict[str, Any]
validate_registry_entry(payload: Mapping[str, Any], *, request_id: str | None = None) -> dict[str, Any]
validate_blocked_actions(payload: Mapping[str, Any], blocked_actions: Sequence[str], *, request_id: str | None = None) -> dict[str, Any]
validate_data_freshness(payload: Mapping[str, Any], *, max_age_seconds: int, request_id: str | None = None) -> dict[str, Any]
validate_environment_mode(mode: str, *, allowed_modes: Sequence[str] | None = None, request_id: str | None = None) -> dict[str, Any]
validate_artifact_reference(payload: Mapping[str, Any], *, request_id: str | None = None) -> dict[str, Any]
```

### Official AI Tool Classification

The following are official low-risk read-only AI Tools:

- `validate_input_schema`
- `validate_output_schema`
- `validate_handoff_payload`
- `validate_evidence_pack`
- `validate_approval_packet`
- `validate_registry_entry`
- `validate_data_freshness`

### Requirements

- Validators must return standard tool envelopes when official.
- `validate_numeric_range` is a support helper returning a native validation result, not a full tool envelope. Its native result must contain at minimum `valid: bool`, `message: str`, `code: str | None`, and `details: dict[str, Any]`.
- Official validators may wrap support-helper validation results inside the standard tool envelope.
- Numeric validation must be reusable for risk values, prices, volumes, spreads, scores, thresholds, and allocation limits.
- Validation results must be deterministic.
- Missing required fields must be explicit.
- `validate_required_fields` is a public support helper and must return a native validation result rather than a tool envelope.
- Unknown extra fields may be allowed or rejected based on supplied schema policy.
- Input/output schema validators must accept an optional `schema_version` and validate it against the supplied schema version when present.
- Version mismatches must return `VALIDATION_FAILED` with a clear compatibility message.
- Evidence validation must require source, timestamp, and evidence type.
- Approval packet validation must require action, reason, evidence, risk class, and approval status.
- Registry entry validation must require name, version, category/domain, risk level, and status.
- Risk-level validation must use the central `VALID_RISK_LEVELS` model.
- Environment validation must use the central `VALID_ENVIRONMENT_MODES` model unless a stricter caller-specific allowlist is provided.
- Blocked action validation must require an `action` field in the payload; if `payload["action"]` appears in `blocked_actions`, validation must fail closed.
- Freshness validation must require `payload["as_of"]` as an ISO timestamp unless the caller supplies a different explicit timestamp field.
- Freshness validation must support injected timestamps.
- `validate_artifact_reference` must require `artifact_id`, `version`, and one location field such as `storage_path`, `uri`, or `content_hash` depending on artifact type.

### Acceptance Criteria

- Valid payloads pass.
- Missing fields fail with `VALIDATION_FAILED` or `INVALID_INPUT` as appropriate.
- Blocked actions return an error response.
- Stale data returns a deterministic validation failure.
- Tool response schema is valid for every official validator.
- Tests verify `validate_numeric_range` and `validate_required_fields` return native validation results.
- Tests verify schema version compatibility and mismatch behavior.
- Tests verify blocked action payloads without `action` fail clearly.
- Tests verify freshness validation requires `as_of` and compares against injected current time.
- Tests verify artifact references require identity, version, and location/hash fields.

---

## 9.11 `tools/utils/security.py`

### Purpose

Provide security helpers for redaction, secret detection, password hashing, encryption, decryption, and secret version selection.

### Public API

```python
MAX_REDACTION_DEPTH = 10

is_sensitive_key(key: str) -> bool
redact_scalar(value: Any, *, replacement: str = "***REDACTED***") -> Any
redact_text(text: str, *, replacement: str = "***REDACTED***") -> str
redact_mapping(
    mapping: Mapping[str, Any],
    *,
    replacement: str = "***REDACTED***",
    max_depth: int = MAX_REDACTION_DEPTH,
) -> dict[str, Any]
hash_password(password: str) -> str
verify_password(password: str, hashed_password: str) -> bool
get_encryption_key(source: str | None = None) -> bytes
encrypt_data(data: str | bytes, key: bytes | None = None) -> str
decrypt_data(token: str, key: bytes | None = None) -> str
select_active_secret_version(secrets: Sequence[Mapping[str, Any]]) -> Mapping[str, Any]
```

### Requirements

- Secret-like keys must be detected case-insensitively.
- Redaction must preserve non-sensitive fields.
- Redaction must handle nested dictionaries and lists.
- Redaction must stop safely at a configured max depth and clearly mark truncated structures.
- Redaction must be applied before sensitive values appear in logs, error responses, metadata, remediation text, or canonical JSON payloads.
- Password hashing must use a production-safe algorithm available in project dependencies.
- Password verification must use constant-time comparison where relevant.
- Encryption key loading must never log key material.
- Phase 1 encryption must use `cryptography.fernet.Fernet` when the optional `cryptography` dependency is installed.
- `HARUQUANT_ENCRYPTION_KEY` must be a 32-byte URL-safe base64-encoded Fernet key when environment-based key loading is used.
- Encryption/decryption failures must not expose plaintext or key material.
- Secret version selection must be deterministic: select the item with `is_active=True` and the highest numeric `version`; if none exists, raise `HaruQuantSecurityError` or return a structured `SECRET_VERSION_NOT_FOUND` error at the tool boundary.

### Sensitive Key Patterns

At minimum, redact keys containing:

```text
password
passwd
secret
token
api_key
apikey
access_key
private_key
authorization
auth
credential
login
```

### Acceptance Criteria

- Redaction catches common sensitive keys.
- Redaction does not mutate input mappings.
- Password hash verification succeeds for correct passwords and fails for wrong ones.
- Encryption/decryption round trip works.
- Invalid encryption input fails safely.
- Missing or malformed encryption keys fail with `CONFIGURATION_ERROR` or `HaruQuantConfigurationError` without leaking key material.
- Secret selection tests cover active/highest-version selection, no active version, malformed version, and duplicate active versions.
- Tests confirm no secrets appear in logs or error strings.
- Security regression tests must include nested mappings, lists, string payloads, exception messages, metadata, and returned error details.

---

## 9.12 `tools/utils/settings.py`

### Purpose

Provide runtime settings loading and injection helpers for HaruQuant modules.

### Public API

```python
@dataclass(frozen=True)
class RuntimeSettings:
    environment: str
    log_level: str
    data_dir: Path
    cache_dir: Path
    audit_dir: Path
    timezone: str
    strict_validation: bool

load_runtime_settings(*, env_file: str | Path | None = None) -> RuntimeSettings
load_runtime_settings_from_mapping(mapping: Mapping[str, Any]) -> RuntimeSettings
inject_runtime_settings(settings: RuntimeSettings, target: MutableMapping[str, Any]) -> MutableMapping[str, Any]
```

### Requirements

- Settings must be typed.
- Required settings must have deterministic defaults where safe.
- Sensitive values must not be logged.
- Environment names should be validated.
- Path settings should use `Path` objects.
- `.env` loading must be optional and dependency-aware.
- Settings source precedence must be deterministic: explicit mapping/function arguments > environment variables > `.env` file > safe defaults.
- Importing `tools.utils` must not read `.env`; settings are loaded only when an explicit settings loader is called.
- Optional dependencies must be detected at runtime and fail with `HaruQuantConfigurationError` or `CONFIGURATION_ERROR` when the requested feature requires a missing dependency.
- Importing `tools.utils` must not fail just because an optional dependency is missing.
- Invalid settings must fail clearly with configuration errors.
- `strict_validation=True` means non-critical validation warnings should be escalated to failures where the caller asks settings to enforce strict behavior.
- `strict_validation=False` allows warnings to be returned or logged without failing the settings load.
- `inject_runtime_settings` is intended for explicit runtime contexts such as FastAPI `app.state`, workflow context dictionaries, or CLI runtime dictionaries. It must not mutate unrelated global state.

### Recommended Environment Modes

```text
local
development
test
staging
production
```

### Acceptance Criteria

- Valid mappings produce `RuntimeSettings`.
- Missing optional settings use defaults.
- Invalid environment mode fails.
- Path settings normalize safely.
- Sensitive values are redacted before logging.
- Tests verify `strict_validation` behavior is preserved from mappings and defaults.
- Tests verify `inject_runtime_settings` mutates only the provided target mapping and returns that mapping.

---


## 10. Cross-Cutting Functional Requirements

These requirements apply across the whole `tools/utils/` module and must be treated as part of the implementation contract.

### 10.1 Traceability Helpers

Utilities must provide standard helpers for request and workflow trace identifiers.

Required functions:

```python
generate_request_id(prefix: str = "req") -> str
generate_workflow_id(prefix: str = "wf") -> str
validate_request_id(request_id: str) -> bool
validate_workflow_id(workflow_id: str) -> bool
```

Rules:

- IDs must be safe for logs, filenames where practical, audit records, and tool metadata.
- IDs must not contain secrets or user-provided raw text.
- Request and workflow IDs must be usable across tools, agents, policy checks, audit logs, and final responses.
- Validators must be deterministic and side-effect free.

### 10.2 Shared Constants and Domain Models

The module must centralize common enum-like values to prevent drift across HaruQuant.

Required constants:

```python
VALID_SEVERITIES = {"info", "warning", "error", "critical"}
VALID_TOOL_STATUSES = {"success", "error"}
VALID_AGENT_STATUSES = {
    "success",
    "error",
    "blocked",
    "needs_approval",
    "needs_clarification",
}
VALID_ENVIRONMENT_MODES = {"local", "development", "test", "staging", "production"}
VALID_RISK_LEVELS = {"low", "medium", "high", "critical"}
DEFAULT_TIMEZONE = "UTC"
MAX_REDACTION_DEPTH = 10
```

Rules:

- Severity, status, risk-level, and environment-mode validation must use these constants unless a stricter caller-specific allowlist is provided.
- Constants must be immutable in practice and must not be mutated at runtime.
- Public functions that accept these values must validate them explicitly.

### 10.3 Canonical JSON Serialization

The module must support deterministic JSON serialization for audit hashing, cache keys, reproducible tests, and tool response comparisons.

Required function:

```python
to_canonical_json(payload: Mapping[str, Any]) -> str
```

Rules:

- Keys must be sorted.
- Datetimes must be normalized deterministically.
- Unsupported objects must fail clearly.
- Sensitive values must be redacted before serialization when configured.
- Output must be stable across repeated runs for equivalent payloads.

### 10.4 Numeric Range Validation

The module must provide reusable numeric validation for risk values, prices, volumes, spreads, thresholds, scores, and allocation limits.

Required function:

```python
validate_numeric_range(
    value: Any,
    *,
    name: str,
    min_value: float | None = None,
    max_value: float | None = None,
    allow_none: bool = False,
) -> dict[str, Any]
```

Rules:

- Non-numeric values must fail with deterministic validation details.
- `NaN`, positive infinity, and negative infinity must be rejected unless explicitly allowed by a future specialized function.
- Bounds must be inclusive unless documented otherwise.
- Error messages must include the logical field name, not just the raw value.

### 10.5 Timezone Policy

Utilities must be UTC-first.

Rules:

- `DEFAULT_TIMEZONE` must be `"UTC"`.
- No helper may use the local machine timezone implicitly.
- Datetime outputs must be UTC-aware or explicitly documented as naive UTC.
- Time-dependent helpers must support injected `now` or clock values where practical.

### 10.6 Audit-Safe Error and Metadata Redaction

Redaction applies to more than logs.

Rules:

- Sensitive values must not appear in logs, error responses, metadata, remediation messages, canonical JSON, or exception text exposed to callers.
- Redaction must handle nested mappings, lists, and string payloads.
- Redaction must stop at `MAX_REDACTION_DEPTH` and mark truncated structures safely.
- Security regression tests must prove that common secret patterns do not leak.

### 10.7 Settings Source Precedence

Runtime settings must load deterministically.

Precedence:

```text
explicit mapping/function arguments > environment variables > .env file > safe defaults
```

Rules:

- Importing `tools.utils` must not load settings automatically.
- `.env` loading must only happen when a settings loader is called explicitly.
- Sensitive values must not be logged.
- Optional dependency absence must not break module import.

### 10.8 Bounded Diagnostics

Validation tools must keep responses bounded and agent-friendly.

Rules:

- Data-quality tools must not return thousands of raw bad rows.
- Issue samples must be bounded by `max_issue_samples`.
- Issue list length must be bounded by `max_issues_returned`.
- Summary counts must preserve diagnostic value even when samples are truncated.

### 10.9 Deterministic OHLCV Quality Score

OHLCV quality scoring must be deterministic and documented.

Default penalty model:

```text
critical issue = -40 points
error issue    = -20 points
warning issue  = -5 points
info issue     = -1 point
minimum score  = 0
maximum score  = 100
```

Rules:

- Severity aggregation must be deterministic.
- Score calculation must be covered by tests.
- The response must explain score drivers through summary counts and issue categories.

### 10.10 No Financial Decisions in Utilities

Utilities may validate, normalize, redact, serialize, and report issues.

Utilities must not:

- approve or reject trades
- recommend allocations
- decide strategy promotion
- approve risk changes
- place, close, modify, or cancel orders
- activate live systems
- override kill switches

Any module that needs such decisions must call the appropriate risk, portfolio, execution, strategy, or governance domain.

---

### 10.11 Standard Execution Timing

Official AI Tools must measure execution time consistently using `get_execution_ms(start_time)` from `standard.py`.

Requirements:

- Use `time.perf_counter()` or an equivalent monotonic timer.
- Return milliseconds rounded consistently to three decimals.
- Include `execution_ms` in every official AI Tool metadata block.
- Do not hand-roll timing logic differently in each tool.
- Tests should mock or control start values where practical.

### 10.12 Schema Versioning for Validation Contracts

Official schema validators must support optional schema version checks.

Requirements:

- Schemas may declare `schema_version`.
- Payloads may declare `schema_version`.
- Callers may pass `schema_version` explicitly to enforce a required version.
- Mismatched versions must fail with `VALIDATION_FAILED`.
- Missing versions may be allowed only when the caller does not require strict versioning.

### 10.13 Resource Limits for Validation Workloads

Validation tools must include bounded resource behavior for large payloads.

Requirements:

- Data-quality validation must limit returned issue counts and samples.
- Validation helpers must avoid returning large raw payloads in errors.
- Expensive validators should accept optional limits such as `max_rows`, `max_issue_samples`, or `max_issues_returned` where appropriate.
- If a configured limit is exceeded, the response must clearly indicate truncation or partial diagnostics.
- Utilities must not implement global rate limiting, but they must expose enough limit parameters for callers to enforce workload controls.

## 11. Cross-Cutting Non-Functional Requirements

### 11.1 Import-Time Performance

Importing `tools.utils` must be lightweight.

Rules:

- Do not import pandas, cryptography, dotenv, broker SDKs, network clients, or other heavy optional dependencies from `tools/utils/__init__.py` unless absolutely necessary.
- Heavy dependencies should be imported inside the specific submodule/function that needs them.
- Dataframe helpers must use lazy pandas imports or `TYPE_CHECKING` guards so that importing `tools.utils` does not load pandas unless a dataframe function is actually called.
- Importing `tools.utils` must be safe in tests, CLI scripts, FastAPI startup, and agent runtime initialization.

### 11.2 Import Side-Effect Rule

Importing any `tools.utils` module must not:

- create files or directories
- read `.env` files
- configure global logging handlers unexpectedly
- open network connections
- initialize broker clients
- mutate environment variables
- run validation jobs
- execute expensive dataframe operations

### 11.3 Thread-Safety and Shared State

Utility functions must be safe for concurrent use unless explicitly documented otherwise.

Rules:

- Avoid mutable module-level state.
- Immutable constants and logger objects are allowed.
- Functions must not mutate caller-owned inputs unless documented in the function name and docstring.
- Shared caches are not allowed in v8 unless explicitly specified and tested.

### 11.4 Deterministic Test Mode

Time-dependent, ID-dependent, and randomness-dependent helpers must support deterministic testing where practical.

Examples:

- `is_stale(..., now=...)`
- ID helper prefixes
- optional clock injection for timestamp generation
- deterministic canonical JSON output

### 11.5 Forward API Governance

There is no backward compatibility requirement for old code. However, once v8 is implemented and accepted, the new public API must be governed.

Rules:

- Public exports may not be renamed or removed without a new versioned specification and registry review.
- New public exports must be justified by real cross-domain reuse.
- Internal helpers should remain internal until multiple modules need them.

### 11.6 Constants, Enums, and Canonical Strings

Public tool responses, metadata, audit records, and schema-validation outputs must use JSON-safe canonical strings.

Internal implementation may use `Enum` classes for stronger type safety, but any enum input must be normalized immediately to its canonical string value before being placed into:

- tool response metadata
- validation results
- audit records
- log records
- serialized JSON
- public return payloads

Validators for risk levels, severities, statuses, and environment modes must accept supported enum values and strings where practical, then return or store canonical strings. Invalid enum values must fail with `INVALID_INPUT` or a native validation failure depending on whether the caller is an official AI Tool or a support helper.

### 11.7 Optional Dependency Behavior

Optional dependencies must not break importability.

Rules:

- Missing optional dependencies must fail only when the relevant feature is used.
- The failure must be explicit and use `HaruQuantConfigurationError`, `CONFIGURATION_ERROR`, or the standard tool error envelope where applicable.
- Error messages must tell the developer which optional dependency is missing and which feature required it.

### 11.8 Memory and Response Size Safety

Utilities must be safe with large datasets.

Rules:

- Avoid unnecessary deep copies.
- Document copy/view/transformed-data behavior for dataframe helpers.
- Bound returned samples and issue lists.
- Avoid returning whole dataframes through official AI Tool envelopes.
- Prefer summaries, counts, and compact samples for agent-facing tool output.

---

## 12. Implementation Priority Order

Implementation must proceed in this order to avoid circular dependencies and unstable foundations:

| Priority | File | Reason |
|---:|---|---|
| 1 | `tools/__init__.py` | Makes `tools` a clean package. |
| 2 | `tools/utils/logger.py` | Required by every production file. |
| 3 | `tools/utils/standard.py` | Required by official AI Tools. |
| 4 | `tools/utils/errors.py` | Required for deterministic failure behavior. |
| 5 | `tools/utils/identity.py` | Required for request/workflow trace helpers. |
| 6 | `tools/utils/normalization.py` | Required by data quality, settings, freshness checks. |
| 7 | `tools/utils/paths.py` | Required by settings and artifact helpers. |
| 8 | `tools/utils/security.py` | Required by logging, settings, audit-safe behavior. |
| 9 | `tools/utils/settings.py` | Depends on paths/security/errors. |
| 10 | `tools/utils/dataframe_tools.py` | Depends on normalization/errors. |
| 11 | `tools/utils/schema_validation.py` | Depends on standard/errors/normalization/security. |
| 12 | `tools/utils/data_quality.py` | Depends on standard/errors/normalization/dataframe_tools. |
| 13 | `tools/utils/__init__.py` | Final registry after modules exist. |
| 14 | Unit tests | Required for production acceptance. |
| 15 | Usage examples | Required for official tools. |
| 16 | CI quality gates | Required before implementation is accepted. |

---

## 13. Logging Standard

Every production file must include:

```python
from tools.utils import logger
```

or, inside the utility module where importing from the registry could create circular imports:

```python
from tools.utils.logger import logger
```

Log these events where applicable:

- function/tool called
- validation failure
- successful completion
- recoverable warning
- execution failure

Never log:

- passwords
- API keys
- broker login credentials
- encryption keys
- tokens
- raw private payloads
- full approval packets containing sensitive content

---

## 14. Error Handling Standard

### 12.1 Support Helpers

Support helpers may raise typed HaruQuant exceptions for programmer or validation errors.

Examples:

- `HaruQuantValidationError`
- `HaruQuantConfigurationError`
- `HaruQuantSecurityError`
- `HaruQuantDataError`

### 12.2 Official AI Tools

Official AI Tools must not raise expected validation errors to the caller. They must return standard error envelopes.

Expected validation failure:

```python
{
    "status": "error",
    "message": "Invalid input.",
    "data": None,
    "error": {
        "code": "INVALID_INPUT",
        "details": "data must be a pandas DataFrame.",
    },
    "metadata": {...},
}
```

Unexpected execution failure:

```python
{
    "status": "error",
    "message": "Tool execution failed.",
    "data": None,
    "error": {
        "code": "TOOL_EXECUTION_FAILED",
        "details": "Unexpected validation failure while checking OHLCV data.",
    },
    "metadata": {...},
}
```

Raw exception objects must never be returned in `data` or `error`.

---

## 15. Type and Dependency Policy

### 13.1 Type Policy

- Use `from __future__ import annotations` in every Python file.
- Use built-in generics such as `dict[str, Any]`.
- Use `Mapping` for read-only mapping inputs.
- Use `MutableMapping` only when mutation is intended.
- Use `Path` for filesystem paths.
- Use `datetime` with explicit timezone policy.
- Use pandas types behind `TYPE_CHECKING` if needed to reduce import friction.

### 13.2 Dependency Policy

Allowed dependencies:

- Python standard library
- pandas for dataframe/data-quality modules
- optional `python-dotenv` for `.env` loading if already part of project dependencies
- optional cryptography/password hashing libraries if included in project dependencies

Disallowed utility-level dependencies:

- broker SDKs
- MT5 runtime
- FastAPI application objects
- UI packages
- LLM/agent framework runtime objects
- database engines unless explicitly required by a future utility submodule

---

## 16. Testing Specification

### 14.1 Minimum Coverage

Coverage must be at least 80% for the utilities module.

Target:

```text
line coverage >= 80%
branch coverage should be meaningful for validators and security helpers
```

### 14.2 Unit Test Matrix

| File | Test File | Required Coverage |
|---|---|---|
| `tools/utils/__init__.py` | `test_utils_registry.py` | public exports, no accidental exports, logger exception, official tool classification |
| `logger.py` | `test_logger.py` | import, configuration, duplicate handler prevention, no secret output in formatter tests |
| `standard.py` | `test_standard.py` | success envelope, error envelope, metadata, invalid schema, missing keys, execution timing helper, required schema constants, error code validation |
| `errors.py` | `test_errors.py` | exception attributes, known codes, unknown codes, fallback messages |
| `identity.py` | `test_identity.py` | ID uniqueness, prefix validation, version defaulting |
| `normalization.py` | `test_normalization.py` | ISO parsing, naive timezone assumption, UTC conversion, stale checks |
| `paths.py` | `test_paths.py` | safe normalization, unsafe traversal, directory creation, parent creation |
| `dataframe_tools.py` | `test_dataframe_tools.py` | alignment, serialization, UTC timestamp output, comparison, index mismatch behavior, missing columns, chunk size validation, no input mutation |
| `data_quality.py` | `test_data_quality.py` | clean OHLCV, missing columns, extra columns, symbol mismatch, timeframe mismatch, duplicates, gaps, bad OHLC, zero/negative values, spread, volume, spikes, flatlines, truncation limits, schema compliance |
| `schema_validation.py` | `test_schema_validation.py` | native helper results, required fields, input/output schema, schema versioning, handoff, evidence, approval, registry, blocked actions, freshness, artifact references |
| `security.py` | `test_security.py` | redaction, nested redaction, password hashing, verification, Fernet key behavior, encryption round trip, invalid token, secret selection, SECRET_VERSION_NOT_FOUND behavior |
| `settings.py` | `test_settings.py` | defaults, mapping load, invalid environment, strict_validation, path normalization, injection |

### 14.3 Usage Example Matrix

| Usage File | Demonstrates |
|---|---|
| `tests/usage/tools/utils/standard.py` | Creating success/error responses and validating envelope schema. |
| `tests/usage/tools/utils/data_quality.py` | Running `validate_ohlcv_quality` on a small OHLCV dataframe. |
| `tests/usage/tools/utils/schema_validation.py` | Validating input/output/evidence payloads. |
| `tests/usage/tools/utils/security.py` | Redacting sensitive mappings and verifying passwords. |
| `tests/usage/tools/utils/settings.py` | Loading runtime settings and consuming typed settings. |

### 14.4 Required Test Categories

Every official AI Tool must test:

- successful call
- invalid input
- standard return schema compliance
- metadata correctness
- request_id propagation
- execution_ms existence
- deterministic error code
- logging footprint where practical
- no secret leakage where relevant

---

## 17. CI Quality Gates

The following commands must pass before the module is accepted:

```bash
black tools tests
isort tools tests
flake8 tools tests
mypy tools tests
pytest tests/unit/tools/utils tests/usage/tools/utils --cov=tools.utils --cov-fail-under=80
```

Recommended full-project gate:

```bash
black .
isort .
flake8 .
mypy tools tests
pytest --cov=tools --cov-fail-under=80
```

---

## 18. Usage Rules for Other Modules

### 16.1 Preferred Imports

Other HaruQuant modules should import public utilities from the domain registry:

```python
from tools.utils import logger
from tools.utils import validate_ohlcv_quality
from tools.utils import build_success_response
```

### 16.2 Internal Imports Inside `tools/utils/`

Files inside `tools/utils/` may import directly from sibling modules to avoid circular registry imports:

```python
from tools.utils.standard import build_error_response
from tools.utils.logger import logger
```

### 16.3 Agent Usage

Agents may call only official AI Tools through approved tool attachment.

Recommended agent-callable utilities:

```python
from tools.utils import validate_ohlcv_quality
from tools.utils import validate_input_schema
from tools.utils import validate_output_schema
from tools.utils import validate_evidence_pack
```

Agents should not call low-level helpers such as `normalize_timestamp`, `ensure_dir`, or `hash_password` unless a workflow explicitly approves that capability.

---

## 19. Security and Safety Requirements

The utilities module must enforce safe behavior because it is used across the full HaruQuant application.

Required security controls:

1. Sensitive values must be redacted before logging.
2. Encryption keys must never be logged.
3. Password hashes must never be treated as plaintext.
4. Approval packets must not leak secrets through error messages.
5. Path helpers must defend against unsafe traversal where a base directory is supplied.
6. Official AI Tools must declare side effects correctly.
7. Side-effecting utilities must not be attached to agents without explicit approval.
8. Validation tools must fail closed when blocked actions are detected.
9. Unknown environment modes must fail validation.
10. Invalid freshness evidence must be surfaced, not ignored.

---

## 20. Performance Requirements

The utilities module should prioritize correctness and clarity, but basic performance discipline is required.

### 18.1 Data Quality

`validate_ohlcv_quality` should handle:

- 1,000 rows quickly for normal agent workflows
- 100,000 rows within a practical local validation budget
- large datasets without unnecessary deep copies

### 18.2 Dataframe Helpers

Dataframe helpers must:

- avoid repeated full-dataframe scans when possible
- avoid mutating caller-owned data
- keep serialization explicit and bounded

### 18.3 Security Helpers

Security helpers must:

- avoid expensive redaction recursion loops
- handle nested structures with recursion depth protection
- avoid logging sensitive payloads during failure

---

## 21. Documentation Requirements

Every Python file must start with a file-level docstring containing:

- purpose
- whether the file contains official AI Tools or support helpers
- exported public functions/classes
- side effects, if any

Every public function must document:

- what it does
- when to use it
- arguments
- return value
- raised exceptions or structured error behavior
- side effects, if any

Official AI Tool docstrings must be agent-facing and explain:

- when an agent should use the tool
- what evidence the tool produces
- what the tool does not do
- what error codes may be returned

---

## 22. Implementation Acceptance Criteria

The v8 utilities module is production-ready only when all items below are complete.

### 20.1 Structure

- [ ] Target folder structure exists.
- [ ] `tools/__init__.py` exists and is side-effect free.
- [ ] `tools/utils/__init__.py` exposes only approved public names.
- [ ] Internal helpers are not accidentally exported.
- [ ] No compatibility shims, aliases, fallback import modules, or duplicate wrapper modules exist.

### 20.2 Code Quality

- [ ] Every Python file has a file-level docstring.
- [ ] Every public function/class has a useful docstring.
- [ ] Public functions and methods are typed.
- [ ] Inputs are validated where appropriate.
- [ ] Errors are explicit and deterministic.
- [ ] Official tools return standard envelopes.
- [ ] Support helpers return clear native values or raise typed exceptions.
- [ ] No production `print()` calls exist.
- [ ] No secrets are logged.

### 20.3 Tool Compliance

- [ ] Official tools include metadata constants.
- [ ] Official tools include side-effect flags.
- [ ] Official tools accept `request_id`.
- [ ] Official tools include `execution_ms`.
- [ ] Official tools use deterministic error codes.
- [ ] Official tools pass `validate_tool_response_schema`.

### 20.4 Testing

- [ ] Unit tests exist for every module.
- [ ] Official tools have schema compliance tests.
- [ ] Official tools have metadata tests.
- [ ] Invalid input tests exist.
- [ ] Edge case tests exist.
- [ ] Security tests verify redaction and no secret leakage.
- [ ] Data quality tests cover realistic OHLCV defects.
- [ ] Coverage is at least 80%.

### 20.5 Usage Examples

- [ ] Usage examples exist for official AI Tools.
- [ ] Usage examples use realistic inputs.
- [ ] Usage examples show success and error handling.
- [ ] Usage examples use `request_id` where applicable.

### 20.6 CI

- [ ] Black passes.
- [ ] isort passes.
- [ ] Flake8 passes.
- [ ] mypy passes.
- [ ] pytest passes.
- [ ] coverage gate passes.

---


### 20.7 v6 Final Clarification Acceptance Criteria

- `standard.py` exposes and tests `get_execution_ms`.
- `TOOL_RESPONSE_REQUIRED_KEYS`, `TOOL_RESPONSE_METADATA_REQUIRED_KEYS`, and `VALID_ERROR_CODES` are defined and used by response validation.
- `logger`, `get_logger`, and `configure_logging` are public support helpers, not official AI Tools.
- `validate_numeric_range` and `validate_required_fields` return native validation results and are wrapped by official tools where needed.
- `validate_ohlcv_quality` validates symbol/timeframe expectations where possible.
- `validate_ohlcv_quality` handles extra columns without failing unless they create ambiguity.
- `serialize_dataframe_records` emits UTC ISO timestamp strings with `Z`.
- `compare_dataframes` defines deterministic index alignment behavior.
- `chunked(size <= 0)` fails clearly.
- `select_active_secret_version` uses active/highest-version deterministic selection and supports `SECRET_VERSION_NOT_FOUND`.
- `RuntimeSettings.strict_validation` behavior is documented and tested.
- Schema validators support optional `schema_version` checks.
- Validation tools expose bounded diagnostics/resource-limit behavior.
- Security tests cover key material, encrypted/decrypted payloads, nested redaction, and error/metadata leakage.

### 20.8 v8 Final Polish Acceptance Criteria

- Importing `tools.utils` does not import pandas, cryptography, dotenv, broker SDKs, or network clients unless the specific feature is used.
- `dataframe_tools.py` uses lazy pandas imports or `TYPE_CHECKING` guards.
- Missing pandas fails only when dataframe helpers are called, with a clear configuration/dependency error.
- `validate_ohlcv_quality` is stateless, diagnostic-only, and does not repair, resample, persist, enrich, or mutate input data.
- Data repair and cleaning workflows are explicitly excluded from `tools.utils` and reserved for `tools.data`.
- Validators accept supported enum values and strings where practical, then normalize to canonical JSON-safe strings.
- Public responses, metadata, audit records, logs, and serialized payloads never expose enum objects directly.
- Future domain-specific errors inherit from `HaruQuantError` or expose a compatible `code` attribute.
- `standard.py` response builders can map `HaruQuantError` subclasses generically without hardcoding every future domain error.

## 23. Definition of Done

The utilities module is done when:

1. It imports cleanly from a fresh environment.
2. `from tools.utils import logger` works.
3. `from tools.utils import validate_ohlcv_quality` works.
4. The public registry contains only approved names.
5. Official AI Tools return the standard HaruQuant envelope.
6. Support helpers are typed, documented, and deterministic.
7. Data quality validation provides actionable issues and remediation.
8. Schema validation supports agent/workflow contracts.
9. Security helpers redact and protect sensitive values.
10. Settings helpers load typed runtime configuration safely.
11. Unit tests and usage examples are present.
12. Quality gates pass.
13. The implementation is clear, maintainable, and free of unnecessary abstraction.

---

## 24. Final Implementation Guidance

Build the module in small slices.

Recommended sequence:

```text
logger -> standard -> errors -> identity -> normalization -> paths -> security -> settings -> dataframe_tools -> schema_validation -> data_quality -> registry -> tests -> usage examples -> CI
```

Keep the design simple.

Use official AI Tool envelopes only where they add value for agent/workflow calls. Keep low-level helpers native and clean. The result should feel like a professional shared library that higher-level HaruQuant domains can trust.

The final implementation must be fresh, coherent, and production-grade.

# Utils — Version 1 Code Audit

## 1. Audit Scope

* **Domain:** `utils`
* **Repository:** `haruperi/HaruQuant`
* **Repository branch / inspected revision:** `main` / `a39d26498e14772c571d75fa9a5f0e477a1dd912`
* **Package path:** `app/services/utils`
* **Tests path supplied:** `ttests/unit/app/services/utils`
* **Tests path found:** `tests/unit/app/services/utils`
* **Usage example found:** `tests/usage/app/services/01_utils.py`
* **Files inspected:** 17 Python files plus `app/services/utils/README.md`
* **Related packages searched:** `app/api`, `app/services`, `data`, `scripts`, `tests`, and repository documentation
* **Audit limitations:**
  * GitHub repository content and indexed code search were available.
  * A complete local checkout could not be obtained because the execution sandbox could not resolve `github.com`; therefore tests, coverage, imports, and runtime workflows were not executed.
  * Static searches covered imports, direct calls, decorators, dynamic module loaders, tests, examples, and documented registries. Reflection, environment-driven entry points, and unindexed string-based imports cannot be completely ruled out.
  * Usage classifications are conservative. An item is not labelled dead code unless the evidence is strong enough; most no-caller findings are labelled **Test-only**, **Possibly used**, or **Questionable**.

## 2. Executive Summary

The Version 1 `utils` package is not a narrow helper library. It currently provides:

* structured logging and file sinks;
* a central error-code and exception catalogue;
* standard tool-response envelopes;
* path and datetime normalization;
* application, broker, live-runtime, and research configuration;
* password hashing, encryption, and secret redaction;
* dataframe manipulation, caching, comparison, and parameter expansion;
* OHLCV validation and data-quality diagnostics;
* schema and policy-packet validation;
* authorization primitives;
* an in-memory event bus;
* in-memory metrics, health snapshots, and a circuit breaker.

The most operationally important confirmed workflows are structured logging, password hashing/verification, safe path normalization, shared settings construction, standard response creation, and dataframe caching used by the data service. Several other capabilities are implemented and tested but have no confirmed production caller, notably the authorization layer, local event bus, circuit breaker/metrics registry, and the newer data-quality facade.

The most important structural problems are:

1. **The public registry advertises names that do not exist.** Its fallback returns the whole module rather than raising `AttributeError`, masking broken exports until later runtime use.
2. **Logging has import-time filesystem side effects.** Importing `app.services.utils.logger` creates `data/logs`, opens four files, and installs sinks.
3. **The package contains overlapping implementations** for paths, dataframe utilities, schema validation, OHLCV validation, redaction, response envelopes, and canonical serialization.
4. **Return contracts are inconsistent.** Public functions variously return native values, standard dictionaries, subclasses that act as both native values and mappings, or raise typed exceptions.
5. **Cross-domain responsibilities leak into utils.** `errors.py` owns error taxonomies for indicator, strategy, trading, risk, simulation, and live domains; `settings.py` owns research models; `normalization.py` owns board/execution freshness policy.
6. **Documentation and tests are stale or incomplete.** The registry test requires `NotificationRouter`, which is absent from `__all__`; the usage script demonstrates schema constraints the implementation does not enforce.

**Evidence trustworthiness:** High for file existence, implementation details, declared exports, direct imports, and direct calls. Medium for “no runtime caller” conclusions because runtime execution and every possible dynamic configuration path could not be exercised.

```text
Module folders: 0 | Files: 18 | Declared package exports: 195 | Exports with confirmed non-test callers: 44 (22.6%, conservative) | Workflows found: 9
```

The confirmed-caller metric counts only package exports for which a non-test call/import was directly found during this audit. It deliberately excludes internal-only calls and uncertain dynamic resolution.

## 3. Actual Package Structure

```text
app/services/utils
├── __init__.py
│   ├── _EXPORTS
│   ├── __all__
│   └── __getattr__()
├── auth.py
│   ├── AuthContext
│   ├── AuthorizationDecision
│   ├── build_auth_context()
│   ├── authorize_action()
│   ├── require_authorization()
│   └── validate_auth_context()
├── common.py
│   ├── Param
│   ├── HQTAccessor
│   ├── HQTSeriesAccessor
│   ├── combine_params()
│   ├── merge()
│   ├── concat()
│   ├── rolling_mean()
│   ├── chunked()
│   ├── serialize_dataframe_records()
│   ├── bars_to_records()
│   ├── clear_dataframe_cache()
│   ├── get_cached_dataframe()
│   ├── tool_result_envelope()
│   ├── align_dataframes_by_datetime()
│   ├── compare_dataframes()
│   ├── compare_ohlc()
│   └── compare_ohlcv()
├── data_quality.py
│   ├── QualityIssue
│   ├── QualityProfile
│   ├── prepare_ohlcv_data()
│   ├── inspect_ohlcv_quality()
│   └── validate_ohlcv_quality()
├── dataframe_tools.py
│   ├── align_dataframe_datetime()
│   ├── align_dataframe_time_index
│   ├── serialize_dataframe_records()
│   ├── bar_to_record()
│   ├── bars_to_records()
│   ├── chunked()
│   ├── chunk_sequence
│   ├── parameter_combinations()
│   ├── generate_parameter_combinations
│   ├── compare_dataframes()
│   ├── compare_ohlc()
│   ├── compare_ohlcv()
│   ├── dataframe_columns()
│   └── iter_dataframe_records()
├── errors.py
│   ├── APPROVED_ERROR_CODES / ERROR_MESSAGES
│   ├── ErrorPayload / error metadata types
│   ├── Error
│   ├── ValidationError
│   ├── ConfigurationError
│   ├── SecurityError
│   ├── DataError
│   ├── ExternalServiceError
│   ├── InfrastructureError
│   ├── TradingError and trading subclasses
│   ├── indicator-domain exception hierarchy
│   ├── strategy-domain exception hierarchy
│   ├── risk/simulation/live error codes
│   ├── normalize_error_code()
│   ├── message_for()
│   ├── error_name()
│   ├── code_for_exception()
│   ├── details_for_exception()
│   ├── exception_to_error_payload()
│   ├── validate_error_payload()
│   ├── raise_for_invalid_code()
│   ├── route_error()
│   ├── classify_broker_error()
│   └── trading_retry_delay()
├── event_bus.py
│   ├── EventEnvelope
│   ├── PublishResult
│   ├── InMemoryEventBus
│   │   ├── subscribe()
│   │   ├── unsubscribe()
│   │   ├── publish()
│   │   ├── queue_depth()
│   │   └── idempotency_size()
│   ├── build_event_envelope()
│   └── publish_event()
├── identity.py
│   ├── DEFAULT_VERSION / ID_PREFIXES
│   ├── generate_id()
│   ├── generate_prefixed_id()
│   ├── generate_request_id()
│   ├── generate_workflow_id()
│   ├── generate_correlation_id()
│   ├── generate_causation_id()
│   ├── generate_event_id()
│   ├── generate_idempotency_id()
│   ├── validate_id()
│   ├── validate_request_id()
│   ├── validate_workflow_id()
│   └── ensure_version()
├── logger.py
│   ├── TRACE / DEBUG / INFO / SUCCESS / WARNING / ERROR / CRITICAL
│   ├── DEFAULT_LEVELS
│   ├── CompatRecord
│   ├── StructlogAdapter / Logger
│   │   ├── add(), remove(), flush()
│   │   ├── set_min_level(), get_min_level()
│   │   ├── set_component_level(), clear_component_level()
│   │   ├── bind(), contextualize()
│   │   └── trace(), debug(), info(), success(), warning(), error(),
│   │       critical(), exception(), log()
│   ├── logger
│   ├── setup_logging()
│   ├── configure_logging()
│   ├── get_logger()
│   ├── get_child_logger()
│   ├── init_worker_logger()
│   └── configure_multiprocess_listener()
├── normalization.py
│   ├── Clock
│   ├── SystemClock
│   ├── FixedClock
│   ├── FreshnessWindow
│   ├── BoardBaselineArtifactWindow
│   ├── BoardBaselineFreshnessEvaluation
│   ├── PathResponse / DatetimeResponse / StringResponse / IntResponse
│   ├── normalize_path()
│   ├── ensure_dir()
│   ├── ensure_parent_dir()
│   ├── parse_datetime()
│   ├── to_utc()
│   ├── to_utc_datetime()
│   ├── to_naive_utc()
│   ├── format_utc_timestamp()
│   ├── format_timestamp_z()
│   ├── utc_now()
│   ├── normalize_timestamp()
│   ├── normalize_timezone_for_series()
│   ├── evaluate_freshness()
│   ├── evaluate_board_baseline_freshness()
│   └── is_stale()
├── observability.py
│   ├── GRAFANA_DASHBOARD_EXPECTATIONS
│   ├── MetricRecord
│   ├── HealthSnapshot
│   ├── MetricRegistry
│   │   ├── record()
│   │   └── export_prometheus_text()
│   ├── CircuitBreaker
│   │   ├── state
│   │   ├── consecutive_failures
│   │   ├── allow_request()
│   │   ├── record_success()
│   │   └── record_failure()
│   ├── record_metric()
│   ├── record_tool_call_metric()
│   ├── build_health_snapshot()
│   ├── check_clock_drift_health()
│   └── export_prometheus_metrics()
├── paths.py
│   ├── normalize_path()
│   ├── safe_join()
│   ├── validate_path_within_root()
│   ├── ensure_dir()
│   └── ensure_parent_dir()
├── schema_validation.py
│   ├── validate_required_fields()
│   ├── validate_input_schema()
│   ├── validate_output_schema()
│   ├── validate_handoff_payload()
│   ├── validate_evidence_pack()
│   ├── validate_approval_packet()
│   ├── validate_registry_entry()
│   ├── validate_blocked_actions()
│   ├── validate_numeric_range()
│   └── validate_data_freshness()
├── security.py
│   ├── REDACTED / SENSITIVE_KEYWORDS / SENSITIVE_KEY_PATTERN
│   ├── SecretRef
│   ├── SecretRotationPolicy
│   ├── StrKey
│   ├── is_sensitive_key()
│   ├── classify_secret_key()
│   ├── redact_scalar()
│   ├── redact_mapping_value()
│   ├── redact_mapping()
│   ├── redact_mapping_tool()
│   ├── redact_mapping_with_diagnostics()
│   ├── redact_payload()
│   ├── redact_text_value()
│   ├── redact_text()
│   ├── redact_text_tool()
│   ├── load_encryption_key()
│   ├── select_active_secret_version()
│   ├── hash_password()
│   ├── verify_password()
│   ├── get_encryption_key()
│   ├── generate_encryption_key()
│   ├── encrypt_value() / encrypt_text
│   ├── decrypt_value() / decrypt_text
│   ├── encrypt_data()
│   └── decrypt_data()
├── settings.py
│   ├── HARUQUANT_HOME / CONFIGURATION_ERROR
│   ├── EnvironmentMode / LiveMode
│   ├── Settings / Config
│   ├── get_settings()
│   ├── settings (lazy module attribute)
│   ├── load_config()
│   ├── validate_config()
│   ├── CleaningConfig
│   ├── DataConfig
│   ├── SessionConfig
│   ├── BootstrapConfig
│   ├── PermutationConfig
│   ├── NullModelsConfig
│   ├── MeanReversionConfig
│   ├── TrendPersistenceConfig
│   ├── MarketStructureConfig
│   ├── SessionEdgeConfig
│   ├── EdgeLabConfig
│   ├── create_config()
│   ├── TradeSample
│   ├── EdgeStats
│   ├── EdgeResult
│   └── research_modeling_module()
├── standard.py
│   ├── standard status/type constants
│   ├── StandardMetadata / ToolMetadata
│   ├── ToolError
│   ├── StandardResponse / StandardEnvelope
│   ├── DataQualityIssue
│   ├── ErrorEvent
│   ├── AlertDeduplicator
│   ├── ToolStandardSpec
│   ├── stable_identifier()
│   ├── get_execution_ms()
│   ├── build_data_quality_issue()
│   ├── validate_ohlcv_records()
│   ├── build_metadata()
│   ├── success_response() / build_success_response
│   ├── error_response() / build_error_response
│   ├── response_from_exception()
│   ├── circuit_open_response()
│   ├── validate_standard_response()
│   ├── validate_tool_response_schema()
│   ├── build_error_event()
│   ├── validate_metric_labels()
│   ├── is_official_tool_allowed()
│   ├── canonical_json()
│   ├── standard_tool_response()
│   ├── standardize_tool_callable()
│   └── standardize_domain_exports()
├── validators.py
│   ├── validation constants and profiles
│   ├── DataSource
│   ├── OHLCVSchema
│   ├── DataQualityReport
│   ├── validate_required_fields()
│   ├── validate_input_schema()
│   ├── validate_output_schema()
│   ├── validate_handoff_payload()
│   ├── validate_evidence_pack()
│   ├── validate_approval_packet()
│   ├── validate_environment_mode()
│   ├── validate_data_freshness()
│   ├── validate_artifact_reference()
│   ├── validate_registry_entry()
│   ├── validate_blocked_actions()
│   ├── prepare_ohlcv_data()
│   ├── get_session_ranges()
│   ├── compute_session_stats()
│   ├── validate_ohlcv_quality()
│   ├── validate_price_sanity()
│   ├── validate_gaps()
│   ├── validate_market_calendar_gaps()
│   ├── validate_numeric_integrity()
│   ├── validate_timezone_awareness()
│   ├── validate_duplicate_ohlc_rows()
│   ├── validate_flatlines()
│   ├── validate_spikes()
│   ├── validate_missing_timestamps()
│   ├── validate_zero_volume()
│   ├── validate_duplicates()
│   ├── validate_monotonic_timestamps()
│   ├── validate_spread()
│   ├── validate_high_low()
│   ├── validate_negative_prices()
│   ├── validate_price_in_range()
│   ├── validate_zero_prices()
│   ├── validate_find_column()
│   ├── validate_find_columns()
│   ├── validate_get_time_series()
│   ├── validate_issue_severity()
│   ├── validate_issue_remediation_action()
│   ├── validate_annotate_issues()
│   └── validate_remediation_summary()
└── README.md
```

## 4. Module and File Inventory

Files are arranged approximately from low-level contracts to higher-level utilities and facades.

| Module | File | Responsibility | Key exports | Dependencies | Usage status | Value status |
| ------ | ---- | -------------- | ----------- | ------------ | ------------ | ------------ |
| package registry | `__init__.py` | Lazy public export registry | 195 names, `__getattr__` | Standard library: `importlib`, `typing`; local modules loaded dynamically | Used widely | Essential but defective |
| logging | `logger.py` | Structlog-compatible logging, sinks, rotation, component levels, multiprocess queue | `logger`, `get_logger`, `configure_logging`, `StructlogAdapter` | Standard library: logging/threading/path/time; optional: `structlog`; local: `security` during emission | Used | Essential |
| errors | `errors.py` | Approved error registry, base exceptions, domain exceptions, mapping/routing | `Error`, typed exceptions, mapping helpers | Standard library; local: `security` for redaction | Used | Essential, structurally overloaded |
| tool contracts | `standard.py` | Standard envelopes, metadata, validation, deterministic serialization | `ToolStandardSpec`, response builders, validators | Standard library; local: `errors`, `logger` | Used | Essential |
| identity | `identity.py` | UUID-based identifiers and format validation | ID generators/validators, `ensure_version` | Standard library: `re`, `uuid`; local: errors/logger | Internal and test/example use; limited runtime evidence | Supporting |
| time/path normalization | `normalization.py` | Datetime, timezone, TTL, filesystem wrappers, board baseline policy | time/path/freshness APIs | Standard library; optional pandas; local errors/logger/standard | Used internally and cross-domain | Supporting, overloaded |
| safe filesystem paths | `paths.py` | Traversal-safe path resolution and explicit directory creation | `normalize_path`, `safe_join`, `ensure_*` | Standard library: `pathlib`; local errors/logger | Used | Essential |
| common compatibility layer | `common.py` | Parameter grids, Data wrappers, pandas accessors, cache, comparisons, chunk execution | `Param`, cache, merge/concat, comparisons | Standard library; required/optional: pandas, NumPy, Numba; local service discovery, data.frames, normalization, standard | Used by data; other surfaces mixed | Useful but high-risk overlap |
| dataframe helpers | `dataframe_tools.py` | Pure/lazy dataframe alignment, conversion, comparison, combinations | conversion/comparison functions | Standard library; lazy pandas; local errors/logger | Mostly test/example; some indirect use possible | Useful |
| schema validation | `schema_validation.py` | Lightweight schema and packet validation envelopes | ten validation functions | Standard library; local normalization/standard/logger | Used by risk and tests; overlap with validators | Useful |
| comprehensive validation | `validators.py` | Generic packets plus extensive OHLCV/session validation | validation classes and functions | Standard library; required pandas/NumPy; local normalization/standard/logger | Used selectively; many test/example-only | Useful but overloaded |
| focused data quality | `data_quality.py` | Focused OHLCV inspection/profile and official wrapper | `prepare`, `inspect`, `validate` | Standard library; required pandas/NumPy; local normalization/standard/logger | Example/test-only confirmed | Questionable current integration |
| security | `security.py` | Redaction, password hashing, encryption, key/version helpers | hashing, crypto, redaction | Standard library; optional cryptography/passlib/argon2/bcrypt; local errors/logger/standard | Partly used | Essential for auth; mixed elsewhere |
| settings | `settings.py` | Application settings, live config validation, research models | `Settings`, `get_settings`, research models | Standard library; required pydantic/pydantic-settings; local paths/errors/logger; dynamic research import | Used | Essential, overloaded |
| authorization | `auth.py` | Auth context and permission/scope decisions | context, decisions, validators | Standard library; local identity/errors/standard/logger | Test/example-only confirmed | Questionable current integration |
| event bus | `event_bus.py` | Caller-owned local in-memory pub/sub | event envelope, bus, publish helper | Standard library; local identity/time/security/errors/logger | Test/example-only confirmed | Questionable |
| observability | `observability.py` | In-memory metrics, health and circuit breaker | registry, breaker, health functions | Standard library; local standard/security/time/errors/logger | Test/example-only confirmed | Questionable |
| documentation | `README.md` | Describes package APIs and usage | None | None | Documentation only | Supporting but stale |

## 5. Public Behaviour Inventory

### `app/services/utils/__init__.py`

**File responsibility:** Define and lazily load the package-level public surface.

| Symbol | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
| ------ | ---- | -------------- | --------------- | ------------ | ------ | ------- | ----- | ------------ | ------------ |
| `_EXPORTS`, `__all__` | registry/constant | Declare 195 package exports | name → target module | None until access | None | All package-root importers | `test_utils_registry.py` | Used | Essential |
| `__getattr__(name)` | function | Import target module and resolve symbol | export name → object | Imports module; may trigger module side effects | `AttributeError` only for unknown registry key | Implicit package access | registry tests | Used | Essential but defective |
| Broken registry names | advertised exports | Names lacking a matching target attribute | access → **module object**, not requested symbol | Imports target module | Does not fail as expected | Any importer of affected name | Not adequately tested | Unused/invalid | No demonstrated value |

Confirmed mismatches include:

```text
errors.py: HaruError, BrokerError
identity.py: ensure_version_value, apply_version_update, StaleVersionError
paths.py: normalize_path_value, ensure_dir_value, ensure_parent_dir_value
dataframe_tools.py: align_dataframes_by_datetime
settings.py: RuntimeSettings, load_runtime_settings,
             load_runtime_settings_from_mapping, inject_runtime_settings
auth.py: AuthorizationResult, authorize_tool_call
event_bus.py: InProcessEventBus
observability.py: HealthCheckResult, health_snapshot
```

`__getattr__()` stores and returns the imported module when `hasattr(module, name)` is false. This is confirmed in `app/services/utils/__init__.py::__getattr__`.

### `app/services/utils/logger.py`

**File responsibility:** Logging adapter, redaction-aware dispatch, file rotation, and worker-process routing.

| Symbol | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
| ------ | ---- | -------------- | --------------- | ------------ | ------ | ------- | ----- | ------------ | ------------ |
| level constants, `DEFAULT_LEVELS` | constants | Shared logging level names | — | None | None | logger internals/tests | `test_logger.py` | Used internally | Supporting |
| `CompatRecord` | dataclass | Callback/file-sink record | fields → record | None | None | `StructlogAdapter` | `test_logger.py` | Used internally | Supporting |
| `StructlogAdapter` / `Logger` | class | Bind context, filter levels, emit, route sinks | log calls → `None` | Local state; file/callback writes; queue publication | Logging errors are swallowed | Broad runtime callers | `test_logger.py` | Used | Essential |
| sink/level/context methods | methods | Configure sinks and logging context | configuration → state | Local mutation/files | Mostly swallowed | runtime and tests | `test_logger.py` | Used | Essential/supporting |
| level methods | methods | Emit redacted records | message/args → `None` | Log/file writes | Suppresses internal failures | Nearly every domain | broad tests | Used | Essential |
| `logger` | singleton | Shared adapter | — | Constructing it configures structlog | None exposed | Broad runtime imports | tests | Used | Essential |
| `setup_logging`, `configure_logging` | functions | Ensure default sinks | options → `None` | Creates directories/files | Filesystem errors possible during setup | application setup/import | tests | Used | Useful |
| `get_logger`, `get_child_logger` | functions | Return bound adapter | component name → adapter | Local object creation | None | multiple services | tests | Used | Essential |
| `init_worker_logger`, `configure_multiprocess_listener` | functions | Route worker logs to main-process listener | queue → `None` | Global mutation/thread creation | Internal failures suppressed | No confirmed production call | tests/docs | Possibly used | Useful |

**Important evidence:** `_configure_default_file_sinks()` is called at module import. It creates `data/logs` and opens `app.log`, `debug.log`, `errors.log`, and `access.log`.

### `app/services/utils/errors.py`

**File responsibility:** Deterministic error codes, exception types, payload conversion, routing, and multiple domain-specific error hierarchies.

| Symbol group | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
| ------------ | ---- | -------------- | --------------- | ------------ | ------ | ------- | ----- | ------------ | ------------ |
| approved-code/message registries | constants | Canonical code lookup | code → metadata | None | None | all error helpers | `test_errors.py` | Used | Essential |
| `ErrorPayload`, descriptor/context/envelope/result types | TypedDict/dataclasses | Typed error structures | fields → object | None | validation on construction where applicable | error routing, infrastructure code | tests | Used | Supporting |
| `Error` | exception class | Base deterministic coded error | message/options → exception | None | invalid severity | broad runtime | tests | Used | Essential |
| `ValidationError`, `ConfigurationError`, `SecurityError`, `DataError`, `ExternalServiceError`, `InfrastructureError` | exception classes | Typed failure categories | message/context → exception | None | construction validation | broad runtime | tests | Used | Essential |
| `DomainError`, `PolicyError` | aliases | Compatibility aliases to `Error` | — | None | None | unclear | tests/docs | Possibly used | Questionable |
| trading/broker classifiers and retry delay | classes/functions | Normalize broker retcodes and retry delay | error/attempt → metadata/delay | Random jitter | validation errors | trading/execution callers | tests | Used | Useful |
| indicator/strategy/risk/simulation/live error taxonomies | classes/constants | Domain-specific failures | message → typed exception | None | — | domain packages | domain tests | Used | Useful, misplaced |
| normalization/lookup helpers | functions | Normalize codes and map exceptions | code/exception → code/message/payload | None | strict helper can raise | broad runtime and standard.py | tests/examples | Used | Essential |
| `route_error` | function | Build route decision for errors | exception/source → result | None/logging | validation errors | examples/tests; some runtime search hits uncertain | tests | Possibly used | Useful |

The package registry advertises `HaruError` and `BrokerError`, but no matching definitions or aliases were found in `errors.py`.

### `app/services/utils/standard.py`

**File responsibility:** Standard response envelope and related deterministic support contracts.

| Symbol group | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
| ------------ | ---- | -------------- | --------------- | ------------ | ------ | ------- | ----- | ------------ | ------------ |
| status/type/constants | constants/type aliases | Contract vocabulary | — | None | None | utility tools | `test_standard.py` | Used | Supporting |
| `StandardMetadata`, `ToolMetadata`, `StandardResponse`, `StandardEnvelope`, `DataQualityIssue`, `ErrorEvent` | TypedDicts | Envelope schemas | fields → mapping | None | None | utilities/risk | tests | Used | Supporting |
| `ToolError` | exception | Tool-boundary failure | message/code → exception | None | — | no confirmed direct runtime caller | tests | Possibly used | Useful |
| `AlertDeduplicator.allow` | class/method | Bounded repeated-alert suppression | key/time → bool | Local state mutation | validation errors | tests only found | tests | Test-only | Questionable |
| `ToolStandardSpec` | dataclass | Tool metadata defaults | fields → spec | None | None | many utility wrappers | tests | Used | Essential |
| `build_metadata`, `get_execution_ms` | functions | Construct canonical metadata | flags/timing → metadata | None except logging | validation errors | risk validators and utilities | tests/examples | Used | Essential |
| `success_response`, `error_response`, aliases | functions | Build typed envelopes | message/data/error/metadata → mapping | Logging | validation errors | risk validators and utilities | tests/examples | Used | Essential |
| `standard_tool_response` | function | Older simpler envelope builder | spec/status/data → dict | Logging | no contract validation | most utility tools | tests | Used | Essential compatibility |
| `response_from_exception`, `circuit_open_response` | functions | Failure envelopes | exception/provider → response | Logging | validation errors | utilities/examples | tests | Used internally | Useful |
| `validate_standard_response`, `validate_tool_response_schema` | functions | Enforce/predicate envelope shape | mapping → None/bool | None except logging | `ValidationError` | tests/tools | tests | Used | Essential |
| `stable_identifier`, `canonical_json` | functions | Deterministic IDs/serialization | object → string | None except logging | validation errors | utility events/tests | tests/examples | Used | Useful |
| data-quality helpers | functions | Record-level OHLCV issue reporting | records → issue list | None except logging | validation errors | no confirmed production caller | tests | Test-only/possibly internal | Questionable overlap |
| `build_error_event`, `validate_metric_labels`, `is_official_tool_allowed` | functions | Error-event, metrics and tool-registry support | mappings/names → result | None except logging | validation/security errors | observability/internal/tests | tests | Internal/test | Useful |
| `standardize_tool_callable` | function | Advertised standardizer | callable → same callable | Logging only | None | no meaningful caller | tests/docs | Unused placeholder | No demonstrated value |
| `standardize_domain_exports` | function | Advertised namespace standardizer | namespace/list → `None` | Logging only | None | no meaningful caller | tests/docs | Unused placeholder | No demonstrated value |

### `app/services/utils/identity.py`

**File responsibility:** Generate and validate UUID-based IDs and normalize version strings.

| Symbol group | Responsibility | Inputs → Return | Side effects | Raises | Usage status | Value status |
| ------------ | -------------- | --------------- | ------------ | ------ | ------------ | ------------ |
| `generate_id`, `generate_prefixed_id`, specialized generators | UUID identifiers | prefix → string | Random UUID generation | `ValidationError` | Mostly test/example; `generate_event_id` used by event bus | Supporting |
| `validate_id`, request/workflow validators | Format validation | value/prefix → string | None | `ValidationError` | Internal/test | Supporting |
| `ensure_version` | Default/validate version string | version/default → string | None | `ValidationError` | Test/documentation evidence | Useful |
| nonexistent advertised version helpers | No implementation | — | — | Registry returns module | Invalid | No demonstrated value |

### `app/services/utils/normalization.py`

**File responsibility:** Filesystem path compatibility, datetime parsing, timezone conversion, freshness calculations, and board-baseline policy.

| Symbol group | Responsibility | Inputs → Return | Side effects | Raises | Usage status | Value status |
| ------------ | -------------- | --------------- | ------------ | ------ | ------------ | ------------ |
| clock/freshness classes | Deterministic time and TTL calculations | time/config → object | None | validation/value errors | Used by schema/event/observability | Supporting |
| hybrid response classes | Act as native scalar plus envelope access | native + dict → object | None | — | Internal/tests | Questionable compatibility |
| path functions | Normalize/create paths | path → hybrid/envelope | directory creation for `ensure_*` | typed errors or envelope errors | Used internally; overlaps `paths.py` | Useful but duplicate |
| datetime conversion functions | Parse and normalize to UTC/naive/ISO/epoch | timestamp → native/hybrid/envelope | None except logging | inconsistent: some raise, some return error envelope | Used internally and cross-domain | Essential/supporting |
| pandas timezone function | Normalize Series/Index | pandas object → envelope | None | errors converted to envelope | likely data/tests | Useful |
| freshness functions | TTL checks | timestamp/TTL → envelope/object | None | mixed | schema validation/internal | Useful |
| board-baseline functions/constants | Domain-specific artifact freshness policy | artifact times → evaluation | None | validation errors | no confirmed external caller | Questionable |

### `app/services/utils/paths.py`

**File responsibility:** Cohesive traversal-safe path handling.

| Symbol | Responsibility | Inputs → Return | Side effects | Raises | Callers | Usage status | Value status |
| ------ | -------------- | --------------- | ------------ | ------ | ------- | ------------ | ------------ |
| `normalize_path` | Resolve path inside optional base | path/base → `Path` | None | `ValidationError`, `SecurityError` | `settings.py`, data storage | Used | Essential |
| `safe_join` | Join beneath root | base/parts → `Path` | None | typed errors | tests/examples, possible runtime | Used/test | Useful |
| `validate_path_within_root` | Gate caller-supplied path | path/root → `Path` | None | typed errors | tests/examples | Test-only confirmed | Useful |
| `ensure_dir`, `ensure_parent_dir` | Create bounded directories | path/base → `Path` | Filesystem write | typed errors | runtime storage and examples | Used | Essential |

### `app/services/utils/common.py`

**File responsibility:** Legacy/compatibility data utility facade with dynamic service discovery.

| Symbol group | Responsibility | Inputs → Return | Side effects | Raises/failure | Usage status | Value status |
| ------------ | -------------- | --------------- | ------------ | -------------- | ------------ | ------------ |
| `Param`, `combine_params` | Parameter expansion | values/grid → envelope | None | errors returned in envelope | strategy/optimization evidence mixed | Possibly used | Useful |
| `merge`, `concat` | Operate on `app.services.data.frames.Data` | datasets → envelope | None | errors returned | data/strategy callers possible | Possibly used | Useful but coupled |
| pandas accessors | `.hqt.rolling_mean` | Series/DataFrame → data | Registers accessors at import | pandas errors | dynamic use cannot be fully searched | Possibly used | Useful |
| `rolling_mean` | Numba/pandas rolling calculation | array/window → envelope | CPU | envelope error | tests/examples | Test-only/possible dynamic | Useful |
| `chunked` | sequential/thread/process chunk execution | data/function → envelope | Threads/processes | envelope error | no confirmed runtime caller | Test-only/possible | Questionable |
| serialization/bar conversion | dataframe → envelope records | frame → dict | None | envelope error | overlaps dataframe_tools/data frames | Possibly used | Questionable |
| cache functions | Process-local dataframe cache | key/loader → object/envelope | Global local-state mutation; loader may read disk | implementation-dependent | `app/services/data/csv.py` | Used | Essential to current CSV workflow |
| `tool_result_envelope` | Legacy envelope builder | status/data/errors → dict | None/logging | none | validation legacy code | Used internally | Supporting |
| alignment/comparison functions | Align/compare frames | frames/options → envelope | None | envelope error | tests/examples | Test-only | Useful |
| module `__getattr__` | Dynamic re-export from sibling services | name → object | Dynamic imports | `AttributeError` | unsearchable dynamic access | Possibly used | Questionable |

### `app/services/utils/dataframe_tools.py`

**File responsibility:** Smaller, mostly pure dataframe conversion/comparison layer.

| Symbol group | Responsibility | Inputs → Return | Side effects | Raises | Usage status | Value status |
| ------------ | -------------- | --------------- | ------------ | ------ | ------------ | ------------ |
| alignment/serialization/record helpers | Normalize datetime and convert rows | dataframe/mapping → dataframe/list | None | `ValidationError` | examples/tests; indirect callers possible | Test-only/possible | Useful |
| `chunked` / `chunk_sequence` | Split sequence | sequence/size → chunks | None | validation errors | tests/examples | Test-only | Useful |
| parameter combinations | Cartesian product | grid → list[dict] | None | validation errors | usage example | Test-only | Useful |
| comparison helpers | Structural/numeric comparisons | frames/options → dict | None | validation errors | tests | Test-only | Useful |
| aliases | Compatibility names | same as target | None | same | tests/docs | Possibly used | Supporting |
| advertised `align_dataframes_by_datetime` | Missing target | — | Registry returns module | — | Invalid | No demonstrated value |

### `app/services/utils/validators.py`

**File responsibility:** Large validation suite spanning payloads, environment, artifacts, OHLCV quality, market calendars, sessions, and remediation.

| Symbol group | Responsibility | Inputs → Return | Side effects | Raises/failure | Usage status | Value status |
| ------------ | -------------- | --------------- | ------------ | -------------- | ------------ | ------------ |
| packet/schema validators | Validate request/handoff/evidence/approval/registry | mapping/schema → envelope | None/logging | errors encoded | selective cross-domain use; duplicates schema_validation | Used/overlap | Useful |
| environment/artifact validators | Mode and artifact path/existence checks | mode/path → envelope | Read-only filesystem access | errors encoded | tests and simulator-related references | Possibly used | Useful |
| `DataSource`, `OHLCVSchema`, `DataQualityReport` | Validation contracts | fields → object/protocol | None | — | data/tests | Supporting |
| preparation/session functions | Normalize bars, filter sessions, compute stats | dataframe/config → data/report | CPU/read-only | typed or native errors | tests/examples | Test-only/possible | Useful |
| OHLCV validators | Detect time, numeric, price, spread, volume, gap and anomaly issues | dataframe/options → report/issues | CPU/read-only | mostly report results | tests/examples; some data-domain calls | Used selectively | Useful |
| issue annotation/remediation functions | Normalize severity and proposed handling | issues → enriched report | None | validation errors | no confirmed runtime caller | Test-only | Questionable |

### `app/services/utils/data_quality.py`

**File responsibility:** Focused, bounded OHLCV quality inspection and official wrapper.

| Symbol | Responsibility | Inputs → Return | Side effects | Raises/failure | Usage status | Value status |
| ------ | -------------- | --------------- | ------------ | -------------- | ------------ | ------------ |
| `QualityIssue`, `QualityProfile` | Result schemas | — | None | None | internal/tests | Supporting |
| `prepare_ohlcv_data` | Copy and UTC-normalize frame | frame/timestamp field → DataFrame | None | `ValidationError` | internal/tests | Supporting |
| `inspect_ohlcv_quality` | Produce score/profile/issues/remediation | frame/options → dict | None | `ValidationError` | examples/tests only found | Test-only | Useful but disconnected |
| `validate_ohlcv_quality` | Standard envelope wrapper | frame/options → response | Logging | catches to error response | scripts/examples/tests | Test/example-only | Questionable current integration |

### `app/services/utils/schema_validation.py`

**File responsibility:** Lightweight packet and schema validation using standard envelopes.

| Symbol group | Responsibility | Inputs → Return | Side effects | Raises/failure | Usage status | Value status |
| ------------ | -------------- | --------------- | ------------ | -------------- | ------------ | ------------ |
| required/input/output schema | Required/type/enum/version subset | payload/schema → envelope | Metadata mutation in output wrapper | errors returned | risk validation and tests | Used | Useful |
| handoff/evidence/approval/registry | Validate fixed required fields | packet → envelope | None/logging | errors returned | tests and possible agent workflows | Possibly used | Useful |
| blocked actions/range/freshness | Policy/range/time checks | values/lists → envelope | None | errors returned | tests/risk references | Used selectively | Useful |

Supported schema semantics are limited to required fields, type, enum, and schema version. Constraints such as `minimum`, `maximum`, and `minLength` are not enforced.

### `app/services/utils/security.py`

**File responsibility:** Secret redaction, password hashing, symmetric encryption, and secret-version helpers.

| Symbol group | Responsibility | Inputs → Return | Side effects | Raises/failure | Callers | Usage status | Value status |
| ------------ | -------------- | --------------- | ------------ | -------------- | ------- | ------------ | ------------ |
| sensitive-key/redaction helpers | Classify and redact mappings/text/scalars | value → native/envelope | None/logging | mixed typed/envelope failure | logger, event bus, errors, observability | Used | Essential |
| password hashing/verification | Argon2/PBKDF2/bcrypt-compatible credentials | password/hash → string/bool | Random salt; CPU | typed validation or false | API auth and SQLite users | Used | Essential |
| key loading/generation | Read env or generate Fernet key | env/ref/options → raw key/envelope/string | Environment read/randomness | typed/envelope failure | SQLite users and tests | Used | Essential/supporting |
| native encryption aliases | Encrypt/decrypt and return plaintext/ciphertext | text/key → string | CPU | cryptography errors | examples; possible persistence | Test/example confirmed | Useful |
| tool encryption wrappers | Standard responses | text/key/approval → envelope | CPU/logging | error envelope | tests | Test-only | Questionable |
| secret version selection | Choose highest active version | versions → dict | None | `SecurityError` | examples/tests | Test-only | Useful |
| diagnostics redaction | Return redacted paths/truncation | nested mapping → tuple | None | validation errors | tests | Test-only | Useful |

`load_encryption_key()` has two incompatible return contracts: raw key/exception in environment mode, or a standard envelope when `key_ref`/`key_material` is supplied.

### `app/services/utils/settings.py`

**File responsibility:** Global application settings plus live-runtime validation and research-domain models.

| Symbol group | Responsibility | Inputs → Return | Side effects | Raises | Usage status | Value status |
| ------------ | -------------- | --------------- | ------------ | ------ | ------------ | ------------ |
| `Settings` / `Config` | Parse env/.env, validate environment/live fields, resolve directories | settings values → model | Reads environment/.env on construction | `ConfigurationError`/Pydantic errors | runtime | Essential |
| `get_settings`, lazy `settings`, `load_config` | Process singleton | — → `Settings` | First call reads configuration and caches global state | construction errors | notification/live/API-related code and examples | Used | Essential |
| `validate_config` | Live readiness checks | settings → list[str] | None | None | usage/live code | Used/possible | Useful |
| research config models and `create_config` | Research EdgeLab configuration | defaults/fields → models | None | Pydantic validation | research/examples | Used outside intended core or test | Useful, misplaced |
| `TradeSample`, `EdgeStats`, `EdgeResult` | Research result contracts | fields → models | None | Pydantic validation | research package | Possibly used | Useful, misplaced |
| `research_modeling_module` | Dynamically import research service | — → module | Dynamic import | import errors | no direct caller confirmed | Possibly used | Questionable |
| advertised runtime-settings aliases | Missing implementation | — | registry module fallback | — | Invalid | No demonstrated value |

### `app/services/utils/auth.py`

**File responsibility:** Build and validate authorization context and enforce permissions/scopes.

| Symbol | Responsibility | Inputs → Return | Side effects | Raises/failure | Usage status | Value status |
| ------ | -------------- | --------------- | ------------ | -------------- | ------------ | ------------ |
| `AuthContext` | Immutable principal context | fields → object | None | None | tests/examples | Test-only | Useful but disconnected |
| `AuthorizationDecision` | Immutable allow/deny result | fields → object | None | None | auth functions/tests | Internal/test | Supporting |
| `build_auth_context` | Validate and construct context | principal/sets/IDs → context | Logging | `ValidationError` | tests/examples | Test-only | Useful |
| `authorize_action` | Deny-by-default permission/scope decision | context/requirements → decision | Logging | None | tests/examples | Test-only | Useful |
| `require_authorization` | Raise on deny | context/requirements → None | Logging | `SecurityError` | tests/examples | Test-only | Useful |
| `validate_auth_context` | Official envelope validator | payload → response | Logging | catches to error response | tests/examples | Test-only | Useful |
| advertised `AuthorizationResult`, `authorize_tool_call` | Missing | — | registry module fallback | — | Invalid | No demonstrated value |

The production API authentication path uses `app/api/auth_utils.py` and database sessions directly; it consumes only `security.verify_password`, not this authorization context.

### `app/services/utils/event_bus.py`

**File responsibility:** Thread-safe local pub/sub with queue and idempotency tracking.

| Symbol | Responsibility | Inputs → Return | Side effects | Raises/failure | Usage status | Value status |
| ------ | -------------- | --------------- | ------------ | -------------- | ------------ | ------------ |
| event types and `EventEnvelope` | Event contract | — | None | None | internal/tests | Supporting |
| `PublishResult` | Delivery result | fields → object | None | None | event bus/tests | Supporting |
| `InMemoryEventBus.subscribe/unsubscribe` | Handler registry | event/handler → None | Local state mutation | validation on empty type | tests/examples | Test-only | Useful |
| `publish` | Idempotency, queue append, synchronous handlers | envelope → result | State mutation and callback invocation | handler exceptions counted | tests/examples | Test-only | Questionable operationally |
| depth methods | State inspection | — → int | Read-only | None | tests | Test-only | Supporting |
| `build_event_envelope` | ID/time/redaction | fields → envelope | Random ID/time | validation errors | tests/examples | Test-only | Useful |
| `publish_event` | Publish with post-hoc elapsed check | bus/event → result | Same as publish | no pre-emption | tests/examples | Test-only | Questionable |
| advertised `InProcessEventBus` | Missing | — | registry module fallback | — | Invalid | No demonstrated value |

The queue is appended to but no public consume/drain operation exists. It therefore grows until full, even though dispatch is synchronous.

### `app/services/utils/observability.py`

**File responsibility:** Caller-owned in-memory metrics, component health, and circuit state.

| Symbol | Responsibility | Inputs → Return | Side effects | Raises | Usage status | Value status |
| ------ | -------------- | --------------- | ------------ | ------ | ------------ | ------------ |
| dashboard expectations/types | Contract constants | — | None | None | docs/tests | Test-only | Supporting |
| `MetricRegistry.record` | Validate/store sample | metric → record | Local state mutation | validation/security errors | tests | Test-only | Useful |
| `export_prometheus_text` / wrapper | Render stored samples | registry → text | Read-only | external-service wrapper error | tests | Test-only | Useful |
| metric wrappers | Record tool count/latency | values → records | Local state mutation | validation errors | tests | Test-only | Useful |
| `CircuitBreaker` methods | Closed/open/half-open transitions | outcomes/time → bool/None | Local state and metrics | little constructor validation | tests/examples | Test-only | Useful but disconnected |
| health functions | Sanitize component status and clock drift | fields → snapshot | Logging | validation errors | tests | Test-only | Useful |
| advertised `HealthCheckResult`, `health_snapshot` | Missing | — | registry module fallback | — | Invalid | No demonstrated value |

### `app/services/utils/README.md`

**File responsibility:** Package documentation.

| Finding | Evidence | Status | Value |
| ------- | -------- | ------ | ----- |
| Describes package as import-safe | `logger.py` configures file sinks at import; `common.py` eagerly imports pandas/NumPy and registers pandas accessors | Incorrect/stale | Questionable |
| Refers to `validations.py` | Actual focused file is `schema_validation.py`; separate `validators.py` also exists | Stale | Questionable |
| Documents approved exports | Registry and implementations disagree on multiple names | Stale | Questionable |
| Usage examples | Several examples do not match current return/error semantics | Partially stale | Supporting |

## 6. Actual Workflows

### `V1-WF-UTILS-001` — Structured Logging and Redaction

* **Scope:** Cross-domain
* **Trigger:** Any service imports and calls `logger`, `get_logger`, or a bound child logger.
* **Input boundary:** Message, positional/keyword formatting values, optional structured `extra`.
* **Functions and methods used:** `StructlogAdapter._emit()` → `security.redact_mapping()` / `security.redact_text()` → structlog/std logging → configured sinks.
* **Files involved:** `logger.py`, `security.py`.
* **External dependencies:** Optional `structlog`; local filesystem.
* **Output boundary:** stderr and/or `data/logs/*.log`; optional callback/queue sink.
* **Failure behaviour:** Most formatting, redaction, sink, and queue failures are swallowed to avoid breaking callers.
* **Operational status:** **Working**, with import-time side effects and silent failure risk.
* **Evidence:** Broad imports throughout `app/api`, `app/services`, and `data`; module-level `_configure_default_file_sinks()`.

```text
Runtime service call
→ logger.info()/warning()/error()
→ StructlogAdapter._emit()
→ redact_mapping() + redact_text()
→ structlog/std logger
→ callback/file/worker-queue sink
```

### `V1-WF-UTILS-002` — User Credential Hashing and Verification

* **Scope:** Cross-domain
* **Trigger:** User creation/password update or API login.
* **Input boundary:** Plain password and stored hash.
* **Functions and methods used:** `hash_password()` and `verify_password()`.
* **Files involved:** `security.py`, `data/database/sqlite/users.py`, `app/api/auth_utils.py`.
* **External dependencies:** Optional Argon2/bcrypt; PBKDF2 from standard library.
* **Output boundary:** Stored hash or authentication decision.
* **Failure behaviour:** Invalid password input raises `ValidationError`; verification generally returns `False` on malformed hashes or backend failures.
* **Operational status:** **Working**.
* **Evidence:** `UserManager.create_user()` and `_prepare_update_fields()` call `hash_password`; `authenticate_user()` calls `verify_password`.

```text
User registration/update
→ hash_password()
→ database stores hash

Login request
→ database loads hash
→ verify_password()
→ API authentication result
```

### `V1-WF-UTILS-003` — CSV Dataframe Cache

* **Scope:** Cross-domain
* **Trigger:** Data service loads CSV market data.
* **Input boundary:** Cache key and loader callback.
* **Functions and methods used:** `get_cached_dataframe()` and `clear_dataframe_cache()`.
* **Files involved:** `common.py`, `app/services/data/csv.py`.
* **External dependencies:** pandas and filesystem through the loader.
* **Output boundary:** Cached or newly loaded DataFrame.
* **Failure behaviour:** Loader/file errors propagate or are wrapped depending entry path.
* **Operational status:** **Working**.
* **Evidence:** Direct imports in `app/services/data/csv.py`.

```text
CSV request
→ construct cache key
→ get_cached_dataframe(key, loader)
→ cache hit: copy/return
   or cache miss: pandas.read_csv()
→ DataFrame returned to data service
```

### `V1-WF-UTILS-004` — Standard Tool Response Construction

* **Scope:** Cross-domain
* **Trigger:** Utility or domain tool completes or fails.
* **Input boundary:** Tool spec, result/error, request ID, timing flags.
* **Functions and methods used:** `ToolStandardSpec` → `standard_tool_response()`, or `build_metadata()` → `success_response()` / `error_response()`.
* **Files involved:** `standard.py`, `errors.py`, many utility modules, `app/services/risk/validators/validations.py`.
* **External dependencies:** None beyond logging.
* **Output boundary:** Standard dictionary envelope.
* **Failure behaviour:** Newer builders validate fields/codes; `standard_tool_response()` accepts looser values.
* **Operational status:** **Working**, but contract consistency is partial.
* **Evidence:** Direct imports and calls throughout utils and risk validators.

```text
Tool starts
→ capture timing/spec
→ execute implementation
→ standard_tool_response()
   or build_metadata() + success_response()/error_response()
→ response returned to caller
```

### `V1-WF-UTILS-005` — Safe Configuration Path Resolution

* **Scope:** Internal and cross-domain
* **Trigger:** `Settings` construction or data storage path handling.
* **Input boundary:** `HARUQUANT_HOME` and relative data/cache/audit/log directories.
* **Functions and methods used:** `Settings._validate_and_resolve_paths()` → `paths.normalize_path()`.
* **Files involved:** `settings.py`, `paths.py`, `app/services/data/storage.py`.
* **External dependencies:** Environment/.env and filesystem resolution.
* **Output boundary:** Absolute, base-bounded `Path` values.
* **Failure behaviour:** Invalid environment/path raises `ConfigurationError`, `ValidationError`, or `SecurityError`.
* **Operational status:** **Working**.
* **Evidence:** Direct import and calls in settings and data storage.

```text
Settings construction
→ validate environment/live values
→ normalize HARUQUANT_HOME
→ normalize child directories within home
→ resolved Settings instance
```

### `V1-WF-UTILS-006` — Shared Settings Bootstrap

* **Scope:** Cross-domain
* **Trigger:** First `get_settings()`, lazy `settings`, or `load_config()` call.
* **Input boundary:** Environment variables and optional `.env`.
* **Functions and methods used:** `get_settings()` → `Settings()` → Pydantic model validator.
* **Files involved:** `settings.py`, `paths.py`, `errors.py`, `logger.py`.
* **External dependencies:** `pydantic`, `pydantic-settings`.
* **Output boundary:** Process-wide cached settings model.
* **Failure behaviour:** Construction fails closed for invalid production/live configuration.
* **Operational status:** **Working**, but singleton reset/injection surface advertised by the registry is missing.
* **Evidence:** Settings tests, usage script, and cross-domain imports.

```text
Caller requests configuration
→ get_settings()
→ first access: Settings()
→ environment/live validation
→ path resolution
→ singleton cached and returned
```

### `V1-WF-UTILS-007` — Risk/Packet Validation

* **Scope:** Cross-domain
* **Trigger:** Risk or agent workflow validates payload/schema/packet.
* **Input boundary:** Mapping plus schema or required fields.
* **Functions and methods used:** schema validation functions and standard response builders.
* **Files involved:** `schema_validation.py`, `standard.py`, `normalization.py`, risk validators.
* **External dependencies:** None.
* **Output boundary:** Validation envelope or risk-native result.
* **Failure behaviour:** Usually returns a failure envelope; some parallel validators raise.
* **Operational status:** **Partial** because several competing validators implement different contracts.
* **Evidence:** `app/services/risk/validators/validations.py` imports shared error/standard utilities; repository search shows calls to validation names in both utils and risk.

```text
Risk/agent payload
→ required/schema/version/freshness check
→ standard success/error envelope
→ consuming domain decides whether to proceed
```

### `V1-WF-UTILS-008` — Local Event Publication

* **Scope:** Internal
* **Trigger:** Caller builds an event and publishes through a caller-owned bus.
* **Input boundary:** Event fields, payload, handlers.
* **Functions and methods used:** `build_event_envelope()` → `InMemoryEventBus.publish()` or `publish_event()`.
* **Files involved:** `event_bus.py`, `identity.py`, `normalization.py`, `security.py`.
* **External dependencies:** None.
* **Output boundary:** Synchronous handler calls and `PublishResult`.
* **Failure behaviour:** Handler exceptions are counted, not raised; full queue returns dropped; timeout is detected only after dispatch.
* **Operational status:** **Partial / test-only**.
* **Evidence:** Only tests, README, and usage example were confirmed as callers.

```text
Caller
→ build_event_envelope()
→ redact payload + generate ID/time
→ bus.publish()
→ append queue + invoke handlers
→ PublishResult
```

### `V1-WF-UTILS-009` — OHLCV Data Quality Inspection

* **Scope:** Internal utility / potential cross-domain
* **Trigger:** Example or test provides a DataFrame.
* **Input boundary:** OHLCV DataFrame and optional expected symbol/limits.
* **Functions and methods used:** `prepare_ohlcv_data()` → `inspect_ohlcv_quality()` → optional `validate_ohlcv_quality()`.
* **Files involved:** `data_quality.py`, `normalization.py`, `standard.py`.
* **External dependencies:** pandas and NumPy.
* **Output boundary:** Quality profile/issues or standard response.
* **Failure behaviour:** Native inspection raises `ValidationError`; official wrapper converts failure to envelope.
* **Operational status:** **Working in isolation; production integration unverified**.
* **Evidence:** Tests and examples; no confirmed production call to the focused facade.

```text
DataFrame
→ UTC/time preparation
→ OHLCV/time/symbol/volume checks
→ score + issues + remediation
→ optional standard envelope
```

## 7. Usage and Caller Map

| Public symbol / group | Called from | Call type | Runtime or test | Evidence |
| --------------------- | ----------- | --------- | --------------- | -------- |
| `logger`, logger methods | Broadly across `app/api`, `app/services`, `data` | direct import/call | Runtime | Numerous `from app.services.utils... import logger` hits |
| `hash_password` | `data/database/sqlite/users.py` | direct call | Runtime | user creation/password update |
| `verify_password` | `app/api/auth_utils.py`, `data/database/sqlite/users.py` | direct call | Runtime | login and user verification |
| `get_encryption_key` | `data/database/sqlite/users.py` | direct submodule import/call | Runtime | user encryption-key creation |
| `normalize_path` from `paths.py` | `settings.py`, `app/services/data/storage.py` | direct call | Runtime | config/storage path normalization |
| `ensure_parent_dir` / path helpers | storage and usage examples | direct call | Runtime/example | filesystem preparation |
| `get_cached_dataframe`, `clear_dataframe_cache` | `app/services/data/csv.py` | direct import/call | Runtime | CSV cache |
| standard response builders | utility modules and risk validators | direct import/call | Runtime | response contracts |
| shared error classes/helpers | API, brokers, data, execution, risk, strategy, trading | direct import/call | Runtime | typed errors and mapping |
| `Settings`, `get_settings`, `load_config` | settings consumers, tests, usage | direct/lazy access | Runtime/test | shared configuration |
| datetime/freshness helpers | settings/event/observability/schema and other services | direct internal/cross-domain call | Runtime/internal | UTC normalization |
| schema validation names | risk validators, utils, tests | direct call | Runtime/test | payload validation |
| focused `validate_ohlcv_quality` | scripts and usage/tests | direct call | Example/test | no confirmed production caller |
| identity generators | auth/event bus and tests | internal call | Internal/test | no broad runtime caller found |
| auth context/action functions | utility tests and usage script | direct call | Test/example | production API uses separate auth path |
| event bus | utility tests and usage script | direct call | Test/example | no runtime subscriber/publisher found |
| `CircuitBreaker`, metrics registry | utility tests and usage script | direct call | Test/example | no runtime provider integration found |
| `standardize_tool_callable`, `standardize_domain_exports` | definitions/docs/tests only | no meaningful execution | Test/unknown | implementations are placeholders |
| broken registry names | package `__all__` only | lazy fallback | None | target attributes absent |

## 8. Cross-Domain Surface

### Outbound — this domain depends on

| Depends on | Symbols or capabilities consumed | Where used in utils | Evidence |
| ---------- | -------------------------------- | ------------------- | -------- |
| `app.services` service discovery | `load_service_module`, `resolve_service_attr`, `service_modules` | `common.py` | dynamic compatibility facade |
| Data domain | `app.services.data.frames.Data` | `common.py::merge`, `concat`, `_get_data_class` | direct local imports |
| Research domain | `app.services.research.studies.unsupervised` | `settings.py::research_modeling_module` | string-based dynamic import |
| pandas / NumPy | dataframe and OHLCV operations | `common.py`, `validators.py`, `data_quality.py`, `dataframe_tools.py`, normalization series helper | direct and lazy imports |
| Numba | optimized rolling mean | `common.py` | optional import |
| Pydantic | settings and research models | `settings.py` | required import |
| structlog | structured output | `logger.py` | optional import |
| cryptography / Argon2 / bcrypt / passlib | crypto and password handling | `security.py` | lazy optional imports |
| filesystem/environment | logging, settings, path checks, artifact checks | logger/settings/paths/validators/security | direct standard-library use |

### Inbound — other domains depend on this domain

| Consuming domain/package | Symbols consumed | Purpose | Evidence |
| ------------------------ | ---------------- | ------- | -------- |
| API | logger, password verification, errors, utility contracts | request handling/auth/logging | `app/api/auth_utils.py`, routes |
| Data | logger, cache, paths, errors, normalization/validation | storage and market-data handling | `app/services/data/*` |
| Brokers | logger, settings/errors/standard contracts | routing/provider handling | broker search hits |
| Trading/execution | logger, errors, standard responses, time/settings | workflow safety and reporting | execution/trading search hits |
| Risk | errors, logger, standard builders, schema validation | policy validation and results | `app/services/risk/validators/validations.py` and other risk files |
| Strategy/indicator | domain exceptions, logger, dataframe utilities | calculations and registry handling | domain imports and error hierarchy |
| Notification | logger and configuration values | provider configuration/diagnostics | notification files |
| Research | research models/settings, logger, validation | studies and reports | settings dynamic import and research files |
| Database | password hashing/verification, encryption key, logger | user persistence/authentication | `data/database/sqlite/users.py` |
| Tests/examples | nearly all public surfaces | verification/demonstration | 17 utility test files plus usage scripts |

## 9. Duplicate and Overlapping Behaviour

| Item A | Item B | Overlap | Evidence | Risk |
| ------ | ------ | ------- | -------- | ---- |
| `normalization.normalize_path/ensure_*` | `paths.normalize_path/ensure_*` | Path normalization and directory creation | Same names and similar responsibilities | Callers receive different return/error contracts |
| `common` dataframe functions | `dataframe_tools` | serialization, records, alignment, comparison, chunks, combinations | Duplicate public functions | Divergent outputs and maintenance |
| `validators.py` packet validators | `schema_validation.py` | required/schema/handoff/evidence/approval/registry/freshness | Same public names | Registry hides which implementation is canonical |
| `validators.validate_ohlcv_quality` | `data_quality.validate_ohlcv_quality` | OHLCV validation | Same public name; root selects focused facade | Different reports and integration paths |
| `standard.validate_ohlcv_records` | validators/data_quality | OHLCV diagnostics | Third implementation | Inconsistent issue schemas |
| `security` redaction | `standard` sanitization | Sensitive key/value removal | Separate patterns and recursion rules | Different data may be redacted depending path |
| `common.canonical_json` | `standard.canonical_json` | Deterministic JSON | Root exports `common` version while standard uses its own | Contract drift |
| `standard_tool_response` | metadata + success/error builders | Envelope creation | Two official styles in same module | Different validation and metadata semantics |
| `security.generate_encryption_key` | `security.get_encryption_key` | Fernet key generation | Native string vs `StrKey` compatibility object | Type/contract confusion |
| native crypto/redaction APIs | tool-wrapper APIs | Same capability | `redact_text` vs `redact_text_tool`, etc. | Callers may expose or hide data differently |
| `auth.py` authorization | `app/api/auth_utils.py` authentication/session checks | Related access-control concerns | Production API bypasses utils auth context | Disconnected security model |
| settings/live/research models | domain-local configuration | Domain configuration | Research and live contracts embedded in utils | Central coupling |

## 10. Unused or Questionable Items

| Item | Finding | Searches performed | Confidence | Evidence |
| ---- | ------- | ------------------ | ---------- | -------- |
| 18 broken registry exports | Target attribute absent; registry returns module | full registry and target-file inspection; exact-name searches | High | listed in Section 5 |
| `standardize_tool_callable` | Returns the original function unchanged | implementation and caller search | High | marked “Placeholder” in `standard.py` |
| `standardize_domain_exports` | Logs only; does not standardize exports | implementation and caller search | High | marked “Placeholder” |
| `AuthContext` workflow | No production caller found; API uses separate session auth | direct call/import search and API inspection | Medium | `app/api/auth_utils.py` |
| event bus | Only tests/examples confirmed | imports, calls, subscribers, publishers | Medium | `test_event_bus.py`, usage example |
| observability registry/breaker | Only tests/examples confirmed | constructor/method/call search | Medium | `test_observability.py`, usage example |
| focused data-quality facade | Scripts/tests/examples only | import/call search | Medium | `scripts/examples/01_development.py`, tests/usage |
| board baseline freshness policy | No caller confirmed outside normalization/tests | exact-name and related-term search | Medium | `normalization.py` |
| `research_modeling_module` | Dynamic loader without direct caller | exact call and string-import search | Medium | `settings.py` |
| `AlertDeduplicator` | Test support with no runtime notification integration | class/call search | Medium | `standard.py` docstring explicitly describes future router |
| multiprocess logging helpers | No direct production setup call confirmed | import/call search | Medium | logger implementation/docs |
| `DomainError` / `PolicyError` aliases | Aliases add no type distinction | implementation and import search | Medium | aliases equal `Error` |
| registry pseudo-module exports (`data_quality`, `dataframe_tools`) | Deliberately resolve to module through missing attribute fallback | registry/target inspection | High | same fallback mechanism used for accidental missing names |

No item above is labelled dead code unless confidence is High. Medium findings may still be reached through dynamic configuration or unindexed code.

## 11. Incomplete or Disconnected Workflows

| Workflow / capability | Missing connection | Current impact | Evidence |
| --------------------- | ------------------ | -------------- | -------- |
| Authorization | No production middleware/tool attachment uses `AuthContext` or `require_authorization` | Implemented policy is not enforcing API access | production API uses database token checks |
| Event bus | No queue consume/drain API; no runtime publishers/subscribers found | Queue fills permanently; no system-level event workflow | `InMemoryEventBus.publish` only appends |
| Event timeout | Timeout checked after synchronous dispatch | Side effects may complete before a timeout failure is returned | `publish_event` implementation |
| Observability | Registry and circuit breaker not connected to providers/routes/export endpoint | Metrics and circuit state do not protect runtime work | only tests/examples found |
| Focused OHLCV quality | No confirmed production gate before data/backtest/live work | Valuable checks may not affect operational workflows | caller search |
| Runtime settings injection | Registry advertises injection/loading helpers that do not exist | Tests/callers cannot reliably substitute singleton through advertised API | registry mismatch |
| Tool standardization | Public standardizer functions are placeholders | Callables/exports are not actually wrapped or validated | `standard.py` |
| Usage schema example | Example expects `minimum`/`minLength` enforcement and exception | Example can report success for unsupported constraints and catches an exception that implementation returns as envelope | `tests/usage/app/services/01_utils.py` vs `schema_validation.py` |
| Registry validation test | Test requires `NotificationRouter`, but registry does not export it | Test suite is statically inconsistent with current registry | `test_utils_registry.py` |
| Logger import safety | Registry import itself is lazy, but accessing most utilities imports logger and opens files | “Import-safe” claim is narrower than documentation implies | `logger.py` module-level sink setup |

## 12. Structural Problems

| ID | Problem | Location | Impact | Evidence |
| -- | ------- | -------- | ------ | -------- |
| `V1-ISSUE-UTILS-001` | Missing exports silently resolve to module objects | `__init__.py::__getattr__` | Delayed, confusing runtime failures | fallback branch |
| `V1-ISSUE-UTILS-002` | 18 advertised exports have no matching target attribute | `__init__.py` and target modules | Public contract is inaccurate | Section 5 mismatch list |
| `V1-ISSUE-UTILS-003` | Importing logger creates directories and opens four files | `logger.py` | Import side effects, test pollution, unexpected writes | `_configure_default_file_sinks()` at module scope |
| `V1-ISSUE-UTILS-004` | Duplicate path implementations | `normalization.py`, `paths.py` | Ambiguous canonical API and incompatible returns | same public names |
| `V1-ISSUE-UTILS-005` | Duplicate dataframe utilities | `common.py`, `dataframe_tools.py` | Drift and maintenance burden | overlapping functions |
| `V1-ISSUE-UTILS-006` | Three OHLCV validation surfaces | `validators.py`, `data_quality.py`, `standard.py` | Different issue/report contracts | overlapping checks |
| `V1-ISSUE-UTILS-007` | Duplicate packet/schema validation | `validators.py`, `schema_validation.py`, risk validators | Different signatures and failure styles | same names |
| `V1-ISSUE-UTILS-008` | Inconsistent native/envelope/hybrid return types | normalization/security/common/standard | Callers must know implementation-specific conventions | response subclasses and wrappers |
| `V1-ISSUE-UTILS-009` | Placeholders exported as real standardization APIs | `standard.py` | Advertised behavior does not occur | placeholder implementations |
| `V1-ISSUE-UTILS-010` | Logger swallows all internal failures | `StructlogAdapter._emit` and sink dispatch | Lost diagnostics and false confidence | broad `except Exception: pass` |
| `V1-ISSUE-UTILS-011` | Event queue has no drain/consume lifecycle | `event_bus.py` | Event bus eventually reports full queue despite synchronous delivery | append-only queue |
| `V1-ISSUE-UTILS-012` | Event timeout is post-hoc | `publish_event()` | Cannot prevent slow handler side effects | elapsed check after `bus.publish` |
| `V1-ISSUE-UTILS-013` | Idempotency cache is unbounded | `InMemoryEventBus._idempotency` | Memory growth in long process | class note and implementation |
| `V1-ISSUE-UTILS-014` | Cross-domain error taxonomies live in utils | `errors.py` | Central coupling and oversized change surface | indicator/strategy/risk/simulation/live sections |
| `V1-ISSUE-UTILS-015` | Research models and dynamic research import live in settings | `settings.py` | Utilities depend on a domain they should support | EdgeLab models/import |
| `V1-ISSUE-UTILS-016` | Board/execution freshness policy lives in normalization | `normalization.py` | Generic time helper contains domain policy | board baseline types/policy |
| `V1-ISSUE-UTILS-017` | Common layer depends directly on Data domain | `common.py` | Shared kernel is not dependency-neutral | `app.services.data.frames.Data` import |
| `V1-ISSUE-UTILS-018` | Common imports pandas/NumPy and registers accessors at import | `common.py` | Heavy import and global pandas mutation | eager imports/decorators |
| `V1-ISSUE-UTILS-019` | Documentation and examples do not match implementation | README and usage script | Misleads callers and audits | validation and import-safety examples |
| `V1-ISSUE-UTILS-020` | Registry test is inconsistent with registry | `test_utils_registry.py` | Likely failing or obsolete expectation | requires absent `NotificationRouter` |
| `V1-ISSUE-UTILS-021` | Security key loader has bifurcated return contract | `security.py::load_encryption_key` | Same function returns raw key or envelope | branch by arguments |
| `V1-ISSUE-UTILS-022` | Root `normalize_path` selects the compatibility implementation, not cohesive `paths.py` | `__init__.py` | Package caller gets hybrid semantics while direct callers get `Path` | export target mapping |
| `V1-ISSUE-UTILS-023` | Error aliases advertised under names absent from implementation | `HaruError`, `BrokerError` | Imports appear valid but resolve to module | registry fallback |
| `V1-ISSUE-UTILS-024` | Production authentication bypasses utils authorization policy | `auth.py`, `app/api/auth_utils.py` | Separate security paths may diverge | caller inspection |

## 13. V1 Capability Catalogue

| Capability ID | Capability | Current implementation | Workflow(s) | Usage status | Value status | Notes |
| ------------- | ---------- | ---------------------- | ----------- | ------------ | ------------ | ----- |
| `V1-CAP-UTILS-001` | Structured logging | `logger.py` | `V1-WF-UTILS-001` | Used | Essential | Import-time files |
| `V1-CAP-UTILS-002` | Secret-safe logging | logger + security redaction | `001` | Used | Essential | Separate redaction engines exist |
| `V1-CAP-UTILS-003` | Deterministic error contracts | `errors.py` | `001`, `004`, `007` | Used | Essential | Cross-domain catalogue |
| `V1-CAP-UTILS-004` | Standard tool envelopes | `standard.py` | `004`, `007`, `009` | Used | Essential | Two builder styles |
| `V1-CAP-UTILS-005` | Deterministic IDs/JSON | identity + standard | `004`, `008` | Internal/test | Supporting | Several broken version exports |
| `V1-CAP-UTILS-006` | UTC/time normalization | `normalization.py` | `005`, `007`, `008`, `009` | Used | Essential/supporting | Mixed return types |
| `V1-CAP-UTILS-007` | Freshness/TTL evaluation | normalization + schema validation | `007` | Used internally | Useful | Includes domain policy |
| `V1-CAP-UTILS-008` | Safe path normalization | `paths.py` | `005` | Used | Essential | Duplicate compatibility version |
| `V1-CAP-UTILS-009` | Directory creation | paths/normalization | `005` | Used | Essential | Filesystem side effects explicit in paths.py |
| `V1-CAP-UTILS-010` | Dataframe caching | `common.py` | `003` | Used | Essential to current CSV workflow | Process-local global cache |
| `V1-CAP-UTILS-011` | Dataframe conversion/comparison | common + dataframe_tools | `009`/support | Test/possible | Useful | Duplicate APIs |
| `V1-CAP-UTILS-012` | Parameter expansion/chunk execution | common + dataframe_tools | none confirmed production | Test/possible | Useful/questionable | Threads/processes available |
| `V1-CAP-UTILS-013` | OHLCV quality validation | validators/data_quality/standard | `009` | Test/selective use | Useful | Three implementations |
| `V1-CAP-UTILS-014` | Generic schema validation | schema_validation/validators | `007` | Used selectively | Useful | Limited schema subset |
| `V1-CAP-UTILS-015` | Approval/handoff/registry validation | schema_validation/validators | `007` | Possible/test | Useful | No end-to-end agent flow confirmed |
| `V1-CAP-UTILS-016` | Password hashing/verification | `security.py` | `002` | Used | Essential | Environment-dependent algorithm choice |
| `V1-CAP-UTILS-017` | Symmetric encryption | `security.py` | none confirmed production | Test/example | Useful | Native and wrapper APIs |
| `V1-CAP-UTILS-018` | Secret version selection | `security.py` | none confirmed production | Test/example | Useful | No secret provider integration |
| `V1-CAP-UTILS-019` | Shared application settings | `settings.py` | `005`, `006` | Used | Essential | Broker/live/research fields combined |
| `V1-CAP-UTILS-020` | Live config readiness | `settings.py::validate_config` | `006` | Used/possible | Useful | No V2 comparison performed |
| `V1-CAP-UTILS-021` | Research configuration models | `settings.py` | none inside utils | Possible | Useful, misplaced | Direct domain leakage |
| `V1-CAP-UTILS-022` | Authorization decisions | `auth.py` | none production confirmed | Test/example | Useful but disconnected | Separate API auth |
| `V1-CAP-UTILS-023` | In-memory pub/sub | `event_bus.py` | `008` | Test/example | Questionable | Queue lifecycle incomplete |
| `V1-CAP-UTILS-024` | In-memory metrics | `observability.py` | none production confirmed | Test/example | Useful but disconnected | No exporter route found |
| `V1-CAP-UTILS-025` | Circuit breaking | `observability.py` | none production confirmed | Test/example | Useful but disconnected | No provider integration |
| `V1-CAP-UTILS-026` | Health/clock drift snapshots | `observability.py` | none production confirmed | Test/example | Useful | No runtime health aggregation found |
| `V1-CAP-UTILS-027` | Public lazy facade | `__init__.py` | all | Used | Essential but defective | 195 declared exports, 18 mismatches |
| `V1-CAP-UTILS-028` | Multiprocess log routing | `logger.py` | none confirmed | Possibly used | Useful | Setup caller not found |

## 14. Audit Conclusions

### Valuable behaviour worth preserving

Confirmed high-value Version 1 behaviour includes:

* structured logging used across the application;
* deterministic error codes and typed base exceptions;
* standard tool response creation;
* password hashing and verification used by user persistence and API login;
* safe path normalization and directory creation;
* application settings parsing and validation;
* dataframe caching used by CSV market-data loading;
* UTC normalization and freshness primitives;
* selected schema/validation helpers used by risk and other domains.

### Behaviour that exists but is disconnected

The following implementations are coherent enough to demonstrate value but currently lack a confirmed production workflow:

* `auth.py` authorization context and deny-by-default enforcement;
* local event publication;
* in-memory metrics and circuit breaking;
* focused data-quality inspection;
* alert deduplication;
* several packet validators and secret-rotation helpers;
* multiprocess logging setup.

### Likely dead weight or invalid surface

High-confidence candidates are:

* the 18 broken package exports;
* `standardize_tool_callable`;
* `standardize_domain_exports`;
* stale registry/documentation names.

These are not declared dead code beyond the available static evidence, but they currently provide no demonstrated functional behaviour.

### Duplicated responsibilities

The strongest duplication clusters are:

* `paths.py` versus path functions in `normalization.py`;
* `common.py` versus `dataframe_tools.py`;
* `schema_validation.py` versus schema portions of `validators.py`;
* three OHLCV validation implementations;
* security redaction versus standard-envelope sanitization;
* multiple standard response builders.

### Important uncertainties

Manual confirmation or executable checkout is still needed for:

* dynamic symbols resolved through `common.__getattr__`;
* environment/configuration-driven module imports;
* whether any scheduled/agent runtime loads utilities by string;
* actual test status and coverage;
* runtime use of research models, board-baseline freshness, event bus, observability, or multiprocess logging;
* whether the inspected commit is the exact deployed Version 1 revision.

### Final validation result

* Every Python file discovered under `app/services/utils` is represented.
* The package-level `__init__.py` registry was checked.
* Direct runtime callers, tests, examples, dynamic loaders, and decorators were searched.
* Production usage is distinguished from test/example usage.
* Uncertain no-caller findings are labelled conservatively.
* No Version 2 design or requirements were introduced.
* No source code was changed.

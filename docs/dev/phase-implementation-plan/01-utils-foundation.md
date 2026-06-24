## Phase 1 Utils Foundation

### Goal

Implement the Utils Foundation requirements under `app/utils/` while preserving the phase module boundaries and governance rules.

Task inventory: calculated from the checkbox tasks in this section.

### Dependency Files and Functionality

Required functionality:

- JSON structured logging and console log configuration.
- Standard tool response envelope construction.
- Domain exception types and error registration mapping.
- Timestamp UTC normalization and ISO string formatting.
- Monotonic clock duration timing.
- Collision-resistant trace ID generation and prefix checks.
- Safe traversal directory normalization and creation.
- Thread-safe Event Bus subscription and publishing.
- Metrics registry and Prometheus text format output.
- Secret payload redaction and settings loading.

### Functionality to Implement

Tasks are grouped by domain functionality. Each task is actionable; related original requirements are preserved as sub-bullets where merged.

#### Package Initialization

- [x] Implement `app/__init__.py` as a clean, side-effect-free package entry point.
  - `app/__init__.py` exists and is side-effect free
  - Implementation is fresh and clean, with no backward-compatibility shims
- [x] Implement `app/utils/__init__.py` as the public registry for the utility domain, exposing only approved names listed in `__all__`, only after modules exist and names are finalized.
  - Only intentionally imported names listed in `__all__` may be public
  - Internal helpers remain private unless explicitly intended for public import
  - No accidental public exports may exist
  - Implement only after modules exist and public names are finalized
- [x] Enforce that no compatibility shims, aliases, fallback import modules, or duplicate wrapper modules exist anywhere in the package.
- [x] Require new public exports to be justified by real cross-domain reuse, and lock public exports against renaming or removal after v8 acceptance without a new versioned specification and registry review.
- [x] Keep `app/utils/__init__.py` import-light: must not eagerly import pandas, cryptography, dotenv, broker SDKs, network clients, notification clients, Prometheus exporters, or other heavy optional dependencies unless absolutely necessary.
- [x] Document compatibility review notes for future public API changes.
- [x] Treat support helpers as returning native Python values when they are not classified as agent-callable official AI tools.

#### Logging and Diagnostics

- [x] Implement `app/utils/logger.py` exposing a project-wide `logger`, `get_logger(name: str | None = None)`, and `configure_logging(level: str | int = "INFO")`, built on Python `logging`, before any module that needs production logging.
  - The logger is exported as a support object, not an official AI tool
  - Module exposes project-wide `logger`, `get_logger`, and `configure_logging`
- [x] Implement structured JSON-compatible logging for production runtime events, and colorized human-readable console logging for local development in the approved format.
  - Official AI tools use structured logging
  - Production logging uses a JSON-compatible structured formatter
  - Local development logging supports colorized human-readable console output
  - Human-readable console lines use format `datetime | level | module.submodule.filename:function:line | message`
  - Human-readable console timestamps use format `YYYY-MM-DD HH:MM:SS`
  - Human-readable console logging includes source line numbers where available
- [x] Ensure logging output includes `timestamp`, `level`, `logger_name`, `message`, `event_name`, `module`, `function`, `request_id`, `workflow_id`, `correlation_id`, and `error_code` where available.
- [x] Support child loggers per module while preserving a stable root logger name, and prevent duplicate handlers.
  - Logging supports child loggers while preserving a stable root logger name
  - Logging configuration avoids duplicate handlers
- [x] Restrict logging configuration to an explicit configuration function, so importing logger utilities does not force application-level logging configuration.
- [x] Implement opt-in file logging, configured explicitly through runtime settings or `configure_logging`, writing only to configured log directories normalized through safe path handling.
  - File logging is opt-in and explicitly configured
  - File logging writes only to configured, safe-path-normalized log directories
- [x] Implement rotating log files with configurable maximum file size and maximum retained file count, plus configurable retention deletion of old rotated log files bounded to configured log directories.
  - Log rotation supports configurable maximum file size and retained file count
  - Log retention supports configurable deletion of old rotated log files
  - Retention deletion is bounded to configured log directories and must not delete arbitrary files
- [x] Ensure log file writes, rotation, and retention deletion degrade safely if the filesystem or logging sink fails, and that logging never writes secrets.
- [x] Make log-level configuration controllable by runtime settings.
- [x] Log function/tool calls, validation failures, successful completions, recoverable warnings, and execution failures across production files, with lifecycle distinctions and trace identifiers for official AI tools.
  - Production files log function/tool calls, validation failures, successful completions, recoverable warnings, and execution failures where applicable
  - Official AI tool logs distinguish start, completion, validation failure, recoverable warning, and execution failure lifecycle events
  - Official AI tool logs include request and workflow trace identifiers where available
- [x] Log Event Bus publish, subscribe, delivery failure, retry, dead-letter, queue-full, and dropped-event events.
- [x] Log notification routing decisions and delivery outcomes without exposing sensitive message bodies.
- [x] Log sanitized auth validation and authorization decisions.
- [x] Log metrics/export/health-check failures where detectable.
- [x] Ensure production files never log passwords, API keys, broker credentials, encryption keys, tokens, raw private payloads, full approval packets, notification provider credentials, authorization headers, or Telegram bot tokens.
- [x] Ensure logging is thread-safe under concurrent tool execution, has minimal overhead, and degrades safely if a logging sink fails.
- [x] Document required log fields and optional trace fields.
- [x] Write logger tests verifying colorized console output can be enabled and disabled deterministically, human-readable formatting includes datetime/level/module path/function/line/message, duplicate handler prevention, and that output is deterministic enough for field assertions.

#### Standard Primitives and Tool Response Envelope

- [x] Scope `app.utils` strictly as a shared utility layer: it must not own trading strategy logic, broker execution logic, risk-governor decisions, portfolio allocation decisions, application orchestration, UI, database repositories, or backtest engines, must not become a dumping ground for unrelated helpers, and must not export every internal helper as a public agent tool.
  - Does not own trading strategy, broker execution, risk-governor, portfolio allocation, or orchestration decisions
  - Does not implement UI, database repositories, or backtest engines
  - Does not become a dumping ground for unrelated helpers or export every helper as a public tool
  - Does not hide external dependency behavior behind unclear convenience functions
- [x] Prohibit `app.utils` from performing live trading, live account mutation, or any trading/risk/allocation/execution/strategy acceptance decision; route financial decisions to the appropriate risk, portfolio, execution, strategy, or governance domain.
  - Utilities must not approve/reject trades, recommend allocations, decide strategy promotion, approve risk changes, place/close/modify/cancel orders, activate live systems, or override kill switches
  - Modules requiring financial decisions call the appropriate governed domain
  - This is a domain-level requirements document for `docs/planning/DOMAIN.md`, not a sprint-specific requirements document
- [x] Reserve data repair, resampling, enrichment, persistence, and cleaning workflows for `app.services.data`, which will own them; keep `app.utils` free of UI, broker runtime, database repository, or LLM framework dependencies.
- [x] Classify every public name as either an official AI tool or a support object/helper, and keep support helpers native unless explicitly classified as official tools or conditional tools approved for direct agent use.
- [x] Implement `app/utils/standard.py`, before official AI tools exist, defining the standard HaruQuant tool envelope with top-level keys `status`, `message`, `data`, `error`, and `metadata`.
  - `status` is `success` or `error`; `message` is a string; `error` is `None` or a mapping with `code` and `details`
  - Official success responses include `status="success"`, message, data, `error=None`, and metadata
  - Official error responses include `status="error"`, message, `data=None`, error code/details, and metadata
  - Standard response validation rejects missing top-level keys, missing metadata keys, and malformed errors
- [x] Implement `get_execution_ms(start_time)` returning milliseconds rounded to three decimals, using a consistent calculation for official tools.
- [x] Require official AI tools to validate inputs, never fail silently, never return unstructured `None`, and return standard error envelopes for expected validation failures, including `CIRCUIT_OPEN` or provider-specific deterministic details for circuit-open failures.
- [x] Ensure agents may call only approved official AI tools through approved tool attachment, and that data-quality issues reported through the envelope include code, severity, message, column, row count, and samples.
- [x] Implement canonical JSON serialization returning deterministic JSON strings, and error helpers returning deterministic names and fallback messages, with sanitized details only in error events.
- [x] Implement domain-specific error mapping so future errors inherit from `Error` or expose a compatible `code` attribute, and standard response builders map `Error` subclasses generically without hardcoding every future domain error.
- [x] Document every public function's purpose, usage guidance, arguments, return value, and side effects, with agent-facing docstrings for official AI tools explaining when to use the tool and what it does not do.
  - Documentation includes an operational runbook for critical utility-layer failures
  - Documentation describes safe metric-label rules and rejected-label examples
  - Documentation describes which features are support helpers vs. official AI tools, and which adapters are optional/lazy-loaded
- [x] Implement usage examples for official AI tools and production primitives demonstrating success and error handling with realistic inputs.
- [x] Enforce engineering baseline standards across `app.utils`: full typing on public functions/methods, explicit input validation and output shapes, deterministic error behavior, no `print()` in production logic, concurrency-safety unless documented otherwise, no unsafe mutation of caller-owned inputs, and documented concurrency guarantees per component.
  - No mutable module-level state unless explicitly bounded, tested, and specified as a shared cache
  - Time-dependent, ID-dependent, and randomness-dependent helpers support deterministic testing where practical
- [x] Ensure optional dependencies never break importability, and that missing optional dependencies fail only when the relevant feature is used, with explicit error messages identifying the missing dependency and required feature.
- [x] Implement deterministic OHLC/data-quality reporting primitives: negative prices, zero prices, out-of-range OHLC values, and NaN/infinity values must be reported; symbol verification must be marked `not_available` when no symbol column exists.
- [x] Bound diagnostic output: issue lists and issue samples truncate when limits are reached, repeated identical alerts are deduplicated or throttled, and high-cardinality metric labels are rejected or normalized.
- [x] Implement fast-fail behavior for open circuit state.
- [x] Achieve at least 80% line coverage for `app.utils`, with edge-case coverage, official AI tool tests verifying metadata correctness and `execution_ms` existence, and data-quality tests covering at least 15 distinct data-quality cases.

#### Domain Exception Handling and Error Routing

- [x] Implement `app/utils/errors.py`, before deterministic failure behavior is needed, defining `Error`, `ValidationError`, `ConfigurationError`, `SecurityError`, `DataError`, and `ExternalServiceError`, each carrying a deterministic `code` attribute and human-readable message.
  - Module defines `Error`, `ValidationError`, `ConfigurationError`, `SecurityError`, `DataError`, `ExternalServiceError`
  - Every shared exception carries a deterministic `code` attribute and human-readable message
- [x] Implement `error_name(code)` and `message_for(code, default)` so unknown codes resolve safely to `UNKNOWN_ERROR` or a provided default, and so future domain-specific errors inheriting from `Error` (or exposing a compatible `code: str`) map generically without hardcoding.
  - `error_name(code)` returns deterministic names; `message_for(code, default)` returns useful fallback messages
  - Unknown codes resolve safely to `UNKNOWN_ERROR` or a provided default
  - Standard response builders map `Error` subclasses generically
- [x] Map unknown non-HaruQuant exceptions safely to `UNKNOWN_ERROR` or `TOOL_EXECUTION_FAILED` at controlled tool boundaries, and unexpected execution failures to `TOOL_EXECUTION_FAILED` or another safe deterministic error code.
- [x] Allow support helpers to return clear native values or raise typed HaruQuant exceptions for programmer or validation errors, using deterministic codes such as `INVALID_INPUT` or `VALIDATION_FAILED` for expected validation failures; raw exception objects must never be returned in `data` or `error`.
- [x] Define and support the deterministic error-code set: `INVALID_AUTH_CONTEXT`, `AUTHORIZATION_FAILED`, `INVALID_EVENT`, `EVENT_PUBLISH_FAILED`, `EVENT_HANDLER_FAILED`, `EVENT_DEAD_LETTER_FAILED`, `QUEUE_FULL`, `BACKPRESSURE_EXCEEDED`, `NOTIFICATION_FAILED`, `NOTIFICATION_SUPPRESSED`, `NOTIFICATION_THROTTLED`, `OBSERVABILITY_ERROR`, `METRICS_EXPORT_FAILED`, `CLOCK_DRIFT_DETECTED`, `CIRCUIT_OPEN`, `SECRET_VERSION_CONFLICT`, including `INVALID_EVENT` for event validation failures and `INVALID_INPUT` for missing mandatory OHLC columns.
- [x] Document every public function's raised exceptions or structured error behavior, including official AI tool docstrings explaining what error codes may be returned.
- [x] Write error tests verifying exception attributes, known codes, unknown codes, fallback messages, and official AI tool deterministic error codes.
- [x] Implement `app/utils/errors.py` early alert/error routing (`ErrorRouter` / `route_error`), before notification routing, so the rest of the system can report issues consistently, failing safely without exposing sensitive information.
  - Event Bus is intended for utility, workflow, alert, and error-routing events, not direct trading execution
- [x] Implement the standard error event model including error code, severity, source module, source function or tool, request ID, workflow ID, correlation ID, sanitized message, sanitized details, and timestamp.
  - Expected validation failures route as warning or error events depending on severity
  - Unexpected execution failures route as error or critical events; critical system failures route to notifications
- [x] Implement error-routing deduplication within a configurable time window, recursion/alert-storm prevention, secret redaction before publishing, and preservation of diagnostic context without exposing sensitive payloads.
  - Deduplicates repeated identical errors within a configurable window
  - Prevents recursive alert storms and recursively triggered infinite error routing
  - Redacts secrets before publishing events, logging, metrics, or notifications
  - Preserves original error code and attaches routing failure code separately when both exist
- [x] Support severity-based routing rules, environment-specific routing rules, and suppression rules for known noisy non-critical errors; expose metrics for routed, suppressed, retried, failed, and dead-lettered error events.
- [x] Accept sanitized exception context, deterministic error code, severity, request ID, workflow ID, and correlation ID as routing inputs, and return routed, suppressed, deduplicated, throttled, or failed status.
- [x] Document error routing behavior, severity rules, and how alerts/error routing initialize early in the system lifecycle; include a production readiness checklist for secrets, auth, alert routing, and metrics before enabling live workflows.
- [x] Write error-routing tests covering validation error routing, unexpected exception routing, deduplication/throttling, recursive error suppression (including under circuit-open and notification-failure scenarios), and that alert failures are logged/measured without exposing secrets.

#### Collision-Resistant Identity and Trace ID Generation

- [x] Implement `app/utils/identity.py`, before request/workflow/event trace helpers are needed, providing `generate_id`, `generate_prefixed_id`, `generate_request_id`, `generate_workflow_id`, `generate_correlation_id` (or equivalent), and `generate_event_id` (or equivalent), using UUID4, ULID-like generation, or an equivalently collision-resistant approach unless deterministic IDs are explicitly required.
  - Module provides all listed ID generators
  - Generated IDs are collision-resistant and string-safe
- [x] Implement `validate_request_id`, `validate_workflow_id`, and `ensure_version`, where `ensure_version(None)` returns the configured default; ID validation is deterministic and performs no external lookups.
- [x] Ensure IDs are safe for logs, filenames where practical, audit records, tool metadata, events, notifications, and metrics after cardinality controls, and never contain secrets or raw user-provided text.
- [x] Reject empty or unsafe ID prefixes during prefix validation.
- [x] Wire official AI tools to accept optional `request_id: str | None = None` and include `tool_name`, `tool_version`, `tool_category`, `tool_risk_level`, `request_id`, `execution_ms`, `read_only`, `writes_file`, `modifies_database`, `places_trade`, and `requires_network` in `metadata`; standard response validation rejects invalid statuses.
  - Request IDs and workflow IDs are suitable for logs, audit records, tool responses, and agent handoffs
  - Usage examples use `request_id` where applicable
- [x] Avoid avoidable circular imports and unnecessary deep copies in large data-quality validations.
- [x] Write identity tests verifying ID uniqueness, prefix validation, version defaulting, request ID propagation through official AI tool tests, and invalid-input handling (invalid datetime inputs, invalid high-low relationships, empty/unsafe prefixes).

#### Timestamp and Data Normalization

- [x] Implement `app/utils/normalization.py`, before data quality, settings, freshness checks, and event timestamp validation, defining `DEFAULT_TIMEZONE = "UTC"` and providing datetime parsing, timestamp normalization, UTC conversion, naive UTC conversion, UTC timestamp formatting with trailing `Z`, timezone normalization for pandas-like series/timestamp columns, and stale-data checks.
  - Module defines `DEFAULT_TIMEZONE = "UTC"` and provides each listed normalization capability
  - Timestamp formatting returns UTC ISO strings ending in `Z`
- [x] Make timezone behavior explicit: naive datetimes are handled deterministically using an explicit assumed timezone, ISO strings parse consistently, helpers never use the local machine timezone implicitly, and wall-clock timestamps are UTC-aware.
- [x] Implement execution timing using monotonic timers (`get_execution_ms(start_time)` via `time.perf_counter()`), distinguishing wall-clock timestamps from monotonic durations, with time-dependent helpers supporting injected `now` values or clock objects where practical.
- [x] Surface clock-drift risk in distributed workflow timestamp validation where relevant; include event creation/processing time in event envelopes, created/routed/sent/failed timestamps in notification diagnostics, and clock-drift status in health checks where supported.
- [x] Keep `app.utils` import-light and side-effect free: importing must not open network connections, initialize broker clients, run validation jobs, or mutate environment variables, and heavy dependencies import inside the specific submodule/function that needs them, so `app.utils` import stays safe in tests, CLI scripts, FastAPI startup, and agent runtime initialization.
- [x] Document the UTC-first time policy and monotonic execution timing policy.
- [x] Implement deterministic reporting for unparseable datetimes, non-monotonic timestamps, duplicate timestamps, and stale data, with naive datetimes normalized using the explicit assumed timezone and stale checks deterministic when `now` is injected.
- [x] Write normalization tests verifying ISO parsing, naive timezone assumptions, UTC conversion, and stale checks.

#### Safe Path Traversal and Directory Utilities

- [x] Implement `app/utils/paths.py`, before settings and artifact helpers, providing `normalize_path` (no side effects), `ensure_dir` (creates a directory when missing), and `ensure_parent_dir` (creates a parent directory when missing), accepting string or `Path` values and optional `base_dir`, and returning `Path` objects.
  - Module provides `normalize_path`, `ensure_dir`, `ensure_parent_dir`
  - Path helpers accept string or `Path` values and optional `base_dir`, and return `Path` objects
- [x] Validate path inputs, reject empty paths, and reject path traversal outside `base_dir` when a base directory is supplied; use platform-safe file/directory permission defaults.
- [x] Ensure importing any `app.utils` module never creates files or directories as a side effect.
- [x] Write path tests covering safe normalization, unsafe traversal rejection, directory creation, parent creation, success paths, and failure paths; include a concurrency stress test suite outside the fast unit-test path.

#### Dataframe Manipulations and Operations

- [x] Implement `app/utils/dataframe_tools.py`, after normalization and errors, providing datetime alignment for dataframes, bar-to-record conversion, chunking for sequences, parameter-combination helpers, dataframe comparison helpers (including OHLC/OHLCV comparison with tolerance support), and dataframe-record serialization.
  - Module provides each listed dataframe helper
  - Comparisons support tolerance
- [x] Ensure dataframe helpers return native Python objects where applicable, validate required columns, never mutate caller-owned dataframes unless explicitly documented, and document copy/view/transformed-data behavior.
  - `serialize_dataframe_records` emits UTC ISO timestamp strings ending in `Z`, and serialization is JSON-safe where practical
  - `compare_dataframes` aligns by comparable indexes or fails with a clear validation error when deterministic alignment is impossible
  - `chunked` rejects `size <= 0` with a clear validation error
  - Empty dataframes are handled deterministically
- [x] Keep pandas import lazy: importing `app.utils` must not eagerly import pandas, dataframe helpers use lazy pandas imports or `TYPE_CHECKING` guards, and missing pandas fails only when a dataframe helper is called; importing any `app.utils` module must not execute expensive dataframe operations, and dataframe helpers avoid repeated full-dataframe scans where possible.
- [x] Implement clear failure for missing required dataframe columns and for dataframe index mismatch when deterministic alignment is impossible.
- [x] Write dataframe tests verifying alignment, serialization, UTC timestamp output, comparison, index mismatch behavior, missing columns, chunk-size validation, and no input mutation.

#### Data Quality Auditing and Integrity Checking

- [x] Implement `app/utils/data_quality.py`, after standard, errors, normalization, dataframe tools, and schema validation, providing `prepare_ohlcv_data` and `validate_ohlcv_quality` as a stateless, diagnostic-only, low-risk read-only official AI tool that inspects, profiles, scores, and reports issues with descriptive remediation recommendations — never repairing, enriching, persisting, resampling, cleaning, or mutating input data (those workflows are reserved for `app.services.data`).
  - Market-calendar gap handling depends on session rules supplied by a caller or future domain module; default OHLCV scoring model applies unless a later module-specific spec replaces it
  - `validate_ohlcv_quality` is stateless, diagnostic-only, and does not repair/resample/persist/enrich/mutate input data
  - Caller-owned dataframes are never mutated
- [x] Validate structural input: confirm input is a pandas DataFrame, confirm mandatory OHLC columns exist (producing structured `INVALID_INPUT` details when missing, and `INVALID_INPUT` for invalid OHLCV input type), ignore extra columns by default unless they create ambiguity, and confirm datetime column or datetime-compatible index availability with parseable datetimes.
- [x] Detect and report timestamp issues: monotonicity, duplicate timestamps, duplicate OHLC/OHLCV rows, missing timestamps or inferred gaps when timeframe is known, and market-calendar gaps distinguished from unexpected gaps where session rules are supplied.
- [x] Validate price/volume integrity: OHLC values numeric, negative prices flagged, zero prices flagged, high-low relationships validated, OHLC values within candle high/low range, zero/negative volume flagged when volume is supplied, spread numeric and non-negative when supplied, non-numeric OHLC values reported, and non-numeric or negative spread reported when supplied.
- [x] Detect extreme spikes using configurable thresholds, flatline candles, and numeric infinities/NaN values; report timezone awareness and produce session-level statistics where possible.
- [x] Calculate a deterministic quality score using the default penalty model (critical `-40`, error `-20`, warning `-5`, info `-1`, bounded `0`–`100`) against a default pass threshold of `90.0`, assign severity levels consistently (aggregating to `critical` > `error` > `warning` > `info`), and require `passed=True` only when there are no critical or error issues and `quality_score >= quality_pass_threshold`.
  - Warning/info issues may still produce `passed=True` only when the score remains above threshold
- [x] Bound diagnostic output for large datasets: cap issue samples by `max_issue_samples` and issue list length by `max_issues_returned`, marking truncation explicitly through `summary["issues_truncated"]` and `summary["samples_truncated"]`, to avoid oversized tool responses.
- [x] Report symbol and timeframe context: `SYMBOL_MISMATCH` when `symbol` is provided and a dataframe `symbol` column exists; `not_available` in summary when `symbol` is provided with no dataframe `symbol` column; `TIMEFRAME_MISMATCH` or `UNEXPECTED_TIME_GAP` when timeframe checks fail.
- [x] Return successful validation responses including `symbol`, `timeframe`, `rows_checked`, `quality_score`, `passed`, `severity`, `issues`, `summary`, `profile`, and `remediation`, with each issue including `code`, `severity`, `message`, `column`, `row_count`, and `sample`; accept a pandas DataFrame plus optional symbol/timeframe context.
- [x] Meet performance targets: handle 1,000 rows quickly for normal agent workflows and 100,000 rows within a practical local validation budget.
- [x] Write data-quality tests covering clean OHLCV data, missing columns, extra columns, symbol mismatch, timeframe mismatch, duplicates, gaps, bad OHLC, zero/negative values, spread, volume, spikes, flatlines, truncation limits, schema compliance, and 10,000 bad rows returning no more than configured issue/sample limits.

#### Input Parameter Validation Helpers

- [x] Implement `app/utils/validations.py`, after standard, errors, normalization, security, auth, and observability foundations, providing reusable validation helpers for agent, workflow, tool, registry, evidence, approval, freshness, artifact, and payload contracts, including `validate_numeric_range` and `validate_required_fields` as support helpers returning native validation results.
  - Native validation results include at minimum `valid`, `message`, `code`, and `details`
  - Official validators may wrap native validation results in standard tool envelopes
  - `validate_handoff_payload` is implemented as a low-risk, read-only official AI tool
- [x] Implement numeric-range validation for risk values, prices, volumes, spreads, scores, thresholds, and allocation limits: reject non-numeric values, reject `NaN`/positive infinity/negative infinity unless a future specialized function explicitly allows them, treat bounds as inclusive unless documented otherwise, and include the logical field name in messages.
  - Accepts a value, logical field name, optional minimum, optional maximum, and `allow_none`
- [x] Implement required-field and schema validation: explicit missing-required-field errors, unknown extra fields rejected by default (unless a documented schema policy allows them), and accept payload/schema mappings with optional `schema_version`.
- [x] Implement schema-version compatibility checks: version mismatches return `VALIDATION_FAILED` with a clear message; compatibility follows semantic-version rules requiring the same major version, may accept payload minor versions ≤ schema minor version when no breaking change is declared, and may be overridden by an explicit compatible-version allowlist.
- [x] Return precise schema validation errors: specific path to the invalid field using a deterministic format such as JSON Pointer (dot-path strings allowed for human-readable display when documented), nearest valid parent path when the exact path cannot be determined, and bounded `invalid_fields` as a list of `{path, code, message}` objects, redacted and bounded.
- [x] Implement domain-specific validators: evidence (source, timestamp, evidence type required), approval packets (action, reason, evidence, risk class, approval status required), registry entries (name, version, category/domain, risk level, status required), risk-level validation via the central `VALID_RISK_LEVELS` model, environment validation via `VALID_ENVIRONMENT_MODES` (or a stricter allowlist), blocked-action validation (requires `action`, fails closed when the action is in `blocked_actions`), freshness validation (requires a timestamp field defaulting to `as_of`, configurable field, comparison against injected timestamps), and artifact reference validation (requires `artifact_id`, `version`, and at least one of `storage_path`/`uri`/`content_hash`).
- [x] Enforce configured resource limits for schema validation — maximum depth, field count, issue count, sample count, and payload size — returning bounded diagnostics that include the relevant path or validation area, without dumping entire payloads in errors.
- [x] Normalize validator inputs to canonical, JSON-safe, deterministic forms: accept supported enum values and strings where practical and normalize to canonical strings, and ensure public responses/metadata/audit records/logs/serialized payloads never expose enum objects directly.
- [x] Meet performance and safety constraints: low latency, no blocking I/O, no network calls, and no unbounded CPU spikes during normal market-data processing.
- [x] Document the structured logging schema, schema-validation invalid-field path format, schema-validation resource limits and performance expectations, schema examples for evidence packs/approval packets/registry entries/freshness metadata/artifact references, and official AI tool docstrings explaining what evidence the tool produces.
- [x] Write schema-validation tests verifying native helper results, required fields, input/output schemas, schema versioning, handoffs, evidence, approvals, registry entries, blocked actions, freshness, artifact references, invalid-field paths for flat and nested payloads, payload-size/depth/field-count/issue-count/sample-count limits, low-latency behavior with representative market-data payloads, and absence of blocking I/O or network access; verify official tools pass `validate_tool_response_schema` and standard response tests cover success envelope, error envelope, metadata, invalid schema, missing keys, execution timing, schema constants, and error code validation.

#### Security, Cryptography, and Payload Redaction

- [x] Implement `app/core/security.py` (re-exported by `app.utils`), before logging, settings, events, notifications, and audit-safe behavior are finalized, providing sensitive-key detection, scalar/text/mapping redaction, password hashing and verification, encryption key loading, encryption, decryption, and active secret-version selection.
  - Module provides each listed security capability
  - Agents must not call low-level helpers such as `normalize_timestamp`, `ensure_dir`, or `hash_password` unless a workflow explicitly approves that capability
  - `redact_mapping` is classified as a low-risk, read-only official AI tool only for approved audit/log-redaction workflows
  - `encrypt_data` remains a restricted support helper and is not attached to agents by default
- [x] Implement denylist-first, case-insensitive secret-key detection covering password, passwd, token, secret, key, credential, authorization, auth, API key, private key, access key, login, session, cookie, bearer, broker, and encryption-related patterns, with partial-key matching for common sensitive names.
  - Secret-like keys detected case-insensitively
  - Denylist includes the listed pattern categories and supports partial-key matching
- [x] Provide an explicit, narrow, field-specific allowlist mechanism for fields safe to log despite matching denylist patterns, with no broad wildcard exposure of secrets, audited through configuration/tests/documented approval, and failing closed on denylist/allowlist conflicts unless explicitly approved.
  - Redaction allowlist decisions are narrow, field-specific, and never grant broad wildcard exposure
  - Redaction helpers expose diagnostics showing which fields were redacted without exposing redacted values
- [x] Implement nested redaction for dictionaries and lists, preserving non-sensitive fields, stopping safely at `MAX_REDACTION_DEPTH` and marking truncated structures, without mutating input.
- [x] Apply redaction before sensitive values appear in logs, error responses, metadata, remediation text, tool responses, events, notifications, metrics, health checks, dead-letter diagnostics, exception text exposed to callers, or canonical JSON payloads (canonical JSON redacts by default unless a caller explicitly disables redaction in a trusted internal context, with redaction configuration exposed through documented options).
- [x] Implement password hashing with Argon2id as the preferred production algorithm (failing clearly if unavailable unless a separately approved fallback is configured) and constant-time password verification.
- [x] Implement Fernet-based symmetric encryption (`cryptography.fernet.Fernet`) for phase 1 when encryption is enabled: missing `cryptography` must not break module import but must fail encryption/decryption calls with a clear configuration error; encryption key loading never logs key material; environment-based keys use `ENCRYPTION_KEY` as a 32-byte URL-safe base64-encoded Fernet key; encryption/decryption failures never expose plaintext or key material.
- [x] Implement deterministic active secret-version selection choosing the highest numeric active version, raising `SecurityError` or returning structured `SECRET_VERSION_NOT_FOUND` when no active version exists, and failing closed with `SECRET_VERSION_CONFLICT` on duplicate active versions with the same numeric version.
- [x] Guard against expensive redaction recursion: use recursion depth protection for nested structures, and never log sensitive payloads during failure.
- [x] Document safe examples that do not contain real secrets, and document safe redaction allowlist use.
- [x] Write security tests verifying redaction, nested redaction, password hashing, password verification, Fernet key behavior, encryption round trip, invalid tokens, secret selection, `SECRET_VERSION_NOT_FOUND`, redaction denylist matching, audited allowlist exceptions, denylist/allowlist conflict behavior, metric labels rejecting sensitive/high-cardinality values, and meaningful branch coverage for validators and security helpers, proving common secret patterns do not leak and no secrets are logged.

#### Configuration Settings and Environment Loading

- [x] Implement `app/utils/settings.py`, before adapters and runtime configuration consumers, defining immutable typed `RuntimeSettings` including environment, log level, data directory, cache directory, audit directory, timezone, strict validation, logging configuration, auth configuration, Event Bus configuration, notification configuration, and observability configuration.
  - `load_runtime_settings` remains a support helper and is not attached to agents by default
  - Logging configuration includes optional log directory, file logging enablement, rotation max size, retained file count, retention deletion policy, console format selection, and color enablement
- [x] Load settings only through explicit calls, from mappings, with explicit precedence: mapping/function arguments, then environment variables, then `.env` file, then safe defaults; `.env` loading is optional and dependency-aware, and importing any `app.utils` module never reads `.env` files or mutates environment variables.
- [x] Implement `inject_runtime_settings` to inject settings into an explicitly supplied mutable target mapping, mutating only that mapping and returning it.
- [x] Validate settings deterministically: environment names validated, path settings use `Path` objects, invalid settings fail clearly with configuration errors, `strict_validation=True` escalates non-critical warnings to failures, `strict_validation=False` allows warnings to be returned/logged without failing load, and required settings have deterministic defaults where safe.
- [x] Resolve default runtime paths under `HARUQUANT_HOME` when configured (production deployments must configure it explicitly), defaulting to `data`, `cache`, and `audit` directories under the resolved home; when `HARUQUANT_HOME` is not configured, local/test defaults resolve under a deterministic `.haruquant` directory beneath the current working directory.
- [x] Support configurable OHLCV/validation parameters through settings: configurable datetime/open/high/low/close/volume/spread column names, configurable gap multiplier/spike threshold/issue-sample limit/returned-issue limit, resource-limit configuration for schema validators, and freshness validation accepting timestamp metadata, configurable timestamp field, injected `now`, and `max_age_seconds`.
- [x] Ensure missing optional dependencies (including pandas) never break import and fail only when the relevant feature/dataframe helper is called, surfaced via `HaruQuantConfigurationError`, `CONFIGURATION_ERROR`, or the standard tool error envelope.
- [x] Write settings tests verifying defaults, mapping load, invalid environments, `strict_validation`, path normalization, injection (returning the same mutated target mapping), and logger tests verifying file logging writes only to configured safe directories, log rotation by max file size, and retention deletion without deleting unrelated files.

#### Authorization and Permission Boundaries

- [x] Establish `app/utils/` as the shared utility foundation for HaruQuantAI, supporting higher-level domains (data, research, simulation, risk, portfolio, execution, analytics, governance, agentic workflows) with structured logging, standard tool envelopes, deterministic error codes, UTC-first timestamp/timezone normalization, safe path handling, dataframe/OHLCV helpers, OHLCV data-quality validation, schema/payload/risk-level/numeric-range/contract validation, security helpers, runtime settings, execution timing, tool-response schema constants, schema-version compatibility, resource-limit controls, lazy-loaded heavy optional dependencies, a stateless diagnostic-only data-quality boundary, string-serializable/enum-friendly canonicalization, and extensible domain error mapping.
- [x] Define the actor model for this domain: Agent/tool caller, Authorized tool caller, Authenticated principal, Workflow caller, Production module developer, Higher-level domain module, Human approver, Maintainer/reviewer, and Security reviewer, with the utils module providing auth primitives and validation helpers while the application/infrastructure layer owns external identity-provider integration.
- [x] Implement a shared authentication context model for internal tools, agents, workflows, and services, supporting principal ID, principal type, roles, permissions, scopes, tenant/environment context where applicable, request ID, workflow ID, and correlation ID, with validation helpers for authenticated principal context.
- [x] Implement `app/utils/auth.py`, before tool allowlists and side-effect permission checks, providing authorization helper checks for required roles, permissions, scopes, and tool names, denying by default when identity, permission, role, scope, or tool context is missing or malformed.
  - Auth helpers may validate identity context, roles, scopes, and permissions, but must not become the identity provider
  - Auth helpers do not validate external identity-provider tokens unless an explicit adapter is supplied by the application layer, and never contact external identity providers at import time
  - Auth helpers avoid hidden global mutable state
- [x] Require agents to be authorized through an explicit tool allowlist before accessing official AI tools, and require explicit permission checks before execution of side-effecting or sensitive utilities (including agent access to encryption/decryption, which requires explicit security approval, permission checks, and audit logging).
- [x] Return deterministic validation results or standard tool error envelopes at official tool boundaries, mapping auth failures to `PERMISSION_DENIED`, `INVALID_AUTH_CONTEXT`, or `AUTHORIZATION_FAILED`; redact auth context before logging, events, metrics, or error reporting, and make authentication/authorization events observable through logs, metrics, and sanitized audit events.
- [x] Accept sanitized auth context mappings or typed auth context objects plus required permissions/roles/scopes/tool names, returning allow/deny decisions with sanitized reason details.
- [x] Map redaction allowlist misuse to `SECURITY_ERROR` or a more specific deterministic security code.
- [x] Document auth context fields, authorization deny-by-default behavior, redaction denylist defaults, audited redaction allowlist configuration, and a warning against broad redaction allowlist rules.
- [x] Provide canonical JSON serialization for audit, hashing, caching, reproducible tests, and comparison workflows.
- [x] Write auth tests covering valid auth context, missing auth context, malformed auth context, missing role/permission/scope, denied-by-default behavior, and no token/credential leakage; write security tests verifying redaction denylist matching, audited allowlist exceptions, and denylist/allowlist conflict behavior.

#### Thread-Safe Local Event Bus

- [x] Implement `app/utils/event_bus.py`, before error routing and notification routing, providing request/workflow/generic ID/version/correlation ID/causation ID/idempotency helpers and Event Bus pub/sub primitives, with the utils module providing Event Bus contracts and an in-process implementation while production broker-backed adapters live in infrastructure modules or optional adapters.
  - Event publisher: a module or workflow that emits validated events
  - Event subscriber: a handler that receives events by topic or event type
  - Event Bus utilities route events but must not own application orchestration, place trades, approve trades, modify orders, activate live systems, or override kill switches
- [x] Define the standard event envelope including `event_id`, `event_type`, `event_version`, `source`, `severity`, `timestamp`, `request_id`, `workflow_id`, `correlation_id`, `causation_id`, `idempotency_key`, `payload`, and `metadata`; payloads must be JSON-serializable or fail validation clearly, and must be redacted before logging, metrics labeling, notification routing, audit serialization, or dead-letter forwarding.
- [x] Implement publish/subscribe with topic or event-type subscriptions, handler registration/unregistration, and error isolation so one failing subscriber does not silently prevent other subscribers from receiving the event; route subscriber failures to the error-routing mechanism with retry policy metadata and dead-letter routing for events that exceed retry limits.
  - Distributed broker adapters are not required to guarantee global ordering unless explicitly documented
- [x] Implement idempotency-key support with configurable TTL and configurable maximum cache size, where the default TTL is short enough to prevent memory growth but long enough to cover expected retry windows, entries store compact metadata rather than full payloads, duplicate detection may use hashes of sanitized canonical payloads without retaining sensitive payloads, expired keys are evicted deterministically (expired-first, then oldest, observable through logs/metrics), and cache state never exposes sensitive payloads/raw event bodies/tokens/credentials/approval packets/private data.
  - Idempotency-key storage does not grow without bound in long-running processes
  - Duplicate idempotency keys with different payload hashes fail safely or emit deterministic conflict diagnostics
- [x] Support correlation IDs across tool calls, logs, notifications, and metrics; expose bounded queue depth/handler backlog diagnostics including delivered, failed, retried, dead-lettered, dropped counts, and queue depth.
- [x] Implement explicit queue policies (fail-fast, bounded wait, or lossy-drop), with production defaulting to fail-fast for critical workflows, returning a deterministic `QUEUE_FULL` or `BACKPRESSURE_EXCEEDED` error immediately when the queue is full (`BACKPRESSURE_EXCEEDED` when the caller can retry, `QUEUE_FULL` for lower-level diagnostics), never silently dropping events unless the caller explicitly selected a lossy policy (allowed only for low-severity telemetry), with dropped events counted in metrics and logged with sanitized metadata.
  - Queue-full diagnostics include event type, source, severity, queue name/topic, queue depth, configured limit, request ID, workflow ID, and correlation ID, never raw event payloads by default
- [x] Keep the Event Bus import-light and dependency-aware: no network connections or external pub/sub client initialization at module import time; production external broker adapters are lazy-loaded, fail clearly when required optional dependencies are missing, and implement circuit breakers (a documented circuit-breaker pattern) whose diagnostics never include credentials, provider tokens, message bodies, or raw event payloads.
- [x] Ensure publish/subscribe/unregister/retry/dead-letter/idempotency-tracking operations are thread-safe and/or async-safe, handlers don't share mutable event payloads unless copied or contractually immutable, event versioning supports forward compatibility for consumers, and delivery diagnostics remain consistent under concurrent publishing.
- [x] Keep diagnostics and payloads bounded for large-scale use: avoid unnecessary deep copies, prefer summaries/counts/compact samples for agent-facing diagnostics, bound returned issue lists/samples, bound idempotency storage by TTL and max cache size, and bound Event Bus diagnostics to avoid oversized logs/metrics.
- [x] Map Event Bus failures to deterministic codes: `EVENT_PUBLISH_FAILED` for publish failures, `EVENT_HANDLER_FAILED` for subscriber failures, `EVENT_DEAD_LETTER_FAILED` for dead-letter routing failures; return queue-full errors immediately to publishers; keep backpressure errors distinct from subscriber execution errors, and don't misclassify subscriber execution errors as publish failures unless publish requires synchronous all-handler success.
- [x] Redact sensitive values before they appear in Event Bus payload logs or publication, ensure dead-letter event storage (if configured outside utils) receives redacted payloads by default, keep idempotency keys/event IDs/request IDs/workflow IDs/correlation IDs free of raw secrets and safe for logs/metrics, and ensure payload hashes used for idempotency conflict detection never allow reconstruction of sensitive payloads.
- [x] Document the Event Bus event envelope fields, idempotency TTL and max-cache-size behavior, queue-full/backpressure behavior, delivery/retry/dead-letter behavior, concurrency guarantees, whether the implementation is synchronous/asynchronous/dual-mode, that deterministic ordered delivery applies to the in-process Event Bus per event type (not necessarily distributed broker adapters), circuit-breaker configuration for external adapters, and each event type's ordering/durability/retry/loss-tolerance expectations.
- [x] Provide an in-process pub/sub mechanism suitable for local development, unit tests, and deterministic workflow tests, including disabled/no-op adapter behavior for tests/local development, guaranteed deterministic ordered handler execution per event type for reproducible test outcomes, and idempotency tracking testable with injected clocks or deterministic time controls.
- [x] Write Event Bus tests covering: publish success; subscription and unsubscription; subscriber failure isolation; retry and dead-letter behavior; idempotency keys, TTL expiration, max cache size enforcement, and duplicate key handling; concurrent publish, subscribe/unsubscribe, and retry/dead-letter behavior; payload serialization failure (missing event type, unserializable payload); queue-full behavior returning `QUEUE_FULL`/`BACKPRESSURE_EXCEEDED` and deterministic backpressure with dropped-event metrics and queue limit/backlog diagnostics; external adapter circuit-breaker closed/open/half-open states with fake adapters (including outage opening the circuit after threshold and half-open recovery not creating duplicate delivery); no secret leakage in event logs; fake clock/queue implementations for deterministic time/queue behavior; and disabled/no-op adapter behavior. Verify observability tests cover Event Bus metrics and queue-depth metrics, and that concurrent subscriber registration/unregistration during publishing does not corrupt handler lists or produce non-deterministic behavior.

#### Notification Dispatching and Delivery Sinks

- [x] Implement `app/utils/notifications.py`, before alert delivery is attached to workflows, providing shared status/severity/risk-level/environment-mode/auth/event/notification/health-state constants and notification routing primitives for email, Telegram, and desktop channels, with routing contracts and adapter boundaries rather than hard-coded provider credentials.
  - Notification recipient: a configured email, Telegram, or desktop recipient for alerts
  - Security/audit consumer: relies on redacted logs, metadata, tool responses, canonical JSON, events, notifications, and secret-safe error handling
  - Notification utilities may alert humans or systems but must not make trading, portfolio, risk, or strategy decisions
  - Auth, Event Bus, notification, and observability primitives are support helpers by default unless explicitly promoted to official AI tools
- [x] Disable email, Telegram, and desktop notifications unless explicitly configured for the current environment, with production desktop notifications disabled by default and no channel enabled in production without explicit per-environment configuration; configure notification recipients explicitly.
- [x] Implement severity-based, environment-specific notification routing with per-channel enablement/disablement through runtime settings, per-channel recipient configuration, and safe templates for alert title/summary/severity/source/timestamp/request ID/workflow ID/correlation ID rendered from sanitized data transfer objects rather than raw event payloads.
  - Templates support markdown and plain-text fallbacks for readability across email/Telegram/desktop clients, degrading to plain text when a channel doesn't support markdown
  - Markdown rendering escapes/sanitizes unsafe user-controlled content where applicable
  - Template rendering failures return deterministic notification failure diagnostics without exposing raw payloads
- [x] Redact secrets before message construction so routing never includes raw sensitive payloads; support rate limiting/throttling to avoid alert storms and deduplication of repeated alerts; produce delivery status results and publish notification success/failure events to the Event Bus; expose metrics for sent, failed, suppressed, throttled, and deduplicated notifications.
- [x] Implement email notifications with configurable SMTP/provider adapter settings and Telegram notifications with bot-token/chat-recipient configuration, neither logging credentials; keep desktop notifications disabled by default in production unless explicitly enabled.
- [x] Keep notification adapters lazy-loaded with no network client initialization at import time, implementing circuit breakers (a documented circuit-breaker pattern) for external adapters; notification delivery failures must not fail the original business operation unless the caller explicitly requires fail-closed alerting.
- [x] Accept alert severity, channel preferences, sanitized message template data, and routing policy as inputs; accept logging/notification/Event Bus/auth/observability configuration via runtime settings; return sent/suppressed/throttled/deduplicated/failed/disabled status; ensure desktop notification content never includes secrets.
- [x] Document runbook sections for Event Bus backpressure incidents, notification outage incidents, clock-drift incidents, and schema-validation performance regressions; expose Prometheus-compatible metrics including circuit-breaker state, queue depth, idempotency cache size, backpressure count, notification failures, and clock drift.
- [x] Ensure production code never leaks secrets in logs, errors, events, notifications, metrics, or health snapshots; importing any `app.utils` module never initializes notification clients; wall-clock timestamp serialization stays UTC-first and safe for logs/events/notifications/metrics/health snapshots/audit metadata.
- [x] Make notification routing, deduplication, throttling, rate-limit counters, and circuit-breaker state thread-safe and/or async-safe, with delivery diagnostics remaining consistent under concurrent alert bursts and routing remaining safe under repeated error bursts; keep optional notification provider dependencies lazy-loaded and isolate delivery failures from core utility functions unless explicitly configured otherwise; keep notification messages concise and actionable.
- [x] Isolate external notification provider outages through circuit breakers and deterministic error codes, with delivery observable through logs/metrics/sanitized events; map notification routing failures to `NOTIFICATION_FAILED` and configuration failures to `CONFIGURATION_ERROR`, distinguishing configuration failure, provider timeout, provider rejection, circuit-open state, throttling, and suppression; map unknown Event Bus/notification provider errors safely to deterministic error codes.
- [x] Redact sensitive values before they appear in notification templates; ensure authorization headers, email credentials, and Telegram bot tokens never appear in logs, metrics, events, or notifications; treat notification recipient lists as sensitive configuration; require explicit configuration for side-effecting notification/event adapter actions; ensure external notification/pub-sub adapters are lazy-loaded and fail closed when credentials are missing or malformed; reject metric labels containing raw IDs, arbitrary user strings, exception strings, notification recipients, provider tokens, or event payload values; exclude auth and notification provider credentials from Event Bus payloads by default.
- [x] Document notification routing rules for email/Telegram/desktop channels, concurrency guarantees, whether each adapter is synchronous/asynchronous/dual-mode, throttling and deduplication behavior, markdown/plain-text fallback behavior, and circuit-breaker configuration; ensure importing `app.utils` never imports pandas, cryptography, dotenv, broker SDKs, notification clients, pub/sub clients, Prometheus exporters, or network clients unless the specific feature is used; support test mode with fake adapters.
- [x] Write notification tests covering email/Telegram/desktop routing with fake adapters, disabled channel behavior, missing credentials, provider failure/timeout behavior, throttling and deduplication, concurrent routing and concurrent suppression/throttling/deduplication/adapter-failure behavior, thread-safe/async-safe throttling and deduplication state, markdown rendering and plain-text fallback, provider circuit-breaker closed/open/half-open states with fake adapters, and that notification content never leaks secrets after template rendering (including sensitive payloads being redacted before logging/notification routing, channel-disabled returning disabled/suppressed status without error, missing credentials failing safely without leaking configuration, provider timeout returning failed status with metrics, markdown rendering failure falling back to plain text, and unsupported formatting not failing the original operation unless fail-closed alerting is configured). Verify observability tests cover notification metrics, Grafana documentation/review checks confirm dashboards cover system health/tool health/Event Bus/notifications/errors/auth failures, a chaos-test profile covers notification provider failures and pub/sub adapter outages, and tests prove no sensitive values leak through logs/events/notifications/metrics/dead-letter diagnostics/schema errors/health checks.

#### Metrics Registry and Observability Sinks

- [x] Implement `app/utils/observability.py`, before production health gates are accepted, providing observability primitives for logs, metrics, health snapshots, and trace correlation, exposing Prometheus-compatible metrics for system health and defining Grafana dashboard expectations for operational health.
  - System operator: a maintainer who monitors logs, alerts, metrics, dashboards, and health status
  - Observability consumer: a developer, operator, or automated monitor that uses Prometheus/Grafana metrics
  - Observability utilities may report system health but must not decide operational actions without governance approval
  - Prometheus metrics export may be provided by application runtime while utils provides registration/recording helpers; Grafana dashboards may be maintained as version-controlled definitions
  - Metrics and logs are operational telemetry and must not contain raw market payloads, secrets, or approval-packet contents; Prometheus/Grafana metrics must include system-health visibility, not just business alerts
- [x] Cover the following with metrics: official AI tool call counts, success/error counts, and execution latency; validation failure counts by error code and source; Event Bus events published/delivered/failed/retried/dead-lettered/dropped/backpressured and queue depth/backlog; Event Bus idempotency cache size, eviction count, duplicate count, and conflict count; notification sent/failed/suppressed/throttled/deduplicated counts and delivery latency; logging error counts where detectable; settings load failures; security redaction failures; encryption/decryption failures (without exposing plaintext or key material); auth validation/authorization failures; circuit-breaker state transitions and current state; and clock-drift status where available.
- [x] Implement Prometheus-compatible alerting covering circuit-open state, queue saturation, dead-letter growth, notification failure rate, and clock drift where alerting is implemented; implement Grafana dashboards with panels for idempotency cache size, backpressure count, retry count, circuit-breaker state, and clock drift where dashboards are implemented, plus dashboard documentation covering system health, tool health, Event Bus health, notification health, error routing, auth failures, and data-quality validation health.
- [x] Bound metric labels: no high-cardinality raw IDs unless explicitly approved, and no secrets/raw payloads/tokens/API keys/personal data/notification recipients/approval packet contents/full exception strings/user-provided arbitrary values.
- [x] Support no-op operation when Prometheus dependencies are not installed, failing only when Prometheus-specific export features are used; ensure observability helpers are import-safe without Prometheus dependencies and that optional Prometheus dependencies are lazy-loaded.
- [x] Implement health snapshots including component status, last error timestamp, last successful event timestamp, degraded status, and critical status where applicable, distinguishing healthy/degraded/critical/unsupported/not-configured states deterministically and fast.
- [x] Implement wall-clock drift monitoring detecting significant NTP or system-clock offset beyond a configurable, environment-specific threshold: emit clock-drift warnings as observability events, produce degraded or critical health status depending on threshold, include measured offset/threshold/timestamp/source/component status in diagnostics, and treat no-op behavior (when the runtime cannot provide an offset source) as explicit and observable as unsupported/not-configured rather than healthy. Map clock-drift health failures to `CLOCK_DRIFT_DETECTED` where the error boundary requires a deterministic code.
- [x] Implement circuit breakers that open after a configurable threshold of consecutive failures/timeouts/provider errors, fail fast without repeatedly consuming threads/sockets/connection-pool capacity, support half-open recovery after a configurable cooldown, close after successful recovery, log state transitions with sanitized metadata, expose transitions through Prometheus-compatible metrics, include state in component health snapshots, and never expose credentials/tokens/message bodies/sensitive payloads in failures.
- [x] Accept metric names, bounded labels, numeric values, durations, and component health states; return metric registration/recording status where applicable; return healthy/degraded/critical/unsupported/not-configured status with sanitized details from health checks; ensure metrics recording failures never fail the original operation unless explicitly configured to fail closed, and that metrics collection adds low overhead.
- [x] Document a dashboard review checklist ensuring Grafana panels cover system health (not only trading/business outcomes), circuit-breaker metrics and health states, clock-drift monitoring and environment-specific thresholds, Prometheus metric names/labels/cardinality limits, Grafana dashboard expectations, and how to run observability in no-op/local/test mode; include production readiness checklists, operational runbooks, dashboard review checklists, and compatibility review notes; version-control Grafana dashboard definitions if implemented as files.
- [x] Map observability export failures to `OBSERVABILITY_ERROR` or `CONFIGURATION_ERROR`; make circuit-open failures observable through logs and metrics; redact sensitive values before they appear in Prometheus metrics or Grafana variables; avoid high-cardinality sensitive identifiers in Prometheus metrics; ensure Grafana dashboard variables never expose secrets; ensure clock-drift diagnostics never expose infrastructure secrets; keep logging output machine-parseable in production and human-readable enough for local development.
- [x] Write observability tests covering metrics registration, tool-call counters and latency histograms, auth failure metrics, no-op behavior when Prometheus dependencies are unavailable (using fake Prometheus exporters where exporter behavior must be exercised without external services), rejection of high-cardinality or sensitive metric labels, clock-drift healthy/degraded/critical/unsupported/not-configured states, and circuit-breaker metrics; write health-check tests covering healthy/degraded/critical/unsupported/not-configured states.

### Hardening Amendments

#### Sprint-pack execution boundary

Requirements:

- [x] Split Phase 1 implementation into approved sprint packs before editing code: 01A package/errors/standard, 01B logging/time/identity/paths, 01C settings/security/auth, 01D event bus/error routing/notifications, 01E observability/metrics, and 01F dataframe/data-quality/validators.
- [x] Each Phase 1 sprint pack must have its own dry run, approval, tests, rollback plan, and implementation report.
- [x] Ensure Utils imports do not depend on contracts that would create circular imports with Phase 1.5.
- [x] Document which Utils functions are allowed to be used by Core Contracts without importing heavy optional dependencies.

### Unit Tests Required

```text
tests/unit/app/test_package_imports.py
tests/unit/app/utils/test_utils_registry.py
tests/unit/app/utils/test_logger.py
tests/unit/app/utils/test_standard.py
tests/unit/app/utils/test_errors.py
tests/unit/app/utils/test_identity.py
tests/unit/app/utils/test_normalization.py
tests/unit/app/utils/test_paths.py
tests/unit/app/utils/test_dataframe_tools.py
tests/unit/app/utils/test_data_quality.py
tests/unit/app/utils/test_validations.py
tests/unit/app/utils/test_security.py
tests/unit/app/utils/test_settings.py
tests/unit/app/utils/test_auth.py
tests/unit/app/utils/test_event_bus.py
tests/unit/app/utils/test_error_routing.py
tests/unit/app/utils/test_notifications.py
tests/unit/app/utils/test_observability.py
tests/unit/app/utils
```

Test coverage:

- Cover every requirement in this phase with normal, edge, invalid-input, fail-closed, logging, schema, and regression tests as applicable.
- Preserve the project gate of at least 80% coverage for each affected file and package.
- Verify standard envelopes, deterministic error codes, import behavior, and ownership boundaries.

### Usage Examples Required

```text
tests/usage/app/services/01_utils.py
```

Usage examples must show:

- [x] `example_01_logging_and_tracing`: Demonstrate `configure_logging`, logger usage, and trace context propagation.
- [x] `example_02_standard_responses`: Demonstrate standardized success, error, validation, and exception response envelopes.
- [x] `example_03_identities`: Demonstrate request, workflow, correlation, event, idempotency, and custom prefixed IDs.
- [x] `example_04_datetimes_and_normalization`: Demonstrate UTC parsing, formatting, staleness checks, timestamp sequence validation, and execution timing.
- [x] `example_05_security_and_redaction`: Demonstrate payload redaction, password hashing, verification, encryption, and decryption without leaking secrets.
- [x] `example_06_dataframe_and_combinations`: Demonstrate dataframe alignment, record serialization, chunking, and parameter-combination helpers.
- [x] `example_07_data_quality`: Demonstrate OHLCV diagnostics and standard-envelope quality validation for valid and invalid records.
- [x] `example_08_validations`: Demonstrate input/output schema validation, evidence validation, registry validation, and failure envelopes.
- [x] `example_09_event_bus`: Demonstrate event envelope creation, publish/subscribe behavior, idempotency handling, and queue failure behavior.
- [x] `example_10_circuit_breakers_and_observability`: Demonstrate circuit-breaker states, health snapshots, metric recording, and Prometheus text export.
- [x] `example_11_notifications`: Demonstrate fake/local notification routing, throttling, disabled channels, and redacted alert payloads.
- [x] `example_12_paths`: Demonstrate safe path normalization, parent directory creation, traversal rejection, and approved-root checks.
- [x] The single usage file must be runnable as a script and organize separate examples as focused functions.
- [x] Examples must extensively cover the phase's official public capabilities, important edge cases, fail-closed paths, and standard envelope fields where applicable.

### Documentation and Logging Requirements

- [x] Log calls, validation failures, success, exception paths, and governed/fail-closed decisions with redacted metadata only.

### Quality and Documentation Standards

- [x] All Python modules and public functions/classes must have appropriate file-level and Google-style docstrings.
- [x] Implement unit tests for all modules and verify coverage is at least 80%.
- [x] The implementation must pass all CI quality gates (Ruff format, Ruff check, mypy --strict, pytest, and coverage at least 80%).
- [x] Update module README and active documentation for any architecture or API changes.

### Acceptance Checklist

- Done criterion: All 1186 checkbox tasks are implemented or explicitly deferred with a documented reason.
- Done criterion: Scope stayed within this phase and approved dependency surfaces.
- Done criterion: Public exports match the phase registry rules and do not expose unapproved helpers.
- Done criterion: Standard envelopes, metadata, request IDs, error codes, logging, and redaction rules are satisfied where applicable.
- Done criterion: Unit tests, usage examples, static typing, linting, formatting, and coverage gates pass.
- Done criterion: Active docs and changelog are updated for any implemented project meaning changes.
- Done criterion: Rollback path and implementation report are recorded before handoff.

### Commit Message

```text
feat(utils-foundation): implement core utility modules and safety envelopes

- Setup project logging under `app/utils/logger.py` with structured JSON format
- Implement StandardResponse and ToolMetadata schemas in `app/utils/standard.py`
- Define central domain exceptions and error code maps in `app/utils/errors.py`
- Create trace-identity, path-traversal validation, and datetime parsing utilities
- Implement Event Bus, fake notification channels, and Prometheus exporter
```

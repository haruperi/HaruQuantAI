# FEAT-HOST-LOGGING — Host telemetry

**Status:** Implemented. **Boundary:** no imports from other `app.*` features; consumers import `app.host.logging`.

| FR | Responsibility | Owning file |
| --- | --- | --- |
| FR-HOST-LOGGING-WORKER | Async bounded queue, flush and shutdown | `runtime.py` |
| FR-HOST-LOGGING-REDACTION | Path/secret sanitization and fingerprints | `security.py` |
| FR-HOST-LOGGING-ERROR-BOUNDARY | Fail-safe formatting and sink diagnostics | `formatting.py`, `sinks.py`, `runtime.py` |
| FR-HOST-LOGGING-FORMATTING | Millisecond event format and colors | `formatting.py` |
| FR-HOST-LOGGING-SINKS | app/errors/access files, Windows rotation | `sinks.py` |
| FR-HOST-LOGGING-RING-BUFFER | 2000-entry buffer, event-publish callbacks | `sinks.py` |
| FR-HOST-LOGGING-BOUND-LOGGER | `TelemetryLogger.bind`, severity methods | `runtime.py` |
| FR-HOST-LOGGING-CORRELATION | ContextVar request token functions | `runtime.py` |
| FR-HOST-LOGGING-EXPORTS | Stable exports and verification | `__init__.py`, `cli.py`, `__main__.py` |

## Workflow

1. `get_logger(name)` creates an inert adapter; the first emission lazily configures the worker when needed.
2. At host startup, `setup_logging(log_dir, publish_log=...)` creates the app-owned handlers.
3. The queue prepares redacted records, dispatches to file/console/ring sinks, and invokes the host-owned live-log callback.
4. `flush_logs()` drains pending records; `shutdown_logging()` stops the worker and releases only app-owned root handlers.

## Public API

Use `from app.host.logging import get_logger, setup_logging, flush_logs, shutdown_logging`. Only the feature's documented public API is exported from `__init__.py`. Internal constants and handler classes are imported from their owning modules by tests; no legacy aliases are retained. Run `uv run python -m app.host.logging --verify` for the CLI smoke test.

## Validation

`uv run --frozen pytest tests/unit/test_telemetry_logging.py --no-cov`; `uv run --frozen ruff check app/host/logging tests/unit/test_telemetry_logging.py`; `uv run --frozen mypy app/host/logging`.

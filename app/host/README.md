# Host Subsystem Telemetry (`app/host/logging.py`)

## Overview

The host telemetry engine provides centralized, non-blocking, credential-redacted logging and multi-sink routing for HaruQuantAI host and plugin processes.

Application modules obtain logger handles via `get_logger(__name__)` or the global `logger` instance without configuring sinks. The engine initializes lazily on the first runtime log emission, leaving import-time invocations completely inert.

## Core Capabilities

1. **Namespace Resolution & Lazy Bootstrap (`FR-HOST-LOGGER-RESOLUTION`)**:
   - `get_logger(__name__)` returns a lightweight `BoundLogger` without opening sinks or starting background threads.
   - Sinks and background worker start lazily upon the first actual emission.

2. **Immutable Bound Context (`FR-HOST-BOUND-LOGGER`)**:
   - `logger.bind(worker_id="w-01")` returns a new immutable `BoundLogger` instance with merged context.

3. **Credential Redaction (`FR-HOST-SECRET-REDACTION`)**:
   - Pre-emission regex scanners detect passwords, tokens, API keys, and bearer headers.
   - Values are replaced with deterministic SHA-256 fingerprint digests: `[REDACTED:<digest:12>]`.
   - Sensitive dictionary keys are omitted or masked.

4. **Multi-Sink Demultiplexing (`FR-HOST-MULTI-SINK-ROUTING`)**:
   - `app.log`: Aggregates all runtime logs.
   - `access.log`: Demultiplexes HTTP and network access events (tagged with `category="access"` or namespaces matching `uvicorn.access` / `*.access`).
   - `debug.log`: Captures all `DEBUG` level events.
   - `errors.log`: Captures all `ERROR` and `CRITICAL` events.

5. **Bounded Telemetry, Windows File Locking & 10 MB ZIP Rotation (`FR-HOST-BOUNDED-TELEMETRY`, `FR-HOST-WINDOWS-ROTATION`)**:
   - Files rotate upon reaching 10 MB (`10,000,000` bytes).
   - Under Windows, active file descriptors are closed before file rename.
   - Rolled files are compressed into `.zip` archives with deflated compression in the background, unlinking the raw rollover file.
   - Archives older than 10 days are pruned automatically.

6. **Asynchronous Non-Blocking Queue (`FR-HOST-ASYNC-QUEUE`)**:
   - Emissions enqueue into an in-memory queue (`maxsize=1024`).
   - Saturated queues drop telemetry non-blockingly, incrementing an observable drop counter without stalling quantitative execution.

7. **Request Correlation (`FR-HOST-REQUEST-CORRELATION`)**:
   - `request_context(request_id="...")` scopes metadata using `contextvars.ContextVar`, preventing cross-task leaks in async runtimes.

8. **Safe Error Boundary (`FR-HOST-SAFE-ERROR-BOUNDARY`)**:
   - Strips caller locals, environment variables, and raw tracebacks.
   - Preserves exception type, sanitized message, and bounded call-site frame locations `(file:line:function)`.

9. **Lifecycle Management & Teardown (`FR-HOST-LIFECYCLE-SYNC`, `FR-HOST-TEST-ISOLATION`)**:
   - `flush()` drains pending queued events.
   - `shutdown()` cleanly releases resources on process exit via `atexit`.
   - `configure_host_logging(tmp_path)` and `reset_logging()` provide complete isolation for test suites.

## Python API Usage

```python
from pathlib import Path
from app.host.logging import (
    configure_host_logging,
    get_logger,
    request_context,
    reset_logging,
)

# Optional explicit configuration (e.g. In entrypoints or test fixtures)
configure_host_logging(Path("data/logs"))

# Obtain logger and bind context
log = get_logger("app.strategy").bind(strategy_id="momentum-01")

with request_context(order_id="ord-555"):
    log.info("Submitting order", extra={"symbol": "EURUSD", "volume": 1.0})

# Clean shutdown
reset_logging()
```

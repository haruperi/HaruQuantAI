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

# Optional explicit configuration (e.g. in entrypoints or test fixtures)
configure_host_logging(Path("data/logs"))

# Obtain logger and bind context
log = get_logger("app.strategy").bind(strategy_id="momentum-01")

with request_context(order_id="ord-555"):
    log.info("Submitting order", extra={"symbol": "EURUSD", "volume": 1.0})

# Clean shutdown
reset_logging()
```

---

# Host SQLite Persistence (`app/host/persistance.py`)

## Overview

The host persistence layer provides authoritative SQLite database management and transactional storage for HaruQuantAI host services within `data/database/haruquantai.db`.

It enforces connection-per-operation isolation, foreign key constraints, busy wait timeouts, and serialized `BEGIN IMMEDIATE` write transactions to eliminate concurrency deadlocks.

> [!NOTE]
> `app/host/persistance.py` is an internal host data access engine. External consumer modules, CLI commands, and user entrypoints must never import `app/host/persistance.py` directly; all configuration settings operations must flow through `app/host/settings.py`.

## Core Capabilities

1. **Scoped Settings Keyset Pagination (`FR-HOST-SETTINGS-READ`)**:
   - `read_settings(scope, key=None, after_key=None, limit=100)` queries settings with deterministic lexicographical ordering.
   - Decodes stored JSON values into immutable `SettingRecord` instances.
   - Emits structured DEBUG telemetry (`FR-HOST-SETTINGS-READ`) without leaking values.

2. **Atomic Batch Settings Upserts (`FR-HOST-SETTINGS-UPDATE`)**:
   - `update_settings(scope, values)` applies batch upserts in a single transaction.
   - Unchanged canonical JSON preserves original `updated_at_utc` timestamps.
   - Emits structured INFO telemetry (`FR-HOST-SETTINGS-UPDATE`) upon commit.

## Internal Host API Usage

```python
from pathlib import Path
from app.host.persistance import SettingsStore

# Internal store usage within host subsystem
store = SettingsStore(Path("data/database/haruquantai.db"))
store.initialize()

# Atomically update scoped settings
changed = store.update_settings("system", {"theme": "dark", "refresh_rate": 60})

# Read scoped settings page
page = store.read_settings("system", limit=50)
for record in page.items:
    _ = (record.key, record.value)
```

---

# Host Settings Container & Dot-Access Interface (`app/host/settings.py`)

## Overview

The host settings subsystem provides the central configuration settings container and dot-accessible interface for HaruQuantAI operations. It encapsulates the authoritative SQLite persistence store (`SettingsStore`) to query, parse, and structure scoped application and host configuration records into memory.

It exposes a module-level `settings` singleton, enabling application services, quantitative engines, and operator diagnostic utilities to navigate configuration values cleanly via dot-notation (e.g. `settings.app_general.theme` or `settings.config_agents.gemini.model`) or dictionary indexing, without direct coupling to low-level persistence tables.

## Core Capabilities

1. **Scoped Record Loading & Key Normalization (`FR-HOST-SETTINGS-LOAD`)**:
   - `HostSettings.reload()` queries scoped records from the SQLite database.
   - Automatically normalizes dot-separated keys to valid Python attribute identifiers (`app.general` -> `app_general`), while preserving original key lookups.
   - Organizes scoped containers (`settings.application`, `settings.host`).
   - Emits structured INFO telemetry upon loading with count of items loaded.

2. **Recursive Dot & Dictionary Navigation (`FR-HOST-SETTINGS-DOT-ACCESS`)**:
   - Internal `_SettingsNode` instances recursively wrap nested dictionaries and lists.
   - Provides intuitive dot-notation (`settings.app_general.theme`), dictionary indexing (`settings["app_general"]`), `.get(key, default)`, and `in` membership testing.
   - Emits DEBUG telemetry when accessing setting attributes or scoped namespaces.

3. **Dynamic Reload & Persistence Updates**:
   - `settings.reload()` refreshes memory state from disk.
   - `settings.update(scope, values)` executes atomic transactional upserts in the SQLite store and refreshes in-memory structures.

## Python API Usage

```python
from app.host.settings import HostSettings, settings

# Use the global singleton directly
theme = settings.app_general.theme
gemini_model = settings.config_agents.gemini.model

# Scoped namespace access
port = settings.host.bound_port

# Dictionary-style lookup and defaults
timeout = settings.get("request_timeout", 30)

# Isolated instance for testing or alternative databases
custom_settings = HostSettings(db_path="path/to/isolated.db")
```

## CLI Diagnostics

Inspect loaded host settings via the diagnostic CLI:

```bash
uv run python -m app.cli
```

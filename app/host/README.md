# HaruQuantAI Host System

> **Authority:** This document owns the backend host runtime contracts, boot lifecycle, and host features.
> [ARCHITECTURE.md](../../docs/ARCHITECTURE.md) owns spatial and structural composability rules;
> [PROJECT.md](../../docs/PROJECT.md) owns system scope and traced requirements;
> [AGENTS.md](../../AGENTS.md) owns verification and engineering guidelines.

---

## 1. System Pair Overview

The HaruQuantAI Host is a decoupled, paired system providing universal runtime infrastructure:

```text
Backend Host (app/host/)                 Frontend Host (app/ui/app/host/)
========================================================================================
- Five-phase startup lifecycle            - SPA router and navigation chrome
- Process state and health monitoring      - WebSocket transport & event hub
- Session auth & token verification        - Session store & authentication UI
- Dynamic catalog discovery (AST/JSON)    - Catalog cache & dynamic schema renderers
- JSON-RPC / REST envelope handling        - Notification hub & error diagnostics
- Rotating JSON logging & secret redaction - Zero domain algorithms or market formulas
- Host database persistence (SQLite)
- Resource custody & background jobs
```

The host owns universal operational infrastructure. It contains **zero** quantitative domain algorithms, strategy meanings, or workspace workflow policies.

---

## 2. Boot Contract: Schema Version 2

The host implements boot snapshot **schema_version 2**, executing a clean five-phase lifecycle:

```text
[runtime]  -->  [services]  -->  [packages]  -->  [transport]  -->  [serving]
   |                |                 |                |                 |
Config, logs,   Storage verify,   Discovery &      ASGI routes,      Listening gate,
lease & port    sessions, jobs,   composition,     static assets,    server ready
reservation     event bus, db     slot bindings    WebSockets        published
```

### 2.1 Boot Phases

| Phase | Identifier | Responsibilities | Failure Policy |
| :--- | :--- | :--- | :--- |
| **1. Runtime** | `runtime` | CLI argument parsing, immutable `HostSettings` resolution, early log buffering, installation lease lock, and candidate port reservation. | Fail-closed (process exits with non-zero exit code). |
| **2. Services** | `services` | Relational SQLite database connection (`data/database/haruquantai.db`), schema verification, user/session repository, pub/sub event bus, job queue, and thread pool initialization. | Fail-closed for required services; optional services degrade gracefully. |
| **3. Packages** | `packages` | AST/JSON manifest discovery of workspaces and plugins, slot compatibility validation, composition graph creation. | Missing optional plugins reported as unavailable; workspace discovery succeeds. |
| **4. Transport** | `transport` | FastAPI router assembly, REST endpoints, WebSocket `/ws/updates` and `/ws/control` channels, and static SPA delivery configuration. | Fail-closed if core routes cannot mount; missing built UI reports transport warning. |
| **5. Serving** | `serving` | Uvicorn server socket binding, confirmed TCP listening gate, and final process state transition to `SERVER_READY`. | Fail-closed if port cannot be bound. |

### 2.2 Process States

The host process transitions through the following lifecycle states:

- `OFFLINE`: Process initialized but startup not yet started.
- `INITIALIZING`: Currently executing boot phases 1 through 5.
- `SERVER_READY`: Successfully bound to port and actively serving API/WebSocket requests.
- `DEGRADED`: Server is listening, but an optional background service encountered a non-fatal error.
- `FAILED`: Fatal error encountered during boot; server halts.
- `STOPPED`: Clean graceful shutdown completed.

### 2.3 Client Initialization Boundary

- **Decoupled Readiness:** Server readiness (`SERVER_READY`) is published as soon as the listening socket gate passes, completely independent of whether a frontend client or CLI connects.
- **Client Handshake:** Connected clients authenticate, attach to WebSocket updates, read initial state via `GET /api/v1/init-data`, and send an idempotent `/app-loaded` acknowledgment.
- **No Side-Effects:** Client acknowledgments never trigger backend strategy restoration, data acquisition, or global state mutation.

---

## 3. Host Feature Registry & Traceability

In accordance with the Five-Level Structural Hierarchy, each file in `app/host/` represents a traced feature (`FEAT-HOST-*`) containing traced functional requirements:

| Feature Identifier | Implementation File | Primary Responsibilities | Traced Operations (`FR-*`) | Verification Test Suite |
| :--- | :--- | :--- | :--- | :--- |
| `FEAT-HOST-BOOT` | `bootstrap.py`<br>`startup.py` | Phase coordination, lifecycle hooks, monotonic boot timing, and clean shutdown. | 5 boot phases, graceful SIGINT/SIGTERM handling, process state reporting. | `tests/host/test_lifecycle.py`<br>`tests/host/test_bootstrapper.py` |
| `FEAT-HOST-SESSION` | `sessions.py`<br>`security.py` | Operator authentication, PBKDF2-SHA256 password hashing, signed bearer tokens, revocation. | Loopback auto-login, session expiry, token verification, brute-force rate limits. | `tests/host/test_sessions.py` |
| `FEAT-HOST-TRANSPORT` | `http_server.py`<br>`envelope.py`<br>`contracts.py` | FastAPI application, uniform `{api_version, request_id, status, data, error}` envelope, WebSockets. | Request ID tracing, structured error responses, connection heartbeat. | `tests/host/test_webserver.py`<br>`tests/host/test_envelope.py` |
| `FEAT-HOST-CATALOG` | `catalog.py`<br>`packages.py`<br>`composition.py` | AST and JSON descriptor discovery, slot validation, composition graph, zero-plugin fallback. | Dynamic package discovery, slot matching, contract version checks. | `tests/host/test_catalog.py`<br>`tests/host/test_packages.py`<br>`tests/host/test_composition.py` |
| `FEAT-HOST-SETTINGS` | `settings.py` | Strongly typed host configuration, compare-and-set updates, change event broadcast. | Transactional updates, schema validation, secret masking. | `tests/host/test_settings.py` |
| `FEAT-HOST-LOGGING` | `logging.py` | Rotating JSON log file, early buffer replay, console output, secret redaction. | Secret masking, structured log format, log level filtering. | `tests/host/test_telemetry.py` |
| `FEAT-HOST-RESOURCES` | `resource_store.py`<br>`resources.py` | Shared Host Resource Custody (`host.resources@1.0.0`), digest verification, retention. | Immutable artifact storage, SHA-256 validation, uncoupled reads. | `tests/host/test_resource_store.py` |
| `FEAT-HOST-JOBS` | `jobs.py` | Background job execution, bounded concurrency, cancellation, task status tracking. | Task enqueue, task cancellation, progress reporting. | `tests/host/test_jobs.py` |
| `FEAT-HOST-REMOVAL` | `removal.py` | Reversible package uninstallation, quarantine journaling, dependency cascade calculation. | Atomic quarantine move, survivor validation, uninstallation rollback. | `tests/host/test_removal.py` |
| `FEAT-HOST-EVENTS` | `events.py` | In-process pub/sub event bus with sequence numbering and topic filtering. | Event publishing, subscription dispatch, buffer replay. | `tests/host/test_events.py` |
| `FEAT-HOST-COMMANDS` | `commands.py` | Typed command mediation and handler dispatch. | Bounded command execution, authorization checks. | `tests/host/test_commands.py` |

### 3.1 Host Capabilities

The host exposes explicitly typed capability slots to attached workspaces:

- `host.market_data@1.0.0` (`market_data.py`): Typed access to historical dataset registries and timeseries partition reading without exposing raw database handles.
- `host.network@1.0.0` (`network.py`): Bounded, rate-limited HTTP/HTTPS requests with retry policies, timeouts, and credential redaction for data-source plugins.

---

## 4. Multi-Level Persistence: Host Level

Host-level persistence is managed exclusively via `app/persistence/host.py` in the unified relational database:

```text
data/database/
`-- haruquantai.db             # Relational SQLite database
    |-- host_settings          # Scoped key-value store (scope, key, value, updated_at)
    |-- users                  # Operator accounts, password hashes (PBKDF2)
    |-- sessions               # Active bearer tokens, token hashes, expiry
    `-- audit_log              # Security events, administrative modifications
```

### 4.1 Host Persistence Invariants

1. **Transactional Field Updates:** Settings updates perform atomic compare-and-set operations with post-commit event broadcasts (`settings.changed`).
2. **Secret Redaction:** Fields marked sensitive are redacted from diagnostic logs, export dumps, and API responses.
3. **Database Migrations:** Schema migrations require explicit operator commands. Startup never performs destructive or silent automatic schema upgrades on existing stores.
4. **Backup on Upgrade:** The `--migrate-auth-schema` command produces an exclusive SQLite recovery snapshot under `data/database/backups/` before applying modifications.

---

## 5. Deployment and Execution

### 5.1 Starting the System

```bash
# Start Backend Host
uv run python app/main.py --port 8000 --data-dir data/

# Start Frontend UI Shell (Development)
npm --prefix app/ui run dev

# Run Headless CLI Client
uv run python -m app.cli --url http://127.0.0.1:8000 --page=login --json
```

### 5.2 Environment Configuration Overrides

| Environment Variable | Description | Default |
| :--- | :--- | :--- |
| `HARU_PORT` | Listening TCP port for ASGI server | `8000` |
| `HARU_HOST` | Listening interface binding | `127.0.0.1` |
| `HARU_DATA_DIR` | Absolute or relative path to application data root | `data/` |
| `HARU_PASSWORD` | Operator password for non-loopback authentication | (Empty / loopback-only) |
| `HARU_LOG_LEVEL` | Logging verbosity (`DEBUG`, `INFO`, `WARNING`, `ERROR`) | `INFO` |

---

## 6. Verification and Acceptance Matrix

| Verification Scope | Requirement | Command |
| :--- | :--- | :--- |
| **Host Lifecycle & Boot** | 5-phase boot execution and state transitions | `uv run pytest tests/host/test_lifecycle.py tests/host/test_bootstrapper.py` |
| **Authentication & Sessions** | Token hashing, session expiration, loopback login | `uv run pytest tests/host/test_sessions.py` |
| **Transport & Endpoints** | REST API envelope, WebSockets, error schemas | `uv run pytest tests/host/test_webserver.py tests/host/test_envelope.py` |
| **Catalog & Discovery** | AST parsing, manifest inspection, slot composition | `uv run pytest tests/host/test_catalog.py tests/host/test_packages.py tests/host/test_composition.py` |
| **Settings & Persistence** | Host SQLite settings, migrations, transactional updates | `uv run pytest tests/host/test_settings.py tests/persistence/test_host.py` |
| **Telemetry & Redaction** | Rotating JSON log, secret filtering, early buffering | `uv run pytest tests/host/test_telemetry.py` |
| **Resource Custody** | Shared artifact storage, digest verification | `uv run pytest tests/host/test_resource_store.py` |
| **Full Host CI Suite** | Complete host test suite with coverage | `uv run pytest tests/host/ tests/persistence/` |

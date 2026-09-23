# Host Domain Registry (`app/host/`)

The host is the HaruQuantAI platform shell — the counterpart of the SQX shell
(Java engine + embedded web server + shared web services) and the backend half
of the host pair with `app/ui/src/app/`. Workspaces and plugins plug into it;
it knows no domain by name (Law 5: discovery over knowledge).

## Feature registry

| Feature ID | Feature | Owning module | Status |
|---|---|---|---|
| FEAT-GATEWAY-LIFECYCLE | Engine lifecycle: serve, status probe, graceful shutdown; UI-satellite supervision | `bootstrapper.py`, `lifecycle.py` | implemented (web scope: `status` with CPU/RAM/platform sizing + graceful `shutdown`; desktop-satellite supervision N/A for the web architecture) |
| FEAT-GATEWAY-WEBSERVER | HTTP server, shared envelope, static UI serving with SPA fallback, domain route mounting | `webserver.py`, `envelope.py`, `http.py` | implemented (starlette/uvicorn with `CORSMiddleware`; domains mount from catalog manifests) |
| FEAT-GATEWAY-COMMANDS | Closed host command surface incl. validated OS mediation and sandboxed file exchange | `webserver.py`, `commands.py` | implemented (`health`, `status`, `app-loaded`, `open-link`, `copy`, `files/read`, `files/write`, `files/exists`, `files/list`, `files/delete`) |
| FEAT-GATEWAY-SESSIONS | Session/token issuance and verification | `sessions.py` | implemented (bearer tokens, 12 h TTL, in-memory — restart requires re-login; env password or documented research mode) |
| FEAT-GATEWAY-EVENTS | Channel pub/sub live-update hub | `events.py` | implemented (SSE `GET /api/v1/events?channels=…` + publish API; WebSocket may follow without contract change) |
| FEAT-GATEWAY-CATALOG | Domain/plugin discovery from self-describing manifests; manifest serving | `catalog.py` | implemented (startup snapshot from `app/workspace` + `app/plugins`; `GET /api/v1/catalog` marks each entry as mounted or manifest-only) |
| FEAT-GATEWAY-TELEMETRY | Dated file logging + per-request access log | `telemetry.py`, `webserver.py` | implemented (`data/logs/log_Y_M_D.log`; access lines carry method, path, status, request id — never payloads) |
| FEAT-GATEWAY-SETTINGS | Settings service: transactional load/save and push refresh | `settings.py` | implemented (`data/database/haruquantai.db`, scoped `host_settings` records with safe field updates; committed changes publish `settings.changed`) |

## Module inventory

Every file in this package, so the registry always matches disk truth:

| File | Role |
|---|---|
| `__init__.py` | package docstring (host boundary laws pointer) |
| `bootstrapper.py` | configuration (env, fail-closed), service assembly, uvicorn lifecycle |
| `envelope.py` | shared wire contract: success/error payloads, validation issues, request ids |
| `http.py` | shared endpoint helpers: request ids, envelope responses, JSON-body parsing |
| `webserver.py` | application wiring: routes, auth + access middlewares, SPA static, domain mounting |
| `sessions.py` | bearer-token session manager |
| `events.py` | channel bus, SSE endpoint, publish endpoint |
| `catalog.py` | manifest model/validation, scanner, catalog endpoint, route mounting |
| `settings.py` | SQLite scoped settings store, schema validation, endpoints, change events |
| `commands.py` | OS-mediation validation + sandboxed exchange files + endpoints |
| `lifecycle.py` | status probe + graceful shutdown endpoints |
| `telemetry.py` | dated file logging |
| `README.md` | this registry |

## Running

```text
uv run python -m app.main
```

Defaults: `127.0.0.1:8000` (frontend 3000), logs `data/logs`, settings
`data/database/haruquantai.db`, file-exchange jail `data/exchange`, UI dist
`app/ui/dist`, domain roots `app/workspace,app/plugins`.

Environment overrides: `HARUQUANTAI_HOST_ADDRESS`, `HARUQUANTAI_HOST_PORT`,
`HARUQUANTAI_HOST_LOG_DIR`, `HARUQUANTAI_HOST_PASSWORD`,
`HARUQUANTAI_DATABASE_PATH`, `HARUQUANTAI_EXCHANGE_ROOT`,
`HARUQUANTAI_DOMAIN_ROOTS`, `HARUQUANTAI_UI_DIST` (empty disables static
serving), `HARUQUANTAI_CORS_ORIGINS` (comma-separated allowed origins,
defaulting to `http://127.0.0.1:3000,http://localhost:3000`). Invalid values
fail closed at startup.

Auth: every `/api/*` route except `health`, `status`, and `auth/login`
requires `Authorization: Bearer <token>` from `POST /api/v1/auth/login`.
When `HARUQUANTAI_HOST_PASSWORD` is unset, tokens are issued without a
password (research mode) while enforcement stays on. HTTP `OPTIONS` requests
are exempt to allow CORS preflight.

## Boundary law

- The host owns the envelope, error shape, request IDs, and mounting — nothing
  else. No domain knowledge; no domain names in host code.
- Domain pairs (workspaces, plugins) mount beneath the host by self-describing
  `manifest.json` (id, kind, route_base, version, capabilities, optional route
  module exposing `create_routes()`) and handle their own route families.
- Duplicate domain IDs or colliding `route_base` declarations are rejected by
  `catalog.py` with structured `duplicate` issues, preventing route shadowing.
- In Starlette, route mounting is startup-bound. `GET /api/v1/catalog` returns
  the same immutable startup snapshot used for mounting. Its `mounted` flag is
  `false` for manifest-only entries. A new manifest or changed route requires
  host restart. Routes conflicting with a host endpoint are rejected with a
  structured `reserved_route` issue.
- UI readiness is tracked via `LifecycleState.ui_ready`: `POST /api/v1/app-loaded`
  records frontend initialization, transitioning `health` from `services.ui = pending`
  to `services.ui = ready`.
- The browser shell acquires an in-memory bearer session before signaling
  `app-loaded`. It reads and conditionally saves the editable global Settings
  menu fields under `ui`; a stale revision receives 409. Commits publish
  `settings.changed`, prompting clients to re-read. Passwords and license keys
  are not stored. Workspace settings remain with their workspace owners.
- The old `data/user/settings.json` is never read or written. JSON app presets
  belong in `data/presets/` when their owning features are implemented.
- Evidence basis for each feature is the clean-room ledger
  (`docs/dev/evidence/reimplementation.json`, gateway-domain records).

## Status

The eight backend host features are implemented. Host-pair integration covers
session startup, UI readiness, the startup-bound catalog, and shell preference
updates. Domain-specific UI synchronization still requires the owning backend
domain. Candidate verification for this integration is recorded in
`.agents/logs/2026-09-23T093052_host-integration-closure/`.

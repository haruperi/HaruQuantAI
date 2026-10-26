# Host transport gateway

The FastAPI application mounts `app.host.transport` at `/api/v1`. Start it with:

```powershell
uv run python -m app.main --reload
```

Responses contain the host `StandardResponse` fields and a `status` field (`success` or `error`) for the existing UI client. Invalid requests return 422, missing authentication 401, missing capabilities 403, missing records 404, revision conflicts 409, and unavailable services 503.

## Stopping and restarting

Press Ctrl+C once to stop the backend. The launcher allows five seconds for
in-flight connections to finish, then cancels remaining request tasks before
application cleanup. This also applies to restarts triggered by `--reload`.
The UI's `/api/v1/events` server-sent event connection stays open while the UI is
connected; without a shutdown deadline, it can keep Uvicorn waiting indefinitely.

When an open stream reaches the deadline, Uvicorn may log
`timeout graceful shutdown exceeded` as it cancels the request. The stream's
subscription is released and application shutdown continues. The deadline bounds
connection draining, not arbitrary synchronous work or application cleanup.

If an older process is already stuck at `Waiting for connections to close`,
press Ctrl+C a second time to force its exit, then restart with the updated code.
There is no need to close the terminal. When launching Uvicorn directly instead
of using `app.main`, supply the equivalent option explicitly:

```powershell
uv run uvicorn app.main:app --reload --timeout-graceful-shutdown 5
```

## Routes

| Handler | Methods and paths, relative to `/api/v1` |
| --- | --- |
| `_auth_route` | `GET /auth`, `POST /auth`, `POST /auth/login`, `GET /sessions/me` |
| `_meta` | `GET /status`, `GET /readiness`, `POST /app-loaded`, `GET /about`, `GET /constants`, `GET /specs` |
| `_cfg_route` | `GET /settings`, `PUT /settings`, `GET /settings/catalogue`, `PUT /settings/secrets`, `GET /auth/account`, `PUT /auth/account` |
| `_conn_route` | `GET /connections`, `POST /connections`, `POST /connections/test`, `DELETE /connections/{connection_id}`, `POST /connections/{connection_id}/test` |
| `_ws` | WebSocket `/ws` |

Authentication discovery, status, and readiness are public. Other routes require a UI session and the corresponding `session:read`, `host:read`, `settings:read/write`, or `connections:read/write/test/delete` capability. The configured application account receives all capabilities. CLI tokens are rejected by UI routes.

## Sessions

POST a JSON object containing `password` and optionally `username` to `/auth/login` or `/auth`. Successful login returns `data.token`, `data.peer_id`, and `data.expires_at`, and sets HttpOnly session and browser identity cookies. UI peer identities use `ui:<random-browser-id>`. Cookies and persisted sessions use a sliding 24-hour inactivity timeout and survive host restarts. HTTPS requests receive Secure cookies.

Send `Authorization: Bearer <token>` and retain the browser cookie. POST `{"action":"logout"}` to `/auth` to revoke the current session. WebSockets authenticate through cookies or the Authorization header, revalidate on each message, and respond to text `ping` with a JSON `pong`. Idle sockets close after 60 seconds. They do not yet broadcast application events.

The local development UI origins `http://localhost:3000` and `http://127.0.0.1:3000` are allowed with credentials. The UI transport includes cookies with requests. Other deployment origins require explicit CORS configuration.

## Settings

Settings reads omit secret values. The catalogue exposes secret presence through `configured` and supports dotted nested field paths. Updates use `expected_revision` and `changes`, for example:

```json
{"expected_revision": 3, "changes": {"app.general": {"theme": "dark"}}}
```

Secret field updates use `/settings/secrets`; account password changes use `/auth/account` and require the current password. Secret settings use the existing `SettingsManager` storage contract. Connection credentials use vault references instead.

## Connections and vault integration

`ServletConnection` stores immutable public connection records in the existing `host_entities` table with `entity_type="connection"`. Saving an existing ID returns a conflict. No database migration is performed.

Example public connection body:

```json
{
  "name": "Research exchange",
  "provider": "example",
  "kind": "exchange",
  "endpoint": "https://api.example.com/",
  "vault_refs": {"api_key": "vault:owned-reference"}
}
```

Inline passwords, tokens, and API keys are rejected by save. Credential-bearing URLs, query strings, fragments, and non-HTTP(S) endpoints are rejected. Vault references cannot be shared between saved connections. Delete revokes owned references before deleting metadata. A revocation failure retains the metadata for retry; vault revocation must be idempotent because SQLite and the vault cannot commit atomically.

Inject a production vault and real provider testers with `create_app(vault=..., connection_testers={"provider": async_tester})`, or pass them directly to `ServletConnection`. The vault implements `resolve(reference) -> str` and idempotent `revoke(reference) -> None`. Testers receive public metadata plus resolved `credentials`, perform a read-only authentication check, and return a boolean. They must not place orders or log credentials.

`test_connection()` accepts exactly one saved `connection_id` or inline connection mapping. Inline tests may include a `credentials` object, which is never persisted or echoed. Missing vault or tester integrations return unavailable. No production vault backend or provider authentication adapter is installed by this module.

## Network diagnostics

| Method | Behavior |
| --- | --- |
| `ping_endpoint(endpoint, timeout=5)` | HTTP HEAD probe of a local or remote endpoint; reports reachability, application health, status, and RTT. No redirects or response bodies are consumed. |
| `check_latency(endpoint, probes=3, timeout=5)` | Reports minimum, maximum, and mean RTT, failed probes, and failure percentage. |
| `diagnose_network(endpoint, timeout=5)` | Separates DNS failures from TCP socket connection failures. |
| `list()`, `save(metadata)`, `delete(connection_id)` | Manage saved public connection metadata through `HostPersistence`. |
| `test_connection(...)` | Runs the injected provider credential tester and reports authentication status and elapsed latency. |

Probes are limited to 1–20 attempts and timeouts to 30 seconds. `packet_loss_percent` measures failed HTTP probes, not ICMP packets. An HTTP 401 or 500 proves reachability while reporting unhealthy application status. Socket diagnostics test TCP connectivity, not TLS validity or provider authentication. Network diagnostic methods are Python APIs; no additional diagnostic HTTP routes are exposed yet.

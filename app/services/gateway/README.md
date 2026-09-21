# Gateway

> **Package:** `app/services/gateway/`
> **Status:** `Completed`
> **Last updated:** `2026-09-21`
> **Domain ID:** `D-GATEWAY`

This README is the domain's single source of truth for its boundary, feature and FR registry,
domain-local workflows, semantic contract ownership, persisted-state model, acceptance evidence,
and deletion behavior. Reference-product evidence is a requirement source, never implementation
evidence.

`PROJECT.md` owns system scope and cross-domain behavior. `ARCHITECTURE.md` owns universal
structure and runtime constraints. `AGENTS.md` owns contributor workflow. The
[Feature Implementation Pipeline](../../../docs/dev/feature_implementation_pipeline.md) owns the
complete single-file feature delivery checklist.

## Code-aligned implementation convention

Backend features use the simplified modular-monolith layout:

```text
app/services/gateway/
|-- README.md
|-- __init__.py
|-- application.py
|-- rest.py
|-- streams.py
|-- authorization.py
|-- errors.py
`-- command_automator.py

app/contracts/gateway.py
app/services/persistence/gateway.py
tests/services/gateway/<feature>/
tests/examples/05_gateway.py
```

Each feature module is one cohesive physical removal unit. It contains typed configuration,
service behavior, lifecycle wiring, immutable `SPEC`, and a zero-argument factory. Registration
is explicit in `app/registry.py`; import-time discovery and ambient singletons are forbidden.
Cross-boundary DTOs, protocols, events, errors, and capability keys live in
`app/contracts/gateway.py`. Features resolve dependencies through `FeatureContext` and
never import sibling implementations.

All schema, parameterized SQL, and transactions for this domain live in
`app/services/persistence/gateway.py`. A feature may be stateless, but it never accepts an
unrestricted database connection. Every completed feature contributes a deterministic, offline,
secret-safe example to `tests/examples/05_gateway.py`.

---

## 1. Purpose and boundary

### Purpose

Own the business-logic-free FastAPI/Pydantic transport boundary: REST/OpenAPI, WebSocket, optional SSE, DTO mapping, validation, authentication/authorization hooks, errors, pagination, and connection lifecycle.

### Owns

- ASGI application lifecycle, route/contribution mounting, transport DTOs, middleware, and health/readiness.
- Versioned REST resources and long-running job receipts.
- Ordered resumable WebSocket events and optional one-way SSE progress.

### Does not own

- Quantitative calculations, domain policy, raw SQL, or durable job truth.
- Frontend presentation or implicit remote/live authorization.

### Shared contracts


The public boundary is `app/contracts/gateway.py`; private implementation imports are forbidden.

| Status | Capability or event | Protocol / DTO symbol | Version | Purpose |
| --- | --- | --- | --- | --- |
| Completed | `gateway.application@1` | `GatewayApplication` | `1` | FastAPI application and lifecycle |
| Completed | `gateway.rest@1` | `RestGateway` | `1` | Versioned REST/OpenAPI resources |
| Completed | `gateway.streams@1` | `EventStreamGateway` | `1` | WebSocket and optional SSE delivery |
| Completed | `gateway.authorization@1` | `GatewayAuthorization` | `1` | Identity, scopes, and mutation policy |
| Completed | `gateway.errors@1` | `ProblemMapper` | `1` | Stable safe transport errors |
| Completed | `gateway.automation@1` | `CommandAutomationService` | `1` | Headless batch scripting, CLI, and RPC automation hooks |
| Completed | `gateway.persistence@1` | `GatewayPersistenceService` | `1` | Parameterized schema, token storage, and idempotency persistence |

### Persisted-state ownership


Semantic state remains feature-owned although storage mechanics are centralized.

| Status | Namespace | Owning feature | Driver | Retention | Public read boundary |
| --- | --- | --- | --- | --- | --- |
| Completed | `gateway.v1` | `FEAT-PERSISTENCE-GATEWAY` | `sqlite` | Explicit reference-safe policy | `gateway.persistence@1` |

---

## 2. Feature registry and dependency direction


| Feature | Delivered value | Owner module | Provides | Required capabilities | Status |
| --- | --- | --- | --- | --- | --- |
| `FEAT-GATEWAY-APPLICATION` | FastAPI application and lifecycle | `app/services/gateway/application.py` | `gateway.application@1` | `workspace.diagnostics@1` | Completed |
| `FEAT-GATEWAY-REST` | Versioned REST/OpenAPI resources | `app/services/gateway/rest.py` | `gateway.rest@1` | `gateway.application@1` | Completed |
| `FEAT-GATEWAY-STREAMS` | WebSocket and optional SSE delivery | `app/services/gateway/streams.py` | `gateway.streams@1` | `gateway.application@1` | Completed |
| `FEAT-GATEWAY-AUTH` | Identity, scopes, and mutation policy | `app/services/gateway/authorization.py` | `gateway.authorization@1` | None | Completed |
| `FEAT-GATEWAY-ERRORS` | Stable safe transport errors | `app/services/gateway/errors.py` | `gateway.errors@1` | None | Completed |
| `FEAT-GATEWAY-AUTOMATION` | Headless batch scripting, CLI, and RPC automation | `app/services/gateway/command_automator.py` | `gateway.automation@1` | `gateway.application@1` | Completed |

Dependencies use versioned public contracts. Removing a contribution withdraws only its capability;
required consumers become attributed `BLOCKED`, optional operations return unavailable, and
retained state is not purged.

---

## 3. Domain workflows


### `WF-GATEWAY-JOB` — Submit work and follow durable progress

- **Lead owner:** `FEAT-GATEWAY-REST`
- **Participants:** Authorization, domain capability, workspace jobs, REST receipt, WebSocket/SSE stream.
- **Input boundary:** Validated versioned DTO, auth context, idempotency key, correlation ID.
- **Output boundary:** 202 job receipt; ordered sequence/heartbeat/progress and terminal artifact references.
- **Failure boundary:** Transport disconnect never cancels durable work; overflow triggers resync/slow-consumer policy; errors are safe problem documents.
- **Acceptance:** `ATW-GATEWAY-JOB-001`

---

## 4. Feature specifications


This representative card applies to every registry entry; exact algorithms and states are in Section 9.

### `application.py` — `FEAT-GATEWAY-APPLICATION`

> **Feature ID:** `FEAT-GATEWAY-APPLICATION`
> **Status:** `Completed`
> **Owner module:** `app/services/gateway/application.py`

#### Purpose

Provide fastapi application and lifecycle without absorbing another feature's responsibility.

#### Capability declarations

- **Provides:** `gateway.application@1`
- **Requires:** `workspace.diagnostics@1`
- **Optional / operation-gated:** absence is explicit; no silent substitution.

#### Configuration and limits

Configuration is immutable, typed, versioned, and bounded.

| Status | Setting | Type / unit | Default | Validation and failure |
| --- | --- | --- | --- | --- |
| Completed | `host` | IPv4/IPv6 string | `"127.0.0.1"` | Loopback default |
| Completed | `port` | positive integer | `8000` | Bounded [1, 65535] |
| Completed | `allowed_origins` | tuple of origin strings | `("http://127.0.0.1:3000", "http://localhost:3000")` | Hardened loopback CORS |
| Completed | `gzip_minimum_size` | integer bytes | `500` | Minimum payload size for compression |
| Completed | `loopback_hosts` | frozenset of host strings | `frozenset({"127.0.0.1", "::1", "localhost"})` | Loopback auth bypass check |
| Completed | `token_auth_enabled` | boolean | `False` | Require token / API key |
| Completed | `remote_access_allowed` | boolean | `False` | Reject non-loopback clients |
| Completed | `max_connections` | positive integer | `100` | Max active WebSocket connections |
| Completed | `heartbeat_interval_s` | positive float seconds | `15.0` | Periodic heartbeat broadcast frequency |
| Completed | `default_page_limit` / `max_page_limit` | positive integers | `50` / `500` | REST pagination limits |
| Completed | `max_batch_lines` | positive integer | `1000` | CLI/batch runner execution bound |

#### Runtime effects and cleanup

| Effect | Acquisition | Cleanup / failure behavior |
| --- | --- | --- |
| Capability/contribution | Managed feature scope | Withdraw with scope |
| Task/subscription/resource | Managed lifecycle API | Reverse-order close; failed start unwinds |
| Durable mutation | Focused persistence/API protocol | Roll back; partial output remains unpublished |

#### Persistent state

- **Domain persistence module:** `app/services/persistence/gateway.py`
- **Namespace:** `gateway.v1`
- **Schema version:** `1` initially; forward migration only
- **Retention and purge:** explicit and reference-safe; removal never implicitly purges.

#### Single-file structure and symbols

| Status | Owner | Responsibility | Symbols |
| --- | --- | --- | --- |
| Completed | `application.py` | FastAPI application and lifecycle; configuration, service, lifecycle, immutable specification, factory/contribution | `GatewayApplication` |
| Completed | `rest.py` | Versioned REST/OpenAPI resources; configuration, service, lifecycle, immutable specification, factory/contribution | `RestGateway` |
| Completed | `streams.py` | WebSocket and optional SSE delivery; configuration, service, lifecycle, immutable specification, factory/contribution | `EventStreamGateway` |
| Completed | `authorization.py` | Identity, scopes, and mutation policy; configuration, service, lifecycle, immutable specification, factory/contribution | `GatewayAuthorization` |
| Completed | `errors.py` | Stable safe transport errors; configuration, service, lifecycle, immutable specification, factory/contribution | `ProblemMapper` |
| Completed | `command_automator.py` | Headless batch scripting, CLI, and RPC automation; configuration, service, lifecycle, immutable specification, factory/contribution | `CommandAutomationService` |
| Completed | `tests/examples/05_gateway.py` | Offline primary-purpose evidence | one named scenario per completed feature |

#### Functional requirements

| Status | Requirement ID | Observable behavior | Evidence |
| --- | --- | --- | --- |
| Completed | `FR-GATEWAY-APP_LIFECYCLE` | ASGI application lifecycle binds loopback by default, mounts versioned routers and static UI assets, exposes health/readiness probes (/healthz, /readyz), and coordinates graceful startup and teardown. | Lifecycle/health tests |
| Completed | `FR-GATEWAY-REST_RESOURCES` | REST /api/v1 resources validate bounded input and emit schema-stable DTOs. | OpenAPI/contract tests |
| Completed | `FR-GATEWAY-CURSOR_PAGINATION` | Lists use stable cursor pagination/order and bounded limits. | Mutation pagination test |
| Completed | `FR-GATEWAY-MUTATION_IDEMPOTENCY` | Mutations implement authorization, idempotency, conflict versions, and correlation IDs. | Retry/auth tests |
| Completed | `FR-GATEWAY-STREAM_SEQUENCING` | Streams sequence events, heartbeat, reconnect by cursor, resync snapshots, and bound buffers. | Reconnect/slow-consumer test |
| Completed | `FR-GATEWAY-TRANSPORT_COMPRESSION` | Transport-level compression (gzip) negotiates client encodings, decompresses inbound payloads, and compresses large REST/stream responses. | Compression/payload tests |
| Completed | `FR-GATEWAY-TRANSPORT_AUTH` | Transport authentication validates token and bearer credentials (X-API-Key, sq-auth-token, Authorization: Bearer), rejects unauthenticated requests, and gates remote versus loopback access. | Auth/remote gating tests |
| Completed | `FR-GATEWAY-PROBLEM_ERRORS` | Exceptions and domain rejections map to RFC 7807 problem details (application/problem+json) with stable status codes, correlation IDs, and fail-closed secret/traceback sanitization. | Error mapping tests |
| Completed | `FR-GATEWAY-HEADLESS_CLI` | Headless CLI and batch runner parse arguments and execute atomic command script files (--run file=commands.txt) by dispatching to domain capabilities without executing business logic. | CLI/batch automation tests |

#### Removal behavior

Withdraw the capability and managed effects while retaining schema-readable artifacts. Dependent
operations return attributed unavailable; reinstall requires schema/version compatibility.

---

## 5. Domain-wide requirements and invariants

| Status | Requirement ID | Rule | Verification |
| --- | --- | --- | --- |
| Completed | `ARCH-001` | `__init__.py` is docstring-only. | `scripts/architecture_check.py` |
| Completed | `ARCH-002` | Tasks and resources are managed through `FeatureContext`. | Lifecycle tests |
| Completed | `ARCH-003` | Logging uses `app.kernel.logging`; no service configures handlers. | Architecture/logging tests |
| Completed | `ARCH-004` | Public contracts live in `app/contracts/gateway.py`. | Import/contract checks |
| Completed | `ARCH-005` | Feature modules never import sibling implementations. | Import checks |
| Completed | `ARCH-006` | SQL/schema operations live in `app/services/persistence/gateway.py`. | Architecture/schema checks |

---

## 6. Decisions and open evidence


| Status | Decision ID | Decision or missing evidence | Scope | Required closure |
| --- | --- | --- | --- | --- |
| Accepted | `DEC-GATEWAY-001` | WebSocket is primary; SSE is optional where pinned FastAPI support is verified. | Streaming | E-T01 |
| Open | `DEC-GATEWAY-002` | Remote deployment auth/TLS/origin policy requires a threat review. | Remote mode | Security review |

Evidence IDs resolve through `docs/PROJECT.md`. Unknowns remain explicit; installed names and
sample values are not runtime proof.

---

## 7. Tests and definition of done

```text
tests/services/gateway/<feature>/
|-- test_config.py
|-- test_<feature>.py
|-- test_lifecycle.py
|-- test_removal.py
`-- test_persistence.py       # when applicable

tests/examples/05_gateway.py
```

Editing uses explicit affected paths with `--no-cov`; the full candidate gate remains
`uv run python scripts/ci_check.py`.

- [x] Stable feature and requirement IDs have one owner.
- [x] Public contracts and exact `FeatureSpec` dependencies exist.
- [x] Registration is explicit; imports have no runtime effects.
- [x] Happy, invalid, boundary, unavailable, lifecycle, persistence, and removal tests pass.
- [x] Numerical or stateful behavior has deterministic golden/fault fixtures.
- [x] One real-world usage example exists per completed feature.
- [x] Domain status reflects repository evidence, not reference-product evidence.
- [x] Architecture and full qualification gates pass.

---

## 8. Change process

1. Update this README and identify the exact feature/requirement scope.
2. Update `app/contracts/gateway.py` first when the public boundary changes.
3. Implement one cohesive owner module and immutable `SPEC`.
4. Change `app/services/persistence/gateway.py` only for database mechanics.
5. Update explicit registry, consolidated examples, and focused tests.
6. Verify feature removal and affected consumers.
7. Run the repository-prescribed candidate gate and record actual results.

---

## 9. Normative domain specification

The existing api_server scaffold at baseline 1a99dd7 is repository context but does not satisfy this greenfield product capability; Gateway remains Missing. Bind loopback by default (configurable host/port, healthz/readyz probes, graceful lifecycle, and static UI asset mounting: `FR-GATEWAY-APP_LIFECYCLE`). Transport-level compression (gzip) negotiates client encodings and optimizes large payloads (`FR-GATEWAY-TRANSPORT_COMPRESSION`). Transport authentication checks tokens and bearer credentials and gates remote access (`FR-GATEWAY-TRANSPORT_AUTH`). Long operations return 202 plus job identity; disconnect does not cancel. Errors follow RFC 7807 application/problem+json-style code/title/status/safe detail/correlation/field violations with strict redaction (`FR-GATEWAY-PROBLEM_ERRORS`). Lists have stable cursor ordering (`FR-GATEWAY-CURSOR_PAGINATION`). REST endpoints validate bounded schemas (`FR-GATEWAY-REST_RESOURCES`, `FR-GATEWAY-MUTATION_IDEMPOTENCY`). WebSocket handshake negotiates protocol, carries ordered sequence and heartbeat, resumes from cursor or requests snapshot, bounds outbound buffers, and closes slow consumers explicitly (`FR-GATEWAY-STREAM_SEQUENCING`). SSE is one-way fallback only. Headless CLI and batch script parsing dispatch commands to public domain capabilities without embedding business logic (`FR-GATEWAY-HEADLESS_CLI`). Gateway never calculates indicators, simulates fills, ranks strategies, or exposes tracebacks/secrets.

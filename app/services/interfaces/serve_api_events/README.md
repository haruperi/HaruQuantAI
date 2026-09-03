# Serve API Events — FEAT-IFACE-SERVE_API_EVENTS

> Runtime-validated feature specification. `scripts/validate_feature_docs.py`
> checks this document against `manifest.py` on every run. The domain-level
> registry lives in `app/services/interfaces/README.md`.

## Purpose

Provide the composable transport foundation for HaruQuantAI's external
boundary. The feature serves API version negotiation, OpenAPI manifest
projection, compatibility and deprecation reporting, optimistic concurrency
validation, idempotent mutation deduplication, asynchronous job references,
artifact download validation, and the bounded SSE event buffer with replay
cursors and retention expiry. It contains no business workflow, resolves no
business capability, and never imports a business-domain implementation.
Kernel capability absence is translated into the stable
`CAPABILITY_UNAVAILABLE` `InterfaceFailure` result.

## Domain

interfaces

## Provides

| Capability bundle | Runtime identifier |
| --- | --- |
| ServeApiEventsCapability | `interfaces.serve-api-events@1` |

## Required Capabilities

None. The transport foundation is self-contained; vertical-slice gateway
features declare their own business dependencies.

## Optional Capabilities

None.

## Configuration

| Key | Type | Default | Description |
| --- | --- | --- | --- |
| `supported_api_versions` | list of vN labels | `["v1"]` | Served API version labels. |
| `server_prefixes` | list of paths | `["/api/v1"]` | Server base paths reported by the OpenAPI manifest. |
| `stream_retention_events` | integer >= 1 | `1000` | Maximum retained event envelopes before eviction. |
| `stream_replay_batch_limit` | integer 1..10000 | `100` | Maximum events returned per replay batch; larger replay requests are clamped. |
| `event_payload_max_bytes` | integer >= 1 | `65536` | Maximum serialized event payload size in bytes. |

Unknown keys are rejected with `ValueError`.

## Runtime Effects

- Creates exactly one in-memory `ServeApiEventsTransport` (HTTP boundary +
  event stream buffer) per mounted feature generation; no process-global
  singleton.
- Registers exactly one scope cleanup callback (`transport.close`) so
  disposal clears the idempotency registry, job registry, and retained
  events; repeated disposal is safe.
- Starts no sockets, listeners, background tasks, or servers, and performs
  no I/O at import time.
- Owns the raw-ASGI mounting surface (`asgi.py`,
  `create_api_asgi_app(registry)`): it serves `GET /api/v1/market/ticks`
  (JSON snapshot envelope) and `GET /api/v1/market/ticks/stream` plus the
  adopted alias `GET /api/v1/data/snapshot-stream` (SSE `StreamEvent`
  frames), resolving `interfaces.observe-market-data@1` per request and
  translating absence to the stable `CAPABILITY_UNAVAILABLE` envelope.
  `uv run haruquantai` composes the runtime and serves this adapter;
  request-scoped racing tasks are released in the handler's teardown.

## Persistent State

None. All registries and the event buffer are process-local and are
cleared on disposal.

## Functional Requirements

| Requirement | Requirement statement | Usage-harness scenario |
| --- | --- | --- |
| FR-IFACE-SAE-001 | Serve a version-filtered OpenAPI manifest per configured API label and reject unsupported labels. | manifest + version negotiation |
| FR-IFACE-SAE-002 | Report client compatibility and active deprecations against the served API version. | compatibility check |
| FR-IFACE-SAE-003 | Assign strictly monotonic sequences and deterministic cursor IDs to published events. | sequence assignment |
| FR-IFACE-SAE-004 | Replay ordered batches from a cursor with `has_more` signaling, clamped by the configured batch limit. | replay batch |
| FR-IFACE-SAE-005 | Enforce bounded retention and signal expired cursors for resync. | retention expiry |
| FR-IFACE-SAE-006 | Execute a mutation exactly once per idempotency scope, replaying the cached response on repeats. | idempotency dedup |
| FR-IFACE-SAE-007 | Validate optimistic concurrency tokens without partial mutation. | concurrency validation |
| FR-IFACE-SAE-008 | Track asynchronous job lifecycle references with bounded progress. | job references |
| FR-IFACE-SAE-009 | Validate artifact downloads against committed state and storage-root containment. | artifact validation |
| FR-IFACE-SAE-010 | Translate capability absence into the stable CAPABILITY_UNAVAILABLE failure with no mutation. | unavailable translation |

Run the bounded executable demonstration with:

```powershell
uv run python -m app.services.interfaces.serve_api_events.transport
```

## Failure Behavior

- Unsupported API version label raises `ApiIncompatibleError` carrying the
  supported labels (wire code `UPGRADE_REQUIRED`).
- Stale concurrency tokens raise `VersionConflictError` with the expected
  and current versions (wire code `VERSION_CONFLICT`); no mutation runs.
- An in-flight duplicate idempotency key raises `IdempotencyConflictError`;
  a previously failed key replays its recorded failure code and never
  re-executes.
- Expired, unknown, or invalid replay cursors raise
  `EventCursorExpiredError` (wire code `EVENT_CURSOR_EXPIRED`) so consumers
  resync from authoritative state.
- Unknown jobs raise `JobNotFoundError`; out-of-range progress raises
  `ValueError`.
- Uncommitted, missing, or path-traversing artifacts raise
  `ArtifactAccessDeniedError` without reading outside the storage root.
- Oversized event payloads and empty labels are rejected before any state
  changes.
- Use after disposal raises `InterfaceError` with code `TRANSPORT_CLOSED`;
  repeated disposal is a no-op.
- Kernel capability absence translates to `InterfaceFailure` code
  `CAPABILITY_UNAVAILABLE` and performs no mutation.

## Removal Behavior

Disabling or physically removing the feature withdraws exactly the
`interfaces.serve-api-events@1` capability: Python consumers receive
`CapabilityUnavailableError` from capability resolution and external
surfaces translate it to the stable `CAPABILITY_UNAVAILABLE` failure. The
scope-owned disposal clears the mutation registry, job registry, and
retained events; no tasks or listeners are created, so nothing leaks.
Unrelated features remain active. The feature owns no durable state, so
removal involves no data migration or purge.

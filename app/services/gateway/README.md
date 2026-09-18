# Gateway

> **Package:** `app/services/gateway/`
> **Status:** `Missing`
> **Last updated:** `2026-09-18`
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
`-- errors.py

app/contracts/gateway.py
app/services/persistence/gateway.py
tests/services/gateway/<feature>/
tests/examples/gateway_usage.py
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
secret-safe example to `tests/examples/gateway_usage.py`.

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
| Missing | `gateway.application@1` | `GatewayApplication` | `1` | FastAPI application and lifecycle |
| Missing | `gateway.rest@1` | `RestGateway` | `1` | Versioned REST/OpenAPI resources |
| Missing | `gateway.streams@1` | `EventStreamGateway` | `1` | WebSocket and optional SSE delivery |
| Missing | `gateway.authorization@1` | `GatewayAuthorization` | `1` | Identity, scopes, and mutation policy |
| Missing | `gateway.errors@1` | `ProblemMapper` | `1` | Stable safe transport errors |

### Persisted-state ownership


Semantic state remains feature-owned although storage mechanics are centralized.

| Status | Namespace | Owning feature | Driver | Retention | Public read boundary |
| --- | --- | --- | --- | --- | --- |
| Missing | `gateway.v1` | `FEAT-GATEWAY-APPLICATION` and registry peers | `sqlite` | Explicit reference-safe policy | `gateway.application@1` |

---

## 2. Feature registry and dependency direction


| Feature | Delivered value | Owner module | Provides | Required capabilities | Status |
| --- | --- | --- | --- | --- | --- |
| `FEAT-GATEWAY-APPLICATION` | FastAPI application and lifecycle | `app/services/gateway/application.py` | `gateway.application@1` | `workspace.diagnostics@1` | Missing |
| `FEAT-GATEWAY-REST` | Versioned REST/OpenAPI resources | `app/services/gateway/rest.py` | `gateway.rest@1` | `gateway.application@1` | Missing |
| `FEAT-GATEWAY-STREAMS` | WebSocket and optional SSE delivery | `app/services/gateway/streams.py` | `gateway.streams@1` | `workspace.jobs@1` | Missing |
| `FEAT-GATEWAY-AUTH` | Identity, scopes, and mutation policy | `app/services/gateway/authorization.py` | `gateway.authorization@1` | None | Missing |
| `FEAT-GATEWAY-ERRORS` | Stable safe transport errors | `app/services/gateway/errors.py` | `gateway.errors@1` | None | Missing |

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
> **Status:** `Missing`
> **Owner module:** `app/services/gateway/application.py`

#### Purpose

Provide fastapi application and lifecycle without absorbing another feature's responsibility.

#### Capability declarations

- **Provides:** `gateway.application@1`
- **Requires:** `workspace.diagnostics@1`
- **Optional / operation-gated:** absence is explicit; no silent substitution.

#### Configuration and limits

Configuration is immutable, typed, versioned, and bounded. Reference sample values are not defaults.

| Status | Setting | Type / unit | Default | Validation and failure |
| --- | --- | --- | --- | --- |
| Missing | `schema_version` | positive integer | `1` | Reject incompatible versions |
| Missing | `operation_timeout_s` | finite seconds | operation-specific | Positive and bounded |
| Missing | `resource_limit` | positive integer | deployment-specific | Reject unbounded/nonpositive |

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
| Missing | `application.py` | FastAPI application and lifecycle; configuration, service, lifecycle, immutable specification, factory/contribution | `GatewayApplication` |
| Missing | `rest.py` | Versioned REST/OpenAPI resources; configuration, service, lifecycle, immutable specification, factory/contribution | `RestGateway` |
| Missing | `streams.py` | WebSocket and optional SSE delivery; configuration, service, lifecycle, immutable specification, factory/contribution | `EventStreamGateway` |
| Missing | `authorization.py` | Identity, scopes, and mutation policy; configuration, service, lifecycle, immutable specification, factory/contribution | `GatewayAuthorization` |
| Missing | `errors.py` | Stable safe transport errors; configuration, service, lifecycle, immutable specification, factory/contribution | `ProblemMapper` |
| Missing | `tests/examples/gateway_usage.py` | Offline primary-purpose evidence | one named scenario per completed feature |

#### Functional requirements

| Status | Requirement ID | Observable behavior | Evidence |
| --- | --- | --- | --- |
| Missing | `FR-GATEWAY-001` | REST /api/v1 resources validate bounded input and emit schema-stable DTOs. | OpenAPI/contract tests |
| Missing | `FR-GATEWAY-002` | Lists use stable cursor pagination/order and bounded limits. | Mutation pagination test |
| Missing | `FR-GATEWAY-003` | Mutations implement authorization, idempotency, conflict versions, and correlation IDs. | Retry/auth tests |
| Missing | `FR-GATEWAY-004` | Streams sequence events, heartbeat, reconnect by cursor, resync snapshots, and bound buffers. | Reconnect/slow-consumer test |

#### Removal behavior

Withdraw the capability and managed effects while retaining schema-readable artifacts. Dependent
operations return attributed unavailable; reinstall requires schema/version compatibility.

---

## 5. Domain-wide requirements and invariants

| Status | Requirement ID | Rule | Verification |
| --- | --- | --- | --- |
| Missing | `ARCH-001` | `__init__.py` is docstring-only. | `scripts/architecture_check.py` |
| Missing | `ARCH-002` | Tasks and resources are managed through `FeatureContext`. | Lifecycle tests |
| Missing | `ARCH-003` | Logging uses `app.kernel.logging`; no service configures handlers. | Architecture/logging tests |
| Missing | `ARCH-004` | Public contracts live in `app/contracts/gateway.py`. | Import/contract checks |
| Missing | `ARCH-005` | Feature modules never import sibling implementations. | Import checks |
| Missing | `ARCH-006` | SQL/schema operations live in `app/services/persistence/gateway.py`. | Architecture/schema checks |

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

tests/examples/gateway_usage.py
```

Editing uses explicit affected paths with `--no-cov`; the full candidate gate remains
`uv run python scripts/ci_check.py`.

- [ ] Stable feature and requirement IDs have one owner.
- [ ] Public contracts and exact `FeatureSpec` dependencies exist.
- [ ] Registration is explicit; imports have no runtime effects.
- [ ] Happy, invalid, boundary, unavailable, lifecycle, persistence, and removal tests pass.
- [ ] Numerical or stateful behavior has deterministic golden/fault fixtures.
- [ ] One offline usage example exists per completed feature.
- [ ] Domain status reflects repository evidence, not reference-product evidence.
- [ ] Architecture and full qualification gates pass.

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

The existing api_server scaffold at baseline 1a99dd7 is repository context but does not satisfy this greenfield product capability; Gateway remains Missing. Bind loopback by default. Long operations return 202 plus job identity; disconnect does not cancel. Errors follow application/problem+json-style code/title/status/safe detail/correlation/field violations. Lists have stable cursor ordering. WebSocket handshake negotiates protocol, carries ordered sequence and heartbeat, resumes from cursor or requests snapshot, bounds outbound buffers, and closes slow consumers explicitly. SSE is one-way fallback only. Gateway never calculates indicators, simulates fills, ranks strategies, or exposes tracebacks/secrets.

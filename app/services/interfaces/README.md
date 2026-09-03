# Interfaces (D-IFACE)

> **Package:** `app/services/interfaces/`
> **System role:** Capability-aware external boundary domain (D-IFACE) for
> HaruQuantAI. Every HTTP, SSE, CLI, MCP, and automation surface is a
> registered feature in this package that resolves business capabilities
> through `FeatureContext` and never imports a business implementation.
> **Status:** `In Progress` — 4 registered features
> (`FEAT-IFACE-SERVE_API_EVENTS`, `FEAT-IFACE-OBSERVE_MARKET_DATA`,
> `FEAT-IFACE-OBSERVE_MARKET_CATALOGUE`, `FEAT-IFACE-OPERATE_WATCHLISTS`).
> **Last updated:** `2026-09-03`

This README is the Interfaces domain's source of truth. The baseline
reconciliation that established this domain is recorded in
`docs/dev/iface-ui-migration/phase-0-baseline-reconciliation.md`.

---

## 1. Purpose and Boundary

### Purpose

Translate approved public capabilities into stable external contracts
(HTTP/OpenAPI, SSE event streams, CLI, MCP, and automation commands) while
keeping every business decision in its owning domain. Interfaces features
fail closed with the stable `CAPABILITY_UNAVAILABLE` result whenever a
declared capability has no active provider.

### Owns

- Transport-level semantics: API version negotiation, OpenAPI manifest
  projection, compatibility and deprecation reporting.
- SSE event envelopes, monotonic sequences, replay cursors, retention
  windows, and resync signaling.
- Boundary helpers reused by governed writes: optimistic concurrency
  validation, idempotent mutation deduplication, asynchronous job
  references, and artifact download validation.
- Presentation-neutral command delegation for CLI/MCP/automation callers.
- Translation of wire DTOs to and from public contract records.

### Does not own

- Business logic, domain state, or market-data truth of any kind.

### Explicit capability boundary

```text
D-IFACE MAY:
    expose HTTP
    expose SSE
    authorize requests
    translate wire DTOs
    resolve capabilities
    normalize transport errors

D-IFACE MAY NOT:
    calculate indicators
    make trading decisions
    calculate risk
    query MT5 directly
    own market-data truth
    duplicate business-domain logic
```

### Authentication boundary

Authentication, session, and CSRF enforcement are boundary transport
concerns owned by Interfaces features, not business domains. The concrete
identity/session design for the workstation boundary is gap G2 in the
Phase 0 record and must be ratified here before the Phase 7 session/auth
UI migration begins.

## 2. Feature Registry

| Status | Feature | Provides | Notes |
| --- | --- | --- | --- |
| Completed | `FEAT-IFACE-SERVE_API_EVENTS` | `interfaces.serve-api-events@1` | Transport foundation: versioning, OpenAPI, SSE buffer, idempotency, jobs, artifacts. |
| Completed | `FEAT-IFACE-OBSERVE_MARKET_DATA` | `interfaces.observe-market-data@1` | Phase 3 Market Ticks vertical slice; requires `data.stream-market-events@1`. |
| Completed | `FEAT-IFACE-OBSERVE_MARKET_CATALOGUE` | `interfaces.observe-market-catalogue@1` | Phase 6 Markets slice backend; requires `catalogue.catalog-instruments@1`. |
| Completed | `FEAT-IFACE-OPERATE_WATCHLISTS` | `interfaces.operate-watchlists@1` | Phase 6 Watchlists slice backend; requires `workspace.manage-watchlists@1`. |
| Pending | `FEAT-IFACE-OPERATE_TRADING` | `interfaces.operate-trading@1` | With the Phase 7 Trading migration. |
| Pending | `FEAT-IFACE-OPERATE_RESEARCH` | `interfaces.operate-research@1` | With the Research workbench migration. |
| Pending | `FEAT-IFACE-OPERATE_PORTFOLIOS` | `interfaces.operate-portfolios@1` | With the Portfolio migration. |
| Pending | `FEAT-IFACE-ADMINISTER_CAPABILITIES` | `interfaces.administer-capabilities@1` | System surfaces after Phase 5. |
| Pending | `FEAT-IFACE-AUTOMATE_COMMANDS` | `interfaces.automate-commands@1` | Deferred until a CLI/MCP consumer is ratified. |
| Pending | *(feature pending ratification, gap G5)* | `interfaces.edit-projects@1` | Declared contract; no provisional feature yet. |

Additional features are added only when an audit proves a distinct cohesive
responsibility; one feature per route is explicitly rejected.

## 3. Capability Map

| Capability key | Contract owner | Serving feature |
| --- | --- | --- |
| `interfaces.serve-api-events@1` | `app/contracts/interfaces/` | `FEAT-IFACE-SERVE_API_EVENTS` |
| `interfaces.observe-market-data@1` | `app/contracts/interfaces/` | `FEAT-IFACE-OBSERVE_MARKET_DATA` |
| `interfaces.observe-market-catalogue@1` | `app/contracts/interfaces/` | `FEAT-IFACE-OBSERVE_MARKET_CATALOGUE` |
| `interfaces.operate-watchlists@1` | `app/contracts/interfaces/` | `FEAT-IFACE-OPERATE_WATCHLISTS` |
| `interfaces.automate-commands@1` | `app/contracts/interfaces/` | `FEAT-IFACE-AUTOMATE_COMMANDS` (pending) |
| `interfaces.operate-research@1` | `app/contracts/interfaces/` | `FEAT-IFACE-OPERATE_RESEARCH` (pending) |
| `interfaces.edit-projects@1` | `app/contracts/interfaces/` | pending ratification (gap G5) |
| `interfaces.operate-portfolios@1` | `app/contracts/interfaces/` | `FEAT-IFACE-OPERATE_PORTFOLIOS` (pending) |
| `interfaces.administer-capabilities@1` | `app/contracts/interfaces/` | `FEAT-IFACE-ADMINISTER_CAPABILITIES` (pending) |
| `interfaces.operate-trading@1` | `app/contracts/interfaces/` | `FEAT-IFACE-OPERATE_TRADING` (pending) |

Contract ownership stays in `app/contracts/interfaces/` (see
`app/contracts/README.md` §4.10; machine-reconciled by
`tests/contracts/test_contract_inventory.py`). The UI-facing
`ApiResponse.v1`/`StreamEvent.v1` envelope records remain frozen client
evidence (Phase 0 decision D4); their canonical ratification lands with the
first served wire slice.

## 4. HTTP Responsibility

Interfaces HTTP surfaces serve versioned OpenAPI-described contracts,
produce uniform response envelopes, validate optimistic concurrency tokens,
deduplicate idempotent mutations, translate capability absence to the
stable `CAPABILITY_UNAVAILABLE` failure, and never embed a business
workflow. Business data crosses the boundary only as public contract
records. The current mounting surface (`serve_api_events/asgi.py`, served
by `uv run haruquantai`) exposes `GET /api/v1/market/ticks` (JSON
snapshot) and `GET /api/v1/market/ticks/stream` with the adopted alias
`GET /api/v1/data/snapshot-stream` (SSE), the watchlist CRUD routes
(`GET/POST /api/v1/watchlists`, `PATCH/DELETE /api/v1/watchlists/{id}`).
Authentication/session
enforcement is not yet active on the mounting surface; it is gap G2 and
must be ratified before any governed write goes live.

## 5. SSE Responsibility

Interfaces SSE surfaces publish ordered `InterfaceEventEnvelope` events
with monotonic sequence numbers, honor `Last-Event-ID`-style replay
cursors within a bounded retention window, report `has_more` batches,
signal resync when a cursor expires, and dispose exactly with the owning
feature scope.

## 6. Dependency Direction

```text
app/contracts/interfaces/  (public contracts, typed events)
        ▲
        │ imports only contracts + kernel primitives
app/services/interfaces/<feature>/
        ▲
        │ resolves declared CapabilityKey providers via FeatureContext
business domain features (brokers, data, trading, risk, ...)
```

An Interfaces feature never imports `app/services/<domain>/<feature>/`
implementation modules and never duplicates their policy.

## 7. Removal Semantics

Removing an Interfaces feature withdraws exactly its provided capability
bundle; consumers observe `CapabilityUnavailableError` (Python) or the
stable `CAPABILITY_UNAVAILABLE` failure (external surfaces). Unrelated
features remain active. Interfaces features own no durable state in this
foundation; any future persistent boundary state must declare a
`StateDeclaration` in the owning feature manifest.

# Implementation Plan: Brokers Domain Remediation (Post-Audit TASK-BROKERS-REMEDIATION-1)

> **Task ID:** `TASK-BROKERS-REMEDIATION-1`
> **Iteration:** `2` (supersedes Iteration 1 before any execution — owner directive: real transports, not fail-closed stubs)
> **Branch:** `backend`
> **Baseline Commit:** `2abbf625a15988cea9a454c33c17789442138931` (plus the uncommitted brokers working tree — the audited candidate this remediation corrects)
> **Audit of record:** Domain Implementation Audit of `D-BROKERS` performed 2026-09-20 against the same revision/working tree (26 controls: 7 PASS, 9 PARTIAL, 8 FAIL, 2 N/A).

**Iteration 2 change summary:** Iteration 1 proposed `mock_mode=False` →
fail-closed "not implemented" errors. The owner rejected that direction: the
domain must implement **real network transports** so that non-mock usage
genuinely connects to providers and connectivity can be observed. Iteration 2
therefore adds real-transport implementation (stdlib-only) for every
connector/adapter, a manual live-connectivity checker, and keeps mock mode
solely as the deterministic offline evidence channel required by the
repository constitution.

Follow-up work on the same task appends a clearly labelled iteration to this
file. Do not create a second plan for the same task run.

---

### User Review Required

> [!IMPORTANT]
> Critical design decisions requiring explicit owner sign-off before execution:
>
> 1. **Real transports are in scope (owner directive).** `mock_mode=False`
>    (the default) performs actual network I/O: stdlib `urllib`/`socket`/`ssl`
>    only — **no new third-party dependencies**. `mock_mode=True` remains
>    available exclusively for offline deterministic tests and the canonical
>    example, with clearly attributed simulated outcomes. No code path
>    fabricates success: real-mode outcomes are connected, refused, timeout,
>    DNS-unresolved, or auth-required — reported truthfully.
> 2. **Canonical usage example stays offline (constitution constraint).**
>    `AGENTS.md` and `FIP-08` require `tests/examples/<NN>_<domain>.py` to be
>    deterministic, offline, and secret-safe. Real-connection evidence is
>    delivered by a NEW manual harness `scripts/brokers_live_check.py`
>    (excluded from `ci_check.py`). If the owner instead wants
>    `03_brokers.py` itself to go live, that requires ratifying a change to
>    the offline-evidence rule first — flagged, not assumed.
> 3. **Live checker never submits orders (safety boundary).** It verifies
>    transport, authentication, symbol discovery, and streams a bounded number
>    of raw chunks (read-only). Real `submit_order` exists in the adapters but
>    the checker exercises it only behind explicit future owner
>    authorization (`--submit-live` is deliberately NOT implemented in this
>    iteration). Live trading submission is a destructive/financial action
>    under the AGENTS destructive-action guard.
> 4. **Credentials via environment only, never committed.** Credentialed
>    providers (SQ Equity/Futures, Darwinex, cTrader app auth, MT5 accounts)
>    read secrets from documented `HARU_BROKER_*` environment variables /
>    secret-key refs. Absent credentials produce truthful
>    `AUTH_REQUIRED`/`SKIPPED_NO_CREDENTIALS` outcomes — never bypassed.
> 5. **Reachability probe evidence (2026-09-20, this machine, bounded
>    `curl -m 8..12`):** Binance `/api/v3/ping` → **200 (0.35s)**; Yahoo v8
>    chart SPY with UA → **200 (0.39s)**; cTrader `demo.ctraderapi.com:5035`
>    → TLS reachable (**400 on non-protobuf request — expected, endpoint is
>    alive**); Dukascopy `datafeed.dukascopy.com` → **TIMEOUT from this
>    network** (even root path, with UA); `data.strategyquant.com` →
>    **NXDOMAIN (DNS does not exist)**. Consequence: SQ Equity/Futures
>    `base_url` values in the code were donor assumptions — they become
>    explicit configuration whose unresolved-host outcome is reported
>    truthfully. Expected live-checker results from this machine:
>    Binance/Yahoo CONNECTED, cTrader CONNECTED (transport level), Dukascopy
>    TIMEOUT (network-dependent), SQ HOST_UNRESOLVED.
> 6. **Contract amendments stay additive at `@1`** (no consumer or implementer
>    outside the domain exists — same precedent as
>    `TASK-PERSISTENCE-REMEDIATION-1` decision 2): `BrokerExecutionAck.
>    is_simulated`, `reconcile()` provider-snapshot parameter, measured
>    latency semantics on `ConnectionHealth`.
> 7. **Dead schema removal without migration** (`broker_instrument_overrides`)
>    and **status flip ordered last** — unchanged from Iteration 1. The
>    gitignored dev DB keeps its stale table; physical cleanup is owner-gated.
> 8. **Commit remains owner-gated** (AGENTS §6).

### Open Questions

> [!NOTE]
> - **Q1:** Negative-authorization gate (`allow_live=False`) applies to the
>   two trading adapters (FR scope: live execution profiles). Feeds keep
>   `environment` as metadata. (Recommended: Yes.)
> - **Q2:** Duplicate `submit_order` intent → replay original ack (logged)
>   rather than raise. (Recommended: replay.)
> - **Q3:** Keep `broker_connections` table with documented retained-evidence
>   purpose. (Recommended: keep + document.)
> - **Q4:** MT5: implement against the optional `MetaTrader5` package via
>   guarded import (typed `BrokerConnectionError` when package/terminal is
>   absent) and do NOT add it as a hard dependency now. Add the dependency
>   when an owner terminal exists. (Recommended: yes.)
> - **Q5:** cTrader scope this iteration: stdlib TLS connect +
>   `ProtoHeartbeat` (payloadType 53) frame round-trip proves the transport;
>   full `ProtoOAAuthorizationReq` application auth requires protobuf +
>   client credentials and is deferred to a follow-up task (typed
>   `BrokerAuthenticationError` meanwhile). (Recommended: yes.)
> - **Q6:** Live checker stays manual evidence, never wired into
>   `ci_check.py`. (Recommended: yes.)

---

## 1. Goal, Requirements & Usage Evidence

- **Problem Statement & Goal**:
  The 2026-09-20 audit found `D-BROKERS` mechanically sound but truthfulness-
  broken: zero network I/O behind "Completed" transport claims, fail-open
  fabricated successes, four FRs unimplemented, dead schema state, docs
  contradictions, and no acceptance evidence. Per owner direction, the
  remediation implements **real stdlib network transports** so `mock_mode=False`
  genuinely connects, and provides a manual live-connectivity checker that
  answers "do we actually connect?" with truthful per-provider outcomes.
- **Ratified Requirements** (target state):
  - `FR-BROKERS-TRANSPORT_BOUNDARY`: connectors stream genuinely acquired raw
    bytes (real mode) or clearly-attributed simulated bytes (mock mode); still
    zero persistence/compression/aggregation inside `brokers`.
  - Real-mode connection semantics: explicit timeouts, bounded retries,
    rate-limit spacing; DNS failure / refusal / timeout / TLS failure raise
    typed `BrokerConnectionError` with truthful reasons; authentication
    failures raise `BrokerAuthenticationError`.
  - `FR-BROKERS-ORDER_IDEMPOTENCY`: duplicate intent IDs replay the original
    ack; never a second submission (both trading adapters).
  - `FR-BROKERS-LIVE_AUTHORIZATION`: `environment="live"` refuses with
    `BrokerAuthenticationError` unless the adapter is explicitly constructed
    with `allow_live=True`.
  - `FR-BROKERS-STATE_RECONCILIATION`: reconciler consumes a provider order
    snapshot; matched/missing/ambiguous all computable and tested.
  - `FR-BROKERS-CAPABILITY_DISCOVERY`: unsupported order types / invalid
    stream spans raise `UnsupportedCapabilityError` before any transmission.
  - `FR-BROKERS-CALCULATION_MODE`, `SYMBOL_TRANSLATION`, `SERVER_TIMEZONE`,
    `SYSTEM_PROTECTION`, `CREDENTIAL_ISOLATION`, `CIRCUIT_FENCING`: remain
    conformant; credential isolation now also covers env-var secret
    resolution for real transports.
  - New evidence obligation: `scripts/brokers_live_check.py` demonstrates real
    connectivity per provider with bounded, read-only probes.
- **Usage Evidence**:
  - Canonical offline example `tests/examples/03_brokers.py` (mock,
    deterministic — constitution) restructured to one `example_03_<slug>()`
    per feature with truthful labeling.
  - NEW manual live harness `scripts/brokers_live_check.py` (real mode,
    network, optional credentials from env) producing a per-provider outcome
    table; its actual run output is recorded verbatim in the walkthrough.

## 2. Files Read (Audit Trail)

- [docs/dev/domain_implementation_audit.md](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/docs/dev/domain_implementation_audit.md) — 26-control audit procedure; §2 forbids provider invocation during audit (probes below were run during planning, not audit, and are read-only public GET/TCP checks).
- [docs/templates/implementation-plan.md](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/docs/templates/implementation-plan.md) — canonical plan structure.
- [app/services/brokers/README.md](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/app/services/brokers/README.md) — audited claims being corrected.
- [app/contracts/brokers.py](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/app/contracts/brokers.py) — DTO/protocol surface for WP1 amendments.
- All 11 modules under `app/services/brokers/` — confirmed fabricated non-mock payloads and absent transports (audit evidence, line-referenced in the audit report).
- [app/services/persistence/brokers.py](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/app/services/persistence/brokers.py) — dead/orphan schema findings.
- [app/services/persistence/migrations.py](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/app/services/persistence/migrations.py) — migration discovery; domain schemas use direct `execute_script` per workspace-domain convention.
- [app/registry.py](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/app/registry.py) — 12 factories under `FEATURES`/`"all"`/`"persistence"`/`"brokers"`.
- All 7 files under `tests/services/brokers/` and [tests/examples/03_brokers.py](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/tests/examples/03_brokers.py) — cited-FR gaps; grouped example functions.
- [docs/dev/evidence/features/FEAT-PERSISTENCE-DATABANKS/acceptance.json](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/docs/dev/evidence/features/FEAT-PERSISTENCE-DATABANKS/acceptance.json) — manifest schema template.
- [docs/PROJECT.md](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/docs/PROJECT.md) — domain capability map row 61 (`Brokers | Missing`), flipped last.
- [pyproject.toml](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/pyproject.toml) — runtime deps are fastapi/pydantic/pyarrow/uvicorn only; plan adds none (stdlib transports).
- [.agents/logs/2026-09-20T134225_persistence-remediation-1/implementation-plan.md](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/.agents/logs/2026-09-20T134225_persistence-remediation-1/implementation-plan.md) — remediation-plan precedent.
- [.agents/logs/2026-09-20T152500_brokers-full-implementation/](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/.agents/logs/2026-09-20T152500_brokers-full-implementation/) — original task record (history; superseded claims documented in walkthrough).
- **Reachability probes (planning evidence, 2026-09-20, bounded `curl -m 8..12`):**
  `api.binance.com/api/v3/ping` → 200/0.35s; `query1.finance.yahoo.com/v8/finance/chart/SPY` (UA) → 200/0.39s; `demo.ctraderapi.com:5035` → 400/0.72s (TLS endpoint alive, non-protobuf request rejected as expected); `datafeed.dukascopy.com/…/00h_ticks.bi5` → timeout 10–12s with and without UA; `data.strategyquant.com` → NXDOMAIN.

## 3. Proposed Changes & Implementation Order

Work packages (WP); tests are written inside each WP; change-scoped
`--no-cov` runs only. Unit tests never touch the network — they exercise the
real code paths through injectable/monkeypatchable module-private transport
functions.

### WP0 — Baseline verification

- Re-run `uv run pytest --no-cov tests/services/brokers/ -q` (expect 25
  passed) so remediation starts from a known-green baseline.

### WP1 — Public contract amendments (`app/contracts/brokers.py`)

- `[MODIFY]` `BrokerExecutionAck` — add `is_simulated: bool = False`.
- `[MODIFY]` `ConnectionHealth` docstring — `latency_ms` is a measured probe
  duration in real mode; `0.0` in mock mode (no measurement performed).
- `[MODIFY]` `BrokerReconciliationService.reconcile` — gains
  `provider_orders: Sequence[BrokerExecutionAck]` snapshot parameter.
- `[MODIFY]` `BrokerFeedConnector`/`BrokerTradingAdapter` docstrings — real
  error taxonomy: `BrokerConnectionError` (DNS/refused/timeout/TLS),
  `BrokerAuthenticationError` (credentials), `UnsupportedCapabilityError`
  (semantics), `BrokerFencedError` (fence).
- Capability majors stay `@1` (User Review item 6).

### WP2 — Real-transport core per module (no shared support module)

Each connector/adapter module gains a module-private stdlib transport helper
(e.g. `_http_get(url, *, headers, timeout_s, max_retries)` returning raw
bytes; `_open_tls(host, port, timeout_s)` for cTrader) implementing:

- socket/HTTP timeout from config (`timeout_s`), bounded retries from config
  (`max_retries`, default 3, with small backoff), rate-limit spacing
  (`rate_limit_rps`) between consecutive chunk fetches;
- truthful exception mapping: `URLError`/`gaierror` → DNS/refused, `timeout`
  → timeout, `HTTPError` 401/403 → `BrokerAuthenticationError`, other
  `HTTPError` → `BrokerConnectionError` with status code in the message;
- a monkeypatch seam (plain module-level function) so unit tests inject
  deterministic responses without network.

Duplication across modules is intentional: FIP-04 forbids shared support
acting as a registry; each helper stays ~20 lines.

### WP3 — Public feed transports, real (`dukascopy.py`, `crypto_adapter.py`, `yahoo.py`)

- `[MODIFY]` configs — enforced `timeout_s` (default 15.0), `max_retries`
  (default 3), `mock_mode: bool = False`; Dukascopy keeps `base_url`
  (publicly documented datafeed host).
- `[MODIFY]` `stream_raw_data()` real path:
  - Dukascopy: for each hour in span, `_http_get` the existing (already
    correct, 0-indexed-month) bi5 URL and yield the actual bytes as
    `RawTransportChunk`; 404 (no data for that hour) yields a skip-log and
    continues (provider semantics), other errors raise.
  - Crypto (Binance): `_http_get`
    `{rest_endpoint}/klines?symbol=…&interval=1h&startTime=…&endTime=…&limit=…`
    per bounded window; yield raw JSON bytes per response.
  - Yahoo: real session bootstrap — best-effort cookie from
    `fc.yahoo.com` + crumb from `query1.finance.yahoo.com/v1/test/getcrumb`
    with browser UA; then chart payload per symbol/window; throttling (429)
    raises `BrokerConnectionError` with truthful reason.
  - Latency measured per request and surfaced via `get_health()`.
- `[MODIFY]` mock path — unchanged synthetic bytes but only reachable with
  explicit `mock_mode=True`; chunks carry `metadata["simulated"]=True`.
- Tests: URL/parameter construction, response parsing hand-off, retry/timeout
  enforcement via seam, 401/404/timeout mappings, mock-vs-real branch
  selection, `simulated` metadata.

### WP4 — Credentialed feed transports, real (`sq_equity.py`, `sq_futures.py`, `darwinex.py`)

- `[MODIFY]` configs — `base_url` kept but documented as owner-configurable;
  current SQ defaults are donor placeholders whose DNS is unresolvable
  (probe: NXDOMAIN) — real runs report `HOST_UNRESOLVED` truthfully.
- `[MODIFY]` `connect()` real path — resolve endpoint, open transport, send
  provider handshake/license headers built from secret-key refs
  (`HARU_BROKER_SQ_LICENSE`, `HARU_BROKER_DARWINEX_TOKEN`, documented in
  README); absent credentials → `BrokerAuthenticationError`
  ("credentials required"). Streaming uses authenticated requests only.
- Tests: seam-injected DNS failure, auth-required, and success paths.

### WP5 — Trading adapters, real + safe (`mt5_adapter.py`, `ctrader_adapter.py`)

- `[MODIFY]` `Mt5AdapterConfig` — real `host`/`port`/`timeout_s`; `mock_mode`
  default `False`; guarded `import MetaTrader5` (Q4): absent package →
  `BrokerConnectionError("MetaTrader5 package/terminal not available")`
  (truthful, fail-closed); present → `initialize()`/`login()` with account
  credentials from secret refs, real `symbol_info` population of
  `Mt5SymbolMetadata`, `order_send` only via `submit_order` when
  `allow_live=True` (live) or in demo environment.
- `[MODIFY]` both adapters —
  - `connect()`: `environment="live"` + `allow_live=False` →
    `BrokerAuthenticationError`; cTrader real path: `_open_tls` to configured
    host/port, encode/decode a `ProtoHeartbeat` frame (4-byte length +
    varint payloadType 53 + empty payload) and require a heartbeat reply —
    transport-level proof (Q5); full app auth deferred with typed
    `BrokerAuthenticationError`.
  - `submit_order()`: order-type validation against declared
    `SUPPORTED_ORDER_TYPES` (`UnsupportedCapabilityError`); idempotency
    registry keyed by `intent.intent_id` — duplicates replay the original
    ack and log `duplicate_intent_replayed` (Q2); mock fills set
    `is_simulated=True`.
  - `disconnect()` clears registries; `get_health()` measures real round-trip
    latency (mock: `0.0`).
- `[MODIFY]` SPEC descriptions — drop "quote streaming" (no streaming API on
  the trading protocol).
- Tests: duplicate replay, live refusal, allow-live acceptance, unsupported
  type, MT5-package-absent typed error (monkeypatched import), heartbeat
  frame encode/decode round-trip, `is_simulated` provenance.

### WP6 — Reconciler redesign (`reconciliation.py`)

- `[MODIFY]` `reconcile(provider_name, active_intents, provider_orders)` —
  deterministic ticket↔intent matching (tickets derive from idempotency
  keys): `matched` = intent with counterpart; `missing` = intent without
  counterpart; `ambiguous` = provider order without local intent or intent
  lacking `idempotency_key`; duplicate `intent_id` input raises
  `BrokerReconciliationError`. Fence auto-reset only on clean parity.
- Tests: missing>0, provider-orphan ambiguity, duplicate-input refusal,
  clean parity, fence interactions.

### WP7 — Persistence corrections (`app/services/persistence/brokers.py`)

- `[MODIFY]` `_SCHEMA_SQL` — remove dead `broker_instrument_overrides`;
  keep `broker_connections` with documented retained-evidence purpose (Q3);
  docstring records the `execute_script` convention (workspace parity).
- Tests: fresh-DB schema assertion (dead table absent), all existing tests
  retained.

### WP8 — Composition/removal evidence (`tests/services/brokers/test_composition.py`)

- `[NEW]` — physical removal (capability absent, unrelated features start,
  retained profile rows intact on the same isolated DB) and required-
  dependency loss (catalog without `persistence.brokers` fails closed).

### WP9 — Canonical offline example (`tests/examples/03_brokers.py`)

- `[MODIFY]` — 12 `example_03_<slug>()` functions, explicit
  `mock_mode=True` configs, truthful labeling ("mock mode — payload
  synthesized locally; run scripts/brokers_live_check.py for real
  connectivity"), reconciliation against a snapshot, banner "EXERCISED
  OFFLINE (MOCK MODE)".

### WP10 — Live connectivity checker (`scripts/brokers_live_check.py`)

- `[NEW]` — manual, read-only harness (User Review items 2–4):
  - constructs every provider with `mock_mode=False` and real configs;
  - per provider: `connect()` → (auth where applicable) → symbol/metadata
    discovery where available → stream at most N=2 raw chunks → print
    first-chunk byte count (never chunk contents) → `disconnect()`;
  - outcome vocabulary: `CONNECTED`, `CONNECTED_PARTIAL` (transport ok,
    auth deferred), `AUTH_REQUIRED`, `SKIPPED_NO_CREDENTIALS`,
    `HOST_UNRESOLVED`, `TIMEOUT`, `REFUSED`, `PACKAGE_MISSING`, `ERROR`;
  - credentials read only from documented `HARU_BROKER_*` env vars;
  - bounded timeouts, no retries beyond config, secrets never printed;
  - exit code 0 iff every selected provider reached CONNECTED or
    CONNECTED_PARTIAL; not referenced by `ci_check.py`;
  - expected result from this machine per WP-planning probes: Binance
    CONNECTED, Yahoo CONNECTED, cTrader CONNECTED_PARTIAL, Dukascopy TIMEOUT,
    SQ Equity/Futures HOST_UNRESOLVED, Darwinex AUTH_REQUIRED (no creds),
    MT5 PACKAGE_MISSING (no package/terminal), catalog/fencing/reconciliation
    CONNECTED (local).

### WP11 — Documentation reconciliation (`app/services/brokers/README.md`, `docs/PROJECT.md`)

- `[MODIFY]` README — config table rewritten to final classes/fields/defaults
  (enforced timeouts/retries, `mock_mode=False` default, `allow_live`);
  per-provider transport reality table (public vs credential/terminal-gated
  vs currently unresolvable) incl. env-var secret names and live-checker
  usage; contract symbol fix `CryptoBrokerService` → `CryptoFeedService`;
  "quote streaming" wording dropped; persisted-state table updated (drop
  `instrument_overrides`, add `broker_connections` purpose row); FR evidence
  paths updated; workflows marked `Planned` with `data.imports@1` dependency;
  `DEC-BROKERS-002` restated as mock-for-offline-evidence, real-default for
  operation; DoD re-ticked only for evidenced items.
- `[MODIFY]` `docs/PROJECT.md` — Brokers row flips last to
  `Completed (real stdlib transports; Binance/Yahoo/Dukascopy public, SQ/Darwinex/cTrader/MT5 credential- or terminal-gated)`.

### WP12 — Acceptance evidence + full qualification

- `[NEW]` 11 `docs/dev/evidence/features/FEAT-BROKERS-*/acceptance.json`
  following the persistence manifest schema (requirements, symbols,
  capabilities, persistence mapping, test target, example function,
  verification command + exit code, SHA-256 fingerprints, `tested_revision`
  = baseline `2abbf62` + working-tree note, pipeline stages with truthful
  `NOT_APPLICABLE` justifications; live-checker run output referenced in the
  walkthrough as manual evidence, not CI).
- Full gate + walkthrough in this task directory, presented for the Owner
  Commit Gate.

### Sequential Implementation Order

1. WP0 baseline → WP1 contracts → WP2 transport core
2. WP3 public feeds → WP4 credentialed feeds → WP5 trading adapters
3. WP6 reconciler → WP7 persistence → WP8 composition/removal
4. WP9 offline example → WP10 live checker
5. WP11 documentation → WP12 manifests + qualification + walkthrough

## 4. Dependencies and Contracts

- **No new third-party runtime dependencies.** Transports use stdlib
  `urllib.request`, `socket`, `ssl`, `json`. `MetaTrader5` stays an optional
  guarded import (Q4). Existing deps (fastapi/pydantic/pyarrow/uvicorn) untouched.
- **Kernel:** `FeatureContext`, `FeatureSpec`, `get_logger` — unchanged usage.
- **Public contract:** only `app/contracts/brokers.py` (WP1, additive `@1`).
- **Persistence boundary:** all SQL remains in
  `app/services/persistence/brokers.py`.
- **External integration policy (AGENTS §5):** typed protocols + explicit
  timeouts + bounded retries + fencing circuit breaker — satisfied by WP2
  helpers and existing `brokers.fencing@1`.
- **Cross-module purity:** per-module private transport helpers; no shared
  support module (FIP-04).

## 5. Blockers, Risks, and Trade-offs

- **Network variance:** live-checker outcomes differ by machine/region (probe:
  Dukascopy times out here). The checker is manual evidence with truthful
  outcomes; failures are informative, not test failures.
- **SQ endpoints unresolvable (NXDOMAIN):** donor URLs were assumptions;
  kept configurable, reported truthfully. If the owner has the real SQX
  server URLs/licences, they are plugged in via config — no code change.
- **Yahoo throttling (429)** possible; mapped to a typed, truthful error.
- **cTrader scope:** heartbeat-level transport proof only this iteration
  (Q5); full protobuf trading deferred — the checker reports
  `CONNECTED_PARTIAL`, never implying full qualification.
- **MT5 requires a terminal + optional package** — absent → truthful
  `PACKAGE_MISSING`; no silent mock substitution.
- **Safety:** no order submission from the checker; live submission gated by
  `allow_live` + credentials; unit tests never perform network I/O (seam).
- **Constitution tension managed:** offline example retained; live evidence
  isolated in `scripts/`; if the owner wants the example itself live, that is
  a rule change to ratify explicitly.
- **Assumption:** the gitignored dev DB may retain dropped-table/seed rows;
  harmless, recorded as residual; destructive cleanup owner-gated.

## 6. Scope Boundaries (Inclusions & Exclusions)

- **In Scope:** WP0–WP12; 11 service modules, 1 persistence module, 1
  contract file, 8 test files (7 modified + 1 new), 1 offline example, 1 new
  live checker script, README, PROJECT.md single row, 11 acceptance
  manifests, this task directory.
- **Out of Scope / Non-Goals:**
  - Full cTrader protobuf application authorization and trading; WebSocket
    streaming; `MetaTrader5` as a hard dependency (Q4/Q5).
  - Order submission from the live checker; any live trading.
  - Making `tests/examples/03_brokers.py` network-dependent (constitution;
    see User Review item 2).
  - Dropping/migrating tables in the active dev database (owner-gated).
  - D-DATA / `data.imports@1`, D-TRADING consumers, Interfaces/UI.
  - `ATW-*` workflow closure; CI/browser/provider/release qualification
    claims; changes to `app/registry.py`.

## 7. Verification Plan

### Automated Tests (change-scoped, offline, per WP)

```bash
uv run pytest --no-cov tests/services/brokers/ -q                                   # WP0 baseline + domain roll-up
uv run pytest --no-cov tests/services/brokers/test_feeds.py -v                      # WP3/WP4
uv run pytest --no-cov tests/services/brokers/test_mt5_adapter.py tests/services/brokers/test_ctrader_adapter.py -v   # WP5
uv run pytest --no-cov tests/services/brokers/test_reconciliation.py -v             # WP6
uv run pytest --no-cov tests/services/brokers/test_persistence.py tests/services/brokers/test_composition.py -v       # WP7/WP8
```

### Usage Evidence Run (offline canonical)

```bash
uv run python -m tests.examples.03_brokers
```

### Live Connectivity Run (manual, real network — recorded verbatim in walkthrough)

```bash
uv run python scripts/brokers_live_check.py            # all providers
uv run python scripts/brokers_live_check.py --providers binance,yahoo,ctrader
```

### Quality Pipeline

```bash
uv run python scripts/architecture_check.py
uv run python scripts/ci_check.py
uv run pytest --cov=app.services.brokers --cov=app.services.persistence.brokers --cov-report=term --cov-fail-under=0 -q tests/services/brokers/
```

### Manual Verification

- Owner reviews live-checker output (expected mixed outcomes per probe
  evidence) and the four open questions Q1–Q6 before the commit gate.

## 8. Rollback & Contingency

Everything in scope is uncommitted. Full revert of this remediation:

```bash
git checkout 2abbf62 -- app/services/brokers/README.md docs/PROJECT.md
git clean -fd app/contracts/brokers.py app/services/brokers/ app/services/persistence/brokers.py \
  tests/services/brokers/ tests/examples/03_brokers.py scripts/brokers_live_check.py \
  docs/dev/evidence/features/ .agents/logs/2026-09-20T131500_brokers-remediation-1/
```

(If the owner commits the base implementation first, revert becomes
`git revert` of the remediation commit.)

```text
ALLOWED_WRITE_PATHS:
- app/contracts/brokers.py
- app/services/brokers/catalog.py
- app/services/brokers/mt5_adapter.py
- app/services/brokers/ctrader_adapter.py
- app/services/brokers/dukascopy.py
- app/services/brokers/sq_equity.py
- app/services/brokers/sq_futures.py
- app/services/brokers/darwinex.py
- app/services/brokers/crypto_adapter.py
- app/services/brokers/yahoo.py
- app/services/brokers/reconciliation.py
- app/services/brokers/isolation_fencing.py
- app/services/persistence/brokers.py
- tests/services/brokers/
- tests/examples/03_brokers.py
- scripts/brokers_live_check.py
- app/services/brokers/README.md
- docs/PROJECT.md
- docs/dev/evidence/features/FEAT-BROKERS-*/
- .agents/logs/2026-09-20T131500_brokers-remediation-1/
END_ALLOWED_WRITE_PATHS:
```

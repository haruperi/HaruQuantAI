# Brokers — V1/V2 Reconciliation

## 1. Reconciliation Scope

* **Domain:** Brokers
* **Domain ID:** `brk`
* **Current and intended package:** `app/services/brokers`
* **V1 audit report:** `brokers-v1-audit.md`
* **V2 requirements:** uploaded as `brokers(1).md` (document title: *Broker Domain — Functional Requirements*)
* **Comparison limitations:** This reconciliation uses only the two supplied documents. It does not re-audit or execute code, tests, provider SDKs, terminals, credentials, external endpoints, or deployment configuration. Cross-domain alignment with the top-level system document is intentionally deferred to pipeline step 05.

## 2. Executive Summary

V1 contains substantial value worth preserving: MT5 connectivity and trading reads/mutations, cTrader authentication and protocol translation, multi-provider market-data access, and lazy optional-provider imports. The Data gateway and Trading workflows prove that broker connectivity is not dead infrastructure.

The rebuild should not preserve V1 unchanged. The active-broker router silently falls back to MT5, the simulator route is broken, provider clients are global mutable singletons, MT5 and cTrader expose raw/provider-shaped surfaces, broker data wrappers overlap Data, and cTrader/Yahoo can fabricate prices, identifiers, success, ticks, or spread-like values. Those behaviours must be removed or corrected.

V2’s domain boundary is accepted: Brokers owns direct provider protocol integration and truthful structural mapping; Data owns acquisition policy, normalization, cache, and persistence; Trading owns approved execution policy, idempotency, unknown-outcome handling, reconciliation, and persistence. Canonical results, errors, DTOs, capabilities, explicit registry resolution, provider/account/environment isolation, and deterministic unsupported outcomes should be added.

Several V2 prescriptions are excessive for the initial rebuild and are simplified: no second general-purpose synchronous façade until needed; no strict exception façade; no universal priority throttling queue; no mandatory ten-state lifecycle for every HTTP adapter; no in-place account switching; no version fields repeated on every nested DTO; no per-bar timezone evidence duplication; no unproven `<100 µs` mapping gate; no mandatory OpenTelemetry dependency; and no always-on external sandbox execution in ordinary CI.

The recommended migration is evolutionary: establish canonical contracts and registry first, then refactor MT5 and cTrader behind them, migrate Data and Trading, convert the read-only providers, remove V1 compatibility/tool/database surfaces, and only then delete provider-native public APIs.

## 3. Decision Principles

* Preserve proven provider calls and protocol knowledge.
* Treat V1 code as evidence, not future authority.
* Treat V2 requirements as proposals, not automatic approvals.
* Preserve provider truth; never fabricate missing values or success.
* Keep Brokers thin: direct provider communication and structural mapping only.
* Require explicit provider, account, and environment selection.
* Prefer caller-owned adapter instances over hidden singletons.
* Prefer focused capability protocols over one bloated interface file.
* Use classes only where connection state, dependencies, or lifecycle require them.
* Keep stateless mapping and validation as private or focused functions.
* Add complexity only for a confirmed workflow, safety constraint, provider protocol, or measurable need.
* Stage unsupported/unverified provider features rather than claiming completeness.
## 4. Capability Reconciliation Matrix

| Capability ID | Capability | V1 evidence | V2 requirement | Gap | Decision | Final behaviour | Reuse approach | Reason |
|---|---|---|---|---|---|---|---|---|
| CAP-BRK-001 | Explicit broker registry and public package API | `V1-CAP-BROKERS-001/002`; `V1-WF-BROKERS-001/002/006` | `BRK-FR-REG-*`, `BRK-FR-API-*` | V1 lazy exports are valuable, but implicit active-broker fallback is unsafe. | Modify | Lazy registry/factory requires an explicit broker/profile ID; unknown IDs return `BROKER_UNKNOWN`; package root exposes only canonical contracts and factories. | Refactor | Preserves optional SDK isolation while eliminating silent MT5 selection. |
| CAP-BRK-002 | Adapter connection and session lifecycle | `V1-CAP-BROKERS-003/008`; `V1-WF-BROKERS-004/005/007` | `BRK-FR-CON-*`, `BRK-FR-ASYNC-*` | V1 lifecycle is provider-specific, auto-connects, and uses global mutable state. | Modify | One adapter instance owns one provider/account/environment session; explicit async connect/disconnect, verified state, deterministic cleanup, and no hidden auto-connect. | Refactor | Required for account isolation, event-loop safety, and provider-truth connection status. |
| CAP-BRK-003 | Canonical results, errors, and provider-truth DTOs | V1 provider outputs and inconsistent failures; issues `006-013`, `018`, `020` | `BRK-FR-CONTRACT-001`–`017` | V1 leaks provider objects, fabricates defaults, and returns inconsistent error/empty shapes. | Add | All public operations return canonical `BrokerResult`; expected failures are values; raw SDK objects never cross; missing fields remain null/unknown; decimals and UTC are explicit. | New with mapping reuse | A common truthful contract is the main missing cross-provider boundary. |
| CAP-BRK-004 | Capability catalogue and deterministic unsupported outcomes | V1 conventional client shape; provider support inferred at runtime | `BRK-FR-CAP-*`, unsupported-capability rule | V1 has no verified capability matrix and unsupported methods are absent or approximated. | Add | Publish complete capability records by provider/profile/account; unsupported operations return `BROKER_CAPABILITY_UNSUPPORTED` without SDK calls. | New | Consumers need safe capability discovery without concrete-provider branching. |
| CAP-BRK-005 | Provider symbols and market metadata | `V1-CAP-BROKERS-005/013`; MT5/cTrader symbol reads | Section 6.2–6.3, `BRK-FR-READ-005` | V1 symbol outputs and alias handling are inconsistent. | Modify | Return provider symbol/asset/session metadata structurally mapped; aliases are explicit and fetchable; no canonical identity policy in Brokers. | Refactor | Preserves useful reads while keeping market identity policy in Data. |
| CAP-BRK-006 | Quotes, ticks, bars, and order books | `V1-CAP-BROKERS-004/009/012/014/015/016/017`; `V1-WF-BROKERS-003` | Section 6.3, contracts `013-015`, read requirements | V1 market-data support is valuable but errors, timeframes, spreads, provenance, and synthetic fallbacks differ. | Modify | Return genuine bounded provider observations only; unsupported quote/tick/order-book operations fail explicitly; structural mapping only. | Refactor | Core existing value should remain, but fabricated and assumed values must be removed. |
| CAP-BRK-007 | Streaming subscriptions | cTrader spot subscription support; no common contract | Section 6.4, `BRK-FR-SUB-*`, `BRK-FR-CON-026` | V1 support is cTrader-specific and callback/request lifecycle is incomplete. | Add | Adapter-scoped async streams with bounded buffers, FIFO ordering where provider evidence permits, explicit disconnect/resync events, and deterministic unsubscribe. | New with cTrader reuse | Needed for real-time Data and Trading workflows; implementation must remain proportionate to provider support. |
| CAP-BRK-008 | Account, permissions, balances, assets, and platform state | `V1-CAP-BROKERS-005/010`; MT5/cTrader account/terminal reads | Section 6.1–6.2 | V1 has useful account reads but inconsistent wrappers and defaults. | Modify | Return direct provider account/platform/permission data in canonical DTOs; unavailable fields are null/unknown; no persisted snapshots. | Refactor | Preserves proven read value and removes fake compatibility fields. |
| CAP-BRK-009 | Positions, orders, deals, and account activity reads | `V1-CAP-BROKERS-005/010`; `V1-WF-BROKERS-006` | Section 6.5, `BRK-FR-READ-006`–`009` | V1 has working paths but inconsistent types, filtering, history bounds, and cTrader field defects. | Modify | Bounded canonical pages preserve provider IDs, partial states, and page limits; malformed responses are errors. | Refactor | Required for Trading reconciliation while keeping reconciliation authority outside Brokers. |
| CAP-BRK-010 | Single-target broker mutations | `V1-CAP-BROKERS-006/011`; `V1-WF-BROKERS-006/007` | Section 6.6, `BRK-FR-MUT-*` | V1 submits orders but cTrader can fabricate success and provider-native constants leak. | Modify | Check/place/modify/cancel orders and modify/close positions perform one explicit provider action; success requires acknowledgement; uncertain transmission returns `BROKER_UNKNOWN_OUTCOME`. | Refactor | Preserves direct mutation capability while enforcing truth and boundary safety. |
| CAP-BRK-011 | Provider-native calculations | V1 cTrader margin/profit and MT5 delegated calculations | Section 6.7 | V1 calculations are not canonical and cTrader profit can be locally approximated. | Modify | Expose provider-native margin/profit/fee estimates only; unsupported when the provider lacks a verified calculation endpoint. | Refactor | Local trading/risk formulas do not belong in Brokers. |
| CAP-BRK-012 | MT5 adapter | `V1-CAP-BROKERS-003`–`007`; `V1-WF-BROKERS-004`–`006` | Provider requirements and complete canonical contract | V1 is the strongest runtime integration but is large, singleton-based, credential-coupled, and SDK-leaky. | Modify | Retain terminal calls and provider semantics behind a focused canonical adapter; isolate blocking calls; caller supplies config; remove delegated public SDK surface. | Heavy refactor | Highest-value migration target and most important live compatibility path. |
| CAP-BRK-013 | cTrader adapter | `V1-CAP-BROKERS-008`–`011`; `V1-WF-BROKERS-007` | Provider requirements and complete canonical contract | Substantial protocol work exists, but correlation, fallback truth, profit mapping, and reactor lifecycle are unsafe. | Modify | Retain authentication/protobuf decoding and request translation; correlate requests safely; remove fabricated quotes/IDs; use canonical DTOs and explicit lifecycle. | Heavy refactor | Large reuse value, but correctness defects preclude unchanged retention. |
| CAP-BRK-014 | Binance immutable product-profile adapters | `V1-CAP-BROKERS-014` | Initial support; `BRK-FR-PROV-009` | V1 is public-data-only and silently maps unsupported timeframes. | Modify | Keep public market data; add explicit `BINANCE_SPOT` adapter in initial rebuild; define separate Futures profiles but defer mutation availability until sandbox-verified. | Refactor plus staged new work | Avoids one mutable multi-product adapter and prevents unverified trading claims. |
| CAP-BRK-015 | Dukascopy read-only adapter | `V1-CAP-BROKERS-012/013` | Provider requirements; `BRK-FR-PROV-008` | V1 scraper is useful but connection status is local-only and aliases are inconsistent. | Modify | Read-only adapter returns verified HTTP results; trading/account/subscription methods are deterministic unsupported; symbol mappings must resolve actual requests. | Refactor | Retains source diversity without pretending trading or connection authentication. |
| CAP-BRK-016 | Yahoo read-only historical-bar adapter | `V1-CAP-BROKERS-015/016` | Provider requirements; `BRK-FR-PROV-007` | Bars are useful; synthetic ticks violate broker truth. | Split | Preserve genuine historical bars; remove synthetic ticks and return unsupported for genuine tick/quote capabilities unless the integration changes. | Refactor/remove | Separates legitimate provider data from simulation behaviour. |
| CAP-BRK-017 | Session and account isolation | V1 global singletons; `V1-ISSUE-BROKERS-019` | `BRK-FR-REG-006/007/010/011`, `BRK-FR-CON-013/014/025` | V1 process-wide state can leak credentials, subscriptions, and selected accounts. | Add | Registry is a factory; caller owns adapter lifetime; provider/account/environment are immutable after connection; sharing requires explicit dependency injection. | New with provider lifecycle reuse | Essential safety boundary for concurrent and multi-account operation. |
| CAP-BRK-018 | Logging, correlation, and technical observability | V1 logging in provider modules | `BRK-FR-OBS-*`, latency fields | V1 logs exist but lack a canonical correlation/redaction contract. | Modify | Structured redacted logs cover lifecycle and provider calls; results carry correlation and latency; full payload sinks and mandatory tracing integrations are deferred. | Refactor | Supports diagnosis without leaking secrets or adding premature infrastructure. |
| CAP-BRK-019 | Shared contract, boundary, and fake-adapter tests | V1 provider-specific tests identified but not run | Section 18, `BRK-FR-API-006`, `BRK-FR-TEST-001` | V1 test files exist, but runtime success and uniform contract compliance are unverified. | Add | One shared contract suite, import-boundary tests, deterministic fake adapter, and credential-gated sandbox suites with honest verification status. | New plus test reuse | Required to claim cross-provider equivalence safely. |

## 5. V1 Disposition Register

| V1 capability ID | V1 capability | Current implementation | Current value | Decision | Final destination | Removal condition |
|---|---|---|---|---|---|---|
| V1-CAP-BROKERS-001 | Lazy optional-provider exports | `__init__.py::__getattr__`, `_EXPORT_MODULES`, `__all__` | Supporting | Modify | `CAP-BRK-001` registry/public API | Verify no external caller depends on removed legacy export names. |
| V1-CAP-BROKERS-002 | Active trading broker selection | `router.py::get_active_broker_name/get_broker_module` | Essential | Modify | `CAP-BRK-001` explicit registry resolution | Remove legacy router only after Trading and tests pass explicit broker IDs. |
| V1-CAP-BROKERS-003 | MT5 terminal/account lifecycle | `MT5Client.connect/is_connected/shutdown` | Essential | Modify | `CAP-BRK-002`, `CAP-BRK-012` | N/A; retain behaviour but replace singleton/config coupling. |
| V1-CAP-BROKERS-004 | MT5 bars and ticks | `MT5Client.get_bars/get_ticks` | Essential | Modify | `CAP-BRK-006`, `CAP-BRK-012` | N/A; preserve provider calls and validate canonical mapping. |
| V1-CAP-BROKERS-005 | MT5 account/order/position/deal reads | MT5 module `get_*_info` functions and delegated SDK calls | Essential | Modify | `CAP-BRK-008`, `CAP-BRK-009`, `CAP-BRK-012` | N/A; retain provider reads, remove raw SDK leakage. |
| V1-CAP-BROKERS-006 | MT5 order mutation | `mt5.py::trade` and native delegated methods | Essential | Modify | `CAP-BRK-010`, `CAP-BRK-012` | N/A; preserve direct order submission after canonical request/result conversion. |
| V1-CAP-BROKERS-007 | Stored/explicit MT5 credential data operations | `get_mt5_credentials`, `get_connected_mt5_client`, `load_mt5`, `mt5_data_*` | Useful but boundary-violating | Remove | Caller-owned secret/config creation; Data-owned data workflow | Verify no external tool registry or API route invokes these names; migrate callers before deletion. |
| V1-CAP-BROKERS-008 | cTrader connection/authentication | `CTraderClient.connect` and callback/auth state machine | Essential when selected | Modify | `CAP-BRK-002`, `CAP-BRK-013` | N/A; retain protocol/auth logic after concurrency and lifecycle correction. |
| V1-CAP-BROKERS-009 | cTrader bars/ticks | `CTraderClient.get_bars/get_ticks` | Essential | Modify | `CAP-BRK-006`, `CAP-BRK-013` | N/A; preserve decoding, replace silent empty/error ambiguity. |
| V1-CAP-BROKERS-010 | cTrader MT5-compatible information objects | Wrapper classes and module `get_*_info` functions | Useful | Modify | Canonical DTO mapping in `CAP-BRK-008/009/013` | Delete compatibility classes only after canonical DTO parity and caller migration. |
| V1-CAP-BROKERS-011 | cTrader order mutation | `ctrader.py::trade` | Essential when selected | Modify | `CAP-BRK-010`, `CAP-BRK-013` | N/A; retain provider translation, remove fabricated IDs/success. |
| V1-CAP-BROKERS-012 | Dukascopy historical/tick data | `fetch`, `DukascopyClient` | Useful | Modify | `CAP-BRK-006`, `CAP-BRK-015` | Retain only if endpoint legality/reliability is accepted and integration tests pass. |
| V1-CAP-BROKERS-013 | Dukascopy instrument discovery | `INSTRUMENT_MAP`, `dukascopy_data_list_symbols` | Useful | Modify | `CAP-BRK-005`, `CAP-BRK-015` | Remove aliases not resolvable by the actual fetch path. |
| V1-CAP-BROKERS-014 | Binance klines and public-trade ticks | `BinanceClient.get_bars/get_ticks` | Useful | Modify | `CAP-BRK-006`, `CAP-BRK-014` | N/A for data; trading additions require authenticated profile tests. |
| V1-CAP-BROKERS-015 | Yahoo historical bars | `YahooClient.get_bars` | Useful | Modify | `CAP-BRK-006`, `CAP-BRK-016` | Retain only provider-observed bars with explicit limitations. |
| V1-CAP-BROKERS-016 | Yahoo synthetic ticks | `YahooClient.get_ticks` plus Data synthetic transform | No acceptable broker-domain value | Remove | None; synthetic generation may exist only in Simulation/Data under explicit provenance | Verify no consumer relies on Yahoo as a genuine tick source; replace with unsupported outcome. |
| V1-CAP-BROKERS-017 | Shared broker-backed data integration shape | Conventional `connect/is_connected/get_bars/get_ticks` used by Data gateway | Essential integration surface | Modify | Canonical capability protocols and registry (`CAP-BRK-001/004/006`) | N/A; migrate Data gateway to public canonical API. |

## 6. V2 Requirement Disposition Register

All 130 explicit V2 requirement IDs are classified below. Ten additional `V2-NORM-*` rows classify unnumbered normative requirements so that no material proposal is omitted.

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| BRK-FR-OWN-001 | Brokers owns provider passthrough only and excludes business logic, persistence, credentials, synthesis, and orchestration. | Modify | Retain direct provider passthrough, but remove V1 credential lookup, data normalization/envelopes, synthetic data, and routing policy. | V1 crosses several boundaries that V2 correctly assigns to Data, Trading, composition, or Simulation. |
| BRK-FR-ASYNC-001 | Async-first canonical adapter operations and a safe synchronous façade for synchronous consumers. | Modify | Async is the primary canonical contract; isolate blocking SDK calls. Defer a separate general-purpose `SyncBrokerAdapter` until a confirmed synchronous consumer requires it. | Async-first is justified, but two complete public facades would duplicate the initial surface. |
| BRK-FR-ASYNC-002 | Propagate caller cancellation safely without corrupting adapter state. | Add | Use async adapter operations and propagate cancellation safely. | Needed for streaming/non-blocking consumers and blocking-SDK isolation. |
| BRK-FR-CONTRACT-001 | Return one standard `BrokerResult[T]` envelope from every public operation. | Add | Introduce the canonical contract. | V1 lacks uniform result, error, DTO, and truth-preservation semantics. |
| BRK-FR-CONTRACT-002 | Represent operational failures with one canonical `BrokerError`. | Add | Introduce the canonical contract. | V1 lacks uniform result, error, DTO, and truth-preservation semantics. |
| BRK-FR-CONTRACT-003 | Provide a canonical broker error-code taxonomy. | Modify | Define a stable core error taxonomy now; add operation-specific codes only when accepted capabilities require them. | The proposed list is mostly sound, but premature unused codes should not drive implementation. |
| BRK-FR-CONTRACT-003A | Use result-based canonical errors and optionally provide a typed strict exception wrapper. | Modify | Keep result-only canonical adapters and propagation of cancellation/fatal exceptions; reject the initial typed `StrictBrokerAdapter` façade. | A second error-mode façade adds maintenance cost without a demonstrated consumer. |
| BRK-FR-CONTRACT-003B | Do not implement business retries; only provider-required flow control is allowed. | Modify | Keep the prohibition on business retries and mutation replay; implement only provider-required flow control and header-aware throttling. | A universal throttling implementation is not justified across very different SDKs. |
| BRK-FR-CONTRACT-003C | Define bounded rate-limit queueing, priority, cancellation, ordering, weights, and telemetry. | Defer | Initial adapters may use bounded provider-specific throttling and fail-fast backpressure. Defer cross-operation priority queues, weighted scheduling, and same-symbol FIFO machinery until a provider workload proves the need. | The full queue specification is disproportionate and risks becoming an execution-policy layer. |
| BRK-FR-CONTRACT-004 | Do not expose provider SDK objects, handles, messages, or provider exceptions. | Add | Introduce the canonical contract. | V1 lacks uniform result, error, DTO, and truth-preservation semantics. |
| BRK-FR-CONTRACT-005 | Map provider responses into canonical transport/schema DTOs without changing provider truth. | Modify | Define DTOs only for accepted capabilities, grouped into focused contract modules; do not create every proposed DTO before an operation is implemented. | Avoids speculative schema bulk while retaining canonical types. |
| BRK-FR-CONTRACT-006 | Missing provider fields | Add | Introduce the canonical contract. | V1 lacks uniform result, error, DTO, and truth-preservation semantics. |
| BRK-FR-CONTRACT-007 | Use decimal-compatible numeric values and reject invalid mandatory numbers such as NaN/Infinity. | Add | Introduce the canonical contract. | V1 lacks uniform result, error, DTO, and truth-preservation semantics. |
| BRK-FR-CONTRACT-008 | Represent every quantity with an explicit unit or interpretation. | Add | Introduce the canonical contract. | V1 lacks uniform result, error, DTO, and truth-preservation semantics. |
| BRK-FR-CONTRACT-009 | Map all canonical timestamps to timezone-aware UTC without assuming provider timezones. | Add | Introduce the canonical contract. | V1 lacks uniform result, error, DTO, and truth-preservation semantics. |
| BRK-FR-CONTRACT-010 | Return bounded canonical pages with provider-derived cursors and explicit truncation. | Add | Introduce the canonical contract. | V1 lacks uniform result, error, DTO, and truth-preservation semantics. |
| BRK-FR-CONTRACT-011 | Standard Order Fields | Modify | Keep common order fields required by MT5, cTrader, and Binance Spot; add derivatives-only fields with the relevant immutable Binance Futures profile. | A single oversized order DTO with every platform feature obscures applicability. |
| BRK-FR-CONTRACT-012 | Represent every connection transition with a canonical connection-event DTO. | Modify | Keep lifecycle state, reason, UTC timestamp, session generation, and resync flag; populate reconnect counters only for adapters that reconnect. | Preserves useful evidence without forcing meaningless fields. |
| BRK-FR-CONTRACT-013 | Define explicit open/close time, closure, volume, timeframe, and timezone evidence for bars. | Modify | Keep open/close timestamps, closed state, volume distinctions, and native/requested timeframe; place detailed timezone-conversion evidence in page/result metadata rather than duplicating it on every bar. | Per-row evidence creates excessive payload overhead. |
| BRK-FR-CONTRACT-014 | Define provider sequence, event/receipt time, prices, quantities, and tick type for ticks. | Add | Introduce the canonical contract. | V1 lacks uniform result, error, DTO, and truth-preservation semantics. |
| BRK-FR-CONTRACT-015 | Order Book Semantics | Add | Introduce the canonical contract. | V1 lacks uniform result, error, DTO, and truth-preservation semantics. |
| BRK-FR-CONTRACT-016 | Clock Skew and Latency Metadata | Add | Introduce the canonical contract. | V1 lacks uniform result, error, DTO, and truth-preservation semantics. |
| BRK-FR-CONTRACT-017 | DTO and Contract Versioning | Modify | Version the public contract, result envelope, capability report, and adapter. Nested DTOs inherit the result contract version unless independently versioned later. | Repeating three version fields on every nested object is unnecessary. |
| BRK-FR-CAP-001 | The capability catalogue must contain one canonical identifier for every operation in Section 6. | Add | Implement one generated capability catalogue and runtime feature report. | V1 has no authoritative capability contract. |
| BRK-FR-CAP-002 | Each adapter must publish a complete feature-flag report containing all catalogue entries, not only supported entries. | Add | Implement one generated capability catalogue and runtime feature report. | V1 has no authoritative capability contract. |
| BRK-FR-CAP-003 | Structured Capability Record | Add | Keep implementation, availability, access, requirement, verification, and reason fields; derive values from one declaration source. | The structure is useful when generated, not hand-maintained. |
| BRK-FR-TEST-001 | Sandbox/testnet integration tests verify every capability claimed as supported. | Modify | Run deterministic contract/boundary tests in normal CI; run credential-gated sandbox/testnet suites on scheduled/release pipelines and record verification status. | External provider availability and credentials cannot be assumed on every CI run. |
| BRK-FR-CAP-004 | Capability status may vary by broker, environment, account type, permissions, market, SDK version, or credentials. | Add | Implement one generated capability catalogue and runtime feature report. | V1 has no authoritative capability contract. |
| BRK-FR-CAP-005 | A feature-flag report must be refreshed after connection, authentication, account selection, permission changes, or provider version changes. | Add | Implement one generated capability catalogue and runtime feature report. | V1 has no authoritative capability contract. |
| BRK-FR-CAP-006 | The adapter must not claim a capability as supported unless an implementation exists and its provider response path is covered by contract tests. | Add | Implement one generated capability catalogue and runtime feature report. | V1 has no authoritative capability contract. |
| BRK-FR-CAP-007 | Unsupported capability behavior must be deterministic and must not depend on catching missing provider attributes at runtime. | Add | Implement one generated capability catalogue and runtime feature report. | V1 has no authoritative capability contract. |
| BRK-FR-CAP-008 | Compose the canonical adapter from focused lifecycle, market-data, account, execution, and calculation capability protocols. | Add | Compose the adapter contract from focused market-data, account, execution, calculation, and lifecycle protocols; use shared unsupported implementations to keep deterministic methods. | This directly reduces the monolithic-interface risk. |
| BRK-FR-REG-001 | The domain must provide an explicit broker registry mapping canonical broker IDs to adapter factories. | Modify | Replace the V1 router/export map with an explicit registry of canonical broker/profile factories. | V1 proves resolution is needed, but its active-broker selection and module return type are unsafe. |
| BRK-FR-REG-002 | Adapter resolution must require an explicit broker ID. Unknown broker IDs must return BROKER_UNKNOWN. | Modify | Require an explicit canonical broker/profile ID and return `BROKER_UNKNOWN` for unknown IDs. | V1 accepts configuration strings and silently routes unknown values to MT5. |
| BRK-FR-REG-003 | The registry must never silently default an unknown or unavailable broker to MT5 or any other provider. | Modify | Remove every silent fallback, including the unconditional MT5 default. | Directly corrects `V1-ISSUE-BROKERS-001`. |
| BRK-FR-REG-004 | The registry must not select a provider based on symbol, route, environment, data availability, fallback priority, or business policy. | Modify | Keep selection policy outside Brokers; registry resolves only the exact ID supplied by Data or Trading. | V1’s active-broker setting mixes caller policy with technical resolution. |
| BRK-FR-REG-005 | Data owns data-source selection. Trading owns execution-broker selection. Brokers only resolves the explicit provider requested by the caller. | Modify | Data selects data providers and Trading selects execution providers before calling the registry. | Clarifies the split between V1 router use and Data gateway source selection. |
| BRK-FR-REG-006 | The registry must support independent adapter instances for different accounts, credentials, environments, and concurrent sessions. | Add | Factories create independent adapters for each account, credential set, environment, and session. | V1 singletons cannot safely represent concurrent sessions. |
| BRK-FR-REG-007 | A global singleton must not be the only supported lifecycle because it would allow account and credential state to leak between callers. | Modify | Remove singleton-only lifecycle; optional caller-owned reuse is allowed through explicit dependency injection. | V1 provider classes rely on process-global singleton instances. |
| BRK-FR-REG-008 | Optional provider SDKs must be imported lazily so unavailable SDKs do not break unrelated providers. | Keep | Preserve V1 lazy optional-provider imports in the new registry/factory implementation. | This V1 behaviour already prevents unrelated missing SDKs from breaking package import. |
| BRK-FR-REG-009 | Missing SDK dependency handling | Add | Keep providers registered when SDKs are missing and return `BROKER_DEPENDENCY_MISSING` with dependency metadata on use. | V1 lazy imports help, but no canonical missing-dependency result exists. |
| BRK-FR-REG-010 | Session ownership and adapter lifetime | Add | Composition creates adapters and the caller owns their deterministic lifetime; registry is factory-only. | Prevents hidden connection pools and state ownership. |
| BRK-FR-REG-011 | Dependency injection and session sharing boundaries | Add | Allow session sharing only through explicit dependency injection with documented ownership. | V1 has implicit process-wide sharing through singletons. |
| BRK-FR-CON-001 | connect() must validate only connection-level configuration required by the selected provider. | Modify | Implement as part of adapter lifecycle. | V1 lifecycle semantics are inconsistent or incomplete. |
| BRK-FR-CON-002 | Credentials and secrets must be supplied by the caller through BrokerConnectionConfig or an injected secret reference. | Modify | Implement as part of adapter lifecycle. | V1 lifecycle semantics are inconsistent or incomplete. |
| BRK-FR-CON-003 | Secrets must remain in memory only for the active adapter lifecycle unless the provider SDK manages its own secure token store. | Add | Implement as part of adapter lifecycle. | V1 lifecycle semantics are inconsistent or incomplete. |
| BRK-FR-CON-004 | Secrets, access tokens, passwords, private keys, and full account identifiers must never be logged or included in errors. | Modify | Implement as part of adapter lifecycle. | V1 lifecycle semantics are inconsistent or incomplete. |
| BRK-FR-CON-005 | connect() success must mean provider connectivity and required authentication were actually verified. Setting a local Boolean flag is insufficient. | Modify | Implement as part of adapter lifecycle. | V1 lifecycle semantics are inconsistent or incomplete. |
| BRK-FR-CON-006 | The connection status must distinguish transport connection, application authentication, account authentication, trading permission, and subscripti... | Modify | Implement as part of adapter lifecycle. | V1 lifecycle semantics are inconsistent or incomplete. |
| BRK-FR-CON-007 | Calling an operation requiring connection while disconnected must return BROKER_NOT_CONNECTED. | Modify | Implement as part of adapter lifecycle. | V1 lifecycle semantics are inconsistent or incomplete. |
| BRK-FR-CON-008 | disconnect() must close network sessions, terminal handles, subscriptions, reactors/tasks, and SDK resources owned by the adapter instance. | Modify | Implement as part of adapter lifecycle. | V1 lifecycle semantics are inconsistent or incomplete. |
| BRK-FR-CON-009 | disconnect() must be idempotent. | Modify | Implement as part of adapter lifecycle. | V1 lifecycle semantics are inconsistent or incomplete. |
| BRK-FR-CON-010 | reconnect() must not change provider, environment, credentials, or account unless the caller supplies a new configuration through a separate connec... | Add | Implement as part of adapter lifecycle. | V1 lifecycle semantics are inconsistent or incomplete. |
| BRK-FR-CON-011 | Token refresh must use only provider-supported refresh flows. | Modify | Implement as part of adapter lifecycle. | V1 lifecycle semantics are inconsistent or incomplete. |
| BRK-FR-CON-012 | The adapter must detect provider disconnect events and update connection state without waiting for a subsequent business call. | Modify | Implement as part of adapter lifecycle. | V1 lifecycle semantics are inconsistent or incomplete. |
| BRK-FR-CON-013 | Multiple adapter instances must not share mutable connection/account/subscription state unless the shared provider runtime explicitly requires it a... | Modify | Implement as part of adapter lifecycle. | V1 lifecycle semantics are inconsistent or incomplete. |
| BRK-FR-CON-014 | Account selection concurrency and session isolation | Modify | Initial adapters are immutable per provider/account/environment. `select_account()` returns unsupported unless a provider-specific, tested need later justifies safe switching. | Creating a new instance is simpler and safer than a complex in-place account-switch protocol. |
| BRK-FR-CON-015 | Allow connection timeout, request timeout, reconnect-attempt, and stream-buffer configuration. | Add | Implement as part of adapter lifecycle. | V1 lifecycle semantics are inconsistent or incomplete. |
| BRK-FR-CON-016 | When a session or token refresh fails, the adapter must immediately transition to BROKER_AUTHENTICATION_FAILED, cancel any pending in-flight reques... | Add | Implement as part of adapter lifecycle. | V1 lifecycle semantics are inconsistent or incomplete. |
| BRK-FR-CON-017 | In-flight subscription callbacks must receive a BROKER_CONNECTION_LOST event before the adapter attempts reconnection (if auto-reconnect is enabled). | Add | Implement as part of adapter lifecycle. | V1 lifecycle semantics are inconsistent or incomplete. |
| BRK-FR-CON-018 | After a successful reconnect+refresh, subscriptions may be transparently resumed only if the provider and adapter guarantee no data loss during the... | Add | Implement as part of adapter lifecycle. | V1 lifecycle semantics are inconsistent or incomplete. |
| BRK-FR-CON-019 | The adapter should implement a transport-level circuit breaker. | Modify | Maintain explicit degraded/failed transport state and fast failure. Do not add an independent policy-heavy circuit-breaker framework inside Brokers. | Connection state already provides the required protection; circuit policy belongs to callers. |
| BRK-FR-CON-020 | The adapter must support async context manager protocols (i.e. | Add | Implement as part of adapter lifecycle. | V1 lifecycle semantics are inconsistent or incomplete. |
| BRK-FR-CON-021 | If a provider returns scheduled maintenance headers or indicates active downtime, the adapter must update get_connection_status() status to reflect... | Add | Implement as part of adapter lifecycle. | V1 lifecycle semantics are inconsistent or incomplete. |
| BRK-FR-CON-022 | If a provider protocol requires periodic pings or heartbeats to keep a session (e.g. | Modify | Implement as part of adapter lifecycle. | V1 lifecycle semantics are inconsistent or incomplete. |
| BRK-FR-CON-023 | Explicit Connection Lifecycle State Machine | Modify | Use a minimal explicit lifecycle (`DISCONNECTED`, `CONNECTING`, `READY`, `DEGRADED`, `CLOSING`, `FAILED`) plus provider-specific substates where evidence requires them; validate transitions and cancel affected calls. | The ten-state mandatory graph is over-specified for simple HTTP providers. |
| BRK-FR-CON-024 | Connection recovery vs operation retries | Add | Implement as part of adapter lifecycle. | V1 lifecycle semantics are inconsistent or incomplete. |
| BRK-FR-CON-025 | Provider Environment Safety | Add | Implement as part of adapter lifecycle. | V1 lifecycle semantics are inconsistent or incomplete. |
| BRK-FR-CON-026 | Connection event streaming | Add | Implement as part of adapter lifecycle. | V1 lifecycle semantics are inconsistent or incomplete. |
| BRK-FR-READ-001 | Each operation must perform the minimum bounded provider interaction required by the provider protocol (e.g. | Modify | Retain the corresponding V1 provider read where present, but enforce bounded canonical result semantics and the accepted domain boundary. | V1 contains useful read behaviour, but its mapping, error, provenance, or ownership semantics must change. |
| BRK-FR-READ-002 | All read operations must strictly adhere to the out-of-scope boundaries defined in BRK-FR-OWN-001 (Section 3.2). | Modify | Retain the corresponding V1 provider read where present, but enforce bounded canonical result semantics and the accepted domain boundary. | V1 contains useful read behaviour, but its mapping, error, provenance, or ownership semantics must change. |
| BRK-FR-READ-005 | Provider-native symbol aliases may be translated only through explicit adapter mappings. | Modify | Retain the corresponding V1 provider read where present, but enforce bounded canonical result semantics and the accepted domain boundary. | V1 contains useful read behaviour, but its mapping, error, provenance, or ownership semantics must change. |
| BRK-FR-READ-006 | An empty valid provider result must return successful empty data, distinct from connection, permission, unsupported, and provider errors. | Add | Add the requirement to the canonical read contract and shared contract tests. | The behaviour is required for safe cross-provider reads and is not consistently present in V1. |
| BRK-FR-READ-007 | The adapter must preserve broker order, position, deal, and account identifiers exactly as supplied by the provider. | Modify | Retain the corresponding V1 provider read where present, but enforce bounded canonical result semantics and the accepted domain boundary. | V1 contains useful read behaviour, but its mapping, error, provenance, or ownership semantics must change. |
| BRK-FR-READ-008 | Provider response truncation or page limits must be explicit in the canonical page metadata. | Add | Add the requirement to the canonical read contract and shared contract tests. | The behaviour is required for safe cross-provider reads and is not consistently present in V1. |
| BRK-FR-READ-009 | Any malformed provider response must return BROKER_RESPONSE_INVALID; the adapter must not manufacture a success payload. | Modify | Retain the corresponding V1 provider read where present, but enforce bounded canonical result semantics and the accepted domain boundary. | V1 contains useful read behaviour, but its mapping, error, provenance, or ownership semantics must change. |
| BRK-FR-MUT-001 | Mutation methods perform direct provider submission only. They must not decide whether an order should be placed. | Keep | Preserve this direct single-target/no-policy behaviour in the final contract. | V1 already follows the essential boundary and the V2 rule prevents business logic from entering Brokers. |
| BRK-FR-MUT-002 | The caller must supply the complete canonical mutation request. Brokers may perform provider-required structural conversion only. | Modify | Refactor existing MT5/cTrader mutation behaviour to satisfy the canonical truthful single-operation contract. | V1 has useful direct submission logic, but request, acknowledgement, error, or provider-truth semantics are incomplete. |
| BRK-FR-MUT-003 | All mutation operations must strictly adhere to the out-of-scope boundaries defined in BRK-FR-OWN-001 (Section 3.2). | Keep | Preserve this direct single-target/no-policy behaviour in the final contract. | V1 already follows the essential boundary and the V2 rule prevents business logic from entering Brokers. |
| BRK-FR-MUT-004 | The adapter may validate provider-required fields and reject structurally invalid requests with BROKER_REQUEST_INVALID. | Modify | Refactor existing MT5/cTrader mutation behaviour to satisfy the canonical truthful single-operation contract. | V1 has useful direct submission logic, but request, acknowledgement, error, or provider-truth semantics are incomplete. |
| BRK-FR-MUT-005 | The canonical order request must support the direct provider fields needed across platforms, including symbol, side, order type, quantity and quant... | Modify | Refactor existing MT5/cTrader mutation behaviour to satisfy the canonical truthful single-operation contract. | V1 has useful direct submission logic, but request, acknowledgement, error, or provider-truth semantics are incomplete. |
| BRK-FR-MUT-006 | The domain must not generate business idempotency keys. | Add | Add the behaviour to the canonical mutation contract; unsupported providers return the standard unsupported result. | The requirement is necessary for safe execution and is not currently provided consistently. |
| BRK-FR-MUT-007 | Mutation success must be based on explicit provider acknowledgement. Local packaging, queueing, or request transmission alone is not success. | Modify | Refactor existing MT5/cTrader mutation behaviour to satisfy the canonical truthful single-operation contract. | V1 has useful direct submission logic, but request, acknowledgement, error, or provider-truth semantics are incomplete. |
| BRK-FR-MUT-008 | The adapter must not fabricate accepted order IDs, deal IDs, fills, prices, or success codes. | Modify | Refactor existing MT5/cTrader mutation behaviour to satisfy the canonical truthful single-operation contract. | V1 has useful direct submission logic, but request, acknowledgement, error, or provider-truth semantics are incomplete. |
| BRK-FR-MUT-009 | A timeout or connection loss after a mutation may have reached the provider must return BROKER_UNKNOWN_OUTCOME. | Add | Add the behaviour to the canonical mutation contract; unsupported providers return the standard unsupported result. | The requirement is necessary for safe execution and is not currently provided consistently. |
| BRK-FR-MUT-010 | In accordance with BRK-FR-OWN-001 (Section 3.2), the Brokers domain must not implement business retry policies for mutations. | Keep | Preserve this direct single-target/no-policy behaviour in the final contract. | V1 already follows the essential boundary and the V2 rule prevents business logic from entering Brokers. |
| BRK-FR-MUT-011 | Provider rejections must be returned as BROKER_REQUEST_REJECTED with the redacted provider code and message. | Modify | Refactor existing MT5/cTrader mutation behaviour to satisfy the canonical truthful single-operation contract. | V1 has useful direct submission logic, but request, acknowledgement, error, or provider-truth semantics are incomplete. |
| BRK-FR-MUT-012 | Partial fills and partial closes must be represented exactly as returned by the provider. | Add | Add the behaviour to the canonical mutation contract; unsupported providers return the standard unsupported result. | The requirement is necessary for safe execution and is not currently provided consistently. |
| BRK-FR-MUT-013 | A mutation method must affect only the one order or position identified in the request. | Keep | Preserve this direct single-target/no-policy behaviour in the final contract. | V1 already follows the essential boundary and the V2 rule prevents business logic from entering Brokers. |
| BRK-FR-MUT-014 | In accordance with BRK-FR-OWN-001 (Section 3.2), the domain must not provide automatic bulk mutations, liquidations, averaging, or complex multi-le... | Keep | Preserve this direct single-target/no-policy behaviour in the final contract. | V1 already follows the essential boundary and the V2 rule prevents business logic from entering Brokers. |
| BRK-FR-MUT-015 | Provider-side order validation or preview must be exposed through check_order() and must not be represented as final order acceptance. | Add | Add the behaviour to the canonical mutation contract; unsupported providers return the standard unsupported result. | The requirement is necessary for safe execution and is not currently provided consistently. |
| BRK-FR-SUB-001 | Each successful subscription must return a unique adapter-scoped subscription ID. | Add | Implement provider-scoped canonical subscription behaviour where supported; otherwise deterministic unsupported. | V1 lacks a safe common streaming contract. |
| BRK-FR-SUB-002 | Subscription callbacks/events must use canonical broker event DTOs and must not expose provider SDK message objects. | Modify | Refactor cTrader subscription behaviour into the canonical adapter-scoped stream contract. | V1 provides partial subscription value but lacks uniform lifecycle, error, and delivery semantics. |
| BRK-FR-SUB-003 | The adapter must report disconnect, resubscription-required, provider-error, and permission-change events to the subscriber. | Add | Implement provider-scoped canonical subscription behaviour where supported; otherwise deterministic unsupported. | V1 lacks a safe common streaming contract. |
| BRK-FR-SUB-004 | Automatic resubscription may occur only when it cannot cause a broker mutation and the adapter reports the reconnection event. | Add | Implement provider-scoped canonical subscription behaviour where supported; otherwise deterministic unsupported. | V1 lacks a safe common streaming contract. |
| BRK-FR-SUB-005 | Unsubscribing an unknown subscription must return a deterministic not-found result and must not affect other subscriptions. | Modify | Refactor cTrader subscription behaviour into the canonical adapter-scoped stream contract. | V1 provides partial subscription value but lacks uniform lifecycle, error, and delivery semantics. |
| BRK-FR-SUB-006 | disconnect() must terminate all subscriptions owned by that adapter instance. | Modify | Refactor cTrader subscription behaviour into the canonical adapter-scoped stream contract. | V1 provides partial subscription value but lacks uniform lifecycle, error, and delivery semantics. |
| BRK-FR-SUB-007 | The adapter must not persist event streams or subscription data. | Keep | Preserve the non-persistence boundary for streams and subscriptions. | V1 does not demonstrate broker-domain stream persistence, and the rule is appropriate. |
| BRK-FR-SUB-008 | Bounded Event Buffer and Overflow Semantics | Modify | Refactor cTrader subscription behaviour into the canonical adapter-scoped stream contract. | V1 provides partial subscription value but lacks uniform lifecycle, error, and delivery semantics. |
| BRK-FR-SUB-009 | Streaming Delivery and Callback Semantics | Modify | Refactor cTrader subscription behaviour into the canonical adapter-scoped stream contract. | V1 provides partial subscription value but lacks uniform lifecycle, error, and delivery semantics. |
| BRK-FR-PROV-001 | Limit provider modules to SDK integration, lifecycle, request/response mapping, errors, capabilities, and private helpers. | Modify | Apply to every provider implementation. | Keeps provider modules thin and prevents cross-domain leakage. |
| BRK-FR-PROV-002 | Provider modules must strictly adhere to the out-of-scope ownership boundaries defined in BRK-FR-OWN-001 (Section 3.2). | Modify | Apply to every provider implementation. | Keeps provider modules thin and prevents cross-domain leakage. |
| BRK-FR-PROV-003 | Each adapter must implement every standard public operation, including unsupported methods. | Modify | Every adapter implements the accepted composite capability protocols with deterministic shared unsupported methods; do not force speculative operations outside the accepted catalogue. | Retains uniformity while avoiding uncontrolled interface growth. |
| BRK-FR-PROV-004 | Provider-specific extension methods must remain private unless added to the canonical contract for all adapters. | Modify | Apply to every provider implementation. | Keeps provider modules thin and prevents cross-domain leakage. |
| BRK-FR-PROV-005 | Provider-native constants must not become the cross-domain public contract. Canonical enums and DTOs must be used. | Modify | Apply to every provider implementation. | Keeps provider modules thin and prevents cross-domain leakage. |
| BRK-FR-PROV-006 | MT5 and cTrader compatibility must be achieved through canonical contracts, not by pretending one provider is the other or copying another provider... | Modify | Apply to every provider implementation. | Keeps provider modules thin and prevents cross-domain leakage. |
| BRK-FR-PROV-007 | Yahoo Finance ticks must return unsupported unless the selected Yahoo integration supplies genuine provider tick data. | Modify | Remove V1 Yahoo synthetic ticks; return unsupported unless a genuine Yahoo tick source is implemented. | V1 synthetic ticks are explicitly incompatible with provider truth. |
| BRK-FR-PROV-008 | Dukascopy trading methods must return unsupported unless a genuine authenticated trading API is implemented and verified. | Add | Declare every Dukascopy trading/account mutation capability unsupported unless a genuine authenticated API is added and verified. | V1 Dukascopy implementation is read-only. |
| BRK-FR-PROV-009 | Binance Product Profiles | Modify | Register `BINANCE_SPOT`, `BINANCE_USD_M_FUTURES`, and `BINANCE_COIN_M_FUTURES` as immutable profiles. Implement Spot first; defer Futures mutation capability until sandbox verified. | The profile split is sound, but V1 provides no Futures/trading evidence. |
| BRK-FR-PROV-010 | No provider adapter may advertise trading capability solely because its SDK contains an order method; authenticated permission and a tested respons... | Add | Apply to every provider implementation. | Keeps provider modules thin and prevents cross-domain leakage. |
| BRK-FR-API-001 | app/services/brokers/__init__.py must expose only canonical contracts, registry/factory entry points, capability identifiers, and approved adapter... | Modify | Use the canonical public package surface. | Needed to stop direct provider coupling. |
| BRK-FR-API-002 | __init__.py must contain no connection, provider, routing, conversion, or business logic. | Keep | Keep `__init__.py` limited to exports/lazy resolution; move all provider and conversion logic into focused modules. | V1 package root already contains only lazy export logic. |
| BRK-FR-API-003 | Expose `create_broker_adapter`, registered-broker listing, and capability-catalogue entry points. | Modify | Use the canonical public package surface. | Needed to stop direct provider coupling. |
| BRK-FR-API-004 | Consumers must import the public domain API rather than provider implementation files, except provider-specific integration tests. | Modify | Use the canonical public package surface. | Needed to stop direct provider coupling. |
| BRK-FR-API-005 | The domain must not expose AI tools directly. Data, Trading, or UI/API may expose governed tools that call their own business workflows. | Modify | Use the canonical public package surface. | Needed to stop direct provider coupling. |
| BRK-FR-API-006 | Provide a complete deterministic fake/mock adapter for calling-domain tests. | Add | Provide a deterministic fake adapter in test utilities, not as a production runtime provider. | Calling-domain tests need a complete non-networked contract double. |
| BRK-FR-OBS-001 | The domain must log connection transitions, authentication outcomes, provider calls, provider errors, subscription transitions, and mutation acknow... | Modify | Standardize existing logging around redaction, correlation, and latency. | V1 logging is valuable but not contractually uniform. |
| BRK-FR-OBS-002 | Logs must include broker ID, operation, request/correlation ID, environment, redacted account reference, result status, provider code, and latency... | Add | Standardize existing logging around redaction, correlation, and latency. | V1 logging is valuable but not contractually uniform. |
| BRK-FR-OBS-003 | Logs must never include secrets or complete private account credentials. | Modify | Formalize redaction tests and prohibit secrets/full account identifiers in all logs and errors. | V1 logging exists, but the audit could not prove complete redaction. |
| BRK-FR-OBS-004 | Every broker interaction must be technically reconstructable using timestamp, broker/adapter name, operation, correlation ID, redacted request payl... | Modify | Require reconstructable redacted summaries and provider references. Defer a secure full-payload audit sink until an operational retention/security design exists. | The sink is infrastructure-heavy and not necessary for the initial domain boundary. |
| BRK-FR-OBS-005 | Unknown mutation outcomes must be logged at error severity with enough provider references for Trading to reconcile. | Add | Standardize existing logging around redaction, correlation, and latency. | V1 logging is valuable but not contractually uniform. |
| BRK-FR-OBS-006 | Propagate distributed trace context through adapter calls and `BrokerResult`. | Defer | Propagate caller request/correlation IDs now; add OpenTelemetry trace-context integration when the system-wide observability contract is confirmed. | Avoids a Brokers-only tracing dependency before shared observability is standardized. |
| BRK-NFR-001 | Keep Brokers free of business logic and enforce the accepted ownership boundary. | Modify | Adopt as an architectural quality requirement. | Supports a thin, independent provider boundary. |
| BRK-NFR-002 | Thread and concurrency safety | Add | Adopt as an architectural quality requirement. | Supports a thin, independent provider boundary. |
| BRK-NFR-003 | Keep canonical wrapping and telemetry overhead minimal and bounded. | Modify | Adopt as an architectural quality requirement. | Supports a thin, independent provider boundary. |
| BRK-NFR-004 | Allow Brokers to compile, test, and operate independently of business domains. | Modify | Adopt as an architectural quality requirement. | Supports a thin, independent provider boundary. |
| BRK-NFR-005 | Adding a provider must not require changes in Data, Trading, or other consumers. | Modify | A new provider should require only focused capability implementations, declarations, tests, and registration; consumers remain unchanged. | Requiring every provider to implement all speculative operations would reduce extensibility. |
| BRK-NFR-006 | Deterministic unsupported behavior | Add | Adopt as an architectural quality requirement. | Supports a thin, independent provider boundary. |
| BRK-NFR-007 | Performance budgets and latency observability | Modify | Measure provider latency and local wrapping overhead and prevent event-loop blocking; reject the universal p99 `<100 µs` DTO-mapping gate until benchmarked per runtime and DTO size. | The numeric budget is unsupported by evidence and may be unrealistic in Python. |
| BRK-NFR-008 | Blocking SDK isolation | Add | Adopt as an architectural quality requirement. | Supports a thin, independent provider boundary. |
| V2-NORM-001 | Brokers owns all direct real provider connectivity; Data/Trading own business workflows. | Keep | Adopt the boundary and later verify it against the top-level system document. | Corrects V1 overlap and direct provider coupling. |
| V2-NORM-002 | Initial providers: MT5, cTrader, Binance Spot/Futures, Dukascopy, Yahoo. | Modify | MT5, cTrader, Binance Spot, Dukascopy, and Yahoo bars are initial; Binance Futures profiles are registered but mutation capability is deferred until verified. | V1 provides no authenticated Futures evidence. |
| V2-NORM-003 | Every provider exposes one complete common adapter interface. | Modify | Use a composite of focused capability protocols with shared deterministic unsupported methods. | Prevents a single enormous implementation file while preserving uniform calls. |
| V2-NORM-004 | Unsupported capability returns canonical error and makes no SDK call. | Add | Adopt exactly as a core safety rule. | Eliminates V1 approximation and missing-method ambiguity. |
| V2-NORM-005 | Normative core operations in Section 5.4. | Modify | Accept lifecycle, capability, account, symbols, genuine market data, subscriptions, single-target mutations, and reads; unsupported operations remain explicit. | The behavioural surface is valid when composed and capability-driven. |
| V2-NORM-006 | All Section 6 standard operations exist on every adapter. | Modify | Keep the accepted operation catalogue, but stage implementation by proven workflows; unsupported defaults remain deterministic. | Avoids implementing unverified provider features merely for completeness. |
| V2-NORM-007 | Data, execution, and account-state cross-domain workflow boundaries. | Keep | Adopt the stated input → Brokers responsibility → caller-owned output boundaries. | Matches the desired clean domain separation. |
| V2-NORM-008 | Explicitly forbidden behaviours in Section 21. | Keep | Adopt all prohibitions, especially no silent selection, synthetic truth, database access, bulk business mutations, or raw SDK leakage. | Directly addresses major V1 defects. |
| V2-NORM-009 | Definition of Done in Section 22. | Modify | Use it after applying this reconciliation’s simplifications and staged-provider decisions. | Several checklist items assume rejected/deferred implementation details. |
| V2-NORM-010 | Required project documentation and ADR changes. | Defer | Record as mandatory input to pipeline step 05/top-level alignment; do not modify system documents in this step. | This reconciliation is intentionally domain-only. |

### Accepted behaviour and simplified implementation

**Accepted behaviour**

* Explicit broker/provider selection with no fallback.
* Caller-supplied connection configuration and secrets.
* Truthful provider responses mapped to canonical result/error/DTO contracts.
* Canonical capability reporting and deterministic unsupported outcomes.
* Genuine provider market data only.
* Single-target provider reads and mutations.
* No business retries, risk policy, idempotency policy, reconciliation authority, persistence, or data normalization in Brokers.
* Independent adapter instances and explicit dependency injection.
* Shared contract, boundary, and fake-adapter tests.

**Rejected, deferred, or simplified implementation**

* A mandatory second synchronous adapter façade is deferred.
* The strict typed-exception façade is rejected for the initial rebuild; canonical adapters remain result-based.
* The full priority/weighted rate-limit queue is deferred; provider-required bounded throttling remains.
* The ten-state universal lifecycle graph is reduced to a smaller validated state model.
* Runtime account switching is not part of the initial contract; create a new immutable adapter instance.
* DTOs are created for accepted operations, not speculatively for unused capabilities.
* Contract versions are carried at result/capability/adapter level, not repeated on every nested DTO.
* Per-bar timezone evidence moves to page/result metadata.
* Binance Futures mutations are deferred until sandbox verified.
* Mandatory OpenTelemetry integration and secure full-payload audit infrastructure are deferred to system-wide observability design.
* The unproven p99 `<100 µs` local mapping gate is rejected; measurement and non-blocking design remain.
* External sandbox tests are credential-gated and scheduled/release-gated, not required on every ordinary CI run.

## 7. Workflow Reconciliation

| Final workflow ID | Workflow | Scope | V1 status | V2 proposal | Decision | Final boundary and outcome |
|---|---|---|---|---|---|---|
| WF-BRK-001 | Resolve explicit broker adapter | Internal | `V1-WF-BROKERS-001/002`: lazy exports plus configured router; partial and unsafe | Explicit registry/factory | Replace | Caller provides broker/profile ID and config → registry lazy-loads factory → independent adapter or canonical error. |
| WF-BRK-002 | Connect and authenticate provider session | Internal | `V1-WF-BROKERS-004/007`: provider-specific, often singleton/auto-connect | Verified async lifecycle | Modify | Connection config input → provider transport/authentication → truthful status/capabilities → caller-owned adapter session. |
| WF-BRK-003 | Acquire provider market data | Cross-domain | `V1-WF-BROKERS-003`: working static gateway path | Data acquisition boundary | Modify | Data selects explicit source → Brokers returns direct canonical provider page/stream → Data owns validation, normalization, cache, persistence. |
| WF-BRK-004 | Submit one broker mutation | Cross-domain | `V1-WF-BROKERS-006`: trading router → MT5/cTrader trade | Approved execution boundary | Modify | Trading completes policy/idempotency → calls explicit adapter mutation → Brokers returns provider acknowledgement/error → Trading reconciles and persists. |
| WF-BRK-005 | Read account/order/position truth | Cross-domain | `V1-WF-BROKERS-005/006`: direct MT5 and routed reads | Account-state snapshot boundary | Modify | Data or Trading requests bounded provider state → Brokers returns canonical provider truth with timestamps → caller assesses freshness/reconciliation. |
| WF-BRK-006 | Stream quotes and connection events | Cross-domain | Partial cTrader-only support in `V1-WF-BROKERS-007` | Canonical subscription workflow | Add | Caller subscribes → adapter yields canonical bounded events → disconnect/backpressure/resync is explicit → caller rebuilds owned state. |
| WF-BRK-007 | Load MT5 data with stored credentials | Cross-domain | `V1-WF-BROKERS-004`: Brokers reads user DB and returns tool envelope | V2 forbids credential persistence and Data overlap | Replace | Composition root resolves secret/config → Data creates adapter → Data calls bars → Data owns envelope/normalization; Brokers never reads the DB. |
| WF-BRK-008 | Inject broker into live execution | Cross-domain | `V1-WF-BROKERS-005`: live runtime receives concrete `MT5Client` | Canonical dependency injection | Replace | Composition root creates explicit adapter → Trading/runtime receives canonical broker capability → no direct MT5 class dependency. |
| WF-BRK-009 | cTrader request/response correlation | Internal | `V1-WF-BROKERS-007`: payload-type matching and compatibility wrappers | Safe correlated provider exchange | Modify | Adapter correlates each request to its provider request ID/session generation → decodes response → canonical result; stale/mismatched callbacks are discarded. |
| WF-BRK-010 | Unsupported provider operation | Internal | V1 methods may be absent, approximate, or return fabricated data | Deterministic unsupported outcome | Add | Capability check/method call → no SDK call → `BROKER_CAPABILITY_UNSUPPORTED` with broker, operation, and capability metadata. |

### `WF-BRK-001` — Resolve Explicit Broker Adapter

**Scope:** `Internal`

**V1 behaviour:**

```text
Package import or Trading request
→ V1 lazy export or configured active-broker router
→ cTrader/simulator branch
→ otherwise MT5, including unknown values
```

**V2 proposal:**

```text
Caller supplies canonical broker/profile ID and connection config
→ public registry resolves a lazily imported factory
→ factory creates an independent adapter
→ unknown/missing dependency returns canonical error
```

**Final decision:**

```text
Replace V1 active-broker routing. Preserve lazy optional imports, but broker choice belongs to Data or Trading and must always be explicit.
```

**Reason:**

Silent MT5 fallback and the absent simulator target are unsafe. Registry resolution is a technical factory operation, not execution policy.

### `WF-BRK-002` — Connect and Authenticate Provider Session

**Scope:** `Internal`

**V1 behaviour:**

```text
Provider singleton/client
→ often reads global settings
→ may auto-connect on first operation
→ local flag or provider-specific state indicates readiness
```

**V2 proposal:**

```text
Caller-owned adapter plus explicit config
→ validated transport connection
→ provider authentication/account authorization
→ truthful connection status and capability refresh
→ deterministic disconnect
```

**Final decision:**

```text
Modify and reuse provider protocol knowledge. Remove hidden auto-connect by default, global settings ownership, and singleton-only lifecycle.
```

**Reason:**

One session per adapter prevents account/environment leakage and makes cleanup testable.

### `WF-BRK-003` — Acquire Provider Market Data

**Scope:** `Cross-domain`

**V1 behaviour:**

```text
Data gateway selects V1 provider client
→ connect/is_connected
→ get_bars/get_ticks
→ provider-specific frame/empty/error shape
→ Data normalization/cache
```

**V2 proposal:**

```text
Data selects explicit provider
→ creates/receives canonical market-data capability
→ Brokers performs bounded provider call
→ returns canonical page/result
→ Data validates, normalizes, caches, and persists
```

**Final decision:**

```text
Modify. Preserve provider retrieval and decoding; remove synthetic/fixed/assumed values and standardize errors, pagination, time, and units.
```

**Reason:**

V1 proves the workflow’s value, while V2 correctly limits Brokers to direct provider truth.

### `WF-BRK-004` — Submit One Broker Mutation

**Scope:** `Cross-domain`

**V1 behaviour:**

```text
Trading validates and selects routed broker module
→ broker.trade(request)
→ MT5/cTrader provider call
→ normalized Trading result and reconciliation
```

**V2 proposal:**

```text
Trading completes approval, readiness, idempotency, and route selection
→ sends one canonical mutation to an explicit adapter
→ Brokers submits once
→ returns acknowledgement, rejection, or unknown outcome
→ Trading reconciles and persists
```

**Final decision:**

```text
Modify. Reuse provider submission logic, but replace MT5-shaped cross-provider requests and fabricated cTrader success with canonical truthful contracts.
```

**Reason:**

Trading policy stays outside Brokers; Brokers must still preserve uncertain-transmission semantics.

### `WF-BRK-005` — Read Account, Order, Position, and Deal Truth

**Scope:** `Cross-domain`

**V1 behaviour:**

```text
Trading/live/risk code calls concrete MT5 or routed MT5-shaped functions
→ provider objects/wrappers returned
→ caller interprets and reconciles
```

**V2 proposal:**

```text
Data or Trading requests a bounded canonical read
→ Brokers returns provider truth, timestamps, identifiers, and pagination
→ caller builds snapshots or reconciliation state
```

**Final decision:**

```text
Modify. Preserve reads, correct cTrader field mappings, and stop raw objects/default compatibility fields crossing the boundary.
```

**Reason:**

These reads are essential, but snapshot freshness, persistence, and reconciliation belong to the caller.

### `WF-BRK-006` — Stream Quotes and Connection Events

**Scope:** `Cross-domain`

**V1 behaviour:**

```text
cTrader subscribes to spots and maintains callback/tick caches
→ no shared provider-neutral stream contract
→ disconnect/resync semantics vary
```

**V2 proposal:**

```text
Caller obtains supported streaming capability
→ subscription returns adapter-scoped ID/async iterator
→ bounded FIFO delivery of canonical events
→ explicit connection loss, backpressure, and resync requirement
```

**Final decision:**

```text
Add a common workflow, reusing cTrader transport/subscription code. Providers without genuine streaming return unsupported.
```

**Reason:**

Streaming is a real provider responsibility, but the consumer owns normalized state and recovery actions.

### `WF-BRK-007` — Stored-Credential MT5 Data Load

**Scope:** `Cross-domain`

**V1 behaviour:**

```text
Broker wrapper reads UserManager/database credentials
→ connects non-singleton MT5 client
→ fetches and normalizes bars
→ returns tool/status envelope
→ disconnects
```

**V2 proposal:**

```text
Composition root resolves secret/config
→ Data creates adapter
→ Data requests historical bars
→ Brokers returns provider data
→ Data owns normalization, caching, and presentation envelope
```

**Final decision:**

```text
Replace and remove the V1 Brokers workflow after caller migration.
```

**Reason:**

Credential persistence, user lookup, data normalization, and AI/tool envelopes violate the accepted boundary.

### `WF-BRK-008` — Inject Broker into Live Execution

**Scope:** `Cross-domain`

**V1 behaviour:**

```text
Live API/session obtains concrete MT5Client
→ injects it into live engine
→ engine calls MT5-native surface
```

**V2 proposal:**

```text
Composition root creates explicit canonical adapter
→ Trading/runtime depends on required capability protocols
→ no provider class or SDK surface crosses the boundary
```

**Final decision:**

```text
Replace direct MT5 injection with canonical dependency injection. Preserve the caller-owned session pattern.
```

**Reason:**

V1 confirms dependency injection value but couples execution to one provider.

### `WF-BRK-009` — cTrader Request and Response Correlation

**Scope:** `Internal`

**V1 behaviour:**

```text
send_request installs temporary callback
→ matches only response payload type
→ decodes response or timeout
→ compatibility wrapper/result
```

**V2 proposal:**

```text
Create request correlation token plus session generation
→ provider request
→ accept only matching response
→ discard stale responses
→ map provider payload/error to canonical result
```

**Final decision:**

```text
Modify the internal workflow; do not expose correlation machinery publicly.
```

**Reason:**

Payload-type-only matching can misroute concurrent responses.

### `WF-BRK-010` — Unsupported Provider Operation

**Scope:** `Internal`

**V1 behaviour:**

```text
Method may be absent, approximated, silently mapped, or return synthetic/default values
```

**V2 proposal:**

```text
Capability declaration reports unsupported
→ method makes no SDK call
→ returns `BROKER_CAPABILITY_UNSUPPORTED`
→ result identifies provider, operation, and capability
```

**Final decision:**

```text
Add and enforce through shared default implementations and contract tests.
```

**Reason:**

Deterministic unsupported outcomes are safer than simulation or provider-specific branching.

## 8. Recommended Minimal Capability Structure

```text
app/services/brokers/
├── contracts/        # Canonical results, errors, DTOs, enums, and focused capability protocols
├── registry/         # Explicit lazy factory and capability catalogue
├── mt5/              # MT5 provider integration
├── ctrader/          # cTrader provider integration
├── binance/          # Immutable Binance product-profile integrations
├── dukascopy/        # Read-only Dukascopy integration
├── yahoo/            # Read-only Yahoo historical-bar integration
└── testing/          # Fake adapter and shared contract-test fixtures
```

This is a capability-level structure only. The final README will decide focused files and public symbols. Provider folders may contain multiple focused files when lifecycle, market data, account reads, or mutations are too large for one file; no additional service/manager/repository/command layers are approved.

| Module | Capability | Source | Main decision |
|---|---|---|---|
| `contracts` | Canonical provider-neutral boundary | V2 plus V1 failure evidence | Add |
| `registry` | Explicit resolution, lazy imports, factories, capability catalogue | Both | Modify |
| `mt5` | MT5 lifecycle, reads, market data, and single mutations | V1 | Modify |
| `ctrader` | cTrader lifecycle, protocol requests, reads, streams, and single mutations | V1 | Modify |
| `binance` | Spot market data and staged trading; separate Futures profiles | Both | Modify |
| `dukascopy` | Read-only provider market data and symbols | V1 | Modify |
| `yahoo` | Genuine provider historical bars only | V1 | Split |
| `testing` | Fake adapter and shared contract fixtures | V2 | Add |

## 9. Reuse and Migration Plan

| Priority | Existing V1 item | Migration action | Target capability | Validation required |
|---:|---|---|---|---|
| 1 | V1 public call inventory and direct MT5 native callers | Audit migration surface; freeze new direct imports | All | Confirm every Data, Trading, Live, Risk, and API caller before removing compatibility |
| 2 | New canonical contracts | New | `CAP-BRK-003/004` | DTO/error/result unit tests; no raw SDK leakage; UTC/Decimal tests |
| 3 | `__init__.py` lazy export mechanism and `router.py` | Refactor | `CAP-BRK-001/017` | Unknown broker test; missing dependency test; independent-instance test |
| 4 | `MT5Client` provider calls | Refactor | `CAP-BRK-002/005/006/008/009/010/011/012` | Blocking-call isolation, live/demo mismatch, provider acknowledgement, contract tests |
| 5 | `CTraderClient` auth/request/decoding | Refactor | `CAP-BRK-002/006/007/008/009/010/011/013` | Request correlation, reactor cleanup, no fabricated fields, sandbox tests |
| 6 | Data gateway broker factories and private cTrader loader | Replace consumer integration | `WF-BRK-003` | Data uses only public canonical protocols; no provider imports/private loaders |
| 7 | Trading routed module calls and live MT5 injection | Replace consumer integration | `WF-BRK-004/005/008` | Trading selects explicit adapter; unknown outcomes and reconciliation tests |
| 8 | Binance V1 client | Refactor | `CAP-BRK-014` | Strict timeframe mapping, real connectivity, Spot sandbox permissions; Futures remain unsupported until tested |
| 9 | Dukascopy scraper/client and instrument map | Refactor | `CAP-BRK-015` | Endpoint/terms decision, resolvable aliases, explicit HTTP failures, bounded pagination |
| 10 | Yahoo bars | Refactor | `CAP-BRK-016` | Proven provider bar semantics and unsupported quote/tick tests |
| 11 | Yahoo synthetic tick path | Remove | None | Confirm consumer migration and provenance correction |
| 12 | MT5 credential/tool/data wrappers | Remove | Caller/Data workflows | Confirm no dynamic tool registry or external consumer uses the legacy names |
| 13 | MT5Api, compatibility wrappers, module-level provider functions | Remove after cutover | Canonical adapters | Contract parity and all caller imports migrated |
| 14 | Provider singletons and implicit auto-connect | Remove | `CAP-BRK-002/017` | Multi-account isolation, deterministic disconnect, no state leakage |
| 15 | V1 package tests | Reuse/refactor | `CAP-BRK-019` | Shared contract suite plus provider-specific tests pass |

## 10. Simplifications from V2

| V2 proposal | Problem | Simplified final direction |
|---|---|---|
| One giant adapter exposing every proposed operation directly | Encourages bloated provider files and speculative methods | Compose focused lifecycle, market-data, account, execution, and calculation protocols with shared unsupported defaults |
| Mandatory separate `SyncBrokerAdapter` | Duplicates the complete public surface before a consumer proves the need | Async-first contract; isolate blocking SDK calls; add a sync wrapper only for a confirmed use case |
| `StrictBrokerAdapter` typed exception façade | Creates a second error mode and exception hierarchy | Canonical result-only adapters; cancellation/fatal exceptions still propagate |
| Universal weighted priority throttling queue | Complex scheduling can become execution policy and is not required by every provider | Provider-required bounded throttling and header awareness; fail-fast backpressure initially |
| Exact ten-state lifecycle graph for every adapter | Over-specified for simple HTTP providers and costly to implement uniformly | Minimal validated state set with provider-specific substates only where needed |
| Safe in-place account switching | Requires locks, cancellation, generation tracking, and subscription teardown | One immutable adapter per provider/account/environment; create a new instance |
| Every listed DTO created immediately | Large speculative contract with unused types | Create canonical DTOs as accepted capabilities are implemented |
| All order fields in one universal request | Mixes Spot, CFD, Forex, and derivatives semantics | Core order request plus product-profile-specific optional structures |
| Contract/version fields on every nested DTO | Repetitive payload and mapping overhead | Version result envelope, capability report, and adapter; nested DTOs inherit contract version |
| Timezone-conversion evidence on every bar | Duplicates metadata for every row | Store conversion evidence once in page/result metadata unless records differ |
| Full callback and async-iterator APIs as equal primary surfaces | Doubles stream complexity | Async iterator is primary; callback wrapper is optional and isolated |
| Sequence ranges required even when provider lacks them | Would force invented transport evidence | Preserve provider sequence IDs; use clearly labeled adapter delivery sequence only |
| Mandatory OpenTelemetry integration | Premature provider-domain dependency before system observability is finalized | Preserve request/trace correlation fields; integrate tracing through a later shared contract |
| Secure full-payload audit sink in initial domain | Requires system-wide storage, security, retention, and access-control design | Redacted reconstructable logs now; secure sink deferred |
| Universal p99 DTO mapping `<100 µs` | No benchmark evidence and payload sizes differ | Measure local overhead separately; set budgets after representative benchmarks |
| Every sandbox suite on ordinary CI | Credentials, terminals, and external providers are not reliably available | Deterministic contract tests in CI; sandbox/testnet suites scheduled or release-gated |
| Binance Spot and both Futures fully trading-capable immediately | V1 only proves public market data | Implement Spot first; register distinct Futures profiles and keep trading unsupported until verified |

## 11. Open Decisions

| Status | Decision required | Evidence available | Options | Affected capabilities |
|---|---|---|---|---|
| Open — escalate to system document | Which composition-root/secret facility creates `BrokerConnectionConfig` without Brokers reading user databases? | V1 uses `UserManager`; V2 forbids credential persistence in Brokers | Utils secret reference; application composition root; Trading/Data-owned secret resolution | `CAP-BRK-002/017`, `WF-BRK-002/003/004` |
| Open — escalate to system document | Which exact native MT5 methods are still required by Live, Risk, and API callers before `MT5Client.__getattr__` is removed? | V1 audit confirms direct/native use but not the complete runtime method set | Add accepted methods to canonical capabilities; migrate ownership; retain temporary compatibility shim | `CAP-BRK-012`, `WF-BRK-008` |
| Open — domain internal | Is the Dukascopy freeserv scraping endpoint approved for production use and redistribution? | V1 proves an HTTP scraper and source diversity; no contractual/operational evidence supplied | Keep production provider; development-only; remove | `CAP-BRK-015` |
| Open — domain internal | Are all `INSTRUMENT_MAP` aliases intended to be accepted inputs or only discovery labels? | V1 audit shows listing and fetch paths disagree | Normalize all aliases; expose only resolvable symbols; remove alias catalogue | `CAP-BRK-005/015` |
| Open — cross-domain verification | Does any external AI-tool registry, deployment script, or consumer call `load_mt5`, `mt5_data_*`, or `load_dukascopy` by string name? | V1 audit found exports/tests but no conclusive production callers | Migrate and remove; temporary deprecation shim; retain outside Brokers | `V1-CAP-BROKERS-007/012/013` |
| Open — domain internal | Can cTrader SDK/protobuf requests expose a reliable request/correlation identifier for all concurrent operations? | V1 matches responses by payload type only | Native request ID; adapter correlation map; serialized same-response-type requests | `CAP-BRK-013`, `WF-BRK-009` |
| Open — escalate to system document | What is the release gate for changing an adapter capability from `NOT_TESTED` to available for live mutation? | V2 asks for sandbox verification; provider credentials/test environments are unavailable | Sandbox pass plus manual approval; live canary; provider-specific evidence policy | `CAP-BRK-004/010/014/019` |
| Open — domain internal | Are Yahoo Finance historical bars acceptable for production-grade data provenance and usage terms? | V1 proves yfinance bars but no operational/legal evidence | Production read-only; research-only; remove provider | `CAP-BRK-016` |

## 12. Inputs for the Final Domain README

### Approved capabilities

* Explicit lazy broker/profile registry and caller-owned adapter factories.
* Verified provider connection/authentication/session lifecycle.
* Canonical result, error, DTO, enum, unit, UTC, and pagination contracts.
* Complete generated capability catalogue and deterministic unsupported outcomes.
* Provider symbols, metadata, account, balance, permission, order, position, deal, and transaction reads where genuinely supported.
* Genuine provider quotes, ticks, bars, order books, and streams where genuinely supported.
* Single-target order/position mutations with explicit acknowledgement and unknown-outcome handling.
* Provider-native margin, profit, and fee calculations only.
* MT5, cTrader, Binance Spot, read-only Dukascopy, and Yahoo historical bars.
* Separate registered Binance Futures profiles with mutations unavailable until verified.
* Structured redacted observability and shared contract/boundary tests.

### Approved workflows

* Explicit adapter resolution.
* Connect/authenticate/disconnect a caller-owned provider session.
* Data acquisition through Brokers, with Data owning downstream processing.
* Approved Trading mutation through Brokers, with Trading owning policy and reconciliation.
* Bounded account/order/position/deal reads.
* Canonical quote and connection event subscriptions.
* Deterministic unsupported-operation handling.
* Canonical dependency injection into live execution.

### V1 behaviours to preserve

* Lazy optional provider imports from `V1-CAP-BROKERS-001`.
* MT5 terminal/provider calls, bars, ticks, account/order/position/deal reads, and direct mutation from `V1-CAP-BROKERS-003`–`006`.
* cTrader authentication, protocol request/response decoding, data reads, and mutation translation from `V1-CAP-BROKERS-008`–`011`.
* Dukascopy, Binance, and Yahoo provider retrieval where results are genuine from `V1-CAP-BROKERS-012`, `014`, and `015`.
* Data gateway’s proven need for a common provider capability shape from `V1-CAP-BROKERS-017`.
* Caller-owned live-session injection concept from `V1-WF-BROKERS-005`.

### V1 behaviours to modify

* Replace configured active broker and silent MT5 fallback with explicit registry resolution.
* Replace global singletons and implicit auto-connect with independent explicit sessions.
* Replace provider/native objects and MT5-shaped cTrader compatibility with canonical DTOs.
* Correct cTrader request correlation, position profit mapping, and failure handling.
* Replace empty/`None`/exception/error-dictionary inconsistency with canonical results.
* Replace fixed/zero/assumed spread and price fields with provider values or null/unsupported.
* Align Dukascopy discovery aliases with actual fetch inputs.
* Move Data normalization, caching, serialization, and envelopes out of provider modules.
* Migrate live execution from concrete `MT5Client` injection to canonical capability injection.

### V1 behaviours to remove

* Stored-credential/database access and `load_mt5`/`mt5_data_*` broker-owned data tools, after dynamic callers are verified and migrated.
* Yahoo synthetic ticks, after consumers stop treating Yahoo as a genuine tick source.
* Fabricated cTrader quote prices, fallback order IDs, fixed success retcodes, and guessed compatibility fields.
* Unknown-provider fallback to MT5.
* Broken Brokers-owned simulator route.
* Second MT5 provider wrapper (`MT5Api`) and raw delegated public SDK surface after contract parity.
* Private cTrader cross-domain loader after Data migrates to the public registry.
* Singleton-only provider lifecycle and unverified Boolean-only connection status.

### V2 behaviours to add

* Canonical result/error/DTO and capability contracts.
* Explicit broker/profile registry and missing-dependency handling.
* Caller-owned immutable adapter sessions.
* Async-first provider operations with blocking SDK isolation.
* Genuine streaming and connection events where supported.
* Deterministic unsupported capability results.
* Environment mismatch protection and unknown mutation outcome.
* Shared fake adapter, contract tests, import-boundary tests, and credential-gated integration tests.
* Binance immutable product profiles.

### V2 proposals to reject or defer

* Separate general-purpose sync façade — defer until a consumer requires it.
* Strict exception façade — reject initially.
* Universal priority/weighted throttling queue — defer.
* Mandatory universal ten-state lifecycle — simplify.
* Runtime account switching — exclude initially.
* Speculative creation of every DTO and operation implementation — stage by accepted capability.
* Contract version fields on every nested object — simplify.
* Per-bar timezone evidence duplication — simplify.
* Mandatory OpenTelemetry and secure full-payload audit sink — defer to system observability.
* Universal `<100 µs` mapping gate — reject pending benchmarks.
* Always-on external sandbox suites in normal CI — modify to credential-gated pipelines.
* Binance Futures live mutation support — defer until verified.

### Required open decisions before README completion

* Identify the composition-root/secret boundary that supplies connection configs.
* Inventory direct native MT5 calls that must migrate into approved canonical capabilities.
* Decide Dukascopy production approval and alias semantics.
* Verify dynamic/external callers of legacy broker data/tool wrappers.
* Confirm safe cTrader request correlation mechanism.
* Define capability release evidence for live mutations.
* Decide Yahoo historical-bar production scope.

## 13. Final Reconciliation Checklist

* [x] Every V1 capability (`17/17`) received a disposition.
* [x] Every explicit V2 requirement ID (`130/130`) received a disposition.
* [x] Material unnumbered V2 requirements received synthetic disposition IDs (`10/10`).
* [x] Every V1 workflow (`7/7`) was reconciled.
* [x] Every proposed V2 cross-domain workflow was reconciled.
* [x] Confirmed working V1 behaviour was not discarded without reason.
* [x] Unused/questionable V1 behaviour was not preserved automatically.
* [x] V2 implementation complexity was not accepted automatically.
* [x] The direction follows the Package → Module folder → File → Public symbol model.
* [x] Potential cross-domain ownership conflicts are flagged for pipeline step 05.
* [x] Unresolved conflicts are listed under Open Decisions.
* [x] Cross-domain open decisions and shape-changing deferrals are marked for escalation.
* [x] No code was changed.
* [x] Neither source document was modified.
* [x] The document provides approved inputs for the final Brokers README.

# Agile Roadmap Traceability Matrix

> **Status:** Thirteen-phase delivery-plan allocation
> **Source baseline:** Authoritative repository specifications plus owner clarifications confirmed on 2026-07-16
> **Allocation rule:** Each current inventory ID appears exactly once. Provisional IDs identify unnumbered components; negative requirements preserve required absence tests.

Phase 1 includes both the deterministic simulation/backtest loop and actual MT5 demo-account place/reconcile/close through the production Brokers/Risk/Trading path. No fake adapter participates in that proof. The ledger-mandated FakeBrokerAdapter remains test-only production-assurance scope in Phase 12. Phase 13 is v2.0 parity.

| ID | Domain | Title | Tier | Size | Depends on | Phase | Source doc |
|---|---|---|---|---|---|---:|---|
| `P-SYS-001` | System | Stable public ports, contract versioning, and acyclic domain boundaries | T0 Skeleton | M | — | 1 | `docs/PROJECT.md` |
| `P-SYS-002` | System | Runtime profiles and execution-route compatibility | T0 Skeleton | M | `P-SYS-001` | 1 | `docs/PROJECT.md` |
| `SYS-NFR-001` | System | Architecture | T0 Skeleton | S | — | 1 | `docs/PROJECT.md` |
| `SYS-NFR-002` | System | Maintainability | T0 Skeleton | S | — | 1 | `docs/PROJECT.md` |
| `SYS-NFR-003` | System | Reliability | T0 Skeleton | S | — | 1 | `docs/PROJECT.md` |
| `SYS-NFR-004` | System | Security | T0 Skeleton | S | — | 1 | `docs/PROJECT.md` |
| `SYS-NFR-005` | System | Determinism | T0 Skeleton | S | — | 1 | `docs/PROJECT.md` |
| `SYS-NFR-006` | System | Observability | T0 Skeleton | S | — | 1 | `docs/PROJECT.md` |
| `SYS-WF-001` | System | Historical backtest | T0 Skeleton | M | `P-SYS-001` | 1 | `docs/PROJECT.md` |
| `SYS-WF-002` | System | Signal to live execution | T0 Skeleton | M | `SYS-WF-001`, `SYS-WF-005` | 1 | `docs/PROJECT.md` |
| `SYS-WF-005` | System | Operator monitoring and kill switch | T0 Skeleton | M | `P-SYS-001` | 1 | `docs/PROJECT.md` |
| `P-SYS-003` | System | Shared configuration and limits manifest | T1 Core | M | `P-SYS-001` | 2 | `docs/PROJECT.md` |
| `SYS-WF-003` | System | Parameter optimization and approved adoption | T2 Advanced | M | `SYS-WF-001` | 8 | `docs/PROJECT.md` |
| `SYS-WF-006` | System | Strategy operational eligibility | T2 Advanced | M | `SYS-WF-005` | 9 | `docs/PROJECT.md` |
| `SYS-WF-007` | System | Portfolio construction and activation | T2 Advanced | M | `SYS-WF-001`, `SYS-WF-006` | 9 | `docs/PROJECT.md` |
| `SYS-WF-008` | System | Governed portfolio rebalance | T2 Advanced | M | `SYS-WF-005`, `SYS-WF-007` | 9 | `docs/PROJECT.md` |
| `SYS-WF-004` | System | Research to strategy candidate | T2 Advanced | M | `SYS-WF-001` | 10 | `docs/PROJECT.md` |
| `P-SYS-004` | System | Portable modular-monolith deployment topology and startup | T1 Core | M | `P-SYS-001` | 11 | `docs/PROJECT.md` |
| `P-SYS-006` | System | Production assurance, release hardening, and quality-gate evidence (provisional) | T3 Complete | M | `P-SYS-004` | 12 | `docs/PROJECT.md` |
| `P-SYS-005` | System | Full-system usage, integration verification, and parity definition of done | T3 Complete | M | `P-SYS-001` | 13 | `docs/PROJECT.md` |
| `FR-UTL-001` | Utils | Define immutable AuthContext v1 with only USER and SERVICE_ACCOUNT principal types and complete trace context. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/utils/README.md` |
| `FR-UTL-002` | Utils | Define immutable redacted AuditEvent v1 with bounded JSON-safe payload. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/utils/README.md` |
| `FR-UTL-003` | Utils | Reject naive timestamps, empty identity/trace fields, unsupported principal types, and malformed schema identity. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/utils/README.md` |
| `FR-UTL-004` | Utils | Provide focused shared base exceptions without domain-specific policy. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/utils/README.md` |
| `FR-UTL-005` | Utils | Preserve deterministic code and sanitized detail while never returning a raw provider exception across a boundary. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/utils/README.md` |
| `FR-UTL-006` | Utils | Require domains to define their own codes and boundary mapping above the shared base hierarchy. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/utils/README.md` |
| `FR-UTL-007` | Utils | Generate prefixed UUID4 identifiers without embedded secrets. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/utils/README.md` |
| `FR-UTL-008` | Utils | Validate supported prefixes and canonical identifier syntax. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/utils/README.md` |
| `FR-UTL-009` | Utils | Derive deterministic SHA-256 identifiers from canonical, caller-supplied identity material. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/utils/README.md` |
| `FR-UTL-010` | Utils | Return aware UTC time from an injectable clock. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/utils/README.md` |
| `FR-UTL-011` | Utils | Parse and format UTC timestamps using canonical Z output. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/utils/README.md` |
| `FR-UTL-012` | Utils | Calculate non-negative age and explicit freshness against an injected instant. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/utils/README.md` |
| `FR-UTL-013` | Utils | Convert supported datetimes, decimals, enums, dataclasses, mappings, and sequences to deterministic JSON-safe values. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/utils/README.md` |
| `FR-UTL-014` | Utils | Produce stable UTF-8 JSON with sorted keys and no hidden redaction. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/utils/README.md` |
| `FR-UTL-015` | Utils | Reject unsupported, cyclic, non-finite, or unsafe values deterministically. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/utils/README.md` |
| `FR-UTL-021` | Utils | Reject policies that allow protected credential fields. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/utils/README.md` |
| `FR-UTL-022` | Utils | Define the immutable central settings base and generic runtime/logging settings, including the approved human-readable default logging profile. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/utils/README.md` |
| `FR-UTL-025` | Utils | Reserved / unused numbering gap — defines no behavior (excluded from ranges) | T0 Skeleton | S | `P-SYS-001` | 1 | `app/utils/README.md` |
| `FR-UTL-026` | Utils | Return stable child loggers without configuring handlers. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/utils/README.md` |
| `FR-UTL-027` | Utils | Atomically install deduplicated console and optional bounded rotating-file handlers from the approved default before the first runtime bound-log emission; ex... | T0 Skeleton | S | `P-SYS-001` | 1 | `app/utils/README.md` |
| `FR-UTL-028` | Utils | Redact messages and structured context before formatting. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/utils/README.md` |
| `FR-UTL-029` | Utils | Emit JSON or source-aware human-readable records with UTC time, padded level, module, function, line, message, and trace IDs. Human records use YYYY-MM-DD HH... | T0 Skeleton | S | `P-SYS-001` | 1 | `app/utils/README.md` |
| `FR-UTL-030` | Utils | Surface sink failure through a bounded secret-safe fallback. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/utils/README.md` |
| `FR-UTL-031` | Utils | Prevent duplicate handler or queue-listener installation across concurrent first use and repeated explicit configuration calls. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/utils/README.md` |
| `FR-UTL-032` | Utils | Keep import free of handler registration, environment reads, and filesystem writes. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/utils/README.md` |
| `FR-UTL-033` | Utils | Respect the shared LOG_LEVEL setting without redefining domain observability policy. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/utils/README.md` |
| `FR-UTL-034` | Utils | Normalize an error code and look up immutable safe metadata without a mutable registry. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/utils/README.md` |
| `FR-UTL-035` | Utils | Map an exception and synchronously deliver its safe payload to an explicitly injected sink. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/utils/README.md` |
| `FR-UTL-039` | Utils | Expose an import-safe global bound logger with standard levels, exception traceback capture, immutable context binding, and automatic approved-default activa... | T0 Skeleton | S | `P-SYS-001` | 1 | `app/utils/README.md` |
| `FR-UTL-040` | Utils | Route access-context records to access.log, exact DEBUG records to debug.log, and ERROR-or-higher records to errors.log. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/utils/README.md` |
| `FR-UTL-041` | Utils | Provide the approved lazy default profile: human-readable DEBUG stdout with ANSI color limited to level and message content, data/logs, 10 MB ZIP rotation, t... | T0 Skeleton | S | `P-SYS-001` | 1 | `app/utils/README.md` |
| `P-UTL-001` | Utils | contracts feature/component (provisional) | T0 Skeleton | M | `P-SYS-001` | 1 | `app/utils/README.md` |
| `P-UTL-002` | Utils | errors feature/component (provisional) | T0 Skeleton | M | `P-SYS-001` | 1 | `app/utils/README.md` |
| `P-UTL-003` | Utils | identity feature/component (provisional) | T0 Skeleton | M | `P-SYS-001` | 1 | `app/utils/README.md` |
| `P-UTL-004` | Utils | time feature/component (provisional) | T0 Skeleton | M | `P-SYS-001` | 1 | `app/utils/README.md` |
| `P-UTL-005` | Utils | serialization feature/component (provisional) | T0 Skeleton | M | `P-SYS-001` | 1 | `app/utils/README.md` |
| `P-UTL-008` | Utils | logging feature/component (provisional) | T0 Skeleton | M | `P-SYS-001` | 1 | `app/utils/README.md` |
| `WF-UTL-001` | Utils | Structured Logging and Redaction | T0 Skeleton | M | `P-SYS-001` | 1 | `app/utils/README.md` |
| `FR-UTL-016` | Utils | Define immutable denylist-first redaction policy with narrow reviewed field-path allowlists. | T1 Core | S | `P-SYS-001` | 2 | `app/utils/README.md` |
| `FR-UTL-017` | Utils | Detect sensitive keys case-insensitively. | T1 Core | S | `P-SYS-001` | 2 | `app/utils/README.md` |
| `FR-UTL-018` | Utils | Redact bounded text without mutating input. | T1 Core | S | `P-SYS-001` | 2 | `app/utils/README.md` |
| `FR-UTL-019` | Utils | Recursively redact a JSON-safe mapping without mutating input. | T1 Core | S | `P-SYS-001` | 2 | `app/utils/README.md` |
| `FR-UTL-020` | Utils | Return redacted paths and truncation diagnostics without secret values. | T1 Core | S | `P-SYS-001` | 2 | `app/utils/README.md` |
| `FR-UTL-023` | Utils | Load explicit values and centralized .env/process settings in documented precedence order only when called. | T1 Core | S | `P-SYS-001` | 2 | `app/utils/README.md` |
| `FR-UTL-024` | Utils | Reject unknown, incompatible, or unsafe deployment/runtime values without partial mutation. | T1 Core | S | `P-SYS-001` | 2 | `app/utils/README.md` |
| `NFR-UTL-001` | Utils | Boundary | T1 Core | S | `P-SYS-001` | 2 | `app/utils/README.md` |
| `NFR-UTL-002` | Utils | Security | T1 Core | S | `P-SYS-001` | 2 | `app/utils/README.md` |
| `NFR-UTL-003` | Utils | Import safety | T1 Core | S | `P-SYS-001` | 2 | `app/utils/README.md` |
| `NFR-UTL-004` | Utils | Determinism | T1 Core | S | `P-SYS-001` | 2 | `app/utils/README.md` |
| `NFR-UTL-005` | Utils | Maintainability | T1 Core | S | `P-SYS-001` | 2 | `app/utils/README.md` |
| `NFR-UTL-006` | Utils | Testing | T1 Core | S | `P-SYS-001` | 2 | `app/utils/README.md` |
| `NFR-UTL-007` | Utils | Persistence | T1 Core | S | `P-SYS-001` | 2 | `app/utils/README.md` |
| `P-UTL-006` | Utils | security feature/component (provisional) | T1 Core | M | `P-SYS-001` | 2 | `app/utils/README.md` |
| `P-UTL-007` | Utils | settings feature/component (provisional) | T1 Core | M | `P-SYS-001` | 2 | `app/utils/README.md` |
| `WF-UTL-002` | Utils | Shared Settings Bootstrap | T1 Core | M | `P-SYS-001` | 2 | `app/utils/README.md` |
| `WF-UTL-003` | Utils | Audit-Event Construction | T1 Core | M | `P-SYS-001` | 2 | `app/utils/README.md` |
| `CAP-BRK-001` | Brokers | Explicit registry/public API | T0 Skeleton | M | `P-SYS-001` | 1 | `app/services/brokers/README.md` |
| `CAP-BRK-003` | Brokers | Canonical results/errors/DTOs | T0 Skeleton | M | `P-SYS-001` | 1 | `app/services/brokers/README.md` |
| `CAP-BRK-012` | Brokers | MT5 adapter | T0 Skeleton | M | `P-SYS-001` | 1 | `app/services/brokers/README.md` |
| `FR-BRK-001` | Brokers | identify MT5, cTrader, Binance Spot, Binance USD-M Futures, Binance Coin-M Futures, Dukascopy, and Yahoo without aliases or implicit fallback. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/brokers/README.md` |
| `FR-BRK-002` | Brokers | require an explicit LIVE, DEMO, TESTNET, or SANDBOX environment and shall define no implicit live default. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/brokers/README.md` |
| `FR-BRK-003` | Brokers | expose the minimal validated lifecycle states DISCONNECTED, CONNECTING, READY, DEGRADED, CLOSING, and FAILED. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/brokers/README.md` |
| `FR-BRK-004` | Brokers | expose the stable accepted BROKER_* error taxonomy and shall add codes only with an accepted operation. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/brokers/README.md` |
| `FR-BRK-005` | Brokers | provide one identifier for every accepted canonical adapter operation so capability reports cannot omit unsupported entries. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/brokers/README.md` |
| `FR-BRK-006` | Brokers | carry immutable provider/profile, environment, composition-root-derived provider enablement, account reference, resolved in-memory credentia... | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/brokers/README.md` |
| `FR-BRK-007` | Brokers | represent code, message, retryability, redacted provider evidence, capability, and diagnostic details for an operational failure. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/brokers/README.md` |
| `FR-BRK-008` | Brokers | Every public operation shall return one versioned status/broker/operation/request/time/data/error/provider-metadata/latency envelope. Success has no error an... | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/brokers/README.md` |
| `FR-BRK-009` | Brokers | List and history operations shall return bounded records with provider cursor and explicit truncation metadata. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/brokers/README.md` |
| `FR-BRK-010` | Brokers | Each capability shall report implementation, availability, access, requirement, verification, evidence references, release approval, reason, and execution mo... | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/brokers/README.md` |
| `FR-BRK-011` | Brokers | return every catalogue entry for one provider/profile/account, including unsupported and untested operations, and shall keep every unapprove... | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/brokers/README.md` |
| `FR-BRK-012` | Brokers | distinguish transport, authentication, account authorization, trading permission, subscription readiness, environment, and lifecycle state. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/brokers/README.md` |
| `FR-BRK-013` | Brokers | Every lifecycle transition shall expose previous/new state, reason, UTC time, session generation, optional reconnect attempt, and resync requirement. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/brokers/README.md` |
| `FR-BRK-014` | Brokers | expose provider, API/terminal version, endpoint metadata, immutable profile, and environment without secrets. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/brokers/README.md` |
| `FR-BRK-015` | Brokers | expose only permissions reported for the authenticated provider session. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/brokers/README.md` |
| `FR-BRK-016` | Brokers | preserve provider account identity, currency, balances, equity, margin, status, and provider/retrieval timestamps without certifying freshness. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/brokers/README.md` |
| `FR-BRK-017` | Brokers | represent provider-reported asset/currency balance values with exact decimals and explicit units. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/brokers/README.md` |
| `FR-BRK-018` | Brokers | represent provider asset/currency metadata without canonical identity policy or currency conversion. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/brokers/README.md` |
| `FR-BRK-019` | Brokers | preserve the exact provider-native symbol identifier, specifications, sessions, units, and trading flags without canonical identity, friendl... | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/brokers/README.md` |
| `FR-BRK-020` | Brokers | represent provider-reported open, closed, halted, or unknown market state. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/brokers/README.md` |
| `FR-BRK-021` | Brokers | represent provider-supplied trading windows as timezone-aware UTC intervals with native metadata retained. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/brokers/README.md` |
| `FR-BRK-022` | Brokers | expose only genuine bid/ask/last values with exact decimals, nullable missing fields, explicit units, and provider/retrieval times. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/brokers/README.md` |
| `FR-BRK-023` | Brokers | preserve provider sequence, event/receipt time, nullable bid/ask/last and quantities, and tick type without invented sequence evidence. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/brokers/README.md` |
| `FR-BRK-024` | Brokers | preserve UTC open/close time, closed state, trade/tick volume distinctions, and native/requested timeframe while storing conversion evidence... | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/brokers/README.md` |
| `FR-BRK-025` | Brokers | represent order-book snapshot/delta state, levels, provider sequence/checksum, depth truncation, and resnapshot requirement without invented... | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/brokers/README.md` |
| `FR-BRK-026` | Brokers | represent immutable metadata for one adapter-scoped bounded subscription, including capability, exact provider-native symbols, creation time... | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/brokers/README.md` |
| `FR-BRK-027` | Brokers | preserve provider position ID, symbol, side, exact quantities/prices/P&L fields, partial state, and timestamps. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/brokers/README.md` |
| `FR-BRK-028` | Brokers | express structural order filters only, without selection policy or unbounded history. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/brokers/README.md` |
| `FR-BRK-029` | Brokers | express structural position filters only. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/brokers/README.md` |
| `FR-BRK-030` | Brokers | preserve provider order IDs, caller IDs, product-applicable fields, exact quantity/unit, partial state, prices, and timestamps without fabri... | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/brokers/README.md` |
| `FR-BRK-031` | Brokers | preserve provider deal/fill ID, order reference, exact quantity/price/fee, partial state, and timestamps. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/brokers/README.md` |
| `FR-BRK-032` | Brokers | represent provider-reported deposits, withdrawals, fees, swaps, and account transactions with exact values and units. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/brokers/README.md` |
| `FR-BRK-033` | Brokers | require one complete V1 order request with the exact side, order type, positive finite quantity/unit, applicable finite prices, approved tim... | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/brokers/README.md` |
| `FR-BRK-034` | Brokers | identify exactly one provider order and only caller-supplied modifications. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/brokers/README.md` |
| `FR-BRK-035` | Brokers | distinguish provider validation/preview from final order acceptance. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/brokers/README.md` |
| `FR-BRK-036` | Brokers | represent explicit provider acknowledgement, rejection, unknown outcome, partial fill, and provider identifiers without synthetic success. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/brokers/README.md` |
| `FR-BRK-037` | Brokers | identify one position and only provider-supported caller-supplied stop/take-profit modifications. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/brokers/README.md` |
| `FR-BRK-038` | Brokers | identify one position and exact caller-supplied close/reduce quantity and unit. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/brokers/README.md` |
| `FR-BRK-039` | Brokers | carry only fields required for a provider-native margin request. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/brokers/README.md` |
| `FR-BRK-040` | Brokers | carry only fields required for a provider-native profit request, including explicit open/close prices and units. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/brokers/README.md` |
| `FR-BRK-041` | Brokers | represent a provider-native fee/commission estimate with exact value, currency/unit, and provider evidence. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/brokers/README.md` |
| `FR-BRK-042` | Brokers | expose provider time, local send/receive UTC times, estimated offset, and round-trip latency without silently correcting business timestamps. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/brokers/README.md` |
| `FR-BRK-043` | Brokers | define the genuine market-data and subscription read surface independently of execution capabilities. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/brokers/README.md` |
| `FR-BRK-044` | Brokers | define account/platform/state reads independently of mutation capabilities. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/brokers/README.md` |
| `FR-BRK-045` | Brokers | define only single-target provider mutation primitives. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/brokers/README.md` |
| `FR-BRK-046` | Brokers | define provider-native calculation requests without local fallback formulas. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/brokers/README.md` |
| `FR-BRK-047` | Brokers | compose lifecycle and focused capabilities into one async adapter, expose read-only contract_version="v1" and schema_id="brokers.adapter.v1"... | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/brokers/README.md` |
| `FR-BRK-048` | Brokers | explicitly establish and verify the configured transport, authentication, account, and environment before returning success. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/brokers/README.md` |
| `FR-BRK-049` | Brokers | idempotently close every session, task, terminal handle, reactor, and subscription owned by the adapter. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/brokers/README.md` |
| `FR-BRK-050` | Brokers | recover only the same transport/session up to the configured bound and shall never replay interrupted reads or mutations. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/brokers/README.md` |
| `FR-BRK-051` | Brokers | return verified current connectivity rather than a caller-local Boolean flag. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/brokers/README.md` |
| `FR-BRK-052` | Brokers | return detailed lifecycle, authentication, account, permission, subscription, environment, and maintenance state. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/brokers/README.md` |
| `FR-BRK-053` | Brokers | perform only a provider-supported liveness probe and return unsupported otherwise. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/brokers/README.md` |
| `FR-BRK-054` | Brokers | use only provider-supported token/session refresh and shall fail the session closed when refresh fails. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/brokers/README.md` |
| `FR-BRK-055` | Brokers | return provider time and local clock/latency evidence when available, otherwise unsupported. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/brokers/README.md` |
| `FR-BRK-056` | Brokers | expose the adapter instance's latest redacted diagnostic error as non-authoritative state. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/brokers/README.md` |
| `FR-BRK-057` | Brokers | yield one canonical event per validated lifecycle transition through a bounded async iterator. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/brokers/README.md` |
| `FR-BRK-058` | Brokers | return a bounded page of exact provider-native symbols only. query, when supported, is transmitted or matched only against provider-native s... | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/brokers/README.md` |
| `FR-BRK-059` | Brokers | return direct provider specifications and trading flags for one symbol without canonical identity policy. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/brokers/README.md` |
| `FR-BRK-060` | Brokers | perform only a provider watch-list selection and return unsupported when unavailable. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/brokers/README.md` |
| `FR-BRK-061` | Brokers | return provider-reported market state without deriving calendars. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/brokers/README.md` |
| `FR-BRK-062` | Brokers | return provider-supplied trading windows within optional bounds without generating sessions. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/brokers/README.md` |
| `FR-BRK-063` | Brokers | return the latest genuine provider quote and shall return unsupported or invalid-response instead of fallback prices. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/brokers/README.md` |
| `FR-BRK-064` | Brokers | return bounded genuine provider ticks with explicit sequence/provenance or unsupported when genuine ticks do not exist. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/brokers/README.md` |
| `FR-BRK-065` | Brokers | return bounded provider bars using structural timeframe translation only, with no resampling or hidden default timeframe. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/brokers/README.md` |
| `FR-BRK-066` | Brokers | return provider order-book truth with explicit depth/sequence/resnapshot evidence or deterministic unsupported. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/brokers/README.md` |
| `FR-BRK-067` | Brokers | return a provider-reported spread only and shall never insert fixed or zero placeholder spread. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/brokers/README.md` |
| `FR-BRK-068` | Brokers | create one adapter-scoped bounded genuine quote stream and return its typed subscription handle. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/brokers/README.md` |
| `FR-BRK-069` | Brokers | create a provider bar stream only where genuine provider events are supported. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/brokers/README.md` |
| `FR-BRK-070` | Brokers | create a provider order-book stream only where sequence-safe events are supported. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/brokers/README.md` |
| `FR-BRK-071` | Brokers | terminate exactly one owned subscription and report an unknown ID without affecting any other stream. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/brokers/README.md` |
| `FR-BRK-072` | Brokers | list immutable metadata only for subscriptions owned by the current adapter instance. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/brokers/README.md` |
| `FR-BRK-073` | Brokers | return the complete refreshed capability report for the connected profile/account, with untested or unapproved mutations unavailable regardl... | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/brokers/README.md` |
| `FR-BRK-074` | Brokers | answer one capability from the complete report without probing a missing SDK attribute. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/brokers/README.md` |
| `FR-BRK-075` | Brokers | return direct provider platform/version/endpoint/environment metadata without secrets. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/brokers/README.md` |
| `FR-BRK-076` | Brokers | return provider-reported current permissions and shall not infer trade access from SDK method presence. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/brokers/README.md` |
| `FR-BRK-077` | Brokers | return a bounded page of provider-visible accounts where supported. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/brokers/README.md` |
| `FR-BRK-078` | Brokers | The initial system shall reject in-place account switching as unsupported; callers create a new immutable adapter instance. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/brokers/README.md` |
| `FR-BRK-079` | Brokers | return direct provider account identity and financial state without persisting or certifying freshness. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/brokers/README.md` |
| `FR-BRK-080` | Brokers | return exact provider-reported balances without currency conversion. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/brokers/README.md` |
| `FR-BRK-081` | Brokers | return provider-known account/assets without constructing a canonical asset universe. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/brokers/README.md` |
| `FR-BRK-082` | Brokers | return direct provider metadata for one asset or an exact not-found result. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/brokers/README.md` |
| `FR-BRK-083` | Brokers | return a bounded canonical page of current positions matching structural filters. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/brokers/README.md` |
| `FR-BRK-084` | Brokers | return one provider position or BROKER_POSITION_NOT_FOUND. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/brokers/README.md` |
| `FR-BRK-085` | Brokers | return a bounded page of provider orders matching structural filters. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/brokers/README.md` |
| `FR-BRK-086` | Brokers | return one provider order or BROKER_ORDER_NOT_FOUND. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/brokers/README.md` |
| `FR-BRK-087` | Brokers | return bounded provider order history with explicit page limits/cursors. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/brokers/README.md` |
| `FR-BRK-088` | Brokers | return bounded provider deal/fill history preserving exact provider IDs and partial state. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/brokers/README.md` |
| `FR-BRK-089` | Brokers | return one provider deal/fill or BROKER_DEAL_NOT_FOUND. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/brokers/README.md` |
| `FR-BRK-090` | Brokers | return bounded direct provider account transactions where supported and deterministic unsupported otherwise. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/brokers/README.md` |
| `FR-BRK-091` | Brokers | request provider validation/preview for one order and shall not present the result as acceptance. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/brokers/README.md` |
| `FR-BRK-092` | Brokers | submit exactly one complete caller-defined order and report success only on explicit provider acknowledgement. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/brokers/README.md` |
| `FR-BRK-093` | Brokers | modify exactly one order using only supplied fields. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/brokers/README.md` |
| `FR-BRK-094` | Brokers | cancel exactly one provider order and transmit the caller request ID where supported. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/brokers/README.md` |
| `FR-BRK-095` | Brokers | modify provider-supported fields on exactly one position. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/brokers/README.md` |
| `FR-BRK-096` | Brokers | close or reduce exactly one position and preserve partial-close acknowledgement. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/brokers/README.md` |
| `FR-BRK-097` | Brokers | request one provider-atomic replacement only where verified; it shall not emulate cancel-then-place. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/brokers/README.md` |
| `FR-BRK-098` | Brokers | return a provider-native margin estimate or unsupported, never a local risk formula. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/brokers/README.md` |
| `FR-BRK-099` | Brokers | return a provider-native profit estimate or unsupported, never a locally approximated value. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/brokers/README.md` |
| `FR-BRK-100` | Brokers | return a provider-native commission/fee estimate or deterministic unsupported. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/brokers/README.md` |
| `FR-BRK-101` | Brokers | require an exact provider/profile ID and matching immutable config, reject provider_enabled=False before provider import, lazily import only... | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/brokers/README.md` |
| `FR-BRK-102` | Brokers | list every canonical registered provider/profile, including profiles whose optional SDK is absent, without importing provider SDKs. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/brokers/README.md` |
| `FR-BRK-103` | Brokers | generate one complete capability catalogue covering every protocol operation and registered profile from the static declaration table in reg... | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/brokers/README.md` |
| `FR-BRK-104` | Brokers | expose all accepted MT5 lifecycle, genuine market-data, account/order/position/deal reads, supported provider calculations, and single mutat... | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/brokers/README.md` |
| `FR-BRK-105` | Brokers | expose verified cTrader lifecycle, genuine reads/streams, account and execution state, supported provider calculations, and single mutations... | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/brokers/README.md` |
| `FR-BRK-110` | Brokers | contracts/unsupported.py | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/brokers/README.md` |
| `FR-BRK-111` | Brokers | Each adapter shall own one transport circuit with CLOSED, OPEN, and HALF_OPEN states. BROKER_CONNECTION_FAILED, BROKER_CONNECTION_LOST, BROKER_TIMEOUT, BROKE... | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/brokers/README.md` |
| `FR-BRK-112` | Brokers | expose each provider-event subscription as a typed bounded FIFO asynchronous stream with immutable metadata and explicit unsubscribe; termin... | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/brokers/README.md` |
| `FR-BRK-113` | Brokers | contracts/__init__.py | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/brokers/README.md` |
| `FR-BRK-114` | Brokers | The runtime subscription shall implement FR-BRK-112 with one bounded queue per handle, FIFO delivery, explicit terminal errors, deterministic unsubscribe, an... | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/brokers/README.md` |
| `FR-BRK-116` | Brokers | mt5/transport.py | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/brokers/README.md` |
| `FR-BRK-117` | Brokers | mt5/mapping.py | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/brokers/README.md` |
| `FR-BRK-118` | Brokers | mt5/__init__.py | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/brokers/README.md` |
| `FR-BRK-133` | Brokers | registry/__init__.py | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/brokers/README.md` |
| `P-BRK-001` | Brokers | contracts feature/component (provisional) | T0 Skeleton | M | `P-SYS-001` | 1 | `app/services/brokers/README.md` |
| `P-BRK-003` | Brokers | registry feature/component (provisional) | T0 Skeleton | M | `P-SYS-001` | 1 | `app/services/brokers/README.md` |
| `P-BRK-004` | Brokers | mt5 feature/component (provisional) | T0 Skeleton | M | `P-SYS-001` | 1 | `app/services/brokers/README.md` |
| `WF-BRK-001` | Brokers | Resolve Explicit Adapter | T0 Skeleton | M | `P-SYS-001` | 1 | `app/services/brokers/README.md` |
| `WF-BRK-002` | Brokers | Connect and Authenticate Provider Session | T0 Skeleton | M | `P-SYS-001` | 1 | `app/services/brokers/README.md` |
| `WF-BRK-003` | Brokers | Acquire Provider Market Data | T0 Skeleton | M | `P-SYS-001` | 1 | `app/services/brokers/README.md` |
| `WF-BRK-008` | Brokers | Handle Unsupported Operation | T0 Skeleton | M | `P-SYS-001` | 1 | `app/services/brokers/README.md` |
| `WF-BRK-009` | Brokers | Inject Canonical Broker into Execution | T0 Skeleton | M | `P-SYS-001` | 1 | `app/services/brokers/README.md` |
| `CAP-BRK-005` | Brokers | Symbols/metadata | T1 Core | M | `P-SYS-001` | 2 | `app/services/brokers/README.md` |
| `CAP-BRK-016` | Brokers | Yahoo historical bars | T1 Core | M | `P-SYS-001` | 2 | `app/services/brokers/README.md` |
| `FR-BRK-108` | Brokers | expose genuine bounded Yahoo historical bars for research/development use, report production/live availability as unavailable, attach explic... | T1 Core | S | `P-SYS-001` | 2 | `app/services/brokers/README.md` |
| `FR-BRK-130` | Brokers | yahoo/transport.py | T1 Core | S | `P-SYS-001` | 2 | `app/services/brokers/README.md` |
| `FR-BRK-131` | Brokers | yahoo/mapping.py | T1 Core | S | `P-SYS-001` | 2 | `app/services/brokers/README.md` |
| `FR-BRK-132` | Brokers | yahoo/__init__.py | T1 Core | S | `P-SYS-001` | 2 | `app/services/brokers/README.md` |
| `P-BRK-008` | Brokers | yahoo feature/component (provisional) | T1 Core | M | `P-SYS-001` | 2 | `app/services/brokers/README.md` |
| `CAP-BRK-013` | Brokers | cTrader adapter | T1 Core | M | `P-SYS-001` | 5 | `app/services/brokers/README.md` |
| `CAP-BRK-014` | Brokers | Binance profiles | T1 Core | M | `P-SYS-001` | 5 | `app/services/brokers/README.md` |
| `FR-BRK-106` | Brokers | expose genuine Binance Spot market data through the canonical adapter, keep the selected product profile immutable, and keep every Futures/a... | T1 Core | S | `P-SYS-001` | 5 | `app/services/brokers/README.md` |
| `FR-BRK-115` | Brokers | The runtime package initializer shall expose no public symbol and cause no provider import or state mutation. | T1 Core | S | `P-SYS-001` | 5 | `app/services/brokers/README.md` |
| `FR-BRK-119` | Brokers | ctrader/transport.py | T1 Core | S | `P-SYS-001` | 5 | `app/services/brokers/README.md` |
| `FR-BRK-120` | Brokers | ctrader/mapping.py | T1 Core | S | `P-SYS-001` | 5 | `app/services/brokers/README.md` |
| `FR-BRK-121` | Brokers | ctrader/__init__.py | T1 Core | S | `P-SYS-001` | 5 | `app/services/brokers/README.md` |
| `FR-BRK-122` | Brokers | binance/profiles.py | T1 Core | S | `P-SYS-001` | 5 | `app/services/brokers/README.md` |
| `FR-BRK-123` | Brokers | binance/transport.py | T1 Core | S | `P-SYS-001` | 5 | `app/services/brokers/README.md` |
| `FR-BRK-124` | Brokers | binance/mapping.py | T1 Core | S | `P-SYS-001` | 5 | `app/services/brokers/README.md` |
| `FR-BRK-125` | Brokers | binance/__init__.py | T1 Core | S | `P-SYS-001` | 5 | `app/services/brokers/README.md` |
| `P-BRK-002` | Brokers | runtime feature/component (provisional) | T1 Core | M | `P-SYS-001` | 5 | `app/services/brokers/README.md` |
| `P-BRK-005` | Brokers | ctrader feature/component (provisional) | T1 Core | M | `P-SYS-001` | 5 | `app/services/brokers/README.md` |
| `P-BRK-006` | Brokers | binance feature/component (provisional) | T1 Core | M | `P-SYS-001` | 5 | `app/services/brokers/README.md` |
| `WF-BRK-004` | Brokers | Submit One Broker Mutation | T1 Core | M | `P-SYS-001` | 5 | `app/services/brokers/README.md` |
| `WF-BRK-005` | Brokers | Read Account and Execution State | T1 Core | M | `P-SYS-001` | 5 | `app/services/brokers/README.md` |
| `WF-BRK-007` | Brokers | Correlate cTrader Response | T1 Core | M | `P-SYS-001` | 5 | `app/services/brokers/README.md` |
| `CAP-BRK-007` | Brokers | Streaming | T1 Core | M | `P-SYS-001` | 11 | `app/services/brokers/README.md` |
| `CAP-BRK-015` | Brokers | Dukascopy read-only adapter | T1 Core | M | `P-SYS-001` | 11 | `app/services/brokers/README.md` |
| `FR-BRK-107` | Brokers | expose only genuine bounded Dukascopy ticks for research/development use, advertise exact provider-native symbols only, report production/li... | T1 Core | S | `P-SYS-001` | 11 | `app/services/brokers/README.md` |
| `FR-BRK-126` | Brokers | dukascopy/instruments.py | T1 Core | S | `P-SYS-001` | 11 | `app/services/brokers/README.md` |
| `FR-BRK-127` | Brokers | dukascopy/transport.py | T1 Core | S | `P-SYS-001` | 11 | `app/services/brokers/README.md` |
| `FR-BRK-128` | Brokers | dukascopy/mapping.py | T1 Core | S | `P-SYS-001` | 11 | `app/services/brokers/README.md` |
| `FR-BRK-129` | Brokers | dukascopy/__init__.py | T1 Core | S | `P-SYS-001` | 11 | `app/services/brokers/README.md` |
| `P-BRK-007` | Brokers | dukascopy feature/component (provisional) | T1 Core | M | `P-SYS-001` | 11 | `app/services/brokers/README.md` |
| `WF-BRK-006` | Brokers | Stream Provider and Connection Events | T1 Core | M | `P-SYS-001` | 11 | `app/services/brokers/README.md` |
| `CAP-BRK-019` | Brokers | Contract/boundary/fake tests | T3 Complete | M | `P-SYS-001` | 12 | `app/services/brokers/README.md` |
| `FR-BRK-109` | Brokers | provide a complete deterministic BrokerAdapter test double whose operations return canonical DTOs, support bounded streams, preserve isolati... | T3 Complete | S | `P-SYS-001` | 12 | `app/services/brokers/README.md` |
| `FR-BRK-134` | Brokers | testing/__init__.py | T3 Complete | S | `P-SYS-001` | 12 | `app/services/brokers/README.md` |
| `NFR-BRK-001` | Brokers | Architecture | T3 Complete | S | `P-SYS-001` | 12 | `app/services/brokers/README.md` |
| `NFR-BRK-002` | Brokers | Provider truth | T3 Complete | S | `P-SYS-001` | 12 | `app/services/brokers/README.md` |
| `NFR-BRK-003` | Brokers | API boundary | T3 Complete | S | `P-SYS-001` | 12 | `app/services/brokers/README.md` |
| `NFR-BRK-004` | Brokers | Reliability | T3 Complete | S | `P-SYS-001` | 12 | `app/services/brokers/README.md` |
| `NFR-BRK-005` | Brokers | Concurrency | T3 Complete | S | `P-SYS-001` | 12 | `app/services/brokers/README.md` |
| `NFR-BRK-006` | Brokers | Async safety | T3 Complete | S | `P-SYS-001` | 12 | `app/services/brokers/README.md` |
| `NFR-BRK-007` | Brokers | Security | T3 Complete | S | `P-SYS-001` | 12 | `app/services/brokers/README.md` |
| `NFR-BRK-008` | Brokers | Observability | T3 Complete | S | `P-SYS-001` | 12 | `app/services/brokers/README.md` |
| `NFR-BRK-009` | Brokers | Determinism | T3 Complete | S | `P-SYS-001` | 12 | `app/services/brokers/README.md` |
| `NFR-BRK-010` | Brokers | Performance | T3 Complete | S | `P-SYS-001` | 12 | `app/services/brokers/README.md` |
| `NFR-BRK-011` | Brokers | Independence | T3 Complete | S | `P-SYS-001` | 12 | `app/services/brokers/README.md` |
| `NFR-BRK-012` | Brokers | Testing | T3 Complete | S | `P-SYS-001` | 12 | `app/services/brokers/README.md` |
| `NFR-BRK-013` | Brokers | Dependencies | T3 Complete | S | `P-SYS-001` | 12 | `app/services/brokers/README.md` |
| `NFR-BRK-014` | Brokers | Persistence | T3 Complete | S | `P-SYS-001` | 12 | `app/services/brokers/README.md` |
| `NFR-BRK-015` | Brokers | Provider scope | T3 Complete | S | `P-SYS-001` | 12 | `app/services/brokers/README.md` |
| `P-BRK-009` | Brokers | testing feature/component (provisional) | T3 Complete | M | `P-SYS-001` | 12 | `app/services/brokers/README.md` |
| `CAP-BRK-002` | Brokers | Session lifecycle | T3 Complete | M | `P-SYS-001` | 13 | `app/services/brokers/README.md` |
| `CAP-BRK-004` | Brokers | Capabilities/unsupported outcomes | T3 Complete | M | `P-SYS-001` | 13 | `app/services/brokers/README.md` |
| `CAP-BRK-006` | Brokers | Quotes/ticks/bars/order books | T3 Complete | M | `P-SYS-001` | 13 | `app/services/brokers/README.md` |
| `CAP-BRK-008` | Brokers | Account/platform/permissions | T3 Complete | M | `P-SYS-001` | 13 | `app/services/brokers/README.md` |
| `CAP-BRK-009` | Brokers | Positions/orders/deals/activity | T3 Complete | M | `P-SYS-001` | 13 | `app/services/brokers/README.md` |
| `CAP-BRK-010` | Brokers | Single-target mutations | T3 Complete | M | `P-SYS-001` | 13 | `app/services/brokers/README.md` |
| `CAP-BRK-011` | Brokers | Provider-native calculations | T3 Complete | M | `P-SYS-001` | 13 | `app/services/brokers/README.md` |
| `CAP-BRK-017` | Brokers | Session/account isolation | T3 Complete | M | `P-SYS-001` | 13 | `app/services/brokers/README.md` |
| `CAP-BRK-018` | Brokers | Redacted observability | T3 Complete | M | `P-SYS-001` | 13 | `app/services/brokers/README.md` |
| `FR-BRK-135` | Brokers | brokers/__init__.py | T3 Complete | S | `P-SYS-001` | 13 | `app/services/brokers/README.md` |
| `CAP-DATA-003` | Data | Source protocol/registry/readiness/adapters | T0 Skeleton | M | `P-SYS-001` | 1 | `app/services/data/README.md` |
| `CAP-DATA-004` | Data | Canonical records/UTC/versioning | T0 Skeleton | M | `P-SYS-001` | 1 | `app/services/data/README.md` |
| `FR-DATA-001` | Data | Validate UTC OHLCV with finite exact numerics, low open/close high, non-negative volume, provenance, and available_at. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/data/README.md` |
| `FR-DATA-002` | Data | Validate UTC ticks with finite bid/ask/last, ask bid when both exist, volume metadata, provenance, and available_at. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/data/README.md` |
| `FR-DATA-003` | Data | Validate spread records with declared unit/scale, non-negative exact spread, UTC timestamp, provenance, and available_at. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/data/README.md` |
| `FR-DATA-004` | Data | Represent bounded quality evidence with status, score, issues, warnings, counts, truncation, schema version, UTC generation time, and governed blocking behav... | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/data/README.md` |
| `FR-DATA-005` | Data | Expose immutable normalized records with availability, quality, provenance, license, cache, workflow, schema, normalization, and precision metadata. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/data/README.md` |
| `FR-DATA-006` | Data | Validate one typed internal request containing source, symbol, kind, optional timeframe/range/limit, cache/quality policies, UTC/IANA inputs, workflow, preci... | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/data/README.md` |
| `FR-DATA-007` | Data | Represent indexed ranges, gaps, overlap/completeness evidence, record count, source revision/readiness, and provenance without materializing the full dataset. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/data/README.md` |
| `FR-DATA-008` | Data | Expose immutable normalized account, balance, margin, position, order, connectivity, and staleness evidence with exact decimals and UTC snapshot time. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/data/README.md` |
| `FR-DATA-010` | Data | Declare source readiness, capabilities, credential/network/write requirements, schema/timezone/version metadata, promotion criteria, and sign-off evidence. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/data/README.md` |
| `FR-DATA-011` | Data | Declare permitted workflow contexts, export/retention/attribution restrictions, enforcement behavior, and license status for each source. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/data/README.md` |
| `FR-DATA-012` | Data | Expose one redacted domain exception carrying a manifest code, safe details, retryability, severity, request ID, and operator action without raw exceptions. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/data/README.md` |
| `FR-DATA-013` | Data | Expose one immutable manifest for active deterministic codes and reserve UNKNOWN_ERROR for failures not otherwise mapped. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/data/README.md` |
| `FR-DATA-016` | Data | Grant at most one writer lease per resolved path, reject conflicts deterministically, and release it on exit or verified stale recovery. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/data/README.md` |
| `FR-DATA-023` | Data | Require bounded, deterministically ordered symbol discovery with cursor pagination and declared discovery capability. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/data/README.md` |
| `FR-DATA-026` | Data | Validate requested and explicit fallback sources in order against capability, readiness, license, context, timeout/rate, and breaker state and record every a... | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/data/README.md` |
| `FR-DATA-028` | Data | Return a fresh normalized AccountStateSnapshot v1 from read-only Brokers BrokerAdapter account reads without exposing credentials/provider objects. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/data/README.md` |
| `FR-DATA-030` | Data | Execute bounded bars/ticks/spreads retrieval through explicit source policy, versioned cache, normalization, quality, and precision, returning MarketDataset. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/data/README.md` |
| `FR-DATA-031` | Data | Return a bounded deterministic symbol page with cursor, source readiness, and provenance. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/data/README.md` |
| `FR-DATA-032` | Data | Return normalized asset-aware metadata and explicitly mark unknown optional fields without provider-derived optimistic defaults. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/data/README.md` |
| `FR-DATA-033` | Data | Compute ranges, gaps, overlaps, completeness, count, revision, and readiness from manifests/indexes and bounded probing, never hard-code certainty. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/data/README.md` |
| `FR-DATA-034` | Data | Return current configured hours and normalized UTC sessions, advance cross-midnight windows correctly, and reject historical reconstruction. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/data/README.md` |
| `FR-DATA-035` | Data | Return bounded source-native or derived volume as records, buckets, or summary with explicit volume kind/unit and provenance. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/data/README.md` |
| `FR-DATA-036` | Data | Resample ordered canonical OHLCV only to a supported higher timeframe using deterministic OHLCV/spread aggregation and updated available_at. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/data/README.md` |
| `FR-DATA-039` | Data | Generate bounded canonical bars or ticks with GBM, exact parameters, and deterministic output when a seed is supplied; generation is not a source adapter. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/data/README.md` |
| `FR-DATA-041` | Data | Derive the stable SHA-256 idempotency key from source, symbol, kind, timeframe, start/end, schema version, and normalization version. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/data/README.md` |
| `FR-DATA-046` | Data | Start one internal feed only for a declared live-capable staging/production source, persist initial state, and expose no public subscription handle. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/data/README.md` |
| `FR-DATA-075` | Data | Validate a bounded request for session, calendar, spread, liquidity, volatility, correlation, and crisis evidence for one declared scope. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/data/README.md` |
| `FR-DATA-076` | Data | Produce immutable MarketContextEvidence v1 with separate contract version/schema ID, UTC freshness, provenance, and explicit missingness; never produce a Ris... | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/data/README.md` |
| `FR-DATA-078` | Data | Validate source/target currencies, UTC as_of, explicit maximum age, and explicit allowed-path policy; reject same-leg cycles and unbounded discovery. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/data/README.md` |
| `FR-DATA-079` | Data | Deterministically select an allowed acyclic direct/synthesized path and publish exact rates, UTC freshness, policy version, and source provenance as FXConver... | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/data/README.md` |
| `P-DATA-001` | Data | contracts feature/component (provisional) | T0 Skeleton | M | `P-SYS-001` | 1 | `app/services/data/README.md` |
| `P-DATA-004` | Data | access feature/component (provisional) | T0 Skeleton | M | `P-SYS-001` | 1 | `app/services/data/README.md` |
| `P-DATA-008` | Data | public_api feature/component (provisional) | T0 Skeleton | M | `P-SYS-001` | 1 | `app/services/data/README.md` |
| `WF-DATA-001` | Data | Historical Bars, Ticks, and Spreads | T0 Skeleton | M | `P-SYS-001` | 1 | `app/services/data/README.md` |
| `WF-DATA-013` | Data | Account Snapshot Service | T0 Skeleton | M | `P-SYS-001` | 1 | `app/services/data/README.md` |
| `WF-DATA-014` | Data | Risk Market-Context Evidence | T0 Skeleton | M | `P-SYS-001` | 1 | `app/services/data/README.md` |
| `CAP-DATA-007` | Data | Local CSV/Parquet and atomic storage | T1 Core | M | `P-SYS-001` | 2 | `app/services/data/README.md` |
| `CAP-DATA-015` | Data | License/fallback/rate/breaker/source safety | T1 Core | M | `P-SYS-001` | 2 | `app/services/data/README.md` |
| `CAP-DATA-016` | Data | Symbol discovery and metadata | T1 Core | M | `P-SYS-001` | 2 | `app/services/data/README.md` |
| `FR-DATA-014` | Data | Execute a bounded caller-owned statement plan in one short-lived SQLite transaction, return normalized results without a connection/session, and roll back at... | T1 Core | S | `P-SYS-001` | 2 | `app/services/data/README.md` |
| `FR-DATA-015` | Data | Validate ownership/order/checksums, acquire the shared lock, and execute domain-owned migration definitions exactly once while preserving an immutable ledger. | T1 Core | S | `P-SYS-001` | 2 | `app/services/data/README.md` |
| `FR-DATA-017` | Data | Load CSV/Parquet plus manifest only from an approved root, verify hash/schema/normalization metadata, normalize records, and reject corruption without hidden... | T1 Core | S | `P-SYS-001` | 2 | `app/services/data/README.md` |
| `FR-DATA-018` | Data | Validate license/quality/path, lock the target, write artifact and manifest through a temporary file, and atomically commit or quarantine failure. | T1 Core | S | `P-SYS-001` | 2 | `app/services/data/README.md` |
| `FR-DATA-019` | Data | Return a cache entry only when request dimensions, schema/normalization, source revision/raw hash, and stale policy match; stale data is never silent. | T1 Core | S | `P-SYS-001` | 2 | `app/services/data/README.md` |
| `FR-DATA-020` | Data | Write a bounded cache entry with complete identity/TTL metadata and surface an optional cache-write failure without corrupting a successful retrieval result. | T1 Core | S | `P-SYS-001` | 2 | `app/services/data/README.md` |
| `FR-DATA-021` | Data | Persist a redacted AuditEvent v1 idempotently with trace identifiers and surface every persistence failure. | T1 Core | S | `P-SYS-001` | 2 | `app/services/data/README.md` |
| `FR-DATA-022` | Data | Require every adapter to perform one bounded read and return provider-neutral raw records plus source metadata without broker mutation. | T1 Core | S | `P-SYS-001` | 2 | `app/services/data/README.md` |
| `FR-DATA-024` | Data | Require normalized symbol metadata with provenance and explicit missing fields rather than optimistic defaults. | T1 Core | S | `P-SYS-001` | 2 | `app/services/data/README.md` |
| `FR-DATA-025` | Data | Register a source descriptor and lazy factory atomically, reject duplicate/conflicting declarations, and perform no I/O during registration/import. | T1 Core | S | `P-SYS-001` | 2 | `app/services/data/README.md` |
| `FR-DATA-027` | Data | Change readiness only from a complete authenticated evidence package, record an audit event, and permit immediate reversible demotion. | T1 Core | S | `P-SYS-001` | 2 | `app/services/data/README.md` |
| `FR-DATA-037` | Data | Backward-align multiple datasets using only values available by each target timestamp, preserving source availability metadata and failing atomically on look... | T1 Core | S | `P-SYS-001` | 2 | `app/services/data/README.md` |
| `FR-DATA-038` | Data | Aggregate sorted canonical ticks into OHLCV bars with explicit timeframe and spread policy, rejecting disorder or ambiguous spread units. | T1 Core | S | `P-SYS-001` | 2 | `app/services/data/README.md` |
| `FR-DATA-077` | Data | Authorize and execute a bounded, deterministically ordered audit query without exposing storage handles or unredacted payloads. | T1 Core | S | `P-SYS-001` | 2 | `app/services/data/README.md` |
| `FR-DATA-080` | Data | Align a private tabular market-data copy to an aware UTC datetime field/index without mutating caller input. | T1 Core | S | `P-SYS-001` | 2 | `app/services/data/README.md` |
| `FR-DATA-081` | Data | Convert bar rows or private DataFrames to deterministic JSON-safe records with canonical UTC timestamps. | T1 Core | S | `P-SYS-001` | 2 | `app/services/data/README.md` |
| `FR-DATA-082` | Data | Compare aligned private DataFrames using explicit finite tolerance and bounded diagnostics. | T1 Core | S | `P-SYS-001` | 2 | `app/services/data/README.md` |
| `FR-DATA-083` | Data | Compare OHLC or OHLCV columns only after schema and alignment validation. | T1 Core | S | `P-SYS-001` | 2 | `app/services/data/README.md` |
| `FR-DATA-084` | Data | Keep ingestion chunking private to the bounded backfill workflow; expose no generic sequence helper. | T1 Core | S | `P-SYS-001` | 2 | `app/services/data/README.md` |
| `P-DATA-002` | Data | storage feature/component (provisional) | T1 Core | M | `P-SYS-001` | 2 | `app/services/data/README.md` |
| `P-DATA-003` | Data | sources feature/component (provisional) | T1 Core | M | `P-SYS-001` | 2 | `app/services/data/README.md` |
| `P-DATA-005` | Data | processing feature/component (provisional) | T1 Core | M | `P-SYS-001` | 2 | `app/services/data/README.md` |
| `WF-DATA-002` | Data | Cross-domain | T1 Core | M | `P-SYS-001` | 2 | `app/services/data/README.md` |
| `WF-DATA-003` | Data | Local Dataset Load and Save | T1 Core | M | `P-SYS-001` | 2 | `app/services/data/README.md` |
| `WF-DATA-004` | Data | Resample, Align, and Aggregate | T1 Core | M | `P-SYS-001` | 2 | `app/services/data/README.md` |
| `WF-DATA-005` | Data | Cross-domain | T1 Core | M | `P-SYS-001` | 2 | `app/services/data/README.md` |
| `WF-DATA-009` | Data | Cross-domain | T1 Core | M | `P-SYS-001` | 2 | `app/services/data/README.md` |
| `WF-DATA-010` | Data | Cross-domain | T1 Core | M | `P-SYS-001` | 2 | `app/services/data/README.md` |
| `WF-DATA-011` | Data | Source Readiness and Promotion | T1 Core | M | `P-SYS-001` | 2 | `app/services/data/README.md` |
| `CAP-DATA-008` | Data | SQLite state and transactional infrastructure | T1 Core | M | `P-SYS-001` | 5 | `app/services/data/README.md` |
| `CAP-DATA-019` | Data | Simulation tick-model boundary | T1 Core | M | `P-SYS-001` | 6 | `app/services/data/README.md` |
| `WF-DATA-012` | Data | Simulation Data-Modelling Boundary | T1 Core | M | `P-SYS-001` | 6 | `app/services/data/README.md` |
| `WF-DATA-015` | Data | FX Conversion Evidence | T1 Core | M | `P-SYS-001` | 6 | `app/services/data/README.md` |
| `CAP-DATA-010` | Data | Internal real-time feed lifecycle | T1 Core | M | `P-SYS-001` | 11 | `app/services/data/README.md` |
| `FR-DATA-042` | Data | Execute retrieval, normalization, quality, persistence, and checkpoint for one bounded chunk as one recoverable unit, deduplicating a committed key. | T1 Core | S | `P-SYS-001` | 11 | `app/services/data/README.md` |
| `FR-DATA-043` | Data | Validate interrupted job leases/checkpoints at startup and resume only after the last committed chunk without publishing partial work. | T1 Core | S | `P-SYS-001` | 11 | `app/services/data/README.md` |
| `FR-DATA-044` | Data | Start or stop a persisted job only after state-transition, lease, source-policy, and schedule validation; recurring execution uses the single-node in-process... | T1 Core | S | `P-SYS-001` | 11 | `app/services/data/README.md` |
| `FR-DATA-045` | Data | Return persisted job definition/state, enabled flag, run/checkpoint/error/next-run evidence, lease and recovery state, and request ID without mutation. | T1 Core | S | `P-SYS-001` | 11 | `app/services/data/README.md` |
| `FR-DATA-047` | Data | Normalize each event, update heartbeat/counters, enforce bounded overflow, record gap windows/drops, and reconnect with bounded backoff without hidden histor... | T1 Core | S | `P-SYS-001` | 11 | `app/services/data/README.md` |
| `FR-DATA-048` | Data | Return bounded feed ID/state, heartbeat/event times, depth/capacity, dropped/gap/reconnect counts, breaker state, drift, and last safe error from real runtim... | T1 Core | S | `P-SYS-001` | 11 | `app/services/data/README.md` |
| `P-DATA-006` | Data | jobs feature/component (provisional) | T1 Core | M | `P-SYS-001` | 11 | `app/services/data/README.md` |
| `P-DATA-007` | Data | feeds feature/component (provisional) | T1 Core | M | `P-SYS-001` | 11 | `app/services/data/README.md` |
| `WF-DATA-007` | Data | Update Job and Historical Backfill | T1 Core | M | `P-SYS-001` | 11 | `app/services/data/README.md` |
| `WF-DATA-008` | Data | Internal Real-Time Feed and Status | T1 Core | M | `P-SYS-001` | 11 | `app/services/data/README.md` |
| `NFR-DATA-001` | Data | Architecture | T3 Complete | S | `P-SYS-001` | 12 | `app/services/data/README.md` |
| `NFR-DATA-002` | Data | Determinism | T3 Complete | S | `P-SYS-001` | 12 | `app/services/data/README.md` |
| `NFR-DATA-003` | Data | Time safety | T3 Complete | S | `P-SYS-001` | 12 | `app/services/data/README.md` |
| `NFR-DATA-004` | Data | Reliability | T3 Complete | S | `P-SYS-001` | 12 | `app/services/data/README.md` |
| `NFR-DATA-005` | Data | Security | T3 Complete | S | `P-SYS-001` | 12 | `app/services/data/README.md` |
| `NFR-DATA-006` | Data | Broker safety | T3 Complete | S | `P-SYS-001` | 12 | `app/services/data/README.md` |
| `NFR-DATA-007` | Data | Persistence | T3 Complete | S | `P-SYS-001` | 12 | `app/services/data/README.md` |
| `NFR-DATA-008` | Data | Observability | T3 Complete | S | `P-SYS-001` | 12 | `app/services/data/README.md` |
| `NFR-DATA-009` | Data | Performance | T3 Complete | S | `P-SYS-001` | 12 | `app/services/data/README.md` |
| `NFR-DATA-010` | Data | Compatibility | T3 Complete | S | `P-SYS-001` | 12 | `app/services/data/README.md` |
| `NFR-DATA-011` | Data | Maintainability | T3 Complete | S | `P-SYS-001` | 12 | `app/services/data/README.md` |
| `NFR-DATA-012` | Data | Testing | T3 Complete | S | `P-SYS-001` | 12 | `app/services/data/README.md` |
| `CAP-DATA-001` | Data | Typed public and internal API boundary | T3 Complete | M | `P-SYS-001` | 13 | `app/services/data/README.md` |
| `CAP-DATA-002` | Data | Historical OHLCV/tick/spread retrieval | T3 Complete | M | `P-SYS-001` | 13 | `app/services/data/README.md` |
| `CAP-DATA-005` | Data | Quality/gaps/availability/revision | T3 Complete | M | `P-SYS-001` | 13 | `app/services/data/README.md` |
| `CAP-DATA-006` | Data | Versioned cache and safe clear | T3 Complete | M | `P-SYS-001` | 13 | `app/services/data/README.md` |
| `CAP-DATA-009` | Data | Jobs and resumable backfills | T3 Complete | M | `P-SYS-001` | 13 | `app/services/data/README.md` |
| `CAP-DATA-011` | Data | Timeframes/resampling/alignment/aggregation | T3 Complete | M | `P-SYS-001` | 13 | `app/services/data/README.md` |
| `CAP-DATA-012` | Data | Deterministic synthetic generation | T3 Complete | M | `P-SYS-001` | 13 | `app/services/data/README.md` |
| `CAP-DATA-013` | Data | Historical labeling | T3 Complete | M | `P-SYS-001` | 13 | `app/services/data/README.md` |
| `CAP-DATA-014` | Data | Market hours/sessions/volume | T3 Complete | M | `P-SYS-001` | 13 | `app/services/data/README.md` |
| `CAP-DATA-017` | Data | Errors/request correlation/audit/side effects | T3 Complete | M | `P-SYS-001` | 13 | `app/services/data/README.md` |
| `CAP-DATA-018` | Data | Workflow-aware precision/serialization | T3 Complete | M | `P-SYS-001` | 13 | `app/services/data/README.md` |
| `CAP-DATA-020` | Data | Legacy implementation/facade cleanup | T3 Complete | M | `P-SYS-001` | 13 | `app/services/data/README.md` |
| `CAP-DATA-021` | Data | Tests and validation evidence | T3 Complete | M | `P-SYS-001` | 13 | `app/services/data/README.md` |
| `FR-DATA-009` | Data | Negative requirement: Data exposes no restricted broker-execution channel. | T3 Complete | S | `P-SYS-001` | 13 | `app/services/data/README.md` |
| `FR-DATA-029` | Data | Negative requirement: Data issues no mutation capability; Trading obtains it from Brokers. | T3 Complete | S | `P-SYS-001` | 13 | `app/services/data/README.md` |
| `FR-DATA-040` | Data | Negative requirement: Data contains no historical labeling implementation. | T3 Complete | S | `P-SYS-001` | 13 | `app/services/data/README.md` |
| `WF-DATA-006` | Data | Negative requirement: historical labeling remains outside Data and owned by Research. | T3 Complete | M | `P-SYS-001` | 13 | `app/services/data/README.md` |
| `FR-INDI-001` | Indicators | expose exactly the approved Core MVP codes: IND_INVALID_CONFIG, IND_INVALID_PARAMETER, IND_UNSUPPORTED_INDICATOR, IND_UNSUPPORTED_TIMEFRAME,... | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/indicators/README.md` |
| `FR-INDI-002` | Indicators | represent a deterministic, redacted failure with code, safe message, and structured details without exposing raw exceptions or sensitive inp... | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/indicators/README.md` |
| `FR-INDI-003` | Indicators | represent indicator ID, canonical parameters, source, output/precision/availability/quality policy, error mode, and basic limits in one immu... | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/indicators/README.md` |
| `FR-INDI-004` | Indicators | describe each official indicator's ID, name, versions, tier, required columns, parameter/output schemas, warmup policy, supported batch capa... | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/indicators/README.md` |
| `FR-INDI-005` | Indicators | expose the exact normalized history requirement for an indicator/config without fetching data, including minimum observations, source timefr... | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/indicators/README.md` |
| `FR-INDI-006` | Indicators | expose a minimal structural batch protocol whose approved calculation accepts normalized pandas data plus IndicatorConfig and returns Indica... | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/indicators/README.md` |
| `FR-INDI-007` | Indicators | expose a standalone serializable deterministic manifest containing manifest/indicator/formula/output-schema versions, canonical parameter ha... | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/indicators/README.md` |
| `FR-INDI-008` | Indicators | return timestamp/symbol-aligned values, canonical output columns, availability, quality, errors, and manifest as IndicatorSeries v1, preserv... | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/indicators/README.md` |
| `FR-INDI-009` | Indicators | expose a copy-safe projection containing generated indicator, availability, and quality columns without original OHLCV columns. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/indicators/README.md` |
| `FR-INDI-010` | Indicators | append generated columns to a copy of aligned source data while preserving original columns, row count/order, timestamp/symbol layout, warmu... | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/indicators/README.md` |
| `FR-INDI-011` | Indicators | resolve one official ID (ema, sma, adx, atr, adr, rolling_volatility, rsi, williams_r) to its immutable spec and reject all unknown IDs befo... | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/indicators/README.md` |
| `FR-INDI-012` | Indicators | list official specs in stable indicator-ID order with no mutable registry handle. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/indicators/README.md` |
| `FR-INDI-013` | Indicators | expose a JSON/YAML-compatible matrix containing ID, versions, tier, batch/vectorized/multi-symbol/multi-timeframe support, unsupported optio... | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/indicators/README.md` |
| `FR-INDI-014` | Indicators | resolve the spec and atomically validate config, parameters, resource limits, lowercase/unique required columns, supported dtype/timeframe, ... | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/indicators/README.md` |
| `FR-INDI-015` | Indicators | calculate EMA per symbol from a validated source using the approved seed/smoothing contract, return ema_{period} (or source-qualified name),... | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/indicators/README.md` |
| `FR-INDI-016` | Indicators | calculate SMA per symbol over the approved inclusive window, return deterministic source-qualified output, preserve warmup rows, and expose ... | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/indicators/README.md` |
| `FR-INDI-017` | Indicators | calculate approved ADX, +DI, and -DI values per symbol from validated OHLC, return the three canonical columns with warmup/availability meta... | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/indicators/README.md` |
| `P-INDI-001` | Indicators | core feature/component (provisional) | T0 Skeleton | M | `P-SYS-001` | 1 | `app/services/indicators/README.md` |
| `P-INDI-002` | Indicators | trend feature/component (provisional) | T0 Skeleton | M | `P-SYS-001` | 1 | `app/services/indicators/README.md` |
| `WF-INDI-001` | Indicators | Core Batch Indicator Calculation | T0 Skeleton | M | `P-SYS-001` | 1 | `app/services/indicators/README.md` |
| `WF-INDI-002` | Indicators | Decision-Time Consumption | T0 Skeleton | M | `P-SYS-001` | 1 | `app/services/indicators/README.md` |
| `FR-INDI-018` | Indicators | calculate non-negative ATR per symbol from validated OHLC using the approved true-range/smoothing/seed contract, preserve gap and warmup sem... | T1 Core | S | `P-SYS-001` | 3 | `app/services/indicators/README.md` |
| `FR-INDI-019` | Indicators | calculate ADR per symbol using the owner-approved range and session/day convention, preserve warmup rows, and return deterministic availabil... | T1 Core | S | `P-SYS-001` | 3 | `app/services/indicators/README.md` |
| `FR-INDI-020` | Indicators | calculate rolling volatility per symbol from the approved simple/log-return, ddof, window, and annualization convention, handling constant/a... | T1 Core | S | `P-SYS-001` | 3 | `app/services/indicators/README.md` |
| `FR-INDI-021` | Indicators | calculate RSI per symbol using the approved gain/loss smoothing and seed contract, keep values within approved bounds, handle flat/zero-gain... | T1 Core | S | `P-SYS-001` | 3 | `app/services/indicators/README.md` |
| `FR-INDI-022` | Indicators | calculate Williams %R per symbol over the approved inclusive high/low window, enforce approved bounds and zero-range behavior, preserve warm... | T1 Core | S | `P-SYS-001` | 3 | `app/services/indicators/README.md` |
| `P-INDI-003` | Indicators | volatility feature/component (provisional) | T1 Core | M | `P-SYS-001` | 3 | `app/services/indicators/README.md` |
| `P-INDI-004` | Indicators | momentum feature/component (provisional) | T1 Core | M | `P-SYS-001` | 3 | `app/services/indicators/README.md` |
| `WF-INDI-003` | Indicators | Warmup Coordination | T1 Core | M | `P-SYS-001` | 3 | `app/services/indicators/README.md` |
| `WF-INDI-004` | Indicators | Availability-Aware Multi-Timeframe Calculation | T1 Core | M | `P-SYS-001` | 3 | `app/services/indicators/README.md` |
| `WF-INDI-005` | Indicators | Static Registry Discovery and Validation | T1 Core | M | `P-SYS-001` | 3 | `app/services/indicators/README.md` |
| `NFR-INDI-001` | Indicators | Architecture | T3 Complete | S | `P-SYS-001` | 12 | `app/services/indicators/README.md` |
| `NFR-INDI-002` | Indicators | Determinism | T3 Complete | S | `P-SYS-001` | 12 | `app/services/indicators/README.md` |
| `NFR-INDI-003` | Indicators | API boundary | T3 Complete | S | `P-SYS-001` | 12 | `app/services/indicators/README.md` |
| `NFR-INDI-004` | Indicators | Maintainability | T3 Complete | S | `P-SYS-001` | 12 | `app/services/indicators/README.md` |
| `NFR-INDI-005` | Indicators | Vectorization | T3 Complete | S | `P-SYS-001` | 12 | `app/services/indicators/README.md` |
| `NFR-INDI-006` | Indicators | Numeric policy | T3 Complete | S | `P-SYS-001` | 12 | `app/services/indicators/README.md` |
| `NFR-INDI-007` | Indicators | No-lookahead | T3 Complete | S | `P-SYS-001` | 12 | `app/services/indicators/README.md` |
| `NFR-INDI-008` | Indicators | Data boundary | T3 Complete | S | `P-SYS-001` | 12 | `app/services/indicators/README.md` |
| `NFR-INDI-009` | Indicators | Reliability | T3 Complete | S | `P-SYS-001` | 12 | `app/services/indicators/README.md` |
| `NFR-INDI-010` | Indicators | Concurrency | T3 Complete | S | `P-SYS-001` | 12 | `app/services/indicators/README.md` |
| `NFR-INDI-011` | Indicators | Testing | T3 Complete | S | `P-SYS-001` | 12 | `app/services/indicators/README.md` |
| `NFR-INDI-012` | Indicators | Coverage | T3 Complete | S | `P-SYS-001` | 12 | `app/services/indicators/README.md` |
| `NFR-INDI-013` | Indicators | Dependencies | T3 Complete | S | `P-SYS-001` | 12 | `app/services/indicators/README.md` |
| `NFR-INDI-014` | Indicators | Security | T3 Complete | S | `P-SYS-001` | 12 | `app/services/indicators/README.md` |
| `FR-STR-001` | Strategy | enumerate only approved Strategy runtime profiles and reject unsupported values. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/strategy/README.md` |
| `FR-STR-002` | Strategy | identify the decision timing policy used for every evaluation. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/strategy/README.md` |
| `FR-STR-003` | Strategy | represent immutable registry lifecycle eligibility without granting governance approval itself. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/strategy/README.md` |
| `FR-STR-004` | Strategy | accept a non-empty strategy id, exact version or version constraint, environment, and trace identifiers for resolution. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/strategy/README.md` |
| `FR-STR-005` | Strategy | expose the single immutable registry entry selected for execution, including hashes and compatibility metadata. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/strategy/README.md` |
| `FR-STR-006` | Strategy | represent declarative JSON-compatible strategy configuration without executable values. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/strategy/README.md` |
| `FR-STR-007` | Strategy | expose normalized defaults, schema version, and canonical configuration hash after validation. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/strategy/README.md` |
| `FR-STR-008` | Strategy | define one applicability-aware manifest for identity, data, indicators, timing, environments, resources, local risk assumptions, execution p... | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/strategy/README.md` |
| `FR-STR-009` | Strategy | define the completeStrategyRegistrationRequest v1 receiver-owned command described in Section 1. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/strategy/README.md` |
| `FR-STR-010` | Strategy | define the completeStrategyParameterUpdateRequest v1 receiver-owned command described in Section 1. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/strategy/README.md` |
| `FR-STR-011` | Strategy | fix environment, decision timestamp, timing policy, seed, trace identifiers, dependency status, and immutable snapshot references for one ev... | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/strategy/README.md` |
| `FR-STR-012` | Strategy | represent one typed event without granting mutable access to official external state. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/strategy/README.md` |
| `FR-STR-013` | Strategy | represent a neutral decision or proposed actions, rationale references, diagnostics facts, and candidate local-state update. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/strategy/README.md` |
| `FR-STR-014` | Strategy | return ordered intents, diagnostics, replay metadata, and an optional validated local-state update as one atomic result. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/strategy/README.md` |
| `FR-STR-015` | Strategy | represent a stable Strategy error code, safe message, redacted details, and trace identifiers without exposing raw exceptions. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/strategy/README.md` |
| `FR-STR-016` | Strategy | return exactly one typed success value or one structured error for every public operation. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/strategy/README.md` |
| `FR-STR-017` | Strategy | return a versioned immutable mutation result for every registration or parameter-version command, including exact record references/hashes, ... | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/strategy/README.md` |
| `FR-STR-018` | Strategy | expose only the accepted deterministic codes listed below, includingSTRATEGY_ARBITRARY_CODE_REJECTED instead of the cross-domain SIM_* name. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/strategy/README.md` |
| `FR-STR-019` | Strategy | export schema-valid diagnostics after recursive redaction and payload-size enforcement. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/strategy/README.md` |
| `FR-STR-020` | Strategy | register one unique immutable strategy version only after command, schema, module, hash, provenance, and lifecycle-reference validation. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/strategy/README.md` |
| `FR-STR-021` | Strategy | validate and record a parameter update as a new canonical configuration hash without mutating an approved prior record. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/strategy/README.md` |
| `FR-STR-023` | Strategy | resolve exactly one approved immutable version and fail before execution for invalid identity, lifecycle, environment, module, or hashes. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/strategy/README.md` |
| `FR-STR-024` | Strategy | validate declarative configuration, explicit defaults, unknown fields, types, enums, bounds, and resource limits, producing a canonical hash... | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/strategy/README.md` |
| `FR-STR-025` | Strategy | define and validate every field of the canonicalTradeIntent v1 contract described in Section 1. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/strategy/README.md` |
| `FR-STR-026` | Strategy | build a schema-valid intent with deterministic IDs, monotonic sequence, canonical idempotency key, and preserved parent/lineage references. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/strategy/README.md` |
| `FR-STR-029` | Strategy | create a deterministic replay manifest from exact validated identities and input hashes. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/strategy/README.md` |
| `FR-STR-030` | Strategy | serialize and checksum candidate local decision state only after redaction and size validation. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/strategy/README.md` |
| `FR-STR-031` | Strategy | reject corrupt, incompatible, mismatched, unauthorized, or oversized checkpoints before evaluation. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/strategy/README.md` |
| `FR-STR-032` | Strategy | validate normalized data, indicator readiness, previous-close timing, fixed decision clock, environment, config, deterministic ordering, and... | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/strategy/README.md` |
| `FR-STR-033` | Strategy | invoke one declared typed event hook in deterministic order using immutable external snapshots, and shall atomically return intents, diagnos... | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/strategy/README.md` |
| `P-STR-001` | Strategy | contracts feature/component (provisional) | T0 Skeleton | M | `P-SYS-001` | 1 | `app/services/strategy/README.md` |
| `P-STR-004` | Strategy | intents feature/component (provisional) | T0 Skeleton | M | `P-SYS-001` | 1 | `app/services/strategy/README.md` |
| `P-STR-006` | Strategy | vectorized feature/component (provisional) | T0 Skeleton | M | `P-SYS-001` | 1 | `app/services/strategy/README.md` |
| `WF-STR-001` | Strategy | Validate Strategy Reference and Configuration | T0 Skeleton | M | `P-SYS-001` | 1 | `app/services/strategy/README.md` |
| `WF-STR-002` | Strategy | Generate Vectorized Strategy Decisions | T0 Skeleton | M | `P-SYS-001` | 1 | `app/services/strategy/README.md` |
| `WF-STR-004` | Strategy | Build and Hand Off TradeIntent | T0 Skeleton | M | `P-SYS-001` | 1 | `app/services/strategy/README.md` |
| `P-STR-002` | Strategy | diagnostics feature/component (provisional) | T1 Core | M | `P-SYS-001` | 2 | `app/services/strategy/README.md` |
| `WF-STR-006` | Strategy | Export Structured Diagnostics | T1 Core | M | `P-SYS-001` | 2 | `app/services/strategy/README.md` |
| `FR-STR-022` | Strategy | return immutable registry entries in deterministic strategy-id/version order without exposing persistence objects. | T1 Core | S | `P-SYS-001` | 3 | `app/services/strategy/README.md` |
| `P-STR-003` | Strategy | registry feature/component (provisional) | T1 Core | M | `P-SYS-001` | 3 | `app/services/strategy/README.md` |
| `P-STR-007` | Strategy | event feature/component (provisional) | T1 Core | M | `P-SYS-001` | 3 | `app/services/strategy/README.md` |
| `WF-STR-003` | Strategy | Run Stateful Event Strategy Hook | T1 Core | M | `P-SYS-001` | 3 | `app/services/strategy/README.md` |
| `WF-STR-008` | Strategy | Register Immutable Strategy Version | T1 Core | M | `P-SYS-001` | 3 | `app/services/strategy/README.md` |
| `WF-STR-009` | Strategy | Reject Arbitrary Strategy Code | T1 Core | M | `P-SYS-001` | 3 | `app/services/strategy/README.md` |
| `FR-STR-027` | Strategy | bind strategy/interface/config/data/indicator/simulation/seed/timing identity for deterministic replay. | T1 Core | S | `P-SYS-001` | 6 | `app/services/strategy/README.md` |
| `FR-STR-028` | Strategy | contain only serializable, redacted, bounded strategy-local state with identity, schema, checksum, and authorization reference. | T1 Core | S | `P-SYS-001` | 6 | `app/services/strategy/README.md` |
| `P-STR-005` | Strategy | replay feature/component (provisional) | T1 Core | M | `P-SYS-001` | 6 | `app/services/strategy/README.md` |
| `WF-STR-005` | Strategy | Create Replay Manifest and Checkpoint | T1 Core | M | `P-SYS-001` | 6 | `app/services/strategy/README.md` |
| `WF-STR-007` | Strategy | Supply Paper/Live Decisions | T1 Core | M | `P-SYS-001` | 11 | `app/services/strategy/README.md` |
| `NFR-STR-001` | Strategy | Architecture | T3 Complete | S | `P-SYS-001` | 12 | `app/services/strategy/README.md` |
| `NFR-STR-002` | Strategy | Determinism | T3 Complete | S | `P-SYS-001` | 12 | `app/services/strategy/README.md` |
| `NFR-STR-003` | Strategy | Safety | T3 Complete | S | `P-SYS-001` | 12 | `app/services/strategy/README.md` |
| `NFR-STR-004` | Strategy | Security | T3 Complete | S | `P-SYS-001` | 12 | `app/services/strategy/README.md` |
| `NFR-STR-005` | Strategy | Reliability | T3 Complete | S | `P-SYS-001` | 12 | `app/services/strategy/README.md` |
| `NFR-STR-006` | Strategy | Error handling | T3 Complete | S | `P-SYS-001` | 12 | `app/services/strategy/README.md` |
| `NFR-STR-007` | Strategy | Precision | T3 Complete | S | `P-SYS-001` | 12 | `app/services/strategy/README.md` |
| `NFR-STR-008` | Strategy | Time | T3 Complete | S | `P-SYS-001` | 12 | `app/services/strategy/README.md` |
| `NFR-STR-009` | Strategy | Compatibility | T3 Complete | S | `P-SYS-001` | 12 | `app/services/strategy/README.md` |
| `NFR-STR-010` | Strategy | Maintainability | T3 Complete | S | `P-SYS-001` | 12 | `app/services/strategy/README.md` |
| `NFR-STR-011` | Strategy | Testing | T3 Complete | S | `P-SYS-001` | 12 | `app/services/strategy/README.md` |
| `NFR-STR-012` | Strategy | Performance | T3 Complete | S | `P-SYS-001` | 12 | `app/services/strategy/README.md` |
| `FR-RISK-001` | Risk | Define approve, warn, needs_approval, needs_more_evidence, reject, block, and error exactly. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/risk/README.md` |
| `FR-RISK-002` | Risk | Define pass, warn, needs_more_evidence, fail, and blocked exactly. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/risk/README.md` |
| `FR-RISK-003` | Risk | Define every accepted deterministic Risk error code; historical VaR/CVaR is the sole supported VaR method. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/risk/README.md` |
| `FR-RISK-004` | Risk | Carry immutable account/position/pending-order/symbol/market evidence with UTC as_of, provenance, missingness, and schema version. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/risk/README.md` |
| `FR-RISK-005` | Risk | Carry reproducible base-currency metrics, limit results, assumptions, coverage, regime, request/workflow IDs, evidence refs, and config hash. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/risk/README.md` |
| `FR-RISK-006` | Risk | Represent one non-executable risk-increasing proposal with intent reference, scope, direction, requested size, price/stop evidence, validity, and provenance. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/risk/README.md` |
| `FR-RISK-007` | Risk | Represent one of six sizing methods and its complete evidence/config references. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/risk/README.md` |
| `FR-RISK-008` | Risk | Return exact requested/normalized size, constraints applied, evidence gaps, fallback disclosure, and no approval claim. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/risk/README.md` |
| `FR-RISK-009` | Risk | Validate and review AllocationReviewRequest v1 without constructing or applying a Portfolio allocation. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/risk/README.md` |
| `FR-RISK-010` | Risk | Validate StrategyOperationalEligibilityRequest v1 for an exact registered strategy/version and scope. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/risk/README.md` |
| `FR-RISK-011` | Risk | Return classified volatility/liquidity/correlation/drawdown/crisis/news/session states, transition evidence, modifiers, and missingness. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/risk/README.md` |
| `FR-RISK-012` | Risk | Define a bounded immutable advisory scenario with deterministic shocks and optional explicit seed. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/risk/README.md` |
| `FR-RISK-013` | Risk | Return baseline/projected risk comparison and state that the output is advisory and not approved. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/risk/README.md` |
| `FR-RISK-014` | Risk | Implement RiskDecision v1 with verdict, approved size, ordered checks, primary/composite reasons, provenance, expiry, concurrency disclosure, and optional to... | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/risk/README.md` |
| `FR-RISK-015` | Risk | Carry signed token scope, decision/config hashes, approver, expiry, nonce, schema version, and no secret key. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/risk/README.md` |
| `FR-RISK-016` | Risk | Implement KillSwitchCommand v1 with action, explicit scope level, applicable portfolio/strategy/symbol identifiers, reason, UTC timestamp, request/workflow/c... | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/risk/README.md` |
| `FR-RISK-017` | Risk | Implement KillSwitchState v1 with scope, active/unknown state, reason, version, and UTC update time. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/risk/README.md` |
| `FR-RISK-018` | Risk | Carry canonical redacted audit payload, evidence/config/decision provenance, sequence, previous hash, and record hash. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/risk/README.md` |
| `FR-RISK-019` | Risk | Carry Markdown or exact JSON summary with separated evidence, assumptions, warnings, decision, and recommendations. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/risk/README.md` |
| `FR-RISK-020` | Risk | Return token validity, consumption state, reason code, and audit reference without exposing secrets. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/risk/README.md` |
| `FR-RISK-021` | Risk | Raise one redacted domain exception carrying a RiskErrorCode and safe details for boundary mapping. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/risk/README.md` |
| `FR-RISK-023` | Risk | Load only the selected YAML profile from the bounded root and fail closed on missing/invalid live configuration. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/risk/README.md` |
| `FR-RISK-025` | Risk | Build an immutable snapshot containing pending-order-aware gross/net exposure by dimension, account-currency conversions, drawdown/loss state, margin/leverag... | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/risk/README.md` |
| `FR-RISK-026` | Risk | Calculate fixed-lot, fixed-risk, milestone, fractional-Kelly, volatility, or fixed-fractional size; enforce stop/equity/evidence rules; disclose fallback/cor... | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/risk/README.md` |
| `FR-RISK-027` | Risk | Evaluate daily/total loss, drawdown state, consistency, exposure/concentration, margin/leverage, historical tail risk, correlation, and freshness in determin... | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/risk/README.md` |
| `FR-RISK-029` | Risk | Produce and persist StrategyOperationalEligibilityDecision v1 with exact scope, conditions, evidence/policy lineage, issue/expiry, and suspension semantics; ... | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/risk/README.md` |
| `FR-RISK-030` | Risk | Produce AllocationRiskDecision v1, enforce caps, and atomically activate the authoritative risk-budget projection only for the exact approved Portfolio version. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/risk/README.md` |
| `FR-RISK-031` | Risk | Classify volatility, liquidity, correlation, drawdown, crisis, news, and session regimes; record deterministic transitions/evidence; return only equal-or-str... | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/risk/README.md` |
| `FR-RISK-033` | Risk | Redact, canonicalize, hash, and durably append a material record with previous-hash continuity. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/risk/README.md` |
| `FR-RISK-034` | Risk | Verify genesis, sequence, previous hash, and record hash; identify tamper deterministically. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/risk/README.md` |
| `FR-RISK-036` | Risk | Validate Risk-owned, UI/API-produced ApprovalAttestation v1, then issue a tamper-evident token only for an eligible decision, binding request/workflow/action... | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/risk/README.md` |
| `FR-RISK-037` | Risk | Atomically verify schema/signature/scope/hashes/attestation/time/revocation/nonce, reserve token + workflow + action scope + expiry, persist single-use consu... | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/risk/README.md` |
| `FR-RISK-038` | Risk | Revoke every outstanding token intersecting an activated global/portfolio/strategy/symbol scope and write a material audit event. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/risk/README.md` |
| `FR-RISK-039` | Risk | Own immutable config plus injected token, audit, clock, and optional configured concurrency protection dependencies. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/risk/README.md` |
| `FR-RISK-040` | Risk | Validate and review one proposed trade in fixed precedence, include regime/projected risks/final capped size/concurrency disclosure, attach token only when e... | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/risk/README.md` |
| `FR-RISK-041` | Risk | Evaluate current portfolio compliance and return a remediation recommendation without changing execution state. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/risk/README.md` |
| `FR-RISK-042` | Risk | Compare proposal/evidence/config/time with a prior decision and invalidate material changes, expiry, skew, stale state, config mismatch, or reconciliation ex... | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/risk/README.md` |
| `FR-RISK-043` | Risk | Apply authorized activation/clearance under global > portfolio > strategy > symbol precedence, revoke affected approvals on activation, and never mutate exec... | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/risk/README.md` |
| `FR-RISK-044` | Risk | Return deterministic block/recovery eligibility; active or unknown applicable state blocks live risk increase, and recovery requires all applicable scopes in... | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/risk/README.md` |
| `FR-RISK-045` | Risk | Deterministically apply bounded scenarios to immutable snapshot evidence, return baseline/projected risk differences, preserve explicit seed, and mark every ... | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/risk/README.md` |
| `FR-RISK-046` | Risk | Render evidence, calculations, assumptions, warnings, decision, and recommendations separately; show primary failure first; never claim live approval without... | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/risk/README.md` |
| `FR-RISK-058` | Risk | Validate the consumed Data-owned MarketContextEvidence v1 version, UTC freshness, provenance, bounded values, and explicit missingness without redefining or ... | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/risk/README.md` |
| `FR-RISK-059` | Risk | Return ActionPolicyVerdict v1 bound to action, scope, policy version, approval attestation, decision, reservation, expiry, reasons, and trace IDs. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/risk/README.md` |
| `FR-RISK-060` | Risk | Carry one ordered limit result with status, observed/threshold values, reason code, evidence refs, and precedence without granting approval. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/risk/README.md` |
| `P-RISK-001` | Risk | contracts feature/component (provisional) | T0 Skeleton | M | `P-SYS-001` | 1 | `app/services/risk/README.md` |
| `P-RISK-002` | Risk | config feature/component (provisional) | T0 Skeleton | M | `P-SYS-001` | 1 | `app/services/risk/README.md` |
| `P-RISK-004` | Risk | sizing feature/component (provisional) | T0 Skeleton | M | `P-SYS-001` | 1 | `app/services/risk/README.md` |
| `P-RISK-005` | Risk | policy feature/component (provisional) | T0 Skeleton | M | `P-SYS-001` | 1 | `app/services/risk/README.md` |
| `P-RISK-007` | Risk | audit feature/component (provisional) | T0 Skeleton | M | `P-SYS-001` | 1 | `app/services/risk/README.md` |
| `P-RISK-008` | Risk | approvals feature/component (provisional) | T0 Skeleton | M | `P-SYS-001` | 1 | `app/services/risk/README.md` |
| `P-RISK-009` | Risk | decisions feature/component (provisional) | T0 Skeleton | M | `P-SYS-001` | 1 | `app/services/risk/README.md` |
| `WF-RISK-002` | Risk | Calculate position size | T0 Skeleton | M | `P-SYS-001` | 1 | `app/services/risk/README.md` |
| `WF-RISK-004` | Risk | Review proposed trade risk | T0 Skeleton | M | `P-SYS-001` | 1 | `app/services/risk/README.md` |
| `WF-RISK-008` | Risk | Validate approval token | T0 Skeleton | M | `P-SYS-001` | 1 | `app/services/risk/README.md` |
| `WF-RISK-009` | Risk | Apply or check kill-switch state | T0 Skeleton | M | `P-SYS-001` | 1 | `app/services/risk/README.md` |
| `WF-RISK-012` | Risk | Persist risk audit and token state | T0 Skeleton | M | `P-SYS-001` | 1 | `app/services/risk/README.md` |
| `FR-RISK-022` | Risk | Define strict profile fields, thresholds, modes, freshness, rounding, concurrency, audit, and dependency timeouts with stable schema version. | T1 Core | S | `P-SYS-001` | 4 | `app/services/risk/README.md` |
| `FR-RISK-024` | Risk | Hash canonical exact serialization so any material config change changes the SHA-256 hash. | T1 Core | S | `P-SYS-001` | 4 | `app/services/risk/README.md` |
| `FR-RISK-028` | Risk | Evaluate supplied spread, slippage, liquidity, session, and calendar evidence without external fetches or naive/aware datetime comparison. | T1 Core | S | `P-SYS-001` | 4 | `app/services/risk/README.md` |
| `FR-RISK-032` | Risk | Own injected canonical serializer, clock, storage port, and deterministic chain configuration without owning database infrastructure. | T1 Core | S | `P-SYS-001` | 4 | `app/services/risk/README.md` |
| `FR-RISK-035` | Risk | Own injected signer/secret resolver, clock, durable state port, authorization verifier, and audit chain. | T1 Core | S | `P-SYS-001` | 4 | `app/services/risk/README.md` |
| `P-RISK-003` | Risk | portfolio feature/component (provisional) | T1 Core | M | `P-SYS-001` | 4 | `app/services/risk/README.md` |
| `P-RISK-006` | Risk | regimes feature/component (provisional) | T1 Core | M | `P-SYS-001` | 4 | `app/services/risk/README.md` |
| `P-RISK-010` | Risk | scenarios feature/component (provisional) | T1 Core | M | `P-SYS-001` | 4 | `app/services/risk/README.md` |
| `P-RISK-011` | Risk | reporting feature/component (provisional) | T1 Core | M | `P-SYS-001` | 4 | `app/services/risk/README.md` |
| `WF-RISK-001` | Risk | Build portfolio risk snapshot | T1 Core | M | `P-SYS-001` | 4 | `app/services/risk/README.md` |
| `WF-RISK-003` | Risk | Assess risk regime | T1 Core | M | `P-SYS-001` | 4 | `app/services/risk/README.md` |
| `WF-RISK-005` | Risk | Run current portfolio governor | T1 Core | M | `P-SYS-001` | 4 | `app/services/risk/README.md` |
| `WF-RISK-010` | Risk | Run scenario or what-if analysis | T1 Core | M | `P-SYS-001` | 4 | `app/services/risk/README.md` |
| `WF-RISK-011` | Risk | Generate risk decision summary | T1 Core | M | `P-SYS-001` | 4 | `app/services/risk/README.md` |
| `WF-RISK-014` | Risk | Revalidate decision/evidence before reuse | T1 Core | M | `P-SYS-001` | 4 | `app/services/risk/README.md` |
| `WF-RISK-006` | Risk | Review strategy admission | T2 Advanced | M | `P-SYS-001` | 9 | `app/services/risk/README.md` |
| `WF-RISK-007` | Risk | Review allocation proposal | T2 Advanced | M | `P-SYS-001` | 9 | `app/services/risk/README.md` |
| `NFR-RISK-001` | Risk | API boundary | T3 Complete | S | `P-SYS-001` | 12 | `app/services/risk/README.md` |
| `NFR-RISK-002` | Risk | Determinism | T3 Complete | S | `P-SYS-001` | 12 | `app/services/risk/README.md` |
| `NFR-RISK-003` | Risk | Precision | T3 Complete | S | `P-SYS-001` | 12 | `app/services/risk/README.md` |
| `NFR-RISK-004` | Risk | Reliability | T3 Complete | S | `P-SYS-001` | 12 | `app/services/risk/README.md` |
| `NFR-RISK-005` | Risk | Concurrency | T3 Complete | S | `P-SYS-001` | 12 | `app/services/risk/README.md` |
| `NFR-RISK-006` | Risk | Security | T3 Complete | S | `P-SYS-001` | 12 | `app/services/risk/README.md` |
| `NFR-RISK-007` | Risk | Observability | T3 Complete | S | `P-SYS-001` | 12 | `app/services/risk/README.md` |
| `NFR-RISK-008` | Risk | Performance | T3 Complete | S | `P-SYS-001` | 12 | `app/services/risk/README.md` |
| `NFR-RISK-009` | Risk | Maintainability | T3 Complete | S | `P-SYS-001` | 12 | `app/services/risk/README.md` |
| `NFR-RISK-010` | Risk | Testing | T3 Complete | S | `P-SYS-001` | 12 | `app/services/risk/README.md` |
| `NFR-RISK-011` | Risk | Persistence | T3 Complete | S | `P-SYS-001` | 12 | `app/services/risk/README.md` |
| `NFR-RISK-012` | Risk | Safety | T3 Complete | S | `P-SYS-001` | 12 | `app/services/risk/README.md` |
| `FR-TRD-001` | Trading | expose only sim, paper, and live action routes; package-only is a side-effect mode, not a route. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/trading/README.md` |
| `FR-TRD-002` | Trading | validate one immutable canonical request with route, action, trace, authority, approval, Risk, idempotency, and UTC evidence. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/trading/README.md` |
| `FR-TRD-003` | Trading | return one finite JSON-safe envelope distinguishing packaging, rejection, block, send, fill, cancellation, unknown outcome, and error. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/trading/README.md` |
| `FR-TRD-004` | Trading | expose OrderIntent v1 exactly as defined in Section 1 and preserve Risk-approved size. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/trading/README.md` |
| `FR-TRD-005` | Trading | expose immutable ExecutionReceipt v1 with authority, status, fill, retry, and reconciliation evidence. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/trading/README.md` |
| `FR-TRD-006` | Trading | expose TradeRecord v1 without deriving Analytics metrics or hiding unreconciled state. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/trading/README.md` |
| `FR-TRD-007` | Trading | expose one finite Trading exception carrying a registered code and redacted trace context. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/trading/README.md` |
| `FR-TRD-008` | Trading | map validation, permission, persistence, timeout, provider, and unknown failures into the canonical envelope without raw exceptions. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/trading/README.md` |
| `FR-TRD-009` | Trading | recursively redact secrets before any log, error, event, metric, or returned payload. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/trading/README.md` |
| `FR-TRD-010` | Trading | return the exact stable Python API with routes, schemas, side effects, approvals, idempotency, statuses, errors, and stability metadata. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/trading/README.md` |
| `FR-TRD-012` | Trading | create a non-executable action draft that cannot call a route authority. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/trading/README.md` |
| `FR-TRD-013` | Trading | submit one validated Risk-approved order through the selected route. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/trading/README.md` |
| `FR-TRD-014` | Trading | modify only the approved identity/scope with optimistic version and caller idempotency. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/trading/README.md` |
| `FR-TRD-015` | Trading | cancel one pending order after normal gates. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/trading/README.md` |
| `FR-TRD-016` | Trading | close a position fully or partially with correct netting/hedging identity. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/trading/README.md` |
| `FR-TRD-017` | Trading | modify only approved stop-loss/take-profit scope. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/trading/README.md` |
| `FR-TRD-018` | Trading | reduce, never increase, exposure and execute exactly the Risk-approved reduction. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/trading/README.md` |
| `FR-TRD-019` | Trading | pause runtime admission without changing strategy lifecycle governance. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/trading/README.md` |
| `FR-TRD-020` | Trading | resume only after a valid Risk-owned ActionPolicyVerdict, all applicable global > portfolio > strategy > symbol kill-switch scopes are inact... | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/trading/README.md` |
| `FR-TRD-021` | Trading | request a scoped Risk-owned kill-switch transition only with a compatible ActionPolicyVerdict; request text cannot create emergency authority. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/trading/README.md` |
| `FR-TRD-022` | Trading | clear a switch only through Risk-authorized clearance; an inactive child cannot override an active parent, and resume requires reconciliatio... | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/trading/README.md` |
| `FR-TRD-023` | Trading | mass-cancel pending or otherwise cancellable orders through normal gates, return every child result, and never claim cancellation for uncert... | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/trading/README.md` |
| `FR-TRD-024` | Trading | validate symbol, action, Decimal volume/price/stops, instrument limits, margin evidence, tickets, and operation preconditions before route s... | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/trading/README.md` |
| `FR-TRD-025` | Trading | synchronize projections from route truth without mutating route orders or positions. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/trading/README.md` |
| `FR-TRD-026` | Trading | return timestamped account/symbol/quote/permission/authority facts or explicit unavailable/stale failures. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/trading/README.md` |
| `FR-TRD-027` | Trading | aggregate all required checks and return a bounded pass/fail assessment with evidence references. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/trading/README.md` |
| `FR-TRD-028` | Trading | construct a deterministic plan and canonical idempotency material without side effects. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/trading/README.md` |
| `FR-TRD-030` | Trading | classify malformed success, timeout, and ambiguous/rate-limited mutation conservatively with retry delay/safety evidence. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/trading/README.md` |
| `FR-TRD-031` | Trading | dispatch exactly one approved intent to Simulation for sim or Brokers' BrokerAdapter mutation operations for paper/live. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/trading/README.md` |
| `FR-TRD-032` | Trading | use one stateful lifecycle object for admission, startup evidence, recovery lock, in-flight work, and shutdown. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/trading/README.md` |
| `FR-TRD-033` | Trading | validate config/security, bind opaque Data authority, and complete startup reconciliation before enabling mutation. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/trading/README.md` |
| `FR-TRD-034` | Trading | return the actual session mode, admission, authority, health, reconciliation, and unresolved-work state. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/trading/README.md` |
| `FR-TRD-035` | Trading | stop admission, drain/mark work, flush evidence, reconcile, and report every incomplete shutdown step. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/trading/README.md` |
| `FR-TRD-036` | Trading | enforce the canonical mandatory gate order and prohibit passthrough Risk or caller-declared emergency authority. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/trading/README.md` |
| `FR-TRD-037` | Trading | represent send attempts, receipts, fills, reconciliation transitions, and incidents as versioned, redacted events. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/trading/README.md` |
| `FR-TRD-038` | Trading | expose only minimal injected operations for idempotency, append, projection reads/writes, and reconciliation evidence. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/trading/README.md` |
| `FR-TRD-039` | Trading | reserve a caller-supplied key against versioned canonical SHA-256 material before send and reject different-material reuse. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/trading/README.md` |
| `FR-TRD-042` | Trading | provide additive Trading migration definitions for execution-owned state without opening a database. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/trading/README.md` |
| `FR-TRD-043` | Trading | expose normalized account/order/position/time authority evidence without provider objects. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/trading/README.md` |
| `FR-TRD-044` | Trading | deterministically report missing, extra, mismatched, and stale records without claiming resolution. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/trading/README.md` |
| `FR-TRD-045` | Trading | lock retry, persist evidence, prefer route authority truth, and release only after an approved transition resolves. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/trading/README.md` |
| `FR-TRD-046` | Trading | represent focused health, dependency, staleness, timeout, latency, cost, and incident evidence in a Trading-owned contract. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/trading/README.md` |
| `FR-TRD-048` | Trading | publish redacted runtime evidence through an injected composition sink without importing Data or UI/API and without hiding delivery failure. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/trading/README.md` |
| `FR-TRD-049` | Trading | package receipts, factual costs, readiness, reconciliation, incidents, warnings, and unresolved actions without calculating performance/TCA. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/trading/README.md` |
| `FR-TRD-050` | Trading | mass-close positions through normal gates and return every child result. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/trading/README.md` |
| `FR-TRD-051` | Trading | The store shall reserve one caller key against canonical material and return the existing/new/conflict decision atomically. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/trading/README.md` |
| `FR-TRD-052` | Trading | The store shall append one versioned event without rewriting prior events. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/trading/README.md` |
| `FR-TRD-053` | Trading | The store shall load the latest projection for an exact route/tenant/authority scope. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/trading/README.md` |
| `FR-TRD-054` | Trading | The store shall save a projection only when the expected optimistic version matches. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/trading/README.md` |
| `FR-TRD-055` | Trading | The store shall return every unresolved send attempt for an exact authority/conflict scope. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/trading/README.md` |
| `FR-TRD-056` | Trading | expose one immutable injected dependency container without resolving secrets or creating route/store dependencies at import time. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/trading/README.md` |
| `FR-TRD-057` | Trading | expose an immutable reservation result distinguishing new, duplicate-completed, duplicate-active, conflict, and reconciliation-required states. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/trading/README.md` |
| `FR-TRD-058` | Trading | expose a route/tenant-scoped order, position, fill, receipt, and authority projection with optimistic version. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/trading/README.md` |
| `FR-TRD-061` | Trading | expose a deterministic comparison result with discrepancy classes, severity, evidence references, and unresolved status. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/trading/README.md` |
| `FR-TRD-062` | Trading | expose the approved authority transition, retry decision, incident reference, and remaining unresolved scope. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/trading/README.md` |
| `P-TRD-001` | Trading | contracts feature/component (provisional) | T0 Skeleton | M | `P-SYS-001` | 1 | `app/services/trading/README.md` |
| `P-TRD-002` | Trading | state feature/component (provisional) | T0 Skeleton | M | `P-SYS-001` | 1 | `app/services/trading/README.md` |
| `P-TRD-003` | Trading | validation feature/component (provisional) | T0 Skeleton | M | `P-SYS-001` | 1 | `app/services/trading/README.md` |
| `P-TRD-004` | Trading | routing feature/component (provisional) | T0 Skeleton | M | `P-SYS-001` | 1 | `app/services/trading/README.md` |
| `P-TRD-005` | Trading | reconciliation feature/component (provisional) | T0 Skeleton | M | `P-SYS-001` | 1 | `app/services/trading/README.md` |
| `P-TRD-007` | Trading | live feature/component (provisional) | T0 Skeleton | M | `P-SYS-001` | 1 | `app/services/trading/README.md` |
| `P-TRD-008` | Trading | actions feature/component (provisional) | T0 Skeleton | M | `P-SYS-001` | 1 | `app/services/trading/README.md` |
| `P-TRD-009` | Trading | reporting feature/component (provisional) | T0 Skeleton | M | `P-SYS-001` | 1 | `app/services/trading/README.md` |
| `WF-TRD-001` | Trading | Validate and package a route-aware action | T0 Skeleton | M | `P-SYS-001` | 1 | `app/services/trading/README.md` |
| `WF-TRD-002` | Trading | Execute a simulation-route action | T0 Skeleton | M | `P-SYS-001` | 1 | `app/services/trading/README.md` |
| `WF-TRD-003` | Trading | Start and enable a live session | T0 Skeleton | M | `P-SYS-001` | 1 | `app/services/trading/README.md` |
| `WF-TRD-004` | Trading | Gate and dispatch a live action | T0 Skeleton | M | `P-SYS-001` | 1 | `app/services/trading/README.md` |
| `WF-TRD-006` | Trading | Read route facts and aggregate readiness | T0 Skeleton | M | `P-SYS-001` | 1 | `app/services/trading/README.md` |
| `WF-TRD-008` | Trading | Persist execution evidence and recover state | T0 Skeleton | M | `P-SYS-001` | 1 | `app/services/trading/README.md` |
| `WF-TRD-011` | Trading | Build execution and reconciliation evidence | T0 Skeleton | M | `P-SYS-001` | 1 | `app/services/trading/README.md` |
| `WF-TRD-012` | Trading | Accept a governed upstream request | T0 Skeleton | M | `P-SYS-001` | 1 | `app/services/trading/README.md` |
| `FR-TRD-059` | Trading | expose one immutable snapshot containing explicit fact values, source, authority, UTC timestamps, freshness, availability, and capability ev... | T1 Core | S | `P-SYS-001` | 4 | `app/services/trading/README.md` |
| `FR-TRD-060` | Trading | expose a bounded passed/failed readiness result with failed check codes and evidence references. | T1 Core | S | `P-SYS-001` | 4 | `app/services/trading/README.md` |
| `WF-TRD-007` | Trading | Activate/enforce kill switch and emergency controls | T1 Core | M | `P-SYS-001` | 4 | `app/services/trading/README.md` |
| `FR-TRD-029` | Trading | reject adapters lacking approved provider, API/schema, action, security, timeout, malformed-response, rate-limit, retry, and redaction decla... | T1 Core | S | `P-SYS-001` | 5 | `app/services/trading/README.md` |
| `FR-TRD-040` | Trading | apply deduplicated authority events in logical order with optimistic version checks. | T1 Core | S | `P-SYS-001` | 5 | `app/services/trading/README.md` |
| `FR-TRD-041` | Trading | expose the current Trading schema version. | T1 Core | S | `P-SYS-001` | 5 | `app/services/trading/README.md` |
| `WF-TRD-005` | Trading | Resolve an unknown route outcome | T1 Core | M | `P-SYS-001` | 5 | `app/services/trading/README.md` |
| `WF-TRD-013` | Trading | Execute an Authorized Portfolio Rebalance | T2 Advanced | M | `P-SYS-001` | 9 | `app/services/trading/README.md` |
| `FR-TRD-047` | Trading | Enforce the current Risk-owned AllocationRiskDecision v1 and authoritative portfolio risk-budget projection for the exact allocation/plan; never calculate or... | T1 Core | S | `P-SYS-001` | 11 | `app/services/trading/README.md` |
| `P-TRD-006` | Trading | monitoring feature/component (provisional) | T1 Core | M | `P-SYS-001` | 11 | `app/services/trading/README.md` |
| `WF-TRD-009` | Trading | Perform safe live shutdown | T1 Core | M | `P-SYS-001` | 11 | `app/services/trading/README.md` |
| `WF-TRD-010` | Trading | Emit monitoring, cost, and incident evidence | T1 Core | M | `P-SYS-001` | 11 | `app/services/trading/README.md` |
| `NFR-TRD-001` | Trading | Safety | T3 Complete | S | `P-SYS-001` | 12 | `app/services/trading/README.md` |
| `NFR-TRD-002` | Trading | Determinism | T3 Complete | S | `P-SYS-001` | 12 | `app/services/trading/README.md` |
| `NFR-TRD-003` | Trading | Security | T3 Complete | S | `P-SYS-001` | 12 | `app/services/trading/README.md` |
| `NFR-TRD-004` | Trading | Reliability | T3 Complete | S | `P-SYS-001` | 12 | `app/services/trading/README.md` |
| `NFR-TRD-005` | Trading | API boundary | T3 Complete | S | `P-SYS-001` | 12 | `app/services/trading/README.md` |
| `NFR-TRD-006` | Trading | Observability | T3 Complete | S | `P-SYS-001` | 12 | `app/services/trading/README.md` |
| `NFR-TRD-007` | Trading | Testing | T3 Complete | S | `P-SYS-001` | 12 | `app/services/trading/README.md` |
| `NFR-TRD-008` | Trading | Performance | T3 Complete | S | `P-SYS-001` | 12 | `app/services/trading/README.md` |
| `CAP-TRD-001` | Trading | Modify | T3 Complete | M | `P-SYS-001` | 13 | `app/services/trading/README.md` |
| `CAP-TRD-002` | Trading | Modify | T3 Complete | M | `P-SYS-001` | 13 | `app/services/trading/README.md` |
| `CAP-TRD-003` | Trading | Merge | T3 Complete | M | `P-SYS-001` | 13 | `app/services/trading/README.md` |
| `CAP-TRD-004` | Trading | Modify | T3 Complete | M | `P-SYS-001` | 13 | `app/services/trading/README.md` |
| `CAP-TRD-005` | Trading | Modify | T3 Complete | M | `P-SYS-001` | 13 | `app/services/trading/README.md` |
| `CAP-TRD-006` | Trading | Add | T3 Complete | M | `P-SYS-001` | 13 | `app/services/trading/README.md` |
| `CAP-TRD-007` | Trading | Modify | T3 Complete | M | `P-SYS-001` | 13 | `app/services/trading/README.md` |
| `CAP-TRD-008` | Trading | Merge | T3 Complete | M | `P-SYS-001` | 13 | `app/services/trading/README.md` |
| `CAP-TRD-009` | Trading | Modify | T3 Complete | M | `P-SYS-001` | 13 | `app/services/trading/README.md` |
| `CAP-TRD-010` | Trading | Modify | T3 Complete | M | `P-SYS-001` | 13 | `app/services/trading/README.md` |
| `CAP-TRD-011` | Trading | Modify | T3 Complete | M | `P-SYS-001` | 13 | `app/services/trading/README.md` |
| `CAP-TRD-012` | Trading | Modify | T3 Complete | M | `P-SYS-001` | 13 | `app/services/trading/README.md` |
| `CAP-TRD-013` | Trading | Modify | T3 Complete | M | `P-SYS-001` | 13 | `app/services/trading/README.md` |
| `CAP-TRD-014` | Trading | Modify | T3 Complete | M | `P-SYS-001` | 13 | `app/services/trading/README.md` |
| `CAP-TRD-015` | Trading | Modify | T3 Complete | M | `P-SYS-001` | 13 | `app/services/trading/README.md` |
| `CAP-TRD-016` | Trading | Merge | T3 Complete | M | `P-SYS-001` | 13 | `app/services/trading/README.md` |
| `CAP-TRD-017` | Trading | Modify | T3 Complete | M | `P-SYS-001` | 13 | `app/services/trading/README.md` |
| `CAP-TRD-018` | Trading | Add | T3 Complete | M | `P-SYS-001` | 13 | `app/services/trading/README.md` |
| `CAP-TRD-019` | Trading | Modify | T3 Complete | M | `P-SYS-001` | 13 | `app/services/trading/README.md` |
| `CAP-TRD-022` | Trading | Remove | T3 Complete | M | `P-SYS-001` | 13 | `app/services/trading/README.md` |
| `CAP-TRD-023` | Trading | Merge | T3 Complete | M | `P-SYS-001` | 13 | `app/services/trading/README.md` |
| `CAP-TRD-024` | Trading | Modify | T3 Complete | M | `P-SYS-001` | 13 | `app/services/trading/README.md` |
| `CAP-TRD-025` | Trading | Modify | T3 Complete | M | `P-SYS-001` | 13 | `app/services/trading/README.md` |
| `CAP-SIM-001` | Simulation | Typed public API and versioned contracts | T0 Skeleton | M | `P-SYS-001` | 1 | `app/services/simulator/README.md` |
| `CAP-SIM-004` | Simulation | Canonical FX execution, matching, realism | T0 Skeleton | M | `P-SYS-001` | 1 | `app/services/simulator/README.md` |
| `FR-SIM-001` | Simulation | validate authentication-relevant request structure, registered strategy references, Data references, broker-profile references, trace identi... | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/simulator/README.md` |
| `FR-SIM-002` | Simulation | verify manifest checksum, required schema, UTC monotonic timestamps, uniqueness, OHLC consistency, bid/ask spread, staleness, availability m... | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/simulator/README.md` |
| `FR-SIM-003` | Simulation | permit only approved FX scope or explicit FAST_RESEARCH, rejecting unsupported assets, features, service mode, and canonical claims from app... | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/simulator/README.md` |
| `FR-SIM-005` | Simulation | transform approved FX bars or real ticks into a stable, strictly ordered bid/ask tick tuple whose identity is reproducible from data, model,... | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/simulator/README.md` |
| `FR-SIM-006` | Simulation | reject a strategy intent whose evidence became available after its execution time and enforce previous-closed-bar visibility by default. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/simulator/README.md` |
| `FR-SIM-010` | Simulation | Apply only supplied fresh FXConversionEvidence v1 to conversion-dependent accounting; never choose/synthesize a path or fetch a rate. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/simulator/README.md` |
| `FR-SIM-014` | Simulation | append one event with the next monotonic sequence and hash-chain link before the corresponding governed state transition is considered durable. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/simulator/README.md` |
| `FR-SIM-016` | Simulation | validate schema, sequence, hash chain, config/data/engine identities, and invariants while reconstructing state through an injected determin... | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/simulator/README.md` |
| `FR-SIM-018` | Simulation | derive an executable bid/ask price from the current tick and approved spread/slippage model without using future ticks. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/simulator/README.md` |
| `FR-SIM-019` | Simulation | deterministically match supported FX market and pending intents using configured trigger, gap, liquidity, FOK/IOC, and same-tick priority ru... | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/simulator/README.md` |
| `FR-SIM-020` | Simulation | process one canonical tick at a time, enforce timing and state transitions, apply fills through the ledger, append journal events, and retur... | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/simulator/README.md` |
| `FR-SIM-021` | Simulation | accept only a Trading-owned OrderIntent for route sim, preserve its final approved volume, and submit it to the active simulation engine wit... | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/simulator/README.md` |
| `FR-SIM-022` | Simulation | close an existing simulated position by approved quantity using the current canonical tick and journal the resulting fill. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/simulator/README.md` |
| `FR-SIM-023` | Simulation | expose immutable read-only orders, positions, pending orders, deals, and account state for the current run without leaking mutable engine ob... | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/simulator/README.md` |
| `FR-SIM-024` | Simulation | expose SimulationResult v1 with separate compatibility/schema identity, reproducibility identities, completed status, fills/journal/artifact... | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/simulator/README.md` |
| `FR-SIM-025` | Simulation | expose a versioned manifest entry for every canonical artifact with relative path, media type, size, SHA-256 checksum, schema version, and c... | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/simulator/README.md` |
| `FR-SIM-026` | Simulation | read completed canonical artifacts, verify containment and size, calculate checksums, and return a stable manifest without publishing tempor... | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/simulator/README.md` |
| `FR-SIM-027` | Simulation | serialize a SimulationResult to deterministic canonical JSON with execution/accounting diagnostics and realism/data-quality disclosures, exc... | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/simulator/README.md` |
| `FR-SIM-028` | Simulation | render a deterministic Markdown execution report with assumptions, limitations, costs, fills, rejections, data quality, and artifact identit... | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/simulator/README.md` |
| `FR-SIM-029` | Simulation | expose the exact docs/PROJECT.md 5 request for one synchronous bounded FX run, with separate contract version/schema ID, immutable Strateg... | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/simulator/README.md` |
| `FR-SIM-030` | Simulation | authenticate, deduplicate, validate, execute, journal, report, persist, and return one deterministic canonical FX run, never publishing a pa... | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/simulator/README.md` |
| `FR-SIM-031` | Simulation | run an explicitly requested approximation only when enabled, mark every output canonical=false, disclose assumptions, and prohibit canonical... | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/simulator/README.md` |
| `P-SIM-001` | Simulation | validation feature/component (provisional) | T0 Skeleton | M | `P-SYS-001` | 1 | `app/services/simulator/README.md` |
| `P-SIM-005` | Simulation | execution feature/component (provisional) | T0 Skeleton | M | `P-SYS-001` | 1 | `app/services/simulator/README.md` |
| `P-SIM-006` | Simulation | reporting feature/component (provisional) | T0 Skeleton | M | `P-SYS-001` | 1 | `app/services/simulator/README.md` |
| `P-SIM-007` | Simulation | run feature/component (provisional) | T0 Skeleton | M | `P-SYS-001` | 1 | `app/services/simulator/README.md` |
| `WF-SIM-001` | Simulation | Official FX Backtest | T0 Skeleton | M | `P-SYS-001` | 1 | `app/services/simulator/README.md` |
| `WF-SIM-002` | Simulation | Simulation Trader Operations | T0 Skeleton | M | `P-SYS-001` | 1 | `app/services/simulator/README.md` |
| `CAP-SIM-009` | Simulation | Data authority and quality gate | T1 Core | M | `P-SYS-001` | 2 | `app/services/simulator/README.md` |
| `CAP-SIM-010` | Simulation | Strategy and Indicator boundary | T1 Core | M | `P-SYS-001` | 3 | `app/services/simulator/README.md` |
| `WF-SIM-006` | Simulation | Registered-Strategy Security Rejection | T1 Core | M | `P-SYS-001` | 3 | `app/services/simulator/README.md` |
| `CAP-SIM-006` | Simulation | Sizing application, accounting, costs, margin, FX | T1 Core | M | `P-SYS-001` | 4 | `app/services/simulator/README.md` |
| `CAP-SIM-005` | Simulation | Simulated Trader and authoritative state | T1 Core | M | `P-SYS-001` | 5 | `app/services/simulator/README.md` |
| `CAP-SIM-007` | Simulation | Journal, replay, persistence, idempotency | T1 Core | M | `P-SYS-001` | 6 | `app/services/simulator/README.md` |
| `FR-SIM-004` | Simulation | expose an immutable UTC tick containing symbol, timestamp, bid, ask, source identity, sequence, and availability metadata with finite positi... | T1 Core | S | `P-SYS-001` | 6 | `app/services/simulator/README.md` |
| `FR-SIM-007` | Simulation | verify that the final approved volume is finite, positive, and within symbol min/max/step constraints without increasing, decreasing, or oth... | T1 Core | S | `P-SYS-001` | 6 | `app/services/simulator/README.md` |
| `FR-SIM-008` | Simulation | calculate configured Phase 1 commission and swap deterministically and return an itemized fixed-precision cost mapping. | T1 Core | S | `P-SYS-001` | 6 | `app/services/simulator/README.md` |
| `FR-SIM-009` | Simulation | calculate required FX margin from approved symbol evidence, price, volume, and leverage, rejecting insufficient free margin before a fill. | T1 Core | S | `P-SYS-001` | 6 | `app/services/simulator/README.md` |
| `FR-SIM-011` | Simulation | atomically apply a simulated fill, realized PnL, commission, swap, and margin effect while preserving balance/equity/free-margin invariants ... | T1 Core | S | `P-SYS-001` | 6 | `app/services/simulator/README.md` |
| `FR-SIM-012` | Simulation | return an immutable read-only fixed-precision account snapshot without exposing mutable engine state. | T1 Core | S | `P-SYS-001` | 6 | `app/services/simulator/README.md` |
| `FR-SIM-013` | Simulation | expose an immutable versioned journal event containing run, sequence, UTC time, event type, redacted payload, previous hash, event hash, cor... | T1 Core | S | `P-SYS-001` | 6 | `app/services/simulator/README.md` |
| `FR-SIM-015` | Simulation | finalize a completed journal atomically and return its checksum without publishing incomplete temporary artifacts. | T1 Core | S | `P-SYS-001` | 6 | `app/services/simulator/README.md` |
| `FR-SIM-017` | Simulation | return the existing completed run for the same request ID and hash, and reject the same request ID with a different hash. | T1 Core | S | `P-SYS-001` | 6 | `app/services/simulator/README.md` |
| `P-SIM-002` | Simulation | timeline feature/component (provisional) | T1 Core | M | `P-SYS-001` | 6 | `app/services/simulator/README.md` |
| `P-SIM-003` | Simulation | accounting feature/component (provisional) | T1 Core | M | `P-SYS-001` | 6 | `app/services/simulator/README.md` |
| `P-SIM-004` | Simulation | journal feature/component (provisional) | T1 Core | M | `P-SYS-001` | 6 | `app/services/simulator/README.md` |
| `WF-SIM-004` | Simulation | Severe Data-Quality Block | T1 Core | M | `P-SYS-001` | 6 | `app/services/simulator/README.md` |
| `WF-SIM-005` | Simulation | Deterministic Replay | T1 Core | M | `P-SYS-001` | 6 | `app/services/simulator/README.md` |
| `CAP-SIM-008` | Simulation | Results, artifacts, Analytics boundary | T2 Advanced | M | `P-SYS-001` | 7 | `app/services/simulator/README.md` |
| `CAP-SIM-012` | Simulation | Explicit fast-research mode | T2 Advanced | M | `P-SYS-001` | 8 | `app/services/simulator/README.md` |
| `CAP-SIM-013` | Simulation | Optimization/robustness execution boundary | T2 Advanced | M | `P-SYS-001` | 8 | `app/services/simulator/README.md` |
| `WF-SIM-003` | Simulation | Optimization Candidate Execution | T2 Advanced | M | `P-SYS-001` | 8 | `app/services/simulator/README.md` |
| `WF-SIM-009` | Simulation | Portfolio Backtest | T2 Advanced | M | `P-SYS-001` | 9 | `app/services/simulator/README.md` |
| `WF-SIM-007` | Simulation | Non-Canonical Fast Research | T2 Advanced | M | `P-SYS-001` | 10 | `app/services/simulator/README.md` |
| `NFR-SIM-001` | Simulation | Determinism | T3 Complete | S | `P-SYS-001` | 12 | `app/services/simulator/README.md` |
| `NFR-SIM-002` | Simulation | Precision | T3 Complete | S | `P-SYS-001` | 12 | `app/services/simulator/README.md` |
| `NFR-SIM-003` | Simulation | No lookahead | T3 Complete | S | `P-SYS-001` | 12 | `app/services/simulator/README.md` |
| `NFR-SIM-004` | Simulation | Safety | T3 Complete | S | `P-SYS-001` | 12 | `app/services/simulator/README.md` |
| `NFR-SIM-005` | Simulation | API boundary | T3 Complete | S | `P-SYS-001` | 12 | `app/services/simulator/README.md` |
| `NFR-SIM-006` | Simulation | Security | T3 Complete | S | `P-SYS-001` | 12 | `app/services/simulator/README.md` |
| `NFR-SIM-007` | Simulation | Reliability | T3 Complete | S | `P-SYS-001` | 12 | `app/services/simulator/README.md` |
| `NFR-SIM-008` | Simulation | Auditability | T3 Complete | S | `P-SYS-001` | 12 | `app/services/simulator/README.md` |
| `NFR-SIM-009` | Simulation | Maintainability | T3 Complete | S | `P-SYS-001` | 12 | `app/services/simulator/README.md` |
| `NFR-SIM-010` | Simulation | Testing | T3 Complete | S | `P-SYS-001` | 12 | `app/services/simulator/README.md` |
| `NFR-SIM-011` | Simulation | Performance | T3 Complete | S | `P-SYS-001` | 12 | `app/services/simulator/README.md` |
| `NFR-SIM-012` | Simulation | Compatibility | T3 Complete | S | `P-SYS-001` | 12 | `app/services/simulator/README.md` |
| `CAP-SIM-002` | Simulation | Validation, orchestration, and lifecycle | T3 Complete | M | `P-SYS-001` | 13 | `app/services/simulator/README.md` |
| `CAP-SIM-003` | Simulation | Signal timing, tick construction, no-lookahead | T3 Complete | M | `P-SYS-001` | 13 | `app/services/simulator/README.md` |
| `CAP-SIM-011` | Simulation | Determinism, precision, reliability, security | T3 Complete | M | `P-SYS-001` | 13 | `app/services/simulator/README.md` |
| `FR-ANLT-001` | Analytics | expose one base exception for direct Analytics feature APIs. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/analytics/README.md` |
| `FR-ANLT-002` | Analytics | distinguish invalid, missing, incompatible, or unsafe analytics evidence from execution failures. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/analytics/README.md` |
| `FR-ANLT-003` | Analytics | convert a controlled exception into a bounded, redacted error payload without exposing provider exceptions or secrets. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/analytics/README.md` |
| `FR-ANLT-004` | Analytics | represent an adapted upstream result with source version, IDs, phase, UTC window, currency, strategy, symbols, timeframe, trades, curves, be... | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/analytics/README.md` |
| `FR-ANLT-005` | Analytics | represent one metric as a finite calculated/undefined/skipped value with unit, confidence, warnings, and source context. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/analytics/README.md` |
| `FR-ANLT-006` | Analytics | represent one report section with approved criticality, ordered metrics, status, warnings, and failure/skipped reason. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/analytics/README.md` |
| `FR-ANLT-007` | Analytics | represent a bounded warning with code, severity, affected section, source context, and detail. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/analytics/README.md` |
| `FR-ANLT-008` | Analytics | represent a quality flag separately from metrics and governance decisions, including blocker semantics and source evidence. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/analytics/README.md` |
| `FR-ANLT-009` | Analytics | preserve bounded source IDs, versions, configuration sources, inherited currency, and transformation history. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/analytics/README.md` |
| `FR-ANLT-010` | Analytics | hold SHA-256 hashes for input, configuration, trade ledger, equity curve, optional benchmark, and final report evidence. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/analytics/README.md` |
| `FR-ANLT-011` | Analytics | expose the owned PerformanceReport v1 cross-domain contract with ordered sections, caveats, lineage, hashes, precision metadata, and non_bin... | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/analytics/README.md` |
| `FR-ANLT-012` | Analytics | represent real portfolio aggregation with component lineage, base currency, FX evidence, blocker flags, and no fabricated aggregate values. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/analytics/README.md` |
| `FR-ANLT-013` | Analytics | represent versioned finite chart/table payloads, section statuses, warnings, units, and truncation metadata without UI rendering logic. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/analytics/README.md` |
| `FR-ANLT-014` | Analytics | represent report-derived facts, score inputs, warnings, and recommendation context while explicitly excluding governance authority. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/analytics/README.md` |
| `FR-ANLT-016` | Analytics | expose an authoritative definition for every metric used by a report, dashboard, warning, or quality flag. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/analytics/README.md` |
| `FR-ANLT-017` | Analytics | expose deterministic, separately namespaced warning and quality-flag definitions with bounded details, source-backed status, and blocker mea... | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/analytics/README.md` |
| `FR-ANLT-018` | Analytics | classify accepted, deprecated, legacy-adapted, unsupported, and future source/report contract versions independently of schema_id. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/analytics/README.md` |
| `FR-ANLT-020` | Analytics | reject a metric catalog lacking formula, unit, inputs, scale, annualization, sample convention, minimum sample, undefined behavior, evidence... | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/analytics/README.md` |
| `FR-ANLT-021` | Analytics | classify contract_version and reject missing, unsupported, or unsafe future compatibility versions before calculation; schema_id is validate... | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/analytics/README.md` |
| `FR-ANLT-022` | Analytics | build a catalog-backed warning with deterministic ordering and bounded redacted detail. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/analytics/README.md` |
| `FR-ANLT-023` | Analytics | build a catalog-backed quality flag that separates evidence from final governance decisions. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/analytics/README.md` |
| `FR-ANLT-025` | Analytics | convert supported contracts, Decimal, datetime, pandas, and NumPy values to finite JSON-safe values and reject unsupported/non-finite values. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/analytics/README.md` |
| `FR-ANLT-027` | Analytics | deterministically map an approved versioned Trading or Simulation result to TradingResult, preserving IDs, phase, UTC window, currency, stra... | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/analytics/README.md` |
| `FR-ANLT-028` | Analytics | calculate closed-trade outcomes, explicit-direction splits, cataloged R-multiples, merged-overlap market presence, streaks, and source conte... | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/analytics/README.md` |
| `FR-ANLT-033` | Analytics | normalize strategy/benchmark timestamps to UTC, restrict the comparison window, resolve duplicates under approved policy, and return determi... | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/analytics/README.md` |
| `FR-ANLT-034` | Analytics | calculate approved benchmark-relative evidence only after alignment and currency checks; non-overlap or zero variance is explicit skipped/un... | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/analytics/README.md` |
| `FR-ANLT-036` | Analytics | compute real, bounded, seeded bootstrap, permutation, multiple-comparison, and sample diagnostics reproducibly and shall not return fixed pl... | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/analytics/README.md` |
| `FR-ANLT-038` | Analytics | execute approved metric groups in deterministic order and preserve all/long/short/benchmark/cost/statistical source context without exportin... | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/analytics/README.md` |
| `FR-ANLT-039` | Analytics | compute deterministic SHA-256 input, config, ledger, equity, optional benchmark, and report hashes from canonical JSON while excluding docum... | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/analytics/README.md` |
| `FR-ANLT-040` | Analytics | serialize a validated report as canonical JSON or one minimal approved human-readable representation without file writes or placeholder form... | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/analytics/README.md` |
| `FR-ANLT-041` | Analytics | aggregate actual compatible component evidence only after schema, base-currency, and caller-supplied FX validation; missing conversion block... | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/analytics/README.md` |
| `FR-ANLT-042` | Analytics | compare schema- and pairing-compatible reports using actual common cataloged metrics, preserving omissions and caveats without mutating eith... | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/analytics/README.md` |
| `FR-ANLT-043` | Analytics | build PerformanceReport v1 from approved source evidence, required and optional cataloged sections, deterministic warnings/flags, lineage, p... | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/analytics/README.md` |
| `FR-ANLT-044` | Analytics | evaluate canonical report facts under owner-approved thresholds, surface sample/drawdown/overfit/profitability caveats, and return non-bindi... | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/analytics/README.md` |
| `FR-ANLT-045` | Analytics | deterministically bound a series without exceeding the approved limit, preserving endpoints and approved extrema/trough/high/warning points ... | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/analytics/README.md` |
| `FR-ANLT-046` | Analytics | project only approved PerformanceReport sections into finite versioned summary, equity, drawdown, warning, and quality-flag payloads with un... | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/analytics/README.md` |
| `P-ANLT-001` | Analytics | contracts feature/component (provisional) | T0 Skeleton | M | `P-SYS-001` | 1 | `app/services/analytics/README.md` |
| `P-ANLT-002` | Analytics | adapters feature/component (provisional) | T0 Skeleton | M | `P-SYS-001` | 1 | `app/services/analytics/README.md` |
| `P-ANLT-004` | Analytics | reports feature/component (provisional) | T0 Skeleton | M | `P-SYS-001` | 1 | `app/services/analytics/README.md` |
| `P-ANLT-006` | Analytics | dashboards feature/component (provisional) | T0 Skeleton | M | `P-SYS-001` | 1 | `app/services/analytics/README.md` |
| `WF-ANLT-001` | Analytics | Build Canonical Performance Report | T0 Skeleton | M | `P-SYS-001` | 1 | `app/services/analytics/README.md` |
| `WF-ANLT-005` | Analytics | Build Dashboard Payload | T0 Skeleton | M | `P-SYS-001` | 1 | `app/services/analytics/README.md` |
| `WF-ANLT-006` | Analytics | Adapt Upstream Result | T0 Skeleton | M | `P-SYS-001` | 1 | `app/services/analytics/README.md` |
| `FR-ANLT-029` | Analytics | calculate monetary PnL in Decimal and deterministic sorted equity/return evidence with explicit frequency, scale, UTC, and undefined behavior. | T2 Advanced | S | `P-SYS-001` | 7 | `app/services/analytics/README.md` |
| `FR-ANLT-030` | Analytics | calculate core drawdown depth, duration, recovery, ulcer, and pain evidence from approved curves while returning undefined ratios as None wi... | T2 Advanced | S | `P-SYS-001` | 7 | `app/services/analytics/README.md` |
| `FR-ANLT-031` | Analytics | calculate only approved volatility, VaR, CVaR, and expected-shortfall evidence with cataloged sign, confidence, sample, and units. | T2 Advanced | S | `P-SYS-001` | 7 | `app/services/analytics/README.md` |
| `FR-ANLT-032` | Analytics | calculate only approved core ratios and return zero-denominator/insufficient-sample results as None with warnings. | T2 Advanced | S | `P-SYS-001` | 7 | `app/services/analytics/README.md` |
| `FR-ANLT-035` | Analytics | use one cataloged implementation for approved moments, percentiles, tails, histogram, and outlier evidence, with constant/short samples hand... | T2 Advanced | S | `P-SYS-001` | 7 | `app/services/analytics/README.md` |
| `FR-ANLT-037` | Analytics | calculate supplied cost drag, duration, MAE/MFE, and selected efficiency evidence with documented sign conventions and no source mutation. | T2 Advanced | S | `P-SYS-001` | 7 | `app/services/analytics/README.md` |
| `P-ANLT-003` | Analytics | metrics feature/component (provisional) | T2 Advanced | M | `P-SYS-001` | 7 | `app/services/analytics/README.md` |
| `P-ANLT-005` | Analytics | scorecards feature/component (provisional) | T2 Advanced | M | `P-SYS-001` | 7 | `app/services/analytics/README.md` |
| `WF-ANLT-002` | Analytics | Calculate Grouped Analytics Evidence | T2 Advanced | M | `P-SYS-001` | 7 | `app/services/analytics/README.md` |
| `WF-ANLT-003` | Analytics | Benchmark-Relative Analysis | T2 Advanced | M | `P-SYS-001` | 7 | `app/services/analytics/README.md` |
| `WF-ANLT-004` | Analytics | Evaluate Strategy Quality | T2 Advanced | M | `P-SYS-001` | 7 | `app/services/analytics/README.md` |
| `WF-ANLT-007` | Analytics | Run Statistical Validation | T2 Advanced | M | `P-SYS-001` | 7 | `app/services/analytics/README.md` |
| `WF-ANLT-008` | Analytics | Serialize and Hash Report | T2 Advanced | M | `P-SYS-001` | 7 | `app/services/analytics/README.md` |
| `WF-ANLT-010` | Analytics | Compare Performance Reports | T2 Advanced | M | `P-SYS-001` | 7 | `app/services/analytics/README.md` |
| `WF-ANLT-009` | Analytics | Build Portfolio Performance Report | T2 Advanced | M | `P-SYS-001` | 9 | `app/services/analytics/README.md` |
| `WF-ANLT-013` | Analytics | Build Portfolio Allocation Evidence | T2 Advanced | M | `P-SYS-001` | 9 | `app/services/analytics/README.md` |
| `NFR-ANLT-001` | Analytics | API boundary | T3 Complete | S | `P-SYS-001` | 12 | `app/services/analytics/README.md` |
| `NFR-ANLT-002` | Analytics | Safety | T3 Complete | S | `P-SYS-001` | 12 | `app/services/analytics/README.md` |
| `NFR-ANLT-003` | Analytics | Determinism | T3 Complete | S | `P-SYS-001` | 12 | `app/services/analytics/README.md` |
| `NFR-ANLT-004` | Analytics | Serialization | T3 Complete | S | `P-SYS-001` | 12 | `app/services/analytics/README.md` |
| `NFR-ANLT-005` | Analytics | Precision | T3 Complete | S | `P-SYS-001` | 12 | `app/services/analytics/README.md` |
| `NFR-ANLT-006` | Analytics | Security | T3 Complete | S | `P-SYS-001` | 12 | `app/services/analytics/README.md` |
| `NFR-ANLT-007` | Analytics | Reliability | T3 Complete | S | `P-SYS-001` | 12 | `app/services/analytics/README.md` |
| `NFR-ANLT-008` | Analytics | Performance | T3 Complete | S | `P-SYS-001` | 12 | `app/services/analytics/README.md` |
| `NFR-ANLT-009` | Analytics | Observability | T3 Complete | S | `P-SYS-001` | 12 | `app/services/analytics/README.md` |
| `NFR-ANLT-010` | Analytics | Compatibility | T3 Complete | S | `P-SYS-001` | 12 | `app/services/analytics/README.md` |
| `NFR-ANLT-011` | Analytics | Testing | T3 Complete | S | `P-SYS-001` | 12 | `app/services/analytics/README.md` |
| `NFR-ANLT-012` | Analytics | Dependencies | T3 Complete | S | `P-SYS-001` | 12 | `app/services/analytics/README.md` |
| `NFR-ANLT-013` | Analytics | Coverage | T3 Complete | S | `P-SYS-001` | 12 | `app/services/analytics/README.md` |
| `FR-ANLT-024` | Analytics | Negative requirement: Analytics defines no local redaction primitive and uses Utils. | T3 Complete | S | `P-SYS-001` | 13 | `app/services/analytics/README.md` |
| `FR-ANLT-026` | Analytics | Negative requirement: Analytics defines no local canonical serializer and uses Utils. | T3 Complete | S | `P-SYS-001` | 13 | `app/services/analytics/README.md` |
| `FR-OPT-001` | Optimization | model one float, integer, categorical, boolean, fixed, or conditional parameter with validated bounds, step/options, and activation condition. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/optimization/README.md` |
| `FR-OPT-002` | Optimization | model a uniquely named collection of parameter ranges and constraints without accepting an empty or duplicate definition. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/optimization/README.md` |
| `FR-OPT-003` | Optimization | validate parameter types, conditional cycles, constraints, expansion bounds, and configured limits before candidate generation. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/optimization/README.md` |
| `FR-OPT-004` | Optimization | evaluate only allowlisted expression nodes and names, returning false for a valid violated constraint and blocking unsafe expressions. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/optimization/README.md` |
| `FR-OPT-005` | Optimization | exclude inactive conditional parameters from execution while retaining the original definition for metadata and audit evidence. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/optimization/README.md` |
| `FR-OPT-006` | Optimization | compute an order-invariant SHA-256 parameter-space hash from canonical definitions and constraints using normalized decimals. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/optimization/README.md` |
| `FR-OPT-007` | Optimization | compute the candidate source-of-truth hash from strategy/data/cost/realism/objective/engine/module/space provenance and executable parameter... | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/optimization/README.md` |
| `FR-OPT-010` | Optimization | calculate the selected enabled core objective from validated outcomes and return explicit unavailable evidence when inputs are insufficient. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/optimization/README.md` |
| `FR-OPT-011` | Optimization | calculate Deflated Sharpe evidence only from validated Sharpe, sample moments, sample count, and nominal-trial evidence. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/optimization/README.md` |
| `FR-OPT-012` | Optimization | count unique executable candidate hashes after constraint rejection and deduplication and label the count nominal rather than independent. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/optimization/README.md` |
| `FR-OPT-013` | Optimization | rank candidates by score descending, present trade count descending, then candidate hash ascending without mutating input records. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/optimization/README.md` |
| `FR-OPT-015` | Optimization | assess IS/OOS degradation, DSR availability, nominal-trial caveats, trade-count adequacy, and cost/MC evidence; PBO and topology gates are n... | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/optimization/README.md` |
| `FR-OPT-016` | Optimization | expose a domain exception carrying a deterministic OPT_* code and redacted details for internal execution failures. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/optimization/README.md` |
| `FR-OPT-017` | Optimization | define a versioned protocol implemented by Simulation and accepting only an optimization execution request. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/optimization/README.md` |
| `FR-OPT-018` | Optimization | model one executable candidate with approved strategy reference, MarketDataset reference/provenance, executable parameters, seed, costs, rea... | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/optimization/README.md` |
| `FR-OPT-019` | Optimization | expose an optimization-facing immutable result converted from SimulationResult without leaking simulator internals. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/optimization/README.md` |
| `FR-OPT-020` | Optimization | validate adapter version, engine type, deterministic seed, cost/realism evidence, strategy compatibility, and required data before invoking ... | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/optimization/README.md` |
| `FR-OPT-021` | Optimization | support only grid and random search. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/optimization/README.md` |
| `FR-OPT-022` | Optimization | model a bounded search with strategy/data provenance, parameter space, objective, method, seed, and approved resource caps. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/optimization/README.md` |
| `FR-OPT-023` | Optimization | represent one accepted, rejected, or failed candidate with executable parameters, hash, score/evidence, and structured reason. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/optimization/README.md` |
| `FR-OPT-024` | Optimization | represent a completed bounded search with deterministic candidate order, best candidate, runtime, objective, method, provenance, and warnings. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/optimization/README.md` |
| `FR-OPT-025` | Optimization | lazily yield valid grid candidates without materializing the full Cartesian product and shall stop before exceeding the configured cap. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/optimization/README.md` |
| `FR-OPT-026` | Optimization | generate unique pseudo-random candidates deterministically from validated ranges and a required seed, without claiming Sobol or LHS behavior. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/optimization/README.md` |
| `FR-OPT-027` | Optimization | evaluate each unique valid candidate through the injected adapter, retain structured failures, score successful results, and return determin... | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/optimization/README.md` |
| `FR-OPT-028` | Optimization | return the first N candidates from an already deterministic summary without dataframe conversion or input mutation. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/optimization/README.md` |
| `FR-OPT-032` | Optimization | represent fold results, selected parameters, train/OOS scores, degradation, pass rate, drift, retention, WFE, and leakage evidence. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/optimization/README.md` |
| `FR-OPT-033` | Optimization | construct deterministic folds in chronological order, enforce purge/embargo, and reject insufficient or invalid ranges. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/optimization/README.md` |
| `FR-OPT-038` | Optimization | model explicit spread, slippage, commission, or skip-trade stress without hidden unit conversion. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/optimization/README.md` |
| `FR-OPT-039` | Optimization | run the selected core Monte Carlo method with deterministic run/candidate/phase sub-seeds and within the approved cap. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/optimization/README.md` |
| `FR-OPT-040` | Optimization | calculate the fraction of supplied drawdowns or equity paths that cross an explicit ruin threshold. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/optimization/README.md` |
| `FR-OPT-042` | Optimization | simulate compounding outcomes from validated win rate, reward/risk, risk per trade, trade count, path count, balance, and seed without claim... | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/optimization/README.md` |
| `FR-OPT-043` | Optimization | return copied stressed outcomes for an explicit execution-cost or skip-trade assumption without mutating inputs. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/optimization/README.md` |
| `FR-OPT-044` | Optimization | combine only supplied/applicable MC and stress checks into a robustness percentage, warnings, and evidence-availability summary. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/optimization/README.md` |
| `FR-OPT-045` | Optimization | use only ready_for_risk_review, validation_needed, research_only, rejected, or failed as synchronous final decisions; no background-job canc... | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/optimization/README.md` |
| `FR-OPT-046` | Optimization | model the supplied search, WFA, MC, robustness, warnings, audit references, chart data, and optional externally owned evidence needed for as... | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/optimization/README.md` |
| `FR-OPT-047` | Optimization | define advisory OptimizationResult v1 with separate compatibility/schema identity, search ID, reproducibility hash, ranked candidates, diagn... | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/optimization/README.md` |
| `FR-OPT-048` | Optimization | assemble versioned baseline evidence and reproducibility hash from supplied results without recomputing metrics or external decisions. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/optimization/README.md` |
| `FR-OPT-049` | Optimization | package chart-ready series and tables from OptimizationResult without rendering or recomputation. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/optimization/README.md` |
| `FR-OPT-053` | Optimization | atomically persist one canonical OptimizationResult v1 with its ranked-candidate evidence before reporting durable success. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/optimization/README.md` |
| `P-OPT-001` | Optimization | parameters feature/component (provisional) | T0 Skeleton | M | `P-SYS-001` | 1 | `app/services/optimization/README.md` |
| `P-OPT-003` | Optimization | execution feature/component (provisional) | T0 Skeleton | M | `P-SYS-001` | 1 | `app/services/optimization/README.md` |
| `P-OPT-004` | Optimization | search feature/component (provisional) | T0 Skeleton | M | `P-SYS-001` | 1 | `app/services/optimization/README.md` |
| `P-OPT-007` | Optimization | evidence feature/component (provisional) | T0 Skeleton | M | `P-SYS-001` | 1 | `app/services/optimization/README.md` |
| `P-OPT-009` | Optimization | public_api feature/component (provisional) | T0 Skeleton | M | `P-SYS-001` | 1 | `app/services/optimization/README.md` |
| `WF-OPT-001` | Optimization | Package an Optimization or Robustness Request | T0 Skeleton | M | `P-SYS-001` | 1 | `app/services/optimization/README.md` |
| `WF-OPT-002` | Optimization | Execute a Bounded Parameter Sweep | T0 Skeleton | M | `P-SYS-001` | 1 | `app/services/optimization/README.md` |
| `FR-OPT-008` | Optimization | enumerate the approved calculation names total_return, profit_factor, sharpe, sortino, and calmar; production enablement remains controlled ... | T2 Advanced | S | `P-SYS-001` | 8 | `app/services/optimization/README.md` |
| `FR-OPT-009` | Optimization | represent a candidate score with availability, raw value, objective, trade count, metric evidence, and caveats without substituting another ... | T2 Advanced | S | `P-SYS-001` | 8 | `app/services/optimization/README.md` |
| `FR-OPT-014` | Optimization | return a deterministic non-dominated candidate set for explicitly supplied objectives without choosing an unapproved knee point. | T2 Advanced | S | `P-SYS-001` | 8 | `app/services/optimization/README.md` |
| `FR-OPT-029` | Optimization | support rolling, anchored, and expanding modes; anchored and expanding have equivalent growing-train semantics. | T2 Advanced | S | `P-SYS-001` | 8 | `app/services/optimization/README.md` |
| `FR-OPT-030` | Optimization | represent one UTC train/test fold with explicit purge, embargo, and leakage-prevention evidence. | T2 Advanced | S | `P-SYS-001` | 8 | `app/services/optimization/README.md` |
| `FR-OPT-031` | Optimization | model one WFA request with a bounded search, mode, windows, purge/embargo, optional average trade duration, and minimum fold count. | T2 Advanced | S | `P-SYS-001` | 8 | `app/services/optimization/README.md` |
| `FR-OPT-034` | Optimization | optimize each train fold, evaluate the selected candidate OOS through Simulation, and aggregate evidence without replacing failures with zero. | T2 Advanced | S | `P-SYS-001` | 8 | `app/services/optimization/README.md` |
| `FR-OPT-035` | Optimization | support shuffle_trades, resample_returns, and block_bootstrap Monte Carlo methods in the initial implementation. | T2 Advanced | S | `P-SYS-001` | 8 | `app/services/optimization/README.md` |
| `FR-OPT-036` | Optimization | model bounded Monte Carlo inputs with supplied outcomes, balance, method, simulations, seed, block size, and optional thresholds. | T2 Advanced | S | `P-SYS-001` | 8 | `app/services/optimization/README.md` |
| `FR-OPT-037` | Optimization | represent reproducible path summaries, equity/drawdown percentiles, ruin probability, streak/return evidence, seed provenance, and caveats. | T2 Advanced | S | `P-SYS-001` | 8 | `app/services/optimization/README.md` |
| `FR-OPT-041` | Optimization | calculate deterministic empirical confidence intervals for validated finite metric samples at a caller-supplied confidence level. | T2 Advanced | S | `P-SYS-001` | 8 | `app/services/optimization/README.md` |
| `FR-OPT-050` | Optimization | define an injected store port limited to Optimization-owned checkpoint/result reads and atomic writes. | T2 Advanced | S | `P-SYS-001` | 8 | `app/services/optimization/README.md` |
| `FR-OPT-051` | Optimization | define immutable checkpoint evidence with schema version, search ID, reproducibility hash, completed-candidate position, deterministic RNG s... | T2 Advanced | S | `P-SYS-001` | 8 | `app/services/optimization/README.md` |
| `FR-OPT-052` | Optimization | atomically save each completed-candidate checkpoint and recover only an exact schema/search/reproducibility match. | T2 Advanced | S | `P-SYS-001` | 8 | `app/services/optimization/README.md` |
| `FR-OPT-054` | Optimization | build artifact locations only beneath the approved result/checkpoint roots from validated search and reproducibility identifiers. | T2 Advanced | S | `P-SYS-001` | 8 | `app/services/optimization/README.md` |
| `FR-OPT-055` | Optimization | expose ordered additive Optimization migration definitions for optimization_results and optimization_checkpoints without opening a database. | T2 Advanced | S | `P-SYS-001` | 8 | `app/services/optimization/README.md` |
| `P-OPT-002` | Optimization | scoring feature/component (provisional) | T2 Advanced | M | `P-SYS-001` | 8 | `app/services/optimization/README.md` |
| `P-OPT-005` | Optimization | validation feature/component (provisional) | T2 Advanced | M | `P-SYS-001` | 8 | `app/services/optimization/README.md` |
| `P-OPT-006` | Optimization | robustness feature/component (provisional) | T2 Advanced | M | `P-SYS-001` | 8 | `app/services/optimization/README.md` |
| `P-OPT-008` | Optimization | state feature/component (provisional) | T2 Advanced | M | `P-SYS-001` | 8 | `app/services/optimization/README.md` |
| `WF-OPT-003` | Optimization | Score, Rank, and Assess Overfit Evidence | T2 Advanced | M | `P-SYS-001` | 8 | `app/services/optimization/README.md` |
| `WF-OPT-004` | Optimization | Run Walk-Forward Validation | T2 Advanced | M | `P-SYS-001` | 8 | `app/services/optimization/README.md` |
| `WF-OPT-005` | Optimization | Run Monte Carlo and Robustness Analysis | T2 Advanced | M | `P-SYS-001` | 8 | `app/services/optimization/README.md` |
| `WF-OPT-006` | Optimization | Build Versioned Evidence and Handoffs | T2 Advanced | M | `P-SYS-001` | 8 | `app/services/optimization/README.md` |
| `NFR-OPT-001` | Optimization | Architecture | T3 Complete | S | `P-SYS-001` | 12 | `app/services/optimization/README.md` |
| `NFR-OPT-002` | Optimization | Determinism | T3 Complete | S | `P-SYS-001` | 12 | `app/services/optimization/README.md` |
| `NFR-OPT-003` | Optimization | Safety | T3 Complete | S | `P-SYS-001` | 12 | `app/services/optimization/README.md` |
| `NFR-OPT-004` | Optimization | Reliability | T3 Complete | S | `P-SYS-001` | 12 | `app/services/optimization/README.md` |
| `NFR-OPT-005` | Optimization | Security | T3 Complete | S | `P-SYS-001` | 12 | `app/services/optimization/README.md` |
| `NFR-OPT-006` | Optimization | Serialization | T3 Complete | S | `P-SYS-001` | 12 | `app/services/optimization/README.md` |
| `NFR-OPT-007` | Optimization | Import safety | T3 Complete | S | `P-SYS-001` | 12 | `app/services/optimization/README.md` |
| `NFR-OPT-008` | Optimization | Observability | T3 Complete | S | `P-SYS-001` | 12 | `app/services/optimization/README.md` |
| `NFR-OPT-009` | Optimization | Time | T3 Complete | S | `P-SYS-001` | 12 | `app/services/optimization/README.md` |
| `NFR-OPT-010` | Optimization | Compatibility | T3 Complete | S | `P-SYS-001` | 12 | `app/services/optimization/README.md` |
| `NFR-OPT-011` | Optimization | Persistence truth | T3 Complete | S | `P-SYS-001` | 12 | `app/services/optimization/README.md` |
| `NFR-OPT-012` | Optimization | Testing | T3 Complete | S | `P-SYS-001` | 12 | `app/services/optimization/README.md` |
| `FR-RES-001` | Research | define bounded row, duration, artifact-size, and advisory memory budgets without claiming unverified production performance. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/research/README.md` |
| `FR-RES-002` | Research | require explicit timestamp, duplicate, missing-bar, non-trading-period, and spread-cleaning policies and shall never silently fill or drop d... | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/research/README.md` |
| `FR-RES-003` | Research | define explicit pip, geometry, return-label, and calendar enrichment selections; canonical session tagging remains owned by seasonality/. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/research/README.md` |
| `FR-RES-004` | Research | define feature windows, declared forward columns, warm-up/NaN policy, and non-mutation behavior. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/research/README.md` |
| `FR-RES-005` | Research | define bootstrap, permutation, null, correction, effective-seed, and bounded-iteration settings in one statistical contract. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/research/README.md` |
| `FR-RES-006` | Research | define mean-reversion, trend-persistence, session-study, confirmation, and explicit isolated-failure policy. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/research/README.md` |
| `FR-RES-007` | Research | define one timezone-aware set of named windows and deterministic overlap precedence for all session consumers. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/research/README.md` |
| `FR-RES-008` | Research | define bounded structure detection, canonical scoring, quality, validation, and calibration settings. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/research/README.md` |
| `FR-RES-009` | Research | define selected features, preprocessing, PCA components, cluster count, minimum sample, and effective seed. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/research/README.md` |
| `FR-RES-010` | Research | define an allowed root, format, encoding, overwrite, masking, and atomic-write policy for artifacts. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/research/README.md` |
| `FR-RES-011` | Research | aggregate explicit stage configs, selected stages, and resource limits without supplying hidden trading/data policies. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/research/README.md` |
| `FR-RES-012` | Research | carry prepared records, canonical schema metadata, quality evidence, dataset/config hashes, and provenance without provider objects. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/research/README.md` |
| `FR-RES-013` | Research | distinguish fatal issues, warnings, checks, and explicit cleaning actions with machine-readable codes. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/research/README.md` |
| `FR-RES-014` | Research | identify suspected lookahead columns, severity, evidence, recommendation, allowed forward columns, target, and source metadata. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/research/README.md` |
| `FR-RES-015` | Research | represent deterministic chronological train/validation/test partitions and boundary identities. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/research/README.md` |
| `FR-RES-016` | Research | represent seven-family metric values with units, sample size, undefined-value reason, warnings, and reproducibility metadata. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/research/README.md` |
| `FR-RES-017` | Research | represent one advisory edge study with sample, rule/config, split identity, null evidence, uncertainty, confirmation, seed, warnings, and pr... | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/research/README.md` |
| `FR-RES-018` | Research | represent reproducible swings, legs, distributions, regimes, canonical score, verdict, and advisory fit evidence. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/research/README.md` |
| `FR-RES-019` | Research | represent opt-in stability, robustness, validation, calibration candidates, ranking criteria, windows, duration, and warnings. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/research/README.md` |
| `FR-RES-020` | Research | represent preprocessing, features, dropped columns, scaler, PCA, clusters, factor/cluster evidence, seed, parameters, diagnostics, and advis... | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/research/README.md` |
| `FR-RES-021` | Research | represent deterministic score rows, uncertainty, final score, readiness reasons, versions, and advisory status. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/research/README.md` |
| `FR-RES-022` | Research | normalize approved stage outputs into one versioned snapshot with hashes, versions, warnings, and advisory status. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/research/README.md` |
| `FR-RES-023` | Research | expose bounded structured warnings with code, message, severity, optional field path, and bounded details. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/research/README.md` |
| `FR-RES-024` | Research | produce the fully defined ResearchReport v1 contract in Section 1 with advisory_only=True and complete reproducibility metadata. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/research/README.md` |
| `FR-RES-025` | Research | return a safe artifact reference containing relative location, format, byte size, content hash, atomicity, schema version, and audit identity. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/research/README.md` |
| `FR-RES-026` | Research | expose a unique immutable mapping for every __all__ name with stable classification and lazy import target, without recursive scanning or ca... | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/research/README.md` |
| `FR-RES-027` | Research | validate required columns, UTC/time ordering, duplicates, gaps, OHLC consistency, spread quality, volume, finite values, and source metadata... | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/research/README.md` |
| `FR-RES-028` | Research | clean a copy using only explicit approved strategies and record every action and unresolved warning. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/research/README.md` |
| `FR-RES-029` | Research | enrich a copy with selected pip/geometry/return-label/calendar fields, label forward fields as research-only, and preserve row alignment; se... | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/research/README.md` |
| `FR-RES-030` | Research | execute validate clean revalidate enrich deterministically and return hashes, provenance, and quality evidence, never fetching p... | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/research/README.md` |
| `FR-RES-031` | Research | Compute one-period log returns without mutating input and preserve index alignment. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/research/README.md` |
| `FR-RES-042` | Research | Define the read-only contract implemented by one named metric-family calculator. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/research/README.md` |
| `FR-RES-043` | Research | Compute normalized values for one family from an immutable metric context. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/research/README.md` |
| `FR-RES-044` | Research | Own unique bounded calculator membership without global mutable defaults. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/research/README.md` |
| `FR-RES-045` | Research | Construct an isolated registry from a bounded calculator iterable. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/research/README.md` |
| `FR-RES-046` | Research | Resolve a calculator by exact family name. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/research/README.md` |
| `FR-RES-047` | Research | Return calculators in deterministic registration order without exposing mutable storage. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/research/README.md` |
| `FR-RES-048` | Research | Build a new default registry containing the seven retained metric families. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/research/README.md` |
| `FR-RES-049` | Research | Build a deterministic profile with units, samples, undefined reasons, hashes, warnings, and duration from a prepared dataset. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/research/README.md` |
| `FR-RES-050` | Research | Generate a seeded block-bootstrap statistic distribution and record the effective parameters. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/research/README.md` |
| `FR-RES-069` | Research | Return every configured session active for a timezone-aware hour using canonical overlap precedence. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/research/README.md` |
| `FR-RES-075` | Research | Build swings, directional legs, range/distribution/excursion/regime evidence, canonical score/verdict, warnings, hashes, and advisory fit. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/research/README.md` |
| `FR-RES-077` | Research | Label later bars as trend/reversion/mixed under one approved horizon/truth policy and return insufficiency as structured evidence. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/research/README.md` |
| `FR-RES-081` | Research | Scale selected finite numeric features and return PCA scores, loadings, variance, preprocessing, and diagnostics without mutation. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/research/README.md` |
| `FR-RES-089` | Research | Build deterministic score rows, final score, uncertainty, readiness/reasons, versions, warnings, and advisory status from approved evidence. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/research/README.md` |
| `FR-RES-090` | Research | Build one canonical versioned snapshot from approved stage outputs and reject route-specific/unversioned payloads. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/research/README.md` |
| `FR-RES-091` | Research | Return a concise observation/uncertainty/readiness summary from a canonical snapshot. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/research/README.md` |
| `FR-RES-092` | Research | Return a bounded UI-ready block from a canonical snapshot without presentation-side calculation. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/research/README.md` |
| `FR-RES-093` | Research | Render a canonical report as JSON-compatible data or Markdown with UTC metadata and no persistence side effect. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/research/README.md` |
| `FR-RES-094` | Research | Render a Markdown comparison of two compatible snapshots while exposing schema/config/dataset differences. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/research/README.md` |
| `FR-RES-095` | Research | Render per-symbol and combined advisory summaries in memory while preserving individual failures/warnings; it shall not write files. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/research/README.md` |
| `FR-RES-096` | Research | Execute selected deterministic stage APIs over supplied contracts and return ResearchReport v1 while leaving provider reads, cache, scheduling, database writ... | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/research/README.md` |
| `P-RES-001` | Research | contracts feature/component (provisional) | T0 Skeleton | M | `P-SYS-001` | 1 | `app/services/research/README.md` |
| `P-RES-002` | Research | data feature/component (provisional) | T0 Skeleton | M | `P-SYS-001` | 1 | `app/services/research/README.md` |
| `P-RES-005` | Research | metrics feature/component (provisional) | T0 Skeleton | M | `P-SYS-001` | 1 | `app/services/research/README.md` |
| `P-RES-011` | Research | profiles feature/component (provisional) | T0 Skeleton | M | `P-SYS-001` | 1 | `app/services/research/README.md` |
| `WF-RES-001` | Research | Prepare Research Dataset | T0 Skeleton | M | `P-SYS-001` | 1 | `app/services/research/README.md` |
| `WF-RES-002` | Research | Build Core Metric Profile | T0 Skeleton | M | `P-SYS-001` | 1 | `app/services/research/README.md` |
| `FR-RES-032` | Research | Compute arithmetic returns without mutating input and preserve index alignment. | T2 Advanced | S | `P-SYS-001` | 10 | `app/services/research/README.md` |
| `FR-RES-033` | Research | Estimate Hurst exponent with explicit minimum sample and finite-value validation. | T2 Advanced | S | `P-SYS-001` | 10 | `app/services/research/README.md` |
| `FR-RES-034` | Research | Compute rolling Hurst values with documented warm-up NaNs and stable alignment. | T2 Advanced | S | `P-SYS-001` | 10 | `app/services/research/README.md` |
| `FR-RES-035` | Research | Compute one canonical horizon-aligned forward return in log or simple mode and mark it research-only. | T2 Advanced | S | `P-SYS-001` | 10 | `app/services/research/README.md` |
| `FR-RES-036` | Research | Compute forward maximum favorable excursion for declared side/horizon with trailing unavailability explicit. | T2 Advanced | S | `P-SYS-001` | 10 | `app/services/research/README.md` |
| `FR-RES-037` | Research | Compute forward maximum adverse excursion for declared side/horizon with trailing unavailability explicit. | T2 Advanced | S | `P-SYS-001` | 10 | `app/services/research/README.md` |
| `FR-RES-038` | Research | Build a new feature frame with declared lineage, warm-up/NaN behavior, shared indicator inputs, research-only forward columns, and no input mutation. | T2 Advanced | S | `P-SYS-001` | 10 | `app/services/research/README.md` |
| `FR-RES-039` | Research | Inspect feature metadata, names, targets, horizons, and declarations and return evidence/severity/recommendation without claiming proof of no leakage. | T2 Advanced | S | `P-SYS-001` | 10 | `app/services/research/README.md` |
| `FR-RES-040` | Research | Split chronologically into non-overlapping train/validation/test frames with deterministic boundaries and split hash. | T2 Advanced | S | `P-SYS-001` | 10 | `app/services/research/README.md` |
| `FR-RES-041` | Research | Recursively mask sensitive, broker/account, and forbidden forward fields before sharing or serialization without mutating input. | T2 Advanced | S | `P-SYS-001` | 10 | `app/services/research/README.md` |
| `FR-RES-051` | Research | Compute a block-bootstrap confidence interval from the seeded distribution. | T2 Advanced | S | `P-SYS-001` | 10 | `app/services/research/README.md` |
| `FR-RES-052` | Research | Compute an empirical permutation p-value with declared alternative and seed. | T2 Advanced | S | `P-SYS-001` | 10 | `app/services/research/README.md` |
| `FR-RES-053` | Research | Generate a side- and horizon-matched random-entry null in log-return space. | T2 Advanced | S | `P-SYS-001` | 10 | `app/services/research/README.md` |
| `FR-RES-054` | Research | Generate a seeded null distribution in R-multiple space from declared trade assumptions. | T2 Advanced | S | `P-SYS-001` | 10 | `app/services/research/README.md` |
| `FR-RES-055` | Research | Generate a seeded null by shuffling entries only within the same configured session. | T2 Advanced | S | `P-SYS-001` | 10 | `app/services/research/README.md` |
| `FR-RES-056` | Research | Generate a seeded null by shuffling return blocks while preserving declared block length. | T2 Advanced | S | `P-SYS-001` | 10 | `app/services/research/README.md` |
| `FR-RES-057` | Research | Compute the observed percentile within a finite non-empty null distribution. | T2 Advanced | S | `P-SYS-001` | 10 | `app/services/research/README.md` |
| `FR-RES-058` | Research | Return finite count, location, dispersion, and declared quantiles for a null distribution. | T2 Advanced | S | `P-SYS-001` | 10 | `app/services/research/README.md` |
| `FR-RES-059` | Research | Determine threshold exceedance under an explicit upper/lower/two-sided rule. | T2 Advanced | S | `P-SYS-001` | 10 | `app/services/research/README.md` |
| `FR-RES-060` | Research | Apply Benjamini-Hochberg FDR correction to finite p-values in original order. | T2 Advanced | S | `P-SYS-001` | 10 | `app/services/research/README.md` |
| `FR-RES-061` | Research | Apply Holm-Bonferroni family-wise correction to finite p-values in original order. | T2 Advanced | S | `P-SYS-001` | 10 | `app/services/research/README.md` |
| `FR-RES-062` | Research | Build seeded random-entry, R-space, and shuffled-return baselines with recorded data/split/config identity. | T2 Advanced | S | `P-SYS-001` | 10 | `app/services/research/README.md` |
| `FR-RES-063` | Research | Compare observed evidence to the correctly matched null and return percentile, threshold, p-value, and warnings. | T2 Advanced | S | `P-SYS-001` | 10 | `app/services/research/README.md` |
| `FR-RES-064` | Research | Extract versioned acceptance criteria from baseline evidence without hard-coded direction drift. | T2 Advanced | S | `P-SYS-001` | 10 | `app/services/research/README.md` |
| `FR-RES-065` | Research | Evaluate compression/z-score fade mean reversion on declared split data and return advisory uncertainty evidence. | T2 Advanced | S | `P-SYS-001` | 10 | `app/services/research/README.md` |
| `FR-RES-066` | Research | Evaluate high-volatility breakout follow-through on declared split data and return advisory uncertainty evidence. | T2 Advanced | S | `P-SYS-001` | 10 | `app/services/research/README.md` |
| `FR-RES-067` | Research | Evaluate breakout/fade hypotheses on a frame already tagged by seasonality.tag_sessions and apply multiple-testing correction without redefining session wind... | T2 Advanced | S | `P-SYS-001` | 10 | `app/services/research/README.md` |
| `FR-RES-068` | Research | Classify mean-reversion and trend evidence using one versioned confirmation policy and preserve uncertainty/advisory status. | T2 Advanced | S | `P-SYS-001` | 10 | `app/services/research/README.md` |
| `FR-RES-070` | Research | Return the deterministic primary session label for an hour while preserving overlap evidence. | T2 Advanced | S | `P-SYS-001` | 10 | `app/services/research/README.md` |
| `FR-RES-071` | Research | Return a machine-readable payload of timezone, windows, order, overlaps, and schema version. | T2 Advanced | S | `P-SYS-001` | 10 | `app/services/research/README.md` |
| `FR-RES-072` | Research | Add session labels to a copied timezone-aware frame and record DST/unmatched warnings without changing row order. | T2 Advanced | S | `P-SYS-001` | 10 | `app/services/research/README.md` |
| `FR-RES-073` | Research | Define immutable optional calendar, session, symbol, and hour filters without embedding session definitions. | T2 Advanced | S | `P-SYS-001` | 10 | `app/services/research/README.md` |
| `FR-RES-074` | Research | Compute calendar/session/hour summaries, sparse-bucket warnings, opportunity windows, and extremes from supplied data and filters. | T2 Advanced | S | `P-SYS-001` | 10 | `app/services/research/README.md` |
| `FR-RES-076` | Research | Run bounded temporal stability and parameter robustness only when enabled and record windows, variants, duration, and warnings. | T2 Advanced | S | `P-SYS-001` | 10 | `app/services/research/README.md` |
| `FR-RES-078` | Research | Aggregate prediction evidence by confidence, verdict, symbol, and timeframe with sample counts and warnings. | T2 Advanced | S | `P-SYS-001` | 10 | `app/services/research/README.md` |
| `FR-RES-079` | Research | Build and rank a bounded candidate grid against approved validation truth using the same canonical score, recording parameters, criteria, window, stability, ... | T2 Advanced | S | `P-SYS-001` | 10 | `app/services/research/README.md` |
| `FR-RES-080` | Research | Rank advisory strategy archetypes from profile evidence without mutating or approving Strategy, Risk, or Trading state. | T2 Advanced | S | `P-SYS-001` | 10 | `app/services/research/README.md` |
| `FR-RES-082` | Research | Cluster finite feature rows with deterministic K-Means under the effective seed and return labels/centers/diagnostics. | T2 Advanced | S | `P-SYS-001` | 10 | `app/services/research/README.md` |
| `FR-RES-083` | Research | Attach aligned labels to a copied feature frame without mutating input or changing row order. | T2 Advanced | S | `P-SYS-001` | 10 | `app/services/research/README.md` |
| `FR-RES-084` | Research | Return descriptive finite-value, missingness, duplicate, return, and correlation evidence for investment data. | T2 Advanced | S | `P-SYS-001` | 10 | `app/services/research/README.md` |
| `FR-RES-085` | Research | Extract the largest absolute PCA loadings as interpretable factors with component/feature/sign/magnitude evidence. | T2 Advanced | S | `P-SYS-001` | 10 | `app/services/research/README.md` |
| `FR-RES-086` | Research | Compare clusters using canonical forward returns, sample counts, uncertainty, and semantic advisory names without adapting signals. | T2 Advanced | S | `P-SYS-001` | 10 | `app/services/research/README.md` |
| `FR-RES-087` | Research | Combine descriptive, PCA, cluster, factor, and forward evidence with warnings and diagnostics; omit all signal-adaptation behavior. | T2 Advanced | S | `P-SYS-001` | 10 | `app/services/research/README.md` |
| `FR-RES-088` | Research | Execute the stateless bounded modeling workflow and return complete reproducibility metadata and advisory status. | T2 Advanced | S | `P-SYS-001` | 10 | `app/services/research/README.md` |
| `FR-RES-097` | Research | Mask and render an approved artifact, enforce allowed root/overwrite/encoding/size/atomic policy, write via temporary replacement, emit a redacted audit even... | T2 Advanced | S | `P-SYS-001` | 10 | `app/services/research/README.md` |
| `P-RES-003` | Research | features feature/component (provisional) | T2 Advanced | M | `P-SYS-001` | 10 | `app/services/research/README.md` |
| `P-RES-004` | Research | leakage feature/component (provisional) | T2 Advanced | M | `P-SYS-001` | 10 | `app/services/research/README.md` |
| `P-RES-006` | Research | statistics feature/component (provisional) | T2 Advanced | M | `P-SYS-001` | 10 | `app/services/research/README.md` |
| `P-RES-007` | Research | studies feature/component (provisional) | T2 Advanced | M | `P-SYS-001` | 10 | `app/services/research/README.md` |
| `P-RES-008` | Research | seasonality feature/component (provisional) | T2 Advanced | M | `P-SYS-001` | 10 | `app/services/research/README.md` |
| `P-RES-009` | Research | market_structure feature/component (provisional) | T2 Advanced | M | `P-SYS-001` | 10 | `app/services/research/README.md` |
| `P-RES-010` | Research | modeling feature/component (provisional) | T2 Advanced | M | `P-SYS-001` | 10 | `app/services/research/README.md` |
| `P-RES-012` | Research | artifacts feature/component (provisional) | T2 Advanced | M | `P-SYS-001` | 10 | `app/services/research/README.md` |
| `WF-RES-003` | Research | Build Leakage-Safe Feature Frame and Time Splits | T2 Advanced | M | `P-SYS-001` | 10 | `app/services/research/README.md` |
| `WF-RES-004` | Research | Analyze Session and Seasonality Opportunity | T2 Advanced | M | `P-SYS-001` | 10 | `app/services/research/README.md` |
| `WF-RES-005` | Research | Run Edge Study Against Null Evidence | T2 Advanced | M | `P-SYS-001` | 10 | `app/services/research/README.md` |
| `WF-RES-006` | Research | Build Market-Structure Profile | T2 Advanced | M | `P-SYS-001` | 10 | `app/services/research/README.md` |
| `WF-RES-007` | Research | Forward Validate and Calibrate Market Structure | T2 Advanced | M | `P-SYS-001` | 10 | `app/services/research/README.md` |
| `WF-RES-008` | Research | Run Unsupervised Market-Structure Research | T2 Advanced | M | `P-SYS-001` | 10 | `app/services/research/README.md` |
| `WF-RES-009` | Research | Build Research Scorecard and Profile Snapshot | T2 Advanced | M | `P-SYS-001` | 10 | `app/services/research/README.md` |
| `WF-RES-010` | Research | Render and Persist Research Artifact | T2 Advanced | M | `P-SYS-001` | 10 | `app/services/research/README.md` |
| `WF-RES-011` | Research | Run Complete Edge Lab Profile | T2 Advanced | M | `P-SYS-001` | 10 | `app/services/research/README.md` |
| `NFR-RES-001` | Research | Safety | T3 Complete | S | `P-SYS-001` | 12 | `app/services/research/README.md` |
| `NFR-RES-002` | Research | Reliability | T3 Complete | S | `P-SYS-001` | 12 | `app/services/research/README.md` |
| `NFR-RES-003` | Research | Reproducibility | T3 Complete | S | `P-SYS-001` | 12 | `app/services/research/README.md` |
| `NFR-RES-004` | Research | Leakage | T3 Complete | S | `P-SYS-001` | 12 | `app/services/research/README.md` |
| `NFR-RES-005` | Research | Statistical quality | T3 Complete | S | `P-SYS-001` | 12 | `app/services/research/README.md` |
| `NFR-RES-006` | Research | API boundary | T3 Complete | S | `P-SYS-001` | 12 | `app/services/research/README.md` |
| `NFR-RES-007` | Research | Import safety | T3 Complete | S | `P-SYS-001` | 12 | `app/services/research/README.md` |
| `NFR-RES-008` | Research | Security | T3 Complete | S | `P-SYS-001` | 12 | `app/services/research/README.md` |
| `NFR-RES-009` | Research | Persistence safety | T3 Complete | S | `P-SYS-001` | 12 | `app/services/research/README.md` |
| `NFR-RES-010` | Research | Resource safety | T3 Complete | S | `P-SYS-001` | 12 | `app/services/research/README.md` |
| `NFR-RES-011` | Research | Observability | T3 Complete | S | `P-SYS-001` | 12 | `app/services/research/README.md` |
| `NFR-RES-012` | Research | Platform | T3 Complete | S | `P-SYS-001` | 12 | `app/services/research/README.md` |
| `NFR-RES-013` | Research | Maintainability | T3 Complete | S | `P-SYS-001` | 12 | `app/services/research/README.md` |
| `NFR-RES-014` | Research | Testing | T3 Complete | S | `P-SYS-001` | 12 | `app/services/research/README.md` |
| `NFR-RES-015` | Research | Documentation | T3 Complete | S | `P-SYS-001` | 12 | `app/services/research/README.md` |
| `FR-PORT-001` | Portfolio | Reject unknown fields and unsafe runtime objects. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/portfolio/README.md` |
| `FR-PORT-002` | Portfolio | Separate contract_version from namespaced schema_id. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/portfolio/README.md` |
| `FR-PORT-003` | Portfolio | Require UTC timestamps, trace IDs, immutable owner references, and finite numbers. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/portfolio/README.md` |
| `FR-PORT-004` | Portfolio | Represent capital weights separately from Risk-authoritative budget projection references. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/portfolio/README.md` |
| `FR-PORT-005` | Portfolio | Version breaking contract changes and update every producer/consumer document together. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/portfolio/README.md` |
| `FR-PORT-006` | Portfolio | Require a current approving eligibility decision for every exact strategy/version/scope. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/portfolio/README.md` |
| `FR-PORT-009` | Portfolio | Detect a reference/version change before publication or activation. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/portfolio/README.md` |
| `FR-PORT-010` | Portfolio | Support fixed, equal, and inverse-volatility methods only. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/portfolio/README.md` |
| `FR-PORT-011` | Portfolio | Reject zero/negative volatility, insufficient observations, non-finite values, and invalid weight totals. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/portfolio/README.md` |
| `FR-PORT-012` | Portfolio | Return identical bytes and hash for identical inputs/configuration. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/portfolio/README.md` |
| `FR-PORT-013` | Portfolio | Exclude MVO, Black-Litterman, CVaR, and implicit optimizer delegation. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/portfolio/README.md` |
| `FR-PORT-014` | Portfolio | Publish nothing on partial construction failure. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/portfolio/README.md` |
| `FR-PORT-015` | Portfolio | Require Simulation validation and current Risk authorization before activation. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/portfolio/README.md` |
| `FR-PORT-018` | Portfolio | Use optimistic concurrency and one active version per scope. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/portfolio/README.md` |
| `FR-PORT-019` | Portfolio | Implement rollback only as a new governed version. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/portfolio/README.md` |
| `FR-PORT-020` | Portfolio | Bind drift to an active allocation version and fresh actual-exposure evidence. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/portfolio/README.md` |
| `FR-PORT-024` | Portfolio | Block planning/submission on kill switch, expiry, stale evidence, or target-version change. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/portfolio/README.md` |
| `FR-PORT-025` | Portfolio | Submit only receiver-owned Risk, Simulation, and Trading request contracts. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/portfolio/README.md` |
| `FR-PORT-029` | Portfolio | Never retry a potentially accepted mutation without receiver-provided idempotency semantics. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/portfolio/README.md` |
| `FR-PORT-030` | Portfolio | Prevent direct writes by other domains. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/portfolio/README.md` |
| `FR-PORT-034` | Portfolio | Expose construction, status, activation, drift/rebalance, rollback, and history operations. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/portfolio/README.md` |
| `FR-PORT-035` | Portfolio | Accept AuthContext and request_id: str \ | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/portfolio/README.md` |
| `FR-PORT-036` | Portfolio | Return structured success/error envelopes; never None or raw exceptions. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/portfolio/README.md` |
| `FR-PORT-037` | Portfolio | Keep authentication and presentation logic outside Portfolio. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/portfolio/README.md` |
| `P-PORT-001` | Portfolio | contracts feature/component (provisional) | T0 Skeleton | M | `P-SYS-001` | 1 | `app/services/portfolio/README.md` |
| `P-PORT-003` | Portfolio | construction feature/component (provisional) | T0 Skeleton | M | `P-SYS-001` | 1 | `app/services/portfolio/README.md` |
| `P-PORT-008` | Portfolio | api feature/component (provisional) | T0 Skeleton | M | `P-SYS-001` | 1 | `app/services/portfolio/README.md` |
| `WF-PORT-002` | Portfolio | Construct Allocation Candidate | T0 Skeleton | M | `P-SYS-001` | 1 | `app/services/portfolio/README.md` |
| `FR-PORT-007` | Portfolio | Fail closed on missing, stale, incompatible, cyclic, or unverifiable FX evidence. | T2 Advanced | S | `P-SYS-001` | 9 | `app/services/portfolio/README.md` |
| `FR-PORT-008` | Portfolio | Never synthesize rates, metrics, registrations, or approvals. | T2 Advanced | S | `P-SYS-001` | 9 | `app/services/portfolio/README.md` |
| `FR-PORT-016` | Portfolio | Require explicit human approval for paper/live; allow automatic simulation activation only within simulation policy. | T2 Advanced | S | `P-SYS-001` | 9 | `app/services/portfolio/README.md` |
| `FR-PORT-017` | Portfolio | Block activation while any applicable kill switch is active. | T2 Advanced | S | `P-SYS-001` | 9 | `app/services/portfolio/README.md` |
| `FR-PORT-021` | Portfolio | Route every plan through Risk review before Trading submission. | T2 Advanced | S | `P-SYS-001` | 9 | `app/services/portfolio/README.md` |
| `FR-PORT-022` | Portfolio | Make existing over-budget correction reduce-only unless a separately authorized risk increase exists. | T2 Advanced | S | `P-SYS-001` | 9 | `app/services/portfolio/README.md` |
| `FR-PORT-023` | Portfolio | Never open solely to match target weights. | T2 Advanced | S | `P-SYS-001` | 9 | `app/services/portfolio/README.md` |
| `FR-PORT-026` | Portfolio | Revalidate every mutable/expiring gate immediately before side effects. | T2 Advanced | S | `P-SYS-001` | 9 | `app/services/portfolio/README.md` |
| `FR-PORT-027` | Portfolio | Propagate request/correlation/causation IDs end to end. | T2 Advanced | S | `P-SYS-001` | 9 | `app/services/portfolio/README.md` |
| `FR-PORT-028` | Portfolio | Emit redacted audit events for requests, decisions, activation, rollback, and submission. | T2 Advanced | S | `P-SYS-001` | 9 | `app/services/portfolio/README.md` |
| `FR-PORT-031` | Portfolio | Preserve every superseded and rolled-back version. | T2 Advanced | S | `P-SYS-001` | 9 | `app/services/portfolio/README.md` |
| `FR-PORT-032` | Portfolio | Use atomic activation and deterministic idempotency keys. | T2 Advanced | S | `P-SYS-001` | 9 | `app/services/portfolio/README.md` |
| `FR-PORT-033` | Portfolio | Store references, hashes, and decisions needed to reproduce lineage. | T2 Advanced | S | `P-SYS-001` | 9 | `app/services/portfolio/README.md` |
| `P-PORT-002` | Portfolio | evidence feature/component (provisional) | T2 Advanced | M | `P-SYS-001` | 9 | `app/services/portfolio/README.md` |
| `P-PORT-004` | Portfolio | state feature/component (provisional) | T2 Advanced | M | `P-SYS-001` | 9 | `app/services/portfolio/README.md` |
| `P-PORT-005` | Portfolio | allocation feature/component (provisional) | T2 Advanced | M | `P-SYS-001` | 9 | `app/services/portfolio/README.md` |
| `P-PORT-006` | Portfolio | rebalancing feature/component (provisional) | T2 Advanced | M | `P-SYS-001` | 9 | `app/services/portfolio/README.md` |
| `P-PORT-007` | Portfolio | orchestration feature/component (provisional) | T2 Advanced | M | `P-SYS-001` | 9 | `app/services/portfolio/README.md` |
| `WF-PORT-001` | Portfolio | Cross-domain | T2 Advanced | M | `P-SYS-001` | 9 | `app/services/portfolio/README.md` |
| `WF-PORT-003` | Portfolio | Cross-domain | T2 Advanced | M | `P-SYS-001` | 9 | `app/services/portfolio/README.md` |
| `WF-PORT-004` | Portfolio | Activate Allocation Version | T2 Advanced | M | `P-SYS-001` | 9 | `app/services/portfolio/README.md` |
| `WF-PORT-005` | Portfolio | Detect Drift and Plan Rebalance | T2 Advanced | M | `P-SYS-001` | 9 | `app/services/portfolio/README.md` |
| `WF-PORT-006` | Portfolio | Cross-domain | T2 Advanced | M | `P-SYS-001` | 9 | `app/services/portfolio/README.md` |
| `WF-PORT-007` | Portfolio | Internal | T2 Advanced | M | `P-SYS-001` | 9 | `app/services/portfolio/README.md` |
| `NFR-PORT-001` | Portfolio | Google Python Style, complete types, Google docstrings, absolute imports, and no print. | T3 Complete | S | `P-SYS-001` | 12 | `app/services/portfolio/README.md` |
| `NFR-PORT-002` | Portfolio | Deterministic output for identical versioned inputs and explicit configuration. | T3 Complete | S | `P-SYS-001` | 12 | `app/services/portfolio/README.md` |
| `NFR-PORT-003` | Portfolio | Fail closed on missing evidence, authorization, policy, configuration, or ownership ambiguity. | T3 Complete | S | `P-SYS-001` | 12 | `app/services/portfolio/README.md` |
| `NFR-PORT-004` | Portfolio | Never log secrets, raw approval tokens, credentials, or unredacted account data. | T3 Complete | S | `P-SYS-001` | 12 | `app/services/portfolio/README.md` |
| `NFR-PORT-005` | Portfolio | Maintain at least 80% package test coverage. | T3 Complete | S | `P-SYS-001` | 12 | `app/services/portfolio/README.md` |
| `NFR-PORT-006` | Portfolio | No live side effect originates in Portfolio; Trading remains the sole execution authority. | T3 Complete | S | `P-SYS-001` | 12 | `app/services/portfolio/README.md` |
| `NFR-PORT-007` | Portfolio | All money, rates, weights, and tolerances use documented decimal/precision rules; no binary-float ambiguity at boundaries. | T3 Complete | S | `P-SYS-001` | 12 | `app/services/portfolio/README.md` |
| `NFR-PORT-008` | Portfolio | All timestamps are timezone-aware UTC. | T3 Complete | S | `P-SYS-001` | 12 | `app/services/portfolio/README.md` |
| `NFR-PORT-009` | Portfolio | No hidden numeric defaults; every cap, threshold, tolerance, schedule, expiry, and observation minimum is required configuration. | T3 Complete | S | `P-SYS-001` | 12 | `app/services/portfolio/README.md` |
| `NFR-PORT-010` | Portfolio | Package errors extend Utils canonical exceptions and map to structured Portfolio codes. | T3 Complete | S | `P-SYS-001` | 12 | `app/services/portfolio/README.md` |
| `CAP-UI-001` | UI/API | canonical composition/lifecycle | T0 Skeleton | M | `P-SYS-001` | 1 | `app/services/api/README.md` |
| `CAP-UI-002` | UI/API | contracts/envelopes/errors | T0 Skeleton | M | `P-SYS-001` | 1 | `app/services/api/README.md` |
| `CAP-UI-003` | UI/API | canonical identity/sessions | T0 Skeleton | M | `P-SYS-001` | 1 | `app/services/api/README.md` |
| `CAP-UI-007` | UI/API | operator approvals/events | T0 Skeleton | M | `P-SYS-001` | 1 | `app/services/api/README.md` |
| `CAP-UI-013` | UI/API | risk decision support | T0 Skeleton | M | `P-SYS-001` | 1 | `app/services/api/README.md` |
| `CAP-UI-014` | UI/API | live monitoring/mutations | T0 Skeleton | M | `P-SYS-001` | 1 | `app/services/api/README.md` |
| `CAP-UI-024` | UI/API | contract/security/workflow tests | T0 Skeleton | M | `P-SYS-001` | 1 | `app/services/api/README.md` |
| `FR-API-001` | UI/API | Carry request/trace, route, operation, side-effect, timing, timestamp, stale, pagination, and idempotency-replay metadata. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/api/README.md` |
| `FR-API-002` | UI/API | Expose a bounded redacted error with deterministic code, message, details, request/trace IDs, and retryability. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/api/README.md` |
| `FR-API-003` | UI/API | Return exactly status, message, data, error, and metadata for non-streaming responses; HTTP 204 has no body. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/api/README.md` |
| `FR-API-004` | UI/API | Validate ordered stream events with type, data, request/trace IDs, sequence, UTC timestamp, heartbeat, and terminal error. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/api/README.md` |
| `FR-API-005` | UI/API | Declare classification, stability, method/path, auth, permission, schemas, status/errors, side effects, owner, pagination, idempotency, audit, rate class, an... | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/api/README.md` |
| `FR-API-006` | UI/API | Carry validated request, workflow, permission, approval, audit, idempotency, and safety context without granting authority itself. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/api/README.md` |
| `FR-API-007` | UI/API | Bound and redact current route, visible entity IDs, and approved actions before context leaves the frontend. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/api/README.md` |
| `FR-API-008` | UI/API | Register each route contract exactly once and reject collisions or incomplete declarations. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/api/README.md` |
| `FR-API-013` | UI/API | Produce Utils AuthContext from validated authority claims and trace context, never caller-controlled role headers. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/api/README.md` |
| `FR-API-014` | UI/API | Enforce the approved permission at the backend boundary and return the standard 403 envelope on failure. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/api/README.md` |
| `FR-API-015` | UI/API | Validate governed context, CSRF when applicable, approval scope, idempotency dependency, stale evidence, and audit intent before delegation. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/api/README.md` |
| `FR-API-017` | UI/API | Create/validate request and correlation IDs, classify registered route intent, authenticate where required, and attach canonical context. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/api/README.md` |
| `FR-API-018` | UI/API | Return HTTP 200 with coarse service status only when the process accepts requests; expose no private dependency data. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/api/README.md` |
| `FR-API-019` | UI/API | Return protected required/optional component readiness with degraded reasons and timestamps. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/api/README.md` |
| `FR-API-020` | UI/API | Translate a validated authoritative owner event into a redacted ordered StreamEvent. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/api/README.md` |
| `FR-API-021` | UI/API | Authenticate connection, enforce quota policy, deliver ordered events, detect gaps/backpressure, resume when supported, emit terminal errors, and clean up on... | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/api/README.md` |
| `FR-API-022` | UI/API | Expose typed registration, login, and logout without fallback identities. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/api/README.md` |
| `FR-API-023` | UI/API | Expose authenticated settings read/update through one canonical path. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/api/README.md` |
| `FR-API-024` | UI/API | Expose authenticated symbol discovery and bounded delegated dataset preparation. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/api/README.md` |
| `FR-API-025` | UI/API | Expose strategy catalogue/version reads and explicitly approved Optimization-result adoption through Strategy-owned registration/parameter commands, returnin... | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/api/README.md` |
| `FR-API-026` | UI/API | Expose one exact synchronous SimulationBacktestRequestV1 run returning a terminal SimulationResult/report or structured error through Simulation/Analytics; n... | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/api/README.md` |
| `FR-API-028` | UI/API | Expose position sizing, regime, allocation, governance, and bounded advisory scenario evaluation solely through Risk; scenario responses use registered Scena... | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/api/README.md` |
| `FR-API-029` | UI/API | Expose live/paper session lifecycle, reads, strategy assignment, governed orders/positions, and events solely through Trading after Risk clearance. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/api/README.md` |
| `FR-API-030` | UI/API | Expose bounded synchronous optimization, walk-forward, unsupervised, and Monte Carlo/scenario operations returning one terminal OptimizationResult or structu... | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/api/README.md` |
| `FR-API-031` | UI/API | Submit one bounded initial Research request and return only registered ResearchReport v1 advisory evidence; Research-internal datasets, stage profiles, score... | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/api/README.md` |
| `FR-API-032` | UI/API | Expose broker/equity/summary/resource/market-hours/calendar snapshots with timestamps and stale/unavailable states; merge system status into readiness. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/api/README.md` |
| `FR-API-034` | UI/API | Authenticate/authorize a human operator; construct KillSwitchCommand v1 with explicit global/portfolio/strategy/symbol scope and applicable identifiers; subm... | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/api/README.md` |
| `FR-API-035` | UI/API | Initialize required storage/migrations and approved cleanup/scheduler work, surface optional degradation, and close only gateway-owned resources. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/api/README.md` |
| `FR-API-036` | UI/API | Construct one canonical FastAPI app with configured exact-origin CORS, redaction/context middleware, required/optional routers, liveness, and readiness. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/api/README.md` |
| `FR-API-037` | UI/API | Expose the canonical ASGI application at app.services.api.main:app. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/api/README.md` |
| `FR-API-038` | UI/API | Send typed requests with configured base URL, approved auth transport, request/trace IDs, safe JSON/204 parsing, contract validation, one opt-in transient GE... | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/api/README.md` |
| `FR-API-039` | UI/API | Expose only data from a successful envelope without creating another transport stack. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/api/README.md` |
| `FR-API-040` | UI/API | Carry status, code, request/trace IDs, retryability, and bounded details for frontend failures. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/api/README.md` |
| `FR-API-041` | UI/API | Provide one catalog containing typed clients only for auth, settings, data, strategies, backtests, simulation, risk, Trading, portfolio, optimization, core r... | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/api/README.md` |
| `FR-API-042` | UI/API | Recover the approved browser session, protect layouts, and clear/redirect on expiration without exposing credentials. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/api/README.md` |
| `FR-API-043` | UI/API | Register only bounded, redacted current page entities/actions for route-aware workflows. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/api/README.md` |
| `FR-API-044` | UI/API | Build governed options and block obviously incomplete/stale requests before fetch while treating backend checks as authoritative. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/api/README.md` |
| `FR-API-045` | UI/API | Validate ordered events, heartbeat/reconnect/backpressure/terminal behavior, clean up on disconnect, and refresh authoritative state after a gap. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/api/README.md` |
| `FR-API-046` | UI/API | Provide accessible shell/navigation/error boundary and render stale/offline/unavailable states without hiding governed controls. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/api/README.md` |
| `FR-API-047` | UI/API | Render approved dashboard snapshots with time/freshness and without currency strength. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/api/README.md` |
| `FR-API-048` | UI/API | Render registered strategy catalogue/version commands using typed clients only; raw import/export/SQX controls are absent. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/api/README.md` |
| `FR-API-049` | UI/API | Render synchronous backtest configuration, local request activity, and completed SimulationResult/report evidence without presenting local activity as author... | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/api/README.md` |
| `FR-API-050` | UI/API | Render Risk decision support and live/paper Trading monitoring/controls only when authoritative backend gates are available. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/api/README.md` |
| `FR-API-051` | UI/API | Render terminal synchronous OptimizationResult and registered ResearchReport evidence, excluding optimization job progress/cancellation and direct Research-i... | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/api/README.md` |
| `FR-API-053` | UI/API | Render login/register routes and recover cleanly from invalid or expired sessions. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/api/README.md` |
| `FR-API-054` | UI/API | Protect dashboard, settings, strategies, backtests, simulation, risk, live, optimization, and Edge Lab routes. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/api/README.md` |
| `FR-API-055` | UI/API | Compose an approved workflow route exclusively from public clients, context, and workflow components. | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/api/README.md` |
| `FR-API-056` | UI/API | Expose Portfolio construction/result/history/drift and governed activation/rollback/rebalance operations through Portfolio, with Risk eligibility/review and ... | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/api/README.md` |
| `FR-API-057` | UI/API | Encrypt credential material before persistence with authenticated encryption, store key ID/version and integrity metadata but never the key, select exactly t... | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/api/README.md` |
| `FR-API-058` | UI/API | Resolve an opaque secret:// reference only at composition, build one immutable Brokers-owned BrokerConnectionConfig v1 with SecretStr values, and discard pla... | T0 Skeleton | S | `P-SYS-001` | 1 | `app/services/api/README.md` |
| `P-API-001` | UI/API | contracts feature/component (provisional) | T0 Skeleton | M | `P-SYS-001` | 1 | `app/services/api/README.md` |
| `P-API-002` | UI/API | identity feature/component (provisional) | T0 Skeleton | M | `P-SYS-001` | 1 | `app/services/api/README.md` |
| `P-API-003` | UI/API | middleware feature/component (provisional) | T0 Skeleton | M | `P-SYS-001` | 1 | `app/services/api/README.md` |
| `P-API-004` | UI/API | health feature/component (provisional) | T0 Skeleton | M | `P-SYS-001` | 1 | `app/services/api/README.md` |
| `P-API-006` | UI/API | routes feature/component (provisional) | T0 Skeleton | M | `P-SYS-001` | 1 | `app/services/api/README.md` |
| `P-API-007` | UI/API | composition feature/component (provisional) | T0 Skeleton | M | `P-SYS-001` | 1 | `app/services/api/README.md` |
| `P-API-008` | UI/API | ui_clients feature/component (provisional) | T0 Skeleton | M | `P-SYS-001` | 1 | `app/services/api/README.md` |
| `P-API-009` | UI/API | ui_context feature/component (provisional) | T0 Skeleton | M | `P-SYS-001` | 1 | `app/services/api/README.md` |
| `P-API-010` | UI/API | ui_components feature/component (provisional) | T0 Skeleton | M | `P-SYS-001` | 1 | `app/services/api/README.md` |
| `P-API-011` | UI/API | ui_app feature/component (provisional) | T0 Skeleton | M | `P-SYS-001` | 1 | `app/services/api/README.md` |
| `WF-API-001` | UI/API | Internal | T0 Skeleton | M | `P-SYS-001` | 1 | `app/services/api/README.md` |
| `WF-API-002` | UI/API | Internal | T0 Skeleton | M | `P-SYS-001` | 1 | `app/services/api/README.md` |
| `WF-API-004` | UI/API | Cross-domain | T0 Skeleton | M | `P-SYS-001` | 1 | `app/services/api/README.md` |
| `WF-API-006` | UI/API | Cross-domain | T0 Skeleton | M | `P-SYS-001` | 1 | `app/services/api/README.md` |
| `WF-API-012` | UI/API | Cross-domain | T0 Skeleton | M | `P-SYS-001` | 1 | `app/services/api/README.md` |
| `WF-API-013` | UI/API | Cross-domain | T0 Skeleton | M | `P-SYS-001` | 1 | `app/services/api/README.md` |
| `WF-API-015` | UI/API | Cross-domain | T0 Skeleton | M | `P-SYS-001` | 1 | `app/services/api/README.md` |
| `CAP-UI-008` | UI/API | settings | T1 Core | M | `P-SYS-001` | 2 | `app/services/api/README.md` |
| `CAP-UI-009` | UI/API | market data/prepared datasets | T1 Core | M | `P-SYS-001` | 2 | `app/services/api/README.md` |
| `FR-API-009` | UI/API | Hash new non-empty passwords and verify stored hashes within UI/API, then authenticate valid active and verified credentials, update last-login evidence, rat... | T1 Core | S | `P-SYS-001` | 2 | `app/services/api/README.md` |
| `FR-API-010` | UI/API | Replace the user's prior active session and create one configurable-expiry opaque server-side session in the UI/API-owned store; return it through a secure H... | T1 Core | S | `P-SYS-001` | 2 | `app/services/api/README.md` |
| `FR-API-011` | UI/API | Validate standard session credentials, expiry, revocation, and current account status and delete expired sessions. | T1 Core | S | `P-SYS-001` | 2 | `app/services/api/README.md` |
| `FR-API-012` | UI/API | Revoke the caller's persisted session on logout; repeated logout is deterministic. | T1 Core | S | `P-SYS-001` | 2 | `app/services/api/README.md` |
| `FR-API-016` | UI/API | Redact secrets before any log/trace/metric emission and log only allowlisted method, route, identifiers, status, duration, and error code. | T1 Core | S | `P-SYS-001` | 2 | `app/services/api/README.md` |
| `WF-API-016` | UI/API | Cross-domain | T1 Core | M | `P-SYS-001` | 2 | `app/services/api/README.md` |
| `CAP-UI-010` | UI/API | strategy catalogue/version commands | T1 Core | M | `P-SYS-001` | 3 | `app/services/api/README.md` |
| `WF-API-003` | UI/API | Cross-domain | T1 Core | M | `P-SYS-001` | 4 | `app/services/api/README.md` |
| `WF-API-011` | UI/API | Cross-domain | T1 Core | M | `P-SYS-001` | 4 | `app/services/api/README.md` |
| `CAP-UI-018` | UI/API | dashboard reads | T2 Advanced | M | `P-SYS-001` | 7 | `app/services/api/README.md` |
| `CAP-UI-015` | UI/API | optimization/scenarios | T2 Advanced | M | `P-SYS-001` | 8 | `app/services/api/README.md` |
| `WF-API-010` | UI/API | Cross-domain | T2 Advanced | M | `P-SYS-001` | 9 | `app/services/api/README.md` |
| `WF-API-009` | UI/API | Cross-domain | T2 Advanced | M | `P-SYS-001` | 10 | `app/services/api/README.md` |
| `CAP-UI-020` | UI/API | shared streaming | T1 Core | M | `P-SYS-001` | 11 | `app/services/api/README.md` |
| `P-API-005` | UI/API | streams feature/component (provisional) | T1 Core | M | `P-SYS-001` | 11 | `app/services/api/README.md` |
| `WF-API-005` | UI/API | Cross-domain | T1 Core | M | `P-SYS-001` | 11 | `app/services/api/README.md` |
| `WF-API-017` | UI/API | Cross-domain | T1 Core | M | `P-SYS-001` | 11 | `app/services/api/README.md` |
| `NFR-API-001` | UI/API | Architecture | T3 Complete | S | `P-SYS-001` | 12 | `app/services/api/README.md` |
| `NFR-API-002` | UI/API | Security | T3 Complete | S | `P-SYS-001` | 12 | `app/services/api/README.md` |
| `NFR-API-003` | UI/API | Safety | T3 Complete | S | `P-SYS-001` | 12 | `app/services/api/README.md` |
| `NFR-API-004` | UI/API | Contracts | T3 Complete | S | `P-SYS-001` | 12 | `app/services/api/README.md` |
| `NFR-API-005` | UI/API | Security | T3 Complete | S | `P-SYS-001` | 12 | `app/services/api/README.md` |
| `NFR-API-006` | UI/API | Reliability | T3 Complete | S | `P-SYS-001` | 12 | `app/services/api/README.md` |
| `NFR-API-007` | UI/API | Streaming | T3 Complete | S | `P-SYS-001` | 12 | `app/services/api/README.md` |
| `NFR-API-008` | UI/API | Freshness | T3 Complete | S | `P-SYS-001` | 12 | `app/services/api/README.md` |
| `NFR-API-009` | UI/API | Accessibility | T3 Complete | S | `P-SYS-001` | 12 | `app/services/api/README.md` |
| `NFR-API-010` | UI/API | Observability | T3 Complete | S | `P-SYS-001` | 12 | `app/services/api/README.md` |
| `NFR-API-011` | UI/API | Pagination | T3 Complete | S | `P-SYS-001` | 12 | `app/services/api/README.md` |
| `NFR-API-012` | UI/API | Timeouts | T3 Complete | S | `P-SYS-001` | 12 | `app/services/api/README.md` |
| `NFR-API-013` | UI/API | Resilience | T3 Complete | S | `P-SYS-001` | 12 | `app/services/api/README.md` |
| `NFR-API-014` | UI/API | Imports | T3 Complete | S | `P-SYS-001` | 12 | `app/services/api/README.md` |
| `NFR-API-015` | UI/API | Documentation | T3 Complete | S | `P-SYS-001` | 12 | `app/services/api/README.md` |
| `NFR-API-016` | UI/API | Testing | T3 Complete | S | `P-SYS-001` | 12 | `app/services/api/README.md` |
| `NFR-API-017` | UI/API | Quality | T3 Complete | S | `P-SYS-001` | 12 | `app/services/api/README.md` |
| `NFR-API-018` | UI/API | Determinism | T3 Complete | S | `P-SYS-001` | 12 | `app/services/api/README.md` |
| `CAP-UI-004` | UI/API | authorization/governed writes/idempotency | T3 Complete | M | `P-SYS-001` | 13 | `app/services/api/README.md` |
| `CAP-UI-005` | UI/API | request security/context/observability | T3 Complete | M | `P-SYS-001` | 13 | `app/services/api/README.md` |
| `CAP-UI-006` | UI/API | health/readiness | T3 Complete | M | `P-SYS-001` | 13 | `app/services/api/README.md` |
| `CAP-UI-011` | UI/API | synchronous backtest result | T3 Complete | M | `P-SYS-001` | 13 | `app/services/api/README.md` |
| `CAP-UI-012` | UI/API | interactive simulator | T3 Complete | M | `P-SYS-001` | 13 | `app/services/api/README.md` |
| `CAP-UI-016` | UI/API | initial Edge Lab | T3 Complete | M | `P-SYS-001` | 13 | `app/services/api/README.md` |
| `CAP-UI-019` | UI/API | documentation | T3 Complete | M | `P-SYS-001` | 13 | `app/services/api/README.md` |
| `CAP-UI-021` | UI/API | typed frontend clients | T3 Complete | M | `P-SYS-001` | 13 | `app/services/api/README.md` |
| `CAP-UI-022` | UI/API | frontend auth/shell | T3 Complete | M | `P-SYS-001` | 13 | `app/services/api/README.md` |
| `CAP-UI-023` | UI/API | workflow pages/components | T3 Complete | M | `P-SYS-001` | 13 | `app/services/api/README.md` |
| `FR-API-027` | UI/API | Negative requirement: interactive Simulation session/frame/mutation routes remain absent. | T3 Complete | S | `P-SYS-001` | 13 | `app/services/api/README.md` |
| `WF-API-007` | UI/API | Negative requirement: interactive Simulation session lifecycle remains excluded. | T3 Complete | M | `P-SYS-001` | 13 | `app/services/api/README.md` |
| `WF-API-008` | UI/API | Negative requirement: interactive Simulation mutation and what-if workflow remains excluded. | T3 Complete | M | `P-SYS-001` | 13 | `app/services/api/README.md` |

## Coverage summary

- Total IDs: **1230**
- Explicit source IDs: **1115**
- Provisional feature/component IDs: **115**
- Explicit negative/absence IDs: **9**
- Unassigned: **0**
- Duplicate inventory IDs: **0**

### Count per phase

| Phase | Version | IDs |
|---:|---|---:|
| 1 | 1.1 | 675 |
| 2 | 1.2 | 69 |
| 3 | 1.3 | 19 |
| 4 | 1.4 | 21 |
| 5 | 1.5 | 23 |
| 6 | 1.6 | 22 |
| 7 | 1.7 | 16 |
| 8 | 1.8 | 29 |
| 9 | 1.9 | 34 |
| 10 | 1.10 | 65 |
| 11 | 1.11 | 30 |
| 12 | 1.12 | 158 |
| 13 | 2.0 | 69 |

### Count per domain

| Domain | IDs |
|---|---:|
| System | 20 |
| Utils | 56 |
| Brokers | 187 |
| Data | 114 |
| Indicators | 45 |
| Strategy | 61 |
| Risk | 85 |
| Trading | 114 |
| Simulation | 71 |
| Analytics | 74 |
| Optimization | 82 |
| Research | 135 |
| Portfolio | 62 |
| UI/API | 124 |

## Coverage assertions

- **Unassigned: 0.**
- **Every inventory ID is assigned to exactly one of 13 phases.**
- **Phase 1 contains the complete narrow MT5 demo execution workflow plus the simulation workflow.**
- **The FakeBrokerAdapter is not used by the Phase 1 integration or usage proof.**
- **The union of Phases 1-13 equals the authoritative ledger scope plus provisional component and negative-boundary verification.**

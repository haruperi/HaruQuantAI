# Utils — V1/V2 Reconciliation

## 1. Reconciliation Scope

* **Domain:** Utils
* **Domain ID:** `UTL`
* **Current V1 package:** `app/services/utils`
* **Intended V2 package:** **Open Decision** — the V2 document alternates between `app/services/utils` and `tools/utils`.
* **V1 audit report:** `docs/dev/audits/utils-v1-audit.md`
* **V2 requirements:** `01-utils.md`
* **Comparison method:** Behaviour-to-behaviour reconciliation using only the two supplied documents. No code was inspected or modified.
* **V2 requirement identification:** The V2 source does not provide stable requirement IDs. This reconciliation assigns IDs to every checklist item and to additional normative ownership, matrix, default, architecture, and CI statements.
* **Coverage:** 28 V1 capability dispositions, 9 V1 workflow reconciliations, 4 added/inferred final workflows, and 1,241 V2 normative-item dispositions.
* **Comparison limitations:**
  * The V1 audit is static evidence; tests, coverage, runtime imports, dynamic registration, and production configuration were unavailable.
  * The V2 document contains extensive duplication across requirements, tests, acceptance criteria, and Definition of Done. Every item is retained in the disposition register, but repeated items map to the same final capability.
  * Package location, adapter ownership, benchmark thresholds, supported platforms, CI tooling, and agent-safe dataframe input modes are unresolved.
  * Cross-domain boundary decisions are flagged for the later system alignment review. This document does not update the top-level system document.

## 2. Executive Summary

### Valuable V1 behaviour to preserve

The proven V1 core is worth preserving: structured logging, secret-safe logging, deterministic error mapping, standard tool envelopes, password hashing and verification, safe paths, UTC/time normalization, explicit directory creation, runtime settings, dataframe caching used by the Data service, selected schema validation, and OHLCV diagnostics.

### Major V1 weaknesses to correct

The final rebuild must correct the defective package registry, import-time log-file creation, duplicate response builders, duplicate path/dataframe/schema/OHLCV implementations, hybrid return types, unbounded or disconnected stateful components, and domain leakage from Errors, Settings, Normalization, and Common utilities. Dataframe caching, live readiness, research models, and domain-specific exceptions do not belong in the final Utils core.

### Important V2 behaviour to add

The accepted additions are a strict classified public registry, public contract entries, one immutable limits profile, bounded validation diagnostics, deterministic field paths, explicit settings mapping/injection, deny-by-default tool allowlists, stronger redaction governance, explicit optional-dependency errors, and import-safety guarantees.

### V2 complexity to reject, simplify, or defer

The initial rebuild should not include the proposed full Event Bus retry/dead-letter/idempotency/backpressure subsystem, notification routing and provider clients, broad Prometheus/Grafana coverage, clock-drift integration, provider circuit breakers, chaos testing, or external adapters. These capabilities have no confirmed V1 production workflow and depend on unresolved ownership, dependencies, configuration, benchmarks, and providers.

Two V2 proposals are rejected outright:

1. the unexplained rule freezing public exports after “v8 acceptance”; and
2. implicit redaction inside canonical JSON serialization.

### Major open decisions

The most important unresolved decisions are the canonical package path, first implementation slice, agent-safe dataframe inputs, adapter ownership, notification ownership, observability ownership, benchmark thresholds, platform/dependency matrix, CI toolchain, Data-cache migration, and auth-context ownership.

### Recommended migration direction

Refactor in place around the proven core, consolidate duplicated implementations, move domain-specific responsibilities to their owners, and rebuild the package registry last. Treat events, notifications, and observability as separate production slices rather than prerequisites for the core Utils foundation.

### Disposition summary


| Decision | Count |
| --- | --- |
| Keep | 150 |
| Modify | 502 |
| Add | 173 |
| Merge | 0 |
| Split | 0 |
| Remove | 0 |
| Defer | 391 |
| Reject | 2 |
| Open Decision | 23 |


**Total V2 normative items classified:** 1241


## 3. Decision Principles

1. Preserve proven behaviour and caller value.
2. Treat V1 as evidence, not future authority.
3. Treat V2 as a proposal, not automatic approval.
4. Keep the first rebuild limited to the smallest shared production foundation.
5. Prefer native functions for stateless transformations and validation.
6. Use classes only for immutable models, owned state, or explicit lifecycle.
7. Keep one return contract per public name.
8. Separate native support helpers from official AI tool wrappers.
9. Keep imports side-effect free and optional dependencies lazy.
10. Bound validation depth, payloads, issues, samples, strings, and responses.
11. Keep canonical serialization pure; apply redaction explicitly at sensitive boundaries.
12. Move domain-specific policy, configuration, errors, and caches to their owning domains.
13. Defer provider-backed and stateful infrastructure until real workflows and ownership are confirmed.
14. Do not create modules merely to match a proposed tree.
15. Require explicit contract and registry tests for every public symbol.

## 4. Capability Reconciliation Matrix


| Capability ID | Capability | V1 evidence | V2 requirement | Gap | Decision | Final behaviour | Reuse approach | Reason |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| CAP-UTL-001 | Public registry and API classification | `V1-CAP-UTILS-027`; `__init__.py`; broken lazy facade | `V2-FR-REG-001..011`, `V2-API-RULE-001..007` | V1 registry is used but advertises missing names and returns modules on lookup failure. | Modify | One strict, side-effect-free registry. Every public name is real, classified, contracted, and tested. | Refactor | Preserve the valuable import facade while removing fallback aliases and accidental exports. |
| CAP-UTL-002 | Structured and secret-safe logging | `V1-CAP-UTILS-001`, `002`, `028`; `V1-WF-UTILS-001` | `V2-FR-LOG-*`, `V2-NFR-IMPORT-*` | V1 is widely used but configures file sinks at import and hides sink failures. | Modify | Import-safe logger object; explicit settings-driven console/file configuration; structured fields; bounded secret-safe degradation. | Refactor | Logging is proven production value, but its lifecycle and failure behavior must change. |
| CAP-UTL-003 | Shared error model and mapping | `V1-CAP-UTILS-003`; `errors.py` | `V2-FR-ERR-*`, `V2-ERR-*` | Useful shared errors coexist with domain-specific taxonomies and broken aliases. | Split | Utils keeps base errors, shared codes, generic mapping, and tool-boundary conversion. Domain errors move to owning domains. | Refactor | The common contract is essential; domain taxonomies create central coupling. |
| CAP-UTL-004 | Standard tool responses and timing | `V1-CAP-UTILS-004`; `V1-WF-UTILS-004` | `V2-FR-RESP-*`, `V2-FR-TOOL-*` | V1 has two response builders with different semantics. | Merge | One envelope schema, one metadata builder, one validator, and explicit native-to-tool wrappers. | Refactor | The behavior is proven; duplicate contracts are the defect. |
| CAP-UTL-005 | Identity, version, and trace identifiers | `V1-CAP-UTILS-005`; `identity.py` | `V2-FR-ID-*` | Core generators exist, while several advertised aliases do not. | Modify | Small native UUID-based generators and deterministic validators for request, workflow, correlation, causation, event, idempotency, and version values. | Refactor | Keep the simple working behavior and remove fictional compatibility exports. |
| CAP-UTL-006 | UTC time, clock, and freshness | `V1-CAP-UTILS-006`, `007`; normalization; `V1-WF-UTILS-006`, `007` | `V2-FR-TIME-*`, freshness portions of `V2-FR-SCHEMA-*` | V1 has valuable helpers but hybrid return types and embedded board policy. | Split | Utils keeps native UTC parsing/formatting, monotonic timing, injected clocks, and generic freshness. Domain policies move out. | Refactor | Generic time behavior is shared; board/execution policy is not. |
| CAP-UTL-007 | Safe paths and explicit directory creation | `V1-CAP-UTILS-008`, `009`; `V1-WF-UTILS-005` | `V2-FR-PATH-*` | A sound `paths.py` API is duplicated by hybrid wrappers in normalization. | Merge | One `Path`-returning, traversal-safe API; creation only through explicit `ensure_*` calls. | Reuse and refactor | The cohesive V1 implementation already matches the desired behavior. |
| CAP-UTL-008 | Canonical serialization | `V1-CAP-UTILS-005`; duplicate `canonical_json` implementations | `V2-FR-FOUND-010`, `022`; `V2-FR-SEC-025` | Duplicate implementations and a V2 proposal for implicit redaction. | Merge | One pure deterministic JSON serializer. Sensitive workflows must redact explicitly before serialization. | Refactor | Canonical identity must not change silently because of hidden redaction policy. |
| CAP-UTL-009 | Dataframe and sequence helpers | `V1-CAP-UTILS-011`, `012`; common/dataframe_tools | `V2-FR-DF-*` | V1 duplicates conversions/comparisons and includes process-pool orchestration. | Merge | Pure lazy-loaded alignment, serialization, comparison, chunking, and parameter-combination helpers; no process orchestration in core. | Refactor | Preserve useful stateless operations while removing duplicate and heavyweight behavior. |
| CAP-UTL-010 | OHLCV diagnostic quality validation | `V1-CAP-UTILS-013`; `V1-WF-UTILS-009` | `V2-FR-DQ-*`, `V2-MATRIX-TOOL-001` | Three V1 implementations expose different issue/report contracts and no confirmed production gate. | Merge | One stateless native diagnostic engine plus one approved read-only official wrapper with bounded deterministic scoring. | Refactor | The checks are useful; consolidation and explicit workflow ownership are required. |
| CAP-UTL-011 | Schema and contract validation | `V1-CAP-UTILS-014`, `015`; `V1-WF-UTILS-007` | `V2-FR-SCHEMA-*`, `V2-MATRIX-TOOL-002..008` | V1 validators overlap and support only part of the proposed contract. | Merge | One native bounded validation engine and focused official wrappers for input, output, handoff, evidence, approval, registry, freshness, and artifact contracts. | Refactor | This preserves selective runtime use and removes duplicate semantics. |
| CAP-UTL-012 | Redaction and secret-safe diagnostics | `V1-CAP-UTILS-002`; security redaction | `V2-FR-SEC-001..027`, `V2-MATRIX-TOOL-009..010` | V1 has useful redaction but multiple native/tool names and inconsistent policies. | Modify | Non-mutating bounded native redaction plus explicit official wrappers; narrow audited allowlists; diagnostics reveal paths only. | Refactor | Proven value must be standardized without exposing secrets or mixing return shapes. |
| CAP-UTL-013 | Password hashing, encryption, and secret versions | `V1-CAP-UTILS-016`, `017`, `018`; `V1-WF-UTILS-002` | remaining `V2-FR-SEC-*` | Password hashing is used; encryption/version helpers are mostly test/example and key loading has bifurcated returns. | Modify | Native restricted helpers; Argon2id policy for passwords; explicit Fernet dependency/configuration; one key-loading contract; deterministic version conflict handling. | Refactor | Preserve the production credential workflow while tightening optional and sensitive behavior. |
| CAP-UTL-014 | Generic runtime settings | `V1-CAP-UTILS-019`; `V1-WF-UTILS-006` | `V2-FR-SET-*` | V1 settings are used but combine generic, live, and research concerns and lack advertised mapping/injection helpers. | Split | Immutable explicitly loaded generic utility settings with deterministic precedence and mapping injection. Live/research settings move out. | Refactor | The shared settings workflow is valuable; its current domain leakage is not. |
| CAP-UTL-015 | Internal auth context and tool authorization | `V1-CAP-UTILS-022`; no production workflow confirmed | `V2-FR-AUTH-*` | V1 has deny-by-default primitives but no tool allowlist integration; API authentication is separate. | Modify | Small immutable auth context and native deny-by-default role/permission/scope/tool checks. External identity verification stays outside. | Refactor | The safety contract is valid for official tool attachment, but external authentication is out of scope. |
| CAP-UTL-016 | In-process event bus | `V1-CAP-UTILS-023`; `V1-WF-UTILS-008` | `V2-FR-EVENT-*` | V1 bus is test-only, append-only, post-hoc timeout, and unbounded idempotency; V2 proposes a much larger subsystem. | Defer | No Event Bus in the initial rebuild. Later slice may add a bounded deterministic in-process bus after ownership and callers are confirmed. | Replace later | Current evidence does not justify retry, dead-letter, queue, timeout, and adapter complexity now. |
| CAP-UTL-017 | Error routing and notifications | `route_error`, `AlertDeduplicator`; notification functionality exists outside utils | `V2-FR-ALERT-*`, `V2-FR-NOTIFY-*` | No complete utils production workflow; provider ownership is unresolved. | Defer | Core keeps error-event construction only. Active routing, throttling, templates, and providers require a later cross-domain decision. | Refactor core; new later | The proposal is operational infrastructure, not a proven utility workflow. |
| CAP-UTL-018 | Metrics, health, clock drift, and circuit breakers | `V1-CAP-UTILS-024`, `025`, `026`; tests/examples only | `V2-FR-OBS-*`, `V2-FR-CB-*` | V1 is disconnected; V2 specifies extensive metrics and provider behavior. | Defer | Retain design constraints only. Implement a production slice when exporters/providers and acceptance thresholds are approved. | Refactor later | No current production integration or benchmark evidence supports immediate inclusion. |
| CAP-UTL-019 | Operational limits profile | Scattered limits across validators, redaction, event bus, and metrics | `V2-CFG-DEFAULT-001..017`, `V2-CFG-RULE-*` | No single authoritative profile or override validation. | Add | One immutable limits profile for accepted core validators/redaction/responses; production-only limits are added with their deferred capabilities. | New with selective constants | Bounded workloads are a measurable safety requirement. |
| CAP-UTL-020 | Domain-boundary cleanup | `V1-CAP-UTILS-010`, `020`, `021`; common/settings/errors leakage | ownership and does-not-own rules | Utils currently owns dataframe cache, live readiness, research models, domain errors, and Data-domain coupling. | Split | Move dataframe cache to Data, live readiness to Live, research models to Research, and domain errors to owners; keep only generic primitives. | Move/refactor | The final utility package must be dependency-neutral and focused. |

## 5. V1 Disposition Register

Every capability from the V1 audit is classified below.


| V1 capability ID | V1 capability | Current implementation | Current value | Decision | Final destination | Removal condition |
| --- | --- | --- | --- | --- | --- | --- |
| V1-CAP-UTILS-001 | Structured logging | `logger.py` | Essential | Modify | CAP-UTL-002 | None; preserve callers while replacing import-time configuration. |
| V1-CAP-UTILS-002 | Secret-safe logging | logger + security redaction | Essential | Merge | CAP-UTL-002 / CAP-UTL-012 | Remove duplicate sanitization only after leakage tests cover the unified path. |
| V1-CAP-UTILS-003 | Deterministic error contracts | `errors.py` | Essential | Split | CAP-UTL-003 | Move domain-specific errors only after consuming domains import their replacements. |
| V1-CAP-UTILS-004 | Standard tool envelopes | `standard.py` | Essential | Merge | CAP-UTL-004 | Remove the looser builder after all official tools pass one contract suite. |
| V1-CAP-UTILS-005 | Deterministic IDs/JSON | identity + standard | Supporting | Split | CAP-UTL-005 / CAP-UTL-008 | Delete broken aliases and duplicate serializer after package callers migrate. |
| V1-CAP-UTILS-006 | UTC/time normalization | `normalization.py` | Essential/supporting | Split | CAP-UTL-006 | Move board/domain policies only after owning domains accept them. |
| V1-CAP-UTILS-007 | Freshness/TTL evaluation | normalization + schema validation | Useful | Modify | CAP-UTL-006 / CAP-UTL-011 | Remove duplicate freshness wrappers after native and official contracts are mapped. |
| V1-CAP-UTILS-008 | Safe path normalization | `paths.py` | Essential | Keep | CAP-UTL-007 | No removal; preserve behavior and strengthen tests. |
| V1-CAP-UTILS-009 | Directory creation | paths/normalization | Essential | Merge | CAP-UTL-007 | Remove normalization duplicates after runtime callers use explicit `ensure_*` helpers. |
| V1-CAP-UTILS-010 | Dataframe caching | `common.py` | Essential to current CSV workflow | Remove | Data domain, not Utils | Verify `app.services.data` owns a bounded replacement and CSV callers are migrated. |
| V1-CAP-UTILS-011 | Dataframe conversion/comparison | common + dataframe_tools | Useful | Merge | CAP-UTL-009 | Delete duplicate implementations after behavior and no-mutation tests pass. |
| V1-CAP-UTILS-012 | Parameter expansion/chunk execution | common + dataframe_tools | Useful/questionable | Split | CAP-UTL-009; orchestration excluded | Verify no runtime caller needs process/thread execution; retain only pure sequence chunking and combinations. |
| V1-CAP-UTILS-013 | OHLCV quality validation | validators/data_quality/standard | Useful | Merge | CAP-UTL-010 | Remove old surfaces after one diagnostic contract covers all approved checks. |
| V1-CAP-UTILS-014 | Generic schema validation | schema_validation/validators | Useful | Merge | CAP-UTL-011 | Remove duplicates after field-path/resource-limit contract tests pass. |
| V1-CAP-UTILS-015 | Approval/handoff/registry validation | schema_validation/validators | Useful | Merge | CAP-UTL-011 | Remove duplicate wrappers after agent/workflow callers use the canonical tools. |
| V1-CAP-UTILS-016 | Password hashing/verification | `security.py` | Essential | Modify | CAP-UTL-013 | No deletion until database/API authentication passes migration tests. |
| V1-CAP-UTILS-017 | Symmetric encryption | `security.py` | Useful | Modify | CAP-UTL-013 | Remove legacy wrapper variants after one restricted native contract is accepted. |
| V1-CAP-UTILS-018 | Secret version selection | `security.py` | Useful | Modify | CAP-UTL-013 | Delete only duplicate/ambiguous branches after conflict tests pass. |
| V1-CAP-UTILS-019 | Shared application settings | `settings.py` | Essential | Split | CAP-UTL-014 | Move non-generic settings after consumers accept domain-owned configuration. |
| V1-CAP-UTILS-020 | Live config readiness | `settings.py::validate_config` | Useful | Remove | Live domain | Verify live runtime has its own readiness policy and no caller depends on utils validation. |
| V1-CAP-UTILS-021 | Research configuration models | `settings.py` | Useful, misplaced | Remove | Research domain | Verify research imports and persisted schemas migrate to the research owner. |
| V1-CAP-UTILS-022 | Authorization decisions | `auth.py` | Useful but disconnected | Modify | CAP-UTL-015 | Retain until tool-attachment boundary decides whether the helpers are adopted or moved. |
| V1-CAP-UTILS-023 | In-memory pub/sub | `event_bus.py` | Questionable | Defer | CAP-UTL-016 | Before deletion, confirm no dynamic publisher/subscriber and preserve tests as behavioral evidence. |
| V1-CAP-UTILS-024 | In-memory metrics | `observability.py` | Useful but disconnected | Defer | CAP-UTL-018 | Confirm no runtime exporter/registry caller before removal from the core slice. |
| V1-CAP-UTILS-025 | Circuit breaking | `observability.py` | Useful but disconnected | Defer | CAP-UTL-018 | Confirm no provider integration; reintroduce only with an accepted external boundary. |
| V1-CAP-UTILS-026 | Health/clock drift snapshots | `observability.py` | Useful | Defer | CAP-UTL-018 | Confirm no health endpoint consumes the current types. |
| V1-CAP-UTILS-027 | Public lazy facade | `__init__.py` | Essential but defective | Modify | CAP-UTL-001 | Delete fallback behavior only after strict registry contract tests cover every export. |
| V1-CAP-UTILS-028 | Multiprocess log routing | `logger.py` | Useful/possible | Defer | CAP-UTL-002 future extension | Confirm no production process-pool initializer uses it before deletion from initial scope. |

## 6. V2 Requirement Disposition Register

The source document contains no stable requirement IDs. IDs below were assigned during reconciliation.

### 6.1 Additional normative statements

This table covers purpose statements, ownership bullets, contract matrices, configuration-default rows, architecture prescriptions, and CI commands that were not represented by checkbox items.



#### Purpose and Scope


| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
| --- | --- | --- | --- | --- |
| V2-SCOPE-001 | Utils is the shared production-grade utility foundation for higher-level HaruQuantAI domains. | Modify | Keep a small cross-domain foundation limited to approved shared primitives. | The purpose is valid, but the proposed scope must exclude disconnected production infrastructure from the initial rebuild. |
| V2-SCOPE-002 | Utils may validate, normalize, redact, serialize, route events, report diagnostics, emit telemetry, and provide safe adapters, but must not own domain decisions or orchestration. | Modify | Keep the exclusion boundary; defer event routing, telemetry, and adapters until ownership and callers are confirmed. | The behavioral boundary is sound, while several listed capabilities are premature. |


#### Ownership


| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
| --- | --- | --- | --- | --- |
| V2-OWN-001 | Owns the shared `app/services/utils/` utility foundation for HaruQuantAI. | Keep | Retain this ownership item for the approved core capability. | It matches proven V1 value or a necessary cross-domain contract. |
| V2-OWN-002 | Owns structured logging primitives and logger configuration helpers. | Keep | Retain this ownership item for the approved core capability. | It matches proven V1 value or a necessary cross-domain contract. |
| V2-OWN-003 | Owns standard HaruQuant tool response envelopes, metadata, timing, and response schema validation. | Keep | Retain this ownership item for the approved core capability. | It matches proven V1 value or a necessary cross-domain contract. |
| V2-OWN-004 | Owns deterministic error types, error codes, and exception-to-envelope mapping support. | Keep | Retain this ownership item for the approved core capability. | It matches proven V1 value or a necessary cross-domain contract. |
| V2-OWN-005 | Owns request, workflow, correlation, causation, event, version, and idempotency helper primitives. | Keep | Retain this ownership item for the approved core capability. | It matches proven V1 value or a necessary cross-domain contract. |
| V2-OWN-006 | Owns UTC-first timestamp normalization, stale-data checks, and monotonic execution timing helpers. | Keep | Retain this ownership item for the approved core capability. | It matches proven V1 value or a necessary cross-domain contract. |
| V2-OWN-007 | Owns safe path handling and deterministic canonical JSON serialization. | Keep | Retain this ownership item for the approved core capability. | It matches proven V1 value or a necessary cross-domain contract. |
| V2-OWN-008 | Owns dataframe helper utilities and diagnostic-only OHLCV data-quality validation. | Modify | Own pure dataframe helpers and diagnostic-only OHLCV validation; caching/repair/persistence remain outside. | V1 contains useful behavior mixed with data-domain responsibilities. |
| V2-OWN-009 | Owns schema, payload, numeric range, freshness, evidence, approval, registry, handoff, and artifact-reference validation helpers. | Keep | Retain this ownership item for the approved core capability. | It matches proven V1 value or a necessary cross-domain contract. |
| V2-OWN-010 | Owns security utilities for redaction, password hashing/verification, encryption/decryption boundaries, and secret-version selection. | Keep | Retain this ownership item for the approved core capability. | It matches proven V1 value or a necessary cross-domain contract. |
| V2-OWN-011 | Owns runtime settings loading and injection with deterministic source precedence. | Modify | Utils owns generic immutable runtime settings only; live/research domain settings move out. | V1 settings are cross-domain and overloaded. |
| V2-OWN-012 | Owns auth-context validation and authorization support helpers, including deny-by-default behavior and tool allowlists. | Keep | Retain this ownership item for the approved core capability. | It matches proven V1 value or a necessary cross-domain contract. |
| V2-OWN-013 | Owns Event Bus and pub/sub primitives for utility, workflow, alert, and error-routing events. | Defer | Treat this ownership as provisional for the later production infrastructure slice; resolve external adapter ownership first. | V1 implementations are disconnected and the V2 document lists ownership questions. |
| V2-OWN-014 | Owns error-routing and alert-routing primitives. | Modify | Utils owns deterministic error-event construction and mapping; active routing/delivery is deferred. | This preserves core value without adding a routing subsystem prematurely. |
| V2-OWN-015 | Owns notification routing primitives for email, Telegram, and desktop channels. | Defer | Treat this ownership as provisional for the later production infrastructure slice; resolve external adapter ownership first. | V1 implementations are disconnected and the V2 document lists ownership questions. |
| V2-OWN-016 | Owns observability primitives for logs, metrics, health snapshots, trace correlation, Prometheus-compatible metrics, and Grafana dashboard expectations. | Defer | Treat this ownership as provisional for the later production infrastructure slice; resolve external adapter ownership first. | V1 implementations are disconnected and the V2 document lists ownership questions. |
| V2-OWN-017 | Owns provider-neutral contracts, DTOs, fake/test adapters, and in-process implementations unless an approved implementation ticket explicitly includes external providers. | Defer | Treat this ownership as provisional for the later production infrastructure slice; resolve external adapter ownership first. | V1 implementations are disconnected and the V2 document lists ownership questions. |
| V2-OWN-018 | Does not own trading strategy logic. | Keep | Retain this exclusion as a final domain boundary. | It prevents utility-domain leakage. |
| V2-OWN-019 | Does not own broker execution logic or live account mutation. | Keep | Retain this exclusion as a final domain boundary. | It prevents utility-domain leakage. |
| V2-OWN-020 | Does not own risk-governor decisions, portfolio allocation decisions, or strategy promotion decisions. | Keep | Retain this exclusion as a final domain boundary. | It prevents utility-domain leakage. |
| V2-OWN-021 | Does not approve, reject, place, close, modify, or cancel trades or orders. | Keep | Retain this exclusion as a final domain boundary. | It prevents utility-domain leakage. |
| V2-OWN-022 | Does not activate live systems or override kill switches. | Keep | Retain this exclusion as a final domain boundary. | It prevents utility-domain leakage. |
| V2-OWN-023 | Does not own application orchestration, UI behavior, database repositories, or backtest engines. | Keep | Retain this exclusion as a final domain boundary. | It prevents utility-domain leakage. |
| V2-OWN-024 | Does not repair, resample, enrich, persist, or clean market data; those workflows belong to `app.services.data`. | Keep | Retain this exclusion as a final domain boundary. | It prevents utility-domain leakage. |
| V2-OWN-025 | Does not act as an external identity provider or validate external identity-provider tokens unless an explicit adapter is supplied by the application layer. | Keep | Retain this exclusion as a final domain boundary. | It prevents utility-domain leakage. |
| V2-OWN-026 | Does not hard-code notification provider credentials or initialize external clients during import. | Keep | Retain this exclusion as a final domain boundary. | It prevents utility-domain leakage. |
| V2-OWN-027 | Does not own production external provider/client implementations unless they are approved as optional adapters for `app.services.utils`. | Keep | Retain this exclusion as a final domain boundary. | It prevents utility-domain leakage. |
| V2-OWN-028 | Does not expose every internal helper as an agent-callable tool. | Keep | Retain this exclusion as a final domain boundary. | It prevents utility-domain leakage. |
| V2-OWN-029 | Does not hide dependency behavior behind unclear compatibility shims, fallback modules, aliases, or duplicate wrapper modules. | Keep | Retain this exclusion as a final domain boundary. | It prevents utility-domain leakage. |


#### Official Tool Contract Matrix


| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
| --- | --- | --- | --- | --- |
| V2-MATRIX-TOOL-001 | Official tool contract for `validate_ohlcv_quality` with documented inputs, standard envelope, low-risk read-only flags, and controlled agent attachment. | Modify | Implement `validate_ohlcv_quality` as one explicit wrapper over a canonical native helper, with a generated contract entry and bounded diagnostics. | V1 has related behavior but duplicate or inconsistent contracts. |
| V2-MATRIX-TOOL-002 | Official tool contract for `validate_input_schema` with documented inputs, standard envelope, low-risk read-only flags, and controlled agent attachment. | Modify | Implement `validate_input_schema` as one explicit wrapper over a canonical native helper, with a generated contract entry and bounded diagnostics. | V1 has related behavior but duplicate or inconsistent contracts. |
| V2-MATRIX-TOOL-003 | Official tool contract for `validate_output_schema` with documented inputs, standard envelope, low-risk read-only flags, and controlled agent attachment. | Modify | Implement `validate_output_schema` as one explicit wrapper over a canonical native helper, with a generated contract entry and bounded diagnostics. | V1 has related behavior but duplicate or inconsistent contracts. |
| V2-MATRIX-TOOL-004 | Official tool contract for `validate_handoff_payload` with documented inputs, standard envelope, low-risk read-only flags, and controlled agent attachment. | Modify | Implement `validate_handoff_payload` as one explicit wrapper over a canonical native helper, with a generated contract entry and bounded diagnostics. | V1 has related behavior but duplicate or inconsistent contracts. |
| V2-MATRIX-TOOL-005 | Official tool contract for `validate_evidence_pack` with documented inputs, standard envelope, low-risk read-only flags, and controlled agent attachment. | Modify | Implement `validate_evidence_pack` as one explicit wrapper over a canonical native helper, with a generated contract entry and bounded diagnostics. | V1 has related behavior but duplicate or inconsistent contracts. |
| V2-MATRIX-TOOL-006 | Official tool contract for `validate_approval_packet` with documented inputs, standard envelope, low-risk read-only flags, and controlled agent attachment. | Modify | Implement `validate_approval_packet` as one explicit wrapper over a canonical native helper, with a generated contract entry and bounded diagnostics. | V1 has related behavior but duplicate or inconsistent contracts. |
| V2-MATRIX-TOOL-007 | Official tool contract for `validate_registry_entry` with documented inputs, standard envelope, low-risk read-only flags, and controlled agent attachment. | Modify | Implement `validate_registry_entry` as one explicit wrapper over a canonical native helper, with a generated contract entry and bounded diagnostics. | V1 has related behavior but duplicate or inconsistent contracts. |
| V2-MATRIX-TOOL-008 | Official tool contract for `validate_data_freshness` with documented inputs, standard envelope, low-risk read-only flags, and controlled agent attachment. | Modify | Implement `validate_data_freshness` as one explicit wrapper over a canonical native helper, with a generated contract entry and bounded diagnostics. | V1 has related behavior but duplicate or inconsistent contracts. |
| V2-MATRIX-TOOL-009 | Official tool contract for `redact_text_tool` with documented inputs, standard envelope, low-risk read-only flags, and controlled agent attachment. | Modify | Implement `redact_text_tool` as one explicit wrapper over a canonical native helper, with a generated contract entry and bounded diagnostics. | V1 has related behavior but duplicate or inconsistent contracts. |
| V2-MATRIX-TOOL-010 | Official tool contract for `redact_mapping_tool` with documented inputs, standard envelope, low-risk read-only flags, and controlled agent attachment. | Modify | Implement `redact_mapping_tool` as one explicit wrapper over a canonical native helper, with a generated contract entry and bounded diagnostics. | V1 has related behavior but duplicate or inconsistent contracts. |


#### Support Helper Contract Matrix


| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
| --- | --- | --- | --- | --- |
| V2-MATRIX-HELP-001 | `Logging helpers` classified as Core Required with the stated native return and side-effect policy. | Modify | Adopt a single native contract for `Logging helpers` with explicit side effects and typed errors. | V1 provides value but exposes duplicate or hybrid APIs. |
| V2-MATRIX-HELP-002 | `Standard response helpers` classified as Core Required with the stated native return and side-effect policy. | Modify | Adopt a single native contract for `Standard response helpers` with explicit side effects and typed errors. | V1 provides value but exposes duplicate or hybrid APIs. |
| V2-MATRIX-HELP-003 | `Error helpers` classified as Core Required with the stated native return and side-effect policy. | Modify | Adopt a single native contract for `Error helpers` with explicit side effects and typed errors. | V1 provides value but exposes duplicate or hybrid APIs. |
| V2-MATRIX-HELP-004 | `Identity/time helpers` classified as Core Required with the stated native return and side-effect policy. | Modify | Adopt a single native contract for `Identity/time helpers` with explicit side effects and typed errors. | V1 provides value but exposes duplicate or hybrid APIs. |
| V2-MATRIX-HELP-005 | `Path helpers` classified as Core Required with the stated native return and side-effect policy. | Modify | Adopt a single native contract for `Path helpers` with explicit side effects and typed errors. | V1 provides value but exposes duplicate or hybrid APIs. |
| V2-MATRIX-HELP-006 | `Dataframe helpers` classified as Core Required with the stated native return and side-effect policy. | Modify | Adopt a single native contract for `Dataframe helpers` with explicit side effects and typed errors. | V1 provides value but exposes duplicate or hybrid APIs. |
| V2-MATRIX-HELP-007 | `Native redaction helpers` classified as Core Required with the stated native return and side-effect policy. | Modify | Adopt a single native contract for `Native redaction helpers` with explicit side effects and typed errors. | V1 provides value but exposes duplicate or hybrid APIs. |
| V2-MATRIX-HELP-008 | `Hashing/encryption helpers` classified as Production Required with the stated native return and side-effect policy. | Modify | Keep native restricted helpers; password hashing remains core because V1 has a production caller, while optional encryption dependency behavior is explicit. | V1 behavior is valuable but fallback/return contracts need correction. |
| V2-MATRIX-HELP-009 | `Settings helpers` classified as Core Required with the stated native return and side-effect policy. | Modify | Adopt a single native contract for `Settings helpers` with explicit side effects and typed errors. | V1 provides value but exposes duplicate or hybrid APIs. |
| V2-MATRIX-HELP-010 | `Auth helpers` classified as Core Required with the stated native return and side-effect policy. | Modify | Adopt a single native contract for `Auth helpers` with explicit side effects and typed errors. | V1 provides value but exposes duplicate or hybrid APIs. |
| V2-MATRIX-HELP-011 | `Event Bus in-process helpers` classified as Production Required with the stated native return and side-effect policy. | Defer | Retain the `Event Bus in-process helpers` contract only for a later approved production/adapter slice. | No complete production caller is confirmed and ownership remains unresolved. |
| V2-MATRIX-HELP-012 | `External Event Bus adapters` classified as Optional Adapter with the stated native return and side-effect policy. | Defer | Retain the `External Event Bus adapters` contract only for a later approved production/adapter slice. | No complete production caller is confirmed and ownership remains unresolved. |
| V2-MATRIX-HELP-013 | `Notification routing helpers` classified as Production Required with the stated native return and side-effect policy. | Defer | Retain the `Notification routing helpers` contract only for a later approved production/adapter slice. | No complete production caller is confirmed and ownership remains unresolved. |
| V2-MATRIX-HELP-014 | `Real notification providers` classified as Optional Adapter with the stated native return and side-effect policy. | Defer | Retain the `Real notification providers` contract only for a later approved production/adapter slice. | No complete production caller is confirmed and ownership remains unresolved. |
| V2-MATRIX-HELP-015 | `Observability helpers` classified as Production Required with the stated native return and side-effect policy. | Defer | Retain the `Observability helpers` contract only for a later approved production/adapter slice. | No complete production caller is confirmed and ownership remains unresolved. |


#### Configuration Defaults Matrix


| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
| --- | --- | --- | --- | --- |
| V2-CFG-DEFAULT-001 | `MAX_PAYLOAD_SIZE_BYTES = 5242880` (Core Required). | Add | Add `MAX_PAYLOAD_SIZE_BYTES` to one immutable limits profile, subject to validated environment overrides. | V1 has scattered limits and no canonical profile. |
| V2-CFG-DEFAULT-002 | `MAX_VALIDATION_DEPTH = 20` (Core Required). | Add | Add `MAX_VALIDATION_DEPTH` to one immutable limits profile, subject to validated environment overrides. | V1 has scattered limits and no canonical profile. |
| V2-CFG-DEFAULT-003 | `MAX_FIELD_COUNT = 500` (Core Required). | Add | Add `MAX_FIELD_COUNT` to one immutable limits profile, subject to validated environment overrides. | V1 has scattered limits and no canonical profile. |
| V2-CFG-DEFAULT-004 | `MAX_ISSUE_COUNT = 100` (Core Required). | Add | Add `MAX_ISSUE_COUNT` to one immutable limits profile, subject to validated environment overrides. | V1 has scattered limits and no canonical profile. |
| V2-CFG-DEFAULT-005 | `MAX_SAMPLE_COUNT = 20` (Core Required). | Add | Add `MAX_SAMPLE_COUNT` to one immutable limits profile, subject to validated environment overrides. | V1 has scattered limits and no canonical profile. |
| V2-CFG-DEFAULT-006 | `MAX_RESPONSE_SIZE_BYTES = 1048576` (Core Required). | Add | Add `MAX_RESPONSE_SIZE_BYTES` to one immutable limits profile, subject to validated environment overrides. | V1 has scattered limits and no canonical profile. |
| V2-CFG-DEFAULT-007 | `MAX_REDACTION_DEPTH = 10` (Core Required). | Add | Add `MAX_REDACTION_DEPTH` to one immutable limits profile, subject to validated environment overrides. | V1 has scattered limits and no canonical profile. |
| V2-CFG-DEFAULT-008 | `MAX_STRING_LENGTH = 10000` (Core Required). | Add | Add `MAX_STRING_LENGTH` to one immutable limits profile, subject to validated environment overrides. | V1 has scattered limits and no canonical profile. |
| V2-CFG-DEFAULT-009 | `IDEMPOTENCY_TTL_SECONDS = 300` (Production Required). | Defer | Reserve `IDEMPOTENCY_TTL_SECONDS` for the corresponding production capability profile; validate before that slice is accepted. | The related production capability is deferred. |
| V2-CFG-DEFAULT-010 | `MAX_IDEMPOTENCY_CACHE_ENTRIES = 10000` (Production Required). | Defer | Reserve `MAX_IDEMPOTENCY_CACHE_ENTRIES` for the corresponding production capability profile; validate before that slice is accepted. | The related production capability is deferred. |
| V2-CFG-DEFAULT-011 | `EVENT_BUS_QUEUE_SIZE = 1000` (Production Required). | Defer | Reserve `EVENT_BUS_QUEUE_SIZE` for the corresponding production capability profile; validate before that slice is accepted. | The related production capability is deferred. |
| V2-CFG-DEFAULT-012 | `EVENT_HANDLER_TIMEOUT_MS = 5000` (Production Required). | Defer | Reserve `EVENT_HANDLER_TIMEOUT_MS` for the corresponding production capability profile; validate before that slice is accepted. | The related production capability is deferred. |
| V2-CFG-DEFAULT-013 | `ERROR_DEDUP_WINDOW_SECONDS = 300` (Production Required). | Defer | Reserve `ERROR_DEDUP_WINDOW_SECONDS` for the corresponding production capability profile; validate before that slice is accepted. | The related production capability is deferred. |
| V2-CFG-DEFAULT-014 | `NOTIFICATION_THROTTLE_WINDOW_SECONDS = 300` (Production Required). | Defer | Reserve `NOTIFICATION_THROTTLE_WINDOW_SECONDS` for the corresponding production capability profile; validate before that slice is accepted. | The related production capability is deferred. |
| V2-CFG-DEFAULT-015 | `METRIC_LABEL_MAX_DISTINCT_VALUES = 10` (Production Required). | Defer | Reserve `METRIC_LABEL_MAX_DISTINCT_VALUES` for the corresponding production capability profile; validate before that slice is accepted. | The related production capability is deferred. |
| V2-CFG-DEFAULT-016 | `CLOCK_DRIFT_WARNING_SECONDS = 1` (Production Required). | Defer | Reserve `CLOCK_DRIFT_WARNING_SECONDS` for the corresponding production capability profile; validate before that slice is accepted. | The related production capability is deferred. |
| V2-CFG-DEFAULT-017 | `CLOCK_DRIFT_CRITICAL_SECONDS = 5` (Production Required). | Defer | Reserve `CLOCK_DRIFT_CRITICAL_SECONDS` for the corresponding production capability profile; validate before that slice is accepted. | The related production capability is deferred. |


#### Architecture


| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
| --- | --- | --- | --- | --- |
| V2-ARCH-001 | Use the proposed `tools/utils/` target folder structure with flat utility files. | Open Decision | Resolve the authoritative package root first; then create only folders for approved capabilities, not the entire proposed flat tree. | The document alternates between `app/services/utils` and `tools/utils`, and includes deferred modules. |
| V2-ARCH-002 | Use the proposed class diagram with `InProcessEventBus`, `StandardToolEnvelope`, `Error`, and `Settings`. | Modify | Treat it as illustrative only; retain classes solely where state/lifecycle is required. | The diagram is not a sufficient behavioral contract and includes a deferred bus. |


#### CI Quality Gates


| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
| --- | --- | --- | --- | --- |
| V2-CI-001 | Run the listed partial CI commands using Black, isort, Flake8, mypy, pytest, and coverage. | Open Decision | Use the repository-approved quality toolchain and corrected package paths after system-level CI standards are confirmed. | The V1 audit did not establish the authoritative toolchain and the command paths reference `tools` inconsistently. |
| V2-CI-002 | Run the listed full-project gate with coverage targeting `tools`. | Open Decision | Use the authoritative project package and coverage target once package location is resolved. | The command conflicts with the V2 purpose path and cannot be accepted as written. |

### 6.2 Checklist requirement dispositions

All 1,164 checkbox requirements are classified below. Repeated requirements remain visible and map to the same final capability rather than disappearing silently.



#### 1.1 Assumptions


| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
| --- | --- | --- | --- | --- |
| V2-ASM-001 | This is a domain-level requirements document, not a sprint-specific requirements document. | Keep | Carry this assumption into the final domain contract. | It supports a clear utility boundary or import-safety rule. |
| V2-ASM-002 | The implementation is expected to be fresh and clean, with no backward-compatibility shims. | Keep | Carry this assumption into the final domain contract. | It supports a clear utility boundary or import-safety rule. |
| V2-ASM-003 | Support helpers remain native unless explicitly classified as official AI tools. | Keep | Carry this assumption into the final domain contract. | It supports a clear utility boundary or import-safety rule. |
| V2-ASM-004 | Conditional AI tools remain support helpers unless direct agent use is approved. | Keep | Carry this assumption into the final domain contract. | It supports a clear utility boundary or import-safety rule. |
| V2-ASM-005 | `app.services.data` will own repair, resampling, enrichment, persistence, and cleaning workflows for market data. | Keep | Carry this assumption into the final domain contract. | It supports a clear utility boundary or import-safety rule. |
| V2-ASM-006 | Data-quality market-calendar gap handling depends on session rules being supplied by a caller or future domain module. | Keep | Carry this assumption into the final domain contract. | It supports a clear utility boundary or import-safety rule. |
| V2-ASM-007 | Optional dependencies may or may not be installed; importability must remain intact either way. | Keep | Carry this assumption into the final domain contract. | It supports a clear utility boundary or import-safety rule. |
| V2-ASM-008 | The default OHLCV scoring model applies unless a later module-specific specification replaces it. | Modify | Treat the proposed score as the initial documented profile, configurable and replaceable by a versioned profile. | A fixed model is useful, but it should not become an unversioned global constant. |
| V2-ASM-009 | Strict schema-version enforcement occurs only when a caller or schema requires a version. | Keep | Carry this assumption into the final domain contract. | It supports a clear utility boundary or import-safety rule. |
| V2-ASM-010 | No UI, broker runtime, database repository, or LLM framework dependency is required inside `app.services.utils`. | Keep | Carry this assumption into the final domain contract. | It supports a clear utility boundary or import-safety rule. |
| V2-ASM-011 | The utils module will provide auth primitives and validation helpers, but the application or infrastructure layer will own external identity-provider integration. | Keep | Carry this assumption into the final domain contract. | It supports a clear utility boundary or import-safety rule. |
| V2-ASM-012 | The utils module will provide Event Bus contracts and an in-process implementation, while production broker-backed adapters may live in infrastructure modules or optional adapters. | Open Decision | Retain the boundary assumption but resolve provider and adapter ownership outside this document. | The source requirements identify ownership as unresolved. |
| V2-ASM-013 | The Event Bus is intended for utility, workflow, alert, and error-routing events, not direct trading execution. | Defer | Apply this assumption only to the later production infrastructure slice. | The related capability has no confirmed production caller in V1 and is excluded from the initial rebuild. |
| V2-ASM-014 | Notification helpers will provide routing contracts and adapter boundaries, not hard-coded provider credentials. | Defer | Apply this assumption only to the later production infrastructure slice. | The related capability has no confirmed production caller in V1 and is excluded from the initial rebuild. |
| V2-ASM-015 | Email, Telegram, and desktop notification providers will be configured explicitly per environment. | Defer | Apply this assumption only to the later production infrastructure slice. | The related capability has no confirmed production caller in V1 and is excluded from the initial rebuild. |
| V2-ASM-016 | Prometheus metrics export may be provided by application runtime, while utils provides metric registration and recording helpers. | Defer | Apply this assumption only to the later production infrastructure slice. | The related capability has no confirmed production caller in V1 and is excluded from the initial rebuild. |
| V2-ASM-017 | Grafana dashboards may be maintained as documentation or version-controlled dashboard definitions. | Defer | Apply this assumption only to the later production infrastructure slice. | The related capability has no confirmed production caller in V1 and is excluded from the initial rebuild. |
| V2-ASM-018 | Sensitive runtime settings and provider credentials are supplied through secure environment/configuration mechanisms. | Keep | Carry this assumption into the final domain contract. | It supports a clear utility boundary or import-safety rule. |
| V2-ASM-019 | No notification channel is enabled in production without explicit configuration. | Keep | Carry this assumption into the final domain contract. | It supports a clear utility boundary or import-safety rule. |
| V2-ASM-020 | Metrics and logs are operational telemetry and must not contain raw market payloads, secrets, or approval-packet contents. | Keep | Carry this assumption into the final domain contract. | It supports a clear utility boundary or import-safety rule. |


#### Official AI tools


| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
| --- | --- | --- | --- | --- |
| V2-API-TOOL-001 | `validate_ohlcv_quality` | Modify | Keep the named read-only tool, but implement it through one canonical native validator plus one explicit envelope wrapper and contract. | V1 contains overlapping or inconsistent versions that must be consolidated. |
| V2-API-TOOL-002 | `validate_input_schema` | Modify | Keep the named read-only tool, but implement it through one canonical native validator plus one explicit envelope wrapper and contract. | V1 contains overlapping or inconsistent versions that must be consolidated. |
| V2-API-TOOL-003 | `validate_output_schema` | Modify | Keep the named read-only tool, but implement it through one canonical native validator plus one explicit envelope wrapper and contract. | V1 contains overlapping or inconsistent versions that must be consolidated. |
| V2-API-TOOL-004 | `validate_handoff_payload` | Modify | Keep the named read-only tool, but implement it through one canonical native validator plus one explicit envelope wrapper and contract. | V1 contains overlapping or inconsistent versions that must be consolidated. |
| V2-API-TOOL-005 | `validate_evidence_pack` | Modify | Keep the named read-only tool, but implement it through one canonical native validator plus one explicit envelope wrapper and contract. | V1 contains overlapping or inconsistent versions that must be consolidated. |
| V2-API-TOOL-006 | `validate_approval_packet` | Modify | Keep the named read-only tool, but implement it through one canonical native validator plus one explicit envelope wrapper and contract. | V1 contains overlapping or inconsistent versions that must be consolidated. |
| V2-API-TOOL-007 | `validate_registry_entry` | Modify | Keep the named read-only tool, but implement it through one canonical native validator plus one explicit envelope wrapper and contract. | V1 contains overlapping or inconsistent versions that must be consolidated. |
| V2-API-TOOL-008 | `validate_data_freshness` | Modify | Keep the named read-only tool, but implement it through one canonical native validator plus one explicit envelope wrapper and contract. | V1 contains overlapping or inconsistent versions that must be consolidated. |
| V2-API-TOOL-009 | `redact_text_tool`, only for approved audit/log-redaction workflows. | Modify | Keep the named read-only tool, but implement it through one canonical native validator plus one explicit envelope wrapper and contract. | V1 contains overlapping or inconsistent versions that must be consolidated. |
| V2-API-TOOL-010 | `redact_mapping_tool`, only for approved audit/log-redaction workflows. | Modify | Keep the named read-only tool, but implement it through one canonical native validator plus one explicit envelope wrapper and contract. | V1 contains overlapping or inconsistent versions that must be consolidated. |


#### Support helpers and public support objects


| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
| --- | --- | --- | --- | --- |
| V2-API-HELP-001 | Project-wide `logger`, `get_logger`, and `configure_logging`. | Modify | Retain the capability as a native support API with one documented return/raise contract. | V1 provides value but exposes duplicate and hybrid contracts. |
| V2-API-HELP-002 | Standard response builders, metadata helpers, and `validate_tool_response_schema`. | Modify | Retain the capability as a native support API with one documented return/raise contract. | V1 provides value but exposes duplicate and hybrid contracts. |
| V2-API-HELP-003 | `Error` and shared deterministic exception classes. | Modify | Retain the capability as a native support API with one documented return/raise contract. | V1 provides value but exposes duplicate and hybrid contracts. |
| V2-API-HELP-004 | ID, request, workflow, correlation, causation, event, and version helpers. | Modify | Retain the capability as a native support API with one documented return/raise contract. | V1 provides value but exposes duplicate and hybrid contracts. |
| V2-API-HELP-005 | UTC timestamp, timezone, stale-data, and monotonic execution timing helpers. | Modify | Retain the capability as a native support API with one documented return/raise contract. | V1 provides value but exposes duplicate and hybrid contracts. |
| V2-API-HELP-006 | Safe path helpers such as `normalize_path`, `ensure_dir`, and `ensure_parent_dir`. | Modify | Retain the capability as a native support API with one documented return/raise contract. | V1 provides value but exposes duplicate and hybrid contracts. |
| V2-API-HELP-007 | Dataframe helpers such as datetime alignment, bar-to-record conversion, chunking, comparison, and dataframe-record serialization. | Modify | Retain the capability as a native support API with one documented return/raise contract. | V1 provides value but exposes duplicate and hybrid contracts. |
| V2-API-HELP-008 | Schema validation support helpers such as `validate_numeric_range` and `validate_required_fields`. | Modify | Retain the capability as a native support API with one documented return/raise contract. | V1 provides value but exposes duplicate and hybrid contracts. |
| V2-API-HELP-009 | Security helpers such as `redact_text_value`, `redact_mapping_value`, password hashing/verification, encryption/decryption, key loading, and secret-version selection. | Modify | Retain the capability as a native support API with one documented return/raise contract. | V1 provides value but exposes duplicate and hybrid contracts. |
| V2-API-HELP-010 | Runtime settings loaders and injection helpers. | Modify | Retain the capability as a native support API with one documented return/raise contract. | V1 provides value but exposes duplicate and hybrid contracts. |
| V2-API-HELP-011 | Auth-context validation and authorization helpers. | Modify | Retain the capability as a native support API with one documented return/raise contract. | V1 provides value but exposes duplicate and hybrid contracts. |
| V2-API-HELP-012 | Event Bus publish/subscribe, event envelope, idempotency, retry, dead-letter, queue, and diagnostic helpers. | Defer | Reserve the provider-neutral support surface for the production infrastructure slice after ownership is resolved. | V1 implementation is disconnected and the V2 class is Production Required. |
| V2-API-HELP-013 | Error-routing and notification-routing helpers. | Defer | Reserve the provider-neutral support surface for the production infrastructure slice after ownership is resolved. | V1 implementation is disconnected and the V2 class is Production Required. |
| V2-API-HELP-014 | Observability helpers for metrics, health checks, trace correlation, Prometheus-compatible metrics, and Grafana expectations. | Defer | Reserve the provider-neutral support surface for the production infrastructure slice after ownership is resolved. | V1 implementation is disconnected and the V2 class is Production Required. |


#### Public API rules


| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
| --- | --- | --- | --- | --- |
| V2-API-RULE-001 | `app/services/utils/__init__.py` is the public registry. | Modify | Use a strict explicit registry that raises immediately for missing exports and performs no fallback-module substitution. | V1 registry is essential but advertises broken names. |
| V2-API-RULE-002 | Only intentionally imported names listed in `__all__` may be public. | Keep | Adopt this public API rule as a final contract. | It directly corrects V1 ambiguity and accidental exports. |
| V2-API-RULE-003 | Public names must be classified as official AI tools or support helpers. | Keep | Adopt this public API rule as a final contract. | It directly corrects V1 ambiguity and accidental exports. |
| V2-API-RULE-004 | Official AI tools must return standard HaruQuant envelopes. | Keep | Adopt this public API rule as a final contract. | It directly corrects V1 ambiguity and accidental exports. |
| V2-API-RULE-005 | Support helpers may return native Python values. | Keep | Adopt this public API rule as a final contract. | It directly corrects V1 ambiguity and accidental exports. |
| V2-API-RULE-006 | Sensitive helpers such as `load_runtime_settings`, `encrypt_data`, and `decrypt_data` remain support helpers and must not be attached to agents by default. | Keep | Adopt this public API rule as a final contract. | It directly corrects V1 ambiguity and accidental exports. |
| V2-API-RULE-007 | Native helpers and official AI tool wrappers must not share the same public name when their return shapes differ. | Keep | Adopt this public API rule as a final contract. | It directly corrects V1 ambiguity and accidental exports. |


#### 3.2 Public API Contracts


| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
| --- | --- | --- | --- | --- |
| V2-API-CONTRACT-001 | Every public capability must have a contract entry before Builder handoff. | Add | Create a compact contract entry for every approved public symbol; generate tests from the same registry where practical. | V1 registry tests do not validate actual target attributes or public classification. |
| V2-API-CONTRACT-002 | Every contract entry must define callable name, module path, requirement class, public classification, stability status, accepted input types, required fields, optional fields, return shape, error behavior, side effects, risk level, network/filesystem/database/trading flags, and default agent-attachment status. | Add | Create a compact contract entry for every approved public symbol; generate tests from the same registry where practical. | V1 registry tests do not validate actual target attributes or public classification. |
| V2-API-CONTRACT-003 | Official AI tool contracts must include at least one success envelope example and one error envelope example. | Add | Create a compact contract entry for every approved public symbol; generate tests from the same registry where practical. | V1 registry tests do not validate actual target attributes or public classification. |
| V2-API-CONTRACT-004 | Support helper contracts must state whether the helper returns a native value, returns a native validation result, mutates an explicitly supplied target, or raises a typed HaruQuant exception. | Add | Create a compact contract entry for every approved public symbol; generate tests from the same registry where practical. | V1 registry tests do not validate actual target attributes or public classification. |
| V2-API-CONTRACT-005 | Official AI tools that accept dataframe-like data must document whether they accept pandas DataFrames, JSON-serializable records, artifact references, or multiple input modes. | Open Decision | Select approved agent input modes before attachment; keep native dataframe support separate from agent-safe inputs. | The V2 document explicitly leaves this unresolved. |
| V2-API-CONTRACT-006 | Official AI tools must reject non-agent-safe input modes when invoked through an agent attachment. | Open Decision | Select approved agent input modes before attachment; keep native dataframe support separate from agent-safe inputs. | The V2 document explicitly leaves this unresolved. |
| V2-API-CONTRACT-007 | Official AI tools must document schema version and compatibility policy. | Add | Create a compact contract entry for every approved public symbol; generate tests from the same registry where practical. | V1 registry tests do not validate actual target attributes or public classification. |
| V2-API-CONTRACT-008 | Official AI tools must document whether the output `data` payload is stable, experimental, or diagnostic-only. | Add | Create a compact contract entry for every approved public symbol; generate tests from the same registry where practical. | V1 registry tests do not validate actual target attributes or public classification. |


#### Configuration Defaults


| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
| --- | --- | --- | --- | --- |
| V2-CFG-RULE-001 | The implementation must expose these values through a single configuration profile or settings object. | Add | Centralize approved limits in one immutable utility configuration profile and validate overrides. | V1 has scattered limits and no single authoritative profile. |
| V2-CFG-RULE-002 | Environment overrides must be validated against safe minimum and maximum ranges. | Add | Centralize approved limits in one immutable utility configuration profile and validate overrides. | V1 has scattered limits and no single authoritative profile. |
| V2-CFG-RULE-003 | Production acceptance must either approve these defaults or document approved replacement values. | Add | Centralize approved limits in one immutable utility configuration profile and validate overrides. | V1 has scattered limits and no single authoritative profile. |
| V2-CFG-RULE-004 | Tests must assert behavior against the active configuration profile rather than hard-coded duplicate constants. | Add | Centralize approved limits in one immutable utility configuration profile and validate overrides. | V1 has scattered limits and no single authoritative profile. |
| V2-CFG-RULE-005 | Official AI tools must return bounded diagnostics when these limits are reached. | Add | Centralize approved limits in one immutable utility configuration profile and validate overrides. | V1 has scattered limits and no single authoritative profile. |


#### Module Foundation and Scope


| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
| --- | --- | --- | --- | --- |
| V2-FR-FOUND-001 | The system must implement `app/services/utils/` as the shared utility foundation for HaruQuantAI. | Modify | Preserve the behavior but consolidate duplicate implementations and remove domain-specific leakage. | V1 provides partial or valuable behavior with structural defects. |
| V2-FR-FOUND-002 | The module must support higher-level domains including data, research, simulation, risk, portfolio, execution, analytics, governance, and agentic workflows. | Modify | Preserve the behavior but consolidate duplicate implementations and remove domain-specific leakage. | V1 provides partial or valuable behavior with structural defects. |
| V2-FR-FOUND-003 | The module must provide project-wide structured logging. | Modify | Preserve the behavior but consolidate duplicate implementations and remove domain-specific leakage. | V1 provides partial or valuable behavior with structural defects. |
| V2-FR-FOUND-004 | The module must provide standard HaruQuant tool response envelopes. | Modify | Preserve the behavior but consolidate duplicate implementations and remove domain-specific leakage. | V1 provides partial or valuable behavior with structural defects. |
| V2-FR-FOUND-005 | The module must provide deterministic error codes and exception mapping. | Modify | Preserve the behavior but consolidate duplicate implementations and remove domain-specific leakage. | V1 provides partial or valuable behavior with structural defects. |
| V2-FR-FOUND-006 | The module must provide request, workflow, generic ID, version, correlation ID, causation ID, and idempotency helpers. | Modify | Preserve the behavior but consolidate duplicate implementations and remove domain-specific leakage. | V1 provides partial or valuable behavior with structural defects. |
| V2-FR-FOUND-007 | The module must provide shared status, severity, risk-level, environment-mode, auth, event, notification, and health-state constants. | Modify | Centralize only genuinely cross-domain constants; keep event, notification, and health-specific states with their deferred capabilities. | A single constants catalogue would recreate cross-domain coupling. |
| V2-FR-FOUND-008 | The module must provide timestamp and timezone normalization using a UTC-first policy. | Modify | Preserve the behavior but consolidate duplicate implementations and remove domain-specific leakage. | V1 provides partial or valuable behavior with structural defects. |
| V2-FR-FOUND-009 | The module must provide safe path handling. | Modify | Preserve the behavior but consolidate duplicate implementations and remove domain-specific leakage. | V1 provides partial or valuable behavior with structural defects. |
| V2-FR-FOUND-010 | The module must provide canonical JSON serialization for audit, hashing, caching, reproducible tests, and comparison workflows. | Modify | Preserve the behavior but consolidate duplicate implementations and remove domain-specific leakage. | V1 provides partial or valuable behavior with structural defects. |
| V2-FR-FOUND-011 | The module must provide dataframe and OHLCV helper utilities. | Modify | Preserve the behavior but consolidate duplicate implementations and remove domain-specific leakage. | V1 provides partial or valuable behavior with structural defects. |
| V2-FR-FOUND-012 | The module must provide OHLCV data-quality validation with bounded diagnostics and deterministic scoring. | Modify | Preserve the behavior but consolidate duplicate implementations and remove domain-specific leakage. | V1 provides partial or valuable behavior with structural defects. |
| V2-FR-FOUND-013 | The module must provide schema, payload, risk-level, numeric-range, and contract validation. | Modify | Preserve the behavior but consolidate duplicate implementations and remove domain-specific leakage. | V1 provides partial or valuable behavior with structural defects. |
| V2-FR-FOUND-014 | The module must provide security helpers for redaction, hashing, encryption, decryption, and secret-version selection. | Modify | Preserve the behavior but consolidate duplicate implementations and remove domain-specific leakage. | V1 provides partial or valuable behavior with structural defects. |
| V2-FR-FOUND-015 | The module must provide runtime settings loading and injection with deterministic source precedence. | Modify | Preserve the behavior but consolidate duplicate implementations and remove domain-specific leakage. | V1 provides partial or valuable behavior with structural defects. |
| V2-FR-FOUND-016 | The module must provide standard execution timing helpers for consistent `execution_ms` values. | Modify | Preserve the behavior but consolidate duplicate implementations and remove domain-specific leakage. | V1 provides partial or valuable behavior with structural defects. |
| V2-FR-FOUND-017 | The module must provide explicit tool-response schema validation constants. | Add | Add the bounded contract behavior to the canonical core capability. | The V1 audit did not confirm a complete implementation. |
| V2-FR-FOUND-018 | The module must provide schema-version compatibility checks for validation contracts. | Add | Add the bounded contract behavior to the canonical core capability. | The V1 audit did not confirm a complete implementation. |
| V2-FR-FOUND-019 | The module must provide resource-limit controls for large validation workloads. | Add | Add the bounded contract behavior to the canonical core capability. | The V1 audit did not confirm a complete implementation. |
| V2-FR-FOUND-020 | The module must support lazy loading for pandas and other heavy optional dependencies. | Modify | Preserve the behavior but consolidate duplicate implementations and remove domain-specific leakage. | V1 provides partial or valuable behavior with structural defects. |
| V2-FR-FOUND-021 | The module must preserve a stateless, diagnostic-only data-quality boundary. | Modify | Preserve the behavior but consolidate duplicate implementations and remove domain-specific leakage. | V1 provides partial or valuable behavior with structural defects. |
| V2-FR-FOUND-022 | The module must support string-serializable constants and enum-friendly canonicalization. | Add | Add the bounded contract behavior to the canonical core capability. | The V1 audit did not confirm a complete implementation. |
| V2-FR-FOUND-023 | The module must support extensible domain error mapping through `Error` and compatible `code` attributes. | Modify | Preserve the behavior but consolidate duplicate implementations and remove domain-specific leakage. | V1 provides partial or valuable behavior with structural defects. |
| V2-FR-FOUND-024 | The module must provide auth context validation and authorization support helpers. | Modify | Preserve the behavior but consolidate duplicate implementations and remove domain-specific leakage. | V1 provides partial or valuable behavior with structural defects. |
| V2-FR-FOUND-025 | The module must provide Event Bus and pub/sub primitives. | Defer | Exclude from the initial rebuild; retain as a production-slice candidate with provider-neutral boundaries. | V1 implementation is disconnected and the V2 capability is operational infrastructure. |
| V2-FR-FOUND-026 | The module must provide early alert routing and error routing so the rest of the system can report issues consistently. | Defer | Exclude from the initial rebuild; retain as a production-slice candidate with provider-neutral boundaries. | V1 implementation is disconnected and the V2 capability is operational infrastructure. |
| V2-FR-FOUND-027 | The module must provide notification routing primitives for email, Telegram, and desktop channels. | Defer | Exclude from the initial rebuild; retain as a production-slice candidate with provider-neutral boundaries. | V1 implementation is disconnected and the V2 capability is operational infrastructure. |
| V2-FR-FOUND-028 | The module must provide observability primitives for logs, metrics, health snapshots, and trace correlation. | Defer | Exclude from the initial rebuild; retain as a production-slice candidate with provider-neutral boundaries. | V1 implementation is disconnected and the V2 capability is operational infrastructure. |
| V2-FR-FOUND-029 | The module must provide Prometheus-compatible system-health metrics. | Defer | Exclude from the initial rebuild; retain as a production-slice candidate with provider-neutral boundaries. | V1 implementation is disconnected and the V2 capability is operational infrastructure. |
| V2-FR-FOUND-030 | The module must define Grafana dashboard expectations for operational health. | Defer | Exclude from the initial rebuild; retain as a production-slice candidate with provider-neutral boundaries. | V1 implementation is disconnected and the V2 capability is operational infrastructure. |


#### Public API and Registry


| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
| --- | --- | --- | --- | --- |
| V2-FR-REG-001 | `app/services/utils/__init__.py` must act as the public registry for the utility domain. | Modify | Implement a strict, explicit, side-effect-free registry with no fallback aliases or duplicate wrappers. | This directly fixes V1 registry defects. |
| V2-FR-REG-002 | Only intentionally imported names listed in `__all__` may be public. | Keep | Adopt as a final public API governance rule. | The rule supports a small and auditable surface. |
| V2-FR-REG-003 | Public names must be classified as either official AI tools or support objects/helpers. | Keep | Adopt as a final public API governance rule. | The rule supports a small and auditable surface. |
| V2-FR-REG-004 | Official AI tools must return the standard HaruQuant tool envelope. | Keep | Adopt as a final public API governance rule. | The rule supports a small and auditable surface. |
| V2-FR-REG-005 | Support helpers may return native Python values when they are not agent-callable tools. | Keep | Adopt as a final public API governance rule. | The rule supports a small and auditable surface. |
| V2-FR-REG-006 | The logger must be exported as a support object and must not be treated as an official AI tool. | Keep | Adopt as a final public API governance rule. | The rule supports a small and auditable surface. |
| V2-FR-REG-007 | Auth, Event Bus, notification, and observability primitives must be support helpers by default unless explicitly promoted to official AI tools. | Keep | Adopt as a final public API governance rule. | The rule supports a small and auditable surface. |
| V2-FR-REG-008 | Internal helpers must remain private unless explicitly intended for public import. | Keep | Adopt as a final public API governance rule. | The rule supports a small and auditable surface. |
| V2-FR-REG-009 | No accidental public exports may exist. | Modify | Implement a strict, explicit, side-effect-free registry with no fallback aliases or duplicate wrappers. | This directly fixes V1 registry defects. |
| V2-FR-REG-010 | No compatibility shims, aliases, fallback import modules, or duplicate wrapper modules may exist. | Modify | Implement a strict, explicit, side-effect-free registry with no fallback aliases or duplicate wrappers. | This directly fixes V1 registry defects. |
| V2-FR-REG-011 | New public exports must be justified by real cross-domain reuse. | Keep | Adopt as a final public API governance rule. | The rule supports a small and auditable surface. |
| V2-FR-REG-012 | Public exports may not be renamed or removed after v8 acceptance without a new versioned specification and registry review. | Reject | Use semantic versioning and registry review from the first accepted public contract; remove the unexplained `v8` milestone. | The milestone is undefined and adds arbitrary policy. |


#### Official AI Tools


| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
| --- | --- | --- | --- | --- |
| V2-FR-TOOL-001 | `validate_ohlcv_quality` must be implemented as a low-risk, read-only official AI tool. | Modify | Implement through a canonical wrapper with request ID, timing, metadata, deterministic errors, and no silent failure. | V1 tools exist but contracts are inconsistent. |
| V2-FR-TOOL-002 | `validate_input_schema` must be implemented as a low-risk, read-only official AI tool. | Modify | Implement through a canonical wrapper with request ID, timing, metadata, deterministic errors, and no silent failure. | V1 tools exist but contracts are inconsistent. |
| V2-FR-TOOL-003 | `validate_output_schema` must be implemented as a low-risk, read-only official AI tool. | Modify | Implement through a canonical wrapper with request ID, timing, metadata, deterministic errors, and no silent failure. | V1 tools exist but contracts are inconsistent. |
| V2-FR-TOOL-004 | `validate_handoff_payload` must be implemented as a low-risk, read-only official AI tool. | Modify | Implement through a canonical wrapper with request ID, timing, metadata, deterministic errors, and no silent failure. | V1 tools exist but contracts are inconsistent. |
| V2-FR-TOOL-005 | `validate_evidence_pack` must be implemented as a low-risk, read-only official AI tool. | Modify | Implement through a canonical wrapper with request ID, timing, metadata, deterministic errors, and no silent failure. | V1 tools exist but contracts are inconsistent. |
| V2-FR-TOOL-006 | `validate_approval_packet` must be implemented as a low-risk, read-only official AI tool. | Modify | Implement through a canonical wrapper with request ID, timing, metadata, deterministic errors, and no silent failure. | V1 tools exist but contracts are inconsistent. |
| V2-FR-TOOL-007 | `validate_registry_entry` must be implemented as a low-risk, read-only official AI tool. | Modify | Implement through a canonical wrapper with request ID, timing, metadata, deterministic errors, and no silent failure. | V1 tools exist but contracts are inconsistent. |
| V2-FR-TOOL-008 | `validate_data_freshness` must be implemented as a low-risk, read-only official AI tool. | Modify | Implement through a canonical wrapper with request ID, timing, metadata, deterministic errors, and no silent failure. | V1 tools exist but contracts are inconsistent. |
| V2-FR-TOOL-009 | `redact_text_tool` must be classified as a low-risk, read-only official AI tool only for approved audit/log-redaction workflows. | Modify | Implement through a canonical wrapper with request ID, timing, metadata, deterministic errors, and no silent failure. | V1 tools exist but contracts are inconsistent. |
| V2-FR-TOOL-010 | `redact_mapping_tool` must be classified as a low-risk, read-only official AI tool only for approved audit/log-redaction workflows. | Modify | Implement through a canonical wrapper with request ID, timing, metadata, deterministic errors, and no silent failure. | V1 tools exist but contracts are inconsistent. |
| V2-FR-TOOL-011 | Native redaction helpers such as `redact_text_value` and `redact_mapping_value` must return native redacted values and remain support helpers. | Modify | Implement through a canonical wrapper with request ID, timing, metadata, deterministic errors, and no silent failure. | V1 tools exist but contracts are inconsistent. |
| V2-FR-TOOL-012 | Native redaction helpers must not be attached to agents by default unless wrapped by an approved official AI tool. | Modify | Implement through a canonical wrapper with request ID, timing, metadata, deterministic errors, and no silent failure. | V1 tools exist but contracts are inconsistent. |
| V2-FR-TOOL-013 | Native helper names and official AI tool wrapper names must not collide when return shapes differ. | Modify | Implement through a canonical wrapper with request ID, timing, metadata, deterministic errors, and no silent failure. | V1 tools exist but contracts are inconsistent. |
| V2-FR-TOOL-014 | `load_runtime_settings` must remain a support helper and must not be attached to agents by default. | Keep | Keep runtime settings as a native restricted support helper, never an agent tool. | Settings may expose sensitive configuration. |
| V2-FR-TOOL-015 | `encrypt_data` must remain a restricted support helper and must not be attached to agents by default. | Keep | Keep encryption helpers restricted and require explicit authorization/audit before any future agent exposure. | This is a necessary safety boundary. |
| V2-FR-TOOL-016 | `decrypt_data` must remain a restricted support helper and must not be attached to agents by default. | Keep | Keep encryption helpers restricted and require explicit authorization/audit before any future agent exposure. | This is a necessary safety boundary. |
| V2-FR-TOOL-017 | Agent access to encryption or decryption must require explicit security approval, permission checks, and audit logging. | Keep | Keep encryption helpers restricted and require explicit authorization/audit before any future agent exposure. | This is a necessary safety boundary. |
| V2-FR-TOOL-018 | Official AI tools must include `request_id: str \| None = None`. | Modify | Implement through a canonical wrapper with request ID, timing, metadata, deterministic errors, and no silent failure. | V1 tools exist but contracts are inconsistent. |
| V2-FR-TOOL-019 | Official AI tools must include tool metadata. | Modify | Implement through a canonical wrapper with request ID, timing, metadata, deterministic errors, and no silent failure. | V1 tools exist but contracts are inconsistent. |
| V2-FR-TOOL-020 | Official AI tools must include risk and side-effect flags. | Modify | Implement through a canonical wrapper with request ID, timing, metadata, deterministic errors, and no silent failure. | V1 tools exist but contracts are inconsistent. |
| V2-FR-TOOL-021 | Official AI tools must validate inputs. | Modify | Implement through a canonical wrapper with request ID, timing, metadata, deterministic errors, and no silent failure. | V1 tools exist but contracts are inconsistent. |
| V2-FR-TOOL-022 | Official AI tools must measure execution timing. | Modify | Implement through a canonical wrapper with request ID, timing, metadata, deterministic errors, and no silent failure. | V1 tools exist but contracts are inconsistent. |
| V2-FR-TOOL-023 | Official AI tools must use structured logging. | Modify | Implement through a canonical wrapper with request ID, timing, metadata, deterministic errors, and no silent failure. | V1 tools exist but contracts are inconsistent. |
| V2-FR-TOOL-024 | Official AI tools must return the standard response schema. | Modify | Implement through a canonical wrapper with request ID, timing, metadata, deterministic errors, and no silent failure. | V1 tools exist but contracts are inconsistent. |
| V2-FR-TOOL-025 | Official AI tools must use deterministic error codes. | Modify | Implement through a canonical wrapper with request ID, timing, metadata, deterministic errors, and no silent failure. | V1 tools exist but contracts are inconsistent. |
| V2-FR-TOOL-026 | Official AI tools must not fail silently. | Modify | Implement through a canonical wrapper with request ID, timing, metadata, deterministic errors, and no silent failure. | V1 tools exist but contracts are inconsistent. |
| V2-FR-TOOL-027 | Agents may call only approved official AI tools through approved tool attachment. | Keep | Enforce explicit tool allowlists at attachment and invocation boundaries. | This is a confirmed safety constraint. |


#### Standard Tool Response


| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
| --- | --- | --- | --- | --- |
| V2-FR-RESP-001 | Every official AI tool must return the top-level keys `status`, `message`, `data`, `error`, and `metadata`. | Modify | Consolidate to one standard envelope schema and one validator; remove the looser parallel builder. | V1 has two response-building styles with different semantics. |
| V2-FR-RESP-002 | `status` must be either `success` or `error`. | Modify | Consolidate to one standard envelope schema and one validator; remove the looser parallel builder. | V1 has two response-building styles with different semantics. |
| V2-FR-RESP-003 | `message` must be a string. | Modify | Consolidate to one standard envelope schema and one validator; remove the looser parallel builder. | V1 has two response-building styles with different semantics. |
| V2-FR-RESP-004 | `error` must be either `None` or a mapping with `code` and `details`. | Modify | Consolidate to one standard envelope schema and one validator; remove the looser parallel builder. | V1 has two response-building styles with different semantics. |
| V2-FR-RESP-005 | `metadata` must include `tool_name`, `tool_version`, `tool_category`, `tool_risk_level`, `request_id`, `execution_ms`, `read_only`, `writes_file`, `modifies_database`, `places_trade`, and `requires_network`. | Modify | Consolidate to one standard envelope schema and one validator; remove the looser parallel builder. | V1 has two response-building styles with different semantics. |
| V2-FR-RESP-006 | Standard response validation must reject missing top-level keys. | Modify | Consolidate to one standard envelope schema and one validator; remove the looser parallel builder. | V1 has two response-building styles with different semantics. |
| V2-FR-RESP-007 | Standard response validation must reject missing metadata keys. | Modify | Consolidate to one standard envelope schema and one validator; remove the looser parallel builder. | V1 has two response-building styles with different semantics. |
| V2-FR-RESP-008 | Standard response validation must reject invalid statuses. | Modify | Consolidate to one standard envelope schema and one validator; remove the looser parallel builder. | V1 has two response-building styles with different semantics. |
| V2-FR-RESP-009 | Standard response validation must reject malformed errors. | Modify | Consolidate to one standard envelope schema and one validator; remove the looser parallel builder. | V1 has two response-building styles with different semantics. |
| V2-FR-RESP-010 | Standard response validation should validate error codes against the approved error-code set where practical. | Modify | Consolidate to one standard envelope schema and one validator; remove the looser parallel builder. | V1 has two response-building styles with different semantics. |
| V2-FR-RESP-011 | `get_execution_ms(start_time)` must calculate execution duration consistently for official tools. | Modify | Consolidate to one standard envelope schema and one validator; remove the looser parallel builder. | V1 has two response-building styles with different semantics. |
| V2-FR-RESP-012 | `get_execution_ms(start_time)` must use a monotonic clock source such as `time.perf_counter()`. | Modify | Consolidate to one standard envelope schema and one validator; remove the looser parallel builder. | V1 has two response-building styles with different semantics. |
| V2-FR-RESP-013 | `get_execution_ms(start_time)` must return milliseconds rounded to three decimals. | Modify | Consolidate to one standard envelope schema and one validator; remove the looser parallel builder. | V1 has two response-building styles with different semantics. |


#### Logging


| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
| --- | --- | --- | --- | --- |
| V2-FR-LOG-001 | The module must expose a project-wide `logger`. | Modify | Preserve structured, secret-safe logging but make configuration explicit, import-safe, bounded, and settings-driven. | V1 logging is widely used but configures file sinks during import. |
| V2-FR-LOG-002 | The module must expose `get_logger(name: str \| None = None)`. | Modify | Preserve structured, secret-safe logging but make configuration explicit, import-safe, bounded, and settings-driven. | V1 logging is widely used but configures file sinks during import. |
| V2-FR-LOG-003 | The module must expose `configure_logging(level: str \| int = "INFO")`. | Modify | Preserve structured, secret-safe logging but make configuration explicit, import-safe, bounded, and settings-driven. | V1 logging is widely used but configures file sinks during import. |
| V2-FR-LOG-004 | Logging must use Python `logging`. | Modify | Use a standard-library logging-compatible backend and public API; do not require a second compatibility adapter layer. | V1's structlog compatibility layer is oversized and has import-time side effects. |
| V2-FR-LOG-005 | Logging must use structured JSON-compatible output for production runtime events. | Modify | Preserve structured, secret-safe logging but make configuration explicit, import-safe, bounded, and settings-driven. | V1 logging is widely used but configures file sinks during import. |
| V2-FR-LOG-006 | Production logging must use a JSON-compatible structured formatter. | Modify | Preserve structured, secret-safe logging but make configuration explicit, import-safe, bounded, and settings-driven. | V1 logging is widely used but configures file sinks during import. |
| V2-FR-LOG-007 | Local development console logging must support colorized human-readable output. | Modify | Preserve structured, secret-safe logging but make configuration explicit, import-safe, bounded, and settings-driven. | V1 logging is widely used but configures file sinks during import. |
| V2-FR-LOG-008 | Human-readable console log lines must use the format `datetime \| level \| module.submodule.filename:function:line \| message`. | Modify | Preserve structured, secret-safe logging but make configuration explicit, import-safe, bounded, and settings-driven. | V1 logging is widely used but configures file sinks during import. |
| V2-FR-LOG-009 | Human-readable console timestamps must use the format `YYYY-MM-DD HH:MM:SS`. | Modify | Preserve structured, secret-safe logging but make configuration explicit, import-safe, bounded, and settings-driven. | V1 logging is widely used but configures file sinks during import. |
| V2-FR-LOG-010 | Logging must include `timestamp`, `level`, `logger_name`, `message`, `event_name`, `module`, `function`, `request_id`, `workflow_id`, `correlation_id`, and `error_code` where available. | Modify | Preserve structured, secret-safe logging but make configuration explicit, import-safe, bounded, and settings-driven. | V1 logging is widely used but configures file sinks during import. |
| V2-FR-LOG-011 | Human-readable console logging must include source line numbers where available. | Modify | Preserve structured, secret-safe logging but make configuration explicit, import-safe, bounded, and settings-driven. | V1 logging is widely used but configures file sinks during import. |
| V2-FR-LOG-012 | Logging must support child loggers per module while preserving a stable root logger name. | Modify | Preserve structured, secret-safe logging but make configuration explicit, import-safe, bounded, and settings-driven. | V1 logging is widely used but configures file sinks during import. |
| V2-FR-LOG-013 | Logging configuration must avoid duplicate handlers. | Modify | Preserve structured, secret-safe logging but make configuration explicit, import-safe, bounded, and settings-driven. | V1 logging is widely used but configures file sinks during import. |
| V2-FR-LOG-014 | Logging configuration must happen only through an explicit configuration function. | Modify | Preserve structured, secret-safe logging but make configuration explicit, import-safe, bounded, and settings-driven. | V1 logging is widely used but configures file sinks during import. |
| V2-FR-LOG-015 | Importing logger utilities must not force application-level logging configuration. | Modify | Preserve structured, secret-safe logging but make configuration explicit, import-safe, bounded, and settings-driven. | V1 logging is widely used but configures file sinks during import. |
| V2-FR-LOG-016 | File logging must be opt-in and configured explicitly through runtime settings or `configure_logging`. | Modify | Preserve structured, secret-safe logging but make configuration explicit, import-safe, bounded, and settings-driven. | V1 logging is widely used but configures file sinks during import. |
| V2-FR-LOG-017 | File logging must write only to configured log directories that are normalized through safe path handling. | Modify | Preserve structured, secret-safe logging but make configuration explicit, import-safe, bounded, and settings-driven. | V1 logging is widely used but configures file sinks during import. |
| V2-FR-LOG-018 | File logging must use rotating log files when enabled. | Modify | Preserve structured, secret-safe logging but make configuration explicit, import-safe, bounded, and settings-driven. | V1 logging is widely used but configures file sinks during import. |
| V2-FR-LOG-019 | Log rotation must support configurable maximum file size and maximum retained file count. | Modify | Preserve structured, secret-safe logging but make configuration explicit, import-safe, bounded, and settings-driven. | V1 logging is widely used but configures file sinks during import. |
| V2-FR-LOG-020 | Log retention must support configurable deletion of old rotated log files. | Modify | Preserve structured, secret-safe logging but make configuration explicit, import-safe, bounded, and settings-driven. | V1 logging is widely used but configures file sinks during import. |
| V2-FR-LOG-021 | Log retention deletion must be bounded to configured log directories and must not delete arbitrary files. | Modify | Preserve structured, secret-safe logging but make configuration explicit, import-safe, bounded, and settings-driven. | V1 logging is widely used but configures file sinks during import. |
| V2-FR-LOG-022 | Log file writes, rotation, and retention deletion must degrade safely if the filesystem or logging sink fails. | Modify | Preserve structured, secret-safe logging but make configuration explicit, import-safe, bounded, and settings-driven. | V1 logging is widely used but configures file sinks during import. |
| V2-FR-LOG-023 | Logging must avoid writing secrets. | Modify | Preserve structured, secret-safe logging but make configuration explicit, import-safe, bounded, and settings-driven. | V1 logging is widely used but configures file sinks during import. |
| V2-FR-LOG-024 | Log-level configuration must be controlled by runtime settings. | Modify | Preserve structured, secret-safe logging but make configuration explicit, import-safe, bounded, and settings-driven. | V1 logging is widely used but configures file sinks during import. |
| V2-FR-LOG-025 | Production files must log function/tool calls, validation failures, successful completions, recoverable warnings, and execution failures where applicable. | Modify | Log meaningful lifecycle events and failures, not every low-level function call. | Indiscriminate call logging creates noise and cost. |
| V2-FR-LOG-026 | Official AI tool logs must distinguish start, completion, validation failure, recoverable warning, and execution failure lifecycle events. | Modify | Preserve structured, secret-safe logging but make configuration explicit, import-safe, bounded, and settings-driven. | V1 logging is widely used but configures file sinks during import. |
| V2-FR-LOG-027 | Official AI tool logs must include request and workflow trace identifiers where available. | Modify | Preserve structured, secret-safe logging but make configuration explicit, import-safe, bounded, and settings-driven. | V1 logging is widely used but configures file sinks during import. |
| V2-FR-LOG-028 | Event Bus logs must include publish, subscribe, delivery failure, retry, dead-letter, queue-full, and dropped-event events. | Defer | Apply this logging requirement when the deferred production capability is implemented. | The associated capability is deferred. |
| V2-FR-LOG-029 | Notification logs must include routing decisions and delivery outcomes without exposing sensitive message bodies. | Defer | Apply this logging requirement when the deferred production capability is implemented. | The associated capability is deferred. |
| V2-FR-LOG-030 | Auth logs must include sanitized auth validation and authorization decisions. | Modify | Preserve structured, secret-safe logging but make configuration explicit, import-safe, bounded, and settings-driven. | V1 logging is widely used but configures file sinks during import. |
| V2-FR-LOG-031 | Observability logs must include metrics/export/health-check failures where detectable. | Defer | Apply this logging requirement when the deferred production capability is implemented. | The associated capability is deferred. |
| V2-FR-LOG-032 | Production files must never log passwords, API keys, broker credentials, encryption keys, tokens, raw private payloads, full approval packets, notification provider credentials, authorization headers, or Telegram bot tokens. | Modify | Preserve structured, secret-safe logging but make configuration explicit, import-safe, bounded, and settings-driven. | V1 logging is widely used but configures file sinks during import. |


#### Time and Clock Handling


| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
| --- | --- | --- | --- | --- |
| V2-FR-TIME-001 | The module must define `DEFAULT_TIMEZONE = "UTC"`. | Modify | Retain UTC-first native helpers with injected clocks/`now` and one consistent raise/return contract. | V1 time helpers are valuable but use hybrid result types and include domain policy. |
| V2-FR-TIME-002 | The module must provide datetime parsing. | Modify | Retain UTC-first native helpers with injected clocks/`now` and one consistent raise/return contract. | V1 time helpers are valuable but use hybrid result types and include domain policy. |
| V2-FR-TIME-003 | The module must provide timestamp normalization. | Modify | Retain UTC-first native helpers with injected clocks/`now` and one consistent raise/return contract. | V1 time helpers are valuable but use hybrid result types and include domain policy. |
| V2-FR-TIME-004 | The module must provide UTC conversion. | Modify | Retain UTC-first native helpers with injected clocks/`now` and one consistent raise/return contract. | V1 time helpers are valuable but use hybrid result types and include domain policy. |
| V2-FR-TIME-005 | The module must provide naive UTC conversion. | Modify | Retain UTC-first native helpers with injected clocks/`now` and one consistent raise/return contract. | V1 time helpers are valuable but use hybrid result types and include domain policy. |
| V2-FR-TIME-006 | The module must provide UTC timestamp formatting with trailing `Z`. | Modify | Retain UTC-first native helpers with injected clocks/`now` and one consistent raise/return contract. | V1 time helpers are valuable but use hybrid result types and include domain policy. |
| V2-FR-TIME-007 | The module must provide timezone normalization for pandas-like series or timestamp columns. | Modify | Retain UTC-first native helpers with injected clocks/`now` and one consistent raise/return contract. | V1 time helpers are valuable but use hybrid result types and include domain policy. |
| V2-FR-TIME-008 | The module must provide stale-data checks. | Modify | Retain UTC-first native helpers with injected clocks/`now` and one consistent raise/return contract. | V1 time helpers are valuable but use hybrid result types and include domain policy. |
| V2-FR-TIME-009 | Timezone behavior must be explicit. | Modify | Retain UTC-first native helpers with injected clocks/`now` and one consistent raise/return contract. | V1 time helpers are valuable but use hybrid result types and include domain policy. |
| V2-FR-TIME-010 | Naive datetimes must be handled deterministically using an explicit assumed timezone. | Modify | Retain UTC-first native helpers with injected clocks/`now` and one consistent raise/return contract. | V1 time helpers are valuable but use hybrid result types and include domain policy. |
| V2-FR-TIME-011 | ISO strings must parse consistently. | Modify | Retain UTC-first native helpers with injected clocks/`now` and one consistent raise/return contract. | V1 time helpers are valuable but use hybrid result types and include domain policy. |
| V2-FR-TIME-012 | Time-dependent helpers must support injected `now` values or injected clock objects where practical. | Modify | Retain UTC-first native helpers with injected clocks/`now` and one consistent raise/return contract. | V1 time helpers are valuable but use hybrid result types and include domain policy. |
| V2-FR-TIME-013 | Invalid datetimes must fail clearly. | Modify | Retain UTC-first native helpers with injected clocks/`now` and one consistent raise/return contract. | V1 time helpers are valuable but use hybrid result types and include domain policy. |
| V2-FR-TIME-014 | Helpers must not use the local machine timezone implicitly. | Modify | Retain UTC-first native helpers with injected clocks/`now` and one consistent raise/return contract. | V1 time helpers are valuable but use hybrid result types and include domain policy. |
| V2-FR-TIME-015 | Wall-clock timestamps must be UTC-aware. | Modify | Retain UTC-first native helpers with injected clocks/`now` and one consistent raise/return contract. | V1 time helpers are valuable but use hybrid result types and include domain policy. |
| V2-FR-TIME-016 | Execution timing must use monotonic timers. | Modify | Retain UTC-first native helpers with injected clocks/`now` and one consistent raise/return contract. | V1 time helpers are valuable but use hybrid result types and include domain policy. |
| V2-FR-TIME-017 | The system must distinguish wall-clock timestamps from monotonic durations. | Modify | Retain UTC-first native helpers with injected clocks/`now` and one consistent raise/return contract. | V1 time helpers are valuable but use hybrid result types and include domain policy. |
| V2-FR-TIME-018 | Distributed workflow timestamp validation must surface clock-drift risk where relevant. | Defer | Apply this requirement in the later events/alerts/observability slice. | The dependent capability is deferred. |
| V2-FR-TIME-019 | Event envelopes must include event creation time and event processing time where applicable. | Defer | Apply this requirement in the later events/alerts/observability slice. | The dependent capability is deferred. |
| V2-FR-TIME-020 | Notification diagnostics must include created, routed, sent, and failed timestamps where applicable. | Defer | Apply this requirement in the later events/alerts/observability slice. | The dependent capability is deferred. |
| V2-FR-TIME-021 | Health checks should include clock-drift status where supported by runtime environment. | Defer | Apply this requirement in the later events/alerts/observability slice. | The dependent capability is deferred. |


#### Authentication and Authorization


| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
| --- | --- | --- | --- | --- |
| V2-FR-AUTH-001 | The module must define a shared authentication context model for internal tools, agents, workflows, and services. | Modify | Keep a small immutable auth context and deny-by-default role/permission/scope/tool allowlist helpers; external token validation stays outside utils. | V1 authorization is useful but disconnected and lacks the full tool allowlist contract. |
| V2-FR-AUTH-002 | The auth context must support principal ID, principal type, roles, permissions, scopes, tenant or environment context where applicable, request ID, workflow ID, and correlation ID. | Modify | Keep a small immutable auth context and deny-by-default role/permission/scope/tool allowlist helpers; external token validation stays outside utils. | V1 authorization is useful but disconnected and lacks the full tool allowlist contract. |
| V2-FR-AUTH-003 | The module must provide validation helpers for authenticated principal context. | Modify | Keep a small immutable auth context and deny-by-default role/permission/scope/tool allowlist helpers; external token validation stays outside utils. | V1 authorization is useful but disconnected and lacks the full tool allowlist contract. |
| V2-FR-AUTH-004 | The module must provide authorization helper checks for required roles, permissions, scopes, and tool names. | Modify | Keep a small immutable auth context and deny-by-default role/permission/scope/tool allowlist helpers; external token validation stays outside utils. | V1 authorization is useful but disconnected and lacks the full tool allowlist contract. |
| V2-FR-AUTH-005 | Authorization helpers must deny by default when identity, permission, role, scope, or tool context is missing. | Modify | Keep a small immutable auth context and deny-by-default role/permission/scope/tool allowlist helpers; external token validation stays outside utils. | V1 authorization is useful but disconnected and lacks the full tool allowlist contract. |
| V2-FR-AUTH-006 | Agents must be authorized through an explicit tool allowlist before accessing official AI tools. | Modify | Keep a small immutable auth context and deny-by-default role/permission/scope/tool allowlist helpers; external token validation stays outside utils. | V1 authorization is useful but disconnected and lacks the full tool allowlist contract. |
| V2-FR-AUTH-007 | Side-effecting or sensitive utilities must require explicit permission checks before execution. | Modify | Keep a small immutable auth context and deny-by-default role/permission/scope/tool allowlist helpers; external token validation stays outside utils. | V1 authorization is useful but disconnected and lacks the full tool allowlist contract. |
| V2-FR-AUTH-008 | Auth helpers must return deterministic validation results or standard tool error envelopes at official tool boundaries. | Modify | Keep a small immutable auth context and deny-by-default role/permission/scope/tool allowlist helpers; external token validation stays outside utils. | V1 authorization is useful but disconnected and lacks the full tool allowlist contract. |
| V2-FR-AUTH-009 | Auth helpers must not validate external identity-provider tokens unless an explicit adapter is supplied by the application layer. | Modify | Keep a small immutable auth context and deny-by-default role/permission/scope/tool allowlist helpers; external token validation stays outside utils. | V1 authorization is useful but disconnected and lacks the full tool allowlist contract. |
| V2-FR-AUTH-010 | Auth helpers must not contact external identity providers at import time. | Modify | Keep a small immutable auth context and deny-by-default role/permission/scope/tool allowlist helpers; external token validation stays outside utils. | V1 authorization is useful but disconnected and lacks the full tool allowlist contract. |
| V2-FR-AUTH-011 | Auth context must be redacted before logging, events, metrics, or error reporting. | Modify | Keep a small immutable auth context and deny-by-default role/permission/scope/tool allowlist helpers; external token validation stays outside utils. | V1 authorization is useful but disconnected and lacks the full tool allowlist contract. |
| V2-FR-AUTH-012 | Auth failures must use deterministic error codes such as `PERMISSION_DENIED`, `INVALID_AUTH_CONTEXT`, or `AUTHORIZATION_FAILED`. | Modify | Keep a small immutable auth context and deny-by-default role/permission/scope/tool allowlist helpers; external token validation stays outside utils. | V1 authorization is useful but disconnected and lacks the full tool allowlist contract. |
| V2-FR-AUTH-013 | Authentication and authorization events must be observable through logs, metrics, and sanitized audit events. | Defer | Keep sanitized logging now; add metrics/events with the observability slice. | The metrics/event pipeline is deferred. |


#### Error Utilities


| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
| --- | --- | --- | --- | --- |
| V2-FR-ERR-001 | The module must define `Error`. | Modify | Keep the shared base errors and generic mapping; move domain-specific taxonomies to their owning domains. | V1 error behavior is proven, but `errors.py` is cross-domain and oversized. |
| V2-FR-ERR-002 | The module must define `ValidationError`. | Modify | Keep the shared base errors and generic mapping; move domain-specific taxonomies to their owning domains. | V1 error behavior is proven, but `errors.py` is cross-domain and oversized. |
| V2-FR-ERR-003 | The module must define `ConfigurationError`. | Modify | Keep the shared base errors and generic mapping; move domain-specific taxonomies to their owning domains. | V1 error behavior is proven, but `errors.py` is cross-domain and oversized. |
| V2-FR-ERR-004 | The module must define `SecurityError`. | Modify | Keep the shared base errors and generic mapping; move domain-specific taxonomies to their owning domains. | V1 error behavior is proven, but `errors.py` is cross-domain and oversized. |
| V2-FR-ERR-005 | The module must define `DataError`. | Modify | Keep the shared base errors and generic mapping; move domain-specific taxonomies to their owning domains. | V1 error behavior is proven, but `errors.py` is cross-domain and oversized. |
| V2-FR-ERR-006 | The module must define `ExternalServiceError`. | Modify | Keep the shared base errors and generic mapping; move domain-specific taxonomies to their owning domains. | V1 error behavior is proven, but `errors.py` is cross-domain and oversized. |
| V2-FR-ERR-007 | Every shared exception must carry a deterministic `code` attribute. | Modify | Keep the shared base errors and generic mapping; move domain-specific taxonomies to their owning domains. | V1 error behavior is proven, but `errors.py` is cross-domain and oversized. |
| V2-FR-ERR-008 | Error messages must be human-readable. | Modify | Keep the shared base errors and generic mapping; move domain-specific taxonomies to their owning domains. | V1 error behavior is proven, but `errors.py` is cross-domain and oversized. |
| V2-FR-ERR-009 | `error_name(code)` must return deterministic names. | Modify | Keep the shared base errors and generic mapping; move domain-specific taxonomies to their owning domains. | V1 error behavior is proven, but `errors.py` is cross-domain and oversized. |
| V2-FR-ERR-010 | `message_for(code, default)` must return useful fallback messages. | Modify | Keep the shared base errors and generic mapping; move domain-specific taxonomies to their owning domains. | V1 error behavior is proven, but `errors.py` is cross-domain and oversized. |
| V2-FR-ERR-011 | Unknown codes must resolve safely to `UNKNOWN_ERROR` or a provided default. | Modify | Keep the shared base errors and generic mapping; move domain-specific taxonomies to their owning domains. | V1 error behavior is proven, but `errors.py` is cross-domain and oversized. |
| V2-FR-ERR-012 | Future domain-specific errors must inherit from `Error` or expose a compatible `code: str` attribute. | Modify | Keep the shared base errors and generic mapping; move domain-specific taxonomies to their owning domains. | V1 error behavior is proven, but `errors.py` is cross-domain and oversized. |
| V2-FR-ERR-013 | Standard response builders must map `Error` subclasses generically without requiring every future domain error to be hardcoded. | Modify | Keep the shared base errors and generic mapping; move domain-specific taxonomies to their owning domains. | V1 error behavior is proven, but `errors.py` is cross-domain and oversized. |
| V2-FR-ERR-014 | Unknown non-HaruQuant exceptions must map safely to `UNKNOWN_ERROR` or `TOOL_EXECUTION_FAILED` at controlled tool boundaries. | Modify | Keep the shared base errors and generic mapping; move domain-specific taxonomies to their owning domains. | V1 error behavior is proven, but `errors.py` is cross-domain and oversized. |


#### Identity and Traceability


| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
| --- | --- | --- | --- | --- |
| V2-FR-ID-001 | The module must provide `generate_id`. | Modify | Retain collision-resistant native ID/version helpers, remove nonexistent aliases, and document deterministic validation. | V1 helpers are useful but registry exports are inaccurate. |
| V2-FR-ID-002 | The module must provide `generate_prefixed_id`. | Modify | Retain collision-resistant native ID/version helpers, remove nonexistent aliases, and document deterministic validation. | V1 helpers are useful but registry exports are inaccurate. |
| V2-FR-ID-003 | The module must provide `generate_request_id`. | Modify | Retain collision-resistant native ID/version helpers, remove nonexistent aliases, and document deterministic validation. | V1 helpers are useful but registry exports are inaccurate. |
| V2-FR-ID-004 | The module must provide `generate_workflow_id`. | Modify | Retain collision-resistant native ID/version helpers, remove nonexistent aliases, and document deterministic validation. | V1 helpers are useful but registry exports are inaccurate. |
| V2-FR-ID-005 | The module must provide `generate_correlation_id` or equivalent correlation ID support. | Modify | Retain collision-resistant native ID/version helpers, remove nonexistent aliases, and document deterministic validation. | V1 helpers are useful but registry exports are inaccurate. |
| V2-FR-ID-006 | The module must provide `generate_event_id` or equivalent event ID support. | Modify | Retain collision-resistant native ID/version helpers, remove nonexistent aliases, and document deterministic validation. | V1 helpers are useful but registry exports are inaccurate. |
| V2-FR-ID-007 | The module must provide `validate_request_id`. | Modify | Retain collision-resistant native ID/version helpers, remove nonexistent aliases, and document deterministic validation. | V1 helpers are useful but registry exports are inaccurate. |
| V2-FR-ID-008 | The module must provide `validate_workflow_id`. | Modify | Retain collision-resistant native ID/version helpers, remove nonexistent aliases, and document deterministic validation. | V1 helpers are useful but registry exports are inaccurate. |
| V2-FR-ID-009 | The module must provide `ensure_version`. | Modify | Retain collision-resistant native ID/version helpers, remove nonexistent aliases, and document deterministic validation. | V1 helpers are useful but registry exports are inaccurate. |
| V2-FR-ID-010 | IDs must be string-safe. | Modify | Retain collision-resistant native ID/version helpers, remove nonexistent aliases, and document deterministic validation. | V1 helpers are useful but registry exports are inaccurate. |
| V2-FR-ID-011 | IDs must be safe for logs, filenames where practical, audit records, tool metadata, events, notifications, and metrics after cardinality controls. | Modify | Retain collision-resistant native ID/version helpers, remove nonexistent aliases, and document deterministic validation. | V1 helpers are useful but registry exports are inaccurate. |
| V2-FR-ID-012 | IDs must not contain secrets or raw user-provided text. | Modify | Retain collision-resistant native ID/version helpers, remove nonexistent aliases, and document deterministic validation. | V1 helpers are useful but registry exports are inaccurate. |
| V2-FR-ID-013 | Prefix validation must reject empty or unsafe prefixes. | Modify | Retain collision-resistant native ID/version helpers, remove nonexistent aliases, and document deterministic validation. | V1 helpers are useful but registry exports are inaccurate. |
| V2-FR-ID-014 | Generated IDs must be collision-resistant. | Modify | Retain collision-resistant native ID/version helpers, remove nonexistent aliases, and document deterministic validation. | V1 helpers are useful but registry exports are inaccurate. |
| V2-FR-ID-015 | Generated IDs must use UUID4, ULID-like generation, or an equivalently collision-resistant approach unless deterministic IDs are explicitly required. | Modify | Retain collision-resistant native ID/version helpers, remove nonexistent aliases, and document deterministic validation. | V1 helpers are useful but registry exports are inaccurate. |
| V2-FR-ID-016 | Request IDs and workflow IDs must be suitable for logs, audit records, tool responses, and agent handoffs. | Modify | Retain collision-resistant native ID/version helpers, remove nonexistent aliases, and document deterministic validation. | V1 helpers are useful but registry exports are inaccurate. |
| V2-FR-ID-017 | ID validation must be deterministic and must not perform external lookups. | Modify | Retain collision-resistant native ID/version helpers, remove nonexistent aliases, and document deterministic validation. | V1 helpers are useful but registry exports are inaccurate. |
| V2-FR-ID-018 | `ensure_version(None)` must return the configured default. | Modify | Retain collision-resistant native ID/version helpers, remove nonexistent aliases, and document deterministic validation. | V1 helpers are useful but registry exports are inaccurate. |


#### Path Utilities


| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
| --- | --- | --- | --- | --- |
| V2-FR-PATH-001 | The module must provide `normalize_path`. | Modify | Keep the cohesive `Path`-returning API and remove duplicate envelope/hybrid path wrappers. | V1 has a sound implementation in `paths.py` plus a conflicting duplicate in normalization. |
| V2-FR-PATH-002 | The module must provide `ensure_dir`. | Modify | Keep the cohesive `Path`-returning API and remove duplicate envelope/hybrid path wrappers. | V1 has a sound implementation in `paths.py` plus a conflicting duplicate in normalization. |
| V2-FR-PATH-003 | The module must provide `ensure_parent_dir`. | Modify | Keep the cohesive `Path`-returning API and remove duplicate envelope/hybrid path wrappers. | V1 has a sound implementation in `paths.py` plus a conflicting duplicate in normalization. |
| V2-FR-PATH-004 | Path inputs must be validated. | Modify | Keep the cohesive `Path`-returning API and remove duplicate envelope/hybrid path wrappers. | V1 has a sound implementation in `paths.py` plus a conflicting duplicate in normalization. |
| V2-FR-PATH-005 | Directory creation helpers must be explicit side-effect helpers. | Modify | Keep the cohesive `Path`-returning API and remove duplicate envelope/hybrid path wrappers. | V1 has a sound implementation in `paths.py` plus a conflicting duplicate in normalization. |
| V2-FR-PATH-006 | `normalize_path` must have no side effects. | Modify | Keep the cohesive `Path`-returning API and remove duplicate envelope/hybrid path wrappers. | V1 has a sound implementation in `paths.py` plus a conflicting duplicate in normalization. |
| V2-FR-PATH-007 | `ensure_dir` must create a directory when missing. | Modify | Keep the cohesive `Path`-returning API and remove duplicate envelope/hybrid path wrappers. | V1 has a sound implementation in `paths.py` plus a conflicting duplicate in normalization. |
| V2-FR-PATH-008 | `ensure_parent_dir` must create a parent directory when missing. | Modify | Keep the cohesive `Path`-returning API and remove duplicate envelope/hybrid path wrappers. | V1 has a sound implementation in `paths.py` plus a conflicting duplicate in normalization. |
| V2-FR-PATH-009 | Path traversal outside `base_dir` must be rejected when a base directory is supplied. | Modify | Keep the cohesive `Path`-returning API and remove duplicate envelope/hybrid path wrappers. | V1 has a sound implementation in `paths.py` plus a conflicting duplicate in normalization. |
| V2-FR-PATH-010 | Path helpers must return `Path` objects. | Modify | Keep the cohesive `Path`-returning API and remove duplicate envelope/hybrid path wrappers. | V1 has a sound implementation in `paths.py` plus a conflicting duplicate in normalization. |
| V2-FR-PATH-011 | File and directory permissions must use platform-safe defaults. | Modify | Keep the cohesive `Path`-returning API and remove duplicate envelope/hybrid path wrappers. | V1 has a sound implementation in `paths.py` plus a conflicting duplicate in normalization. |


#### Dataframe Utilities


| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
| --- | --- | --- | --- | --- |
| V2-FR-DF-001 | The module must provide datetime alignment for dataframes. | Modify | Consolidate pure dataframe/sequence helpers, lazy-load pandas, avoid mutation, and exclude process-pool orchestration from the core. | V1 has duplicated helpers and eager heavy imports. |
| V2-FR-DF-002 | The module must provide bar-to-record conversion. | Modify | Consolidate pure dataframe/sequence helpers, lazy-load pandas, avoid mutation, and exclude process-pool orchestration from the core. | V1 has duplicated helpers and eager heavy imports. |
| V2-FR-DF-003 | The module must provide chunking for sequences. | Modify | Consolidate pure dataframe/sequence helpers, lazy-load pandas, avoid mutation, and exclude process-pool orchestration from the core. | V1 has duplicated helpers and eager heavy imports. |
| V2-FR-DF-004 | The module must provide parameter-combination helpers. | Modify | Consolidate pure dataframe/sequence helpers, lazy-load pandas, avoid mutation, and exclude process-pool orchestration from the core. | V1 has duplicated helpers and eager heavy imports. |
| V2-FR-DF-005 | The module must provide dataframe comparison helpers. | Modify | Consolidate pure dataframe/sequence helpers, lazy-load pandas, avoid mutation, and exclude process-pool orchestration from the core. | V1 has duplicated helpers and eager heavy imports. |
| V2-FR-DF-006 | The module must provide OHLC and OHLCV comparison helpers. | Modify | Consolidate pure dataframe/sequence helpers, lazy-load pandas, avoid mutation, and exclude process-pool orchestration from the core. | V1 has duplicated helpers and eager heavy imports. |
| V2-FR-DF-007 | The module must provide dataframe-record serialization. | Modify | Consolidate pure dataframe/sequence helpers, lazy-load pandas, avoid mutation, and exclude process-pool orchestration from the core. | V1 has duplicated helpers and eager heavy imports. |
| V2-FR-DF-008 | Dataframe helpers may return native Python objects. | Modify | Consolidate pure dataframe/sequence helpers, lazy-load pandas, avoid mutation, and exclude process-pool orchestration from the core. | V1 has duplicated helpers and eager heavy imports. |
| V2-FR-DF-009 | Dataframe columns must be validated where required. | Modify | Consolidate pure dataframe/sequence helpers, lazy-load pandas, avoid mutation, and exclude process-pool orchestration from the core. | V1 has duplicated helpers and eager heavy imports. |
| V2-FR-DF-010 | Dataframe helpers must not mutate caller-owned dataframes unless explicitly documented. | Modify | Consolidate pure dataframe/sequence helpers, lazy-load pandas, avoid mutation, and exclude process-pool orchestration from the core. | V1 has duplicated helpers and eager heavy imports. |
| V2-FR-DF-011 | Dataframe helpers must document copy, view, or transformed-data behavior. | Modify | Consolidate pure dataframe/sequence helpers, lazy-load pandas, avoid mutation, and exclude process-pool orchestration from the core. | V1 has duplicated helpers and eager heavy imports. |
| V2-FR-DF-012 | Serialization must handle timestamps safely. | Modify | Consolidate pure dataframe/sequence helpers, lazy-load pandas, avoid mutation, and exclude process-pool orchestration from the core. | V1 has duplicated helpers and eager heavy imports. |
| V2-FR-DF-013 | `serialize_dataframe_records` must emit UTC ISO timestamp strings ending in `Z`. | Modify | Consolidate pure dataframe/sequence helpers, lazy-load pandas, avoid mutation, and exclude process-pool orchestration from the core. | V1 has duplicated helpers and eager heavy imports. |
| V2-FR-DF-014 | `compare_dataframes` must align by comparable indexes or fail with a clear validation error when deterministic alignment is impossible. | Modify | Consolidate pure dataframe/sequence helpers, lazy-load pandas, avoid mutation, and exclude process-pool orchestration from the core. | V1 has duplicated helpers and eager heavy imports. |
| V2-FR-DF-015 | `chunked` must reject `size <= 0` with a clear validation error. | Modify | Consolidate pure dataframe/sequence helpers, lazy-load pandas, avoid mutation, and exclude process-pool orchestration from the core. | V1 has duplicated helpers and eager heavy imports. |
| V2-FR-DF-016 | Comparisons must support tolerance. | Modify | Consolidate pure dataframe/sequence helpers, lazy-load pandas, avoid mutation, and exclude process-pool orchestration from the core. | V1 has duplicated helpers and eager heavy imports. |
| V2-FR-DF-017 | Empty dataframes must be handled deterministically. | Modify | Consolidate pure dataframe/sequence helpers, lazy-load pandas, avoid mutation, and exclude process-pool orchestration from the core. | V1 has duplicated helpers and eager heavy imports. |
| V2-FR-DF-018 | Importing `app.services.utils` must not eagerly import pandas. | Modify | Consolidate pure dataframe/sequence helpers, lazy-load pandas, avoid mutation, and exclude process-pool orchestration from the core. | V1 has duplicated helpers and eager heavy imports. |
| V2-FR-DF-019 | Missing pandas must fail only when a dataframe helper is called. | Modify | Consolidate pure dataframe/sequence helpers, lazy-load pandas, avoid mutation, and exclude process-pool orchestration from the core. | V1 has duplicated helpers and eager heavy imports. |


#### OHLCV Data Quality


| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
| --- | --- | --- | --- | --- |
| V2-FR-DQ-001 | Public OHLCV helper names must not imply repair, resampling, enrichment, cleaning, persistence, or mutation. | Keep | Keep preparation private and expose only stateless diagnostic validation. | This corrects V1's ambiguous public preparation API. |
| V2-FR-DQ-002 | `prepare_ohlcv_data` must not be part of the public Utils registry because the name implies transformation or cleaning. | Keep | Keep preparation private and expose only stateless diagnostic validation. | This corrects V1's ambiguous public preparation API. |
| V2-FR-DQ-003 | If diagnostic structural inspection is needed, it must use a private helper name such as `_inspect_ohlcv_structure`. | Keep | Keep preparation private and expose only stateless diagnostic validation. | This corrects V1's ambiguous public preparation API. |
| V2-FR-DQ-004 | `_inspect_ohlcv_structure`, if implemented, must be constrained to diagnostic inspection for validation only and must not mutate caller-owned data. | Keep | Keep preparation private and expose only stateless diagnostic validation. | This corrects V1's ambiguous public preparation API. |
| V2-FR-DQ-005 | The module must provide `validate_ohlcv_quality`. | Modify | Merge the three V1 validation surfaces into one bounded, deterministic, diagnostic-only validator and one official wrapper. | V1 has useful checks but inconsistent issue schemas and no single canonical contract. |
| V2-FR-DQ-006 | `validate_ohlcv_quality` must be stateless and diagnostic-only. | Modify | Merge the three V1 validation surfaces into one bounded, deterministic, diagnostic-only validator and one official wrapper. | V1 has useful checks but inconsistent issue schemas and no single canonical contract. |
| V2-FR-DQ-007 | `validate_ohlcv_quality` must not repair, enrich, persist, resample, clean, or mutate input data. | Modify | Merge the three V1 validation surfaces into one bounded, deterministic, diagnostic-only validator and one official wrapper. | V1 has useful checks but inconsistent issue schemas and no single canonical contract. |
| V2-FR-DQ-008 | `validate_ohlcv_quality` may inspect, profile, score, report issues, and provide descriptive remediation recommendations. | Modify | Merge the three V1 validation surfaces into one bounded, deterministic, diagnostic-only validator and one official wrapper. | V1 has useful checks but inconsistent issue schemas and no single canonical contract. |
| V2-FR-DQ-009 | Data repair, resampling, enrichment, persistence, and cleaning workflows must be reserved for `app.services.data`. | Modify | Merge the three V1 validation surfaces into one bounded, deterministic, diagnostic-only validator and one official wrapper. | V1 has useful checks but inconsistent issue schemas and no single canonical contract. |
| V2-FR-DQ-010 | Caller-owned dataframes must not be mutated. | Modify | Merge the three V1 validation surfaces into one bounded, deterministic, diagnostic-only validator and one official wrapper. | V1 has useful checks but inconsistent issue schemas and no single canonical contract. |
| V2-FR-DQ-011 | Validation must verify the input is a pandas DataFrame. | Modify | Merge the three V1 validation surfaces into one bounded, deterministic, diagnostic-only validator and one official wrapper. | V1 has useful checks but inconsistent issue schemas and no single canonical contract. |
| V2-FR-DQ-012 | Validation must verify mandatory OHLC columns exist. | Modify | Merge the three V1 validation surfaces into one bounded, deterministic, diagnostic-only validator and one official wrapper. | V1 has useful checks but inconsistent issue schemas and no single canonical contract. |
| V2-FR-DQ-013 | Missing mandatory columns must produce structured `INVALID_INPUT` details. | Modify | Merge the three V1 validation surfaces into one bounded, deterministic, diagnostic-only validator and one official wrapper. | V1 has useful checks but inconsistent issue schemas and no single canonical contract. |
| V2-FR-DQ-014 | Extra columns must be ignored by default and must not fail validation unless they create ambiguity. | Modify | Merge the three V1 validation surfaces into one bounded, deterministic, diagnostic-only validator and one official wrapper. | V1 has useful checks but inconsistent issue schemas and no single canonical contract. |
| V2-FR-DQ-015 | Validation must verify datetime column or datetime-compatible index availability. | Modify | Merge the three V1 validation surfaces into one bounded, deterministic, diagnostic-only validator and one official wrapper. | V1 has useful checks but inconsistent issue schemas and no single canonical contract. |
| V2-FR-DQ-016 | Validation must verify datetimes are parseable. | Modify | Merge the three V1 validation surfaces into one bounded, deterministic, diagnostic-only validator and one official wrapper. | V1 has useful checks but inconsistent issue schemas and no single canonical contract. |
| V2-FR-DQ-017 | Validation must report timestamp monotonicity. | Modify | Merge the three V1 validation surfaces into one bounded, deterministic, diagnostic-only validator and one official wrapper. | V1 has useful checks but inconsistent issue schemas and no single canonical contract. |
| V2-FR-DQ-018 | Validation must detect duplicate timestamps. | Modify | Merge the three V1 validation surfaces into one bounded, deterministic, diagnostic-only validator and one official wrapper. | V1 has useful checks but inconsistent issue schemas and no single canonical contract. |
| V2-FR-DQ-019 | Validation must detect duplicate OHLC/OHLCV rows. | Modify | Merge the three V1 validation surfaces into one bounded, deterministic, diagnostic-only validator and one official wrapper. | V1 has useful checks but inconsistent issue schemas and no single canonical contract. |
| V2-FR-DQ-020 | Validation must detect missing timestamps or inferred gaps when timeframe is known. | Modify | Merge the three V1 validation surfaces into one bounded, deterministic, diagnostic-only validator and one official wrapper. | V1 has useful checks but inconsistent issue schemas and no single canonical contract. |
| V2-FR-DQ-021 | Validation must distinguish market-calendar gaps from unexpected gaps where session rules are supplied. | Modify | Merge the three V1 validation surfaces into one bounded, deterministic, diagnostic-only validator and one official wrapper. | V1 has useful checks but inconsistent issue schemas and no single canonical contract. |
| V2-FR-DQ-022 | Validation must verify OHLC values are numeric. | Modify | Merge the three V1 validation surfaces into one bounded, deterministic, diagnostic-only validator and one official wrapper. | V1 has useful checks but inconsistent issue schemas and no single canonical contract. |
| V2-FR-DQ-023 | Validation must flag negative prices. | Modify | Merge the three V1 validation surfaces into one bounded, deterministic, diagnostic-only validator and one official wrapper. | V1 has useful checks but inconsistent issue schemas and no single canonical contract. |
| V2-FR-DQ-024 | Validation must flag zero prices. | Modify | Merge the three V1 validation surfaces into one bounded, deterministic, diagnostic-only validator and one official wrapper. | V1 has useful checks but inconsistent issue schemas and no single canonical contract. |
| V2-FR-DQ-025 | Validation must validate high-low relationships. | Modify | Merge the three V1 validation surfaces into one bounded, deterministic, diagnostic-only validator and one official wrapper. | V1 has useful checks but inconsistent issue schemas and no single canonical contract. |
| V2-FR-DQ-026 | Validation must verify OHLC values are within candle high/low range. | Modify | Merge the three V1 validation surfaces into one bounded, deterministic, diagnostic-only validator and one official wrapper. | V1 has useful checks but inconsistent issue schemas and no single canonical contract. |
| V2-FR-DQ-027 | Validation must flag zero volume when volume is supplied. | Modify | Merge the three V1 validation surfaces into one bounded, deterministic, diagnostic-only validator and one official wrapper. | V1 has useful checks but inconsistent issue schemas and no single canonical contract. |
| V2-FR-DQ-028 | Validation must flag negative volume when volume is supplied. | Modify | Merge the three V1 validation surfaces into one bounded, deterministic, diagnostic-only validator and one official wrapper. | V1 has useful checks but inconsistent issue schemas and no single canonical contract. |
| V2-FR-DQ-029 | Validation must verify spread is numeric and non-negative when supplied. | Modify | Merge the three V1 validation surfaces into one bounded, deterministic, diagnostic-only validator and one official wrapper. | V1 has useful checks but inconsistent issue schemas and no single canonical contract. |
| V2-FR-DQ-030 | Validation must detect extreme spikes using configurable thresholds. | Modify | Merge the three V1 validation surfaces into one bounded, deterministic, diagnostic-only validator and one official wrapper. | V1 has useful checks but inconsistent issue schemas and no single canonical contract. |
| V2-FR-DQ-031 | Validation must detect flatline candles. | Modify | Merge the three V1 validation surfaces into one bounded, deterministic, diagnostic-only validator and one official wrapper. | V1 has useful checks but inconsistent issue schemas and no single canonical contract. |
| V2-FR-DQ-032 | Validation must detect numeric infinities and NaN values. | Modify | Merge the three V1 validation surfaces into one bounded, deterministic, diagnostic-only validator and one official wrapper. | V1 has useful checks but inconsistent issue schemas and no single canonical contract. |
| V2-FR-DQ-033 | Validation must report timezone awareness. | Modify | Merge the three V1 validation surfaces into one bounded, deterministic, diagnostic-only validator and one official wrapper. | V1 has useful checks but inconsistent issue schemas and no single canonical contract. |
| V2-FR-DQ-034 | Validation must produce session-level statistics where possible. | Modify | Merge the three V1 validation surfaces into one bounded, deterministic, diagnostic-only validator and one official wrapper. | V1 has useful checks but inconsistent issue schemas and no single canonical contract. |
| V2-FR-DQ-035 | Validation must calculate a deterministic quality score. | Modify | Merge the three V1 validation surfaces into one bounded, deterministic, diagnostic-only validator and one official wrapper. | V1 has useful checks but inconsistent issue schemas and no single canonical contract. |
| V2-FR-DQ-036 | Validation must assign severity levels consistently. | Modify | Merge the three V1 validation surfaces into one bounded, deterministic, diagnostic-only validator and one official wrapper. | V1 has useful checks but inconsistent issue schemas and no single canonical contract. |
| V2-FR-DQ-037 | Validation must bound issue samples by `max_issue_samples`. | Modify | Merge the three V1 validation surfaces into one bounded, deterministic, diagnostic-only validator and one official wrapper. | V1 has useful checks but inconsistent issue schemas and no single canonical contract. |
| V2-FR-DQ-038 | Validation must bound issue list length by `max_issues_returned`. | Modify | Merge the three V1 validation surfaces into one bounded, deterministic, diagnostic-only validator and one official wrapper. | V1 has useful checks but inconsistent issue schemas and no single canonical contract. |
| V2-FR-DQ-039 | Validation must avoid oversized tool responses for large datasets. | Modify | Merge the three V1 validation surfaces into one bounded, deterministic, diagnostic-only validator and one official wrapper. | V1 has useful checks but inconsistent issue schemas and no single canonical contract. |
| V2-FR-DQ-040 | Validation must report symbol mismatches as `SYMBOL_MISMATCH` when `symbol` is provided and a dataframe `symbol` column exists. | Modify | Merge the three V1 validation surfaces into one bounded, deterministic, diagnostic-only validator and one official wrapper. | V1 has useful checks but inconsistent issue schemas and no single canonical contract. |
| V2-FR-DQ-041 | Validation must mark symbol verification as `not_available` in summary when `symbol` is provided and no dataframe `symbol` column exists. | Modify | Merge the three V1 validation surfaces into one bounded, deterministic, diagnostic-only validator and one official wrapper. | V1 has useful checks but inconsistent issue schemas and no single canonical contract. |
| V2-FR-DQ-042 | Validation must report timeframe mismatches as `TIMEFRAME_MISMATCH` or `UNEXPECTED_TIME_GAP` when timeframe checks fail. | Modify | Merge the three V1 validation surfaces into one bounded, deterministic, diagnostic-only validator and one official wrapper. | V1 has useful checks but inconsistent issue schemas and no single canonical contract. |
| V2-FR-DQ-043 | Successful validation responses must include `symbol`, `timeframe`, `rows_checked`, `quality_score`, `passed`, `severity`, `issues`, `summary`, `profile`, and `remediation`. | Modify | Merge the three V1 validation surfaces into one bounded, deterministic, diagnostic-only validator and one official wrapper. | V1 has useful checks but inconsistent issue schemas and no single canonical contract. |
| V2-FR-DQ-044 | Each issue must include `code`, `severity`, `message`, `column`, `row_count`, and `sample`. | Modify | Merge the three V1 validation surfaces into one bounded, deterministic, diagnostic-only validator and one official wrapper. | V1 has useful checks but inconsistent issue schemas and no single canonical contract. |
| V2-FR-DQ-045 | The default quality score penalty model must be: critical `-40`, error `-20`, warning `-5`, info `-1`, bounded from `0` to `100`. | Modify | Merge the three V1 validation surfaces into one bounded, deterministic, diagnostic-only validator and one official wrapper. | V1 has useful checks but inconsistent issue schemas and no single canonical contract. |
| V2-FR-DQ-046 | OHLCV validation must use a default quality pass threshold of `90.0`. | Modify | Merge the three V1 validation surfaces into one bounded, deterministic, diagnostic-only validator and one official wrapper. | V1 has useful checks but inconsistent issue schemas and no single canonical contract. |
| V2-FR-DQ-047 | OHLCV `passed=True` must require no critical issues, no error issues, and `quality_score >= quality_pass_threshold`. | Modify | Merge the three V1 validation surfaces into one bounded, deterministic, diagnostic-only validator and one official wrapper. | V1 has useful checks but inconsistent issue schemas and no single canonical contract. |
| V2-FR-DQ-048 | Warning and info issues may still produce `passed=True` only when the quality score remains above threshold. | Modify | Merge the three V1 validation surfaces into one bounded, deterministic, diagnostic-only validator and one official wrapper. | V1 has useful checks but inconsistent issue schemas and no single canonical contract. |
| V2-FR-DQ-049 | Overall severity must aggregate deterministically: any critical issue means `critical`; otherwise any error means `error`; otherwise any warning means `warning`; otherwise `info`. | Modify | Merge the three V1 validation surfaces into one bounded, deterministic, diagnostic-only validator and one official wrapper. | V1 has useful checks but inconsistent issue schemas and no single canonical contract. |
| V2-FR-DQ-050 | Issue truncation must be explicit through `summary["issues_truncated"]` and `summary["samples_truncated"]` when limits are reached. | Modify | Merge the three V1 validation surfaces into one bounded, deterministic, diagnostic-only validator and one official wrapper. | V1 has useful checks but inconsistent issue schemas and no single canonical contract. |


#### Schema Validation


| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
| --- | --- | --- | --- | --- |
| V2-FR-SCHEMA-001 | The module must provide reusable validation helpers for agent, workflow, tool, registry, evidence, approval, freshness, artifact, and payload contracts. | Modify | Merge V1 schema validators into one native validation engine plus explicit official wrappers with bounded JSON-pointer diagnostics. | V1 has overlapping implementations and incomplete schema semantics. |
| V2-FR-SCHEMA-002 | `validate_numeric_range` must be a support helper returning a native validation result. | Modify | Merge V1 schema validators into one native validation engine plus explicit official wrappers with bounded JSON-pointer diagnostics. | V1 has overlapping implementations and incomplete schema semantics. |
| V2-FR-SCHEMA-003 | `validate_required_fields` must be a support helper returning a native validation result. | Modify | Merge V1 schema validators into one native validation engine plus explicit official wrappers with bounded JSON-pointer diagnostics. | V1 has overlapping implementations and incomplete schema semantics. |
| V2-FR-SCHEMA-004 | Native validation results must include at minimum `valid`, `message`, `code`, and `details`. | Modify | Merge V1 schema validators into one native validation engine plus explicit official wrappers with bounded JSON-pointer diagnostics. | V1 has overlapping implementations and incomplete schema semantics. |
| V2-FR-SCHEMA-005 | Official validators may wrap native validation results in standard tool envelopes. | Modify | Merge V1 schema validators into one native validation engine plus explicit official wrappers with bounded JSON-pointer diagnostics. | V1 has overlapping implementations and incomplete schema semantics. |
| V2-FR-SCHEMA-006 | Numeric validation must support risk values, prices, volumes, spreads, scores, thresholds, and allocation limits. | Modify | Merge V1 schema validators into one native validation engine plus explicit official wrappers with bounded JSON-pointer diagnostics. | V1 has overlapping implementations and incomplete schema semantics. |
| V2-FR-SCHEMA-007 | Numeric validation must reject non-numeric values with deterministic details. | Modify | Merge V1 schema validators into one native validation engine plus explicit official wrappers with bounded JSON-pointer diagnostics. | V1 has overlapping implementations and incomplete schema semantics. |
| V2-FR-SCHEMA-008 | Numeric validation must reject `NaN`, positive infinity, and negative infinity unless a future specialized function explicitly allows them. | Modify | Merge V1 schema validators into one native validation engine plus explicit official wrappers with bounded JSON-pointer diagnostics. | V1 has overlapping implementations and incomplete schema semantics. |
| V2-FR-SCHEMA-009 | Numeric validation bounds must be inclusive unless documented otherwise. | Modify | Merge V1 schema validators into one native validation engine plus explicit official wrappers with bounded JSON-pointer diagnostics. | V1 has overlapping implementations and incomplete schema semantics. |
| V2-FR-SCHEMA-010 | Numeric validation messages must include the logical field name. | Modify | Merge V1 schema validators into one native validation engine plus explicit official wrappers with bounded JSON-pointer diagnostics. | V1 has overlapping implementations and incomplete schema semantics. |
| V2-FR-SCHEMA-011 | Missing required fields must be explicit. | Modify | Merge V1 schema validators into one native validation engine plus explicit official wrappers with bounded JSON-pointer diagnostics. | V1 has overlapping implementations and incomplete schema semantics. |
| V2-FR-SCHEMA-012 | Unknown extra fields must be rejected by default for official schema validators. | Modify | Merge V1 schema validators into one native validation engine plus explicit official wrappers with bounded JSON-pointer diagnostics. | V1 has overlapping implementations and incomplete schema semantics. |
| V2-FR-SCHEMA-013 | Schemas may explicitly allow extra fields through a documented schema policy. | Modify | Merge V1 schema validators into one native validation engine plus explicit official wrappers with bounded JSON-pointer diagnostics. | V1 has overlapping implementations and incomplete schema semantics. |
| V2-FR-SCHEMA-014 | Input and output schema validators must support optional schema-version checks. | Modify | Merge V1 schema validators into one native validation engine plus explicit official wrappers with bounded JSON-pointer diagnostics. | V1 has overlapping implementations and incomplete schema semantics. |
| V2-FR-SCHEMA-015 | Version mismatches must return `VALIDATION_FAILED` with a clear compatibility message. | Modify | Merge V1 schema validators into one native validation engine plus explicit official wrappers with bounded JSON-pointer diagnostics. | V1 has overlapping implementations and incomplete schema semantics. |
| V2-FR-SCHEMA-016 | Schema compatibility must follow semantic-version rules. | Modify | Merge V1 schema validators into one native validation engine plus explicit official wrappers with bounded JSON-pointer diagnostics. | V1 has overlapping implementations and incomplete schema semantics. |
| V2-FR-SCHEMA-017 | Schema compatibility must require the same major version. | Modify | Merge V1 schema validators into one native validation engine plus explicit official wrappers with bounded JSON-pointer diagnostics. | V1 has overlapping implementations and incomplete schema semantics. |
| V2-FR-SCHEMA-018 | Schema compatibility may accept payload minor versions less than or equal to the schema minor version when no breaking change is declared. | Modify | Merge V1 schema validators into one native validation engine plus explicit official wrappers with bounded JSON-pointer diagnostics. | V1 has overlapping implementations and incomplete schema semantics. |
| V2-FR-SCHEMA-019 | Schema compatibility may be overridden by an explicit compatible-version allowlist in the schema. | Modify | Merge V1 schema validators into one native validation engine plus explicit official wrappers with bounded JSON-pointer diagnostics. | V1 has overlapping implementations and incomplete schema semantics. |
| V2-FR-SCHEMA-020 | Schema validation errors must return the specific path to the invalid field. | Modify | Merge V1 schema validators into one native validation engine plus explicit official wrappers with bounded JSON-pointer diagnostics. | V1 has overlapping implementations and incomplete schema semantics. |
| V2-FR-SCHEMA-021 | Official schema validator errors must include `invalid_fields` as a bounded list of `{path, code, message}` objects where practical. | Modify | Merge V1 schema validators into one native validation engine plus explicit official wrappers with bounded JSON-pointer diagnostics. | V1 has overlapping implementations and incomplete schema semantics. |
| V2-FR-SCHEMA-022 | Invalid-field paths must use a deterministic format such as JSON Pointer. | Modify | Merge V1 schema validators into one native validation engine plus explicit official wrappers with bounded JSON-pointer diagnostics. | V1 has overlapping implementations and incomplete schema semantics. |
| V2-FR-SCHEMA-023 | Dot-path strings may be allowed for human-readable display when documented. | Modify | Merge V1 schema validators into one native validation engine plus explicit official wrappers with bounded JSON-pointer diagnostics. | V1 has overlapping implementations and incomplete schema semantics. |
| V2-FR-SCHEMA-024 | Nested validation errors must include the nearest valid parent path when the exact path cannot be determined. | Modify | Merge V1 schema validators into one native validation engine plus explicit official wrappers with bounded JSON-pointer diagnostics. | V1 has overlapping implementations and incomplete schema semantics. |
| V2-FR-SCHEMA-025 | Schema validation error details must remain bounded and redacted. | Modify | Merge V1 schema validators into one native validation engine plus explicit official wrappers with bounded JSON-pointer diagnostics. | V1 has overlapping implementations and incomplete schema semantics. |
| V2-FR-SCHEMA-026 | Evidence validation must require source, timestamp, and evidence type. | Modify | Merge V1 schema validators into one native validation engine plus explicit official wrappers with bounded JSON-pointer diagnostics. | V1 has overlapping implementations and incomplete schema semantics. |
| V2-FR-SCHEMA-027 | Approval packet validation must require action, reason, evidence, risk class, and approval status. | Modify | Merge V1 schema validators into one native validation engine plus explicit official wrappers with bounded JSON-pointer diagnostics. | V1 has overlapping implementations and incomplete schema semantics. |
| V2-FR-SCHEMA-028 | Registry entry validation must require name, version, category or domain, risk level, and status. | Modify | Merge V1 schema validators into one native validation engine plus explicit official wrappers with bounded JSON-pointer diagnostics. | V1 has overlapping implementations and incomplete schema semantics. |
| V2-FR-SCHEMA-029 | Risk-level validation must use the central `VALID_RISK_LEVELS` model. | Modify | Merge V1 schema validators into one native validation engine plus explicit official wrappers with bounded JSON-pointer diagnostics. | V1 has overlapping implementations and incomplete schema semantics. |
| V2-FR-SCHEMA-030 | Environment validation must use the central `VALID_ENVIRONMENT_MODES` model unless a stricter allowlist is supplied. | Modify | Merge V1 schema validators into one native validation engine plus explicit official wrappers with bounded JSON-pointer diagnostics. | V1 has overlapping implementations and incomplete schema semantics. |
| V2-FR-SCHEMA-031 | Blocked action validation must require an `action` field. | Modify | Merge V1 schema validators into one native validation engine plus explicit official wrappers with bounded JSON-pointer diagnostics. | V1 has overlapping implementations and incomplete schema semantics. |
| V2-FR-SCHEMA-032 | Blocked action validation must fail closed when `payload["action"]` appears in `blocked_actions`. | Modify | Merge V1 schema validators into one native validation engine plus explicit official wrappers with bounded JSON-pointer diagnostics. | V1 has overlapping implementations and incomplete schema semantics. |
| V2-FR-SCHEMA-033 | Freshness validation must require a timestamp field with default `as_of`. | Modify | Merge V1 schema validators into one native validation engine plus explicit official wrappers with bounded JSON-pointer diagnostics. | V1 has overlapping implementations and incomplete schema semantics. |
| V2-FR-SCHEMA-034 | Freshness validation must support a configurable timestamp field. | Modify | Merge V1 schema validators into one native validation engine plus explicit official wrappers with bounded JSON-pointer diagnostics. | V1 has overlapping implementations and incomplete schema semantics. |
| V2-FR-SCHEMA-035 | Freshness validation must compare against injected timestamps where supported. | Modify | Merge V1 schema validators into one native validation engine plus explicit official wrappers with bounded JSON-pointer diagnostics. | V1 has overlapping implementations and incomplete schema semantics. |
| V2-FR-SCHEMA-036 | Artifact reference validation must require `artifact_id`, `version`, and at least one location field such as `storage_path`, `uri`, or `content_hash`. | Modify | Merge V1 schema validators into one native validation engine plus explicit official wrappers with bounded JSON-pointer diagnostics. | V1 has overlapping implementations and incomplete schema semantics. |
| V2-FR-SCHEMA-037 | Schema validation helpers must enforce configured maximum depth, maximum field count, maximum issue count, maximum sample count, and maximum payload size. | Modify | Merge V1 schema validators into one native validation engine plus explicit official wrappers with bounded JSON-pointer diagnostics. | V1 has overlapping implementations and incomplete schema semantics. |
| V2-FR-SCHEMA-038 | Resource-limit failures must return bounded diagnostics. | Modify | Merge V1 schema validators into one native validation engine plus explicit official wrappers with bounded JSON-pointer diagnostics. | V1 has overlapping implementations and incomplete schema semantics. |
| V2-FR-SCHEMA-039 | Resource-limit failures must include the relevant path or validation area where available. | Modify | Merge V1 schema validators into one native validation engine plus explicit official wrappers with bounded JSON-pointer diagnostics. | V1 has overlapping implementations and incomplete schema semantics. |
| V2-FR-SCHEMA-040 | Schema validation helpers must avoid dumping entire payloads in errors. | Modify | Merge V1 schema validators into one native validation engine plus explicit official wrappers with bounded JSON-pointer diagnostics. | V1 has overlapping implementations and incomplete schema semantics. |


#### Security Utilities


| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
| --- | --- | --- | --- | --- |
| V2-FR-SEC-001 | The module must provide sensitive-key detection. | Modify | Preserve native redaction/hash/encryption behavior, enforce one return contract, Argon2id policy, depth limits, audited narrow allowlists, and secret-safe failures. | V1 security is valuable but has bifurcated and fallback behavior. |
| V2-FR-SEC-002 | The module must provide scalar redaction. | Modify | Preserve native redaction/hash/encryption behavior, enforce one return contract, Argon2id policy, depth limits, audited narrow allowlists, and secret-safe failures. | V1 security is valuable but has bifurcated and fallback behavior. |
| V2-FR-SEC-003 | The module must provide text redaction. | Modify | Preserve native redaction/hash/encryption behavior, enforce one return contract, Argon2id policy, depth limits, audited narrow allowlists, and secret-safe failures. | V1 security is valuable but has bifurcated and fallback behavior. |
| V2-FR-SEC-004 | The module must provide mapping redaction. | Modify | Preserve native redaction/hash/encryption behavior, enforce one return contract, Argon2id policy, depth limits, audited narrow allowlists, and secret-safe failures. | V1 security is valuable but has bifurcated and fallback behavior. |
| V2-FR-SEC-005 | The module must provide password hashing. | Modify | Preserve native redaction/hash/encryption behavior, enforce one return contract, Argon2id policy, depth limits, audited narrow allowlists, and secret-safe failures. | V1 security is valuable but has bifurcated and fallback behavior. |
| V2-FR-SEC-006 | The module must provide password verification. | Modify | Preserve native redaction/hash/encryption behavior, enforce one return contract, Argon2id policy, depth limits, audited narrow allowlists, and secret-safe failures. | V1 security is valuable but has bifurcated and fallback behavior. |
| V2-FR-SEC-007 | The module must provide encryption key loading. | Modify | Preserve native redaction/hash/encryption behavior, enforce one return contract, Argon2id policy, depth limits, audited narrow allowlists, and secret-safe failures. | V1 security is valuable but has bifurcated and fallback behavior. |
| V2-FR-SEC-008 | The module must provide encryption. | Modify | Preserve native redaction/hash/encryption behavior, enforce one return contract, Argon2id policy, depth limits, audited narrow allowlists, and secret-safe failures. | V1 security is valuable but has bifurcated and fallback behavior. |
| V2-FR-SEC-009 | The module must provide decryption. | Modify | Preserve native redaction/hash/encryption behavior, enforce one return contract, Argon2id policy, depth limits, audited narrow allowlists, and secret-safe failures. | V1 security is valuable but has bifurcated and fallback behavior. |
| V2-FR-SEC-010 | The module must provide active secret-version selection. | Modify | Preserve native redaction/hash/encryption behavior, enforce one return contract, Argon2id policy, depth limits, audited narrow allowlists, and secret-safe failures. | V1 security is valuable but has bifurcated and fallback behavior. |
| V2-FR-SEC-011 | Secret-like keys must be detected case-insensitively. | Modify | Preserve native redaction/hash/encryption behavior, enforce one return contract, Argon2id policy, depth limits, audited narrow allowlists, and secret-safe failures. | V1 security is valuable but has bifurcated and fallback behavior. |
| V2-FR-SEC-012 | Redaction must use a denylist-first strategy. | Modify | Preserve native redaction/hash/encryption behavior, enforce one return contract, Argon2id policy, depth limits, audited narrow allowlists, and secret-safe failures. | V1 security is valuable but has bifurcated and fallback behavior. |
| V2-FR-SEC-013 | The denylist must include password, passwd, token, secret, key, credential, authorization, auth, API key, private key, access key, login, session, cookie, bearer, broker, and encryption-related patterns. | Modify | Preserve native redaction/hash/encryption behavior, enforce one return contract, Argon2id policy, depth limits, audited narrow allowlists, and secret-safe failures. | V1 security is valuable but has bifurcated and fallback behavior. |
| V2-FR-SEC-014 | Denylist matching must be case-insensitive. | Modify | Preserve native redaction/hash/encryption behavior, enforce one return contract, Argon2id policy, depth limits, audited narrow allowlists, and secret-safe failures. | V1 security is valuable but has bifurcated and fallback behavior. |
| V2-FR-SEC-015 | Denylist matching must support partial-key matching for common sensitive names. | Modify | Preserve native redaction/hash/encryption behavior, enforce one return contract, Argon2id policy, depth limits, audited narrow allowlists, and secret-safe failures. | V1 security is valuable but has bifurcated and fallback behavior. |
| V2-FR-SEC-016 | Redaction helpers must provide an explicit allowlist mechanism for fields that are safe to log despite matching denylist patterns. | Modify | Preserve native redaction/hash/encryption behavior, enforce one return contract, Argon2id policy, depth limits, audited narrow allowlists, and secret-safe failures. | V1 security is valuable but has bifurcated and fallback behavior. |
| V2-FR-SEC-017 | Redaction allowlist entries must be audited through configuration, tests, or documented approval. | Modify | Preserve native redaction/hash/encryption behavior, enforce one return contract, Argon2id policy, depth limits, audited narrow allowlists, and secret-safe failures. | V1 security is valuable but has bifurcated and fallback behavior. |
| V2-FR-SEC-018 | Redaction allowlist decisions must be narrow and field-specific. | Modify | Preserve native redaction/hash/encryption behavior, enforce one return contract, Argon2id policy, depth limits, audited narrow allowlists, and secret-safe failures. | V1 security is valuable but has bifurcated and fallback behavior. |
| V2-FR-SEC-019 | Redaction allowlist decisions must not allow broad wildcard exposure of secrets. | Modify | Preserve native redaction/hash/encryption behavior, enforce one return contract, Argon2id policy, depth limits, audited narrow allowlists, and secret-safe failures. | V1 security is valuable but has bifurcated and fallback behavior. |
| V2-FR-SEC-020 | Redaction helpers must expose diagnostics showing which fields were redacted without exposing redacted values. | Modify | Preserve native redaction/hash/encryption behavior, enforce one return contract, Argon2id policy, depth limits, audited narrow allowlists, and secret-safe failures. | V1 security is valuable but has bifurcated and fallback behavior. |
| V2-FR-SEC-021 | Redaction must preserve non-sensitive fields. | Modify | Preserve native redaction/hash/encryption behavior, enforce one return contract, Argon2id policy, depth limits, audited narrow allowlists, and secret-safe failures. | V1 security is valuable but has bifurcated and fallback behavior. |
| V2-FR-SEC-022 | Redaction must handle nested dictionaries and lists. | Modify | Preserve native redaction/hash/encryption behavior, enforce one return contract, Argon2id policy, depth limits, audited narrow allowlists, and secret-safe failures. | V1 security is valuable but has bifurcated and fallback behavior. |
| V2-FR-SEC-023 | Redaction must stop safely at `MAX_REDACTION_DEPTH` and mark truncated structures. | Modify | Preserve native redaction/hash/encryption behavior, enforce one return contract, Argon2id policy, depth limits, audited narrow allowlists, and secret-safe failures. | V1 security is valuable but has bifurcated and fallback behavior. |
| V2-FR-SEC-024 | Redaction must be applied before sensitive values appear in logs, error responses, metadata, remediation text, tool responses, events, notifications, metrics, health checks, dead-letter diagnostics, or canonical JSON payloads. | Modify | Preserve native redaction/hash/encryption behavior, enforce one return contract, Argon2id policy, depth limits, audited narrow allowlists, and secret-safe failures. | V1 security is valuable but has bifurcated and fallback behavior. |
| V2-FR-SEC-025 | Canonical JSON serialization must redact sensitive values by default unless a caller explicitly disables redaction in a trusted internal context. | Reject | Keep canonical serialization pure and deterministic; require explicit redaction before serialization or an explicit trusted wrapper. | Implicit redaction changes payload identity and mixes security policy into serialization. |
| V2-FR-SEC-026 | Canonical JSON serialization must expose redaction configuration through documented options. | Modify | Preserve native redaction/hash/encryption behavior, enforce one return contract, Argon2id policy, depth limits, audited narrow allowlists, and secret-safe failures. | V1 security is valuable but has bifurcated and fallback behavior. |
| V2-FR-SEC-027 | Password hashing must use Argon2id as the preferred production algorithm. | Modify | Preserve native redaction/hash/encryption behavior, enforce one return contract, Argon2id policy, depth limits, audited narrow allowlists, and secret-safe failures. | V1 security is valuable but has bifurcated and fallback behavior. |
| V2-FR-SEC-028 | If Argon2id is unavailable, the implementation must fail clearly unless a separately approved fallback is configured. | Modify | Preserve native redaction/hash/encryption behavior, enforce one return contract, Argon2id policy, depth limits, audited narrow allowlists, and secret-safe failures. | V1 security is valuable but has bifurcated and fallback behavior. |
| V2-FR-SEC-029 | Password verification must use constant-time comparison where relevant. | Modify | Preserve native redaction/hash/encryption behavior, enforce one return contract, Argon2id policy, depth limits, audited narrow allowlists, and secret-safe failures. | V1 security is valuable but has bifurcated and fallback behavior. |
| V2-FR-SEC-030 | Encryption features must use `cryptography.fernet.Fernet` for phase 1 symmetric encryption when encryption is enabled. | Modify | Preserve native redaction/hash/encryption behavior, enforce one return contract, Argon2id policy, depth limits, audited narrow allowlists, and secret-safe failures. | V1 security is valuable but has bifurcated and fallback behavior. |
| V2-FR-SEC-031 | Missing `cryptography` must not break module import, but encryption/decryption calls must fail with a clear configuration error. | Modify | Preserve native redaction/hash/encryption behavior, enforce one return contract, Argon2id policy, depth limits, audited narrow allowlists, and secret-safe failures. | V1 security is valuable but has bifurcated and fallback behavior. |
| V2-FR-SEC-032 | Encryption key loading must never log key material. | Modify | Preserve native redaction/hash/encryption behavior, enforce one return contract, Argon2id policy, depth limits, audited narrow allowlists, and secret-safe failures. | V1 security is valuable but has bifurcated and fallback behavior. |
| V2-FR-SEC-033 | Environment-based encryption keys must use `ENCRYPTION_KEY`. | Modify | Preserve native redaction/hash/encryption behavior, enforce one return contract, Argon2id policy, depth limits, audited narrow allowlists, and secret-safe failures. | V1 security is valuable but has bifurcated and fallback behavior. |
| V2-FR-SEC-034 | `ENCRYPTION_KEY` must be a 32-byte URL-safe base64-encoded Fernet key when environment-based key loading is used. | Modify | Preserve native redaction/hash/encryption behavior, enforce one return contract, Argon2id policy, depth limits, audited narrow allowlists, and secret-safe failures. | V1 security is valuable but has bifurcated and fallback behavior. |
| V2-FR-SEC-035 | Encryption and decryption failures must not expose plaintext or key material. | Modify | Preserve native redaction/hash/encryption behavior, enforce one return contract, Argon2id policy, depth limits, audited narrow allowlists, and secret-safe failures. | V1 security is valuable but has bifurcated and fallback behavior. |
| V2-FR-SEC-036 | Secret version selection must choose the active item with the highest numeric version. | Modify | Preserve native redaction/hash/encryption behavior, enforce one return contract, Argon2id policy, depth limits, audited narrow allowlists, and secret-safe failures. | V1 security is valuable but has bifurcated and fallback behavior. |
| V2-FR-SEC-037 | If no active secret version exists, the function must raise `SecurityError` or return a structured `SECRET_VERSION_NOT_FOUND` error at the tool boundary. | Modify | Preserve native redaction/hash/encryption behavior, enforce one return contract, Argon2id policy, depth limits, audited narrow allowlists, and secret-safe failures. | V1 security is valuable but has bifurcated and fallback behavior. |
| V2-FR-SEC-038 | Duplicate active secret versions with the same numeric version must fail closed with `SECRET_VERSION_CONFLICT`. | Modify | Preserve native redaction/hash/encryption behavior, enforce one return contract, Argon2id policy, depth limits, audited narrow allowlists, and secret-safe failures. | V1 security is valuable but has bifurcated and fallback behavior. |


#### Runtime Settings


| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
| --- | --- | --- | --- | --- |
| V2-FR-SET-001 | The module must define immutable typed runtime settings. | Modify | Replace the current broad singleton with immutable explicitly loaded settings, mapping load/injection, clear precedence, and no import-time `.env` read. | V1 settings are used but combine live and research domain models and lack advertised injection helpers. |
| V2-FR-SET-002 | Runtime settings must include environment, log level, data directory, cache directory, audit directory, timezone, and strict validation. | Modify | Replace the current broad singleton with immutable explicitly loaded settings, mapping load/injection, clear precedence, and no import-time `.env` read. | V1 settings are used but combine live and research domain models and lack advertised injection helpers. |
| V2-FR-SET-003 | Runtime settings must include logging configuration. | Modify | Replace the current broad singleton with immutable explicitly loaded settings, mapping load/injection, clear precedence, and no import-time `.env` read. | V1 settings are used but combine live and research domain models and lack advertised injection helpers. |
| V2-FR-SET-004 | Logging configuration must include optional log directory, file logging enablement, rotation maximum size, retained file count, and retention deletion policy. | Modify | Replace the current broad singleton with immutable explicitly loaded settings, mapping load/injection, clear precedence, and no import-time `.env` read. | V1 settings are used but combine live and research domain models and lack advertised injection helpers. |
| V2-FR-SET-005 | Logging configuration must include human-readable console format selection and color enablement or disablement. | Modify | Replace the current broad singleton with immutable explicitly loaded settings, mapping load/injection, clear precedence, and no import-time `.env` read. | V1 settings are used but combine live and research domain models and lack advertised injection helpers. |
| V2-FR-SET-006 | Runtime settings must include auth configuration. | Modify | Replace the current broad singleton with immutable explicitly loaded settings, mapping load/injection, clear precedence, and no import-time `.env` read. | V1 settings are used but combine live and research domain models and lack advertised injection helpers. |
| V2-FR-SET-007 | Runtime settings must include Event Bus configuration. | Defer | Add this settings subsection only when the related production capability is accepted. | The dependent capability is deferred. |
| V2-FR-SET-008 | Runtime settings must include notification configuration. | Defer | Add this settings subsection only when the related production capability is accepted. | The dependent capability is deferred. |
| V2-FR-SET-009 | Runtime settings must include observability configuration. | Defer | Add this settings subsection only when the related production capability is accepted. | The dependent capability is deferred. |
| V2-FR-SET-010 | The module must load runtime settings from explicit calls only. | Modify | Replace the current broad singleton with immutable explicitly loaded settings, mapping load/injection, clear precedence, and no import-time `.env` read. | V1 settings are used but combine live and research domain models and lack advertised injection helpers. |
| V2-FR-SET-011 | The module must load runtime settings from mappings. | Modify | Replace the current broad singleton with immutable explicitly loaded settings, mapping load/injection, clear precedence, and no import-time `.env` read. | V1 settings are used but combine live and research domain models and lack advertised injection helpers. |
| V2-FR-SET-012 | The module must inject runtime settings into an explicitly supplied mutable target mapping. | Modify | Replace the current broad singleton with immutable explicitly loaded settings, mapping load/injection, clear precedence, and no import-time `.env` read. | V1 settings are used but combine live and research domain models and lack advertised injection helpers. |
| V2-FR-SET-013 | Required settings must have deterministic defaults where safe. | Modify | Replace the current broad singleton with immutable explicitly loaded settings, mapping load/injection, clear precedence, and no import-time `.env` read. | V1 settings are used but combine live and research domain models and lack advertised injection helpers. |
| V2-FR-SET-014 | Sensitive settings must not be logged. | Modify | Replace the current broad singleton with immutable explicitly loaded settings, mapping load/injection, clear precedence, and no import-time `.env` read. | V1 settings are used but combine live and research domain models and lack advertised injection helpers. |
| V2-FR-SET-015 | Environment names must be validated. | Modify | Replace the current broad singleton with immutable explicitly loaded settings, mapping load/injection, clear precedence, and no import-time `.env` read. | V1 settings are used but combine live and research domain models and lack advertised injection helpers. |
| V2-FR-SET-016 | Path settings must use `Path` objects. | Modify | Replace the current broad singleton with immutable explicitly loaded settings, mapping load/injection, clear precedence, and no import-time `.env` read. | V1 settings are used but combine live and research domain models and lack advertised injection helpers. |
| V2-FR-SET-017 | `.env` loading must be optional and dependency-aware. | Modify | Replace the current broad singleton with immutable explicitly loaded settings, mapping load/injection, clear precedence, and no import-time `.env` read. | V1 settings are used but combine live and research domain models and lack advertised injection helpers. |
| V2-FR-SET-018 | Settings source precedence must be explicit mapping/function arguments, then environment variables, then `.env` file, then safe defaults. | Modify | Replace the current broad singleton with immutable explicitly loaded settings, mapping load/injection, clear precedence, and no import-time `.env` read. | V1 settings are used but combine live and research domain models and lack advertised injection helpers. |
| V2-FR-SET-019 | Importing `app.services.utils` must not read `.env`. | Modify | Replace the current broad singleton with immutable explicitly loaded settings, mapping load/injection, clear precedence, and no import-time `.env` read. | V1 settings are used but combine live and research domain models and lack advertised injection helpers. |
| V2-FR-SET-020 | Optional dependency absence must not break import. | Modify | Replace the current broad singleton with immutable explicitly loaded settings, mapping load/injection, clear precedence, and no import-time `.env` read. | V1 settings are used but combine live and research domain models and lack advertised injection helpers. |
| V2-FR-SET-021 | Optional dependency absence must fail only when the requested feature requires the dependency. | Modify | Replace the current broad singleton with immutable explicitly loaded settings, mapping load/injection, clear precedence, and no import-time `.env` read. | V1 settings are used but combine live and research domain models and lack advertised injection helpers. |
| V2-FR-SET-022 | Invalid settings must fail clearly with configuration errors. | Modify | Replace the current broad singleton with immutable explicitly loaded settings, mapping load/injection, clear precedence, and no import-time `.env` read. | V1 settings are used but combine live and research domain models and lack advertised injection helpers. |
| V2-FR-SET-023 | `strict_validation=True` must escalate non-critical validation warnings to failures where the caller asks settings to enforce strict behavior. | Modify | Replace the current broad singleton with immutable explicitly loaded settings, mapping load/injection, clear precedence, and no import-time `.env` read. | V1 settings are used but combine live and research domain models and lack advertised injection helpers. |
| V2-FR-SET-024 | `strict_validation=False` must allow warnings to be returned or logged without failing settings load. | Modify | Replace the current broad singleton with immutable explicitly loaded settings, mapping load/injection, clear precedence, and no import-time `.env` read. | V1 settings are used but combine live and research domain models and lack advertised injection helpers. |
| V2-FR-SET-025 | `inject_runtime_settings` must mutate only the provided target mapping and return that mapping. | Modify | Replace the current broad singleton with immutable explicitly loaded settings, mapping load/injection, clear precedence, and no import-time `.env` read. | V1 settings are used but combine live and research domain models and lack advertised injection helpers. |
| V2-FR-SET-026 | Default runtime paths must resolve under `HARUQUANT_HOME` when configured. | Modify | Replace the current broad singleton with immutable explicitly loaded settings, mapping load/injection, clear precedence, and no import-time `.env` read. | V1 settings are used but combine live and research domain models and lack advertised injection helpers. |
| V2-FR-SET-027 | When `HARUQUANT_HOME` is not configured, local/test defaults must resolve under a deterministic `.haruquant` directory beneath the current working directory. | Modify | Replace the current broad singleton with immutable explicitly loaded settings, mapping load/injection, clear precedence, and no import-time `.env` read. | V1 settings are used but combine live and research domain models and lack advertised injection helpers. |
| V2-FR-SET-028 | Production deployments must configure `HARUQUANT_HOME` explicitly. | Modify | Replace the current broad singleton with immutable explicitly loaded settings, mapping load/injection, clear precedence, and no import-time `.env` read. | V1 settings are used but combine live and research domain models and lack advertised injection helpers. |
| V2-FR-SET-029 | Default directories must be `data`, `cache`, and `audit` under the resolved HaruQuant home directory. | Modify | Replace the current broad singleton with immutable explicitly loaded settings, mapping load/injection, clear precedence, and no import-time `.env` read. | V1 settings are used but combine live and research domain models and lack advertised injection helpers. |


#### Event Bus and Pub/Sub


| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
| --- | --- | --- | --- | --- |
| V2-FR-EVENT-001 | The system must provide a shared Event Bus abstraction for internal utility, workflow, alert, and error-routing events. | Defer | Exclude from the initial rebuild; reassess as a production infrastructure slice after ownership, configuration, and real callers are confirmed. | V1 versions are disconnected and the V2 proposal is substantially more complex than current evidence supports. |
| V2-FR-EVENT-002 | The system must provide an in-process pub/sub mechanism suitable for local development, unit tests, and deterministic workflow tests. | Defer | Exclude from the initial rebuild; reassess as a production infrastructure slice after ownership, configuration, and real callers are confirmed. | V1 versions are disconnected and the V2 proposal is substantially more complex than current evidence supports. |
| V2-FR-EVENT-003 | The Event Bus must support disabled or no-op adapter behavior for tests and local development where event delivery is intentionally suppressed. | Defer | Exclude from the initial rebuild; reassess as a production infrastructure slice after ownership, configuration, and real callers are confirmed. | V1 versions are disconnected and the V2 proposal is substantially more complex than current evidence supports. |
| V2-FR-EVENT-004 | The system must define a standard event envelope. | Defer | Exclude from the initial rebuild; reassess as a production infrastructure slice after ownership, configuration, and real callers are confirmed. | V1 versions are disconnected and the V2 proposal is substantially more complex than current evidence supports. |
| V2-FR-EVENT-005 | The standard event envelope must include `event_id`, `event_type`, `event_version`, `source`, `severity`, `timestamp`, `request_id`, `workflow_id`, `correlation_id`, `causation_id`, `idempotency_key`, `payload`, and `metadata`. | Defer | Exclude from the initial rebuild; reassess as a production infrastructure slice after ownership, configuration, and real callers are confirmed. | V1 versions are disconnected and the V2 proposal is substantially more complex than current evidence supports. |
| V2-FR-EVENT-006 | Event payloads must be JSON-serializable or fail validation clearly. | Defer | Exclude from the initial rebuild; reassess as a production infrastructure slice after ownership, configuration, and real callers are confirmed. | V1 versions are disconnected and the V2 proposal is substantially more complex than current evidence supports. |
| V2-FR-EVENT-007 | Event payloads must be redacted before logging, metrics labeling, notification routing, audit serialization, or dead-letter forwarding. | Defer | Exclude from the initial rebuild; reassess as a production infrastructure slice after ownership, configuration, and real callers are confirmed. | V1 versions are disconnected and the V2 proposal is substantially more complex than current evidence supports. |
| V2-FR-EVENT-008 | The Event Bus must support publish and subscribe operations. | Defer | Exclude from the initial rebuild; reassess as a production infrastructure slice after ownership, configuration, and real callers are confirmed. | V1 versions are disconnected and the V2 proposal is substantially more complex than current evidence supports. |
| V2-FR-EVENT-009 | The Event Bus must support topic or event-type subscriptions. | Defer | Exclude from the initial rebuild; reassess as a production infrastructure slice after ownership, configuration, and real callers are confirmed. | V1 versions are disconnected and the V2 proposal is substantially more complex than current evidence supports. |
| V2-FR-EVENT-010 | The Event Bus must support handler registration and unregistration. | Defer | Exclude from the initial rebuild; reassess as a production infrastructure slice after ownership, configuration, and real callers are confirmed. | V1 versions are disconnected and the V2 proposal is substantially more complex than current evidence supports. |
| V2-FR-EVENT-011 | The in-process Event Bus must guarantee deterministic, ordered handler execution per event type to ensure reproducible test outcomes. | Defer | Exclude from the initial rebuild; reassess as a production infrastructure slice after ownership, configuration, and real callers are confirmed. | V1 versions are disconnected and the V2 proposal is substantially more complex than current evidence supports. |
| V2-FR-EVENT-012 | Distributed broker adapters are not required to guarantee global ordering unless the adapter explicitly documents that guarantee. | Defer | Exclude from the initial rebuild; reassess as a production infrastructure slice after ownership, configuration, and real callers are confirmed. | V1 versions are disconnected and the V2 proposal is substantially more complex than current evidence supports. |
| V2-FR-EVENT-013 | The Event Bus must support error isolation so one failing subscriber does not silently prevent other subscribers from receiving the event. | Defer | Exclude from the initial rebuild; reassess as a production infrastructure slice after ownership, configuration, and real callers are confirmed. | V1 versions are disconnected and the V2 proposal is substantially more complex than current evidence supports. |
| V2-FR-EVENT-014 | The Event Bus must route subscriber failures to the error-routing mechanism. | Defer | Exclude from the initial rebuild; reassess as a production infrastructure slice after ownership, configuration, and real callers are confirmed. | V1 versions are disconnected and the V2 proposal is substantially more complex than current evidence supports. |
| V2-FR-EVENT-015 | The Event Bus must support retry policy metadata for delivery failures. | Defer | Exclude from the initial rebuild; reassess as a production infrastructure slice after ownership, configuration, and real callers are confirmed. | V1 versions are disconnected and the V2 proposal is substantially more complex than current evidence supports. |
| V2-FR-EVENT-016 | The Event Bus must support dead-letter routing for events that exceed retry limits. | Defer | Exclude from the initial rebuild; reassess as a production infrastructure slice after ownership, configuration, and real callers are confirmed. | V1 versions are disconnected and the V2 proposal is substantially more complex than current evidence supports. |
| V2-FR-EVENT-017 | The Event Bus must support idempotency keys to reduce duplicate event processing. | Defer | Exclude from the initial rebuild; reassess as a production infrastructure slice after ownership, configuration, and real callers are confirmed. | V1 versions are disconnected and the V2 proposal is substantially more complex than current evidence supports. |
| V2-FR-EVENT-018 | Idempotency keys must have both a configurable TTL and a configurable maximum cache size. | Defer | Exclude from the initial rebuild; reassess as a production infrastructure slice after ownership, configuration, and real callers are confirmed. | V1 versions are disconnected and the V2 proposal is substantially more complex than current evidence supports. |
| V2-FR-EVENT-019 | The default idempotency TTL must come from `IDEMPOTENCY_TTL_SECONDS`. | Defer | Exclude from the initial rebuild; reassess as a production infrastructure slice after ownership, configuration, and real callers are confirmed. | V1 versions are disconnected and the V2 proposal is substantially more complex than current evidence supports. |
| V2-FR-EVENT-020 | Idempotency entries must store compact metadata rather than full event payloads by default. | Defer | Exclude from the initial rebuild; reassess as a production infrastructure slice after ownership, configuration, and real callers are confirmed. | V1 versions are disconnected and the V2 proposal is substantially more complex than current evidence supports. |
| V2-FR-EVENT-021 | Idempotency entries must store only `event_id`, `idempotency_key`, sanitized canonical payload hash, creation timestamp, expiry timestamp, and compact delivery status metadata. | Defer | Exclude from the initial rebuild; reassess as a production infrastructure slice after ownership, configuration, and real callers are confirmed. | V1 versions are disconnected and the V2 proposal is substantially more complex than current evidence supports. |
| V2-FR-EVENT-022 | Idempotency entries must never store raw payloads, credentials, tokens, approval packets, notification bodies, or broker/private data. | Defer | Exclude from the initial rebuild; reassess as a production infrastructure slice after ownership, configuration, and real callers are confirmed. | V1 versions are disconnected and the V2 proposal is substantially more complex than current evidence supports. |
| V2-FR-EVENT-023 | Idempotency duplicate detection may use hashes of sanitized canonical event payloads and must not retain full sensitive payloads. | Defer | Exclude from the initial rebuild; reassess as a production infrastructure slice after ownership, configuration, and real callers are confirmed. | V1 versions are disconnected and the V2 proposal is substantially more complex than current evidence supports. |
| V2-FR-EVENT-024 | Idempotency hashing must use a documented collision-resistant hash algorithm. | Defer | Exclude from the initial rebuild; reassess as a production infrastructure slice after ownership, configuration, and real callers are confirmed. | V1 versions are disconnected and the V2 proposal is substantially more complex than current evidence supports. |
| V2-FR-EVENT-025 | If an idempotency key matches but the sanitized canonical payload hash differs, the Event Bus must return deterministic `IDEMPOTENCY_CONFLICT` diagnostics and must not deliver the conflicting event. | Defer | Exclude from the initial rebuild; reassess as a production infrastructure slice after ownership, configuration, and real callers are confirmed. | V1 versions are disconnected and the V2 proposal is substantially more complex than current evidence supports. |
| V2-FR-EVENT-026 | If a true hash collision is suspected because distinct canonical payloads produce the same hash, the behavior must fail closed with `IDEMPOTENCY_HASH_COLLISION_SUSPECTED` unless a later approved design stores additional non-sensitive disambiguation metadata. | Defer | Exclude from the initial rebuild; reassess as a production infrastructure slice after ownership, configuration, and real callers are confirmed. | V1 versions are disconnected and the V2 proposal is substantially more complex than current evidence supports. |
| V2-FR-EVENT-027 | Idempotency-key storage must not grow without bound in long-running processes. | Defer | Exclude from the initial rebuild; reassess as a production infrastructure slice after ownership, configuration, and real callers are confirmed. | V1 versions are disconnected and the V2 proposal is substantially more complex than current evidence supports. |
| V2-FR-EVENT-028 | Expired idempotency keys must be evicted deterministically. | Defer | Exclude from the initial rebuild; reassess as a production infrastructure slice after ownership, configuration, and real callers are confirmed. | V1 versions are disconnected and the V2 proposal is substantially more complex than current evidence supports. |
| V2-FR-EVENT-029 | The default idempotency cache eviction policy must evict expired entries first, then oldest entries. | Defer | Exclude from the initial rebuild; reassess as a production infrastructure slice after ownership, configuration, and real callers are confirmed. | V1 versions are disconnected and the V2 proposal is substantially more complex than current evidence supports. |
| V2-FR-EVENT-030 | Idempotency cache eviction must be observable through logs and metrics. | Defer | Exclude from the initial rebuild; reassess as a production infrastructure slice after ownership, configuration, and real callers are confirmed. | V1 versions are disconnected and the V2 proposal is substantially more complex than current evidence supports. |
| V2-FR-EVENT-031 | Idempotency cache state must not expose sensitive payloads, raw event bodies, tokens, credentials, approval packets, or private data. | Defer | Exclude from the initial rebuild; reassess as a production infrastructure slice after ownership, configuration, and real callers are confirmed. | V1 versions are disconnected and the V2 proposal is substantially more complex than current evidence supports. |
| V2-FR-EVENT-032 | Duplicate idempotency keys with different payload hashes must fail safely or emit deterministic conflict diagnostics. | Defer | Exclude from the initial rebuild; reassess as a production infrastructure slice after ownership, configuration, and real callers are confirmed. | V1 versions are disconnected and the V2 proposal is substantially more complex than current evidence supports. |
| V2-FR-EVENT-033 | Idempotency tracking must be testable with injected clocks or deterministic time controls. | Defer | Exclude from the initial rebuild; reassess as a production infrastructure slice after ownership, configuration, and real callers are confirmed. | V1 versions are disconnected and the V2 proposal is substantially more complex than current evidence supports. |
| V2-FR-EVENT-034 | The Event Bus must support correlation IDs across tool calls, logs, notifications, and metrics. | Defer | Exclude from the initial rebuild; reassess as a production infrastructure slice after ownership, configuration, and real callers are confirmed. | V1 versions are disconnected and the V2 proposal is substantially more complex than current evidence supports. |
| V2-FR-EVENT-035 | The Event Bus must expose bounded queue depth or handler backlog diagnostics. | Defer | Exclude from the initial rebuild; reassess as a production infrastructure slice after ownership, configuration, and real callers are confirmed. | V1 versions are disconnected and the V2 proposal is substantially more complex than current evidence supports. |
| V2-FR-EVENT-036 | Event Bus delivery diagnostics must include delivered, failed, retried, dead-lettered, dropped counts, and queue depth where applicable. | Defer | Exclude from the initial rebuild; reassess as a production infrastructure slice after ownership, configuration, and real callers are confirmed. | V1 versions are disconnected and the V2 proposal is substantially more complex than current evidence supports. |
| V2-FR-EVENT-037 | When the Event Bus queue is full, publish operations must immediately return a deterministic `QUEUE_FULL` or `BACKPRESSURE_EXCEEDED` error code. | Defer | Exclude from the initial rebuild; reassess as a production infrastructure slice after ownership, configuration, and real callers are confirmed. | V1 versions are disconnected and the V2 proposal is substantially more complex than current evidence supports. |
| V2-FR-EVENT-038 | Queue-full behavior must return `BACKPRESSURE_EXCEEDED` when the caller can retry later. | Defer | Exclude from the initial rebuild; reassess as a production infrastructure slice after ownership, configuration, and real callers are confirmed. | V1 versions are disconnected and the V2 proposal is substantially more complex than current evidence supports. |
| V2-FR-EVENT-039 | Queue-full behavior may return `QUEUE_FULL` for lower-level queue diagnostics. | Defer | Exclude from the initial rebuild; reassess as a production infrastructure slice after ownership, configuration, and real callers are confirmed. | V1 versions are disconnected and the V2 proposal is substantially more complex than current evidence supports. |
| V2-FR-EVENT-040 | Event publishers must receive enough structured queue-full detail to implement retry, degradation, or fail-closed behavior. | Defer | Exclude from the initial rebuild; reassess as a production infrastructure slice after ownership, configuration, and real callers are confirmed. | V1 versions are disconnected and the V2 proposal is substantially more complex than current evidence supports. |
| V2-FR-EVENT-041 | Event Bus queue policies must be explicit modes such as fail-fast, bounded wait, or lossy-drop. | Defer | Exclude from the initial rebuild; reassess as a production infrastructure slice after ownership, configuration, and real callers are confirmed. | V1 versions are disconnected and the V2 proposal is substantially more complex than current evidence supports. |
| V2-FR-EVENT-042 | Production Event Bus queue policy must default to fail-fast for critical workflows. | Defer | Exclude from the initial rebuild; reassess as a production infrastructure slice after ownership, configuration, and real callers are confirmed. | V1 versions are disconnected and the V2 proposal is substantially more complex than current evidence supports. |
| V2-FR-EVENT-043 | Queue-full behavior must not silently drop events unless the caller explicitly selected a lossy policy. | Defer | Exclude from the initial rebuild; reassess as a production infrastructure slice after ownership, configuration, and real callers are confirmed. | V1 versions are disconnected and the V2 proposal is substantially more complex than current evidence supports. |
| V2-FR-EVENT-044 | Lossy-drop behavior must be allowed only for explicitly configured low-severity telemetry events. | Defer | Exclude from the initial rebuild; reassess as a production infrastructure slice after ownership, configuration, and real callers are confirmed. | V1 versions are disconnected and the V2 proposal is substantially more complex than current evidence supports. |
| V2-FR-EVENT-045 | Dropped events must be counted in metrics. | Defer | Exclude from the initial rebuild; reassess as a production infrastructure slice after ownership, configuration, and real callers are confirmed. | V1 versions are disconnected and the V2 proposal is substantially more complex than current evidence supports. |
| V2-FR-EVENT-046 | Dropped events must be logged with sanitized metadata. | Defer | Exclude from the initial rebuild; reassess as a production infrastructure slice after ownership, configuration, and real callers are confirmed. | V1 versions are disconnected and the V2 proposal is substantially more complex than current evidence supports. |
| V2-FR-EVENT-047 | Queue-full diagnostics must include event type, source, severity, queue name or topic, queue depth, configured queue limit, request ID, workflow ID, and correlation ID where available. | Defer | Exclude from the initial rebuild; reassess as a production infrastructure slice after ownership, configuration, and real callers are confirmed. | V1 versions are disconnected and the V2 proposal is substantially more complex than current evidence supports. |
| V2-FR-EVENT-048 | Queue-full diagnostics must not include raw event payloads by default. | Defer | Exclude from the initial rebuild; reassess as a production infrastructure slice after ownership, configuration, and real callers are confirmed. | V1 versions are disconnected and the V2 proposal is substantially more complex than current evidence supports. |
| V2-FR-EVENT-049 | In-process Event Bus delivery must enforce `EVENT_HANDLER_TIMEOUT_MS` per handler when timeout enforcement is enabled. | Defer | Exclude from the initial rebuild; reassess as a production infrastructure slice after ownership, configuration, and real callers are confirmed. | V1 versions are disconnected and the V2 proposal is substantially more complex than current evidence supports. |
| V2-FR-EVENT-050 | A subscriber that exceeds the configured handler timeout must be isolated, counted, routed to error handling, and must not block delivery to unrelated subscribers. | Defer | Exclude from the initial rebuild; reassess as a production infrastructure slice after ownership, configuration, and real callers are confirmed. | V1 versions are disconnected and the V2 proposal is substantially more complex than current evidence supports. |
| V2-FR-EVENT-051 | The Event Bus must not open network connections during module import. | Keep | Carry this safety boundary into any future implementation. | The boundary is valid independent of scheduling. |
| V2-FR-EVENT-052 | Production external broker adapters must be dependency-aware and lazy-loaded. | Defer | Exclude from the initial rebuild; reassess as a production infrastructure slice after ownership, configuration, and real callers are confirmed. | V1 versions are disconnected and the V2 proposal is substantially more complex than current evidence supports. |
| V2-FR-EVENT-053 | Production external broker adapters must fail clearly when required optional dependencies are missing. | Defer | Exclude from the initial rebuild; reassess as a production infrastructure slice after ownership, configuration, and real callers are confirmed. | V1 versions are disconnected and the V2 proposal is substantially more complex than current evidence supports. |
| V2-FR-EVENT-054 | Production external broker adapters must implement circuit breakers. | Defer | Exclude from the initial rebuild; reassess as a production infrastructure slice after ownership, configuration, and real callers are confirmed. | V1 versions are disconnected and the V2 proposal is substantially more complex than current evidence supports. |
| V2-FR-EVENT-055 | Event Bus support must not approve trades, place orders, mutate broker state, or make risk decisions. | Keep | Carry this safety boundary into any future implementation. | The boundary is valid independent of scheduling. |


#### Error Routing and Alerts


| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
| --- | --- | --- | --- | --- |
| V2-FR-ALERT-001 | The system must provide a standard error event model. | Defer | Exclude from the initial rebuild; reassess as a production infrastructure slice after ownership, configuration, and real callers are confirmed. | V1 versions are disconnected and the V2 proposal is substantially more complex than current evidence supports. |
| V2-FR-ALERT-002 | The error event model must include error code, severity, source module, source function or tool, request ID, workflow ID, correlation ID, sanitized message, sanitized details, and timestamp. | Defer | Exclude from the initial rebuild; reassess as a production infrastructure slice after ownership, configuration, and real callers are confirmed. | V1 versions are disconnected and the V2 proposal is substantially more complex than current evidence supports. |
| V2-FR-ALERT-003 | Expected validation failures must be routable as warning or error events depending on severity. | Defer | Exclude from the initial rebuild; reassess as a production infrastructure slice after ownership, configuration, and real callers are confirmed. | V1 versions are disconnected and the V2 proposal is substantially more complex than current evidence supports. |
| V2-FR-ALERT-004 | Unexpected execution failures must be routable as error or critical events. | Defer | Exclude from the initial rebuild; reassess as a production infrastructure slice after ownership, configuration, and real callers are confirmed. | V1 versions are disconnected and the V2 proposal is substantially more complex than current evidence supports. |
| V2-FR-ALERT-005 | Critical system failures must be routable to notifications. | Defer | Exclude from the initial rebuild; reassess as a production infrastructure slice after ownership, configuration, and real callers are confirmed. | V1 versions are disconnected and the V2 proposal is substantially more complex than current evidence supports. |
| V2-FR-ALERT-006 | Error routing must deduplicate repeated identical errors within a configurable time window. | Defer | Exclude from the initial rebuild; reassess as a production infrastructure slice after ownership, configuration, and real callers are confirmed. | V1 versions are disconnected and the V2 proposal is substantially more complex than current evidence supports. |
| V2-FR-ALERT-007 | Error routing must prevent recursive alert storms. | Defer | Exclude from the initial rebuild; reassess as a production infrastructure slice after ownership, configuration, and real callers are confirmed. | V1 versions are disconnected and the V2 proposal is substantially more complex than current evidence supports. |
| V2-FR-ALERT-008 | Error routing must redact secrets before publishing events, logging, metrics, or notifications. | Defer | Exclude from the initial rebuild; reassess as a production infrastructure slice after ownership, configuration, and real callers are confirmed. | V1 versions are disconnected and the V2 proposal is substantially more complex than current evidence supports. |
| V2-FR-ALERT-009 | Error routing must preserve enough diagnostic context for troubleshooting without exposing sensitive payloads. | Defer | Exclude from the initial rebuild; reassess as a production infrastructure slice after ownership, configuration, and real callers are confirmed. | V1 versions are disconnected and the V2 proposal is substantially more complex than current evidence supports. |
| V2-FR-ALERT-010 | Error routing must support severity-based routing rules. | Defer | Exclude from the initial rebuild; reassess as a production infrastructure slice after ownership, configuration, and real callers are confirmed. | V1 versions are disconnected and the V2 proposal is substantially more complex than current evidence supports. |
| V2-FR-ALERT-011 | Error routing must support environment-specific routing rules. | Defer | Exclude from the initial rebuild; reassess as a production infrastructure slice after ownership, configuration, and real callers are confirmed. | V1 versions are disconnected and the V2 proposal is substantially more complex than current evidence supports. |
| V2-FR-ALERT-012 | Error routing must support suppression rules for known noisy non-critical errors. | Defer | Exclude from the initial rebuild; reassess as a production infrastructure slice after ownership, configuration, and real callers are confirmed. | V1 versions are disconnected and the V2 proposal is substantially more complex than current evidence supports. |
| V2-FR-ALERT-013 | Error routing must expose metrics for routed, suppressed, retried, failed, and dead-lettered error events. | Defer | Exclude from the initial rebuild; reassess as a production infrastructure slice after ownership, configuration, and real callers are confirmed. | V1 versions are disconnected and the V2 proposal is substantially more complex than current evidence supports. |
| V2-FR-ALERT-014 | Error routing failures must not recursively trigger infinite error routing. | Defer | Exclude from the initial rebuild; reassess as a production infrastructure slice after ownership, configuration, and real callers are confirmed. | V1 versions are disconnected and the V2 proposal is substantially more complex than current evidence supports. |
| V2-FR-ALERT-015 | Error routing must preserve the original error code and attach routing failure code separately when both exist. | Defer | Exclude from the initial rebuild; reassess as a production infrastructure slice after ownership, configuration, and real callers are confirmed. | V1 versions are disconnected and the V2 proposal is substantially more complex than current evidence supports. |


#### Notifications


| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
| --- | --- | --- | --- | --- |
| V2-FR-NOTIFY-001 | The system must provide notification routing primitives for email, Telegram, and desktop channels. | Defer | Exclude from the initial rebuild; reassess as a production infrastructure slice after ownership, configuration, and real callers are confirmed. | V1 versions are disconnected and the V2 proposal is substantially more complex than current evidence supports. |
| V2-FR-NOTIFY-002 | Notification routing must support severity-based routing. | Defer | Exclude from the initial rebuild; reassess as a production infrastructure slice after ownership, configuration, and real callers are confirmed. | V1 versions are disconnected and the V2 proposal is substantially more complex than current evidence supports. |
| V2-FR-NOTIFY-003 | Notification routing must support environment-specific routing. | Defer | Exclude from the initial rebuild; reassess as a production infrastructure slice after ownership, configuration, and real callers are confirmed. | V1 versions are disconnected and the V2 proposal is substantially more complex than current evidence supports. |
| V2-FR-NOTIFY-004 | Notification routing must support channel enablement and disablement through runtime settings. | Defer | Exclude from the initial rebuild; reassess as a production infrastructure slice after ownership, configuration, and real callers are confirmed. | V1 versions are disconnected and the V2 proposal is substantially more complex than current evidence supports. |
| V2-FR-NOTIFY-005 | Notification routing must support per-channel recipient configuration. | Defer | Exclude from the initial rebuild; reassess as a production infrastructure slice after ownership, configuration, and real callers are confirmed. | V1 versions are disconnected and the V2 proposal is substantially more complex than current evidence supports. |
| V2-FR-NOTIFY-006 | Notification routing must support safe templates for alert title, summary, severity, source, timestamp, request ID, workflow ID, and correlation ID. | Defer | Exclude from the initial rebuild; reassess as a production infrastructure slice after ownership, configuration, and real callers are confirmed. | V1 versions are disconnected and the V2 proposal is substantially more complex than current evidence supports. |
| V2-FR-NOTIFY-007 | Notification templates must render from sanitized data transfer objects rather than raw event payloads. | Defer | Exclude from the initial rebuild; reassess as a production infrastructure slice after ownership, configuration, and real callers are confirmed. | V1 versions are disconnected and the V2 proposal is substantially more complex than current evidence supports. |
| V2-FR-NOTIFY-008 | Notification templates must support markdown and plain-text fallbacks to ensure readability across email, Telegram, and desktop clients. | Defer | Exclude from the initial rebuild; reassess as a production infrastructure slice after ownership, configuration, and real callers are confirmed. | V1 versions are disconnected and the V2 proposal is substantially more complex than current evidence supports. |
| V2-FR-NOTIFY-009 | Notification rendering must degrade to plain text when a channel does not support markdown. | Defer | Exclude from the initial rebuild; reassess as a production infrastructure slice after ownership, configuration, and real callers are confirmed. | V1 versions are disconnected and the V2 proposal is substantially more complex than current evidence supports. |
| V2-FR-NOTIFY-010 | Notification template rendering failures must return deterministic notification failure diagnostics without exposing raw payloads. | Defer | Exclude from the initial rebuild; reassess as a production infrastructure slice after ownership, configuration, and real callers are confirmed. | V1 versions are disconnected and the V2 proposal is substantially more complex than current evidence supports. |
| V2-FR-NOTIFY-011 | Notification routing must not include raw sensitive payloads. | Keep | Carry this safety boundary into any future implementation. | The boundary is valid independent of scheduling. |
| V2-FR-NOTIFY-012 | Notification routing must redact secrets before message construction. | Defer | Exclude from the initial rebuild; reassess as a production infrastructure slice after ownership, configuration, and real callers are confirmed. | V1 versions are disconnected and the V2 proposal is substantially more complex than current evidence supports. |
| V2-FR-NOTIFY-013 | Notification markdown rendering must escape or sanitize unsafe user-controlled content where applicable. | Defer | Exclude from the initial rebuild; reassess as a production infrastructure slice after ownership, configuration, and real callers are confirmed. | V1 versions are disconnected and the V2 proposal is substantially more complex than current evidence supports. |
| V2-FR-NOTIFY-014 | Notification sanitization must strip HTML tags, escape Markdown control characters where the channel requires it, normalize control characters, truncate fields using `MAX_STRING_LENGTH`, and reject or redact unsafe links where applicable. | Defer | Exclude from the initial rebuild; reassess as a production infrastructure slice after ownership, configuration, and real callers are confirmed. | V1 versions are disconnected and the V2 proposal is substantially more complex than current evidence supports. |
| V2-FR-NOTIFY-015 | Notification templates must never render raw event payloads, raw exception strings, credentials, tokens, recipient lists, or approval packet contents. | Defer | Exclude from the initial rebuild; reassess as a production infrastructure slice after ownership, configuration, and real callers are confirmed. | V1 versions are disconnected and the V2 proposal is substantially more complex than current evidence supports. |
| V2-FR-NOTIFY-016 | Notification routing must support rate limiting or throttling to avoid alert storms. | Defer | Exclude from the initial rebuild; reassess as a production infrastructure slice after ownership, configuration, and real callers are confirmed. | V1 versions are disconnected and the V2 proposal is substantially more complex than current evidence supports. |
| V2-FR-NOTIFY-017 | Notification routing must support deduplication of repeated alerts. | Defer | Exclude from the initial rebuild; reassess as a production infrastructure slice after ownership, configuration, and real callers are confirmed. | V1 versions are disconnected and the V2 proposal is substantially more complex than current evidence supports. |
| V2-FR-NOTIFY-018 | Notification routing must support test mode with fake adapters. | Defer | Exclude from the initial rebuild; reassess as a production infrastructure slice after ownership, configuration, and real callers are confirmed. | V1 versions are disconnected and the V2 proposal is substantially more complex than current evidence supports. |
| V2-FR-NOTIFY-019 | Notification routing must produce delivery status results. | Defer | Exclude from the initial rebuild; reassess as a production infrastructure slice after ownership, configuration, and real callers are confirmed. | V1 versions are disconnected and the V2 proposal is substantially more complex than current evidence supports. |
| V2-FR-NOTIFY-020 | Notification routing must publish notification success and failure events to the Event Bus. | Defer | Exclude from the initial rebuild; reassess as a production infrastructure slice after ownership, configuration, and real callers are confirmed. | V1 versions are disconnected and the V2 proposal is substantially more complex than current evidence supports. |
| V2-FR-NOTIFY-021 | Notification routing must expose metrics for sent, failed, suppressed, throttled, and deduplicated notifications. | Defer | Exclude from the initial rebuild; reassess as a production infrastructure slice after ownership, configuration, and real callers are confirmed. | V1 versions are disconnected and the V2 proposal is substantially more complex than current evidence supports. |
| V2-FR-NOTIFY-022 | Email notifications must support configurable SMTP or provider adapter settings without logging credentials. | Defer | Exclude from the initial rebuild; reassess as a production infrastructure slice after ownership, configuration, and real callers are confirmed. | V1 versions are disconnected and the V2 proposal is substantially more complex than current evidence supports. |
| V2-FR-NOTIFY-023 | Telegram notifications must support bot-token and chat-recipient configuration without logging credentials. | Defer | Exclude from the initial rebuild; reassess as a production infrastructure slice after ownership, configuration, and real callers are confirmed. | V1 versions are disconnected and the V2 proposal is substantially more complex than current evidence supports. |
| V2-FR-NOTIFY-024 | Desktop notifications must be disabled by default in production unless explicitly enabled. | Defer | Exclude from the initial rebuild; reassess as a production infrastructure slice after ownership, configuration, and real callers are confirmed. | V1 versions are disconnected and the V2 proposal is substantially more complex than current evidence supports. |
| V2-FR-NOTIFY-025 | Notification adapters must be lazy-loaded and must not initialize network clients at import time. | Defer | Exclude from the initial rebuild; reassess as a production infrastructure slice after ownership, configuration, and real callers are confirmed. | V1 versions are disconnected and the V2 proposal is substantially more complex than current evidence supports. |
| V2-FR-NOTIFY-026 | External notification adapters must implement circuit breakers. | Defer | Exclude from the initial rebuild; reassess as a production infrastructure slice after ownership, configuration, and real callers are confirmed. | V1 versions are disconnected and the V2 proposal is substantially more complex than current evidence supports. |
| V2-FR-NOTIFY-027 | Notification delivery failures must not fail the original business operation unless the caller explicitly requires fail-closed alerting. | Defer | Exclude from the initial rebuild; reassess as a production infrastructure slice after ownership, configuration, and real callers are confirmed. | V1 versions are disconnected and the V2 proposal is substantially more complex than current evidence supports. |


#### Observability, Metrics, and Health


| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
| --- | --- | --- | --- | --- |
| V2-FR-OBS-001 | The system must provide observability helpers for logs, metrics, health checks, and trace correlation. | Defer | Exclude from the initial rebuild; reassess as a production infrastructure slice after ownership, configuration, and real callers are confirmed. | V1 versions are disconnected and the V2 proposal is substantially more complex than current evidence supports. |
| V2-FR-OBS-002 | The system must expose Prometheus-compatible metrics for system health. | Defer | Exclude from the initial rebuild; reassess as a production infrastructure slice after ownership, configuration, and real callers are confirmed. | V1 versions are disconnected and the V2 proposal is substantially more complex than current evidence supports. |
| V2-FR-OBS-003 | The system must support Grafana dashboards for operational visibility. | Defer | Exclude from the initial rebuild; reassess as a production infrastructure slice after ownership, configuration, and real callers are confirmed. | V1 versions are disconnected and the V2 proposal is substantially more complex than current evidence supports. |
| V2-FR-OBS-004 | Metrics must cover official AI tool call counts. | Defer | Exclude from the initial rebuild; reassess as a production infrastructure slice after ownership, configuration, and real callers are confirmed. | V1 versions are disconnected and the V2 proposal is substantially more complex than current evidence supports. |
| V2-FR-OBS-005 | Metrics must cover official AI tool success and error counts. | Defer | Exclude from the initial rebuild; reassess as a production infrastructure slice after ownership, configuration, and real callers are confirmed. | V1 versions are disconnected and the V2 proposal is substantially more complex than current evidence supports. |
| V2-FR-OBS-006 | Metrics must cover tool execution latency. | Defer | Exclude from the initial rebuild; reassess as a production infrastructure slice after ownership, configuration, and real callers are confirmed. | V1 versions are disconnected and the V2 proposal is substantially more complex than current evidence supports. |
| V2-FR-OBS-007 | Metrics must cover validation failure counts by error code and source. | Defer | Exclude from the initial rebuild; reassess as a production infrastructure slice after ownership, configuration, and real callers are confirmed. | V1 versions are disconnected and the V2 proposal is substantially more complex than current evidence supports. |
| V2-FR-OBS-008 | Metrics must cover Event Bus events published, delivered, failed, retried, dead-lettered, dropped, and backpressured. | Defer | Exclude from the initial rebuild; reassess as a production infrastructure slice after ownership, configuration, and real callers are confirmed. | V1 versions are disconnected and the V2 proposal is substantially more complex than current evidence supports. |
| V2-FR-OBS-009 | Metrics must cover Event Bus queue depth or backlog where applicable. | Defer | Exclude from the initial rebuild; reassess as a production infrastructure slice after ownership, configuration, and real callers are confirmed. | V1 versions are disconnected and the V2 proposal is substantially more complex than current evidence supports. |
| V2-FR-OBS-010 | Metrics must cover Event Bus idempotency cache size, eviction count, duplicate count, and conflict count. | Defer | Exclude from the initial rebuild; reassess as a production infrastructure slice after ownership, configuration, and real callers are confirmed. | V1 versions are disconnected and the V2 proposal is substantially more complex than current evidence supports. |
| V2-FR-OBS-011 | Metrics must cover notification sent, failed, suppressed, throttled, and deduplicated counts. | Defer | Exclude from the initial rebuild; reassess as a production infrastructure slice after ownership, configuration, and real callers are confirmed. | V1 versions are disconnected and the V2 proposal is substantially more complex than current evidence supports. |
| V2-FR-OBS-012 | Metrics must cover notification delivery latency. | Defer | Exclude from the initial rebuild; reassess as a production infrastructure slice after ownership, configuration, and real callers are confirmed. | V1 versions are disconnected and the V2 proposal is substantially more complex than current evidence supports. |
| V2-FR-OBS-013 | Metrics must cover logging error counts where detectable. | Defer | Exclude from the initial rebuild; reassess as a production infrastructure slice after ownership, configuration, and real callers are confirmed. | V1 versions are disconnected and the V2 proposal is substantially more complex than current evidence supports. |
| V2-FR-OBS-014 | Metrics must cover settings load failures. | Defer | Exclude from the initial rebuild; reassess as a production infrastructure slice after ownership, configuration, and real callers are confirmed. | V1 versions are disconnected and the V2 proposal is substantially more complex than current evidence supports. |
| V2-FR-OBS-015 | Metrics must cover security redaction failures. | Defer | Exclude from the initial rebuild; reassess as a production infrastructure slice after ownership, configuration, and real callers are confirmed. | V1 versions are disconnected and the V2 proposal is substantially more complex than current evidence supports. |
| V2-FR-OBS-016 | Metrics must cover encryption and decryption failures without exposing plaintext or key material. | Defer | Exclude from the initial rebuild; reassess as a production infrastructure slice after ownership, configuration, and real callers are confirmed. | V1 versions are disconnected and the V2 proposal is substantially more complex than current evidence supports. |
| V2-FR-OBS-017 | Metrics must cover auth validation and authorization failures. | Defer | Exclude from the initial rebuild; reassess as a production infrastructure slice after ownership, configuration, and real callers are confirmed. | V1 versions are disconnected and the V2 proposal is substantially more complex than current evidence supports. |
| V2-FR-OBS-018 | Metrics must cover circuit-breaker state transitions and current state. | Defer | Exclude from the initial rebuild; reassess as a production infrastructure slice after ownership, configuration, and real callers are confirmed. | V1 versions are disconnected and the V2 proposal is substantially more complex than current evidence supports. |
| V2-FR-OBS-019 | Metrics must cover clock-drift status where available. | Defer | Exclude from the initial rebuild; reassess as a production infrastructure slice after ownership, configuration, and real callers are confirmed. | V1 versions are disconnected and the V2 proposal is substantially more complex than current evidence supports. |
| V2-FR-OBS-020 | Metrics must include system-health metrics, not only business alerts. | Defer | Exclude from the initial rebuild; reassess as a production infrastructure slice after ownership, configuration, and real callers are confirmed. | V1 versions are disconnected and the V2 proposal is substantially more complex than current evidence supports. |
| V2-FR-OBS-021 | Prometheus-compatible metric names must follow `<component>_<metric>_<unit_or_suffix>`. | Defer | Exclude from the initial rebuild; reassess as a production infrastructure slice after ownership, configuration, and real callers are confirmed. | V1 versions are disconnected and the V2 proposal is substantially more complex than current evidence supports. |
| V2-FR-OBS-022 | Counter metric names must end with `_total`. | Defer | Exclude from the initial rebuild; reassess as a production infrastructure slice after ownership, configuration, and real callers are confirmed. | V1 versions are disconnected and the V2 proposal is substantially more complex than current evidence supports. |
| V2-FR-OBS-023 | Duration metric names must include `_seconds`. | Defer | Exclude from the initial rebuild; reassess as a production infrastructure slice after ownership, configuration, and real callers are confirmed. | V1 versions are disconnected and the V2 proposal is substantially more complex than current evidence supports. |
| V2-FR-OBS-024 | Gauge metric names must describe the current state without `_total`. | Defer | Exclude from the initial rebuild; reassess as a production infrastructure slice after ownership, configuration, and real callers are confirmed. | V1 versions are disconnected and the V2 proposal is substantially more complex than current evidence supports. |
| V2-FR-OBS-025 | Prometheus-compatible alerts must cover circuit-open state, queue saturation, dead-letter growth, notification failure rate, and clock drift where alerting is implemented. | Defer | Exclude from the initial rebuild; reassess as a production infrastructure slice after ownership, configuration, and real callers are confirmed. | V1 versions are disconnected and the V2 proposal is substantially more complex than current evidence supports. |
| V2-FR-OBS-026 | Grafana dashboards must include panels for idempotency cache size, backpressure count, retry count, circuit-breaker state, and clock drift where dashboards are implemented. | Defer | Exclude from the initial rebuild; reassess as a production infrastructure slice after ownership, configuration, and real callers are confirmed. | V1 versions are disconnected and the V2 proposal is substantially more complex than current evidence supports. |
| V2-FR-OBS-027 | Metrics labels must be bounded and must not include high-cardinality raw IDs unless explicitly approved. | Defer | Exclude from the initial rebuild; reassess as a production infrastructure slice after ownership, configuration, and real callers are confirmed. | V1 versions are disconnected and the V2 proposal is substantially more complex than current evidence supports. |
| V2-FR-OBS-028 | Metric labels must allow no more than `METRIC_LABEL_MAX_DISTINCT_VALUES` distinct values per label in the configured process window unless the label uses a reviewed static allowlist. | Defer | Exclude from the initial rebuild; reassess as a production infrastructure slice after ownership, configuration, and real callers are confirmed. | V1 versions are disconnected and the V2 proposal is substantially more complex than current evidence supports. |
| V2-FR-OBS-029 | Metric labels must be selected from approved low-cardinality dimensions such as component, status, severity, error_code, channel, and health_state. | Defer | Exclude from the initial rebuild; reassess as a production infrastructure slice after ownership, configuration, and real callers are confirmed. | V1 versions are disconnected and the V2 proposal is substantially more complex than current evidence supports. |
| V2-FR-OBS-030 | Request IDs, workflow IDs, correlation IDs, event IDs, idempotency keys, user strings, notification recipients, symbols, raw paths, exception strings, and payload-derived values must not be metric labels. | Defer | Exclude from the initial rebuild; reassess as a production infrastructure slice after ownership, configuration, and real callers are confirmed. | V1 versions are disconnected and the V2 proposal is substantially more complex than current evidence supports. |
| V2-FR-OBS-031 | Metrics labels must not include secrets, raw payloads, tokens, API keys, personal data, notification recipients, or approval packet contents. | Defer | Exclude from the initial rebuild; reassess as a production infrastructure slice after ownership, configuration, and real callers are confirmed. | V1 versions are disconnected and the V2 proposal is substantially more complex than current evidence supports. |
| V2-FR-OBS-032 | Observability helpers must support no-op operation when Prometheus dependencies are not installed. | Defer | Exclude from the initial rebuild; reassess as a production infrastructure slice after ownership, configuration, and real callers are confirmed. | V1 versions are disconnected and the V2 proposal is substantially more complex than current evidence supports. |
| V2-FR-OBS-033 | Missing Prometheus dependencies must fail only when Prometheus-specific export features are used. | Defer | Exclude from the initial rebuild; reassess as a production infrastructure slice after ownership, configuration, and real callers are confirmed. | V1 versions are disconnected and the V2 proposal is substantially more complex than current evidence supports. |
| V2-FR-OBS-034 | Grafana dashboard documentation must include panels for system health, tool health, Event Bus health, notification health, error routing, auth failures, and data-quality validation health. | Defer | Exclude from the initial rebuild; reassess as a production infrastructure slice after ownership, configuration, and real callers are confirmed. | V1 versions are disconnected and the V2 proposal is substantially more complex than current evidence supports. |
| V2-FR-OBS-035 | Health snapshots must include component status, last error timestamp, last successful event timestamp, degraded status, and critical status where applicable. | Defer | Exclude from the initial rebuild; reassess as a production infrastructure slice after ownership, configuration, and real callers are confirmed. | V1 versions are disconnected and the V2 proposal is substantially more complex than current evidence supports. |
| V2-FR-OBS-036 | Production health checks must include wall-clock drift monitoring when the runtime environment provides a reliable offset source. | Defer | Exclude from the initial rebuild; reassess as a production infrastructure slice after ownership, configuration, and real callers are confirmed. | V1 versions are disconnected and the V2 proposal is substantially more complex than current evidence supports. |
| V2-FR-OBS-037 | Clock drift monitoring must detect significant NTP or system-clock offset beyond configured thresholds. | Defer | Exclude from the initial rebuild; reassess as a production infrastructure slice after ownership, configuration, and real callers are confirmed. | V1 versions are disconnected and the V2 proposal is substantially more complex than current evidence supports. |
| V2-FR-OBS-038 | Clock drift thresholds must be configurable by environment. | Defer | Exclude from the initial rebuild; reassess as a production infrastructure slice after ownership, configuration, and real callers are confirmed. | V1 versions are disconnected and the V2 proposal is substantially more complex than current evidence supports. |
| V2-FR-OBS-039 | Clock drift warnings must be emitted as observability events. | Defer | Exclude from the initial rebuild; reassess as a production infrastructure slice after ownership, configuration, and real callers are confirmed. | V1 versions are disconnected and the V2 proposal is substantially more complex than current evidence supports. |
| V2-FR-OBS-040 | Critical clock drift must produce degraded or critical health status depending on threshold. | Defer | Exclude from the initial rebuild; reassess as a production infrastructure slice after ownership, configuration, and real callers are confirmed. | V1 versions are disconnected and the V2 proposal is substantially more complex than current evidence supports. |
| V2-FR-OBS-041 | Clock drift diagnostics must include measured offset, threshold, timestamp, source, and component status where available. | Defer | Exclude from the initial rebuild; reassess as a production infrastructure slice after ownership, configuration, and real callers are confirmed. | V1 versions are disconnected and the V2 proposal is substantially more complex than current evidence supports. |
| V2-FR-OBS-042 | Clock drift monitoring may be no-op when the runtime environment cannot provide an offset source. | Defer | Exclude from the initial rebuild; reassess as a production infrastructure slice after ownership, configuration, and real callers are confirmed. | V1 versions are disconnected and the V2 proposal is substantially more complex than current evidence supports. |
| V2-FR-OBS-043 | Clock drift no-op behavior must be explicit and observable as unsupported or not configured. | Defer | Exclude from the initial rebuild; reassess as a production infrastructure slice after ownership, configuration, and real callers are confirmed. | V1 versions are disconnected and the V2 proposal is substantially more complex than current evidence supports. |


#### Circuit Breakers


| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
| --- | --- | --- | --- | --- |
| V2-FR-CB-001 | External notification adapters must implement a circuit-breaker pattern. | Defer | Exclude from the initial rebuild; reassess as a production infrastructure slice after ownership, configuration, and real callers are confirmed. | V1 versions are disconnected and the V2 proposal is substantially more complex than current evidence supports. |
| V2-FR-CB-002 | External pub/sub adapters must implement a circuit-breaker pattern. | Defer | Exclude from the initial rebuild; reassess as a production infrastructure slice after ownership, configuration, and real callers are confirmed. | V1 versions are disconnected and the V2 proposal is substantially more complex than current evidence supports. |
| V2-FR-CB-003 | Circuit breakers must open after a configurable threshold of consecutive failures, timeouts, or provider errors. | Defer | Exclude from the initial rebuild; reassess as a production infrastructure slice after ownership, configuration, and real callers are confirmed. | V1 versions are disconnected and the V2 proposal is substantially more complex than current evidence supports. |
| V2-FR-CB-004 | Open circuits must fail fast without repeatedly consuming threads, sockets, or connection-pool capacity. | Defer | Exclude from the initial rebuild; reassess as a production infrastructure slice after ownership, configuration, and real callers are confirmed. | V1 versions are disconnected and the V2 proposal is substantially more complex than current evidence supports. |
| V2-FR-CB-005 | Circuit breakers must support half-open recovery attempts after a configurable cooldown interval. | Defer | Exclude from the initial rebuild; reassess as a production infrastructure slice after ownership, configuration, and real callers are confirmed. | V1 versions are disconnected and the V2 proposal is substantially more complex than current evidence supports. |
| V2-FR-CB-006 | Circuit breakers must close after successful recovery attempts. | Defer | Exclude from the initial rebuild; reassess as a production infrastructure slice after ownership, configuration, and real callers are confirmed. | V1 versions are disconnected and the V2 proposal is substantially more complex than current evidence supports. |
| V2-FR-CB-007 | Circuit-breaker state transitions must be logged with sanitized metadata. | Defer | Exclude from the initial rebuild; reassess as a production infrastructure slice after ownership, configuration, and real callers are confirmed. | V1 versions are disconnected and the V2 proposal is substantially more complex than current evidence supports. |
| V2-FR-CB-008 | Circuit-breaker state transitions must be exposed through Prometheus-compatible metrics. | Defer | Exclude from the initial rebuild; reassess as a production infrastructure slice after ownership, configuration, and real callers are confirmed. | V1 versions are disconnected and the V2 proposal is substantially more complex than current evidence supports. |
| V2-FR-CB-009 | Circuit-breaker state must be included in component health snapshots. | Defer | Exclude from the initial rebuild; reassess as a production infrastructure slice after ownership, configuration, and real callers are confirmed. | V1 versions are disconnected and the V2 proposal is substantially more complex than current evidence supports. |
| V2-FR-CB-010 | Circuit-breaker failures must not expose credentials, tokens, message bodies, or sensitive payloads. | Keep | Carry this safety boundary into any future implementation. | The boundary is valid independent of scheduling. |


#### Code Quality


| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
| --- | --- | --- | --- | --- |
| V2-NFR-CODE-001 | Every Python file must have a file-level docstring. | Keep | Adopt as a baseline code-quality rule for approved capabilities. | This is proportionate and implementation-neutral. |
| V2-NFR-CODE-002 | Every public function and class must have a useful docstring. | Keep | Adopt as a baseline code-quality rule for approved capabilities. | This is proportionate and implementation-neutral. |
| V2-NFR-CODE-003 | All public functions and methods must be typed. | Keep | Adopt as a baseline code-quality rule for approved capabilities. | This is proportionate and implementation-neutral. |
| V2-NFR-CODE-004 | Inputs must be validated where appropriate. | Keep | Adopt as a baseline code-quality rule for approved capabilities. | This is proportionate and implementation-neutral. |
| V2-NFR-CODE-005 | Output shapes must be explicit where applicable. | Keep | Adopt as a baseline code-quality rule for approved capabilities. | This is proportionate and implementation-neutral. |
| V2-NFR-CODE-006 | Error behavior must be deterministic. | Keep | Adopt as a baseline code-quality rule for approved capabilities. | This is proportionate and implementation-neutral. |
| V2-NFR-CODE-007 | Important events and recoverable failures must use structured logging. | Keep | Adopt as a baseline code-quality rule for approved capabilities. | This is proportionate and implementation-neutral. |
| V2-NFR-CODE-008 | Production logic must not use `print()`. | Keep | Adopt as a baseline code-quality rule for approved capabilities. | This is proportionate and implementation-neutral. |
| V2-NFR-CODE-009 | Official tools must not return unstructured `None`. | Keep | Adopt as a baseline code-quality rule for approved capabilities. | This is proportionate and implementation-neutral. |
| V2-NFR-CODE-010 | Production code must not leak secrets in logs, errors, events, notifications, metrics, or health snapshots. | Keep | Adopt as a baseline code-quality rule for approved capabilities. | This is proportionate and implementation-neutral. |
| V2-NFR-CODE-011 | The implementation must avoid avoidable circular imports. | Keep | Adopt as a baseline code-quality rule for approved capabilities. | This is proportionate and implementation-neutral. |
| V2-NFR-CODE-012 | The implementation must be compatible with Black, isort, Flake8, mypy, pytest, and coverage. | Open Decision | Use the repository-approved quality toolchain and coverage gate once the system-wide CI standard is confirmed. | The V1 audit did not establish the authoritative repository-wide toolchain. |


#### Import-Time Performance and Side Effects


| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
| --- | --- | --- | --- | --- |
| V2-NFR-IMPORT-001 | Importing `app.services.utils` must be lightweight. | Keep | Adopt as a mandatory import-safety rule. | It directly corrects V1 logger/file and heavy-import side effects. |
| V2-NFR-IMPORT-002 | `app/services/utils/__init__.py` must not eagerly import pandas, cryptography, dotenv, broker SDKs, network clients, notification clients, Prometheus exporters, or other heavy optional dependencies unless absolutely necessary. | Keep | Adopt as a mandatory import-safety rule. | It directly corrects V1 logger/file and heavy-import side effects. |
| V2-NFR-IMPORT-003 | Heavy dependencies must be imported inside the specific submodule or function that needs them. | Keep | Adopt as a mandatory import-safety rule. | It directly corrects V1 logger/file and heavy-import side effects. |
| V2-NFR-IMPORT-004 | Dataframe helpers must use lazy pandas imports or `TYPE_CHECKING` guards. | Keep | Adopt as a mandatory import-safety rule. | It directly corrects V1 logger/file and heavy-import side effects. |
| V2-NFR-IMPORT-005 | Importing `app.services.utils` must be safe in tests, CLI scripts, FastAPI startup, and agent runtime initialization. | Keep | Adopt as a mandatory import-safety rule. | It directly corrects V1 logger/file and heavy-import side effects. |
| V2-NFR-IMPORT-006 | Importing any `app.services.utils` module must not create files or directories. | Keep | Adopt as a mandatory import-safety rule. | It directly corrects V1 logger/file and heavy-import side effects. |
| V2-NFR-IMPORT-007 | Importing any `app.services.utils` module must not read `.env` files. | Keep | Adopt as a mandatory import-safety rule. | It directly corrects V1 logger/file and heavy-import side effects. |
| V2-NFR-IMPORT-008 | Importing any `app.services.utils` module must not configure global logging handlers unexpectedly. | Keep | Adopt as a mandatory import-safety rule. | It directly corrects V1 logger/file and heavy-import side effects. |
| V2-NFR-IMPORT-009 | Importing any `app.services.utils` module must not open network connections. | Keep | Adopt as a mandatory import-safety rule. | It directly corrects V1 logger/file and heavy-import side effects. |
| V2-NFR-IMPORT-010 | Importing any `app.services.utils` module must not initialize broker clients. | Keep | Adopt as a mandatory import-safety rule. | It directly corrects V1 logger/file and heavy-import side effects. |
| V2-NFR-IMPORT-011 | Importing any `app.services.utils` module must not initialize notification clients. | Keep | Adopt as a mandatory import-safety rule. | It directly corrects V1 logger/file and heavy-import side effects. |
| V2-NFR-IMPORT-012 | Importing any `app.services.utils` module must not initialize external pub/sub clients. | Keep | Adopt as a mandatory import-safety rule. | It directly corrects V1 logger/file and heavy-import side effects. |
| V2-NFR-IMPORT-013 | Importing any `app.services.utils` module must not mutate environment variables. | Keep | Adopt as a mandatory import-safety rule. | It directly corrects V1 logger/file and heavy-import side effects. |
| V2-NFR-IMPORT-014 | Importing any `app.services.utils` module must not run validation jobs. | Keep | Adopt as a mandatory import-safety rule. | It directly corrects V1 logger/file and heavy-import side effects. |
| V2-NFR-IMPORT-015 | Importing any `app.services.utils` module must not execute expensive dataframe operations. | Keep | Adopt as a mandatory import-safety rule. | It directly corrects V1 logger/file and heavy-import side effects. |


#### Determinism, Concurrency, and Shared State


| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
| --- | --- | --- | --- | --- |
| V2-NFR-CONC-001 | Utility functions must be safe for concurrent use unless explicitly documented otherwise. | Modify | Keep deterministic native helpers and document concurrency; remove or relocate unbounded shared caches. | V1 contains mutable module state and mixed concurrency guarantees. |
| V2-NFR-CONC-002 | Mutable module-level state must be avoided. | Modify | Keep deterministic native helpers and document concurrency; remove or relocate unbounded shared caches. | V1 contains mutable module state and mixed concurrency guarantees. |
| V2-NFR-CONC-003 | Immutable constants and logger objects are allowed. | Modify | Keep deterministic native helpers and document concurrency; remove or relocate unbounded shared caches. | V1 contains mutable module state and mixed concurrency guarantees. |
| V2-NFR-CONC-004 | Caller-owned inputs must not be mutated unless documented in the function name and docstring. | Modify | Keep deterministic native helpers and document concurrency; remove or relocate unbounded shared caches. | V1 contains mutable module state and mixed concurrency guarantees. |
| V2-NFR-CONC-005 | Shared caches are allowed only when explicitly specified, bounded, and tested. | Modify | Keep deterministic native helpers and document concurrency; remove or relocate unbounded shared caches. | V1 contains mutable module state and mixed concurrency guarantees. |
| V2-NFR-CONC-006 | Time-dependent helpers must support deterministic testing where practical. | Modify | Keep deterministic native helpers and document concurrency; remove or relocate unbounded shared caches. | V1 contains mutable module state and mixed concurrency guarantees. |
| V2-NFR-CONC-007 | Time handling must be deterministic and timezone-safe across supported runtime environments. | Modify | Keep deterministic native helpers and document concurrency; remove or relocate unbounded shared caches. | V1 contains mutable module state and mixed concurrency guarantees. |
| V2-NFR-CONC-008 | Wall-clock timestamp serialization must be UTC-first and safe for logs, events, notifications, metrics, health snapshots, and audit metadata. | Defer | Apply when the related stateful production capability is implemented. | The associated capability is deferred. |
| V2-NFR-CONC-009 | ID-dependent and randomness-dependent helpers must support deterministic testing where practical. | Modify | Keep deterministic native helpers and document concurrency; remove or relocate unbounded shared caches. | V1 contains mutable module state and mixed concurrency guarantees. |
| V2-NFR-CONC-010 | Canonical JSON output must be deterministic across equivalent payloads. | Modify | Keep deterministic native helpers and document concurrency; remove or relocate unbounded shared caches. | V1 contains mutable module state and mixed concurrency guarantees. |
| V2-NFR-CONC-011 | Logging output must be deterministic enough for unit testing where log fields are asserted. | Modify | Keep deterministic native helpers and document concurrency; remove or relocate unbounded shared caches. | V1 contains mutable module state and mixed concurrency guarantees. |
| V2-NFR-CONC-012 | Auth helpers must avoid hidden global mutable state. | Modify | Keep deterministic native helpers and document concurrency; remove or relocate unbounded shared caches. | V1 contains mutable module state and mixed concurrency guarantees. |
| V2-NFR-CONC-013 | The in-process Event Bus must be thread-safe for synchronous callers. | Defer | Apply when the related stateful production capability is implemented. | The associated capability is deferred. |
| V2-NFR-CONC-014 | Async Event Bus APIs, if implemented, must be async-safe and must not share unsafe mutable state with synchronous APIs. | Defer | Apply when the related stateful production capability is implemented. | The associated capability is deferred. |
| V2-NFR-CONC-015 | Event Bus handler registration, unregistration, publishing, retry, dead-letter handling, and idempotency tracking must state whether each API is thread-safe, async-safe, or both. | Defer | Apply when the related stateful production capability is implemented. | The associated capability is deferred. |
| V2-NFR-CONC-016 | Event Bus handlers must not share mutable event payloads unless payloads are explicitly copied or treated as immutable by contract. | Defer | Apply when the related stateful production capability is implemented. | The associated capability is deferred. |
| V2-NFR-CONC-017 | Event Bus event versioning must support forward compatibility for event consumers. | Defer | Apply when the related stateful production capability is implemented. | The associated capability is deferred. |
| V2-NFR-CONC-018 | Event Bus delivery diagnostics must remain consistent under concurrent publishing. | Defer | Apply when the related stateful production capability is implemented. | The associated capability is deferred. |
| V2-NFR-CONC-019 | Notification routing, deduplication, throttling, rate-limit counters, and circuit-breaker state must be thread-safe for synchronous callers. | Defer | Apply when the related stateful production capability is implemented. | The associated capability is deferred. |
| V2-NFR-CONC-020 | Async notification APIs, if implemented, must be async-safe and must document interaction with synchronous routing state. | Defer | Apply when the related stateful production capability is implemented. | The associated capability is deferred. |
| V2-NFR-CONC-021 | Notification delivery diagnostics must remain consistent under concurrent alert bursts. | Defer | Apply when the related stateful production capability is implemented. | The associated capability is deferred. |
| V2-NFR-CONC-022 | Logging must be thread-safe under concurrent tool execution. | Modify | Keep deterministic native helpers and document concurrency; remove or relocate unbounded shared caches. | V1 contains mutable module state and mixed concurrency guarantees. |
| V2-NFR-CONC-023 | Idempotency cache reads, writes, eviction, and conflict checks must be thread-safe for the in-process Event Bus. | Defer | Apply when the related stateful production capability is implemented. | The associated capability is deferred. |
| V2-NFR-CONC-024 | Concurrency guarantees and limitations must be documented per component using the exact terms `thread-safe`, `async-safe`, `both`, or `not concurrent-safe`. | Modify | Keep deterministic native helpers and document concurrency; remove or relocate unbounded shared caches. | V1 contains mutable module state and mixed concurrency guarantees. |


#### Optional Dependencies


| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
| --- | --- | --- | --- | --- |
| V2-NFR-OPTDEP-001 | Optional dependencies must not break importability. | Keep | Adopt lazy, explicit optional-dependency failure behavior. | This supports import safety. |
| V2-NFR-OPTDEP-002 | Missing optional dependencies must fail only when the relevant feature is used. | Keep | Adopt lazy, explicit optional-dependency failure behavior. | This supports import safety. |
| V2-NFR-OPTDEP-003 | Missing optional dependency failures must be explicit. | Keep | Adopt lazy, explicit optional-dependency failure behavior. | This supports import safety. |
| V2-NFR-OPTDEP-004 | Missing optional dependency failures must use `ConfigurationError`, `CONFIGURATION_ERROR`, or the standard tool error envelope where applicable. | Keep | Adopt lazy, explicit optional-dependency failure behavior. | This supports import safety. |
| V2-NFR-OPTDEP-005 | Optional dependency error messages must identify the missing dependency and required feature. | Keep | Adopt lazy, explicit optional-dependency failure behavior. | This supports import safety. |
| V2-NFR-OPTDEP-006 | Optional dependency behavior must list the dependency name, feature requiring it, failure code, and install extra where applicable. | Keep | Adopt lazy, explicit optional-dependency failure behavior. | This supports import safety. |
| V2-NFR-OPTDEP-007 | Optional Event Bus broker dependencies must be lazy-loaded. | Defer | Apply to the corresponding optional adapter slice. | The adapter capability is deferred. |
| V2-NFR-OPTDEP-008 | Optional notification provider dependencies must be lazy-loaded. | Defer | Apply to the corresponding optional adapter slice. | The adapter capability is deferred. |
| V2-NFR-OPTDEP-009 | Optional Prometheus dependencies must be lazy-loaded. | Defer | Apply to the corresponding optional adapter slice. | The adapter capability is deferred. |


#### Compatibility


| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
| --- | --- | --- | --- | --- |
| V2-NFR-COMPAT-001 | The module must define supported Python versions before Builder handoff. | Open Decision | Record supported Python/OS/dependency versions after the system-wide compatibility baseline is approved. | The source documents do not provide the actual supported matrix. |
| V2-NFR-COMPAT-002 | The module must define supported operating-system assumptions for paths, desktop notifications, file permissions, console colors, and line endings. | Open Decision | Record supported Python/OS/dependency versions after the system-wide compatibility baseline is approved. | The source documents do not provide the actual supported matrix. |
| V2-NFR-COMPAT-003 | The module must document package compatibility assumptions for optional dataframe, cryptography, notification, pub/sub, and Prometheus/exporter features. | Open Decision | Record supported Python/OS/dependency versions after the system-wide compatibility baseline is approved. | The source documents do not provide the actual supported matrix. |
| V2-NFR-COMPAT-004 | Compatibility requirements must distinguish required runtime support from optional adapter support. | Open Decision | Record supported Python/OS/dependency versions after the system-wide compatibility baseline is approved. | The source documents do not provide the actual supported matrix. |


#### Memory, Response Size, and Backpressure


| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
| --- | --- | --- | --- | --- |
| V2-NFR-MEM-001 | Utilities must be safe with large datasets. | Keep | Adopt bounded diagnostics, no whole-dataframe responses, and explicit copy behavior. | These are necessary for safe validation workloads. |
| V2-NFR-MEM-002 | Utilities must avoid unnecessary deep copies. | Keep | Adopt bounded diagnostics, no whole-dataframe responses, and explicit copy behavior. | These are necessary for safe validation workloads. |
| V2-NFR-MEM-003 | Dataframe helpers must document copy, view, and transformed-data behavior. | Keep | Adopt bounded diagnostics, no whole-dataframe responses, and explicit copy behavior. | These are necessary for safe validation workloads. |
| V2-NFR-MEM-004 | Official AI tool responses must not return whole dataframes. | Keep | Adopt bounded diagnostics, no whole-dataframe responses, and explicit copy behavior. | These are necessary for safe validation workloads. |
| V2-NFR-MEM-005 | Agent-facing diagnostics must prefer summaries, counts, and compact samples. | Keep | Adopt bounded diagnostics, no whole-dataframe responses, and explicit copy behavior. | These are necessary for safe validation workloads. |
| V2-NFR-MEM-006 | Returned issue lists and samples must be bounded. | Keep | Adopt bounded diagnostics, no whole-dataframe responses, and explicit copy behavior. | These are necessary for safe validation workloads. |
| V2-NFR-MEM-007 | Event Bus diagnostics must remain bounded to avoid oversized logs and metrics. | Defer | Apply to the deferred Event Bus capability. | The associated stateful capability is deferred. |
| V2-NFR-MEM-008 | Event Bus idempotency storage must be bounded by TTL and maximum cache size. | Defer | Apply to the deferred Event Bus capability. | The associated stateful capability is deferred. |
| V2-NFR-MEM-009 | Event Bus queues must have explicit limits. | Defer | Apply to the deferred Event Bus capability. | The associated stateful capability is deferred. |
| V2-NFR-MEM-010 | Queue-full behavior must fail fast or follow a documented bounded policy. | Defer | Apply to the deferred Event Bus capability. | The associated stateful capability is deferred. |
| V2-NFR-MEM-011 | Lossy-drop behavior may be allowed only when explicitly configured for low-severity telemetry events. | Keep | Adopt bounded diagnostics, no whole-dataframe responses, and explicit copy behavior. | These are necessary for safe validation workloads. |
| V2-NFR-MEM-012 | Backpressure diagnostics must be bounded and redacted. | Defer | Apply to the deferred Event Bus capability. | The associated stateful capability is deferred. |


#### Performance


| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
| --- | --- | --- | --- | --- |
| V2-NFR-PERF-001 | Performance requirements must use measurable thresholds or a named benchmark profile before production acceptance. | Open Decision | Define the benchmark profile and numeric acceptance thresholds before production acceptance. | The V2 document intentionally leaves thresholds unresolved. |
| V2-NFR-PERF-002 | `validate_ohlcv_quality` must validate 1,000 OHLCV rows within the documented fast-path benchmark threshold for the project-standard local test profile. | Open Decision | Define the benchmark profile and numeric acceptance thresholds before production acceptance. | The V2 document intentionally leaves thresholds unresolved. |
| V2-NFR-PERF-003 | `validate_ohlcv_quality` must validate 100,000 OHLCV rows within the documented large-validation benchmark threshold for the project-standard local test profile. | Open Decision | Define the benchmark profile and numeric acceptance thresholds before production acceptance. | The V2 document intentionally leaves thresholds unresolved. |
| V2-NFR-PERF-004 | The benchmark profile must document hardware class, Python version, dependency versions, configured validation options, allowed variance, and whether the run is an acceptance gate or baseline-recording check. | Open Decision | Define the benchmark profile and numeric acceptance thresholds before production acceptance. | The V2 document intentionally leaves thresholds unresolved. |
| V2-NFR-PERF-005 | Subjective performance adjectives must be replaced with measurable targets before production acceptance. | Keep | Adopt as a performance design constraint and verify against the approved benchmark profile. | The requirement is measurable or supports bounded execution. |
| V2-NFR-PERF-006 | Resource-limit settings must define default maximum payload size, maximum validation depth, maximum field count, maximum issue count, maximum sample count, maximum string length, and maximum response size. | Keep | Adopt as a performance design constraint and verify against the approved benchmark profile. | The requirement is measurable or supports bounded execution. |
| V2-NFR-PERF-007 | Large validation behavior must define whether the tool fails closed, truncates diagnostics, samples records, or returns a partial diagnostic result. | Keep | Adopt as a performance design constraint and verify against the approved benchmark profile. | The requirement is measurable or supports bounded execution. |
| V2-NFR-PERF-008 | Large data-quality validations must avoid unnecessary deep copies. | Keep | Adopt as a performance design constraint and verify against the approved benchmark profile. | The requirement is measurable or supports bounded execution. |
| V2-NFR-PERF-009 | Dataframe helpers must avoid repeated full-dataframe scans where possible. | Keep | Adopt as a performance design constraint and verify against the approved benchmark profile. | The requirement is measurable or supports bounded execution. |
| V2-NFR-PERF-010 | Schema validation helpers must meet the documented schema-validation benchmark or baseline profile. | Keep | Adopt as a performance design constraint and verify against the approved benchmark profile. | The requirement is measurable or supports bounded execution. |
| V2-NFR-PERF-011 | Schema validation helpers must not perform blocking I/O. | Keep | Adopt as a performance design constraint and verify against the approved benchmark profile. | The requirement is measurable or supports bounded execution. |
| V2-NFR-PERF-012 | Schema validation helpers must not perform network calls. | Keep | Adopt as a performance design constraint and verify against the approved benchmark profile. | The requirement is measurable or supports bounded execution. |
| V2-NFR-PERF-013 | Schema validation helpers must not introduce unbounded CPU spikes during normal market-data processing. | Keep | Adopt as a performance design constraint and verify against the approved benchmark profile. | The requirement is measurable or supports bounded execution. |
| V2-NFR-PERF-014 | Security helpers must avoid expensive redaction recursion loops. | Keep | Adopt as a performance design constraint and verify against the approved benchmark profile. | The requirement is measurable or supports bounded execution. |
| V2-NFR-PERF-015 | Security helpers must use recursion depth protection for nested structures. | Keep | Adopt as a performance design constraint and verify against the approved benchmark profile. | The requirement is measurable or supports bounded execution. |
| V2-NFR-PERF-016 | Security helpers must avoid logging sensitive payloads during failure. | Keep | Adopt as a performance design constraint and verify against the approved benchmark profile. | The requirement is measurable or supports bounded execution. |
| V2-NFR-PERF-017 | Logging overhead must meet the documented normal tool execution benchmark or baseline profile. | Keep | Adopt as a performance design constraint and verify against the approved benchmark profile. | The requirement is measurable or supports bounded execution. |
| V2-NFR-PERF-018 | Metrics collection overhead must meet the documented observability benchmark or baseline profile. | Defer | Benchmark when the deferred capability exists. | No implementation is approved yet. |
| V2-NFR-PERF-019 | Health checks must be deterministic and must meet the documented health-check benchmark or baseline profile. | Defer | Benchmark when the deferred capability exists. | No implementation is approved yet. |


#### Reliability and Degradation


| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
| --- | --- | --- | --- | --- |
| V2-NFR-REL-001 | Logging must degrade safely if a logging sink fails. | Modify | Keep safe logging degradation with bounded fallback diagnostics and no recursive failure. | V1 swallows failures completely; safe degradation must remain observable. |
| V2-NFR-REL-002 | Logging sink failure behavior must cover disk full, permission denied, path missing, rotation failure, retention deletion failure, and network filesystem dropout where applicable. | Modify | Keep safe logging degradation with bounded fallback diagnostics and no recursive failure. | V1 swallows failures completely; safe degradation must remain observable. |
| V2-NFR-REL-003 | Logging sink failures must not raise unhandled exceptions into official AI tool callers. | Modify | Keep safe logging degradation with bounded fallback diagnostics and no recursive failure. | V1 swallows failures completely; safe degradation must remain observable. |
| V2-NFR-REL-004 | Logging sink failures must increment logging error metrics where metrics are available. | Modify | Keep safe logging degradation with bounded fallback diagnostics and no recursive failure. | V1 swallows failures completely; safe degradation must remain observable. |
| V2-NFR-REL-005 | Logging sink failures must fall back to an available safe sink or no-op logging, without exposing secrets or recursively logging the same failure indefinitely. | Modify | Keep safe logging degradation with bounded fallback diagnostics and no recursive failure. | V1 swallows failures completely; safe degradation must remain observable. |
| V2-NFR-REL-006 | Metrics recording failures must not fail the original operation unless explicitly configured to fail closed. | Defer | Apply in the later production infrastructure slice. | The associated capability is deferred. |
| V2-NFR-REL-007 | Notification delivery failures must be isolated from core utility functions unless explicitly configured otherwise. | Defer | Apply in the later production infrastructure slice. | The associated capability is deferred. |
| V2-NFR-REL-008 | Notification routing must remain safe under repeated error bursts. | Defer | Apply in the later production infrastructure slice. | The associated capability is deferred. |
| V2-NFR-REL-009 | Notification messages must be concise and actionable. | Defer | Apply in the later production infrastructure slice. | The associated capability is deferred. |
| V2-NFR-REL-010 | External Event Bus broker outages must be isolated through circuit breakers and deterministic error codes. | Defer | Apply in the later production infrastructure slice. | The associated capability is deferred. |
| V2-NFR-REL-011 | External notification provider outages must be isolated through circuit breakers and deterministic error codes. | Defer | Apply in the later production infrastructure slice. | The associated capability is deferred. |
| V2-NFR-REL-012 | Component health checks must distinguish healthy, degraded, critical, unsupported, and not-configured states. | Defer | Apply in the later production infrastructure slice. | The associated capability is deferred. |


#### Observability Non-Functional Requirements


| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
| --- | --- | --- | --- | --- |
| V2-NFR-OBS-001 | Metrics labels must be bounded-cardinality. | Defer | Apply to the deferred observability/notification capability. | No production observability workflow is confirmed. |
| V2-NFR-OBS-002 | Metrics must be safe to expose to Prometheus without leaking secrets. | Defer | Apply to the deferred observability/notification capability. | No production observability workflow is confirmed. |
| V2-NFR-OBS-003 | Observability helpers must be import-safe without Prometheus dependencies. | Defer | Apply to the deferred observability/notification capability. | No production observability workflow is confirmed. |
| V2-NFR-OBS-004 | Logging output must be machine-parseable in production and human-readable enough for local development. | Modify | Apply machine-readable production and human-readable local logging now. | Logging is a core capability. |
| V2-NFR-OBS-005 | Notification delivery must be observable through logs, metrics, or sanitized events. | Defer | Apply to the deferred observability/notification capability. | No production observability workflow is confirmed. |
| V2-NFR-OBS-006 | Grafana dashboard definitions must be version-controlled if implemented as files. | Defer | Apply to the deferred observability/notification capability. | No production observability workflow is confirmed. |
| V2-NFR-OBS-007 | Observability must support local/test no-op behavior. | Defer | Apply to the deferred observability/notification capability. | No production observability workflow is confirmed. |
| V2-NFR-OBS-008 | Health checks must distinguish healthy, degraded, and critical states. | Defer | Apply to the deferred observability/notification capability. | No production observability workflow is confirmed. |
| V2-NFR-OBS-009 | System-health observability must not be limited to trading or business alerts. | Defer | Apply to the deferred observability/notification capability. | No production observability workflow is confirmed. |


#### 5.1 Security Requirements


| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
| --- | --- | --- | --- | --- |
| V2-SEC-001 | Sensitive values must be redacted before logging. | Modify | Apply the requirement to the accepted core security boundary with bounded, non-mutating redaction and deterministic failures. | V1 security is valuable but inconsistent. |
| V2-SEC-002 | Sensitive values must be redacted before appearing in error responses. | Modify | Apply the requirement to the accepted core security boundary with bounded, non-mutating redaction and deterministic failures. | V1 security is valuable but inconsistent. |
| V2-SEC-003 | Sensitive values must be redacted before appearing in metadata. | Modify | Apply the requirement to the accepted core security boundary with bounded, non-mutating redaction and deterministic failures. | V1 security is valuable but inconsistent. |
| V2-SEC-004 | Sensitive values must be redacted before appearing in remediation messages. | Modify | Apply the requirement to the accepted core security boundary with bounded, non-mutating redaction and deterministic failures. | V1 security is valuable but inconsistent. |
| V2-SEC-005 | Sensitive values must be redacted before canonical JSON serialization where configured. | Modify | Require explicit redaction before serialization in sensitive workflows; keep canonical serialization itself pure. | This preserves deterministic identity. |
| V2-SEC-006 | Sensitive values must be redacted before appearing in exception text exposed to callers. | Modify | Apply the requirement to the accepted core security boundary with bounded, non-mutating redaction and deterministic failures. | V1 security is valuable but inconsistent. |
| V2-SEC-007 | Sensitive values must be redacted before appearing in Event Bus payload logs. | Defer | Retain this as a mandatory security constraint for the corresponding deferred capability. | The dependent feature is deferred. |
| V2-SEC-008 | Sensitive values must be redacted before appearing in notification templates. | Defer | Retain this as a mandatory security constraint for the corresponding deferred capability. | The dependent feature is deferred. |
| V2-SEC-009 | Sensitive values must be redacted before appearing in Prometheus metrics or Grafana variables. | Defer | Retain this as a mandatory security constraint for the corresponding deferred capability. | The dependent feature is deferred. |
| V2-SEC-010 | Encryption keys must never be logged. | Modify | Apply the requirement to the accepted core security boundary with bounded, non-mutating redaction and deterministic failures. | V1 security is valuable but inconsistent. |
| V2-SEC-011 | Password hashes must never be treated as plaintext. | Modify | Apply the requirement to the accepted core security boundary with bounded, non-mutating redaction and deterministic failures. | V1 security is valuable but inconsistent. |
| V2-SEC-012 | Approval packets must not leak secrets through error messages. | Modify | Apply the requirement to the accepted core security boundary with bounded, non-mutating redaction and deterministic failures. | V1 security is valuable but inconsistent. |
| V2-SEC-013 | Path helpers must defend against unsafe traversal when `base_dir` is supplied. | Modify | Apply the requirement to the accepted core security boundary with bounded, non-mutating redaction and deterministic failures. | V1 security is valuable but inconsistent. |
| V2-SEC-014 | Official AI tools must declare side effects correctly. | Modify | Apply the requirement to the accepted core security boundary with bounded, non-mutating redaction and deterministic failures. | V1 security is valuable but inconsistent. |
| V2-SEC-015 | Side-effecting utilities must not be attached to agents without explicit approval. | Modify | Apply the requirement to the accepted core security boundary with bounded, non-mutating redaction and deterministic failures. | V1 security is valuable but inconsistent. |
| V2-SEC-016 | Validation tools must fail closed when blocked actions are detected. | Modify | Apply the requirement to the accepted core security boundary with bounded, non-mutating redaction and deterministic failures. | V1 security is valuable but inconsistent. |
| V2-SEC-017 | Unknown environment modes must fail validation. | Modify | Apply the requirement to the accepted core security boundary with bounded, non-mutating redaction and deterministic failures. | V1 security is valuable but inconsistent. |
| V2-SEC-018 | Invalid freshness evidence must be surfaced, not ignored. | Modify | Apply the requirement to the accepted core security boundary with bounded, non-mutating redaction and deterministic failures. | V1 security is valuable but inconsistent. |
| V2-SEC-019 | Redaction must handle nested mappings, lists, string payloads, exception messages, metadata, and returned error details. | Modify | Apply the requirement to the accepted core security boundary with bounded, non-mutating redaction and deterministic failures. | V1 security is valuable but inconsistent. |
| V2-SEC-020 | Security regression tests must prove common secret patterns do not leak. | Modify | Apply the requirement to the accepted core security boundary with bounded, non-mutating redaction and deterministic failures. | V1 security is valuable but inconsistent. |
| V2-SEC-021 | Encryption and decryption failures must not expose plaintext or key material. | Modify | Apply the requirement to the accepted core security boundary with bounded, non-mutating redaction and deterministic failures. | V1 security is valuable but inconsistent. |
| V2-SEC-022 | Secret selection must be deterministic. | Modify | Apply the requirement to the accepted core security boundary with bounded, non-mutating redaction and deterministic failures. | V1 security is valuable but inconsistent. |
| V2-SEC-023 | Auth context must be redacted before logging. | Modify | Apply the requirement to the accepted core security boundary with bounded, non-mutating redaction and deterministic failures. | V1 security is valuable but inconsistent. |
| V2-SEC-024 | Authorization headers must never appear in logs, metrics, events, or notifications. | Defer | Retain this as a mandatory security constraint for the corresponding deferred capability. | The dependent feature is deferred. |
| V2-SEC-025 | Notification recipient lists must be treated as sensitive configuration. | Defer | Retain this as a mandatory security constraint for the corresponding deferred capability. | The dependent feature is deferred. |
| V2-SEC-026 | Email credentials must never appear in logs, metrics, events, or notifications. | Defer | Retain this as a mandatory security constraint for the corresponding deferred capability. | The dependent feature is deferred. |
| V2-SEC-027 | Telegram bot tokens must never appear in logs, metrics, events, or notifications. | Defer | Retain this as a mandatory security constraint for the corresponding deferred capability. | The dependent feature is deferred. |
| V2-SEC-028 | Desktop notification content must not include secrets. | Defer | Retain this as a mandatory security constraint for the corresponding deferred capability. | The dependent feature is deferred. |
| V2-SEC-029 | Event payloads must be redacted before publication when they contain sensitive fields. | Modify | Apply the requirement to the accepted core security boundary with bounded, non-mutating redaction and deterministic failures. | V1 security is valuable but inconsistent. |
| V2-SEC-030 | Event metadata must not include secrets. | Modify | Apply the requirement to the accepted core security boundary with bounded, non-mutating redaction and deterministic failures. | V1 security is valuable but inconsistent. |
| V2-SEC-031 | Metrics labels must not include secrets, tokens, raw payloads, full exception strings, or user-provided arbitrary values. | Modify | Apply the requirement to the accepted core security boundary with bounded, non-mutating redaction and deterministic failures. | V1 security is valuable but inconsistent. |
| V2-SEC-032 | Prometheus metrics must avoid high-cardinality sensitive identifiers. | Defer | Retain this as a mandatory security constraint for the corresponding deferred capability. | The dependent feature is deferred. |
| V2-SEC-033 | Grafana dashboard variables must not expose secrets. | Defer | Retain this as a mandatory security constraint for the corresponding deferred capability. | The dependent feature is deferred. |
| V2-SEC-034 | Error routing must sanitize exception text before alerting. | Modify | Apply the requirement to the accepted core security boundary with bounded, non-mutating redaction and deterministic failures. | V1 security is valuable but inconsistent. |
| V2-SEC-035 | Dead-letter event storage, if configured outside utils, must receive redacted payloads by default. | Defer | Retain this as a mandatory security constraint for the corresponding deferred capability. | The dependent feature is deferred. |
| V2-SEC-036 | Agent tool authorization must use explicit allowlists. | Modify | Apply the requirement to the accepted core security boundary with bounded, non-mutating redaction and deterministic failures. | V1 security is valuable but inconsistent. |
| V2-SEC-037 | Side-effecting notification and event adapter actions must require explicit configuration. | Defer | Retain this as a mandatory security constraint for the corresponding deferred capability. | The dependent feature is deferred. |
| V2-SEC-038 | External notification and pub/sub adapters must be lazy-loaded. | Defer | Retain this as a mandatory security constraint for the corresponding deferred capability. | The dependent feature is deferred. |
| V2-SEC-039 | External notification and pub/sub adapters must fail closed when credentials are missing or malformed. | Defer | Retain this as a mandatory security constraint for the corresponding deferred capability. | The dependent feature is deferred. |
| V2-SEC-040 | Idempotency keys must not encode raw secrets or raw payloads. | Modify | Apply the requirement to the accepted core security boundary with bounded, non-mutating redaction and deterministic failures. | V1 security is valuable but inconsistent. |
| V2-SEC-041 | Event IDs, request IDs, workflow IDs, and correlation IDs must be safe for logs and metrics. | Modify | Apply the requirement to the accepted core security boundary with bounded, non-mutating redaction and deterministic failures. | V1 security is valuable but inconsistent. |
| V2-SEC-042 | Event payload hashes, if used for idempotency conflict detection, must not allow reconstruction of sensitive payloads. | Modify | Apply the requirement to the accepted core security boundary with bounded, non-mutating redaction and deterministic failures. | V1 security is valuable but inconsistent. |
| V2-SEC-043 | Queue diagnostics must not include raw payloads. | Modify | Apply the requirement to the accepted core security boundary with bounded, non-mutating redaction and deterministic failures. | V1 security is valuable but inconsistent. |
| V2-SEC-044 | Circuit-breaker diagnostics must not include credentials, provider tokens, message bodies, or raw event payloads. | Defer | Retain this as a mandatory security constraint for the corresponding deferred capability. | The dependent feature is deferred. |
| V2-SEC-045 | Clock-drift diagnostics must not expose infrastructure secrets. | Modify | Apply the requirement to the accepted core security boundary with bounded, non-mutating redaction and deterministic failures. | V1 security is valuable but inconsistent. |
| V2-SEC-046 | Redaction allowlist configuration must be reviewed and tested. | Modify | Apply the requirement to the accepted core security boundary with bounded, non-mutating redaction and deterministic failures. | V1 security is valuable but inconsistent. |
| V2-SEC-047 | Redaction allowlist entries must be narrow and auditable. | Modify | Apply the requirement to the accepted core security boundary with bounded, non-mutating redaction and deterministic failures. | V1 security is valuable but inconsistent. |
| V2-SEC-048 | Redaction denylist patterns must be extendable through configuration without code changes. | Modify | Apply the requirement to the accepted core security boundary with bounded, non-mutating redaction and deterministic failures. | V1 security is valuable but inconsistent. |
| V2-SEC-049 | Redaction allowlist changes must require security review, owner approval, reason, reviewer, timestamp, scope, expiration or review date, and regression tests. | Modify | Apply the requirement to the accepted core security boundary with bounded, non-mutating redaction and deterministic failures. | V1 security is valuable but inconsistent. |
| V2-SEC-050 | Redaction false-positive remediation must prefer narrow field-path allowlist entries over broad pattern exemptions. | Modify | Apply the requirement to the accepted core security boundary with bounded, non-mutating redaction and deterministic failures. | V1 security is valuable but inconsistent. |
| V2-SEC-051 | Redaction allowlist entries must never allow values from known secret fields such as passwords, API keys, broker credentials, tokens, private keys, authorization headers, Telegram bot tokens, or notification credentials. | Defer | Retain this as a mandatory security constraint for the corresponding deferred capability. | The dependent feature is deferred. |
| V2-SEC-052 | Redaction denylist and allowlist conflicts must fail closed unless a documented security-reviewed override exists. | Modify | Apply the requirement to the accepted core security boundary with bounded, non-mutating redaction and deterministic failures. | V1 security is valuable but inconsistent. |
| V2-SEC-053 | Metric labels must reject raw IDs, arbitrary user strings, exception strings, notification recipients, provider tokens, and event payload values. | Defer | Retain this as a mandatory security constraint for the corresponding deferred capability. | The dependent feature is deferred. |
| V2-SEC-054 | Dead-letter payloads must be redacted by default before storage or forwarding. | Defer | Retain this as a mandatory security constraint for the corresponding deferred capability. | The dependent feature is deferred. |
| V2-SEC-055 | Notification markdown rendering must escape or sanitize unsafe user-controlled content where applicable. | Defer | Retain this as a mandatory security constraint for the corresponding deferred capability. | The dependent feature is deferred. |
| V2-SEC-056 | Auth and notification provider credentials must be excluded from Event Bus payloads by default. | Defer | Retain this as a mandatory security constraint for the corresponding deferred capability. | The dependent feature is deferred. |


#### 5.1 Error Handling Expectations


| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
| --- | --- | --- | --- | --- |
| V2-ERR-001 | Support helpers may raise typed HaruQuant exceptions for programmer or validation errors. | Keep | Adopt as the final core error-boundary behavior. | It supports predictable native helpers and official tool envelopes. |
| V2-ERR-002 | Official AI tools must not raise expected validation errors to callers. | Keep | Adopt as the final core error-boundary behavior. | It supports predictable native helpers and official tool envelopes. |
| V2-ERR-003 | Official AI tools must return standard error envelopes for expected validation failures. | Keep | Adopt as the final core error-boundary behavior. | It supports predictable native helpers and official tool envelopes. |
| V2-ERR-004 | Expected validation failures should use deterministic codes such as `INVALID_INPUT` or `VALIDATION_FAILED`. | Keep | Adopt as the final core error-boundary behavior. | It supports predictable native helpers and official tool envelopes. |
| V2-ERR-005 | Unexpected execution failures must return `TOOL_EXECUTION_FAILED` or another safe deterministic error code. | Keep | Adopt as the final core error-boundary behavior. | It supports predictable native helpers and official tool envelopes. |
| V2-ERR-006 | Raw exception objects must never be returned in `data`. | Keep | Adopt as the final core error-boundary behavior. | It supports predictable native helpers and official tool envelopes. |
| V2-ERR-007 | Raw exception objects must never be returned in `error`. | Keep | Adopt as the final core error-boundary behavior. | It supports predictable native helpers and official tool envelopes. |
| V2-ERR-008 | Error details must not expose secrets. | Keep | Adopt as the final core error-boundary behavior. | It supports predictable native helpers and official tool envelopes. |
| V2-ERR-009 | Unknown non-HaruQuant exceptions must map safely to `UNKNOWN_ERROR` or `TOOL_EXECUTION_FAILED`. | Keep | Adopt as the final core error-boundary behavior. | It supports predictable native helpers and official tool envelopes. |
| V2-ERR-010 | Domain-specific errors must be mappable through `Error` inheritance or a compatible `code` attribute. | Keep | Adopt as the final core error-boundary behavior. | It supports predictable native helpers and official tool envelopes. |
| V2-ERR-011 | Error helpers must not raise for unknown codes unless explicitly requested. | Keep | Adopt as the final core error-boundary behavior. | It supports predictable native helpers and official tool envelopes. |
| V2-ERR-012 | Error messages must be human-readable and actionable. | Keep | Adopt as the final core error-boundary behavior. | It supports predictable native helpers and official tool envelopes. |
| V2-ERR-013 | Auth failures must map to `PERMISSION_DENIED`, `INVALID_AUTH_CONTEXT`, or `AUTHORIZATION_FAILED`. | Keep | Adopt as the final core error-boundary behavior. | It supports predictable native helpers and official tool envelopes. |
| V2-ERR-014 | Event validation failures must map to `INVALID_EVENT`. | Defer | Reserve this deterministic code/handling rule for the deferred production capability. | The dependent capability is deferred. |
| V2-ERR-015 | Event publish failures must map to `EVENT_PUBLISH_FAILED`. | Defer | Reserve this deterministic code/handling rule for the deferred production capability. | The dependent capability is deferred. |
| V2-ERR-016 | Event subscriber failures must map to `EVENT_HANDLER_FAILED`. | Defer | Reserve this deterministic code/handling rule for the deferred production capability. | The dependent capability is deferred. |
| V2-ERR-017 | Dead-letter routing failures must map to `EVENT_DEAD_LETTER_FAILED`. | Defer | Reserve this deterministic code/handling rule for the deferred production capability. | The dependent capability is deferred. |
| V2-ERR-018 | Queue-full errors must be returned immediately to publishers. | Keep | Adopt as the final core error-boundary behavior. | It supports predictable native helpers and official tool envelopes. |
| V2-ERR-019 | Queue-full errors must include sanitized queue diagnostics. | Keep | Adopt as the final core error-boundary behavior. | It supports predictable native helpers and official tool envelopes. |
| V2-ERR-020 | Backpressure errors must be distinct from subscriber execution errors. | Keep | Adopt as the final core error-boundary behavior. | It supports predictable native helpers and official tool envelopes. |
| V2-ERR-021 | Subscriber execution errors must not be misclassified as publish failures unless publish requires synchronous all-handler success. | Keep | Adopt as the final core error-boundary behavior. | It supports predictable native helpers and official tool envelopes. |
| V2-ERR-022 | Notification routing failures must map to `NOTIFICATION_FAILED`. | Defer | Reserve this deterministic code/handling rule for the deferred production capability. | The dependent capability is deferred. |
| V2-ERR-023 | Notification configuration failures must map to `CONFIGURATION_ERROR`. | Defer | Reserve this deterministic code/handling rule for the deferred production capability. | The dependent capability is deferred. |
| V2-ERR-024 | Notification failures must distinguish configuration failure, provider timeout, provider rejection, circuit-open state, throttling, and suppression. | Defer | Reserve this deterministic code/handling rule for the deferred production capability. | The dependent capability is deferred. |
| V2-ERR-025 | Observability export failures must map to `OBSERVABILITY_ERROR` or `CONFIGURATION_ERROR`. | Defer | Reserve this deterministic code/handling rule for the deferred production capability. | The dependent capability is deferred. |
| V2-ERR-026 | Metrics recording failures must not fail the original operation unless explicitly configured to fail closed. | Defer | Reserve this deterministic code/handling rule for the deferred production capability. | The dependent capability is deferred. |
| V2-ERR-027 | Circuit-open failures must return `CIRCUIT_OPEN` or provider-specific deterministic details. | Defer | Reserve this deterministic code/handling rule for the deferred production capability. | The dependent capability is deferred. |
| V2-ERR-028 | Circuit-open failures must be observable through logs and metrics. | Defer | Reserve this deterministic code/handling rule for the deferred production capability. | The dependent capability is deferred. |
| V2-ERR-029 | Clock-drift health failures must return `CLOCK_DRIFT_DETECTED` where the error boundary requires a deterministic code. | Defer | Reserve this deterministic code/handling rule for the deferred production capability. | The dependent capability is deferred. |
| V2-ERR-030 | Schema validation errors must include invalid-field path, error code, sanitized message, and bounded details. | Keep | Adopt as the final core error-boundary behavior. | It supports predictable native helpers and official tool envelopes. |
| V2-ERR-031 | Redaction allowlist misuse must return `SECURITY_ERROR` or a more specific deterministic security code. | Keep | Adopt as the final core error-boundary behavior. | It supports predictable native helpers and official tool envelopes. |
| V2-ERR-032 | Error routing failures must not recursively trigger infinite error routing. | Defer | Reserve this deterministic code/handling rule for the deferred production capability. | The dependent capability is deferred. |
| V2-ERR-033 | Error events must include sanitized details only. | Defer | Reserve this deterministic code/handling rule for the deferred production capability. | The dependent capability is deferred. |
| V2-ERR-034 | Alert failures must be logged and measured without exposing secrets. | Defer | Reserve this deterministic code/handling rule for the deferred production capability. | The dependent capability is deferred. |
| V2-ERR-035 | Unknown Event Bus or notification provider errors must map safely to deterministic error codes. | Defer | Reserve this deterministic code/handling rule for the deferred production capability. | The dependent capability is deferred. |
| V2-ERR-036 | Error routing must preserve original error code and attach routing failure code separately when both exist. | Defer | Reserve this deterministic code/handling rule for the deferred production capability. | The dependent capability is deferred. |


#### Approved Error-Code Registry Additions


| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
| --- | --- | --- | --- | --- |
| V2-ERR-CODE-001 | `INVALID_AUTH_CONTEXT` | Add | Add `INVALID_AUTH_CONTEXT` to the shared approved registry. | The accepted core auth/security capability needs a deterministic code. |
| V2-ERR-CODE-002 | `AUTHORIZATION_FAILED` | Add | Add `AUTHORIZATION_FAILED` to the shared approved registry. | The accepted core auth/security capability needs a deterministic code. |
| V2-ERR-CODE-003 | `INVALID_EVENT` | Defer | Reserve `INVALID_EVENT` for the deferred events/notification/observability capability. | The code has no accepted core caller yet. |
| V2-ERR-CODE-004 | `EVENT_PUBLISH_FAILED` | Defer | Reserve `EVENT_PUBLISH_FAILED` for the deferred events/notification/observability capability. | The code has no accepted core caller yet. |
| V2-ERR-CODE-005 | `EVENT_HANDLER_FAILED` | Defer | Reserve `EVENT_HANDLER_FAILED` for the deferred events/notification/observability capability. | The code has no accepted core caller yet. |
| V2-ERR-CODE-006 | `EVENT_DEAD_LETTER_FAILED` | Defer | Reserve `EVENT_DEAD_LETTER_FAILED` for the deferred events/notification/observability capability. | The code has no accepted core caller yet. |
| V2-ERR-CODE-007 | `QUEUE_FULL` | Defer | Reserve `QUEUE_FULL` for the deferred events/notification/observability capability. | The code has no accepted core caller yet. |
| V2-ERR-CODE-008 | `BACKPRESSURE_EXCEEDED` | Defer | Reserve `BACKPRESSURE_EXCEEDED` for the deferred events/notification/observability capability. | The code has no accepted core caller yet. |
| V2-ERR-CODE-009 | `NOTIFICATION_FAILED` | Defer | Reserve `NOTIFICATION_FAILED` for the deferred events/notification/observability capability. | The code has no accepted core caller yet. |
| V2-ERR-CODE-010 | `NOTIFICATION_SUPPRESSED` | Defer | Reserve `NOTIFICATION_SUPPRESSED` for the deferred events/notification/observability capability. | The code has no accepted core caller yet. |
| V2-ERR-CODE-011 | `NOTIFICATION_THROTTLED` | Defer | Reserve `NOTIFICATION_THROTTLED` for the deferred events/notification/observability capability. | The code has no accepted core caller yet. |
| V2-ERR-CODE-012 | `OBSERVABILITY_ERROR` | Defer | Reserve `OBSERVABILITY_ERROR` for the deferred events/notification/observability capability. | The code has no accepted core caller yet. |
| V2-ERR-CODE-013 | `METRICS_EXPORT_FAILED` | Defer | Reserve `METRICS_EXPORT_FAILED` for the deferred events/notification/observability capability. | The code has no accepted core caller yet. |
| V2-ERR-CODE-014 | `CLOCK_DRIFT_DETECTED` | Defer | Reserve `CLOCK_DRIFT_DETECTED` for the deferred events/notification/observability capability. | The code has no accepted core caller yet. |
| V2-ERR-CODE-015 | `CIRCUIT_OPEN` | Keep | Retain `CIRCUIT_OPEN` for future provider boundaries; V1 already defines it. | Existing deterministic behavior is valuable. |
| V2-ERR-CODE-016 | `SECRET_VERSION_CONFLICT` | Add | Add `SECRET_VERSION_CONFLICT` to the shared approved registry. | The accepted core auth/security capability needs a deterministic code. |


#### 6.1 Edge Cases


| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
| --- | --- | --- | --- | --- |
| V2-TEST-EDGE-001 | Empty or unsafe ID prefixes must fail validation. | Add | Cover this accepted core edge case with deterministic unit or contract tests. | The V1 audit could not verify complete coverage or execution. |
| V2-TEST-EDGE-002 | `ensure_version(None)` must return the default. | Add | Cover this accepted core edge case with deterministic unit or contract tests. | The V1 audit could not verify complete coverage or execution. |
| V2-TEST-EDGE-003 | Invalid datetime inputs must fail clearly. | Add | Cover this accepted core edge case with deterministic unit or contract tests. | The V1 audit could not verify complete coverage or execution. |
| V2-TEST-EDGE-004 | Naive datetimes must be normalized using the explicit assumed timezone. | Add | Cover this accepted core edge case with deterministic unit or contract tests. | The V1 audit could not verify complete coverage or execution. |
| V2-TEST-EDGE-005 | Stale checks must be deterministic when `now` is injected. | Add | Cover this accepted core edge case with deterministic unit or contract tests. | The V1 audit could not verify complete coverage or execution. |
| V2-TEST-EDGE-006 | Empty paths must fail validation. | Add | Cover this accepted core edge case with deterministic unit or contract tests. | The V1 audit could not verify complete coverage or execution. |
| V2-TEST-EDGE-007 | Unsafe path traversal outside `base_dir` must be rejected. | Add | Cover this accepted core edge case with deterministic unit or contract tests. | The V1 audit could not verify complete coverage or execution. |
| V2-TEST-EDGE-008 | Missing pandas must fail only when dataframe helpers are called. | Add | Cover this accepted core edge case with deterministic unit or contract tests. | The V1 audit could not verify complete coverage or execution. |
| V2-TEST-EDGE-009 | Missing required dataframe columns must fail clearly. | Add | Cover this accepted core edge case with deterministic unit or contract tests. | The V1 audit could not verify complete coverage or execution. |
| V2-TEST-EDGE-010 | Empty dataframes must be handled deterministically. | Add | Cover this accepted core edge case with deterministic unit or contract tests. | The V1 audit could not verify complete coverage or execution. |
| V2-TEST-EDGE-011 | Dataframe index mismatch must fail clearly when deterministic alignment is impossible. | Add | Cover this accepted core edge case with deterministic unit or contract tests. | The V1 audit could not verify complete coverage or execution. |
| V2-TEST-EDGE-012 | `chunked(size <= 0)` must fail clearly. | Add | Cover this accepted core edge case with deterministic unit or contract tests. | The V1 audit could not verify complete coverage or execution. |
| V2-TEST-EDGE-013 | Invalid OHLCV input type must return `INVALID_INPUT`. | Add | Cover this accepted core edge case with deterministic unit or contract tests. | The V1 audit could not verify complete coverage or execution. |
| V2-TEST-EDGE-014 | Missing mandatory OHLC columns must return structured `INVALID_INPUT`. | Add | Cover this accepted core edge case with deterministic unit or contract tests. | The V1 audit could not verify complete coverage or execution. |
| V2-TEST-EDGE-015 | Extra OHLCV columns must not fail validation unless they create ambiguity. | Add | Cover this accepted core edge case with deterministic unit or contract tests. | The V1 audit could not verify complete coverage or execution. |
| V2-TEST-EDGE-016 | Unparseable datetimes must be reported. | Add | Cover this accepted core edge case with deterministic unit or contract tests. | The V1 audit could not verify complete coverage or execution. |
| V2-TEST-EDGE-017 | Non-monotonic timestamps must be reported. | Add | Cover this accepted core edge case with deterministic unit or contract tests. | The V1 audit could not verify complete coverage or execution. |
| V2-TEST-EDGE-018 | Duplicate timestamps must be reported. | Add | Cover this accepted core edge case with deterministic unit or contract tests. | The V1 audit could not verify complete coverage or execution. |
| V2-TEST-EDGE-019 | Duplicate OHLC/OHLCV rows must be reported. | Add | Cover this accepted core edge case with deterministic unit or contract tests. | The V1 audit could not verify complete coverage or execution. |
| V2-TEST-EDGE-020 | Missing timestamps or inferred gaps must be reported when timeframe is known. | Add | Cover this accepted core edge case with deterministic unit or contract tests. | The V1 audit could not verify complete coverage or execution. |
| V2-TEST-EDGE-021 | Market-calendar gaps must be distinguished from unexpected gaps where session rules are supplied. | Add | Cover this accepted core edge case with deterministic unit or contract tests. | The V1 audit could not verify complete coverage or execution. |
| V2-TEST-EDGE-022 | Non-numeric OHLC values must be reported. | Add | Cover this accepted core edge case with deterministic unit or contract tests. | The V1 audit could not verify complete coverage or execution. |
| V2-TEST-EDGE-023 | Negative prices must be reported. | Add | Cover this accepted core edge case with deterministic unit or contract tests. | The V1 audit could not verify complete coverage or execution. |
| V2-TEST-EDGE-024 | Zero prices must be reported. | Add | Cover this accepted core edge case with deterministic unit or contract tests. | The V1 audit could not verify complete coverage or execution. |
| V2-TEST-EDGE-025 | Invalid high-low relationships must be reported. | Add | Cover this accepted core edge case with deterministic unit or contract tests. | The V1 audit could not verify complete coverage or execution. |
| V2-TEST-EDGE-026 | OHLC values outside high/low range must be reported. | Add | Cover this accepted core edge case with deterministic unit or contract tests. | The V1 audit could not verify complete coverage or execution. |
| V2-TEST-EDGE-027 | Zero volume must be reported when volume is supplied. | Add | Cover this accepted core edge case with deterministic unit or contract tests. | The V1 audit could not verify complete coverage or execution. |
| V2-TEST-EDGE-028 | Negative volume must be reported when volume is supplied. | Add | Cover this accepted core edge case with deterministic unit or contract tests. | The V1 audit could not verify complete coverage or execution. |
| V2-TEST-EDGE-029 | Non-numeric or negative spread must be reported when spread is supplied. | Add | Cover this accepted core edge case with deterministic unit or contract tests. | The V1 audit could not verify complete coverage or execution. |
| V2-TEST-EDGE-030 | Spikes must be detected using configurable thresholds. | Add | Cover this accepted core edge case with deterministic unit or contract tests. | The V1 audit could not verify complete coverage or execution. |
| V2-TEST-EDGE-031 | Flatline candles must be detected. | Add | Cover this accepted core edge case with deterministic unit or contract tests. | The V1 audit could not verify complete coverage or execution. |
| V2-TEST-EDGE-032 | NaN and infinity values must be detected. | Add | Cover this accepted core edge case with deterministic unit or contract tests. | The V1 audit could not verify complete coverage or execution. |
| V2-TEST-EDGE-033 | Symbol mismatches must be reported when symbol verification is available. | Add | Cover this accepted core edge case with deterministic unit or contract tests. | The V1 audit could not verify complete coverage or execution. |
| V2-TEST-EDGE-034 | Symbol verification must be marked `not_available` when no symbol column exists. | Add | Cover this accepted core edge case with deterministic unit or contract tests. | The V1 audit could not verify complete coverage or execution. |
| V2-TEST-EDGE-035 | Timeframe mismatches must be reported when timeframe is supplied. | Add | Cover this accepted core edge case with deterministic unit or contract tests. | The V1 audit could not verify complete coverage or execution. |
| V2-TEST-EDGE-036 | Issue lists and issue samples must truncate when limits are reached. | Add | Cover this accepted core edge case with deterministic unit or contract tests. | The V1 audit could not verify complete coverage or execution. |
| V2-TEST-EDGE-037 | Missing required payload fields must fail explicitly. | Add | Cover this accepted core edge case with deterministic unit or contract tests. | The V1 audit could not verify complete coverage or execution. |
| V2-TEST-EDGE-038 | Schema version mismatches must fail with `VALIDATION_FAILED`. | Add | Cover this accepted core edge case with deterministic unit or contract tests. | The V1 audit could not verify complete coverage or execution. |
| V2-TEST-EDGE-039 | Schema validation of deeply nested payloads must stop at configured depth. | Add | Cover this accepted core edge case with deterministic unit or contract tests. | The V1 audit could not verify complete coverage or execution. |
| V2-TEST-EDGE-040 | Schema validation of oversized payloads must fail with bounded diagnostics. | Add | Cover this accepted core edge case with deterministic unit or contract tests. | The V1 audit could not verify complete coverage or execution. |
| V2-TEST-EDGE-041 | Schema validation errors for nested fields must include deterministic field paths. | Add | Cover this accepted core edge case with deterministic unit or contract tests. | The V1 audit could not verify complete coverage or execution. |
| V2-TEST-EDGE-042 | Blocked-action payloads without `action` must fail clearly. | Add | Cover this accepted core edge case with deterministic unit or contract tests. | The V1 audit could not verify complete coverage or execution. |
| V2-TEST-EDGE-043 | Blocked actions must fail closed. | Add | Cover this accepted core edge case with deterministic unit or contract tests. | The V1 audit could not verify complete coverage or execution. |
| V2-TEST-EDGE-044 | Missing freshness metadata must fail. | Add | Cover this accepted core edge case with deterministic unit or contract tests. | The V1 audit could not verify complete coverage or execution. |
| V2-TEST-EDGE-045 | Stale data must fail deterministically. | Add | Cover this accepted core edge case with deterministic unit or contract tests. | The V1 audit could not verify complete coverage or execution. |
| V2-TEST-EDGE-046 | Invalid environment modes must fail. | Add | Cover this accepted core edge case with deterministic unit or contract tests. | The V1 audit could not verify complete coverage or execution. |
| V2-TEST-EDGE-047 | Artifact references missing identity, version, or location/hash must fail. | Add | Cover this accepted core edge case with deterministic unit or contract tests. | The V1 audit could not verify complete coverage or execution. |
| V2-TEST-EDGE-048 | Sensitive nested mappings and lists must be redacted without mutating input. | Add | Cover this accepted core edge case with deterministic unit or contract tests. | The V1 audit could not verify complete coverage or execution. |
| V2-TEST-EDGE-049 | Redaction helpers must not mutate the original input object. | Add | Cover this accepted core edge case with deterministic unit or contract tests. | The V1 audit could not verify complete coverage or execution. |
| V2-TEST-EDGE-050 | Excessively deep redaction structures must stop at `MAX_REDACTION_DEPTH`. | Add | Cover this accepted core edge case with deterministic unit or contract tests. | The V1 audit could not verify complete coverage or execution. |
| V2-TEST-EDGE-051 | Invalid encryption input must fail safely. | Add | Cover this accepted core edge case with deterministic unit or contract tests. | The V1 audit could not verify complete coverage or execution. |
| V2-TEST-EDGE-052 | Missing or malformed encryption keys must fail without leaking key material. | Add | Cover this accepted core edge case with deterministic unit or contract tests. | The V1 audit could not verify complete coverage or execution. |
| V2-TEST-EDGE-053 | Missing active secret versions must fail with `SecurityError` or `SECRET_VERSION_NOT_FOUND`. | Add | Cover this accepted core edge case with deterministic unit or contract tests. | The V1 audit could not verify complete coverage or execution. |
| V2-TEST-EDGE-054 | Duplicate active secret versions with the same numeric version must fail with `SECRET_VERSION_CONFLICT`. | Add | Cover this accepted core edge case with deterministic unit or contract tests. | The V1 audit could not verify complete coverage or execution. |
| V2-TEST-EDGE-055 | Unknown error codes must resolve safely. | Add | Cover this accepted core edge case with deterministic unit or contract tests. | The V1 audit could not verify complete coverage or execution. |
| V2-TEST-EDGE-056 | Unknown non-HaruQuant exceptions must map safely at controlled tool boundaries. | Add | Cover this accepted core edge case with deterministic unit or contract tests. | The V1 audit could not verify complete coverage or execution. |
| V2-TEST-EDGE-057 | Missing auth context must deny access. | Add | Cover this accepted core edge case with deterministic unit or contract tests. | The V1 audit could not verify complete coverage or execution. |
| V2-TEST-EDGE-058 | Malformed auth context must deny access with a deterministic error. | Add | Cover this accepted core edge case with deterministic unit or contract tests. | The V1 audit could not verify complete coverage or execution. |
| V2-TEST-EDGE-059 | Missing required role, permission, or scope must deny access. | Add | Cover this accepted core edge case with deterministic unit or contract tests. | The V1 audit could not verify complete coverage or execution. |
| V2-TEST-EDGE-060 | Unknown tool name in authorization checks must deny access. | Add | Cover this accepted core edge case with deterministic unit or contract tests. | The V1 audit could not verify complete coverage or execution. |
| V2-TEST-EDGE-061 | Event publishing with missing event type must fail validation. | Defer | Add this edge case when the related deferred production capability is implemented. | The dependent capability is deferred. |
| V2-TEST-EDGE-062 | Event publishing with unserializable payload must fail validation. | Defer | Add this edge case when the related deferred production capability is implemented. | The dependent capability is deferred. |
| V2-TEST-EDGE-063 | Event publishing with sensitive payload must redact before logging or notification routing. | Defer | Add this edge case when the related deferred production capability is implemented. | The dependent capability is deferred. |
| V2-TEST-EDGE-064 | Duplicate event IDs must be handled idempotently where idempotency keys are supplied. | Defer | Add this edge case when the related deferred production capability is implemented. | The dependent capability is deferred. |
| V2-TEST-EDGE-065 | Idempotency cache TTL expiration must not break valid future event processing. | Defer | Add this edge case when the related deferred production capability is implemented. | The dependent capability is deferred. |
| V2-TEST-EDGE-066 | Idempotency cache eviction must not expose old event payloads. | Defer | Add this edge case when the related deferred production capability is implemented. | The dependent capability is deferred. |
| V2-TEST-EDGE-067 | Concurrent publish calls for the same idempotency key must not double-deliver an event. | Defer | Add this edge case when the related deferred production capability is implemented. | The dependent capability is deferred. |
| V2-TEST-EDGE-068 | Idempotency hash collisions or suspected collisions must fail closed with deterministic diagnostics. | Defer | Add this edge case when the related deferred production capability is implemented. | The dependent capability is deferred. |
| V2-TEST-EDGE-069 | Subscriber failure must not prevent other subscribers from receiving the event. | Defer | Add this edge case when the related deferred production capability is implemented. | The dependent capability is deferred. |
| V2-TEST-EDGE-070 | Subscriber timeout or indefinite blocking must be isolated using configured handler timeout behavior. | Defer | Add this edge case when the related deferred production capability is implemented. | The dependent capability is deferred. |
| V2-TEST-EDGE-071 | Concurrent subscriber registration and publishing must not corrupt handler lists. | Defer | Add this edge case when the related deferred production capability is implemented. | The dependent capability is deferred. |
| V2-TEST-EDGE-072 | Concurrent subscriber unregistration during publishing must have deterministic behavior. | Defer | Add this edge case when the related deferred production capability is implemented. | The dependent capability is deferred. |
| V2-TEST-EDGE-073 | Repeated subscriber failures must route to dead-letter handling after configured retry limits. | Defer | Add this edge case when the related deferred production capability is implemented. | The dependent capability is deferred. |
| V2-TEST-EDGE-074 | Event Bus queue overflow must return `QUEUE_FULL` or `BACKPRESSURE_EXCEEDED` and must not block indefinitely. | Defer | Add this edge case when the related deferred production capability is implemented. | The dependent capability is deferred. |
| V2-TEST-EDGE-075 | Logging sink failures such as disk full, permission denied, path missing, rotation failure, retention deletion failure, and network filesystem dropout must not create unhandled exceptions in callers. | Add | Cover this accepted core edge case with deterministic unit or contract tests. | The V1 audit could not verify complete coverage or execution. |
| V2-TEST-EDGE-076 | Notification channel disabled must return disabled or suppressed status without error. | Defer | Add this edge case when the related deferred production capability is implemented. | The dependent capability is deferred. |
| V2-TEST-EDGE-077 | Notification credentials missing must fail safely without leaking configuration details. | Defer | Add this edge case when the related deferred production capability is implemented. | The dependent capability is deferred. |
| V2-TEST-EDGE-078 | Notification provider timeout must return failed status and emit metrics. | Defer | Add this edge case when the related deferred production capability is implemented. | The dependent capability is deferred. |
| V2-TEST-EDGE-079 | Repeated identical alerts must be deduplicated or throttled. | Add | Cover this accepted core edge case with deterministic unit or contract tests. | The V1 audit could not verify complete coverage or execution. |
| V2-TEST-EDGE-080 | Notification markdown rendering failure must fall back to plain text. | Defer | Add this edge case when the related deferred production capability is implemented. | The dependent capability is deferred. |
| V2-TEST-EDGE-081 | Unsupported notification formatting must not fail the original operation unless fail-closed alerting is explicitly configured. | Defer | Add this edge case when the related deferred production capability is implemented. | The dependent capability is deferred. |
| V2-TEST-EDGE-082 | Prometheus dependency missing must not break module import. | Defer | Add this edge case when the related deferred production capability is implemented. | The dependent capability is deferred. |
| V2-TEST-EDGE-083 | Prometheus exporter unavailable must degrade to no-op metrics or explicit configuration error depending on caller mode. | Defer | Add this edge case when the related deferred production capability is implemented. | The dependent capability is deferred. |
| V2-TEST-EDGE-084 | High-cardinality metric labels must be rejected or normalized. | Defer | Add this edge case when the related deferred production capability is implemented. | The dependent capability is deferred. |
| V2-TEST-EDGE-085 | Health check failures must not expose secrets. | Defer | Add this edge case when the related deferred production capability is implemented. | The dependent capability is deferred. |
| V2-TEST-EDGE-086 | Recursive error routing must be detected and suppressed. | Defer | Add this edge case when the related deferred production capability is implemented. | The dependent capability is deferred. |
| V2-TEST-EDGE-087 | External pub/sub adapter outage must open the circuit after the configured threshold. | Defer | Add this edge case when the related deferred production capability is implemented. | The dependent capability is deferred. |
| V2-TEST-EDGE-088 | Notification adapter outage must open the circuit after the configured threshold. | Defer | Add this edge case when the related deferred production capability is implemented. | The dependent capability is deferred. |
| V2-TEST-EDGE-089 | Open circuit state must fail fast. | Defer | Add this edge case when the related deferred production capability is implemented. | The dependent capability is deferred. |
| V2-TEST-EDGE-090 | Half-open circuit recovery must not create duplicate event delivery. | Defer | Add this edge case when the related deferred production capability is implemented. | The dependent capability is deferred. |
| V2-TEST-EDGE-091 | Clock drift unavailable must be reported as unsupported, not healthy. | Defer | Add this edge case when the related deferred production capability is implemented. | The dependent capability is deferred. |
| V2-TEST-EDGE-092 | Clock drift above warning threshold must produce degraded health. | Defer | Add this edge case when the related deferred production capability is implemented. | The dependent capability is deferred. |
| V2-TEST-EDGE-093 | Clock drift above critical threshold must produce critical health. | Defer | Add this edge case when the related deferred production capability is implemented. | The dependent capability is deferred. |
| V2-TEST-EDGE-094 | Redaction allowlist conflicts with denylist must fail closed unless explicitly approved. | Add | Cover this accepted core edge case with deterministic unit or contract tests. | The V1 audit could not verify complete coverage or execution. |
| V2-TEST-EDGE-095 | Sensitive metric labels must be rejected before metrics emission. | Defer | Add this edge case when the related deferred production capability is implemented. | The dependent capability is deferred. |


#### 6.2 Tests Required


| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
| --- | --- | --- | --- | --- |
| V2-TEST-REQ-001 | Unit tests must exist for every utility module. | Add | Implement or retain this test/contract gate for accepted core capabilities. | The V1 audit could not execute tests or prove coverage. |
| V2-TEST-REQ-002 | Usage examples must exist for official AI tools. | Add | Implement or retain this test/contract gate for accepted core capabilities. | The V1 audit could not execute tests or prove coverage. |
| V2-TEST-REQ-003 | Minimum line coverage must be at least 80% for `app.services.utils`. | Add | Implement or retain this test/contract gate for accepted core capabilities. | The V1 audit could not execute tests or prove coverage. |
| V2-TEST-REQ-004 | Branch coverage must be meaningful for validators and security helpers. | Add | Implement or retain this test/contract gate for accepted core capabilities. | The V1 audit could not execute tests or prove coverage. |
| V2-TEST-REQ-005 | Tests must cover success paths. | Add | Implement or retain this test/contract gate for accepted core capabilities. | The V1 audit could not execute tests or prove coverage. |
| V2-TEST-REQ-006 | Tests must cover invalid inputs. | Add | Implement or retain this test/contract gate for accepted core capabilities. | The V1 audit could not execute tests or prove coverage. |
| V2-TEST-REQ-007 | Tests must cover edge cases. | Add | Implement or retain this test/contract gate for accepted core capabilities. | The V1 audit could not execute tests or prove coverage. |
| V2-TEST-REQ-008 | Tests must cover failure paths. | Add | Implement or retain this test/contract gate for accepted core capabilities. | The V1 audit could not execute tests or prove coverage. |
| V2-TEST-REQ-009 | Official AI tool tests must verify standard return schema compliance. | Add | Implement or retain this test/contract gate for accepted core capabilities. | The V1 audit could not execute tests or prove coverage. |
| V2-TEST-REQ-010 | Official AI tool tests must verify metadata correctness. | Add | Implement or retain this test/contract gate for accepted core capabilities. | The V1 audit could not execute tests or prove coverage. |
| V2-TEST-REQ-011 | Official AI tool tests must verify request ID propagation. | Add | Implement or retain this test/contract gate for accepted core capabilities. | The V1 audit could not execute tests or prove coverage. |
| V2-TEST-REQ-012 | Official AI tool tests must verify `execution_ms` existence. | Add | Implement or retain this test/contract gate for accepted core capabilities. | The V1 audit could not execute tests or prove coverage. |
| V2-TEST-REQ-013 | Official AI tool tests must verify deterministic error codes. | Add | Implement or retain this test/contract gate for accepted core capabilities. | The V1 audit could not execute tests or prove coverage. |
| V2-TEST-REQ-014 | Official AI tool tests must verify no secret leakage where relevant. | Add | Implement or retain this test/contract gate for accepted core capabilities. | The V1 audit could not execute tests or prove coverage. |
| V2-TEST-REQ-015 | Contract tests must verify every official AI tool listed in Public Capabilities has a contract entry. | Add | Implement or retain this test/contract gate for accepted core capabilities. | The V1 audit could not execute tests or prove coverage. |
| V2-TEST-REQ-016 | Contract tests must verify every public support helper listed in the registry has a contract entry or documented exception. | Add | Implement or retain this test/contract gate for accepted core capabilities. | The V1 audit could not execute tests or prove coverage. |
| V2-TEST-REQ-017 | Contract tests must verify official AI tools return `status`, `message`, `data`, `error`, and `metadata`. | Add | Implement or retain this test/contract gate for accepted core capabilities. | The V1 audit could not execute tests or prove coverage. |
| V2-TEST-REQ-018 | Contract tests must verify official AI tool metadata includes all required side-effect flags. | Add | Implement or retain this test/contract gate for accepted core capabilities. | The V1 audit could not execute tests or prove coverage. |
| V2-TEST-REQ-019 | Contract tests must verify native support helpers do not return standard envelopes unless explicitly documented. | Add | Implement or retain this test/contract gate for accepted core capabilities. | The V1 audit could not execute tests or prove coverage. |
| V2-TEST-REQ-020 | Contract tests must verify native helper names and official AI tool wrapper names do not collide when return shapes differ. | Add | Implement or retain this test/contract gate for accepted core capabilities. | The V1 audit could not execute tests or prove coverage. |
| V2-TEST-REQ-021 | Registry tests must verify every name exported from `app/services/utils/__init__.py` appears in the public registry. | Add | Implement or retain this test/contract gate for accepted core capabilities. | The V1 audit could not execute tests or prove coverage. |
| V2-TEST-REQ-022 | Registry tests must verify every public registry item is classified as official AI tool, support helper, support object, or restricted helper. | Add | Implement or retain this test/contract gate for accepted core capabilities. | The V1 audit could not execute tests or prove coverage. |
| V2-TEST-REQ-023 | Registry tests must verify restricted helpers are not agent-attachable by default. | Add | Implement or retain this test/contract gate for accepted core capabilities. | The V1 audit could not execute tests or prove coverage. |
| V2-TEST-REQ-024 | Registry tests must verify no fallback aliases, duplicate wrapper modules, or compatibility shims are exported. | Add | Implement or retain this test/contract gate for accepted core capabilities. | The V1 audit could not execute tests or prove coverage. |
| V2-TEST-REQ-025 | Logger tests must verify duplicate handler prevention. | Add | Implement or retain this test/contract gate for accepted core capabilities. | The V1 audit could not execute tests or prove coverage. |
| V2-TEST-REQ-026 | Logger tests must verify log emission does not leak passwords, tokens, API keys, broker credentials, encryption keys, private payloads, full approval packets, notification provider credentials, authorization headers, or Telegram bot tokens. | Defer | Add this test with the corresponding deferred production capability. | Testing a capability not accepted for the initial rebuild would create speculative architecture. |
| V2-TEST-REQ-027 | Logger tests must verify file logging writes only to configured safe log directories. | Add | Implement or retain this test/contract gate for accepted core capabilities. | The V1 audit could not execute tests or prove coverage. |
| V2-TEST-REQ-028 | Logger tests must verify log rotation by maximum file size or equivalent configured policy. | Add | Implement or retain this test/contract gate for accepted core capabilities. | The V1 audit could not execute tests or prove coverage. |
| V2-TEST-REQ-029 | Logger tests must verify old rotated log files are deleted according to configured retention limits without deleting unrelated files. | Add | Implement or retain this test/contract gate for accepted core capabilities. | The V1 audit could not execute tests or prove coverage. |
| V2-TEST-REQ-030 | Logger tests must simulate logging sink failures including disk full, permission denied, invalid path, rotation failure, retention deletion failure, and network filesystem dropout where practical. | Add | Implement or retain this test/contract gate for accepted core capabilities. | The V1 audit could not execute tests or prove coverage. |
| V2-TEST-REQ-031 | Logger tests must prove logging sink failures do not raise unhandled exceptions into official AI tool callers. | Add | Implement or retain this test/contract gate for accepted core capabilities. | The V1 audit could not execute tests or prove coverage. |
| V2-TEST-REQ-032 | Logger tests must prove logging sink failures increment logging error metrics or produce bounded fallback diagnostics where metrics are unavailable. | Defer | Add this test with the corresponding deferred production capability. | Testing a capability not accepted for the initial rebuild would create speculative architecture. |
| V2-TEST-REQ-033 | Logger tests must verify human-readable console formatting includes datetime, level, module path, function name, line number, and message. | Add | Implement or retain this test/contract gate for accepted core capabilities. | The V1 audit could not execute tests or prove coverage. |
| V2-TEST-REQ-034 | Logger tests must verify colorized console output can be enabled and disabled deterministically. | Add | Implement or retain this test/contract gate for accepted core capabilities. | The V1 audit could not execute tests or prove coverage. |
| V2-TEST-REQ-035 | Standard response tests must verify success envelope, error envelope, metadata, invalid schema, missing keys, execution timing, schema constants, and error code validation. | Add | Implement or retain this test/contract gate for accepted core capabilities. | The V1 audit could not execute tests or prove coverage. |
| V2-TEST-REQ-036 | Error tests must verify exception attributes, known codes, unknown codes, and fallback messages. | Add | Implement or retain this test/contract gate for accepted core capabilities. | The V1 audit could not execute tests or prove coverage. |
| V2-TEST-REQ-037 | Identity tests must verify ID uniqueness, prefix validation, and version defaulting. | Add | Implement or retain this test/contract gate for accepted core capabilities. | The V1 audit could not execute tests or prove coverage. |
| V2-TEST-REQ-038 | Normalization tests must verify ISO parsing, naive timezone assumptions, UTC conversion, and stale checks. | Add | Implement or retain this test/contract gate for accepted core capabilities. | The V1 audit could not execute tests or prove coverage. |
| V2-TEST-REQ-039 | Path tests must verify safe normalization, unsafe traversal, directory creation, and parent creation. | Add | Implement or retain this test/contract gate for accepted core capabilities. | The V1 audit could not execute tests or prove coverage. |
| V2-TEST-REQ-040 | Dataframe tests must verify alignment, serialization, UTC timestamp output, comparison, index mismatch behavior, missing columns, chunk-size validation, and no input mutation. | Add | Implement or retain this test/contract gate for accepted core capabilities. | The V1 audit could not execute tests or prove coverage. |
| V2-TEST-REQ-041 | Data-quality tests must verify clean OHLCV data, missing columns, extra columns, symbol mismatch, timeframe mismatch, duplicates, gaps, bad OHLC, zero/negative values, spread, volume, spikes, flatlines, truncation limits, and schema compliance. | Add | Implement or retain this test/contract gate for accepted core capabilities. | The V1 audit could not execute tests or prove coverage. |
| V2-TEST-REQ-042 | Data-quality tests must cover at least 15 distinct data-quality cases. | Add | Implement or retain this test/contract gate for accepted core capabilities. | The V1 audit could not execute tests or prove coverage. |
| V2-TEST-REQ-043 | Data-quality tests must verify 10,000 bad rows return no more than configured issue and sample limits. | Add | Implement or retain this test/contract gate for accepted core capabilities. | The V1 audit could not execute tests or prove coverage. |
| V2-TEST-REQ-044 | Schema-validation tests must verify native helper results, required fields, input/output schemas, schema versioning, handoffs, evidence, approvals, registry entries, blocked actions, freshness, and artifact references. | Add | Implement or retain this test/contract gate for accepted core capabilities. | The V1 audit could not execute tests or prove coverage. |
| V2-TEST-REQ-045 | Schema-validation tests must verify invalid-field paths for flat and nested payloads. | Add | Implement or retain this test/contract gate for accepted core capabilities. | The V1 audit could not execute tests or prove coverage. |
| V2-TEST-REQ-046 | Schema-validation tests must verify payload-size, depth, field-count, issue-count, and sample-count limits. | Add | Implement or retain this test/contract gate for accepted core capabilities. | The V1 audit could not execute tests or prove coverage. |
| V2-TEST-REQ-047 | Schema-validation tests must verify low-latency behavior with representative market-data payloads. | Add | Implement or retain this test/contract gate for accepted core capabilities. | The V1 audit could not execute tests or prove coverage. |
| V2-TEST-REQ-048 | Schema-validation tests must verify no blocking I/O or network access occurs. | Add | Implement or retain this test/contract gate for accepted core capabilities. | The V1 audit could not execute tests or prove coverage. |
| V2-TEST-REQ-049 | Security tests must verify redaction, nested redaction, password hashing, password verification, Fernet key behavior, encryption round trip, invalid tokens, secret selection, and `SECRET_VERSION_NOT_FOUND`. | Add | Implement or retain this test/contract gate for accepted core capabilities. | The V1 audit could not execute tests or prove coverage. |
| V2-TEST-REQ-050 | Security tests must verify native redaction helper output shape separately from official redaction tool wrapper output shape. | Add | Implement or retain this test/contract gate for accepted core capabilities. | The V1 audit could not execute tests or prove coverage. |
| V2-TEST-REQ-051 | Security tests must verify `redact_text_value` and `redact_mapping_value` return native values. | Add | Implement or retain this test/contract gate for accepted core capabilities. | The V1 audit could not execute tests or prove coverage. |
| V2-TEST-REQ-052 | Security tests must verify `redact_text_tool` and `redact_mapping_tool` return standard envelopes. | Add | Implement or retain this test/contract gate for accepted core capabilities. | The V1 audit could not execute tests or prove coverage. |
| V2-TEST-REQ-053 | Security tests must verify redaction denylist matching. | Add | Implement or retain this test/contract gate for accepted core capabilities. | The V1 audit could not execute tests or prove coverage. |
| V2-TEST-REQ-054 | Security tests must verify audited allowlist exceptions. | Add | Implement or retain this test/contract gate for accepted core capabilities. | The V1 audit could not execute tests or prove coverage. |
| V2-TEST-REQ-055 | Security tests must verify denylist/allowlist conflict behavior. | Add | Implement or retain this test/contract gate for accepted core capabilities. | The V1 audit could not execute tests or prove coverage. |
| V2-TEST-REQ-056 | Security tests must verify redaction diagnostics reveal field paths redacted but never redacted values. | Add | Implement or retain this test/contract gate for accepted core capabilities. | The V1 audit could not execute tests or prove coverage. |
| V2-TEST-REQ-057 | Security tests must verify long strings, deeply nested objects, lists of mappings, exception strings, and metadata are redacted consistently. | Add | Implement or retain this test/contract gate for accepted core capabilities. | The V1 audit could not execute tests or prove coverage. |
| V2-TEST-REQ-058 | Security tests must verify redaction helpers do not mutate the original input object. | Add | Implement or retain this test/contract gate for accepted core capabilities. | The V1 audit could not execute tests or prove coverage. |
| V2-TEST-REQ-059 | Security tests must verify redaction denylist extensions can be loaded from configuration with audit metadata. | Add | Implement or retain this test/contract gate for accepted core capabilities. | The V1 audit could not execute tests or prove coverage. |
| V2-TEST-REQ-060 | Security tests must verify redaction false-positive allowlist entries are narrow, reviewed, and cannot expose known secret fields. | Add | Implement or retain this test/contract gate for accepted core capabilities. | The V1 audit could not execute tests or prove coverage. |
| V2-TEST-REQ-061 | Security tests must verify metric labels reject sensitive or high-cardinality values. | Defer | Add this test with the corresponding deferred production capability. | Testing a capability not accepted for the initial rebuild would create speculative architecture. |
| V2-TEST-REQ-062 | Settings tests must verify defaults, mapping load, invalid environments, `strict_validation`, path normalization, and injection. | Add | Implement or retain this test/contract gate for accepted core capabilities. | The V1 audit could not execute tests or prove coverage. |
| V2-TEST-REQ-063 | Auth tests must cover valid auth context. | Add | Implement or retain this test/contract gate for accepted core capabilities. | The V1 audit could not execute tests or prove coverage. |
| V2-TEST-REQ-064 | Auth tests must cover missing auth context. | Add | Implement or retain this test/contract gate for accepted core capabilities. | The V1 audit could not execute tests or prove coverage. |
| V2-TEST-REQ-065 | Auth tests must cover malformed auth context. | Add | Implement or retain this test/contract gate for accepted core capabilities. | The V1 audit could not execute tests or prove coverage. |
| V2-TEST-REQ-066 | Auth tests must cover missing role, permission, and scope. | Add | Implement or retain this test/contract gate for accepted core capabilities. | The V1 audit could not execute tests or prove coverage. |
| V2-TEST-REQ-067 | Auth tests must cover denied-by-default behavior. | Add | Implement or retain this test/contract gate for accepted core capabilities. | The V1 audit could not execute tests or prove coverage. |
| V2-TEST-REQ-068 | Auth tests must verify no token or credential leakage. | Add | Implement or retain this test/contract gate for accepted core capabilities. | The V1 audit could not execute tests or prove coverage. |
| V2-TEST-REQ-069 | Event Bus tests must cover publish success. | Defer | Add this test with the corresponding deferred production capability. | Testing a capability not accepted for the initial rebuild would create speculative architecture. |
| V2-TEST-REQ-070 | Event Bus tests must cover subscription and unsubscription. | Defer | Add this test with the corresponding deferred production capability. | Testing a capability not accepted for the initial rebuild would create speculative architecture. |
| V2-TEST-REQ-071 | Event Bus tests must verify deterministic ordered handler execution per event type for the in-process bus. | Defer | Add this test with the corresponding deferred production capability. | Testing a capability not accepted for the initial rebuild would create speculative architecture. |
| V2-TEST-REQ-072 | Event Bus tests must cover subscriber failure isolation. | Defer | Add this test with the corresponding deferred production capability. | Testing a capability not accepted for the initial rebuild would create speculative architecture. |
| V2-TEST-REQ-073 | Event Bus tests must cover retry and dead-letter behavior. | Defer | Add this test with the corresponding deferred production capability. | Testing a capability not accepted for the initial rebuild would create speculative architecture. |
| V2-TEST-REQ-074 | Event Bus tests must cover idempotency keys. | Defer | Add this test with the corresponding deferred production capability. | Testing a capability not accepted for the initial rebuild would create speculative architecture. |
| V2-TEST-REQ-075 | Event Bus tests must verify idempotency TTL expiration. | Defer | Add this test with the corresponding deferred production capability. | Testing a capability not accepted for the initial rebuild would create speculative architecture. |
| V2-TEST-REQ-076 | Event Bus tests must verify maximum idempotency cache size enforcement. | Defer | Add this test with the corresponding deferred production capability. | Testing a capability not accepted for the initial rebuild would create speculative architecture. |
| V2-TEST-REQ-077 | Event Bus tests must verify idempotency cache eviction under load. | Defer | Add this test with the corresponding deferred production capability. | Testing a capability not accepted for the initial rebuild would create speculative architecture. |
| V2-TEST-REQ-078 | Event Bus tests must verify duplicate idempotency key handling. | Defer | Add this test with the corresponding deferred production capability. | Testing a capability not accepted for the initial rebuild would create speculative architecture. |
| V2-TEST-REQ-079 | Event Bus tests must verify idempotency entries store only approved compact metadata and never raw payloads. | Defer | Add this test with the corresponding deferred production capability. | Testing a capability not accepted for the initial rebuild would create speculative architecture. |
| V2-TEST-REQ-080 | Event Bus tests must verify idempotency hash mismatch returns deterministic conflict diagnostics. | Defer | Add this test with the corresponding deferred production capability. | Testing a capability not accepted for the initial rebuild would create speculative architecture. |
| V2-TEST-REQ-081 | Event Bus tests must verify suspected idempotency hash collisions fail closed or follow the approved non-sensitive disambiguation design. | Defer | Add this test with the corresponding deferred production capability. | Testing a capability not accepted for the initial rebuild would create speculative architecture. |
| V2-TEST-REQ-082 | Event Bus tests must verify concurrent publish behavior. | Defer | Add this test with the corresponding deferred production capability. | Testing a capability not accepted for the initial rebuild would create speculative architecture. |
| V2-TEST-REQ-083 | Event Bus tests must verify concurrent subscribe and unsubscribe behavior. | Defer | Add this test with the corresponding deferred production capability. | Testing a capability not accepted for the initial rebuild would create speculative architecture. |
| V2-TEST-REQ-084 | Event Bus tests must verify concurrent retry and dead-letter behavior where supported. | Defer | Add this test with the corresponding deferred production capability. | Testing a capability not accepted for the initial rebuild would create speculative architecture. |
| V2-TEST-REQ-085 | Event Bus tests must cover payload serialization failure. | Defer | Add this test with the corresponding deferred production capability. | Testing a capability not accepted for the initial rebuild would create speculative architecture. |
| V2-TEST-REQ-086 | Event Bus tests must verify queue-full behavior returns `QUEUE_FULL` or `BACKPRESSURE_EXCEEDED`. | Defer | Add this test with the corresponding deferred production capability. | Testing a capability not accepted for the initial rebuild would create speculative architecture. |
| V2-TEST-REQ-087 | Event Bus tests must verify a subscriber that blocks past `EVENT_HANDLER_TIMEOUT_MS` is isolated and does not block unrelated subscribers. | Defer | Add this test with the corresponding deferred production capability. | Testing a capability not accepted for the initial rebuild would create speculative architecture. |
| V2-TEST-REQ-088 | Event Bus tests must cover deterministic backpressure behavior. | Defer | Add this test with the corresponding deferred production capability. | Testing a capability not accepted for the initial rebuild would create speculative architecture. |
| V2-TEST-REQ-089 | Event Bus tests must verify dropped-event metrics. | Defer | Add this test with the corresponding deferred production capability. | Testing a capability not accepted for the initial rebuild would create speculative architecture. |
| V2-TEST-REQ-090 | Event Bus tests must cover queue limit or backlog diagnostics. | Defer | Add this test with the corresponding deferred production capability. | Testing a capability not accepted for the initial rebuild would create speculative architecture. |
| V2-TEST-REQ-091 | Event Bus tests must verify external adapter circuit-breaker closed, open, and half-open states with fake adapters. | Defer | Add this test with the corresponding deferred production capability. | Testing a capability not accepted for the initial rebuild would create speculative architecture. |
| V2-TEST-REQ-092 | Event Bus tests must verify no secret leakage in event logs. | Defer | Add this test with the corresponding deferred production capability. | Testing a capability not accepted for the initial rebuild would create speculative architecture. |
| V2-TEST-REQ-093 | Event Bus tests must use fake clock and fake queue implementations where needed for deterministic time and queue behavior. | Defer | Add this test with the corresponding deferred production capability. | Testing a capability not accepted for the initial rebuild would create speculative architecture. |
| V2-TEST-REQ-094 | Event Bus tests must cover disabled or no-op adapter behavior. | Defer | Add this test with the corresponding deferred production capability. | Testing a capability not accepted for the initial rebuild would create speculative architecture. |
| V2-TEST-REQ-095 | Error-routing tests must cover validation error routing. | Add | Implement or retain this test/contract gate for accepted core capabilities. | The V1 audit could not execute tests or prove coverage. |
| V2-TEST-REQ-096 | Error-routing tests must cover unexpected exception routing. | Add | Implement or retain this test/contract gate for accepted core capabilities. | The V1 audit could not execute tests or prove coverage. |
| V2-TEST-REQ-097 | Error-routing tests must cover deduplication and throttling. | Add | Implement or retain this test/contract gate for accepted core capabilities. | The V1 audit could not execute tests or prove coverage. |
| V2-TEST-REQ-098 | Error-routing tests must cover recursive error suppression. | Add | Implement or retain this test/contract gate for accepted core capabilities. | The V1 audit could not execute tests or prove coverage. |
| V2-TEST-REQ-099 | Error-routing tests must verify recursive alert suppression under circuit-open and notification-failure scenarios. | Defer | Add this test with the corresponding deferred production capability. | Testing a capability not accepted for the initial rebuild would create speculative architecture. |
| V2-TEST-REQ-100 | Notification tests must cover email routing with fake adapter. | Defer | Add this test with the corresponding deferred production capability. | Testing a capability not accepted for the initial rebuild would create speculative architecture. |
| V2-TEST-REQ-101 | Notification tests must cover Telegram routing with fake adapter. | Defer | Add this test with the corresponding deferred production capability. | Testing a capability not accepted for the initial rebuild would create speculative architecture. |
| V2-TEST-REQ-102 | Notification tests must cover desktop routing with fake adapter. | Defer | Add this test with the corresponding deferred production capability. | Testing a capability not accepted for the initial rebuild would create speculative architecture. |
| V2-TEST-REQ-103 | Notification tests must cover disabled channel behavior. | Defer | Add this test with the corresponding deferred production capability. | Testing a capability not accepted for the initial rebuild would create speculative architecture. |
| V2-TEST-REQ-104 | Notification tests must cover missing credentials. | Defer | Add this test with the corresponding deferred production capability. | Testing a capability not accepted for the initial rebuild would create speculative architecture. |
| V2-TEST-REQ-105 | Notification tests must cover provider failure and timeout behavior. | Defer | Add this test with the corresponding deferred production capability. | Testing a capability not accepted for the initial rebuild would create speculative architecture. |
| V2-TEST-REQ-106 | Notification tests must verify throttling and deduplication. | Defer | Add this test with the corresponding deferred production capability. | Testing a capability not accepted for the initial rebuild would create speculative architecture. |
| V2-TEST-REQ-107 | Notification tests must verify concurrent routing behavior. | Defer | Add this test with the corresponding deferred production capability. | Testing a capability not accepted for the initial rebuild would create speculative architecture. |
| V2-TEST-REQ-108 | Notification tests must verify concurrent suppression, throttling, deduplication, and adapter-failure behavior. | Defer | Add this test with the corresponding deferred production capability. | Testing a capability not accepted for the initial rebuild would create speculative architecture. |
| V2-TEST-REQ-109 | Notification tests must verify thread-safe or async-safe throttling and deduplication state. | Defer | Add this test with the corresponding deferred production capability. | Testing a capability not accepted for the initial rebuild would create speculative architecture. |
| V2-TEST-REQ-110 | Notification tests must verify markdown rendering. | Defer | Add this test with the corresponding deferred production capability. | Testing a capability not accepted for the initial rebuild would create speculative architecture. |
| V2-TEST-REQ-111 | Notification tests must verify plain-text fallback rendering. | Defer | Add this test with the corresponding deferred production capability. | Testing a capability not accepted for the initial rebuild would create speculative architecture. |
| V2-TEST-REQ-112 | Notification tests must verify provider circuit-breaker closed, open, and half-open states with fake adapters. | Defer | Add this test with the corresponding deferred production capability. | Testing a capability not accepted for the initial rebuild would create speculative architecture. |
| V2-TEST-REQ-113 | Notification tests must verify notification content does not leak secrets after template rendering. | Defer | Add this test with the corresponding deferred production capability. | Testing a capability not accepted for the initial rebuild would create speculative architecture. |
| V2-TEST-REQ-114 | Observability tests must cover metrics registration. | Defer | Add this test with the corresponding deferred production capability. | Testing a capability not accepted for the initial rebuild would create speculative architecture. |
| V2-TEST-REQ-115 | Observability tests must cover tool-call counters and latency histograms. | Add | Implement or retain this test/contract gate for accepted core capabilities. | The V1 audit could not execute tests or prove coverage. |
| V2-TEST-REQ-116 | Observability tests must cover Event Bus metrics. | Defer | Add this test with the corresponding deferred production capability. | Testing a capability not accepted for the initial rebuild would create speculative architecture. |
| V2-TEST-REQ-117 | Observability tests must cover notification metrics. | Defer | Add this test with the corresponding deferred production capability. | Testing a capability not accepted for the initial rebuild would create speculative architecture. |
| V2-TEST-REQ-118 | Observability tests must cover auth failure metrics. | Defer | Add this test with the corresponding deferred production capability. | Testing a capability not accepted for the initial rebuild would create speculative architecture. |
| V2-TEST-REQ-119 | Observability tests must cover no-op behavior when Prometheus dependencies are unavailable. | Defer | Add this test with the corresponding deferred production capability. | Testing a capability not accepted for the initial rebuild would create speculative architecture. |
| V2-TEST-REQ-120 | Observability tests must use fake Prometheus exporters where exporter behavior must be exercised without external services. | Defer | Add this test with the corresponding deferred production capability. | Testing a capability not accepted for the initial rebuild would create speculative architecture. |
| V2-TEST-REQ-121 | Observability tests must reject high-cardinality or sensitive metric labels. | Defer | Add this test with the corresponding deferred production capability. | Testing a capability not accepted for the initial rebuild would create speculative architecture. |
| V2-TEST-REQ-122 | Observability tests must verify metric names follow `<component>_<metric>_<unit_or_suffix>`. | Defer | Add this test with the corresponding deferred production capability. | Testing a capability not accepted for the initial rebuild would create speculative architecture. |
| V2-TEST-REQ-123 | Observability tests must verify metric label cardinality gates reject values beyond `METRIC_LABEL_MAX_DISTINCT_VALUES`. | Defer | Add this test with the corresponding deferred production capability. | Testing a capability not accepted for the initial rebuild would create speculative architecture. |
| V2-TEST-REQ-124 | Observability tests must verify clock-drift healthy, degraded, critical, unsupported, and not-configured states. | Defer | Add this test with the corresponding deferred production capability. | Testing a capability not accepted for the initial rebuild would create speculative architecture. |
| V2-TEST-REQ-125 | Observability tests must verify circuit-breaker metrics. | Defer | Add this test with the corresponding deferred production capability. | Testing a capability not accepted for the initial rebuild would create speculative architecture. |
| V2-TEST-REQ-126 | Observability tests must verify queue-depth metrics. | Defer | Add this test with the corresponding deferred production capability. | Testing a capability not accepted for the initial rebuild would create speculative architecture. |
| V2-TEST-REQ-127 | Health-check tests must cover healthy, degraded, critical, unsupported, and not-configured states. | Defer | Add this test with the corresponding deferred production capability. | Testing a capability not accepted for the initial rebuild would create speculative architecture. |
| V2-TEST-REQ-128 | Grafana documentation tests or review checks must confirm dashboards cover system health, tool health, Event Bus, notifications, errors, and auth failures. | Defer | Add this test with the corresponding deferred production capability. | Testing a capability not accepted for the initial rebuild would create speculative architecture. |
| V2-TEST-REQ-129 | Performance tests must benchmark `validate_ohlcv_quality` against the documented 1,000-row threshold. | Add | Implement or retain this test/contract gate for accepted core capabilities. | The V1 audit could not execute tests or prove coverage. |
| V2-TEST-REQ-130 | Performance tests must benchmark `validate_ohlcv_quality` against the documented 100,000-row threshold. | Add | Implement or retain this test/contract gate for accepted core capabilities. | The V1 audit could not execute tests or prove coverage. |
| V2-TEST-REQ-131 | Performance tests must verify schema validation maximum payload size, maximum depth, maximum field count, and maximum issue count. | Add | Implement or retain this test/contract gate for accepted core capabilities. | The V1 audit could not execute tests or prove coverage. |
| V2-TEST-REQ-132 | Performance tests must verify redaction maximum depth and maximum string length behavior. | Add | Implement or retain this test/contract gate for accepted core capabilities. | The V1 audit could not execute tests or prove coverage. |
| V2-TEST-REQ-133 | Import-safety tests must verify importing `app.services.utils` does not import pandas, cryptography, dotenv, notification clients, pub/sub clients, Prometheus exporters, broker SDKs, or network clients. | Defer | Add this test with the corresponding deferred production capability. | Testing a capability not accepted for the initial rebuild would create speculative architecture. |
| V2-TEST-REQ-134 | Import-safety tests must verify fake notification and Event Bus adapters do not require external credentials. | Defer | Add this test with the corresponding deferred production capability. | Testing a capability not accepted for the initial rebuild would create speculative architecture. |
| V2-TEST-REQ-135 | Import-safety tests must verify production adapter classes lazy-load dependencies only when used. | Add | Implement or retain this test/contract gate for accepted core capabilities. | The V1 audit could not execute tests or prove coverage. |
| V2-TEST-REQ-136 | Import-safety tests must verify missing optional dependencies fail with deterministic configuration errors only when the dependent feature is called. | Add | Implement or retain this test/contract gate for accepted core capabilities. | The V1 audit could not execute tests or prove coverage. |
| V2-TEST-REQ-137 | Usage-example tests must execute every usage example as documentation. | Add | Implement or retain this test/contract gate for accepted core capabilities. | The V1 audit could not execute tests or prove coverage. |
| V2-TEST-REQ-138 | Usage-example tests must cover one success and one failure example for each official AI tool. | Add | Implement or retain this test/contract gate for accepted core capabilities. | The V1 audit could not execute tests or prove coverage. |
| V2-TEST-REQ-139 | Usage-example tests must verify examples avoid production-disallowed `print()` unless explicitly labeled illustrative. | Add | Implement or retain this test/contract gate for accepted core capabilities. | The V1 audit could not execute tests or prove coverage. |
| V2-TEST-REQ-140 | Usage-example tests must verify examples show expected output shapes, not only invocation. | Add | Implement or retain this test/contract gate for accepted core capabilities. | The V1 audit could not execute tests or prove coverage. |
| V2-TEST-REQ-141 | Documentation review must verify every requirement has at least one mapped test, documented exception, or future-work classification. | Add | Implement or retain this test/contract gate for accepted core capabilities. | The V1 audit could not execute tests or prove coverage. |
| V2-TEST-REQ-142 | Documentation review must verify every Future Improvement is optional and not required for baseline production readiness. | Add | Implement or retain this test/contract gate for accepted core capabilities. | The V1 audit could not execute tests or prove coverage. |
| V2-TEST-REQ-143 | Documentation review must verify every Open Question is either non-blocking or resolved before Builder handoff. | Add | Implement or retain this test/contract gate for accepted core capabilities. | The V1 audit could not execute tests or prove coverage. |
| V2-TEST-REQ-144 | A concurrency stress test suite must exist outside the fast unit-test path. | Add | Implement or retain this test/contract gate for accepted core capabilities. | The V1 audit could not execute tests or prove coverage. |
| V2-TEST-REQ-145 | A chaos-test profile must cover notification provider failures, pub/sub adapter outages, sink timeout injection, circuit-breaker open/half-open transitions, queue saturation, and dropped-event accounting. | Defer | Add this test with the corresponding deferred production capability. | Testing a capability not accepted for the initial rebuild would create speculative architecture. |
| V2-TEST-REQ-146 | CI must pass Black, isort, Flake8, mypy, pytest, and the coverage gate. | Open Decision | Use the repository-approved quality toolchain and coverage gate once the system-wide CI standard is confirmed. | The V1 audit did not establish the authoritative repository-wide toolchain. |


#### 8.1 Builder Handoff Checklist


| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
| --- | --- | --- | --- | --- |
| V2-ACC-HANDOFF-001 | The implementation slice lists each included requirement as `Core Required`, `Production Required`, `Optional Adapter`, or `Future Improvement`. | Keep | Use this as a gating rule for each approved implementation slice. | It prevents unresolved or out-of-scope work from entering Builder execution. |
| V2-ACC-HANDOFF-002 | Every included public capability has a contract entry. | Keep | Use this as a gating rule for each approved implementation slice. | It prevents unresolved or out-of-scope work from entering Builder execution. |
| V2-ACC-HANDOFF-003 | Every included official AI tool has success and error envelope examples. | Keep | Use this as a gating rule for each approved implementation slice. | It prevents unresolved or out-of-scope work from entering Builder execution. |
| V2-ACC-HANDOFF-004 | Every included support helper has native return/raise behavior documented. | Keep | Use this as a gating rule for each approved implementation slice. | It prevents unresolved or out-of-scope work from entering Builder execution. |
| V2-ACC-HANDOFF-005 | Native helper names do not collide with official AI tool wrapper names. | Keep | Use this as a gating rule for each approved implementation slice. | It prevents unresolved or out-of-scope work from entering Builder execution. |
| V2-ACC-HANDOFF-006 | Redaction wrapper/helper behavior is resolved before implementation. | Keep | Use this as a gating rule for each approved implementation slice. | It prevents unresolved or out-of-scope work from entering Builder execution. |
| V2-ACC-HANDOFF-007 | Agent-safe input modes are resolved before agent attachment. | Open Decision | Select approved agent input modes before attachment; keep native dataframe support separate from agent-safe inputs. | The V2 document explicitly leaves this unresolved. |
| V2-ACC-HANDOFF-008 | Optional external adapters are explicitly approved before implementation. | Keep | Use this as a gating rule for each approved implementation slice. | It prevents unresolved or out-of-scope work from entering Builder execution. |
| V2-ACC-HANDOFF-009 | Benchmark profile and thresholds are approved before production acceptance. | Keep | Use this as a gating rule for each approved implementation slice. | It prevents unresolved or out-of-scope work from entering Builder execution. |
| V2-ACC-HANDOFF-010 | All blocking open questions for the implementation slice are resolved. | Keep | Use this as a gating rule for each approved implementation slice. | It prevents unresolved or out-of-scope work from entering Builder execution. |
| V2-ACC-HANDOFF-011 | No live trading, broker mutation, real notification send, dependency change, or production data mutation is included unless separately approved. | Keep | Use this as a gating rule for each approved implementation slice. | It prevents unresolved or out-of-scope work from entering Builder execution. |


#### Known Limitations


| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
| --- | --- | --- | --- | --- |
| V2-ACC-LIMIT-001 | This document does not approve live trading, live broker calls, production data mutation, or real notification sends. | Keep | Carry this exclusion or limitation into the final domain handoff. | It prevents scope expansion. |
| V2-ACC-LIMIT-002 | This document does not approve new dependencies; dependency changes require separate approval and manifest/lockfile updates. | Keep | Carry this exclusion or limitation into the final domain handoff. | It prevents scope expansion. |
| V2-ACC-LIMIT-003 | This document does not define numeric trading risk thresholds. | Keep | Carry this exclusion or limitation into the final domain handoff. | It prevents scope expansion. |
| V2-ACC-LIMIT-004 | This document does not make old HaruQuant implementation files authoritative for Sprint 001. | Keep | Carry this exclusion or limitation into the final domain handoff. | It prevents scope expansion. |
| V2-ACC-LIMIT-005 | This document does not require production external Event Bus or notification adapters in the first core implementation slice. | Keep | Carry this exclusion or limitation into the final domain handoff. | It prevents scope expansion. |
| V2-ACC-LIMIT-006 | This document does not require version-controlled Grafana dashboard JSON unless a production observability ticket explicitly includes it. | Keep | Carry this exclusion or limitation into the final domain handoff. | It prevents scope expansion. |
| V2-ACC-LIMIT-007 | Benchmark thresholds are required before production acceptance, but exact threshold values remain pending. | Open Decision | Approve thresholds before production acceptance. | The document explicitly leaves them pending. |


#### Implementation Priority Order


| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
| --- | --- | --- | --- | --- |
| V2-ACC-ORDER-001 | Implement `tools/__init__.py` first to establish a clean side-effect-free package. | Open Decision | Resolve the authoritative package root (`app.services.utils` versus `tools.utils`) at system alignment before implementation. | The V2 document prescribes both package locations. |
| V2-ACC-ORDER-002 | Implement `app/services/utils/logger.py` before modules that need production logging. | Modify | Use dependency order only within the approved core capability slice; do not pre-create the entire proposed tree. | The final structure must follow reconciliation decisions, not the original file list. |
| V2-ACC-ORDER-003 | Implement `app/services/utils/standard.py` before official AI tools. | Modify | Use dependency order only within the approved core capability slice; do not pre-create the entire proposed tree. | The final structure must follow reconciliation decisions, not the original file list. |
| V2-ACC-ORDER-004 | Implement `app/services/utils/errors.py` before deterministic failure behavior is needed. | Modify | Use dependency order only within the approved core capability slice; do not pre-create the entire proposed tree. | The final structure must follow reconciliation decisions, not the original file list. |
| V2-ACC-ORDER-005 | Implement `app/services/utils/identity.py` before request/workflow/event trace helpers are needed. | Modify | Use dependency order only within the approved core capability slice; do not pre-create the entire proposed tree. | The final structure must follow reconciliation decisions, not the original file list. |
| V2-ACC-ORDER-006 | Implement `app/services/utils/normalization.py` before data quality, settings, freshness checks, and event timestamp validation. | Modify | Use dependency order only within the approved core capability slice; do not pre-create the entire proposed tree. | The final structure must follow reconciliation decisions, not the original file list. |
| V2-ACC-ORDER-007 | Implement `app/services/utils/paths.py` before settings and artifact helpers. | Modify | Use dependency order only within the approved core capability slice; do not pre-create the entire proposed tree. | The final structure must follow reconciliation decisions, not the original file list. |
| V2-ACC-ORDER-008 | Implement `app/services/utils/security.py` before logging, settings, events, notifications, and audit-safe behavior are finalized. | Modify | Use dependency order only within the approved core capability slice; do not pre-create the entire proposed tree. | The final structure must follow reconciliation decisions, not the original file list. |
| V2-ACC-ORDER-009 | Implement `app/services/utils/settings.py` before adapters and runtime configuration consumers. | Modify | Use dependency order only within the approved core capability slice; do not pre-create the entire proposed tree. | The final structure must follow reconciliation decisions, not the original file list. |
| V2-ACC-ORDER-010 | Implement `app/services/utils/auth.py` before tool allowlists and side-effect permission checks. | Modify | Use dependency order only within the approved core capability slice; do not pre-create the entire proposed tree. | The final structure must follow reconciliation decisions, not the original file list. |
| V2-ACC-ORDER-011 | Implement `app/services/utils/event_bus.py` before error routing and notification routing. | Defer | Schedule only after the production capability is approved. | The capability is deferred. |
| V2-ACC-ORDER-012 | Implement `app/services/utils/error_routing.py` before notification routing. | Defer | Schedule only after the production capability is approved. | The capability is deferred. |
| V2-ACC-ORDER-013 | Implement `app/services/utils/notifications.py` before alert delivery is attached to workflows. | Defer | Schedule only after the production capability is approved. | The capability is deferred. |
| V2-ACC-ORDER-014 | Implement `app/services/utils/observability.py` before production health gates are accepted. | Defer | Schedule only after the production capability is approved. | The capability is deferred. |
| V2-ACC-ORDER-015 | Implement `app/services/utils/dataframe_tools.py` after normalization and errors. | Modify | Use dependency order only within the approved core capability slice; do not pre-create the entire proposed tree. | The final structure must follow reconciliation decisions, not the original file list. |
| V2-ACC-ORDER-016 | Implement `app/services/utils/schema_validation.py` after standard, errors, normalization, security, auth, and observability foundations. | Modify | Use dependency order only within the approved core capability slice; do not pre-create the entire proposed tree. | The final structure must follow reconciliation decisions, not the original file list. |
| V2-ACC-ORDER-017 | Implement `app/services/utils/data_quality.py` after standard, errors, normalization, dataframe tools, and schema validation. | Modify | Use dependency order only within the approved core capability slice; do not pre-create the entire proposed tree. | The final structure must follow reconciliation decisions, not the original file list. |
| V2-ACC-ORDER-018 | Implement `app/services/utils/__init__.py` only after modules exist and public names are finalized. | Modify | Use dependency order only within the approved core capability slice; do not pre-create the entire proposed tree. | The final structure must follow reconciliation decisions, not the original file list. |
| V2-ACC-ORDER-019 | Implement unit tests for every module. | Modify | Use dependency order only within the approved core capability slice; do not pre-create the entire proposed tree. | The final structure must follow reconciliation decisions, not the original file list. |
| V2-ACC-ORDER-020 | Implement usage examples for official AI tools and production primitives. | Modify | Use dependency order only within the approved core capability slice; do not pre-create the entire proposed tree. | The final structure must follow reconciliation decisions, not the original file list. |
| V2-ACC-ORDER-021 | Run CI quality gates before accepting the implementation. | Modify | Run the repository-approved gates for every accepted slice. | Exact tools remain a system-level decision. |


#### Definition of Done


| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
| --- | --- | --- | --- | --- |
| V2-ACC-DOD-001 | The target folder structure exists. | Modify | Require only the reconciled minimal capability structure, not the entire proposed V2 tree. | The original tree includes deferred capabilities. |
| V2-ACC-DOD-002 | `tools/__init__.py` exists and is side-effect free. | Open Decision | Resolve the authoritative package root (`app.services.utils` versus `tools.utils`) at system alignment before implementation. | The V2 document prescribes both package locations. |
| V2-ACC-DOD-003 | `app/services/utils/__init__.py` exposes only approved public names. | Modify | Apply this acceptance condition to the approved core scope and its explicit public contracts. | V1 behavior must be consolidated and revalidated. |
| V2-ACC-DOD-004 | Public registry documentation classifies every official AI tool and support helper. | Modify | Apply this acceptance condition to the approved core scope and its explicit public contracts. | V1 behavior must be consolidated and revalidated. |
| V2-ACC-DOD-005 | Internal helpers are not accidentally exported. | Modify | Apply this acceptance condition to the approved core scope and its explicit public contracts. | V1 behavior must be consolidated and revalidated. |
| V2-ACC-DOD-006 | No compatibility shims, aliases, fallback import modules, or duplicate wrapper modules exist. | Modify | Apply this acceptance condition to the approved core scope and its explicit public contracts. | V1 behavior must be consolidated and revalidated. |
| V2-ACC-DOD-007 | Every Python file has a file-level docstring. | Modify | Apply this acceptance condition to the approved core scope and its explicit public contracts. | V1 behavior must be consolidated and revalidated. |
| V2-ACC-DOD-008 | Every public function/class has a useful docstring. | Modify | Apply this acceptance condition to the approved core scope and its explicit public contracts. | V1 behavior must be consolidated and revalidated. |
| V2-ACC-DOD-009 | Public functions and methods are typed. | Modify | Apply this acceptance condition to the approved core scope and its explicit public contracts. | V1 behavior must be consolidated and revalidated. |
| V2-ACC-DOD-010 | Inputs are validated where appropriate. | Modify | Apply this acceptance condition to the approved core scope and its explicit public contracts. | V1 behavior must be consolidated and revalidated. |
| V2-ACC-DOD-011 | Errors are explicit and deterministic. | Modify | Apply this acceptance condition to the approved core scope and its explicit public contracts. | V1 behavior must be consolidated and revalidated. |
| V2-ACC-DOD-012 | Official tools return standard envelopes. | Modify | Apply this acceptance condition to the approved core scope and its explicit public contracts. | V1 behavior must be consolidated and revalidated. |
| V2-ACC-DOD-013 | Support helpers return clear native values or raise typed exceptions. | Modify | Apply this acceptance condition to the approved core scope and its explicit public contracts. | V1 behavior must be consolidated and revalidated. |
| V2-ACC-DOD-014 | No production `print()` calls exist. | Modify | Apply this acceptance condition to the approved core scope and its explicit public contracts. | V1 behavior must be consolidated and revalidated. |
| V2-ACC-DOD-015 | No secrets are logged. | Modify | Apply this acceptance condition to the approved core scope and its explicit public contracts. | V1 behavior must be consolidated and revalidated. |
| V2-ACC-DOD-016 | File logging is explicit, safely scoped, rotating, and retention-limited when enabled. | Modify | Apply this acceptance condition to the approved core scope and its explicit public contracts. | V1 behavior must be consolidated and revalidated. |
| V2-ACC-DOD-017 | Local development logging supports colorized human-readable console output in the approved format. | Modify | Apply this acceptance condition to the approved core scope and its explicit public contracts. | V1 behavior must be consolidated and revalidated. |
| V2-ACC-DOD-018 | Official tools include metadata constants. | Modify | Apply this acceptance condition to the approved core scope and its explicit public contracts. | V1 behavior must be consolidated and revalidated. |
| V2-ACC-DOD-019 | Official tools include side-effect flags. | Modify | Apply this acceptance condition to the approved core scope and its explicit public contracts. | V1 behavior must be consolidated and revalidated. |
| V2-ACC-DOD-020 | Official tools accept `request_id`. | Modify | Apply this acceptance condition to the approved core scope and its explicit public contracts. | V1 behavior must be consolidated and revalidated. |
| V2-ACC-DOD-021 | Official tools include `execution_ms`. | Modify | Apply this acceptance condition to the approved core scope and its explicit public contracts. | V1 behavior must be consolidated and revalidated. |
| V2-ACC-DOD-022 | Official tools use deterministic error codes. | Modify | Apply this acceptance condition to the approved core scope and its explicit public contracts. | V1 behavior must be consolidated and revalidated. |
| V2-ACC-DOD-023 | Official tools pass `validate_tool_response_schema`. | Modify | Apply this acceptance condition to the approved core scope and its explicit public contracts. | V1 behavior must be consolidated and revalidated. |
| V2-ACC-DOD-024 | Importing `app.services.utils` does not import pandas, cryptography, dotenv, broker SDKs, notification clients, pub/sub clients, Prometheus exporters, or network clients unless the specific feature is used. | Defer | Move this acceptance condition to the deferred production capability. | It should not block the core rebuild. |
| V2-ACC-DOD-025 | Dataframe helpers use lazy pandas imports or `TYPE_CHECKING` guards. | Modify | Apply this acceptance condition to the approved core scope and its explicit public contracts. | V1 behavior must be consolidated and revalidated. |
| V2-ACC-DOD-026 | Missing pandas fails only when dataframe helpers are called, with a clear configuration/dependency error. | Modify | Apply this acceptance condition to the approved core scope and its explicit public contracts. | V1 behavior must be consolidated and revalidated. |
| V2-ACC-DOD-027 | `validate_ohlcv_quality` is stateless, diagnostic-only, and does not repair, resample, persist, enrich, or mutate input data. | Modify | Apply this acceptance condition to the approved core scope and its explicit public contracts. | V1 behavior must be consolidated and revalidated. |
| V2-ACC-DOD-028 | Data repair and cleaning workflows are explicitly excluded from `app.services.utils` and reserved for `app.services.data`. | Modify | Apply this acceptance condition to the approved core scope and its explicit public contracts. | V1 behavior must be consolidated and revalidated. |
| V2-ACC-DOD-029 | Validators accept supported enum values and strings where practical, then normalize to canonical JSON-safe strings. | Modify | Apply this acceptance condition to the approved core scope and its explicit public contracts. | V1 behavior must be consolidated and revalidated. |
| V2-ACC-DOD-030 | Public responses, metadata, audit records, logs, and serialized payloads never expose enum objects directly. | Modify | Apply this acceptance condition to the approved core scope and its explicit public contracts. | V1 behavior must be consolidated and revalidated. |
| V2-ACC-DOD-031 | Future domain-specific errors inherit from `Error` or expose a compatible `code` attribute. | Modify | Apply this acceptance condition to the approved core scope and its explicit public contracts. | V1 behavior must be consolidated and revalidated. |
| V2-ACC-DOD-032 | Standard response builders can map `Error` subclasses generically without hardcoding every future domain error. | Modify | Apply this acceptance condition to the approved core scope and its explicit public contracts. | V1 behavior must be consolidated and revalidated. |
| V2-ACC-DOD-033 | Auth helpers deny by default and enforce tool allowlists. | Modify | Apply this acceptance condition to the approved core scope and its explicit public contracts. | V1 behavior must be consolidated and revalidated. |
| V2-ACC-DOD-034 | Event Bus idempotency storage is bounded by TTL and maximum cache size. | Defer | Move this acceptance condition to the deferred production capability. | It should not block the core rebuild. |
| V2-ACC-DOD-035 | Event Bus idempotency storage uses compact metadata rather than full event payloads by default. | Defer | Move this acceptance condition to the deferred production capability. | It should not block the core rebuild. |
| V2-ACC-DOD-036 | Event Bus queue policies are explicit and production critical workflows default to fail-fast behavior. | Defer | Move this acceptance condition to the deferred production capability. | It should not block the core rebuild. |
| V2-ACC-DOD-037 | Event Bus publish, subscribe, unsubscribe, retry, and dead-letter paths document exact concurrency guarantees as `thread-safe`, `async-safe`, `both`, or `not concurrent-safe`. | Defer | Move this acceptance condition to the deferred production capability. | It should not block the core rebuild. |
| V2-ACC-DOD-038 | Notification routing, throttling, deduplication, and circuit-breaker state document exact concurrency guarantees as `thread-safe`, `async-safe`, `both`, or `not concurrent-safe`. | Defer | Move this acceptance condition to the deferred production capability. | It should not block the core rebuild. |
| V2-ACC-DOD-039 | Queue-full publishing returns deterministic `QUEUE_FULL` or `BACKPRESSURE_EXCEEDED` diagnostics. | Defer | Move this acceptance condition to the deferred production capability. | It should not block the core rebuild. |
| V2-ACC-DOD-040 | External notification adapters have circuit breakers. | Defer | Move this acceptance condition to the deferred production capability. | It should not block the core rebuild. |
| V2-ACC-DOD-041 | External pub/sub adapters have circuit breakers. | Modify | Apply this acceptance condition to the approved core scope and its explicit public contracts. | V1 behavior must be consolidated and revalidated. |
| V2-ACC-DOD-042 | Prometheus-compatible metrics include circuit-breaker state, queue depth, idempotency cache size, backpressure count, notification failures, and clock drift. | Defer | Move this acceptance condition to the deferred production capability. | It should not block the core rebuild. |
| V2-ACC-DOD-043 | Health checks include clock-drift monitoring or explicit no-op status. | Defer | Move this acceptance condition to the deferred production capability. | It should not block the core rebuild. |
| V2-ACC-DOD-044 | Schema validation errors include deterministic invalid-field paths. | Modify | Apply this acceptance condition to the approved core scope and its explicit public contracts. | V1 behavior must be consolidated and revalidated. |
| V2-ACC-DOD-045 | Official schema validation errors include bounded `invalid_fields` diagnostics where practical. | Modify | Apply this acceptance condition to the approved core scope and its explicit public contracts. | V1 behavior must be consolidated and revalidated. |
| V2-ACC-DOD-046 | Schema validation resource limits prevent unbounded CPU, memory, and response sizes. | Modify | Apply this acceptance condition to the approved core scope and its explicit public contracts. | V1 behavior must be consolidated and revalidated. |
| V2-ACC-DOD-047 | Redaction denylist and audited allowlist behavior is implemented and tested. | Modify | Apply this acceptance condition to the approved core scope and its explicit public contracts. | V1 behavior must be consolidated and revalidated. |
| V2-ACC-DOD-048 | Notification templates support markdown and plain-text fallback rendering. | Defer | Move this acceptance condition to the deferred production capability. | It should not block the core rebuild. |
| V2-ACC-DOD-049 | Notification templates render from sanitized data transfer objects rather than raw event payloads. | Defer | Move this acceptance condition to the deferred production capability. | It should not block the core rebuild. |
| V2-ACC-DOD-050 | Tests prove no sensitive values leak through logs, events, notifications, metrics, dead-letter diagnostics, schema errors, or health checks. | Defer | Move this acceptance condition to the deferred production capability. | It should not block the core rebuild. |
| V2-ACC-DOD-051 | Unit tests exist for every module. | Modify | Apply this acceptance condition to the approved core scope and its explicit public contracts. | V1 behavior must be consolidated and revalidated. |
| V2-ACC-DOD-052 | Official tools have schema compliance tests. | Modify | Apply this acceptance condition to the approved core scope and its explicit public contracts. | V1 behavior must be consolidated and revalidated. |
| V2-ACC-DOD-053 | Official tools have metadata tests. | Modify | Apply this acceptance condition to the approved core scope and its explicit public contracts. | V1 behavior must be consolidated and revalidated. |
| V2-ACC-DOD-054 | Invalid input tests exist. | Modify | Apply this acceptance condition to the approved core scope and its explicit public contracts. | V1 behavior must be consolidated and revalidated. |
| V2-ACC-DOD-055 | Edge case tests exist. | Modify | Apply this acceptance condition to the approved core scope and its explicit public contracts. | V1 behavior must be consolidated and revalidated. |
| V2-ACC-DOD-056 | Security tests verify redaction and no secret leakage. | Modify | Apply this acceptance condition to the approved core scope and its explicit public contracts. | V1 behavior must be consolidated and revalidated. |
| V2-ACC-DOD-057 | Data-quality tests cover realistic OHLCV defects. | Modify | Apply this acceptance condition to the approved core scope and its explicit public contracts. | V1 behavior must be consolidated and revalidated. |
| V2-ACC-DOD-058 | Coverage is at least 80%. | Modify | Apply this acceptance condition to the approved core scope and its explicit public contracts. | V1 behavior must be consolidated and revalidated. |
| V2-ACC-DOD-059 | Usage examples exist for official AI tools. | Modify | Apply this acceptance condition to the approved core scope and its explicit public contracts. | V1 behavior must be consolidated and revalidated. |
| V2-ACC-DOD-060 | Usage examples use realistic inputs. | Modify | Apply this acceptance condition to the approved core scope and its explicit public contracts. | V1 behavior must be consolidated and revalidated. |
| V2-ACC-DOD-061 | Usage examples show success and error handling. | Modify | Apply this acceptance condition to the approved core scope and its explicit public contracts. | V1 behavior must be consolidated and revalidated. |
| V2-ACC-DOD-062 | Usage examples use `request_id` where applicable. | Modify | Apply this acceptance condition to the approved core scope and its explicit public contracts. | V1 behavior must be consolidated and revalidated. |
| V2-ACC-DOD-063 | Usage examples avoid `print()` unless explicitly labeled as illustrative non-production snippets. | Modify | Apply this acceptance condition to the approved core scope and its explicit public contracts. | V1 behavior must be consolidated and revalidated. |
| V2-ACC-DOD-064 | Black passes. | Open Decision | Use the authoritative repository-wide quality toolchain. | The toolchain is not established by the source documents. |
| V2-ACC-DOD-065 | isort passes. | Open Decision | Use the authoritative repository-wide quality toolchain. | The toolchain is not established by the source documents. |
| V2-ACC-DOD-066 | Flake8 passes. | Open Decision | Use the authoritative repository-wide quality toolchain. | The toolchain is not established by the source documents. |
| V2-ACC-DOD-067 | mypy passes. | Modify | Apply this acceptance condition to the approved core scope and its explicit public contracts. | V1 behavior must be consolidated and revalidated. |
| V2-ACC-DOD-068 | pytest passes. | Modify | Apply this acceptance condition to the approved core scope and its explicit public contracts. | V1 behavior must be consolidated and revalidated. |
| V2-ACC-DOD-069 | Coverage gate passes. | Modify | Apply this acceptance condition to the approved core scope and its explicit public contracts. | V1 behavior must be consolidated and revalidated. |
| V2-ACC-DOD-070 | Full-project quality gate passes. | Modify | Apply this acceptance condition to the approved core scope and its explicit public contracts. | V1 behavior must be consolidated and revalidated. |
| V2-ACC-DOD-071 | Documentation covers Event Bus backpressure, idempotency, circuit breakers, clock drift, schema field paths, and redaction allowlist governance. | Defer | Move this acceptance condition to the deferred production capability. | It should not block the core rebuild. |
| V2-ACC-DOD-072 | Documentation includes production readiness checklists, operational runbooks, dashboard review checklists, and compatibility review notes. | Modify | Apply this acceptance condition to the approved core scope and its explicit public contracts. | V1 behavior must be consolidated and revalidated. |
| V2-ACC-DOD-073 | No unresolved open questions remain for the baseline production-ready utils module. | Modify | Apply this acceptance condition to the approved core scope and its explicit public contracts. | V1 behavior must be consolidated and revalidated. |


#### Future Improvements


| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
| --- | --- | --- | --- | --- |
| V2-FUTURE-001 | Production external Event Bus broker adapters may be added after adapter ownership and dependencies are approved. | Defer | Track as future work outside the initial rebuild and require explicit approval before implementation. | The V2 document already classifies it as future improvement. |
| V2-FUTURE-002 | Real provider delivery clients for email, Telegram, and desktop notifications may be added after provider ownership and dependencies are approved. | Defer | Track as future work outside the initial rebuild and require explicit approval before implementation. | The V2 document already classifies it as future improvement. |
| V2-FUTURE-003 | Version-controlled Grafana dashboard JSON may be added after observability artifact ownership is approved. | Defer | Track as future work outside the initial rebuild and require explicit approval before implementation. | The V2 document already classifies it as future improvement. |
| V2-FUTURE-004 | Clock-drift monitoring may integrate with a real offset source after the runtime environment and dependency policy are approved. | Defer | Track as future work outside the initial rebuild and require explicit approval before implementation. | The V2 document already classifies it as future improvement. |
| V2-FUTURE-005 | Property-based or mutation tests may be added for redaction, path normalization, schema validation, and event-envelope validation. | Defer | Track as future work outside the initial rebuild and require explicit approval before implementation. | The V2 document already classifies it as future improvement. |
| V2-FUTURE-006 | Chaos-test profiles may expand once external provider adapters exist. | Defer | Track as future work outside the initial rebuild and require explicit approval before implementation. | The V2 document already classifies it as future improvement. |

## 7. Workflow Reconciliation


| Final workflow ID | Workflow | Scope | V1 status | V2 proposal | Decision | Final boundary and outcome |
| --- | --- | --- | --- | --- | --- | --- |
| WF-UTL-001 | Structured logging and redaction | Cross-domain | Working | Explicit import-safe logging lifecycle | Modify | Caller log event → utils validates/redacts/formats → configured sinks or bounded fallback; no import-time files. |
| WF-UTL-002 | Credential hashing and verification | Cross-domain | Working | Argon2id-first restricted security helpers | Modify | Plain credential/hash boundary → native security helper → hash/boolean or typed error; no agent exposure. |
| WF-UTL-003 | CSV dataframe cache | Cross-domain | Working | No V2 Utils cache requirement | Replace | Data request → Data-owned bounded cache → DataFrame; Utils provides no global dataframe cache. |
| WF-UTL-004 | Standard tool response construction | Cross-domain | Working | One official-tool contract | Modify | Native result/error → canonical metadata and envelope → validated response returned to agent/workflow. |
| WF-UTL-005 | Safe configuration path resolution | Internal/Cross-domain | Working | Single `Path` API and explicit settings load | Preserve | Raw configured path → utils normalization/traversal check → safe `Path`; directory creation only by explicit helper. |
| WF-UTL-006 | Shared settings bootstrap | Cross-domain | Working | Immutable explicit settings load and injection | Modify | Explicit mapping/environment/.env/defaults → validation and path normalization → immutable settings object. |
| WF-UTL-007 | Risk/packet validation | Cross-domain | Partial | Canonical schema/contract validators | Replace | JSON-safe payload + policy → native bounded validation → optional official tool envelope; domain decides action. |
| WF-UTL-008 | Local event publication | Internal | Partial/test-only | Large bounded Event Bus proposal | Defer | No initial workflow. Later: sanitized event → bounded in-process bus → ordered handlers/diagnostics. |
| WF-UTL-009 | OHLCV quality inspection | Cross-domain | Isolated | One diagnostic validator and official wrapper | Modify | Caller-owned data + symbol/timeframe → read-only bounded checks → score/issues/summary envelope. |
| WF-UTL-010 | Official tool authorization | Cross-domain | Missing integration | Deny-by-default tool allowlist | Add | Validated auth context + tool contract → role/permission/scope/allowlist check → allow decision or deterministic denial. |
| WF-UTL-011 | Error routing and notification delivery | Cross-domain | Missing/fragmented | Full routing, deduplication and providers | Defer | Core returns sanitized error event only; routing boundary remains unresolved until a later production slice. |
| WF-UTL-012 | Metrics, health and circuit protection | Cross-domain | Test-only/disconnected | Prometheus/Grafana/health/circuit stack | Defer | No initial workflow; implement only with approved exporters/providers, limits and benchmarks. |
| WF-UTL-013 | Public symbol registration | Internal | Defective | Strict classified registry | Add | Approved contract entry → registry export → import/contract test; missing target fails immediately. |


### `WF-UTL-001` — Structured Logging and Redaction

**Scope:** Cross-domain

**V1 behaviour:**

```text
Application/domain caller
→ logger method with structured context
→ V1 adapter redacts text/mapping
→ structlog/std logging
→ import-created file/callback/queue sinks
```

**V2 proposal:**

```text
Import-safe logger object
→ explicit `configure_logging(settings)`
→ structured JSON or human console renderer
→ optional safe rotating file sink
→ bounded fallback diagnostics
```

**Final decision:**

```text
Modify. Preserve the public logger/get_logger behavior and redaction, but remove import-time configuration, unconditional file creation, and silent sink failure.
```

**Reason:**

V1-WF-UTILS-001 is a proven cross-domain workflow; the defect is lifecycle and failure visibility, not the need for logging.



### `WF-UTL-002` — Credential Hashing and Verification

**Scope:** Cross-domain

**V1 behaviour:**

```text
User registration/update → `hash_password()` → database hash
Login → stored hash + password → `verify_password()` → authentication decision
```

**V2 proposal:**

```text
Restricted native password helpers
→ Argon2id when configured
→ deterministic configuration failure when unavailable
→ no agent attachment
```

**Final decision:**

```text
Modify, not replace. Preserve callers and native return shapes while removing silent algorithm fallback.
```

**Reason:**

V1-WF-UTILS-002 is one of the clearest production workflows.



### `WF-UTL-003` — CSV Dataframe Cache

**Scope:** Cross-domain

**V1 behaviour:**

```text
Data CSV loader → `common.get_cached_dataframe()` → module-global cache → DataFrame
```

**V2 proposal:**

```text
Data domain owns any cache and its lifecycle.
Utils may provide pure serialization/comparison helpers only.
```

**Final decision:**

```text
Replace the cross-domain workflow and remove the cache from Utils after Data migration.
```

**Reason:**

The cache is proven useful but violates the V2 utility boundary and mutable-state rules.



### `WF-UTL-004` — Standard Tool Response Construction

**Scope:** Cross-domain

**V1 behaviour:**

```text
Tool execution → one of two V1 response-builder styles → dictionary envelope
```

**V2 proposal:**

```text
Native implementation result
→ one metadata/timing builder
→ one success/error envelope builder
→ one schema validator
```

**Final decision:**

```text
Modify and merge. Preserve envelope behavior, remove the parallel loose builder.
```

**Reason:**

V1-WF-UTILS-004 is valuable, while contract duplication is a confirmed defect.



### `WF-UTL-005` — Safe Configuration Path Resolution

**Scope:** Internal/Cross-domain

**V1 behaviour:**

```text
Settings/storage input → `paths.normalize_path()` → safe Path
Explicit `ensure_*` → directory creation
```

**V2 proposal:**

```text
Same boundary, with one canonical `Path`-returning API and no normalization-side effects.
```

**Final decision:**

```text
Preserve and consolidate.
```

**Reason:**

V1-WF-UTILS-005 already matches the smallest safe behavior.



### `WF-UTL-006` — Shared Settings Bootstrap

**Scope:** Cross-domain

**V1 behaviour:**

```text
First singleton access → environment/.env read → broad Settings model → cached process state
```

**V2 proposal:**

```text
Explicit load call
→ precedence: explicit mapping, environment, optional `.env`, defaults
→ immutable generic settings
→ optional injection into caller-owned target
```

**Final decision:**

```text
Modify. Remove import/lazy magic, live/research fields, and missing advertised aliases.
```

**Reason:**

V1-WF-UTILS-006 is used, but V1 settings mix domains and source behavior.



### `WF-UTL-007` — Schema and Packet Validation

**Scope:** Cross-domain

**V1 behaviour:**

```text
Payload → one of several overlapping validators → mixed native/envelope output
```

**V2 proposal:**

```text
JSON-safe payload + schema/policy + limits
→ canonical native validation result with bounded field paths
→ explicit official wrapper where agent-callable
```

**Final decision:**

```text
Replace the duplicate implementations with one engine and focused wrappers.
```

**Reason:**

V1-WF-UTILS-007 is partial and inconsistent; V2 adds valid bounded-contract requirements.



### `WF-UTL-008` — In-Process Event Publication

**Scope:** Internal

**V1 behaviour:**

```text
Event builder → append-only queue → synchronous handlers → post-hoc timeout/result
```

**V2 proposal:**

```text
Later production slice only:
sanitized serializable event → bounded idempotency/queue policy → ordered isolated handlers → diagnostics
```

**Final decision:**

```text
Defer and replace rather than preserving V1 structure.
```

**Reason:**

V1-WF-UTILS-008 has no confirmed production caller and the current queue/idempotency lifecycle is unsafe.



### `WF-UTL-009` — OHLCV Data Quality Inspection

**Scope:** Cross-domain

**V1 behaviour:**

```text
DataFrame → one of three validators → inconsistent issue/report shapes
```

**V2 proposal:**

```text
Caller-owned dataframe or approved agent-safe input
→ non-mutating diagnostic checks
→ bounded deterministic profile, score, issues and remediation
→ optional official envelope
```

**Final decision:**

```text
Modify and merge.
```

**Reason:**

V1-WF-UTILS-009 demonstrates useful behavior, but production gating and agent input modes remain unresolved.



### `WF-UTL-010` — Official Tool Authorization

**Scope:** Cross-domain

**V1 behaviour:**

```text
V1 auth helpers exist only in tests/examples; production API uses separate token/session authentication.
```

**V2 proposal:**

```text
Validated internal auth context + requested official tool
→ deny-by-default role/permission/scope/tool-allowlist check
→ native allow/deny result
→ official boundary returns deterministic error envelope
```

**Final decision:**

```text
Add the integration while keeping external identity verification outside Utils.
```

**Reason:**

The V2 safety requirement is valid even though V1 has no end-to-end caller.



### `WF-UTL-011` — Error Routing and Notifications

**Scope:** Cross-domain

**V1 behaviour:**

```text
V1 provides error mapping/dedup fragments; notification examples call a separate notification package.
```

**V2 proposal:**

```text
Proposed: error event → rules/dedup/throttle → Event Bus → channel templates/adapters → metrics
```

**Final decision:**

```text
Defer active routing and providers. Core may build a sanitized error event only.
```

**Reason:**

The proposal crosses domain/infrastructure boundaries and lacks a confirmed runtime workflow.



### `WF-UTL-012` — Metrics, Health and Circuit Protection

**Scope:** Cross-domain

**V1 behaviour:**

```text
Caller-owned in-memory registry, health snapshot and breaker; tests/examples only.
```

**V2 proposal:**

```text
Proposed: broad Prometheus metrics, Grafana expectations, clock drift and provider circuit breakers.
```

**Final decision:**

```text
Defer. Preserve requirements as production-slice constraints, not core implementation.
```

**Reason:**

V1 is disconnected and V2 acceptance thresholds/exporter ownership are unresolved.



### `WF-UTL-013` — Public Symbol Registration

**Scope:** Internal

**V1 behaviour:**

```text
Name in `_EXPORTS` → lazy import → missing attribute returns whole module.
```

**V2 proposal:**

```text
Approved contract entry → explicit registry name/target/classification → import and schema checks → fail-fast on mismatch.
```

**Final decision:**

```text
Add as a formal internal workflow and modify V1 facade.
```

**Reason:**

This directly prevents the strongest confirmed V1 defect.


## 8. Recommended Minimal Capability Structure

The authoritative package root is unresolved. The structure below uses the current V1 path only as a neutral placeholder and shows capability folders, not a complete file tree.

```text
app/services/utils/
├── registry/          # Public registry, classifications, and contracts
├── logging/           # Structured import-safe logging
├── errors/            # Shared errors and generic mapping
├── responses/         # Standard tool envelopes and timing
├── identity/          # IDs, versions, and trace values
├── time/              # UTC clocks, timestamps, and freshness
├── paths/             # Safe paths and explicit directory creation
├── serialization/     # Canonical JSON
├── dataframes/        # Pure dataframe and sequence helpers
├── data_quality/      # Diagnostic OHLCV validation
├── validation/        # Schema and contract validation
├── security/          # Redaction, credentials, and restricted crypto
├── settings/          # Generic immutable runtime settings
├── auth/              # Internal auth context and tool allowlists
├── events/            # Deferred production capability
├── alerts/            # Deferred production capability
└── observability/     # Deferred production capability
```


| Module | Capability | Source | Main decision |
| --- | --- | --- | --- |
| registry | Public API registry and contracts | Both | Modify |
| logging | Structured, import-safe logging | Both | Modify |
| errors | Shared error model and mapping | Both | Split |
| responses | Standard tool envelopes and timing | Both | Merge |
| identity | IDs, versions and trace values | Both | Modify |
| time | UTC clocks, timestamps and freshness | Both | Split |
| paths | Safe paths and explicit directory creation | V1 | Merge |
| serialization | Canonical JSON | Both | Merge |
| dataframes | Pure dataframe/sequence helpers | Both | Merge |
| data_quality | Diagnostic OHLCV validation | Both | Merge |
| validation | Schema and contract validation | Both | Merge |
| security | Redaction, credentials and restricted crypto | Both | Modify |
| settings | Generic immutable runtime settings | Both | Split |
| auth | Internal auth context and tool allowlists | Both | Modify |
| events | Deferred in-process Event Bus | Both | Defer |
| alerts | Deferred error/notification routing | V2 | Defer |
| observability | Deferred metrics/health/circuit protection | Both | Defer |

## 9. Reuse and Migration Plan


| Priority | Existing V1 item | Migration action | Target capability | Validation required |
| --- | --- | --- | --- | --- |
| 1 | `__init__.py` registry | Refactor | CAP-UTL-001 | Every exported target exists; import is side-effect free; no module fallback. |
| 2 | `logger.py` core public API | Refactor | CAP-UTL-002 | Existing caller compatibility tests; no import-time file/handler creation; secret leakage tests. |
| 3 | `errors.py` shared base/mappers | Refactor and split | CAP-UTL-003 | Domain import migration; generic mapping tests; approved code registry. |
| 4 | `standard.py` response builders | Refactor and merge | CAP-UTL-004 | All official tools pass one contract and metadata suite. |
| 5 | `identity.py` and duplicate serializers | Refactor | CAP-UTL-005 / 008 | ID validation/uniqueness and canonical serialization tests. |
| 6 | `normalization.py` generic time helpers | Refactor and split | CAP-UTL-006 | Timezone, injected clock, freshness tests; domain policy owners confirmed. |
| 7 | `paths.py` | Reuse | CAP-UTL-007 | Traversal and explicit side-effect tests. |
| 8 | `common.py` dataframe cache | Remove/move | Data domain | CSV workflow regression and bounded Data-owned cache. |
| 9 | `common.py` + `dataframe_tools.py` | Refactor and merge | CAP-UTL-009 | Lazy pandas, no mutation, comparison and serialization tests. |
| 10 | three V1 OHLCV validators | Replace with merged implementation | CAP-UTL-010 | Approved scoring/profile contract and at least 15 defect cases. |
| 11 | schema validators in two files | Replace with merged engine | CAP-UTL-011 | Field-path, size/depth/issue limits and official wrapper tests. |
| 12 | security redaction/hash/crypto | Refactor | CAP-UTL-012 / 013 | No leakage, Argon2id policy, Fernet dependency, version conflict tests. |
| 13 | broad `settings.py` | Split and refactor | CAP-UTL-014 | Source precedence, immutable mapping load/injection; live/research migrations. |
| 14 | `auth.py` | Refactor | CAP-UTL-015 | Deny-by-default roles/permissions/scopes/tool allowlist tests. |
| 15 | `event_bus.py` | Defer; replace later | CAP-UTL-016 | Confirm no runtime caller before excluding from core. |
| 16 | `observability.py` and alert fragments | Defer | CAP-UTL-017 / 018 | Ownership, exporters/providers, benchmarks and real caller approved. |
| 17 | limits scattered across files | New consolidated profile | CAP-UTL-019 | Override bounds and contract tests. |

## 10. Simplifications from V2


| V2 proposal | Problem | Simplified final direction |
| --- | --- | --- |
| Flat `tools/utils` tree plus `app/services/utils` references | Conflicting package roots and pre-creates deferred files | Resolve package root, then create feature folders only for approved capabilities. |
| 195-name lazy registry | Large surface masks missing symbols | Strict explicit registry generated/validated from public contracts. |
| Two response-building styles | Different metadata and validation semantics | One envelope builder family and one validator. |
| Path APIs in normalization and paths | Duplicate names and incompatible returns | One native `Path` API. |
| Dataframe helpers in common and dataframe_tools | Duplicate logic plus heavy dynamic service discovery | One pure lazy dataframe capability; move cache to Data. |
| Three OHLCV validators | Different issue schemas and boundaries | One native engine plus one official wrapper. |
| Two schema-validation modules | Overlapping behavior and return shapes | One bounded engine plus focused wrappers. |
| Universal shared constants catalogue | Would centralize event/notification/health states prematurely | Keep only cross-domain status/severity/risk/environment values; capability states stay local. |
| Automatic redaction inside canonical JSON | Changes serialized identity silently | Pure serializer; explicit redaction wrapper. |
| Structlog compatibility adapter plus default sinks | Large compatibility layer and import-time filesystem writes | Small standard logging-compatible facade with explicit configuration. |
| Full Event Bus retry/dead-letter/idempotency/backpressure stack | No confirmed production caller and multiple unresolved choices | Defer entire stateful capability; later approve a bounded in-process slice. |
| Email/Telegram/desktop routing inside Utils | Provider ownership unresolved and notification package already exists outside Utils | Defer and resolve domain/infrastructure owner; Utils may keep sanitized DTOs only if needed. |
| Prometheus/Grafana/clock drift/circuit stack | Disconnected V1 implementation and no thresholds/exporter owner | Defer to production observability slice. |
| Process/thread pool chunk execution in core dataframe helpers | Orchestration and pickling/lifecycle complexity | Retain only deterministic sequence chunking. |
| Domain error taxonomies in Utils | Every domain change expands shared kernel | Move domain errors to owners; preserve generic `code` mapping. |
| Live readiness and research models in settings | Domain leakage | Move to Live and Research domains. |

## 11. Open Decisions

Cross-domain items must be added to the top-level system document during pipeline step 05 and resolved there, with an ADR where required. They are not resolved by this domain reconciliation.


| Status | Decision required | Evidence available | Options | Affected capabilities |
| --- | --- | --- | --- | --- |
| Open | Authoritative package root: `app.services.utils` or `tools.utils` | V2 purpose/FRs use the first; target structure and CI use the second. | Keep `app.services.utils`; move to `tools.utils`; define another canonical root. | CAP-UTL-001 and all modules |
| Open | First accepted implementation slice | V2 classes Core/Production/Adapter/Future exist, but the exact Builder slice is not selected. | Core only; core plus selected security; larger production slice. | All capabilities |
| Open | Agent-safe input modes for dataframe-like official tools | V2 explicitly leaves pandas/records/artifact references unresolved. | JSON records only; artifact references only; pandas for non-agent callers plus records for agents. | CAP-UTL-010 / 011 |
| Open | Ownership of external pub/sub adapters | V2 says Utils optional adapters or infrastructure; V1 has only in-process test use. | Infrastructure owns adapters; Utils optional adapter folder; separate event domain. | CAP-UTL-016 |
| Open | Ownership of notifications and real providers | V2 proposes Utils routing; V1 audit shows a separate notification package. | Notification domain; infrastructure adapters; Utils DTOs only. | CAP-UTL-017 |
| Open | Observability/exporter/dashboard ownership | V2 proposes Utils metrics/Grafana; V1 implementation is disconnected. | Utils primitives; infrastructure observability domain; application runtime export. | CAP-UTL-018 |
| Open | Benchmark profile and numeric thresholds | V2 requires measurable gates but supplies no approved profile. | Baseline-only; acceptance gate; environment-specific profiles. | CAP-UTL-010 / 011 / 018 / 019 |
| Open | Supported Python, OS and optional-dependency matrix | V2 requires documentation but gives no values. | Project-wide baseline plus optional-adapter matrix. | All capabilities |
| Open | Repository-wide quality toolchain | V2 prescribes Black/isort/Flake8, but the V1 audit does not establish the authoritative CI standard. | Accept listed tools; use another project standard; mixed transitional gate. | All implementation/tests |
| Open | Dataframe cache destination and migration timing | V1-WF-UTILS-003 is a real Data caller; V2 does not assign cache ownership to Utils. | Move immediately to Data; temporarily retain compatibility; remove caching. | CAP-UTL-020 |
| Open | Final owner of internal auth context | V2 assigns it to Utils; V1 production API uses a separate authentication path. | Utils for tool authorization; governance/agentic domain; application security domain. | CAP-UTL-015 |

## 12. Inputs for the Final Domain README

### Approved capabilities

* Strict public registry and public contract classification.
* Structured import-safe logging with explicit configuration.
* Shared error model and generic exception mapping.
* Standard official-tool envelopes, timing, and schema validation.
* Native identity, version, and trace helpers.
* UTC-first time, clock, and freshness helpers.
* Safe path normalization and explicit directory creation.
* Pure deterministic canonical JSON serialization.
* Pure lazy-loaded dataframe and sequence helpers.
* Stateless diagnostic OHLCV quality validation.
* Bounded schema and contract validation.
* Native redaction and secret-safe diagnostics.
* Restricted password, encryption, and secret-version helpers.
* Immutable explicitly loaded generic runtime settings.
* Internal auth context and deny-by-default official-tool authorization.
* One immutable operational limits profile for accepted core capabilities.

### Approved workflows

* Structured logging and redaction.
* Credential hashing and verification.
* Standard tool-response construction.
* Safe path resolution.
* Explicit settings loading and injection.
* Schema and packet validation.
* OHLCV diagnostic validation.
* Official-tool authorization.
* Strict public symbol registration.

### V1 behaviours to preserve

* Logger/get_logger caller-facing usage.
* Secret redaction before log emission.
* Deterministic error codes and generic exception mapping.
* Standard envelope top-level shape.
* Monotonic execution timing.
* UUID-based ID generation and validation.
* UTC-first time conversion.
* Traversal-safe paths and explicit `ensure_*` side effects.
* Password hashing and verification used by API/database workflows.
* Existing useful OHLCV defect checks.
* Existing useful schema/packet validators.

### V1 behaviours to modify

* Remove import-time logging configuration and file creation.
* Replace silent registry fallback with fail-fast strict resolution.
* Merge duplicate response, path, dataframe, schema, redaction, and OHLCV implementations.
* Replace hybrid native/envelope return objects with explicit contracts.
* Split domain error taxonomies from shared errors.
* Split generic time helpers from board/execution freshness policy.
* Split generic settings from live and research settings.
* Add mapping-based settings loading and explicit injection.
* Add tool allowlist authorization.
* Bound all validator and redaction workloads.

### V1 behaviours to remove

* Broken package export aliases, after import migration checks.
* Placeholder standardization APIs.
* Utils-owned dataframe cache, after Data-domain migration.
* Process/thread-pool chunk orchestration from the core helper surface, after caller verification.
* Live readiness policy from Utils, after Live-domain migration.
* Research configuration models from Utils, after Research-domain migration.
* Domain-specific error hierarchies from Utils, after owner migration.
* Import-time default log sinks.
* Duplicate wrappers and fallback modules.

### V2 behaviours to add

* Public contract entries and classifications.
* Registry contract tests that resolve every export.
* Immutable limits profile and validated overrides.
* Bounded JSON-pointer validation diagnostics.
* Explicit schema-version policy.
* Redaction depth/string limits and narrow audited allowlists.
* Argon2id-first password policy.
* Explicit optional-dependency failure contracts.
* Immutable settings mapping load and target injection.
* Official-tool role/permission/scope/tool allowlists.
* Import-safety and no-side-effect tests.
* Measurable performance gates once the benchmark profile is approved.

### V2 proposals to reject or defer

* Reject the arbitrary “v8 acceptance” export-freeze rule.
* Reject implicit redaction inside canonical JSON.
* Defer the full Event Bus subsystem.
* Defer error-routing orchestration.
* Defer notification routing, templates, and providers.
* Defer Prometheus/Grafana integration.
* Defer clock-drift integration.
* Defer circuit breakers until external providers exist.
* Defer external pub/sub and notification adapters.
* Defer chaos tests tied to absent adapters.
* Defer multiprocess logging unless a production caller is confirmed.

### Required open decisions before README completion

* Canonical package root.
* Core implementation slice.
* Agent-safe dataframe input modes.
* Dataframe-cache migration owner and timing.
* Internal auth-context owner.
* Cross-domain Event Bus ownership.
* Notification/provider ownership.
* Observability/exporter/dashboard ownership.
* Benchmark profile and thresholds.
* Supported Python/OS/dependency matrix.
* Repository-wide CI/quality toolchain.

## 13. Final Reconciliation Checklist

* [x] Every V1 capability received a disposition: **28 of 28**.
* [x] Every V2 checklist requirement received a disposition: **1,164 of 1,164**.
* [x] Additional V2 normative ownership, matrix, default, architecture, and CI statements received dispositions: **77 of 77**.
* [x] Every V1 workflow was reconciled: **9 of 9**.
* [x] Proposed V2 workflows were reconciled through final workflows `WF-UTL-010` to `WF-UTL-013`.
* [x] Confirmed working V1 behaviour was not discarded without a migration reason.
* [x] Unused or disconnected V1 behaviour was not preserved automatically.
* [x] V2 implementation complexity was not accepted automatically.
* [x] The proposed direction follows the four-level minimal structure at capability level.
* [x] Suspected cross-domain responsibilities are flagged.
* [x] Unresolved conflicts are listed under Open Decisions.
* [ ] Cross-domain open decisions and deferrals must be added to the top-level system document in pipeline step 05; that document was intentionally not modified here.
* [x] No code was inspected or changed during reconciliation.
* [x] Neither source document was modified.
* [x] The approved inputs are sufficient to begin the final domain README after blocking package, scope, and ownership decisions are resolved.

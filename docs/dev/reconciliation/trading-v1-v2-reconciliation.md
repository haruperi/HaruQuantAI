# Trading — V1/V2 Reconciliation

## 1. Reconciliation Scope

* **Domain:** trading (`trd`)
* **V1 audit report:** `docs/dev/audits/trading-v1-audit.md`
* **V2 requirements:** `07_trading.md` and `10_live.md`, treated as one proposed domain specification.
* **Package direction:** one route-aware `app.services.trading` domain. Accepted live-only behavior becomes an internal Trading capability rather than a separate `app.services.live` domain.
* **Comparison limitations:**
  * This step used only the V1 audit and the two V2 requirement documents. No code was inspected, executed, or modified.
  * The V1 audit could not prove complete production caller wiring, runtime dependency injection, deployment configuration, or test execution.
  * The V2 documents do not assign stable IDs to individual checklist items. This reconciliation assigns source-local IDs (`TRD-V2-*` and `LIVE-V2-*`) in document order solely for disposition traceability.
  * Concrete broker, governance, risk, simulator, persistence, observability and infrastructure contracts remain subject to the later cross-domain alignment review.

## 2. Executive Summary

The final direction is to **keep one Trading domain** with explicit route selection and an internal live-runtime capability. The strongest V1 behavior should be preserved: Decimal-safe validation, route-neutral request/response contracts, the fail-closed packaged-only path, a single broker mutation boundary, response normalization, idempotency, concurrency control, state projections, reconciliation, unknown-outcome retry blocking, emergency controls, session lifecycle, read-only broker facts, redaction and audit evidence.

The highest-priority correction is removal of the V1 risk passthrough. A live request must never pass the risk gate without a real externally owned risk verdict. The duplicate V1 error systems, duplicate `OrderIntent` models, competing contract bases, silent read fallbacks, disconnected cost/monitoring components, internal rate-limit policy, raw signal translator, and internal promotion ownership must also be corrected.

Important V2 behavior to add includes an actual simulation-route authority dispatch, one canonical envelope and public contract matrix, caller-controlled idempotency material, structured route snapshots/readiness, startup reconciliation before live enablement, approved broker adapter capability/security contracts, malformed-success and rate-limit classification, complete pre/post audit evidence, notification incidents, and connected cost-budget enforcement.

The V2 proposals are significantly simplified. Rejected or deferred architecture includes a separate Live package and registry, concrete MT5/cTrader/paper/simulator bridges inside Trading, simulator engine state and monitoring inside Trading, approval creation/voting services, dozens of public validation helpers, lazy package attribute resolution, a post-failure diagnostic-gate framework, generic service/manager/engine layers, custom domain-owned persistence architecture, a local rate-limit policy engine, performance snapshot caches, generalized automatic compensation, and initial shadow-comparison breadth.

Production live mutation remains disabled until the safety-critical open decisions are approved and versioned: external action policy and approval contracts, risk verdict contract, idempotency schema/store/retention, reconciliation authority transitions, kill-switch hierarchy and in-flight behavior, launch broker adapter/security contracts, concurrency rules, operational limits, audit durability and recovery objectives. Proposed throughput and latency SLOs do not by themselves determine mutation safety.

**Recommended migration direction:** refactor V1 incrementally around one canonical contract family and one approved route dispatcher. Keep proven behavior where it is already focused, replace duplicated infrastructure abstractions with minimal injected interfaces, add the missing simulation and live composition connections, and defer nonessential shadow and generalized compensation features.

## 3. Decision Principles

* Preserve proven working safety and execution behavior.
* Use one Trading package for shared and live-only behavior; routes select authority and side effects.
* Keep policy creation in its owning domains; Trading consumes and enforces versioned verdicts.
* Prefer one canonical request, result, error and audit contract.
* Prefer functions for stateless validation, packaging, comparison and classification.
* Use classes only when they own state, dependencies, concurrency or lifecycle.
* Keep one production broker/simulator authority dispatch boundary.
* Never treat packaged-only success as execution, approval, readiness or broker acceptance.
* Never permit a risk passthrough, blind retry after unknown outcome, or broker mutation after failed pre-audit.
* Return structured unavailable/stale failures instead of silent neutral broker facts.
* Define persistence events and minimal interfaces; keep backend/schema/migration ownership external.
* Reject duplicate public APIs and implementation layers that do not support a confirmed workflow.
* Defer optional shadow, snapshot-cache and generalized compensation behavior until their contracts are approved.
* Approve limits and SLOs from provider/workload evidence rather than copying proposed defaults.
* Keep one focused responsibility per capability module and per public file.

## 4. Capability Reconciliation Matrix

| Capability ID | Capability | V1 evidence | V2 requirement | Gap | Decision | Final behaviour | Reuse approach | Reason |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| CAP-TRD-001 | Public API, contract registry and route metadata | `V1-CAP-TRADING-001`, `V1-CAP-TRADING-032`; `contracts.py`, `tool_registry.py`; `V1-WF-TRADING-001` | `TRD-V2-OWN-001`–`003`, `TRD-V2-API-001`–`004`, `TRD-V2-FR-003`–`007`, `LIVE-V2-API-001`–`006` | V1 exposes a broad Python facade and one metadata-only AI tool; V2 conflates `__all__`, public API and agent tools. | Modify | One explicit public Python contract matrix plus a separate restricted agent-tool registry; every approved call declares routes, side effects, approvals, idempotency, statuses and schemas. | Refactor | Preserves discoverability while preventing internal helpers or mutation-capable calls from becoming agent authority. |
| CAP-TRD-002 | Canonical route, request, receipt and result contracts | `V1-CAP-TRADING-001`; `TradingRequestEnvelope`, `TradingResponseEnvelope`, execution/fill compatibility contracts | `TRD-V2-FR-008`–`017`, `032`–`040`, `LIVE-V2-FR-004`–`007`, `021`–`022` | V1 has two base-contract families, duplicate intent models and incomplete envelope fields/statuses. | Modify | One Decimal-safe, UTC, JSON-safe request/receipt/result family with a finite status, error, warning, side-effect and retry-safety taxonomy. | Refactor | A single contract family removes ambiguity and supports all routes. |
| CAP-TRD-003 | Error taxonomy, redaction and boundary safety | `V1-CAP-TRADING-020`; `errors.py`, `security/error_mapping.py`, `security/redaction_boundary.py` | `TRD-V2-FR-017`, `032`–`040`; `TRD-V2-NFR-005`–`007`, `022`; `LIVE-V2-NFR-005`–`009` | V1 has duplicate exception hierarchies, duplicate mappers and inconsistent codes. | Merge | One error hierarchy, one finite error registry, one envelope mapper and one recursive redaction boundary. | Refactor | Prevents mismatched codes and return types at safety boundaries. |
| CAP-TRD-004 | Order and operation validation | `V1-CAP-TRADING-002`; `actions/validation.py`; `V1-WF-TRADING-001` | `TRD-V2-API-007`, `TRD-V2-FR-073`–`083`, `117`–`143`, Decimal/time requirements | V1 has strong Decimal validation but V2 proposes dozens of public validators and some out-of-domain checks. | Modify | Expose one canonical `validate_order_request` and one aggregate readiness operation; use private focused validators for symbol, volume, price, stops, margin, tickets and operation preconditions. | Reuse/Refactor | Preserves proven checks with a smaller stable API. |
| CAP-TRD-005 | Route-aware order and position actions | `V1-CAP-TRADING-003`, `004`; `actions/orders.py`, `actions/positions.py` | `TRD-V2-FR-046`–`055`, `111`–`115`; `LIVE-V2-FR-032`–`041` | V1 names are fragmented (`buy`, `sell`, pending helpers) and non-live calls normally only package. | Modify | Use canonical verbs `submit_order`, `modify_order`, `cancel_order`, `close_position`, `modify_position`, `reduce_exposure` with one request shape and route-selected authority. | Refactor | One verb family avoids simulation/live drift. |
| CAP-TRD-006 | Simulation route execution boundary | `V1-WF-TRADING-001`; V1 packages non-live requests but does not prove simulator mutation | `TRD-V2-OWN-007`, `010`; `TRD-V2-FR-046`, `144`–`149`; simulation tests | Required `sim` mutation is missing, while V2 incorrectly places simulator engine state and monitors in Trading. | Add | Trading validates and dispatches `route='sim'` to an injected simulator authority and returns canonical receipts; Simulator owns state, fills, monitors and resource behavior. | New boundary using V1 request packaging | Adds the missing workflow without duplicating the Simulator domain. |
| CAP-TRD-007 | Route snapshots and execution readiness | `V1-CAP-TRADING-013`, `016`; `info/*`, readiness/capability checks; `V1-WF-TRADING-004` | `TRD-V2-API-005`–`010`, `TRD-V2-FR-060`–`083`; `LIVE-V2-FR-016`–`017` | V1 read facades are useful but silently return neutral defaults; V2 proposes too many top-level check functions. | Modify | Provide structured route snapshots plus aggregate readiness with explicit unavailable/stale evidence and approved adapter capability/version checks. | Refactor | Retains read value while preventing false readiness. |
| CAP-TRD-008 | Live runtime configuration and session lifecycle | `V1-CAP-TRADING-017`–`019`, `028`; `config/*`, `runtime/session_manager.py`; `V1-WF-TRADING-009`, `010` | `LIVE-V2-OWN-001`–`002`, `LIVE-V2-FR-042`–`049`, live startup/shutdown NFRs | V1 components exist but production composition and secret/session ownership are unconfirmed. | Merge | Place live enablement, startup, startup reconciliation, status, recovery and safe shutdown under `app.services.trading.live`; consume opaque secret/session providers. | Refactor | Combines Trading and Live without weakening secret boundaries. |
| CAP-TRD-009 | Canonical live gate pipeline | `V1-CAP-TRADING-007`; `gates/*`, `LiveGatePipelineImpl`; `V1-WF-TRADING-002` | `LIVE-V2-FR-001`–`031`, `TRD-V2-NFR-001`–`003` | V1 has sixteen gates but permits a risk passthrough; V2 proposes a different order and post-failure diagnostic framework. | Modify | Use one deterministic fail-fast sequence: schema → live/session enablement → action policy/approval → risk verdict → kill switch → readiness/staleness → idempotency → concurrency → reconciliation authority → pre-audit → adapter permission → dispatch. | Refactor | Keeps all safety invariants, removes duplicate gates and forbids risk passthrough. |
| CAP-TRD-010 | External governance verdict consumption | V1 approval/risk evidence seams; `V1-ISSUE-TRADING-001`; `V1-WF-TRADING-002` | `TRD-V2-FR-015`, `091`–`105`; `LIVE-V2-FR-023`–`031` | V1 can accept a risk passthrough and owns an internal policy matrix/promotion logic; approval/risk ownership is unresolved. | Modify | Consume versioned approval, risk, authorization, action-policy and kill-switch verdict contracts; validate scope/expiry/revocation and re-check immediately before send. | Replace risk passthrough; refactor policy use | Trading enforces verdicts but never creates policy, approvals or risk decisions. |
| CAP-TRD-011 | Idempotency and concurrency control | `V1-CAP-TRADING-022`, `029`; `state/idempotency.py`, `runtime/coordination.py` | `TRD-V2-FR-018`–`023`, `030`; `LIVE-V2-FR-075`, `085`–`088` | V1 sometimes generates keys internally and has one lock scope; final fields, retention and scopes are unresolved. | Modify | Require caller-controlled keys for governed mutation, canonical material/version conflict checks, durable reservation before send and approved per-action conflict scopes. | Refactor | Preserves duplicate protection while avoiding false exactly-once guarantees. |
| CAP-TRD-012 | Broker/simulator authority dispatch and adapter contract | `V1-CAP-TRADING-008`, `009`, `013`; single mutation boundary and response classifier | `TRD-V2-OWN-013`, `TRD-V2-FR-101`, `106`–`116`; `LIVE-V2-FR-076`–`084` | V1 has a good single broker boundary but incomplete adapter version/security/rate-limit contracts; V2 proposes duplicate concrete bridges. | Modify | Keep one authority-dispatch boundary; consume concrete broker/simulator adapters and validate their capability, schema, security, timeout and retry-safety contracts. | Reuse/Refactor | Preserves the strongest V1 boundary without duplicating adapter implementations. |
| CAP-TRD-013 | Receipts, lifecycle transitions and route state projections | `V1-CAP-TRADING-011`, `024`; execution state machine and trade stores | `TRD-V2-FR-057`, `149`–`153`; live state requirements | V1 has lifecycle/projection machinery but mixed contracts and concrete JSONL/in-memory stores. | Modify | Use canonical send-attempt, receipt, fill, order and position events with explicit authority state and optimistic version checks; storage implementation is injected. | Refactor | Supports recovery and analytics without domain-owned persistence backends. |
| CAP-TRD-014 | Reconciliation, authority and unknown-outcome retry guard | `V1-CAP-TRADING-025`; `reconciliation/*`; `V1-WF-TRADING-003` | `TRD-V2-FR-153`–`158`; `LIVE-V2-FR-066`–`075` | V1 comparison/guard exists, but the live timeout hook may only snapshot and the authority transition model is pending. | Modify | Normalize authority snapshots, compare missing/extra/mismatched/stale records, persist evidence, prefer broker truth for live, and block retry until an approved authority transition resolves. | Reuse/Refactor | Core safety value is proven; production composition must be completed. |
| CAP-TRD-015 | Operational controls, kill switches and emergency actions | `V1-CAP-TRADING-005`, `006`; controls/emergency actions; `V1-WF-TRADING-005`, `008` | `LIVE-V2-FR-054`–`065`; action policy requirements | V1 trigger events and gate state are not confirmed to share one authoritative projection; approval/emergency classification is incomplete. | Modify | Provide pause/resume, scoped kill-switch trigger/enforcement/clear, disable-new-orders, cancel-all and close-all through the same action-policy, approval, audit and live-gate rules. | Refactor | Preserves emergency value while closing the trigger-to-enforcement gap. |
| CAP-TRD-016 | Audit and persistence event contracts | `V1-CAP-TRADING-021`, `023`, parts of `024`; custom JSONL journal, DLQ and stores | `TRD-V2-OWN-012`, `FR-087`–`090`, `150`–`158`; `LIVE-V2-FR-013`–`015` | V1 custom encrypted JSONL/hash-chain/DLQ implementations are complex and production use is unconfirmed. | Merge | Trading defines versioned audit/send/receipt/reconciliation/incident events and minimal sinks; Infrastructure provides durable implementations. Pre-audit failure blocks send. | Refactor/Replace concrete stores | Preserves forensic evidence without embedding storage architecture. |
| CAP-TRD-017 | Monitoring and incident events | `V1-CAP-TRADING-026`; monitoring components | `TRD-V2-FR-159`–`164`; `LIVE-V2-FR-089`–`099`; monitoring NFRs | V1 components are not production-wired; V2 over-specifies universal fields and snapshot caching. | Modify | Emit focused health, dependency, staleness, timeout, latency, notification and incident events; external observability aggregates/transports them. Defer snapshot caches. | Refactor | Delivers operational value with smaller state. |
| CAP-TRD-018 | Cost-budget verdict enforcement | `V1-CAP-TRADING-030`; disconnected `CostController` | `TRD-V2-FR-166`; `LIVE-V2-FR-100`–`103` | V1 budget control is disconnected; Trading versus Live ownership conflicts. | Modify | Consume externally owned budget limits/verdicts, block before send when exceeded, and record an incident if exceeded after send. | Refactor | Trading enforces the safety verdict but does not own budget policy. |
| CAP-TRD-019 | Execution evidence and trading reports | `V1-CAP-TRADING-014`; execution reporting/TCA events | `TRD-V2-FR-056`–`058`, `150`; `LIVE-V2-FR-041`, `104` | V1 reporting is test-only; V2 mixes evidence packaging and performance analytics. | Modify | Trading packages immutable execution, receipt, readiness, reconciliation, incident and warning evidence; Analytics computes derived performance and comparisons. | Refactor | Clarifies cross-domain ownership. |
| CAP-TRD-020 | Shadow execution and expected-versus-realized comparison | `V1-CAP-TRADING-015`; `execution/shadow.py` | `TRD-V2-OWN-016`, `FR-059`; `LIVE-V2-FR-107`–`111` | Test-only V1 behavior; no initial launch workflow requires it. | Defer | Exclude from the initial rebuild; later add a no-live-reference shadow mode and analytics comparison after validation criteria are approved. | Defer V1 code | Reduces initial complexity without losing the proposal. |
| CAP-TRD-021 | Generalized compensation plans | V1 emergency actions and audit compensation helper; no approved generic catalog | `TRD-V2-FR-167`–`171`; compensation NFR/tests; `LIVE-PEND-008` | No approved ownership, catalog, scope, retry or terminal-state model. | Defer | Use explicit emergency cancel/close actions initially; defer a generalized compensation registry and automatic execution. | New later | Generic compensation is unsafe without a governed catalog. |
| CAP-TRD-022 | Canonical upstream request intake | `V1-CAP-TRADING-031`; raw dictionary `SignalProcessor`; `V1-WF-TRADING-007` | `TRD-V2-BOUND-001`, `FR-098`–`100`; `LIVE-V2-FR-050` | V1 translator is test-only and blurs Strategy/Trading ownership. | Remove | Upstream Strategy/Conversation/Governance supplies the canonical Trading request; Trading validates it and does not translate arbitrary strategy signal dictionaries. | Remove/Replace at boundary | Eliminates an unproven duplicate orchestration layer. |
| CAP-TRD-023 | Rate-limit outcome handling | `V1-CAP-TRADING-012`; local token-bucket policy | `TRD-V2-BOUND-003`, `FR-016`; `LIVE-V2-FR-080`–`083` | V1 owns policy despite V2 assigning policy externally; provider retry behavior is unresolved. | Merge | Consume rate-limit verdicts and classify provider responses with `retry_after_seconds` and conservative retry safety; remove local policy engine. | Remove token bucket; reuse classifier | Avoids policy duplication and blind retries. |
| CAP-TRD-024 | Route capability and promotion evidence | `V1-CAP-TRADING-027`; promotion ladder and preconditions | `TRD-V2-BOUND-001`, `FR-015`; live action policy requirements | V1 appears to own promotion transitions, while V2 places strategy promotion outside Trading. | Modify | Consume approved strategy/promotion state and enforce route/capability compatibility; remove strategy promotion transition ownership from Trading. | Refactor | Retains a useful gate without crossing governance boundaries. |
| CAP-TRD-025 | Agent-safe trading drafts | `V1-CAP-TRADING-032`; metadata-only `create_trading_action_draft` | `TRD-V2-FR-003`–`007`, `098`; public contract matrix requirements | V1 registry has no confirmed callable binding and only one draft definition. | Modify | Expose only non-mutating draft/inspection tools to agents by default; any governed action callable must pass the same canonical request and live gates. | Refactor/New binding | Preserves AI assistance without granting execution authority. |

## 5. V1 Disposition Register

Every capability in the V1 audit is explicitly dispositioned below.

| V1 capability ID | V1 capability | Current implementation | Current value | Decision | Final destination | Removal condition |
| --- | --- | --- | --- | --- | --- | --- |
| V1-CAP-TRADING-001 | Canonical trading contracts | `contracts.py`; root facade | Essential | Modify | `CAP-TRD-001`, `002`, `003` | N/A; split and migrate all callers before removing legacy models. |
| V1-CAP-TRADING-002 | Local order validation and normalization | `actions/validation.py::validate_order_request` | Essential | Modify | `CAP-TRD-004` | N/A; preserve tests and Decimal geometry. |
| V1-CAP-TRADING-003 | Market and pending order actions | `actions/orders.py` | Essential | Modify | `CAP-TRD-005` | N/A; migrate callers to canonical action names. |
| V1-CAP-TRADING-004 | Position lifecycle actions | `actions/positions.py` | Essential | Modify | `CAP-TRD-005` | N/A; preserve netting/hedging and partial-close behavior. |
| V1-CAP-TRADING-005 | Strategy/session controls | `actions/controls.py` | Useful | Modify | `CAP-TRD-015`, `008` | N/A; separate operational controls from session lifecycle. |
| V1-CAP-TRADING-006 | Emergency cancel/close/flatten | `actions/emergency.py` | Essential | Modify | `CAP-TRD-015` | N/A; retain partial completion and apply action-policy/approval gates. |
| V1-CAP-TRADING-007 | Sixteen-gate live preflight | `gates/*`; `LiveGatePipelineImpl` | Essential | Modify | `CAP-TRD-009`, `010` | N/A; delete passthrough risk only after real risk-verdict integration tests pass. |
| V1-CAP-TRADING-008 | Single broker mutation boundary | `execution/broker_dispatch.py` | Essential | Keep | `CAP-TRD-012` | N/A; extend only for approved authority adapters and contract checks. |
| V1-CAP-TRADING-009 | Broker response normalization | `execution/response_classifier.py` | Essential | Modify | `CAP-TRD-003`, `012` | N/A; unify codes/status/retry taxonomy first. |
| V1-CAP-TRADING-010 | Async dispatch and execution coordination | `execution/coordinator.py` | Essential | Split | `CAP-TRD-012`, `013`; advanced OCO/multi-leg deferred | Verify no production callers need deferred OCO/multi-leg/non-atomic helpers before removal. |
| V1-CAP-TRADING-011 | Lifecycle state machine | `execution/state_machine.py` | Essential | Modify | `CAP-TRD-013` | N/A; simplify to approved transition/receipt states. |
| V1-CAP-TRADING-012 | Rate limiting | `execution/rate_limiter.py` | Supporting | Remove | `CAP-TRD-023` consumes external verdicts | Verify no production caller depends on the local token bucket; migrate provider response tests first. |
| V1-CAP-TRADING-013 | Broker capability validation | `execution/broker_capability_validation.py` | Essential | Modify | `CAP-TRD-007`, `012` | N/A; add version/schema/security checks. |
| V1-CAP-TRADING-014 | Execution reporting/TCA events | `execution/reporting.py` | Useful | Modify | `CAP-TRD-019` | N/A; move derived analytics to Analytics. |
| V1-CAP-TRADING-015 | Shadow intent/fill comparison | `execution/shadow.py` | Useful | Defer | `CAP-TRD-020` | Verify no production shadow caller; retain tests/source until deferred milestone decision. |
| V1-CAP-TRADING-016 | Read-only broker facades | `info/*` | Useful | Modify | `CAP-TRD-007` | N/A; replace silent neutral fallbacks with structured availability/staleness results. |
| V1-CAP-TRADING-017 | Configuration load/reload/hash | `config/loader.py`, `config/models.py` | Supporting | Modify | `CAP-TRD-008` | N/A; retain live enablement and deterministic config evidence only. |
| V1-CAP-TRADING-018 | Secret-reference and credential rotation | `config/secrets.py` | Supporting | Modify | `CAP-TRD-008` | Remove credential-rotation ownership after external secret/session provider integration is verified. |
| V1-CAP-TRADING-019 | Live security profile validation | `config/security_profile.py` | Supporting | Modify | `CAP-TRD-012` | N/A; align with approved broker adapter security contract. |
| V1-CAP-TRADING-020 | Boundary error mapping/redaction | `security/*`, `errors.py` | Essential | Merge | `CAP-TRD-003` | Delete duplicate hierarchy/mapper only after all imports and public error snapshots migrate. |
| V1-CAP-TRADING-021 | Dead-letter/manual-review persistence | `WriteAheadDeadLetterQueue` | Essential | Merge | `CAP-TRD-016` incident/audit persistence | Verify infrastructure audit sink provides durable failure/incident handling before deleting custom DLQ. |
| V1-CAP-TRADING-022 | Idempotency leases and completion cache | `state/idempotency.py` | Essential | Modify | `CAP-TRD-011` | N/A; change to caller-controlled keys and approved retention/material. |
| V1-CAP-TRADING-023 | Append-only encrypted journal and replay | `state/event_journal.py` | Essential | Modify | `CAP-TRD-016` | Replace custom storage only after durable audit/event store contract and replay tests are available. |
| V1-CAP-TRADING-024 | Versioned trade projection store | `state/trade_store.py` | Essential | Modify | `CAP-TRD-013`, `016` | Replace concrete JSONL/in-memory production assumptions after injected store contract passes recovery tests. |
| V1-CAP-TRADING-025 | Reconciliation comparison and authority guard | `reconciliation/*` | Essential | Modify | `CAP-TRD-014` | N/A; approve authority-state transitions and complete timeout/startup wiring. |
| V1-CAP-TRADING-026 | Monitoring, heartbeat and incident signals | `monitoring/*` | Supporting | Modify | `CAP-TRD-017` | Remove unneeded snapshot/cache breadth only after final monitoring event contract is approved. |
| V1-CAP-TRADING-027 | Promotion ladder and preconditions | `promotion/*` | Essential | Modify | `CAP-TRD-024`, `009` | Remove internal promotion transition ownership after external lifecycle/governance state contract is integrated. |
| V1-CAP-TRADING-028 | Session lifecycle and operational modes | `runtime/session_manager.py` | Essential | Modify | `CAP-TRD-008` | N/A; retain stateful lifecycle where required. |
| V1-CAP-TRADING-029 | Per-scope concurrency coordination | `runtime/coordination.py` | Essential | Modify | `CAP-TRD-011` | N/A; approve final per-action scopes/timeouts/recovery. |
| V1-CAP-TRADING-030 | Cost budget control | `runtime/cost_control.py` | Supporting | Modify | `CAP-TRD-018` | Remove internal budget-policy calculation after external verdict contract is integrated. |
| V1-CAP-TRADING-031 | Strategy signal translation | `runtime/signal_processor.py` | Questionable | Remove | `CAP-TRD-022` canonical request boundary | Confirm no production caller uses it; migrate upstream to construct canonical requests, then delete. |
| V1-CAP-TRADING-032 | Packaged-only AI tool catalog | `tool_registry.py` | Useful | Modify | `CAP-TRD-001`, `025` | N/A; bind only approved non-mutating tools and separate from Python exports. |

## 6. V2 Requirement Disposition Register

This register dispositions **all 649 identified V2 items**: 535 checklist requirements, 92 named edge cases, 4 architecture prescriptions, 10 proposed target values, and 8 pre-production pending decisions. Source-local IDs were assigned in document order because the source documents do not yet provide item-level stable IDs.

### 6.1 `07_trading.md` checklist requirements

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
| --- | --- | --- | --- | --- |
| `TRD-V2-OWN-001` | The public trading tool registry exposed by `app.services.trading.__all__`. | **Modify** | Use one explicit public API registry; do not equate all `__all__` exports with agent tools. | V1 has a registry, but the V2 wording conflates package exports and agent-facing tools. |
| `TRD-V2-OWN-002` | The canonical trading route contract, including `route="sim"` and `route="live"`. | **Keep** | Retain one canonical route contract, initially `sim` and `live`. | This is the central unifying design. |
| `TRD-V2-OWN-003` | Standard trading tool envelopes for agent-facing trading tools. | **Modify** | Use one canonical envelope for all public trading calls; agent tools are a restricted subset. | V1 has envelopes but not the complete proposed schema. |
| `TRD-V2-OWN-004` | Shared broker/connectivity request packaging for account, symbol, quote, spread, market, margin, lot, stop-distance, permission, and broker-time checks. | **Modify** | Retain the behaviour as focused route-aware capabilities with a smaller public surface. | V1 already covers much of it, but V2 lists too many separate public helpers. |
| `TRD-V2-OWN-005` | Shared execution-readiness validation for environments, strategy runtime config, broker symbol mapping, order requests, price, size, stop loss, take profit, slippage, transaction cost, and execution plan construction. | **Modify** | Retain the behaviour as focused route-aware capabilities with a smaller public surface. | V1 already covers much of it, but V2 lists too many separate public helpers. |
| `TRD-V2-OWN-006` | Shared order, pending-order, position, pause, resume, exposure-reduction, synchronization, reconciliation, receipt, and report request functions. | **Modify** | Retain the behaviour as focused route-aware capabilities with a smaller public surface. | V1 already covers much of it, but V2 lists too many separate public helpers. |
| `TRD-V2-OWN-007` | Simulation-compatible trading behavior, including simulated order placement, pending-order processing, fill records, account snapshots, equity points, trade records, and JSON-safe result containers. | **Modify** | Trading owns the route contract and dispatch boundary; simulator state and fill mechanics remain with the simulator authority. | Keeps one API without duplicating the simulator engine. |
| `TRD-V2-OWN-008` | Live-compatible trading request packaging before live runtime and broker mutation gates are applied. | **Merge** | Merge live packaging and live enforcement into the unified trading package under a `live` capability module. | The user selected one domain rather than separate Trading and Live packages. |
| `TRD-V2-OWN-009` | Construction and validation of trading request packages while consuming approval, risk, kill-switch, authorization, and live-runtime enablement verdicts from their owning modules. | **Merge** | Merge live packaging and live enforcement into the unified trading package under a `live` capability module. | The user selected one domain rather than separate Trading and Live packages. |
| `TRD-V2-OWN-010` | Simulator-state mutation for `route="sim"` without production broker mutation. | **Modify** | Trading owns the route contract and dispatch boundary; simulator state and fill mechanics remain with the simulator authority. | Keeps one API without duplicating the simulator engine. |
| `TRD-V2-OWN-011` | Execution intent assembly, idempotency material, authority-state propagation, pre-send validation, send-attempt evidence payloads, receipts, compensation plan packages, and retry guard inputs. | **Modify** | Split into intent/idempotency, receipts/authority, and optional compensation capabilities. | The proposed ownership bundle combines unrelated responsibilities. |
| `TRD-V2-OWN-012` | Persistence event payloads and repository interfaces for send attempts, receipts, reconciliation evidence, and compensation records, while database schema and migration ownership remain outside Trading. | **Keep** | Define persistence event contracts and minimal store interfaces; concrete persistence remains external. | This is a valid domain boundary. |
| `TRD-V2-OWN-013` | Broker bridge boundaries for MT5, cTrader, paper broker, simulator, and other approved trading adapters. | **Modify** | Own adapter capability contracts and routing calls, but consume concrete broker/simulator adapters from their owning packages. | Avoids duplicate MT5/cTrader/paper implementations. |
| `TRD-V2-OWN-014` | Trading validation rules for symbols, volume, price, order type, magic/expert identifiers, slippage, expiration, timeframe, date ranges, stop loss, take profit, credentials, margin, tickets, max orders, and symbol volume. | **Modify** | Keep order and operation validation; move credential, timeframe and generic date-range validation to their owning domains unless broker-critical. | The list overreaches beyond trading action validation. |
| `TRD-V2-OWN-015` | Trading monitoring inputs for stale state, ingestion health, tool health, workflow timeout, incident classification, latency, cost, and operational status. | **Modify** | Emit trading monitoring inputs and incidents; central observability transport remains external. | V1 has components but lacks confirmed production wiring. |
| `TRD-V2-OWN-016` | Shadow-trading feeds and expected-versus-realized reporting when no live broker mutation occurs. | **Defer** | Exclude full shadow expected-versus-realized reporting from the initial rebuild; retain no-live-mutation safety rules. | Useful but not required to establish safe core execution. |
| `TRD-V2-BOUND-001` | The module does not own strategy signal generation, strategy lifecycle promotion, or strategy approval. | **Keep** | Retain this boundary in the unified trading domain. | It prevents scope leakage into strategy, risk, data, UI, governance or infrastructure. |
| `TRD-V2-BOUND-002` | The module does not own risk policy, position sizing approval, exposure limits, portfolio allocation policy, or kill-switch policy ownership. | **Keep** | Retain this boundary in the unified trading domain. | It prevents scope leakage into strategy, risk, data, UI, governance or infrastructure. |
| `TRD-V2-BOUND-003` | The module does not own rate-limiting policy enforcement; it consumes rate-limit verdicts from API Gateway, Live, or another approved policy owner where applicable. | **Keep** | Retain this boundary in the unified trading domain. | It prevents scope leakage into strategy, risk, data, UI, governance or infrastructure. |
| `TRD-V2-BOUND-004` | The module does not own market-data ingestion, provider data normalization, or historical data storage. | **Keep** | Retain this boundary in the unified trading domain. | It prevents scope leakage into strategy, risk, data, UI, governance or infrastructure. |
| `TRD-V2-BOUND-005` | The module does not own final live runtime enablement, live session orchestration, live secret resolution, or production broker mutation policy; those belong to `10_live.md`. | **Merge** | Live runtime ownership is internal to the unified trading domain, while policies still remain externally owned. | The separate `10_live` package boundary is removed. |
| `TRD-V2-BOUND-006` | The module does not initiate live credential discovery, live secret lookup, credential rotation, or live broker login flows on its own. | **Modify** | The unified trading live module may consume an injected secret/session provider but shall not discover or store raw credentials. | Preserves safe live startup without owning secrets. |
| `TRD-V2-BOUND-007` | The module does not own durable database schema/migration ownership. | **Keep** | Retain this boundary in the unified trading domain. | It prevents scope leakage into strategy, risk, data, UI, governance or infrastructure. |
| `TRD-V2-BOUND-008` | The module does not own approval voting policy, final approval-state authority, override policy, or strategy-promotion governance. | **Keep** | Retain this boundary in the unified trading domain. | It prevents scope leakage into strategy, risk, data, UI, governance or infrastructure. |
| `TRD-V2-BOUND-009` | The module does not independently authorize production broker mutation. | **Modify** | Trading may authorize mutation only by enforcing externally owned verdicts and configuration; it shall not create the policies. | A unified package must perform the final gate while remaining policy-neutral. |
| `TRD-V2-BOUND-010` | The module does not execute live compensation actions unless the same external live-runtime, approval, risk, kill-switch, idempotency, and reconciliation gates required for live mutation are satisfied. | **Keep** | Retain this boundary in the unified trading domain. | It prevents scope leakage into strategy, risk, data, UI, governance or infrastructure. |
| `TRD-V2-BOUND-011` | The module does not own API authentication, UI rendering, websocket connection management, or frontend workflow policy. | **Keep** | Retain this boundary in the unified trading domain. | It prevents scope leakage into strategy, risk, data, UI, governance or infrastructure. |
| `TRD-V2-BOUND-012` | The module does not grant AI chat, UI, API, backtest, or optimization workflows authority to bypass risk, approval, idempotency, reconciliation, audit, or kill-switch controls. | **Keep** | Retain this boundary in the unified trading domain. | It prevents scope leakage into strategy, risk, data, UI, governance or infrastructure. |
| `TRD-V2-BOUND-013` | The module does not provide financial advice, trading recommendations, or owner-approved live threshold decisions. | **Keep** | Retain this boundary in the unified trading domain. | It prevents scope leakage into strategy, risk, data, UI, governance or infrastructure. |
| `TRD-V2-API-001` | Export approved shared trading service tools through `app.services.trading.__all__`. | **Modify** | Expose a deliberately small stable public facade; maintain a separate agent-tool registry. | `__all__` is not itself an agent authorization mechanism. |
| `TRD-V2-API-002` | Validate `app.services.trading.__all__` against the approved public contract matrix during registry validation so internal helpers cannot leak into the public namespace. | **Modify** | Validate public facade and agent registry against separate approved contract matrices. | Internal Python exports and agent-callable tools need different controls. |
| `TRD-V2-API-003` | Return standard trading result envelopes with tool name, status, request ID, data, errors, warnings, and audit metadata. | **Modify** | Adopt the unified envelope and explicit route on route-aware operations. | V1 partially provides this. |
| `TRD-V2-API-004` | Accept an explicit trading route for every trading action that can run in simulation or live mode. | **Modify** | Adopt the unified envelope and explicit route on route-aware operations. | V1 partially provides this. |
| `TRD-V2-API-005` | Package broker connectivity checks for MT5, cTrader-style providers, paper brokers, and simulator bridges. | **Modify** | Consolidate connectivity/readiness/validation into snapshot and readiness capabilities rather than many public functions. | The behaviour is useful; the proposed surface is too broad. |
| `TRD-V2-API-006` | Package account, symbol, bid/ask, spread, trade-permission, broker-time, market-open, lot-rule, stop-distance, and free-margin checks. | **Modify** | Consolidate connectivity/readiness/validation into snapshot and readiness capabilities rather than many public functions. | The behaviour is useful; the proposed surface is too broad. |
| `TRD-V2-API-007` | Validate trading environment, strategy runtime config, broker symbol mapping, order request, order price, order size, and stop-loss/take-profit geometry. | **Modify** | Consolidate connectivity/readiness/validation into snapshot and readiness capabilities rather than many public functions. | The behaviour is useful; the proposed surface is too broad. |
| `TRD-V2-API-008` | Estimate slippage and transaction cost with the same contract for simulation and live routes. | **Add** | Add deterministic pre-trade estimates/plans and aggregate readiness using existing validation evidence. | V1 has pieces but not the complete public capability. |
| `TRD-V2-API-009` | Build deterministic trading plans from validated order requests. | **Add** | Add deterministic pre-trade estimates/plans and aggregate readiness using existing validation evidence. | V1 has pieces but not the complete public capability. |
| `TRD-V2-API-010` | Aggregate readiness checks before a trading request is accepted. | **Add** | Add deterministic pre-trade estimates/plans and aggregate readiness using existing validation evidence. | V1 has pieces but not the complete public capability. |
| `TRD-V2-API-011` | Start, stop, submit, modify, cancel, close, fill, synchronize, reconcile, compare, and report trading workflows using route-aware functions. | **Modify** | Support route-aware lifecycle operations through a focused action API; keep runtime start/stop separate from order verbs. | The list mixes session and trade lifecycle responsibilities. |
| `TRD-V2-API-012` | Provide lower-level rebuild support for approval packets, broker bridges, paper broker, simulator state, validation rules, order routing, idempotency, reconciliation, receipts, attempts, compensation, monitoring, shadow trading, and performance helpers. | **Reject** | Do not promise a blanket lower-level rebuild surface for every proposed subsystem. | It preserves complexity without a confirmed public workflow. |
| `TRD-V2-API-013` | Declare whether each exported trading name is a public agent-facing API, internal helper, bridge adapter, or experimental/internal rebuild support. | **Modify** | Document classification, routes, side effects, schemas, statuses and governance for each approved public call. | Required for a safe stable facade. |
| `TRD-V2-API-014` | Declare supported routes, side-effect class, approval requirement, idempotency requirement, stability level, required inputs, optional inputs, output `data` schema, possible `status` values, possible error codes, and audit metadata fields for each exported trading tool. | **Modify** | Document classification, routes, side effects, schemas, statuses and governance for each approved public call. | Required for a safe stable facade. |
| `TRD-V2-FR-001` | Every functional and non-functional requirement shall receive a stable requirement ID before implementation handoff, using prefixes such as `TRD-FR`, `TRD-NFR`, `TRD-EDGE`, and `TRD-TST`. | **Keep** | Assign stable final IDs and test mappings before implementation handoff. | Traceability is valuable and proportionate. |
| `TRD-V2-FR-002` | Every requirement ID shall map to at least one corresponding test ID before implementation handoff. | **Keep** | Assign stable final IDs and test mappings before implementation handoff. | Traceability is valuable and proportionate. |
| `TRD-V2-FR-003` | The trading registry shall expose only intentional agent-facing trading tools through `app.services.trading.__all__`. | **Modify** | Use separate public-facade and agent-tool matrices with one canonical envelope/error taxonomy. | V1 has partial support; V2 conflates registries and duplicates metadata. |
| `TRD-V2-FR-004` | The trading registry shall keep exports unique, callable, documented, and synchronized with tests and catalog entries. | **Modify** | Use separate public-facade and agent-tool matrices with one canonical envelope/error taxonomy. | V1 has partial support; V2 conflates registries and duplicates metadata. |
| `TRD-V2-FR-005` | Agent-facing trading tools shall return `StandardTradingEnvelope v1` as defined in this requirements document, and tests shall verify every exported tool against that schema. | **Modify** | Use separate public-facade and agent-tool matrices with one canonical envelope/error taxonomy. | V1 has partial support; V2 conflates registries and duplicates metadata. |
| `TRD-V2-FR-006` | Trading tool results shall include tool name, status, tool call ID, request ID, data, errors, warnings, and audit metadata. | **Modify** | Use separate public-facade and agent-tool matrices with one canonical envelope/error taxonomy. | V1 has partial support; V2 conflates registries and duplicates metadata. |
| `TRD-V2-FR-007` | Audit metadata shall include route, approval requirement, risk level, and side-effect classification. | **Modify** | Use separate public-facade and agent-tool matrices with one canonical envelope/error taxonomy. | V1 has partial support; V2 conflates registries and duplicates metadata. |
| `TRD-V2-FR-008` | Trading workflows shall distinguish request packaging from broker or simulator mutation. | **Modify** | Retain route/side-effect/status/trace/rejection behaviour under one unified contract and external verdict boundaries. | Core behaviour is valid; exact fields and statuses need consolidation. |
| `TRD-V2-FR-009` | For each route-aware trading action, the document shall define whether the action is non-mutating packaging, simulator-state mutation, paper-broker mutation, or live-broker mutation. | **Modify** | Retain route/side-effect/status/trace/rejection behaviour under one unified contract and external verdict boundaries. | Core behaviour is valid; exact fields and statuses need consolidation. |
| `TRD-V2-FR-010` | For each route-aware trading action, the document shall define the exact status returned for accepted, rejected, blocked, pending, sent, partially filled, filled, cancelled, failed, and unknown-outcome states where those states apply. | **Modify** | Retain route/side-effect/status/trace/rejection behaviour under one unified contract and external verdict boundaries. | Core behaviour is valid; exact fields and statuses need consolidation. |
| `TRD-V2-FR-011` | Trading workflows shall include `request_id`, `correlation_id`, `tool_call_id` where applicable, `route`, `provider`, `strategy_id` where applicable, `idempotency_key` where applicable, and UTC timestamps in every accepted, rejected, blocked, sent, unknown-outcome, and error envelope. | **Modify** | Retain route/side-effect/status/trace/rejection behaviour under one unified contract and external verdict boundaries. | Core behaviour is valid; exact fields and statuses need consolidation. |
| `TRD-V2-FR-012` | Trading workflows shall return structured rejections or blocks for invalid orders, unsupported environments, failed readiness checks, unknown routes, or unsafe live conditions. | **Modify** | Retain route/side-effect/status/trace/rejection behaviour under one unified contract and external verdict boundaries. | Core behaviour is valid; exact fields and statuses need consolidation. |
| `TRD-V2-FR-013` | Trading functions shall keep the same public names for simulation/backtest and live workflows; the route shall decide whether the request is simulated or live. | **Modify** | Retain route/side-effect/status/trace/rejection behaviour under one unified contract and external verdict boundaries. | Core behaviour is valid; exact fields and statuses need consolidation. |
| `TRD-V2-FR-014` | Trading functions shall support only approved route values and shall reject unknown routes deterministically. | **Modify** | Retain route/side-effect/status/trace/rejection behaviour under one unified contract and external verdict boundaries. | Core behaviour is valid; exact fields and statuses need consolidation. |
| `TRD-V2-FR-015` | Trading shall consume approval, risk, kill-switch, live-runtime, and authorization verdicts from their owning modules and shall not create final policy decisions, approve strategy promotion, resolve live secrets, or independently authorize production broker mutation. | **Modify** | Retain route/side-effect/status/trace/rejection behaviour under one unified contract and external verdict boundaries. | Core behaviour is valid; exact fields and statuses need consolidation. |
| `TRD-V2-FR-016` | Trading shall consume rate-limit verdicts from their owning modules and shall not independently define user, account, provider, or API rate-limit policy. | **Modify** | Retain route/side-effect/status/trace/rejection behaviour under one unified contract and external verdict boundaries. | Core behaviour is valid; exact fields and statuses need consolidation. |
| `TRD-V2-FR-017` | Trading rejection envelopes shall include machine-readable error codes, human-readable messages, affected field paths where applicable, retryability, severity, route, provider, request ID, and correlation ID. | **Modify** | Retain route/side-effect/status/trace/rejection behaviour under one unified contract and external verdict boundaries. | Core behaviour is valid; exact fields and statuses need consolidation. |
| `TRD-V2-FR-018` | Idempotency keys shall be supplied by the caller or owning workflow as part of the request for mutating or broker-impacting actions. | **Modify** | Require caller-provided idempotency keys for governed mutations, canonical material, schema version and conflict detection. | V1 currently computes keys internally in some paths. |
| `TRD-V2-FR-019` | Trading shall validate the supplied idempotency key against canonical stored material and shall not silently generate a new key for a request that requires caller-controlled idempotency. | **Modify** | Require caller-provided idempotency keys for governed mutations, canonical material, schema version and conflict detection. | V1 currently computes keys internally in some paths. |
| `TRD-V2-FR-020` | Idempotency material shall be derived from canonical JSON serialization of route, action, account, strategy, symbol, side, quantity, price, stops, target, approval reference, and request payload version. | **Modify** | Require caller-provided idempotency keys for governed mutations, canonical material, schema version and conflict detection. | V1 currently computes keys internally in some paths. |
| `TRD-V2-FR-021` | Idempotency serialization shall use UTF-8 canonical JSON with sorted keys, no insignificant whitespace, stable field ordering, UTC timestamps formatted as `YYYY-MM-DDTHH:MM:SS.ssssssZ`, Decimal values serialized as canonical strings, and no binary, object, float, NaN, Infinity, or locale-dependent values in broker-critical material. | **Modify** | Require caller-provided idempotency keys for governed mutations, canonical material, schema version and conflict detection. | V1 currently computes keys internally in some paths. |
| `TRD-V2-FR-022` | Idempotency material hashing shall use an approved cryptographic hash such as SHA-256 over the canonical UTF-8 JSON bytes and shall record the payload schema version used for hashing. | **Modify** | Require caller-provided idempotency keys for governed mutations, canonical material, schema version and conflict detection. | V1 currently computes keys internally in some paths. |
| `TRD-V2-FR-023` | Trading shall reject idempotency reuse when the same idempotency key is submitted with materially different canonical payload fields. | **Modify** | Require caller-provided idempotency keys for governed mutations, canonical material, schema version and conflict detection. | V1 currently computes keys internally in some paths. |
| `TRD-V2-FR-024` | Trading shall preserve all timestamps in timezone-aware UTC and shall include broker-time evidence separately from system-time evidence. | **Keep** | Normalize system and broker timestamps to explicit timezone-aware UTC evidence. | Necessary for approvals, freshness, hashing and reconciliation. |
| `TRD-V2-FR-025` | Broker-time evidence shall be parsed into timezone-aware UTC objects before validation, hashing, reporting, or persistence; naive broker timestamps shall require an explicitly documented broker timezone assumption or be rejected for governed/live workflows. | **Keep** | Normalize system and broker timestamps to explicit timezone-aware UTC evidence. | Necessary for approvals, freshness, hashing and reconciliation. |
| `TRD-V2-FR-026` | Trading shall normalize price, volume, commission, spread, slippage, margin, PnL, equity, and balance using Python `decimal.Decimal` before validation, hashing, reporting, or persistence. | **Modify** | Use `Decimal` for broker-critical values at domain boundaries; avoid converting every historical/reporting value unnecessarily. | Precision safety is valid but the blanket scope is excessive. |
| `TRD-V2-FR-027` | Decimal normalization shall use `ROUND_HALF_EVEN` by default, at least 28 digits of working precision, and a minimum quantization scale of 8 decimal places for broker-critical price, quantity, margin, PnL, equity, balance, and cost material unless a documented instrument or provider contract requires a stricter scale. | **Modify** | Define an approved Decimal context and instrument/provider quantization; do not mandate an arbitrary minimum eight-decimal scale for every asset. | Fixed universal scale can be wrong for instruments and currencies. |
| `TRD-V2-FR-028` | Decimal context, quantization scale, and rounding mode shall be recorded in audit metadata or deterministic validation diagnostics where they affect idempotency material, simulator results, or live request packages. | **Keep** | Record the effective precision/rounding contract when it changes deterministic material. | Supports audit and replay. |
| `TRD-V2-FR-029` | Readiness failure shall produce `status="rejected"` with `code="READINESS_FAILED"` and a bounded list of failed readiness checks. | **Modify** | Standardize readiness/concurrency failures and document thresholds after limits are approved. | Exact statuses/scopes/limits require final contract decisions. |
| `TRD-V2-FR-030` | Concurrent mutation rejection shall produce `status="blocked"` or `status="rejected"` with `code="TRADING_CONCURRENCY_CONFLICT"` and the documented concurrency scope. | **Modify** | Standardize readiness/concurrency failures and document thresholds after limits are approved. | Exact statuses/scopes/limits require final contract decisions. |
| `TRD-V2-FR-031` | Every configurable trading threshold shall document its default, allowed range, unit, owning configuration key, and consequence of violation. | **Modify** | Standardize readiness/concurrency failures and document thresholds after limits are approved. | Exact statuses/scopes/limits require final contract decisions. |
| `TRD-V2-FR-032` | `StandardTradingEnvelope v1` shall define exact fields for `status`, `message`, `data`, `errors`, `warnings`, and `audit_metadata`. | **Modify** | Replace V1 envelopes with one canonical envelope, finite status/error/warning taxonomy and unified audit metadata. | The proposed detail is valuable but must be deduplicated with Live. |
| `TRD-V2-FR-033` | `status` shall use a documented enum including `success`, `rejected`, `blocked`, `pending_approval`, `packaged`, `sent`, `partial`, `filled`, `cancelled`, `unknown_outcome`, and `error` where applicable. | **Modify** | Replace V1 envelopes with one canonical envelope, finite status/error/warning taxonomy and unified audit metadata. | The proposed detail is valuable but must be deduplicated with Live. |
| `TRD-V2-FR-034` | `packaged` shall mean a request was built and validated but not submitted to a broker or simulator. | **Modify** | Replace V1 envelopes with one canonical envelope, finite status/error/warning taxonomy and unified audit metadata. | The proposed detail is valuable but must be deduplicated with Live. |
| `TRD-V2-FR-035` | `pending_approval` shall mean a request cannot proceed until external approval state changes. | **Modify** | Replace V1 envelopes with one canonical envelope, finite status/error/warning taxonomy and unified audit metadata. | The proposed detail is valuable but must be deduplicated with Live. |
| `TRD-V2-FR-036` | `sent` shall mean a request was submitted to the route authority but final acknowledgment is not yet available. | **Modify** | Replace V1 envelopes with one canonical envelope, finite status/error/warning taxonomy and unified audit metadata. | The proposed detail is valuable but must be deduplicated with Live. |
| `TRD-V2-FR-037` | `unknown_outcome` shall mean the route authority may have accepted a request but authoritative state is unresolved and blind retry is blocked until reconciliation. | **Modify** | Replace V1 envelopes with one canonical envelope, finite status/error/warning taxonomy and unified audit metadata. | The proposed detail is valuable but must be deduplicated with Live. |
| `TRD-V2-FR-038` | Error objects shall include `code`, `message`, `field_path` where applicable, `severity`, `retryable`, `route`, `provider`, `request_id`, and `correlation_id`. | **Modify** | Replace V1 envelopes with one canonical envelope, finite status/error/warning taxonomy and unified audit metadata. | The proposed detail is valuable but must be deduplicated with Live. |
| `TRD-V2-FR-039` | Warning objects shall include `code`, `message`, `severity`, and affected context where applicable. | **Modify** | Replace V1 envelopes with one canonical envelope, finite status/error/warning taxonomy and unified audit metadata. | The proposed detail is valuable but must be deduplicated with Live. |
| `TRD-V2-FR-040` | Audit metadata shall include `tool_name`, `tool_call_id`, `request_id`, `correlation_id`, `route`, `provider`, `approval_requirement`, `approval_reference`, `risk_decision_reference`, `side_effect_class`, `idempotency_key`, `payload_version`, `created_at_utc`, and redaction status. | **Modify** | Replace V1 envelopes with one canonical envelope, finite status/error/warning taxonomy and unified audit metadata. | The proposed detail is valuable but must be deduplicated with Live. |
| `TRD-V2-FR-041` | `trading_connect` shall connect and hold one active trading/data bridge for the requested route and provider. | **Modify** | Provide route-authority bind/unbind/status behaviour using pre-authorized handles; concrete connect/login remains adapter/live-session owned. | Direct connection ownership and `ICredentialProvider` naming are implementation prescriptions. |
| `TRD-V2-FR-042` | `trading_connect(route="live")` shall accept a pre-authorized Live-owned connection/session handle or an injected `ICredentialProvider` interface and shall not independently resolve secrets, read raw credential fields, or initiate live broker login outside the Live-owned session boundary. | **Modify** | Provide route-authority bind/unbind/status behaviour using pre-authorized handles; concrete connect/login remains adapter/live-session owned. | Direct connection ownership and `ICredentialProvider` naming are implementation prescriptions. |
| `TRD-V2-FR-043` | `trading_connect(route="live")` shall verify external live-runtime enablement and session authority before creating or binding an active bridge. | **Modify** | Provide route-authority bind/unbind/status behaviour using pre-authorized handles; concrete connect/login remains adapter/live-session owned. | Direct connection ownership and `ICredentialProvider` naming are implementation prescriptions. |
| `TRD-V2-FR-044` | `trading_disconnect` shall disconnect and clear the active trading/data bridge for the requested route and provider. | **Modify** | Provide route-authority bind/unbind/status behaviour using pre-authorized handles; concrete connect/login remains adapter/live-session owned. | Direct connection ownership and `ICredentialProvider` naming are implementation prescriptions. |
| `TRD-V2-FR-045` | `trading_is_connected` shall report active bridge connection status for the requested route. | **Modify** | Provide route-authority bind/unbind/status behaviour using pre-authorized handles; concrete connect/login remains adapter/live-session owned. | Direct connection ownership and `ICredentialProvider` naming are implementation prescriptions. |
| `TRD-V2-FR-046` | `submit_order` shall use the same request shape for `sim` and `live` routes. For `route="sim"`, it may mutate simulator state according to simulator rules. For `route="live"`, it shall package a live-compatible request and shall not mutate a production broker unless an external live-runtime authority explicitly authorizes mutation and all approval, risk, kill-switch, idempotency, readiness, and reconciliation gates pass. | **Modify** | Adopt canonical route-aware action names and shared request shapes; live dispatch uses the unified live gate and sim dispatch uses simulator authority. | V1 has equivalent lower-level verbs but inconsistent names and non-live mutation behaviour. |
| `TRD-V2-FR-047` | `modify_order` shall modify an existing order using the same request shape for `sim` and `live` routes. | **Modify** | Adopt canonical route-aware action names and shared request shapes; live dispatch uses the unified live gate and sim dispatch uses simulator authority. | V1 has equivalent lower-level verbs but inconsistent names and non-live mutation behaviour. |
| `TRD-V2-FR-048` | `cancel_order` shall cancel a pending order using the same request shape for `sim` and `live` routes. | **Modify** | Adopt canonical route-aware action names and shared request shapes; live dispatch uses the unified live gate and sim dispatch uses simulator authority. | V1 has equivalent lower-level verbs but inconsistent names and non-live mutation behaviour. |
| `TRD-V2-FR-049` | `close_position` shall close an open position fully or partially using the same request shape for `sim` and `live` routes. | **Modify** | Adopt canonical route-aware action names and shared request shapes; live dispatch uses the unified live gate and sim dispatch uses simulator authority. | V1 has equivalent lower-level verbs but inconsistent names and non-live mutation behaviour. |
| `TRD-V2-FR-050` | `modify_position` shall modify stop loss or take profit on an open position using the same request shape for `sim` and `live` routes. | **Modify** | Adopt canonical route-aware action names and shared request shapes; live dispatch uses the unified live gate and sim dispatch uses simulator authority. | V1 has equivalent lower-level verbs but inconsistent names and non-live mutation behaviour. |
| `TRD-V2-FR-051` | `reduce_exposure` shall reduce exposure using the same request shape for `sim` and `live` routes. | **Modify** | Adopt canonical route-aware action names and shared request shapes; live dispatch uses the unified live gate and sim dispatch uses simulator authority. | V1 has equivalent lower-level verbs but inconsistent names and non-live mutation behaviour. |
| `TRD-V2-FR-052` | `pause_strategy` shall pause strategy trading activity using the same request shape for `sim` and `live` routes. | **Modify** | Adopt canonical route-aware action names and shared request shapes; live dispatch uses the unified live gate and sim dispatch uses simulator authority. | V1 has equivalent lower-level verbs but inconsistent names and non-live mutation behaviour. |
| `TRD-V2-FR-053` | `resume_strategy` shall resume strategy trading activity using the same request shape for `sim` and `live` routes. | **Modify** | Adopt canonical route-aware action names and shared request shapes; live dispatch uses the unified live gate and sim dispatch uses simulator authority. | V1 has equivalent lower-level verbs but inconsistent names and non-live mutation behaviour. |
| `TRD-V2-FR-054` | `sync_positions` shall synchronize route-specific position state from the active authority source. | **Modify** | Adopt canonical route-aware action names and shared request shapes; live dispatch uses the unified live gate and sim dispatch uses simulator authority. | V1 has equivalent lower-level verbs but inconsistent names and non-live mutation behaviour. |
| `TRD-V2-FR-055` | `reconcile_state` shall compare internal trading state against the route authority source. | **Modify** | Adopt canonical route-aware action names and shared request shapes; live dispatch uses the unified live gate and sim dispatch uses simulator authority. | V1 has equivalent lower-level verbs but inconsistent names and non-live mutation behaviour. |
| `TRD-V2-FR-056` | `build_trading_report` shall package route-specific trading results, readiness, receipts, reconciliation evidence, and warnings. | **Modify** | Adopt canonical route-aware action names and shared request shapes; live dispatch uses the unified live gate and sim dispatch uses simulator authority. | V1 has equivalent lower-level verbs but inconsistent names and non-live mutation behaviour. |
| `TRD-V2-FR-057` | `record_fill` shall package a fill record for simulated or observed execution. | **Add** | Add canonical receipt/fill recording shared by observed and simulated routes. | V1 has fill contracts but not a focused public operation. |
| `TRD-V2-FR-058` | `calculate_slippage` shall calculate simulated or observed slippage through the same public contract. | **Merge** | Fold slippage calculation into execution-cost/reporting capability rather than a standalone top-level tool. | It is a focused calculation, not a separate workflow. |
| `TRD-V2-FR-059` | `compare_route_vs_backtest` shall package comparison of route behavior against backtest expectations. | **Defer** | Defer route-versus-backtest comparison to analytics/shadow validation after core execution is stable. | No initial safety-critical workflow requires it. |
| `TRD-V2-FR-060` | `check_broker_connection` shall package a broker connection status check for the selected route. | **Merge** | Expose a small route snapshot/readiness API; implement individual checks as internal functions. | V1 facades prove value, but dozens of top-level calls are unnecessary. |
| `TRD-V2-FR-061` | `get_account_info` shall package account balance, equity, margin, and leverage context retrieval for the selected route. | **Merge** | Expose a small route snapshot/readiness API; implement individual checks as internal functions. | V1 facades prove value, but dozens of top-level calls are unnecessary. |
| `TRD-V2-FR-062` | `get_symbol_info` shall package broker or simulator metadata retrieval for one symbol. | **Merge** | Expose a small route snapshot/readiness API; implement individual checks as internal functions. | V1 facades prove value, but dozens of top-level calls are unnecessary. |
| `TRD-V2-FR-063` | `get_current_bid_ask` shall package current bid and ask retrieval for a trading decision. | **Merge** | Expose a small route snapshot/readiness API; implement individual checks as internal functions. | V1 facades prove value, but dozens of top-level calls are unnecessary. |
| `TRD-V2-FR-064` | `get_current_spread` shall package current spread retrieval for one symbol. | **Merge** | Expose a small route snapshot/readiness API; implement individual checks as internal functions. | V1 facades prove value, but dozens of top-level calls are unnecessary. |
| `TRD-V2-FR-065` | `get_trade_permissions` shall package account and symbol trading-permission retrieval. | **Merge** | Expose a small route snapshot/readiness API; implement individual checks as internal functions. | V1 facades prove value, but dozens of top-level calls are unnecessary. |
| `TRD-V2-FR-066` | `get_broker_time` shall package broker, paper-broker, or simulator timestamp retrieval for freshness checks. | **Merge** | Expose a small route snapshot/readiness API; implement individual checks as internal functions. | V1 facades prove value, but dozens of top-level calls are unnecessary. |
| `TRD-V2-FR-067` | `check_market_open` shall package a market-open check for a symbol. | **Merge** | Expose a small route snapshot/readiness API; implement individual checks as internal functions. | V1 facades prove value, but dozens of top-level calls are unnecessary. |
| `TRD-V2-FR-068` | `check_min_lot` shall package broker or simulator minimum-lot validation. | **Merge** | Expose a small route snapshot/readiness API; implement individual checks as internal functions. | V1 facades prove value, but dozens of top-level calls are unnecessary. |
| `TRD-V2-FR-069` | `check_max_lot` shall package broker or simulator maximum-lot validation. | **Merge** | Expose a small route snapshot/readiness API; implement individual checks as internal functions. | V1 facades prove value, but dozens of top-level calls are unnecessary. |
| `TRD-V2-FR-070` | `check_lot_step` shall package broker or simulator lot-step validation. | **Merge** | Expose a small route snapshot/readiness API; implement individual checks as internal functions. | V1 facades prove value, but dozens of top-level calls are unnecessary. |
| `TRD-V2-FR-071` | `check_stop_distance` shall package broker or simulator minimum stop-distance validation. | **Merge** | Expose a small route snapshot/readiness API; implement individual checks as internal functions. | V1 facades prove value, but dozens of top-level calls are unnecessary. |
| `TRD-V2-FR-072` | `check_free_margin` shall package free-margin availability validation before trading. | **Merge** | Expose a small route snapshot/readiness API; implement individual checks as internal functions. | V1 facades prove value, but dozens of top-level calls are unnecessary. |
| `TRD-V2-FR-073` | `validate_execution_environment` shall validate that trading targets an allowed environment and route. | **Merge** | Consolidate into `validate_order_request` plus focused private validators and readiness checks. | The proposed public helper count is excessive. |
| `TRD-V2-FR-074` | `validate_strategy_runtime_config` shall validate strategy runtime configuration before trading-plan construction. | **Merge** | Consolidate into `validate_order_request` plus focused private validators and readiness checks. | The proposed public helper count is excessive. |
| `TRD-V2-FR-075` | `validate_broker_symbol_mapping` shall validate internal symbol to broker/simulator symbol mapping. | **Merge** | Consolidate into `validate_order_request` plus focused private validators and readiness checks. | The proposed public helper count is excessive. |
| `TRD-V2-FR-076` | `validate_order_request` shall validate a proposed order request before trading-plan construction. | **Merge** | Consolidate into `validate_order_request` plus focused private validators and readiness checks. | The proposed public helper count is excessive. |
| `TRD-V2-FR-077` | `validate_order_price` shall validate that a proposed order price is positive. | **Merge** | Consolidate into `validate_order_request` plus focused private validators and readiness checks. | The proposed public helper count is excessive. |
| `TRD-V2-FR-078` | `validate_order_size` shall validate that a proposed order volume is positive. | **Merge** | Consolidate into `validate_order_request` plus focused private validators and readiness checks. | The proposed public helper count is excessive. |
| `TRD-V2-FR-079` | `validate_stop_loss_take_profit` shall validate stop-loss and take-profit placement relative to side and price. | **Merge** | Consolidate into `validate_order_request` plus focused private validators and readiness checks. | The proposed public helper count is excessive. |
| `TRD-V2-FR-080` | `estimate_slippage` shall estimate expected slippage from spread and volatility inputs. | **Add** | Add focused deterministic estimation/plan/readiness aggregation built from validated evidence. | V1 has validation and capability checks but not the complete final operation. |
| `TRD-V2-FR-081` | `estimate_transaction_cost` shall estimate spread, commission, and slippage cost. | **Add** | Add focused deterministic estimation/plan/readiness aggregation built from validated evidence. | V1 has validation and capability checks but not the complete final operation. |
| `TRD-V2-FR-082` | `build_execution_plan` shall build a deterministic trading plan from a validated order request. | **Add** | Add focused deterministic estimation/plan/readiness aggregation built from validated evidence. | V1 has validation and capability checks but not the complete final operation. |
| `TRD-V2-FR-083` | `run_execution_readiness_check` shall aggregate readiness checks and block when any required check fails. | **Add** | Add focused deterministic estimation/plan/readiness aggregation built from validated evidence. | V1 has validation and capability checks but not the complete final operation. |
| `TRD-V2-FR-084` | `trading_tool_result` shall build the standard HaruQuant result envelope for trading tools. | **Merge** | Keep these as private envelope/context/request helpers, not separate public requirements. | They support the public API but do not represent user-facing capabilities. |
| `TRD-V2-FR-085` | `trading_tool_context` shall extract standard trading tool context fields from keyword arguments. | **Merge** | Keep these as private envelope/context/request helpers, not separate public requirements. | They support the public API but do not represent user-facing capabilities. |
| `TRD-V2-FR-086` | `package_trading_request` shall package deterministic trading requests without live side effects. | **Merge** | Keep these as private envelope/context/request helpers, not separate public requirements. | They support the public API but do not represent user-facing capabilities. |
| `TRD-V2-FR-087` | Repository and persistence dependencies shall flow through dependency injection: Trading defines repository/interface contracts and persistence event payload schemas, while Infrastructure, Data, Live, or another approved owner provides concrete implementations. | **Keep** | Retain dependency injection and import-time safety; concrete persistence and side effects remain outside import paths. | Matches V1's intended boundaries. |
| `TRD-V2-FR-088` | Trading shall not import concrete database engines, open database connections, run migrations, or select persistence backends at import time. | **Keep** | Retain dependency injection and import-time safety; concrete persistence and side effects remain outside import paths. | Matches V1's intended boundaries. |
| `TRD-V2-FR-089` | Lazy trading attribute resolution shall expose approved lower-level trading service attributes without moving business logic into the package initializer. | **Reject** | Do not use lazy attribute resolution as an API design mechanism. | Explicit imports and registries are safer and easier to audit. |
| `TRD-V2-FR-090` | Importing `app.services.trading` shall not connect to brokers, resolve secrets, perform network calls, perform database writes, start background workers, or mutate simulator/live state. | **Keep** | Retain dependency injection and import-time safety; concrete persistence and side effects remain outside import paths. | Matches V1's intended boundaries. |
| `TRD-V2-FR-091` | `ApprovalPacket` shall represent a full approval packet and report completeness/missing fields. | **Reject** | Do not implement approval packet models/builders in Trading; consume the governance contract by reference. | Approval construction belongs to governance. |
| `TRD-V2-FR-092` | `ApprovalRequest` shall model an approval request. | **Reject** | Do not implement approval packet models/builders in Trading; consume the governance contract by reference. | Approval construction belongs to governance. |
| `TRD-V2-FR-093` | `ApprovalPacketBuilder` shall build approval packets from action, reason, evidence, confidence, uncertainty, policy checks, risk class, alternatives, expected impact, rollback plan, and escalation triggers. | **Reject** | Do not implement approval packet models/builders in Trading; consume the governance contract by reference. | Approval construction belongs to governance. |
| `TRD-V2-FR-094` | Trading shall consume externally owned approval verdicts and approval references. | **Keep** | Consume externally owned approval/risk/governance verdicts and prohibit direct Conversation execution. | This is a critical boundary. |
| `TRD-V2-FR-095` | Trading may package local approval evidence DTOs for execution requests but shall not own approval voting policy, approval-state authority, or approval persistence schema. | **Keep** | Consume externally owned approval/risk/governance verdicts and prohibit direct Conversation execution. | This is a critical boundary. |
| `TRD-V2-FR-096` | `ApprovalCreationService`, `ApprovalVoteService`, `ApprovalStateMachine`, and `OverrideRequestService` requirements shall be treated as external governance-module dependencies unless a later approved decision narrows them to Trading-owned DTO or adapter behavior. | **Keep** | Consume externally owned approval/risk/governance verdicts and prohibit direct Conversation execution. | This is a critical boundary. |
| `TRD-V2-FR-097` | Trade action governance shall consume externally owned approval state, risk decision, readiness, and kill-switch state before any route mutation. | **Keep** | Consume externally owned approval/risk/governance verdicts and prohibit direct Conversation execution. | This is a critical boundary. |
| `TRD-V2-FR-098` | AI chat order drafts shall become governed route-aware trading requests only through approved governance and execution boundaries; Trading shall not grant Conversation direct execution authority. | **Keep** | Consume externally owned approval/risk/governance verdicts and prohibit direct Conversation execution. | This is a critical boundary. |
| `TRD-V2-FR-099` | `assemble_execution_intent` shall build a canonical trading intent linked to approved proposal and risk decision. | **Modify** | Build one canonical execution request from approved references and validate it immediately before route dispatch; document conflict scope. | V1 has request envelopes and idempotency, but the final contract needs caller-controlled references. |
| `TRD-V2-FR-100` | Trading intent assembly shall include route, idempotency material, proposal/risk references, action, symbol, side, quantity, price, stops, target, and trace metadata. | **Modify** | Build one canonical execution request from approved references and validate it immediately before route dispatch; document conflict scope. | V1 has request envelopes and idempotency, but the final contract needs caller-controlled references. |
| `TRD-V2-FR-101` | Order routing shall choose an eligible route adapter only after policy, broker, readiness, and safety context are available. | **Modify** | Build one canonical execution request from approved references and validate it immediately before route dispatch; document conflict scope. | V1 has request envelopes and idempotency, but the final contract needs caller-controlled references. |
| `TRD-V2-FR-102` | Idempotency helpers shall produce stable material and detect conflicts between duplicate keys and differing payloads. | **Modify** | Build one canonical execution request from approved references and validate it immediately before route dispatch; document conflict scope. | V1 has request envelopes and idempotency, but the final contract needs caller-controlled references. |
| `TRD-V2-FR-103` | Pre-send validation shall verify that a trading request is still valid immediately before route submission. | **Modify** | Build one canonical execution request from approved references and validate it immediately before route dispatch; document conflict scope. | V1 has request envelopes and idempotency, but the final contract needs caller-controlled references. |
| `TRD-V2-FR-104` | Readiness services shall fail closed when required market/account/broker/risk context is missing or stale. | **Modify** | Build one canonical execution request from approved references and validate it immediately before route dispatch; document conflict scope. | V1 has request envelopes and idempotency, but the final contract needs caller-controlled references. |
| `TRD-V2-FR-105` | Route adapters shall document the serialization scope used for conflicting requests, such as route plus account plus strategy plus symbol, route plus order ticket, route plus position ticket, or idempotency key. | **Modify** | Build one canonical execution request from approved references and validate it immediately before route dispatch; document conflict scope. | V1 has request envelopes and idempotency, but the final contract needs caller-controlled references. |
| `TRD-V2-FR-106` | `BaseExecutionBridge` shall define heartbeat and place-order bridge behavior for route adapters. | **Modify** | Define only the minimal route-adapter capability protocol needed by Trading; remove legacy `Trade` class preservation as a requirement. | Behaviour matters, not legacy class structure. |
| `TRD-V2-FR-107` | `MT5Bridge` shall provide MT5 connectivity, account info, symbol info, tick reads, positions, orders, and fail-closed mutation methods. | **Reject** | Do not duplicate concrete MT5, cTrader or paper/simulator implementations inside Trading; consume approved adapters/authorities. | V1 already uses a broker router and the system has broker/simulator domains. |
| `TRD-V2-FR-108` | `CTraderBridge` shall provide cTrader symbol/status normalization and fail-closed bridge behavior. | **Reject** | Do not duplicate concrete MT5, cTrader or paper/simulator implementations inside Trading; consume approved adapters/authorities. | V1 already uses a broker router and the system has broker/simulator domains. |
| `TRD-V2-FR-109` | `PaperBroker` shall provide deterministic paper order placement, pending-order processing, and account snapshots. | **Reject** | Do not duplicate concrete MT5, cTrader or paper/simulator implementations inside Trading; consume approved adapters/authorities. | V1 already uses a broker router and the system has broker/simulator domains. |
| `TRD-V2-FR-110` | `Trade` shall retain low-level MT5/simulator order request, check, send, result, open, modify, delete, close, and partial-close behavior. | **Modify** | Define only the minimal route-adapter capability protocol needed by Trading; remove legacy `Trade` class preservation as a requirement. | Behaviour matters, not legacy class structure. |
| `TRD-V2-FR-111` | `trading_place_order` shall submit a broker or simulator order through a fail-closed route bridge. | **Merge** | Map these low-level verbs into the canonical submit/modify/cancel action functions and private route dispatch. | Duplicate public order APIs would create drift. |
| `TRD-V2-FR-112` | `place_market_order` shall place a market order through the active route bridge when allowed. | **Merge** | Map these low-level verbs into the canonical submit/modify/cancel action functions and private route dispatch. | Duplicate public order APIs would create drift. |
| `TRD-V2-FR-113` | `place_pending_order` shall place a pending order through the active route bridge or simulator mode when allowed. | **Merge** | Map these low-level verbs into the canonical submit/modify/cancel action functions and private route dispatch. | Duplicate public order APIs would create drift. |
| `TRD-V2-FR-114` | `modify_pending_order` shall modify price, stop loss, take profit, or expiration on a pending order only when bridge support and gates allow it. | **Merge** | Map these low-level verbs into the canonical submit/modify/cancel action functions and private route dispatch. | Duplicate public order APIs would create drift. |
| `TRD-V2-FR-115` | `cancel_pending_order` shall cancel a pending order through the active route bridge when allowed. | **Merge** | Map these low-level verbs into the canonical submit/modify/cancel action functions and private route dispatch. | Duplicate public order APIs would create drift. |
| `TRD-V2-FR-116` | Trading snapshot functions shall return JSON-safe account, position, order, history, symbol, terminal, margin, profit, and deal-history information. | **Modify** | Retain JSON-safe route snapshots but return structured unavailable/stale errors instead of silent neutral defaults. | V1 proves value but hides read failures. |
| `TRD-V2-FR-117` | `validate_action_type` shall validate request action and order type compatibility. | **Merge** | Implement this rule inside focused order/operation validation; do not expose every rule as a public capability. | Private helpers satisfy the behaviour with less API surface. |
| `TRD-V2-FR-118` | `validate_submission_inputs` shall validate symbol, volume, symbol metadata, bid, and ask inputs. | **Merge** | Implement this rule inside focused order/operation validation; do not expose every rule as a public capability. | Private helpers satisfy the behaviour with less API surface. |
| `TRD-V2-FR-119` | `validate_trade_request` shall validate a full trade request against account and symbol metadata. | **Merge** | Implement this rule inside focused order/operation validation; do not expose every rule as a public capability. | Private helpers satisfy the behaviour with less API surface. |
| `TRD-V2-FR-120` | `validate_symbol` shall validate symbol availability in trading context. | **Merge** | Implement this rule inside focused order/operation validation; do not expose every rule as a public capability. | Private helpers satisfy the behaviour with less API surface. |
| `TRD-V2-FR-121` | `validate_volume_basic` shall validate basic volume positivity. | **Merge** | Implement this rule inside focused order/operation validation; do not expose every rule as a public capability. | Private helpers satisfy the behaviour with less API surface. |
| `TRD-V2-FR-122` | `validate_volume_symbol_limits` shall validate volume against symbol min/max rules. | **Merge** | Implement this rule inside focused order/operation validation; do not expose every rule as a public capability. | Private helpers satisfy the behaviour with less API surface. |
| `TRD-V2-FR-123` | `validate_volume_step` shall validate broker volume step alignment. | **Merge** | Implement this rule inside focused order/operation validation; do not expose every rule as a public capability. | Private helpers satisfy the behaviour with less API surface. |
| `TRD-V2-FR-124` | `validate_volume_format` shall validate volume text formatting. | **Merge** | Implement this rule inside focused order/operation validation; do not expose every rule as a public capability. | Private helpers satisfy the behaviour with less API surface. |
| `TRD-V2-FR-125` | `validate_price_format` shall validate price text formatting. | **Merge** | Implement this rule inside focused order/operation validation; do not expose every rule as a public capability. | Private helpers satisfy the behaviour with less API surface. |
| `TRD-V2-FR-126` | `validate_volume` shall validate volume using context and rule settings. | **Merge** | Implement this rule inside focused order/operation validation; do not expose every rule as a public capability. | Private helpers satisfy the behaviour with less API surface. |
| `TRD-V2-FR-127` | `validate_price` shall validate price using context and rule settings. | **Merge** | Implement this rule inside focused order/operation validation; do not expose every rule as a public capability. | Private helpers satisfy the behaviour with less API surface. |
| `TRD-V2-FR-128` | `validate_order_type` shall validate supported order type tokens. | **Merge** | Implement this rule inside focused order/operation validation; do not expose every rule as a public capability. | Private helpers satisfy the behaviour with less API surface. |
| `TRD-V2-FR-129` | `validate_magic` shall validate expert/magic number rules. | **Merge** | Implement this rule inside focused order/operation validation; do not expose every rule as a public capability. | Private helpers satisfy the behaviour with less API surface. |
| `TRD-V2-FR-130` | `validate_slippage` shall validate allowed slippage relative to requested price and order type. | **Merge** | Implement this rule inside focused order/operation validation; do not expose every rule as a public capability. | Private helpers satisfy the behaviour with less API surface. |
| `TRD-V2-FR-131` | `validate_expiration_unix` shall validate expiration timestamp against current time. | **Merge** | Implement this rule inside focused order/operation validation; do not expose every rule as a public capability. | Private helpers satisfy the behaviour with less API surface. |
| `TRD-V2-FR-132` | `validate_expiration_mode` shall validate order expiration mode. | **Merge** | Implement this rule inside focused order/operation validation; do not expose every rule as a public capability. | Private helpers satisfy the behaviour with less API surface. |
| `TRD-V2-FR-133` | `validate_timeframe` shall validate timeframe tokens. | **Reject** | Generic timeframe and date-range validation belongs to Data/Research/Simulation unless required by a concrete trading operation. | No core trading action workflow requires generic validators. |
| `TRD-V2-FR-134` | `validate_date_range_unix` shall validate date-range bounds. | **Reject** | Generic timeframe and date-range validation belongs to Data/Research/Simulation unless required by a concrete trading operation. | No core trading action workflow requires generic validators. |
| `TRD-V2-FR-135` | `validate_stop_loss` shall validate stop-loss geometry and broker distance/freeze rules. | **Merge** | Implement this rule inside focused order/operation validation; do not expose every rule as a public capability. | Private helpers satisfy the behaviour with less API surface. |
| `TRD-V2-FR-136` | `validate_take_profit` shall validate take-profit geometry and broker distance/freeze rules. | **Merge** | Implement this rule inside focused order/operation validation; do not expose every rule as a public capability. | Private helpers satisfy the behaviour with less API surface. |
| `TRD-V2-FR-137` | `validate_trade_request_payload` shall validate canonical trade request payloads. | **Merge** | Implement this rule inside focused order/operation validation; do not expose every rule as a public capability. | Private helpers satisfy the behaviour with less API surface. |
| `TRD-V2-FR-138` | `validate_credentials` shall validate credential payload completeness without exposing secrets. | **Reject** | Credential completeness is validated by the approved session/secret owner; Trading validates only an opaque authorized handle/reference. | Prevents Trading from handling secret payloads. |
| `TRD-V2-FR-139` | `validate_margin` shall validate available margin against required margin. | **Merge** | Implement this rule inside focused order/operation validation; do not expose every rule as a public capability. | Private helpers satisfy the behaviour with less API surface. |
| `TRD-V2-FR-140` | `validate_ticket` shall validate broker ticket identifiers. | **Merge** | Implement this rule inside focused order/operation validation; do not expose every rule as a public capability. | Private helpers satisfy the behaviour with less API surface. |
| `TRD-V2-FR-141` | `validate_max_orders` shall validate open/pending order count against limits. | **Merge** | Implement this rule inside focused order/operation validation; do not expose every rule as a public capability. | Private helpers satisfy the behaviour with less API surface. |
| `TRD-V2-FR-142` | `validate_symbol_volume` shall validate total symbol volume against limits. | **Merge** | Implement this rule inside focused order/operation validation; do not expose every rule as a public capability. | Private helpers satisfy the behaviour with less API surface. |
| `TRD-V2-FR-143` | Open, modify, delete, close, and partial-close validation helpers shall enforce operation-specific preconditions. | **Merge** | Implement this rule inside focused order/operation validation; do not expose every rule as a public capability. | Private helpers satisfy the behaviour with less API surface. |
| `TRD-V2-FR-144` | Simulator state shall own simulated account, position, order, history, symbol, margin, equity, balance, and trade-record state. | **Reject** | Do not place simulator engine state/monitor loops inside Trading; Trading dispatches the `sim` route to the simulator authority. | Avoids duplicating the Simulator domain. |
| `TRD-V2-FR-145` | `order_send` shall process simulated trade requests and update simulator state. | **Reject** | Do not place simulator engine state/monitor loops inside Trading; Trading dispatches the `sim` route to the simulator authority. | Avoids duplicating the Simulator domain. |
| `TRD-V2-FR-146` | `monitor_positions` shall update open positions and auto-close on stop loss or take profit when allowed. | **Reject** | Do not place simulator engine state/monitor loops inside Trading; Trading dispatches the `sim` route to the simulator authority. | Avoids duplicating the Simulator domain. |
| `TRD-V2-FR-147` | `monitor_pending_orders` shall expire and trigger pending orders when allowed. | **Reject** | Do not place simulator engine state/monitor loops inside Trading; Trading dispatches the `sim` route to the simulator authority. | Avoids duplicating the Simulator domain. |
| `TRD-V2-FR-148` | `monitor_account` shall update account aggregates from open positions. | **Reject** | Do not place simulator engine state/monitor loops inside Trading; Trading dispatches the `sim` route to the simulator authority. | Avoids duplicating the Simulator domain. |
| `TRD-V2-FR-149` | Trade records, equity points, run results, and backtest result containers shall serialize to JSON-safe dictionaries. | **Keep** | Require JSON-safe canonical records at the trading boundary. | Needed for persistence and analytics. |
| `TRD-V2-FR-150` | Receipt builders shall preserve broker/order/deal identifiers, requested and filled values, status, timestamps, provider, route, and trace metadata. | **Modify** | Retain canonical receipts, authority evidence, send-attempt records, reconciliation comparison and retry guard using externally implemented stores. | V1 already provides most behaviour; contracts need consolidation. |
| `TRD-V2-FR-151` | Authority-state propagation shall identify whether broker receipt state, simulator state, or reconciliation state is currently authoritative. | **Modify** | Retain canonical receipts, authority evidence, send-attempt records, reconciliation comparison and retry guard using externally implemented stores. | V1 already provides most behaviour; contracts need consolidation. |
| `TRD-V2-FR-152` | Send-attempt persistence shall hash submitted payloads and preserve retry/audit context. | **Modify** | Retain canonical receipts, authority evidence, send-attempt records, reconciliation comparison and retry guard using externally implemented stores. | V1 already provides most behaviour; contracts need consolidation. |
| `TRD-V2-FR-153` | Broker-truth and simulator-truth snapshots shall normalize positions, orders, account, and timestamp evidence. | **Modify** | Retain canonical receipts, authority evidence, send-attempt records, reconciliation comparison and retry guard using externally implemented stores. | V1 already provides most behaviour; contracts need consolidation. |
| `TRD-V2-FR-154` | Reconciliation comparison shall detect missing, extra, mismatched, and stale authority/internal records. | **Modify** | Retain canonical receipts, authority evidence, send-attempt records, reconciliation comparison and retry guard using externally implemented stores. | V1 already provides most behaviour; contracts need consolidation. |
| `TRD-V2-FR-155` | Reconciliation persistence event payloads shall preserve reconciliation runs, mismatches, incidents, and evidence references through externally owned persistence interfaces. | **Modify** | Retain canonical receipts, authority evidence, send-attempt records, reconciliation comparison and retry guard using externally implemented stores. | V1 already provides most behaviour; contracts need consolidation. |
| `TRD-V2-FR-156` | Startup reconciliation inputs shall be available before live recovery or live mutation workflows. | **Modify** | Retain canonical receipts, authority evidence, send-attempt records, reconciliation comparison and retry guard using externally implemented stores. | V1 already provides most behaviour; contracts need consolidation. |
| `TRD-V2-FR-157` | Retry guard behavior shall prevent unsafe blind retries after unknown route outcomes. | **Modify** | Retain canonical receipts, authority evidence, send-attempt records, reconciliation comparison and retry guard using externally implemented stores. | V1 already provides most behaviour; contracts need consolidation. |
| `TRD-V2-FR-158` | Reconciliation incidents shall package discrepancy severity, evidence, action requirement, and audit context. | **Modify** | Retain canonical receipts, authority evidence, send-attempt records, reconciliation comparison and retry guard using externally implemented stores. | V1 already provides most behaviour; contracts need consolidation. |
| `TRD-V2-FR-159` | Tool health monitoring shall track trading tool availability and failure status. | **Modify** | Retain a minimal monitoring event surface for health, timeout, staleness, ingestion, incidents and latency. | V1 has components but no confirmed runtime composition. |
| `TRD-V2-FR-160` | Workflow timeout monitoring shall detect stale or overdue trading workflows. | **Modify** | Retain a minimal monitoring event surface for health, timeout, staleness, ingestion, incidents and latency. | V1 has components but no confirmed runtime composition. |
| `TRD-V2-FR-161` | Stale-state monitoring shall identify stale market, account, broker, approval, or risk state. | **Modify** | Retain a minimal monitoring event surface for health, timeout, staleness, ingestion, incidents and latency. | V1 has components but no confirmed runtime composition. |
| `TRD-V2-FR-162` | Ingestion monitoring shall track whether required trading inputs are arriving. | **Modify** | Retain a minimal monitoring event surface for health, timeout, staleness, ingestion, incidents and latency. | V1 has components but no confirmed runtime composition. |
| `TRD-V2-FR-163` | Incident classification shall classify trading incidents by severity and action need. | **Modify** | Retain a minimal monitoring event surface for health, timeout, staleness, ingestion, incidents and latency. | V1 has components but no confirmed runtime composition. |
| `TRD-V2-FR-164` | Latency helpers shall record trading timing and latency diagnostics. | **Modify** | Retain a minimal monitoring event surface for health, timeout, staleness, ingestion, incidents and latency. | V1 has components but no confirmed runtime composition. |
| `TRD-V2-FR-165` | Snapshot caches shall preserve recent trading performance snapshots. | **Defer** | Defer performance snapshot caching until a readiness/audit workflow proves it necessary. | Premature state and invalidation complexity. |
| `TRD-V2-FR-166` | Cost enforcement shall consume externally owned per-request, workflow, and session budget verdicts and package cost entries for persistence or monitoring. | **Modify** | Consume externally owned budget limits/verdicts and enforce them before send; emit cost evidence. | V1 CostController is disconnected and should not own policy. |
| `TRD-V2-FR-167` | Trading shall validate and package compensation plans for partial or failed side-effect paths. | **Defer** | Defer the generalized compensation catalog/registry; preserve only explicit approved emergency actions through the normal gate. | No approved compensation catalog or ownership contract exists. |
| `TRD-V2-FR-168` | Execution of any compensation step that can mutate live broker state shall require the same external live-runtime, approval, risk, kill-switch, idempotency, and reconciliation gates as any other live mutation. | **Defer** | Defer the generalized compensation catalog/registry; preserve only explicit approved emergency actions through the normal gate. | No approved compensation catalog or ownership contract exists. |
| `TRD-V2-FR-169` | Order compensation shall support pending-order cancellation or offsetting-order style remediation packages where configured. | **Defer** | Defer the generalized compensation catalog/registry; preserve only explicit approved emergency actions through the normal gate. | No approved compensation catalog or ownership contract exists. |
| `TRD-V2-FR-170` | Position compensation shall support position close or size adjustment remediation packages where configured. | **Defer** | Defer the generalized compensation catalog/registry; preserve only explicit approved emergency actions through the normal gate. | No approved compensation catalog or ownership contract exists. |
| `TRD-V2-FR-171` | Compensation registry shall map action classes to compensation plans and report registered compensation coverage. | **Defer** | Defer the generalized compensation catalog/registry; preserve only explicit approved emergency actions through the normal gate. | No approved compensation catalog or ownership contract exists. |
| `TRD-V2-NFR-001` | Trading shall fail closed on missing risk context, stale broker/account state, active kill switch, reconciliation mismatch, idempotency conflict, disabled live flag, unknown route, or unknown route result. | **Modify** | Retain the safety property under the unified route-aware trading contract and finite envelope taxonomy. | V1 covers much of it but has gaps and duplicate types. |
| `TRD-V2-NFR-002` | Live mutations shall be disabled by default even when trading functions support `route="live"`. | **Modify** | Retain the safety property under the unified route-aware trading contract and finite envelope taxonomy. | V1 covers much of it but has gaps and duplicate types. |
| `TRD-V2-NFR-003` | Critical live and kill-switch actions shall require explicit approval context before the live route can mutate broker state. | **Modify** | Retain the safety property under the unified route-aware trading contract and finite envelope taxonomy. | V1 covers much of it but has gaps and duplicate types. |
| `TRD-V2-NFR-004` | Broker calls shall be isolated behind approved adapters or bridges. | **Modify** | Retain the safety property under the unified route-aware trading contract and finite envelope taxonomy. | V1 covers much of it but has gaps and duplicate types. |
| `TRD-V2-NFR-005` | Trading outputs shall be structured, traceable, redacted, and JSON-safe. | **Modify** | Retain the safety property under the unified route-aware trading contract and finite envelope taxonomy. | V1 covers much of it but has gaps and duplicate types. |
| `TRD-V2-NFR-006` | Trading errors shall use documented machine-readable error codes, stable status values, deterministic field paths where applicable, retryability flags, severity, route, provider, request ID, correlation ID, and redacted diagnostic context. | **Modify** | Retain the safety property under the unified route-aware trading contract and finite envelope taxonomy. | V1 covers much of it but has gaps and duplicate types. |
| `TRD-V2-NFR-007` | Secrets, credentials, tokens, authorization headers, private broker payloads, and raw approval packets shall not leak through logs, errors, notifications, metrics, reports, or chat. | **Modify** | Retain the safety property under the unified route-aware trading contract and finite envelope taxonomy. | V1 covers much of it but has gaps and duplicate types. |
| `TRD-V2-NFR-008` | Idempotency shall prevent unsafe duplicate trading and shall not be mistaken for exactly-once broker semantics. | **Modify** | Retain the safety property under the unified route-aware trading contract and finite envelope taxonomy. | V1 covers much of it but has gaps and duplicate types. |
| `TRD-V2-NFR-009` | Unknown broker or simulator outcomes shall block blind retries until reconciliation resolves state. | **Modify** | Retain the safety property under the unified route-aware trading contract and finite envelope taxonomy. | V1 covers much of it but has gaps and duplicate types. |
| `TRD-V2-NFR-010` | Reconciliation shall prefer the configured authority source when determining route state. | **Modify** | Retain the safety property under the unified route-aware trading contract and finite envelope taxonomy. | V1 covers much of it but has gaps and duplicate types. |
| `TRD-V2-NFR-011` | Simulation, shadow, and live routes shall remain separate even when they share the same function names. | **Modify** | Retain the safety property under the unified route-aware trading contract and finite envelope taxonomy. | V1 covers much of it but has gaps and duplicate types. |
| `TRD-V2-NFR-012` | Trading tools shall preserve clear side-effect flags and approval requirements. | **Modify** | Retain the safety property under the unified route-aware trading contract and finite envelope taxonomy. | V1 covers much of it but has gaps and duplicate types. |
| `TRD-V2-NFR-013` | Trading monitoring shall emit structured events for stale state, timeout, health failure, incident, latency, and cost-budget conditions. Each event shall include route, provider, request ID, correlation ID, tool name, status, severity, side-effect class, latency duration where applicable, and redacted diagnostic context. | **Modify** | Emit a minimal structured monitoring event contract; avoid requiring every field on events where it is not meaningful. | The behaviour is valuable but the universal schema is excessive. |
| `TRD-V2-NFR-014` | Compensation behavior shall be explicit, validated, auditable, and bounded. | **Defer** | Defer generalized compensation behaviour pending an approved catalog. | No current workflow justifies it. |
| `TRD-V2-NFR-015` | Trading shall report readiness as failed whenever any required readiness check is failed, missing, stale, or unsupported; successful readiness may be reported only when all required checks pass and none are unknown. | **Keep** | Retain this fail-closed, traceability or coordination requirement. | It directly supports safe workflows. |
| `TRD-V2-NFR-016` | Public registry changes shall remain covered by tests and catalog updates. | **Keep** | Retain this fail-closed, traceability or coordination requirement. | It directly supports safe workflows. |
| `TRD-V2-NFR-017` | Trading functions shall reject market/account/broker/risk context older than the documented freshness threshold and shall include the stale field name, observed timestamp, threshold, route, and provider in the rejection envelope. | **Keep** | Retain this fail-closed, traceability or coordination requirement. | It directly supports safe workflows. |
| `TRD-V2-NFR-018` | Trading shall enforce documented timeout budgets for broker checks, readiness aggregation, send attempts, reconciliation, compensation, and report generation. | **Keep** | Retain this fail-closed, traceability or coordination requirement. | It directly supports safe workflows. |
| `TRD-V2-NFR-019` | Trading shall enforce documented maximum payload size, maximum batch size, maximum readiness-check count, and maximum reconciliation snapshot size. | **Modify** | Enforce bounded inputs and snapshots, with exact limits decided from provider/benchmark evidence. | Limits are needed; proposed universal values are not yet approved. |
| `TRD-V2-NFR-020` | Trading shall use a documented concurrency guard or return `TRADING_CONCURRENCY_CONFLICT` for concurrent mutating requests that target the same route, account, strategy, symbol, order ticket, position ticket, or idempotency key when concurrent execution could create duplicate or conflicting exposure. | **Keep** | Retain this fail-closed, traceability or coordination requirement. | It directly supports safe workflows. |
| `TRD-V2-NFR-021` | Trading shall reject retry exhaustion with deterministic failure status and audit metadata. | **Keep** | Retain this fail-closed, traceability or coordination requirement. | It directly supports safe workflows. |
| `TRD-V2-NFR-022` | Redaction behavior shall cover nested exceptions, nested broker payloads, serialized approval evidence, logs, metrics, reports, notifications, chat responses, and audit metadata. | **Keep** | Retain this fail-closed, traceability or coordination requirement. | It directly supports safe workflows. |
| `TRD-V2-NFR-023` | Default broker operation timeout shall be 10 seconds unless an approved module-specific contract overrides it. | **Open Decision** | Do not approve the concrete default/target until provider contracts, benchmark hardware and cross-domain freshness/concurrency ownership are resolved. | The documents contain conflicting or unvalidated values. |
| `TRD-V2-NFR-024` | Default broker check timeout shall be 5 seconds unless an approved module-specific contract overrides it. | **Open Decision** | Do not approve the concrete default/target until provider contracts, benchmark hardware and cross-domain freshness/concurrency ownership are resolved. | The documents contain conflicting or unvalidated values. |
| `TRD-V2-NFR-025` | Default market data freshness threshold shall be 5 seconds unless an approved module-specific contract overrides it. | **Open Decision** | Do not approve the concrete default/target until provider contracts, benchmark hardware and cross-domain freshness/concurrency ownership are resolved. | The documents contain conflicting or unvalidated values. |
| `TRD-V2-NFR-026` | Default maximum request payload size shall be 1 MiB unless an approved module-specific contract overrides it. | **Open Decision** | Do not approve the concrete default/target until provider contracts, benchmark hardware and cross-domain freshness/concurrency ownership are resolved. | The documents contain conflicting or unvalidated values. |
| `TRD-V2-NFR-027` | Default maximum readiness check count shall be 20 unless an approved module-specific contract overrides it. | **Open Decision** | Do not approve the concrete default/target until provider contracts, benchmark hardware and cross-domain freshness/concurrency ownership are resolved. | The documents contain conflicting or unvalidated values. |
| `TRD-V2-NFR-028` | Default maximum reconciliation snapshot size shall be 10,000 records or 5 MiB, whichever limit is reached first, unless an approved module-specific contract overrides it. | **Open Decision** | Do not approve the concrete default/target until provider contracts, benchmark hardware and cross-domain freshness/concurrency ownership are resolved. | The documents contain conflicting or unvalidated values. |
| `TRD-V2-NFR-029` | Proposed readiness aggregation engineering baseline: p99 readiness aggregation target is less than 50 ms under the approved normal-load benchmark profile; this target remains Pending until the benchmark profile and reference hardware are approved. | **Open Decision** | Do not approve the concrete default/target until provider contracts, benchmark hardware and cross-domain freshness/concurrency ownership are resolved. | The documents contain conflicting or unvalidated values. |
| `TRD-V2-NFR-030` | Default concurrency scope for order submission shall be route plus account plus strategy plus symbol plus side plus idempotency key until a more specific route contract is approved. | **Open Decision** | Do not approve the concrete default/target until provider contracts, benchmark hardware and cross-domain freshness/concurrency ownership are resolved. | The documents contain conflicting or unvalidated values. |
| `TRD-V2-TST-001` | Requirement-to-test mapping shall prove every `TRD-FR`, `TRD-NFR`, and `TRD-EDGE` requirement has at least one test ID before Builder handoff. | **Add** | Add or expand this test at the final public contract/gate/integration boundary. | V1 testing exists but the audit does not prove full V2 coverage. |
| `TRD-V2-TST-002` | Public tool contract tests shall prove every exported trading tool matches the documented public tool contract matrix. | **Add** | Add or expand this test at the final public contract/gate/integration boundary. | V1 testing exists but the audit does not prove full V2 coverage. |
| `TRD-V2-TST-003` | Public tool contract tests shall prove every exported public tool returns only documented status values. | **Add** | Add or expand this test at the final public contract/gate/integration boundary. | V1 testing exists but the audit does not prove full V2 coverage. |
| `TRD-V2-TST-004` | Public tool contract tests shall prove internal helpers are not accidentally exported through `app.services.trading.__all__`. | **Add** | Add or expand this test at the final public contract/gate/integration boundary. | V1 testing exists but the audit does not prove full V2 coverage. |
| `TRD-V2-TST-005` | Public tool contract tests shall be generated from, or mechanically checked against, the public tool contract matrix. | **Add** | Add or expand this test at the final public contract/gate/integration boundary. | V1 testing exists but the audit does not prove full V2 coverage. |
| `TRD-V2-TST-006` | API signature tests shall verify exact documented signatures, required fields, optional fields, defaults, enum values, and `data` schemas for public agent-facing tools. | **Add** | Add or expand this test at the final public contract/gate/integration boundary. | V1 testing exists but the audit does not prove full V2 coverage. |
| `TRD-V2-TST-007` | Registry tests shall prove `app.services.trading.__all__` matches the approved agent-facing tool surface. | **Add** | Add or expand this test at the final public contract/gate/integration boundary. | V1 testing exists but the audit does not prove full V2 coverage. |
| `TRD-V2-TST-008` | Callable/docstring tests shall cover every exported trading service tool. | **Add** | Add or expand this test at the final public contract/gate/integration boundary. | V1 testing exists but the audit does not prove full V2 coverage. |
| `TRD-V2-TST-009` | Standard-envelope tests shall cover every exported trading service tool and `StandardTradingEnvelope v1` serialization for success, rejected, blocked, pending approval, packaged, sent, partial, unknown outcome, and error statuses. | **Add** | Add or expand this test at the final public contract/gate/integration boundary. | V1 testing exists but the audit does not prove full V2 coverage. |
| `TRD-V2-TST-010` | Rejection-envelope tests shall prove every rejection contains error code, message, field path when applicable, severity, retryability, route, provider, request ID, and correlation ID. | **Add** | Add or expand this test at the final public contract/gate/integration boundary. | V1 testing exists but the audit does not prove full V2 coverage. |
| `TRD-V2-TST-011` | Route tests shall prove all shared trading verbs accept `route="sim"` and `route="live"` where applicable and reject unknown routes. | **Add** | Add or expand this test at the final public contract/gate/integration boundary. | V1 testing exists but the audit does not prove full V2 coverage. |
| `TRD-V2-TST-012` | Critical live-route tests shall prove shared trading functions block without approval ID when the live action requires approval. | **Add** | Add or expand this test at the final public contract/gate/integration boundary. | V1 testing exists but the audit does not prove full V2 coverage. |
| `TRD-V2-TST-013` | Order-request validation tests shall cover missing symbol, invalid side, zero/negative volume, invalid price, invalid stops, invalid environment, unsupported route, and unsupported broker mapping. | **Add** | Add or expand this test at the final public contract/gate/integration boundary. | V1 testing exists but the audit does not prove full V2 coverage. |
| `TRD-V2-TST-014` | Readiness aggregation tests shall prove failed checks block trading. | **Add** | Add or expand this test at the final public contract/gate/integration boundary. | V1 testing exists but the audit does not prove full V2 coverage. |
| `TRD-V2-TST-015` | Broker-connectivity packaging tests shall cover account, symbol, quote, spread, permissions, broker time, market open, lot rules, stop distance, and margin. | **Add** | Add or expand this test at the final public contract/gate/integration boundary. | V1 testing exists but the audit does not prove full V2 coverage. |
| `TRD-V2-TST-016` | Simulation route tests shall cover start, stop, submit, modify, cancel, close, fill record, slippage, route/backtest comparison, and report packaging. | **Add** | Add or expand this test at the final public contract/gate/integration boundary. | V1 testing exists but the audit does not prove full V2 coverage. |
| `TRD-V2-TST-017` | Live route tests with mocks shall prove submit, modify, cancel, close, pause, resume, exposure reduction, sync, reconciliation, and reports require approval and fail closed when context is missing. | **Add** | Add or expand this test at the final public contract/gate/integration boundary. | V1 testing exists but the audit does not prove full V2 coverage. |
| `TRD-V2-TST-018` | Approval packet completeness, state-machine, creation, voting, override, and distinct-approver tests shall cover governance inputs consumed by trading. | **Reject** | Trading tests shall validate consumed approval contracts, not governance creation/voting/state-machine internals. | Those tests belong to governance. |
| `TRD-V2-TST-019` | Trading intent assembly tests shall cover approved proposal/risk-decision linkage and idempotency material. | **Add** | Add or expand this test at the final public contract/gate/integration boundary. | V1 testing exists but the audit does not prove full V2 coverage. |
| `TRD-V2-TST-020` | Idempotency tests shall cover duplicate same-material requests, duplicate different-material requests, stable canonical material across dictionary key ordering, and equivalent numeric formatting. | **Add** | Add or expand this test at the final public contract/gate/integration boundary. | V1 testing exists but the audit does not prove full V2 coverage. |
| `TRD-V2-TST-021` | Decimal-safe validation tests shall cover volume step, price precision, stop distance, commission, slippage, margin, and PnL fields. | **Add** | Add or expand this test at the final public contract/gate/integration boundary. | V1 testing exists but the audit does not prove full V2 coverage. |
| `TRD-V2-TST-022` | Property-based tests shall cover canonical payload serialization, idempotency material stability, Decimal quantization and rounding edge cases, timestamp normalization, and concurrency conflict detection. | **Add** | Add or expand this test at the final public contract/gate/integration boundary. | V1 testing exists but the audit does not prove full V2 coverage. |
| `TRD-V2-TST-023` | If Python `hypothesis` or another property-based testing library is used, the dependency shall require explicit dependency approval and documentation before being added. | **Keep** | Require explicit approval before adding a property-based testing dependency. | This is a sound dependency-governance rule. |
| `TRD-V2-TST-024` | UTC timestamp normalization and broker-time skew rejection tests shall cover system-time and broker-time evidence. | **Add** | Add or expand this test at the final public contract/gate/integration boundary. | V1 testing exists but the audit does not prove full V2 coverage. |
| `TRD-V2-TST-025` | Import-time safety tests shall prove `import app.services.trading` performs no broker connections, network calls, secret resolution, database writes, background worker starts, or simulator/live state mutation. | **Add** | Add or expand this test at the final public contract/gate/integration boundary. | V1 testing exists but the audit does not prove full V2 coverage. |
| `TRD-V2-TST-026` | Concurrency tests shall cover two concurrent submissions with the same idempotency key and same material, the same idempotency key and different material, two concurrent live-route submissions targeting the same account/strategy/symbol/side, and concurrent close/modify operations against the same position ticket. | **Add** | Add or expand this test at the final public contract/gate/integration boundary. | V1 testing exists but the audit does not prove full V2 coverage. |
| `TRD-V2-TST-027` | Broker bridge tests shall cover MT5, cTrader, paper broker, simulator bridge, and fail-closed behavior. | **Modify** | Test Trading against approved broker/simulator adapter contracts; concrete adapter unit tests remain in their owning domains. | Avoid duplicate adapter ownership. |
| `TRD-V2-TST-028` | Live connection boundary tests shall prove `trading_connect(route="live")` consumes only an approved credential/session interface and does not independently resolve secrets. | **Add** | Add or expand this test at the final public contract/gate/integration boundary. | V1 testing exists but the audit does not prove full V2 coverage. |
| `TRD-V2-TST-029` | Credential-expiry tests shall prove expired live session material returns `TRADING_CREDENTIAL_EXPIRED` with redacted diagnostics. | **Add** | Add or expand this test at the final public contract/gate/integration boundary. | V1 testing exists but the audit does not prove full V2 coverage. |
| `TRD-V2-TST-030` | Trade validator tests shall cover symbol, volume, price, order type, magic, slippage, expiration, timeframe, date range, stop loss, take profit, credentials, margin, tickets, max orders, and symbol volume. | **Add** | Add or expand this test at the final public contract/gate/integration boundary. | V1 testing exists but the audit does not prove full V2 coverage. |
| `TRD-V2-TST-031` | Simulator core tests shall cover order send, position monitoring, pending-order monitoring, account monitoring, trade records, equity points, and JSON serialization. | **Reject** | Simulator engine tests belong to the Simulator domain; Trading needs route-contract integration tests only. | Trading will not own simulator internals. |
| `TRD-V2-TST-032` | Reconciliation tests shall cover matched, missing, extra, mismatched, stale, unknown-outcome, startup, persistence event payloads, retry guard, and incident paths. | **Add** | Add or expand this test at the final public contract/gate/integration boundary. | V1 testing exists but the audit does not prove full V2 coverage. |
| `TRD-V2-TST-033` | Failure-path integration tests shall cover broker timeout after send attempt, broker disconnect mid-call, persistence failure before send, persistence failure after send, receipt missing, reconciliation mismatch, and compensation missing. | **Add** | Add or expand this test at the final public contract/gate/integration boundary. | V1 testing exists but the audit does not prove full V2 coverage. |
| `TRD-V2-TST-034` | Failure-path integration tests shall cover network partition after send-attempt persistence but before broker transmission. | **Add** | Add or expand this test at the final public contract/gate/integration boundary. | V1 testing exists but the audit does not prove full V2 coverage. |
| `TRD-V2-TST-035` | Failure-path integration tests shall run against a broker simulator capable of injecting network timeouts, disconnects, delayed responses, missing receipts, partial fills, and unknown outcomes. | **Add** | Add fault-injection integration tests using an approved test adapter; implementation belongs to test infrastructure. | Critical unknown-outcome evidence is missing from V1 audit. |
| `TRD-V2-TST-036` | Performance and resource tests shall cover readiness aggregation timeout budgets, reconciliation maximum snapshot size, large payload rejection before expensive validation or broker calls, and retry exhaustion. | **Modify** | Test approved limits and timeout behavior after limits are decided; do not hard-code pending targets. | Values remain open. |
| `TRD-V2-TST-037` | Simulator resource tests shall cover high-frequency simulated order generation, bounded memory behavior, and deterministic resource-exhaustion envelopes. | **Reject** | High-frequency simulator resource tests belong to Simulator; Trading tests only bounded route requests. | Domain boundary. |
| `TRD-V2-TST-038` | Monitoring tests shall cover stale state, ingestion health, workflow timeout, tool health, incident classification, latency, and snapshot cache behavior. | **Add** | Add or expand this test at the final public contract/gate/integration boundary. | V1 testing exists but the audit does not prove full V2 coverage. |
| `TRD-V2-TST-039` | Cost enforcement tests shall cover per-request, workflow, and session budget checks. | **Add** | Add or expand this test at the final public contract/gate/integration boundary. | V1 testing exists but the audit does not prove full V2 coverage. |
| `TRD-V2-TST-040` | Shadow trading tests shall cover feed building, no-live-mutation execution, and expected-versus-realized reporting. | **Defer** | Defer shadow/compensation test suites with the deferred capabilities. | No initial implementation is approved. |
| `TRD-V2-TST-041` | Compensation tests shall cover order, position, registry, validation, packaging, gated execution, missing-plan, and audit-log behavior. | **Defer** | Defer shadow/compensation test suites with the deferred capabilities. | No initial implementation is approved. |
| `TRD-V2-TST-042` | Security tests shall prove secrets and private broker/approval payloads are redacted from errors, logs, reports, notifications, metrics, chat responses, nested exceptions, and audit metadata. | **Add** | Add or expand this test at the final public contract/gate/integration boundary. | V1 testing exists but the audit does not prove full V2 coverage. |
| `TRD-V2-TST-043` | Documentation and usage-example tests shall execute all usage examples and verify exact envelope shapes for success and failure paths. | **Add** | Add or expand this test at the final public contract/gate/integration boundary. | V1 testing exists but the audit does not prove full V2 coverage. |
| `TRD-V2-DEP-001` | Trading consumes approval verdicts, approval references, and approval completeness evidence from the owning governance or approval module. | **Keep** | Retain this cross-domain dependency boundary. | It keeps Trading focused. |
| `TRD-V2-DEP-002` | Trading consumes risk decisions, risk constraints, kill-switch state, and exposure verdicts from the Risk module. | **Keep** | Retain this cross-domain dependency boundary. | It keeps Trading focused. |
| `TRD-V2-DEP-003` | Trading consumes broker readiness, live runtime enablement, session orchestration, secret-resolution status, and production broker mutation authorization from the Live module and related policy modules. | **Merge** | Broker readiness, session enablement and live authorization are internal sub-capabilities of unified Trading; policy/secret owners remain external. | Removes the separate Live-domain dependency. |
| `TRD-V2-DEP-004` | Trading consumes live credential/session material only through an approved external credential/session interface, such as an injected `ICredentialProvider`, pre-authorized connection handle, or Live-owned session reference. | **Modify** | Consume an approved opaque session/credential provider from the external secret/broker owner; do not expose raw material. | Preserves safe binding. |
| `TRD-V2-DEP-005` | Trading consumes an injected `RedactionService` or Utils-owned redaction helper for logs, errors, envelopes, reports, notifications, and audit metadata. | **Keep** | Retain this cross-domain dependency boundary. | It keeps Trading focused. |
| `TRD-V2-DEP-006` | Trading consumes market, account, portfolio, symbol, and broker state from Data, broker adapters, or approved state repositories. | **Keep** | Retain this cross-domain dependency boundary. | It keeps Trading focused. |
| `TRD-V2-DEP-007` | Trading coordinates with persistence through documented repository interfaces or event payloads but does not own durable schema or migration definitions. | **Keep** | Retain this cross-domain dependency boundary. | It keeps Trading focused. |
| `TRD-V2-DEP-008` | Trading coordinates with API, UI, Research, Optimization, Simulation, Live, and Conversation through documented request and response contracts only. | **Modify** | Coordinate through contracts with API, UI, Research, Optimization, Simulation and Conversation; remove Live as a separate domain. | Matches the unified package decision. |
| `TRD-V2-PCM-001` | Before Builder handoff, every exported name in `app.services.trading.__all__` shall have a documented public contract. | **Modify** | Maintain separate matrices for public Python API and agent-callable tools; mechanically test both against approved contracts. | The documentation requirement is sound but `__all__` is not an agent registry. |
| `TRD-V2-PCM-002` | Each contract shall include tool name, public/internal classification, stability level, route support, required inputs, optional inputs, input schema version, standard envelope output schema, `data` schema, status values, error codes, warning codes where applicable, side-effect classification, approval requirement, idempotency requirement, audit metadata fields, network behavior, persistence behavior, and usage examples. | **Modify** | Maintain separate matrices for public Python API and agent-callable tools; mechanically test both against approved contracts. | The documentation requirement is sound but `__all__` is not an agent registry. |
| `TRD-V2-PCM-003` | The actual public tool contract matrix shall be present in this document or an explicitly referenced appendix before Builder handoff; this process requirement alone is not sufficient for implementation. | **Modify** | Maintain separate matrices for public Python API and agent-callable tools; mechanically test both against approved contracts. | The documentation requirement is sound but `__all__` is not an agent registry. |
| `TRD-V2-PCM-004` | Each public contract shall define exact callable signature, parameter types, required and optional fields, constraints, default values, enum values, failure behavior, and return schema. | **Modify** | Maintain separate matrices for public Python API and agent-callable tools; mechanically test both against approved contracts. | The documentation requirement is sound but `__all__` is not an agent registry. |
| `TRD-V2-PCM-005` | Public agent-facing tools shall be separate from lower-level helpers, adapters, DTOs, repository interfaces, and experimental rebuild support. | **Modify** | Maintain separate matrices for public Python API and agent-callable tools; mechanically test both against approved contracts. | The documentation requirement is sound but `__all__` is not an agent registry. |
| `TRD-V2-PCM-006` | Contract tests shall be automatically generated from, or mechanically checked against, the public tool contract matrix to prevent drift. | **Modify** | Maintain separate matrices for public Python API and agent-callable tools; mechanically test both against approved contracts. | The documentation requirement is sound but `__all__` is not an agent registry. |
| `TRD-V2-IDA-001` | Before Builder handoff, this document shall include an Interface Definition Appendix with exact contracts for every public agent-facing Trading function. | **Keep** | Provide exact interface definitions before Builder handoff. | Required for a stable rebuild. |
| `TRD-V2-IDA-002` | The appendix shall include at minimum `trading_connect`, `trading_disconnect`, `trading_is_connected`, `validate_order_request`, `build_execution_plan`, `run_execution_readiness_check`, `submit_order`, `modify_order`, `cancel_order`, `close_position`, `sync_positions`, `reconcile_state`, and `build_trading_report`. | **Modify** | Document exact contracts for the approved minimal API; connection operations are route-authority binding, not raw broker login. | The proposed minimum list is broadly valid but needs final names/ownership. |
| `TRD-V2-IDA-003` | Each entry shall include a Python-style signature, schema version, JSON-safe input schema, JSON-safe `data` schema, exact status values, exact error and warning codes, side-effect class, approval requirement, idempotency requirement, concurrency scope, timeout behavior, freshness behavior, and usage examples. | **Keep** | Provide exact interface definitions before Builder handoff. | Required for a stable rebuild. |
| `TRD-V2-IDA-004` | Lower-level validation helpers may be represented in a validation table instead of long prose, but the table shall include function name, input fields, validation rule, error code, and requirement/test IDs. | **Keep** | Provide exact interface definitions before Builder handoff. | Required for a stable rebuild. |
| `TRD-V2-NOTE-001` | The trading module shall be built as one route-aware public contract rather than separate execution, paper, and live API families. | **Keep** | Build one route-aware trading package with an internal live runtime capability. | This matches the selected architecture. |
| `TRD-V2-NOTE-002` | Exact route names beyond `sim` and `live` are not approved by this document. | **Modify** | Approve `sim` and `live` for the initial rebuild; treat paper/shadow as modes or deferred routes pending a system decision. | V1 currently exposes additional routes. |
| `TRD-V2-NOTE-003` | Live broker mutation remains governed by `10_live.md`, risk, approval, kill switch, reconciliation, idempotency, and runtime enablement gates. | **Merge** | Apply the listed live gates inside unified Trading rather than a separate Live module. | Same safety behaviour, simpler domain shape. |
| `TRD-V2-NOTE-004` | Secret storage, rotation, live credential resolution, and live credentials lifecycle remain outside the Trading module and are handled by Secrets, Live, or another approved owner. | **Keep** | Keep secret storage, rotation and credential lifecycle external; consume opaque references/handles. | Clear boundary. |
| `TRD-V2-NOTE-005` | Shadow-trading behavior is strictly read-only with respect to live state and is mathematically prohibited from mutating live broker, account, position, order, approval, risk, or kill-switch state. | **Keep** | Shadow mode must be incapable of live mutation. | Essential if shadow is later enabled. |
| `TRD-V2-NOTE-006` | Full cTrader bridge behavior, automatic live compensation execution, and shadow-trading expected-versus-realized reporting may be staged after the first Trading implementation slice unless explicitly approved earlier. | **Keep** | Stage cTrader-specific integration, generalized compensation and shadow comparison after the initial safe core. | Proportionate sequencing. |
| `TRD-V2-NOTE-007` | Public registry and catalog updates are mandatory when trading tools are added, renamed, or removed. | **Keep** | Require registry/catalog/test synchronization for API changes. | Prevents drift. |

### 6.2 `07_trading.md` edge cases

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
| --- | --- | --- | --- | --- |
| `TRD-V2-EDGE-001` | Empty request payload. | **Add** | Include this scenario in the final contract, validation, gate or integration test suite. | It exercises an accepted core behavior. |
| `TRD-V2-EDGE-002` | Malformed JSON or non-dictionary request payload. | **Add** | Include this scenario in the final contract, validation, gate or integration test suite. | It exercises an accepted core behavior. |
| `TRD-V2-EDGE-003` | Required field present with invalid type. | **Add** | Include this scenario in the final contract, validation, gate or integration test suite. | It exercises an accepted core behavior. |
| `TRD-V2-EDGE-004` | Oversized request payload. | **Add** | Include this scenario in the final contract, validation, gate or integration test suite. | It exercises an accepted core behavior. |
| `TRD-V2-EDGE-005` | Unknown, missing, or misspelled trading route. | **Add** | Add fault-path and unknown-outcome/reconciliation coverage. | V1 components exist but production behavior is not proven. |
| `TRD-V2-EDGE-006` | Missing approval ID for a live route action that requires approval. | **Add** | Include this scenario in the final contract, validation, gate or integration test suite. | It exercises an accepted core behavior. |
| `TRD-V2-EDGE-007` | Live mutation flag disabled while a shared trading function is called with `route="live"`. | **Add** | Include this scenario in the final contract, validation, gate or integration test suite. | It exercises an accepted core behavior. |
| `TRD-V2-EDGE-008` | Live-route credential, token, or session handle expires mid-session; Trading shall return `TRADING_CREDENTIAL_EXPIRED` without leaking secrets. | **Add** | Include this scenario in the final contract, validation, gate or integration test suite. | It exercises an accepted core behavior. |
| `TRD-V2-EDGE-009` | Multiple concurrent `trading_connect` calls target the same live route and provider. | **Add** | Add idempotency and coordination coverage using the approved conflict scope. | Critical duplicate/conflict behavior. |
| `TRD-V2-EDGE-010` | Active global, strategy, or symbol kill switch. | **Add** | Add deterministic policy/gate/race coverage in unified Trading. | Critical live safety case. |
| `TRD-V2-EDGE-011` | Broker disconnected, stale broker time, stale quote, stale account snapshot, stale permissions, or stale symbol metadata. | **Add** | Include this scenario in the final contract, validation, gate or integration test suite. | It exercises an accepted core behavior. |
| `TRD-V2-EDGE-012` | Daylight Saving Time transition or timezone rule change creates artificial clock skew between system time and broker time. | **Add** | Add explicit UTC/broker-time/approval-time normalization and skew coverage. | Required for deterministic gating. |
| `TRD-V2-EDGE-013` | Unknown broker or simulator result after a send attempt. | **Add** | Add fault-path and unknown-outcome/reconciliation coverage. | V1 components exist but production behavior is not proven. |
| `TRD-V2-EDGE-014` | Broker call times out after the broker may have accepted the request. | **Add** | Include this scenario in the final contract, validation, gate or integration test suite. | It exercises an accepted core behavior. |
| `TRD-V2-EDGE-015` | Duplicate idempotency key with different material fields. | **Add** | Add idempotency and coordination coverage using the approved conflict scope. | Critical duplicate/conflict behavior. |
| `TRD-V2-EDGE-016` | Duplicate request submitted concurrently with the same idempotency key. | **Add** | Add idempotency and coordination coverage using the approved conflict scope. | Critical duplicate/conflict behavior. |
| `TRD-V2-EDGE-017` | Duplicate request submitted concurrently with different idempotency keys but identical broker-impacting material. | **Add** | Add idempotency and coordination coverage using the approved conflict scope. | Critical duplicate/conflict behavior. |
| `TRD-V2-EDGE-018` | Existing send attempt with no authoritative receipt. | **Add** | Add fault-path and unknown-outcome/reconciliation coverage. | V1 components exist but production behavior is not proven. |
| `TRD-V2-EDGE-019` | Network partition occurs after send-attempt persistence but before broker transmission. | **Add** | Add fault-path and unknown-outcome/reconciliation coverage. | V1 components exist but production behavior is not proven. |
| `TRD-V2-EDGE-020` | Persistence succeeds before broker send but fails after broker response. | **Add** | Add fault-path and unknown-outcome/reconciliation coverage. | V1 components exist but production behavior is not proven. |
| `TRD-V2-EDGE-021` | Broker receipt received without matching send-attempt record. | **Add** | Add fault-path and unknown-outcome/reconciliation coverage. | V1 components exist but production behavior is not proven. |
| `TRD-V2-EDGE-022` | Reconciliation mismatch between authority source and internal state. | **Add** | Include this scenario in the final contract, validation, gate or integration test suite. | It exercises an accepted core behavior. |
| `TRD-V2-EDGE-023` | Missing or unsupported route provider. | **Add** | Include this scenario in the final contract, validation, gate or integration test suite. | It exercises an accepted core behavior. |
| `TRD-V2-EDGE-024` | Symbol mapping absent, alias collision, or broker symbol disabled. | **Add** | Include this scenario in the final contract, validation, gate or integration test suite. | It exercises an accepted core behavior. |
| `TRD-V2-EDGE-025` | Market closed, trade permission disabled, invalid account mode, insufficient margin, or margin level below policy. | **Add** | Include this scenario in the final contract, validation, gate or integration test suite. | It exercises an accepted core behavior. |
| `TRD-V2-EDGE-026` | Volume below minimum, above maximum, not aligned to step, malformed, or exceeding symbol exposure limits. | **Add** | Include this scenario in the final contract, validation, gate or integration test suite. | It exercises an accepted core behavior. |
| `TRD-V2-EDGE-027` | Invalid side, unsupported order type, invalid price, malformed ticket, invalid magic number, invalid timeframe, or invalid expiration. | **Add** | Include this scenario in the final contract, validation, gate or integration test suite. | It exercises an accepted core behavior. |
| `TRD-V2-EDGE-028` | Stop loss or take profit on the wrong side of entry price, too close to market, or inside broker freeze distance. | **Add** | Include this scenario in the final contract, validation, gate or integration test suite. | It exercises an accepted core behavior. |
| `TRD-V2-EDGE-029` | Price, volume, spread, slippage, commission, bid, ask, or account values missing, non-finite, zero, or negative where invalid. | **Add** | Include this scenario in the final contract, validation, gate or integration test suite. | It exercises an accepted core behavior. |
| `TRD-V2-EDGE-030` | Clock skew between system time and broker time exceeds configured tolerance. | **Add** | Add explicit UTC/broker-time/approval-time normalization and skew coverage. | Required for deterministic gating. |
| `TRD-V2-EDGE-031` | Decimal rounding changes volume, price, stop distance, margin, or idempotency material. | **Add** | Include this scenario in the final contract, validation, gate or integration test suite. | It exercises an accepted core behavior. |
| `TRD-V2-EDGE-032` | Partial fills, partial closes, pending-order expiry, pending-order trigger, or IOC-like remainder behavior. | **Add** | Include this scenario in the final contract, validation, gate or integration test suite. | It exercises an accepted core behavior. |
| `TRD-V2-EDGE-033` | Simulated fills diverging from backtest expectations. | **Defer** | Retain as a future shadow/route-comparison acceptance scenario. | Shadow comparison is deferred. |
| `TRD-V2-EDGE-034` | Shadow expected fill/PnL diverging from realized market behavior. | **Defer** | Retain as a future shadow/route-comparison acceptance scenario. | Shadow comparison is deferred. |
| `TRD-V2-EDGE-035` | Simulator resource exhaustion during high-frequency simulated order generation. | **Reject** | Test simulator resource behavior in the Simulator domain; Trading tests bounded route dispatch and envelope handling. | Simulator internals are outside Trading. |
| `TRD-V2-EDGE-036` | Compensation plan missing for an action class. | **Defer** | Add when the compensation catalog is approved. | Compensation is deferred. |
| `TRD-V2-EDGE-037` | Cost budget exceeded before a governed action completes. | **Modify** | Cover before-send block and after-send incident using externally owned budget limits. | Cost policy is external; enforcement evidence remains in Trading. |
| `TRD-V2-EDGE-038` | Workflow timeout while approval, send, receipt, reconciliation, or compensation remains pending. | **Add** | Add fault-path and unknown-outcome/reconciliation coverage. | V1 components exist but production behavior is not proven. |
| `TRD-V2-EDGE-039` | Secret-reference resolution failure or accidental raw secret in config input. | **Add** | Add redaction and opaque-reference failure coverage in unified Trading. | Required security boundary. |
| `TRD-V2-EDGE-040` | Redaction failure caused by nested exception, nested broker payload, or serialized approval evidence. | **Add** | Include this scenario in the final contract, validation, gate or integration test suite. | It exercises an accepted core behavior. |

### 6.3 `10_live.md` checklist requirements

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
| --- | --- | --- | --- | --- |
| `LIVE-V2-PUR-001` | The Live module shall be consumed only by approved shared trading tools, live runtime orchestration, operator workflows, monitoring, reconciliation, audit, and reporting consumers. | **Merge** | Implement this responsibility inside `app.services.trading.live`; do not create a separate Live domain/package. | The user chose one route-aware Trading domain. |
| `LIVE-V2-PUR-002` | The Live module shall act as a strict middleware/gateway for live-route requests and shall not implement strategy, risk, approval, broker, UI, or business-policy logic. | **Merge** | Implement this responsibility inside `app.services.trading.live`; do not create a separate Live domain/package. | The user chose one route-aware Trading domain. |
| `LIVE-V2-OWN-001` | Live runtime configuration, including trading enablement flags, safety settings, notification settings, logging settings, state settings, and secret-reference resolution. | **Modify** | Unified Trading owns live enablement/session settings and validates secret references through an injected provider; secret storage/rotation remain external. | Resolves the Trading/Live ownership conflict safely. |
| `LIVE-V2-OWN-002` | Live session, live run, startup, shutdown, signal handling, recovery diagnostics, and runtime status/event emission for approved consumers. | **Merge** | Merge this live-only behaviour into the unified Trading live runtime capability. | Behaviour is valid; separate domain structure is not. |
| `LIVE-V2-OWN-003` | Live-only approval gates for broker mutation, kill-switch action, pause, resume, exposure reduction, mass cancel, mass close, and recovery. | **Merge** | Merge this live-only behaviour into the unified Trading live runtime capability. | Behaviour is valid; separate domain structure is not. |
| `LIVE-V2-OWN-004` | Live gate decision records for every live-route request, including gate inputs, gate outcomes, final decision, side-effect mode, and audit reference. | **Merge** | Merge this live-only behaviour into the unified Trading live runtime capability. | Behaviour is valid; separate domain structure is not. |
| `LIVE-V2-OWN-005` | Live side-effect state classification for each request: no side effect, packaged only, broker mutation attempted, broker mutation accepted, broker mutation rejected, unknown outcome, reconciled, or incident. | **Merge** | Merge this live-only behaviour into the unified Trading live runtime capability. | Behaviour is valid; separate domain structure is not. |
| `LIVE-V2-OWN-006` | Live broker readiness and broker-truth synchronization before live mutation. | **Merge** | Merge this live-only behaviour into the unified Trading live runtime capability. | Behaviour is valid; separate domain structure is not. |
| `LIVE-V2-OWN-007` | Live reconciliation authority state, startup reconciliation, retry guard, unknown-outcome handling, and live discrepancy incidents. | **Merge** | Merge this live-only behaviour into the unified Trading live runtime capability. | Behaviour is valid; separate domain structure is not. |
| `LIVE-V2-OWN-008` | Live kill-switch enforcement, live order disablement, live mass-cancel/mass-close request packaging, re-enable approval, and approval-cleared recovery. | **Merge** | Merge this live-only behaviour into the unified Trading live runtime capability. | Behaviour is valid; separate domain structure is not. |
| `LIVE-V2-OWN-009` | Live state management for positions, orders, broker receipts, reconciliation status, run status, incidents, and recovery context. | **Merge** | Merge this live-only behaviour into the unified Trading live runtime capability. | Behaviour is valid; separate domain structure is not. |
| `LIVE-V2-OWN-010` | Live monitoring for stale state, ingestion health, tool health, workflow timeout, operational incidents, latency, cost, notification failures, and live readiness. | **Modify** | Merge a minimal live monitoring/incident surface into Trading; external observability transports remain outside. | V1 monitoring exists but is disconnected. |
| `LIVE-V2-OWN-011` | Live performance reports, live execution reports, broker-truth snapshots, and live audit evidence. | **Modify** | Package execution/reconciliation/audit evidence in Trading; performance calculation remains Analytics-owned. | Avoids reporting-domain duplication. |
| `LIVE-V2-OWN-012` | Live notifications through configured safe channels without leaking secrets or private broker data. | **Modify** | Emit safe notification events through an injected notifier; do not own notification transport policy. | V1 has notification configuration and injected dispatch concepts. |
| `LIVE-V2-OWN-013` | Live-compatible shadow execution and production-like comparison reports when real broker mutation is disabled. | **Defer** | Defer production-like shadow comparison until the core live runtime is proven. | Not required for initial live safety. |
| `LIVE-V2-BOUND-001` | The module does not own shared order, position, validation, route, bridge, receipt, simulator, or reconciliation function contracts; those belong to `07_trading.md`. | **Merge** | Shared trading and live contracts now belong to one Trading domain, while focused submodules remain separate internally. | Removes the obsolete inter-module split. |
| `LIVE-V2-BOUND-002` | The module does not own strategy signal generation, strategy lifecycle promotion, or strategy approval. | **Keep** | Retain this domain boundary within unified Trading. | It prevents policy and infrastructure leakage. |
| `LIVE-V2-BOUND-003` | The module does not own risk policy, position sizing approval, exposure limits, portfolio allocation policy, or kill-switch policy ownership outside live enforcement. | **Keep** | Retain this domain boundary within unified Trading. | It prevents policy and infrastructure leakage. |
| `LIVE-V2-BOUND-004` | The module does not own strategy selection, financial advice, risk-policy creation, approval-policy creation, or broker-adapter policy decisions. | **Keep** | Retain this domain boundary within unified Trading. | It prevents policy and infrastructure leakage. |
| `LIVE-V2-BOUND-005` | The module does not own market-data ingestion, provider data normalization, or historical data storage. | **Keep** | Retain this domain boundary within unified Trading. | It prevents policy and infrastructure leakage. |
| `LIVE-V2-BOUND-006` | The module does not own durable database schema/migration ownership, but it shall define required persistence ports such as `LiveStateStore`, `AuditSink`, and `IdempotencyStore`, including exact method signatures, required fields, failure behavior, and schema-version compatibility expectations before Builder handoff. | **Modify** | Define minimal state/audit/idempotency interfaces in Trading; concrete storage and schemas remain infrastructure-owned. | Exact interfaces are needed, but avoid unnecessary repository layers. |
| `LIVE-V2-BOUND-007` | The module does not own approval policy creation, but it shall validate approval context against the approved approval-policy contract. | **Keep** | Retain this domain boundary within unified Trading. | It prevents policy and infrastructure leakage. |
| `LIVE-V2-BOUND-008` | The module does not own the live action policy matrix unless a later governance decision assigns it to Live; until then, Live shall consume the approved matrix from the owning governance module. | **Keep** | Retain this domain boundary within unified Trading. | It prevents policy and infrastructure leakage. |
| `LIVE-V2-BOUND-009` | The module does not own broker adapter implementation or interface definition; it owns live readiness validation, response classification, and error-mapping requirements for approved broker adapters before live use. | **Keep** | Consume approved broker adapters; Trading owns readiness requirements, capability validation and response classification only. | Matches V1's router boundary. |
| `LIVE-V2-BOUND-010` | The module does not own API authentication, UI rendering, websocket connection management, or frontend workflow policy. | **Keep** | Retain this domain boundary within unified Trading. | It prevents policy and infrastructure leakage. |
| `LIVE-V2-BOUND-011` | The module does not grant AI chat, UI, API, backtest, or optimization workflows authority to execute live broker mutations. | **Keep** | Retain this domain boundary within unified Trading. | It prevents policy and infrastructure leakage. |
| `LIVE-V2-BOUND-012` | The module does not provide financial advice, trading recommendations, or owner-approved live threshold decisions. | **Keep** | Retain this domain boundary within unified Trading. | It prevents policy and infrastructure leakage. |
| `LIVE-V2-API-001` | Expose a registry of callable live tools through the live tool registry, with each callable live tool accepting a standard request envelope and returning a standard response envelope. | **Merge** | Use the unified Trading registry and contract matrix; mark live-only operations within it. | A separate live registry would duplicate public governance. |
| `LIVE-V2-API-002` | Each exported live tool shall document whether it is public API, internal helper, or official callable tool. | **Merge** | Use the unified Trading registry and contract matrix; mark live-only operations within it. | A separate live registry would duplicate public governance. |
| `LIVE-V2-API-003` | Each exported live tool shall define a stable public contract including tool name, purpose, input schema, output schema, approval requirement, side-effect classification, risk level, error codes, warning codes, audit metadata, idempotency behavior, and stability status. | **Merge** | Use the unified Trading registry and contract matrix; mark live-only operations within it. | A separate live registry would duplicate public governance. |
| `LIVE-V2-API-004` | Each exported live tool shall return a standard envelope containing tool name, status, request ID, correlation ID, side-effect mode, data, errors, warnings, audit metadata, incident reference, and `retry_after_seconds` where applicable. | **Modify** | Use the unified Trading envelope, side-effect and retry enums, including incident and retry delay fields when applicable. | V1 has partial types but duplicate taxonomies. |
| `LIVE-V2-API-005` | `retry_after_seconds` shall be present for `retry_after_reconciliation`, broker rate-limit, and configured retry-delay scenarios, and shall be `null` or omitted only when no retry delay is applicable. | **Modify** | Use the unified Trading envelope, side-effect and retry enums, including incident and retry delay fields when applicable. | V1 has partial types but duplicate taxonomies. |
| `LIVE-V2-API-006` | Each exported live tool contract shall reference the shared side-effect mode and retry-safety enumerations from Terminology And Data Definitions rather than redefining them. | **Modify** | Use the unified Trading envelope, side-effect and retry enums, including incident and retry delay fields when applicable. | V1 has partial types but duplicate taxonomies. |
| `LIVE-V2-API-007` | Validate live runtime configuration and resolve secret references without exposing secret values. | **Modify** | Validate live configuration and resolve only opaque references through an injected provider. | No raw secret ownership. |
| `LIVE-V2-API-008` | Start and stop live sessions safely. | **Merge** | Expose these live behaviours through the unified Trading package and live submodule. | Same behavior without a separate public API family. |
| `LIVE-V2-API-009` | Evaluate live readiness before `route="live"` trading functions can mutate broker state. | **Merge** | Expose these live behaviours through the unified Trading package and live submodule. | Same behavior without a separate public API family. |
| `LIVE-V2-API-010` | Gate shared trading functions such as `submit_order`, `modify_order`, `cancel_order`, `close_position`, `modify_position`, `reduce_exposure`, `pause_strategy`, `resume_strategy`, `sync_positions`, `reconcile_state`, and `build_trading_report` when called with `route="live"`. | **Merge** | Expose these live behaviours through the unified Trading package and live submodule. | Same behavior without a separate public API family. |
| `LIVE-V2-API-011` | Package live submit, cancel, modify, close, pause, resume, reduce exposure, position sync, broker reconciliation, and live report requests through shared trading contracts. | **Merge** | Expose these live behaviours through the unified Trading package and live submodule. | Same behavior without a separate public API family. |
| `LIVE-V2-API-012` | Package kill-switch trigger, condition check, order-disable, mass-cancel, mass-close, event-record, re-enable-approval, and approval-cleared recovery requests. | **Merge** | Expose these live behaviours through the unified Trading package and live submodule. | Same behavior without a separate public API family. |
| `LIVE-V2-API-013` | Monitor live stale state, ingestion, tool health, workflow timeout, operational status, incidents, cost, latency, and notification outcomes. | **Modify** | Expose a minimal live monitoring event capability; defer snapshot-cache breadth. | V1 lacks proven production composition. |
| `LIVE-V2-API-014` | Produce live execution, reconciliation, incident, and performance reports with audit evidence. | **Modify** | Package execution/reconciliation/incident evidence; delegate performance analytics. | Clearer boundary. |
| `LIVE-V2-API-015` | Support shadow execution and expected-versus-realized reporting without real broker mutation. | **Defer** | Defer shadow comparison from the initial rebuild. | Nonessential for safe launch. |
| `LIVE-V2-FR-001` | Live runtime shall fail closed unless live mode is explicitly enabled by approved runtime configuration. | **Merge** | Retain this live safety behaviour inside the unified Trading live runtime. | V1 already has substantial support but missing real risk wiring. |
| `LIVE-V2-FR-002` | Live runtime shall treat shared trading functions as the only live trading action surface. | **Merge** | Retain this live safety behaviour inside the unified Trading live runtime. | V1 already has substantial support but missing real risk wiring. |
| `LIVE-V2-FR-003` | Live runtime shall reject any direct live broker mutation that bypasses shared trading, risk, approval, idempotency, reconciliation, audit, or kill-switch gates. | **Merge** | Retain this live safety behaviour inside the unified Trading live runtime. | V1 already has substantial support but missing real risk wiring. |
| `LIVE-V2-FR-004` | Live runtime shall propagate, log, and persist request ID, correlation ID, approval ID, risk decision reference, idempotency material, broker provider, route, account, strategy, symbol, and audit metadata through every gate, package, broker-attempt, reconciliation, and report boundary. | **Merge** | Retain this live safety behaviour inside the unified Trading live runtime. | V1 already has substantial support but missing real risk wiring. |
| `LIVE-V2-FR-005` | Live runtime shall return structured rejections or blocks for invalid orders, disabled live mode, unsupported broker, failed readiness checks, stale context, active kill switch, reconciliation mismatch, missing approval, or unsafe live conditions. | **Merge** | Retain this live safety behaviour inside the unified Trading live runtime. | V1 already has substantial support but missing real risk wiring. |
| `LIVE-V2-FR-006` | Live runtime shall keep live broker mutations disabled by default unless explicitly enabled and governed. | **Merge** | Retain this live safety behaviour inside the unified Trading live runtime. | V1 already has substantial support but missing real risk wiring. |
| `LIVE-V2-FR-007` | Live runtime shall classify unknown broker outcomes separately from broker rejections, validation rejections, and successful broker acknowledgements. | **Merge** | Retain this live safety behaviour inside the unified Trading live runtime. | V1 already has substantial support but missing real risk wiring. |
| `LIVE-V2-FR-008` | Live route gating shall evaluate gates in a deterministic order: live enablement, request schema validation, approval validation, risk decision validation, broker readiness, stale-context validation, idempotency validation, reconciliation authority validation, kill-switch validation, audit pre-recording, and broker adapter permission. | **Modify** | Use one deterministic fail-fast gate sequence that also includes session enablement and concurrency, while combining closely related readiness/staleness checks. | V1's 16 gates and V2's 11 gates should be simplified into one approved sequence. |
| `LIVE-V2-FR-009` | A failed mandatory gate shall stop evaluation before any downstream gate that could mutate broker state, mutate durable state beyond audit-safe diagnostics, or consume external broker capacity. | **Keep** | Fail mandatory gates before broker capacity or unsafe durable mutation is consumed. | Core safety invariant. |
| `LIVE-V2-FR-010` | Diagnostic-only gates may run after a mandatory gate failure only when the gate contract marks `diagnostic_after_failure=true`, `mutates_state=false`, `calls_broker=false`, and `requires_network=false`. | **Reject** | Do not add a post-failure diagnostic-gate framework in the initial rebuild; perform local contract/redaction validation before the mandatory sequence. | The framework adds flags and paths without demonstrated workflow value. |
| `LIVE-V2-FR-011` | Initially approved diagnostic-only gates are limited to local tool-contract metadata validation and local redaction validation; every other gate is mandatory until explicitly approved otherwise. | **Reject** | Do not add a post-failure diagnostic-gate framework in the initial rebuild; perform local contract/redaction validation before the mandatory sequence. | The framework adds flags and paths without demonstrated workflow value. |
| `LIVE-V2-FR-012` | Each gate failure shall return a standard error code, human-readable operator message, request ID, correlation ID, failed gate name, retry-safety classification, and audit metadata. | **Modify** | Retain structured gate decisions, pre/post audit and current broker-truth/readiness checks using the unified envelope and approved adapter contract. | V1 provides most pieces but persistence and adapter compatibility need connection. |
| `LIVE-V2-FR-013` | Live gate decision records shall persist the requested action, gate order, gate inputs by reference, gate outcomes, final decision, side-effect mode, and audit reference when persistence is available. | **Modify** | Retain structured gate decisions, pre/post audit and current broker-truth/readiness checks using the unified envelope and approved adapter contract. | V1 provides most pieces but persistence and adapter compatibility need connection. |
| `LIVE-V2-FR-014` | Audit pre-event evidence shall be recorded before broker mutation and audit post-event evidence after broker response, rejection, timeout, or unknown outcome. | **Modify** | Retain structured gate decisions, pre/post audit and current broker-truth/readiness checks using the unified envelope and approved adapter contract. | V1 provides most pieces but persistence and adapter compatibility need connection. |
| `LIVE-V2-FR-015` | Audit-write failure before broker mutation shall always block broker mutation. | **Modify** | Retain structured gate decisions, pre/post audit and current broker-truth/readiness checks using the unified envelope and approved adapter contract. | V1 provides most pieces but persistence and adapter compatibility need connection. |
| `LIVE-V2-FR-016` | The runtime must verify that its internal position/order view matches broker truth within configured `max_staleness_seconds` or narrower approved context-specific staleness thresholds before any broker mutation. | **Modify** | Retain structured gate decisions, pre/post audit and current broker-truth/readiness checks using the unified envelope and approved adapter contract. | V1 provides most pieces but persistence and adapter compatibility need connection. |
| `LIVE-V2-FR-017` | Broker readiness shall include broker API/version compatibility checks once the broker adapter contract is approved. | **Modify** | Retain structured gate decisions, pre/post audit and current broker-truth/readiness checks using the unified envelope and approved adapter contract. | V1 provides most pieces but persistence and adapter compatibility need connection. |
| `LIVE-V2-FR-018` | Live runtime shall run in package-only mode unless live broker mutation is explicitly enabled. | **Merge** | Implement package-only and mutation-enabled modes in the unified Trading live route with one side-effect taxonomy. | Central design choice. |
| `LIVE-V2-FR-019` | When live broker mutation is disabled, live trading actions shall only package validated broker-mutation requests or return structured blocks and shall not call any broker adapter. | **Merge** | Implement package-only and mutation-enabled modes in the unified Trading live route with one side-effect taxonomy. | Central design choice. |
| `LIVE-V2-FR-020` | When live broker mutation is enabled, live trading actions may call an approved broker adapter only after all mandatory live gates pass. | **Merge** | Implement package-only and mutation-enabled modes in the unified Trading live route with one side-effect taxonomy. | Central design choice. |
| `LIVE-V2-FR-021` | Every live result envelope shall include `side_effect_mode` with one of `none`, `packaged_only`, `broker_mutation_attempted`, `broker_mutation_confirmed`, `broker_mutation_rejected`, `unknown_outcome`, or `incident`. | **Merge** | Implement package-only and mutation-enabled modes in the unified Trading live route with one side-effect taxonomy. | Central design choice. |
| `LIVE-V2-FR-022` | Package-only success shall not be treated as broker acceptance, live readiness, risk approval, or execution evidence. | **Merge** | Implement package-only and mutation-enabled modes in the unified Trading live route with one side-effect taxonomy. | Central design choice. |
| `LIVE-V2-FR-023` | The live action policy matrix shall define every action mentioned in this file before Builder handoff. | **Modify** | Consume an externally owned action policy matrix and enforce it fail closed; do not own policy creation. | V1 has an internal matrix but ownership is unresolved. |
| `LIVE-V2-FR-024` | Each live action policy entry shall define action name, owning module, required permissions, approval requirement, emergency fail-safe eligibility, idempotency requirement, required audit events, side-effect ceiling, retry-safety default, and operator-review requirement. | **Modify** | Consume an externally owned action policy matrix and enforce it fail closed; do not own policy creation. | V1 has an internal matrix but ownership is unresolved. |
| `LIVE-V2-FR-025` | Live runtime shall enforce the live action policy matrix and shall return `LIVE_POLICY_UNDEFINED` for any live action missing from the matrix. | **Modify** | Consume an externally owned action policy matrix and enforce it fail closed; do not own policy creation. | V1 has an internal matrix but ownership is unresolved. |
| `LIVE-V2-FR-026` | Emergency fail-safe classification shall come only from the approved live action policy matrix. | **Modify** | Consume an externally owned action policy matrix and enforce it fail closed; do not own policy creation. | V1 has an internal matrix but ownership is unresolved. |
| `LIVE-V2-FR-027` | `disable_new_orders` behavior shall be dictated by the live action policy matrix. The functional requirement is enforcement of the matrix, not self-classification by the runtime. | **Modify** | Consume an externally owned action policy matrix and enforce it fail closed; do not own policy creation. | V1 has an internal matrix but ownership is unresolved. |
| `LIVE-V2-FR-028` | Live runtime shall require valid approval context for each action classified as approval-required in the live action policy matrix. | **Modify** | Validate an externally issued approval contract at gate time and again immediately before send. | V1 approval tokens exist but the final contract needs scope/expiry/revocation fields. |
| `LIVE-V2-FR-029` | Approval context shall include approval ID, approved action type, approved account scope, strategy scope where applicable, symbol scope where applicable, risk decision reference where applicable, approver identity reference, approval timestamp, expiration timestamp, approval state, and audit metadata. | **Modify** | Validate an externally issued approval contract at gate time and again immediately before send. | V1 approval tokens exist but the final contract needs scope/expiry/revocation fields. |
| `LIVE-V2-FR-030` | Live runtime shall reject approval context that is expired, revoked, not approved, outside action scope, outside account scope, outside strategy or symbol scope, or missing required audit metadata. | **Modify** | Validate an externally issued approval contract at gate time and again immediately before send. | V1 approval tokens exist but the final contract needs scope/expiry/revocation fields. |
| `LIVE-V2-FR-031` | Approval expiry between gate evaluation and broker send shall block mutation or produce an unknown/incident state only if a broker send already occurred. | **Modify** | Validate an externally issued approval contract at gate time and again immediately before send. | V1 approval tokens exist but the final contract needs scope/expiry/revocation fields. |
| `LIVE-V2-FR-032` | `submit_order(route="live")` shall return a blocked result unless the canonical live route gate passes. If the gate passes and live mutation is disabled, it shall return a packaged-only submit request. If the gate passes and live mutation is enabled, it may call an approved broker adapter and shall record the resulting side-effect state. | **Merge** | Apply the canonical live gate to the shared Trading actions and evidence/report functions. | Avoid duplicate live action implementations. |
| `LIVE-V2-FR-033` | `modify_order(route="live")` shall follow the canonical live route gate and shall preserve order identity, approved mutation scope, idempotency material, and side-effect mode. | **Merge** | Apply the canonical live gate to the shared Trading actions and evidence/report functions. | Avoid duplicate live action implementations. |
| `LIVE-V2-FR-034` | `cancel_order(route="live")` shall follow the canonical live route gate and shall preserve order identity, cancel reason, idempotency material, and side-effect mode. | **Merge** | Apply the canonical live gate to the shared Trading actions and evidence/report functions. | Avoid duplicate live action implementations. |
| `LIVE-V2-FR-035` | `close_position(route="live")` shall follow the canonical live route gate and shall preserve position identity, close scope, risk/approval references, idempotency material, and side-effect mode. | **Merge** | Apply the canonical live gate to the shared Trading actions and evidence/report functions. | Avoid duplicate live action implementations. |
| `LIVE-V2-FR-036` | `modify_position(route="live")` shall follow the canonical live route gate and shall preserve stop-loss or take-profit mutation scope, broker constraints, idempotency material, and side-effect mode. | **Merge** | Apply the canonical live gate to the shared Trading actions and evidence/report functions. | Avoid duplicate live action implementations. |
| `LIVE-V2-FR-037` | `reduce_exposure(route="live")` shall follow the canonical live route gate and shall preserve the approved reduction scope, position/symbol/account scope, idempotency material, and side-effect mode. | **Merge** | Apply the canonical live gate to the shared Trading actions and evidence/report functions. | Avoid duplicate live action implementations. |
| `LIVE-V2-FR-038` | `pause_strategy(route="live")` and `resume_strategy(route="live")` shall be operational live controls only and shall not replace strategy lifecycle promotion or approval. | **Merge** | Apply the canonical live gate to the shared Trading actions and evidence/report functions. | Avoid duplicate live action implementations. |
| `LIVE-V2-FR-039` | `sync_positions(route="live")` shall package live position synchronization from broker state and shall not mutate broker orders or positions. | **Merge** | Apply the canonical live gate to the shared Trading actions and evidence/report functions. | Avoid duplicate live action implementations. |
| `LIVE-V2-FR-040` | `reconcile_state(route="live")` shall package reconciliation of internal state against broker truth and shall record mismatch, unknown-outcome, and incident states. | **Merge** | Apply the canonical live gate to the shared Trading actions and evidence/report functions. | Avoid duplicate live action implementations. |
| `LIVE-V2-FR-041` | `build_trading_report(route="live")` shall package a live execution result report request without recomputing or fabricating execution evidence. | **Merge** | Apply the canonical live gate to the shared Trading actions and evidence/report functions. | Avoid duplicate live action implementations. |
| `LIVE-V2-FR-042` | Live configuration shall be validated at startup. Any invalid configured broker provider, strategy reference, trading setting, safety setting, notification route, logging setting, state setting, or secret reference shall prevent live trading until corrected. | **Modify** | Validate startup configuration and opaque secret references; use injected resolution and prohibit raw secret values. | V1 config/security components can be refactored. |
| `LIVE-V2-FR-043` | Live config parsing shall resolve only approved secret references, reject raw secret values where prohibited, and return structured validation errors without exposing secret values. | **Modify** | Validate startup configuration and opaque secret references; use injected resolution and prohibit raw secret values. | V1 config/security components can be refactored. |
| `LIVE-V2-FR-044` | Live secrets helpers shall resolve configured secret references without logging secret values. | **Modify** | Validate startup configuration and opaque secret references; use injected resolution and prohibit raw secret values. | V1 config/security components can be refactored. |
| `LIVE-V2-FR-045` | Live engine/session/run helpers shall orchestrate live runtime startup, shutdown, signal handling, and structured runtime status/event emission. | **Merge** | Retain live session startup, startup reconciliation, safe shutdown and recovery state inside the unified Trading live runtime. | V1 session and shutdown components provide a base. |
| `LIVE-V2-FR-046` | Live startup shall run broker readiness and startup reconciliation before live recovery or live mutation workflows. | **Merge** | Retain live session startup, startup reconciliation, safe shutdown and recovery state inside the unified Trading live runtime. | V1 session and shutdown components provide a base. |
| `LIVE-V2-FR-047` | Live startup shall not permit live mutation until startup reconciliation completes successfully or produces an approved operator-cleared recovery state. | **Merge** | Retain live session startup, startup reconciliation, safe shutdown and recovery state inside the unified Trading live runtime. | V1 session and shutdown components provide a base. |
| `LIVE-V2-FR-048` | Live shutdown shall stop accepting new live mutation requests before preserving state, flushing audit evidence, and reporting unresolved live work. | **Merge** | Retain live session startup, startup reconciliation, safe shutdown and recovery state inside the unified Trading live runtime. | V1 session and shutdown components provide a base. |
| `LIVE-V2-FR-049` | Live state manager shall preserve runtime state needed for live execution recovery and monitoring. | **Merge** | Retain live session startup, startup reconciliation, safe shutdown and recovery state inside the unified Trading live runtime. | V1 session and shutdown components provide a base. |
| `LIVE-V2-FR-050` | Signal processor shall transform strategy signals into live trading candidates only through approved runtime checks. | **Reject** | Do not keep a raw strategy-signal processor in Trading; upstream orchestration must submit the canonical Trading request. | V1 capability is test-only and boundary-blurring. |
| `LIVE-V2-FR-051` | Trade executor shall enforce live execution safety checks before broker mutation. | **Merge** | The canonical live gate plus route dispatcher is the trade executor; no separate `TradeExecutor` class is required. | Avoids duplicate execution layers. |
| `LIVE-V2-FR-052` | Position manager shall maintain live position views used by trading decisions. | **Modify** | Maintain authoritative order/position projections in state/reconciliation; no generic `PositionManager` abstraction is required. | State ownership is justified; the named layer is not. |
| `LIVE-V2-FR-053` | Notification adapter shall send live execution success/failure notifications through configured safe channels. | **Add** | Emit redacted execution outcome notifications through an injected safe notifier. | V1 has notification payload support but no confirmed connected workflow. |
| `LIVE-V2-FR-054` | `trigger_global_kill_switch` shall package global trading kill-switch activation only after approval gates unless explicitly classified as an emergency fail-safe action. | **Modify** | Retain scoped kill-switch activation/enforcement, mass actions and approved clearing through the normal gate and external policy matrix. | V1 has triggers/evaluation but the trigger-to-state bridge is incomplete. |
| `LIVE-V2-FR-055` | `trigger_strategy_kill_switch` shall package strategy-level kill-switch activation only after approval gates unless explicitly classified as an emergency fail-safe action. | **Modify** | Retain scoped kill-switch activation/enforcement, mass actions and approved clearing through the normal gate and external policy matrix. | V1 has triggers/evaluation but the trigger-to-state bridge is incomplete. |
| `LIVE-V2-FR-056` | `trigger_symbol_kill_switch` shall package symbol-level kill-switch activation only after approval gates unless explicitly classified as an emergency fail-safe action. | **Modify** | Retain scoped kill-switch activation/enforcement, mass actions and approved clearing through the normal gate and external policy matrix. | V1 has triggers/evaluation but the trigger-to-state bridge is incomplete. |
| `LIVE-V2-FR-057` | Kill-switch trigger tools shall consume emergency fail-safe classification only from the approved live action policy matrix and shall not infer emergency status from request text, user role, chat instruction, UI input, or API route. | **Modify** | Retain scoped kill-switch activation/enforcement, mass actions and approved clearing through the normal gate and external policy matrix. | V1 has triggers/evaluation but the trigger-to-state bridge is incomplete. |
| `LIVE-V2-FR-058` | `check_kill_switch_conditions` shall package kill-switch trigger-condition evaluation. | **Modify** | Retain scoped kill-switch activation/enforcement, mass actions and approved clearing through the normal gate and external policy matrix. | V1 has triggers/evaluation but the trigger-to-state bridge is incomplete. |
| `LIVE-V2-FR-059` | `disable_new_orders` shall package or perform disabling new order submission according to the live action policy matrix. | **Modify** | Retain scoped kill-switch activation/enforcement, mass actions and approved clearing through the normal gate and external policy matrix. | V1 has triggers/evaluation but the trigger-to-state bridge is incomplete. |
| `LIVE-V2-FR-060` | `cancel_all_orders` shall package cancellation of all pending orders only after approval gates. | **Modify** | Retain scoped kill-switch activation/enforcement, mass actions and approved clearing through the normal gate and external policy matrix. | V1 has triggers/evaluation but the trigger-to-state bridge is incomplete. |
| `LIVE-V2-FR-061` | `close_all_positions` shall package closing all positions only after approval gates. | **Modify** | Retain scoped kill-switch activation/enforcement, mass actions and approved clearing through the normal gate and external policy matrix. | V1 has triggers/evaluation but the trigger-to-state bridge is incomplete. |
| `LIVE-V2-FR-062` | `record_kill_switch_event` shall package durable kill-switch event recording. | **Modify** | Retain scoped kill-switch activation/enforcement, mass actions and approved clearing through the normal gate and external policy matrix. | V1 has triggers/evaluation but the trigger-to-state bridge is incomplete. |
| `LIVE-V2-FR-063` | `require_reenable_approval` shall require approval before trading can be re-enabled. | **Modify** | Retain scoped kill-switch activation/enforcement, mass actions and approved clearing through the normal gate and external policy matrix. | V1 has triggers/evaluation but the trigger-to-state bridge is incomplete. |
| `LIVE-V2-FR-064` | `clear_kill_switch_after_approval` shall package kill-switch clearing only after approval gates. | **Modify** | Retain scoped kill-switch activation/enforcement, mass actions and approved clearing through the normal gate and external policy matrix. | V1 has triggers/evaluation but the trigger-to-state bridge is incomplete. |
| `LIVE-V2-FR-065` | Active kill switch shall block live trading requests regardless of route request text, UI input, API input, or chat instruction. | **Modify** | Retain scoped kill-switch activation/enforcement, mass actions and approved clearing through the normal gate and external policy matrix. | V1 has triggers/evaluation but the trigger-to-state bridge is incomplete. |
| `LIVE-V2-FR-066` | Broker-truth snapshots shall normalize broker positions, orders, account, and timestamp evidence. | **Merge** | Use the shared Trading reconciliation contracts and persistence events for live broker truth. | Duplicate live reconciliation API is unnecessary. |
| `LIVE-V2-FR-067` | Live reconciliation comparison shall detect missing, extra, mismatched, and stale broker/internal records. | **Merge** | Use the shared Trading reconciliation contracts and persistence events for live broker truth. | Duplicate live reconciliation API is unnecessary. |
| `LIVE-V2-FR-068` | Live reconciliation persistence shall preserve reconciliation runs, mismatches, incidents, and evidence references through the approved persistence interface. | **Merge** | Use the shared Trading reconciliation contracts and persistence events for live broker truth. | Duplicate live reconciliation API is unnecessary. |
| `LIVE-V2-FR-069` | Live authority-state transitions shall remain pending until the reconciliation state machine is approved; until then, production live broker mutation shall remain disabled. | **Open Decision** | Production mutation remains disabled until the authority-state transition model and persistence contract are approved. | The requirement explicitly marks the state machine pending. |
| `LIVE-V2-FR-070` | Startup reconciliation shall run before live recovery or live mutation workflows. | **Modify** | Require startup reconciliation, broker-truth precedence, retry guard and durable idempotency before live send. | V1 has these components but full production composition is unconfirmed. |
| `LIVE-V2-FR-071` | Retry guard behavior shall prevent unsafe blind retries after unknown broker outcomes. | **Modify** | Require startup reconciliation, broker-truth precedence, retry guard and durable idempotency before live send. | V1 has these components but full production composition is unconfirmed. |
| `LIVE-V2-FR-072` | Unknown broker outcomes shall block blind retry until broker truth resolves the live authority state. | **Modify** | Require startup reconciliation, broker-truth precedence, retry guard and durable idempotency before live send. | V1 has these components but full production composition is unconfirmed. |
| `LIVE-V2-FR-073` | Live reconciliation incidents shall package discrepancy severity, evidence, action requirement, and audit context. | **Modify** | Require startup reconciliation, broker-truth precedence, retry guard and durable idempotency before live send. | V1 has these components but full production composition is unconfirmed. |
| `LIVE-V2-FR-074` | Reconciliation shall prefer broker truth when determining live authority state. | **Modify** | Require startup reconciliation, broker-truth precedence, retry guard and durable idempotency before live send. | V1 has these components but full production composition is unconfirmed. |
| `LIVE-V2-FR-075` | Live runtime shall persist idempotency records before any broker mutation attempt where persistence is available and shall fail closed if required idempotency persistence cannot be written. | **Modify** | Require startup reconciliation, broker-truth precedence, retry guard and durable idempotency before live send. | V1 has these components but full production composition is unconfirmed. |
| `LIVE-V2-FR-076` | Each approved broker adapter shall expose a documented capability contract before Live can use it for broker mutation. | **Add** | Require an approved adapter capability/security/error contract and conservative malformed/rate-limit response classification before use. | V1 capability validation exists but not the complete external contract. |
| `LIVE-V2-FR-077` | Broker adapter contracts shall define provider ID, API/version compatibility, supported actions, symbol metadata access, account/order/position snapshot access, readiness checks, request schema, response schema, timeout behavior, rate-limit behavior, malformed-response handling, error mapping, retry-safety classification, and redaction rules. | **Add** | Require an approved adapter capability/security/error contract and conservative malformed/rate-limit response classification before use. | V1 capability validation exists but not the complete external contract. |
| `LIVE-V2-FR-078` | Malformed broker success responses, including HTTP 200 or equivalent success status with missing required fields or invalid data types, shall be classified as `unknown_outcome`, shall trigger reconciliation, and shall not be treated as confirmed broker mutation. | **Add** | Require an approved adapter capability/security/error contract and conservative malformed/rate-limit response classification before use. | V1 capability validation exists but not the complete external contract. |
| `LIVE-V2-FR-079` | Broker adapter readiness shall fail closed on unsupported API version, deprecated endpoint use, missing capability declaration, stale symbol metadata, missing account snapshot, or incompatible response schema version. | **Add** | Require an approved adapter capability/security/error contract and conservative malformed/rate-limit response classification before use. | V1 capability validation exists but not the complete external contract. |
| `LIVE-V2-FR-080` | Broker-side rate limiting, including HTTP 429 or provider-equivalent rate-limit responses, shall not be retried blindly. | **Add** | Require an approved adapter capability/security/error contract and conservative malformed/rate-limit response classification before use. | V1 capability validation exists but not the complete external contract. |
| `LIVE-V2-FR-081` | Broker rate-limit responses shall return `retry_safety="safe_to_retry"` only when the adapter contract proves no broker mutation occurred; otherwise they shall return `retry_safety="retry_after_reconciliation"` or `do_not_retry`. | **Add** | Require an approved adapter capability/security/error contract and conservative malformed/rate-limit response classification before use. | V1 capability validation exists but not the complete external contract. |
| `LIVE-V2-FR-082` | Broker rate-limit responses shall include `retry_after_seconds` when the provider supplies or the approved rate-limit policy derives a retry delay. | **Add** | Require an approved adapter capability/security/error contract and conservative malformed/rate-limit response classification before use. | V1 capability validation exists but not the complete external contract. |
| `LIVE-V2-FR-083` | Broker rate-limit backoff policy shall be approved before production live mutation. Proposed Decision: exponential backoff with jitter and at most three attempts before incident escalation. | **Open Decision** | Approve retry/backoff only per provider contract and only when no mutation is proven; do not approve three attempts globally yet. | Blind generic backoff is unsafe. |
| `LIVE-V2-FR-084` | Broker communication security is a mandatory pre-production gate. Live shall not allow production broker mutation until the approved security profile defines encrypted transport, certificate validation requirements, credential handling, logging restrictions, and adapter compliance tests. | **Keep** | Block production mutation until broker communication security is approved and tested. | Mandatory pre-production safety gate. |
| `LIVE-V2-FR-085` | Live runtime shall define a concurrency coordination contract before Builder handoff. | **Open Decision** | Approve exact lock/version scopes, timeout and stale-lock recovery before implementation handoff. | V1 has per-account/symbol locks but the final scope is unresolved. |
| `LIVE-V2-FR-086` | The concurrency coordination contract shall specify whether coordination uses per-account locks, per-symbol locks, per-order/position locks, optimistic version checks, or another approved mechanism. | **Open Decision** | Approve exact lock/version scopes, timeout and stale-lock recovery before implementation handoff. | V1 has per-account/symbol locks but the final scope is unresolved. |
| `LIVE-V2-FR-087` | Conflicting actions for the same account, strategy, symbol, order, or position shall be serialized, rejected with a deterministic conflict error, or coordinated through an approved optimistic concurrency rule. | **Keep** | Conflicting live actions must be serialized or deterministically rejected. | Core safety behavior. |
| `LIVE-V2-FR-088` | The coordination contract shall define lock acquisition timeout, stale lock recovery, conflict error code, idempotency interaction, and audit evidence. | **Open Decision** | Approve exact lock/version scopes, timeout and stale-lock recovery before implementation handoff. | V1 has per-account/symbol locks but the final scope is unresolved. |
| `LIVE-V2-FR-089` | Tool health monitoring shall track last successful call time, last failure time, consecutive failure count, timeout count, dependency status, and current health state for each exported live tool. | **Modify** | Retain minimal health, timeout, staleness, ingestion, incident and latency events with approved thresholds. | V1 components exist but are not production-wired. |
| `LIVE-V2-FR-090` | Workflow timeout monitoring shall detect stale or overdue live workflows. | **Modify** | Retain minimal health, timeout, staleness, ingestion, incident and latency events with approved thresholds. | V1 components exist but are not production-wired. |
| `LIVE-V2-FR-091` | Workflows exceeding configured `live_workflow_timeout_seconds` shall trigger a `WORKFLOW_TIMEOUT` incident. | **Modify** | Retain minimal health, timeout, staleness, ingestion, incident and latency events with approved thresholds. | V1 components exist but are not production-wired. |
| `LIVE-V2-FR-092` | Stale-state monitoring shall identify stale market, account, broker, approval, or risk state. | **Modify** | Retain minimal health, timeout, staleness, ingestion, incident and latency events with approved thresholds. | V1 components exist but are not production-wired. |
| `LIVE-V2-FR-093` | Stale-state monitoring shall tie broker/account/order/position freshness checks to approved market-data freshness thresholds where broker mutation depends on current market state. | **Modify** | Retain minimal health, timeout, staleness, ingestion, incident and latency events with approved thresholds. | V1 components exist but are not production-wired. |
| `LIVE-V2-FR-094` | Live readiness stale thresholds shall be configurable per context type and shall be enforced deterministically. | **Modify** | Retain minimal health, timeout, staleness, ingestion, incident and latency events with approved thresholds. | V1 components exist but are not production-wired. |
| `LIVE-V2-FR-095` | Live broker adapter calls shall have configured timeout limits and shall classify timeout as unknown outcome unless broker truth proves otherwise. | **Modify** | Retain minimal health, timeout, staleness, ingestion, incident and latency events with approved thresholds. | V1 components exist but are not production-wired. |
| `LIVE-V2-FR-096` | Ingestion monitoring shall track whether required live inputs are arriving. | **Modify** | Retain minimal health, timeout, staleness, ingestion, incident and latency events with approved thresholds. | V1 components exist but are not production-wired. |
| `LIVE-V2-FR-097` | Incident classification shall classify live incidents by severity and action need. | **Modify** | Retain minimal health, timeout, staleness, ingestion, incident and latency events with approved thresholds. | V1 components exist but are not production-wired. |
| `LIVE-V2-FR-098` | Latency helpers shall record live trading timing and latency diagnostics. | **Modify** | Retain minimal health, timeout, staleness, ingestion, incident and latency events with approved thresholds. | V1 components exist but are not production-wired. |
| `LIVE-V2-FR-099` | Snapshot caches shall preserve recent live performance snapshots. | **Defer** | Defer live performance snapshot caches unless needed for readiness or audit. | No confirmed critical workflow. |
| `LIVE-V2-FR-100` | Cost enforcement shall enforce per-request, workflow, and session cost budgets and record cost entries. | **Modify** | Consume externally owned budget limits/verdicts, block before send and emit an incident after send when exceeded. | V1 CostController is disconnected and should not own policy. |
| `LIVE-V2-FR-101` | Live runtime shall prevent broker mutation when cost budget is exceeded before broker send. | **Modify** | Consume externally owned budget limits/verdicts, block before send and emit an incident after send when exceeded. | V1 CostController is disconnected and should not own policy. |
| `LIVE-V2-FR-102` | If cost budget is exceeded after gate approval but before broker send, the runtime shall block mutation and record a cost-budget incident. | **Modify** | Consume externally owned budget limits/verdicts, block before send and emit an incident after send when exceeded. | V1 CostController is disconnected and should not own policy. |
| `LIVE-V2-FR-103` | Live runtime shall record an incident when cost budget is exceeded after broker send but before reconciliation completion. | **Modify** | Consume externally owned budget limits/verdicts, block before send and emit an incident after send when exceeded. | V1 CostController is disconnected and should not own policy. |
| `LIVE-V2-FR-104` | Live reports shall include approvals, risk decisions, route, broker evidence, receipts, reconciliation state, incidents, warnings, and unresolved actions. | **Modify** | Trading packages live execution/reconciliation/incident evidence; Analytics owns derived performance metrics. | Avoids domain duplication. |
| `LIVE-V2-FR-105` | Performance tests shall use approved values from this table or later owner-approved replacements. | **Keep** | Performance tests use only approved target values. | Sound process rule. |
| `LIVE-V2-FR-106` | Production live broker mutation is strictly blocked until all `Proposed Decision` statuses in this table are updated to `Decision: Approved` by the owner/architect or replaced by approved values. | **Reject** | Do not block production solely on every throughput/latency target being approved; block on safety contracts and use approved operational limits where necessary. | Performance SLO approval is not equivalent to mutation safety. |
| `LIVE-V2-FR-107` | Shadow data feeds shall package production-like account, portfolio, market, and environment snapshots. | **Defer** | Defer shadow feed/execution/comparison; preserve the no-live-reference invariant for later implementation. | Optional future capability. |
| `LIVE-V2-FR-108` | Shadow execution shall execute production-like workflows without real broker mutation. | **Defer** | Defer shadow feed/execution/comparison; preserve the no-live-reference invariant for later implementation. | Optional future capability. |
| `LIVE-V2-FR-109` | Shadow comparison reports shall compare expected and realized fill/PnL outcomes. | **Defer** | Defer shadow feed/execution/comparison; preserve the no-live-reference invariant for later implementation. | Optional future capability. |
| `LIVE-V2-FR-110` | Shadow execution shall not be treated as live broker approval or live readiness by itself. | **Defer** | Defer shadow feed/execution/comparison; preserve the no-live-reference invariant for later implementation. | Optional future capability. |
| `LIVE-V2-FR-111` | Shadow execution shall fail closed if it receives a live account reference or live broker adapter reference. | **Defer** | Defer shadow feed/execution/comparison; preserve the no-live-reference invariant for later implementation. | Optional future capability. |
| `LIVE-V2-NFR-001` | Live shall fail closed on missing approval, missing risk context, stale broker/account state, active kill switch, reconciliation mismatch, idempotency conflict, disabled live flag, or unknown broker result. | **Merge** | Retain this non-functional requirement in the unified Trading live runtime and shared contract. | Valid safety/operability behavior; separate Live domain is removed. |
| `LIVE-V2-NFR-002` | Live mutations shall be disabled by default. | **Merge** | Retain this non-functional requirement in the unified Trading live runtime and shared contract. | Valid safety/operability behavior; separate Live domain is removed. |
| `LIVE-V2-NFR-003` | Critical live and kill-switch actions shall require explicit approval context unless classified as emergency fail-safe actions by the approved live action policy matrix. | **Merge** | Retain this non-functional requirement in the unified Trading live runtime and shared contract. | Valid safety/operability behavior; separate Live domain is removed. |
| `LIVE-V2-NFR-004` | Broker calls shall be isolated behind approved adapters or bridges. | **Merge** | Retain this non-functional requirement in the unified Trading live runtime and shared contract. | Valid safety/operability behavior; separate Live domain is removed. |
| `LIVE-V2-NFR-005` | Live outputs shall be structured, traceable, redacted, and JSON-safe. | **Merge** | Retain this non-functional requirement in the unified Trading live runtime and shared contract. | Valid safety/operability behavior; separate Live domain is removed. |
| `LIVE-V2-NFR-006` | Live errors shall use documented error codes from a finite taxonomy and shall include request ID, correlation ID, failed gate where applicable, retry-safety classification, operator action hint, and audit reference when available. | **Merge** | Retain this non-functional requirement in the unified Trading live runtime and shared contract. | Valid safety/operability behavior; separate Live domain is removed. |
| `LIVE-V2-NFR-007` | Secrets, credentials, tokens, authorization headers, private broker payloads, and raw approval packets shall not leak through logs, errors, notifications, metrics, reports, or chat. | **Merge** | Retain this non-functional requirement in the unified Trading live runtime and shared contract. | Valid safety/operability behavior; separate Live domain is removed. |
| `LIVE-V2-NFR-008` | Loggers and redaction helpers shall recursively scrub fields whose names contain `secret`, `token`, `key`, `authorization`, `password`, `credential`, or `api_key`, case-insensitively, before logs, errors, reports, notifications, metrics, or chat output are emitted. | **Merge** | Retain this non-functional requirement in the unified Trading live runtime and shared contract. | Valid safety/operability behavior; separate Live domain is removed. |
| `LIVE-V2-NFR-009` | Raw broker payloads shall be stored only as redacted evidence references unless explicitly classified safe. | **Merge** | Retain this non-functional requirement in the unified Trading live runtime and shared contract. | Valid safety/operability behavior; separate Live domain is removed. |
| `LIVE-V2-NFR-010` | Idempotency shall prevent unsafe duplicate live execution and shall not be mistaken for exactly-once broker semantics. | **Merge** | Retain this non-functional requirement in the unified Trading live runtime and shared contract. | Valid safety/operability behavior; separate Live domain is removed. |
| `LIVE-V2-NFR-011` | Unknown broker outcomes shall block blind retries until reconciliation resolves state. | **Merge** | Retain this non-functional requirement in the unified Trading live runtime and shared contract. | Valid safety/operability behavior; separate Live domain is removed. |
| `LIVE-V2-NFR-012` | Reconciliation shall prefer broker truth when determining live authority state. | **Merge** | Retain this non-functional requirement in the unified Trading live runtime and shared contract. | Valid safety/operability behavior; separate Live domain is removed. |
| `LIVE-V2-NFR-013` | Paper, simulation, and shadow trading shall remain separate from live broker mutation. | **Merge** | Retain this non-functional requirement in the unified Trading live runtime and shared contract. | Valid safety/operability behavior; separate Live domain is removed. |
| `LIVE-V2-NFR-014` | Live tools shall preserve clear side-effect flags and approval requirements. | **Merge** | Retain this non-functional requirement in the unified Trading live runtime and shared contract. | Valid safety/operability behavior; separate Live domain is removed. |
| `LIVE-V2-NFR-015` | Live runtime components shall support safe startup, safe shutdown, signal handling, and recovery diagnostics. | **Merge** | Retain this non-functional requirement in the unified Trading live runtime and shared contract. | Valid safety/operability behavior; separate Live domain is removed. |
| `LIVE-V2-NFR-016` | Live runtime shall enforce bounded queue sizes or explicit rejection behavior under request overload. | **Open Decision** | Require bounded overload behavior, but approve the queue/rejection model and limits before implementation. | No workload evidence supports a concrete queue. |
| `LIVE-V2-NFR-017` | Live runtime shall serialize or otherwise safely coordinate conflicting actions for the same account, strategy, symbol, order, or position. | **Merge** | Retain this non-functional requirement in the unified Trading live runtime and shared contract. | Valid safety/operability behavior; separate Live domain is removed. |
| `LIVE-V2-NFR-018` | Importing live modules shall not start broker sessions, start background workers, mutate state, or resolve raw secret values. | **Merge** | Retain this non-functional requirement in the unified Trading live runtime and shared contract. | Valid safety/operability behavior; separate Live domain is removed. |
| `LIVE-V2-NFR-019` | Importing live modules shall not resolve secrets, open sockets, spawn threads, start async tasks, or initialize broker SDK sessions. | **Merge** | Retain this non-functional requirement in the unified Trading live runtime and shared contract. | Valid safety/operability behavior; separate Live domain is removed. |
| `LIVE-V2-NFR-020` | Broker communication security shall be enforced through an owner/architect-approved security profile before production broker mutation can be enabled. | **Merge** | Retain this non-functional requirement in the unified Trading live runtime and shared contract. | Valid safety/operability behavior; separate Live domain is removed. |
| `LIVE-V2-NFR-021` | The approved broker communication security profile shall define minimum encrypted transport version, certificate validation or pinning requirements where supported, credential handling, adapter compliance evidence, and failure behavior. | **Merge** | Retain this non-functional requirement in the unified Trading live runtime and shared contract. | Valid safety/operability behavior; separate Live domain is removed. |
| `LIVE-V2-NFR-022` | Monitoring shall expose stale state, timeouts, health failures, incidents, latency, and cost-budget conditions. | **Modify** | Expose a focused monitoring event set; external observability owns aggregation and transport. | Avoids duplicating observability infrastructure. |
| `LIVE-V2-NFR-023` | Compensation behavior shall be allowed only for approved compensation action classes. Each compensation action shall define preconditions, maximum scope, approval requirement, timeout, audit evidence, retry policy, and terminal failure behavior. | **Defer** | Defer generalized compensation until an approved catalog and ownership model exist. | No initial catalog is approved. |
| `LIVE-V2-NFR-024` | Live runtime shall not overstate readiness or safety when context is partial or stale. | **Merge** | Retain this non-functional requirement in the unified Trading live runtime and shared contract. | Valid safety/operability behavior; separate Live domain is removed. |
| `LIVE-V2-NFR-025` | Public registry changes shall remain covered by tests and catalog updates. | **Merge** | Retain this non-functional requirement in the unified Trading live runtime and shared contract. | Valid safety/operability behavior; separate Live domain is removed. |
| `LIVE-V2-TST-001` | Live registry tests shall prove the approved live runtime and governance surface is exported intentionally. | **Merge** | Test the unified Trading registry/envelope, including live-only classifications, rather than a separate live registry. | Matches the one-package design. |
| `LIVE-V2-TST-002` | Callable/docstring tests shall cover every exported live service tool. | **Merge** | Test the unified Trading registry/envelope, including live-only classifications, rather than a separate live registry. | Matches the one-package design. |
| `LIVE-V2-TST-003` | Contract tests shall cover every exported public tool input schema, result-envelope schema, risk level, approval requirement, side-effect flag, stability, and documentation reference. | **Merge** | Test the unified Trading registry/envelope, including live-only classifications, rather than a separate live registry. | Matches the one-package design. |
| `LIVE-V2-TST-004` | Standard-envelope snapshot tests shall cover success, blocked, rejected, packaged-only, mutation-attempted, mutation-confirmed, unknown-outcome, and incident states. | **Merge** | Test the unified Trading registry/envelope, including live-only classifications, rather than a separate live registry. | Matches the one-package design. |
| `LIVE-V2-TST-005` | Live gate tests shall prove each gate returns deterministic pass/block/error results and that gate failures stop unsafe downstream actions. | **Add** | Add or extend this safety, contract or integration test in the unified Trading test suite. | The V1 audit does not prove complete coverage. |
| `LIVE-V2-TST-006` | Diagnostic-only gate tests shall prove only approved local diagnostic gates run after mandatory gate failure and that they do not mutate state, call broker adapters, or require network access. | **Reject** | No post-failure diagnostic-gate framework will be implemented initially. | Test requirement follows rejected architecture. |
| `LIVE-V2-TST-007` | Critical live-route tests shall prove shared trading functions block without approval ID when approval is required. | **Add** | Add or extend this safety, contract or integration test in the unified Trading test suite. | The V1 audit does not prove complete coverage. |
| `LIVE-V2-TST-008` | Policy matrix consistency tests shall prove every action mentioned in functional requirements has a defined matrix entry with approval class, emergency flag, idempotency requirement, side-effect ceiling, and audit requirement. | **Add** | Add or extend this safety, contract or integration test in the unified Trading test suite. | The V1 audit does not prove complete coverage. |
| `LIVE-V2-TST-009` | Package-only tests shall prove no broker adapter call occurs when live mutation is disabled. | **Add** | Add or extend this safety, contract or integration test in the unified Trading test suite. | The V1 audit does not prove complete coverage. |
| `LIVE-V2-TST-010` | Mutation-enabled tests with mocks shall prove adapter calls occur only after all mandatory gates pass. | **Add** | Add or extend this safety, contract or integration test in the unified Trading test suite. | The V1 audit does not prove complete coverage. |
| `LIVE-V2-TST-011` | Live execution tests with mocks shall prove submit, modify, cancel, close, pause, resume, exposure reduction, sync, reconciliation, and reports require approval and fail closed when context is missing. | **Add** | Add or extend this safety, contract or integration test in the unified Trading test suite. | The V1 audit does not prove complete coverage. |
| `LIVE-V2-TST-012` | Kill-switch tests shall cover global, strategy, symbol, disable orders, cancel all, close all, record event, require re-enable approval, and clear after approval. | **Add** | Add or extend this safety, contract or integration test in the unified Trading test suite. | The V1 audit does not prove complete coverage. |
| `LIVE-V2-TST-013` | Approval context tests shall reject expired, revoked, out-of-scope, malformed, missing-audit, and wrong-action approvals. | **Add** | Add or extend this safety, contract or integration test in the unified Trading test suite. | The V1 audit does not prove complete coverage. |
| `LIVE-V2-TST-014` | Approval packet completeness, state-machine, creation, voting, override, and distinct-approver tests shall cover live governance only after ownership is approved by the governance module. | **Reject** | Governance creation/voting/override tests belong to Governance; Trading tests only consumed approval validation. | Boundary correction. |
| `LIVE-V2-TST-015` | Idempotency tests shall cover duplicate same-material, duplicate different-material, and simultaneous duplicate live requests. | **Add** | Add or extend this safety, contract or integration test in the unified Trading test suite. | The V1 audit does not prove complete coverage. |
| `LIVE-V2-TST-016` | Broker bridge tests shall cover approved broker adapters, response classification, error mapping, timeout mapping, and fail-closed live behavior. | **Modify** | Test Trading against approved adapter contracts and mocks; concrete adapter implementation tests remain in Brokers. | Avoid duplicate ownership. |
| `LIVE-V2-TST-017` | Broker adapter contract tests shall cover capability discovery, readiness, API/version compatibility, malformed success responses, response schema validation, error mapping, and retry-safety classification. | **Add** | Add or extend this safety, contract or integration test in the unified Trading test suite. | The V1 audit does not prove complete coverage. |
| `LIVE-V2-TST-018` | Broker rate-limit tests shall cover HTTP 429 or provider-equivalent responses, `retry_after_seconds`, retry-safety classification, approved backoff limits, and incident escalation after backoff exhaustion. | **Open Decision** | Add provider-specific rate-limit tests after the approved backoff/retry contract is decided. | Policy remains unresolved. |
| `LIVE-V2-TST-019` | Reconciliation tests shall cover matched, missing, extra, mismatched, stale, unknown-outcome, startup, persistence, retry guard, restart recovery, and incident paths. | **Add** | Add or extend this safety, contract or integration test in the unified Trading test suite. | The V1 audit does not prove complete coverage. |
| `LIVE-V2-TST-020` | Monitoring tests shall cover stale state, ingestion health, workflow timeout, tool health, incident classification, latency, and snapshot cache behavior. | **Modify** | Test the retained minimal monitoring set; defer snapshot-cache cases. | Scope simplification. |
| `LIVE-V2-TST-021` | Cost enforcement tests shall cover per-request, workflow, session budget, before-send failure, and after-send incident behavior. | **Add** | Add or extend this safety, contract or integration test in the unified Trading test suite. | The V1 audit does not prove complete coverage. |
| `LIVE-V2-TST-022` | Live runtime tests with mocks shall cover config parsing, secret resolution, state manager, signal processor, trade executor, position manager, notifications, startup, shutdown, and safe recovery. | **Modify** | Test configuration, session, state, notification and recovery behavior; omit rejected SignalProcessor/PositionManager class prescriptions. | Behaviour over named layers. |
| `LIVE-V2-TST-023` | Shadow execution tests shall cover feed building, no-live-mutation execution, live-reference rejection, and expected-versus-realized reporting. | **Defer** | Defer shadow/compensation tests with those capabilities. | Not initial scope. |
| `LIVE-V2-TST-024` | Compensation tests shall cover order, position, registry, validation, execution, missing-plan, and audit-log behavior after compensation ownership is approved. | **Defer** | Defer shadow/compensation tests with those capabilities. | Not initial scope. |
| `LIVE-V2-TST-025` | Concurrency tests shall cover simultaneous submit/cancel, close/reduce exposure, pause/resume, duplicate idempotency keys, and kill-switch racing with live submit. | **Add** | Add or extend this safety, contract or integration test in the unified Trading test suite. | The V1 audit does not prove complete coverage. |
| `LIVE-V2-TST-026` | Restart tests shall cover persisted unknown outcomes, in-flight approvals, in-flight reconciliation, pending compensation, and startup mismatch blocking. | **Add** | Add or extend this safety, contract or integration test in the unified Trading test suite. | The V1 audit does not prove complete coverage. |
| `LIVE-V2-TST-027` | Performance and reliability tests shall cover readiness latency budget, reconciliation timeout, broker adapter timeout, bounded queue behavior, shutdown audit flush, and monitoring signal emission. | **Open Decision** | Run performance/reliability tests only against approved limits and targets. | Values are pending. |
| `LIVE-V2-TST-028` | Performance tests shall include approved concrete targets, including readiness latency, gate latency, reconciliation loop interval, adapter timeout, request throughput, queue-depth rejection, and shutdown audit flush once the owner approves those values. | **Open Decision** | Run performance/reliability tests only against approved limits and targets. | Values are pending. |
| `LIVE-V2-TST-029` | Chaos/network partition tests shall prove the runtime fails closed and records incidents when broker connection, audit sink, receipt read, or reconciliation persistence fails mid-mutation. | **Add** | Add or extend this safety, contract or integration test in the unified Trading test suite. | The V1 audit does not prove complete coverage. |
| `LIVE-V2-TST-030` | Broker communication security tests shall prove production mutation is blocked when the approved transport/security profile is missing, unsupported, or failed. | **Add** | Add or extend this safety, contract or integration test in the unified Trading test suite. | The V1 audit does not prove complete coverage. |
| `LIVE-V2-TST-031` | Security tests shall prove secrets, private broker payloads, and raw approval packets are redacted from errors, logs, reports, notifications, metrics, and chat. | **Add** | Add or extend this safety, contract or integration test in the unified Trading test suite. | The V1 audit does not prove complete coverage. |
| `LIVE-V2-TST-032` | Secrets redaction tests shall inject fake values such as `password: secret123` and prove no log line, error message, notification, metric, report, or chat response contains `secret123`. | **Add** | Add or extend this safety, contract or integration test in the unified Trading test suite. | The V1 audit does not prove complete coverage. |
| `LIVE-V2-TST-033` | Import-time safety tests shall prove importing live modules performs no broker connection, mutation, background start, or raw secret logging. | **Add** | Add or extend this safety, contract or integration test in the unified Trading test suite. | The V1 audit does not prove complete coverage. |
| `LIVE-V2-TST-034` | Usage-example tests shall prove examples remain executable against documented signatures and include blocked live mode, missing approval, active kill switch, package-only mode, and unknown outcome. | **Add** | Add or extend this safety, contract or integration test in the unified Trading test suite. | The V1 audit does not prove complete coverage. |
| `LIVE-V2-TST-035` | Unknown-outcome retry tests shall prove clients receive `retry_after_reconciliation` and cannot blindly retry before reconciliation. | **Add** | Add or extend this safety, contract or integration test in the unified Trading test suite. | The V1 audit does not prove complete coverage. |
| `LIVE-V2-TST-036` | Requirement traceability tests shall map every functional `shall` requirement to at least one named test or explicitly approved deferral. | **Add** | Add or extend this safety, contract or integration test in the unified Trading test suite. | The V1 audit does not prove complete coverage. |
| `LIVE-V2-PEND-001` | Production live broker mutation shall remain disabled until the decisions above are approved and referenced by version. | **Keep** | Keep production mutation disabled until all safety-critical open decisions are approved and versioned. | Appropriate launch gate; performance-only targets are excluded. |
| `LIVE-V2-PEND-002` | Broker communication security is not a deferrable pending decision for production; production broker mutation shall remain disabled until the mandatory broker communication security profile is approved and enforced. | **Keep** | Broker communication security remains a mandatory non-deferrable launch gate. | Critical safety requirement. |
| `LIVE-V2-NOTE-001` | Live is an operational runtime around `route="live"` trading functions, not a separate implementation of order and position behavior. | **Keep** | Implement live as an internal operational capability of the route-aware Trading package. | Matches the chosen domain design. |
| `LIVE-V2-NOTE-002` | Optional shadow expected-versus-realized PnL reporting can remain future work unless required before live launch. | **Defer** | Defer shadow PnL comparison and its production acceptance criteria. | Optional future work. |
| `LIVE-V2-NOTE-003` | Proposed Decision: shadow expected-versus-realized PnL reporting should be accepted for production only after an owner-approved paper-trading validation window and correlation threshold are defined. | **Defer** | Defer shadow PnL comparison and its production acceptance criteria. | Optional future work. |
| `LIVE-V2-NOTE-004` | Dashboard/runtime helper orchestration can remain future work if the runtime can operate safely without dashboard hints. | **Keep** | Dashboard helper orchestration is not required for the runtime core. | Avoids UI coupling. |
| `LIVE-V2-NOTE-005` | UI/dashboard rendering and websocket connection management are strictly out of scope for Live. Live may emit structured JSON events for approved consumers; rendering, websocket transport, and dashboard orchestration belong to API/UI or other consumer modules. | **Keep** | Keep UI rendering and websocket transport outside Trading; emit structured events only. | Correct boundary. |
| `LIVE-V2-NOTE-006` | Snapshot cache behavior can remain future work unless required for live readiness or audit. | **Defer** | Defer snapshot caching unless readiness or audit later requires it. | No demonstrated need. |
| `LIVE-V2-NOTE-007` | Public registry and catalog updates shall be mandatory when live tools are added, renamed, or removed. | **Merge** | Apply registry/catalog/test synchronization to the unified Trading registry. | No separate Live registry. |

### 6.4 `10_live.md` edge cases

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
| --- | --- | --- | --- | --- |
| `LIVE-V2-EDGE-001` | Empty request payload or malformed payload. | **Add** | Include this scenario in the final contract, validation, gate or integration test suite. | It exercises an accepted core behavior. |
| `LIVE-V2-EDGE-002` | Missing request ID or duplicate request ID. | **Add** | Add idempotency and coordination coverage using the approved conflict scope. | Critical duplicate/conflict behavior. |
| `LIVE-V2-EDGE-003` | Missing correlation ID where required. | **Add** | Include this scenario in the final contract, validation, gate or integration test suite. | It exercises an accepted core behavior. |
| `LIVE-V2-EDGE-004` | Missing approval ID for live or kill-switch action. | **Add** | Add deterministic policy/gate/race coverage in unified Trading. | Critical live safety case. |
| `LIVE-V2-EDGE-005` | Approval expires between gate evaluation and broker send. | **Add** | Include this scenario in the final contract, validation, gate or integration test suite. | It exercises an accepted core behavior. |
| `LIVE-V2-EDGE-006` | Approval is revoked or falls outside account, strategy, symbol, or action scope. | **Add** | Include this scenario in the final contract, validation, gate or integration test suite. | It exercises an accepted core behavior. |
| `LIVE-V2-EDGE-007` | Live mutation flag disabled. | **Add** | Include this scenario in the final contract, validation, gate or integration test suite. | It exercises an accepted core behavior. |
| `LIVE-V2-EDGE-008` | Active global, strategy, or symbol kill switch. | **Add** | Add deterministic policy/gate/race coverage in unified Trading. | Critical live safety case. |
| `LIVE-V2-EDGE-009` | Kill switch activates while a live request is in flight. | **Add** | Add deterministic policy/gate/race coverage in unified Trading. | Critical live safety case. |
| `LIVE-V2-EDGE-010` | Operator sends kill-switch trigger while live request is in flight; kill-switch activation must supersede the in-flight request and force block, incident, or reconciliation according to the approved state machine. | **Add** | Add deterministic policy/gate/race coverage in unified Trading. | Critical live safety case. |
| `LIVE-V2-EDGE-011` | Broker disconnected, stale broker time, stale quote, stale account snapshot, stale permissions, or stale symbol metadata. | **Add** | Include this scenario in the final contract, validation, gate or integration test suite. | It exercises an accepted core behavior. |
| `LIVE-V2-EDGE-012` | Broker API version skew or deprecated endpoint returned during readiness check. | **Add** | Add adapter-contract compatibility and fail-closed readiness coverage. | Missing from V1. |
| `LIVE-V2-EDGE-013` | Malformed broker response, including success status with missing required fields or wrong data types. | **Add** | Classify malformed success as unknown outcome and require reconciliation. | Important adapter safety case. |
| `LIVE-V2-EDGE-014` | Broker rate limiting, including HTTP 429 or provider-equivalent rate-limit response. | **Open Decision** | Retain the scenario, but finalize expected behavior after provider retry-safety/backoff contracts are approved. | Backoff policy is unresolved. |
| `LIVE-V2-EDGE-015` | Broker rate-limit backoff exhaustion before request acceptance is proven. | **Open Decision** | Retain the scenario, but finalize expected behavior after provider retry-safety/backoff contracts are approved. | Backoff policy is unresolved. |
| `LIVE-V2-EDGE-016` | Broker adapter timeout after broker accepted the request but before receipt is received. | **Add** | Add fault-path and unknown-outcome/reconciliation coverage. | V1 components exist but production behavior is not proven. |
| `LIVE-V2-EDGE-017` | Unknown broker result after a send attempt. | **Add** | Add fault-path and unknown-outcome/reconciliation coverage. | V1 components exist but production behavior is not proven. |
| `LIVE-V2-EDGE-018` | Duplicate idempotency key with different material fields. | **Add** | Add idempotency and coordination coverage using the approved conflict scope. | Critical duplicate/conflict behavior. |
| `LIVE-V2-EDGE-019` | Duplicate idempotency keys arriving simultaneously. | **Add** | Add idempotency and coordination coverage using the approved conflict scope. | Critical duplicate/conflict behavior. |
| `LIVE-V2-EDGE-020` | Existing send attempt with no authoritative receipt. | **Add** | Add fault-path and unknown-outcome/reconciliation coverage. | V1 components exist but production behavior is not proven. |
| `LIVE-V2-EDGE-021` | Persistence write failure before idempotency record is committed. | **Add** | Add fault-path and unknown-outcome/reconciliation coverage. | V1 components exist but production behavior is not proven. |
| `LIVE-V2-EDGE-022` | Audit sink failure before broker mutation. | **Add** | Add fault-path and unknown-outcome/reconciliation coverage. | V1 components exist but production behavior is not proven. |
| `LIVE-V2-EDGE-023` | Audit sink failure after broker mutation. | **Add** | Add fault-path and unknown-outcome/reconciliation coverage. | V1 components exist but production behavior is not proven. |
| `LIVE-V2-EDGE-024` | Partial network partition where audit write succeeds but broker send fails. | **Add** | Add fault-path and unknown-outcome/reconciliation coverage. | V1 components exist but production behavior is not proven. |
| `LIVE-V2-EDGE-025` | Partial network partition where broker send may have succeeded but audit post-write, receipt read, or reconciliation write fails. | **Add** | Add fault-path and unknown-outcome/reconciliation coverage. | V1 components exist but production behavior is not proven. |
| `LIVE-V2-EDGE-026` | Reconciliation mismatch between broker and internal state. | **Add** | Include this scenario in the final contract, validation, gate or integration test suite. | It exercises an accepted core behavior. |
| `LIVE-V2-EDGE-027` | Reconciliation authority state is missing, unsupported, stale, or in an unapproved transition. | **Add** | Include this scenario in the final contract, validation, gate or integration test suite. | It exercises an accepted core behavior. |
| `LIVE-V2-EDGE-028` | Runtime restart with in-flight unknown broker outcome. | **Add** | Add fault-path and unknown-outcome/reconciliation coverage. | V1 components exist but production behavior is not proven. |
| `LIVE-V2-EDGE-029` | Missing or unsupported broker provider. | **Add** | Include this scenario in the final contract, validation, gate or integration test suite. | It exercises an accepted core behavior. |
| `LIVE-V2-EDGE-030` | Symbol mapping absent, alias collision, or broker symbol disabled. | **Add** | Include this scenario in the final contract, validation, gate or integration test suite. | It exercises an accepted core behavior. |
| `LIVE-V2-EDGE-031` | Market closed, trade permission disabled, invalid account mode, insufficient margin, or margin level below policy. | **Add** | Include this scenario in the final contract, validation, gate or integration test suite. | It exercises an accepted core behavior. |
| `LIVE-V2-EDGE-032` | Volume below minimum, above maximum, not aligned to step, malformed, or exceeding symbol exposure limits. | **Add** | Include this scenario in the final contract, validation, gate or integration test suite. | It exercises an accepted core behavior. |
| `LIVE-V2-EDGE-033` | Invalid side, unsupported order type, invalid price, malformed ticket, invalid magic number, invalid timeframe, or invalid expiration. | **Add** | Include this scenario in the final contract, validation, gate or integration test suite. | It exercises an accepted core behavior. |
| `LIVE-V2-EDGE-034` | Stop loss or take profit on the wrong side of entry price, too close to market, or inside broker freeze distance. | **Add** | Include this scenario in the final contract, validation, gate or integration test suite. | It exercises an accepted core behavior. |
| `LIVE-V2-EDGE-035` | Price, volume, spread, slippage, commission, bid, ask, or account values missing, non-finite, zero, or negative where invalid. | **Add** | Include this scenario in the final contract, validation, gate or integration test suite. | It exercises an accepted core behavior. |
| `LIVE-V2-EDGE-036` | Partial fills, partial closes, pending-order expiry, pending-order trigger, or IOC-like remainder behavior. | **Add** | Include this scenario in the final contract, validation, gate or integration test suite. | It exercises an accepted core behavior. |
| `LIVE-V2-EDGE-037` | Concurrent submit and cancel for the same order intent. | **Add** | Add idempotency and coordination coverage using the approved conflict scope. | Critical duplicate/conflict behavior. |
| `LIVE-V2-EDGE-038` | Concurrent close and reduce exposure for the same position. | **Add** | Add idempotency and coordination coverage using the approved conflict scope. | Critical duplicate/conflict behavior. |
| `LIVE-V2-EDGE-039` | Concurrent pause and resume for the same strategy. | **Add** | Add idempotency and coordination coverage using the approved conflict scope. | Critical duplicate/conflict behavior. |
| `LIVE-V2-EDGE-040` | Shadow expected fill/PnL diverging from realized market behavior. | **Defer** | Retain as a future shadow/route-comparison acceptance scenario. | Shadow comparison is deferred. |
| `LIVE-V2-EDGE-041` | Shadow execution accidentally receives a live account or live broker adapter reference. | **Defer** | Retain as a future shadow/route-comparison acceptance scenario. | Shadow comparison is deferred. |
| `LIVE-V2-EDGE-042` | Notification adapter failure during live execution event. | **Add** | Add notification-failure incident coverage without changing broker outcome. | Live notifications are added through an injected sink. |
| `LIVE-V2-EDGE-043` | Compensation plan missing for an action class. | **Defer** | Add when the compensation catalog is approved. | Compensation is deferred. |
| `LIVE-V2-EDGE-044` | Cost budget exceeded before broker send. | **Modify** | Cover before-send block and after-send incident using externally owned budget limits. | Cost policy is external; enforcement evidence remains in Trading. |
| `LIVE-V2-EDGE-045` | Cost budget exceeded after broker send but before reconciliation completion. | **Modify** | Cover before-send block and after-send incident using externally owned budget limits. | Cost policy is external; enforcement evidence remains in Trading. |
| `LIVE-V2-EDGE-046` | Workflow timeout while approval, send, receipt, reconciliation, or compensation remains pending. | **Add** | Add fault-path and unknown-outcome/reconciliation coverage. | V1 components exist but production behavior is not proven. |
| `LIVE-V2-EDGE-047` | Clock skew between runtime, broker, approval service, and audit store. | **Add** | Add explicit UTC/broker-time/approval-time normalization and skew coverage. | Required for deterministic gating. |
| `LIVE-V2-EDGE-048` | System clock drift exceeds approved NTP or clock-health thresholds and could invalidate approval expiry or timestamp validation. | **Add** | Add explicit UTC/broker-time/approval-time normalization and skew coverage. | Required for deterministic gating. |
| `LIVE-V2-EDGE-049` | Timezone mismatch in approval expiry, broker timestamps, and reconciliation evidence. | **Add** | Add explicit UTC/broker-time/approval-time normalization and skew coverage. | Required for deterministic gating. |
| `LIVE-V2-EDGE-050` | Secret-reference resolution failure or accidental raw secret in config input. | **Add** | Add redaction and opaque-reference failure coverage in unified Trading. | Required security boundary. |
| `LIVE-V2-EDGE-051` | Live config YAML/JSON parse error containing raw secret-like text. | **Add** | Add redaction and opaque-reference failure coverage in unified Trading. | Required security boundary. |
| `LIVE-V2-EDGE-052` | Broker adapter contract version missing or incompatible. | **Add** | Add adapter-contract compatibility and fail-closed readiness coverage. | Missing from V1. |

### 6.5 Architecture prescriptions, proposed targets and pending decisions

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
| --- | --- | --- | --- | --- |
| `TRD-V2-ARCH-001` | Target folder structure under `tools/trading` with `bridge`, `simulator`, validation, registry, reconciliation, monitoring and compensation modules. | **Reject** | Keep the domain at `app/services/trading` and use capability folders; do not duplicate concrete broker bridges or simulator core. | The proposed location conflicts with the current package and duplicates Brokers/Simulator ownership. |
| `TRD-V2-ARCH-002` | Class design centered on `BaseExecutionBridge`, `MT5Bridge`, `PaperBroker`, and `TradingRegistry`. | **Reject** | Use the existing broker/simulator authority contracts and a small trading router; keep a stateful session class only where lifecycle is required. | The class hierarchy is an implementation prescription and duplicates concrete adapter domains. |
| `LIVE-V2-ARCH-001` | Separate `tools/live` package with config, session, gates, executor, reconciliation, monitoring and errors. | **Merge** | Place accepted live capabilities under `app/services/trading/live` and shared Trading modules. | The user selected one Trading domain. |
| `LIVE-V2-ARCH-002` | Class design centered on `LiveSession`, `LiveGateEngine`, `ReconciliationEngine`, and `TradeExecutor`. | **Modify** | Keep a stateful live session; implement gate/reconciliation/dispatch as focused functions or classes only when state/lifecycle requires them. | The behaviour is valid but the named engine/executor layers are not automatically justified. |
| `LIVE-V2-TARGET-001` | Gate evaluation latency p95 = 50 ms | **Open Decision** | Benchmark and approve against reference hardware before making it normative. | No benchmark profile exists. |
| `LIVE-V2-TARGET-002` | Gate evaluation latency p99 = 100 ms | **Open Decision** | Benchmark and approve against reference hardware before making it normative. | No benchmark profile exists. |
| `LIVE-V2-TARGET-003` | Readiness check latency p95 = 200 ms | **Open Decision** | Benchmark and approve against the final readiness checks and providers. | The target conflicts with the Trading p99 proposal and lacks evidence. |
| `LIVE-V2-TARGET-004` | Live order throughput = 100 requests/sec/node | **Open Decision** | Approve only after workload and broker-capacity evidence exists. | No expected workload or broker limit is documented. |
| `LIVE-V2-TARGET-005` | Reconciliation interval <= 30 seconds | **Open Decision** | Approve per broker, account criticality and staleness model. | The correct interval is authority/provider dependent. |
| `LIVE-V2-TARGET-006` | Broker adapter timeout default = 5 seconds | **Open Decision** | Resolve against Trading's proposed 10-second operation timeout and provider contracts. | The two V2 documents conflict. |
| `LIVE-V2-TARGET-007` | Broker rate-limit retries = 3 with exponential backoff and jitter | **Open Decision** | Approve per provider and only when no mutation is proven. | Generic retries can duplicate exposure. |
| `LIVE-V2-TARGET-008` | Live workflow timeout default = 60 seconds | **Open Decision** | Approve per workflow class after measurements. | Approval, send and reconciliation have different safe budgets. |
| `LIVE-V2-TARGET-009` | Live request queue depth limit = 10,000 | **Open Decision** | Choose bounded rejection/queue behavior from load evidence. | The value is unsubstantiated and may be unsafe. |
| `LIVE-V2-TARGET-010` | Shutdown audit flush timeout = 10 seconds | **Open Decision** | Approve from audit durability and shutdown objectives. | No durability objective is defined. |
| `LIVE-PEND-001` | Exact live execution schema | **Open Decision** | Approve one versioned unified Trading request/response/envelope contract. | Cross-domain callers depend on it. |
| `LIVE-PEND-002` | Idempotency fields, storage, duplicate behavior and retention | **Open Decision** | Approve per-action canonical material, store contract, retention and conflict behavior. | Safety-critical and cross-domain. |
| `LIVE-PEND-003` | Reconciliation persistence, mismatch states and authority transitions | **Open Decision** | Approve the authority state machine, broker-truth precedence and recovery transitions. | Production mutation depends on it. |
| `LIVE-PEND-004` | Approval quorum, action policy matrix, emergency classification and expiry | **Open Decision** | Governance must own and version the matrix/approval contract consumed by Trading. | Policy ownership is unresolved. |
| `LIVE-PEND-005` | Kill-switch hierarchy, re-enable and mass-action authority | **Open Decision** | Approve scope hierarchy, in-flight behavior, trigger/clear/re-enable rules and tests. | Safety-critical cross-domain decision. |
| `LIVE-PEND-006` | Broker adapter launch set and contract | **Open Decision** | Approve launch providers, capability/version/error/timeout/rate-limit contracts and security evidence. | Required before live mutation. |
| `LIVE-PEND-007` | Staleness, timeout, overload, concurrency, audit durability and recovery objectives | **Open Decision** | Approve concrete operational limits and coordination/restart contracts. | Current values are proposed or conflicting. |
| `LIVE-PEND-008` | Compensation action catalog and execution rules | **Open Decision** | Decide ownership and catalog; capability remains deferred until approved. | No safe generic compensation model exists. |

## 7. Workflow Reconciliation

| Final workflow ID | Workflow | Scope | V1 status | V2 proposal | Decision | Final boundary and outcome |
| --- | --- | --- | --- | --- | --- | --- |
| WF-TRD-001 | Validate and package a route-aware action | Internal | `V1-WF-TRADING-001` Working | `TRD-V2-FR-008`–`017`, `046`–`056` | Modify | Validated canonical request is either packaged, dispatched to simulator authority, or passed to the live gate; outcome uses one envelope. |
| WF-TRD-002 | Execute a simulation-route action | Cross-domain | Missing as actual mutation; V1 packaged only | `TRD-V2-OWN-007`, `010`; `FR-046`, `144`–`149` | Add | Canonical Trading request → Trading validation/routing → Simulator authority mutation → canonical receipt/result. |
| WF-TRD-003 | Start and enable a live session | Cross-domain | `V1-WF-TRADING-009`, `010` Partial | `LIVE-V2-FR-042`–`049`, `069`–`070` | Modify | Approved config/session handle + broker capability/security + startup reconciliation → live session `ready` or fail-closed status. |
| WF-TRD-004 | Gate and dispatch a live action | Cross-domain | `V1-WF-TRADING-002` Partial | `LIVE-V2-FR-001`–`041`; Trading action requirements | Modify | Canonical request + external verdicts/evidence → deterministic live gate → packaged-only or one approved broker dispatch → canonical outcome. |
| WF-TRD-005 | Resolve an unknown route outcome | Cross-domain | `V1-WF-TRADING-003` Partial | `TRD-V2-FR-153`–`158`; `LIVE-V2-FR-066`–`075` | Modify | Unknown receipt/timeout → authority snapshots → compare/persist incident → block retry until authority state resolves. |
| WF-TRD-006 | Read route facts and aggregate readiness | Cross-domain | `V1-WF-TRADING-004` Working | `TRD-V2-FR-060`–`083`; `LIVE-V2-FR-016`–`017` | Modify | Route/provider/symbol/account query → structured snapshot and freshness/capability checks → passed/failed readiness with evidence. |
| WF-TRD-007 | Activate/enforce kill switch and emergency controls | Cross-domain | `V1-WF-TRADING-005`, `008` Partial | `LIVE-V2-FR-054`–`065` | Modify | Approved policy/approval/emergency classification → durable switch state → block new actions and optionally run gated cancel/close → approved clear/re-enable. |
| WF-TRD-008 | Persist execution evidence and recover state | Cross-domain | `V1-WF-TRADING-006` Working at component level | `TRD-V2-FR-087`–`090`, `150`–`158`; live state requirements | Replace | Domain events/interfaces → external durable stores → reconstruct projections and unresolved attempts without custom domain-owned storage engines. |
| WF-TRD-009 | Perform safe live shutdown | Internal/Cross-domain | Part of `V1-WF-TRADING-009`; control helper exists | `LIVE-V2-FR-045`, `048`; shutdown NFR/tests | Modify | Stop admission → drain/mark in-flight work → flush audit/state → final reconciliation attempt → report unresolved work. |
| WF-TRD-010 | Emit monitoring, cost and incident evidence | Cross-domain | Monitoring/cost components disconnected | `TRD-V2-FR-159`–`166`; `LIVE-V2-FR-089`–`104` | Add | Runtime observations + external budget verdicts → pre-send block or post-send incident → structured events to observability/notifier. |
| WF-TRD-011 | Build execution and reconciliation report evidence | Cross-domain | Reporting test-only; `V1-CAP-TRADING-014` | `TRD-V2-FR-056`–`058`, `150`; `LIVE-V2-FR-041`, `104` | Modify | Receipts/readiness/reconciliation/incidents → immutable Trading report evidence → Analytics/consumers derive metrics. |
| WF-TRD-012 | Accept an upstream governed trading request | Cross-domain | `V1-WF-TRADING-007` Unverified raw signal translation | `TRD-V2-FR-094`–`105`; `LIVE-V2-FR-050` | Replace | Strategy/Conversation/Governance → canonical request with approval/risk references → Trading validates; no raw signal processor. |
| WF-TRD-013 | Shadow execution and comparison | Cross-domain | Shadow helpers test-only | Shadow requirements in both V2 documents | Defer | No-live-reference shadow workflow is excluded from the initial rebuild and later produces evidence for Analytics. |
| WF-TRD-014 | Generalized compensation workflow | Cross-domain | Only explicit emergency actions exist | Compensation requirements and `LIVE-PEND-008` | Defer | Use approved emergency actions initially; add catalog-driven compensation only after ownership and safety contracts are approved. |

### `WF-TRD-001` — Validate and package a route-aware action

**Scope:** `Internal`

**V1 behaviour:**

```text
Action parameters + explicit evidence
→ `validate_order_request`
→ build canonical request
→ package-only response when no route authority is selected
```

**V2 proposal:**

```text
One public verb and request shape
→ route chooses packaging, simulator mutation, or governed live mutation
```

**Final decision:**

```text
Validate once, build one canonical request, then route to package-only, Simulator authority, or the live gate. Never let route selection bypass validation.
```

**Reason:**

V1 packaging is proven and fail-closed. It must be extended rather than replaced so that simulation and live share the same contracts.

### `WF-TRD-002` — Execute a simulation-route action

**Scope:** `Cross-domain`

**V1 behaviour:**

```text
Validated `sim` actions normally return `packaged_only`; actual simulator state mutation is not proven in the audit.
```

**V2 proposal:**

```text
Trading contains simulator state, order send, pending/position/account monitoring and result containers.
```

**Final decision:**

```text
Canonical `sim` request
→ Trading validation and route dispatch
→ external Simulator authority mutates state
→ canonical receipt/result returns to Trading.
```

**Reason:**

The route workflow is required, but embedding the simulator engine in Trading duplicates a separate domain.

### `WF-TRD-003` — Start and enable a live session

**Scope:** `Cross-domain`

**V1 behaviour:**

```text
Config/session components
→ session state and operational mode
→ gate admission; production startup composition unverified.
```

**V2 proposal:**

```text
Validate config/secrets
→ broker readiness
→ startup reconciliation
→ enable recovery/mutation only after success.
```

**Final decision:**

```text
Approved runtime config + opaque session handle
→ adapter capability/security validation
→ startup broker snapshot and reconciliation
→ session becomes package-only or mutation-enabled.
```

**Reason:**

Safe startup is required; secret storage, broker login and policy creation remain external.

### `WF-TRD-004` — Gate and dispatch a live action

**Scope:** `Cross-domain`

**V1 behaviour:**

```text
Validated live action
→ sixteen gates
→ broker dispatch
→ normalize/finalize; Gate 7 may use risk passthrough.
```

**V2 proposal:**

```text
Deterministic live gate
→ package-only when disabled
→ adapter call only after mandatory gates.
```

**Final decision:**

```text
Canonical request + approval/risk/policy/readiness evidence
→ one fail-fast live gate
→ package-only or single authority dispatch
→ canonical receipt/incident.
```

**Reason:**

The V1 structure has strong value but is unsafe until real risk validation and final production composition are mandatory.

### `WF-TRD-005` — Resolve an unknown route outcome

**Scope:** `Cross-domain`

**V1 behaviour:**

```text
Broker timeout
→ unknown outcome
→ snapshot/reconciliation hook
→ retry guard; full service hook unconfirmed.
```

**V2 proposal:**

```text
Persist attempt
→ broker-truth reconciliation
→ authority-state transition
→ retry only after resolution.
```

**Final decision:**

```text
Classify unknown immediately, preserve attempt evidence, lock the conflict scope, reconcile against authority truth, persist the transition and release retry only after resolution.
```

**Reason:**

Blind retry is unacceptable; V1 already provides the right foundation.

### `WF-TRD-006` — Read route facts and aggregate readiness

**Scope:** `Cross-domain`

**V1 behaviour:**

```text
Facade method
→ dynamic broker read
→ neutral fallback/redaction.
```

**V2 proposal:**

```text
Many public account/symbol/quote/spread/permission/time/lot/margin check functions plus readiness aggregation.
```

**Final decision:**

```text
One route snapshot/readiness boundary returns structured facts, timestamps, freshness and failed checks; internal helpers perform individual validations.
```

**Reason:**

V1 reads are useful, but neutral defaults can overstate safety and V2's public surface is excessive.

### `WF-TRD-007` — Activate/enforce kill switch and emergency controls

**Scope:** `Cross-domain`

**V1 behaviour:**

```text
Trigger scope
→ reserve idempotency
→ journal activation; gate consumes separately supplied switch state. Emergency cancel/close aggregates child outcomes.
```

**V2 proposal:**

```text
Policy-matrix approval/emergency classification
→ trigger/disable/cancel/close
→ durable event
→ approved clear/re-enable.
```

**Final decision:**

```text
External policy classifies the action; Trading validates approval, writes authoritative switch state, immediately blocks governed actions, and routes mass actions through the normal live gate.
```

**Reason:**

The trigger-to-enforcement state bridge must be explicit, and emergency actions cannot self-classify.

### `WF-TRD-008` — Persist execution evidence and recover state

**Scope:** `Cross-domain`

**V1 behaviour:**

```text
Hash/reserve
→ custom JSONL journal/store
→ snapshot/seal/replay.
```

**V2 proposal:**

```text
Versioned send-attempt, receipt, reconciliation and incident payloads through injected repositories.
```

**Final decision:**

```text
Trading emits versioned events and uses minimal injected sinks/stores; Infrastructure provides transactions, encryption, retention and replay implementation.
```

**Reason:**

Forensic behavior is essential, but the domain should not prescribe a custom storage engine.

### `WF-TRD-009` — Perform safe live shutdown

**Scope:** `Internal/Cross-domain`

**V1 behaviour:**

```text
Drain callback
→ flush callback
→ optional reconciliation
→ journal result; reconciliation errors are logged.
```

**V2 proposal:**

```text
Stop admission
→ preserve state/audit
→ report unresolved work and safe recovery.
```

**Final decision:**

```text
Stop new mutations, mark in-flight work, drain within approved budget, flush audit/state, attempt reconciliation, and return a structured unresolved-work report.
```

**Reason:**

V1 behavior is useful but must fail visibly rather than silently logging unverified shutdown state.

### `WF-TRD-010` — Emit monitoring, cost and incident evidence

**Scope:** `Cross-domain`

**V1 behaviour:**

```text
Monitoring and cost components exist but no production wiring is confirmed.
```

**V2 proposal:**

```text
Health, ingestion, staleness, timeout, latency, notification, cost and incident monitoring.
```

**Final decision:**

```text
Runtime emits a small event set; external observability transports it. External budget verdicts are enforced before send, and post-send budget breaches become incidents.
```

**Reason:**

Operational evidence is required, but Trading should not duplicate observability or budget-policy systems.

### `WF-TRD-011` — Build execution and reconciliation report evidence

**Scope:** `Cross-domain`

**V1 behaviour:**

```text
Reporting helpers build execution/TCA events; callers are test/usage only.
```

**V2 proposal:**

```text
Build route-specific trading/live reports containing readiness, receipts, reconciliation, incidents and performance.
```

**Final decision:**

```text
Trading packages immutable execution evidence and unresolved actions; Analytics derives performance/TCA metrics.
```

**Reason:**

This preserves evidence ownership while avoiding duplicated analytics.

### `WF-TRD-012` — Accept an upstream governed trading request

**Scope:** `Cross-domain`

**V1 behaviour:**

```text
Raw strategy signal dictionary
→ enum/reference checks
→ request envelope
→ arbitrary gate callback.
```

**V2 proposal:**

```text
Signal processor and execution-intent assembly linked to proposal/risk decisions.
```

**Final decision:**

```text
Upstream owner produces the canonical Trading request with immutable references; Trading validates it and does not translate arbitrary strategy signal dictionaries.
```

**Reason:**

Signal generation/orchestration is outside Trading, and the V1 processor has no proven production caller.

### `WF-TRD-013` — Shadow execution and comparison

**Scope:** `Cross-domain`

**V1 behaviour:**

```text
Shadow intent/fill comparison helpers exist and are test-only.
```

**V2 proposal:**

```text
Production-like shadow feeds/execution/comparison without live mutation.
```

**Final decision:**

```text
Deferred. Later workflow must reject live account/adapter references and emit comparison evidence to Analytics.
```

**Reason:**

Useful validation, but not needed to establish the initial safe execution boundary.

### `WF-TRD-014` — Generalized compensation workflow

**Scope:** `Cross-domain`

**V1 behaviour:**

```text
Explicit cancel/close/flatten actions exist; no general compensation catalog is proven.
```

**V2 proposal:**

```text
Compensation plans, registry, order/position remediation and gated live execution.
```

**Final decision:**

```text
Deferred. Initial rebuild uses explicit approved emergency actions through the normal gate.
```

**Reason:**

A generic automatic compensation system is unsafe until ownership, action catalog, scope and terminal behavior are approved.

## 8. Recommended Minimal Capability Structure

This is a capability-level structure only. Exact files, signatures and private helpers belong in the next domain README and implementation blueprint.

```text
app/services/trading/
├── contracts/        # Canonical requests, receipts, envelopes, errors and registries
├── actions/          # Route-aware order, position and operational-control use cases
├── validation/       # Order validation, readiness and deterministic execution plans
├── routing/          # Route-authority selection, adapter capability checks and one dispatch boundary
├── live/             # Live config, session lifecycle, canonical gate and startup/shutdown
├── state/            # Idempotency, concurrency, projections and persistence event contracts
├── reconciliation/   # Authority snapshots, comparison, incidents and retry guard
├── monitoring/       # Health, staleness, timeout, latency, cost and notification incidents
└── reporting/        # Immutable execution/reconciliation evidence packages
```

| Module | Capability | Source | Main decision |
| --- | --- | --- | --- |
| `contracts` | Public contracts, envelope, error taxonomy and registries | Both | Modify / Merge |
| `actions` | Canonical order, position, pause/resume, kill-switch and emergency actions | Both | Modify |
| `validation` | Order validation, route readiness, precision/time rules and execution plans | Both | Modify / Add |
| `routing` | Simulator/broker authority selection, adapter capabilities, response classification and one mutation boundary | Both | Keep / Modify / Add |
| `live` | Live enablement, session lifecycle, startup reconciliation, gate sequence and safe shutdown | Both | Merge / Modify |
| `state` | Idempotency, concurrency, receipts/projections and event/store contracts | Both | Modify / Merge |
| `reconciliation` | Authority snapshots, mismatch comparison, incidents and retry guard | Both | Modify |
| `monitoring` | Health/staleness/timeout/latency/cost/notification evidence | Both | Modify / Add |
| `reporting` | Execution, readiness and reconciliation evidence packaging | Both | Modify |

## 9. Reuse and Migration Plan

| Priority | Existing V1 item | Migration action | Target capability | Validation required |
| ---: | --- | --- | --- | --- |
| 1 | `contracts.py` and root facade | Refactor | Contracts/envelope/registry | Approve canonical schemas; migrate analytics adapter compatibility tests. |
| 2 | `security/error_mapping.py`, `errors.py`, redaction boundary | Merge | Error/redaction taxonomy | One finite code registry; all callers and snapshots pass. |
| 3 | `actions/validation.py` | Reuse/Refactor | Order validation | Preserve Decimal/order-geometry tests; remove out-of-domain public validators. |
| 4 | `actions/orders.py`, `actions/positions.py` | Refactor | Canonical action API | Route parity tests for sim/live; exact signatures approved. |
| 5 | `execution/broker_dispatch.py` | Reuse | Authority dispatch boundary | Prove it remains the only production mutation call site. |
| 6 | `execution/response_classifier.py` | Refactor | Response/unknown-outcome classification | Malformed success, timeout and rate-limit contract tests. |
| 7 | `gates/live_pipeline.py` and gate helpers | Refactor | Canonical live gate | Remove risk passthrough; deterministic fail-fast order tests. |
| 8 | `runtime/session_manager.py`, config models/loader | Refactor | Live session lifecycle | Startup reconciliation, disabled-by-default and safe shutdown tests. |
| 9 | `state/idempotency.py`, `runtime/coordination.py` | Refactor | Idempotency/concurrency | Caller key, material-version, duplicate/conflict and race tests. |
| 10 | `state/trade_store.py`, execution state machine | Refactor | Receipts/state projections | Authority/version/restart tests against injected store. |
| 11 | `reconciliation/*` | Reuse/Refactor | Reconciliation/authority | Approve transition model; startup and unknown-outcome integration tests. |
| 12 | `actions/controls.py`, `actions/emergency.py`, kill-switch gates | Refactor | Operational controls | Policy/approval/in-flight/trigger-to-state tests. |
| 13 | `state/event_journal.py`, DLQ and state manager | Replace | Audit/persistence contracts | External durability and recovery tests before deleting custom stores. |
| 14 | `info/*` | Refactor | Route snapshots/readiness | Replace neutral defaults with structured unavailable/stale responses. |
| 15 | `monitoring/*` | Refactor | Monitoring/incidents | Connect minimal event set to live runtime; remove unused cache breadth. |
| 16 | `runtime/cost_control.py` | Refactor | Budget verdict enforcement | External owner/verdict contract and before/after-send tests. |
| 17 | `execution/reporting.py` | Refactor | Execution evidence reports | Confirm Analytics boundary and immutable evidence schema. |
| 18 | `execution/rate_limiter.py` | Remove | External rate verdict handling | No production callers; provider response handling migrated. |
| 19 | `runtime/signal_processor.py` | Remove | Canonical upstream request boundary | No production callers; upstream integration migrated. |
| 20 | `execution/shadow.py` and advanced compensation/OCO helpers | Defer | Deferred capabilities | No production dependency; retain source until deferred milestone decision. |
| 21 | Simulator route authority integration | New | Simulation route execution | Contract tests with Simulator; no simulator engine code inside Trading. |
| 22 | Broker adapter contract/security checks | New | Adapter readiness | Approved provider contract and security profile tests. |
| 23 | Notification outcome sink | New | Live notifications/incidents | Injected notifier and redaction/failure tests. |

## 10. Simplifications from V2

| V2 proposal | Problem | Simplified final direction |
| --- | --- | --- |
| Separate Trading and Live packages/registries | Duplicates action contracts, envelopes, gates and public governance. | One `app.services.trading` package with a focused `live/` capability and one registry. |
| V1 sixteen gates plus V2 eleven-gate sequence | Two overlapping gate models and duplicated checks. | One twelve-stage fail-fast sequence combining related readiness/staleness and adding session/concurrency. |
| Post-failure diagnostic-gate framework | Adds four metadata flags and alternate execution paths without a demonstrated need. | Run local contract/redaction validation before the mandatory pipeline; stop on first mandatory failure. |
| `BaseExecutionBridge`, `MT5Bridge`, `CTraderBridge`, `PaperBroker` inside Trading | Duplicates Brokers and Simulator implementations. | Trading consumes minimal authority adapter contracts and keeps one dispatch boundary. |
| Simulator state/monitor loops inside Trading | Duplicates the Simulator domain and couples backtest mechanics to live safety. | Trading dispatches `sim` requests to Simulator and receives canonical receipts. |
| Approval packet builder and approval services in Trading | Duplicates Governance and violates ownership. | Consume versioned approval references/verdicts only. |
| Dozens of public validation helpers | Creates a large unstable API around private rules. | One public order validator and readiness aggregator with private focused helpers. |
| Separate low-level order APIs (`trading_place_order`, `place_market_order`, etc.) | Duplicates canonical submit/modify/cancel actions. | Keep one public action verb family; route dispatch stays private. |
| Custom JSONL journal, stores, encryption and DLQ as domain architecture | Production use is unconfirmed and persistence concerns dominate the domain. | Define events/minimal interfaces; Infrastructure supplies durable implementations. |
| Internal token-bucket rate-limit policy | Conflicts with external policy ownership and provider-specific safety. | Consume verdicts; classify adapter responses and expose retry delay/safety. |
| Generic `Service`, `Manager`, `Engine`, `Executor` layers | Names do not prove state or lifecycle need. | Use functions for stateless behavior; retain stateful session/store/lock classes only. |
| Performance snapshot caches | No current readiness or audit workflow requires them. | Defer until measured need. |
| Generalized compensation registry and automatic execution | No approved catalog, owner or terminal-state model. | Use explicit gated emergency actions; defer generic compensation. |
| Shadow route and expected-versus-realized PnL in initial rebuild | Test-only V1 behavior and no launch-critical workflow. | Defer; later add no-live-reference mode with Analytics comparison. |
| Production block on every proposed performance target | Conflates safety approval with SLO approval. | Block on safety contracts; approve and test operational targets independently. |

## 11. Open Decisions

| Status | Decision required | Evidence available | Options | Affected capabilities |
| --- | --- | --- | --- | --- |
| Open | Exact initial route set and simulator authority boundary | V1 exposes `sim`, `paper`, `shadow`, `live`; V2 initially approves `sim`/`live` but asks Trading to own simulator state. | A: `sim`/`live` only and external Simulator authority; B: include paper route; C: internal simulator state | `CAP-TRD-002`, `006`, `020` |
| Open | Versioned approval and live action policy contracts and their owner | V1 has an internal policy matrix; both V2 documents state policy/governance ownership is external. | Governance-owned matrix; Risk-owned emergency matrix; Trading-owned only if system ADR approves | `CAP-TRD-009`, `010`, `015` |
| Open | Risk decision/verdict contract used by the live gate | V1 Gate 7 can be a passthrough; V2 requires real external risk context. | Signed RiskDecision token; immutable RiskVerdict DTO; synchronous Risk API reference | `CAP-TRD-009`, `010` |
| Open | Idempotency material by action, storage durability, retention and duplicate response | V1 has JSONL leases and generated keys; V2 requires caller-controlled keys and versioned material. | Per-action schemas and shared store; one generic schema; provider-specific scope | `CAP-TRD-011`, `013`, `016` |
| Open | Reconciliation authority-state transition model | V1 comparison/guard exists; V2 explicitly marks transitions pending. | Minimal pending/resolved/incident state machine; richer mismatch transition table | `CAP-TRD-014` |
| Open | Launch broker providers and adapter capability/security contracts | V1 supports router-based MT5/cTrader paths; V2 requires approved version, schema, transport and rate-limit behavior. | MT5 first; MT5+cTrader; other phased set | `CAP-TRD-007`, `012` |
| Open | Kill-switch scope hierarchy, in-flight supersession, emergency classification and re-enable authority | V1 supports global/strategy/symbol triggers but trigger-to-state propagation is unconfirmed. | Strict global>strategy>symbol hierarchy; policy-matrix-specific scopes | `CAP-TRD-015` |
| Open | Concurrency scopes, lock timeout and stale-lock recovery | V1 uses per-account/symbol coordination; V2 proposes broader scopes and optimistic versions. | Per-action lock keys; optimistic versions for modify; hybrid | `CAP-TRD-011` |
| Open | Operational limits and timeout/freshness defaults | Trading proposes 10s broker operations and 5s checks; Live proposes 5s adapter timeout and unapproved latency/queue targets. | Provider-specific table; conservative global defaults with overrides | `CAP-TRD-007`, `009`, `011`, `017` |
| Open | Budget owner and verdict contract | V1 owns a disconnected CostController; V2 conflicts between consuming and enforcing budgets. | External budget verdict enforced by Trading; Trading-owned counters; API-gateway-only | `CAP-TRD-018` |
| Open | Persistence durability and recovery objectives | V1 has custom JSONL/journal/DLQ; V2 asks for interfaces but not durability semantics. | Infrastructure event store; database transaction/outbox; append-only log service | `CAP-TRD-013`, `014`, `016` |
| Open | Exact public Python API and agent-callable tool list | V1 root exports 39 names and registry has one metadata-only draft tool; V2 proposes many public helpers. | Small action/readiness/report API plus draft-only agent tools; broader governed tools | `CAP-TRD-001`, `025` |
| Open | Whether generalized compensation is owned by Trading and required for initial live launch | V2 has extensive compensation requirements but also marks catalog decisions pending; V1 has explicit emergency actions only. | Defer; explicit actions only; governed catalog before launch | `CAP-TRD-021` |
| Open | Whether shadow execution is a route, a mode, or an Analytics/Validation workflow | V1 has a `shadow` route/helper; V2 says exact routes beyond sim/live are not approved and shadow is optional. | Deferred mode under Trading; external validation workflow; future route | `CAP-TRD-020` |

### Cross-domain escalation required

The following decisions affect more than Trading and must be added to the top-level system document during the cross-domain alignment review, with ADRs where required: route/Simulator authority, approval/action-policy ownership, risk verdict contract, idempotency persistence, reconciliation authority transitions, broker adapter/security contracts, kill-switch authority, operational limits, budget ownership, persistence durability, compensation ownership and shadow-mode ownership. This reconciliation identifies the escalation but does not modify the top-level system document because it was not an input to this step.

The deferred shadow and generalized compensation capabilities also change cross-domain workflows. They must be reflected in the top-level Deferred Capabilities section during pipeline step 05.

## 12. Inputs for the Final Domain README

### Approved capabilities

* One canonical Trading public facade and a separate restricted agent-tool registry.
* Canonical route/request/receipt/result/error/audit contracts.
* Decimal-safe order and operation validation.
* Route-aware order, position and operational-control actions.
* Simulation route dispatch to an external Simulator authority.
* Structured route snapshots and aggregate readiness.
* Unified live configuration/session lifecycle within Trading.
* One deterministic fail-fast live gate with real external risk validation.
* External approval, risk, action-policy, authorization and kill-switch verdict consumption.
* Caller-controlled idempotency and approved concurrency coordination.
* One broker/simulator authority dispatch boundary with adapter capability/security validation.
* Canonical receipts, lifecycle transitions and authority-state projections.
* Reconciliation, unknown-outcome handling and retry guard.
* Scoped kill switches and gated emergency cancel/close behavior.
* Audit/persistence event contracts with externally implemented durability.
* Minimal health, staleness, timeout, latency, cost, notification and incident events.
* Execution and reconciliation evidence reports for Analytics and other consumers.
* Non-mutating governed agent drafts.

### Approved workflows

* `WF-TRD-001` — Validate and package a route-aware action.
* `WF-TRD-002` — Execute a simulation-route action.
* `WF-TRD-003` — Start and enable a live session.
* `WF-TRD-004` — Gate and dispatch a live action.
* `WF-TRD-005` — Resolve an unknown route outcome.
* `WF-TRD-006` — Read route facts and aggregate readiness.
* `WF-TRD-007` — Activate/enforce kill switch and emergency controls.
* `WF-TRD-008` — Persist execution evidence and recover state.
* `WF-TRD-009` — Perform safe live shutdown.
* `WF-TRD-010` — Emit monitoring, cost and incident evidence.
* `WF-TRD-011` — Build execution and reconciliation report evidence.
* `WF-TRD-012` — Accept an upstream governed trading request.

### V1 behaviours to preserve

* Decimal-based order normalization and stop/volume/margin checks from `actions/validation.py`.
* Fail-closed packaged-only behavior when mutation authority is absent.
* The single broker mutation call boundary in `execution/broker_dispatch.py`.
* Broker response normalization and explicit unknown-outcome classification.
* Pre-mutation audit blocking, idempotency, optimistic versions and concurrency coordination.
* Reconciliation comparison and retry blocking after unknown outcomes.
* Netting/hedging position addressing and partial-close behavior.
* Emergency partial-completion reporting.
* Session admission, reconnect/reconciliation lock and safe shutdown foundations.
* Recursive redaction and JSON-safe boundary contracts.

### V1 behaviours to modify

* Replace risk passthrough with mandatory real risk-verdict validation.
* Unify duplicate contracts, `OrderIntent` models, exception hierarchies and error maps.
* Rename and consolidate action APIs into canonical route-aware verbs.
* Replace silent neutral read fallbacks with structured unavailable/stale results.
* Change generated idempotency behavior to caller-controlled keys for governed mutation.
* Simplify the sixteen V1 gates into one approved fail-fast sequence.
* Connect cost, monitoring, notification, startup reconciliation and kill-switch state to the actual live runtime.
* Move persistence implementation details behind minimal injected sinks/stores.
* Remove internal strategy promotion ownership while retaining route compatibility validation.
* Separate Trading execution evidence from Analytics-derived performance metrics.

### V1 behaviours to remove

* Local token-bucket rate-limit policy, after callers migrate to external verdicts and adapter response classification.
* Raw dictionary strategy `SignalProcessor`, after upstream callers produce canonical Trading requests.
* Duplicate error hierarchy/mapper and duplicate contract bases, after all imports and snapshots migrate.
* Internal promotion transition ownership, after the external lifecycle/governance contract is connected.
* Legacy or unapproved advanced OCO/multi-leg/non-atomic helpers, only after production caller search confirms no dependency.

### V2 behaviours to add

* Actual `sim` route dispatch to Simulator authority and canonical simulated receipts.
* One complete standard envelope with finite status/error/warning/side-effect/retry taxonomy.
* Caller-controlled, versioned idempotency material and conflict detection.
* Aggregate structured readiness with adapter API/schema/security compatibility.
* Startup reconciliation and explicit package-only/mutation-enabled live modes.
* Malformed-success and provider rate-limit response safety classification.
* Pre/post audit evidence and connected authority-state recovery.
* Connected notification and cost-budget incident behavior.
* Public contract matrices and mechanically checked registry/signature/envelope tests.

### V2 proposals to reject or defer

* Reject a separate Live domain/package and separate live registry; merge into Trading.
* Reject concrete MT5/cTrader/paper/simulator implementations inside Trading.
* Reject simulator engine state and monitor loops inside Trading.
* Reject Trading-owned approval creation/voting/override services.
* Reject lazy package attribute resolution and duplicate low-level public order APIs.
* Reject post-failure diagnostic-gate framework for the initial rebuild.
* Reject generic service/manager/engine/executor layers unless state or lifecycle proves the need.
* Defer shadow execution/comparison, performance snapshot caches and generalized compensation.
* Reject production gating on unapproved performance SLOs; retain safety-critical launch gates.

### Required open decisions before README completion

* Exact initial route set and simulator authority boundary.
* Versioned approval and live action policy contracts and their owner.
* Risk decision/verdict contract used by the live gate.
* Idempotency material by action, storage durability, retention and duplicate response.
* Reconciliation authority-state transition model.
* Launch broker providers and adapter capability/security contracts.
* Kill-switch scope hierarchy, in-flight supersession, emergency classification and re-enable authority.
* Concurrency scopes, lock timeout and stale-lock recovery.
* Operational limits and timeout/freshness defaults.
* Budget owner and verdict contract.
* Persistence durability and recovery objectives.
* Exact public Python API and agent-callable tool list.
* Whether generalized compensation is owned by Trading and required for initial live launch.
* Whether shadow execution is a route, a mode, or an Analytics/Validation workflow.

The README may document these as explicit unresolved contracts, but it must not imply that production live mutation is approved until the safety-critical items are resolved.

## 13. Final Reconciliation Checklist

* [x] Every V1 capability received a disposition: **32/32**.
* [x] Every identified V2 item received a disposition: **649/649**.
* [x] Every V1 workflow was reconciled: **10/10** mapped into final workflows.
* [x] All proposed V2 workflow families were normalized and reconciled, including route actions, simulation, live startup/gating, reconciliation, kill switches, persistence/recovery, monitoring/cost, reporting, shadow and compensation.
* [x] Confirmed working V1 behavior was not discarded without a destination and reason.
* [x] Questionable or duplicated V1 behavior was not preserved automatically.
* [x] V2 implementation complexity was not accepted automatically.
* [x] The direction follows the package → capability module → focused file → public behavior structure.
* [x] Capabilities that may belong to Simulator, Brokers, Governance, Risk, Analytics, Infrastructure, Observability, Secrets, API/UI or Conversation are explicitly bounded and flagged for step 05.
* [x] Unresolved conflicts are listed under Open Decisions.
* [x] Cross-domain open decisions and deferrals are identified for top-level escalation; the top-level document was not modified in this step.
* [x] No code was inspected or changed during this reconciliation.
* [x] The V1 audit and both V2 source documents were not modified.
* [x] The approved capability, workflow, migration and open-decision inputs are sufficient to draft the final domain README without inventing missing policy decisions.

---

## Evidence Not Available

* Confirmed production composition and callers for the V1 live pipeline, monitoring, cost, reconciliation, signal and persistence components.
* Executed V1 unit/integration/usage test results and coverage.
* Approved cross-domain contracts for Risk decisions, Governance approvals/action policy, Simulator authority, broker adapters, persistence, secrets, observability and budgets.
* Owner-approved performance, timeout, freshness, queue, concurrency, retention and recovery limits.
* An approved broker communication security profile and launch-provider list.

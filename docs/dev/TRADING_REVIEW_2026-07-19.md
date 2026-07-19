# Trading Domain — Post-Build Completion Review

> **Reviewer role:** read-only verification agent. No file, code, status, or dependency was created, modified, or deleted during this review.
> **Domain:** `app/services/trading` · **Tests:** `tests/trading` · **Domain README:** `app/services/trading/README.md`
> **Date:** 2026-07-19

---

## 1. Result

**NOT READY**

---

## 2. Executive reason

The implementation is materially complete and of high mechanical quality: 41 source
files, 230 functions, every function carrying a Google-style docstring, full explicit
typing, and at least one `app.utils.logger` call; `ruff format --check`, `mypy --strict`,
and all 160 domain tests pass at 84.06% coverage. Structure, module dependency order,
`__init__` export surfaces, and import side-effect freedom all match README Section 2.

`READY` is nevertheless not attainable, because completion is claimed in four places
where evidence contradicts it:

1. **Redaction is asserted but never performed.** Eleven returned envelopes, audit
   metadata blocks, and persisted events carry `redaction_applied: True` while
   `redact_trading_payload` is invoked in only two modules. Full `ExecutionReceipt`,
   `OrderIntent`, gate evidence, and stored report evidence are returned and persisted
   unredacted under a true-redaction claim. This is a false safety claim under
   `NFR-TRD-003`, `NFR-TRD-006`, and `FR-TRD-009`.
2. **Four `Completed`, `Required` configuration bounds do not exist in code.**
   `TRADING_CONTRACT_VERSION`, `IDEMPOTENCY_RETENTION_SECONDS`,
   `CONCURRENCY_LOCK_TIMEOUT_SECONDS`, and `MAX_STALENESS_SECONDS` appear nowhere in
   `app/services/trading` or `tests/trading`. `MAX_STALENESS_SECONDS` is a fail-closed
   freshness bound; without it, evidence freshness is delegated entirely to a
   caller-supplied `expires_at`.
3. **`docs/PROJECT.md` — a higher authority than the domain README — still records
   every Trading-owned contract, the Trading persisted-state row, and both
   Trading-owned shared settings as `Missing`.** The domain README marks the same
   items `Completed`. One of the two documents is wrong; the higher-authority one was
   not reconciled.
4. **`WF-TRD-013`'s mapped integration test file does not exist**, and no test drives
   any action verb end to end on a `paper`/`live` route through the positive
   gate → dispatch → receipt path. Every integration test additionally imports its
   fixtures — including private `_request`, `_session`, `_config`, `_evidence` — from
   unit test modules, so integration coverage re-uses unit-level doubles rather than
   exercising genuine end-to-end behaviour.

Coverage passing at 84% does not offset these; coverage alone does not prove
requirement compliance, and the four items above are exactly the kind of claim the
Definition of Done requires to be proven rather than asserted.

---

## 3. Blocking and high findings

### `TRD-B01` — BLOCKING — False redaction claim on returned, logged, and persisted payloads

* **Rule violated:** `FR-TRD-009`; `NFR-TRD-003` (Security); `NFR-TRD-006`
  (Observability — "emit redacted pre/post evidence"); AGENTS.md §4 Security; review
  §7 "No secret leakage in logs, errors, events, reports, audit records, or tests" and
  "Treat any … false success claim as a blocking finding".
* **Exact file and line:**
  * `app/services/trading/actions/orders.py:85` and `:222` — envelope `audit_metadata`
  * `app/services/trading/actions/orders.py:124` — `TradingEvent.payload` carries
    `receipt.model_dump(mode="json")` unredacted into a model whose
    `redaction_applied` is `Literal[True]` (`app/services/trading/state/events.py:49`)
  * `app/services/trading/live/gates.py:158`, `:239` — gate envelope and pre-audit
    record; `:252` embeds the full `intent.model_dump(mode="json")`
  * `app/services/trading/live/session.py:288`
  * `app/services/trading/actions/controls.py:123`
  * `app/services/trading/actions/emergency.py:87`
  * `app/services/trading/actions/rebalance.py:279`
  * `app/services/trading/actions/runtime.py:321`
  * `app/services/trading/reporting/evidence.py:87` — with unredacted `evidence` at `:64`
  * `app/services/trading/contracts/registry.py:205`
  * `app/services/trading/contracts/models.py:365` — `redaction_applied: Literal[True]`
  * Only actual redaction call sites: `app/services/trading/monitoring/events.py:121`,
    `app/services/trading/contracts/errors.py:140` and `:215`
* **Current behavior:** `redaction_applied` is a hard-coded literal `True`. No
  redaction pass runs on `data`, `payload`, or `evidence` before the value is returned
  to a caller, appended to the event store, or written as pre-audit evidence.
* **Required behavior:** Every payload that carries `redaction_applied: True` must have
  been produced by `redact_trading_payload(...)` immediately before emission,
  persistence, or return. The flag must be evidence of a completed action, not a
  constant.
* **Why it matters:** Downstream consumers (UI/API, Data audit storage, Analytics) and
  the adapter-capability check at `routing/capabilities.py:126` all trust this flag.
  A `True` value that no code produced means any secret that reaches an intent,
  receipt, trace context, or store payload is exported with an explicit assurance that
  it was scrubbed. This is precisely the leakage class `NFR-TRD-003` exists to prevent.
* **Verification after correction:** A unit test per emitting module that plants a
  sensitive key (e.g. `api_secret`, `password`, `token`) in the source material and
  asserts the value is absent from the returned envelope, the appended `TradingEvent`,
  and the pre-audit record while `redaction_applied` remains `True`; plus a negative
  test proving the flag cannot be set without the redaction call.

### `TRD-B02` — BLOCKING — Higher-authority `docs/PROJECT.md` contradicts every Trading `Completed` claim

* **Rule violated:** Authority order (Owner → `AGENTS.md` → `docs/PROJECT.md` →
  domain README); AGENTS.md §6 Update Rules; review §6 "Reconcile every owned and
  consumed contract with `docs/PROJECT.md`", "Persisted-state ownership … match the
  top-level registry"; review §10 "A false or unsupported `Completed` status is a
  blocking documentation-integrity finding".
* **Exact file and line:**
  * `docs/PROJECT.md:765` — `OrderIntent v1` → `Missing` (README:49 → `Completed`)
  * `docs/PROJECT.md:766` — `TradeRecord` / `ExecutionReceipt v1` → `Missing`
    (README:50–51 → `Completed`)
  * `docs/PROJECT.md:767` — `OperationalEvent v1` → `Missing` (README:53 → `Completed`)
  * `docs/PROJECT.md:785` — `PortfolioRebalanceExecutionRequest v1` → `Missing`
    (README:52 → `Completed`)
  * `docs/PROJECT.md:841` — Trading orders/fills/execution/idempotency/`TradeRecord`
    persisted state → `Missing` (README:97–99 → `Completed`)
  * `docs/PROJECT.md:869` — `EXECUTION_ROUTE` → `Missing` (README:905 → `Completed`)
  * `docs/PROJECT.md:870` — `ALLOW_LIVE_MUTATIONS` → `Missing` (README:906 → `Completed`)
  * `docs/PROJECT.md:936` — MT5 external integration: "Trading mutation workflow
    remains pending"
* **Current behavior:** The domain README declares the Trading contract family,
  persisted state, and owned shared settings `Completed`; the authoritative top-level
  registry still declares each of them `Missing`.
* **Required behavior:** Because Trading owns these registry rows and the code exists,
  `docs/PROJECT.md` rows 765, 766, 767, 785, 841, 869, 870 must be updated to
  `Completed` in the same change that completed the domain, and row 936's Trading
  clause must be corrected. `docs/PROJECT.md` §5 line 830 already mandates this:
  "A version bump must update the contract table above, the owner's README, and every
  consumer README in the same change."
* **Why it matters:** Consumers (Analytics, Portfolio, UI/API, Simulation) read the
  top-level registry to decide whether a contract may be depended upon. Leaving it
  `Missing` blocks legitimate downstream work and means the repository has two
  contradictory truths about production-critical execution contracts.
* **Verification after correction:** Re-grep `docs/PROJECT.md` for each row and confirm
  status parity with `app/services/trading/README.md` §1; confirm `docs/CHANGELOG.md`
  records the registry reconciliation.

### `TRD-B03` — BLOCKING — `WF-TRD-013` mapped integration test does not exist; checklist claim unsupported

* **Rule violated:** README §3 `WF-TRD-013` (status `Completed`); README §7 checklist
  "[X] Every collaborative workflow has an integration test"; `NFR-TRD-007`; review §3
  "A workflow is compliant only when its complete integration test passes".
* **Exact file and line:**
  * `app/services/trading/README.md:494` names
    `tests/trading/integration/test_portfolio_rebalance.py::test_rebalance_cannot_bypass_risk_or_open_to_match_weight()`
    — this file does not exist (verified: 142 README test references resolved, 1 missing).
  * `app/services/trading/README.md:994` — checklist cites a different file,
    `tests/trading/integration/test_rebalance.py:20`.
  * `tests/trading/integration/test_rebalance.py:20` — the only rebalance integration
    test is `test_authorized_rebalance_uses_existing_order_path()`, a happy-path
    assertion (`outcome.data["outcomes"][0]["status"] == "sent"`).
* **Current behavior:** `WF-TRD-013` is marked `Completed` against a nonexistent test.
  The negative behaviour the workflow specification centres on — "cannot bypass Risk"
  and "no order opens solely to match a target weight" — has no integration evidence;
  only a unit test (`tests/trading/unit/actions/test_rebalance.py:174`) covers the
  weight-matching half.
* **Required behavior:** Either create
  `tests/trading/integration/test_portfolio_rebalance.py` with the named function
  covering both negative branches, or update README:494 to the real path *and* extend
  the existing integration test to assert Risk-bypass rejection and reduce-only
  enforcement. The README-first change process (§8) makes the first option correct.
* **Why it matters:** `WF-TRD-013` is the path by which Portfolio can cause live
  broker mutations. Its stated safety property is unproven at the workflow level, and
  a `Completed` status is being carried on a test reference that resolves to nothing.
* **Verification after correction:** Re-run the README reference resolver — all 142+
  `tests/trading/...::test_...` references must resolve to an existing file and
  function; the new test must fail if the Risk-bypass guard or reduce-only guard is
  removed.

### `TRD-B04` — BLOCKING — Four `Completed`, `Required` configuration bounds are unimplemented

* **Rule violated:** README §4.1/§4.2/§4.3 Configuration and Limits Manifests (all
  rows `Required = Yes`, status `Completed`); review §5 "Required values cannot be
  omitted", "'No shared default' values require explicit profile configuration",
  "Bounds are validated before allocation, mutation, network access, or expensive
  work", "Exceeded limits produce the documented deterministic failure";
  `NFR-TRD-001` (Safety).
* **Exact file and line:**
  * `README.md:521` `TRADING_CONTRACT_VERSION` — 0 occurrences in
    `app/services/trading/**/*.py` or `tests/trading/**/*.py`. Also referenced by
    README:874 ("Report schema version follows `TRADING_CONTRACT_VERSION`") — the
    report instead hard-codes `"contract_version": "v1"` at
    `app/services/trading/reporting/evidence.py:71`.
  * `README.md:587` `IDEMPOTENCY_RETENTION_SECONDS` — 0 occurrences.
    `app/services/trading/state/idempotency.py:140` passes `request.valid_until` as the
    reservation expiry instead of a configured positive retention window.
  * `README.md:588` `CONCURRENCY_LOCK_TIMEOUT_SECONDS` — 0 occurrences. No stale-lock
    recovery policy and no timeout-driven `TRADING_CONCURRENCY_CONFLICT` path exists;
    the code raises that error only from reservation-status branches
    (`live/gates.py:213`, `actions/orders.py:227`).
  * `README.md:634` `MAX_STALENESS_SECONDS` — 0 occurrences.
    `app/services/trading/validation/readiness.py:129`, `:154`, `:184` derive staleness
    solely from `expires_at <= request.system_time` on caller-supplied evidence.
* **Current behavior:** Freshness, retention, and concurrency bounds are either absent
  or delegated to values the caller supplies inside the evidence being validated.
  Omitting the settings does not fail configuration; it silently succeeds.
* **Required behavior:** Each setting must exist as a typed, required, positive value
  with no shared default, be validated at configuration load, be enforced at the
  documented call site, and produce the documented deterministic failure when omitted
  or exceeded — or the README rows must be corrected to describe what was actually
  built and their status downgraded.
* **Why it matters:** `MAX_STALENESS_SECONDS` is the fail-closed freshness bound. As
  built, a caller that supplies a `RouteSnapshot` with a distant `expires_at` passes
  readiness on arbitrarily old market and account evidence, and the system will size
  and dispatch against it. That is a fail-open path in a mutation-authorising gate.
* **Verification after correction:** A unit test per setting proving (a) omission
  raises the documented configuration failure, (b) a value at the bound passes and one
  past the bound fails closed with the documented code, and (c) the bound is checked
  before any dispatch call.

### `TRD-H01` — HIGH — No positive end-to-end `paper`/`live` dispatch test; `WF-TRD-004` half-covered

* **Rule violated:** README §3 `WF-TRD-004` output boundary ("One dispatch through
  Brokers' `BrokerAdapter` mutation operations, or an audited fail-closed result");
  `NFR-TRD-007`; review §3.
* **Exact file and line:** `tests/trading/integration/test_live_dispatch.py:19–25` —
  the whole test is `pytest.raises(TradingError, match="GATE_BLOCKED")`.
  `tests/trading/unit/actions/test_orders.py:26–28` — the only `live`-route action test
  asserts `SERVICE_UNAVAILABLE`. `tests/trading/integration/test_sim_dispatch.py:19` is
  the sole end-to-end action test and uses `route="sim"`.
* **Current behavior:** No test anywhere drives `submit_order` (or any verb) on
  `paper`/`live` through `evaluate_live_gate` → `dispatch_order_intent` → receipt →
  `_record_receipt`. The `else` branch of `evaluate_live_gate` (lines 244–254) and the
  `route in {"paper","live"}` branch of `_execute_request` (`actions/orders.py:203–209`)
  are exercised only in isolation, never joined.
* **Required behavior:** One integration test constructing a real `LiveSession` with
  `ALLOW_LIVE_MUTATIONS=True`, a valid `RiskDecisionPackage`, `ActionPolicyVerdict`,
  inactive kill-switch hierarchy, and a fake `BrokerAdapter`, asserting exactly one
  adapter mutation call, a canonical receipt, and one appended `TradingEvent`.
* **Why it matters:** `SYS-WF-002` is the domain's reason to exist. Its positive path
  is currently unproven end to end while being marked `Completed`.
* **Verification after correction:** The new test must fail if any mandatory gate is
  bypassed or if the adapter is called zero or more than one time.

### `TRD-H02` — HIGH — Integration tests import fixtures and private helpers from unit tests

* **Rule violated:** Review §3 "The integration test exercises the genuine end-to-end
  workflow rather than mocking away the behavior under review"; README §7 Required test
  levels.
* **Exact file and line:** 21 `from tests…` imports across 14 of 14 integration files.
  Representative:
  * `tests/trading/integration/test_live_dispatch.py:8–9` — imports private `_request`,
    `_session`, `_config`, `_evidence`
  * `tests/trading/integration/test_kill_switch.py:10–15` — imports `switch`,
    `dependencies`, `policy`, `request`, `emergency_dependencies`, `unknown_dispatch`
  * `tests/trading/integration/test_rebalance.py:7–10` — imports `rebalance_dependencies`,
    `rebalance_request`
* **Current behavior:** Integration tests are thin wrappers over unit-level fakes and
  private constructors. A change to a unit test helper silently changes what the
  integration suite proves.
* **Required behavior:** Integration tests should compose their own subject under test
  from public APIs, or share fixtures through a `tests/trading/conftest.py` designed as
  a shared public fixture surface — never through cross-imports of private unit-test
  symbols.
* **Why it matters:** It makes the integration layer non-independent, so a defect
  masked by a unit double is masked identically at the integration level.
* **Verification after correction:** No `from tests.trading.unit…` import remains in
  `tests/trading/integration`; the suite still passes.

### `TRD-H03` — HIGH — Bulk emergency verbs are untested on `paper`/`live` and appear structurally blocked there

* **Rule violated:** `FR-TRD-023`, `FR-TRD-050`; README §3 `WF-TRD-007` ("Trigger,
  clear, cancel-all, and close-all pass the same policy, approval, idempotency, audit,
  and live gates as other mutations"); `NFR-TRD-007`.
* **Exact file and line:**
  * `tests/trading/unit/actions/test_emergency.py:52` — `route="sim"`, the only route
    exercised for both bulk verbs; `tests/trading/integration/test_kill_switch.py:38`
    likewise.
  * `app/services/trading/actions/emergency.py:142–156` and `:224–235` — each child
    request inherits the parent's `risk_decision_id`, `approval_token_ref`, and
    `action_policy_verdict_id` while its `quantity` is taken from the broker snapshot.
  * `app/services/trading/live/gates.py:96` — `_validate_risk` requires
    `decision.approved_size == request.quantity` for every action.
* **Current behavior:** On `paper`/`live`, each bulk child must satisfy a Risk decision
  whose `approved_size` equals that child's snapshot quantity. A single parent decision
  cannot satisfy more than one child, so bulk cancel/close fails closed for every child
  after the first coincidental match. No test covers this because no bulk test uses a
  non-`sim` route.
* **Required behavior:** Confirm and document the intended Risk-binding semantics for
  bulk children (per-child decisions supplied by the composition root, or an explicit
  exemption of `cancel_order` from the size-equality check), then implement and test it
  on a `paper` route.
* **Why it matters:** Mass cancellation and closure are the emergency controls invoked
  when something has already gone wrong. They are marked `Completed` while being
  unverified on the only routes where they carry real consequences.
* **Verification after correction:** A `paper`-route integration test where
  `cancel_all_orders` produces one successful child per eligible order and explicit
  skip/error rows for the rest, with the child count bounded by `max_children`.

### `TRD-H04` — HIGH — Child requests are built with `model_copy(update=…)`, skipping `TradingRequest` validation

* **Rule violated:** `FR-TRD-002` ("validate one immutable canonical request");
  review §4 "Validation occurs at the required boundary".
* **Exact file and line:** `app/services/trading/actions/emergency.py:142` and `:224`.
* **Current behavior:** Pydantic's `model_copy(update=…)` does not re-run field
  validators or `model_validator(mode="after")`. Child requests mutate `action`,
  `symbol`, `side`, `quantity`, `price`, `order_id` / `position_id`, target broker IDs,
  `expected_version`, and `idempotency_key` without any model-level revalidation of the
  resulting combination.
* **Required behavior:** Construct children with `TradingRequest.model_validate(
  {**parent.model_dump(), **updates})` (or an explicit validated factory) so every
  canonical field rule in README §4.1 is re-enforced on the derived request.
* **Why it matters:** `TradingRequest` is the domain's single validation boundary for
  order shape, Decimal safety, and target-identity nullability. Bypassing it for the
  exact requests that will be dispatched in an emergency defeats that boundary; the
  downstream `validate_order_request` covers order fields but not the model's own
  cross-field invariants.
* **Verification after correction:** A unit test proving a child built from a parent
  with an incompatible field combination raises `TradingError` before any dispatch.

### `TRD-H05` — HIGH — Unregistered schema identifier emitted by `build_trading_report`

* **Rule violated:** README §1 Shared contracts; `docs/PROJECT.md:805` (registered
  contracts carry `contract_version` separately from a namespaced `schema_id`);
  review §6 "Name, owner, version, producer, consumer, and purpose match".
* **Exact file and line:** `app/services/trading/reporting/evidence.py:72` —
  `"schema_id": "trading.execution_evidence_report.v1"`.
* **Current behavior:** A versioned schema identifier is emitted across the boundary to
  Analytics, Portfolio, and UI/API. It appears in neither the domain README's owned
  contract table nor `docs/PROJECT.md` §5.
* **Required behavior:** Either register the report evidence contract in both documents
  (owner, version, producer, consumers, purpose, failure behaviour) or stop emitting a
  `schema_id` and return the evidence inside the already-registered
  `StandardTradingEnvelope` shape without minting a new identifier.
* **Why it matters:** Unregistered schema identifiers become de facto contracts that
  consumers pin to, outside the change process that governs versioning.
* **Verification after correction:** The identifier resolves to a registry row, or is
  absent from the returned payload; a contract test asserts the registered shape.

---

## 4. Medium and low findings

### `TRD-M01` — MEDIUM — `TradingStateStore` exposes six operations; README declares five, and one has no requirement row

* **Rule:** README §4.2 Files table key export "`TradingStateStore` and its five public
  operations"; review §4 "Every public symbol has exactly one functional requirement,
  usage example, and unit test"; README §7 checklist line 993 marked `[X]`.
* **Location:** `app/services/trading/state/stores.py:93` `load_report_evidence` — a
  sixth operation. `FR-TRD-051`–`FR-TRD-055` define exactly five. The sixth is
  mentioned only in `FR-TRD-049` prose (README:880) and has no `FR-TRD-*` row of its own.
* **Current:** Export count in the Files table is stale; one public port operation is
  untraced.
* **Required:** Update the key-export cell to six operations and add a dedicated
  `FR-TRD-*` row for `load_report_evidence` with its own unit and usage test mapping.
* **Why it matters:** The port is the persistence contract Data must implement; an
  untraced operation can be missed by the implementer.
* **Verify:** Regenerate the traceability matrix — every public store operation appears
  exactly once.

### `TRD-M02` — MEDIUM — Undocumented public export `SymbolCapability`

* **Rule:** Review §4 "No undocumented public export exists"; README §4.8 Files table
  declares `dependencies.py` key exports as `TradingDependencies` only.
* **Location:** `app/services/trading/actions/dependencies.py:165` —
  `__all__ = ["SymbolCapability", "TradingDependencies"]`; alias defined at `:44`.
* **Current:** A second name is publicly exported at module level without documentation.
* **Required:** Remove `SymbolCapability` from `__all__`, or document it as a key export
  with a requirement row.
* **Why it matters:** `__all__` is the declared public surface; undeclared entries drift
  into consumer imports.
* **Verify:** `__all__` matches the README Files-table key exports for every module.

### `TRD-M03` — MEDIUM — `FR-TRD-056` documents a `route-incompatible` error that is not implemented

* **Rule:** `FR-TRD-056` Raises column — "`TradingError`: required dependency missing
  **or route-incompatible**"; review §4 "Documented errors and failure conditions are
  implemented".
* **Location:** `app/services/trading/actions/dependencies.py:133–162` —
  `__post_init__` checks only `is None` on 17 ports. No route compatibility check
  exists, and the container holds no route field on which to base one.
* **Current:** A container built for a `live` route with `connection=None` and
  `broker_adapter=None` constructs successfully; the failure surfaces later as
  `SERVICE_UNAVAILABLE` from `actions/orders.py:205`.
* **Required:** Either implement route-compatibility validation, or amend the
  requirement to describe the deferred check and where it is enforced.
* **Why it matters:** A documented fail-closed condition that does not exist creates
  false confidence in the dependency boundary.
* **Verify:** A unit test proving the documented error is raised at the documented site.

### `TRD-M04` — MEDIUM — `FR-TRD-031` side-effect classification overstates `dispatch_order_intent`

* **Rule:** Review §4 "Side effects match the documented side-effect classification".
* **Location:** README:682 declares "Broker mutation or external Simulation mutation;
  **persistence write**". `app/services/trading/routing/dispatcher.py:335–409` performs
  no persistence; the write occurs in the caller
  (`app/services/trading/actions/orders.py:126`).
* **Required:** Correct the side-effect cell to "Broker mutation or external Simulation
  mutation" and note that persistence is the caller's responsibility.
* **Verify:** Side-effect column matches the implementation for every FR row.

### `TRD-M05` — MEDIUM — Timeout receipt identity is non-deterministic

* **Rule:** `NFR-TRD-002` (Determinism — "Canonical JSON, Decimal material, IDs,
  projections, and comparisons shall be deterministic", verified by "Replay/hash tests").
* **Location:** `app/services/trading/routing/dispatcher.py:327` —
  `f"timeout-{observed_at.isoformat()}"` feeds `_receipt_identity` at `:48–69`;
  `observed_at` is `datetime.now(UTC)` at `:323`.
* **Current:** Two identical timeouts for the same `client_order_id` produce different
  `receipt_id` values.
* **Required:** Derive the timeout evidence identifier from deterministic material
  (`client_order_id`, `authority_id`, attempt/version) so an unknown-outcome incident
  for one attempt has one stable identity.
* **Why it matters:** `resolve_unknown_outcome` and the unresolved-attempt store key
  off receipt identity. Non-deterministic IDs can produce duplicate unresolved
  incidents for a single frozen attempt.
* **Verify:** A replay test asserting identical timeout inputs yield an identical
  `receipt_id`.

### `TRD-M06` — MEDIUM — Systemic Files-table dependency inaccuracies

* **Rule:** Review §4 "Standard-library, third-party, and local dependencies match the
  table"; README §8 step 5.
* **Locations (most material):**
  * `contracts/errors.py` — README:513 declares third-party "None"; the module imports
    `pydantic.ValidationError` (`errors.py:5`) and `re` (`:3`), and declares stdlib
    `typing` only.
  * `contracts/registry.py` — README:514 declares third-party "None"; imports
    `pydantic` (`registry.py:5`) and `types` (`:4`).
  * `reporting/evidence.py` — README:869 declares `pydantic>=2.13.4`; the module
    imports no pydantic.
  * `live/config.py` — README:774 declares `pydantic-settings>=2.14.2` and local
    "Utils settings; Data session provider"; the module imports neither
    (`config.py:7–18`).
  * `routing/capabilities.py` — README:664 declares local Brokers `BrokerFeatureFlags`
    and Simulation public contracts; the module imports neither
    (`capabilities.py:1–10`).
  * Undeclared stdlib imports across ~20 files (`hashlib`, `types`, `typing`,
    `datetime`, `decimal`, `collections.abc`, `asyncio`) — e.g. `state/projections.py`
    and `state/migrations.py` declare "Standard library: None" while importing
    `collections.abc`/`datetime`/`types`/`typing` and `hashlib` respectively.
* **Required:** Reconcile every Files-table dependency cell against actual imports.
* **Why it matters:** The Files table is the declared dependency boundary used to detect
  forbidden deep imports; if it is inaccurate, the check cannot be trusted.
* **Verify:** An automated comparison of declared versus actual imports reports zero
  differences.

### `TRD-L01` — LOW — Cross-module private-symbol imports

`app/services/trading/actions/emergency.py:7–11` imports `_authority_id` and
`_require_action` from `actions/orders.py`. Private helpers should be promoted to a
shared internal module or given non-underscore internal names. No behavioural impact.
**Verify:** No underscore-prefixed symbol is imported across modules.

### `TRD-L02` — LOW — `BROKER_OPERATION_TIMEOUT_SECONDS` is a hard-coded constant

`app/services/trading/routing/capabilities.py:10` — `Decimal(10)`. README:673 marks it
`Required = Yes` with a ratified default of `10`, so the value is correct, but it is not
profile-configurable and `capabilities.py:80` requires adapters to declare exactly this
number. Consider sourcing it from validated configuration alongside the other bounds
fixed in `TRD-B04`. **Verify:** Configuration-driven timeout with the ratified default.

### `TRD-L03` — LOW — Dispatcher uses process wall clock rather than the injected clock

`app/services/trading/routing/dispatcher.py:158` and `:323` call `datetime.now(UTC)`
while `TradingDependencies.clock` (`actions/dependencies.py:116`) exists as the domain's
aware UTC clock. Receipt `received_at` and timeout observation are therefore not
replay-controllable. `FR-TRD-031`'s signature does not currently admit a clock, so this
requires a spec decision. **Verify:** Receipt timestamps are reproducible under a
frozen clock.

### `TRD-L04` — LOW — Inconsistent bulk ceiling semantics

`app/services/trading/actions/emergency.py:131` compares `max_children` against
*eligible* orders only, while `:210` compares it against *all* positions. README §4.8
describes one `max_children` ceiling for bulk actions. Align both to the same
definition. **Verify:** A unit test pinning the ceiling semantics for both verbs.

### `TRD-L05` — LOW — Usage-example convention diverges from the recorded Strategy precedent

`docs/CHANGELOG.md` records that Strategy "replaced pytest-style usage cases with 14
numbered scripts using package-root exports". Trading uses pytest-style
`test_usage_*` functions (`tests/trading/usage/`), which is what the Trading README
§2 and §7 prescribe, so the domain is internally consistent — but the repository now
has two usage conventions. Owner decision required; no behavioural impact.
**Verify:** One recorded convention, or an explicit note that both are permitted.

### `TRD-L06` — LOW — `FR-TRD-011` absent from numbering with no retirement note

The requirement sequence runs `FR-TRD-001`…`FR-TRD-065` with `FR-TRD-011` missing
(64 rows, all `Completed`). `CAP-TRD-022` (README:935, "Remove — No raw signal
translator") is the probable origin, but no note records the retirement.
AGENTS.md §6 Decision Hygiene forbids retaining resolved decision history yet expects
the outcome to be written as an explicit exclusion. **Verify:** A one-line explicit
exclusion note, or renumbering.

---

## 5. Expected-versus-actual package inventory

Source of truth: `app/services/trading/README.md` §2 (lines 155–208).

| Expected path | Actual | Result |
|---|---|---|
| `trading/__init__.py` | present | Match |
| `trading/README.md` | present | Match |
| `trading/contracts/__init__.py` | present | Match |
| `trading/contracts/models.py` | present | Match |
| `trading/contracts/errors.py` | present | Match |
| `trading/contracts/registry.py` | present | Match |
| `trading/state/__init__.py` | present | Match |
| `trading/state/events.py` | present | Match |
| `trading/state/stores.py` | present | Match |
| `trading/state/idempotency.py` | present | Match |
| `trading/state/projections.py` | present | Match |
| `trading/state/migrations.py` | present | Match |
| `trading/validation/__init__.py` | present | Match |
| `trading/validation/orders.py` | present | Match |
| `trading/validation/snapshots.py` | present | Match |
| `trading/validation/readiness.py` | present | Match |
| `trading/validation/plans.py` | present | Match |
| `trading/routing/__init__.py` | present | Match |
| `trading/routing/capabilities.py` | present | Match |
| `trading/routing/responses.py` | present | Match |
| `trading/routing/dispatcher.py` | present | Match |
| `trading/reconciliation/__init__.py` | present | Match |
| `trading/reconciliation/snapshots.py` | present | Match |
| `trading/reconciliation/compare.py` | present | Match |
| `trading/reconciliation/authority.py` | present | Match |
| `trading/monitoring/__init__.py` | present | Match |
| `trading/monitoring/events.py` | present | Match |
| `trading/monitoring/budgets.py` | present | Match |
| `trading/live/__init__.py` | present | Match |
| `trading/live/config.py` | present | Match |
| `trading/live/session.py` | present | Match |
| `trading/live/gates.py` | present | Match |
| `trading/actions/__init__.py` | present | Match |
| `trading/actions/dependencies.py` | present | Match |
| `trading/actions/orders.py` | present | Match |
| `trading/actions/positions.py` | present | Match |
| `trading/actions/controls.py` | present | Match |
| `trading/actions/emergency.py` | present | Match |
| `trading/actions/rebalance.py` | present | Match |
| `trading/actions/runtime.py` | present | Match |
| `trading/reporting/__init__.py` | present | Match |
| `trading/reporting/evidence.py` | present | Match |

* **Undocumented production files:** none.
* **Parallel or legacy implementations:** none. No alias, wrapper, shim, agent, or
  compatibility module found.
* **Package root contents:** exactly `README.md`, `__init__.py`, and the nine capability
  modules, as required by README:238.
* **Dependency order:** file and module ordering matches the §2 dependency diagram; no
  reverse import found (`contracts` imports no sibling module; `state` imports
  `contracts` only; `live` imports `validation`/`routing`/`reconciliation`/`monitoring`;
  `actions` imports `live` and below; `reporting` imports `state`/`reconciliation`
  contracts).
* **`__init__.py` export surfaces:** all ten declare explicit imports and `__all__`; the
  package root re-exports exactly 58 names, all resolvable. One deviation —
  `TRD-M02`, `SymbolCapability` in `actions/dependencies.py.__all__`.
* **Import side effects:** verified by AST scan of every module top level. Only pure
  constant construction occurs (`frozenset`, `re.compile`, `Decimal(10)`). No network,
  database, broker, worker, simulator, clock, or filesystem access at import.
  `NFR-TRD-005` satisfied.

---

## 6. Functional-requirement traceability matrix

All 64 declared `FR-TRD-*` rows appear exactly once. `FR-TRD-011` is not declared
(`TRD-L06`). "Unit" and "Usage" columns were verified to resolve to an existing file
*and* function for all 64 rows.

| Requirement | README location | Implementation location | Unit test | Usage test | Result | Finding |
|---|---|---|---|---|---|---|
| FR-TRD-001 | README:537 | `contracts/models.py:298` | `unit/contracts/test_models.py::test_trading_route_rejects_unknown` | `usage/test_usage_contracts.py::test_usage_models_trading_route` | Pass | — |
| FR-TRD-002 | README:538 | `contracts/models.py:306` | `…test_models.py::test_trading_request_requires_governed_evidence` | `…test_usage_contracts.py::test_usage_models_trading_request` | Pass | see TRD-H04 (bypassed by `model_copy`) |
| FR-TRD-003 | README:539 | `contracts/models.py:531` | `…test_models.py::test_standard_envelope_status_contract` | `…test_usage_models_standard_envelope` | Pass | — |
| FR-TRD-004 | README:540 | `contracts/models.py:645` | `…test_order_intent_cannot_exceed_risk_size` | `…test_usage_models_order_intent` | Pass | — |
| FR-TRD-005 | README:541 | `contracts/models.py:861` | `…test_receipt_requires_authority_evidence` | `…test_usage_models_execution_receipt` | Pass | — |
| FR-TRD-006 | README:542 | `contracts/models.py:1043` | `…test_trade_record_flags_unreconciled_state` | `…test_usage_models_trade_record` | Pass | — |
| FR-TRD-007 | README:549 | `contracts/errors.py:110` | `unit/contracts/test_errors.py::test_trading_error_rejects_unknown_code` | `…test_usage_errors_trading_error` | Pass | — |
| FR-TRD-008 | README:550 | `contracts/errors.py:201` | `…test_map_trading_error_redacts_provider_exception` | `…test_usage_errors_map_trading_error` | Pass | — |
| FR-TRD-009 | README:551 | `contracts/errors.py:79` | `…test_redaction_is_recursive_and_case_insensitive` | `…test_usage_errors_redact_trading_payload` | **Fail** | **TRD-B01** — implemented but not applied at 11 emission sites |
| FR-TRD-010 | README:557 | `contracts/registry.py:148` | `unit/contracts/test_registry.py::test_public_catalog_matches_exports` | `…test_usage_registry_get_public_contracts` | Pass | — |
| FR-TRD-012 | README:558 | `contracts/registry.py:158` | `…test_create_draft_has_no_side_effect` | `…test_usage_registry_create_draft` | Pass | — |
| FR-TRD-013 | README:836 | `actions/orders.py:289` | `unit/actions/test_orders.py::test_submit_order_route_parity` | `usage/test_usage_actions.py::test_usage_orders_submit_order` | Partial | TRD-H01 — live/paper positive path untested |
| FR-TRD-014 | README:837 | `actions/orders.py:306` | `…test_modify_order_rejects_stale_version` | `…test_usage_orders_modify_order` | Pass | — |
| FR-TRD-015 | README:838 | `actions/orders.py:329` | `…test_cancel_order_is_idempotent` | `…test_usage_orders_cancel_order` | Pass | — |
| FR-TRD-016 | README:839 | `actions/positions.py` (`close_position`) | `unit/actions/test_positions.py::test_partial_close_preserves_position_identity` | `…test_usage_positions_close_position` | Pass | — |
| FR-TRD-017 | README:840 | `actions/positions.py` (`modify_position`) | `…test_modify_position_rejects_unapproved_field` | `…test_usage_positions_modify_position` | Pass | — |
| FR-TRD-018 | README:841 | `actions/positions.py:150` (`reduce_exposure`) | `…test_reduce_exposure_cannot_increase` | `…test_usage_positions_reduce_exposure` | Pass | — |
| FR-TRD-019 | README:842 | `actions/controls.py` (`pause_strategy`) | `unit/actions/test_controls.py::test_pause_does_not_promote_strategy` | `…test_usage_controls_pause_strategy` | Pass | — |
| FR-TRD-020 | README:843 | `actions/controls.py` (`resume_strategy`) | `…test_resume_requires_cleared_hierarchy_and_reconciliation` | `…test_usage_controls_resume_strategy` | Pass | — |
| FR-TRD-021 | README:845 | `actions/controls.py` (`trigger_kill_switch`) | `…test_request_text_cannot_self_classify_emergency` | `…test_usage_controls_trigger_kill_switch` | Pass | — |
| FR-TRD-022 | README:846 | `actions/controls.py` (`clear_kill_switch`) | `…test_clear_cannot_override_active_parent` | `…test_usage_controls_clear_kill_switch` | Pass | — |
| FR-TRD-023 | README:847 | `actions/emergency.py:92` | `unit/actions/test_emergency.py::test_cancel_all_preserves_uncertain_results` | `…test_usage_emergency_cancel_all` | Partial | **TRD-H03**, TRD-H04, TRD-L04 |
| FR-TRD-024 | README:641 | `validation/orders.py:267` | `unit/validation/test_orders.py::test_invalid_order_never_reaches_authority` | `usage/test_usage_validation.py::test_usage_orders_validate_order_request` | Pass | — |
| FR-TRD-025 | README:844 | `actions/controls.py` (`sync_positions`) | `…test_sync_is_route_read_only` | `…test_usage_controls_sync_positions` | Pass | — |
| FR-TRD-026 | README:642 | `validation/snapshots.py:155` | `unit/validation/test_snapshots.py::test_snapshot_never_substitutes_neutral_defaults` | `…test_usage_snapshots_get_route_snapshot` | Pass | — |
| FR-TRD-027 | README:643 | `validation/readiness.py:188` | `unit/validation/test_readiness.py::test_readiness_fails_on_any_missing_evidence` | `…test_usage_readiness_assess` | **Fail** | **TRD-B04** — `MAX_STALENESS_SECONDS` not enforced |
| FR-TRD-028 | README:644 | `validation/plans.py:10` | `unit/validation/test_plans.py::test_plan_is_deterministic` | `…test_usage_plans_build_execution_plan` | Pass | — |
| FR-TRD-029 | README:680 | `routing/capabilities.py:84` | `unit/routing/test_capabilities.py::test_missing_security_contract_blocks` | `usage/test_usage_routing.py::test_usage_capabilities_validate` | Pass | TRD-M06 |
| FR-TRD-030 | README:681 | `routing/responses.py:219` | `unit/routing/test_responses.py::test_malformed_success_is_unknown_outcome` | `…test_usage_responses_classify` | Pass | — |
| FR-TRD-031 | README:682 | `routing/dispatcher.py:335` | `unit/routing/test_dispatcher.py::test_dispatch_has_single_mutation_boundary` | `…test_usage_dispatcher_dispatch` | Partial | TRD-M04, TRD-M05, TRD-L03 |
| FR-TRD-032 | README:791 | `live/session.py:51` | `unit/live/test_session.py::test_session_starts_package_only` | `usage/test_usage_live.py::test_usage_session_live_session` | Pass | — |
| FR-TRD-033 | README:792 | `live/session.py:373` | `…test_start_never_enables_before_reconciliation` | `…test_usage_session_start` | Pass | — |
| FR-TRD-034 | README:793 | `live/session.py:438` | `…test_status_never_overstates_readiness` | `…test_usage_session_status` | Pass | — |
| FR-TRD-035 | README:794 | `live/session.py` (`stop`) | `…test_stop_reports_flush_and_reconciliation_failure` | `…test_usage_session_stop` | Pass | — |
| FR-TRD-036 | README:795 | `live/gates.py:163` | `unit/live/test_gates.py::test_real_risk_decision_is_mandatory` | `…test_usage_gates_evaluate_live_gate` | Partial | TRD-B01 (pre-audit unredacted), TRD-H01 |
| FR-TRD-037 | README:594 | `state/events.py:22` | `unit/state/test_events.py::test_event_requires_trace_and_utc_time` | `usage/test_usage_state.py::test_usage_events_trading_event` | **Fail** | **TRD-B01** — `redaction_applied: Literal[True]` at `events.py:49` |
| FR-TRD-038 | README:595 | `state/stores.py:20` | `unit/state/test_stores.py::test_store_contract_failure_is_visible` | `…test_usage_stores_trading_state_store` | Partial | TRD-M01 |
| FR-TRD-039 | README:596 | `state/idempotency.py:116` | `unit/state/test_idempotency.py::test_same_key_different_material_rejected` | `…test_usage_idempotency_reserve` | **Fail** | **TRD-B04** — `IDEMPOTENCY_RETENTION_SECONDS` absent |
| FR-TRD-040 | README:597 | `state/projections.py:273` | `unit/state/test_projections.py::test_apply_event_rejects_stale_version` | `…test_usage_projections_apply_event` | Pass | — |
| FR-TRD-041 | README:598 | `state/migrations.py:8` | `unit/state/test_migrations.py::test_schema_version_matches_events` | `…test_usage_migrations_schema_version` | Pass | — |
| FR-TRD-042 | README:599 | `state/migrations.py:57` | `…test_migrations_are_additive_and_ordered` | `…test_usage_migrations_get_migrations` | Pass | — |
| FR-TRD-043 | README:715 | `reconciliation/snapshots.py:34` | `unit/reconciliation/test_snapshots.py::test_snapshot_is_json_safe` | `usage/test_usage_reconciliation.py::test_usage_snapshots_authority_snapshot` | Pass | — |
| FR-TRD-044 | README:716 | `reconciliation/compare.py:163` | `unit/reconciliation/test_compare.py::test_unresolved_mismatch_stays_unresolved` | `…test_usage_compare_authority_state` | Pass | — |
| FR-TRD-045 | README:717 | `reconciliation/authority.py:248` | `unit/reconciliation/test_authority.py::test_unknown_outcome_cannot_blind_retry` | `…test_usage_authority_resolve_unknown` | Pass | TRD-M05 (identity determinism) |
| FR-TRD-046 | README:752 | `monitoring/events.py:27` | `unit/monitoring/test_events.py::test_event_has_trace_and_severity` | `usage/test_usage_monitoring.py::test_usage_events_operational_event` | Pass | — |
| FR-TRD-047 | README:753 | `monitoring/budgets.py:21` | `unit/monitoring/test_budgets.py::test_budget_gate_requires_exact_plan_binding` | `…test_usage_budgets_budget_gate` | Pass | — |
| FR-TRD-048 | README:754 | `monitoring/events.py:189` | `…test_event_delivery_failure_is_incident` | `…test_usage_events_emit_runtime_event` | Pass | Only correct redaction site in the domain |
| FR-TRD-049 | README:880 | `reporting/evidence.py:31` | `unit/reporting/test_evidence.py::test_report_does_not_compute_analytics_metrics` | `usage/test_usage_reporting.py::test_usage_evidence_build_trading_report` | **Fail** | **TRD-B01**, **TRD-H05**, TRD-M01 |
| FR-TRD-050 | README:848 | `actions/emergency.py:174` | `unit/actions/test_emergency.py::test_close_all_reports_partial_completion` | `…test_usage_emergency_close_all` | Partial | **TRD-H03**, TRD-H04, TRD-L04 |
| FR-TRD-051 | README:600 | `state/stores.py:23` | `unit/state/test_stores.py::test_reserve_idempotency_is_atomic` | `…test_usage_stores_reserve_idempotency` | Pass | — |
| FR-TRD-052 | README:601 | `state/stores.py:43` | `…test_append_event_is_append_only` | `…test_usage_stores_append_event` | Pass | — |
| FR-TRD-053 | README:602 | `state/stores.py:53` | `…test_load_projection_is_scope_isolated` | `…test_usage_stores_load_projection` | Pass | — |
| FR-TRD-054 | README:603 | `state/stores.py:64` | `…test_save_projection_rejects_stale_version` | `…test_usage_stores_save_projection` | Pass | — |
| FR-TRD-055 | README:604 | `state/stores.py:79` | `…test_unresolved_attempts_are_scope_isolated` | `…test_usage_stores_load_unresolved_attempts` | Pass | — |
| FR-TRD-056 | README:849 | `actions/dependencies.py:84` | `unit/actions/test_dependencies.py::test_dependencies_have_no_import_side_effect` | `…test_usage_dependencies_trading_dependencies` | Partial | TRD-M02, TRD-M03 |
| FR-TRD-057 | README:605 | `state/idempotency.py:23` | `unit/state/test_idempotency.py::test_reservation_states_are_finite` | `…test_usage_idempotency_reservation` | Pass | — |
| FR-TRD-058 | README:606 | `state/projections.py:36` | `unit/state/test_projections.py::test_projection_requires_scope_and_version` | `…test_usage_projections_trading_projection` | Pass | — |
| FR-TRD-059 | README:645 | `validation/snapshots.py:15` | `unit/validation/test_snapshots.py::test_route_snapshot_requires_provenance` | `…test_usage_snapshots_route_snapshot` | Pass | — |
| FR-TRD-060 | README:646 | `validation/readiness.py:20` | `unit/validation/test_readiness.py::test_readiness_assessment_is_bounded` | `…test_usage_readiness_assessment` | Pass | — |
| FR-TRD-061 | README:718 | `reconciliation/compare.py:23` | `…test_report_cannot_claim_false_resolution` | `…test_usage_compare_reconciliation_report` | Pass | — |
| FR-TRD-062 | README:719 | `reconciliation/authority.py:28` | `…test_resolution_requires_approved_transition` | `…test_usage_authority_resolution` | Pass | — |
| FR-TRD-063 | README:543 | `contracts/models.py:1294` | `unit/contracts/test_models.py::test_rebalance_request_requires_canonical_hash` | `…test_usage_models_portfolio_rebalance_request` | Pass | — |
| FR-TRD-064 | README:850 | `actions/rebalance.py:238` | `unit/actions/test_rebalance.py::test_rebalance_cannot_open_to_match_weight` | `…test_usage_rebalance_execute_portfolio_rebalance` | Partial | **TRD-B03** — workflow-level negative evidence absent |
| FR-TRD-065 | README:851 | `actions/runtime.py:304` | `unit/actions/test_runtime.py::test_cycle_never_generates_or_sizes_signals` | `…test_usage_runtime_run_live_evaluation_cycle` | Pass | — |

**Summary:** 64 declared · 51 Pass · 8 Partial · 5 Fail.

---

## 7. Non-functional-requirement compliance matrix

| NFR | Type | Implementation evidence | Test evidence | Result | Finding |
|---|---|---|---|---|---|
| NFR-TRD-001 | Safety | Fail-closed gate chain `live/gates.py:181–254`; `_validate_kill_switches` `:111`; `reconciliation_ready` `:226`; pre-audit block `:242` | `integration/test_live_dispatch.py`, `test_readiness.py`, `test_unknown_outcome.py`, `test_kill_switch.py` | **Fail** | **TRD-B04** — `MAX_STALENESS_SECONDS` bound absent; freshness delegated to caller-supplied `expires_at` |
| NFR-TRD-002 | Determinism | `canonical_json` + SHA-256 in `validation/plans.py`, `state/idempotency.py:134`, `actions/orders.py:111`; frozen pydantic models throughout | `unit/validation/test_plans.py::test_plan_is_deterministic` | **Fail** | **TRD-M05** — `dispatcher.py:327` timeout identity varies per call; TRD-L03 wall clock |
| NFR-TRD-003 | Security | `redact_trading_payload` `contracts/errors.py:79`; `is_sensitive_key` gate `live/config.py:116`; no provider SDK import (verified across all 31 modules) | `unit/contracts/test_errors.py::test_redaction_is_recursive_and_case_insensitive` | **Fail** | **TRD-B01** — redaction claimed at 11 sites, applied at 2 |
| NFR-TRD-004 | Reliability | `classify_authority_response` conservative mapping `routing/responses.py`; `_timeout_receipt` `dispatcher.py:313`; retry lock `reconciliation/authority.py:248` | `integration/test_unknown_outcome.py::test_unknown_outcome_blocks_retry` | Pass | TRD-M05 (identity) |
| NFR-TRD-005 | API boundary | Explicit `__all__` in all 10 `__init__.py`; AST scan confirms zero import-time side effects | `unit/contracts/test_registry.py::test_public_catalog_matches_exports`; `unit/actions/test_dependencies.py::test_dependencies_have_no_import_side_effect` | Partial | TRD-M02 |
| NFR-TRD-006 | Observability | Trace IDs on every contract; 230/230 functions carry a `logger` call; pre-audit write blocks send `live/gates.py:231–243` | `unit/live/test_gates.py`; `integration/test_monitoring.py` | **Fail** | **TRD-B01** — pre/post evidence is not redacted |
| NFR-TRD-007 | Testing | 160 tests: 82 unit / 14 integration / 64 usage; every FR has a resolvable unit + usage test | Full domain run, coverage 84.06% | **Fail** | **TRD-B03**, **TRD-H01**, **TRD-H02**, **TRD-H03** |
| NFR-TRD-008 | Performance | Only the ratified `BROKER_OPERATION_TIMEOUT_SECONDS = 10` is enforced; no unapproved SLO represented | `unit/routing/test_capabilities.py` | Pass | TRD-L02 |

---

## 8. Workflow and system-workflow verification

| Workflow | Mapped integration test | Exists | Passes | Genuine end-to-end | Result |
|---|---|---|---|---|---|
| WF-TRD-001 | `test_validate_and_package.py::test_validate_and_package_fails_closed` | Yes | Yes | Partial (fail-closed branch only) | Pass with TRD-H02 |
| WF-TRD-002 | `test_sim_dispatch.py::test_sim_dispatch_uses_simulation_authority` | Yes | Yes | Yes | Pass |
| WF-TRD-003 | `test_live_startup.py::test_live_startup_requires_reconciliation` | Yes | Yes | Partial | Pass with TRD-H02 |
| WF-TRD-004 | `test_live_dispatch.py::test_live_dispatch_requires_real_risk_decision` | Yes | Yes | **No — negative branch only** | **Fail — TRD-H01** |
| WF-TRD-005 | `test_unknown_outcome.py::test_unknown_outcome_blocks_retry` | Yes | Yes | Yes | Pass |
| WF-TRD-006 | `test_readiness.py::test_unavailable_route_fact_fails_readiness` | Yes | Yes | Partial | Pass with TRD-B04 caveat |
| WF-TRD-007 | `test_kill_switch.py::test_kill_switch_blocks_and_reports_partial_emergency_results` | Yes | Yes | `sim` route only | **Partial — TRD-H03** |
| WF-TRD-008 | `test_state_recovery.py::test_recovery_preserves_unresolved_attempt` | Yes | Yes | Yes | Pass |
| WF-TRD-009 | `test_live_shutdown.py::test_shutdown_reports_unresolved_work` | Yes | Yes | Partial | Pass with TRD-H02 |
| WF-TRD-010 | `test_monitoring.py::test_budget_and_event_delivery_failures_emit_incidents` | Yes | Yes | Yes | Pass |
| WF-TRD-011 | `test_reporting.py::test_report_contains_only_execution_evidence` | Yes | Yes | Yes | **Fail — TRD-B01, TRD-H05** |
| WF-TRD-012 | `test_upstream_request.py::test_raw_signal_translation_is_rejected` | Yes | Yes | Yes | Pass |
| WF-TRD-013 | `test_portfolio_rebalance.py::test_rebalance_cannot_bypass_risk_or_open_to_match_weight` | **No** | n/a | n/a | **Fail — TRD-B03** |
| WF-TRD-014 | `test_live_cycle.py::test_cycle_submits_intent_and_never_sizes` | Yes | Yes | Yes | Pass |

**`SYS-WF-*` chain reconciliation.** Trading's workflows reference `SYS-WF-001`,
`SYS-WF-002`, `SYS-WF-005`, `SYS-WF-006`, and `SYS-WF-008`. All five are recorded
`Missing` in `docs/PROJECT.md:401–408` with system-level integration tests under
`tests/system/integration/` that do not yet exist. That is expected at this stage —
system-level assembly is a later phase and is not a Trading defect — but it means no
Trading workflow currently has end-to-end system evidence, and the chain step
descriptions (`docs/PROJECT.md:493`, `:642`, `:735`) match the Trading implementation on
inspection only.

---

## 9. Contract and persistence reconciliation

**Owned contracts.**

| Contract | README §1 | `docs/PROJECT.md` | `contract_version` | `schema_id` | Result |
|---|---|---|---|---|---|
| `OrderIntent v1` | Completed | **Missing** (`:765`) | `models.py:656` `Literal["v1"]` | `models.py:657` `trading.order_intent.v1` | Schema correct; **status conflict TRD-B02** |
| `ExecutionReceipt v1` | Completed | **Missing** (`:766`) | `models.py:870` | `models.py:871` `trading.execution_receipt.v1` | Schema correct; **TRD-B02** |
| `TradeRecord v1` | Completed | **Missing** (`:766`) | `models.py:1052` | `models.py:1053` `trading.trade_record.v1` | Schema correct; **TRD-B02** |
| `PortfolioRebalanceExecutionRequest v1` | Completed | **Missing** (`:785`) | `models.py:1304` | `models.py:1305` `trading.portfolio_rebalance_execution_request.v1` | Schema correct; **TRD-B02** |
| `OperationalEvent v1` | Completed | **Missing** (`:767`) | `monitoring/events.py` | `events.py:33` `trading.operational_event.v1` | Schema correct; **TRD-B02** |
| `TradingRequest v1` (internal) | README §4.1 | n/a (internal) | `models.py:319` | `models.py:320` `trading.trading_request.v1` | Pass |
| *(unregistered)* execution evidence report | — | — | hard-coded `"v1"` | `reporting/evidence.py:72` `trading.execution_evidence_report.v1` | **Fail — TRD-H05** |

* `contract_version` and `schema_id` are separate `Literal` fields on every owned model;
  compatibility is never inferred from the identifier. Matches `docs/PROJECT.md:805`.
* `StandardTradingEnvelope` is kept Trading-internal and is not exported as a
  cross-domain contract, matching README:82 and `docs/PROJECT.md:815`.

**Consumed contracts.** No redefinition found. All consumed types are imported from the
owning domain's public contract module: `app.services.risk.contracts`
(`ActionPolicyVerdict`, `AllocationRiskDecision`, `KillSwitchCommand`, `KillSwitchState`,
`PortfolioBudgetExecutionVerdict`, `RiskDecisionPackage`,
`StrategyOperationalEligibilityDecision`, `DecisionState`), `app.services.data.contracts`
(`AccountStateSnapshot`, `MarketDataset`, `MigrationStep`),
`app.services.brokers.contracts` (`BrokerAdapter`, `BrokerConnectionConfig`,
`BrokerSymbolInfo`, `BrokerResult`, `BrokerError*`, mutation DTOs),
`app.services.indicators` (`IndicatorResult`), `app.services.strategy` (`TradeIntent`).
The name reconciliation table at README:85–89 is accurate. Simulation is reached only
through the injected `Callable[[OrderIntent], Awaitable[ExecutionReceipt]]` — no
Simulation import exists, as specified.

**Producer–consumer compatibility tests.** `integration/test_upstream_request.py` and
`integration/test_sim_dispatch.py` cover Risk lineage and Simulation dispatch.
`unit/routing/test_dispatcher.py:217–381` covers the Brokers `BrokerAdapter` mutation
DTO surface for all six mutation actions plus environment/provider mismatch rejection.
No dedicated compatibility test exists for the `PortfolioRebalanceExecutionRequest`
producer boundary (covered by TRD-B03).

**Persistence.** Trading declares schemas and migrations only
(`state/migrations.py:8` `TRADING_SCHEMA_VERSION`, `:57` `get_trading_migrations`
returning Data-owned `MigrationStep` values). No connection, session, engine, lock, or
file handle is created anywhere in the package; all persistence flows through the
injected `TradingStateStore` protocol. No foreign state is written. This matches
`docs/PROJECT.md:834` ownership rules — **except** that the registry row itself is
still `Missing` (`TRD-B02`).

---

## 10. Public API and dependency-boundary review

* **Root surface:** 58 names in `app/services/trading/__init__.py.__all__`, each backed
  by a module-level `__all__` and a documented key export. Verified resolvable.
* **Prohibited crossings:** no provider SDK import (`MetaTrader5`, `binance`,
  `ctrader_open_api`, `twisted`), no database session, no `DataFrame`, no foreign
  internal module import, and no reverse dependency. Cross-domain imports use
  `…contracts` public modules or documented package roots only.
* **Circular dependencies:** none. Module order matches the §2 diagram.
* **Rejected capabilities:** absent as required — no shadow comparison, no performance
  snapshot cache, no Trading-owned rate-limit policy engine, no raw signal translator,
  no generic service/manager/engine layer, no duplicate low-level order API, no lazy
  package attributes, and no `asyncio.run` bridge inside library code (`asyncio.run`
  appears only in tests).
* **Async contract:** every mutation-capable verb is `async` and awaits the dispatch
  path; `dispatch_order_intent` awaits both the `BrokerAdapter` and the injected
  simulation callback, and applies `asyncio.timeout` at `dispatcher.py:386`.
* **Deviations:** `TRD-M02` (`SymbolCapability`), `TRD-L01` (cross-module private
  imports), `TRD-M06` (Files-table dependency drift).

---

## 11. Safety and security review

| Rule | Evidence | Result |
|---|---|---|
| Fail-closed on missing/stale/invalid/unknown/conflicting evidence | `live/gates.py:182–243`; `_validate_kill_switches:111` treats absent or `unknown` state as blocking; `validation/snapshots.py` returns explicit unavailable/stale | Pass, with **TRD-B04** freshness-bound gap |
| No live mutation without deterministic approval | `live/config.py:60` `allow_live_mutations` defaults `False`; `live/gates.py:189` returns `packaged` when admission is disabled | Pass |
| No Risk / kill-switch / idempotency / reconciliation / authority bypass | `_validate_risk` requires a real `RiskDecisionPackage` with a bound token (`gates.py:89–107`); reservation and `reconciliation_ready` are mandatory | Pass |
| No invented backtest results, performance values, broker fills, or provider evidence | `reporting/evidence.py` packages stored facts only and computes no metric; `dispatcher.py` never synthesizes a fill; `_timeout_receipt` yields `unknown_outcome` | Pass |
| No secret leakage in logs, errors, events, reports, audit records | Redaction implemented but not applied at 11 emission sites | **Fail — TRD-B01** |
| No raw external exception crossing a public boundary | `dispatcher.py:394–400`, `idempotency.py:142–151`, `evidence.py:54–59`, `gates.py:242` all map to `TradingError`; zero bare `except` (ruff `BLE` clean) | Pass |
| No unsafe network / filesystem / subprocess / env access | Verified by grep across the package: zero occurrences of `open(`, `Path(`, `os.environ`, `getenv`, `subprocess`, `requests`, `importlib`, `eval`, `exec` | Pass |
| No unsafe wall clock or randomness where prohibited | `datetime.now(UTC)` at `dispatcher.py:158`, `:323` only; no `random` usage | Partial — **TRD-L03**, **TRD-M05** |
| No silent retry after an unknown mutation outcome | `reconciliation/authority.py:248` locks the scope; `classify_authority_response` marks `retry_safe` conservatively | Pass |
| No arbitrary code execution or unapproved dynamic import | None found | Pass |
| No import-time external or persistent side effect | AST scan of all 31 modules — only constant construction at module level | Pass |
| Secrets never persisted or embedded in identifiers | `live/config.py:116` rejects any sensitive key in configuration; identifiers derive from `client_order_id` / canonical hashes | Pass |

---

## 12. Commands and validation results

Environment: Linux sandbox, CPython 3.14.5, `uv sync --frozen` into an isolated
`/tmp/venv` (the repository `.venv` is a Windows environment and was not modified).
No live broker call, external send, or destructive persistence action was performed.

| # | Command | Exit | Result |
|---|---|---|---|
| 1 | `uv run ruff check app/services/trading tests/trading` | 1 | 94 findings, **all `EXE001 shebang-missing-executable-file`** — an artifact of the Windows→Linux mount exposing files as `0755`. `git ls-files -s` reports mode `100644` for tracked files, so this is environmental, not a repository defect. |
| 2 | `uv run ruff check --ignore EXE001 app/services/trading tests/trading` | 0 | **All checks passed** (full rule set: `D`, `DOC`, `ANN`, `S`, `BLE`, `TRY`, `PL`, `C90`, `RUF`, …) |
| 3 | `uv run ruff format --check app/services/trading tests/trading` | 0 | 94 files already formatted |
| 4 | `uv run mypy app/services/trading` | 0 | Success: no issues found in 41 source files |
| 5 | `uv run mypy app/services/trading tests/trading` | 0 | Success: no issues found in 94 source files |
| 6 | `uv run pytest tests/trading/unit -o addopts="" --import-mode=importlib` | 0 | **82 passed** in 8.08 s |
| 7 | `uv run pytest tests/trading/integration -o addopts="" --import-mode=importlib` | 0 | **14 passed** in 5.84 s |
| 8 | `uv run pytest tests/trading/usage -o addopts="" --import-mode=importlib` | 0 | **64 passed** in 5.69 s |
| 9 | `uv run pytest tests/trading -o addopts="" --import-mode=importlib --cov=app/services/trading --cov-report=term --cov-fail-under=80` | 0 | **160 passed** in 29.37 s; coverage gate reached |
| 10 | Trailing-whitespace scan (`grep -nP '[ \t]+$'`) across `app/services/trading` + `tests/trading` (`.py`, `.md`) | 0 | Zero occurrences |
| 11 | End-of-file-newline scan | 0 | Every file ends with a newline |
| 12 | AST audit — docstring, logger call, and annotation presence for all 230 functions | 0 | 0 missing docstrings · 0 missing `logger` calls · 0 missing annotations |
| 13 | AST audit — module-level side effects | 0 | Constant construction only |
| 14 | README test-reference resolver (142 references) | 1 | **1 unresolved:** `tests/trading/integration/test_portfolio_rebalance.py` (`TRD-B03`) |
| 15 | Requirement-ID audit | — | 64 `FR-TRD-*` rows, 0 duplicates, `FR-TRD-011` absent (`TRD-L06`); 8 `NFR-TRD-*` rows, all `Completed` |

Not run, and why:
* Full repository `pytest` — AGENTS.md §6 prohibits it during targeted work and the
  Trading README does not require it.
* `pre-commit run` — requires network hook installation; equivalent checks (1, 3, 10, 11)
  were run directly. Note the implementation is currently **untracked in git**
  (`git status` reports `?? app/services/trading/{actions,contracts,live,monitoring,reconciliation,reporting,routing,state}/`
  and modified `README.md` / `__init__.py`), so the `detect-secrets`, `trailing-whitespace`,
  and `end-of-file-fixer` hooks have never executed against it. Checks 10 and 11 cover
  the latter two; a `detect-secrets` scan should be run before commit.

---

## 13. Coverage result

```
TOTAL   2570 statements   296 missed   724 branches   227 partial   84.06%
Required test coverage of 80% reached. Total coverage: 84.06%
```

Coverage **passes** the gate. Lowest-covered modules, which correlate directly with the
findings above:

| Module | Coverage | Notable uncovered lines |
|---|---|---|
| `live/gates.py` | 74% | 56, 66, 107, 122, 124, 185, 188, 201, 212, 217, 227, 242–243 — scope mismatch, kill-switch-unknown, schema rejection, and audit-failure branches |
| `live/config.py` | 74% | 36, 39–40, 42, 95, 99, 117, 123–124 — duration rejection and sensitive-key rejection paths |
| `actions/emergency.py` | 76% | 43, 46–47, 115, 132, 135–138, 166–168, 197, 211, 215–222, 245–247 — exactly the bulk-policy and partial-result paths flagged in `TRD-H03` |
| `state/idempotency.py` | 77% | 57, 78, 97, 112, 142–147, 159 — persistence-failure and version-conflict paths |
| `actions/rebalance.py` | 78% | 42, 79–81, 101, 109, 134, 141, 241, 245, 256 — authorization-rejection paths (`TRD-B03`) |
| `routing/dispatcher.py` | 78% | 122–130, 196–197, 230, 232, 276, 290, 294, 303, 310, 322–332, 363, 372, 392–397, 405 — timeout receipt and target-absent branches |
| `routing/responses.py` | 78% | 38, 60, 84, 111–123, 144–153, 174, 205, 240–251 |

Per the review standard, coverage alone does not prove requirement compliance; the five
`Fail` rows in §6 stand despite the gate passing.

---

## 14. README status/checklist accuracy

| README §7 checklist item | Cited evidence | Verdict |
|---|---|---|
| The actual package tree matches Section 2 | `__init__.py:1` | **True** |
| Modules/files remain in dependency order with one coherent responsibility | `README.md:151` | **True** |
| Every requirement and workflow is `Completed` with its mapped test passing | `integration/test_live_cycle.py:33` | **False** — `WF-TRD-013`'s mapped test does not exist (`TRD-B03`); `FR-TRD-009`, `-027`, `-037`, `-039`, `-049` fail |
| The typed public API catalog is exact and import-side-effect free | `contracts/registry.py:78` | **Partly true** — side-effect freedom verified; catalog exactness broken by `TRD-M02` |
| Owned/consumed contracts match `docs/PROJECT.md` and compatibility tests pass | `integration/test_upstream_request.py:11` | **False** — `TRD-B02`, `TRD-H05` |
| Trading-owned schemas/migrations use Data's infrastructure; no foreign state written | `state/stores.py:20` | **True** in code; registry row still `Missing` (`TRD-B02`) |
| Every dependency is documented and no provider SDK crosses the boundary | `actions/dependencies.py:84` | **Partly true** — no SDK crossing; dependency documentation inaccurate (`TRD-M06`) |
| Every public symbol has exactly one FR, usage example, and unit test | `contracts/registry.py:78` | **False** — `load_report_evidence` and `SymbolCapability` untraced (`TRD-M01`, `TRD-M02`) |
| Every collaborative workflow has an integration test | `integration/test_rebalance.py:20` | **False** — cites a different file than `WF-TRD-013` specifies (`TRD-B03`) |
| No rejected capability appears in the architecture or public API | `__init__.py:1` | **True** |
| No unresolved Open Decision affects a completed requirement | — | **True** — §6 reads "No open decisions"; no `TODO`, `FIXME`, `XXX`, or placeholder found in the package |
| Production live mutation is disabled by default and all safety gates fail closed | `live/config.py:49` | **Partly true** — default is `False` (`config.py:60`); the freshness gate does not fail closed (`TRD-B04`) |
| Targeted lint, format, mypy, tests, and 80% coverage pass | `integration/test_live_dispatch.py:19` | **True** — verified in §12 |

Header status `Completed` (README:4) and the `docs/CHANGELOG.md` entry
("Trading is a completed implementation baseline across all 64 functional and eight
non-functional requirements … and all fourteen documented workflows") are **not
supported** by the evidence above and inherit `TRD-B01`–`TRD-B04`.

Also noted: README:986–998 checklist entries carry file:line evidence as AGENTS.md §6
requires, but four of them cite evidence that does not demonstrate the claim.

---

## 15. Final review checklist

* `[X]` Read-only review — no file, code, status, dependency, or staged change created,
  modified, or deleted.
* `[X]` All authoritative sources read in priority order.
* `[X]` Purpose, ownership, and boundaries verified against Section 1.
* `[X]` Full recursive package inventory compared with Section 2.
* `[X]` All 14 `WF-TRD-*` workflows verified against their mapped tests.
* `[X]` All 64 `FR-TRD-*` requirements traced to implementation, unit, and usage evidence.
* `[X]` All 8 `NFR-TRD-*` requirements and every configuration row verified.
* `[X]` Owned and consumed contracts reconciled with `docs/PROJECT.md`.
* `[X]` Persistence ownership and write authority verified.
* `[X]` Safety and security rules reviewed against code, not lint output alone.
* `[X]` Code-quality rules verified by AST audit across all 230 functions.
* `[X]` Domain-scoped lint, format, type, test, and coverage validation executed and recorded.
* `[X]` No live broker operation, external send, or destructive persistence action performed.
* `[X]` Every finding carries severity, rule, file:line, current behavior, required
  behavior, rationale, and post-correction verification.
* `[X]` Result recorded as **NOT READY**; 4 blocking, 5 high, 6 medium, 6 low findings.

---

# GEMINI HANDOFF REPORT

> Copy everything below this line into Gemini as a standalone task prompt.

---

You are the build agent for the HaruQuantAI `Trading` domain
(`app/services/trading`, tests in `tests/trading`). A read-only completion review
returned **NOT READY** with 4 blocking, 5 high, 6 medium, and 6 low findings.

Before doing anything, read `AGENTS.md`, `docs/PROJECT.md`, `docs/ARCHITECTURE.md`,
`docs/CHANGELOG.md`, and `app/services/trading/README.md`. Follow AGENTS.md §2/§3:
produce a Dry Run first (files to read/change, commands planned, scope boundaries,
blockers, rollback path) and wait for the exact phrase `APPROVED: EXECUTE` before
modifying any file. Follow README §8: **update the README before changing code.**

Work the corrections in the order below. Do not batch them; complete and validate each
one before starting the next. Do not refactor anything not named here. Do not invent
requirements, limits, or trading rules — where a decision is required, stop and report
it as `Proposed Decision`.

After every correction, run:

```bash
uv run ruff check app/services/trading tests/trading
uv run ruff format --check app/services/trading tests/trading
uv run mypy app/services/trading tests/trading
uv run pytest tests/trading -o addopts="" --import-mode=importlib \
  --cov=app/services/trading --cov-report=term-missing --cov-fail-under=80
```

(If `ruff check` reports only `EXE001 shebang-missing-executable-file`, ignore it —
it is a filesystem-permission artifact, not a code defect.)

---

## Step 1 — `TRD-B01` (BLOCKING): make `redaction_applied` true evidence, not a constant

**Recommendation:** Every payload that claims redaction must be produced by
`redact_trading_payload` immediately before it is returned, persisted, or audited.

**Implementation:**

1. In `app/services/trading/contracts/errors.py`, keep `redact_trading_payload` as is.
2. Add one internal helper — put it in `app/services/trading/contracts/errors.py` and
   export it through `contracts/__init__.py` **only if** you also add a README §4.1
   requirement row for it; otherwise keep it private and import it directly:

   ```python
   def _redacted_envelope_data(data: Mapping[str, JsonValue]) -> dict[str, JsonValue]:
   ```

   which returns `redact_trading_payload(dict(data))` narrowed to `dict`.
3. Apply redaction at each site that currently hard-codes `redaction_applied: True`:
   * `actions/orders.py:70–87` — redact `data` before constructing the envelope.
   * `actions/orders.py:112–125` — redact the `payload` mapping before building the
     `TradingEvent`.
   * `actions/orders.py:213–224` — redact `data`.
   * `actions/controls.py:~110–125` — redact `data`.
   * `actions/emergency.py:74–89` — redact `results` and `skipped` before packaging.
   * `actions/rebalance.py:~270–281` — redact `data`.
   * `actions/runtime.py:~310–322` — redact `data`.
   * `live/gates.py:146–160` — redact `data` (this includes the full `intent` dump at
     `:252`).
   * `live/gates.py:232–241` — redact the pre-audit mapping before
     `session.write_pre_audit(...)`.
   * `live/session.py:~280–290` — redact `data`.
   * `reporting/evidence.py:64–79` — redact `evidence` before it enters `data`.
   * `contracts/registry.py:~200–207` — redact the draft `data`.
4. In `app/services/trading/state/events.py:49` and
   `app/services/trading/contracts/models.py:365`, keep `redaction_applied` as
   `Literal[True]` but add a `model_validator(mode="after")` that rejects any payload
   containing a key for which `app.utils.is_sensitive_key` returns `True`. This makes
   the literal enforceable rather than decorative.

**Tests to add** (`tests/trading/unit/…`, one per emitting module):

* Plant `{"api_secret": "s3cr3t", "password": "p", "access_token": "t"}` into the source
  material (request extra context, receipt provider metadata, report evidence, gate
  evidence).
* Assert the literal secret string does not appear in
  `json.dumps(result.model_dump(mode="json"))`.
* Assert `redaction_applied` is still `True`.
* Add one negative test proving `TradingEvent(payload={"api_secret": "x"}, …)` raises.

**Verification:** all four commands green; the new tests fail if any redaction call is
removed; grep confirms every `redaction_applied` site is preceded by a
`redact_trading_payload` call in the same function.

---

## Step 2 — `TRD-B04` (BLOCKING): implement the four missing required configuration bounds

**Recommendation:** Implement all four as typed, required, positive settings with no
shared default, validated at configuration load and enforced at the documented call
site. Do **not** silently downgrade the README rows instead — `MAX_STALENESS_SECONDS`
is a fail-closed safety bound.

**Implementation:**

1. **README first.** Confirm README:521, 587, 588, 634 describe the behaviour you are
   about to build. If any row is wrong, correct the row and record the change under
   `Decisions` in `docs/CHANGELOG.md` per AGENTS.md §6.
2. `TRADING_CONTRACT_VERSION` — add to `app/services/trading/contracts/models.py` as
   `TRADING_CONTRACT_VERSION: Final[str] = "v1"`; export it through
   `contracts/__init__.py` and the package root; use it in
   `reporting/evidence.py:71` in place of the hard-coded `"v1"`; add an `FR-TRD-*`
   row (reuse the retired `FR-TRD-011` number and note the reuse, or mint a new one) or
   attach it to the existing §4.1 configuration row with unit + usage tests.
3. `IDEMPOTENCY_RETENTION_SECONDS` — add a required positive `int` field to the runtime
   configuration model in `app/services/trading/live/config.py` (mirroring
   `_PositiveDecimal` validation) and thread it to `reserve_idempotency`. Change
   `state/idempotency.py:116` to accept the retention window (either as an explicit
   parameter or via the request's already-validated configuration reference) and compute
   `expires_at = reservation_time + timedelta(seconds=retention)` instead of using
   `request.valid_until` at `:140`. Update the `FR-TRD-039` signature in README:596 to
   match the new parameter list.
4. `CONCURRENCY_LOCK_TIMEOUT_SECONDS` — add a required positive `Decimal` field to the
   same configuration model. Enforce it where the reservation is held: raise
   `TradingError("TRADING_CONCURRENCY_CONFLICT", …)` when a `duplicate_active`
   reservation's age exceeds the bound (`live/gates.py:206–215`,
   `actions/orders.py:211–228`), and document the stale-lock recovery policy in
   README:588.
5. `MAX_STALENESS_SECONDS` — add a required positive `Decimal` per evidence class.
   Change `validation/readiness.py` so `assess_execution_readiness` receives the bound
   and, in `_append_snapshot_failures` (`:116`) and `_append_risk_failures` (`:135`),
   fails on **both** conditions: caller-declared expiry passed **and**
   `request.system_time - evidence.as_of > MAX_STALENESS_SECONDS`. Update the
   `FR-TRD-027` signature in README:643.

**Tests to add:**

* Per setting: omission raises the documented configuration failure.
* Per setting: a value exactly at the bound passes; one past it fails closed with the
  documented error code.
* `MAX_STALENESS_SECONDS`: a `RouteSnapshot` carrying a far-future `expires_at` but an
  `as_of` older than the bound must now fail readiness. This test must fail against the
  current code.

**Verification:** all four commands green; the staleness test proves the fail-open path
is closed; `grep -r TRADING_CONTRACT_VERSION app/services/trading` returns a definition
and at least one use.

---

## Step 3 — `TRD-B03` (BLOCKING): create the missing `WF-TRD-013` integration test

**Recommendation:** Create the file the README names, covering both negative branches.
Do not "fix" this by editing the README to point at the existing happy-path test.

**Implementation:**

1. Create `tests/trading/integration/test_portfolio_rebalance.py` containing
   `async def test_rebalance_cannot_bypass_risk_or_open_to_match_weight() -> None:`.
2. Build its own fixtures — do **not** import from
   `tests/trading/unit/actions/test_rebalance.py` (see Step 4).
3. The test must assert all of:
   * A `PortfolioRebalanceExecutionRequest` whose `AllocationRiskDecision` is absent,
     expired, or non-approving raises `TradingError` and causes **zero** adapter and
     zero simulation dispatch calls.
   * A request whose `PortfolioBudgetExecutionVerdict` does not bind the exact
     `plan_id` / canonical hash is rejected by `BudgetGate.validate`.
   * An action that would open or increase exposure to match a target weight is
     rejected; only canonical `reduce_exposure` corrections proceed.
   * A tampered `canonical_hash` is rejected.
4. Keep `tests/trading/integration/test_rebalance.py` as the positive-path test, or fold
   it into the new file and delete it — if you delete it, update README:994.

**Verification:** re-run the README reference resolver — every
`tests/trading/…::test_…` reference in the README must resolve to an existing file and
function. The new test must fail if the Risk-authorization check in
`actions/rebalance.py` is removed.

---

## Step 4 — `TRD-H02` (HIGH): stop importing unit-test fixtures into integration tests

**Recommendation:** Move shared fixtures into `tests/trading/conftest.py` as a
deliberate public fixture surface.

**Implementation:**

1. Create `tests/trading/conftest.py`.
2. Move the shared builders currently living in unit test modules into it, with
   non-underscore names: `trading_request`, `trading_dependencies`, `live_session`,
   `live_config`, `live_evidence`, `kill_switch`, `action_policy`,
   `rebalance_request`, `rebalance_dependencies`, `emergency_dependencies`,
   `unknown_dispatch`, `anyio_backend`.
3. Update all 14 integration files and the unit files that defined them to consume the
   shared fixtures. Remove every `from tests.trading.unit…` import from
   `tests/trading/integration/`.
4. Remove the now-redundant per-file `anyio_backend` fixtures.

**Verification:**
`grep -r "from tests.trading.unit" tests/trading/integration` returns nothing; 160+
tests still pass; coverage stays at or above 84%.

---

## Step 5 — `TRD-H01` (HIGH): add the positive end-to-end paper/live dispatch test

**Implementation:**

1. Add `async def test_live_dispatch_completes_single_broker_mutation() -> None:` to
   `tests/trading/integration/test_live_dispatch.py`.
2. Compose from the Step 4 fixtures: a `LiveSession` started with
   `ALLOW_LIVE_MUTATIONS=True` on `route="paper"`, a valid `RiskDecisionPackage` with a
   bound approval token, a matching `ActionPolicyVerdict`, an inactive kill-switch
   hierarchy at every applicable scope, passing readiness, and a counting fake
   `BrokerAdapter` (reuse the `_Adapter` pattern at
   `tests/trading/unit/routing/test_dispatcher.py:217`).
3. Call `submit_order(request, deps)` and assert:
   * `adapter.calls == 1` — exactly one mutation.
   * `outcome.status == "sent"`.
   * Exactly one `TradingEvent` was appended to the store.
   * The pre-audit record was written **before** the adapter call.
4. Add a companion assertion that removing any single mandatory gate causes zero adapter
   calls.

**Verification:** all four commands green; `live/gates.py` coverage rises above 74%;
the test fails if `evaluate_live_gate` is bypassed or if the adapter is called twice.

---

## Step 6 — `TRD-H03` (HIGH): resolve bulk-emergency Risk binding on paper/live

**This step requires an owner decision. Stop and report a `Proposed Decision` before
implementing.**

**Problem:** `live/gates.py:96` requires `decision.approved_size == request.quantity` for
every action. `actions/emergency.py:142` and `:224` give each bulk child a quantity taken
from the broker snapshot while inheriting the parent's single `risk_decision_id`. On
`paper`/`live`, bulk cancel/close therefore fails closed for essentially every child.

**Present these two options to the owner:**

* **Option A** — the composition root supplies a per-child `RiskDecisionPackage`; add a
  `child_risk_decision_source` port to `TradingDependencies` and document it in
  README §4.8.
* **Option B** — exempt non-size-changing actions (`cancel_order`, and `close_position`
  where `reduce_only` is set) from the `approved_size` equality check in
  `_validate_risk`, and document the exemption explicitly in README §4.7 Rules.

**After the decision:** implement it, then add a `paper`-route integration test in which
`cancel_all_orders` produces one successful child per eligible order, explicit
skip rows for non-cancellable states, explicit error rows for orders absent from Trading
state, a `partial` envelope status, and a child count bounded by `max_children`.

**Verification:** `actions/emergency.py` coverage rises above 76%; the bulk verbs are
proven on a non-`sim` route.

---

## Step 7 — `TRD-H04` (HIGH): revalidate derived child requests

**Implementation:** In `app/services/trading/actions/emergency.py`, replace both
`request.model_copy(update={...})` calls (`:142`, `:224`) with a validated construction:

```python
child = TradingRequest.model_validate({**request.model_dump(mode="python"), **updates})
```

Audit `actions/rebalance.py` and `actions/runtime.py` for the same pattern and apply the
same fix wherever a `TradingRequest` is derived rather than constructed.

**Test to add:** a unit test where the update produces an invalid combination (for
example `action="cancel_order"` with `target_broker_order_id=None`, or a non-quantized
`quantity`) and assert `TradingError` is raised before any dispatch call.

**Verification:** all four commands green; the new test fails if `model_validate` is
reverted to `model_copy`.

---

## Step 8 — `TRD-H05` (HIGH): register or remove the report evidence schema identifier

**Recommendation:** Register it — the report is a real cross-domain output to Analytics,
Portfolio, and UI/API.

**Implementation:**

1. Add a row to `app/services/trading/README.md` §1 "Owned by this domain":
   `ExecutionEvidenceReport` · `v1` · counterparty Analytics; Portfolio; UI/API · purpose
   and failure behaviour, carrying `contract_version="v1"` and
   `schema_id="trading.execution_evidence_report.v1"`.
2. Add the matching row to `docs/PROJECT.md` §5 with status `Completed`, owner
   `Trading`, producer `Trading`, consumers `Analytics, Portfolio, UI/API`.
3. Reference `TRADING_CONTRACT_VERSION` (from Step 2) at
   `reporting/evidence.py:71` instead of the hard-coded literal.
4. Add a contract test asserting the emitted `schema_id` and `contract_version`.

**Verification:** the identifier resolves to a registry row in both documents; the
contract test passes.

---

## Step 9 — `TRD-B02` (BLOCKING): reconcile `docs/PROJECT.md` with the completed domain

Do this **last**, so the registry reflects the corrected state rather than the state at
review time.

**Implementation:** In `docs/PROJECT.md`, change status `Missing` → `Completed` on:

* `:765` `OrderIntent v1`
* `:766` `TradeRecord` / `ExecutionReceipt v1`
* `:767` `OperationalEvent v1`
* `:785` `PortfolioRebalanceExecutionRequest v1`
* `:841` Trading orders/fills/execution-state/idempotency/`TradeRecord` persisted state
* `:869` `EXECUTION_ROUTE`
* `:870` `ALLOW_LIVE_MUTATIONS`

Also update `:936` — replace "Trading mutation workflow remains pending" with the
current state, and add the new `ExecutionEvidenceReport v1` row from Step 8.

Leave `SYS-WF-001/002/005/006/008` (`:401–408`) as `Missing` — system-level assembly is a
later phase and out of this scope.

Then append one entry to `docs/CHANGELOG.md` under `Added` recording the corrections
made in Steps 1–9 (three sentences maximum, per the file's own instruction).

**Verification:** every Trading row in `docs/PROJECT.md` matches the status in
`app/services/trading/README.md` §1; no other domain's row was touched.

---

## Step 10 — Medium and low findings

Apply these together after Steps 1–9 are green.

* **`TRD-M01`** — `app/services/trading/README.md` §4.2 Files table: change
  "`TradingStateStore` and its five public operations" to six, and add an `FR-TRD-*` row
  for `TradingStateStore.load_report_evidence` (`state/stores.py:93`) with its own unit
  test (`tests/trading/unit/state/test_stores.py`) and usage test
  (`tests/trading/usage/test_usage_state.py`).
* **`TRD-M02`** — `app/services/trading/actions/dependencies.py:165`: remove
  `"SymbolCapability"` from `__all__` (it stays importable for typing without being a
  declared public export).
* **`TRD-M03`** — `app/services/trading/README.md:849`: remove "or route-incompatible"
  from the `FR-TRD-056` Raises cell, or implement the check by adding a `route` field to
  `TradingDependencies` and validating connection/adapter/dispatch presence against it in
  `__post_init__` (`dependencies.py:133`). If you implement it, add the matching unit test.
* **`TRD-M04`** — `app/services/trading/README.md:682`: remove "persistence write" from
  the `FR-TRD-031` Side Effects cell; note that persistence is performed by the caller.
* **`TRD-M05`** — `app/services/trading/routing/dispatcher.py:327`: replace
  `f"timeout-{observed_at.isoformat()}"` with deterministic material, e.g.
  `f"timeout-{intent.client_order_id}-{intent.idempotency_material_version}"`. Add a
  replay test asserting two identical timeouts produce an identical `receipt_id`.
* **`TRD-M06`** — reconcile every Files-table dependency cell in README §4 against actual
  imports. Highest-priority corrections: `contracts/errors.py` and `contracts/registry.py`
  (declare `pydantic`), `reporting/evidence.py` (remove `pydantic`), `live/config.py`
  (remove `pydantic-settings` and "Data session provider"), `routing/capabilities.py`
  (remove `BrokerFeatureFlags` and Simulation contracts, or import and use them).
  Add the missing stdlib entries across the ~20 affected rows.
* **`TRD-L01`** — move `_authority_id` and `_require_action` out of
  `actions/orders.py` into a shared internal module (e.g.
  `app/services/trading/actions/_shared.py`), or rename them without the leading
  underscore, and update `actions/emergency.py:7–11`.
* **`TRD-L02`** — source `BROKER_OPERATION_TIMEOUT_SECONDS`
  (`routing/capabilities.py:10`) from the validated configuration added in Step 2,
  keeping `10` as the ratified default.
* **`TRD-L03`** — report as a `Proposed Decision`: whether `FR-TRD-031`'s signature
  should gain an injected clock so `dispatcher.py:158` and `:323` stop using
  `datetime.now(UTC)`. Do not change the documented signature without approval.
* **`TRD-L04`** — align the `max_children` comparison in
  `actions/emergency.py:131` and `:210` to one definition, and pin it with a unit test.
* **`TRD-L05`** — report as a `Proposed Decision`: whether Trading's pytest-style usage
  examples should be converted to standalone runnable scripts to match the Strategy
  convention recorded in `docs/CHANGELOG.md`. Do not convert without approval.
* **`TRD-L06`** — add an explicit exclusion note near README:935 recording that
  `FR-TRD-011` was retired with `CAP-TRD-022` (no raw signal translator), or renumber.

**Verification:** all four commands green; the README reference resolver reports zero
unresolved references; `__all__` matches the Files-table key exports for every module.

---

## Final report required from you

Per AGENTS.md §3, close with: files changed, decisions and risks updated, commands run,
validation results, and the rollback path, using positive checklist wording
(`[X] Scope followed`). Update the README §7 checklist entries with accurate file:line
evidence.

Run `detect-secrets scan --baseline .secrets.baseline` before committing — the Trading
implementation is currently untracked in git, so that hook has never run against it.

**When you are finished, the completion review must be re-run from scratch. Do not mark
the domain `Completed` on the basis of this correction pass alone.**

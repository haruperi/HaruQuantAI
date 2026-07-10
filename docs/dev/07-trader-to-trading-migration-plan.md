# Phase 07 Trader → Trading — Brownfield Migration and Deletion Plan

Status: proposed
Owner: Haruperi
Target: delete `app/services/trader/` with zero functional regression

---

## 0. Brownfield Objective

`app/services/trading/` was written as the successor to `app/services/trader/`.
An audit of both trees shows `trading` is a strict superset of `trader` in
every area except two, and those two are the only things that make `trader`
able to place an order.

This plan closes those two gaps, migrates the usage example, folds the
`trader` README into the `trading` README, deletes the `trader` tests that
cover only `trader`, and then deletes `app/services/trader/`.

Out of scope: `app/services/live/`. That is the next refactor step. This plan
does not touch it, and does not depend on it.

---

## 1. Repository Baseline Audit

### 1.1 Consumers

Neither package has a single non-test importer anywhere under `app/`. Every
reference to `app.services.trader` lives in tests or the usage example:

| File                                                                 | Nature of reference         |
| -------------------------------------------------------------------- | --------------------------- |
| `tests/unit/app/services/trader/test_trader.py`                    | Real tests, 237 asserts     |
| `tests/unit/app/services/trader/test_trader_extra.py`              | Vacuous, 0 asserts          |
| `tests/unit/test_massive_others_extra.py`                          | Vacuous trader stanza       |
| `tests/unit/app/services/live/test_live_risk_sim_pybots_extra2.py` | Vacuous trader stanza       |
| `tests/usage/07_trading.py`                                        | Live usage, examples 23–30 |

This means deletion breaks no production code path. It breaks tests and the
usage example only.

### 1.2 Coverage matrix — `trader` surface against `trading`

| `trader` module         | `trading` equivalent                                                     | Status                                                   |
| ------------------------- | -------------------------------------------------------------------------- | -------------------------------------------------------- |
| `info/account.py`       | `info/account.py`                                                        | Covered                                                  |
| `info/symbol.py`        | `info/symbol.py`                                                         | Covered                                                  |
| `info/terminal.py`      | `info/terminal.py`                                                       | Covered                                                  |
| `info/order.py`         | `info/order.py` + `_ticket.TicketInfoFacade`                           | Covered via inheritance                                  |
| `info/position.py`      | `info/position.py` + `_ticket.TicketInfoFacade`                        | Covered via inheritance                                  |
| `info/deal.py`          | `info/deal.py` + `_ticket.TicketInfoFacade`                            | Covered via inheritance                                  |
| `info/history_order.py` | `info/history_order.py` → `OrderInfo` → `TicketInfoFacade`         | Covered via inheritance                                  |
| `validation.py`         | `actions/validation.py`                                                  | Strict superset                                          |
| `rate_limiter.py`       | `execution/rate_limiter.py`                                              | Covered                                                  |
| `idempotency.py`        | `state/idempotency.py`                                                   | Covered, plus durable store                              |
| `reconciliation.py`     | `reconciliation/service.py`                                              | Covered                                                  |
| `reporting.py`          | `execution/reporting.py`                                                 | Covered, plus execution-quality events                   |
| `result.py`             | `execution/response_classifier.py` + `contracts.NormalizedTradeResult` | Covered                                                  |
| `readiness.py`          | `gates/readiness.py`                                                     | Covered, re-shaped to evidence-in                        |
| `concurrency.py`        | `runtime/coordination.py`                                                | Covered, lock/release instead of context manager         |
| **`store.py`**    | `state/ports.py::TradeStore`                                             | **Protocol only — no concrete implementation**    |
| **`trade.py`**    | `actions/*`                                                              | **Packaging only — never dispatches to a broker** |

Fifteen of seventeen modules are already covered. The plan is about the two
bold rows.

### 1.3 The dispatch gap, verified empirically

Every mutation in `trading` funnels through `dispatch_or_package`
(`actions/_common.py:162`), which delegates to an injected `LiveGatePipeline`.
No class implementing that protocol exists in the repository. `LiveGatePipeline`
is a `Protocol` whose `evaluate` raises `NotImplementedError`.

A fully-valid live buy — `route=LIVE`, `promotion_stage=FULL_LIVE`,
`mutation_capability=FULL_LIVE`, valid quote and session evidence — returns:

```
status          : accepted
side_effect_mode: packaged_only
message         : Trading request packaged; live gate pipeline not yet engaged.
data keys       : ['dispatch_payload']
```

It builds a payload and returns it. Nothing is sent. By contrast
`trader/trade.py:370` calls `broker.trade(sanitized_req)` for real.

Grep confirms the boundary: the only broker access in the whole `trading` tree
is `info/_common.py:29`, the read-only info layer.

### 1.4 The 16 gates

`gates/_common.py::GateName` defines the canonical live pipeline. Current
evaluator availability:

| #  | Gate                         | Evaluator                                                  | Status                          |
| -- | ---------------------------- | ---------------------------------------------------------- | ------------------------------- |
| 1  | `LOCAL_SCHEMA_VALIDATION`  | `actions/validation.validate_order_request`              | Exists                          |
| 2  | `COMPLIANCE`               | `gates/pipeline.evaluate_compliance_gate`                | Exists                          |
| 3  | `PROMOTION_STAGE`          | `promotion/ladder.evaluate_promotion_stage_gate`         | Exists                          |
| 4  | `SESSION_STATUS`           | `runtime/session_manager.SessionManager`                 | Exists, needs adapter           |
| 5  | `KILL_SWITCH`              | `gates/kill_switch.evaluate_kill_switches`               | Exists                          |
| 6  | `OPERATOR_APPROVAL`        | `gates/approval.validate_operator_approval`              | Exists, raises — needs adapter |
| 7  | `RISK_DECISION`            | —                                                         | **None. See BF-TRD-004**  |
| 8  | `MARKET_TURBULENCE`        | `gates/pipeline.MarketTurbulenceMonitor.observe`         | Exists                          |
| 9  | `BROKER_READINESS`         | `gates/readiness.validate_broker_readiness`              | Exists, raises — needs adapter |
| 10 | `CLOCK_DRIFT`              | `gates/readiness.validate_clock_drift`                   | Exists, raises — needs adapter |
| 11 | `IDEMPOTENCY`              | `state/idempotency.JsonlIdempotencyStore.reserve`        | Exists, needs adapter           |
| 12 | `CONCURRENCY_LEASE`        | `runtime/coordination.ConcurrencyLockManager`            | Exists, needs adapter           |
| 13 | `RECONCILIATION_AUTHORITY` | `reconciliation.evaluate_reconciliation_authority_gate`  | Exists                          |
| 14 | `AUDIT_PRE_RECORD`         | `gates/audit_and_compensation.record_pre_mutation_audit` | Exists                          |
| 15 | `ADAPTER_PERMISSION`       | `gates/pipeline.evaluate_adapter_permission_gate`        | Exists                          |
| 16 | `DISPATCH`                 | —                                                         | **None. See BF-TRD-003**  |

`run_gate_pipeline` short-circuits on the first blocked gate, and
`evaluate_seam_gate(gate, None)` blocks with `LIVE_GATE_FAILED`. Therefore
**every one of the 16 needs a real evaluator or the pipeline can never
complete**, and `trading` can never place an order.

Several existing helpers *raise* on failure rather than returning a
`GateStepResult`. They need thin adapters, not rewrites.

---

## 2. Decisions Taken

### D-1 — RISK_DECISION gets a parity passthrough

`trader` performs no risk checks whatsoever before dispatching. Wiring
`app/services/risk` into gate 7 would be a strict safety improvement, but it
couples this deletion to a second, larger integration (`risk` exposes ~400
public symbols and its own snapshot contracts).

Decision: ship `passthrough_risk_evaluator()` — passes the gate, emits a
`WARNING` on every live evaluation, and carries a docstring pointing at
`app/services/risk`. **Net risk posture after this plan is identical to
`trader` today**, so the deletion regresses nothing. Wiring real risk is a
follow-up with its own plan.

This is the single most important thing for a reviewer to understand: the
passthrough is not a new hole, it is the existing hole, made visible and
greppable.

### D-2 — TradeStore ships in-memory and durable

`InMemoryTradeStore` for tests and non-live routes, plus `JsonlTradeStore`
mirroring the existing `JsonlIdempotencyStore` / `AppendOnlyEventJournal`
pattern. The durable store lets the readiness gate assert `stores_durable=True`
honestly, and survives restart — which `trader`'s in-memory store never did.

---

## 3. Migration Actions

### BF-TRD-001 — Baseline characterization

Lock in current behavior before changing anything.

- Run `tests/unit/app/services/trader/test_trader.py` and record the pass set.
- Extract the behavioral contract of `Trade._send_request` as an explicit
  ordered list: kill-switch check → shutdown check → in-flight increment →
  idempotency → startup reconciliation gate → concurrency lock → readiness →
  validation → rate limit → broker dispatch with 5s timeout → timeout-triggers-
  forced-reconciliation → store update → idempotency completion.
- Map each step onto its `GateName` from §1.4. This mapping is the acceptance
  criterion for BF-TRD-003.

Exit: a written step-to-gate table, committed alongside this plan.

### BF-TRD-002 — Concrete `TradeStore`

New file `app/services/trading/state/trade_store.py`.

- `InMemoryTradeStore` implementing all eight `TradeStore` protocol methods:
  `save_order_state`, `save_position_state`, `record_execution_fill`,
  `apply_corporate_action`, `get_order_state`, `get_position_state`,
  `list_order_states`, `list_position_states`.
- `JsonlTradeStore` with the same surface, following the file/clock injection
  pattern of `JsonlIdempotencyStore`.
- Both must honor `expected_version` optimistic concurrency and maintain the
  `Decimal` VWAP and remaining-volume projections the protocol docstring
  requires. Route isolation (`route=` namespacing) is mandatory: non-live
  routes must never share storage with live.
- Export both from `state/__init__.py` and `trading/__init__.py`.

Tests: `tests/services/trading/state/test_trade_store.py`. Cover version
conflict, route isolation, VWAP accumulation across partial fills, and
JSONL round-trip after simulated restart.

Exit: `finalize_dispatch_outcome` can be called with a real store.

### BF-TRD-003 — `LiveGatePipeline` implementation and broker dispatch

This is the core of the plan. New file
`app/services/trading/gates/live_pipeline.py`.

- `class LiveGatePipelineImpl` satisfying the `LiveGatePipeline` protocol, i.e.
  `evaluate(request: TradingRequestEnvelope) -> TradingResponseEnvelope`.
- Constructor takes every collaborator by injection — no module-level broker
  import, preserving the package's "no provider SDKs" rule stated in
  `trading/README.md`. The broker call arrives as an injected
  `dispatch_callable`.
- Assemble all 16 gates in `GateName` order and hand them to the existing
  `run_gate_pipeline`. Do not reimplement short-circuit or deadline logic.
- Write thin `*_step` adapters for the gates whose helpers raise rather than
  return `GateStepResult` (6, 9, 10) and for those needing a live collaborator
  (4, 11, 12).
- Gate 16 `DISPATCH` performs the broker call through the injected callable,
  wrapped by `ExecutionCoordinator.dispatch_async`, with the 5-second timeout
  from BF-TRD-001. On timeout, classify as unknown outcome and trigger forced
  reconciliation — matching `trader/trade.py:377-413`.
- On completion call the existing `finalize_dispatch_outcome` with the
  BF-TRD-002 store.

New file `app/services/trading/execution/broker_dispatch.py` holding the only
function permitted to touch `brokers.router`, so the boundary stays one file
wide and greppable:

```python
def build_broker_dispatch_callable(payload: JsonObject) -> Callable[[], NormalizedTradeResult]:
    """Bind a dispatch payload to the active broker's trade() entrypoint."""
```

Tests: `tests/services/trading/gates/test_live_pipeline.py`.

- Each gate blocks in isolation and short-circuits the rest as
  `diagnostic_skipped`.
- Happy path reaches `DISPATCH` and returns a non-`packaged_only`
  `side_effect_mode`.
- Timeout path produces an unknown outcome and calls reconciliation.
- A fake broker asserts payload shape; no real broker in unit tests.

Exit criterion, stated as a concrete assertion: re-running the §1.3 probe
returns `side_effect_mode != packaged_only` and the fake broker records exactly
one `trade()` call.

### BF-TRD-004 — RISK_DECISION passthrough

Per D-1. In `gates/live_pipeline.py`:

- `passthrough_risk_evaluator() -> GateStepResult` returning a passed step,
  logging `WARNING` with a stable message containing the literal string
  `RISK_DECISION passthrough` for grepping and alerting.
- The pipeline constructor takes `risk_evaluator: Callable[[], GateStepResult]`
  with **no default**, forcing every caller to name its choice at the call site.
  Passing `passthrough_risk_evaluator` is an explicit, visible act.

Tests: assert the warning fires; assert the constructor rejects omission.

Exit: gate 7 passes, and `grep -r "RISK_DECISION passthrough"` locates every
site that opted into it.

### BF-TRD-005 — Kill switch and shutdown behavioral parity

`trader.Trade.set_kill_switch(flatten_positions=True)` genuinely cancels orders
and closes positions through the broker (`trade.py:973`). `trading`'s
`trigger_global_kill_switch` and `flatten_account` only package the intent.

- Once BF-TRD-003 lands, these package into a pipeline that dispatches, so the
  behavior returns for free — but only when a pipeline is injected. Add an
  integration test proving `flatten_account` with an injected live pipeline
  actually issues close dispatches.
- Fix `controls.shutdown` (`controls.py:377`), which currently hardcodes
  `reconciliation_triggered=True` without reconciling anything. It must either
  invoke reconciliation or report what actually happened. A caller trusting that
  field today believes state was reconciled when it was not.
- Port `trader`'s in-flight drain loop (`trade.py:1034-1041`) onto
  `ExecutionCoordinator.in_flight`, which already exposes `is_drained()`.

Tests: extend `tests/services/trading/actions/test_controls.py`.

Exit: shutdown drains, and `reconciliation_triggered` reflects reality.

### BF-TRD-006 — Delete trader-only tests

Delete outright:

- `tests/unit/app/services/trader/test_trader_extra.py` — 16 `try/except ImportError`
  blocks importing classes that do not exist (`ConcurrencyManager`,
  `OrderValidator`, `TraderStore`, `TradeValidator`, `ReadinessManager`,
  `IdempotencyManager`, `ReconciliationManager`, `Reporter`, `TradeResult`).
  Zero asserts. It has never tested anything; it inflates coverage by importing
  modules and swallowing the failure.
- `tests/unit/app/services/trader/` package directory, including
  `test_trader.py`, once BF-TRD-003 tests demonstrably cover the same
  behaviors. **Do not delete `test_trader.py` before that.** Its 237 asserts
  are the specification for the `_send_request` sequence.

Edit, do not delete:

- `tests/unit/test_massive_others_extra.py` — remove only the `# Trader` stanza
  (the `OrderValidator` import block). The file covers other modules.
- `tests/unit/app/services/live/test_live_risk_sim_pybots_extra2.py` — remove
  only the `trader/validation.py` stanza importing `TradeValidator`.

Exit: `grep -rn "app.services.trader" tests/` returns nothing.

Note: all three vacuous stanzas import names that do not exist in `trader`.
Removing them changes no test outcome. Worth a separate look at whether this
`try/except`-around-a-bad-import pattern appears elsewhere in the suite — it
reports coverage for code it never executes.

### BF-TRD-007 — Migrate `tests/usage/07_trading.py`

The example already imports heavily from `trading`; only examples 23–30 use
`Trade`. Requirement: the script must still run end-to-end and still place,
modify, and close real orders against the active broker.

Replace the module-level `from app.services.trader import Trade` and rewrite:

| Example            | Current                           | Replacement                                                  |
| ------------------ | --------------------------------- | ------------------------------------------------------------ |
| 23 open position   | `trade.buy(...)`                | `actions.orders.buy(...)` with an injected live pipeline   |
| 25 modify position | `trade.position_modify(...)`    | `actions.positions.position_modify(...)`                   |
| 26 partial close   | `trade._send_request(raw_dict)` | `actions.positions.position_close(volume=Decimal("0.01"))` |
| 27 close position  | `trade.position_close(...)`     | `actions.positions.position_close(...)`                    |
| 28 pending order   | `trade.buy_limit(...)`          | `actions.orders.buy_limit(...)`                            |
| 29 modify pending  | `trade.order_modify(...)`       | `actions.orders.order_modify(...)`                         |
| 30 delete pending  | `trade.order_delete(...)`       | `actions.orders.order_delete(...)`                         |

Two notes:

- Example 26 currently reaches into the private `trade._send_request` with a
  hand-built request dict, because `trader` has no partial-close API. `trading`'s
  `position_close` takes `volume: Decimal | None` for exactly this. The
  migration removes a private-API call — a genuine improvement, not just a port.
- Examples 23–30 need a real `LiveGatePipelineImpl` wired to the live broker,
  plus an `OrderValidationContext` built from `SymbolInfo`/`AccountInfo`. Add a
  single `build_usage_pipeline()` helper near the top of the file and reuse it
  across all seven, rather than reconstructing dependencies per example.
- Result accessors (`trade.result_retcode()`, `result_deal()`, `result_price()`,
  `result_comment()`) become fields on the returned `TradingResponseEnvelope`
  and the `NormalizedTradeResult` it carries. Print sites need updating.

Exit: `python tests/usage/07_trading.py` runs all 31 examples with the same
observable broker effects as before.

### BF-TRD-008 — Merge READMEs

Fold `app/services/trader/README.md` (181 lines) into
`app/services/trading/README.md` (262 lines). The `trader` README carries
operational content the `trading` README lacks.

Carry over, re-anchored to `trading` paths and APIs:

- §2 Execution Lifecycle → new `## Execution Lifecycle` section in `trading`,
  rewritten against the 16-gate pipeline rather than `_send_request`.
- §4 Resilience & Operational Safety → merge into `trading`'s existing safety
  prose. The four subsections (Startup Reconciliation Gate, Concurrency Queue
  Locks, Global Kill Switch, Graceful Shutdown Sequence, Broker Synchronous
  Timeouts) all have `trading` equivalents after BF-TRD-003/005.
- §5 Code Usage Examples → new `## Usage` section, rewritten to the
  `actions.orders.buy(...)` form. The existing `Trade()` snippets are dead on
  arrival and must not be copied verbatim.
- §6 MQL5 Emulation Wrappers → merge into `trading`'s `info/` description; this
  is the mapping table for the facades and it is worth keeping.

Drop, do not carry:

- §1 System Topology and §3 Component Directory — superseded by `trading`'s
  more detailed `## Implemented Surface`.
- §7 Verification & Testing — points at deleted test paths.

Delete `## Pending Broker Connection Integration` (line 260) from the `trading`
README. After BF-TRD-003 it is false. Line 262's claim that "wiring a real
broker adapter/executor into the session manager and coordinator remains future
work" must go with it.

Exit: `app/services/trader/README.md` is gone; no `trading` README line claims
broker wiring is pending.

### BF-TRD-009 — Delete `app/services/trader/`

Preconditions, all of which must hold:

1. `grep -rn "app.services.trader" --include=*.py .` returns nothing.
2. `grep -rn "services/trader" docs/ app/` returns nothing outside
   `docs/audit/workflows.md` (which is regenerated separately — see §5).
3. The §1.3 probe against `trading` returns a non-`packaged_only` result.
4. `tests/usage/07_trading.py` runs clean end-to-end.
5. Full test suite green.

Then `git rm -r app/services/trader/`.

Exit: the tree builds, tests pass, and the usage example still trades.

---

## 4. Sequencing

BF-TRD-001 gates everything — it produces the acceptance table.

```
001 baseline
 ├── 002 TradeStore ──┐
 └── 004 risk passthru┤
                      ├── 003 LiveGatePipeline + dispatch
                      │    ├── 005 kill switch / shutdown parity
                      │    ├── 006 delete trader-only tests
                      │    └── 007 migrate usage example
                      │         └── 008 merge READMEs
                      │              └── 009 delete trader/
```

002 and 004 are independent and can land in parallel. 003 needs both. Nothing
after 003 can start until its exit criterion — the probe returning
non-`packaged_only` — is demonstrated, not assumed.

006 has an ordering trap: `test_trader_extra.py` and the two vacuous stanzas can
be deleted immediately, at any point. `test_trader.py` must survive until
BF-TRD-003's tests replace its coverage.

---

## 5. Follow-ups, explicitly out of scope

1. **Regenerate `docs/audit/workflows.md`.** It was written pre-refactor and
   describes three parallel live stacks. Regenerate after this plan lands, not
   during.
2. **Wire `app/services/risk` into gate 7**, replacing the BF-TRD-004
   passthrough. Until then, live trading has no pre-trade risk gate — the same
   as today under `trader`.
3. **Retire `app/services/live/`.** The next refactor step. Independent of this
   one.
4. **Audit the `try/except`-around-import test pattern** flagged in BF-TRD-006.

---

## 6. Risk Register

| Risk                                                               | Likelihood | Impact   | Mitigation                                                                                                |
| ------------------------------------------------------------------ | ---------- | -------- | --------------------------------------------------------------------------------------------------------- |
| Gate adapters silently invert a fail-closed helper into a pass     | Medium     | Critical | BF-TRD-003 tests assert each gate blocks in isolation                                                     |
| `test_trader.py` deleted before its coverage is replaced         | Medium     | High     | Explicit ordering constraint in §4                                                                       |
| Usage example 23–30 mutate a real account during a test run       | Low        | Critical | Unchanged from today; example already trades live. Confirm broker points at a demo account before running |
| `passthrough_risk_evaluator` outlives this plan and is forgotten | High       | Medium   | No default in constructor; WARNING on every call; stable grep string                                      |
| `JsonlTradeStore` write latency enters the dispatch hot path     | Medium     | Medium   | Benchmark in BF-TRD-002;`finalize_dispatch_outcome` runs post-response, off the request path            |

---

## Appendix A — BF-TRD-001 Baseline Characterization

Baseline: `tests/unit/app/services/trader/test_trader.py` — **24 passed**.

### A.1 `Trade._send_request` ordered contract → `GateName`

Extracted from `app/services/trader/trade.py:180-458`.

| #  | `_send_request` step             | Source lines | `GateName`                       |
| -- | ---------------------------------- | ------------ | ---------------------------------- |
| 1  | Kill-switch block                  | 189-193      | `KILL_SWITCH` (5)                |
| 2  | Shutdown block                     | 195-200      | `SESSION_STATUS` (4)             |
| 3  | In-flight increment                | 201          | `ExecutionCoordinator.in_flight` |
| 4  | Resolve account/symbol/params      | 204-232      | `LOCAL_SCHEMA_VALIDATION` (1)    |
| 5  | Idempotency key + duplicate check  | 234-262      | `IDEMPOTENCY` (11)               |
| 6  | Startup reconciliation gate        | 264-304      | `RECONCILIATION_AUTHORITY` (13)  |
| 7  | Sequential concurrency lock        | 307          | `CONCURRENCY_LEASE` (12)         |
| 8  | Register in-progress               | 309          | `IDEMPOTENCY` (11)               |
| 9  | Execution readiness check          | 311-327      | `BROKER_READINESS` (9)           |
| 10 | Validation + decimal normalization | 329-351      | `LOCAL_SCHEMA_VALIDATION` (1)    |
| 11 | Rate-limiter acquire               | 354-366      | `ADAPTER_PERMISSION` (15)        |
| 12 | Broker dispatch, 5s timeout        | 368-376      | `DISPATCH` (16)                  |
| 13 | Timeout → forced reconciliation   | 377-413      | `DISPATCH` post-handling         |
| 14 | TradeStore update                  | 423-451      | `finalize_dispatch_outcome`      |
| 15 | Idempotency completion             | 454          | `finalize_dispatch_outcome`      |
| 16 | In-flight decrement                | 456-458      | `ExecutionCoordinator.in_flight` |

### A.2 Gates with no `trader` equivalent

These seven are new safety surface `trading` adds. They are not regressions and
need no baseline: `COMPLIANCE` (2), `PROMOTION_STAGE` (3), `OPERATOR_APPROVAL`
(6), `RISK_DECISION` (7), `MARKET_TURBULENCE` (8), `CLOCK_DRIFT` (10),
`AUDIT_PRE_RECORD` (14).

`RISK_DECISION` is the one covered by the D-1 passthrough.

### A.3 Retcode success set

`trader` treats `retcode in (10009, 10008, 0)` as success (`trade.py:262`, `424`).
`LiveGatePipelineImpl` must preserve exactly this set.

### A.4 Acceptance criterion for BF-TRD-003

Every row in A.1 must have a corresponding assertion in
`tests/services/trading/gates/test_live_pipeline.py`.

---

## Appendix B — Execution Record

Status: **complete**. `app/services/trader/` is deleted.

### B.1 Work items

| Item       | Outcome                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        |
| ---------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| BF-TRD-001 | Baseline: 24 tests passing; step→gate table in Appendix A                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     |
| BF-TRD-002 | `state/trade_store.py`: `InMemoryTradeStore` + `JsonlTradeStore`, 41 tests<br />**`state/trade_store.py`** adds `InMemoryTradeStore` and `JsonlTradeStore`, per your choice. Both enforce optimistic concurrency, dedupe fills on `broker_event_id`, and namespace by `(route, tenant_id)` so sim never shares storage with live.                                                                                                                                                                                                                                                                                                                                                                                                                                                        |
| BF-TRD-003 | `gates/live_pipeline.py` + `execution/broker_dispatch.py`, 47 tests.<br />**`gates/live_pipeline.py`** implements `LiveGatePipelineImpl`, the concrete `LiveGatePipeline` that never existed. It assembles all sixteen gates in `GateName` order, hands them to the existing `run_gate_pipeline` (I reimplemented none of its short-circuit or deadline logic), and dispatches to the broker at gate 16 under a five-second timeout. A timeout becomes an unknown outcome and forces reconciliation, exactly as `trader` did. The broker call itself lives in  **`execution/broker_dispatch.py`** , the only file in the package permitted to touch the router — `grep -rl "brokers.router" app/services/trading` returns it and the read-only `info/` layer, nothing else. |
| BF-TRD-004 | `passthrough_risk_evaluator`, no constructor default                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         |
| BF-TRD-005 | `shutdown` reports reality; `InFlightRequestCounter.wait_drained` added                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    |
| BF-TRD-006 | `tests/unit/app/services/trader/` deleted; 2 vacuous stanzas removed                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         |
| BF-TRD-007 | Usage examples 23–30 migrated; verified against a fake broker                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
| BF-TRD-008 | READMEs merged;`trader/README.md` deleted                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    |
| BF-TRD-009 | `app/services/trader/` deleted                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               |

### B.2 Exit criteria, as measured

- Dispatch probe: `side_effect_mode = broker_mutation_confirmed`, exactly one
  `trade()` call. Previously `packaged_only`, zero calls.
- Usage examples 23–30 against a fake broker: 7 dispatches, 7 expected.
- Full suite: 1743 passed / 2 failed. Baseline before this work: 1665 passed /
  2 failed. **Same two pre-existing failures**
  (`test_massive_others_extra.py::test_others_no_pandas` and
  `test_massive_pybots_extra.py::test_pybots_no_pandas`, both failing on an
  `app.services.optimization.helpers._evaluate_candidate` import unrelated to
  this migration). No new failures.
- `grep -rn "app\.services\.trader\b" --include=*.py .` → no results.

### B.3 Defects found and fixed en route

These were not in the plan. Each was found by a test or probe, not by reading.

1. **`_flatten` reported a hardcoded `PACKAGED_ONLY`** regardless of what its
   children did (`actions/emergency.py`). Its children *do* dispatch through
   `dispatch_or_package`, so an emergency flatten that actually cancelled orders
   and closed positions reported that nothing had happened — and one that was
   fully blocked reported `ACCEPTED`. Both directions wrong, in the emergency
   path. Now derives status, side effect, retry safety, and message from the
   children by explicit severity ordering.
2. **`controls.shutdown` hardcoded `reconciliation_triggered=True`** without
   reconciling. A caller trusting that field believed state was reconciled when
   it was not. Now takes `reconcile` and `drain` callbacks and reports what
   actually ran. The pre-existing test asserting `is True` encoded the bug and
   was corrected.
3. **`JsonlIdempotencyStore` did not satisfy the `IdempotencyStore` port.**
   `runtime_checkable` only checks method *names*, so `isinstance` passed while
   `complete()` lacked the `completed_at` parameter `finalize_dispatch_outcome`
   passes. Would have raised `TypeError` on the first live dispatch. Fixed
   additively.
4. **Approval hash was computed over the wrong payload level.**
   `actions/orders.py` nests the validated order under `payload["intent"]`; the
   first draft of `_canonical_request_hash` read the flat keys, hashing empty
   strings for every order. An approval token issued for a 0.01-lot buy would
   have validated a 100-lot sell. Caught by the exit-criterion probe.
5. **`Decimal(str(None))` raised `ConversionSyntax`** in the adapter-permission
   gate. A full `position_close` packages `volume=None` and a market order
   packages `price=None`; absence is not zero. Caught by the usage-example run.
6. **Gate 1 rejected ticket-addressed closes.** `position_close` by ticket and
   account-wide flattens legitimately package `symbol=None`. The symbol now
   resolves through envelope → payload → quote → `GLOBAL` (matching `trader`'s
   fallback), so an account-wide action takes one coherent concurrency lease
   instead of locking on an empty string. `SUBMIT_ORDER` still requires a symbol.

### B.4 Behavior differences from `trader` (intentional)

- **Price collar.** `trading` enforces a pending-order price collar
  (`price_collar_bps`, default 50) that `trader` did not. Usage example 28
  places a buy limit ~180 bps out, so the example sets the collar to 300 bps
  explicitly. Tune per instrument in production.
- **Fail-closed policy matrix.** `PolicyMatrixEntry.requires_approval` defaults
  to `True`, and an action with no matrix entry blocks with
  `TRADING_POLICY_UNDEFINED`. `trader` had neither concept.
- **One live session per scope.** `SessionManager` rejects a second live session
  for the same scope. Callers hold one session per process.

### B.5 New error codes registered

Added to `APPROVED_ERROR_CODES` with matching `ERROR_MESSAGES` entries:
`LIVE_STATE_VERSION_CONFLICT`, `LIVE_BROKER_REJECTED`.
(`LIVE_UNKNOWN_OUTCOME` already existed.)

### B.6 Outstanding

Unchanged from §5. The risk gate is a passthrough: **live trading still has no
pre-trade risk check, exactly as under `trader`.** `grep -rn "RISK_DECISION passthrough"` locates every opted-in call site.

Gate 7 ships as `passthrough_risk_evaluator`. **Live trading has no pre-trade risk check** — identical to `trader`, so nothing regressed, but it is now the only unimplemented safety gate in an otherwise complete pipeline. I made it as loud as I could: no constructor default, so every call site names it; a WARNING on every live evaluation containing the literal string `RISK_DECISION passthrough`. I've queued a task to wire `app/services/risk` into it.

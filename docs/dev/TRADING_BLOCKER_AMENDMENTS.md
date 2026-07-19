# Trading Blockers — Owner-Ready Amendment Proposals

> **Status:** `Executed` — approved and applied 2026-07-19. D1–D3 were ratified; D2 was
> implemented as a validated `Mapping[str, Decimal]` rather than a `StalenessPolicy`
> model, and its evidence classes were later extended from two to three
> (`route_snapshot`, `risk_decision`, `kill_switch`). See `docs/CHANGELOG.md`.
> Retained as the decision record for this correction pass, not as an open proposal.
> **Scope:** the four BLOCKING findings (`TRD-B01`–`TRD-B04`) from
> `docs/dev/TRADING_REVIEW_2026-07-19.md`. HIGH/MEDIUM/LOW findings are out of scope
> for this pass and are listed in §6 as deferred.
> **Process:** AGENTS.md §3 (Dry Run → approval gate → surgical change → final report)
> and Trading README §8 (README amended before code).

---

## 0. Decisions the owner must ratify

Three of these amendments change specification text, not just code. They are called out
first because approving this document approves these decisions.

| # | Decision | Proposal | Alternative if rejected |
|---|---|---|---|
| **D1** | `assess_execution_readiness` and `reserve_idempotency` currently have no way to receive a configured bound. | Add one explicit parameter to each documented signature (§3.3, §3.2). | Smuggle bounds through the existing `action_policy` / request mappings — rejected: hides configuration inside evidence and defeats the "declared per profile" requirement. |
| **D2** | `MAX_STALENESS_SECONDS` is specified "per evidence class" but no such type exists. | Add a new frozen `StalenessPolicy` contract with four required positive `Decimal` fields, exported from `validation/`, traced by a new `FR-TRD-066` (§3.3). | Single scalar bound applied to all four evidence classes — rejected: contradicts README:634 "per evidence class". |
| **D3** | `CONCURRENCY_LOCK_TIMEOUT_SECONDS` needs a lock-age reference; `IdempotencyReservation` records only `expires_at`. | Add a required `reserved_at: datetime` field to `IdempotencyReservation` (`FR-TRD-057`), so stale-lock age is measurable (§3.4). | Treat `expires_at` as the lock bound — rejected: conflates the retention window with the much shorter concurrency bound; a stale lock would then hold for the full retention period. |

`FR-TRD-011` is currently unused (retired with `CAP-TRD-022`). **This pass does not
reuse it** — reusing a retired ID would make history ambiguous. New requirements take
`FR-TRD-066` and `FR-TRD-067`.

---

## 1. `TRD-B01` — Redaction must be performed, not asserted

### Amendment to `app/services/trading/README.md`

**Add to §4.1 Rules (currently README:560), after the existing sentence:**

> **Rules:** Imports have no network, database, broker, worker, simulator, or clock side
> effects. **Any payload emitted with `redaction_applied` set to `True` — envelope
> `data`, envelope `audit_metadata`, `TradingEvent.payload`, or pre-audit evidence —
> must be the return value of `redact_trading_payload` applied in the same function
> that sets the flag. The flag is evidence of a completed redaction, never a constant.**

**Add one row to §4.1 `errors.py` requirement table:**

| Status | Requirement ID | Responsibility | Class / Function / Method | Side Effects | Raises | Usage / Test |
|---|---|---|---|---|---|---|
| Completed | `FR-TRD-067` | The system shall expose one redaction helper that returns a JSON-safe mapping suitable for envelope `data`, event payloads, and audit evidence, so every `redaction_applied` claim is produced by an actual redaction pass. | `redact_trading_mapping(payload: Mapping[str, JsonValue]) -> dict[str, JsonValue]` | None | `TradingError`: payload is not JSON-safe | **Usage:** `tests/trading/usage/test_usage_contracts.py::test_usage_errors_redact_trading_mapping()`<br>**Unit:** `tests/trading/unit/contracts/test_errors.py::test_redact_mapping_returns_dict_and_scrubs_secrets()` |

**Amend `FR-TRD-037` (README:594) Responsibility cell** — append:

> … as versioned, redacted events. **Construction rejects any payload key for which
> `app.utils.is_sensitive_key` returns `True`, so `redaction_applied: True` is
> enforceable rather than declarative.**

### Code changes

`app/services/trading/contracts/errors.py`
: Add `redact_trading_mapping` — thin `dict`-narrowing wrapper over the existing
  `redact_trading_payload`, so call sites keep exact `dict[str, JsonValue]` typing under
  `mypy --strict`. Export via `contracts/__init__.py` and the package root `__all__`.

Apply the redaction pass at all eleven sites that currently hard-code the flag:

| File | Line | What gets redacted |
|---|---|---|
| `actions/orders.py` | 70–87 | envelope `data` (full receipt dump) |
| `actions/orders.py` | 106–125 | `TradingEvent.payload` (full receipt dump) |
| `actions/orders.py` | 213–224 | duplicate-completed envelope `data` |
| `actions/controls.py` | 110–124 | envelope `data` |
| `actions/emergency.py` | 74–89 | `results` and `skipped` child evidence |
| `actions/rebalance.py` | 268–280 | envelope `data` (`outcomes`) |
| `actions/runtime.py` | 310–322 | envelope `data` |
| `live/gates.py` | 146–160 | envelope `data` (full `intent` dump at `:252`) |
| `live/gates.py` | 232–241 | pre-audit evidence before `session.write_pre_audit` |
| `live/session.py` | 278–290 | envelope `data` |
| `reporting/evidence.py` | 64–79 | stored `evidence` before it enters `data` |
| `contracts/registry.py` | 190–207 | draft `data` |

`app/services/trading/state/events.py:49` and `app/services/trading/contracts/models.py:365`
: Keep `redaction_applied: Literal[True]`, and add a `model_validator(mode="after")`
  that raises if any payload/metadata key satisfies `app.utils.is_sensitive_key`. This
  turns the literal into an invariant the type system actually defends.

### Tests

* `tests/trading/unit/contracts/test_errors.py` — `redact_trading_mapping` returns
  `dict` and scrubs nested secrets.
* One test per emitting module (`orders`, `controls`, `emergency`, `rebalance`,
  `runtime`, `gates`, `session`, `evidence`, `registry`): plant
  `{"api_secret": "s3cr3t", "password": "p", "access_token": "t"}` into the source
  material; assert the literal values are absent from
  `json.dumps(result.model_dump(mode="json"))` while `redaction_applied` stays `True`.
* Negative: `TradingEvent(payload={"api_secret": "x"}, …)` raises.
* `tests/trading/usage/test_usage_contracts.py` — usage example for the new helper.

**Verification:** grep proves every `redaction_applied` site is preceded by a redaction
call in the same function; each new test fails if its redaction call is removed.

---

## 2. `TRD-B04a` — `TRADING_CONTRACT_VERSION`

### Amendment to `app/services/trading/README.md`

**§4.1 Configuration and Limits Manifest — replace the row at README:521:**

> | Completed | `TRADING_CONTRACT_VERSION` | `str` | `v1` | Yes | All contract types | Breaking semantic/schema changes require a new version and coordinated consumer migration. **Exposed as `app.services.trading.TRADING_CONTRACT_VERSION`; every owned contract's `contract_version` literal and every emitted report version reference this constant.** |

**Add one row to the §4.1 `models.py` requirement table:**

| Status | Requirement ID | Responsibility | Class / Function / Method | Side Effects | Raises | Usage / Test |
|---|---|---|---|---|---|---|
| Completed | `FR-TRD-066` | The system shall expose the single canonical Trading contract version constant that every owned contract and emitted report references. | `TRADING_CONTRACT_VERSION: str` | None | None | **Usage:** `tests/trading/usage/test_usage_contracts.py::test_usage_models_contract_version()`<br>**Unit:** `tests/trading/unit/contracts/test_models.py::test_contract_version_matches_every_owned_model()` |

### Code changes

`app/services/trading/contracts/models.py`
: Add `TRADING_CONTRACT_VERSION: Final[str] = "v1"` near the top; add to `__all__`.

`app/services/trading/contracts/__init__.py`, `app/services/trading/__init__.py`
: Re-export.

`app/services/trading/reporting/evidence.py:71`
: Replace the hard-coded `"contract_version": "v1"` with the constant.

### Test

`test_contract_version_matches_every_owned_model` asserts the constant equals the
`contract_version` default on `TradingRequest`, `OrderIntent`, `ExecutionReceipt`,
`TradeRecord`, `PortfolioRebalanceExecutionRequest`, and `OperationalEvent` — so a
future bump cannot drift.

---

## 3. `TRD-B04b` — `IDEMPOTENCY_RETENTION_SECONDS`

### Amendment to `app/services/trading/README.md`

**§4.2 Configuration and Limits Manifest — replace the row at README:587:**

> | Completed | `IDEMPOTENCY_RETENTION_SECONDS` | `int` | No shared default | Yes | `reserve_idempotency()` | Every runtime profile declares an exact positive retention window; omission blocks governed mutation, same-material reuse within the window returns the existing reservation/receipt, and different-material reuse conflicts. **The window is supplied explicitly to `reserve_idempotency()` and determines the reservation `expires_at`; the request's own `valid_until` never sets reservation lifetime.** |

**§4.2 — replace the `FR-TRD-039` signature cell (README:596):**

> `reserve_idempotency(request: TradingRequest, store: TradingStateStore, retention_seconds: int, *, now: datetime) -> IdempotencyReservation`

with Responsibility amended to:

> The system shall reserve a caller-supplied key against versioned canonical SHA-256
> material before send and reject different-material reuse. **The reservation expires
> exactly `retention_seconds` after `now`; a non-positive or absent retention window
> raises `CONFIGURATION_INVALID` before any store call.**

Raises cell becomes:
> `TradingError`: missing key, **invalid retention window**, conflict, or write failure

**§4.7 Configuration and Limits Manifest — add a row** so the live runtime declares it:

> | Completed | `IDEMPOTENCY_RETENTION_SECONDS` | `int` | No shared default | Yes | `LiveSession.start`, `evaluate_live_gate` | Validated at configuration load; omission fails initialization. |

### Code changes

`app/services/trading/live/config.py`
: Add required `idempotency_retention_seconds: _PositiveInt` and
  `concurrency_lock_timeout_seconds: _PositiveDecimal` (see §4) to
  `_LiveRuntimeConfig`, with `AliasChoices` matching the env names. Add a
  `_positive_int` `BeforeValidator` mirroring the existing `_positive_decimal`
  (rejecting `bool`, `float`, non-finite, non-positive).

`app/services/trading/state/idempotency.py`
: `reserve_idempotency` gains `retention_seconds: int` and keyword-only `now: datetime`.
  Validate `retention_seconds > 0` and `now` is aware-UTC before touching the store;
  compute `expires_at = now + timedelta(seconds=retention_seconds)` and pass that to
  `store.reserve_idempotency` in place of `request.valid_until` (currently line 140).

`app/services/trading/live/gates.py:206`
: `reserve_idempotency(request, session.store, session.config.idempotency_retention_seconds, now=now)`.

`app/services/trading/actions/orders.py:211`
: Sim route has no `LiveSession`. Add `idempotency_retention_seconds: int` to
  `TradingDependencies` (documented in §4.8 Files table, `FR-TRD-056`) and pass
  `deps.idempotency_retention_seconds` with `now=deps.clock()`.

### Tests

* Omitted / zero / negative retention raises `CONFIGURATION_INVALID` before any store
  call (assert the store's call counter stays `0`).
* `expires_at == now + retention`, not `request.valid_until` — this test fails against
  current code.
* Same-material reuse inside the window returns the existing reservation; outside it, a
  new one.

---

## 4. `TRD-B04c` — `CONCURRENCY_LOCK_TIMEOUT_SECONDS`

### Amendment to `app/services/trading/README.md`

**§4.2 Configuration and Limits Manifest — replace the row at README:588:**

> | Completed | `CONCURRENCY_LOCK_TIMEOUT_SECONDS` | `Decimal` | No shared default | Yes | `reserve_idempotency()`, `evaluate_live_gate()` | Every runtime profile declares an exact positive timeout. Omission fails configuration. **A `duplicate_active` reservation whose age exceeds the timeout is a stale lock: it is reported as `TRADING_CONCURRENCY_CONFLICT` with `stale_lock=True` in the trace context and never silently reclaimed — recovery requires reconciliation.** Exceeding the bound returns `TRADING_CONCURRENCY_CONFLICT`. |

**§4.2 — amend `FR-TRD-057` (README:605) Responsibility:**

> The system shall expose an immutable reservation result distinguishing new,
> duplicate-completed, duplicate-active, conflict, and reconciliation-required states.
> **It records `reserved_at` so lock age is measurable against
> `CONCURRENCY_LOCK_TIMEOUT_SECONDS`.**

### Code changes

`app/services/trading/state/idempotency.py`
: Add required `reserved_at: datetime` to `IdempotencyReservation`, validated
  aware-UTC, with a model validator requiring `expires_at > reserved_at`.

`app/services/trading/live/gates.py:206–215`
: After reservation, when `status == "duplicate_active"` and
  `now - reservation.reserved_at > config.concurrency_lock_timeout_seconds`, raise
  `TradingError("TRADING_CONCURRENCY_CONFLICT", "Idempotency lock is stale",
  trace_context={"stale_lock": True, "reservation_key": …})`. The existing
  non-stale `duplicate_active` / `conflict` / `reconciliation_required` block is
  unchanged — this only adds explicit stale-lock attribution.

`app/services/trading/actions/orders.py:225–228`
: Same treatment on the sim path.

### Tests

* A `duplicate_active` reservation older than the bound raises with
  `stale_lock=True`; one inside the bound raises the ordinary conflict without the flag.
* Omitted / non-positive timeout fails configuration validation.
* A stale lock is **not** reclaimed — assert no store write and no dispatch occurs.

---

## 5. `TRD-B04d` — `MAX_STALENESS_SECONDS` (the fail-open path)

This is the highest-consequence amendment: today a caller supplying a distant
`expires_at` passes readiness on arbitrarily old market and account evidence.

### Amendment to `app/services/trading/README.md`

**§4.3 Configuration and Limits Manifest — replace the row at README:634:**

> | Completed | `MAX_STALENESS_SECONDS` | `StalenessPolicy` (four positive `Decimal` bounds) | No shared default | Yes | `assess_execution_readiness()` | Every runtime profile declares an exact positive freshness bound for each evidence class — `route_evidence`, `risk_decision`, `kill_switch`, `action_policy`. **Readiness fails closed when either the evidence's own declared expiry has passed or its observed age exceeds the configured bound, whichever is stricter.** Omission fails configuration. |

**§4.3 Files table — amend the `readiness.py` row key exports:**

> `ReadinessAssessment`, `StalenessPolicy`, `assess_execution_readiness`

**§4.3 — replace the `FR-TRD-027` signature cell (README:643):**

> `assess_execution_readiness(request: TradingRequest, snapshot: RouteSnapshot, risk_decision: RiskDecision, kill_switch_state: KillSwitchState, action_policy: Mapping[str, JsonValue], staleness: StalenessPolicy) -> ReadinessAssessment`

with Responsibility amended to:

> The system shall aggregate all required checks and return a bounded pass/fail
> assessment with evidence references. **Each evidence class is checked against both its
> declared expiry and the configured maximum age for its class; exceeding either fails
> the assessment with the class-specific `*_STALE` code.**

**Add one row to the §4.3 requirement table:**

| Status | Requirement ID | Responsibility | Class / Function / Method | Side Effects | Raises | Usage / Test |
|---|---|---|---|---|---|---|
| Completed | `FR-TRD-068` | The system shall expose one immutable per-evidence-class freshness policy with four required positive bounds and no default. | `StalenessPolicy` | None | `TradingError`: absent, non-positive, or non-finite bound | **Usage:** `tests/trading/usage/test_usage_validation.py::test_usage_readiness_staleness_policy()`<br>**Unit:** `tests/trading/unit/validation/test_readiness.py::test_staleness_policy_requires_positive_bounds()` |

**§4.7 Configuration and Limits Manifest — add a row:**

> | Completed | `MAX_STALENESS_SECONDS` | `StalenessPolicy` | No shared default | Yes | `LiveSession.start` | Validated at configuration load and supplied to the injected readiness source; omission fails initialization. |

### Code changes

`app/services/trading/validation/readiness.py`
: Add frozen `StalenessPolicy(BaseModel)` with required positive `Decimal` fields
  `route_evidence`, `risk_decision`, `kill_switch`, `action_policy`
  (`extra="forbid"`, `allow_inf_nan=False`, each `> 0`).

  `assess_execution_readiness` gains the `staleness` parameter and each `_append_*`
  helper gains its bound, adding an age check alongside the existing expiry check:

  | Helper | Line | Existing check | Added age check | New failure code |
  |---|---|---|---|---|
  | `_append_snapshot_failures` | 129 | `snapshot.expires_at <= request.system_time` | `request.system_time - snapshot.observed_at > staleness.route_evidence` | `ROUTE_EVIDENCE_STALE` |
  | `_append_risk_failures` | 154 | `risk_decision.expires_at <= request.system_time` | `request.system_time - risk_decision.issued_at > staleness.risk_decision` | `RISK_DECISION_STALE` |
  | `_append_risk_failures` | 160 | `kill_switch_state.state != "inactive"` | `request.system_time - kill_switch_state.updated_at > staleness.kill_switch` | `KILL_SWITCH_STALE` (new code) |
  | `_append_policy_failures` | 184 | `policy_expiry <= request.system_time` | `request.system_time - policy_issued_at > staleness.action_policy` | `ACTION_POLICY_STALE` |

  `_append_policy_failures` additionally reads `issued_at` from the `action_policy`
  mapping via the existing `_policy_time` helper; an absent or malformed `issued_at`
  fails closed with `ACTION_POLICY_STALE`.

`app/services/trading/validation/__init__.py`, `app/services/trading/__init__.py`
: Export `StalenessPolicy`.

`app/services/trading/live/config.py`
: Add the four required bounds to `_LiveRuntimeConfig` under a
  `max_staleness_seconds` nested model, validated at load.

### Tests

* **The fail-open regression test:** a `RouteSnapshot` with a far-future `expires_at`
  but `observed_at` older than `route_evidence` must fail readiness. *This test fails
  against current code — it is the proof the blocker is closed.*
* One boundary pair per evidence class (exactly at the bound passes; one unit past
  fails) with the correct class-specific code.
* `StalenessPolicy` rejects zero, negative, non-finite, and absent bounds.
* An `action_policy` mapping with no `issued_at` fails closed.

---

## 6. `TRD-B03` — Missing `WF-TRD-013` integration test

### Amendment to `app/services/trading/README.md`

No specification change — README:494 already names the correct test. The code must meet
the README, not the reverse.

**§7 checklist (README:994) — replace the evidence pointer:**

> - [X] Every collaborative workflow has an integration test. `tests/trading/integration/test_portfolio_rebalance.py:20`

### New file

`tests/trading/integration/test_portfolio_rebalance.py` containing
`async def test_rebalance_cannot_bypass_risk_or_open_to_match_weight() -> None:`,
with fixtures built locally (not imported from `tests/trading/unit/`), asserting:

1. Absent, expired, or non-approving `AllocationRiskDecision` → `TradingError`, and
   **zero** adapter and zero simulation dispatch calls.
2. A `PortfolioBudgetExecutionVerdict` not bound to the exact `plan_id` and canonical
   hash → rejected by `BudgetGate.validate`.
3. An action that would open or increase exposure to match a target weight → rejected;
   only canonical `reduce_exposure` corrections proceed.
4. A tampered `canonical_hash` → rejected.

`tests/trading/integration/test_rebalance.py` is retained as the positive-path test.

**Verification:** the README reference resolver reports zero unresolved
`tests/trading/…::test_…` references (currently 1 of 142); the new test fails if the
Risk-authorization check in `actions/rebalance.py` is removed.

---

## 7. `TRD-B02` — Reconcile `docs/PROJECT.md`

**Sequenced last**, so the registry records the corrected state rather than the state at
review time.

### Amendments to `docs/PROJECT.md`

| Line | Row | `Missing` → |
|---|---|---|
| 765 | `OrderIntent v1` | `Completed` |
| 766 | `TradeRecord` / `ExecutionReceipt v1` | `Completed` |
| 767 | `OperationalEvent v1` | `Completed` |
| 785 | `PortfolioRebalanceExecutionRequest v1` | `Completed` |
| 841 | Trading orders/fills/execution state/idempotency/`TradeRecord` tables | `Completed` |
| 869 | `EXECUTION_ROUTE` | `Completed` |
| 870 | `ALLOW_LIVE_MUTATIONS` | `Completed` |

**Line 936** — replace the Trading clause "Trading mutation workflow remains pending"
with "Trading mutation workflow is implemented behind `ALLOW_LIVE_MUTATIONS=false`;
production enablement remains pending owner sign-off." Status stays `Partial` because
the Brokers/UI-API composition clauses in the same row remain open.

**Explicitly not touched:** `SYS-WF-001/002/005/006/008` (`:401–408`) stay `Missing` —
system-level assembly is a later phase. No other domain's row is modified.

### Amendment to `docs/CHANGELOG.md`

One entry under `Added`, three sentences maximum per that file's own instruction:

> - **2026-07-19 — Trading blocker corrections applied.** Enforced real redaction at
>   every `redaction_applied` boundary, implemented the four required Trading
>   configuration bounds (`TRADING_CONTRACT_VERSION`, `IDEMPOTENCY_RETENTION_SECONDS`,
>   `CONCURRENCY_LOCK_TIMEOUT_SECONDS`, per-evidence-class `MAX_STALENESS_SECONDS`), and
>   added the missing `WF-TRD-013` rebalance authorization integration test.
>   Reconciled the top-level contract, persisted-state, and shared-configuration
>   registries with the completed Trading domain.

Under `Decisions`, record D1–D3 from §0.

---

## 8. Deferred — not in this pass

`TRD-H01` (positive live dispatch test), `TRD-H02` (integration tests importing unit
fixtures), `TRD-H03` (bulk emergency Risk binding — needs an owner decision),
`TRD-H04` (`model_copy` revalidation), `TRD-H05` (unregistered report schema id), and
all MEDIUM/LOW findings remain open. `TRD-H05` is deliberately deferred because
registering `ExecutionEvidenceReport v1` touches the same `docs/PROJECT.md` §5 table as
`TRD-B02`; doing both in one pass would blur the blocker boundary.

The domain remains **NOT READY** after this pass. A full re-review is required.

---

## 9. Rollback path

Every change is additive or a localized in-place edit; no file is deleted or renamed.
The implementation is currently untracked in git, so before executing:

```bash
git stash list                      # confirm clean starting point
cp -r app/services/trading /tmp/trading.bak
cp -r tests/trading /tmp/tests-trading.bak
cp docs/PROJECT.md docs/CHANGELOG.md /tmp/
```

Rollback is a restore from those copies plus `git checkout -- docs/PROJECT.md
docs/CHANGELOG.md app/services/trading/README.md` for the tracked files.

---

## 10. Validation gate for this pass

```bash
uv run ruff check app/services/trading tests/trading      # EXE001-only is acceptable
uv run ruff format --check app/services/trading tests/trading
uv run mypy app/services/trading tests/trading
uv run pytest tests/trading -o addopts="" --import-mode=importlib \
  --cov=app/services/trading --cov-report=term-missing --cov-fail-under=80
```

Plus the README reference resolver (0 unresolved) and the AST audit (0 missing
docstrings, logger calls, or annotations across all functions, including new ones).

Expected outcome: all green, coverage at or above the current 84.06%, test count rising
from 160 to roughly 185.

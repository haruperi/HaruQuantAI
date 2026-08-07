# Trading and Broker Safety Baseline

**Work package:** `TC-IMP-BASE-08`
**Baseline ID:** `HQA-TC-P0-20260807T075707Z-3b039544`
**Captured (UTC):** `2026-08-07T07:57:07Z`

**No order was submitted, cancelled, replaced or transmitted. No broker connection was opened. No live
account was contacted.** Every finding below comes from reading source code and tests.

---

## 1. Safety classification

```text
CURRENT SAFETY BOUNDARY: PARTIAL
```

**Why not `PROVEN`:** a boundary is `PROVEN` only when code *and tests* demonstrate it. There is no
Trading Cockpit mode, session or route in the repository, so no test can assert that a cockpit session
cannot reach a live route. The guard that would carry that proof does not have a subject yet.

**Why not `VIOLATED`:** no default or reachable path sends production live-money orders without an
explicit, non-bypassable guard. The evidence for this is set out in sections 3 and 4. The live route
exists by design — HaruQuantAI is a trading application — but reaching it requires all of: an explicit
`RUNTIME_PROFILE=live`, an explicit `EXECUTION_ROUTE=live`, `ALLOW_LIVE_MUTATIONS=true` (default
`False`), a broker connection whose `environment` is `live`, an enabled session admission flag, and a
clean pass through the seven-stage fail-fast gate sequence. Any single failure raises rather than
degrades.

**Why not `UNPROVEN`:** substantial, tested isolation already exists — sim-route/broker-authority
mutual exclusion, route-versus-environment matching in both directions, a durable compare-and-swap kill
switch, and an agent permission model in which broker mutation is an unrepresentable type.

---

## 2. Write-capable adapters and methods

### 2.1 Adapter protocol (the single write surface)

`app/services/brokers/contracts/protocols.py`

| Method | Line |
|---|---|
| `place_order` | 578 |
| `modify_order` | 591 |
| `cancel_order` | 604 |
| `modify_position` | 618 |
| `close_position` | 631 |
| `replace_order` | 644 |

Contract version `v1`; schema id `brokers.adapter.v1`. Both are asserted at dispatch time
(`app/services/trading/routing/dispatcher.py`, `ADAPTER_INCOMPATIBLE` on mismatch).

### 2.2 Concrete adapter implementations

| Adapter | File | Write methods (lines) |
|---|---|---|
| cTrader | `app/services/brokers/ctrader_mutations/operations.py` | `place_order` 62, `modify_order` 86, `cancel_order` 106, `modify_position` 122, `close_position` 152 |
| MetaTrader 5 | `app/services/brokers/mt5_mutations/operations.py` | `place_order` 80, `modify_order` 93, `cancel_order` 112, `modify_position` 127, `close_position` 161 |
| Deterministic fake | `app/services/brokers/testing/` (`FEAT-BRK-14`) | in-memory only, no external transport |

Binance, Dukascopy and Yahoo packages (`binance_session/`, `dukascopy_bars/`, `dukascopy_ticks/`,
`yahoo_history/`) provide session and read paths; no order-write method was located in them.

### 2.3 Domain-level write functions

`app/services/brokers/operations.py`

| Function | Line |
|---|---|
| `place_broker_order` | 1343 |
| `modify_broker_order` | 1359 |
| `cancel_broker_order` | 1375 |
| `modify_broker_position` | 1393 |
| `close_broker_position` | 1409 |
| `replace_broker_order` | 1537 |

---

## 3. Environment selection and the guards on each path

### 3.1 Environment enumerations

| Enum / literal | Location | Values |
|---|---|---|
| `BrokerEnvironment` | `app/services/brokers/contracts/enums.py:18` | `LIVE`, `DEMO`, `TESTNET`, `SANDBOX` |
| `TradingRoute` | `app/services/trading/contracts/models.py:383` | `SIM`, `PAPER`, `LIVE` |
| connection environment literal | `app/services/trading/contracts/models.py:1115` | `"demo"`, `"paper"`, `"sim"`, `"live"` |
| `runtime_profile` / `execution_route` | `app/services/trading/live/config.py:108,111` | `"paper"`, `"live"` |
| `ENVIRONMENT` application setting | `app/utils/settings/loader.py:19,67,239`; `app/utils/settings/models.py:45` | free-form; `AGENTS.md` mandates `ENVIRONMENT=dev` for real integration operations |

> Note: `TradingRoute` includes `SIM` but `_LiveRuntimeConfig.execution_route` is restricted to
> `"paper" | "live"`. The live-session configuration therefore cannot describe a simulation route. This
> asymmetry matters for the cockpit and is recorded as finding S-4.

### 3.2 Guard inventory

| # | Guard | Location | Behavior | Bypassable? |
|---|---|---|---|---|
| G-1 | `_require_non_production(provider, environment)` | `app/services/brokers/registry/provider_connections.py:90` | Raises `ValueError` unless the environment is in `_NON_PRODUCTION_ENVIRONMENTS` (demo, testnet, sandbox). Module docstring: *"Only non-production environments (demo, testnet, sandbox) are permitted through"*. | Not from inside the standalone-connection path. **Applies to standalone provider connections only** — see finding S-1. |
| G-2 | Live route requires live environment | `app/services/trading/routing/dispatcher.py:294-297` | `if intent.route.value == "live" and connection.environment != "live": raise TradingError("SCOPE_MISMATCH", "Live route requires live environment")` | No |
| G-3 | Paper route rejects live environment | `app/services/trading/routing/dispatcher.py:299-302` | `if intent.route.value == "paper" and connection.environment == "live": raise TradingError("SCOPE_MISMATCH", "Paper route cannot use live environment")` | No |
| G-4 | Sim route rejects broker authority | `app/services/trading/routing/dispatcher.py:503` | `if intent.route.value == "sim":` requires a `simulation_dispatch`; if a broker `connection` or `broker_adapter` is supplied, raises `SCOPE_MISMATCH "Sim dispatch received Broker authority"` | No. **This is the strongest structural isolation available to the cockpit today.** |
| G-5 | `allow_live_mutations` | `app/services/trading/live/config.py:114` | `bool = Field(default=False, ...)` from `ALLOW_LIVE_MUTATIONS` | Fail-closed by default |
| G-6 | Profile/route compatibility | `app/services/trading/live/config.py:_validate_compatibility` | `if self.runtime_profile != self.execution_route: raise ValueError("runtime profile and execution route are incompatible")` | No |
| G-7 | Session admission | `app/services/trading/live/gates.py` (`session.admission_enabled`) | When disabled, the request is returned as `packaged` with `dispatch_allowed: False` rather than dispatched | No |
| G-8 | Kill-switch hierarchy | `app/services/trading/validation/authority.py::validate_kill_switch_hierarchy`, consumed in `live/gates.py` | Gate failure raises `GATE_BLOCKED` | `AGENTS.md` section 3: *"Deterministic. No caller can override or bypass a kill switch."* |
| G-9 | Risk authority | `app/services/trading/validation/authority.py::validate_risk_authority` | Authority read error raises `GATE_BLOCKED` | No |
| G-10 | Action policy | `app/services/trading/validation/authority.py::validate_action_policy` | Gate failure raises | No |
| G-11 | Adapter capability | `app/services/trading/routing::validate_adapter_capability` | Unsupported operation rejected before submission | No |
| G-12 | Broker provider enabled + identity match | `app/services/trading/routing/dispatcher.py:288-293` | `GATE_BLOCKED` if disabled; `SCOPE_MISMATCH` if `intent.provider_id` differs from the connection id | No |
| G-13 | Schema compatibility | `app/services/trading/live/gates.py` | `INVALID_REQUEST` unless `contract_version == "v1"` and `schema_id == "trading.trading_request.v1"` | No |
| G-14 | Request validity window | `app/services/trading/live/gates.py` | `GATE_BLOCKED` if the session is not started or `request.valid_until <= now` | No |
| G-15 | Agent tool token deny-list | `app/agentic/permissions/models.py:46` | `place_order`, `cancel_order`, `close_position`, `modify_position`, `modify_order`, `clear_kill_switch`, `activate_kill_switch`, `override_mandate`, `approve_own`, `deploy`, `rotate_key`, `credential` are never registered for an agent (`FR-AGENTIC-015`) | No |
| G-16 | Agent receiver-domain deny-list | `app/agentic/permissions/models.py:64` | `FORBIDDEN_RECEIVER_DOMAINS = {"brokers", "broker"}` | No |
| G-17 | Agent side-effect class | `app/agentic/permissions/models.py:66` | `SideEffectClass = Literal["read_only","deterministic_compute","staging_write","proposal_submission"]`. Module docstring: *"`controlled_mutation` and `critical` classes are unrepresentable, so no broker mutation, kill-switch clearance, or production deployment can be [performed]"* | **Deny by construction**, not deny by check |
| G-18 | Secret-free event stream | `app/services/api/streams/events.py:41` | `_assert_secret_free` raises `StreamValidationError` | No |
| G-19 | Redacted gate envelopes | `app/services/trading/live/gates.py::_gate_envelope` | `_redacted_envelope_data(data)`, `redaction_applied: True` | No |
| G-20 | Secret detection in CI | `.pre-commit-config.yaml` (`detect-secrets` v1.5.0 against `.secrets.baseline`) | pre-commit stage | Only if hooks are skipped |

### 3.3 The fail-fast gate sequence

`app/services/trading/live/gates.py::_evaluate_live_gate_value` (line 71), read in full:

```text
1. schema compatibility          -> INVALID_REQUEST
2. session started + valid_until -> GATE_BLOCKED
3. session.admission_enabled     -> returns "packaged", dispatch_allowed = False
4. action policy                 -> GATE_BLOCKED on read error
5. risk decision                 -> GATE_BLOCKED on read error
6. kill switches                 -> GATE_BLOCKED on read error
7. readiness (freshness bounds)  -> GATE_BLOCKED on read error
8. adapter capability            -> GATE_BLOCKED on read error
```

Every gate result is wrapped in an envelope carrying `risk_level="critical"`, `places_trade=True`,
`modifies_database=True` and `requires_network = route in {"paper","live"}`, with redaction applied.

---

## 4. Entry points that can reach a write

| Entry point | Path | Reaches broker write? | Interposed guards |
|---|---|---|---|
| HTTP `POST /orders` | `app/services/api/routes/trading.py:120` | Yes, via Trading | G-13, G-14, G-7, G-10, G-9, G-8, G-11, G-12, G-2/G-3/G-4, plus API RBAC and mandatory idempotency |
| HTTP `DELETE /orders/{order_id}` | `app/services/api/routes/trading.py:159` | Yes | same |
| HTTP `POST /positions/{position_id}/close` | `app/services/api/routes/trading.py:199` | Yes | same |
| HTTP `GET /trading/session` | `app/services/api/routes/trading.py:95` | No (read) | RBAC |
| Trading public actions | `app/services/trading/actions/orders.py`, `controls.py`, `emergency.py`, `rebalance.py` | Yes | full gate sequence |
| Trading dispatcher | `app/services/trading/routing/dispatcher.py` | Yes | G-2, G-3, G-4, G-11, G-12 |
| Brokers domain functions | `app/services/brokers/operations.py:1343-1537` | Yes — **this is the lowest-level public write surface** | G-1 for standalone connections; otherwise the caller's guards |
| Broker registry factory | `app/services/brokers/registry/factory.py:234,244,281,292` | Constructs a connection carrying `config.environment` | **G-1 not observed on this path** — finding S-1 |
| Agentic agents | `app/agentic/` | **No** | G-15, G-16, G-17 make it structurally impossible |
| Simulator | `app/services/simulator/` | **No** | G-4 forbids broker authority on the sim route |
| Usage programs | `tests/*/usage/` (374 programs) | Only against non-production | `AGENTS.md` section 7; `tests/brokers/unit/test_usage_real_connection_contract.py` |

---

## 5. Test evidence

| Evidence | File |
|---|---|
| Live gate sequence behavior | `tests/trading/unit/live/test_gates.py` |
| Route / scope mismatch handling | `tests/trading/unit/actions/test_orders.py`, `test_positions.py`, `test_rebalance.py` |
| Non-production connection contract | `tests/brokers/unit/test_usage_real_connection_contract.py` |
| README-to-code parity for Brokers | `tests/brokers/unit/test_documentation_parity.py` |
| Owner dependency composition (non-production) | `tests/api/unit/test_owner_dependency_composition.py` |
| Trading route authorization at the API | `tests/api/unit/test_trading_routes.py` |
| Kill switch, unit | `tests/risk/unit/test_kill_switch.py` |
| Kill switch, system-level | `tests/system/integration/test_kill_switch.py` |
| Risk governor | `tests/risk/unit/test_governor.py` |
| Agent tool permissions | `tests/agentic/unit/test_permissions.py`, `tests/agentic/integration/test_tool_permissions.py` |
| Agent governance | `tests/agentic/unit/test_governance.py` |
| Signal-to-live workflow | `tests/system/integration/test_signal_to_live.py` |
| Economic news restriction | `tests/system/integration/test_economic_news_restriction.py` |

---

## 6. Findings

| # | Severity | Finding | Evidence | Recommended action |
|---|---|---|---|---|
| **S-1** | **High** | `_require_non_production` guards *standalone provider connections* only. `app/services/brokers/registry/factory.py` passes `config.environment` through at lines 234, 244, 281 and 292 without an observed non-production assertion, so a caller that constructs a connection config with `environment=BrokerEnvironment.LIVE` through the factory reaches a live-capable connection. Downstream Trading guards (G-2, G-5, G-7, G-8) still apply and are non-bypassable, which is why this is not classified `VIOLATED`. | `provider_connections.py:90`; `factory.py:234,244,281,292`; `catalogue.py:179` ("downstream Trading/Risk controls remain defense in depth") | Before Phase 2 completes, add a cockpit-scoped assertion so a Trading Cockpit session can never obtain a `live` connection, and add a test that proves it. |
| **S-2** | **High** | **No cockpit mode exists to bind a guard to.** The specification requires `Mode = SIMULATION` as checklist step `PRE_001` and requires the master switch to stay `OFF` otherwise. There is no mode concept in any domain, so this interlock cannot be written or tested today. | `TC-IMP-SIM-09` is `ABSENT`/`CREATE`; specification `PRE_001` | `TC-IMP-SIM-09` (mode model) is a prerequisite for proving the cockpit safety boundary. Sequence it early in Phase 8, or lift it earlier. |
| **S-3** | **Medium** | **The kill switch is a single boolean.** `risk_kill_switch_states` blocks or unblocks; it does not separate the new-exposure lock from cancel, protection, reduction and closure permissions. Specification acceptance criterion 12 and steps `FLASH_002`, `DD_002` require risk-reducing actions to stay available while new exposure is locked. | `app/services/risk/kill_switch/`; `app/services/trading/live/config.py::allow_live_mutations`; `TC-IMP-TRD-09` | `EXTEND` the kill switch with permission granularity in Phase 6, and `EXTEND` the Trading master enable in Phase 7. |
| **S-4** | **Medium** | `_LiveRuntimeConfig.execution_route` is `Literal["paper","live"]` and cannot express `sim`, even though `TradingRoute.SIM` exists. A cockpit session running through the live-session machinery has no way to declare itself simulation-only at the configuration layer. | `app/services/trading/live/config.py:111`; `app/services/trading/contracts/models.py:383` | Decide in Phase 7 whether the cockpit uses the live-session machinery at all; if it does, `execution_route` must admit `sim`. |
| **S-5** | **Medium** | **No first-class `UNKNOWN` order state.** A dispatcher timeout produces `_timeout_receipt`, but `UNKNOWN` is not a persisted order state preserved until reconciliation, and no test proves that blind resubmission is prohibited. Specification acceptance criterion 7 and steps `API_001`, `API_002` require it. | `app/services/trading/routing/dispatcher.py::_timeout_receipt`; `TC-IMP-BRK-07`, `TC-IMP-TRD-03` | Phase 2 and Phase 7. Until then, treat timeout handling as unproven. |
| **S-6** | **Medium** | **No protective-order lifecycle at all.** Nothing in the repository attaches, verifies or resizes a protective stop, and nothing prevents an orphaned position or an OCO cancellation that removes both exits. Specification 6.6 and steps `FLASH_003`, `ENTRY_*` depend on it. | `TC-IMP-TRD-08` is `ABSENT` | Phase 7 `CREATE`. This is a safety gap, not merely a feature gap. |
| **S-7** | **Low** | `app/configs/gcp-oauth.keys.json` is tracked in the repository. Its contents were **not** read, hashed or reproduced in any Phase 0 artifact. | filesystem listing of `app/configs/` | Owner review: confirm this file contains no secret material, or remove it from version control. |
| **S-8** | **Informational** | The agent permission model is the strongest safety asset in the repository and should be reused verbatim for cockpit agents rather than reimplemented. Broker mutation and kill-switch clearance are *unrepresentable types*, not runtime checks. | `app/agentic/permissions/models.py:46,64,66`; `tests/agentic/integration/test_tool_permissions.py` | `TC-IMP-AGT-01` is `EXTEND`; `TC-IMP-AGT-09` is the programme's only `REUSE`. |

---

## 7. Can a Trading Cockpit session be structurally restricted today?

**Partially.** The mechanism exists; the subject does not.

`TradingRoute.SIM` combined with guard G-4 gives exactly the isolation the cockpit needs: on the sim
route the dispatcher *requires* a simulation dispatch and *refuses* any broker authority. A cockpit built
on `route = SIM` cannot reach a broker adapter.

What is missing is the binding. There is no cockpit session, no `Mode = SIMULATION`, and therefore no
place to assert "this session may only produce `SIM` intents". Until `TC-IMP-SIM-09` exists, the
restriction is a convention a caller must observe rather than an invariant the system enforces.

**Recommended sequencing change for the owner's consideration:** the plan places mode behavior at
`TC-IMP-SIM-09` in Phase 8, but `TC-IMP-BRK-10` in Phase 2 is supposed to prove simulation/sandbox
isolation. Phase 2 cannot discharge that obligation without the mode concept. Either lift a minimal mode
marker into Phase 2, or explicitly re-date the `TC-IMP-BRK-10` proof to Phase 8.

---

## 8. Phase 0 safety confirmations

| Check | Result |
|---|---|
| Production order submitted | **NO** |
| Live account write attempted | **NO** |
| Broker connection opened | **NO** |
| Migration applied | **NO** |
| Database opened or written | **NO** |
| `.env` file read, modified or reproduced | **NO** |
| Secret value written into any artifact | **NO** |
| Credentials in remote URLs, logs or errors | none encountered; the remote URL is credential-free |
| Account IDs recorded | **NONE** |

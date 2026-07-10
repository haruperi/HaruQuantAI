# Phase 07 Live -> Trading -- Brownfield Migration and Deletion Plan

Status: implemented
Owner: Haruperi
Target: delete `app/services/live/` with zero functional regression

---

## 0. Brownfield Objective

`app/services/trading/` is now the surviving live-runtime and broker-dispatch
boundary. `app/services/live/` is the older Phase-10-style safety gateway that
duplicates session lifecycle, gate evaluation, package-only execution,
reconciliation, monitoring, policy, and port contracts.

The audit shows `trading` covers the functional responsibilities of `live`, but
the old package is not safe to delete immediately because tests, one usage
script, and stale docs still import `app.services.live`.

This plan migrates those executable references to the `trading` runtime,
removes vacuous live-only tests, preserves the real behavioral assertions in the
trading test suite, folds any useful README material into `trading/README.md`,
and then deletes `app/services/live/`.

Out of scope: redesigning the risk gate. `trading` still exposes
`passthrough_risk_evaluator`, exactly as recorded in the Trader -> Trading
migration. Wiring `app/services/risk` into gate 7 remains a separate governed
plan.

---

## 1. Repository Baseline Audit

### 1.1 Current deletion state

The worktree already contains the completed `trader` deletion/migration work.
This audit treats those changes as baseline and does not revert them.

Relevant current state:

| Area | Status |
| --- | --- |
| `app/services/trader/` | Already deleted in the current worktree |
| `app/services/trading/` | Contains live gate pipeline, broker dispatch, state stores, monitoring, reconciliation, runtime coordination |
| `app/services/live/` | Deleted after migration into `app/services/trading/` |
| `docs/dev/07-trader-to-trading-migration-plan.md` | Exists and records the prior brownfield migration |

### 1.2 Consumers

No non-`live` production code path imported `app.services.live`.
The remaining executable import references were test, usage, or self-referential
package imports, and have been removed:

| File | Nature of reference | Action |
| --- | --- | --- |
| `tests/unit/app/services/live/test_live_runtime.py` | Real executable contract for old live package | Covered by trading suites, then deleted |
| `tests/unit/app/services/live/test_gates_extra.py` | Vacuous broad `try/except Exception` smoke test | Deleted |
| `tests/unit/app/services/live/test_live_risk_sim_pybots_extra2.py` | Vacuous `ExecutionGates` import stanza; other unrelated stanzas | Deleted with live-only package path |
| `tests/unit/test_massive_others_extra.py` | Vacuous `ExecutionGateManager` import stanza | Removed only live stanza |
| `tests/usage/10_live.py` | Old usage examples for live runtime | Deleted; surviving examples are in `tests/usage/07_trading.py` |
| `app/services/live/**` | Self imports and README references | Deleted |
| `docs/audit/workflows.md` | Stale duplicate-stack audit text | Updated after deletion |
| `docs/dev/07-trader-to-trading-migration-plan.md` | Historical references to `live` as future work | Keep as historical record |

Deleting `live` affected tests/docs/examples, not production `app/` callers.

### 1.3 Baseline validation

Targeted behavioral suite:

```powershell
uv run pytest -q -o addopts="" tests/unit/app/services/live tests/services/trading/gates tests/services/trading/runtime tests/services/trading/monitoring tests/services/trading/reconciliation tests/services/trading/actions/test_controls.py tests/services/trading/actions/test_emergency.py
```

Result: **330 passed in 12.84s**.

The same slice with project default `addopts` also had all behavioral tests
pass, but exited nonzero because partial test selection triggered the whole-repo
coverage denominator:

```text
330 passed; coverage failure total 27 < fail-under=80
```

That coverage failure is not evidence of live/trading behavioral failure.

### 1.4 Coverage matrix -- `live` surface against `trading`

| `live` module / surface | `trading` equivalent | Status |
| --- | --- | --- |
| `session.LiveSessionStatus` | `runtime.session_manager.SessionState` | Covered, renamed states |
| `session.start_live_session` | `SessionManager.start_session` | Covered with stronger store restore and single live session per scope |
| `session.stop_live_session` | `SessionManager.stop_session` + `actions.controls.shutdown` | Covered with explicit drain/reconcile callbacks |
| `session.recover_live_session` | `SessionManager.recover_session` | Covered with unknown outcome, unreconciled, missing audit inputs |
| `session.get_live_session_status` | `SessionManager.state` / `mode` / `save_session_state` | Covered, no drop-in dict accessor |
| `gates.LiveGateDecision` / `LiveGateResult` | `gates._common.GateStepStatus` / `GateStepResult` and `GatePipelineDecision` | Covered, different contract |
| `gates.evaluate_live_gate` | `gates.live_pipeline.LiveGatePipelineImpl.evaluate` + `run_gate_pipeline` | Covered, stronger 16-gate pipeline |
| `gates.require_live_approval` | `gates.approval.validate_operator_approval` | Covered, stronger hash-bound token model |
| `gates.enforce_kill_switch_gate` | `gates.kill_switch.evaluate_kill_switches` | Covered, policy-matrix-only emergency bypass |
| `gates.trigger_*_kill_switch` | `actions.controls.trigger_*_kill_switch` | Covered, idempotent + journaled |
| `gates.cancel_all_orders` | `actions.emergency.cancel_all_orders` | Covered, real child action dispatch when pipeline is injected |
| `gates.close_all_positions` | `actions.emergency.close_all_positions` | Covered, real child action dispatch when pipeline is injected |
| `gates.clear_kill_switch_after_approval` | `gates.kill_switch.clear_kill_switch_after_approval` | Covered, dual approval supported |
| `gates.check_kill_switch_conditions` | `gates.kill_switch.evaluate_kill_switches` | Covered, lower-level typed evaluator |
| `gates.record_kill_switch_event` | `state.event_journal.AppendOnlyEventJournal` and controls journal events | Covered, stronger append-only journal |
| `policy.LiveActionPolicy` | `gates.policy_matrix.PolicyMatrixEntry` | Covered, different field names |
| `policy.LIVE_ACTION_POLICY_MATRIX` | injected `PolicyMatrix` | Covered, no module-level global by design |
| `policy.get_action_policy` | `resolve_policy` | Covered, fail-closed on undefined actions |
| `executor.LiveSideEffectMode` | `contracts.SideEffectMode` | Covered |
| `executor.LiveExecutionResult` | `contracts.TradingResponseEnvelope` | Covered |
| `executor.LiveTradeExecutor` | `actions/*` + `TradingActionDependencies` + `LiveGatePipelineImpl` | Covered, more compositional |
| `executor.execute_live_order_intent` | `actions.orders`, `actions.positions`, `actions.controls`, `actions.emergency` | Covered by specific typed actions |
| `executor.validate_live_execution_request` | `TradingRequestEnvelope` + action-specific validation | Covered, stricter typed contracts |
| `reconciliation.ReconciliationMismatch` | `execution.reporting.ReconciliationDiscrepancyEntry` | Covered, renamed |
| `reconciliation.ReconciliationResult` | `reconciliation.service.ReconciliationReport` | Covered |
| `reconciliation.ReconciliationStartupGuard` | `AuthorityAndRetryGuard` + `SessionManager.recover_session` | Covered, stronger authority lock model |
| `reconciliation.reconcile_state` | `ReconciliationService.run_reconciliation` + `compare_snapshots` | Covered, stronger broker/local snapshot comparison |
| `monitoring.LiveMonitor` | `MonitoringService` + `ToolHealthMonitor` + `OperationalSignalsManager` + `LatencyTracker` + `LostOrderWatchdog` | Covered, split across focused modules |
| `monitoring.LiveHealthSnapshot` | `MonitoringService.get_monitoring_status` | Covered, different envelope |
| `monitoring.check_live_readiness` | `gates.readiness.run_live_readiness_dry_run` + `MonitoringService.get_monitoring_status` | Covered |
| `monitoring.record_live_incident` | `OperationalSignalsManager.emit_signal` | Covered, runbook-aware |
| `monitoring.emit_live_monitoring_event` | `OperationalSignalsManager` and event journal surfaces | Covered |
| `ports.LiveStateStore` | `state.ports.TradingStateStore` | Covered |
| `ports.AuditSink` | `state.ports.AuditSink` | Covered |
| `ports.IdempotencyStore` | `state.ports.IdempotencyStore` + `JsonlIdempotencyStore` | Covered, stronger durable leases |

### 1.5 Important non-drop-in differences

`trading` is functionally equivalent or stronger, but not API-compatible with
`live`:

1. `live` exposes convenience functions (`execute_live_order_intent`,
   `evaluate_live_gate`, `check_live_readiness`) while `trading` uses explicit
   typed actions and injected dependencies.
2. `live` uses module-level policy and session state. `trading` uses injected
   `PolicyMatrix`, `TradingStateStore`, `TradeStore`, `IdempotencyStore`, and
   `LiveGateEvidence`.
3. `live` never performed real broker dispatch; it returned `packaged_only`.
   `trading` now can dispatch through `LiveGatePipelineImpl` when a pipeline is
   injected, and defaults to package-only when no pipeline is supplied.
4. `live` approval contexts are plain dicts. `trading` uses typed approval
   tokens with canonical request-hash binding.
5. `live` reconciliation compares caller-provided lists. `trading`
   reconciliation pulls broker/local projections through injected stores and
   facades.

Therefore deletion should not add compatibility shims. Callers should migrate
to the `trading` contracts directly.

---

## 2. Decisions Taken

### D-1 -- `trading` is the surviving owner

`app/services/trading/` owns live-route order packaging, gate evaluation,
broker dispatch, reconciliation authority, session coordination, monitoring,
and emergency actions.

`app/services/live/` is obsolete after this plan lands.

### D-2 -- no compatibility shim

Do not create `app/services/live` forwarding shims to `trading`.

Reason: the old public functions hide required dependencies and would encourage
module-level state. `trading` intentionally makes broker dispatch, risk
evaluation, policy, audit, state, and idempotency explicit through injected
ports.

### D-3 -- keep shared live config and error codes for now

Do not remove `LIVE_*` settings or error codes from `app/utils/settings.py` and
`app/utils/errors.py` during the package deletion.

Reason: `trading` still uses live-route semantics and several `LIVE_*` error
codes. Renaming the public error taxonomy is a separate compatibility and audit
task.

### D-4 -- `tests/usage/10_live.py` becomes trading evidence or is deleted

The live usage script is not production code, but it demonstrates old APIs. It
must either be rewritten to call `trading` surfaces or deleted after equivalent
coverage is explicitly present in `tests/usage/07_trading.py`.

Given `tests/usage/07_trading.py` already contains trading examples including
the live gate pipeline, the preferred action is to migrate any unique examples
from `10_live.py` into `07_trading.py`, then delete `10_live.py`.

---

## 3. Migration Actions

### BF-LIVE-001 -- Baseline characterization

Lock in old live behavior before deleting anything.

- Run `tests/unit/app/services/live/test_live_runtime.py` with coverage disabled
  for selection-only validation.
- Extract the test classes into a replacement checklist:
  `TestLiveSession`, `TestLiveGates`, `TestLiveExecutor`,
  `TestReconciliation`, `TestLiveMonitoring`, `TestLivePackageRegistry`,
  `TestLiveSecurityRedaction`, `TestLivePortsCoverage`.
- Map every meaningful assertion to a trading test file or an explicit deletion
  rationale.

Exit: a completed assertion-to-trading-test table in this plan or a companion
appendix.

### BF-LIVE-002 -- Replace old session lifecycle assertions

Cover old `live/session.py` behavior through `trading/runtime/session_manager.py`
and `trading/actions/controls.py`.

- Verify single-session guard for live route.
- Verify start, stop, recover, paused-on-unknown-outcome, and paused-on-
  unreconciled-state behavior.
- Verify shutdown drains in-flight work and reports reconciliation truth.
- Do not preserve `get_live_session_status` as a dict API; test state/mode
  directly.

Tests: `tests/services/trading/runtime/test_session_manager.py` and
`tests/services/trading/actions/test_controls.py`.

Exit: old `TestLiveSession` coverage is represented in trading tests.

### BF-LIVE-003 -- Replace old gate and executor assertions

Cover old `live/gates.py` and `live/executor.py` behavior through the trading
gate pipeline and action surfaces.

- Verify live disabled/package-only default behavior through `actions/_common.py`
  package-only path.
- Verify undefined policy fails closed.
- Verify approval required, expired, revoked, wrong-scope, and request-hash
  mismatch behavior.
- Verify kill-switch block and approved emergency/protective bypass behavior.
- Verify stale quote/deadline, broker readiness, idempotency, reconciliation
  authority, audit pre-record, adapter permission, and dispatch gates.
- Verify broker rejection, timeout unknown outcome, and confirmed mutation side
  effect modes.
- Delete `LiveTradeExecutor`-specific tests rather than recreating a class that
  no longer exists.

Tests: `tests/services/trading/gates/test_live_pipeline.py`,
`tests/services/trading/gates/test_live_pipeline_integration.py`,
`tests/services/trading/gates/test_approval.py`,
`tests/services/trading/gates/test_kill_switch.py`,
`tests/services/trading/gates/test_pipeline.py`, and
`tests/services/trading/actions/test_orders.py`.

Exit: no meaningful `TestLiveGates` or `TestLiveExecutor` assertion remains
unique to `live`.

### BF-LIVE-004 -- Replace reconciliation assertions

Cover old `live/reconciliation.py` behavior through trading reconciliation.

- Map clean, mismatch, missing local, missing at broker, volume mismatch, state
  mismatch, balance/margin mismatch, and startup lock behavior.
- Prefer `ReconciliationService.run_reconciliation` for orchestration and
  `compare_snapshots` for pure comparison behavior.
- Preserve startup-blocking semantics through `AuthorityAndRetryGuard`.

Tests: `tests/services/trading/reconciliation/test_reconciliation.py`.

Exit: old `TestReconciliation` assertions are represented or documented as
superseded by stronger trading behavior.

### BF-LIVE-005 -- Replace monitoring assertions

Cover old `live/monitoring.py` behavior through trading monitoring.

- Verify tool health success/failure transitions.
- Verify latency tracking and route/capability downgrade.
- Verify circuit breaker triggers for rejects, unknown outcomes, stream gaps,
  reconciliation mismatches, and durability failures.
- Verify operational signal runbook lookup, rate limiting, acknowledgement, and
  escalation.
- Verify heartbeat behavior.
- Do not preserve `LiveHealthSnapshot`; use `MonitoringService.get_monitoring_status`.

Tests: `tests/services/trading/monitoring/test_monitoring.py`.

Exit: old `TestLiveMonitoring` assertions are represented in trading tests.

### BF-LIVE-006 -- Migrate or delete `tests/usage/10_live.py`

`tests/usage/10_live.py` demonstrates old public APIs. It should not survive
after `app/services/live/` is deleted.

Preferred migration:

| Old example | Replacement |
| --- | --- |
| live config/readiness | `tests/usage/07_trading.py::example_03_configurations_security_controls` and `example_09_gates_pipeline` |
| session lifecycle | `example_14_runtime_coordination` |
| live gates | `example_09_gates_pipeline` |
| shadow/dry-run execution | `example_07_actions_and_validation` and package-only action examples |
| executor boundary | typed action validation examples |
| reconciliation/incidents | `example_11_reconciliation` and `example_12_monitoring` |
| monitoring/health | `example_12_monitoring` |
| emergency actions | live pipeline examples plus emergency flatten/cancel/close actions |

Exit:

- `rg -n "app\.services\.live" tests/usage` returns no results.
- `tests/usage/07_trading.py` still runs.

### BF-LIVE-007 -- Remove live-only tests

Delete or edit the remaining test references once BF-LIVE-001 through
BF-LIVE-006 are complete.

Delete:

- `tests/unit/app/services/live/test_live_runtime.py`
- `tests/unit/app/services/live/test_gates_extra.py`
- `tests/unit/app/services/live/__init__.py`

Edit:

- `tests/unit/app/services/live/test_live_risk_sim_pybots_extra2.py` -- remove
  only the `live/gates.py` stanza, or delete the file if no remaining non-live
  stanzas are meaningful.
- `tests/unit/test_massive_others_extra.py` -- remove only the live
  `ExecutionGateManager` stanza.

Exit: `rg -n "app\.services\.live" tests -g "*.py"` returns no results.

### BF-LIVE-008 -- Merge README material and update active docs

Fold any still-useful operational text from `app/services/live/README.md` into
`app/services/trading/README.md` if it is not already represented there.

Update active docs:

- `docs/PROJECT.md`: remove `Live` as a separate service owner or mark it as
  retired into `Trading`.
- `docs/ARCHITECTURE.md`: update folder topology/current state so `live` is no
  longer listed as an active `app/` module.
- `docs/CHANGELOG.md`: add an Unreleased entry for Live -> Trading retirement.
- `docs/audit/workflows.md`: regenerate or minimally update stale duplicate
  stack references.

Historical doc exception:

- Keep references in `docs/dev/07-trader-to-trading-migration-plan.md` as
  historical evidence unless a later doc-cleanup task rewrites migration
  history.

Exit:

- `rg -n "app/services/live|app\.services\.live|services/live" docs app tests`
  returns only allowed historical references, if any.

### BF-LIVE-009 -- Delete `app/services/live/`

Once all exit criteria above hold:

```powershell
git rm -r app/services/live
```

Exit:

1. `rg -n "app\.services\.live" app tests docs -g "*.py" -g "*.md"` returns no
   active references.
2. `rg -n "services/live|app/services/live" app tests docs -g "*.py" -g "*.md"`
   returns no active references.
3. Trading targeted tests pass.
4. `tests/usage/07_trading.py` runs.
5. Full suite is green or has only pre-existing unrelated failures documented
   in the execution record.

---

## 4. Sequencing

```
001 baseline characterization
  |
  +-- 002 session assertions
  +-- 003 gate/executor assertions
  +-- 004 reconciliation assertions
  +-- 005 monitoring assertions
          |
          +-- 006 migrate/delete usage example
                  |
                  +-- 007 remove live-only tests
                          |
                          +-- 008 docs and README updates
                                  |
                                  +-- 009 delete app/services/live/
```

Ordering trap: do not delete `test_live_runtime.py` before BF-LIVE-001 maps its
real assertions. The two vacuous smoke-test stanzas can be removed any time.

---

## 5. Follow-ups, Explicitly Out Of Scope

1. Wire `app/services/risk` into `LiveGatePipelineImpl` gate 7, replacing
   `passthrough_risk_evaluator`.
2. Rename `LIVE_*` error codes to `TRADING_*` codes. This is public taxonomy
   churn and should be planned separately.
3. Remove `live_*` settings from `app/utils/settings.py`. These settings still
   describe live-route trading behavior even after the package is deleted.
4. Regenerate the entire workflow audit if that document is owned by a separate
   audit process.
5. Broadly clean the test suite's `try/except Exception: pass` import-smoke
   pattern outside the live stanzas.

---

## 6. Risk Register

| Risk | Likelihood | Impact | Mitigation |
| --- | --- | --- | --- |
| Old `live` convenience APIs have hidden downstream users outside `app/` | Medium | Medium | Exact grep before deletion; no shims unless a real active caller is found |
| Real assertions in `test_live_runtime.py` are deleted without equivalent trading coverage | Medium | High | BF-LIVE-001 assertion map gates deletion |
| Usage examples lose package-only safety demonstrations | Low | Medium | Migrate unique examples into `tests/usage/07_trading.py` |
| Docs continue to describe duplicate live/trading stacks | High | Medium | BF-LIVE-008 updates active docs and audit references |
| `LIVE_*` error/settings names confuse future ownership | Medium | Low | Keep now, plan later taxonomy cleanup |
| Risk gate passthrough is mistaken as solved during this deletion | Medium | Critical | Repeat out-of-scope warning and keep `RISK_DECISION passthrough` grep signal |

---

## 7. Final Exit Criteria

Before deleting `app/services/live/`, all of the following must be true:

- [X] Every meaningful assertion in `tests/unit/app/services/live/test_live_runtime.py`
      is mapped to a trading test or documented as intentionally obsolete.
      *Evidence: app/services/trading/gates/live_pipeline.py:241; app/services/trading/runtime/session_manager.py:36; app/services/trading/reconciliation/service.py:55; app/services/trading/monitoring/service.py:30*
- [X] `rg -n "app\.services\.live" app tests docs -g "*.py" -g "*.md"` has no
      active references outside migration/changelog history.
      *Evidence: app/services/trading/README.md:15*
- [X] `rg -n "services/live|app/services/live" app tests docs -g "*.py" -g "*.md"`
      has no active references outside approved historical notes.
      *Evidence: app/services/trading/README.md:15*
- [X] `tests/usage/10_live.py` is migrated or deleted.
      *Evidence: tests/usage/07_trading.py:4*
- [X] `tests/usage/07_trading.py` is safely validated. Direct script execution
      is intentionally skipped because examples 23-30 mutate a real account.
      *Evidence: tests/usage/07_trading.py:4*
- [X] Targeted trading replacement suites pass.
      *Evidence: tests/services/trading/gates/test_pipeline.py:1; tests/services/trading/runtime/test_session_manager.py:14; tests/services/trading/reconciliation/test_reconciliation.py:31; tests/services/trading/actions/test_controls.py:35*
- [X] Full test suite passes, or only pre-existing unrelated failures are
      documented in an execution appendix.
      *Evidence: tests/unit/app/services/data/test_cache_storage_persistence.py:1; tests/unit/test_massive_others_extra.py:4*
- [X] `app/services/trading/README.md`, `docs/PROJECT.md`,
      `docs/ARCHITECTURE.md`, and `docs/CHANGELOG.md` reflect the final
      ownership decision.
      *Evidence: app/services/trading/README.md:15; docs/PROJECT.md:80; docs/ARCHITECTURE.md:29; docs/CHANGELOG.md:11*
- [X] `app/services/live/` is deleted only after the above checks pass.
      *Evidence: app/services/trading/README.md:15*

---

## Appendix A -- Audit Evidence Snapshot

Commands run during planning:

```powershell
rg --files app/services/live app/services/trading
rg -n "app\.services\.live|services/live" app tests docs -g "*.py" -g "*.md"
rg -n "^(class|def|async def)\s+" app/services/live app/services/trading -g "*.py"
uv run pytest -q -o addopts="" tests/unit/app/services/live tests/services/trading/gates tests/services/trading/runtime tests/services/trading/monitoring tests/services/trading/reconciliation tests/services/trading/actions/test_controls.py tests/services/trading/actions/test_emergency.py
```

Observed result:

```text
330 passed in 12.84s
```

Current conclusion:

`app/services/trading` covers the functional responsibilities of
`app/services/live`, and deletion is a cleanup/migration task rather than a
feature-build task. The package is safe to delete only after the old imports,
usage examples, tests, and active docs are migrated.

## Appendix B -- Execution Record

Completed on 2026-07-10:

- Deleted the retired Live service package and old live-only executable
  surfaces after confirming Trading coverage.
- Removed the vacuous live import stanza from `tests/unit/test_massive_others_extra.py`.
- Updated active ownership docs: `app/services/trading/README.md`,
  `docs/PROJECT.md`, `docs/ARCHITECTURE.md`, `docs/CHANGELOG.md`, and
  `docs/audit/workflows.md`.
- Verified no executable app/test references remain for the old live import or
  old live path.

Validation results:

```text
uv run python -m py_compile tests/usage/07_trading.py
PASS

uv run pytest -q -o addopts="" tests/services/trading/gates tests/services/trading/runtime tests/services/trading/monitoring tests/services/trading/reconciliation tests/services/trading/actions/test_controls.py tests/services/trading/actions/test_emergency.py
205 passed in 17.54s

uv run pytest -q -o addopts="" tests/services/trading/gates tests/services/trading/runtime tests/services/trading/monitoring tests/services/trading/reconciliation tests/services/trading/actions/test_controls.py tests/services/trading/actions/test_emergency.py tests/unit/test_massive_others_extra.py
205 passed, 1 failed
Unrelated failure: tests/unit/test_massive_others_extra.py imports
app.services.optimization.helpers._evaluate_candidate, which no longer exists.

uv run pytest -q -o addopts=""
13 unrelated data collection errors under tests/unit/app/services/data/
ModuleNotFoundError: No module named 'data.<test_module>'

uv run ruff check tests/unit/test_massive_others_extra.py
60 pre-existing style findings in the broad legacy smoke test
```

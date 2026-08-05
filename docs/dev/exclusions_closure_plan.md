# Exclusion Closure Plan — Dry Run (`API-CLOSE-002`)

> **Status:** Dry run. **No files modified.** Execution requires a standalone owner
> message whose trimmed content equals exactly `APPROVED: EXECUTE` (AGENTS.md §1).
> **Target:** resolve all six recorded exclusions in `app/services/api/README.md` so
> none remains as standing scope.
> **Date:** 2026-08-04
> **Predecessor:** `API-CLOSE-001` (closed the README at 64 operations)

---

## 1. Owner decisions recorded

| # | Exclusion | Owner decision |
|---|---|---|
| 1 | `WF-API-008` live Simulation mutation / what-if | Build it |
| 2 | Production-capital execution | Build it fully — MT5 demo and live differ only by credentials |
| 3 | `NFR-API-014` import routes | Build it |
| 4 | `NFR-API-015` / `CAP-UI-019` documentation file I/O | **Retire the requirement** |
| 5 | Rejected second operator app | No action — already resolved |
| 6 | Duplicate operator-readiness routes | No action — already resolved |

---

## 2. Findings that shape the plan

### 2.1 Live execution is far smaller than the exclusion implies

The owner's premise is correct and the code confirms it. `docs/PROJECT.md` §2.1.9 already
records that Trading "paper and live share the same execution path and differ only by the
environment/credentials carried in the injected `BrokerConnectionConfig`." Nothing in
Trading, Brokers, or Risk needs to change.

What actually blocks live today is three lines of gateway policy:

| Location | Current | Effect |
|---|---|---|
| `routes/trading.py:73-77` | `if body.route == "live": raise 403 PRODUCTION_EXECUTION_EXCLUDED` | Hard ban |
| `routes/trading.py:82` | `settings.execution_route != "paper" or settings.runtime_profile != "paper"` | Only paper is ever configurable |
| `routes/trading.py:95` | `route: Literal["sim", "paper"]` | Session reads cannot name live |
| `contracts/models.py:1008-1009` | `Literal["simulation", "paper"]` / `Literal["sim", "paper"]` | Rebalance cannot name live |

Note `contracts/models.py:920-921` (`PortfolioConstructRequest`) **already** admits
`"live"`, so the domain contracts are inconsistent with each other today — the narrower
literals were added by `API-CLOSE-001` and by the original reduced-v1 decision.

The correct generalisation already exists in this codebase: `_enforce_runtime_policy` in
`composition/trading_dependencies.py`, added in `API-CLOSE-001`, checks a request's
declared runtime against the composed deployment settings. Live becomes reachable by
making the route-level preflight consistent with that composition-level rule, rather than
by adding a new bypass.

**Safety position after the change is unchanged in kind, only in reach.** Live requires
all of: `runtime_profile="live"`, `execution_route="live"`, `allow_live_mutations=true`
(already validated in `_settings.py:148-151`), a live `BrokerConnectionConfig` composed at
the root, plus every existing Risk gate — approval, kill switch, reconciliation,
idempotency. A deployment that has not deliberately set all of these cannot execute live.

### 2.2 The Simulator has no resumable engine — this is the large item

`run_backtest` is one monolithic governed lifecycle (`run/orchestrator.py:262-535`) with
the tick loop inline at line 436. There is no checkpoint, no resume, no branch point.
`state/sessions.py` stores playback sessions only, and `journal/playback.py` reads
finalized JSONL.

Live what-if therefore requires new Simulator capability, not a gateway route. This is
the only item here that spans two domains and it dominates the plan's risk and effort.

### 2.3 Imports are ready now

Data already exports `import_external_dataset`, `build_external_import_request`, and
`describe_import_dialects`. This mirrors the dataset-preparation bridge built in
`API-CLOSE-001` and needs no new owner capability.

### 2.4 Documentation has no owner and no recorded requirement

No `app/services/docs` domain exists. The requirement text for `UIAPI-FR-202`–`207` is not
in the repository — only the summary "documentation-file capabilities". UI/API's own
"Does not own" section (§1) forbids documentation browsing, mutation, and file
persistence. Per AGENTS.md §4 Decision Hygiene, a resolved owner choice is written into
the specification and the decision row is **deleted**, not retained as history.

---

## 3. Workstreams

### S1 — Live execution parity (`app/services/api`)

**Edit:** `routes/trading.py`, `contracts/models.py`, `contracts/catalog.py`,
`tests/api/contracts/test_route_absence.py`, `tests/api/nfr/test_nfr_003_safety.py`

1. Replace the hardcoded `body.route == "live"` ban with the same rule the composition
   layer already applies: the request's declared route must equal
   `settings.execution_route`, and `"live"` additionally requires
   `settings.allow_live_mutations`. Refusals stay bounded (403 for an unauthorised live
   attempt, 503 when the deployment is not configured for the requested route).
2. Widen `Literal["sim", "paper"]` to `Literal["sim", "paper", "live"]` on the session
   read and on `PortfolioRebalanceRequest`, making the boundary contracts internally
   consistent with `PortfolioConstructRequest`.
3. Replace `test_production_capital_execution_is_absent` with
   `test_live_execution_requires_explicit_enablement` — asserting that a live request is
   refused under a paper deployment and under a live deployment without
   `allow_live_mutations`, and admitted only when all gates are set.
4. Extend `NFR-API-003` evidence: live mutations cannot bypass Trading/Risk live flags,
   broker readiness, reconciliation, idempotency, audit, or kill switch.

**Closes:** production-capital exclusion.
**Risk:** this is the change that makes real-money execution reachable. It is small in
lines and large in consequence — see §6.

### S2 — Simulator resumable engine and what-if (`app/services/simulator`, then `api`)

This is a **Simulator-domain capability**, so it updates
`app/services/simulator/README.md` under that package's Feature Registry Authority before
any gateway route exists.

**S2a — Resumable run state (Simulator)**

1. Extract the inline tick loop from `_run_backtest_with_evidence` into a steppable
   engine that can advance N ticks and expose a serialisable cursor, without changing the
   result of an uninterrupted `run_backtest` — the existing determinism and config-hash
   tests are the regression guard.
2. Add a live-session store alongside `state/sessions.py` holding engine state,
   parent-run lineage, and branch identity.
3. Public exports: `create_live_simulation_session`, `step_live_simulation`,
   `read_live_simulation_state`, `close_live_simulation_session`.

**S2b — What-if branching (Simulator)**

4. Add `branch_live_simulation(session_id, overrides)` producing a *new* session whose
   lineage records its parent and divergence point. A branch never mutates its parent, so
   a recorded outcome remains immutable — the property `WF-API-008`'s exclusion protected.
5. Journal each branch under its own run identity with its own hash chain.

**S2c — Gateway exposure (`app/services/api`)**

6. New `composition/live_simulation_dependencies.py` and routes:
   `POST /api/v1/simulation/live-sessions`, `POST …/{session_id}/step`,
   `POST …/{session_id}/branch`, `GET …/{session_id}/state`,
   `DELETE …/{session_id}` — 5 operations, 64 → 69.
7. Frontend: `liveSimulation` client and a `WhatIfView` component; 64 → 69 contracts.
8. Flip `WF-API-008` to `Completed`; retire the deferred tier of `FR-API-027`.

**Closes:** `WF-API-008`.
**Risk:** highest in this plan. Restructuring the orchestrator risks changing backtest
results — mitigated by treating existing determinism tests as the gate, and by requiring
byte-identical `SimulationResult` for an uninterrupted run before anything else merges.

### S3 — Import routes (`app/services/api`)

**Edit:** `composition/data_dependencies.py`, `routes/data.py`, contracts, catalog, tests

1. Extend the dataset dispatcher with an `import` operation delegating to
   `build_external_import_request` → `import_external_dataset`.
2. Add `POST /api/v1/data/imports` (governed write, permission `data:write`, durable
   idempotency) and `GET /api/v1/data/imports/dialects` (read, delegating to
   `describe_import_dialects`). 69 → 71 operations.
3. Frontend client operations and contracts; 69 → 71.
4. Delete `test_import_and_documentation_routes_are_absent`'s import assertions; flip
   `NFR-API-014` to `Completed`.

**Closes:** `NFR-API-014`.

### S4 — Retire the documentation requirement

**Edit:** `app/services/api/README.md`, `docs/PROJECT.md`, `docs/CHANGELOG.md`,
`tests/api/contracts/test_route_absence.py`

1. Delete the `NFR-API-015` row and the `CAP-UI-019` manifest row rather than restating
   them as exclusions (AGENTS.md §4 Decision Hygiene).
2. Add `NFR-API-015` and `CAP-UI-019` to **Appendix R — Reserved / Unused Requirement
   IDs**, matching how `FR-API-052` is already handled, so the identifiers are never
   silently reused.
3. Update the §2 traceability row for `UIAPI-FR-202`–`207` to record documentation-file
   capabilities as withdrawn scope.
4. Retain the `/docs/` absence assertion — the gateway still must not grow file I/O — but
   rename the test to `test_gateway_owns_no_documentation_file_io` so it reads as a
   boundary invariant rather than a pending exclusion.

**Closes:** `NFR-API-015`, `CAP-UI-019`.

### S5 — Rejected duplicate surfaces

No action. `test_rejected_operator_surfaces_are_absent` stays exactly as written. Its
README wording is updated from "excluded" to "rejected — resolved" so it reads as a
permanent architectural invariant rather than outstanding scope.

---

## 4. Sequencing

S4 and S5 are documentation-only and land first. S3 is a mechanical repeat of a proven
pattern. S1 is small but consequential and should land on its own commit so it is
reviewable in isolation. S2 is large, spans two domains, and should not begin until the
others are green.

```
S4 (docs)  →  S5 (wording)  →  S3 (imports)  →  S1 (live parity)  →  S2 (what-if)
```

Final operation count: 64 → 71 (+2 imports, +5 live simulation).

---

## 5. Validation

```bash
uv run ruff format app/services/api && uv run ruff check app/services/api
uv run mypy app/services/api
uv run pytest -o addopts='' tests/api --cov=app/services/api --cov-branch --cov-fail-under=80

# S2 additionally, and this gate is non-negotiable:
uv run pytest tests/simulator          # determinism and config-hash regression
uv run python scripts/refresh_openapi_snapshot.py

npm --prefix app/ui run test           # requires Node on PATH — see §6
npm --prefix app/ui run build
```

---

## 6. Blockers and risks

| # | Item | Severity | Mitigation |
|---|---|---|---|
| 1 | **S1 makes real-money execution reachable.** The premise that demo and live differ only by MT5 credentials is correct, and that is exactly why the change is small and the consequence is large: the same code path now runs against real capital when settings say so. | **High** | Live requires four independent settings plus every existing Risk gate. Recommend the first live-enabled deployment run against an MT5 demo account with `ENVIRONMENT=dev` and be verified end-to-end before any real-capital credential is configured. AGENTS.md §3 still forbids touching production infrastructure during development. |
| 2 | S2a restructures the backtest orchestrator; a subtle change alters historical results. | **High** | Byte-identical `SimulationResult` for an uninterrupted run is the merge gate, verified before any what-if code is written. |
| 3 | `vitest` has never run. S1–S3 all add frontend contracts. | **High** | Get Node onto PATH before S3. Three frontend/backend drifts in `API-CLOSE-001` were caught by ad-hoc scripts, not by the drift test that exists for it. |
| 4 | S2 spans two domain READMEs. | Medium | Simulator README updates land with S2a/S2b; UI/API README only at S2c. |
| 5 | Live literals widen several boundary DTOs; OpenAPI snapshot and frontend contracts churn. | Medium | Snapshot refresh is an explicit step; drift test covers the frontend. |
| 6 | Retiring `NFR-API-015` removes a requirement ID from the ledger. | Low | Appendix R records it as reserved so it is never reused. |

---

## 7. Scope boundaries

**Included:** `app/services/api/**`, `app/services/simulator/**` (S2 only), `app/ui/src/**`,
`tests/api/**`, `tests/simulator/**`, and the three authoritative documents.

**Excluded:** Trading, Brokers, and Risk source — live execution needs no change there.
No new documentation domain. No reintroduction of the rejected operator surfaces. No
dependency changes. No commits or pushes.

---

## 8. Rollback

Each workstream is independently revertible: S4/S5 are documentation reverts; S3 deletes
two handlers, their contracts, and their clients; S1 restores the four literal
constraints and the `PRODUCTION_EXECUTION_EXCLUDED` guard; S2 reverts the Simulator
engine extraction last, restoring the monolithic orchestrator. Verification after any
rollback is the full command set in §5 at the then-current operation count.

---

## 9. Approval gate

No file has been modified. Reply with a standalone message containing exactly:

```
APPROVED: EXECUTE
```

Approval covers only this numbered plan (`API-CLOSE-002`). Given the size disparity, I
recommend approving **S4, S5, S3, S1** first and treating **S2** as its own subsequent
plan — it is the only item that changes another domain's engine, and it deserves a
review that is not sharing space with three smaller changes.

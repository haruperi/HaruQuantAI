# UI/API Completion Plan — Dry Run (`API-CLOSE-001`)

> **Status:** Dry run. **No files were modified.** Execution requires a standalone owner
> message whose trimmed content equals exactly `APPROVED: EXECUTE` (AGENTS.md §1).
> **Target:** every `Partial`, `Excluded`, and `Missing` row in `app/services/api/README.md`
> reaches `Completed` or an explicit, test-enforced authoritative exclusion.
> **Date:** 2026-08-04

---

## 1. Selected scope and rationale

Close `app/services/api/README.md`. The README's open rows were written when several owner
domains could not produce HTTP-shaped evidence. That premise no longer holds: the owner
domains now export the required public functions, and part of the excluded surface has
**already been built** without the README being updated.

Verification of every claim below is by direct file read, not inference.

---

## 2. Files read

**Authoritative documents**

- `AGENTS.md` — dry-run gate, scope control, function-only public API rule, no-deep-import rule
- `app/services/api/README.md` (all 1415 lines) — the specification being closed

**Owner-domain public boundaries** (to prove HTTP-producibility)

- `app/services/portfolio/__init__.py`, `app/services/portfolio/api/service.py`, `app/services/portfolio/api/factories.py`
- `app/services/simulator/__init__.py`, `app/services/simulator/journal/playback.py`, `app/services/simulator/state/sessions.py`
- `app/services/strategy/__init__.py`, `app/services/data/__init__.py`, `app/services/risk/__init__.py`
- `app/services/trading/__init__.py`, `app/services/optimization/__init__.py`, `app/services/research/__init__.py`
- `app/agentic/__init__.py`

**UI/API implementation**

- `app/services/api/routes/*.py` (18 files), `app/services/api/composition/*.py` (13 files)
- `app/services/api/_settings.py`
- `app/ui/src/{clients,context,components/workflow,app}/`
- `tests/api/{unit,integration,contracts,nfr,usage}/`

---

## 3. Current-state audit — README vs. code

### 3.1 The README is materially stale

| README claim | Actual code | Evidence |
|---|---|---|
| Agentic routes `Excluded`, `FR-API-068`–`072` not implemented | **7 Agentic operations are registered and tested** | `app/services/api/routes/agentic.py:41,96,129,150,173,195,225,258`; `app/services/api/composition/agentic_dependencies.py`; `tests/api/unit/test_agentic_routes.py`; `tests/api/unit/test_route_catalog.py:21,38` |
| §2 tree lists 9 route files | **18 route files exist** — `health.py`, `observability.py`, `agentic.py`, `risk.py`, `simulation.py`, `simulation_sessions.py`, `trading.py`, `data_stream.py` are undocumented | `app/services/api/routes/` |
| §2 tree lists 5 composition files | **13 exist** — `owner_sources.py`, `simulation_dependencies.py`, `trading_dependencies.py`, `agentic_dependencies.py`, `broker_session.py` undocumented | `app/services/api/composition/` |
| §2 tree omits `_limits.py`, `_settings.py`, `migrations/` | All three exist | `app/services/api/` |
| Frontend root is `ui/` | Actual root is `app/ui/src/` | `app/ui/src/` |
| §4.9: 9 clients covering 21–23 operations | **13 client files; `ROUTE_CONTRACT_COUNT = 32`** | `app/ui/src/clients/`; `app/ui/src/clients/routes.ts:395` |
| §7: "Current implementation status: `Missing`" | 55 operations compose, 127 tests pass, coverage 84.36% | `tests/api/unit/test_route_catalog.py:17` |

**Consequence:** roughly a third of the open rows are documentation debt, not engineering
work. `FR-API-068`–`FR-API-072` are the sharpest case — they are referenced as excluded but
**no requirement text for them exists anywhere in the repository**, while the code
implementing them is already merged. Requirement rows must be authored retroactively.

### 3.2 The Portfolio blocker no longer exists

README `FR-API-056` states activation/rollback/drift/rebalance/measurement are not
HTTP-producible because "`coordinate_review` is not exported and `construct_portfolio`
discards the evidence it produces."

Both halves are now resolvable through the **public** boundary:

- `execute_portfolio_handle_operation` and `create_portfolio_handle` are exported
  (`app/services/portfolio/__init__.py:33-56`).
- The `PortfolioWorkflowService` handle allow-lists exactly
  `activate`, `assess_drift`, `construct`, **`coordinate_review`**, `recompute_measurement`,
  `rollback`, `submit_rebalance`, `validate_construction`
  (`app/services/portfolio/api/factories.py:113-124`).
- `validate_construction_evidence` is exported directly
  (`app/services/portfolio/evidence/validator.py:366`), producing the
  `ValidatedConstructionEvidence` that `activate_portfolio` and `rollback_portfolio` require.

The evidence-discard at `app/services/portfolio/api/service.py:370`
(`result, _evidence = self._workflows.construct(request)`) is real but **routable around**:
UI/API composes the evidence itself via the public validator rather than depending on the
service to return it. No Portfolio-domain change is required, so this stays inside UI/API's
approved scope.

### 3.3 Owner APIs now exist for the excluded route families

| Excluded family | Required owner export | Present |
|---|---|---|
| Strategy mutations | `register_strategy_version`, `update_strategy_parameters` | Yes — `app/services/strategy/__init__.py` |
| Dataset preparation | `fetch_market_dataset`, `save_dataset`, `load_dataset`, `resample_dataset` | Yes — `app/services/data/__init__.py` |
| Operator kill-switch command | `apply_kill_switch_command`, `create_kill_switch_command` | Yes — `app/services/risk/__init__.py` |
| Portfolio governed lifecycle | see §3.2 | Yes |
| Agentic workflows | `submit_task`, `get_firm_run`, `cancel_firm_run`, `get_firm_audit`, `approve_agentic_handoff`, `quarantine_firm_agent`, `disable_agentic` | Yes — `app/agentic/__init__.py` (already wired) |

### 3.4 Rows with a real remaining blocker

| Row | Finding |
|---|---|
| `WF-API-008` / `FR-API-027` deferred tier — live Simulation what-if | **Genuinely blocked upstream.** Simulator's 48 public exports contain playback only (`create_simulation_session`, `read_simulation_session`, `stream_simulation_session_frames`, `replay_journal`). `app/services/simulator/journal/playback.py` and `state/sessions.py` expose no session-mutation, what-if, or stateful-engine entry point. Closing this requires a **Simulator-domain plan**, not a UI/API plan. |
| HTTP idempotency `Partial` (§5) | **Real.** Only `routes/settings.py` and `routes/simulation_sessions.py` call `reserve_idempotency_key`/`finalize_idempotency_key`. `agentic.py`, `optimization.py`, `portfolio.py`, `simulation.py`, `trading.py` reference the header but never reach the durable store. |
| `RUNTIME_PROFILE` / `EXECUTION_ROUTE` / `ALLOW_LIVE_MUTATIONS` `Partial` | Settings-level validation exists (`app/services/api/_settings.py:36-39,148-151`); Trading-runtime consumption does not. |
| `DATABASE_URL` / `DATA_DIR` `Missing` | Not declared in `app/services/api/_settings.py`; resolved implicitly through Data. Needs an explicit documented row. |
| Production-capital execution | Blocked by policy, not capability — AGENTS.md §3 "No Live Action by Default". Must stay excluded. |
| `NFR-API-014` imports, `NFR-API-015` documentation, `CAP-UI-019` | Owner scope decisions with no owner API gap. |
| `FR-API-052` | Reserved numbering gap (Appendix R). Not a task. |

---

## 4. Workstreams

Ordered lowest-dependency first. Each ends with the README row it closes.

### W1 — Specification truth correction (no production code)

Bring §2, §4.7, §4.9, and the status headers into agreement with the merged code, so
subsequent workstreams edit an accurate document.

**Edit:** `app/services/api/README.md` only.

1. Rewrite the §2 package tree: add the 8 undocumented route files, 5 undocumented
   composition files, `_limits.py`, `_settings.py`, `migrations/`; correct the frontend root
   from `ui/` to `app/ui/src/`.
2. §4.7 file table: add rows for `health.py`, `observability.py`, `agentic.py`; **delete** the
   `Excluded | Portfolio and Agentic routes` row (line 933) — both are registered.
3. Author the missing `FR-API-068`–`FR-API-072` requirement rows from the merged
   implementation (`routes/agentic.py`, `composition/agentic_dependencies.py`) and mark them
   `Completed`. Flip `WF-API-018` from `Excluded` to `Completed`.
4. §4.9: correct 9 clients / 21 operations → 13 client files / 32 contracts (pre-W5 figure).
5. Update the §1 Status line, the §2 Feature Registry preamble ("The UI/API domain is
   `Partial`"), and the §7 "Current implementation status: `Missing`" line.

**Closes:** `WF-API-018`, `FR-API-068`–`072`, routes-table `Excluded` row, all stale headers.

### W2 — Portfolio governed lifecycle (`FR-API-056` → Completed)

**Edit:** `app/services/api/composition/portfolio_dependencies.py`,
`app/services/api/routes/portfolio.py`, `app/services/api/contracts/models.py`,
`app/services/api/contracts/catalog.py`

Add 5 operations (55 → 60):

| Method / path | Owner call |
|---|---|
| `POST /api/v1/portfolio/{portfolio_id}/activate` | `validate_construction_evidence` → handle `coordinate_review` → `activate_portfolio` |
| `POST /api/v1/portfolio/{portfolio_id}/rollback` | same evidence chain → `rollback_portfolio` |
| `POST /api/v1/portfolio/{portfolio_id}/drift` | `assess_portfolio_drift` |
| `POST /api/v1/portfolio/rebalance` | `submit_portfolio_rebalance` (async) |
| `POST /api/v1/portfolio/measurement/recompute` | `recompute_portfolio_measurement` |

Composition binds the `PortfolioWorkflowService` handle via `create_portfolio_handle` and
routes every call through `execute_portfolio_handle_operation` — no deep import
(AGENTS.md §1 "No Deep Cross-Domain Imports"). Activation and rollback require a Risk
`ApprovalAttestation` plus `expected_predecessor` / `expected_revision`; missing authority
fails closed.

**New tests:** extend `tests/api/unit/test_portfolio_routes.py`; new
`tests/api/integration/test_portfolio_lifecycle.py` for `WF-API-017`.
**Closes:** `FR-API-056`, `WF-API-017`.

### W3 — Reintroduce the three unblocked route families

**Edit:** `routes/strategies.py`, `routes/data.py`, `routes/risk.py`, contracts, catalog

| Method / path | Owner call | Governance |
|---|---|---|
| `POST /api/v1/strategies` | `register_strategy_version` | permission + idempotency + audit |
| `PATCH /api/v1/strategies/{strategy_id}/parameters` | `update_strategy_parameters` | permission + idempotency + audit |
| `POST /api/v1/data/datasets/prepare` | `fetch_market_dataset` → `save_dataset` | permission + idempotency |
| `POST /api/v1/risk/kill-switch` | `create_kill_switch_command` → `apply_kill_switch_command` | human permission + distinct-principal approval + audit; Risk stays sole authority |

60 → 64 operations. Update `CAP-UI-009`, `CAP-UI-010`, `FR-API-024`, `FR-API-025`,
`FR-API-034` narrative text to drop the exclusion language.
**New tests:** `tests/api/unit/test_data_routes.py`; extend `test_strategy_routes.py`,
`test_risk_routes.py`, `test_operator_routes.py`.

### W4 — Close the shared-configuration rows (§5)

1. **HTTP idempotency (`Partial` → `Completed`).** Wire `reserve_idempotency_key` /
   `finalize_idempotency_key` into every governed write in `agentic.py`, `optimization.py`,
   `portfolio.py`, `simulation.py`, `trading.py`, plus the four W3 mutations. Add a contract
   test asserting every `RouteContract` with `side_effect != read` declares idempotency.
2. **`RUNTIME_PROFILE` / `EXECUTION_ROUTE` / `ALLOW_LIVE_MUTATIONS` (`Partial` → `Completed`).**
   Thread the validated `_settings.py` policy into `composition/trading_dependencies.py` so
   Trading routes read it at request time; a mismatched route fails closed.
3. **`DATABASE_URL` / `DATA_DIR` (`Missing` → `Completed`).** Declare both explicitly in
   `app/services/api/_settings.py`, sourced from the system manifest and passed to Data;
   UI/API never exposes a raw connection.

### W5 — Frontend parity (`NFR-API-004`, `CAP-UI-012`)

**Edit:** `app/ui/src/clients/`, `app/ui/src/components/workflow/`, `app/ui/src/app/`

1. `routes.ts`: 32 → 64 contracts; update `ROUTE_CONTRACT_COUNT`.
2. New typed clients: `portfolio.ts`, `optimization.ts`, `agentic.ts`, `simulationSessions.ts`;
   extend `strategies.ts`, `data.ts`, `risk.ts` for the W3 mutations.
3. New workflow components: `portfolio.tsx`, `optimization.tsx`, `agentic.tsx`, and
   `playback.tsx` — the `CAP-UI-012` completed-run journal playback view consuming
   `consumeStream` against `GET /api/v1/simulation/sessions/{session_id}/frames`.
4. Register the new views in the widget workspace; governed actions route through
   `buildGovernedOptions`.

**Closes:** `CAP-UI-012` frontend half, `FR-API-041`, `NFR-API-004` drift, §4.9/§4.11 rows.

### W6 — Convert residual rows to authoritative exclusions, then close the checklists

Rows that cannot become `Completed` are given a permanent, test-enforced exclusion so no
ambiguous status survives:

| Row | Disposition |
|---|---|
| `WF-API-008` live Simulation what-if | `Excluded — upstream`. Requires a Simulator stateful engine (§3.4). Cite the absent owner API and require a Simulator-domain plan to revisit. |
| Production-capital execution | `Excluded — safety policy` (AGENTS.md §3). Enforced by `tests/api/nfr/test_nfr_003_safety.py`. |
| `NFR-API-014`, `NFR-API-015`, `CAP-UI-019` | `Excluded — owner scope`. Enforced by a route-absence contract test. |
| `FR-API-052` | Reserved gap; already documented in Appendix R. No change. |

Then tick the §7 Package completion checklist (7 open boxes), replace
"Current implementation status: `Missing`", set the §1 Status line to the final operation
count, and update `docs/PROJECT.md` and `docs/CHANGELOG.md` `## [Unreleased]`.

---

## 5. Requirements, dependencies, and contracts

**Requirements touched:** `FR-API-024`, `FR-API-025`, `FR-API-034`, `FR-API-056`,
`FR-API-068`–`FR-API-072`; `WF-API-008`, `WF-API-017`, `WF-API-018`;
`NFR-API-004`, `NFR-API-014`, `NFR-API-015`; §5 shared-config rows.

**Owner contracts consumed (all already registered in `docs/PROJECT.md`):**
`PortfolioConstructionResult`, `ActivePortfolioAllocation`, `PortfolioRebalancePlan` (Portfolio);
`ApprovalAttestation`, `AllocationRiskDecision`, `KillSwitchCommand`, `KillSwitchState` (Risk);
`StrategyRegistrationRequest`, `StrategyParameterUpdateRequest`, `StrategyMutationResult` (Strategy);
`MarketDataset` (Data); `AuthContext v2`, `AuditEvent` (Utils).

**No new third-party dependency. No owner-domain source file is modified.**

---

## 6. Validation commands

```bash
uv run ruff format --check app/services/api
uv run ruff check app/services/api
uv run mypy app/services/api

uv run pytest tests/api/unit
uv run pytest tests/api/integration
uv run pytest tests/api/contracts
uv run pytest tests/api/nfr
uv run pytest tests/api --cov=app/services/api --cov-branch --cov-fail-under=80

uv run python tests/api/usage/07_routes.py
uv run python tests/api/usage/08_composition.py

npm --prefix app/ui run lint
npm --prefix app/ui run test
npm --prefix app/ui run build
```

Per AGENTS.md §7, run only the targeted file during iteration; the full set gates completion.

---

## 7. Scope boundaries

**Included:** `app/services/api/**`, `app/ui/src/**`, `tests/api/**`, and the three
authoritative documents (`app/services/api/README.md`, `docs/PROJECT.md`, `docs/CHANGELOG.md`).

**Explicitly excluded:** any edit to `app/services/{portfolio,simulator,strategy,data,risk,trading,optimization,research}/**`
or `app/agentic/**`; a Simulator live engine; live-broker execution; dependency upgrades;
commits or pushes; refactoring outside the rows named above.

---

## 8. Blockers and risks

| # | Item | Severity | Mitigation |
|---|---|---|---|
| 1 | `FR-API-068`–`072` have **no requirement text anywhere in the repo**, yet the code is merged. Requirements must be reverse-engineered from the implementation — the inverse of AGENTS.md §8. | High | W1 authors them from `routes/agentic.py` and the existing `tests/api/unit/test_agentic_routes.py`, then flags them for owner review before any status flips to `Completed`. |
| 2 | `WF-API-008` cannot be completed in this domain (§3.4). | High | Closed as an authoritative upstream exclusion, not silently left `Excluded`. If you want it genuinely built, that is a separate Simulator-domain plan — say so and I will scope it. |
| 3 | Portfolio activation via the generic handle seam is public but is an escape hatch, not a named function. | Medium | Acceptable under the current allow-list, and it avoids editing another domain. Flagged as an owner decision: the cleaner long-term fix is a Portfolio-domain change exporting `coordinate_review` and returning evidence from `construct_portfolio`. |
| 4 | `POST /api/v1/risk/kill-switch` widens the safety boundary. | Medium | Human permission + distinct-principal approval + audit; Risk remains sole authority; UI/API never mutates canonical state. Covered by `test_nfr_003_safety.py`. |
| 5 | Operation count 55 → 64 breaks frozen OpenAPI snapshots and the frontend drift test. | Medium | Snapshot and count updates are explicit steps in W5, not incidental. |
| 6 | Coverage may dip below 80% while new routes land ahead of tests. | Low | Each workstream ships its tests in the same change; the coverage gate runs per workstream. |

---

## 9. Rollback path

Work is sequenced so each workstream is independently revertible.

- **W1:** revert `app/services/api/README.md`.
- **W2:** delete the 5 route handlers and their contract registrations; revert
  `portfolio_dependencies.py`; delete `tests/api/integration/test_portfolio_lifecycle.py`;
  restore `registry.size == 55`.
- **W3:** delete the 4 handlers and registrations; restore exclusion text.
- **W4:** revert idempotency wiring, `trading_dependencies.py`, `_settings.py`.
- **W5:** revert `routes.ts` and `ROUTE_CONTRACT_COUNT`; delete new clients and components.
- **W6:** revert README/`docs/PROJECT.md`/`docs/CHANGELOG.md`.

**Verification after rollback:** `uv run pytest tests/api` and
`npm --prefix app/ui run test` both green at the 55-operation baseline.

---

## 10. Approval gate

No file has been modified. Reply with a standalone message containing exactly:

```
APPROVED: EXECUTE
```

Approval covers **only** this numbered plan (`API-CLOSE-001`). Confirm alongside approval:

- **Q1 — `WF-API-008`:** close as an upstream exclusion (recommended), or open a separate
  Simulator plan to build a stateful live engine?
- **Q2 — Portfolio seam:** proceed via the public handle allow-list (recommended, stays in
  scope), or request a Portfolio-domain change first?
- **Q3 — `FR-API-068`–`072`:** authoring requirements retroactively from merged code is
  acceptable?

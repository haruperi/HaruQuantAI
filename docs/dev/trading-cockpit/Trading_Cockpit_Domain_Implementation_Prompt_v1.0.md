

## 1. Role

Act as a **Senior Implementation Engineer for HaruQuantAI**. You implement **one domain at a time**, taking it from package status `Partial` back to `Completed` by building the approved Trading Cockpit Phase 0 target behavior already folded into that domain's README.

You are implementing against an existing, well-tested brownfield repository. You are **not** redesigning the domain or the architecture. Every change must satisfy the 22 conformance gates in §6, which are the sole binding definition of "Completed."

Current domain is **`Portfolio`** located in `app/services/portfolio` so replace this on every `{{DOMAIN}}` placeholder.

## 2. Mission

For the single designated **`{{DOMAIN}}`** domain: implement every `Missing` feature and every `Partial` modification recorded in that domain README's `### Trading Cockpit Phase 0 reconciliation` subsection, plus any `REFACTOR`/`DEFERRED_INTEGRATION` items owned there, until the domain satisfies all 22 conformance gates and its README package status can be truthfully restored to `Completed`.

## 3. Domain order, dependencies, and sequencing

Process domains in this fixed order (Utils first; integration last):

```
Utils → Brokers → Data → Indicators → Strategy → Risk → Trading →
Simulator → Analytics → Optimization → Research → Portfolio → Agentic → UI-API
```

- **Utils is already `Completed`** (preserved pre-existing fold). Start at the first `Partial` domain.
- **Dependency rule:** a `DEFERRED_INTEGRATION` item names its later authoritative provider. Implement only the consumer port + fail-closed fallback in this domain. Never implement the provider's business logic here. If the provider does not yet exist, the port is still completable (fail-closed).
- **Recheck before coding:** before implementing any item, re-read its Phase 0 row against the current repository (change-control rule 9). If the codebase has drifted such that the classification is wrong, stop and issue a classification delta rather than implementing the stale plan.

## 4. Settled decisions — binding, do not relitigate

- **D-1 (cross-domain contract transport):** every versioned cross-domain contract travels as a **validated JSON-safe mapping behind `build_*`/`parse_*` function pairs** exported from the package root. The function-only `__all__` rule in `AGENTS.md` §1 stands unchanged. **Never export a class or constant.** Internal classes stay private; expose their behavior through standalone functions.
- **D-3 (transaction/outbox):** transaction, write-lock, migration-ledger, backup, recovery, and outbox **infrastructure stays in Data** at `app/services/data/persistence/`. Utils owns only the idempotency-key contract. Do not relocate this infrastructure.
- **Cockpit is sim-only:** a cockpit session may only produce `TradingRoute.SIM` intents and may never obtain a `BrokerEnvironment.LIVE` connection. `ALLOW_LIVE_MUTATIONS` stays `False`.
- **Financial records are append-only;** corrections are reversal or correction events. Direct historical mutation is prohibited.
- **Deterministic authority:** state, accounting, risk, execution, replay, and scoring are never delegated to an LLM.
- **No invented data:** never invent backtest results, fills, performance, or broker state.

## 5. Authoritative inputs (read before acting)

1. **The target domain README** — the sole requirement authority for this domain. Its `### Trading Cockpit Phase 0 reconciliation` subsection enumerates the work; its Feature Registry/§4 enumerate existing identity to preserve.
2. **`AGENTS.md`** — dry-run/approval gate, scope control, change-control, coding style, database rules, integration boundaries.
3. **`docs/ARCHITECTURE.md`** and **`docs/CHANGELOG.md`** — update targets (gate DOCS).
4. **Phase 0 evidence** under `docs/dev/trading-cockpit/phase-0/` — consult **only** to recheck a classification (rule 9) or to resolve a contract-detail question; the README is standalone and must not become normatively dependent on it.

## 6. The 22 conformance gates — the binding definition of "Completed"

Every gate must pass for the domain's package status to return to `Completed`. Each gate lists the concrete verification the agent must perform and evidence to record.

### Tier 1 — Mechanical Conformance (all must pass; failures block promotion)

| ID | Gate | Verification |
|----|------|--------------|
| **REG** | Feature Registry reconciliation: README-registered `FEAT-[DOM]-NN` IDs equal production feature module folders (features = modules), applying documented Reconciliation Exclusions | Count README `FEAT-*` rows (excl. retired/reserved/support dirs) == count of production feature module folders. No orphan folder, no unregistered feature. |
| **TASK** | All tasks in the domain README are `Completed`; none `Missing`/`Partial`/`Excluded` | Grep the README status columns; zero `Missing`/`Partial` remain for active owned requirements (deferred-integration *ports* are Completed at the port level — see §8). |
| **GATE** | Package-root export gate: `app/services/[DOMAIN]/__init__.py` (or `app/agentic/__init__.py`) declares a literal `__all__` and is the sole public boundary | Read the file; `__all__` is a literal tuple/list; no other module re-exports the public surface. |
| **FUNC** | Function-only public API surface: every `__all__` entry resolves to a standalone `def`, not a class or constant | `python -c "import inspect,app.services.{{DOMAIN}} as d; [print(n, type(getattr(d,n)).__name__) for n in d.__all__]"` — every entry prints `function`. |
| **DEEP** | No deep cross-domain imports by production services, usage examples, workflow scripts, or integration tests | Grep `from app.services.X.` / `from app.agentic.` outside the owning domain and `tests/{{DOMAIN}}/`; only shallow `from app.services.X import ...` allowed. |
| **ROOT** | Root-file rule: package root holds only `__init__.py`, `_settings.py`, `_limits.py`, `py.typed` | List the package root; no production behavior file at root. |
| **USE** | One numbered usage program per registered feature in `tests/[DOMAIN]/usage/features/`; every functional requirement's example function runs and prints exactly two things — a success message and the actual data the function produces | Run each `NN_*.py` under `if __name__=="__main__"`; each FR has a callable demo; output shows a success line + a real produced value (no invented data). |
| **WFE** | One stage-labelled program per active `WF-[DOM]-NNN` in `tests/[DOMAIN]/usage/workflows/`, plus `run_all.py` | Each active workflow has a program; `run_all.py` executes them in order. |
| **UT** | Unit tests present in `tests/[DOMAIN]/unit/`, all pass | `uv run pytest tests/{{DOMAIN}}/unit/ -q` → green. |
| **IT** | Integration tests present in `tests/[DOMAIN]/integration/`, all pass | `uv run pytest tests/{{DOMAIN}}/integration/ -q` → green. |
| **COV** | Coverage ≥ 80% floor **per file** for domain files | `uv run pytest tests/{{DOMAIN}}/ --cov=app/services/{{DOMAIN}} --cov-report=term-missing` (or `app/agentic`); no domain file below 80%. |
| **HYG** | No bare `except`, no `print` in application code, no literal credential patterns | `uv run ruff check .` clean; grep for `except:` and `print(` in `app/`; detect-secrets clean. |

### Tier 2 — Reviewed Conformance (all must pass)

| ID | Gate | Verification |
|----|------|--------------|
| **DB** | Migrations run through the authoritative manifest with ledger verification, write locks, checksum validation, transactional execution | Run the domain's `run_{{domain}}_migrations` against a dev DB; ledger step recorded, checksum verified, `execute_transaction` used for all writes. (Skip if domain owns no tables.) |
| **SCHEMA** | Target-vs-live reconciliation current; divergences between `docs/schema/` and applied migrations stated | Run `docs/schema/verify_schema.py` / `compare_model_to_code.py`; any divergence is documented in the README Persistence section with a reason. |
| **REACH** | Every table the domain declares is traced from its CRUD SQL builder/executor to a production application operation outside `persistence/` — no orphan table | For each owned table: name the feature + public operation that writes it. Unreached tables are removed or justified. |
| **CONTRACT** | Shared contracts documented, owned, versioned, covered by producer–consumer compatibility tests | Each new `build_*`/`parse_*` pair has a contract version (`v1`) and a compatibility test; owner recorded in README; consumers reference (not redefine) it. |
| **LOG** | `logger` used at workflow boundaries, public entry points, external interactions, state transitions, side effects, decisions, retries, failures; no secret exposure | Grep new code for boundary points; each emits a redacted log line; `detect-secrets` + review confirms no credential/PII/full payload. |
| **SAFE** | Fail-closed under uncertainty; non-bypassable kill switch; no live action by default; environment boundaries enforced; credential hygiene | For cockpit-execution domains: assert `route==SIM` and `environment != LIVE` paths are tested and raise on mismatch. Unknown input → visible restricted/unknown state, never a plausible default. |
| **QUANT** | No lookahead bias; deterministic, seeded stochastic paths; reproducible backtests; no invented results/fills/performance | New stochastic code takes an injected seed; a no-lookahead/point-in-time test exists where relevant; two runs with the same seed produce identical output. |
| **NFR** | Declared performance/latency budgets met; unit tests within the 100 ms ceiling | Each new unit test < 100 ms (mock DB/IO); any NFR budget in the README has a measurement. |
| **DOCS** | Owning README, `docs/ARCHITECTURE.md`, `docs/CHANGELOG.md` current; no resolved rows retained in Open Decisions; code and docs reconciled and matching | README status rows flipped to `Completed` with `file:line` evidence; CHANGELOG `## [Unreleased]` updated; resolved ODs converted to requirements and deleted from §6. |
| **UI** | Domain capability reachable through the UI-API boundary and surfaced in the frontend | For domains that produce a cockpit-visible capability: name the UI-API route/read model/panel that exposes it and the frontend surface; otherwise record an explicit exclusion with a reason. |

## 7. Per-item implementation procedure

For **each** `Missing` feature or `Partial` modification in the reconciliation subsection:

1. **Recheck** the Phase 0 classification against current code (rule 9). Confirm the cited evidence still means what the row says.
2. **Dry-run report** (per `AGENTS.md` §1): selected feature; files read; files to create/edit with exact paths and purpose; `FR-*` requirements; contracts (`build_*`/`parse_*`, version); dependencies; tests; validation commands; scope boundaries; blockers/risks; rollback path. **Do not modify files during the dry run.**
3. **Approval gate:** obtain a standalone owner message whose trimmed content is exactly `APPROVED: EXECUTE`. A message containing additional text does not authorize execution.
4. **Implement** to the focused-domain rules: one feature = one module folder = one numbered usage program; FRs atomic and testable; function-only exports; no deep cross-domain imports; match existing style (Google docstrings, `ruff format`, absolute imports).
5. **Test:** unit + integration + the feature usage program + structural import/export tests; coverage ≥ 80% per file; unit tests ≤ 100 ms.
6. **Update the domain README:** flip the feature/FR row `Missing`/`Partial` → `Completed` with concrete evidence (`file:line`, passing test path). Keep the reconciliation subsection intact as history.
7. **Run the 22 gates** for the changed scope and record results.

## 8. Handling the special classifications

- **`DEFERRED_INTEGRATION` (e.g., Risk↔Research expectancy, Trading↔Portfolio ledger events, Optimization↔Simulator models, Agentic/UI-API↔Simulator):**
  Implement the **consumer port and fail-closed fallback in this domain** and mark that FR `Completed`. The port must degrade safely (e.g., a missing expectancy provider returns `NOT_ELIGIBLE`, causing fallback to the normal risk-to-reward gate; it never returns an inferred approval). **Do not build the provider's business logic here.** Record the deferred cross-domain integration as a pending item in the README and final report.

- **`REFACTOR` (e.g., idempotency consolidation, FX authority, `PortfolioState`, `ScenarioDefinition`, `OrderIntent = Any`):**
  Consolidate to the single canonical owner and migrate callers, **or escalate**. If the README's recorded Open Decision documents a safe **in-domain** direction (e.g., Simulator uses a distinct name `MissionDefinition` while Risk retains its advisory model — no cross-domain relocation needed), follow it. If the refactor requires **cross-domain relocation the owner has not approved** (e.g., moving `PortfolioState` from Risk to Portfolio), **STOP, do not guess**, and escalate the OD.

- **`CONFLICTING` / blocking Open Decision:**
  Implement only the parts the OD's documented direction permits. Any portion blocked by an unresolved owner choice keeps the affected requirement `Partial` and the package `Partial`; surface it as a blocker in the final report.

## 9. Status promotion rules

- A **feature/FR** moves `Missing`/`Partial` → `Completed` only when implemented **and** verified with evidence (code path + passing test).
- The **package status** moves to `Completed` only when **all** of the following hold:
  1. Every active owned FR is `Completed` (deferred-integration ports count as Completed at the port level).
  2. All 22 conformance gates pass.
  3. No **blocking** Open Decision remains in this domain (a blocking OD is one that prevents safe implementation of an active requirement).
- A blocking OD keeps the package `Partial`. Report it; do not fake completion.
- Never downgrade existing `Completed` behavior without evidence.

## 10. Scope control

- **One domain only.** Do not modify another domain's code, tests, migrations, or README.
- **Preserve identity:** do not renumber, rename, or reuse existing active/retired/reserved IDs, contracts, schema IDs, error codes, or public symbols.
- **Reuse before create:** extend existing conforming assets; do not duplicate.
- **No new horizontal tech-layer folders** unless the domain's approved architecture already allows it.
- **Database changes** require ledger verification, write-lock acquisition, checksum validation, transactional execution, and an explicit retention rule per table (rule 8). No cockpit durable state in `data_runtime_records`.
- **Do not commit or push** unless the owner explicitly instructs. Do not run `rm -rf`, `git reset`, `git clean`, `git stash` over owner changes, live broker calls, or destructive SQL.
- **Pre-existing owner changes** in the worktree are classified and left untouched (rule 12).

## 11. Required final report

After the domain work, return:

| Field | Content |
|-------|---------|
| Domain | `{{DOMAIN}}` |
| Final package status | `Completed` \| `Partial` (with reason) |
| 22-gate results | pass/fail per gate with evidence command + output |
| Files changed | paths, created vs edited |
| FRs promoted | `Missing`/`Partial` → `Completed`, each with `file:line` + test |
| Contracts added | name, version, owner, `build_*/parse_*` location, compatibility test |
| Persistence changes | tables added/changed, migration step, retention rule, REACH trace |
| Tests run | commands + pass/fail + coverage figure |
| Deferred integrations | item → named provider → fail-closed behavior implemented |
| Blocking Open Decisions | OD ID + why it blocks + recommended resolution |
| Safety confirmations | sim-only enforced, kill switch intact, no live route, no secrets, fail-closed verified |
| DOCS updates | README deltas, CHANGELOG entry, ARCHITECTURE delta |

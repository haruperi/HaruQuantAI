# Phase 0 Findings and Decisions

**Baseline ID:** `HQA-TC-P0-20260807T075707Z-3b039544`
**Captured (UTC):** `2026-08-07T07:57:07Z`
**Commit:** `3b039544b7812a78f140530d39e744421eac1396` on `main` (70 ahead of `origin/main`)

This is an audit conclusion. It does not implement or redesign anything.

---

## 1. Executive current-state summary

HaruQuantAI is a large, disciplined, well-tested quantitative trading platform: **910 Python files,
198,352 lines, 165 registered features across fourteen domains, 1064 public exports, 94 logical database
tables, 758 test files and 374 standalone usage programs.** Architectural rules are real and enforced —
one feature per module folder, a single public export boundary per domain, no deep cross-domain imports,
and a function-only public surface that holds at 1064 exports with zero exceptions.

**The Trading Cockpit does not exist in it.** Not partially, not in prototype. Of 603 atomic
specification requirements, **zero are `FULL`**. Of 229 forward work packages, **exactly one is
`REUSE`** — the Agentic tool-and-response audit.

That is not a criticism of the repository. The cockpit is a different product built from the same parts.
What Phase 0 establishes is which parts genuinely fit, which parts merely share a name, and which parts
are not there at all.

**Three facts should shape the programme plan more than anything else in this document:**

1. **There is no accounting system.** No ledger, account, cash, balance, equity, margin, buying power or
   P&L model exists anywhere in `app/`. The existing Portfolio domain is an allocation and rebalancing
   engine. The cockpit's entire financial authority — specification sections 6.7, 6.8 and 8 — must be
   built from nothing, and the plan schedules it twelfth.
2. **The repository's public-API rule and the plan's contract registry are incompatible as written.**
   Every one of the ~54 required cross-domain contracts is a type; `AGENTS.md` forbids exporting types
   from domain roots. This blocks Phase 1 on day one.
3. **The strongest cockpit asset already exists and is under-recognised by the plan.** A durable
   simulation session with an orchestrator, a create/read/step/branch/close HTTP API, an SSE frame
   stream, an immutable journal, a canonical tick timeline and fixed-precision account math is already
   running (`app/services/simulator/`, `app/services/api/routes/simulation_sessions.py`,
   `simulation_live.py`). Phase 8 should start from it, not beside it.

---

## 2. Counts

### 2.1 Specification requirements (603 total)

| Requirement class | Count |
|---|---:|
| Checklist steps (`PRE_*`, `ENTRY_*`, `MGT_*`, `EXIT_*`, `POST_*`) | 125 |
| Emergency steps (`FLASH_*`, `API_*`, `DD_*`) | 24 |
| Derived normative prose (`TCS-Snn-REQ-nnn`) | 137 |
| Derived normative table rows (`TCS-Snn-m-TBL-nnn`) | 277 |
| Final acceptance criteria (`TCS-AC-001` .. `TCS-AC-040`) | 40 |

| Current status | Count |
|---|---:|
| `FULL` | **0** |
| `PARTIAL` | 353 |
| `ABSENT` | 250 |
| `CONFLICTING` | 0 |
| `UNKNOWN` | 0 |
| `NOT_APPLICABLE` | 0 |

`PARTIAL` means a located repository capability covers part of the requirement, with the exact path and
symbol recorded and the missing part stated. It does not mean "nearly done".

### 2.2 Work packages (239 total; 229 forward + 10 Phase 0)

| Current status | Count |
|---|---:|
| `FULL` | 10 (Phase 0 itself) |
| `PARTIAL` | 115 |
| `ABSENT` | 114 |

| Future action | Count |
|---|---:|
| `REUSE` | 11 (10 Phase 0 + `TC-IMP-AGT-09`) |
| `EXTEND` | 109 |
| `CREATE` | 86 |
| `REFACTOR` | 6 |
| `DEFERRED_INTEGRATION` | 27 |
| `NOT_APPLICABLE` | 0 |

| Confidence | Count |
|---|---:|
| `HIGH` | 174 |
| `MEDIUM` | 61 |
| `LOW` | 4 |

### 2.3 Contracts (66 registry rows)

| Current status | Count | | Future action | Count |
|---|---:|---|---|---:|
| `PARTIAL` | 39 | | `EXTEND` | 29 |
| `ABSENT` | 24 | | `CREATE` | 21 |
| `CONFLICTING` | 3 | | `REFACTOR` | 12 |
| | | | `DEFERRED_INTEGRATION` | 3 |
| | | | `REUSE` | 1 |

**Exactly one required contract exists with the correct name in the correct domain:** `EconomicEvent`
(`app/services/data/economic_calendar/events.py:29`).

### 2.4 Effort distribution by phase

| Phase | Domain | Packages | `CREATE` | `EXTEND` | `REFACTOR` | `DEFERRED` | `REUSE` |
|---|---|---:|---:|---:|---:|---:|---:|
| 1 | Utils | 12 | 2 | 8 | 2 | 0 | 0 |
| 2 | Brokers | 12 | 1 | 11 | 0 | 0 | 0 |
| 3 | Data | 13 | 1 | 12 | 0 | 0 | 0 |
| 4 | Indicators | 10 | 2 | 8 | 0 | 0 | 0 |
| 5 | Strategy | 11 | 3 | 7 | 0 | 1 | 0 |
| 6 | Risk | 17 | 3 | 11 | 1 | 2 | 0 |
| 7 | Trading | 14 | 2 | 12 | 0 | 0 | 0 |
| 8 | Simulator | 31 | 23 | 7 | 1 | 0 | 0 |
| 9 | Analytics | 13 | 10 | 3 | 0 | 0 | 0 |
| 10 | Optimization | 10 | 0 | 7 | 0 | 3 | 0 |
| 11 | Research | 11 | 5 | 5 | 0 | 1 | 0 |
| 12 | Portfolio | 17 | 13 | 2 | 2 | 0 | 0 |
| 13 | Agentic | 11 | 0 | 6 | 0 | 4 | 1 |
| 14 | UI-API | 35 | 22 | 7 | 0 | 6 | 0 |
| 15 | System | 12 | 0 | 2 | 0 | 10 | 0 |

Phases 8, 14, 12 and 9 carry 68 of the 86 `CREATE` packages between them.

---

## 3. Top contract collisions

| # | Collision | Evidence | Impact |
|---|---|---|---|
| **C-1** | **`PortfolioState` is defined in Risk.** The canonical name the plan assigns to Portfolio is already a Risk evidence model. Portfolio owns a differently-shaped `PortfolioStateStore`. | `app/services/risk/contracts/evidence.py:240`; `app/services/portfolio/state/repository.py:25` | Phase 12 must reclaim the name and migrate Risk callers, or the plan must be amended. |
| **C-2** | **`ScenarioDefinition` is defined in Risk as an advisory request.** The plan assigns the name to Simulator as a blocking, versioned mission contract. The semantics are incompatible. | `app/services/risk/contracts/requests.py:486` (`FEAT-RISK-14`, explicitly advisory) | Phase 8 cannot use the canonical name without a rename or namespacing decision. |
| **C-3** | **`OrderIntent` is weakened to `Any` at the Simulator boundary.** The authoritative Trading type exists and is correct, but Simulator rebinds the name to `Any` in two modules, erasing the type. | `app/services/trading/contracts/models.py:653`; `app/services/simulator/execution/engine.py:32`; `app/services/simulator/run/orchestrator.py:41` | Type authority is silently lost at exactly the boundary the cockpit runs through. |
| **C-4** | **FX authority is split three ways.** Data owns rate contracts and a provider; Simulator re-validates conversion evidence; Portfolio — the required owner — owns neither. | `app/services/data/evidence/fx_contracts.py:57,125,194`; `fx_conversion.py:39`; `app/services/simulator/accounting/calculations.py:133` | Multi-currency accounting has no authoritative owner. |
| **C-5** | **Four idempotency stores.** `trading_idempotency`, `portfolio_idempotency`, `api_idempotency` and `data_backfill_checkpoints`, with different key columns and no shared contract. | four migration modules; `app/services/api/identity/authorization.py:24` | Exactly-once economic intent is unproven across them. Specification acceptance criterion 10 depends on it. |
| **C-6** | **`journal` and `Scorecard` are already taken.** Simulator's `journal/` is an immutable replay record; `ResearchScorecard` measures research edges. Neither is the player-facing concept Analytics needs. | `app/services/simulator/journal/`; `app/services/research/contracts/results.py:446` | Phase 9 must pick distinct names or it will create silent semantic collisions. |
| **C-7** | **Two divergent validation-result shapes.** Neither is canonical, and no `PASS/WARN/BLOCK/FAIL/UNKNOWN` taxonomy exists. | `app/services/portfolio/allocation/service.py:24`; `app/services/risk/contracts/results.py:491` | `TC-IMP-UTIL-05` is a `REFACTOR` with caller migration, not a clean addition. |
| **C-8** | **`AccountStateSnapshot` lives in Data**, but the plan assigns normalized account snapshots to Brokers. | `app/services/data/evidence/account_contracts.py:199` | Phase 2 must resolve ownership before extending. |
| **C-9** | **The only order-book model lives in Brokers**, but the plan assigns L2 state to Data. | `app/services/brokers/contracts/models.py:941` | Phase 3 `TC-IMP-DATA-03` is `LOW` confidence pending investigation. |

---

## 4. Top ownership conflicts

| # | Conflict | Current owner | Required owner | Resolving phase |
|---|---|---|---|---|
| **O-1** | Financial accounting authority | *nobody* | Portfolio | 12 |
| **O-2** | `PortfolioState` | Risk | Portfolio | 12 |
| **O-3** | `ScenarioDefinition` | Risk (advisory) | Simulator | 8 |
| **O-4** | FX conversion | Data + Simulator | Portfolio | 12 |
| **O-5** | Fixed-precision money/quantity math | Simulator (`FEAT-SIM-04`) | Utils | 1 |
| **O-6** | Transaction / outbox infrastructure | Data (`AGENTS.md`-documented exemption) | Utils per plan `TC-IMP-UTIL-12` | Owner decision |
| **O-7** | Replay identity | split: Strategy manifests + Simulator journal | Simulator | 8 |
| **O-8** | Instrument identity | split: `data_symbols` (Data) + `broker_symbol_map` (Brokers) | Brokers | 2 |
| **O-9** | Approval authority | split: `risk_approval_tokens` + `api_approvals` | undecided | 14 |
| **O-10** | Idempotency | Trading + Portfolio + UI-API + Data | Utils | 1 |

---

## 5. Top persistence risks

| # | Risk | Evidence |
|---|---|---|
| **P-1** | **No ledger table anywhere.** Across 103 `CREATE TABLE` statements there is no account, cash, posting, balance, equity or P&L table. | all migration modules |
| **P-2** | **`sim_sessions` has four columns.** It must eventually carry clock, scenario, replay identity, checklist, alerts, emergency state, counters, branches and a secured marker. | `app/services/simulator/migrations/definitions.py` |
| **P-3** | **Trading position rebuild in flight with a changed primary key.** `trading_positions` (PK `position_id`, 20 cols) coexists with `trading_positions__new` (PK `ticket`, 26 cols) plus a migration guard table. | `app/services/trading/migrations/definitions.py` |
| **P-4** | **Seven `risk_*__new` rebuild tables** shadow all seven live Risk tables. | `app/services/risk/migrations/definitions.py` |
| **P-5** | **Four `strategy_*_v2` families** coexist with their originals; authority is not determinable from the migration source. | `app/services/strategy/migrations/definitions.py` |
| **P-6** | **`data_runtime_records` is a generic cross-domain key-value store** any domain may write to. Cockpit durable state must be kept out of it. | `app/services/data/migrations/runtime_stores.py` (`FEAT-DATA-17`) |
| **P-7** | **`research_artifacts` is keyed by filesystem path** — a brittle business key for approved expectancy governance. | `app/services/research/migrations/definitions.py` |
| **P-8** | **No retention or archival rule is declared** for any of the 94 logical tables. | all migrations |
| **P-9** | **Only one outbox exists** (`portfolio_audit_outbox`), and it sits in the wrong domain relative to the plan. | `app/services/portfolio/migrations/definitions.py` |
| **P-10** | `agentic_lifecycle_transitions` has no primary key. | `app/agentic/migrations/lifecycle.py` |

---

## 6. Top test gaps

| # | Gap | Evidence |
|---|---|---|
| **T-1** | **mypy strict is red at baseline.** 1 error in 1 file across 2091 checked files. | `app/agentic/migrations/manifest.py:34:31` — `"object" has no attribute "migration_id"` |
| **T-2** | **The Utils cross-domain-import guard is broken.** The test that enforces *No Deep Cross-Domain Imports* for Utils errors on a hardcoded path that does not exist, so the rule is currently unenforced — right before Phase 1 adds ten Utils contracts every domain will import. | `tests/utils/integration/test_consumer_isolation.py:27` → `tests/brokers/wf_support.py` (absent) |
| **T-3** | **The Trading simulation-target parity check is failing.** The repository's own test that every Trading workflow program declares `EXECUTION_TARGET: Target = "sim"` fails for `WF-TRD-017`. | `tests/trading/unit/test_workflow_usage_parity.py:113` |
| **T-4** | **No coverage figure could be produced.** The full suite did not complete within the audit host's per-command limit. The configured gate is `fail_under = 80`; the current true figure is unknown. | `trading-cockpit-test-baseline.md` section 5 |
| **T-5** | **UI-API has the weakest usage coverage** — 10 usage programs against 54 test files, versus 43 for Data and 37 for Agentic. Phase 14 adds 35 work packages there. | per-domain counts |
| **T-6** | **Portfolio has the fewest tests of any domain** — 21 test files — and Phase 12 adds 17 work packages including the entire ledger. | per-domain counts |
| **T-7** | **No determinism, no-lookahead, compound-failure or golden-run test class exists anywhere.** These are mandatory evidence classes in plan section 24.1. | repository-wide scan |
| **T-8** | Seven Indicators and one Portfolio usage-script executions failed in the audit sandbox with no captured reason. Unconfirmed — must be re-run on Windows. | `trading-cockpit-test-baseline.md` U-1, U-2 |

---

## 7. Top safety risks

Full detail in `trading-cockpit-safety-baseline.md`. Current classification: **`PARTIAL`**.

| # | Risk | Severity |
|---|---|---|
| **S-1** | `_require_non_production` guards standalone provider connections only; `registry/factory.py` passes `config.environment` through without an observed non-production assertion. Downstream Trading guards still apply, which is why this is not `VIOLATED`. | High |
| **S-2** | **No cockpit mode exists to bind a guard to.** Specification step `PRE_001` requires `Mode = SIMULATION`; no mode concept exists in any domain, so the interlock cannot be written or tested. | High |
| **S-3** | **The kill switch is a single boolean.** It cannot keep cancel, protection, reduction and closure available while locking new exposure — which acceptance criterion 12 and steps `FLASH_002` / `DD_002` require. | Medium |
| **S-4** | `_LiveRuntimeConfig.execution_route` is `Literal["paper","live"]` and cannot express `sim`, though `TradingRoute.SIM` exists. | Medium |
| **S-5** | **No first-class `UNKNOWN` order state** preserved until reconciliation; blind-resubmission prohibition is untested. | Medium |
| **S-6** | **No protective-order lifecycle at all** — no coverage ratio, no bracket/OCO, no orphan prevention. | Medium |
| **S-7** | `app/configs/gcp-oauth.keys.json` is tracked in git. Contents were not read or reproduced. | Low — owner review |

**Confirmed for Phase 0:** no order submitted, no live account write attempted, no broker connection
opened, no migration applied, no database opened, no `.env` read or modified, no secret written to any
artifact, no account ID recorded.

**The single strongest safety asset in the repository** is `app/agentic/permissions/models.py`, where
broker mutation and kill-switch clearance are *unrepresentable types* rather than runtime checks
(`FORBIDDEN_TOOL_TOKENS` line 46, `FORBIDDEN_RECEIVER_DOMAINS` line 64, `SideEffectClass` line 66).
Cockpit agents must reuse it verbatim.

---

## 8. Decisions already determined by the source documents

These need no owner input; they are settled by the specification, the plan or `AGENTS.md`.

1. The cockpit is built by expanding the fourteen existing domains. No parallel `trading_cockpit/` tree.
2. The domain order is fixed: Utils → Brokers → Data → Indicators → Strategy → Risk → Trading →
   Simulator → Analytics → Optimization → Research → Portfolio → Agentic → UI-API → integration.
3. The domain that owns a concept owns its canonical model and durable state.
4. Earlier consumers may define narrow ports; they may not implement a later provider's business logic.
5. No silent fallbacks. Unknown input produces a visible restricted or unknown state.
6. No production live-money route is authorized for cockpit modes.
7. Deterministic state, accounting, risk, execution, replay and scoring are never delegated to an LLM.
8. Financial records are append-only; corrections are reversal or correction events.
9. The quality toolchain is unchanged: `uv run --frozen`, Ruff, strict mypy, pytest, coverage ≥ 80%.
10. Risk falls back to the normal risk-to-reward gate whenever expectancy evidence is missing, expired,
    suspended, revoked or mismatched.
11. A correctly identified no-trade day is a passing outcome.
12. Phase 0 documentation lives at `docs/dev/trading-cockpit/phase-0/`, matching the repository's
    existing `docs/dev/` convention.

---

## 9. Decisions required from the repository owner

Ordered by how much they block. **D-1 blocks Phase 1 entirely.**

### D-1 — How do versioned types cross domain boundaries? **(BLOCKING — Phase 1 cannot start)**

`AGENTS.md` mandates a **Function-Only Public API Surface**: `__all__` in every
`app/services/[DOMAIN]/__init__.py` must contain only standalone functions; classes stay internal;
constants are exposed through getters. Verified empirically: **1064 public exports, zero class-like,
across all fourteen domains.**

The plan's cross-domain contract registry requires ~54 shared *types* — `ProfileRef`, `EventEnvelope`,
`OrderIntent`, `PortfolioState`, `LedgerEntry`, `ChecklistState` and the rest — to be consumed across
domains.

These are incompatible as written. Options:

| Option | Consequence |
|---|---|
| **(a)** Amend `AGENTS.md` to permit exporting frozen, versioned contract types | Cleanest for the cockpit; changes a rule the whole repository currently satisfies without exception |
| **(b)** Keep functions only; pass contracts as validated mappings or JSON-safe dicts across boundaries | Preserves the rule; loses static typing at exactly the boundaries where the specification demands determinism, and works against `mypy --strict` |
| **(c)** Introduce a shared contracts package outside the domain-root rule | Creates a fifteenth location and risks becoming the parallel tree rule 1 forbids |
| **(d)** Per-domain exception, granted case by case | Slowest; erodes the rule by precedent |

**Recommendation: (a)**, narrowly scoped to frozen, versioned, immutable contract types that carry a
schema identity — with the function-only rule retained for all behavior.

### D-2 — Should Phase 12 (Portfolio) be resequenced? **(HIGH)**

The cockpit's financial authority does not exist. Phase 12 carries 13 `CREATE` and 2 `REFACTOR`
packages, and Risk, Trading, Simulator and Analytics all consume portfolio state before it arrives —
meaning four phases build against fakes that Phase 12 then replaces.

Options: keep the order and accept extensive fake-then-replace churn; or lift a minimal ledger and
account model earlier (after Trading, before Simulator) so downstream phases build against real
accounting.

### D-3 — Where do transaction and outbox primitives live? **(MEDIUM)**

`AGENTS.md` places them in `app/services/data/persistence/` with a documented exemption.
`TC-IMP-UTIL-12` places them in Utils. `portfolio_audit_outbox` is the only outbox and sits in
Portfolio. Three positions, one concern.

### D-4 — Resolve the three name collisions. **(HIGH)**

- `PortfolioState`: does Phase 12 reclaim the name from Risk (migrating callers), or does the plan adopt
  a different name?
- `ScenarioDefinition`: does Phase 8 take the name from Risk, or does Simulator use a distinct name such
  as `MissionDefinition`?
- `Scorecard` / `JournalEntry`: what names does Analytics use, given `ResearchScorecard` and Simulator's
  replay `journal/` already exist?

### D-5 — Resolve the three in-flight schema rebuilds. **(HIGH)**

Which is authoritative: `trading_positions` or `trading_positions__new`? Are the seven `risk_*__new`
tables complete? Which `strategy_*` family is live? Each blocks the phase that touches it.

### D-6 — When must the cockpit safety boundary become `PROVEN`? **(HIGH)**

`TC-IMP-BRK-10` in Phase 2 is supposed to prove simulation/sandbox isolation, but the mode concept it
would guard (`TC-IMP-SIM-09`) does not arrive until Phase 8. Either lift a minimal mode marker into
Phase 2, or formally re-date the `TC-IMP-BRK-10` proof to Phase 8 and accept `PARTIAL` until then.

### D-7 — Fix the three baseline failures, and under what scope? **(MEDIUM)**

`T-1` (mypy), `T-2` (Utils import guard — currently leaves an architectural rule unenforced) and `T-3`
(Trading simulation-target parity — weakens the safety evidence chain). All three predate this work.
`AGENTS.md` scope control means none can be fixed inside another approved scope.

**Recommendation:** fix `T-2` and `T-3` as a small standalone approved change before Phase 1, since both
guard rules the cockpit depends on.

### D-8 — Is `app/configs/gcp-oauth.keys.json` safe to track? **(MEDIUM)**

Contents were deliberately not read. Owner review required.

### D-9 — Should the CRLF condition be addressed? **(LOW)**

With `core.autocrlf=false` and a CRLF working tree, `git status` reports all 1969 tracked text files as
modified and `git diff` is unusable. Every phase will have to use `git -c core.autocrlf=input` to see its
own footprint. A `.gitattributes` file would fix it, but that is a configuration change outside Phase 0
scope.

### D-11 — The Phase 0 `.csv` artifacts are gitignored. **(MEDIUM)**

`.gitignore` line 634 contains `*.csv`, which excludes all three machine-readable Phase 0 artifacts:

```text
docs/dev/trading-cockpit/phase-0/trading-cockpit-gap-matrix.csv
docs/dev/trading-cockpit/phase-0/trading-cockpit-traceability-matrix.csv
docs/dev/trading-cockpit/phase-0/trading-cockpit-contract-registry.csv
```

Verified with `git check-ignore -v`. The files exist on disk and their row sets are identical to the
corresponding `.md` documents (confirmed by the Phase 0 consistency checks), but `git status` will not
offer them and a plain `git add` will skip them. The audit prompt requires
`trading-cockpit-gap-matrix.csv` as a deliverable.

Editing `.gitignore` is a configuration change outside the Phase 0 write boundary, so it was not done.
Options for the owner:

| Option | Consequence |
|---|---|
| **(a)** Add a negation to `.gitignore`: `!docs/dev/trading-cockpit/**/*.csv` | Cleanest; keeps the broad `*.csv` rule for data files while allowing versioned documentation CSVs |
| **(b)** `git add -f` the three files | Works once; the next agent will hit the same surprise |
| **(c)** Accept the `.md` matrices as the only committed form | Loses the machine-readable twins the plan and prompt both call for |

**Recommendation: (a).**

### D-10 — Confirm the ADR omission. **(RESOLVED)**

The audit prompt required `ADR-0001-extend-existing-domains-for-trading-cockpit.md`. `AGENTS.md`
section 4 (*Decision Hygiene*) prohibits standalone ADR and decision-record documents. **The owner chose
to honour `AGENTS.md`**: no ADR file was created, and the decision is recorded as rule 1 of
`trading-cockpit-change-control.md` and in section 8 above.

```text
Decision:
Implement the Trading Cockpit by expanding the fourteen existing HaruQuantAI domains.

Rejected alternative:
Creating a separate top-level Trading Cockpit service tree that duplicates current
domain responsibilities.

Consequences:
- Every cockpit capability is added to the domain that already owns the responsibility.
- Cross-domain contracts are owned by their provider domain (blocked on D-1).
- Existing public APIs are extended under the compatibility rules in
  trading-cockpit-change-control.md.
- No duplicate authoritative implementation may be introduced.
```

---

## 10. Genuine reuse assets

It would be misleading to end on the gaps. These are real, tested and should be built on rather than
rebuilt:

| Asset | Location | Why it matters |
|---|---|---|
| Simulation session + stepping/branching API + SSE stream | `app/services/simulator/`, `app/services/api/routes/simulation_sessions.py`, `simulation_live.py`, tables `sim_sessions`, `sim_runs` | The cockpit session skeleton already runs headless |
| Agent permission constitution | `app/agentic/permissions/models.py:46,64,66`; `tests/agentic/integration/test_tool_permissions.py` | Deny-by-construction; the programme's only `REUSE` |
| Durable kill switch with CAS + approval tokens | `app/services/risk/kill_switch/`, `approvals/`; `tests/system/integration/test_kill_switch.py` | Real, durable, restart-surviving safety machinery |
| Economic calendar | `app/services/data/economic_calendar/`; 3 tables; `tests/system/integration/test_economic_news_restriction.py` | The one contract already correctly named and owned |
| Point-in-time research source evidence | `app/services/data/research_sources/`; 3 tables (`FEAT-DATA-16`) | Exactly the Data/Research boundary the plan asks for |
| Optimization studies, search, validation, robustness, promotion | `app/services/optimization/` (`FEAT-OPT-01..09`) | Best-aligned domain; 7 of 10 packages are `EXTEND` |
| Order lifecycle skeleton | `trading_orders`, `trading_order_transitions`, `trading_fills` (UQ `broker_fill_id`), `trading_events` (UQ `scope_key, aggregate_version`) | Good idempotency and event-sequence invariants already in the schema |
| Sim-route isolation | `app/services/trading/routing/dispatcher.py:503` | The exact structural guard the cockpit needs |
| Indicator library + materializations | `app/services/indicators/` (`FEAT-INDI-01..06`); 3 tables | Reuse the mathematics; add cockpit adapters |
| Capital allocation with activation governance | `app/services/portfolio/allocation/`, `app/services/risk/allocation/`; `tests/system/integration/test_portfolio_activation.py` | The one substantial Portfolio reuse asset |
| API foundation: RBAC, mandatory idempotency, ordered secret-safe events, typed Python↔TypeScript transport | `app/services/api/identity/`, `streams/events.py`, `app/ui/src/clients/` | Phase 14 does not start from zero on the plumbing |

---

## 11. Phase 1 readiness statement

```text
PHASE 1 READINESS: NOT READY
```

The audit is complete and every exit-gate evidence artifact exists. Phase 1 is blocked on one decision,
not on missing analysis.

**Blocking:**

- **D-1** — the function-only public API rule and the cross-domain contract registry are incompatible.
  `TC-IMP-UTIL-01` cannot define `ProfileRef` and `VersionRef` as consumable cross-domain types until
  this is settled.

**Should be resolved before Phase 1, not during it:**

- **D-3** — transaction/outbox ownership determines whether `TC-IMP-UTIL-12` is a `CREATE` in Utils or a
  documented `NOT_APPLICABLE` deferring to Data.
- **D-7** — `T-2` leaves the Utils cross-domain-import guard unenforced at exactly the moment Phase 1
  adds ten contracts every domain will import.

**Ready once D-1 is decided:** all twelve Phase 1 work packages are classified with evidence, owners,
dependencies and acceptance targets. Eight are `EXTEND` against located Utils behavior, two are `CREATE`,
and two are `REFACTOR` requiring caller migration. `TC-IMP-UTIL-07` (idempotency consolidation) is the
largest single item and touches four domains.

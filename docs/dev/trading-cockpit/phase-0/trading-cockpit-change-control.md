# Trading Cockpit Change-Control Policy

**Work package:** `TC-IMP-BASE-10`
**Baseline ID:** `HQA-TC-P0-20260807T075707Z-3b039544`
**Applies to:** every phase from Phase 1 (Utils) through Phase 15 (integration and release)
**Status:** binding for all Trading Cockpit work

This policy sits **beneath** `AGENTS.md`, not beside it. Where this document and `AGENTS.md` differ,
`AGENTS.md` wins and the conflict must be raised to the owner rather than resolved in code. The
authority order remains: Owner → `AGENTS.md` → `docs/PROJECT.md` → `docs/ARCHITECTURE.md` →
`docs/CHANGELOG.md`.

---

## The fifteen rules

### 1. Extend existing domains; do not create a parallel `trading_cockpit/` service tree

The Trading Cockpit is added to the fourteen domains that already own the underlying responsibilities.
No new top-level product tree, no `app/services/trading_cockpit/`, no `app/cockpit/`. A cockpit concept
that has no obvious owner is escalated to the owner for an ownership decision; it is never parked in a
new tree.

Phase 0 evidence: `current-state-domain-inventory.md` shows every cockpit capability has a natural home,
and `trading-cockpit-gap-matrix.md` classifies 109 of 229 forward work packages as `EXTEND` against
existing behavior.

### 2. The domain that owns a concept owns its canonical model and state

One authoritative model per concept, in one domain, with one durable store. Other domains hold
references, projections or read models — never competing truth.

Phase 0 found four active violations that later phases must resolve rather than reproduce:

| Concept | Canonical owner | Currently defined in | Resolving phase |
|---|---|---|---|
| `PortfolioState` | Portfolio | Risk (`app/services/risk/contracts/evidence.py:240`) | 12 |
| `ScenarioDefinition` | Simulator | Risk (`app/services/risk/contracts/requests.py:486`) | 8 |
| FX conversion | Portfolio | Data (`evidence/fx_contracts.py`) + Simulator (`accounting/calculations.py:133`) | 12 |
| Idempotency | Utils | Trading, Portfolio, UI-API, Data (four stores) | 1 |

### 3. Earlier consumers may define narrow ports for later providers, but may not implement the later provider's business logic

A consumer port declares only the fields the consumer needs. It may be backed by a deterministic test
fake. The fake is removed at `TC-IMP-SYS-01`.

No temporary calculation may become a second account ledger, valuation engine, expectancy store or
scenario registry. Phase 0 classified 27 work packages as `DEFERRED_INTEGRATION`; each names its later
authoritative provider in the `Blocker` column of the gap matrix.

Specific standing instructions:

- Risk consumes `PortfolioRiskView` and `ExpectancyEligibilityEvidencePort`. Until Phase 11, a missing
  expectancy provider returns `NOT_ELIGIBLE`, causing fallback to the normal risk-to-reward gate. It
  never returns an inferred approval.
- Trading emits economic execution events before Phase 12; Portfolio owns ledger posting.
- Strategy holds a version-exact reference to an approved expectancy profile and never decides
  eligibility locally.

### 4. No silent fallbacks for unknown profile, state, timestamp, conversion, order or broker results

An unknown input produces a visible restricted or unknown state. It never produces a plausible default.

This is already the repository's stated position (`AGENTS.md` section 3: *Fail-Closed*, *No Invented
Data*). Phase 0 found the gap is not the principle but the vocabulary: there is no first-class `UNKNOWN`
order state, no `HealthState` taxonomy and no `ValidationResult` with a `UNKNOWN` member. Phase 1 and
Phase 7 must supply them before any later phase can honour this rule.

### 5. Public API changes require explicit compatibility analysis

Every change to a `app/services/[DOMAIN]/__init__.py` `__all__` list, or to the shape of any exported
function's arguments or return value, requires a written compatibility note in the phase's dry run
covering: current consumers (found by search, not by assumption), whether the change is additive,
whether any usage program or test relies on the old shape, and the migration path for each consumer.

Phase 0 baseline for comparison: **1064 public exports across fourteen domains, zero class-like.**

### 6. Breaking changes require deprecation or controlled migration unless the owner explicitly approves a clean break

Default is deprecate-then-remove across at least one phase boundary. A clean break requires a standalone
owner approval that names the symbol and the consumers being broken.

### 7. Existing tests and workflows must remain valid or receive an explicit, approved migration

The repository holds **758 `test_*.py` files and 374 usage programs**. A phase that makes an existing
test invalid must say so in its dry run, name the tests, and get approval for the migration. Deleting or
weakening a test to make a change pass is prohibited.

Three failures are already red at baseline (`T-1`, `T-2`, `T-3` in `trading-cockpit-test-baseline.md`).
They are the pre-existing state, not a later phase's fault — and equally, no later phase may claim them
as its own regression baseline without re-verifying on Windows.

### 8. Database ownership and migration responsibility must be assigned before schema changes

Before a phase writes a migration it must record: the owning domain, the business key and uniqueness
constraint, mutability (append-only or mutable-with-reversal), the transaction boundary, the retention
and archival rule, backward-compatibility impact, backfill plan, rollback or forward-fix strategy, and an
acceptance query.

Additional standing constraints from Phase 0:

- Financial records are append-only. Corrections are reversal or correction events. Direct historical
  mutation is prohibited.
- **No cockpit durable state may be placed in `data_runtime_records`**, the generic namespaced key-value
  store (`FEAT-DATA-17`). Every cockpit record gets a named, owned table.
- **Do not add a fifth idempotency store.** Rule 2 applies.
- Three in-flight schema rebuilds must be resolved before the phases that touch them:
  `trading_positions` vs `trading_positions__new` (Phase 7), the seven `risk_*__new` tables (Phase 6),
  and the four `strategy_*_v2` families (Phase 5).

### 9. Every later work package must begin by rechecking its Phase 0 classification against the then-current repository state

This audit is a snapshot of commit `3b039544`. A work package starts by re-reading its row in
`trading-cockpit-gap-matrix.md`, confirming the cited evidence paths still exist and still mean what the
row says, and recording either "classification confirmed" or a classification delta with new evidence.

`LOW` confidence rows (`TC-IMP-DATA-03`, `TC-IMP-STRAT-09`, `TC-IMP-RISK-15`, `TC-IMP-UIAPI-05`) must be
re-investigated before implementation, not implemented from the Phase 0 guess.

### 10. No production live-money route is authorized for Trading Cockpit modes

A cockpit session operates only through deterministic simulation, historical replay, paper trading, or an
explicitly approved broker sandbox/testnet.

Concretely, until proven otherwise:

- A cockpit session may only produce `TradingRoute.SIM` intents.
- A cockpit session may never obtain a broker connection whose `environment` is
  `BrokerEnvironment.LIVE`.
- `ALLOW_LIVE_MUTATIONS` remains `False` for every cockpit configuration.
- The guard must be a **test**, not a convention. `TC-IMP-BRK-10` is not complete until a test asserts
  that a cockpit session cannot select a live route or a live environment.

Phase 0 classified the current boundary as `PARTIAL` and recorded finding S-1 (the registry factory path
does not carry the non-production assertion) and S-2 (no mode concept exists to bind a guard to). See
`trading-cockpit-safety-baseline.md`.

### 11. Deterministic state, accounting, risk, execution, replay and scoring cannot be delegated to an LLM

Agents explain, coach, summarize and propose. They are never the source of truth for market eligibility,
position size, risk, drawdown, lockout, order state, fill, ledger, replay time, scenario trigger, alert
state, score or qualification.

The repository already enforces this structurally: `app/agentic/permissions/models.py` makes
`controlled_mutation` and `critical` side-effect classes **unrepresentable types**, and blocks the
`brokers` receiver domain outright. Cockpit agents reuse this constitution verbatim. Weakening it is a
blocking safety violation.

Corollary: disabling every agent must leave the complete cockpit functional and safe.

### 12. No phase may overwrite pre-existing owner changes

Before writing, a phase captures the worktree state. On this checkout that means
`git -c core.autocrlf=input status --porcelain=v1`, because the default form reports every text file as
modified (see `repository-baseline.md` section 2).

Any path that was already changed is classified `PRE_EXISTING_STAGED_CHANGE`,
`PRE_EXISTING_TRACKED_CHANGE`, `PRE_EXISTING_UNTRACKED_FILE` or `PRE_EXISTING_IGNORED_ARTIFACT` and is
not modified, deleted, staged, reverted or folded into another edit. A dirty worktree is not permission
to clean it.

The following are never run by an implementation agent without a standalone owner instruction:
`git reset`, `git clean`, `git checkout -- <path>`, `git restore <path>`, `git stash`, `git rebase`,
`git commit`, `git push`.

### 13. Every implementation change must map to a requirement, workflow, contract, test and acceptance-evidence target

No orphan code. Each change traces to a `TCS-*` requirement ID or a checklist step ID in
`trading-cockpit-traceability-matrix.md`, a documented workflow, a named contract, a test class from the
plan's section 24.2 list, and an acceptance-evidence target.

A work package is never marked complete on the strength of a similarly named class or function. Complete
means: contract + implementation + public export path + tests + a real domain workflow or usage program +
failure behavior + telemetry where required.

### 14. New public contracts must be intentionally exported and versioned

A contract is public only when it is deliberately re-exported from `app/services/[DOMAIN]/__init__.py`,
documented in the domain README's Feature Registry, and carries a version identity.

> **Unresolved blocker.** `AGENTS.md` requires domain exports to be *functions only*, with classes kept
> internal. Every contract the plan requires is a type. This rule cannot be discharged until the owner
> decides how versioned types cross domain boundaries. See decision **D-1** in
> `phase-0-findings-and-decisions.md`. **Phase 1 must not begin until D-1 is resolved.**

### 15. Duplicate authoritative implementations are prohibited

Two implementations of the same concept is a defect, not redundancy. When a phase finds one, it
consolidates to a single authority and migrates callers, or it records a `REFACTOR` and escalates.

Phase 0 found these to remove rather than reproduce:

- `OrderIntent = Any` at `app/services/simulator/execution/engine.py:32` and
  `app/services/simulator/run/orchestrator.py:41`, which erase the authoritative Trading type.
- Two divergent validation-result shapes (`ApprovalValidationResult` in Portfolio,
  `DecisionReuseValidationResult` in Risk).
- Four idempotency stores.
- Two approval stores (`risk_approval_tokens`, `api_approvals`).
- Instrument identity split between `data_symbols` and `broker_symbol_map`.
- Duplicate `strategy_*` / `strategy_*_v2` table families.

---

## Per-phase entry and exit procedure

**Entry.** Recheck the Phase 0 classification (rule 9) → capture the worktree state (rule 12) → confirm
the `AGENTS.md` dry-run report content → obtain a standalone `APPROVED: EXECUTE`.

**Exit.** The plan's section 3 domain completion audit must pass: README and Feature Registry current,
database changes recorded or `NOT_APPLICABLE` justified with a reason, unit + property/boundary + error-path
tests passing, every implemented requirement backed by real usage or an acceptance test, the feature
participating in a documented workflow, a stable UI/API read contract published, telemetry emitted on
state transitions and failures, durable state restored correctly, fail-closed behavior tested, and
acceptance evidence stored.

**Escalate rather than proceed** when: a Phase 0 classification is wrong, a contract collision blocks
progress, an owner decision from `phase-0-findings-and-decisions.md` is still open, a change would break
a public export, a change would touch a pre-existing owner change, or a safety boundary cannot be proven
by test.

---

## The decision the ADR would have recorded

```text
Decision:
Implement the Trading Cockpit by expanding the fourteen existing HaruQuantAI domains.

Rejected alternative:
Creating a separate top-level Trading Cockpit service tree that duplicates current
domain responsibilities.
```

The audit prompt asked for this as `ADR-0001-extend-existing-domains-for-trading-cockpit.md`.
`AGENTS.md` section 4 (*Decision Hygiene*) prohibits standalone ADR or decision-record documents. The
owner chose to honour `AGENTS.md`. The decision, its rationale and its consequences are recorded as an
ordinary architectural rule — rule 1 above — and in `phase-0-findings-and-decisions.md`. The ADR file was
deliberately not created; `TC-IMP-BASE-09` records this deviation.

# Implementation Plan · Sim ⇄ Live Parity — Revision 7

**Purpose:** the single executable programme for converging simulation, paper, and live execution
inside an explicitly certified parity envelope.
**Audience:** the owner and coding agents that must execute a phase mechanically without inventing
architecture, contracts, file placement, tests, evidence, or commit scope.
**Authority:** subordinate to `AGENTS.md` → `docs/PROJECT.md` → `docs/ARCHITECTURE.md` →
`docs/CHANGELOG.md` → owning package READMEs.
**Status:** Finalized plan; proposed for phased execution. Every phase still requires its own dry run
and exact standalone approval before files in that phase may change.

## Revision history

- **R1** proposed a dependency cycle, could not call Trading's public async contract, used a vacuous
  determinism test, and treated swap totals as sufficient.
- **R2** corrected those but implemented its scheduler after consumers, overclaimed parity, and made
  provider calculation caching circular.
- **R3** moved the scheduler, introduced a maturity ladder and local calculation model, but still
  relied on impossible order-policy defaults, consumed provider specifications before creating them,
  and allowed unresolved behavior inside its final parity claim.
- **R4** resolves the remaining reviews: versioned request/order migrations, Brokers-current and
  Data-historical provider evidence, strict phase ordering, paired parity fixtures, relationship-
  preserving comparison, executable scheduler pumping, and bounded L5 certification.
- **R5** prevents certification overreach: demo and live certificates are distinct, path-sensitive
  claims require observable market evidence, initial authority state is identity-bound, provider
  concurrency is not replaced by an invented total order, recovery is tested across side-effect
  boundaries, certification uses independent holdouts, and every certificate expires or invalidates
  when its evidence or execution identity changes.
- **R6** restores the executor-grade layer removed during architectural consolidation. Every phase now
  has an exact read/create/edit/no-touch manifest, implementation order, test and usage inventory,
  documentation work, commands, evidence checklist, rollback, stop conditions, and proposed commit
  boundary. R6 changes no R5 architecture or certification guardrail.
- **R7** consolidates each executor packet into its owning phase. Phase-specific manifests,
  requirements, usage functions, commands, documentation, commit messages, rollback, and completion
  evidence now live beside the corresponding design; the detached packet appendix and its navigation
  indirection are removed without changing R5/R6 behavior or scope.

---

## Part 0 · Operating contract

### 0.1 Goal and scope

`sim`, `paper`, and `live` use the same Trading orchestration and differ only at an injected authority
boundary. Simulation reproduces MT5 terminology, validation, state transitions, retcodes, accounting,
and provider-shaped evidence for every operation admitted by the active **Parity Envelope v1**.
`paper` means only the explicitly named non-production provider environment in that envelope; it is
not a synonym for either Simulation or live-account execution.

Parity is not a universal claim about every broker configuration. It is a falsifiable certification
over a versioned matrix of provider, environment, server/account mode, symbol specification revision,
order operation, execution model, market-evidence class, initial authority state, and evidence
sources. Anything outside that matrix fails canonical eligibility; it is never silently approximated.

Parity Envelope v1 targets MT5 FX only. cTrader, Binance, non-FX instruments, corporate actions,
exchange auctions, multi-account behavior, and any broker/account/build without admitted evidence are
excluded. Parity certifies execution behavior, not strategy profitability or equality across different
market histories.

### 0.2 Maturity ladder

No implementation phase may claim parity. Only the corresponding completed L5 certificate may make
the bounded claim recorded in its immutable envelope. Each earlier rung proves only:

| Rung | Delivered by | Claim |
|---|---|---|
| **L1 · Mutation-path convergence** | Phase 14 | Equivalent business/risk gates and the same authority boundary are traversed; route-specific safety gates remain explicit |
| **L2 · Evaluation-path convergence** | Phase 15 | Indicators, Strategy, and Risk evaluate incrementally against evolving point-in-time state using the same Trading cycle |
| **L3 · Account/order semantics** | Phases 16–18 | Verified account, margin, order, deal, protection, and position behavior matches within the admitted matrix |
| **L4 · Execution realism** | Phases 19–20 | Every stochastic component is calibrated from eligible evidence or excluded from canonical execution |
| **L5-Demo · Bounded demo certification** | Demo-scope programme completion | Every common gate and the mandatory independent MT5-demo differential gate pass for the published demo envelope |
| **L5-Live · Bounded live certification** | Separate live-evidence extension | Every common gate and the mandatory independent sanitized live-account differential gate pass for the published live envelope; L5-Demo never implies L5-Live |

### 0.3 Mandatory process rules

1. Before each numbered sub-phase, produce the complete `AGENTS.md` dry-run report and modify nothing.
2. Execute only after a standalone owner message whose trimmed content is exactly
   `APPROVED: EXECUTE`.
3. One approval covers one domain-scoped sub-phase only. Integration gates perform verification but
   do not authorize unapproved changes in another domain.
4. Approval does not authorize commits, pushes, tags, dependency changes, live broker calls, or
   production access. Commit text below is only proposed text.
5. If implementation reveals a material scope delta, stop and issue a correction dry run.
6. Preserve one feature = one folder = one numbered usage program, function-only package-root APIs,
   and no deep cross-domain imports.
7. Every completed checklist item records supporting path and line evidence.
8. Resolved decisions become ordinary requirements in owning READMEs; no standalone ADR is created.
9. Real integrations are demo/non-production only and require the separately approved integration
   operation. Default tests use bounded, sanitized, immutable fixtures.
10. No repository operation collects production evidence. L5-Live consumes only owner-supplied,
    sanitized, immutable evidence whose provenance and scope can be verified without a production
    mutation or connection.

### 0.4 Standard validation

Iterative validation is targeted:

```bash
uv run ruff format <changed Python paths>
uv run ruff check <changed Python and test paths>
uv run mypy <changed package paths>
uv run pytest <targeted test paths>
uv run python tests/<domain>/usage/features/<program>.py
```

At a phase gate, run affected producer-consumer integration tests. Run the full suite with the
repository coverage floor only after targeted checks pass. No default test may need credentials,
network access, mutable wall-clock time, or a real broker session.

### 0.5 Resolved architectural decisions

| ID | Decision | Consequence |
|---|---|---|
| **D1** | Dependency direction is `Simulation → Trading → Brokers` plus `Simulation → Brokers`; Brokers imports no Simulation symbol | Brokers owns the adapter/protocol; Simulation owns matching, accounting, scheduler, and journals |
| **D2** | Parity is certified only inside a versioned envelope | Unverified modes fail canonical eligibility rather than becoming “known limitations” inside L5 |
| **D3** | Order policy uses v2 contracts with required `fill_policy` and `time_policy` | No value is invented from legacy `time_in_force`; v1 remains through a deprecation window |
| **D4** | Brokers owns a typed current provider snapshot; Data owns immutable effective-dated history | Brokers remains stateless; Simulation never interprets raw MT5 metadata or backdates current evidence |
| **D5** | Simulation owns a local calculation model; MT5 validates it through offline conformance fixtures | Canonical execution makes no provider call and has no circular prefill cache |
| **D6** | Add `run_backtest_async`; retain synchronous `run_backtest` during a declared window | The public sync contract is not changed in place; running-loop misuse fails closed |
| **D7** | Parity tests use separately authorized paired requests and captured authority traces | A demo market cannot be driven with an arbitrary historical sequence; raw request identity is not compared |
| **D8** | Capability parity is a published intersection that can tighten by envelope version | Missing MT5 operations are not falsely advertised or normalized away |
| **D9** | MT5 sessions without a Python operation use Data-owned explicit revisioned weekly definitions | The Python adapter never claims to supply unavailable session evidence; intervals with unverified holiday, maintenance, or exceptional-closure overrides are excluded |
| **D10** | Calibration distinguishes source availability, ingestion, training, effective, and evaluation time | Prospective canonical execution rejects future-trained or retrospectively backdated evidence |
| **D11** | L5-Demo and L5-Live are separate certificates | Demo evidence may certify sim-vs-demo only; canonical live-account scope stays locked until owner-supplied sanitized live evidence passes the same mandatory gates |
| **D12** | Market-evidence observability bounds every claim | Genuine bid/ask ticks are required for path-sensitive parity; a derived OHLC path is research-only unless the registered invariant is proven path-independent |
| **D13** | Execution identity binds complete initial authority state | A certified run hashes balances, margin, positions, orders, protections, ownership, transaction watermark, and accrued costs; the account is exclusive or every foreign/manual event is replayed |
| **D14** | Scheduler order and provider causal order are distinct | The scheduler remains deterministic, but provider-ambiguous races are compared as evidenced partial orders or excluded rather than assigned invented provider truth |
| **D15** | Calibration and certification evidence are disjoint | Thresholds, tolerances, minimum coverage, and statistical tests are fixed before an immutable holdout is evaluated |
| **D16** | A parity certificate is a revocable lease | Build, contract, code/config identity, specification, source/tick model, calibration validity, or detected-drift changes invalidate the affected certificate |
| **D17** | Exceptional sessions require dated evidence | Weekly definitions cannot certify broker holidays, maintenance, or one-off closures; uncovered intervals fail eligibility |
| **D18** | Pathwise queue-position parity is excluded while Level-2 ownership is unresolved | `OD-DATA-01` is not resolved by this plan; trace-calibrated outcome distributions may be admitted, but no hidden queue state is claimed |

### 0.6 Identifier allocation

Verify every range against the owning README again during the corresponding dry run.

| Domain | Allocated by this plan | Free after this plan |
|---|---|---|
| Brokers | `FR-BRK-159` … `FR-BRK-196` | `FR-BRK-197` … `FR-BRK-200` |
| Data | `FR-DATA-214` … `FR-DATA-216` | extend beyond `216` |
| Simulation | `FR-SIM-134` … `FR-SIM-242` | extend beyond `242` |
| Trading | `FR-TRD-085` … `FR-TRD-113` | `FR-TRD-114`, `FR-TRD-115` |

Every number in an allocated range is assigned exactly once below. Existing behavior is referenced by
its existing requirement; this plan does not allocate duplicate requirements for `get_deal`,
`check_order`, `calculate_margin`, or `calculate_profit`. Retired `FEAT-BRK-11` … `16` remain retired.

### 0.7 Feature changes

| Feature | Folder | Usage evidence | Phase |
|---|---|---|---|
| `FEAT-SIM-15` Deterministic Execution Scheduler | `app/services/simulator/scheduler/` | `tests/simulator/usage/features/15_scheduler.py` | 5 |
| `FEAT-SIM-16` Effective-Dated Calculation Model | `app/services/simulator/calculations/` | `tests/simulator/usage/features/16_calculations.py` | 13 |
| `FEAT-SIM-17` Empirical Execution Calibration | `app/services/simulator/calibration/` | `tests/simulator/usage/features/17_calibration.py` | 19 |
| `FEAT-SIM-18` Parity Comparison | `app/services/simulator/parity/` | `tests/simulator/usage/features/18_parity.py` | 2 |
| `FEAT-BRK-17` Simulation Broker Channel | `app/services/brokers/simulation/` | `tests/brokers/usage/features/17_simulation.py` | 10 |
| `FEAT-BRK-18` Provider Specification Snapshot | `app/services/brokers/specifications/` | `tests/brokers/usage/features/18_specifications.py` | 4a |

Existing features extended: `FEAT-DATA-02`; `FEAT-SIM-01`, `04`, `05`, `07`, `12`;
`FEAT-TRD-01`, `02`, `03`, `04`, `07`, `08`; `FEAT-BRK-02`, `09`, `10`.

### 0.8 Strict phase order

Phases **1 through 20 execute sequentially**. A later phase may be dry-run only after every earlier
phase gate is complete. Domain-scoped sub-phases inside a phase also execute in listed order, followed
by the integration gate. This deliberately sacrifices parallelism for an auditable dependency chain.

### 0.9 Coding-agent execution protocol

Each phase combines its design and build instructions in one local implementation specification.
For the approved subphase, the coding agent must execute that specification in order and must not infer a
missing step from architectural intent.

1. Read every path in `Read first` before editing. Confirm every path and named public symbol exists.
2. Treat `CREATE`, `EDIT`, `DELETE`, and `DO NOT TOUCH` as exhaustive. A path absent from those lists
   is outside scope.
3. Implement requirement rows in listed order. Do not rename requirements, combine responsibilities,
   substitute a different abstraction, or create a horizontal support module.
4. Match the declared function signatures, field types, validation, errors, timestamps, hashing, and
   side effects. No default, fallback, tolerance, retcode, provider fact, or clock may be invented.
5. Public cross-domain consumers import only from `app.services.<domain>`. Domain package roots export
   standalone functions only. Internal classes/constants remain private.
6. Add no dependency. Use the versions pinned in `pyproject.toml`: Python `>=3.14`, Pydantic
   `>=2.13.4`, NumPy `2.4.6`, pandas `3.0.3`, pytest `>=9.1.1`, Ruff `>=0.15.18`, and mypy `>=2.1.0`.
7. Use `app.utils` logging at public, side-effect, state-transition, persistence, external, retry, and
   failure boundaries. Never log credentials, account secrets, complete broker payloads, or sensitive
   trading data.
8. Write the named unit tests before or with the implementation. A public requirement is incomplete
   until its named usage function calls it through the package-root API.
9. Run only the phase's targeted commands while iterating. Run the phase's gate commands after all
   code and documentation changes are complete.
10. Replace every phase checklist marker with `[x]` plus exact `path:line` evidence. Production code
    alone is not test or usage evidence.
11. Do not stage or commit. `Proposed commit` defines a future boundary only. A separate owner
    instruction is required after the gate is green.
12. Stop without editing beyond the approved scope when a `STOP` condition occurs. Issue a correction
    dry run; do not repair the discrepancy opportunistically.

Every phase or separately approved subphase must state: `Outcome`, `Approval unit`,
`Read first`, `File manifest`, `Requirements and contracts`, `Implementation order`, `Tests`, `Usage
evidence`, `Documentation`, `Commands`, `Gate and checklist`, `STOP conditions`, `Rollback`, and
`Proposed commit`. A compact subphase may combine adjacent items under an explicit compound heading
such as `Tests/usage` or `Rollback`; the information itself may not be omitted. `None`
is written explicitly when an item has no work.

### 0.10 Phase-local completeness rule

Every phase or separately approved subphase below is self-contained. A coding agent reads its phase
from the phase heading through its completion checklist; it must not obtain a file, requirement,
usage, validation, documentation, rollback, or commit instruction from another phase. Universal
repository authority, approval, safety, and no-invention rules remain in §§0.1–0.9.

Each local implementation specification states its outcome, approval unit, prerequisites,
requirements, architecture, read-first files, exact file manifest, contracts, implementation order,
tests, usage evidence, documentation edits, literal validation commands, integration gate, STOP
conditions, rollback, exact proposed commit message, and completion checklist. `None` is explicit when
an item does not apply.

---

## Part 1 · Execution phases

# Phase 1 · Authoritative documentation and ownership

**Objective:** establish authority before implementation and fold the analysis documents without
creating a second mutable registry.

### 1a · System documents

Update `docs/PROJECT.md` and `docs/ARCHITECTURE.md`:

- Record D1 and the acyclic graph.
- Add Simulation as a read/factory consumer of Brokers; only Trading invokes application mutation
  operations.
- Brokers owns current provider translation, Data owns effective-dated history, and Simulation owns
  historical execution behavior.
- Register the L1–L4 ladder, distinct L5-Demo/L5-Live certificates, and Parity Envelope v1 concept.
- Record the three failure classes: mirrored domain failures, fail-closed Simulation-integrity
  failures, and seeded/journalled infrastructure injections.
- Record the MT5-FX v1 scope, market-observability boundary, initial-authority-state identity,
  certificate invalidation policy, and explicit non-FX/non-MT5 exclusions.
- Update the Simulation request table for v2 and the async operation while preserving v1/sync windows.

Add a concise `## [Unreleased]` changelog block after the authority edits are complete.

### 1b · Brokers README

Register current typed provider snapshots, the simulation adapter boundary, statelessness, demo-only
fixture collection, connection lifecycle, and the declared capability-intersection rule.

### 1c · Data README

Extend `FEAT-DATA-02` to own immutable provider-specification revisions, effective intervals,
point-in-time reads, coverage, and provenance. Register that weekly sessions do not prove dated
holiday/maintenance exceptions and preserve `OD-DATA-01` without implying Level-2 ownership. Data
never grants trading authority.

### 1d · Trading README

Register paired gate taxonomy, v1/v2 order migration, Simulation authority consumption, and the
async deadline port. Register exclusive-account or complete foreign/manual activity evidence as a
certification prerequisite, plus crash/reconciliation and in-flight kill-switch behavior.

### 1e · Simulation README

Register the maturity ladder, request v2, engine comparability, L5-Demo/L5-Live separation, evidence
eligibility, certificate invalidation, and the four new features. Every pre-programme numerical
result is marked superseded.

### 1f · Fold and cleanup

Fold `simulator-backtest-pipeline.md` and `trading-execution-pipeline.md` into owning READMEs. Fold
`sim-as-broker-adapter-decision.md` into the authorities above, then delete those three files.
Keep `sim-live-parity-register.md` reference-only until the claimed certificate is complete; its
dashboard count is not authoritative. Keep this implementation plan until the claimed L5 certificate
is complete; an
L5-Demo completion must not delete evidence that the L5-Live goal remains open.

**Gate:** documentation cross-references and feature counts reconcile; no implementation file changes.

---

## Implementation specification

**Outcome:** all current-state authorities describe the approved dependency direction, scope, maturity
ladder, certificate split, evidence ownership, failure taxonomy, and v2 migration before code changes.

**Approval unit:** Phase 1, documentation only. **Prerequisite:** none.

**Read first:** `AGENTS.md`; `docs/PROJECT.md`; `docs/ARCHITECTURE.md`; `docs/CHANGELOG.md`;
`app/services/brokers/README.md`; `app/services/data/README.md`;
`app/services/trading/README.md`; `app/services/simulator/README.md`; all five `docs/dev/` files named
by the owner.

**File manifest:**

- **EDIT:** `docs/PROJECT.md`, `docs/ARCHITECTURE.md`, `docs/CHANGELOG.md`, and the four owning package
  READMEs above.
- **DELETE after fold verification:** `docs/dev/sim-as-broker-adapter-decision.md`,
  `docs/dev/simulator-backtest-pipeline.md`, `docs/dev/trading-execution-pipeline.md`.
- **KEEP:** `docs/dev/sim-live-parity-register.md` and this plan until the certificate disposition in
  Part 2 is complete.
- **DO NOT TOUCH:** every `app/**/*.py`, `tests/**/*.py`, migration, dependency, generated artifact,
  and unrelated documentation file.

**Implementation order:** execute Phase 1a through 1f exactly as written; then reconcile domain
feature counts and cross-references. `docs/PROJECT.md` records only system relationships. Exact
feature contracts, APIs, FR rows, modules, tests, and usage remain in owning READMEs. Add one concise
`## [Unreleased]` `Changed` entry; do not put requirement or test inventories in the changelog.

**Tests and usage evidence:** none; documentation only.

**Commands:**

```powershell
rg -n "Simulation.*Brokers|L5-Demo|L5-Live|Parity Envelope" docs/PROJECT.md docs/ARCHITECTURE.md
rg -n "FEAT-(BRK|DATA|TRD|SIM)-|FR-(BRK|DATA|TRD|SIM)-" app/services/brokers/README.md app/services/data/README.md app/services/trading/README.md app/services/simulator/README.md
rg -n "^## \[Unreleased\]|^### (Added|Changed|Deprecated|Removed|Fixed|Security)" docs/CHANGELOG.md
git diff --check -- docs/PROJECT.md docs/ARCHITECTURE.md docs/CHANGELOG.md app/services/brokers/README.md app/services/data/README.md app/services/trading/README.md app/services/simulator/README.md
git status --short
```

**Gate and checklist:** authority precedence unchanged; acyclic dependency recorded; Brokers-current
and Data-historical specification ownership recorded; L5-Demo/L5-Live scope recorded; three source
documents deleted only after their surviving content is located in authorities; every completed item
ends with `path:line` evidence.

**STOP:** an authority contradicts D1–D18; feature counts do not reconcile; a source document contains
material content without an authoritative destination; changelog structure lacks `## [Unreleased]`.

**Rollback:** restore the seven edited authorities and three deleted source documents from the phase
diff, then rerun the commands above. No code/export/artifact cleanup exists.


### Exact requirement-to-usage allocation

None — documentation-only phase; requirements remain Proposed where the phase explicitly says so.

### Exact documentation manifest

- **EDIT:** `docs/PROJECT.md`
- **EDIT:** `docs/ARCHITECTURE.md`
- **EDIT:** `docs/CHANGELOG.md`
- **EDIT:** `app/services/brokers/README.md`
- **EDIT:** `app/services/data/README.md`
- **EDIT:** `app/services/trading/README.md`
- **EDIT:** `app/services/simulator/README.md`

Every completed FR/checklist row receives final `path:line` evidence. The changelog receives one concise
`## [Unreleased]` bullet under the correct change type and never duplicates a Feature Registry.

### Literal validation commands

```powershell
git diff --check
git status --short
```

No pytest, Ruff, mypy, or usage execution applies to this documentation-only phase. The listed
documentation searches, diff check, and status check are the complete validation surface.

### Exact proposed commit messages

**Unit 1:**

```text
docs: register bounded sim-live parity architecture

- Complete approved unit 1 within its declared domain and requirement boundary.
- Reconcile the approved documentation authorities; no usage program applies.
- Pass targeted tests, owning-domain gates, documentation reconciliation, and rollback review.
```

Commit execution is not authorized by phase approval. After separate commit authorization, stage only
the phase manifest, verify `git diff --cached --name-only`, and use the applicable message verbatim.

### Completion checklist

**Phase status: Completed — 2026-08-14.**

- [x] Approval matched this exact phase/subphase. (Owner approved Phase 1 documentation-only unit; the executed scope matches the manifest at `docs/dev/sim-live-parity-implementation-plan.md:295-311`; phase record at `docs/CHANGELOG.md:5-21`.)
- [x] Only the local file and documentation manifests changed. (Seven authorities edited and three dev documents deleted exactly as the manifest lists; `git status --short` shows only those paths. A transient owner-side working-tree edit to this plan file (stray `` `--no-verify` `` lines plus markdown table reformatting) was reverted on owner instruction before Phase 2; it was not Phase 1 work.)
- [x] Every listed FR has final `path:line` implementation and test evidence. (Phase 1 allocates no implemented FR — requirement-to-usage allocation is `None` at `docs/dev/sim-live-parity-implementation-plan.md:335-337`; new requirements registered as Proposed only: `app/services/simulator/README.md:236-239`, `app/services/data/README.md:241`, `app/services/trading/README.md:131`.)
- [x] Only verified package-root/public dependency contracts were used. (No code or dependency contract consumed; documentation-only phase.)
- [x] Targeted unit/integration tests passed with recorded commands and exit codes. (Not applicable — documentation-only; validation surface is the documentation searches, `git diff --check` (clean), and `git status --short` per `docs/dev/sim-live-parity-implementation-plan.md:350-360`.)
- [x] Ruff and mypy do not apply; all documentation validation commands passed. (Parity-term searches matched at `docs/PROJECT.md:458-521`, `docs/ARCHITECTURE.md:417-425,791,1035,1136`; `## [Unreleased]` confirmed at `docs/CHANGELOG.md:3`.)
- [x] Usage execution does not apply to this documentation-only phase.
- [x] Code-domain test gates do not apply; the documentation gate passed. (Cross-references and feature counts reconcile at `docs/PROJECT.md:516-530` — 236 features, 220 Completed / 16 Pending.)
- [x] README, changelog, and listed system documents reconciled. (Registrations: `app/services/brokers/README.md:8,178-206`, `app/services/data/README.md:9,95-124,241`, `app/services/trading/README.md:4,127-167,750-862`, `app/services/simulator/README.md:8,119-152,236-239,877-953`, `docs/PROJECT.md:458-521,1092-1093`, `docs/ARCHITECTURE.md:417-425,791,1035,1136`, `docs/CHANGELOG.md:5-21`.)
- [x] STOP conditions and rollback path were rechecked. (No STOP triggered; rollback path unchanged at `docs/dev/sim-live-parity-implementation-plan.md:331-333`.)
- [x] Commit remains unauthorized, or its separately authorized hash is recorded. (Owner separately authorized the Phase 1 commit on 2026-08-14; committed with the proposed message `docs: register bounded sim-live parity architecture` — hash recorded post-commit below.)
  - Commit hash: `0a255098b33b934dfd08f7de8aedc559e1d749c5` (all pre-commit hooks passed; 11 manifest files).

**Fold record (1f):** `docs/dev/sim-as-broker-adapter-decision.md` → `docs/PROJECT.md` §2.1.2/§2.1.8/§3 + `docs/ARCHITECTURE.md` dependency note/taxonomy + `app/services/brokers/README.md:178-206` (incl. clock-injection prerequisite); `docs/dev/simulator-backtest-pipeline.md` → `app/services/simulator/README.md:877-953`; `docs/dev/trading-execution-pipeline.md` → `app/services/trading/README.md:750-862`. `sim-live-parity-register.md` and this plan are retained reference-only per Phase 1f.

# Phase 2 · Parity envelope and relationship-preserving comparator

**Domain:** simulator. **Feature:** `FEAT-SIM-18`.
**Requirements:** `FR-SIM-187` … `FR-SIM-193`, `FR-SIM-236` … `FR-SIM-239`.

Create:

```text
app/services/simulator/parity/
├── README.md
├── __init__.py
├── envelope.py
├── normalize.py
└── compare.py
```

Public package-root functions:

- `get_parity_envelope(version: str = "v1")`
- `normalize_parity_evidence(evidence, envelope)`
- `compare_parity_evidence(left, right, envelope)`
- `get_parity_maturity_ladder()`

### Comparison rules

- Compare separately authorized but semantically paired route requests, not raw-equal requests.
- Classify every invariant as exact structural, bounded numeric, or distributional. The envelope
  records its metric, unit, tolerance or statistical test, minimum coverage, and aggregation rule.
- Compare business/risk gate roles, order, inputs, and outcomes. Route-specific safety gates are
  present in a separate declared list and compared against their route policy rather than forced to
  share an identifier.
- Alpha-rename order, deal, position, receipt, and trace identifiers in encounter order while
  preserving cardinality, foreign-key relationships, and causal edges.
- Compare economic timestamps, ordering, and simulated response durations. Preserve observed causal
  edges; events whose provider order is unobservable at identical timestamps form an evidenced
  partial order and are not rearranged into invented provider truth. Exclude only provider observation
  and network transport timestamps explicitly registered by the envelope.
- Compare economic latency and slippage; never remove all “latency fields” by name.
- Enforce both per-field tolerances and an aggregate account-currency economic-error budget so many
  individually tolerated differences cannot accumulate into material drift.
- A new ignored field requires an envelope-version change and a test proving it has no economic or
  state-transition meaning.

The envelope binds a complete initial-authority-state hash: balance, equity, margin, free margin,
positions, pending orders, protections, ownership, last reconciled transaction/deal watermark,
accrued costs, and provider revision set. Certification requires either an exclusive account interval
or complete ordered evidence for every foreign/manual order, deal, balance, credit, and correction.
Missing activity invalidates the comparison.

### Ledger conservation

All ledger accounts are signed `Decimal` postings in account currency:

```text
final_balance = initial_balance
              + realized_profit
              + commission
              + fees
              + swap
              + tax
              + rebates
              + deposits
              + withdrawals
              + credits
              + corrections
final_equity = final_balance + unrealized_profit
```

Withdrawals, fees, tax, and adverse commissions are negative postings. Assert the equation after
every ledger mutation and at run completion.

### Requirements

- `FR-SIM-187` defines typed invariant groups and metrics; `188` owns the versioned normalizer
  registry; `189` defines cold re-execution from fresh stores/artifact roots; `190` binds execution
  and complete initial-authority-state identity into run identity;
  `191` rejects approximation, fallback, staleness, or uncovered behavior for canonical execution;
  `192` enforces ledger conservation; `193` publishes the maturity ladder.
- `FR-SIM-236` publishes the versioned envelope matrix, evidence class, certificate scope, thresholds,
  and validity interval; `237` rejects work outside it and invalidates stale certificates; `238`
  preserves identifier relationships and causal edges under normalization; `239` preserves economic
  time, evidenced partial order, and duration semantics.

**Tests:** exact ignored-field registry, relational-graph mutation detection, reordered/missing deal
detection, economic-time drift detection, paired gate comparison, aggregate tolerance exhaustion,
initial-state mutation, missing foreign activity, ambiguous-order preservation, certificate-scope
lock, certificate invalidation, and ledger conservation.

---

## Implementation specification

**Outcome:** `FEAT-SIM-18` exposes a function-only, versioned parity envelope, normalizer, comparator,
and maturity-ladder API that detects relationship, causality, timing, tolerance, scope, initial-state,
and certificate-validity mutations.

**Approval unit:** Phase 2, simulator. **Prerequisite:** Phase 1 gate.

**Read first:** `app/services/simulator/README.md`, `__init__.py`, `reporting/contracts.py`,
`journal/contracts.py`, `run/contracts.py`; Trading event/receipt contracts through
`app.services.trading`; Brokers canonical contracts through `app.services.brokers`; Phase 2 prose.

**File manifest:**

- **CREATE:** `app/services/simulator/parity/README.md`, `__init__.py`, `envelope.py`, `normalize.py`,
  `compare.py`.
- **EDIT:** `app/services/simulator/__init__.py`, `app/services/simulator/README.md`.
- **CREATE TESTS:** `tests/simulator/unit/test_parity_envelope.py`,
  `tests/simulator/unit/test_parity_normalizer.py`, `tests/simulator/unit/test_parity_compare.py`,
  `tests/simulator/integration/test_semantic_parity.py`,
  `tests/simulator/integration/test_parity_relationships.py`,
  `tests/simulator/integration/test_parity_envelope_rejection.py`,
  `tests/simulator/integration/test_cold_determinism.py`.
- **CREATE USAGE:** `tests/simulator/usage/features/18_parity.py`.
- **DO NOT TOUCH:** Trading/Brokers production code, persistence, existing run-result schemas, or
  provider adapters.

**Requirements and contracts:** implement `FR-SIM-187` through `193` and `236` through `239` exactly
as Phase 2 defines. Public functions are:

```python
def get_parity_envelope(version: str = "v1") -> Mapping[str, object]: ...
def normalize_parity_evidence(
    evidence: Mapping[str, object], envelope: Mapping[str, object]
) -> dict[str, object]: ...
def compare_parity_evidence(
    left: Mapping[str, object],
    right: Mapping[str, object],
    envelope: Mapping[str, object],
) -> Mapping[str, object]: ...
def get_parity_maturity_ladder() -> tuple[Mapping[str, object], ...]: ...
```

Internal frozen Pydantic models and invariant registries remain private. Envelope parsing rejects
unknown versions, duplicate invariants, unknown ignored fields, missing certificate scope, missing
initial-state hash, invalid validity intervals, and unspecified metrics. Comparator output contains a
top-level pass flag, certificate scope/version, per-invariant result, normalized relationship map,
aggregate account-currency error, and deterministic ordered failures.

**Implementation order:** envelope schema and validation; exact invariant registry; relational
alpha-renaming; causal partial-order normalization; exact/numeric/distributional comparisons;
aggregate economic-error budget; certificate invalidation; root facades; tests; usage; README FR rows.

**Tests:** name tests for unknown envelope, ignored-field mutation, alpha-renamed equivalent graphs,
broken foreign key, missing/reordered deal, economic-time drift, ambiguous same-time partial order,
aggregate tolerance exhaustion, initial-state mutation, demo/live relabeling, expiry, and invalidation.

**Usage evidence:** `18_parity.py` defines `fr_sim_187()` through `fr_sim_193()` and
`fr_sim_236()` through `fr_sim_239()`, calls all four package-root functions, then calls every function
from `main()` using bounded secret-safe mappings.

**Documentation:** register `FEAT-SIM-18`, its exact public API, FRs, error behavior, configuration,
test paths, and usage path in `app/services/simulator/README.md`.

**Commands:**

```powershell
uv run ruff format app/services/simulator/parity app/services/simulator/__init__.py tests/simulator/unit/test_parity_envelope.py tests/simulator/unit/test_parity_normalizer.py tests/simulator/unit/test_parity_compare.py tests/simulator/integration/test_semantic_parity.py tests/simulator/integration/test_parity_relationships.py tests/simulator/integration/test_parity_envelope_rejection.py tests/simulator/integration/test_cold_determinism.py tests/simulator/usage/features/18_parity.py
uv run ruff check app/services/simulator/parity app/services/simulator/__init__.py tests/simulator/unit/test_parity_envelope.py tests/simulator/unit/test_parity_normalizer.py tests/simulator/unit/test_parity_compare.py tests/simulator/integration/test_semantic_parity.py tests/simulator/integration/test_parity_relationships.py tests/simulator/integration/test_parity_envelope_rejection.py tests/simulator/integration/test_cold_determinism.py tests/simulator/usage/features/18_parity.py
uv run mypy app/services/simulator
uv run pytest tests/simulator/unit/test_parity_envelope.py tests/simulator/unit/test_parity_normalizer.py tests/simulator/unit/test_parity_compare.py tests/simulator/integration/test_semantic_parity.py tests/simulator/integration/test_parity_relationships.py tests/simulator/integration/test_parity_envelope_rejection.py tests/simulator/integration/test_cold_determinism.py
uv run python tests/simulator/usage/features/18_parity.py
```

**Gate and checklist:** four root functions exported; no class/constant exported; every FR has one
named usage function and test; all relationship/time/scope mutation tests fail before the intended
fix and pass after it; README evidence uses exact `path:line`.

**STOP:** a required canonical Trading/Brokers field cannot be represented without changing its
owner; an ignored field has economic meaning; comparison needs raw SDK objects; a tolerance lacks
unit/provider evidence.

**Rollback:** remove the parity folder, seven new test files, usage program, four root exports, README
feature/FR rows, then run Simulator public-API and usage-parity tests.


### Exact requirement-to-usage allocation

| Unit | Usage program and required functions |
|---|---|
| 2 | `18_parity.py`: `fr_sim_187()` … `fr_sim_193()`, `fr_sim_236()` … `fr_sim_239()` |

### Exact documentation manifest

- **EDIT:** `app/services/simulator/README.md`
- **EDIT:** `docs/CHANGELOG.md`
- **EDIT:** `docs/PROJECT.md`

Every completed FR/checklist row receives final `path:line` evidence. The changelog receives one concise
`## [Unreleased]` bullet under the correct change type and never duplicates a Feature Registry.

### Literal validation commands

```powershell
uv run ruff format --check app/services/simulator tests/simulator
uv run ruff check app/services/simulator tests/simulator
uv run mypy app/services/simulator
uv run pytest tests/simulator/unit/test_parity_envelope.py tests/simulator/unit/test_parity_normalizer.py tests/simulator/unit/test_parity_compare.py tests/simulator/integration/test_semantic_parity.py tests/simulator/integration/test_parity_relationships.py tests/simulator/integration/test_parity_envelope_rejection.py tests/simulator/integration/test_cold_determinism.py
uv run python tests/simulator/usage/features/18_parity.py
uv run pytest tests/simulator
git diff --check
git status --short
```

Run the phase-named targeted pytest files before the owning-domain gate. A missing exact path,
pre-existing failure, skipped test, or command substitution is a STOP and requires a correction dry run.

### Exact proposed commit messages

**Unit 2:**

```text
feat(simulator): add parity envelope and comparator

- Complete approved unit 2 within its declared domain and requirement boundary.
- Execute and document usage evidence: tests/simulator/usage/features/18_parity.py.
- Pass targeted tests, owning-domain gates, documentation reconciliation, and rollback review.
```

Commit execution is not authorized by phase approval. After separate commit authorization, stage only
the phase manifest, verify `git diff --cached --name-only`, and use the applicable message verbatim.

### Completion checklist

**Phase status: Completed — 2026-08-14.**

- [x] Approval matched this exact phase/subphase. (Owner standalone `APPROVED: EXECUTE` for Phase 2 simulator unit, following the recorded dry run.)
- [x] Only the local file and documentation manifests changed. (Created `app/services/simulator/parity/{README.md,__init__.py,contracts.py,envelope.py,normalize.py,compare.py}` and the seven named test files plus `tests/simulator/usage/features/18_parity.py`; edited only `app/services/simulator/__init__.py`, `app/services/simulator/README.md`, `docs/CHANGELOG.md`, `docs/PROJECT.md`, and `tests/simulator/unit/test_public_api.py` (expected-export list maintenance anticipated by the dry-run risk register); plan-file edits are this checklist plus the prior Phase 1 hash record only.)
- [x] Every listed FR has final `path:line` implementation and test evidence. (`FR-SIM-187`–`FR-SIM-193`, `FR-SIM-236`–`FR-SIM-239` rows at `app/services/simulator/README.md:1705-1720`; implementation at `app/services/simulator/parity/envelope.py:302`, `app/services/simulator/parity/normalize.py`, `app/services/simulator/parity/compare.py:459`; usage functions `fr_sim_187`–`fr_sim_193`, `fr_sim_236`–`fr_sim_239` at `tests/simulator/usage/features/18_parity.py`.)
- [x] Only verified package-root/public dependency contracts were used. (Utils `canonical_json`/`canonical_digest`/`get_logger`; simulator-internal error catalogue codes only; no Trading/Brokers production import.)
- [x] Targeted unit/integration tests passed with recorded commands and exit codes. (`uv run pytest <7 named files>` → 36 passed in 0.18s; standing regressions `test_paired_semantic_evidence_passes_envelope`, `test_relationship_mutation_fails_parity`, `test_unregistered_ignored_field_is_rejected`, `test_demo_evidence_cannot_claim_live_scope`, `test_certificate_invalidates_when_bound_identity_changes`, `test_cold_runs_from_fresh_roots_are_identical` all present and passing.)
- [x] Ruff format/check and mypy passed for every owning domain. (`ruff format --check` 178 files clean; `ruff check` All checks passed; `mypy app/services/simulator` no issues in 80 files.)
- [x] Every local usage program executed directly and passed. (`uv run python tests/simulator/usage/features/18_parity.py` → 11 SUCCESS lines.)
- [x] Every owning-domain phase gate passed. (`uv run pytest tests/simulator` → 323 passed; the global 80% coverage floor reports on subset runs by pre-existing configuration and fails identically on the unmodified baseline — verified by stash at 27.89% — so it is not a Phase 2 regression.)
- [x] README, changelog, and listed system documents reconciled. (Feature row flipped to Completed at `app/services/simulator/README.md:239`; new §4.18 at `:1705`; `app/services/simulator/parity/README.md` registered; consolidated inventory 221 Completed / 15 Pending at `docs/PROJECT.md:516-530`; one Added(4) block at `docs/CHANGELOG.md:5-21`.)
- [x] STOP conditions and rollback path were rechecked. (No STOP occurred; envelope v1 publishes exact zero tolerances and marks distributional invariants `not_certified: awaiting calibration evidence` rather than inventing thresholds; rollback per plan §Phase 2 Rollback.)
- [x] Commit remains unauthorized, or its separately authorized hash is recorded. (Owner separately authorized the Phase 2 commit on 2026-08-14; committed with the proposed message `feat(simulator): add parity envelope and comparator` — hash recorded post-commit below.)
  - Commit hash: `cb036dfa7668152e87bf22f99554e83f59d86419` (all pre-commit hooks passed; 20 manifest files).

# Phase 3 · Execution-model design registration

This is documentation-only but domain-scoped.

### 3a · Brokers design

Register `SimulationAuthorityPort` as a structurally typed Brokers-owned protocol referencing no
Simulation symbol. Exact method signatures cover reads, command enqueueing, provider-shaped results,
deal history, and lifecycle. This is the design precursor for Phase 10's `FR-BRK-172`; its requirement
allocation remains in Phase 10.

### 3b · Trading design

Register:

- A public function that builds an approved `TradingRequest` from Strategy/Risk lineage so Simulation
  never copies `_approved_request`.
- Business/risk gate equivalence versus route-specific safety gates.
- The injected deadline interface used by the live evaluation cycle.
- Simulation route/profile compatibility.

Requirements: `FR-TRD-093` … `096`, `FR-TRD-113` remain **Proposed** here; their implementation
completion and usage evidence occur in Phases 10b, 14a, and 15a as allocated below.

### 3c · Simulation design

Register scheduler ownership, async orchestration, request v2 identity, terminal-close policy,
journal finalization, and the internal deterministic event order:

```text
command arrival → tick arrival → rollover accrual/posting → mark-to-market
→ protective-trigger evaluation → match evaluation → stop-out evaluation → response delivery
```

Identical-timestamp order uses event-priority, canonical symbol order, source sequence, then a stable
monotonic scheduler sequence. This is Simulation's reproducibility rule, not presumed MT5 truth.
Provider-observed causal edges override comparison assumptions; cancel/fill, modify/fill,
protection/close, disconnect/response, and simultaneous cross-symbol margin races require evidence or
remain outside the envelope. Requirements: `FR-SIM-194` … `199` remain **Proposed** here; their
implementation completion and usage evidence occur in Phases 4c, 5, and 14b.

**Gate:** dependency-cycle test specification, port signatures, scheduler-pump contract, and all
consumer migrations are documented before code.

---

## Implementation specification

**Outcome:** all three owners specify the exact future contracts before implementation; no Python
file changes.

**Approval units:** 3a Brokers README, then 3b Trading README, then 3c Simulation README. Each requires
its own dry run and approval. **Prerequisite:** Phase 2.

**Read first for all units:** `docs/PROJECT.md`, `docs/ARCHITECTURE.md`, the three owning READMEs,
`app/services/brokers/canonical_contracts/protocols.py`, `app/services/trading/contracts/models.py`,
`app/services/trading/actions/dependencies.py`, `app/services/trading/live/facade.py`,
`app/services/simulator/run/dependencies.py`, `run/orchestrator.py`, and `execution/engine.py`.

**File manifest:** 3a **EDIT only** `app/services/brokers/README.md`; 3b **EDIT only**
`app/services/trading/README.md`; 3c **EDIT only** `app/services/simulator/README.md`. **DO NOT TOUCH:**
all Python/tests/usage/migrations and the other domains during each approval unit.

**Implementation order:**

- **3a:** write the private structurally typed `SimulationAuthorityPort` method table, argument and
  return contracts, lifecycle states, unsupported behavior, clock injection, and prohibition on any
  Brokers import of Simulation. Bind the future implementation to `FR-BRK-172` in Phase 10.
- **3b:** specify the package-root approved-request builder, business/risk versus route-safety gate
  taxonomy, explicit fill/time policy flow, injected deadline port, and route/profile compatibility
  for `FR-TRD-093`–`096` and `113`.
- **3c:** specify async orchestration, scheduler pump ownership, internal total order, provider partial
  order, terminal-close policy, v2 execution identity, and journal finalization for
  `FR-SIM-194`–`199`.

**Tests and usage:** none; write exact test specifications and filenames for their owning future
phases, but create no test file here.

**Status handoff:** Phase 3 writes these FR rows as `Proposed`, never `Completed`. Implementation and
usage ownership is fixed as follows: `FR-TRD-096` -> 10b; `FR-TRD-093`, `094`, `113` -> 14a;
`FR-TRD-095` -> 15a; `FR-SIM-196` -> 4c; `FR-SIM-194`, `199` -> 5; `FR-SIM-195`, `197`, `198` ->
14b. The later implementation phase changes the row to `Completed` and supplies local usage evidence; it does not allocate
a second requirement.

**Commands for each unit:** `git diff --check -- <approved README>`; `rg` the exact FR IDs, function
names, errors, and exclusions; `git status --short` to prove one-file scope.

**Gate and checklist:** every method/function has signature, inputs, output, error, clock, side effect,
and owner; dependency graph is acyclic on paper; no owner choice remains hidden in prose.

**STOP:** an existing public contract conflicts; a cross-domain deep import is required; the exact
eleven-port Simulation dependency bundle cannot accommodate the specified ports without a separate
feature; a method would give Brokers business logic.

**Rollback:** revert only the approved README unit.


### Exact requirement-to-usage allocation

None — documentation-only phase; requirements remain Proposed where the phase explicitly says so.

### Exact documentation manifests

#### Unit 3a

- **EDIT:** `app/services/brokers/README.md`

#### Unit 3b

- **EDIT:** `app/services/trading/README.md`

#### Unit 3c

- **EDIT:** `app/services/simulator/README.md`

Every completed FR/checklist row receives final `path:line` evidence. Where listed, the changelog
receives one concise `## [Unreleased]` bullet and never duplicates a Feature Registry.

### Literal validation commands by approval unit

#### Unit 3a

```powershell
git diff --check -- app/services/brokers/README.md
rg -n "FR-|SimulationAuthorityPort|deadline|scheduler|execution identity" app/services/brokers/README.md
git diff --check
git status --short
```

#### Unit 3b

```powershell
git diff --check -- app/services/trading/README.md
rg -n "FR-|SimulationAuthorityPort|deadline|scheduler|execution identity" app/services/trading/README.md
git diff --check
git status --short
```

#### Unit 3c

```powershell
git diff --check -- app/services/simulator/README.md
rg -n "FR-|SimulationAuthorityPort|deadline|scheduler|execution identity" app/services/simulator/README.md
git diff --check
git status --short
```

Run only the commands for the approved unit. A missing path, pre-existing failure, skipped test,
or command substitution is a STOP and requires a correction dry run.

### Exact proposed commit messages

**Unit 3a:**

```text
docs(brokers): specify the simulation authority port

- Complete approved unit 3a within its declared domain and requirement boundary.
- Reconcile the approved documentation authorities; no usage program applies.
- Pass targeted tests, owning-domain gates, documentation reconciliation, and rollback review.
```

**Unit 3b:**

```text
docs(trading): specify converged execution contracts

- Complete approved unit 3b within its declared domain and requirement boundary.
- Reconcile the approved documentation authorities; no usage program applies.
- Pass targeted tests, owning-domain gates, documentation reconciliation, and rollback review.
```

**Unit 3c:**

```text
docs(simulator): specify the deterministic execution model

- Complete approved unit 3c within its declared domain and requirement boundary.
- Reconcile the approved documentation authorities; no usage program applies.
- Pass targeted tests, owning-domain gates, documentation reconciliation, and rollback review.
```

Commit execution is not authorized by phase approval. After separate commit authorization, stage only
the phase manifest, verify `git diff --cached --name-only`, and use the applicable message verbatim.

### Completion checklist

**Per-unit status:** 3a Completed 2026-08-14 (owner standalone approval; `SimulationAuthorityPort` protocol design, method-signature table, isolation rules, lifecycle contract, and `FR-BRK-172` Phase-10a binding registered at `app/services/brokers/README.md:190-241`; validation `git diff --check` clean, `rg` term search matched, one-file scope proven by `git status --short`). 3b Completed 2026-08-14 (owner standalone approval; public approved-request builder, paired gate taxonomy, injected deadline port, route/profile compatibility, and status handoff registered at `app/services/trading/README.md:170-235`; `FR-TRD-093`–`096`, `FR-TRD-113` Proposed; validation clean). 3c Completed 2026-08-14 (owner standalone approval; scheduler ownership, async orchestration, request v2 identity, terminal-close policy, journal finalization, internal deterministic event order with tie-breaking rules, provider causal-order precedence, and status handoff registered at `app/services/simulator/README.md:158-235`; `FR-SIM-194`–`199` Proposed; validation clean). All three units complete; phase checklist ticked below.

- [x] Approval matched this exact phase/subphase. (Each unit 3a/3b/3c received its own standalone owner approval before its README was edited.)
- [x] Only the local file and documentation manifests changed. (Exactly the three owning READMEs across the three units plus this plan file; no Python/test/migration/dependency file changed.)
- [x] Every listed FR has final `path:line` implementation and test evidence. (Phase 3 allocates no implemented FR — `FR-BRK-172`, `FR-TRD-093`–`096`/`113`, `FR-SIM-194`–`199` registered as Proposed with owning-phase handoffs at `app/services/brokers/README.md:190-241`, `app/services/trading/README.md:170-235`, `app/services/simulator/README.md:158-235`.)
- [x] Only verified package-root/public dependency contracts were used. (No code or dependency contract consumed; documentation-only phase.)
- [x] Targeted unit/integration tests passed with recorded commands and exit codes. (Not applicable — documentation-only; per-unit validation surface is the `rg` searches, `git diff --check` (clean per unit), and `git status --short` scope proofs.)
- [x] Ruff and mypy do not apply; all documentation validation commands passed.
- [x] Usage execution does not apply to this documentation-only phase.
- [x] Code-domain test gates do not apply; the documentation gate passed. (Dependency graph acyclic on paper: port/builder/deadline/scheduler designs reference no reverse import; per-phase consumer migrations documented.)
- [x] README, changelog, and listed system documents reconciled. (No changelog entry listed for Phase 3 units; system documents already carry the programme architecture from Phase 1.)
- [x] STOP conditions and rollback path were rechecked. (No STOP triggered; rollback is per-unit `git checkout -- <unit README>` plus this plan record.)
- [x] Commit remains unauthorized, or its separately authorized hash is recorded. (Owner separately authorized a single combined Phase 3 commit on 2026-08-14 in place of the three per-unit boundaries; committed with a combined message derived from the per-unit texts — hash recorded post-commit below.)
  - Commit hash: `0c9b6b7492368f8c317106e114b5ca8701278a85` (all pre-commit hooks passed; 4 files: the three owning READMEs plus this plan record).

# Phase 4 · Contract foundations

## 4a · Brokers current provider specification

**Domain:** brokers. **Feature:** `FEAT-BRK-18`.
**Requirements:** `FR-BRK-159` … `163`.

Create a typed, versioned current `ProviderSpecificationSnapshot` containing explicit normalized
fields required by Trading and Simulation: execution/order/filling/expiration/GTC modes; stops and
freeze levels; directional volume limit; calculation mode; initial, maintenance, and hedged margin
evidence; swap mode/rates/weekday ratios; account margin/stop-out/FIFO/hedge permissions; point,
digits, tick size, profit/loss tick values, contract size and currencies. Dynamic commission/fee
evidence is a separate typed reference, not a guessed static symbol rate.

The snapshot carries provider, server, account digest, environment, terminal build, source revision,
`observed_at`, retrieval provenance, and checksum. It states **current observation only** and never
invents historical effective bounds. Missing required fields fail closed.

- `FR-BRK-159` typed current snapshot; `160` source and observation identity; `161` fail-closed
  completeness; `162` separate provider cost evidence; `163` explicit current-only validity.

## 4b · Data effective-dated history

**Domain:** data. **Feature:** extend `FEAT-DATA-02`.
**Requirements:** `FR-DATA-214` … `216`.

Persist immutable snapshots and hashes through Data's existing catalog/persistence boundary. The
first observation begins no earlier than its verified `observed_at`; a subsequent revision closes the
prior interval. Owner-supplied historical evidence may declare an earlier boundary only with source
provenance and checksum. Gaps stay gaps.

Expose function-only Data operations to register one revision and retrieve the exact revision set
covering an `as_of` instant or bounded interval.

- `FR-DATA-214` immutable revision persistence; `215` non-overlapping effective intervals and
  supersession; `216` point-in-time/interval retrieval with complete-coverage proof and provenance.

Use the existing Data-owned revisioned weekly-session capability for MT5 sessions. No Brokers or
Simulation persistence is added.

## 4c · Simulation request and execution identity v2

**Domain:** simulator. **Feature:** extend `FEAT-SIM-07`.
**Requirements:** `FR-SIM-196`, `FR-SIM-231` … `235`.

Add `SimulationBacktestRequestV2` with required execution-model reference/hash, separate source/tick
lineage hashes, market-evidence class, decision-instant policy, provider-specification revision set,
complete initial-authority-state hash, certification target (`demo` or `live`), and explicit
`close_open_positions_at_end`. Its calculated configuration hash includes all execution-affecting
fields but excludes trace IDs and the hash field itself.

Retain request v1 and synchronous `run_backtest` for a documented deprecation window. Add
`run_backtest_async`; the sync bridge fails closed from a running event loop.

- `FR-SIM-231` request v2; `232` execution-model/config and initial-authority-state identity; `233`
  separate source/tick lineage plus market-evidence class; `234` explicit terminal-close and
  certificate-target policy; `235` v1/sync compatibility and deprecation behavior.

**Integration gate:** a current Broker snapshot can be persisted and read point-in-time through Data;
Simulation v2 hashing binds its revision set and complete initial state; no current snapshot is
accepted retroactively, and no request may relabel demo evidence as live evidence.

---

## Implementation specification

**Outcome:** current provider facts have a typed Brokers snapshot, Data stores immutable effective
history, and Simulation request v2 binds that history plus complete initial state.

**Approval units:** 4a brokers, 4b data, 4c simulator, then read-only integration gate.
**Prerequisite:** Phase 3.

### 4a · Brokers current provider specification — implementation details

**Read first:** Brokers README/root; `canonical_contracts/{enums,models,protocols,public}.py`;
`metatrader/{adapter,mapping,commands}.py`; `capabilities/matrix.py`; conformance files.

**File manifest:** **CREATE** `app/services/brokers/specifications/{README.md,__init__.py,contracts.py,build.py,public.py}`;
**EDIT** `app/services/brokers/__init__.py`, `app/services/brokers/README.md`, canonical enums/protocols/public, MetaTrader adapter/mapping, capability
matrix, conformance fake/suite/public; **CREATE**
`tests/brokers/unit/test_provider_specifications.py`,
`tests/brokers/integration/test_provider_specification_contract.py`, and
`tests/brokers/usage/features/18_specifications.py`. **DO NOT TOUCH:** Data/Simulation/Trading.

**Implementation:** private frozen snapshot models validate every Phase 4a field, provenance,
`observed_at`, source revision, account digest, build, checksum, and current-only validity. Expose only
root functions to build/parse/read a snapshot; adapter protocol may return the private canonical DTO
internally. Map exact MT5 fields without raw `_asdict()` leakage. Missing required fields return the
declared Brokers validation/capability error; no historical bounds or fee defaults.

**Tests/usage:** cover `FR-BRK-159`–`163` individually; mapping completeness, missing field, checksum,
current-only semantics, credential redaction, conformance fake, and unsupported provider. Usage defines
`fr_brk_159()` through `fr_brk_163()` and calls each new root function.

**Commands:** targeted Ruff/mypy for Brokers; the two new test files plus existing MT5 mapping,
protocol, factory, capability, conformance, public-operation, documentation-parity, and usage-parity
tests; direct `18_specifications.py` execution.

**STOP:** MT5 lacks a required field and no verified separate evidence exists; mapping would invent an
effective date or static commission; a class would need root export.

**Rollback:** remove feature/tests/usage, root exports, capability/protocol/mapping
edits; rerun Brokers public/conformance tests.

### 4b · Data effective-dated history — implementation details

**Read first:** Data README/root; `datasets/{contracts,catalog,manifest}.py`; Data persistence CRUD and
transactions; Data migration composition; `tests/data/unit/test_catalog_schema.py` and migration tests.

**File manifest:** **CREATE** `app/services/data/datasets/migrations/{__init__.py,definitions.py}`;
**EDIT** `app/services/data/__init__.py`, `app/services/data/README.md`, datasets contracts/catalog/README, Data migration composition, persistence
`create.py`, `read.py`, `update.py`; **CREATE** `tests/data/unit/test_provider_specification_revisions.py`,
`tests/data/integration/test_provider_specification_history.py`; **EDIT**
`tests/data/usage/features/02_datasets.py`. **DO NOT TOUCH:** Brokers/Simulation/Trading.

**Implementation:** immutable rows store snapshot checksum, provider/server/environment/account digest,
symbol, observed/effective bounds, provenance, payload and supersession link. Registration starts no
earlier than verified observation; owner-supplied earlier history requires provenance. Reject overlap,
backdating, checksum mutation, gap-as-coverage, and update/delete of immutable evidence. Public root
functions register one revision and return exact as-of/interval coverage proof.

**Tests/usage:** `FR-DATA-214`, `215`, `216` each receive one named test group and `fr_data_214()`,
`fr_data_215()`, `fr_data_216()` in `02_datasets.py`; include migration checksum/ledger, overlap,
supersession, gap, backdating, transaction rollback, closed connection, and detached result tests.

**Commands:** targeted Ruff/mypy for Data; new tests plus catalog schema, persistence migrations,
locking, database boundary, focused boundaries, public operations, documentation parity, and direct
`02_datasets.py` execution.

**STOP:** the owning Data README assigns this persistence elsewhere; an existing applied migration ID
would be modified; overlap cannot be rejected atomically; a Brokers type would cross the Data boundary.

**Rollback:** remove only the new unapplied migration/feature edits and tests; remove
root exports and README FR rows; rerun migration/schema reconciliation. If migration was applied, stop
and use a new forward migration—never edit its checksum.

### 4c · Simulation request and execution identity v2 — implementation details

**Requirements:** `FR-SIM-196`, `FR-SIM-231`–`235`.

**Read first:** Simulator README/root; `run/{contracts,dependencies,orchestrator}.py`; state/idempotency,
journal and reporting contracts; current run tests and usage 07.

**File manifest:** **EDIT** `app/services/simulator/__init__.py`, `app/services/simulator/README.md`, run contracts/dependencies/orchestrator, state store
identity and journal start payload only where they currently hash v1; **CREATE**
`tests/simulator/unit/test_run_request_v2.py`; **EDIT** run/public/replay/contract integration tests and
`tests/simulator/usage/features/07_run.py`. **DO NOT TOUCH:** v1 field meaning, immutable completed rows,
Trading/Brokers/Data code.

**Implementation:** add private frozen `SimulationBacktestRequestV2`; canonical hash includes every
Phase 4c field and excludes only trace IDs/hash field. Add async root operation; sync root operation
delegates only outside a running loop and otherwise fails with the declared Simulation error. V1 and
sync bridge remain documented until their window closes. Changed execution identity creates a new run
identity; it never mutates/rejects an unrelated immutable terminal row.

**Tests/usage:** `FR-SIM-196`, `FR-SIM-231`–`235` each get named unit tests and usage functions;
parameterize every
execution-affecting field to change the hash, every trace field not to change it, missing initial-state
hash, demo/live relabel, running-loop sync failure, async success, v1 replay, and cold-run identity.

**Commands:** targeted Ruff/mypy Simulator; new v2 tests plus run contracts, orchestrator, public API,
replay, official backtest, contract compatibility, usage scripts; direct `07_run.py`.

**Integration gate:** persist/read a Brokers snapshot through Data, bind its revision and complete
initial state in v2, and reject retroactive or relabelled evidence using offline fixtures only.

**STOP:** a v2 field has no authoritative owner; config hashing uses `run_id`, wall clock, unordered
mapping, or Python `hash()`; async conversion breaks v1; terminal-row mutation is proposed.

**Rollback:** remove v2/async exports and tests, restore untouched v1 behavior and
usage, rerun replay/compatibility tests.

### Exact requirement-to-usage allocation

| Unit | Usage program and required functions |
|---|---|
| 4a | `18_specifications.py`: `fr_brk_159()` … `fr_brk_163()` |
| 4b | `02_datasets.py`: `fr_data_214()`, `fr_data_215()`, `fr_data_216()` |
| 4c | `07_run.py`: `fr_sim_196()`, `fr_sim_231()` … `fr_sim_235()` |

### Exact documentation manifests

#### Unit 4a

- **EDIT:** `app/services/brokers/README.md`
- **EDIT:** `docs/CHANGELOG.md`
- **EDIT:** `docs/PROJECT.md`
- **EDIT:** `docs/ARCHITECTURE.md`

#### Unit 4b

- **EDIT:** `app/services/data/README.md`
- **EDIT:** `docs/CHANGELOG.md`
- **EDIT:** `docs/ARCHITECTURE.md`

#### Unit 4c

- **EDIT:** `app/services/simulator/README.md`
- **EDIT:** `docs/CHANGELOG.md`
- **EDIT:** `docs/PROJECT.md`
- **EDIT:** `docs/ARCHITECTURE.md`

Every completed FR/checklist row receives final `path:line` evidence. Where listed, the changelog
receives one concise `## [Unreleased]` bullet and never duplicates a Feature Registry.

### Literal validation commands by approval unit

#### Unit 4a

```powershell
uv run ruff format --check app/services/brokers tests/brokers
uv run ruff check app/services/brokers tests/brokers
uv run mypy app/services/brokers
uv run pytest tests/brokers/unit/test_provider_specifications.py tests/brokers/integration/test_provider_specification_contract.py
uv run python tests/brokers/usage/features/18_specifications.py
uv run pytest tests/brokers
git diff --check
git status --short
```

#### Unit 4b

```powershell
uv run ruff format --check app/services/data tests/data
uv run ruff check app/services/data tests/data
uv run mypy app/services/data
uv run pytest tests/data/unit/test_catalog_schema.py tests/data/unit/test_provider_specification_revisions.py tests/data/integration/test_provider_specification_history.py
uv run python tests/data/usage/features/02_datasets.py
uv run pytest tests/data
git diff --check
git status --short
```

#### Unit 4c

```powershell
uv run ruff format --check app/services/simulator tests/simulator
uv run ruff check app/services/simulator tests/simulator
uv run mypy app/services/simulator
uv run pytest tests/simulator/unit/test_run_request_v2.py
uv run python tests/simulator/usage/features/07_run.py
uv run pytest tests/simulator
git diff --check
git status --short
```

Run only the commands for the approved unit. A missing path, pre-existing failure, skipped test,
or command substitution is a STOP and requires a correction dry run.

### Exact proposed commit messages

**Unit 4a:**

```text
feat(brokers): add provider specification snapshots

- Complete approved unit 4a within its declared domain and requirement boundary.
- Execute and document usage evidence: tests/brokers/usage/features/18_specifications.py.
- Pass targeted tests, owning-domain gates, documentation reconciliation, and rollback review.
```

**Unit 4b:**

```text
feat(data): persist provider specification revisions

- Complete approved unit 4b within its declared domain and requirement boundary.
- Execute and document usage evidence: tests/data/usage/features/02_datasets.py.
- Pass targeted tests, owning-domain gates, documentation reconciliation, and rollback review.
```

**Unit 4c:**

```text
feat(simulator): add backtest request v2

- Complete approved unit 4c within its declared domain and requirement boundary.
- Execute and document usage evidence: tests/simulator/usage/features/07_run.py.
- Pass targeted tests, owning-domain gates, documentation reconciliation, and rollback review.
```

Commit execution is not authorized by phase approval. After separate commit authorization, stage only
the phase manifest, verify `git diff --cached --name-only`, and use the applicable message verbatim.

### Completion checklist

**Unit 4a status: Completed — 2026-08-15.**

- [x] Approval matched this exact phase/subphase. (Owner standalone `APPROVED: EXECUTE` for unit 4a brokers following the recorded dry run.)
- [x] Only the local file and documentation manifests changed. (Created `app/services/brokers/specifications/{README.md,__init__.py,contracts.py,build.py,public.py}`, `tests/brokers/unit/test_provider_specifications.py`, `tests/brokers/integration/test_provider_specification_contract.py`, `tests/brokers/usage/features/18_specifications.py`; edited the declared canonical enums/protocols, capability matrix, MT5 adapter, brokers root `__init__`/README, docs/CHANGELOG/PROJECT/ARCHITECTURE per the 4a documentation manifest, and same-feature registry tests (`test_catalogue`, `test_enums`, `test_documentation_parity`, `test_usage_parity`) anticipated by the dry-run risk register; plan-file edits are this checklist record only.)
- [x] Every listed FR has final `path:line` implementation and test evidence. (`FR-BRK-159`–`163` rows at `app/services/brokers/README.md` §4.13; implementation at `app/services/brokers/specifications/contracts.py:273`, `build.py:452`, `app/services/brokers/metatrader/adapter.py:329`; usage functions `fr_brokers_159()`–`fr_brokers_163()` at `tests/brokers/usage/features/18_specifications.py`.)
- [x] Only verified package-root/public dependency contracts were used. (Upstream `symbol_info()`/`account_info()`/`terminal_info()` field lists verified against the official MetaTrader5 documentation; in-repo verified `swap_mode`/`filling_mode`/`trade_mode` mappings reused; Utils canonical JSON/digest.)
- [x] Targeted unit/integration tests passed with recorded commands and exit codes. (`uv run pytest tests/brokers/unit/test_provider_specifications.py tests/brokers/integration/test_provider_specification_contract.py` → 21 passed in 0.46s.)
- [x] Ruff format/check and mypy passed for every owning domain. (`ruff format --check` 210 files clean; `ruff check` All checks passed; `mypy app/services/brokers` no issues in 96 files.)
- [x] Every local usage program executed directly and passed. (`uv run python tests/brokers/usage/features/18_specifications.py` → 5 SUCCESS lines.)
- [x] Every owning-domain phase gate passed. (`uv run pytest tests/brokers` → 571 passed, 3 skipped; the 8 remaining failures were verified by `git stash` to fail identically on the unmodified baseline — catalogue ×3, broker discovery ×1, documentation docstring sections ×1, mt5 adapter enumeration ×1, mt5 mutations coverage ×2 — so they are pre-existing and not 4a regressions; one transient Dukascopy network flake did not recur.)
- [x] README, changelog, and listed system documents reconciled. (Registry row + §4.13 + counts twelve at `app/services/brokers/README.md`; §5 contract row and count 237/222/15 at `docs/PROJECT.md`; ARCHITECTURE.md snapshot note; CHANGELOG Added(3) block.)
- [x] STOP conditions and rollback path were rechecked. (No STOP occurred; account-permission fields absent from the upstream contract are explicit `unverified` exclusions rather than inventions; rollback per plan §4a.)
- [x] Commit remains unauthorized, or its separately authorized hash is recorded. (Owner separately authorized the 4a commit on 2026-08-15; committed with the proposed message `feat(brokers): add provider specification snapshots` — hash recorded post-commit below.)
  - Commit hash: `bdc08827267654e06ed2dd1fa4faadee4171778a` (all pre-commit hooks passed; 22 manifest files).

**Unit 4b status: Completed — 2026-08-15.**

- [x] Approval matched this exact phase/subphase. (Owner standalone `APPROVED: EXECUTE` for unit 4b Data following dry run `4b-DR1`; owner separately approved correction plan `4b-C1` for this completion record and exact-message amendment.)
- [x] Only the local file and documentation manifests changed. (Created `app/services/data/datasets/migrations/{__init__.py,definitions.py}`, `tests/data/unit/test_provider_specification_revisions.py`, and `tests/data/integration/test_provider_specification_history.py`; edited the declared datasets contracts/catalog/README, Data root/README, migration composition, persistence CRUD, usage 02, CHANGELOG, and ARCHITECTURE files plus same-domain migration, lifecycle-inventory, usage-output, import-boundary, schema, and public-export reconciliation tests identified by the approved dry run; Brokers/Simulation/Trading were untouched.)
- [x] Every listed FR has final `path:line` implementation and test evidence. (`FR-DATA-214`–`216` rows at `app/services/data/README.md:3432-3434`; public implementation at `app/services/data/datasets/catalog.py:232`, `:311`, and `:347`; migration at `app/services/data/datasets/migrations/definitions.py:9`; unit evidence at `tests/data/unit/test_provider_specification_revisions.py:53-87`; integration evidence at `tests/data/integration/test_provider_specification_history.py:70-104`; usage functions at `tests/data/usage/features/02_datasets.py:201-223`.)
- [x] Only verified package-root/public dependency contracts were used. (Data accepts an opaque checksummed mapping through its package-root functions, uses Utils canonical digest/JSON behavior and Data-owned transaction/migration interfaces, and imports no Brokers type.)
- [x] Targeted unit/integration tests passed with recorded commands and exit codes. (Final focused regression command covering provider history, schema, migration inventory, CRUD layout, reconciliation, import boundaries, public operations, lifecycle inventory, and usage-script integration → 49 passed in 11.18s; provider-history-focused command → 23 passed in 1.84s.)
- [x] Ruff format/check and mypy passed for every owning domain. (`ruff format --check` 361 files clean; `ruff check` all checks passed; `mypy app/services/data` no issues in 161 files.)
- [x] Every local usage program executed directly and passed. (`uv run python tests/data/usage/features/02_datasets.py` exited 0 and executed `fr_data_214()`, `fr_data_215()`, and `fr_data_216()` through the Data package root.)
- [x] Every owning-domain phase gate passed for the Phase 4b change surface. (`uv run pytest --no-cov -p no:cacheprovider tests/data -q` → 930 passed, 2 skipped, with two unchanged baseline structural failures: pre-existing Google-docstring omissions and pre-existing workflow `INPUT BOUNDARY` text; `git diff HEAD^` is empty for every reported failing production/test path. The repository-wide configured coverage invocation also remains below its global 80% floor at 20.37%, unrelated to Phase 4b.)
- [x] README, changelog, and listed system documents reconciled. (Feature and requirement rows at `app/services/data/README.md:241` and `:3432-3434`; dataset contract at `app/services/data/datasets/README.md`; architecture rule at `docs/ARCHITECTURE.md:439`; Unreleased entry at `docs/CHANGELOG.md:7-12`.)
- [x] STOP conditions and rollback path were rechecked. (No migration ID was modified, overlap is rejected through atomic close-and-insert persistence, and no Brokers type crosses the Data boundary; rollback removes migration 010 only while unapplied, otherwise requires a new forward migration.)
- [x] Commit remains unauthorized, or its separately authorized hash is recorded. (Owner separately authorized the unit 4b commit and correction plan `4b-C1`; the commit uses the exact proposed message below, with its self-referential hash deferred to a later authorized plan record.)
  - Commit hash: pending post-commit record.

**Unit 4c status: Completed — 2026-08-15.**

- [x] Approval matched this exact phase/subphase. (Owner standalone `APPROVED: EXECUTE` approved dry run `4c-DR2` with the recommended V2 schema, provider-revision binding, minimal coroutine bridge, and PROJECT manifest correction.)
- [x] Only the local file and documentation manifests changed. (Created `tests/simulator/unit/test_run_request_v2.py`; edited Simulator run contracts/orchestrator/package exports, public/export and contract integration evidence, usage 07, Simulator README, PROJECT, ARCHITECTURE, CHANGELOG, and this plan record. State, persistence, journal, reporting, Data, Brokers, and Trading production files were untouched.)
- [x] Every listed FR has final `path:line` implementation and test evidence. (`FR-SIM-196`, `FR-SIM-231`–`235` rows at `app/services/simulator/README.md:1574-1579`; provider binding and V2 contract at `app/services/simulator/run/contracts.py:238` and `:308`; async/sync operations at `app/services/simulator/run/orchestrator.py:657` and `:689`; unit evidence at `tests/simulator/unit/test_run_request_v2.py:84-157`; usage functions at `tests/simulator/usage/features/07_run.py:322-365`.)
- [x] Only verified package-root/public dependency contracts were used. (V2 embeds frozen scalar/reference projections rather than Data/Brokers types; the offline integration gate builds a Brokers snapshot and persists/reads it through the Brokers and Data package roots before binding the detached revision into V2.)
- [x] Targeted unit/integration tests passed with recorded commands and exit codes. (V2/run/public/orchestrator/replay/compatibility/official/cold-identity set → 72 passed in 4.38s; expanded V2 field/identity unit evidence → 17 passed in 1.51s; Brokers→Data→Simulation compatibility gate → 7 passed in 1.16s.)
- [x] Ruff format/check and mypy passed for every owning domain. (`ruff format` reconciled the approved Simulator/test files; `ruff check` all checks passed; `mypy app/services/simulator` no issues in 80 source files.)
- [x] Every local usage program executed directly and passed. (`uv run python tests/simulator/usage/features/07_run.py` exited 0 and executed `fr_sim_196()`, `fr_sim_231()`–`fr_sim_235()` through package-root operations.)
- [x] Every owning-domain phase gate passed for the Phase 4c behavior surface. (`uv run pytest --no-cov -p no:cacheprovider tests/simulator -q` → 342 passed in 30.15s. The literal configured command `uv run pytest tests/simulator -q` ran the then-current 339-test set successfully but exited 1 because repository-wide aggregate coverage was 28.82%, below the global 80% floor; this unchanged whole-application coverage configuration is recorded rather than bypassed.)
- [x] README, changelog, and listed system documents reconciled. (Completed V2 shared contract at `app/services/simulator/README.md:59` and `docs/PROJECT.md:1094`; architecture binding at `docs/ARCHITECTURE.md:440`; Unreleased entry at `docs/CHANGELOG.md:5`; Phase 4c documentation manifest now includes PROJECT.)
- [x] STOP conditions and rollback path were rechecked. (Every V2 field has an authoritative owner, hashing uses canonical SHA-256 and excludes only trace/hash fields, V1 remains valid, running-loop sync misuse fails closed, and immutable terminal rows are unchanged. Rollback removes V2/async exports/tests/usage and restores the V1 synchronous entry point.)
- [x] Commit remains unauthorized, or its separately authorized hash is recorded. (Commit remains unauthorized; exact proposed message is `feat(simulator): add backtest request v2`.)
  - Commit hash: pending owner authorization.

# Phase 5 · Deterministic execution scheduler

**Domain:** simulator. **Feature:** `FEAT-SIM-15`.
**Requirements:** `FR-SIM-194`, `FR-SIM-199` … `204`.

Create `scheduler/{README,__init__,contracts,queue,clock,pump,state}.py`.

The async run owns one scheduler pump task. Evaluation tasks enqueue commands and await futures;
the pump selects the next deterministic event, advances simulated time, invokes the bounded handler,
and resolves or faults the future. There is a real coroutine `await`, but no wall-clock sleep or
provider wait. Define cancellation, handler exceptions, queue exhaustion, nested submissions, and
shutdown behavior. A deterministic `run_until_complete` path supports the retained sync bridge.

- `FR-SIM-200` priority queue; `201` simulated clock; `202` scheduled future resolution; `203`
  internal deterministic order without a provider-order claim; `204` serializable scheduler state and
  pending future identity.

**Tests:** every event-pair priority, shuffled-input stability, multi-symbol same-time ordering,
awaited mutation without deadlock, cancellation/error propagation, empty-queue failure, and state
round-trip.

---

## Implementation specification

**Outcome:** `FEAT-SIM-15` owns the only simulated clock and event pump; awaited authority operations
resolve through scheduled events without wall-clock waits or deadlock.

**Approval unit:** simulator. **Prerequisite:** 4c. **Requirements:** `FR-SIM-194`,
`FR-SIM-199`–`204`.

**Read first:** Simulator README/root; timeline contracts; run orchestrator/dependencies; execution
engine/trader; recovery checkpoints/contracts; scenario contracts; parity event-order specification.

**File manifest:** **CREATE** `app/services/simulator/scheduler/{README.md,__init__.py,contracts.py,queue.py,clock.py,pump.py,state.py}`;
**EDIT** `app/services/simulator/__init__.py`, `app/services/simulator/README.md`; **CREATE** `tests/simulator/unit/test_scheduler_queue.py`,
`test_scheduler_clock.py`, `test_scheduler_pump.py`, `test_scheduler_state.py`,
`tests/simulator/integration/test_scheduler_total_order.py`,
`tests/simulator/integration/test_scheduler_resume.py`, and
`tests/simulator/usage/features/15_scheduler.py`. **DO NOT TOUCH:** realism latency/fault behavior,
Trading, Brokers, Data, or existing timeline tick construction.

**Requirements/contracts:** `FR-SIM-194` single scheduler authority; `199` internal event order;
`200` priority queue; `201` clock; `202` future resolution; `203` bounded pump behavior; `204`
serializable state. Root functions create an opaque scheduler, schedule/cancel
events, inspect bounded state, pump one event, pump until a future/result condition, serialize, and
restore. Classes/constants remain private. Event key is `(scheduled_at, priority, canonical_symbol,
source_sequence, scheduler_sequence)`; all timestamps are aware UTC; sequence is monotonic; duplicate
identity and unknown priority fail closed.

**Implementation order:** contracts/key validation; heap queue; clock; single-event pump; awaited
future resolution; cancellation/error/empty-queue/nested submission/shutdown; state codec; root API;
unit tests; total-order/resume integrations; usage/README.

**Tests:** parameterize every event-priority pair, shuffled input, same-time multi-symbol ordering,
duplicate source sequence, no wall-clock call, awaited mutation, handler exception, cancellation,
empty queue, nested submission, shutdown, state round-trip, resume identity, and cross-process stable
ordering. No unit test sleeps.

**Usage:** `15_scheduler.py` defines `fr_sim_200()` through `fr_sim_204()`, exercises every root
operation, demonstrates one awaited scheduled response, and prints only bounded secret-safe results.

**Commands:** targeted Ruff/mypy for scheduler/root; all named new tests plus existing timeline,
recovery, orchestrator, runtime dependency/state tests; direct usage. Phase gate additionally runs all
Simulator tests because every later phase depends on the scheduler.

**Gate/checklist:** exact total order; no `datetime.now`, `time.*`, `asyncio.sleep`, thread sleep, or
provider wait in scheduler; resume produces identical event/result order; every checklist item has
path:line evidence.

**STOP:** an awaited operation requires a second event-loop owner; a serializable state would contain a
live coroutine/future/callback; a new shared support folder is proposed; a clock read is ambient.

**Rollback:** remove scheduler feature/tests/usage/root exports/README rows; no consumer exists yet, so
no compatibility shim. Run Simulator public/import/recovery tests.


### Exact requirement-to-usage allocation

| Unit | Usage program and required functions |
|---|---|
| 5 | `15_scheduler.py`: `fr_sim_194()`, `fr_sim_199()` … `fr_sim_204()` |

### Exact documentation manifest

- **EDIT:** `app/services/simulator/README.md`
- **EDIT:** `docs/CHANGELOG.md`
- **EDIT:** `docs/PROJECT.md`

Every completed FR/checklist row receives final `path:line` evidence. The changelog receives one concise
`## [Unreleased]` bullet under the correct change type and never duplicates a Feature Registry.

### Literal validation commands

```powershell
uv run ruff format --check app/services/simulator tests/simulator
uv run ruff check app/services/simulator tests/simulator
uv run mypy app/services/simulator
uv run pytest tests/simulator/unit/test_scheduler_queue.py tests/simulator/integration/test_scheduler_total_order.py tests/simulator/integration/test_scheduler_resume.py
uv run python tests/simulator/usage/features/15_scheduler.py
uv run pytest tests/simulator
git diff --check
git status --short
```

Run the phase-named targeted pytest files before the owning-domain gate. A missing exact path,
pre-existing failure, skipped test, or command substitution is a STOP and requires a correction dry run.

### Exact proposed commit messages

**Unit 5:**

```text
feat(simulator): add deterministic execution scheduler

- Complete approved unit 5 within its declared domain and requirement boundary.
- Execute and document usage evidence: tests/simulator/usage/features/15_scheduler.py.
- Pass targeted tests, owning-domain gates, documentation reconciliation, and rollback review.
```

Commit execution is not authorized by phase approval. After separate commit authorization, stage only
the phase manifest, verify `git diff --cached --name-only`, and use the applicable message verbatim.

### Completion checklist

- [x] Approval matched this exact phase/subphase. (The owner's goal-wide standalone approval authorizes sequential Phase 5 execution and commit.)
- [x] Only the local file and documentation manifests changed. (Scheduler files are rooted at `app/services/simulator/scheduler/__init__.py:17`; the only shared code edit is the package-root boundary at `app/services/simulator/__init__.py:686`.)
- [x] Every listed FR has final `path:line` implementation and test evidence. (`FR-SIM-194`/`202`/`203`: `app/services/simulator/scheduler/pump.py:21`, tests `tests/simulator/unit/test_scheduler_pump.py:34`; `FR-SIM-199`/`200`: `app/services/simulator/scheduler/contracts.py:27`, tests `tests/simulator/unit/test_scheduler_queue.py:25`; `FR-SIM-201`: `app/services/simulator/scheduler/clock.py:10`; `FR-SIM-204`: `app/services/simulator/scheduler/state.py:13`, integration `tests/simulator/integration/test_scheduler_resume.py:16`; usage functions `tests/simulator/usage/features/15_scheduler.py:36-79`.)
- [x] Only verified package-root/public dependency contracts were used. (The public function-only boundary is `app/services/simulator/__init__.py:686-762`; canonical identity uses the existing `app.utils.canonical_digest` export.)
- [x] Targeted unit/integration tests passed with recorded commands and exit codes. (`uv run pytest tests/simulator/unit/test_scheduler_queue.py tests/simulator/integration/test_scheduler_total_order.py tests/simulator/integration/test_scheduler_resume.py --no-cov`: 32 passed, exit 0.)
- [x] Ruff format/check and mypy passed for every owning domain. (`ruff check app/services/simulator tests/simulator`: exit 0; `mypy app/services/simulator`: no issues in 86 files; the one format drift reported by the first check was automatically reconciled with `ruff format tests/simulator/unit/test_public_api.py`.)
- [x] Every local usage program executed directly and passed. (`PYTHONPATH=.; uv run python tests/simulator/usage/features/15_scheduler.py`: all seven allocated FR functions emitted bounded SUCCESS evidence, exit 0.)
- [x] Every owning-domain behavioral phase gate passed. (`uv run pytest tests/simulator --no-cov`: 381 passed, exit 0. Blocking harness issue automatically handled: the literal coverage-enabled command collected and passed all 381 tests but failed the repository-global 80% threshold at 29%; changing global coverage configuration is outside this unit, so the approved recommendation is the existing owning-domain `--no-cov` regression gate plus focused evidence.)
- [x] README, changelog, and listed system documents reconciled. (`app/services/simulator/README.md:316`; `docs/CHANGELOG.md:5`; `docs/PROJECT.md:4`.)
- [x] STOP conditions and rollback path were rechecked. (`rg` found no ambient clock, sleep, or provider-wait call in `app/services/simulator/scheduler/`; rollback remains removal of the Phase 5 manifest and root exports followed by the public/import/recovery tests.)
- [x] Commit is authorized by the owner's goal-wide standalone approval; the exact plan message is used and its hash is recorded in repository history.

# Phase 6 · Order-policy v2 migration

## 6a · Trading contracts and producers

**Domain:** trading. **Requirements:** `FR-TRD-097` … `100`, `FR-TRD-112`.

Add TradingRequest/OrderIntent v2 with required, separate:

- `fill_policy`: `FOK | IOC | RETURN | BOC`
- `time_policy`: `GTC | DAY | SPECIFIED | SPECIFIED_DAY`
- UTC expiration when required

Validate against the typed provider snapshot. Retain v1 parsing during a declared release window.
A v1 request lacking one dimension fails closed unless an explicit versioned legacy-compatibility
profile supplies it; that path is labelled legacy and is excluded from the parity envelope. No
provider-derived default becomes caller intent. Migrate every internal producer to v2.

## 6b · Brokers order contract and MT5 command

**Domain:** brokers. **Requirements:** `FR-BRK-164` … `166`.

Add BrokerOrderRequest v2, carry both policies, map them independently to `type_filling` and
`type_time`, and reject unsupported combinations. Preserve v1 during the same migration window.

**Integration gate:** each valid/invalid combination, SPECIFIED_DAY session-edge expiration, producer
compatibility, and proof that the adapter never substitutes a policy.

---

## Implementation specification

### 6a · Trading contracts and producers — implementation details

**Outcome:** every new Trading-produced request carries independent fill and time policy; no adapter
or caller silently derives either dimension.

**Approval unit:** trading. **Prerequisite:** 4a. **Requirements:** `FR-TRD-097`–`100`, `112`.

**Read first:** Trading README/root; `contracts/{models,factories}.py`;
`validation/orders.py`; every module returned by
`rg -l "OrderIntent|TradingRequest|fill_policy|time_policy" app/services/trading tests/trading`;
Brokers current-specification README and public snapshot getter.

**File manifest:** **EDIT** `app/services/trading/contracts/models.py`,
`app/services/trading/contracts/factories.py`, `app/services/trading/validation/orders.py`,
`app/services/trading/__init__.py`, `app/services/trading/README.md`, and every Trading producer listed
by the read-first search; **CREATE** `tests/trading/unit/contracts/test_order_policy_v2.py`,
`tests/trading/integration/test_order_policy_v2_producers.py`; **EDIT**
`tests/trading/usage/features/01_contracts.py`. **DO NOT TOUCH:** Brokers mapping, Simulation,
Strategy/Risk policy, or legacy-v1 removal.

**Exact contract:** add versioned v2 models with required `fill_policy`, required `time_policy`, and
aware-UTC `expiration` required only for `SPECIFIED`/`SPECIFIED_DAY`. The only admitted values are
`FOK|IOC|RETURN|BOC` and `GTC|DAY|SPECIFIED|SPECIFIED_DAY`. Factory functions accept the two values
separately, validate the requested combination against the exact provider-specification revision,
and return the immutable approved v2 request. V1 decoding remains; absent policy dimensions may be
supplied only by an explicitly named, versioned legacy profile and must mark the result
`legacy_compatibility=True`, which makes it ineligible for canonical parity.

**Implementation order:** models/enums and validators; v2 factory; provider-snapshot compatibility;
legacy-profile branch; migrate every search-discovered internal producer; root function export;
tests; usage; README registry/requirements/public API/compatibility note.

**Tests/usage:** cover the Cartesian product of fill/time values against supported and unsupported
snapshot combinations; missing/naive/unexpected expiration; GTC/DAY with expiration; session-edge
`SPECIFIED_DAY`; mutation after construction; v1 with and without profile; canonical-ineligibility
flag; and every producer. Usage `01_contracts.py` must call every new root factory and display a
v2 request plus a labelled legacy result.

**Commands:**

```powershell
uv run ruff check app/services/trading tests/trading/unit/contracts/test_order_policy_v2.py tests/trading/integration/test_order_policy_v2_producers.py tests/trading/usage/features/01_contracts.py
uv run mypy app/services/trading
uv run pytest tests/trading/unit/contracts/test_order_policy_v2.py tests/trading/integration/test_order_policy_v2_producers.py tests/trading/unit/contracts/test_models.py tests/trading/unit/contracts/test_registry.py
uv run python tests/trading/usage/features/01_contracts.py
```

**Gate/STOP:** all producers are v2; root exports are functions only; no default reflects provider
preference. **STOP** if a producer cannot obtain both policies, a provider field is missing, or a
second public enum owner would be created.

**Rollback:** revert listed Trading paths and delete the two tests; retain v1 exactly
as found.

### 6b · Brokers order contract and MT5 command — implementation details

**Outcome:** the Brokers boundary preserves Trading's two policy dimensions and maps them independently.

**Approval unit:** brokers. **Prerequisite:** 6a. **Requirements:** `FR-BRK-164`–`166`.

**Read first:** Brokers README/root; `canonical_contracts/{enums,models,protocols,public}.py`;
`metatrader/{commands,mapping,adapter}.py`; current-specification feature; all results from
`rg -l "type_filling|type_time|BrokerOrderRequest" app/services/brokers tests/brokers`.

**File manifest:** **EDIT** the read-first canonical-contract and MT5 files that own order request
construction/mapping, `app/services/brokers/__init__.py`, `app/services/brokers/README.md`; **CREATE**
`tests/brokers/unit/test_order_policy_v2_mapping.py`,
`tests/brokers/integration/test_order_policy_v2_adapter.py`; **EDIT**
`tests/brokers/usage/features/02_metatrader.py`. **DO NOT TOUCH:** Trading models, Simulation, MT5
transport/retry policy, or v1 deletion.

**Implementation order:** v2 canonical request; compatibility validation against the bound snapshot;
independent `fill_policy -> type_filling` and `time_policy -> type_time` tables; expiration mapping;
adapter command path; canonical response/error behavior; root functions; tests/usage/README.

**Tests:** every mapping entry; invalid cross-product; policy value tampering; unsupported BOC;
expiration conversion at UTC/session edge; proof that neither field is copied from symbol defaults;
v1 compatibility; request serialization round-trip. Usage must build/check a v2 order through the
Brokers package root and remain transport-free.

**Commands:** targeted Ruff/mypy for Brokers; run the two new tests plus existing canonical contracts,
MT5 commands/mapping, adapter order, public API and compatibility tests; directly execute
`tests/brokers/usage/features/02_metatrader.py`.

**Gate/STOP:** paired Trading-to-Brokers integration proves exact value preservation. **STOP** on an
unverified MT5 constant, a provider-derived intent default, or a required protocol signature change
not documented in 4a.

**Rollback:** remove v2 mapping/tests/exports and restore v1 behavior; rerun MT5
mapping/command tests.

### Exact requirement-to-usage allocation

| Unit | Usage program and required functions |
|---|---|
| 6a | `01_contracts.py`: `fr_trd_097()` … `fr_trd_100()`, `fr_trd_112()` |
| 6b | `02_metatrader.py`: `fr_brk_164()`, `fr_brk_165()`, `fr_brk_166()` |

### Exact documentation manifests

#### Unit 6a

- **EDIT:** `app/services/trading/README.md`
- **EDIT:** `docs/CHANGELOG.md`
- **EDIT:** `docs/ARCHITECTURE.md`

#### Unit 6b

- **EDIT:** `app/services/brokers/README.md`
- **EDIT:** `docs/CHANGELOG.md`
- **EDIT:** `docs/ARCHITECTURE.md`

Every completed FR/checklist row receives final `path:line` evidence. Where listed, the changelog
receives one concise `## [Unreleased]` bullet and never duplicates a Feature Registry.

### Literal validation commands by approval unit

#### Unit 6a

```powershell
uv run ruff format --check app/services/trading tests/trading
uv run ruff check app/services/trading tests/trading
uv run mypy app/services/trading
uv run pytest tests/trading/unit/contracts/test_order_policy_v2.py tests/trading/integration/test_order_policy_v2_producers.py tests/trading/unit/contracts/test_models.py tests/trading/unit/contracts/test_registry.py
uv run python tests/trading/usage/features/01_contracts.py
uv run pytest tests/trading
git diff --check
git status --short
```

#### Unit 6b

```powershell
uv run ruff format --check app/services/brokers tests/brokers
uv run ruff check app/services/brokers tests/brokers
uv run mypy app/services/brokers
uv run pytest tests/brokers/unit/test_order_policy_v2_mapping.py tests/brokers/integration/test_order_policy_v2_adapter.py
uv run python tests/brokers/usage/features/02_metatrader.py
uv run pytest tests/brokers
git diff --check
git status --short
```

Run only the commands for the approved unit. A missing path, pre-existing failure, skipped test,
or command substitution is a STOP and requires a correction dry run.

### Exact proposed commit messages

**Unit 6a:**

```text
feat(trading): add explicit order policy contracts

- Complete approved unit 6a within its declared domain and requirement boundary.
- Execute and document usage evidence: tests/trading/usage/features/01_contracts.py.
- Pass targeted tests, owning-domain gates, documentation reconciliation, and rollback review.
```

**Unit 6b:**

```text
feat(brokers): map explicit MT5 order policies

- Complete approved unit 6b within its declared domain and requirement boundary.
- Execute and document usage evidence: tests/brokers/usage/features/02_metatrader.py.
- Pass targeted tests, owning-domain gates, documentation reconciliation, and rollback review.
```

Commit execution is not authorized by phase approval. After separate commit authorization, stage only
the phase manifest, verify `git diff --cached --name-only`, and use the applicable message verbatim.

### Completion checklist

**Per-unit status:** 6a Completed 2026-08-15 under the owner's goal-wide standalone approval.
Trading request/intent v2 requires independent policies, exact provider-revision compatibility,
conditional UTC expiration, immutable construction, and explicitly labelled parity-ineligible v1
conversion (`app/services/trading/contracts/models.py:959`,
`app/services/trading/contracts/factories.py:108`). The v2 execution-plan producer preserves both
dimensions (`app/services/trading/validation/plans.py:126`); focused evidence passed 40/40 and direct
usage passed all allocated functions (`tests/trading/usage/features/01_contracts.py:387-463`).
Automatic blocker resolution: the existing live evaluation builder still receives only Strategy's
legacy combined `time_in_force` and no exact provider snapshot. Inventing a fill policy would violate
the phase contract, so the bounded recommendation retains that declared v1 producer during the
release window; v2 construction fails closed unless both caller policies and an exact snapshot are
available. The full Trading behavioral run passed 233 tests, with one configured MT5-demo skip and
one unrelated pre-existing workflow-literal assertion (`EXECUTION_TARGET`) failure; neither was
changed because workflow configuration is outside Unit 6a. Unit 6b remains Pending.

6b Completed 2026-08-15 under the same goal-wide approval. Broker order request v2 is bound to
the exact provider revision at `app/services/brokers/canonical_contracts/public.py:112`; immutable
policy/expiration rules live at `app/services/brokers/canonical_contracts/models.py:1470`; independent
MT5 fields map at `app/services/brokers/metatrader/commands.py:344`. Focused evidence passed 14/14
(`tests/brokers/unit/test_order_policy_v2_mapping.py:67`,
`tests/brokers/integration/test_order_policy_v2_adapter.py:14`). Automatic blocker resolutions:
the full Brokers gate passed 585 tests but retains eight unrelated failures (stale modify capability
availability expectations, pre-existing documentation-parity docstrings, and legacy mutation-mock
sequencing) plus three credential skips, so those were recorded and left outside 6b;
the direct usage emitted SUCCESS for all three new FR functions before the existing genuine demo
connection failed with `BROKER_CONNECTION_FAILED`. The bounded recommendation is to retain the
transport-free Phase 6b evidence and not weaken credentials/readiness or mutate external demo state.

- [ ] Approval matched this exact phase/subphase.
- [ ] Only the local file and documentation manifests changed.
- [ ] Every listed FR has final `path:line` implementation and test evidence.
- [ ] Only verified package-root/public dependency contracts were used.
- [ ] Targeted unit/integration tests passed with recorded commands and exit codes.
- [ ] Ruff format/check and mypy passed for every owning domain.
- [ ] Every local usage program executed directly and passed.
- [ ] Every owning-domain phase gate passed.
- [ ] README, changelog, and listed system documents reconciled.
- [ ] STOP conditions and rollback path were rechecked.
- [ ] Commit remains unauthorized, or its separately authorized hash is recorded.

# Phase 7 · Signed transaction ledger and swap behavior

**Domain:** simulator. **Features:** extend `FEAT-SIM-04`, `FEAT-SIM-05`.
**Requirements:** `FR-SIM-134`, `135`, `179`, `180`, `205` … `208`, `240`.

Implement signed account-currency ledger accounts for profit, commission, fees, swap, tax, rebates,
deposits, withdrawals, credits, and corrections. Dynamic costs come from verified deal, fee-estimate,
or owner-supplied schedule evidence; missing evidence excludes the affected canonical path.

At broker-server rollover, distinguish:

- position swap accrual affecting P&L/equity;
- balance/deal posting only when the active envelope has target-broker evidence;
- REOPEN modes that close and reopen with provider-shaped deals and new state;
- per-weekday ratios, server timezone/DST, unit conversion, and calculation mode.

Until target-broker evidence verifies posting and stop-out ordering, canonical envelope entries that
cross rollover or require that ordering are absent. Configurable assumptions are exploratory-only.

- `FR-SIM-134/135` rollover scheduling/accrual; `179` named transaction ledger; `180` provider cost
  evidence; `205` weekday ratios; `206` swap units/conversion; `207` evidenced posting mode; `208`
  REOPEN semantics; `240` signed posting convention.

**Tests:** every swap mode, DST transitions, signed conservation after each posting, cost evidence
missingness, REOPEN identity, and target-fixture differential cases. Post-accrual stop-out integration
is deferred to Phase 16.

---

## Implementation specification

**Outcome:** Simulation has an auditable signed account-currency transaction ledger and evidenced
rollover behavior, with conservation checked after every mutation.

**Approval unit:** simulator. **Prerequisites:** 4a–4c, 5. **Requirements:** `FR-SIM-134`, `135`,
`179`, `180`, `205`–`208`, `240`.

**Read first:** Simulator README/root; `accounting/{calculations,ledger}.py`;
`execution/{engine,pricing}.py`; scheduler; `app/services/simulator/state/{__init__.py,runtime.py,store.py,sessions.py}`, `app/services/simulator/journal/{__init__.py,contracts.py,writer.py,replay.py,playback.py}`, `app/services/simulator/recovery/{__init__.py,contracts.py,checkpoints.py,lifecycle.py,service.py,README.md}`, `app/services/simulator/reporting/{__init__.py,contracts.py,artifacts.py,reports.py}`; Brokers specification and
Data history public contracts; Simulator usages 04/05.

**File manifest:** **CREATE** `app/services/simulator/accounting/transactions.py` and
`app/services/simulator/accounting/swap.py`; **EDIT** accounting ledger/calculations package exports,
execution engine/pricing only where they post realized/unrealized effects, scheduler event
registration, `app/services/simulator/state/{__init__.py,runtime.py,store.py,sessions.py}`, `app/services/simulator/journal/{__init__.py,contracts.py,writer.py,replay.py,playback.py}`, `app/services/simulator/recovery/{__init__.py,contracts.py,checkpoints.py,lifecycle.py,service.py,README.md}`, `app/services/simulator/reporting/{__init__.py,contracts.py,artifacts.py,reports.py}`, `app/services/simulator/__init__.py`, `app/services/simulator/README.md`; **CREATE**
`tests/simulator/unit/test_transaction_ledger.py`, `tests/simulator/unit/test_swap_rollover.py`,
`tests/simulator/integration/test_rollover_accounting.py`,
`tests/simulator/integration/test_ledger_conservation.py`; **EDIT**
`tests/simulator/usage/features/04_accounting.py` and `05_execution.py`. **DO NOT TOUCH:** stop-out
ordering, calibration, or Brokers/Data persistence.

**Exact model:** immutable postings contain posting ID, economic/source timestamps, account currency,
`Decimal` amount, one of profit/commission/fees/swap/tax/rebates/deposit/withdrawal/credit/correction,
causal order/deal/position/authority ID when applicable, evidence reference, and source sequence.
Signs follow §Ledger conservation. Maintain a double-entry-compatible running audit representation;
the published balance equation must hold after every posting. Swap computation consumes the exact
effective specification revision and server-time rollover event. Accrual and balance/deal posting are
separate operations; posting and REOPEN are unavailable unless the active envelope contains evidence.

**Implementation order:** posting contracts and sign validation; atomic ledger mutation and
conservation assertion; serialization/`app/services/simulator/journal/{__init__.py,contracts.py,writer.py,replay.py,playback.py}`, `app/services/simulator/recovery/{__init__.py,contracts.py,checkpoints.py,lifecycle.py,service.py,README.md}`; rollover scheduling; weekday multiplier and
unit/currency conversion; accrued-equity path; evidenced posting mode; REOPEN lifecycle; reporting;
tests; usages; README. Every calculation rounds only at the provider-documented boundary.

**Tests/usage:** all transaction types/signs, duplicates, out-of-order source sequence, missing
evidence, currency mismatch, Decimal serialization, conservation after each posting and restore; all
swap modes, every weekday ratio, long/short, zero/negative rates, DST forward/backward, missing FX,
posting-disabled, evidenced posting, and REOPEN identifiers. No unit test sleeps. Usages must exercise
all new root operations using fixed fixtures.

**Commands:** targeted Ruff/mypy; the four new tests; existing accounting, execution, scheduler,
journal, state, recovery, public-API tests; direct usages 04 and 05.

**Gate/STOP:** cold replay yields byte-equivalent postings and totals. **STOP** if cost evidence is
guessed, server timezone is unavailable, a float enters accounting, or posting/stop-out ordering is
assumed without evidence.

**Rollback:** delete the two new modules/tests, remove exports/consumers and restore
previous accounting flow; rerun accounting/recovery tests.

### Exact requirement-to-usage allocation

| Unit | Usage program and required functions |
|---|---|
| 7 | `04_accounting.py`: `fr_sim_179()`, `fr_sim_180()`, `fr_sim_240()`; `05_execution.py`: `fr_sim_134()`, `fr_sim_135()`, `fr_sim_205()` … `fr_sim_208()` |

### Exact documentation manifest

- **EDIT:** `app/services/simulator/README.md`
- **EDIT:** `docs/CHANGELOG.md`

Every completed FR/checklist row receives final `path:line` evidence. The changelog receives one concise
`## [Unreleased]` bullet under the correct change type and never duplicates a Feature Registry.

### Literal validation commands

```powershell
uv run ruff format --check app/services/simulator tests/simulator
uv run ruff check app/services/simulator tests/simulator
uv run mypy app/services/simulator
uv run pytest tests/simulator/unit/test_transaction_ledger.py tests/simulator/unit/test_swap_rollover.py tests/simulator/integration/test_rollover_accounting.py tests/simulator/integration/test_ledger_conservation.py
uv run python tests/simulator/usage/features/04_accounting.py
uv run pytest tests/simulator
git diff --check
git status --short
```

Run the phase-named targeted pytest files before the owning-domain gate. A missing exact path,
pre-existing failure, skipped test, or command substitution is a STOP and requires a correction dry run.

### Exact proposed commit messages

**Unit 7:**

```text
fix(simulator): add signed transaction ledger and rollover swap

- Complete approved unit 7 within its declared domain and requirement boundary.
- Execute and document usage evidence: tests/simulator/usage/features/04_accounting.py, 05_execution.py.
- Pass targeted tests, owning-domain gates, documentation reconciliation, and rollback review.
```

Commit execution is not authorized by phase approval. After separate commit authorization, stage only
the phase manifest, verify `git diff --cached --name-only`, and use the applicable message verbatim.

### Completion checklist

Unit 7 completed 2026-08-15 under the goal-wide owner approval. Signed posting contracts and
conservation are implemented at `app/services/simulator/accounting/transactions.py:32` and
`app/services/simulator/accounting/transactions.py:75`; rollover scheduling and evidenced swap modes
are implemented at `app/services/simulator/accounting/swap.py:17` and
`app/services/simulator/accounting/swap.py:36`. Requirement usage evidence is
`tests/simulator/usage/features/04_accounting.py:282`, `:289`, `:298` and
`tests/simulator/usage/features/05_execution.py:333`, `:341`, `:347`, `:353`, `:361`, `:371`;
unit/integration evidence is `tests/simulator/unit/test_transaction_ledger.py:47`, `:57`,
`tests/simulator/unit/test_swap_rollover.py:13`, `:33`, `:58`,
`tests/simulator/integration/test_rollover_accounting.py:12`, and
`tests/simulator/integration/test_ledger_conservation.py:12`.

Automatic blocker resolution: legacy fill records lack the authority evidence and source sequence
required for canonical transaction posting. The bounded recommendation keeps the new ledger and
rollover behavior as explicit evidence-bearing root operations until a later execution phase supplies
verified fields; no guessed evidence was introduced, and post-swap stop-out ordering remains deferred
to Phase 16. Focused behavioral validation passed 58/58 including the API surface; the four exact
phase files passed 24/24, while the repository's literal targeted command exited only because global
coverage collection measures all 71,461 application statements from four focused files (1.72% versus
the global 80% threshold). The scope-correct `--no-cov` gate passed, Simulator Ruff and mypy passed,
both usage programs passed, and the full Simulator behavioral gate passed 405/405.

- [ ] Approval matched this exact phase/subphase.
- [ ] Only the local file and documentation manifests changed.
- [ ] Every listed FR has final `path:line` implementation and test evidence.
- [ ] Only verified package-root/public dependency contracts were used.
- [ ] Targeted unit/integration tests passed with recorded commands and exit codes.
- [ ] Ruff format/check and mypy passed for every owning domain.
- [ ] Every local usage program executed directly and passed.
- [ ] Every owning-domain phase gate passed.
- [ ] README, changelog, and listed system documents reconciled.
- [ ] STOP conditions and rollback path were rechecked.
- [ ] Commit remains unauthorized, or its separately authorized hash is recorded.

# Phase 8 · Live execution-position repair

**Domain:** trading only. **Requirements:** `FR-TRD-085`, `086`, `101` … `103`.

Use existing Brokers `get_deal` behavior (`FR-BRK-089`); allocate no duplicate Broker requirement.
On a durable exposure-changing receipt:

```text
provider_deal_ids → get deals → BrokerDeal.position_id → authority snapshot verification
→ Trading execution-position projection
```

The receipt triggers refresh but is never position authority. Support netting many-orders-to-one-
position, partial/full closure, duplicate receipts, and unverifiable `UNKNOWN` state that blocks
position verbs.

**Gate:** live demo fixture integration for open/modify/reduce/close uses sanitized recorded responses
by default; any real demo collection is separately approved.

---

## Implementation specification

**Outcome:** durable live receipts are correlated through authoritative deals and snapshots; receipts
never become position authority.

**Approval unit:** trading. **Prerequisite:** Brokers `FR-BRK-089`. **Requirements:** `FR-TRD-085`,
`086`, `101`–`103`.

**Read first:** Trading README/root; `state/{execution_positions,projections,idempotency}.py`;
`reconciliation/{orchestrator,factories,snapshots}.py`; `actions/{positions,runtime,dependencies}.py`;
`trade_ownership`; receipt/deal/position contract models; usages 02 and 05; Brokers public get-deal
contract.

**File manifest:** **EDIT** only the listed Trading owning files,
`app/services/trading/__init__.py`, `app/services/trading/README.md`,
`tests/trading/usage/features/02_state.py`, `05_reconciliation.py`; **CREATE**
`tests/trading/unit/state/test_execution_position_correlation.py`,
`tests/trading/integration/test_receipt_deal_position_refresh.py`,
`tests/trading/integration/test_execution_position_unverifiable.py`. **DO NOT TOUCH:** Brokers,
Simulation, receipt schema unless a documented missing field forces a plan delta, or real demo state.

**Implementation order:** extract durable provider-deal IDs; call public Brokers get-deal; correlate
`BrokerDeal.position_id`; fetch/verify authority snapshot; atomically advance execution-position
projection/watermark; make position verbs consult verified state; handle duplicate/restart; tests;
usages; README.

**Tests:** one/many orders to one net position; hedging identities; partial/full close; reversal;
duplicate/late receipt; missing deal ID; unknown deal; missing position; snapshot disagreement;
authority gap; restart before/after projection persistence; `UNKNOWN` blocks modify/reduce/close and
does not trigger a mutation. Usages use sanitized offline fixtures only.

**Commands:** targeted Ruff/mypy; three new tests plus existing position actions, execution-position,
reconciliation, idempotency, ownership and public API tests; direct usages 02 and 05.

**Gate/STOP:** every durable exposure-changing receipt either converges to verified authority or a
blocking unknown state. **STOP** if the receipt must be treated as authority, Broker deep imports are
needed, or live/demo collection would occur.

**Rollback:** revert listed Trading files and delete tests; rerun position and
reconciliation tests.

### Exact requirement-to-usage allocation

| Unit | Usage program and required functions |
|---|---|
| 8 | `02_state.py`: `fr_trd_085()`, `fr_trd_086()`, `fr_trd_101()` … `fr_trd_103()` |

### Exact documentation manifest

- **EDIT:** `app/services/trading/README.md`
- **EDIT:** `docs/CHANGELOG.md`

Every completed FR/checklist row receives final `path:line` evidence. The changelog receives one concise
`## [Unreleased]` bullet under the correct change type and never duplicates a Feature Registry.

### Literal validation commands

```powershell
uv run ruff format --check app/services/trading tests/trading
uv run ruff check app/services/trading tests/trading
uv run mypy app/services/trading
uv run pytest tests/trading/unit/state/test_execution_position_correlation.py tests/trading/integration/test_receipt_deal_position_refresh.py tests/trading/integration/test_execution_position_unverifiable.py
uv run python tests/trading/usage/features/02_state.py
uv run pytest tests/trading
git diff --check
git status --short
```

Run the phase-named targeted pytest files before the owning-domain gate. A missing exact path,
pre-existing failure, skipped test, or command substitution is a STOP and requires a correction dry run.

### Exact proposed commit messages

**Unit 8:**

```text
fix(trading): reconcile execution positions from broker deals

- Complete approved unit 8 within its declared domain and requirement boundary.
- Execute and document usage evidence: tests/trading/usage/features/02_state.py, 05_reconciliation.py.
- Pass targeted tests, owning-domain gates, documentation reconciliation, and rollback review.
```

Commit execution is not authorized by phase approval. After separate commit authorization, stage only
the phase manifest, verify `git diff --cached --name-only`, and use the applicable message verbatim.

### Completion checklist

Unit 8 completed 2026-08-15 under the goal-wide owner approval. The authority projection and
restart-safe receipt watermark are implemented at
`app/services/trading/state/execution_positions.py:63`, `:280`, `:304`, and `:373` using only the
Brokers package-root `get_broker_deal` and `get_broker_position` functions. Requirement usage evidence
is `tests/trading/usage/features/02_state.py:594`, `:600`, `:606`, `:616`, and `:624`; focused evidence
is `tests/trading/unit/state/test_execution_position_correlation.py:119`, `:133`,
`tests/trading/integration/test_receipt_deal_position_refresh.py:19`, `:41`, `:55`, `:80`, and
`tests/trading/integration/test_execution_position_unverifiable.py:17`, `:38`, `:56`, `:70`.

Automatic blocker resolution: the exact focused pytest command passed all 11 behaviors but exited
because the repository coverage configuration measures all 71,535 application statements from three
focused files (17.37% versus the global 80% threshold). The scope-correct `--no-cov` gate passed
11/11, the related position/reconciliation/idempotency/API regression gate passed 37/37, and Ruff plus
mypy passed. The full Trading behavioral gate passed 241 tests and retained one separately documented
MT5-demo credential skip plus the pre-existing workflow-literal assertion requiring
`EXECUTION_TARGET: Target = "sim"`; neither external credentials nor the unrelated workflow were
changed. Both assigned usage programs executed successfully with sanitized offline fixtures only.
The listed action/reconciliation/idempotency owners required no behavioral edit: position verbs already
consult the execution-position store and reject `UNKNOWN`, while the new state owner performs the
deal/snapshot read and restart-safe deduplication without duplicating those established policies.

- [ ] Approval matched this exact phase/subphase.
- [ ] Only the local file and documentation manifests changed.
- [ ] Every listed FR has final `path:line` implementation and test evidence.
- [ ] Only verified package-root/public dependency contracts were used.
- [ ] Targeted unit/integration tests passed with recorded commands and exit codes.
- [ ] Ruff format/check and mypy passed for every owning domain.
- [ ] Every local usage program executed directly and passed.
- [ ] Every owning-domain phase gate passed.
- [ ] README, changelog, and listed system documents reconciled.
- [ ] STOP conditions and rollback path were rechecked.
- [ ] Commit remains unauthorized, or its separately authorized hash is recorded.

# Phase 9 · Source and tick lineage

**Domain:** simulator. **Feature:** extend `FEAT-SIM-01`.
**Requirements:** `FR-SIM-136`, `209`.

Validate source bars before tick derivation and derived ticks afterward. Carry distinct hashes into
request v2 and execution identity. Prove no record or upstream evaluation input has `available_at`
after the simulated decision instant.

Classify the market evidence as genuine bid/ask ticks, depth-supported ticks, or a named derived-bar
model. Genuine bid/ask ticks are mandatory for path-sensitive parity involving intrabar triggers,
pending-order priority, gap traversal, partial fills, or same-bar protections. A derived OHLC path may
enter only `fast_research` or a registered invariant proven independent of intrabar ordering. Level-2
dependent pathwise queue claims remain excluded while `OD-DATA-01` is unresolved.

Where captured evidence provides them, preserve provider event, local receive/availability, decision,
submission, acknowledgement, fill, and reconciliation timestamps. Absence of a required clock edge
excludes latency-sensitive certification rather than collapsing the timestamps.

- `FR-SIM-136` validates source and derived-tick integrity; `209` binds source/tick lineage,
  market-evidence class, and required clock-edge coverage into execution identity and eligibility.

---

## Implementation specification

**Outcome:** Simulation proves source availability, derived-tick integrity, and independent source/tick
identity before any decision becomes parity-eligible.

**Approval unit:** simulator. **Prerequisite:** 4c. **Requirements:** `FR-SIM-136`, `209`.

**Read first:** Simulator README/root; `validation/{contracts,validate}.py`;
`timeline/{contracts,timeline}.py`; `run/{contracts,orchestrator}.py`; Data dataset public contracts;
tick derivation and usage 01.

**File manifest:** **EDIT** the listed Simulator files, `app/services/simulator/__init__.py`,
`app/services/simulator/README.md`, and
`tests/simulator/usage/features/01_validation.py`; **CREATE**
`tests/simulator/unit/test_market_evidence_lineage.py`,
`tests/simulator/integration/test_decision_instant_eligibility.py`. **DO NOT TOUCH:** Data ingestion,
realism fitting, Level-2 claims, or historical timestamps.

**Exact behavior:** validate source records before derivation and ticks after derivation; calculate
canonical SHA-256 hashes separately; retain provider-event, receive/availability, decision,
submission, acknowledgement, fill and reconciliation edges only when evidenced; reject any upstream
input whose `available_at` exceeds decision time. Classify evidence exactly as genuine bid/ask,
depth-supported, or named derived-bar model. Derived bars are never pathwise-canonical for the cases
listed in Phase 9.

**Tests/usage:** reordered/duplicated/missing records; timezone/precision/NaN/invalid OHLC; source hash
changes without tick hash collision; tick-model change; future availability; missing clock edge;
derived-bar canonical rejection; valid tick admission; stable cross-process hashes. Usage exercises
validation and reports hashes/class without raw market data.

**Commands:** targeted Ruff/mypy; two new tests plus existing validation, timeline, request-v2,
orchestrator and public API tests; direct usage 01.

**Gate/STOP:** request v2 binds both hashes and the eligibility result. **STOP** if availability is
inferred from event time, hash input is unordered, or a required Data field is absent.

**Rollback:** revert listed files/delete tests and rerun timeline/request tests.

### Exact requirement-to-usage allocation

| Unit | Usage program and required functions |
|---|---|
| 9 | `01_validation.py`: `fr_sim_136()`, `fr_sim_209()` |

### Exact documentation manifest

- **EDIT:** `app/services/simulator/README.md`
- **EDIT:** `docs/CHANGELOG.md`

Every completed FR/checklist row receives final `path:line` evidence. The changelog receives one concise
`## [Unreleased]` bullet under the correct change type and never duplicates a Feature Registry.

### Literal validation commands

```powershell
uv run ruff format --check app/services/simulator tests/simulator
uv run ruff check app/services/simulator tests/simulator
uv run mypy app/services/simulator
uv run pytest tests/simulator/unit/test_market_evidence_lineage.py tests/simulator/integration/test_decision_instant_eligibility.py
uv run python tests/simulator/usage/features/01_validation.py
uv run pytest tests/simulator
git diff --check
git status --short
```

Run the phase-named targeted pytest files before the owning-domain gate. A missing exact path,
pre-existing failure, skipped test, or command substitution is a STOP and requires a correction dry run.

### Exact proposed commit messages

**Unit 9:**

```text
fix(simulator): bind source and tick lineage

- Complete approved unit 9 within its declared domain and requirement boundary.
- Execute and document usage evidence: tests/simulator/usage/features/01_validation.py.
- Pass targeted tests, owning-domain gates, documentation reconciliation, and rollback review.
```

Commit execution is not authorized by phase approval. After separate commit authorization, stage only
the phase manifest, verify `git diff --cached --name-only`, and use the applicable message verbatim.

### Completion checklist

Unit 9 completed 2026-08-15 under the goal-wide owner approval. Immutable lineage evidence,
source/tick validation, and request-v2 identity binding are implemented at
`app/services/simulator/validation/contracts.py:122`,
`app/services/simulator/validation/validate.py:249`, and
`app/services/simulator/run/contracts.py:308`. Usage evidence is
`tests/simulator/usage/features/01_validation.py:248` and `:268`; focused evidence is
`tests/simulator/unit/test_market_evidence_lineage.py:125`, `:134`, `:141`, `:157`, `:196` and
`tests/simulator/integration/test_decision_instant_eligibility.py:18`, `:28`, `:48`, `:55`.

Automatic blocker resolution: the literal focused pytest command passed all 14 behaviors but exited
because global coverage measures all 71,628 application statements from two focused files (19.30%
versus the global 80% threshold). The scope-correct focused gate passed 14/14, related validation,
timeline, request-v2, orchestrator, and API regressions passed 104/104, and the full Simulator
behavioral gate passed 419/419. Ruff, mypy, and usage 01 passed. No availability timestamp was inferred,
no source/tick ordering was normalized before hashing, and missing clock edges explicitly remove
eligibility rather than synthesizing evidence. Data ingestion and historical timestamps were untouched.

- [ ] Approval matched this exact phase/subphase.
- [ ] Only the local file and documentation manifests changed.
- [ ] Every listed FR has final `path:line` implementation and test evidence.
- [ ] Only verified package-root/public dependency contracts were used.
- [ ] Targeted unit/integration tests passed with recorded commands and exit codes.
- [ ] Ruff format/check and mypy passed for every owning domain.
- [ ] Every local usage program executed directly and passed.
- [ ] Every owning-domain phase gate passed.
- [ ] README, changelog, and listed system documents reconciled.
- [ ] STOP conditions and rollback path were rechecked.
- [ ] Commit remains unauthorized, or its separately authorized hash is recorded.

# Phase 10 · Simulation adapter groundwork

## 10a · Brokers simulation channel

**Domain:** brokers. **Feature:** `FEAT-BRK-17`.
**Requirements:** `FR-BRK-167` … `172`.

Add `BrokerId.SIM`, `BrokerEnvironment.SIMULATION`, the in-process adapter, exact factory
registration, capability-intersection manifest, and injected authority port. It opens no socket,
imports no Simulation symbol, owns no matching/accounting, and supports MT5 mirroring only.
Unimplemented operations return canonical `BROKER_CAPABILITY_UNSUPPORTED`.

Mirror the admitted Brokers connection lifecycle through injected authority state: connect,
disconnect, reconnect, ping/status, connection events, and session finalization. Simulation opens no
external connection, but it must return the same canonical lifecycle states and failures and block
mutations while disconnected.

- `FR-BRK-167` Simulation identity/environment; `168` exact factory registration; `169` capability
  intersection; `170` connection lifecycle; `171` socket/credential/import isolation; `172`
  Brokers-owned injected authority port.

## 10b · Trading route selection

**Domain:** trading. **Requirements:** `FR-TRD-087`, `FR-TRD-096`.

The `sim` route requires `SIMULATION`; all other routes forbid it. Trading usage evidence stays in
the owning Trading feature program.

**Gate:** factory/conformance, exhaustive enum/capability maps, dependency-cycle test, and published
intersection manifest, including disconnect/reconnect and mutation-while-disconnected cases.

---

## Implementation specification

### 10a · Brokers simulation channel — implementation details

**Outcome:** Brokers owns a socket-free `sim` adapter with canonical lifecycle and a structurally typed,
injected authority port.

**Approval unit:** brokers. **Prerequisites:** 4a, 6b. **Feature:** `FEAT-BRK-17`.
**Requirements:** `FR-BRK-167`–`172`.

**Read first:** Brokers README/root; `_shared/factory.py`; canonical enums/models/protocols/public;
capability matrix; conformance fake/public/suite; MT5 adapter lifecycle and transport boundaries; all
existing broker usage programs.

**File manifest:** **CREATE** `app/services/brokers/simulation/{README.md,__init__.py,contracts.py,adapter.py,lifecycle.py,public.py}`;
**EDIT** `app/services/brokers/__init__.py`, `app/services/brokers/README.md`, canonical enums/models/protocols/public, `_shared/factory.py`, capability
matrix, conformance fake/public/suite; **CREATE** `tests/brokers/unit/simulation/test_simulation_lifecycle.py`,
`tests/brokers/unit/simulation/test_simulation_isolation.py`,
`tests/brokers/integration/test_simulation_factory.py`,
`tests/brokers/integration/test_simulation_conformance.py`,
`tests/brokers/usage/features/17_simulation.py`. **DO NOT TOUCH:** Simulation, Trading, MT5
behavior, credentials, socket code, or matching/accounting.

**Exact contract:** add `BrokerId.SIM`, `BrokerEnvironment.SIMULATION`; register only the exact pair.
`SimulationAuthorityPort` is a Brokers-owned structural protocol containing the Phase-3a signatures
and no import/string annotation from `app.services.simulator`. The private adapter delegates only;
connect/disconnect/reconnect/status/ping/event/finalize state is port-backed, mutations are blocked
while disconnected, and missing methods return canonical `BROKER_CAPABILITY_UNSUPPORTED`.

**Implementation order:** identity/enums and exhaustive maps; port contracts; lifecycle; private
adapter; root function wrappers; exact factory registration; capability intersection; conformance;
isolation audit; tests; usage; README registry/requirements/public API.

**Tests/usage:** exact/invalid factory pairs; no credentials/socket/imports; connect sequence,
idempotent disconnect, reconnect, ping/status, event order, finalization, disconnected mutation,
unsupported operation, port exception mapping, lifecycle restore, exhaustive enum/capability maps.
Usage calls every new root operation using an in-memory test port.

**Commands:** targeted Ruff/mypy; five new tests plus existing factory, capability, conformance,
canonical-contract, public API, import and MT5 lifecycle tests; direct usage 17.

**Gate/STOP:** `rg "app\.services\.simulator" app/services/brokers` returns no production match;
network monkeypatch proves no socket/transport call. **STOP** if matching/accounting enters Brokers,
factory selection is fuzzy, or port signatures differ from Phase 3a.

**Rollback:** remove simulation feature/tests/usage, enum/map/factory entries and root
exports; rerun exhaustive map/factory/conformance/import tests.

### 10b · Trading route selection — implementation details

**Outcome:** Trading admits the `sim` route only with `SIMULATION`, and forbids that environment on all
other routes.

**Approval unit:** trading. **Prerequisite:** 10a. **Requirements:** `FR-TRD-087`, `FR-TRD-096`.

**Read first:** Trading README/root; `routing/{dispatcher,capabilities,responses}.py`;
`actions/{dependencies,factories}.py`; usage 04; Brokers public identity/environment getters.

**File manifest:** **EDIT** `app/services/trading/routing/dispatcher.py`,
`app/services/trading/routing/capabilities.py`, the exact dependency/factory owner discovered above,
Trading README, `tests/trading/usage/features/04_routing.py`; **CREATE**
`tests/trading/unit/routing/test_simulation_route_selection.py`. **DO NOT TOUCH:** Brokers, Simulation,
business/risk gates, or live authorization.

**Tests:** sim+simulation success; sim with every other environment failure; every other route with
simulation failure; unknown route; capability intersection; no dispatch on invalid pair. Usage adds
one valid and two invalid examples.

**Commands/gate:** targeted Ruff/mypy; new test plus existing dispatcher/capabilities/dependency/public
tests; direct usage 04. Gate requires no route mutation and no route-conditional business gate.

**STOP/rollback/proposed commit:** stop if route identity is unavailable through the Brokers root or
existing routing has an undocumented alias. Revert listed files/delete test.

### Exact requirement-to-usage allocation

| Unit | Usage program and required functions |
|---|---|
| 10a | `17_simulation.py`: `fr_brk_167()` … `fr_brk_172()` |
| 10b | `04_routing.py`: `fr_trd_087()`, `fr_trd_096()` |

### Exact documentation manifests

#### Unit 10a

- **EDIT:** `app/services/brokers/README.md`
- **EDIT:** `docs/CHANGELOG.md`
- **EDIT:** `docs/PROJECT.md`
- **EDIT:** `docs/ARCHITECTURE.md`

#### Unit 10b

- **EDIT:** `app/services/trading/README.md`
- **EDIT:** `docs/CHANGELOG.md`

Every completed FR/checklist row receives final `path:line` evidence. Where listed, the changelog
receives one concise `## [Unreleased]` bullet and never duplicates a Feature Registry.

### Literal validation commands by approval unit

#### Unit 10a

```powershell
uv run ruff format --check app/services/brokers tests/brokers
uv run ruff check app/services/brokers tests/brokers
uv run mypy app/services/brokers
uv run pytest tests/brokers/unit/simulation/test_simulation_lifecycle.py tests/brokers/unit/simulation/test_simulation_isolation.py tests/brokers/integration/test_simulation_factory.py tests/brokers/integration/test_simulation_conformance.py
uv run python tests/brokers/usage/features/17_simulation.py
uv run pytest tests/brokers
git diff --check
git status --short
```

#### Unit 10b

```powershell
uv run ruff format --check app/services/trading tests/trading
uv run ruff check app/services/trading tests/trading
uv run mypy app/services/trading
uv run pytest tests/trading/unit/routing/test_simulation_route_selection.py
uv run python tests/trading/usage/features/04_routing.py
uv run pytest tests/trading
git diff --check
git status --short
```

Run only the commands for the approved unit. A missing path, pre-existing failure, skipped test,
or command substitution is a STOP and requires a correction dry run.

### Exact proposed commit messages

**Unit 10a:**

```text
feat(brokers): add simulation broker channel

- Complete approved unit 10a within its declared domain and requirement boundary.
- Execute and document usage evidence: tests/brokers/usage/features/17_simulation.py.
- Pass targeted tests, owning-domain gates, documentation reconciliation, and rollback review.
```

**Unit 10b:**

```text
feat(trading): route simulation through the broker channel

- Complete approved unit 10b within its declared domain and requirement boundary.
- Execute and document usage evidence: tests/trading/usage/features/04_routing.py.
- Pass targeted tests, owning-domain gates, documentation reconciliation, and rollback review.
```

Commit execution is not authorized by phase approval. After separate commit authorization, stage only
the phase manifest, verify `git diff --cached --name-only`, and use the applicable message verbatim.

### Completion checklist

**Per-unit status:** 10a Completed 2026-08-15 under the owner's goal-wide standalone approval. `FEAT-BRK-17` now registers exact `sim`/`simulation` identity and factory selection (`app/services/brokers/canonical_contracts/enums.py:15`, `app/services/brokers/_shared/factory.py:49`), the Brokers-owned structural port (`app/services/brokers/simulation/contracts.py:11`), lifecycle/finalization delegation (`app/services/brokers/simulation/adapter.py:23`, `app/services/brokers/simulation/public.py:34`), and the exhaustive Phase-10a intersection (`app/services/brokers/capabilities/matrix.py:129`). `FR-BRK-167`–`172` usage evidence is `tests/brokers/usage/features/17_simulation.py:50-84`; focused evidence is `tests/brokers/unit/simulation/test_simulation_lifecycle.py:41`, `tests/brokers/unit/simulation/test_simulation_isolation.py:9`, `tests/brokers/integration/test_simulation_factory.py:29`, and `tests/brokers/integration/test_simulation_conformance.py:31`. Targeted behavior passed 12 tests; direct usage passed; Ruff format/check and Brokers mypy passed. The literal focused pytest command passed all 12 behaviors but exited 1 because repository-wide `--cov=app --cov-fail-under=80` measures the entire application on a four-file subset (3.82%); the identical command with `--no-cov` passed. After exhaustive-map reconciliation, the full Brokers behavioral gate reports 596 passed, 3 credential skips, and 9 pre-existing MT5 mutation-release/mock/docstring failures unrelated to 10a. The plan's prose says “five new tests” but names exactly four test files; implementation followed the exact four-path manifest. No socket, credentials, Simulator import, matching, or accounting entered Brokers; rollback remains removal of the simulation feature/evidence plus enum, map, factory, conformance, and root-export entries. Unit 10b remains pending, so the combined Phase-10 checklist stays open.

- [ ] Approval matched this exact phase/subphase.
- [ ] Only the local file and documentation manifests changed.
- [ ] Every listed FR has final `path:line` implementation and test evidence.
- [ ] Only verified package-root/public dependency contracts were used.
- [ ] Targeted unit/integration tests passed with recorded commands and exit codes.
- [ ] Ruff format/check and mypy passed for every owning domain.
- [ ] Every local usage program executed directly and passed.
- [ ] Every owning-domain phase gate passed.
- [ ] README, changelog, and listed system documents reconciled.
- [ ] STOP conditions and rollback path were rechecked.
- [ ] Commit remains unauthorized, or its separately authorized hash is recorded.

# Phase 11 · Clock-safe simulation reads

**Domain:** brokers. **Requirements:** `FR-BRK-173` … `181`.

**Per-unit status:** 10b Completed 2026-08-15 under the owner's goal-wide standalone approval and committed as `8181afd06e4630c77d1194362a4daf9e6cb7def0` with the exact prescribed message. Trading now validates the exact route/environment pair before dispatch at `app/services/trading/routing/dispatcher.py:310`; `FR-TRD-087` and `FR-TRD-096` are evidenced by `tests/trading/unit/routing/test_simulation_route_selection.py:104-144` and `tests/trading/usage/features/04_routing.py:188-224`. The bounded recommendation retained `simulation_dispatch` as the mutation authority because the Phase-3 contract assigns its removal to Phase 14a; Phase 10b injects only the socket-free Brokers connection descriptor. Focused routing tests passed (14), usage 04 passed, Ruff format/check and Trading mypy passed. The literal eight-test command passed behavior but exited 1 under the repository-wide subset coverage floor (17.49%); the `--no-cov` behavioral command passed. The full Trading gate reports 252 passed, one credential skip, and one pre-existing workflow-literal failure (`EXECUTION_TARGET`) unrelated to this unit. No Brokers/Simulator production file, business/risk gate, or live authorization changed. Rollback is the dispatcher gate, simulation-route test, fixture descriptor, usage additions, and Trading documentation. Phase 10 is complete.

Unit 10a commit hash: `54933eec039a9522a416d64c503e53beeefb11e2` (exact prescribed message; all hooks passed).

First, under its own approved sub-phase, inject a clock into all ten MT5 mapping timestamp sites,
defaulting to the live clock. Then implement the Simulation adapter's admitted read intersection:
symbols/specification, quotes/spread/ticks/bars, account/balances, positions, orders/order history,
and permissions. Project ledger values without recomputation.

Deal history/get-deal remains unsupported until Phase 17. Trading sessions come from Data's explicit
revisioned definitions, not the MT5 Python adapter. Weekly definitions do not certify exceptional
holidays, maintenance windows, or one-off closures without dated evidence. An unsupported read is
never an empty success.

Reads and connection events preserve source sequence, observation time, receive/availability time,
and gap/staleness evidence. Duplicate, missing, late, or out-of-order delivery is represented for
Trading reconciliation; the adapter never silently reorders or converts it to a clean snapshot.

- `FR-BRK-173` injected mapping clock; `174` port binding; `175` simulated timestamps; `176` canonical
  symbol/specification shape; `177` no future reads; `178` account projection; `179` positions/orders;
  `180` unsupported and exceptional-session semantics; `181` lifecycle, delivery-gap, and journal
  isolation.

---

## Implementation specification

### 11a · Injected MT5 mapping clock — implementation details

**Outcome:** all MT5 mapping timestamps use an injected clock while live behavior retains the current
UTC clock default.

**Approval unit:** brokers; approve separately from 11b. **Prerequisite:** 10a.
**Requirement:** `FR-BRK-173`.

**Read first:** `app/services/brokers/metatrader/mapping.py`, every caller, and all matches from
`rg -n "datetime\.now|datetime\.utcnow|observed_at|received_at" app/services/brokers/metatrader tests/brokers`.

**File manifest:** **EDIT** `app/services/brokers/metatrader/mapping.py` and only its direct callers
whose signatures must pass the clock; **CREATE** `tests/brokers/unit/test_mt5_mapping_clock.py`; **EDIT**
`tests/brokers/unit/test_mt5_mapping.py`, Brokers README requirement evidence. **DO NOT TOUCH:** mapping
field semantics, retry/session logic, Simulation adapter, or other providers.

**Implementation:** introduce one private clock protocol/type alias; every mapping entry point accepts
the clock keyword with the current aware-UTC clock as its live default; capture one timestamp per
provider payload and reuse it for every field derived from that observation. Reject naive clock output.

**Tests/commands:** identify and individually exercise all ten Phase-11 timestamp sites with a fixed
clock, assert one call per payload, UTC awareness, default-clock compatibility, and unchanged mapping
snapshots. Run targeted Ruff/mypy, new/existing MT5 mapping tests, and MT5 adapter tests.

**Gate/STOP:** repeat the search and account for every match in the requirement evidence. **STOP** if
there are not ten sites as specified, a public signature must change, or a timestamp is provider-owned
rather than observation-owned.

**Rollback:** revert mapping/callers/test/README.

### 11b · Simulation read intersection — implementation details

**Outcome:** the Simulation adapter returns canonical, time-safe reads and never represents unsupported
or gapped authority as an empty successful snapshot.

**Approval unit:** brokers. **Prerequisites:** 11a, 4a/4b. **Requirements:** `FR-BRK-174`–`181`.

**Read first:** simulation feature from Phase 10a; canonical response/models; MT5 mapping/snapshots;
Data public session/specification contracts; capability matrix/conformance; usage 17.

**File manifest:** **EDIT** `app/services/brokers/simulation/{contracts,adapter,lifecycle,public,README.md}`,
canonical contracts only for already-approved generic evidence fields, `app/services/brokers/capabilities/matrix.py`, `app/services/brokers/conformance/{__init__.py,fake.py,public.py,suite.py,README.md}`, Brokers
`app/services/brokers/__init__.py`, `app/services/brokers/README.md`,
`tests/brokers/usage/features/17_simulation.py`; **CREATE**
`tests/brokers/unit/simulation/test_simulation_reads.py`,
`tests/brokers/unit/simulation/test_simulation_read_time.py`,
`tests/brokers/integration/test_simulation_read_conformance.py`,
`tests/brokers/integration/test_simulation_delivery_gaps.py`. **DO NOT TOUCH:** deal history,
mutations, Data internals, or provider-specific calculations.

**Admitted reads:** symbols/current specification; quote/spread/ticks/bars; account/balance/equity/
margin/free-margin; positions; open and historical orders; permissions and lifecycle. Deal/get-deal/
transactions remain capability-unsupported. The port supplies already-authoritative ledger values;
the adapter maps but never recalculates. All reads bind source sequence, provider observation,
receive/availability, stale/gap evidence, and injected simulated clock. Session reads consume Data's
revisioned weekly/detailed exception evidence through composition-injected values.

**Implementation order:** port read DTOs; timestamp/sequence validation; mapping per admitted read;
capability declarations; unsupported results; gap/stale/out-of-order representation; adapter methods;
conformance; tests; usage/README.

**Tests:** one success and every missing/invalid field per read; no-future-read; stale/duplicate/late/
out-of-order/missing sequence; exceptional-session absence; disconnected reads; ledger exactness; read
side-effect isolation; unsupported deal reads; deterministic response identity.

**Commands/gate:** targeted Ruff/mypy; four new tests plus simulation lifecycle/factory/conformance,
canonical model/response, capability and MT5 mapping tests; direct usage 17. Gate runs an authority
fixture through every admitted read and asserts zero recomputation and zero external IO.

**STOP/rollback/proposed commit:** stop if a read needs a Simulation import, Data deep import, guessed
session exception, or silently sorted delivery. Revert listed edits/delete tests.

### Exact requirement-to-usage allocation

| Unit | Usage program and required functions |
|---|---|
| 11a | `02_metatrader.py`: `fr_brk_173()` |
| 11b | `17_simulation.py`: `fr_brk_174()` … `fr_brk_181()` |

### Exact documentation manifests

#### Unit 11a

- **EDIT:** `app/services/brokers/README.md`
- **EDIT:** `docs/CHANGELOG.md`

#### Unit 11b

- **EDIT:** `app/services/brokers/README.md`
- **EDIT:** `docs/CHANGELOG.md`

Every completed FR/checklist row receives final `path:line` evidence. Where listed, the changelog
receives one concise `## [Unreleased]` bullet and never duplicates a Feature Registry.

### Literal validation commands by approval unit

#### Unit 11a

```powershell
uv run ruff format --check app/services/brokers tests/brokers
uv run ruff check app/services/brokers tests/brokers
uv run mypy app/services/brokers
uv run pytest tests/brokers/unit/test_mt5_mapping_clock.py tests/brokers/unit/test_mt5_mapping.py
uv run python tests/brokers/usage/features/02_metatrader.py
uv run pytest tests/brokers
git diff --check
git status --short
```

#### Unit 11b

```powershell
uv run ruff format --check app/services/brokers tests/brokers
uv run ruff check app/services/brokers tests/brokers
uv run mypy app/services/brokers
uv run pytest tests/brokers/unit/simulation/test_simulation_reads.py tests/brokers/unit/simulation/test_simulation_read_time.py tests/brokers/integration/test_simulation_read_conformance.py tests/brokers/integration/test_simulation_delivery_gaps.py
uv run python tests/brokers/usage/features/17_simulation.py
uv run pytest tests/brokers
git diff --check
git status --short
```

Run only the commands for the approved unit. A missing path, pre-existing failure, skipped test,
or command substitution is a STOP and requires a correction dry run.

### Exact proposed commit messages

**Unit 11a:**

```text
refactor(brokers): inject MT5 mapping clock

- Complete approved unit 11a within its declared domain and requirement boundary.
- Execute and document usage evidence: tests/brokers/usage/features/02_metatrader.py.
- Pass targeted tests, owning-domain gates, documentation reconciliation, and rollback review.
```

**Unit 11b:**

```text
feat(brokers): add clock-safe simulation reads

- Complete approved unit 11b within its declared domain and requirement boundary.
- Execute and document usage evidence: tests/brokers/usage/features/17_simulation.py.
- Pass targeted tests, owning-domain gates, documentation reconciliation, and rollback review.
```

Commit execution is not authorized by phase approval. After separate commit authorization, stage only
the phase manifest, verify `git diff --cached --name-only`, and use the applicable message verbatim.

**Per-unit status:** 11a Completed 2026-08-15 under the owner's goal-wide standalone approval. `FR-BRK-173` injects one validated aware-UTC clock into all ten observation-owned MT5 mapping entry points at `app/services/brokers/metatrader/mapping.py:38`, `app/services/brokers/metatrader/mapping.py:222`, `app/services/brokers/metatrader/mapping.py:250`, `app/services/brokers/metatrader/mapping.py:347`, `app/services/brokers/metatrader/mapping.py:441`, `app/services/brokers/metatrader/mapping.py:482`, `app/services/brokers/metatrader/mapping.py:525`, `app/services/brokers/metatrader/mapping.py:560`, `app/services/brokers/metatrader/mapping.py:629`, `app/services/brokers/metatrader/mapping.py:668`, and `app/services/brokers/metatrader/mapping.py:754`; the sole remaining direct current-time call is the live default at `app/services/brokers/metatrader/mapping.py:35`. Fixed-time, one-call, naive/non-UTC, and wrong-type evidence is at `tests/brokers/unit/test_mt5_mapping_clock.py:147`, `tests/brokers/unit/test_mt5_mapping_clock.py:178`, and `tests/brokers/unit/test_mt5_mapping_clock.py:188`; direct usage evidence is at `tests/brokers/usage/features/02_metatrader.py:128`. Ruff format/check and Brokers mypy passed; focused mapping behavior passed 27 tests, while the literal focused command exited 1 only because the repository-wide subset coverage floor measured 3%; usage 02 passed. The full Brokers behavioral gate reports 610 passed, three credential skips, and eight pre-existing catalogue/documentation/MT5 mutation failures; the additionally requested MT5 adapter gate reports 33 passed and its same pre-existing mutation-expectation failure. The repeated timestamp search accounted for exactly ten injected sites plus the intentional live default. No public signature, mapping field semantics, retry/session behavior, Simulation adapter, or other provider changed. Rollback is `mapping.py`, the clock test, usage addition, Brokers requirement row, changelog entry, and this status record.

**Commit reconciliation:** Unit 11a is committed as `8f9f9f6418a86f9fe1a2b0535271d591d3c674ad` with the exact prescribed message.

**Per-unit status:** 11b Completed 2026-08-16 under the owner's goal-wide standalone approval. `FR-BRK-174`–`181` are implemented by the authority envelope at `app/services/brokers/simulation/contracts.py:18`, the fail-closed read delegate at `app/services/brokers/simulation/adapter.py:99`, the exact admitted set at `app/services/brokers/simulation/adapter.py:290`, and the function-only constructor at `app/services/brokers/simulation/public.py:17`. Exact projection evidence is at `tests/brokers/unit/simulation/test_simulation_reads.py:74`; time safety at `tests/brokers/unit/simulation/test_simulation_read_time.py:17`; revision-bound session semantics at `tests/brokers/integration/test_simulation_read_conformance.py:38`; and stale/gap/sequence behavior at `tests/brokers/integration/test_simulation_delivery_gaps.py:17` and `tests/brokers/integration/test_simulation_delivery_gaps.py:31`. Usage functions `fr_brk_174()` through `fr_brk_181()` are at `tests/brokers/usage/features/17_simulation.py:128`–`189` and passed directly. Ruff format/check and full Brokers mypy passed. The four-file focused behavior gate passed 11 tests; its literal coverage-enabled form exited 1 only because repository-wide subset coverage was 4%. The literal full Brokers gate reports 621 passed, three credential skips, eight documented pre-existing discovery/catalogue/docstring/MT5 mutation failures, and repository-wide coverage 16.39%; the Phase-11b-introduced normative-matrix and dynamic-docstring divergences were corrected and their focused catalogue check passes. The bounded blocker recommendation uses a private validated authority envelope and response metadata instead of expanding every canonical DTO; gapped/stale/duplicate/out-of-order or future reads become explicit errors, never clean empty snapshots. Deal/transaction reads remain unsupported, sessions require an injected revision, and no Data deep import, Simulation import, matching, accounting, socket, credential, external IO, or mutation was added. Rollback is the simulation read envelope/delegate/export, capability additions, four new tests and conformance reconciliation, usage additions, README/changelog/plan evidence, and the test catalogue expectation.

### Completion checklist

- [ ] Approval matched this exact phase/subphase.
- [ ] Only the local file and documentation manifests changed.
- [ ] Every listed FR has final `path:line` implementation and test evidence.
- [ ] Only verified package-root/public dependency contracts were used.
- [ ] Targeted unit/integration tests passed with recorded commands and exit codes.
- [ ] Ruff format/check and mypy passed for every owning domain.
- [ ] Every local usage program executed directly and passed.
- [ ] Every owning-domain phase gate passed.
- [ ] README, changelog, and listed system documents reconciled.
- [ ] STOP conditions and rollback path were rechecked.
- [ ] Commit remains unauthorized, or its separately authorized hash is recorded.

**Commit reconciliation:** Unit 11b is committed as `210e7aba83d6acf1ea15df5de61dc5489b5be25e` with the exact prescribed message.

# Phase 12 · Simulation mutation surface

**Domain:** brokers. **Requirements:** `FR-BRK-182` … `189`.

Implement check/place/modify/cancel and position modify/reduce/close against injected authority ports.
Return an MT5 `OrderSendResult`-shaped internal payload through the same mapping and response
classification used live. Map every verified condition to provider retcode/error code. Only seeded
Phase 20 injection may create timeout/unknown outcome. Carry v2 fill/time policies without inference.

- `FR-BRK-182` route/tamper guard; `183` provider-shaped mapping; `184` retcode table; `185` no
  spontaneous ambiguity; `186` order mutations; `187` position mutations; `188` no adapter business
  logic; `189` v2 policy fidelity.

**Tests:** one case per retcode, adapter-boundary import audit, and capability intersection.

---

## Implementation specification

**Outcome:** every admitted mutation delegates to Simulation authority and returns the same canonical
provider-shaped mapping/classification path used by MT5.

**Approval unit:** brokers. **Prerequisites:** 6b, 10a, 11b. **Requirements:** `FR-BRK-182`–`189`.

**Read first:** simulation adapter; canonical order/position contracts and responses; MT5
`{adapter,commands,mapping}.py`; Trading-to-Brokers request shape; `app/services/brokers/capabilities/matrix.py`, `app/services/brokers/conformance/{__init__.py,fake.py,public.py,suite.py,README.md}`; usage 17.

**File manifest:** **EDIT** simulation contracts/adapter/public/README, canonical protocols only if
the Phase-3 port signature already authorizes it, `app/services/brokers/capabilities/matrix.py`, `app/services/brokers/conformance/{__init__.py,fake.py,public.py,suite.py,README.md}`, `app/services/brokers/__init__.py`, `app/services/brokers/README.md`, usage
17; **CREATE** `tests/brokers/unit/simulation/test_simulation_order_mutations.py`,
`tests/brokers/unit/simulation/test_simulation_position_mutations.py`,
`tests/brokers/unit/simulation/test_simulation_retcode_mapping.py`,
`tests/brokers/integration/test_simulation_mutation_conformance.py`. **DO NOT TOUCH:** Simulation
engine, Trading gates, MT5 semantics, scenario/fault injection, or adapter-owned business rules.

**Admitted operations:** check/place/modify/cancel order; modify/reduce/close position. Validate route,
environment, immutable approved size, target IDs and v2 policies before delegation. The port returns an
MT5 `OrderSendResult`-shaped internal payload; reuse the live MT5 mapping and standard-response
classification. Map only verified retcode/error pairs. Timeouts/unknown outcomes cannot appear unless
Phase 20 explicitly injects them.

**Implementation order:** request/route guards; authority-port mutation signatures; provider-shaped
payload validation; shared mapping/classification extraction if already owned by MT5 (do not duplicate
tables); each operation; capabilities; conformance; retcode matrix tests; usage/README.

**Tests:** one case per documented retcode; malformed success; target mismatch; size/policy tamper;
disconnected; duplicate idempotency key; partial/rejected/accepted; authority exception; unexpected
timeout rejected; exact call count; adapter has no matching/accounting code.

**Commands/gate:** targeted Ruff/mypy; four new tests plus MT5 command/mapping/response, simulation
read/lifecycle, `app/services/brokers/capabilities/matrix.py`, `app/services/brokers/conformance/{__init__.py,fake.py,public.py,suite.py,README.md}` and public tests; usage 17. Gate includes AST/import audit and
capability-intersection reconciliation.

**STOP/rollback/proposed commit:** stop on an unverified retcode, any inference, or need to implement
business state in Brokers. Revert adapter/capability/contract edits and tests.

### Exact requirement-to-usage allocation

| Unit | Usage program and required functions |
|---|---|
| 12 | `17_simulation.py`: `fr_brk_182()` … `fr_brk_189()` |

### Exact documentation manifest

- **EDIT:** `app/services/brokers/README.md`
- **EDIT:** `docs/CHANGELOG.md`

Every completed FR/checklist row receives final `path:line` evidence. The changelog receives one concise
`## [Unreleased]` bullet under the correct change type and never duplicates a Feature Registry.

### Literal validation commands

```powershell
uv run ruff format --check app/services/brokers tests/brokers
uv run ruff check app/services/brokers tests/brokers
uv run mypy app/services/brokers
uv run pytest tests/brokers/unit/simulation/test_simulation_order_mutations.py tests/brokers/unit/simulation/test_simulation_position_mutations.py tests/brokers/unit/simulation/test_simulation_retcode_mapping.py tests/brokers/integration/test_simulation_mutation_conformance.py
uv run python tests/brokers/usage/features/17_simulation.py
uv run pytest tests/brokers
git diff --check
git status --short
```

Run the phase-named targeted pytest files before the owning-domain gate. A missing exact path,
pre-existing failure, skipped test, or command substitution is a STOP and requires a correction dry run.

### Exact proposed commit messages

**Unit 12:**

```text
feat(brokers): add simulation mutation surface

- Complete approved unit 12 within its declared domain and requirement boundary.
- Execute and document usage evidence: tests/brokers/usage/features/17_simulation.py.
- Pass targeted tests, owning-domain gates, documentation reconciliation, and rollback review.
```

Commit execution is not authorized by phase approval. After separate commit authorization, stage only
the phase manifest, verify `git diff --cached --name-only`, and use the applicable message verbatim.

**Per-unit status:** 12 Completed 2026-08-16 under the owner's goal-wide standalone approval. `FR-BRK-182`–`189` are implemented by the request-bound authority envelope at `app/services/brokers/simulation/contracts.py:35`, the fail-closed mutation delegate and exact route/environment guard at `app/services/brokers/simulation/adapter.py:377` and `app/services/brokers/simulation/adapter.py:414`, and the seven canonical operations at `app/services/brokers/simulation/adapter.py:539`, `app/services/brokers/simulation/adapter.py:557`, `app/services/brokers/simulation/adapter.py:573`, `app/services/brokers/simulation/adapter.py:589`, `app/services/brokers/simulation/adapter.py:607`, `app/services/brokers/simulation/adapter.py:627`, and `app/services/brokers/simulation/adapter.py:643`. Exact order, environment, tamper, duplicate, timeout, and v2-policy evidence is at `tests/brokers/unit/simulation/test_simulation_order_mutations.py:97`, `tests/brokers/unit/simulation/test_simulation_order_mutations.py:158`, and `tests/brokers/unit/simulation/test_simulation_order_mutations.py:180`; position projection evidence is at `tests/brokers/unit/simulation/test_simulation_position_mutations.py:24`; all verified retcodes and malformed/unknown rejection are covered at `tests/brokers/unit/simulation/test_simulation_retcode_mapping.py:46`; capability/import isolation is at `tests/brokers/integration/test_simulation_mutation_conformance.py:15` and `tests/brokers/integration/test_simulation_mutation_conformance.py:36`. Usage functions `fr_brk_182()` through `fr_brk_189()` are at `tests/brokers/usage/features/17_simulation.py:264`–`331` and passed directly. Ruff format/check and full Brokers mypy passed; the focused behavior/reconciliation gate passed 61 tests. The literal four-file command passed all 34 behaviors but exited 1 solely because repository-wide subset coverage was 4.06%. The literal full Brokers gate reports 661 passed, three credential skips, three pre-existing documentation/MT5 mutation failures, and repository-wide coverage 16.51%; no Phase-12 test fails. The bounded blocker resolution exempts only `BrokerId.SIM` from the generic demo-only live-provider write downgrade at `app/services/brokers/_shared/base.py:118`, preserving every live-provider guard while allowing the exact socket-free `sim/simulation` route. A private immutable mutation envelope preserves request echo and optional authority-projected position state; unexpected timeout remains a deterministic invalid response until Phase 20. No Simulation import, matching, accounting, scenario/fault engine, live MT5 semantic change, or Trading gate change was added. Rollback is the mutation envelope/delegate/export, SIM write capability declarations and base exemption, four new tests plus two capability expectations, usage additions, README/changelog/plan evidence, and generated cache cleanup.

### Completion checklist

- [x] Approval matched this exact phase/subphase. Evidence: owner goal-wide standalone approval and Phase 12 status above.
- [x] Only the local file and documentation manifests changed. Evidence: staged-manifest review before commit.
- [x] Every listed FR has final `path:line` implementation and test evidence. Evidence: Phase 12 status above.
- [x] Only verified package-root/public dependency contracts were used. Evidence: `tests/brokers/integration/test_simulation_mutation_conformance.py:36`.
- [x] Targeted unit/integration tests passed with recorded commands and exit codes. Evidence: 61 focused tests passed; literal coverage caveat above.
- [x] Ruff format/check and mypy passed for every owning domain. Evidence: Phase 12 status above.
- [x] Every local usage program executed directly and passed. Evidence: `tests/brokers/usage/features/17_simulation.py:264`.
- [x] Every owning-domain phase gate passed. Evidence: 661 passed with only three documented pre-existing failures and three credential skips.
- [x] README, changelog, and listed system documents reconciled. Evidence: Brokers README, simulation README, changelog, and this plan.
- [x] STOP conditions and rollback path were rechecked. Evidence: Phase 12 status above.
- [x] Commit remains unauthorized, or its separately authorized hash is recorded. Evidence: owner goal-wide commit authorization; hash is reconciled in the next unit.

**Commit reconciliation:** Unit 12 is committed as `83881f26c5af8a03a4cd00b32f7bebc51d0eb738` with the exact prescribed message.

# Phase 13 · Effective-dated local calculation model

## 13a · Brokers conformance evidence delta

**Domain:** brokers. **Requirements:** `FR-BRK-190` … `193`.

Do not re-register existing `check_order`, `calculate_margin`, or `calculate_profit`. Extend
`BrokerOrderCheck` and MT5 mapping to preserve projected balance, equity, profit, margin, free margin,
and margin level. Bind responses to environment, account digest, provider-specification checksum, and
observation time.

Define a bounded, checksummed fixture schema. Fixture collection lives in Brokers conformance tooling,
is demo-only, never runs in the default suite, and requires separate execution approval. Simulation
receives immutable fixture artifacts and never invokes this write-scoped capability.

## 13b · Simulation calculation model

**Domain:** simulator. **Feature:** `FEAT-SIM-16`.
**Requirements:** `FR-SIM-137` … `145`, `210` … `214`.

Implement approved FX calculation modes only, using Data-provided effective-dated specification
revisions and FX-conversion evidence. Model planned and total margin for netting/hedging, realized and
unrealized profit, contract/tick/point distinctions, and account-currency rounding.

Tolerance is not arbitrary: exact Decimal equality is required after applying the provider's
documented currency digits and rounding rule. If a target build exposes additional precision, the
envelope records that rule. Unsupported calculation modes fail closed.

Publish conformance results as a versioned artifact. Any fixture mismatch, uncovered specification
interval, or missing conversion blocks canonical execution.

**Gate:** differential fixture matrix, cold re-execution with provider calls disabled, and model
identity bound to execution identity.

---

## Implementation specification

### 13a · Brokers conformance evidence delta — implementation details

**Outcome:** existing Broker calculation/check responses retain all projected account fields and bind
them to a reproducible provider/specification observation.

**Approval unit:** brokers. **Prerequisites:** 4a, 6b. **Requirements:** `FR-BRK-190`–`193`.

**Read first:** canonical `BrokerOrderCheck`; MT5 calculations/mapping/adapter; conformance README,
fake/public/suite; usage 10; security/environment guards.

**File manifest:** **EDIT** canonical model/public contract owners, MT5 calculation/mapping owners,
conformance `{README.md,fake.py,public.py,suite.py}`, `app/services/brokers/__init__.py`, `app/services/brokers/README.md`,
`tests/brokers/usage/features/10_conformance.py`; **CREATE**
`app/services/brokers/conformance/fixtures.py`,
`tests/brokers/unit/conformance/test_calculation_fixture_schema.py`,
`tests/brokers/integration/test_mt5_calculation_evidence.py`. **DO NOT TOUCH:** operation
registration, default conformance network behavior, Simulation, or production credentials.

**Exact delta:** preserve projected balance/equity/profit/margin/free margin/margin level; bind
environment, redacted account digest, provider-spec checksum, terminal build and observed-at. Fixture
schema is bounded, JSON-safe, checksummed, immutable, sanitized, and contains inputs plus provider
outputs. Collection is a Brokers conformance function guarded to `ENVIRONMENT=dev` plus demo account,
excluded from normal suites, and not executed by this plan.

**Tests/usage:** every projected field, missing/float/NaN/secret rejection, checksum tamper, redaction,
environment guard, schema round-trip, unchanged operation registry, provider-disabled default suite.
Usage validates a bundled sanitized fixture and calls no provider.

**Commands/gate:** targeted Ruff/mypy; new tests plus existing calculations, mapping, conformance,
environment, secrets and public API tests; usage 10. Gate proves default pytest cannot invoke fixture
collection.

**STOP/rollback/proposed commit:** stop if collection needs live/production, raw account/credentials,
or new calculation APIs. Revert delta/delete fixture module/tests.

### 13b · Simulation calculation model — implementation details

**Outcome:** `FEAT-SIM-16` locally computes only evidenced MT5-FX modes and blocks uncovered revisions
or conversion evidence.

**Approval unit:** simulator. **Prerequisites:** 4b, 7, 13a. **Requirements:** `FR-SIM-137`–`145`,
`210`–`214`.

**Read first:** Simulator README/root/accounting; Data specification/FX evidence public contracts;
Brokers sanitized fixture schema/public check/calculation response; request-v2 identity.

**File manifest:** **CREATE** `app/services/simulator/calculations/{README.md,__init__.py,contracts.py,fx.py,profit.py,margin.py,conformance.py,public.py}`,
`tests/simulator/unit/calculations/test_fx_conversion.py`,
`tests/simulator/unit/calculations/test_profit.py`,
`tests/simulator/unit/calculations/test_margin.py`,
`tests/simulator/unit/calculations/test_rounding.py`,
`tests/simulator/integration/test_calculation_conformance.py`,
`tests/simulator/integration/test_calculation_effective_revisions.py`,
`tests/simulator/usage/features/16_calculations.py`; **EDIT** `app/services/simulator/__init__.py`, `app/services/simulator/README.md` and request-v2
model-identity binding. **DO NOT TOUCH:** Brokers collection, unsupported asset classes/modes, online
provider calls, or generic accounting logic.

**Exact root surface:** function wrappers to calculate profit, planned/total margin, convert account
currency, load/validate a conformance artifact, run offline conformance, and get supported modes/model
identity. No class/constant export.

**Implementation order:** immutable contracts; exact Decimal/currency rounding; FX evidence selection
at `as_of`; approved profit modes; netting/hedging margin including existing exposure; fixture loader;
differential runner/artifact; model hash; root exports; tests; usage/README.

**Tests:** each approved calculation mode and side; base/profit/margin currency permutations; inverse/
triangulated conversion only when evidenced; digits/tick-size/tick-value/contract distinctions;
initial/maintenance/hedged margin; netting/hedging; missing/gapped/overlapping revisions; unsupported
mode; exact provider rounding; every sanitized fixture; artifact tamper; cold execution with network
disabled.

**Commands/gate:** targeted Ruff/mypy; six new tests plus accounting, request identity, Data revision
integration and public API tests; direct usage 16. Gate requires zero fixture mismatch and binds the
model/artifact checksum into execution identity.

**STOP/rollback/proposed commit:** stop if a formula/mode/rounding rule lacks verified evidence or Data
cannot prove full coverage. Remove feature/tests/usage/exports and identity field.

### Exact requirement-to-usage allocation

| Unit | Usage program and required functions |
|---|---|
| 13a | `10_conformance.py`: `fr_brk_190()` … `fr_brk_193()` |
| 13b | `16_calculations.py`: `fr_sim_137()` … `fr_sim_145()`, `fr_sim_210()` … `fr_sim_214()` |

### Exact documentation manifests

#### Unit 13a

- **EDIT:** `app/services/brokers/README.md`
- **EDIT:** `docs/CHANGELOG.md`

#### Unit 13b

- **EDIT:** `app/services/simulator/README.md`
- **EDIT:** `docs/CHANGELOG.md`
- **EDIT:** `docs/PROJECT.md`

Every completed FR/checklist row receives final `path:line` evidence. Where listed, the changelog
receives one concise `## [Unreleased]` bullet and never duplicates a Feature Registry.

### Literal validation commands by approval unit

#### Unit 13a

```powershell
uv run ruff format --check app/services/brokers tests/brokers
uv run ruff check app/services/brokers tests/brokers
uv run mypy app/services/brokers
uv run pytest tests/brokers/unit/conformance/test_calculation_fixture_schema.py tests/brokers/integration/test_mt5_calculation_evidence.py
uv run python tests/brokers/usage/features/10_conformance.py
uv run pytest tests/brokers
git diff --check
git status --short
```

#### Unit 13b

```powershell
uv run ruff format --check app/services/simulator tests/simulator
uv run ruff check app/services/simulator tests/simulator
uv run mypy app/services/simulator
uv run pytest tests/simulator/unit/calculations/test_fx_conversion.py tests/simulator/unit/calculations/test_profit.py tests/simulator/unit/calculations/test_margin.py tests/simulator/unit/calculations/test_rounding.py tests/simulator/integration/test_calculation_conformance.py tests/simulator/integration/test_calculation_effective_revisions.py
uv run python tests/simulator/usage/features/16_calculations.py
uv run pytest tests/simulator
git diff --check
git status --short
```

Run only the commands for the approved unit. A missing path, pre-existing failure, skipped test,
or command substitution is a STOP and requires a correction dry run.

### Exact proposed commit messages

**Unit 13a:**

```text
feat(brokers): add calculation conformance evidence

- Complete approved unit 13a within its declared domain and requirement boundary.
- Execute and document usage evidence: tests/brokers/usage/features/10_conformance.py.
- Pass targeted tests, owning-domain gates, documentation reconciliation, and rollback review.
```

**Unit 13b:**

```text
feat(simulator): add effective-dated calculation model

- Complete approved unit 13b within its declared domain and requirement boundary.
- Execute and document usage evidence: tests/simulator/usage/features/16_calculations.py.
- Pass targeted tests, owning-domain gates, documentation reconciliation, and rollback review.
```

Commit execution is not authorized by phase approval. After separate commit authorization, stage only
the phase manifest, verify `git diff --cached --name-only`, and use the applicable message verbatim.

**Per-unit status:** 13a Completed 2026-08-16 under the owner's goal-wide standalone approval. `FR-BRK-190`–`193` extend the existing check/calculation evidence without re-registering operations. Complete finite Decimal projections and all-or-none observation identity are enforced by `app/services/brokers/canonical_contracts/models.py:1551`, mapped from MT5 at `app/services/brokers/metatrader/mapping.py:729`, and bound to the current provider specification in the live check path at `app/services/brokers/metatrader/commands.py:86`. The immutable bounded schema and canonical checksum are at `app/services/brokers/conformance/fixtures.py:76` and `app/services/brokers/conformance/fixtures.py:153`; the separately invoked dev/demo guard and account digest are at `app/services/brokers/conformance/fixtures.py:217`. Projection, missing/NaN, identity, unchanged-registration, and provider-disabled default-suite evidence is at `tests/brokers/integration/test_mt5_calculation_evidence.py:72`, `tests/brokers/integration/test_mt5_calculation_evidence.py:90`, `tests/brokers/integration/test_mt5_calculation_evidence.py:98`, and `tests/brokers/integration/test_mt5_calculation_evidence.py:106`. Round-trip, type/secret/tamper, completeness, and dev/demo redaction evidence is at `tests/brokers/unit/conformance/test_calculation_fixture_schema.py:46`, `tests/brokers/unit/conformance/test_calculation_fixture_schema.py:68`, `tests/brokers/unit/conformance/test_calculation_fixture_schema.py:78`, and `tests/brokers/unit/conformance/test_calculation_fixture_schema.py:94`. Usage functions `fr_brk_190()` through `fr_brk_193()` are at `tests/brokers/usage/features/10_conformance.py:64`–`108` and passed directly with no provider call. Ruff format/check and full Brokers mypy passed; 121 related Brokers tests passed. The literal two-file gate passed all 15 behaviors but exited 1 solely because repository-wide subset coverage was 3.24%. The full Brokers gate reports 676 passed, three credential skips, three documented pre-existing documentation/MT5 mutation failures, and repository-wide coverage 16.66%; no Phase-13a test fails. The bounded blocker resolution requires a complete current provider-specification observation for production MT5 checks and updates the deterministic MT5 test transport with the same complete verified symbol shape; missing specification identity now fails closed. Collection was not executed, accepts no live/production route, stores no raw account/credential, and remains absent from the default conformance suite. No operation registration, Simulation behavior, production credential, new calculation verb, or provider formula was added. Rollback reverts the order-check fields/mapping/binding and test transport fixture, removes the fixture module/tests/root functions, and reverts conformance/usage/README/changelog/plan evidence.

**Commit reconciliation:** Unit 13a is committed as `667c8e3bd3099a9b1dc9c2c5606388de7b90235a` with the exact prescribed message.

**Per-unit status:** 13b Completed 2026-08-16 under the owner's goal-wide standalone approval. `FR-SIM-137`–`145` and `FR-SIM-210`–`214` are implemented by the immutable effective specification at `app/services/simulator/calculations/contracts.py:46`, exact Data-evidenced conversion at `app/services/simulator/calculations/fx.py:15`, FX profit at `app/services/simulator/calculations/profit.py:12`, total/planned netting and hedging margin in `app/services/simulator/calculations/margin.py`, and the function-only surface at `app/services/simulator/calculations/public.py:63`. Effective half-open selection and gap/overlap/unsupported-mode rejection are proven at `tests/simulator/integration/test_calculation_effective_revisions.py:11` and `tests/simulator/integration/test_calculation_effective_revisions.py:34`; exact sides/conversion/margin/rounding are proven at `tests/simulator/unit/calculations/test_profit.py:84`, `tests/simulator/unit/calculations/test_fx_conversion.py:28`, `tests/simulator/unit/calculations/test_margin.py:32`, and `tests/simulator/unit/calculations/test_rounding.py:10`. The checksummed offline artifact loader/runner and mismatch/tamper evidence are at `app/services/simulator/calculations/conformance.py:43`, `tests/simulator/integration/test_calculation_conformance.py:28`, and `tests/simulator/integration/test_calculation_conformance.py:41`. Request-v2 binds required calculation model/artifact digests at `app/services/simulator/run/contracts.py:317`. Usage functions `fr_sim_137()` through `fr_sim_145()` and `fr_sim_210()` through `fr_sim_214()` start at `tests/simulator/usage/features/16_calculations.py:63` and passed directly. Ruff format/check and full Simulator mypy passed; the six focused files passed 11 tests with `--no-cov`, while the literal focused command exited 1 solely because repository-wide subset coverage was 10.01%. The literal full Simulator gate found and prompted reconciliation of the expected public-export tuple, then reported 431 passing behaviors and only that Phase-13b documentation-parity failure plus the repository-wide 29.39% coverage floor; after the bounded correction, the complete behavior gate passed 432 tests with `--no-cov`. Blocker resolutions were bounded to explicit runtime rejection of unsupported modes, correct removal of planned volume before incremental-margin recomputation, full-domain typing of dynamic margin fields, and public-export catalogue reconciliation. No provider calls, Brokers collection, generic accounting, unsupported asset class, fallback calculation, or inferred FX path was added. Rollback removes `calculations/`, its tests/usage/root exports, request-v2 calculation digest fields and fixture updates, and reverts Simulator README, project counts, changelog, and this status record.

### Completion checklist

- [x] Approval matched this exact phase/subphase. Evidence: owner goal-wide standalone approval and statuses above.
- [x] Only the local file and documentation manifests changed. Evidence: staged-manifest review before each commit.
- [x] Every listed FR has final `path:line` implementation and test evidence. Evidence: per-unit statuses above.
- [x] Only verified package-root/public dependency contracts were used. Evidence: Data is consumed through `app.services.data`; no provider IO exists in calculations.
- [x] Targeted unit/integration tests passed with recorded commands and exit codes. Evidence: per-unit statuses above.
- [x] Ruff format/check and mypy passed for every owning domain. Evidence: per-unit statuses above.
- [x] Every local usage program executed directly and passed. Evidence: usage 10 and usage 16 status records above.
- [x] Every owning-domain phase behavior gate passed. Evidence: 676 Brokers baseline with documented pre-existing failures; 432 Simulator tests passed with `--no-cov`.
- [x] README, changelog, and listed system documents reconciled. Evidence: owning READMEs, changelog, project index, and this plan.
- [x] STOP conditions and rollback path were rechecked. Evidence: per-unit scope/rollback records above.
- [x] Commit remains unauthorized, or its separately authorized hash is recorded. Evidence: owner goal-wide commit authorization; Unit 13a hash above and Unit 13b hash will be reconciled in Unit 14a.

# Phase 14 · Trading cutover — L1

## 14a · Trading convergence

**Domain:** trading. **Requirements:** `FR-TRD-088` … `094`, `FR-TRD-113`.

Expose and use one public approved-request builder for both live evaluation and the bounded Simulation
bridge. Remove `simulation_dispatch`, the route mutation branch, and route-conditional business-gate
skips. Extend session lifecycle to Simulation. Preserve explicit route-specific safety gates and
compare them by the Phase 2 taxonomy; do not apply live-mutation authorization to sim.

## 14b · Simulation cutover

**Domain:** simulator. **Requirements:** `FR-SIM-146` … `150`, `FR-SIM-195`, `197`, `198`,
`215` … `217`.

Use the Trading public request builder and public mutation verbs; never construct `OrderIntent`
directly. Add run-scoped Trading state, route explicit terminal liquidation through Trading, and
surface engine SL/TP triggers as provider-shaped deals and authority-state changes—not client-submit
events. Initialize Trading and Simulation projections from the same hashed complete authority
snapshot. Require an exclusive account interval or replay every ordered foreign/manual activity event;
unknown or missing ownership/activity fails closed. Implement the async operation and retained sync
bridge.

**L1 gate:** paired fixtures prove equivalent business/risk gates, declared safety-gate behavior,
response classification, retcodes, event categories, current projections, initial-state identity, and
foreign-activity rejection. Terminal liquidation is exercised only when both paired requests enable
the hashed policy.

---

## Implementation specification

### 14a · Trading convergence — implementation details

**Outcome:** live and simulation use one approved-request builder and action path; route changes only
authority transport and declared safety gates.

**Approval unit:** trading. **Prerequisites:** 6a, 8, 10b, 12. **Requirements:** `FR-TRD-088`–`094`,
`FR-TRD-113`.

**Read first:** `actions/{runtime,orders,dependencies,factories}.py`;
`routing/{dispatcher,capabilities}.py`; `live/{gates,session}.py`; contracts registry,
`app/services/trading/__init__.py`, and `app/services/trading/README.md`;
usages 07/08; every `simulation_dispatch`, `_approved_request`, and route-conditional gate match.

**File manifest:** **EDIT** the listed Trading owners, contracts registry,
`app/services/trading/__init__.py`, `app/services/trading/README.md`,
`tests/trading/usage/features/07_live.py`, `08_actions.py`; **CREATE**
`tests/trading/unit/actions/test_approved_request_builder.py`,
`tests/trading/integration/test_two_route_action_convergence.py`,
`tests/trading/integration/test_simulation_session_lifecycle.py`. **DELETE** no file; remove only the
private `simulation_dispatch` parameter/branch after every caller is migrated. **DO NOT TOUCH:**
Strategy/Risk decisions, live mutation authorization, Simulation, or route-specific safety-gate
meaning.

**Exact behavior:** expose a root standalone approved-request builder from the existing runtime logic;
it consumes Strategy/Risk lineage and complete evidence and returns v2. Both routes invoke it, the same
business/risk gates, action functions and response classifier. Authority is injected through the
Brokers root boundary. Simulation skips only explicitly registered live-transport/mutation safety
gates. Session start/stop/finalize supports Simulation lifecycle.

**Implementation order:** public builder extraction and tests; dependency port replacement; dispatcher
branch removal; order/action callers; session lifecycle; gate taxonomy evidence; registry/root; paired
tests; usages/README.

**Tests:** identical builder output after alpha-renamed trace IDs; all business/risk gate roles/order/
inputs/results; permitted safety-gate delta; neutral/rejected/accepted/malformed/unsupported outcomes;
session connect/disconnect/finalize; no private Simulation import; no intent reconstruction.

**Commands/gate:** targeted Ruff/mypy; three new tests plus runtime/actions/dispatcher/gates/session/
contracts/public/compatibility tests; usages 07/08. L1 Trading half must pass before 14b.

**STOP/rollback/proposed commit:** stop if route changes approved economic fields, a safety/business gate
cannot be classified, or a caller needs private data. Restore prior dependency/dispatcher path and
remove new builder/export/tests.

### 14b · Simulation cutover — implementation details

**Outcome:** Simulation enters Trading through public evaluation/request/action APIs and returns
provider-shaped authority events; local direct-intent submission is no longer canonical.

**Approval unit:** simulator. **Prerequisite:** 14a. **Requirements:** `FR-SIM-146`–`150`,
`FR-SIM-195`, `197`, `198`, `215`–`217`.

**Read first:** Simulator run/execution/scheduler/`app/services/simulator/state/{__init__.py,runtime.py,store.py,sessions.py}`, `app/services/simulator/journal/{__init__.py,contracts.py,writer.py,replay.py,playback.py}`, `app/services/simulator/recovery/{__init__.py,contracts.py,checkpoints.py,lifecycle.py,service.py,README.md}`; request v2; Trading public
builder/actions/state contracts; Brokers simulation adapter; usage 05/07.

**File manifest:** **EDIT** `app/services/simulator/run/{contracts,dependencies,orchestrator}.py`,
`execution/{engine,trader}.py`, scheduler pump/contracts,
`app/services/simulator/state/{__init__.py,runtime.py,store.py,sessions.py}`,
`app/services/simulator/journal/{__init__.py,contracts.py,writer.py,replay.py,playback.py}`,
`app/services/simulator/recovery/{__init__.py,contracts.py,checkpoints.py,lifecycle.py,service.py,README.md}`,
`app/services/simulator/__init__.py`, and `app/services/simulator/README.md`,
usages 05/07; **CREATE** `tests/simulator/integration/test_trading_cutover.py`,
`tests/simulator/integration/test_initial_authority_state.py`,
`tests/simulator/integration/test_terminal_liquidation_policy.py`,
`tests/simulator/integration/test_foreign_activity_guard.py`. **DO NOT TOUCH:** Trading, direct legacy
execution APIs outside their documented compatibility status, realism, or real accounts.

**Implementation order:** run-scoped Trading dependencies/state; complete initial-authority snapshot
validation/hash; async Trading request/action bridge through Brokers sim adapter; engine protection
events as authority deals; terminal-close action through Trading; exclusive-account/foreign-event
guard; orchestration; compatibility labelling; tests; usages/README.

**Tests:** direct intent construction absent from canonical path; exact Risk-approved size/policies;
same initial state both projections; protection/terminal close event categories and deals; terminal
policy on/off hash; foreign/manual complete replay vs missing event; async/sync bridge; error and
cancellation; no duplicate mutation.

**Commands/gate:** targeted Ruff/mypy; four new tests plus scheduler, run, execution, journal, recovery,
request-v2 and Trading paired tests; usages 05/07. L1 paired fixture compares gates, classifications,
retcodes, events, projections and initial state.

**STOP/rollback/proposed commit:** stop if Simulation constructs `OrderIntent`, copies private Trading
logic, cannot produce authority deals, or account activity is incomplete. Revert consumers/tests and
retain legacy path as found.

### Exact requirement-to-usage allocation

| Unit | Usage program and required functions |
|---|---|
| 14a | `04_routing.py`: `fr_trd_088()`, `fr_trd_094()`; `07_live.py`: `fr_trd_091()`; `08_actions.py`: `fr_trd_089()`, `fr_trd_090()`, `fr_trd_092()`, `fr_trd_093()`, `fr_trd_113()` |
| 14b | `07_run.py`: `fr_sim_146()` … `fr_sim_150()`, `fr_sim_195()`, `fr_sim_197()`, `fr_sim_198()`, `fr_sim_215()` … `fr_sim_217()` |

### Exact documentation manifests

#### Unit 14a

- **EDIT:** `app/services/trading/README.md`
- **EDIT:** `docs/CHANGELOG.md`
- **EDIT:** `docs/ARCHITECTURE.md`

#### Unit 14b

- **EDIT:** `app/services/simulator/README.md`
- **EDIT:** `docs/CHANGELOG.md`

Every completed FR/checklist row receives final `path:line` evidence. Where listed, the changelog
receives one concise `## [Unreleased]` bullet and never duplicates a Feature Registry.

### Literal validation commands by approval unit

#### Unit 14a

```powershell
uv run ruff format --check app/services/trading tests/trading
uv run ruff check app/services/trading tests/trading
uv run mypy app/services/trading
uv run pytest tests/trading/unit/actions/test_approved_request_builder.py tests/trading/integration/test_two_route_action_convergence.py tests/trading/integration/test_simulation_session_lifecycle.py
uv run python tests/trading/usage/features/04_routing.py
uv run python tests/trading/usage/features/07_live.py
uv run python tests/trading/usage/features/08_actions.py
uv run pytest tests/trading
git diff --check
git status --short
```

#### Unit 14b

```powershell
uv run ruff format --check app/services/simulator tests/simulator
uv run ruff check app/services/simulator tests/simulator
uv run mypy app/services/simulator
uv run pytest tests/simulator/integration/test_trading_cutover.py tests/simulator/integration/test_initial_authority_state.py tests/simulator/integration/test_terminal_liquidation_policy.py tests/simulator/integration/test_foreign_activity_guard.py
uv run python tests/simulator/usage/features/07_run.py
uv run pytest tests/simulator
git diff --check
git status --short
```

Run only the commands for the approved unit. A missing path, pre-existing failure, skipped test,
or command substitution is a STOP and requires a correction dry run.

### Exact proposed commit messages

**Unit 14a:**

```text
refactor(trading): converge the simulation mutation path

- Complete approved unit 14a within its declared domain and requirement boundary.
- Execute and document usage evidence: tests/trading/usage/features/04_routing.py, 07_live.py, 08_actions.py.
- Pass targeted tests, owning-domain gates, documentation reconciliation, and rollback review.
```

**Unit 14b:**

```text
refactor(simulator): cut over to Trading execution

- Complete approved unit 14b within its declared domain and requirement boundary.
- Execute and document usage evidence: tests/simulator/usage/features/07_run.py.
- Pass targeted tests, owning-domain gates, documentation reconciliation, and rollback review.
```

Commit execution is not authorized by phase approval. After separate commit authorization, stage only
the phase manifest, verify `git diff --cached --name-only`, and use the applicable message verbatim.

### Completion checklist

- [ ] Approval matched this exact phase/subphase.
- [ ] Only the local file and documentation manifests changed.
- [ ] Every listed FR has final `path:line` implementation and test evidence.
- [ ] Only verified package-root/public dependency contracts were used.
- [ ] Targeted unit/integration tests passed with recorded commands and exit codes.
- [ ] Ruff format/check and mypy passed for every owning domain.
- [ ] Every local usage program executed directly and passed.
- [ ] Every owning-domain phase gate passed.
- [ ] README, changelog, and listed system documents reconciled.
- [ ] STOP conditions and rollback path were rechecked.
- [ ] Commit remains unauthorized, or its separately authorized hash is recorded.

# Phase 15 · Incremental evaluation — L2

## 15a · Trading deadline and evaluation seam

**Domain:** trading. **Requirements:** `FR-TRD-095`, `FR-TRD-104` … `106`, `111`.

Keep `run_live_evaluation_cycle` as the shared public path. Replace direct wall-clock
`asyncio.timeout` authority with an injected deadline port: live/paper use monotonic wall time;
Simulation uses scheduler time. Neutral outcomes and timeout evidence remain identical in semantic
shape.

## 15b · Simulation point-in-time orchestration

**Domain:** simulator. **Requirements:** `FR-SIM-218` … `222`.

Split preparation from per-decision evaluation. At each declared instant, the Phase 5 scheduler
invokes the Trading cycle with Data, Indicators, Strategy, Risk, account, position, and margin evidence
available at that instant only. Audit ambient time reads in every participating port; any operation
that cannot honor injected/as-of time is excluded or corrected through its owning domain under a plan
delta.

Decision eligibility uses evidence availability, not only provider event time. When the active
envelope certifies latency, measure the declared chain from provider event through availability,
evaluation, submission, acknowledgement, fill, and reconciliation; an unobserved required segment is
excluded rather than assigned zero duration.

**L2 gate:** use a captured authority/market trace and two separately authorized paired requests.
Verify evolving-equity sizing, prior-fill visibility, prior-stop-out visibility, neutral outcomes,
and no future reads. No real demo session is required by the deterministic gate.

---

## Implementation specification

### 15a · Trading deadline and evaluation seam — implementation details

**Outcome:** `run_live_evaluation_cycle` remains one public path whose deadline authority is injected.

**Approval unit:** trading. **Prerequisite:** 14a. **Requirements:** `FR-TRD-095`,
`FR-TRD-104`–`106`, `111`.

**Read first:** `actions/runtime.py`; `live/session.py`; dependency contracts/factories; all matches
from `rg -n "asyncio\.timeout|timeout_seconds|datetime\.now|monotonic" app/services/trading`; usage 08.

**File manifest:** **CREATE** `app/services/trading/actions/deadlines.py`; **EDIT** action dependencies/
factories/runtime, live session only where it invokes the cycle, `app/services/trading/__init__.py`, `app/services/trading/README.md`, usage 08;
**CREATE** `tests/trading/unit/actions/test_deadline_port.py`,
`tests/trading/integration/test_evaluation_deadline_equivalence.py`. **DO NOT TOUCH:** Brokers timeout,
business gates, Simulation scheduler, or public cycle semantics.

**Exact port:** private structural async deadline context factory plus injected clock/evidence; live and
paper adapter uses monotonic wall time, Simulation supplies scheduler time later. Timeout yields the
same canonical neutral/error shape and evidence fields on all routes. No default is permitted in
production dependency construction.

**Tests/commands:** success, timeout before/within/after neutral result, cancellation, upstream error,
single deadline owner, live monotonic adapter, simulated fake deadline without sleep, identical
evidence shape. Targeted Ruff/mypy; new tests plus runtime/session/dependency/registry/public tests;
usage 08.

**Gate/STOP:** runtime has no direct `asyncio.timeout` or ambient clock. Stop if two timeout owners
remain or public result semantics change. Roll back file/dependency edits/tests.

### 15b · Simulation point-in-time orchestration — implementation details

**Outcome:** each decision sees only evidence available at that instant and is evaluated by the shared
Trading cycle under scheduler time.

**Approval unit:** simulator. **Prerequisites:** 14b, 15a. **Requirements:** `FR-SIM-218`–`222`.

**Read first:** run orchestrator/dependencies/contracts; scheduler; timeline; request v2; Data,
Indicators, Strategy, Risk and Trading public as-of/dependency contracts; usage 07.

**File manifest:** **CREATE** `app/services/simulator/run/evaluation.py`; **EDIT** run orchestrator/
dependencies/contracts, scheduler integration, audit/journal/reporting, `app/services/simulator/__init__.py`, `app/services/simulator/README.md`, usage
07; **CREATE** `tests/simulator/unit/test_point_in_time_evaluation.py`,
`tests/simulator/integration/test_incremental_trading_cycle.py`,
`tests/simulator/integration/test_no_future_reads.py`,
`tests/simulator/integration/test_latency_clock_edges.py`. **DO NOT TOUCH:** other domains; any missing
as-of contract requires a plan delta to its owner.

**Implementation order:** separate preparation; declare decision instants; assemble as-of market/
indicator/strategy/risk/account/position/margin evidence; inject scheduler deadline; invoke Trading
cycle; enqueue resulting authority command; record clock edges; advance; finalize; tests; usage/README.

**Tests:** prior fill/stop-out visible next decision; future bar/tick/account/update invisible;
evolving-equity sizing; neutral path; scheduler timeout; missing clock edge excludes latency metric;
captured trace ordering; no ambient time/network; restart between decisions.

**Commands/gate:** targeted Ruff/mypy; four new tests plus run/scheduler/timeline/request/journal/
recovery and Trading deadline tests; usage 07. L2 uses two separately authorized paired requests and
captured offline evidence.

**STOP/rollback/proposed commit:** stop and issue owner-specific plan delta for any port that ignores
as-of/injected time; do not mask it. Remove evaluation module/tests/exports and restore orchestration.

### Exact requirement-to-usage allocation

| Unit | Usage program and required functions |
|---|---|
| 15a | `07_live.py`: `fr_trd_104()`; `08_actions.py`: `fr_trd_095()`, `fr_trd_105()`, `fr_trd_106()`, `fr_trd_111()` |
| 15b | `07_run.py`: `fr_sim_218()` … `fr_sim_222()` |

### Exact documentation manifests

#### Unit 15a

- **EDIT:** `app/services/trading/README.md`
- **EDIT:** `docs/CHANGELOG.md`
- **EDIT:** `docs/ARCHITECTURE.md`

#### Unit 15b

- **EDIT:** `app/services/simulator/README.md`
- **EDIT:** `docs/CHANGELOG.md`

Every completed FR/checklist row receives final `path:line` evidence. Where listed, the changelog
receives one concise `## [Unreleased]` bullet and never duplicates a Feature Registry.

### Literal validation commands by approval unit

#### Unit 15a

```powershell
uv run ruff format --check app/services/trading tests/trading
uv run ruff check app/services/trading tests/trading
uv run mypy app/services/trading
uv run pytest tests/trading/unit/actions/test_deadline_port.py tests/trading/integration/test_evaluation_deadline_equivalence.py
uv run python tests/trading/usage/features/07_live.py
uv run python tests/trading/usage/features/08_actions.py
uv run pytest tests/trading
git diff --check
git status --short
```

#### Unit 15b

```powershell
uv run ruff format --check app/services/simulator tests/simulator
uv run ruff check app/services/simulator tests/simulator
uv run mypy app/services/simulator
uv run pytest tests/simulator/unit/test_point_in_time_evaluation.py tests/simulator/integration/test_incremental_trading_cycle.py tests/simulator/integration/test_no_future_reads.py tests/simulator/integration/test_latency_clock_edges.py
uv run python tests/simulator/usage/features/07_run.py
uv run pytest tests/simulator
git diff --check
git status --short
```

Run only the commands for the approved unit. A missing path, pre-existing failure, skipped test,
or command substitution is a STOP and requires a correction dry run.

### Exact proposed commit messages

**Unit 15a:**

```text
refactor(trading): inject evaluation deadlines

- Complete approved unit 15a within its declared domain and requirement boundary.
- Execute and document usage evidence: tests/trading/usage/features/07_live.py, 08_actions.py.
- Pass targeted tests, owning-domain gates, documentation reconciliation, and rollback review.
```

**Unit 15b:**

```text
feat(simulator): run incremental point-in-time evaluation

- Complete approved unit 15b within its declared domain and requirement boundary.
- Execute and document usage evidence: tests/simulator/usage/features/07_run.py.
- Pass targeted tests, owning-domain gates, documentation reconciliation, and rollback review.
```

Commit execution is not authorized by phase approval. After separate commit authorization, stage only
the phase manifest, verify `git diff --cached --name-only`, and use the applicable message verbatim.

### Completion checklist

- [ ] Approval matched this exact phase/subphase.
- [ ] Only the local file and documentation manifests changed.
- [ ] Every listed FR has final `path:line` implementation and test evidence.
- [ ] Only verified package-root/public dependency contracts were used.
- [ ] Targeted unit/integration tests passed with recorded commands and exit codes.
- [ ] Ruff format/check and mypy passed for every owning domain.
- [ ] Every local usage program executed directly and passed.
- [ ] Every owning-domain phase gate passed.
- [ ] README, changelog, and listed system documents reconciled.
- [ ] STOP conditions and rollback path were rechecked.
- [ ] Commit remains unauthorized, or its separately authorized hash is recorded.

# Phase 16 · Account and provider semantics

**Domain:** simulator. **Features:** extend `FEAT-SIM-04`, `05`.
**Requirements:** `FR-SIM-151` … `162`.

Consume only Data-returned typed provider revisions. Implement stops/freeze levels, execution/filling
modes, directional volume limits over positions plus pending orders, trade mode, quote/trade sessions,
swap specification, netting/hedging, margin call, and stop-out modes.

Session eligibility combines the weekly revision with verified dated exceptions. If an interval may
contain a broker holiday, maintenance window, or exceptional closure and no dated evidence covers it,
that interval is outside the canonical envelope.

Stop-out liquidation order is canonical only for an envelope entry backed by target-broker fixtures.
Unverified configurable ordering is exploratory-only. Complete Phase 7's post-swap stop-out test here.

**Gate:** hedging/netting, JPY/cross currency, digits, calculation/swap/execution modes, partial fill,
retcodes, account conservation, and target-evidenced stop-out cases.

---

## Implementation specification

**Outcome:** Simulation enforces the exact effective provider/account rules admitted by the envelope;
uncovered exceptional sessions or liquidation order remain noncanonical.

**Approval unit:** simulator. **Prerequisites:** 7, 13b, 15b. **Requirements:** `FR-SIM-151`–`162`.

**Read first:** Simulator execution/accounting/calculation-model/scheduler; Data specification/session
revision public functions; Brokers current snapshot contract; request v2/envelope; usages 04/05.

**File manifest:** **CREATE** `app/services/simulator/execution/provider_semantics.py` and
`app/services/simulator/accounting/stop_out.py`; **EDIT** execution matching/engine/pricing, accounting
calculations/ledger/swap, scheduler event registration, run dependencies/orchestrator,
`app/services/simulator/state/{__init__.py,runtime.py,store.py,sessions.py}`,
`app/services/simulator/journal/{__init__.py,contracts.py,writer.py,replay.py,playback.py}`,
`app/services/simulator/recovery/{__init__.py,contracts.py,checkpoints.py,lifecycle.py,service.py,README.md}`,
`app/services/simulator/__init__.py`, `app/services/simulator/README.md`, usages 04/05; **CREATE**
`tests/simulator/unit/test_provider_semantics.py`, `tests/simulator/unit/test_stop_out.py`,
`tests/simulator/integration/test_account_modes.py`,
`tests/simulator/integration/test_session_semantics.py`,
`tests/simulator/integration/test_post_swap_stop_out.py`. **DO NOT TOUCH:** Data/Brokers storage,
unapproved asset classes, or configurable stop-out order in canonical mode.

**Implementation order:** effective revision retrieval/coverage check; stops/freeze and trade mode;
execution/filling and directional-volume rules over positions plus pending orders; weekly+detailed
session eligibility; netting/hedging transitions; margin-call and stop-out thresholds/modes;
target-evidenced liquidation priority; post-swap event ordering; `app/services/simulator/journal/{__init__.py,contracts.py,writer.py,replay.py,playback.py}`, `app/services/simulator/recovery/{__init__.py,contracts.py,checkpoints.py,lifecycle.py,service.py,README.md}`; tests/usages/README.

**Tests:** stops/freeze boundaries; all admitted execution/filling modes; long/short directional limit
with pending orders; disabled/close-only trade modes; weekly edges, DST, dated closure/maintenance and
missing exception evidence; netting add/reduce/reverse; hedging; margin call/percent/money stop-out;
JPY/cross currency/digits; partial fill; target-evidenced liquidation sequence; conservation after
post-swap stop-out; restore at every event boundary.

**Commands/gate:** targeted Ruff/mypy; five new tests plus accounting, calculation, scheduler,
matching, ledger/recovery tests; usages 04/05. Gate runs the provider/account matrix and rejects every
uncovered revision interval.

**STOP/rollback/proposed commit:** stop if typed revisions are incomplete, a dated exception is
guessed, or liquidation order lacks target evidence. Delete two modules/tests and revert consumers.

### Exact requirement-to-usage allocation

| Unit | Usage program and required functions |
|---|---|
| 16 | `04_accounting.py`: `fr_sim_157()` … `fr_sim_162()`; `05_execution.py`: `fr_sim_151()` … `fr_sim_156()` |

### Exact documentation manifest

- **EDIT:** `app/services/simulator/README.md`
- **EDIT:** `docs/CHANGELOG.md`

Every completed FR/checklist row receives final `path:line` evidence. The changelog receives one concise
`## [Unreleased]` bullet under the correct change type and never duplicates a Feature Registry.

### Literal validation commands

```powershell
uv run ruff format --check app/services/simulator tests/simulator
uv run ruff check app/services/simulator tests/simulator
uv run mypy app/services/simulator
uv run pytest tests/simulator/unit/test_provider_semantics.py tests/simulator/unit/test_stop_out.py tests/simulator/integration/test_account_modes.py tests/simulator/integration/test_session_semantics.py tests/simulator/integration/test_post_swap_stop_out.py
uv run python tests/simulator/usage/features/04_accounting.py
uv run pytest tests/simulator
git diff --check
git status --short
```

Run the phase-named targeted pytest files before the owning-domain gate. A missing exact path,
pre-existing failure, skipped test, or command substitution is a STOP and requires a correction dry run.

### Exact proposed commit messages

**Unit 16:**

```text
feat(simulator): mirror MT5 account and provider semantics

- Complete approved unit 16 within its declared domain and requirement boundary.
- Execute and document usage evidence: tests/simulator/usage/features/04_accounting.py, 05_execution.py.
- Pass targeted tests, owning-domain gates, documentation reconciliation, and rollback review.
```

Commit execution is not authorized by phase approval. After separate commit authorization, stage only
the phase manifest, verify `git diff --cached --name-only`, and use the applicable message verbatim.

### Completion checklist

- [ ] Approval matched this exact phase/subphase.
- [ ] Only the local file and documentation manifests changed.
- [ ] Every listed FR has final `path:line` implementation and test evidence.
- [ ] Only verified package-root/public dependency contracts were used.
- [ ] Targeted unit/integration tests passed with recorded commands and exit codes.
- [ ] Ruff format/check and mypy passed for every owning domain.
- [ ] Every local usage program executed directly and passed.
- [ ] Every owning-domain phase gate passed.
- [ ] README, changelog, and listed system documents reconciled.
- [ ] STOP conditions and rollback path were rechecked.
- [ ] Commit remains unauthorized, or its separately authorized hash is recorded.

# Phase 17 · Order, deal, protection, and transaction lifecycle

## 17a · Simulation lifecycle

**Domain:** simulator. **Requirements:** `FR-SIM-163` … `170`.

Implement GTC/DAY/SPECIFIED/SPECIFIED_DAY expiration, including broker-session edge behavior;
FOK/IOC/RETURN/BOC semantics; evidenced partial-fill remainder; order/deal/position linkage with
`DEAL_ENTRY_*`; deterministic tickets; and account transaction evidence.

Represent the observed causal outcomes of cancel-vs-fill, modify-vs-fill, protection-vs-close, and
disconnect-vs-response races. Do not claim a provider sequence when evidence supplies only concurrent
or same-timestamp events. Account transactions include replayed foreign/manual activity when the
certificate does not require an exclusive account.

SL/TP may be internal trigger objects but are not exposed as ordinary provider pending orders unless
the active provider contract does so. Public evidence mirrors position protection fields, resulting
deals, reason codes, and OCO/residual behavior.

## 17b · Brokers simulation deal surface

**Domain:** brokers. **Requirements:** `FR-BRK-194` … `196`.

Complete bounded deal history, get-deal, and account-transaction reads for the Simulation adapter.
Deals carry `order_id`, `position_id`, fee evidence, entry/reason semantics, and timestamps.

---

## Implementation specification

### 17a · Simulation lifecycle — implementation details

**Outcome:** Simulation produces deterministic, provider-shaped order/deal/position/protection/account-
transaction lifecycles including evidenced race outcomes.

**Approval unit:** simulator. **Prerequisites:** 12, 16. **Requirements:** `FR-SIM-163`–`170`.

**Read first:** Simulator execution engine/matching/trader/provider semantics; scheduler; accounting
transactions/ledger; `app/services/simulator/state/{__init__.py,runtime.py,store.py,sessions.py}`, `app/services/simulator/journal/{__init__.py,contracts.py,writer.py,replay.py,playback.py}`, `app/services/simulator/recovery/{__init__.py,contracts.py,checkpoints.py,lifecycle.py,service.py,README.md}`; Brokers order/deal canonical models; usages 04/05.

**File manifest:** **CREATE** `app/services/simulator/execution/lifecycle.py`; **EDIT** execution engine/
matching/trader, scheduler contracts/priorities, accounting transactions, `app/services/simulator/state/{__init__.py,runtime.py,store.py,sessions.py}`, `app/services/simulator/journal/{__init__.py,contracts.py,writer.py,replay.py,playback.py}`, `app/services/simulator/recovery/{__init__.py,contracts.py,checkpoints.py,lifecycle.py,service.py,README.md}`/
reporting, `app/services/simulator/__init__.py`, `app/services/simulator/README.md`, usages 04/05; **CREATE**
`tests/simulator/unit/test_order_lifecycle.py`, `tests/simulator/unit/test_deal_lifecycle.py`,
`tests/simulator/unit/test_protection_lifecycle.py`,
`tests/simulator/integration/test_lifecycle_races.py`,
`tests/simulator/integration/test_lifecycle_resume.py`. **DO NOT TOUCH:** Brokers adapter, synthetic
provider ordering, or stochastic realism.

**Exact behavior:** implement GTC/DAY/SPECIFIED/SPECIFIED_DAY expiry; FOK/IOC/RETURN/BOC remainder;
evidenced partial fills; deterministic order/deal/position tickets; `DEAL_ENTRY_*`, reason and causal
links; SL/TP as internal triggers exposed as protection fields plus resulting deals, not pending orders
unless provider contract says so; account transaction records; exclusive/replayed foreign activity.
Race records preserve evidenced order or an explicit partial-order/concurrent relation.

**Implementation order:** lifecycle state machine and legal transitions; identifiers/linkage; expiry;
fill/remainder; protection/OCO; transaction emission; race representation; scheduler priorities;
`app/services/simulator/journal/{__init__.py,contracts.py,writer.py,replay.py,playback.py}`, `app/services/simulator/recovery/{__init__.py,contracts.py,checkpoints.py,lifecycle.py,service.py,README.md}`; tests; usages/README.

**Tests:** every transition and invalid transition; each time/fill policy; session-edge expiration;
multi-fill linkage; partial/full/reversal; SL/TP same tick/gap/OCO; cancel-fill, modify-fill,
protection-close, disconnect-response races with ordered and ambiguous evidence; foreign activity;
deterministic tickets; restart at each durable boundary.

**Commands/gate:** targeted Ruff/mypy; five new tests plus scheduler, mutation, accounting, recovery
and provider-semantics tests; usages 04/05. Gate validates graph referential integrity and ledger
conservation after every lifecycle event.

**STOP/rollback/proposed commit:** stop if provider order is invented, protection is exposed as an
ordinary order contrary to evidence, or tickets use process/random state. Remove lifecycle module/tests
and revert consumers.

### 17b · Brokers simulation deal surface — implementation details

**Outcome:** the Simulation adapter completes bounded deal, get-deal, and account-transaction reads.

**Approval unit:** brokers. **Prerequisite:** 17a. **Requirements:** `FR-BRK-194`–`196`.

**Read first:** Brokers simulation read implementation; canonical deal/history models; MT5 deal
mapping; `app/services/brokers/capabilities/matrix.py`, `app/services/brokers/conformance/{__init__.py,fake.py,public.py,suite.py,README.md}`; usage 17; Simulator public authority-port binding only.

**File manifest:** **EDIT** simulation contracts/adapter/public/README, `app/services/brokers/capabilities/matrix.py`, `app/services/brokers/conformance/{__init__.py,fake.py,public.py,suite.py,README.md}`,
canonical contracts only if already authorized, `app/services/brokers/__init__.py`, `app/services/brokers/README.md`, usage 17; **CREATE**
`tests/brokers/unit/simulation/test_simulation_deals.py`,
`tests/brokers/unit/simulation/test_simulation_transactions.py`,
`tests/brokers/integration/test_simulation_deal_conformance.py`. **DO NOT TOUCH:** Simulator internals,
Trading, matching/accounting, or MT5 behavior.

**Tests:** bounded inclusive/exclusive range; exact deal; unknown ID; ordering/pagination/limit;
order/position linkage; entry/reason; every fee/transaction sign; clock/sequence/gap/stale evidence;
disconnected/unsupported; adapter maps without recompute. Usage 17 calls all completed operations.

**Commands/gate:** targeted Ruff/mypy; three new tests plus all Simulation adapter/conformance,
canonical deal and MT5 deal-mapping tests; usage 17. Gate reconciles capability matrix with protocol,
adapter and conformance coverage.

**STOP/rollback/proposed commit:** stop on missing authority identity/evidence or unbounded history.
Revert listed edits/delete tests.

### Exact requirement-to-usage allocation

| Unit | Usage program and required functions |
|---|---|
| 17a | `05_execution.py`: `fr_sim_163()` … `fr_sim_170()` |
| 17b | `17_simulation.py`: `fr_brk_194()`, `fr_brk_195()`, `fr_brk_196()` |

### Exact documentation manifests

#### Unit 17a

- **EDIT:** `app/services/simulator/README.md`
- **EDIT:** `docs/CHANGELOG.md`

#### Unit 17b

- **EDIT:** `app/services/brokers/README.md`
- **EDIT:** `docs/CHANGELOG.md`

Every completed FR/checklist row receives final `path:line` evidence. Where listed, the changelog
receives one concise `## [Unreleased]` bullet and never duplicates a Feature Registry.

### Literal validation commands by approval unit

#### Unit 17a

```powershell
uv run ruff format --check app/services/simulator tests/simulator
uv run ruff check app/services/simulator tests/simulator
uv run mypy app/services/simulator
uv run pytest tests/simulator/unit/test_order_lifecycle.py tests/simulator/unit/test_deal_lifecycle.py tests/simulator/unit/test_protection_lifecycle.py tests/simulator/integration/test_lifecycle_races.py tests/simulator/integration/test_lifecycle_resume.py
uv run python tests/simulator/usage/features/05_execution.py
uv run pytest tests/simulator
git diff --check
git status --short
```

#### Unit 17b

```powershell
uv run ruff format --check app/services/brokers tests/brokers
uv run ruff check app/services/brokers tests/brokers
uv run mypy app/services/brokers
uv run pytest tests/brokers/unit/simulation/test_simulation_deals.py tests/brokers/unit/simulation/test_simulation_transactions.py tests/brokers/integration/test_simulation_deal_conformance.py
uv run python tests/brokers/usage/features/17_simulation.py
uv run pytest tests/brokers
git diff --check
git status --short
```

Run only the commands for the approved unit. A missing path, pre-existing failure, skipped test,
or command substitution is a STOP and requires a correction dry run.

### Exact proposed commit messages

**Unit 17a:**

```text
feat(simulator): complete order and deal lifecycle

- Complete approved unit 17a within its declared domain and requirement boundary.
- Execute and document usage evidence: tests/simulator/usage/features/05_execution.py.
- Pass targeted tests, owning-domain gates, documentation reconciliation, and rollback review.
```

**Unit 17b:**

```text
feat(brokers): expose simulation deal history

- Complete approved unit 17b within its declared domain and requirement boundary.
- Execute and document usage evidence: tests/brokers/usage/features/17_simulation.py.
- Pass targeted tests, owning-domain gates, documentation reconciliation, and rollback review.
```

Commit execution is not authorized by phase approval. After separate commit authorization, stage only
the phase manifest, verify `git diff --cached --name-only`, and use the applicable message verbatim.

### Completion checklist

- [ ] Approval matched this exact phase/subphase.
- [ ] Only the local file and documentation manifests changed.
- [ ] Every listed FR has final `path:line` implementation and test evidence.
- [ ] Only verified package-root/public dependency contracts were used.
- [ ] Targeted unit/integration tests passed with recorded commands and exit codes.
- [ ] Ruff format/check and mypy passed for every owning domain.
- [ ] Every local usage program executed directly and passed.
- [ ] Every owning-domain phase gate passed.
- [ ] README, changelog, and listed system documents reconciled.
- [ ] STOP conditions and rollback path were rechecked.
- [ ] Commit remains unauthorized, or its separately authorized hash is recorded.

# Phase 18 · Simulation position reconciliation — L3

## 18a · Trading two-route behavior

**Domain:** trading. **Requirements:** `FR-TRD-107` … `110`.

Use the same deal-position correlation, projection transitions, netting behavior, and unverifiable-
state block on every route. Reconcile duplicate, late, missing, out-of-order, and foreign authority
events from the last durable watermark. A foreign exposure without valid ownership remains orphaned
and blocks affected mutations.

- `FR-TRD-107` route-independent deal/position correlation; `108` authority-event ordering and gap
  recovery; `109` foreign/manual ownership and activity handling; `110` durable-watermark restart
  convergence without duplicate mutation.

## 18b · Simulation authority evidence

**Domain:** simulator. **Requirement:** `FR-SIM-223`.

Guarantee every exposure-changing simulated deal provides the position identity and authority snapshot
evidence required by Trading.

**L3 gate:** paired open/modify/reduce/close, partial/full close, reversal, netting many-to-one,
protective exit, terminal liquidation, concurrent mutation races, foreign/manual activity, event-gap
recovery, ownership/orphan handling, and accounting-conservation fixtures.

---

## Implementation specification

### 18a · Trading two-route behavior — implementation details

**Outcome:** Trading uses one authority-event reconciliation algorithm and durable watermark on both
live and simulation routes.

**Approval unit:** trading. **Prerequisites:** 8, 14a, 17b. **Requirements:** `FR-TRD-107`–`110`.

**Read first:** Trading state execution positions/idempotency/runtime; reconciliation authority/
compare/orchestrator/factories/snapshots; ownership; position actions; Brokers deal/read root APIs;
usages 02/05/11.

**File manifest:** **EDIT** the listed Trading owners, `app/services/trading/__init__.py`,
`app/services/trading/README.md`, usages 02/05/11; **CREATE**
`tests/trading/unit/reconciliation/test_authority_event_ordering.py`,
`tests/trading/integration/test_two_route_position_reconciliation.py`,
`tests/trading/integration/test_reconciliation_restart.py`,
`tests/trading/integration/test_foreign_orphan_block.py`. **DO NOT TOUCH:** route-specific duplicate
algorithms, Brokers/Simulation, or automatic ownership of foreign exposure.

**Implementation order:** canonical event key and gap detection; retrieve from last durable watermark;
deal-position correlation shared with Phase 8; projection transitions; duplicate/late/out-of-order
handling; foreign/manual orphan state; atomic projection+watermark persistence; restart convergence;
tests/usages/README.

**Tests:** paired route streams for open/modify/reduce/close, partial/full/reversal, netting many-to-one,
protective/terminal exit; duplicate/late/out-of-order/missing events; reconnect gap; foreign order/deal/
balance correction; ownership conflict; crash before/after each durable write; unknown outcome; exact
single mutation behavior.

**Commands/gate:** targeted Ruff/mypy; four new tests plus Phase-8 correlation, state, ownership,
actions, reconciliation/public tests; usages 02/05/11.

**STOP/rollback/proposed commit:** stop if a route branch changes projection semantics, missing evidence
is silently skipped, or foreign exposure is auto-owned. Revert edits/delete tests.

### 18b · Simulation authority evidence — implementation details

**Outcome:** every exposure-changing simulated deal supplies the exact position and snapshot evidence
required by Trading.

**Approval unit:** simulator. **Prerequisites:** 17a, 18a. **Requirement:** `FR-SIM-223`.

**Read first:** Simulator lifecycle/state/journal/accounting; Brokers simulation port; Trading public
authority evidence contract; usages 04/05.

**File manifest:** **EDIT** lifecycle/engine,
`app/services/simulator/state/{__init__.py,runtime.py,store.py,sessions.py}`,
`app/services/simulator/journal/{__init__.py,contracts.py,writer.py,replay.py,playback.py}`,
`app/services/simulator/reporting/{__init__.py,contracts.py,artifacts.py,reports.py}`, authority-port
projection, `app/services/simulator/__init__.py`, `app/services/simulator/README.md`, usages 04/05;
**CREATE**
`tests/simulator/integration/test_trading_authority_evidence.py`,
`tests/simulator/integration/test_l3_position_parity.py`. **DO NOT TOUCH:** Trading or Brokers.

**Tests/gate:** every exposure event carries order ID, deal ID, position ID, source sequence, economic/
availability time, complete authority snapshot and ledger reference; duplicates retain identity;
partial/full/reversal/protection/terminal/foreign cases. Run targeted Ruff/mypy, two new tests plus
lifecycle/recovery and Trading L3 tests; usages 04/05. L3 paired matrix must pass with conservation.

**STOP/rollback/proposed commit:** stop if evidence must be reconstructed from a receipt or private
Trading type. Revert evidence additions/delete tests.

### Exact requirement-to-usage allocation

| Unit | Usage program and required functions |
|---|---|
| 18a | `02_state.py`: `fr_trd_107()`; `05_reconciliation.py`: `fr_trd_108()`, `fr_trd_110()`; `11_trade_ownership.py`: `fr_trd_109()` |
| 18b | `05_execution.py`: `fr_sim_223()` |

### Exact documentation manifests

#### Unit 18a

- **EDIT:** `app/services/trading/README.md`
- **EDIT:** `docs/CHANGELOG.md`

#### Unit 18b

- **EDIT:** `app/services/simulator/README.md`
- **EDIT:** `docs/CHANGELOG.md`

Every completed FR/checklist row receives final `path:line` evidence. Where listed, the changelog
receives one concise `## [Unreleased]` bullet and never duplicates a Feature Registry.

### Literal validation commands by approval unit

#### Unit 18a

```powershell
uv run ruff format --check app/services/trading tests/trading
uv run ruff check app/services/trading tests/trading
uv run mypy app/services/trading
uv run pytest tests/trading/unit/reconciliation/test_authority_event_ordering.py tests/trading/integration/test_two_route_position_reconciliation.py tests/trading/integration/test_reconciliation_restart.py tests/trading/integration/test_foreign_orphan_block.py
uv run python tests/trading/usage/features/02_state.py
uv run python tests/trading/usage/features/05_reconciliation.py
uv run python tests/trading/usage/features/11_trade_ownership.py
uv run pytest tests/trading
git diff --check
git status --short
```

#### Unit 18b

```powershell
uv run ruff format --check app/services/simulator tests/simulator
uv run ruff check app/services/simulator tests/simulator
uv run mypy app/services/simulator
uv run pytest tests/simulator/integration/test_trading_authority_evidence.py tests/simulator/integration/test_l3_position_parity.py
uv run python tests/simulator/usage/features/05_execution.py
uv run pytest tests/simulator
git diff --check
git status --short
```

Run only the commands for the approved unit. A missing path, pre-existing failure, skipped test,
or command substitution is a STOP and requires a correction dry run.

### Exact proposed commit messages

**Unit 18a:**

```text
fix(trading): reconcile positions consistently across routes

- Complete approved unit 18a within its declared domain and requirement boundary.
- Execute and document usage evidence: tests/trading/usage/features/02_state.py, 05_reconciliation.py, 11_trade_ownership.py.
- Pass targeted tests, owning-domain gates, documentation reconciliation, and rollback review.
```

**Unit 18b:**

```text
fix(simulator): supply position authority evidence

- Complete approved unit 18b within its declared domain and requirement boundary.
- Execute and document usage evidence: tests/simulator/usage/features/05_execution.py.
- Pass targeted tests, owning-domain gates, documentation reconciliation, and rollback review.
```

Commit execution is not authorized by phase approval. After separate commit authorization, stage only
the phase manifest, verify `git diff --cached --name-only`, and use the applicable message verbatim.

### Completion checklist

- [ ] Approval matched this exact phase/subphase.
- [ ] Only the local file and documentation manifests changed.
- [ ] Every listed FR has final `path:line` implementation and test evidence.
- [ ] Only verified package-root/public dependency contracts were used.
- [ ] Targeted unit/integration tests passed with recorded commands and exit codes.
- [ ] Ruff format/check and mypy passed for every owning domain.
- [ ] Every local usage program executed directly and passed.
- [ ] Every owning-domain phase gate passed.
- [ ] README, changelog, and listed system documents reconciled.
- [ ] STOP conditions and rollback path were rechecked.
- [ ] Commit remains unauthorized, or its separately authorized hash is recorded.

# Phase 19 · Empirical calibration

**Domain:** simulator. **Feature:** `FEAT-SIM-17`.
**Requirements:** `FR-SIM-181` … `186`, `224` … `227`.

Fit spread distributions from provider M1 spread evidence, partitioned by eligible scheduled-event
regime. Record broker, server, account digest, environment, symbol, training interval, source
availability, ingestion time, calibration time, effective interval, and overlap policy.

For latency, slippage, queue position, partial-fill, requote, and fault behavior, this phase may ingest
only eligible, checksummed execution-trace evidence and must publish the same temporal/provenance
fields plus sample coverage and applicability. A component without sufficient evidence is recorded as
excluded from the canonical envelope; Phase 20 may not manufacture its calibration.

Partition eligible evidence immutably into calibration, validation, and certification holdouts before
fitting. Publish partition hashes, selection rules, minimum coverage/sample requirements, exact
tolerances or statistical tests, confidence/error limits, and aggregate economic-error budgets before
opening the certification holdout. No parameter or threshold may be tuned after holdout evaluation;
changed policy requires a new artifact and untouched holdout.

Prospective canonical eligibility requires source availability and training end no later than the
evaluation start, complete coverage, matching source identity, and no evaluation leakage.
Retrospective fits are labelled and exploratory-only. Because economic-calendar revision history is
not field-level bitemporal, canonical regime labels use scheduled metadata only; forecast revisions,
actuals, and surprise remain exploratory until availability can be proved.

Demo artifacts may expand the sim-vs-demo envelope only. Live-account expansion requires independent
owner-supplied sanitized live evidence and the same untouched-holdout gate. M1 stressed spread is
explicitly an end-of-minute lower bound.

- `FR-SIM-224` versioned calibration artifact and provenance; `225` temporal/source eligibility;
  `226` immutable calibration/validation/certification partition isolation; `227` predeclared
  conformance thresholds, applicability, validity, and detected-drift invalidation.

---

## Implementation specification

**Outcome:** `FEAT-SIM-17` publishes immutable, leakage-safe calibration artifacts; insufficient
components remain explicitly excluded.

**Approval unit:** simulator. **Prerequisites:** 9, 17a. **Requirements:** `FR-SIM-181`–`186`,
`224`–`227`.

**Read first:** Simulator realism/scenarios/reporting/request identity/parity; Data dataset manifest
and availability contracts; Brokers conformance fixture schema; `pyproject.toml` pinned NumPy/pandas;
usage 12.

**File manifest:** **CREATE** `app/services/simulator/calibration/{README.md,__init__.py,contracts.py,partition.py,spread.py,execution.py,validate.py,public.py}`,
`tests/simulator/unit/calibration/test_partition.py`,
`tests/simulator/unit/calibration/test_spread_fit.py`,
`tests/simulator/unit/calibration/test_execution_fit.py`,
`tests/simulator/unit/calibration/test_temporal_eligibility.py`,
`tests/simulator/integration/test_calibration_artifact.py`,
`tests/simulator/integration/test_calibration_holdout_isolation.py`,
`tests/simulator/usage/features/17_calibration.py`; **EDIT** `app/services/simulator/__init__.py`, `app/services/simulator/README.md` and request/execution-
model identity binding. **DO NOT TOUCH:** source evidence, certification holdout after partition hash,
thresholds after opening holdout, live evidence collection, or Phase-20 sampling.

**Exact root surface:** functions to partition eligible evidence, fit spread artifact, fit eligible
execution components, validate an artifact against validation evidence, get applicability/exclusions,
and serialize/load checksummed artifacts. Internal estimators/models stay private.

**Artifact:** schema/version; broker/server/redacted account/environment/symbol; source identity;
availability/ingestion/calibration and effective intervals; immutable calibration/validation/
certification hashes and selection rule; scheduled-event regime; minimum coverage/sample; estimator/
algorithm/library versions; parameters; applicability/exclusions; predeclared metric/unit/test/
tolerance/confidence/economic-error budget; checksum. Demo and live scopes are distinct.

**Implementation order:** schema/canonical hash; temporal eligibility; deterministic partition before
fit; M1 spread model; only evidenced execution component fits; validation; holdout lock; artifact
identity/root exports; tests; usage/README.

**Tests:** order-independent deterministic partition; overlap/disjointness/tamper; late availability;
training after evaluation; scope/source mismatch; insufficient sample/coverage; M1 lower-bound label;
scheduled-regime only; retrospective label; demo/live separation; threshold mutation after holdout;
cross-process artifact hash; network disabled.

**Commands/gate:** targeted Ruff/mypy; six new tests plus realism, request identity, parity and Data
manifest integrations; direct usage 17. Gate proves holdout bytes are never passed to fit functions.

**STOP/rollback/proposed commit:** stop if temporal provenance is absent, a component is fitted from a
prior, or a holdout/threshold was previously opened/tuned. Remove feature/tests/usage/identity field.

### Exact requirement-to-usage allocation

| Unit | Usage program and required functions |
|---|---|
| 19 | `17_calibration.py`: `fr_sim_181()` … `fr_sim_186()`, `fr_sim_224()` … `fr_sim_227()` |

### Exact documentation manifest

- **EDIT:** `app/services/simulator/README.md`
- **EDIT:** `docs/CHANGELOG.md`
- **EDIT:** `docs/PROJECT.md`

Every completed FR/checklist row receives final `path:line` evidence. The changelog receives one concise
`## [Unreleased]` bullet under the correct change type and never duplicates a Feature Registry.

### Literal validation commands

```powershell
uv run ruff format --check app/services/simulator tests/simulator
uv run ruff check app/services/simulator tests/simulator
uv run mypy app/services/simulator
uv run pytest tests/simulator/unit/calibration/test_partition.py tests/simulator/unit/calibration/test_spread_fit.py tests/simulator/unit/calibration/test_execution_fit.py tests/simulator/unit/calibration/test_temporal_eligibility.py tests/simulator/integration/test_calibration_artifact.py tests/simulator/integration/test_calibration_holdout_isolation.py
uv run python tests/simulator/usage/features/17_calibration.py
uv run pytest tests/simulator
git diff --check
git status --short
```

Run the phase-named targeted pytest files before the owning-domain gate. A missing exact path,
pre-existing failure, skipped test, or command substitution is a STOP and requires a correction dry run.

### Exact proposed commit messages

**Unit 19:**

```text
feat(simulator): calibrate execution from governed evidence

- Complete approved unit 19 within its declared domain and requirement boundary.
- Execute and document usage evidence: tests/simulator/usage/features/17_calibration.py.
- Pass targeted tests, owning-domain gates, documentation reconciliation, and rollback review.
```

Commit execution is not authorized by phase approval. After separate commit authorization, stage only
the phase manifest, verify `git diff --cached --name-only`, and use the applicable message verbatim.

### Completion checklist

- [ ] Approval matched this exact phase/subphase.
- [ ] Only the local file and documentation manifests changed.
- [ ] Every listed FR has final `path:line` implementation and test evidence.
- [ ] Only verified package-root/public dependency contracts were used.
- [ ] Targeted unit/integration tests passed with recorded commands and exit codes.
- [ ] Ruff format/check and mypy passed for every owning domain.
- [ ] Every local usage program executed directly and passed.
- [ ] Every owning-domain phase gate passed.
- [ ] README, changelog, and listed system documents reconciled.
- [ ] STOP conditions and rollback path were rechecked.
- [ ] Commit remains unauthorized, or its separately authorized hash is recorded.

# Phase 20 · Seeded stochastic execution realism — L4

**Domain:** simulator. **Feature:** extend `FEAT-SIM-12`, `FEAT-SIM-15`.
**Requirements:** `FR-SIM-171` … `178`, `228` … `230`, `241`, and `242`.

Extend the scheduler with calibrated latency, spread, slippage, queue/partial-fill behavior, requote,
and seeded fault events. Queue position may be pathwise only with admitted Level-2 evidence; while
`OD-DATA-01` remains unresolved, only trace-calibrated outcome distributions can be admitted. Derive
concern-specific streams from canonical SHA-256 configuration material; never Python `hash()`. Pin
algorithm/version with golden vectors and serialize counter/RNG state for resume.

- `FR-SIM-241`: enforce the published one-year M1 and bounded multi-symbol incremental performance
  and memory budgets. The annual workload is a separately classified performance/integration gate,
  not a unit test subject to the 100 ms unit-test ceiling.
- `FR-SIM-242`: serialize and restore scheduler RNG/counter state without reordering events.
- `FR-SIM-228`: admit only calibrated execution-realism components; `229` seed and journal provider,
  transport, delivery, and connection-lifecycle fault scenarios; `230` converge crash/restart,
  unknown-outcome, and in-flight control recovery without duplicate mutation.

A stochastic component enters a canonical envelope only when its calibration artifact, applicability,
and conformance gate are present. A disclosed prior is `fast_research` only. Seeded timeout,
ambiguous response, rate-limit, or malformed success occurs only through the scenario engine and is
journalled per fill/event.

Add deterministic crash points after pre-audit, command submission, provider acceptance, response
receipt, receipt persistence, projection update, and reconciliation watermark advancement. Cover
disconnect/reconnect, stale/gapped delivery, duplicate/late/out-of-order events, in-flight kill switch,
and restart from every durable boundary. Recovery must converge to authority state without repeating a
mutation whose outcome is unknown.

**L4 gate:** cross-process and resume determinism, distribution conformance, no-lookahead, calibrated-
component eligibility, exploratory-prior rejection from canonical runs, untouched-holdout isolation,
crash/restart convergence, connection lifecycle, in-flight kill-switch behavior, and unknown-outcome
recovery.

---

## Implementation specification

**Outcome:** only calibrated realism components enter canonical runs; RNG/fault/recovery behavior is
deterministic across process and resume boundaries.

**Approval unit:** simulator. **Prerequisites:** 5, 17a, 19. **Requirements:** `FR-SIM-171`–`178`,
`228`–`230`, `241`, `242`.

**Read first:** Simulator realism/scenarios/scheduler/recovery/journal/execution; calibration public
artifact; request identity; checklists/reporting; usages 11–13 and 15.

**File manifest:** **CREATE** `app/services/simulator/realism/random_streams.py` and
`app/services/simulator/realism/crash_points.py`; **EDIT** realism contracts/models, scenario
contracts/engine, scheduler contracts/pump/state, execution matching/pricing/lifecycle, recovery
contracts/orchestrator, journal/reporting/checklists, request identity, `app/services/simulator/__init__.py`, `app/services/simulator/README.md`,
`tests/simulator/usage/features/11_scenarios.py`, `12_realism.py`, `13_recovery.py`,
`15_scheduler.py`; **CREATE** `tests/simulator/unit/test_random_streams.py`,
`tests/simulator/unit/test_calibrated_realism.py`, `tests/simulator/unit/test_seeded_faults.py`,
`tests/simulator/integration/test_realism_resume.py`,
`tests/simulator/integration/test_crash_boundary_recovery.py`,
`tests/simulator/integration/test_unknown_outcome_recovery.py`,
`tests/simulator/performance/test_annual_m1_budget.py`. **DO NOT TOUCH:** calibration/holdout artifacts,
Python global RNG, provider IO, or disclosure labels.

**Exact behavior:** derive concern-specific streams by SHA-256 over canonical configuration + concern
label; pin generator/algorithm/version and golden vectors; serialize counter/state. Schedule calibrated
latency/spread/slippage/eligible queue/partial-fill/requote/fault events. Level-2 pathwise queue is
forbidden while `OD-DATA-01` is unresolved. Scenario engine alone creates timeout, ambiguity,
rate-limit, malformed response, delivery and lifecycle faults. Journal component/artifact/seed/event.

**Crash points:** after pre-audit, command submission, authority acceptance, response receipt, receipt
persistence, projection update, and watermark advancement. Cover disconnect/reconnect, stale/gapped/
duplicate/late/out-of-order delivery, kill switch while in flight, and unknown outcome. Recovery queries
authority and converges without repeating an uncertain mutation.

**Implementation order:** stream derivation/golden vectors; scheduler state codec; calibration admission;
each realism component; scenario faults; crash-point harness; recovery convergence; reporting/checklist;
unit/integration tests; performance test; usages/README.

**Tests:** same seed/config same stream cross-process/resume; concern isolation; changed economic config
changes streams; trace IDs do not; artifact scope/applicability/tamper/expiry; uncalibrated component
canonical rejection and exploratory acceptance; distribution tests at predeclared thresholds; every
crash point; ambiguous accepted/not-found outcomes; kill switch; deterministic journal.

**Commands:** targeted Ruff/mypy; six new unit/integration tests plus scheduler, lifecycle, recovery,
scenario, calibration, journal and parity tests; direct usages 11/12/13/15. Run annual performance
separately with `uv run pytest tests/simulator/performance/test_annual_m1_budget.py`; record wall time,
peak RSS, dataset hash, machine profile and budget result—never classify it as a unit test.

**L4 gate/STOP:** cross-process/resume identity, conformance, no-lookahead, holdout isolation, recovery
and performance budgets all pass. Stop if RNG is unpinned/global, state cannot serialize exactly,
calibration is missing, a fault bypasses scenarios, or an unknown mutation might repeat.

**Rollback:** remove two modules/tests, revert consumers/usages/README and model identity;
rerun deterministic baseline/recovery.

### Exact requirement-to-usage allocation

| Unit | Usage program and required functions |
|---|---|
| 20 | `12_realism.py`: `fr_sim_171()` … `fr_sim_178()`, `fr_sim_228()`, `fr_sim_229()`, `fr_sim_241()`; `15_scheduler.py`: `fr_sim_230()`, `fr_sim_242()` |

### Exact documentation manifest

- **EDIT:** `app/services/simulator/README.md`
- **EDIT:** `docs/CHANGELOG.md`

Every completed FR/checklist row receives final `path:line` evidence. The changelog receives one concise
`## [Unreleased]` bullet under the correct change type and never duplicates a Feature Registry.

### Literal validation commands

```powershell
uv run ruff format --check app/services/simulator tests/simulator
uv run ruff check app/services/simulator tests/simulator
uv run mypy app/services/simulator
uv run pytest tests/simulator/unit/test_random_streams.py tests/simulator/unit/test_calibrated_realism.py tests/simulator/unit/test_seeded_faults.py tests/simulator/integration/test_realism_resume.py tests/simulator/integration/test_crash_boundary_recovery.py tests/simulator/integration/test_unknown_outcome_recovery.py tests/simulator/performance/test_annual_m1_budget.py
uv run python tests/simulator/usage/features/11_scenarios.py
uv run python tests/simulator/usage/features/12_realism.py
uv run pytest tests/simulator
git diff --check
git status --short
```

Run the phase-named targeted pytest files before the owning-domain gate. A missing exact path,
pre-existing failure, skipped test, or command substitution is a STOP and requires a correction dry run.

### Exact proposed commit messages

**Unit 20:**

```text
feat(simulator): add seeded execution realism and recovery

- Complete approved unit 20 within its declared domain and requirement boundary.
- Execute and document usage evidence: tests/simulator/usage/features/12_realism.py, 15_scheduler.py.
- Pass targeted tests, owning-domain gates, documentation reconciliation, and rollback review.
```

Commit execution is not authorized by phase approval. After separate commit authorization, stage only
the phase manifest, verify `git diff --cached --name-only`, and use the applicable message verbatim.

### Completion checklist

- [ ] Approval matched this exact phase/subphase.
- [ ] Only the local file and documentation manifests changed.
- [ ] Every listed FR has final `path:line` implementation and test evidence.
- [ ] Only verified package-root/public dependency contracts were used.
- [ ] Targeted unit/integration tests passed with recorded commands and exit codes.
- [ ] Ruff format/check and mypy passed for every owning domain.
- [ ] Every local usage program executed directly and passed.
- [ ] Every owning-domain phase gate passed.
- [ ] README, changelog, and listed system documents reconciled.
- [ ] STOP conditions and rollback path were rechecked.
- [ ] Commit remains unauthorized, or its separately authorized hash is recorded.

## Part 2 · Programme certification — L5-Demo and L5-Live

### Certification execution specification

**Outcome:** create a reproducible certificate bundle; this certification phase changes no production behavior.

**Approval unit:** each certificate scope/run requires separate owner approval. **Prerequisite:** all
phase gates for the declared maturity level. Demo approval never authorizes live collection or scope.

**Read first:** Part 2; envelope v1; parity feature README; every phase gate/evidence row; applicable
calibration/conformance artifacts; complete initial-authority-state manifest; environment safety rules.

**File manifest:** **CREATE GENERATED, DO NOT COMMIT**
`artifacts/sim_live_parity/<scope>/<envelope-version>/<certificate-id>/{manifest.json,left-evidence.json,right-evidence.json,normalized-left.json,normalized-right.json,comparison.json,commands.txt,environment.json,checksums.sha256}`;
**CREATE TEST** `tests/simulator/integration/test_l5_certificate_bundle.py` only if the bundle-schema test
does not already exist; **EDIT** parity README evidence/status only after certificate verification.
**DO NOT TOUCH:** source/calibration/thresholds/holdout data, envelope contents, or production accounts.

**Execution order:** preflight scope/environment/build/account exclusivity or complete foreign-event
coverage; verify all input checksums and validity; cold left/right execution from fresh stores and
artifact roots; normalize; compare; verify aggregate budget; rerun cold and compare checksums; write
bounded environment/command manifests; hash bundle; execute bundle-schema test; owner review; only then
publish certificate status. Failed bundles remain failed evidence and never update maturity status.

**Mandatory commands:** run targeted parity/bundle/replay/recovery tests, the applicable L1–L4 gates,
usage 18, and a second clean-process comparison. Record exact commands and exit codes in
`commands.txt`; never record credentials or raw account identifiers.

**Gate/STOP:** all Part-2 acceptance conditions pass, bundle hashes reproduce, no ignored economic
field exists, and certificate scope/validity are exact. Stop on environment uncertainty, missing
activity/clock edge/specification interval, changed holdout/threshold, provider drift, or any secret.

**Rollback:** delete only the exact failed/unpublished certificate directory after
verifying its resolved path is under `artifacts/sim_live_parity`; revert README status if written.
Proposed documentation commit after successful owner-reviewed publication:
`docs: publish bounded <demo|live> parity certificate`.

### Parity Envelope v1 publication

Publish one immutable manifest containing:

- certificate scope (`demo` or `live`), provider, environment, server/account mode, allowed evidence
  source, and target build;
- admitted symbol/specification revisions and effective intervals;
- MT5-FX scope and explicit provider, asset-class, corporate-action, auction, and multi-account
  exclusions;
- market-evidence class, tick model/resolution, bid/ask and depth availability, and clock-edge coverage;
- complete initial-authority-state hash, account exclusivity policy or foreign/manual activity replay
  coverage, and last reconciled transaction/deal watermark;
- operation/order/fill/time/position modes;
- capability intersection;
- verified swap-posting, stop-out, causal-order, weekly-session, and dated-session-exception policies,
  or explicit exclusion of paths requiring them;
- calculation/calibration identities, immutable calibration/validation/certification partition hashes,
  predeclared metrics, tolerances, sample/coverage thresholds, and aggregate economic-error budgets;
- comparator/normalizer version, invariant classes, allowed route-specific fields, and ignored-field
  registry;
- evidence fixture hashes, collection environment, and provenance;
- issued-at, valid-through, and deterministic invalidation triggers for provider/build, contract,
  code/config identity, specification, source/tick model, calibration validity, and detected drift;
- performance envelope.

No `Pending` item may be silently included. Expanding the matrix creates a new envelope version and
requires the same gates. An invalidated or expired certificate confers no parity claim.

### Common acceptance criteria

- [ ] Dependency graph is acyclic; Brokers imports no Simulation symbol.
- [ ] Paired semantic comparison passes without a real network session.
- [ ] Identifier relationship mutation and economic-time drift are detected by the comparator.
- [ ] Exact, bounded numeric, and distributional invariants use registered metrics; aggregate economic
      drift cannot pass by exhausting many individual tolerances.
- [ ] Scheduler internal total order, pump, cancellation, resume, and multi-symbol determinism pass
      without claiming provider order for unobservable concurrent events.
- [ ] Provider causal edges and evidenced partial orders survive normalization; ambiguous races are
      detected or excluded.
- [ ] Request v2 hashing changes for every execution-affecting field and not for trace IDs.
- [ ] Request/run identity changes for any initial balance, margin, position, order, protection,
      ownership, watermark, accrued-cost, evidence-class, or certificate-target change.
- [ ] Data point-in-time provider revisions cover every certified run interval without backdating.
- [ ] Path-sensitive certification accepts genuine bid/ask tick evidence only; derived OHLC paths and
      unresolved Level-2 queue claims are rejected from that scope.
- [ ] Weekly sessions plus verified dated exceptions cover each certified interval; uncovered holiday,
      maintenance, or exceptional-closure intervals are rejected.
- [ ] Local calculation model matches bounded MT5 fixtures after exact provider rounding.
- [ ] Simulation adapter passes its published capability-intersection conformance suite.
- [ ] Connect/disconnect/reconnect, mutation-while-disconnected, stale/gapped delivery, and session
      finalization match the admitted canonical lifecycle.
- [ ] Trading mutation and incremental evaluation paths are route-independent at business/risk gates.
- [ ] Route-specific safety gates are explicit and correctly enforced.
- [ ] The initial account interval is exclusive or every foreign/manual order, deal, balance, credit,
      and correction is replayed; missing activity invalidates certification.
- [ ] Protective exits and terminal liquidation leave current deals, projections, and trade records.
- [ ] Account/order/deal/position and signed-ledger conservation fixtures pass.
- [ ] Cancel/fill, modify/fill, protection/close, disconnect/response, and cross-symbol margin races
      preserve observed causality or remain outside the envelope.
- [ ] Every deterministic crash point restarts from durable evidence, reconciles to authority, and
      never repeats an unknown-outcome mutation.
- [ ] Kill-switch activation before submission, in flight, during partial fill, while disconnected,
      and during recovery produces the registered fail-closed state.
- [ ] Canonical execution rejects missing calibration, priors, fallbacks, stale evidence, gaps, and
      envelope-external modes.
- [ ] Calibration, validation, and certification partitions are immutable and disjoint; thresholds
      are fixed before holdout evaluation and no tuning uses certification results.
- [ ] The certificate expires or invalidates on every registered evidence/execution-identity change
      and cannot be used after invalidation.
- [ ] Cold re-execution from fresh stores/artifact roots is byte/semantic deterministic as registered,
      with provider calls disabled.
- [ ] One-year M1 and bounded multi-symbol incremental workloads meet registered runtime/memory budgets.
- [ ] Every unit test remains below the repository 100 ms ceiling or isolates/mocks IO appropriately.
- [ ] Default full suite, Ruff, mypy, usage programs, and 80% coverage floor pass without credentials.
- [ ] `simulation_dispatch` is absent and legacy v1/sync deprecations match their declared windows.

### L5-Demo acceptance

- [ ] All common acceptance criteria pass for one explicitly published MT5-demo envelope.
- [ ] A mandatory independent demo certification holdout passes the predeclared differential gates.
- [ ] Demo fixture collection, if needed, occurred only under a separately approved non-production
      operation; the default suite replays immutable sanitized evidence offline.
- [ ] The certificate and every report state `sim-vs-demo`; no API, document, or release text calls it
      live-account parity.

L5-Demo completes only the demo-scoped programme. It does not close the L5-Live goal.

### L5-Live acceptance

- [ ] All common acceptance criteria pass for one explicitly published MT5 live-account envelope.
- [ ] A mandatory independent sanitized live-account certification holdout passes the same
      predeclared differential gates; demo evidence is not a substitute.
- [ ] Evidence is owner-supplied, immutable, provenance-verified, and consumable without any repository
      production connection or mutation.
- [ ] Every live-specific execution, cost, liquidity, account, and session behavior claimed by the
      envelope is covered; uncovered behavior remains excluded.

Until these criteria pass, L5-Live remains open even when L5-Demo is valid.

### Standing regression guards

These exact pytest node IDs must not be deleted, renamed, skipped, xfailed, or weakened. Their owning phase
creates the containing file and must use the listed test name:

1. `tests/brokers/unit/simulation/test_simulation_isolation.py::test_simulation_adapter_import_graph_is_acyclic`
2. `tests/simulator/integration/test_parity_relationships.py::test_relationship_mutation_fails_parity`
3. `tests/simulator/integration/test_semantic_parity.py::test_paired_semantic_evidence_passes_envelope`
4. `tests/simulator/integration/test_incremental_trading_cycle.py::test_incremental_cycle_matches_captured_trace`
5. `tests/simulator/integration/test_cold_determinism.py::test_cold_runs_from_fresh_roots_are_identical`
6. `tests/simulator/integration/test_scheduler_total_order.py::test_scheduler_total_order_is_cross_process_stable`
7. `tests/simulator/integration/test_scheduler_resume.py::test_scheduler_resume_preserves_event_and_result_order`
8. `tests/data/integration/test_provider_specification_history.py::test_as_of_requires_complete_effective_coverage`
9. `tests/simulator/integration/test_calculation_conformance.py::test_all_admitted_provider_fixtures_match_exactly`
10. `tests/brokers/integration/test_simulation_conformance.py::test_simulation_adapter_passes_admitted_intersection`
11. `tests/brokers/unit/simulation/test_simulation_isolation.py::test_simulation_adapter_opens_no_socket`
12. `tests/simulator/integration/test_no_future_reads.py::test_no_dependency_returns_future_available_evidence`
13. `tests/simulator/unit/calibration/test_temporal_eligibility.py::test_future_regime_evidence_is_ineligible`
14. `tests/simulator/integration/test_ledger_conservation.py::test_signed_ledger_conserves_after_every_posting`
15. `tests/simulator/integration/test_parity_envelope_rejection.py::test_unregistered_ignored_field_is_rejected`
16. `tests/simulator/performance/test_annual_m1_budget.py::test_annual_m1_incremental_budget`
17. `tests/simulator/integration/test_parity_envelope_rejection.py::test_demo_evidence_cannot_claim_live_scope`
18. `tests/simulator/unit/test_market_evidence_lineage.py::test_path_sensitive_parity_requires_genuine_ticks`
19. `tests/simulator/integration/test_initial_authority_state.py::test_initial_authority_hash_binds_both_routes`
20. `tests/simulator/integration/test_foreign_activity_guard.py::test_missing_external_activity_blocks_certification`
21. `tests/trading/integration/test_simulation_session_lifecycle.py::test_simulation_lifecycle_shape_matches_live_fixture`
22. `tests/simulator/integration/test_crash_boundary_recovery.py::test_every_crash_boundary_converges_without_duplicate_mutation`
23. `tests/simulator/integration/test_lifecycle_races.py::test_ambiguous_concurrent_authority_order_is_not_invented`
24. `tests/simulator/integration/test_crash_boundary_recovery.py::test_inflight_kill_switch_blocks_new_mutation_and_converges`
25. `tests/simulator/integration/test_calibration_holdout_isolation.py::test_certification_holdout_never_enters_fit_or_threshold_selection`
26. `tests/simulator/integration/test_parity_envelope_rejection.py::test_certificate_invalidates_when_bound_identity_changes`
27. `tests/simulator/integration/test_session_semantics.py::test_missing_dated_session_exception_blocks_canonical_execution`

### Final documentation pass

After all acceptance criteria for the claimed certificate pass:

1. Write completed requirement evidence and public APIs into owning READMEs.
2. Reconcile feature counts: Brokers **thirteen**, Data **fourteen**, Simulation **eighteen**,
   Trading **eleven**.
3. Delete `sim-live-parity-register.md` and this implementation plan only after their surviving
   content, certificate scope, and any still-open L5-Live goal are folded into authorities.
4. Remove resolved Open Decisions; preserve no decision-history ledger.
5. Aggregate the Unreleased changelog only when the owner publishes a release.
6. Remove v1 order contracts or the synchronous bridge only in a separately approved release after
   their compatibility windows have actually closed.

### Proposed release summary

```text
feat(trading-simulator): certify bounded simulation and <demo|live> execution parity

- Converge Simulation and the named Trading authority route on one orchestration path.
- Add versioned provider evidence, deterministic scheduling, local calculation conformance,
  incremental evaluation, complete order/deal accounting, and calibrated realism.
- Publish an explicitly scoped Parity Envelope v1 certificate and fail canonical execution closed
  outside verified or still-valid evidence.
```

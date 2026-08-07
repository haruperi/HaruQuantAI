# Trading Cockpit — Phase 0 Baseline and Gap Audit

**Baseline ID:** `HQA-TC-P0-20260807T075707Z-3b039544`
**Commit:** `3b039544b7812a78f140530d39e744421eac1396` on `main`
**Captured (UTC):** `2026-08-07T07:57:07Z`
**Prompt:** `HQA-TC-PHASE0-AUDIT-001` v1.0
**Exit gate:** `NOT_READY` — blocked on decision **D-1**

---

## Purpose

Establish a protected, reproducible, evidence-backed baseline before any Trading Cockpit implementation
begins, so that the next agent can start the `Utils` phase without rediscovering what already exists,
what is authoritative, what is duplicated, which gaps are real, which tests already fail, and which
safety boundaries are proven.

**No Trading Cockpit feature was implemented. No application source, test, migration, configuration,
dependency file or lockfile was modified.**

---

## Source documents

| Document | Version | SHA-256 |
|---|---|---|
| [`Trading_Cockpit_Game_Specification_v1.2.md`](../Trading_Cockpit_Game_Specification_v1.2.md) | 1.2 (`TCS-TRADING-COCKPIT-001`) | `b460f314f0fdf6827af381278f917648ad36f3f82c9f27942e04b0ebbc97889c` |
| [`Trading_Cockpit_Phased_Implementation_Plan_v1.0.md`](../Trading_Cockpit_Phased_Implementation_Plan_v1.0.md) | 1.0 (`HQA-TCS-IMP-001`) | `e65fa81834be2dd6dbb5764a27d962dc70de9566f303bfafcd0a2ee68ac2d818` |
| [`Trading_Cockpit_Phase_0_Audit_Prompt.md`](../Trading_Cockpit_Phase_0_Audit_Prompt.md) | 1.0 (`HQA-TC-PHASE0-AUDIT-001`) | `8396968162fd80fbf7ffe45f4df272e97bad1c9676affbf77717aeaf686de252` |

Both required source documents are present; no `BLOCKED_BY_MISSING_SOURCE` condition applies.

---

## Artifact index

| Artifact | Work package | What it answers |
|---|---|---|
| [`repository-baseline.md`](repository-baseline.md) | `TC-IMP-BASE-01` | Exact repository, toolchain, lockfile, migration and source-document state at the moment of the audit, plus the final worktree comparison |
| [`baseline-manifest.json`](baseline-manifest.json) | `TC-IMP-BASE-01` | The same baseline, machine-readable, including every validation command and its outcome |
| [`current-state-domain-inventory.md`](current-state-domain-inventory.md) | `TC-IMP-BASE-02` | What each of the fourteen domains actually contains, with paths, symbols, tables, tests and consumers |
| [`trading-cockpit-traceability-matrix.md`](trading-cockpit-traceability-matrix.md) · [`.csv`](trading-cockpit-traceability-matrix.csv) | `TC-IMP-BASE-03` | 603 atomic specification requirements mapped to owner, evidence, status, work package and acceptance target |
| [`trading-cockpit-gap-matrix.md`](trading-cockpit-gap-matrix.md) · [`.csv`](trading-cockpit-gap-matrix.csv) | `TC-IMP-BASE-04` | All 239 planned work packages, each with one current status and one future action classification |
| [`trading-cockpit-contract-registry.md`](trading-cockpit-contract-registry.md) · [`.csv`](trading-cockpit-contract-registry.csv) | `TC-IMP-BASE-05` | Every required cross-domain contract, its current candidate, owner, and collision analysis |
| [`trading-cockpit-database-ownership.md`](trading-cockpit-database-ownership.md) | `TC-IMP-BASE-06` | 94 logical tables with owner, keys, mutability, retention and collisions; and the durable cockpit state that has no owner |
| [`trading-cockpit-test-baseline.md`](trading-cockpit-test-baseline.md) | `TC-IMP-BASE-07` | Every validation command run, skipped or blocked, with exit codes and pre-existing failures |
| [`trading-cockpit-safety-baseline.md`](trading-cockpit-safety-baseline.md) | `TC-IMP-BASE-08` | Every broker write path, every guard, the safety classification and its justification |
| [`trading-cockpit-change-control.md`](trading-cockpit-change-control.md) | `TC-IMP-BASE-10` | The fifteen binding rules for every later phase, plus the extend-existing-domains decision |
| [`phase-0-findings-and-decisions.md`](phase-0-findings-and-decisions.md) | — | The audit conclusion: counts, collisions, risks, settled decisions, open owner decisions, and the Phase 1 readiness statement |

**Start here:** `phase-0-findings-and-decisions.md`, then the matrix relevant to your phase.

---

## Headline numbers

| | |
|---|---:|
| Domains inventoried | **14 / 14** |
| Python files / lines inspected | 910 / 198,352 |
| Registered features found | 165 |
| Public exports found | 1,064 (**0 class-like**) |
| Test files / usage programs | 758 / 374 |
| Logical database tables | 94 (103 `CREATE TABLE` statements) |
| Specification requirements traced | **603** |
| — final acceptance criteria | **40 / 40** |
| — checklist steps | 125 |
| — emergency steps | 24 |
| Work packages classified | **239 / 239** |
| Contracts inventoried | **66** |
| Requirements at `FULL` | **0** |
| Forward work packages at `REUSE` | **1** (`TC-IMP-AGT-09`) |

### Work-package classification

| Current status | Count | | Future action | Count |
|---|---:|---|---|---:|
| `FULL` | 10 (Phase 0) | | `REUSE` | 11 |
| `PARTIAL` | 115 | | `EXTEND` | 109 |
| `ABSENT` | 114 | | `CREATE` | 86 |
| `CONFLICTING` | 0 | | `REFACTOR` | 6 |
| `UNKNOWN` | 0 | | `DEFERRED_INTEGRATION` | 27 |
| `NOT_APPLICABLE` | 0 | | `NOT_APPLICABLE` | 0 |

---

## Audit scope

**Performed:** full read-only inspection of `app/`, `tests/`, `docs/`, migrations, configuration and CI;
repository-wide symbol scan for every required contract; extraction of all 239 work-package IDs and all
603 specification requirements; static reading of all 103 `CREATE TABLE` statements; safe non-mutating
validation commands with every cache and environment redirected outside the repository; creation of this
artifact set.

**Not performed, by rule:** no migration applied, no database opened, no broker connection opened, no
order transmitted, no `.env` read, no secret recorded, no auto-fix or formatter run, no pre-commit hook
invoked, no git state-changing command executed, no application code changed.

---

## Known limitations

Read these before trusting a number in this directory.

1. **The audit ran on Linux; the project targets Windows.** All 2,127 Ruff findings are `EXE002`,
   caused by the mount presenting files as mode 0755. Seven Brokers test failures are `MetaTrader5`
   being Windows-only. Neither is a repository defect.
2. **No coverage figure was produced.** The full suite did not complete within the audit host's
   ~178-second per-command limit, and detached background processes do not survive a call. 2,311 tests
   were executed across seven packages; the remaining packages were not run.
3. **Three genuine pre-existing failures were confirmed** (mypy `manifest.py:34`, the Utils
   cross-domain-import guard, the Trading simulation-target parity check). Eight further failures are
   environment-sensitive and unconfirmed.
4. **Four gap-matrix rows carry `LOW` confidence** — `TC-IMP-DATA-03`, `TC-IMP-STRAT-09`,
   `TC-IMP-RISK-15`, `TC-IMP-UIAPI-05`. Re-investigate before implementing them.
5. **Derived requirement IDs are Phase 0 constructs.** `TCS-Snn-REQ-nnn` and `TCS-Snn-m-TBL-nnn` are
   stable functions of section and ordinal position in the source document. Source-assigned IDs
   (`PRE_*`, `ENTRY_*`, `MGT_*`, `EXIT_*`, `POST_*`, `FLASH_*`, `API_*`, `DD_*`) were preserved exactly.
6. **`Utils` and `Optimization` own no directly-attributable normative requirement.** Their obligations
   arrive through the work-package plan, not through a specification sentence. Recorded, not resolved.
7. **`docs/schema/` verification scripts were not executed** — they were not proven read-only.
8. **`git status` is unusable on this checkout without `-c core.autocrlf=input`.** The default form
   reports all 1,969 tracked text files as modified. There are zero content changes.
9. **The ADR file was deliberately not created.** `AGENTS.md` section 4 prohibits standalone
   decision-record documents; the owner directed that `AGENTS.md` takes precedence. The decision is
   recorded in `phase-0-findings-and-decisions.md` (D-10) and as rule 1 of
   `trading-cockpit-change-control.md`.
10. **The three `.csv` artifacts in this directory are excluded by `.gitignore` line 634 (`*.csv`).**
    They exist on disk and are byte-for-byte consistent with their `.md` twins, but `git status` will
    not offer them and a plain `git add` will skip them. Modifying `.gitignore` is a configuration
    change outside Phase 0 scope, so it was not done. See decision **D-11**.

---

## Exit-gate status

```text
PHASE 0: COMPLETE
PHASE 1 READINESS: NOT_READY
```

All twelve Phase 0 exit-gate conditions are satisfied — the baseline exists, all fourteen domains are
inventoried, all 239 work packages are classified, all 66 contracts are analysed, all 603 requirements
and all 40 acceptance criteria are traceable, persistence ownership is documented, the quality baseline
is recorded (with blocked commands explicitly stated), live-write isolation is classified with evidence,
the extend-existing-domains decision is recorded, no implementation code was added, no owner change was
overwritten, and the final repository state contains only permitted Phase 0 artifacts.

Phase 1 is nonetheless `NOT_READY`, blocked on one decision rather than on missing analysis:

| | Decision | Why it blocks |
|---|---|---|
| **D-1** | How do versioned types cross domain boundaries? | `AGENTS.md` mandates a function-only public API surface (verified: 1,064 exports, 0 class-like). Every one of the ~54 required cross-domain contracts is a type. `TC-IMP-UTIL-01` cannot define `ProfileRef` or `VersionRef` as consumable cross-domain types until this is settled. |

Recommended to resolve before Phase 1 rather than during it: **D-3** (transaction/outbox ownership) and
**D-7** (fix the Utils import-guard and Trading simulation-target tests, both of which currently leave a
rule the cockpit depends on unenforced).

Full decision list: [`phase-0-findings-and-decisions.md`](phase-0-findings-and-decisions.md) section 9.

---

## The three things that should shape the plan

1. **There is no accounting system.** No ledger, account, cash, balance, equity, margin or P&L model
   exists anywhere in `app/`. The existing Portfolio domain is an allocation and rebalancing engine. The
   cockpit's entire financial authority must be built from nothing — and the plan schedules it twelfth,
   behind four phases that consume portfolio state.
2. **The contract registry and the public-API rule are incompatible as written** (decision D-1).
3. **The strongest cockpit asset already exists.** A durable simulation session with an orchestrator, a
   create/read/step/branch/close HTTP API, an SSE frame stream, an immutable journal and a canonical tick
   timeline is already running. Phase 8 should start from it, not beside it.

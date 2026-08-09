# Dry-Run — Trading Cockpit Phase 0 Findings → Domain README Folding

**Task:** Fold all 229 approved Phase 0 work packages into the 14 owning domain READMEs (doc-only; no code/tests/migrations/configs/deps/Phase-0-evidence/project-wide docs touched). Per `AGENTS.md`, no edits until a standalone `APPROVED: EXECUTE`.

## Critical findings shaping the plan
1. **Utils is ALREADY folded** (pre-existing `app/utils/README.md` change: 498 insertions, all 12 Phase-1 gaps, status `Partial`, FR-UTL-088/NFR-UTL-010/WF-UTL-008/usage 10–14). It also **resolves the two blocking decisions**: **D-1** (contracts = validated JSON-safe mappings behind `build_*`/`parse_*` function pairs — function-only `AGENTS.md` rule unchanged) and **D-3** (transaction/outbox stays in Data). **Per rule 12 + owner confirmation: Utils preserved as-is, verified only.**
2. **CSV-authoritative counts** (prompt/findings off by one): Simulator **24 CREATE/6 EXTEND/1 REFACTOR**; UI-API **23 CREATE/6 EXTEND/6 DEFERRED**; Portfolio **12 CREATE/3 EXTEND/2 REFACTOR**. Global: 109 EXTEND / 86 CREATE / 6 REFACTOR / 27 DEFERRED / 1 REUSE.
3. **Baseline drift CLEAN** (Section 13): only pre-existing Utils README (M, preserved) + prompt (M) in working tree. No code/test/migration/contract/export drift.
4. **Owner decisions (AskUserQuestion):** adopt Utils' D-1/D-3 resolution in all 13 remaining domains as settled; Utils preserved.
5. **Phase-0 errors to correct (not propagate):** `agentic_lifecycle_transitions` HAS composite PK `(artifact_hash, sequence)` (P-10 wrong); `sim_sessions` has 6 cols not 4; `FORBIDDEN_TOOL_TOKENS` has 12 tokens at line 47.

## Files — ONLY these 14 READMEs
Utils `app/utils/README.md` (verify only). Brokers/Data/Indicators/Strategy/Risk/Trading/Simulator/Analytics/Optimization/Research/Portfolio/Agentic/UI-API under `app/services/<domain>/README.md` (Agentic at `app/agentic/README.md`). **Nothing else.**

## Per-domain fold decisions (owner = the README; new work = `Missing`, touched feature = `Partial`)

| Domain | Gaps | CREATE→new FEAT (next valid ID) | EXTEND/REFACTOR/DEFERRED highlights |
|---|---|---|---|
| 1 Utils | 12 | none (folded) | **Preserve as-is.** |
| 2 Brokers | 12 | FEAT-BRK-16 (route_discipline) | 11 EXTEND; BRK-04 AccountStateSnapshot Data→Brokers = Open Decision |
| 3 Data | 13 | FEAT-DATA-19 (replay_packages) | 12 EXTEND; DATA-03 L2 **LOW conf flagged**; OrderBookSnapshot ownership Open Decision |
| 4 Indicators | 10 | FEAT-INDI-07 (snapshots), -08 (input_guards) | 8 EXTEND (regime/liquidity/etc. on existing 21-indicator library) |
| 5 Strategy | 11 | FEAT-STR-12 (operating_envelope), -13 (exit_plans), -14 (manual_plans) | 7 EXTEND; STRAT-08 DEFERRED→RES-03; **`_v2` table authority Open Decision**; TradeIntent/TradePlan divergence documented |
| 6 Risk | 17 | FEAT-RISK-16 (stop_validation), -17 | 12 EXTEND; RISK-12 REFACTOR ScenarioDefinition collision (paired resolution w/ Simulator); RISK-07/-10 DEFERRED; RISK-15 **LOW conf**; kill-switch granularity (S-3) |
| 7 Trading | 14 | FEAT-TRD-10 (protective_orders — FEAT-TRD-08 slot taken), -11 (trade_ownership) | 12 EXTEND; **`OrderIntent = Any` Simulator erasure documented**; UNKNOWN state missing; `trading_positions/__new` authority Open Decision; master-enable granularity (S-3) |
| 8 Simulator | 31 | FEAT-SIM-10.. (24 CREATE) | 6 EXTEND; **SIM-11 REFACTOR ScenarioDefinition→distinct name**; SIM-09 blocks BRK-10; SIM-04 ReplayIdentity split w/ Strategy; SIM-23 sim_sessions 6→full; SIM-28 AlertEvent |
| 9 Analytics | 13 | FEAT-ANLT-06.. (10 CREATE) | 3 EXTEND; **distinct names**: JournalEntry≠Simulator journal/, Scorecard≠Research ResearchScorecard; new `analytics_*` tables target-only |
| 10 Optimization | 10 | none (0 CREATE) | 7 EXTEND; 3 DEFERRED (OPT-02/03/06→SIM/RISK/RES) |
| 11 Research | 11 | FEAT-RES-14.. (4 CREATE) | 6 EXTEND; RES-07 DEFERRED→SIM-11; **RES-03 ApprovedExpectancyProfile blocks STRAT-08+RISK-07**; research_artifacts path-PK brittleness Open Decision |
| 12 Portfolio | 17 | FEAT-PORT-09.. (12 CREATE) | 3 EXTEND; **PORT-06 FX REFACTOR** + **PORT-17 PortfolioState REFACTOR (Risk evidence.py:240)** = Open Decisions; PORT-01 LedgerEntry = entire financial authority (P-1); PORT-07 blocks RISK-10 |
| 13 Agentic | 11 | none (0 CREATE) | 6 EXTEND; 4 DEFERRED; **AGT-09 = ONLY REUSE, preserve verbatim**; correct P-10 PK; fix 10→12 token inaccuracy |
| 14 UI-API | 35 | FEAT-API-14.. (23 CREATE) | 6 EXTEND; 6 DEFERRED (30–35); UIAPI-05 **LOW conf**; zero new tables; api_idempotency/api_approvals REFACTOR candidates |

Each README keeps its **exact existing structure** (header order, table columns, `Completed/Partial/Missing` vocabulary, ID conventions). Folding adds a `### Trading Cockpit Phase 0 reconciliation` subsection under affected sections and extends existing Purpose/Owns/Shared-contracts/Persisted-state/Feature-Registry/Workflows/NFR/Open-Decisions/Tests tables in place. REFACTOR/CONFLICTING gaps are **documented as cross-domain decisions, not executed** (no contract/table/code relocation).

## New identifier floors (contiguous from here; retired/reserved IDs never reused)
BRK-16/FR-136 · DATA-19/FR-181 · INDI-07,08/FR-036 · STR-12,13,14/FR-054 · RISK-16,17/FR-082 · TRD-10,11/FR-078 · SIM-10../FR-091+band · ANLT-06../FR-061 · OPT (extend FR-072) · RES-14../FR-107 · PORT-09../FR-049 · AGT (extend FR-AGENTIC-073) · API-14../FR-078. Usage programs 1:1 with new features.

## Open Decisions to RECORD (not resolve) in READMEs
Strategy `_v2` authority · Trading `trading_positions/__new` authority · Risk↔Simulator ScenarioDefinition name · Portfolio↔Risk PortfolioState reclaim/rename · Portfolio↔Data↔Simulator FX authority · Brokers↔Data AccountStateSnapshot · Brokers↔Data OrderBookSnapshot · Research `research_artifacts` surrogate key · Analytics new-table field detail · UI-API↔Risk second approval store.

## Validation (after edits)
14.1 every gap mapped to one owner · 14.2 no dup/reused IDs · 14.3 one feature↔one folder, atomic FRs · 14.4 owned/consumed contracts agree, one writer/schema-owner per table · 14.5 unimplemented=`Missing`, package→`Partial` · 14.6 grep each README for `docs/dev/trading-cockpit` → no normative dependency · 14.7 `git diff --stat` shows only the 14 READMEs (+ preserved Utils pre-change).

## Excluded
Any code/tests/usage-programs/migrations/configs/deps/lockfiles/API-schemas/`AGENTS.md`/`docs/PROJECT.md`/`docs/ARCHITECTURE.md`/`docs/CHANGELOG.md`/Phase-0-evidence/commits/pushes; actual contract/table relocation.

## Rollback
All edits are additive (new subsections + extended rows). Revert per-file via `git checkout -- <README>` (state-changing — only on explicit owner instruction). No IDs escape READMEs into code. Pre-existing Utils fold is never part of rollback.

**Implementation order:** Utils(verify)→Brokers→Data→Indicators→Strategy→Risk→Trading→Simulator→Analytics→Optimization→Research→Portfolio→Agentic→UI-API; validate per cluster + full validation; then Section-15 final report. **No edits until standalone `APPROVED: EXECUTE`.**

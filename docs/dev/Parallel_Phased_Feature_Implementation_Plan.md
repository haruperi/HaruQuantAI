# HaruQuantAI V3 — Three-Agent Parallel Feature Execution Plan

**Parallel schedule v1.0 · 8 September 2026 · baseline `fde786fa4bd76d241fb6a8b64ba092f7b6e19238`**

## 1. Purpose and authority

This document is a parallel-execution companion to
[`Phased_Feature_Implementation_Plan.md`](Phased_Feature_Implementation_Plan.md). It assigns the
open feature Tasks to three execution lanes—Codex, Gemini and ZCode—without duplicating the feature
cards or becoming a second feature registry.

The original phased plan remains authoritative for feature scope, requirements, task status,
acceptance, evidence and commit identity. `docs/dev/evidence/dependency-schedule.json` remains
authoritative for schedule constraints. Owning domain READMEs, `docs/PROJECT.md`,
`docs/ARCHITECTURE.md`, `AGENTS.md` and the feature implementation pipeline retain their existing
authority. If this schedule conflicts with any of them, the conflicting lane assignment is invalid
and must be regenerated; the authority is never weakened to preserve a slot.

This schedule was calculated from 205 unique Tasks, eight accepted Tasks, 197 open Tasks and 729
schedule constraints. It has 67 waves, at most three Tasks per wave and no known predecessor
violation at the pinned baseline.

## 2. Governance prerequisite

The default repository workflow permits only one active Goal child. Schema-v4 adds opt-in parallel
drafts without weakening the rule that every accepted Task must be refreshed onto latest clean
accepted `main` and merged with exact parent lineage. Stale drafts are never merged directly, and
the controller does not rebase, cherry-pick or resolve semantic conflicts mechanically.

This schedule becomes executable only after the schema-v4 parallel workflow implementation is
committed, a non-Quick-Fix runtime policy explicitly enables it, and a Goal selects
`parallelism = 3`. Merely opening three chats or clones remains insufficient. The governed
controller provides all of the following:

1. Three isolated worktrees and namespaced active-Task workspaces, with no shared mutable runtime
   journals.
2. A deterministic ready queue derived from accepted predecessor evidence.
3. One path lease per production, test, README, evidence and generated-artifact path.
4. Parallel draft execution with a serialized acceptance queue.
5. A baseline-refresh mechanism that preserves one feature/one Task/one accepted implementation
   commit. The safe default is fresh-branch replay from latest accepted `main`, followed by complete
   affected validation and a fresh Reviewer decision; no silent rebase or cherry-pick is implied.
6. Deterministic handling of shared tracker, domain README, evidence-index and generated-file
   updates.
7. Independent Task gates, session continuity, cancellation, recovery and audit evidence for each
   lane.
8. Tests proving that stale baselines, overlapping paths, predecessor loss and integration conflicts
   fail closed.

Until the schema-v4 implementation is committed and explicitly configured, continue using the
existing sequential Goal/Task workflow. Merely opening three chats or clones does not satisfy this
prerequisite.

## 3. Parallel execution contract

### 3.1 Unit of work

A feature remains one atomic Task. Each Task retains its Planner → Executor → Reviewer lifecycle,
owner gates, focused implementation commit, explicit merge record, usage evidence and complete
Definition of Done. An agent owns one Task at a time and may not combine adjacent slots into a
larger commit.

The three names identify execution lanes, not permanent domain owners. Repository ownership remains
with the registered feature and its canonical README. Agent-specific conclusions are claims until
independently verified through the Task workflow.

### 3.2 Readiness

A lane may claim a Task only when all of these conditions hold:

- Every required predecessor is accepted on the integration baseline with the required evidence.
- Any phase, operation-qualification or external-evidence gate applicable to the Task is satisfied.
- The Task is still open in the canonical phased plan.
- No active lane holds an overlapping path lease.
- The Task specification and complete role prompt are generated from the same repository state.
- The lane's worktree is clean except for that Task's explicitly owned changes.

Operation-gated dependencies do not become fabricated provider evidence. The consumer implements its
complete fail-closed adapter behavior in its own Task, while actual provider qualification remains
owned by the later provider Task identified in the canonical schedule.

### 3.3 Waves and dynamic dispatch

The table in §6 is a deterministic equal-duration seed schedule. A wave is a conservative dispatch
barrier: every Task in wave N has only accepted predecessors or predecessors in earlier waves. Tasks
within a wave have no schedule-constraint edge between them.

Actual task durations will vary. When a lane becomes idle, it may pull a Task from a later wave only
after the controller recomputes readiness from accepted evidence and confirms a non-overlapping path
lease. Pulling a Task never allows another Task to bypass an unfinished predecessor. The controller
records the reassignment; this document need not be edited for ordinary dynamic dispatch.

### 3.4 Path isolation

Before execution, the Planner declares exact created, edited and deleted paths. The controller
compares that set with all active leases. An overlap blocks dispatch unless the shared path is
explicitly deferred to the serialized integration step. Directory globs, inferred ownership and
“unlikely to conflict” are not sufficient.

Common conflict points include domain READMEs, the canonical phased-plan checkbox and accepted
commit field, baseline/path/requirement/usage indexes, entry-point declarations, lock files and
generated contract artifacts. These paths must have one writer at a time. Semantic conflicts are
returned to Planner; they are never resolved mechanically.

## 4. Lane and integration lifecycle

For each ready wave:

1. The controller snapshots accepted `main`, recomputes readiness and allocates up to one Task to
   each free lane.
2. Codex, Gemini and ZCode work only in their isolated worktrees and exact path leases.
3. Each lane completes planning, gated execution, focused validation and a draft review result.
4. Completed drafts enter one deterministic integration queue, ordered first by dependency
   criticality and then by numeric Task ID unless a recorded safety reason overrides it.
5. The integration step refreshes the Task onto latest accepted `main` using the separately ratified
   mechanism, reconciles serialized shared files and reruns every affected test and usage command.
6. A fresh Reviewer verifies the refreshed diff. Earlier review of the draft is not acceptance
   evidence after any refresh or conflict correction.
7. Only the accepted Task is committed and merged. The controller then publishes its evidence,
   releases its path leases and recomputes the ready queue for all lanes.

An agent may begin another non-overlapping ready draft while its completed draft waits in the
integration queue only if the ratified controller can preserve separate Task/session state. Queue
waiting never permits a lane to modify the waiting draft.

## 5. Failure and rescheduling rules

- **Planner or external blocker:** retain the Task and lease state, stop only its dependency closure
  and dispatch unrelated ready work to free lanes.
- **Executor blocker or Reviewer changes requested:** keep correction iterations inside the same
  Task conversation and do not mark its successors ready.
- **Path collision:** keep the higher-criticality ready Task; return the other to the ready queue.
- **Stale baseline or integration conflict:** invalidate prior acceptance claims, refresh through the
  ratified mechanism, rerun affected validation and obtain a fresh review.
- **Agent unavailable:** release only leases for work proved unchanged or safely checkpointed, then
  reassign through a fresh canonical prompt. Conversation memory is not a handoff artifact.
- **Failed phase checkpoint:** block the milestone and all work that depends on that checkpoint;
  independent work may continue only when the schedule and owning requirements permit it.
- **Security, credential, live-action or destructive-authority uncertainty:** fail closed. Parallel
  execution grants no additional authority.

## 6. Three-lane schedule

### 6.1 Accepted before this schedule

| Task | Feature |
| --- | --- |
| 1.01 | FEAT-UI-COMPOSE_WORKSPACE |
| 1.02 | FEAT-UI-TYPED_BACKEND |
| 1.03 | FEAT-WS-MANAGE_WORKSPACES |
| 1.04 | FEAT-WS-MANAGE_ACCOUNTS |
| 1.05 | FEAT-PLUG-DECLARE_MANIFESTS |
| 1.06 | FEAT-UI-VIEW_COLLECTIONS |
| 1.07 | FEAT-UI-REVIEW_DRAFTS |
| 1.09 | FEAT-WS-EXECUTE_PERSISTENCE |

### 6.2 Open-task seed waves

| Wave | Codex | Gemini | ZCode |
| ---: | --- | --- | --- |
| 1 | 1.08 FEAT-IFACE-SERVE_API_EVENTS | 1.10 FEAT-WS-SECURE_LOCAL_ACCESS | 1.11 FEAT-WS-ADMINISTER_SETTINGS |
| 2 | 1.12 FEAT-PLUG-REGISTER_CONTRIBUTIONS | 1.13 FEAT-IFACE-OPERATE_IDENTITY | 1.14 FEAT-ORCH-RESERVE_RESOURCES |
| 3 | 1.15 FEAT-AGT-ENFORCE_MANDATE | 1.16 FEAT-UI-SESSION_ACCESS | 1.17 FEAT-WS-MANAGE_ARTIFACTS |
| 4 | 1.18 FEAT-ORCH-MANAGE_JOBS | 1.19 FEAT-AGT-OPERATE_RUNS | 1.20 FEAT-AGT-REGISTER_ROLES |
| 5 | 1.21 FEAT-WS-BUILD_DIAGNOSTICS | 1.22 FEAT-ORCH-EXECUTE_LOCAL_WORK | 1.23 FEAT-AGT-GOVERN_TOOL_CALLS |
| 6 | 1.24 FEAT-AGT-INVOKE_MODELS | 1.25 FEAT-IFACE-OPERATE_SETTINGS | 1.26 FEAT-IFACE-OPERATE_JOBS |
| 7 | 1.27 FEAT-UI-WORKSPACE_NAVIGATION | 1.28 FEAT-UI-SYSTEM_SETTINGS | 1.29 FEAT-UI-RUN_MONITOR |
| 8 | 1.30 FEAT-UI-DEBUG_CONSOLE | 2.01 FEAT-CAT-CATALOG_INSTRUMENTS | 2.02 FEAT-CAT-DEFINE_SESSIONS |
| 9 | 2.03 FEAT-BRK-METATRADER | 2.04 FEAT-BRK-CTRADER | 2.05 FEAT-BRK-BINANCE |
| 10 | 2.06 FEAT-BRK-DUKASCOPY | 2.07 FEAT-BRK-YAHOO | 2.08 FEAT-BRK-RESOLVE |
| 11 | 2.09 FEAT-DATA-MARKET_DATA_STORE | 2.10 FEAT-CAT-MAP_PROVIDERS | 2.11 FEAT-CAT-DEFINE_TRADING_RULES |
| 12 | 2.12 FEAT-CAT-CONVERT_CURRENCIES | 2.13 FEAT-DATA-RESOLVE_QUALITY | 2.14 FEAT-DATA-AGGREGATE_BARS |
| 13 | 2.15 FEAT-DATA-MANAGE_RETENTION | 2.16 FEAT-DATA-NORMALIZE_TICKS | 2.17 FEAT-DATA-GENERATE_SCENARIOS |
| 14 | 2.18 FEAT-DATA-TRACK_MARKET_NEWS | 2.19 FEAT-DATA-INGEST_HISTORY | 2.20 FEAT-DATA-BIND_RUN_DATA |
| 15 | 2.21 FEAT-DATA-STREAM_MARKET_EVENTS | 2.22 FEAT-CAT-MANAGE_UNIVERSES | 2.23 FEAT-DATA-ALIGN_SERIES |
| 16 | 2.24 FEAT-DATA-SYNC_CONNECTORS | 2.25 FEAT-DATA-PREPARE_PROFILES | 2.26 FEAT-DATA-IMPORT_QUANTDATA |
| 17 | 2.27 FEAT-CAT-EXCHANGE_CATALOGUE | 2.28 FEAT-DATA-IMPORT_INDICATORS | 2.29 FEAT-DATA-BROWSE_REFERENCE |
| 18 | 2.30 FEAT-IFACE-OBSERVE_MARKET_REFERENCE | 3.01 FEAT-IND-CALCULATE_TREND | 3.02 FEAT-IND-CALCULATE_MOMENTUM |
| 19 | 2.31 FEAT-UI-DATA_MANAGER | 2.32 FEAT-UI-MARKET_CHARTS | 3.03 FEAT-IND-CALCULATE_VOLATILITY |
| 20 | 3.04 FEAT-IND-CALCULATE_VOLUME_FLOW | 3.05 FEAT-IND-DETECT_CANDLE_PATTERNS | 3.06 FEAT-IND-TRANSFORM_SERIES |
| 21 | 3.07 FEAT-STRAT-DEFINE_AST | 4.01 FEAT-UI-PERFORMANCE_LAB | 4.02 FEAT-RSK-SIZE_POSITIONS |
| 22 | 3.08 FEAT-STRAT-CATALOG_BLOCKS | 3.09 FEAT-STRAT-CONFIGURE_CHARTS | 3.10 FEAT-STRAT-MODEL_ATM_EXITS |
| 23 | 3.11 FEAT-STRAT-EDIT_TEMPLATES | 3.12 FEAT-STRAT-DEFINE_INDICATORS | 3.13 FEAT-STRAT-COMPILE_STRATEGIES |
| 24 | 3.14 FEAT-STRAT-VERSION_STRATEGIES | 3.15 FEAT-STRAT-GENERATE_CODE | 4.03 FEAT-RSK-ASSESS_RESEARCH_RISK |
| 25 | 3.16 FEAT-STRAT-EXCHANGE_STRATEGIES | 4.04 FEAT-TRD-MANAGE_EXECUTION_SESSIONS | 4.05 FEAT-TRD-MODEL_EXECUTION_POLICIES |
| 26 | 3.17 FEAT-IFACE-OPERATE_STRATEGIES | 4.06 FEAT-SIM-MODEL_TICKS | 4.07 FEAT-ANA-COMPUTE_METRICS |
| 27 | 3.18 FEAT-UI-STRATEGY_STUDIO | 4.08 FEAT-SIM-CONFIGURE_ENGINE | 5.01 FEAT-UI-SESSION_CONTEXT |
| 28 | 4.09 FEAT-SIM-EXECUTE_TICKS | 5.02 FEAT-WS-MANAGE_CONVERSATIONS | 6.01 FEAT-STRAT-ACCEPT_PROPOSALS |
| 29 | 4.10 FEAT-SIM-COMMIT_RESULTS | 6.02 FEAT-RES-GOVERN_CAMPAIGNS | 8.01 FEAT-STRAT-DEFINE_SEARCH_SPACES |
| 30 | 4.11 FEAT-IFACE-OPERATE_SIMULATIONS | 4.12 FEAT-SIM-CACHE_EVALUATIONS | 4.13 FEAT-ANA-QUERY_RESULTS |
| 31 | 4.14 FEAT-ANA-DATABANK_MEMBERSHIP | 4.15 FEAT-ANA-ANALYZE_TRADES | 4.16 FEAT-ANA-PROJECT_SERIES |
| 32 | 4.17 FEAT-ANA-COMPARE_RESULTS | 4.18 FEAT-ANA-EXCHANGE_RESULTS | 5.03 FEAT-AGT-ASSEMBLE_CONTEXT |
| 33 | 4.19 FEAT-IFACE-OPERATE_RESULTS | 5.04 FEAT-AGT-RUN_WORKFLOWS | 6.03 FEAT-RES-DEFINE_PROTOCOLS |
| 34 | 4.20 FEAT-UI-RUN_BACKTEST | 4.21 FEAT-UI-RESEARCH_WORKBENCH | 4.22 FEAT-UI-DATABANK_GRID |
| 35 | 4.23 FEAT-UI-RESULT_OVERVIEW | 4.24 FEAT-UI-TRADE_LIST | 4.25 FEAT-UI-EQUITY_CHART |
| 36 | 4.26 FEAT-UI-TRADE_ANALYSIS | 4.27 FEAT-UI-TRADES_ON_CHART | 5.05 FEAT-AGT-EVALUATE_PROFILES |
| 37 | 5.06 FEAT-AGT-MANAGE_CLAIMS | 6.05 FEAT-RES-GOVERN_HOLDOUTS | 7.01 FEAT-SIM-PERTURB_INPUTS |
| 38 | 5.07 FEAT-AGT-SYNTHESIZE_RESEARCH | 6.06 FEAT-RES-RUN_RESEARCH | 7.02 FEAT-ANA-ANALYZE_DISTRIBUTIONS |
| 39 | 5.08 FEAT-AGT-ASSIST_OPERATOR | 6.04 FEAT-AGT-COMPOSE_STRATEGY_PROPOSALS | 6.07 FEAT-IFACE-OPERATE_RESEARCH |
| 40 | 5.09 FEAT-IFACE-AGENTIC_GATEWAY | 6.08 FEAT-AGT-GOVERN_RESEARCH_SEARCH | 7.03 FEAT-AGT-DELIBERATE_RESEARCH |
| 41 | 5.10 FEAT-UI-CHAT_BOT | 5.11 FEAT-UI-AGENTIC_RUN_INSPECTOR | 6.09 FEAT-AGT-DESIGN_RESEARCH |
| 42 | 6.10 FEAT-AGT-COMPOSE_STRATEGY_SPECS | 7.04 FEAT-RES-TEST_ROBUSTNESS | 8.02 FEAT-RES-RANK_CANDIDATES |
| 43 | 6.11 FEAT-UI-EXECUTE_ORDERS | 7.05 FEAT-UI-ROBUSTNESS_RESULTS | 7.06 FEAT-RES-QUALIFY_RESEARCH |
| 44 | 7.07 FEAT-UI-STRATEGY_RETESTER | 8.03 FEAT-RES-GENERATE_STRATEGIES | 9.01 FEAT-OPT-SEARCH_PARAMETERS |
| 45 | 8.04 FEAT-RES-EVOLVE_STRATEGIES | 9.02 FEAT-OPT-VALIDATE_WALK_FORWARD | 9.03 FEAT-OPT-PERMUTE_PARAMETERS |
| 46 | 8.05 FEAT-UI-STRATEGY_BUILDER | 9.04 FEAT-IFACE-OPERATE_OPTIMIZATION | 10.01 FEAT-POR-COMPOSE_PORTFOLIOS |
| 47 | 9.05 FEAT-UI-PARAMETER_OPTIMIZER | 9.06 FEAT-UI-OPTIMIZATION_RESULTS | 10.02 FEAT-POR-ANALYZE_CORRELATION |
| 48 | 10.03 FEAT-ANA-FILTER_CORRELATION | 10.04 FEAT-POR-OPTIMIZE_WEIGHTS | 10.05 FEAT-POR-SIMULATE_PORTFOLIOS |
| 49 | 10.06 FEAT-POR-ANALYZE_PORTFOLIO_RISK | 10.07 FEAT-POR-MERGE_PORTFOLIOS | 10.08 FEAT-POR-SEARCH_PORTFOLIOS |
| 50 | 10.09 FEAT-AGT-ADVISE_PORTFOLIO | 10.10 FEAT-IFACE-OPERATE_PORTFOLIOS | 11.01 FEAT-TRD-OBSERVE_OUTCOMES |
| 51 | 10.11 FEAT-UI-PORTFOLIO_COMPOSER | 10.12 FEAT-UI-PORTFOLIO_BUILDER | 11.02 FEAT-ORCH-DEFINE_PROJECTS |
| 52 | 11.03 FEAT-ORCH-EXECUTE_UTILITIES | 11.04 FEAT-ORCH-DELIVER_NOTIFICATIONS | 11.05 FEAT-AGT-MANAGE_MEMORY |
| 53 | 11.06 FEAT-ORCH-RUN_PROJECTS | 11.07 FEAT-AGT-CALIBRATE_OUTCOMES | 12.01 FEAT-PLUG-SANDBOX_PERMISSIONS |
| 54 | 11.08 FEAT-IFACE-EDIT_PROJECTS | 12.02 FEAT-PLUG-AUTHOR_PACKAGES | 12.03 FEAT-PLUG-ISOLATE_ANALYSIS |
| 55 | 11.09 FEAT-UI-PROJECT_EDITOR | 12.04 FEAT-PLUG-RENDER_RESULT_PANELS | 12.05 FEAT-STRAT-GENERATE_MQL5 |
| 56 | 12.06 FEAT-STRAT-GENERATE_PYTHON | 12.07 FEAT-ANA-PROVIDE_CUSTOM_ANALYSIS | 12.08 FEAT-PLUG-MANAGE_LIFECYCLE |
| 57 | 12.09 FEAT-PLUG-MAINTAIN_COMPATIBILITY | 12.10 FEAT-AGT-AUTHOR_SANDBOX_ARTIFACTS | 13.01 FEAT-IND-CALCULATE_MARKET_PROFILES |
| 58 | 12.11 FEAT-IFACE-ADMINISTER_CAPABILITIES | 13.02 FEAT-STRAT-DEFINE_ARCHITECTURES | 13.03 FEAT-SIM-SIMULATE_STOCKPICKERS |
| 59 | 12.12 FEAT-UI-CODE_EDITOR | 12.13 FEAT-UI-INDICATOR_TESTER | 13.04 FEAT-UI-ADVANCED_ANALYSIS |
| 60 | 14.01 FEAT-RES-PREPARE_NEURAL_DATASETS | 14.02 FEAT-RES-LABEL_NEURAL_DATA | 14.03 FEAT-RES-INFER_MODELS |
| 61 | 14.04 FEAT-RES-TRAIN_MODELS | 15.01 FEAT-ORCH-MANAGE_REMOTE_WORKERS | 16.01 FEAT-IFACE-AUTOMATE_COMMANDS |
| 62 | 14.05 FEAT-RES-VALIDATE_MODELS | 16.02 FEAT-WS-DISTRIBUTE_APPLICATION | 16.03 FEAT-BRK-DARWINEX |
| 63 | 14.06 FEAT-RES-EXPLAIN_MODELS | 16.04 FEAT-BRK-COINBASE | 16.05 FEAT-BRK-BITFINEX |
| 64 | 14.07 FEAT-UI-NEURAL_RESEARCH | 16.06 FEAT-BRK-POLONIEX | 16.07 FEAT-BRK-CONNECT_MARKET_FEEDS |
| 65 | 16.08 FEAT-STRAT-GENERATE_TARGETS | 16.09 FEAT-ANA-IMPORT_EXTERNAL_LEDGERS | — |
| 66 | 16.10 FEAT-STRAT-IMPORT_SQX | 16.11 FEAT-STRAT-PACKAGE_STRATEGIES | — |
| 67 | 16.12 FEAT-UI-STRATEGY_PACKAGER | — | — |

## 7. Phase checkpoints and release gates

The original phase checkpoint remains owned by the last Task named for that phase in the canonical
plan. Cross-phase overlap in the seed table means only that a later Task's explicit predecessors are
ready; it does not declare the earlier phase or its U milestone complete. Phase-level UI and browser
acceptance remains blocked until its checkpoint Task is accepted.

If an owning requirement imposes a full-phase barrier not represented in the pinned dependency
schedule, add that constraint to the authoritative schedule through an approved Task and regenerate
this table. Do not patch the table alone.

## 8. Capacity and timing

At the user's observed 30 minutes per Task, 197 open Tasks require about 98.5 agent-hours when run
serially. The 67-wave seed has a theoretical draft duration of about 33.5 elapsed hours when all
three lanes remain occupied. This is close to the mathematical lower bound of 66 waves, but it is
not a delivery promise.

Review corrections, uneven Task sizes, full-suite gates, external evidence, shared-path
reconciliation and serialized integration add elapsed time. Measure actual planning, execution,
review, queue and rework durations per Task after the first six waves, then regenerate lane priority
using observed duration and critical-path data. Never reduce validation to preserve the estimate.

## 9. Schedule regeneration and verification

Regenerate this schedule whenever the canonical task set, completion state or dependency schedule
changes materially. A valid regeneration must prove:

- The canonical phased plan contains exactly 205 unique feature Tasks.
- Every canonical Task appears exactly once across the accepted table and open-wave table.
- Accepted Tasks are not dispatched again.
- Every open Task appears in exactly one lane and one wave.
- No wave contains more than three Tasks or assigns two Tasks to one lane.
- Every schedule predecessor is accepted or assigned to an earlier wave.
- Each phase checkpoint and operation-qualification obligation retains its canonical owner.
- The source plan, dependency schedule and generation baseline hashes are recorded.

The schedule is an execution optimization only. A stale table may guide discussion, but readiness is
always recomputed from current repository evidence before a Task is activated.

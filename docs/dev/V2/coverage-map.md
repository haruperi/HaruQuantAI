# V2 coverage and legacy dispositions

This is a planning audit appendix. It establishes destinations for V1 scope;
it does not establish application completion or numerical parity. Read the short
[feature plan](product-features.md) and [delivery milestones](delivery-plan.md)
for implementation work. The CSV rows are not 366 new tickets. The [implementation checklist](implementation_checklist.md)
tracks 72 capability tasks in thirteen detailed phases. Its task links now serve as
the CSV implementation destinations; every old row remains auditable.

## Source boundary

Baseline HEAD: `6ac87d2a4dfb111ef8ca03632aeffb9a8de7edec`, reviewed 2026-10-07.
Sources: [roadmap](../V1/sqx-full-application-roadmap.md), all nineteen documents in
`docs/dev/V1`, [master checklist](../V1/implementation_checklist.md),
[baseline audit](../V1/sqx145-baseline-audit.md) and [evidence procedure](../evidence/README.md).

Exact source inventory: **366 numbered tasks**, **289 archive allocations** and
**49 named resource proposals**. Every archive/resource feature identity has a
corresponding numbered task; no proposal is missing from the crosswalk. The 338
archive/resource allocations plus 28 prerequisite/integration/release tasks produce
the 366 rows. There is one inherited phase-allocation discrepancy: the roadmap
assigns `j64/lib/jrt-fs.jar` / `FEAT-HOST-JRT-FS` to P00, while task 1.18 is in P01.
Keep the P00 inventory allocation and P01 target-runtime qualification distinct;
the CSV records both phases and V2 preserves both allocations; the archive move only rebases source references.
Full class/member metadata remains in the original reference tooling;
V2 does not duplicate 51,713 raw class entries as implementation requirements.

## Phase coverage

| V1 phase | Tasks | Primary V2 destination | Behavior retained |
| --- | ---: | --- | --- |
| P01 Host foundation | 38 | F01; P00 reference gate | Bootstrap, settings, logs, diagnostics and Python runtime packaging |
| P02 Host services | 37 | F01; MCP boundary in F12 | Discovery, sessions/transport, jobs, resources and persistence |
| P03 Data Manager | 14 | F02 | Instruments, brokers, sessions, datasets, baskets, custom data/COT and UI actions/help |
| P04 Data ingestion | 23 | F02 | All listed sources, files, COT updates and import/download logs |
| P05 Strategy primitives | 7 | F03 | Blocks/constants/snippets/indicator families, COT and profile kernels |
| P06 Simulation | 5 | F04 | Execution/accounting, advanced management, sizing, stock selection and platform profiles |
| P07 Authoring/export | 18 | F03; AlgoCloud lifecycle in F12 | Editors, resource/testing, native formats and generated code/packages |
| P08 Results/export | 40 | F05 | Databanks, all named result/trade/series views and report/data/image exports |
| P09 Builder | 15 | F06 | Generation/improvement, genetic methods, rankings/fitness and dashboard |
| P10 Optimizer/WF | 10 | F07 | Search/sequential/profile/permutation and walk-forward results |
| P11 Robustness | 18 | F07 | All cross-checks, automatic retest and actual pass/fail results |
| P12 Portfolios | 12 | F08 | Composer/Master, manual/automatic search and aggregate/correlation results |
| P13 Custom Projects | 46 | F09 | All settings/tasks/conditions, side-effect boundaries and Q-callable workflows |
| P14 Grid | 13 | F10 | Compatible worker protocol/placement, Grid Control/Test and recovery |
| P15 Neural | 3 | F11 | Training, model artifacts and qualified inference |
| P16 Connections | 6 | F12 | Test/live-test/MT4, connection management and segregated trading authority |
| P17 Distribution | 22 | F01/F03/F05/F12 | Shell/themes/help, editor/chart/image equivalents, Business/MCP and Marketplace |
| P18 Qualification | 8 | Shared release gate | Traceability, independent behavior, journeys, failures, removal, limits and distribution |
| P19 Q assistant | 31 | F13 | AI core gate, chat/memory/schedules/Python/completion and all 17 procedures |

## Reading the task map

[legacy-task-map.csv](legacy-task-map.csv) has exactly one row per original task.
Columns retain the exact task ID/title/feature, source document, archive locator
when applicable, roadmap allocation phase, primary destination, host capability,
disposition, secondary consumers, V2 reference, rationale and planning status.

| Disposition | Rows | Meaning |
| --- | ---: | --- |
| retain | 147 | Product operation remains explicit within its V2 owner |
| merge | 87 | Settings/command/task/view or workflow wrapper becomes part of the same operation |
| replace | 111 | Standard/library or narrow target adapter supplies the consumed behavior; no framework clone |
| jvm-only | 11 | Java runtime/annotation/reflection mechanics are omitted; target invariants and consumers remain explicit |
| prerequisite | 2 | Existing P00 reference gate or Q-specific evidence/authority gate |
| release | 8 | Shared whole-product qualification, not a domain implementation |

Destinations contain 357 product-group rows, one P00 reference row and eight release
rows. The Q prerequisite remains under F13. Product-group row counts are F01 84,
F02 37, F03 25, F04 5, F05 43, F06 15, F07 28, F08 12, F09 46, F10 13, F11 3,
F12 15 and F13 31. These counts describe inherited planning units, not effort or
feature size. H10 security is explicitly cross-cutting in the old task consumers;
it now has a first-class host definition rather than an invented extra legacy row.

Every disposition is proposed pending the actual owning implementation plan. Even
a JVM-only row must preserve accepted external behavior or runtime guards, if the
consumer audit finds them. Format/protocol/numerical compatibility is never waived
merely because a library is replaced. No V1 checkbox changes through this map.

## Specialist coverage checks

| Scope easy to overlook | V2 implementation/acceptance destination |
| --- | --- |
| COT catalog/five fields/releases and update/export failures | F02 custom data/provider contract; F03 independent COT signal/time/shift vectors |
| COT emergency exits, profile/TPO/Delta/POC/value-area and AnchoredVWAP | F03 per-concept kernels, boundary/tie/session vectors and per-engine availability |
| NinjaTrader backtest engine versus export | F04 separate engine evidence/profile; F03 native code/package qualification; templates do not prove the engine |
| NinjaTrader indicator package and session import | F03 dependency/version/native vectors; F02 session compatibility and overwrite/skip policy |
| All providers including exchange variants | F02 enumerated checklist and per-provider availability/protocol acceptance |
| Stock picking and SP views | F04 universe/ranking/rebalance/accounting; F05 stock-picker projections |
| SQ3/SQ4 and AlgoCloud | F03 bounded format/round-trip adapters; F12 remote lifecycle/entitlements |
| PDF, HTML, spreadsheets, trades and image transformations | F05 common report inputs plus qualified output adapters, layout/encoding/totals checks |
| Benchmark/daily/drawdown/volatility/volume charts and correlation filtering | F05 named series and shared metric/correlation semantics |
| Monte Carlo manipulation versus retest; extra markets; higher precision; What-If | F07 distinct scenario contracts, data availability, seeds and denominators |
| Sequential/profile/system permutation/WF optimization and matrix checks | F07 shared methods with explicit window/ordering/tie semantics |
| Project conditions, go-to/wait/stop/start and every task family | F09 bounded state machine, defined condition boundaries and reusable task adapters |
| Mass config, scripts, mail, databank clearing and file deletion | F09 exact targets/transactions/lifecycle; H10 distinct scoped side-effect authority |
| Grid protocol/leases/placement and lost workers | F10 remote adapter over H07; local/remote deterministic results and duplicate-output rejection |
| Neural scaling/splits/architecture/model retention and inference | F11 independent training/inference contract; local execution sufficient |
| Business, MCP, terminal/sandbox and live operations | F12 typed integration/availability; H10 denial tests and separate live authority |
| Marketplace install/update/removal | F12 staged manifests/checksums/contained extraction/rollback; H05 lifecycle and retained data |
| Q memory layers, schedules, Python isolation, completion/cache/model/credits | F13 scoped evidence, permissions/budgets, cancellation/replay and isolation qualification |
| All 17 Q procedures | F13 named procedure checklist, actual callable payloads and connected research acceptance |
| Home/help/themes/language/zoom and distribution | F01 shell/preferences with browser semantics and fresh installation checks |
| Retained Chart/MTAnalyzer/Trading additions | F02/F05/F12 owned inputs/outputs; identify normative additions instead of inventing donor provenance |

The existing audit records session overwrite/skip behavior and changed resource
availability. Implementation must inspect those actual policies rather than assume
that archive/file handling or UI labels specify them. Source gaps remain scoped.

## Reference and authority

P00 reference readiness and the approved three-host-service gap disposition are
retained. Universal host defaults/lifecycle may be explicit target decisions through
approved plans. Missing domain algorithms, AI bodies, native profiles and independent
runtime observations still constrain their affected claims and release rows.

V2 neither renames registered FEAT/FR/DEC identities nor replaces
[AGENTS.md](../../../AGENTS.md), [architecture](../../ARCHITECTURE.md) or owning READMEs.
The approved P01 v2 plan in
`.agents/logs/20261007_phase-01-host-foundation/implementation-plan.md` remains
unchanged, including its transport/session/log/settings decisions. A future adoption
plan must reconcile tracking and those contracts; documentation publication alone
cannot supersede them.

Verification of this document set checks unique task keys/titles, archive/resource
bindings, valid destinations, links/anchors, source fingerprints and approved paths.
Independent semantic review checks the specialist table against the detailed tasks.
No runtime, donor execution or numerical-parity pass is claimed by those checks.

## Detailed-plan coverage boundary

The thirteen phase scope matrices retain provider variants, specialist blocks,
native formats/targets, execution profiles, result views/exports, search/check
methods, project tasks/conditions, connection lifecycles and every Q contribution.
Each CSV destination links to a concrete phase task or the shared reference/release
gate. Grouping preserves the original 366 rows and does not certify implementation.

The [V1 archive](../V1/README.md) contains the old phase files directly, the three
roadmap documents and the reference tree under `sqx/`. Active evidence remains
in `docs/dev/evidence`; the [relocation audit](../evidence/sqx145/v1-relocation.json)
records path/hash changes and preserved historical captures.

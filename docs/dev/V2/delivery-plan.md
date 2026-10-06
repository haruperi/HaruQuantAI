# V2 delivery plan

Build a usable workstation in vertical slices. The thirteen [feature groups](README.md)
describe ownership and final scope; these nine milestones describe delivery order.
Dependencies are capability-specific, so unavailable advanced features do not hold
up unrelated local research.

## Milestones

| Milestone | Deliver | Demonstrate completion |
| --- | --- | --- |
| M01 Connected host | F01 bootstrap, logging, diagnostics, preferences, sessions, transport and minimum discovery | Fresh real host; shell/settings/DebugConsole connect; invalid configuration and expiry are visible; clean shutdown/restart |
| M02 Durable market data | F01 durable jobs/resources and required persistence; F02 file import, instruments and sessions | Import independent rows, inspect exact units/time/precision, reload revision, cancel a real import; no active store adoption |
| M03 First research loop | F03 minimal qualified blocks/rule editor/save; F04 one execution profile; F05 databank/trades/equity/basic export | Import -> author -> backtest -> inspect/export; independently reconciled trades/equity; save/reload and unavailable/failure paths |
| M04 Builder | F06 random search, then genetic generation/improvement, ranking and progress | Valid candidate lineage, seeded sampling, accepted fitness/ties, real jobs/cancel and retained outputs |
| M05 Optimization and robustness | F07 parameter search/retest, then sequential/profiles/permutations/WF and every cross-check | Independent window/scenario/threshold vectors; no leakage; inspect actual stored outcomes in both workspaces; automatic-retest integration |
| M06 Portfolios and projects | F08 manual then automatic composition; F09 sequential then bounded conditional/repeating workflows | Reconciled aggregate exposure; build -> retest -> portfolio project; condition/failure/cancel/recovery and denied side effects |
| M07 Domain breadth | Complete F02 providers/custom data/baskets/COT; F03 block/profile/native-format/export families; F04 remaining management/precision/stock/platform behavior; F05 reports/views/exports | Each listed provider, method, format and platform has its own compatibility/availability record and scoped acceptance; no blanket engine/provider support |
| M08 Extensions | F10 remote compute; F11 models; F12 terminal/business/MCP/AlgoCloud/Marketplace; F13 assistant/procedures | Each track's actual connected workflow, independent artifacts and negative gates; resolve selected external/native/dependency requirements |
| M09 Full qualification | Cross-cutting release review of F01-F13, distribution and all accepted scope | Whole application journeys, numerical/format evidence, removal/recovery, resource bounds, tooling and owner-reviewed release matrix |

M01 uses the already approved P01 contract unless the owner approves an iteration.
M02's operational persistence decision needs its own schema/root approval. M03
delivers a useful subset, not a complete clone. M07 can advance incrementally when
the earlier loop is stable, without waiting for every advanced project task.

M08 tracks have independent prerequisites: remote workers require qualified jobs;
models require data/local execution; integrations require their selected consumers;
AI can start with read-only tools before project automation. Neither neural training
nor local research requires grid compute. Optimizing a saved strategy does not
require Builder. Manual portfolio composition does not require all robustness tests.

## Milestone acceptance overview

The [implementation checklist](implementation_checklist.md) is the 72-task tracker.
These nine milestone checks summarize usable journeys and are not extra counted
implementation tasks. Each milestone selects the relevant portions of the thirteen
detailed phases; later specialist rows remain pending full-scope obligations.

### Milestone checks

These are future application milestones; none is completed by publishing V2.

- [ ] M01 Connected host
- [ ] M02 Durable market data
- [ ] M03 First research loop
- [ ] M04 Builder
- [ ] M05 Optimization and robustness
- [ ] M06 Portfolios and projects
- [ ] M07 Domain breadth
- [ ] M08 Extensions
- [ ] M09 Full qualification

Next implementation task: review V2 adoption against the approved P01 plan, then
prepare the exact-path plan for the next connected host slice. The archived [V1 checklist](../V1/implementation_checklist.md) preserves its original
status. Publishing the V2 tracker does not adopt unratified runtime contracts.

## Keep each implementation slice small

1. Choose a concrete user action and read its V2 feature plus the relevant old
   task/evidence references. Inspect consumed bodies/resources and current clients;
   do not repeat an exhaustive crawl for an unrelated capability.
2. Define accepted behavior, exact schemas/defaults/limits, ownership, dependencies,
   parity claims and write paths in the canonical implementation plan. Use descriptive
   behavior FRs rather than an FR for every Java declaration.
3. Obtain the constitution's owner execution approval. Reuse ratified services and
   dependencies; document material changes before implementing them.
4. Implement the operation and settings together; connect its retained UI. Run
   explicit focused pytest paths with `--no-cov`, independent vectors, FR log
   assertions and relevant connected UI cases against an isolated host/store.
5. Record exact commands/results, source/input/output lineage, deviations and
   residuals in the canonical walkthrough. A future adopted tracker changes only
   when the scope actually passes. Commit/release authority remains separate.

Libraries usually receive a short consumer/disposition record, not an independent
UI feature, bespoke fixture corpus and walkthrough for every dependency. Numerical
concepts and external formats still need method-specific evidence and independent
tests. Reuse one documented host lifecycle/failure harness across its consumers.

## Release gates

| Gate | Required evidence |
| --- | --- |
| Coverage and scope truth | Every accepted behavior/method/provider/format/procedure has an owner and outcome; explicit JVM-only dispositions and unavailable/added scope |
| Numerical/format qualification | Independent indicator, ledger, search, WF/MC, portfolio, model and archive/export vectors with per-method tolerances and lineage |
| Real application journeys | Import/author/run/results; Builder/Optimizer/Retester/portfolio/project; grid/model/connector/Business/MCP; COT/native export/session import/Marketplace; Q research record |
| Failure and authority | Schema/permission/session failures, rate/timeout/overflow, cancellation races, worker loss, duplicate attempts, transaction/publication failure and denied external mutations |
| Removal and retention | Idle/running/failed-start disable/unmount/removal/reinstall for accepted contributions; retained artifacts inspectable, unrelated data unchanged, no leaked handles/routes |
| Limits and performance | Recorded dataset/workload sizes, worker counts, memory/CPU/time/output bounds, cancellation latency, deterministic results and responsive large tables/charts |
| Clean distribution | Fresh install/start/stop without donor runtime, valid owned paths/settings, optional services visibly unavailable, dependencies and update/version compatibility |
| Review | Source/lockfile/artifact fingerprints, exact results and residuals; owner-reviewed walkthrough and bounded release/parity statement |

For stabilized application candidates, restore >=80% branch-aware coverage across
retained application source and run the repository's required checks:

```powershell
uv run ruff check app tests scripts
uv run ruff format --check app tests scripts
uv run mypy --explicit-package-bases app tests scripts
uv run pytest --cov=app --cov-branch --cov-report=term-missing
npm --prefix ui run typecheck
npm --prefix ui run test
npm --prefix ui run build
uv run python scripts/ci_check.py
```

These are future candidate commands, not passes reported for V2. Restore/extend
application and connected acceptance harnesses through approved scoped plans;
historical removed checkers are not current tools. Full-suite repetition during
editing is unnecessary. Independent connected tests must use actual outputs rather
than intercepting API success or falling back to fixtures.

Keep four outcomes separate: **implemented target behavior**, **compatible external
format/protocol**, **independently verified SQX behavior**, and **pending/unavailable**.
Static reference validation and application coverage do not establish numerical
parity. Release a named useful cohort when qualified; keep deferred full scope open.
Full SQX feature/parity claims remain blocked by any applicable unresolved evidence,
provider, native platform or AI dependency. Live trading and other irreversible
external actions always retain their distinct owner authorization.

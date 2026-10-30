# AppBuilder — executable work orders

```mermaid
classDiagram
  class GeneticOptions
  class AppBuilderWorkflow
  AppBuilderWorkflow --> GeneticOptions : later integration
```

- **Primary Role:** Configure and run candidate generation using the shared generation engine.
- **Dependencies:** AppCore generation/backtest/contracts; AppCodeEditor blocks; AppRetester checks.
- **Outputs / Downstream Role:** Candidate strategies and their recorded evaluations.
- **Execution boundary:** each READY work order is one tested commit. A BLOCKED work order authorizes no code, placeholder endpoint, UI success state or feature-completion claim. Source evidence below does not authorize choosing missing behavior.
- **Baseline:** `f5c7d12d5715b8ebee55165b8eddad9068f83cb9`; normative work orders; owner review pending. Implementation status belongs only in the domain README.
- **Shared response contract:** existing legacy API adapters preserve `StandardResponse.success(*, message, metadata, data)` and `StandardResponse.failure(*, message, metadata, error)`, `ResponseMetadata` and `StandardError` from canonical `app/core/lib/responses.py`. New instance envelopes use `StandardResponse[T](request_id: str, data: T, revision: int | None = None)` only where the individual order specifies that contract; structured new errors use `app/core/lib/errors.py::DomainError`. Pure helpers return their declared values. Preserve existing callers and translate envelopes only at an explicitly specified compatibility boundary.
- **Path rule:** CREATE paths are exact. No one-file-per-Java-class port, sibling workspace import, copied core engine or alternative file name is allowed.


## Source reassessment authority — 2026-10-30

The [workspace source review](research/workspaces-03-08-source-review.md) adds exact readable context to every blocked complete-contribution order in this file. Its source paths supplement the old Context to Read lists. Shared libraries are available locally; plugin bodies, UI consumers, templates and per-definition fixtures remain separate evidence. A complete-contribution order retains its status until its exact target contract and acceptance cases are specified. New bounded READY suborders below supersede only their named portion.

## Current-code migration audit and execution order

*Evidence:* `OBS-HARU-BLD-REUSE-20261029`. This audit concerns migration suitability; domain README files remain the only implementation-status authority. The source files below are existing code, not permission to regenerate their components. Backend directories `app/workspace/builder/` do not currently exist; a complete backend cannot be marked Direct fit from the React screen.

### Work order BLD-M01: move the existing presentation as one revertible commit

*Feature:* Reuse the current workspace and its owned result/settings contributions without inventing a second UI. **READY after the app/web bootstrap and public host/result slot contracts are published.**
*Context to Read:* this order; every current source/test row below; `ui/package.json`; `ui/tsconfig.json`; `ui/vite.config.ts`; `app/web/workspaces/home/public.ts`; `app/web/workspaces/results/public.ts`. For Results itself, CREATE its `public.ts` as an export boundary only; export only the existing ProjectResults contribution types after Home owns their base slot type. Do not create a different shell.
*Implementation Files:* exact MOVE/ADAPT targets in the table; EDIT only the corresponding existing application route import and workspace registration to use the new entry component. No backend calculation code is authorized by this migration order.

| Current HaruQuantAI location | Target proposed location | Fit / action (migration audit) |
|---|---|---|
| `ui/app/workspace/Builder/builderClient.ts` | `app/web/workspaces/builder/builderClient.ts` | ADAPT: retain transport/cancellation; replace fixed demo graph, demoInputs and provisional /executions mapping after typed run contract is locked |
| `ui/app/workspace/Builder/BuilderWorkspace.tsx` | `app/web/workspaces/builder/BuilderWorkspace.tsx` | DIRECT FIT for presentation; move with local imports rewritten; source parity and backend behavior remain separately qualified |
| `ui/app/workspace/Builder/EngineCharts.tsx` | `app/web/workspaces/builder/EngineCharts.tsx` | DIRECT FIT for presentation; move with local imports rewritten; source parity and backend behavior remain separately qualified |
| `ui/app/workspace/Builder/EnginePanel.tsx` | `app/web/workspaces/builder/EnginePanel.tsx` | DIRECT FIT for presentation; move with local imports rewritten; source parity and backend behavior remain separately qualified |
| `ui/app/workspace/Builder/FitnessEvolutionModal.tsx` | `app/web/workspaces/builder/FitnessEvolutionModal.tsx` | DIRECT FIT for presentation; move with local imports rewritten; source parity and backend behavior remain separately qualified |
| `ui/app/workspace/Builder/fixtures.ts` | `app/web/tests/workspaces/builder/fixtures/fixtures.ts` | TEST-ONLY: move to fixtures; remove production imports during service integration |
| `ui/app/workspace/Builder/FullSettingsView.tsx` | `app/web/workspaces/builder/FullSettingsView.tsx` | DIRECT FIT for presentation; move with local imports rewritten; source parity and backend behavior remain separately qualified |
| `ui/app/workspace/Builder/ProgressDashboard.tsx` | `app/web/workspaces/builder/ProgressDashboard.tsx` | ADAPT: reuse layout; replace timer/mock metrics with owned run/result projection |
| `ui/app/workspace/Builder/results/ResultsCharts.tsx` | `app/web/workspaces/builder/results/ResultsCharts.tsx` | DIRECT FIT for presentation; move with local imports rewritten; source parity and backend behavior remain separately qualified |
| `ui/app/workspace/Builder/results/ResultsChrome.tsx` | `app/web/workspaces/builder/results/ResultsChrome.tsx` | DIRECT FIT for presentation; move with local imports rewritten; source parity and backend behavior remain separately qualified |
| `ui/app/workspace/Builder/results/resultsFixtures.ts` | `app/web/tests/workspaces/builder/fixtures/results/resultsFixtures.ts` | TEST-ONLY: move to fixtures; remove production imports during service integration |
| `ui/app/workspace/Builder/results/ResultsModals.tsx` | `app/web/workspaces/builder/results/ResultsModals.tsx` | DIRECT FIT for presentation; move with local imports rewritten; source parity and backend behavior remain separately qualified |
| `ui/app/workspace/Builder/results/resultsModel.ts` | `app/web/workspaces/builder/results/resultsModel.ts` | ADAPT: retain pure draft operations; preview serialization/defaults are not SQX persistence or engine settings |
| `ui/app/workspace/Builder/results/tabs/ConditionalTabs.tsx` | `app/web/workspaces/builder/results/tabs/ConditionalTabs.tsx` | DIRECT FIT for presentation; move with local imports rewritten; source parity and backend behavior remain separately qualified |
| `ui/app/workspace/Builder/results/tabs/EquityChartTab.tsx` | `app/web/workspaces/builder/results/tabs/EquityChartTab.tsx` | DIRECT FIT for presentation; move with local imports rewritten; source parity and backend behavior remain separately qualified |
| `ui/app/workspace/Builder/results/tabs/OverviewTab.tsx` | `app/web/workspaces/builder/results/tabs/OverviewTab.tsx` | DIRECT FIT for presentation; move with local imports rewritten; source parity and backend behavior remain separately qualified |
| `ui/app/workspace/Builder/results/tabs/SmallTabs.tsx` | `app/web/workspaces/builder/results/tabs/SmallTabs.tsx` | DIRECT FIT for presentation; move with local imports rewritten; source parity and backend behavior remain separately qualified |
| `ui/app/workspace/Builder/results/tabs/SourceCodeTab.tsx` | `app/web/workspaces/builder/results/tabs/SourceCodeTab.tsx` | DIRECT FIT for presentation; move with local imports rewritten; source parity and backend behavior remain separately qualified |
| `ui/app/workspace/Builder/results/tabs/TradeListTab.tsx` | `app/web/workspaces/builder/results/tabs/TradeListTab.tsx` | DIRECT FIT for presentation; move with local imports rewritten; source parity and backend behavior remain separately qualified |
| `ui/app/workspace/Builder/ResultsColumn.tsx` | `app/web/workspaces/builder/ResultsColumn.tsx` | DIRECT FIT for presentation; move with local imports rewritten; source parity and backend behavior remain separately qualified |
| `ui/app/workspace/Builder/ResultsView.tsx` | `app/web/workspaces/builder/ResultsView.tsx` | ADAPT: reuse layout; replace timer/mock metrics with owned run/result projection |
| `ui/app/workspace/Builder/settings/AtmTab.tsx` | `app/web/workspaces/builder/settings/AtmTab.tsx` | DIRECT FIT for presentation; move with local imports rewritten; source parity and backend behavior remain separately qualified |
| `ui/app/workspace/Builder/settings/BuildingBlocksTab.tsx` | `app/web/workspaces/builder/settings/BuildingBlocksTab.tsx` | DIRECT FIT for presentation; move with local imports rewritten; source parity and backend behavior remain separately qualified |
| `ui/app/workspace/Builder/settings/CrossChecksTab.tsx` | `app/web/workspaces/builder/settings/CrossChecksTab.tsx` | DIRECT FIT for presentation; move with local imports rewritten; source parity and backend behavior remain separately qualified |
| `ui/app/workspace/Builder/settings/CustomAnalysisTab.tsx` | `app/web/workspaces/builder/settings/CustomAnalysisTab.tsx` | DIRECT FIT for presentation; move with local imports rewritten; source parity and backend behavior remain separately qualified |
| `ui/app/workspace/Builder/settings/DataTab.tsx` | `app/web/workspaces/builder/settings/DataTab.tsx` | DIRECT FIT for presentation; move with local imports rewritten; source parity and backend behavior remain separately qualified |
| `ui/app/workspace/Builder/settings/GeneticOptionsTab.tsx` | `app/web/workspaces/builder/settings/GeneticOptionsTab.tsx` | DIRECT FIT for presentation; move with local imports rewritten; source parity and backend behavior remain separately qualified |
| `ui/app/workspace/Builder/settings/MoneyManagementTab.tsx` | `app/web/workspaces/builder/settings/MoneyManagementTab.tsx` | DIRECT FIT for presentation; move with local imports rewritten; source parity and backend behavior remain separately qualified |
| `ui/app/workspace/Builder/settings/NotesTab.tsx` | `app/web/workspaces/builder/settings/NotesTab.tsx` | DIRECT FIT for presentation; move with local imports rewritten; source parity and backend behavior remain separately qualified |
| `ui/app/workspace/Builder/settings/PartsToImproveTab.tsx` | `app/web/workspaces/builder/settings/PartsToImproveTab.tsx` | DIRECT FIT for presentation; move with local imports rewritten; source parity and backend behavior remain separately qualified |
| `ui/app/workspace/Builder/settings/RankingTab.tsx` | `app/web/workspaces/builder/settings/RankingTab.tsx` | DIRECT FIT for presentation; move with local imports rewritten; source parity and backend behavior remain separately qualified |
| `ui/app/workspace/Builder/settings/SettingsControls.tsx` | `app/web/workspaces/builder/settings/SettingsControls.tsx` | DIRECT FIT for presentation; move with local imports rewritten; source parity and backend behavior remain separately qualified |
| `ui/app/workspace/Builder/settings/settingsFixtures.ts` | `app/web/tests/workspaces/builder/fixtures/settings/settingsFixtures.ts` | TEST-ONLY: move to fixtures; remove production imports during service integration |
| `ui/app/workspace/Builder/settings/TradingOptionsTab.tsx` | `app/web/workspaces/builder/settings/TradingOptionsTab.tsx` | DIRECT FIT for presentation; move with local imports rewritten; source parity and backend behavior remain separately qualified |
| `ui/app/workspace/Builder/settings/WhatToBuildTab.tsx` | `app/web/workspaces/builder/settings/WhatToBuildTab.tsx` | DIRECT FIT for presentation; move with local imports rewritten; source parity and backend behavior remain separately qualified |
| `ui/app/workspace/Builder/SettingsSummary.tsx` | `app/web/workspaces/builder/SettingsSummary.tsx` | DIRECT FIT for presentation; move with local imports rewritten; source parity and backend behavior remain separately qualified |
| `ui/app/plugins/project/SettingsRankings/FitnessFunction/fitnessFunction.tsx` | `app/web/workspaces/builder/SettingsRankings/FitnessFunction/fitnessFunction.tsx` | DIRECT FIT presentation; ADAPT controller services to canonical result/run projection; preserve local relative imports |
| `ui/app/plugins/project/SettingsRankings/FitnessFunction/FitnessFunctionCtrl.ts` | `app/web/workspaces/builder/SettingsRankings/FitnessFunction/FitnessFunctionCtrl.ts` | DIRECT FIT presentation; ADAPT controller services to canonical result/run projection; preserve local relative imports |
| `ui/app/plugins/project/SettingsRankings/module.ts` | `app/web/workspaces/builder/SettingsRankings/module.ts` | DIRECT FIT presentation; ADAPT controller services to canonical result/run projection; preserve local relative imports |
| `ui/app/plugins/project/SettingsRankings/RankingCtrl.ts` | `app/web/workspaces/builder/SettingsRankings/RankingCtrl.ts` | DIRECT FIT presentation; ADAPT controller services to canonical result/run projection; preserve local relative imports |
| `ui/app/plugins/project/SettingsRankings/styles.css` | `app/web/workspaces/builder/SettingsRankings/styles.css` | DIRECT FIT presentation; ADAPT controller services to canonical result/run projection; preserve local relative imports |
| `ui/app/plugins/project/SettingsRankings/views/ranking.tsx` | `app/web/workspaces/builder/SettingsRankings/views/ranking.tsx` | DIRECT FIT presentation; ADAPT controller services to canonical result/run projection; preserve local relative imports |
| `ui/tests/unit/workspace/Builder/fullSettings.test.ts` | `app/web/tests/workspaces/builder/fullSettings.test.ts` | MOVE existing assertions unchanged; rewrite import paths only; this qualifies current preview behavior, not donor numerical parity |
| `ui/tests/unit/workspace/Builder/progressDashboard.test.ts` | `app/web/tests/workspaces/builder/progressDashboard.test.ts` | MOVE existing assertions unchanged; rewrite import paths only; this qualifies current preview behavior, not donor numerical parity |
| `ui/tests/unit/workspace/Builder/resultsModel.test.ts` | `app/web/tests/workspaces/builder/resultsModel.test.ts` | MOVE existing assertions unchanged; rewrite import paths only; this qualifies current preview behavior, not donor numerical parity |
| `ui/tests/unit/workspace/Builder/resultsView.test.ts` | `app/web/tests/workspaces/builder/resultsView.test.ts` | MOVE existing assertions unchanged; rewrite import paths only; this qualifies current preview behavior, not donor numerical parity |

*Functional Requirements & Implementation:*
- [ ] `BuilderWorkspace()` -> Retain component exports, props, rendered labels, keyboard actions, cancellation/unmount cleanup and CSS behavior from each current source row. Rewrite relative imports to the table targets. Consume shared Home and Results through their `public.ts` exports; do not import another workspace's private module or copy ProjectWorkbench.
- [ ] `BuilderWorkspace()` -> Keep fixture/timer execution explicitly in the existing preview mode until its replacement service work order passes. Moving a screen does not authorize reporting a generated strategy, finished retest, optimized parameter or saved portfolio as a real backend result. The current clients using fixed RSI/demoInputs and `/executions` are adaptation candidates, not verified workspace APIs.
- [ ] `migration import guard` -> Run `rg -n 'ui/app/workspace/Builder|plugins/project/ProjectWorkbench' app/web/workspaces/builder`. Expected exit `1` and no lines. Rewrite migrated tests to their exact target imports; preserve current assertions and test names.
- [ ] `existing tests` -> Before moving, run `npm --prefix ui test -- tests/unit/workspace/Builder` (Portfolio Master uses `tests/unit/workspace/Portfolio/portfolioMaster.test.ts`). After moving run `npm --prefix app/web test -- tests/workspaces/builder` then `npm --prefix app/web run typecheck` then `npm --prefix app/web run build`; all must exit `0`. These commands prove migration behavior only. Record executed command, UTC timestamp and counts in the owner README when actually executed; this order does not mark future validation passed.
*Commit:* `refactor(builder): move owned workspace presentation`. This single commit includes only the listed moves, direct import rewrites and registration change. UI integration work is separate from implementing donor engines.

*Shared results ownership:* ProjectResults and all Results* contribution implementations are owned by AppResults. Builder, Retester, Optimizer and portfolio workspaces register configured contributions; none gets a private copy of trade lists, overview, source-code rendering, correlation or shared engine progress. Shared base workbench remains AppHome.


```json
{
  "id": "OBS-HARU-BLD-REUSE-20261029",
  "classification": "observed",
  "confidence": "high",
  "claim": "Current Builder presentation exists and can be relocated; its README and inspected handlers distinguish preview behavior from backend integration.",
  "sources": [
    {
      "path": "ui/app/workspace/Builder/README.md",
      "sha256": "45bbd996c5d92f59d7a100284dab1cc9a91b9af3a10cff98161a37927b616f67"
    }
  ],
  "target_domain": "app/workspaces/builder",
  "feature_ids": [
    "FEAT-UI-BUILDER_PROGRESS_TAB",
    "FEAT-UI-BUILDER_FULLSETTINGS_TAB",
    "FEAT-UI-BUILDER_RESULTS_TAB"
  ],
  "requirement_ids": [],
  "decision_ids": [],
  "registration_gap": "Register missing FR/DEC IDs in the owning domain README before production implementation; this planning task does not edit registries.",
  "limitations": "Passing current UI tests establishes local preview behavior only. This record does not certify complete donor coverage, numerical parity, native archive compatibility or production service integration.",
  "validation": {
    "status": "passed",
    "executed_at": "2026-10-29T10:13:19.769410+00:00",
    "procedure": "Read the existing runtime files, clients and README listed in the migration table. Run the focused current-workspace UI tests in the combined 13-file/72-test command.",
    "expected_observation": "13 focused UI test files, 72 tests passed; Builder/Retester/Optimizer clients and Composer/Master timers still operate on preview inputs.",
    "actual_observation": "13 focused UI test files, 72 tests passed; Builder/Retester/Optimizer clients and Composer/Master timers still operate on preview inputs.",
    "artifacts": [
      "ui/app/workspace/Builder/README.md@sha256:45bbd996c5d92f59d7a100284dab1cc9a91b9af3a10cff98161a37927b616f67"
    ]
  },
  "repository_commit": "f5c7d12d5715b8ebee55165b8eddad9068f83cb9",
  "review_state": "source-inspected-owner-review-pending",
  "contains_proprietary_source": false,
  "contains_sensitive_data": false,
  "contains_personal_data": false,
  "paraphrased_behavior_only": true,
  "supersedes_records": [],
  "superseded_by": []
}
```

## Phase 1: directly specified behavior

### Work order BLD-001: genetic-options initial configuration
*Feature:* Construct the observed initial GUI configuration as a typed backend value. **READY after test bootstrap.** It is not evidence for GP algorithm behavior or valid parameter bounds.
*Implementation Files:*
- **Donor:** `DONOR_REFERENCE_ROOT/internal/plugins/SettingsGeneticOptions/SettingsGeneticOptionsService.js` (`this.config`).
- **Backend CREATE:** `app/workspaces/builder/genetic_defaults.py`.
- **Frontend:** no file changed; no duplicate constants table is permitted in React.
- **Tests CREATE:** `tests/workspaces/builder/test_genetic_defaults.py`.
*Context to Read:* this feature text; the donor file above; `pyproject.toml`.
*Evidence ID:* `OBS-145-GENETIC-DEFAULTS-001`. Target helper names/guards are normative; the scalar values below are observed.
*Functional Requirements & Implementation:*
- [ ] `GeneticOptions.defaults(*, in_sample_type: int) -> GeneticOptionsDefaults` -> Return a new frozen, slotted dataclass with exactly the fields/defaults below; type each integer as `int` and each boolean as `bool`. Assign `evo_fitness_restart_type` from the required argument. No implicit global constant lookup.
- [ ] `GeneticOptions.defaults(in_sample_type=...)` -> Raise `TypeError("in_sample_type must be an integer")` unless `type(in_sample_type) is int`. Do not add numeric bounds: they are unverified in this work order.
- [ ] `TestGeneticDefaults.test_exact_defaults()` -> Call with `in_sample_type=7`; assert `dataclasses.asdict(result)` equals the entire fixture below. `7` is a test-injected constant, not a claimed SQX enum value.
- [ ] `TestGeneticDefaults.test_immutability()` -> Assert assigning `population_size` raises `dataclasses.FrozenInstanceError`; two calls return equal but distinct instances; `True` and `"7"` raise the exact TypeError.

Exact fixture for `in_sample_type=7`:
```json
{
  "population_size": 5,
  "max_generations": 10,
  "crossover_probability": 50,
  "mutation_probability": 20,
  "show_advanced_settings": false,
  "islands": 10,
  "migration_modulo": 50,
  "migration_rate": 20,
  "init_generation_type": 1,
  "decimation_coef": 1,
  "evo_restart_on_finish": true,
  "evo_restart_on_stagnation": true,
  "evo_fitness_restart_type": 7,
  "evo_stagnation_generations": 30,
  "show_last_generation_databank": false,
  "fresh_blood_replace_similar": true,
  "fresh_blood_replace_weakest": true,
  "fresh_blood_weakest_pct": 10,
  "fresh_blood_weakest_generations": 2,
  "evo_training_validation_ratio": 50
}
```
The donor's `condGridInstance` is a runtime widget reference and is deliberately absent from this serializable defaults helper; it is not a persisted strategy field. No other observed scalar field may be dropped or renamed differently.
*Done command:* `uv run python -m pytest tests/workspaces/builder/test_genetic_defaults.py -q` -> exit `0`; exact-value, fresh-instance, frozen-instance and two invalid-type cases pass.
*Commit:* `feat(builder): define observed genetic option defaults`. Only the two CREATE files belong in this commit.

## Phase 2: complete module scope not yet executable

Each module below is retained in full scope. Its proposed files are reserved names, not permission to fill missing semantics. The senior planner must issue a revised READY order with complete signatures, literals and expected results before an executor starts that module. No acceptance test command can prove an unspecified contract; therefore blocked modules have no implementation commit.

### `AppBuilder` — BLOCKED-NOT-EXECUTABLE

*Source reassessment — 2026-10-30:* [Exact available source and declarations](research/workspaces-03-08-source-review.md#appbuilder). Readable shared-library context is now available in `DONOR_REFERENCE_ROOT/internal/libs/`; this removes the shared-bytecode-access obstacle, but does not by itself release this complete-workflow order. Located 1 current plugin JavaScript files and 0 previously recovered primary Java files for `AppBuilder`. The linked review replaces carrier-only lookup as the research starting point; original unresolved target-model and acceptance gates below remain in force.

*Feature:* Full `AppBuilder` behavior; this is not completed by the helper commit above.
*Implementation Files (reserved, no code authorized):*
- **Donor:** `DONOR_REFERENCE_ROOT/internal/plugins/AppBuilder`.
- **Backend:** `app/workspaces/builder/app_builder.py`.
- **Frontend:** `app/web/workspaces/builder/BuilderWorkspace.tsx`.
- **Backend tests:** `tests/workspaces/builder/test_app_builder.py`.
- **Frontend tests:** `app/web/tests/builder/AppBuilder.test.tsx`.
*Context to Read:* `DONOR_REFERENCE_ROOT/internal/plugins/AppBuilder/module.js`.
*Evidence and limit:* `OBS-145-GENETIC-DEFAULTS-001` establishes only the READY behavior described above, not this module's full workflow. Literal frontend request vocabulary observed during this pass: No literal request action was established by the inspected frontend service declarations.
*Exact unresolved contract:* The full action request/response schema, state transitions, persisted fields/defaults and invalid-operation behavior are not locked to independent fixtures.
*Executor action:* do not create the reserved files, signatures, constants, schemas or test expectations for this module. Report this feature heading and the exact unresolved contract to the senior planner. Do not replace the missing contract with a conventional implementation.
*Release condition:* a later work order cites a verbatim behavior evidence ID for `AppBuilder`, fixes every input/output/default/error/persistence transition, provides numerical or state fixtures, and names test commands expected to exit `0`. A source directory or action-name list alone does not meet this condition.

### `FitnessMethodStrategyResult` — BLOCKED-NOT-EXECUTABLE

*Source reassessment — 2026-10-30:* [Exact available source and declarations](research/workspaces-03-08-source-review.md#fitnessmethodstrategyresult). Readable shared-library context is now available in `DONOR_REFERENCE_ROOT/internal/libs/`; this removes the shared-bytecode-access obstacle, but does not by itself release this complete-workflow order. Located 3 current plugin JavaScript files and 0 previously recovered primary Java files for `FitnessMethodStrategyResult`. The linked review replaces carrier-only lookup as the research starting point; original unresolved target-model and acceptance gates below remain in force.

*Feature:* Full `FitnessMethodStrategyResult` behavior; this is not completed by the helper commit above.
*Implementation Files (reserved, no code authorized):*
- **Donor:** `DONOR_REFERENCE_ROOT/internal/plugins/FitnessMethodStrategyResult`.
- **Backend:** `app/workspaces/builder/fitness_method_strategy_result.py`.
- **Frontend:** `app/web/workspaces/builder/FitnessMethodStrategyResult.tsx`.
- **Backend tests:** `tests/workspaces/builder/test_fitness_method_strategy_result.py`.
- **Frontend tests:** `app/web/tests/builder/FitnessMethodStrategyResult.test.tsx`.
*Context to Read:* `DONOR_REFERENCE_ROOT/internal/plugins/FitnessMethodStrategyResult/FitnessMethodStrategyResultService.js`; `DONOR_REFERENCE_ROOT/internal/plugins/FitnessMethodStrategyResult/module.js`.
*Evidence and limit:* `OBS-145-GENETIC-DEFAULTS-001` establishes only the READY behavior described above, not this module's full workflow. Literal frontend request vocabulary observed during this pass: `fitnessMethodStrategyResult/list`
*Exact unresolved contract:* Exact metric expression, value-type mapping, weight normalization, missing-value policy and independently computed expected scores are not locked.
*Executor action:* do not create the reserved files, signatures, constants, schemas or test expectations for this module. Report this feature heading and the exact unresolved contract to the senior planner. Do not replace the missing contract with a conventional implementation.
*Release condition:* a later work order cites a verbatim behavior evidence ID for `FitnessMethodStrategyResult`, fixes every input/output/default/error/persistence transition, provides numerical or state fixtures, and names test commands expected to exit `0`. A source directory or action-name list alone does not meet this condition.

### `ServletBuilder` — BLOCKED-NOT-EXECUTABLE

*Source reassessment — 2026-10-30:* [Exact available source and declarations](research/workspaces-03-08-source-review.md#servletbuilder). Readable shared-library context is now available in `DONOR_REFERENCE_ROOT/internal/libs/`; this removes the shared-bytecode-access obstacle, but does not by itself release this complete-workflow order. Located 1 current plugin JavaScript files and 0 previously recovered primary Java files for `ServletBuilder`. The linked review replaces carrier-only lookup as the research starting point; original unresolved target-model and acceptance gates below remain in force.

*Feature:* Full `ServletBuilder` behavior; this is not completed by the helper commit above.
*Implementation Files (reserved, no code authorized):*
- **Donor:** `DONOR_REFERENCE_ROOT/internal/plugins/ServletBuilder`.
- **Backend:** `app/workspaces/builder/servlet_builder.py`.
- **Frontend:** `app/web/workspaces/builder/ServletBuilder.tsx`.
- **Backend tests:** `tests/workspaces/builder/test_servlet_builder.py`.
- **Frontend tests:** `app/web/tests/builder/ServletBuilder.test.tsx`.
*Context to Read:* `DONOR_REFERENCE_ROOT/internal/plugins/ServletBuilder/module.js`.
*Evidence and limit:* `OBS-145-GENETIC-DEFAULTS-001` establishes only the READY behavior described above, not this module's full workflow. Literal frontend request vocabulary observed during this pass: No literal request action was established by the inspected frontend service declarations.
*Exact unresolved contract:* Exact run-request settings, engine capability selection, candidate/result acceptance, stop/pause/resume transitions and error/partial-result semantics are not locked.
*Executor action:* do not create the reserved files, signatures, constants, schemas or test expectations for this module. Report this feature heading and the exact unresolved contract to the senior planner. Do not replace the missing contract with a conventional implementation.
*Release condition:* a later work order cites a verbatim behavior evidence ID for `ServletBuilder`, fixes every input/output/default/error/persistence transition, provides numerical or state fixtures, and names test commands expected to exit `0`. A source directory or action-name list alone does not meet this condition.

### `SettingsBlocks` — BLOCKED-NOT-EXECUTABLE

*Source reassessment — 2026-10-30:* [Exact available source and declarations](research/workspaces-03-08-source-review.md#settingsblocks). Readable shared-library context is now available in `DONOR_REFERENCE_ROOT/internal/libs/`; this removes the shared-bytecode-access obstacle, but does not by itself release this complete-workflow order. Located 4 current plugin JavaScript files and 0 previously recovered primary Java files for `SettingsBlocks`. The linked review replaces carrier-only lookup as the research starting point; original unresolved target-model and acceptance gates below remain in force.

*Feature:* Full `SettingsBlocks` behavior; this is not completed by the helper commit above.
*Implementation Files (reserved, no code authorized):*
- **Donor:** `DONOR_REFERENCE_ROOT/internal/plugins/SettingsBlocks`.
- **Backend:** `app/workspaces/builder/settings_blocks.py`.
- **Frontend:** `app/web/workspaces/builder/SettingsBlocks.tsx`.
- **Backend tests:** `tests/workspaces/builder/test_settings_blocks.py`.
- **Frontend tests:** `app/web/tests/builder/SettingsBlocks.test.tsx`.
*Context to Read:* `DONOR_REFERENCE_ROOT/internal/plugins/SettingsBlocks/module.js`; `DONOR_REFERENCE_ROOT/internal/plugins/SettingsBlocks/services/BlocksService.js`.
*Evidence and limit:* `OBS-145-GENETIC-DEFAULTS-001` establishes only the READY behavior described above, not this module's full workflow. Literal frontend request vocabulary observed during this pass: `blocks/list` `blocks/loadFromFile` `blocks/saveToFile`
*Exact unresolved contract:* Complete persisted field/default/bounds schema, inheritance/merge rules, enum values and invalid-write behavior are not locked. The READY helper does not supply this complete request contract.
*Executor action:* do not create the reserved files, signatures, constants, schemas or test expectations for this module. Report this feature heading and the exact unresolved contract to the senior planner. Do not replace the missing contract with a conventional implementation.
*Release condition:* a later work order cites a verbatim behavior evidence ID for `SettingsBlocks`, fixes every input/output/default/error/persistence transition, provides numerical or state fixtures, and names test commands expected to exit `0`. A source directory or action-name list alone does not meet this condition.

### `SettingsGeneticOptions` — BLOCKED-NOT-EXECUTABLE

*Source reassessment — 2026-10-30:* [Exact available source and declarations](research/workspaces-03-08-source-review.md#settingsgeneticoptions). Readable shared-library context is now available in `DONOR_REFERENCE_ROOT/internal/libs/`; this removes the shared-bytecode-access obstacle, but does not by itself release this complete-workflow order. Located 3 current plugin JavaScript files and 0 previously recovered primary Java files for `SettingsGeneticOptions`. The linked review replaces carrier-only lookup as the research starting point; original unresolved target-model and acceptance gates below remain in force.

*Feature:* Full `SettingsGeneticOptions` behavior; this is not completed by the helper commit above.
*Implementation Files (reserved, no code authorized):*
- **Donor:** `DONOR_REFERENCE_ROOT/internal/plugins/SettingsGeneticOptions`.
- **Backend:** `app/workspaces/builder/settings_genetic_options.py`.
- **Frontend:** `app/web/workspaces/builder/SettingsGeneticOptions.tsx`.
- **Backend tests:** `tests/workspaces/builder/test_settings_genetic_options.py`.
- **Frontend tests:** `app/web/tests/builder/SettingsGeneticOptions.test.tsx`.
*Context to Read:* `DONOR_REFERENCE_ROOT/internal/plugins/SettingsGeneticOptions/module.js`; `DONOR_REFERENCE_ROOT/internal/plugins/SettingsGeneticOptions/SettingsGeneticOptionsService.js`.
*Evidence and limit:* `OBS-145-GENETIC-DEFAULTS-001` establishes only the READY behavior described above, not this module's full workflow. Literal frontend request vocabulary observed during this pass: No literal request action was established by the inspected frontend service declarations.
*Exact unresolved contract:* Complete persisted field/default/bounds schema, inheritance/merge rules, enum values and invalid-write behavior are not locked. The READY helper does not supply this complete request contract.
*Executor action:* do not create the reserved files, signatures, constants, schemas or test expectations for this module. Report this feature heading and the exact unresolved contract to the senior planner. Do not replace the missing contract with a conventional implementation.
*Release condition:* a later work order cites a verbatim behavior evidence ID for `SettingsGeneticOptions`, fixes every input/output/default/error/persistence transition, provides numerical or state fixtures, and names test commands expected to exit `0`. A source directory or action-name list alone does not meet this condition.

### `SettingsPartsToImprove` — BLOCKED-NOT-EXECUTABLE

*Source reassessment — 2026-10-30:* [Exact available source and declarations](research/workspaces-03-08-source-review.md#settingspartstoimprove). Readable shared-library context is now available in `DONOR_REFERENCE_ROOT/internal/libs/`; this removes the shared-bytecode-access obstacle, but does not by itself release this complete-workflow order. Located 3 current plugin JavaScript files and 0 previously recovered primary Java files for `SettingsPartsToImprove`. The linked review replaces carrier-only lookup as the research starting point; original unresolved target-model and acceptance gates below remain in force.

*Feature:* Full `SettingsPartsToImprove` behavior; this is not completed by the helper commit above.
*Implementation Files (reserved, no code authorized):*
- **Donor:** `DONOR_REFERENCE_ROOT/internal/plugins/SettingsPartsToImprove`.
- **Backend:** `app/workspaces/builder/settings_parts_to_improve.py`.
- **Frontend:** `app/web/workspaces/builder/SettingsPartsToImprove.tsx`.
- **Backend tests:** `tests/workspaces/builder/test_settings_parts_to_improve.py`.
- **Frontend tests:** `app/web/tests/builder/SettingsPartsToImprove.test.tsx`.
*Context to Read:* `DONOR_REFERENCE_ROOT/internal/plugins/SettingsPartsToImprove/module.js`; `DONOR_REFERENCE_ROOT/internal/plugins/SettingsPartsToImprove/PartsToImproveService.js`.
*Evidence and limit:* `OBS-145-GENETIC-DEFAULTS-001` establishes only the READY behavior described above, not this module's full workflow. Literal frontend request vocabulary observed during this pass: No literal request action was established by the inspected frontend service declarations.
*Exact unresolved contract:* Complete persisted field/default/bounds schema, inheritance/merge rules, enum values and invalid-write behavior are not locked. The READY helper does not supply this complete request contract.
*Executor action:* do not create the reserved files, signatures, constants, schemas or test expectations for this module. Report this feature heading and the exact unresolved contract to the senior planner. Do not replace the missing contract with a conventional implementation.
*Release condition:* a later work order cites a verbatim behavior evidence ID for `SettingsPartsToImprove`, fixes every input/output/default/error/persistence transition, provides numerical or state fixtures, and names test commands expected to exit `0`. A source directory or action-name list alone does not meet this condition.

### `SettingsRankings` — BLOCKED-NOT-EXECUTABLE

*Source reassessment — 2026-10-30:* [Exact available source and declarations](research/workspaces-03-08-source-review.md#settingsrankings). Readable shared-library context is now available in `DONOR_REFERENCE_ROOT/internal/libs/`; this removes the shared-bytecode-access obstacle, but does not by itself release this complete-workflow order. Located 6 current plugin JavaScript files and 0 previously recovered primary Java files for `SettingsRankings`. The linked review replaces carrier-only lookup as the research starting point; original unresolved target-model and acceptance gates below remain in force.

*Feature:* Full `SettingsRankings` behavior; this is not completed by the helper commit above.
*Implementation Files (reserved, no code authorized):*
- **Donor:** `DONOR_REFERENCE_ROOT/internal/plugins/SettingsRankings`.
- **Backend:** `app/workspaces/builder/settings_rankings.py`.
- **Frontend:** `app/web/workspaces/builder/SettingsRankings.tsx`.
- **Backend tests:** `tests/workspaces/builder/test_settings_rankings.py`.
- **Frontend tests:** `app/web/tests/builder/SettingsRankings.test.tsx`.
*Context to Read:* `DONOR_REFERENCE_ROOT/internal/plugins/SettingsRankings/FitnessFunction/FitnessFunctionService.js`; `DONOR_REFERENCE_ROOT/internal/plugins/SettingsRankings/module.js`; `DONOR_REFERENCE_ROOT/internal/plugins/SettingsRankings/RankingService.js`.
*Evidence and limit:* `OBS-145-GENETIC-DEFAULTS-001` establishes only the READY behavior described above, not this module's full workflow. Literal frontend request vocabulary observed during this pass: `rankingsettings/getDefaultWFConditions` `project/changeMaxRecords`
*Exact unresolved contract:* Complete persisted field/default/bounds schema, inheritance/merge rules, enum values and invalid-write behavior are not locked. The READY helper does not supply this complete request contract.
*Executor action:* do not create the reserved files, signatures, constants, schemas or test expectations for this module. Report this feature heading and the exact unresolved contract to the senior planner. Do not replace the missing contract with a conventional implementation.
*Release condition:* a later work order cites a verbatim behavior evidence ID for `SettingsRankings`, fixes every input/output/default/error/persistence transition, provides numerical or state fixtures, and names test commands expected to exit `0`. A source directory or action-name list alone does not meet this condition.

### `SettingsWhatToBuild` — BLOCKED-NOT-EXECUTABLE

*Source reassessment — 2026-10-30:* [Exact available source and declarations](research/workspaces-03-08-source-review.md#settingswhattobuild). Readable shared-library context is now available in `DONOR_REFERENCE_ROOT/internal/libs/`; this removes the shared-bytecode-access obstacle, but does not by itself release this complete-workflow order. Located 21 current plugin JavaScript files and 0 previously recovered primary Java files for `SettingsWhatToBuild`. The linked review replaces carrier-only lookup as the research starting point; original unresolved target-model and acceptance gates below remain in force.

*Feature:* Full `SettingsWhatToBuild` behavior; this is not completed by the helper commit above.
*Implementation Files (reserved, no code authorized):*
- **Donor:** `DONOR_REFERENCE_ROOT/internal/plugins/SettingsWhatToBuild`.
- **Backend:** `app/workspaces/builder/settings_what_to_build.py`.
- **Frontend:** `app/web/workspaces/builder/SettingsWhatToBuild.tsx`.
- **Backend tests:** `tests/workspaces/builder/test_settings_what_to_build.py`.
- **Frontend tests:** `app/web/tests/builder/SettingsWhatToBuild.test.tsx`.
*Context to Read:* `DONOR_REFERENCE_ROOT/internal/plugins/SettingsWhatToBuild/module.js`; `DONOR_REFERENCE_ROOT/internal/plugins/SettingsWhatToBuild/views/settings/buildMode/BuildModeService.js`; `DONOR_REFERENCE_ROOT/internal/plugins/SettingsWhatToBuild/views/settings/buildMode/module.js`; `DONOR_REFERENCE_ROOT/internal/plugins/SettingsWhatToBuild/views/settings/conditionsAndPeriods/ConditionsAndPeriodsService.js`.
*Evidence and limit:* `OBS-145-GENETIC-DEFAULTS-001` establishes only the READY behavior described above, not this module's full workflow. Literal frontend request vocabulary observed during this pass: `buildType/listFiles` `buildType/getTemplateConfig` `project/checkTemplateResources`
*Exact unresolved contract:* Complete persisted field/default/bounds schema, inheritance/merge rules, enum values and invalid-write behavior are not locked. The READY helper does not supply this complete request contract.
*Executor action:* do not create the reserved files, signatures, constants, schemas or test expectations for this module. Report this feature heading and the exact unresolved contract to the senior planner. Do not replace the missing contract with a conventional implementation.
*Release condition:* a later work order cites a verbatim behavior evidence ID for `SettingsWhatToBuild`, fixes every input/output/default/error/persistence transition, provides numerical or state fixtures, and names test commands expected to exit `0`. A source directory or action-name list alone does not meet this condition.

### `TaskBuild` — BLOCKED-NOT-EXECUTABLE

*Source reassessment — 2026-10-30:* [Exact available source and declarations](research/workspaces-03-08-source-review.md#taskbuild). Readable shared-library context is now available in `DONOR_REFERENCE_ROOT/internal/libs/`; this removes the shared-bytecode-access obstacle, but does not by itself release this complete-workflow order. Located 4 current plugin JavaScript files and 7 previously recovered primary Java files for `TaskBuild`. The linked review replaces carrier-only lookup as the research starting point; original unresolved target-model and acceptance gates below remain in force.

*Feature:* Full `TaskBuild` behavior; this is not completed by the helper commit above.
*Implementation Files (reserved, no code authorized):*
- **Donor:** `DONOR_REFERENCE_ROOT/internal/plugins/TaskBuild`.
- **Backend:** `app/workspaces/builder/task_build.py`.
- **Frontend:** `app/web/workspaces/builder/TaskBuild.tsx`.
- **Backend tests:** `tests/workspaces/builder/test_task_build.py`.
- **Frontend tests:** `app/web/tests/builder/TaskBuild.test.tsx`.
*Context to Read:* `DONOR_REFERENCE_ROOT/internal/plugins/TaskBuild/BuildTaskService.js`; `DONOR_REFERENCE_ROOT/internal/plugins/TaskBuild/module.js`.
*Evidence and limit:* `OBS-145-GENETIC-DEFAULTS-001` establishes only the READY behavior described above, not this module's full workflow. Literal frontend request vocabulary observed during this pass: `indyTester/calibrate`
*Exact unresolved contract:* Exact run-request settings, engine capability selection, candidate/result acceptance, stop/pause/resume transitions and error/partial-result semantics are not locked.
*Executor action:* do not create the reserved files, signatures, constants, schemas or test expectations for this module. Report this feature heading and the exact unresolved contract to the senior planner. Do not replace the missing contract with a conventional implementation.
*Release condition:* a later work order cites a verbatim behavior evidence ID for `TaskBuild`, fixes every input/output/default/error/persistence transition, provides numerical or state fixtures, and names test commands expected to exit `0`. A source directory or action-name list alone does not meet this condition.

## Phase 3: concrete extension definition work orders — BLOCKED-NOT-EXECUTABLE
*Source reassessment — 2026-10-30:* [Category availability](research/workspaces-03-08-source-review.md#extension-and-export-category-reassessment) verifies primary readable definition paths. The remaining blocker is the absence of an accepted per-definition target contract and independent fixture, not inaccessible library code. WO-BLD-FULL-POSITION below releases the named CloseSize definition; all other Formulas definitions retain individual contract gates. Source file counts do not establish completion or parity.


### `Formulas`
- **Context:** `DONOR_REFERENCE_ROOT/internal/extend/Snippets/SQ/Formulas`; exact current definition count: 19.
- **Blocked reason:** no complete per-definition mapping of target filename, parameter schema, evaluation signature, formula/ordering, boundary behavior and golden fixture exists in this file. The executor is forbidden to choose these.
- **Senior release artifact required:** one work order per definition, with an exact Python file, `Class.method` signature, field/default/error literals and hand-calculated or independently observed test values. Do not register a stub catalogue or port Java classes mechanically.
- **Definition IDs to account for:** `CloseSize/FullPosition.java`, `Price/UseFormula.java`, `Range/ATRBasedValue.java`, `Range/FixedValue.java`, `Range/None.java`, `Range/PriceRange.java`, `RangeLevel/ATRBasedValue.java`, `RangeLevel/FixedValue.java`, `RangeLevel/None.java`, `RangeLevel/PriceLevel.java`, `RangeLevel/PriceRange.java`, `SLPT/ATRBasedValue.java`, `SLPT/FixedValue.java`, `SLPT/None.java`, `SLPT/PctValue.java`, `SLPT/PriceLevel.java`, `SLPT/ValueFromFormula.java`, `Size/DefineOwnSize.java`, `Size/UseGlobalMM.java`.
### `Negater`
- **Context:** `DONOR_REFERENCE_ROOT/internal/extend/Snippets/SQ/Negater`; exact current definition count: 15.
- **Blocked reason:** no complete per-definition mapping of target filename, parameter schema, evaluation signature, formula/ordering, boundary behavior and golden fixture exists in this file. The executor is forbidden to choose these.
- **Senior release artifact required:** one work order per definition, with an exact Python file, `Class.method` signature, field/default/error literals and hand-calculated or independently observed test values. Do not register a stub catalogue or port Java classes mechanically.
- **Definition IDs to account for:** `ActionsNegater.java`, `AndOrNegater.java`, `CBlockNegater.java`, `CDataIndyNegater.java`, `ComparisonsNegater.java`, `ConditionsNegater.java`, `DefaultNegater.java`, `FiboNegater.java`, `FormulaNegater.java`, `FractalNegater.java`, `FunctionsNegater.java`, `OscillatorComparisonsNegater.java`, `PivotsNegater.java`, `UlcerNegater.java`, `UpperLowerNegater.java`.

## Source-backed release: full-position close-size sentinel — WO-BLD-FULL-POSITION — READY

*Evidence:* source-body inspection `OBS-SOURCE-BLD-FULL-POSITION-20261030`. Context: `DONOR_REFERENCE_ROOT/internal/extend/Snippets/SQ/Formulas/CloseSize/FullPosition.java` and `DONOR_REFERENCE_ROOT/internal/extend/Snippets/SQ/Internal/FormulaBlock.java`. The observed formula returns numeric zero regardless of strategy, symbol, price or direction. Zero is a formula sentinel; this order does not authorize a zero-volume order. This releases only this definition from the Formulas category gate.

*Create only:* `app/extend/formulas/close_size/full_position.py`; `tests/extend/formulas/close_size/test_full_position.py`. Local helper has no prerequisite on an unimplemented trading engine. Define class `FullPosition` with `evaluate_formula(self, strategy: object, symbol: str, price: float, direction: int) -> float` returning `0.0`; it must not inspect or mutate strategy or validate/use the other arguments. These Python type annotations are the target adaptation of the observed evaluation signature. No registry descriptor or execution adapter in this commit.

- [ ] `test_returns_zero_for_both_directions` evaluates direction -1 and 1, each yielding float 0.0.
- [ ] `test_does_not_access_strategy` passes an object whose attribute access raises and verifies successful evaluation.
- [ ] `test_has_no_state` calls one instance for two symbols/prices and verifies the same result.

*Acceptance:* `uv run python -m pytest tests/extend/formulas/close_size/test_full_position.py -q` exits 0 with the three named tests. One commit: `feat(formulas): define full-position close-size sentinel`. Full order sizing semantics and all other formulas remain outside this release.

## Source-backed release: PartsToImprove condition labels — WO-BLD-IMPROVEMENT-LABEL — READY

*Evidence:* source-body inspection `OBS-SOURCE-BLD-IMPROVEMENT-LABEL-20261030`; Context: `DONOR_REFERENCE_ROOT/internal/plugins/SettingsPartsToImprove/PartsToImproveService.js#getConditionText`. This releases only pure label selection, not the XML writer or improvement engine.

*Create only:* `app/workspaces/builder/improvement_labels.py`; `tests/workspaces/builder/test_improvement_labels.py`. Define `improvement_label(*, use: bool, action: str | None) -> str`; normalized target action IDs are `add_or_replace`, `add`, `replace` (a target decision; do not equate these strings with donor numeric constants). Do not localize in this helper.

- [ ] When use is false return `Keep existing` for every action.
- [ ] Otherwise `add_or_replace` returns `Keep existing or generate randomly`; `add` returns `Keep existing + generate randomly`; `replace`, None, an empty string and unrecognized actions return `Generate randomly`.
- [ ] Tests `test_disabled_keeps_existing`, `test_add_or_replace`, `test_add`, `test_other_actions_generate` assert these exact strings, with the last test parameterized over replace/None/empty/unknown.

*Acceptance:* `uv run python -m pytest tests/workspaces/builder/test_improvement_labels.py -q` exits 0 and collects seven cases across the four named test functions. One commit: `feat(builder): define improvement condition labels`.

## Embedded evidence

New evidence record; fields are retained verbatim for future supersession:

```json
{
  "id": "OBS-145-GENETIC-DEFAULTS-001",
  "classification": "observed",
  "confidence": "high",
  "claim": "Genetic options service declares the listed scalar initial configuration values; the restart fitness type is taken from the in-sample constant rather than a literal number.",
  "sources": [
    {
      "path": "DONOR_REFERENCE_ROOT/internal/plugins/SettingsGeneticOptions/SettingsGeneticOptionsService.js",
      "sha256": "2368c266a4530174fd25896efa96a9ee598892121344db34836fb481beb1a72c"
    }
  ],
  "target_domain": "app/workspaces/builder",
  "feature_ids": [],
  "requirement_ids": [],
  "decision_ids": [],
  "registration_gap": "The evidence ID is established here; domain feature/requirement registration remains required before committing production code.",
  "limitations": "Direct current source observation. Helper types/names/type-error guards are target decisions; no underlying numerical or end-to-end workflow parity asserted.",
  "validation": {
    "status": "passed",
    "executed_at": "2026-10-29T09:19:49.839676+00:00",
    "procedure": "Read the named source functions and initial configuration blocks; compare every branch/literal used by the helper work order.",
    "expected_observation": "Genetic options service declares the listed scalar initial configuration values; the restart fitness type is taken from the in-sample constant rather than a literal number.",
    "actual_observation": "Genetic options service declares the listed scalar initial configuration values; the restart fitness type is taken from the in-sample constant rather than a literal number.",
    "artifacts": [
      "08-AppBuilder.md#embedded-evidence"
    ]
  },
  "repository_commit": "f5c7d12d5715b8ebee55165b8eddad9068f83cb9",
  "review_state": "source-inspected-owner-review-pending",
  "contains_proprietary_source": false,
  "contains_sensitive_data": false,
  "contains_personal_data": false,
  "paraphrased_behavior_only": true,
  "supersedes_records": [],
  "superseded_by": []
}
```

## Preserved historical finding records

```json
{
  "id": "MAP-001",
  "classification": "observed",
  "confidence": "high",
  "claim": "TaskBuild defines concrete build jobs and GeneticBuildEngine; TaskRetest defines retest task/job classes; TaskOptimize defines optimize task and configuration verifier.",
  "sources": [
    "DONOR_REFERENCE_ROOT/internal/plugins/TaskBuild/TaskBuild.jar",
    "DONOR_REFERENCE_ROOT/internal/plugins/TaskRetest/TaskRetest.jar",
    "DONOR_REFERENCE_ROOT/internal/plugins/TaskOptimize/TaskOptimize.jar"
  ],
  "target_domain": "app/workspaces/builder; app/workspaces/retester; app/workspaces/optimizer",
  "feature_ids": [
    "FEAT-UI-BUILDER_PROGRESS_TAB"
  ],
  "requirement_ids": [],
  "decision_ids": [],
  "related_existing_owners": [
    "ui/app/workspace/Builder/README.md"
  ],
  "registration_gap": "No registered owning feature under proposed architecture; propose domain README registration before implementation.",
  "limitations": "Class definitions and signatures establish placement, not full algorithms or runtime semantics. Shared GP internals remain unresolved.",
  "validation": {
    "status": "passed",
    "procedure": "List archive classes with jar; inspect GeneticBuildEngine signatures with javap.",
    "expected_observation": "Named classes are defined in plugin archives; build engine references shared GP/project interfaces.",
    "executed_at": "2026-10-29T06:23:54.532477+00:00",
    "actual_observation": "TaskBuild defines concrete build jobs and GeneticBuildEngine; TaskRetest defines retest task/job classes; TaskOptimize defines optimize task and configuration verifier.",
    "artifacts": "artifact-manifest.json"
  },
  "repository_commit": "f5c7d12d5715b8ebee55165b8eddad9068f83cb9",
  "review_state": "preliminary-owner-review-pending",
  "contains_proprietary_source": false,
  "contains_sensitive_data": false,
  "contains_personal_data": false,
  "paraphrased_behavior_only": true,
  "supersedes_records": [
    "CHAT-2026-10-29-all-execution-core-proposal"
  ],
  "superseded_by": []
}
```

# Phase 5 — Results and reporting

**Feature group:** F05. **Tasks:** 5. **Status:** proposed; 0 complete.

[Checklist](implementation_checklist.md) · [V2 index](README.md) · [Delivery milestones](delivery-plan.md)

## Objective and boundary

Manage stable databanks and immutable result references with saved view settings. This phase owns the results and reporting capability group. Use the shared host and existing domain operations; settings, execution and presentation belong to the same capability.

**Dependencies:** F01 retained resources/persistence and qualified F04/F07/F08 producer outputs. F03 source-code and F13 completion remain separate owners.

**Delivery:** M03, M07 and M09. Phase numbers identify scope, not a requirement to finish every earlier feature before starting this one. Deliver the smallest connected operation first; pending matrix rows remain full-product obligations.

**Ownership:** proposed semantic owner `app/plugins/analytics`; workspace composition remains in `app/workspace/<workspace>`, and the host owns storage, jobs, resource custody and route mounting. No sibling business imports or plugin SQL. Package/module names below are proposed targets to audit and ratify per task, not newly registered contracts.

## Research and authority

Read [V1 P08](../V1/phase-08-results-databanks-exports.md), [V1 P17](../V1/phase-17-product-distribution.md), the [legacy task map](legacy-task-map.csv), [scope coverage](coverage-map.md), [current inventory](../evidence/p00-inventory.json) and [evidence procedure](../evidence/README.md). The V1 files retain exact archive/resource locators, fingerprints, consumed symbols and source limitations; use the relevant rows instead of recrawling unrelated archives. The sole donor is `SQX_145_REFERENCE_ROOT` (145-dev1). Hash and inspect the selected consumed bodies/resources before deciding defaults or numerical behavior. Signatures and UI labels alone do not establish semantics.

The root [AGENTS.md](../../../AGENTS.md), [architecture](../../ARCHITECTURE.md) and approved P01 contracts remain authoritative. For each implementation slice: audit current source, create an exact-path canonical plan, get owner approval, implement, verify and write a walkthrough. Missing source behavior requires explicit disposition; no copied proprietary implementation or invented SQX parity.

## Scope and acceptance matrix

Each row is a mandatory acceptance set inside its numbered tasks, not another feature/plugin backlog. Mark a task complete only when all of its promised rows are qualified.

| Acceptance set | Tasks | Retained behavior |
| --- | --- | --- |
| Databanks/actions | 5.1 | Rename/bulk rename, correlation filters, columns/views/settings, custom databank/actions and ProjectDatabanks |
| Result projections | 5.2 | Overview, exploration, strategy configuration, SP overview, stock-picker, trade lists/views/analysis and compare |
| Charts | 5.3 | Equity/daily/drawdown/volatility/volume/benchmark; trades-on-price, distributions, profile charts and portfolio correlation |
| Reports/exports | 5.4 | ResultsReport, HTML, PDF, spreadsheets, strategy trades, SVG/browser rendering and image format/scaling transformations |
| Retained surfaces | 5.5 | ProjectResults, custom results plugins/actions, Chart and target-added MTAnalyzer; real owned data/connection inputs required |

## Shared proposed changes and verification rules

- Audit/Create the owning domain README when absent; update it after each accepted capability. Reconcile actual FEAT/FR/DEC identities there; F05 and task numbers are planning labels.
- Compose domain capabilities in the selected workspace with typed attachment; public requests use the host transport. Reuse earlier qualified schemas/services instead of copying modules to satisfy a file list.
- Every proposed Python module follows the canonical module template, explicitly typed APIs and observable FR logs. Test success, failure, cancellation and redaction; never use silent exceptions.
- Proposed tests below are future commands, **not reported passes**. They use isolated stores/resources. Run scoped tests while editing, then required quality/coverage gates for the actual approved runtime scope.
- Retained UI files to audit/connect: [ui/app/workspace/Results/ResultsWorkspace.tsx](../../../ui/app/workspace/Results/ResultsWorkspace.tsx), [ui/app/workspace/Chart/ChartWorkspace.tsx](../../../ui/app/workspace/Chart/ChartWorkspace.tsx), [ui/app/workspace/MTAnalyzer/MTAnalyzerWorkspace.tsx](../../../ui/app/workspace/MTAnalyzer/MTAnalyzerWorkspace.tsx). Preserve existing layouts and meaningful controls.
- After actual UI changes run `npm --prefix ui run typecheck`, `npm --prefix ui run test` and `npm --prefix ui run build`. Fixture-only UI regressions do not replace real backend/UI acceptance.

# 5.1 Databanks, immutable results and saved view settings

## 1. Objective

Manage stable databanks and immutable result references with saved view settings.

## 2. Research and donors

P08 DatabankActions/Views/Rename/custom/project resource contributions.

Use the phase sources and legacy CSV to recover exact donor entries/fingerprints. Write independent input/output expectations before translation. Record missing bodies, target decisions and compatibility limits in source-bound evidence.

## 3. File Changes

- **Create (proposed):** `app/plugins/analytics/databanks.py` — owned implementation of the operations below; reuse an earlier qualified module when appropriate.
- **Create (proposed):** `tests/unit/v2/phase_05/test_databanks.py` — independent contract, failure and FR-log cases for this task.
- **Audit/compose:** the owning README and applicable workspace/client listed above; choose exact existing files in the task plan. Host services remain the only job/resource/persistence authority.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Define databank/result IDs, producer revisions, ownership and retained result compatibility.
- [ ] **Step 2:** Implement add/move/copy/rename/bulk-rename/filter plus custom actions through owned capabilities.
- [ ] **Step 3:** Persist selected columns, sorting, filters and view preferences with revision conflicts; validate unsupported producer/action states.
- [ ] **Acceptance:** implement the independent tests below; retain evidence, owned lifecycle and observable errors in the connected consumer before checking this task.

## 5. Verification and Testing

**Future automated command:** `uv run pytest tests/unit/v2/phase_05/test_databanks.py --no-cov`.

**Independent cases:** Rename collisions, duplicate identity, correlation threshold equality, mixed producers, bulk partial-failure policy and save/reload without result loss.

**Connected acceptance:** use an isolated real host and temporary resources through the declared workspace/consumer. Verify genuine job/resource IDs, visible unavailable/denied/failure states, cancellation and retained lineage after reconnect/reload. Capture expected versus actual results; do not report fixture outputs as runtime behavior.

# 5.2 Statistics, trade projections and result comparisons

## 1. Objective

Project metrics, configurations, trades and comparisons from stored outputs.

## 2. Research and donors

P08 Overview/Explore/StrategyConfig/SPOverview/Stockpicker/TradeList/TradeAnalysis consumers.

Use the phase sources and legacy CSV to recover exact donor entries/fingerprints. Write independent input/output expectations before translation. Record missing bodies, target decisions and compatibility limits in source-bound evidence.

## 3. File Changes

- **Create (proposed):** `app/plugins/analytics/metrics.py` — owned implementation of the operations below; reuse an earlier qualified module when appropriate.
- **Create (proposed):** `app/plugins/analytics/projections.py` — owned implementation of the operations below; reuse an earlier qualified module when appropriate.
- **Create (proposed):** `tests/unit/v2/phase_05/test_metrics.py` — independent contract, failure and FR-log cases for this task.
- **Audit/compose:** the owning README and applicable workspace/client listed above; choose exact existing files in the task plan. Host services remain the only job/resource/persistence authority.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Define each overview, exploration, strategy-config, trade-list/view/analysis, SP and stock-picker projection with units/denominators.
- [ ] **Step 2:** Implement one owner-defined metric/correlation primitive and explicit undefined/nonfinite states.
- [ ] **Step 3:** Support compare/filter/drill-down without recomputing invented trades in the browser.
- [ ] **Acceptance:** implement the independent tests below; retain evidence, owned lifecycle and observable errors in the connected consumer before checking this task.

## 5. Verification and Testing

**Future automated command:** `uv run pytest tests/unit/v2/phase_05/test_metrics.py --no-cov`.

**Independent cases:** Independent known-trade metrics, excluded-trade denominators, empty samples, zero variance, incompatible results and exact reconciliation to run ledgers.

**Connected acceptance:** use an isolated real host and temporary resources through the declared workspace/consumer. Verify genuine job/resource IDs, visible unavailable/denied/failure states, cancellation and retained lineage after reconnect/reload. Capture expected versus actual results; do not report fixture outputs as runtime behavior.

# 5.3 Charts, series, distributions and correlation views

## 1. Objective

Render all retained chart and series views from authoritative projections.

## 2. Research and donors

P08 named equity/result charts, P17 chart/image presentation and retained Chart/profile/correlation views.

Use the phase sources and legacy CSV to recover exact donor entries/fingerprints. Write independent input/output expectations before translation. Record missing bodies, target decisions and compatibility limits in source-bound evidence.

## 3. File Changes

- **Create (proposed):** `app/plugins/analytics/charts.py` — owned implementation of the operations below; reuse an earlier qualified module when appropriate.
- **Create (proposed):** `tests/unit/v2/phase_05/test_charts.py` — independent contract, failure and FR-log cases for this task.
- **Audit/compose:** the owning README and applicable workspace/client listed above; choose exact existing files in the task plan. Host services remain the only job/resource/persistence authority.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Specify equity, daily, drawdown, volatility, volume, benchmark and trade-on-price series plus distributions/profile/correlation views.
- [ ] **Step 2:** Align time/calendars/currency and bound pagination/downsampling with explicit missing-data semantics.
- [ ] **Step 3:** Connect chart controls and custom results plugins to versioned projections; keep numerical definitions shared with metrics.
- [ ] **Acceptance:** implement the independent tests below; retain evidence, owned lifecycle and observable errors in the connected consumer before checking this task.

## 5. Verification and Testing

**Future automated command:** `uv run pytest tests/unit/v2/phase_05/test_charts.py --no-cov`.

**Independent cases:** Independent series values/alignment, missing benchmark, incompatible units, downsample extrema and persisted chart settings; browser charts must match exported data.

**Connected acceptance:** use an isolated real host and temporary resources through the declared workspace/consumer. Verify genuine job/resource IDs, visible unavailable/denied/failure states, cancellation and retained lineage after reconnect/reload. Capture expected versus actual results; do not report fixture outputs as runtime behavior.

# 5.4 Reports, spreadsheets, trades, PDF and image exports

## 1. Objective

Export all retained report, trade, spreadsheet and image families from one report model.

## 2. Research and donors

P08 SaverHTML/PDF/StrategyTrades/POI/XMLBeans/image families and ResultsReport/custom report resources.

Use the phase sources and legacy CSV to recover exact donor entries/fingerprints. Write independent input/output expectations before translation. Record missing bodies, target decisions and compatibility limits in source-bound evidence.

## 3. File Changes

- **Create (proposed):** `app/plugins/analytics/reports.py` — owned implementation of the operations below; reuse an earlier qualified module when appropriate.
- **Create (proposed):** `app/plugins/analytics/exporters.py` — owned implementation of the operations below; reuse an earlier qualified module when appropriate.
- **Create (proposed):** `tests/unit/v2/phase_05/test_reports.py` — independent contract, failure and FR-log cases for this task.
- **Audit/compose:** the owning README and applicable workspace/client listed above; choose exact existing files in the task plan. Host services remain the only job/resource/persistence authority.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Build one validated report-data projection and narrow HTML/PDF/spreadsheet/trade/image adapters.
- [ ] **Step 2:** Specify types/precision, formula policy, escaping, fonts/layout, image encoding/dimensions/scaling and deterministic metadata.
- [ ] **Step 3:** Publish downloadable artifacts with checksums, timeout/cancel behavior and individually approved rendering dependencies.
- [ ] **Acceptance:** implement the independent tests below; retain evidence, owned lifecycle and observable errors in the connected consumer before checking this task.

## 5. Verification and Testing

**Future automated command:** `uv run pytest tests/unit/v2/phase_05/test_reports.py --no-cov`.

**Independent cases:** HTML escaping, spreadsheet types/formula injection policy, trade precision, PDF layout/font checks, image transforms and failure cleanup; verify exports against stored totals.

**Connected acceptance:** use an isolated real host and temporary resources through the declared workspace/consumer. Verify genuine job/resource IDs, visible unavailable/denied/failure states, cancellation and retained lineage after reconnect/reload. Capture expected versus actual results; do not report fixture outputs as runtime behavior.

# 5.5 Connected results and retained analysis surfaces

## 1. Objective

Connect all retained results and analysis surfaces to their owned inputs.

## 2. Research and donors

P08/P17 integration plus retained Chart/MTAnalyzer inventory; target additions are not established donor parity.

Use the phase sources and legacy CSV to recover exact donor entries/fingerprints. Write independent input/output expectations before translation. Record missing bodies, target decisions and compatibility limits in source-bound evidence.

## 3. File Changes

- **Create (proposed):** `app/plugins/analytics/integration.py` — owned implementation of the operations below; reuse an earlier qualified module when appropriate.
- **Create (proposed):** `tests/unit/v2/phase_05/test_integration.py` — independent contract, failure and FR-log cases for this task.
- **Audit/compose:** the owning README and applicable workspace/client listed above; choose exact existing files in the task plan. Host services remain the only job/resource/persistence authority.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Wire Results, databanks, project results, result plugins and Chart to real projections and actions.
- [ ] **Step 2:** Specify MTAnalyzer target-added analysis through F02 data/F12 connection inputs with its own approved contracts.
- [ ] **Step 3:** Connect source-code through F03 and AI completion through F13; expose missing producers rather than fixture success.
- [ ] **Acceptance:** implement the independent tests below; retain evidence, owned lifecycle and observable errors in the connected consumer before checking this task.

## 5. Verification and Testing

**Future automated command:** `uv run pytest tests/unit/v2/phase_05/test_integration.py --no-cov`.

**Independent cases:** Create/reload databank, compare and inspect trades/charts, rename/filter and export through a real host; all projection/export matrix rows need independent acceptance.

**Connected acceptance:** use an isolated real host and temporary resources through the declared workspace/consumer. Verify genuine job/resource IDs, visible unavailable/denied/failure states, cancellation and retained lineage after reconnect/reload. Capture expected versus actual results; do not report fixture outputs as runtime behavior.

## Phase completion gate

- [ ] All 5 numbered tasks and all specialist matrix rows are accepted under their own approved plans.
- [ ] Independent behavioral/numerical/format evidence supports each claimed compatibility scope; missing donor/provider/platform behavior remains explicitly unresolved.
- [ ] Actual backend/UI journey, failures, cancellation, restart/reconnect and scoped removal preserve retained outputs and unrelated work.
- [ ] Owning READMEs, task evidence and the master checklist agree; required Ruff/mypy/tests/coverage and applicable UI gates pass for implemented source.

A milestone subset is usable progress. Whole-product release also requires the [shared release gate](implementation_checklist.md#shared-release-gate). No checkbox is completed by publishing this plan.

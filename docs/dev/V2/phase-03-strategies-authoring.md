# Phase 3 — Strategies and authoring

**Feature group:** F03. **Tasks:** 8. **Status:** proposed; 0 complete.

[Checklist](implementation_checklist.md) · [V2 index](README.md) · [Delivery milestones](delivery-plan.md)

## Objective and boundary

Use one semantic strategy document for editors, generators, simulation and export. This phase owns the strategies and authoring capability group. Use the shared host and existing domain operations; settings, execution and presentation belong to the same capability.

**Dependencies:** F01 resource/discovery/document services; F02 data and F04 for execution tests. Schema/edit/save can precede the full engine.

**Delivery:** M03 and M07. Phase numbers identify scope, not a requirement to finish every earlier feature before starting this one. Deliver the smallest connected operation first; pending matrix rows remain full-product obligations.

**Ownership:** proposed semantic owner `app/plugins/strategy`; workspace composition remains in `app/workspace/<workspace>`, and the host owns storage, jobs, resource custody and route mounting. No sibling business imports or plugin SQL. Package/module names below are proposed targets to audit and ratify per task, not newly registered contracts.

## Research and authority

Read [V1 P05](../V1/phase-05-strategy-primitives.md), [V1 P07](../V1/phase-07-authoring-code-generation.md), [V1 P17](../V1/phase-17-product-distribution.md), the [legacy task map](legacy-task-map.csv), [scope coverage](coverage-map.md), [current inventory](../evidence/p00-inventory.json) and [evidence procedure](../evidence/README.md). The V1 files retain exact archive/resource locators, fingerprints, consumed symbols and source limitations; use the relevant rows instead of recrawling unrelated archives. The sole donor is `SQX_145_REFERENCE_ROOT` (145-dev1). Hash and inspect the selected consumed bodies/resources before deciding defaults or numerical behavior. Signatures and UI labels alone do not establish semantics.

The root [AGENTS.md](../../../AGENTS.md), [architecture](../../ARCHITECTURE.md) and approved P01 contracts remain authoritative. For each implementation slice: audit current source, create an exact-path canonical plan, get owner approval, implement, verify and write a walkthrough. Missing source behavior requires explicit disposition; no copied proprietary implementation or invented SQX parity.

## Scope and acceptance matrix

Each row is a mandatory acceptance set inside its numbered tasks, not another feature/plugin backlog. Mark a task complete only when all of its promised rows are qualified.

| Acceptance set | Tasks | Retained behavior |
| --- | --- | --- |
| Catalog | 3.1/3.2 | Every consumed Snippets/TA-Lib/constants family; formula/default/type/constraint/lookback/missing/shift metadata and generation eligibility |
| Specialist blocks | 3.3 | 67 COT-folder additions and both emergency exits; 32 new VP-folder files and changed kernels; Delta/POC/value-area, TPO and AnchoredVWAP |
| Engine restrictions | 3.3/3.7 | Per-block ForEngine limits: generic VolumeProfile omits NT while selected signals/TPO include NT; independent qualification required |
| Authoring | 3.4/3.5 | AlgoWizard, CodeEditor, custom ProjectResources, import/export and real isolated indicator testing |
| Native formats | 3.6 | SQ3/SQ4 reading, SQ3 writing, accepted unknown-field preservation, AlgoCloud parsed documents |
| Platform export | 3.7 | Every retained template/target from the actual catalog; NinjaTrader8 native .cs, indicator package/version/session dependencies, bar-close behavior and explicit on-tick rejection |

## Shared proposed changes and verification rules

- Audit/Create the owning domain README when absent; update it after each accepted capability. Reconcile actual FEAT/FR/DEC identities there; F03 and task numbers are planning labels.
- Compose domain capabilities in the selected workspace with typed attachment; public requests use the host transport. Reuse earlier qualified schemas/services instead of copying modules to satisfy a file list.
- Every proposed Python module follows the canonical module template, explicitly typed APIs and observable FR logs. Test success, failure, cancellation and redaction; never use silent exceptions.
- Proposed tests below are future commands, **not reported passes**. They use isolated stores/resources. Run scoped tests while editing, then required quality/coverage gates for the actual approved runtime scope.
- Retained UI files to audit/connect: [ui/app/workspace/AlgoWizard/AlgoWizardWorkspace.tsx](../../../ui/app/workspace/AlgoWizard/AlgoWizardWorkspace.tsx), [ui/app/workspace/CodeEditor/CodeEditorWorkspace.tsx](../../../ui/app/workspace/CodeEditor/CodeEditorWorkspace.tsx). Preserve existing layouts and meaningful controls.
- After actual UI changes run `npm --prefix ui run typecheck`, `npm --prefix ui run test` and `npm --prefix ui run build`. Fixture-only UI regressions do not replace real backend/UI acceptance.

# 3.1 Versioned semantic strategy document

## 1. Objective

Use one semantic strategy document for editors, generators, simulation and export.

## 2. Research and donors

P05 snippet/constants/block contracts and P07 strategy servlet consumers.

Use the phase sources and legacy CSV to recover exact donor entries/fingerprints. Write independent input/output expectations before translation. Record missing bodies, target decisions and compatibility limits in source-bound evidence.

## 3. File Changes

- **Create (proposed):** `app/plugins/strategy/documents.py` — owned implementation of the operations below; reuse an earlier qualified module when appropriate.
- **Create (proposed):** `tests/unit/v2/phase_03/test_documents.py` — independent contract, failure and FR-log cases for this task.
- **Audit/compose:** the owning README and applicable workspace/client listed above; choose exact existing files in the task plan. Host services remain the only job/resource/persistence authority.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Define version, rules, typed parameters, block references, input/engine requirements and stable identities.
- [ ] **Step 2:** Validate graph/order/type constraints and qualify supported nodes with clear unsupported errors.
- [ ] **Step 3:** Publish immutable revisions through host repositories; carry data/block/engine version references downstream.
- [ ] **Acceptance:** implement the independent tests below; retain evidence, owned lifecycle and observable errors in the connected consumer before checking this task.

## 5. Verification and Testing

**Future automated command:** `uv run pytest tests/unit/v2/phase_03/test_documents.py --no-cov`.

**Independent cases:** Test invalid types/cycles, missing block/version, constraints, clone/update conflicts and equivalent save/reload semantics.

**Connected acceptance:** use an isolated real host and temporary resources through the declared workspace/consumer. Verify genuine job/resource IDs, visible unavailable/denied/failure states, cancellation and retained lineage after reconnect/reload. Capture expected versus actual results; do not report fixture outputs as runtime behavior.

# 3.2 Blocks, snippets, constants and indicator catalog

## 1. Objective

Implement the complete consumed block and indicator catalog as local evaluators.

## 2. Research and donors

P05 Snippets/TA-Lib/ServletConstants/SettingsBlocks and full scoped resource inventory; a short starter catalog is not full completion.

Use the phase sources and legacy CSV to recover exact donor entries/fingerprints. Write independent input/output expectations before translation. Record missing bodies, target decisions and compatibility limits in source-bound evidence.

## 3. File Changes

- **Create (proposed):** `app/plugins/strategy/blocks.py` — owned implementation of the operations below; reuse an earlier qualified module when appropriate.
- **Create (proposed):** `app/plugins/strategy/indicator_catalog.py` — owned implementation of the operations below; reuse an earlier qualified module when appropriate.
- **Create (proposed):** `tests/unit/v2/phase_03/test_blocks.py` — independent contract, failure and FR-log cases for this task.
- **Audit/compose:** the owning README and applicable workspace/client listed above; choose exact existing files in the task plan. Host services remain the only job/resource/persistence authority.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Inventory all consumed Snippets/TA-Lib/constants families with per-entry formula, defaults, lookback, shifts, missing values, parameter bounds and generation eligibility.
- [ ] **Step 2:** Implement independent evaluators and metadata; test before declaring a block available.
- [ ] **Step 3:** Publish engine/export lowering hooks per qualified entry rather than duplicating indicator logic in each workspace.
- [ ] **Acceptance:** implement the independent tests below; retain evidence, owned lifecycle and observable errors in the connected consumer before checking this task.

## 5. Verification and Testing

**Future automated command:** `uv run pytest tests/unit/v2/phase_03/test_blocks.py --no-cov`.

**Independent cases:** Independent formula/warm-up/shift/equality vectors for every retained entry; invalid periods, insufficient data, nonfinite input and metadata/evaluator mismatch.

**Connected acceptance:** use an isolated real host and temporary resources through the declared workspace/consumer. Verify genuine job/resource IDs, visible unavailable/denied/failure states, cancellation and retained lineage after reconnect/reload. Capture expected versus actual results; do not report fixture outputs as runtime behavior.

# 3.3 COT, market/profile and specialist indicators

## 1. Objective

Retain COT and profile extensions with per-block engine restrictions.

## 2. Research and donors

P05 COT/HighestLowest/VP/TPOProfile/AnchoredVWAP bodies and per-block ForEngine metadata.

Use the phase sources and legacy CSV to recover exact donor entries/fingerprints. Write independent input/output expectations before translation. Record missing bodies, target decisions and compatibility limits in source-bound evidence.

## 3. File Changes

- **Create (proposed):** `app/plugins/indicators/impl/cot.py` — owned implementation of the operations below; reuse an earlier qualified module when appropriate.
- **Create (proposed):** `app/plugins/indicators/impl/profiles.py` — owned implementation of the operations below; reuse an earlier qualified module when appropriate.
- **Create (proposed):** `tests/unit/v2/phase_03/test_indicators_cot.py` — independent contract, failure and FR-log cases for this task.
- **Audit/compose:** the owning README and applicable workspace/client listed above; choose exact existing files in the task plan. Host services remain the only job/resource/persistence authority.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Disposition all 67 COT-folder additions and both emergency exits, plus 32 new VP-folder files and changed kernels.
- [ ] **Step 2:** Specify COT fields/releases, bin sizing, sessions, POC/value-area ties, Delta, TPO, AnchoredVWAP rounding/warm-up and operation order.
- [ ] **Step 3:** Keep generic VolumeProfile, selected signals and TPO engine availability distinct; qualify native indicator dependencies separately.
- [ ] **Acceptance:** implement the independent tests below; retain evidence, owned lifecycle and observable errors in the connected consumer before checking this task.

## 5. Verification and Testing

**Future automated command:** `uv run pytest tests/unit/v2/phase_03/test_indicators_cot.py --no-cov`.

**Independent cases:** Independent COT publication/emergency-exit vectors and profile bin/tie/session/rounding/warm-up cases; reject unsupported engine/block combinations.

**Connected acceptance:** use an isolated real host and temporary resources through the declared workspace/consumer. Verify genuine job/resource IDs, visible unavailable/denied/failure states, cancellation and retained lineage after reconnect/reload. Capture expected versus actual results; do not report fixture outputs as runtime behavior.

# 3.4 AlgoWizard rule authoring

## 1. Objective

Connect AlgoWizard editing to the shared semantic strategy.

## 2. Research and donors

P07 AppWizard/ServletAlgoWizard plus retained AlgoWizard UI.

Use the phase sources and legacy CSV to recover exact donor entries/fingerprints. Write independent input/output expectations before translation. Record missing bodies, target decisions and compatibility limits in source-bound evidence.

## 3. File Changes

- **Create (proposed):** `app/plugins/strategy/wizard.py` — owned implementation of the operations below; reuse an earlier qualified module when appropriate.
- **Create (proposed):** `tests/unit/v2/phase_03/test_wizard.py` — independent contract, failure and FR-log cases for this task.
- **Audit/compose:** the owning README and applicable workspace/client listed above; choose exact existing files in the task plan. Host services remain the only job/resource/persistence authority.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Map retained rule/condition/action controls and typed parameter forms to valid semantic nodes.
- [ ] **Step 2:** Validate edits with actionable local/server errors and expose availability by block/engine.
- [ ] **Step 3:** Save, clone, reload and request a backtest through existing capabilities without a second execution model.
- [ ] **Acceptance:** implement the independent tests below; retain evidence, owned lifecycle and observable errors in the connected consumer before checking this task.

## 5. Verification and Testing

**Future automated command:** `uv run pytest tests/unit/v2/phase_03/test_wizard.py --no-cov`.

**Independent cases:** Author a strategy, reject invalid parameter/type/engine combinations, save/reload and compare the exact specification used by the engine.

**Connected acceptance:** use an isolated real host and temporary resources through the declared workspace/consumer. Verify genuine job/resource IDs, visible unavailable/denied/failure states, cancellation and retained lineage after reconnect/reload. Capture expected versus actual results; do not report fixture outputs as runtime behavior.

# 3.5 Code editor, custom code and indicator testing

## 1. Objective

Provide real custom-code and indicator testing with qualified isolation.

## 2. Research and donors

P07 CodeEditor/IndicatorTester/ProjectResources and P17 editor resources; no Java bytecode framework replica.

Use the phase sources and legacy CSV to recover exact donor entries/fingerprints. Write independent input/output expectations before translation. Record missing bodies, target decisions and compatibility limits in source-bound evidence.

## 3. File Changes

- **Create (proposed):** `app/plugins/strategy/code_editor.py` — owned implementation of the operations below; reuse an earlier qualified module when appropriate.
- **Create (proposed):** `app/plugins/strategy/indicator_testing.py` — owned implementation of the operations below; reuse an earlier qualified module when appropriate.
- **Create (proposed):** `tests/unit/v2/phase_03/test_code_editor.py` — independent contract, failure and FR-log cases for this task.
- **Audit/compose:** the owning README and applicable workspace/client listed above; choose exact existing files in the task plan. Host services remain the only job/resource/persistence authority.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Recover custom-resource import/export, compilation/evaluation and test input/output contracts.
- [ ] **Step 2:** Choose an explicit trust/isolation policy before running user code; bound CPU/memory/time/output and restrict access.
- [ ] **Step 3:** Run indicator tests on owned data resources and return genuine traces/errors; integrate text editing and saved source lineage.
- [ ] **Acceptance:** implement the independent tests below; retain evidence, owned lifecycle and observable errors in the connected consumer before checking this task.

## 5. Verification and Testing

**Future automated command:** `uv run pytest tests/unit/v2/phase_03/test_code_editor.py --no-cov`.

**Independent cases:** Test formula outputs, invalid code, timeout/resource exhaustion, denied file/network access and cancel; an unsandboxed worker or saved text alone does not qualify testing.

**Connected acceptance:** use an isolated real host and temporary resources through the declared workspace/consumer. Verify genuine job/resource IDs, visible unavailable/denied/failure states, cancellation and retained lineage after reconnect/reload. Capture expected versus actual results; do not report fixture outputs as runtime behavior.

# 3.6 Saved revisions and SQ3/SQ4 compatibility

## 1. Objective

Read/write accepted native strategies and retain revisions without silent loss.

## 2. Research and donors

P07 LoaderSQ3/LoaderSQ4/SaverSQ3 and strategy resource contracts; F12 owns AlgoCloud access.

Use the phase sources and legacy CSV to recover exact donor entries/fingerprints. Write independent input/output expectations before translation. Record missing bodies, target decisions and compatibility limits in source-bound evidence.

## 3. File Changes

- **Create (proposed):** `app/plugins/strategy/formats.py` — owned implementation of the operations below; reuse an earlier qualified module when appropriate.
- **Create (proposed):** `app/plugins/strategy/strategy_store.py` — owned implementation of the operations below; reuse an earlier qualified module when appropriate.
- **Create (proposed):** `tests/unit/v2/phase_03/test_formats.py` — independent contract, failure and FR-log cases for this task.
- **Audit/compose:** the owning README and applicable workspace/client listed above; choose exact existing files in the task plan. Host services remain the only job/resource/persistence authority.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Inventory SQ3/SQ4 versions, contained archive entries/XML fields and AlgoCloud strategy representation.
- [ ] **Step 2:** Implement narrow parsers, SQ3 save and accepted unknown-field preservation; reject unsupported versions/unsafe entries.
- [ ] **Step 3:** Retain provenance and conflict behavior on load/save; compare semantic and format round trips independently.
- [ ] **Acceptance:** implement the independent tests below; retain evidence, owned lifecycle and observable errors in the connected consumer before checking this task.

## 5. Verification and Testing

**Future automated command:** `uv run pytest tests/unit/v2/phase_03/test_formats.py --no-cov`.

**Independent cases:** Golden accepted format fixtures, unknown fields, corrupt archives/XML, traversal, duplicate identity and SQ3 save/reload; do not claim an unevidenced SQ4 writer.

**Connected acceptance:** use an isolated real host and temporary resources through the declared workspace/consumer. Verify genuine job/resource IDs, visible unavailable/denied/failure states, cancellation and retained lineage after reconnect/reload. Capture expected versus actual results; do not report fixture outputs as runtime behavior.

# 3.7 Platform code and package export

## 1. Objective

Export platform code and dependent packages from qualified strategy semantics.

## 2. Research and donors

P07 templates and NinjaTrader package/resources; F04 owns execution-profile qualification.

Use the phase sources and legacy CSV to recover exact donor entries/fingerprints. Write independent input/output expectations before translation. Record missing bodies, target decisions and compatibility limits in source-bound evidence.

## 3. File Changes

- **Create (proposed):** `app/plugins/strategy/exporters.py` — owned implementation of the operations below; reuse an earlier qualified module when appropriate.
- **Create (proposed):** `tests/unit/v2/phase_03/test_exporters.py` — independent contract, failure and FR-log cases for this task.
- **Audit/compose:** the owning README and applicable workspace/client listed above; choose exact existing files in the task plan. Host services remain the only job/resource/persistence authority.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Inventory every retained target/template and its parameter/indicator/session/compiler contract.
- [ ] **Step 2:** Render escaped, deterministic source with explicit version/package dependencies and unsupported features.
- [ ] **Step 3:** Qualify NinjaTrader8 native .cs and indicator package; preserve bar-close behavior and explicit on-tick rejection.
- [ ] **Step 4:** Compile/import and compare independent execution traces in each approved isolated target.
- [ ] **Acceptance:** implement the independent tests below; retain evidence, owned lifecycle and observable errors in the connected consumer before checking this task.

## 5. Verification and Testing

**Future automated command:** `uv run pytest tests/unit/v2/phase_03/test_exporters.py --no-cov`.

**Independent cases:** Template escaping/defaults, package/version integrity, native dependency checks and target traces; generated strings do not prove execution/export parity.

**Connected acceptance:** use an isolated real host and temporary resources through the declared workspace/consumer. Verify genuine job/resource IDs, visible unavailable/denied/failure states, cancellation and retained lineage after reconnect/reload. Capture expected versus actual results; do not report fixture outputs as runtime behavior.

# 3.8 Connected authoring and round-trip qualification

## 1. Objective

Complete the author/save/run/export journey through retained authoring surfaces.

## 2. Research and donors

P05/P07 integration gates and retained editor/source-code consumers.

Use the phase sources and legacy CSV to recover exact donor entries/fingerprints. Write independent input/output expectations before translation. Record missing bodies, target decisions and compatibility limits in source-bound evidence.

## 3. File Changes

- **Create (proposed):** `app/plugins/strategy/integration.py` — owned implementation of the operations below; reuse an earlier qualified module when appropriate.
- **Create (proposed):** `tests/unit/v2/phase_03/test_integration.py` — independent contract, failure and FR-log cases for this task.
- **Audit/compose:** the owning README and applicable workspace/client listed above; choose exact existing files in the task plan. Host services remain the only job/resource/persistence authority.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Connect AlgoWizard, CodeEditor, indicator test, strategy resources and ResultsSourceCode to owned operations.
- [ ] **Step 2:** Demonstrate native import, meaningful edit, saved revision, backtest and qualified export with the same semantic lineage.
- [ ] **Step 3:** Verify unsupported block/format/engine states and backend errors survive restart/reconnect.
- [ ] **Acceptance:** implement the independent tests below; retain evidence, owned lifecycle and observable errors in the connected consumer before checking this task.

## 5. Verification and Testing

**Future automated command:** `uv run pytest tests/unit/v2/phase_03/test_integration.py --no-cov`.

**Independent cases:** Isolated connected UI journey plus native round-trip/compiler evidence; every block/format/target row must be accepted before this phase is complete.

**Connected acceptance:** use an isolated real host and temporary resources through the declared workspace/consumer. Verify genuine job/resource IDs, visible unavailable/denied/failure states, cancellation and retained lineage after reconnect/reload. Capture expected versus actual results; do not report fixture outputs as runtime behavior.

## Phase completion gate

- [ ] All 8 numbered tasks and all specialist matrix rows are accepted under their own approved plans.
- [ ] Independent behavioral/numerical/format evidence supports each claimed compatibility scope; missing donor/provider/platform behavior remains explicitly unresolved.
- [ ] Actual backend/UI journey, failures, cancellation, restart/reconnect and scoped removal preserve retained outputs and unrelated work.
- [ ] Owning READMEs, task evidence and the master checklist agree; required Ruff/mypy/tests/coverage and applicable UI gates pass for implemented source.

A milestone subset is usable progress. Whole-product release also requires the [shared release gate](implementation_checklist.md#shared-release-gate). No checkbox is completed by publishing this plan.

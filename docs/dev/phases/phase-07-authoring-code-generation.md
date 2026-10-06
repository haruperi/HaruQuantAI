# P07 — AlgoWizard, CodeEditor, custom resources and platform code generation

- **Source:** `HARUQUANTAI_ROOT/docs/dev/sqx-full-application-roadmap.md`; SHA-256 `9abec0aa2faf6bd78b39e80c2dcfb7dfcae62ae412d9b56a77904de6a7b5a54c`.
- **Dependencies:** P02,P05,P06.
- **Scope:** 16 JAR feature tasks, 1 resource tasks, one phase integration task.
- **State:** proposed checklists; all execution, registrations and target contracts require task-level approval.
- **File labels:** existing paths are Modify; absent paths are Create; later shared edits name their earlier proposed owner.
- **Execution standard:** AGENTS.md plan → approval → implementation → tests → walkthrough; canonical Python docstrings, typed public APIs and explicit FR logs.
- **Clean room:** donor signatures guide behavioral research; independently written implementations; no proprietary source in evidence; no parity claim without independent validation.
- **Verification:** commands below are future tasks, not reported passes; isolated stores only; no live-store schema change/restore or Git mutation.

# freemarker.jar — FEAT-AUTHORING-FREEMARKER

## 1. Objective

- **Goal:** Render supported code/report templates through a ratified Python template adapter.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Save, validate and execute authored strategies and generated platform code.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/libs/freemarker.jar`; 1124 class declarations; SHA-256 `de92d103d3a86c2287307218ff50dc1c941de283f7b9e1fb23e93fc7220838bf`.
- **Inspected reference:** No dedicated docs/sqx coverage; expand archive inspection; roadmap allocation `FEAT-AUTHORING-FREEMARKER`.
- **Owner:** `app/workspace/AlgoWizard/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Authoring, snippet/resource loading and target-language template generation; downstream P08,P09,P17.
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/libs/freemarker.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/libs/freemarker.jar" freemarker.cache.AndMatcher`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Dependency:** qualify stdlib/declared packages; approve additions; classify JVM-only internals.

## 3. File Changes

- **Create:** `app/workspace/AlgoWizard/service.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/workspace/AlgoWizard/contracts.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/code_generation/templates.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/code_generation/emitters.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/workspace/AlgoWizard/README.md`
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_authoring_freemarker.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/authoring_freemarker.json`
  - Store versioned paraphrased donor input/output fixtures.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Render supported code/report templates through a ratified Python template adapter; verify escaping, missing variables, deterministic output and target syntax.
- [ ] **Step 4:** `FR-AUTHORING-FREEMARKER-AND-MATCHER-CONTRACT` → `freemarker.cache.AndMatcher`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-AUTHORING-FREEMARKER-AND-MATCHER-MATCHES` → `freemarker.cache.AndMatcher.matches`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** Wire qualified adapters to consumers; release resources on failure/shutdown.
- [ ] **Step 7:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_authoring_freemarker.py --no-cov`; expect escaping, missing variables, deterministic output and target syntax; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture escaping, missing variables, deterministic output and target syntax and visible failures.

# javassist.jar — FEAT-AUTHORING-JAVASSIST

## 1. Objective

- **Goal:** Replace consumed bytecode-extension mechanisms with an approved Python resource mechanism.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Save, validate and execute authored strategies and generated platform code.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/libs/javassist.jar`; 402 class declarations; SHA-256 `59531c00f3e3aa1ff48b3a8cf4ead47d203ab0e2fd9e0ad401f764e05947e252`.
- **Inspected reference:** No dedicated docs/sqx coverage; expand archive inspection; roadmap allocation `FEAT-AUTHORING-JAVASSIST`.
- **Owner:** `app/workspace/AlgoWizard/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Authoring, snippet/resource loading and target-language template generation; downstream P08,P09,P17.
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/libs/javassist.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/libs/javassist.jar" javassist.ByteArrayClassPath`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Dependency:** qualify stdlib/declared packages; approve additions; classify JVM-only internals.

## 3. File Changes

- **Modify:** `app/workspace/AlgoWizard/service.py` (proposed earlier in FEAT-AUTHORING-FREEMARKER)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/workspace/AlgoWizard/contracts.py` (proposed earlier in FEAT-AUTHORING-FREEMARKER)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/plugins/code_generation/templates.py` (proposed earlier in FEAT-AUTHORING-FREEMARKER)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/plugins/code_generation/emitters.py` (proposed earlier in FEAT-AUTHORING-FREEMARKER)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/workspace/AlgoWizard/README.md` (proposed earlier in FEAT-AUTHORING-FREEMARKER)
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_authoring_javassist.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/authoring_javassist.json`
  - Store versioned paraphrased donor input/output fixtures.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Replace consumed bytecode-extension mechanisms with an approved Python resource mechanism; verify trust boundary, version rejection and qualified extension lifecycle.
- [ ] **Step 4:** `FR-AUTHORING-JAVASSIST-BYTE-ARRAY-CLASS-PATH-CONTRACT` → `javassist.ByteArrayClassPath`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-AUTHORING-JAVASSIST-BYTE-ARRAY-CLASS-PATH-CLOSE` → `javassist.ByteArrayClassPath.close`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** `FR-AUTHORING-JAVASSIST-BYTE-ARRAY-CLASS-PATH-OPEN-CLASSFILE` → `javassist.ByteArrayClassPath.openClassfile`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 7:** Wire qualified adapters to consumers; release resources on failure/shutdown.
- [ ] **Step 8:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_authoring_javassist.py --no-cov`; expect trust boundary, version rejection and qualified extension lifecycle; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture trust boundary, version rejection and qualified extension lifecycle and visible failures.

# SQWizardBusiness.jar — FEAT-AUTHORING-SQ-WIZARD-BUSINESS

## 1. Objective

- **Goal:** Lower authored rules and resources to validated executable strategy nodes.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Save, validate and execute authored strategies and generated platform code.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/libs/SQWizardBusiness.jar`; 24 class declarations; SHA-256 `3f908f6dc5c057d204e7688d093f89f9c0cf6bc5f55891e044993cb7098d71ee`.
- **Inspected reference:** `HARUQUANTAI_ROOT/docs/sqx/Shared/SQWizardBusiness.md`; roadmap allocation `FEAT-AUTHORING-SQ-WIZARD-BUSINESS`.
- **Owner:** `app/workspace/AlgoWizard/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Authoring, snippet/resource loading and target-language template generation; downstream P08,P09,P17.
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/libs/SQWizardBusiness.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/libs/SQWizardBusiness.jar" com.strategyquant.wizard.desktop.loader.TransformEngineLoader`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Dependency:** qualify stdlib/declared packages; approve additions; classify JVM-only internals.

## 3. File Changes

- **Modify:** `app/workspace/AlgoWizard/service.py` (proposed earlier in FEAT-AUTHORING-FREEMARKER)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/workspace/AlgoWizard/contracts.py` (proposed earlier in FEAT-AUTHORING-FREEMARKER)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/plugins/code_generation/templates.py` (proposed earlier in FEAT-AUTHORING-FREEMARKER)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/plugins/code_generation/emitters.py` (proposed earlier in FEAT-AUTHORING-FREEMARKER)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/workspace/AlgoWizard/README.md` (proposed earlier in FEAT-AUTHORING-FREEMARKER)
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_authoring_sq_wizard_business.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/authoring_sq_wizard_business.json`
  - Store versioned paraphrased donor input/output fixtures.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Lower authored rules and resources to validated executable strategy nodes; verify node types, parameter mapping and save/reload semantics.
- [ ] **Step 4:** `FR-AUTHORING-SQ-WIZARD-BUSINESS-TRANSFORM-ENGINE-LOADER-CONTRACT` → `com.strategyquant.wizard.desktop.loader.TransformEngineLoader`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-AUTHORING-SQ-WIZARD-BUSINESS-TRANSFORM-ENGINE-LOADER-LOAD` → `com.strategyquant.wizard.desktop.loader.TransformEngineLoader.load`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** `FR-AUTHORING-SQ-WIZARD-BUSINESS-TRANSFORM-ENGINE-LOADER-TRANSFORM-CODE` → `com.strategyquant.wizard.desktop.loader.TransformEngineLoader.transformCode`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 7:** Wire qualified adapters to consumers; release resources on failure/shutdown.
- [ ] **Step 8:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_authoring_sq_wizard_business.py --no-cov`; expect node types, parameter mapping and save/reload semantics; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture node types, parameter mapping and save/reload semantics and visible failures.

# AppCodeEditor.jar — FEAT-AUTHORING-APP-CODE-EDITOR

## 1. Objective

- **Goal:** Qualify editor resources and execute actual indicator test fixtures.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Save, validate and execute authored strategies and generated platform code.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/plugins/AppCodeEditor/AppCodeEditor.jar`; 3 class declarations; SHA-256 `55e2e1254d7ac8ed935e40eb09007d3f369279156077c98986fa00b9f463dc08`.
- **Inspected reference:** `HARUQUANTAI_ROOT/docs/sqx/CodeEditor/AppCodeEditor.md`; roadmap allocation `FEAT-AUTHORING-APP-CODE-EDITOR`.
- **Owner:** `app/workspace/CodeEditor/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Workspace/product registration and backend composition; downstream .
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/plugins/AppCodeEditor/AppCodeEditor.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/plugins/AppCodeEditor/AppCodeEditor.jar" com.strategyquant.plugin.App.impl.CodeEditor.CodeEditorAppPlugin`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

## 3. File Changes

- **Create:** `app/workspace/CodeEditor/workspace.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/workspace/CodeEditor/routes.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/workspace/CodeEditor/contracts.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/workspace/CodeEditor/README.md`
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_authoring_app_code_editor.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/authoring_app_code_editor.json`
  - Store versioned paraphrased donor input/output fixtures.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Qualify editor resources and execute actual indicator test fixtures; verify resource validation, compile/qualification errors and fixture outputs.
- [ ] **Step 4:** `FR-AUTHORING-APP-CODE-EDITOR-CODE-EDITOR-APP-PLUGIN-CONTRACT` → `com.strategyquant.plugin.App.impl.CodeEditor.CodeEditorAppPlugin`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-AUTHORING-APP-CODE-EDITOR-CODE-EDITOR-APP-PLUGIN-GET-PREFERRED-POSITION` → `com.strategyquant.plugin.App.impl.CodeEditor.CodeEditorAppPlugin.getPreferredPosition`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** `FR-AUTHORING-APP-CODE-EDITOR-CODE-EDITOR-APP-PLUGIN-INIT-PLUGIN` → `com.strategyquant.plugin.App.impl.CodeEditor.CodeEditorAppPlugin.initPlugin`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 7:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 8:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_authoring_app_code_editor.py --no-cov`; expect resource validation, compile/qualification errors and fixture outputs; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture resource validation, compile/qualification errors and fixture outputs and visible failures.

# AppWizard.jar — FEAT-AUTHORING-APP-WIZARD

## 1. Objective

- **Goal:** Mount the Wizard workspace against real backend capabilities.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Save, validate and execute authored strategies and generated platform code.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/plugins/AppWizard/AppWizard.jar`; 1 class declarations; SHA-256 `051f00bcfa2fc60de169faa4a1de99a478b3386f927cb74b6ce9961aa10b6f2f`.
- **Inspected reference:** `HARUQUANTAI_ROOT/docs/sqx/AlgoWizard/AppWizard.md`; roadmap allocation `FEAT-AUTHORING-APP-WIZARD`.
- **Owner:** `app/workspace/AlgoWizard/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Workspace/product registration and backend composition; downstream .
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/plugins/AppWizard/AppWizard.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/plugins/AppWizard/AppWizard.jar" com.strategyquant.plugin.App.impl.Wizard.WizardAppPlugin`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

## 3. File Changes

- **Create:** `app/workspace/AlgoWizard/workspace.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/workspace/AlgoWizard/routes.py`
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/workspace/AlgoWizard/contracts.py` (proposed earlier in FEAT-AUTHORING-FREEMARKER)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/workspace/AlgoWizard/README.md` (proposed earlier in FEAT-AUTHORING-FREEMARKER)
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_authoring_app_wizard.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/authoring_app_wizard.json`
  - Store versioned paraphrased donor input/output fixtures.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Mount the Wizard workspace against real backend capabilities; verify discovery, workspace readiness, job/resource ownership and unmount cleanup.
- [ ] **Step 4:** `FR-AUTHORING-APP-WIZARD-WIZARD-APP-PLUGIN-CONTRACT` → `com.strategyquant.plugin.App.impl.Wizard.WizardAppPlugin`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-AUTHORING-APP-WIZARD-WIZARD-APP-PLUGIN-GET-PREFERRED-POSITION` → `com.strategyquant.plugin.App.impl.Wizard.WizardAppPlugin.getPreferredPosition`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** `FR-AUTHORING-APP-WIZARD-WIZARD-APP-PLUGIN-INIT-PLUGIN` → `com.strategyquant.plugin.App.impl.Wizard.WizardAppPlugin.initPlugin`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 7:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 8:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_authoring_app_wizard.py --no-cov`; expect discovery, workspace readiness, job/resource ownership and unmount cleanup; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture discovery, workspace readiness, job/resource ownership and unmount cleanup and visible failures.

# CodeEditorImportExport.jar — FEAT-AUTHORING-CODE-EDITOR-IMPORT-EXPORT

## 1. Objective

- **Goal:** Qualify editor resources and execute actual indicator test fixtures.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Save, validate and execute authored strategies and generated platform code.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/plugins/CodeEditorImportExport/CodeEditorImportExport.jar`; 5 class declarations; SHA-256 `c2a0f530874c947e743e82c5ac98793e40e5d45764e1632e85a0396a3f830dbb`.
- **Inspected reference:** `HARUQUANTAI_ROOT/docs/sqx/CodeEditor/CodeEditorImportExport.md`; roadmap allocation `FEAT-AUTHORING-CODE-EDITOR-IMPORT-EXPORT`.
- **Owner:** `app/workspace/CodeEditor/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Code/resource authoring, exchange and indicator qualification; downstream .
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/plugins/CodeEditorImportExport/CodeEditorImportExport.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/plugins/CodeEditorImportExport/CodeEditorImportExport.jar" com.strategyquant.plugin.CodeEditor.impl.ImportExport.ImportExportServlet`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

## 3. File Changes

- **Create:** `app/workspace/CodeEditor/service.py`
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/workspace/CodeEditor/routes.py` (proposed earlier in FEAT-AUTHORING-APP-CODE-EDITOR)
  - Implement this feature's consumed typed contracts.
- **Create:** `app/workspace/CodeEditor/resources.py`
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/workspace/CodeEditor/README.md` (proposed earlier in FEAT-AUTHORING-APP-CODE-EDITOR)
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_authoring_code_editor_import_export.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/authoring_code_editor_import_export.json`
  - Store versioned paraphrased donor input/output fixtures.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Qualify editor resources and execute actual indicator test fixtures; verify resource validation, compile/qualification errors and fixture outputs.
- [ ] **Step 4:** `FR-AUTHORING-CODE-EDITOR-IMPORT-EXPORT-IMPORT-EXPORT-SERVLET-CONTRACT` → `com.strategyquant.plugin.CodeEditor.impl.ImportExport.ImportExportServlet`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-AUTHORING-CODE-EDITOR-IMPORT-EXPORT-IMPORT-EXPORT-SERVLET-EXECUTE` → `com.strategyquant.plugin.CodeEditor.impl.ImportExport.ImportExportServlet.execute`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 7:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_authoring_code_editor_import_export.py --no-cov`; expect resource validation, compile/qualification errors and fixture outputs; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture resource validation, compile/qualification errors and fixture outputs and visible failures.

# CodeEditorIndicatorTester.jar — FEAT-AUTHORING-CODE-EDITOR-INDICATOR-TESTER

## 1. Objective

- **Goal:** Qualify editor resources and execute actual indicator test fixtures.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Save, validate and execute authored strategies and generated platform code.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/plugins/CodeEditorIndicatorTester/CodeEditorIndicatorTester.jar`; 7 class declarations; SHA-256 `0a9dae03be5a30d26bc68da2289b33010af52c833ce239979b8338fec5dd233b`.
- **Inspected reference:** `HARUQUANTAI_ROOT/docs/sqx/CodeEditor/CodeEditorIndicatorTester.md`; roadmap allocation `FEAT-AUTHORING-CODE-EDITOR-INDICATOR-TESTER`.
- **Owner:** `app/workspace/CodeEditor/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Code/resource authoring, exchange and indicator qualification; downstream .
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/plugins/CodeEditorIndicatorTester/CodeEditorIndicatorTester.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/plugins/CodeEditorIndicatorTester/CodeEditorIndicatorTester.jar" com.strategyquant.plugin.CodeEditor.impl.IndicatorTester.IndicatorTestExecutor`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

## 3. File Changes

- **Modify:** `app/workspace/CodeEditor/service.py` (proposed earlier in FEAT-AUTHORING-CODE-EDITOR-IMPORT-EXPORT)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/workspace/CodeEditor/routes.py` (proposed earlier in FEAT-AUTHORING-APP-CODE-EDITOR)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/workspace/CodeEditor/resources.py` (proposed earlier in FEAT-AUTHORING-CODE-EDITOR-IMPORT-EXPORT)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/workspace/CodeEditor/README.md` (proposed earlier in FEAT-AUTHORING-APP-CODE-EDITOR)
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_authoring_code_editor_indicator_tester.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/authoring_code_editor_indicator_tester.json`
  - Store versioned paraphrased donor input/output fixtures.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Qualify editor resources and execute actual indicator test fixtures; verify resource validation, compile/qualification errors and fixture outputs.
- [ ] **Step 4:** `FR-AUTHORING-CODE-EDITOR-INDICATOR-TESTER-INDICATOR-TEST-EXECUTOR-CONTRACT` → `com.strategyquant.plugin.CodeEditor.impl.IndicatorTester.IndicatorTestExecutor`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-AUTHORING-CODE-EDITOR-INDICATOR-TESTER-INDICATOR-TEST-EXECUTOR-GET` → `com.strategyquant.plugin.CodeEditor.impl.IndicatorTester.IndicatorTestExecutor.get`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** `FR-AUTHORING-CODE-EDITOR-INDICATOR-TESTER-INDICATOR-TEST-EXECUTOR-START` → `com.strategyquant.plugin.CodeEditor.impl.IndicatorTester.IndicatorTestExecutor.start`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 7:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 8:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_authoring_code_editor_indicator_tester.py --no-cov`; expect resource validation, compile/qualification errors and fixture outputs; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture resource validation, compile/qualification errors and fixture outputs and visible failures.

# LoaderSQ3.jar — FEAT-AUTHORING-LOADER-SQ3

## 1. Objective

- **Goal:** Implement the named native strategy archive version and round-trip rules.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Save, validate and execute authored strategies and generated platform code.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/plugins/LoaderSQ3/LoaderSQ3.jar`; 5 class declarations; SHA-256 `ea5d85eda47ef76feb832232af9ca8581d9be8860385b59bf45478b6ed6c7da8`.
- **Inspected reference:** `HARUQUANTAI_ROOT/docs/sqx/Shared/LoaderSQ3.md`; roadmap allocation `FEAT-AUTHORING-LOADER-SQ3`.
- **Owner:** `app/plugins/strategy/LoaderSQ3/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Strategy archive exchange, authoring and strategy wire contracts; downstream .
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/plugins/LoaderSQ3/LoaderSQ3.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/plugins/LoaderSQ3/LoaderSQ3.jar" com.strategyquant.plugin.Loader.impl.SQ3.SQ3FileLoader`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

## 3. File Changes

- **Create:** `app/plugins/strategy/LoaderSQ3/codec.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/strategy/LoaderSQ3/service.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/strategy/LoaderSQ3/routes.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/strategy/LoaderSQ3/README.md`
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_authoring_loader_sq3.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/authoring_loader_sq3.json`
  - Store versioned paraphrased donor input/output fixtures.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Implement the named native strategy archive version and round-trip rules; verify format version, unknown fields, checksum/entry validation and preserved semantics.
- [ ] **Step 4:** `FR-AUTHORING-LOADER-SQ3-SQ3-FILE-LOADER-CONTRACT` → `com.strategyquant.plugin.Loader.impl.SQ3.SQ3FileLoader`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-AUTHORING-LOADER-SQ3-SQ3-FILE-LOADER-LOAD` → `com.strategyquant.plugin.Loader.impl.SQ3.SQ3FileLoader.load`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 7:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_authoring_loader_sq3.py --no-cov`; expect format version, unknown fields, checksum/entry validation and preserved semantics; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture format version, unknown fields, checksum/entry validation and preserved semantics and visible failures.

# LoaderSQ4.jar — FEAT-AUTHORING-LOADER-SQ4

## 1. Objective

- **Goal:** Implement the named native strategy archive version and round-trip rules.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Save, validate and execute authored strategies and generated platform code.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/plugins/LoaderSQ4/LoaderSQ4.jar`; 1 class declarations; SHA-256 `4a22421e5c16dc07a0d7da0ea3d5116e71b46a3751001df8a03392ee8c3b86a9`.
- **Inspected reference:** `HARUQUANTAI_ROOT/docs/sqx/Shared/LoaderSQ4.md`; roadmap allocation `FEAT-AUTHORING-LOADER-SQ4`.
- **Owner:** `app/plugins/strategy/LoaderSQ4/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Strategy archive exchange, authoring and strategy wire contracts; downstream .
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/plugins/LoaderSQ4/LoaderSQ4.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/plugins/LoaderSQ4/LoaderSQ4.jar" com.strategyquant.plugin.Loader.impl.SQ4.SQ4LoaderPlugin`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

## 3. File Changes

- **Create:** `app/plugins/strategy/LoaderSQ4/codec.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/strategy/LoaderSQ4/service.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/strategy/LoaderSQ4/routes.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/strategy/LoaderSQ4/README.md`
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_authoring_loader_sq4.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/authoring_loader_sq4.json`
  - Store versioned paraphrased donor input/output fixtures.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Implement the named native strategy archive version and round-trip rules; verify format version, unknown fields, checksum/entry validation and preserved semantics.
- [ ] **Step 4:** `FR-AUTHORING-LOADER-SQ4-SQ4-LOADER-PLUGIN-CONTRACT` → `com.strategyquant.plugin.Loader.impl.SQ4.SQ4LoaderPlugin`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-AUTHORING-LOADER-SQ4-SQ4-LOADER-PLUGIN-GET-PREFERRED-POSITION` → `com.strategyquant.plugin.Loader.impl.SQ4.SQ4LoaderPlugin.getPreferredPosition`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** `FR-AUTHORING-LOADER-SQ4-SQ4-LOADER-PLUGIN-INIT-PLUGIN` → `com.strategyquant.plugin.Loader.impl.SQ4.SQ4LoaderPlugin.initPlugin`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 7:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 8:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_authoring_loader_sq4.py --no-cov`; expect format version, unknown fields, checksum/entry validation and preserved semantics; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture format version, unknown fields, checksum/entry validation and preserved semantics and visible failures.

# ResultsSourceCode.jar — FEAT-AUTHORING-RESULTS-SOURCE-CODE

## 1. Objective

- **Goal:** Implement authoritative SourceCode result projections/actions.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Save, validate and execute authored strategies and generated platform code.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/plugins/ResultsSourceCode/ResultsSourceCode.jar`; 2 class declarations; SHA-256 `fdab52cc9a0e0c535b881ee56b58771e71bab86385d78a32a8346fc868b39794`.
- **Inspected reference:** `HARUQUANTAI_ROOT/docs/sqx/Results/ResultsSourceCode.md`; roadmap allocation `FEAT-AUTHORING-RESULTS-SOURCE-CODE`.
- **Owner:** `app/plugins/code_generation/ResultsSourceCode/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Strategy source-generation projection; downstream .
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/plugins/ResultsSourceCode/ResultsSourceCode.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/plugins/ResultsSourceCode/ResultsSourceCode.jar" com.strategyquant.plugin.Results.impl.SourceCode.SourceCodeServlet`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

## 3. File Changes

- **Create:** `app/plugins/code_generation/ResultsSourceCode/service.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/code_generation/ResultsSourceCode/contracts.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/code_generation/ResultsSourceCode/README.md`
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_authoring_results_source_code.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/authoring_results_source_code.json`
  - Store versioned paraphrased donor input/output fixtures.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Implement authoritative SourceCode result projections/actions; verify metric provenance, result identity, empty/error state and stored-value reconciliation.
- [ ] **Step 4:** `FR-AUTHORING-RESULTS-SOURCE-CODE-SOURCE-CODE-SERVLET-CONTRACT` → `com.strategyquant.plugin.Results.impl.SourceCode.SourceCodeServlet`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-AUTHORING-RESULTS-SOURCE-CODE-SOURCE-CODE-SERVLET-EXECUTE` → `com.strategyquant.plugin.Results.impl.SourceCode.SourceCodeServlet.execute`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** `FR-AUTHORING-RESULTS-SOURCE-CODE-SOURCE-CODE-SERVLET-ON-LIST-MM` → `com.strategyquant.plugin.Results.impl.SourceCode.SourceCodeServlet.onListMM`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 7:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 8:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_authoring_results_source_code.py --no-cov`; expect metric provenance, result identity, empty/error state and stored-value reconciliation; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture metric provenance, result identity, empty/error state and stored-value reconciliation and visible failures.

# SaverSQ3.jar — FEAT-AUTHORING-SAVER-SQ3

## 1. Objective

- **Goal:** Implement the named native strategy archive version and round-trip rules.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Save, validate and execute authored strategies and generated platform code.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/plugins/SaverSQ3/SaverSQ3.jar`; 2 class declarations; SHA-256 `e1e12388a0232cd9cad0615bbe2e076e01b51304230e9bcefb2b13cb1a5b666a`.
- **Inspected reference:** `HARUQUANTAI_ROOT/docs/sqx/Shared/SaverSQ3.md`; roadmap allocation `FEAT-AUTHORING-SAVER-SQ3`.
- **Owner:** `app/plugins/strategy/SaverSQ3/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Strategy archive exchange, authoring and strategy wire contracts; downstream .
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/plugins/SaverSQ3/SaverSQ3.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/plugins/SaverSQ3/SaverSQ3.jar" com.strategyquant.plugin.Saver.impl.SQ3.SQ3FileSaver`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

## 3. File Changes

- **Create:** `app/plugins/strategy/SaverSQ3/codec.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/strategy/SaverSQ3/service.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/strategy/SaverSQ3/routes.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/strategy/SaverSQ3/README.md`
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_authoring_saver_sq3.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/authoring_saver_sq3.json`
  - Store versioned paraphrased donor input/output fixtures.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Implement the named native strategy archive version and round-trip rules; verify format version, unknown fields, checksum/entry validation and preserved semantics.
- [ ] **Step 4:** `FR-AUTHORING-SAVER-SQ3-SQ3-FILE-SAVER-CONTRACT` → `com.strategyquant.plugin.Saver.impl.SQ3.SQ3FileSaver`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-AUTHORING-SAVER-SQ3-SQ3-FILE-SAVER-SAVE` → `com.strategyquant.plugin.Saver.impl.SQ3.SQ3FileSaver.save`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** `FR-AUTHORING-SAVER-SQ3-SQ3-FILE-SAVER-GET-PARAM` → `com.strategyquant.plugin.Saver.impl.SQ3.SQ3FileSaver.getParam`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 7:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 8:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_authoring_saver_sq3.py --no-cov`; expect format version, unknown fields, checksum/entry validation and preserved semantics; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture format version, unknown fields, checksum/entry validation and preserved semantics and visible failures.

# ServletAlgoWizard.jar — FEAT-AUTHORING-SERVLET-ALGO-WIZARD

## 1. Objective

- **Goal:** Expose AlgoWizard commands through the owning domain routes.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Save, validate and execute authored strategies and generated platform code.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/plugins/ServletAlgoWizard/ServletAlgoWizard.jar`; 4 class declarations; SHA-256 `c6b7b2f21b9a299759a3d760d611646f460fab39e8dd173a78f17a9f806ff541`.
- **Inspected reference:** `HARUQUANTAI_ROOT/docs/sqx/AlgoWizard/ServletAlgoWizard.md`; roadmap allocation `FEAT-AUTHORING-SERVLET-ALGO-WIZARD`.
- **Owner:** `app/plugins/strategy/ServletAlgoWizard/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Strategy archive exchange, authoring and strategy wire contracts; downstream .
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/plugins/ServletAlgoWizard/ServletAlgoWizard.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/plugins/ServletAlgoWizard/ServletAlgoWizard.jar" com.strategyquant.plugin.Servlet.impl.AlgoWizard.AlgoWizardBlocksTagCloud`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

## 3. File Changes

- **Create:** `app/plugins/strategy/ServletAlgoWizard/codec.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/strategy/ServletAlgoWizard/service.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/strategy/ServletAlgoWizard/routes.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/strategy/ServletAlgoWizard/README.md`
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_authoring_servlet_algo_wizard.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/authoring_servlet_algo_wizard.json`
  - Store versioned paraphrased donor input/output fixtures.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Expose AlgoWizard commands through the owning domain routes; verify command parsing, typed outputs, authority, validation errors and cancellation.
- [ ] **Step 4:** `FR-AUTHORING-SERVLET-ALGO-WIZARD-ALGO-WIZARD-BLOCKS-TAG-CLOUD-CONTRACT` → `com.strategyquant.plugin.Servlet.impl.AlgoWizard.AlgoWizardBlocksTagCloud`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-AUTHORING-SERVLET-ALGO-WIZARD-ALGO-WIZARD-BLOCKS-TAG-CLOUD-LIST-JSON` → `com.strategyquant.plugin.Servlet.impl.AlgoWizard.AlgoWizardBlocksTagCloud.listJSON`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** `FR-AUTHORING-SERVLET-ALGO-WIZARD-ALGO-WIZARD-BLOCKS-TAG-CLOUD-SAVE` → `com.strategyquant.plugin.Servlet.impl.AlgoWizard.AlgoWizardBlocksTagCloud.save`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 7:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 8:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_authoring_servlet_algo_wizard.py --no-cov`; expect command parsing, typed outputs, authority, validation errors and cancellation; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture command parsing, typed outputs, authority, validation errors and cancellation and visible failures.

# ServletCodeEditor.jar — FEAT-AUTHORING-SERVLET-CODE-EDITOR

## 1. Objective

- **Goal:** Qualify editor resources and execute actual indicator test fixtures.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Save, validate and execute authored strategies and generated platform code.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/plugins/ServletCodeEditor/ServletCodeEditor.jar`; 13 class declarations; SHA-256 `2950747967d42710cad4df45cef4aaf0d3317df5261964c788eb147138e9744e`.
- **Inspected reference:** `HARUQUANTAI_ROOT/docs/sqx/CodeEditor/ServletCodeEditor.md`; roadmap allocation `FEAT-AUTHORING-SERVLET-CODE-EDITOR`.
- **Owner:** `app/workspace/CodeEditor/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Code/resource authoring, exchange and indicator qualification; downstream .
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/plugins/ServletCodeEditor/ServletCodeEditor.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/plugins/ServletCodeEditor/ServletCodeEditor.jar" com.strategyquant.plugin.Servlet.impl.CodeEditor.CodeEditorServlet`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

## 3. File Changes

- **Modify:** `app/workspace/CodeEditor/service.py` (proposed earlier in FEAT-AUTHORING-CODE-EDITOR-IMPORT-EXPORT)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/workspace/CodeEditor/routes.py` (proposed earlier in FEAT-AUTHORING-APP-CODE-EDITOR)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/workspace/CodeEditor/resources.py` (proposed earlier in FEAT-AUTHORING-CODE-EDITOR-IMPORT-EXPORT)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/workspace/CodeEditor/README.md` (proposed earlier in FEAT-AUTHORING-APP-CODE-EDITOR)
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_authoring_servlet_code_editor.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/authoring_servlet_code_editor.json`
  - Store versioned paraphrased donor input/output fixtures.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Qualify editor resources and execute actual indicator test fixtures; verify resource validation, compile/qualification errors and fixture outputs.
- [ ] **Step 4:** `FR-AUTHORING-SERVLET-CODE-EDITOR-CODE-EDITOR-SERVLET-CONTRACT` → `com.strategyquant.plugin.Servlet.impl.CodeEditor.CodeEditorServlet`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-AUTHORING-SERVLET-CODE-EDITOR-CODE-EDITOR-SERVLET-EXECUTE` → `com.strategyquant.plugin.Servlet.impl.CodeEditor.CodeEditorServlet.execute`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** `FR-AUTHORING-SERVLET-CODE-EDITOR-CODE-EDITOR-SERVLET-DELETE-RECURSIVE` → `com.strategyquant.plugin.Servlet.impl.CodeEditor.CodeEditorServlet.deleteRecursive`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 7:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 8:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_authoring_servlet_code_editor.py --no-cov`; expect resource validation, compile/qualification errors and fixture outputs; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture resource validation, compile/qualification errors and fixture outputs and visible failures.

# ServletIndicatorTester.jar — FEAT-AUTHORING-SERVLET-INDICATOR-TESTER

## 1. Objective

- **Goal:** Qualify editor resources and execute actual indicator test fixtures.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Save, validate and execute authored strategies and generated platform code.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/plugins/ServletIndicatorTester/ServletIndicatorTester.jar`; 0 class declarations; SHA-256 `f6bdd59758b3df89d4163a268a11b1da550583fcef508737c2c3b7b9c23e2685`.
- **Inspected reference:** `HARUQUANTAI_ROOT/docs/sqx/Shared/ServletIndicatorTester.md`; roadmap allocation `FEAT-AUTHORING-SERVLET-INDICATOR-TESTER`.
- **Owner:** `app/workspace/CodeEditor/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Code/resource authoring, exchange and indicator qualification; downstream .
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/plugins/ServletIndicatorTester/ServletIndicatorTester.jar"`; inspect manifest/resources and target runtime requirements.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

## 3. File Changes

- **Modify:** `app/workspace/CodeEditor/service.py` (proposed earlier in FEAT-AUTHORING-CODE-EDITOR-IMPORT-EXPORT)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/workspace/CodeEditor/routes.py` (proposed earlier in FEAT-AUTHORING-APP-CODE-EDITOR)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/workspace/CodeEditor/resources.py` (proposed earlier in FEAT-AUTHORING-CODE-EDITOR-IMPORT-EXPORT)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/workspace/CodeEditor/README.md` (proposed earlier in FEAT-AUTHORING-APP-CODE-EDITOR)
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_authoring_servlet_indicator_tester.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/authoring_servlet_indicator_tester.json`
  - Store versioned paraphrased donor input/output fixtures.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Qualify editor resources and execute actual indicator test fixtures; verify resource validation, compile/qualification errors and fixture outputs.
- [ ] **Step 4:** `FR-AUTHORING-SERVLET-INDICATOR-TESTER-RESOURCE-CONTRIBUTION` → `No compiled class entries; inspect registration/resources`: Verify the resource/manifest contract.
- [ ] **Step 5:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 6:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_authoring_servlet_indicator_tester.py --no-cov`; expect resource validation, compile/qualification errors and fixture outputs; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture resource validation, compile/qualification errors and fixture outputs and visible failures.

# ServletStrategy.jar — FEAT-AUTHORING-SERVLET-STRATEGY

## 1. Objective

- **Goal:** Expose Strategy commands through the owning domain routes.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Save, validate and execute authored strategies and generated platform code.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/plugins/ServletStrategy/ServletStrategy.jar`; 3 class declarations; SHA-256 `03907ceeeaf800838cc8e17d458c4f6bb5c958c043489f517d043071705a7260`.
- **Inspected reference:** `HARUQUANTAI_ROOT/docs/sqx/Shared/ServletStrategy.md`; roadmap allocation `FEAT-AUTHORING-SERVLET-STRATEGY`.
- **Owner:** `app/plugins/strategy/ServletStrategy/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Strategy archive exchange, authoring and strategy wire contracts; downstream .
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/plugins/ServletStrategy/ServletStrategy.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/plugins/ServletStrategy/ServletStrategy.jar" com.strategyquant.plugin.Servlet.impl.Strategy.StrategyServlet`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

## 3. File Changes

- **Create:** `app/plugins/strategy/ServletStrategy/codec.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/strategy/ServletStrategy/service.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/strategy/ServletStrategy/routes.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/strategy/ServletStrategy/README.md`
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_authoring_servlet_strategy.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/authoring_servlet_strategy.json`
  - Store versioned paraphrased donor input/output fixtures.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Expose Strategy commands through the owning domain routes; verify command parsing, typed outputs, authority, validation errors and cancellation.
- [ ] **Step 4:** `FR-AUTHORING-SERVLET-STRATEGY-STRATEGY-SERVLET-CONTRACT` → `com.strategyquant.plugin.Servlet.impl.Strategy.StrategyServlet`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-AUTHORING-SERVLET-STRATEGY-STRATEGY-SERVLET-GET-INSTANCE` → `com.strategyquant.plugin.Servlet.impl.Strategy.StrategyServlet.getInstance`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** `FR-AUTHORING-SERVLET-STRATEGY-STRATEGY-SERVLET-EXECUTE` → `com.strategyquant.plugin.Servlet.impl.Strategy.StrategyServlet.execute`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 7:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 8:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_authoring_servlet_strategy.py --no-cov`; expect command parsing, typed outputs, authority, validation errors and cancellation; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture command parsing, typed outputs, authority, validation errors and cancellation and visible failures.

# ServletWizard.jar — FEAT-AUTHORING-SERVLET-WIZARD

## 1. Objective

- **Goal:** Expose Wizard commands through the owning domain routes.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Save, validate and execute authored strategies and generated platform code.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/plugins/ServletWizard/ServletWizard.jar`; 2 class declarations; SHA-256 `1b452b3b77ca15997aa9d5461c858869ed3106068a6600b3c451b0b473fcc91e`.
- **Inspected reference:** `HARUQUANTAI_ROOT/docs/sqx/AlgoWizard/ServletWizard.md`; roadmap allocation `FEAT-AUTHORING-SERVLET-WIZARD`.
- **Owner:** `app/plugins/strategy/ServletWizard/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Strategy archive exchange, authoring and strategy wire contracts; downstream .
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/plugins/ServletWizard/ServletWizard.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/plugins/ServletWizard/ServletWizard.jar" com.strategyquant.plugin.Servlet.impl.Wizard.WizardServlet`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

## 3. File Changes

- **Create:** `app/plugins/strategy/ServletWizard/codec.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/strategy/ServletWizard/service.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/strategy/ServletWizard/routes.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/strategy/ServletWizard/README.md`
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_authoring_servlet_wizard.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/authoring_servlet_wizard.json`
  - Store versioned paraphrased donor input/output fixtures.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Expose Wizard commands through the owning domain routes; verify command parsing, typed outputs, authority, validation errors and cancellation.
- [ ] **Step 4:** `FR-AUTHORING-SERVLET-WIZARD-WIZARD-SERVLET-CONTRACT` → `com.strategyquant.plugin.Servlet.impl.Wizard.WizardServlet`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-AUTHORING-SERVLET-WIZARD-WIZARD-SERVLET-EXECUTE` → `com.strategyquant.plugin.Servlet.impl.Wizard.WizardServlet.execute`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 7:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_authoring_servlet_wizard.py --no-cov`; expect command parsing, typed outputs, authority, validation errors and cancellation; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture command parsing, typed outputs, authority, validation errors and cancellation and visible failures.

# ProjectResources resource contribution — FEAT-UI-PROJECT-RESOURCES

## 1. Objective

- **Goal:** Qualify and connect ProjectResources without assuming a missing backend JAR.
- **Context / Problem Solved:** ProjectResources is one of 17 roadmap contributions with no immediate JAR.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/plugins/ProjectResources`; narrow source: `SQX_REFERENCE_ROOT/internal/plugins/ProjectResources/module.js`.
- **FR:** `FR-UI-PROJECT-RESOURCES-RESOURCE-WORKFLOW`; proposed owning README `app/workspace/AlgoWizard/README.md`.
- **Research:** inspect resource/module/config declarations and consuming registrations; fingerprint stable files and trace action routes.
- **Gap:** directory/resource presence does not prove an enabled workflow; empty contributions need explicit dispositions.

## 3. File Changes

- **Create:** `app/workspace/AlgoWizard/resource_contributions.py`
  - Mount only verified resource/action contributions through this owning capability.
- **Modify:** `app/workspace/AlgoWizard/README.md` (proposed earlier in FEAT-AUTHORING-FREEMARKER)
  - Register the resource workflow and explicit empty/unavailable dispositions.
- **Create:** `tests/unit/sqx_features/test_ui_project_resources.py`
  - Verify contribution mount/unmount and action authority.
- **Modify:** `ui/app/workspace/AlgoWizard/AlgoWizardWorkspace.tsx`
  - Bind the verified resource workflow to real capability state.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Inspect and specify resource/action declarations, defaults, route consumers and active registration; approve the resulting FR contract.
- [ ] **Step 2:** `FR-UI-PROJECT-RESOURCES-RESOURCE-WORKFLOW`: implement the evidenced resource workflow or ratified empty contribution; preserve domain ownership.
- [ ] **Step 3:** Bind verified UI controls to host/domain capabilities; define disabled, denied and unavailable states.
- [ ] **Step 4:** Test mount/unmount, missing resources, action authority and FR logs; retain versioned donor observations.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_ui_project_resources.py --no-cov`; assert resource availability, owned lifecycle and denied/missing actions.
- **Manual / Browser Verification:** Author a fixture strategy; save/reload/run it; test an indicator in CodeEditor; export each promised target and qualify its syntax. Inspect the ProjectResources contribution; an empty or unavailable contribution must remain explicit.

# P07 integration — Save, validate and execute authored strategies and generated platform code

## 1. Objective

- **Goal:** Save, validate and execute authored strategies and generated platform code.
- **Context / Problem Solved:** The existing UI needs a real end-to-end backend workflow, beyond isolated JAR adapters.

## 2. Research and donors

- **Roadmap:** `HARUQUANTAI_ROOT/docs/dev/sqx-full-application-roadmap.md`, P07; donor features and FRs are the tasks in this file.
- **Existing code:** `ui/app/workspace/AlgoWizard/AlgoWizardWorkspace.tsx`, `ui/app/workspace/CodeEditor/CodeEditorWorkspace.tsx`; backend counterparts are proposed.
- **Declared dependencies:** FastAPI, Pydantic, Uvicorn, psutil; host persistence choice remains unratified.
- **Existing tests:** `ui/tests/unit/workspace/AlgoWizard/algoWizardModel.test.ts`; extend actual-backend assertions.
- **Conflict/gap:** frontend existence does not establish functional backend behavior; route/schema/discovery changes need a task plan and approval.
- **Cross-feature ownership:** shared files may host multiple features; keep per-FR traces and delegate persistence/jobs to host capabilities.

## 3. File Changes

- **Modify:** `app/workspace/AlgoWizard/workspace.py` (proposed earlier in FEAT-AUTHORING-APP-WIZARD)
  - Deliver the phase's typed contracts and integration flow; extend prior approved owners where shared.
- **Modify:** `app/workspace/AlgoWizard/service.py` (proposed earlier in FEAT-AUTHORING-FREEMARKER)
  - Deliver the phase's typed contracts and integration flow; extend prior approved owners where shared.
- **Modify:** `app/workspace/AlgoWizard/routes.py` (proposed earlier in FEAT-AUTHORING-APP-WIZARD)
  - Deliver the phase's typed contracts and integration flow; extend prior approved owners where shared.
- **Modify:** `app/workspace/CodeEditor/workspace.py` (proposed earlier in FEAT-AUTHORING-APP-CODE-EDITOR)
  - Deliver the phase's typed contracts and integration flow; extend prior approved owners where shared.
- **Modify:** `app/workspace/CodeEditor/routes.py` (proposed earlier in FEAT-AUTHORING-APP-CODE-EDITOR)
  - Deliver the phase's typed contracts and integration flow; extend prior approved owners where shared.
- **Create:** `app/plugins/strategy/archive.py`
  - Deliver the phase's typed contracts and integration flow; extend prior approved owners where shared.
- **Create:** `app/plugins/strategy/codec.py`
  - Deliver the phase's typed contracts and integration flow; extend prior approved owners where shared.
- **Create:** `app/plugins/strategy/repository.py`
  - Deliver the phase's typed contracts and integration flow; extend prior approved owners where shared.
- **Modify:** `app/plugins/code_generation/templates.py` (proposed earlier in FEAT-AUTHORING-FREEMARKER)
  - Deliver the phase's typed contracts and integration flow; extend prior approved owners where shared.
- **Modify:** `app/plugins/code_generation/emitters.py` (proposed earlier in FEAT-AUTHORING-FREEMARKER)
  - Deliver the phase's typed contracts and integration flow; extend prior approved owners where shared.
- **Create:** `app/plugins/extensions/qualification.py`
  - Deliver the phase's typed contracts and integration flow; extend prior approved owners where shared.
- **Modify:** `ui/app/workspace/AlgoWizard/AlgoWizardWorkspace.tsx`
  - Bind real capability state, errors and cancellation while preserving the existing layout.
- **Modify:** `ui/app/workspace/AlgoWizard/algoWizardClient.ts` (proposed earlier in P05 integration)
  - Own typed routes/envelopes for this domain; replace mock execution with authoritative requests.
- **Modify:** `ui/app/workspace/CodeEditor/CodeEditorWorkspace.tsx`
  - Bind real capability state, errors and cancellation while preserving the existing layout.
- **Create:** `ui/app/workspace/CodeEditor/codeEditorClient.ts`
  - Own typed routes/envelopes for this domain; replace mock execution with authoritative requests.
- **Modify:** `app/workspace/AlgoWizard/README.md` (proposed earlier in FEAT-AUTHORING-FREEMARKER)
  - Own feature registration/status and phase contract decisions after ratification.
- **Create:** `tests/integration/test_authoring_code_generation_workflow.py`
  - Exercise the real phase workflow in isolated stores with failure/cancellation assertions.
- **Create:** `ui/tests/e2e/sqx-authoring-code-generation-backend.spec.ts`
  - Use an isolated real host to verify UI state and request/output reconciliation.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Review preceding feature fixtures and owning README registrations; ratify the phase integration contracts and execution plan.
- [ ] **Step 2:** Specify SQ3/SQ4 round trips, editor lowering, resource versions and extension trust boundaries.
- [ ] **Step 3:** Implement strategy archives, resource qualification and evidence-backed generation templates.
- [ ] **Step 4:** Connect AlgoWizard and CodeEditor save/reload/run/export and genuine indicator testing.
- [ ] **Step 5:** Replace fixture-driven production execution in the affected workflow; retain deterministic fixtures only in tests.
- [ ] **Step 6:** Test positive/failure/cancellation paths and observable FR logs; reload/reconnect and reconcile persisted outputs.
- [ ] **Step 7:** Record exact commands, timestamped artifacts, unresolved gaps and walkthrough; obtain separate owner commit authority.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/integration/test_authoring_code_generation_workflow.py --no-cov`; `npm --prefix ui run test -- tests/unit/workspace/AlgoWizard/algoWizardModel.test.ts`; `npm --prefix ui run test:ui -- tests/e2e/sqx-authoring-code-generation-backend.spec.ts`. Assert author/save/reload/run semantics, archive preservation and target compilation; reject malformed archive, unresolved resource, extension rejection and template failure.
- **Manual / Browser Verification:** Author a fixture strategy; save/reload/run it; test an indicator in CodeEditor; export each promised target and qualify its syntax.

## Phase completion gate

- [ ] Reconcile all allocated FEAT/FR dispositions, donor fixtures and ownership gaps.
- [ ] Run Ruff format/check and strict Mypy on the approved changed Python paths; verify branch-aware coverage ≥80% across retained application source at release.
- [ ] For affected UI: `npm --prefix ui run typecheck`, `npm --prefix ui run test`, `npm --prefix ui run build`.
- [ ] Record real workflow observations, timestamps, failure artifacts and remaining gaps in the walkthrough.
- [ ] Obtain the next task/phase approval; commits and external/destructive actions retain separate owner gates.

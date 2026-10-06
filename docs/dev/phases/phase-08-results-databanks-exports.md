# P08 — Databanks, results, chart projections, analysis and exports

- **Source:** `HARUQUANTAI_ROOT/docs/dev/sqx-full-application-roadmap.md`; SHA-256 `9abec0aa2faf6bd78b39e80c2dcfb7dfcae62ae412d9b56a77904de6a7b5a54c`.
- **Dependencies:** P02,P06,P07.
- **Scope:** 35 JAR feature tasks, 5 resource tasks, one phase integration task.
- **State:** proposed checklists; all execution, registrations and target contracts require task-level approval.
- **File labels:** existing paths are Modify; absent paths are Create; later shared edits name their earlier proposed owner.
- **Execution standard:** AGENTS.md plan → approval → implementation → tests → walkthrough; canonical Python docstrings, typed public APIs and explicit FR logs.
- **Clean room:** donor signatures guide behavioral research; independently written implementations; no proprietary source in evidence; no parity claim without independent validation.
- **Verification:** commands below are future tasks, not reported passes; isolated stores only; no live-store schema change/restore or Git mutation.
- **UI completion:** Applicable features finish with backend + retained UI connected; preserve layouts. Production mocks cannot substitute for capability execution; keep a task unchecked while transport/contracts or required controls are unresolved.
- **Connected verification:** Use an isolated real host and temporary data. Existing mock-only/browser-API-blocking suites are UI regressions, not connected acceptance. Run `npm --prefix ui run typecheck`, `npm --prefix ui run test`, `npm --prefix ui run build` after actual UI source changes.

# 8.1 FEAT-RESULTS-COMMONS-IMAGING - commons-imaging.jar

## 1. Objective

- **Goal:** Generate and transform result images through a qualified export adapter.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Render authoritative databanks, result analysis, charts and exports.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/libs/commons-imaging.jar`; 412 class declarations; SHA-256 `0a2b0b98142e6624ae9c6dae6f84478127aa7fd8278353baa4d09c8543eca31a`.
- **Inspected reference:** No dedicated docs/sqx coverage; expand archive inspection; roadmap allocation `FEAT-RESULTS-COMMONS-IMAGING`.
- **Owner:** `app/plugins/export/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Report/image/document export infrastructure; use equivalent maintained implementations; downstream P12,P13,P17.
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/libs/commons-imaging.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/libs/commons-imaging.jar" org.apache.commons.imaging.ColorTools`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Dependency:** qualify stdlib/declared packages; approve additions; classify JVM-only internals.

- **UI disposition:** Infrastructure only; no standalone UI component found in this library allocation. Its owned backend consumer feeds Results through the phase integration gate; do not invent a library screen or direct plugin route.

## 3. File Changes

- **Create:** `app/plugins/export/html.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/export/pdf.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/export/spreadsheet.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/export/images.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/export/README.md`
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_results_commons_imaging.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/results_commons_imaging.json`
  - Store versioned paraphrased donor input/output fixtures.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Generate and transform result images through a qualified export adapter; verify dimensions, scaling, supported encodings and malformed image handling.
- [ ] **Step 4:** `FR-RESULTS-COMMONS-IMAGING-COLOR-TOOLS-CONTRACT` → `org.apache.commons.imaging.ColorTools`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-RESULTS-COMMONS-IMAGING-COLOR-TOOLS-CORRECT-IMAGE` → `org.apache.commons.imaging.ColorTools.correctImage`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** `FR-RESULTS-COMMONS-IMAGING-COLOR-TOOLS-RELABEL-COLOR-SPACE` → `org.apache.commons.imaging.ColorTools.relabelColorSpace`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 7:** Wire qualified adapters to consumers; release resources on failure/shutdown.
- [ ] **Step 8:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 9:** Verify UI-facing consumer contract: Test this infrastructure through its declared backend/host consumer; expose failures through the owning domain envelope. The phase's connected UI gate verifies the observable workflow.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_results_commons_imaging.py --no-cov`; expect dimensions, scaling, supported encodings and malformed image handling; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture dimensions, scaling, supported encodings and malformed image handling and visible failures.

# 8.2 FEAT-RESULTS-IMAGE4J - image4j.jar

## 1. Objective

- **Goal:** Generate and transform result images through a qualified export adapter.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Render authoritative databanks, result analysis, charts and exports.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/libs/image4j.jar`; 25 class declarations; SHA-256 `93b02ca70ae019d327846489dd3534e7dfbf7595b719441af3a3dfbbce4b04e3`.
- **Inspected reference:** No dedicated docs/sqx coverage; expand archive inspection; roadmap allocation `FEAT-RESULTS-IMAGE4J`.
- **Owner:** `app/plugins/export/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Report/image/document export infrastructure; use equivalent maintained implementations; downstream P12,P13,P17.
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/libs/image4j.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/libs/image4j.jar" net.sf.image4j.codec.bmp.BMPConstants`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Dependency:** qualify stdlib/declared packages; approve additions; classify JVM-only internals.

- **UI disposition:** Infrastructure only; no standalone UI component found in this library allocation. Its owned backend consumer feeds Results through the phase integration gate; do not invent a library screen or direct plugin route.

## 3. File Changes

- **Modify:** `app/plugins/export/html.py` (proposed earlier in FEAT-RESULTS-COMMONS-IMAGING)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/plugins/export/pdf.py` (proposed earlier in FEAT-RESULTS-COMMONS-IMAGING)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/plugins/export/spreadsheet.py` (proposed earlier in FEAT-RESULTS-COMMONS-IMAGING)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/plugins/export/images.py` (proposed earlier in FEAT-RESULTS-COMMONS-IMAGING)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/plugins/export/README.md` (proposed earlier in FEAT-RESULTS-COMMONS-IMAGING)
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_results_image4j.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/results_image4j.json`
  - Store versioned paraphrased donor input/output fixtures.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Generate and transform result images through a qualified export adapter; verify dimensions, scaling, supported encodings and malformed image handling.
- [ ] **Step 4:** `FR-RESULTS-IMAGE4J-BMP-CONSTANTS-CONTRACT` → `net.sf.image4j.codec.bmp.BMPConstants`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** Wire qualified adapters to consumers; release resources on failure/shutdown.
- [ ] **Step 6:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 7:** Verify UI-facing consumer contract: Test this infrastructure through its declared backend/host consumer; expose failures through the owning domain envelope. The phase's connected UI gate verifies the observable workflow.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_results_image4j.py --no-cov`; expect dimensions, scaling, supported encodings and malformed image handling; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture dimensions, scaling, supported encodings and malformed image handling and visible failures.

# 8.3 FEAT-RESULTS-JAVA-IMAGE-SCALING-0-8-6 - java-image-scaling-0.8.6.jar

## 1. Objective

- **Goal:** Generate and transform result images through a qualified export adapter.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Render authoritative databanks, result analysis, charts and exports.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/libs/java-image-scaling-0.8.6.jar`; 31 class declarations; SHA-256 `fabd02916eed5cd1cd5881d94970ea3c74e140b4c21acc6b640ddf3ed1472b95`.
- **Inspected reference:** No dedicated docs/sqx coverage; expand archive inspection; roadmap allocation `FEAT-RESULTS-JAVA-IMAGE-SCALING-0-8-6`.
- **Owner:** `app/plugins/export/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Report/image/document export infrastructure; use equivalent maintained implementations; downstream P12,P13,P17.
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/libs/java-image-scaling-0.8.6.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/libs/java-image-scaling-0.8.6.jar" com.mortennobel.imagescaling.AdvancedResizeOp`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Dependency:** qualify stdlib/declared packages; approve additions; classify JVM-only internals.

- **UI disposition:** Infrastructure only; no standalone UI component found in this library allocation. Its owned backend consumer feeds Results through the phase integration gate; do not invent a library screen or direct plugin route.

## 3. File Changes

- **Modify:** `app/plugins/export/html.py` (proposed earlier in FEAT-RESULTS-COMMONS-IMAGING)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/plugins/export/pdf.py` (proposed earlier in FEAT-RESULTS-COMMONS-IMAGING)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/plugins/export/spreadsheet.py` (proposed earlier in FEAT-RESULTS-COMMONS-IMAGING)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/plugins/export/images.py` (proposed earlier in FEAT-RESULTS-COMMONS-IMAGING)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/plugins/export/README.md` (proposed earlier in FEAT-RESULTS-COMMONS-IMAGING)
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_results_java_image_scaling_0_8_6.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/results_java_image_scaling_0_8_6.json`
  - Store versioned paraphrased donor input/output fixtures.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Generate and transform result images through a qualified export adapter; verify dimensions, scaling, supported encodings and malformed image handling.
- [ ] **Step 4:** `FR-RESULTS-JAVA-IMAGE-SCALING-0-8-6-ADVANCED-RESIZE-OP-CONTRACT` → `com.mortennobel.imagescaling.AdvancedResizeOp`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-RESULTS-JAVA-IMAGE-SCALING-0-8-6-ADVANCED-RESIZE-OP-GET-UNSHARPEN-MASK` → `com.mortennobel.imagescaling.AdvancedResizeOp.getUnsharpenMask`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** `FR-RESULTS-JAVA-IMAGE-SCALING-0-8-6-ADVANCED-RESIZE-OP-SET-UNSHARPEN-MASK` → `com.mortennobel.imagescaling.AdvancedResizeOp.setUnsharpenMask`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 7:** Wire qualified adapters to consumers; release resources on failure/shutdown.
- [ ] **Step 8:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 9:** Verify UI-facing consumer contract: Test this infrastructure through its declared backend/host consumer; expose failures through the owning domain envelope. The phase's connected UI gate verifies the observable workflow.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_results_java_image_scaling_0_8_6.py --no-cov`; expect dimensions, scaling, supported encodings and malformed image handling; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture dimensions, scaling, supported encodings and malformed image handling and visible failures.

# 8.4 FEAT-RESULTS-PD4ML - pd4ml.jar

## 1. Objective

- **Goal:** Qualify PDF result/report generation through a chosen target adapter.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Render authoritative databanks, result analysis, charts and exports.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/libs/pd4ml.jar`; 397 class declarations; SHA-256 `679254d54d47d2373a2c3fe0f34a3658d583c06c51777a07c03abb2a0527d7d2`.
- **Inspected reference:** No dedicated docs/sqx coverage; expand archive inspection; roadmap allocation `FEAT-RESULTS-PD4ML`.
- **Owner:** `app/plugins/export/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Report/image/document export infrastructure; use equivalent maintained implementations; downstream P12,P13,P17.
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/libs/pd4ml.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/libs/pd4ml.jar" org.zefer.pd4ml.PD4PageMark`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Dependency:** qualify stdlib/declared packages; approve additions; classify JVM-only internals.

- **UI disposition:** Infrastructure only; no standalone UI component found in this library allocation. Its owned backend consumer feeds Results through the phase integration gate; do not invent a library screen or direct plugin route.

## 3. File Changes

- **Modify:** `app/plugins/export/html.py` (proposed earlier in FEAT-RESULTS-COMMONS-IMAGING)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/plugins/export/pdf.py` (proposed earlier in FEAT-RESULTS-COMMONS-IMAGING)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/plugins/export/spreadsheet.py` (proposed earlier in FEAT-RESULTS-COMMONS-IMAGING)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/plugins/export/images.py` (proposed earlier in FEAT-RESULTS-COMMONS-IMAGING)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/plugins/export/README.md` (proposed earlier in FEAT-RESULTS-COMMONS-IMAGING)
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_results_pd4ml.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/results_pd4ml.json`
  - Store versioned paraphrased donor input/output fixtures.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Qualify PDF result/report generation through a chosen target adapter; verify page layout, fonts, metadata and totals matching result artifacts.
- [ ] **Step 4:** `FR-RESULTS-PD4ML-PD4-PAGE-MARK-CONTRACT` → `org.zefer.pd4ml.PD4PageMark`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** Wire qualified adapters to consumers; release resources on failure/shutdown.
- [ ] **Step 6:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 7:** Verify UI-facing consumer contract: Test this infrastructure through its declared backend/host consumer; expose failures through the owning domain envelope. The phase's connected UI gate verifies the observable workflow.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_results_pd4ml.py --no-cov`; expect page layout, fonts, metadata and totals matching result artifacts; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture page layout, fonts, metadata and totals matching result artifacts and visible failures.

# 8.5 FEAT-RESULTS-PNGJ - pngj.jar

## 1. Objective

- **Goal:** Generate and transform result images through a qualified export adapter.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Render authoritative databanks, result analysis, charts and exports.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/libs/pngj.jar`; 113 class declarations; SHA-256 `6278c81c54106c78c0725718f73f80e5bfee2acea149eafab4c24a451cd6fc3c`.
- **Inspected reference:** No dedicated docs/sqx coverage; expand archive inspection; roadmap allocation `FEAT-RESULTS-PNGJ`.
- **Owner:** `app/plugins/export/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Report/image/document export infrastructure; use equivalent maintained implementations; downstream P12,P13,P17.
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/libs/pngj.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/libs/pngj.jar" ar.com.hjg.pngj.BufferedStreamFeeder`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Dependency:** qualify stdlib/declared packages; approve additions; classify JVM-only internals.

- **UI disposition:** Infrastructure only; no standalone UI component found in this library allocation. Its owned backend consumer feeds Results through the phase integration gate; do not invent a library screen or direct plugin route.

## 3. File Changes

- **Modify:** `app/plugins/export/html.py` (proposed earlier in FEAT-RESULTS-COMMONS-IMAGING)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/plugins/export/pdf.py` (proposed earlier in FEAT-RESULTS-COMMONS-IMAGING)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/plugins/export/spreadsheet.py` (proposed earlier in FEAT-RESULTS-COMMONS-IMAGING)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/plugins/export/images.py` (proposed earlier in FEAT-RESULTS-COMMONS-IMAGING)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/plugins/export/README.md` (proposed earlier in FEAT-RESULTS-COMMONS-IMAGING)
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_results_pngj.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/results_pngj.json`
  - Store versioned paraphrased donor input/output fixtures.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Generate and transform result images through a qualified export adapter; verify dimensions, scaling, supported encodings and malformed image handling.
- [ ] **Step 4:** `FR-RESULTS-PNGJ-BUFFERED-STREAM-FEEDER-CONTRACT` → `ar.com.hjg.pngj.BufferedStreamFeeder`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-RESULTS-PNGJ-BUFFERED-STREAM-FEEDER-GET-STREAM` → `ar.com.hjg.pngj.BufferedStreamFeeder.getStream`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** `FR-RESULTS-PNGJ-BUFFERED-STREAM-FEEDER-FEED` → `ar.com.hjg.pngj.BufferedStreamFeeder.feed`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 7:** Wire qualified adapters to consumers; release resources on failure/shutdown.
- [ ] **Step 8:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 9:** Verify UI-facing consumer contract: Test this infrastructure through its declared backend/host consumer; expose failures through the owning domain envelope. The phase's connected UI gate verifies the observable workflow.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_results_pngj.py --no-cov`; expect dimensions, scaling, supported encodings and malformed image handling; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture dimensions, scaling, supported encodings and malformed image handling and visible failures.

# 8.6 FEAT-RESULTS-POI-OOXML-SCHEMAS - poi-ooxml-schemas.jar

## 1. Objective

- **Goal:** Qualify spreadsheet result/report generation through a chosen target adapter.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Render authoritative databanks, result analysis, charts and exports.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/libs/poi-ooxml-schemas.jar`; 2383 class declarations; SHA-256 `6bc4a179f61447559bafee3ecbe3c4de7ba4b5c3954ded909cd477783c7db275`.
- **Inspected reference:** No dedicated docs/sqx coverage; expand archive inspection; roadmap allocation `FEAT-RESULTS-POI-OOXML-SCHEMAS`.
- **Owner:** `app/plugins/export/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Report/image/document export infrastructure; use equivalent maintained implementations; downstream P12,P13,P17.
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/libs/poi-ooxml-schemas.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/libs/poi-ooxml-schemas.jar" com.microsoft.schemas.office.x2006.digsig.CTSignatureInfoV1`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Dependency:** qualify stdlib/declared packages; approve additions; classify JVM-only internals.

- **UI disposition:** Infrastructure only; no standalone UI component found in this library allocation. Its owned backend consumer feeds Results through the phase integration gate; do not invent a library screen or direct plugin route.

## 3. File Changes

- **Modify:** `app/plugins/export/html.py` (proposed earlier in FEAT-RESULTS-COMMONS-IMAGING)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/plugins/export/pdf.py` (proposed earlier in FEAT-RESULTS-COMMONS-IMAGING)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/plugins/export/spreadsheet.py` (proposed earlier in FEAT-RESULTS-COMMONS-IMAGING)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/plugins/export/images.py` (proposed earlier in FEAT-RESULTS-COMMONS-IMAGING)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/plugins/export/README.md` (proposed earlier in FEAT-RESULTS-COMMONS-IMAGING)
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_results_poi_ooxml_schemas.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/results_poi_ooxml_schemas.json`
  - Store versioned paraphrased donor input/output fixtures.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Qualify spreadsheet result/report generation through a chosen target adapter; verify sheet types, formula/value policy, units and totals matching artifacts.
- [ ] **Step 4:** `FR-RESULTS-POI-OOXML-SCHEMAS-CT-SIGNATURE-INFO-V1-CONTRACT` → `com.microsoft.schemas.office.x2006.digsig.CTSignatureInfoV1`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-RESULTS-POI-OOXML-SCHEMAS-CT-SIGNATURE-INFO-V1-GET-SETUP-ID` → `com.microsoft.schemas.office.x2006.digsig.CTSignatureInfoV1.getSetupID`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** `FR-RESULTS-POI-OOXML-SCHEMAS-CT-SIGNATURE-INFO-V1-XGET-SETUP-ID` → `com.microsoft.schemas.office.x2006.digsig.CTSignatureInfoV1.xgetSetupID`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 7:** Wire qualified adapters to consumers; release resources on failure/shutdown.
- [ ] **Step 8:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 9:** Verify UI-facing consumer contract: Test this infrastructure through its declared backend/host consumer; expose failures through the owning domain envelope. The phase's connected UI gate verifies the observable workflow.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_results_poi_ooxml_schemas.py --no-cov`; expect sheet types, formula/value policy, units and totals matching artifacts; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture sheet types, formula/value policy, units and totals matching artifacts and visible failures.

# 8.7 FEAT-RESULTS-POI-OOXML - poi-ooxml.jar

## 1. Objective

- **Goal:** Qualify spreadsheet result/report generation through a chosen target adapter.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Render authoritative databanks, result analysis, charts and exports.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/libs/poi-ooxml.jar`; 562 class declarations; SHA-256 `02db7dd9db4a71bd48452aee87e5691bae2a0f26e7fea264a8f271a42d32599e`.
- **Inspected reference:** No dedicated docs/sqx coverage; expand archive inspection; roadmap allocation `FEAT-RESULTS-POI-OOXML`.
- **Owner:** `app/plugins/export/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Report/image/document export infrastructure; use equivalent maintained implementations; downstream P12,P13,P17.
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/libs/poi-ooxml.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/libs/poi-ooxml.jar" org.apache.poi.POIXMLDocument`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Dependency:** qualify stdlib/declared packages; approve additions; classify JVM-only internals.

- **UI disposition:** Infrastructure only; no standalone UI component found in this library allocation. Its owned backend consumer feeds Results through the phase integration gate; do not invent a library screen or direct plugin route.

## 3. File Changes

- **Modify:** `app/plugins/export/html.py` (proposed earlier in FEAT-RESULTS-COMMONS-IMAGING)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/plugins/export/pdf.py` (proposed earlier in FEAT-RESULTS-COMMONS-IMAGING)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/plugins/export/spreadsheet.py` (proposed earlier in FEAT-RESULTS-COMMONS-IMAGING)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/plugins/export/images.py` (proposed earlier in FEAT-RESULTS-COMMONS-IMAGING)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/plugins/export/README.md` (proposed earlier in FEAT-RESULTS-COMMONS-IMAGING)
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_results_poi_ooxml.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/results_poi_ooxml.json`
  - Store versioned paraphrased donor input/output fixtures.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Qualify spreadsheet result/report generation through a chosen target adapter; verify sheet types, formula/value policy, units and totals matching artifacts.
- [ ] **Step 4:** `FR-RESULTS-POI-OOXML-POIXML-DOCUMENT-CONTRACT` → `org.apache.poi.POIXMLDocument`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-RESULTS-POI-OOXML-POIXML-DOCUMENT-OPEN-PACKAGE` → `org.apache.poi.POIXMLDocument.openPackage`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** `FR-RESULTS-POI-OOXML-POIXML-DOCUMENT-GET-PACKAGE` → `org.apache.poi.POIXMLDocument.getPackage`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 7:** Wire qualified adapters to consumers; release resources on failure/shutdown.
- [ ] **Step 8:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 9:** Verify UI-facing consumer contract: Test this infrastructure through its declared backend/host consumer; expose failures through the owning domain envelope. The phase's connected UI gate verifies the observable workflow.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_results_poi_ooxml.py --no-cov`; expect sheet types, formula/value policy, units and totals matching artifacts; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture sheet types, formula/value policy, units and totals matching artifacts and visible failures.

# 8.8 FEAT-RESULTS-POI - poi.jar

## 1. Objective

- **Goal:** Qualify spreadsheet result/report generation through a chosen target adapter.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Render authoritative databanks, result analysis, charts and exports.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/libs/poi.jar`; 1358 class declarations; SHA-256 `1412f527ed0a766a6a3697c81705381fa1c34aecc15c4cdcca12a1e52de24d0e`.
- **Inspected reference:** No dedicated docs/sqx coverage; expand archive inspection; roadmap allocation `FEAT-RESULTS-POI`.
- **Owner:** `app/plugins/export/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Report/image/document export infrastructure; use equivalent maintained implementations; downstream P12,P13,P17.
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/libs/poi.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/libs/poi.jar" org.apache.poi.EncryptedDocumentException`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Dependency:** qualify stdlib/declared packages; approve additions; classify JVM-only internals.

- **UI disposition:** Infrastructure only; no standalone UI component found in this library allocation. Its owned backend consumer feeds Results through the phase integration gate; do not invent a library screen or direct plugin route.

## 3. File Changes

- **Modify:** `app/plugins/export/html.py` (proposed earlier in FEAT-RESULTS-COMMONS-IMAGING)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/plugins/export/pdf.py` (proposed earlier in FEAT-RESULTS-COMMONS-IMAGING)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/plugins/export/spreadsheet.py` (proposed earlier in FEAT-RESULTS-COMMONS-IMAGING)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/plugins/export/images.py` (proposed earlier in FEAT-RESULTS-COMMONS-IMAGING)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/plugins/export/README.md` (proposed earlier in FEAT-RESULTS-COMMONS-IMAGING)
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_results_poi.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/results_poi.json`
  - Store versioned paraphrased donor input/output fixtures.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Qualify spreadsheet result/report generation through a chosen target adapter; verify sheet types, formula/value policy, units and totals matching artifacts.
- [ ] **Step 4:** `FR-RESULTS-POI-ENCRYPTED-DOCUMENT-EXCEPTION-CONTRACT` → `org.apache.poi.EncryptedDocumentException`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** Wire qualified adapters to consumers; release resources on failure/shutdown.
- [ ] **Step 6:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 7:** Verify UI-facing consumer contract: Test this infrastructure through its declared backend/host consumer; expose failures through the owning domain envelope. The phase's connected UI gate verifies the observable workflow.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_results_poi.py --no-cov`; expect sheet types, formula/value policy, units and totals matching artifacts; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture sheet types, formula/value policy, units and totals matching artifacts and visible failures.

# 8.9 FEAT-RESULTS-XMLBEANS - xmlbeans.jar

## 1. Objective

- **Goal:** Parse and preserve supported XML document fields.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Render authoritative databanks, result analysis, charts and exports.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/libs/xmlbeans.jar`; 1531 class declarations; SHA-256 `c77974359688b2823b48fa9a33da68559d64f8474441480d9df4f9e254332a96`.
- **Inspected reference:** No dedicated docs/sqx coverage; expand archive inspection; roadmap allocation `FEAT-RESULTS-XMLBEANS`.
- **Owner:** `app/plugins/export/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Report/image/document export infrastructure; use equivalent maintained implementations; downstream P12,P13,P17.
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/libs/xmlbeans.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/libs/xmlbeans.jar" org.apache.xmlbeans.BindingConfig`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Dependency:** qualify stdlib/declared packages; approve additions; classify JVM-only internals.

- **UI disposition:** Infrastructure only; no standalone UI component found in this library allocation. Its owned backend consumer feeds Results through the phase integration gate; do not invent a library screen or direct plugin route.

## 3. File Changes

- **Modify:** `app/plugins/export/html.py` (proposed earlier in FEAT-RESULTS-COMMONS-IMAGING)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/plugins/export/pdf.py` (proposed earlier in FEAT-RESULTS-COMMONS-IMAGING)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/plugins/export/spreadsheet.py` (proposed earlier in FEAT-RESULTS-COMMONS-IMAGING)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/plugins/export/images.py` (proposed earlier in FEAT-RESULTS-COMMONS-IMAGING)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/plugins/export/README.md` (proposed earlier in FEAT-RESULTS-COMMONS-IMAGING)
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_results_xmlbeans.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/results_xmlbeans.json`
  - Store versioned paraphrased donor input/output fixtures.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Parse and preserve supported XML document fields; verify namespaces, encoding, rejected unsafe constructs and lossless unknown fields.
- [ ] **Step 4:** `FR-RESULTS-XMLBEANS-BINDING-CONFIG-CONTRACT` → `org.apache.xmlbeans.BindingConfig`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-RESULTS-XMLBEANS-BINDING-CONFIG-LOOKUP-PACKAGE-FOR-NAMESPACE` → `org.apache.xmlbeans.BindingConfig.lookupPackageForNamespace`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** `FR-RESULTS-XMLBEANS-BINDING-CONFIG-LOOKUP-PREFIX-FOR-NAMESPACE` → `org.apache.xmlbeans.BindingConfig.lookupPrefixForNamespace`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 7:** Wire qualified adapters to consumers; release resources on failure/shutdown.
- [ ] **Step 8:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 9:** Verify UI-facing consumer contract: Test this infrastructure through its declared backend/host consumer; expose failures through the owning domain envelope. The phase's connected UI gate verifies the observable workflow.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_results_xmlbeans.py --no-cov`; expect namespaces, encoding, rejected unsafe constructs and lossless unknown fields; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture namespaces, encoding, rejected unsafe constructs and lossless unknown fields and visible failures.

# 8.10 FEAT-RESULTS-APP-RESULTS - AppResults.jar

## 1. Objective

- **Goal:** Mount the Results workspace against real backend capabilities.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Render authoritative databanks, result analysis, charts and exports.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/plugins/AppResults/AppResults.jar`; 1 class declarations; SHA-256 `af4b02953d5d15b61c15cb28b6dcd80b3f3b1cbdedeacecb7fa1ede9aedf3821`.
- **Inspected reference:** `HARUQUANTAI_ROOT/docs/sqx/Results/AppResults.md`; roadmap allocation `FEAT-RESULTS-APP-RESULTS`.
- **Owner:** `app/workspace/Results/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Workspace/product registration and backend composition; downstream .
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/plugins/AppResults/AppResults.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/plugins/AppResults/AppResults.jar" com.strategyquant.plugin.App.impl.Results.ResultsAppPlugin`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_REFERENCE_ROOT/internal/plugins/AppResults`; `SQX_REFERENCE_ROOT/internal/web/RESULTS`; `SQX_REFERENCE_ROOT/internal/plugins/ProjectResults`. Inspect `SQX_REFERENCE_ROOT/internal/plugins/AppResults/module.js`; `SQX_REFERENCE_ROOT/internal/plugins/AppResults/SQResultsData.js`.
- **Existing UI connection:** Results; proposed shared consumer; verify the exact existing control and public contract before implementation. Target `ui/app/workspace/Results/ResultsWorkspace.tsx`; wire persisted run/result lookup, selected sample, trades and reconciled metrics.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Create:** `app/workspace/Results/workspace.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/workspace/Results/routes.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/workspace/Results/contracts.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/workspace/Results/README.md`
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_results_app_results.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/results_app_results.json`
  - Store versioned paraphrased donor input/output fixtures.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/workspace/Results/ResultsWorkspace.tsx`
  - Display persisted run/result lookup, selected sample, trades and reconciled metrics from backend responses; preserve layout.
- **Modify:** `ui/app/plugins/project/ProjectResults/ResultsCtrl.ts`
  - Await backend validation/commands; bind actual result and job states to existing controls.
- **Modify:** `ui/app/plugins/databank/ProjectDatabanks/databankStore.ts`
  - Replace affected mock job/resource authority with server projections; preserve selection/view state.
- **Create:** `ui/app/workspace/Results/resultsClient.ts`
  - Typed domain client over host transport; ratify route/schema/version, errors and cancellation. Reuse this proposed owner if delivered earlier.
- **Create:** `ui/tests/unit/backend-connections/feat-results-app-results.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-results-databanks-exports-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Mount the Results workspace against real backend capabilities; verify discovery, workspace readiness, job/resource ownership and unmount cleanup.
- [ ] **Step 4:** `FR-RESULTS-APP-RESULTS-RESULTS-APP-PLUGIN-CONTRACT` → `com.strategyquant.plugin.App.impl.Results.ResultsAppPlugin`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-RESULTS-APP-RESULTS-RESULTS-APP-PLUGIN-GET-PREFERRED-POSITION` → `com.strategyquant.plugin.App.impl.Results.ResultsAppPlugin.getPreferredPosition`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** `FR-RESULTS-APP-RESULTS-RESULTS-APP-PLUGIN-INIT-PLUGIN` → `com.strategyquant.plugin.App.impl.Results.ResultsAppPlugin.initPlugin`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 7:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 8:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 9:** Connect retained UI: Ratify the feature-owned wire contract; bind persisted run/result lookup, selected sample, trades and reconciled metrics to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 10:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_results_app_results.py --no-cov`; expect discovery, workspace readiness, job/resource ownership and unmount cleanup; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture discovery, workspace readiness, job/resource ownership and unmount cleanup and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-results-app-results.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-results-databanks-exports-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise Results for FEAT-RESULTS-APP-RESULTS; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.

# 8.11 FEAT-RESULTS-DATABANK-FILTER-BY-CORRELATION - DatabankFilterByCorrelation.jar

## 1. Objective

- **Goal:** Calculate qualified correlations and apply selection/filter rules.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Render authoritative databanks, result analysis, charts and exports.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/plugins/DatabankFilterByCorrelation/DatabankFilterByCorrelation.jar`; 2 class declarations; SHA-256 `e2dcd26a6e9046a16eba7654b1c090ae2087cf1eb2b4ecc1fd22c25541c8bd26`.
- **Inspected reference:** `HARUQUANTAI_ROOT/docs/sqx/Results/DatabankFilterByCorrelation.md`; roadmap allocation `FEAT-RESULTS-DATABANK-FILTER-BY-CORRELATION`.
- **Owner:** `app/plugins/databank/DatabankFilterByCorrelation/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Databank views/actions/rename and correlation projections; downstream P09–P13.
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/plugins/DatabankFilterByCorrelation/DatabankFilterByCorrelation.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/plugins/DatabankFilterByCorrelation/DatabankFilterByCorrelation.jar" com.strategyquant.plugin.Databank.impl.FilterByCorrelation.DatabankFilterByCorrelationServlet`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_REFERENCE_ROOT/internal/plugins/DatabankFilterByCorrelation`; `SQX_REFERENCE_ROOT/internal/plugins/ResultsDatabankActions`; `SQX_REFERENCE_ROOT/internal/plugins/ProjectDatabanks`. Inspect `SQX_REFERENCE_ROOT/internal/plugins/DatabankFilterByCorrelation/databankFilterByCorrelationPopup.html`; `SQX_REFERENCE_ROOT/internal/plugins/DatabankFilterByCorrelation/module.js`.
- **Existing UI connection:** databanks; exact retained source-map `ui/app/plugins/databank/DatabankFilterByCorrelation/source-map.json`. Target `ui/app/plugins/databank/DatabankFilterByCorrelation/databankFilterByCorrelationPopup.tsx`; wire databank selection, actual resource mutations and saved/exported artifact IDs.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Create:** `app/plugins/databank/DatabankFilterByCorrelation/service.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/databank/DatabankFilterByCorrelation/routes.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/databank/DatabankFilterByCorrelation/contracts.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/databank/DatabankFilterByCorrelation/README.md`
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_results_databank_filter_by_correlation.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/results_databank_filter_by_correlation.json`
  - Store versioned paraphrased donor input/output fixtures.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/plugins/databank/DatabankFilterByCorrelation/databankFilterByCorrelationPopup.tsx`
  - Display databank selection, actual resource mutations and saved/exported artifact IDs from backend responses; preserve layout.
- **Modify:** `ui/app/plugins/databank/DatabankFilterByCorrelation/module.ts`
  - Display databank selection, actual resource mutations and saved/exported artifact IDs from backend responses; preserve layout.
- **Create:** `ui/app/plugins/databank/DatabankFilterByCorrelation/backendClient.ts`
  - Typed domain client over host transport; ratify route/schema/version, errors and cancellation. Reuse this proposed owner if delivered earlier.
- **Create:** `ui/tests/unit/backend-connections/feat-results-databank-filter-by-correlation.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-results-databanks-exports-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Calculate qualified correlations and apply selection/filter rules; verify alignment, sample basis, undefined correlation and threshold equality.
- [ ] **Step 4:** `FR-RESULTS-DATABANK-FILTER-BY-CORRELATION-DATABANK-FILTER-BY-CORRELATION-SERVLET-CONTRACT` → `com.strategyquant.plugin.Databank.impl.FilterByCorrelation.DatabankFilterByCorrelationServlet`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-RESULTS-DATABANK-FILTER-BY-CORRELATION-DATABANK-FILTER-BY-CORRELATION-SERVLET-EXECUTE` → `com.strategyquant.plugin.Databank.impl.FilterByCorrelation.DatabankFilterByCorrelationServlet.execute`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 7:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 8:** Connect retained UI: Ratify the feature-owned wire contract; bind databank selection, actual resource mutations and saved/exported artifact IDs to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 9:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_results_databank_filter_by_correlation.py --no-cov`; expect alignment, sample basis, undefined correlation and threshold equality; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture alignment, sample basis, undefined correlation and threshold equality and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-results-databank-filter-by-correlation.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-results-databanks-exports-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise databanks for FEAT-RESULTS-DATABANK-FILTER-BY-CORRELATION; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.

# 8.12 FEAT-RESULTS-DATABANK-RENAME - DatabankRename.jar

## 1. Objective

- **Goal:** Rename identified resources atomically through the owning service.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Render authoritative databanks, result analysis, charts and exports.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/plugins/DatabankRename/DatabankRename.jar`; 2 class declarations; SHA-256 `f3fa6e90b8a222f61a608081bec6d71ba3d6b234099cb37064299441b8a08b84`.
- **Inspected reference:** `HARUQUANTAI_ROOT/docs/sqx/Results/DatabankRename.md`; roadmap allocation `FEAT-RESULTS-DATABANK-RENAME`.
- **Owner:** `app/plugins/databank/DatabankRename/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Databank views/actions/rename and correlation projections; downstream P09–P13.
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/plugins/DatabankRename/DatabankRename.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/plugins/DatabankRename/DatabankRename.jar" com.strategyquant.plugin.Databank.impl.Rename.DatabankRenameServlet`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_REFERENCE_ROOT/internal/plugins/DatabankRename`; `SQX_REFERENCE_ROOT/internal/plugins/ResultsDatabankActions`; `SQX_REFERENCE_ROOT/internal/plugins/ProjectDatabanks`. Inspect `SQX_REFERENCE_ROOT/internal/plugins/DatabankRename/ui/DatabankRenamePopupCtrl.js`; `SQX_REFERENCE_ROOT/internal/plugins/DatabankRename/ui/databankRenamePopup.html`; `SQX_REFERENCE_ROOT/internal/plugins/DatabankRename/ui/module.js`.
- **Existing UI connection:** databanks; exact retained source-map `ui/app/plugins/databank/DatabankRename/source-map.json`. Target `ui/app/plugins/databank/DatabankRename/ui/DatabankRenamePopupCtrl.ts`; wire databank selection, actual resource mutations and saved/exported artifact IDs.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Create:** `app/plugins/databank/DatabankRename/service.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/databank/DatabankRename/routes.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/databank/DatabankRename/contracts.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/databank/DatabankRename/README.md`
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_results_databank_rename.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/results_databank_rename.json`
  - Store versioned paraphrased donor input/output fixtures.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/plugins/databank/DatabankRename/ui/DatabankRenamePopupCtrl.ts`
  - Await backend validation/commands; bind actual result and job states to existing controls.
- **Modify:** `ui/app/plugins/databank/DatabankRename/ui/databankRenamePopup.tsx`
  - Display databank selection, actual resource mutations and saved/exported artifact IDs from backend responses; preserve layout.
- **Modify:** `ui/app/plugins/databank/DatabankRename/ui/module.ts`
  - Display databank selection, actual resource mutations and saved/exported artifact IDs from backend responses; preserve layout.
- **Create:** `ui/app/plugins/databank/DatabankRename/backendClient.ts`
  - Typed domain client over host transport; ratify route/schema/version, errors and cancellation. Reuse this proposed owner if delivered earlier.
- **Create:** `ui/tests/unit/backend-connections/feat-results-databank-rename.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-results-databanks-exports-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Rename identified resources atomically through the owning service; verify collision, stable IDs, history and permission rejection.
- [ ] **Step 4:** `FR-RESULTS-DATABANK-RENAME-DATABANK-RENAME-SERVLET-CONTRACT` → `com.strategyquant.plugin.Databank.impl.Rename.DatabankRenameServlet`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-RESULTS-DATABANK-RENAME-DATABANK-RENAME-SERVLET-EXECUTE` → `com.strategyquant.plugin.Databank.impl.Rename.DatabankRenameServlet.execute`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 7:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 8:** Connect retained UI: Ratify the feature-owned wire contract; bind databank selection, actual resource mutations and saved/exported artifact IDs to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 9:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_results_databank_rename.py --no-cov`; expect collision, stable IDs, history and permission rejection; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture collision, stable IDs, history and permission rejection and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-results-databank-rename.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-results-databanks-exports-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise databanks for FEAT-RESULTS-DATABANK-RENAME; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.

# 8.13 FEAT-RESULTS-EQUITY-CHART-BENCHMARK - EquityChartBenchmark.jar

## 1. Objective

- **Goal:** Project the named result series with verified metrics and sampling.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Render authoritative databanks, result analysis, charts and exports.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/plugins/EquityChartBenchmark/EquityChartBenchmark.jar`; 3 class declarations; SHA-256 `d04a9b53951cf574b7bb0bf58bc0b9c39820fca334f55cf7f429d541dd1a8877`.
- **Inspected reference:** `HARUQUANTAI_ROOT/docs/sqx/Results/EquityChartBenchmark.md`; roadmap allocation `FEAT-RESULTS-EQUITY-CHART-BENCHMARK`.
- **Owner:** `app/plugins/results/EquityChartBenchmark/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Result chart calculation/projection; downstream .
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/plugins/EquityChartBenchmark/EquityChartBenchmark.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/plugins/EquityChartBenchmark/EquityChartBenchmark.jar" com.strategyquant.plugin.EquityChart.impl.Benchmark.Benchmark`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_REFERENCE_ROOT/internal/plugins/EquityChartBenchmark`; `SQX_REFERENCE_ROOT/internal/plugins/ResultsEquityChart`. Inspect `SQX_REFERENCE_ROOT/internal/plugins/ResultsEquityChart/EquityChartService.js`.
- **Existing UI connection:** equity chart; proposed shared consumer; verify the exact existing control and public contract before implementation. Target `ui/app/plugins/project/ResultsEquityChart/EquityChartCtrl.ts`; wire selected result/sample, actual equity series and backend-computed benchmark/drawdown/volatility/volume overlays.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Create:** `app/plugins/results/EquityChartBenchmark/series.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/results/EquityChartBenchmark/contracts.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/results/EquityChartBenchmark/README.md`
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_results_equity_chart_benchmark.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/results_equity_chart_benchmark.json`
  - Store versioned paraphrased donor input/output fixtures.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/plugins/project/ResultsEquityChart/EquityChartCtrl.ts`
  - Await backend validation/commands; bind actual result and job states to existing controls.
- **Modify:** `ui/app/plugins/project/ResultsEquityChart/benchmark/BenchmarkCtrl.ts`
  - Await backend validation/commands; bind actual result and job states to existing controls.
- **Modify:** `ui/app/plugins/project/ProjectWorkbench/results/resultsModel.ts`
  - Display selected result/sample, actual equity series and backend-computed benchmark/drawdown/volatility/volume overlays from backend responses; preserve layout.
- **Create:** `ui/app/workspace/Results/resultsClient.ts`
  - Typed domain client over host transport; ratify route/schema/version, errors and cancellation. Reuse this proposed owner if delivered earlier.
- **Create:** `ui/tests/unit/backend-connections/feat-results-equity-chart-benchmark.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-results-databanks-exports-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Project the named result series with verified metrics and sampling; verify units, timestamp alignment, missing samples and reconciled source totals.
- [ ] **Step 4:** `FR-RESULTS-EQUITY-CHART-BENCHMARK-BENCHMARK-CONTRACT` → `com.strategyquant.plugin.EquityChart.impl.Benchmark.Benchmark`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-RESULTS-EQUITY-CHART-BENCHMARK-BENCHMARK-GET-PREFERRED-POSITION` → `com.strategyquant.plugin.EquityChart.impl.Benchmark.Benchmark.getPreferredPosition`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** `FR-RESULTS-EQUITY-CHART-BENCHMARK-BENCHMARK-INIT-PLUGIN` → `com.strategyquant.plugin.EquityChart.impl.Benchmark.Benchmark.initPlugin`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 7:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 8:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 9:** Connect retained UI: Ratify the feature-owned wire contract; bind selected result/sample, actual equity series and backend-computed benchmark/drawdown/volatility/volume overlays to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 10:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_results_equity_chart_benchmark.py --no-cov`; expect units, timestamp alignment, missing samples and reconciled source totals; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture units, timestamp alignment, missing samples and reconciled source totals and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-results-equity-chart-benchmark.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-results-databanks-exports-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise equity chart for FEAT-RESULTS-EQUITY-CHART-BENCHMARK; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.

# 8.14 FEAT-RESULTS-EQUITY-CHART-DAILY-CHART - EquityChartDailyChart.jar

## 1. Objective

- **Goal:** Project the named result series with verified metrics and sampling.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Render authoritative databanks, result analysis, charts and exports.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/plugins/EquityChartDailyChart/EquityChartDailyChart.jar`; 1 class declarations; SHA-256 `5be9e3fbc72c350e9c1d8a06e3493900286338193e3a1ac0620df5ad07c1e797`.
- **Inspected reference:** `HARUQUANTAI_ROOT/docs/sqx/Results/EquityChartDailyChart.md`; roadmap allocation `FEAT-RESULTS-EQUITY-CHART-DAILY-CHART`.
- **Owner:** `app/plugins/results/EquityChartDailyChart/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Result chart calculation/projection; downstream .
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/plugins/EquityChartDailyChart/EquityChartDailyChart.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/plugins/EquityChartDailyChart/EquityChartDailyChart.jar" com.strategyquant.plugin.EquityChart.impl.DailyChart.DailyChart`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_REFERENCE_ROOT/internal/plugins/EquityChartDailyChart`; `SQX_REFERENCE_ROOT/internal/plugins/ResultsEquityChart`. Inspect `SQX_REFERENCE_ROOT/internal/plugins/ResultsEquityChart/EquityChartService.js`.
- **Existing UI connection:** equity chart; proposed shared consumer; verify the exact existing control and public contract before implementation. Target `ui/app/plugins/project/ResultsEquityChart/EquityChartCtrl.ts`; wire selected result/sample, actual equity series and backend-computed benchmark/drawdown/volatility/volume overlays.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Create:** `app/plugins/results/EquityChartDailyChart/series.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/results/EquityChartDailyChart/contracts.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/results/EquityChartDailyChart/README.md`
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_results_equity_chart_daily_chart.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/results_equity_chart_daily_chart.json`
  - Store versioned paraphrased donor input/output fixtures.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/plugins/project/ResultsEquityChart/EquityChartCtrl.ts`
  - Await backend validation/commands; bind actual result and job states to existing controls.
- **Modify:** `ui/app/plugins/project/ResultsEquityChart/benchmark/BenchmarkCtrl.ts`
  - Await backend validation/commands; bind actual result and job states to existing controls.
- **Modify:** `ui/app/plugins/project/ProjectWorkbench/results/resultsModel.ts`
  - Display selected result/sample, actual equity series and backend-computed benchmark/drawdown/volatility/volume overlays from backend responses; preserve layout.
- **Create:** `ui/app/workspace/Results/resultsClient.ts`
  - Typed domain client over host transport; ratify route/schema/version, errors and cancellation. Reuse this proposed owner if delivered earlier.
- **Create:** `ui/tests/unit/backend-connections/feat-results-equity-chart-daily-chart.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-results-databanks-exports-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Project the named result series with verified metrics and sampling; verify units, timestamp alignment, missing samples and reconciled source totals.
- [ ] **Step 4:** `FR-RESULTS-EQUITY-CHART-DAILY-CHART-DAILY-CHART-CONTRACT` → `com.strategyquant.plugin.EquityChart.impl.DailyChart.DailyChart`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-RESULTS-EQUITY-CHART-DAILY-CHART-DAILY-CHART-GET-PREFERRED-POSITION` → `com.strategyquant.plugin.EquityChart.impl.DailyChart.DailyChart.getPreferredPosition`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** `FR-RESULTS-EQUITY-CHART-DAILY-CHART-DAILY-CHART-INIT-PLUGIN` → `com.strategyquant.plugin.EquityChart.impl.DailyChart.DailyChart.initPlugin`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 7:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 8:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 9:** Connect retained UI: Ratify the feature-owned wire contract; bind selected result/sample, actual equity series and backend-computed benchmark/drawdown/volatility/volume overlays to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 10:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_results_equity_chart_daily_chart.py --no-cov`; expect units, timestamp alignment, missing samples and reconciled source totals; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture units, timestamp alignment, missing samples and reconciled source totals and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-results-equity-chart-daily-chart.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-results-databanks-exports-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise equity chart for FEAT-RESULTS-EQUITY-CHART-DAILY-CHART; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.

# 8.15 FEAT-RESULTS-EQUITY-CHART-DRAWDOWN - EquityChartDrawdown.jar

## 1. Objective

- **Goal:** Project the named result series with verified metrics and sampling.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Render authoritative databanks, result analysis, charts and exports.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/plugins/EquityChartDrawdown/EquityChartDrawdown.jar`; 1 class declarations; SHA-256 `5d0f0861a80c860dc3a5c2e77a503639e990b146c376c7ba5e611c2a96022b7c`.
- **Inspected reference:** `HARUQUANTAI_ROOT/docs/sqx/Results/EquityChartDrawdown.md`; roadmap allocation `FEAT-RESULTS-EQUITY-CHART-DRAWDOWN`.
- **Owner:** `app/plugins/results/EquityChartDrawdown/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Result chart calculation/projection; downstream .
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/plugins/EquityChartDrawdown/EquityChartDrawdown.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/plugins/EquityChartDrawdown/EquityChartDrawdown.jar" com.strategyquant.plugin.EquityChart.impl.Drawdown.EquityChartDrawdown`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_REFERENCE_ROOT/internal/plugins/EquityChartDrawdown`; `SQX_REFERENCE_ROOT/internal/plugins/ResultsEquityChart`. Inspect `SQX_REFERENCE_ROOT/internal/plugins/ResultsEquityChart/EquityChartService.js`.
- **Existing UI connection:** equity chart; proposed shared consumer; verify the exact existing control and public contract before implementation. Target `ui/app/plugins/project/ResultsEquityChart/EquityChartCtrl.ts`; wire selected result/sample, actual equity series and backend-computed benchmark/drawdown/volatility/volume overlays.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Create:** `app/plugins/results/EquityChartDrawdown/series.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/results/EquityChartDrawdown/contracts.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/results/EquityChartDrawdown/README.md`
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_results_equity_chart_drawdown.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/results_equity_chart_drawdown.json`
  - Store versioned paraphrased donor input/output fixtures.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/plugins/project/ResultsEquityChart/EquityChartCtrl.ts`
  - Await backend validation/commands; bind actual result and job states to existing controls.
- **Modify:** `ui/app/plugins/project/ResultsEquityChart/benchmark/BenchmarkCtrl.ts`
  - Await backend validation/commands; bind actual result and job states to existing controls.
- **Modify:** `ui/app/plugins/project/ProjectWorkbench/results/resultsModel.ts`
  - Display selected result/sample, actual equity series and backend-computed benchmark/drawdown/volatility/volume overlays from backend responses; preserve layout.
- **Create:** `ui/app/workspace/Results/resultsClient.ts`
  - Typed domain client over host transport; ratify route/schema/version, errors and cancellation. Reuse this proposed owner if delivered earlier.
- **Create:** `ui/tests/unit/backend-connections/feat-results-equity-chart-drawdown.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-results-databanks-exports-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Project the named result series with verified metrics and sampling; verify units, timestamp alignment, missing samples and reconciled source totals.
- [ ] **Step 4:** `FR-RESULTS-EQUITY-CHART-DRAWDOWN-EQUITY-CHART-DRAWDOWN-CONTRACT` → `com.strategyquant.plugin.EquityChart.impl.Drawdown.EquityChartDrawdown`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-RESULTS-EQUITY-CHART-DRAWDOWN-EQUITY-CHART-DRAWDOWN-GET-PREFERRED-POSITION` → `com.strategyquant.plugin.EquityChart.impl.Drawdown.EquityChartDrawdown.getPreferredPosition`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** `FR-RESULTS-EQUITY-CHART-DRAWDOWN-EQUITY-CHART-DRAWDOWN-INIT-PLUGIN` → `com.strategyquant.plugin.EquityChart.impl.Drawdown.EquityChartDrawdown.initPlugin`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 7:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 8:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 9:** Connect retained UI: Ratify the feature-owned wire contract; bind selected result/sample, actual equity series and backend-computed benchmark/drawdown/volatility/volume overlays to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 10:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_results_equity_chart_drawdown.py --no-cov`; expect units, timestamp alignment, missing samples and reconciled source totals; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture units, timestamp alignment, missing samples and reconciled source totals and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-results-equity-chart-drawdown.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-results-databanks-exports-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise equity chart for FEAT-RESULTS-EQUITY-CHART-DRAWDOWN; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.

# 8.16 FEAT-RESULTS-EQUITY-CHART-VOLATILITY - EquityChartVolatility.jar

## 1. Objective

- **Goal:** Project the named result series with verified metrics and sampling.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Render authoritative databanks, result analysis, charts and exports.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/plugins/EquityChartVolatility/EquityChartVolatility.jar`; 1 class declarations; SHA-256 `dd60204046dca5a6cdead97460cb7854eb2ad63f745cc216bc8f2bc824152608`.
- **Inspected reference:** `HARUQUANTAI_ROOT/docs/sqx/Results/EquityChartVolatility.md`; roadmap allocation `FEAT-RESULTS-EQUITY-CHART-VOLATILITY`.
- **Owner:** `app/plugins/results/EquityChartVolatility/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Result chart calculation/projection; downstream .
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/plugins/EquityChartVolatility/EquityChartVolatility.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/plugins/EquityChartVolatility/EquityChartVolatility.jar" com.strategyquant.plugin.EquityChart.impl.Volatility.Volatility`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_REFERENCE_ROOT/internal/plugins/EquityChartVolatility`; `SQX_REFERENCE_ROOT/internal/plugins/ResultsEquityChart`. Inspect `SQX_REFERENCE_ROOT/internal/plugins/ResultsEquityChart/EquityChartService.js`.
- **Existing UI connection:** equity chart; proposed shared consumer; verify the exact existing control and public contract before implementation. Target `ui/app/plugins/project/ResultsEquityChart/EquityChartCtrl.ts`; wire selected result/sample, actual equity series and backend-computed benchmark/drawdown/volatility/volume overlays.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Create:** `app/plugins/results/EquityChartVolatility/series.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/results/EquityChartVolatility/contracts.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/results/EquityChartVolatility/README.md`
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_results_equity_chart_volatility.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/results_equity_chart_volatility.json`
  - Store versioned paraphrased donor input/output fixtures.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/plugins/project/ResultsEquityChart/EquityChartCtrl.ts`
  - Await backend validation/commands; bind actual result and job states to existing controls.
- **Modify:** `ui/app/plugins/project/ResultsEquityChart/benchmark/BenchmarkCtrl.ts`
  - Await backend validation/commands; bind actual result and job states to existing controls.
- **Modify:** `ui/app/plugins/project/ProjectWorkbench/results/resultsModel.ts`
  - Display selected result/sample, actual equity series and backend-computed benchmark/drawdown/volatility/volume overlays from backend responses; preserve layout.
- **Create:** `ui/app/workspace/Results/resultsClient.ts`
  - Typed domain client over host transport; ratify route/schema/version, errors and cancellation. Reuse this proposed owner if delivered earlier.
- **Create:** `ui/tests/unit/backend-connections/feat-results-equity-chart-volatility.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-results-databanks-exports-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Project the named result series with verified metrics and sampling; verify units, timestamp alignment, missing samples and reconciled source totals.
- [ ] **Step 4:** `FR-RESULTS-EQUITY-CHART-VOLATILITY-VOLATILITY-CONTRACT` → `com.strategyquant.plugin.EquityChart.impl.Volatility.Volatility`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-RESULTS-EQUITY-CHART-VOLATILITY-VOLATILITY-GET-PREFERRED-POSITION` → `com.strategyquant.plugin.EquityChart.impl.Volatility.Volatility.getPreferredPosition`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** `FR-RESULTS-EQUITY-CHART-VOLATILITY-VOLATILITY-INIT-PLUGIN` → `com.strategyquant.plugin.EquityChart.impl.Volatility.Volatility.initPlugin`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 7:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 8:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 9:** Connect retained UI: Ratify the feature-owned wire contract; bind selected result/sample, actual equity series and backend-computed benchmark/drawdown/volatility/volume overlays to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 10:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_results_equity_chart_volatility.py --no-cov`; expect units, timestamp alignment, missing samples and reconciled source totals; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture units, timestamp alignment, missing samples and reconciled source totals and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-results-equity-chart-volatility.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-results-databanks-exports-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise equity chart for FEAT-RESULTS-EQUITY-CHART-VOLATILITY; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.

# 8.17 FEAT-RESULTS-EQUITY-CHART-VOLUME - EquityChartVolume.jar

## 1. Objective

- **Goal:** Project the named result series with verified metrics and sampling.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Render authoritative databanks, result analysis, charts and exports.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/plugins/EquityChartVolume/EquityChartVolume.jar`; 1 class declarations; SHA-256 `5cf96acea98addb47b86d599117d0e97c77321230250ec94a18f05a3588da8a8`.
- **Inspected reference:** `HARUQUANTAI_ROOT/docs/sqx/Results/EquityChartVolume.md`; roadmap allocation `FEAT-RESULTS-EQUITY-CHART-VOLUME`.
- **Owner:** `app/plugins/results/EquityChartVolume/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Result chart calculation/projection; downstream .
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/plugins/EquityChartVolume/EquityChartVolume.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/plugins/EquityChartVolume/EquityChartVolume.jar" com.strategyquant.plugin.EquityChart.impl.Volume.EquityChartVolume`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_REFERENCE_ROOT/internal/plugins/EquityChartVolume`; `SQX_REFERENCE_ROOT/internal/plugins/ResultsEquityChart`. Inspect `SQX_REFERENCE_ROOT/internal/plugins/ResultsEquityChart/EquityChartService.js`.
- **Existing UI connection:** equity chart; proposed shared consumer; verify the exact existing control and public contract before implementation. Target `ui/app/plugins/project/ResultsEquityChart/EquityChartCtrl.ts`; wire selected result/sample, actual equity series and backend-computed benchmark/drawdown/volatility/volume overlays.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Create:** `app/plugins/results/EquityChartVolume/series.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/results/EquityChartVolume/contracts.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/results/EquityChartVolume/README.md`
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_results_equity_chart_volume.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/results_equity_chart_volume.json`
  - Store versioned paraphrased donor input/output fixtures.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/plugins/project/ResultsEquityChart/EquityChartCtrl.ts`
  - Await backend validation/commands; bind actual result and job states to existing controls.
- **Modify:** `ui/app/plugins/project/ResultsEquityChart/benchmark/BenchmarkCtrl.ts`
  - Await backend validation/commands; bind actual result and job states to existing controls.
- **Modify:** `ui/app/plugins/project/ProjectWorkbench/results/resultsModel.ts`
  - Display selected result/sample, actual equity series and backend-computed benchmark/drawdown/volatility/volume overlays from backend responses; preserve layout.
- **Create:** `ui/app/workspace/Results/resultsClient.ts`
  - Typed domain client over host transport; ratify route/schema/version, errors and cancellation. Reuse this proposed owner if delivered earlier.
- **Create:** `ui/tests/unit/backend-connections/feat-results-equity-chart-volume.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-results-databanks-exports-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Project the named result series with verified metrics and sampling; verify units, timestamp alignment, missing samples and reconciled source totals.
- [ ] **Step 4:** `FR-RESULTS-EQUITY-CHART-VOLUME-EQUITY-CHART-VOLUME-CONTRACT` → `com.strategyquant.plugin.EquityChart.impl.Volume.EquityChartVolume`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-RESULTS-EQUITY-CHART-VOLUME-EQUITY-CHART-VOLUME-GET-PREFERRED-POSITION` → `com.strategyquant.plugin.EquityChart.impl.Volume.EquityChartVolume.getPreferredPosition`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** `FR-RESULTS-EQUITY-CHART-VOLUME-EQUITY-CHART-VOLUME-INIT-PLUGIN` → `com.strategyquant.plugin.EquityChart.impl.Volume.EquityChartVolume.initPlugin`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 7:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 8:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 9:** Connect retained UI: Ratify the feature-owned wire contract; bind selected result/sample, actual equity series and backend-computed benchmark/drawdown/volatility/volume overlays to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 10:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_results_equity_chart_volume.py --no-cov`; expect units, timestamp alignment, missing samples and reconciled source totals; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture units, timestamp alignment, missing samples and reconciled source totals and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-results-equity-chart-volume.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-results-databanks-exports-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise equity chart for FEAT-RESULTS-EQUITY-CHART-VOLUME; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.

# 8.18 FEAT-RESULTS-RESULTS-CHART - ResultsChart.jar

## 1. Objective

- **Goal:** Project the named result series with verified metrics and sampling.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Render authoritative databanks, result analysis, charts and exports.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/plugins/ResultsChart/ResultsChart.jar`; 2 class declarations; SHA-256 `33cca54b95a76fd447a1664d2def1b46d9f2da1f429c788df6c0b76597a793ba`.
- **Inspected reference:** `HARUQUANTAI_ROOT/docs/sqx/Results/ResultsChart.md`; roadmap allocation `FEAT-RESULTS-RESULTS-CHART`.
- **Owner:** `app/plugins/results/ResultsChart/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Shared result exploration, stockpicker reporting, trade analysis and projections; downstream .
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/plugins/ResultsChart/ResultsChart.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/plugins/ResultsChart/ResultsChart.jar" com.strategyquant.plugin.Results.impl.Chart.ChartServlet`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_REFERENCE_ROOT/internal/plugins/ResultsChart`; `SQX_REFERENCE_ROOT/internal/web/RESULTS`; `SQX_REFERENCE_ROOT/internal/plugins/ProjectResults`. Inspect `SQX_REFERENCE_ROOT/internal/plugins/ResultsChart/ResultsChartService.js`; `SQX_REFERENCE_ROOT/internal/plugins/ResultsChart/ResultsChartCtrl.js`; `SQX_REFERENCE_ROOT/internal/plugins/ResultsChart/chart.html`.
- **Existing UI connection:** Results; exact retained source-map `ui/app/plugins/project/ResultsChart/source-map.json`. Target `ui/app/plugins/project/ResultsChart/chart.tsx`; wire persisted run/result lookup, selected sample, trades and reconciled metrics.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Create:** `app/plugins/results/ResultsChart/service.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/results/ResultsChart/contracts.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/results/ResultsChart/routes.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/results/ResultsChart/README.md`
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_results_results_chart.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/results_results_chart.json`
  - Store versioned paraphrased donor input/output fixtures.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/plugins/project/ResultsChart/chart.tsx`
  - Display persisted run/result lookup, selected sample, trades and reconciled metrics from backend responses; preserve layout.
- **Modify:** `ui/app/plugins/project/ResultsChart/module.ts`
  - Display persisted run/result lookup, selected sample, trades and reconciled metrics from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/Results/ResultsWorkspace.tsx`
  - Display persisted run/result lookup, selected sample, trades and reconciled metrics from backend responses; preserve layout.
- **Create:** `ui/app/plugins/project/ResultsChart/backendClient.ts`
  - Typed domain client over host transport; ratify route/schema/version, errors and cancellation. Reuse this proposed owner if delivered earlier.
- **Create:** `ui/tests/unit/backend-connections/feat-results-results-chart.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-results-databanks-exports-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Project the named result series with verified metrics and sampling; verify units, timestamp alignment, missing samples and reconciled source totals.
- [ ] **Step 4:** `FR-RESULTS-RESULTS-CHART-CHART-SERVLET-CONTRACT` → `com.strategyquant.plugin.Results.impl.Chart.ChartServlet`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-RESULTS-RESULTS-CHART-CHART-SERVLET-EXECUTE` → `com.strategyquant.plugin.Results.impl.Chart.ChartServlet.execute`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 7:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 8:** Connect retained UI: Ratify the feature-owned wire contract; bind persisted run/result lookup, selected sample, trades and reconciled metrics to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 9:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_results_results_chart.py --no-cov`; expect units, timestamp alignment, missing samples and reconciled source totals; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture units, timestamp alignment, missing samples and reconciled source totals and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-results-results-chart.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-results-databanks-exports-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise Results for FEAT-RESULTS-RESULTS-CHART; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.

# 8.19 FEAT-RESULTS-RESULTS-DATABANK-ACTIONS - ResultsDatabankActions.jar

## 1. Objective

- **Goal:** Implement authoritative DatabankActions result projections/actions.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Render authoritative databanks, result analysis, charts and exports.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/plugins/ResultsDatabankActions/ResultsDatabankActions.jar`; 3 class declarations; SHA-256 `2542b663f56004be15797da27f223903b78eea4a0208a28754d741737755cc74`.
- **Inspected reference:** `HARUQUANTAI_ROOT/docs/sqx/Results/ResultsDatabankActions.md`; roadmap allocation `FEAT-RESULTS-RESULTS-DATABANK-ACTIONS`.
- **Owner:** `app/plugins/databank/ResultsDatabankActions/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Databank views/actions/rename and correlation projections; downstream P09–P13.
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/plugins/ResultsDatabankActions/ResultsDatabankActions.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/plugins/ResultsDatabankActions/ResultsDatabankActions.jar" com.strategyquant.plugin.Results.impl.DatabankActions.DatabankActionsServlet`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_REFERENCE_ROOT/internal/plugins/ResultsDatabankActions`; `SQX_REFERENCE_ROOT/internal/plugins/ProjectDatabanks`. Inspect `SQX_REFERENCE_ROOT/internal/plugins/ResultsDatabankActions/DatabankActionsService.js`; `SQX_REFERENCE_ROOT/internal/plugins/ResultsDatabankActions/load/LoadService.js`; `SQX_REFERENCE_ROOT/internal/plugins/ResultsDatabankActions/save/SaveButtonService.js`.
- **Existing UI connection:** databanks; exact retained source-map `ui/app/plugins/databank/ResultsDatabankActions/source-map.json`. Target `ui/app/plugins/databank/ResultsDatabankActions/DatabankActionsService.ts`; wire databank selection, actual resource mutations and saved/exported artifact IDs.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Create:** `app/plugins/databank/ResultsDatabankActions/service.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/databank/ResultsDatabankActions/routes.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/databank/ResultsDatabankActions/contracts.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/databank/ResultsDatabankActions/README.md`
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_results_results_databank_actions.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/results_results_databank_actions.json`
  - Store versioned paraphrased donor input/output fixtures.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/plugins/databank/ResultsDatabankActions/DatabankActionsService.ts`
  - Call owned typed commands; map responses/errors to current dialogs.
- **Modify:** `ui/app/plugins/databank/ResultsDatabankActions/load/LoadService.ts`
  - Call owned typed commands; map responses/errors to current dialogs.
- **Modify:** `ui/app/plugins/databank/ResultsDatabankActions/save/SaveButtonService.ts`
  - Call owned typed commands; map responses/errors to current dialogs.
- **Modify:** `ui/app/plugins/databank/ResultsDatabankActions/load/loadPopup.tsx`
  - Display databank selection, actual resource mutations and saved/exported artifact IDs from backend responses; preserve layout.
- **Create:** `ui/tests/unit/backend-connections/feat-results-results-databank-actions.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-results-databanks-exports-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Implement authoritative DatabankActions result projections/actions; verify metric provenance, result identity, empty/error state and stored-value reconciliation.
- [ ] **Step 4:** `FR-RESULTS-RESULTS-DATABANK-ACTIONS-DATABANK-ACTIONS-SERVLET-CONTRACT` → `com.strategyquant.plugin.Results.impl.DatabankActions.DatabankActionsServlet`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-RESULTS-RESULTS-DATABANK-ACTIONS-DATABANK-ACTIONS-SERVLET-EXECUTE` → `com.strategyquant.plugin.Results.impl.DatabankActions.DatabankActionsServlet.execute`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 7:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 8:** Connect retained UI: Ratify the feature-owned wire contract; bind databank selection, actual resource mutations and saved/exported artifact IDs to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 9:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_results_results_databank_actions.py --no-cov`; expect metric provenance, result identity, empty/error state and stored-value reconciliation; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture metric provenance, result identity, empty/error state and stored-value reconciliation and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-results-results-databank-actions.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-results-databanks-exports-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise databanks for FEAT-RESULTS-RESULTS-DATABANK-ACTIONS; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.

# 8.20 FEAT-RESULTS-RESULTS-DATABANK-VIEWS - ResultsDatabankViews.jar

## 1. Objective

- **Goal:** Implement authoritative DatabankViews result projections/actions.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Render authoritative databanks, result analysis, charts and exports.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/plugins/ResultsDatabankViews/ResultsDatabankViews.jar`; 2 class declarations; SHA-256 `22fe5655735ae9dda9226304966ea67c38f47b1ef7244d5dfed0c9249a61ed20`.
- **Inspected reference:** `HARUQUANTAI_ROOT/docs/sqx/Results/ResultsDatabankViews.md`; roadmap allocation `FEAT-RESULTS-RESULTS-DATABANK-VIEWS`.
- **Owner:** `app/plugins/databank/ResultsDatabankViews/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Databank views/actions/rename and correlation projections; downstream P09–P13.
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/plugins/ResultsDatabankViews/ResultsDatabankViews.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/plugins/ResultsDatabankViews/ResultsDatabankViews.jar" com.strategyquant.plugin.Results.impl.DatabankViews.DatabankViewsServlet`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_REFERENCE_ROOT/internal/plugins/ResultsDatabankViews`; `SQX_REFERENCE_ROOT/internal/plugins/ResultsDatabankActions`; `SQX_REFERENCE_ROOT/internal/plugins/ProjectDatabanks`. Inspect `SQX_REFERENCE_ROOT/internal/plugins/ResultsDatabankViews/DatabankViewsService.js`; `SQX_REFERENCE_ROOT/internal/plugins/ResultsDatabankViews/DatabankViewsCtrl.js`; `SQX_REFERENCE_ROOT/internal/plugins/ResultsDatabankViews/databankViews.html`.
- **Existing UI connection:** databanks; exact retained source-map `ui/app/plugins/databank/ResultsDatabankViews/source-map.json`. Target `ui/app/plugins/databank/ResultsDatabankViews/DatabankViewsService.ts`; wire databank selection, actual resource mutations and saved/exported artifact IDs.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Create:** `app/plugins/databank/ResultsDatabankViews/service.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/databank/ResultsDatabankViews/routes.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/databank/ResultsDatabankViews/contracts.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/databank/ResultsDatabankViews/README.md`
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_results_results_databank_views.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/results_results_databank_views.json`
  - Store versioned paraphrased donor input/output fixtures.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/plugins/databank/ResultsDatabankViews/DatabankViewsService.ts`
  - Call owned typed commands; map responses/errors to current dialogs.
- **Modify:** `ui/app/plugins/databank/ResultsDatabankViews/DatabankViewsCtrl.ts`
  - Await backend validation/commands; bind actual result and job states to existing controls.
- **Modify:** `ui/app/plugins/databank/ResultsDatabankViews/databankViews.tsx`
  - Display databank selection, actual resource mutations and saved/exported artifact IDs from backend responses; preserve layout.
- **Create:** `ui/tests/unit/backend-connections/feat-results-results-databank-views.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-results-databanks-exports-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Implement authoritative DatabankViews result projections/actions; verify metric provenance, result identity, empty/error state and stored-value reconciliation.
- [ ] **Step 4:** `FR-RESULTS-RESULTS-DATABANK-VIEWS-DATABANK-VIEWS-SERVLET-CONTRACT` → `com.strategyquant.plugin.Results.impl.DatabankViews.DatabankViewsServlet`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-RESULTS-RESULTS-DATABANK-VIEWS-DATABANK-VIEWS-SERVLET-EXECUTE` → `com.strategyquant.plugin.Results.impl.DatabankViews.DatabankViewsServlet.execute`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 7:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 8:** Connect retained UI: Ratify the feature-owned wire contract; bind databank selection, actual resource mutations and saved/exported artifact IDs to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 9:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_results_results_databank_views.py --no-cov`; expect metric provenance, result identity, empty/error state and stored-value reconciliation; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture metric provenance, result identity, empty/error state and stored-value reconciliation and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-results-results-databank-views.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-results-databanks-exports-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise databanks for FEAT-RESULTS-RESULTS-DATABANK-VIEWS; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.

# 8.21 FEAT-RESULTS-RESULTS-EQUITY-CHART - ResultsEquityChart.jar

## 1. Objective

- **Goal:** Project the named result series with verified metrics and sampling.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Render authoritative databanks, result analysis, charts and exports.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/plugins/ResultsEquityChart/ResultsEquityChart.jar`; 2 class declarations; SHA-256 `d13f1ffdd75ec94f33d7c383b5a8239f3f1a28700b4aed2303041cbd936e4645`.
- **Inspected reference:** `HARUQUANTAI_ROOT/docs/sqx/Results/ResultsEquityChart.md`; roadmap allocation `FEAT-RESULTS-RESULTS-EQUITY-CHART`.
- **Owner:** `app/plugins/results/ResultsEquityChart/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Shared result exploration, stockpicker reporting, trade analysis and projections; downstream .
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/plugins/ResultsEquityChart/ResultsEquityChart.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/plugins/ResultsEquityChart/ResultsEquityChart.jar" com.strategyquant.plugin.Results.impl.EquityChart.EquityChartServlet`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_REFERENCE_ROOT/internal/plugins/ResultsEquityChart`; `SQX_REFERENCE_ROOT/internal/web/RESULTS`; `SQX_REFERENCE_ROOT/internal/plugins/ProjectResults`. Inspect `SQX_REFERENCE_ROOT/internal/plugins/ResultsEquityChart/EquityChartService.js`; `SQX_REFERENCE_ROOT/internal/plugins/ResultsEquityChart/EquityChartCtrl.js`; `SQX_REFERENCE_ROOT/internal/plugins/ResultsEquityChart/benchmark/BenchmarkCtrl.js`.
- **Existing UI connection:** Results; exact retained source-map `ui/app/plugins/project/ResultsEquityChart/source-map.json`. Target `ui/app/plugins/project/ResultsEquityChart/EquityChartCtrl.ts`; wire persisted run/result lookup, selected sample, trades and reconciled metrics.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Create:** `app/plugins/results/ResultsEquityChart/service.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/results/ResultsEquityChart/contracts.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/results/ResultsEquityChart/routes.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/results/ResultsEquityChart/README.md`
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_results_results_equity_chart.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/results_results_equity_chart.json`
  - Store versioned paraphrased donor input/output fixtures.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/plugins/project/ResultsEquityChart/EquityChartCtrl.ts`
  - Await backend validation/commands; bind actual result and job states to existing controls.
- **Modify:** `ui/app/plugins/project/ResultsEquityChart/benchmark/BenchmarkCtrl.ts`
  - Await backend validation/commands; bind actual result and job states to existing controls.
- **Modify:** `ui/app/plugins/project/ResultsEquityChart/equityChart.tsx`
  - Display persisted run/result lookup, selected sample, trades and reconciled metrics from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/Results/ResultsWorkspace.tsx`
  - Display persisted run/result lookup, selected sample, trades and reconciled metrics from backend responses; preserve layout.
- **Create:** `ui/app/plugins/project/ResultsEquityChart/backendClient.ts`
  - Typed domain client over host transport; ratify route/schema/version, errors and cancellation. Reuse this proposed owner if delivered earlier.
- **Create:** `ui/tests/unit/backend-connections/feat-results-results-equity-chart.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-results-databanks-exports-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Project the named result series with verified metrics and sampling; verify units, timestamp alignment, missing samples and reconciled source totals.
- [ ] **Step 4:** `FR-RESULTS-RESULTS-EQUITY-CHART-EQUITY-CHART-SERVLET-CONTRACT` → `com.strategyquant.plugin.Results.impl.EquityChart.EquityChartServlet`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-RESULTS-RESULTS-EQUITY-CHART-EQUITY-CHART-SERVLET-EXECUTE` → `com.strategyquant.plugin.Results.impl.EquityChart.EquityChartServlet.execute`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** `FR-RESULTS-RESULTS-EQUITY-CHART-EQUITY-CHART-SERVLET-LOAD-LAST-SETTINGS` → `com.strategyquant.plugin.Results.impl.EquityChart.EquityChartServlet.loadLastSettings`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 7:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 8:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 9:** Connect retained UI: Ratify the feature-owned wire contract; bind persisted run/result lookup, selected sample, trades and reconciled metrics to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 10:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_results_results_equity_chart.py --no-cov`; expect units, timestamp alignment, missing samples and reconciled source totals; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture units, timestamp alignment, missing samples and reconciled source totals and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-results-results-equity-chart.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-results-databanks-exports-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise Results for FEAT-RESULTS-RESULTS-EQUITY-CHART; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.

# 8.22 FEAT-RESULTS-RESULTS-EXPLORE - ResultsExplore.jar

## 1. Objective

- **Goal:** Implement authoritative Explore result projections/actions.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Render authoritative databanks, result analysis, charts and exports.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/plugins/ResultsExplore/ResultsExplore.jar`; 2 class declarations; SHA-256 `06bea0feab6aa8553d15a038440421129a9456309d6f8b948f47c50e80507847`.
- **Inspected reference:** `HARUQUANTAI_ROOT/docs/sqx/Results/ResultsExplore.md`; roadmap allocation `FEAT-RESULTS-RESULTS-EXPLORE`.
- **Owner:** `app/plugins/results/ResultsExplore/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Shared result exploration, stockpicker reporting, trade analysis and projections; downstream .
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/plugins/ResultsExplore/ResultsExplore.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/plugins/ResultsExplore/ResultsExplore.jar" com.strategyquant.plugin.Results.impl.Explore.ExploreServlet`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_REFERENCE_ROOT/internal/plugins/ResultsExplore`; `SQX_REFERENCE_ROOT/internal/web/RESULTS`; `SQX_REFERENCE_ROOT/internal/plugins/ProjectResults`. Inspect `SQX_REFERENCE_ROOT/internal/plugins/ResultsExplore/ExploreService.js`; `SQX_REFERENCE_ROOT/internal/plugins/ResultsExplore/ExploreCtrl.js`; `SQX_REFERENCE_ROOT/internal/plugins/ResultsExplore/explore.html`.
- **Existing UI connection:** Results; proposed shared consumer; verify the exact existing control and public contract before implementation. Target `ui/app/workspace/Results/ResultsWorkspace.tsx`; wire persisted run/result lookup, selected sample, trades and reconciled metrics.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Create:** `app/plugins/results/ResultsExplore/service.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/results/ResultsExplore/contracts.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/results/ResultsExplore/routes.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/results/ResultsExplore/README.md`
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_results_results_explore.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/results_results_explore.json`
  - Store versioned paraphrased donor input/output fixtures.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/workspace/Results/ResultsWorkspace.tsx`
  - Display persisted run/result lookup, selected sample, trades and reconciled metrics from backend responses; preserve layout.
- **Modify:** `ui/app/plugins/project/ProjectResults/ResultsCtrl.ts`
  - Await backend validation/commands; bind actual result and job states to existing controls.
- **Modify:** `ui/app/plugins/databank/ProjectDatabanks/databankStore.ts`
  - Replace affected mock job/resource authority with server projections; preserve selection/view state.
- **Create:** `ui/app/workspace/Results/resultsClient.ts`
  - Typed domain client over host transport; ratify route/schema/version, errors and cancellation. Reuse this proposed owner if delivered earlier.
- **Create:** `ui/tests/unit/backend-connections/feat-results-results-explore.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-results-databanks-exports-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Implement authoritative Explore result projections/actions; verify metric provenance, result identity, empty/error state and stored-value reconciliation.
- [ ] **Step 4:** `FR-RESULTS-RESULTS-EXPLORE-EXPLORE-SERVLET-CONTRACT` → `com.strategyquant.plugin.Results.impl.Explore.ExploreServlet`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-RESULTS-RESULTS-EXPLORE-EXPLORE-SERVLET-EXECUTE` → `com.strategyquant.plugin.Results.impl.Explore.ExploreServlet.execute`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 7:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 8:** Connect retained UI: Ratify the feature-owned wire contract; bind persisted run/result lookup, selected sample, trades and reconciled metrics to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 9:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_results_results_explore.py --no-cov`; expect metric provenance, result identity, empty/error state and stored-value reconciliation; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture metric provenance, result identity, empty/error state and stored-value reconciliation and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-results-results-explore.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-results-databanks-exports-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise Results for FEAT-RESULTS-RESULTS-EXPLORE; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.

# 8.23 FEAT-RESULTS-RESULTS-OVERVIEW - ResultsOverview.jar

## 1. Objective

- **Goal:** Implement authoritative Overview result projections/actions.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Render authoritative databanks, result analysis, charts and exports.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/plugins/ResultsOverview/ResultsOverview.jar`; 2 class declarations; SHA-256 `9a97ec7cf2324e744f87a5e5039e7365cb162713ca4ff5b0cc324a6bf7dcfa23`.
- **Inspected reference:** `HARUQUANTAI_ROOT/docs/sqx/Results/ResultsOverview.md`; roadmap allocation `FEAT-RESULTS-RESULTS-OVERVIEW`.
- **Owner:** `app/plugins/results/ResultsOverview/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Shared result exploration, stockpicker reporting, trade analysis and projections; downstream .
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/plugins/ResultsOverview/ResultsOverview.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/plugins/ResultsOverview/ResultsOverview.jar" com.strategyquant.plugin.Results.impl.Overview.OverviewServlet`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_REFERENCE_ROOT/internal/plugins/ResultsOverview`; `SQX_REFERENCE_ROOT/internal/web/RESULTS`; `SQX_REFERENCE_ROOT/internal/plugins/ProjectResults`. Inspect `SQX_REFERENCE_ROOT/internal/plugins/ResultsOverview/ResultsOverviewService.js`; `SQX_REFERENCE_ROOT/internal/plugins/ResultsOverview/ResultsOverviewCtrl.js`; `SQX_REFERENCE_ROOT/internal/plugins/ResultsOverview/overview.html`.
- **Existing UI connection:** Results; exact retained source-map `ui/app/plugins/project/ResultsOverview/source-map.json`. Target `ui/app/plugins/project/ResultsOverview/ResultsOverviewCtrl.ts`; wire persisted run/result lookup, selected sample, trades and reconciled metrics.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Create:** `app/plugins/results/ResultsOverview/service.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/results/ResultsOverview/contracts.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/results/ResultsOverview/routes.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/results/ResultsOverview/README.md`
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_results_results_overview.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/results_results_overview.json`
  - Store versioned paraphrased donor input/output fixtures.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/plugins/project/ResultsOverview/ResultsOverviewCtrl.ts`
  - Await backend validation/commands; bind actual result and job states to existing controls.
- **Modify:** `ui/app/plugins/project/ResultsOverview/overview.tsx`
  - Display persisted run/result lookup, selected sample, trades and reconciled metrics from backend responses; preserve layout.
- **Modify:** `ui/app/plugins/project/ResultsOverview/module.ts`
  - Display persisted run/result lookup, selected sample, trades and reconciled metrics from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/Results/ResultsWorkspace.tsx`
  - Display persisted run/result lookup, selected sample, trades and reconciled metrics from backend responses; preserve layout.
- **Create:** `ui/app/plugins/project/ResultsOverview/backendClient.ts`
  - Typed domain client over host transport; ratify route/schema/version, errors and cancellation. Reuse this proposed owner if delivered earlier.
- **Create:** `ui/tests/unit/backend-connections/feat-results-results-overview.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-results-databanks-exports-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Implement authoritative Overview result projections/actions; verify metric provenance, result identity, empty/error state and stored-value reconciliation.
- [ ] **Step 4:** `FR-RESULTS-RESULTS-OVERVIEW-OVERVIEW-SERVLET-CONTRACT` → `com.strategyquant.plugin.Results.impl.Overview.OverviewServlet`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-RESULTS-RESULTS-OVERVIEW-OVERVIEW-SERVLET-EXECUTE` → `com.strategyquant.plugin.Results.impl.Overview.OverviewServlet.execute`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** `FR-RESULTS-RESULTS-OVERVIEW-OVERVIEW-SERVLET-GET-TEMPLATES` → `com.strategyquant.plugin.Results.impl.Overview.OverviewServlet.getTemplates`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 7:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 8:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 9:** Connect retained UI: Ratify the feature-owned wire contract; bind persisted run/result lookup, selected sample, trades and reconciled metrics to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 10:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_results_results_overview.py --no-cov`; expect metric provenance, result identity, empty/error state and stored-value reconciliation; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture metric provenance, result identity, empty/error state and stored-value reconciliation and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-results-results-overview.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-results-databanks-exports-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise Results for FEAT-RESULTS-RESULTS-OVERVIEW; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.

# 8.24 FEAT-RESULTS-RESULTS-PLUGINS - ResultsPlugins.jar

## 1. Objective

- **Goal:** Implement authoritative Plugins result projections/actions.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Render authoritative databanks, result analysis, charts and exports.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/plugins/ResultsPlugins/ResultsPlugins.jar`; 2 class declarations; SHA-256 `419272195dd39a87631f6e46df6319121235acf412935b94620f79365345830a`.
- **Inspected reference:** `HARUQUANTAI_ROOT/docs/sqx/Results/ResultsPlugins.md`; roadmap allocation `FEAT-RESULTS-RESULTS-PLUGINS`.
- **Owner:** `app/plugins/results/ResultsPlugins/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Shared result exploration, stockpicker reporting, trade analysis and projections; downstream .
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/plugins/ResultsPlugins/ResultsPlugins.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/plugins/ResultsPlugins/ResultsPlugins.jar" com.strategyquant.plugin.Results.impl.Plugins.ResultsPluginsServlet`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_REFERENCE_ROOT/internal/plugins/ResultsPlugins`; `SQX_REFERENCE_ROOT/internal/web/RESULTS`; `SQX_REFERENCE_ROOT/internal/plugins/ProjectResults`. Inspect `SQX_REFERENCE_ROOT/internal/plugins/ResultsPlugins/ResultsPluginsService.js`; `SQX_REFERENCE_ROOT/internal/plugins/ResultsPlugins/PluginIframeCtrl.js`; `SQX_REFERENCE_ROOT/internal/plugins/ResultsPlugins/pluginIframe.html`.
- **Existing UI connection:** Results; proposed shared consumer; verify the exact existing control and public contract before implementation. Target `ui/app/workspace/Results/ResultsWorkspace.tsx`; wire persisted run/result lookup, selected sample, trades and reconciled metrics.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Create:** `app/plugins/results/ResultsPlugins/service.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/results/ResultsPlugins/contracts.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/results/ResultsPlugins/routes.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/results/ResultsPlugins/README.md`
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_results_results_plugins.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/results_results_plugins.json`
  - Store versioned paraphrased donor input/output fixtures.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/workspace/Results/ResultsWorkspace.tsx`
  - Display persisted run/result lookup, selected sample, trades and reconciled metrics from backend responses; preserve layout.
- **Modify:** `ui/app/plugins/project/ProjectResults/ResultsCtrl.ts`
  - Await backend validation/commands; bind actual result and job states to existing controls.
- **Modify:** `ui/app/plugins/databank/ProjectDatabanks/databankStore.ts`
  - Replace affected mock job/resource authority with server projections; preserve selection/view state.
- **Create:** `ui/app/workspace/Results/resultsClient.ts`
  - Typed domain client over host transport; ratify route/schema/version, errors and cancellation. Reuse this proposed owner if delivered earlier.
- **Create:** `ui/tests/unit/backend-connections/feat-results-results-plugins.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-results-databanks-exports-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Implement authoritative Plugins result projections/actions; verify metric provenance, result identity, empty/error state and stored-value reconciliation.
- [ ] **Step 4:** `FR-RESULTS-RESULTS-PLUGINS-RESULTS-PLUGINS-SERVLET-CONTRACT` → `com.strategyquant.plugin.Results.impl.Plugins.ResultsPluginsServlet`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-RESULTS-RESULTS-PLUGINS-RESULTS-PLUGINS-SERVLET-EXECUTE` → `com.strategyquant.plugin.Results.impl.Plugins.ResultsPluginsServlet.execute`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 7:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 8:** Connect retained UI: Ratify the feature-owned wire contract; bind persisted run/result lookup, selected sample, trades and reconciled metrics to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 9:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_results_results_plugins.py --no-cov`; expect metric provenance, result identity, empty/error state and stored-value reconciliation; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture metric provenance, result identity, empty/error state and stored-value reconciliation and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-results-results-plugins.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-results-databanks-exports-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise Results for FEAT-RESULTS-RESULTS-PLUGINS; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.

# 8.25 FEAT-RESULTS-RESULTS-SP-OVERVIEW - ResultsSPOverview.jar

## 1. Objective

- **Goal:** Implement authoritative SPOverview result projections/actions.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Render authoritative databanks, result analysis, charts and exports.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/plugins/ResultsSPOverview/ResultsSPOverview.jar`; 5 class declarations; SHA-256 `68c7cadc03dcd867ff506c74654b427e4de3d38f027ddcb458500ef60b99d34b`.
- **Inspected reference:** `HARUQUANTAI_ROOT/docs/sqx/Results/ResultsSPOverview.md`; roadmap allocation `FEAT-RESULTS-RESULTS-SP-OVERVIEW`.
- **Owner:** `app/plugins/results/ResultsSPOverview/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Shared result exploration, stockpicker reporting, trade analysis and projections; downstream .
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/plugins/ResultsSPOverview/ResultsSPOverview.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/plugins/ResultsSPOverview/ResultsSPOverview.jar" com.strategyquant.plugin.Results.impl.SPOverview.SPOverviewServlet`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_REFERENCE_ROOT/internal/plugins/ResultsSPOverview`; `SQX_REFERENCE_ROOT/internal/web/RESULTS`; `SQX_REFERENCE_ROOT/internal/plugins/ProjectResults`. Inspect `SQX_REFERENCE_ROOT/internal/plugins/ResultsSPOverview/SPOverviewService.js`; `SQX_REFERENCE_ROOT/internal/plugins/ResultsSPOverview/SPOverviewCtrl.js`; `SQX_REFERENCE_ROOT/internal/plugins/ResultsSPOverview/directives/spOverviewList/SPOverviewListCtrl.js`.
- **Existing UI connection:** Results; exact retained source-map `ui/app/plugins/project/ResultsSPOverview/source-map.json`. Target `ui/app/plugins/project/ResultsSPOverview/SPOverviewCtrl.ts`; wire persisted run/result lookup, selected sample, trades and reconciled metrics.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Create:** `app/plugins/results/ResultsSPOverview/service.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/results/ResultsSPOverview/contracts.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/results/ResultsSPOverview/routes.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/results/ResultsSPOverview/README.md`
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_results_results_sp_overview.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/results_results_sp_overview.json`
  - Store versioned paraphrased donor input/output fixtures.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/plugins/project/ResultsSPOverview/SPOverviewCtrl.ts`
  - Await backend validation/commands; bind actual result and job states to existing controls.
- **Modify:** `ui/app/plugins/project/ResultsSPOverview/spOverview.tsx`
  - Display persisted run/result lookup, selected sample, trades and reconciled metrics from backend responses; preserve layout.
- **Modify:** `ui/app/plugins/project/ResultsSPOverview/directives/spOverviewStats/spOverviewStats.tsx`
  - Display persisted run/result lookup, selected sample, trades and reconciled metrics from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/Results/ResultsWorkspace.tsx`
  - Display persisted run/result lookup, selected sample, trades and reconciled metrics from backend responses; preserve layout.
- **Create:** `ui/app/plugins/project/ResultsSPOverview/backendClient.ts`
  - Typed domain client over host transport; ratify route/schema/version, errors and cancellation. Reuse this proposed owner if delivered earlier.
- **Create:** `ui/tests/unit/backend-connections/feat-results-results-sp-overview.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-results-databanks-exports-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Implement authoritative SPOverview result projections/actions; verify metric provenance, result identity, empty/error state and stored-value reconciliation.
- [ ] **Step 4:** `FR-RESULTS-RESULTS-SP-OVERVIEW-SP-OVERVIEW-SERVLET-CONTRACT` → `com.strategyquant.plugin.Results.impl.SPOverview.SPOverviewServlet`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-RESULTS-RESULTS-SP-OVERVIEW-SP-OVERVIEW-SERVLET-EXECUTE` → `com.strategyquant.plugin.Results.impl.SPOverview.SPOverviewServlet.execute`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 7:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 8:** Connect retained UI: Ratify the feature-owned wire contract; bind persisted run/result lookup, selected sample, trades and reconciled metrics to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 9:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_results_results_sp_overview.py --no-cov`; expect metric provenance, result identity, empty/error state and stored-value reconciliation; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture metric provenance, result identity, empty/error state and stored-value reconciliation and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-results-results-sp-overview.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-results-databanks-exports-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise Results for FEAT-RESULTS-RESULTS-SP-OVERVIEW; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.

# 8.26 FEAT-RESULTS-RESULTS-STOCKPICKER - ResultsStockpicker.jar

## 1. Objective

- **Goal:** Implement authoritative Stockpicker result projections/actions.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Render authoritative databanks, result analysis, charts and exports.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/plugins/ResultsStockpicker/ResultsStockpicker.jar`; 2 class declarations; SHA-256 `5b616da0ab1bb4e0ef5d2fd77c59ac5a40e0e409460f35e25527d258e4a9f8a8`.
- **Inspected reference:** `HARUQUANTAI_ROOT/docs/sqx/Results/ResultsStockpicker.md`; roadmap allocation `FEAT-RESULTS-RESULTS-STOCKPICKER`.
- **Owner:** `app/plugins/results/ResultsStockpicker/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Shared result exploration, stockpicker reporting, trade analysis and projections; downstream .
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/plugins/ResultsStockpicker/ResultsStockpicker.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/plugins/ResultsStockpicker/ResultsStockpicker.jar" com.strategyquant.plugin.Results.impl.Stockpicker.StockpickerServlet`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_REFERENCE_ROOT/internal/plugins/ResultsStockpicker`; `SQX_REFERENCE_ROOT/internal/web/RESULTS`; `SQX_REFERENCE_ROOT/internal/plugins/ProjectResults`. Inspect `SQX_REFERENCE_ROOT/internal/plugins/ResultsStockpicker/StockpickerService.js`; `SQX_REFERENCE_ROOT/internal/plugins/ResultsStockpicker/StockpickerCtrl.js`; `SQX_REFERENCE_ROOT/internal/plugins/ResultsStockpicker/stockpicker.html`.
- **Existing UI connection:** Results; exact retained source-map `ui/app/plugins/project/ResultsStockpicker/source-map.json`. Target `ui/app/plugins/project/ResultsStockpicker/stockpicker.tsx`; wire persisted run/result lookup, selected sample, trades and reconciled metrics.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Create:** `app/plugins/results/ResultsStockpicker/service.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/results/ResultsStockpicker/contracts.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/results/ResultsStockpicker/routes.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/results/ResultsStockpicker/README.md`
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_results_results_stockpicker.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/results_results_stockpicker.json`
  - Store versioned paraphrased donor input/output fixtures.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/plugins/project/ResultsStockpicker/stockpicker.tsx`
  - Display persisted run/result lookup, selected sample, trades and reconciled metrics from backend responses; preserve layout.
- **Modify:** `ui/app/plugins/project/ResultsStockpicker/module.ts`
  - Display persisted run/result lookup, selected sample, trades and reconciled metrics from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/Results/ResultsWorkspace.tsx`
  - Display persisted run/result lookup, selected sample, trades and reconciled metrics from backend responses; preserve layout.
- **Create:** `ui/app/plugins/project/ResultsStockpicker/backendClient.ts`
  - Typed domain client over host transport; ratify route/schema/version, errors and cancellation. Reuse this proposed owner if delivered earlier.
- **Create:** `ui/tests/unit/backend-connections/feat-results-results-stockpicker.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-results-databanks-exports-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Implement authoritative Stockpicker result projections/actions; verify metric provenance, result identity, empty/error state and stored-value reconciliation.
- [ ] **Step 4:** `FR-RESULTS-RESULTS-STOCKPICKER-STOCKPICKER-SERVLET-CONTRACT` → `com.strategyquant.plugin.Results.impl.Stockpicker.StockpickerServlet`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-RESULTS-RESULTS-STOCKPICKER-STOCKPICKER-SERVLET-EXECUTE` → `com.strategyquant.plugin.Results.impl.Stockpicker.StockpickerServlet.execute`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 7:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 8:** Connect retained UI: Ratify the feature-owned wire contract; bind persisted run/result lookup, selected sample, trades and reconciled metrics to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 9:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_results_results_stockpicker.py --no-cov`; expect metric provenance, result identity, empty/error state and stored-value reconciliation; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture metric provenance, result identity, empty/error state and stored-value reconciliation and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-results-results-stockpicker.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-results-databanks-exports-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise Results for FEAT-RESULTS-RESULTS-STOCKPICKER; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.

# 8.27 FEAT-RESULTS-RESULTS-STRATEGY-CONFIG - ResultsStrategyConfig.jar

## 1. Objective

- **Goal:** Implement authoritative StrategyConfig result projections/actions.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Render authoritative databanks, result analysis, charts and exports.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/plugins/ResultsStrategyConfig/ResultsStrategyConfig.jar`; 2 class declarations; SHA-256 `6409614e40da9c8afeee39bbde288ca87194eba4c77fbf1c7104d6c0f7dfba2d`.
- **Inspected reference:** `HARUQUANTAI_ROOT/docs/sqx/Results/ResultsStrategyConfig.md`; roadmap allocation `FEAT-RESULTS-RESULTS-STRATEGY-CONFIG`.
- **Owner:** `app/plugins/results/ResultsStrategyConfig/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Shared result exploration, stockpicker reporting, trade analysis and projections; downstream .
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/plugins/ResultsStrategyConfig/ResultsStrategyConfig.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/plugins/ResultsStrategyConfig/ResultsStrategyConfig.jar" com.strategyquant.plugin.Results.impl.StrategyConfig.StrategyConfigServlet`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_REFERENCE_ROOT/internal/plugins/ResultsStrategyConfig`; `SQX_REFERENCE_ROOT/internal/web/RESULTS`; `SQX_REFERENCE_ROOT/internal/plugins/ProjectResults`. Inspect `SQX_REFERENCE_ROOT/internal/plugins/ResultsStrategyConfig/StrategyConfigService.js`; `SQX_REFERENCE_ROOT/internal/plugins/ResultsStrategyConfig/StrategyConfigCtrl.js`; `SQX_REFERENCE_ROOT/internal/plugins/ResultsStrategyConfig/strategyconfig.html`.
- **Existing UI connection:** Results; exact retained source-map `ui/app/plugins/project/ResultsStrategyConfig/source-map.json`. Target `ui/app/plugins/project/ResultsStrategyConfig/strategyconfig.tsx`; wire persisted run/result lookup, selected sample, trades and reconciled metrics.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Create:** `app/plugins/results/ResultsStrategyConfig/service.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/results/ResultsStrategyConfig/contracts.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/results/ResultsStrategyConfig/routes.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/results/ResultsStrategyConfig/README.md`
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_results_results_strategy_config.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/results_results_strategy_config.json`
  - Store versioned paraphrased donor input/output fixtures.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/plugins/project/ResultsStrategyConfig/strategyconfig.tsx`
  - Display persisted run/result lookup, selected sample, trades and reconciled metrics from backend responses; preserve layout.
- **Modify:** `ui/app/plugins/project/ResultsStrategyConfig/module.ts`
  - Display persisted run/result lookup, selected sample, trades and reconciled metrics from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/Results/ResultsWorkspace.tsx`
  - Display persisted run/result lookup, selected sample, trades and reconciled metrics from backend responses; preserve layout.
- **Create:** `ui/app/plugins/project/ResultsStrategyConfig/backendClient.ts`
  - Typed domain client over host transport; ratify route/schema/version, errors and cancellation. Reuse this proposed owner if delivered earlier.
- **Create:** `ui/tests/unit/backend-connections/feat-results-results-strategy-config.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-results-databanks-exports-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Implement authoritative StrategyConfig result projections/actions; verify metric provenance, result identity, empty/error state and stored-value reconciliation.
- [ ] **Step 4:** `FR-RESULTS-RESULTS-STRATEGY-CONFIG-STRATEGY-CONFIG-SERVLET-CONTRACT` → `com.strategyquant.plugin.Results.impl.StrategyConfig.StrategyConfigServlet`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-RESULTS-RESULTS-STRATEGY-CONFIG-STRATEGY-CONFIG-SERVLET-EXECUTE` → `com.strategyquant.plugin.Results.impl.StrategyConfig.StrategyConfigServlet.execute`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 7:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 8:** Connect retained UI: Ratify the feature-owned wire contract; bind persisted run/result lookup, selected sample, trades and reconciled metrics to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 9:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_results_results_strategy_config.py --no-cov`; expect metric provenance, result identity, empty/error state and stored-value reconciliation; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture metric provenance, result identity, empty/error state and stored-value reconciliation and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-results-results-strategy-config.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-results-databanks-exports-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise Results for FEAT-RESULTS-RESULTS-STRATEGY-CONFIG; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.

# 8.28 FEAT-RESULTS-RESULTS-TRADE-ANALYSIS - ResultsTradeAnalysis.jar

## 1. Objective

- **Goal:** Project authoritative trade records, analysis and view configuration.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Render authoritative databanks, result analysis, charts and exports.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/plugins/ResultsTradeAnalysis/ResultsTradeAnalysis.jar`; 3 class declarations; SHA-256 `7c7ba403d569744e36cd88fa4e8e62640249db056c36171fe781e58e30a17816`.
- **Inspected reference:** `HARUQUANTAI_ROOT/docs/sqx/Results/ResultsTradeAnalysis.md`; roadmap allocation `FEAT-RESULTS-RESULTS-TRADE-ANALYSIS`.
- **Owner:** `app/plugins/results/ResultsTradeAnalysis/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Shared result exploration, stockpicker reporting, trade analysis and projections; downstream .
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/plugins/ResultsTradeAnalysis/ResultsTradeAnalysis.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/plugins/ResultsTradeAnalysis/ResultsTradeAnalysis.jar" com.strategyquant.plugin.Results.impl.TradeAnalysis.TradeAnalysisServlet`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_REFERENCE_ROOT/internal/plugins/ResultsTradeAnalysis`; `SQX_REFERENCE_ROOT/internal/web/RESULTS`; `SQX_REFERENCE_ROOT/internal/plugins/ProjectResults`. Inspect `SQX_REFERENCE_ROOT/internal/plugins/ResultsTradeAnalysis/services/TradeAnalysisService.js`; `SQX_REFERENCE_ROOT/internal/plugins/ResultsTradeAnalysis/controllers/TradeAnalysisCtrl.js`; `SQX_REFERENCE_ROOT/internal/plugins/ResultsTradeAnalysis/directives/TradeAnalysisPanelCtrl.js`.
- **Existing UI connection:** Results; exact retained source-map `ui/app/plugins/project/ResultsTradeAnalysis/source-map.json`. Target `ui/app/plugins/project/ResultsTradeAnalysis/controllers/TradeAnalysisCtrl.ts`; wire persisted run/result lookup, selected sample, trades and reconciled metrics.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Create:** `app/plugins/results/ResultsTradeAnalysis/service.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/results/ResultsTradeAnalysis/contracts.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/results/ResultsTradeAnalysis/routes.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/results/ResultsTradeAnalysis/README.md`
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_results_results_trade_analysis.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/results_results_trade_analysis.json`
  - Store versioned paraphrased donor input/output fixtures.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/plugins/project/ResultsTradeAnalysis/controllers/TradeAnalysisCtrl.ts`
  - Await backend validation/commands; bind actual result and job states to existing controls.
- **Modify:** `ui/app/plugins/project/ResultsTradeAnalysis/directives/tradeAnalysisPanel.tsx`
  - Display persisted run/result lookup, selected sample, trades and reconciled metrics from backend responses; preserve layout.
- **Modify:** `ui/app/plugins/project/ResultsTradeAnalysis/views/tradeAnalysis.tsx`
  - Display persisted run/result lookup, selected sample, trades and reconciled metrics from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/Results/ResultsWorkspace.tsx`
  - Display persisted run/result lookup, selected sample, trades and reconciled metrics from backend responses; preserve layout.
- **Create:** `ui/app/plugins/project/ResultsTradeAnalysis/backendClient.ts`
  - Typed domain client over host transport; ratify route/schema/version, errors and cancellation. Reuse this proposed owner if delivered earlier.
- **Create:** `ui/tests/unit/backend-connections/feat-results-results-trade-analysis.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-results-databanks-exports-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Project authoritative trade records, analysis and view configuration; verify trade identity, filters, aggregation boundaries and empty results.
- [ ] **Step 4:** `FR-RESULTS-RESULTS-TRADE-ANALYSIS-TRADE-ANALYSIS-SERVLET-CONTRACT` → `com.strategyquant.plugin.Results.impl.TradeAnalysis.TradeAnalysisServlet`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-RESULTS-RESULTS-TRADE-ANALYSIS-TRADE-ANALYSIS-SERVLET-EXECUTE` → `com.strategyquant.plugin.Results.impl.TradeAnalysis.TradeAnalysisServlet.execute`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** `FR-RESULTS-RESULTS-TRADE-ANALYSIS-TRADE-ANALYSIS-SERVLET-LOAD-LAST-SETTINGS` → `com.strategyquant.plugin.Results.impl.TradeAnalysis.TradeAnalysisServlet.loadLastSettings`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 7:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 8:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 9:** Connect retained UI: Ratify the feature-owned wire contract; bind persisted run/result lookup, selected sample, trades and reconciled metrics to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 10:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_results_results_trade_analysis.py --no-cov`; expect trade identity, filters, aggregation boundaries and empty results; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture trade identity, filters, aggregation boundaries and empty results and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-results-results-trade-analysis.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-results-databanks-exports-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise Results for FEAT-RESULTS-RESULTS-TRADE-ANALYSIS; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.

# 8.29 FEAT-RESULTS-RESULTS-TRADE-LIST - ResultsTradeList.jar

## 1. Objective

- **Goal:** Project authoritative trade records, analysis and view configuration.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Render authoritative databanks, result analysis, charts and exports.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/plugins/ResultsTradeList/ResultsTradeList.jar`; 2 class declarations; SHA-256 `0f44d384771374d1f42497dde2b6f5663024767e931f0ef58da1c208a95ec317`.
- **Inspected reference:** `HARUQUANTAI_ROOT/docs/sqx/Results/ResultsTradeList.md`; roadmap allocation `FEAT-RESULTS-RESULTS-TRADE-LIST`.
- **Owner:** `app/plugins/results/ResultsTradeList/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Shared result exploration, stockpicker reporting, trade analysis and projections; downstream .
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/plugins/ResultsTradeList/ResultsTradeList.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/plugins/ResultsTradeList/ResultsTradeList.jar" com.strategyquant.plugin.Results.impl.TradeList.TradeListServlet`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_REFERENCE_ROOT/internal/plugins/ResultsTradeList`; `SQX_REFERENCE_ROOT/internal/web/RESULTS`; `SQX_REFERENCE_ROOT/internal/plugins/ProjectResults`. Inspect `SQX_REFERENCE_ROOT/internal/plugins/ResultsTradeList/ResultsTradelistCtrl.js`; `SQX_REFERENCE_ROOT/internal/plugins/ResultsTradeList/tradeList.html`; `SQX_REFERENCE_ROOT/internal/plugins/ResultsTradeList/module.js`.
- **Existing UI connection:** Results; exact retained source-map `ui/app/plugins/project/ResultsTradeList/source-map.json`. Target `ui/app/plugins/project/ResultsTradeList/ResultsTradelistCtrl.ts`; wire persisted run/result lookup, selected sample, trades and reconciled metrics.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Create:** `app/plugins/results/ResultsTradeList/service.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/results/ResultsTradeList/contracts.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/results/ResultsTradeList/routes.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/results/ResultsTradeList/README.md`
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_results_results_trade_list.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/results_results_trade_list.json`
  - Store versioned paraphrased donor input/output fixtures.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/plugins/project/ResultsTradeList/ResultsTradelistCtrl.ts`
  - Await backend validation/commands; bind actual result and job states to existing controls.
- **Modify:** `ui/app/plugins/project/ResultsTradeList/tradeList.tsx`
  - Display persisted run/result lookup, selected sample, trades and reconciled metrics from backend responses; preserve layout.
- **Modify:** `ui/app/plugins/project/ResultsTradeList/module.ts`
  - Display persisted run/result lookup, selected sample, trades and reconciled metrics from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/Results/ResultsWorkspace.tsx`
  - Display persisted run/result lookup, selected sample, trades and reconciled metrics from backend responses; preserve layout.
- **Create:** `ui/app/plugins/project/ResultsTradeList/backendClient.ts`
  - Typed domain client over host transport; ratify route/schema/version, errors and cancellation. Reuse this proposed owner if delivered earlier.
- **Create:** `ui/tests/unit/backend-connections/feat-results-results-trade-list.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-results-databanks-exports-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Project authoritative trade records, analysis and view configuration; verify trade identity, filters, aggregation boundaries and empty results.
- [ ] **Step 4:** `FR-RESULTS-RESULTS-TRADE-LIST-TRADE-LIST-SERVLET-CONTRACT` → `com.strategyquant.plugin.Results.impl.TradeList.TradeListServlet`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-RESULTS-RESULTS-TRADE-LIST-TRADE-LIST-SERVLET-EXECUTE` → `com.strategyquant.plugin.Results.impl.TradeList.TradeListServlet.execute`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 7:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 8:** Connect retained UI: Ratify the feature-owned wire contract; bind persisted run/result lookup, selected sample, trades and reconciled metrics to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 9:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_results_results_trade_list.py --no-cov`; expect trade identity, filters, aggregation boundaries and empty results; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture trade identity, filters, aggregation boundaries and empty results and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-results-results-trade-list.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-results-databanks-exports-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise Results for FEAT-RESULTS-RESULTS-TRADE-LIST; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.

# 8.30 FEAT-RESULTS-RESULTS-TRADELIST-VIEWS - ResultsTradelistViews.jar

## 1. Objective

- **Goal:** Project authoritative trade records, analysis and view configuration.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Render authoritative databanks, result analysis, charts and exports.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/plugins/ResultsTradelistViews/ResultsTradelistViews.jar`; 2 class declarations; SHA-256 `f0b240c1d0907dc879d423d426dff448569f01d2e7b6c67427f4b21fc4feddd7`.
- **Inspected reference:** `HARUQUANTAI_ROOT/docs/sqx/Results/ResultsTradelistViews.md`; roadmap allocation `FEAT-RESULTS-RESULTS-TRADELIST-VIEWS`.
- **Owner:** `app/plugins/databank/ResultsTradelistViews/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Databank views/actions/rename and correlation projections; downstream P09–P13.
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/plugins/ResultsTradelistViews/ResultsTradelistViews.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/plugins/ResultsTradelistViews/ResultsTradelistViews.jar" com.strategyquant.plugin.Results.impl.TradelistViews.TradelistViewsServlet`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_REFERENCE_ROOT/internal/plugins/ResultsTradelistViews`; `SQX_REFERENCE_ROOT/internal/web/RESULTS`; `SQX_REFERENCE_ROOT/internal/plugins/ProjectResults`. Inspect `SQX_REFERENCE_ROOT/internal/plugins/ResultsTradelistViews/TradelistViewsService.js`; `SQX_REFERENCE_ROOT/internal/plugins/ResultsTradelistViews/TradelistViewsCtrl.js`; `SQX_REFERENCE_ROOT/internal/plugins/ResultsTradelistViews/tradelistViews.html`.
- **Existing UI connection:** Results; exact retained source-map `ui/app/plugins/project/ResultsTradelistViews/source-map.json`. Target `ui/app/plugins/project/ResultsTradelistViews/TradelistViewsCtrl.ts`; wire persisted run/result lookup, selected sample, trades and reconciled metrics.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Create:** `app/plugins/databank/ResultsTradelistViews/service.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/databank/ResultsTradelistViews/routes.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/databank/ResultsTradelistViews/contracts.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/databank/ResultsTradelistViews/README.md`
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_results_results_tradelist_views.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/results_results_tradelist_views.json`
  - Store versioned paraphrased donor input/output fixtures.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/plugins/project/ResultsTradelistViews/TradelistViewsCtrl.ts`
  - Await backend validation/commands; bind actual result and job states to existing controls.
- **Modify:** `ui/app/plugins/project/ResultsTradelistViews/tradelistViews.tsx`
  - Display persisted run/result lookup, selected sample, trades and reconciled metrics from backend responses; preserve layout.
- **Modify:** `ui/app/plugins/project/ResultsTradelistViews/module.ts`
  - Display persisted run/result lookup, selected sample, trades and reconciled metrics from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/Results/ResultsWorkspace.tsx`
  - Display persisted run/result lookup, selected sample, trades and reconciled metrics from backend responses; preserve layout.
- **Create:** `ui/app/plugins/project/ResultsTradelistViews/backendClient.ts`
  - Typed domain client over host transport; ratify route/schema/version, errors and cancellation. Reuse this proposed owner if delivered earlier.
- **Create:** `ui/tests/unit/backend-connections/feat-results-results-tradelist-views.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-results-databanks-exports-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Project authoritative trade records, analysis and view configuration; verify trade identity, filters, aggregation boundaries and empty results.
- [ ] **Step 4:** `FR-RESULTS-RESULTS-TRADELIST-VIEWS-TRADELIST-VIEWS-SERVLET-CONTRACT` → `com.strategyquant.plugin.Results.impl.TradelistViews.TradelistViewsServlet`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-RESULTS-RESULTS-TRADELIST-VIEWS-TRADELIST-VIEWS-SERVLET-EXECUTE` → `com.strategyquant.plugin.Results.impl.TradelistViews.TradelistViewsServlet.execute`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 7:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 8:** Connect retained UI: Ratify the feature-owned wire contract; bind persisted run/result lookup, selected sample, trades and reconciled metrics to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 9:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_results_results_tradelist_views.py --no-cov`; expect trade identity, filters, aggregation boundaries and empty results; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture trade identity, filters, aggregation boundaries and empty results and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-results-results-tradelist-views.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-results-databanks-exports-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise Results for FEAT-RESULTS-RESULTS-TRADELIST-VIEWS; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.

# 8.31 FEAT-RESULTS-SAVER-HTML - SaverHTML.jar

## 1. Objective

- **Goal:** Export the named result artifact with source-bound provenance.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Render authoritative databanks, result analysis, charts and exports.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/plugins/SaverHTML/SaverHTML.jar`; 1 class declarations; SHA-256 `87f11f13c3a7691d2ae656ec844926160419c5af6763fe8a9f18912d70310ce9`.
- **Inspected reference:** `HARUQUANTAI_ROOT/docs/sqx/Shared/SaverHTML.md`; roadmap allocation `FEAT-RESULTS-SAVER-HTML`.
- **Owner:** `app/plugins/export/SaverHTML/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** HTML/PDF/trade export adapters; downstream .
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/plugins/SaverHTML/SaverHTML.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/plugins/SaverHTML/SaverHTML.jar" com.strategyquant.plugin.Saver.impl.HTML.HTMLReportPlugin`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_REFERENCE_ROOT/internal/plugins/SaverHTML`; `SQX_REFERENCE_ROOT/internal/plugins/ResultsDatabankActions`. Inspect `SQX_REFERENCE_ROOT/internal/plugins/ResultsDatabankActions/DatabankActionsService.js`.
- **Existing UI connection:** databank save/export; proposed shared consumer; verify the exact existing control and public contract before implementation. Target `ui/app/plugins/databank/ResultsDatabankActions/save/SaveButtonService.ts`; wire selected format/strategy export, real generated artifact IDs and verified downloads.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Create:** `app/plugins/export/SaverHTML/exporter.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/export/SaverHTML/contracts.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/export/SaverHTML/README.md`
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_results_saver_html.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/results_saver_html.json`
  - Store versioned paraphrased donor input/output fixtures.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/plugins/databank/ResultsDatabankActions/save/SaveButtonService.ts`
  - Call owned typed commands; map responses/errors to current dialogs.
- **Modify:** `ui/app/plugins/databank/ResultsDatabankActions/save/saveBtnPopupCtrl.ts`
  - Await backend validation/commands; bind actual result and job states to existing controls.
- **Modify:** `ui/app/plugins/databank/ResultsDatabankActions/save/savePopup.tsx`
  - Display selected format/strategy export, real generated artifact IDs and verified downloads from backend responses; preserve layout.
- **Create:** `ui/tests/unit/backend-connections/feat-results-saver-html.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-results-databanks-exports-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Export the named result artifact with source-bound provenance; verify escaping/format, missing output destination and totals reconciliation.
- [ ] **Step 4:** `FR-RESULTS-SAVER-HTML-HTML-REPORT-PLUGIN-CONTRACT` → `com.strategyquant.plugin.Saver.impl.HTML.HTMLReportPlugin`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-RESULTS-SAVER-HTML-HTML-REPORT-PLUGIN-GET-PREFERRED-POSITION` → `com.strategyquant.plugin.Saver.impl.HTML.HTMLReportPlugin.getPreferredPosition`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** `FR-RESULTS-SAVER-HTML-HTML-REPORT-PLUGIN-INIT-PLUGIN` → `com.strategyquant.plugin.Saver.impl.HTML.HTMLReportPlugin.initPlugin`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 7:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 8:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 9:** Connect retained UI: Ratify the feature-owned wire contract; bind selected format/strategy export, real generated artifact IDs and verified downloads to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 10:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_results_saver_html.py --no-cov`; expect escaping/format, missing output destination and totals reconciliation; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture escaping/format, missing output destination and totals reconciliation and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-results-saver-html.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-results-databanks-exports-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise databank save/export for FEAT-RESULTS-SAVER-HTML; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.

# 8.32 FEAT-RESULTS-SAVER-PDF - SaverPDF.jar

## 1. Objective

- **Goal:** Export the named result artifact with source-bound provenance.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Render authoritative databanks, result analysis, charts and exports.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/plugins/SaverPDF/SaverPDF.jar`; 1 class declarations; SHA-256 `cce4a187ee04a39eae19850545da96c001e0ca8f39b62e2c525121d90e41add0`.
- **Inspected reference:** `HARUQUANTAI_ROOT/docs/sqx/Shared/SaverPDF.md`; roadmap allocation `FEAT-RESULTS-SAVER-PDF`.
- **Owner:** `app/plugins/export/SaverPDF/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** HTML/PDF/trade export adapters; downstream .
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/plugins/SaverPDF/SaverPDF.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/plugins/SaverPDF/SaverPDF.jar" com.strategyquant.plugin.Saver.impl.PDF.PDFReportPlugin`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_REFERENCE_ROOT/internal/plugins/SaverPDF`; `SQX_REFERENCE_ROOT/internal/plugins/ResultsDatabankActions`. Inspect `SQX_REFERENCE_ROOT/internal/plugins/ResultsDatabankActions/DatabankActionsService.js`.
- **Existing UI connection:** databank save/export; proposed shared consumer; verify the exact existing control and public contract before implementation. Target `ui/app/plugins/databank/ResultsDatabankActions/save/SaveButtonService.ts`; wire selected format/strategy export, real generated artifact IDs and verified downloads.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Create:** `app/plugins/export/SaverPDF/exporter.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/export/SaverPDF/contracts.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/export/SaverPDF/README.md`
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_results_saver_pdf.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/results_saver_pdf.json`
  - Store versioned paraphrased donor input/output fixtures.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/plugins/databank/ResultsDatabankActions/save/SaveButtonService.ts`
  - Call owned typed commands; map responses/errors to current dialogs.
- **Modify:** `ui/app/plugins/databank/ResultsDatabankActions/save/saveBtnPopupCtrl.ts`
  - Await backend validation/commands; bind actual result and job states to existing controls.
- **Modify:** `ui/app/plugins/databank/ResultsDatabankActions/save/savePopup.tsx`
  - Display selected format/strategy export, real generated artifact IDs and verified downloads from backend responses; preserve layout.
- **Create:** `ui/tests/unit/backend-connections/feat-results-saver-pdf.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-results-databanks-exports-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Export the named result artifact with source-bound provenance; verify escaping/format, missing output destination and totals reconciliation.
- [ ] **Step 4:** `FR-RESULTS-SAVER-PDF-PDF-REPORT-PLUGIN-CONTRACT` → `com.strategyquant.plugin.Saver.impl.PDF.PDFReportPlugin`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-RESULTS-SAVER-PDF-PDF-REPORT-PLUGIN-GET-PREFERRED-POSITION` → `com.strategyquant.plugin.Saver.impl.PDF.PDFReportPlugin.getPreferredPosition`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** `FR-RESULTS-SAVER-PDF-PDF-REPORT-PLUGIN-INIT-PLUGIN` → `com.strategyquant.plugin.Saver.impl.PDF.PDFReportPlugin.initPlugin`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 7:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 8:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 9:** Connect retained UI: Ratify the feature-owned wire contract; bind selected format/strategy export, real generated artifact IDs and verified downloads to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 10:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_results_saver_pdf.py --no-cov`; expect escaping/format, missing output destination and totals reconciliation; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture escaping/format, missing output destination and totals reconciliation and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-results-saver-pdf.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-results-databanks-exports-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise databank save/export for FEAT-RESULTS-SAVER-PDF; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.

# 8.33 FEAT-RESULTS-SAVER-STRATEGY-TRADES - SaverStrategyTrades.jar

## 1. Objective

- **Goal:** Export the named result artifact with source-bound provenance.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Render authoritative databanks, result analysis, charts and exports.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/plugins/SaverStrategyTrades/SaverStrategyTrades.jar`; 1 class declarations; SHA-256 `cac2b8ccfbbda049ccfbbdfa016488fde36dc5ea4ca93ddaba07eb39b75f2e35`.
- **Inspected reference:** `HARUQUANTAI_ROOT/docs/sqx/Shared/SaverStrategyTrades.md`; roadmap allocation `FEAT-RESULTS-SAVER-STRATEGY-TRADES`.
- **Owner:** `app/plugins/export/SaverStrategyTrades/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** HTML/PDF/trade export adapters; downstream .
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/plugins/SaverStrategyTrades/SaverStrategyTrades.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/plugins/SaverStrategyTrades/SaverStrategyTrades.jar" com.strategyquant.plugin.Saver.impl.StrategyTrades.StrategyTradesSaverPlugin`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_REFERENCE_ROOT/internal/plugins/SaverStrategyTrades`; `SQX_REFERENCE_ROOT/internal/plugins/ResultsDatabankActions`. Inspect `SQX_REFERENCE_ROOT/internal/plugins/ResultsDatabankActions/DatabankActionsService.js`.
- **Existing UI connection:** databank save/export; proposed shared consumer; verify the exact existing control and public contract before implementation. Target `ui/app/plugins/databank/ResultsDatabankActions/save/SaveButtonService.ts`; wire selected format/strategy export, real generated artifact IDs and verified downloads.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Create:** `app/plugins/export/SaverStrategyTrades/exporter.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/export/SaverStrategyTrades/contracts.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/export/SaverStrategyTrades/README.md`
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_results_saver_strategy_trades.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/results_saver_strategy_trades.json`
  - Store versioned paraphrased donor input/output fixtures.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/plugins/databank/ResultsDatabankActions/save/SaveButtonService.ts`
  - Call owned typed commands; map responses/errors to current dialogs.
- **Modify:** `ui/app/plugins/databank/ResultsDatabankActions/save/saveBtnPopupCtrl.ts`
  - Await backend validation/commands; bind actual result and job states to existing controls.
- **Modify:** `ui/app/plugins/databank/ResultsDatabankActions/save/savePopup.tsx`
  - Display selected format/strategy export, real generated artifact IDs and verified downloads from backend responses; preserve layout.
- **Create:** `ui/tests/unit/backend-connections/feat-results-saver-strategy-trades.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-results-databanks-exports-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Export the named result artifact with source-bound provenance; verify escaping/format, missing output destination and totals reconciliation.
- [ ] **Step 4:** `FR-RESULTS-SAVER-STRATEGY-TRADES-STRATEGY-TRADES-SAVER-PLUGIN-CONTRACT` → `com.strategyquant.plugin.Saver.impl.StrategyTrades.StrategyTradesSaverPlugin`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-RESULTS-SAVER-STRATEGY-TRADES-STRATEGY-TRADES-SAVER-PLUGIN-GET-PREFERRED-POSITION` → `com.strategyquant.plugin.Saver.impl.StrategyTrades.StrategyTradesSaverPlugin.getPreferredPosition`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** `FR-RESULTS-SAVER-STRATEGY-TRADES-STRATEGY-TRADES-SAVER-PLUGIN-INIT-PLUGIN` → `com.strategyquant.plugin.Saver.impl.StrategyTrades.StrategyTradesSaverPlugin.initPlugin`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 7:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 8:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 9:** Connect retained UI: Ratify the feature-owned wire contract; bind selected format/strategy export, real generated artifact IDs and verified downloads to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 10:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_results_saver_strategy_trades.py --no-cov`; expect escaping/format, missing output destination and totals reconciliation; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture escaping/format, missing output destination and totals reconciliation and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-results-saver-strategy-trades.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-results-databanks-exports-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise databank save/export for FEAT-RESULTS-SAVER-STRATEGY-TRADES; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.

# 8.34 FEAT-RESULTS-SERVLET-DATABANK-VIEWS - ServletDatabankViews.jar

## 1. Objective

- **Goal:** Expose DatabankViews commands through the owning domain routes.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Render authoritative databanks, result analysis, charts and exports.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/plugins/ServletDatabankViews/ServletDatabankViews.jar`; 0 class declarations; SHA-256 `bed7a5051a0eee40bfc64876d5a0e38ff322a61759545f7d647ce990571790f6`.
- **Inspected reference:** `HARUQUANTAI_ROOT/docs/sqx/Shared/ServletDatabankViews.md`; roadmap allocation `FEAT-RESULTS-SERVLET-DATABANK-VIEWS`.
- **Owner:** `app/plugins/databank/ServletDatabankViews/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Databank views/actions/rename and correlation projections; downstream P09–P13.
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/plugins/ServletDatabankViews/ServletDatabankViews.jar"`; inspect manifest/resources and target runtime requirements.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_REFERENCE_ROOT/internal/plugins/ServletDatabankViews`; `SQX_REFERENCE_ROOT/internal/plugins/ResultsDatabankActions`; `SQX_REFERENCE_ROOT/internal/plugins/ProjectDatabanks`. Inspect `SQX_REFERENCE_ROOT/internal/plugins/ResultsDatabankActions/DatabankActionsService.js`; `SQX_REFERENCE_ROOT/internal/plugins/ProjectDatabanks/DatabankService.js`.
- **Existing UI connection:** databanks; proposed shared consumer; verify the exact existing control and public contract before implementation. Target `ui/app/plugins/databank/ResultsDatabankActions/DatabankActionsService.ts`; wire databank selection, actual resource mutations and saved/exported artifact IDs.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Create:** `app/plugins/databank/ServletDatabankViews/service.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/databank/ServletDatabankViews/routes.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/databank/ServletDatabankViews/contracts.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/databank/ServletDatabankViews/README.md`
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_results_servlet_databank_views.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/results_servlet_databank_views.json`
  - Store versioned paraphrased donor input/output fixtures.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/plugins/databank/ResultsDatabankActions/DatabankActionsService.ts`
  - Call owned typed commands; map responses/errors to current dialogs.
- **Modify:** `ui/app/plugins/databank/ProjectDatabanks/DatabankService.ts`
  - Call owned typed commands; map responses/errors to current dialogs.
- **Modify:** `ui/app/plugins/databank/ProjectDatabanks/databankStore.ts`
  - Replace affected mock job/resource authority with server projections; preserve selection/view state.
- **Create:** `ui/tests/unit/backend-connections/feat-results-servlet-databank-views.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-results-databanks-exports-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Expose DatabankViews commands through the owning domain routes; verify command parsing, typed outputs, authority, validation errors and cancellation.
- [ ] **Step 4:** `FR-RESULTS-SERVLET-DATABANK-VIEWS-RESOURCE-CONTRIBUTION` → `No compiled class entries; inspect registration/resources`: Verify the resource/manifest contract.
- [ ] **Step 5:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 6:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 7:** Connect retained UI: Ratify the feature-owned wire contract; bind databank selection, actual resource mutations and saved/exported artifact IDs to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 8:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_results_servlet_databank_views.py --no-cov`; expect command parsing, typed outputs, authority, validation errors and cancellation; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture command parsing, typed outputs, authority, validation errors and cancellation and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-results-servlet-databank-views.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-results-databanks-exports-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise databanks for FEAT-RESULTS-SERVLET-DATABANK-VIEWS; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.

# 8.35 FEAT-RESULTS-SERVLET-RENAME-TOOL - ServletRenameTool.jar

## 1. Objective

- **Goal:** Rename identified resources atomically through the owning service.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Render authoritative databanks, result analysis, charts and exports.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/plugins/ServletRenameTool/ServletRenameTool.jar`; 4 class declarations; SHA-256 `ebe6f9347a0c34737dafa1df96f5c381ccc532d3c431940189de4952bd638388`.
- **Inspected reference:** `HARUQUANTAI_ROOT/docs/sqx/Shared/ServletRenameTool.md`; roadmap allocation `FEAT-RESULTS-SERVLET-RENAME-TOOL`.
- **Owner:** `app/plugins/databank/ServletRenameTool/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Databank views/actions/rename and correlation projections; downstream P09–P13.
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/plugins/ServletRenameTool/ServletRenameTool.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/plugins/ServletRenameTool/ServletRenameTool.jar" com.strategyquant.plugin.Servlet.impl.RenameTool.RenameToolServlet`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_REFERENCE_ROOT/internal/plugins/ServletRenameTool`; `SQX_REFERENCE_ROOT/internal/plugins/ResultsDatabankActions`; `SQX_REFERENCE_ROOT/internal/plugins/ProjectDatabanks`. Inspect `SQX_REFERENCE_ROOT/internal/plugins/ResultsDatabankActions/DatabankActionsService.js`; `SQX_REFERENCE_ROOT/internal/plugins/ProjectDatabanks/DatabankService.js`.
- **Existing UI connection:** databanks; proposed shared consumer; verify the exact existing control and public contract before implementation. Target `ui/app/plugins/databank/ResultsDatabankActions/DatabankActionsService.ts`; wire databank selection, actual resource mutations and saved/exported artifact IDs.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Create:** `app/plugins/databank/ServletRenameTool/service.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/databank/ServletRenameTool/routes.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/databank/ServletRenameTool/contracts.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/databank/ServletRenameTool/README.md`
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_results_servlet_rename_tool.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/results_servlet_rename_tool.json`
  - Store versioned paraphrased donor input/output fixtures.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/plugins/databank/ResultsDatabankActions/DatabankActionsService.ts`
  - Call owned typed commands; map responses/errors to current dialogs.
- **Modify:** `ui/app/plugins/databank/ProjectDatabanks/DatabankService.ts`
  - Call owned typed commands; map responses/errors to current dialogs.
- **Modify:** `ui/app/plugins/databank/ProjectDatabanks/databankStore.ts`
  - Replace affected mock job/resource authority with server projections; preserve selection/view state.
- **Create:** `ui/tests/unit/backend-connections/feat-results-servlet-rename-tool.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-results-databanks-exports-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Rename identified resources atomically through the owning service; verify collision, stable IDs, history and permission rejection.
- [ ] **Step 4:** `FR-RESULTS-SERVLET-RENAME-TOOL-RENAME-TOOL-SERVLET-CONTRACT` → `com.strategyquant.plugin.Servlet.impl.RenameTool.RenameToolServlet`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-RESULTS-SERVLET-RENAME-TOOL-RENAME-TOOL-SERVLET-EXECUTE` → `com.strategyquant.plugin.Servlet.impl.RenameTool.RenameToolServlet.execute`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 7:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 8:** Connect retained UI: Ratify the feature-owned wire contract; bind databank selection, actual resource mutations and saved/exported artifact IDs to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 9:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_results_servlet_rename_tool.py --no-cov`; expect collision, stable IDs, history and permission rejection; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture collision, stable IDs, history and permission rejection and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-results-servlet-rename-tool.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-results-databanks-exports-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise databanks for FEAT-RESULTS-SERVLET-RENAME-TOOL; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.

# 8.36 FEAT-UI-CUSTOM-DATABANK-ACTIONS - CustomDatabankActions resource contribution

## 1. Objective

- **Goal:** Qualify and connect CustomDatabankActions without assuming a missing backend JAR.
- **Context / Problem Solved:** CustomDatabankActions is one of 17 roadmap contributions with no immediate JAR.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/plugins/CustomDatabankActions`; narrow source: Directory enumeration; no immediate file.
- **FR:** `FR-UI-CUSTOM-DATABANK-ACTIONS-RESOURCE-WORKFLOW`; proposed owning README `app/workspace/Results/README.md`.
- **Research:** inspect resource/module/config declarations and consuming registrations; fingerprint stable files and trace action routes.
- **Gap:** directory/resource presence does not prove an enabled workflow; empty contributions need explicit dispositions.

- **UI donors:** `SQX_REFERENCE_ROOT/internal/plugins/CustomDatabankActions`; `SQX_REFERENCE_ROOT/internal/plugins/ResultsDatabankActions`; `SQX_REFERENCE_ROOT/internal/plugins/ProjectDatabanks`. Inspect `SQX_REFERENCE_ROOT/internal/plugins/CustomDatabankActions/rename/RenameDatabankPopupCtrl.js`; `SQX_REFERENCE_ROOT/internal/plugins/CustomDatabankActions/rename/renameDatabankPopup.html`; `SQX_REFERENCE_ROOT/internal/plugins/CustomDatabankActions/delete/module.js`.
- **Existing UI connection:** databanks; proposed shared consumer; verify the exact existing control and public contract before implementation. Target `ui/app/plugins/databank/ResultsDatabankActions/DatabankActionsService.ts`; wire databank selection, actual resource mutations and saved/exported artifact IDs.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Create:** `app/workspace/Results/resource_contributions.py`
  - Mount only verified resource/action contributions through this owning capability.
- **Modify:** `app/workspace/Results/README.md` (proposed earlier in FEAT-RESULTS-APP-RESULTS)
  - Register the resource workflow and explicit empty/unavailable dispositions.
- **Create:** `tests/unit/sqx_features/test_ui_custom_databank_actions.py`
  - Verify contribution mount/unmount and action authority.
- **Modify:** `ui/app/workspace/Results/ResultsWorkspace.tsx`
  - Bind the verified resource workflow to real capability state.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/plugins/databank/ResultsDatabankActions/DatabankActionsService.ts`
  - Call owned typed commands; map responses/errors to current dialogs.
- **Modify:** `ui/app/plugins/databank/ProjectDatabanks/DatabankService.ts`
  - Call owned typed commands; map responses/errors to current dialogs.
- **Modify:** `ui/app/plugins/databank/ProjectDatabanks/databankStore.ts`
  - Replace affected mock job/resource authority with server projections; preserve selection/view state.
- **Create:** `ui/tests/unit/backend-connections/feat-ui-custom-databank-actions.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-results-databanks-exports-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Inspect and specify resource/action declarations, defaults, route consumers and active registration; approve the resulting FR contract.
- [ ] **Step 2:** `FR-UI-CUSTOM-DATABANK-ACTIONS-RESOURCE-WORKFLOW`: implement the evidenced resource workflow or ratified empty contribution; preserve domain ownership.
- [ ] **Step 3:** Bind verified UI controls to host/domain capabilities; define disabled, denied and unavailable states.
- [ ] **Step 4:** Test mount/unmount, missing resources, action authority and FR logs; retain versioned donor observations.

- [ ] **Step 5:** Connect retained UI: Ratify the feature-owned wire contract; bind databank selection, actual resource mutations and saved/exported artifact IDs to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 6:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_ui_custom_databank_actions.py --no-cov`; assert resource availability, owned lifecycle and denied/missing actions.
- **Manual / Browser Verification:** Open a real simulation result; filter/rename a fixture databank; compare trades/equity; download an export and reconcile totals. Inspect the CustomDatabankActions contribution; an empty or unavailable contribution must remain explicit.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-ui-custom-databank-actions.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-results-databanks-exports-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise databanks for FEAT-UI-CUSTOM-DATABANK-ACTIONS; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.

# 8.37 FEAT-UI-CUSTOM-RESULTS-PLUGIN-ACTIONS - CustomResultsPluginActions resource contribution

## 1. Objective

- **Goal:** Qualify and connect CustomResultsPluginActions without assuming a missing backend JAR.
- **Context / Problem Solved:** CustomResultsPluginActions is one of 17 roadmap contributions with no immediate JAR.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/plugins/CustomResultsPluginActions`; narrow source: Directory enumeration; no immediate file.
- **FR:** `FR-UI-CUSTOM-RESULTS-PLUGIN-ACTIONS-RESOURCE-WORKFLOW`; proposed owning README `app/workspace/Results/README.md`.
- **Research:** inspect resource/module/config declarations and consuming registrations; fingerprint stable files and trace action routes.
- **Gap:** directory/resource presence does not prove an enabled workflow; empty contributions need explicit dispositions.

- **UI donors:** `SQX_REFERENCE_ROOT/internal/plugins/CustomResultsPluginActions`; `SQX_REFERENCE_ROOT/internal/web/RESULTS`; `SQX_REFERENCE_ROOT/internal/plugins/ProjectResults`. Inspect `SQX_REFERENCE_ROOT/internal/plugins/CustomResultsPluginActions/rename/RenameResultsPluginPopupCtrl.js`; `SQX_REFERENCE_ROOT/internal/plugins/CustomResultsPluginActions/rename/renameResultsPluginPopup.html`; `SQX_REFERENCE_ROOT/internal/plugins/CustomResultsPluginActions/delete/module.js`.
- **Existing UI connection:** Results; proposed shared consumer; verify the exact existing control and public contract before implementation. Target `ui/app/workspace/Results/ResultsWorkspace.tsx`; wire persisted run/result lookup, selected sample, trades and reconciled metrics.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Modify:** `app/workspace/Results/resource_contributions.py` (proposed earlier in FEAT-UI-CUSTOM-DATABANK-ACTIONS)
  - Mount only verified resource/action contributions through this owning capability.
- **Modify:** `app/workspace/Results/README.md` (proposed earlier in FEAT-RESULTS-APP-RESULTS)
  - Register the resource workflow and explicit empty/unavailable dispositions.
- **Create:** `tests/unit/sqx_features/test_ui_custom_results_plugin_actions.py`
  - Verify contribution mount/unmount and action authority.
- **Modify:** `ui/app/workspace/Results/ResultsWorkspace.tsx`
  - Bind the verified resource workflow to real capability state.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/plugins/project/ProjectResults/ResultsCtrl.ts`
  - Await backend validation/commands; bind actual result and job states to existing controls.
- **Modify:** `ui/app/plugins/databank/ProjectDatabanks/databankStore.ts`
  - Replace affected mock job/resource authority with server projections; preserve selection/view state.
- **Create:** `ui/app/workspace/Results/resultsClient.ts`
  - Typed domain client over host transport; ratify route/schema/version, errors and cancellation. Reuse this proposed owner if delivered earlier.
- **Create:** `ui/tests/unit/backend-connections/feat-ui-custom-results-plugin-actions.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-results-databanks-exports-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Inspect and specify resource/action declarations, defaults, route consumers and active registration; approve the resulting FR contract.
- [ ] **Step 2:** `FR-UI-CUSTOM-RESULTS-PLUGIN-ACTIONS-RESOURCE-WORKFLOW`: implement the evidenced resource workflow or ratified empty contribution; preserve domain ownership.
- [ ] **Step 3:** Bind verified UI controls to host/domain capabilities; define disabled, denied and unavailable states.
- [ ] **Step 4:** Test mount/unmount, missing resources, action authority and FR logs; retain versioned donor observations.

- [ ] **Step 5:** Connect retained UI: Ratify the feature-owned wire contract; bind persisted run/result lookup, selected sample, trades and reconciled metrics to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 6:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_ui_custom_results_plugin_actions.py --no-cov`; assert resource availability, owned lifecycle and denied/missing actions.
- **Manual / Browser Verification:** Open a real simulation result; filter/rename a fixture databank; compare trades/equity; download an export and reconcile totals. Inspect the CustomResultsPluginActions contribution; an empty or unavailable contribution must remain explicit.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-ui-custom-results-plugin-actions.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-results-databanks-exports-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise Results for FEAT-UI-CUSTOM-RESULTS-PLUGIN-ACTIONS; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.

# 8.38 FEAT-UI-PROJECT-DATABANKS - ProjectDatabanks resource contribution

## 1. Objective

- **Goal:** Qualify and connect ProjectDatabanks without assuming a missing backend JAR.
- **Context / Problem Solved:** ProjectDatabanks is one of 17 roadmap contributions with no immediate JAR.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/plugins/ProjectDatabanks`; narrow source: `SQX_REFERENCE_ROOT/internal/plugins/ProjectDatabanks/module.js`.
- **FR:** `FR-UI-PROJECT-DATABANKS-RESOURCE-WORKFLOW`; proposed owning README `app/workspace/Results/README.md`.
- **Research:** inspect resource/module/config declarations and consuming registrations; fingerprint stable files and trace action routes.
- **Gap:** directory/resource presence does not prove an enabled workflow; empty contributions need explicit dispositions.

- **UI donors:** `SQX_REFERENCE_ROOT/internal/plugins/ProjectDatabanks`; `SQX_REFERENCE_ROOT/internal/plugins/ResultsDatabankActions`. Inspect `SQX_REFERENCE_ROOT/internal/plugins/ProjectDatabanks/DatabankService.js`; `SQX_REFERENCE_ROOT/internal/plugins/ProjectDatabanks/DatabankCtrl.js`; `SQX_REFERENCE_ROOT/internal/plugins/ProjectDatabanks/DatabanksCtrl.js`.
- **Existing UI connection:** databanks; exact retained source-map `ui/app/plugins/databank/ProjectDatabanks/source-map.json`. Target `ui/app/plugins/databank/ProjectDatabanks/DatabankService.ts`; wire databank selection, actual resource mutations and saved/exported artifact IDs.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Modify:** `app/workspace/Results/resource_contributions.py` (proposed earlier in FEAT-UI-CUSTOM-DATABANK-ACTIONS)
  - Mount only verified resource/action contributions through this owning capability.
- **Modify:** `app/workspace/Results/README.md` (proposed earlier in FEAT-RESULTS-APP-RESULTS)
  - Register the resource workflow and explicit empty/unavailable dispositions.
- **Create:** `tests/unit/sqx_features/test_ui_project_databanks.py`
  - Verify contribution mount/unmount and action authority.
- **Modify:** `ui/app/workspace/Results/ResultsWorkspace.tsx`
  - Bind the verified resource workflow to real capability state.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/plugins/databank/ProjectDatabanks/DatabankService.ts`
  - Call owned typed commands; map responses/errors to current dialogs.
- **Modify:** `ui/app/plugins/databank/ProjectDatabanks/DatabankCtrl.ts`
  - Await backend validation/commands; bind actual result and job states to existing controls.
- **Modify:** `ui/app/plugins/databank/ProjectDatabanks/DatabanksCtrl.ts`
  - Await backend validation/commands; bind actual result and job states to existing controls.
- **Modify:** `ui/app/plugins/databank/ProjectDatabanks/DatabankDialogs.tsx`
  - Display databank selection, actual resource mutations and saved/exported artifact IDs from backend responses; preserve layout.
- **Modify:** `ui/app/plugins/databank/ProjectDatabanks/databankStore.ts`
  - Replace affected mock job/resource authority with server projections; preserve selection/view state.
- **Create:** `ui/tests/unit/backend-connections/feat-ui-project-databanks.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-results-databanks-exports-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Inspect and specify resource/action declarations, defaults, route consumers and active registration; approve the resulting FR contract.
- [ ] **Step 2:** `FR-UI-PROJECT-DATABANKS-RESOURCE-WORKFLOW`: implement the evidenced resource workflow or ratified empty contribution; preserve domain ownership.
- [ ] **Step 3:** Bind verified UI controls to host/domain capabilities; define disabled, denied and unavailable states.
- [ ] **Step 4:** Test mount/unmount, missing resources, action authority and FR logs; retain versioned donor observations.

- [ ] **Step 5:** Connect retained UI: Ratify the feature-owned wire contract; bind databank selection, actual resource mutations and saved/exported artifact IDs to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 6:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_ui_project_databanks.py --no-cov`; assert resource availability, owned lifecycle and denied/missing actions.
- **Manual / Browser Verification:** Open a real simulation result; filter/rename a fixture databank; compare trades/equity; download an export and reconcile totals. Inspect the ProjectDatabanks contribution; an empty or unavailable contribution must remain explicit.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-ui-project-databanks.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-results-databanks-exports-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise databanks for FEAT-UI-PROJECT-DATABANKS; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.

# 8.39 FEAT-UI-PROJECT-RESULTS - ProjectResults resource contribution

## 1. Objective

- **Goal:** Qualify and connect ProjectResults without assuming a missing backend JAR.
- **Context / Problem Solved:** ProjectResults is one of 17 roadmap contributions with no immediate JAR.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/plugins/ProjectResults`; narrow source: `SQX_REFERENCE_ROOT/internal/plugins/ProjectResults/module.js`.
- **FR:** `FR-UI-PROJECT-RESULTS-RESOURCE-WORKFLOW`; proposed owning README `app/workspace/Results/README.md`.
- **Research:** inspect resource/module/config declarations and consuming registrations; fingerprint stable files and trace action routes.
- **Gap:** directory/resource presence does not prove an enabled workflow; empty contributions need explicit dispositions.

- **UI donors:** `SQX_REFERENCE_ROOT/internal/plugins/ProjectResults`; `SQX_REFERENCE_ROOT/internal/web/RESULTS`. Inspect `SQX_REFERENCE_ROOT/internal/plugins/ProjectResults/ResultsCtrl.js`; `SQX_REFERENCE_ROOT/internal/plugins/ProjectResults/newCustomPluginModal.html`; `SQX_REFERENCE_ROOT/internal/plugins/ProjectResults/results.html`.
- **Existing UI connection:** Results; exact retained source-map `ui/app/plugins/project/ProjectResults/source-map.json`. Target `ui/app/plugins/project/ProjectResults/ResultsCtrl.ts`; wire persisted run/result lookup, selected sample, trades and reconciled metrics.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Modify:** `app/workspace/Results/resource_contributions.py` (proposed earlier in FEAT-UI-CUSTOM-DATABANK-ACTIONS)
  - Mount only verified resource/action contributions through this owning capability.
- **Modify:** `app/workspace/Results/README.md` (proposed earlier in FEAT-RESULTS-APP-RESULTS)
  - Register the resource workflow and explicit empty/unavailable dispositions.
- **Create:** `tests/unit/sqx_features/test_ui_project_results.py`
  - Verify contribution mount/unmount and action authority.
- **Modify:** `ui/app/workspace/Results/ResultsWorkspace.tsx`
  - Bind the verified resource workflow to real capability state.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/plugins/project/ProjectResults/ResultsCtrl.ts`
  - Await backend validation/commands; bind actual result and job states to existing controls.
- **Modify:** `ui/app/plugins/project/ProjectResults/newCustomPluginModal.tsx`
  - Display persisted run/result lookup, selected sample, trades and reconciled metrics from backend responses; preserve layout.
- **Modify:** `ui/app/plugins/project/ProjectResults/results.tsx`
  - Display persisted run/result lookup, selected sample, trades and reconciled metrics from backend responses; preserve layout.
- **Create:** `ui/app/plugins/project/ProjectResults/backendClient.ts`
  - Typed domain client over host transport; ratify route/schema/version, errors and cancellation. Reuse this proposed owner if delivered earlier.
- **Create:** `ui/tests/unit/backend-connections/feat-ui-project-results.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-results-databanks-exports-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Inspect and specify resource/action declarations, defaults, route consumers and active registration; approve the resulting FR contract.
- [ ] **Step 2:** `FR-UI-PROJECT-RESULTS-RESOURCE-WORKFLOW`: implement the evidenced resource workflow or ratified empty contribution; preserve domain ownership.
- [ ] **Step 3:** Bind verified UI controls to host/domain capabilities; define disabled, denied and unavailable states.
- [ ] **Step 4:** Test mount/unmount, missing resources, action authority and FR logs; retain versioned donor observations.

- [ ] **Step 5:** Connect retained UI: Ratify the feature-owned wire contract; bind persisted run/result lookup, selected sample, trades and reconciled metrics to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 6:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_ui_project_results.py --no-cov`; assert resource availability, owned lifecycle and denied/missing actions.
- **Manual / Browser Verification:** Open a real simulation result; filter/rename a fixture databank; compare trades/equity; download an export and reconcile totals. Inspect the ProjectResults contribution; an empty or unavailable contribution must remain explicit.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-ui-project-results.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-results-databanks-exports-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise Results for FEAT-UI-PROJECT-RESULTS; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.

# 8.40 FEAT-UI-RESULTS-REPORT - ResultsReport resource contribution

## 1. Objective

- **Goal:** Qualify and connect ResultsReport without assuming a missing backend JAR.
- **Context / Problem Solved:** ResultsReport is one of 17 roadmap contributions with no immediate JAR.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/plugins/ResultsReport`; narrow source: `SQX_REFERENCE_ROOT/internal/plugins/ResultsReport/module.js`.
- **FR:** `FR-UI-RESULTS-REPORT-RESOURCE-WORKFLOW`; proposed owning README `app/workspace/Results/README.md`.
- **Research:** inspect resource/module/config declarations and consuming registrations; fingerprint stable files and trace action routes.
- **Gap:** directory/resource presence does not prove an enabled workflow; empty contributions need explicit dispositions.

- **UI donors:** `SQX_REFERENCE_ROOT/internal/plugins/ResultsReport`; `SQX_REFERENCE_ROOT/internal/web/RESULTS`; `SQX_REFERENCE_ROOT/internal/plugins/ProjectResults`. Inspect `SQX_REFERENCE_ROOT/internal/plugins/ResultsReport/ReportCtrl.js`; `SQX_REFERENCE_ROOT/internal/plugins/ResultsReport/report.html`; `SQX_REFERENCE_ROOT/internal/plugins/ResultsReport/module.js`.
- **Existing UI connection:** Results; proposed shared consumer; verify the exact existing control and public contract before implementation. Target `ui/app/workspace/Results/ResultsWorkspace.tsx`; wire persisted run/result lookup, selected sample, trades and reconciled metrics.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Modify:** `app/workspace/Results/resource_contributions.py` (proposed earlier in FEAT-UI-CUSTOM-DATABANK-ACTIONS)
  - Mount only verified resource/action contributions through this owning capability.
- **Modify:** `app/workspace/Results/README.md` (proposed earlier in FEAT-RESULTS-APP-RESULTS)
  - Register the resource workflow and explicit empty/unavailable dispositions.
- **Create:** `tests/unit/sqx_features/test_ui_results_report.py`
  - Verify contribution mount/unmount and action authority.
- **Modify:** `ui/app/workspace/Results/ResultsWorkspace.tsx`
  - Bind the verified resource workflow to real capability state.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/plugins/project/ProjectResults/ResultsCtrl.ts`
  - Await backend validation/commands; bind actual result and job states to existing controls.
- **Modify:** `ui/app/plugins/databank/ProjectDatabanks/databankStore.ts`
  - Replace affected mock job/resource authority with server projections; preserve selection/view state.
- **Create:** `ui/app/workspace/Results/resultsClient.ts`
  - Typed domain client over host transport; ratify route/schema/version, errors and cancellation. Reuse this proposed owner if delivered earlier.
- **Create:** `ui/tests/unit/backend-connections/feat-ui-results-report.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-results-databanks-exports-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Inspect and specify resource/action declarations, defaults, route consumers and active registration; approve the resulting FR contract.
- [ ] **Step 2:** `FR-UI-RESULTS-REPORT-RESOURCE-WORKFLOW`: implement the evidenced resource workflow or ratified empty contribution; preserve domain ownership.
- [ ] **Step 3:** Bind verified UI controls to host/domain capabilities; define disabled, denied and unavailable states.
- [ ] **Step 4:** Test mount/unmount, missing resources, action authority and FR logs; retain versioned donor observations.

- [ ] **Step 5:** Connect retained UI: Ratify the feature-owned wire contract; bind persisted run/result lookup, selected sample, trades and reconciled metrics to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 6:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_ui_results_report.py --no-cov`; assert resource availability, owned lifecycle and denied/missing actions.
- **Manual / Browser Verification:** Open a real simulation result; filter/rename a fixture databank; compare trades/equity; download an export and reconcile totals. Inspect the ResultsReport contribution; an empty or unavailable contribution must remain explicit.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-ui-results-report.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-results-databanks-exports-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise Results for FEAT-UI-RESULTS-REPORT; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.

# 8.41 P08 integration — Render authoritative databanks, result analysis, charts and exports

## 1. Objective

- **Goal:** Render authoritative databanks, result analysis, charts and exports.
- **Context / Problem Solved:** The existing UI needs a real end-to-end backend workflow, beyond isolated JAR adapters.

## 2. Research and donors

- **Roadmap:** `HARUQUANTAI_ROOT/docs/dev/sqx-full-application-roadmap.md`, P08; donor features and FRs are the tasks in this file.
- **Existing code:** `ui/app/workspace/Results/ResultsWorkspace.tsx`, `ui/app/workspace/Chart/ChartWorkspace.tsx`; backend counterparts are proposed.
- **Declared dependencies:** FastAPI, Pydantic, Uvicorn, psutil; host persistence choice remains unratified.
- **Existing tests:** `ui/tests/unit/workspace/Chart/alerts.test.ts`; extend actual-backend assertions.
- **Conflict/gap:** frontend existence does not establish functional backend behavior; route/schema/discovery changes need a task plan and approval.
- **Cross-feature ownership:** shared files may host multiple features; keep per-FR traces and delegate persistence/jobs to host capabilities.

- **UI donors:** `SQX_REFERENCE_ROOT/internal/web/RESULTS`; `SQX_REFERENCE_ROOT/internal/plugins/ProjectResults`. Inspect `SQX_REFERENCE_ROOT/internal/web/RESULTS/layout/LayoutService.js`; `SQX_REFERENCE_ROOT/internal/plugins/ProjectResults/ResultsCtrl.js`.
- **Existing UI connection:** Results; proposed shared consumer; verify the exact existing control and public contract before implementation. Target `ui/app/workspace/Results/ResultsWorkspace.tsx`; wire persisted run/result lookup, selected sample, trades and reconciled metrics.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Create:** `app/plugins/databank/repository.py`
  - Deliver the phase's typed contracts and integration flow; extend prior approved owners where shared.
- **Create:** `app/plugins/databank/views.py`
  - Deliver the phase's typed contracts and integration flow; extend prior approved owners where shared.
- **Create:** `app/plugins/databank/actions.py`
  - Deliver the phase's typed contracts and integration flow; extend prior approved owners where shared.
- **Create:** `app/plugins/results/service.py`
  - Deliver the phase's typed contracts and integration flow; extend prior approved owners where shared.
- **Create:** `app/plugins/results/series.py`
  - Deliver the phase's typed contracts and integration flow; extend prior approved owners where shared.
- **Create:** `app/plugins/results/trade_analysis.py`
  - Deliver the phase's typed contracts and integration flow; extend prior approved owners where shared.
- **Modify:** `app/workspace/Results/routes.py` (proposed earlier in FEAT-RESULTS-APP-RESULTS)
  - Deliver the phase's typed contracts and integration flow; extend prior approved owners where shared.
- **Create:** `app/workspace/Chart/routes.py`
  - Deliver the phase's typed contracts and integration flow; extend prior approved owners where shared.
- **Modify:** `app/plugins/export/html.py` (proposed earlier in FEAT-RESULTS-COMMONS-IMAGING)
  - Deliver the phase's typed contracts and integration flow; extend prior approved owners where shared.
- **Modify:** `app/plugins/export/pdf.py` (proposed earlier in FEAT-RESULTS-COMMONS-IMAGING)
  - Deliver the phase's typed contracts and integration flow; extend prior approved owners where shared.
- **Modify:** `app/plugins/export/spreadsheet.py` (proposed earlier in FEAT-RESULTS-COMMONS-IMAGING)
  - Deliver the phase's typed contracts and integration flow; extend prior approved owners where shared.
- **Modify:** `ui/app/workspace/Results/ResultsWorkspace.tsx`
  - Bind real capability state, errors and cancellation while preserving the existing layout.
- **Create:** `ui/app/workspace/Results/resultsClient.ts`
  - Own typed routes/envelopes for this domain; replace mock execution with authoritative requests.
- **Modify:** `ui/app/workspace/Chart/ChartWorkspace.tsx`
  - Bind real capability state, errors and cancellation while preserving the existing layout.
- **Create:** `ui/app/workspace/Chart/chartClient.ts`
  - Own typed routes/envelopes for this domain; replace mock execution with authoritative requests.
- **Modify:** `app/workspace/Results/README.md` (proposed earlier in FEAT-RESULTS-APP-RESULTS)
  - Own feature registration/status and phase contract decisions after ratification.
- **Create:** `tests/integration/test_results_databanks_exports_workflow.py`
  - Exercise the real phase workflow in isolated stores with failure/cancellation assertions.
- **Create:** `ui/tests/e2e/sqx-results-databanks-exports-backend.spec.ts`
  - Use an isolated real host to verify UI state and request/output reconciliation.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/plugins/project/ProjectResults/ResultsCtrl.ts`
  - Await backend validation/commands; bind actual result and job states to existing controls.
- **Modify:** `ui/app/plugins/databank/ProjectDatabanks/databankStore.ts`
  - Replace affected mock job/resource authority with server projections; preserve selection/view state.
- **Create:** `ui/tests/unit/backend-connections/task-8-41.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Review preceding feature fixtures and owning README registrations; ratify the phase integration contracts and execution plan.
- [ ] **Step 2:** Define result/databank identities, metric provenance, projection units and action authority.
- [ ] **Step 3:** Implement views, correlation/filter/rename, chart series, trade analysis and artifact exports.
- [ ] **Step 4:** Bind Results and Chart to stored simulator artifacts; preserve selection and history.
- [ ] **Step 5:** Replace fixture-driven production execution in the affected workflow; retain deterministic fixtures only in tests.
- [ ] **Step 6:** Test positive/failure/cancellation paths and observable FR logs; reload/reconnect and reconcile persisted outputs.
- [ ] **Step 7:** Record exact commands, timestamped artifacts, unresolved gaps and walkthrough; obtain separate owner commit authority.

- [ ] **Step 8:** Connect retained UI: Ratify the feature-owned wire contract; bind persisted run/result lookup, selected sample, trades and reconciled metrics to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 9:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/integration/test_results_databanks_exports_workflow.py --no-cov`; `npm --prefix ui run test -- tests/unit/workspace/Chart/alerts.test.ts`; `npm --prefix ui run test:ui -- tests/e2e/sqx-results-databanks-exports-backend.spec.ts`. Assert stored-result reload, table/chart reconciliation, correlation and exported totals; reject empty result, missing benchmark, invalid filter and denied destructive action.
- **Manual / Browser Verification:** Open a real simulation result; filter/rename a fixture databank; compare trades/equity; download an export and reconcile totals.

- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/task-8-41.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-results-databanks-exports-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise Results for 8.41; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.

## Phase completion gate

- [ ] Every applicable feature passed its own isolated real-host UI/backend case; no production mock fallback or unresolved required UI remains.

- [ ] Reconcile all allocated FEAT/FR dispositions, donor fixtures and ownership gaps.
- [ ] Run Ruff format/check and strict Mypy on the approved changed Python paths; verify branch-aware coverage ≥80% across retained application source at release.
- [ ] For affected UI: `npm --prefix ui run typecheck`, `npm --prefix ui run test`, `npm --prefix ui run build`.
- [ ] Record real workflow observations, timestamps, failure artifacts and remaining gaps in the walkthrough.
- [ ] Obtain the next task/phase approval; commits and external/destructive actions retain separate owner gates.

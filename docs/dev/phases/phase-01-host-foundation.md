# P01 — Host bootstrap, logging, configuration and diagnostics

- **Source:** `HARUQUANTAI_ROOT/docs/dev/sqx-full-application-roadmap.md`; SHA-256 `9abec0aa2faf6bd78b39e80c2dcfb7dfcae62ae412d9b56a77904de6a7b5a54c`.
- **Dependencies:** P00 (P00 prerequisites below).
- **Scope:** 18 JAR feature tasks, 0 resource tasks, one phase integration task.
- **State:** proposed checklists; all execution, registrations and target contracts require task-level approval.
- **File labels:** existing paths are Modify; absent paths are Create; later shared edits name their earlier proposed owner.
- **Execution standard:** AGENTS.md plan → approval → implementation → tests → walkthrough; canonical Python docstrings, typed public APIs and explicit FR logs.
- **Clean room:** donor signatures guide behavioral research; independently written implementations; no proprietary source in evidence; no parity claim without independent validation.
- **Verification:** commands below are future tasks, not reported passes; isolated stores only; no live-store schema change/restore or Git mutation.
- **UI completion:** Applicable features finish with backend + retained UI connected; preserve layouts. Production mocks cannot substitute for capability execution; keep a task unchecked while transport/contracts or required controls are unresolved.
- **Connected verification:** Use an isolated real host and temporary data. Existing mock-only/browser-API-blocking suites are UI regressions, not connected acceptance. Run `npm --prefix ui run typecheck`, `npm --prefix ui run test`, `npm --prefix ui run build` after actual UI source changes.

# 1.1 P00 prerequisites — evidence, ownership and missing common core

## 1. Objective

- **Goal:** Ratify a recoverable evidence/architecture baseline before P01 source execution.
- **Context / Problem Solved:** P00 is folded into P01 to keep exactly 18 files. The owner-approved P00 plan restores reset-aware authority and reference tooling; common-core/runtime prerequisites remain blocked.
- **Delivery status:** P00 evidence baseline delivered under plan version 1, approved `APPROVED: EXECUTE` on 2026-10-06. This is not completion of all P00 runtime prerequisites or qualification of P01. See `docs/dev/evidence/p00-release-matrix.md` and `.agents/logs/20261006_175657_p00-prerequisites/walkthrough.md` for recorded candidate checks.

## 2. Research and donors

- **Donors:** SQX launcher/configuration, internal JAR manifests, Extending_SQX.pdf and user settings/projects/strategies/customdata under SQX_REFERENCE_ROOT.
- **Audit:** backend Python runtime remains absent. Reset-aware docs/PROJECT.md, docs/ARCHITECTURE.md, app/host/README.md and tests/reference tooling now exist. Current ledger/schema are `docs/dev/evidence/reimplementation.{json,schema.json}`; 88 historical records and their original schema are preserved at `docs/dev/evidence/history/3ede688/`. UI typed clients remain provisional.
- **Conflict resolved:** docs/templates/PYTHON_MODULE.md now uses the constitutional `Key Capabilities:` sample heading under `DEC-HOST-P00-MODULE-HEADING`.
- **Gap:** MainApp/AppSettings and launcher SQLib.jar packaging remain unresolved; manifest/class lookup and runtime validation must establish the owner.
- **Commands:** `git status --short`; `rg --files docs ui scripts`; inspect StrategyQuantX.config/sqcli.config and `jar tf` using logical-root variables.

- **UI readiness research:** `ui/app/host/transport.ts`, `ui/README.md` and current workspace/plugin source maps; distinguish retained mock screens from qualified backend consumers.

## 3. File Changes

- **Create:** `docs/PROJECT.md`
  - Restore or create only after owner ratifies scope and feature ownership.
- **Create:** `docs/ARCHITECTURE.md`
  - Restore or create ratified host/domain boundaries and capability contracts.
- **Create:** `app/host/README.md`
  - Register approved host feature/FR/decision IDs and resource/storage ownership.
- **Create:** `tests/reference/manifest.py`
  - Track donor version, fingerprint, fixture provenance and execution timestamps.
- **Create:** `tests/reference/fixtures.py`
  - Load independent bounded fixtures with no proprietary source or sensitive data.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Freeze the 261-JAR/17-resource inventory and source roadmap hash; resolve active/inactive products and unresolved core symbols.
- [x] **Step 2:** Locate historical specification/ledger authority read-only; propose restoration/new schema paths for owner approval before writing them. Original ledger/schema snapshots and source fingerprints are preserved; schema v2 evolution was explicitly approved.
- [x] **Step 3:** Map each proposed FEAT/FR to its owning README; retain existing IDs, identify registration gaps and ratify decision IDs. `p00-ownership.json` maps 261 feature proposals, 667 seeds and 17 resources with proposed README paths and missing registrations. Only FEAT-HOST-EVIDENCE and its seven FRs/nine decisions are registered; existing UI registries are preserved.
- [ ] **Step 4:** Enumerate consumed classes/functions beyond the 667 seeds; write paraphrased behavioral specifications and versioned expected outputs.
- [x] **Step 5:** When ledger edits are approved, read ledger/schema, allocate highest ID + 1, record atomic claims with fingerprints/locations/limits/review and link supersessions. New atomic records are SQX144-EV-000089 through SQX144-EV-000117; history keeps original identities/relationships and historical validation states. New source observations remain unreviewed.
- [x] **Step 6:** Preserve clean-room flags; keep proprietary source outside repository evidence; validate ledger schema, source/record references and registry IDs. Full Draft 2020-12, lineage, registered identity and negative-gate checks execute through tests/reference/validate.py; bytecode is paraphrased, not published.
- [ ] **Step 7:** Ratify release cohort, numerical tolerances, dependency decisions, external/destructive authority and future exact ALLOWED_WRITE_PATHS.

- **Remaining Step 1:** The 261-JAR/17-resource inventory and roadmap hash are frozen and rechecked. Installed product build/activation and missing SQLib/MainApp/AppSettings/CpuInfo implementation remain unresolved.
- **Remaining Step 4:** A 182-class/58-archive structural consumer index and selected body-derived traces extend the seeds. Initial fixtures record actual static count/order observations. Complete consumed-method closure and independent donor runtime outputs remain unavailable.
- **Remaining Step 7:** P00 evidence-only release, exact static comparisons, two dev validation dependencies, tooling logging adapter and exact writes were approved. Future numerical policies, runtime contracts, external/destructive effects and P01 write paths require their own decisions/plans. No blanket tolerance or operational store activation was ratified.

- [ ] **Step 8:** Record UI prerequisites: Reconcile feature-to-retained-screen ownership, transport/session dependencies and missing controls before execution; do not register completion from a mock screen.

## 5. Verification & Testing

- **Automated Tests:** Inventory reconciliation and registry/schema checks after restoration; no runtime or ledger pass is claimed before actual recorded observations.
- **Manual / Browser Verification:** Owner reviews restored authority, common-core gaps and the selected fixture/release matrix before backend execution.

# 1.2 FEAT-HOST-COMMONS-BEANUTILS - commons-beanutils.jar

## 1. Objective

- **Goal:** Replace consumed bean/property conversion with typed settings conversion.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Boot the host with validated settings, structured logging and diagnostics.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/libs/commons-beanutils.jar`; 137 class declarations; SHA-256 `23729e3a2677ed5fb164ec999ba3fcdde3f8460e5ed086b6a43d8b5d46998d42`.
- **Inspected reference:** No dedicated docs/sqx coverage; expand archive inspection; roadmap allocation `FEAT-HOST-COMMONS-BEANUTILS`.
- **Owner:** `app/host/resources/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Common utility dependencies; use standard/library adapters for verified consumed functions; downstream P02–P18.
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/libs/commons-beanutils.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/libs/commons-beanutils.jar" org.apache.commons.beanutils.BaseDynaBeanMapDecorator`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Dependency:** qualify stdlib/declared packages; approve additions; classify JVM-only internals.

- **UI disposition:** Infrastructure only; no standalone UI component found in this library allocation. Its owned backend consumer feeds Debug Console through the phase integration gate; do not invent a library screen or direct plugin route.

## 3. File Changes

- **Create:** `app/host/resources/files.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/host/resources/encoding.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/host/resources/README.md`
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_host_commons_beanutils.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/host_commons_beanutils.json`
  - Store versioned paraphrased donor input/output fixtures.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Replace consumed bean/property conversion with typed settings conversion; verify coercion, missing properties and rejected unknown fields.
- [ ] **Step 4:** `FR-HOST-COMMONS-BEANUTILS-BASE-DYNA-BEAN-MAP-DECORATOR-CONTRACT` → `org.apache.commons.beanutils.BaseDynaBeanMapDecorator`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-HOST-COMMONS-BEANUTILS-BASE-DYNA-BEAN-MAP-DECORATOR-IS-READ-ONLY` → `org.apache.commons.beanutils.BaseDynaBeanMapDecorator.isReadOnly`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** `FR-HOST-COMMONS-BEANUTILS-BASE-DYNA-BEAN-MAP-DECORATOR-CLEAR` → `org.apache.commons.beanutils.BaseDynaBeanMapDecorator.clear`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 7:** Wire qualified adapters to consumers; release resources on failure/shutdown.
- [ ] **Step 8:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 9:** Verify UI-facing consumer contract: Test this infrastructure through its declared backend/host consumer; expose failures through the owning domain envelope. The phase's connected UI gate verifies the observable workflow.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_host_commons_beanutils.py --no-cov`; expect coercion, missing properties and rejected unknown fields; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture coercion, missing properties and rejected unknown fields and visible failures.

# 1.3 FEAT-HOST-COMMONS-CODEC - commons-codec.jar

## 1. Objective

- **Goal:** Provide only consumed encoding, decoding and digest operations.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Boot the host with validated settings, structured logging and diagnostics.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/libs/commons-codec.jar`; 85 class declarations; SHA-256 `ad19d2601c3abf0b946b5c3a4113e226a8c1e3305e395b90013b78dd94a723ce`.
- **Inspected reference:** No dedicated docs/sqx coverage; expand archive inspection; roadmap allocation `FEAT-HOST-COMMONS-CODEC`.
- **Owner:** `app/host/resources/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Common utility dependencies; use standard/library adapters for verified consumed functions; downstream P02–P18.
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/libs/commons-codec.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/libs/commons-codec.jar" org.apache.commons.codec.BinaryDecoder`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Dependency:** qualify stdlib/declared packages; approve additions; classify JVM-only internals.

- **UI disposition:** Infrastructure only; no standalone UI component found in this library allocation. Its owned backend consumer feeds Debug Console through the phase integration gate; do not invent a library screen or direct plugin route.

## 3. File Changes

- **Modify:** `app/host/resources/files.py` (proposed earlier in FEAT-HOST-COMMONS-BEANUTILS)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/host/resources/encoding.py` (proposed earlier in FEAT-HOST-COMMONS-BEANUTILS)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/host/resources/README.md` (proposed earlier in FEAT-HOST-COMMONS-BEANUTILS)
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_host_commons_codec.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/host_commons_codec.json`
  - Store versioned paraphrased donor input/output fixtures.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Provide only consumed encoding, decoding and digest operations; verify encoding vectors, malformed input and byte/text boundary.
- [ ] **Step 4:** `FR-HOST-COMMONS-CODEC-BINARY-DECODER-CONTRACT` → `org.apache.commons.codec.BinaryDecoder`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-HOST-COMMONS-CODEC-BINARY-DECODER-DECODE` → `org.apache.commons.codec.BinaryDecoder.decode`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** Wire qualified adapters to consumers; release resources on failure/shutdown.
- [ ] **Step 7:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 8:** Verify UI-facing consumer contract: Test this infrastructure through its declared backend/host consumer; expose failures through the owning domain envelope. The phase's connected UI gate verifies the observable workflow.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_host_commons_codec.py --no-cov`; expect encoding vectors, malformed input and byte/text boundary; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture encoding vectors, malformed input and byte/text boundary and visible failures.

# 1.4 FEAT-HOST-COMMONS-COLLECTIONS - commons-collections.jar

## 1. Objective

- **Goal:** Adapt consumed collection, string and utility contracts through Python primitives.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Boot the host with validated settings, structured logging and diagnostics.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/libs/commons-collections.jar`; 458 class declarations; SHA-256 `87363a4c94eaabeefd8b930cb059f66b64c9f7d632862f23de3012da7660047b`.
- **Inspected reference:** No dedicated docs/sqx coverage; expand archive inspection; roadmap allocation `FEAT-HOST-COMMONS-COLLECTIONS`.
- **Owner:** `app/host/resources/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Common utility dependencies; use standard/library adapters for verified consumed functions; downstream P02–P18.
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/libs/commons-collections.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/libs/commons-collections.jar" org.apache.commons.collections.ArrayStack`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Dependency:** qualify stdlib/declared packages; approve additions; classify JVM-only internals.

- **UI disposition:** Infrastructure only; no standalone UI component found in this library allocation. Its owned backend consumer feeds Debug Console through the phase integration gate; do not invent a library screen or direct plugin route.

## 3. File Changes

- **Modify:** `app/host/resources/files.py` (proposed earlier in FEAT-HOST-COMMONS-BEANUTILS)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/host/resources/encoding.py` (proposed earlier in FEAT-HOST-COMMONS-BEANUTILS)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/host/resources/README.md` (proposed earlier in FEAT-HOST-COMMONS-BEANUTILS)
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_host_commons_collections.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/host_commons_collections.json`
  - Store versioned paraphrased donor input/output fixtures.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Adapt consumed collection, string and utility contracts through Python primitives; verify ordering, duplicate/null handling and bounded collection behavior.
- [ ] **Step 4:** `FR-HOST-COMMONS-COLLECTIONS-ARRAY-STACK-CONTRACT` → `org.apache.commons.collections.ArrayStack`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-HOST-COMMONS-COLLECTIONS-ARRAY-STACK-EMPTY` → `org.apache.commons.collections.ArrayStack.empty`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** `FR-HOST-COMMONS-COLLECTIONS-ARRAY-STACK-PEEK` → `org.apache.commons.collections.ArrayStack.peek`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 7:** Wire qualified adapters to consumers; release resources on failure/shutdown.
- [ ] **Step 8:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 9:** Verify UI-facing consumer contract: Test this infrastructure through its declared backend/host consumer; expose failures through the owning domain envelope. The phase's connected UI gate verifies the observable workflow.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_host_commons_collections.py --no-cov`; expect ordering, duplicate/null handling and bounded collection behavior; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture ordering, duplicate/null handling and bounded collection behavior and visible failures.

# 1.5 FEAT-HOST-COMMONS-IO-ICM - commons-io-icm.jar

## 1. Objective

- **Goal:** Own consumed file/path/stream operations through host resources.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Boot the host with validated settings, structured logging and diagnostics.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/libs/commons-io-icm.jar`; 110 class declarations; SHA-256 `cc6a41dc3eaacc9e440a6bd0d2890b20d36b4ee408fe2d67122f328bb6e01581`.
- **Inspected reference:** No dedicated docs/sqx coverage; expand archive inspection; roadmap allocation `FEAT-HOST-COMMONS-IO-ICM`.
- **Owner:** `app/host/resources/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Common utility dependencies; use standard/library adapters for verified consumed functions; downstream P02–P18.
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/libs/commons-io-icm.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/libs/commons-io-icm.jar" org.apache.commons.io.ByteOrderMark`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Dependency:** qualify stdlib/declared packages; approve additions; classify JVM-only internals.

- **UI disposition:** Infrastructure only; no standalone UI component found in this library allocation. Its owned backend consumer feeds Debug Console through the phase integration gate; do not invent a library screen or direct plugin route.

## 3. File Changes

- **Modify:** `app/host/resources/files.py` (proposed earlier in FEAT-HOST-COMMONS-BEANUTILS)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/host/resources/encoding.py` (proposed earlier in FEAT-HOST-COMMONS-BEANUTILS)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/host/resources/README.md` (proposed earlier in FEAT-HOST-COMMONS-BEANUTILS)
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_host_commons_io_icm.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/host_commons_io_icm.json`
  - Store versioned paraphrased donor input/output fixtures.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Own consumed file/path/stream operations through host resources; verify encoding, path containment, interrupted write and closed handle.
- [ ] **Step 4:** `FR-HOST-COMMONS-IO-ICM-BYTE-ORDER-MARK-CONTRACT` → `org.apache.commons.io.ByteOrderMark`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-HOST-COMMONS-IO-ICM-BYTE-ORDER-MARK-GET-CHARSET-NAME` → `org.apache.commons.io.ByteOrderMark.getCharsetName`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** `FR-HOST-COMMONS-IO-ICM-BYTE-ORDER-MARK-LENGTH` → `org.apache.commons.io.ByteOrderMark.length`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 7:** Wire qualified adapters to consumers; release resources on failure/shutdown.
- [ ] **Step 8:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 9:** Verify UI-facing consumer contract: Test this infrastructure through its declared backend/host consumer; expose failures through the owning domain envelope. The phase's connected UI gate verifies the observable workflow.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_host_commons_io_icm.py --no-cov`; expect encoding, path containment, interrupted write and closed handle; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture encoding, path containment, interrupted write and closed handle and visible failures.

# 1.6 FEAT-HOST-COMMONS-IO - commons-io.jar

## 1. Objective

- **Goal:** Own consumed file/path/stream operations through host resources.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Boot the host with validated settings, structured logging and diagnostics.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/libs/commons-io.jar`; 110 class declarations; SHA-256 `cc6a41dc3eaacc9e440a6bd0d2890b20d36b4ee408fe2d67122f328bb6e01581`.
- **Inspected reference:** No dedicated docs/sqx coverage; expand archive inspection; roadmap allocation `FEAT-HOST-COMMONS-IO`.
- **Owner:** `app/host/resources/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Common utility dependencies; use standard/library adapters for verified consumed functions; downstream P02–P18.
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/libs/commons-io.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/libs/commons-io.jar" org.apache.commons.io.ByteOrderMark`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Dependency:** qualify stdlib/declared packages; approve additions; classify JVM-only internals.

- **UI disposition:** Infrastructure only; no standalone UI component found in this library allocation. Its owned backend consumer feeds Debug Console through the phase integration gate; do not invent a library screen or direct plugin route.

## 3. File Changes

- **Modify:** `app/host/resources/files.py` (proposed earlier in FEAT-HOST-COMMONS-BEANUTILS)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/host/resources/encoding.py` (proposed earlier in FEAT-HOST-COMMONS-BEANUTILS)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/host/resources/README.md` (proposed earlier in FEAT-HOST-COMMONS-BEANUTILS)
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_host_commons_io.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/host_commons_io.json`
  - Store versioned paraphrased donor input/output fixtures.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Own consumed file/path/stream operations through host resources; verify encoding, path containment, interrupted write and closed handle.
- [ ] **Step 4:** `FR-HOST-COMMONS-IO-BYTE-ORDER-MARK-CONTRACT` → `org.apache.commons.io.ByteOrderMark`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-HOST-COMMONS-IO-BYTE-ORDER-MARK-GET-CHARSET-NAME` → `org.apache.commons.io.ByteOrderMark.getCharsetName`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** `FR-HOST-COMMONS-IO-BYTE-ORDER-MARK-LENGTH` → `org.apache.commons.io.ByteOrderMark.length`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 7:** Wire qualified adapters to consumers; release resources on failure/shutdown.
- [ ] **Step 8:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 9:** Verify UI-facing consumer contract: Test this infrastructure through its declared backend/host consumer; expose failures through the owning domain envelope. The phase's connected UI gate verifies the observable workflow.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_host_commons_io.py --no-cov`; expect encoding, path containment, interrupted write and closed handle; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture encoding, path containment, interrupted write and closed handle and visible failures.

# 1.7 FEAT-HOST-COMMONS-LANG3 - commons-lang3.jar

## 1. Objective

- **Goal:** Adapt consumed collection, string and utility contracts through Python primitives.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Boot the host with validated settings, structured logging and diagnostics.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/libs/commons-lang3.jar`; 260 class declarations; SHA-256 `8ac96fc686512d777fca85e144f196cd7cfe0c0aec23127229497d1a38ff651c`.
- **Inspected reference:** No dedicated docs/sqx coverage; expand archive inspection; roadmap allocation `FEAT-HOST-COMMONS-LANG3`.
- **Owner:** `app/host/resources/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Common utility dependencies; use standard/library adapters for verified consumed functions; downstream P02–P18.
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/libs/commons-lang3.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/libs/commons-lang3.jar" org.apache.commons.lang3.AnnotationUtils`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Dependency:** qualify stdlib/declared packages; approve additions; classify JVM-only internals.

- **UI disposition:** Infrastructure only; no standalone UI component found in this library allocation. Its owned backend consumer feeds Debug Console through the phase integration gate; do not invent a library screen or direct plugin route.

## 3. File Changes

- **Modify:** `app/host/resources/files.py` (proposed earlier in FEAT-HOST-COMMONS-BEANUTILS)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/host/resources/encoding.py` (proposed earlier in FEAT-HOST-COMMONS-BEANUTILS)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/host/resources/README.md` (proposed earlier in FEAT-HOST-COMMONS-BEANUTILS)
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_host_commons_lang3.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/host_commons_lang3.json`
  - Store versioned paraphrased donor input/output fixtures.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Adapt consumed collection, string and utility contracts through Python primitives; verify ordering, duplicate/null handling and bounded collection behavior.
- [ ] **Step 4:** `FR-HOST-COMMONS-LANG3-ANNOTATION-UTILS-CONTRACT` → `org.apache.commons.lang3.AnnotationUtils`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-HOST-COMMONS-LANG3-ANNOTATION-UTILS-IS-VALID-ANNOTATION-MEMBER-TYPE` → `org.apache.commons.lang3.AnnotationUtils.isValidAnnotationMemberType`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** Wire qualified adapters to consumers; release resources on failure/shutdown.
- [ ] **Step 7:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 8:** Verify UI-facing consumer contract: Test this infrastructure through its declared backend/host consumer; expose failures through the owning domain envelope. The phase's connected UI gate verifies the observable workflow.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_host_commons_lang3.py --no-cov`; expect ordering, duplicate/null handling and bounded collection behavior; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture ordering, duplicate/null handling and bounded collection behavior and visible failures.

# 1.8 FEAT-HOST-COMMONS-LOGGING - commons-logging.jar

## 1. Objective

- **Goal:** Route named loggers and severity through host-owned structured logging.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Boot the host with validated settings, structured logging and diagnostics.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/libs/commons-logging.jar`; 28 class declarations; SHA-256 `70903f6fc82e9908c8da9f20443f61d90f0870a312642991fe8462a0b9391784`.
- **Inspected reference:** No dedicated docs/sqx coverage; expand archive inspection; roadmap allocation `FEAT-HOST-COMMONS-LOGGING`.
- **Owner:** `app/host/logging/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Logging API, binding, sinks and interoperability; downstream P02–P18.
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/libs/commons-logging.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/libs/commons-logging.jar" org.apache.commons.logging.Log`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Dependency:** qualify stdlib/declared packages; approve additions; classify JVM-only internals.

- **UI disposition:** Infrastructure only; no standalone UI component found in this library allocation. Its owned backend consumer feeds Debug Console through the phase integration gate; do not invent a library screen or direct plugin route.

## 3. File Changes

- **Create:** `app/host/logging/setup.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/host/logging/sinks.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/host/logging/redaction.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/host/logging/README.md`
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_host_commons_logging.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/host_commons_logging.json`
  - Store versioned paraphrased donor input/output fixtures.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Route named loggers and severity through host-owned structured logging; verify logger identity, level filtering and exception/redaction projection.
- [ ] **Step 4:** `FR-HOST-COMMONS-LOGGING-LOG-CONTRACT` → `org.apache.commons.logging.Log`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-HOST-COMMONS-LOGGING-LOG-IS-DEBUG-ENABLED` → `org.apache.commons.logging.Log.isDebugEnabled`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** `FR-HOST-COMMONS-LOGGING-LOG-IS-ERROR-ENABLED` → `org.apache.commons.logging.Log.isErrorEnabled`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 7:** Wire qualified adapters to consumers; release resources on failure/shutdown.
- [ ] **Step 8:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 9:** Verify UI-facing consumer contract: Test this infrastructure through its declared backend/host consumer; expose failures through the owning domain envelope. The phase's connected UI gate verifies the observable workflow.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_host_commons_logging.py --no-cov`; expect logger identity, level filtering and exception/redaction projection; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture logger identity, level filtering and exception/redaction projection and visible failures.

# 1.9 FEAT-HOST-GUAVA - guava.jar

## 1. Objective

- **Goal:** Adapt consumed collection, string and utility contracts through Python primitives.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Boot the host with validated settings, structured logging and diagnostics.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/libs/guava.jar`; 1951 class declarations; SHA-256 `a0e9cabad665bc20bcd2b01f108e5fc03f756e13aea80abaadb9f407033bea2c`.
- **Inspected reference:** No dedicated docs/sqx coverage; expand archive inspection; roadmap allocation `FEAT-HOST-GUAVA`.
- **Owner:** `app/host/resources/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Common utility dependencies; use standard/library adapters for verified consumed functions; downstream P02–P18.
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/libs/guava.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/libs/guava.jar" com.google.common.annotations.Beta`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Dependency:** qualify stdlib/declared packages; approve additions; classify JVM-only internals.

- **UI disposition:** Infrastructure only; no standalone UI component found in this library allocation. Its owned backend consumer feeds Debug Console through the phase integration gate; do not invent a library screen or direct plugin route.

## 3. File Changes

- **Modify:** `app/host/resources/files.py` (proposed earlier in FEAT-HOST-COMMONS-BEANUTILS)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/host/resources/encoding.py` (proposed earlier in FEAT-HOST-COMMONS-BEANUTILS)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/host/resources/README.md` (proposed earlier in FEAT-HOST-COMMONS-BEANUTILS)
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_host_guava.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/host_guava.json`
  - Store versioned paraphrased donor input/output fixtures.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Adapt consumed collection, string and utility contracts through Python primitives; verify ordering, duplicate/null handling and bounded collection behavior.
- [ ] **Step 4:** `FR-HOST-GUAVA-BETA-CONTRACT` → `com.google.common.annotations.Beta`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** Wire qualified adapters to consumers; release resources on failure/shutdown.
- [ ] **Step 6:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 7:** Verify UI-facing consumer contract: Test this infrastructure through its declared backend/host consumer; expose failures through the owning domain envelope. The phase's connected UI gate verifies the observable workflow.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_host_guava.py --no-cov`; expect ordering, duplicate/null handling and bounded collection behavior; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture ordering, duplicate/null handling and bounded collection behavior and visible failures.

# 1.10 FEAT-HOST-JNA-PLATFORM - jna-platform.jar

## 1. Objective

- **Goal:** Adapt consumed process/platform probes and placement through declared psutil/OS capabilities.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Boot the host with validated settings, structured logging and diagnostics.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/libs/jna-platform.jar`; 1282 class declarations; SHA-256 `474d7b88f6e97009b6ec1d98c3024dd95c23187c65dabfbc35331bcac3d173dd`.
- **Inspected reference:** No dedicated docs/sqx coverage; expand archive inspection; roadmap allocation `FEAT-HOST-JNA-PLATFORM`.
- **Owner:** `app/host/platform/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Platform/process diagnostics; donor-specific native calls require separate evidence; downstream P14,P16,P17.
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/libs/jna-platform.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/libs/jna-platform.jar" com.sun.jna.platform.DesktopWindow`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Dependency:** qualify stdlib/declared packages; approve additions; classify JVM-only internals.

- **UI disposition:** Infrastructure only; no standalone UI component found in this library allocation. Its owned backend consumer feeds Debug Console through the phase integration gate; do not invent a library screen or direct plugin route.

## 3. File Changes

- **Create:** `app/host/platform/processes.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/host/platform/diagnostics.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/host/platform/README.md`
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_host_jna_platform.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/host_jna_platform.json`
  - Store versioned paraphrased donor input/output fixtures.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Adapt consumed process/platform probes and placement through declared psutil/OS capabilities; verify unsupported probe, process lifetime and bounded sampling.
- [ ] **Step 4:** `FR-HOST-JNA-PLATFORM-DESKTOP-WINDOW-CONTRACT` → `com.sun.jna.platform.DesktopWindow`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-HOST-JNA-PLATFORM-DESKTOP-WINDOW-GET-HWND` → `com.sun.jna.platform.DesktopWindow.getHWND`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** `FR-HOST-JNA-PLATFORM-DESKTOP-WINDOW-GET-TITLE` → `com.sun.jna.platform.DesktopWindow.getTitle`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 7:** Wire qualified adapters to consumers; release resources on failure/shutdown.
- [ ] **Step 8:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 9:** Verify UI-facing consumer contract: Test this infrastructure through its declared backend/host consumer; expose failures through the owning domain envelope. The phase's connected UI gate verifies the observable workflow.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_host_jna_platform.py --no-cov`; expect unsupported probe, process lifetime and bounded sampling; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture unsupported probe, process lifetime and bounded sampling and visible failures.

# 1.11 FEAT-HOST-JNA - jna.jar

## 1. Objective

- **Goal:** Adapt consumed process/platform probes and placement through declared psutil/OS capabilities.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Boot the host with validated settings, structured logging and diagnostics.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/libs/jna.jar`; 125 class declarations; SHA-256 `66d4f819a062a51a1d5627bffc23fac55d1677f0e0a1feba144aabdd670a64bb`.
- **Inspected reference:** No dedicated docs/sqx coverage; expand archive inspection; roadmap allocation `FEAT-HOST-JNA`.
- **Owner:** `app/host/platform/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Platform/process diagnostics; donor-specific native calls require separate evidence; downstream P14,P16,P17.
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/libs/jna.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/libs/jna.jar" com.sun.jna.AltCallingConvention`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Dependency:** qualify stdlib/declared packages; approve additions; classify JVM-only internals.

- **UI disposition:** Infrastructure only; no standalone UI component found in this library allocation. Its owned backend consumer feeds Debug Console through the phase integration gate; do not invent a library screen or direct plugin route.

## 3. File Changes

- **Modify:** `app/host/platform/processes.py` (proposed earlier in FEAT-HOST-JNA-PLATFORM)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/host/platform/diagnostics.py` (proposed earlier in FEAT-HOST-JNA-PLATFORM)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/host/platform/README.md` (proposed earlier in FEAT-HOST-JNA-PLATFORM)
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_host_jna.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/host_jna.json`
  - Store versioned paraphrased donor input/output fixtures.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Adapt consumed process/platform probes and placement through declared psutil/OS capabilities; verify unsupported probe, process lifetime and bounded sampling.
- [ ] **Step 4:** `FR-HOST-JNA-ALT-CALLING-CONVENTION-CONTRACT` → `com.sun.jna.AltCallingConvention`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** Wire qualified adapters to consumers; release resources on failure/shutdown.
- [ ] **Step 6:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 7:** Verify UI-facing consumer contract: Test this infrastructure through its declared backend/host consumer; expose failures through the owning domain envelope. The phase's connected UI gate verifies the observable workflow.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_host_jna.py --no-cov`; expect unsupported probe, process lifetime and bounded sampling; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture unsupported probe, process lifetime and bounded sampling and visible failures.

# 1.12 FEAT-HOST-J-PROCESSES - jProcesses.jar

## 1. Objective

- **Goal:** Adapt consumed process/platform probes and placement through declared psutil/OS capabilities.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Boot the host with validated settings, structured logging and diagnostics.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/libs/jProcesses.jar`; 12 class declarations; SHA-256 `57f61d01102f0e88e87c4a3cae6ccea3e5b390a38aeb3abd2ed20b06f25466ea`.
- **Inspected reference:** No dedicated docs/sqx coverage; expand archive inspection; roadmap allocation `FEAT-HOST-J-PROCESSES`.
- **Owner:** `app/host/platform/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Platform/process diagnostics; donor-specific native calls require separate evidence; downstream P14,P16,P17.
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/libs/jProcesses.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/libs/jProcesses.jar" org.jutils.jprocesses.JProcesses`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Dependency:** qualify stdlib/declared packages; approve additions; classify JVM-only internals.

- **UI disposition:** Infrastructure only; no standalone UI component found in this library allocation. Its owned backend consumer feeds Debug Console through the phase integration gate; do not invent a library screen or direct plugin route.

## 3. File Changes

- **Modify:** `app/host/platform/processes.py` (proposed earlier in FEAT-HOST-JNA-PLATFORM)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/host/platform/diagnostics.py` (proposed earlier in FEAT-HOST-JNA-PLATFORM)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/host/platform/README.md` (proposed earlier in FEAT-HOST-JNA-PLATFORM)
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_host_j_processes.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/host_j_processes.json`
  - Store versioned paraphrased donor input/output fixtures.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Adapt consumed process/platform probes and placement through declared psutil/OS capabilities; verify unsupported probe, process lifetime and bounded sampling.
- [ ] **Step 4:** `FR-HOST-J-PROCESSES-J-PROCESSES-CONTRACT` → `org.jutils.jprocesses.JProcesses`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-HOST-J-PROCESSES-J-PROCESSES-GET` → `org.jutils.jprocesses.JProcesses.get`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** `FR-HOST-J-PROCESSES-J-PROCESSES-FAST-MODE` → `org.jutils.jprocesses.JProcesses.fastMode`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 7:** Wire qualified adapters to consumers; release resources on failure/shutdown.
- [ ] **Step 8:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 9:** Verify UI-facing consumer contract: Test this infrastructure through its declared backend/host consumer; expose failures through the owning domain envelope. The phase's connected UI gate verifies the observable workflow.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_host_j_processes.py --no-cov`; expect unsupported probe, process lifetime and bounded sampling; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture unsupported probe, process lifetime and bounded sampling and visible failures.

# 1.13 FEAT-HOST-LOGBACK-CLASSIC - logback-classic.jar

## 1. Objective

- **Goal:** Configure logger hierarchy and diagnostic context.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Boot the host with validated settings, structured logging and diagnostics.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/libs/logback-classic.jar`; 173 class declarations; SHA-256 `b4ecaf8bd993f5df004e44cd7869af6184342db51fccf3c2e03757b8e1d3f149`.
- **Inspected reference:** No dedicated docs/sqx coverage; expand archive inspection; roadmap allocation `FEAT-HOST-LOGBACK-CLASSIC`.
- **Owner:** `app/host/logging/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Logging API, binding, sinks and interoperability; downstream P02–P18.
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/libs/logback-classic.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/libs/logback-classic.jar" ch.qos.logback.classic.Logger`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Dependency:** qualify stdlib/declared packages; approve additions; classify JVM-only internals.

- **UI disposition:** Infrastructure only; no standalone UI component found in this library allocation. Its owned backend consumer feeds Debug Console through the phase integration gate; do not invent a library screen or direct plugin route.

## 3. File Changes

- **Modify:** `app/host/logging/setup.py` (proposed earlier in FEAT-HOST-COMMONS-LOGGING)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/host/logging/sinks.py` (proposed earlier in FEAT-HOST-COMMONS-LOGGING)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/host/logging/redaction.py` (proposed earlier in FEAT-HOST-COMMONS-LOGGING)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/host/logging/README.md` (proposed earlier in FEAT-HOST-COMMONS-LOGGING)
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_host_logback_classic.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/host_logback_classic.json`
  - Store versioned paraphrased donor input/output fixtures.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Configure logger hierarchy and diagnostic context; verify inheritance, context isolation and sanitized exception records.
- [ ] **Step 4:** `FR-HOST-LOGBACK-CLASSIC-LOGGER-CONTRACT` → `ch.qos.logback.classic.Logger`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-HOST-LOGBACK-CLASSIC-LOGGER-GET-EFFECTIVE-LEVEL` → `ch.qos.logback.classic.Logger.getEffectiveLevel`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** `FR-HOST-LOGBACK-CLASSIC-LOGGER-GET-LEVEL` → `ch.qos.logback.classic.Logger.getLevel`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 7:** Wire qualified adapters to consumers; release resources on failure/shutdown.
- [ ] **Step 8:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 9:** Verify UI-facing consumer contract: Test this infrastructure through its declared backend/host consumer; expose failures through the owning domain envelope. The phase's connected UI gate verifies the observable workflow.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_host_logback_classic.py --no-cov`; expect inheritance, context isolation and sanitized exception records; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture inheritance, context isolation and sanitized exception records and visible failures.

# 1.14 FEAT-HOST-LOGBACK-CORE - logback-core.jar

## 1. Objective

- **Goal:** Own logging sink configuration, buffering, rotation and cleanup.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Boot the host with validated settings, structured logging and diagnostics.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/libs/logback-core.jar`; 355 class declarations; SHA-256 `0252340d20a44cf2c49ed3fecd16cdf4582442981c6f6e11cbf0b84a4ece1f10`.
- **Inspected reference:** No dedicated docs/sqx coverage; expand archive inspection; roadmap allocation `FEAT-HOST-LOGBACK-CORE`.
- **Owner:** `app/host/logging/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Logging API, binding, sinks and interoperability; downstream P02–P18.
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/libs/logback-core.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/libs/logback-core.jar" ch.qos.logback.core.Appender`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Dependency:** qualify stdlib/declared packages; approve additions; classify JVM-only internals.

- **UI disposition:** Infrastructure only; no standalone UI component found in this library allocation. Its owned backend consumer feeds Debug Console through the phase integration gate; do not invent a library screen or direct plugin route.

## 3. File Changes

- **Modify:** `app/host/logging/setup.py` (proposed earlier in FEAT-HOST-COMMONS-LOGGING)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/host/logging/sinks.py` (proposed earlier in FEAT-HOST-COMMONS-LOGGING)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/host/logging/redaction.py` (proposed earlier in FEAT-HOST-COMMONS-LOGGING)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/host/logging/README.md` (proposed earlier in FEAT-HOST-COMMONS-LOGGING)
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_host_logback_core.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/host_logback_core.json`
  - Store versioned paraphrased donor input/output fixtures.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Own logging sink configuration, buffering, rotation and cleanup; verify sink failure, rotation limits, flush ordering and shutdown.
- [ ] **Step 4:** `FR-HOST-LOGBACK-CORE-APPENDER-CONTRACT` → `ch.qos.logback.core.Appender`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-HOST-LOGBACK-CORE-APPENDER-DO-APPEND` → `ch.qos.logback.core.Appender.doAppend`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** `FR-HOST-LOGBACK-CORE-APPENDER-SET-NAME` → `ch.qos.logback.core.Appender.setName`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 7:** Wire qualified adapters to consumers; release resources on failure/shutdown.
- [ ] **Step 8:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 9:** Verify UI-facing consumer contract: Test this infrastructure through its declared backend/host consumer; expose failures through the owning domain envelope. The phase's connected UI gate verifies the observable workflow.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_host_logback_core.py --no-cov`; expect sink failure, rotation limits, flush ordering and shutdown; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture sink failure, rotation limits, flush ordering and shutdown and visible failures.

# 1.15 FEAT-HOST-OSHI-CORE - oshi-core.jar

## 1. Objective

- **Goal:** Adapt consumed process/platform probes and placement through declared psutil/OS capabilities.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Boot the host with validated settings, structured logging and diagnostics.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/libs/oshi-core.jar`; 569 class declarations; SHA-256 `59c4bde18e4c19a29d2b996cb7a018da2f8d2b1f39cb0d73a78855c0673cc94f`.
- **Inspected reference:** No dedicated docs/sqx coverage; expand archive inspection; roadmap allocation `FEAT-HOST-OSHI-CORE`.
- **Owner:** `app/host/platform/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Platform/process diagnostics; donor-specific native calls require separate evidence; downstream P14,P16,P17.
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/libs/oshi-core.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/libs/oshi-core.jar" oshi.PlatformEnum`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Dependency:** qualify stdlib/declared packages; approve additions; classify JVM-only internals.

- **UI disposition:** Infrastructure only; no standalone UI component found in this library allocation. Its owned backend consumer feeds Debug Console through the phase integration gate; do not invent a library screen or direct plugin route.

## 3. File Changes

- **Modify:** `app/host/platform/processes.py` (proposed earlier in FEAT-HOST-JNA-PLATFORM)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/host/platform/diagnostics.py` (proposed earlier in FEAT-HOST-JNA-PLATFORM)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/host/platform/README.md` (proposed earlier in FEAT-HOST-JNA-PLATFORM)
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_host_oshi_core.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/host_oshi_core.json`
  - Store versioned paraphrased donor input/output fixtures.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Adapt consumed process/platform probes and placement through declared psutil/OS capabilities; verify unsupported probe, process lifetime and bounded sampling.
- [ ] **Step 4:** `FR-HOST-OSHI-CORE-PLATFORM-ENUM-CONTRACT` → `oshi.PlatformEnum`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-HOST-OSHI-CORE-PLATFORM-ENUM-VALUES` → `oshi.PlatformEnum.values`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** `FR-HOST-OSHI-CORE-PLATFORM-ENUM-VALUE-OF` → `oshi.PlatformEnum.valueOf`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 7:** Wire qualified adapters to consumers; release resources on failure/shutdown.
- [ ] **Step 8:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 9:** Verify UI-facing consumer contract: Test this infrastructure through its declared backend/host consumer; expose failures through the owning domain envelope. The phase's connected UI gate verifies the observable workflow.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_host_oshi_core.py --no-cov`; expect unsupported probe, process lifetime and bounded sampling; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture unsupported probe, process lifetime and bounded sampling and visible failures.

# 1.16 FEAT-HOST-PS-UTILS - PSUtils.jar

## 1. Objective

- **Goal:** Adapt consumed process/platform probes and placement through declared psutil/OS capabilities.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Boot the host with validated settings, structured logging and diagnostics.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/libs/PSUtils.jar`; 1 class declarations; SHA-256 `03ebfabefe9cb716e29757e64bd020bb78cfa0cb5d6088d622c16a5dc3e35da5`.
- **Inspected reference:** No dedicated docs/sqx coverage; expand archive inspection; roadmap allocation `FEAT-HOST-PS-UTILS`.
- **Owner:** `app/host/platform/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Platform/process diagnostics; donor-specific native calls require separate evidence; downstream P14,P16,P17.
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/libs/PSUtils.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/libs/PSUtils.jar" com.jfx.ts.io.PSUtils`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Dependency:** qualify stdlib/declared packages; approve additions; classify JVM-only internals.

- **UI disposition:** Infrastructure only; no standalone UI component found in this library allocation. Its owned backend consumer feeds Debug Console through the phase integration gate; do not invent a library screen or direct plugin route.

## 3. File Changes

- **Modify:** `app/host/platform/processes.py` (proposed earlier in FEAT-HOST-JNA-PLATFORM)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/host/platform/diagnostics.py` (proposed earlier in FEAT-HOST-JNA-PLATFORM)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/host/platform/README.md` (proposed earlier in FEAT-HOST-JNA-PLATFORM)
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_host_ps_utils.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/host_ps_utils.json`
  - Store versioned paraphrased donor input/output fixtures.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Adapt consumed process/platform probes and placement through declared psutil/OS capabilities; verify unsupported probe, process lifetime and bounded sampling.
- [ ] **Step 4:** `FR-HOST-PS-UTILS-PS-UTILS-CONTRACT` → `com.jfx.ts.io.PSUtils`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-HOST-PS-UTILS-PS-UTILS-GET-INSTANCE` → `com.jfx.ts.io.PSUtils.getInstance`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** `FR-HOST-PS-UTILS-PS-UTILS-DEINIT` → `com.jfx.ts.io.PSUtils.deinit`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 7:** Wire qualified adapters to consumers; release resources on failure/shutdown.
- [ ] **Step 8:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 9:** Verify UI-facing consumer contract: Test this infrastructure through its declared backend/host consumer; expose failures through the owning domain envelope. The phase's connected UI gate verifies the observable workflow.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_host_ps_utils.py --no-cov`; expect unsupported probe, process lifetime and bounded sampling; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture unsupported probe, process lifetime and bounded sampling and visible failures.

# 1.17 FEAT-HOST-SLF4J-API - slf4j-api.jar

## 1. Objective

- **Goal:** Route named loggers and severity through host-owned structured logging.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Boot the host with validated settings, structured logging and diagnostics.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/libs/slf4j-api.jar`; 24 class declarations; SHA-256 `3c5b5c3411e1cf2d1f44513d7280eb72180875cbb5d4c924bb378cf3b7968267`.
- **Inspected reference:** No dedicated docs/sqx coverage; expand archive inspection; roadmap allocation `FEAT-HOST-SLF4J-API`.
- **Owner:** `app/host/logging/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Logging API, binding, sinks and interoperability; downstream P02–P18.
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/libs/slf4j-api.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/libs/slf4j-api.jar" org.slf4j.Logger`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Dependency:** qualify stdlib/declared packages; approve additions; classify JVM-only internals.

- **UI disposition:** Infrastructure only; no standalone UI component found in this library allocation. Its owned backend consumer feeds Debug Console through the phase integration gate; do not invent a library screen or direct plugin route.

## 3. File Changes

- **Modify:** `app/host/logging/setup.py` (proposed earlier in FEAT-HOST-COMMONS-LOGGING)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/host/logging/sinks.py` (proposed earlier in FEAT-HOST-COMMONS-LOGGING)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/host/logging/redaction.py` (proposed earlier in FEAT-HOST-COMMONS-LOGGING)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/host/logging/README.md` (proposed earlier in FEAT-HOST-COMMONS-LOGGING)
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_host_slf4j_api.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/host_slf4j_api.json`
  - Store versioned paraphrased donor input/output fixtures.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Route named loggers and severity through host-owned structured logging; verify logger identity, level filtering and exception/redaction projection.
- [ ] **Step 4:** `FR-HOST-SLF4J-API-LOGGER-CONTRACT` → `org.slf4j.Logger`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-HOST-SLF4J-API-LOGGER-IS-TRACE-ENABLED` → `org.slf4j.Logger.isTraceEnabled`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** `FR-HOST-SLF4J-API-LOGGER-TRACE` → `org.slf4j.Logger.trace`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 7:** Wire qualified adapters to consumers; release resources on failure/shutdown.
- [ ] **Step 8:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 9:** Verify UI-facing consumer contract: Test this infrastructure through its declared backend/host consumer; expose failures through the owning domain envelope. The phase's connected UI gate verifies the observable workflow.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_host_slf4j_api.py --no-cov`; expect logger identity, level filtering and exception/redaction projection; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture logger identity, level filtering and exception/redaction projection and visible failures.

# 1.18 FEAT-HOST-APP-DEBUG-CONSOLE - AppDebugConsole.jar

## 1. Objective

- **Goal:** Mount the DebugConsole workspace against real backend capabilities.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Boot the host with validated settings, structured logging and diagnostics.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/plugins/AppDebugConsole/AppDebugConsole.jar`; 1 class declarations; SHA-256 `67385f439772238bec088a089cc88437dfd58d29fae8ae397fb1dbacfb34e1da`.
- **Inspected reference:** `HARUQUANTAI_ROOT/docs/sqx/DebugConsole/AppDebugConsole.md`; roadmap allocation `FEAT-HOST-APP-DEBUG-CONSOLE`.
- **Owner:** `app/workspace/DebugConsole/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Workspace/product registration and backend composition; downstream .
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/plugins/AppDebugConsole/AppDebugConsole.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/plugins/AppDebugConsole/AppDebugConsole.jar" com.strategyquant.plugin.App.impl.DebugConsole.DebugConsoleAppPlugin`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_REFERENCE_ROOT/internal/plugins/AppDebugConsole`; `SQX_REFERENCE_ROOT/internal/web/DEBUGCONSOLE`. Inspect `SQX_REFERENCE_ROOT/internal/plugins/AppDebugConsole/module.js`.
- **Existing UI connection:** Debug Console; proposed shared consumer; verify the exact existing control and public contract before implementation. Target `ui/app/workspace/DebugConsole/DebugConsoleWorkspace.tsx`; wire redacted backend diagnostics/log query and live log lifecycle.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Create:** `app/workspace/DebugConsole/workspace.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/workspace/DebugConsole/routes.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/workspace/DebugConsole/contracts.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/workspace/DebugConsole/README.md`
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_host_app_debug_console.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/host_app_debug_console.json`
  - Store versioned paraphrased donor input/output fixtures.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/workspace/DebugConsole/DebugConsoleWorkspace.tsx`
  - Display redacted backend diagnostics/log query and live log lifecycle from backend responses; preserve layout.
- **Create:** `ui/app/workspace/DebugConsole/debugConsoleClient.ts`
  - Typed domain client over host transport; ratify route/schema/version, errors and cancellation. Reuse this proposed owner if delivered earlier.
- **Create:** `ui/tests/unit/backend-connections/feat-host-app-debug-console.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-host-foundation-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Mount the DebugConsole workspace against real backend capabilities; verify discovery, workspace readiness, job/resource ownership and unmount cleanup.
- [ ] **Step 4:** `FR-HOST-APP-DEBUG-CONSOLE-DEBUG-CONSOLE-APP-PLUGIN-CONTRACT` → `com.strategyquant.plugin.App.impl.DebugConsole.DebugConsoleAppPlugin`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-HOST-APP-DEBUG-CONSOLE-DEBUG-CONSOLE-APP-PLUGIN-GET-PREFERRED-POSITION` → `com.strategyquant.plugin.App.impl.DebugConsole.DebugConsoleAppPlugin.getPreferredPosition`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** `FR-HOST-APP-DEBUG-CONSOLE-DEBUG-CONSOLE-APP-PLUGIN-INIT-PLUGIN` → `com.strategyquant.plugin.App.impl.DebugConsole.DebugConsoleAppPlugin.initPlugin`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 7:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 8:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 9:** Connect retained UI: Ratify the feature-owned wire contract; bind redacted backend diagnostics/log query and live log lifecycle to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 10:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.
- **UI prerequisite:** P02 host transport/session/envelope capability is a dependency; ratify prerequisite ordering and keep this UI task open until the connection can execute.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_host_app_debug_console.py --no-cov`; expect discovery, workspace readiness, job/resource ownership and unmount cleanup; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture discovery, workspace readiness, job/resource ownership and unmount cleanup and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-host-app-debug-console.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-host-foundation-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise Debug Console for FEAT-HOST-APP-DEBUG-CONSOLE; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.

# 1.19 FEAT-HOST-JRT-FS - jrt-fs.jar

## 1. Objective

- **Goal:** Deliver the consumed jrt-fs capability in host.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Boot the host with validated settings, structured logging and diagnostics.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/j64/lib/jrt-fs.jar`; 57 class declarations; SHA-256 `1db242eab55fb04e456d042ebc9b1c6192e5c755357567496d43b3c9da75a701`.
- **Inspected reference:** No dedicated docs/sqx coverage; expand archive inspection; roadmap allocation `FEAT-HOST-JRT-FS`.
- **Owner:** `app/host/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Bundled JVM filesystem support; replace with CPython/runtime packaging, not a Python class clone; downstream P01,P17.
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/j64/lib/jrt-fs.jar"`; inspect manifest/resources and target runtime requirements.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Dependency:** qualify stdlib/declared packages; approve additions; classify JVM-only internals.

- **UI disposition:** Infrastructure only; no standalone UI component found in this library allocation. Its owned backend consumer feeds Debug Console through the phase integration gate; do not invent a library screen or direct plugin route.

## 3. File Changes

- **Modify:** `pyproject.toml`
  - Verify the ratified Python/runtime support; no Java runtime translation.
- **Modify:** `app/host/README.md` (proposed earlier in P00)
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_host_jrt_fs.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/host_jrt_fs.json`
  - Store versioned paraphrased donor input/output fixtures.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Record every runtime-only class disposition; qualify Python 3.14+ startup/resource access and deployment support.
- [ ] **Step 4:** `FR-HOST-JRT-FS-RUNTIME-FILESYSTEM-SUPPORT` → `JVM runtime support; validate target runtime equivalent`: Verify runtime support; record non-port disposition.
- [ ] **Step 5:** Wire qualified adapters to consumers; release resources on failure/shutdown.
- [ ] **Step 6:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 7:** Verify UI-facing consumer contract: Test this infrastructure through its declared backend/host consumer; expose failures through the owning domain envelope. The phase's connected UI gate verifies the observable workflow.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_host_jrt_fs.py --no-cov`; expect fresh-process boot/shutdown, deterministic settings and sanitized logs; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture fresh-process boot/shutdown, deterministic settings and sanitized logs and visible failures.

# 1.20 P01 integration — Boot the host with validated settings, structured logging and diagnostics

## 1. Objective

- **Goal:** Boot the host with validated settings, structured logging and diagnostics.
- **Context / Problem Solved:** The existing UI needs a real end-to-end backend workflow, beyond isolated JAR adapters.

## 2. Research and donors

- **Roadmap:** `HARUQUANTAI_ROOT/docs/dev/sqx-full-application-roadmap.md`, P01; donor features and FRs are the tasks in this file.
- **Existing code:** `ui/app/workspace/DebugConsole/DebugConsoleWorkspace.tsx`; backend counterparts are proposed.
- **Declared dependencies:** FastAPI, Pydantic, Uvicorn, psutil; host persistence choice remains unratified.
- **Existing tests:** `ui/tests/unit/workspace/DebugConsole/debugConsole.test.ts`; extend actual-backend assertions.
- **Conflict/gap:** frontend existence does not establish functional backend behavior; route/schema/discovery changes need a task plan and approval.
- **Cross-feature ownership:** shared files may host multiple features; keep per-FR traces and delegate persistence/jobs to host capabilities.

- **UI donors:** `SQX_REFERENCE_ROOT/internal/web/DEBUGCONSOLE`. Inspect `SQX_REFERENCE_ROOT/internal/web/DEBUGCONSOLE/index.html`.
- **Existing UI connection:** Debug Console; proposed shared consumer; verify the exact existing control and public contract before implementation. Target `ui/app/workspace/DebugConsole/DebugConsoleWorkspace.tsx`; wire redacted backend diagnostics/log query and live log lifecycle.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Create:** `app/main.py`
  - Deliver the phase's typed contracts and integration flow; extend prior approved owners where shared.
- **Create:** `app/host/bootstrap.py`
  - Deliver the phase's typed contracts and integration flow; extend prior approved owners where shared.
- **Create:** `app/host/lifecycle.py`
  - Deliver the phase's typed contracts and integration flow; extend prior approved owners where shared.
- **Create:** `app/host/settings.py`
  - Deliver the phase's typed contracts and integration flow; extend prior approved owners where shared.
- **Create:** `app/host/paths.py`
  - Deliver the phase's typed contracts and integration flow; extend prior approved owners where shared.
- **Create:** `app/host/health.py`
  - Deliver the phase's typed contracts and integration flow; extend prior approved owners where shared.
- **Modify:** `ui/app/workspace/DebugConsole/DebugConsoleWorkspace.tsx`
  - Bind real capability state, errors and cancellation while preserving the existing layout.
- **Create:** `ui/app/workspace/DebugConsole/debugConsoleClient.ts`
  - Own typed routes/envelopes for this domain; replace mock execution with authoritative requests.
- **Modify:** `app/host/README.md` (proposed earlier in P00)
  - Own feature registration/status and phase contract decisions after ratification.
- **Create:** `tests/integration/test_host_foundation_workflow.py`
  - Exercise the real phase workflow in isolated stores with failure/cancellation assertions.
- **Create:** `ui/tests/e2e/sqx-host-foundation-backend.spec.ts`
  - Use an isolated real host to verify UI state and request/output reconciliation.

- **UI connection files (existing presentation):**
- **Create:** `ui/tests/unit/backend-connections/task-1-20.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Review preceding feature fixtures and owning README registrations; ratify the phase integration contracts and execution plan.
- [ ] **Step 2:** Define startup/shutdown states, settings precedence and resource-path authority.
- [ ] **Step 3:** Implement explicit log setup, redaction, bounded sinks and platform diagnostics.
- [ ] **Step 4:** Expose readiness and a sanitized debug-log projection through host capabilities.
- [ ] **Step 5:** Replace fixture-driven production execution in the affected workflow; retain deterministic fixtures only in tests.
- [ ] **Step 6:** Test positive/failure/cancellation paths and observable FR logs; reload/reconnect and reconcile persisted outputs.
- [ ] **Step 7:** Record exact commands, timestamped artifacts, unresolved gaps and walkthrough; obtain separate owner commit authority.

- [ ] **Step 8:** Connect retained UI: Ratify the feature-owned wire contract; bind redacted backend diagnostics/log query and live log lifecycle to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 9:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.
- **UI prerequisite:** P02 host transport/session/envelope capability is a dependency; ratify prerequisite ordering and keep this UI task open until the connection can execute.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/integration/test_host_foundation_workflow.py --no-cov`; `npm --prefix ui run test -- tests/unit/workspace/DebugConsole/debugConsole.test.ts`; `npm --prefix ui run test:ui -- tests/e2e/sqx-host-foundation-backend.spec.ts`. Assert fresh-process boot/shutdown, deterministic settings and sanitized logs; reject invalid configuration, failed log sink and unavailable platform probe.
- **Manual / Browser Verification:** Launch a fresh process; open DebugConsole; trigger a configuration error; confirm actionable redacted logs and clean exit.

- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/task-1-20.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-host-foundation-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise Debug Console for 1.20; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.

## Phase completion gate

- [ ] Every applicable feature passed its own isolated real-host UI/backend case; no production mock fallback or unresolved required UI remains.

- [ ] Reconcile all allocated FEAT/FR dispositions, donor fixtures and ownership gaps.
- [ ] Run Ruff format/check and strict Mypy on the approved changed Python paths; verify branch-aware coverage ≥80% across retained application source at release.
- [ ] For affected UI: `npm --prefix ui run typecheck`, `npm --prefix ui run test`, `npm --prefix ui run build`.
- [ ] Record real workflow observations, timestamps, failure artifacts and remaining gaps in the walkthrough.
- [ ] Obtain the next task/phase approval; commits and external/destructive actions retain separate owner gates.

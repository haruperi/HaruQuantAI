# P01 — Host bootstrap, logging, configuration and diagnostics

- **Source:** `HARUQUANTAI_ROOT/docs/dev/sqx-full-application-roadmap.md`; current-only source inventory `docs/dev/evidence/p00-inventory.json`.
- **Dependencies:** P00 (P00 prerequisites below).
- **State:** proposed checklists; all execution, registrations and target contracts require task-level approval.
- **File labels:** existing paths are Modify; absent paths are Create; later shared edits name their earlier proposed owner.
- **Execution standard:** AGENTS.md plan → approval → implementation → tests → walkthrough; canonical Python docstrings, typed public APIs and explicit FR logs.
- **Clean room:** donor signatures guide behavioral research; independently written implementations; no proprietary source in evidence; no parity claim without independent validation.
- **Verification:** commands below are future tasks, not reported passes; isolated stores only; no live-store schema change/restore or Git mutation.
- **UI completion:** Applicable features finish with backend + retained UI connected; preserve layouts. Production mocks cannot substitute for capability execution; keep a task unchecked while transport/contracts or required controls are unresolved.
- **Connected verification:** Use an isolated real host and temporary data. Existing mock-only/browser-API-blocking suites are UI regressions, not connected acceptance. Run `npm --prefix ui run typecheck`, `npm --prefix ui run test`, `npm --prefix ui run build` after actual UI source changes.



- **Donor baseline:** SQX145 Dev 1 only; all source fingerprints and member seeds use `SQX_145_REFERENCE_ROOT`. Missing bodies remain prerequisites.
- **Scope:** 38 tasks; current archive allocations and resource/integration tasks only.

# 1.1 P00 prerequisites — evidence, ownership and missing common core

## 1. Objective

- **Goal:** Qualify sole-cohort evidence, ownership and unavailable common-core prerequisites before host implementation.
- **Context / Problem Solved:** Reference tooling exists; structural completeness does not supply missing application bodies or runtime fixtures.

## 2. Research and donors

- **Donors:** `SQX_145_REFERENCE_ROOT/internal/libs`, `internal/plugins` and shipped static resources; [common-core gaps](../evidence/p00-common-core.md).
- **Authority:** `AGENTS.md`, `docs/PROJECT.md`, `docs/ARCHITECTURE.md`, `app/host/README.md`, current ledger/schema, inventory/member indices and target UI READMEs.
- **Gap:** 26 structural core-symbol references lack current standalone definitions; installed build/activation and donor runtime qualification remain unavailable.

## 3. File Changes

- **Modify:** `tests/reference/{manifest,fixtures,validate}.py` — existing evidence qualification tooling, not a runtime substitute.
- **Modify:** `docs/dev/evidence/{reimplementation.json,reimplementation.schema.json,p00-common-core.md,p00-release-matrix.md}` — fresh atomic observations and unresolved gates.
- **Modify:** `app/host/README.md` — existing evidence capability status and approved reference decisions.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Verify the current inventory/member/ownership gates and isolated static fixtures; inspect every unresolved current core caller.
- [ ] **Step 2:** Locate missing bodies using authorized current artifacts or applicable official sources; do not reconstruct unavailable formulas from declarations.
- [ ] **Step 3:** Ratify owning features/descriptive FRs/decisions before application implementation; allocate new atomic current-source evidence IDs.
- [ ] **Step 4:** Obtain independent normal/boundary/failure donor observations and distinguish static inspection from runtime qualification.
- [ ] **Step 5:** Keep this prerequisite unchecked until required common-core/runtime gates pass; update the master tracker after actual completion.

## 5. Verification & Testing

- **Automated Tests:** `uv run python -m tests.reference.validate`; explicit donor check with `--check-donor`; focused reference pytest, Ruff and strict Mypy.
- **Manual / Browser Verification:** Review unresolved core bodies and source/target ownership; no connected UI or runtime parity is qualified by P00 tooling.


# 1.2 FEAT-HOST-COMMONS-BEANUTILS - commons-beanutils-1.9.2.jar

## 1. Objective

- **Goal:** Replace consumed bean/property conversion with typed settings conversion.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Boot the host with validated settings, structured logging and diagnostics.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/libs/commons-beanutils-1.9.2.jar`; 137 raw class entries; SHA-256 `23729e3a2677ed5fb164ec999ba3fcdde3f8460e5ed086b6a43d8b5d46998d42`.
- **Inspected reference:** [commons-beanutils-1.9.2.md](../../sqx/Libraries/commons-beanutils-1.9.2.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/libs/commons-beanutils-1.9.2.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/libs/commons-beanutils-1.9.2.jar" org.apache.commons.beanutils.BaseDynaBeanMapDecorator`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/host/resources/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Common utility dependencies; use standard/library adapters for verified consumed functions; downstream P02–P18.
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
- [ ] **Step 4:** Wire qualified adapters to consumers; release resources on failure/shutdown.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Verify UI-facing consumer contract: Test this infrastructure through its declared backend/host consumer; expose failures through the owning domain envelope. The phase's connected UI gate verifies the observable workflow.


- [ ] **Step 7:** `FR-HOST-COMMONS-BEANUTILS-BASE-DYNA-BEAN-MAP-DECORATOR-CONTRACT` → `org.apache.commons.beanutils.BaseDynaBeanMapDecorator`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 8:** `FR-HOST-COMMONS-BEANUTILS-BASE-DYNA-BEAN-MAP-DECORATOR-IS-READ-ONLY` → `org.apache.commons.beanutils.BaseDynaBeanMapDecorator.isReadOnly()Z`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-HOST-COMMONS-BEANUTILS-BASE-DYNA-BEAN-MAP-DECORATOR-CLEAR` → `org.apache.commons.beanutils.BaseDynaBeanMapDecorator.clear()V`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_host_commons_beanutils.py --no-cov`; expect coercion, missing properties and rejected unknown fields; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture coercion, missing properties and rejected unknown fields and visible failures.


# 1.3 FEAT-HOST-COMMONS-CODEC - commons-codec-1.17.1.jar

## 1. Objective

- **Goal:** Provide only consumed encoding, decoding and digest operations.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Boot the host with validated settings, structured logging and diagnostics.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/libs/commons-codec-1.17.1.jar`; 115 raw class entries; SHA-256 `f9f6cb103f2ddc3c99a9d80ada2ae7bf0685111fd6bffccb72033d1da4e6ff23`.
- **Inspected reference:** [commons-codec-1.17.1.md](../../sqx/Libraries/commons-codec-1.17.1.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/libs/commons-codec-1.17.1.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/libs/commons-codec-1.17.1.jar" org.apache.commons.codec.BinaryDecoder`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/host/resources/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Common utility dependencies; use standard/library adapters for verified consumed functions; downstream P02–P18.
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
- [ ] **Step 4:** Wire qualified adapters to consumers; release resources on failure/shutdown.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Verify UI-facing consumer contract: Test this infrastructure through its declared backend/host consumer; expose failures through the owning domain envelope. The phase's connected UI gate verifies the observable workflow.


- [ ] **Step 7:** `FR-HOST-COMMONS-CODEC-BINARY-DECODER-CONTRACT` → `org.apache.commons.codec.BinaryDecoder`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 8:** `FR-HOST-COMMONS-CODEC-BINARY-DECODER-DECODE` → `org.apache.commons.codec.BinaryDecoder.decode([B)[B`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_host_commons_codec.py --no-cov`; expect encoding vectors, malformed input and byte/text boundary; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture encoding vectors, malformed input and byte/text boundary and visible failures.


# 1.4 FEAT-HOST-COMMONS-COLLECTIONS - commons-collections-3.2.1.jar

## 1. Objective

- **Goal:** Adapt consumed collection, string and utility contracts through Python primitives.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Boot the host with validated settings, structured logging and diagnostics.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/libs/commons-collections-3.2.1.jar`; 458 raw class entries; SHA-256 `87363a4c94eaabeefd8b930cb059f66b64c9f7d632862f23de3012da7660047b`.
- **Inspected reference:** [commons-collections-3.2.1.md](../../sqx/Libraries/commons-collections-3.2.1.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/libs/commons-collections-3.2.1.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/libs/commons-collections-3.2.1.jar" org.apache.commons.collections.ArrayStack`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/host/resources/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Common utility dependencies; use standard/library adapters for verified consumed functions; downstream P02–P18.
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
- [ ] **Step 4:** Wire qualified adapters to consumers; release resources on failure/shutdown.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Verify UI-facing consumer contract: Test this infrastructure through its declared backend/host consumer; expose failures through the owning domain envelope. The phase's connected UI gate verifies the observable workflow.


- [ ] **Step 7:** `FR-HOST-COMMONS-COLLECTIONS-ARRAY-STACK-CONTRACT` → `org.apache.commons.collections.ArrayStack`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 8:** `FR-HOST-COMMONS-COLLECTIONS-ARRAY-STACK-EMPTY` → `org.apache.commons.collections.ArrayStack.empty()Z`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-HOST-COMMONS-COLLECTIONS-ARRAY-STACK-PEEK` → `org.apache.commons.collections.ArrayStack.peek()Ljava/lang/Object;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_host_commons_collections.py --no-cov`; expect ordering, duplicate/null handling and bounded collection behavior; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture ordering, duplicate/null handling and bounded collection behavior and visible failures.


# 1.5 FEAT-HOST-COMMONS-IO - commons-io-2.16.1.jar

## 1. Objective

- **Goal:** Own consumed file/path/stream operations through host resources.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Boot the host with validated settings, structured logging and diagnostics.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/libs/commons-io-2.16.1.jar`; 347 raw class entries; SHA-256 `f41f7baacd716896447ace9758621f62c1c6b0a91d89acee488da26fc477c84f`.
- **Inspected reference:** [commons-io-2.16.1.md](../../sqx/Libraries/commons-io-2.16.1.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/libs/commons-io-2.16.1.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/libs/commons-io-2.16.1.jar" org.apache.commons.io.ByteOrderMark`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/host/resources/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Common utility dependencies; use standard/library adapters for verified consumed functions; downstream P02–P18.
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
- [ ] **Step 4:** Wire qualified adapters to consumers; release resources on failure/shutdown.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Verify UI-facing consumer contract: Test this infrastructure through its declared backend/host consumer; expose failures through the owning domain envelope. The phase's connected UI gate verifies the observable workflow.


- [ ] **Step 7:** `FR-HOST-COMMONS-IO-BYTE-ORDER-MARK-CONTRACT` → `org.apache.commons.io.ByteOrderMark`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 8:** `FR-HOST-COMMONS-IO-BYTE-ORDER-MARK-EQUALS` → `org.apache.commons.io.ByteOrderMark.equals(Ljava/lang/Object;)Z`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-HOST-COMMONS-IO-BYTE-ORDER-MARK-GET` → `org.apache.commons.io.ByteOrderMark.get(I)I`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_host_commons_io.py --no-cov`; expect encoding, path containment, interrupted write and closed handle; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture encoding, path containment, interrupted write and closed handle and visible failures.


# 1.6 FEAT-HOST-COMMONS-LANG3 - commons-lang3-3.16.0.jar

## 1. Objective

- **Goal:** Adapt consumed collection, string and utility contracts through Python primitives.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Boot the host with validated settings, structured logging and diagnostics.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/libs/commons-lang3-3.16.0.jar`; 396 raw class entries; SHA-256 `08709dd74d602b705ce4017d26544210056a4ba583d5b20c09373406fe7a00f8`.
- **Inspected reference:** [commons-lang3-3.16.0.md](../../sqx/Libraries/commons-lang3-3.16.0.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/libs/commons-lang3-3.16.0.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/libs/commons-lang3-3.16.0.jar" org.apache.commons.lang3.AnnotationUtils`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/host/resources/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Common utility dependencies; use standard/library adapters for verified consumed functions; downstream P02–P18.
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
- [ ] **Step 4:** Wire qualified adapters to consumers; release resources on failure/shutdown.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Verify UI-facing consumer contract: Test this infrastructure through its declared backend/host consumer; expose failures through the owning domain envelope. The phase's connected UI gate verifies the observable workflow.


- [ ] **Step 7:** `FR-HOST-COMMONS-LANG3-ANNOTATION-UTILS-CONTRACT` → `org.apache.commons.lang3.AnnotationUtils`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 8:** `FR-HOST-COMMONS-LANG3-ANNOTATION-UTILS-ANNOTATION-ARRAY-MEMBER-EQUALS` → `org.apache.commons.lang3.AnnotationUtils.annotationArrayMemberEquals([Ljava/lang/annotation/Annotation;[Ljava/lang/annotation/Annotation;)Z`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-HOST-COMMONS-LANG3-ANNOTATION-UTILS-ARRAY-MEMBER-EQUALS` → `org.apache.commons.lang3.AnnotationUtils.arrayMemberEquals(Ljava/lang/Class;Ljava/lang/Object;Ljava/lang/Object;)Z`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_host_commons_lang3.py --no-cov`; expect ordering, duplicate/null handling and bounded collection behavior; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture ordering, duplicate/null handling and bounded collection behavior and visible failures.


# 1.7 FEAT-HOST-COMMONS-LOGGING - commons-logging-1.2.jar

## 1. Objective

- **Goal:** Route named loggers and severity through host-owned structured logging.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Boot the host with validated settings, structured logging and diagnostics.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/libs/commons-logging-1.2.jar`; 28 raw class entries; SHA-256 `daddea1ea0be0f56978ab3006b8ac92834afeefbd9b7e4e6316fca57df0fa636`.
- **Inspected reference:** [commons-logging-1.2.md](../../sqx/Libraries/commons-logging-1.2.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/libs/commons-logging-1.2.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/libs/commons-logging-1.2.jar" org.apache.commons.logging.Log`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/host/logging/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Logging API, binding, sinks and interoperability; downstream P02–P18.
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
- [ ] **Step 4:** Wire qualified adapters to consumers; release resources on failure/shutdown.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Verify UI-facing consumer contract: Test this infrastructure through its declared backend/host consumer; expose failures through the owning domain envelope. The phase's connected UI gate verifies the observable workflow.


- [ ] **Step 7:** `FR-HOST-COMMONS-LOGGING-LOG-CONTRACT` → `org.apache.commons.logging.Log`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 8:** `FR-HOST-COMMONS-LOGGING-LOG-DEBUG` → `org.apache.commons.logging.Log.debug(Ljava/lang/Object;)V`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-HOST-COMMONS-LOGGING-LOG-DEBUG-75F89DD0` → `org.apache.commons.logging.Log.debug(Ljava/lang/Object;Ljava/lang/Throwable;)V`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_host_commons_logging.py --no-cov`; expect logger identity, level filtering and exception/redaction projection; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture logger identity, level filtering and exception/redaction projection and visible failures.


# 1.8 FEAT-HOST-GUAVA - guava-26.0-jre.jar

## 1. Objective

- **Goal:** Adapt consumed collection, string and utility contracts through Python primitives.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Boot the host with validated settings, structured logging and diagnostics.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/libs/guava-26.0-jre.jar`; 1951 raw class entries; SHA-256 `a0e9cabad665bc20bcd2b01f108e5fc03f756e13aea80abaadb9f407033bea2c`.
- **Inspected reference:** [guava-26.0-jre.md](../../sqx/Libraries/guava-26.0-jre.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/libs/guava-26.0-jre.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/libs/guava-26.0-jre.jar" com.google.common.annotations.Beta`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/host/resources/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Common utility dependencies; use standard/library adapters for verified consumed functions; downstream P02–P18.
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
- [ ] **Step 4:** Wire qualified adapters to consumers; release resources on failure/shutdown.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Verify UI-facing consumer contract: Test this infrastructure through its declared backend/host consumer; expose failures through the owning domain envelope. The phase's connected UI gate verifies the observable workflow.


- [ ] **Step 7:** `FR-HOST-GUAVA-BETA-CONTRACT` → `com.google.common.annotations.Beta`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_host_guava.py --no-cov`; expect ordering, duplicate/null handling and bounded collection behavior; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture ordering, duplicate/null handling and bounded collection behavior and visible failures.


# 1.9 FEAT-HOST-JNA-PLATFORM - jna-platform-5.13.0.jar

## 1. Objective

- **Goal:** Adapt consumed process/platform probes and placement through declared psutil/OS capabilities.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Boot the host with validated settings, structured logging and diagnostics.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/libs/jna-platform-5.13.0.jar`; 1282 raw class entries; SHA-256 `474d7b88f6e97009b6ec1d98c3024dd95c23187c65dabfbc35331bcac3d173dd`.
- **Inspected reference:** [jna-platform-5.13.0.md](../../sqx/Libraries/jna-platform-5.13.0.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/libs/jna-platform-5.13.0.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/libs/jna-platform-5.13.0.jar" com.sun.jna.platform.DesktopWindow`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/host/platform/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Platform/process diagnostics; donor-specific native calls require separate evidence; downstream P14,P16,P17.
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
- [ ] **Step 4:** Wire qualified adapters to consumers; release resources on failure/shutdown.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Verify UI-facing consumer contract: Test this infrastructure through its declared backend/host consumer; expose failures through the owning domain envelope. The phase's connected UI gate verifies the observable workflow.


- [ ] **Step 7:** `FR-HOST-JNA-PLATFORM-DESKTOP-WINDOW-CONTRACT` → `com.sun.jna.platform.DesktopWindow`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 8:** `FR-HOST-JNA-PLATFORM-DESKTOP-WINDOW-GET-HWND` → `com.sun.jna.platform.DesktopWindow.getHWND()Lcom/sun/jna/platform/win32/WinDef$HWND;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-HOST-JNA-PLATFORM-DESKTOP-WINDOW-GET-TITLE` → `com.sun.jna.platform.DesktopWindow.getTitle()Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_host_jna_platform.py --no-cov`; expect unsupported probe, process lifetime and bounded sampling; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture unsupported probe, process lifetime and bounded sampling and visible failures.


# 1.10 FEAT-HOST-JNA - jna-5.13.0.jar

## 1. Objective

- **Goal:** Adapt consumed process/platform probes and placement through declared psutil/OS capabilities.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Boot the host with validated settings, structured logging and diagnostics.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/libs/jna-5.13.0.jar`; 125 raw class entries; SHA-256 `66d4f819a062a51a1d5627bffc23fac55d1677f0e0a1feba144aabdd670a64bb`.
- **Inspected reference:** [jna-5.13.0.md](../../sqx/Libraries/jna-5.13.0.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/libs/jna-5.13.0.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/libs/jna-5.13.0.jar" com.sun.jna.AltCallingConvention`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/host/platform/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Platform/process diagnostics; donor-specific native calls require separate evidence; downstream P14,P16,P17.
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
- [ ] **Step 4:** Wire qualified adapters to consumers; release resources on failure/shutdown.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Verify UI-facing consumer contract: Test this infrastructure through its declared backend/host consumer; expose failures through the owning domain envelope. The phase's connected UI gate verifies the observable workflow.


- [ ] **Step 7:** `FR-HOST-JNA-ALT-CALLING-CONVENTION-CONTRACT` → `com.sun.jna.AltCallingConvention`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_host_jna.py --no-cov`; expect unsupported probe, process lifetime and bounded sampling; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture unsupported probe, process lifetime and bounded sampling and visible failures.


# 1.11 FEAT-HOST-J-PROCESSES - jProcesses-1.6.5.jar

## 1. Objective

- **Goal:** Adapt consumed process/platform probes and placement through declared psutil/OS capabilities.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Boot the host with validated settings, structured logging and diagnostics.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/libs/jProcesses-1.6.5.jar`; 12 raw class entries; SHA-256 `57f61d01102f0e88e87c4a3cae6ccea3e5b390a38aeb3abd2ed20b06f25466ea`.
- **Inspected reference:** [jProcesses-1.6.5.md](../../sqx/Libraries/jProcesses-1.6.5.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/libs/jProcesses-1.6.5.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/libs/jProcesses-1.6.5.jar" org.jutils.jprocesses.JProcesses`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/host/platform/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Platform/process diagnostics; donor-specific native calls require separate evidence; downstream P14,P16,P17.
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
- [ ] **Step 4:** Wire qualified adapters to consumers; release resources on failure/shutdown.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Verify UI-facing consumer contract: Test this infrastructure through its declared backend/host consumer; expose failures through the owning domain envelope. The phase's connected UI gate verifies the observable workflow.


- [ ] **Step 7:** `FR-HOST-J-PROCESSES-JPROCESSES-CONTRACT` → `org.jutils.jprocesses.JProcesses`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 8:** `FR-HOST-J-PROCESSES-JPROCESSES-GET` → `org.jutils.jprocesses.JProcesses.get()Lorg/jutils/jprocesses/JProcesses;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-HOST-J-PROCESSES-JPROCESSES-FAST-MODE` → `org.jutils.jprocesses.JProcesses.fastMode()Lorg/jutils/jprocesses/JProcesses;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_host_j_processes.py --no-cov`; expect unsupported probe, process lifetime and bounded sampling; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture unsupported probe, process lifetime and bounded sampling and visible failures.


# 1.12 FEAT-HOST-LOGBACK-CLASSIC - logback-classic-1.4.14.jar

## 1. Objective

- **Goal:** Configure logger hierarchy and diagnostic context.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Boot the host with validated settings, structured logging and diagnostics.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/libs/logback-classic-1.4.14.jar`; 178 raw class entries; SHA-256 `8e832f7263ca606ae36dabb2d8b24c2f43d82cf634e81dad9d1640fa6ee3c596`.
- **Inspected reference:** [logback-classic-1.4.14.md](../../sqx/Libraries/logback-classic-1.4.14.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/libs/logback-classic-1.4.14.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/libs/logback-classic-1.4.14.jar" ch.qos.logback.classic.Logger`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/host/logging/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Logging API, binding, sinks and interoperability; downstream P02–P18.
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
- [ ] **Step 4:** Wire qualified adapters to consumers; release resources on failure/shutdown.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Verify UI-facing consumer contract: Test this infrastructure through its declared backend/host consumer; expose failures through the owning domain envelope. The phase's connected UI gate verifies the observable workflow.


- [ ] **Step 7:** `FR-HOST-LOGBACK-CLASSIC-LOGGER-CONTRACT` → `ch.qos.logback.classic.Logger`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 8:** `FR-HOST-LOGBACK-CLASSIC-LOGGER-GET-EFFECTIVE-LEVEL` → `ch.qos.logback.classic.Logger.getEffectiveLevel()Lch/qos/logback/classic/Level;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-HOST-LOGBACK-CLASSIC-LOGGER-GET-EFFECTIVE-LEVEL-INT` → `ch.qos.logback.classic.Logger.getEffectiveLevelInt()I`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_host_logback_classic.py --no-cov`; expect inheritance, context isolation and sanitized exception records; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture inheritance, context isolation and sanitized exception records and visible failures.


# 1.13 FEAT-HOST-LOGBACK-CORE - logback-core-1.4.14.jar

## 1. Objective

- **Goal:** Own logging sink configuration, buffering, rotation and cleanup.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Boot the host with validated settings, structured logging and diagnostics.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/libs/logback-core-1.4.14.jar`; 454 raw class entries; SHA-256 `f8c2f05f42530b1852739507c1792f0080167850ed8f396444c6913d6617a293`.
- **Inspected reference:** [logback-core-1.4.14.md](../../sqx/Libraries/logback-core-1.4.14.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/libs/logback-core-1.4.14.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/libs/logback-core-1.4.14.jar" ch.qos.logback.core.Appender`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/host/logging/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Logging API, binding, sinks and interoperability; downstream P02–P18.
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
- [ ] **Step 4:** Wire qualified adapters to consumers; release resources on failure/shutdown.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Verify UI-facing consumer contract: Test this infrastructure through its declared backend/host consumer; expose failures through the owning domain envelope. The phase's connected UI gate verifies the observable workflow.


- [ ] **Step 7:** `FR-HOST-LOGBACK-CORE-APPENDER-CONTRACT` → `ch.qos.logback.core.Appender`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 8:** `FR-HOST-LOGBACK-CORE-APPENDER-GET-NAME` → `ch.qos.logback.core.Appender.getName()Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-HOST-LOGBACK-CORE-APPENDER-DO-APPEND` → `ch.qos.logback.core.Appender.doAppend(Ljava/lang/Object;)V`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_host_logback_core.py --no-cov`; expect sink failure, rotation limits, flush ordering and shutdown; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture sink failure, rotation limits, flush ordering and shutdown and visible failures.


# 1.14 FEAT-HOST-OSHI-CORE - oshi-core-5.8.5.jar

## 1. Objective

- **Goal:** Adapt consumed process/platform probes and placement through declared psutil/OS capabilities.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Boot the host with validated settings, structured logging and diagnostics.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/libs/oshi-core-5.8.5.jar`; 482 raw class entries; SHA-256 `fe16bd8836eecf3d152585c2151322273b68237d13f223e662e0db959dd13680`.
- **Inspected reference:** [oshi-core-5.8.5.md](../../sqx/Libraries/oshi-core-5.8.5.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/libs/oshi-core-5.8.5.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/libs/oshi-core-5.8.5.jar" oshi.PlatformEnum`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/host/platform/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Platform/process diagnostics; donor-specific native calls require separate evidence; downstream P14,P16,P17.
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
- [ ] **Step 4:** Wire qualified adapters to consumers; release resources on failure/shutdown.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Verify UI-facing consumer contract: Test this infrastructure through its declared backend/host consumer; expose failures through the owning domain envelope. The phase's connected UI gate verifies the observable workflow.


- [ ] **Step 7:** `FR-HOST-OSHI-CORE-PLATFORM-ENUM-CONTRACT` → `oshi.PlatformEnum`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 8:** `FR-HOST-OSHI-CORE-PLATFORM-ENUM-VALUES` → `oshi.PlatformEnum.values()[Loshi/PlatformEnum;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-HOST-OSHI-CORE-PLATFORM-ENUM-VALUE-OF` → `oshi.PlatformEnum.valueOf(Ljava/lang/String;)Loshi/PlatformEnum;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_host_oshi_core.py --no-cov`; expect unsupported probe, process lifetime and bounded sampling; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture unsupported probe, process lifetime and bounded sampling and visible failures.


# 1.15 FEAT-HOST-PS-UTILS - PSUtils.jar

## 1. Objective

- **Goal:** Adapt consumed process/platform probes and placement through declared psutil/OS capabilities.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Boot the host with validated settings, structured logging and diagnostics.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/libs/PSUtils.jar`; 1 raw class entries; SHA-256 `03ebfabefe9cb716e29757e64bd020bb78cfa0cb5d6088d622c16a5dc3e35da5`.
- **Inspected reference:** [PSUtils.md](../../sqx/Libraries/PSUtils.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/libs/PSUtils.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/libs/PSUtils.jar" com.jfx.ts.io.PSUtils`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/host/platform/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Platform/process diagnostics; donor-specific native calls require separate evidence; downstream P14,P16,P17.
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
- [ ] **Step 4:** Wire qualified adapters to consumers; release resources on failure/shutdown.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Verify UI-facing consumer contract: Test this infrastructure through its declared backend/host consumer; expose failures through the owning domain envelope. The phase's connected UI gate verifies the observable workflow.


- [ ] **Step 7:** `FR-HOST-PS-UTILS-PSUTILS-CONTRACT` → `com.jfx.ts.io.PSUtils`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 8:** `FR-HOST-PS-UTILS-PSUTILS-GET-INSTANCE` → `com.jfx.ts.io.PSUtils.getInstance()Lcom/jfx/ts/io/PSUtils;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-HOST-PS-UTILS-PSUTILS-INIT` → `com.jfx.ts.io.PSUtils.init()V`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_host_ps_utils.py --no-cov`; expect unsupported probe, process lifetime and bounded sampling; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture unsupported probe, process lifetime and bounded sampling and visible failures.


# 1.16 FEAT-HOST-SLF4J-API - slf4j-api-2.0.17.jar

## 1. Objective

- **Goal:** Route named loggers and severity through host-owned structured logging.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Boot the host with validated settings, structured logging and diagnostics.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/libs/slf4j-api-2.0.17.jar`; 56 raw class entries; SHA-256 `7b751d952061954d5abfed7181c1f645d336091b679891591d63329c622eb832`.
- **Inspected reference:** [slf4j-api-2.0.17.md](../../sqx/Libraries/slf4j-api-2.0.17.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/libs/slf4j-api-2.0.17.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/libs/slf4j-api-2.0.17.jar" org.slf4j.Logger`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/host/logging/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Logging API, binding, sinks and interoperability; downstream P02–P18.
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
- [ ] **Step 4:** Wire qualified adapters to consumers; release resources on failure/shutdown.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Verify UI-facing consumer contract: Test this infrastructure through its declared backend/host consumer; expose failures through the owning domain envelope. The phase's connected UI gate verifies the observable workflow.


- [ ] **Step 7:** `FR-HOST-SLF4J-API-LOGGER-CONTRACT` → `org.slf4j.Logger`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 8:** `FR-HOST-SLF4J-API-LOGGER-GET-NAME` → `org.slf4j.Logger.getName()Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-HOST-SLF4J-API-LOGGER-MAKE-LOGGING-EVENT-BUILDER` → `org.slf4j.Logger.makeLoggingEventBuilder(Lorg/slf4j/event/Level;)Lorg/slf4j/spi/LoggingEventBuilder;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_host_slf4j_api.py --no-cov`; expect logger identity, level filtering and exception/redaction projection; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture logger identity, level filtering and exception/redaction projection and visible failures.


# 1.17 FEAT-HOST-APP-DEBUG-CONSOLE - AppDebugConsole.jar

## 1. Objective

- **Goal:** Mount the DebugConsole workspace against real backend capabilities.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Boot the host with validated settings, structured logging and diagnostics.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/plugins/AppDebugConsole/AppDebugConsole.jar`; 1 raw class entries; SHA-256 `aaaf875f1a4897aa3ea0a415bdca4da672b166bd0ea117bad9f5276723330394`.
- **Inspected reference:** [AppDebugConsole.md](../../sqx/DebugConsole/AppDebugConsole.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/plugins/AppDebugConsole/AppDebugConsole.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/plugins/AppDebugConsole/AppDebugConsole.jar" com.strategyquant.plugin.App.impl.DebugConsole.DebugConsoleAppPlugin`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/workspace/DebugConsole/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Workspace/product registration and backend composition; downstream .
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/plugins/AppDebugConsole`; `SQX_145_REFERENCE_ROOT/internal/web/DEBUGCONSOLE`. Inspect `SQX_145_REFERENCE_ROOT/internal/plugins/AppDebugConsole/module.js`.
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
- [ ] **Step 4:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Connect retained UI: Ratify the feature-owned wire contract; bind redacted backend diagnostics/log query and live log lifecycle to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 7:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.
- **UI prerequisite:** P02 host transport/session/envelope capability is a dependency; ratify prerequisite ordering and keep this UI task open until the connection can execute.


- [ ] **Step 8:** `FR-HOST-APP-DEBUG-CONSOLE-DEBUG-CONSOLE-APP-PLUGIN-CONTRACT` → `com.strategyquant.plugin.App.impl.DebugConsole.DebugConsoleAppPlugin`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-HOST-APP-DEBUG-CONSOLE-DEBUG-CONSOLE-APP-PLUGIN-GET-NAME` → `com.strategyquant.plugin.App.impl.DebugConsole.DebugConsoleAppPlugin.getName()Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 10:** `FR-HOST-APP-DEBUG-CONSOLE-DEBUG-CONSOLE-APP-PLUGIN-GET-PRODUCT` → `com.strategyquant.plugin.App.impl.DebugConsole.DebugConsoleAppPlugin.getProduct()Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_host_app_debug_console.py --no-cov`; expect discovery, workspace readiness, job/resource ownership and unmount cleanup; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture discovery, workspace readiness, job/resource ownership and unmount cleanup and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-host-app-debug-console.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-host-foundation-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise Debug Console for FEAT-HOST-APP-DEBUG-CONSOLE; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.


# 1.18 FEAT-HOST-JRT-FS - jrt-fs.jar

## 1. Objective

- **Goal:** Deliver the consumed jrt-fs capability in host.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Boot the host with validated settings, structured logging and diagnostics.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/j64/lib/jrt-fs.jar`; 57 raw class entries; SHA-256 `085f7db20ffb6e9f836fc7ffddc85be80ab36adb5eb1debe728913562416a342`.
- **Inspected reference:** [jrt-fs.md](../../sqx/Runtime/jrt-fs.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/j64/lib/jrt-fs.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/j64/lib/jrt-fs.jar" jdk.internal.jimage.BasicImageReader`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/host/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Bundled JVM filesystem support; replace with CPython/runtime packaging, not a Python class clone; downstream P01,P17.
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
- [ ] **Step 4:** Wire qualified adapters to consumers; release resources on failure/shutdown.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Verify UI-facing consumer contract: Test this infrastructure through its declared backend/host consumer; expose failures through the owning domain envelope. The phase's connected UI gate verifies the observable workflow.


- [ ] **Step 7:** `FR-HOST-JRT-FS-BASIC-IMAGE-READER-CONTRACT` → `jdk.internal.jimage.BasicImageReader`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 8:** `FR-HOST-JRT-FS-BASIC-IMAGE-READER-IS-SYSTEM-PROPERTY` → `jdk.internal.jimage.BasicImageReader.isSystemProperty(Ljava/lang/String;Ljava/lang/String;Ljava/lang/String;)Z`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-HOST-JRT-FS-BASIC-IMAGE-READER-OPEN` → `jdk.internal.jimage.BasicImageReader.open(Ljava/nio/file/Path;)Ljdk/internal/jimage/BasicImageReader;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_host_jrt_fs.py --no-cov`; expect fresh-process boot/shutdown, deterministic settings and sanitized logs; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture fresh-process boot/shutdown, deterministic settings and sanitized logs and visible failures.


# 1.19 FEAT-HOST-WMI4JAVA - WMI4Java-1.6.3.jar

## 1. Objective

- **Goal:** Resolve the consumed diagnostic, metadata or telemetry contract through approved host capabilities.
- **Context / Problem Solved:** Build 145 adds/changes this donor contribution; existing mock presentation and a filename do not establish functional support.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/libs/WMI4Java-1.6.3.jar`; 7 raw class entries; SHA-256 `7b9955ac56dcef6731961588f037b56d3e27f36222a3ec4ead2cd315059eea72`.
- **Inspected reference:** [WMI4Java-1.6.3.md](../../sqx/Libraries/WMI4Java-1.6.3.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/libs/WMI4Java-1.6.3.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/libs/WMI4Java-1.6.3.jar" com.profesorfalken.wmi4java.WMI4Java`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Ownership:** proposed `FEAT-HOST-WMI4JAVA` and `FR-HOST-WMI4JAVA-CONSUMED-CONTRACTS`; owner `app/host/README.md`. No application registration or implementation is implied.
- **Dependencies:** P00 evidence/ownership, P01 logging and P02 typed sessions/jobs/resources; phase-specific data/engine/project prerequisites from the delivery graph.
- **UI donors:** No standalone UI contribution is established for this infrastructure archive; trace its consuming host/domain feature and connect there.

## 3. File Changes

- **Create:** `app/host/diagnostics/vendor_contracts.py` — Resolve the consumed diagnostic, metadata or telemetry contract through approved host capabilities.
- **Modify:** `app/host/README.md` — ratify owning FEAT/FR contracts and status in the approved feature plan.
- **Create:** `tests/unit/reference_145/test_host_wmi4java.py` — donor-derived normal, boundary, failure and FR-log checks.
- **Delete / Deprecate:** none; version/dependency retirement requires explicit approved disposition.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Ratify cohort, owning FEAT/FRs, target decisions, dependencies and exact write paths in the canonical plan.
- [ ] **Step 2:** Fingerprint the selected cohort; enumerate classes, methods and actual consumers.
- [ ] **Step 3:** Inspect consumed bodies and record normal/boundary/error contracts as descriptive FRs.
- [ ] **Step 4:** Ratify ownership and a reuse/adaptation/JVM-only disposition; implement only retained behavior.
- [ ] **Step 5:** Verify fixtures, invalid inputs, lifecycle/cancellation where applicable and explicit FR logs.
- [ ] **Step 6:** Expose the typed capability to its existing host/domain consumers; no standalone UI is established for this infrastructure JAR.
- [ ] **Step 7:** Record timestamped observations and walkthrough; update the matching master checklist row only when all requirements pass.

- [ ] **Step 8:** `FR-HOST-WMI4JAVA-WMI4-JAVA-CONTRACT` → `com.profesorfalken.wmi4java.WMI4Java`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-HOST-WMI4JAVA-WMI4-JAVA-GET-WMISTUB` → `com.profesorfalken.wmi4java.WMI4Java.getWMIStub()Lcom/profesorfalken/wmi4java/WMIStub;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 10:** `FR-HOST-WMI4JAVA-WMI4-JAVA-GET` → `com.profesorfalken.wmi4java.WMI4Java.get()Lcom/profesorfalken/wmi4java/WMI4Java;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/reference_145/test_host_wmi4java.py --no-cov`; scoped Ruff format/check and strict Mypy; assert independent expected outputs and FR logs.
- **Manual / Browser Verification:** Inspect consumer logs, lifecycle/failure outcomes and the declared infrastructure/JVM-only disposition.
- **Completion limit:** missing bodies/ownership/entitlement or independent expected outputs keep the task unchecked; static declarations do not establish SQX parity.


# 1.20 FEAT-HOST-ANIMAL-SNIFFER-ANNOTATIONS - animal-sniffer-annotations-1.14.jar

## 1. Objective

- **Goal:** Resolve the consumed diagnostic, metadata or telemetry contract through approved host capabilities.
- **Context / Problem Solved:** Build 145 adds/changes this donor contribution; existing mock presentation and a filename do not establish functional support.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/libs/animal-sniffer-annotations-1.14.jar`; 1 raw class entries; SHA-256 `2068320bd6bad744c3673ab048f67e30bef8f518996fa380033556600669905d`.
- **Inspected reference:** [animal-sniffer-annotations-1.14.md](../../sqx/Libraries/animal-sniffer-annotations-1.14.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/libs/animal-sniffer-annotations-1.14.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/libs/animal-sniffer-annotations-1.14.jar" org.codehaus.mojo.animal_sniffer.IgnoreJRERequirement`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Ownership:** proposed `FEAT-HOST-ANIMAL-SNIFFER-ANNOTATIONS` and `FR-HOST-ANIMAL-SNIFFER-ANNOTATIONS-CONSUMED-CONTRACTS`; owner `app/host/README.md`. No application registration or implementation is implied.
- **Dependencies:** P00 evidence/ownership, P01 logging and P02 typed sessions/jobs/resources; phase-specific data/engine/project prerequisites from the delivery graph.
- **UI donors:** No standalone UI contribution is established for this infrastructure archive; trace its consuming host/domain feature and connect there.

## 3. File Changes

- **Create:** `app/host/diagnostics/vendor_contracts.py` — Resolve the consumed diagnostic, metadata or telemetry contract through approved host capabilities.
- **Modify:** `app/host/README.md` — ratify owning FEAT/FR contracts and status in the approved feature plan.
- **Create:** `tests/unit/reference_145/test_host_animal_sniffer_annotations.py` — donor-derived normal, boundary, failure and FR-log checks.
- **Delete / Deprecate:** none; version/dependency retirement requires explicit approved disposition.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Ratify cohort, owning FEAT/FRs, target decisions, dependencies and exact write paths in the canonical plan.
- [ ] **Step 2:** Fingerprint the selected cohort; enumerate classes, methods and actual consumers.
- [ ] **Step 3:** Inspect consumed bodies and record normal/boundary/error contracts as descriptive FRs.
- [ ] **Step 4:** Ratify ownership and a reuse/adaptation/JVM-only disposition; implement only retained behavior.
- [ ] **Step 5:** Verify fixtures, invalid inputs, lifecycle/cancellation where applicable and explicit FR logs.
- [ ] **Step 6:** Expose the typed capability to its existing host/domain consumers; no standalone UI is established for this infrastructure JAR.
- [ ] **Step 7:** Record timestamped observations and walkthrough; update the matching master checklist row only when all requirements pass.

- [ ] **Step 8:** `FR-HOST-ANIMAL-SNIFFER-ANNOTATIONS-IGNORE-JREREQUIREMENT-CONTRACT` → `org.codehaus.mojo.animal_sniffer.IgnoreJRERequirement`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/reference_145/test_host_animal_sniffer_annotations.py --no-cov`; scoped Ruff format/check and strict Mypy; assert independent expected outputs and FR logs.
- **Manual / Browser Verification:** Inspect consumer logs, lifecycle/failure outcomes and the declared infrastructure/JVM-only disposition.
- **Completion limit:** missing bodies/ownership/entitlement or independent expected outputs keep the task unchecked; static declarations do not establish SQX parity.


# 1.21 FEAT-HOST-ANNOTATIONS - annotations-13.0.jar

## 1. Objective

- **Goal:** Resolve the consumed diagnostic, metadata or telemetry contract through approved host capabilities.
- **Context / Problem Solved:** Build 145 adds/changes this donor contribution; existing mock presentation and a filename do not establish functional support.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/libs/annotations-13.0.jar`; 32 raw class entries; SHA-256 `ace2a10dc8e2d5fd34925ecac03e4988b2c0f851650c94b8cef49ba1bd111478`.
- **Inspected reference:** [annotations-13.0.md](../../sqx/Libraries/annotations-13.0.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/libs/annotations-13.0.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/libs/annotations-13.0.jar" org.intellij.lang.annotations.Flow`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Ownership:** proposed `FEAT-HOST-ANNOTATIONS` and `FR-HOST-ANNOTATIONS-CONSUMED-CONTRACTS`; owner `app/host/README.md`. No application registration or implementation is implied.
- **Dependencies:** P00 evidence/ownership, P01 logging and P02 typed sessions/jobs/resources; phase-specific data/engine/project prerequisites from the delivery graph.
- **UI donors:** No standalone UI contribution is established for this infrastructure archive; trace its consuming host/domain feature and connect there.

## 3. File Changes

- **Create:** `app/host/diagnostics/vendor_contracts.py` — Resolve the consumed diagnostic, metadata or telemetry contract through approved host capabilities.
- **Modify:** `app/host/README.md` — ratify owning FEAT/FR contracts and status in the approved feature plan.
- **Create:** `tests/unit/reference_145/test_host_annotations.py` — donor-derived normal, boundary, failure and FR-log checks.
- **Delete / Deprecate:** none; version/dependency retirement requires explicit approved disposition.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Ratify cohort, owning FEAT/FRs, target decisions, dependencies and exact write paths in the canonical plan.
- [ ] **Step 2:** Fingerprint the selected cohort; enumerate classes, methods and actual consumers.
- [ ] **Step 3:** Inspect consumed bodies and record normal/boundary/error contracts as descriptive FRs.
- [ ] **Step 4:** Ratify ownership and a reuse/adaptation/JVM-only disposition; implement only retained behavior.
- [ ] **Step 5:** Verify fixtures, invalid inputs, lifecycle/cancellation where applicable and explicit FR logs.
- [ ] **Step 6:** Expose the typed capability to its existing host/domain consumers; no standalone UI is established for this infrastructure JAR.
- [ ] **Step 7:** Record timestamped observations and walkthrough; update the matching master checklist row only when all requirements pass.

- [ ] **Step 8:** `FR-HOST-ANNOTATIONS-FLOW-CONTRACT` → `org.intellij.lang.annotations.Flow`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-HOST-ANNOTATIONS-FLOW-SOURCE` → `org.intellij.lang.annotations.Flow.source()Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 10:** `FR-HOST-ANNOTATIONS-FLOW-SOURCE-IS-CONTAINER` → `org.intellij.lang.annotations.Flow.sourceIsContainer()Z`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/reference_145/test_host_annotations.py --no-cov`; scoped Ruff format/check and strict Mypy; assert independent expected outputs and FR logs.
- **Manual / Browser Verification:** Inspect consumer logs, lifecycle/failure outcomes and the declared infrastructure/JVM-only disposition.
- **Completion limit:** missing bodies/ownership/entitlement or independent expected outputs keep the task unchecked; static declarations do not establish SQX parity.


# 1.22 FEAT-HOST-CHECKER-QUAL - checker-qual-3.4.1.jar

## 1. Objective

- **Goal:** Resolve the consumed diagnostic, metadata or telemetry contract through approved host capabilities.
- **Context / Problem Solved:** Build 145 adds/changes this donor contribution; existing mock presentation and a filename do not establish functional support.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/libs/checker-qual-3.4.1.jar`; 315 raw class entries; SHA-256 `bce5c887460542d69c0ffce05919fef8f56f9964a1505a99f6ae69a58351507e`.
- **Inspected reference:** [checker-qual-3.4.1.md](../../sqx/Libraries/checker-qual-3.4.1.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/libs/checker-qual-3.4.1.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/libs/checker-qual-3.4.1.jar" org.checkerframework.checker.compilermsgs.qual.CompilerMessageKey`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Ownership:** proposed `FEAT-HOST-CHECKER-QUAL` and `FR-HOST-CHECKER-QUAL-CONSUMED-CONTRACTS`; owner `app/host/README.md`. No application registration or implementation is implied.
- **Dependencies:** P00 evidence/ownership, P01 logging and P02 typed sessions/jobs/resources; phase-specific data/engine/project prerequisites from the delivery graph.
- **UI donors:** No standalone UI contribution is established for this infrastructure archive; trace its consuming host/domain feature and connect there.

## 3. File Changes

- **Create:** `app/host/diagnostics/vendor_contracts.py` — Resolve the consumed diagnostic, metadata or telemetry contract through approved host capabilities.
- **Modify:** `app/host/README.md` — ratify owning FEAT/FR contracts and status in the approved feature plan.
- **Create:** `tests/unit/reference_145/test_host_checker_qual.py` — donor-derived normal, boundary, failure and FR-log checks.
- **Delete / Deprecate:** none; version/dependency retirement requires explicit approved disposition.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Ratify cohort, owning FEAT/FRs, target decisions, dependencies and exact write paths in the canonical plan.
- [ ] **Step 2:** Fingerprint the selected cohort; enumerate classes, methods and actual consumers.
- [ ] **Step 3:** Inspect consumed bodies and record normal/boundary/error contracts as descriptive FRs.
- [ ] **Step 4:** Ratify ownership and a reuse/adaptation/JVM-only disposition; implement only retained behavior.
- [ ] **Step 5:** Verify fixtures, invalid inputs, lifecycle/cancellation where applicable and explicit FR logs.
- [ ] **Step 6:** Expose the typed capability to its existing host/domain consumers; no standalone UI is established for this infrastructure JAR.
- [ ] **Step 7:** Record timestamped observations and walkthrough; update the matching master checklist row only when all requirements pass.

- [ ] **Step 8:** `FR-HOST-CHECKER-QUAL-COMPILER-MESSAGE-KEY-CONTRACT` → `org.checkerframework.checker.compilermsgs.qual.CompilerMessageKey`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/reference_145/test_host_checker_qual.py --no-cov`; scoped Ruff format/check and strict Mypy; assert independent expected outputs and FR logs.
- **Manual / Browser Verification:** Inspect consumer logs, lifecycle/failure outcomes and the declared infrastructure/JVM-only disposition.
- **Completion limit:** missing bodies/ownership/entitlement or independent expected outputs keep the task unchecked; static declarations do not establish SQX parity.


# 1.23 FEAT-HOST-ERROR-PRONE-ANNOTATIONS - error_prone_annotations-2.4.0.jar

## 1. Objective

- **Goal:** Resolve the consumed diagnostic, metadata or telemetry contract through approved host capabilities.
- **Context / Problem Solved:** Build 145 adds/changes this donor contribution; existing mock presentation and a filename do not establish functional support.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/libs/error_prone_annotations-2.4.0.jar`; 22 raw class entries; SHA-256 `5f2a0648230a662e8be049df308d583d7369f13af683e44ddf5829b6d741a228`.
- **Inspected reference:** [error_prone_annotations-2.4.0.md](../../sqx/Libraries/error_prone_annotations-2.4.0.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/libs/error_prone_annotations-2.4.0.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/libs/error_prone_annotations-2.4.0.jar" com.google.errorprone.annotations.CanIgnoreReturnValue`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Ownership:** proposed `FEAT-HOST-ERROR-PRONE-ANNOTATIONS` and `FR-HOST-ERROR-PRONE-ANNOTATIONS-CONSUMED-CONTRACTS`; owner `app/host/README.md`. No application registration or implementation is implied.
- **Dependencies:** P00 evidence/ownership, P01 logging and P02 typed sessions/jobs/resources; phase-specific data/engine/project prerequisites from the delivery graph.
- **UI donors:** No standalone UI contribution is established for this infrastructure archive; trace its consuming host/domain feature and connect there.

## 3. File Changes

- **Create:** `app/host/diagnostics/vendor_contracts.py` — Resolve the consumed diagnostic, metadata or telemetry contract through approved host capabilities.
- **Modify:** `app/host/README.md` — ratify owning FEAT/FR contracts and status in the approved feature plan.
- **Create:** `tests/unit/reference_145/test_host_error_prone_annotations.py` — donor-derived normal, boundary, failure and FR-log checks.
- **Delete / Deprecate:** none; version/dependency retirement requires explicit approved disposition.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Ratify cohort, owning FEAT/FRs, target decisions, dependencies and exact write paths in the canonical plan.
- [ ] **Step 2:** Fingerprint the selected cohort; enumerate classes, methods and actual consumers.
- [ ] **Step 3:** Inspect consumed bodies and record normal/boundary/error contracts as descriptive FRs.
- [ ] **Step 4:** Ratify ownership and a reuse/adaptation/JVM-only disposition; implement only retained behavior.
- [ ] **Step 5:** Verify fixtures, invalid inputs, lifecycle/cancellation where applicable and explicit FR logs.
- [ ] **Step 6:** Expose the typed capability to its existing host/domain consumers; no standalone UI is established for this infrastructure JAR.
- [ ] **Step 7:** Record timestamped observations and walkthrough; update the matching master checklist row only when all requirements pass.

- [ ] **Step 8:** `FR-HOST-ERROR-PRONE-ANNOTATIONS-CAN-IGNORE-RETURN-VALUE-CONTRACT` → `com.google.errorprone.annotations.CanIgnoreReturnValue`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/reference_145/test_host_error_prone_annotations.py --no-cov`; scoped Ruff format/check and strict Mypy; assert independent expected outputs and FR logs.
- **Manual / Browser Verification:** Inspect consumer logs, lifecycle/failure outcomes and the declared infrastructure/JVM-only disposition.
- **Completion limit:** missing bodies/ownership/entitlement or independent expected outputs keep the task unchecked; static declarations do not establish SQX parity.


# 1.24 FEAT-HOST-J2OBJC-ANNOTATIONS - j2objc-annotations-1.1.jar

## 1. Objective

- **Goal:** Resolve the consumed diagnostic, metadata or telemetry contract through approved host capabilities.
- **Context / Problem Solved:** Build 145 adds/changes this donor contribution; existing mock presentation and a filename do not establish functional support.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/libs/j2objc-annotations-1.1.jar`; 12 raw class entries; SHA-256 `2994a7eb78f2710bd3d3bfb639b2c94e219cedac0d4d084d516e78c16dddecf6`.
- **Inspected reference:** [j2objc-annotations-1.1.md](../../sqx/Libraries/j2objc-annotations-1.1.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/libs/j2objc-annotations-1.1.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/libs/j2objc-annotations-1.1.jar" com.google.j2objc.annotations.AutoreleasePool`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Ownership:** proposed `FEAT-HOST-J2OBJC-ANNOTATIONS` and `FR-HOST-J2OBJC-ANNOTATIONS-CONSUMED-CONTRACTS`; owner `app/host/README.md`. No application registration or implementation is implied.
- **Dependencies:** P00 evidence/ownership, P01 logging and P02 typed sessions/jobs/resources; phase-specific data/engine/project prerequisites from the delivery graph.
- **UI donors:** No standalone UI contribution is established for this infrastructure archive; trace its consuming host/domain feature and connect there.

## 3. File Changes

- **Create:** `app/host/diagnostics/vendor_contracts.py` — Resolve the consumed diagnostic, metadata or telemetry contract through approved host capabilities.
- **Modify:** `app/host/README.md` — ratify owning FEAT/FR contracts and status in the approved feature plan.
- **Create:** `tests/unit/reference_145/test_host_j2objc_annotations.py` — donor-derived normal, boundary, failure and FR-log checks.
- **Delete / Deprecate:** none; version/dependency retirement requires explicit approved disposition.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Ratify cohort, owning FEAT/FRs, target decisions, dependencies and exact write paths in the canonical plan.
- [ ] **Step 2:** Fingerprint the selected cohort; enumerate classes, methods and actual consumers.
- [ ] **Step 3:** Inspect consumed bodies and record normal/boundary/error contracts as descriptive FRs.
- [ ] **Step 4:** Ratify ownership and a reuse/adaptation/JVM-only disposition; implement only retained behavior.
- [ ] **Step 5:** Verify fixtures, invalid inputs, lifecycle/cancellation where applicable and explicit FR logs.
- [ ] **Step 6:** Expose the typed capability to its existing host/domain consumers; no standalone UI is established for this infrastructure JAR.
- [ ] **Step 7:** Record timestamped observations and walkthrough; update the matching master checklist row only when all requirements pass.

- [ ] **Step 8:** `FR-HOST-J2OBJC-ANNOTATIONS-AUTORELEASE-POOL-CONTRACT` → `com.google.j2objc.annotations.AutoreleasePool`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/reference_145/test_host_j2objc_annotations.py --no-cov`; scoped Ruff format/check and strict Mypy; assert independent expected outputs and FR logs.
- **Manual / Browser Verification:** Inspect consumer logs, lifecycle/failure outcomes and the declared infrastructure/JVM-only disposition.
- **Completion limit:** missing bodies/ownership/entitlement or independent expected outputs keep the task unchecked; static declarations do not establish SQX parity.


# 1.25 FEAT-HOST-JBOSS-LOGGING - jboss-logging-3.3.0.Final.jar

## 1. Objective

- **Goal:** Resolve the consumed diagnostic, metadata or telemetry contract through approved host capabilities.
- **Context / Problem Solved:** Build 145 adds/changes this donor contribution; existing mock presentation and a filename do not establish functional support.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/libs/jboss-logging-3.3.0.Final.jar`; 48 raw class entries; SHA-256 `e0e0595e7f70c464609095aef9e47a8484e05f2f621c0aa5081c18e3db2d498c`.
- **Inspected reference:** [jboss-logging-3.3.0.Final.md](../../sqx/Libraries/jboss-logging-3.3.0.Final.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/libs/jboss-logging-3.3.0.Final.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/libs/jboss-logging-3.3.0.Final.jar" org.jboss.logging.LogMessage`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Ownership:** proposed `FEAT-HOST-JBOSS-LOGGING` and `FR-HOST-JBOSS-LOGGING-CONSUMED-CONTRACTS`; owner `app/host/README.md`. No application registration or implementation is implied.
- **Dependencies:** P00 evidence/ownership, P01 logging and P02 typed sessions/jobs/resources; phase-specific data/engine/project prerequisites from the delivery graph.
- **UI donors:** No standalone UI contribution is established for this infrastructure archive; trace its consuming host/domain feature and connect there.

## 3. File Changes

- **Create:** `app/host/diagnostics/vendor_contracts.py` — Resolve the consumed diagnostic, metadata or telemetry contract through approved host capabilities.
- **Modify:** `app/host/README.md` — ratify owning FEAT/FR contracts and status in the approved feature plan.
- **Create:** `tests/unit/reference_145/test_host_jboss_logging.py` — donor-derived normal, boundary, failure and FR-log checks.
- **Delete / Deprecate:** none; version/dependency retirement requires explicit approved disposition.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Ratify cohort, owning FEAT/FRs, target decisions, dependencies and exact write paths in the canonical plan.
- [ ] **Step 2:** Fingerprint the selected cohort; enumerate classes, methods and actual consumers.
- [ ] **Step 3:** Inspect consumed bodies and record normal/boundary/error contracts as descriptive FRs.
- [ ] **Step 4:** Ratify ownership and a reuse/adaptation/JVM-only disposition; implement only retained behavior.
- [ ] **Step 5:** Verify fixtures, invalid inputs, lifecycle/cancellation where applicable and explicit FR logs.
- [ ] **Step 6:** Expose the typed capability to its existing host/domain consumers; no standalone UI is established for this infrastructure JAR.
- [ ] **Step 7:** Record timestamped observations and walkthrough; update the matching master checklist row only when all requirements pass.

- [ ] **Step 8:** `FR-HOST-JBOSS-LOGGING-LOG-MESSAGE-CONTRACT` → `org.jboss.logging.LogMessage`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-HOST-JBOSS-LOGGING-LOG-MESSAGE-LEVEL` → `org.jboss.logging.LogMessage.level()Lorg/jboss/logging/Logger$Level;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 10:** `FR-HOST-JBOSS-LOGGING-LOG-MESSAGE-LOGGING-CLASS` → `org.jboss.logging.LogMessage.loggingClass()Ljava/lang/Class;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/reference_145/test_host_jboss_logging.py --no-cov`; scoped Ruff format/check and strict Mypy; assert independent expected outputs and FR logs.
- **Manual / Browser Verification:** Inspect consumer logs, lifecycle/failure outcomes and the declared infrastructure/JVM-only disposition.
- **Completion limit:** missing bodies/ownership/entitlement or independent expected outputs keep the task unchecked; static declarations do not establish SQX parity.


# 1.26 FEAT-HOST-JSPECIFY - jspecify-1.0.0.jar

## 1. Objective

- **Goal:** Resolve the consumed diagnostic, metadata or telemetry contract through approved host capabilities.
- **Context / Problem Solved:** Build 145 adds/changes this donor contribution; existing mock presentation and a filename do not establish functional support.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/libs/jspecify-1.0.0.jar`; 5 raw class entries; SHA-256 `1fad6e6be7557781e4d33729d49ae1cdc8fdda6fe477bb0cc68ce351eafdfbab`.
- **Inspected reference:** [jspecify-1.0.0.md](../../sqx/Libraries/jspecify-1.0.0.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/libs/jspecify-1.0.0.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/libs/jspecify-1.0.0.jar" org.jspecify.annotations.NonNull`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Ownership:** proposed `FEAT-HOST-JSPECIFY` and `FR-HOST-JSPECIFY-CONSUMED-CONTRACTS`; owner `app/host/README.md`. No application registration or implementation is implied.
- **Dependencies:** P00 evidence/ownership, P01 logging and P02 typed sessions/jobs/resources; phase-specific data/engine/project prerequisites from the delivery graph.
- **UI donors:** No standalone UI contribution is established for this infrastructure archive; trace its consuming host/domain feature and connect there.

## 3. File Changes

- **Create:** `app/host/diagnostics/vendor_contracts.py` — Resolve the consumed diagnostic, metadata or telemetry contract through approved host capabilities.
- **Modify:** `app/host/README.md` — ratify owning FEAT/FR contracts and status in the approved feature plan.
- **Create:** `tests/unit/reference_145/test_host_jspecify.py` — donor-derived normal, boundary, failure and FR-log checks.
- **Delete / Deprecate:** none; version/dependency retirement requires explicit approved disposition.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Ratify cohort, owning FEAT/FRs, target decisions, dependencies and exact write paths in the canonical plan.
- [ ] **Step 2:** Fingerprint the selected cohort; enumerate classes, methods and actual consumers.
- [ ] **Step 3:** Inspect consumed bodies and record normal/boundary/error contracts as descriptive FRs.
- [ ] **Step 4:** Ratify ownership and a reuse/adaptation/JVM-only disposition; implement only retained behavior.
- [ ] **Step 5:** Verify fixtures, invalid inputs, lifecycle/cancellation where applicable and explicit FR logs.
- [ ] **Step 6:** Expose the typed capability to its existing host/domain consumers; no standalone UI is established for this infrastructure JAR.
- [ ] **Step 7:** Record timestamped observations and walkthrough; update the matching master checklist row only when all requirements pass.

- [ ] **Step 8:** `FR-HOST-JSPECIFY-NON-NULL-CONTRACT` → `org.jspecify.annotations.NonNull`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/reference_145/test_host_jspecify.py --no-cov`; scoped Ruff format/check and strict Mypy; assert independent expected outputs and FR logs.
- **Manual / Browser Verification:** Inspect consumer logs, lifecycle/failure outcomes and the declared infrastructure/JVM-only disposition.
- **Completion limit:** missing bodies/ownership/entitlement or independent expected outputs keep the task unchecked; static declarations do not establish SQX parity.


# 1.27 FEAT-HOST-JSR305 - jsr305-3.0.2.jar

## 1. Objective

- **Goal:** Resolve the consumed diagnostic, metadata or telemetry contract through approved host capabilities.
- **Context / Problem Solved:** Build 145 adds/changes this donor contribution; existing mock presentation and a filename do not establish functional support.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/libs/jsr305-3.0.2.jar`; 35 raw class entries; SHA-256 `766ad2a0783f2687962c8ad74ceecc38a28b9f72a2d085ee438b7813e928d0c7`.
- **Inspected reference:** [jsr305-3.0.2.md](../../sqx/Libraries/jsr305-3.0.2.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/libs/jsr305-3.0.2.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/libs/jsr305-3.0.2.jar" javax.annotation.CheckForNull`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Ownership:** proposed `FEAT-HOST-JSR305` and `FR-HOST-JSR305-CONSUMED-CONTRACTS`; owner `app/host/README.md`. No application registration or implementation is implied.
- **Dependencies:** P00 evidence/ownership, P01 logging and P02 typed sessions/jobs/resources; phase-specific data/engine/project prerequisites from the delivery graph.
- **UI donors:** No standalone UI contribution is established for this infrastructure archive; trace its consuming host/domain feature and connect there.

## 3. File Changes

- **Create:** `app/host/diagnostics/vendor_contracts.py` — Resolve the consumed diagnostic, metadata or telemetry contract through approved host capabilities.
- **Modify:** `app/host/README.md` — ratify owning FEAT/FR contracts and status in the approved feature plan.
- **Create:** `tests/unit/reference_145/test_host_jsr305.py` — donor-derived normal, boundary, failure and FR-log checks.
- **Delete / Deprecate:** none; version/dependency retirement requires explicit approved disposition.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Ratify cohort, owning FEAT/FRs, target decisions, dependencies and exact write paths in the canonical plan.
- [ ] **Step 2:** Fingerprint the selected cohort; enumerate classes, methods and actual consumers.
- [ ] **Step 3:** Inspect consumed bodies and record normal/boundary/error contracts as descriptive FRs.
- [ ] **Step 4:** Ratify ownership and a reuse/adaptation/JVM-only disposition; implement only retained behavior.
- [ ] **Step 5:** Verify fixtures, invalid inputs, lifecycle/cancellation where applicable and explicit FR logs.
- [ ] **Step 6:** Expose the typed capability to its existing host/domain consumers; no standalone UI is established for this infrastructure JAR.
- [ ] **Step 7:** Record timestamped observations and walkthrough; update the matching master checklist row only when all requirements pass.

- [ ] **Step 8:** `FR-HOST-JSR305-CHECK-FOR-NULL-CONTRACT` → `javax.annotation.CheckForNull`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/reference_145/test_host_jsr305.py --no-cov`; scoped Ruff format/check and strict Mypy; assert independent expected outputs and FR logs.
- **Manual / Browser Verification:** Inspect consumer logs, lifecycle/failure outcomes and the declared infrastructure/JVM-only disposition.
- **Completion limit:** missing bodies/ownership/entitlement or independent expected outputs keep the task unchecked; static declarations do not establish SQX parity.


# 1.28 FEAT-HOST-OPENTELEMETRY-API - opentelemetry-api-1.61.0.jar

## 1. Objective

- **Goal:** Resolve the consumed diagnostic, metadata or telemetry contract through approved host capabilities.
- **Context / Problem Solved:** Build 145 adds/changes this donor contribution; existing mock presentation and a filename do not establish functional support.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/libs/opentelemetry-api-1.61.0.jar`; 172 raw class entries; SHA-256 `ff5d610db14da2881eaa8f543f3bd6578a306163d02675254ff0669286c89158`.
- **Inspected reference:** [opentelemetry-api-1.61.0.md](../../sqx/Libraries/opentelemetry-api-1.61.0.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/libs/opentelemetry-api-1.61.0.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/libs/opentelemetry-api-1.61.0.jar" io.opentelemetry.api.DefaultOpenTelemetry`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Ownership:** proposed `FEAT-HOST-OPENTELEMETRY-API` and `FR-HOST-OPENTELEMETRY-API-CONSUMED-CONTRACTS`; owner `app/host/README.md`. No application registration or implementation is implied.
- **Dependencies:** P00 evidence/ownership, P01 logging and P02 typed sessions/jobs/resources; phase-specific data/engine/project prerequisites from the delivery graph.
- **UI donors:** No standalone UI contribution is established for this infrastructure archive; trace its consuming host/domain feature and connect there.

## 3. File Changes

- **Create:** `app/host/diagnostics/vendor_contracts.py` — Resolve the consumed diagnostic, metadata or telemetry contract through approved host capabilities.
- **Modify:** `app/host/README.md` — ratify owning FEAT/FR contracts and status in the approved feature plan.
- **Create:** `tests/unit/reference_145/test_host_opentelemetry_api.py` — donor-derived normal, boundary, failure and FR-log checks.
- **Delete / Deprecate:** none; version/dependency retirement requires explicit approved disposition.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Ratify cohort, owning FEAT/FRs, target decisions, dependencies and exact write paths in the canonical plan.
- [ ] **Step 2:** Fingerprint the selected cohort; enumerate classes, methods and actual consumers.
- [ ] **Step 3:** Inspect consumed bodies and record normal/boundary/error contracts as descriptive FRs.
- [ ] **Step 4:** Ratify ownership and a reuse/adaptation/JVM-only disposition; implement only retained behavior.
- [ ] **Step 5:** Verify fixtures, invalid inputs, lifecycle/cancellation where applicable and explicit FR logs.
- [ ] **Step 6:** Expose the typed capability to its existing host/domain consumers; no standalone UI is established for this infrastructure JAR.
- [ ] **Step 7:** Record timestamped observations and walkthrough; update the matching master checklist row only when all requirements pass.

- [ ] **Step 8:** `FR-HOST-OPENTELEMETRY-API-DEFAULT-OPEN-TELEMETRY-CONTRACT` → `io.opentelemetry.api.DefaultOpenTelemetry`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-HOST-OPENTELEMETRY-API-DEFAULT-OPEN-TELEMETRY-GET-NOOP` → `io.opentelemetry.api.DefaultOpenTelemetry.getNoop()Lio/opentelemetry/api/OpenTelemetry;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 10:** `FR-HOST-OPENTELEMETRY-API-DEFAULT-OPEN-TELEMETRY-GET-PROPAGATING` → `io.opentelemetry.api.DefaultOpenTelemetry.getPropagating(Lio/opentelemetry/context/propagation/ContextPropagators;)Lio/opentelemetry/api/OpenTelemetry;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/reference_145/test_host_opentelemetry_api.py --no-cov`; scoped Ruff format/check and strict Mypy; assert independent expected outputs and FR logs.
- **Manual / Browser Verification:** Inspect consumer logs, lifecycle/failure outcomes and the declared infrastructure/JVM-only disposition.
- **Completion limit:** missing bodies/ownership/entitlement or independent expected outputs keep the task unchecked; static declarations do not establish SQX parity.


# 1.29 FEAT-HOST-OPENTELEMETRY-API-INCUBATOR - opentelemetry-api-incubator-1.61.0-alpha.jar

## 1. Objective

- **Goal:** Resolve the consumed diagnostic, metadata or telemetry contract through approved host capabilities.
- **Context / Problem Solved:** Build 145 adds/changes this donor contribution; existing mock presentation and a filename do not establish functional support.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/libs/opentelemetry-api-incubator-1.61.0-alpha.jar`; 87 raw class entries; SHA-256 `0f3f4eacb0a29579cb56e94bfbb75fab6aa4e893e7c1e37e91da874d06dbc7ce`.
- **Inspected reference:** [opentelemetry-api-incubator-1.61.0-alpha.md](../../sqx/Libraries/opentelemetry-api-incubator-1.61.0-alpha.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/libs/opentelemetry-api-incubator-1.61.0-alpha.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/libs/opentelemetry-api-incubator-1.61.0-alpha.jar" io.opentelemetry.api.incubator.ExtendedOpenTelemetry`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Ownership:** proposed `FEAT-HOST-OPENTELEMETRY-API-INCUBATOR` and `FR-HOST-OPENTELEMETRY-API-INCUBATOR-CONSUMED-CONTRACTS`; owner `app/host/README.md`. No application registration or implementation is implied.
- **Dependencies:** P00 evidence/ownership, P01 logging and P02 typed sessions/jobs/resources; phase-specific data/engine/project prerequisites from the delivery graph.
- **UI donors:** No standalone UI contribution is established for this infrastructure archive; trace its consuming host/domain feature and connect there.

## 3. File Changes

- **Create:** `app/host/diagnostics/vendor_contracts.py` — Resolve the consumed diagnostic, metadata or telemetry contract through approved host capabilities.
- **Modify:** `app/host/README.md` — ratify owning FEAT/FR contracts and status in the approved feature plan.
- **Create:** `tests/unit/reference_145/test_host_opentelemetry_api_incubator.py` — donor-derived normal, boundary, failure and FR-log checks.
- **Delete / Deprecate:** none; version/dependency retirement requires explicit approved disposition.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Ratify cohort, owning FEAT/FRs, target decisions, dependencies and exact write paths in the canonical plan.
- [ ] **Step 2:** Fingerprint the selected cohort; enumerate classes, methods and actual consumers.
- [ ] **Step 3:** Inspect consumed bodies and record normal/boundary/error contracts as descriptive FRs.
- [ ] **Step 4:** Ratify ownership and a reuse/adaptation/JVM-only disposition; implement only retained behavior.
- [ ] **Step 5:** Verify fixtures, invalid inputs, lifecycle/cancellation where applicable and explicit FR logs.
- [ ] **Step 6:** Expose the typed capability to its existing host/domain consumers; no standalone UI is established for this infrastructure JAR.
- [ ] **Step 7:** Record timestamped observations and walkthrough; update the matching master checklist row only when all requirements pass.

- [ ] **Step 8:** `FR-HOST-OPENTELEMETRY-API-INCUBATOR-EXTENDED-OPEN-TELEMETRY-CONTRACT` → `io.opentelemetry.api.incubator.ExtendedOpenTelemetry`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-HOST-OPENTELEMETRY-API-INCUBATOR-EXTENDED-OPEN-TELEMETRY-GET-CONFIG-PROVIDER` → `io.opentelemetry.api.incubator.ExtendedOpenTelemetry.getConfigProvider()Lio/opentelemetry/api/incubator/config/ConfigProvider;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 10:** `FR-HOST-OPENTELEMETRY-API-INCUBATOR-EXTENDED-OPEN-TELEMETRY-GET-INSTRUMENTATION-CONFIG` → `io.opentelemetry.api.incubator.ExtendedOpenTelemetry.getInstrumentationConfig(Ljava/lang/String;)Lio/opentelemetry/api/incubator/config/DeclarativeConfigProperties;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/reference_145/test_host_opentelemetry_api_incubator.py --no-cov`; scoped Ruff format/check and strict Mypy; assert independent expected outputs and FR logs.
- **Manual / Browser Verification:** Inspect consumer logs, lifecycle/failure outcomes and the declared infrastructure/JVM-only disposition.
- **Completion limit:** missing bodies/ownership/entitlement or independent expected outputs keep the task unchecked; static declarations do not establish SQX parity.


# 1.30 FEAT-HOST-OPENTELEMETRY-COMMON - opentelemetry-common-1.61.0.jar

## 1. Objective

- **Goal:** Resolve the consumed diagnostic, metadata or telemetry contract through approved host capabilities.
- **Context / Problem Solved:** Build 145 adds/changes this donor contribution; existing mock presentation and a filename do not establish functional support.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/libs/opentelemetry-common-1.61.0.jar`; 2 raw class entries; SHA-256 `618bd894feb3f65a563209603d27cbab534310be22705f78c525fc0e799e8e91`.
- **Inspected reference:** [opentelemetry-common-1.61.0.md](../../sqx/Libraries/opentelemetry-common-1.61.0.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/libs/opentelemetry-common-1.61.0.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/libs/opentelemetry-common-1.61.0.jar" io.opentelemetry.common.ComponentLoader`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Ownership:** proposed `FEAT-HOST-OPENTELEMETRY-COMMON` and `FR-HOST-OPENTELEMETRY-COMMON-CONSUMED-CONTRACTS`; owner `app/host/README.md`. No application registration or implementation is implied.
- **Dependencies:** P00 evidence/ownership, P01 logging and P02 typed sessions/jobs/resources; phase-specific data/engine/project prerequisites from the delivery graph.
- **UI donors:** No standalone UI contribution is established for this infrastructure archive; trace its consuming host/domain feature and connect there.

## 3. File Changes

- **Create:** `app/host/diagnostics/vendor_contracts.py` — Resolve the consumed diagnostic, metadata or telemetry contract through approved host capabilities.
- **Modify:** `app/host/README.md` — ratify owning FEAT/FR contracts and status in the approved feature plan.
- **Create:** `tests/unit/reference_145/test_host_opentelemetry_common.py` — donor-derived normal, boundary, failure and FR-log checks.
- **Delete / Deprecate:** none; version/dependency retirement requires explicit approved disposition.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Ratify cohort, owning FEAT/FRs, target decisions, dependencies and exact write paths in the canonical plan.
- [ ] **Step 2:** Fingerprint the selected cohort; enumerate classes, methods and actual consumers.
- [ ] **Step 3:** Inspect consumed bodies and record normal/boundary/error contracts as descriptive FRs.
- [ ] **Step 4:** Ratify ownership and a reuse/adaptation/JVM-only disposition; implement only retained behavior.
- [ ] **Step 5:** Verify fixtures, invalid inputs, lifecycle/cancellation where applicable and explicit FR logs.
- [ ] **Step 6:** Expose the typed capability to its existing host/domain consumers; no standalone UI is established for this infrastructure JAR.
- [ ] **Step 7:** Record timestamped observations and walkthrough; update the matching master checklist row only when all requirements pass.

- [ ] **Step 8:** `FR-HOST-OPENTELEMETRY-COMMON-COMPONENT-LOADER-CONTRACT` → `io.opentelemetry.common.ComponentLoader`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-HOST-OPENTELEMETRY-COMMON-COMPONENT-LOADER-LOAD` → `io.opentelemetry.common.ComponentLoader.load(Ljava/lang/Class;)Ljava/lang/Iterable;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 10:** `FR-HOST-OPENTELEMETRY-COMMON-COMPONENT-LOADER-FOR-CLASS-LOADER` → `io.opentelemetry.common.ComponentLoader.forClassLoader(Ljava/lang/ClassLoader;)Lio/opentelemetry/common/ComponentLoader;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/reference_145/test_host_opentelemetry_common.py --no-cov`; scoped Ruff format/check and strict Mypy; assert independent expected outputs and FR logs.
- **Manual / Browser Verification:** Inspect consumer logs, lifecycle/failure outcomes and the declared infrastructure/JVM-only disposition.
- **Completion limit:** missing bodies/ownership/entitlement or independent expected outputs keep the task unchecked; static declarations do not establish SQX parity.


# 1.31 FEAT-HOST-OPENTELEMETRY-CONTEXT - opentelemetry-context-1.61.0.jar

## 1. Objective

- **Goal:** Resolve the consumed diagnostic, metadata or telemetry contract through approved host capabilities.
- **Context / Problem Solved:** Build 145 adds/changes this donor contribution; existing mock presentation and a filename do not establish functional support.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/libs/opentelemetry-context-1.61.0.jar`; 42 raw class entries; SHA-256 `2325b9b9081e506b5b58c54053109aa446f774e233e90511dc17fd8b20500558`.
- **Inspected reference:** [opentelemetry-context-1.61.0.md](../../sqx/Libraries/opentelemetry-context-1.61.0.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/libs/opentelemetry-context-1.61.0.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/libs/opentelemetry-context-1.61.0.jar" io.opentelemetry.context.ArrayBasedContext`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Ownership:** proposed `FEAT-HOST-OPENTELEMETRY-CONTEXT` and `FR-HOST-OPENTELEMETRY-CONTEXT-CONSUMED-CONTRACTS`; owner `app/host/README.md`. No application registration or implementation is implied.
- **Dependencies:** P00 evidence/ownership, P01 logging and P02 typed sessions/jobs/resources; phase-specific data/engine/project prerequisites from the delivery graph.
- **UI donors:** No standalone UI contribution is established for this infrastructure archive; trace its consuming host/domain feature and connect there.

## 3. File Changes

- **Create:** `app/host/diagnostics/vendor_contracts.py` — Resolve the consumed diagnostic, metadata or telemetry contract through approved host capabilities.
- **Modify:** `app/host/README.md` — ratify owning FEAT/FR contracts and status in the approved feature plan.
- **Create:** `tests/unit/reference_145/test_host_opentelemetry_context.py` — donor-derived normal, boundary, failure and FR-log checks.
- **Delete / Deprecate:** none; version/dependency retirement requires explicit approved disposition.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Ratify cohort, owning FEAT/FRs, target decisions, dependencies and exact write paths in the canonical plan.
- [ ] **Step 2:** Fingerprint the selected cohort; enumerate classes, methods and actual consumers.
- [ ] **Step 3:** Inspect consumed bodies and record normal/boundary/error contracts as descriptive FRs.
- [ ] **Step 4:** Ratify ownership and a reuse/adaptation/JVM-only disposition; implement only retained behavior.
- [ ] **Step 5:** Verify fixtures, invalid inputs, lifecycle/cancellation where applicable and explicit FR logs.
- [ ] **Step 6:** Expose the typed capability to its existing host/domain consumers; no standalone UI is established for this infrastructure JAR.
- [ ] **Step 7:** Record timestamped observations and walkthrough; update the matching master checklist row only when all requirements pass.

- [ ] **Step 8:** `FR-HOST-OPENTELEMETRY-CONTEXT-ARRAY-BASED-CONTEXT-CONTRACT` → `io.opentelemetry.context.ArrayBasedContext`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-HOST-OPENTELEMETRY-CONTEXT-ARRAY-BASED-CONTEXT-ROOT` → `io.opentelemetry.context.ArrayBasedContext.root()Lio/opentelemetry/context/Context;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 10:** `FR-HOST-OPENTELEMETRY-CONTEXT-ARRAY-BASED-CONTEXT-GET` → `io.opentelemetry.context.ArrayBasedContext.get(Lio/opentelemetry/context/ContextKey;)Ljava/lang/Object;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/reference_145/test_host_opentelemetry_context.py --no-cov`; scoped Ruff format/check and strict Mypy; assert independent expected outputs and FR logs.
- **Manual / Browser Verification:** Inspect consumer logs, lifecycle/failure outcomes and the declared infrastructure/JVM-only disposition.
- **Completion limit:** missing bodies/ownership/entitlement or independent expected outputs keep the task unchecked; static declarations do not establish SQX parity.


# 1.32 FEAT-HOST-OPENTELEMETRY-INSTRUMENTATION-ANNOTATIONS-SUPPORT - opentelemetry-instrumentation-annotations-support-2.27.0-alpha.jar

## 1. Objective

- **Goal:** Resolve the consumed diagnostic, metadata or telemetry contract through approved host capabilities.
- **Context / Problem Solved:** Build 145 adds/changes this donor contribution; existing mock presentation and a filename do not establish functional support.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/libs/opentelemetry-instrumentation-annotations-support-2.27.0-alpha.jar`; 27 raw class entries; SHA-256 `e144b9e11b70d2c0090ab0ccf32432e78f8311910f31b6a304d9cb90a2e02e17`.
- **Inspected reference:** [opentelemetry-instrumentation-annotations-support-2.27.0-alpha.md](../../sqx/Libraries/opentelemetry-instrumentation-annotations-support-2.27.0-alpha.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/libs/opentelemetry-instrumentation-annotations-support-2.27.0-alpha.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/libs/opentelemetry-instrumentation-annotations-support-2.27.0-alpha.jar" io.opentelemetry.instrumentation.api.annotation.support.AnnotationReflectionHelper`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Ownership:** proposed `FEAT-HOST-OPENTELEMETRY-INSTRUMENTATION-ANNOTATIONS-SUPPORT` and `FR-HOST-OPENTELEMETRY-INSTRUMENTATION-ANNOTATIONS-SUPPORT-CONSUMED-CONTRACTS`; owner `app/host/README.md`. No application registration or implementation is implied.
- **Dependencies:** P00 evidence/ownership, P01 logging and P02 typed sessions/jobs/resources; phase-specific data/engine/project prerequisites from the delivery graph.
- **UI donors:** No standalone UI contribution is established for this infrastructure archive; trace its consuming host/domain feature and connect there.

## 3. File Changes

- **Create:** `app/host/diagnostics/vendor_contracts.py` — Resolve the consumed diagnostic, metadata or telemetry contract through approved host capabilities.
- **Modify:** `app/host/README.md` — ratify owning FEAT/FR contracts and status in the approved feature plan.
- **Create:** `tests/unit/reference_145/test_host_opentelemetry_instrumentation_annotations_support.py` — donor-derived normal, boundary, failure and FR-log checks.
- **Delete / Deprecate:** none; version/dependency retirement requires explicit approved disposition.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Ratify cohort, owning FEAT/FRs, target decisions, dependencies and exact write paths in the canonical plan.
- [ ] **Step 2:** Fingerprint the selected cohort; enumerate classes, methods and actual consumers.
- [ ] **Step 3:** Inspect consumed bodies and record normal/boundary/error contracts as descriptive FRs.
- [ ] **Step 4:** Ratify ownership and a reuse/adaptation/JVM-only disposition; implement only retained behavior.
- [ ] **Step 5:** Verify fixtures, invalid inputs, lifecycle/cancellation where applicable and explicit FR logs.
- [ ] **Step 6:** Expose the typed capability to its existing host/domain consumers; no standalone UI is established for this infrastructure JAR.
- [ ] **Step 7:** Record timestamped observations and walkthrough; update the matching master checklist row only when all requirements pass.

- [ ] **Step 8:** `FR-HOST-OPENTELEMETRY-INSTRUMENTATION-ANNOTATIONS-SUPPORT-ANNOTATION-REFLECTION-HELPER-CONTRACT` → `io.opentelemetry.instrumentation.api.annotation.support.AnnotationReflectionHelper`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-HOST-OPENTELEMETRY-INSTRUMENTATION-ANNOTATIONS-SUPPORT-ANNOTATION-REFLECTION-HELPER-FOR-NAME-OR-NULL` → `io.opentelemetry.instrumentation.api.annotation.support.AnnotationReflectionHelper.forNameOrNull(Ljava/lang/ClassLoader;Ljava/lang/String;)Ljava/lang/Class;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 10:** `FR-HOST-OPENTELEMETRY-INSTRUMENTATION-ANNOTATIONS-SUPPORT-ANNOTATION-REFLECTION-HELPER-BIND-ANNOTATION-ELEMENT-METHOD` → `io.opentelemetry.instrumentation.api.annotation.support.AnnotationReflectionHelper.bindAnnotationElementMethod(Ljava/lang/invoke/MethodHandles$Lookup;Ljava/lang/Class;Ljava/lang/String;Ljava/lang/Class;)Ljava/util/function/Function;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/reference_145/test_host_opentelemetry_instrumentation_annotations_support.py --no-cov`; scoped Ruff format/check and strict Mypy; assert independent expected outputs and FR logs.
- **Manual / Browser Verification:** Inspect consumer logs, lifecycle/failure outcomes and the declared infrastructure/JVM-only disposition.
- **Completion limit:** missing bodies/ownership/entitlement or independent expected outputs keep the task unchecked; static declarations do not establish SQX parity.


# 1.33 FEAT-HOST-OPENTELEMETRY-INSTRUMENTATION-API - opentelemetry-instrumentation-api-2.27.0.jar

## 1. Objective

- **Goal:** Resolve the consumed diagnostic, metadata or telemetry contract through approved host capabilities.
- **Context / Problem Solved:** Build 145 adds/changes this donor contribution; existing mock presentation and a filename do not establish functional support.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/libs/opentelemetry-instrumentation-api-2.27.0.jar`; 197 raw class entries; SHA-256 `e9928acbe8867fa84102c6a40c35266f39eef7f72c566884270565434b315c07`.
- **Inspected reference:** [opentelemetry-instrumentation-api-2.27.0.md](../../sqx/Libraries/opentelemetry-instrumentation-api-2.27.0.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/libs/opentelemetry-instrumentation-api-2.27.0.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/libs/opentelemetry-instrumentation-api-2.27.0.jar" io.opentelemetry.instrumentation.api.instrumenter.AttributesExtractor`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Ownership:** proposed `FEAT-HOST-OPENTELEMETRY-INSTRUMENTATION-API` and `FR-HOST-OPENTELEMETRY-INSTRUMENTATION-API-CONSUMED-CONTRACTS`; owner `app/host/README.md`. No application registration or implementation is implied.
- **Dependencies:** P00 evidence/ownership, P01 logging and P02 typed sessions/jobs/resources; phase-specific data/engine/project prerequisites from the delivery graph.
- **UI donors:** No standalone UI contribution is established for this infrastructure archive; trace its consuming host/domain feature and connect there.

## 3. File Changes

- **Create:** `app/host/diagnostics/vendor_contracts.py` — Resolve the consumed diagnostic, metadata or telemetry contract through approved host capabilities.
- **Modify:** `app/host/README.md` — ratify owning FEAT/FR contracts and status in the approved feature plan.
- **Create:** `tests/unit/reference_145/test_host_opentelemetry_instrumentation_api.py` — donor-derived normal, boundary, failure and FR-log checks.
- **Delete / Deprecate:** none; version/dependency retirement requires explicit approved disposition.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Ratify cohort, owning FEAT/FRs, target decisions, dependencies and exact write paths in the canonical plan.
- [ ] **Step 2:** Fingerprint the selected cohort; enumerate classes, methods and actual consumers.
- [ ] **Step 3:** Inspect consumed bodies and record normal/boundary/error contracts as descriptive FRs.
- [ ] **Step 4:** Ratify ownership and a reuse/adaptation/JVM-only disposition; implement only retained behavior.
- [ ] **Step 5:** Verify fixtures, invalid inputs, lifecycle/cancellation where applicable and explicit FR logs.
- [ ] **Step 6:** Expose the typed capability to its existing host/domain consumers; no standalone UI is established for this infrastructure JAR.
- [ ] **Step 7:** Record timestamped observations and walkthrough; update the matching master checklist row only when all requirements pass.

- [ ] **Step 8:** `FR-HOST-OPENTELEMETRY-INSTRUMENTATION-API-ATTRIBUTES-EXTRACTOR-CONTRACT` → `io.opentelemetry.instrumentation.api.instrumenter.AttributesExtractor`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-HOST-OPENTELEMETRY-INSTRUMENTATION-API-ATTRIBUTES-EXTRACTOR-ON-START` → `io.opentelemetry.instrumentation.api.instrumenter.AttributesExtractor.onStart(Lio/opentelemetry/api/common/AttributesBuilder;Lio/opentelemetry/context/Context;Ljava/lang/Object;)V`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 10:** `FR-HOST-OPENTELEMETRY-INSTRUMENTATION-API-ATTRIBUTES-EXTRACTOR-ON-END` → `io.opentelemetry.instrumentation.api.instrumenter.AttributesExtractor.onEnd(Lio/opentelemetry/api/common/AttributesBuilder;Lio/opentelemetry/context/Context;Ljava/lang/Object;Ljava/lang/Object;Ljava/lang/Throwable;)V`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/reference_145/test_host_opentelemetry_instrumentation_api.py --no-cov`; scoped Ruff format/check and strict Mypy; assert independent expected outputs and FR logs.
- **Manual / Browser Verification:** Inspect consumer logs, lifecycle/failure outcomes and the declared infrastructure/JVM-only disposition.
- **Completion limit:** missing bodies/ownership/entitlement or independent expected outputs keep the task unchecked; static declarations do not establish SQX parity.


# 1.34 FEAT-HOST-OPENTELEMETRY-INSTRUMENTATION-API-INCUBATOR - opentelemetry-instrumentation-api-incubator-2.27.0-alpha.jar

## 1. Objective

- **Goal:** Resolve the consumed diagnostic, metadata or telemetry contract through approved host capabilities.
- **Context / Problem Solved:** Build 145 adds/changes this donor contribution; existing mock presentation and a filename do not establish functional support.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/libs/opentelemetry-instrumentation-api-incubator-2.27.0-alpha.jar`; 154 raw class entries; SHA-256 `991a817ef0cf97aa53e35744c8ab47667526c665701ab3084af00336cec7e3ed`.
- **Inspected reference:** [opentelemetry-instrumentation-api-incubator-2.27.0-alpha.md](../../sqx/Libraries/opentelemetry-instrumentation-api-incubator-2.27.0-alpha.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/libs/opentelemetry-instrumentation-api-incubator-2.27.0-alpha.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/libs/opentelemetry-instrumentation-api-incubator-2.27.0-alpha.jar" io.opentelemetry.instrumentation.api.incubator.builder.internal.DefaultHttpClientInstrumenterBuilder`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Ownership:** proposed `FEAT-HOST-OPENTELEMETRY-INSTRUMENTATION-API-INCUBATOR` and `FR-HOST-OPENTELEMETRY-INSTRUMENTATION-API-INCUBATOR-CONSUMED-CONTRACTS`; owner `app/host/README.md`. No application registration or implementation is implied.
- **Dependencies:** P00 evidence/ownership, P01 logging and P02 typed sessions/jobs/resources; phase-specific data/engine/project prerequisites from the delivery graph.
- **UI donors:** No standalone UI contribution is established for this infrastructure archive; trace its consuming host/domain feature and connect there.

## 3. File Changes

- **Create:** `app/host/diagnostics/vendor_contracts.py` — Resolve the consumed diagnostic, metadata or telemetry contract through approved host capabilities.
- **Modify:** `app/host/README.md` — ratify owning FEAT/FR contracts and status in the approved feature plan.
- **Create:** `tests/unit/reference_145/test_host_opentelemetry_instrumentation_api_incubator.py` — donor-derived normal, boundary, failure and FR-log checks.
- **Delete / Deprecate:** none; version/dependency retirement requires explicit approved disposition.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Ratify cohort, owning FEAT/FRs, target decisions, dependencies and exact write paths in the canonical plan.
- [ ] **Step 2:** Fingerprint the selected cohort; enumerate classes, methods and actual consumers.
- [ ] **Step 3:** Inspect consumed bodies and record normal/boundary/error contracts as descriptive FRs.
- [ ] **Step 4:** Ratify ownership and a reuse/adaptation/JVM-only disposition; implement only retained behavior.
- [ ] **Step 5:** Verify fixtures, invalid inputs, lifecycle/cancellation where applicable and explicit FR logs.
- [ ] **Step 6:** Expose the typed capability to its existing host/domain consumers; no standalone UI is established for this infrastructure JAR.
- [ ] **Step 7:** Record timestamped observations and walkthrough; update the matching master checklist row only when all requirements pass.

- [ ] **Step 8:** `FR-HOST-OPENTELEMETRY-INSTRUMENTATION-API-INCUBATOR-DEFAULT-HTTP-CLIENT-INSTRUMENTER-BUILDER-CONTRACT` → `io.opentelemetry.instrumentation.api.incubator.builder.internal.DefaultHttpClientInstrumenterBuilder`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-HOST-OPENTELEMETRY-INSTRUMENTATION-API-INCUBATOR-DEFAULT-HTTP-CLIENT-INSTRUMENTER-BUILDER-CREATE` → `io.opentelemetry.instrumentation.api.incubator.builder.internal.DefaultHttpClientInstrumenterBuilder.create(Ljava/lang/String;Lio/opentelemetry/api/OpenTelemetry;Lio/opentelemetry/instrumentation/api/semconv/http/HttpClientAttributesGetter;)Lio/opentelemetry/instrumentation/api/incubator/builder/internal/DefaultHttpClientInstrumenterBuilder;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 10:** `FR-HOST-OPENTELEMETRY-INSTRUMENTATION-API-INCUBATOR-DEFAULT-HTTP-CLIENT-INSTRUMENTER-BUILDER-CREATE-EC34F39F` → `io.opentelemetry.instrumentation.api.incubator.builder.internal.DefaultHttpClientInstrumenterBuilder.create(Ljava/lang/String;Lio/opentelemetry/api/OpenTelemetry;Lio/opentelemetry/instrumentation/api/semconv/http/HttpClientAttributesGetter;Lio/opentelemetry/context/propagation/TextMapSetter;)Lio/opentelemetry/instrumentation/api/incubator/builder/internal/DefaultHttpClientInstrumenterBuilder;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/reference_145/test_host_opentelemetry_instrumentation_api_incubator.py --no-cov`; scoped Ruff format/check and strict Mypy; assert independent expected outputs and FR logs.
- **Manual / Browser Verification:** Inspect consumer logs, lifecycle/failure outcomes and the declared infrastructure/JVM-only disposition.
- **Completion limit:** missing bodies/ownership/entitlement or independent expected outputs keep the task unchecked; static declarations do not establish SQX parity.


# 1.35 FEAT-HOST-OPENTELEMETRY-REACTOR - opentelemetry-reactor-3.1-2.27.0-alpha.jar

## 1. Objective

- **Goal:** Resolve the consumed diagnostic, metadata or telemetry contract through approved host capabilities.
- **Context / Problem Solved:** Build 145 adds/changes this donor contribution; existing mock presentation and a filename do not establish functional support.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/libs/opentelemetry-reactor-3.1-2.27.0-alpha.jar`; 13 raw class entries; SHA-256 `be1db19d7861a5a878c2329fb7b2c9ad35a15d898460b6a1e70a399b95af54a5`.
- **Inspected reference:** [opentelemetry-reactor-3.1-2.27.0-alpha.md](../../sqx/Libraries/opentelemetry-reactor-3.1-2.27.0-alpha.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/libs/opentelemetry-reactor-3.1-2.27.0-alpha.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/libs/opentelemetry-reactor-3.1-2.27.0-alpha.jar" io.opentelemetry.instrumentation.reactor.v3_1.ContextPropagationOperator`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Ownership:** proposed `FEAT-HOST-OPENTELEMETRY-REACTOR` and `FR-HOST-OPENTELEMETRY-REACTOR-CONSUMED-CONTRACTS`; owner `app/host/README.md`. No application registration or implementation is implied.
- **Dependencies:** P00 evidence/ownership, P01 logging and P02 typed sessions/jobs/resources; phase-specific data/engine/project prerequisites from the delivery graph.
- **UI donors:** No standalone UI contribution is established for this infrastructure archive; trace its consuming host/domain feature and connect there.

## 3. File Changes

- **Create:** `app/host/diagnostics/vendor_contracts.py` — Resolve the consumed diagnostic, metadata or telemetry contract through approved host capabilities.
- **Modify:** `app/host/README.md` — ratify owning FEAT/FR contracts and status in the approved feature plan.
- **Create:** `tests/unit/reference_145/test_host_opentelemetry_reactor.py` — donor-derived normal, boundary, failure and FR-log checks.
- **Delete / Deprecate:** none; version/dependency retirement requires explicit approved disposition.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Ratify cohort, owning FEAT/FRs, target decisions, dependencies and exact write paths in the canonical plan.
- [ ] **Step 2:** Fingerprint the selected cohort; enumerate classes, methods and actual consumers.
- [ ] **Step 3:** Inspect consumed bodies and record normal/boundary/error contracts as descriptive FRs.
- [ ] **Step 4:** Ratify ownership and a reuse/adaptation/JVM-only disposition; implement only retained behavior.
- [ ] **Step 5:** Verify fixtures, invalid inputs, lifecycle/cancellation where applicable and explicit FR logs.
- [ ] **Step 6:** Expose the typed capability to its existing host/domain consumers; no standalone UI is established for this infrastructure JAR.
- [ ] **Step 7:** Record timestamped observations and walkthrough; update the matching master checklist row only when all requirements pass.

- [ ] **Step 8:** `FR-HOST-OPENTELEMETRY-REACTOR-CONTEXT-PROPAGATION-OPERATOR-CONTRACT` → `io.opentelemetry.instrumentation.reactor.v3_1.ContextPropagationOperator`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-HOST-OPENTELEMETRY-REACTOR-CONTEXT-PROPAGATION-OPERATOR-GET-CONTEXT-WRITE-METHOD` → `io.opentelemetry.instrumentation.reactor.v3_1.ContextPropagationOperator.getContextWriteMethod(Ljava/lang/Class;)Ljava/lang/invoke/MethodHandle;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 10:** `FR-HOST-OPENTELEMETRY-REACTOR-CONTEXT-PROPAGATION-OPERATOR-GET-SCHEDULERS-HOOK-METHOD` → `io.opentelemetry.instrumentation.reactor.v3_1.ContextPropagationOperator.getSchedulersHookMethod()Ljava/lang/invoke/MethodHandle;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/reference_145/test_host_opentelemetry_reactor.py --no-cov`; scoped Ruff format/check and strict Mypy; assert independent expected outputs and FR logs.
- **Manual / Browser Verification:** Inspect consumer logs, lifecycle/failure outcomes and the declared infrastructure/JVM-only disposition.
- **Completion limit:** missing bodies/ownership/entitlement or independent expected outputs keep the task unchecked; static declarations do not establish SQX parity.


# 1.36 FEAT-HOST-OPENTELEMETRY-SEMCONV - opentelemetry-semconv-1.40.0.jar

## 1. Objective

- **Goal:** Resolve the consumed diagnostic, metadata or telemetry contract through approved host capabilities.
- **Context / Problem Solved:** Build 145 adds/changes this donor contribution; existing mock presentation and a filename do not establish functional support.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/libs/opentelemetry-semconv-1.40.0.jar`; 25 raw class entries; SHA-256 `27eb65c14b91487cc25d35bd6f455193aac981d1ebe1b9472d5160cece573ba4`.
- **Inspected reference:** [opentelemetry-semconv-1.40.0.md](../../sqx/Libraries/opentelemetry-semconv-1.40.0.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/libs/opentelemetry-semconv-1.40.0.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/libs/opentelemetry-semconv-1.40.0.jar" io.opentelemetry.semconv.AttributeKeyTemplate`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Ownership:** proposed `FEAT-HOST-OPENTELEMETRY-SEMCONV` and `FR-HOST-OPENTELEMETRY-SEMCONV-CONSUMED-CONTRACTS`; owner `app/host/README.md`. No application registration or implementation is implied.
- **Dependencies:** P00 evidence/ownership, P01 logging and P02 typed sessions/jobs/resources; phase-specific data/engine/project prerequisites from the delivery graph.
- **UI donors:** No standalone UI contribution is established for this infrastructure archive; trace its consuming host/domain feature and connect there.

## 3. File Changes

- **Create:** `app/host/diagnostics/vendor_contracts.py` — Resolve the consumed diagnostic, metadata or telemetry contract through approved host capabilities.
- **Modify:** `app/host/README.md` — ratify owning FEAT/FR contracts and status in the approved feature plan.
- **Create:** `tests/unit/reference_145/test_host_opentelemetry_semconv.py` — donor-derived normal, boundary, failure and FR-log checks.
- **Delete / Deprecate:** none; version/dependency retirement requires explicit approved disposition.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Ratify cohort, owning FEAT/FRs, target decisions, dependencies and exact write paths in the canonical plan.
- [ ] **Step 2:** Fingerprint the selected cohort; enumerate classes, methods and actual consumers.
- [ ] **Step 3:** Inspect consumed bodies and record normal/boundary/error contracts as descriptive FRs.
- [ ] **Step 4:** Ratify ownership and a reuse/adaptation/JVM-only disposition; implement only retained behavior.
- [ ] **Step 5:** Verify fixtures, invalid inputs, lifecycle/cancellation where applicable and explicit FR logs.
- [ ] **Step 6:** Expose the typed capability to its existing host/domain consumers; no standalone UI is established for this infrastructure JAR.
- [ ] **Step 7:** Record timestamped observations and walkthrough; update the matching master checklist row only when all requirements pass.

- [ ] **Step 8:** `FR-HOST-OPENTELEMETRY-SEMCONV-ATTRIBUTE-KEY-TEMPLATE-CONTRACT` → `io.opentelemetry.semconv.AttributeKeyTemplate`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-HOST-OPENTELEMETRY-SEMCONV-ATTRIBUTE-KEY-TEMPLATE-STRING-KEY-TEMPLATE` → `io.opentelemetry.semconv.AttributeKeyTemplate.stringKeyTemplate(Ljava/lang/String;)Lio/opentelemetry/semconv/AttributeKeyTemplate;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 10:** `FR-HOST-OPENTELEMETRY-SEMCONV-ATTRIBUTE-KEY-TEMPLATE-STRING-ARRAY-KEY-TEMPLATE` → `io.opentelemetry.semconv.AttributeKeyTemplate.stringArrayKeyTemplate(Ljava/lang/String;)Lio/opentelemetry/semconv/AttributeKeyTemplate;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/reference_145/test_host_opentelemetry_semconv.py --no-cov`; scoped Ruff format/check and strict Mypy; assert independent expected outputs and FR logs.
- **Manual / Browser Verification:** Inspect consumer logs, lifecycle/failure outcomes and the declared infrastructure/JVM-only disposition.
- **Completion limit:** missing bodies/ownership/entitlement or independent expected outputs keep the task unchecked; static declarations do not establish SQX parity.


# 1.37 FEAT-HOST-OPENTELEMETRY-SEMCONV-INCUBATING - opentelemetry-semconv-incubating-1.40.0-alpha.jar

## 1. Objective

- **Goal:** Resolve the consumed diagnostic, metadata or telemetry contract through approved host capabilities.
- **Context / Problem Solved:** Build 145 adds/changes this donor contribution; existing mock presentation and a filename do not establish functional support.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/libs/opentelemetry-semconv-incubating-1.40.0-alpha.jar`; 227 raw class entries; SHA-256 `b73e725e970e3120670d3e64b8ff058fba495b0e8040b259b50dd38e030380e4`.
- **Inspected reference:** [opentelemetry-semconv-incubating-1.40.0-alpha.md](../../sqx/Libraries/opentelemetry-semconv-incubating-1.40.0-alpha.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/libs/opentelemetry-semconv-incubating-1.40.0-alpha.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/libs/opentelemetry-semconv-incubating-1.40.0-alpha.jar" io.opentelemetry.semconv.incubating.AndroidIncubatingAttributes`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Ownership:** proposed `FEAT-HOST-OPENTELEMETRY-SEMCONV-INCUBATING` and `FR-HOST-OPENTELEMETRY-SEMCONV-INCUBATING-CONSUMED-CONTRACTS`; owner `app/host/README.md`. No application registration or implementation is implied.
- **Dependencies:** P00 evidence/ownership, P01 logging and P02 typed sessions/jobs/resources; phase-specific data/engine/project prerequisites from the delivery graph.
- **UI donors:** No standalone UI contribution is established for this infrastructure archive; trace its consuming host/domain feature and connect there.

## 3. File Changes

- **Create:** `app/host/diagnostics/vendor_contracts.py` — Resolve the consumed diagnostic, metadata or telemetry contract through approved host capabilities.
- **Modify:** `app/host/README.md` — ratify owning FEAT/FR contracts and status in the approved feature plan.
- **Create:** `tests/unit/reference_145/test_host_opentelemetry_semconv_incubating.py` — donor-derived normal, boundary, failure and FR-log checks.
- **Delete / Deprecate:** none; version/dependency retirement requires explicit approved disposition.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Ratify cohort, owning FEAT/FRs, target decisions, dependencies and exact write paths in the canonical plan.
- [ ] **Step 2:** Fingerprint the selected cohort; enumerate classes, methods and actual consumers.
- [ ] **Step 3:** Inspect consumed bodies and record normal/boundary/error contracts as descriptive FRs.
- [ ] **Step 4:** Ratify ownership and a reuse/adaptation/JVM-only disposition; implement only retained behavior.
- [ ] **Step 5:** Verify fixtures, invalid inputs, lifecycle/cancellation where applicable and explicit FR logs.
- [ ] **Step 6:** Expose the typed capability to its existing host/domain consumers; no standalone UI is established for this infrastructure JAR.
- [ ] **Step 7:** Record timestamped observations and walkthrough; update the matching master checklist row only when all requirements pass.

- [ ] **Step 8:** `FR-HOST-OPENTELEMETRY-SEMCONV-INCUBATING-ANDROID-INCUBATING-ATTRIBUTES-CONTRACT` → `io.opentelemetry.semconv.incubating.AndroidIncubatingAttributes`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/reference_145/test_host_opentelemetry_semconv_incubating.py --no-cov`; scoped Ruff format/check and strict Mypy; assert independent expected outputs and FR logs.
- **Manual / Browser Verification:** Inspect consumer logs, lifecycle/failure outcomes and the declared infrastructure/JVM-only disposition.
- **Completion limit:** missing bodies/ownership/entitlement or independent expected outputs keep the task unchecked; static declarations do not establish SQX parity.


# 1.38 P01 integration — Boot the host with validated settings, structured logging and diagnostics

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

- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/web/DEBUGCONSOLE`. Inspect `SQX_145_REFERENCE_ROOT/internal/web/DEBUGCONSOLE/index.html`.
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
- **Create:** `ui/tests/unit/backend-connections/task-1-38.test.ts`
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

- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/task-1-38.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-host-foundation-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise Debug Console for 1.39; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.

## Phase completion gate

- [ ] Every applicable feature passed its own isolated real-host UI/backend case; no production mock fallback or unresolved required UI remains.

- [ ] Reconcile all allocated FEAT/FR dispositions, donor fixtures and ownership gaps.
- [ ] Run Ruff format/check and strict Mypy on the approved changed Python paths; verify branch-aware coverage ≥80% across retained application source at release.
- [ ] For affected UI: `npm --prefix ui run typecheck`, `npm --prefix ui run test`, `npm --prefix ui run build`.
- [ ] Record real workflow observations, timestamps, failure artifacts and remaining gaps in the walkthrough.
- [ ] Obtain the next task/phase approval; commits and external/destructive actions retain separate owner gates.

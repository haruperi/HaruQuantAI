# P02 — Host discovery, transport, jobs, resource services and persistence

- **Source:** `HARUQUANTAI_ROOT/docs/dev/V1/sqx-full-application-roadmap.md`; current-only source inventory `docs/dev/evidence/p00-inventory.json`.
- **Dependencies:** P01.
- **State:** proposed checklists; all execution, registrations and target contracts require task-level approval.
- **File labels:** existing paths are Modify; absent paths are Create; later shared edits name their earlier proposed owner.
- **Execution standard:** AGENTS.md plan → approval → implementation → tests → walkthrough; canonical Python docstrings, typed public APIs and explicit FR logs.
- **Clean room:** donor signatures guide behavioral research; independently written implementations; no proprietary source in evidence; no parity claim without independent validation.
- **Verification:** commands below are future tasks, not reported passes; isolated stores only; no live-store schema change/restore or Git mutation.
- **UI completion:** Applicable features finish with backend + retained UI connected; preserve layouts. Production mocks cannot substitute for capability execution; keep a task unchecked while transport/contracts or required controls are unresolved.
- **Connected verification:** Use an isolated real host and temporary data. Existing mock-only/browser-API-blocking suites are UI regressions, not connected acceptance. Run `npm --prefix ui run typecheck`, `npm --prefix ui run test`, `npm --prefix ui run build` after actual UI source changes.



- **Donor baseline:** SQX145 Dev 1 only; all source fingerprints and member seeds use `SQX_145_REFERENCE_ROOT`. Missing bodies remain prerequisites.
- **Scope:** 37 tasks; current archive allocations and resource/integration tasks only.

# 2.1 FEAT-HOST-CAFFEINE-2-8-5 - caffeine-2.8.5.jar

## 1. Objective

- **Goal:** Provide bounded host cache behavior for approved consumers.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Connect the frontend to typed host discovery, sessions, jobs and resources.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/libs/caffeine-2.8.5.jar`; 690 raw class entries; SHA-256 `814b15a9bf598e0fa854dd70ba9f6e03a413a97979de0c3f49317295e4352bc8`.
- **Inspected reference:** [caffeine-2.8.5.md](sqx/Libraries/caffeine-2.8.5.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/libs/caffeine-2.8.5.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/libs/caffeine-2.8.5.jar" com.github.benmanes.caffeine.SCQHeader`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/host/resources/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Cache/collection support; implement measured consumed policies via existing packages; downstream P03,P06,P09,P14.
- **Dependency:** qualify stdlib/declared packages; approve additions; classify JVM-only internals.

- **UI disposition:** Infrastructure only; no standalone UI component found in this library allocation. Its owned backend consumer feeds host connection through the phase integration gate; do not invent a library screen or direct plugin route.

## 3. File Changes

- **Create:** `app/host/resources/cache.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/host/resources/limits.py`
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/host/resources/README.md` (proposed earlier in FEAT-HOST-COMMONS-BEANUTILS)
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_host_caffeine_2_8_5.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/host_caffeine_2_8_5.json`
  - Store versioned paraphrased donor input/output fixtures.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Provide bounded host cache behavior for approved consumers; verify expiry, eviction, invalidation and concurrent lookup.
- [ ] **Step 4:** Wire qualified adapters to consumers; release resources on failure/shutdown.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Verify UI-facing consumer contract: Test this infrastructure through its declared backend/host consumer; expose failures through the owning domain envelope. The phase's connected UI gate verifies the observable workflow.


- [ ] **Step 7:** `FR-HOST-CAFFEINE-2-8-5-SCQHEADER-CONTRACT` → `com.github.benmanes.caffeine.SCQHeader`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_host_caffeine_2_8_5.py --no-cov`; expect expiry, eviction, invalidation and concurrent lookup; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture expiry, eviction, invalidation and concurrent lookup and visible failures.


# 2.2 FEAT-HOST-FASTUTIL - fastutil-8.3.0.jar

## 1. Objective

- **Goal:** Adapt consumed collection, string and utility contracts through Python primitives.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Connect the frontend to typed host discovery, sessions, jobs and resources.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/libs/fastutil-8.3.0.jar`; 10777 raw class entries; SHA-256 `77249efd4f23d039515bcc0bfc973cf65ee560da0a26a9db7fa2532e11deb4e7`.
- **Inspected reference:** [fastutil-8.3.0.md](sqx/Libraries/fastutil-8.3.0.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/libs/fastutil-8.3.0.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/libs/fastutil-8.3.0.jar" it.unimi.dsi.fastutil.AbstractIndirectPriorityQueue`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/host/resources/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Cache/collection support; implement measured consumed policies via existing packages; downstream P03,P06,P09,P14.
- **Dependency:** qualify stdlib/declared packages; approve additions; classify JVM-only internals.

- **UI disposition:** Infrastructure only; no standalone UI component found in this library allocation. Its owned backend consumer feeds host connection through the phase integration gate; do not invent a library screen or direct plugin route.

## 3. File Changes

- **Modify:** `app/host/resources/cache.py` (proposed earlier in FEAT-HOST-CAFFEINE-2-8-5)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/host/resources/limits.py` (proposed earlier in FEAT-HOST-CAFFEINE-2-8-5)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/host/resources/README.md` (proposed earlier in FEAT-HOST-COMMONS-BEANUTILS)
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_host_fastutil.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/host_fastutil.json`
  - Store versioned paraphrased donor input/output fixtures.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Adapt consumed collection, string and utility contracts through Python primitives; verify ordering, duplicate/null handling and bounded collection behavior.
- [ ] **Step 4:** Wire qualified adapters to consumers; release resources on failure/shutdown.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Verify UI-facing consumer contract: Test this infrastructure through its declared backend/host consumer; expose failures through the owning domain envelope. The phase's connected UI gate verifies the observable workflow.


- [ ] **Step 7:** `FR-HOST-FASTUTIL-ABSTRACT-INDIRECT-PRIORITY-QUEUE-CONTRACT` → `it.unimi.dsi.fastutil.AbstractIndirectPriorityQueue`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_host_fastutil.py --no-cov`; expect ordering, duplicate/null handling and bounded collection behavior; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture ordering, duplicate/null handling and bounded collection behavior and visible failures.


# 2.3 FEAT-HOST-FST - fst-2.57.jar

## 1. Objective

- **Goal:** Replace consumed Java object serialization/construction with typed document codecs.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Connect the frontend to typed host discovery, sessions, jobs and resources.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/libs/fst-2.57.jar`; 220 raw class entries; SHA-256 `ba57fdc0673ec3726921e5f113d906587d7f7000ba3981dfb79cc082929af3c1`.
- **Inspected reference:** [fst-2.57.md](sqx/Libraries/fst-2.57.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/libs/fst-2.57.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/libs/fst-2.57.jar" org.nustaq.kson.ArgTypes`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/host/persistence/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Store/serialization/archive dependencies; store ownership and formats require validation; downstream P03,P07,P08,P13.
- **Dependency:** qualify stdlib/declared packages; approve additions; classify JVM-only internals.

- **UI disposition:** Infrastructure only; no standalone UI component found in this library allocation. Its owned backend consumer feeds host connection through the phase integration gate; do not invent a library screen or direct plugin route.

## 3. File Changes

- **Create:** `app/host/persistence/store.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/host/persistence/transactions.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/host/persistence/retention.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/host/resources/archives.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/host/persistence/README.md`
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_host_fst.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/host_fst.json`
  - Store versioned paraphrased donor input/output fixtures.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Replace consumed Java object serialization/construction with typed document codecs; verify version compatibility, invalid object shape and round-trip identity.
- [ ] **Step 4:** Wire qualified adapters to consumers; release resources on failure/shutdown.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Verify UI-facing consumer contract: Test this infrastructure through its declared backend/host consumer; expose failures through the owning domain envelope. The phase's connected UI gate verifies the observable workflow.


- [ ] **Step 7:** `FR-HOST-FST-ARG-TYPES-CONTRACT` → `org.nustaq.kson.ArgTypes`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_host_fst.py --no-cov`; expect version compatibility, invalid object shape and round-trip identity; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture version compatibility, invalid object shape and round-trip identity and visible failures.


# 2.4 FEAT-HOST-GERONIMO-JSON - geronimo-json_1.0_spec-1.0-alpha-1.jar

## 1. Objective

- **Goal:** Encode and validate typed JSON documents without Java object coupling.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Connect the frontend to typed host discovery, sessions, jobs and resources.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/libs/geronimo-json_1.0_spec-1.0-alpha-1.jar`; 29 raw class entries; SHA-256 `9ad66832295ebfb21e168f29e9411924e13e233ee2ddc61b9a9b09a3f18dc183`.
- **Inspected reference:** [geronimo-json_1.0_spec-1.0-alpha-1.md](sqx/Libraries/geronimo-json_1.0_spec-1.0-alpha-1.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/libs/geronimo-json_1.0_spec-1.0-alpha-1.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/libs/geronimo-json_1.0_spec-1.0-alpha-1.jar" javax.json.Json`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/host/documents/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** JSON/XML codecs and schema validation used by public or saved documents; downstream P03,P07–P13,P17.
- **Dependency:** qualify stdlib/declared packages; approve additions; classify JVM-only internals.

- **UI disposition:** Infrastructure only; no standalone UI component found in this library allocation. Its owned backend consumer feeds host connection through the phase integration gate; do not invent a library screen or direct plugin route.

## 3. File Changes

- **Create:** `app/host/documents/json_codec.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/host/documents/xml_codec.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/host/documents/validation.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/host/documents/README.md`
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_host_geronimo_json.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/host_geronimo_json.json`
  - Store versioned paraphrased donor input/output fixtures.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Encode and validate typed JSON documents without Java object coupling; verify null/number handling, unknown fields and malformed payload.
- [ ] **Step 4:** Wire qualified adapters to consumers; release resources on failure/shutdown.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Verify UI-facing consumer contract: Test this infrastructure through its declared backend/host consumer; expose failures through the owning domain envelope. The phase's connected UI gate verifies the observable workflow.


- [ ] **Step 7:** `FR-HOST-GERONIMO-JSON-JSON-CONTRACT` → `javax.json.Json`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 8:** `FR-HOST-GERONIMO-JSON-JSON-CREATE-PARSER` → `javax.json.Json.createParser(Ljava/io/Reader;)Ljavax/json/stream/JsonParser;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-HOST-GERONIMO-JSON-JSON-CREATE-PARSER-BC4D2DE8` → `javax.json.Json.createParser(Ljava/io/InputStream;)Ljavax/json/stream/JsonParser;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_host_geronimo_json.py --no-cov`; expect null/number handling, unknown fields and malformed payload; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture null/number handling, unknown fields and malformed payload and visible failures.


# 2.5 FEAT-HOST-H2 - h2-1.3.149.jar

## 1. Objective

- **Goal:** Map donor persistence behavior to a ratified host store capability.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Connect the frontend to typed host discovery, sessions, jobs and resources.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/libs/h2-1.3.149.jar`; 499 raw class entries; SHA-256 `7c3e3b93ffaf617393126870be7f8e1708bbe8e05b931c51c638a8cb03f79a36`.
- **Inspected reference:** [h2-1.3.149.md](sqx/Libraries/h2-1.3.149.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/libs/h2-1.3.149.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/libs/h2-1.3.149.jar" org.h2.Driver`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/host/persistence/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Store/serialization/archive dependencies; store ownership and formats require validation; downstream P03,P07,P08,P13.
- **Dependency:** qualify stdlib/declared packages; approve additions; classify JVM-only internals.

- **UI disposition:** Infrastructure only; no standalone UI component found in this library allocation. Its owned backend consumer feeds host connection through the phase integration gate; do not invent a library screen or direct plugin route.

## 3. File Changes

- **Modify:** `app/host/persistence/store.py` (proposed earlier in FEAT-HOST-FST)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/host/persistence/transactions.py` (proposed earlier in FEAT-HOST-FST)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/host/persistence/retention.py` (proposed earlier in FEAT-HOST-FST)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/host/resources/archives.py` (proposed earlier in FEAT-HOST-FST)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/host/persistence/README.md` (proposed earlier in FEAT-HOST-FST)
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_host_h2.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/host_h2.json`
  - Store versioned paraphrased donor input/output fixtures.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Map donor persistence behavior to a ratified host store capability; verify transaction rollback, restart durability and retention in temporary stores.
- [ ] **Step 4:** Wire qualified adapters to consumers; release resources on failure/shutdown.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Verify UI-facing consumer contract: Test this infrastructure through its declared backend/host consumer; expose failures through the owning domain envelope. The phase's connected UI gate verifies the observable workflow.


- [ ] **Step 7:** `FR-HOST-H2-DRIVER-CONTRACT` → `org.h2.Driver`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 8:** `FR-HOST-H2-DRIVER-CONNECT` → `org.h2.Driver.connect(Ljava/lang/String;Ljava/util/Properties;)Ljava/sql/Connection;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-HOST-H2-DRIVER-ACCEPTS-URL` → `org.h2.Driver.acceptsURL(Ljava/lang/String;)Z`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_host_h2.py --no-cov`; expect transaction rollback, restart durability and retention in temporary stores; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture transaction rollback, restart durability and retention in temporary stores and visible failures.


# 2.6 FEAT-HOST-JACKSON-ANNOTATIONS - jackson-annotations-2.21.jar

## 1. Objective

- **Goal:** Encode and validate typed JSON documents without Java object coupling.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Connect the frontend to typed host discovery, sessions, jobs and resources.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/libs/jackson-annotations-2.21.jar`; 76 raw class entries; SHA-256 `53ca085f4a150f703f49e1aabd935bd03b43e1ea3d55d135438292af22cef56b`.
- **Inspected reference:** [jackson-annotations-2.21.md](sqx/Libraries/jackson-annotations-2.21.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/libs/jackson-annotations-2.21.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/libs/jackson-annotations-2.21.jar" com.fasterxml.jackson.annotation.JacksonAnnotation`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/host/documents/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** JSON/XML codecs and schema validation used by public or saved documents; downstream P03,P07–P13,P17.
- **Dependency:** qualify stdlib/declared packages; approve additions; classify JVM-only internals.

- **UI disposition:** Infrastructure only; no standalone UI component found in this library allocation. Its owned backend consumer feeds host connection through the phase integration gate; do not invent a library screen or direct plugin route.

## 3. File Changes

- **Modify:** `app/host/documents/json_codec.py` (proposed earlier in FEAT-HOST-GERONIMO-JSON)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/host/documents/xml_codec.py` (proposed earlier in FEAT-HOST-GERONIMO-JSON)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/host/documents/validation.py` (proposed earlier in FEAT-HOST-GERONIMO-JSON)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/host/documents/README.md` (proposed earlier in FEAT-HOST-GERONIMO-JSON)
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_host_jackson_annotations.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/host_jackson_annotations.json`
  - Store versioned paraphrased donor input/output fixtures.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Encode and validate typed JSON documents without Java object coupling; verify null/number handling, unknown fields and malformed payload.
- [ ] **Step 4:** Wire qualified adapters to consumers; release resources on failure/shutdown.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Verify UI-facing consumer contract: Test this infrastructure through its declared backend/host consumer; expose failures through the owning domain envelope. The phase's connected UI gate verifies the observable workflow.


- [ ] **Step 7:** `FR-HOST-JACKSON-ANNOTATIONS-JACKSON-ANNOTATION-CONTRACT` → `com.fasterxml.jackson.annotation.JacksonAnnotation`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_host_jackson_annotations.py --no-cov`; expect null/number handling, unknown fields and malformed payload; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture null/number handling, unknown fields and malformed payload and visible failures.


# 2.7 FEAT-HOST-JACKSON-CORE - jackson-core-2.21.1.jar

## 1. Objective

- **Goal:** Encode and validate typed JSON documents without Java object coupling.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Connect the frontend to typed host discovery, sessions, jobs and resources.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/libs/jackson-core-2.21.1.jar`; 221 raw class entries; SHA-256 `1edd5f2e49dca5f8e4519957c24b7b3050bd1c7ee883920da33cff031ff1f7c0`.
- **Inspected reference:** [jackson-core-2.21.1.md](sqx/Libraries/jackson-core-2.21.1.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/libs/jackson-core-2.21.1.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/libs/jackson-core-2.21.1.jar" com.fasterxml.jackson.core.Base64Variant`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/host/documents/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** JSON/XML codecs and schema validation used by public or saved documents; downstream P03,P07–P13,P17.
- **Dependency:** qualify stdlib/declared packages; approve additions; classify JVM-only internals.

- **UI disposition:** Infrastructure only; no standalone UI component found in this library allocation. Its owned backend consumer feeds host connection through the phase integration gate; do not invent a library screen or direct plugin route.

## 3. File Changes

- **Modify:** `app/host/documents/json_codec.py` (proposed earlier in FEAT-HOST-GERONIMO-JSON)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/host/documents/xml_codec.py` (proposed earlier in FEAT-HOST-GERONIMO-JSON)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/host/documents/validation.py` (proposed earlier in FEAT-HOST-GERONIMO-JSON)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/host/documents/README.md` (proposed earlier in FEAT-HOST-GERONIMO-JSON)
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_host_jackson_core.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/host_jackson_core.json`
  - Store versioned paraphrased donor input/output fixtures.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Encode and validate typed JSON documents without Java object coupling; verify null/number handling, unknown fields and malformed payload.
- [ ] **Step 4:** Wire qualified adapters to consumers; release resources on failure/shutdown.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Verify UI-facing consumer contract: Test this infrastructure through its declared backend/host consumer; expose failures through the owning domain envelope. The phase's connected UI gate verifies the observable workflow.


- [ ] **Step 7:** `FR-HOST-JACKSON-CORE-BASE64-VARIANT-CONTRACT` → `com.fasterxml.jackson.core.Base64Variant`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 8:** `FR-HOST-JACKSON-CORE-BASE64-VARIANT-WITH-PADDING-ALLOWED` → `com.fasterxml.jackson.core.Base64Variant.withPaddingAllowed()Lcom/fasterxml/jackson/core/Base64Variant;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-HOST-JACKSON-CORE-BASE64-VARIANT-WITH-PADDING-REQUIRED` → `com.fasterxml.jackson.core.Base64Variant.withPaddingRequired()Lcom/fasterxml/jackson/core/Base64Variant;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_host_jackson_core.py --no-cov`; expect null/number handling, unknown fields and malformed payload; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture null/number handling, unknown fields and malformed payload and visible failures.


# 2.8 FEAT-HOST-JACKSON-DATABIND - jackson-databind-2.21.1.jar

## 1. Objective

- **Goal:** Encode and validate typed JSON documents without Java object coupling.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Connect the frontend to typed host discovery, sessions, jobs and resources.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/libs/jackson-databind-2.21.1.jar`; 813 raw class entries; SHA-256 `b011eb5202d9ec889e27f1dcbdf6c63f06a76e7a16c0a1b30c6048d556c9a28e`.
- **Inspected reference:** [jackson-databind-2.21.1.md](sqx/Libraries/jackson-databind-2.21.1.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/libs/jackson-databind-2.21.1.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/libs/jackson-databind-2.21.1.jar" com.fasterxml.jackson.databind.AbstractTypeResolver`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/host/documents/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** JSON/XML codecs and schema validation used by public or saved documents; downstream P03,P07–P13,P17.
- **Dependency:** qualify stdlib/declared packages; approve additions; classify JVM-only internals.

- **UI disposition:** Infrastructure only; no standalone UI component found in this library allocation. Its owned backend consumer feeds host connection through the phase integration gate; do not invent a library screen or direct plugin route.

## 3. File Changes

- **Modify:** `app/host/documents/json_codec.py` (proposed earlier in FEAT-HOST-GERONIMO-JSON)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/host/documents/xml_codec.py` (proposed earlier in FEAT-HOST-GERONIMO-JSON)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/host/documents/validation.py` (proposed earlier in FEAT-HOST-GERONIMO-JSON)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/host/documents/README.md` (proposed earlier in FEAT-HOST-GERONIMO-JSON)
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_host_jackson_databind.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/host_jackson_databind.json`
  - Store versioned paraphrased donor input/output fixtures.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Encode and validate typed JSON documents without Java object coupling; verify null/number handling, unknown fields and malformed payload.
- [ ] **Step 4:** Wire qualified adapters to consumers; release resources on failure/shutdown.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Verify UI-facing consumer contract: Test this infrastructure through its declared backend/host consumer; expose failures through the owning domain envelope. The phase's connected UI gate verifies the observable workflow.


- [ ] **Step 7:** `FR-HOST-JACKSON-DATABIND-ABSTRACT-TYPE-RESOLVER-CONTRACT` → `com.fasterxml.jackson.databind.AbstractTypeResolver`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 8:** `FR-HOST-JACKSON-DATABIND-ABSTRACT-TYPE-RESOLVER-FIND-TYPE-MAPPING` → `com.fasterxml.jackson.databind.AbstractTypeResolver.findTypeMapping(Lcom/fasterxml/jackson/databind/DeserializationConfig;Lcom/fasterxml/jackson/databind/JavaType;)Lcom/fasterxml/jackson/databind/JavaType;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-HOST-JACKSON-DATABIND-ABSTRACT-TYPE-RESOLVER-RESOLVE-ABSTRACT-TYPE` → `com.fasterxml.jackson.databind.AbstractTypeResolver.resolveAbstractType(Lcom/fasterxml/jackson/databind/DeserializationConfig;Lcom/fasterxml/jackson/databind/JavaType;)Lcom/fasterxml/jackson/databind/JavaType;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_host_jackson_databind.py --no-cov`; expect null/number handling, unknown fields and malformed payload; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture null/number handling, unknown fields and malformed payload and visible failures.


# 2.9 FEAT-HOST-JDOM - jdom-2.0.0.jar

## 1. Objective

- **Goal:** Parse and preserve supported XML document fields.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Connect the frontend to typed host discovery, sessions, jobs and resources.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/libs/jdom-2.0.0.jar`; 185 raw class entries; SHA-256 `4a8817acf7f719e4bcfbcaf96250defff4cc87b4c20634c6eaa96ee04fd38bfe`.
- **Inspected reference:** [jdom-2.0.0.md](sqx/Libraries/jdom-2.0.0.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/libs/jdom-2.0.0.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/libs/jdom-2.0.0.jar" org.jdom2.Element`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/host/documents/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** JSON/XML codecs and schema validation used by public or saved documents; downstream P03,P07–P13,P17.
- **Dependency:** qualify stdlib/declared packages; approve additions; classify JVM-only internals.

- **UI disposition:** Infrastructure only; no standalone UI component found in this library allocation. Its owned backend consumer feeds host connection through the phase integration gate; do not invent a library screen or direct plugin route.

## 3. File Changes

- **Modify:** `app/host/documents/json_codec.py` (proposed earlier in FEAT-HOST-GERONIMO-JSON)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/host/documents/xml_codec.py` (proposed earlier in FEAT-HOST-GERONIMO-JSON)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/host/documents/validation.py` (proposed earlier in FEAT-HOST-GERONIMO-JSON)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/host/documents/README.md` (proposed earlier in FEAT-HOST-GERONIMO-JSON)
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_host_jdom.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/host_jdom.json`
  - Store versioned paraphrased donor input/output fixtures.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Parse and preserve supported XML document fields; verify namespaces, encoding, rejected unsafe constructs and lossless unknown fields.
- [ ] **Step 4:** Wire qualified adapters to consumers; release resources on failure/shutdown.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Verify UI-facing consumer contract: Test this infrastructure through its declared backend/host consumer; expose failures through the owning domain envelope. The phase's connected UI gate verifies the observable workflow.


- [ ] **Step 7:** `FR-HOST-JDOM-ELEMENT-CONTRACT` → `org.jdom2.Element`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 8:** `FR-HOST-JDOM-ELEMENT-GET-NAME` → `org.jdom2.Element.getName()Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-HOST-JDOM-ELEMENT-SET-NAME` → `org.jdom2.Element.setName(Ljava/lang/String;)Lorg/jdom2/Element;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_host_jdom.py --no-cov`; expect namespaces, encoding, rejected unsafe constructs and lossless unknown fields; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture namespaces, encoding, rejected unsafe constructs and lossless unknown fields and visible failures.


# 2.10 FEAT-HOST-JETTY-ALL-UBER - jetty-all-uber.jar

## 1. Objective

- **Goal:** Adapt server, TLS and protocol lifecycle through declared FastAPI/Uvicorn capabilities.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Connect the frontend to typed host discovery, sessions, jobs and resources.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/libs/jetty-all-uber.jar`; 1703 raw class entries; SHA-256 `7ce8b3a1ed9852b9d7b16ba10a9db9a4fb42151845fd3fa3f9f45ac2ee416a98`.
- **Inspected reference:** [jetty-all-uber.md](sqx/Libraries/jetty-all-uber.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/libs/jetty-all-uber.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/libs/jetty-all-uber.jar" org.eclipse.jetty.server.Server`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/host/transport/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Web-server lifecycle, handler mounting and optional TLS transports; downstream P03–P18.
- **Dependency:** qualify stdlib/declared packages; approve additions; classify JVM-only internals.

- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/web/app`; `SQX_145_REFERENCE_ROOT/internal/web/common`. Inspect `SQX_145_REFERENCE_ROOT/internal/web/app/login/LoginService.js`; `SQX_145_REFERENCE_ROOT/internal/web/common/templates.html`.
- **Existing UI connection:** host connection; proposed shared consumer; verify the exact existing control and public contract before implementation. Target `ui/app/host/HostConnection.tsx`; wire session/readiness, capability availability and server-owned shell state.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Modify:** `app/host/transport/server.py` (proposed shared TLS owner; current-source qualification required)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/host/transport/routes.py` (proposed shared TLS owner; current-source qualification required)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/host/transport/session.py` (proposed shared TLS owner; current-source qualification required)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/host/transport/events.py` (proposed shared TLS owner; current-source qualification required)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/host/transport/README.md` (proposed shared TLS owner; current-source qualification required)
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_host_jetty_all_uber.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/host_jetty_all_uber.json`
  - Store versioned paraphrased donor input/output fixtures.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/host/HostConnection.tsx`
  - Display session/readiness, capability availability and server-owned shell state from backend responses; preserve layout.
- **Modify:** `ui/app/host/hostSettings.ts`
  - Display session/readiness, capability availability and server-owned shell state from backend responses; preserve layout.
- **Modify:** `ui/app/host/transport.ts`
  - Display session/readiness, capability availability and server-owned shell state from backend responses; preserve layout.
- **Modify:** `ui/app/host/store.ts`
  - Replace affected mock job/resource authority with server projections; preserve selection/view state.
- **Create:** `ui/tests/unit/backend-connections/feat-host-jetty-all-uber.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-host-services-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Adapt server, TLS and protocol lifecycle through declared FastAPI/Uvicorn capabilities; verify startup failure, protocol compatibility, connection cleanup and TLS configuration.
- [ ] **Step 4:** Wire qualified adapters to consumers; release resources on failure/shutdown.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Connect retained UI: Ratify the feature-owned wire contract; bind session/readiness, capability availability and server-owned shell state to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 7:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.


- [ ] **Step 8:** `FR-HOST-JETTY-ALL-UBER-SERVER-CONTRACT` → `org.eclipse.jetty.server.Server`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-HOST-JETTY-ALL-UBER-SERVER-IS-DRY-RUN` → `org.eclipse.jetty.server.Server.isDryRun()Z`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 10:** `FR-HOST-JETTY-ALL-UBER-SERVER-SET-DRY-RUN` → `org.eclipse.jetty.server.Server.setDryRun(Z)V`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_host_jetty_all_uber.py --no-cov`; expect startup failure, protocol compatibility, connection cleanup and TLS configuration; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture startup failure, protocol compatibility, connection cleanup and TLS configuration and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-host-jetty-all-uber.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-host-services-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise host connection for FEAT-HOST-JETTY-ALL-UBER; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.


# 2.11 FEAT-HOST-JSON-SCHEMA-VALIDATOR - json-schema-validator-2.0.0.jar

## 1. Objective

- **Goal:** Validate versioned resource documents against ratified schemas.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Connect the frontend to typed host discovery, sessions, jobs and resources.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/libs/json-schema-validator-2.0.0.jar`; 313 raw class entries; SHA-256 `ee940241043ae01801df5954bc3744bf723c449ff0da719f97e1b9a6889739d7`.
- **Inspected reference:** [json-schema-validator-2.0.0.md](sqx/Libraries/json-schema-validator-2.0.0.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/libs/json-schema-validator-2.0.0.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/libs/json-schema-validator-2.0.0.jar" com.networknt.org.apache.commons.validator.routines.DomainValidator`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/host/documents/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** JSON/XML codecs and schema validation used by public or saved documents; downstream P03,P07–P13,P17.
- **Dependency:** qualify stdlib/declared packages; approve additions; classify JVM-only internals.

- **UI disposition:** Infrastructure only; no standalone UI component found in this library allocation. Its owned backend consumer feeds host connection through the phase integration gate; do not invent a library screen or direct plugin route.

## 3. File Changes

- **Modify:** `app/host/documents/json_codec.py` (proposed earlier in FEAT-HOST-GERONIMO-JSON)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/host/documents/xml_codec.py` (proposed earlier in FEAT-HOST-GERONIMO-JSON)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/host/documents/validation.py` (proposed earlier in FEAT-HOST-GERONIMO-JSON)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/host/documents/README.md` (proposed earlier in FEAT-HOST-GERONIMO-JSON)
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_host_json_schema_validator.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/host_json_schema_validator.json`
  - Store versioned paraphrased donor input/output fixtures.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Validate versioned resource documents against ratified schemas; verify required fields, schema versions and actionable validation errors.
- [ ] **Step 4:** Wire qualified adapters to consumers; release resources on failure/shutdown.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Verify UI-facing consumer contract: Test this infrastructure through its declared backend/host consumer; expose failures through the owning domain envelope. The phase's connected UI gate verifies the observable workflow.


- [ ] **Step 7:** `FR-HOST-JSON-SCHEMA-VALIDATOR-DOMAIN-VALIDATOR-CONTRACT` → `com.networknt.org.apache.commons.validator.routines.DomainValidator`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 8:** `FR-HOST-JSON-SCHEMA-VALIDATOR-DOMAIN-VALIDATOR-ARRAY-CONTAINS` → `com.networknt.org.apache.commons.validator.routines.DomainValidator.arrayContains([Ljava/lang/String;Ljava/lang/String;)Z`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-HOST-JSON-SCHEMA-VALIDATOR-DOMAIN-VALIDATOR-GET-INSTANCE` → `com.networknt.org.apache.commons.validator.routines.DomainValidator.getInstance()Lcom/networknt/org/apache/commons/validator/routines/DomainValidator;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_host_json_schema_validator.py --no-cov`; expect required fields, schema versions and actionable validation errors; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture required fields, schema versions and actionable validation errors and visible failures.


# 2.12 FEAT-HOST-JSON - json-20150729.jar

## 1. Objective

- **Goal:** Deliver the consumed json capability in host.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Connect the frontend to typed host discovery, sessions, jobs and resources.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/libs/json-20150729.jar`; 18 raw class entries; SHA-256 `38c21b9c3d6d24919cd15d027d20afab0a019ac9205f7ed9083b32bdd42a2353`.
- **Inspected reference:** [json-20150729.md](sqx/Libraries/json-20150729.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/libs/json-20150729.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/libs/json-20150729.jar" org.json.JSONObject`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/host/documents/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** JSON/XML codecs and schema validation used by public or saved documents; downstream P03,P07–P13,P17.
- **Dependency:** qualify stdlib/declared packages; approve additions; classify JVM-only internals.

- **UI disposition:** Infrastructure only; no standalone UI component found in this library allocation. Its owned backend consumer feeds host connection through the phase integration gate; do not invent a library screen or direct plugin route.

## 3. File Changes

- **Modify:** `app/host/documents/json_codec.py` (proposed earlier in FEAT-HOST-GERONIMO-JSON)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/host/documents/xml_codec.py` (proposed earlier in FEAT-HOST-GERONIMO-JSON)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/host/documents/validation.py` (proposed earlier in FEAT-HOST-GERONIMO-JSON)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/host/documents/README.md` (proposed earlier in FEAT-HOST-GERONIMO-JSON)
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_host_json.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/host_json.json`
  - Store versioned paraphrased donor input/output fixtures.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Deliver the consumed json capability in host; verify login/readiness/preferences, event correlation, restart durability and cancellation.
- [ ] **Step 4:** Wire qualified adapters to consumers; release resources on failure/shutdown.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Verify UI-facing consumer contract: Test this infrastructure through its declared backend/host consumer; expose failures through the owning domain envelope. The phase's connected UI gate verifies the observable workflow.


- [ ] **Step 7:** `FR-HOST-JSON-JSONOBJECT-CONTRACT` → `org.json.JSONObject`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 8:** `FR-HOST-JSON-JSONOBJECT-ACCUMULATE` → `org.json.JSONObject.accumulate(Ljava/lang/String;Ljava/lang/Object;)Lorg/json/JSONObject;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-HOST-JSON-JSONOBJECT-APPEND` → `org.json.JSONObject.append(Ljava/lang/String;Ljava/lang/Object;)Lorg/json/JSONObject;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_host_json.py --no-cov`; expect login/readiness/preferences, event correlation, restart durability and cancellation; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture login/readiness/preferences, event correlation, restart durability and cancellation and visible failures.


# 2.13 FEAT-HOST-JSPF-CORE - jspf.core.jar

## 1. Objective

- **Goal:** Discover and bind typed plugin capabilities with lifecycle ownership.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Connect the frontend to typed host discovery, sessions, jobs and resources.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/libs/jspf.core.jar`; 295 raw class entries; SHA-256 `94f287909bc8fb0970819f165cf091b08f1787053c9875824b6deb9a12ea0185`.
- **Inspected reference:** [jspf.core.md](sqx/Libraries/jspf.core.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/libs/jspf.core.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/libs/jspf.core.jar" net.xeoh.plugins.base.PluginManager`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/host/discovery/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Typed discovery and registration infrastructure; downstream P03–P18.
- **Dependency:** qualify stdlib/declared packages; approve additions; classify JVM-only internals.

- **UI disposition:** Infrastructure only; no standalone UI component found in this library allocation. Its owned backend consumer feeds host connection through the phase integration gate; do not invent a library screen or direct plugin route.

## 3. File Changes

- **Create:** `app/host/discovery/contracts.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/host/discovery/registry.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/host/discovery/loader.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/host/discovery/README.md`
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_host_jspf_core.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/host_jspf_core.json`
  - Store versioned paraphrased donor input/output fixtures.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Discover and bind typed plugin capabilities with lifecycle ownership; verify duplicate registration, compatibility failure and mount/unmount cleanup.
- [ ] **Step 4:** Wire qualified adapters to consumers; release resources on failure/shutdown.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Verify UI-facing consumer contract: Test this infrastructure through its declared backend/host consumer; expose failures through the owning domain envelope. The phase's connected UI gate verifies the observable workflow.


- [ ] **Step 7:** `FR-HOST-JSPF-CORE-PLUGIN-MANAGER-CONTRACT` → `net.xeoh.plugins.base.PluginManager`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 8:** `FR-HOST-JSPF-CORE-PLUGIN-MANAGER-ADD-PLUGINS-FROM` → `net.xeoh.plugins.base.PluginManager.addPluginsFrom(Ljava/net/URI;[Lnet/xeoh/plugins/base/options/AddPluginsFromOption;)V`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-HOST-JSPF-CORE-PLUGIN-MANAGER-GET-PLUGIN` → `net.xeoh.plugins.base.PluginManager.getPlugin(Ljava/lang/Class;[Lnet/xeoh/plugins/base/options/GetPluginOption;)Lnet/xeoh/plugins/base/Plugin;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_host_jspf_core.py --no-cov`; expect duplicate registration, compatibility failure and mount/unmount cleanup; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture duplicate registration, compatibility failure and mount/unmount cleanup and visible failures.


# 2.14 FEAT-HOST-OBJENESIS - objenesis-2.5.1.jar

## 1. Objective

- **Goal:** Replace consumed Java object serialization/construction with typed document codecs.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Connect the frontend to typed host discovery, sessions, jobs and resources.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/libs/objenesis-2.5.1.jar`; 43 raw class entries; SHA-256 `b043f03e466752f7f03e2326a3b13a49b7c649f8f2a2dc87715827e24f73d9c6`.
- **Inspected reference:** [objenesis-2.5.1.md](sqx/Libraries/objenesis-2.5.1.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/libs/objenesis-2.5.1.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/libs/objenesis-2.5.1.jar" org.objenesis.Objenesis`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/host/persistence/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Store/serialization/archive dependencies; store ownership and formats require validation; downstream P03,P07,P08,P13.
- **Dependency:** qualify stdlib/declared packages; approve additions; classify JVM-only internals.

- **UI disposition:** Infrastructure only; no standalone UI component found in this library allocation. Its owned backend consumer feeds host connection through the phase integration gate; do not invent a library screen or direct plugin route.

## 3. File Changes

- **Modify:** `app/host/persistence/store.py` (proposed earlier in FEAT-HOST-FST)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/host/persistence/transactions.py` (proposed earlier in FEAT-HOST-FST)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/host/persistence/retention.py` (proposed earlier in FEAT-HOST-FST)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/host/resources/archives.py` (proposed earlier in FEAT-HOST-FST)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/host/persistence/README.md` (proposed earlier in FEAT-HOST-FST)
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_host_objenesis.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/host_objenesis.json`
  - Store versioned paraphrased donor input/output fixtures.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Replace consumed Java object serialization/construction with typed document codecs; verify version compatibility, invalid object shape and round-trip identity.
- [ ] **Step 4:** Wire qualified adapters to consumers; release resources on failure/shutdown.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Verify UI-facing consumer contract: Test this infrastructure through its declared backend/host consumer; expose failures through the owning domain envelope. The phase's connected UI gate verifies the observable workflow.


- [ ] **Step 7:** `FR-HOST-OBJENESIS-OBJENESIS-CONTRACT` → `org.objenesis.Objenesis`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 8:** `FR-HOST-OBJENESIS-OBJENESIS-NEW-INSTANCE` → `org.objenesis.Objenesis.newInstance(Ljava/lang/Class;)Ljava/lang/Object;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-HOST-OBJENESIS-OBJENESIS-GET-INSTANTIATOR-OF` → `org.objenesis.Objenesis.getInstantiatorOf(Ljava/lang/Class;)Lorg/objenesis/instantiator/ObjectInstantiator;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_host_objenesis.py --no-cov`; expect version compatibility, invalid object shape and round-trip identity; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture version compatibility, invalid object shape and round-trip identity and visible failures.


# 2.15 FEAT-HOST-REACTIVE-STREAMS - reactive-streams-1.0.4.jar

## 1. Objective

- **Goal:** Implement bounded owned event streams and cancellation.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Connect the frontend to typed host discovery, sessions, jobs and resources.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/libs/reactive-streams-1.0.4.jar`; 13 raw class entries; SHA-256 `f75ca597789b3dac58f61857b9ac2e1034a68fa672db35055a8fb4509e325f28`.
- **Inspected reference:** [reactive-streams-1.0.4.md](sqx/Libraries/reactive-streams-1.0.4.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/libs/reactive-streams-1.0.4.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/libs/reactive-streams-1.0.4.jar" org.reactivestreams.FlowAdapters`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/host/jobs/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Jobs and event/backpressure infrastructure; exact reactive consumers unresolved; downstream P04,P06,P09–P16.
- **Dependency:** qualify stdlib/declared packages; approve additions; classify JVM-only internals.

- **UI disposition:** Infrastructure only; no standalone UI component found in this library allocation. Its owned backend consumer feeds host connection through the phase integration gate; do not invent a library screen or direct plugin route.

## 3. File Changes

- **Create:** `app/host/jobs/contracts.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/host/jobs/scheduler.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/host/jobs/events.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/host/jobs/README.md`
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_host_reactive_streams.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/host_reactive_streams.json`
  - Store versioned paraphrased donor input/output fixtures.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Implement bounded owned event streams and cancellation; verify ordering, backpressure, subscriber loss and resource release.
- [ ] **Step 4:** Wire qualified adapters to consumers; release resources on failure/shutdown.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Verify UI-facing consumer contract: Test this infrastructure through its declared backend/host consumer; expose failures through the owning domain envelope. The phase's connected UI gate verifies the observable workflow.


- [ ] **Step 7:** `FR-HOST-REACTIVE-STREAMS-FLOW-ADAPTERS-CONTRACT` → `org.reactivestreams.FlowAdapters`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 8:** `FR-HOST-REACTIVE-STREAMS-FLOW-ADAPTERS-TO-PUBLISHER` → `org.reactivestreams.FlowAdapters.toPublisher(Ljava/util/concurrent/Flow$Publisher;)Lorg/reactivestreams/Publisher;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-HOST-REACTIVE-STREAMS-FLOW-ADAPTERS-TO-FLOW-PUBLISHER` → `org.reactivestreams.FlowAdapters.toFlowPublisher(Lorg/reactivestreams/Publisher;)Ljava/util/concurrent/Flow$Publisher;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_host_reactive_streams.py --no-cov`; expect ordering, backpressure, subscriber loss and resource release; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture ordering, backpressure, subscriber loss and resource release and visible failures.


# 2.16 FEAT-HOST-REACTOR-CORE - reactor-core-3.8.2.jar

## 1. Objective

- **Goal:** Implement bounded owned event streams and cancellation.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Connect the frontend to typed host discovery, sessions, jobs and resources.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/libs/reactor-core-3.8.2.jar`; 948 raw class entries; SHA-256 `e800681657a370c6416ae66b3060bf2fe87d3a3107bd7ce932acac0c2e002d97`.
- **Inspected reference:** [reactor-core-3.8.2.md](sqx/Libraries/reactor-core-3.8.2.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/libs/reactor-core-3.8.2.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/libs/reactor-core-3.8.2.jar" reactor.adapter.JdkFlowAdapter`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/host/jobs/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Jobs and event/backpressure infrastructure; exact reactive consumers unresolved; downstream P04,P06,P09–P16.
- **Dependency:** qualify stdlib/declared packages; approve additions; classify JVM-only internals.

- **UI disposition:** Infrastructure only; no standalone UI component found in this library allocation. Its owned backend consumer feeds host connection through the phase integration gate; do not invent a library screen or direct plugin route.

## 3. File Changes

- **Modify:** `app/host/jobs/contracts.py` (proposed earlier in FEAT-HOST-REACTIVE-STREAMS)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/host/jobs/scheduler.py` (proposed earlier in FEAT-HOST-REACTIVE-STREAMS)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/host/jobs/events.py` (proposed earlier in FEAT-HOST-REACTIVE-STREAMS)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/host/jobs/README.md` (proposed earlier in FEAT-HOST-REACTIVE-STREAMS)
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_host_reactor_core.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/host_reactor_core.json`
  - Store versioned paraphrased donor input/output fixtures.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Implement bounded owned event streams and cancellation; verify ordering, backpressure, subscriber loss and resource release.
- [ ] **Step 4:** Wire qualified adapters to consumers; release resources on failure/shutdown.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Verify UI-facing consumer contract: Test this infrastructure through its declared backend/host consumer; expose failures through the owning domain envelope. The phase's connected UI gate verifies the observable workflow.


- [ ] **Step 7:** `FR-HOST-REACTOR-CORE-JDK-FLOW-ADAPTER-CONTRACT` → `reactor.adapter.JdkFlowAdapter`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 8:** `FR-HOST-REACTOR-CORE-JDK-FLOW-ADAPTER-PUBLISHER-TO-FLOW-PUBLISHER` → `reactor.adapter.JdkFlowAdapter.publisherToFlowPublisher(Lorg/reactivestreams/Publisher;)Ljava/util/concurrent/Flow$Publisher;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-HOST-REACTOR-CORE-JDK-FLOW-ADAPTER-FLOW-PUBLISHER-TO-FLUX` → `reactor.adapter.JdkFlowAdapter.flowPublisherToFlux(Ljava/util/concurrent/Flow$Publisher;)Lreactor/core/publisher/Flux;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_host_reactor_core.py --no-cov`; expect ordering, backpressure, subscriber loss and resource release; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture ordering, backpressure, subscriber loss and resource release and visible failures.


# 2.17 FEAT-HOST-SQLITE-JDBC - sqlite-jdbc-3.51.2.0.jar

## 1. Objective

- **Goal:** Map donor persistence behavior to a ratified host store capability.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Connect the frontend to typed host discovery, sessions, jobs and resources.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/libs/sqlite-jdbc-3.51.2.0.jar`; 129 raw class entries; SHA-256 `5454be00f3a04b4d67ef6179121aa900a904da53b9cbffea742d548d737f0ebc`.
- **Inspected reference:** [sqlite-jdbc-3.51.2.0.md](sqx/Libraries/sqlite-jdbc-3.51.2.0.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/libs/sqlite-jdbc-3.51.2.0.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/libs/sqlite-jdbc-3.51.2.0.jar" org.sqlite.JDBC`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/host/persistence/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Store/serialization/archive dependencies; store ownership and formats require validation; downstream P03,P07,P08,P13.
- **Dependency:** qualify stdlib/declared packages; approve additions; classify JVM-only internals.

- **UI disposition:** Infrastructure only; no standalone UI component found in this library allocation. Its owned backend consumer feeds host connection through the phase integration gate; do not invent a library screen or direct plugin route.

## 3. File Changes

- **Modify:** `app/host/persistence/store.py` (proposed earlier in FEAT-HOST-FST)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/host/persistence/transactions.py` (proposed earlier in FEAT-HOST-FST)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/host/persistence/retention.py` (proposed earlier in FEAT-HOST-FST)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/host/resources/archives.py` (proposed earlier in FEAT-HOST-FST)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/host/persistence/README.md` (proposed earlier in FEAT-HOST-FST)
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_host_sqlite_jdbc.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/host_sqlite_jdbc.json`
  - Store versioned paraphrased donor input/output fixtures.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Map donor persistence behavior to a ratified host store capability; verify transaction rollback, restart durability and retention in temporary stores.
- [ ] **Step 4:** Wire qualified adapters to consumers; release resources on failure/shutdown.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Verify UI-facing consumer contract: Test this infrastructure through its declared backend/host consumer; expose failures through the owning domain envelope. The phase's connected UI gate verifies the observable workflow.


- [ ] **Step 7:** `FR-HOST-SQLITE-JDBC-JDBC-CONTRACT` → `org.sqlite.JDBC`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 8:** `FR-HOST-SQLITE-JDBC-JDBC-GET-MAJOR-VERSION` → `org.sqlite.JDBC.getMajorVersion()I`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-HOST-SQLITE-JDBC-JDBC-GET-MINOR-VERSION` → `org.sqlite.JDBC.getMinorVersion()I`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_host_sqlite_jdbc.py --no-cov`; expect transaction rollback, restart durability and retention in temporary stores; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture transaction rollback, restart durability and retention in temporary stores and visible failures.


# 2.18 FEAT-HOST-ZIP4J - zip4j-1.3.2.jar

## 1. Objective

- **Goal:** Read/write supported bounded archives through host resource services.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Connect the frontend to typed host discovery, sessions, jobs and resources.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/libs/zip4j-1.3.2.jar`; 60 raw class entries; SHA-256 `c67098d430c574311432728ebd4c7c45672f9ccf5c64702eb6afb8816c22ad08`.
- **Inspected reference:** [zip4j-1.3.2.md](sqx/Libraries/zip4j-1.3.2.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/libs/zip4j-1.3.2.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/libs/zip4j-1.3.2.jar" net.lingala.zip4j.core.HeaderReader`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/host/persistence/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Store/serialization/archive dependencies; store ownership and formats require validation; downstream P03,P07,P08,P13.
- **Dependency:** qualify stdlib/declared packages; approve additions; classify JVM-only internals.

- **UI disposition:** Infrastructure only; no standalone UI component found in this library allocation. Its owned backend consumer feeds host connection through the phase integration gate; do not invent a library screen or direct plugin route.

## 3. File Changes

- **Modify:** `app/host/persistence/store.py` (proposed earlier in FEAT-HOST-FST)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/host/persistence/transactions.py` (proposed earlier in FEAT-HOST-FST)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/host/persistence/retention.py` (proposed earlier in FEAT-HOST-FST)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/host/resources/archives.py` (proposed earlier in FEAT-HOST-FST)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/host/persistence/README.md` (proposed earlier in FEAT-HOST-FST)
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_host_zip4j.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/host_zip4j.json`
  - Store versioned paraphrased donor input/output fixtures.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Read/write supported bounded archives through host resource services; verify compression round trip, expansion limits, corrupt entry and traversal rejection.
- [ ] **Step 4:** Wire qualified adapters to consumers; release resources on failure/shutdown.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Verify UI-facing consumer contract: Test this infrastructure through its declared backend/host consumer; expose failures through the owning domain envelope. The phase's connected UI gate verifies the observable workflow.


- [ ] **Step 7:** `FR-HOST-ZIP4J-HEADER-READER-CONTRACT` → `net.lingala.zip4j.core.HeaderReader`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 8:** `FR-HOST-ZIP4J-HEADER-READER-READ-ALL-HEADERS` → `net.lingala.zip4j.core.HeaderReader.readAllHeaders()Lnet/lingala/zip4j/model/ZipModel;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-HOST-ZIP4J-HEADER-READER-READ-ALL-HEADERS-8F2A56CA` → `net.lingala.zip4j.core.HeaderReader.readAllHeaders(Ljava/lang/String;)Lnet/lingala/zip4j/model/ZipModel;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_host_zip4j.py --no-cov`; expect compression round trip, expansion limits, corrupt entry and traversal rejection; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture compression round trip, expansion limits, corrupt entry and traversal rejection and visible failures.


# 2.19 FEAT-HOST-CLASSMATE - classmate-1.7.0.jar

## 1. Objective

- **Goal:** Provide the consumed serialization, archive or HTTP contract through the host resource boundary.
- **Context / Problem Solved:** Build 145 adds/changes this donor contribution; existing mock presentation and a filename do not establish functional support.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/libs/classmate-1.7.0.jar`; 44 raw class entries; SHA-256 `cb868f231c5cceb89d795ea00e6e1b7a93b8f4ac1ce1d8be76dde322dff4a046`.
- **Inspected reference:** [classmate-1.7.0.md](sqx/Libraries/classmate-1.7.0.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/libs/classmate-1.7.0.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/libs/classmate-1.7.0.jar" com.fasterxml.classmate.AnnotationConfiguration`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Ownership:** proposed `FEAT-HOST-CLASSMATE` and `FR-HOST-CLASSMATE-CONSUMED-CONTRACTS`; owner `app/host/README.md`. No application registration or implementation is implied.
- **Dependencies:** P00 evidence/ownership, P01 logging and P02 typed sessions/jobs/resources; phase-specific data/engine/project prerequisites from the delivery graph.
- **UI donors:** No standalone UI contribution is established for this infrastructure archive; trace its consuming host/domain feature and connect there.

## 3. File Changes

- **Create:** `app/host/resources/vendor_contracts.py` — Provide the consumed serialization, archive or HTTP contract through the host resource boundary.
- **Modify:** `app/host/README.md` — ratify owning FEAT/FR contracts and status in the approved feature plan.
- **Create:** `tests/unit/reference_145/test_host_classmate.py` — donor-derived normal, boundary, failure and FR-log checks.
- **Delete / Deprecate:** none; version/dependency retirement requires explicit approved disposition.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Ratify cohort, owning FEAT/FRs, target decisions, dependencies and exact write paths in the canonical plan.
- [ ] **Step 2:** Fingerprint the selected cohort; enumerate classes, methods and actual consumers.
- [ ] **Step 3:** Inspect consumed bodies and record normal/boundary/error contracts as descriptive FRs.
- [ ] **Step 4:** Ratify ownership and a reuse/adaptation/JVM-only disposition; implement only retained behavior.
- [ ] **Step 5:** Verify fixtures, invalid inputs, lifecycle/cancellation where applicable and explicit FR logs.
- [ ] **Step 6:** Expose the typed capability to its existing host/domain consumers; no standalone UI is established for this infrastructure JAR.
- [ ] **Step 7:** Record timestamped observations and walkthrough; update the matching master checklist row only when all requirements pass.

- [ ] **Step 8:** `FR-HOST-CLASSMATE-ANNOTATION-CONFIGURATION-CONTRACT` → `com.fasterxml.classmate.AnnotationConfiguration`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-HOST-CLASSMATE-ANNOTATION-CONFIGURATION-GET-INCLUSION-FOR-CLASS` → `com.fasterxml.classmate.AnnotationConfiguration.getInclusionForClass(Ljava/lang/Class;)Lcom/fasterxml/classmate/AnnotationInclusion;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 10:** `FR-HOST-CLASSMATE-ANNOTATION-CONFIGURATION-GET-INCLUSION-FOR-CONSTRUCTOR` → `com.fasterxml.classmate.AnnotationConfiguration.getInclusionForConstructor(Ljava/lang/Class;)Lcom/fasterxml/classmate/AnnotationInclusion;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/reference_145/test_host_classmate.py --no-cov`; scoped Ruff format/check and strict Mypy; assert independent expected outputs and FR logs.
- **Manual / Browser Verification:** Inspect consumer logs, lifecycle/failure outcomes and the declared infrastructure/JVM-only disposition.
- **Completion limit:** missing bodies/ownership/entitlement or independent expected outputs keep the task unchecked; static declarations do not establish SQX parity.


# 2.20 FEAT-HOST-COMMONS-COMPRESS - commons-compress-1.27.1.jar

## 1. Objective

- **Goal:** Provide the consumed serialization, archive or HTTP contract through the host resource boundary.
- **Context / Problem Solved:** Build 145 adds/changes this donor contribution; existing mock presentation and a filename do not establish functional support.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/libs/commons-compress-1.27.1.jar`; 573 raw class entries; SHA-256 `293d80f54b536b74095dcd7ea3cf0a29bbfc3402519281332495f4420d370d16`.
- **Inspected reference:** [commons-compress-1.27.1.md](sqx/Libraries/commons-compress-1.27.1.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/libs/commons-compress-1.27.1.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/libs/commons-compress-1.27.1.jar" org.apache.commons.compress.MemoryLimitException`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Ownership:** proposed `FEAT-HOST-COMMONS-COMPRESS` and `FR-HOST-COMMONS-COMPRESS-CONSUMED-CONTRACTS`; owner `app/host/README.md`. No application registration or implementation is implied.
- **Dependencies:** P00 evidence/ownership, P01 logging and P02 typed sessions/jobs/resources; phase-specific data/engine/project prerequisites from the delivery graph.
- **UI donors:** No standalone UI contribution is established for this infrastructure archive; trace its consuming host/domain feature and connect there.

## 3. File Changes

- **Create:** `app/host/resources/vendor_contracts.py` — Provide the consumed serialization, archive or HTTP contract through the host resource boundary.
- **Modify:** `app/host/README.md` — ratify owning FEAT/FR contracts and status in the approved feature plan.
- **Create:** `tests/unit/reference_145/test_host_commons_compress.py` — donor-derived normal, boundary, failure and FR-log checks.
- **Delete / Deprecate:** none; version/dependency retirement requires explicit approved disposition.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Ratify cohort, owning FEAT/FRs, target decisions, dependencies and exact write paths in the canonical plan.
- [ ] **Step 2:** Fingerprint the selected cohort; enumerate classes, methods and actual consumers.
- [ ] **Step 3:** Inspect consumed bodies and record normal/boundary/error contracts as descriptive FRs.
- [ ] **Step 4:** Ratify ownership and a reuse/adaptation/JVM-only disposition; implement only retained behavior.
- [ ] **Step 5:** Verify fixtures, invalid inputs, lifecycle/cancellation where applicable and explicit FR logs.
- [ ] **Step 6:** Expose the typed capability to its existing host/domain consumers; no standalone UI is established for this infrastructure JAR.
- [ ] **Step 7:** Record timestamped observations and walkthrough; update the matching master checklist row only when all requirements pass.

- [ ] **Step 8:** `FR-HOST-COMMONS-COMPRESS-MEMORY-LIMIT-EXCEPTION-CONTRACT` → `org.apache.commons.compress.MemoryLimitException`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-HOST-COMMONS-COMPRESS-MEMORY-LIMIT-EXCEPTION-BUILD-MESSAGE` → `org.apache.commons.compress.MemoryLimitException.buildMessage(JI)Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 10:** `FR-HOST-COMMONS-COMPRESS-MEMORY-LIMIT-EXCEPTION-GET-MEMORY-LIMIT-IN-KB` → `org.apache.commons.compress.MemoryLimitException.getMemoryLimitInKb()I`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/reference_145/test_host_commons_compress.py --no-cov`; scoped Ruff format/check and strict Mypy; assert independent expected outputs and FR logs.
- **Manual / Browser Verification:** Inspect consumer logs, lifecycle/failure outcomes and the declared infrastructure/JVM-only disposition.
- **Completion limit:** missing bodies/ownership/entitlement or independent expected outputs keep the task unchecked; static declarations do not establish SQX parity.


# 2.21 FEAT-HOST-ITU - itu-1.14.0.jar

## 1. Objective

- **Goal:** Provide the consumed serialization, archive or HTTP contract through the host resource boundary.
- **Context / Problem Solved:** Build 145 adds/changes this donor contribution; existing mock presentation and a filename do not establish functional support.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/libs/itu-1.14.0.jar`; 34 raw class entries; SHA-256 `5cf40ab0cc77828ab2b875b1f3ecd71c8295d7721933476abc2e08fddcea164a`.
- **Inspected reference:** [itu-1.14.0.md](sqx/Libraries/itu-1.14.0.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/libs/itu-1.14.0.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/libs/itu-1.14.0.jar" com.ethlo.time.DateTime`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Ownership:** proposed `FEAT-HOST-ITU` and `FR-HOST-ITU-CONSUMED-CONTRACTS`; owner `app/host/README.md`. No application registration or implementation is implied.
- **Dependencies:** P00 evidence/ownership, P01 logging and P02 typed sessions/jobs/resources; phase-specific data/engine/project prerequisites from the delivery graph.
- **UI donors:** No standalone UI contribution is established for this infrastructure archive; trace its consuming host/domain feature and connect there.

## 3. File Changes

- **Create:** `app/host/resources/vendor_contracts.py` — Provide the consumed serialization, archive or HTTP contract through the host resource boundary.
- **Modify:** `app/host/README.md` — ratify owning FEAT/FR contracts and status in the approved feature plan.
- **Create:** `tests/unit/reference_145/test_host_itu.py` — donor-derived normal, boundary, failure and FR-log checks.
- **Delete / Deprecate:** none; version/dependency retirement requires explicit approved disposition.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Ratify cohort, owning FEAT/FRs, target decisions, dependencies and exact write paths in the canonical plan.
- [ ] **Step 2:** Fingerprint the selected cohort; enumerate classes, methods and actual consumers.
- [ ] **Step 3:** Inspect consumed bodies and record normal/boundary/error contracts as descriptive FRs.
- [ ] **Step 4:** Ratify ownership and a reuse/adaptation/JVM-only disposition; implement only retained behavior.
- [ ] **Step 5:** Verify fixtures, invalid inputs, lifecycle/cancellation where applicable and explicit FR logs.
- [ ] **Step 6:** Expose the typed capability to its existing host/domain consumers; no standalone UI is established for this infrastructure JAR.
- [ ] **Step 7:** Record timestamped observations and walkthrough; update the matching master checklist row only when all requirements pass.

- [ ] **Step 8:** `FR-HOST-ITU-DATE-TIME-CONTRACT` → `com.ethlo.time.DateTime`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-HOST-ITU-DATE-TIME-OF` → `com.ethlo.time.DateTime.of(IIIIIILcom/ethlo/time/TimezoneOffset;)Lcom/ethlo/time/DateTime;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 10:** `FR-HOST-ITU-DATE-TIME-OF-FF723AC2` → `com.ethlo.time.DateTime.of(IIIIIIILcom/ethlo/time/TimezoneOffset;I)Lcom/ethlo/time/DateTime;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/reference_145/test_host_itu.py --no-cov`; scoped Ruff format/check and strict Mypy; assert independent expected outputs and FR logs.
- **Manual / Browser Verification:** Inspect consumer logs, lifecycle/failure outcomes and the declared infrastructure/JVM-only disposition.
- **Completion limit:** missing bodies/ownership/entitlement or independent expected outputs keep the task unchecked; static declarations do not establish SQX parity.


# 2.22 FEAT-HOST-JACKSON-DATAFORMAT-YAML - jackson-dataformat-yaml-2.21.1.jar

## 1. Objective

- **Goal:** Provide the consumed serialization, archive or HTTP contract through the host resource boundary.
- **Context / Problem Solved:** Build 145 adds/changes this donor contribution; existing mock presentation and a filename do not establish functional support.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/libs/jackson-dataformat-yaml-2.21.1.jar`; 24 raw class entries; SHA-256 `5c94fa55d4b93bd4ea9ac6f2cf4928ff50822d1c43e521e715d3abf23031a06d`.
- **Inspected reference:** [jackson-dataformat-yaml-2.21.1.md](sqx/Libraries/jackson-dataformat-yaml-2.21.1.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/libs/jackson-dataformat-yaml-2.21.1.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/libs/jackson-dataformat-yaml-2.21.1.jar" com.fasterxml.jackson.dataformat.yaml.JacksonYAMLParseException`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Ownership:** proposed `FEAT-HOST-JACKSON-DATAFORMAT-YAML` and `FR-HOST-JACKSON-DATAFORMAT-YAML-CONSUMED-CONTRACTS`; owner `app/host/README.md`. No application registration or implementation is implied.
- **Dependencies:** P00 evidence/ownership, P01 logging and P02 typed sessions/jobs/resources; phase-specific data/engine/project prerequisites from the delivery graph.
- **UI donors:** No standalone UI contribution is established for this infrastructure archive; trace its consuming host/domain feature and connect there.

## 3. File Changes

- **Create:** `app/host/resources/vendor_contracts.py` — Provide the consumed serialization, archive or HTTP contract through the host resource boundary.
- **Modify:** `app/host/README.md` — ratify owning FEAT/FR contracts and status in the approved feature plan.
- **Create:** `tests/unit/reference_145/test_host_jackson_dataformat_yaml.py` — donor-derived normal, boundary, failure and FR-log checks.
- **Delete / Deprecate:** none; version/dependency retirement requires explicit approved disposition.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Ratify cohort, owning FEAT/FRs, target decisions, dependencies and exact write paths in the canonical plan.
- [ ] **Step 2:** Fingerprint the selected cohort; enumerate classes, methods and actual consumers.
- [ ] **Step 3:** Inspect consumed bodies and record normal/boundary/error contracts as descriptive FRs.
- [ ] **Step 4:** Ratify ownership and a reuse/adaptation/JVM-only disposition; implement only retained behavior.
- [ ] **Step 5:** Verify fixtures, invalid inputs, lifecycle/cancellation where applicable and explicit FR logs.
- [ ] **Step 6:** Expose the typed capability to its existing host/domain consumers; no standalone UI is established for this infrastructure JAR.
- [ ] **Step 7:** Record timestamped observations and walkthrough; update the matching master checklist row only when all requirements pass.

- [ ] **Step 8:** `FR-HOST-JACKSON-DATAFORMAT-YAML-JACKSON-YAMLPARSE-EXCEPTION-CONTRACT` → `com.fasterxml.jackson.dataformat.yaml.JacksonYAMLParseException`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/reference_145/test_host_jackson_dataformat_yaml.py --no-cov`; scoped Ruff format/check and strict Mypy; assert independent expected outputs and FR logs.
- **Manual / Browser Verification:** Inspect consumer logs, lifecycle/failure outcomes and the declared infrastructure/JVM-only disposition.
- **Completion limit:** missing bodies/ownership/entitlement or independent expected outputs keep the task unchecked; static declarations do not establish SQX parity.


# 2.23 FEAT-HOST-JACKSON-DATATYPE-JSR310 - jackson-datatype-jsr310-2.21.1.jar

## 1. Objective

- **Goal:** Provide the consumed serialization, archive or HTTP contract through the host resource boundary.
- **Context / Problem Solved:** Build 145 adds/changes this donor contribution; existing mock presentation and a filename do not establish functional support.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/libs/jackson-datatype-jsr310-2.21.1.jar`; 65 raw class entries; SHA-256 `4d63378b0a6b53733f086ebd301023ba211b9387e417bd584a5400320cd08b8d`.
- **Inspected reference:** [jackson-datatype-jsr310-2.21.1.md](sqx/Libraries/jackson-datatype-jsr310-2.21.1.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/libs/jackson-datatype-jsr310-2.21.1.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/libs/jackson-datatype-jsr310-2.21.1.jar" com.fasterxml.jackson.datatype.jsr310.DecimalUtils`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Ownership:** proposed `FEAT-HOST-JACKSON-DATATYPE-JSR310` and `FR-HOST-JACKSON-DATATYPE-JSR310-CONSUMED-CONTRACTS`; owner `app/host/README.md`. No application registration or implementation is implied.
- **Dependencies:** P00 evidence/ownership, P01 logging and P02 typed sessions/jobs/resources; phase-specific data/engine/project prerequisites from the delivery graph.
- **UI donors:** No standalone UI contribution is established for this infrastructure archive; trace its consuming host/domain feature and connect there.

## 3. File Changes

- **Create:** `app/host/resources/vendor_contracts.py` — Provide the consumed serialization, archive or HTTP contract through the host resource boundary.
- **Modify:** `app/host/README.md` — ratify owning FEAT/FR contracts and status in the approved feature plan.
- **Create:** `tests/unit/reference_145/test_host_jackson_datatype_jsr310.py` — donor-derived normal, boundary, failure and FR-log checks.
- **Delete / Deprecate:** none; version/dependency retirement requires explicit approved disposition.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Ratify cohort, owning FEAT/FRs, target decisions, dependencies and exact write paths in the canonical plan.
- [ ] **Step 2:** Fingerprint the selected cohort; enumerate classes, methods and actual consumers.
- [ ] **Step 3:** Inspect consumed bodies and record normal/boundary/error contracts as descriptive FRs.
- [ ] **Step 4:** Ratify ownership and a reuse/adaptation/JVM-only disposition; implement only retained behavior.
- [ ] **Step 5:** Verify fixtures, invalid inputs, lifecycle/cancellation where applicable and explicit FR logs.
- [ ] **Step 6:** Expose the typed capability to its existing host/domain consumers; no standalone UI is established for this infrastructure JAR.
- [ ] **Step 7:** Record timestamped observations and walkthrough; update the matching master checklist row only when all requirements pass.

- [ ] **Step 8:** `FR-HOST-JACKSON-DATATYPE-JSR310-DECIMAL-UTILS-CONTRACT` → `com.fasterxml.jackson.datatype.jsr310.DecimalUtils`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-HOST-JACKSON-DATATYPE-JSR310-DECIMAL-UTILS-TO-DECIMAL` → `com.fasterxml.jackson.datatype.jsr310.DecimalUtils.toDecimal(JI)Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 10:** `FR-HOST-JACKSON-DATATYPE-JSR310-DECIMAL-UTILS-TO-BIG-DECIMAL` → `com.fasterxml.jackson.datatype.jsr310.DecimalUtils.toBigDecimal(JI)Ljava/math/BigDecimal;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/reference_145/test_host_jackson_datatype_jsr310.py --no-cov`; scoped Ruff format/check and strict Mypy; assert independent expected outputs and FR logs.
- **Manual / Browser Verification:** Inspect consumer logs, lifecycle/failure outcomes and the declared infrastructure/JVM-only disposition.
- **Completion limit:** missing bodies/ownership/entitlement or independent expected outputs keep the task unchecked; static declarations do not establish SQX parity.


# 2.24 FEAT-HOST-JERICHO-HTML - jericho-html-3.3.jar

## 1. Objective

- **Goal:** Provide the consumed serialization, archive or HTTP contract through the host resource boundary.
- **Context / Problem Solved:** Build 145 adds/changes this donor contribution; existing mock presentation and a filename do not establish functional support.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/libs/jericho-html-3.3.jar`; 156 raw class entries; SHA-256 `149f74929589c67b76efe85804c2c285ec1cc5ab6fcc1c2bc99694475a1656d6`.
- **Inspected reference:** [jericho-html-3.3.md](sqx/Libraries/jericho-html-3.3.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/libs/jericho-html-3.3.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/libs/jericho-html-3.3.jar" net.htmlparser.jericho.Attribute`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Ownership:** proposed `FEAT-HOST-JERICHO-HTML` and `FR-HOST-JERICHO-HTML-CONSUMED-CONTRACTS`; owner `app/host/README.md`. No application registration or implementation is implied.
- **Dependencies:** P00 evidence/ownership, P01 logging and P02 typed sessions/jobs/resources; phase-specific data/engine/project prerequisites from the delivery graph.
- **UI donors:** No standalone UI contribution is established for this infrastructure archive; trace its consuming host/domain feature and connect there.

## 3. File Changes

- **Create:** `app/host/resources/vendor_contracts.py` — Provide the consumed serialization, archive or HTTP contract through the host resource boundary.
- **Modify:** `app/host/README.md` — ratify owning FEAT/FR contracts and status in the approved feature plan.
- **Create:** `tests/unit/reference_145/test_host_jericho_html.py` — donor-derived normal, boundary, failure and FR-log checks.
- **Delete / Deprecate:** none; version/dependency retirement requires explicit approved disposition.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Ratify cohort, owning FEAT/FRs, target decisions, dependencies and exact write paths in the canonical plan.
- [ ] **Step 2:** Fingerprint the selected cohort; enumerate classes, methods and actual consumers.
- [ ] **Step 3:** Inspect consumed bodies and record normal/boundary/error contracts as descriptive FRs.
- [ ] **Step 4:** Ratify ownership and a reuse/adaptation/JVM-only disposition; implement only retained behavior.
- [ ] **Step 5:** Verify fixtures, invalid inputs, lifecycle/cancellation where applicable and explicit FR logs.
- [ ] **Step 6:** Expose the typed capability to its existing host/domain consumers; no standalone UI is established for this infrastructure JAR.
- [ ] **Step 7:** Record timestamped observations and walkthrough; update the matching master checklist row only when all requirements pass.

- [ ] **Step 8:** `FR-HOST-JERICHO-HTML-ATTRIBUTE-CONTRACT` → `net.htmlparser.jericho.Attribute`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-HOST-JERICHO-HTML-ATTRIBUTE-GET-KEY` → `net.htmlparser.jericho.Attribute.getKey()Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 10:** `FR-HOST-JERICHO-HTML-ATTRIBUTE-GET-NAME` → `net.htmlparser.jericho.Attribute.getName()Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/reference_145/test_host_jericho_html.py --no-cov`; scoped Ruff format/check and strict Mypy; assert independent expected outputs and FR logs.
- **Manual / Browser Verification:** Inspect consumer logs, lifecycle/failure outcomes and the declared infrastructure/JVM-only disposition.
- **Completion limit:** missing bodies/ownership/entitlement or independent expected outputs keep the task unchecked; static declarations do not establish SQX parity.


# 2.25 FEAT-HOST-JOHNZON-CORE - johnzon-core-0.9.5.jar

## 1. Objective

- **Goal:** Provide the consumed serialization, archive or HTTP contract through the host resource boundary.
- **Context / Problem Solved:** Build 145 adds/changes this donor contribution; existing mock presentation and a filename do not establish functional support.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/libs/johnzon-core-0.9.5.jar`; 59 raw class entries; SHA-256 `f3854251548ce8c8d5d1c6975732fbf7b5a5f2dfb7a78d3c1138351e1f362378`.
- **Inspected reference:** [johnzon-core-0.9.5.md](sqx/Libraries/johnzon-core-0.9.5.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/libs/johnzon-core-0.9.5.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/libs/johnzon-core-0.9.5.jar" org.apache.johnzon.core.AbstractJsonFactory`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Ownership:** proposed `FEAT-HOST-JOHNZON-CORE` and `FR-HOST-JOHNZON-CORE-CONSUMED-CONTRACTS`; owner `app/host/README.md`. No application registration or implementation is implied.
- **Dependencies:** P00 evidence/ownership, P01 logging and P02 typed sessions/jobs/resources; phase-specific data/engine/project prerequisites from the delivery graph.
- **UI donors:** No standalone UI contribution is established for this infrastructure archive; trace its consuming host/domain feature and connect there.

## 3. File Changes

- **Create:** `app/host/resources/vendor_contracts.py` — Provide the consumed serialization, archive or HTTP contract through the host resource boundary.
- **Modify:** `app/host/README.md` — ratify owning FEAT/FR contracts and status in the approved feature plan.
- **Create:** `tests/unit/reference_145/test_host_johnzon_core.py` — donor-derived normal, boundary, failure and FR-log checks.
- **Delete / Deprecate:** none; version/dependency retirement requires explicit approved disposition.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Ratify cohort, owning FEAT/FRs, target decisions, dependencies and exact write paths in the canonical plan.
- [ ] **Step 2:** Fingerprint the selected cohort; enumerate classes, methods and actual consumers.
- [ ] **Step 3:** Inspect consumed bodies and record normal/boundary/error contracts as descriptive FRs.
- [ ] **Step 4:** Ratify ownership and a reuse/adaptation/JVM-only disposition; implement only retained behavior.
- [ ] **Step 5:** Verify fixtures, invalid inputs, lifecycle/cancellation where applicable and explicit FR logs.
- [ ] **Step 6:** Expose the typed capability to its existing host/domain consumers; no standalone UI is established for this infrastructure JAR.
- [ ] **Step 7:** Record timestamped observations and walkthrough; update the matching master checklist row only when all requirements pass.

- [ ] **Step 8:** `FR-HOST-JOHNZON-CORE-ABSTRACT-JSON-FACTORY-CONTRACT` → `org.apache.johnzon.core.AbstractJsonFactory`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-HOST-JOHNZON-CORE-ABSTRACT-JSON-FACTORY-GET-BUFFER-PROVIDER` → `org.apache.johnzon.core.AbstractJsonFactory.getBufferProvider()Lorg/apache/johnzon/core/BufferStrategy;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 10:** `FR-HOST-JOHNZON-CORE-ABSTRACT-JSON-FACTORY-GET-INT` → `org.apache.johnzon.core.AbstractJsonFactory.getInt(Ljava/lang/String;I)I`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/reference_145/test_host_johnzon_core.py --no-cov`; scoped Ruff format/check and strict Mypy; assert independent expected outputs and FR logs.
- **Manual / Browser Verification:** Inspect consumer logs, lifecycle/failure outcomes and the declared infrastructure/JVM-only disposition.
- **Completion limit:** missing bodies/ownership/entitlement or independent expected outputs keep the task unchecked; static declarations do not establish SQX parity.


# 2.26 FEAT-HOST-JSONSCHEMA-GENERATOR - jsonschema-generator-4.38.0.jar

## 1. Objective

- **Goal:** Provide the consumed serialization, archive or HTTP contract through the host resource boundary.
- **Context / Problem Solved:** Build 145 adds/changes this donor contribution; existing mock presentation and a filename do not establish functional support.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/libs/jsonschema-generator-4.38.0.jar`; 69 raw class entries; SHA-256 `ade4aeb301db4028ac6bcba016c31405677e37aae6eebaf13c99de3fdb3531b4`.
- **Inspected reference:** [jsonschema-generator-4.38.0.md](sqx/Libraries/jsonschema-generator-4.38.0.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/libs/jsonschema-generator-4.38.0.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/libs/jsonschema-generator-4.38.0.jar" com.github.victools.jsonschema.generator.FieldScope`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Ownership:** proposed `FEAT-HOST-JSONSCHEMA-GENERATOR` and `FR-HOST-JSONSCHEMA-GENERATOR-CONSUMED-CONTRACTS`; owner `app/host/README.md`. No application registration or implementation is implied.
- **Dependencies:** P00 evidence/ownership, P01 logging and P02 typed sessions/jobs/resources; phase-specific data/engine/project prerequisites from the delivery graph.
- **UI donors:** No standalone UI contribution is established for this infrastructure archive; trace its consuming host/domain feature and connect there.

## 3. File Changes

- **Create:** `app/host/resources/vendor_contracts.py` — Provide the consumed serialization, archive or HTTP contract through the host resource boundary.
- **Modify:** `app/host/README.md` — ratify owning FEAT/FR contracts and status in the approved feature plan.
- **Create:** `tests/unit/reference_145/test_host_jsonschema_generator.py` — donor-derived normal, boundary, failure and FR-log checks.
- **Delete / Deprecate:** none; version/dependency retirement requires explicit approved disposition.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Ratify cohort, owning FEAT/FRs, target decisions, dependencies and exact write paths in the canonical plan.
- [ ] **Step 2:** Fingerprint the selected cohort; enumerate classes, methods and actual consumers.
- [ ] **Step 3:** Inspect consumed bodies and record normal/boundary/error contracts as descriptive FRs.
- [ ] **Step 4:** Ratify ownership and a reuse/adaptation/JVM-only disposition; implement only retained behavior.
- [ ] **Step 5:** Verify fixtures, invalid inputs, lifecycle/cancellation where applicable and explicit FR logs.
- [ ] **Step 6:** Expose the typed capability to its existing host/domain consumers; no standalone UI is established for this infrastructure JAR.
- [ ] **Step 7:** Record timestamped observations and walkthrough; update the matching master checklist row only when all requirements pass.

- [ ] **Step 8:** `FR-HOST-JSONSCHEMA-GENERATOR-FIELD-SCOPE-CONTRACT` → `com.github.victools.jsonschema.generator.FieldScope`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-HOST-JSONSCHEMA-GENERATOR-FIELD-SCOPE-WITH-OVERRIDDEN-TYPE` → `com.github.victools.jsonschema.generator.FieldScope.withOverriddenType(Lcom/fasterxml/classmate/ResolvedType;)Lcom/github/victools/jsonschema/generator/FieldScope;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 10:** `FR-HOST-JSONSCHEMA-GENERATOR-FIELD-SCOPE-WITH-OVERRIDDEN-NAME` → `com.github.victools.jsonschema.generator.FieldScope.withOverriddenName(Ljava/lang/String;)Lcom/github/victools/jsonschema/generator/FieldScope;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/reference_145/test_host_jsonschema_generator.py --no-cov`; scoped Ruff format/check and strict Mypy; assert independent expected outputs and FR logs.
- **Manual / Browser Verification:** Inspect consumer logs, lifecycle/failure outcomes and the declared infrastructure/JVM-only disposition.
- **Completion limit:** missing bodies/ownership/entitlement or independent expected outputs keep the task unchecked; static declarations do not establish SQX parity.


# 2.27 FEAT-HOST-JSONSCHEMA-MODULE-JACKSON - jsonschema-module-jackson-4.38.0.jar

## 1. Objective

- **Goal:** Provide the consumed serialization, archive or HTTP contract through the host resource boundary.
- **Context / Problem Solved:** Build 145 adds/changes this donor contribution; existing mock presentation and a filename do not establish functional support.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/libs/jsonschema-module-jackson-4.38.0.jar`; 10 raw class entries; SHA-256 `36fbd3f1c27379c3ba8420ac2cb0b42411f7bc3b3df8bdd11d8d7e024a1c28ca`.
- **Inspected reference:** [jsonschema-module-jackson-4.38.0.md](sqx/Libraries/jsonschema-module-jackson-4.38.0.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/libs/jsonschema-module-jackson-4.38.0.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/libs/jsonschema-module-jackson-4.38.0.jar" com.github.victools.jsonschema.module.jackson.JacksonOption`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Ownership:** proposed `FEAT-HOST-JSONSCHEMA-MODULE-JACKSON` and `FR-HOST-JSONSCHEMA-MODULE-JACKSON-CONSUMED-CONTRACTS`; owner `app/host/README.md`. No application registration or implementation is implied.
- **Dependencies:** P00 evidence/ownership, P01 logging and P02 typed sessions/jobs/resources; phase-specific data/engine/project prerequisites from the delivery graph.
- **UI donors:** No standalone UI contribution is established for this infrastructure archive; trace its consuming host/domain feature and connect there.

## 3. File Changes

- **Create:** `app/host/resources/vendor_contracts.py` — Provide the consumed serialization, archive or HTTP contract through the host resource boundary.
- **Modify:** `app/host/README.md` — ratify owning FEAT/FR contracts and status in the approved feature plan.
- **Create:** `tests/unit/reference_145/test_host_jsonschema_module_jackson.py` — donor-derived normal, boundary, failure and FR-log checks.
- **Delete / Deprecate:** none; version/dependency retirement requires explicit approved disposition.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Ratify cohort, owning FEAT/FRs, target decisions, dependencies and exact write paths in the canonical plan.
- [ ] **Step 2:** Fingerprint the selected cohort; enumerate classes, methods and actual consumers.
- [ ] **Step 3:** Inspect consumed bodies and record normal/boundary/error contracts as descriptive FRs.
- [ ] **Step 4:** Ratify ownership and a reuse/adaptation/JVM-only disposition; implement only retained behavior.
- [ ] **Step 5:** Verify fixtures, invalid inputs, lifecycle/cancellation where applicable and explicit FR logs.
- [ ] **Step 6:** Expose the typed capability to its existing host/domain consumers; no standalone UI is established for this infrastructure JAR.
- [ ] **Step 7:** Record timestamped observations and walkthrough; update the matching master checklist row only when all requirements pass.

- [ ] **Step 8:** `FR-HOST-JSONSCHEMA-MODULE-JACKSON-JACKSON-OPTION-CONTRACT` → `com.github.victools.jsonschema.module.jackson.JacksonOption`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-HOST-JSONSCHEMA-MODULE-JACKSON-JACKSON-OPTION-VALUES` → `com.github.victools.jsonschema.module.jackson.JacksonOption.values()[Lcom/github/victools/jsonschema/module/jackson/JacksonOption;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 10:** `FR-HOST-JSONSCHEMA-MODULE-JACKSON-JACKSON-OPTION-VALUE-OF` → `com.github.victools.jsonschema.module.jackson.JacksonOption.valueOf(Ljava/lang/String;)Lcom/github/victools/jsonschema/module/jackson/JacksonOption;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/reference_145/test_host_jsonschema_module_jackson.py --no-cov`; scoped Ruff format/check and strict Mypy; assert independent expected outputs and FR logs.
- **Manual / Browser Verification:** Inspect consumer logs, lifecycle/failure outcomes and the declared infrastructure/JVM-only disposition.
- **Completion limit:** missing bodies/ownership/entitlement or independent expected outputs keep the task unchecked; static declarations do not establish SQX parity.


# 2.28 FEAT-HOST-KOTLIN-STDLIB - kotlin-stdlib-2.2.21.jar

## 1. Objective

- **Goal:** Provide the consumed serialization, archive or HTTP contract through the host resource boundary.
- **Context / Problem Solved:** Build 145 adds/changes this donor contribution; existing mock presentation and a filename do not establish functional support.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/libs/kotlin-stdlib-2.2.21.jar`; 974 raw class entries; SHA-256 `6558a3d233da56a20934b32159f9db5f86ed5816ef098f78a2c223dc6abb79dd`.
- **Inspected reference:** [kotlin-stdlib-2.2.21.md](sqx/Libraries/kotlin-stdlib-2.2.21.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/libs/kotlin-stdlib-2.2.21.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/libs/kotlin-stdlib-2.2.21.jar" kotlin.ArrayIntrinsicsKt`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Ownership:** proposed `FEAT-HOST-KOTLIN-STDLIB` and `FR-HOST-KOTLIN-STDLIB-CONSUMED-CONTRACTS`; owner `app/host/README.md`. No application registration or implementation is implied.
- **Dependencies:** P00 evidence/ownership, P01 logging and P02 typed sessions/jobs/resources; phase-specific data/engine/project prerequisites from the delivery graph.
- **UI donors:** No standalone UI contribution is established for this infrastructure archive; trace its consuming host/domain feature and connect there.

## 3. File Changes

- **Create:** `app/host/resources/vendor_contracts.py` — Provide the consumed serialization, archive or HTTP contract through the host resource boundary.
- **Modify:** `app/host/README.md` — ratify owning FEAT/FR contracts and status in the approved feature plan.
- **Create:** `tests/unit/reference_145/test_host_kotlin_stdlib.py` — donor-derived normal, boundary, failure and FR-log checks.
- **Delete / Deprecate:** none; version/dependency retirement requires explicit approved disposition.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Ratify cohort, owning FEAT/FRs, target decisions, dependencies and exact write paths in the canonical plan.
- [ ] **Step 2:** Fingerprint the selected cohort; enumerate classes, methods and actual consumers.
- [ ] **Step 3:** Inspect consumed bodies and record normal/boundary/error contracts as descriptive FRs.
- [ ] **Step 4:** Ratify ownership and a reuse/adaptation/JVM-only disposition; implement only retained behavior.
- [ ] **Step 5:** Verify fixtures, invalid inputs, lifecycle/cancellation where applicable and explicit FR logs.
- [ ] **Step 6:** Expose the typed capability to its existing host/domain consumers; no standalone UI is established for this infrastructure JAR.
- [ ] **Step 7:** Record timestamped observations and walkthrough; update the matching master checklist row only when all requirements pass.

- [ ] **Step 8:** `FR-HOST-KOTLIN-STDLIB-ARRAY-INTRINSICS-KT-CONTRACT` → `kotlin.ArrayIntrinsicsKt`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/reference_145/test_host_kotlin_stdlib.py --no-cov`; scoped Ruff format/check and strict Mypy; assert independent expected outputs and FR logs.
- **Manual / Browser Verification:** Inspect consumer logs, lifecycle/failure outcomes and the declared infrastructure/JVM-only disposition.
- **Completion limit:** missing bodies/ownership/entitlement or independent expected outputs keep the task unchecked; static declarations do not establish SQX parity.


# 2.29 FEAT-HOST-MCP - mcp-0.17.2.jar

## 1. Objective

- **Goal:** Provide the consumed serialization, archive or HTTP contract through the host resource boundary.
- **Context / Problem Solved:** Build 145 adds/changes this donor contribution; existing mock presentation and a filename do not establish functional support.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/libs/mcp-0.17.2.jar`; 0 raw class entries; SHA-256 `03933059322e5d64f2d305701338f0a3b894a2c983079b44b675b63ea12798b0`.
- **Inspected reference:** [mcp-0.17.2.md](sqx/Libraries/mcp-0.17.2.md); full class/member metadata is linked there.
- **Research:** this archive has no compiled class entries; inspect current resource/registration payloads, not invented class requirements.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Ownership:** proposed `FEAT-HOST-MCP` and `FR-HOST-MCP-CONSUMED-CONTRACTS`; owner `app/host/README.md`. No application registration or implementation is implied.
- **Dependencies:** P00 evidence/ownership, P01 logging and P02 typed sessions/jobs/resources; phase-specific data/engine/project prerequisites from the delivery graph.
- **UI donors:** No standalone UI contribution is established for this infrastructure archive; trace its consuming host/domain feature and connect there.

## 3. File Changes

- **Create:** `app/host/resources/vendor_contracts.py` — Provide the consumed serialization, archive or HTTP contract through the host resource boundary.
- **Modify:** `app/host/README.md` — ratify owning FEAT/FR contracts and status in the approved feature plan.
- **Create:** `tests/unit/reference_145/test_host_mcp.py` — donor-derived normal, boundary, failure and FR-log checks.
- **Delete / Deprecate:** none; version/dependency retirement requires explicit approved disposition.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Ratify cohort, owning FEAT/FRs, target decisions, dependencies and exact write paths in the canonical plan.
- [ ] **Step 2:** Fingerprint the selected cohort; enumerate classes, methods and actual consumers.
- [ ] **Step 3:** Inspect consumed bodies and record normal/boundary/error contracts as descriptive FRs.
- [ ] **Step 4:** Ratify ownership and a reuse/adaptation/JVM-only disposition; implement only retained behavior.
- [ ] **Step 5:** Verify fixtures, invalid inputs, lifecycle/cancellation where applicable and explicit FR logs.
- [ ] **Step 6:** Expose the typed capability to its existing host/domain consumers; no standalone UI is established for this infrastructure JAR.
- [ ] **Step 7:** Record timestamped observations and walkthrough; update the matching master checklist row only when all requirements pass.



## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/reference_145/test_host_mcp.py --no-cov`; scoped Ruff format/check and strict Mypy; assert independent expected outputs and FR logs.
- **Manual / Browser Verification:** Inspect consumer logs, lifecycle/failure outcomes and the declared infrastructure/JVM-only disposition.
- **Completion limit:** missing bodies/ownership/entitlement or independent expected outputs keep the task unchecked; static declarations do not establish SQX parity.


# 2.30 FEAT-HOST-MCP-JSON - mcp-json-0.17.2.jar

## 1. Objective

- **Goal:** Provide the consumed serialization, archive or HTTP contract through the host resource boundary.
- **Context / Problem Solved:** Build 145 adds/changes this donor contribution; existing mock presentation and a filename do not establish functional support.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/libs/mcp-json-0.17.2.jar`; 8 raw class entries; SHA-256 `6df99ef400836bd213d63895684eb066d36e1a9b759bd38342c32a6b9b0b6e4f`.
- **Inspected reference:** [mcp-json-0.17.2.md](sqx/Libraries/mcp-json-0.17.2.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/libs/mcp-json-0.17.2.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/libs/mcp-json-0.17.2.jar" io.modelcontextprotocol.json.McpJsonMapperSupplier`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Ownership:** proposed `FEAT-HOST-MCP-JSON` and `FR-HOST-MCP-JSON-CONSUMED-CONTRACTS`; owner `app/host/README.md`. No application registration or implementation is implied.
- **Dependencies:** P00 evidence/ownership, P01 logging and P02 typed sessions/jobs/resources; phase-specific data/engine/project prerequisites from the delivery graph.
- **UI donors:** No standalone UI contribution is established for this infrastructure archive; trace its consuming host/domain feature and connect there.

## 3. File Changes

- **Create:** `app/host/resources/vendor_contracts.py` — Provide the consumed serialization, archive or HTTP contract through the host resource boundary.
- **Modify:** `app/host/README.md` — ratify owning FEAT/FR contracts and status in the approved feature plan.
- **Create:** `tests/unit/reference_145/test_host_mcp_json.py` — donor-derived normal, boundary, failure and FR-log checks.
- **Delete / Deprecate:** none; version/dependency retirement requires explicit approved disposition.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Ratify cohort, owning FEAT/FRs, target decisions, dependencies and exact write paths in the canonical plan.
- [ ] **Step 2:** Fingerprint the selected cohort; enumerate classes, methods and actual consumers.
- [ ] **Step 3:** Inspect consumed bodies and record normal/boundary/error contracts as descriptive FRs.
- [ ] **Step 4:** Ratify ownership and a reuse/adaptation/JVM-only disposition; implement only retained behavior.
- [ ] **Step 5:** Verify fixtures, invalid inputs, lifecycle/cancellation where applicable and explicit FR logs.
- [ ] **Step 6:** Expose the typed capability to its existing host/domain consumers; no standalone UI is established for this infrastructure JAR.
- [ ] **Step 7:** Record timestamped observations and walkthrough; update the matching master checklist row only when all requirements pass.

- [ ] **Step 8:** `FR-HOST-MCP-JSON-MCP-JSON-MAPPER-SUPPLIER-CONTRACT` → `io.modelcontextprotocol.json.McpJsonMapperSupplier`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/reference_145/test_host_mcp_json.py --no-cov`; scoped Ruff format/check and strict Mypy; assert independent expected outputs and FR logs.
- **Manual / Browser Verification:** Inspect consumer logs, lifecycle/failure outcomes and the declared infrastructure/JVM-only disposition.
- **Completion limit:** missing bodies/ownership/entitlement or independent expected outputs keep the task unchecked; static declarations do not establish SQX parity.


# 2.31 FEAT-HOST-OKHTTP-JVM - okhttp-jvm-5.3.2.jar

## 1. Objective

- **Goal:** Provide the consumed serialization, archive or HTTP contract through the host resource boundary.
- **Context / Problem Solved:** Build 145 adds/changes this donor contribution; existing mock presentation and a filename do not establish functional support.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/libs/okhttp-jvm-5.3.2.jar`; 336 raw class entries; SHA-256 `c771f48075b763f6c322055e21129a94b7de4c1faf3f8f58ace320b0c9517a30`.
- **Inspected reference:** [okhttp-jvm-5.3.2.md](sqx/Libraries/okhttp-jvm-5.3.2.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/libs/okhttp-jvm-5.3.2.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/libs/okhttp-jvm-5.3.2.jar" okhttp3.Address`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Ownership:** proposed `FEAT-HOST-OKHTTP-JVM` and `FR-HOST-OKHTTP-JVM-CONSUMED-CONTRACTS`; owner `app/host/README.md`. No application registration or implementation is implied.
- **Dependencies:** P00 evidence/ownership, P01 logging and P02 typed sessions/jobs/resources; phase-specific data/engine/project prerequisites from the delivery graph.
- **UI donors:** No standalone UI contribution is established for this infrastructure archive; trace its consuming host/domain feature and connect there.

## 3. File Changes

- **Create:** `app/host/resources/vendor_contracts.py` — Provide the consumed serialization, archive or HTTP contract through the host resource boundary.
- **Modify:** `app/host/README.md` — ratify owning FEAT/FR contracts and status in the approved feature plan.
- **Create:** `tests/unit/reference_145/test_host_okhttp_jvm.py` — donor-derived normal, boundary, failure and FR-log checks.
- **Delete / Deprecate:** none; version/dependency retirement requires explicit approved disposition.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Ratify cohort, owning FEAT/FRs, target decisions, dependencies and exact write paths in the canonical plan.
- [ ] **Step 2:** Fingerprint the selected cohort; enumerate classes, methods and actual consumers.
- [ ] **Step 3:** Inspect consumed bodies and record normal/boundary/error contracts as descriptive FRs.
- [ ] **Step 4:** Ratify ownership and a reuse/adaptation/JVM-only disposition; implement only retained behavior.
- [ ] **Step 5:** Verify fixtures, invalid inputs, lifecycle/cancellation where applicable and explicit FR logs.
- [ ] **Step 6:** Expose the typed capability to its existing host/domain consumers; no standalone UI is established for this infrastructure JAR.
- [ ] **Step 7:** Record timestamped observations and walkthrough; update the matching master checklist row only when all requirements pass.

- [ ] **Step 8:** `FR-HOST-OKHTTP-JVM-ADDRESS-CONTRACT` → `okhttp3.Address`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-HOST-OKHTTP-JVM-ADDRESS-DNS` → `okhttp3.Address.dns()Lokhttp3/Dns;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 10:** `FR-HOST-OKHTTP-JVM-ADDRESS-SOCKET-FACTORY` → `okhttp3.Address.socketFactory()Ljavax/net/SocketFactory;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/reference_145/test_host_okhttp_jvm.py --no-cov`; scoped Ruff format/check and strict Mypy; assert independent expected outputs and FR logs.
- **Manual / Browser Verification:** Inspect consumer logs, lifecycle/failure outcomes and the declared infrastructure/JVM-only disposition.
- **Completion limit:** missing bodies/ownership/entitlement or independent expected outputs keep the task unchecked; static declarations do not establish SQX parity.


# 2.32 FEAT-HOST-OKIO-JVM - okio-jvm-3.16.4.jar

## 1. Objective

- **Goal:** Provide the consumed serialization, archive or HTTP contract through the host resource boundary.
- **Context / Problem Solved:** Build 145 adds/changes this donor contribution; existing mock presentation and a filename do not establish functional support.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/libs/okio-jvm-3.16.4.jar`; 117 raw class entries; SHA-256 `2196b993cd34dbbd919e7e01f57a4781b58bee80f86106163e287c20343a96a7`.
- **Inspected reference:** [okio-jvm-3.16.4.md](sqx/Libraries/okio-jvm-3.16.4.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/libs/okio-jvm-3.16.4.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/libs/okio-jvm-3.16.4.jar" okio.-Base64`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Ownership:** proposed `FEAT-HOST-OKIO-JVM` and `FR-HOST-OKIO-JVM-CONSUMED-CONTRACTS`; owner `app/host/README.md`. No application registration or implementation is implied.
- **Dependencies:** P00 evidence/ownership, P01 logging and P02 typed sessions/jobs/resources; phase-specific data/engine/project prerequisites from the delivery graph.
- **UI donors:** No standalone UI contribution is established for this infrastructure archive; trace its consuming host/domain feature and connect there.

## 3. File Changes

- **Create:** `app/host/resources/vendor_contracts.py` — Provide the consumed serialization, archive or HTTP contract through the host resource boundary.
- **Modify:** `app/host/README.md` — ratify owning FEAT/FR contracts and status in the approved feature plan.
- **Create:** `tests/unit/reference_145/test_host_okio_jvm.py` — donor-derived normal, boundary, failure and FR-log checks.
- **Delete / Deprecate:** none; version/dependency retirement requires explicit approved disposition.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Ratify cohort, owning FEAT/FRs, target decisions, dependencies and exact write paths in the canonical plan.
- [ ] **Step 2:** Fingerprint the selected cohort; enumerate classes, methods and actual consumers.
- [ ] **Step 3:** Inspect consumed bodies and record normal/boundary/error contracts as descriptive FRs.
- [ ] **Step 4:** Ratify ownership and a reuse/adaptation/JVM-only disposition; implement only retained behavior.
- [ ] **Step 5:** Verify fixtures, invalid inputs, lifecycle/cancellation where applicable and explicit FR logs.
- [ ] **Step 6:** Expose the typed capability to its existing host/domain consumers; no standalone UI is established for this infrastructure JAR.
- [ ] **Step 7:** Record timestamped observations and walkthrough; update the matching master checklist row only when all requirements pass.

- [ ] **Step 8:** `FR-HOST-OKIO-JVM-BASE64-CONTRACT` → `okio.-Base64`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-HOST-OKIO-JVM-BASE64-GET-BASE64` → `okio.-Base64.getBASE64()[B`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 10:** `FR-HOST-OKIO-JVM-BASE64-GET-BASE64-URL-SAFE` → `okio.-Base64.getBASE64_URL_SAFE()[B`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/reference_145/test_host_okio_jvm.py --no-cov`; scoped Ruff format/check and strict Mypy; assert independent expected outputs and FR logs.
- **Manual / Browser Verification:** Inspect consumer logs, lifecycle/failure outcomes and the declared infrastructure/JVM-only disposition.
- **Completion limit:** missing bodies/ownership/entitlement or independent expected outputs keep the task unchecked; static declarations do not establish SQX parity.


# 2.33 FEAT-HOST-SNAKEYAML - snakeyaml-2.6.jar

## 1. Objective

- **Goal:** Provide the consumed serialization, archive or HTTP contract through the host resource boundary.
- **Context / Problem Solved:** Build 145 adds/changes this donor contribution; existing mock presentation and a filename do not establish functional support.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/libs/snakeyaml-2.6.jar`; 237 raw class entries; SHA-256 `c8f7a98e7394adda02f6317249710e4d1b4c7a25aa8c7eace0c2eea52eb8bf85`.
- **Inspected reference:** [snakeyaml-2.6.md](sqx/Libraries/snakeyaml-2.6.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/libs/snakeyaml-2.6.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/libs/snakeyaml-2.6.jar" org.yaml.snakeyaml.internal.Logger`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Ownership:** proposed `FEAT-HOST-SNAKEYAML` and `FR-HOST-SNAKEYAML-CONSUMED-CONTRACTS`; owner `app/host/README.md`. No application registration or implementation is implied.
- **Dependencies:** P00 evidence/ownership, P01 logging and P02 typed sessions/jobs/resources; phase-specific data/engine/project prerequisites from the delivery graph.
- **UI donors:** No standalone UI contribution is established for this infrastructure archive; trace its consuming host/domain feature and connect there.

## 3. File Changes

- **Create:** `app/host/resources/vendor_contracts.py` — Provide the consumed serialization, archive or HTTP contract through the host resource boundary.
- **Modify:** `app/host/README.md` — ratify owning FEAT/FR contracts and status in the approved feature plan.
- **Create:** `tests/unit/reference_145/test_host_snakeyaml.py` — donor-derived normal, boundary, failure and FR-log checks.
- **Delete / Deprecate:** none; version/dependency retirement requires explicit approved disposition.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Ratify cohort, owning FEAT/FRs, target decisions, dependencies and exact write paths in the canonical plan.
- [ ] **Step 2:** Fingerprint the selected cohort; enumerate classes, methods and actual consumers.
- [ ] **Step 3:** Inspect consumed bodies and record normal/boundary/error contracts as descriptive FRs.
- [ ] **Step 4:** Ratify ownership and a reuse/adaptation/JVM-only disposition; implement only retained behavior.
- [ ] **Step 5:** Verify fixtures, invalid inputs, lifecycle/cancellation where applicable and explicit FR logs.
- [ ] **Step 6:** Expose the typed capability to its existing host/domain consumers; no standalone UI is established for this infrastructure JAR.
- [ ] **Step 7:** Record timestamped observations and walkthrough; update the matching master checklist row only when all requirements pass.

- [ ] **Step 8:** `FR-HOST-SNAKEYAML-LOGGER-CONTRACT` → `org.yaml.snakeyaml.internal.Logger`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-HOST-SNAKEYAML-LOGGER-GET-LOGGER` → `org.yaml.snakeyaml.internal.Logger.getLogger(Ljava/lang/String;)Lorg/yaml/snakeyaml/internal/Logger;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 10:** `FR-HOST-SNAKEYAML-LOGGER-IS-LOGGABLE` → `org.yaml.snakeyaml.internal.Logger.isLoggable(Lorg/yaml/snakeyaml/internal/Logger$Level;)Z`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/reference_145/test_host_snakeyaml.py --no-cov`; scoped Ruff format/check and strict Mypy; assert independent expected outputs and FR logs.
- **Manual / Browser Verification:** Inspect consumer logs, lifecycle/failure outcomes and the declared infrastructure/JVM-only disposition.
- **Completion limit:** missing bodies/ownership/entitlement or independent expected outputs keep the task unchecked; static declarations do not establish SQX parity.


# 2.34 FEAT-HOST-STAX-API - stax-api-1.0.1.jar

## 1. Objective

- **Goal:** Provide the consumed serialization, archive or HTTP contract through the host resource boundary.
- **Context / Problem Solved:** Build 145 adds/changes this donor contribution; existing mock presentation and a filename do not establish functional support.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/libs/stax-api-1.0.1.jar`; 40 raw class entries; SHA-256 `d1968436fc216c901fb9b82c7e878b50fd1d30091676da95b2edd3a9c0ccf92e`.
- **Inspected reference:** [stax-api-1.0.1.md](sqx/Libraries/stax-api-1.0.1.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/libs/stax-api-1.0.1.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/libs/stax-api-1.0.1.jar" javax.xml.stream.events.StartElement`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Ownership:** proposed `FEAT-HOST-STAX-API` and `FR-HOST-STAX-API-CONSUMED-CONTRACTS`; owner `app/host/README.md`. No application registration or implementation is implied.
- **Dependencies:** P00 evidence/ownership, P01 logging and P02 typed sessions/jobs/resources; phase-specific data/engine/project prerequisites from the delivery graph.
- **UI donors:** No standalone UI contribution is established for this infrastructure archive; trace its consuming host/domain feature and connect there.

## 3. File Changes

- **Create:** `app/host/resources/vendor_contracts.py` — Provide the consumed serialization, archive or HTTP contract through the host resource boundary.
- **Modify:** `app/host/README.md` — ratify owning FEAT/FR contracts and status in the approved feature plan.
- **Create:** `tests/unit/reference_145/test_host_stax_api.py` — donor-derived normal, boundary, failure and FR-log checks.
- **Delete / Deprecate:** none; version/dependency retirement requires explicit approved disposition.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Ratify cohort, owning FEAT/FRs, target decisions, dependencies and exact write paths in the canonical plan.
- [ ] **Step 2:** Fingerprint the selected cohort; enumerate classes, methods and actual consumers.
- [ ] **Step 3:** Inspect consumed bodies and record normal/boundary/error contracts as descriptive FRs.
- [ ] **Step 4:** Ratify ownership and a reuse/adaptation/JVM-only disposition; implement only retained behavior.
- [ ] **Step 5:** Verify fixtures, invalid inputs, lifecycle/cancellation where applicable and explicit FR logs.
- [ ] **Step 6:** Expose the typed capability to its existing host/domain consumers; no standalone UI is established for this infrastructure JAR.
- [ ] **Step 7:** Record timestamped observations and walkthrough; update the matching master checklist row only when all requirements pass.

- [ ] **Step 8:** `FR-HOST-STAX-API-START-ELEMENT-CONTRACT` → `javax.xml.stream.events.StartElement`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-HOST-STAX-API-START-ELEMENT-GET-NAME` → `javax.xml.stream.events.StartElement.getName()Ljavax/xml/namespace/QName;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 10:** `FR-HOST-STAX-API-START-ELEMENT-GET-ATTRIBUTES` → `javax.xml.stream.events.StartElement.getAttributes()Ljava/util/Iterator;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/reference_145/test_host_stax_api.py --no-cov`; scoped Ruff format/check and strict Mypy; assert independent expected outputs and FR logs.
- **Manual / Browser Verification:** Inspect consumer logs, lifecycle/failure outcomes and the declared infrastructure/JVM-only disposition.
- **Completion limit:** missing bodies/ownership/entitlement or independent expected outputs keep the task unchecked; static declarations do not establish SQX parity.


# 2.35 FEAT-HOST-XSTREAM - xstream-1.4.9.jar

## 1. Objective

- **Goal:** Provide the consumed serialization, archive or HTTP contract through the host resource boundary.
- **Context / Problem Solved:** Build 145 adds/changes this donor contribution; existing mock presentation and a filename do not establish functional support.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/libs/xstream-1.4.9.jar`; 446 raw class entries; SHA-256 `381ea035b0e22eb1a02e5c09b60fb93293930516c4c79b43519f97a9ea9cbad3`.
- **Inspected reference:** [xstream-1.4.9.md](sqx/Libraries/xstream-1.4.9.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/libs/xstream-1.4.9.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/libs/xstream-1.4.9.jar" com.thoughtworks.xstream.MarshallingStrategy`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Ownership:** proposed `FEAT-HOST-XSTREAM` and `FR-HOST-XSTREAM-CONSUMED-CONTRACTS`; owner `app/host/README.md`. No application registration or implementation is implied.
- **Dependencies:** P00 evidence/ownership, P01 logging and P02 typed sessions/jobs/resources; phase-specific data/engine/project prerequisites from the delivery graph.
- **UI donors:** No standalone UI contribution is established for this infrastructure archive; trace its consuming host/domain feature and connect there.

## 3. File Changes

- **Create:** `app/host/resources/vendor_contracts.py` — Provide the consumed serialization, archive or HTTP contract through the host resource boundary.
- **Modify:** `app/host/README.md` — ratify owning FEAT/FR contracts and status in the approved feature plan.
- **Create:** `tests/unit/reference_145/test_host_xstream.py` — donor-derived normal, boundary, failure and FR-log checks.
- **Delete / Deprecate:** none; version/dependency retirement requires explicit approved disposition.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Ratify cohort, owning FEAT/FRs, target decisions, dependencies and exact write paths in the canonical plan.
- [ ] **Step 2:** Fingerprint the selected cohort; enumerate classes, methods and actual consumers.
- [ ] **Step 3:** Inspect consumed bodies and record normal/boundary/error contracts as descriptive FRs.
- [ ] **Step 4:** Ratify ownership and a reuse/adaptation/JVM-only disposition; implement only retained behavior.
- [ ] **Step 5:** Verify fixtures, invalid inputs, lifecycle/cancellation where applicable and explicit FR logs.
- [ ] **Step 6:** Expose the typed capability to its existing host/domain consumers; no standalone UI is established for this infrastructure JAR.
- [ ] **Step 7:** Record timestamped observations and walkthrough; update the matching master checklist row only when all requirements pass.

- [ ] **Step 8:** `FR-HOST-XSTREAM-MARSHALLING-STRATEGY-CONTRACT` → `com.thoughtworks.xstream.MarshallingStrategy`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-HOST-XSTREAM-MARSHALLING-STRATEGY-UNMARSHAL` → `com.thoughtworks.xstream.MarshallingStrategy.unmarshal(Ljava/lang/Object;Lcom/thoughtworks/xstream/io/HierarchicalStreamReader;Lcom/thoughtworks/xstream/converters/DataHolder;Lcom/thoughtworks/xstream/converters/ConverterLookup;Lcom/thoughtworks/xstream/mapper/Mapper;)Ljava/lang/Object;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 10:** `FR-HOST-XSTREAM-MARSHALLING-STRATEGY-MARSHAL` → `com.thoughtworks.xstream.MarshallingStrategy.marshal(Lcom/thoughtworks/xstream/io/HierarchicalStreamWriter;Ljava/lang/Object;Lcom/thoughtworks/xstream/converters/ConverterLookup;Lcom/thoughtworks/xstream/mapper/Mapper;Lcom/thoughtworks/xstream/converters/DataHolder;)V`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/reference_145/test_host_xstream.py --no-cov`; scoped Ruff format/check and strict Mypy; assert independent expected outputs and FR logs.
- **Manual / Browser Verification:** Inspect consumer logs, lifecycle/failure outcomes and the declared infrastructure/JVM-only disposition.
- **Completion limit:** missing bodies/ownership/entitlement or independent expected outputs keep the task unchecked; static declarations do not establish SQX parity.


# 2.36 FEAT-HOST-XZ - xz-1.9.jar

## 1. Objective

- **Goal:** Provide the consumed serialization, archive or HTTP contract through the host resource boundary.
- **Context / Problem Solved:** Build 145 adds/changes this donor contribution; existing mock presentation and a filename do not establish functional support.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/libs/xz-1.9.jar`; 117 raw class entries; SHA-256 `211b306cfc44f8f96df3a0a3ddaf75ba8c5289eed77d60d72f889bb855f535e5`.
- **Inspected reference:** [xz-1.9.md](sqx/Libraries/xz-1.9.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/libs/xz-1.9.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/libs/xz-1.9.jar" org.tukaani.xz.ARMOptions`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Ownership:** proposed `FEAT-HOST-XZ` and `FR-HOST-XZ-CONSUMED-CONTRACTS`; owner `app/host/README.md`. No application registration or implementation is implied.
- **Dependencies:** P00 evidence/ownership, P01 logging and P02 typed sessions/jobs/resources; phase-specific data/engine/project prerequisites from the delivery graph.
- **UI donors:** No standalone UI contribution is established for this infrastructure archive; trace its consuming host/domain feature and connect there.

## 3. File Changes

- **Create:** `app/host/resources/vendor_contracts.py` — Provide the consumed serialization, archive or HTTP contract through the host resource boundary.
- **Modify:** `app/host/README.md` — ratify owning FEAT/FR contracts and status in the approved feature plan.
- **Create:** `tests/unit/reference_145/test_host_xz.py` — donor-derived normal, boundary, failure and FR-log checks.
- **Delete / Deprecate:** none; version/dependency retirement requires explicit approved disposition.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Ratify cohort, owning FEAT/FRs, target decisions, dependencies and exact write paths in the canonical plan.
- [ ] **Step 2:** Fingerprint the selected cohort; enumerate classes, methods and actual consumers.
- [ ] **Step 3:** Inspect consumed bodies and record normal/boundary/error contracts as descriptive FRs.
- [ ] **Step 4:** Ratify ownership and a reuse/adaptation/JVM-only disposition; implement only retained behavior.
- [ ] **Step 5:** Verify fixtures, invalid inputs, lifecycle/cancellation where applicable and explicit FR logs.
- [ ] **Step 6:** Expose the typed capability to its existing host/domain consumers; no standalone UI is established for this infrastructure JAR.
- [ ] **Step 7:** Record timestamped observations and walkthrough; update the matching master checklist row only when all requirements pass.

- [ ] **Step 8:** `FR-HOST-XZ-ARMOPTIONS-CONTRACT` → `org.tukaani.xz.ARMOptions`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-HOST-XZ-ARMOPTIONS-GET-OUTPUT-STREAM` → `org.tukaani.xz.ARMOptions.getOutputStream(Lorg/tukaani/xz/FinishableOutputStream;Lorg/tukaani/xz/ArrayCache;)Lorg/tukaani/xz/FinishableOutputStream;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 10:** `FR-HOST-XZ-ARMOPTIONS-GET-INPUT-STREAM` → `org.tukaani.xz.ARMOptions.getInputStream(Ljava/io/InputStream;Lorg/tukaani/xz/ArrayCache;)Ljava/io/InputStream;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/reference_145/test_host_xz.py --no-cov`; scoped Ruff format/check and strict Mypy; assert independent expected outputs and FR logs.
- **Manual / Browser Verification:** Inspect consumer logs, lifecycle/failure outcomes and the declared infrastructure/JVM-only disposition.
- **Completion limit:** missing bodies/ownership/entitlement or independent expected outputs keep the task unchecked; static declarations do not establish SQX parity.


# 2.37 P02 integration — Connect the frontend to typed host discovery, sessions, jobs and resources

## 1. Objective

- **Goal:** Connect the frontend to typed host discovery, sessions, jobs and resources.
- **Context / Problem Solved:** The existing UI needs a real end-to-end backend workflow, beyond isolated JAR adapters.

## 2. Research and donors

- **Roadmap:** `HARUQUANTAI_ROOT/docs/dev/V1/sqx-full-application-roadmap.md`, P02; donor features and FRs are the tasks in this file.
- **Existing code:** `ui/app/host/transport.ts`, `HostConnection.tsx`, `hostSettings.ts`; backend counterparts are proposed.
- **Declared dependencies:** FastAPI, Pydantic, Uvicorn, psutil; host persistence choice remains unratified.
- **Existing tests:** No audited phase backend suite; create the integration tests below.
- **Conflict/gap:** frontend existence does not establish functional backend behavior; route/schema/discovery changes need a task plan and approval.
- **Cross-feature ownership:** shared files may host multiple features; keep per-FR traces and delegate persistence/jobs to host capabilities.

- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/web/app`; `SQX_145_REFERENCE_ROOT/internal/web/common`. Inspect `SQX_145_REFERENCE_ROOT/internal/web/app/login/LoginService.js`; `SQX_145_REFERENCE_ROOT/internal/web/common/templates.html`.
- **Existing UI connection:** host connection; proposed shared consumer; verify the exact existing control and public contract before implementation. Target `ui/app/host/HostConnection.tsx`; wire session/readiness, capability availability and server-owned shell state.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Modify:** `app/host/discovery/contracts.py` (proposed earlier in FEAT-HOST-JSPF-CORE)
  - Deliver the phase's typed contracts and integration flow; extend prior approved owners where shared.
- **Modify:** `app/host/discovery/registry.py` (proposed earlier in FEAT-HOST-JSPF-CORE)
  - Deliver the phase's typed contracts and integration flow; extend prior approved owners where shared.
- **Modify:** `app/host/discovery/loader.py` (proposed earlier in FEAT-HOST-JSPF-CORE)
  - Deliver the phase's typed contracts and integration flow; extend prior approved owners where shared.
- **Modify:** `app/host/transport/server.py` (proposed shared TLS owner; current-source qualification required)
  - Deliver the phase's typed contracts and integration flow; extend prior approved owners where shared.
- **Modify:** `app/host/transport/routes.py` (proposed shared TLS owner; current-source qualification required)
  - Deliver the phase's typed contracts and integration flow; extend prior approved owners where shared.
- **Modify:** `app/host/transport/session.py` (proposed shared TLS owner; current-source qualification required)
  - Deliver the phase's typed contracts and integration flow; extend prior approved owners where shared.
- **Modify:** `app/host/transport/events.py` (proposed shared TLS owner; current-source qualification required)
  - Deliver the phase's typed contracts and integration flow; extend prior approved owners where shared.
- **Modify:** `app/host/jobs/contracts.py` (proposed earlier in FEAT-HOST-REACTIVE-STREAMS)
  - Deliver the phase's typed contracts and integration flow; extend prior approved owners where shared.
- **Modify:** `app/host/jobs/scheduler.py` (proposed earlier in FEAT-HOST-REACTIVE-STREAMS)
  - Deliver the phase's typed contracts and integration flow; extend prior approved owners where shared.
- **Modify:** `app/host/persistence/store.py` (proposed earlier in FEAT-HOST-FST)
  - Deliver the phase's typed contracts and integration flow; extend prior approved owners where shared.
- **Modify:** `app/host/persistence/transactions.py` (proposed earlier in FEAT-HOST-FST)
  - Deliver the phase's typed contracts and integration flow; extend prior approved owners where shared.
- **Modify:** `app/host/persistence/retention.py` (proposed earlier in FEAT-HOST-FST)
  - Deliver the phase's typed contracts and integration flow; extend prior approved owners where shared.
- **Modify:** `ui/app/host/transport.ts`
  - Align only universal transport/session/preferences with the ratified host; keep domain contracts outside the host.
- **Modify:** `ui/app/host/HostConnection.tsx`
  - Align only universal transport/session/preferences with the ratified host; keep domain contracts outside the host.
- **Modify:** `ui/app/host/hostSettings.ts`
  - Align only universal transport/session/preferences with the ratified host; keep domain contracts outside the host.
- **Modify:** `ui/app/host/README.md`
  - Align only universal transport/session/preferences with the ratified host; keep domain contracts outside the host.
- **Modify:** `app/host/README.md` (proposed earlier in P00)
  - Own feature registration/status and phase contract decisions after ratification.
- **Create:** `tests/integration/test_host_services_workflow.py`
  - Exercise the real phase workflow in isolated stores with failure/cancellation assertions.
- **Create:** `ui/tests/e2e/sqx-host-services-backend.spec.ts`
  - Use an isolated real host to verify UI state and request/output reconciliation.

- **UI connection files (existing presentation):**
- **Create:** `ui/playwright.backend.config.ts`
  - Shared connected-test harness: isolated real host/store, readiness, UI base URL/proxy and shutdown; no application API interception.
- **Modify:** `ui/app/host/store.ts`
  - Replace affected mock job/resource authority with server projections; preserve selection/view state.
- **Create:** `ui/tests/unit/backend-connections/task-2-37.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Review preceding feature fixtures and owning README registrations; ratify the phase integration contracts and execution plan.
- [ ] **Step 2:** Ratify capability registration, compatibility and HTTP/event envelopes with frontend counterparts.
- [ ] **Step 3:** Implement sessions, authenticated events, job scheduling/cancellation and bounded resource handles.
- [ ] **Step 4:** Provide host-owned document validation and isolated store transactions; verify mount/unmount cleanup.
- [ ] **Step 5:** Replace fixture-driven production execution in the affected workflow; retain deterministic fixtures only in tests.
- [ ] **Step 6:** Test positive/failure/cancellation paths and observable FR logs; reload/reconnect and reconcile persisted outputs.
- [ ] **Step 7:** Record exact commands, timestamped artifacts, unresolved gaps and walkthrough; obtain separate owner commit authority.

- [ ] **Step 8:** Connect retained UI: Ratify the feature-owned wire contract; bind session/readiness, capability availability and server-owned shell state to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 9:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/integration/test_host_services_workflow.py --no-cov`; `npm --prefix ui run test:ui -- tests/e2e/sqx-host-services-backend.spec.ts`. Assert login/readiness/preferences, event correlation, restart durability and cancellation; reject unauthorized call, incompatible plugin, queue overflow and transaction failure.
- **Manual / Browser Verification:** Connect the shell; change a preference; reconnect; cancel a real job; unmount a capability and confirm dependent controls disable.

- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/task-2-37.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-host-services-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise host connection for 2.37; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.

## Phase completion gate

- [ ] Every applicable feature passed its own isolated real-host UI/backend case; no production mock fallback or unresolved required UI remains.

- [ ] Reconcile all allocated FEAT/FR dispositions, donor fixtures and ownership gaps.
- [ ] Run Ruff format/check and strict Mypy on the approved changed Python paths; verify branch-aware coverage ≥80% across retained application source at release.
- [ ] For affected UI: `npm --prefix ui run typecheck`, `npm --prefix ui run test`, `npm --prefix ui run build`.
- [ ] Record real workflow observations, timestamps, failure artifacts and remaining gaps in the walkthrough.
- [ ] Obtain the next task/phase approval; commits and external/destructive actions retain separate owner gates.

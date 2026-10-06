# P02 — Host discovery, transport, jobs, resource services and persistence

- **Source:** `HARUQUANTAI_ROOT/docs/dev/sqx-full-application-roadmap.md`; SHA-256 `9abec0aa2faf6bd78b39e80c2dcfb7dfcae62ae412d9b56a77904de6a7b5a54c`.
- **Dependencies:** P01.
- **Scope:** 26 JAR feature tasks, 0 resource tasks, one phase integration task.
- **State:** proposed checklists; all execution, registrations and target contracts require task-level approval.
- **File labels:** existing paths are Modify; absent paths are Create; later shared edits name their earlier proposed owner.
- **Execution standard:** AGENTS.md plan → approval → implementation → tests → walkthrough; canonical Python docstrings, typed public APIs and explicit FR logs.
- **Clean room:** donor signatures guide behavioral research; independently written implementations; no proprietary source in evidence; no parity claim without independent validation.
- **Verification:** commands below are future tasks, not reported passes; isolated stores only; no live-store schema change/restore or Git mutation.

# caffeine-2.8.5.jar — FEAT-HOST-CAFFEINE-2-8-5

## 1. Objective

- **Goal:** Provide bounded host cache behavior for approved consumers.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Connect the frontend to typed host discovery, sessions, jobs and resources.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/libs/caffeine-2.8.5.jar`; 690 class declarations; SHA-256 `814b15a9bf598e0fa854dd70ba9f6e03a413a97979de0c3f49317295e4352bc8`.
- **Inspected reference:** No dedicated docs/sqx coverage; expand archive inspection; roadmap allocation `FEAT-HOST-CAFFEINE-2-8-5`.
- **Owner:** `app/host/resources/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Cache/collection support; implement measured consumed policies via existing packages; downstream P03,P06,P09,P14.
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/libs/caffeine-2.8.5.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/libs/caffeine-2.8.5.jar" com.github.benmanes.caffeine.SCQHeader`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Dependency:** qualify stdlib/declared packages; approve additions; classify JVM-only internals.

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
- [ ] **Step 4:** `FR-HOST-CAFFEINE-2-8-5-SCQ-HEADER-CONTRACT` → `com.github.benmanes.caffeine.SCQHeader`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** Wire qualified adapters to consumers; release resources on failure/shutdown.
- [ ] **Step 6:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_host_caffeine_2_8_5.py --no-cov`; expect expiry, eviction, invalidation and concurrent lookup; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture expiry, eviction, invalidation and concurrent lookup and visible failures.

# conscrypt-openjdk-uber.jar — FEAT-HOST-CONSCRYPT-OPENJDK-UBER

## 1. Objective

- **Goal:** Adapt server, TLS and protocol lifecycle through declared FastAPI/Uvicorn capabilities.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Connect the frontend to typed host discovery, sessions, jobs and resources.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/libs/conscrypt-openjdk-uber.jar`; 306 class declarations; SHA-256 `7ff18e73fe4ae752735db191108b23d90f52cc792bf3bdc5a1b774c01c809f64`.
- **Inspected reference:** No dedicated docs/sqx coverage; expand archive inspection; roadmap allocation `FEAT-HOST-CONSCRYPT-OPENJDK-UBER`.
- **Owner:** `app/host/transport/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Web-server lifecycle, handler mounting and optional TLS transports; downstream P03–P18.
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/libs/conscrypt-openjdk-uber.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/libs/conscrypt-openjdk-uber.jar" org.conscrypt.AbstractConscryptEngine`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Dependency:** qualify stdlib/declared packages; approve additions; classify JVM-only internals.

## 3. File Changes

- **Create:** `app/host/transport/server.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/host/transport/routes.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/host/transport/session.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/host/transport/events.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/host/transport/README.md`
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_host_conscrypt_openjdk_uber.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/host_conscrypt_openjdk_uber.json`
  - Store versioned paraphrased donor input/output fixtures.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Adapt server, TLS and protocol lifecycle through declared FastAPI/Uvicorn capabilities; verify startup failure, protocol compatibility, connection cleanup and TLS configuration.
- [ ] **Step 4:** `FR-HOST-CONSCRYPT-OPENJDK-UBER-ABSTRACT-CONSCRYPT-ENGINE-CONTRACT` → `org.conscrypt.AbstractConscryptEngine`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-HOST-CONSCRYPT-OPENJDK-UBER-ABSTRACT-CONSCRYPT-ENGINE-GET-PEER-HOST` → `org.conscrypt.AbstractConscryptEngine.getPeerHost`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** `FR-HOST-CONSCRYPT-OPENJDK-UBER-ABSTRACT-CONSCRYPT-ENGINE-GET-PEER-PORT` → `org.conscrypt.AbstractConscryptEngine.getPeerPort`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 7:** Wire qualified adapters to consumers; release resources on failure/shutdown.
- [ ] **Step 8:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_host_conscrypt_openjdk_uber.py --no-cov`; expect startup failure, protocol compatibility, connection cleanup and TLS configuration; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture startup failure, protocol compatibility, connection cleanup and TLS configuration and visible failures.

# fastutil.jar — FEAT-HOST-FASTUTIL

## 1. Objective

- **Goal:** Adapt consumed collection, string and utility contracts through Python primitives.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Connect the frontend to typed host discovery, sessions, jobs and resources.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/libs/fastutil.jar`; 10777 class declarations; SHA-256 `77249efd4f23d039515bcc0bfc973cf65ee560da0a26a9db7fa2532e11deb4e7`.
- **Inspected reference:** No dedicated docs/sqx coverage; expand archive inspection; roadmap allocation `FEAT-HOST-FASTUTIL`.
- **Owner:** `app/host/resources/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Cache/collection support; implement measured consumed policies via existing packages; downstream P03,P06,P09,P14.
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/libs/fastutil.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/libs/fastutil.jar" it.unimi.dsi.fastutil.AbstractIndirectPriorityQueue`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Dependency:** qualify stdlib/declared packages; approve additions; classify JVM-only internals.

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
- [ ] **Step 4:** `FR-HOST-FASTUTIL-ABSTRACT-INDIRECT-PRIORITY-QUEUE-CONTRACT` → `it.unimi.dsi.fastutil.AbstractIndirectPriorityQueue`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** Wire qualified adapters to consumers; release resources on failure/shutdown.
- [ ] **Step 6:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_host_fastutil.py --no-cov`; expect ordering, duplicate/null handling and bounded collection behavior; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture ordering, duplicate/null handling and bounded collection behavior and visible failures.

# fst.jar — FEAT-HOST-FST

## 1. Objective

- **Goal:** Replace consumed Java object serialization/construction with typed document codecs.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Connect the frontend to typed host discovery, sessions, jobs and resources.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/libs/fst.jar`; 220 class declarations; SHA-256 `ba57fdc0673ec3726921e5f113d906587d7f7000ba3981dfb79cc082929af3c1`.
- **Inspected reference:** No dedicated docs/sqx coverage; expand archive inspection; roadmap allocation `FEAT-HOST-FST`.
- **Owner:** `app/host/persistence/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Store/serialization/archive dependencies; store ownership and formats require validation; downstream P03,P07,P08,P13.
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/libs/fst.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/libs/fst.jar" org.nustaq.kson.ArgTypes`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Dependency:** qualify stdlib/declared packages; approve additions; classify JVM-only internals.

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
- [ ] **Step 4:** `FR-HOST-FST-ARG-TYPES-CONTRACT` → `org.nustaq.kson.ArgTypes`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** Wire qualified adapters to consumers; release resources on failure/shutdown.
- [ ] **Step 6:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_host_fst.py --no-cov`; expect version compatibility, invalid object shape and round-trip identity; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture version compatibility, invalid object shape and round-trip identity and visible failures.

# geronimo-json.jar — FEAT-HOST-GERONIMO-JSON

## 1. Objective

- **Goal:** Encode and validate typed JSON documents without Java object coupling.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Connect the frontend to typed host discovery, sessions, jobs and resources.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/libs/geronimo-json.jar`; 29 class declarations; SHA-256 `9ad66832295ebfb21e168f29e9411924e13e233ee2ddc61b9a9b09a3f18dc183`.
- **Inspected reference:** No dedicated docs/sqx coverage; expand archive inspection; roadmap allocation `FEAT-HOST-GERONIMO-JSON`.
- **Owner:** `app/host/documents/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** JSON/XML codecs and schema validation used by public or saved documents; downstream P03,P07–P13,P17.
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/libs/geronimo-json.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/libs/geronimo-json.jar" javax.json.Json`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Dependency:** qualify stdlib/declared packages; approve additions; classify JVM-only internals.

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
- [ ] **Step 4:** `FR-HOST-GERONIMO-JSON-JSON-CONTRACT` → `javax.json.Json`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-HOST-GERONIMO-JSON-JSON-CREATE-PARSER` → `javax.json.Json.createParser`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** `FR-HOST-GERONIMO-JSON-JSON-CREATE-GENERATOR` → `javax.json.Json.createGenerator`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 7:** Wire qualified adapters to consumers; release resources on failure/shutdown.
- [ ] **Step 8:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_host_geronimo_json.py --no-cov`; expect null/number handling, unknown fields and malformed payload; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture null/number handling, unknown fields and malformed payload and visible failures.

# h2.jar — FEAT-HOST-H2

## 1. Objective

- **Goal:** Map donor persistence behavior to a ratified host store capability.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Connect the frontend to typed host discovery, sessions, jobs and resources.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/libs/h2.jar`; 499 class declarations; SHA-256 `7c3e3b93ffaf617393126870be7f8e1708bbe8e05b931c51c638a8cb03f79a36`.
- **Inspected reference:** No dedicated docs/sqx coverage; expand archive inspection; roadmap allocation `FEAT-HOST-H2`.
- **Owner:** `app/host/persistence/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Store/serialization/archive dependencies; store ownership and formats require validation; downstream P03,P07,P08,P13.
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/libs/h2.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/libs/h2.jar" org.h2.Driver`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Dependency:** qualify stdlib/declared packages; approve additions; classify JVM-only internals.

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
- [ ] **Step 4:** `FR-HOST-H2-DRIVER-CONTRACT` → `org.h2.Driver`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-HOST-H2-DRIVER-CONNECT` → `org.h2.Driver.connect`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** `FR-HOST-H2-DRIVER-ACCEPTS-URL` → `org.h2.Driver.acceptsURL`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 7:** Wire qualified adapters to consumers; release resources on failure/shutdown.
- [ ] **Step 8:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_host_h2.py --no-cov`; expect transaction rollback, restart durability and retention in temporary stores; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture transaction rollback, restart durability and retention in temporary stores and visible failures.

# jackson-annotations.jar — FEAT-HOST-JACKSON-ANNOTATIONS

## 1. Objective

- **Goal:** Encode and validate typed JSON documents without Java object coupling.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Connect the frontend to typed host discovery, sessions, jobs and resources.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/libs/jackson-annotations.jar`; 74 class declarations; SHA-256 `959a2ffb2d591436f51f183c6a521fc89347912f711bf0cae008cdf045d95319`.
- **Inspected reference:** No dedicated docs/sqx coverage; expand archive inspection; roadmap allocation `FEAT-HOST-JACKSON-ANNOTATIONS`.
- **Owner:** `app/host/documents/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** JSON/XML codecs and schema validation used by public or saved documents; downstream P03,P07–P13,P17.
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/libs/jackson-annotations.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/libs/jackson-annotations.jar" com.fasterxml.jackson.annotation.JacksonAnnotation`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Dependency:** qualify stdlib/declared packages; approve additions; classify JVM-only internals.

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
- [ ] **Step 4:** `FR-HOST-JACKSON-ANNOTATIONS-JACKSON-ANNOTATION-CONTRACT` → `com.fasterxml.jackson.annotation.JacksonAnnotation`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** Wire qualified adapters to consumers; release resources on failure/shutdown.
- [ ] **Step 6:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_host_jackson_annotations.py --no-cov`; expect null/number handling, unknown fields and malformed payload; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture null/number handling, unknown fields and malformed payload and visible failures.

# jackson-core.jar — FEAT-HOST-JACKSON-CORE

## 1. Objective

- **Goal:** Encode and validate typed JSON documents without Java object coupling.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Connect the frontend to typed host discovery, sessions, jobs and resources.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/libs/jackson-core.jar`; 221 class declarations; SHA-256 `ffab4d957daa2796cf24cb66d0b78a7090f1bcbe17c3a4578f09affaaf137089`.
- **Inspected reference:** No dedicated docs/sqx coverage; expand archive inspection; roadmap allocation `FEAT-HOST-JACKSON-CORE`.
- **Owner:** `app/host/documents/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** JSON/XML codecs and schema validation used by public or saved documents; downstream P03,P07–P13,P17.
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/libs/jackson-core.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/libs/jackson-core.jar" com.fasterxml.jackson.core.Base64Variant`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Dependency:** qualify stdlib/declared packages; approve additions; classify JVM-only internals.

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
- [ ] **Step 4:** `FR-HOST-JACKSON-CORE-BASE64-VARIANT-CONTRACT` → `com.fasterxml.jackson.core.Base64Variant`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-HOST-JACKSON-CORE-BASE64-VARIANT-WITH-PADDING-ALLOWED` → `com.fasterxml.jackson.core.Base64Variant.withPaddingAllowed`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** `FR-HOST-JACKSON-CORE-BASE64-VARIANT-WITH-PADDING-REQUIRED` → `com.fasterxml.jackson.core.Base64Variant.withPaddingRequired`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 7:** Wire qualified adapters to consumers; release resources on failure/shutdown.
- [ ] **Step 8:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_host_jackson_core.py --no-cov`; expect null/number handling, unknown fields and malformed payload; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture null/number handling, unknown fields and malformed payload and visible failures.

# jackson-databind.jar — FEAT-HOST-JACKSON-DATABIND

## 1. Objective

- **Goal:** Encode and validate typed JSON documents without Java object coupling.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Connect the frontend to typed host discovery, sessions, jobs and resources.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/libs/jackson-databind.jar`; 809 class declarations; SHA-256 `34bbeb4526fff4f8565b12106bf85a6afcbae858966d489b54214ac46b2e26e8`.
- **Inspected reference:** No dedicated docs/sqx coverage; expand archive inspection; roadmap allocation `FEAT-HOST-JACKSON-DATABIND`.
- **Owner:** `app/host/documents/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** JSON/XML codecs and schema validation used by public or saved documents; downstream P03,P07–P13,P17.
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/libs/jackson-databind.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/libs/jackson-databind.jar" com.fasterxml.jackson.databind.AbstractTypeResolver`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Dependency:** qualify stdlib/declared packages; approve additions; classify JVM-only internals.

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
- [ ] **Step 4:** `FR-HOST-JACKSON-DATABIND-ABSTRACT-TYPE-RESOLVER-CONTRACT` → `com.fasterxml.jackson.databind.AbstractTypeResolver`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-HOST-JACKSON-DATABIND-ABSTRACT-TYPE-RESOLVER-FIND-TYPE-MAPPING` → `com.fasterxml.jackson.databind.AbstractTypeResolver.findTypeMapping`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** `FR-HOST-JACKSON-DATABIND-ABSTRACT-TYPE-RESOLVER-RESOLVE-ABSTRACT-TYPE` → `com.fasterxml.jackson.databind.AbstractTypeResolver.resolveAbstractType`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 7:** Wire qualified adapters to consumers; release resources on failure/shutdown.
- [ ] **Step 8:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_host_jackson_databind.py --no-cov`; expect null/number handling, unknown fields and malformed payload; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture null/number handling, unknown fields and malformed payload and visible failures.

# jdom.jar — FEAT-HOST-JDOM

## 1. Objective

- **Goal:** Parse and preserve supported XML document fields.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Connect the frontend to typed host discovery, sessions, jobs and resources.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/libs/jdom.jar`; 195 class declarations; SHA-256 `1345f11ba606d15603d6740551a8c21947c0215640770ec67271fe78bea97cf5`.
- **Inspected reference:** No dedicated docs/sqx coverage; expand archive inspection; roadmap allocation `FEAT-HOST-JDOM`.
- **Owner:** `app/host/documents/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** JSON/XML codecs and schema validation used by public or saved documents; downstream P03,P07–P13,P17.
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/libs/jdom.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/libs/jdom.jar" org.jdom2.Element`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Dependency:** qualify stdlib/declared packages; approve additions; classify JVM-only internals.

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
- [ ] **Step 4:** `FR-HOST-JDOM-ELEMENT-CONTRACT` → `org.jdom2.Element`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-HOST-JDOM-ELEMENT-SET-NAME` → `org.jdom2.Element.setName`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** `FR-HOST-JDOM-ELEMENT-GET-NAMESPACE` → `org.jdom2.Element.getNamespace`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 7:** Wire qualified adapters to consumers; release resources on failure/shutdown.
- [ ] **Step 8:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_host_jdom.py --no-cov`; expect namespaces, encoding, rejected unsafe constructs and lossless unknown fields; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture namespaces, encoding, rejected unsafe constructs and lossless unknown fields and visible failures.

# jetty-all-uber.jar — FEAT-HOST-JETTY-ALL-UBER

## 1. Objective

- **Goal:** Adapt server, TLS and protocol lifecycle through declared FastAPI/Uvicorn capabilities.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Connect the frontend to typed host discovery, sessions, jobs and resources.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/libs/jetty-all-uber.jar`; 1703 class declarations; SHA-256 `7ce8b3a1ed9852b9d7b16ba10a9db9a4fb42151845fd3fa3f9f45ac2ee416a98`.
- **Inspected reference:** No dedicated docs/sqx coverage; expand archive inspection; roadmap allocation `FEAT-HOST-JETTY-ALL-UBER`.
- **Owner:** `app/host/transport/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Web-server lifecycle, handler mounting and optional TLS transports; downstream P03–P18.
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/libs/jetty-all-uber.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/libs/jetty-all-uber.jar" org.eclipse.jetty.server.Server`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Dependency:** qualify stdlib/declared packages; approve additions; classify JVM-only internals.

## 3. File Changes

- **Modify:** `app/host/transport/server.py` (proposed earlier in FEAT-HOST-CONSCRYPT-OPENJDK-UBER)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/host/transport/routes.py` (proposed earlier in FEAT-HOST-CONSCRYPT-OPENJDK-UBER)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/host/transport/session.py` (proposed earlier in FEAT-HOST-CONSCRYPT-OPENJDK-UBER)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/host/transport/events.py` (proposed earlier in FEAT-HOST-CONSCRYPT-OPENJDK-UBER)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/host/transport/README.md` (proposed earlier in FEAT-HOST-CONSCRYPT-OPENJDK-UBER)
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_host_jetty_all_uber.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/host_jetty_all_uber.json`
  - Store versioned paraphrased donor input/output fixtures.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Adapt server, TLS and protocol lifecycle through declared FastAPI/Uvicorn capabilities; verify startup failure, protocol compatibility, connection cleanup and TLS configuration.
- [ ] **Step 4:** `FR-HOST-JETTY-ALL-UBER-SERVER-CONTRACT` → `org.eclipse.jetty.server.Server`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-HOST-JETTY-ALL-UBER-SERVER-IS-DRY-RUN` → `org.eclipse.jetty.server.Server.isDryRun`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** `FR-HOST-JETTY-ALL-UBER-SERVER-SET-DRY-RUN` → `org.eclipse.jetty.server.Server.setDryRun`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 7:** Wire qualified adapters to consumers; release resources on failure/shutdown.
- [ ] **Step 8:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_host_jetty_all_uber.py --no-cov`; expect startup failure, protocol compatibility, connection cleanup and TLS configuration; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture startup failure, protocol compatibility, connection cleanup and TLS configuration and visible failures.

# jetty-alpn-conscrypt-server.jar — FEAT-HOST-JETTY-ALPN-CONSCRYPT-SERVER

## 1. Objective

- **Goal:** Adapt server, TLS and protocol lifecycle through declared FastAPI/Uvicorn capabilities.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Connect the frontend to typed host discovery, sessions, jobs and resources.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/libs/jetty-alpn-conscrypt-server.jar`; 3 class declarations; SHA-256 `62d26efc17624827dc228fdaa4a13e5eb30df299a78293c247cfebe9e324a889`.
- **Inspected reference:** No dedicated docs/sqx coverage; expand archive inspection; roadmap allocation `FEAT-HOST-JETTY-ALPN-CONSCRYPT-SERVER`.
- **Owner:** `app/host/transport/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Web-server lifecycle, handler mounting and optional TLS transports; downstream P03–P18.
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/libs/jetty-alpn-conscrypt-server.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/libs/jetty-alpn-conscrypt-server.jar" org.eclipse.jetty.alpn.conscrypt.server.ConscryptServerALPNProcessor`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Dependency:** qualify stdlib/declared packages; approve additions; classify JVM-only internals.

## 3. File Changes

- **Modify:** `app/host/transport/server.py` (proposed earlier in FEAT-HOST-CONSCRYPT-OPENJDK-UBER)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/host/transport/routes.py` (proposed earlier in FEAT-HOST-CONSCRYPT-OPENJDK-UBER)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/host/transport/session.py` (proposed earlier in FEAT-HOST-CONSCRYPT-OPENJDK-UBER)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/host/transport/events.py` (proposed earlier in FEAT-HOST-CONSCRYPT-OPENJDK-UBER)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/host/transport/README.md` (proposed earlier in FEAT-HOST-CONSCRYPT-OPENJDK-UBER)
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_host_jetty_alpn_conscrypt_server.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/host_jetty_alpn_conscrypt_server.json`
  - Store versioned paraphrased donor input/output fixtures.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Adapt server, TLS and protocol lifecycle through declared FastAPI/Uvicorn capabilities; verify startup failure, protocol compatibility, connection cleanup and TLS configuration.
- [ ] **Step 4:** `FR-HOST-JETTY-ALPN-CONSCRYPT-SERVER-CONSCRYPT-SERVER-ALPN-PROCESSOR-CONTRACT` → `org.eclipse.jetty.alpn.conscrypt.server.ConscryptServerALPNProcessor`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-HOST-JETTY-ALPN-CONSCRYPT-SERVER-CONSCRYPT-SERVER-ALPN-PROCESSOR-INIT` → `org.eclipse.jetty.alpn.conscrypt.server.ConscryptServerALPNProcessor.init`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** `FR-HOST-JETTY-ALPN-CONSCRYPT-SERVER-CONSCRYPT-SERVER-ALPN-PROCESSOR-APPLIES-TO` → `org.eclipse.jetty.alpn.conscrypt.server.ConscryptServerALPNProcessor.appliesTo`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 7:** Wire qualified adapters to consumers; release resources on failure/shutdown.
- [ ] **Step 8:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_host_jetty_alpn_conscrypt_server.py --no-cov`; expect startup failure, protocol compatibility, connection cleanup and TLS configuration; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture startup failure, protocol compatibility, connection cleanup and TLS configuration and visible failures.

# jetty-alpn-java-server.jar — FEAT-HOST-JETTY-ALPN-JAVA-SERVER

## 1. Objective

- **Goal:** Adapt server, TLS and protocol lifecycle through declared FastAPI/Uvicorn capabilities.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Connect the frontend to typed host discovery, sessions, jobs and resources.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/libs/jetty-alpn-java-server.jar`; 3 class declarations; SHA-256 `3965c15329624b4b761f1af10121b0c5f57da7bbefe4a722d8f956fa1736ce82`.
- **Inspected reference:** No dedicated docs/sqx coverage; expand archive inspection; roadmap allocation `FEAT-HOST-JETTY-ALPN-JAVA-SERVER`.
- **Owner:** `app/host/transport/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Web-server lifecycle, handler mounting and optional TLS transports; downstream P03–P18.
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/libs/jetty-alpn-java-server.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/libs/jetty-alpn-java-server.jar" org.eclipse.jetty.alpn.java.server.JDK9ServerALPNProcessor`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Dependency:** qualify stdlib/declared packages; approve additions; classify JVM-only internals.

## 3. File Changes

- **Modify:** `app/host/transport/server.py` (proposed earlier in FEAT-HOST-CONSCRYPT-OPENJDK-UBER)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/host/transport/routes.py` (proposed earlier in FEAT-HOST-CONSCRYPT-OPENJDK-UBER)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/host/transport/session.py` (proposed earlier in FEAT-HOST-CONSCRYPT-OPENJDK-UBER)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/host/transport/events.py` (proposed earlier in FEAT-HOST-CONSCRYPT-OPENJDK-UBER)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/host/transport/README.md` (proposed earlier in FEAT-HOST-CONSCRYPT-OPENJDK-UBER)
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_host_jetty_alpn_java_server.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/host_jetty_alpn_java_server.json`
  - Store versioned paraphrased donor input/output fixtures.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Adapt server, TLS and protocol lifecycle through declared FastAPI/Uvicorn capabilities; verify startup failure, protocol compatibility, connection cleanup and TLS configuration.
- [ ] **Step 4:** `FR-HOST-JETTY-ALPN-JAVA-SERVER-JDK9-SERVER-ALPN-PROCESSOR-CONTRACT` → `org.eclipse.jetty.alpn.java.server.JDK9ServerALPNProcessor`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-HOST-JETTY-ALPN-JAVA-SERVER-JDK9-SERVER-ALPN-PROCESSOR-INIT` → `org.eclipse.jetty.alpn.java.server.JDK9ServerALPNProcessor.init`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** `FR-HOST-JETTY-ALPN-JAVA-SERVER-JDK9-SERVER-ALPN-PROCESSOR-APPLIES-TO` → `org.eclipse.jetty.alpn.java.server.JDK9ServerALPNProcessor.appliesTo`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 7:** Wire qualified adapters to consumers; release resources on failure/shutdown.
- [ ] **Step 8:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_host_jetty_alpn_java_server.py --no-cov`; expect startup failure, protocol compatibility, connection cleanup and TLS configuration; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture startup failure, protocol compatibility, connection cleanup and TLS configuration and visible failures.

# jetty-alpn-server.jar — FEAT-HOST-JETTY-ALPN-SERVER

## 1. Objective

- **Goal:** Adapt server, TLS and protocol lifecycle through declared FastAPI/Uvicorn capabilities.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Connect the frontend to typed host discovery, sessions, jobs and resources.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/libs/jetty-alpn-server.jar`; 2 class declarations; SHA-256 `a60f7cfcdc365a2b6c2f01ccc8d3122f5ff6ee6fd3e8331979ac0da71d9204ab`.
- **Inspected reference:** No dedicated docs/sqx coverage; expand archive inspection; roadmap allocation `FEAT-HOST-JETTY-ALPN-SERVER`.
- **Owner:** `app/host/transport/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Web-server lifecycle, handler mounting and optional TLS transports; downstream P03–P18.
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/libs/jetty-alpn-server.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/libs/jetty-alpn-server.jar" org.eclipse.jetty.alpn.server.ALPNServerConnection`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Dependency:** qualify stdlib/declared packages; approve additions; classify JVM-only internals.

## 3. File Changes

- **Modify:** `app/host/transport/server.py` (proposed earlier in FEAT-HOST-CONSCRYPT-OPENJDK-UBER)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/host/transport/routes.py` (proposed earlier in FEAT-HOST-CONSCRYPT-OPENJDK-UBER)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/host/transport/session.py` (proposed earlier in FEAT-HOST-CONSCRYPT-OPENJDK-UBER)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/host/transport/events.py` (proposed earlier in FEAT-HOST-CONSCRYPT-OPENJDK-UBER)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/host/transport/README.md` (proposed earlier in FEAT-HOST-CONSCRYPT-OPENJDK-UBER)
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_host_jetty_alpn_server.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/host_jetty_alpn_server.json`
  - Store versioned paraphrased donor input/output fixtures.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Adapt server, TLS and protocol lifecycle through declared FastAPI/Uvicorn capabilities; verify startup failure, protocol compatibility, connection cleanup and TLS configuration.
- [ ] **Step 4:** `FR-HOST-JETTY-ALPN-SERVER-ALPN-SERVER-CONNECTION-CONTRACT` → `org.eclipse.jetty.alpn.server.ALPNServerConnection`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-HOST-JETTY-ALPN-SERVER-ALPN-SERVER-CONNECTION-UNSUPPORTED` → `org.eclipse.jetty.alpn.server.ALPNServerConnection.unsupported`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** `FR-HOST-JETTY-ALPN-SERVER-ALPN-SERVER-CONNECTION-SELECT` → `org.eclipse.jetty.alpn.server.ALPNServerConnection.select`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 7:** Wire qualified adapters to consumers; release resources on failure/shutdown.
- [ ] **Step 8:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_host_jetty_alpn_server.py --no-cov`; expect startup failure, protocol compatibility, connection cleanup and TLS configuration; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture startup failure, protocol compatibility, connection cleanup and TLS configuration and visible failures.

# json-schema-validator.jar — FEAT-HOST-JSON-SCHEMA-VALIDATOR

## 1. Objective

- **Goal:** Validate versioned resource documents against ratified schemas.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Connect the frontend to typed host discovery, sessions, jobs and resources.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/libs/json-schema-validator.jar`; 313 class declarations; SHA-256 `ee940241043ae01801df5954bc3744bf723c449ff0da719f97e1b9a6889739d7`.
- **Inspected reference:** No dedicated docs/sqx coverage; expand archive inspection; roadmap allocation `FEAT-HOST-JSON-SCHEMA-VALIDATOR`.
- **Owner:** `app/host/documents/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** JSON/XML codecs and schema validation used by public or saved documents; downstream P03,P07–P13,P17.
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/libs/json-schema-validator.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/libs/json-schema-validator.jar" com.networknt.org.apache.commons.validator.routines.DomainValidator`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Dependency:** qualify stdlib/declared packages; approve additions; classify JVM-only internals.

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
- [ ] **Step 4:** `FR-HOST-JSON-SCHEMA-VALIDATOR-DOMAIN-VALIDATOR-CONTRACT` → `com.networknt.org.apache.commons.validator.routines.DomainValidator`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-HOST-JSON-SCHEMA-VALIDATOR-DOMAIN-VALIDATOR-GET-INSTANCE` → `com.networknt.org.apache.commons.validator.routines.DomainValidator.getInstance`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** `FR-HOST-JSON-SCHEMA-VALIDATOR-DOMAIN-VALIDATOR-GET-TLD-ENTRIES` → `com.networknt.org.apache.commons.validator.routines.DomainValidator.getTLDEntries`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 7:** Wire qualified adapters to consumers; release resources on failure/shutdown.
- [ ] **Step 8:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_host_json_schema_validator.py --no-cov`; expect required fields, schema versions and actionable validation errors; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture required fields, schema versions and actionable validation errors and visible failures.

# json.jar — FEAT-HOST-JSON

## 1. Objective

- **Goal:** Deliver the consumed json capability in host.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Connect the frontend to typed host discovery, sessions, jobs and resources.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/libs/json.jar`; 18 class declarations; SHA-256 `38c21b9c3d6d24919cd15d027d20afab0a019ac9205f7ed9083b32bdd42a2353`.
- **Inspected reference:** No dedicated docs/sqx coverage; expand archive inspection; roadmap allocation `FEAT-HOST-JSON`.
- **Owner:** `app/host/documents/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** JSON/XML codecs and schema validation used by public or saved documents; downstream P03,P07–P13,P17.
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/libs/json.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/libs/json.jar" org.json.JSONObject`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Dependency:** qualify stdlib/declared packages; approve additions; classify JVM-only internals.

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
- [ ] **Step 4:** `FR-HOST-JSON-JSON-OBJECT-CONTRACT` → `org.json.JSONObject`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-HOST-JSON-JSON-OBJECT-ACCUMULATE` → `org.json.JSONObject.accumulate`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** `FR-HOST-JSON-JSON-OBJECT-APPEND` → `org.json.JSONObject.append`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 7:** Wire qualified adapters to consumers; release resources on failure/shutdown.
- [ ] **Step 8:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_host_json.py --no-cov`; expect login/readiness/preferences, event correlation, restart durability and cancellation; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture login/readiness/preferences, event correlation, restart durability and cancellation and visible failures.

# jspf.core.jar — FEAT-HOST-JSPF-CORE

## 1. Objective

- **Goal:** Discover and bind typed plugin capabilities with lifecycle ownership.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Connect the frontend to typed host discovery, sessions, jobs and resources.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/libs/jspf.core.jar`; 295 class declarations; SHA-256 `94f287909bc8fb0970819f165cf091b08f1787053c9875824b6deb9a12ea0185`.
- **Inspected reference:** No dedicated docs/sqx coverage; expand archive inspection; roadmap allocation `FEAT-HOST-JSPF-CORE`.
- **Owner:** `app/host/discovery/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Typed discovery and registration infrastructure; downstream P03–P18.
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/libs/jspf.core.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/libs/jspf.core.jar" net.xeoh.plugins.base.PluginManager`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Dependency:** qualify stdlib/declared packages; approve additions; classify JVM-only internals.

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
- [ ] **Step 4:** `FR-HOST-JSPF-CORE-PLUGIN-MANAGER-CONTRACT` → `net.xeoh.plugins.base.PluginManager`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-HOST-JSPF-CORE-PLUGIN-MANAGER-ADD-PLUGINS-FROM` → `net.xeoh.plugins.base.PluginManager.addPluginsFrom`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** `FR-HOST-JSPF-CORE-PLUGIN-MANAGER-GET-PLUGIN` → `net.xeoh.plugins.base.PluginManager.getPlugin`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 7:** Wire qualified adapters to consumers; release resources on failure/shutdown.
- [ ] **Step 8:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_host_jspf_core.py --no-cov`; expect duplicate registration, compatibility failure and mount/unmount cleanup; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture duplicate registration, compatibility failure and mount/unmount cleanup and visible failures.

# lzma.jar — FEAT-HOST-LZMA

## 1. Objective

- **Goal:** Read/write supported bounded archives through host resource services.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Connect the frontend to typed host discovery, sessions, jobs and resources.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/libs/lzma.jar`; 30 class declarations; SHA-256 `4d389ab352c55955c790a54b3f93ebbbcb0b0936acbd2bec24aba587d0b2f99b`.
- **Inspected reference:** No dedicated docs/sqx coverage; expand archive inspection; roadmap allocation `FEAT-HOST-LZMA`.
- **Owner:** `app/host/persistence/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Store/serialization/archive dependencies; store ownership and formats require validation; downstream P03,P07,P08,P13.
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/libs/lzma.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/libs/lzma.jar" SevenZip.CRC`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Dependency:** qualify stdlib/declared packages; approve additions; classify JVM-only internals.

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
- **Create:** `tests/unit/sqx_features/test_host_lzma.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/host_lzma.json`
  - Store versioned paraphrased donor input/output fixtures.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Read/write supported bounded archives through host resource services; verify compression round trip, expansion limits, corrupt entry and traversal rejection.
- [ ] **Step 4:** `FR-HOST-LZMA-CRC-CONTRACT` → `SevenZip.CRC`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-HOST-LZMA-CRC-INIT` → `SevenZip.CRC.Init`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** `FR-HOST-LZMA-CRC-UPDATE` → `SevenZip.CRC.Update`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 7:** Wire qualified adapters to consumers; release resources on failure/shutdown.
- [ ] **Step 8:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_host_lzma.py --no-cov`; expect compression round trip, expansion limits, corrupt entry and traversal rejection; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture compression round trip, expansion limits, corrupt entry and traversal rejection and visible failures.

# objenesis.jar — FEAT-HOST-OBJENESIS

## 1. Objective

- **Goal:** Replace consumed Java object serialization/construction with typed document codecs.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Connect the frontend to typed host discovery, sessions, jobs and resources.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/libs/objenesis.jar`; 43 class declarations; SHA-256 `5e168368fbc250af3c79aa5fef0c3467a2d64e5a7bd74005f25d8399aeb0708d`.
- **Inspected reference:** No dedicated docs/sqx coverage; expand archive inspection; roadmap allocation `FEAT-HOST-OBJENESIS`.
- **Owner:** `app/host/persistence/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Store/serialization/archive dependencies; store ownership and formats require validation; downstream P03,P07,P08,P13.
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/libs/objenesis.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/libs/objenesis.jar" org.objenesis.Objenesis`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Dependency:** qualify stdlib/declared packages; approve additions; classify JVM-only internals.

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
- [ ] **Step 4:** `FR-HOST-OBJENESIS-OBJENESIS-CONTRACT` → `org.objenesis.Objenesis`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-HOST-OBJENESIS-OBJENESIS-NEW-INSTANCE` → `org.objenesis.Objenesis.newInstance`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** `FR-HOST-OBJENESIS-OBJENESIS-GET-INSTANTIATOR-OF` → `org.objenesis.Objenesis.getInstantiatorOf`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 7:** Wire qualified adapters to consumers; release resources on failure/shutdown.
- [ ] **Step 8:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_host_objenesis.py --no-cov`; expect version compatibility, invalid object shape and round-trip identity; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture version compatibility, invalid object shape and round-trip identity and visible failures.

# reactive-streams.jar — FEAT-HOST-REACTIVE-STREAMS

## 1. Objective

- **Goal:** Implement bounded owned event streams and cancellation.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Connect the frontend to typed host discovery, sessions, jobs and resources.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/libs/reactive-streams.jar`; 13 class declarations; SHA-256 `f75ca597789b3dac58f61857b9ac2e1034a68fa672db35055a8fb4509e325f28`.
- **Inspected reference:** No dedicated docs/sqx coverage; expand archive inspection; roadmap allocation `FEAT-HOST-REACTIVE-STREAMS`.
- **Owner:** `app/host/jobs/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Jobs and event/backpressure infrastructure; exact reactive consumers unresolved; downstream P04,P06,P09–P16.
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/libs/reactive-streams.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/libs/reactive-streams.jar" org.reactivestreams.FlowAdapters`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Dependency:** qualify stdlib/declared packages; approve additions; classify JVM-only internals.

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
- [ ] **Step 4:** `FR-HOST-REACTIVE-STREAMS-FLOW-ADAPTERS-CONTRACT` → `org.reactivestreams.FlowAdapters`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-HOST-REACTIVE-STREAMS-FLOW-ADAPTERS-TO-PUBLISHER` → `org.reactivestreams.FlowAdapters.toPublisher`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** `FR-HOST-REACTIVE-STREAMS-FLOW-ADAPTERS-TO-FLOW-PUBLISHER` → `org.reactivestreams.FlowAdapters.toFlowPublisher`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 7:** Wire qualified adapters to consumers; release resources on failure/shutdown.
- [ ] **Step 8:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_host_reactive_streams.py --no-cov`; expect ordering, backpressure, subscriber loss and resource release; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture ordering, backpressure, subscriber loss and resource release and visible failures.

# reactor-core.jar — FEAT-HOST-REACTOR-CORE

## 1. Objective

- **Goal:** Implement bounded owned event streams and cancellation.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Connect the frontend to typed host discovery, sessions, jobs and resources.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/libs/reactor-core.jar`; 946 class declarations; SHA-256 `14aebad4882def1f88389656cf9b46177f6b090bb00a0707025d76aeacaaead2`.
- **Inspected reference:** No dedicated docs/sqx coverage; expand archive inspection; roadmap allocation `FEAT-HOST-REACTOR-CORE`.
- **Owner:** `app/host/jobs/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Jobs and event/backpressure infrastructure; exact reactive consumers unresolved; downstream P04,P06,P09–P16.
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/libs/reactor-core.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/libs/reactor-core.jar" reactor.adapter.JdkFlowAdapter`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Dependency:** qualify stdlib/declared packages; approve additions; classify JVM-only internals.

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
- [ ] **Step 4:** `FR-HOST-REACTOR-CORE-JDK-FLOW-ADAPTER-CONTRACT` → `reactor.adapter.JdkFlowAdapter`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-HOST-REACTOR-CORE-JDK-FLOW-ADAPTER-PUBLISHER-TO-FLOW-PUBLISHER` → `reactor.adapter.JdkFlowAdapter.publisherToFlowPublisher`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** `FR-HOST-REACTOR-CORE-JDK-FLOW-ADAPTER-FLOW-PUBLISHER-TO-FLUX` → `reactor.adapter.JdkFlowAdapter.flowPublisherToFlux`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 7:** Wire qualified adapters to consumers; release resources on failure/shutdown.
- [ ] **Step 8:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_host_reactor_core.py --no-cov`; expect ordering, backpressure, subscriber loss and resource release; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture ordering, backpressure, subscriber loss and resource release and visible failures.

# SQJobsLib.jar — FEAT-HOST-SQ-JOBS-LIB

## 1. Objective

- **Goal:** Run owned jobs with typed states, cancellation and progress.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Connect the frontend to typed host discovery, sessions, jobs and resources.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/libs/SQJobsLib.jar`; 11 class declarations; SHA-256 `90a7d687dd4df30964512d8cd2cebf865f0bdcd9798b1310ed54007bf388ab5e`.
- **Inspected reference:** `HARUQUANTAI_ROOT/docs/sqx/Shared/SQJobsLib.md`; roadmap allocation `FEAT-HOST-SQ-JOBS-LIB`.
- **Owner:** `app/host/jobs/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Jobs and event/backpressure infrastructure; exact reactive consumers unresolved; downstream P04,P06,P09–P16.
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/libs/SQJobsLib.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/libs/SQJobsLib.jar" com.strategyquant.jobslib.JobEngine`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Dependency:** qualify stdlib/declared packages; approve additions; classify JVM-only internals.

## 3. File Changes

- **Modify:** `app/host/jobs/contracts.py` (proposed earlier in FEAT-HOST-REACTIVE-STREAMS)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/host/jobs/scheduler.py` (proposed earlier in FEAT-HOST-REACTIVE-STREAMS)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/host/jobs/events.py` (proposed earlier in FEAT-HOST-REACTIVE-STREAMS)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/host/jobs/README.md` (proposed earlier in FEAT-HOST-REACTIVE-STREAMS)
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_host_sq_jobs_lib.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/host_sq_jobs_lib.json`
  - Store versioned paraphrased donor input/output fixtures.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Run owned jobs with typed states, cancellation and progress; verify state transitions, concurrency limits, duplicate submit and cancellation.
- [ ] **Step 4:** `FR-HOST-SQ-JOBS-LIB-JOB-ENGINE-CONTRACT` → `com.strategyquant.jobslib.JobEngine`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-HOST-SQ-JOBS-LIB-JOB-ENGINE-SUBMIT` → `com.strategyquant.jobslib.JobEngine.submit`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** `FR-HOST-SQ-JOBS-LIB-JOB-ENGINE-JOBS` → `com.strategyquant.jobslib.JobEngine.jobs`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 7:** Wire qualified adapters to consumers; release resources on failure/shutdown.
- [ ] **Step 8:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_host_sq_jobs_lib.py --no-cov`; expect state transitions, concurrency limits, duplicate submit and cancellation; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture state transitions, concurrency limits, duplicate submit and cancellation and visible failures.

# sqlite-jdbc.jar — FEAT-HOST-SQLITE-JDBC

## 1. Objective

- **Goal:** Map donor persistence behavior to a ratified host store capability.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Connect the frontend to typed host discovery, sessions, jobs and resources.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/libs/sqlite-jdbc.jar`; 129 class declarations; SHA-256 `5454be00f3a04b4d67ef6179121aa900a904da53b9cbffea742d548d737f0ebc`.
- **Inspected reference:** No dedicated docs/sqx coverage; expand archive inspection; roadmap allocation `FEAT-HOST-SQLITE-JDBC`.
- **Owner:** `app/host/persistence/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Store/serialization/archive dependencies; store ownership and formats require validation; downstream P03,P07,P08,P13.
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/libs/sqlite-jdbc.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/libs/sqlite-jdbc.jar" org.sqlite.JDBC`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Dependency:** qualify stdlib/declared packages; approve additions; classify JVM-only internals.

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
- [ ] **Step 4:** `FR-HOST-SQLITE-JDBC-JDBC-CONTRACT` → `org.sqlite.JDBC`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-HOST-SQLITE-JDBC-JDBC-GET-MAJOR-VERSION` → `org.sqlite.JDBC.getMajorVersion`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** `FR-HOST-SQLITE-JDBC-JDBC-GET-MINOR-VERSION` → `org.sqlite.JDBC.getMinorVersion`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 7:** Wire qualified adapters to consumers; release resources on failure/shutdown.
- [ ] **Step 8:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_host_sqlite_jdbc.py --no-cov`; expect transaction rollback, restart durability and retention in temporary stores; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture transaction rollback, restart durability and retention in temporary stores and visible failures.

# SQPluginLib.jar — FEAT-HOST-SQ-PLUGIN-LIB

## 1. Objective

- **Goal:** Discover and bind typed plugin capabilities with lifecycle ownership.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Connect the frontend to typed host discovery, sessions, jobs and resources.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/libs/SQPluginLib.jar`; 18 class declarations; SHA-256 `40c962d2087d68aadb4bc4a3b9bb2363a453cb57830fd672c50716d502e771c3`.
- **Inspected reference:** `HARUQUANTAI_ROOT/docs/sqx/Shared/SQPluginLib.md`; roadmap allocation `FEAT-HOST-SQ-PLUGIN-LIB`.
- **Owner:** `app/host/discovery/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Typed discovery and registration infrastructure; downstream P03–P18.
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/libs/SQPluginLib.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/libs/SQPluginLib.jar" com.strategyquant.pluginlib.SQPluginManager`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Dependency:** qualify stdlib/declared packages; approve additions; classify JVM-only internals.

## 3. File Changes

- **Modify:** `app/host/discovery/contracts.py` (proposed earlier in FEAT-HOST-JSPF-CORE)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/host/discovery/registry.py` (proposed earlier in FEAT-HOST-JSPF-CORE)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/host/discovery/loader.py` (proposed earlier in FEAT-HOST-JSPF-CORE)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/host/discovery/README.md` (proposed earlier in FEAT-HOST-JSPF-CORE)
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_host_sq_plugin_lib.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/host_sq_plugin_lib.json`
  - Store versioned paraphrased donor input/output fixtures.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Discover and bind typed plugin capabilities with lifecycle ownership; verify duplicate registration, compatibility failure and mount/unmount cleanup.
- [ ] **Step 4:** `FR-HOST-SQ-PLUGIN-LIB-SQ-PLUGIN-MANAGER-CONTRACT` → `com.strategyquant.pluginlib.SQPluginManager`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-HOST-SQ-PLUGIN-LIB-SQ-PLUGIN-MANAGER-LOAD-PLUGINS` → `com.strategyquant.pluginlib.SQPluginManager.loadPlugins`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** `FR-HOST-SQ-PLUGIN-LIB-SQ-PLUGIN-MANAGER-GET-PLUGINS` → `com.strategyquant.pluginlib.SQPluginManager.getPlugins`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 7:** Wire qualified adapters to consumers; release resources on failure/shutdown.
- [ ] **Step 8:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_host_sq_plugin_lib.py --no-cov`; expect duplicate registration, compatibility failure and mount/unmount cleanup; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture duplicate registration, compatibility failure and mount/unmount cleanup and visible failures.

# SQWebGUILib.jar — FEAT-HOST-SQ-WEB-GUI-LIB

## 1. Objective

- **Goal:** Expose typed host/UI transport with sessions, errors and events.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Connect the frontend to typed host discovery, sessions, jobs and resources.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/libs/SQWebGUILib.jar`; 34 class declarations; SHA-256 `3a319dc358d46207a0e4520c6dacb694039a3d5c35b0069c08a7e869aa6fd0af`.
- **Inspected reference:** `HARUQUANTAI_ROOT/docs/sqx/Shared/SQWebGUILib.md`; roadmap allocation `FEAT-HOST-SQ-WEB-GUI-LIB`.
- **Owner:** `app/host/transport/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Web-server lifecycle, handler mounting and optional TLS transports; downstream P03–P18.
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/libs/SQWebGUILib.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/libs/SQWebGUILib.jar" com.strategyquant.webguilib.server.AbstractUIWebServer`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Dependency:** qualify stdlib/declared packages; approve additions; classify JVM-only internals.

## 3. File Changes

- **Modify:** `app/host/transport/server.py` (proposed earlier in FEAT-HOST-CONSCRYPT-OPENJDK-UBER)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/host/transport/routes.py` (proposed earlier in FEAT-HOST-CONSCRYPT-OPENJDK-UBER)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/host/transport/session.py` (proposed earlier in FEAT-HOST-CONSCRYPT-OPENJDK-UBER)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/host/transport/events.py` (proposed earlier in FEAT-HOST-CONSCRYPT-OPENJDK-UBER)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/host/transport/README.md` (proposed earlier in FEAT-HOST-CONSCRYPT-OPENJDK-UBER)
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_host_sq_web_gui_lib.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/host_sq_web_gui_lib.json`
  - Store versioned paraphrased donor input/output fixtures.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Expose typed host/UI transport with sessions, errors and events; verify request correlation, unauthorized access, reconnect and domain mounting.
- [ ] **Step 4:** `FR-HOST-SQ-WEB-GUI-LIB-ABSTRACT-UI-WEB-SERVER-CONTRACT` → `com.strategyquant.webguilib.server.AbstractUIWebServer`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-HOST-SQ-WEB-GUI-LIB-ABSTRACT-UI-WEB-SERVER-START` → `com.strategyquant.webguilib.server.AbstractUIWebServer.start`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** `FR-HOST-SQ-WEB-GUI-LIB-ABSTRACT-UI-WEB-SERVER-STOP` → `com.strategyquant.webguilib.server.AbstractUIWebServer.stop`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 7:** Wire qualified adapters to consumers; release resources on failure/shutdown.
- [ ] **Step 8:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_host_sq_web_gui_lib.py --no-cov`; expect request correlation, unauthorized access, reconnect and domain mounting; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture request correlation, unauthorized access, reconnect and domain mounting and visible failures.

# zip4j.jar — FEAT-HOST-ZIP4J

## 1. Objective

- **Goal:** Read/write supported bounded archives through host resource services.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Connect the frontend to typed host discovery, sessions, jobs and resources.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/libs/zip4j.jar`; 60 class declarations; SHA-256 `92524aa1bf716f1d15e75fb66c2212ee903e118677ca625506f94487628317f7`.
- **Inspected reference:** No dedicated docs/sqx coverage; expand archive inspection; roadmap allocation `FEAT-HOST-ZIP4J`.
- **Owner:** `app/host/persistence/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Store/serialization/archive dependencies; store ownership and formats require validation; downstream P03,P07,P08,P13.
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/libs/zip4j.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/libs/zip4j.jar" net.lingala.zip4j.core.HeaderReader`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Dependency:** qualify stdlib/declared packages; approve additions; classify JVM-only internals.

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
- [ ] **Step 4:** `FR-HOST-ZIP4J-HEADER-READER-CONTRACT` → `net.lingala.zip4j.core.HeaderReader`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-HOST-ZIP4J-HEADER-READER-READ-ALL-HEADERS` → `net.lingala.zip4j.core.HeaderReader.readAllHeaders`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** `FR-HOST-ZIP4J-HEADER-READER-READ-LOCAL-FILE-HEADER` → `net.lingala.zip4j.core.HeaderReader.readLocalFileHeader`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 7:** Wire qualified adapters to consumers; release resources on failure/shutdown.
- [ ] **Step 8:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_host_zip4j.py --no-cov`; expect compression round trip, expansion limits, corrupt entry and traversal rejection; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture compression round trip, expansion limits, corrupt entry and traversal rejection and visible failures.

# P02 integration — Connect the frontend to typed host discovery, sessions, jobs and resources

## 1. Objective

- **Goal:** Connect the frontend to typed host discovery, sessions, jobs and resources.
- **Context / Problem Solved:** The existing UI needs a real end-to-end backend workflow, beyond isolated JAR adapters.

## 2. Research and donors

- **Roadmap:** `HARUQUANTAI_ROOT/docs/dev/sqx-full-application-roadmap.md`, P02; donor features and FRs are the tasks in this file.
- **Existing code:** `ui/app/host/transport.ts`, `HostConnection.tsx`, `hostSettings.ts`; backend counterparts are proposed.
- **Declared dependencies:** FastAPI, Pydantic, Uvicorn, psutil; host persistence choice remains unratified.
- **Existing tests:** No audited phase backend suite; create the integration tests below.
- **Conflict/gap:** frontend existence does not establish functional backend behavior; route/schema/discovery changes need a task plan and approval.
- **Cross-feature ownership:** shared files may host multiple features; keep per-FR traces and delegate persistence/jobs to host capabilities.

## 3. File Changes

- **Modify:** `app/host/discovery/contracts.py` (proposed earlier in FEAT-HOST-JSPF-CORE)
  - Deliver the phase's typed contracts and integration flow; extend prior approved owners where shared.
- **Modify:** `app/host/discovery/registry.py` (proposed earlier in FEAT-HOST-JSPF-CORE)
  - Deliver the phase's typed contracts and integration flow; extend prior approved owners where shared.
- **Modify:** `app/host/discovery/loader.py` (proposed earlier in FEAT-HOST-JSPF-CORE)
  - Deliver the phase's typed contracts and integration flow; extend prior approved owners where shared.
- **Modify:** `app/host/transport/server.py` (proposed earlier in FEAT-HOST-CONSCRYPT-OPENJDK-UBER)
  - Deliver the phase's typed contracts and integration flow; extend prior approved owners where shared.
- **Modify:** `app/host/transport/routes.py` (proposed earlier in FEAT-HOST-CONSCRYPT-OPENJDK-UBER)
  - Deliver the phase's typed contracts and integration flow; extend prior approved owners where shared.
- **Modify:** `app/host/transport/session.py` (proposed earlier in FEAT-HOST-CONSCRYPT-OPENJDK-UBER)
  - Deliver the phase's typed contracts and integration flow; extend prior approved owners where shared.
- **Modify:** `app/host/transport/events.py` (proposed earlier in FEAT-HOST-CONSCRYPT-OPENJDK-UBER)
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

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Review preceding feature fixtures and owning README registrations; ratify the phase integration contracts and execution plan.
- [ ] **Step 2:** Ratify capability registration, compatibility and HTTP/event envelopes with frontend counterparts.
- [ ] **Step 3:** Implement sessions, authenticated events, job scheduling/cancellation and bounded resource handles.
- [ ] **Step 4:** Provide host-owned document validation and isolated store transactions; verify mount/unmount cleanup.
- [ ] **Step 5:** Replace fixture-driven production execution in the affected workflow; retain deterministic fixtures only in tests.
- [ ] **Step 6:** Test positive/failure/cancellation paths and observable FR logs; reload/reconnect and reconcile persisted outputs.
- [ ] **Step 7:** Record exact commands, timestamped artifacts, unresolved gaps and walkthrough; obtain separate owner commit authority.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/integration/test_host_services_workflow.py --no-cov`; `npm --prefix ui run test:ui -- tests/e2e/sqx-host-services-backend.spec.ts`. Assert login/readiness/preferences, event correlation, restart durability and cancellation; reject unauthorized call, incompatible plugin, queue overflow and transaction failure.
- **Manual / Browser Verification:** Connect the shell; change a preference; reconnect; cancel a real job; unmount a capability and confirm dependent controls disable.

## Phase completion gate

- [ ] Reconcile all allocated FEAT/FR dispositions, donor fixtures and ownership gaps.
- [ ] Run Ruff format/check and strict Mypy on the approved changed Python paths; verify branch-aware coverage ≥80% across retained application source at release.
- [ ] For affected UI: `npm --prefix ui run typecheck`, `npm --prefix ui run test`, `npm --prefix ui run build`.
- [ ] Record real workflow observations, timestamps, failure artifacts and remaining gaps in the walkthrough.
- [ ] Obtain the next task/phase approval; commits and external/destructive actions retain separate owner gates.

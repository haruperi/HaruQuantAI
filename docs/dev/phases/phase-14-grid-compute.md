# P14 — Grid Control, Grid Test and compute execution

- **Source:** `HARUQUANTAI_ROOT/docs/dev/sqx-full-application-roadmap.md`; SHA-256 `9abec0aa2faf6bd78b39e80c2dcfb7dfcae62ae412d9b56a77904de6a7b5a54c`.
- **Dependencies:** P02,P06,P09,P10,P11,P13.
- **Scope:** 11 JAR feature tasks, 0 resource tasks, one phase integration task.
- **State:** proposed checklists; all execution, registrations and target contracts require task-level approval.
- **File labels:** existing paths are Modify; absent paths are Create; later shared edits name their earlier proposed owner.
- **Execution standard:** AGENTS.md plan → approval → implementation → tests → walkthrough; canonical Python docstrings, typed public APIs and explicit FR logs.
- **Clean room:** donor signatures guide behavioral research; independently written implementations; no proprietary source in evidence; no parity claim without independent validation.
- **Verification:** commands below are future tasks, not reported passes; isolated stores only; no live-store schema change/restore or Git mutation.

# affinity.jar — FEAT-COMPUTE-AFFINITY

## 1. Objective

- **Goal:** Adapt consumed process/platform probes and placement through declared psutil/OS capabilities.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Run owned distributed jobs with compatible workers and bounded messaging.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/libs/affinity.jar`; 52 class declarations; SHA-256 `66d40c208001d33b0223a528b661a962be424b69b089b42581548b2bbcb71b49`.
- **Inspected reference:** No dedicated docs/sqx coverage; expand archive inspection; roadmap allocation `FEAT-COMPUTE-AFFINITY`.
- **Owner:** `app/plugins/compute/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Compute/grid messaging, remote registration and worker placement; downstream P06,P09–P13,P15.
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/libs/affinity.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/libs/affinity.jar" net.openhft.affinity.Affinity`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Dependency:** qualify stdlib/declared packages; approve additions; classify JVM-only internals.

## 3. File Changes

- **Create:** `app/plugins/compute/workers.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/compute/protocol.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/compute/queue.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/compute/placement.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/compute/README.md`
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_compute_affinity.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/compute_affinity.json`
  - Store versioned paraphrased donor input/output fixtures.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Adapt consumed process/platform probes and placement through declared psutil/OS capabilities; verify unsupported probe, process lifetime and bounded sampling.
- [ ] **Step 4:** `FR-COMPUTE-AFFINITY-AFFINITY-CONTRACT` → `net.openhft.affinity.Affinity`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-COMPUTE-AFFINITY-AFFINITY-VALUES` → `net.openhft.affinity.Affinity.values`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** `FR-COMPUTE-AFFINITY-AFFINITY-VALUE-OF` → `net.openhft.affinity.Affinity.valueOf`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 7:** Wire qualified adapters to consumers; release resources on failure/shutdown.
- [ ] **Step 8:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_compute_affinity.py --no-cov`; expect unsupported probe, process lifetime and bounded sampling; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture unsupported probe, process lifetime and bounded sampling and visible failures.

# artemis-commons.jar — FEAT-COMPUTE-ARTEMIS-COMMONS

## 1. Objective

- **Goal:** Implement compatible compute messages, worker admission and job ownership.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Run owned distributed jobs with compatible workers and bounded messaging.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/libs/artemis-commons.jar`; 153 class declarations; SHA-256 `9134161c80f5972dece8f7c933075ee33cf557a42e2d24bed7f9f2d1cc249a00`.
- **Inspected reference:** No dedicated docs/sqx coverage; expand archive inspection; roadmap allocation `FEAT-COMPUTE-ARTEMIS-COMMONS`.
- **Owner:** `app/plugins/compute/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Compute/grid messaging, remote registration and worker placement; downstream P06,P09–P13,P15.
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/libs/artemis-commons.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/libs/artemis-commons.jar" org.apache.activemq.artemis.ArtemisConstants`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Dependency:** qualify stdlib/declared packages; approve additions; classify JVM-only internals.

## 3. File Changes

- **Modify:** `app/plugins/compute/workers.py` (proposed earlier in FEAT-COMPUTE-AFFINITY)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/plugins/compute/protocol.py` (proposed earlier in FEAT-COMPUTE-AFFINITY)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/plugins/compute/queue.py` (proposed earlier in FEAT-COMPUTE-AFFINITY)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/plugins/compute/placement.py` (proposed earlier in FEAT-COMPUTE-AFFINITY)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/plugins/compute/README.md` (proposed earlier in FEAT-COMPUTE-AFFINITY)
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_compute_artemis_commons.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/compute_artemis_commons.json`
  - Store versioned paraphrased donor input/output fixtures.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Implement compatible compute messages, worker admission and job ownership; verify delivery identity, stale lease, retry, backpressure and remote failure.
- [ ] **Step 4:** `FR-COMPUTE-ARTEMIS-COMMONS-ARTEMIS-CONSTANTS-CONTRACT` → `org.apache.activemq.artemis.ArtemisConstants`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** Wire qualified adapters to consumers; release resources on failure/shutdown.
- [ ] **Step 6:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_compute_artemis_commons.py --no-cov`; expect delivery identity, stale lease, retry, backpressure and remote failure; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture delivery identity, stale lease, retry, backpressure and remote failure and visible failures.

# artemis-core-client.jar — FEAT-COMPUTE-ARTEMIS-CORE-CLIENT

## 1. Objective

- **Goal:** Implement compatible compute messages, worker admission and job ownership.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Run owned distributed jobs with compatible workers and bounded messaging.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/libs/artemis-core-client.jar`; 359 class declarations; SHA-256 `14d38e4e405f3b597dfa23a82544664140dcd67e86bbc174e2b7d1c59770087f`.
- **Inspected reference:** No dedicated docs/sqx coverage; expand archive inspection; roadmap allocation `FEAT-COMPUTE-ARTEMIS-CORE-CLIENT`.
- **Owner:** `app/plugins/compute/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Compute/grid messaging, remote registration and worker placement; downstream P06,P09–P13,P15.
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/libs/artemis-core-client.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/libs/artemis-core-client.jar" org.apache.activemq.artemis.api.config.ActiveMQDefaultConfiguration`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Dependency:** qualify stdlib/declared packages; approve additions; classify JVM-only internals.

## 3. File Changes

- **Modify:** `app/plugins/compute/workers.py` (proposed earlier in FEAT-COMPUTE-AFFINITY)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/plugins/compute/protocol.py` (proposed earlier in FEAT-COMPUTE-AFFINITY)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/plugins/compute/queue.py` (proposed earlier in FEAT-COMPUTE-AFFINITY)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/plugins/compute/placement.py` (proposed earlier in FEAT-COMPUTE-AFFINITY)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/plugins/compute/README.md` (proposed earlier in FEAT-COMPUTE-AFFINITY)
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_compute_artemis_core_client.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/compute_artemis_core_client.json`
  - Store versioned paraphrased donor input/output fixtures.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Implement compatible compute messages, worker admission and job ownership; verify delivery identity, stale lease, retry, backpressure and remote failure.
- [ ] **Step 4:** `FR-COMPUTE-ARTEMIS-CORE-CLIENT-ACTIVE-MQ-DEFAULT-CONFIGURATION-CONTRACT` → `org.apache.activemq.artemis.api.config.ActiveMQDefaultConfiguration`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-COMPUTE-ARTEMIS-CORE-CLIENT-ACTIVE-MQ-DEFAULT-CONFIGURATION-GET-DEFAULT-CLIENT-FAILURE-CHECK-PERIOD` → `org.apache.activemq.artemis.api.config.ActiveMQDefaultConfiguration.getDefaultClientFailureCheckPeriod`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** `FR-COMPUTE-ARTEMIS-CORE-CLIENT-ACTIVE-MQ-DEFAULT-CONFIGURATION-GET-DEFAULT-FILE-DEPLOYER-SCAN-PERIOD` → `org.apache.activemq.artemis.api.config.ActiveMQDefaultConfiguration.getDefaultFileDeployerScanPeriod`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 7:** Wire qualified adapters to consumers; release resources on failure/shutdown.
- [ ] **Step 8:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_compute_artemis_core_client.py --no-cov`; expect delivery identity, stale lease, retry, backpressure and remote failure; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture delivery identity, stale lease, retry, backpressure and remote failure and visible failures.

# artemis-jms-client.jar — FEAT-COMPUTE-ARTEMIS-JMS-CLIENT

## 1. Objective

- **Goal:** Implement compatible compute messages, worker admission and job ownership.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Run owned distributed jobs with compatible workers and bounded messaging.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/libs/artemis-jms-client.jar`; 92 class declarations; SHA-256 `4222e99981a27e0d096b3f27433b0e4149a01c45fc0ddd8251aa0f7ed5c21bec`.
- **Inspected reference:** No dedicated docs/sqx coverage; expand archive inspection; roadmap allocation `FEAT-COMPUTE-ARTEMIS-JMS-CLIENT`.
- **Owner:** `app/plugins/compute/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Compute/grid messaging, remote registration and worker placement; downstream P06,P09–P13,P15.
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/libs/artemis-jms-client.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/libs/artemis-jms-client.jar" org.apache.activemq.artemis.api.jms.ActiveMQJMSClient`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Dependency:** qualify stdlib/declared packages; approve additions; classify JVM-only internals.

## 3. File Changes

- **Modify:** `app/plugins/compute/workers.py` (proposed earlier in FEAT-COMPUTE-AFFINITY)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/plugins/compute/protocol.py` (proposed earlier in FEAT-COMPUTE-AFFINITY)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/plugins/compute/queue.py` (proposed earlier in FEAT-COMPUTE-AFFINITY)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/plugins/compute/placement.py` (proposed earlier in FEAT-COMPUTE-AFFINITY)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/plugins/compute/README.md` (proposed earlier in FEAT-COMPUTE-AFFINITY)
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_compute_artemis_jms_client.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/compute_artemis_jms_client.json`
  - Store versioned paraphrased donor input/output fixtures.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Implement compatible compute messages, worker admission and job ownership; verify delivery identity, stale lease, retry, backpressure and remote failure.
- [ ] **Step 4:** `FR-COMPUTE-ARTEMIS-JMS-CLIENT-ACTIVE-MQJMS-CLIENT-CONTRACT` → `org.apache.activemq.artemis.api.jms.ActiveMQJMSClient`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-COMPUTE-ARTEMIS-JMS-CLIENT-ACTIVE-MQJMS-CLIENT-CREATE-CONNECTION-FACTORY` → `org.apache.activemq.artemis.api.jms.ActiveMQJMSClient.createConnectionFactory`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** `FR-COMPUTE-ARTEMIS-JMS-CLIENT-ACTIVE-MQJMS-CLIENT-CREATE-CONNECTION-FACTORY-WITH-HA` → `org.apache.activemq.artemis.api.jms.ActiveMQJMSClient.createConnectionFactoryWithHA`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 7:** Wire qualified adapters to consumers; release resources on failure/shutdown.
- [ ] **Step 8:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_compute_artemis_jms_client.py --no-cov`; expect delivery identity, stale lease, retry, backpressure and remote failure; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture delivery identity, stale lease, retry, backpressure and remote failure and visible failures.

# artemis-selector.jar — FEAT-COMPUTE-ARTEMIS-SELECTOR

## 1. Objective

- **Goal:** Implement compatible compute messages, worker admission and job ownership.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Run owned distributed jobs with compatible workers and bounded messaging.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/libs/artemis-selector.jar`; 56 class declarations; SHA-256 `e078da2c298014b047e963c5ae88cb885ba9092deb141e55e8fefb2b25edca17`.
- **Inspected reference:** No dedicated docs/sqx coverage; expand archive inspection; roadmap allocation `FEAT-COMPUTE-ARTEMIS-SELECTOR`.
- **Owner:** `app/plugins/compute/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Compute/grid messaging, remote registration and worker placement; downstream P06,P09–P13,P15.
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/libs/artemis-selector.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/libs/artemis-selector.jar" org.apache.activemq.artemis.selector.filter.ArithmeticExpression`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Dependency:** qualify stdlib/declared packages; approve additions; classify JVM-only internals.

## 3. File Changes

- **Modify:** `app/plugins/compute/workers.py` (proposed earlier in FEAT-COMPUTE-AFFINITY)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/plugins/compute/protocol.py` (proposed earlier in FEAT-COMPUTE-AFFINITY)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/plugins/compute/queue.py` (proposed earlier in FEAT-COMPUTE-AFFINITY)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/plugins/compute/placement.py` (proposed earlier in FEAT-COMPUTE-AFFINITY)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/plugins/compute/README.md` (proposed earlier in FEAT-COMPUTE-AFFINITY)
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_compute_artemis_selector.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/compute_artemis_selector.json`
  - Store versioned paraphrased donor input/output fixtures.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Implement compatible compute messages, worker admission and job ownership; verify delivery identity, stale lease, retry, backpressure and remote failure.
- [ ] **Step 4:** `FR-COMPUTE-ARTEMIS-SELECTOR-ARITHMETIC-EXPRESSION-CONTRACT` → `org.apache.activemq.artemis.selector.filter.ArithmeticExpression`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-COMPUTE-ARTEMIS-SELECTOR-ARITHMETIC-EXPRESSION-CREATE-PLUS` → `org.apache.activemq.artemis.selector.filter.ArithmeticExpression.createPlus`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** `FR-COMPUTE-ARTEMIS-SELECTOR-ARITHMETIC-EXPRESSION-CREATE-MINUS` → `org.apache.activemq.artemis.selector.filter.ArithmeticExpression.createMinus`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 7:** Wire qualified adapters to consumers; release resources on failure/shutdown.
- [ ] **Step 8:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_compute_artemis_selector.py --no-cov`; expect delivery identity, stale lease, retry, backpressure and remote failure; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture delivery identity, stale lease, retry, backpressure and remote failure and visible failures.

# geronimo-jms.jar — FEAT-COMPUTE-GERONIMO-JMS

## 1. Objective

- **Goal:** Implement compatible compute messages, worker admission and job ownership.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Run owned distributed jobs with compatible workers and bounded messaging.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/libs/geronimo-jms.jar`; 81 class declarations; SHA-256 `62a109edef3de718b0cb600bf040b4be5e32c683a57ee16f9f8a89537bf5da51`.
- **Inspected reference:** No dedicated docs/sqx coverage; expand archive inspection; roadmap allocation `FEAT-COMPUTE-GERONIMO-JMS`.
- **Owner:** `app/plugins/compute/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Compute/grid messaging, remote registration and worker placement; downstream P06,P09–P13,P15.
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/libs/geronimo-jms.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/libs/geronimo-jms.jar" javax.jms.BytesMessage`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Dependency:** qualify stdlib/declared packages; approve additions; classify JVM-only internals.

## 3. File Changes

- **Modify:** `app/plugins/compute/workers.py` (proposed earlier in FEAT-COMPUTE-AFFINITY)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/plugins/compute/protocol.py` (proposed earlier in FEAT-COMPUTE-AFFINITY)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/plugins/compute/queue.py` (proposed earlier in FEAT-COMPUTE-AFFINITY)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/plugins/compute/placement.py` (proposed earlier in FEAT-COMPUTE-AFFINITY)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/plugins/compute/README.md` (proposed earlier in FEAT-COMPUTE-AFFINITY)
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_compute_geronimo_jms.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/compute_geronimo_jms.json`
  - Store versioned paraphrased donor input/output fixtures.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Implement compatible compute messages, worker admission and job ownership; verify delivery identity, stale lease, retry, backpressure and remote failure.
- [ ] **Step 4:** `FR-COMPUTE-GERONIMO-JMS-BYTES-MESSAGE-CONTRACT` → `javax.jms.BytesMessage`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-COMPUTE-GERONIMO-JMS-BYTES-MESSAGE-GET-BODY-LENGTH` → `javax.jms.BytesMessage.getBodyLength`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** `FR-COMPUTE-GERONIMO-JMS-BYTES-MESSAGE-READ-BOOLEAN` → `javax.jms.BytesMessage.readBoolean`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 7:** Wire qualified adapters to consumers; release resources on failure/shutdown.
- [ ] **Step 8:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_compute_geronimo_jms.py --no-cov`; expect delivery identity, stale lease, retry, backpressure and remote failure; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture delivery identity, stale lease, retry, backpressure and remote failure and visible failures.

# jspf.remote.jar — FEAT-COMPUTE-JSPF-REMOTE

## 1. Objective

- **Goal:** Implement compatible compute messages, worker admission and job ownership.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Run owned distributed jobs with compatible workers and bounded messaging.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/libs/jspf.remote.jar`; 6 class declarations; SHA-256 `9987cca1d084129a024a5c7132e561a039c9ec933cc8ebe8697bf89e79412652`.
- **Inspected reference:** No dedicated docs/sqx coverage; expand archive inspection; roadmap allocation `FEAT-COMPUTE-JSPF-REMOTE`.
- **Owner:** `app/plugins/compute/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Compute/grid messaging, remote registration and worker placement; downstream P06,P09–P13,P15.
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/libs/jspf.remote.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/libs/jspf.remote.jar" net.xeoh.plugins.remote.ExportResult`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Dependency:** qualify stdlib/declared packages; approve additions; classify JVM-only internals.

## 3. File Changes

- **Modify:** `app/plugins/compute/workers.py` (proposed earlier in FEAT-COMPUTE-AFFINITY)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/plugins/compute/protocol.py` (proposed earlier in FEAT-COMPUTE-AFFINITY)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/plugins/compute/queue.py` (proposed earlier in FEAT-COMPUTE-AFFINITY)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/plugins/compute/placement.py` (proposed earlier in FEAT-COMPUTE-AFFINITY)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/plugins/compute/README.md` (proposed earlier in FEAT-COMPUTE-AFFINITY)
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_compute_jspf_remote.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/compute_jspf_remote.json`
  - Store versioned paraphrased donor input/output fixtures.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Implement compatible compute messages, worker admission and job ownership; verify delivery identity, stale lease, retry, backpressure and remote failure.
- [ ] **Step 4:** `FR-COMPUTE-JSPF-REMOTE-EXPORT-RESULT-CONTRACT` → `net.xeoh.plugins.remote.ExportResult`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-COMPUTE-JSPF-REMOTE-EXPORT-RESULT-GET-EXPORT-UR-IS` → `net.xeoh.plugins.remote.ExportResult.getExportURIs`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** Wire qualified adapters to consumers; release resources on failure/shutdown.
- [ ] **Step 7:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_compute_jspf_remote.py --no-cov`; expect delivery identity, stale lease, retry, backpressure and remote failure; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture delivery identity, stale lease, retry, backpressure and remote failure and visible failures.

# SQGridLib2.jar — FEAT-COMPUTE-SQ-GRID-LIB2

## 1. Objective

- **Goal:** Implement compatible compute messages, worker admission and job ownership.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Run owned distributed jobs with compatible workers and bounded messaging.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/libs/SQGridLib2.jar`; 81 class declarations; SHA-256 `dd1851fada0ebe511c16fd422472d938465b0d3a971a5718d4448ee9c4183673`.
- **Inspected reference:** `HARUQUANTAI_ROOT/docs/sqx/Shared/SQGridLib2.md`; roadmap allocation `FEAT-COMPUTE-SQ-GRID-LIB2`.
- **Owner:** `app/plugins/compute/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Compute/grid messaging, remote registration and worker placement; downstream P06,P09–P13,P15.
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/libs/SQGridLib2.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/libs/SQGridLib2.jar" com.strategyquant.gridlib.client.GridClient`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Dependency:** qualify stdlib/declared packages; approve additions; classify JVM-only internals.

## 3. File Changes

- **Modify:** `app/plugins/compute/workers.py` (proposed earlier in FEAT-COMPUTE-AFFINITY)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/plugins/compute/protocol.py` (proposed earlier in FEAT-COMPUTE-AFFINITY)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/plugins/compute/queue.py` (proposed earlier in FEAT-COMPUTE-AFFINITY)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/plugins/compute/placement.py` (proposed earlier in FEAT-COMPUTE-AFFINITY)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/plugins/compute/README.md` (proposed earlier in FEAT-COMPUTE-AFFINITY)
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_compute_sq_grid_lib2.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/compute_sq_grid_lib2.json`
  - Store versioned paraphrased donor input/output fixtures.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Implement compatible compute messages, worker admission and job ownership; verify delivery identity, stale lease, retry, backpressure and remote failure.
- [ ] **Step 4:** `FR-COMPUTE-SQ-GRID-LIB2-GRID-CLIENT-CONTRACT` → `com.strategyquant.gridlib.client.GridClient`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-COMPUTE-SQ-GRID-LIB2-GRID-CLIENT-GET-CONFIG` → `com.strategyquant.gridlib.client.GridClient.getConfig`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** `FR-COMPUTE-SQ-GRID-LIB2-GRID-CLIENT-JOB-FINISHED` → `com.strategyquant.gridlib.client.GridClient.jobFinished`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 7:** Wire qualified adapters to consumers; release resources on failure/shutdown.
- [ ] **Step 8:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_compute_sq_grid_lib2.py --no-cov`; expect delivery identity, stale lease, retry, backpressure and remote failure; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture delivery identity, stale lease, retry, backpressure and remote failure and visible failures.

# AppGridControl.jar — FEAT-COMPUTE-APP-GRID-CONTROL

## 1. Objective

- **Goal:** Mount the GridControl workspace against real backend capabilities.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Run owned distributed jobs with compatible workers and bounded messaging.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/plugins/AppGridControl/AppGridControl.jar`; 1 class declarations; SHA-256 `1e71d9a8e6c722b542ceea77c98ebf4496f119756fd4596753ba8917c5252e4f`.
- **Inspected reference:** `HARUQUANTAI_ROOT/docs/sqx/GridControl/AppGridControl.md`; roadmap allocation `FEAT-COMPUTE-APP-GRID-CONTROL`.
- **Owner:** `app/workspace/GridControl/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Workspace/product registration and backend composition; downstream .
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/plugins/AppGridControl/AppGridControl.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/plugins/AppGridControl/AppGridControl.jar" com.strategyquant.plugin.App.impl.GridControl.GridControlAppPlugin`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

## 3. File Changes

- **Create:** `app/workspace/GridControl/workspace.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/workspace/GridControl/routes.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/workspace/GridControl/contracts.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/workspace/GridControl/README.md`
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_compute_app_grid_control.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/compute_app_grid_control.json`
  - Store versioned paraphrased donor input/output fixtures.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Mount the GridControl workspace against real backend capabilities; verify discovery, workspace readiness, job/resource ownership and unmount cleanup.
- [ ] **Step 4:** `FR-COMPUTE-APP-GRID-CONTROL-GRID-CONTROL-APP-PLUGIN-CONTRACT` → `com.strategyquant.plugin.App.impl.GridControl.GridControlAppPlugin`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-COMPUTE-APP-GRID-CONTROL-GRID-CONTROL-APP-PLUGIN-GET-PREFERRED-POSITION` → `com.strategyquant.plugin.App.impl.GridControl.GridControlAppPlugin.getPreferredPosition`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** `FR-COMPUTE-APP-GRID-CONTROL-GRID-CONTROL-APP-PLUGIN-INIT-PLUGIN` → `com.strategyquant.plugin.App.impl.GridControl.GridControlAppPlugin.initPlugin`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 7:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 8:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_compute_app_grid_control.py --no-cov`; expect discovery, workspace readiness, job/resource ownership and unmount cleanup; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture discovery, workspace readiness, job/resource ownership and unmount cleanup and visible failures.

# AppGridTest.jar — FEAT-COMPUTE-APP-GRID-TEST

## 1. Objective

- **Goal:** Mount the GridTest workspace against real backend capabilities.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Run owned distributed jobs with compatible workers and bounded messaging.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/plugins/AppGridTest/AppGridTest.jar`; 1 class declarations; SHA-256 `8d0b4a1b3f095fb57652b98b4ca870754d02e8fff6d8992c753e9120c3c5c78b`.
- **Inspected reference:** `HARUQUANTAI_ROOT/docs/sqx/GridTest/AppGridTest.md`; roadmap allocation `FEAT-COMPUTE-APP-GRID-TEST`.
- **Owner:** `app/workspace/GridTest/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Workspace/product registration and backend composition; downstream .
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/plugins/AppGridTest/AppGridTest.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/plugins/AppGridTest/AppGridTest.jar" com.strategyquant.plugin.App.impl.GridTest.GridTestAppPlugin`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

## 3. File Changes

- **Create:** `app/workspace/GridTest/workspace.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/workspace/GridTest/routes.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/workspace/GridTest/contracts.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/workspace/GridTest/README.md`
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_compute_app_grid_test.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/compute_app_grid_test.json`
  - Store versioned paraphrased donor input/output fixtures.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Mount the GridTest workspace against real backend capabilities; verify discovery, workspace readiness, job/resource ownership and unmount cleanup.
- [ ] **Step 4:** `FR-COMPUTE-APP-GRID-TEST-GRID-TEST-APP-PLUGIN-CONTRACT` → `com.strategyquant.plugin.App.impl.GridTest.GridTestAppPlugin`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-COMPUTE-APP-GRID-TEST-GRID-TEST-APP-PLUGIN-GET-PREFERRED-POSITION` → `com.strategyquant.plugin.App.impl.GridTest.GridTestAppPlugin.getPreferredPosition`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** `FR-COMPUTE-APP-GRID-TEST-GRID-TEST-APP-PLUGIN-INIT-PLUGIN` → `com.strategyquant.plugin.App.impl.GridTest.GridTestAppPlugin.initPlugin`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 7:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 8:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_compute_app_grid_test.py --no-cov`; expect discovery, workspace readiness, job/resource ownership and unmount cleanup; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture discovery, workspace readiness, job/resource ownership and unmount cleanup and visible failures.

# ServletGridControl.jar — FEAT-COMPUTE-SERVLET-GRID-CONTROL

## 1. Objective

- **Goal:** Expose GridControl commands through the owning domain routes.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Run owned distributed jobs with compatible workers and bounded messaging.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/plugins/ServletGridControl/ServletGridControl.jar`; 2 class declarations; SHA-256 `0d5288f68c62da3e1ddbdbae2b1ba2221b3822045c50bb74613c3b3d4af51476`.
- **Inspected reference:** `HARUQUANTAI_ROOT/docs/sqx/GridControl/ServletGridControl.md`; roadmap allocation `FEAT-COMPUTE-SERVLET-GRID-CONTROL`.
- **Owner:** `app/workspace/GridControl/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Grid-management API; downstream .
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/plugins/ServletGridControl/ServletGridControl.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/plugins/ServletGridControl/ServletGridControl.jar" com.strategyquant.plugin.Servlet.impl.GridControl.GridControlServlet`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

## 3. File Changes

- **Modify:** `app/workspace/GridControl/routes.py` (proposed earlier in FEAT-COMPUTE-APP-GRID-CONTROL)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/workspace/GridControl/contracts.py` (proposed earlier in FEAT-COMPUTE-APP-GRID-CONTROL)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/workspace/GridControl/README.md` (proposed earlier in FEAT-COMPUTE-APP-GRID-CONTROL)
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_compute_servlet_grid_control.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/compute_servlet_grid_control.json`
  - Store versioned paraphrased donor input/output fixtures.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Expose GridControl commands through the owning domain routes; verify command parsing, typed outputs, authority, validation errors and cancellation.
- [ ] **Step 4:** `FR-COMPUTE-SERVLET-GRID-CONTROL-GRID-CONTROL-SERVLET-CONTRACT` → `com.strategyquant.plugin.Servlet.impl.GridControl.GridControlServlet`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-COMPUTE-SERVLET-GRID-CONTROL-GRID-CONTROL-SERVLET-EXECUTE` → `com.strategyquant.plugin.Servlet.impl.GridControl.GridControlServlet.execute`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 7:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_compute_servlet_grid_control.py --no-cov`; expect command parsing, typed outputs, authority, validation errors and cancellation; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture command parsing, typed outputs, authority, validation errors and cancellation and visible failures.

# P14 integration — Run owned distributed jobs with compatible workers and bounded messaging

## 1. Objective

- **Goal:** Run owned distributed jobs with compatible workers and bounded messaging.
- **Context / Problem Solved:** The existing UI needs a real end-to-end backend workflow, beyond isolated JAR adapters.

## 2. Research and donors

- **Roadmap:** `HARUQUANTAI_ROOT/docs/dev/sqx-full-application-roadmap.md`, P14; donor features and FRs are the tasks in this file.
- **Existing code:** `ui/app/workspace/GridControl/GridControlWorkspace.tsx`, `ui/app/workspace/GridTest/GridTestWorkspace.tsx`; backend counterparts are proposed.
- **Declared dependencies:** FastAPI, Pydantic, Uvicorn, psutil; host persistence choice remains unratified.
- **Existing tests:** `ui/tests/unit/workspace/GridControl/gridControl.test.ts`; extend actual-backend assertions.
- **Conflict/gap:** frontend existence does not establish functional backend behavior; route/schema/discovery changes need a task plan and approval.
- **Cross-feature ownership:** shared files may host multiple features; keep per-FR traces and delegate persistence/jobs to host capabilities.

## 3. File Changes

- **Modify:** `app/plugins/compute/workers.py` (proposed earlier in FEAT-COMPUTE-AFFINITY)
  - Deliver the phase's typed contracts and integration flow; extend prior approved owners where shared.
- **Modify:** `app/plugins/compute/protocol.py` (proposed earlier in FEAT-COMPUTE-AFFINITY)
  - Deliver the phase's typed contracts and integration flow; extend prior approved owners where shared.
- **Modify:** `app/plugins/compute/queue.py` (proposed earlier in FEAT-COMPUTE-AFFINITY)
  - Deliver the phase's typed contracts and integration flow; extend prior approved owners where shared.
- **Modify:** `app/plugins/compute/placement.py` (proposed earlier in FEAT-COMPUTE-AFFINITY)
  - Deliver the phase's typed contracts and integration flow; extend prior approved owners where shared.
- **Modify:** `app/workspace/GridControl/routes.py` (proposed earlier in FEAT-COMPUTE-APP-GRID-CONTROL)
  - Deliver the phase's typed contracts and integration flow; extend prior approved owners where shared.
- **Modify:** `app/workspace/GridTest/routes.py` (proposed earlier in FEAT-COMPUTE-APP-GRID-TEST)
  - Deliver the phase's typed contracts and integration flow; extend prior approved owners where shared.
- **Modify:** `ui/app/workspace/GridControl/GridControlWorkspace.tsx`
  - Bind real capability state, errors and cancellation while preserving the existing layout.
- **Create:** `ui/app/workspace/GridControl/gridControlClient.ts`
  - Own typed routes/envelopes for this domain; replace mock execution with authoritative requests.
- **Modify:** `ui/app/workspace/GridTest/GridTestWorkspace.tsx`
  - Bind real capability state, errors and cancellation while preserving the existing layout.
- **Create:** `ui/app/workspace/GridTest/gridTestClient.ts`
  - Own typed routes/envelopes for this domain; replace mock execution with authoritative requests.
- **Modify:** `app/plugins/compute/README.md` (proposed earlier in FEAT-COMPUTE-AFFINITY)
  - Own feature registration/status and phase contract decisions after ratification.
- **Create:** `tests/integration/test_grid_compute_workflow.py`
  - Exercise the real phase workflow in isolated stores with failure/cancellation assertions.
- **Create:** `ui/tests/e2e/sqx-grid-compute-backend.spec.ts`
  - Use an isolated real host to verify UI state and request/output reconciliation.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Review preceding feature fixtures and owning README registrations; ratify the phase integration contracts and execution plan.
- [ ] **Step 2:** Specify worker versions, placement, protocol envelopes, leases and duplicate-delivery handling.
- [ ] **Step 3:** Implement registration, scheduling, heartbeat/loss, retry/cancellation and resource cleanup.
- [ ] **Step 4:** Connect GridControl status/actions and GridTest repeatable benchmarks to real worker runs.
- [ ] **Step 5:** Replace fixture-driven production execution in the affected workflow; retain deterministic fixtures only in tests.
- [ ] **Step 6:** Test positive/failure/cancellation paths and observable FR logs; reload/reconnect and reconcile persisted outputs.
- [ ] **Step 7:** Record exact commands, timestamped artifacts, unresolved gaps and walkthrough; obtain separate owner commit authority.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/integration/test_grid_compute_workflow.py --no-cov`; `npm --prefix ui run test -- tests/unit/workspace/GridControl/gridControl.test.ts`; `npm --prefix ui run test:ui -- tests/e2e/sqx-grid-compute-backend.spec.ts`. Assert local/remote result equivalence, worker admission and placement/benchmark accounting; reject lost worker, stale lease, duplicate result, incompatible version and queue overload.
- **Manual / Browser Verification:** Register a test worker; dispatch a fixture job; disconnect it; verify bounded recovery; run GridTest and reconcile completed counts.

## Phase completion gate

- [ ] Reconcile all allocated FEAT/FR dispositions, donor fixtures and ownership gaps.
- [ ] Run Ruff format/check and strict Mypy on the approved changed Python paths; verify branch-aware coverage ≥80% across retained application source at release.
- [ ] For affected UI: `npm --prefix ui run typecheck`, `npm --prefix ui run test`, `npm --prefix ui run build`.
- [ ] Record real workflow observations, timestamps, failure artifacts and remaining gaps in the walkthrough.
- [ ] Obtain the next task/phase approval; commits and external/destructive actions retain separate owner gates.

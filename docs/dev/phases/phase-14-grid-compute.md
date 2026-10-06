# P14 — Grid Control, Grid Test and compute execution

- **Source:** `HARUQUANTAI_ROOT/docs/dev/sqx-full-application-roadmap.md`; current-only source inventory `docs/dev/evidence/p00-inventory.json`.
- **Dependencies:** P02,P06,P09,P10,P11,P13.
- **State:** proposed checklists; all execution, registrations and target contracts require task-level approval.
- **File labels:** existing paths are Modify; absent paths are Create; later shared edits name their earlier proposed owner.
- **Execution standard:** AGENTS.md plan → approval → implementation → tests → walkthrough; canonical Python docstrings, typed public APIs and explicit FR logs.
- **Clean room:** donor signatures guide behavioral research; independently written implementations; no proprietary source in evidence; no parity claim without independent validation.
- **Verification:** commands below are future tasks, not reported passes; isolated stores only; no live-store schema change/restore or Git mutation.
- **UI completion:** Applicable features finish with backend + retained UI connected; preserve layouts. Production mocks cannot substitute for capability execution; keep a task unchecked while transport/contracts or required controls are unresolved.
- **Connected verification:** Use an isolated real host and temporary data. Existing mock-only/browser-API-blocking suites are UI regressions, not connected acceptance. Run `npm --prefix ui run typecheck`, `npm --prefix ui run test`, `npm --prefix ui run build` after actual UI source changes.



- **Donor baseline:** SQX145 Dev 1 only; all source fingerprints and member seeds use `SQX_145_REFERENCE_ROOT`. Missing bodies remain prerequisites.
- **Scope:** 13 tasks; current archive allocations and resource/integration tasks only.

# 14.1 FEAT-COMPUTE-AFFINITY - affinity-3.23.3.jar

## 1. Objective

- **Goal:** Adapt consumed process/platform probes and placement through declared psutil/OS capabilities.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Run owned distributed jobs with compatible workers and bounded messaging.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/libs/affinity-3.23.3.jar`; 49 raw class entries; SHA-256 `969e4b4ad761e34f3c5d59fe173bba08623bbf4e9002bc567665626886f01928`.
- **Inspected reference:** [affinity-3.23.3.md](../../sqx/Libraries/affinity-3.23.3.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/libs/affinity-3.23.3.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/libs/affinity-3.23.3.jar" net.openhft.affinity.Affinity`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/plugins/compute/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Compute/grid messaging, remote registration and worker placement; downstream P06,P09–P13,P15.
- **Dependency:** qualify stdlib/declared packages; approve additions; classify JVM-only internals.

- **UI disposition:** Infrastructure only; no standalone UI component found in this library allocation. Its owned backend consumer feeds Grid Control/Test through the phase integration gate; do not invent a library screen or direct plugin route.

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
- [ ] **Step 4:** Wire qualified adapters to consumers; release resources on failure/shutdown.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Verify UI-facing consumer contract: Test this infrastructure through its declared backend/host consumer; expose failures through the owning domain envelope. The phase's connected UI gate verifies the observable workflow.


- [ ] **Step 7:** `FR-COMPUTE-AFFINITY-AFFINITY-CONTRACT` → `net.openhft.affinity.Affinity`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 8:** `FR-COMPUTE-AFFINITY-AFFINITY-VALUES` → `net.openhft.affinity.Affinity.values()[Lnet/openhft/affinity/Affinity;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-COMPUTE-AFFINITY-AFFINITY-VALUE-OF` → `net.openhft.affinity.Affinity.valueOf(Ljava/lang/String;)Lnet/openhft/affinity/Affinity;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_compute_affinity.py --no-cov`; expect unsupported probe, process lifetime and bounded sampling; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture unsupported probe, process lifetime and bounded sampling and visible failures.


# 14.2 FEAT-COMPUTE-ARTEMIS-COMMONS - artemis-commons-1.5.0.jar

## 1. Objective

- **Goal:** Implement compatible compute messages, worker admission and job ownership.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Run owned distributed jobs with compatible workers and bounded messaging.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/libs/artemis-commons-1.5.0.jar`; 153 raw class entries; SHA-256 `9134161c80f5972dece8f7c933075ee33cf557a42e2d24bed7f9f2d1cc249a00`.
- **Inspected reference:** [artemis-commons-1.5.0.md](../../sqx/Libraries/artemis-commons-1.5.0.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/libs/artemis-commons-1.5.0.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/libs/artemis-commons-1.5.0.jar" org.apache.activemq.artemis.ArtemisConstants`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/plugins/compute/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Compute/grid messaging, remote registration and worker placement; downstream P06,P09–P13,P15.
- **Dependency:** qualify stdlib/declared packages; approve additions; classify JVM-only internals.

- **UI disposition:** Infrastructure only; no standalone UI component found in this library allocation. Its owned backend consumer feeds Grid Control/Test through the phase integration gate; do not invent a library screen or direct plugin route.

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
- [ ] **Step 4:** Wire qualified adapters to consumers; release resources on failure/shutdown.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Verify UI-facing consumer contract: Test this infrastructure through its declared backend/host consumer; expose failures through the owning domain envelope. The phase's connected UI gate verifies the observable workflow.


- [ ] **Step 7:** `FR-COMPUTE-ARTEMIS-COMMONS-ARTEMIS-CONSTANTS-CONTRACT` → `org.apache.activemq.artemis.ArtemisConstants`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_compute_artemis_commons.py --no-cov`; expect delivery identity, stale lease, retry, backpressure and remote failure; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture delivery identity, stale lease, retry, backpressure and remote failure and visible failures.


# 14.3 FEAT-COMPUTE-ARTEMIS-CORE-CLIENT - artemis-core-client-1.5.0.jar

## 1. Objective

- **Goal:** Implement compatible compute messages, worker admission and job ownership.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Run owned distributed jobs with compatible workers and bounded messaging.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/libs/artemis-core-client-1.5.0.jar`; 359 raw class entries; SHA-256 `14d38e4e405f3b597dfa23a82544664140dcd67e86bbc174e2b7d1c59770087f`.
- **Inspected reference:** [artemis-core-client-1.5.0.md](../../sqx/Libraries/artemis-core-client-1.5.0.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/libs/artemis-core-client-1.5.0.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/libs/artemis-core-client-1.5.0.jar" org.apache.activemq.artemis.api.config.ActiveMQDefaultConfiguration`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/plugins/compute/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Compute/grid messaging, remote registration and worker placement; downstream P06,P09–P13,P15.
- **Dependency:** qualify stdlib/declared packages; approve additions; classify JVM-only internals.

- **UI disposition:** Infrastructure only; no standalone UI component found in this library allocation. Its owned backend consumer feeds Grid Control/Test through the phase integration gate; do not invent a library screen or direct plugin route.

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
- [ ] **Step 4:** Wire qualified adapters to consumers; release resources on failure/shutdown.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Verify UI-facing consumer contract: Test this infrastructure through its declared backend/host consumer; expose failures through the owning domain envelope. The phase's connected UI gate verifies the observable workflow.


- [ ] **Step 7:** `FR-COMPUTE-ARTEMIS-CORE-CLIENT-ACTIVE-MQDEFAULT-CONFIGURATION-CONTRACT` → `org.apache.activemq.artemis.api.config.ActiveMQDefaultConfiguration`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 8:** `FR-COMPUTE-ARTEMIS-CORE-CLIENT-ACTIVE-MQDEFAULT-CONFIGURATION-GET-DEFAULT-CLIENT-FAILURE-CHECK-PERIOD` → `org.apache.activemq.artemis.api.config.ActiveMQDefaultConfiguration.getDefaultClientFailureCheckPeriod()J`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-COMPUTE-ARTEMIS-CORE-CLIENT-ACTIVE-MQDEFAULT-CONFIGURATION-GET-DEFAULT-FILE-DEPLOYER-SCAN-PERIOD` → `org.apache.activemq.artemis.api.config.ActiveMQDefaultConfiguration.getDefaultFileDeployerScanPeriod()J`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_compute_artemis_core_client.py --no-cov`; expect delivery identity, stale lease, retry, backpressure and remote failure; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture delivery identity, stale lease, retry, backpressure and remote failure and visible failures.


# 14.4 FEAT-COMPUTE-ARTEMIS-JMS-CLIENT - artemis-jms-client-1.5.0.jar

## 1. Objective

- **Goal:** Implement compatible compute messages, worker admission and job ownership.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Run owned distributed jobs with compatible workers and bounded messaging.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/libs/artemis-jms-client-1.5.0.jar`; 92 raw class entries; SHA-256 `4222e99981a27e0d096b3f27433b0e4149a01c45fc0ddd8251aa0f7ed5c21bec`.
- **Inspected reference:** [artemis-jms-client-1.5.0.md](../../sqx/Libraries/artemis-jms-client-1.5.0.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/libs/artemis-jms-client-1.5.0.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/libs/artemis-jms-client-1.5.0.jar" org.apache.activemq.artemis.api.jms.ActiveMQJMSClient`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/plugins/compute/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Compute/grid messaging, remote registration and worker placement; downstream P06,P09–P13,P15.
- **Dependency:** qualify stdlib/declared packages; approve additions; classify JVM-only internals.

- **UI disposition:** Infrastructure only; no standalone UI component found in this library allocation. Its owned backend consumer feeds Grid Control/Test through the phase integration gate; do not invent a library screen or direct plugin route.

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
- [ ] **Step 4:** Wire qualified adapters to consumers; release resources on failure/shutdown.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Verify UI-facing consumer contract: Test this infrastructure through its declared backend/host consumer; expose failures through the owning domain envelope. The phase's connected UI gate verifies the observable workflow.


- [ ] **Step 7:** `FR-COMPUTE-ARTEMIS-JMS-CLIENT-ACTIVE-MQJMSCLIENT-CONTRACT` → `org.apache.activemq.artemis.api.jms.ActiveMQJMSClient`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 8:** `FR-COMPUTE-ARTEMIS-JMS-CLIENT-ACTIVE-MQJMSCLIENT-CREATE-CONNECTION-FACTORY` → `org.apache.activemq.artemis.api.jms.ActiveMQJMSClient.createConnectionFactory(Ljava/lang/String;Ljava/lang/String;)Lorg/apache/activemq/artemis/jms/client/ActiveMQConnectionFactory;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-COMPUTE-ARTEMIS-JMS-CLIENT-ACTIVE-MQJMSCLIENT-CREATE-CONNECTION-FACTORY-WITH-HA` → `org.apache.activemq.artemis.api.jms.ActiveMQJMSClient.createConnectionFactoryWithHA(Lorg/apache/activemq/artemis/api/core/DiscoveryGroupConfiguration;Lorg/apache/activemq/artemis/api/jms/JMSFactoryType;)Lorg/apache/activemq/artemis/jms/client/ActiveMQConnectionFactory;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_compute_artemis_jms_client.py --no-cov`; expect delivery identity, stale lease, retry, backpressure and remote failure; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture delivery identity, stale lease, retry, backpressure and remote failure and visible failures.


# 14.5 FEAT-COMPUTE-ARTEMIS-SELECTOR - artemis-selector-1.5.0.jar

## 1. Objective

- **Goal:** Implement compatible compute messages, worker admission and job ownership.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Run owned distributed jobs with compatible workers and bounded messaging.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/libs/artemis-selector-1.5.0.jar`; 56 raw class entries; SHA-256 `e078da2c298014b047e963c5ae88cb885ba9092deb141e55e8fefb2b25edca17`.
- **Inspected reference:** [artemis-selector-1.5.0.md](../../sqx/Libraries/artemis-selector-1.5.0.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/libs/artemis-selector-1.5.0.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/libs/artemis-selector-1.5.0.jar" org.apache.activemq.artemis.selector.filter.ArithmeticExpression`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/plugins/compute/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Compute/grid messaging, remote registration and worker placement; downstream P06,P09–P13,P15.
- **Dependency:** qualify stdlib/declared packages; approve additions; classify JVM-only internals.

- **UI disposition:** Infrastructure only; no standalone UI component found in this library allocation. Its owned backend consumer feeds Grid Control/Test through the phase integration gate; do not invent a library screen or direct plugin route.

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
- [ ] **Step 4:** Wire qualified adapters to consumers; release resources on failure/shutdown.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Verify UI-facing consumer contract: Test this infrastructure through its declared backend/host consumer; expose failures through the owning domain envelope. The phase's connected UI gate verifies the observable workflow.


- [ ] **Step 7:** `FR-COMPUTE-ARTEMIS-SELECTOR-ARITHMETIC-EXPRESSION-CONTRACT` → `org.apache.activemq.artemis.selector.filter.ArithmeticExpression`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 8:** `FR-COMPUTE-ARTEMIS-SELECTOR-ARITHMETIC-EXPRESSION-CREATE-PLUS` → `org.apache.activemq.artemis.selector.filter.ArithmeticExpression.createPlus(Lorg/apache/activemq/artemis/selector/filter/Expression;Lorg/apache/activemq/artemis/selector/filter/Expression;)Lorg/apache/activemq/artemis/selector/filter/Expression;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-COMPUTE-ARTEMIS-SELECTOR-ARITHMETIC-EXPRESSION-CREATE-MINUS` → `org.apache.activemq.artemis.selector.filter.ArithmeticExpression.createMinus(Lorg/apache/activemq/artemis/selector/filter/Expression;Lorg/apache/activemq/artemis/selector/filter/Expression;)Lorg/apache/activemq/artemis/selector/filter/Expression;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_compute_artemis_selector.py --no-cov`; expect delivery identity, stale lease, retry, backpressure and remote failure; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture delivery identity, stale lease, retry, backpressure and remote failure and visible failures.


# 14.6 FEAT-COMPUTE-GERONIMO-JMS - geronimo-jms_2.0_spec-1.0-alpha-2.jar

## 1. Objective

- **Goal:** Implement compatible compute messages, worker admission and job ownership.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Run owned distributed jobs with compatible workers and bounded messaging.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/libs/geronimo-jms_2.0_spec-1.0-alpha-2.jar`; 81 raw class entries; SHA-256 `62a109edef3de718b0cb600bf040b4be5e32c683a57ee16f9f8a89537bf5da51`.
- **Inspected reference:** [geronimo-jms_2.0_spec-1.0-alpha-2.md](../../sqx/Libraries/geronimo-jms_2.0_spec-1.0-alpha-2.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/libs/geronimo-jms_2.0_spec-1.0-alpha-2.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/libs/geronimo-jms_2.0_spec-1.0-alpha-2.jar" javax.jms.BytesMessage`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/plugins/compute/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Compute/grid messaging, remote registration and worker placement; downstream P06,P09–P13,P15.
- **Dependency:** qualify stdlib/declared packages; approve additions; classify JVM-only internals.

- **UI disposition:** Infrastructure only; no standalone UI component found in this library allocation. Its owned backend consumer feeds Grid Control/Test through the phase integration gate; do not invent a library screen or direct plugin route.

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
- [ ] **Step 4:** Wire qualified adapters to consumers; release resources on failure/shutdown.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Verify UI-facing consumer contract: Test this infrastructure through its declared backend/host consumer; expose failures through the owning domain envelope. The phase's connected UI gate verifies the observable workflow.


- [ ] **Step 7:** `FR-COMPUTE-GERONIMO-JMS-BYTES-MESSAGE-CONTRACT` → `javax.jms.BytesMessage`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 8:** `FR-COMPUTE-GERONIMO-JMS-BYTES-MESSAGE-GET-BODY-LENGTH` → `javax.jms.BytesMessage.getBodyLength()J`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-COMPUTE-GERONIMO-JMS-BYTES-MESSAGE-READ-BOOLEAN` → `javax.jms.BytesMessage.readBoolean()Z`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_compute_geronimo_jms.py --no-cov`; expect delivery identity, stale lease, retry, backpressure and remote failure; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture delivery identity, stale lease, retry, backpressure and remote failure and visible failures.


# 14.7 FEAT-COMPUTE-JSPF-REMOTE - jspf.remote.jar

## 1. Objective

- **Goal:** Implement compatible compute messages, worker admission and job ownership.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Run owned distributed jobs with compatible workers and bounded messaging.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/libs/jspf.remote.jar`; 6 raw class entries; SHA-256 `9987cca1d084129a024a5c7132e561a039c9ec933cc8ebe8697bf89e79412652`.
- **Inspected reference:** [jspf.remote.md](../../sqx/Libraries/jspf.remote.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/libs/jspf.remote.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/libs/jspf.remote.jar" net.xeoh.plugins.remote.ExportResult`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/plugins/compute/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Compute/grid messaging, remote registration and worker placement; downstream P06,P09–P13,P15.
- **Dependency:** qualify stdlib/declared packages; approve additions; classify JVM-only internals.

- **UI disposition:** Infrastructure only; no standalone UI component found in this library allocation. Its owned backend consumer feeds Grid Control/Test through the phase integration gate; do not invent a library screen or direct plugin route.

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
- [ ] **Step 4:** Wire qualified adapters to consumers; release resources on failure/shutdown.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Verify UI-facing consumer contract: Test this infrastructure through its declared backend/host consumer; expose failures through the owning domain envelope. The phase's connected UI gate verifies the observable workflow.


- [ ] **Step 7:** `FR-COMPUTE-JSPF-REMOTE-EXPORT-RESULT-CONTRACT` → `net.xeoh.plugins.remote.ExportResult`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 8:** `FR-COMPUTE-JSPF-REMOTE-EXPORT-RESULT-GET-EXPORT-URIS` → `net.xeoh.plugins.remote.ExportResult.getExportURIs()Ljava/util/Collection;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_compute_jspf_remote.py --no-cov`; expect delivery identity, stale lease, retry, backpressure and remote failure; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture delivery identity, stale lease, retry, backpressure and remote failure and visible failures.


# 14.8 FEAT-COMPUTE-APP-GRID-CONTROL - AppGridControl.jar

## 1. Objective

- **Goal:** Mount the GridControl workspace against real backend capabilities.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Run owned distributed jobs with compatible workers and bounded messaging.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/plugins/AppGridControl/AppGridControl.jar`; 1 raw class entries; SHA-256 `edc5f2cdac1835cdbe512ea3c19b25a1d660ad9a990a488c533db3b27bad9197`.
- **Inspected reference:** [AppGridControl.md](../../sqx/GridControl/AppGridControl.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/plugins/AppGridControl/AppGridControl.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/plugins/AppGridControl/AppGridControl.jar" com.strategyquant.plugin.App.impl.GridControl.GridControlAppPlugin`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/workspace/GridControl/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Workspace/product registration and backend composition; downstream .
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/plugins/AppGridControl`; `SQX_145_REFERENCE_ROOT/internal/web/GRIDCONTROL`; `SQX_145_REFERENCE_ROOT/internal/web/GRIDTEST`; `SQX_145_REFERENCE_ROOT/internal/plugins/ServletGridControl`. Inspect `SQX_145_REFERENCE_ROOT/internal/plugins/AppGridControl/module.js`.
- **Existing UI connection:** Grid Control/Test; proposed shared consumer; verify the exact existing control and public contract before implementation. Target `ui/app/workspace/GridControl/GridControlWorkspace.tsx`; wire worker compatibility/discovery, real grid job progress and bounded failure status.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

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

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/workspace/GridControl/GridControlWorkspace.tsx`
  - Display worker compatibility/discovery, real grid job progress and bounded failure status from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/GridTest/GridTestWorkspace.tsx`
  - Display worker compatibility/discovery, real grid job progress and bounded failure status from backend responses; preserve layout.
- **Create:** `ui/app/workspace/GridControl/gridControlClient.ts`
  - Typed domain client over host transport; ratify route/schema/version, errors and cancellation. Reuse this proposed owner if delivered earlier.
- **Create:** `ui/tests/unit/backend-connections/feat-compute-app-grid-control.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-grid-compute-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Mount the GridControl workspace against real backend capabilities; verify discovery, workspace readiness, job/resource ownership and unmount cleanup.
- [ ] **Step 4:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Connect retained UI: Ratify the feature-owned wire contract; bind worker compatibility/discovery, real grid job progress and bounded failure status to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 7:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.


- [ ] **Step 8:** `FR-COMPUTE-APP-GRID-CONTROL-GRID-CONTROL-APP-PLUGIN-CONTRACT` → `com.strategyquant.plugin.App.impl.GridControl.GridControlAppPlugin`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-COMPUTE-APP-GRID-CONTROL-GRID-CONTROL-APP-PLUGIN-GET-NAME` → `com.strategyquant.plugin.App.impl.GridControl.GridControlAppPlugin.getName()Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 10:** `FR-COMPUTE-APP-GRID-CONTROL-GRID-CONTROL-APP-PLUGIN-GET-PRODUCT` → `com.strategyquant.plugin.App.impl.GridControl.GridControlAppPlugin.getProduct()Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_compute_app_grid_control.py --no-cov`; expect discovery, workspace readiness, job/resource ownership and unmount cleanup; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture discovery, workspace readiness, job/resource ownership and unmount cleanup and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-compute-app-grid-control.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-grid-compute-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise Grid Control/Test for FEAT-COMPUTE-APP-GRID-CONTROL; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.


# 14.9 FEAT-COMPUTE-APP-GRID-TEST - AppGridTest.jar

## 1. Objective

- **Goal:** Mount the GridTest workspace against real backend capabilities.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Run owned distributed jobs with compatible workers and bounded messaging.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/plugins/AppGridTest/AppGridTest.jar`; 1 raw class entries; SHA-256 `54052d60afe500b1cbe04113905e1812077bd2f6e696329e42b5e14ef8529023`.
- **Inspected reference:** [AppGridTest.md](../../sqx/GridTest/AppGridTest.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/plugins/AppGridTest/AppGridTest.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/plugins/AppGridTest/AppGridTest.jar" com.strategyquant.plugin.App.impl.GridTest.GridTestAppPlugin`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/workspace/GridTest/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Workspace/product registration and backend composition; downstream .
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/plugins/AppGridTest`; `SQX_145_REFERENCE_ROOT/internal/web/GRIDCONTROL`; `SQX_145_REFERENCE_ROOT/internal/web/GRIDTEST`; `SQX_145_REFERENCE_ROOT/internal/plugins/ServletGridControl`. Inspect `SQX_145_REFERENCE_ROOT/internal/plugins/AppGridTest/module.js`.
- **Existing UI connection:** Grid Control/Test; proposed shared consumer; verify the exact existing control and public contract before implementation. Target `ui/app/workspace/GridControl/GridControlWorkspace.tsx`; wire worker compatibility/discovery, real grid job progress and bounded failure status.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

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

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/workspace/GridControl/GridControlWorkspace.tsx`
  - Display worker compatibility/discovery, real grid job progress and bounded failure status from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/GridTest/GridTestWorkspace.tsx`
  - Display worker compatibility/discovery, real grid job progress and bounded failure status from backend responses; preserve layout.
- **Create:** `ui/app/workspace/GridControl/gridControlClient.ts`
  - Typed domain client over host transport; ratify route/schema/version, errors and cancellation. Reuse this proposed owner if delivered earlier.
- **Create:** `ui/tests/unit/backend-connections/feat-compute-app-grid-test.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-grid-compute-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Mount the GridTest workspace against real backend capabilities; verify discovery, workspace readiness, job/resource ownership and unmount cleanup.
- [ ] **Step 4:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Connect retained UI: Ratify the feature-owned wire contract; bind worker compatibility/discovery, real grid job progress and bounded failure status to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 7:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.


- [ ] **Step 8:** `FR-COMPUTE-APP-GRID-TEST-GRID-TEST-APP-PLUGIN-CONTRACT` → `com.strategyquant.plugin.App.impl.GridTest.GridTestAppPlugin`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-COMPUTE-APP-GRID-TEST-GRID-TEST-APP-PLUGIN-GET-NAME` → `com.strategyquant.plugin.App.impl.GridTest.GridTestAppPlugin.getName()Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 10:** `FR-COMPUTE-APP-GRID-TEST-GRID-TEST-APP-PLUGIN-GET-PRODUCT` → `com.strategyquant.plugin.App.impl.GridTest.GridTestAppPlugin.getProduct()Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_compute_app_grid_test.py --no-cov`; expect discovery, workspace readiness, job/resource ownership and unmount cleanup; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture discovery, workspace readiness, job/resource ownership and unmount cleanup and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-compute-app-grid-test.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-grid-compute-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise Grid Control/Test for FEAT-COMPUTE-APP-GRID-TEST; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.


# 14.10 FEAT-COMPUTE-SERVLET-GRID-CONTROL - ServletGridControl.jar

## 1. Objective

- **Goal:** Expose GridControl commands through the owning domain routes.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Run owned distributed jobs with compatible workers and bounded messaging.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/plugins/ServletGridControl/ServletGridControl.jar`; 2 raw class entries; SHA-256 `eb88c3bfc9a8fd1fc45f3556431d5161b48e3a23c29b23150adb02299d320f0d`.
- **Inspected reference:** [ServletGridControl.md](../../sqx/GridControl/ServletGridControl.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/plugins/ServletGridControl/ServletGridControl.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/plugins/ServletGridControl/ServletGridControl.jar" com.strategyquant.plugin.Servlet.impl.GridControl.GridControlServlet`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/workspace/GridControl/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Grid-management API; downstream .
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/plugins/ServletGridControl`; `SQX_145_REFERENCE_ROOT/internal/web/GRIDCONTROL`; `SQX_145_REFERENCE_ROOT/internal/web/GRIDTEST`. Inspect `SQX_145_REFERENCE_ROOT/internal/web/GRIDCONTROL/layout/LayoutCtrl.js`; `SQX_145_REFERENCE_ROOT/internal/web/GRIDTEST/layout/LayoutCtrl.js`.
- **Existing UI connection:** Grid Control/Test; proposed shared consumer; verify the exact existing control and public contract before implementation. Target `ui/app/workspace/GridControl/GridControlWorkspace.tsx`; wire worker compatibility/discovery, real grid job progress and bounded failure status.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

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

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/workspace/GridControl/GridControlWorkspace.tsx`
  - Display worker compatibility/discovery, real grid job progress and bounded failure status from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/GridTest/GridTestWorkspace.tsx`
  - Display worker compatibility/discovery, real grid job progress and bounded failure status from backend responses; preserve layout.
- **Create:** `ui/app/workspace/GridControl/gridControlClient.ts`
  - Typed domain client over host transport; ratify route/schema/version, errors and cancellation. Reuse this proposed owner if delivered earlier.
- **Create:** `ui/tests/unit/backend-connections/feat-compute-servlet-grid-control.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-grid-compute-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Expose GridControl commands through the owning domain routes; verify command parsing, typed outputs, authority, validation errors and cancellation.
- [ ] **Step 4:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Connect retained UI: Ratify the feature-owned wire contract; bind worker compatibility/discovery, real grid job progress and bounded failure status to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 7:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.


- [ ] **Step 8:** `FR-COMPUTE-SERVLET-GRID-CONTROL-GRID-CONTROL-SERVLET-CONTRACT` → `com.strategyquant.plugin.Servlet.impl.GridControl.GridControlServlet`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-COMPUTE-SERVLET-GRID-CONTROL-GRID-CONTROL-SERVLET-EXECUTE` → `com.strategyquant.plugin.Servlet.impl.GridControl.GridControlServlet.execute(Ljava/lang/String;Ljava/util/Map;Ljava/lang/String;)Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 10:** `FR-COMPUTE-SERVLET-GRID-CONTROL-GRID-CONTROL-SERVLET-ON-GET-DATA` → `com.strategyquant.plugin.Servlet.impl.GridControl.GridControlServlet.onGetData(Ljava/util/Map;)Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_compute_servlet_grid_control.py --no-cov`; expect command parsing, typed outputs, authority, validation errors and cancellation; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture command parsing, typed outputs, authority, validation errors and cancellation and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-compute-servlet-grid-control.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-grid-compute-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise Grid Control/Test for FEAT-COMPUTE-SERVLET-GRID-CONTROL; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.


# 14.11 FEAT-COMPUTE-JGROUPS - jgroups-3.6.9.Final.jar

## 1. Objective

- **Goal:** Adapt the consumed distributed transport/lifecycle contract to the approved compute capability.
- **Context / Problem Solved:** Build 145 adds/changes this donor contribution; existing mock presentation and a filename do not establish functional support.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/libs/jgroups-3.6.9.Final.jar`; 1060 raw class entries; SHA-256 `006cb0ca4b7358e2ae778afe7f7056786fcd4d4b3b02ae7377bb778baf6be196`.
- **Inspected reference:** [jgroups-3.6.9.Final.md](../../sqx/Libraries/jgroups-3.6.9.Final.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/libs/jgroups-3.6.9.Final.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/libs/jgroups-3.6.9.Final.jar" org.jgroups.Address`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Ownership:** proposed `FEAT-COMPUTE-JGROUPS` and `FR-COMPUTE-JGROUPS-CONSUMED-CONTRACTS`; owner `app/plugins/compute/README.md`. No application registration or implementation is implied.
- **Dependencies:** P00 evidence/ownership, P01 logging and P02 typed sessions/jobs/resources; phase-specific data/engine/project prerequisites from the delivery graph.
- **UI donors:** No standalone UI contribution is established for this infrastructure archive; trace its consuming host/domain feature and connect there.

## 3. File Changes

- **Create:** `app/plugins/compute/vendor_protocols.py` — Adapt the consumed distributed transport/lifecycle contract to the approved compute capability.
- **Create:** `app/plugins/compute/README.md` — ratify owning FEAT/FR contracts and status in the approved feature plan.
- **Create:** `tests/unit/reference_145/test_compute_jgroups.py` — donor-derived normal, boundary, failure and FR-log checks.
- **Delete / Deprecate:** none; version/dependency retirement requires explicit approved disposition.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Ratify cohort, owning FEAT/FRs, target decisions, dependencies and exact write paths in the canonical plan.
- [ ] **Step 2:** Fingerprint the selected cohort; enumerate classes, methods and actual consumers.
- [ ] **Step 3:** Inspect consumed bodies and record normal/boundary/error contracts as descriptive FRs.
- [ ] **Step 4:** Ratify ownership and a reuse/adaptation/JVM-only disposition; implement only retained behavior.
- [ ] **Step 5:** Verify fixtures, invalid inputs, lifecycle/cancellation where applicable and explicit FR logs.
- [ ] **Step 6:** Expose the typed capability to its existing host/domain consumers; no standalone UI is established for this infrastructure JAR.
- [ ] **Step 7:** Record timestamped observations and walkthrough; update the matching master checklist row only when all requirements pass.

- [ ] **Step 8:** `FR-COMPUTE-JGROUPS-ADDRESS-CONTRACT` → `org.jgroups.Address`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-COMPUTE-JGROUPS-ADDRESS-SIZE` → `org.jgroups.Address.size()I`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/reference_145/test_compute_jgroups.py --no-cov`; scoped Ruff format/check and strict Mypy; assert independent expected outputs and FR logs.
- **Manual / Browser Verification:** Inspect consumer logs, lifecycle/failure outcomes and the declared infrastructure/JVM-only disposition.
- **Completion limit:** missing bodies/ownership/entitlement or independent expected outputs keep the task unchecked; static declarations do not establish SQX parity.


# 14.12 FEAT-COMPUTE-NETTY-ALL - netty-all-4.1.5.Final.jar

## 1. Objective

- **Goal:** Adapt the consumed distributed transport/lifecycle contract to the approved compute capability.
- **Context / Problem Solved:** Build 145 adds/changes this donor contribution; existing mock presentation and a filename do not establish functional support.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/libs/netty-all-4.1.5.Final.jar`; 2289 raw class entries; SHA-256 `1b583a45b4ad1ff7a01a29f17787c9f95e51b76d28bc8b13c6a8db8ec47b7bf7`.
- **Inspected reference:** [netty-all-4.1.5.Final.md](../../sqx/Libraries/netty-all-4.1.5.Final.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/libs/netty-all-4.1.5.Final.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/libs/netty-all-4.1.5.Final.jar" io.netty.util.Attribute`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Ownership:** proposed `FEAT-COMPUTE-NETTY-ALL` and `FR-COMPUTE-NETTY-ALL-CONSUMED-CONTRACTS`; owner `app/plugins/compute/README.md`. No application registration or implementation is implied.
- **Dependencies:** P00 evidence/ownership, P01 logging and P02 typed sessions/jobs/resources; phase-specific data/engine/project prerequisites from the delivery graph.
- **UI donors:** No standalone UI contribution is established for this infrastructure archive; trace its consuming host/domain feature and connect there.

## 3. File Changes

- **Create:** `app/plugins/compute/vendor_protocols.py` — Adapt the consumed distributed transport/lifecycle contract to the approved compute capability.
- **Create:** `app/plugins/compute/README.md` — ratify owning FEAT/FR contracts and status in the approved feature plan.
- **Create:** `tests/unit/reference_145/test_compute_netty_all.py` — donor-derived normal, boundary, failure and FR-log checks.
- **Delete / Deprecate:** none; version/dependency retirement requires explicit approved disposition.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Ratify cohort, owning FEAT/FRs, target decisions, dependencies and exact write paths in the canonical plan.
- [ ] **Step 2:** Fingerprint the selected cohort; enumerate classes, methods and actual consumers.
- [ ] **Step 3:** Inspect consumed bodies and record normal/boundary/error contracts as descriptive FRs.
- [ ] **Step 4:** Ratify ownership and a reuse/adaptation/JVM-only disposition; implement only retained behavior.
- [ ] **Step 5:** Verify fixtures, invalid inputs, lifecycle/cancellation where applicable and explicit FR logs.
- [ ] **Step 6:** Expose the typed capability to its existing host/domain consumers; no standalone UI is established for this infrastructure JAR.
- [ ] **Step 7:** Record timestamped observations and walkthrough; update the matching master checklist row only when all requirements pass.

- [ ] **Step 8:** `FR-COMPUTE-NETTY-ALL-ATTRIBUTE-CONTRACT` → `io.netty.util.Attribute`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-COMPUTE-NETTY-ALL-ATTRIBUTE-KEY` → `io.netty.util.Attribute.key()Lio/netty/util/AttributeKey;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 10:** `FR-COMPUTE-NETTY-ALL-ATTRIBUTE-GET` → `io.netty.util.Attribute.get()Ljava/lang/Object;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/reference_145/test_compute_netty_all.py --no-cov`; scoped Ruff format/check and strict Mypy; assert independent expected outputs and FR logs.
- **Manual / Browser Verification:** Inspect consumer logs, lifecycle/failure outcomes and the declared infrastructure/JVM-only disposition.
- **Completion limit:** missing bodies/ownership/entitlement or independent expected outputs keep the task unchecked; static declarations do not establish SQX parity.


# 14.13 P14 integration — Run owned distributed jobs with compatible workers and bounded messaging

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

- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/web/GRIDCONTROL`; `SQX_145_REFERENCE_ROOT/internal/web/GRIDTEST`; `SQX_145_REFERENCE_ROOT/internal/plugins/ServletGridControl`. Inspect `SQX_145_REFERENCE_ROOT/internal/web/GRIDCONTROL/layout/LayoutCtrl.js`; `SQX_145_REFERENCE_ROOT/internal/web/GRIDTEST/layout/LayoutCtrl.js`.
- **Existing UI connection:** Grid Control/Test; proposed shared consumer; verify the exact existing control and public contract before implementation. Target `ui/app/workspace/GridControl/GridControlWorkspace.tsx`; wire worker compatibility/discovery, real grid job progress and bounded failure status.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

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

- **UI connection files (existing presentation):**
- **Create:** `ui/tests/unit/backend-connections/task-14-13.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Review preceding feature fixtures and owning README registrations; ratify the phase integration contracts and execution plan.
- [ ] **Step 2:** Specify worker versions, placement, protocol envelopes, leases and duplicate-delivery handling.
- [ ] **Step 3:** Implement registration, scheduling, heartbeat/loss, retry/cancellation and resource cleanup.
- [ ] **Step 4:** Connect GridControl status/actions and GridTest repeatable benchmarks to real worker runs.
- [ ] **Step 5:** Replace fixture-driven production execution in the affected workflow; retain deterministic fixtures only in tests.
- [ ] **Step 6:** Test positive/failure/cancellation paths and observable FR logs; reload/reconnect and reconcile persisted outputs.
- [ ] **Step 7:** Record exact commands, timestamped artifacts, unresolved gaps and walkthrough; obtain separate owner commit authority.

- [ ] **Step 8:** Connect retained UI: Ratify the feature-owned wire contract; bind worker compatibility/discovery, real grid job progress and bounded failure status to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 9:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/integration/test_grid_compute_workflow.py --no-cov`; `npm --prefix ui run test -- tests/unit/workspace/GridControl/gridControl.test.ts`; `npm --prefix ui run test:ui -- tests/e2e/sqx-grid-compute-backend.spec.ts`. Assert local/remote result equivalence, worker admission and placement/benchmark accounting; reject lost worker, stale lease, duplicate result, incompatible version and queue overload.
- **Manual / Browser Verification:** Register a test worker; dispatch a fixture job; disconnect it; verify bounded recovery; run GridTest and reconcile completed counts.

- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/task-14-13.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-grid-compute-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise Grid Control/Test for 14.14; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.

## Phase completion gate

- [ ] Every applicable feature passed its own isolated real-host UI/backend case; no production mock fallback or unresolved required UI remains.

- [ ] Reconcile all allocated FEAT/FR dispositions, donor fixtures and ownership gaps.
- [ ] Run Ruff format/check and strict Mypy on the approved changed Python paths; verify branch-aware coverage ≥80% across retained application source at release.
- [ ] For affected UI: `npm --prefix ui run typecheck`, `npm --prefix ui run test`, `npm --prefix ui run build`.
- [ ] Record real workflow observations, timestamps, failure artifacts and remaining gaps in the walkthrough.
- [ ] Obtain the next task/phase approval; commits and external/destructive actions retain separate owner gates.
